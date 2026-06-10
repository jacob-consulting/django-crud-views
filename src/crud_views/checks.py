from django.core.checks import Error
from django.core.checks import register

from crud_views.lib import ordered as ordered_helper
from crud_views.lib.formsets.formsets import FormSet
from crud_views.lib.settings import crud_views_settings
from crud_views.lib.views.action_ordered import OrderedDownView, OrderedUpView
from crud_views.lib.viewset import ViewSet, _REGISTRY, _REGISTRY_LOCK

TAG = "crud_views"


@register(TAG)
def check_viewsets(app_configs=None, **kwargs):
    """Run all ViewSet, CrudView and settings checks."""

    errors = crud_views_settings.check_messages

    for check in ViewSet.checks_all():
        for message in check.messages():
            errors.append(message)
    return errors


def _formset_uses_ordering(formset: FormSet) -> bool:
    """True if this formset or any nested child enables can_order."""
    if formset.klass.can_order:
        return True
    return any(_formset_uses_ordering(child) for child in formset.children.values())


def _registry_needs_ordered_model() -> bool:
    """True if any registered view requires django-ordered-model."""
    with _REGISTRY_LOCK:
        viewsets = list(_REGISTRY.values())

    for viewset in viewsets:
        for view in viewset.get_all_views().values():
            if issubclass(view, (OrderedUpView, OrderedDownView)):
                return True
            formsets = getattr(view, "cv_formsets", None)
            if formsets is not None:
                if any(_formset_uses_ordering(fs) for fs in formsets.values()):
                    return True
    return False


@register(TAG)
def check_ordered_model_installed(app_configs=None, **kwargs):
    """Error if an ordered view / can_order formset is used without django-ordered-model."""
    if ordered_helper.get_ordered_model() is not None:
        return []
    if not _registry_needs_ordered_model():
        return []
    return [
        Error(
            "django-ordered-model is required by an ordered view or a can_order formset, but it is not installed.",
            hint="Install the optional extra: pip install django-crud-views[ordered]",
            id="crud_views.E300",
        )
    ]
