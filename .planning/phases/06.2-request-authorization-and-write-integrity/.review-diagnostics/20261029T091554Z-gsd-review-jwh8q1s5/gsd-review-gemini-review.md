## 06.2-01

### Summary
Plan `06.2-01` (`.planning/phases/06.2-request-authorization-and-write-integrity/06.2-01-PLAN.md:1-191`) closes the inherited HTTP `DELETE` bypass (`B1`, `AUTH-01`) across core and Guardian delete views by restricting `DeleteView.http_method_names` and overriding `DeleteView.delete()` to return `http_method_not_allowed`, and secures protected related-object previews (`B3`, `AUTH-03`) by capturing `has_protected_objects` before `cv_filter_related_objects`, filtering `related.protected` in core and Guardian hooks, and gating both the outer template include and inner alert on `has_protected_objects`.

### Strengths
- **Complete closure of `H01` (outer preview include gate):** `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-01-PLAN.md:10,43-44,54-56,95-99` adds `src/crud_views/templates/crud_views/view_delete.content.html` to `files_modified`, `artifacts`, `key_links`, and Task `01-01`. Because `DeleteView.cv_get_related_objects()` (`src/crud_views/lib/views/delete.py:88-96`) excludes the root model from `related.summary`, a protected-only `Publisher` with an unpermitted `Contract` (`tests/test1/app/models.py:72-74`) yields `related_summary == {}` and `protected_objects == []`. Updating both `src/crud_views/templates/crud_views/view_delete.content.html:8` and `src/crud_views/templates/crud_views/snippets/delete/related_objects.html:4` to check `has_protected_objects` ensures `{% cv_alert "error" ... items=protected_objects %}` still renders the generic blocked heading via `TEXT_BODY` (`src/crud_views/lib/messages.py:42-44`).
- **Defense-in-depth against `DeletionMixin.delete()` (`A05`) and clean hook separation (`A04`):** Task `01-01` (`.planning/phases/06.2-request-authorization-and-write-integrity/06.2-01-PLAN.md:99`) both removes `"delete"` from `DeleteView.http_method_names` and overrides `delete()` to return `self.http_method_not_allowed(...)` without loading or deleting an object, preventing subclasses that restore `"delete"` in `http_method_names` from reaching Django's `DeletionMixin.delete()`. Filtering `related.protected` inside `DeleteView.cv_filter_related_objects()` (`src/crud_views/lib/views/delete.py:147-172`) and `GuardianDeleteRelatedObjectsMixin.cv_filter_related_objects()` (`src/crud_views_guardian/lib/views.py:39-50`, removing the empty-tree shortcut at `:42-43`) while `get_context_data()` (`src/crud_views/lib/views/delete.py:179-185`) consumes the hook output directly prevents a second core model-permission filter from stripping valid Guardian object grants.
- **Explicit protection semantics (`A01`), obsolete test replacement (`A02`), and pre-handler ordering (`A10`):** Tasks `01-01`, `01-02`, and `01-03` (`.planning/phases/06.2-request-authorization-and-write-integrity/06.2-01-PLAN.md:99,113,127`) separately pin `cv_check_delete_protection()` POST responses (`200` full-page / `422` modal at `src/crud_views/lib/views/delete.py:206-214`) vs confirmed database `PROTECT` raising `ProtectedError` (`src/crud_views/lib/views/delete.py:221-222`), replace the three obsolete characterization assertions in `tests/test1/test_delete.py:142-155` and `tests/test1/test_guardian_delete.py:45-73`, and preserve `CrudViewProcessFormMixin.cv_form_valid_process()` (`src/crud_views/lib/views/mixins.py:48-57`).

### Concerns
None.

### Suggestions
- In `src/crud_views/templates/crud_views/view_delete.content.html:8` and `src/crud_views/templates/crud_views/snippets/delete/related_objects.html:4`, consider checking `has_protected_objects or protected_objects` so direct template renders in isolated tests that pass only `protected_objects` continue to render the alert alongside view-driven `has_protected_objects` contexts.

### Risk Assessment
- **Low risk:** The plan's method restriction, hook boundary, and template context changes are tightly scoped to `DeleteView`, `GuardianDeleteRelatedObjectsMixin`, and the two delete templates, with explicit regression coverage for full-page, modal, and transaction rollback paths.

---

## 06.2-02

