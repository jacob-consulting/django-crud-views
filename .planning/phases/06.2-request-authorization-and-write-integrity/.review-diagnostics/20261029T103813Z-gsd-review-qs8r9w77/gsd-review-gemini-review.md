## 06.2-01

### Summary
Plan `06.2-01` (`.planning/phases/06.2-request-authorization-and-write-integrity/06.2-01-PLAN.md:1-237`) closes the inherited HTTP `DELETE` write-bypass (`AUTH-01`, `D-01`, `D-02`) and secures delete confirmation previews for protected related objects (`AUTH-03`, `D-07`, `D-08`) across core, Guardian, and polymorphic delete views while preserving validated `POST` deletion, protection checks, hooks, and atomic rollback (`AUTH-07`, `D-12`, `D-13`). In cycle 5, Task `01-03` explicitly incorporates `A26` by owning `tests/test1/test_polymorphic.py` and adding a direct `DELETE` rejection regression on the registered `VehicleDeleteView` alongside the retained `GET`/validated-`POST` positive controls.

### Strengths
- **Complete closure of `A26` on the registered polymorphic delete route:** `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-01-PLAN.md:15,28,54-55,129-143,222-232` owns `tests/test1/test_polymorphic.py` and specifies `test_delete_vehicle_http_delete_rejected` using existing fixtures `client_user_vehicle_delete`, `cv_vehicle`, and `car_sedan` (`tests/test1/conftest.py:420-431,495-497`) against `/vehicle/{pk}/delete/` served by `VehicleDeleteView` (`tests/test1/app/views.py:579-581`, which inherits `PolymorphicDeleteViewPermissionRequired` -> `PolymorphicDeleteView` -> `DeleteView` at `src/crud_views_polymorphic/lib/delete.py:5-10`). It snapshots both `Car` (`tests/test1/app/models.py:158-159`) and `Vehicle.objects.non_polymorphic()` (`tests/test1/app/models.py:148-155`), asserts HTTP `405` and `DELETE` absent from `Allow`, verifies unchanged concrete and base storage, retains `test_delete_vehicle` (`tests/test1/test_polymorphic.py:163-175`) as the `GET=200` / confirmed-`POST=302` positive control, and executes `-k delete` under both cached Django 6.0 and 4.2 environments (`06.2-01-PLAN.md:140`, synced in `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-VALIDATION.md:35,208-214`).
- **Warning-free cooperative `DELETE` guard and truthful method advertisement (`A18`, `A22`):** `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-01-PLAN.md:91,103-105,135` places `_DeleteMethodGuardMixin` after `CrudView` and before `generic.DeleteView` in `DeleteView` (`src/crud_views/lib/views/delete.py:27`) and filters `DELETE` in `DeleteView._allowed_methods()`. This preserves `DeletionMixin.delete` identity (avoiding `DeleteViewCustomDeleteWarning` on Django 4.2), keeps `CrudView.dispatch` modal `Vary: X-CV-Modal` decoration (`src/crud_views/lib/view/base.py:227-234`), preserves earlier `GuardianParentPermissionMixin.dispatch` (`src/crud_views_guardian/lib/mixins.py:196-202`) and `CrudViewPermissionRequiredMixin.has_permission` (`src/crud_views/lib/view/base.py:900-910`) gates, and ensures both `405 Allow` and `OPTIONS` omit `DELETE` even when a subclass restores `"delete"` in `http_method_names`.
- **Independent blocked-deletion notice and single-pass permission projection (`H01`, `A01`, `A02`, `A04`):** `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-01-PLAN.md:57-62,103,119` captures `has_protected_objects = bool(related.protected)` in `DeleteView.get_context_data` (`src/crud_views/lib/views/delete.py:179-185`) before calling `cv_filter_related_objects`, updates both `src/crud_views/templates/crud_views/view_delete.content.html:8` and `src/crud_views/templates/crud_views/snippets/delete/related_objects.html:4`, removes the empty-tree shortcut in `GuardianDeleteRelatedObjectsMixin.cv_filter_related_objects` (`src/crud_views_guardian/lib/views.py:42-43`), and updates obsolete assertions in `tests/test1/test_delete.py:142-156` and `tests/test1/test_guardian_delete.py:45-73`.

### Concerns
None.

