## 06.2-01

### Summary
Plan `06.2-01` closes the inherited HTTP `DELETE` bypass in `DeleteView` (`AUTH-01` / B1), filters `protected_objects` before template projection in both core and Guardian delete previews while adding an independent `has_protected_objects` boolean (`AUTH-03` / B3), and pins `POST` validation, delete protection, hook ordering, and transaction rollback boundaries (`AUTH-07`). While the core mechanism in `src/crud_views/lib/views/delete.py` and `src/crud_views_guardian/lib/views.py` is well-targeted, there is a high-severity template gate omission in `src/crud_views/templates/crud_views/view_delete.content.html:8` that will suppress `related_objects.html` (and therefore the generic blocked notice) whenever a model has only `PROTECT` relationships (`related_summary` is empty) and all protected objects are filtered out (`protected_objects` is empty).

### Strengths
- **Closes inherited `DeletionMixin.delete()` at the shared base class (`src/crud_views/lib/views/delete.py:27, 199-222`):** `DeleteView` inherits from `django.views.generic.DeleteView` (`DeletionMixin`), whose `delete()` method calls `self.get_object()` and `self.object.delete()` directly, bypassing `DeleteView.post()` (`src/crud_views/lib/views/delete.py:199-220`), `CrispyDeleteForm` validation, `cv_check_delete_protection()` (`delete.py:176, 206`), and `cv_form_valid_process()` (`src/crud_views/lib/views/mixins.py:48-57`). Restricting `DeleteView` in core automatically covers `DeleteViewPermissionRequired` (`delete.py:225`), `PolymorphicDeleteView` (`src/crud_views_polymorphic/lib/delete.py:5`), and `GuardianDeleteViewPermissionRequired` (`src/crud_views_guardian/lib/views.py:85`).
- **Removes the empty-tree early return in Guardian preview filtering (`src/crud_views_guardian/lib/views.py:42-43`):** Currently `GuardianDeleteRelatedObjectsMixin.cv_filter_related_objects()` executes `if not related.tree: return related` at lines 42–43 and passes `protected=related.protected` unfiltered at line 49. Removing the early return and applying `_PermittedPks` (`src/crud_views_guardian/lib/views.py:53-70`) to `related.protected` ensures protected-only collections are filtered using one bulk `get_objects_for_user()` query per model.
- **Preserves `alert_data()` list-vs-text body selection (`src/crud_views/lib/messages.py:42-44`):** `crud_views/snippets/delete/related_objects.html:4-6` renders the blocked notice via `{% cv_alert "error" heading=_("Deletion is blocked by protected relationships:") items=protected_objects %}`. In `alert_data()` (`src/crud_views/lib/messages.py:42-44`), when `items` is empty (`[]`), `body_template` automatically switches from `LIST_BODY` (`snippets/alert/list.html`) to `TEXT_BODY` (`snippets/alert/text.html` with `text=""`), rendering the heading alert cleanly without an empty `<ul>` or `<li>None</li>` placeholder.
- **Follows established `monkeypatch` transaction test patterns (`tests/test1/test_transactions.py:28-33, 310-385`):** Task `01-03` extends `tests/test1/test_transactions.py` by patching existing registered view classes (`PublisherDeleteView`, `PublisherProtectedDeleteView`, `GuardianPublisherCascadeDeleteView`) rather than subclassing with a registered `cv_viewset` in the class body (which would fail `ViewSet.register_view_class` at `src/crud_views/lib/viewset/__init__.py:319`).

### Concerns
- **HIGH — Missing `view_delete.content.html:8` template guard update suppresses the blocked notice for protected-only objects (`src/crud_views/templates/crud_views/view_delete.content.html:8`, `src/crud_views/lib/views/delete.py:88-96`):**
  - In `DeleteView.cv_get_related_objects()` (`src/crud_views/lib/views/delete.py:85-96`), `NestedObjects.collect([self.object])` catches `ProtectedError` and adds `PROTECT`-related instances (such as `Contract` on `Publisher`, `tests/test1/app/models.py:72-75`) to `collector.protected`, **not** `collector.data`. Consequently, when a `Publisher` has a protected `Contract` and zero cascade `Book`s, `related.summary` is `{}` (empty).
  - When the user lacks `view_contract` permission, `cv_filter_related_objects()` filters `context["protected_objects"]` to `[]` (empty) while `context["has_protected_objects"]` is `True`.
  - However, `src/crud_views/templates/crud_views/view_delete.content.html:8` guards the inclusion of `related_objects.html` with:
    `{% if related_summary or protected_objects %}{% include "crud_views/snippets/delete/related_objects.html" %}{% endif %}`
  - Because `view_delete.content.html` is **not** in `06.2-01`'s `files_modified`, when `related_summary` is `{}` and `protected_objects` is `[]`, `view_delete.content.html:8` evaluates to `False` and never includes `related_objects.html` at all—violating `D-08` / `AUTH-03` ("The generic notice must remain visible even when every protected-object label is hidden" and "Edge AUTH-03 empty: Empty, protected-only, single and entirely hidden protected collections preserve correct blocked state").
- **MEDIUM — Existing tests in `tests/test1/test_delete.py` will break without permission/assertion updates (`tests/test1/test_delete.py:142-156, 304-319`):**
  - `test_protected_objects_shown_as_warning` (`tests/test1/test_delete.py:142-156`) creates only a `Contract` (no `Book`) and uses `client_user_publisher_cascade_delete`, which only holds `delete_publisher` (not `view_contract`). Once core `cv_filter_related_objects()` (`src/crud_views/lib/views/delete.py:147-172`) filters `related.protected` by `app.view_contract`, `context["protected_objects"]` becomes `[]`, breaking `assert len(context["protected_objects"]) > 0` at `tests/test1/test_delete.py:153` unless updated to assert `context["has_protected_objects"] is True` and `context["protected_objects"] == []` (and a companion test or grant tests visible `protected_objects`).
  - Similarly, in `test_guardian_delete.py:54-73` (`test_filter_related_objects_hides_unpermitted_and_keeps_structure`), `protected=["p"]` uses a synthetic string sentinel (`line 66, 73`), which Task `01-02` notes must be adapted to real `PROTECT` model instances.
