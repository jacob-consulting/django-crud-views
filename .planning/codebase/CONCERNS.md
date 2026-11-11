---
last_mapped_commit: 6c09417f8f15a93e0e39d8340ec05dba331e82fb
last_mapped_at: 2026-11-11
---
# Codebase Concerns

**Analysis Date:** 2026-11-11

## Tech Debt

**Startup-captured settings and template registration:**
- Issue: `CrudViewsSettings` defaults read Django settings during model definition, while template-tag registration captures the theme path. `override_settings()` cannot refresh those captured values after import; label-mode defaults are among settings read at call time.
- Files: `src/crud_views/lib/settings.py`, `src/crud_views/templatetags/crud_views.py`
- Impact: runtime changes to startup-captured configuration are not reflected in settings instances or registered template paths.
- Fix approach: keep startup-only settings explicit; add lazy evaluation or `setting_changed` handling only for a demonstrated runtime reconfiguration need.

**Placeholder public management command:**
- Issue: `crud_views_show` is registered with help text but `handle()` is a no-op.
- Files: `src/crud_views/management/commands/crud_views_show.py`
- Impact: invoking an advertised command produces no useful output.
- Fix approach: implement a bounded ViewSet/URL report or remove the command from the public command surface.

**Large central modules:**
- Issue: multiple shared modules concentrate substantial behavior: `base.py` (about 1,229 lines), `checks.py` (600), template tags (667), buttons (599), ancestors (607), formsets (546), and ViewSet registration (532).
- Files: `src/crud_views/lib/view/base.py`, `src/crud_views/checks.py`, `src/crud_views/templatetags/crud_views.py`, `src/crud_views/lib/view/buttons.py`, `src/crud_views/lib/ancestors.py`, `src/crud_views/lib/formsets/formsets.py`, `src/crud_views/lib/viewset/__init__.py`
- Impact: shared changes have broad regression surfaces and require navigating several responsibilities in large files.
- Fix approach: preserve the public APIs and extract cohesive subsystems only when a concrete maintenance need justifies the extra abstraction. Project decisions are constrained by developer maintainability; see `AGENTS.md` and `superpowers/notes/2026-11-04-opt-in-url-helper-decision.md`.

**Ancestor authorization crosses runtime layers:**
- Issue: ancestor policy and resolution span query helpers, ViewSet hooks, breadcrumbs, resource loading, deletion/manage views, and Guardian integration; policy can also be shaped by multiple settings maps.
- Files: `src/crud_views/lib/ancestors.py`, `src/crud_views/lib/ancestor_db.py`, `src/crud_views/lib/ancestor_policy.py`, `src/crud_views/lib/viewset/__init__.py`, `src/crud_views_guardian/lib/ancestors.py`
- Impact: changes can affect request ordering, database routing, visibility, permission decisions, and query count across endpoint types.
- Fix approach: retain the opt-in bounded policy model and use focused `tests/test1/test_ancestor_*.py` coverage for query budgets, routing, Guardian, migration, and redirects when changing it.

**Assertions used for caller/configuration contracts:**
- Issue: assertions enforce some public or configuration preconditions and disappear under optimized Python. Examples include permission-map lookup and workflow/Guardian configuration checks.
- Files: `src/crud_views/lib/view/base.py`, `src/crud_views_workflow/lib/mixins.py`, `src/crud_views_guardian/lib/mixins.py`, `src/crud_views_guardian/lib/views.py`, `src/crud_views_polymorphic/lib/utils.py`, `src/crud_views/lib/formsets/formsets.py`
- Impact: invalid configuration may fail later or less clearly under `python -O`; current evidence does not establish an authorization bypass.
- Fix approach: use explicit exceptions or Django system checks for caller/configuration contracts, retaining assertions for internal invariants.

## Known Bugs

