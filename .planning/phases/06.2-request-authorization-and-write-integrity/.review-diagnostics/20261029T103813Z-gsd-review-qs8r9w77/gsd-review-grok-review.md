I'll verify A26 against the current plans and source, then review all six plans without editing.
A26 is named in plan 01 and VALIDATION. I'll check fixtures, the Vehicle route, and whether the planned assertion is executable.
A26’s fixtures and inheritance look real. I’ll check dispatch order and the other plans for a new executable gap.
## 06.2-01

**Summary:** A26 is closed in task 01-03. The registered polymorphic DELETE regression is executable; source remains unfixed and is not a plan failure.

**Strengths:** `06.2-01-PLAN.md:15`, `:28`, `:54`, and `:130` own `tests/test1/test_polymorphic.py`. `:137` adds `test_delete_vehicle_http_delete_rejected` on the existing `/vehicle/{pk}/delete/` route with `client_user_vehicle_delete`, `cv_vehicle`, and `car_sedan`, asserting 405, DELETE absent from Allow, and unchanged Car plus base Vehicle rows via `non_polymorphic`. `:138` and `:140` keep `test_delete_vehicle` (GET 200, validated POST 302) and run `-k delete` on cached Django 6.0 and 4.2. Round 4 at `:227` matches `06.2-VALIDATION.md:35` and `:212`. `VehicleDeleteView` at `tests/test1/app/views.py:579` subclasses `PolymorphicDeleteViewPermissionRequired` (`src/crud_views_polymorphic/lib/delete.py:9`), which subclasses `DeleteView` (`:5`, `src/crud_views/lib/views/delete.py:27`). Fixtures exist at `tests/test1/conftest.py:420`, `:427`, and `:495`. `Car`/`Vehicle` are multi-table (`tests/test1/app/models.py:148` and `:158`). The delete-permission user already gets GET 200 (`tests/test1/test_polymorphic.py:167`), so `CrudViewPermissionRequiredMixin.has_permission` (`src/crud_views/lib/view/base.py:900`) passes and the planned post-`CrudView` guard can return 405. Current GET/POST-only coverage at `test_polymorphic.py:163` is the gap the task fills.

**Concerns:** None.

**Suggestions:** None.

**Risk Assessment:** Low. Inheritance is the mechanism; 01-03 is the missing request assertion. Sequencing after 01-01 is explicit, so a second manufactured red is not required.

## 06.2-02

**Summary:** Parent-None, inactive denial, and the FK/M2M boundary are unchanged and still executable. A25's route-aware M2M enhancement stays an explicit deferral, not a missing task.

**Strengths:** `06.2-02-PLAN.md:115` denies M2M own-child inference and tests explicit-parent plus URL-bound Genre create/list. `ParentViewSet.many_to_many_through_attribute` is real (`src/crud_views/lib/viewset/parentviewset.py:19`); Genre uses it (`tests/test1/app/views.py:458`, `tests/test1/app/models.py:48`). Annotation-only names match `CheckUnknownAttributes` (`src/crud_views/lib/check.py:298`). List fallback still calls `cv_action_enabled(user, parent_obj)` after a failed lookup (`src/crud_views_guardian/lib/mixins.py:145`), which 02-01 routes through the adapter. Ledger deferral is at `:226`.

**Concerns:** None.

**Suggestions:** None.

**Risk Assessment:** Low. The deferred M2M control needs a selected-parent contract; choosing a related parent would invent authority.

## 06.2-03

**Summary:** Fragment authorization and ancestry validation remain in scope. A19's non-first-child output index is still an explicit proposed-6.3 deferral, not an omitted security check.

**Strengths:** `FormSetMixinBase.get` returns fragments before `super().get()` (`src/crud_views/lib/formsets/mixins.py:37`). `06.2-03-PLAN.md:90` initializes the authorized object first. `FormSet.init` passes `index=child_index` (`src/crud_views/lib/formsets/formsets.py:159`), while `get_template` still uses `index=0` (`:379`). `:81` and `:108` keep that mismatch out of passing round trips and still require authorization and FK ancestry on every declared path, including the second child. Ledger deferral is at `:176`.

**Concerns:** None.

**Suggestions:** None.

**Risk Assessment:** Low for D-09. The output-index defect remains a lifecycle limit, not an authorization bypass.

## 06.2-04

**Summary:** Inert ViewSet-flag removal, strict helper, and per-view manage policy are unchanged. The AUTH-06 classifier limit stays flagged, not treated as passed.

**Strengths:** The inert field is still read by manage (`src/crud_views_guardian/lib/viewset.py:23`, `src/crud_views_guardian/lib/views.py:231`). The helper already passes `accept_global_perms=False` (`viewset.py:67`). `06.2-04-PLAN.md:80` quotes the unclassified probe and forbids inferring completion from test count. `:163` carries that into the handoff.

**Concerns:** None.

**Suggestions:** None.

**Risk Assessment:** Low for the named D-03–D-06 work. Unclassified edges stay an acceptance limitation, not a silent pass.

## 06.2-05

**Summary:** The actor and native-template matrices still replay core/Guardian cells. Polymorphic DELETE is not missing here; 01-03 owns that assertion.

**Strengths:** `06.2-05-PLAN.md:110` limits own-child agreement to FK nesting and points M2M positives at 02-01. `:207` and `:219` keep A19 and route-aware M2M as deferrals. Manage singleton patching remains in the matrix preamble. Full `tests/test1` in plan 06 still collects `test_polymorphic.py`; this wave does not need a duplicate Vehicle cell.

**Concerns:** None.

**Suggestions:** None.

**Risk Assessment:** Low. A post-fix replay wave, with defect evidence cited from 01–04 rather than a manufactured red.

## 06.2-06

**Summary:** Docs, migration pairing, and supported-version evidence are unchanged. A19, A25, and AUTH-06 remain explicitly separated from implemented requirements. Polymorphic DELETE rides the existing full `tests/test1` selection.

**Strengths:** `06.2-06-PLAN.md:97` and `:201` document the index-zero deferral without calling it fixed. `:97`, `:115`, and `:214` keep route-aware M2M deferred and preserve explicit-parent and URL-bound paths. `:133` keeps the AUTH-06 probe flagged. `06.2-VALIDATION.md:214` correctly leaves plan 06 commands unchanged because full `tests/test1` includes `test_polymorphic.py`. Pre-fix baseline remains 5459/5460; no future AUTH pass is claimed.

**Concerns:** None.

**Suggestions:** None.

**Risk Assessment:** Low. Documentation wave; semantic review is still required at execution, and strict mkdocs is not that proof.

## Prior-item closure ledger

| Item | Disposition |
| --- | --- |
| A26 | **CLOSED.** 01-03 owns the registered `VehicleDeleteView` HTTP DELETE assertion: 405, DELETE absent from Allow, unchanged concrete Car and base Vehicle storage, retained GET/validated POST, focused Django 6.0 and 4.2 `-k delete` commands, synced `06.2-VALIDATION.md:35` and `:212`, Round 4 ledger at `06.2-01-PLAN.md:227`. |
| H01–H03, A01–A25 | **No regression.** Prior sign-offs stand. A19 second-child output index and A25 route-aware M2M controls remain explicit reasoned deferrals (`06.2-03-PLAN.md:176`, `06.2-02-PLAN.md:226`, repeated in 05 and 06). AUTH-06 unclassified probe remains flagged (`06.2-04-PLAN.md:80`). |
| New defects | None found. Current unfixed source, including GET/POST-only `test_polymorphic.py:163`, is not a failed plan. |

**Unresolved plan concerns:** None.