### Concrete Suggestions
None. All prior findings for `06.2-01` (`H01`, `A01–A05`, `A10`, `A18`, `A22`, `A26`) are closed with executable task specifications and verification commands.

### Risk Assessment
- **Risk Level:** Low.
- **Justification:** MRO ordering, template context gates, Django 4.2/6.0 compatibility, and core/Guardian/polymorphic delete coverage are all explicitly pinned to concrete source locations and verified in both supported Django environments.

---

## 06.2-02

### Summary
Plan `06.2-02` (`.planning/phases/06.2-request-authorization-and-write-integrity/06.2-02-PLAN.md:1-231`) unifies `cv_guardian_parent_permission=None` handling with parent resolution and independent `cv_action_enabled` checks (`AUTH-04`, `D-10`), supports FK own-child normalization while failing closed on unrelated or M2M object-only inputs (`H03`, `A25`), routes list/toolbar/card action-state checks through a shared `_cv_action_enabled_for_context` adapter (`A24`), preserves consumer mixin attributes via annotation-only declarations (`A23`), and enforces inactive-user denial across Guardian request and callable helper paths (`AUTH-05`, `D-05`, `D-11`).

### Strengths
- **Shared parent-permission key and FK own-child resolver (`H03`, `A25`):** `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-02-PLAN.md:107-110,115` centralizes parent permission-key resolution across `GuardianParentPermissionMixin._guardian_check_parent` (`src/crud_views_guardian/lib/mixins.py:212-245`) and `GuardianCreateViewPermissionRequired` (`src/crud_views_guardian/lib/views.py:123-206`), resolving the URL parent before skipping only the permission check when `perm_key is None` and always enforcing `cv_action_enabled(user, parent_obj)` on no-object child views. For `cv_has_access` / `cv_create_has_access`, it accepts a configured parent instance or resolves an FK child instance via `cls.cv_viewset.parent.get_attribute()`, while rejecting M2M own-child inference when `many_to_many_through_attribute` is set (`tests/test1/app/views.py:455-459`).
- **Context-state adapter across base, list fallback, `ContextButton`, and card actions (`H03`, `A24`):** `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-02-PLAN.md:113,142-145` introduces `CrudView._cv_action_enabled_for_context(user, obj)` in Task `02-01` and routes `GuardianQuerysetMixin.cv_get_context` (`src/crud_views_guardian/lib/mixins.py:155`) through it so a failed `cv_get_parent_object()` lookup returns `False` without passing `None` to custom `cv_action_enabled` hooks, then expands to `ContextButton` (`src/crud_views/lib/view/buttons.py:109,182,234,291`) and `CardListView` (`src/crud_views/lib/views/card.py:66,89`) in Task `02-03`.
- **Annotation-only parent mixin vocabulary (`A13`, `A23`):** `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-02-PLAN.md:111` declares `cv_guardian_accept_global_perms: bool` and `cv_guardian_anonymous_behavior: str` as annotations only on `GuardianParentPermissionMixin` (`src/crud_views_guardian/lib/mixins.py:173`), satisfying `CheckUnknownAttributes` (`W280`) without shadowing consumer subclasses or later mixins in `(GuardianParentPermissionMixin, CustomMixin, ...)` compositions.
- **Comprehensive inactive-actor denial (`AUTH-05`, `D-05`, `D-11`):** `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-02-PLAN.md:125-135` guards `GuardianParentPermissionMixin.dispatch`, `GuardianObjectPermissionMixin` (`has_permission`, `cv_has_access`), `GuardianQuerysetMixin` (`has_permission`, `get_queryset`), `GuardianCreateViewPermissionRequired` helpers, `_PermittedPks` (`src/crud_views_guardian/lib/views.py:61-69`), and `GuardianViewSet.get_objects_for_user` (`src/crud_views_guardian/lib/viewset.py:63-73`), verified with `AllowAllUsersModelBackend`.

### Concerns
None.

### Concrete Suggestions
None.

### Risk Assessment
- **Risk Level:** Low.
- **Justification:** Task file ownership stays within five files per task (`02-01` owns 5 files, `02-02` owns 4, `02-03` owns 3), MRO attribute resolution and late parent-lookup failure modes are explicitly tested, and test-local routes use strict `finally` teardown.

---

## 06.2-03

