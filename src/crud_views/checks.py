import dataclasses
from contextlib import suppress

from django.core.checks import Error, register
from django.core.checks import Warning as DjangoWarning
from django.core.exceptions import FieldDoesNotExist, ImproperlyConfigured

from crud_views.lib import assets
from crud_views.lib import ordered as ordered_helper
from crud_views.lib import pipeline as pipeline_helper
from crud_views.lib.ancestors import (
    _action_declaration_problems,
    _AncestryError,
    _concrete_opts,
    _declared_permission_keys,
    _has_model_vocabulary,
    _requirement_source,
    _selected_gates,
    _validate_ancestor_structure,
    _walk_ancestors,
)
from crud_views.lib.button_classes import button_class_check_messages
from crud_views.lib.conditional.group import ConditionalGroupFormMixin, resolve_conditional_empty_value
from crud_views.lib.formsets.formsets import FormSet
from crud_views.lib.icons import ICON_VALUE_HINT, icon_check_messages, is_icon_value, unregistered_prefix
from crud_views.lib.settings import crud_views_settings
from crud_views.lib.view import CrudViewPermissionRequiredMixin
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


def _ancestor_structure_messages(viewsets, *, completed: bool = True) -> list:
    """viewset.E266 for every nested ViewSet whose declared ancestry cannot be walked or expressed: a cycle, an
    unregistered parent or an unsupported relationship. Declarations and model metadata only — no database.

    A Resource parent is not repeated here: the owning child ViewSet already reports that edge once as
    viewset.E261 (ViewSet.checks()). An unregistered parent may still be a valid forward reference until the
    registry is complete, so it is reported only when ``completed``. URL construction and requests raise
    ImproperlyConfigured for every kind regardless.
    """
    messages = []
    for viewset in viewsets:
        if viewset.parent is None:
            continue
        try:
            _validate_ancestor_structure(viewset)
        except _AncestryError as exc:
            if exc.kind == "resource_parent" or (exc.kind == "missing" and not completed):
                continue
            messages.append(
                Error(
                    str(exc),
                    hint="Fix the ParentViewSet declaration (name, attribute, many_to_many_through_attribute).",
                    obj=viewset,
                    id="viewset.E266",
                )
            )
    return messages


def _ancestor_action_messages(viewsets) -> list:
    """viewset.E267 (an ``ancestor_policy.actions`` key that is not literally registered) and viewset.E268 (a
    nested unclassified endpoint without its exact entry). Needs a completed registry; no database."""
    hints = {
        "E267": "Use the exact registered endpoint key; navigation aliases such as list -> card do not count.",
        "E268": "Generic actions, custom forms and workflow views need a complete ancestor permission pair.",
    }
    return [
        Error(message, hint=hints[code], obj=viewset, id=f"viewset.{code}")
        for viewset in viewsets
        for code, message in _action_declaration_problems(viewset)
    ]


def _permission_key_messages(viewsets) -> list:
    """viewset.E269 for undeclared ``cv_permission`` keys on core PermissionRequired views.
    Read only the concrete model's declared permissions, never the database. Resources belong
    to E260 and an unset key belongs to E202; other providers have their own runtime maps.
    """
    messages = []
    for viewset in viewsets:
        if not _has_model_vocabulary(viewset):
            continue
        declared = _declared_permission_keys(viewset.model)
        opts = _concrete_opts(viewset.model)
        for key, view_class in viewset.get_all_views().items():
            if not issubclass(view_class, CrudViewPermissionRequiredMixin):
                continue
            permission = view_class.cv_permission
            if permission is None or permission in declared:
                continue
            messages.append(
                Error(
                    f"cv_permission {permission!r} of view {key!r} is not declared on model {opts.label}",
                    hint=(
                        f'add ("{permission}_{opts.model_name}", "...") to {opts.object_name}.Meta.permissions, '
                        "or use the non-PermissionRequired view variant"
                    ),
                    obj=viewset,
                    id="viewset.E269",
                )
            )
    return messages


