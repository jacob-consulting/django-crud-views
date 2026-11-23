---
last_mapped_commit: 3a28b40a2c700f23a61fad18eef0a2fe25b009c0
last_mapped_at: 2026-11-23
---
# Codebase Structure

**Analysis Date:** 2026-11-23

Scope: the reusable apps under `src/`, test harnesses under `tests/`, theme contracts under `docs/reference/`, and feature consumers under `examples/bootstrap5/`. Apply the developer-maintainability rule in `AGENTS.md` when choosing locations: use focused opt-in modules and keep shared request paths easy to trace.

## Directory Layout

```text
django-crud-views/
├── src/
│   ├── crud_views/                     # Core app (Bootstrap 5 theme)
│   │   ├── apps.py, checks.py          # AppConfig; Django system checks
│   │   ├── lib/                        # Runtime library (viewset, request, forms, bulk, diagnostics, theme JS/data-prefix registration, support)
│   │   ├── management/commands/        # cv_access, cv_manage_view, cv_manage_group, cv_assets, crud_views_show
│   │   ├── templatetags/               # crud_views.py, crud_views_formsets.py
│   │   ├── templates/crud_views/       # view_*.html, snippets/, tags/, formsets/, modal/, includes/ ...
│   │   ├── static/crud_views/{css,js}/ # core CSS/JS, including the UI adapter boundary
│   │   ├── locale/de/                  # translations
│   │   └── migrations/                 # empty package (no models)
│   ├── crud_views_guardian/            # django-guardian: lib/{viewset,mixins,views,ancestors}.py, checks.py
│   ├── crud_views_object_detail/       # lib/{views,mixins,config,resolvers,presentation,conf}.py, templatetags/, layout-pack templates, js
│   ├── crud_views_polymorphic/         # lib/{create,create_select,detail,update,delete,utils}.py
│   └── crud_views_workflow/            # lib/{views,mixins,execution,forms,widgets,enums}.py, models.py, migrations/, checks.py
├── tests/
│   ├── test1/                          # Django pytest project (main suite)
│   ├── browser/                        # Node *.test.cjs + Python fixture servers
│   ├── js/, js-integration/            # JavaScript unit/integration tests (vitest)
│   ├── lib/helper/                     # shared Python helpers
│   ├── conftest.py
│   └── check_manage_schema.py          # standalone validator of cv_manage_view exports
├── examples/bootstrap5/                # demo project + feature apps, including bulk_selection and navbar_demo
├── docs/                               # MkDocs source (reference/, getting_started/, development/)
├── scripts/                            # check_dist.py, generate_screenshots.py, wait_for_server.py
├── superpowers/                        # design notes, plans, specs, archives (committed)
├── .planning/                          # GSD state, phases, codebase maps
├── .github/                            # workflows (tests, lint, docs, js, publish, demo, readme-examples), templates
├── pyproject.toml, noxfile.py, taskfile.yaml
├── package.json, vitest.config.js, vitest.integration.config.js
├── mkdocs.yml, settings_i18n.py, render.yaml, codecov.yml
└── CHANGELOG.md, README.md, CLAUDE.md, AGENTS.md, CONTRIBUTING.md, SECURITY.md, AUDIT.md
```

Root also holds untracked/ignored build and report artifacts (`site/`, `dist/`, `node_modules/`, `coverage-*.xml`, `__pycache__/`); do not edit them.

Theme data-prefix registration is in `src/crud_views/lib/data_prefix.py`; four default component templates consume it across the actions menu, language selector, vertical tabs and accordion. `cv_config` supplies the same current value to the object-detail tab selector in `src/crud_views_object_detail/static/crud_views_object_detail/js/tabs.js`.

JavaScript theme defaults are registered independently in `src/crud_views/lib/js_config.py`: `register_js_namespace()` chooses the compatible global namespace and `register_tooltip_placements()` replaces the location map. The public functions are re-exported by `src/crud_views/lib/__init__.py`; a theme registers them in its `AppConfig.ready()`. At request render time, `src/crud_views/templatetags/crud_views.py` fills `#cv-config` via `src/crud_views/templates/crud_views/tags/cv_config.html`. Browser scripts use `src/crud_views/static/crud_views/js/adapters.js` as the UI library boundary; it resolves the selected global from rendered config when adapter methods run, allowing late-loaded config/library state without retrying or rebuilding existing UI instances.

