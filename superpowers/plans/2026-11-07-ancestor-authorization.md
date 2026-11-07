# Ancestor Authorization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enforce the approved ancestor policy on every supported nested endpoint, independently of its local permissions, while preserving scoped ancestry and deterministic failure order.

**Architecture:** Use small typed configuration values, one bounded metadata walk, and one request-local traversal that interleaves scoped lookup and permission evaluation. Add explicit dispatch bridges where shipped permission mixins precede `CrudView`, and keep Guardian evaluation in the Guardian extension. Migrate existing immediate-parent helpers without adding full-chain rendering authorization.

**Tech Stack:** Existing Django CBVs/ORM/auth, Pydantic v2, django-guardian, pytest/pytest-django/pytest-xdist; existing polymorphic, workflow, and ObjectDetail integrations. No new dependency.

**Spec:** [Canonical v2 design](../notes/2026-11-07-ancestor-authorization-design-v2.md). Read it before this plan; its topic contracts control. Historical D-IDs below are provenance, not additional requirements.

## Global Constraints

- Developer maintainability is a hard constraint alongside correctness. Preserve proven local permission, queryset, state, form, modal, cancel, and transaction paths.
- `CRUD_VIEWS_ANCESTOR_PERMISSION_CASCADE = True`.
- `CRUD_VIEWS_ANCESTOR_READ_PERMISSIONS = {"nearest": "view", "higher": "view"}`.
- `CRUD_VIEWS_ANCESTOR_WRITE_PERMISSIONS = {"nearest": "change", "higher": "view"}`.
- `AncestorPolicy`: `provider=None`, `accept_global_perms=False`, `cascade=None`, `read=None`, `write=None`, fresh `actions={}`. `AncestorPermissions` requires named string fields `nearest` and `higher`.
- Providers are `"model"`, `"guardian"`, `"none"`; default core provider is model, default Guardian provider is strict object permission. Core must work without Guardian installed.
- Both depths validate every declared relationship. `none` consumes no protected position. Nearest-only still checks the nearest protected ancestor; it is not a disable switch.
- Static validation → existing/selected actor admission → outermost lookup and gate, then next level → remaining endpoint-local work. Never dispatch an ancestor endpoint.
- Call each ancestor's `get_queryset(view=requested_child_view)` with the actual endpoint/request/kwargs. Preserve its filtering and database selection; never retry an excluded object through its manager.
- Only `default` is supported for nested ORM data and relevant authorization records. Reject reached nondefault selection; preserve existing top-level database behavior.
- Resources can be leaves under ORM ancestors; the application still owns Resource collection/object scoping. Resources cannot be ancestors.
- Authorization covers the URL path. No automatic destination-parent gate, FK pinning, all-membership authorization, unlink-on-delete, or generic mutation policy.
- Use request-local objects/checkers only; no persistent ancestry or access cache. Permission-vocabulary caching remains distinct.
- Remove `cv_guardian_parent_permission` and `cv_guardian_parent_create_permission`; reject explicit constructor/subclass declarations, including old defaults and `None`. Keep the applicable view-local `cv_guardian_accept_global_perms`.
- Do not broaden unknown-attribute exemptions to conceal mistakes in the new policy or private integration hooks.
- Static checks must not query model, ContentType, Permission, or grant tables. Resolve permission-map keys only at reached selected gates.
- Public docs use generic examples. Any new `### Breaking` entry also updates `docs/migrating-1.0.md`.
- This request authorizes a standalone plan, not implementation or GSD phase creation. Do not assign a phase or change `.planning/`.

## Review Focus

These five easily missed conditions receive explicit tests in the owning tasks:

1. `CustomFormView` inherits `DetailView`, and Workflow inherits CustomForm: neither silently becomes Read; exact declarations remain mandatory (Task 2).
2. A deeper scoped queryset must never run after an outer denial; all-none must still preserve actual early actor denials without treating every permission mixin as login-required (Tasks 3–4).
3. A selected permission key or nondefault database fails only when reached; an outer denial cannot be displaced by speculative deeper vocabulary/routing queries (Tasks 3 and 6).
4. A class-level removed field or invalid owning policy must fail before registry/manage side effects and permit a corrected declaration with the same name (Tasks 1 and 4).
5. A `none` immediate parent remains the create/state/helper object, and Card navigation aliases never select another registered endpoint's action policy (Tasks 2, 3, and 5).

---

## Repository Findings and Implementation Choices

Planning baseline: `9c8e68e4`. Recheck HEAD before execution and record the execution baseline; unrelated dirty files are not part of this work.

- `ViewSet.register()` inserts into `_REGISTRY` and creates manage views. New owning-policy validation must precede both, including when `GuardianViewSet.register()` delegates to it.
- `get_parent_url_args`, `get_parent_attributes`, `get_path_parent`, `get_queryset`, and `BreadcrumbMixin._cv_breadcrumb_ancestors` currently walk parent pointers without cycle protection.
- `CrudViewPermissionRequiredMixin` and `ManageView` inherit Django permission dispatch before `CrudView.dispatch()`. Guardian's parent mixin also runs first. A guard solely in `CrudView.dispatch()` is insufficient.
- Use a private idempotent `CrudView._cv_authorize_ancestors() -> HttpResponse | None`, called first by explicit `dispatch()` bridges in `CrudView`, `CrudViewPermissionRequiredMixin`, `ManageView`, and `GuardianParentPermissionMixin`. Each bridge returns a denial response immediately or calls `super()`. Mark successful completion on that view instance; never mark a partial/failed traversal successful. This supports normal `as_view()` and explicitly initialized instance dispatch without replacing Django's lifecycle or metaclass.
- Keep `GuardianParentPermissionMixin` as a composition/local-state adapter; remove its old ancestor evaluator. Retaining this exported mixin does not retain a second policy mechanism.
- Use a private endpoint actor hook, `_cv_ancestor_actor_response() -> HttpResponse | None`, whose base implementation admits the actor. Shipped permission/manage/Guardian families supply bounded overrides; ancestry's protected-actor rules run separately. No child lookup or state hook is permitted here.
- Put configuration types in `crud_views/lib/ancestor_policy.py`, outside `lib/viewset/`, to avoid executing the ViewSet package when settings imports the types. Re-export from `crud_views.lib.viewset` as specified.
- Use a finite class-family classifier with explicit CustomForm exclusions before Detail matching. Recognize polymorphic selection lazily without importing absent extensions. Do not add public operation markers or a plugin registry.
- Keep private provider methods on ViewSet: `_ancestor_provider() -> Literal["model", "guardian", "none"]` and `_ancestor_has_permission(user, obj: Model, permission: str) -> bool`. Guardian overrides the default and Guardian evaluation; explicit model/none continue to work there. Configuration objects have no evaluator methods.
- Tests use real URLs/Client requests for ordering and effects. Tiny validation selections may run serially; broad selections use `-n 4`. Existing settings are captured singletons, so patch them deliberately.