def _ancestor_pair_messages(viewsets) -> list:
    """viewset.E269 for undeclared ancestor Read, Write and ``actions`` pair keys.
    Mirror the request engine's selection: ``nearest`` on the nearest protected ancestor,
    ``higher`` on farther selected ancestors. Guardian and Resource checked ViewSets and
    ancestors are skipped; ``none`` ancestors are never selected. No database access.
    """
    messages = []
    for viewset in viewsets:
        if viewset.parent is None or not _has_model_vocabulary(viewset):
            continue
        try:
            chain = _walk_ancestors(viewset)
        except _AncestryError:
            continue  # E266 owns structural errors.
        selected = _selected_gates(viewset, chain)
        seen = set()
        declared = {}
        for view_class in viewset.get_all_views().values():
            try:
                source, pair = _requirement_source(view_class)
            except ImproperlyConfigured:
                continue  # E268 owns an unclassified endpoint without an actions entry.
            for index, side in selected.items():
                ancestor = chain[index][1]
                if not _has_model_vocabulary(ancestor):
                    continue
                if ancestor.name not in declared:
                    declared[ancestor.name] = _declared_permission_keys(ancestor.model)
                key = getattr(pair, side)
                if key in declared[ancestor.name] or (key, ancestor.name) in seen:
                    continue
                seen.add((key, ancestor.name))
                opts = _concrete_opts(ancestor.model)
                messages.append(
                    Error(
                        f"ancestor permission key {key!r} ({source}.{side}) of ViewSet {viewset.name!r} "
                        f"is not declared on model {opts.label}",
                        hint=(
                            f'declare ("{key}_{opts.model_name}", "...") in {opts.object_name}.Meta.permissions, '
                            f"or change the pair on ViewSet {viewset.name!r}"
                        ),
                        obj=viewset,
                        id="viewset.E269",
                    )
                )
    return messages


def _url_configuration_loaded() -> bool:
    """The readiness barrier of the completion-dependent ancestor checks.

    Import the configured ROOT_URLCONF and every included URLconf through Django's own resolver (visiting each
    resolver once), so view modules that only the URLconf imports have registered their views. True when that
    completed; False without ROOT_URLCONF, or when the import failed or is still in progress (a check run
    during URLconf import) — Django's own URL checks report such failures. Nothing is remembered between calls.
    """
    from django.conf import settings
    from django.urls import URLResolver, get_resolver

    if not getattr(settings, "ROOT_URLCONF", None):
        return False
    pending, seen = [get_resolver()], set()
    try:
        while pending:
            resolver = pending.pop()
            if id(resolver) in seen:
                continue
            seen.add(id(resolver))
            pending.extend(pattern for pattern in resolver.url_patterns if isinstance(pattern, URLResolver))
    except Exception:  # any import failure means "not completed", never a misleading missing-action error
        return False
    return True


@register(TAG)
def check_ancestor_declarations(app_configs=None, **kwargs):
    """Ancestor structure and action declarations of every registered nested ViewSet (phase 06.18).

    Cycles and unsupported relationships are always reported. Unregistered parents, unregistered action keys
    and missing custom-endpoint entries depend on a completed registry: they are checked only after the
    configured URLconf (and everything it includes) has been imported; otherwise they are deferred. Runtime
    guards enforce all of them on the actual request regardless.
    Undeclared ``cv_permission`` and ancestor pair keys (viewset.E269) are checked against the
    respective model's declared permissions in the same completed-registry pass.
    """
    completed = _url_configuration_loaded()
    with _REGISTRY_LOCK:
        viewsets = list(_REGISTRY.values())
    messages = _ancestor_structure_messages(viewsets, completed=completed)
    if completed:
        messages += _ancestor_action_messages(viewsets)
        messages += _permission_key_messages(viewsets)
        messages += _ancestor_pair_messages(viewsets)
    return messages


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


