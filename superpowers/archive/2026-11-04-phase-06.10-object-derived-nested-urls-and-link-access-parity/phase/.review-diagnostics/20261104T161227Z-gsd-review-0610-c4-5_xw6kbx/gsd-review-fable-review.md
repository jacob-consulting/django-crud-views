Verification complete. I read the current plans at 7581bc0, diffed them against 808c396, and traced every seam the plans rely on in the live source. No product tests were run and no files were edited. Review follows.

# Cross-AI Plan Review — Phase 06.10, Cycle 4 (commit 7581bc0)

**Delta confirmed:** `git diff 808c396 7581bc0 --stat` shows exactly one file changed, `06.10-02-PLAN.md` (+15/−3): the 02-02 behavior bullet, action sentence, acceptance criterion and a new Round 3 ledger. Plans 01, 03, 04, 05 and 06 are byte-identical to cycle 3.

## C3-L01 verdict: FULLY RESOLVED

Source evidence for each required element:

- `src/crud_views/lib/table/columns.py:47-50` — `LinkDetailColumnMixin.get_url` is decorated `@ignore_exception(ViewSetKeyFoundError)` and calls `table.view.cv_get_url("detail", obj=record)`.
- `src/crud_views/lib/exceptions.py:39-61` — the decorator re-raises when `is_strict()` is true and returns `default_value=None` otherwise; `is_strict()` reads `CRUD_VIEWS_STRICT` falling back to `DEBUG` (lines 32-36).
- The raising path is real: `cv_get_url` → `cv_get_router_and_args` → `cv_get_cls_assert_object` → `cv_get_cls` → `ViewSet.get_view_class`, which raises `ViewSetKeyFoundError` via `cv_raise` at `src/crud_views/lib/viewset/__init__.py:342`.
- `tests/test1/test_strict_mode.py:18-25` uses `with override_settings(CRUD_VIEWS_STRICT=True), pytest.raises(...)` and `override_settings(CRUD_VIEWS_STRICT=False)` — exactly the pattern the plan now names. `tests/test1/conftest.py:49` sets `CRUD_VIEWS_STRICT=True` as the suite default, which the plan says to preserve.
- Plan 02 task 02-02 now states the two assertions in `<behavior>`, names the pattern and both settings values in `<action>`, repeats them in `<acceptance_criteria>`, and keeps them inside the `navigation_preservation` group that the unchanged `-k 'hook_contract or context_isolation or navigation_preservation'` selector collects.

One execution note, not a plan gap: Plan 01 rewrites `cv_get_router_and_args`, so the missing-key error must still surface from `cv_get_cls_assert_object` before any resolver work. Plan 01's "Compatibility boundary" paragraph already requires that ("existing view callers retain ViewSetKeyFoundError, including action skipping and LinkDetailColumnMixin's decorator"), and the action-skip seam it refers to is real at `base.py:746-755`.

---

## 06.10-01

**Summary.** The resolver/public-helper plan is unchanged since cycle 3 and its contracts match the source it replaces. The old page-only parent loop at `base.py:598-604` (`if not value: raise ValueError`, caller-dict mutation at line 586, extra-kwargs overwrite at 605) is exactly what the precedence matrix and copy/zero-value/hook-constraint rules target. `ParentViewSet.get_pk_name()`/`get_attribute()` (`parentviewset.py:56-66`) are the declared metadata the plan binds to, and `ViewSet.get_queryset()` (`viewset/__init__.py:281-316`) remains the request authority, untouched.

**Strengths.**
- Exception boundary verified: `cv_get_cls_assert_object` (`base.py:550-556`) uses the default `ViewSetError` through `cv_raise` (`exceptions.py:27-29`); `get_view_class` raises `ViewSetKeyFoundError`; the plan keeps both and localizes NoReverseMatch translation to the new public helper only.
- The list→card fallback the plan must preserve is a real branch at `viewset/__init__.py:340-341`.
- Isolated `NestedUrl*` fixture family avoids touching Publisher's reverse-deletion graph, which `tests/test1/test_delete_inspection.py` pins (replayed in 01-02).

**Concerns.** None new. Prior C1/C2 dispositions are intact in the ledger and still match source.

**Suggestions.** None required.

**Risk: LOW.**

## 06.10-02

**Summary.** The only plan that changed. The C3-L01 closure is complete (see verdict above). The rest of the plan's scope-role claims still match the call sites: `ParentContextButton` reverses raw URL kwargs itself (`buttons.py:159-169`) and gates on `cv_get_parent_object()` (177-189); `SiblingContextButton` reverses raw kwargs and checks `cv_has_access(user, None)` (287-301); `FilterContextButton` calls `cv_get_url(key=cv_key)` with no object (337); `ChildContextButton` goes through `cv_get_child_url` (229), whose `viewset.parent.name` at `base.py:990` is unguarded (C1-M07). The row/context action branch resolves the URL at `base.py:761` before the access check at 772, so "publish stock resolver outcomes before access" is the right ordering.

