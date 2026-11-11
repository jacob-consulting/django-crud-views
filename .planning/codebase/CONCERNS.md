---
last_mapped_commit: 8eb29692c0f41a919593a05bfbcb9e7426efe2bd
last_mapped_at: 2026-11-11
---
# Codebase Concerns

**Analysis Date:** 2026-11-11

## Tech Debt

**Settings snapshot at module import:**
- Issue: `CrudViewsSettings` field defaults read Django settings in the model class body, and the template-tag registration decorators capture `theme_path`. `override_settings()` does not refresh these captured values, though some settings such as label-mode defaults are deliberately read at call time.
- Files: `src/crud_views/lib/settings.py`, `src/crud_views/templatetags/crud_views.py`
- Impact: applications and tests cannot switch startup-captured CRUD settings or registered template paths dynamically after imports.
- Fix approach: keep startup-only configuration explicit; make a setting lazy or respond to `setting_changed` only when runtime reconfiguration is a demonstrated requirement.

**No-op public management command:**
- Issue: `crud_views_show` is registered, but `handle()` only contains `pass` and a placeholder comment.
- Files: `src/crud_views/management/commands/crud_views_show.py`
- Impact: `manage.py help` advertises a command that produces no output.
- Fix approach: implement ViewSet/URL inspection or remove the command.

**Large central modules concentrate unrelated behavior:**
- Files: `src/crud_views/lib/view/base.py` (1229 lines), `src/crud_views/templatetags/crud_views.py` (667), `src/crud_views/lib/view/buttons.py` (599), `src/crud_views/lib/ancestors.py` (607), `src/crud_views/lib/formsets/formsets.py` (544), `src/crud_views/lib/viewset/__init__.py` (532)
- Impact: shared changes have broad regression surfaces; the base view and ancestor modules have grown beyond their sizes in the previous map.
- Fix approach: extract cohesive subsystems behind existing public APIs only when a concrete maintenance need justifies the added abstraction.

**Ancestor authorization spans several runtime layers:**
- Issue: authorization policy and resolution cross `ancestors.py`, `ancestor_db.py`, `ancestor_policy.py`, ViewSet hooks, breadcrumbs, resource loading, delete/manage views, polymorphic creation and Guardian adapters. Global policy also has three settings maps.
- Files: `src/crud_views/lib/ancestors.py`, `src/crud_views/lib/ancestor_db.py`, `src/crud_views/lib/ancestor_policy.py`, `src/crud_views/lib/viewset/__init__.py`, `src/crud_views_guardian/lib/ancestors.py`
- Impact: changes can alter request order, database routing, visibility and permission behavior across endpoint types.
- Fix approach: preserve the opt-in bounded policy model and exercise the focused `tests/test1/test_ancestor_*.py` coverage for query costs, database routing, Guardian, migration and redirects when changing it.

**Runtime contracts use Python assertions:**
- Issue: public/configuration preconditions and type checks use `assert`, which Python removes under `-O`; examples include permission-map lookup in `CrudViewPermissionRequiredMixin`, workflow state configuration, and Guardian context input checks.
- Files: `src/crud_views/lib/view/base.py`, `src/crud_views_workflow/lib/mixins.py`, `src/crud_views_guardian/lib/mixins.py`, `src/crud_views_guardian/lib/views.py`, `src/crud_views_polymorphic/lib/utils.py`, `src/crud_views/lib/formsets/formsets.py`
- Impact: invalid configuration or unexpected inputs can fail later with less direct errors in optimized Python. No authorization bypass is established by the current evidence.
- Fix approach: use explicit exceptions or Django checks for caller/configuration contracts; retain assertions for internal invariants.

## Known Bugs

**Polymorphic create with unknown or unconfigured content-type ids:**
- Symptoms: `polymorphic_model` lets `ContentType.DoesNotExist` escape for an unknown id. A valid but unconfigured subtype reaches `get_form_class()` and raises `ValueError`; its message refers to `self.object.__class__` during create-form selection, which can identify `NoneType` instead of the requested subtype.
- Files: `src/crud_views_polymorphic/lib/utils.py`, `src/crud_views_polymorphic/lib/create.py`, `src/crud_views_polymorphic/lib/create_select.py`
- Trigger: request a direct polymorphic-create URL using a nonexistent content-type id or a model absent from `polymorphic_forms`.
- Workaround: expose only the content types offered by the configured selector. Fix by converting missing/unconfigured types to a deliberate 404 or form error and reporting the resolved model accurately.

