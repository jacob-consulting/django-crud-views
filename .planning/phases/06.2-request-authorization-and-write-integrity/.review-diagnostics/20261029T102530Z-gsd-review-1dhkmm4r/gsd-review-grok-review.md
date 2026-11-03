I'll verify A22–A25 against the revised plans and current source, without treating unfixed code as a plan defect.
The plans name the A22–A25 remedies. Next I’ll check those mechanisms against Django and the current call sites.
## 06.2-01

**Summary:** Reject DELETE with a cooperative dispatch guard and keep the validated POST path. Source is still the unfixed bypass; that is not a plan defect.

**Strengths:** The guard is specified after `CrudView` and before `generic.DeleteView` (`06.2-01-PLAN.md:100`). Current bases are `DeleteView(CrudViewProcessFormMixin, CrudView, generic.DeleteView)` (`src/crud_views/lib/views/delete.py:27`). `CrudView.dispatch` wraps `super()` and then sets `X-CV-Modal` Vary (`src/crud_views/lib/view/base.py:227-231`). Guardian parent dispatch and `PermissionRequiredMixin.dispatch` sit earlier in the MRO (`src/crud_views_guardian/lib/views.py:85-90`, `src/crud_views_guardian/lib/mixins.py:196-202`). Authenticated Guardian `has_permission` returns True without `get_object` (`src/crud_views_guardian/lib/mixins.py:31-38`), so top-level DELETE can 405 before object lookup. Django 4.2 warns only when `self.__class__.delete is not DeletionMixin.delete` (`.nox/crispy_floor-3-12-django-4-2/lib/python3.12/site-packages/django/views/generic/edit.py:259-265`). The plan leaves that identity unchanged, filters DELETE in `_allowed_methods` for both 405 Allow and OPTIONS, and tests restored `http_method_names` (`06.2-01-PLAN.md:102`, `:132`, `:210`). POST stays on the package handler (`src/crud_views/lib/views/delete.py:199-219`).

**Concerns:** None.

**Suggestions:** None.

**Risk Assessment:** Low. The warning, header, and reinstatement vectors are executable and version-specific. Implementation has not run.

## 06.2-02

**Summary:** Parent-None, inactive denial, and FK parent resolution, with annotation-only policy names, a list-fallback adapter, and an explicit M2M fail-closed boundary.

**Strengths:** A23 is annotation-only, with `getattr` fallbacks kept (`06.2-02-PLAN.md:28`, `:111`). `CheckUnknownAttributes` already unions annotation-only `cv_*` names (`src/crud_views/lib/check.py:297-301`). Parent mixins precede object/queryset mixins (`src/crud_views_guardian/lib/views.py:24-25`, `:112`), so assigned defaults would shadow a later `True`/`"404"`; annotations do not. A24 routes the post-lookup call at `src/crud_views_guardian/lib/mixins.py:145-155` through `_cv_action_enabled_for_context`, returns False with no hook when unresolved, and spies a real Publisher on success (`06.2-02-PLAN.md:113`). Dispatch uses `get_object_or_404` (`src/crud_views_guardian/lib/mixins.py:235`), so a late `cv_get_parent_object` failure is a separate seam. `cv_create_has_access(None)` is already False (`src/crud_views_guardian/lib/views.py:144-145`). A25 rejects own-child inference when `many_to_many_through_attribute` is set, accepts an explicit parent, and tests URL create (`06.2-02-PLAN.md:109`, `:115`). Genre is an existing M2M (`tests/test1/app/models.py:48-52`, `tests/test1/app/views.py:458`); URL binding uses the parent manager (`src/crud_views/lib/views/create.py:53-64`). Route-aware M2M controls are deferred with a no-selected-parent rationale (`06.2-02-PLAN.md:226`).

**Concerns:** None.

**Suggestions:** None.

**Risk Assessment:** Low. FK resolution, list-hook denial, and M2M positives are specified on real models. The deferred M2M control is not claimed as delivered.

## 06.2-03

**Summary:** Authorize fragments and validate ancestry. The non-first child output-index mismatch stays deferred.

**Strengths:** `FormSets.get_template` still passes `index=0` (`src/crud_views/lib/formsets/formsets.py:374-379`). The plan keeps authorization and FK ancestry for every declared path, bounds round-trip positives to first-child coordinates, and defers the emitted-index repair to proposed 6.3 (`06.2-03-PLAN.md:81`, `:176`). No ancestry check is removed.

**Concerns:** None.

**Suggestions:** None.

