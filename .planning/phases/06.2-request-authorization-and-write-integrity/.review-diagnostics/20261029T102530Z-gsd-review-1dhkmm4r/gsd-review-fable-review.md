Evidence basis for this cycle: all mechanism claims below come from source reads at HEAD e385113. Runtime Python probes were not executable under this session's permissions (every interpreter invocation was declined), so the A22 "no warning emitted" and A23 "composed True/404 preserved" runtime facts are carried from the cycle-3 probes and re-derived here from Django's own source and Python attribute semantics. Where that matters I say so.

## 06.2-01

**Summary.** Rejects DELETE via a private cooperative dispatch guard inserted between `CrudView` and `generic.DeleteView` in `DeleteView`'s bases (`src/crud_views/lib/views/delete.py:27` today reads `CrudViewProcessFormMixin, CrudView, generic.DeleteView`), restricts `http_method_names`, filters `_allowed_methods`, and projects safe protected previews with an independent `has_protected_objects` flag.

**Strengths.**
- Guard placement is correct for both families. `CrudView.dispatch` wraps `super().dispatch` and applies `patch_vary_headers` afterwards (`src/crud_views/lib/view/base.py:227-231`), so a 405 produced by the guard still receives the modal Vary header. C3 puts `PermissionRequiredMixin.dispatch` ahead of `DeleteView` for `DeleteViewPermissionRequired` (`delete.py:225`), so core object/state lookup in `CrudViewPermissionRequiredMixin.has_permission` (`base.py:899-908`) still denies earlier; for Guardian, `GuardianObjectPermissionMixin.has_permission` returns True without calling super (`src/crud_views_guardian/lib/mixins.py:31-38`), so no `get_object` runs before the guard. The plan's truth at `06.2-01-PLAN.md:22` matches source.
- Warning avoidance is sound. Django 4.2 warns only when `self.__class__.delete is not DeletionMixin.delete` (`.nox/crispy_floor-3-12-django-4-2/.../django/views/generic/edit.py:257-266`); the guard defines no `delete`, and `06.2-01-PLAN.md:99` explicitly leaves identity intact. Django 6.0's `edit.py` no longer defines the warning class (grep returned nothing), matching the conditional-import instruction at `:101`.
- Single header hook is real: Django's `http_method_not_allowed` and `options` both read `self._allowed_methods()` (`django/views/generic/base.py:147-148`, `:166-168`, `:181`). No other `http_method_names` consumer exists in `src/` (grep empty), so restricting the list has no URL or check side effects.
- Preview flag: both gates are owned (`view_delete.content.html:8` and `related_objects.html:4`), and protected values currently pass through unfiltered at `delete.py:172`/`:184`, confirming the defect and the fix boundary.

**Concerns.**
- LOW (new, evidence gap only): D-02 says "all package delete views". `PolymorphicDeleteView(DeleteView)` (`src/crud_views_polymorphic/lib/delete.py:5-10`) inherits the guard, and a registered polymorphic delete route exists (`VehicleDeleteView`, `tests/test1/app/views.py:579`), but neither plan 01 nor plan 05 names a polymorphic DELETE assertion. Mechanism is covered by inheritance; evidence is not.

**Suggestions.**
- Add one row to 01-03 or the 05-01 matrix: DELETE on the registered `VehicleDeleteView` route returns 405 with DELETE absent from Allow. One assertion, no new fixtures.

**Risk Assessment.** Low. The guard is additive, exercises existing Django hooks, and the plan already pins warning-free construction in both supported environments.

## 06.2-02

**Summary.** Shared parent-permission resolver, FK own-child parent resolution, annotation-only mixin declarations, a private context-state adapter routed through base/list/button/card sites, M2M fail-closed boundary, and inactive denial across dispatch, `has_permission`, helpers and `_PermittedPks`.