## File Map

| File(s) | Responsibility |
| --- | --- |
| New `src/crud_views/lib/ancestor_policy.py` | Strict policy/pair types; no view imports or request state |
| New `src/crud_views/lib/viewset/ancestry.py` | Bounded metadata walk, relationship validation, finite operation resolution |
| New `src/crud_views/lib/view/ancestors.py` | Request enforcement, selected gates, scoped resolution, bounded helper gate |
| New `src/crud_views/lib/ancestor_databases.py` | Small reached-operation database guards, no routers or rerouting |
| `src/crud_views/lib/viewset/__init__.py`, `src/crud_views/lib/settings.py` | Public exports/field/defaults, pre-registration validation, guarded existing walks |
| `src/crud_views/lib/view/base.py`, `src/crud_views/lib/views/manage.py`, `src/crud_views/lib/views/create.py`, `src/crud_views/lib/views/mixins.py` | Early dispatch bridges, structural-parent reuse, local child read/write DB guards |
| `src/crud_views_guardian/lib/{viewset,mixins,views}.py` | Guardian provider, legacy removal, preserved child gates/state, migrated helpers and diagnostics |
| `src/crud_views/checks.py`, `src/crud_views_guardian/checks.py`, `src/crud_views/lib/breadcrumb.py` | Completed-registry checks, composition checks, safe navigation walk |
| New `tests/test1/ancestor_cases.py` and `tests/test1/test_ancestor_*.py` | Shared route fixtures and behavioral suites; no production abstraction derived from a test harness |
| `tests/test1/app/{models,views}.py`, existing authorization/Guardian/Resource tests | Minimal chain fixture, migration and preservation evidence |
| Core manage and Guardian configuration templates | Display ancestor settings separately from local fallback |
| `docs/reference/{nested,settings,guardian,resources,request_lifecycle}.md`, `docs/migrating-1.0.md`, `CHANGELOG.md`, `mkdocs.yml` | User contracts, migration, new reference navigation |
| New `docs/reference/ancestor_authorization.md` | Canonical public policy/operation/failure tables |
| New `superpowers/notes/2026-11-07-ancestor-authorization-performance.md` | Reproducible before/after measurements and verification record |

Execute Tasks 1–8 in order. These are reviewable increments on one feature branch, not independent releases. Migrate affected fixtures in the task introducing the new behavior; do not wait until the end to repair test collection. No task may retain permissive compatibility behavior to make old assertions pass.

### Task 1: Strict Public Configuration and Construction Atomicity

**Files:** Create `src/crud_views/lib/ancestor_policy.py`, `tests/test1/test_ancestor_policy.py`, `tests/test1/ancestor_cases.py`, `tests/test1/test_ancestor_performance.py`, and the performance note above. Modify `src/crud_views/lib/settings.py`, `src/crud_views/lib/viewset/__init__.py`, `src/crud_views_guardian/lib/viewset.py`, `tests/test1/app/models.py`.

**Interfaces:** Produces `AncestorPermissions(nearest: str, higher: str)`, `AncestorPolicy(provider: Literal["model", "guardian", "none"] | None = None, accept_global_perms: bool = False, cascade: bool | None = None, read: AncestorPermissions | None = None, write: AncestorPermissions | None = None, actions: dict[str, AncestorPermissions] = {})`, and `ViewSet.ancestor_policy`. Adds settings attributes `ancestor_permission_cascade`, `ancestor_read_permissions`, `ancestor_write_permissions`. Produces `_ancestor_provider()` on both ViewSet classes. Pair/action defaults are factories, not shared objects.

- [ ] **Step 1: Capture a reproducible query baseline before changing authorization.** Build isolated route fixtures using Publisher → Book → BookNote → a new minimal `AncestorAttachment(note=ForeignKey(BookNote), text=CharField)` test model; one-level routes use Publisher → Book. Reuse Author → UUIDFragmentRow → UUIDFragmentLeaf for UUID evidence later. Snapshot/restore registry, settings, URL modules/caches, and per-ViewSet permission vocabulary. In `test_ancestor_performance.py`, measure plain and Guardian list/detail/create requests with all required existing grants, disabled navigation actions, and fixed templates. Capture cold/warm counts separately and label mode as `legacy` before policies exist. Record baseline revision, Python/Django/Guardian versions, grant setup, status and SQL categories in the performance note; baseline and final fixtures must describe identical operations. Run `.venv/bin/pytest tests/test1/test_ancestor_performance.py -n 4 -v`; expect all baseline requests to succeed. Do not fake missing baseline measurements.

- [ ] **Step 2: Write failing configuration tests.** Parameterize exact invalid values and assert `ValidationError`, no database queries, unchanged registry and no manage class creation:

