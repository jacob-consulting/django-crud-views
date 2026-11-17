---
last_mapped_commit: 54c18a1b65f038e5fcdb5dc0038782133f93ffb8
last_mapped_at: 2026-11-17
---
# Codebase Structure

**Analysis Date:** 2026-11-17

Paths were verified to exist at mapping time. Items marked *(inferred)* were not read in detail.

## Directory Layout

```text
django-crud-views/
├── src/
│   ├── crud_views/                     # Core app (Bootstrap 5 theme)
│   │   ├── apps.py, checks.py          # AppConfig; Django system checks
│   │   ├── lib/                        # Runtime library (see below)
│   │   ├── management/commands/        # cv_access, cv_manage_view, cv_manage_group, cv_assets, crud_views_show
│   │   ├── templatetags/               # crud_views.py, crud_views_formsets.py
│   │   ├── templates/crud_views/       # view_*.html, snippets/, tags/, formsets/, modal/, includes/ ...
│   │   ├── static/crud_views/{css,js}/ # core CSS/JS
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
├── examples/bootstrap5/                # demo project + feature apps
├── docs/                               # MkDocs source (reference/, getting_started/, development/)
├── scripts/                            # check_dist.py, generate_screenshots.py, wait_for_server.py
├── superpowers/                        # design notes, plans, specs, archives (committed)
├── .planning/                          # GSD state, phases, codebase maps
├── .github/                            # workflows (tests, lint, docs, js, publish, demo, readme-examples), templates
├── pyproject.toml, noxfile.py, taskfile.yaml, uv.lock
├── package.json, vitest.config.js, vitest.integration.config.js
├── mkdocs.yml, settings_i18n.py, render.yaml, codecov.yml
└── CHANGELOG.md, README.md, CLAUDE.md, AGENTS.md, CONTRIBUTING.md, SECURITY.md, AUDIT.md
```

Root also holds untracked/ignored build and report artifacts (`site/`, `dist/`, `node_modules/`, `coverage-*.xml`, `__pycache__/`); do not edit them.

## `src/crud_views/lib/` Map