## `src/crud_views/lib/` Map

```text
lib/
├── viewset/            __init__.py (ViewSet, _REGISTRY), parentviewset.py, path_regs.py
├── view/               base.py (CrudView, CrudViewPermissionRequiredMixin), meta.py, context.py,
│                       buttons.py, button_data.py, action_menu.py, label_mode.py, visibility.py,
│                       variant.py, cancel.py, card.py
├── views/              list, detail, create, update, delete, action, action_ordered, card, child,
│                       form, manage, mixins (+ __init__ re-exports)
├── bulk/               __init__.py (BulkSelectionMixin, BulkFormViewPermissionRequired, BulkConfirmForm)
├── ancestors.py        request-time ancestor authorization and child scoping
├── ancestor_policy.py  AncestorPolicy / AncestorPermissions (config values only)
├── ancestor_db.py      database-alias handling for ancestor reads
├── resource.py         Resource, ResourceMeta/ResourceOptions, ResourceViewMixin (leaf module)
├── access_trace.py     AccessTrace/AccessStep/AccessRecorder, get_recorder, recording, trace_access
├── access_trace_runner.py  synthetic-request runner, _run_trace
├── access_trace_export.py  Pydantic v1 wire models, validate_export, export_schema
├── navbar.py             NavBar/NavItem declarations, checks, request-local lazy builder and visibility
├── data_prefix.py        validated startup scalar for a theme's native data-API attribute prefix
├── js_config.py          startup JavaScript namespace + tooltip placement defaults for rendered #cv-config
├── manage_report.py    Pydantic wire models for cv_manage_view, adapt_section, report_schema
├── settings.py         CrudViewsSettings + crud_views_settings singleton
├── check.py            Check classes used by CrudView.checks()/ViewSet.checks()
├── assets.py, pipeline.py, vendor.py   asset registry, django-pipeline sources, vendoring
├── crispy/, table/, formsets/, conditional/   form/table/formset/conditional-field helpers
├── breadcrumb.py, icons.py, button_classes.py, messages.py, session.py, deletion.py, ordered.py,
│   lazy.py, exceptions.py, context_processor.py
```

## Directory Purposes

**`src/crud_views/lib/viewset/`:**
- Purpose: ViewSet declaration, registration, parent metadata, PK regexes.
- Key files: `src/crud_views/lib/viewset/__init__.py` (`ViewSet`, `_REGISTRY`, `_REGISTRY_LOCK`), `src/crud_views/lib/viewset/parentviewset.py`, `src/crud_views/lib/viewset/path_regs.py`.
- Add routing, naming, permission-map or per-ViewSet configuration fields here; never in consumer URLconfs.

**`src/crud_views/lib/view/`:**
- Purpose: behavior shared by every view (metaclass, base contract, action/button projection, label modes, cancel).
- Key files: `src/crud_views/lib/view/base.py`, `src/crud_views/lib/view/meta.py`.

**`src/crud_views/lib/bulk/` and bulk theme leaves:**
- Core implementation: `src/crud_views/lib/bulk/__init__.py` contains `BulkSelectionMixin`, `BulkConfirmForm`, `BulkFormViewPermissionRequired`, bounded ID normalization and request-local review data.
- Toolbar button rendering: `BulkSelectionMixin.cv_bulk_buttons` uses `src/crud_views/lib/view/button_data.py` with location `form`, then adds `destination.cv_action_variant` (unset renders `secondary`) and renders `src/crud_views/templates/crud_views/tags/button/bulk.html`. Keep this dedicated leaf separate from generic action leaves and the review form's Confirm button.
- Theme class registry: `src/crud_views/lib/button_classes.py` defines four `bulk:<variant>` defaults, mode-specific overrides and seven structural bulk slots. Bulk label mode comes from `src/crud_views/lib/view/label_mode.py`; unavailable icons force label mode before classes are selected.
- Entry-point boundary: `src/crud_views/lib/view/button_data.py` and `src/crud_views/templatetags/crud_views.py` reject direct generic rendering with location `bulk`; preserve these guards when changing normalization.
- Review rendering: `src/crud_views/templates/crud_views/view_bulk_form.html`, `view_bulk_form.content.html`, and `snippets/bulk/{blocked,eligible}.html`; transport stays in the content template while snippets own presentation.
- Reference consumer: `examples/bootstrap5/bulk_selection/views.py`; contract: `docs/reference/bulk_actions.md` and `docs/reference/buttons.md`.

