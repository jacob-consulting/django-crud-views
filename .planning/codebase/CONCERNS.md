---
last_mapped_commit: b9c8a9841b8a33aeedbb1aa9d92e04199ef7b424
last_mapped_at: 2026-11-21
---
<!-- refreshed: 2026-11-21 -->
# Codebase Concerns

**Analysis Date:** 2026-11-21

## Tech Debt

**Startup-captured settings and template registration:**
- Issue: `CrudViewsSettings` class defaults and template-tag registration capture some Django settings at import/startup. `override_settings()` does not refresh those values after import; selected label defaults are intentionally read at call time.
- Files: `src/crud_views/lib/settings.py`, `src/crud_views/templatetags/crud_views.py`
- Impact: changing startup-captured configuration during a process does not reconfigure the package.
- Fix approach: treat these as startup configuration. Add lazy evaluation or `setting_changed` handling only for a demonstrated supported runtime-reconfiguration use case.

**Placeholder public management command:**
- Issue: `crud_views_show` advertises a command but its `handle()` is a no-op.
- Files: `src/crud_views/management/commands/crud_views_show.py`
- Impact: invoking the command produces no report.
- Fix approach: implement a bounded ViewSet/URL report or remove the command from the advertised surface.

**Large central modules:**
- Issue: shared behavior remains concentrated in modules including `src/crud_views/lib/view/base.py`, `src/crud_views/lib/views/manage.py`, `src/crud_views_guardian/lib/views.py`, `src/crud_views/templatetags/crud_views.py`, `src/crud_views/checks.py`, `src/crud_views/lib/view/buttons.py`, `src/crud_views_guardian/lib/mixins.py`, `src/crud_views/lib/formsets/formsets.py`, `src/crud_views/lib/ancestors.py`, `src/crud_views/lib/viewset/__init__.py`, `src/crud_views/lib/manage_report.py`, and `src/crud_views/lib/icons.py`.
- Impact: edits to shared pathways have broad regression surfaces and require navigating multiple responsibilities.
- Fix approach: preserve public APIs and extract cohesive subsystems only for demonstrated maintenance needs. Apply the developer-maintainability constraint in `AGENTS.md` and `superpowers/notes/2026-11-04-opt-in-url-helper-decision.md`.

**Ancestor authorization crosses runtime layers:**
- Issue: policy and resolution span query helpers, ViewSet hooks, breadcrumbs, resources, deletion/manage views, and Guardian integration; settings and ViewSet policy can select different bounded behaviors.
- Files: `src/crud_views/lib/ancestors.py`, `src/crud_views/lib/ancestor_db.py`, `src/crud_views/lib/ancestor_policy.py`, `src/crud_views/lib/viewset/__init__.py`, `src/crud_views_guardian/lib/ancestors.py`
- Impact: changes can alter request ordering, database routing, visibility, permission decisions, or query counts across endpoint types.
- Fix approach: preserve the opt-in bounded policy model and run the focused `tests/test1/test_ancestor_*.py` suites for query budgets, routing, Guardian, migration, and redirects.

**Access tracing spans authorization owners and a synthetic dispatcher:**
- Issue: traces collect decisions from core, ancestor, Resource, manage, and Guardian paths, then dispatch a synthetic GET with a handler stub. The real request handler is not run.
- Files: `src/crud_views/lib/access_trace.py`, `src/crud_views/lib/access_trace_runner.py`, `src/crud_views/lib/ancestors.py`, `src/crud_views/lib/resource.py`, `src/crud_views/lib/views/manage.py`, `src/crud_views_guardian/lib/ancestors.py`, `src/crud_views_guardian/lib/mixins.py`
- Impact: a new gate can be absent from diagnostics unless its decision is recorded at the owning path. Arbitrary middleware effects, external side effects, extra database routing, host/header/body/method rules, and hidden custom super-call frames are outside the documented simulation contract; these are limitations, not confirmed defects.
- Fix approach: keep tracing default-off and tied to computed authorization results. Update `tests/test1/test_access_trace*.py` and `tests/test1/test_access_trace_grid.py` when supported decision owners change.

