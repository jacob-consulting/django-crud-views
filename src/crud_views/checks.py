import dataclasses

from django.core.checks import Error, register
from django.core.checks import Warning as DjangoWarning

from crud_views.lib import assets
from crud_views.lib import ordered as ordered_helper
from crud_views.lib import pipeline as pipeline_helper
from crud_views.lib.formsets.formsets import FormSet
from crud_views.lib.settings import crud_views_settings
from crud_views.lib.views.action_ordered import OrderedDownView, OrderedUpView
from crud_views.lib.viewset import _REGISTRY, _REGISTRY_LOCK, ViewSet

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
            if formsets is not None and any(_formset_uses_ordering(fs) for fs in formsets.values()):
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


@dataclasses.dataclass
class _ConditionalFindings:
    """Raw findings of check_conditional, collected across all registered views."""

    nested_conditionals: list = dataclasses.field(default_factory=list)
    missing_toggles: list = dataclasses.field(default_factory=list)
    non_nullable_clears: list = dataclasses.field(default_factory=list)
    purge_conflicts: list = dataclasses.field(default_factory=list)


def _purge_conflict(klass) -> str | None:
    """Why purge contradicts the formset class, or None if it doesn't."""
    if not klass.can_delete:
        return "can_delete=False"
    if klass.edit_only:
        return "edit_only=True"
    return None


def _check_top_level_conditional(formset, key, form_class, available_toggles, findings):
    conditional = formset.conditional
    if form_class is not None:
        tname = conditional.toggle.field_name()
        if tname not in available_toggles:
            findings.missing_toggles.append((form_class.__name__, tname))
    if conditional.on_off == "purge":
        conflict = _purge_conflict(formset.klass)
        if conflict:
            findings.purge_conflicts.append((key, conflict))


def _walk_formset(formset, key, is_top, form_class, available_toggles, findings):
    """Only top-level formsets may carry a conditional; recurse into children."""
    if formset.conditional is not None:
        if is_top:
            _check_top_level_conditional(formset, key, form_class, available_toggles, findings)
        else:
            findings.nested_conditionals.append((key, formset.conditional))
    for ckey, child in formset.children.items():
        _walk_formset(child, f"{key}-{ckey}", False, form_class, available_toggles, findings)


def _non_nullable_clears(model, group):
    """Group fields that clearing (toggle off) would set to an invalid empty value."""
    for fname in group.fields:
        try:
            mf = model._meta.get_field(fname)
        except Exception:
            continue
        if not (getattr(mf, "null", False) and getattr(mf, "blank", False)) and fname not in group.empty_values:
            yield fname


def _collect_group_findings(form_class, groups, declared, findings):
    model = getattr(getattr(form_class, "_meta", None), "model", None)
    for group in groups:
        tname = group.toggle.field_name()
        if not group.toggle.inject and tname not in declared:
            findings.missing_toggles.append((form_class.__name__, tname))
        if model is not None:
            findings.non_nullable_clears.extend(
                (form_class.__name__, fname) for fname in _non_nullable_clears(model, group)
            )


def _collect_view_findings(view, findings):
    form_class = getattr(view, "form_class", None)
    declared = set(getattr(form_class, "base_fields", {}).keys()) if form_class else set()

    groups = getattr(form_class, "cv_conditional_groups", None) if form_class else None
    # ConditionalGroupFormMixin injects these at form init — the only
    # injection path there is; formset toggles are never auto-injected.
    group_injected = {g.toggle.field_name() for g in groups or [] if g.toggle.inject}

    formsets = getattr(view, "cv_formsets", None)
    if formsets is not None:
        for key, fs in formsets.items():
            _walk_formset(fs, key, True, form_class, declared | group_injected, findings)

    if groups:
        _collect_group_findings(form_class, groups, declared, findings)


@register(TAG)
def check_conditional(app_configs=None, **kwargs):
    """Validate ConditionalGroup / ConditionalFormSet declarations."""
    findings = _ConditionalFindings()

    with _REGISTRY_LOCK:
        viewsets = list(_REGISTRY.values())

    for viewset in viewsets:
        for view in viewset.get_all_views().values():
            _collect_view_findings(view, findings)

    # Create/Update views routinely share form_class + cv_formsets — report each
    # distinct finding once, not once per view.
    seen_nested = set()
    nested_conditionals = [
        (key, cond) for key, cond in findings.nested_conditionals if not (key in seen_nested or seen_nested.add(key))
    ]
    missing_toggles = list(dict.fromkeys(findings.missing_toggles))
    non_nullable_clears = list(dict.fromkeys(findings.non_nullable_clears))
    purge_conflicts = list(dict.fromkeys(findings.purge_conflicts))

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


