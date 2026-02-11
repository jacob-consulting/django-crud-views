# Django CRUD Views - Changelog

## Unreleased

- Replaced custom detail view property system (`PropertyGroup`, `Property`, `PropertyInfo`, renderers, `@cv_property` decorator, tabs) with [django-object-detail](https://django-object-detail.readthedocs.io/en/latest/)
- Detail views now use `property_display` (from django-object-detail) instead of `cv_property_groups`
- Removed `@cv_property` decorator — use model-level `@property` methods instead
- Removed tabs functionality
- Removed `Detail2View` custom template_name per-group feature
- Added `django-object-detail` to project dependencies
- Added `OBJECT_DETAIL_*` settings for Font Awesome icons and split-card layout
- Updated bootstrap5 examples with icons, descriptions, and property details