**Published access-trace and manage-report contracts:**
- Issue: command output and the `--schema` contract are Pydantic models whose field names, literals, and extra-field behavior are public compatibility surface.
- Files: `src/crud_views/lib/access_trace.py`, `src/crud_views/lib/access_trace_export.py`, `src/crud_views/lib/access_trace_runner.py`, `src/crud_views/lib/manage_report.py`, `src/crud_views/management/commands/cv_access.py`, `src/crud_views/management/commands/cv_manage_view.py`, `docs/reference/manage.md`
- Impact: model or literal changes can break consumers that validate or parse the documented JSON.
- Fix approach: update the models, docs, changelog, and `tests/test1/test_access_trace_contract.py`, `tests/test1/test_access_trace_docs.py`, and `tests/test1/test_manage_command_docs.py` together. Counts remain shape-validated integers by the accepted contract; adding numeric bounds requires an intentional schema change.

**Unresolved actor text output:**
- Issue: text output formats an unresolved non-anonymous actor as `None (pk None, inactive)` rather than identifying it as unresolved; JSON shape is unaffected.
- Files: `src/crud_views/management/commands/cv_access.py`, `src/crud_views/lib/access_trace_export.py`
- Impact: the human-readable diagnostic can mislead when actor resolution fails.
- Fix approach: render an explicit unresolved label when touching this output path.

**Assertions enforce some caller/configuration preconditions:**
- Issue: assertions in public-adjacent configuration paths disappear under optimized Python.
- Files: `src/crud_views/lib/view/base.py`, `src/crud_views_workflow/lib/mixins.py`, `src/crud_views_guardian/lib/mixins.py`, `src/crud_views_guardian/lib/views.py`, `src/crud_views_polymorphic/lib/utils.py`, `src/crud_views/lib/formsets/formsets.py`
- Impact: invalid configuration may fail later or less clearly under `python -O`; current evidence does not establish an authorization bypass.
- Fix approach: use explicit exceptions or Django system checks for caller/configuration contracts while retaining assertions for internal invariants.

## Known Bugs

**Polymorphic create with invalid or unconfigured content type:**
- Symptoms: an unknown content-type id propagates `ContentType.DoesNotExist`; a valid but unconfigured subtype raises `ValueError` with a message based on `self.object.__class__`, which can say `NoneType` during create-form selection.
- Files: `src/crud_views_polymorphic/lib/utils.py`, `src/crud_views_polymorphic/lib/create.py`, `src/crud_views_polymorphic/lib/create_select.py`
- Trigger: directly request a polymorphic-create URL with a nonexistent content-type id or a model missing from `polymorphic_forms`.
- Workaround: link only to selector-provided types. A targeted fix can convert invalid/unconfigured types to a deliberate 404 or form error and name the resolved model.

## Security Considerations

No distinct security defect is confirmed by current evidence. Keep navbar rendering and endpoint authorization separate: a navbar item is admitted for display using destination access/state checks, but a rendered link is not an authorization grant. The destination request still applies its own permission, ancestor, and queryset restrictions; a reachable nested host can display a child link whose destination returns 403/404. Relevant implementation and regressions are `src/crud_views/lib/navbar.py`, `src/crud_views/lib/viewset/__init__.py`, `tests/test1/test_navbar_permissions.py`, and `tests/test1/test_authorization_matrix.py`.

## Performance Bottlenecks

**Delete preview limit is a display cap, not an inspection cap:**
- Problem: `cv_delete_preview_limit` limits displayed rows after cascade inspection and permission filtering.
- Files: `src/crud_views/lib/views/delete.py`, `src/crud_views/lib/deletion.py`, `tests/test1/test_delete_preview_limit.py`
- Cause: `_cv_inspect_deletion()` runs before `_cv_select_delete_preview()` applies the display limit.
- Improvement path: document the display-only behavior; profile real cascades before designing a separately bounded inspection contract.

**Guardian object-action checks can repeat:**
- Problem: list/card objects and their actions may each perform permission checks. Ancestor checks have request-scoped caching, but ordinary object-action checks can construct separate checkers.
- Files: `src/crud_views_guardian/lib/mixins.py`, `src/crud_views_guardian/lib/views.py`, `src/crud_views/lib/view/buttons.py`, `src/crud_views/lib/views/card.py`
- Cause: permissions are consulted while visible actions are assembled for objects.
- Improvement path: profile large pages before considering checker reuse; preserve the query budgets in `tests/test1/test_ancestor_costs.py`.

