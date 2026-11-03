# Phase 6.2 plan review, cycle 3 (HEAD bb2b609)

Repo access confirmed. Plan citations below resolve under `.planning/phases/06.2-request-authorization-and-write-integrity/`. Source was read directly; the one runtime probe I attempted (Django 4.2 warning reproduction) needed shell approval and did not run, so that finding rests on static source evidence.

## 06.2-01

**Summary.** `06.2-01-PLAN.md:99` restricts `http_method_names`, overrides `delete()`, captures `has_protected_objects` before filtering, and updates both templates. `:101` adds the A18 `_allowed_methods` filter. `:115` filters protected instances through `_PermittedPks` and removes the empty-tree shortcut. `:131` patches `http_method_names` on registered classes with teardown.

**Strengths.**
- The A18 mechanism is correct. Django builds the 405 `Allow` header and OPTIONS from `_allowed_methods()` (`.nox/crispy_floor-3-12-django-6-0/lib/python3.12/site-packages/django/views/generic/base.py:147-148`, `:166-169`, `:181-182`). One override covers both paths, as `:101` claims.
- Ordering claims hold. Guardian `has_permission` returns True without fetching (`src/crud_views_guardian/lib/mixins.py:31-38`), so a top-level Guardian DELETE reaches the handler before any object lookup. Core `has_permission` fetches the object and evaluates state (`src/crud_views/lib/view/base.py:900-910`), which produces the 403/404-before-405 rows in plan 05.
- Both gates on the notice are owned: `src/crud_views/templates/crud_views/view_delete.content.html:8` and `snippets/delete/related_objects.html:4-5`. The raw pass-through at `src/crud_views/lib/views/delete.py:172` and `:184`, and the Guardian shortcut at `src/crud_views_guardian/lib/views.py:42-43`, are the right targets.
- `post()` never calls `self.delete()` (`delete.py:199-222`), so closing the raw handler cannot affect the validated POST path.

**Concerns.**
- **MEDIUM (new, N-C1).** Overriding `delete()` as `:99` prescribes triggers Django 4.2's `DeleteViewCustomDeleteWarning` on every DeleteView instantiation. `BaseDeleteView.__init__` warns whenever `self.__class__.delete is not DeletionMixin.delete` (`.nox/crispy_floor-3-12-django-4-2/lib/python3.12/site-packages/django/views/generic/edit.py:257-266`). The package's `DeleteView` currently defines no `delete()` (`delete.py:27-222`), so this is a new per-request warning on a supported version. It does not fail the suite, since pytest only sets `--strict-markers` (`pyproject.toml:129-130`), but plan 06-03's Django 4.2 full run will carry it in the warnings summary. Django 6.0 has no such warning (`edit.py:220`).
- **LOW (new, N-C5).** The truth "filtering retains the relative order of permitted protected entries" (`:33`) must be tested against the same-request pre-filter list. `NestedObjects.protected` is a set (`django/contrib/admin/utils.py:190`), so `list(collector.protected)` at `delete.py:96` has no stable order across runs.

**Suggestions.**
- Replace the `delete()` override with a DELETE guard in a new `DeleteView.dispatch()` in `delete.py`, keeping the `http_method_names` restriction and the `_allowed_methods` filter. By MRO it runs after `PermissionRequiredMixin.dispatch` and Guardian parent dispatch and before `View.dispatch` handler lookup (`base.py:139-145`), so a subclass restoring the name, or even redefining `delete()`, still gets 405 with no `get_object`. If the override is kept, the plan must explicitly accept and filter the 4.2 warning.
- Word the order assertion as "permitted subsequence of the captured pre-filter list".

**Risk.** Low to medium. The remedy is sound; the one defect is a quality regression on Django 4.2 with an easy alternative.

## 06.2-02

**Summary.** `06.2-02-PLAN.md:105` centralizes the parent-permission key, resolves the URL parent first and runs state for no-object views. `:107` adds the H03 own-child resolver. `:123` adds inactive denial. `:136` adds the `_cv_action_enabled_for_context` adapter and routes toolbar, ContextButton and card state through it. `:138` owns real child-page tests.

