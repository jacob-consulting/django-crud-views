---
last_mapped_commit: db82bc76f38fdba7396dcdf93e5edd637e44ac8e
last_mapped_at: 2026-11-15
---
# Codebase Structure

**Analysis Date:** 2026-11-15

## Directory Layout

```text
django-crud-views/
├── src/
│   ├── crud_views/                    # Core Django app
│   │   ├── lib/                        # ViewSet, CBVs, authorization, forms and support
│   │   ├── management/commands/        # Package Django commands, including cv_access
│   │   ├── templates/crud_views/       # Core Bootstrap 5 templates and partials
│   │   └── static/crud_views/          # Core CSS/JavaScript
│   ├── crud_views_guardian/            # django-guardian integration
│   ├── crud_views_object_detail/       # ObjectDetailView and property presentation
│   ├── crud_views_polymorphic/         # django-polymorphic flows
│   └── crud_views_workflow/            # django-fsm integration and history models
├── tests/
│   ├── test1/                          # Django integration/unit test project
│   ├── js/                             # JavaScript unit tests
│   ├── js-integration/                 # JavaScript integration tests
│   ├── browser/                        # Browser tests and fixture servers
│   └── lib/                            # Shared Python test helpers
├── examples/bootstrap5/                # Consumer-style demo Django project
├── docs/                               # MkDocs documentation source
├── scripts/                            # Build/release and developer scripts
├── .planning/                          # GSD plans, phase records and codebase maps
├── pyproject.toml                      # Python package and tool configuration
├── noxfile.py                          # Python/Django test matrix
├── taskfile.yaml                       # Developer task aliases
├── package.json                        # JavaScript test tooling
└── mkdocs.yml                          # Documentation site configuration
```

## Directory Purposes

**`src/crud_views/lib/`:**
- Purpose: Core reusable runtime behavior.
- Contains: `viewset/` registry/router, `view/` shared CrudView contracts, `views/` concrete CBVs, ancestor authorization, settings, checks, formsets, conditional fields, tables, crispy helpers and assets.
- Key files: `src/crud_views/lib/viewset/__init__.py`, `src/crud_views/lib/view/base.py`, `src/crud_views/lib/ancestors.py`, `src/crud_views/lib/settings.py`.
- Add ViewSet-wide routing/registration behavior in `viewset/`; put cross-view behavior in `view/`; put operation-specific handlers in `views/`.

**`src/crud_views/lib/access_trace.py` and `src/crud_views/lib/access_trace_runner.py`:**
- Purpose: Context-local gate recording and the synthetic request runner for the `cv_access` diagnostics.
- Contains: Versioned scalar trace result classes, recorder context manager, route/actor resolution, temporary request/session/message objects, handler stub and outcome mapping.
- Key files: `src/crud_views/lib/access_trace.py`, `src/crud_views/lib/access_trace_runner.py`.
- Gate-specific observations belong beside the existing enforcement gate in `src/crud_views/lib/view/base.py`, `src/crud_views/lib/ancestors.py`, `src/crud_views_guardian/lib/mixins.py`, or `src/crud_views/lib/views/manage.py`. Preserve the single recorder contract; do not implement separate authorization logic in the command or template.

**`src/crud_views/lib/viewset/`:**
- Purpose: ViewSet declaration, registration, parent metadata and path converters.
- Contains: `ViewSet`, `ParentViewSet`, and PK path registrations.
- Key files: `src/crud_views/lib/viewset/__init__.py`, `src/crud_views/lib/viewset/parentviewset.py`, `src/crud_views/lib/viewset/path_regs.py`.
- Guidance: Add URL shape or sibling lookup behavior to ViewSet APIs rather than embedding it in consumer URLconfs.

**`src/crud_views/lib/view/` and `src/crud_views/lib/views/`:**
- Purpose: Separate shared view integration from individual request handlers.
- Contains: CrudView metaclass/base, action and context projections, visibility/variant helpers, plus list/detail/create/update/delete/action/manage CBVs.
- Key files: `src/crud_views/lib/view/meta.py`, `src/crud_views/lib/view/base.py`, `src/crud_views/lib/views/list.py`, `src/crud_views/lib/views/manage.py`.
- Guidance: Keep generic handler lifecycle in the concrete CBV module; use the shared base/mixins for behavior that multiple operations need.

**`src/crud_views/management/commands/`:**
- Purpose: Django management commands exposed by the core app.
- Contains: Asset/configuration tools, manage-group setup, and access tracing.
- Key files: `src/crud_views/management/commands/cv_access.py`, `src/crud_views/management/commands/cv_assets.py`, `src/crud_views/management/commands/cv_manage_group.py`, `src/crud_views/management/commands/crud_views_show.py`.
- Guidance: Keep command argument parsing and output here; delegate runtime behavior to library APIs.