**Navbar SQL is bounded only by the published fixture contract:**
- Problem: navbar admission may execute permission and ContentType reads; Guardian object-permission work remains visible. It is not a universal whole-page query budget or a guarantee for custom authorization hooks/backends.
- Files: `src/crud_views/lib/navbar.py`, `tests/test1/test_navbar_costs.py`, `docs/reference/navbar.md`
- Cause: admission invokes owner/destination access hooks; vocabulary and actor permission caches change the fixture's counts.
- Improvement path: preserve the isolated navbar-only measurements and exact per-cell expectations in the test/docs; the current parametrized test spans 120 combinations (composition, depth, placement, permission-vocabulary cache, and actor-cache state). Profile real application hooks before making broader claims. Existing request/object/ancestor queries are excluded by design.

**Resource manage-action admission check:**
- Problem: Resource list/detail views that inherit context actions may project the `manage` action. With manage mode enabled, its access check runs nested authorization and a developer-group membership query for each authenticated active actor, even when the default hide policy keeps it invisible; access-recorder mode can also record a `manage_gate` event.
- Files: `src/crud_views/lib/viewset/__init__.py`, `src/crud_views/lib/views/manage.py`, `src/crud_views/lib/settings.py`, `docs/reference/resources.md`
- Cause: Resource views share the manage action and gate with model ViewSets to preserve action parity.
- Improvement path: retain parity and profile real Resource list/detail pages before considering a cached gate or altered projection. Phase 06.35's model and Guardian manage-page baselines (9 and 21 statements) do not establish this separate Resource-path cost.

## Fragile Areas

**ViewSet registration, URL routing, and metaclass integration:**
- Files: `src/crud_views/lib/view/base.py`, `src/crud_views/lib/viewset/__init__.py`, `src/crud_views/lib/viewset/path_regs.py`, `src/crud_views/checks.py`
- Why fragile: views register during class construction; URLs depend on shared registries, parent chains, primary-key shape, and startup checks.
- Safe modification: preserve import-safety boundaries in `src/crud_views/lib/resource.py`; cover nested URLs and startup checks for affected combinations.
- Test coverage: request and system-check suites under `tests/test1/`.

**Templates, themes, and header-icon compatibility:**
- Files: `src/crud_views/lib/button_classes.py`, `src/crud_views/lib/view/button_data.py`, `src/crud_views/lib/icons.py`, `src/crud_views/lib/view/base.py`, `src/crud_views/templates/crud_views/`, `src/crud_views/static/crud_views/js/`
- Why fragile: themes consume class keys, button context, icons, template variables, and JavaScript adapters as a connected contract. Empty `cv_icon_header` suppresses inheritance; consumers that need inherited icons use `None` or `Icon.VIEWSET_DEFAULT`, and `Icon.NONE` suppresses explicitly.
- Safe modification: preserve custom header content independently of icon choice and update `CHANGELOG.md` and `docs/migrating-1.0.md` for contract changes.
- Test coverage: built-in and example themes are exercised; arbitrary installed third-party themes are not certified (`docs/development/stability.md`). Conditional/formset empty-default hooks and fragment ownership have coverage in `tests/test1/test_conditional_layout.py` and `tests/test1/test_formsets_compact.py`.