**Strengths.**
- Ordering of the C3-L01 fix is right: both strict/non-strict cases live in the already-selected group, so no new selector is needed.
- `CreateView._cv_action_enabled_for_context` (`create.py:45-48`) is the broad `ObjectDoesNotExist` catch C1-M06 removes; `_cv_action_enabled_for_rendering` (52-70) is the page-parent seam the carrier must replace. Both confirmed.
- The breadcrumb pin is correctly retained rather than predicted to fail.

**Concerns.**
- **LOW (wording, non-blocking):** The rendering-cost paragraph says `bc_chain` "caches note.book and book.publisher, so retain its 2-query first call". The 2 queries in `test_ancestor_query_count` (`test_breadcrumb.py:294-298`) actually come from the scoped ancestor fetches at `src/crud_views/lib/breadcrumb.py:244` (`parent.viewset.get_queryset(view=self).get(pk=...)`), one per level, and are independent of relation caches. The caching point matters only for the current object's own item, built via `cv_get_router_and_args(self.cv_key, obj=obj)` at `breadcrumb.py:168-180`, which after Plan 01 derives ancestry from `note.book`/`book.publisher`. The plan's conclusion (pin stays 2/0; add a cold fixture) is correct; the attribution could mislead an executor into "optimizing" the wrong path. Optional one-sentence clarification.

**Suggestions.**
- Optional: reword the rationale to "the existing 2 queries are the scoped ancestor fetches at breadcrumb.py:244; the self-item URL must add 0 because bc_chain's create() calls cache note.book and book.publisher".

**Risk: LOW.**

## 06.10-03

**Summary.** Unchanged since cycle 3; source still supports every ordering claim. The D-11 defects are concrete: core `cv_has_access` turns a missing permission into `user.has_perms(())` (`base.py:1086-1088`); Guardian object access reaches `perm.split(".")` with `None` (`mixins.py:88-97`); `get_queryset` would pass `None` to `get_objects_for_user` (199-212); `_guardian_user_has_parent_perm` splits a `None` parent permission (`mixins.py:360-368`). The top-level Guardian create currently falls through `GuardianParentPermissionMixin.has_permission` (307-311) to the core assertion, which is why the explicit guard in 03-01 is needed.

**Strengths.**
- `GuardianParentPermissionMixin` currently defines no `cv_has_access`, so the cooperative composition slots cleanly ahead of `GuardianObjectPermissionMixin`/`GuardianQuerysetMixin` in every shipped MRO (`views.py:32-40, 230-257`).
- The certified-adapter ownership is anchored to a real seam: `_cv_cancel_target_available` (`mixins.py:248-269`) runs its explicit parent gate at 258 and then calls `cls.cv_has_access(user, obj)` at 261; without the frame, the new cooperative gate would re-resolve and re-check the parent. The plan binds the frame inside that method, so both the ordinary cancel path (`base.py:864-884`) and the protected path (`delete.py:357-369`) are covered.
- `cv_context_has_permission` (`templatetags/crud_views.py:602-607`) wraps only `get_view_class` in `except Exception`; `cv_has_access` runs outside the try, so the plan's "exception identity preserved" assertion is achievable without product change.

**Concerns.** None new.

**Suggestions.** None required.

**Risk: MEDIUM** (inherent to authorization composition, not to plan quality; mitigations are explicit and testable).

## 06.10-04

**Summary.** Unchanged. The stock hook it replaces is one-level (`delete.py:192-210`): it reads `getattr(obj, parent_attr, None)`, uses a truthiness test, and swallows `NoReverseMatch`. The certification path it must leave intact (`_cv_get_protected_object_url`, 212-372) is independent of the candidate string and already reuses the certified parent through `destination._cv_cancel_parent_object = lambda: parent` (368), which is the exact instance Plan 03's certified-adapter frame must receive.

**Strengths.**
- Ownership ordering is right: Plan 04 depends on 03, and a seam failure reopens 03-02 rather than being deferred.
- Query budget replacement targets a real test with real counters (`test_delete_databases.py:222-271`, `_assert_protected_query_budget`).

