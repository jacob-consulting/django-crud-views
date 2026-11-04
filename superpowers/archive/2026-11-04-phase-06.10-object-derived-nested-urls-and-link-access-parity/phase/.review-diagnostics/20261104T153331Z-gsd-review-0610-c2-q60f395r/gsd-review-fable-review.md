# Cross-AI Plan Review — Phase 06.10, cycle 2 of 8

Baseline reviewed: `f6990f3` (all six PLAN.md files). Source grounding: live reads of `src/crud_views/lib/view/base.py`, `buttons.py`, `views/card.py`, `views/create.py`, `views/delete.py`, `views/child.py`, `table/columns.py`, `breadcrumb.py`, `viewset/__init__.py`, `viewset/parentviewset.py`, `resource.py`, `deletion.py`, `crud_views_guardian/lib/{mixins,views,viewset}.py`, `templatetags/crud_views.py`, the three browser harness files, `tests/test1/app/{models,views}.py`, `test_guardian_delete.py`, `test_delete_databases.py`, `test_breadcrumb.py`, `test_viewset.py`, `conftest.py`, `docs/development/stability.md`, `docs/reference/{buttons,context_buttons}.md`, `CHANGELOG.md`. The intel authority has no Python symbols, so every symbol the plans *declare as new* (`resolution.py`, `_ParentResolution`, `link_context.py`, `get_url`, `get_parent_pks`, `cv_guardian_has_parent_access`, `_guardian_declared_permission`, `_cv_has_access_for_rendering`) is UNCHECKABLE by that authority; I treat them as planned artifacts. Everything cited below with a line number was read in this checkout. No product tests were run.

---

## 06.10-01

**Summary.** Shared resolver, public `ViewSet.get_parent_pks`/`get_url`, isolated test-model family, precedence/metadata/query/error matrix. Three tasks, wave 1.

**Strengths**
- The compatibility boundary is now concrete and matches the live seams: `ViewSetKeyFoundError` stays at `get_view_class` (`src/crud_views/lib/viewset/__init__.py:339-343`) and at the view callers that skip on it (`src/crud_views/lib/view/base.py:674,748,754`; `src/crud_views/lib/table/columns.py:48-50`), `CrudViewError` stays at `cv_get_cls_assert_object` (`base.py:550-556`), and only the new public helper translates unknown keys. Plan text: `06.10-01-PLAN.md` "Compatibility boundary (C1-M01/M02)".
- The page-kwargs overwrite and falsey-value rejection that the plan replaces are exactly `base.py:598-604`; keeping `cv_get_url` → `cv_get_router_and_args` (`base.py:611-617`) preserves the five breadcrumb callers (`src/crud_views/lib/breadcrumb.py:168-193`) and the four `cv_get_child_url` consumers (`buttons.py:229`, `card.py:58`, `columns.py:42`, `child.py:23`).
- Fixture isolation is real: `src/crud_views/lib/deletion.py:117-140` walks `get_candidate_relations_to_delete(opts)` from the deleted model, so models with no FK to `Publisher` cannot alter its boundaries; `tests/test1/app/` has no `migrations/` directory, so syncdb creates the new tables without a migration file.
- Metadata handling is correct in principle: `ParentViewSet.get_pk_name/get_attribute` (`parentviewset.py:56-66`) are the only registered names; `ViewSet.pk` auto-detects `CharField` as `STR` (`viewset/__init__.py:130-143`), so the custom string PK fixture will route.

