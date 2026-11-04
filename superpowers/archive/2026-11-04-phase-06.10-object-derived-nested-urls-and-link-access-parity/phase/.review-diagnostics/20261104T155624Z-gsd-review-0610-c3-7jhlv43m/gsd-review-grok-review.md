I'll verify the six plans against the current source, starting with the exception, query, and import seams the cycle-3 items depend on.
## 06.10-01

The resolver plan matches the live URL and exception seams. `cv_get_router_and_args` still copies page parent kwargs and treats a missing value as `not value` (`src/crud_views/lib/view/base.py:598-603`), and `cv_get_cls_assert_object` raises through `cv_raise`'s default (`src/crud_views/lib/view/base.py:555`, `src/crud_views/lib/exceptions.py:27`).

**Strengths**
- Object-over-page precedence is applied inside the existing `cv_get_url` → `cv_get_router_and_args` seam (`base.py:611-616`), so view overrides that call `self.cv_get_router_and_args` keep working.
- Unknown view keys stay `ViewSetKeyFoundError` at `ViewSet.get_view_class` (`src/crud_views/lib/viewset/__init__.py:339-342`); only the new public helper translates them.
- PK `0` is called out against the current truthiness check, and M2M/Resource paths are forbidden from guessing relationships. `ParentViewSet.get_attribute` / `get_pk_name` are the right metadata (`src/crud_views/lib/viewset/parentviewset.py:56-66`).
- The isolated `NestedUrl*` family avoids Publisher's deletion graph. A multi-table child can have its own PK distinct from `parent_ptr` (Django 5.2 promotes the parent link only when the child has no PK).

**Concerns**
- None at plan level. The strict column/action `ValueError` for a null parent is a chosen D-06 break, not a hole: `LinkDetailColumnMixin` only swallows `ViewSetKeyFoundError` (`src/crud_views/lib/table/columns.py:47-50`).

**Suggestions**
- In 01-01, record breadcrumb SQL from `cv_breadcrumb()` itself. The existing 2-query pin is ancestor `get()` calls (`src/crud_views/lib/breadcrumb.py:243-244`), not `note.book` cache hits.

**Risk Assessment:** LOW. The matrix, exception split, and query bounds are executable against current call sites.

## 06.10-02

View integration is aimed at the real builders: ordinary actions (`base.py:735-772`), context/parent/child/sibling buttons (`src/crud_views/lib/view/buttons.py:95-302`), and both card branches (`src/crud_views/lib/views/card.py:57-87`).

**Strengths**
- Sibling links already pass `obj=None` (`buttons.py:297-301`). Keeping that path out of the destination-parent frame preserves D-10.
- `ParentContextButton` already builds remaining kwargs from the page URL (`buttons.py:159-165`), which is the right input for the three-level A-versus-B case.
- `cv_get_child_url` currently dereferences `viewset.parent.name` (`base.py:990`). Guarding `parent is None` before that is required.
- Create state already has a second resolver (`src/crud_views/lib/views/create.py:35-70`). Naming `CreateView._cv_action_enabled_for_rendering` as the consumer of the selected parent is the correct seam.
- Carrier tests are database-free, which matches Django's connection constraints.

**Concerns**
- None new. A custom `cv_get_url` that does not call `super()` still will not publish coordinates; the plan assigns that override routing responsibility and does not pretend the carrier can parse its URL.

**Suggestions**
- Open the scope before `cv_get_link_url` / `cv_get_child_url`, not only around `cv_has_access`. Those helpers run first (`base.py:761`, `buttons.py:103`, `card.py:77`).

**Risk Assessment:** LOW. Hook signatures and the ContextVar ownership checks are specified tightly enough to implement.

## 06.10-03

Access parity is grounded in the actual gaps: core `cv_has_access` turns a missing perm into `has_perms(())` (`base.py:1085-1088`), Guardian object checks call `perm.split` (`src/crud_views_guardian/lib/mixins.py:88-97`), and create bypasses the parent mixin (`src/crud_views_guardian/lib/views.py:344-387`).

**Strengths**
- Shipped detail MRO is parent-then-object (`views.py:32-34`), so a new `GuardianParentPermissionMixin.cv_has_access` will run for object links. Create's own override will not, and the plan edits that class explicitly (`views.py:257`).
- Dispatch still resolves the URL parent once (`mixins.py:370-372`) and does not store it. Reusing that instance only after model, normalized PK, and database agree does not create a permission cache. Checkers stay per call (`mixins.py:366-368`).
- `_cv_cancel_target_available` already checks the parent, then calls `cv_has_access` (`mixins.py:257-261`). The certified-adapter flag is necessary to keep that to one policy evaluation.
- The URL-free regression names the real filter, `cv_context_has_permission` (`src/crud_views/templatetags/crud_views.py:601-607`), which passes `view.object` and does not build a URL.
- D-09/D-10 stay fallbacks. A displayed unresolved link can still 403 on the request.

**Concerns**
- LOW: 03-02's pytest `-k` omits `queries_same_parent_list`. The pre-gate baseline is only an action instruction, not a failing gate of that task. 03-03 cannot reconstruct a skipped baseline.

**Suggestions**
- Run the baseline capture as its own command before the mixin edit, and store the counts in the summary the acceptance criteria already require.

**Risk Assessment:** LOW. Opposite-parent, create MRO, and missing-declaration orders match the live methods.

## 06.10-04

Delete reuse is correctly limited to candidate generation. Stock `cv_get_related_object_url` still adds only one parent and skips a falsy parent (`src/crud_views/lib/views/delete.py:192-210`). Certification stays in `_cv_get_protected_object_url` (`delete.py:212-372`).

