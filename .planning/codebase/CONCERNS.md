---
last_mapped_commit: 7d9b74dc51306d98ce007cd001f416463982c456
last_mapped_at: 2026-11-26
---
<!-- refreshed: 2026-11-26 -->
# Codebase Concerns

**Analysis Date:** 2026-11-26

## Tech Debt

**Placeholder reporting command:**
- Issue: `crud_views_show` advertises a report but `handle()` contains only `pass`.
- Files: `src/crud_views/management/commands/crud_views_show.py`.
- Impact: invoking the command produces no report.
- Fix approach: implement a bounded report or remove the placeholder command; keep this distinct from the implemented `cv_manage_view` and `cv_access` commands.

**Large shared modules and MRO-sensitive authorization:**
- Issue: registration, dispatch, navigation and configuration share central classes; Guardian adds cooperating mixins.
- Files: `src/crud_views/lib/view/base.py`, `src/crud_views/lib/viewset/__init__.py`, `src/crud_views/lib/views/manage.py`, `src/crud_views_guardian/lib/mixins.py`, `src/crud_views_guardian/lib/views.py`, `src/crud_views/templatetags/crud_views.py`.
- Impact: local changes have broad rendering/request regression surfaces and require tracing multiple owners.
- Fix approach: extract cohesive responsibilities only for a demonstrated maintenance need. Preserve proven public paths and the developer-maintainability constraint in `CLAUDE.md` and `superpowers/notes/2026-11-04-opt-in-url-helper-decision.md`.

**Assertions enforce configuration preconditions:**
- Issue: some invalid configuration/caller inputs are rejected with assertions, which optimized Python removes.
- Files: `src/crud_views_polymorphic/lib/utils.py`, `src/crud_views_workflow/lib/mixins.py`, `src/crud_views/lib/formsets/formsets.py`, `src/crud_views/lib/view/base.py`.
- Impact: invalid configurations may fail later or less clearly under `python -O`; no authorization bypass is established.
- Fix approach: use explicit exceptions or system checks for public configuration contracts when changing these paths; keep assertions for internal invariants.

**Startup configuration and process-global registries:**
- Issue: settings defaults capture Django configuration at import; theme prefix, namespace and placement registration keeps process-global values.
- Files: `src/crud_views/lib/settings.py`, `src/crud_views/lib/data_prefix.py`, `src/crud_views/lib/js_config.py`, `src/crud_views/templatetags/crud_views.py`.
- Impact: runtime settings changes/test overrides do not uniformly refresh captured state. Per-request theme switching is outside the startup-only contract.
- Fix approach: register at startup, preserve validation before assignment and snapshot copying, and restore registry state in tests. Do not broaden semantics without a concrete application need.

## Known Bugs

**Invalid polymorphic content-type selection:**
- Symptoms: nonexistent IDs raise `ContentType.DoesNotExist`; a resolved model without a configured form raises `ValueError`. The latter message uses `self.object.__class__`, which can name `NoneType` during create.
- Files: `src/crud_views_polymorphic/lib/utils.py`, `src/crud_views_polymorphic/lib/create.py`, `src/crud_views_polymorphic/lib/create_select.py`.
- Trigger: directly request polymorphic create with an unknown or unconfigured content-type ID. This is a source-observed error path, not a fresh runtime reproduction in this map.
- Workaround: use selector-generated URLs. When fixing, convert invalid selections to a deliberate 404 or form error and name the resolved model.

## Security Considerations

**Link eligibility differs from destination authorization:**
- Risk: applications can mistake a visible/hidden link for proof of endpoint authorization.
- Files: `src/crud_views/lib/link_access.py`, `src/crud_views/lib/view/base.py`, `src/crud_views_guardian/lib/mixins.py`, `docs/reference/link_access.md`, `docs/reference/guardian.md`.
- Current mitigation: public `check_link_access` validates target, own-object presence/type and finite list/tuple ancestry before delegation. Shared checks apply known higher gates, immediate-parent/provider checks, own permission and then state. Ordinary checks neither discover unknown ancestors nor cache permission/state decisions. Destination requests enforce independent permission/queryset restrictions.
- Public API boundary: compatible unsaved objects and partial higher ancestry are accepted. Validation establishes type/presence, not membership, queryset access or request authorization; unknown higher levels stay unchecked, and a missing immediate parent denies. The public checker supplies no rendering view, so rendering-view-dependent hooks can differ from package buttons. These limits are intentional and documented in `docs/reference/link_access.md`.
- Accepted boundary: ordinary nested parent-only non-create links still call `cv_has_access`; a `PermissionRequired` base can hide a link whose parent-only request is allowed. Cancel deliberately omits that hook, including custom overrides, and retains higher/immediate gates and state. Actual Cancel retains bounded parent lookup; ordinary links do not acquire that lookup. These are documented decisions, not defects.
- Recommendations: use the public full checker for custom Python links, retaining independent endpoint authorization. Test rendered eligibility and direct destination responses together. Preserve object/parent argument separation and gate-before-hook/state ordering in `tests/test1/test_public_link_access.py`, `tests/test1/test_link_access.py`, `tests/test1/test_link_consumers.py`, `tests/test1/test_link_cancel.py`, and `tests/test1/test_guardian_composition.py`.