| Test | Setup and assertions |
| --- | --- |
| `test_policy_defaults_are_independent` | Two ViewSets: `assert first.ancestor_policy is not second.ancestor_policy`; changing one `actions` leaves the other `{}` |
| `test_strict_pair_and_policy_values` | Reject unknown fields/provider, `"true"`, `1`, `0` for booleans, missing pair component, `None`, empty/padded/non-string keys, and `actions={"approve": None}` |
| `test_global_defaults_and_explicit_partial_pairs` | Omitted settings yield exact defaults; explicit incomplete/None mappings and coercible cascade fail; complete mapping replaces the pair |
| `test_owner_policy_validates_before_registration` | Core Guardian provider, ineffective fallback, and top-level request fields fail; `assert name not in registry`; corrected declaration succeeds with exactly one manage key |
| `test_top_level_policy_scope` | Reject both cascade booleans, non-None read/write, nonempty actions; accept omitted/explicit None/empty values and valid provider/fallback |
| `test_core_policy_import_without_guardian` | Subprocess with core app and Guardian imports blocked successfully imports public types and constructs a core ViewSet |

Standalone policy objects may contain request settings; owning-ViewSet validation applies only when attached. Include inherited Guardian class defaults and explicit provider model/none cases.

- [ ] **Step 3: Run `.venv/bin/pytest tests/test1/test_ancestor_policy.py -q`.** Expect missing exports/fields or missing validation failures; fix test setup failures before implementation.
- [ ] **Step 4: Implement the types, settings and owning validation.** Forbid extras on new types; enforce uncoerced booleans/string keys, including settings values captured as defaults. Validate complete mappings as a unit. Run all new decidable owning checks before `register()` side effects; don't rely on a subclass after-validator running after `super().register()`. Keep the existing registry behavior for unrelated declarations. Legacy-field rejection/removal is Task 4, where its consumers migrate together.
- [ ] **Step 5: Run `.venv/bin/pytest tests/test1/test_ancestor_policy.py tests/test1/test_settings_checks.py tests/test1/test_import_safety.py -n 4`.** Expect passing tests and no Guardian import in the core-only subprocess. Ensure incomplete nested registries and unresolved forward references still construct.
- [ ] **Step 6: Commit only this task's files:** `feat: add validated ancestor policy configuration`.

### Task 2: Safe Metadata Walks, Relationships, and Exact Operation Classification

**Files:** Create `src/crud_views/lib/viewset/ancestry.py`, `tests/test1/test_ancestor_structure.py`, `tests/test1/test_ancestor_operations.py`. Modify `src/crud_views/lib/viewset/__init__.py`, `src/crud_views/lib/breadcrumb.py`, `src/crud_views/checks.py`; reuse `tests/test1/ancestor_cases.py`.

**Interfaces:** Consumes Task 1 types. Produces `walk_ancestors(viewset: ViewSet) -> tuple[ParentViewSet, ...]` in **nearest-first** order, validating the entire chain before returning; `validate_relationships(viewset: ViewSet) -> None`; `operation_permissions(view_class: type[CrudView]) -> AncestorPermissions | None` (`None` only for top-level); `validate_registered_actions(viewset: ViewSet) -> None`. Runtime errors are `ImproperlyConfigured`; checks translate them into actionable Django errors. Keep permissions/ContentType out of these helpers.

- [ ] **Step 1: Add failing metadata and operation tests with zero-query assertions.** Use real `.urlpatterns` access and URLconf import, not just direct helper calls.

| Test | Setup and assertions |
| --- | --- |
| `test_url_walk_rejects_cycles_and_missing_parent` | Self-cycle, two-node cycle, missing reference: `with pytest.raises(ImproperlyConfigured, match=affected_name)`; complete boundedly and name the chain |
| `test_child_before_parent_resolves_when_urls_needed` | Construct child first, then register parent: `assert reverse(...) == expected_url`; same valid output as existing URL generation |
| `test_all_supported_walks_terminate` | Exercise URL args/attributes/path/queryset setup, breadcrumb walk, checks and runtime validation against cycles; no DB access before error |
| `test_declared_relationships_are_validated` | Explicit FK and URL names, supported Genre/Publisher M2M reverse metadata pass; wrong target model, ambiguous/inconsistent metadata and Resource ancestor fail |
| `test_family_classification_survives_key_and_permission_changes` | Every approved family/subclass/permission variant: `assert pair == AncestorPermissions(nearest="view", higher="view")` for Read or `("change", "view")` for Write, including GET |
| `test_custom_forms_workflow_and_misleading_actions_require_entries` | CustomForm, CustomFormNoObject, Workflow and generic Action named `detail` with `cv_permission="view"` all raise without an exact action entry, including both depths/all-none |
| `test_card_policy_uses_literal_registration` | Card-only `card` passes, unregistered `list` fails; both keys independent; Card actually registered as `list` passes; navigation fallback still targets Card policy |
| `test_registration_checks_wait_until_complete` | Action policy can precede view class registration; after final registration missing literal key errors; adding a real List never retargets a Card override |

- [ ] **Step 2: Run `.venv/bin/pytest tests/test1/test_ancestor_structure.py tests/test1/test_ancestor_operations.py -n 4 -q`.** Expect failures for unsafe walks/classification. Guard cycle tests with a bounded subprocess timeout until the walk is fixed so the red run cannot hang a worker.
- [ ] **Step 3: Implement the shared metadata walk and classifier.** Detect visited ViewSet names, include the requested ViewSet in cycle detection, and preserve child-before-parent registration. Replace existing pointer loops with this walk; preserve existing output ordering. Validate ORM relations using declared field/related-model metadata, including agreement between the child attribute and parent M2M attachment attribute. Resource-leaf edges need no ORM relation; ORM ancestor edges do. Explicit action entries win before family defaults. Check CustomForm families before Detail and ordered actions before generic Action. Polymorphic selector and Card need explicit finite recognition. Do not classify by `cv_key`, `cv_permission`, HTTP method, or method-body inspection.
- [ ] **Step 4: Wire checks and runtime guards.** Check `get_all_views()` literal keys, not `get_view_class()` aliases. Reserve currently unused `crud_views.E320` (ancestry structure/relationship), `E321` (missing/unknown action declaration), and `E322` (global ancestor settings); recheck IDs before using them. Integrate with existing `E261` Resource-parent reporting without duplicate messages. Existing checks must return diagnostics instead of crashing on unresolved parent access. Runtime validation uses the same rules. Global settings validation must remain usable before migrated tables exist.
- [ ] **Step 5: Run `.venv/bin/pytest tests/test1/test_ancestor_structure.py tests/test1/test_ancestor_operations.py tests/test1/test_viewset.py tests/test1/test_viewset_registry.py tests/test1/test_nested_viewset.py tests/test1/test_breadcrumb.py tests/test1/test_resource_viewset.py -n 4`.** Expect passing tests, unchanged valid URL strings, preserved list→card navigation fallback, and zero-query configuration evidence.
- [ ] **Step 6: Commit:** `feat: validate ancestor structure and operation policies`.