### Summary
Plan `06.2-02` (`.planning/phases/06.2-request-authorization-and-write-integrity/06.2-02-PLAN.md:1-164`) fixes `B4`/`B6` (`AUTH-04`) by resolving the URL parent and enforcing `cv_action_enabled` even when the effective parent permission key is `None`, unifies parent permission-key resolution across dispatch and create access helpers, resolves `H02` by making `GuardianCreateViewPermissionRequired.cv_has_access` fail closed (`False`) on wrong-model objects, and fixes `B5` (`AUTH-05`) by denying authenticated inactive actors across Guardian dispatch, `has_permission`, queryset, and callable helper paths.

### Strengths
- **Complete closure of `H02` (wrong-type helper contract and test ownership):** `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-02-PLAN.md:11,37-38,86,89,150,159` adds `tests/test1/test_guardian.py` to `files_modified` and Task `02-01`, explicitly updates `test_create_cv_has_access_child_wrong_type_obj` (`tests/test1/test_guardian.py:337-341`) from `True` to `False`, and updates the helper docstrings at `src/crud_views_guardian/lib/views.py:181-183,206` while keeping `cv_has_access(user, None) is False` (`src/crud_views_guardian/lib/views.py:190-191`) so `GuardianQuerysetMixin.cv_get_context()` (`src/crud_views_guardian/lib/mixins.py:130-156`) continues to resolve the URL parent via `cv_create_has_access`.
- **Unified parent-`None` resolution and action-state enforcement (`B4`/`B6`, `A13`):** Task `02-01` (`.planning/phases/06.2-request-authorization-and-write-integrity/06.2-02-PLAN.md:89`) shares a class-callable parent-permission key resolver across `GuardianParentPermissionMixin._guardian_check_parent()` (`src/crud_views_guardian/lib/mixins.py:212-245`), `cv_create_has_access()` (`src/crud_views_guardian/lib/views.py:146-148`), and `cv_has_access()` (`src/crud_views_guardian/lib/views.py:195-197`). Resolving `parent_obj = get_object_or_404(...)` before checking `if perm_key is not None:` ensures missing parents `404` and `cv_action_enabled(user, parent_obj)` at `src/crud_views_guardian/lib/mixins.py:244` always runs for no-object child views. Declaring `cv_guardian_accept_global_perms = False` and `cv_guardian_anonymous_behavior = "redirect"` on `GuardianParentPermissionMixin` (`src/crud_views_guardian/lib/mixins.py:173`) satisfies `CheckUnknownAttributes` (`src/crud_views/lib/check.py:364-374`).
- **Comprehensive inactive-user denial (`B5`) and wave-2 route isolation (`A08`):** Task `02-02` (`.planning/phases/06.2-request-authorization-and-write-integrity/06.2-02-PLAN.md:80,103`) denies `not request.user.is_active` with `PermissionDenied` in `GuardianParentPermissionMixin.dispatch()` (`src/crud_views_guardian/lib/mixins.py:196-202`, which also protects top-level `GuardianCreateViewPermissionRequired` before `PermissionRequiredMixin.has_permission()` can consult `AllowAllUsersModelBackend`), in `GuardianObjectPermissionMixin.has_permission()` (`:31-38`) and `GuardianQuerysetMixin.has_permission()` (`:98-105`), and across callable helpers (`GuardianViewSet.get_objects_for_user` at `src/crud_views_guardian/lib/viewset.py:63-73`, `_PermittedPks` at `src/crud_views_guardian/lib/views.py:53-69`, `GuardianQuerysetMixin.get_queryset` at `src/crud_views_guardian/lib/mixins.py:159-170`, and `cv_has_access` / `cv_create_has_access`). Defining isolated action and formset routes directly in `test_guardian_inactive.py` with full `_REGISTRY`, `_VOCAB_CACHE`, `ROOT_URLCONF`, and `clear_url_caches()` teardown avoids any forward dependency on Wave 3.

### Concerns
None.

### Suggestions
- In `GuardianObjectPermissionMixin.cv_has_access`, `GuardianQuerysetMixin.cv_has_access`, and `GuardianCreateViewPermissionRequired.cv_has_access` / `cv_create_has_access` (`src/crud_views_guardian/lib/mixins.py:61,108`, `src/crud_views_guardian/lib/views.py:123,158`), guard `if not getattr(user, "is_authenticated", False) or not getattr(user, "is_active", False): return False` at the top of each callable helper so `AllowAllUsersModelBackend`'s `user.has_perm()` cannot grant access to inactive superusers or global-perm holders when `cv_guardian_accept_global_perms=True`.

