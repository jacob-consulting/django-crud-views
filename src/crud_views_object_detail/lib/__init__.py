"""Public API surface for crud_views_object_detail (lazy PEP 562 __getattr__)."""

from importlib import import_module

__all__ = [
    "BadgeConfig",
    "LinkConfig",
    "ObjectDetailMixin",
    "ObjectDetailView",
    "ObjectDetailViewPermissionRequired",
    "PropertyConfig",
    "PropertyGroupConfig",
    "x",
]

_CONFIG = "crud_views_object_detail.lib.config"

_EXPORTS = {
    "BadgeConfig": (_CONFIG, "BadgeConfig"),
    "LinkConfig": (_CONFIG, "LinkConfig"),
    "PropertyConfig": (_CONFIG, "PropertyConfig"),
    "PropertyGroupConfig": (_CONFIG, "PropertyGroupConfig"),
    "x": (_CONFIG, "x"),
    "ObjectDetailMixin": ("crud_views_object_detail.lib.mixins", "ObjectDetailMixin"),
    "ObjectDetailView": ("crud_views_object_detail.lib.views", "ObjectDetailView"),
    "ObjectDetailViewPermissionRequired": ("crud_views_object_detail.lib.views", "ObjectDetailViewPermissionRequired"),
}


def __getattr__(name: str):
    try:
        module_path, attr = _EXPORTS[name]
    except KeyError:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from None
    value = getattr(import_module(module_path), attr)
    globals()[name] = value
    return value


def __dir__():
    return sorted(set(globals()) | set(__all__))
