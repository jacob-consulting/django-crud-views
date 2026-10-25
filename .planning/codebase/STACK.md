---
last_mapped_commit: 38b0100683fa71412b8bc00dd0eeb7f985efb459
last_mapped_at: 2026-10-25
---
# Technology Stack

**Analysis Date:** 2026-10-25

## Languages

**Primary:**

- Python >=3.12 (supported 3.12, 3.13, 3.14, 3.15 per `pyproject.toml` classifiers and `noxfile.py`). Used for all five packages under `src/` (`crud_views`, `crud_views_object_detail`, `crud_views_workflow`, `crud_views_polymorphic`, `crud_views_guardian`), the tests (`tests/`) and the example project (`examples/bootstrap5/`).

**Secondary:**

- Django template language: package templates in `src/crud_views/templates/crud_views/`, `src/crud_views_object_detail/templates/crud_views_object_detail/`, `src/crud_views_workflow/templates/crud_views_workflow/`, `src/crud_views_guardian/templates/crud_views/`.
- JavaScript (plain browser JS, some jQuery 3.x usage in `src/crud_views/static/crud_views/js/formset.js`): `adapters.js`, `formset.js`, `list.filter.js`, `modal.js`, `toggle.js`, `tooltip.js`, `viewset.js` in `src/crud_views/static/crud_views/js/`.
- CSS: `src/crud_views/static/crud_views/css/` (`formset.css`, `icons.css`, `property.css`, `table.css`).
- gettext `.po`/`.mo` catalogs (German, `de`) under each package's `locale/` and `examples/bootstrap5/locale/`.
- Markdown for docs (`docs/`, built by MkDocs via `mkdocs.yml`).

## Runtime

**Environment:**

- CPython 3.12+ (local dev venv pinned to 3.12 via `PYTHON: "3.12"` in `taskfile.yaml`; `.venv` runs Python 3.12.3).
- Django >=4.2 at runtime. Test matrix: Django 4.2 / 5.2 / 6.0 (`DJANGO_VERSIONS` in `noxfile.py`). Django 4.2 is skipped on Python 3.14+.
- Node.js >=20 for the dev-only JS test harness only (`package.json` `engines`; CI uses Node 22 in `.github/workflows/js.yml`). Node is never needed at package runtime.

**Package Manager:**

- uv (venv creation and installs: `uv venv`, `uv pip install`, `uv build`, `uv run` in `taskfile.yaml`; nox sessions use `venv_backend="uv"`).
- Lockfile: `uv.lock` present (dev resolution, e.g. Django 5.2.14, pydantic 2.13.4).
- npm for JS dev deps; lockfile `package-lock.json` present.
- CI uses pip with hash-pinned locks: `.github/requirements/ci.txt` (from `.github/requirements/ci.in`) and `docs/requirements.txt`, installed with `--require-hashes --only-binary :all:`.
- Task runner: go-task (`taskfile.yaml`, includes `examples/bootstrap5/taskfile.yaml`).

## Frameworks

**Core:**

- Django >=4.2 (locked 5.2.14) — host framework; package views extend Django generic CBVs (`src/crud_views/lib/views/`).
- Pydantic >=2.2.1 (locked 2.13.4) — `ViewSet` model (`src/crud_views/lib/viewset/__init__.py`), settings model `CrudViewsSettings` (`src/crud_views/lib/settings.py`), non-ORM `Resource` base (`src/crud_views/lib/resource.py`).
- django-tables2 >=2.5.3 (locked 3.0.0) — list tables (`src/crud_views/lib/table/`).
- django-filter >=21.1 (locked 25.2) — list filtering (`ListViewTableFilterMixin`, `src/crud_views/lib/views/mixins.py`).
- django-crispy-forms >=2.0 (locked 2.6) + crispy-bootstrap5 >=2023.10 (locked 2026.3) — form rendering (`src/crud_views/lib/crispy/`).
- Bootstrap 5 — the only theme; templates target Bootstrap 5.3 markup. Bootstrap itself is not bundled; host projects load it (example loads 5.3.3 from jsDelivr in `examples/bootstrap5/project/templates/project/base.html`).

**Optional extras (`[project.optional-dependencies]` in `pyproject.toml`):**

- `workflow`: django-fsm-2 >=4.0.0 (locked 4.2.4), django-fsm-2-admin >=2.0.1 — used by `src/crud_views_workflow/`.
- `polymorphic`: django-polymorphic >=3.1.0 (locked 4.11.3) — used by `src/crud_views_polymorphic/`.
- `ordered`: django-ordered-model >=3.4.3 (locked 3.7.4) — used by `src/crud_views/lib/ordered.py` and `src/crud_views/lib/views/action_ordered.py`.
- `guardian`: django-guardian >=2.4 (locked 3.3.1) — used by `src/crud_views_guardian/`.
- `all`: all four of the above.

**Testing:**

- pytest (locked 9.0.3) + pytest-django (4.12.0), pytest-cov, pytest-xdist (3.8.0, `-n auto` in nox), pytest-random-order, pytest-mock. `addopts = "--strict-markers"` in `pyproject.toml`.
- lxml (6.1.0) + cssselect — HTML assertions in tests.
- polib — i18n catalog tests (`tests/test1/test_i18n.py`).
- django-pipeline (4.1.0) — test-only, exercises `src/crud_views/lib/pipeline.py`.
- nox — matrix runner (`noxfile.py`, sessions `tests` and `examples`).
- Vitest ^5.0.3 + jsdom ^30.1.2 + jquery ~3.7.1 — JS unit tests (`vitest.config.js`, specs in `tests/js/**/*.test.js`, setup `tests/js/helpers/setup.js`).
- Coverage: `[tool.coverage.*]` in `pyproject.toml`, `fail_under = 88`, paths remapped from `site-packages/` to `src/`.