## Security Considerations

No distinct security defect is confirmed by the current evidence. Permission checks, including ancestor and Guardian paths, remain fragile cross-cutting code; use their request-level regression suites when changing them (see `tests/test1/test_ancestor_*.py`, `tests/test1/test_guardian.py`, and `tests/test1/test_authorization_matrix.py`).

## Performance Bottlenecks

**Delete preview limit does not bound cascade inspection:**
- Problem: `cv_delete_preview_limit` caps the entries selected for display only after cascade inspection and permission filtering have completed.
- Files: `src/crud_views/lib/views/delete.py`, `src/crud_views/lib/deletion.py`, `tests/test1/test_delete_preview_limit.py`
- Cause: `_cv_inspect_deletion()` runs before `_cv_select_delete_preview()` applies the limit.
- Improvement path: treat the setting as a display limit; profile real cascades before introducing a separately bounded inspection contract.

**Guardian checks may repeat for rendered objects and actions:**
- Files: `src/crud_views_guardian/lib/mixins.py`, `src/crud_views_guardian/lib/views.py`, `src/crud_views/lib/view/buttons.py`, `src/crud_views/lib/views/card.py`
- Cause: permission checks can be invoked while building each object's visible actions; request-scoped caching exists for ancestor checks, but the regular object-action path constructs checkers in its own calls.
- Improvement path: profile large list/card pages and consider request-scoped checker reuse if query counts are material. `tests/test1/test_ancestor_costs.py` pins current ancestor-query budgets.

## Fragile Areas

**ViewSet registration, routing and metaclass integration:**
- Files: `src/crud_views/lib/view/base.py`, `src/crud_views/lib/viewset/__init__.py`, `src/crud_views/lib/viewset/path_regs.py`, `src/crud_views/checks.py`
- Why fragile: views register during class construction; URL behavior depends on the shared registry, parent chain, PK shape and startup checks.
- Safe modification: preserve the import-safety boundary documented in `src/crud_views/lib/resource.py`; cover nested URLs and startup checks for affected combinations.
- Test coverage: broad request and system-check coverage exists in `tests/test1/`.

**Template, theme and header-icon compatibility surface:**
- Files: `src/crud_views/lib/button_classes.py`, `src/crud_views/lib/view/button_data.py`, `src/crud_views/lib/icons.py`, `src/crud_views/lib/view/base.py`, `src/crud_views/templates/crud_views/`, `src/crud_views/static/crud_views/js/`
- Why fragile: themes consume class keys, button context, icons, template variables and JS adapters as a connected contract. Phase 06.23 also intentionally changes `cv_icon_header=""` from ViewSet inheritance to suppression.
- Safe modification: consumers that used the empty string to inherit must switch to `None` or `Icon.VIEWSET_DEFAULT`; `Icon.NONE` is the readable suppression value. The Breaking entry and before/after instructions are in `CHANGELOG.md` and `docs/migrating-1.0.md#explicit-header-icon-suppression`. Preserve custom header content independently of icon choice.
- Test coverage: Phase 06.23 verification reports 13/13 truths, with 317 focused tests and 12,301 full-suite tests recorded as passing; the example-theme fragment is rendered, but external theme installations are not certified.

**Nested formset rendering and persistence:**
- Files: `src/crud_views/lib/formsets/formsets.py`, `src/crud_views/lib/formsets/render_tree.py`, `src/crud_views/lib/formsets/mixins.py`, `src/crud_views/lib/formsets/inline_formset.py`
- Why fragile: management forms, indexes, save order and validation errors must stay aligned between server rendering and JavaScript cloning.
- Safe modification: cover GET, invalid POST, deletion, nested indexes and transaction behavior.
- Test coverage: focused formset tests are in `tests/test1/test_formsets*.py` and `tests/test1/test_fragment_authorization.py`.