### Risk Assessment
- **Low risk:** All modified paths are confined to `crud_views_guardian` and its test modules, and the fixture cleanup contract (`.planning/phases/06.2-request-authorization-and-write-integrity/06.2-02-PLAN.md:80`) prevents global `_REGISTRY` (`src/crud_views/lib/viewset/__init__.py:43,151`) or `_VOCAB_CACHE` (`src/crud_views/lib/check.py:321`) leakage.

---

## 06.2-03

### Summary
Plan `06.2-03` (`.planning/phases/06.2-request-authorization-and-write-integrity/06.2-03-PLAN.md:1-165`) fixes `B2` (`AUTH-02`) by authorizing the target object in `FormSetMixinBase.get()` before serving AJAX formset fragments, validating declaration/root/parent-prefix/FK ancestry coordinates before rendering, normalizing unsaved UUID-default model instances (`_state.adding`) to the `"None"` prefix sentinel in `FormSet.init()`, and testing persisted UUID FK ancestry via two test-only models in `tests/test1/app/models.py`.

### Strengths
- **Cooperative target authorization before fragment rendering (`B2`):** Task `03-01` (`.planning/phases/06.2-request-authorization-and-write-integrity/06.2-03-PLAN.md:88`) initializes `self.object = self.get_object() if self.cv_object else None` (matching `CrudViewProcessFormMixin.post` at `src/crud_views/lib/views/mixins.py:37`) in `FormSetMixinBase.get()` (`src/crud_views/lib/formsets/mixins.py:37-45`) before calling `self.get_template_html(request)`. For `GuardianUpdateViewPermissionRequired` (`src/crud_views_guardian/lib/views.py:30-33`), `self.get_object()` runs `GuardianObjectPermissionMixin.get_object()` (`src/crud_views_guardian/lib/mixins.py:50-58`), enforcing parent-filtered queryset lookup (`404` on missing/wrong-parent PK), per-object permission (`403`), and `cv_action_enabled` (`403`) before any inline `ModelChoiceField` queryset can be evaluated.
- **Browser-faithful coordinate grammar (`A06`), ASCII index validation (`A15`), and unsaved UUID normalization (`A14`):** `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-03-PLAN.md:79,102-104` aligns validation with `XForm.add()` in `src/crud_views/static/crud_views/js/formset.js:318-323` and `XFormSet.parent_prefix_key` in `src/crud_views/lib/formsets/render_tree.py:135-138` (which sends `formset_parent_prefix_key=""` at level 0). Normalizing `FormSet.init()` (`src/crud_views/lib/formsets/formsets.py:123`) to emit `None` in `prefix_key` when `form.instance._state.adding` is `True` prevents `Author.id = models.UUIDField(primary_key=True, default=uuid.uuid4)` (`tests/test1/app/models.py:14`) from generating a random unpersisted UUID prefix that would mismatch `FormSet.template()` (`src/crud_views/lib/formsets/formsets.py:189,234`) and bound POST validation. Validating `num` and prefix indices with ASCII `^[0-9]+$` and guarded `int` conversion closes the `.isdigit()` vs `int()` mismatch (`src/crud_views/lib/formsets/mixins.py:54,68`) for inputs like `num=²`.
- **Executable persisted UUID ancestry fixture (`A07`):** Adding `UUIDFragmentRow` and `UUIDFragmentLeaf` to `tests/test1/app/models.py` (`.planning/phases/06.2-request-authorization-and-write-integrity/06.2-03-PLAN.md:12,36-37,104`) allows `pytest-django` to create their SQLite tables automatically and tests real multi-level UUID FK ancestry (`Author -> UUIDFragmentRow -> UUIDFragmentLeaf`) without touching production schemas.

### Concerns
None.

### Suggestions
- In `FormSetMixinBase.get()` (`src/crud_views/lib/formsets/mixins.py:41-42`), dispatch to the fragment path whenever `"template" in request.GET` (i.e. `template is not None` rather than truthy `if template:`) so an explicit empty query parameter `?template=` enters `get_template_html()` and raises `BadRequest` (`400`) as specified by `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-03-PLAN.md:102` ("Unknown/empty key paths ... produce BadRequest before rendering") instead of falling through to `super().get()`.