```text
lib/
├── viewset/            __init__.py (ViewSet, _REGISTRY), parentviewset.py, path_regs.py
├── view/               base.py (CrudView, CrudViewPermissionRequiredMixin), meta.py, context.py,
│                       buttons.py, button_data.py, action_menu.py, label_mode.py, visibility.py,
│                       variant.py, cancel.py, card.py
├── views/              list, detail, create, update, delete, action, action_ordered, card, child,
│                       form, manage, mixins (+ __init__ re-exports)
├── ancestors.py        request-time ancestor authorization and child scoping
├── ancestor_policy.py  AncestorPolicy / AncestorPermissions (config values only)
├── ancestor_db.py      database-alias handling for ancestor reads
├── resource.py         Resource, ResourceMeta/ResourceOptions, ResourceViewMixin (leaf module)
├── access_trace.py     AccessTrace/AccessStep/AccessRecorder, get_recorder, recording, trace_access
├── access_trace_runner.py  synthetic-request runner, _run_trace
├── access_trace_export.py  Pydantic v1 wire models, validate_export, export_schema
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

**`src/crud_views/lib/views/`:**
- Purpose: one module per operation type; each combines `CrudView` with a Django generic view and has a `*PermissionRequired` variant.
- Key files: `src/crud_views/lib/views/list.py`, `src/crud_views/lib/views/create.py`, `src/crud_views/lib/views/delete.py`, `src/crud_views/lib/views/manage.py`, `src/crud_views/lib/views/mixins.py`.
- Public exports are listed in `src/crud_views/lib/views/__init__.py` (note: `ManageView`, `CustomFormView*` and the polymorphic/workflow views are imported from their modules or apps *(inferred from `__all__` contents)*).

**Diagnostics files:**
- `src/crud_views/lib/views/manage.py`: nine `get_manage_*` builders, `manage_export()`, access-trace form query/projection.
- `src/crud_views/lib/manage_report.py`: wire models and `adapt_section`; `src/crud_views/management/commands/cv_manage_view.py` consumes them.
- `src/crud_views/lib/access_trace.py`, `access_trace_runner.py`, `access_trace_export.py`: trace model, runner, export contract; `src/crud_views/management/commands/cv_access.py` consumes them.
- `src/crud_views/templates/crud_views/view_manage.html`, `src/crud_views/templates/crud_views/includes/access_trace.html`, `src/crud_views/static/crud_views/js/manage.js`, `src/crud_views/static/crud_views/css/manage.css`: manage page rendering.
- `docs/reference/cv_manage_view.schema.json`: committed generated schema (regenerate through `cv_manage_view --schema`).

**`src/crud_views/management/commands/`:**
- `cv_access.py` (trace CLI), `cv_manage_view.py` (configuration CLI), `cv_manage_group.py` (ensures `CRUD_VIEWS_MANAGE_GROUP` exists), `cv_assets.py` (asset delivery table/JSON), `crud_views_show.py` (no-op placeholder).
- Keep argument parsing, rendering and exit codes here; delegate to `lib/`.

**`src/crud_views/templates/crud_views/` and `static/crud_views/`:**
- Templates: top-level `view_<op>.html` plus `.content.html` (modal/body), `snippets/{action,action_short,header,paragraph,message,alert,delete}/<key>.html` (per-view text templates referenced by `cv_*_template`), `tags/` (template-tag partials), `columns/`, `crispy/`, `formsets/`, `conditional/`, `modal/`, `shared/` (`css.html`, `js.html`), `table/`.
- Static: `css/{formset,icons,manage,property,table}.css`; `js/{adapters,formset,list.filter,manage,modal,toggle,tooltip,viewset}.js`.

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

**`examples/bootstrap5/`:** `project/` (settings, URLs, base templates, `features.py` catalog, `seeding.py`, `management/commands/seed.py`), plus one app per feature (`library`, `nested`, `resources`, `guardian_demo`, `workflow`, `polymorphic_demo`, `object_detail`, `formsets`, `conditional`, `action_menus`, `label_modes`, `breadcrumbs`, `theming`, ...). Each has `views.py`, `urls.py`, `seed.py`, `tests.py`. Doc-sync tests: `examples/bootstrap5/test_docs_sync.py`, `test_doc_links.py`, `test_i18n.py`.

**`docs/`:** `docs/reference/*.md` (one page per feature, including `manage.md`, `resources.md`, `nested.md`, `guardian.md`), `docs/getting_started/`, `docs/development/` (`i18n.md`, `stability.md`), `docs/migrating-1.0.md`, `docs/reference/cv_manage_view.schema.json`. Navigation: `mkdocs.yml`.

**`.planning/`:** `PROJECT.md`, `REQUIREMENTS.md`, `ROADMAP.md`, `STATE.md`, `state.json`, `config.json`, `codebase/`, `phases/`, `quick/`, `research/`, `notes/`, `intel/`, `debug/`, `ui-reviews/`. Phase artifacts stay in `.planning/phases/<phase>/`.

## Key File Locations

**Entry Points:**
- `src/crud_views/apps.py`: AppConfig; `ready()` imports `crud_views.checks`.
- `src/crud_views/lib/viewset/__init__.py`: `ViewSet`, `.register`, `.urlpatterns`.
- `src/crud_views/management/commands/cv_access.py`, `src/crud_views/management/commands/cv_manage_view.py`: diagnostics CLIs.
- `examples/bootstrap5/project/urls.py`, `examples/bootstrap5/manage.py`: demo wiring.

**Configuration:**
- `pyproject.toml` (metadata, ruff 120 cols, hatchling), `src/crud_views/lib/settings.py` (`CRUD_VIEWS_*`), `src/crud_views_object_detail/lib/conf.py`, `noxfile.py`, `taskfile.yaml`, `package.json`, `vitest.config.js`, `mkdocs.yml`, `.pre-commit-config.yaml`.

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

**New view type or shared view behavior:**
- Operation handler: new module in `src/crud_views/lib/views/` plus `*PermissionRequired` variant and export in `__init__.py`.
- Shared behavior: `src/crud_views/lib/view/base.py` or a focused module in `src/crud_views/lib/view/`.
- Templates/snippets: `src/crud_views/templates/crud_views/`.
- Validation: add `Check` objects in the view's `checks()` (`src/crud_views/lib/check.py`) or a Django check in `src/crud_views/checks.py`.
- Tests: `tests/test1/test_<feature>.py`.

**New ViewSet option:**
- Field on `ViewSet` in `src/crud_views/lib/viewset/__init__.py` (add a validator if constrained), consider a global default in `src/crud_views/lib/settings.py`, expose in manage (`get_manage_facts`/`get_manage_presentation` in `src/crud_views/lib/views/manage.py`) and, if it appears in the report, in `src/crud_views/lib/manage_report.py` plus the committed schema.

**New setting:**
- Field in `CrudViewsSettings` (`src/crud_views/lib/settings.py`); validation goes in `check_messages`; document in `docs/reference/settings.md`.

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

*Structure analysis: 2026-11-17*
