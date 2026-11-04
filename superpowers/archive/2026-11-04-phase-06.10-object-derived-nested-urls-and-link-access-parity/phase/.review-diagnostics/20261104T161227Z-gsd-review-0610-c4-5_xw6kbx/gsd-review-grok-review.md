I'll verify the six plans against the current source, starting with the C3-L01 strict-mode column contract and the URL/access seams they depend on.
C3-L01 depends on the column decorator and strict helper. I'll trace those callers and the parent/access seams the plans say they reuse.
## 06.10-01

The resolver plan matches the live URL seam. `cv_get_router_and_args` still copies page kwargs and treats a falsey parent id as missing (`src/crud_views/lib/view/base.py:599-603`), while parent names come only from `ParentViewSet.get_pk_name` / `get_attribute` (`src/crud_views/lib/viewset/parentviewset.py:56-66`). The plan’s typed unavailable result, public `strict` flag, and view-vs-helper exception split are the right way to change that without turning `ViewSetKeyFoundError` (`src/crud_views/lib/viewset/__init__.py:339-343`) into `NoReverseMatch`.

**Strengths**
- Object/collection precedence is a chain rule, not a per-key merge, and it keeps page scope for collections when kwargs exist.
- Query bounds distinguish raw PK attname, `to_field`, preloaded relations, and explicit coordinates. The Publisher deletion graph stays untouched; `test_delete_inspection.py` is the regression gate.
- Optional mode is an internal result, not a broad `ValueError` catch, which matches D-12 and D-14.

**Concerns**
- None newly actionable. Prior C1/C2 dispositions are still present and match the source.

**Suggestions**
- None that require a plan edit.

**Risk Assessment:** MEDIUM. The contract is executable, but the first change to `cv_get_router_and_args` also feeds breadcrumbs and columns, so a wrong object/collection classification will show up outside the new module.

## 06.10-02

**C3-L01: FULLY RESOLVED.** `LinkDetailColumnMixin.get_url` is decorated with `@ignore_exception(ViewSetKeyFoundError)` and calls `cv_get_url("detail", obj=record)` (`src/crud_views/lib/table/columns.py:47-50`). The decorator re-raises when `is_strict()` is true and otherwise returns `None` (`src/crud_views/lib/exceptions.py:32-57`). A missing key becomes `ViewSetKeyFoundError` only after a truthy object passes `cv_get_cls_assert_object` (`src/crud_views/lib/view/base.py:550-555`, `src/crud_views/lib/viewset/__init__.py:339-343`). Task 02-02 now requires both `django.test.override_settings` cases, the same context-manager pattern as `tests/test1/test_strict_mode.py:8-19`, an unchanged decorator, the `tests/test1/conftest.py:49` strict default, and the existing `-k 'hook_contract or context_isolation or navigation_preservation'` selector.

The carrier plan also matches the real call sites: ordinary actions go through `_cv_get_action_context` (`src/crud_views/lib/view/base.py:735-772`), while parent/sibling/child/filter buttons build or skip URLs independently (`src/crud_views/lib/view/buttons.py:145-337`).

**Strengths**
- Page-A collection versus object-B is published before access, without changing `cv_has_access(user, obj)` signatures.
- Sibling `obj=None`, filter, and middle-tier parent URL ancestry are explicit exclusions, not implied by a global wrapper.
- Breadcrumb preservation is tied to the real pin: first call 2 queries, repeat 0 (`tests/test1/test_breadcrumb.py:297-303`), with a separate cold measurement.

**Concerns**
- None newly actionable.

**Suggestions**
- None.

**Risk Assessment:** MEDIUM. ContextVar ownership is specified, including thread and task identity, but it remains the easiest seam to implement as a mutable class attribute.

## 06.10-03

The access plan targets the actual gaps. Core `cv_has_access` turns a missing permission into `has_perms(())` (`src/crud_views/lib/view/base.py:1085-1088`). Guardian object checks call `perm.split` with no declaration guard (`src/crud_views_guardian/lib/mixins.py:85-97`), and create implements its own `cv_has_access` so a parent-mixin method would not reach it (`src/crud_views_guardian/lib/views.py:344-387`). Cancel certification already loads one parent and then calls child access (`src/crud_views_guardian/lib/mixins.py:248-269`).