**Guardian grant lifetime follows the supplied user object:**
- Risk: a retained user can retain positive or negative grants after direct/group permission changes; `refresh_from_db()` does not reset permission caches.
- Files: `src/crud_views_guardian/lib/permissions.py`, `docs/reference/guardian.md`, `tests/test1/test_guardian_checker.py`, `tests/test1/test_workflow_review.py`.
- Current mitigation: fresh normal requests use fresh users; destination permission/state decisions remain independent. Workflow refusal reload and retained-user boundaries are documented and tested.
- Recommendations: preserve fresh-request revocation semantics; applications retaining users across authorization changes must account for cache lifetime.

**Resource scoping and external writes are application-owned:**
- Risk: a Resource implementation that ignores parent URL kwargs can return unscoped remote data; Django transactions cannot roll back external writes.
- Files: `src/crud_views/lib/resource.py`, `docs/reference/request_lifecycle.md`.
- Current mitigation: `ResourceViewMixin` explicitly assigns parent filtering to the application and defaults `cv_atomic` to false.
- Recommendations: scope source reads and authorization in Resource implementations; design compensation for external writes when needed. This is an extension contract, not a confirmed package leak.

**Scoped security/review evidence is clean:**
- Files: `.planning/phases/06.52-publish-check-link-access-as-the-documented-way-to-decide-a/06.52-SECURITY.md`, `.planning/phases/06.52-publish-check-link-access-as-the-documented-way-to-decide-a/06.52-REVIEW.md`, `.planning/phases/06.52-publish-check-link-access-as-the-documented-way-to-decide-a/06.52-VERIFICATION.md`.
- Current mitigation: independent verification passes 17/17 must-haves; all nine authored threats are closed; review reports zero findings, including the three-file documentation/test delta at `9ec58fa4`.
- Recommendations: treat this as scoped evidence rather than universal certification. Documented public API limits are approved scope, not waived security findings. The shared-gate implementation does not retain stage-1 Guardian link exceptions; do not list those as open concerns.

## Performance Bottlenecks

**Delete preview limit bounds display after inspection:**
- Problem: a small preview cap does not bound cascade collection work.
- Files: `src/crud_views/lib/views/delete.py`, `src/crud_views/lib/deletion.py`, `tests/test1/test_delete_preview_limit.py`.
- Cause: deletion inspection and permission filtering run before preview row selection.
- Improvement path: profile real cascades before designing separately bounded inspection. Preserve the documented display-only cap.

**Navigation still executes destination hooks:**
- Problem: grant reuse reduces SQL but does not remove independent permission/state calls or certify customer latency.
- Files: `src/crud_views_guardian/lib/permissions.py`, `src/crud_views/lib/link_access.py`, `src/crud_views/lib/navbar.py`, `tests/test1/test_guardian_checker_costs.py`, `tests/test1/test_navbar_costs.py`.
- Cause: custom destination hooks/backends can add work outside the published fixture budgets.
- Improvement path: preserve exact fixture/category budgets and profile actual pages before broader prefetching. Do not turn grant reuse into permission/state decision caching.

## Fragile Areas

**Ancestor resolution and link/request composition:**
- Files: `src/crud_views/lib/ancestors.py`, `src/crud_views/lib/ancestor_db.py`, `src/crud_views/lib/ancestor_policy.py`, `src/crud_views/lib/link_access.py`, `src/crud_views_guardian/lib/ancestors.py`, `src/crud_views_guardian/lib/mixins.py`.
- Why fragile: actor admission, provider, database alias, MRO and known-ancestry alignment interact. Unknown ancestor holes must stay at their declared levels.
- Safe modification: preserve missing-immediate-parent denial, supplied-ancestry-only ordinary checks and independent endpoint enforcement. Keep create hook context bound to its own ViewSet and preserve explicit Cancel actor/request semantics.
- Test coverage: `tests/test1/test_ancestor_*.py`, `tests/test1/test_link_*.py`, `tests/test1/test_public_link_access.py`, `tests/test1/test_guardian_child_link_visibility.py`, and `tests/test1/test_authorization_matrix.py` cover supported contracts; arbitrary downstream overrides remain uncertified.

