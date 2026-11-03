## 06.2-01

### Summary
Plan `06.2-01` (`06.2-01-PLAN.md:1–220`) closes the inherited HTTP `DELETE` bypass (AUTH-01 / B1) and filters unauthorized protected-object labels while preserving an independent blocked-deletion notice (AUTH-03 / B3) and existing `POST` validation/protection/transaction semantics (AUTH-07). In revision `e385113`, Task `01-01` replaces the `delete()` method override with a private cooperative `_DeleteMethodGuardMixin` placed after `CrudView` and before `generic.DeleteView`, paired with `DeleteView._allowed_methods()` filtering and dual Django 6.0 / 4.2 verification (`06.2-01-PLAN.md:88, 100–106, 132, 210`).

### Strengths
- **Cooperative `DELETE` dispatch guard avoids Django 4.2 `DeleteViewCustomDeleteWarning` while preserving MRO gates and `Vary` decoration (closes A22):** In Django 4.2, `BaseDeleteView.__init__` (`.nox/crispy_floor-3-12-django-4-2/lib/python3.12/site-packages/django/views/generic/edit.py:257–268`) warns whenever `self.__class__.delete is not DeletionMixin.delete`. By inserting `_DeleteMethodGuardMixin` between `CrudView` and `generic.DeleteView` (`src/crud_views/lib/views/delete.py:27`; `06.2-01-PLAN.md:88, 100–102`), `DeleteView.delete` remains identical to `DeletionMixin.delete`, while `GuardianParentPermissionMixin.dispatch` (`src/crud_views_guardian/lib/mixins.py:196–202`), `PermissionRequiredMixin.dispatch`, and `CrudView.dispatch` (`src/crud_views/lib/view/base.py:227–231`) still execute before `_DeleteMethodGuardMixin.dispatch` returns `self.http_method_not_allowed(request, *args, **kwargs)`.
- **Truthful method advertisement and subclass reinstatement protection (preserves A05/A18):** Overriding `DeleteView._allowed_methods()` to strip `"DELETE"` from `super()._allowed_methods()` (`06.2-01-PLAN.md:102, 132`) keeps `DELETE` out of both 405 `Allow` and `OPTIONS` responses even when a concrete subclass restores `"delete"` in `http_method_names`, while `_DeleteMethodGuardMixin.dispatch` prevents execution from reaching `View.dispatch`'s handler lookup.
- **Two-level template gate and single-pass permission filtering for protected previews (preserves H01/A01/A02/A04):** Capturing `has_protected_objects = bool(related.protected)` in `DeleteView.get_context_data` (`src/crud_views/lib/views/delete.py:179–185`) before `cv_filter_related_objects` and gating both `src/crud_views/templates/crud_views/view_delete.content.html:8` and `src/crud_views/templates/crud_views/snippets/delete/related_objects.html:4` (`06.2-01-PLAN.md:100, 116`) preserves the blocked notice when `related_summary` and filtered `protected_objects` are both empty, without re-filtering Guardian object grants through core model-level permissions.

### Concerns
None.

### Suggestions
None.

### Risk Assessment
**Low.** The MRO placement of `_DeleteMethodGuardMixin` after `CrudView` and before `generic.DeleteView` preserves existing authentication, parent, core permission/state, and modal `Vary` behavior while eliminating the Django 4.2 instantiation warning, verified directly under both `.nox/crispy_floor-3-12-django-6-0` and `.nox/crispy_floor-3-12-django-4-2` (`06.2-01-PLAN.md:105`).

---

## 06.2-02

### Summary
Plan `06.2-02` (`06.2-02-PLAN.md:1–231`) unifies `cv_guardian_parent_permission = None` handling and parent action-state enforcement across dispatch, callable helpers, and rendered create controls (AUTH-04 / B4, B6), and enforces inactive-user denial across all Guardian request and callable paths (AUTH-05 / B5). Revision `e385113` switches `GuardianParentPermissionMixin` attribute declarations to annotations only (A23), moves `CrudView._cv_action_enabled_for_context` into Task `02-01` and routes `GuardianQuerysetMixin.cv_get_context`'s list fallback through it (A24), and defines and tests the explicit FK-only own-child normalization boundary vs. M2M-through relations (A25) (`06.2-02-PLAN.md:27–29, 109–115, 139–145, 219–226`).