**Nested and compact formset rendering/persistence:**
- Files: `src/crud_views/lib/formsets/formsets.py`, `src/crud_views/lib/formsets/render_tree.py`, `src/crud_views/lib/formsets/mixins.py`, `src/crud_views/lib/formsets/inline_formset.py`, `src/crud_views/lib/formsets/compact.py`, `src/crud_views/templates/crud_views/formsets/compact_headings.html`, `src/crud_views/static/crud_views/css/formset.css`, `src/crud_views/static/crud_views/js/formset.js`
- Why fragile: management forms, indexes, save order, hidden/control feedback, dynamic cloning, and validation errors must stay aligned across nested server rendering and JavaScript.
- Safe modification: cover GET, invalid POST, deletion, nested indexes, transaction behavior, fragment lifecycle, and nested compact/classic combinations. Compact metadata must stay query-free and index-independent; changing columns in `add_fields()` is unsupported.
- Test coverage: `tests/test1/test_formsets*.py`, `tests/test1/test_fragment_authorization.py`, `tests/test1/test_formsets_compact.py`, `tests/js/formset.test.js`, `tests/js-integration/formset.test.js`, and `tests/browser/compact-checkboxes.cjs`. Compact custom widgets/templates outside the documented stock set, password inputs, textareas, and compact polymorphic forms are explicit product boundaries, not defects (`docs/reference/formsets.md`).

**Conditional group and queryset contracts:**
- Files: `src/crud_views/lib/conditional/group.py`, `src/crud_views/lib/conditional/toggle.py`, `src/crud_views/lib/conditional/formset.py`, `src/crud_views/lib/conditional/queryset.py`, `src/crud_views/static/crud_views/js/toggle.js`, `docs/reference/conditional.md`
- Why fragile: cleaned choices govern server-side activation/clearing while browser state preserves unsaved inputs; offered-option coverage and POST selected-object validation are distinct bounded checks.
- Safe modification: preserve cleaned-data authority, native choice validation, exact value matching, and query-free metadata. Supported value-driven controls are single `Select` and same-name `RadioSelect`; custom sources/widgets and overlapping or whole-formset activation remain outside the documented contract.
- Test coverage: `tests/test1/test_conditional_*.py`, `tests/test1/test_conditional_queryset*.py`, `tests/js/toggle.test.js`, `tests/js/formset.test.js`, `tests/browser/conditional-formsets-evidence.test.cjs`, `tests/browser/queryset-conditional.cjs`, and `examples/bootstrap5/conditional/tests.py`.

**Current-page bulk selection and action-form lifecycle:**
- Files: `src/crud_views/lib/bulk/__init__.py`, `src/crud_views/templates/crud_views/view_bulk_form.content.html`, `src/crud_views/static/crud_views/js/bulk.js`, `docs/reference/bulk_actions.md`
- Why fragile: submitted identifiers are resolved and rechecked for permission and eligibility at review and again inside the write transaction; the action destination owns the write through `cv_form_valid`. The `cv_bulk_` transport fields and hooks form a public contract, and overriding the ordinary `cv_form_valid_process` hook does not affect this path.
- Safe modification: retain the maximum-selection check before resolution, fresh scoped resolution at execution, atomic revalidation/write ordering, and the documented `cv_form_valid` override contract. The implementation supports the default database alias and ordinary single-field primary keys; multi-database writes and composite primary keys are unsupported by design.
- Test coverage: `tests/test1/test_bulk_*.py`, `tests/js/bulk.test.js`, `examples/bootstrap5/bulk_selection/tests.py`, and `tests/test1/test_bulk_docs.py` cover source scope, admission, review, execution, and public documentation.

**Manage authorization and setup command:**
- Files: `src/crud_views/lib/views/manage.py`, `src/crud_views/management/commands/cv_manage_group.py`, `src/crud_views/lib/settings.py`, `src/crud_views_guardian/lib/views.py`
- Why fragile: page access and action visibility combine mode, active authentication, group membership, and nested ancestor checks. The setup command creates only the configured group; it does not grant permissions or change memberships. Staff/superusers still need group membership when group-gated mode is active.
- Safe modification: keep page access, action visibility, and Django permissions distinct; preserve idempotent group-only setup and cover top-level/nested mode changes.
- Test coverage: `tests/test1/test_manage.py`, `tests/test1/test_manage_group.py`, `tests/test1/test_ancestor_manage.py`, `tests/test1/test_guardian.py`, `tests/test1/test_authorization_matrix.py`, and `tests/test1/test_resource_manage*.py`.