**Public link API compatibility:**
- Files: `src/crud_views/lib/link_access.py`, `docs/reference/link_access.md`, `docs/development/stability.md`, `tests/test1/test_public_link_access.py`, `tests/test1/test_link_access_docs.py`.
- Why fragile: enum truthiness, argument validation and parent/own/state ordering are public promises. Input errors and reached-gate errors share `ImproperlyConfigured`; only public caller-input diagnostics have the `check_link_access` prefix. Private outcome strings are not a serialization API.
- Safe modification: preserve names, signature, three results, boolean behavior, validation cases and gate ordering. Keep database-gate placement, denial-versus-configuration-error ordering and message wording beyond the input prefix distinguished as current behavior that can change in a minor release. Reached hook exceptions must propagate.
- Test coverage: public tests exercise compatible subtypes, unsaved objects, malformed containers, missing parents, ancestor holes, no domain lookups, absent membership validation, error propagation and ordinary/Guardian composition; docs tests execute extracted examples. No universal downstream hook or zero-auth-query guarantee is established.

**Nested formsets and conditional activation:**
- Files: `src/crud_views/lib/formsets/formsets.py`, `src/crud_views/lib/formsets/render_tree.py`, `src/crud_views/lib/formsets/compact.py`, `src/crud_views/lib/conditional/group.py`, `src/crud_views/lib/conditional/queryset.py`, `src/crud_views/static/crud_views/js/formset.js`, `src/crud_views/static/crud_views/js/toggle.js`.
- Why fragile: management indexes, save order, server activation, browser cloning and hidden validation feedback must agree.
- Safe modification: cover GET, invalid POST, deletion, nested indexes and fragment lifecycle together. Keep compact metadata query-free/index-independent and native selected-object validation authoritative.
- Test coverage: `tests/test1/test_formsets*.py`, `tests/test1/test_conditional_*.py`, `tests/js/formset.test.js`, `tests/js/toggle.test.js`, `tests/js-integration/formset.test.js`. Arbitrary custom widgets and compact polymorphic forms remain bounded by `docs/reference/formsets.md`.

**Bulk admission and write lifecycle:**
- Files: `src/crud_views/lib/bulk/__init__.py`, `src/crud_views/templates/crud_views/snippets/bulk_toolbar.html`, `src/crud_views/templates/crud_views/tags/button/bulk.html`, `src/crud_views/static/crud_views/js/bulk.js`, `docs/reference/bulk_actions.md`.
- Why fragile: source selection, review and execution have separate checks; execution re-resolves and revalidates identifiers inside its transaction. Copied templates must retain native submit identity and destination URL semantics.
- Safe modification: preserve selection limits before resolution, fresh scoped resolution before writes and the `cv_form_valid` override contract. Keep toolbar eligibility eager in `get_context_data()` so template evaluation cannot swallow hook errors.
- Test coverage: `tests/test1/test_bulk_*.py`, `tests/js/bulk.test.js`, `examples/bootstrap5/bulk_selection/tests.py`. Default-database/single-field-PK support is a deliberate boundary.

**Theme configuration and copied templates:**
- Files: `src/crud_views/lib/data_prefix.py`, `src/crud_views/lib/js_config.py`, `src/crud_views/static/crud_views/js/adapters.js`, `src/crud_views/templates/crud_views/const/js.html`, `docs/reference/theme.md`.
- Why fragile: startup registrations, copied config, class keys and provider lifecycle events must align.
- Safe modification: retain `cv_config`/`cv_const_js`, absence-only prefix/namespace fallback and explicit trigger placement precedence. Providers with different lifecycle event names must supply their own adapter.
- Test coverage: `tests/test1/test_data_prefix.py`, `tests/test1/test_js_config.py`, `tests/js/adapters.test.js`, `tests/js/object-detail-tabs.test.js`; stub/jsdom evidence does not establish native third-party browser behavior.

**Access-trace simulation and JSON compatibility:**
- Files: `src/crud_views/lib/access_trace.py`, `src/crud_views/lib/access_trace_runner.py`, `src/crud_views/lib/access_trace_export.py`, `src/crud_views/lib/manage_report.py`, `src/crud_views/management/commands/cv_access.py`, `docs/reference/manage.md`.
- Why fragile: traces record decisions at owning gates and dispatch a synthetic GET with a stubbed handler. Public schema field names/literals are consumer compatibility surface.
- Safe modification: record new supported gates at their owner; retain default-off tracing and its bounded simulation contract. Change output models, schema and docs together.
- Test coverage: `tests/test1/test_access_trace*.py`, `tests/test1/test_access_trace_grid.py`, `tests/test1/test_manage_command_docs.py`; arbitrary middleware/custom side effects are outside simulation scope.

