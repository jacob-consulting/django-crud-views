"""Public API surface for crud_views_object_detail (lazy PEP 562 __getattr__)."""

from importlib import import_module

__all__ = [
    "BadgeConfig",
    "LinkConfig",
    "PropertyConfig",
    "PropertyGroupConfig",
    "x",
    "ObjectDetailMixin",
    "ObjectDetailView",
    "ObjectDetailViewPermissionRequired",
]

_EXPORTS = {
    "BadgeConfig": ("crud_views_object_detail.lib.config", "BadgeConfig"),
    "LinkConfig": ("crud_views_object_detail.lib.config", "LinkConfig"),
    "PropertyConfig": ("crud_views_object_detail.lib.config", "PropertyConfig"),
    "PropertyGroupConfig": ("crud_views_object_detail.lib.config", "PropertyGroupConfig"),
    "x": ("crud_views_object_detail.lib.config", "x"),
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