- **MEDIUM — Conflation between `cv_check_delete_protection()` POST handling and database `on_delete=PROTECT` on `POST` (`src/crud_views/lib/views/delete.py:199-222`):**
  - Task `01-01` states: `"A real authorized core delete confirmation for a protected Publisher renders one generic notice without a hidden Contract label; GET and protected POST preserve the row"`, and Task `01-02` states: `"Add actual PROTECT model cases rather than relying on string sentinels. ... assert actual protected POST keeps the row."`
  - In `src/crud_views/lib/views/delete.py:206-222`, `DeleteView.post()` checks `errors = context.get("delete_protection_errors", [])` (from `cv_check_delete_protection()`), **not** `has_protected_objects` / `ProtectedError`. If a view has `cv_check_delete_protection()` returning errors (`PublisherProtectedDeleteView`, `tests/test1/app/views.py:807-814`), `view_delete.content.html:5` (`{% if delete_protection_errors %}`) renders `protection_errors.html` instead of `related_objects.html`. Conversely, if `cv_check_delete_protection()` returns `[]` (`PublisherCascadeDeleteView` / `GuardianPublisherCascadeDeleteView`) and a database `Contract` (`on_delete=PROTECT`) blocks deletion, `DeleteView.post()` calls `self.object.delete()` at line 222, which raises `django.db.models.deletion.ProtectedError` unless `post()` either blocks/catches it or the test asserts `pytest.raises(ProtectedError)` before checking `Publisher.objects.filter(pk=pk).exists()`.
- **LOW — Inherited `DeletionMixin.delete` method remains callable on `DeleteView` if only `http_method_names` is narrowed (`src/crud_views/lib/views/delete.py:27`):**
  - If `DeleteView` only narrows `http_method_names` without also overriding `delete(self, request, *args, **kwargs)` to return `self.http_method_not_allowed(request, *args, **kwargs)`, a subclass that customizes `http_method_names` or delegates to `super().delete()` would still hit `DeletionMixin.delete()`.

### Suggestions
- Add `src/crud_views/templates/crud_views/view_delete.content.html` to `06.2-01`'s `files_modified` and change line 8 from `{% if related_summary or protected_objects %}` to `{% if related_summary or has_protected_objects or protected_objects %}` (and in `related_objects.html:4`, use `{% if has_protected_objects or protected_objects %}` so direct template renders passing only `protected_objects` also continue to work).
- In `DeleteView` (`src/crud_views/lib/views/delete.py`), in addition to removing `"delete"` from `http_method_names`, override `def delete(self, request, *args, **kwargs): return self.http_method_not_allowed(request, *args, **kwargs)`.
- Explicitly clarify in Tasks `01-01` and `01-02` whether `POST` on a `Contract`-protected `Publisher` asserts `pytest.raises(ProtectedError)` with the row preserved in storage, or whether `DeleteView.post()` should also prevent `self.object.delete()` when `has_protected_objects` is true.
- Update `test_protected_objects_shown_as_warning` (`tests/test1/test_delete.py:142-156`) so it tests both the ungranted (`has_protected_objects is True`, `protected_objects == []`) and granted (`view_contract` -> `protected_objects == [contract]`) cases.

### Risk Assessment
**MEDIUM** — The omitted `{% if related_summary or protected_objects %}` condition in `src/crud_views/templates/crud_views/view_delete.content.html:8` would directly cause the protected-only hidden-label test case to fail to render the generic blocked alert in full-page and modal delete confirmations. Once `view_delete.content.html:8` is included, the changes are localized and well-bounded.

---

## 06.2-02

### Summary
Plan `06.2-02` fixes the `cv_guardian_parent_permission = None` / `cv_guardian_parent_create_permission = None` action-state bypass and helper crash (`AUTH-04` / B4 & B6) and enforces inactive-user denial across all Guardian request gates and callable helpers (`AUTH-05` / B5). The plan rightly identifies that default `ModelBackend` masks B5 and mandates testing with `AllowAllUsersModelBackend`. However, there is a direct conflict in Task `02-01` with an existing test in `tests/test1/test_guardian.py:337-342` regarding wrong-type `obj` in `GuardianCreateViewPermissionRequired.cv_has_access()`, and Task `02-02` references testing `action` and `fragment` routes that do not yet exist in `tests/test1/app/views.py`.

### Strengths
- **Fixes both the state-gate bypass and the `None.split` crash from a single root cause (`src/crud_views_guardian/lib/mixins.py:212-245`, `src/crud_views_guardian/lib/views.py:146-155, 195-204`):**
  - In `GuardianParentPermissionMixin._guardian_check_parent()` (`src/crud_views_guardian/lib/mixins.py:230-245`), `if perm_key is None: return` at lines 233–234 currently exits before `parent_obj = get_object_or_404(...)` (line 235) and before `if not self.cv_object and not self.cv_action_enabled(user, parent_obj): raise PermissionDenied` (lines 244–245).
  - In `GuardianCreateViewPermissionRequired.cv_create_has_access()` (`src/crud_views_guardian/lib/views.py:146-155`) and `cv_has_access()` (`views.py:195-204`), `perm_key = getattr(..., "cv_guardian_parent_create_permission", None) or getattr(..., "cv_guardian_parent_permission", "view")` evaluates to `None` when both are `None`, causing `perm.split(".")[1]` at lines 155 and 204 to raise `AttributeError: 'NoneType' object has no attribute 'split'`.
  - Centralizing `_guardian_parent_perm_key()` as a classmethod on `GuardianParentPermissionMixin` and resolving `parent_obj` before the optional permission check cleanly fixes both B4 and B6.
