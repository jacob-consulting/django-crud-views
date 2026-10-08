"""django-pipeline integration for the crud_views asset registry.

Settings-time safe: module-level imports are stdlib only, so ``settings.py`` can do
``from crud_views.lib.pipeline import cv_sources``. Never imports django-pipeline: it only produces
values pipeline reads, and reads ``settings.PIPELINE`` as plain data.
"""

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from fnmatch import fnmatchcase

KINDS = ("js", "css")
SECTIONS = {"js": "JAVASCRIPT", "css": "STYLESHEETS"}

NOT_READY_MESSAGE = (
    "cv_sources() was resolved before the app registry is ready - most likely it was expanded in settings.py "
    "(e.g. [*cv_sources('js')] or list(cv_sources('js'))). Pass extra files via before=/after= or combine "
    "with + instead."
)


def _as_tuple(value: Iterable[str] | str) -> tuple[str, ...]:
    """A bare string is one item, not an iterable of characters."""
    return (value,) if isinstance(value, str) else tuple(value)


def _ensure_ready() -> None:
    from django.apps import apps
    from django.core.exceptions import AppRegistryNotReady

    if not apps.ready:
        raise AppRegistryNotReady(NOT_READY_MESSAGE)


def _dedupe(paths: Iterable[str]) -> list[str]:
    seen = set()
    result = []
    for path in paths:
        if path not in seen:
            seen.add(path)
            result.append(path)
    return result


class LazySources(Sequence):
    """A pipeline ``source_filenames`` value that resolves from the asset registry on every access.

    django-pipeline keeps the object by reference and first iterates it when a package is rendered or
    collected - after AppConfig.ready(), when every bundle is registered.
    """

    def __init__(
        self,
        kind: str,
        *,
        before: Iterable[str] | str = (),
        after: Iterable[str] | str = (),
        keys: Iterable[str] | str | None = None,
        exclude: Iterable[str] | str = (),
    ):
        if kind not in KINDS:
            raise ValueError(f"cv_sources() kind must be 'js' or 'css', got {kind!r}")
        self._kind = kind
        self._before = _as_tuple(before)
        self._after = _as_tuple(after)
        self._keys = None if keys is None else _as_tuple(keys)
        self._exclude = _as_tuple(exclude)

    @property
    def kind(self) -> str:
        return self._kind

    @property
    def keys(self) -> tuple[str, ...] | None:
        return self._keys

    @property
    def exclude(self) -> tuple[str, ...]:
        return self._exclude

    def registry_entries(self) -> list:
        """Local registry entries (BundleEntry) this list draws from, after keys/exclude; includes emit=False."""
        _ensure_ready()
        from crud_views.lib import assets

        return [
            entry
            for entry in assets.collect(self._kind)
            if (self._keys is None or entry.key in self._keys)
            and entry.key not in self._exclude
            and not assets.is_external(entry.asset.path)
        ]

    def _resolve(self) -> list[str]:
        registry_paths = [entry.asset.path for entry in self.registry_entries()]
        return _dedupe([*self._before, *registry_paths, *self._after])

    def __iter__(self):
        return iter(self._resolve())

    def __len__(self) -> int:
        return len(self._resolve())

    def __getitem__(self, index):
        return self._resolve()[index]

    def _with(self, before: tuple[str, ...], after: tuple[str, ...]) -> "LazySources":
        return LazySources(self._kind, before=before, after=after, keys=self._keys, exclude=self._exclude)

    def __add__(self, other):
        if isinstance(other, (list, tuple)):
            return self._with(self._before, self._after + tuple(other))
        return NotImplemented

    def __radd__(self, other):
        if isinstance(other, (list, tuple)):
            return self._with(tuple(other) + self._before, self._after)
        return NotImplemented

    def __repr__(self) -> str:
        return (
            f"<LazySources kind={self._kind!r} keys={self._keys!r} exclude={self._exclude!r} "
            f"before={len(self._before)} after={len(self._after)}>"
        )


def cv_sources(
    kind: str,
    *,
    before: Iterable[str] | str = (),
    after: Iterable[str] | str = (),
    keys: Iterable[str] | str | None = None,
    exclude: Iterable[str] | str = (),
) -> LazySources:
    """Lazy pipeline ``source_filenames``: local registry assets of one kind ("js"/"css"), core first.

    keys=None selects every bundle ("crud_views" = core); exclude drops bundles; before/after wrap the
    registry entries (e.g. jQuery before, the project's app.js after). External (CDN) entries are left
    out - pipeline cannot bundle them; {% cv_js %}/{% cv_css %} keep rendering them.
    """
    return LazySources(kind, before=before, after=after, keys=keys, exclude=exclude)