**Strengths.**
- The resolver sits at the one seam every permission caller shares. `_cv_get_action_context` (`base.py:710`), `ContextButton` (`src/crud_views/lib/view/buttons.py:112`), card actions (`src/crud_views/lib/views/card.py:88`) and the filter (`src/crud_views/templatetags/crud_views.py:473`) all call `cls.cv_has_access(user, page object)`. Today `src/crud_views_guardian/lib/views.py:206` returns True for a Book and `:190-191` False for None. The plan's FK path via `ParentViewSet.get_attribute()` (`src/crud_views/lib/viewset/parentviewset.py:62-66`) matches the test fixture `attribute="publisher"` (`tests/test1/app/views.py:715`).
- The adapter covers every state call site I found: `base.py:707`, `buttons.py:109`, `:182`, `:234`, `:291`, `card.py:66`, `:89`. Dispatch stays untouched and already uses the parent as the action object (`base.py:368-375`, `mixins.py:244`).
- "Linked to the actual FK parent" is sound: create URLs take parent args from `self.kwargs` (`base.py:530-536`), and child querysets are parent-filtered (`src/crud_views/lib/viewset/__init__.py:281-293`), so the own-child's FK parent equals the URL parent for FK children.
- `:109` and `:123` match the mixin seams at `mixins.py:196-202` and `:230-245`.

**Concerns.**
- **LOW (new, N-C2).** `:109` declares `cv_guardian_accept_global_perms=False` and `cv_guardian_anonymous_behavior="redirect"` as values on `GuardianParentPermissionMixin`. That mixin is first in every package composition (`views.py:24-26`, `:30-32`, `:85-90`, `:100-103`), so a value there shadows a project mixin placed later, such as `class Obj(GuardianObjectPermissionMixin): cv_guardian_accept_global_perms = True` composed after the parent mixin. Today the parent mixin has no attribute and the later value wins. W280 accepts annotation-only declarations (`src/crud_views/lib/check.py:298-301`), so annotations satisfy A13 without changing resolution.
- **LOW (new, N-C3).** The list-page override at `mixins.py:155` calls `target_cls.cv_action_enabled(user, parent_obj)` directly, with `parent_obj` possibly None after `:147-153`. It is not among the sites `:136` routes through the adapter, so a custom hook still receives None there while every other seam now returns False without calling it.
- **LOW (new, N-C4).** For many-to-many-through children the configured attribute is a manager, not an instance (`tests/test1/app/views.py:458`, core ViewSet). The `:107` rule denies, which is fail-closed and acceptable, but plan 06 should state that own-child resolution supports FK parents only.
- **LOW (new, N-C6).** `:105` phrases parent resolution under a None key around no-object views. Plan 05 row `06.2-05-PLAN.md:96` expects 404 for a missing parent "including DELETE" on object child views. Today `mixins.py:233-235` returns before `get_object_or_404` when the key is None, and the DELETE handler never reaches `get_object`, so that row needs 02-01 to resolve the parent for all child views, not only no-object ones.

**Suggestions.** Use annotation-only declarations for A13. Route `mixins.py:155` through the adapter. Add one sentence to `:105` making parent resolution under None apply to every child view. Add the FK-only note to 06-01.

**Risk.** Low. H03's remedy is complete and independently checkable; residual items are precision refinements.

## 06.2-03

**Summary.** `06.2-03-PLAN.md:90` authorizes before `get_template_html`. `:104` adds the declaration-aware validator. `:106` adds UUID test models. `:81` bounds round-trip claims. `:108` and `:176` characterize and defer the non-first-child index mismatch.