- **Addresses the exact `django-guardian` asymmetry for inactive users (`src/crud_views_guardian/lib/mixins.py:98-105, 159-170`, `src/crud_views_guardian/lib/viewset.py:63-73`, `src/crud_views_guardian/lib/views.py:53-70`):**
  - `guardian.core.ObjectPermissionChecker.has_perm()` checks `self.user.is_active`, whereas `guardian.shortcuts.get_objects_for_user()` returns granted rows for inactive users and `qs.all()` for inactive superusers when authenticated via `AllowAllUsersModelBackend`. Checking `user.is_active` across `GuardianParentPermissionMixin`, `GuardianObjectPermissionMixin`, `GuardianQuerysetMixin`, `GuardianCreateViewPermissionRequired`, `GuardianViewSet.get_objects_for_user()`, and `_PermittedPks` eliminates this discrepancy while preserving active superuser behavior (`D-05`).
- **Preserves anonymous redirect/403/404 handling (`src/crud_views_guardian/lib/mixins.py:31-38, 98-105, 196-210`):**
  - By checking `request.user.is_authenticated` first (which routes anonymous users to `_guardian_deny_anonymous()` / `cv_guardian_anonymous_behavior`) and only then raising `PermissionDenied` when `not request.user.is_active`, existing anonymous behavior (`tests/test1/test_guardian.py:695-748`) is preserved.

### Concerns
- **HIGH — Contradiction between Task `02-01` ("fail closed on absent/wrong-type parent") and existing `test_create_cv_has_access_child_wrong_type_obj` (`tests/test1/test_guardian.py:337-342`, `src/crud_views_guardian/lib/views.py:181-183, 194-206`):**
  - In `src/crud_views_guardian/lib/views.py:194-206`, `GuardianCreateViewPermissionRequired.cv_has_access(cls, user, obj=None)` checks `if isinstance(obj, parent_vs.model): ...` and at line 206 falls back to `return True` when `obj` is not an instance of `parent_vs.model` (for example, when rendering a child detail page where `obj` is a `Book` rather than a `Publisher`).
  - `tests/test1/test_guardian.py:337-342` explicitly asserts:
    `def test_create_cv_has_access_child_wrong_type_obj(user_guardian, book_under_publisher_a): assert GuardianBookCreateView.cv_has_access(user_guardian, book_under_publisher_a) is True`
  - Task `02-01` instructs: `"Ensure helpers handle None without splitting it, fail closed on absent/wrong-type parent"`, does **not** include `tests/test1/test_guardian.py` in `files_modified`, and runs `pytest tests/test1/test_guardian_parent_none.py tests/test1/test_guardian.py` in its `<verify>` step. If the executor changes `cv_has_access` line 206 to return `False` for wrong-type `obj` (rather than only failing closed in `cv_create_has_access` when `parent_obj` is `None` or not an instance of `parent_vs.model`), `test_guardian.py::test_create_cv_has_access_child_wrong_type_obj` will immediately fail.
- **MEDIUM — `GuardianActionViewPermissionRequired` and Guardian formset fragment routes are not registered in `tests/test1/app/views.py` (`src/crud_views_guardian/lib/views.py:94-97`, `tests/test1/app/views.py:640-774`):**
  - Task `02-02` specifies: `"Cover ordinary, direct grants, group grants, global-only fallback on/off and superusers across list/card/detail/update/delete/action/create/fragment entry and callable paths."`
  - However, `tests/test1/app/views.py` has zero `GuardianActionViewPermissionRequired` subclasses and zero Guardian `FormSetMixin` views registered on `cv_guardian_author`, `cv_guardian_publisher`, or `cv_guardian_book`. Furthermore, because `ViewSet.urlpatterns` is a `@cached_property` (`src/crud_views/lib/viewset/__init__.py:403-404`) evaluated when `tests/test1/project/urls.py` is imported, registering a new view on an existing ViewSet inside `test_guardian_inactive.py` will not add its route to the root URLConf.
  - Note also that Plan `06.2-03` (Wave 3, which fixes `FormSetMixinBase.get()` fragment authorization) runs *after* Plan `06.2-02` (Wave 2); for an inactive user in Wave 2, fragment requests on a Guardian view are only denied if `GuardianParentPermissionMixin.dispatch()` or `has_permission()` denies inactive users during `dispatch()` before `FormSetMixinBase.get()` runs.
- **LOW — Missing `cv_guardian_accept_global_perms` and `cv_guardian_anonymous_behavior` class attributes on `GuardianParentPermissionMixin` (`src/crud_views_guardian/lib/mixins.py:173-228`):**
  - `GuardianObjectPermissionMixin` (`mixins.py:28-29`) and `GuardianQuerysetMixin` (`mixins.py:95-96`) declare `cv_guardian_accept_global_perms: bool = False` and `cv_guardian_anonymous_behavior: str = "redirect"`, but `GuardianParentPermissionMixin` only reads them via `getattr(self, ...)` (`mixins.py:205, 224`). As a result, `GuardianCreateViewPermissionRequired` (`src/crud_views_guardian/lib/views.py:112`) does not have those attributes on its MRO (forcing `monkeypatch.setattr(..., raising=False)` in `tests/test1/test_guardian.py:886, 897, 916` and excluding them from `CheckUnknownAttributes._context_names()` in `src/crud_views/lib/check.py:364-374`).