**`src/crud_views/templates/crud_views/` and `src/crud_views/static/crud_views/`:**
- Purpose: Core theme templates and browser behavior.
- Contains: View templates/content blocks, shared UI snippets, formsets, CSS, JavaScript and adapters.
- Key files: `src/crud_views/templates/crud_views/view_manage.html`, `src/crud_views/templates/crud_views/view_list.html`, `src/crud_views/static/crud_views/js/`, `src/crud_views/static/crud_views/css/`.
- Guidance: Keep reusable markup in package templates and preserve documented template blocks and data attributes for host overrides.

**`src/crud_views_guardian/`, `src/crud_views_object_detail/`, `src/crud_views_polymorphic/`, `src/crud_views_workflow/`:**
- Purpose: Optional integration apps packaged alongside core.
- Contains: App configs, specialized classes, integration templates/translations, and tests under `tests/test1/`; workflow also has models and migrations.
- Key files: `src/crud_views_guardian/lib/viewset.py`, `src/crud_views_guardian/lib/mixins.py`, `src/crud_views_object_detail/lib/views.py`, `src/crud_views_polymorphic/lib/create_select.py`, `src/crud_views_workflow/lib/views.py`, `src/crud_views_workflow/migrations/`.
- Guidance: Put integration-specific behavior in its app and keep core imports free from optional dependency imports.

**`tests/test1/`:**
- Purpose: Main Django test project and most Python regression tests.
- Contains: Feature-level test modules, `app/` test models, `project/` settings, `od/` object-detail tests, `od_app/` fixtures and golden files.
- Key files: `tests/test1/conftest.py`, `tests/test1/app/models.py`, `tests/test1/project/`.
- Access trace coverage: `tests/test1/test_access_trace*.py`, `tests/test1/test_manage_access_trace.py`; these exercise gate, middleware/route, command, manage form, serialization and safety boundaries.

**`tests/browser/`, `tests/js/`, `tests/js-integration/`, `tests/lib/`:**
- Purpose: Browser behavior, JavaScript contracts, integration tests and shared Python helpers.
- Contains: Node tests and `*.cjs` harnesses, Python fixture servers, templates and reusable helper modules.
- Key files: `tests/browser/access-trace.test.cjs`, `tests/browser/access_trace_server.py`, `tests/browser/templates/`, `tests/js/`, `tests/js-integration/`, `tests/lib/helper/`.

**`examples/bootstrap5/`:**
- Purpose: Consumer-style project that demonstrates public package APIs across feature apps.
- Contains: Django settings/URLconf, feature applications, seed command, translations and documentation tests.
- Key files: `examples/bootstrap5/project/settings_demo.py`, `examples/bootstrap5/project/urls.py`, `examples/bootstrap5/project/management/commands/seed.py`.
- Guidance: Add a consumer example in the closest feature app and register it through the existing feature catalog where navigation is needed.

**`docs/`:**
- Purpose: MkDocs source documentation.
- Contains: Getting-started, reference, development guides and documentation assets.
- Key files: `docs/reference/`, `docs/getting_started/`, `docs/development/`, `mkdocs.yml`.
- Guidance: Public API changes should update the relevant reference page and executable documentation tests in `tests/test1/` where present.

**`.planning/`:**
- Purpose: GSD project state and planning artifacts.
- Contains: `.planning/codebase/`, `.planning/phases/`, `.planning/quick/`, `.planning/research/`, and project-level roadmap/state documents.
- Guidance: Codebase maps describe current source organization; phase-specific rationale and receipts stay under their phase directory.

## Key File Locations

**Entry Points:**
- `src/crud_views/apps.py`: Core Django app config and system-check registration.
- `src/crud_views/lib/viewset/__init__.py`: `ViewSet` public routing/registration contract.
- `src/crud_views/management/commands/cv_access.py`: `cv_access` CLI.
- `src/crud_views/lib/views/manage.py`: Manage page diagnostics and opt-in access-trace form processing.
- `examples/bootstrap5/project/urls.py`: Demo URL wiring.

**Configuration:**
- `pyproject.toml`: Package metadata, dependencies and Ruff/coverage settings.
- `src/crud_views/lib/settings.py`: `CRUD_VIEWS_*` settings model.
- `noxfile.py`: Supported Python/Django test sessions.
- `taskfile.yaml`: Developer task aliases.
- `package.json`, `vitest.config.js`, `vitest.integration.config.js`: JavaScript tooling.
- `mkdocs.yml`: Documentation navigation/build configuration.

