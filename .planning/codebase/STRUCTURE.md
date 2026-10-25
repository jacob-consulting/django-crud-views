---
last_mapped_commit: 38b0100683fa71412b8bc00dd0eeb7f985efb459
last_mapped_at: 2026-10-25
---
# Codebase Structure

**Analysis Date:** 2026-10-25

## Directory Layout

```
django-crud-views/
├── src/                                  # All shipped Python packages (hatchling wheel targets)
│   ├── crud_views/                       # Core Django app (label "crud_views")
│   │   ├── __init__.py                   # __version__ only (bump-my-version target)
│   │   ├── apps.py                       # CrudViewsConfig; ready() imports checks
│   │   ├── checks.py                     # Django system-check registration (crud_views.E###)
│   │   ├── lib/                          # Library code (all importable API lives here)
│   │   │   ├── viewset/                  # ViewSet, ParentViewSet, PK regexes
│   │   │   ├── view/                     # CrudView base, buttons, context, menus, enums
│   │   │   ├── views/                    # Concrete CBVs (list/detail/create/update/delete/action/card/form/manage)
│   │   │   ├── crispy/                   # crispy-forms integration (forms, buttons, ColumnN)
│   │   │   ├── table/                    # django-tables2 Table + columns + column attrs
│   │   │   ├── formsets/                 # Nested inline formsets
│   │   │   ├── conditional/              # Toggle-driven conditional groups/formsets
│   │   │   ├── settings.py               # CrudViewsSettings singleton (CRUD_VIEWS_*)
│   │   │   ├── check.py                  # Check classes (viewset.E###/W###)
│   │   │   ├── exceptions.py             # Exceptions, cv_raise, strict mode
│   │   │   ├── resource.py               # Resource (non-ORM rows) + ResourceViewMixin
│   │   │   ├── breadcrumb.py             # CrudViewBreadcrumbMixin
│   │   │   ├── assets.py / pipeline.py / vendor.py  # JS/CSS registry, django-pipeline, vendoring
│   │   │   ├── icons.py / button_classes.py         # Icon + button CSS class registries
│   │   │   ├── session.py                # Per-view session storage
│   │   │   ├── messages.py               # Alert/message helpers
│   │   │   ├── ordered.py                # Optional django-ordered-model loader
│   │   │   ├── lazy.py                   # Lazy-string Pydantic validator
│   │   │   └── context_processor.py      # crud_views_context
│   │   ├── templatetags/                 # crud_views.py, crud_views_formsets.py
│   │   ├── templates/crud_views/         # Bootstrap 5 templates (views, snippets, tags, columns, modal)
│   │   ├── static/crud_views/{js,css}/   # Vanilla JS (no jQuery) + CSS
│   │   ├── management/commands/          # cv_assets, crud_views_show
│   │   ├── migrations/                   # Empty (no models)
│   │   └── locale/de/                    # Translations
│   ├── crud_views_object_detail/         # Extension: property-grid detail view (label "cvod")
│   │   ├── lib/                          # config.py, conf.py, mixins.py, resolvers.py, views.py
│   │   ├── templatetags/
│   │   └── templates/crud_views_object_detail/{layouts/<pack>/,types/default/}
│   ├── crud_views_workflow/              # Extension: django-fsm workflows (label "cvw")
│   │   ├── lib/                          # enums.py, forms.py, mixins.py, views.py (lazy __init__)
│   │   ├── models.py                     # WorkflowInfo audit model
│   │   ├── checks.py
│   │   ├── migrations/
│   │   └── templates/crud_views_workflow/
│   ├── crud_views_polymorphic/           # Extension: django-polymorphic (label "cvp")
│   │   └── lib/                          # create_select.py, create.py, update.py, detail.py, delete.py, utils.py
│   └── crud_views_guardian/              # Extension: django-guardian per-object perms (label "cvg")
│       ├── lib/                          # viewset.py, mixins.py, views.py
│       └── templates/crud_views/         # view_guardian_manage.html, snippets/guardian/
├── tests/                                # pytest suite (Python) + vitest suite (JS)
│   ├── conftest.py                       # Shared fixtures (asset_registry)
│   ├── lib/helper/                       # Test helpers (users, forms, guardian, icons, bootstrap5)
│   ├── test1/                            # Test Django project
│   │   ├── conftest.py                   # pytest_configure(): in-memory Django settings
│   │   ├── app/                          # Test app: models.py, views.py, views_formset.py, resources.py, urls.py, templates/
│   │   ├── od_app/                       # Object-detail test app
│   │   ├── od/                           # Object-detail tests
│   │   ├── project/urls.py               # Root URLconf for tests
│   │   ├── golden/                       # Golden HTML snapshots
│   │   └── test_*.py                     # Flat test modules (one per feature/issue)
│   └── js/                               # vitest specs (*.test.js) + helpers/
├── examples/bootstrap5/                  # Runnable demo project (one Django app per feature)
│   ├── project/                          # settings, urls, base templates, seeding, demo views
│   ├── library/ nested/ formsets/ workflow/ polymorphic_demo/ guardian_demo/
│   ├── resources/ showcase/ object_detail/ conditional/ breadcrumbs/
│   ├── context_buttons/ action_menus/ app/   # Feature demo apps
│   ├── manage.py, taskfile.yaml, pytest.ini
│   └── test_doc_links.py, test_docs_sync.py, test_i18n.py
├── docs/                                 # mkdocs site source (getting_started/, reference/, development/)
├── superpowers/                          # Design specs, plans, notes, prompts (excluded from ruff)
├── scripts/                              # generate_screenshots.py, wait_for_server.py
├── requirements/                         # demo.txt, test.txt (pinned)
├── .github/workflows/                    # tests, lint, js, docs, demo, publish, readme-examples
├── pyproject.toml                        # Project metadata, extras, ruff, coverage, hatch
├── noxfile.py                            # Python × Django test matrix
├── taskfile.yaml                         # Developer tasks (dev, test, format, check, docs, bump)
├── package.json / vitest.config.js       # JS test tooling
├── mkdocs.yml                            # Docs site config
├── settings_i18n.py                      # Minimal settings for makemessages/compilemessages
├── CHANGELOG.md, docs/migrating-1.0.md   # Release notes (Breaking entries mirrored in migrating-1.0)
└── AGENTS.md / CLAUDE.md                 # Agent guidance
```