**Workflow permission and transition helper boundaries:**
- Files: `src/crud_views_workflow/lib/execution.py`, `src/crud_views_workflow/lib/views.py`, `src/crud_views_workflow/lib/mixins.py`, `docs/reference/workflow_view.md`
- Why fragile: `run_transition()` requires a persisted actor/object on the selected write alias; direct django-fsm calls bypass helper validation/history, and `workflow_check_transition()` is business validation rather than authorization. Page and transition permissions are separate.
- Safe modification: route transitions through the documented helper and preserve independent page and transition permission checks.
- Test coverage: `tests/test1/test_workflow_permissions.py`, `tests/test1/test_workflow_execution.py`; concurrency and Guardian/nested combinations are not certified.

**Lazy snippet parent resolution:**
- Files: `src/crud_views/lib/view/base.py`, `docs/reference/templates.md`, `tests/test1/test_snippet_context.py`, `tests/test1/test_snippet_docs.py`
- Why fragile: `parent_object` resolves lazily through Django template evaluation, where missing-variable behavior inside operators such as `{% if parent_object %}` can suppress exceptions. `cv_assert_parent()` is also called redundantly through `cv_get_parent_object()`.
- Safe modification: distinguish direct access from template-operator use in tests/docs and consolidate the duplicate guard only when touching this path.
- Test coverage: direct lazy resolution, missing-parent 404, and filter-header context are covered; operator-expression behavior is not.

## Scaling Limits

**Resource lookup and list materialization:**
- Current capacity: `Resource.cv_get_items()` returns a plain list and default `cv_get_item()` scans it linearly.
- Limit: large remote datasets require full-read memory and O(n) lookup.
- Scaling path: override lookup for sources with direct key access; add pagination or source-native lookup only if large remote collections become supported.

## Dependencies at Risk

**Django 4.2 support floor:**
- Risk: Django 4.2 remains the declared package floor and is included in the supported-version matrix.
- Impact: the oldest compatibility line increases maintenance and release-verification work.
- Migration plan: decide whether 1.0 retains this floor and update `pyproject.toml`, `noxfile.py`, and migration guidance together if it changes.

## Documentation Accuracy

**Access-trace login redirect wording:**
- Problem: `docs/reference/manage.md` describes a login redirect as a `denied` step with `login_redirect`; project overrides of `has_permission()` may convert a recorded 404 into a redirect, leaving `not_found` as the recorded decision.
- Files: `docs/reference/manage.md`, `src/crud_views/lib/access_trace_runner.py`, `.planning/phases/06.37-cv-access-pydantic-json-contract-validation-and-schema-375/06.37-VERIFICATION.md`
- Impact: readers may misinterpret the trace decision for custom views.
- Fix approach: qualify docs to the stock-view case and bind the custom case with an additional test in `tests/test1/test_access_trace_docs.py`.

**CLI validation-error exit/text documentation:**
- Problem: `docs/reference/manage.md` documents exit code 2 for output validation failures and advises detecting the untranslated `(ValidationError)` token. Django command-line option errors may exit 1, and stderr can echo caller input containing that token.
- Files: `docs/reference/manage.md`, `src/crud_views/management/commands/cv_access.py`, `src/crud_views/lib/access_trace_export.py`, `tests/test1/test_access_trace_docs.py`
- Impact: scripts may classify unrelated errors as validation failures or expect the wrong exit code.
- Fix approach: qualify the exit-code wording and document a robust detection rule if the CLI contract is revised.

## Missing Critical Features

None independently confirmed.

## Test Coverage Gaps

**Invalid polymorphic content-type URLs:**
- What's not tested: direct create with nonexistent content-type ids or existing but unconfigured subtype ids.
- Files: `src/crud_views_polymorphic/lib/utils.py`, `src/crud_views_polymorphic/lib/create.py`, `tests/test1/test_polymorphic.py`
- Risk: lookup/form-selection exceptions can surface as server errors instead of a controlled response.
- Priority: Medium.

**Custom user model without `username` in legacy permission-holder path:**
- What's not tested: `CRUD_VIEWS_MANAGE_SHOW_USERS=True` on an email-only user model through `get_permission_holders()`.
- Files: `src/crud_views/lib/views/manage.py`, `src/crud_views_guardian/lib/views.py`, `tests/test1/test_manage.py`, `tests/test1/test_guardian.py`
- Risk: the legacy path uses `username` directly in `values_list()` and `order_by()`, which can raise `FieldError`; the structured matrix's `USERNAME_FIELD` support does not cover this separate path.
- Priority: Medium.