**Strengths**
- Visibility-before-URL and the public hook remain. `strict=False` is confined to this optional path, matching plan 01.
- The certified-parent lambda is a real seam (`delete.py:356-368`). Depending on plan 03, then asserting one policy call for both delegating and non-delegating hooks, is the right gate.
- Cross-alias work cannot stop at `cv_get_parent_object`, which loads only the immediate parent (`base.py:1023-1035`) via `get_object_or_404` without `using`. The plan requires every ancestor alias.
- No new Publisher FK. Existing inspection tests stay a replay.

**Concerns**
- None new. Cascade rows stay on the shared hook and are not pulled into protected-only checks.

**Suggestions**
- Walk intermediate ancestors from the candidate instance's `_state.db` inside `_cv_get_protected_object_url`. Do not assume `_cv_cancel_parent_object` already did that.

**Risk Assessment:** LOW. The optional resolver does not replace certification.

## 06.10-05

Documentation is tied to executed fences and to measured summaries, not to predicted query counts.

**Strengths**
- Breaking-plus-migration matches D-16, including the implicit page-A collection plus obj-B case versus an explicit conflicting parent.
- Exception docs name `ViewSetError` for the object assertion, `ViewSetKeyFoundError` for missing keys, and `ValueError` / `NoReverseMatch` only for the new helper. That matches `cv_raise` and `get_view_class`.
- Sibling `obj=None`, middle-tier parent URL scope, and the possible displayed-link 403 are written as limits, not as parity claims.
- The stability handoff is a subsection, not a Phase 7 classification. Private carrier names stay internal.

**Concerns**
- None. Numeric rows are required to match plan 01/02/03 assertions, so this plan cannot invent the budgets.

**Suggestions**
- State that the breadcrumb 2/0 pin is ancestor label queries plus the view cache (`breadcrumb.py:151-155` and `:243-244`), and that cold URL assembly is a separate number.

**Risk Assessment:** LOW. The recipe extractor and signature checks are concrete.

## 06.10-06

The browser plan extends a validator that currently treats every case as a protected-delete case (`tests/browser/protected-delete.cjs:41-67`) and hashes only tracked `git ls-files` output (`protected-delete.cjs:36-39`).

**Strengths**
- Family split is explicit: old `smoke`/`all` keep delete DOM keys; nested cases validate navigation and same-row hrefs. A 403 is not a browser pass.
- Untracked `resolution.py` / `link_context.py` are required in both runner and server manifests. Current `sourceHashes()` would miss them until that change lands.
- Final `validateEvidence` after gates, with recapture if hashes move, closes the stale-evidence hole.
- The Django 6.0 deselection matches the existing golden `test_filter_form_baseline` (`tests/test1/test_form_buttons_golden.py:278`). Supported-series commands are source-bound.

**Concerns**
- LOW: `validateEvidence` currently requires `wholeFormAbsent`, `sharedAlert`, and `href is None` unless the id ends in `-click`/`-enter` (`protected-delete.cjs:48-65`). Nested action cases will fail that loop unless the family branch lands before smoke. The plan says to do that; it is still the easiest way to burn a browser run.

**Suggestions**
- Add the family branch and the untracked-file hash test before the first Chromium invocation, as 06-01 already orders.

**Risk Assessment:** LOW. Evidence rules are strict; runtime launch is correctly an execution preflight, not a claimed pass.

## Cycle 3 closure

| ID | Disposition | Evidence |
|---|---|---|
| C1-M02 | FULLY RESOLVED | Plans 01, 02, and 05 pin `ViewSetError` at `cv_get_cls_assert_object`. That is `cv_raise`'s default (`exceptions.py:27`, `base.py:555`). `ViewSetKeyFoundError` stays on `get_view_class` (`viewset/__init__.py:342`). No remaining `CrudViewError` pin for this assertion. |
| C2-M01 | FULLY RESOLVED | Plans 01 and 02 record a pre-change baseline and pin fresh, creation-cached, and `select_related` costs for single views and N=1/4 lists, plus cold versus cached breadcrumb URL and total SQL. The existing `test_ancestor_query_count` 2-then-0 pin is retained (`tests/test1/test_breadcrumb.py:297-303`). The immediate-FK page shortcut stays rejected. Plan 05 publishes measured deltas only. |
| C2-M02 | FULLY RESOLVED | Plan 03 measures same-parent lists separately from distinct-parent cards at N=1/4, splits relation SQL from parent and child permission SQL, and reuses a request parent only when model, normalized identity, and database agree (`mixins.py:370-372`). No permission-result cache. Plan 05 documents that split. |
| C2-L01 | FULLY RESOLVED | Plans 02 and 03 name and render `cv_context_has_permission` (`templatetags/crud_views.py:601-607`), not a `cv_has_access` tag. |
| C2-L02 | FULLY RESOLVED | Resolver and carrier stay off the package init cycle. `viewset/__init__.py:23` imports views while initializing; `resource.py:9-16` and `views/child.py:6-8` already document that trap. Fresh-process import-order smokes are required. |

No regression of the six previously closed HIGH findings. Create still bypasses the parent mixin (`views.py:344`). Sibling access is still `obj=None` (`buttons.py:301`). The certified-parent lambda still exists (`delete.py:366-368`). Plan 04 still waits on plan 03. Fixture roots are still independent of Publisher.

## Overall

**Risk: LOW.** All six plans have their own executable tasks, the wave order matches the shared resolver → rendering carrier → Guardian gate → delete certification → docs → browser sequence, and the five cycle-3 items are closed against current source. Remaining notes are implementation cautions, not missing requirements.
