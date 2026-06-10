# Design: DetailCustomView

## Problem

The existing `DetailView` requires `ObjectDetailMixin` and `cv_property_display` to render object details. There is no way to use a completely custom template for displaying an object without the django-object-detail machinery.

## Solution

Extract a base `DetailCustomView` from the existing `DetailView`. `DetailCustomView` provides the "detail" role in a ViewSet (key, path, icons, snippets, context actions) without `ObjectDetailMixin`. `DetailView` inherits from `DetailCustomView` and adds `ObjectDetailMixin` + `cv_property_display`.

## Class Hierarchy

```
DetailCustomView = CrudView + generic.DetailView
    template_name = "crud_views/view_detail_custom.html"
    cv_key = "detail"
    cv_path = "detail"
    cv_context_actions, cv_icon_action, snippet templates

DetailView = ObjectDetailMixin + DetailCustomView
    template_name = "crud_views/view_detail.html"   (overrides parent)
    cv_property_display + checks()

DetailCustomViewPermissionRequired = CrudViewPermissionRequiredMixin + DetailCustomView
DetailViewPermissionRequired = CrudViewPermissionRequiredMixin + DetailView

GuardianDetailCustomViewPermissionRequired = Guardian mixins + DetailCustomViewPermissionRequired
GuardianDetailViewPermissionRequired = Guardian mixins + DetailViewPermissionRequired  (unchanged)
```

## Changes

### 1. `crud_views/lib/views/detail_custom.py` (new)

New file containing `DetailCustomView` and `DetailCustomViewPermissionRequired`. Holds all shared detail view attributes: `cv_key`, `cv_path`, `cv_context_actions`, snippet templates, `cv_icon_action`.

Uses `template_name = "crud_views/view_detail_custom.html"` — a minimal wrapper with an empty `cv_content` block that the user overrides.

### 2. `crud_views/templates/crud_views/view_detail_custom.html` (new)

Minimal template: extends `cv_extends`, provides empty `cv_content` block. Users override `template_name` to point to their own template.

### 3. `crud_views/lib/views/detail.py` (modify)

Refactor `DetailView` to inherit from `DetailCustomView` instead of `CrudView + generic.DetailView` directly. Move shared attributes to `DetailCustomView`. `DetailView` keeps only `ObjectDetailMixin`, `template_name` override, `cv_property_display`, and `checks()`.

### 4. `crud_views/lib/views/__init__.py` (modify)

Export `DetailCustomView` and `DetailCustomViewPermissionRequired`.

### 5. `crud_views/lib/view/__init__.py` (no change needed)

### 6. `crud_views_guardian/lib/views.py` (modify)

Add `GuardianDetailCustomViewPermissionRequired` following the same pattern as `GuardianDetailViewPermissionRequired`.

### 7. `tests/test1/test_detail_custom.py` (new)

Tests:
- `DetailCustomView` renders with a custom template
- `DetailCustomView` returns 200 with object context
- `DetailCustomViewPermissionRequired` returns 403 without permission
- Existing `DetailView` still works unchanged (regression)

### 8. `examples/bootstrap5/app/views/book.py` (modify)

Replace `BookDetailView` base class from `GuardianDetailViewPermissionRequired` to `GuardianDetailCustomViewPermissionRequired` with a custom template. Remove `cv_property_display`.

### 9. `examples/bootstrap5/app/templates/app/book_detail.html` (new)

Custom book detail template used by the example.

### 10. `docs/reference/detail_custom_view.md` (new)

Document `DetailCustomView` with usage examples and comparison to `DetailView`.

### 11. `skills/django-crud-views/SKILL.md` (modify)

Add `DetailCustomView` section.

## Backwards Compatibility

Fully backwards compatible. `DetailView` inherits from `DetailCustomView` now, but its public API and behavior are identical. Existing code using `DetailView` or `DetailViewPermissionRequired` is unchanged.
