## 06.10-01

### 1. Summary
Plan `06.10-01` defines the shared parent-chain resolver (`src/crud_views/lib/viewset/resolution.py`), public `ViewSet.get_parent_pks()` and `ViewSet.get_url()` helpers (`src/crud_views/lib/viewset/__init__.py`), and `CrudView.cv_get_router_and_args()` integration (`src/crud_views/lib/view/base.py:576-610`). All prior Cycle 1–2 findings assigned to this plan (`C1-H2`, `C1-M01`–`C1-M05`, `C2-M01`, `C2-L02`) remain intact with no regressions.

### 2. Strengths
- **Coherent parent-chain precedence and metadata-aware PK extraction:** Uses `ParentViewSet.get_attribute()` and `ParentViewSet.get_pk_name()` (`src/crud_views/lib/viewset/parentviewset.py:56-66`) and extracts registered model PKs via `_meta.pk.value_from_object` (`06.10-01-PLAN.md:140`) instead of `obj.pk` (`src/crud_views/lib/view/base.py:591`), preventing multi-table inheritance and non-PK `ForeignKey(to_field=...)` mismatches.
- **Preserved exception and import contracts:** Localizes unknown-key `NoReverseMatch`/`None` translation to `ViewSet.get_url()` (`06.10-01-PLAN.md:104,156`), preserving `ViewSetKeyFoundError` in `ViewSet.get_view_class()` (`src/crud_views/lib/viewset/__init__.py:339-343`) and `ViewSetError` in `CrudView.cv_get_cls_assert_object()` (`src/crud_views/lib/view/base.py:550-556`). Enforces the leaf-import boundary required by `src/crud_views/lib/resource.py:9-16` (`06.10-01-PLAN.md:79,121`).
- **Isolated test models and pre-change query baseline:** Roots test models at `NestedUrlRoot` (`06.10-01-PLAN.md:75,140`) without touching `Publisher`'s reverse deletion graph, and captures pre-edit `BookNote` query baselines in Task `01-01` before pinning `N=1/4` bounds in Task `01-02` (`06.10-01-PLAN.md:108,121,138-140`).

### 3. Concerns
- None actionable. All Cycle 1–3 findings for `06.10-01` remain resolved in `06.10-01-PLAN.md:172-204`.

### 4. Suggestions
- None; the specification is ready for execution.

### 5. Risk Assessment
- **LOW** — The resolver contract, exception taxonomy, import boundaries, and query-count preconditions are fully specified against current source.

---

## 06.10-02

### 1. Summary
Plan `06.10-02` wires view-based URL builders (`cv_get_router_and_args`, `cv_get_child_url`) and action rendering locations (`src/crud_views/lib/view/base.py:735-780`, `src/crud_views/lib/view/buttons.py:95-311`, `src/crud_views/lib/views/card.py:46-91`, `src/crud_views/lib/views/create.py:35-70`) into a call-scoped `_LinkDestinationContext` carrier (`src/crud_views/lib/view/link_context.py`). The commit `7581bc0` update to Task `02-02` and its Round 3 ledger (`06.10-02-PLAN.md:116,121,123,128,169-179`) cleanly closes `C3-L01` without disturbing any prior Cycle 1–2 fixes.