**Concerns**
- **MEDIUM (C2-N1) — view-path query bound for in-scope multilevel rows is unpinned.** Plan 01 pins URL-only bounds (standalone, no page kwargs) and phrases page-fragment reuse as optional: "Page fragments *may* fill an unresolved boundary only when the known connecting parent agrees" (`06.10-01-PLAN.md`, Resolution contract). Today the view path costs zero queries for ancestry (`base.py:598-604`). Under strict object derivation at h=2 (`cv_booknote_bc`, `tests/test1/app/views.py:1034`), each row needs `note.book` to reach `publisher_pk`, i.e. one query per row on every nested list page (descriptor-cached across the row's actions, but still N+1). A pinned existing test will trip first: `tests/test1/test_breadcrumb.py:297-302` asserts exactly 2 queries for `cv_breadcrumb()` on a BookNote detail view, and that method calls `cv_get_router_and_args(..., obj=note)` five times (`breadcrumb.py:168-193`) *before* the ancestor loads; a `note.book` load makes it 3. Plan 02-02 replays `test_breadcrumb.py`, so this would surface late, as an execution failure, rather than being decided now. The plan should make agreeing-page-fragment fill mandatory for the view path (zero added ancestry queries when the row's raw PK-targeting FK equals the page kwarg), add an N-row list-page zero-delta assertion to the `queries` group, and name `test_ancestor_query_count` as a preservation pin.
- **LOW (C2-N3) — wrong-model `obj` on collection destinations becomes a new error.** Today `obj` is only read for object targets (`base.py:590-592`); the plan's "wrong-model inputs always raise ValueError" rule would also fire for collection targets reached via `cv_get_context_buttons(keys, obj=...)` from custom templates (`base.py:645-661`). Either scope the rule to object destinations and parent-context roles, or add it to plan 05's migration text.
- **LOW (C2-N6) — import cycle hazard.** `resolution.py` lives inside the `viewset` package; `src/crud_views/lib/views/child.py:6-9` documents that importing any `viewset` submodule executes the package `__init__`, which imports `..view`. The resolver must import only `.parentviewset`/Django metadata at module level.

**Suggestions**
- State the page-fill rule as a MUST with its own bound row ("Object, O's connecting raw PK FK agrees with W: fill remaining levels from W, 0 queries").
- Add the breadcrumb pin and an N=8 nested list render to `-k queries`.

**Risk Assessment.** Medium. Semantics are well specified; the unresolved risk is a quiet performance regression on ordinary nested pages and a late-failing pinned test.

---

## 06.10-02

**Summary.** View-builder integration, scope roles for the five button kinds, ContextVar carrier for destination resolution, core `CreateView` state ownership, hook/isolation/navigation preservation. Two tasks, wave 2.

**Strengths**
- Scope roles are now exact and match the code: `SiblingContextButton` uses raw current-URL kwargs and `cv_has_access(user, None)` (`buttons.py:287-301`); `FilterContextButton` builds the list URL with no row (`buttons.py:337`); `ParentContextButton` already takes idx>0 ancestors from page kwargs (`buttons.py:159-166`) and gates on the URL parent (`buttons.py:176-189`), so "bind its target's remaining page ancestor chain" is a faithful description. Plan text: `06.10-02-PLAN.md` "Scope roles (C1-H3)".
- C1-M07 is grounded: `base.py:990` dereferences `viewset.parent.name` with no None guard; `ParentViewSetError` is already imported (`base.py:41`).
- The one-scope-per-assembly points are the right ones: `_cv_get_action_context` (`base.py:758-778`), `ContextButton.get_context` (`buttons.py:101-118`), both card branches (`card.py:57-88`). The hook-count contract is checkable because every site calls `cv_has_access` exactly once today.
- Owning core `CreateView` state (`create.py:36-70`, including the broad `ObjectDoesNotExist` catch at 45-48 and the page-kwargs lookup at 55-69) in 02-02 is the correct owner split for C1-M06.

**Concerns**
- **LOW (C2-N8)** — `owner_task` capture: `asyncio.current_task()` raises `RuntimeError` with no running loop; the carrier must guard the synchronous path. The planned sync tests would catch it, but the plan should say "None when no loop".
- **LOW** — naming: the "URL-free `cv_has_access` templatetag" the plan tests is the `cv_context_has_permission` filter (`src/crud_views/templatetags/crud_views.py:601-607`), which also swallows every exception when resolving the key (line 605). Name it exactly so the test targets the real caller.
- **LOW** — see C2-N1 above: this plan's `navigation_preservation` is where `test_breadcrumb.py::test_ancestor_query_count` will fail if plan 01 does not pin the page-fill rule.

**Suggestions**
- Add `tests/test1/test_breadcrumb.py::TestAncestors::test_ancestor_query_count` as a named must-pass in 02-02's verify block.
- Record in the summary which page-A/row-B rendering fixtures are *constructed* (unscoped view with mixed rows) versus stock scoped pages, so goldens are known to stay byte-identical for the latter.