**Polymorphic create with invalid or unconfigured content type:**
- Symptoms: an unknown content-type id lets `ContentType.DoesNotExist` escape; a valid but unconfigured subtype raises `ValueError`, whose message refers to `self.object.__class__` and can report `NoneType` during create-form selection.
- Files: `src/crud_views_polymorphic/lib/utils.py`, `src/crud_views_polymorphic/lib/create.py`, `src/crud_views_polymorphic/lib/create_select.py`
- Trigger: directly request a polymorphic-create URL with a nonexistent content-type id or a model missing from `polymorphic_forms`.
- Workaround: expose only selector-provided types. A targeted fix could turn invalid/unconfigured types into a deliberate 404 or form error and report the resolved model.

## Security Considerations

No distinct security defect is confirmed by current evidence. Permission and ancestor paths are cross-cutting and should be changed with request-level regressions, including `tests/test1/test_ancestor_*.py`, `tests/test1/test_guardian.py`, and `tests/test1/test_authorization_matrix.py`.

## Performance Bottlenecks

**Delete preview limit does not bound cascade inspection:**
- Problem: `cv_delete_preview_limit` limits displayed entries after cascade inspection and permission filtering have completed.
- Files: `src/crud_views/lib/views/delete.py`, `src/crud_views/lib/deletion.py`, `tests/test1/test_delete_preview_limit.py`
- Cause: `_cv_inspect_deletion()` runs before `_cv_select_delete_preview()` applies the display limit.
- Improvement path: treat the setting as a display cap; profile real cascades before adding a separately bounded inspection contract.

**Guardian object-action checks can repeat:**
- Problem: rendered objects and actions may each trigger permission checks; request-scoped caching exists for ancestor checks but regular object-action paths instantiate their own checkers.
- Files: `src/crud_views_guardian/lib/mixins.py`, `src/crud_views_guardian/lib/views.py`, `src/crud_views/lib/view/buttons.py`, `src/crud_views/lib/views/card.py`
- Cause: permission checks are reached during construction of visible actions for objects.
- Improvement path: profile large list/card pages and consider request-scoped checker reuse only if query counts are material; `tests/test1/test_ancestor_costs.py` pins current ancestor query budgets.

## Fragile Areas

**ViewSet registration, URL routing, and metaclass integration:**
- Files: `src/crud_views/lib/view/base.py`, `src/crud_views/lib/viewset/__init__.py`, `src/crud_views/lib/viewset/path_regs.py`, `src/crud_views/checks.py`
- Why fragile: views register during class construction and URL behavior depends on shared registries, parent chains, PK shape, and startup checks.
- Safe modification: preserve the import-safety boundary in `src/crud_views/lib/resource.py`; cover nested URLs and startup checks for affected combinations.
- Test coverage: broad request and system-check coverage is in `tests/test1/`.

**Templates, themes, and header-icon compatibility:**
- Files: `src/crud_views/lib/button_classes.py`, `src/crud_views/lib/view/button_data.py`, `src/crud_views/lib/icons.py`, `src/crud_views/lib/view/base.py`, `src/crud_views/templates/crud_views/`, `src/crud_views/static/crud_views/js/`
- Why fragile: themes consume class keys, button context, icons, template variables, and JavaScript adapters as a connected contract. The empty `cv_icon_header` value explicitly suppresses inheritance; consumers that previously used it to inherit must use `None` or `Icon.VIEWSET_DEFAULT`, while `Icon.NONE` expresses suppression.
- Safe modification: preserve custom header content independently of icon choice and update the migration guidance in `CHANGELOG.md` and `docs/migrating-1.0.md` when changing the contract.
- Test coverage: built-in templates and the example theme are exercised; installed third-party themes are not certified (`docs/development/stability.md`).

**Nested formset rendering and persistence:**
- Files: `src/crud_views/lib/formsets/formsets.py`, `src/crud_views/lib/formsets/render_tree.py`, `src/crud_views/lib/formsets/mixins.py`, `src/crud_views/lib/formsets/inline_formset.py`
- Why fragile: management forms, indexes, save order, and validation errors must stay aligned across server rendering and JavaScript cloning.
- Safe modification: cover GET, invalid POST, deletion, nested indexes, and transaction behavior.
- Test coverage: `tests/test1/test_formsets*.py` and `tests/test1/test_fragment_authorization.py`.