### Suggestions
- Clarify in Task `02-01` that `cv_create_has_access(cls, user, rendering_view, parent_obj)` must return `False` when `parent_obj is None` or `not isinstance(parent_obj, parent_vs.model)`, while `cv_has_access(cls, user, obj=None)` must preserve the existing `test_create_cv_has_access_child_wrong_type_obj` (`tests/test1/test_guardian.py:337-342`) contract for non-parent `obj` (while still returning `False` for inactive users).
- In Task `02-02`, instruct `tests/test1/test_guardian_inactive.py` to define an isolated test-local `GuardianViewSet` (cleaning up `_REGISTRY` on teardown) with a local `urlpatterns` / `@override_settings(ROOT_URLCONF=...)` to test `GuardianActionViewPermissionRequired` and Guardian fragment entry routes, and ensure `GuardianParentPermissionMixin.dispatch()` raises `PermissionDenied` for authenticated inactive users (`if not request.user.is_active: raise PermissionDenied`) so fragment requests are blocked in `dispatch()` even in Wave 2.
- Declare `cv_guardian_accept_global_perms: bool = False` and `cv_guardian_anonymous_behavior: str = "redirect"` on `GuardianParentPermissionMixin` (`src/crud_views_guardian/lib/mixins.py:190`).

### Risk Assessment
**MEDIUM** — The potential breakage of `tests/test1/test_guardian.py:337-342` (`test_create_cv_has_access_child_wrong_type_obj`) and the need for test-local URL routing for `GuardianActionViewPermissionRequired` in `test_guardian_inactive.py` are concrete implementation traps that should be disambiguated before execution.

---

## 06.2-03

### Summary
Plan `06.2-03` closes the AJAX formset fragment authorization bypass (`AUTH-02` / B2) by initializing and authorizing the view target in `FormSetMixinBase.get()` before calling `get_template_html()`, and adds a declaration-aware coordinate and FK-ancestry validator in `src/crud_views/lib/formsets/formsets.py`. The plan accurately captures the distinction between the endpoint root object and nested inline parent PKs. However, there are two important technical gaps around UUID-keyed models in `tests/test1/app/models.py` and `FormSet.init()` (`src/crud_views/lib/formsets/formsets.py:123`) that need attention.

### Strengths
- **Resolves the MRO / early-return root cause of B2 (`src/crud_views/lib/formsets/mixins.py:37-45`, `src/crud_views_guardian/lib/mixins.py:31-58`):**
  - Currently `FormSetMixinBase.get()` (`src/crud_views/lib/formsets/mixins.py:37-45`) checks `if template: data = self.get_template_html(request); return JsonResponse(data)` before calling `super().get()`. Because `GuardianObjectPermissionMixin.has_permission()` (`src/crud_views_guardian/lib/mixins.py:31-38`) returns `True` for all authenticated users and defers object permission and `cv_action_enabled()` checks to `get_object()` (`mixins.py:50-58`), `FormSetMixinBase.get()` never triggers `get_object()` on update views. Initializing `self.object = self.get_object() if self.cv_object else None` (mirroring `CrudViewProcessFormMixin.post()` at `src/crud_views/lib/views/mixins.py:37`) before `get_template_html()` runs all object, parent, and action-state gates before any formset or `ModelChoiceField` is instantiated.
- **Correctly distinguishes nested inline `pk` from the endpoint root PK (`src/crud_views/lib/formsets/formsets.py:123, 189, 374-380`, `src/crud_views/static/crud_views/js/formset.js:155-161, 318-323`):**
  - In `formset.js:318-323`, clicking "Add row" sends `template: this.formset.hierarchy.join("|")`, `pk: this.formset.pk === null ? "None" : this.formset.pk`, `num: this.formset.get_total_forms()`, and `formset_parent_prefix_key: this.formset.parent_prefix_key`. For a nested level-1 formset (`books|notes`), `pk` is the `Book` PK (or `"None"` for an unsaved `Book` row), while `formset_parent_prefix_key` (`"<publisher_pk>-0-<book_row_index>"`) carries the endpoint `Publisher` PK in its first segment. Plan `06.2-03` explicitly preserves this wire protocol (`D-09`) while validating the ancestry chain.
- **Uses isolated test-local ViewSets and URLConf (`tests/test1/test_fragment_authorization.py`):**
  - Creating uniquely named `GuardianViewSet` instances with a temporary URLConf in `tests/test1/test_fragment_authorization.py` avoids mutating `cv_publisher_formset` (`tests/test1/app/views_formset.py:29-33`) or colliding with `_REGISTRY` (`src/crud_views/lib/viewset/__init__.py:147-151`).

### Concerns
- **MEDIUM — No existing model in `tests/test1/app/models.py` has a `ForeignKey` to or from the UUID-keyed `Author` model (`tests/test1/app/models.py:13-81`, `06.2-03-PLAN.md` Task `03-02`):**
  - Task `03-02` states: `"Valid root/nested persisted and None chains, UUID IDs and client-added row indices pass... Add existing UUID-model inline fixture declarations inside tests where possible, not production schema changes."`
  - However, in `tests/test1/app/models.py`, `Author` (`line 13-14`) is the **only** model in `tests/` with a `UUIDField` primary key, and **no model in `tests/test1/app/models.py` or `tests/test1/od_app/models.py` has a `ForeignKey` to `Author`** (nor does `Author` have a `ForeignKey` to any other model).
  - Calling Django's `inlineformset_factory(Author, Book, ...)` raises `ValueError: 'app.Book' has no ForeignKey to 'app.Author'`. And calling `inlineformset_factory(Publisher, Book, ...)` with `FormSet(pk=FormSet.PK.UUID)` will fail model-field PK conversion (`Publisher._meta.pk.to_python(uuid_str)`) because `Publisher.id` is a `BigAutoField` (`int`), not a `UUIDField`.
  - Note also that `tests/test1/app/models.py` is a test-only app migrated in-memory by `tests/test1/conftest.py` (it is not part of `src/` or any shipped package migration). If `tests/test1/app/models.py` is not modified, `test_fragment_authorization.py` will need to either create a test-only model/table with `connection.schema_editor()` or attach a synthetic/test `ForeignKey` to `Author`.