**Risk Assessment.** Medium-high. The ContextVar carrier is the most intricate piece in the phase; the plan now specifies immutability, owner identity, `finally` reset and nested restore, which is enough to review the implementation against.

---

## 06.10-03

**Summary.** Declared-permission diagnostics (D-11), destination-parent Guardian gate (D-09/D-10), explicit create MRO wiring, certified-parent ownership, measured Guardian costs. Three tasks, wave 3.

**Strengths**
- MRO trace supports the cooperative design: `GuardianDetailViewPermissionRequired(GuardianParentPermissionMixin, GuardianObjectPermissionMixin, …)` (`views.py:32-35`, same shape for update/delete/action/list/card at 38-41, 230-254). A `cv_has_access` on the parent mixin runs first and `super()` reaches the terminal object/queryset implementations (`mixins.py:85-98`, `143-144`), neither of which calls `super()`. `GuardianCreateViewPermissionRequired` defines its own `cv_has_access` (`views.py:344-387`) ahead of the mixin, so the plan's explicit create modification (C1-H4) is required and correctly named.
- Request ordering for C1-H5 is structurally achievable: `GuardianParentPermissionMixin.dispatch` runs composition → anonymous → inactive before `super().dispatch()` (`mixins.py:313-322`), and `has_permission` (`mixins.py:307-311`) only runs inside that `super()` chain, so a create-specific declaration guard there precedes `PermissionRequiredMixin` reaching the core assertion (`base.py:1062-1070`).
- D-11 targets are the actual bugs: `perms = (perm,) if perm else ()` (`base.py:1087`), `perm.split(".")` (`mixins.py:72,97,368`), and `get_objects_for_user(user, None, …)` (`mixins.py:205-212`). The positive-only permission cache (`viewset/__init__.py:452-470`) is what `migration_retry` must preserve; `test_viewset.py:76-102` is the existing precedent.
- Certified-parent ownership (C1-H1) is coherent with both consumers of `_cv_cancel_target_available`: cancel (`base.py:875-877`) and the protected adapter, which pre-binds the certified instance through `destination._cv_cancel_parent_object = lambda: parent` (`delete.py:356-369`). The mixin override (`mixins.py:248-269`) is the single gate the plan retains.

**Concerns**
- **MEDIUM (C2-N2) — same-parent N-row list cost is not measured.** `_guardian_user_has_parent_perm` instantiates a fresh `ObjectPermissionChecker` per call (`mixins.py:366-368`), and rendering calls `cv_has_access` once per row per action (`base.py:772` via `cv_get_list_action_group`). The new parent gate therefore adds parent-permission SQL per row per action and, unless the row's agreeing raw FK reuses the rendering view's already-resolved URL parent instance, one parent load per row. 03-03 measures "rendered N-parent cards" (N distinct parents) but not the common nested list page where N rows share the page parent. Add that case with a numeric budget and specify reuse of the page parent instance (resolution only, not a permission cache, so still within the no-cache rule).
- **LOW** — the top-level create guard is described as living in `GuardianParentPermissionMixin.has_permission`, which every parentless Guardian view traverses (`mixins.py:307-311`); the plan already limits it to "the top-level create's add mapping", so make the predicate explicit (`parent is None and cv_permission == "add"`) to keep detail/list untouched.

**Suggestions**
- In `queries`, pin: same-parent list page N=1/4 (per-row delta), distinct-parent cards N=1/4, helper-only.
- State in the summary the measured delta versus current behavior for a nested Guardian list page so plan 05 can document it honestly.

**Risk Assessment.** High (authorization surface), mitigated by opposite-grant render+request matrices, explicit create MRO handling, the single certified gate, and no new cache.

---

## 06.10-04

**Summary.** Multilevel protected/cascade candidates through `get_url(strict=False)`, preserved certification, identity/topology/query regressions. Two tasks, wave 4, now serialized after plan 03.