**Strengths.**
- The defect seam is exactly as stated: `src/crud_views/lib/formsets/mixins.py:37-45` serves fragments before `super().get()`, and `:47-69` validates only key path and `num.isdigit()` (`:54-55`), which accepts Unicode digits, confirming A15's ASCII grammar.
- A19 is grounded: `FormSet.init` passes `index=child_index` (`src/crud_views/lib/formsets/formsets.py:159-167`) while `get_template` hardcodes `index=0` (`:379`). The boundary at `:81` is stated precisely, ancestry validation stays mandatory, and `:108` forbids rejecting valid coordinates to hide the defect.
- Object initialization follows the existing POST pattern (`src/crud_views/lib/views/mixins.py:37`).

**Concerns.** None new.

**Suggestions.** None beyond keeping the summary record of the two-child characterization, as `:108` already requires.

**Risk.** Low. Validator complexity is the main implementation risk, already bounded by explicit payload positives.

## 06.2-04

**Summary.** `06.2-04-PLAN.md:92` removes the field, reader and leaf atomically with a Mapping-guarded before-validator. `:106` projects per-view applicability. `:108` patches the settings singleton for A20. `:80` keeps the AUTH-06 probe flagged.

**Strengths.**
- Removal targets are real: field at `src/crud_views_guardian/lib/viewset.py:22`, reader at `src/crud_views_guardian/lib/views.py:231`, strict helper at `viewset.py:64-73`. The after-validator at `:35-49` registers only after before-validation passes, so a rejected constructor leaves no registry entry.
- A20's seam is confirmed: `from_settings` is a `getattr` snapshot (`src/crud_views/lib/settings.py:13-14`), fields at `:27-28`, singleton at `:337`; manage reads the singleton and live `DEBUG` (`src/crud_views/lib/views/manage.py:31-39`). The recipe matches `tests/test1/test_manage.py:122`, `:140`, `:154`.
- Applicability rules at `:106` map onto `GUARDIAN_MIXINS` (`views.py:17-21`) and `get_view_data` (`:270-276`).

**Concerns.** None new. The AUTH-06 unclassified probe remains a flagged assumption at `:80`, assessed as such.

**Suggestions.** None.

**Risk.** Low.

## 06.2-05

**Summary.** `06.2-05-PLAN.md:64-106` is the status and storage oracle, `:91-93` the DELETE ordering rows, `:97-101` parent-None and child-page rows, `:103-106` manage modes, `:108` the A20 recipe, `:110` and `:139` the H03 render and route coverage, `:137` the six native seams.

**Strengths.**
- Every DELETE row is derivable from source: `:91` from `mixins.py:31-38` plus MRO, `:92-93` from `base.py:900-910`, `:95` from `mixins.py:230-238`.
- `:99-101` separate page access, create permission, state and filter result, and `:139` asserts the hook receives a Publisher while rendering a Book page. That is the discriminating test H03 required.
- `:108` names the exact singleton fields and reserves `override_settings` for `DEBUG` and `ROOT_URLCONF`.

**Concerns.**
- **LOW (shared N-C6).** Row `:96` for Guardian object views under a None parent key depends on 02-01 resolving the parent in dispatch, per the 06.2-02 concern above. The row itself is correct as the target contract.

**Suggestions.** Cross-reference `:96` to the 02-01 clarification once made.

**Risk.** Low. Test-only wave with exact expectations.

## 06.2-06

**Summary.** `06.2-06-PLAN.md:95` documents helpers, parent-None, manage rows and the own-child filter recipes. `:97` documents 405 and truthful Allow/OPTIONS. `:113` pairs Breaking and migration. `:115` is the A21 override contract. `:129-131` run both environments and hand off. `:86` records the measured baseline.

**Strengths.**
- A21 is precise: it names `RelatedObjects.protected`, the pre-filter flag, superclass delegation, and the per-view fallback effect on related labels. Hooks are at `delete.py:147` and `src/crud_views_guardian/lib/views.py:39`; `_PermittedPks` consumes the view's fallback at `:45` and `:67`.
- The recipes to update exist at `docs/reference/context_buttons.md:482`, `:531-539`, and the fallback prose at `docs/reference/guardian.md:88`, `:97`, `:181`, `:242`. `docs/reference/delete_view.md` currently does not mention the filter hook at all, so 06-01 is adding, not amending.
- `:129` includes all six new modules and the full suite under both cached environments, which exist (`.nox/crispy_floor-3-12-django-4-2`, `-6-0`). Every test module named in verify commands exists on disk.