**Build/Dev:**

- hatchling — build backend (`[build-system]`); wheel ships the five `src/` packages (`[tool.hatch.build.targets.wheel]`).
- ruff 0.17.x — format + lint (`[tool.ruff]`: line-length 120, double quotes, rules `E,F,I,UP,B,C4,SIM,RUF`; `superpowers/**` excluded). Pre-commit runs `ruff-check` and `ruff-format` (`.pre-commit-config.yaml`, rev v0.17.1).
- bump-my-version — syncs version across `pyproject.toml`, `src/crud_views/__init__.py`, `docs/index.md`, `README.md` (`[tool.bumpversion]`); creates `v{version}` tags.
- MkDocs 1.6.1 (theme `readthedocs`) + mkdocs-awesome-pages-plugin + pymdown-extensions (mermaid fences) — `mkdocs.yml`, `docs/`.
- python `build` — used in `.github/workflows/publish.yml` (`python -m build`).
- complexipy cache present (`.complexipy_cache/`) — ad-hoc complexity tooling, not wired into CI.

## Key Dependencies

**Critical:**

- `django` — every module depends on it; compatibility gated by the 4.2/5.2/6.0 nox matrix. Django 6-only APIs are imported lazily (e.g. `django.middleware.csp.get_nonce` in `src/crud_views/templatetags/crud_views.py`).
- `pydantic` v2 — ViewSet and settings are Pydantic models; v1 APIs are not supported.
- `python-box` >=6.0.2 (locked 7.4.1) — `Box` dicts for asset maps in `src/crud_views/lib/settings.py`.
- `django-tables2`, `django-filter`, `django-crispy-forms`, `crispy-bootstrap5` — hard runtime deps for list/form views.
- `typing-extensions` >=4.7.1.

**Infrastructure:**

- Demo-only (`requirements/demo.txt`, not part of the package): gunicorn >=23, whitenoise >=6.9, django-ratelimit >=4.1.
- `pygments` — `examples` extra (source display in the example project).

## Configuration

**Environment:**

- Package configuration is read from Django settings with the `CRUD_VIEWS_*` prefix via `from_settings()` in `src/crud_views/lib/settings.py` (`CrudViewsSettings`). Required: `CRUD_VIEWS_EXTENDS` (base template; system check `crud_views.E100`). Notable optional: `CRUD_VIEWS_MANAGE_VIEWS_ENABLED` (`no`/`yes`/`debug_only`), `CRUD_VIEWS_CSP_NONCE_ATTR`, `CRUD_VIEWS_ASSETS_BUNDLED`, `CRUD_VIEWS_INACCESSIBLE_ACTIONS`, `CRUD_VIEWS_HEADER_LEVEL`, `CRUD_VIEWS_BREADCRUMB_PREFIX`, `CRUD_VIEWS_FILTER_PERSISTENCE`, `CRUD_VIEWS_*_ACTIONS*`, `CRUD_VIEWS_STRICT` (set in tests), `CRUD_VIEWS_OBJECT_DETAIL_TEMPLATE_PACK_*`.
- Host must set `CRISPY_TEMPLATE_PACK = "bootstrap5"` and may set `DJANGO_TABLES2_TEMPLATE = "crud_views/table/bootstrap5.html"` (see `examples/bootstrap5/project/settings.py`).
- Settings are validated at startup through Django system checks in `src/crud_views/checks.py`.
- The package itself reads no environment variables. Only the demo settings do (`SECRET_KEY`, `RENDER_EXTERNAL_HOSTNAME` in `examples/bootstrap5/project/settings_demo.py`).
- `.env` file present at repo root — contains environment configuration (not read; not used by package code).

**Build:**

- `pyproject.toml` (project metadata, extras, ruff, pytest, coverage, bumpversion)
- `noxfile.py` (test matrix), `taskfile.yaml` (dev tasks), `.pre-commit-config.yaml`
- `vitest.config.js`, `package.json`, `package-lock.json` (JS tests)
- `mkdocs.yml`, `.readthedocs.yaml`, `docs/requirements.txt` (docs)
- `settings_i18n.py` (root; minimal settings for `makemessages`/`compilemessages` via `task msg-make` / `task msg-comp`)
- `render.yaml` (demo deployment), `codecov.yml`, `.sonarcloud.properties`

## Platform Requirements

**Development:**

- uv and go-task (`task dev` → `uv venv --python=3.12` + `uv pip install .[all,dev,test,examples] -r requirements/demo.txt`).
- Node 20+ and npm only for `task test-js`.
- Multiple Python interpreters (3.12–3.15) for the full `task test` nox matrix.
- Example project: `examples/bootstrap5/` with SQLite (`db.sqlite3`); `task run` migrates, seeds, serves.

**Production:**

- Distributed as a library on PyPI (`django-crud-views`, version 0.30.0) via `.github/workflows/publish.yml` on `v*` tags (trusted publishing, `id-token: write`).
- Public demo of `examples/bootstrap5` on Render free plan (`render.yaml`): Python 3.13, gunicorn single worker, whitenoise static files, ephemeral SQLite re-seeded each boot.
- Docs hosted on Read the Docs (`.readthedocs.yaml`, Ubuntu 24.04, Python 3.12).

---

*Stack analysis: 2026-10-25*