**`src/crud_views/lib/navbar.py`:**
- Purpose: opt-in object-section navigation declaration and builder; mixin attaches lazy data to participating view contexts.
- Contains: `NavBar`, `NavItem`, `CrudViewNavBarMixin`, metadata-only `Check` integration and `_build()` destination/admission logic.
- Rendering is separate: three public tags are in `src/crud_views/templatetags/crud_views.py`; default theme wrapper and leaves are `src/crud_views/templates/crud_views/tags/navbar.html`, `navbar_identity.html`, and `navbar_items.html`.
- Add navigation behavior here; keep reusable presentation in theme templates and avoid adding navigation work to `CrudView` globally.

**Breadcrumb and table presentation files:**
- Hierarchy/context: `src/crud_views/lib/breadcrumb.py`; tag: `src/crud_views/templatetags/crud_views.py`; stock leaf: `src/crud_views/templates/crud_views/tags/breadcrumb.html`.
- Breadcrumb class defaults and theme registration: `src/crud_views/lib/button_classes.py`. Ordinary keys are `breadcrumb:list`, `breadcrumb:item`, and `breadcrumb:item-active`; use the registry for class-only changes.
- Table wrappers/columns: `src/crud_views/lib/table/`; view integration: `src/crud_views/lib/views/mixins.py`; stock table and `table.thead` override: `src/crud_views/templates/crud_views/table/bootstrap5.html`.
- The header projects `column.is_ordered` and `column.order_by_alias.is_descending` to icons and `aria-sort`, gated by `column.orderable`. Keep effective state in django-tables2 and preserve prefixed links with `cv_querystring`.

**Theme CSS tokens and compact formsets:**
- Token consumers: `src/crud_views/static/crud_views/css/manage.css` and `src/crud_views/static/crud_views/css/formset.css`. These use six `--cv-*` properties with Bootstrap-property and literal fallbacks; the package intentionally does not declare the custom properties globally.
- Theme contract and root-mapping guidance: `docs/reference/theme.md`. Map all six tokens on each theme root to allow nested modes to resolve against their local theme variables. Keep the use-site fallback chains, including the help button's `--bs-btn-color` assignment.
- Compact row shape and border state: `src/crud_views/static/crud_views/css/formset.css`; rendered headings: `src/crud_views/templates/crud_views/formsets/compact_headings.html`; field-grid declaration: `src/crud_views/lib/formsets/compact.py`.
- Preserve `gx-3` on both compact headings and field rows alongside `cv-formset-compact-headings` / `cv-formset-compact-fields`. Its 1rem gutter equivalence is specific to Bootstrap's standard spacing scale, not arbitrary customized Sass scales.

**Theme data-API prefix files:**
- Registration state/default and validation: `src/crud_views/lib/data_prefix.py`; public function: `src/crud_views/lib/__init__.py`.
- Simple tag, config context, and inclusion-tag wiring: `src/crud_views/templatetags/crud_views.py`; config leaf: `src/crud_views/templates/crud_views/tags/cv_config.html`.
- Four prefix-aware templates: `src/crud_views/templates/crud_views/tags/actions_menu_toggle.html`, `src/crud_views/templates/crud_views/snippets/language_selector.html`, `src/crud_views_object_detail/templates/crud_views_object_detail/layouts/tabs-vertical/object_detail.html`, and `src/crud_views_object_detail/templates/crud_views_object_detail/layouts/accordion/group.html`.
- Owned tab trigger selector: `src/crud_views_object_detail/static/crud_views_object_detail/js/tabs.js`; it reads `#cv-config[data-data-prefix]` at call time and falls back to `bs`.
- For new prefix-aware markup, use `{% cv_data_prefix %}` in the component template. For JS selectors, read `data-data-prefix` when selecting elements rather than capturing it at module load. Register the prefix in theme `AppConfig.ready()`.