**Opt-in compact formset projection:**
- Files: `src/crud_views/lib/formsets/compact.py`, `src/crud_views/lib/formsets/render_tree.py`, `src/crud_views/templates/crud_views/formsets/compact_headings.html`, `src/crud_views/static/crud_views/css/formset.css`, `src/crud_views/static/crud_views/js/formset.js`
- Why fragile: compact layout derives shared schema from request-time form metadata, projects hidden/control feedback to row owners, and shares geometry rules with nested rendering and dynamic cloning. The mode is opt-in; classic helper dispatch remains separate.
- Safe modification: keep metadata query-free and index-independent, preserve visible-field/schema validation and hidden-error ownership, and check fragment lifecycle plus nested compact/classic combinations. Phase 06.26 extends support only to exact stock `CheckboxInput` controls; custom widgets/templates retain their documented theme responsibility.
- Test coverage: `tests/test1/test_formsets_compact.py`, `tests/js/formset.test.js`, `tests/js-integration/formset.test.js`, and `tests/browser/compact-checkboxes.cjs` cover the package paths; Phase 06.26 evidence is recorded in `.planning/phases/06.26-issue-351/06.26-VERIFICATION.md`.

**Compact formset support boundary:**
- Issue: compact metadata requires constructors and `get_form_kwargs(None)` to be query-free and independent of a live row index; changing compact columns in `add_fields()` is unsupported. Compact polymorphic declarations reject explicitly. Password inputs, textareas, and custom widgets/templates beyond the documented stock set are unsupported.
- Files: `src/crud_views/lib/formsets/compact.py`, `docs/reference/formsets.md`, `.planning/phases/06.24-opt-in-compact-formsets-shared-desktop-headings-and-nested-m/06.24-COMPATIBILITY.md`
- Impact: these patterns cannot opt into compact mode; classic rendering remains available. This is a documented product boundary, not a defect.
- Fix approach: keep the bounded contract explicit and expand only for a demonstrated consumer need with a query-safe metadata design.

**Workflow permission and transition helper boundaries:**
- Files: `src/crud_views_workflow/lib/execution.py`, `src/crud_views_workflow/lib/views.py`, `src/crud_views_workflow/lib/mixins.py`, `docs/reference/workflow_view.md`
- Why fragile: `run_transition()` requires a persisted actor/object on the selected write alias; direct django-fsm calls bypass helper validation/history, and `workflow_check_transition()` is business validation rather than authorization. Page access and transition permissions are separate.
- Safe modification: route transitions through the documented helper and preserve independent page and transition permission checks.
- Test coverage: `tests/test1/test_workflow_permissions.py` and `tests/test1/test_workflow_execution.py`; concurrency and Guardian/nested-object combinations are not certified.

**Snippet parent resolution:**
- Files: `src/crud_views/lib/view/base.py`, `docs/reference/templates.md`, `tests/test1/test_snippet_context.py`, `tests/test1/test_snippet_docs.py`
- Why fragile: `parent_object` resolves lazily through Django template evaluation, whose variable-resolution handling can suppress exceptions inside operators such as `{% if parent_object %}`. `cv_assert_parent()` also uses assertions and is invoked redundantly from `cv_get_parent_object()`.
- Safe modification: document/test direct access separately from operator expressions; consolidate the duplicate guard if touching this path.
- Test coverage: direct lazy resolution, missing-parent 404, and filter-header context are covered; operator-expression behavior is not.