### Summary
Plan `06.2-03` (`.planning/phases/06.2-request-authorization-and-write-integrity/06.2-03-PLAN.md:1-181`) enforces target authorization before formset fragment rendering and validates root/parent/fragment coordinate chains (`AUTH-02`, `AUTH-07`, `D-09`, `D-12`, `D-13`). It preserves working persisted and unsaved nested row coordinates (including UUID models with defaults via `_state.adding` normalization) and explicitly bounds and defers the pre-existing non-first sibling child-declaration output-index mismatch (`A19`) to proposed Phase 6.3.

### Strengths
- **Target authorization before fragment rendering (`B2`, `D-09`):** `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-03-PLAN.md:85-97` updates `FormSetMixinBase.get` (`src/crud_views/lib/formsets/mixins.py:37-45`) so object views resolve `self.object = self.get_object()` (triggering `GuardianObjectPermissionMixin.get_object` permission and action-state checks at `src/crud_views_guardian/lib/mixins.py:50-58`) and create views set `self.object = None` before `get_template_html` evaluates any formset or `ModelChoiceField` queryset.
- **Declaration-aware coordinate and persisted FK ancestry validation (`A06`, `A07`, `A14`, `A15`):** `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-03-PLAN.md:100-115` validates `key_path`, ASCII `[0-9]+` indices (rejecting Unicode digits like `²` with `BadRequest` `400` instead of `ValueError` at `src/crud_views/lib/formsets/mixins.py:54-68`), root identity, parent-prefix depth, and persisted FK ancestry across integer (`Publisher` -> `Book` -> `BookNote`) and test-only UUID (`Author` -> `UUIDFragmentRow` -> `UUIDFragmentLeaf` in `tests/test1/app/models.py:13-25`) hierarchies, while normalizing `FormSet.init` prefix keys to `None` when `form.instance._state.adding` is true (`src/crud_views/lib/formsets/formsets.py:123`).
- **Explicit, well-reasoned boundary and deferral for `A19`:** `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-03-PLAN.md:81,108,166-176` accurately distinguishes input coordinate validation (mandatory for all declared sibling children) from the pre-existing `FormSets.get_template(..., index=0)` output prefix mismatch (`src/crud_views/lib/formsets/formsets.py:159,379`), characterizing both sibling declarations without weakening security gates or making false round-trip claims for non-first child declarations.

### Concerns
None.

### Concrete Suggestions
None.

### Risk Assessment
- **Risk Level:** Low.
- **Justification:** Browser-derived positive payloads, unsaved UUID default instances, and forged-ancestry negatives are thoroughly specified and isolated within test-only models and fixtures.

---

## 06.2-04

### Summary
Plan `06.2-04` (`.planning/phases/06.2-request-authorization-and-write-integrity/06.2-04-PLAN.md:1-180`) settles Guardian global-permission configuration (`AUTH-06`, `AUTH-07`, `D-03`–`D-06`) by atomically removing the inert `GuardianViewSet.cv_guardian_accept_global_perms` field with a targeted `mode="before"` validator diagnostic, keeping `GuardianViewSet.get_objects_for_user` strict, and updating `GuardianManageView` to display per-view effective global-fallback policy and applicability alongside the strict helper policy.

### Strengths
- **Atomic field removal and `Mapping`-guarded validator (`A09`, `A12`):** `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-04-PLAN.md:86-99` removes `cv_guardian_accept_global_perms` from `GuardianViewSet` (`src/crud_views_guardian/lib/viewset.py:23`) and updates `GuardianManageView.get_context_data` (`src/crud_views_guardian/lib/views.py:228-233`), `src/crud_views_guardian/templates/crud_views/snippets/guardian/config_table.html:16-18`, and `tests/test1/test_guardian.py` in the same task so manage rendering never breaks between commits. The `mode="before"` validator checks `isinstance(data, collections.abc.Mapping)` before inspecting keys so `model_validate` and non-mapping inputs preserve standard Pydantic validation behavior without raising `TypeError` or leaving partial registrations in `_REGISTRY`.
- **Truthful per-view applicability and cached manage-settings testing (`A17`, `A20`):** `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-04-PLAN.md:101-115` projects per-view effective `cv_guardian_accept_global_perms` and applicability in `GuardianManageView.get_view_data` (`src/crud_views_guardian/lib/views.py:270-276`), marking plain views, manage itself, top-level create, and parent-only views with resolved parent permission `None` as not applicable while keeping object/queryset views applicable. It also patches the cached `crud_views.lib.settings.crud_views_settings` singleton (`manage_views_enabled` and `manage_group`) via `monkeypatch.setattr` so group-gated `403`/`302` negative controls are genuinely exercised.
- **Explicit preservation of flagged `AUTH-06` classifier assumption:** `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-04-PLAN.md:80,160-163` preserves the unresolved `AUTH-06/unclassified` assumption transparently for the Phase 7 handoff.