**JavaScript theme configuration and adapter files:**
- Startup state and validation: `src/crud_views/lib/js_config.py`; public registration functions are re-exported from `src/crud_views/lib/__init__.py`. Register with `register_js_namespace(name)` and `register_tooltip_placements(mapping)` in a theme app's `AppConfig.ready()`; the latter replaces the complete mapping and both values are process-wide startup configuration.
- Render path: `src/crud_views/templatetags/crud_views.py` builds current values in `_cv_config_context()` for both `{% cv_config %}` and backwards-compatible `{% cv_const_js %}`. `src/crud_views/templates/crud_views/tags/cv_config.html` emits escaped namespace/placement attributes alongside request, CSRF and native-prefix values, then includes `crud_views/modal/shell.html`.
- Browser boundary: `src/crud_views/static/crud_views/js/adapters.js` initializes defaults on `globalThis.cv.adapters`, preserving earlier custom entries and exposing `cv.bootstrapAdapters(namespaceOrProvider)`. Its namespace provider reads `#cv-config[data-js-namespace]` when a component operation resolves; tooltip placement and native prefix are read at tooltip initialization. Core modules such as `modal.js`, `tooltip.js`, `list.filter.js`, and `viewset.js` use the adapter interface rather than accessing the UI library directly.
- Keep JS namespace, tooltip placement mapping, and native data prefix independent. A selected namespace with a missing component does not silently fall back to another library. When adding config attributes, update both the context and default config template, then preserve these values in theme overrides. Contract guidance is in `docs/reference/theme.md` and `docs/reference/javascript.md`.

**`src/crud_views/lib/views/`:**
- Purpose: one module per operation type; each combines `CrudView` with a Django generic view and has a `*PermissionRequired` variant.
- Key files: `src/crud_views/lib/views/list.py`, `src/crud_views/lib/views/create.py`, `src/crud_views/lib/views/delete.py`, `src/crud_views/lib/views/manage.py`, `src/crud_views/lib/views/mixins.py`.
- Public exports are listed in `src/crud_views/lib/views/__init__.py`. Import `ManageView` from `src/crud_views/lib/views/manage.py`, `CustomFormView*` from `src/crud_views/lib/views/form.py`, and polymorphic/workflow views from their extension apps; these are not in the core views barrel.

**`src/crud_views/lib/bulk/`:**
- Purpose: optional current-page selection controls and a reusable permission-gated bulk action destination.
- Key file: `src/crud_views/lib/bulk/__init__.py`; exports `BulkSelectionMixin`, `BulkFormViewPermissionRequired`, and `BulkConfirmForm`.
- Only actions whose destination passes `cv_has_access`/`cv_action_enabled` for the viewer are offered; with none, no toolbar or checkboxes render.
- Keep selection opt-in on table/card classes. The destination rechecks visibility and object eligibility; put app-specific writes in its `cv_form_valid()` implementation.
- Rendering lives in `src/crud_views/templates/crud_views/snippets/bulk_toolbar.html`, `columns/bulk_select.html`, `view_bulk_form.content.html`, and `snippets/bulk/`. Progressive enhancement is in `src/crud_views/static/crud_views/js/bulk.js`; list and card content templates include the toolbar when actions are declared.
- The consumer example is `examples/bootstrap5/bulk_selection/views.py`; its model, routes, seed data and tests are in that app directory.

**Diagnostics files:**
- `src/crud_views/lib/views/manage.py`: nine `get_manage_*` builders, `manage_export()`, access-trace form query/projection.
- `src/crud_views/lib/manage_report.py`: wire models and `adapt_section`; `src/crud_views/management/commands/cv_manage_view.py` consumes them.
- `src/crud_views/lib/access_trace.py`, `access_trace_runner.py`, `access_trace_export.py`: trace model, runner, export contract; `src/crud_views/management/commands/cv_access.py` consumes them.
- `src/crud_views/templates/crud_views/view_manage.html`, `src/crud_views/templates/crud_views/includes/access_trace.html`, `src/crud_views/static/crud_views/js/manage.js`, `src/crud_views/static/crud_views/css/manage.css`: manage page rendering.
- `docs/reference/cv_manage_view.schema.json`: committed generated schema (regenerate through `cv_manage_view --schema`).

**`src/crud_views/management/commands/`:**
- `cv_access.py` (trace CLI), `cv_manage_view.py` (configuration CLI), `cv_manage_group.py` (ensures `CRUD_VIEWS_MANAGE_GROUP` exists), `cv_assets.py` (asset delivery table/JSON), `crud_views_show.py` (no-op placeholder).
- Keep argument parsing, rendering and exit codes here; delegate to `lib/`.
- Runtime wire contracts stay separate: `cv_manage_view` uses `src/crud_views/lib/manage_report.py`; `cv_access` uses `src/crud_views/lib/access_trace_export.py`. Keep contract changes with their own validators, schemas and tests.