### Strengths
- **Annotation-only declarations on `GuardianParentPermissionMixin` preserve MRO inheritance and W280 vocabulary (closes A23):** In `src/crud_views_guardian/lib/views.py:24–32, 85–109`, `GuardianParentPermissionMixin` precedes `GuardianObjectPermissionMixin` and `GuardianQuerysetMixin`. Declaring `cv_guardian_accept_global_perms: bool` and `cv_guardian_anonymous_behavior: str` as annotations without default values (`06.2-02-PLAN.md:111`) registers both names in `_own_cv_annotations` / `_collect_cv_names` (`src/crud_views/lib/check.py:281–307`) so `CheckUnknownAttributes` (W280) does not warn on parent-only views, without placing default values in `GuardianParentPermissionMixin.__dict__` that would shadow custom object/queryset mixin attributes later in the MRO.
- **Unified context-state adapter covers `GuardianQuerysetMixin.cv_get_context` list fallback as well as toolbar/card callers (closes A24):** Moving `CrudView._cv_action_enabled_for_context` and `GuardianCreateViewPermissionRequired._cv_action_enabled_for_context` into Task `02-01` (`06.2-02-PLAN.md:104, 113`) and routing `src/crud_views_guardian/lib/mixins.py:155` through `target_cls._cv_action_enabled_for_context(user, parent_obj)` ensures that when `cv_get_parent_object()` catches `Http404` or `KeyError` (`mixins.py:147–153`), `_cv_action_enabled_for_context(user, None)` returns `False` without invoking a consumer's `cv_action_enabled(user, None)` hook, while passing the resolved `Publisher` on success. Task `02-03` (`06.2-02-PLAN.md:139–145`) then expands the same adapter to `ContextButton.get_context` (`src/crud_views/lib/view/buttons.py:109`), `ChildContextButton.get_context` (`buttons.py:234`), `SiblingContextButton.get_context` (`buttons.py:291`), and `CardListView.cv_get_card_action_data` (`src/crud_views/lib/views/card.py:66, 89`).
- **Explicit FK vs. M2M-through boundary in the parent-object resolver (closes A25, preserves H03):** `ParentViewSet` supports M2M nesting via `many_to_many_through_attribute` (`src/crud_views/lib/viewset/parentviewset.py:19–21`; `src/crud_views/lib/views/create.py:53–61`; `tests/test1/app/views.py:455–459`), where `getattr(genre, "publishers")` is a `ManyRelatedManager` rather than a unique parent instance. Accepting an explicit `parent_vs.model` instance first and rejecting own-child inference when `parent.many_to_many_through_attribute` is set (`06.2-02-PLAN.md:109, 115`) keeps explicit-parent calls and URL-bound M2M list/create routes working while failing closed on ambiguous object-only M2M child inputs.
- **Comprehensive inactive-user enforcement across dispatch and callable helpers (preserves B5 / D-11):** Task `02-02` (`06.2-02-PLAN.md:129`) guards `GuardianParentPermissionMixin.dispatch` (`src/crud_views_guardian/lib/mixins.py:196–202`), `GuardianObjectPermissionMixin` (`mixins.py:31–73`), `GuardianQuerysetMixin` (`mixins.py:98–170`), `GuardianCreateViewPermissionRequired` (`src/crud_views_guardian/lib/views.py:123–206`), `_PermittedPks` (`views.py:53–70`), and `GuardianViewSet.get_objects_for_user` (`src/crud_views_guardian/lib/viewset.py:63–73`) under `AllowAllUsersModelBackend`.

### Concerns
None.

