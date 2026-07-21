from django.core.checks import Error
from django.core.checks import Warning as DjangoWarning
from django.core.checks import register

from crud_views.lib import assets
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


def _conditional_messages(nested_conditionals, missing_toggles, non_nullable_clears, purge_conflicts=()):
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
                hint=(
                    "Declare the field on the form (a model field or a BooleanField(required=False)). "
                    "Only ConditionalGroup toggles are auto-injected (UIFieldToggle via "
                    "ConditionalGroupFormMixin); ConditionalFormSet toggles never are."
                ),
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
    for key, reason in purge_conflicts:
        messages.append(
            DjangoWarning(
                f"ConditionalFormSet on formset '{key}' uses on_off='purge' but the formset forbids "
                f"row deletion ({reason}); the toggle will bulk-delete rows anyway.",
                hint="Use on_off='skip', or allow deletion on the formset explicitly.",
                id="crud_views.W321",
            )
        )
    return messages


@register(TAG)
def check_conditional(app_configs=None, **kwargs):
    """Validate ConditionalGroup / ConditionalFormSet declarations."""
    nested_conditionals: list = []
    missing_toggles: list = []
    non_nullable_clears: list = []
    purge_conflicts: list = []

    with _REGISTRY_LOCK:
        viewsets = list(_REGISTRY.values())

    for viewset in viewsets:
        for view in viewset.get_all_views().values():
            form_class = getattr(view, "form_class", None)
            declared = set(getattr(form_class, "base_fields", {}).keys()) if form_class else set()

            groups = getattr(form_class, "cv_conditional_groups", None) if form_class else None
            # ConditionalGroupFormMixin injects these at form init — the only
            # injection path there is; formset toggles are never auto-injected.
            group_injected = {g.toggle.field_name() for g in groups or [] if g.toggle.inject}

            formsets = getattr(view, "cv_formsets", None)
            if formsets is not None:
                # top-level only are allowed to carry a conditional
                def _walk(formset, key, is_top):
                    if formset.conditional is not None:
                        if not is_top:
                            nested_conditionals.append((key, formset.conditional))
                        else:
                            if form_class is not None:
                                tname = formset.conditional.toggle.field_name()
                                if tname not in declared and tname not in group_injected:
                                    missing_toggles.append((form_class.__name__, tname))
                            if formset.conditional.on_off == "purge":
                                if not formset.klass.can_delete:
                                    purge_conflicts.append((key, "can_delete=False"))
                                elif formset.klass.edit_only:
                                    purge_conflicts.append((key, "edit_only=True"))
                    for ckey, child in formset.children.items():
                        _walk(child, f"{key}-{ckey}", False)

                for key, fs in formsets.items():
                    _walk(fs, key, True)

            if groups:
                model = getattr(getattr(form_class, "_meta", None), "model", None)
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

    # Create/Update views routinely share form_class + cv_formsets — report each
    # distinct finding once, not once per view.
    seen_nested = set()
    nested_conditionals = [
        (key, cond) for key, cond in nested_conditionals if not (key in seen_nested or seen_nested.add(key))
    ]
    missing_toggles = list(dict.fromkeys(missing_toggles))
    non_nullable_clears = list(dict.fromkeys(non_nullable_clears))
    purge_conflicts = list(dict.fromkeys(purge_conflicts))

    return _conditional_messages(nested_conditionals, missing_toggles, non_nullable_clears, purge_conflicts)


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


_INTEGRITY_PREFIXES = ("sha256-", "sha384-", "sha512-")


@register(TAG)
def check_asset_registry(app_configs=None, **kwargs):
    """Validate SRI metadata on registered asset bundles."""
    messages = []
    for bundle in assets.get_registered():
        for asset in bundle.js + bundle.css:
            if asset.integrity is None:
                continue
            if not asset.integrity.startswith(_INTEGRITY_PREFIXES):
                messages.append(
                    Error(
                        f"Asset {asset.path!r} in bundle {bundle.key!r} has an invalid integrity value "
                        f"{asset.integrity!r}.",
                        hint="Use a sha256-/sha384-/sha512- prefixed hash, e.g. from: "
                        "openssl dgst -sha384 -binary FILE | openssl base64 -A",
                        id="crud_views.E330",
                    )
                )
            if not assets.is_external(asset.path):
                messages.append(
                    DjangoWarning(
                        f"Asset {asset.path!r} in bundle {bundle.key!r} sets integrity on a same-origin static path.",
                        hint="SRI is meant for external URLs; on own static files it breaks on every asset "
                        "edit and adds no security value. Remove the integrity attribute.",
                        id="crud_views.W332",
                    )
                )
    return messages