### Risk Assessment
- **Low-to-Medium risk:** Coordinate parsing across multi-level persisted and unsaved chains (`FormSet.PK.INT` and `FormSet.PK.UUID` in `src/crud_views/lib/formsets/formsets.py:27-30`) is the most intricate logic in Phase 6.2, but the explicit browser-payload positive matrix (`.planning/phases/06.2-request-authorization-and-write-integrity/06.2-03-PLAN.md:79`) and bound POST round-trip assertions mitigate regression risk.

---

## 06.2-04

### Summary
Plan `06.2-04` (`.planning/phases/06.2-request-authorization-and-write-integrity/06.2-04-PLAN.md:1-166`) resolves `B7` (`AUTH-06`) by atomically removing the inert `GuardianViewSet.cv_guardian_accept_global_perms` field with a Mapping-guarded `mode="before"` validator diagnostic, updating `GuardianManageView` and its templates in the same commit (`A09`), and projecting each registered view's effective global-permission fallback policy and applicability alongside the independently strict `GuardianViewSet.get_objects_for_user()` helper.

### Strengths
- **Atomic field removal and manage reader update (`A09`) with safe `mode="before"` validation (`A12`):** Task `04-01` (`.planning/phases/06.2-request-authorization-and-write-integrity/06.2-04-PLAN.md:87-98`) modifies `src/crud_views_guardian/lib/viewset.py:23`, `src/crud_views_guardian/lib/views.py:231`, `src/crud_views_guardian/templates/crud_views/snippets/guardian/config_table.html:16-18`, and `tests/test1/test_guardian.py:636-649` in a single atomic task so `GuardianManageView` never raises `AttributeError` between tasks. Guarding the `@model_validator(mode="before")` check with `isinstance(data, collections.abc.Mapping)` (following the pattern in `src/crud_views/lib/formsets/formsets.py:270-277` while avoiding unguarded `.get()` on non-mappings) ensures `GuardianViewSet(model=..., name=..., cv_guardian_accept_global_perms=...)` fails before `ViewSet.register` (`src/crud_views/lib/viewset/__init__.py:125-158`) mutates `_REGISTRY`, while `model_validate(existing_instance)` and non-mapping inputs keep standard Pydantic behavior.
- **Exact per-view applicability rules (`A17`):** Task `04-02` (`.planning/phases/06.2-request-authorization-and-write-integrity/06.2-04-PLAN.md:26,106`) cleanly defines applicability in `GuardianManageView.get_view_data()` (`src/crud_views_guardian/lib/views.py:270-276`): views with `GuardianObjectPermissionMixin` or `GuardianQuerysetMixin` are always applicable; parent-only views (`GuardianParentPermissionMixin` without object/queryset mixins, such as `GuardianCreateViewPermissionRequired` at `src/crud_views_guardian/lib/views.py:112`) are applicable only when `cv_viewset.parent is not None` and Plan 02's shared parent-permission resolver returns a non-`None` key; plain views, `manage` itself, top-level create, and parent-only `None`-permission views report not applicable.
- **Explicit tracking of the `AUTH-06/unclassified` assumption:** `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-04-PLAN.md:80,161` preserves the exact unclassified detector status for `AUTH-06` and carries it forward to `06.2-ACCEPTANCE.md` rather than silently dismissing it.

### Concerns
None.

### Suggestions
- When updating `tests/test1/test_guardian.py:636-657` in Task `04-01`, verify that `test_guardian_manage_config_renders_in_an_alert` (`tests/test1/test_guardian.py:652-656`) still matches `<table class="table table-striped mb-0">` and `"cv_guardian_parent_permission"` in `src/crud_views_guardian/templates/crud_views/snippets/guardian/config_table.html`.

### Risk Assessment
- **Low risk:** Disjoint file ownership from Plan 03 allows Wave 3 parallel execution if desired, and combining the field removal with the manage reader update in Task `04-01` eliminates intermediate breakage.

---

## 06.2-05

### Summary
Plan `06.2-05` (`.planning/phases/06.2-request-authorization-and-write-integrity/06.2-05-PLAN.md:1-188`) provides the Wave 4 post-fix verification suite (`AUTH-07`, `D-12`–`D-14`): `tests/test1/test_authorization_matrix.py` replays the direct-request actor × route × method matrix with exact status, storage, and hook assertions, and `tests/test1/test_authorization_templates.py` proves that native template overrides across all six seams receive only library-filtered context and never leak unauthorized rows, choices, or protected labels.