**Strengths**
- The replacement target is precisely `cv_get_related_object_url` (`delete.py:192-210`), which today builds only one parent level and whose `getattr(obj, parent_attr, None)` would even return a manager for M2M nesting; the independent certifier `_cv_get_protected_object_url` (`delete.py:212-372`) is untouched, and visibility-first ordering (`delete.py:443-449`) and cascade calls (`delete.py:453-456`) are preserved as stated.
- The ordered-ownership paragraph makes C1-H1's integration gate executable: wave 4 `depends_on: ["06.10-03"]`, and 04-01's `fails_when` includes repeated/lost certified-instance identity.
- C1-M18 is grounded: `database_routes` (`tests/test1/conftest.py:136-170`) is request-local and supports per-model overrides, which is exactly what an intermediate-ancestor-on-wrong-alias case needs; `test_protected_target_database_identity` (`test_delete_databases.py:167`) is the precedent.
- C1-M12: the counter to replace is `test_protected_adapter_query_budget` (`test_delete_databases.py:222-269`), including its quadratic negative control.

**Concerns**
- **LOW (C2-N9)** — "supply a visible saved nested blocker through its read-only inspection result seam" should name the mechanism: `DeletePreviewContribution.protected` via `cv_get_delete_preview` (`deletion.py:47-50`, merged at 184-246). Overriding `cv_get_related_objects` is rejected by E263 (`delete.py:88-96`) and patching `_cv_inspect_deletion` would skip merge validation, so the provider route is the only one that keeps "the candidate and destination remain real".
- **LOW** — first-exact-model selection uses `viewset.model == type(obj)` (`delete.py:195-197`); the plan preserves it, but the isolated fixture must register the leaf ViewSet under the concrete class, not the inherited child, or the first match differs from the destination.

**Suggestions**
- Add one cascade-tree case at h=2 to show the previously `NoReverseMatch`-suppressed node (`delete.py:207-209`) now links at the same per-node cost.

**Risk Assessment.** Medium. Certification is unchanged; the risk is confined to candidate generation and measured cost.

---

## 06.10-05

**Summary.** Paired Breaking/migration, executable recipes, reference updates, Phase 7 handoff subsection in `stability.md`. Three tasks, wave 5.

**Strengths**
- Marker/fence extraction has exact precedent (`tests/test1/test_delete_migration_docs.py:48-76`) and the Breaking/migration pairing test already exists (`:725-729`), so the new entry is automatically checked for its anchor.
- The handoff placement resolves C1-M13 without pre-empting Phase 7: `docs/development/stability.md` currently lists only `GuardianViewSet`, `GuardianManageView` and the `Guardian*PermissionRequired` variants for the extension, so the mixin and its method need a scoped subsection rather than an edit of the existing Public API list.
- C1-M11 content is correct against the code: superusers currently pass `has_perms(())` (`base.py:1087-1088`), and the sibling/parent/breadcrumb ancestor behavior documented at `docs/reference/context_buttons.md:245-247` and `breadcrumb.py:206-260` is what stays.

**Concerns**
- **LOW (C2-N10)** — `test_protected_public_surface_inventory` already exists (`test_delete_migration_docs.py:770`); the new `public_inventory` group must extend rather than duplicate or contradict it.
- **LOW** — the strict-docs verify path `/tmp/cv-069-docs` is inherited; cosmetic.
- **LOW** — if C2-N1/C2-N2 are accepted, the migration text should state the measured page-level cost change for multilevel nested and Guardian list pages, not only standalone helper bounds.

**Suggestions**
- Include the C2-N3 wrong-model-on-collection behavior in the migration bullets if plan 01 keeps that rule.

**Risk Assessment.** Low. Documentation is executable and paired; residual risk is accuracy of cost claims, which depends on plans 01/03 pinning the page-path numbers.

---

## 06.10-06

**Summary.** Browser identity contract, nested fixture routes, schema/validator extension, full gate matrix and final evidence revalidation. Three tasks, wave 6.

**Strengths**
- The identity divergence it fixes is real: runner `sourceHashes()` (`tests/browser/protected-delete.cjs:36-40`) and server `source_hashes()` (`tests/browser/protected_delete_server.py:70-80`) both use `git ls-files` (tracked only) plus four explicit files, compared at startup (`cjs:133`); an untracked `resolution.py` would be silently absent from both. Adding `--others --exclude-standard` on both sides and asserting the two new module paths closes it.
- `recipes(source, expected)` (`cjs:23-35`) and the old `all` screenshot rule (`cjs:74-78`) are preserved by name; the nested family gets its own screenshots, consistent with `cjs:198` only capturing under `opts.case === 'all'`.
- C1-M17 is grounded: `FixtureMiddleware` applies every patch to every request (`server.py:93-136`), so route/scenario scoping is necessary once Guardian/action pages share the server.
- C1-M15: `validateEvidence` requires `detailStatus === 200` (`cjs:53`), so the plan's choice to keep 403 coverage in plan 03's Python tests is the only consistent one.
- Required runtimes exist: `.nox/tests-3-12-django-5-2`, `tests-3-12-django-4-2`, `crispy_floor-3-12-django-6-0`; `npm run test:integration` is defined (`package.json:12`); `examples/bootstrap5/pytest.ini` exists.