**`src/crud_views/templates/crud_views/` and `static/crud_views/`:**
- Templates: top-level `view_<op>.html` plus `.content.html` (modal/body), `snippets/{action,action_short,header,paragraph,message,alert,delete}/<key>.html` (per-view text templates referenced by `cv_*_template`), `tags/` (template-tag partials), `columns/`, `crispy/`, `formsets/`, `conditional/`, `modal/`, `shared/` (`css.html`, `js.html`), `table/`.
- Static: `css/{formset,icons,manage,property,table}.css`; `js/{adapters,bulk,formset,list.filter,manage,modal,toggle,tooltip,viewset}.js`.

**Extension apps** (`src/crud_views_*/`):
- Guardian: `src/crud_views_guardian/lib/viewset.py` (`GuardianViewSet`), `mixins.py`, `views.py` (`Guardian*ViewPermissionRequired`, `GuardianManageView`), `ancestors.py`; template `templates/crud_views/view_guardian_manage.html`.
- Object detail: `src/crud_views_object_detail/lib/views.py`, `mixins.py`, `config.py`, `resolvers.py`, `presentation.py`, `conf.py`, `templatetags/crud_views_object_detail.py`, layout packs under `templates/crud_views_object_detail/layouts/`, field types under `types/default/`.
- Polymorphic: `src/crud_views_polymorphic/lib/create_select.py` (type picker), `create.py`, `detail.py`, `update.py`, `delete.py`, `utils.py`.
- Workflow: `src/crud_views_workflow/lib/views.py` (`WorkflowView`), `execution.py` (`run_transition`), `mixins.py` (`WorkflowModelMixin`), `forms.py`, `widgets.py`, `models.py` (`WorkflowInfo`), `migrations/0001_initial.py`, `0002_rename_workflow_object_id_to_pk.py`.

**`tests/test1/`:**
- Main Django/pytest project configured in `tests/test1/conftest.py`; models in `tests/test1/app/models.py`; URLs in `tests/test1/project/urls.py`.
- Groups by prefix: `test_access_trace_*.py` (recorder, runner, command, contract, ancestors, guardian, resources, safety, docs, locales), `test_manage_*.py` (report, export, command, command_ci, access_trace, resource and guardian manage), `test_resource_*.py`, `test_ancestor_*.py`, `test_action_menus_*.py` (+ `golden/` snapshots), `test_assets*.py`, `od/` (object detail) with `od_app/` fixtures.
- Fixtures for the CLI: `tests/test1/access_trace_cli_fixture.py`.

**`tests/browser/`, `tests/js/`, `tests/js-integration/`:** Node harnesses (`*.cjs`, `*.test.cjs`) paired with Python fixture servers (`*_server.py`), e.g. `tests/browser/access-trace.test.cjs` with `tests/browser/access_trace_server.py`.

**`examples/bootstrap5/`:** `project/` (settings, URLs, base templates, `features.py` catalog, `seeding.py`, `management/commands/seed.py`), plus one app per feature (`library`, `nested`, `resources`, `navbar_demo`, `guardian_demo`, `workflow`, `polymorphic_demo`, `object_detail`, `formsets`, `conditional`, `action_menus`, `label_modes`, `breadcrumbs`, `theming`, ...). `navbar_demo` is an independent opt-in consumer: declarations/views in `examples/bootstrap5/navbar_demo/views.py`, routes in `urls.py`, wrapper in `templates/navbar_demo/crud_base.html`, app-local models/seed/static/tests, mounted at `/object-navbar/` in `examples/bootstrap5/project/urls.py`. It demonstrates the package API and does not define package runtime behavior. Doc-sync tests: `examples/bootstrap5/test_docs_sync.py`, `test_doc_links.py`, `test_i18n.py`.

**`docs/`:** `docs/reference/*.md` (one page per feature, including `navbar.md`, `manage.md`, `resources.md`, `nested.md`, `guardian.md`), `docs/getting_started/`, `docs/development/` (`i18n.md`, `stability.md`), `docs/migrating-1.0.md`, `docs/reference/cv_manage_view.schema.json`. Navigation: `mkdocs.yml`.

**`.planning/`:** `PROJECT.md`, `REQUIREMENTS.md`, `ROADMAP.md`, `STATE.md`, `state.json`, `config.json`, `codebase/`, `phases/`, `quick/`, `research/`, `notes/`, `intel/`, `debug/`, `ui-reviews/`. Phase artifacts stay in `.planning/phases/<phase>/`.

