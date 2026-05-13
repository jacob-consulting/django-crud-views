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