### Concerns
None.

### Concrete Suggestions
None.

### Risk Assessment
- **Risk Level:** Low.
- **Justification:** `06.2-04` touches only Guardian ViewSet/manage files and `tests/test1/test_guardian*.py`, which are completely disjoint from Wave 3 sibling `06.2-03`.

---

## 06.2-05

### Summary
Plan `06.2-05` (`.planning/phases/06.2-request-authorization-and-write-integrity/06.2-05-PLAN.md:1-224`) replays the full direct-request actor matrix (`05-01`) and six native template overrides (`05-02`) (`AUTH-07` and `AUTH-01`–`AUTH-06`, `D-12`–`D-14`), verifying server-side enforcement, exact HTTP status codes, storage/hook invariants, FK child-page create control agreement (`H03`, `A25`), and library-owned context filtering independently of presentation.

### Strengths
- **Deterministic status, storage, and hook oracle (`A10`, `A20`):** `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-05-PLAN.md:65-109,116-130` specifies single expected status codes and storage/hook outcomes for every actor/route/method cell, distinguishing active top-level Guardian `DELETE` (`405` before `get_object`) from core `DELETE` (`403`/`404` when permission/state/lookup fails before method selection, `405` when granted on an existing enabled target) and nested parent-gate denials (`403`/`404`), and patching the `crud_views_settings` singleton for manage-mode tests.
- **End-to-end FK child-page create control and native-template verification (`H03`, `A25`):** `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-05-PLAN.md:99-101,110,132-146` tests reachable FK child `detail`/`update`/`delete` pages and card rows where `cv_context_has_permission:"create"` reflects parent permission while `cv_context_button` / card actions and direct `GET`/`POST` routes enforce both parent permission and parent `cv_action_enabled`, scoped accurately to FK nesting per `A25`. Task `05-02` overrides all six native template seams (`view_list.content.html`, `tags/card.html`, `tags/button/action.html`, `view_guardian_manage.html`, `tags/alert.html`, `formsets/formset.html`) via a `locmem` loader to prove context safety without template-level permission logic while preserving Phase 6/6.1 form-button and cancel-link contracts.

### Concerns
None.

### Concrete Suggestions
None.

### Risk Assessment
- **Risk Level:** Low.
- **Justification:** Test-only wave with explicit `finally` cleanup of `_REGISTRY`, `_VOCAB_CACHE`, `ROOT_URLCONF`, URL caches, `TEMPLATES`, and `crud_views_settings`.

---

## 06.2-06

### Summary
Plan `06.2-06` (`.planning/phases/06.2-request-authorization-and-write-integrity/06.2-06-PLAN.md:1-219`) updates canonical reference documentation (`06-01`), pairs `CHANGELOG.md` `### Breaking` entries with `docs/migrating-1.0.md` and `docs/reference/theme.md` custom-template guidance (`06-02`), and executes the full supported Django 6.0 and 4.2 verification suites plus `mkdocs build --strict` to record `06.2-ACCEPTANCE.md` and the Phase 7 stability handoff (`06-03`) (`AUTH-01`–`AUTH-07`, `D-13`, `D-14`).

