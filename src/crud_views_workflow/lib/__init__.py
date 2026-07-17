"""Public API surface for crud_views_workflow.

Resolved lazily (PEP 562 module __getattr__) on purpose. Consumer *model* modules import
WorkflowModelMixin from crud_views_workflow.lib while Django is still populating apps (before
django.setup()). Importing any submodule runs this package __init__ first, so eager imports here
would drag in crud_views_workflow.lib.views -- which imports the WorkflowInfo model and
CustomFormView (django.contrib.auth.mixins) at module top and therefore cannot be imported before
the app registry is ready. Lazy resolution keeps the model mixin, enums, and form pulling only
import-safe submodules; WorkflowView is loaded only when explicitly requested, which happens from
view modules after setup. See tests/test1/test_import_safety.py.
"""

from importlib import import_module

__all__ = [
    "BadgeEnum",
    "WorkflowComment",
    "WorkflowForm",
    "WorkflowModelMixin",
    "WorkflowView",
    "WorkflowViewPermissionRequired",
]

_EXPORTS = {
    "BadgeEnum": ("crud_views_workflow.lib.enums", "BadgeEnum"),
    "WorkflowComment": ("crud_views_workflow.lib.enums", "WorkflowComment"),
    "WorkflowForm": ("crud_views_workflow.lib.forms", "WorkflowForm"),
    "WorkflowModelMixin": ("crud_views_workflow.lib.mixins", "WorkflowModelMixin"),
    "WorkflowView": ("crud_views_workflow.lib.views", "WorkflowView"),
    "WorkflowViewPermissionRequired": ("crud_views_workflow.lib.views", "WorkflowViewPermissionRequired"),
}


def __getattr__(name: str):
    try:
        module_path, attr = _EXPORTS[name]
    except KeyError:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from None
    value = getattr(import_module(module_path), attr)
    globals()[name] = value  # cache so subsequent lookups skip __getattr__
    return value


def __dir__():
    return sorted(set(globals()) | set(__all__))