**Third-party theme integration:**
- What's not tested: arbitrary consumer overrides across template variables, class keys, icons, and JavaScript adapters.
- Files: `src/crud_views/templates/crud_views/`, `src/crud_views/static/crud_views/js/`, `docs/development/stability.md`
- Risk: compatibility issues in installed downstream themes may escape built-in and example-theme tests.
- Priority: Low; this is an extension certification boundary.

**Navbar interaction recapture after component-tag composition:**
- What's not tested: a fresh keyboard/focus/Enter and long-text interaction run against the final component-tag composition. Historical interaction receipts in `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-BROWSER.json` are bound to product revision `7ccee139`; the later plan09 UI review states interaction capture was off and explicitly treats historical evidence as supplemental. The identity/items leaves are unchanged, and focused current source/tests cover their semantics and composition.
- Files: `src/crud_views/templatetags/crud_views.py`, `src/crud_views/templates/crud_views/tags/navbar.html`, `src/crud_views/templates/crud_views/tags/navbar_items.html`, `tests/test1/test_navbar_templates.py`, `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-UI-REVIEW.md`, `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-BROWSER.json`
- Risk: interaction behavior after wrapper composition is supported by unchanged leaf/source and earlier receipt, but was not freshly captured at the final revision. This is a provenance boundary, not a confirmed defect or an unpassed release criterion.
- Priority: Low.

**Navbar visual verification scope:**
- What's not tested: arbitrary downstream themes, Firefox/WebKit/older engines, real browser zoom, and universal assistive-technology behavior. Phase 06.40's fresh static audit covered six viewport widths and the pinned example theme; 640px is a 200%-reflow equivalent, not actual zoom. Historical browser interaction evidence supplements this scope and is separately revision-bound.
- Files: `examples/bootstrap5/navbar_demo/`, `tests/browser/`, `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-UI-REVIEW.md`, `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/08-UI-REVIEW-historical.md`
- Risk: downstream rendering and browser/AT behavior remain unestablished; no navbar defect is inferred.
- Priority: Low.

**Navbar example supporting-copy typography advisory:**
- What's not tested/fixed: whether the design should retain the measured 16px supporting paragraphs or apply the proposed 14px style. The current UI audit records this as minor warning UI-01, not a completion defect.
- Files: `examples/bootstrap5/navbar_demo/templates/navbar_demo/home.html`, `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-UI-REVIEW.md`, `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/09-ui-static-audit.json`
- Risk: minor hierarchy difference from the approved proposed default; it does not affect navigation or page behavior.
- Priority: Low/advisory.

**Compact formset consumer extension hooks:**
- What's not tested: arbitrary third-party widgets/templates, compact-column mutation in `add_fields()`, query-issuing constructors/`get_form_kwargs(None)`, and compact polymorphic forms; these are outside the documented compact-mode contract.
- Files: `docs/reference/formsets.md`, `src/crud_views/lib/formsets/compact.py`, `.planning/phases/06.24-opt-in-compact-formsets-shared-desktop-headings-and-nested-m/06.24-COMPATIBILITY.md`
- Risk: unsupported hooks may fail validation or behave outside contract if a consumer opts into compact mode.
- Priority: Low; documented support boundary.

**Bulk transaction behavior on PostgreSQL:**
- What's not tested: PostgreSQL-specific transaction and locking behavior under concurrent updates; no server-side row-lock guarantee is part of the bulk contract.
- Files: `src/crud_views/lib/bulk/__init__.py`, `docs/reference/bulk_actions.md`, `docs/reference/request_lifecycle.md`, `.planning/phases/06.41-current-page-bulk-selection-and-action-forms-for-table-and-c/06.41-SECURITY.md`
- Risk: database-specific concurrency behavior beyond the documented re-resolution and transaction boundary is unmeasured. This is an evidence limit, not a defect in the supported contract.
- Priority: Low; add database-specific measurement only if applications require a stronger concurrency guarantee.

## Resolved Findings

