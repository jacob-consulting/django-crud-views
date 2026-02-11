# Django CRUD Views - Changelog

## 0.1.0

- Updated development status from Alpha to Beta
- Fixed `OrderedDownView.down()` calling `up()` instead of `down()`
- Added comprehensive test suite covering:
  - INT primary key models (`Publisher`)
  - Nested `ParentViewSet` with parent-child relationships (`Book` under `Publisher`)
  - `django-filter` integration (`ListViewTableFilterMixin`)
  - `MessageMixin` flash messages on create/update/delete
  - Form validation: missing fields, CSRF enforcement, re-render on invalid POST
  - Ordered action views (up/down) with edge cases and permissions
  - Auto-registered manage views with context introspection
  - Polymorphic views: create-select, subtype-specific create/update, detail, delete
- Cleaned up `test_factory.py` dead code

## Unreleased

- Replaced custom detail view property system (`PropertyGroup`, `Property`, `PropertyInfo`, renderers, `@cv_property` decorator, tabs) with [django-object-detail](https://django-object-detail.readthedocs.io/en/latest/)
- Detail views now use `property_display` (from django-object-detail) instead of `cv_property_groups`
- Removed `@cv_property` decorator — use model-level `@property` methods instead
- Removed tabs functionality
- Removed `Detail2View` custom template_name per-group feature
- Added `django-object-detail` to project dependencies
- Added `OBJECT_DETAIL_*` settings for Font Awesome icons and split-card layout
- Updated bootstrap5 examples with icons, descriptions, and property details