## Directory Purposes

**`src/crud_views/lib/viewset/`:**

- Purpose: Registry and URL routing.
- Contains: `ViewSet` (`__init__.py`), `ParentViewSet` (`parentviewset.py`), `PrimaryKeys` + `get_path_pk` (`path_regs.py`).
- Key files: `src/crud_views/lib/viewset/__init__.py`

**`src/crud_views/lib/view/`:**

- Purpose: The `CrudView` base and everything a view needs to render actions (no concrete Django views).
- Contains: `base.py` (CrudView, CrudViewPermissionRequiredMixin), `meta.py` (metaclass), `buttons.py` (ContextButton family), `button_data.py`, `card.py` (CardAction), `context.py` (ViewContext), `action_menu.py` (ActionGroup, inline split), `visibility.py` (cv_resolve_action), `label_mode.py`, `variant.py`.
- Key files: `src/crud_views/lib/view/base.py`, `src/crud_views/lib/view/buttons.py`

**`src/crud_views/lib/views/`:**

- Purpose: Concrete, user-facing view classes.
- Contains: one module per view type (`list.py`, `detail.py`, `create.py`, `update.py`, `delete.py`, `action.py`, `action_ordered.py`, `card.py`, `form.py`, `child.py`, `manage.py`) and shared `mixins.py`.
- Key files: `src/crud_views/lib/views/__init__.py` (public `__all__`), `src/crud_views/lib/views/mixins.py`

**`src/crud_views/lib/crispy/`, `src/crud_views/lib/table/`, `src/crud_views/lib/formsets/`, `src/crud_views/lib/conditional/`:**

- Purpose: Third-party integrations and form features, each re-exported via its `__init__.py`.
- Key files: `src/crud_views/lib/crispy/form.py`, `src/crud_views/lib/table/table.py`, `src/crud_views/lib/formsets/formsets.py`, `src/crud_views/lib/conditional/group.py`

**`src/crud_views/templates/crud_views/`:**

- Purpose: Bootstrap 5 templates; overridable by consumers at the same path.
- Contains:
  - `view_<type>.html` (page, `{% extends cv_extends %}`) + `view_<type>.content.html` (body partial shared with modals)
  - `snippets/{header,paragraph,action,action_short,message}/<key>.html` — label snippets per view key
  - `tags/` — inclusion-tag templates (buttons, menus, breadcrumb, alerts, config)
  - `tags/button/` — button leaf templates (`action.html`, `menu_item.html`, `container.html`)
  - `columns/` — django-tables2 column templates
  - `modal/`, `formsets/`, `conditional/`, `shared/` (css/js tags), `table/bootstrap5.html`

**`src/crud_views/static/crud_views/`:**

- Purpose: Client behavior (vanilla JS, `globalThis.cv` namespace) and CSS.
- Key files: `js/adapters.js` (only place touching Bootstrap JS), `js/viewset.js` (`cvGetConfig`, form submit actions), `js/modal.js`, `js/formset.js`, `js/list.filter.js`, `js/toggle.js`, `js/tooltip.js`

**`src/crud_views_<ext>/`:**

