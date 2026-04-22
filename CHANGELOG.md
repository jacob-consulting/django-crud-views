# Django CRUD Views - Changelog

## 0.3.11

- Fixed `TemplateSyntaxError` caused by the `{% querystring %}` template tag being renamed to `{% querystring_replace %}` in django-tables2 3.0. Updated `crud_views/templates/crud_views/table/bootstrap5.html` to use the new tag name. The old template is preserved as `bootstrap5_lt3.html` for use with django-tables2 < 3.0.

## 0.3.10

- Fixed `TemplateColumn.render()` signature in `ActionColumn`, `LinkChildColumn`, and `UUIDColumn` to be compatible with django-tables2 2.9.x, which changed the method signature from positional `(record, table, value, bound_column, **kwargs)` to `(table, **kwargs)`

## 0.3.9

- Completed German i18n coverage for bootstrap5 example: wrapped all untranslated strings in views (`bar`, `baz`, `foo`, `book`, `campaign`, `detail`, `group`, `group_members`, `author`) with `gettext_lazy`
- Fixed `gettext` → `gettext_lazy` in `detail.py`, `group.py`, `group_members.py` for correct runtime translation of class-level strings
- Fixed wrong entity name in `group.py` cv_messages ("author" → "group")
- Added missing German translations for singular verbose names (`Author`, `Book`) and nav strings
- Cleaned up all fuzzy entries in `crud_views` and `bootstrap5` German `.po` files; corrected bad fuzzy suggestions
- Updated `crud_views` templates: translation strings changed from multiline to single-line `msgid` format
- Added `settings_i18n.py` — minimal Django settings file for running `makemessages`/`compilemessages` without a full project settings module
- Added taskfile tasks: `msg-make-crud_views`, `msg-comp-crud_views`, `msg-make-example`, `msg-comp-example`
- Updated i18n developer documentation with taskfile commands and fuzzy flag guidance

## 0.3.8

- Improved bootstrap5 example: `book_count` is now resolved via the view-callable fallback (view method) while `full_name` is annotated as coming from the model, making the distinction clear

## 0.3.7

- Added documentation and examples for the django-object-detail View-Callable Fallback feature: view methods are called when a `cv_property_display` path is not found on the model instance

## 0.3.6

- Added `docs/reference/custom_form_view.md` documenting `CustomFormView`, `CustomFormViewPermissionRequired`, `CustomFormNoObjectView`, and `CrispyModelViewMixin`
- Added unit tests for `CustomFormView` / `CustomFormViewPermissionRequired` and `CrispyModelViewMixin`

## 0.3.5

- Moved `django-ordered-model` to optional dependency group `ordered` (`pip install django-crud-views[ordered]`)
- Added `docs/reference/ordered_view.md` documenting the ordered views

## 0.3.4

- Moved `BadgeEnum` from `crud_views_workflow.lib.mixins` to `crud_views_workflow.lib.enums`
- Renamed `WorkflowMixin` to `WorkflowModelMixin`

## 0.3.3

- Added `BadgeEnum` (`StrEnum`) covering all Bootstrap contextual colours; use as values in `STATE_BADGES`
- Renamed `WorkflowMixin.STATE_ENUM` → `STATE_CHOICES` and `STATE_BADGES_DEFAULT` → `STATE_BADGE_DEFAULT`
- Fixed `WorkflowMixin.get_state_badge` to render a badge with `STATE_BADGE_DEFAULT` for states absent from `STATE_BADGES` (previously returned plain text)

## 0.3.2

- Changed `WorkflowInfo.workflow_object_id` (PositiveBigIntegerField) to `workflow_object_pk` (CharField, max_length=255) to support UUID, integer, and string primary keys
- Added compound index on `(workflow_object_pk, workflow_object_content_type)` for efficient history lookups

## 0.3.1

- Fixed bug in `WorkflowMixin` using `model.id` instead of `model.pk`
- Added ruff lint GitHub Actions workflow; publish now depends on lint passing
- Added lint badge to README

## 0.3.0

- Added `crud_views_polymorphic` package — polymorphic CRUD views built on `django-polymorphic`
  - `PolymorphicCreateSelectView` / `PolymorphicCreateSelectViewPermissionRequired` — two-step create flow: select subtype then fill subtype form
  - `PolymorphicCreateView`, `PolymorphicUpdateView`, `PolymorphicDetailView`, `PolymorphicDeleteView` and their `PermissionRequired` variants
  - `cv_polymorphic_exclude` / `cv_polymorphic_include` to filter available subtypes; system check `E220` enforces mutual exclusivity
  - Added `PolymorphicView` reference documentation
- `crud_views_workflow` restructured into `lib/` subpackage; `WorkflowComment` extracted as top-level enum (`crud_views_workflow.lib.enums`)
- Added `WorkflowViewPermissionRequired` — enforces `change` permission on workflow views
- Added `WorkflowView.checks()` — validates `form_class`, transition/comment labels, `WorkflowMixin` on model, and required model attributes `STATE_ENUM` / `STATE_BADGES` (checks E230–E235)
- Added `cv_property_display` class attribute to `DetailView` for declarative property group configuration
- Restructured `pyproject.toml`: bootstrap5 deps moved to core dependencies; `workflow`, `polymorphic`, and `all` optional extras added
- Added ruff as formatter and linter, replacing black; ruff pre-commit hook added
- Added `pytest-xdist` for parallel test execution (`-n auto`); nox sessions run in parallel (`-p`)

## 0.2.1
- short app label `cvw` for app `crud_views_workflow`

## 0.2.0

- Added `crud_views_workflow` package: FSM-based workflow views built on `django-fsm-2`
  - `WorkflowMixin` for models — state badges, transition helpers, audit history via `WorkflowInfo`
  - `WorkflowView` — renders available transitions as a radio-select form with optional/required comment support
  - `WorkflowForm` — crispy-forms form with dynamic choices and per-transition comment validation
  - `WorkflowInfo` model — generic foreign key audit log recording every state transition, actor, comment and timestamp
  - `Comment.NONE / OPTIONAL / REQUIRED` per-transition comment requirement declared via `@transition(custom={...})`
  - `on_transition` hook for post-transition side effects
  - Campaign example added to the bootstrap5 example app
- Added unit tests for `crud_views_workflow` (38 tests covering mixin, view, and form behaviour)
- Added `WorkflowView` reference documentation
- Updated nox test matrix to install the `workflow` extra

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
