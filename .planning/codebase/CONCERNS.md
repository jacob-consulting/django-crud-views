---
last_mapped_commit: 3a28b40a2c700f23a61fad18eef0a2fe25b009c0
last_mapped_at: 2026-11-23
---
<!-- refreshed: 2026-11-23 -->
# Codebase Concerns

**Analysis Date:** 2026-11-23

## Tech Debt

**Startup-captured settings and template registration:**
- Issue: `CrudViewsSettings` class defaults and template-tag registration capture some Django settings at import/startup. `register_data_prefix()` and `register_js_namespace()` keep independent process-global values with defaults `bs` and `bootstrap`; the last valid call wins. `register_tooltip_placements()` replaces its whole mapping after validation. `override_settings()` does not refresh these registries or captured values, while selected label defaults are intentionally read at call time.
- Files: `src/crud_views/lib/settings.py`, `src/crud_views/templatetags/crud_views.py`, `src/crud_views/lib/data_prefix.py`, `src/crud_views/lib/js_config.py`, `src/crud_views/lib/__init__.py`
- Impact: changing startup configuration during a process does not reconfigure the package; a theme that registers too late or fails to register uses the default prefix. The supported contract is startup registration, not concurrent per-request or runtime theme switching.
- Fix approach: register prefix, namespace, and placements from the theme's startup hook. Keep configuration startup-only unless a demonstrated use case justifies broader runtime semantics; preserve validation-before-assignment, independent placement snapshots, and test isolation in `tests/test1/test_data_prefix.py` and `tests/test1/test_js_config.py`.

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

**Theme configuration adoption and native-library ownership:**
- Files: `src/crud_views/lib/data_prefix.py`, `src/crud_views/lib/js_config.py`, `src/crud_views/templatetags/crud_views.py`, `src/crud_views/templates/crud_views/tags/cv_config.html`, `src/crud_views/static/crud_views/js/adapters.js`, `src/crud_views_object_detail/static/crud_views_object_detail/js/tabs.js`, `docs/reference/theme.md`, `docs/reference/javascript.md`
- Why fragile: copied config markup must carry `data-data-prefix`, `data-js-namespace`, and escaped `data-tooltip-placements`. Missing attributes use the documented `bs`/`bootstrap`/empty-map defaults; present empty namespace/prefix values do not request fallback. Namespace registration selects the global provider independently of prefix spelling. It does not certify another library's DOM/API conventions; the stock modal adapter observes `hide.<prefix>.modal` and `hidden.<prefix>.modal` using the registered data prefix (PR #405), so prefix-renamed forks need no custom adapter for those events, but this repository's tests use stub providers only. Native CoreUI 5.9.1 modal close was checked in the browser downstream when #403 closed (2026-11-22, recorded in the issue and the CoreUI theme tracker), not here.
- Safe modification: keep startup registration and copied-config adoption together, preserve both `cv_config` and `cv_const_js` context contracts, and retain absence-only prefix/namespace fallback. Trigger placement attributes, including empty ones, override registered location defaults. Bulk buttons retain the existing `form` tooltip location. Custom adapters retain ownership of their replaced entries; themes with lifecycle event names not of the form `<event>.<prefix>.modal` must supply the appropriate adapter.
- Test coverage: registration, copied recipes/config, and namespace/placement dispatch are covered by `tests/test1/test_data_prefix.py`, `tests/test1/test_data_prefix_docs.py`, `tests/test1/test_js_config.py`, `tests/js/adapters.test.js`, and `tests/js/object-detail-tabs.test.js`. The two-config-alias bulk integration probes are recorded in `.planning/phases/06.47-semantic-variants-for-bulk-toolbar-buttons-400/06.47-VERIFICATION.md`; stub-provider/jsdom evidence does not establish native CoreUI/Tabler browser behavior.