- **MEDIUM — Unsaved `ModelForm` instances for models with `UUIDField(default=uuid.uuid4)` already have a non-`None` `.pk` in `FormSet.init()` (`src/crud_views/lib/formsets/formsets.py:123`):**
  - In `src/crud_views/lib/formsets/formsets.py:123`, `FormSet.init()` constructs `prefix_key = f"{parent_prefix_}{form.instance.pk}-{index}"`.
  - When a model has `id = models.UUIDField(primary_key=True, default=uuid.uuid4)` (like `Author` in `tests/test1/app/models.py:14`), Django assigns a new UUID to `form.instance.pk` in `Model.__init__()` even when the instance is unsaved (`form.instance._state.adding is True` — compare `src/crud_views/lib/view/base.py:752-756`).
  - If `FormSet.init()` emits that unsaved default UUID into `prefix_key` on a `CreateView` (or an unsaved inline extra row on an `UpdateView`), `formset.js` will send that unsaved UUID as `pk` / `formset_parent_prefix_key`, and a coordinate validator checking `model.objects.filter(pk=...)` for non-`"None"` PKs will reject it with `400 BadRequest` because that UUID has not been saved to the database yet.
- **LOW — `str.isdigit()` in `FormSetMixinBase.get_template_html()` accepts non-ASCII Unicode digits (`src/crud_views/lib/formsets/mixins.py:54`):**
  - Line 54 checks `if num is None or not num.isdigit(): raise BadRequest("num must be an integer")`, followed by `int(num)` at line 68. For Unicode superscript digits such as `"²"` (`"\u00b2"`), `num.isdigit()` is `True` while `int(num)` raises `ValueError` (500).
- **LOW — `formset_parent_prefix_key` is `""` from `formset.js` at level 0 but `None` when omitted in existing tests (`src/crud_views/static/crud_views/js/formset.js:322`, `src/crud_views/lib/formsets/render_tree.py:135-138`, `tests/test1/test_formsets.py:156`):**
  - At level 0 (`len(key_path) == 1`), `XFormSet.parent_prefix_key` (`render_tree.py:138`) is `""`, so `formset.js:322` sends `formset_parent_prefix_key=""`, which `FormSet.template()` (`formsets.py:187`) treats as falsy (`f"{parent_prefix}-" if parent_prefix else ""`). The coordinate validator must treat both `None` and `""` as empty at level 0, require a non-empty `formset_parent_prefix_key` at `len(key_path) > 1`, and reject non-empty `formset_parent_prefix_key` at `len(key_path) == 1`.

### Suggestions
- To test real UUID coordinate parsing and FK ancestry in Task `03-02` without touching `src/`, either add `tests/test1/app/models.py` to `files_modified` (e.g., an optional nullable `author = models.ForeignKey(Author, on_delete=models.CASCADE, null=True, blank=True, related_name="books")` on `Book` or a small test model in `tests/test1/app/models.py`), or create an in-memory test model via `schema_editor.create_model()` inside a fixture in `tests/test1/test_fragment_authorization.py`.
- Check `form.instance._state.adding` in `FormSet.init()` (`src/crud_views/lib/formsets/formsets.py:123`)—i.e., `instance_pk = None if form.instance._state.adding else form.instance.pk`—or ensure the coordinate validator accounts for unsaved `CreateView` / extra-row instances whose `UUIDField` has `default=uuid.uuid4`.
- In `src/crud_views/lib/formsets/formsets.py` / `mixins.py:54`, validate `num` and prefix indices with `isascii() and isdigit()` (or `re.fullmatch(r"[0-9]+", ...)`), and enforce the monotonic ancestry rule:
  1. At level 0, root PK must equal `str(self.object.pk)` when `self.cv_object` is `True` (`UpdateView`) and `"None"` when `self.cv_object` is `False` (`CreateView`).
  2. For each step `d` along `key_path`, the child index segment in `formset_parent_prefix_key` must match the declared child index (`0` at `d == 0`, and the position of `key_path[d]` in `parent_node.children` for `d >= 1`).
  3. Once any ancestor PK in the chain is `"None"`, all deeper PKs (including `pk`) must also be `"None"`.
  4. Any non-`"None"` PK at depth `d >= 1` must parse via `parent_node.klass.model._meta.pk.to_python()` and match an existing row in `parent_node.klass.model.objects.filter(pk=parsed_pk, **{parent_node.klass.fk.name: prev_obj})`.

### Risk Assessment
**MEDIUM** — The coordinate grammar and ancestry validation have subtle interactions with `UUIDField` defaults, `test_formsets.py` missing-param defaults (`formset_parent_prefix_key=None` vs `""`), and multi-child `child_index` offsets (`src/crud_views/lib/formsets/formsets.py:159-167`). Addressing the UUID test-model setup and `isascii()` / ancestry monotonicity makes the implementation solid.

---

## 06.2-04

### Summary
Plan `06.2-04` resolves B7 (`AUTH-06`) by removing the inert `GuardianViewSet.cv_guardian_accept_global_perms` field (`src/crud_views_guardian/lib/viewset.py:23`), adding a targeted `mode="before"` Pydantic validator that raises a clear error naming the per-view replacement, keeping `GuardianViewSet.get_objects_for_user()` strict (`accept_global_perms=False`), and updating `GuardianManageView` and its templates (`src/crud_views_guardian/lib/views.py:212-234, 270-276`, `config_table.html`, `view_guardian_manage.html`) to report per-view effective global-permission policy and the strict helper policy. The design is clean, low-risk, and well-aligned with `D-03`–`D-06`.

### Strengths
- **Targeted `mode="before"` validator catches the removed constructor argument before Pydantic drops extras (`src/crud_views_guardian/lib/viewset.py:9-24, 35-49`):**
  - Because `ViewSet(BaseModel)` (`src/crud_views/lib/viewset/__init__.py:47`) uses Pydantic's default `extra="ignore"`, simply deleting `cv_guardian_accept_global_perms: bool = False` from `GuardianViewSet` would cause `GuardianViewSet(..., cv_guardian_accept_global_perms=True)` to be silently ignored at construction time and invisible to Django system checks.
  - Using `@model_validator(mode="before")` (analogous to `FormSets.check_keys` in `src/crud_views/lib/formsets/formsets.py:270-277`) inspects raw constructor kwargs before `extra="ignore"` strips them and before `GuardianViewSet.register` (`mode="after"`, `src/crud_views_guardian/lib/viewset.py:35-49`) registers the ViewSet in `_REGISTRY`.