### Suggestions
None.

### Risk Assessment
**Low.** Task file counts remain within the 5-file ceiling (`02-01`: 5 files, `02-02`: 4 files, `02-03`: 3 files), MRO attribute lookup and fallback state handling are verified by dedicated regressions, and route/registry/vocabulary teardown is enforced via `finally` blocks (`06.2-02-PLAN.md:98`).

---

## 06.2-03

### Summary
Plan `06.2-03` (`06.2-03-PLAN.md:1–181`) secures formset AJAX fragment requests by running target resolution and object/parent authorization in `FormSetMixinBase.get` before `get_template_html` renders choices, validates declared key paths, row indices, and persisted/unsaved FK ancestry chains, normalizes unsaved UUID-default instances in `FormSet.init`, and explicitly bounds/defers the pre-existing non-first child output-index mismatch (AUTH-02 / B2, A19).

### Strengths
- **Cooperative target authorization before fragment rendering (closes B2):** `FormSetMixinBase.get` (`src/crud_views/lib/formsets/mixins.py:37–45`) currently serves `?template=...` before `super().get()` calls `get_object()`. Initializing `self.object = self.get_object()` for object views (`self.object = None` for create views) before `self.get_template_html(request)` (`06.2-03-PLAN.md:41, 90`) ensures `GuardianObjectPermissionMixin.get_object` (`src/crud_views_guardian/lib/mixins.py:50–58`) enforces object permission and `cv_action_enabled` before any formset or `ModelChoiceField` is instantiated.
- **Declaration-aware coordinate validation and unsaved UUID prefix normalization (preserves A06/A07/A14/A15):** `FormSet.init` (`src/crud_views/lib/formsets/formsets.py:123`) formats `form.instance.pk` into `prefix_key`, which on unsaved models with `UUIDField(default=uuid.uuid4)` (`tests/test1/app/models.py:14`) is already a UUID when `form.instance._state.adding` is `True`. Normalizing `prefix_key` identity to `None` when `form.instance._state.adding` is `True` without mutating `form.instance.pk` (`06.2-03-PLAN.md:106`) aligns initial rendering with `FormSet.template` (`formsets.py:234`) and `formset.js`, while ASCII `[0-9]+` index parsing prevents Unicode digit bypasses (`num="²"`, `mixins.py:54`).
- **Clear A19 boundary for non-first sibling child declarations:** `06.2-03-PLAN.md:81, 108, 176` accurately distinguishes input ancestry validation from `FormSets.get_template`'s pre-existing `index=0` call (`src/crud_views/lib/formsets/formsets.py:379`), characterizing the output-index mismatch for proposed 6.3 while still enforcing authorization and ancestry validation across all declared paths.

### Concerns
None.

### Suggestions
None.

### Risk Assessment
**Low.** The plan preserves the wire protocol and `{html, rows}` response shape while closing unauthorized choice disclosure and forged coordinate traversal.

---

## 06.2-04

### Summary
Plan `06.2-04` (`06.2-04-PLAN.md:1–180`) atomically removes the inert `GuardianViewSet.cv_guardian_accept_global_perms` field (`src/crud_views_guardian/lib/viewset.py:23`) with a mapping-guarded `mode="before"` validator diagnostic, updates `GuardianManageView` (`src/crud_views_guardian/lib/views.py:209–276`) and `config_table.html` (`src/crud_views_guardian/templates/crud_views/snippets/guardian/config_table.html:16–18`) to report per-view effective global-permission policy and the strict `get_objects_for_user()` helper, and tests manage access modes via `monkeypatch.setattr` on the `crud_views_settings` singleton (AUTH-06 / B7, A09, A12, A17, A20).

