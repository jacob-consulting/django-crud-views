# Django CRUD Views - Changelog

## 0.1.3

- Made Bootstrap 5 the default theme — templates in `crud_views/` now ship with Bootstrap 5 styling out of the box
- Moved plain (unstyled) templates to a new `crud_views_plain` override package
- Removed `CRUD_VIEWS_THEME` setting (no longer needed; theme is determined by installed apps)

## 0.1.2

- Auto-detect `pk` regex from model's primary key field (`UUIDField` → UUID, `CharField`/`SlugField` → STR, integer fields → INT), removing the need to manually specify `pk=ViewSet.PK.UUID`
- Auto-derive `model` from `cv_viewset` in `CrudView` subclasses

## 0.1.1

- Added `polymorphic` extra to nox test sessions

## 0.1.0

- Updated development status from Alpha to Beta
- Fixed `OrderedDownView.down()` calling `up()` instead of `down()`
- Added a comprehensive test suite covering:
  - INT primary key models (`Publisher`)
  - Nested `ParentViewSet` with parent-child relationships (`Book` under `Publisher`)
  - `django-filter` integration (`ListViewTableFilterMixin`)
  - `MessageMixin` flash messages on create/update/delete
  - Form validation: missing fields, CSRF enforcement, re-render on invalid POST
  - Ordered action views (up/down) with edge cases and permissions
  - Auto-registered manage views with context introspection
  - Polymorphic views: create-select, subtype-specific create/update, detail, delete
- Cleaned up `test_factory.py` dead code

## 0.0.11

- Replaced custom detail view property system (`PropertyGroup`, `Property`, `PropertyInfo`, renderers, `@cv_property` decorator, tabs) with [django-object-detail](https://django-object-detail.readthedocs.io/en/latest/)