## Key File Locations

**Entry Points:**
- `src/crud_views/apps.py`: AppConfig; `ready()` imports `crud_views.checks`.
- `src/crud_views/lib/viewset/__init__.py`: `ViewSet`, `.register`, `.urlpatterns`.
- `src/crud_views/management/commands/cv_access.py`, `src/crud_views/management/commands/cv_manage_view.py`: diagnostics CLIs.
- `examples/bootstrap5/project/urls.py`, `examples/bootstrap5/manage.py`: demo wiring.

**Configuration:**
- `pyproject.toml` (metadata, ruff 120 cols, hatchling), `src/crud_views/lib/settings.py` (`CRUD_VIEWS_*`), `src/crud_views_object_detail/lib/conf.py`, `noxfile.py`, `taskfile.yaml`, `package.json`, `vitest.config.js`, `mkdocs.yml`, `.pre-commit-config.yaml`.
- Theme-native data prefix is registered by theme app startup through `crud_views.lib.register_data_prefix()`; it is a process-wide module scalar defaulting to `bs`, not a `CRUD_VIEWS_*` setting.
- CSS token values belong to the consumer theme and its theme-root selectors; there is no package setting or global token declaration. See `docs/reference/theme.md` and the stock consumers in `src/crud_views/static/crud_views/css/manage.css` and `formset.css`.

**Core Logic:**
- `src/crud_views/lib/view/meta.py`, `src/crud_views/lib/view/base.py`, `src/crud_views/lib/ancestors.py`, `src/crud_views/lib/resource.py`, `src/crud_views/lib/access_trace_runner.py`, `src/crud_views/lib/manage_report.py`.

**Contracts (machine-readable output):**
- `src/crud_views/lib/manage_report.py` (`report_schema`), `docs/reference/cv_manage_view.schema.json`, `src/crud_views/lib/access_trace_export.py` (`export_schema`), `tests/check_manage_schema.py`, `tests/test1/test_access_trace_contract.py`.

**Testing:**
- `tests/test1/conftest.py`, `tests/test1/app/models.py`, `tests/conftest.py`, `tests/lib/helper/`.

## Naming Conventions

**Files:**
- Python modules: lowercase snake_case (`access_trace_runner.py`, `parentviewset.py`).
- Management commands: command name equals module (`cv_access.py`, `cv_manage_view.py`; legacy `crud_views_show.py`).
- Templates: `view_<key>.html` with `.content.html` body variants; per-view text snippets under `snippets/<kind>/<key>.html`.
- Python tests: `tests/test1/test_<feature>.py`; Node tests `*.test.cjs` with a same-stem harness and `*_server.py`.
- Extension modules inside `lib/` named after the view or concern.

**Code:**
- `CrudView` attributes use the `cv_` prefix; internal helpers `_cv_*`; manage builders `get_manage_*` and `_manage_*`.
- View keys: `list`, `detail`, `create`, `update`, `delete`, `workflow`, `manage`.
- Wire-model names: nouns (`ViewRow`, `HolderRow`, `Step`, `PlanRow`); enum-like values are `Literal[...]` snake_case strings.

**Directories:**
- Importable packages are lowercase; optional integrations are separate `crud_views_<name>` roots under `src/`.

## Where to Add New Code

**Breadcrumb styling and table-header changes:**
- Class defaults/registration: `src/crud_views/lib/button_classes.py`; markup: `src/crud_views/templates/crud_views/tags/breadcrumb.html`. Keep trail construction in `src/crud_views/lib/breadcrumb.py` separate from styling. The final item's `aria-current="page"` remains when class contributions are empty.
- Header presentation: `src/crud_views/templates/crud_views/table/bootstrap5.html`. Use bound-column effective ordering for default/constructor/request/prefixed sorts; the stock header owns `aria-sort`, so remove caller-supplied collisions or override `table.thead`.
- Tests: `tests/test1/test_breadcrumb.py` (default bytes, class precedence, empty/non-string overrides and semantics), `tests/test1/test_button_classes.py` (defaults), and `tests/test1/test_table_template.py` (effective state, links and escaping).
- References: `docs/reference/buttons.md`, `docs/reference/breadcrumb.md`, `docs/reference/theme.md`, and `docs/reference/list_view.md`; feature announcement: `CHANGELOG.md`.