**Core Logic:**
- `src/crud_views/lib/view/meta.py`: Import-time CrudView registration.
- `src/crud_views/lib/view/base.py`: Shared CrudView contract and permission integration.
- `src/crud_views/lib/ancestors.py`: Nested route authorization and child queryset scope.
- `src/crud_views/lib/access_trace.py`, `src/crud_views/lib/access_trace_runner.py`: Access trace recording and execution.
- `src/crud_views/lib/views/`: Core Django request handlers.
- `src/crud_views_guardian/lib/`: Object permission provider and Guardian views.
- `src/crud_views/lib/formsets/`, `src/crud_views/lib/conditional/`: Reusable complex form behavior.

**Testing:**
- `tests/test1/`: Main Python test suite.
- `tests/test1/conftest.py`: Test Django initialization and fixtures.
- `tests/browser/`: Browser harnesses and browser-level behavior.
- `tests/js/`: JavaScript unit tests.
- `tests/js-integration/`: JavaScript integration tests.
- `examples/bootstrap5/test_docs_sync.py`: Demo documentation/example synchronization checks.

## Naming Conventions

**Files:**
- Python implementation modules use lowercase snake_case, such as `access_trace_runner.py` and `parentviewset.py`.
- Python feature tests use `test_<feature>.py`, such as `tests/test1/test_access_trace_command.py`.
- Browser tests use `*.test.cjs`; their harnesses use descriptive kebab-case `.cjs` names or Python `*_server.py` names.
- Templates use descriptive lowercase names with `.html`; static files are grouped by CSS/JS under the owning app.

**Directories:**
- Importable packages use lowercase names, with separate `crud_views_*` roots for optional integrations.
- Runtime support is grouped by responsibility under `src/crud_views/lib/`, including `views/`, `view/`, `viewset/`, `formsets/`, `conditional/`, `crispy/`, and `table/`.
- Tests group project fixtures under `tests/test1/app/`, `tests/test1/project/` and `tests/test1/od_app/`.

## Where to Add New Code

**New CRUD behavior:**
- Shared behavior: `src/crud_views/lib/view/base.py` or a focused mixin/module under `src/crud_views/lib/view/`.
- Operation-specific behavior: corresponding module under `src/crud_views/lib/views/`.
- Tests: a feature-focused `tests/test1/test_<feature>.py`.

**New authorization gate or trace fact:**
- Enforcement: existing owning gate in `src/crud_views/lib/view/base.py`, `src/crud_views/lib/ancestors.py`, or provider implementation under `src/crud_views_guardian/lib/`.
- Trace fact: report through `get_recorder()` / `AccessRecorder` from `src/crud_views/lib/access_trace.py` beside that gate; do not infer decisions in `src/crud_views/management/commands/cv_access.py`.
- Tests: gate-level `tests/test1/test_access_trace*.py`; command output tests in `tests/test1/test_access_trace_command.py`; manage integration in `tests/test1/test_manage_access_trace.py`.
- Browser-facing form behavior: `src/crud_views/lib/views/manage.py`, `src/crud_views/templates/crud_views/view_manage.html` or its focused partial, with harness under `tests/browser/`.

**New optional integration:**
- Implementation: add an app root under `src/crud_views_<integration>/` with `apps.py`, public `__init__.py`, focused `lib/`, and app-owned templates/static assets as needed.
- Tests: add coverage in `tests/test1/` and keep optional imports out of core modules.

**New documentation:**
- Reference/API pages: `docs/reference/`.
- Setup and usage pages: `docs/getting_started/`.
- Developer process: `docs/development/`.
- Add or update executable docs checks under `tests/test1/` when the page contains supported code examples.

**Examples:**
- Feature demo: relevant folder under `examples/bootstrap5/`.
- Shared navigation/catalog metadata: `examples/bootstrap5/project/features.py` and related project template tags.

## Special Directories

**`src/*/migrations/`:**
- Purpose: Django schema migrations for apps that own database models.
- Generated: Yes, by Django migration tooling.
- Committed: Yes; workflow migrations are in `src/crud_views_workflow/migrations/`.

**`site/`:**
- Purpose: Generated/static documentation site output used by the repository's publishing setup.
- Generated: Yes, by the documentation build.
- Committed: Present in the repository; edit source pages under `docs/` and configuration in `mkdocs.yml` rather than editing rendered output by hand.

**`.planning/phases/`:**
- Purpose: Phase plans, implementation summaries, validation artifacts and evidence.
- Generated: No; maintained planning records.
- Committed: Yes.

**`node_modules/`, `.venv/`, `.nox/`, `dist/`:**
- Purpose: Installed JavaScript/Python environments, test environments and build artifacts.
- Generated: Yes.
- Committed: No; do not place source changes there.

---

*Structure analysis: 2026-11-15*