**Concerns**
- **LOW (C2-N5)** — `git ls-files --others --exclude-standard` over `tests/test1` admits any transient untracked file an executor leaves there into the identity set (`.gitignore:3-4` covers only `__pycache__`/`*.pyc`), so the final 06-03 validation can report "stale" spuriously and force a recapture. Restrict `--others` to the two expected new module paths, or assert the untracked subset equals an expected list.
- **LOW (C2-N4)** — the existing tooltip harness strips the fence's final LF (`tests/browser/action-tooltips.cjs:30`; `action_tooltips_server.py:66`), while plan 06 preserves it for the same `tooltip-recipe` fences; the stock leaf ends with LF (`tags/button/action.html` tail), so rendering is fine, but two harnesses will publish different hashes for one fence family. Either reuse the existing extractor or document the deliberate difference.

**Suggestions**
- Have 06-01's negative tests include "untracked scratch file appears under tests/test1 after capture" to prove the chosen manifest rule behaves as intended.

**Risk Assessment.** Medium. Evidence integrity is strong; residual risk is harness brittleness, not product behavior.

---

## Cross-plan assessment

- **Serialization is sound.** 01 → 02 → 03 → 04 → 05 → 06 with `depends_on` chains; the only semantic cross-plan seam (certified parent) now has one owner (03-02) and one integration gate (04-01) with a stated reopen rule. No parallel-wave hazards remain.
- **Decisions D-01–D-16** each map to executable tasks and to `06.10-VALIDATION.md` rows; I found no contradiction with CONTEXT.md. The research matrix and plan 01's table agree.
- **Requirements** NURL-01–04, AUTH-08/09 are all referenced by at least one plan with tests; AUTH-08/09 are registered in `REQUIREMENTS.md:211-212`.
- **Preservation of goldens.** For stock scoped pages the object-derived chain equals the page chain, so hrefs and markup should stay byte-identical; plans 02/06 should say so explicitly (only constructed mixed-row fixtures change hrefs).
- **New cycle-2 findings:** two MEDIUM (C2-N1 view-path/breadcrumb query pin; C2-N2 same-parent Guardian list cost), eight LOW. None contradict a locked decision; both MEDIUMs are pin-and-measure additions, not design changes.
- **UNCHECKABLE** items: all declared new symbols and the proposed signatures; cycle-1 "divergent views" (ContextVar vs explicit adapter) remain a reviewable design choice with rationale recorded in plan 02.

## Closure ledger (C1 findings)