### Task 3: Core Request Traversal, Actor Order, and Structural-Parent Reuse

**Files:** Create `src/crud_views/lib/view/ancestors.py`, `src/crud_views/lib/ancestor_databases.py`, `tests/test1/test_ancestor_requests.py`, `tests/test1/test_ancestor_scope.py`. Modify `src/crud_views/lib/view/base.py`, `src/crud_views/lib/views/manage.py`, `src/crud_views/lib/views/create.py`, `src/crud_views/lib/views/mixins.py`, `src/crud_views/lib/viewset/__init__.py`; migrate affected core route fixtures in `tests/test1/test_authorization_matrix.py` and `tests/test1/test_fragment_authorization.py`.

**Interfaces:** Consumes Task 2 metadata/operation helpers. Produces `authorize_ancestors(view: CrudView) -> HttpResponse | None`, private `_cv_authorize_ancestors()` and `_cv_ancestor_actor_response()` hooks, plus `ViewSet._ancestor_has_permission(user, obj: Model, permission: str) -> bool`. Stores successfully resolved objects in `view._cv_ancestor_objects: dict[str, Model]` and success flag `view._cv_ancestors_authorized`; these are instance-only. `cv_get_parent_object() -> Model` retains its public signature and returns the cached structural parent after traversal. Produces `require_default_database(alias: str, *, context: str) -> None`; contextual DB checks only run on reached nested operations.

- [ ] **Step 1: Write failing core request tests.** Drive Client requests and instrument named events (`outer_queryset`, `outer_gate`, `inner_queryset`, `inner_gate`, `local_permission`, `child`, `state`, `form`, `save`, `on_commit`). Assert exact statuses and event sequences, not sets of acceptable responses.

| Test | Setup and assertions |
| --- | --- |
| `test_core_ancestor_gate_is_independent_of_plain_or_local_child` | Parent deny with plain child/local grant: `assert response.status_code == 403`; parent allow/local deny also 403; no local gate plus parent allow succeeds |
| `test_depth_and_protected_positions` | Global/ViewSet override matrix, ancestor cascade unable to stop descendants, none-middle/all-none; `assert checked_levels == expected_levels`; denied nearest never evaluates a farther alternative |
| `test_read_write_and_complete_pair_override` | Read view/view; create/update/delete GET and POST change/view; parent delete alone does not permit child delete; change/change and view/view pairs replace defaults |
| `test_each_ancestor_resolves_its_own_permission_map` | Use a complete custom-key pair across differently named ancestor models/maps; `assert checked_permissions == expected_fully_qualified_permissions`; no reuse of the child or nearest map for a higher gate |
| `test_outer_denial_prevents_deeper_queries_and_local_work` | Outer gate denies, deeper row absent: `assert response.status_code == 403`; `assert events == ["outer_queryset", "outer_gate"]` |
| `test_scope_and_relationship_failures_are_reached_in_order` | Outer allowed, deeper missing/excluded/mismatched: 404; actor denial before any lookup; no unfiltered retry; ancestor endpoint queryset override never called |
| `test_actual_child_context_and_parent_identity` | Capture `view is requested_view`, request identity, unchanged kwargs/leaf pk/key; none immediate parent reused by create attachment/state/helper with equal model/PK/DB and object identity |
| `test_all_none_preserves_existing_actor_admission` | Core permission denial for anonymous/inactive returns existing result for valid/missing/mismatched ancestry with `assert ancestor_calls == []`; anonymous-permitting backend and public plain/manage continue to reached 404/success |
| `test_top_level_does_no_ancestor_work` | Patch traversal/provider methods to fail if called; existing top-level list/object/create/manage still behave identically |
| `test_nested_core_manage_requires_both_gates` | Public/debug/manage-group cannot bypass ancestry; ancestry success followed by local manage denial denies; both depths/all-none and reached 404 covered |

- [ ] **Step 2: Run `.venv/bin/pytest tests/test1/test_ancestor_requests.py tests/test1/test_ancestor_scope.py -n 4 -q`.** Expect the missing enforcement/order failures, without accepting unrelated fixture errors.
- [ ] **Step 3: Implement core traversal and dispatch bridges.** Resolve static declarations, effective pair/depth, and selected protected positions before loading any object. Reverse the metadata tuple for outermost-first processing. At each level call that ancestor ViewSet's queryset with the actual child view, validate its DB, resolve its configured URL PK, independently validate the declared relationship to the already resolved parent, then evaluate its selected gate before continuing. Do not assume a ViewSet queryset override retains relationship filtering. Resolve `ancestor.permissions[required_key]` only at that selected gate; missing keys raise `ImproperlyConfigured` with ViewSet/action/key. No permission map access for unselected/none levels.
- [ ] **Step 4: Implement early actor handling without child/state evaluation.** Protected ancestry rejects anonymous through the requested endpoint's supported denial behavior (plain views use Django login redirect), and authenticated inactive actors with 403. Active authenticated ancestor denial always raises `PermissionDenied`. For all-none, call only the bounded actor hook: core permission-required families evaluate their existing permission-only admission for anonymous/inactive actors, excluding `cv_get_action_object`/state; active actors defer local permission work. Manage preserves its actual public/debug/group admission logic. Preserve configured `raise_exception`/login URL/redirect field and later local behavior. A mere `PermissionRequiredMixin` type check cannot decide admission.
- [ ] **Step 5: Reuse structural parents and preserve endpoint phases.** Replace supported request-time parent rereads in `cv_get_parent_object`, create rendering/state adapters and cancel helpers with the resolved identity where present; direct out-of-request helper calls retain their bounded existing behavior. The new helper map may also supply an already-resolved higher structural parent without a second query. Leave forms, M2M through defaults, atomic/save callbacks, cancel restore and modal response processing on existing paths after ancestry. Add reached DB validation at core child queryset/read and write-alias boundaries without changing top-level paths. Task 6 extends coverage to overridden querysets and authorization routing.
- [ ] **Step 6: Run `.venv/bin/pytest tests/test1/test_ancestor_requests.py tests/test1/test_ancestor_scope.py tests/test1/test_authorization_matrix.py tests/test1/test_fragment_authorization.py -n 4`.** Migrate nested custom test views with explicit action pairs and grant ancestor model permissions where the scenario is about a local gate; keep separate ancestor-denial scenarios. Assert fragments cannot evaluate secret form choices before ancestry. Expect pass.
- [ ] **Step 7: Commit:** `feat: enforce scoped ancestor authorization for core views`.