## Scaling Limits

**Resource materialization and lookup:**
- Current capacity: `cv_get_items()` returns a full plain list; default `cv_get_item()` scans it.
- Files: `src/crud_views/lib/resource.py`.
- Limit: O(n) lookup/full-read memory; no fixed maximum size is enforced.
- Scaling path: override source-native key lookup. Add pagination only for a demonstrated large-collection requirement.

## Dependencies at Risk

**Wide declared compatibility surface:**
- Risk: Python >=3.12, Django >=4.2 and Pydantic >=2.2.1 require explicit lower-bound and runtime-matrix maintenance.
- Files: `pyproject.toml`, `noxfile.py`.
- Impact: a passing source suite in one environment does not establish every installed-distribution/dependency combination. Django 4.2 with Python 3.14/3.15 is explicitly skipped in the configured matrix.
- Migration plan: update floors, classifiers, nox sessions and migration guidance together when support changes. No newly confirmed broken dependency floor is established by this map.

## Missing Critical Features

None independently confirmed. Partial ancestry and absent membership/rendering-view checks in `docs/reference/link_access.md`, parent-only link/Cancel semantics in `docs/reference/guardian.md`, Resource behavior in `src/crud_views/lib/resource.py`, and bulk database/PK bounds in `docs/reference/bulk_actions.md` are accepted contracts, not requests to broaden scope.

## Test Coverage Gaps

**Invalid polymorphic selection responses:**
- What's not tested: deliberate responses for nonexistent content-type IDs or valid but unconfigured subtype IDs.
- Files: `src/crud_views_polymorphic/lib/utils.py`, `tests/test1/test_polymorphic.py`.
- Risk: crafted direct URLs can expose exceptions beyond ordinary selector-path coverage.
- Priority: Medium; bind the intended response when fixing the path.

**Database-specific concurrency:**
- What's not tested: PostgreSQL-specific bulk locking/concurrent updates and general workflow concurrency guarantees.
- Files: `src/crud_views/lib/bulk/__init__.py`, `src/crud_views_workflow/lib/execution.py`, `tests/test1/test_workflow_execution.py`, `docs/reference/bulk_actions.md`.
- Risk: transactions and fresh revalidation alone do not establish stronger row-lock/concurrent-transition guarantees. This is an evidence boundary.
- Priority: Low; add database-specific evidence for applications requiring stronger guarantees.

**Downstream browser and assistive-technology certification:**
- What's not tested: universal native CoreUI/Tabler behavior, arbitrary copied themes, all engines and assistive-technology combinations.
- Files: `tests/browser/`, `tests/js/adapters.test.js`, `docs/reference/theme.md`, `.planning/phases/06.52-publish-check-link-access-as-the-documented-way-to-decide-a/06.52-UI-REVIEW.md`.
- Risk: source/template/jsdom checks have bounded scope; downstream runtime certification is not established. No defect or failed phase criterion is inferred.
- Priority: Low; consumer-specific validation lane.

**Latest source acceptance is not every runtime lane:**
- What's not tested: a fresh full dependency matrix, rebuilt installed distribution, recorder-enabled execution and universal browser run are not established by source-scoped receipts.
- Files: `.planning/phases/06.52-publish-check-link-access-as-the-documented-way-to-decide-a/06.52-VERIFICATION.md`, `.planning/phases/06.52-publish-check-link-access-as-the-documented-way-to-decide-a/06.52-REGRESSION.md`, `.planning/phases/06.52-publish-check-link-access-as-the-documented-way-to-decide-a/06.52-ship-evidence/receipt.json`, `noxfile.py`.
- Risk: conflating revisions and lanes overstates release coverage. Historical runtime acceptance is 20,397 core passes and 637 example passes plus 300 subtests. The `9ec58fa4` delta changes two Markdown files and one docs test; production and examples remain unchanged. Fresh checks cover 77 documentation cases, two independent verifier cases, strict docs and scoped Ruff. The full suites are retained evidence for unchanged runtime inputs, not reruns at that documentation commit. The recorded environment is Python 3.12.3 / Django 6.0.10 / Guardian 3.5.2 with request recording disabled.
- Priority: Low; preserve revision/environment-bound receipts. No tests were rerun for this mapping.

---

*Concerns audit: 2026-11-26*
