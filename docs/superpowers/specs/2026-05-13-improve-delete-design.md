# Improve DeleteView: Cascading Deletes Display & Delete Protection

## Overview

Enhance the `DeleteView` with two features:

1. **Cascading deletes display** — show users what related objects will be deleted via CASCADE, similar to Django Admin
2. **Delete protection** — a hook for custom business logic that can prevent deletion

Both features are opt-in and backward-compatible.

## Approach

Use Django's `NestedObjects` collector (from `django.contrib.admin.utils`) to discover related objects. The view collects the data and passes it to the template context. A separate included template renders the nested tree. This is the same proven pattern Django Admin has used since Django 1.x.

## Cascading Deletes Display

### View Attributes

New class attributes on `DeleteView`:

- `cv_show_related_objects: bool = False` — opt-in to show cascading deletes
- `cv_link_related_objects: bool = False` — opt-in to render related objects as links to their detail views (requires registered ViewSets with detail views)

### Data Collection

**`cv_get_related_objects(self)`** — uses Django's `NestedObjects` collector (from `django.contrib.admin.utils`) to discover all objects that will be cascade-deleted. Returns a dataclass (or named tuple) with three fields:

- `tree: list` — nested list of related objects, where each item is `(model_instance, children_list)`
- `summary: dict[str, int]` — maps model verbose name to count, e.g. `{"Book": 3, "Contract": 1}`
- `protected: list` — objects with `on_delete=PROTECT` relations that would block deletion at the database level

Note: `django.contrib.admin.utils.NestedObjects` is a semi-public API that Django Admin has used since Django 1.x. It is stable and widely relied upon by third-party packages.

### Permission Filtering

**`cv_filter_related_objects(self, user, related_tree)`** — walks the tree and for each model checks if the user has `view` permission:

- **Permitted**: show full details (`str(obj)`, optional link)
- **Restricted**: replace with aggregated count, e.g. "3 Book objects"

This gives users full impact visibility without leaking details of objects they can't normally see.

### Context Data

When `cv_show_related_objects` is `True`, `get_context_data()` adds:

- `related_objects` — the filtered nested tree
- `related_summary` — the `{model_verbose_name: count}` summary
- `protected_objects` — list of protected objects (if any)

### Templates

Related objects display is rendered via included templates, so projects can override them:

- **`crud_views/snippets/delete/related_objects.html`** — main included template, rendered inside the delete content template when `cv_show_related_objects` is `True` and there are related objects
- **`crud_views/snippets/delete/related_objects_tree.html`** — recursive include for rendering the nested tree (each level includes itself for children)

**Rendering behavior:**

- Summary section at the top: "Deleting this Publisher will also delete: 3 Books, 1 Contract"
- Nested tree below with the actual objects, indented by depth
- When `cv_link_related_objects` is `True` and a ViewSet with a detail view exists for the related model, the object renders as a link; otherwise plain text
- For restricted models (user lacks view permission): "3 Book objects" without individual details
- If protected objects are found: a warning message indicating deletion will be blocked

**Placement:** the include goes into `view_delete.content.html`, between the paragraph ("Delete Publisher «Acme»") and the form. The user sees what will be affected before interacting with the confirmation checkbox.

## Delete Protection

### View-Side Hook

**`cv_check_delete_protection(self) -> list[str]`** — returns a list of error message strings. Empty list means deletion is allowed. Developers override this to add custom business logic.

Called inside `cv_form_valid()`, after the form's own validation has passed but before `self.object.delete()`. If it returns errors, the form is re-rendered with those errors as non-field errors. The object is not deleted.

**Default implementation:** returns an empty list (no protection).

This is distinct from database-level `on_delete=PROTECT` (which is detected by the collector and surfaced via `protected_objects` in the template context). `cv_check_delete_protection()` is for custom business logic — e.g., "cannot delete a publisher with active contracts."

### Form-Side Hook

Standard Django `clean()` on the form class is also respected. Developers who prefer form-level validation can create a custom form subclass. Errors surface as non-field errors via crispy forms rendering.

The existing `CrispyDeleteForm` stays unchanged.

### Execution Order

1. Form validates (checkbox confirmed, form `clean()` passes)
2. Inside `cv_form_valid()`, the view calls `cv_check_delete_protection()`
3. If protection errors are returned, form re-renders with those errors as non-field errors
4. If no errors, `self.object.delete()` proceeds