**Concerns.**
- **LOW (optional):** Cascade-tree candidates go through the same hook once per tree node (`delete.py:451-456`). Today each uncached node costs one FK load; with multilevel ancestry it costs up to h−1. Growth stays linear, so no contract is broken, but `test_protected_adapter_query_budget` measures only the protected adapter. 04-02's sentence "separate resolver candidate cost from certification and preserve linear growth" covers this implicitly; an explicit cascade-tree N-node measurement would make the published numbers complete. May be deferred with the rationale that it is a constant-factor consequence of D-01.
- **LOW (incidental, informational):** The current hook on an M2M child returns a related manager from `getattr`, which is truthy, and then raises `AttributeError` on `.pk` (`delete.py:203-205`). After 04-01 that case becomes recognized-unavailable text. This is an improvement; Plan 05 might mention it under Fixed. No PLAN change required.

**Suggestions.**
- Optional: add "cascade tree, N nodes, 3-level fixture" as a named measurement row in 04-02.

**Risk: LOW–MEDIUM** (protected certification is security-relevant; the plan preserves it unchanged and tests it).

## 06.10-05

**Summary.** Unchanged. Documentation/migration plan with executable snippets; its dependencies (summaries 01–04) and the recipe-marker pattern (`docs/migrating-1.0.md:977/1005/1037`, `tests/test1/test_delete_migration_docs.py`) exist. The exception-name handoff (ViewSetError vs ViewSetKeyFoundError vs new ValueError/NoReverseMatch) matches `exceptions.py:11-24` and `base.py:555`.

**Strengths.**
- D-16 pairing (Breaking + migrating-1.0.md) matches `CLAUDE.md:107`.
- Stability handoff places names in `docs/development/stability.md` without pre-empting Phase 7 classification.

**Concerns.**
- **LOW (cosmetic):** 05-03 and 06-03 build strict docs into `/tmp/cv-069-docs`, the 06.9 directory name. Harmless; `/tmp/cv-0610-docs` would avoid confusion in gate records.

**Suggestions.** None required.

**Risk: LOW.**

## 06.10-06

**Summary.** Unchanged. The runner it extends currently accepts only `smoke|all` (`tests/browser/protected-delete.cjs:20`), hashes tracked files only (`sourceHashes()`, 36-40, `git ls-files src tests/test1 docs/migrating-1.0.md`), and the server mirrors that list (`protected_delete_server.py:70-80`). The C1-H6 fix (tracked-plus-untracked via `--cached --others --exclude-standard`, add `docs/reference/buttons.md`) is the right remedy, since `resolution.py`/`link_context.py` will be untracked until committed. `FixtureMiddleware` (server 89-120) patches by cookie inside an `ExitStack` with a ContextVar, so scoping patches per scenario/route (C1-M17) is a local extension.

**Strengths.**
- `validateEvidence` already compares source and recipe hashes (`protected-delete.cjs:69-70`); the final post-gate validation in 06-03 reuses that export.
- `CV_CANCEL_ASSETS_DIR` is a real requirement of the shared runtime (`cancel-navigation.cjs:57, 378-384`).
- 403 for D-09 is explicitly kept out of browser "passed navigation" and left to Plan 03 client tests.

**Concerns.**
- **LOW (informational):** Including `--others` makes any stray untracked file under `src/` or `tests/test1/` (editor backups, `.orig`) invalidate hashes. That is intended strictness; the executor should expect it and the gate record should name the offending path when it happens. No plan change needed.

**Suggestions.** None required.

**Risk: LOW** for plan quality; runtime availability (Chromium/assets) remains an execution-time preflight, which the plan treats as missing evidence rather than a pass.

---

## Overall assessment

- **C3-L01: FULLY RESOLVED** with source-verified mechanism and test pattern.
- **Regression of prior fixes:** none. All C1-H1–H6, C1-M01–M19, C2-M01/M02, C2-L01/L02 dispositions remain in the ledgers and their source anchors still hold (sampled above: `base.py:550-617, 735-780, 985-1005, 1085-1089`; `buttons.py:95-344`; `create.py:35-70`; `mixins.py:85-98, 146-197, 248-269, 347-382`; `views.py:274-387`; `delete.py:192-372, 451-456`; `columns.py:47-50`; `breadcrumb.py:168-193, 232-262`; browser runner/server identity functions).
- **New actionable findings:** 0 HIGH, 0 MEDIUM. Three LOW optional items (Plan 02 breadcrumb-cost wording, Plan 04 cascade-tree measurement row, Plan 05/06 temp dir name), each of which may be deferred with a one-line rationale.
- **Dependency ordering:** waves 1→6 are strictly serialized; Plan 04's blocking dependency on Plan 03's certified-adapter seam and Plan 06's post-gate re-validation are the two ordering constraints that matter, and both are explicit.
- **Scope:** no scope creep observed; exclusions (DataView, core parent permissions, cross-request permission cache, issue #286) remain stated in every plan.
- **Goal achievement:** the six plans, as written, cover NURL-01–04 and AUTH-08/09 with executable tasks and real fixture anchors.

**Cycle 4 recommendation:** converged. No further plan revision is required before execution.