### Task 4: Guardian Provider and Complete Legacy-Policy Migration

**Files:** Modify `src/crud_views_guardian/lib/{viewset,mixins,views}.py`, `src/crud_views_guardian/checks.py`, `src/crud_views/lib/view/ancestors.py`, `tests/test1/app/views.py`, all active `tests/test1/test_guardian*.py` consumers of removed fields, and Guardian cases in existing authorization/fragment suites. Create `tests/test1/test_ancestor_guardian.py`. Update obsolete manage field reads in this task; complete the presentation in Task 5.

**Interfaces:** Guardian overrides `_ancestor_provider()` and `_ancestor_has_permission(user, obj, permission)`. Shared helper `immediate_parent_has_permission(view_class: type[CrudView], user, parent_obj: Model) -> bool` resolves the target's nearest requirement against the immediate parent's provider; `none` returns permission success without walking farther. `GuardianParentPermissionMixin` keeps composition checking, actor response and nested no-object state responsibility; its request path delegates ancestry to the one shared guard.

- [ ] **Step 1: Add failing Guardian tests and migrate declarations that would otherwise break collection.** Search `cv_guardian_parent_permission`, `cv_guardian_parent_create_permission`, `_guardian_check_parent`, `_guardian_user_has_parent_perm`, and `_guardian_resolve_parent_perm_key` across source, tests, examples and docs. Change active fixtures deliberately; preserve old strings only in rejection tests and explanatory migration docs/history.

| Test | Setup and assertions |
| --- | --- |
| `test_guardian_ancestor_grant_matrix` | Direct/group required object grant passes; model-only denied by default and passes only with ancestor fallback; no grant denies; correct object/content type required |
| `test_core_parent_and_guardian_child_defaults` | Object-only parent grant denies for core parent; model-only passes; changing parent to Guardian reverses these outcomes |
| `test_ancestor_and_local_fallback_are_independent` | Child view fallback cannot relax ancestor; ancestor fallback cannot relax strict child object gate; ancestor setting applies consistently across descendants |
| `test_guardian_actor_responses_precede_lookup` | Anonymous default redirect and configured 403/404; inactive including superuser 403; active superuser follows backend semantics; all-none preserves Guardian early rules |
| `test_guardian_local_gates_remain_after_ancestry` | Ancestor success still filters list/checks child object and state; parent-only nested create has no model-add requirement; top-level create still requires add |
| `test_none_structural_parent_still_drives_create_state` | Farther protected ancestor supplies permission, immediate parent supplies state/attachment; disabled state denies after ancestry and writes nothing |
| `test_removed_fields_fail_before_registration` | Constructor and subclass declarations for both old fields, including `None`/old default, raise `ValidationError`; registry/manage unchanged; corrected-name retry works |
| `test_guardian_composition_guards_are_preserved` | Unsupported object/list MRO compositions still produce `crud_views_guardian.E001` and runtime errors; a deliberately plain child without the Guardian permission family works |
| `test_guardian_order_matches_core_order` | Outer denial blocks deeper queryset/local object/state calls; both mixin orders supported by existing composition checks reach the shared guard once |

- [ ] **Step 2: Run `.venv/bin/pytest tests/test1/test_ancestor_guardian.py -n 4 -q`.** Expect grant/provider/legacy-policy failures against the prior implementation.
- [ ] **Step 3: Implement Guardian evaluation and remove old request evaluation.** Use configured `guardian.ctypes.get_content_type` semantics and object checker/group grants. Fallback checks `user.has_perm(permission)` separately from the object check; never rely on the model backend receiving `obj`. Guard inactive actors. Keep checkers request-local. Preserve strict `GuardianViewSet.get_objects_for_user()` and permission-vocabulary caching. Core neither imports Guardian nor interprets Guardian permission maps itself.
- [ ] **Step 4: Reject removed declarations before any registration side effect.** Remove framework defaults; inspect constructor mapping plus actual user subclass declarations (including Pydantic fields, class variables and inherited user declarations) without misidentifying the removed framework defaults as user use. Keep the prior rejection of the already-removed ViewSet-level `cv_guardian_accept_global_perms`. Use existing Pydantic-style construction errors with replacement guidance.
- [ ] **Step 5: Preserve local adapters and migrate every callable consumer.** Implement the early actor hook on the Guardian object, queryset and parent adapters so every supported MRO retains its existing anonymous/inactive admission, without using the state-bearing local `has_permission()` as the preflight. Guardian parent dispatch calls the shared guard first, retains existing top-level actor behavior and no-object parent state gate, and no longer resolves/checks its old parent policy. Keep object/queryset composition protection. Redirect existing parent helper calls to `immediate_parent_has_permission`; use target class/actual key and the ancestor's fallback, not the child view's flag. Remove stale manage field accesses immediately. Do not add child-add fallback in nearest-only mode or bypass state for `none`.
- [ ] **Step 6: Run `.venv/bin/pytest tests/test1/test_ancestor_guardian.py tests/test1/test_guardian*.py tests/test1/test_authorization_matrix.py tests/test1/test_fragment_authorization.py -n 4`.** Existing old-policy tests become named new-policy/state preservation tests; unchanged top-level/local expectations remain. Expect pass and no live access to either removed field.
- [ ] **Step 7: Commit:** `feat: migrate Guardian ancestry to shared policies`.