**Strengths.**
- A23 mechanism verified. `_own_cv_annotations` reads `klass.__annotations__` and `_collect_cv_names` adds those names to `data_names` (`src/crud_views/lib/check.py:290-302`), so annotation-only declarations satisfy W280. An annotation without a value creates no class attribute, so MRO lookup falls through to a later consumer mixin's `True`/`"404"`; the existing `getattr` fallbacks at `mixins.py:205` and `:224` and `views.py:171`, `:194` keep parent-only views at False/redirect. Package compositions put the parent mixin first (`src/crud_views_guardian/lib/views.py:24`, `:30`, `:85-90`, `:100`), which is exactly the ordering `06.2-02-PLAN.md:109` tests.
- A24 seam verified. `mixins.py:145-155` catches `Http404`/`KeyError` from `cv_get_parent_object` and then calls `target_cls.cv_action_enabled(user, None)` at `:155`. `cv_get_parent_object` raises exactly those two (`base.py:851-863`: `self.kwargs[arg]` and `get_object_or_404`), and dispatch's parent lookup at `mixins.py:235` is a separate query, so the "late failure after successful dispatch" case in `06.2-02-PLAN.md:113` is simulable by patching the list view only. Routing `:155` through the adapter also removes today's double invocation (base `_cv_get_action_context` at `base.py:703` with None, then `:155` with the parent).
- A25 fixture verified. `Genre.publishers` is an M2M (`tests/test1/app/models.py:52`), `cv_genre` declares `attribute="publishers", many_to_many_through_attribute="genres"` (`tests/test1/app/views.py:458`), and `CreateViewParentMixin.cv_form_valid` binds via the parent manager (`src/crud_views/lib/views/create.py:53-61`). The explicit-parent path keeps working because the existing `isinstance(obj, parent_vs.model)` branch (`views.py:184-196`) is retained. Duplicate-model isolated ViewSets are an established pattern (`cv_guardian_publisher_cascade`, `cv_guardian_author_origin`).
- H02/H03 preservation: the named stale test still asserts True for a Book input (`tests/test1/test_guardian.py:337-341`) and the filter passes `view.object` straight to `cv_has_access` (`src/crud_views/templatetags/crud_views.py:473`), so the FK-resolution remedy is still needed and still owned here.
- Inactive: the conftest backend list is ModelBackend plus Guardian (`tests/test1/conftest.py:104-107`), so the plan's `AllowAllUsersModelBackend` override and `force_login(backend=...)` are required for a real inactive session, as `:138` specifies.

**Concerns.** None actionable. The A25 deferral rationale ("object-only input carries no selected parent") is precise for the classmethod signature; note that ContextButton and the filter do receive the view (`buttons.py:109`, `templatetags/crud_views.py:473`), so a future route-aware contract is feasible without widening the helper. The plan's wording at `06.2-02-PLAN.md:201` already frames it that way; no change needed.

**Suggestions.** None beyond what is written.

**Risk Assessment.** Low-medium only because 02-01 is the largest task (five files) and carries three distinct remedies; the plan sequences them explicitly and 02-03 does not redefine them.

## 06.2-03

**Summary.** Authorizes fragments before rendering by initializing the target through the cooperative `get_object`, then validates declaration/FK ancestry with UUID-aware grammar; A19's non-first-child output-index defect stays deferred.

**Strengths.**
- Defect confirmed in source: `FormSetMixinBase.get` serves fragments before `super().get()` (`src/crud_views/lib/formsets/mixins.py:37-45`), and `get_template_html` only checks the key path and `num.isdigit()` (`:47-69`); `"²".isdigit()` is True and `int("²")` raises, so A15's stable-400 fix is needed.
- A19 characterization is accurate: `FormSet.init` enumerates child declarations with `child_index` (`formsets.py:153-160`) while `get_template` always calls `formset.template(index=0, ...)` (`formsets.py:378`).
- UUID fixture is executable: the test app has no migrations directory, so added models are created by the in-memory setup.

**Concerns.** None.

**Suggestions.** None.

**Risk Assessment.** Medium. The validator touches the most protocol-sensitive code path, but the plan pins exact browser payloads and preserves wire names.

## 06.2-04

**Summary.** Removes `GuardianViewSet.cv_guardian_accept_global_perms` with a targeted before-validator, replaces the manage reader atomically, and reports per-view effective policy plus the strict helper.

**Strengths.**
- Atomic ownership is justified: the manage reader dereferences the field today (`src/crud_views_guardian/lib/views.py:232`) and the leaf renders it (`config_table.html:15-18`); the field and strict helper sit together (`viewset.py:23`, `:63-73`).
- Registration cannot survive a failed before-validator because `register` is an after-validator (`viewset.py:35-49`, base `src/crud_views/lib/viewset/__init__.py:125-151`).
- A20 remains correct: `manage_views_enabled`/`manage_group` are import-time snapshots (`src/crud_views/lib/settings.py:27-28`).

**Concerns.** None. AUTH-06/unclassified stays flagged at `06.2-04-PLAN.md:80`.

**Suggestions.** None.

**Risk Assessment.** Low.