def _pipeline_location(source) -> str:
    return f"PIPELINE[{pipeline_helper.SECTIONS[source.kind]!r}][{source.package!r}]"


def _check_cv_sources_args(lazies, known_keys) -> list:
    """W344 (js/css mismatch) and W343 (unknown bundle keys) for each cv_sources() package."""
    messages = []
    for source in lazies:
        lazy = source.sources
        where = _pipeline_location(source)
        if lazy.kind != source.kind:
            messages.append(
                DjangoWarning(
                    f"cv_sources({lazy.kind!r}) is used in {where}, a {source.kind} package.",
                    hint=f"Use cv_sources({source.kind!r}) there; pipeline would concatenate the files silently.",
                    id="crud_views.W344",
                )
            )
        messages.extend(
            DjangoWarning(
                f"cv_sources() in {where} names unknown asset bundle {key!r}.",
                hint=f"Known bundle keys: {', '.join(known_keys)}.",
                id="crud_views.W343",
            )
            for key in (*(lazy.keys or ()), *lazy.exclude)
            if key not in known_keys
        )
    return messages


def _check_bundled_coverage(lazies) -> list:
    """W340 (no cv_sources() at all) or W341 (local asset in no package) in bundled mode."""
    if not lazies:
        return [
            DjangoWarning(
                "CRUD_VIEWS_ASSETS_BUNDLED is on, but no PIPELINE package uses cv_sources(): local "
                "crud_views assets are delivered by nothing.",
                hint="Add cv_sources('js') / cv_sources('css') to your PIPELINE packages' source_filenames.",
                id="crud_views.W340",
            )
        ]
    return [
        DjangoWarning(
            f"Asset {row.path!r} (bundle {row.key!r}) is not in any "
            f"PIPELINE[{pipeline_helper.SECTIONS[row.kind]!r}] package.",
            hint=(
                "Bundled mode suppresses its tag; include the bundle in a cv_sources() call."
                if row.emit
                else "emit=False: delivered by nothing; include the bundle in a cv_sources() call."
            ),
            id="crud_views.W341",
        )
        for row in pipeline_helper.asset_rows()
        if not row.external and not row.bundled
    ]


def _check_mixed_bundles() -> list:
    """W345: in bundled mode a bundle mixing CDN and local entries cannot be bundled consistently."""
    messages = []
    for bundle in assets.iter_bundles():
        for kind in pipeline_helper.KINDS:
            entries = getattr(bundle, kind)
            external = [a for a in entries if assets.is_external(a.path)]
            if not external or len(external) == len(entries):
                continue
            consequence = (
                "bundle the CDN ones, so its local entries may load before them."
                if bundle.emit
                else "bundle the CDN ones and, with emit=False, no tag emits them: they are delivered by nothing."
            )
            messages.append(
                DjangoWarning(
                    f"Asset bundle {bundle.key!r} mixes CDN and local {kind} entries; pipeline cannot {consequence}",
                    hint="Switch the extension to a vendored/local mode. List the affected entries with: "
                    "manage.py cv_assets --external",
                    id="crud_views.W345",
                )
            )
    return messages


def _check_double_load(lazies) -> list:
    """W342: not bundled, but cv_sources() bundles assets the tags also emit."""
    return [
        DjangoWarning(
            f"cv_sources() in {_pipeline_location(source)} bundles assets that {{% cv_js %}}/{{% cv_css %}} also "
            "emit: they load twice.",
            hint="Set CRUD_VIEWS_ASSETS_BUNDLED = True.",
            id="crud_views.W342",
        )
        for source in lazies
        if any(entry.emit for entry in source.sources.registry_entries())
    ]


@register(TAG)
def check_asset_pipeline(app_configs=None, **kwargs):
    """Validate the django-pipeline integration (cv_sources / CRUD_VIEWS_ASSETS_BUNDLED)."""
    lazies = [s for s in pipeline_helper.pipeline_sources() if isinstance(s.sources, pipeline_helper.LazySources)]
    known_keys = [assets.CORE_KEY, *(bundle.key for bundle in assets.get_registered())]
    messages = _check_cv_sources_args(lazies, known_keys)
    if crud_views_settings.assets_bundled:
        messages += _check_bundled_coverage(lazies)
        messages += _check_mixed_bundles()
    else:
        messages += _check_double_load(lazies)
    return messages