**New view type or shared view behavior:**
- Operation handler: new module in `src/crud_views/lib/views/` plus `*PermissionRequired` variant and export in `__init__.py`.
- Shared behavior: `src/crud_views/lib/view/base.py` or a focused module in `src/crud_views/lib/view/`.
- Templates/snippets: `src/crud_views/templates/crud_views/`.
- Validation: add `Check` objects in the view's `checks()` (`src/crud_views/lib/check.py`) or a Django check in `src/crud_views/checks.py`.
- Tests: `tests/test1/test_<feature>.py`.

**Bulk selection/action changes:**
- Core API and checks: `src/crud_views/lib/bulk/__init__.py`.
- Toolbar payload normalization: keep `cv_button_data(raw, "form")` in `BulkSelectionMixin.cv_bulk_buttons`, apply the bulk label-mode floor with icon fallback, then add the destination variant. Do not route location `bulk` through `cv_button_data()` or `cv_button`; both reject that entry point (`src/crud_views/lib/view/button_data.py`, `src/crud_views/templatetags/crud_views.py`).
- Toolbar presentation: `src/crud_views/templates/crud_views/tags/button/bulk.html`; classes: `bulk:<variant>` or `bulk:<variant>:<mode>` in `src/crud_views/lib/button_classes.py`. Preserve native submit attributes, `form:hidden-label`, host icon handling and form tooltip location. Review Confirm continues through `form:submit`.
- Shared presentation: `src/crud_views/templates/crud_views/snippets/bulk_toolbar.html`, `columns/bulk_select.html`, `view_bulk_form.content.html`, and `snippets/bulk/`.
- Selection transport: `_read_ids()` in `src/crud_views/lib/bulk/__init__.py` owns canonicalization/deduplication/overlap checks; raw count limits run before normalization. Keep numeric hidden IDs and card checkbox values unlocalized in the content/card templates.
- List/card integration: `src/crud_views/templates/crud_views/view_list_table.content.html` and `view_card.content.html`; table selection is contributed through `BulkSelectionMixin.get_table_kwargs()`.
- Example consumer and package reference: `examples/bootstrap5/bulk_selection/views.py`, `examples/bootstrap5/bulk_selection/tests.py`, and `docs/reference/bulk_actions.md`.
- Core test coverage is grouped in `tests/test1/test_bulk_*.py`; browser behavior is in `tests/js/bulk.test.js`.
- Semantic class, normalization boundary, icon and raw-byte compatibility checks: `tests/test1/test_bulk_variants.py` (live comparison with the unchanged form leaf, no fixture). ID/stage/review checks: `tests/test1/test_bulk_flow.py`; source markup/localization: `tests/test1/test_bulk_source.py`.

**Object navbar change:**
- Declaration, request-local lazy builder, destination validation and admission: `src/crud_views/lib/navbar.py`.
- Rendering tag changes: `src/crud_views/templatetags/crud_views.py`; theme wrapper/identity/items: `src/crud_views/templates/crud_views/tags/navbar*.html`.
- Consumer composition: `examples/bootstrap5/navbar_demo/views.py` and `templates/navbar_demo/crud_base.html`; package contract reference: `docs/reference/navbar.md`.
- Focused checks: `tests/test1/test_navbar.py`, `test_navbar_checks.py`, `test_navbar_templates.py`, `test_navbar_permissions.py`, and `test_navbar_costs.py`.

**Theme data-prefix change:**
- Startup API and validation: `src/crud_views/lib/data_prefix.py`, exported from `src/crud_views/lib/__init__.py`.
- Template tag and config value: `src/crud_views/templatetags/crud_views.py`, `src/crud_views/templates/crud_views/tags/cv_config.html`.
- Component templates and selector: the four paths above and `src/crud_views_object_detail/static/crud_views_object_detail/js/tabs.js`.
- Contract and focused tests: `docs/reference/theme.md`, `docs/reference/javascript.md`, `docs/reference/object_detail_layout_packs.md`, `tests/test1/test_data_prefix.py`, and `tests/test1/test_data_prefix_docs.py`.