### Strengths
- **Complete contract and boundary documentation (`H03`, `A16`, `A18`, `A19`, `A21`, `A25`):** `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-06-PLAN.md:90-124` updates `docs/reference/guardian.md`, `docs/reference/delete_view.md`, `docs/reference/formsets.md`, `docs/reference/context_buttons.md`, `docs/faq.md`, `docs/reference/theme.md`, `docs/migrating-1.0.md`, and `CHANGELOG.md`. It covers `405` on inherited `DELETE` (and `Allow`/`OPTIONS` omitting `DELETE`), `has_protected_objects` in outer and inner delete templates, custom `cv_filter_related_objects` responsibilities and per-view global fallback on related protected labels (`A21`), FK own-child vs M2M fail-closed helper boundaries and deferred route-aware M2M controls (`A25`), the `A19` non-first child fragment output-index limitation, and places new theme guidance in a standalone `##` section in `docs/reference/theme.md` so existing code-fence and heading-anchor tests (`test_alerts.py`, `test_form_button_docs.py`, `test_label_mode_docs.py`, `test_pagination_docs.py`) continue to pass.
- **Rigorous supported-version integration and honest baseline comparison (`A11`, `A22`–`A26`):** `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-06-PLAN.md:86,126-140` runs all existing and new test modules plus full `tests/test1` across both `.nox/crispy_floor-3-12-django-6-0` and `.nox/crispy_floor-3-12-django-4-2` (which collects `tests/test1/test_polymorphic.py` including `A26`'s new regression), compares against the measured pre-fix baselines (5459 passed on Django 4.2.30; 5460 passed on Django 6.0.9), and hands off the complete contract and limitation inventory (including `A19`, `A25`, and the flagged `AUTH-06/unclassified` assumption) to Phase 7.

### Concerns
None.

### Concrete Suggestions
None.

### Risk Assessment
- **Risk Level:** Low.
- **Justification:** Documentation fence/anchor constraints are guarded by automated doc tests and `mkdocs build --strict`, and full-suite verification is anchored to measured pre-fix baselines on both supported cached Django environments.

---

## Prior-Item Closure Ledger

| Item | Cycle 5 Status | Verification & Evidence |
| --- | --- | --- |
| **A26** — Registered polymorphic `DELETE` evidence | **CLOSED — Explicit Reviewer Sign-Off** | `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-01-PLAN.md:15,28,54-55,129-143,222-232` explicitly owns `tests/test1/test_polymorphic.py` in Task `01-03`, adds `test_delete_vehicle_http_delete_rejected` against `/vehicle/{pk}/delete/` (`VehicleDeleteView` at `tests/test1/app/views.py:579-581`, inheriting `PolymorphicDeleteViewPermissionRequired` at `src/crud_views_polymorphic/lib/delete.py:9-10`), asserts `405` and `DELETE` absent from `Allow`, verifies unchanged `Car` and `Vehicle.objects.non_polymorphic()` storage (`tests/test1/app/models.py:148-159`), retains `test_delete_vehicle` (`tests/test1/test_polymorphic.py:163-175`) `GET=200` and validated `POST=302` positive controls, runs focused `-k delete` commands under both Django 6.0 and 4.2 (`06.2-01-PLAN.md:140`), and syncs `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-VALIDATION.md:35,208-214`. |
| **A22–A25** | **CLOSED / DEFERRED PRESERVED — No Regression** | `A22` cooperative `_DeleteMethodGuardMixin` (`06.2-01-PLAN.md:91,103-105,135`), `A23` annotation-only parent-mixin declarations (`06.2-02-PLAN.md:111`), `A24` shared `_cv_action_enabled_for_context` adapter and list fallback (`06.2-02-PLAN.md:113,142`), and `A25` FK-only own-child boundary + explicit deferral of route-aware M2M own-child controls (`06.2-02-PLAN.md:109,115,226`; `06.2-05-PLAN.md:110,219`; `06.2-06-PLAN.md:97,115,214`) remain intact. |
| **H01–H03, A01–A21** | **CLOSED / DEFERRED PRESERVED — No Regression** | All prior closures (`H01`–`H03`, `A01`–`A18`, `A20`–`A21`), `A19`'s reasoned deferral of non-first sibling child-declaration output-index repair to proposed Phase 6.3 (`06.2-03-PLAN.md:81,108,176`; `06.2-06-PLAN.md:101,133,201`), and the flagged `AUTH-06/unclassified` assumption (`06.2-04-PLAN.md:80,163`; `06.2-06-PLAN.md:131,133`) remain intact without regression. |

## Deduplicated List of Genuinely Unresolved Plan Concerns

None. All HIGH, MEDIUM, and LOW plan concerns are resolved (`current_high=0`, `current_actionable=0`).