### Strengths
- **Complete, unambiguous status and storage oracle (`A10`):** `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-05-PLAN.md:64-103` defines two exhaustive tables covering anonymous (`redirect` / `403` / `404`), no-grant, revoked, object-granted, group-granted, global-only (strict vs `cv_guardian_accept_global_perms=True`), active superuser, and permissive-backend inactive actors (`AllowAllUsersModelBackend`), and pins exact method-ordering differences between core `CrudViewPermissionRequiredMixin.has_permission()` (`src/crud_views/lib/view/base.py:900-910`, where missing permission/disabled state/missing object return `403`/`403`/`404` before `View.dispatch` method selection) and top-level Guardian views (`src/crud_views_guardian/lib/mixins.py:31-38,196-202`, where active authenticated `DELETE` reaches `View.dispatch` and returns `405` before `get_object()`).
- **Post-fix evidence discipline (`A03`) and complete fixture hygiene (`A08`):** Tasks `05-01` and `05-02` (`.planning/phases/06.2-request-authorization-and-write-integrity/06.2-05-PLAN.md:105,114-115,128-131`) explicitly treat Wave 4 as post-fix replay/preservation verification referencing Waves 1–3 defect reproductions, and enforce `finally` restoration of `_REGISTRY`, `_VOCAB_CACHE`, `ROOT_URLCONF`, URL caches, and `settings.TEMPLATES`.

### Concerns
None.

### Suggestions
- In `tests/test1/test_authorization_templates.py` (Task `05-02`, `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-05-PLAN.md:128`), ensure the test-local list view route subclasses `GuardianListViewPermissionRequired` / `ListViewPermissionRequired` directly (`src/crud_views/lib/views/list.py:18-20`, which renders `crud_views/view_list.content.html`) rather than mixing in `ListViewTableMixin` (`src/crud_views/lib/views/mixins.py:288-289`, which switches `cv_content_template` to `crud_views/view_list_table.content.html`), so the `crud_views/view_list.content.html` locmem override and its sentinel are exercised directly.

### Risk Assessment
- **Low risk:** Test-only wave with no production code modifications and strict fixture isolation.

---

## 06.2-06

### Summary
Plan `06.2-06` (`.planning/phases/06.2-request-authorization-and-write-integrity/06.2-06-PLAN.md:1-176`) updates the canonical reference documentation (`docs/reference/guardian.md`, `docs/reference/delete_view.md`, `docs/reference/formsets.md`, `docs/reference/theme.md`), pairs `CHANGELOG.md` `### Breaking` entries with `docs/migrating-1.0.md` guidance (`D-14`), runs the targeted and full `tests/test1` suites across both cached supported Django 4.2 and 6.0 floor environments plus `mkdocs build --strict`, and records the measured verification and Phase 7 contract inventory in `06.2-ACCEPTANCE.md` and `06.2-VALIDATION.md`.

### Strengths
- **Fence- and anchor-safe documentation updates (`A16`) and H02 compatibility pairing:** Task `06-02` (`.planning/phases/06.2-request-authorization-and-write-integrity/06.2-06-PLAN.md:103-106`) places the new safe-context theme section in `docs/reference/theme.md` as a standalone `##` section outside `### Custom alert frame` (`tests/test1/test_alerts.py:249-254`, which asserts `len(bodies) == 1`), `## Custom form-button templates` (`tests/test1/test_form_button_docs.py:168-174`, which unpacks `(code,)` and `(template,)`), and `## Cancel links in custom form-button templates` (`tests/test1/test_form_button_docs.py:403-409`), and runs `test_alerts.py`, `test_form_button_docs.py`, `test_label_mode_docs.py`, and `test_pagination_docs.py` alongside `.venv/bin/mkdocs build --strict`. It also documents the intentional wrong-model `GuardianCreateViewPermissionRequired.cv_has_access` denial (`H02`) and both the outer (`view_delete.content.html`) and inner (`related_objects.html`) `has_protected_objects` template migration (`H01`).
- **Measured pre-fix full-suite baselines (`A11`) and honest evidence reporting (`A03`):** `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-06-PLAN.md:80,117-120` and `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-VALIDATION.md:146-162` record the exact pre-fix full-suite baselines (`5459 passed, 1 skipped, 1 deselected` on Django 4.2.30; `5460 passed, 1 deselected` on Django 6.0.9) and require comparing post-fix runs against those baselines while carrying the unresolved `AUTH-06/unclassified` probe into `06.2-ACCEPTANCE.md`.