### Task 5: Bounded Rendering Helpers and Manage Diagnostics

**Files:** Modify `src/crud_views_guardian/lib/{mixins,views}.py`, `src/crud_views/lib/view/base.py`, `src/crud_views/lib/views/{create,manage}.py`, `src/crud_views_guardian/templates/crud_views/snippets/guardian/config_table.html`, and the existing core manage template under `src/crud_views/templates/crud_views/view_manage.html`. Create `tests/test1/test_ancestor_helpers.py`; update `tests/test1/test_guardian_child_link_visibility.py`, `tests/test1/test_guardian_policy.py`, and existing cancel tests.

**Interfaces:** Consumes `immediate_parent_has_permission` and request-local parent identities. Manage context adds `ancestor_config` with declared `provider`, effective provider, `accept_global_perms`, declared/effective cascade, read/write pairs and literal action entries. `guardian_policy` continues to describe only endpoint-local fallback; nested create reports it not applicable when no remaining local consumer exists.

- [ ] **Step 1: Write failing helper and rendered diagnostic tests.**

| Test | Setup and assertions |
| --- | --- |
| `test_existing_helpers_use_immediate_parent_policy` | Collection link, create button, `cv_create_has_access`, cancel: assert model/Guardian provider and target nearest requirement determine their existing local gate |
| `test_none_parent_helper_does_not_walk_farther` | Immediate `none` plus farther denied ancestor: helper may allow while request denies; `assert higher_queries == 0` during helper evaluation |
| `test_helper_retains_actor_state_custom_denials` | `none` does not erase existing inactive/state/custom denial; missing parent context returns `False`; malformed configuration raises instead of returning False/True |
| `test_helper_identity_and_ambiguous_m2m` | Request helper receives the resolved parent instance; supported single-FK child input resolves it; ambiguous child-only M2M input returns `False` |
| `test_manage_separates_declared_ancestor_and_local_fallback` | Render both flags with opposite values and assert independent labels; nested create local fallback is not applicable; policy display makes no access claim |

- [ ] **Step 2: Run `.venv/bin/pytest tests/test1/test_ancestor_helpers.py -q`.** Expect targeted helper/presentation failures.
- [ ] **Step 3: Complete helper migration and diagnostics.** Keep callbacks, state handling and unavailable-context behavior. Do not catch `ImproperlyConfigured` as ordinary unavailable access. Do not extend ancestry evaluation into breadcrumbs, generic buttons, child tabs, cancel destinations or every rendering path. Show policy scopes on both core/Guardian manage pages; remove descriptions implying that view fallback controls parents. Retain strict-helper policy display.
- [ ] **Step 4: Run `.venv/bin/pytest tests/test1/test_ancestor_helpers.py tests/test1/test_guardian_child_link_visibility.py tests/test1/test_cancel*.py tests/test1/test_guardian_policy.py tests/test1/test_manage.py -n 4`.** Expect exact rendered values, unchanged existing custom-helper denials and no new higher-level rendering queries.
- [ ] **Step 5: Commit:** `fix: migrate parent helpers and ancestor policy diagnostics`.

### Task 6: Scoped Identity, Database Boundaries, and Mutation Evidence

**Files:** Create `tests/test1/test_ancestor_databases.py`, `tests/test1/test_ancestor_mutations.py`. Extend `tests/test1/test_ancestor_scope.py`, `src/crud_views/lib/ancestor_databases.py`, `src/crud_views/lib/view/ancestors.py`, `src/crud_views/lib/view/base.py`, `src/crud_views/lib/views/mixins.py`, `src/crud_views_guardian/lib/{viewset,mixins,views}.py` and shared test fixtures as required by the boundary tests.

**Interfaces:** Consumes previous guards and parent identity. Database helpers stay private: `require_default_database` and `validate_authorization_databases(user, *, provider: str) -> None` validate reached ORM aliases/router selections and actor object identity before relevant auth queries; they do not change routing. Validate effective querysets (including supplied queryset arguments/custom ViewSet overrides), loaded object `_state.db`, and actual write alias where the ORM operation is reached.

- [ ] **Step 1: Add failing boundary tests using existing independent `default`/`shard` databases and `database_routes` fixture.**

| Test | Setup and assertions |
| --- | --- |
| `test_scoped_ancestor_visibility_is_authoritative` | Manager, soft-delete/tenant ViewSet exclusions despite valid grants yield 404 in both modes and at none levels; overridden queryset cannot waive declared membership |
| `test_default_database_selection_is_preserved` | Implicit default and `.using("default")` succeed; queryset identity and actual child context remain intact |
| `test_reached_nondefault_orm_and_auth_paths_fail` | Ancestor/child `.using("shard")`, read/write routers, actor loaded from shard, Permission/ContentType/group/Guardian object-grant routing: `with pytest.raises(ImproperlyConfigured)`; colliding default/shard PKs must not produce success or a fallback read |
| `test_database_and_permission_key_errors_obey_order` | Outer deny then deeper shard/missing key gives 403 without deeper validation/query; reached shard/missing selected key raises configuration error; higher unselected key in nearest-only is never resolved |
| `test_queryset_override_cannot_bypass_child_database_guard` | Custom endpoint queryset, supplied `get_object(queryset=...)`, Guardian-filtered queryset and write alias are checked at their supported read/write entry points |
| `test_top_level_routed_behavior_is_unchanged` | Existing top-level nondefault read/write/delete and auth cases retain their previous outcomes |
| `test_shared_m2m_edit_only_authorizes_url_path` | Publisher A/B share Genre; grant A's gate only; edit via A changes B-visible same row; `assert checked_parent_pks == [a.pk]` in both depths |
| `test_valid_editable_fk_move_remains_application_owned` | Valid Book update through A changes publisher to B without a new B gate; an application form excluding the FK prevents the submitted move |
| `test_shared_delete_keeps_normal_semantics` | Delete through A deletes the shared object normally, not merely A's membership; both modes |