### 2. Strengths
- **`C3-L01` (FULLY RESOLVED):** `LinkDetailColumnMixin.get_url` (`src/crud_views/lib/table/columns.py:47-50`) is decorated with `@ignore_exception(ViewSetKeyFoundError)`. Because `tests/test1/conftest.py:49` sets `CRUD_VIEWS_STRICT=True` globally (verified by `tests/test1/test_strict_mode.py:49-53`), `ignore_exception` re-raises `ViewSetKeyFoundError` by default and only returns `None` when `CRUD_VIEWS_STRICT=False` (`tests/test1/test_strict_mode.py:18-26`). Task `02-02` now explicitly requires testing both `override_settings(CRUD_VIEWS_STRICT=True)` with `pytest.raises(ViewSetKeyFoundError)` and `override_settings(CRUD_VIEWS_STRICT=False)` with `is None` on `LinkDetailColumnMixin.get_url`, while preserving the existing `@ignore_exception(ViewSetKeyFoundError)` decorator and keeping the tests under `navigation_preservation` in `-k 'hook_contract or context_isolation or navigation_preservation'` (`06.10-02-PLAN.md:116,121,123,128,174`).
- **Action-location and button-scope precision:** Properly separates `ContextButton` (`src/crud_views/lib/view/buttons.py:95-129`), `ParentContextButton` (`buttons.py:145-200`), `ChildContextButton` (`buttons.py:222-252`), `SiblingContextButton` (`buttons.py:277-311`), and `FilterContextButton` (`buttons.py:324-361`) so `SiblingContextButton` retains `obj=None` D-10 behavior and middle-tier `ParentContextButton` collections bind remaining page ancestor kwargs (`06.10-02-PLAN.md:82,99`).
- **Breadcrumb and list query preservation:** Preserves `tests/test1/test_breadcrumb.py:297-304` (`TestBreadcrumbAncestors::test_ancestor_query_count` at 2 queries then 0 memoized) while adding independent cold vs. cached measurements for `src/crud_views/lib/breadcrumb.py:157-276` (`06.10-02-PLAN.md:86,119,128`).

### 3. Concerns
- None actionable. `C3-L01` is fully resolved and all prior Cycle 1–2 dispositions (`06.10-02-PLAN.md:134-168`) remain intact.

### 4. Suggestions
- None; Task `02-01` and Task `02-02` are ready for execution.

### 5. Risk Assessment
- **LOW** — The `ContextVar` frame immutability, owner thread/task checks, `finally` token reset, and strict-mode column preservation are tightly constrained and directly tested.

---

## 06.10-03

### 1. Summary
Plan `06.10-03` closes the undeclared-permission and Guardian parent-gate link visibility gaps across `src/crud_views/lib/view/base.py:1061-1089`, `src/crud_views_guardian/lib/mixins.py:45-382`, and `src/crud_views_guardian/lib/views.py:257-388`, introducing public `GuardianParentPermissionMixin.cv_guardian_has_parent_access()` and mandatory certified-parent evaluation. All Cycle 1–2 findings (`C1-H1`, `C1-H3`–`C1-H5`, `C1-M03`, `C1-M05`, `C1-M06`, `C1-M09`, `C1-M10`, `C1-M19`, `C2-M02`, `C2-L01`) remain intact.

### 2. Strengths
- **Undeclared-permission gating and request ordering:** Fixes `CrudViewPermissionRequiredMixin.cv_has_access` (`src/crud_views/lib/view/base.py:1085-1089`) so missing permissions return `False` before `user.has_perms(())` grants access to every user/superuser, and guards `GuardianObjectPermissionMixin` (`src/crud_views_guardian/lib/mixins.py:76,88`), `GuardianQuerysetMixin` (`mixins.py:205`), `GuardianParentPermissionMixin` (`mixins.py:307-311,360`), and top-level `GuardianCreateViewPermissionRequired` (`views.py:257-260`) after anonymous/inactive actor checks (`06.10-03-PLAN.md:76-78,101-103`).
- **Cooperative and non-cooperative MRO coverage:** Explicitly updates `GuardianCreateViewPermissionRequired.cv_has_access` (`src/crud_views_guardian/lib/views.py:344-388`) and consolidates `GuardianQuerysetMixin.cv_get_context` (`src/crud_views_guardian/lib/mixins.py:146-197`) into `_cv_has_access_for_rendering`, while forwarding `_guardian_user_has_parent_perm` (`mixins.py:348-368`) to `cls.cv_guardian_has_parent_access(user, parent_obj)` (`06.10-03-PLAN.md:68,71,86,127`).
- **Single mandatory certified-parent check and safe request-parent reuse:** Prevents double evaluation or custom non-delegating `cv_has_access` bypass in `_cv_cancel_target_available` (`src/crud_views_guardian/lib/mixins.py:248-269`), exercises the real `cv_context_has_permission` filter (`src/crud_views/templatetags/crud_views.py:601-608`), and reuses request-resolved parent model evidence (`mixins.py:370-374`) only when model, normalized PK, and DB alias match (`06.10-03-PLAN.md:84,88,123-125`).