Phase 06.27's inherited-cleaner and contradictory-browser-observation findings are closed in `src/crud_views/lib/conditional/group.py` and `tests/browser/conditional-formsets.cjs`; evidence is in `.planning/phases/06.27-choice-driven-conditional-groups-354/06.27-REVIEW-DISPOSITION.md` and `06.27-FIXES.md`.

Phase 06.29's lazy caller-class rendering failure is closed in `src/crud_views/lib/crispy/table.py`, with regression coverage in `tests/test1/test_crispy_columns.py` and disposition in `.planning/phases/06.29-themeable-column-helpers-356/06.29-REVIEW-DISPOSITION.md`.

Phase 06.30 passed 54/54 must-haves with zero active review findings; earlier defects in that phase are historical, not open concerns (`.planning/phases/06.30-queryset-driven-conditional-fields-360/06.30-VERIFICATION.md`). Phase 06.31's seed command rollback issue is fixed transactionally; phase 06.32's workflow icon integration passed 7/7 (`.planning/phases/06.31-developer-only-manage-diagnostics-361/06.31-REVIEW-DISPOSITION.md`, `.planning/phases/06.32-workflow-transition-variant-and-icon-metadata-362/06.32-VERIFICATION.md`).

Phase 06.34 access tracing passed 36/36 and its UAT is complete. Phase 06.35 Resource manage parity passed 5/5, deep review found zero issues, and the security audit closed all 14 threats. Its old seven-runtime and four Tabler-fixture gaps are not current matrix gaps: phase 06.40 provides a fresh full supported matrix. The external Tabler fixture limitation remains a historical, environment-specific check and is not a package blocker (`.planning/phases/06.34-access-trace-cv-access-command-and-manage-page-form-370/06.34-VERIFICATION.md`, `.planning/phases/06.35-resource-manage-pages-with-cv-access-parity-372/06.35-VERIFICATION.md`, `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-ACCEPTANCE.md`).

The Pydantic 2.2.1 concern that had been recorded from phases 06.36–06.37 is not retained as an open floor failure: phase 06.40's floor run passed 792 tests, including all navbar modules, on Pydantic 2.2.1/Django 5.2.19. This is targeted floor evidence, not a claim that every suite has been run at that floor (`.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-ACCEPTANCE.md`).

Phase 06.37 strict TraceUser validation, schema regeneration guidance, registry isolation, and command error-line findings are closed. Remaining WR-01, WR-06, IN-03, and IN-09–11 are represented above only where current source/docs still support them; earlier review failures and fixed items are historical (`.planning/phases/06.37-cv-access-pydantic-json-contract-validation-and-schema-375/06.37-REVIEW-DISPOSITION.md`).

Phase 06.40 passed all ten supported Python/Django runtime cells in installed normal and request-recorder modes, all ten example cells, both crispy floors, the Pydantic floor, distribution, and required tooling. Python 3.14/3.15 with Django 4.2 are explicit unsupported skips. Its source-bound receipts retain failed attempts and distinguish final-revision full runs from earlier full runs plus affected-file reruns after the test-helper-only change; no earlier run is relabeled as a run of the later test revision. Fresh static UI evidence covers six widths, while the prior 345-assertion browser receipt and keyboard interactions remain bound to their recorded earlier product revision. These are evidence boundaries, not product defects (`.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-MATRIX.json`, `06.40-INPUTS.json`, `06.40-ACCEPTANCE.md`, `06.40-UI-REVIEW.md`, `06.40-BROWSER.json`).

Phase 06.41 passed 130/130 verified must-haves and all seven UAT checks. Current retained evidence reports the latest core suite at 16,952 passed, 1 skipped, and the bulk example at 637 passed plus 296 subtests. Human confirmation of installed-distribution/full-recorder CI was recorded without a URL or revision, so that CI result is not independently inspectable here. PostgreSQL concurrency/locking measurement was not performed. These are evidence boundaries; the feature contract remains default-database and single-field-PK only (`.planning/phases/06.41-current-page-bulk-selection-and-action-forms-for-table-and-c/06.41-VERIFICATION.md`, `06.41-UAT.md`, `06.41-REGRESSION.md`, `06.41-SECURITY.md`).

---

*Concerns audit: 2026-11-21*
