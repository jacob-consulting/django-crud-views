from django.core.checks import Error
from django.core.checks import Warning as DjangoWarning
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


def _conditional_messages(nested_conditionals, missing_toggles, non_nullable_clears):
    """Pure formatter — turns collected findings into Django check messages.

    Kept separate from registry traversal so it is unit-testable without the
    full app registry."""
    messages = []
    for key, _conditional in nested_conditionals:
        messages.append(
            Error(
                f"ConditionalFormSet declared on nested formset '{key}'; only first-level formsets are supported.",
                hint="Move the conditional to the top-level formset or remove it.",
                id="crud_views.E310",
            )
        )
    for form_name, field in missing_toggles:
        messages.append(
            Error(
                f"Conditional toggle field '{field}' is not present on form '{form_name}'.",
                hint="Add the field to the form (model field) or use UIFieldToggle so it is injected.",
                id="crud_views.E311",
            )
        )
    for form_name, field in non_nullable_clears:
        messages.append(
            DjangoWarning(
                f"ConditionalGroup clears '{field}' on '{form_name}' but the model field is not null/blank.",
                hint="Set null=True, blank=True on the field, or provide empty_values for it.",
                id="crud_views.W320",
            )
        )
    return messages


@register(TAG)
def check_conditional(app_configs=None, **kwargs):
    """Validate ConditionalGroup / ConditionalFormSet declarations."""
    nested_conditionals: list = []
    missing_toggles: list = []
    non_nullable_clears: list = []

    with _REGISTRY_LOCK:
        viewsets = list(_REGISTRY.values())

    for viewset in viewsets:
        for view in viewset.get_all_views().values():
            formsets = getattr(view, "cv_formsets", None)
            if formsets is not None:
                # top-level only are allowed to carry a conditional
                def _walk(formset, key, is_top):
                    if formset.conditional is not None and not is_top:
                        nested_conditionals.append((key, formset.conditional))
                    for ckey, child in formset.children.items():
                        _walk(child, f"{key}-{ckey}", False)

                for key, fs in formsets.items():
                    _walk(fs, key, True)

            form_class = getattr(view, "form_class", None)
            groups = getattr(form_class, "cv_conditional_groups", None) if form_class else None
            if groups:
                model = getattr(getattr(form_class, "_meta", None), "model", None)
                declared = set(getattr(form_class, "base_fields", {}).keys())
                for group in groups:
                    tname = group.toggle.field_name()
                    if not group.toggle.inject and tname not in declared:
                        missing_toggles.append((form_class.__name__, tname))
                    if model is not None:
                        for fname in group.fields:
                            try:
                                mf = model._meta.get_field(fname)
                            except Exception:
                                continue
                            if not (getattr(mf, "null", False) and getattr(mf, "blank", False)):
                                if fname not in group.empty_values:
                                    non_nullable_clears.append((form_class.__name__, fname))

    return _conditional_messages(nested_conditionals, missing_toggles, non_nullable_clears)


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