- Purpose: Optional extension apps; each has `apps.py`, `lib/`, `locale/`, and optional `templates/`, `templatetags/`, `models.py`, `migrations/`, `checks.py`.

**`tests/test1/`:**

- Purpose: The whole Python test suite, run against a configured in-memory Django project.
- Contains: `app/` (models Author/Publisher/Book/Vehicle/Campaign…, ViewSets in `views.py`), flat `test_*.py`, `golden/` HTML snapshots.

**`examples/bootstrap5/`:**

- Purpose: Demo site and documentation source of truth (`test_docs_sync.py` keeps docs in sync).
- Contains: one Django app per feature with `models.py`, `views.py`, `urls.py`, `seed.py`, `tests.py`, `migrations/`.

**`superpowers/`:**

- Purpose: Design artefacts — `specs/`, `plans/`, `notes/` (acceptance reports), `prompts/`, `instructions/`. Referenced from code comments (e.g. modal spec in `src/crud_views/lib/view/base.py:98`).

## Key File Locations

**Entry Points:**

- `src/crud_views/apps.py`: Core AppConfig; registers system checks.
- `src/crud_views/lib/viewset/__init__.py`: `ViewSet.urlpatterns` — URL entry for consumers.
- `src/crud_views/templatetags/crud_views.py`: `{% load crud_views %}` tag library.
- `src/crud_views/lib/context_processor.py`: `crud_views.lib.context_processor.crud_views_context`.
- `src/crud_views/management/commands/cv_assets.py`: `manage.py cv_assets`.

**Configuration:**

- `pyproject.toml`: dependencies, extras (`workflow`, `polymorphic`, `ordered`, `guardian`, `all`, `dev`, `test`), ruff (line-length 120), coverage, hatch wheel packages.
- `src/crud_views/lib/settings.py`: All `CRUD_VIEWS_*` settings and their checks.
- `src/crud_views_object_detail/lib/conf.py`: Object-detail settings.
- `noxfile.py`, `taskfile.yaml`, `vitest.config.js`, `mkdocs.yml`, `.pre-commit-config.yaml`.
- `tests/test1/conftest.py`: Django settings for tests.

**Core Logic:**

- `src/crud_views/lib/view/base.py`: `CrudView` — URL building, action context, origin keys, transactions, checks.
- `src/crud_views/lib/views/mixins.py`: POST pipeline, messages, card ordering, table/filter mixins.
- `src/crud_views/lib/view/buttons.py`: Context buttons.
- `src/crud_views/lib/check.py`, `src/crud_views/checks.py`: Validation.

**Testing:**

- `tests/test1/test_*.py`: Python tests.
- `tests/test1/app/views.py`: Test ViewSets/views (fixtures reference `cv_<model>`).
- `tests/lib/helper/user.py`: `user_viewset_permission` helper.
- `tests/js/*.test.js`: JS tests.

## Naming Conventions

**Files:**

- View modules named by view type, singular, lowercase: `src/crud_views/lib/views/create.py`, `action_ordered.py`.
- Page templates: `view_<type>.html`; body partials: `view_<type>.content.html`; variants with dots: `view_list_table.filter.html`.
- Label snippets: `snippets/<role>/<cv_key>.html` (e.g. `snippets/header/create.html`, `snippets/action_short/delete.html`).
- JS: lowercase, dot-separated feature names (`list.filter.js`); tests mirror as `tests/js/list.filter.test.js`.
- Tests: `test_<feature>.py`, flat in `tests/test1/`; golden files under `tests/test1/golden/<feature>/<case>.html`.

**Directories:**

- Extension packages: `crud_views_<feature>/` with code in `lib/`.
- Template namespace equals app name (`templates/crud_views/`, `templates/crud_views_workflow/`); guardian deliberately adds into `templates/crud_views/`.
- Object-detail layout packs: `templates/crud_views_object_detail/layouts/<pack-name>/{group,property,object_detail}.html`; field types: `types/<pack>/<fieldtype>.html`.

**Classes / attributes:**

- Views: `<Type>View` and `<Type>ViewPermissionRequired`; extension prefixes `Guardian…`, `Polymorphic…`, `Workflow…`, `ObjectDetail…`.
- CrudView attributes and methods: `cv_` prefix (`cv_key`, `cv_get_url`); workflow transitions: `wf_` prefix.
- ViewSet variables in consumer code: `cv_<model>` (e.g. `cv_author`).
- URL names: `[app:]<viewset_name>-<cv_key>`; parent URL kwarg `<parent_viewset_name>_pk`.

## Where to Add New Code

**New core view type:**