### 3. Concerns
- None actionable. All Cycle 1–2 dispositions (`06.10-03-PLAN.md:158-192`) remain complete.

### 4. Suggestions
- None; ready for execution.

### 5. Risk Assessment
- **LOW** — Every permission lookup, actor prelude, create MRO branch, and query-cost boundary is grounded in `src/crud_views_guardian/lib/mixins.py` and `views.py`.

---

## 06.10-04

### 1. Summary
Plan `06.10-04` updates `DeleteView.cv_get_related_object_url()` (`src/crud_views/lib/views/delete.py:192-210`) to delegate stock candidate URL construction to `viewset.get_url("detail", obj, strict=False)` while preserving Phase 06.9's visibility-first filtering (`delete.py:442-458`) and independent exact-candidate certification in `DeleteView._cv_get_protected_object_url()` (`delete.py:212-372`). All Cycle 1 findings (`C1-H1`, `C1-H2`, `C1-M03`, `C1-M12`, `C1-M18`) remain resolved.

### 2. Strengths
- **Strict separation of candidate generation and certification:** Replaces only the single-parent construction in `cv_get_related_object_url()` (`src/crud_views/lib/views/delete.py:198-206`) with `viewset.get_url("detail", obj, strict=False)` (`06.10-04-PLAN.md:83`), keeping local-path validation, route resolution, `SingleObjectMixin.get_object` verification, concrete model/PK/DB alias matching, and `_PermittedPks` projection checks in `_cv_get_protected_object_url()` (`delete.py:224-372`).
- **Serialized verification of the certified-parent seam:** Depends on `06.10-03` (`06.10-04-PLAN.md:5-6,69`) and verifies that `destination._cv_cancel_parent_object = lambda: parent` (`src/crud_views/lib/views/delete.py:357-369`) passes the exact certified parent instance and DB alias once to the mandatory parent gate (`06.10-04-PLAN.md:81,83`).
- **Cross-database intermediate ancestry and exact query budgets:** Uses `database_routes` (`tests/test1/conftest.py:137-150`) to test intermediate ancestor alias mismatches and re-pins `test_protected_adapter_query_budget` at `N=1/4/8` (`06.10-04-PLAN.md:100,104`).

### 3. Concerns
- None actionable. All Cycle 1 dispositions (`06.10-04-PLAN.md:115-132`) remain intact.

### 4. Suggestions
- None; ready for execution.

### 5. Risk Assessment
- **LOW** — The change to `src/crud_views/lib/views/delete.py` is minimal and protected by existing and multilevel certification tests.

---

## 06.10-05

### 1. Summary
Plan `06.10-05` delivers the `### Breaking` and `### Fixed` entries in `CHANGELOG.md`, executable caller migration snippets in `docs/migrating-1.0.md`, reference documentation updates (`docs/reference/nested.md`, `docs/reference/guardian.md`, `docs/reference/context_buttons.md`, `docs/reference/delete_view.md`), the Phase 06.10 handoff inventory in `docs/development/stability.md`, and `tests/test1/test_nested_url_docs.py`. All Cycle 1–2 findings (`C1-H3`, `C1-M02`, `C1-M11`, `C1-M13`, `C2-M01`, `C2-M02`) remain addressed.

### 2. Strengths
- **Executable documentation fences and signature checks:** Extracts marked Python snippets (`nested-url-recipe: object`, `collection`, `optional`, `explicit-context`) from `docs/migrating-1.0.md` and executes them against real ViewSets and routes (`06.10-05-PLAN.md:70,82-87`), while preserving existing `protected-delete-recipe` markers (`tests/browser/protected_delete_server.py:57-62`).
- **Exact exception and query-cost reporting:** Documents and tests `ViewSetError` (`src/crud_views/lib/view/base.py:555`), `ViewSetKeyFoundError` (`src/crud_views/lib/viewset/__init__.py:342`), `ValueError`, and `NoReverseMatch` distinctions, and publishes only measured query counts and deltas from Plans 01–03 (`06.10-05-PLAN.md:74,95,100`).
- **Scoped Phase 7 stability handoff:** Adds a dedicated Phase 06.10 handoff subsection to `docs/development/stability.md` (`docs/development/stability.md:19-86`) listing `ViewSet.get_parent_pks`, `ViewSet.get_url`, and `GuardianParentPermissionMixin.cv_guardian_has_parent_access` while marking `_ParentResolution`, `link_context`, and private rendering/forwarding seams internal (`06.10-05-PLAN.md:71,108`).