### Strengths
- **Atomic removal of the field and its manage reader prevents intermediate breakage (preserves A09/A12):** Task `04-01` (`06.2-04-PLAN.md:88–92`) modifies `src/crud_views_guardian/lib/viewset.py:23`, `src/crud_views_guardian/lib/views.py:231`, `src/crud_views_guardian/templates/crud_views/snippets/guardian/config_table.html:16–18`, and `tests/test1/test_guardian.py:644–645` in one commit, and guards the `mode="before"` Pydantic validator with `isinstance(data, collections.abc.Mapping)` so `model_validate(existing_instance)` and non-mapping inputs retain standard Pydantic validation semantics.
- **Exact per-view applicability rules and singleton-patched manage gate tests (preserves A17/A20):** Task `04-02` (`06.2-04-PLAN.md:106–108`) uses Plan 02's shared parent permission-key resolver to classify `GuardianObjectPermissionMixin`/`GuardianQuerysetMixin` views and non-`None` parent-only views as applicable while marking plain views, `manage`, top-level `create`, and `None`-permission parent-only views as not applicable, and patches `crud_views_settings.manage_views_enabled` and `crud_views_settings.manage_group` directly (`src/crud_views/lib/views/manage.py:30–39`).

### Concerns
None.

### Suggestions
None.

### Risk Assessment
**Low.** Plans `06.2-03` and `06.2-04` share Wave 3 with completely disjoint `files_modified` sets (`06.2-03-PLAN.md:7–12` vs. `06.2-04-PLAN.md:7–13`). The `AUTH-06/unclassified` detector note remains explicitly flagged in `06.2-04-PLAN.md:80, 163`.

---

## 06.2-05

### Summary
Plan `06.2-05` (`06.2-05-PLAN.md:1–224`) replays the full direct-request actor matrix (`tests/test1/test_authorization_matrix.py`) and six native locmem template overrides (`tests/test1/test_authorization_templates.py`) after Waves 1–3 land (AUTH-07 / D-12–D-14). Revision `e385113` scopes the child-page own-child control/request agreement rows in the matrix to FK nesting per A25 while referencing `02-01`'s M2M fail-closed, explicit-parent, and URL-aware list/create coverage (`06.2-05-PLAN.md:110, 214, 219`).

### Strengths
- **Deterministic single-status actor/method/route matrix (preserves A10/A20/H03/A25):** The tables in `06.2-05-PLAN.md:69–106` pin exact status codes and side-effect boundaries for every actor and route, including the distinction between active top-level Guardian `DELETE` (405 via `_DeleteMethodGuardMixin.dispatch` before `get_object`) and core `DELETE` (where `PermissionRequiredMixin.dispatch` runs `has_permission()` / `cv_get_action_object()` before `_DeleteMethodGuardMixin.dispatch`, yielding 403/404 when ungranted/disabled/missing), FK child-page create control/filter/state agreement, and singleton-patched manage modes.
- **Six native template overrides verify server-owned context filtering (preserves D-12/D-14):** Task `05-02` (`06.2-05-PLAN.md:137–139`) exercises `crud_views/view_list.content.html`, `crud_views/tags/card.html`, `crud_views/tags/button/action.html`, `crud_views/view_guardian_manage.html`, `crud_views/tags/alert.html`, and `crud_views/formsets/formset.html` with `locmem.Loader` and `APP_DIRS=False`, verifying that unauthorized rows, choices, and protected labels never enter template context while `has_protected_objects` preserves the blocked alert.

### Concerns
None.

### Suggestions
None.

### Risk Assessment
**Low.** Test-only Wave 4 plan with strict fixture teardown of `_REGISTRY`, `_VOCAB_CACHE`, `ROOT_URLCONF`, URL caches, `crud_views_settings`, and `TEMPLATES` (`06.2-05-PLAN.md:108, 112`).

---

## 06.2-06

### Summary
Plan `06.2-06` (`06.2-06-PLAN.md:1–219`) updates canonical reference documentation, pairs `CHANGELOG.md` `### Breaking` entries with `docs/migrating-1.0.md` and `docs/reference/theme.md` guidance, and executes the final supported-version verification across Django 6.0 and Django 4.2 plus `mkdocs build --strict` to produce `06.2-VALIDATION.md` and `06.2-ACCEPTANCE.md` for Phase 7 (AUTH-01–AUTH-07). Revision `e385113` adds explicit FK vs. M2M-through child-create documentation, migration guidance, and handoff tracking for A22–A25 (`06.2-06-PLAN.md:95–97, 115, 133–134, 208–214`).

