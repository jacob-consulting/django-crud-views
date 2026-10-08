"""django-pipeline integration for the crud_views asset registry.

Settings-time safe: module-level imports are stdlib only, so ``settings.py`` can do
``from crud_views.lib.pipeline import cv_sources``. Never imports django-pipeline: it only produces
values pipeline reads, and reads ``settings.PIPELINE`` as plain data.
"""

from collections.abc import Iterable, Sequence

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