**Strengths**
- Rendering denial and request `ImproperlyConfigured` are separate orders, with inactive/anonymous handling kept ahead of the new diagnostic.
- D-09/D-10 are tested as fallbacks, including `cv_context_has_permission` (`src/crud_views/templatetags/crud_views.py:601-607`), not described as full parity.
- Certified-parent ownership is control flow, not a permission cache, and plan 04 is the required delete integration gate.

**Concerns**
- None newly actionable.

**Suggestions**
- None.

**Risk Assessment:** MEDIUM. MRO and the no-object create correction are named, but a second parent check in `cv_has_access` would still pass a naive grant test unless the one-call spies are implemented as written.

## 06.10-04

Stock preview URLs stop at one parent and swallow only `NoReverseMatch` (`src/crud_views/lib/views/delete.py:192-210`). Certification is a later exact-candidate check, and the protected path already installs the fetched parent as `_cv_cancel_parent_object` (`src/crud_views/lib/views/delete.py:356-369`). Reusing `get_url(..., strict=False)` without replacing that validator matches the source boundary.

**Strengths**
- Visibility stays before URL work; cascade links stay on the public hook and are not newly certified.
- Cross-alias ancestry is an explicit `database_routes` case, not only a direct-parent PK compare.
- Query counters must be remeasured at N=1/4/8, including the existing excess-work control (`tests/test1/test_delete_databases.py:210-222`).

**Concerns**
- None newly actionable.

**Suggestions**
- None.

**Risk Assessment:** LOW. The change is narrow and blocked on the plan 03 certified-parent seam, with a hard reopen rule if identity or call counts fail.

## 06.10-05

The docs plan publishes the behavior the code will actually change, and it leaves the current Public API list intact (`docs/development/stability.md:19-27`) for Phase 7. Existing protected recipe markers remain the executable migration surface (`docs/migrating-1.0.md:977-1039`).

**Strengths**
- Breaking text is paired with extracted, executed fences, including the implicit page-A plus obj-B case versus an explicit conflicting parent.
- Exception names stay split: `ViewSetError` for a missing object, `ViewSetKeyFoundError` for a missing view key, and public-helper `ValueError` / `NoReverseMatch`.
- Query tables are required to copy measured plan 01–03 results, not predicted bounds.

**Concerns**
- None newly actionable.

**Suggestions**
- None.

**Risk Assessment:** LOW. The main failure mode is documenting a helper that execution did not actually ship; `inspect.signature` checks cover that.

## 06.10-06

The browser plan extends a validator that currently assumes every case is a protected-delete case (`tests/browser/protected-delete.cjs:41-67`) and hashes only tracked files (`tests/browser/protected-delete.cjs:36-39`, `tests/browser/protected_delete_server.py:70-80`). The new family schema, `--others` manifest, and final `validateEvidence` call are necessary and specified.

**Strengths**
- Stock/custom mixed-parent navigation is a real HTTP fixture, not a relabeled 06.9 report.
- A displayed unresolved-parent 403 stays in plan 03’s request tests; browser navigation still requires the expected 200.
- Gate commands are source-bound and cannot pass on stale screenshots after a later edit.

**Concerns**
- None newly actionable.

**Suggestions**
- None.

**Risk Assessment:** MEDIUM. Evidence identity is well specified, but the run still depends on a preflighted Chromium and the cached asset directory; a missing runtime is correctly treated as missing evidence.

## Closure

C3-L01 is fully resolved in plan 02. Prior C1-H1–C1-H6, C1-M01–C1-M19, and C2 findings remain incorporated; no regression and no new actionable plan omission. All six plans were reviewed. Overall delivery risk is MEDIUM because the resolver, rendering carrier, and Guardian MRO change one public URL rule, not because a required decision is still missing.