### Concerns
None.

### Suggestions
- When adding `### Breaking` bullets in `CHANGELOG.md` and sections in `docs/migrating-1.0.md` during Task `06-02`, keep `### Table pagination overrides` immediately before `## Silent breaks` in `docs/migrating-1.0.md` (`tests/test1/test_pagination_docs.py:36-42` asserts `text.index(HEADING) + len(HEADING) + len(section) == text.index(SILENT_HEADING)`).

### Risk Assessment
- **Low risk:** Documentation and verification wave guarded by automated doc-extraction tests, `mkdocs build --strict`, and measured dual-Django floor test runs.

---

## Cross-Plan Assessment & Prior-Item Closure Ledger

### Explicit Sign-Off on Prior HIGH Findings (`H01`, `H02`)
- **`H01` — SIGNED OFF (CLOSED):** `06.2-01-PLAN.md:10,43-44,54-56,95-99` and `06.2-06-PLAN.md:89,103` add `src/crud_views/templates/crud_views/view_delete.content.html` to Plan 01's modified files and Task `01-01`, gate both the outer `{% include "crud_views/snippets/delete/related_objects.html" %}` (`src/crud_views/templates/crud_views/view_delete.content.html:8`) and the inner error alert (`src/crud_views/templates/crud_views/snippets/delete/related_objects.html:4`) on `has_protected_objects`, and test an all-hidden protected-only `Publisher` confirmation where `related_summary == {}` and `protected_objects == []` in full-page and modal HTML.
- **`H02` — SIGNED OFF (CLOSED):** `06.2-02-PLAN.md:11,37-38,86,89,150,159` and `06.2-06-PLAN.md:89,103,163` add `tests/test1/test_guardian.py` to Plan 02's modified files and Task `02-01`, explicitly update `test_create_cv_has_access_child_wrong_type_obj` (`tests/test1/test_guardian.py:337-341`) and the helper docstrings (`src/crud_views_guardian/lib/views.py:181-183,206`) from `True` to `False`, preserve `cv_has_access(user, None) is False` (`src/crud_views_guardian/lib/views.py:190-191`) for URL-bound list context resolution, and document the breaking helper change in `docs/reference/guardian.md`, `CHANGELOG.md`, and `docs/migrating-1.0.md`.

### Prior-Item Closure Ledger (`H01`, `H02`, `A01`–`A17`)