- Implementation: `src/crud_views/lib/views/<type>.py` — `class <Type>View(<needed mixins>, CrudView, generic.<X>)` with `cv_key`, `cv_path`, `cv_object`, label snippet templates, `cv_icon_action`; plus `class <Type>ViewPermissionRequired(CrudViewPermissionRequiredMixin, <Type>View)` with `cv_permission`.
- Export: add to `src/crud_views/lib/views/__init__.py` `__all__` (and update `tests/test1/test_public_api_surface.py`).
- Templates: `src/crud_views/templates/crud_views/view_<type>.html` + `.content.html`; snippets under `snippets/{header,paragraph,action,action_short}/<key>.html`.
- Default context actions: add a `<type>_context_actions` setting in `src/crud_views/lib/settings.py`.
- Tests: `tests/test1/test_<type>.py`; register a test ViewSet in `tests/test1/app/views.py` and its URLs in `tests/test1/app/urls.py`.
- Docs: `docs/reference/<type>_view.md`; demo in `examples/bootstrap5/<app>/views.py`.

**New reusable view behavior (mixin):**

- Generic view mixins: `src/crud_views/lib/views/mixins.py`.
- Larger feature with its own models/forms: new subpackage `src/crud_views/lib/<feature>/` with `__init__.py` re-exports and `__all__`.
- Add checks via `@classmethod checks(cls)` that `yield from super().checks()`.

**New context button kind:**

- `src/crud_views/lib/view/buttons.py` — subclass `ContextButton`, implement `get_context()` and `cv_check_target()`; export in `src/crud_views/lib/view/__init__.py`.

**New template tag:**

- `src/crud_views/templatetags/crud_views.py`; its template under `src/crud_views/templates/crud_views/tags/` using `f"{crud_views_settings.theme_path}/tags/..."`.

**New setting:**

- Field on `CrudViewsSettings` in `src/crud_views/lib/settings.py` using `from_settings("CRUD_VIEWS_<NAME>", default=...)`; validation in `check_messages`; document in `docs/reference/settings.md`.

**New system check:**

- Per-view/ViewSet: yield a `Check*` from `checks()` with a new `E###`/`W###` id (`src/crud_views/lib/check.py` for new check types).
- Global/package checks: `src/crud_views/checks.py` (`crud_views.E###`).

**New JS behavior:**

- `src/crud_views/static/crud_views/js/<feature>.js`; register in `CrudViewsSettings.javascript()` / core asset bundle (`src/crud_views/lib/assets.py`); UI-library calls only through `cv.adapters` in `adapters.js`.
- Tests: `tests/js/<feature>.test.js` using `tests/js/helpers/`.

**New extension package:**

- `src/crud_views_<name>/` with `apps.py` (unique short `label`), `lib/`, `locale/.gitkeep`; add to `[tool.hatch.build.targets.wheel] packages` in `pyproject.toml`, an extra in `[project.optional-dependencies]`, `I18N_PACKAGES` in `taskfile.yaml`, and `INSTALLED_APPS` in `tests/test1/conftest.py`.
- If model modules must import from `lib`, use the lazy `_EXPORTS` + `__getattr__` pattern of `src/crud_views_workflow/lib/__init__.py`.

**Utilities:**

- Shared helpers: `src/crud_views/lib/<topic>.py` (keep leaf modules free of `crud_views.lib.viewset` imports).
- Test helpers: `tests/lib/helper/`.

## Special Directories

**`src/crud_views/migrations/`:**

- Purpose: Placeholder (core has no models).
- Generated: No
- Committed: Yes

**`src/crud_views_workflow/migrations/`:**

- Purpose: `WorkflowInfo` schema (`0001_initial.py`, `0002_rename_workflow_object_id_to_pk.py`).
- Generated: Yes (makemigrations)
- Committed: Yes

**`src/*/locale/`:**

- Purpose: gettext catalogs (`de`).
- Generated: `.po` via `makemessages`, `.mo` compiled
- Committed: Yes

**`tests/test1/golden/`:**

- Purpose: Expected rendered HTML for snapshot tests.
- Generated: Partially (regenerated when markup changes intentionally)
- Committed: Yes

**`site/`, `dist/`, `.nox/`, `node_modules/`, `.ruff_cache/`, `.complexipy_cache/`, `.pytest_cache/`:**

- Purpose: Build output (mkdocs, wheels), tool caches, JS deps.
- Generated: Yes
- Committed: No (gitignored)

**`examples/bootstrap5/db.sqlite3`, `tests/.coverage`, `tests/coverage.xml`:**

- Purpose: Local demo DB and coverage artefacts.
- Generated: Yes
- Committed: No (gitignored)

**`superpowers/`:**

- Purpose: Design specs/plans/notes.
- Generated: No
- Committed: Yes (excluded from ruff via `extend-exclude`)

**`.planning/`:**

- Purpose: GSD planning artefacts (`codebase/` maps, `config.json`).
- Generated: Yes (tooling)
- Committed: Managed by orchestrator

---

*Structure analysis: 2026-10-25*
