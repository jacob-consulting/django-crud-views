"""Public asset registry: apps contribute JS/CSS to cv_js/cv_css via AppConfig.ready()."""

from dataclasses import dataclass
from threading import Lock
from typing import Iterable, List

from django.core.exceptions import ImproperlyConfigured
from django.templatetags.static import static

_EXTERNAL_PREFIXES = ("http://", "https://", "//")


@dataclass(frozen=True)
class Asset:
    """A single JS/CSS asset: a static path or external URL, with optional SRI metadata.

    integrity is meant for external URLs (see system checks E330/W331); when set and
    crossorigin is None, tags render crossorigin="anonymous".
    """

    path: str
    integrity: str | None = None
    crossorigin: str | None = None


def normalize_entries(entries: Iterable) -> tuple:
    """Normalize a mix of str and Asset entries to a tuple of Asset."""
    return tuple(entry if isinstance(entry, Asset) else Asset(path=entry) for entry in entries)


@dataclass(frozen=True)
class AssetBundle:
    key: str
    js: tuple = ()
    css: tuple = ()
    emit: bool = True


_REGISTRY: dict = {}
_LOCK = Lock()


def register_assets(key: str, js: Iterable[str] = (), css: Iterable[str] = (), emit: bool = True) -> None:
    """Register an asset bundle. Call from AppConfig.ready().

    Entries are static paths, external URLs (http://, https://, //) rendered verbatim, or Asset
    instances carrying SRI metadata.
    Bundles render after core assets, in registration order (= INSTALLED_APPS order).
    """
    with _LOCK:
        if key in _REGISTRY:
            raise ImproperlyConfigured(f"crud_views asset bundle {key!r} is already registered")
        _REGISTRY[key] = AssetBundle(key=key, js=normalize_entries(js), css=normalize_entries(css), emit=emit)


def get_registered(only_emitting: bool = False) -> List[AssetBundle]:
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