### Strengths
- **Complete documentation and migration coverage of the FK/M2M own-child boundary (closes A25 in docs):** Task `06-01` (`06.2-06-PLAN.md:95–97`) and Task `06-02` (`06.2-06-PLAN.md:115`) explicitly qualify `docs/reference/guardian.md`, `docs/reference/context_buttons.md`, `docs/faq.md`, `docs/migrating-1.0.md`, and `CHANGELOG.md` so that FK own-child parent resolution via `ParentViewSet.get_attribute()` is distinguished from M2M-through relations (`many_to_many_through_attribute`), where object-only helper/control calls fail closed while explicit-parent helper calls and URL-bound list/create routes remain supported.
- **Preservation of doc-extraction test invariants (preserves A16/A21):** Task `06-02` (`06.2-06-PLAN.md:117–120`) places new safe-context theme guidance in a standalone level-two section in `docs/reference/theme.md` outside the fence-counted sections (`Custom form-button templates`, `Cancel links in custom form-button templates`, `Custom alert frame`) and runs `tests/test1/test_alerts.py`, `tests/test1/test_form_button_docs.py`, `tests/test1/test_label_mode_docs.py`, `tests/test1/test_pagination_docs.py`, and `.venv/bin/mkdocs build --strict`.
- **Comprehensive dual-Django verification and transparent handoff ledger (closes A22–A25 handoff, preserves A11/A19/AUTH-06):** Task `06-03` (`06.2-06-PLAN.md:131–136`) runs all 17 targeted test modules and the full `tests/test1` suite on both `.nox/crispy_floor-3-12-django-6-0` and `.nox/crispy_floor-3-12-django-4-2`, compares results against the measured pre-fix baseline (`5459 passed` on Django 4.2.30 / `5460 passed` on Django 6.0.9), and records A22–A25, A19's deferred non-first child output-index limitation, and the flagged `AUTH-06/unclassified` assumption in `06.2-ACCEPTANCE.md`.

### Concerns
None.

### Suggestions
None.

### Risk Assessment
**Low.** Documentation and final verification tasks are tightly coupled to the executable tests in Plans 01–05 and existing doc-structure guard tests.

---

## Prior-Item Closure Ledger (Cycle 4 Verification of A22–A25 and Prior H01–H03 / A01–A21)