- **Truthful manage view projection per view and for the helper (`src/crud_views_guardian/lib/views.py:228-233, 270-276`, `src/crud_views_guardian/templates/crud_views/snippets/guardian/config_table.html:15-18`):**
  - Currently `GuardianManageView.get_context_data()` (`src/crud_views_guardian/lib/views.py:231`) sets `"cv_guardian_accept_global_perms": self.cv_viewset.cv_guardian_accept_global_perms`, which never reflected the view-level `cv_guardian_accept_global_perms` read by `GuardianObjectPermissionMixin`, `GuardianQuerysetMixin`, and `GuardianParentPermissionMixin`. Moving the per-view effective policy into `GuardianManageView.get_view_data()` (`views.py:270-276`) and reporting the strict `get_objects_for_user` helper in `guardian_config` (`config_table.html`) makes the manage diagnostics accurate when views on the same ViewSet have mixed policies.
- **Explicitly tracks the `AUTH-06/unclassified` assumption rather than silently dropping it:**
  - The plan surfaces the unclassified edge probe result and covers constructor rejection, mixed-policy views, strict helper behavior, and manage access gates with concrete tests in `tests/test1/test_guardian_policy.py` and `tests/test1/test_guardian.py`.

### Concerns
- **MEDIUM — Applicability of `cv_guardian_accept_global_perms` on `GuardianCreateViewPermissionRequired` depends on whether the ViewSet has a parent and a non-`None` parent permission (`src/crud_views_guardian/lib/views.py:112-120, 270-276`, `src/crud_views_guardian/lib/mixins.py:191-245`):**
  - Task `04-02` states: `"Enrich each registered view's existing get_view_data projection with its effective per-view global fallback and applicability, using registered view class attributes and applicable Guardian mixins; avoid implying a plain or top-level-create view uses an object fallback it does not."`
  - Trace `GuardianCreateViewPermissionRequired(GuardianParentPermissionMixin, CreateViewPermissionRequired)` (`src/crud_views_guardian/lib/views.py:112`):
    1. Its only Guardian mixin in `GUARDIAN_MIXINS` (`views.py:17-21`) is `GuardianParentPermissionMixin`.
    2. When `self.cv_viewset.parent is None` (a top-level create view like `GuardianAuthorCreateView`), `GuardianParentPermissionMixin` is a no-op and `CreateViewPermissionRequired` always checks the global model-level `add_<model>` permission (`mixins.py:191-194`). Thus `cv_guardian_accept_global_perms` is **not applicable** to a top-level create view.
    3. When `self.cv_viewset.parent is not None` (a child create view like `GuardianBookCreateView`), `GuardianParentPermissionMixin._guardian_has_parent_perm()` (`mixins.py:224`) and `cv_create_has_access()` / `cv_has_access()` (`views.py:150, 199`) **do** use `cv_guardian_accept_global_perms`—unless the effective parent permission key (`_guardian_parent_perm_key()`) is `None`!
    4. Similarly, `GuardianManageView` itself is registered in `self.cv_viewset.get_all_views()["manage"]` (`src/crud_views_guardian/lib/viewset.py:47`) and has no Guardian mixin (`guardian_mixin == "—"`), so `cv_guardian_accept_global_perms` is not applicable to `manage`.
- **LOW — Intra-plan ordering between Task `04-01` and Task `04-02` (`src/crud_views_guardian/lib/viewset.py:23`, `src/crud_views_guardian/lib/views.py:231`):**
  - When Task `04-01` removes `GuardianViewSet.cv_guardian_accept_global_perms` from `src/crud_views_guardian/lib/viewset.py:23`, `GuardianManageView.get_context_data()` at `src/crud_views_guardian/lib/views.py:231` still references `self.cv_viewset.cv_guardian_accept_global_perms` until Task `04-02` updates `views.py:231`. In `04-01`, `test_guardian_policy.py` must not hit `/manage/` until `04-02` updates `GuardianManageView.get_context_data()`.
- **LOW — `mode="before"` validator should guard `isinstance(data, Mapping)` (`src/crud_views_guardian/lib/viewset.py`):**
  - If a caller invokes `GuardianViewSet.model_validate(...)` with a non-mapping input, `if "cv_guardian_accept_global_perms" in data` could raise `TypeError` unless guarded with `isinstance(data, Mapping)`.