- [ ] **Step 2: Run `.venv/bin/pytest tests/test1/test_ancestor_databases.py tests/test1/test_ancestor_scope.py tests/test1/test_ancestor_mutations.py -n 4`.** Expect missing reached-path guards or scope gaps; do not reinterpret a database error as ordinary denial or skip shard tests.
- [ ] **Step 3: Close the demonstrated boundary gaps.** Inspect queryset `.db` before evaluation, preserving explicit `.using`. Validate write/router choice before transaction/save, including when `cv_atomic=False`. Check auth selections at the gate that will use them, including custom Guardian permission model selections. Cached permission vocabulary must not conceal a newly invalid route. Keep this a bounded check of supported Django/Guardian paths, not an arbitrary backend SQL-interception framework. Do not preflight deeper routes before outer gates; Resource application loaders remain outside the new ORM-leaf restriction.
- [ ] **Step 4: Preserve mutation behavior; add no mutation engine.** Test existing FK/M2M create attachment and through defaults using the resolved structural parent. The application-owned restricted form example is test/demo code, not a framework default. Explain any otherwise redundant identity or database checks in code comments at their entry points.
- [ ] **Step 5: Run `.venv/bin/pytest tests/test1/test_ancestor_databases.py tests/test1/test_ancestor_scope.py tests/test1/test_ancestor_mutations.py tests/test1/test_delete_databases.py tests/test1/test_transactions.py -n 4`.** Expect pass, zero unauthorized mutations/callbacks, and unchanged top-level routing evidence.
- [ ] **Step 6: Commit:** `fix: enforce nested identity and database boundaries`.

### Task 7: Shipped Extension and Endpoint Integration

**Files:** Create `tests/test1/test_ancestor_extensions.py`. Extend `tests/test1/test_fragment_authorization.py`, `tests/test1/test_resource_views.py`, `tests/test1/test_authorization_matrix.py`, and `tests/test1/ancestor_cases.py`. Modify only demonstrated integration gaps in `src/crud_views/lib/{resource.py,formsets/mixins.py,views/child.py}`, `src/crud_views_polymorphic/lib/create_select.py`, `src/crud_views_object_detail/lib/views.py`, `src/crud_views_workflow/lib/views.py`, or shared classifier/guard; avoid redundant guards in every `get()`.

**Interfaces:** All families consume the shared guard and Task 2 classification. Resource `cv_get_items`/`cv_get_item` signatures and kwargs stay unchanged; fragment authorization uses the owning endpoint's operation pair. Redirect destinations remain separate requests.

- [ ] **Step 1: Write failing request-level integration tests, beyond the classifier unit tests.**

| Test | Setup and assertions |
| --- | --- |
| `test_all_shipped_families_reach_ancestry_before_local_work` | Core list/card/detail, ObjectDetail, polymorphic detail/create/update/delete/selection, ordered actions and normal subclasses/permission variants: deny ancestor and assert 403 with zero child/state/form/side-effect calls |
| `test_renamed_builtin_and_exact_action_override_requests` | Renamed CRUD retains family; exact override replaces the whole pair; Card-only navigation uses Card actual key and later List registration does not change it |
| `test_nested_custom_endpoint_requires_explicit_pair` | Core/Guardian generic Action, object/no-object CustomForm, Workflow, arbitrary custom redirect: missing pair errors before actor/object work in both depths/all-none; declared pair reaches existing local behavior; top-level needs no declaration |
| `test_fragments_authorize_the_owning_editor` | Read grant alone cannot open Write editor fragment; ancestor deny yields no secret choices or HTML; allowed ancestry still enforces local object/state and fragment-coordinate 400 rules |
| `test_resource_leaf_authorizes_before_application_loading` | List/detail below one and multiple ORM ancestors, both depths/plain and local permission-required: denial prevents loaders; success passes original kwargs and application scoping; top-level unchanged |
| `test_nested_manage_local_gate_is_independent` | Core and Guardian public/group manage still require ancestry; local denial after ancestor success remains; all-none preserves existing actor behavior and reached 404 |
| `test_redirect_child_is_read_and_destination_is_independent` | Built-in redirect works without action entry, explicit pair overrides it, denied ancestry prevents object/redirect processing; allowed source redirect followed by denied destination returns destination denial |

- [ ] **Step 2: Run `.venv/bin/pytest tests/test1/test_ancestor_extensions.py tests/test1/test_fragment_authorization.py tests/test1/test_resource_views.py -n 4`.** Expect uncovered integration failures; if an existing path already satisfies an assertion, record it as preservation evidence rather than adding code to force a red test.
- [ ] **Step 3: Repair only demonstrated integration gaps.** Keep dispatch bridges before fragment object loading, Resource loaders and extension form handling. Extend finite family recognition only to the approved families. Preserve local permissions and independent destination requests. Add exact action declarations to nested example/test endpoints; top-level custom forms/workflow stay unchanged.
- [ ] **Step 4: Run `.venv/bin/pytest tests/test1/test_ancestor_extensions.py tests/test1/test_fragment_authorization.py tests/test1/test_resource*.py tests/test1/test_authorization_matrix.py -n 4`.** Expect exact response/status/state assertions to pass. Run core-without-Guardian and optional-polymorphic subprocess tests again if imports changed.
- [ ] **Step 5: Commit:** `test: cover ancestor authorization across shipped endpoints` (use `fix:` if production integration repairs were required).

### Task 8: Performance, Revocation, Release Documentation, and Final Verification

**Files:** Extend `tests/test1/test_ancestor_performance.py`, `tests/test1/test_ancestor_guardian.py` and the performance note. Create `docs/reference/ancestor_authorization.md`; modify `docs/reference/{nested,settings,guardian,resources,request_lifecycle}.md`, `docs/migrating-1.0.md`, `CHANGELOG.md`, `mkdocs.yml`, and affected examples discovered in Task 4.

**Interfaces:** No new production API. Final documentation describes exactly the shipped behavior from Tasks 1–7 and links to existing local permission/state contracts.