| ID | Prior Severity | Status | Resolution & Plan Citation |
| --- | --- | --- | --- |
| **H01** | HIGH | **Closed (Signed Off)** | `06.2-01-PLAN.md:10,43-44,54-56,95-99` owns `src/crud_views/templates/crud_views/view_delete.content.html`, gates both the outer snippet include and inner alert on `has_protected_objects`, and tests empty-summary all-hidden full-page/modal responses. |
| **H02** | HIGH | **Closed (Signed Off)** | `06.2-02-PLAN.md:11,37-38,86,89,150,159` owns `tests/test1/test_guardian.py`, changes `test_create_cv_has_access_child_wrong_type_obj` and helper docstrings to `False`, and `06.2-06-PLAN.md:89,103,163` pairs Breaking/migration docs. |
| **A01** | MEDIUM | **Closed** | `06.2-01-PLAN.md:97,99,113,176,186` distinguishes custom `cv_check_delete_protection` (`200`/`422`) from database `PROTECT` (`pytest.raises(ProtectedError)` with storage intact) and explicitly rejects catching `ProtectedError` in the ledger. |
| **A02** | MEDIUM | **Closed** | `06.2-01-PLAN.md:99,113,177` names and replaces `test_protected_objects_shown_as_warning` (`tests/test1/test_delete.py:142`), `test_filter_related_objects_empty_tree_is_returned_unchanged` (`tests/test1/test_guardian_delete.py:45`), and `test_filter_related_objects_hides_unpermitted_and_keeps_structure` (`:54`). |
| **A03** | MEDIUM | **Closed** | `06.2-01-PLAN.md:100,114,127-128,158`, `06.2-02-PLAN.md:90,103-104,133`, `06.2-03-PLAN.md:88-89,105,134`, `06.2-04-PLAN.md:107,136`, `06.2-05-PLAN.md:114-115,128,158`, and `06.2-06-PLAN.md:90,104,117,146` distinguish red-to-green defect repros from preservation, replay, and docs tasks. |
| **A04** | MEDIUM | **Closed** | `06.2-01-PLAN.md:54-59,99,113,179` places core model-level protected filtering in `DeleteView.cv_filter_related_objects` and Guardian per-object filtering in `GuardianDeleteRelatedObjectsMixin.cv_filter_related_objects` without a second core pass. |
| **A05** | MEDIUM | **Closed** | `06.2-01-PLAN.md:24,97,99,127,180` restricts `DeleteView.http_method_names` and overrides `DeleteView.delete()` to return `http_method_not_allowed`, plus tests a subclass restoring `"delete"`. |
| **A06** | MEDIUM | **Closed** | `06.2-03-PLAN.md:24,79,88,102,151` specifies exact browser-equivalent payloads (including `formset_parent_prefix_key=""` and omitted top-level prefix, saved/unsaved nested rows, and new row indices). |
| **A07** | MEDIUM | **Closed** | `06.2-03-PLAN.md:12,36-37,77,99,104,152` adds test-only `UUIDFragmentRow` and `UUIDFragmentLeaf` to `tests/test1/app/models.py` and exercises persisted `Author -> UUIDFragmentRow -> UUIDFragmentLeaf` FK ancestry. |
| **A08** | MEDIUM | **Closed** | `06.2-02-PLAN.md:80,103,152`, `06.2-03-PLAN.md:77,153`, `06.2-04-PLAN.md:82,153`, and `06.2-05-PLAN.md:105,176` define wave-2 self-contained action/fragment routes and require `finally` restoration of `_REGISTRY`, `_VOCAB_CACHE`, `ROOT_URLCONF`, URL caches, and `TEMPLATES`. |
| **A09** | MEDIUM | **Closed** | `06.2-04-PLAN.md:87-98,154` atomically combines removing `GuardianViewSet.cv_guardian_accept_global_perms` with updating `GuardianManageView.get_context_data`, `config_table.html`, and `test_guardian_manage_context_has_guardian_config` in Task `04-01`. |
| **A10** | MEDIUM | **Closed** | `06.2-05-PLAN.md:64-103,177-178`, `06.2-01-PLAN.md:24,127,181`, and `06.2-02-PLAN.md:89,103,153` define the complete actor × route × method status/storage tables and six native template seams. |
| **A11** | MEDIUM | **Closed** | `06.2-06-PLAN.md:80,117-120,165` and `06.2-VALIDATION.md:146-162` record measured pre-fix full-suite baselines in both Django 4.2 (`5459 passed`) and Django 6.0 (`5460 passed`) crispy-floor environments and define the comparison rules. |
| **A12** | LOW | **Closed** | `06.2-04-PLAN.md:92-93,155` guards the `mode="before"` validator with `isinstance(data, collections.abc.Mapping)` and tests `model_validate(existing_instance)` and non-mapping inputs. |
| **A13** | LOW | **Closed** | `06.2-02-PLAN.md:89,154` declares `cv_guardian_accept_global_perms = False` and `cv_guardian_anonymous_behavior = "redirect"` on `GuardianParentPermissionMixin` and verifies zero `W280` warnings via `CheckUnknownAttributes`. |
| **A14** | MEDIUM | **Closed** | `06.2-03-PLAN.md:24,104,154` normalizes `FormSet.init` prefix identity to `None` when `form.instance._state.adding` is `True` and verifies create/extra-row add-row and bound POST prefix agreement. |
| **A15** | LOW | **Closed** | `06.2-03-PLAN.md:24,102,155` validates `num` and prefix indices with ASCII `[0-9]+` and guarded `int` conversion, testing `num=²` and prefix index `²` for stable `400` responses. |
| **A16** | MEDIUM | **Closed** | `06.2-06-PLAN.md:103-106,166` places new theme guidance in a standalone `##` section outside fence-counted sections and runs `test_alerts.py`, `test_form_button_docs.py`, `test_label_mode_docs.py`, and `test_pagination_docs.py`. |
| **A17** | MEDIUM | **Closed** | `06.2-04-PLAN.md:26,106,156` specifies and tests that parent-only views with resolved parent permission `None` report global fallback as not applicable even when `cv_guardian_accept_global_perms=True`. |

### Deduplicated Unresolved Plan Concerns
None — 0 unresolved HIGH, MEDIUM, or LOW plan concerns remain. The revised Phase 6.2 plans are ready for execution.