| Finding | Cycle 4 Status & Reviewer Sign-Off | Plan & Source Evidence |
| --- | --- | --- |
| **A22** (Django 4.2 `DeleteViewCustomDeleteWarning` on `delete()` override) | **CLOSED — Explicit Reviewer Sign-Off.** `06.2-01` replaces the `delete()` override with a private cooperative `_DeleteMethodGuardMixin` placed after `CrudView` and before `generic.DeleteView` (`src/crud_views/lib/views/delete.py:27`), plus `DeleteView._allowed_methods()` filtering `"DELETE"`. `DeleteView.delete` remains `DeletionMixin.delete` (no warning at `.nox/crispy_floor-3-12-django-4-2/lib/python3.12/site-packages/django/views/generic/edit.py:259`), prior auth/parent/core-permission gates and `CrudView.dispatch` modal `Vary` decoration (`src/crud_views/lib/view/base.py:227–231`) remain intact, subclass `"delete"` restoration in `http_method_names` is still rejected at dispatch with truthful 405/OPTIONS `Allow` headers, and `01-01` runs pytest on both Django 6.0 and 4.2 with `warnings.catch_warnings(record=True)`. | `06.2-01-PLAN.md:24, 88, 100–106, 132, 210`; `06.2-06-PLAN.md:133, 209` |
| **A23** (`GuardianParentPermissionMixin` default values shadowing consumer mixins) | **CLOSED — Explicit Reviewer Sign-Off.** `06.2-02` declares `cv_guardian_accept_global_perms: bool` and `cv_guardian_anonymous_behavior: str` on `GuardianParentPermissionMixin` (`src/crud_views_guardian/lib/mixins.py:173`) as annotations ONLY without assigned default values. `_own_cv_annotations` / `_collect_cv_names` (`src/crud_views/lib/check.py:281–307`) still collect them for W280, while later mixins in `(GuardianParentPermissionMixin, CustomObjectOrQuerysetMixin, ...)` (`src/crud_views_guardian/lib/views.py:24–32, 85–109`) are not shadowed. `02-01` pins both W280 and `global=True` / `anonymous="404"` composition regressions. | `06.2-02-PLAN.md:28, 111, 116, 219`; `06.2-06-PLAN.md:133, 209` |
| **A24** (`GuardianQuerysetMixin.cv_get_context` list fallback calling `cv_action_enabled(user, None)`) | **CLOSED — Explicit Reviewer Sign-Off.** `06.2-02` moves `CrudView._cv_action_enabled_for_context` (`src/crud_views/lib/view/base.py:707`) and `GuardianCreateViewPermissionRequired._cv_action_enabled_for_context` (`src/crud_views_guardian/lib/views.py:112`) into Task `02-01`, and routes `GuardianQuerysetMixin.cv_get_context` (`src/crud_views_guardian/lib/mixins.py:155`) through `target_cls._cv_action_enabled_for_context(user, parent_obj)`. Late `Http404`/`KeyError` fallback failure yields `cv_access=False` and `cv_action_enabled=False` without invoking custom `cv_action_enabled(user, None)`, while normal list rendering passes the resolved `Publisher`. Task `02-03` expands the adapter to `buttons.py` and `card.py`. | `06.2-02-PLAN.md:29, 104, 113, 116, 139–142, 220`; `06.2-06-PLAN.md:133, 209` |
| **A25** (FK vs. M2M-through own-child boundary in create helpers, controls, and docs) | **CLOSED — Explicit Reviewer Sign-Off.** `06.2-02` accepts an explicit `parent_vs.model` instance first in the private parent-object resolver, rejects own-child inference when `parent.many_to_many_through_attribute` is set (`src/crud_views/lib/viewset/parentviewset.py:19–21`; `tests/test1/app/views.py:458`), and resolves `parent.get_attribute()` only for FK child instances. `02-01` tests multi-publisher `Genre` own-child denial alongside explicit-`Publisher` helper positives and URL-bound `Genre` list/create GET/POST positives. Plans `02`, `05`, and `06` explicitly document the FK/M2M boundary and defer route-aware M2M own-child controls with clear rationale. | `06.2-02-PLAN.md:27, 109, 115–116, 141–145, 221, 226`; `06.2-05-PLAN.md:110, 214, 219`; `06.2-06-PLAN.md:95–97, 115, 133–134, 208, 214` |
| **H01–H03, A01–A21** (Prior cycle closures and scoped deferrals) | **PRESERVED — No Regression.** All previously closed items (including H01 two-template preview gate, H02/H03 FK own-child resolution and independent context-state adapter, A18 `_allowed_methods` + monkeypatched concrete subclass teardown, A19 explicit non-first child fragment output-index deferral to proposed 6.3, A20 `crud_views_settings` singleton monkeypatching, and A21 custom `cv_filter_related_objects` and delete-view related-label global-fallback documentation) remain intact and unregressed in `e385113`. | `06.2-01-PLAN.md`–`06.2-06-PLAN.md`; `06.2-VALIDATION.md:195–207` |

## Unresolved Plan Concerns

None. All prior items (**H01–H03**, **A01–A25**) are resolved by executable plan actions or explicit scoped deferrals, and no new HIGH, MEDIUM, or LOW plan defects were found.
