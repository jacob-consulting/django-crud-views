# Django CRUD Views - Changelog

## Unreleased

### Added

- View-level context buttons: set `cv_context_buttons` on a `CrudView` (a list of `ContextButton`s) to define buttons for a single view instead of the whole ViewSet. View-level buttons override ViewSet-level ones with the same `key`; they render only when the key is listed in `cv_context_actions`, matching existing button behavior.
- `FilterContextButton` now honors `label_template` / `label_template_code`, so the filter toggle's label (default `Filter`) can be customized like any other context button.

## 0.7.1

### Added

- `cv_context_url` template tag: resolves the permission-gated target URL for a context-button key — the same context resolution as `cv_context_button` — but returns just the URL string, or `None` when the user lacks access or the action is disabled (`cv_action_enabled` is `False`). Use it to build your own link/tile markup in custom templates: `{% cv_context_url "update" as edit_url %}{% if edit_url %}…{% endif %}`. The object defaults to the view's current object; pass a second argument to target another. Documented in the Context Buttons reference (new "Manual Placement (Template Tags)" section) alongside `cv_context_button` and the `cv_context_has_permission` filter.

## 0.7.0

### Added

- ViewSet-level `extends` field to override the base template for all views in a ViewSet; resolution order is view (`cv_extends_template`) → ViewSet (`extends`) → global (`CRUD_VIEWS_EXTENDS`). Override templates are validated at startup (`crud_views.viewset.E111`).
- `SiblingContextButton`: a context button on a child view that links to a *sibling* collection — another child of the same parent — by reusing the parent PK already present in the current URL. Declare it with `sibling_name` (the sibling child ViewSet) and an optional `sibling_key` (defaults to `list`, auto-falling back to `card` when no `list` view is registered). Only renders on child views (those with a parent); access and `cv_action_enabled` are evaluated against the sibling collection view
- Context button templating & manual placement: `ContextButton` now accepts `template`/`template_code` to render the whole button (not just its label, which `label_template`/`label_template_code` still cover), defaulting to the new `CRUD_VIEWS_CONTEXT_BUTTON_TEMPLATE` setting (default `crud_views/tags/context_action.html`). Place a single button anywhere with `{% cv_context_button "key" %}` (object defaults to the view's object; renders nothing when access is denied — unlike the `{% cv_context_actions %}` container, which greys it out); render a custom loop via `view.cv_get_context_buttons` (access-filtered) + `{% cv_render_context_button ctx %}`; and gate surrounding markup with the `view|cv_context_has_permission:"key"` filter
- Pinned filter: set `cv_filter_pinned = True` on a filtered `ListView`/`CardListView` (or the global `CRUD_VIEWS_FILTER_PINNED` setting, default `False`) to render the filter always-open and hide the filter toggle button. Filter field values are still persisted to the session via `cv_filter_persistence`; only the now-irrelevant expanded/collapsed state is dropped (bootstrap5 renders the filter without its collapse wrapper; the plain theme is unaffected)
- `cv_is_active` is now populated for all context buttons (previously only view-key buttons), so `{% cv_context_button %}` highlights when it points at the current page. Matched by URL router name.
- `ActionView` now evaluates its action result and emits a Django message: a success message (`cv_message_template`/`cv_message_template_code`) on a truthy result and an error message (new `cv_message_template_error`/`cv_message_template_error_code`) on a falsy result. Emission is built in (no `MessageMixin` needed); disable per view with `cv_action_messages = False` or by leaving the templates unset. As a result, `OrderedUpView`/`OrderedDownView` now show their "Moved … up/down" messages automatically.

### Fixed

- Guardian: a custom `ContextButton` whose `key` differs from its `key_target` and that targets a child viewset's `create` view is no longer always rendered as "no access" on list pages. The Guardian list mixin now resolves the button's `key_target` before re-deriving create access, so any create button (not just the built-in `"create"`) gets the parent-object permission check — enabling, e.g., a second differently-styled create button on the same page
- `ParentContextButton`: a parent button targeting an object-permission-gated parent view (e.g. the parent's `detail`) is no longer wrongly hidden on object-less child pages (list/card). Access is now checked against the resolved **parent object** (via `cv_get_parent_object()`) rather than the current view's object, so the button reflects whether the user can access that parent — the same gate as opening the parent detail page directly. The default `parent`→list button is unaffected
- `ParentContextButton` now honors its own `label_template`/`label_template_code` like the other button types (`ContextButton`, `ChildContextButton`, `SiblingContextButton`), instead of silently rendering the target (parent) view's default action label. When no label is set it still falls back to that default. The label-rendering step is now shared via a `ContextButton._apply_label()` helper so no button subclass can omit it
- `MessageMixin`'s error path could never fire (its `cv_get_message` ignored the requested attribute and it guarded on an undefined `cv_error_message`). The success/error message renderer now lives on `CrudView.cv_get_message(*, error=False)`, returns `None` when unconfigured instead of raising, and the dead `MessageMixin.action()` wrapper was removed.
- bootstrap5 example: `CampaignWorkflowView` listed a non-existent `"edit"` context-action key, raising `ViewSetKeyFoundError` ("key edit not registered at campaign") and a 500 on the campaign workflow page. Corrected to `"update"`, the registered key.
- bootstrap5 example: the `/parent/` list 500'd because `ParentTable.id` (a `UUIDLinkDetailColumn`) linked to a `detail` view the parent ViewSet never registered, raising `ViewSetKeyFoundError` ("key detail not registered at parent"). Added the missing `ParentDetailView`.

### Changed

- Formsets: `FormSet.fields` and `FormSet.pk_field` are now optional and derived from the formset `klass` (the inline form's fields and the child model's primary-key name) when omitted; pass them explicitly only to override. New `FormSet.form_show_labels` (default `False`) controls crispy label rendering for inline-formset rows instead of the previously hardcoded value.
- Renamed `crud_views.lib.formsets.mixins.PolymorphicFormSetMixin` to `PolymorphicFormSetsViewMixin`; the old name collided with django-polymorphic's `Polymorphic*FormSet` classes. This formsets API is semi-private, so the rename ships without a deprecation shim — update any `from crud_views.lib.formsets.mixins import PolymorphicFormSetMixin` imports to the new name.

## 0.6.0

### Added

- Card views: `CardOrderMixin` adds whitelisted queryset ordering — declare sortable fields via `cv_order_fields` (`"name"` or `("name", "Label")`) and an optional `cv_order_default` (e.g. `"-name"`). Order field/direction are read from the `cv_order_param`/`cv_order_dir_param` query params and validated against the whitelist, so arbitrary `order_by` input is rejected
- Card views: order-by combo + direction-toggle toolbar, and pagination controls (set `paginate_by` per view to enable). Active filter and ordering are preserved across submits, paging, and reset so all three stay in sync
- New `cv_action_enabled(user, obj)` hook — a secondary action gate evaluated only after `cv_has_access` passes. `cv_has_access` answers "may you do this in principle?" (permission); `cv_action_enabled` answers "is this action currently applicable to *this* object?" (state) — e.g. a locked parent disables child create/delete. Both must be true for the action button to render and the request to be allowed (default: enabled). Enforced for both the plain (`has_permission`) and guardian (`get_object`/`dispatch`) permission paths; the `cv_get_action_object()` helper resolves the relevant object (the instance for object-views, the parent for child create-views). Button/companion-form guards apply across list, context, and card views in the bootstrap5 and plain themes
- New `CRUD_VIEWS_STRICT` setting (defaults to `DEBUG`): in strict mode, exceptions previously swallowed by `ignore_exception` (e.g. unknown view keys in `cv_context_action` template tags or table link columns) are raised so misconfigurations fail loudly during development; in non-strict mode they are logged as warnings under the `crud_views` logger hierarchy
- Logging: swallowed/narrowed exceptions in `DeleteView.cv_get_related_object_url` and the guardian create-button parent resolution are now logged instead of silently ignored

### Fixed

- The filter-persistence endpoint returns 400 (Bad Request) for a malformed JSON body instead of a 500
- `SessionData` no longer writes partial state to the session when the with-block raised
- `cv_check_delete_protection()` runs once per DELETE POST (was called twice)

- Removed all import-time `get_user_model()` calls: `WorkflowInfo.user` now references `settings.AUTH_USER_MODEL` (Django's documented pattern for swappable user models, migration-identical), templatetag modules import without the app registry, and type hints in `lib.view.base` moved under `TYPE_CHECKING`

- Settings checks: a missing `CRUD_VIEWS_EXTENDS` now produces a clear "setting CRUD_VIEWS_EXTENDS is not set" check error instead of crashing; an invalid `CRUD_VIEWS_MANAGE_VIEWS_ENABLED` value is reported (`crud_views.E101`); repeated check runs no longer accumulate duplicate messages

- View registration no longer mutates the context-action lists owned by the settings singleton (copy-on-write when adding the `manage` action), and it now honors `CRUD_VIEWS_MANAGE_VIEWS_ENABLED="no"` instead of an unconditional `if True`

- Formsets: a form/x-form mismatch during nested formset save now raises `CrudViewError` instead of failing silently (the previous `assert Exception(...)` never raised)
- Formsets: fixed an inner loop shadowing the `index` parameter in `FormSet.init()`/`FormSet.template()`, which corrupted prefixes when initializing multiple forms with 2+ child formsets
- Formsets: `PolymorphicFormSetMixin.cv_get_formsets()` now returns `None` for polymorphic models without formsets, as documented, instead of raising `ValueError`
- Formsets: the AJAX formset-template endpoint now returns 400 (Bad Request) for unknown formset keys or a non-integer `num` instead of a 500
- System checks: custom check messages passed to `Check.get_message()` are no longer discarded; `CheckEitherAttribute` now emits its two distinct messages
- System checks: crud_views checks are now registered under the `crud_views` tag (was a leftover placeholder tag `my_new_tag`)
- UUID primary keys: URL patterns now accept any UUID version (previously only version-4 UUIDs matched, so uuid1/uuid7 PKs produced 404s)
- Packaging: the `all` extra now includes `guardian`; fixed the malformed `Repository` URL in `pyproject.toml`
- Example app: fixed a bootstrap5 demo startup crash caused by a duplicate `poly` ViewSet name — the formset polymorphic ViewSet is renamed to `poly_formset` to resolve the collision

### Changed

- **Behavior change:** create/update/delete views no longer decide between create and update by swallowing `AttributeError` from `get_object()`; the object is resolved structurally via `cv_object`. A genuine error inside a custom `get_object()`/queryset now propagates instead of silently running the create path
- `CustomFormNoObjectView` now sets `cv_object = False` explicitly
- Registering two ViewSets under the same name now raises `ViewSetError` instead of silently overwriting the first registration

### Internal

- Pre-commit now runs `ruff check` in addition to `ruff format`
- Removed the stale `docs/tbd/` outline; documented the process-lifetime permission caching of `ViewSet.default_permissions` in the settings reference

- TODO triage: all 37 inline `# todo` markers removed — meaningful ones converted to GitHub issues #27–#34, stale ones and commented-out code blocks deleted

- Renamed `crud_views/lib/formsets/x.py` to `render_tree.py` with a module docstring explaining the XForm/XFormSet render-tree model; renamed `XFormSet.start_at_rows` to `render_rows_only` (semi-private formsets API)

- New nested-formset test suite (Publisher → Book → BookNote) raising formsets coverage from 34–62% to 78–100%; total coverage 95% with a `fail_under = 88` CI gate
- `task bump-patch` now invokes `bump-my-version` (was the unrelated `bumpver` tool); removed the nonexistent `bootstrap5` extra from `noxfile.py`
- Moved internal planning artifacts from `docs/superpowers/` to `superpowers/` so they are no longer built into the documentation site

## 0.5.0

### Changed: `django-ordered-model` is now an optional dependency

- `django-ordered-model` is no longer installed by default — install it via the `ordered` extra: `pip install django-crud-views[ordered]` (also included in the `all` extra)
- Added `get_ordered_model` lazy-import helper so `crud_views.lib.formsets` and the ordered up/down actions import cleanly when the package is absent
- Removed the top-level `ordered_model` import from `formsets.py`; `OrderedCheckBase` now resolves the model through `get_ordered_model`
- New `check_ordered_model_installed` Django system check errors only when a ViewSet actually uses ordering but the `ordered` extra is not installed

> **Upgrade note:** if you use ordered list actions and previously relied on `django-ordered-model` being pulled in automatically, add the `[ordered]` extra to your install.

### Internal

- Migrated the project to a `src/` layout (all packages moved under `src/`); the built wheel is byte-for-byte identical, so there is no change for installed users
- CI: force the codecov action's transitive `actions/github-script` onto Node 24 to clear the Node 20 deprecation warning

## 0.4.3

- Added `crud_views_guardian` to the packaged views list in `pyproject.toml`

## 0.4.2

- Fixed CSRF token handling — the token is now added to `cvGetConfig` instead of being queried from the DOM (strict CSP compatibility)

## 0.4.1

- Excluded the `superpowers` folder from mkdocs navigation

## 0.4.0

### New: `crud_views_guardian` — django-guardian per-object permission support

- Added `crud_views_guardian` sub-package with `GuardianViewSet` and per-object permission checking via django-guardian
- `GuardianListViewPermissionRequired`, `GuardianDetailViewPermissionRequired`, `GuardianCreateViewPermissionRequired`, `GuardianUpdateViewPermissionRequired`, `GuardianDeleteViewPermissionRequired` — drop-in replacements for standard permission-required views
- `GuardianCardListViewPermissionRequired`, `GuardianDetailCustomViewPermissionRequired` — guardian variants for card and custom detail views
- `GuardianManageView` — displays guardian configuration, per-object permission holders, and object counts
- `GuardianObjectPermissionMixin`, `GuardianQuerysetMixin`, `GuardianParentPermissionMixin` — composable mixins for custom guardian views
- `cv_guardian_anonymous_behavior` setting to redirect or deny anonymous users
- `cv_guardian_accept_global_perms` viewset field to control whether global permissions grant access
- Guardian-aware cascading delete display with per-object permission filtering

### New: `CardListView` — card-based list view

- Added `CardListView` and `CardListViewPermissionRequired` — renders objects as Bootstrap cards instead of table rows
- `CardAction` Pydantic model for per-card button configuration with `key`, `label`, `variant`, `flex`, `no_label`, and `child_name` fields
- `cv_card_action` supports child viewset links via `child_name` for cross-viewset card actions
- `cv_card_template` attribute for model-specific custom card templates
- `cv_card_container_class` attribute for configurable card grid layout (default: `col-md-6`)
- `cv_card` and `cv_card_action` template tags for rendering cards and actions
- Default icon changed to `fa-solid fa-rectangle-list`

### New: `DetailCustomView` — custom template detail view

- Extracted `DetailCustomView` as a base class for detail views with full custom template control (no `ObjectDetailMixin`)
- Same `cv_key = "detail"` registration as `DetailView` — use when you want to write your own detail template
- `GuardianDetailCustomViewPermissionRequired` guardian variant

### New: Improved `DeleteView` — cascading deletes and delete protection

- Delete confirmation page now shows all related objects that will be cascade-deleted, grouped and linked
- `cv_check_delete_protection` runs on both GET and POST — hides the delete form when deletion is blocked by protected relations
- Related objects display supports dict-based tree structure with linking to detail views
- Guardian-aware: cascading delete display filters objects by per-object permissions

### New: `ContextButton` improvements

- Added `ChildContextButton` for linking to child viewsets from context action bars
- `ContextButton` resolves "list" to "card" when list view is not registered (fallback)
- `cv_user_in_group` template tag to check group membership in templates

### New: `ManageView` improvements

- `manage_view_class` field on `ViewSet` and `CRUD_VIEWS_MANAGE_VIEW_CLASS` setting for custom manage view subclasses
- `CRUD_VIEWS_GUARDIAN_MANAGE_VIEW_CLASS` setting for custom guardian manage views
- `CRUD_VIEWS_MANAGE_GROUP` setting for group-based manage view access
- `CRUD_VIEWS_MANAGE_SHOW_USERS` setting to show user column in permission holders
- `ManageView` always auto-registered, access controlled by `manage_views_enabled` setting

### CSP compatibility

- Fully compatible with strict Content Security Policy — no inline scripts, inline event handlers, inline styles, or `javascript:` URIs
- New `{% cv_config %}` template tag replaces `{% cv_const_js %}` (backwards-compatible alias retained)
- `{% cv_csrf_token %}` template tag removed — CSRF token read from DOM at point of use
- All interactive behavior handled via event delegation in external `viewset.js`
- Formset CSS animations extracted to `formset.css` static file
- Cancel buttons use anchor `<a href>` instead of `onclick` handlers
- Crispy forms cancel button uses `data-cv-cancel-url` attribute instead of `onclick`

### Other improvements

- `cv_header_icon_class` and `cv_filter_icon_class` simple template tags for icon CSS classes
- ViewSet `get_view_class()` falls back from `list` to `card` key when list view is not registered
- Filter form helper now receives view context

### Bug fixes

- Fixed guardian create button visibility — `cv_create_has_access` now correctly checks permissions
- Fixed guardian list button visibility for per-object permission views
- Fixed anonymous user handling in guardian views (redirect instead of 500)
- Fixed `cv_guardian_accept_global_perms` not being respected in create access checks
- Fixed permission holder queries not scoped to `app_label` in ManageView
- Fixed `ContextButton` failing on child ViewSets without a list view
- Fixed empty string and type assertion for user in context methods
- Fixed `BookReviewDetailView` missing `cv_property_display` configuration in bootstrap5 example
- Added create context action to `BookReviewCardListView` in bootstrap5 example

## 0.3.12

- Fixed `view_delete.content.html` rendering the raw `{{ object }}` string above the delete confirmation form

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