### Suggestions
- In `GuardianManageView.get_view_data()` (`src/crud_views_guardian/lib/views.py:270-276`), determine applicability of `cv_guardian_accept_global_perms` as:
  - Applicable (`bool(getattr(view_class, "cv_guardian_accept_global_perms", False))`) when `issubclass(view_class, (GuardianObjectPermissionMixin, GuardianQuerysetMixin))` OR (`issubclass(view_class, GuardianParentPermissionMixin)` and `self.cv_viewset.parent is not None` and the view's resolved parent permission key is not `None`);
  - Not applicable (`"—"`) for `GuardianManageView`, plain non-Guardian views, top-level `GuardianCreateViewPermissionRequired` (`parent is None`), or parent-only views whose resolved parent permission key is `None`.
- Guard the `mode="before"` validator on `GuardianViewSet` with `if isinstance(data, Mapping) and "cv_guardian_accept_global_perms" in data: raise ValueError(...)`, and verify in `test_guardian_policy.py` that a failed `GuardianViewSet(..., cv_guardian_accept_global_perms=True)` call does not leave a partial entry in `_REGISTRY`.

### Risk Assessment
**LOW** — The scope is tight, all touched files (`viewset.py`, `views.py`, `config_table.html`, `view_guardian_manage.html`, `test_guardian.py`, `test_guardian_policy.py`) are well-isolated from `06.2-03` in Wave 3, and existing manage tests in `tests/test1/test_guardian.py:636-690` provide a clear baseline.

---

## 06.2-05

### Summary
Plan `06.2-05` provides comprehensive end-to-end verification (`AUTH-07`) across two new test modules: `tests/test1/test_authorization_matrix.py` (replaying the full actor matrix from `superpowers/notes/2026-10-28-pre-1.0-before-theme-freeze-analysis.md` §3 on direct routes) and `tests/test1/test_authorization_templates.py` (proving via `locmem.Loader` template overrides that list, card, action, manage, alert, and formset templates receive already-filtered safe context without needing template-level permission checks).

### Strengths
- **Verifies server-owned context confidentiality independently of stock markup (`tests/test1/test_authorization_templates.py`, `tests/test1/test_crispy_buttons.py:354-375`):**
  - Reusing the `copy.deepcopy(settings.TEMPLATES)` + `django.template.loaders.locmem.Loader` pattern (`APP_DIRS=False`) to override list, card, action, manage, alert, and formset templates with minimal native HTML (`<dl>`, `<details>`, `<form>`, `<div role="alert">`) andoverride sentinels proves both that the override is rendered and that no unauthorized rows, protected object labels, or secret `ModelChoiceField` choices reach template context.
- **Covers cross-request and interleaved actor isolation (`06.2-05-PLAN.md` Task `05-01`):**
  - Testing interleaved requests across strict and global-fallback views, distinct URL parents, next-request permission revocation, and `AllowAllUsersModelBackend` inactive sessions verifies that `_PermittedPks` (`src/crud_views_guardian/lib/views.py:53-70`) and `ObjectPermissionChecker` caches never leak across requests.
- **Includes the required `--deselect` flag for `crispy_floor` (`06.2-05-PLAN.md` Task `05-02`, `noxfile.py:57`):**
  - Task `05-02`'s `<verify>` command includes `--deselect tests/test1/test_form_buttons_golden.py::test_filter_form_baseline`, matching `CRISPY_FLOOR_DESELECT` in `noxfile.py:57` so pack-wrapper whitespace differences in `crispy-bootstrap5==2023.10` do not cause a false failure while `test_filter_form_controls_match_golden` still runs.

### Concerns
- **LOW — Discrepancy between `06.2-05-PLAN.md` Task `05-02` command and `06.2-VALIDATION.md` line 43 (`06.2-VALIDATION.md:43, 142`):**
  - `06.2-05-PLAN.md` Task `05-02` includes `--deselect tests/test1/test_form_buttons_golden.py::test_filter_form_baseline` in `<verify>`, and `06.2-VALIDATION.md:142` documents that exclusion, but the table cell at `06.2-VALIDATION.md:43` omits `--deselect ...` (which would fail if copied verbatim from the table cell in the `crispy_floor` venv).
- **LOW — Global `_REGISTRY` and `settings.TEMPLATES` state hygiene when combining test-local routes and `locmem` overrides (`src/crud_views/lib/viewset/__init__.py:43-44, 146-152`):**
  - Because `ViewSet.register()` mutates the process-global `_REGISTRY` (`src/crud_views/lib/viewset/__init__.py:151`) and `CheckUnknownAttributes` caches vocabulary keyed by `len(_registered_view_classes())` in `_VOCAB_CACHE` (`src/crud_views/lib/check.py:321-344`), leaving test-local ViewSets in `_REGISTRY` or failing to pop them (and clear `_VOCAB_CACHE` if needed) can affect subsequent system-check tests in a full-suite run (`06.2-06` Task `06-03`).

### Suggestions
- Ensure any test-local `ViewSet` / `GuardianViewSet` created in `test_authorization_matrix.py` or `test_authorization_templates.py` cleans up `_REGISTRY` (and `_VOCAB_CACHE` in `crud_views.lib.check`) in a `try/finally` or fixture teardown block, matching `tests/test1/test_guardian.py:819-821`.
- Sync the command in `06.2-VALIDATION.md:43` (and `46`) with `06.2-VALIDATION.md:142` during Plan `06.2-06` so the table cells also include `--deselect tests/test1/test_form_buttons_golden.py::test_filter_form_baseline`.

### Risk Assessment
**LOW** — Plan `06.2-05` only adds test modules (`tests/test1/test_authorization_matrix.py` and `tests/test1/test_authorization_templates.py`) and modifies no production files. With proper `_REGISTRY` fixture cleanup, risk of side effects on the rest of the test suite is minimal.

---

## 06.2-06

### Summary
Plan `06.2-06` updates the canonical reference docs (`guardian.md`, `delete_view.md`, `formsets.md`, `theme.md`), pairs `CHANGELOG.md` `### Breaking` entries with `docs/migrating-1.0.md` migration guidance (`D-14`), and executes the full regression matrix across both cached supported Django environments (`4.2` and `6.0`) plus `.venv/bin/mkdocs build --strict`, recording the measured evidence and Phase 7 stability-inventory handoff in `06.2-VALIDATION.md` and `06.2-ACCEPTANCE.md`.

### Strengths
- **Strict adherence to repository documentation and breaking-change conventions (`CLAUDE.md`, `D-14`):**
  - Every behavioral/contract change (HTTP `DELETE` 405 rejection, removal of `GuardianViewSet.cv_guardian_accept_global_perms`, `has_protected_objects` + filtered `protected_objects` context, per-view manage policy + strict helper in `guardian_config`, and fragment coordinate/ancestry validation) is paired across `CHANGELOG.md` (`### Breaking`), `docs/migrating-1.0.md`, and the reference docs, and verified via `.venv/bin/mkdocs build --strict`.
- **Runs both the targeted 17-file suite and the full `tests/test1` suite on both supported Django floors (`4.2` and `6.0`):**
  - Task `06-03` explicitly includes all six newly created test modules (`test_guardian_parent_none.py`, `test_guardian_inactive.py`, `test_fragment_authorization.py`, `test_guardian_policy.py`, `test_authorization_matrix.py`, `test_authorization_templates.py`) alongside the existing baseline and runs the full `tests/test1` directory under both `.nox/crispy_floor-3-12-django-6-0` and `.nox/crispy_floor-3-12-django-4-2`.
- **Explicit Phase 7 stability-inventory handoff (`06.2-ACCEPTANCE.md`):**
  - Capturing the finalized names (`has_protected_objects`, `protected_objects`, `guardian_config`, per-view manage policy keys, `GuardianViewSet` validator behavior, and fragment protocol) ensures Phase 7 (`STAB-01`–`STAB-06`) inventories the settled contracts rather than pre-6.2 behavior.

### Concerns
- **MEDIUM — Existing doc-fence extraction tests in `tests/test1/test_alerts.py` and `tests/test1/test_form_button_docs.py` enforce exact code-fence counts in specific sections of `docs/reference/theme.md` (`tests/test1/test_alerts.py:249-254`, `tests/test1/test_form_button_docs.py:168-174, 400-415`):**
  - In `tests/test1/test_alerts.py:249-254`, `_documented_alert_frame()` extracts `### Custom alert frame` under `## Alerts` in `docs/reference/theme.md` and asserts `assert len(bodies) == 1`.
  - In `tests/test1/test_form_button_docs.py:168-174`, `_theme_recipe()` extracts `## Custom form-button templates` in `docs/reference/theme.md` and unpacks `(code,) = FENCE.findall(section)` and `(template,) = TEMPLATE_FENCE.findall(section)` (requiring exactly one `python` fence and one `django`/`html` fence in that section), and similarly for `## Cancel links in custom form-button templates` (`line 243, 400+`).
  - If Task `06-02` adds a code or template fence inside any of those existing sections in `docs/reference/theme.md`, `test_alerts.py` or `test_form_button_docs.py` will fail during the full `tests/test1` run in Task `06-03`.
- **LOW — `docs/migrating-1.0.md` anchor links are asserted by existing doc tests (`tests/test1/test_label_mode_docs.py:267-270, 835-860`, `tests/test1/test_pagination_docs.py:167-170`):**
  - Existing tests in `test_label_mode_docs.py` and `test_pagination_docs.py` parse `CHANGELOG.md` (`## Unreleased` -> `### Breaking`) and `docs/migrating-1.0.md` using heading names (`_section(...)`). New `### Breaking` bullets and `docs/migrating-1.0.md` subsections must preserve all existing headings and anchor slugs.

### Suggestions
- When editing `docs/reference/theme.md` in Task `06-02`, place the new guidance on library-owned authorization and safe template contexts in its own `##` section (for example, at the end of `docs/reference/theme.md` after `## Disabled actions in overridden templates`, `theme.md:318-323`) rather than adding fences inside `## Custom form-button templates`, `## Cancel links in custom form-button templates`, or `### Custom alert frame`.
- Run `pytest tests/test1/test_alerts.py tests/test1/test_form_button_docs.py tests/test1/test_label_mode_docs.py tests/test1/test_pagination_docs.py` alongside `.venv/bin/mkdocs build --strict` in Task `06-02` to catch any doc-test interaction immediately.

### Risk Assessment
**LOW** — This is a documentation and verification plan with no production code edits. Keeping new `docs/reference/theme.md` content outside the fence-counted sections guarantees compatibility with existing documentation tests.

---

## Cross-Plan Comparison and Overall Risk Assessment

### Wave and Dependency Ordering
- **Wave 1 (`06.2-01`) → Wave 2 (`06.2-02`) → Wave 3 (`06.2-03` + `06.2-04`) → Wave 4 (`06.2-05`) → Wave 5 (`06.2-06`)** is well-structured:
  - `src/crud_views_guardian/lib/views.py` is modified in Wave 1 (`06.2-01`), Wave 2 (`06.2-02`), and Wave 3 (`06.2-04`), so serializing those three plans across Waves 1, 2, and 3 avoids merge conflicts.
  - The only parallel plans are `06.2-03` and `06.2-04` in Wave 3, whose `files_modified` sets are completely disjoint (`06.2-03` touches `src/crud_views/lib/formsets/*` and formset tests; `06.2-04` touches `src/crud_views_guardian/*`, manage templates, and Guardian policy tests).

### Top Cross-Plan Issues to Resolve Before Execution
1. **`06.2-01` (HIGH):** Include `src/crud_views/templates/crud_views/view_delete.content.html:8` (`{% if related_summary or has_protected_objects or protected_objects %}`) so the generic blocked-deletion alert is not skipped when `related_summary` is empty and all `protected_objects` are hidden by permission filtering.
2. **`06.2-02` (HIGH):** Preserve `GuardianCreateViewPermissionRequired.cv_has_access()`'s fallback (`src/crud_views_guardian/lib/views.py:206`) for active users when `obj` is not an instance of the parent model so `tests/test1/test_guardian.py:337-342` (`test_create_cv_has_access_child_wrong_type_obj`) continues to pass, while failing closed in `cv_create_has_access()` when `parent_obj` is `None` or wrong-typed.
3. **`06.2-03` (MEDIUM):** Account for the fact that `Author` (`tests/test1/app/models.py:13-14`) has no `ForeignKey`-related model in `tests/test1/app/models.py` when constructing UUID inline formset tests, and ensure `FormSet.init()` (`src/crud_views/lib/formsets/formsets.py:123`) / coordinate validation handles unsaved instances whose `UUIDField` has `default=uuid.uuid4`.

### Overall Risk Level
**MEDIUM** — The architectural approach across all six plans is sound, directly addresses every reproduced B1–B7 finding in the codebase, and maintains library-owned authorization and context safety without scope creep. Resolving the three concrete source-level findings above before or during execution will prevent test and template regressions.