@dataclass(frozen=True)
class PipelineSource:
    """One pipeline package's source_filenames, tagged with the kind of its PIPELINE section."""

    kind: str
    package: str
    sources: object  # LazySources or an iterable of plain path / glob strings


def pipeline_sources(conf: dict | None = None) -> list[PipelineSource]:
    """Walk PIPELINE["JAVASCRIPT"] / ["STYLESHEETS"] as plain data (never imports pipeline)."""
    if conf is None:
        from django.conf import settings

        conf = getattr(settings, "PIPELINE", None)
    conf = conf or {}
    result = []
    for kind, section in SECTIONS.items():
        packages = conf.get(section)
        if not isinstance(packages, dict):
            continue
        for package, config in packages.items():
            if isinstance(config, dict):
                value = config.get("source_filenames")  # no truthiness test: it would resolve a LazySources
                result.append(PipelineSource(kind=kind, package=package, sources=() if value is None else value))
    return result


def _glob_match(path: str, pattern: str) -> bool:
    """Match like pipeline/glob.py: one path segment at a time, so ``*`` never crosses ``/`` (no ``**`` support).

    pipeline lists a directory and fnmatch-filters its names, hiding dotfiles unless the pattern starts with ".".
    """
    path_parts, pattern_parts = path.split("/"), pattern.split("/")
    if len(path_parts) != len(pattern_parts):
        return False
    for name, part in zip(path_parts, pattern_parts, strict=True):
        if not fnmatchcase(name, part):
            return False
        if _has_magic(part) and name.startswith(".") and not part.startswith("."):
            return False
    return True


def _has_magic(text: str) -> bool:
    return any(char in text for char in "*?[")


def _coverage(sources: list[PipelineSource]) -> list[tuple[PipelineSource, Callable[[str], bool]]]:
    """Per package a path predicate; LazySources resolve once, plain strings match as glob patterns."""
    result = []
    for source in sources:
        if isinstance(source.sources, LazySources):
            result.append((source, frozenset(source.sources).__contains__))
        else:
            items = (source.sources,) if isinstance(source.sources, str) else source.sources
            patterns = tuple(p for p in items if isinstance(p, str))
            result.append((source, lambda path, patterns=patterns: any(_glob_match(path, p) for p in patterns)))
    return result


@dataclass(frozen=True)
class AssetRow:
    """One registry asset and how it reaches the browser."""

    key: str
    kind: str
    path: str
    external: bool
    integrity: str | None
    crossorigin: str | None
    emit: bool
    delivery: tuple[str, ...]

    @property
    def delivery_label(self) -> str:
        return ", ".join(self.delivery)

    @property
    def bundled(self) -> bool:
        return any(d.startswith("pipeline:") for d in self.delivery)


def asset_rows(conf: dict | None = None) -> list[AssetRow]:
    """Every registry asset (core first, all bundles incl. emit=False) with its delivery.

    The single resolver behind the W34x checks and ``manage.py cv_assets``; "tag" delivery comes from
    assets.tag_entries(), the exact list {% cv_js %}/{% cv_css %} render.
    """
    from crud_views.lib import assets

    coverage = _coverage(pipeline_sources(conf))
    rows = []
    for kind in KINDS:
        tagged = {(entry.key, entry.asset.path) for entry in assets.tag_entries(kind)}
        for entry in assets.collect(kind):
            path = entry.asset.path
            external = assets.is_external(path)
            delivery = []
            if (entry.key, path) in tagged:
                delivery.append("tag (CDN)" if external else "tag")
            if not external:
                delivery += [f"pipeline:{s.package}" for s, covers in coverage if s.kind == kind and covers(path)]
            if not delivery:
                delivery.append("none" if entry.emit else "none (emit=False)")
            rows.append(
                AssetRow(
                    key=entry.key,
                    kind=kind,
                    path=path,
                    external=external,
                    integrity=entry.asset.integrity,
                    crossorigin=entry.asset.crossorigin,
                    emit=entry.emit,
                    delivery=tuple(delivery),
                )
            )
    return rows