**Object-detail template migration:**
- Files: `src/crud_views_object_detail/lib/conf.py`, `src/crud_views_object_detail/lib/resolvers.py`, `src/crud_views_object_detail/templatetags/crud_views_object_detail.py`, `docs/migrating-1.0.md`
- Why fragile: model-derived help defaults off and scalar choices display labels; copied value templates keep their own behavior until migrated.
- Safe modification: use documented help restoration or `choices_display=False` where needed; treat cached settings as startup configuration.
- Test coverage: built-in configuration and rendering paths are exercised in `tests/test1/od/`; third-party copied templates are not.

## Scaling Limits

**Resource lookup and list materialization:**
- Current capacity: `Resource.cv_get_items()` returns a plain list and default `cv_get_item()` scans it linearly.
- Limit: large remote datasets require full-read memory and O(n) lookup.
- Scaling path: override item lookup for sources with direct key access; add pagination or source-native lookup only if large remote collections become supported.

## Dependencies at Risk

**Django 4.2 support floor:**
- Risk: Django 4.2 remains the declared package floor and is included in the supported-version test matrix.
- Impact: the oldest compatibility line increases maintenance and release-verification work.
- Migration plan: decide whether 1.0 retains this floor and update `pyproject.toml`, `noxfile.py`, and migration guidance together if it changes.

## Missing Critical Features

None independently confirmed.

## Test Coverage Gaps

**Invalid polymorphic content-type URLs:**
- What's not tested: direct create with nonexistent content-type ids or existing but unconfigured subtype ids.
- Files: `src/crud_views_polymorphic/lib/utils.py`, `src/crud_views_polymorphic/lib/create.py`, `tests/test1/test_polymorphic.py`
- Risk: uncaught lookup/form-selection exceptions can return server errors instead of a controlled response.
- Priority: High

**Custom user model without `username` in manage view:**
- What's not tested: `CRUD_VIEWS_MANAGE_SHOW_USERS=True` with an email-only user model; the query names `username` directly.
- Files: `src/crud_views/lib/views/manage.py`, `tests/test1/test_manage.py`
- Risk: Django raises `FieldError` when the configured user model has no `username` field.
- Priority: Medium

**Third-party theme contract:**
- What's not tested: consumer overrides across template variables, class keys, icons, and JavaScript adapters; built-in and example theme coverage does not certify installed external themes.
- Files: `src/crud_views/templates/crud_views/`, `src/crud_views/static/crud_views/js/`, `docs/development/stability.md`
- Risk: extension breakage may escape the built-in template suite.
- Priority: Medium

**Phase 06.26 visual sign-off advisories and environment scope:**
- What's not tested: browser evidence for checkbox behavior is retained at 390, 767, 768, and 1280px and UAT records acceptance, but that does not certify other browser engines, supported Python/Django combinations, or installed external themes. The actual Checklist example was exercised only on Python 3.12.3 / Django 6.1.2 with the Bootstrap pack.
- Files: `.planning/phases/06.26-issue-351/06.26-UI-REVIEW.md`, `.planning/phases/06.26-issue-351/06.26-VERIFICATION.md`, `.planning/phases/06.26-issue-351/06.26-UAT.md`
- Risk: visual/runtime differences outside the recorded environment are not established. The accepted UI review retains cramped Done-help wrapping at 768px and a long shared introduction on checklist pages; these are presentation advisories, not unresolved release blockers.
- Priority: Low

**Compact formset consumer extension hooks:**
- What's not tested: arbitrary third-party widgets/templates, compact-column mutation in `add_fields()`, query-issuing constructors/`get_form_kwargs(None)`, and compact polymorphic forms are outside the documented support contract.
- Files: `docs/reference/formsets.md`, `src/crud_views/lib/formsets/compact.py`, `.planning/phases/06.24-opt-in-compact-formsets-shared-desktop-headings-and-nested-m/06.24-COMPATIBILITY.md`
- Risk: an application opting into compact mode with unsupported hooks may receive validation errors or behavior outside the contract.
- Priority: Low; documentation and explicit validation define the boundary.

---

*Concerns audit: 2026-11-11*