**Risk Assessment:** Low for this cycle. A19 remains a known lifecycle limit, not an authorization hole, and is not scheduled.

## 06.2-04

**Summary:** Remove the inert ViewSet flag and show per-view manage policy. AUTH-06 classifier limit stays flagged.

**Strengths:** The removed field is still on the ViewSet (`src/crud_views_guardian/lib/viewset.py:23`). Removal, strict helper, and manage projection remain in 04-01/04-02. The unclassified AUTH-06 probe is carried as unresolved, not inferred complete (`06.2-04-PLAN.md` flagged-assumption block; ledger deferral). Round-3 edits do not drop A20 singleton patching.

**Concerns:** None.

**Suggestions:** None.

**Risk Assessment:** Low for plan closure. AUTH-06's unclassified edge stays a handoff assumption, not a new gap.

## 06.2-05

**Summary:** Direct actor and native-template matrices. Own-child agreement is limited to FK nesting.

**Strengths:** The matrix preamble keeps reachable child-page FK rows and points M2M object-only denial plus explicit-parent/URL positives at 02-01 (`06.2-05-PLAN.md:110`, `:214`). It does not promise M2M child-page inference. A19 positives stay inside plan 03's coordinate boundary. A20 singleton patching is unchanged.

**Concerns:** None.

**Suggestions:** None.

**Risk Assessment:** Low. Replay scope matches the FK contract and does not reopen deferred M2M controls.

## 06.2-06

**Summary:** Document the method, helper, preview, and M2M boundaries and record supported-version evidence.

**Strengths:** guardian/context-button/FAQ text, Breaking/migration, and the Phase 7 handoff all state M2M object-only fail-closed behavior, explicit-parent and URL-bound positives, and deferred route-aware controls (`06.2-06-PLAN.md:95-97`, `:115`, `:133`, `:208`, `:214`). Handoff also records warning-free Django 4.2 construction, annotation-only inherited policy, and list-fallback failure (`06.2-06-PLAN.md:133`, `:209`). A19 and the AUTH-06 probe stay separate from passing evidence (`06.2-06-PLAN.md:99`, `:133`). URL ancestry validation is retained.

**Concerns:** None.

**Suggestions:** None.

**Risk Assessment:** Low. Docs are specified against named tests. Baseline 5459/5460 is pre-fix evidence only; future AUTH runs are not claimed.

## Cross-plan assessment

A22–A25 are closed as plan defects. The DELETE guard matches Django 4.2's delete-identity warning and the live MRO, so it can 405 after existing gates without a `delete()` override. Annotation-only names preserve later mixin values and remain W280-visible. The list fallback and the create adapter share one unresolved-parent rule. M2M own-child inference is fail-closed, with explicit-parent and URL-create positives, and route-aware controls are deferred rather than invented. No H01–H03 or A01–A21 regression: both preview gates, FK own-child resolution, method headers, manage singleton patches, and ancestry checks remain required. Source is still unfixed at `e385113`; that is expected.

## Prior-item closure ledger

| ID | Verdict |
| --- | --- |
| A22 | **Signed off.** Dispatch guard after `CrudView`, before Django `DeleteView`; no `delete()` override; `_allowed_methods` filters DELETE; restored `http_method_names` still 405; warning asserted by category name on 4.2/6.0 (`06.2-01-PLAN.md:100`, `:102`, `:132`, `:210`). |
| A23 | **Signed off.** Annotation-only declarations, `getattr` fallbacks, composed `True`/`"404"` regression (`06.2-02-PLAN.md:111`, `:219`). |
| A24 | **Signed off.** List fallback uses the context-state adapter; failed lookup does not call the custom hook with None; success passes the real parent; 02-01 owns it, 02-03 does not redefine it (`06.2-02-PLAN.md:113`, `:142`, `:220`). |
| A25 | **Signed off as boundary plus explicit deferral.** FK-only own-child helper; M2M object-only denial; explicit parent and URL create/list positives; route-aware controls deferred (`06.2-02-PLAN.md:115`, `:226`; `06.2-05-PLAN.md:110`; `06.2-06-PLAN.md:97`, `:214`). |
| A19 | **Deferral preserved.** Non-first child output index remains proposed 6.3; ancestry stays mandatory (`06.2-03-PLAN.md:81`, `:176`). |
| H01–H03, A01–A21 | **No regression.** Prior closures and the A19 deferral still have executable actions or explicit disposition. |
| AUTH-06 unclassified | **Still flagged**, not counted as a new defect. |

## Unresolved plan concerns

None.