def _conditional_messages(nested_conditionals, missing_toggles, unsupported_clears, purge_conflicts=()):
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
    for form_name, toggle, field in unsupported_clears:
        messages.append(
            Error(
                f"Conditional group '{toggle}' field '{field}' on form '{form_name}' has no supported "
                "automatic empty value.",
                hint="Configure empty_values explicitly for this field.",
                id="crud_views.E312",
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
    unsupported_clears: list = dataclasses.field(default_factory=list)
    purge_conflicts: list = dataclasses.field(default_factory=list)
    inspected_forms: set = dataclasses.field(default_factory=set)


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
    _collect_form_findings(getattr(formset.klass, "form", None), findings)
    if formset.conditional is not None:
        if is_top:
            _check_top_level_conditional(formset, key, form_class, available_toggles, findings)
        else:
            findings.nested_conditionals.append((key, formset.conditional))
    for ckey, child in formset.children.items():
        _walk_formset(child, f"{key}-{ckey}", False, form_class, available_toggles, findings)


def _collect_group_findings(form_class, groups, declared, findings):
    model = getattr(getattr(form_class, "_meta", None), "model", None)
    for group in groups:
        tname = group.toggle.field_name()
        if tname not in declared:
            findings.missing_toggles.append((form_class.__name__, tname))
        for name in group.fields:
            field = form_class.base_fields.get(name)
            if field is None or field.disabled:
                continue
            model_field = None
            if model is not None:
                with suppress(FieldDoesNotExist):
                    model_field = model._meta.get_field(name)
            try:
                resolve_conditional_empty_value(field, model_field, group, name)
            except ImproperlyConfigured:
                findings.unsupported_clears.append((form_class.__name__, tname, name))


def _form_toggle_names(form_class):
    """Return only this form's declared and actually injected toggle names."""
    declared = set(getattr(form_class, "base_fields", {}))
    if form_class is not None and issubclass(form_class, ConditionalGroupFormMixin):
        declared.update(g.toggle.field_name() for g in form_class.cv_conditional_groups if g.toggle.inject)
    return declared


def _collect_form_findings(form_class, findings):
    if form_class is None or form_class in findings.inspected_forms:
        return
    findings.inspected_forms.add(form_class)
    groups = getattr(form_class, "cv_conditional_groups", ())
    _collect_group_findings(form_class, groups, _form_toggle_names(form_class), findings)


def _collect_view_findings(view, findings):
    form_class = getattr(view, "form_class", None)
    _collect_form_findings(form_class, findings)

    formsets = getattr(view, "cv_formsets", None)
    if formsets is not None:
        for key, fs in formsets.items():
            _walk_formset(fs, key, True, form_class, _form_toggle_names(form_class), findings)


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
    unsupported_clears = list(dict.fromkeys(findings.unsupported_clears))
    purge_conflicts = list(dict.fromkeys(findings.purge_conflicts))

    return _conditional_messages(nested_conditionals, missing_toggles, unsupported_clears, purge_conflicts)


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


@register(TAG)
def check_icons(app_configs=None, **kwargs):
    """E350/E351/E354/E355/E356/W352 from the icon registry; W353/E356 for view and ViewSet icon attributes."""
    messages = icon_check_messages()

    with _REGISTRY_LOCK:
        viewsets = list(_REGISTRY.values())

    def warn(owner: str, attr: str, value: str, prefix: str) -> None:
        messages.append(
            DjangoWarning(
                f"{owner}.{attr} = {value!r} uses unregistered icon library prefix {prefix!r}.",
                hint="Register the library in CRUD_VIEWS_ICON_LIBRARIES.",
                id="crud_views.W353",
            )
        )

    def error(owner: str, attr: str, value) -> None:
        messages.append(Error(f"{owner}.{attr} = {value!r} is not a str.", hint=ICON_VALUE_HINT, id="crud_views.E356"))

    for viewset in viewsets:
        # ViewSet.icon_header is `str | None`, validated by pydantic: no E356 needed here
        prefix = unregistered_prefix(viewset.icon_header)
        if prefix is not None:
            warn(f"ViewSet {viewset.name!r}", "icon_header", viewset.icon_header, prefix)
        for key, view in viewset.get_all_views().items():
            owner = f"ViewSet {viewset.name!r} view {key!r}"
            for attr in ("cv_icon_action", "cv_icon_header"):
                value = getattr(view, attr, None)
                if not is_icon_value(value):
                    error(owner, attr, value)
                    continue
                prefix = unregistered_prefix(value)
                if prefix is not None:
                    warn(owner, attr, value, prefix)
    return messages


@register(TAG)
def check_button_classes(app_configs=None, **kwargs):
    """E360/E361/W362/E363/E364/E365 from the button class table."""
    return button_class_check_messages()
