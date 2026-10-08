"""Public asset registry: apps contribute JS/CSS to cv_js/cv_css via AppConfig.ready()."""

from collections.abc import Iterable
from dataclasses import dataclass
from threading import Lock

from django.core.exceptions import ImproperlyConfigured
from django.templatetags.static import static

_EXTERNAL_PREFIXES = ("http://", "https://", "//")  # NOSONAR S5332: matches URLs, never requests them


@dataclass(frozen=True)
class Asset:
    """A single JS/CSS asset: a static path or external URL, with optional SRI metadata.

    integrity is meant for external URLs (see system checks E330/W332); when set and
    crossorigin is None, tags render crossorigin="anonymous".
    """

    path: str
    integrity: str | None = None
    crossorigin: str | None = None


def normalize_entries(entries: Iterable[str | Asset]) -> tuple[Asset, ...]:
    """Normalize a mix of str and Asset entries to a tuple of Asset."""
    return tuple(entry if isinstance(entry, Asset) else Asset(path=entry) for entry in entries)


@dataclass(frozen=True)
class AssetBundle:
    key: str
    js: tuple = ()
    css: tuple = ()
    emit: bool = True


CORE_KEY = "crud_views"
KINDS = ("js", "css")


@dataclass(frozen=True)
class BundleEntry:
    """One asset together with the bundle it belongs to (key and emit travel with the asset)."""

    key: str
    emit: bool
    asset: Asset


_REGISTRY: dict = {}
_LOCK = Lock()


def register_assets(key: str, js: Iterable[str] = (), css: Iterable[str] = (), emit: bool = True) -> None:
    """Register an asset bundle. Call from AppConfig.ready().

    Entries are static paths, external URLs (http://, https://, //) rendered verbatim, or Asset
    instances carrying SRI metadata.
    Bundles render after core assets, in registration order (= INSTALLED_APPS order).
    """
    if key == CORE_KEY:
        raise ImproperlyConfigured(f"crud_views asset bundle key {CORE_KEY!r} is reserved for the core assets")
    with _LOCK:
        if key in _REGISTRY:
            raise ImproperlyConfigured(f"crud_views asset bundle {key!r} is already registered")
        _REGISTRY[key] = AssetBundle(key=key, js=normalize_entries(js), css=normalize_entries(css), emit=emit)


def get_registered(only_emitting: bool = False) -> list[AssetBundle]:
    with _LOCK:
        bundles = list(_REGISTRY.values())
    if only_emitting:
        bundles = [b for b in bundles if b.emit]
    return bundles


def is_external(entry: str) -> bool:
    return entry.startswith(_EXTERNAL_PREFIXES)


def resolve_url(entry: str) -> str:
    """External URLs pass through; static paths resolve via the configured staticfiles storage."""
    return entry if is_external(entry) else static(entry)


def core_bundle() -> AssetBundle:
    """The package's own assets as a bundle, built from CrudViewsSettings (the source of truth)."""
    from crud_views.lib.settings import crud_views_settings

    return AssetBundle(
        key=CORE_KEY,
        js=normalize_entries(crud_views_settings.javascript().values()),
        css=normalize_entries(crud_views_settings.css.values()),
    )


def iter_bundles(only_emitting: bool = False) -> list[AssetBundle]:
    """Core bundle first (regardless of INSTALLED_APPS order), then registered bundles in registration order."""
    return [core_bundle(), *get_registered(only_emitting=only_emitting)]


def collect(kind: str, *, only_emitting: bool = False) -> list[BundleEntry]:
    """All entries of one kind ("js" or "css") across iter_bundles(), in render order."""
    if kind not in KINDS:
        raise ValueError(f"asset kind must be 'js' or 'css', got {kind!r}")
    return [
        BundleEntry(key=bundle.key, emit=bundle.emit, asset=asset)
        for bundle in iter_bundles(only_emitting=only_emitting)
        for asset in getattr(bundle, kind)
    ]


def tag_entries(kind: str) -> list[BundleEntry]:
    """The entries {% cv_js %} / {% cv_css %} render.

    With CRUD_VIEWS_ASSETS_BUNDLED a bundler (django-pipeline) delivers every local static path, so
    only external (CDN) entries remain for the tags.
    """
    from crud_views.lib.settings import crud_views_settings

    entries = collect(kind, only_emitting=True)
    if crud_views_settings.assets_bundled:
        entries = [entry for entry in entries if is_external(entry.asset.path)]
    return entries