### 3. Concerns
- None actionable. All Cycle 1–2 dispositions (`06.10-05-PLAN.md:123-152`) remain complete.

### 4. Suggestions
- None; ready for execution.

### 5. Risk Assessment
- **LOW** — Documentation claims and code snippets are verified by pytest and `mkdocs build --strict`.

---

## 06.10-06

### 1. Summary
Plan `06.10-06` extends the Playwright browser harness (`tests/browser/protected-delete.cjs`, `tests/browser/protected-delete.test.cjs`, `tests/browser/protected_delete_server.py`) with `--case nested-smoke` and `--case nested-all`, executes the full Python/Django 4.2/5.2/6.0, example, Vitest, fragment integration, MkDocs, and Ruff gates, and validates persisted browser evidence after all gate-driven edits settle. All Cycle 1 findings (`C1-H1`, `C1-H6`, `C1-M03`, `C1-M14`–`C1-M17`) remain intact.

### 2. Strengths
- **Synchronized tracked + untracked source and recipe hashing:** Updates `sourceHashes()` (`tests/browser/protected-delete.cjs:36-40`) and `source_hashes()` (`tests/browser/protected_delete_server.py:70-81`) to use `git ls-files --cached --others --exclude-standard` over `src`, `tests/test1`, `docs/migrating-1.0.md`, and `docs/reference/buttons.md`, ensuring untracked `resolution.py` and `link_context.py` are hashed and verified inside `ROOT / "src"` (`tests/browser/protected_delete_server.py:47`, `06.10-06-PLAN.md:81`).
- **Scenario-isolated middleware and preserved recipe interface:** Preserves `recipes(source, expected)` (`tests/browser/protected-delete.cjs:23-35`) and restricts `FixtureMiddleware` patches (`tests/browser/protected_delete_server.py:89-137`) to their owning routes and scenarios (`06.10-06-PLAN.md:83-85`).
- **Post-gate evidence freshness check:** Runs `runner.validateEvidence(..., "nested-all", output)` as the final step of Task `06-03` (`06.10-06-PLAN.md:135,155-156`) so any formatting or doc fix that mutates hashed files forces re-validation/recapture before completion.

### 3. Concerns
- None actionable. All Cycle 1 dispositions (`06.10-06-PLAN.md:164-183`) remain intact.

### 4. Suggestions
- None; ready for execution.

### 5. Risk Assessment
- **LOW** — Browser fixture isolation, hash manifests, and full repository gate sequencing are thoroughly specified and verified.

---

## Cycle 4 Closure & Overall Assessment

- **`C3-L01` Status:** **FULLY RESOLVED**. In `06.10-02-PLAN.md:116,121,123,128,174`, Task `02-02` explicitly specifies using `django.test.override_settings(CRUD_VIEWS_STRICT=True)` with `pytest.raises(ViewSetKeyFoundError)` and `override_settings(CRUD_VIEWS_STRICT=False)` with `is None` on `LinkDetailColumnMixin.get_url` (`src/crud_views/lib/table/columns.py:47-50`), matching the pattern in `tests/test1/test_strict_mode.py:18-26` and the default `CRUD_VIEWS_STRICT=True` in `tests/test1/conftest.py:49`, while retaining `@ignore_exception(ViewSetKeyFoundError)` and the `-k 'hook_contract or context_isolation or navigation_preservation'` selector.
- **Prior Cycle 1–3 Findings (`C1-H1`–`C1-H6`, `C1-M01`–`C1-M19`, `C2-M01`, `C2-M02`, `C2-L01`, `C2-L02`):** Confirmed intact with **0 regressions**.
- **New Actionable Concerns:** **0** (0 HIGH, 0 MEDIUM, 0 LOW). All six plans (`06.10-01` through `06.10-06`) have converged and are ready for execution.