| ID | Status | Evidence (plan + source) |
|---|---|---|
| C1-H1 | **CLOSED** | `06.10-03-PLAN.md` "Certified availability (C1-H1)" + 03-02 `certified_parent_contract`; `06.10-04-PLAN.md` wave 4 `depends_on 03`, 04-01 identical-instance/single-check/both-override-style assertions; mechanism verified at `mixins.py:248-269`, `delete.py:356-369`, `base.py:850-851,877`. |
| C1-H2 | **CLOSED** | `06.10-01-PLAN.md` artifact inventory (isolated `NestedUrlRoot` family, no FK to existing models); 01-02 replays `test_delete_inspection.py`; `deletion.py:117-140` reverse-relation walk; no migrations dir under `tests/test1/app/`. |
| C1-H3 | **CLOSED** | `06.10-02-PLAN.md` "Scope roles"; `buttons.py:159-166,176-189,287-301,337`; 03-02 and 05-02 test/document the roles. |
| C1-H4 | **CLOSED** | 02-02 owns `create.py:36-70`; 03-02 explicitly modifies `views.py:344-387` and consolidates `mixins.py:146-197`; A/B create tests in context/table/card, both grant directions. |
| C1-H5 | **CLOSED** | 03-01 names the `has_permission` guard and GET/POST actor matrix; ordering supported by `mixins.py:307-322` before `base.py:1062-1070`. |
| C1-H6 | **CLOSED** | `06.10-06-PLAN.md` "Browser identity and fixture contract"; current divergence at `cjs:36-40` / `server.py:70-80`, equality at `cjs:133`. Residual LOW C2-N5. |
| C1-M01 | **CLOSED** | Plan 01 compatibility boundary; 01-03 and 02-01 strict-ValueError tests across locations. |
| C1-M02 | **CLOSED** | Public-only key translation; `base.py:555,674,748,754`, `columns.py:48` retained; falsey/0/None pinned in 01-03. |
| C1-M03 | **CLOSED** | Plan 01 M2M/self-FK/Resource fixtures; 03-02 three-level Guardian fixture; 04-01 `guardian_nested_protected_destination` + core; 06-01 server-local ViewSets. |
| C1-M04 | **CLOSED** | 01-02 `_meta.pk.value_from_object`, `NestedUrlInheritedChild` with distinct IDs, row and parent roles. |
| C1-M05 | **CLOSED** | 02-02 names `LinkDetailColumnMixin`/`LinkChildColumn` (`columns.py:38-50`), `RedirectChildView` (`child.py:21-28`), `FilterContextButton`; 03-02 tests the filter at `templatetags/crud_views.py:601-607` (naming imprecision noted). |
| C1-M06 | **CLOSED** | 02-02 replaces `create.py:45-48` catch with resolver provenance and tests `ObjectDoesNotExist` identity; 03-02 removes `views.py:292-296` duplicate. |
| C1-M07 | **CLOSED** | 02-01 guards `base.py:990` with `ParentViewSetError`. |
| C1-M08 | **CLOSED** | 02-02 matching-unpublished vs absent scope; DB-free thread/task tests. |
| C1-M09 | **CLOSED** | 03-02 three-level opposite grants, direct-parent-only gate (`mixins.py:357-368`). |
| C1-M10 | **CLOSED** | 03-01 sibling/no-object, Resource maps, cross-ViewSet retry (`viewset/__init__.py:452-470`), actor precedence. |
| C1-M11 | **CLOSED** | 05-01/05-02 content; `base.py:1087-1088`, `context_buttons.md:245-247`. |
| C1-M12 | **CLOSED** | 04-02 remeasures `test_delete_databases.py:222-269` at N=1/4/8 with negative control, records deltas. |
| C1-M13 | **CLOSED** | 05-03 scoped handoff subsection + summary table; existing Public API list (`stability.md`, Guardian section) untouched; classification left to Phase 7. |
| C1-M14 | **CLOSED** | 06-03 final `validateEvidence` after all gates, recapture on stale hashes. |
| C1-M15 | **CLOSED** | Plan 06 schema rules; `cjs:53` requires 200; 403 covered by plan 03 Python requests. |
| C1-M16 | **CLOSED** | `recipes(source, expected)` (`cjs:23`) and old screenshot rule (`cjs:74-78`) preserved; family-specific nested validation and corruption tests. Residual LOW C2-N4. |
| C1-M17 | **CLOSED** | 06-01 scopes `server.py:93-136` patches/headers per route/scenario with `finally` cleanup and isolation tests. |
| C1-M18 | **CLOSED** | 04-02 uses `database_routes` (`conftest.py:136-170`) for intermediate-ancestor alias mismatch with identity assertions. |
| C1-M19 | **CLOSED** | Plan 03 artifacts: private → public forwarding, internal callers enter private, public default never calls private; both override styles tested without recursion. |

**New tasks coverage.** All 16 tasks (01-01…06-03) have automated verify commands with observable `fails_when`, referenced test files exist, and the three cached interpreters plus npm scripts they invoke are present. The one gap I would ask the planner to close before execution is C2-N1 (pin the view-path/breadcrumb query bound in 01-02 and name the breadcrumb test in 02-02); C2-N2 is a measurement addition to 03-03. The remaining cycle-2 items are LOW and can be absorbed during execution.

**CYCLE_SUMMARY: current_high=0 current_actionable=2 (C2-N1, C2-N2 MEDIUM) plus 8 LOW advisories; all 25 cycle-1 findings CLOSED at plan level.**