**Opt-in compact formset projection:**
- Files: `src/crud_views/lib/formsets/compact.py`, `src/crud_views/lib/formsets/render_tree.py`, `src/crud_views/templates/crud_views/formsets/compact_headings.html`, `src/crud_views/static/crud_views/css/formset.css`, `src/crud_views/static/crud_views/js/formset.js`
- Why fragile: compact layout derives a shared schema from request-time form metadata, projects hidden/control field feedback into row owners, and shares geometry rules with nested rendering and dynamic row cloning. These are opt-in APIs; classic helper dispatch remains a separate path.
- Safe modification: keep compact metadata query-free and index-independent, preserve exact visible-field/schema validation and hidden-error ownership, and verify actual fragment lifecycle plus nested compact/classic combinations. See `tests/test1/test_formsets_compact.py`, `tests/js/formset.test.js`, and `tests/js-integration/formset.test.js`.
- Test coverage: Phase 06.24 records focused, browser, docs, and compatibility replay evidence in `.planning/phases/06.24-opt-in-compact-formsets-shared-desktop-headings-and-nested-m/06.24-VERIFICATION.md` and `06.24-COMPATIBILITY.md`.

**Accepted compact-formset support boundaries (Phase 06.24):**
- Issue: compact metadata requires constructors and `get_form_kwargs(None)` to be query-free and independent of a live row index; changing compact columns in `add_fields()` is unsupported. Compact polymorphic declarations reject explicitly. Password inputs and textareas are unsupported compact columns; configured custom widgets/templates outside the documented stock set are rejected.
- Files: `src/crud_views/lib/formsets/compact.py`, `docs/reference/formsets.md`, `.planning/phases/06.24-opt-in-compact-formsets-shared-desktop-headings-and-nested-m/06.24-02-SUMMARY.md`
- Impact: these constraints exclude some custom formset construction and field rendering patterns from compact mode, while classic rendering remains available. They are documented product boundaries, not known defects.
- Fix approach: retain/document the bounded contract; expand support only with a concrete consumer need and a query-safe metadata design. The Vite native config-loader ESM warning recorded in `06.24-03-SUMMARY.md` is a pre-existing test-harness warning, accepted as outside compact presentation scope.

**Workflow permission and transition helper boundaries:**
- Files: `src/crud_views_workflow/lib/execution.py`, `src/crud_views_workflow/lib/views.py`, `src/crud_views_workflow/lib/mixins.py`, `docs/reference/workflow_view.md`
- Why fragile: `run_transition()` requires a persisted actor/object on the selected write alias; direct django-fsm calls bypass helper validation/history, and `workflow_check_transition()` is business validation rather than authorization. Page access and transition permissions are independent.
- Safe modification: route transitions through the documented helper and keep page/transition permission checks distinct.
- Test coverage: request-level coverage exists in `tests/test1/test_workflow_permissions.py` and `tests/test1/test_workflow_execution.py`; concurrency and Guardian/nested-object combinations are not certified.

**Snippet parent resolution and documentation boundary:**
- Files: `src/crud_views/lib/view/base.py`, `docs/reference/templates.md`, `tests/test1/test_snippet_context.py`, `tests/test1/test_snippet_docs.py`
- Why fragile: `parent_object` is lazy and resolves through Django template evaluation; the docs' direct-render 404 statement does not cover operators such as `{% if parent_object %}`, whose variable-resolution error handling can suppress exceptions. `cv_assert_parent()` also interpolates undefined `self.cv_name` in its assertion message on a top-level ViewSet and repeats the same assertion in `cv_get_parent_object()`.
- Safe modification: document/test direct variable access separately from operator expressions; replace the undefined name and duplicate guard with one explicit top-level error path.
- Test coverage: direct lazy resolution and missing-parent 404 are covered, as is filter-header context (`tests/test1/test_snippet_context.py`); operator-expression behavior and top-level `cv_assert_parent()` are not covered.

**Object-detail migration and template ownership:**
- Files: `src/crud_views_object_detail/lib/conf.py`, `src/crud_views_object_detail/lib/resolvers.py`, `src/crud_views_object_detail/templatetags/crud_views_object_detail.py`, `docs/migrating-1.0.md`
- Why fragile: model-derived help defaults off and scalar choices display labels; copied value templates keep their own behavior until migrated.
- Safe modification: use documented help restoration or `choices_display=False` where needed; treat cached settings as startup configuration.
- Test coverage: built-in configuration and rendering paths are exercised in `tests/test1/od/`; third-party copied templates are not.