## 06.2-05

**Summary.** Direct actor/route matrix and six native-template override regressions.

**Strengths.**
- Core versus Guardian DELETE ordering rows match source as traced under plan 01. Manage rows match the gate: `has_permission` returns True for "yes" or debug_only+DEBUG, False for anonymous, else group membership (`src/crud_views/lib/views/manage.py:30-39`), so "no" mode with group member 200, nongroup 403, anonymous 302 is correct.
- Every module named in the verify commands exists, including the golden pair `test_filter_form_baseline`/`test_filter_form_controls_match_golden` (`tests/test1/test_form_buttons_golden.py:266`, `:275`), both nox interpreters and `.venv/bin/mkdocs`.
- A25 scoping sentence at the matrix preamble keeps child-page rows FK-only without withdrawing H03 coverage.

**Concerns.**
- LOW: shares the polymorphic evidence gap noted under plan 01; the matrix lists only core and Guardian DELETE rows.

**Suggestions.** Add the `VehicleDeleteView` 405 cell here if not in 01-03.

**Risk Assessment.** Low.

## 06.2-06

**Summary.** Reference, migration and changelog pairing plus the supported-version acceptance record and Phase 7 handoff.

**Strengths.**
- Targets exist: `cv_context_has_permission` sections at `docs/reference/context_buttons.md:531` and `docs/faq.md:130`; `theme.md` headings "Custom form-button templates" (:136), "Cancel links in custom form-button templates" (:191) and "Custom alert frame" (:272) are the ones A16 protects; `CHANGELOG.md:3-7` has the Unreleased Breaking section.
- A21 and A25 documentation obligations are stated with the correct boundary (delete-view fallback governs related-label global grants; M2M object-only controls fail closed while URL-bound create works), matching `views.py:44` and `create.py:53-61`.

**Concerns.** None.

**Suggestions.** When documenting D-02, name `PolymorphicDeleteView` as an inheriting package delete view so the "all package delete views" claim is explicit.

**Risk Assessment.** Low.

## Cross-plan assessment

Wave ordering still holds: 04's applicability rows depend on 02's class-callable resolver (02 precedes 04), and 05/06 only consume. No same-wave file overlap was introduced by moving the adapter into 02-01.

## Prior-item closure ledger

| Item | Verdict | Evidence |
| --- | --- | --- |
| A22 | **Signed off.** Guard after `CrudView`, before `generic.DeleteView`; no `delete` override; `_allowed_methods` filter feeds 405 and OPTIONS; Vary retained. | `06.2-01-PLAN.md:99-101`; `delete.py:27`; `base.py:227-231`; Django 4.2 `edit.py:257-266`, `base.py:147-181`. Runtime no-warning check not re-run this session; plan 01-01 mandates it in both environments. |
| A23 | **Signed off.** Annotation-only declarations, W280 recognition, retained getattr defaults, composed True/404 regression. | `06.2-02-PLAN.md:109`; `check.py:290-302`; `mixins.py:205`, `:224`; `views.py:24-30`. |
| A24 | **Signed off.** List fallback routed through the adapter; late `Http404`/`KeyError` case executable; hook never receives None. | `06.2-02-PLAN.md:111-113`; `mixins.py:145-155`; `base.py:851-863`. |
| A25 | **Signed off.** FK-only own-child resolution, M2M flag rejection without parent selection, explicit-parent and URL-bound positives, route-aware controls explicitly deferred in 02/05/06. | `06.2-02-PLAN.md:115`, `:201`; `06.2-05-PLAN.md` preamble; `06.2-06-PLAN.md:95`, `:113`; `models.py:52`; `views.py:458`; `create.py:53-61`. |
| H01–H03, A01–A21 | No regression found. Both preview gates still owned by 01; stale wrong-type test and filter path still owned by 02; A19 deferral unchanged in 03/05/06; A20 singleton patching unchanged in 04/05. | `view_delete.content.html:8`; `related_objects.html:4`; `test_guardian.py:337`; `formsets.py:378`; `settings.py:27-28`. |

## Unresolved plan concerns

1. **LOW, new:** no explicit DELETE regression for the registered polymorphic delete route (`VehicleDeleteView`), although the guard is inherited. One matrix cell closes it.

Counts for this cycle: 0 HIGH, 1 actionable non-HIGH (new, LOW). A19 deferral and the AUTH-06 flagged assumption remain as recorded and add no count.

CYCLE_SUMMARY: current_high=0 current_actionable=1