**Breadcrumb class and table-header contracts:**
- Files: `src/crud_views/lib/button_classes.py`, `src/crud_views/templates/crud_views/tags/breadcrumb.html`, `src/crud_views/templates/crud_views/table/bootstrap5.html`, `docs/reference/buttons.md`, `docs/reference/breadcrumb.md`, `docs/reference/list_view.md`, `docs/reference/theme.md`
- Why fragile: copied templates can bypass the public class registry or diverge from django-tables2's effective ordering. The stock breadcrumb uses `breadcrumb:list`, `breadcrumb:item`, and `breadcrumb:item-active`; its final item's `aria-current="page"` is independent of those classes. Stock table headers use bound-column ordering for both icons and `aria-sort`, including constructor/default ordering and prefixed query parameters.
- Safe modification: retain default breadcrumb output, per-key defaults → theme → project precedence, and empty contributions for empty/non-string values. Derive sorting from `column.is_ordered` and `column.order_by_alias.is_descending`; preserve sorting links, ordinary header-attribute escaping, and non-orderable headers. The stock header owns `aria-sort`: caller-supplied same-name attrs are explicitly unsupported, with no deduplication or collision-precedence contract. Use the existing `table.thead` block for different header semantics; this exclusion is not an open defect or a request to expand scope.
- Test coverage: `tests/test1/test_breadcrumb.py` binds default bytes, class precedence, empty/non-string values, escaping, links, and current-page semantics; `tests/test1/test_button_classes.py` binds registry inventories; `tests/test1/test_table_template.py` covers effective ordering, prefixed links, attribute escaping, and generated attribute counts within the supported contract. `tests/test1/test_theme_adoption_docs.py` checks the documented adoption recipe. Arbitrary downstream copied-template adoption remains consumer-owned.

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

**Bulk toolbar gating and `cv_bulk_buttons` template guard:**
- Files: `src/crud_views/lib/bulk/__init__.py`, `src/crud_views/templates/crud_views/snippets/bulk_toolbar.html`, `src/crud_views/templates/crud_views/view_list_table.content.html`, `src/crud_views/templates/crud_views/view_card.content.html`, `docs/reference/bulk_actions.md`
- Why fragile: the toolbar shows only destinations the viewer can enter (Phase 06.46). `cv_bulk_buttons` is evaluated eagerly in `get_context_data` so label/URL exceptions surface instead of being swallowed by template evaluation. Templates still guard on `view.cv_bulk_buttons`, an internal name outside the stable 1.0 inventory.
- Safe modification: keep eager evaluation before render. Whether to promote, replace, or retain the guard is deferred to Phase 7; copied templates relying on it may break then.
- Test coverage: `tests/test1/test_bulk_source.py`, `tests/test1/test_bulk_scope.py`, `tests/test1/test_bulk_docs.py`.

**Bulk toolbar variant and copied-leaf contracts:**
- Files: `src/crud_views/lib/bulk/__init__.py`, `src/crud_views/lib/button_classes.py`, `src/crud_views/templates/crud_views/tags/button/bulk.html`, `docs/reference/buttons.md`, `docs/reference/bulk_actions.md`, `docs/reference/theme.md`
- Why fragile: toolbar classes come from the destination's `cv_action_variant` and `bulk:*` keys, independently of `form:submit`. All four stock variant defaults remain `btn btn-primary`; `danger` metadata alone does not change stock appearance. Themes customizing only `form:submit` must explicitly configure bulk keys. Copied leaves must preserve native submit identity, destination `formaction`, short action labels, escaping, and the published nine-field payload.
- Safe modification: preserve effective-mode lookup and empty/`None` mode-key suppression. Unavailable icons select label mode, while normalized `cv_icon` can remain nonblank. Reuse `form:hidden-label`, `form:icon-host`, and the `form` tooltip location; retain Confirm/Cancel's existing form rendering. Keep bulk out of generic button-data/tag dispatch; no per-action label-mode map is part of this contract.
- Test coverage: `tests/test1/test_bulk_variants.py` checks destination variants, native source-to-review submission, stock bytes against the form leaf, form-style isolation, short labels, escaping, and effective-mode precedence. `tests/test1/test_bulk_docs.py` executes the copied leaf with projected fields and rejects undeclared variable dependencies. Downstream copied-template adoption remains consumer-owned, not an unresolved package finding.

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

Phase 06.41 passed 130/130 verified must-haves and all seven UAT checks. Its core-suite and bulk-example results are superseded by the post-06.42 combined acceptance below. Human confirmation of installed-distribution/full-recorder CI was recorded without a URL or revision, so that CI result is not independently inspectable here. PostgreSQL concurrency/locking measurement was not performed. These are evidence boundaries; the feature contract remains default-database and single-field-PK only (`.planning/phases/06.41-current-page-bulk-selection-and-action-forms-for-table-and-c/06.41-VERIFICATION.md`, `06.41-UAT.md`, `06.41-REGRESSION.md`, `06.41-SECURITY.md`).

Phase 06.42 passed 22/22 verified must-haves after integration with merged PR #392. The combined post-06.42 core suite passed 17,057 tests with one skip, JavaScript passed 486 tests, and the bulk example passed 637 tests plus 296 subtests. Strict documentation and Ruff/format checks also passed. Registration is intentionally startup-only; copied templates/config need downstream adoption. These results do not claim a native CoreUI browser run or a fresh full supported Python/Django matrix (`.planning/phases/06.42-theme-registered-data-attribute-prefix-for-templates-and-obj/06.42-VERIFICATION.md`, `06.42-SECURITY.md`).