## Guardian Integration

### Per-Object Permission Checking

`GuardianDeleteViewPermissionRequired` overrides `cv_filter_related_objects()` to use per-object permission checks instead of model-level checks.

**Behavior:**

- For each related object, check if the user has the object-level `view` permission
- Permitted objects: show full details
- Restricted objects: aggregate into counts

### Performance

Uses `guardian.shortcuts.get_objects_for_user` for bulk queryset filtering — one query per related model, not one per object.

### Implementation Location

A new `GuardianDeleteRelatedObjectsMixin` in `crud_views_guardian/lib/views.py`, composed into `GuardianDeleteViewPermissionRequired`.

## Documentation

Update the existing mkdocs documentation to cover the new features.

### `docs/reference/delete_view.md`

Add sections for:

- **Cascading Deletes Display** — explain `cv_show_related_objects` and `cv_link_related_objects` attributes, with a code example showing opt-in usage
- **Delete Protection** — explain `cv_check_delete_protection()` hook with a code example showing custom business logic (e.g., preventing deletion of a publisher with active contracts), and mention that form `clean()` is also respected
- **Configuration table** — add the new `cv_show_related_objects` and `cv_link_related_objects` attributes to the existing configuration table
- **Template Customization** — document the included templates (`crud_views/snippets/delete/related_objects.html`, `crud_views/snippets/delete/related_objects_tree.html`) and how projects can override them

### `docs/reference/guardian.md`

Add a section for:

- **Cascading Deletes with Per-Object Permissions** — explain that `GuardianDeleteViewPermissionRequired` uses per-object `view` permission checks when filtering related objects, with bulk queryset filtering for performance. Note that objects the user lacks permission to view are shown as aggregated counts.

## Skill Update

### `skills/django-crud-views/references/api-reference.md`

Update the existing DeleteView section to include:

- `cv_show_related_objects` and `cv_link_related_objects` attributes in the code example
- `cv_check_delete_protection()` method signature and brief description
- Mention of the cascading deletes feature in the `CrispyDeleteForm` description

## Unit Tests

### `tests/test1/` — crud_views tests

Add a new test file `tests/test1/test_delete.py` covering:

- **Related objects display (off by default):** GET the delete page for a Publisher with Books — verify the response does NOT contain related object information when `cv_show_related_objects` is `False` (default)
- **Related objects display (opt-in):** create a DeleteView variant with `cv_show_related_objects = True`, GET the delete page for a Publisher with Books — verify the response contains the related Book objects in the context (`related_objects`, `related_summary`)
- **Related objects linking:** create a DeleteView variant with both `cv_show_related_objects = True` and `cv_link_related_objects = True` — verify the response contains links to related objects that have registered ViewSets with detail views
- **Protected objects display:** add a new test model (or a new FK on an existing test model) with `on_delete=PROTECT` pointing to Publisher, enable `cv_show_related_objects` — verify the response contains protected object warnings in the context and that the template renders a warning
- **Permission filtering:** test that a user without `view` permission on the related model sees counts ("3 Book objects") instead of individual object details
- **Delete protection (view hook):** create a DeleteView with `cv_check_delete_protection()` returning error messages — POST the delete form and verify the object is NOT deleted and the errors appear as non-field errors
- **Delete protection (form clean):** create a custom form with `clean()` raising `ValidationError` — POST the delete form and verify the object is NOT deleted
- **Successful delete still works:** verify that with `cv_show_related_objects = True`, a POST with confirmed checkbox still deletes the object and its CASCADE relations

Test views and ViewSets needed for these tests should be defined in `tests/test1/app/views.py` (or inline in the test file if simpler). The Publisher → Book relationship already exists with `on_delete=CASCADE` and can be reused.

### `tests/test1/` — crud_views_guardian tests

Add delete-specific tests to `tests/test1/test_guardian.py` (or a new `tests/test1/test_guardian_delete.py`) covering:

- **Guardian per-object filtering:** create a Guardian DeleteView with `cv_show_related_objects = True` — assign `view` permission on some related objects but not others — verify the user sees details for permitted objects and counts for restricted ones
- **Guardian bulk filtering performance:** verify that the guardian variant uses queryset-based filtering (not per-object checks) by confirming the related objects context is correct with a reasonable number of related objects