## Scaling Limits

**Resource lookup and list materialization:**
- Current capacity: `Resource.cv_get_items()` returns a plain list and the default `cv_get_item()` scans it linearly.
- Limit: large remote datasets incur full-read memory and O(n) lookup.
- Scaling path: override item lookup for sources with direct key access; add pagination/source-native lookup only if large remote collections become a supported use case.

## Dependencies at Risk

**Django 4.2 support floor:**
- Risk: Django 4.2 remains the declared package floor and appears in the supported-version test matrix.
- Impact: the oldest compatibility line increases maintenance and release-verification work.
- Migration plan: decide whether 1.0 retains this floor and update `pyproject.toml`, `noxfile.py`, and migration guidance together if it changes.

## Missing Critical Features

None independently confirmed.

## Test Coverage Gaps

**Invalid polymorphic content-type URL cases:**
- What's not tested: direct create with nonexistent content-type ids or existing but unconfigured subtype ids.
- Files: `src/crud_views_polymorphic/lib/utils.py`, `src/crud_views_polymorphic/lib/create.py`, `tests/test1/test_polymorphic.py`
- Risk: uncaught lookup/form-selection exceptions return server errors instead of a controlled response.
- Priority: High

**Custom user model without `username` in manage view:**
- What's not tested: `CRUD_VIEWS_MANAGE_SHOW_USERS=True` with an email-only user model; current query names `username` directly.
- Files: `src/crud_views/lib/views/manage.py`, `tests/test1/test_manage.py`
- Risk: Django raises `FieldError` when the configured user model has no `username` field.
- Priority: Medium

**Third-party theme contract compatibility:**
- What's not tested: consumer overrides across template variables, class keys, icons and JS adapters; phase 06.23 tests the shipped example theme fragment but not separately installed consumer themes.
- Files: `src/crud_views/templates/crud_views/`, `src/crud_views/static/crud_views/js/`, `docs/development/stability.md`
- Risk: extension breakage may escape the built-in template suite.
- Priority: Medium

**Snippet operator/error and changelog-guard edge cases (Phase 06.21 review):**
- What's not tested or robustly guarded: parent lookup inside Django `{% if %}` operator expressions, and resilience of the snippet documentation test to unrelated later changelog mentions of #339. The filter-header coverage finding from that review is resolved by `test_filter_header_snippet_sees_view_and_parent_object`.
- Files: `docs/reference/templates.md`, `tests/test1/test_snippet_context.py`, `tests/test1/test_snippet_docs.py`
- Risk: docs can overstate 404 behavior for operator expressions; the changelog test can fail due to unrelated edits or section movement.
- Priority: Low

**Human acceptance and supported-environment coverage:**
- What's not tested: Phase 06.23 has automated local evidence only on Python 3.12.3 / Django 6.1.2; no additional version matrix, downstream-theme installation, browser appearance or assistive-technology evaluation is claimed. The Phase 06.17 review also excluded other-browser, assistive-technology and visual acceptance.
- Files: `.planning/phases/06.23-explicit-header-icon-suppression-with-icon-constants-329/06.23-VERIFICATION.md`, `.planning/phases/06.23-explicit-header-icon-suppression-with-icon-constants-329/06.23-REVIEW.md`, `.planning/phases/06.17-object-detail-open-the-first-accordion-group-and-initialize/06.17-UI-REVIEW.md`
- Risk: automated pass results do not establish behavior on other supported combinations, consumer themes or assistive technologies.
- Priority: Low

**Compact formset consumer-extension and unsupported-hook cases:**
- What's not tested: arbitrary third-party form widgets/templates, compact-column mutation in `add_fields()`, query-issuing constructors/`get_form_kwargs(None)`, and compact polymorphic forms are outside the documented support contract; consumer-specific custom themes are not exhaustively tested.
- Files: `docs/reference/formsets.md`, `src/crud_views/lib/formsets/compact.py`, `.planning/phases/06.24-opt-in-compact-formsets-shared-desktop-headings-and-nested-m/06.24-COMPATIBILITY.md`
- Risk: an application opting into compact mode with an unsupported field or metadata hook receives configuration failure or behavior outside the supported contract.
- Priority: Low; documentation and explicit validation define the current boundary.

---

*Concerns audit: 2026-11-11*