**JavaScript namespace / tooltip defaults:**
- Registration state and validation: `src/crud_views/lib/js_config.py`; public exports: `src/crud_views/lib/__init__.py`.
- Rendered configuration: `src/crud_views/templatetags/crud_views.py` and `src/crud_views/templates/crud_views/tags/cv_config.html`; retain all config attributes when overriding the template.
- Adapter implementation and consuming scripts: `src/crud_views/static/crud_views/js/adapters.js`, `modal.js`, `tooltip.js`, `list.filter.js`, and `viewset.js`. Keep library-specific behavior behind `cv.adapters` and resolve the provider at operation time.
- Contract and focused tests: `docs/reference/theme.md`, `docs/reference/javascript.md`, `tests/test1/test_js_config.py`, and JavaScript adapter suites under `tests/js/` and `tests/js-integration/`.

**New ViewSet option:**
- Field on `ViewSet` in `src/crud_views/lib/viewset/__init__.py` (add a validator if constrained), consider a global default in `src/crud_views/lib/settings.py`, expose in manage (`get_manage_facts`/`get_manage_presentation` in `src/crud_views/lib/views/manage.py`) and, if it appears in the report, in `src/crud_views/lib/manage_report.py` plus the committed schema.

**New setting:**
- Field in `CrudViewsSettings` (`src/crud_views/lib/settings.py`); validation goes in `check_messages`; document in `docs/reference/settings.md`.

**Theme palette or compact formset styling:**
- Stock token consumers: `src/crud_views/static/crud_views/css/manage.css` and `src/crud_views/static/crud_views/css/formset.css`; retain the six documented `--cv-*` fallback chains and existing component selectors.
- Theme mappings and nested theme-root behavior: `docs/reference/theme.md`. Add mappings in a consumer theme's stylesheet, not package settings or upstream `:root` declarations.
- Compact headings and field gutters: `src/crud_views/templates/crud_views/formsets/compact_headings.html` and `src/crud_views/lib/formsets/compact.py`; keep `gx-3` on each row plus the existing `cv-formset-*` classes.

**New authorization gate or trace fact:**
- Record beside the enforcing gate via `get_recorder()` (`src/crud_views/lib/view/base.py`, `src/crud_views/lib/ancestors.py`, `src/crud_views_guardian/lib/mixins.py`, `src/crud_views/lib/views/manage.py`); add any new `kind`/`result`/`provider` literal to `src/crud_views/lib/access_trace_export.py`; tests in `tests/test1/test_access_trace_*.py`.

**New manage/report section or field (cv_manage_view):**
- Builder in `ManageView` -> model in `src/crud_views/lib/manage_report.py` -> branch in `adapt_section` and `InspectionData`/`SectionKey` -> text rendering in `_format_text` of `src/crud_views/management/commands/cv_manage_view.py` -> schema file `docs/reference/cv_manage_view.schema.json` -> tests `tests/test1/test_manage_report.py`, `test_manage_export.py`, `test_manage_command.py`. Update `docs/reference/manage.md` and, when a `### Breaking` entry is added to `CHANGELOG.md`, `docs/migrating-1.0.md`.

**New Resource-backed view:**
- Subclass `Resource` in the consumer app, implement `cv_get_items`, build a `ViewSet(model=..., resource_permissions=...)`, put `ResourceViewMixin` first in view bases. Tests: `tests/test1/test_resource_*.py`.

**New optional integration:**
- New root `src/crud_views_<name>/` with `apps.py`, `lib/`, optional `templates/`, `locale/`, `checks.py`; keep core free of its imports; add to `pyproject.toml` package list and `I18N_PACKAGES` in `taskfile.yaml`; tests in `tests/test1/`.

**Examples and docs:**
- Feature demo: matching app under `examples/bootstrap5/`, registered in `examples/bootstrap5/project/features.py`.
- Reference page: `docs/reference/`; add to `mkdocs.yml`.

## Special Directories

**`src/*/migrations/`:** Django migrations; only `src/crud_views_workflow/migrations/` has schema; `src/crud_views/migrations/` is an empty package. Committed.
**`.planning/phases/`:** phase plans/receipts, committed; some `.gitkeep`/`.review-inputs/` entries are untracked.
**`superpowers/`:** committed design notes and archives (`notes/`, `plans/`, `specs/`, `archive/`).
**`site/`, `dist/`, `node_modules/`, `.venv/`, `.nox/`:** generated and git-ignored (confirmed for `site`, `dist`, `node_modules`).
**`src/*/locale/`:** `.po/.mo` translation catalogues (`de`); `src/crud_views_workflow/locale/` exists *(contents not read)*.

---

*Structure analysis: 2026-11-23*