Phase 06.44's capture override symlink finding CR-01 is fixed and independently re-reviewed: `tests/browser/conditional-formsets.cjs` preflights all planned override leaves with `lstat`/regular-file checks before screenshots, and the evidence checker applies the same policy. Six real-filesystem regressions cover symlinks, dangling links, and non-regular files; the refreshed evidence tests passed 51 cases and the independent lifecycle checker passed. The finding is historical provenance, not an open security concern (`.planning/phases/06.44-css-tokens-for-manage-pages-and-formsets-with-bootstrap-fall/06.44-REVIEW-DISPOSITION.md`, `06.44-SECURITY.md`, `06.44-VERIFICATION.md`). Phase 06.44's CSS-token source contract is deliberately bounded to six documented tokens and twelve existing reads across the two CSS sheets; the parser guard fails closed on unsupported syntax, so extending CSS syntax requires updating its contract and tests. This adds no runtime registration, settings, or API surface (`src/crud_views/static/crud_views/css/manage.css`, `src/crud_views/static/crud_views/css/formset.css`, `tests/js/css-tokens.test.js`, `docs/reference/theme.md`). Its refreshed combined acceptance passed 17,122 Python and 512 Node tests (`.planning/phases/06.44-css-tokens-for-manage-pages-and-formsets-with-bootstrap-fall/06.44-VERIFICATION.md`).

Phase 06.45 shipped through PR #401. Verification passed all 9/9 must-haves, and the deep code review is clean with zero findings. Recorded final acceptance is 17,222 Python tests passed with one expected Django-version skip on Python 3.12.3/Django 5.2.19; focused compatibility selections passed 292 tests each on Django 4.2 and 6.0. JavaScript passed 541 tests and integration passed three tests. This is not a full Python/Django matrix or installed-distribution acceptance. Fake providers prove namespace/placement dispatch only; native CoreUI/Tabler behavior, real-browser certification, and downstream adoption remain unclaimed. The phase adds startup registration for namespace and tooltip placements, and records no defect in the supported contract (`src/crud_views/lib/js_config.py`, `src/crud_views/static/crud_views/js/adapters.js`, `.planning/phases/06.45-theme-registered-js-namespace-and-tooltip-placements-398/06.45-VERIFICATION.md`, `.planning/phases/06.45-theme-registered-js-namespace-and-tooltip-placements-398/06.45-REVIEW.md`).

Phase 06.46 shipped through PR #404: the earlier risk of Django templates silently swallowing bulk button label/URL exceptions is fixed by eager evaluation in `get_context_data` (`.planning/phases/06.46-bulk-toolbar-show-only-actions-the-viewer-can-enter-399/06.46-VERIFICATION.md`). PR #405 made the stock modal adapter observe hide/hidden events by registered data prefix, closing the fixed `*.bs.modal` concern for Bootstrap forks (`src/crud_views/static/crud_views/js/adapters.js`, `tests/js/adapters.test.js`).

Phase 06.47 shipped through PR #402 with 16/16 verified must-haves and zero open review findings. WR-01's incorrect promise that an unavailable icon becomes empty is corrected in the copied-leaf documentation and regression checks; it is not an open concern. The security register closes all nine entries. Recorded original acceptance passed 17,264 Python tests on Python 3.12.3/Django 6.0.10; the merged phase 06.45 integration has 470 affected Python passes, 541 JavaScript passes, three Django/JS integration passes, and independent rendered-config/jsdom checks for both config aliases. The broad Python result remains attributed to its original revision, rather than relabeled as a combined full-suite run. Native bulk submission and form tooltip dispatch remain intact; no fresh browser, downstream-theme, full dependency-matrix, or installed-distribution runtime acceptance is claimed. The source/template scope explicitly requires no additional human verification (`src/crud_views/lib/bulk/__init__.py`, `src/crud_views/templates/crud_views/tags/button/bulk.html`, `.planning/phases/06.47-semantic-variants-for-bulk-toolbar-buttons-400/06.47-VERIFICATION.md`, `.planning/phases/06.47-semantic-variants-for-bulk-toolbar-buttons-400/06.47-REVIEW-DISPOSITION.md`, `.planning/phases/06.47-semantic-variants-for-bulk-toolbar-buttons-400/06.47-SECURITY.md`).

---

*Concerns audit: 2026-11-23*