- [ ] **Step 1: Add revocation and measurable-work tests.** `test_revocation_applies_on_next_request`: grant → fresh request succeeds → revoke direct/group/model grant as applicable → fresh request denies; do not reuse a Django user's stale permission cache as a new authentication session. `test_no_top_level_ancestor_queries` asserts zero ancestor queryset/provider calls. `test_nearest_only_never_checks_higher_permissions` asserts only the selected gate is evaluated while higher relationship reads still occur. `test_one_and_three_level_query_costs` records both modes across the same plain/Guardian list/detail/create fixtures from Task 1.
- [ ] **Step 2: Run `.venv/bin/pytest tests/test1/test_ancestor_performance.py tests/test1/test_ancestor_guardian.py -n 4 -v`.** Expect behavioral assertions to pass. Record actual measured before/after counts by endpoint, chain length, mode and cache condition, including parent reuse, vocabulary, grant and local-gate queries. Explain changed outcomes/work relative to the weaker legacy baseline; do not invent a fixed backend-independent query budget. Fix any repeated identical ancestor check caused by bridge reentry.
- [ ] **Step 3: Write user documentation and migration examples.** Include public imports, complete typed pairs/raw settings maps, provider versus request scopes, both cascade override directions, Read/Write family table, literal action-key rules, early/interleaved failures, and custom dispatch cooperation. Include a complete `approve` pair example and explain check/runtime failure in both modes; built-in classified and top-level custom exceptions; removed fields and `None` meanings; core-parent object-only/model-only outcomes; explicit migration to Guardian parent; independent fallback across descendants; nested manage gates; authoritative ViewSet queryset with actual child context; default-DB boundary; Resource leaf application scoping; shared-M2M/FK move/delete boundary and an application restriction example; request-authoritative/UI limitation. No identifying downstream examples.
- [ ] **Step 4: Add the `### Breaking` release entry and matching `docs/migrating-1.0.md` section.** Link the reference tables; make removed fields, changed provider defaults, independent fallback, mandatory nested custom declarations and nested manage behavior prominent. Update stale present-tense old-policy prose and examples, while retaining historical design notes and rejection tests.
- [ ] **Step 5: Run final verification once the scoped suites pass.**

```bash
.venv/bin/ruff check src tests
.venv/bin/ruff format --check src tests
.venv/bin/pytest tests -n 4
.venv/bin/nox -s "tests-3.12(django='4.2')" "tests-3.12(django='5.2')" "tests-3.12(django='6.0')" -- -n 4
.venv/bin/mkdocs build --strict
.venv/bin/nox -s package
```

Use `nox --list` to confirm session selectors first and the repository's installed runner if these executables are elsewhere. The nox sessions already supply `-n auto`; the explicit trailing `-n 4` bounds workers when resources are shared. Run versions sequentially with multicore workers inside each. Exercise remaining supported Python combinations through the existing CI/nox matrix; record unavailable environments as unverified, never passed. Compare docs failures with baseline if strict mode has pre-existing warnings. Do not interrupt an already-running verification just to change worker count.

- [ ] **Step 6: Audit acceptance coverage and stale consumers.** Search source/tests/examples/docs for removed field/helper names and classify every remaining hit as rejection/migration/history. Map every row of the design's acceptance table using the crosswalk below; verify concrete test names and results exist. Record commands, versions, counts and any genuine limitations in the performance/verification note. Review the final diff for scope and query regressions; no persistent policy state, speculative backend framework, full-chain UI authorization, or automatic mutation restriction should appear.
- [ ] **Step 7: Commit:** `docs: document ancestor authorization and migration evidence`.

## Acceptance Crosswalk

| Canonical acceptance area | Owning tasks / evidence |
| --- | --- |
| Independent gates; selection and precedence; requirements | 3–4: core/Guardian request, depth and permission matrices |
| Finite families; custom declarations; exact keys | 2 and 7: static classifier plus real endpoint/fragment requests |
| Actor/provider behavior; early actor order; interleaved enforcement; downstream work | 3–4 and 7: event order, actor outcomes, zero child/form/write calls |
| Relationships/creates; queryset scope; parent identity | 2–3 and 6: FK/M2M/UUID, filtering and resolved structural parent |
| Resource leaves | 2 and 7: static boundary, application loader/scoping evidence |
| Database boundary | 3 and 6: reached routing, colliding identities, unchanged top-level paths |
| Construction failures; validation timing; URL construction safety; top-level policy | 1–2 and 4: no-query validation, registry atomicity, real URL import, forward references |
| Manage; redirect | 3–5 and 7: independent gates, diagnostics, independent destination |
| Migration; helpers/diagnostics | 4–5 and 8: removed fields, provider/fallback outcomes, bounded helpers, release instructions |
| Mutation boundary | 6 and 8: shared edits/moves/deletes and documented application restriction |
| Performance/revocation | 1 and 8: measured baseline/final comparisons and fresh-request revocation |
| Release documentation | 8: Breaking + migration + public reference/examples |

D-01–D-22 and D-26–D-37 drive the configuration/traversal/operation/helper tasks; D-39–D-53 drive Resource, migration, actor order, construction, manage/redirect, literal keys, identity/database, mutation and safe-walk evidence. D-23/D-25/D-38 remain history/handoff boundaries, D-24 controls public examples, and D-50's import correction is reflected in the public documentation. No obsolete D-29 blanket Resource exclusion is carried forward.

## Plan Self-Review and Handoff

- Specification scope is one shared authorization mechanism; Guardian and extensions are dependent integrations, not independent projects.
- All acceptance rows have owners above. Tests focus on observable access, ordering, identity, writes and query work rather than mirroring implementation bodies.
- Private module names, four explicit dispatch bridges, helper signatures and test organization are builder choices in this plan; public behavior is unchanged from v2.
- Implementation starts only after a separate execution instruction. Use an isolated execution worktree according to the selected execution skill; this plan assigns no GSD phase.
- Recommended execution: subagent-driven, sequentially, because the request-order and Guardian migration tasks each warrant an independent review before later integrations. Native execution remains a valid choice.