**Concerns.**
- **LOW (shared N-C1, N-C4).** If 01 keeps the `delete()` override, 06-02 must document the Django 4.2 warning. 06-01 should state FK-only own-child resolution.

**Suggestions.** Add the two sentences above once 01 and 02 settle.

**Risk.** Low.

## Cross-plan assessment

The H03 remedy is coherent across plans: 02-01 fixes permission at the shared classmethod, 02-03 fixes state through a private adapter without touching the public hook or ViewContext, 05 proves it on real pages and routes, and 06 rewrites the recipes. No plan reopens locked decisions. URL ancestry validation is retained. The one cross-plan dependency worth tightening is parent resolution under a None key, which plan 05 assumes and plan 02 states only for no-object views.

## Prior-item closure ledger

| ID | Verdict | Plan evidence | Source mechanism verified |
| --- | --- | --- | --- |
| H03 | **Signed off** | 02:27, 02:107, 02:136, 02:138, 05:99-101, 05:110, 05:139, 06:95, 06:113 | `views.py:190-206` caller paths at `base.py:707/710`, `buttons.py:109/112/182/234/291`, `card.py:66/88-89`, `templatetags/crud_views.py:473`; URL binding `base.py:530-536`; FK map `parentviewset.py:62-66` |
| A18 | Closed | 01:24, 01:101, 01:131, 06:97 | `django/views/generic/base.py:147-148`, `:166-169`, `:181-182` |
| A19 | Closed (explicit deferral) | 03:81, 03:108, 03:176, 05:207, 06:99, 06:131 | `formsets.py:159-167` vs `:379` |
| A20 | Closed | 04:108, 05:108 | `settings.py:13-14`, `:27-28`, `:337`; `manage.py:31-39`; `test_manage.py:122/140/154` |
| A21 | Closed | 06:115, 06:194 | `delete.py:147`, `guardian/lib/views.py:39`, `:45`, `:67` |
| H01 | No regression | 01:99 both templates | `view_delete.content.html:8`, `related_objects.html:4-5` |
| H02 | No regression; superseded for own-child only | 02:107, 02:206, 06:113 | `tests/test1/test_guardian.py:337-341` still owned |
| A01–A17 | No regression | Round 1 ledgers unchanged in all six plans; A04 at 01:115, A09/A12/A17 at 04:92/106, A13 at 02:109, A15 at 03:104, A16 at 06:113 | Spot-checked seams unchanged |

## Genuinely unresolved plan concerns (deduplicated)

1. **N-C1, MEDIUM, plan 01.** The `delete()` override emits `DeleteViewCustomDeleteWarning` per instantiation on Django 4.2 (`edit.py:257-266`). Prefer a DELETE guard in `DeleteView.dispatch()` with the existing `http_method_names` and `_allowed_methods` changes, or explicitly accept and filter the warning.
2. **N-C2, LOW, plan 02-01.** Attribute values on `GuardianParentPermissionMixin` can shadow later customized mixins by MRO; use annotation-only declarations, which W280 accepts (`check.py:298-301`).
3. **N-C3, LOW, plan 02-03.** Route `mixins.py:155` through the new adapter.
4. **N-C4, LOW, plans 02/06.** Document FK-only own-child resolution; M2M-through children deny.
5. **N-C5, LOW, plan 01.** Assert protected order against the same-request pre-filter list, since `NestedObjects.protected` is a set (`admin/utils.py:190`).
6. **N-C6, LOW, plans 02/05.** State in 02-01 that URL-parent resolution under a None key applies to all child views, so row 05:96 holds for DELETE on object views (`mixins.py:233-235`).

CYCLE_SUMMARY: current_high=0 current_actionable=6 (1 MEDIUM, 5 LOW); H03 and A18–A21 closed; no regression to H01, H02, A01–A17.
