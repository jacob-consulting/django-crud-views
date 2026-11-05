---
last_mapped_commit: dced8509ce37fd54351952d2e1302784d0278d0b
last_mapped_at: 2026-11-05
---
# Technology Stack

**Analysis Date:** 2026-11-05

## Languages

**Primary:**
- Python >=3.12 — distributable Django package and example projects under `src/` and `examples/`

**Secondary:**
- JavaScript (Node.js >=20 for the private test harness) — browser-side unit and integration tests under `tests/js/` and `tests/js-integration/`
- HTML, CSS, gettext PO/MO — Django templates/assets and translations in `src/` and `docs/development/i18n.md`

## Runtime

**Environment:**
- Python >=3.12; CI covers Python 3.12, 3.13, 3.14, and 3.15 (see `noxfile.py` and `.github/workflows/tests.yml`)
- Django >=4.2; tested against Django 4.2, 5.2, and 6.0 (see `pyproject.toml` and `noxfile.py`)
- Node.js >=20 for JavaScript tests (see `package.json`); CI currently selects Node 22 in `.github/workflows/js-tests.yml`

**Package Manager:**
- Python: `uv` for development and nox virtual environments; `pip` for install/deploy instructions
- Lockfile: `uv.lock` present; `package-lock.json` present for the JS harness
- JavaScript: npm

## Frameworks

**Core:**
- Django >=4.2 — host framework for the five installable apps in `src/crud_views*/`
- Pydantic >=2.2.1 — settings, ViewSet configuration, and validated configuration models
- django-crispy-forms >=2.0 and crispy-bootstrap5 >=2023.10 — form layout and Bootstrap 5 rendering
- django-tables2 >=2.5.3 and django-filter >=21.1 — table and filter support for list views

**Testing:**
- pytest with pytest-django, pytest-cov, pytest-xdist, pytest-mock, and pytest-random-order — Python test suite in `tests/`
- nox — Python/Django compatibility matrix in `noxfile.py`
- Vitest 5 with jsdom 30 — JavaScript tests configured in `vitest.config.js` and `vitest.integration.config.js`

**Build/Dev:**
- Hatchling — PEP 517 build backend; `pyproject.toml` explicitly packages all five `src/crud_views*` apps
- Ruff >=0.17,<0.18 — Python formatting and linting
- MkDocs with `mkdocs-awesome-pages-plugin`, `mkdocs-get-deps`, and `pymdown-extensions` — documentation site (`mkdocs.yml`)
- bump-my-version — synchronized version updates configured in `pyproject.toml`

## Key Dependencies

**Critical:**
- `Django` — host framework and runtime dependency for every app in `src/`
- `pydantic` — core settings and ViewSet model validation (`src/crud_views/lib/settings.py`, `src/crud_views/lib/viewset/`)
- `django-crispy-forms` and `crispy-bootstrap5` — form rendering adapter (`src/crud_views/lib/crispy/`)
- `django-tables2` and `django-filter` — optional list table/filter capabilities included in core dependencies (`src/crud_views/lib/table/`, `src/crud_views/lib/views/mixins.py`)
- `python-box` and `typing-extensions` — utility dependencies declared by the core package in `pyproject.toml`

**Infrastructure:**
- `django-fsm-2` and `django-fsm-2-admin` — optional `[workflow]` extra for state-machine support (`src/crud_views_workflow/`)
- `django-polymorphic` — optional `[polymorphic]` extra (`src/crud_views_polymorphic/`)
- `django-ordered-model` — optional `[ordered]` extra for ordered model actions
- `django-guardian` — optional `[guardian]` extra for per-object permissions (`src/crud_views_guardian/`)
- `django-crud-views[all]` installs all four extension extras
- `lxml`, `cssselect`, `polib`, and `django-pipeline` — test-only dependencies declared in `pyproject.toml`
- `gunicorn`, `whitenoise`, and `django-ratelimit` — demo deployment requirements in `requirements/demo.txt`, not package runtime dependencies

## Configuration

**Environment:**
- The library reads project configuration from the host Django settings module; package options use the `CRUD_VIEWS_*` prefix and are modeled in `src/crud_views/lib/settings.py`.
- Each example supplies its own Django settings and environment handling, e.g. `examples/bootstrap5/project/settings_demo.py`; the library itself does not load a `.env` file.
- `render.yaml` declares deployment-time `DJANGO_SETTINGS_MODULE`, generated `SECRET_KEY`, and Python runtime for the public demo. `.env` files, if present, are not inspected.

**Build:**
- `pyproject.toml` defines package metadata, dependency extras, Hatchling wheel package paths, Ruff, pytest, coverage, and version-bump settings.
- `noxfile.py` defines Python/Django test matrices and example test sessions.
- `package.json`, `vitest.config.js`, and `vitest.integration.config.js` define the private JavaScript test harness.
- `mkdocs.yml` and `docs/requirements.txt` configure documentation builds.

## Platform Requirements

**Development:**
- Python >=3.12, `uv`, and `task` for the documented workflow; Node.js >=20/npm only for JS tests (`CLAUDE.md`, `package.json`).
- The package supports Django 4.2, 5.2, and 6.0; Django 4.2 sessions are skipped on Python 3.14+ in `noxfile.py`.

**Production:**
- A Django host project and a supported Python/Django combination; the package does not prescribe a production database or web server.
- The included demo is deployed to Render using Gunicorn and WhiteNoise (`render.yaml`, `requirements/demo.txt`); it seeds a fresh SQLite database at startup because the demo plan has ephemeral storage.

---

*Stack analysis: 2026-11-05*

## Phase 06.12 incremental refresh — 2026-11-05

Scope: workflow presentation, class registry, associated tests/docs and companion integration. Other sections retain the preceding full-map findings.

### Workflow presentation dependencies

Phase 06.12 adds no runtime dependency. `pyproject.toml` retains the optional workflow extra with `django-fsm-2>=4.0.0` and `django-fsm-2-admin>=2.0.1`. The new presentation path uses existing Django AppConfig/template APIs, the class registry, and crispy rendering.

`tests/browser/workflow-presentation.cjs` uses an available Playwright/Chromium runtime and separate stock/companion Python environments. It records actual versions and template origins rather than assuming the full supported matrix was exercised locally. `CV_WORKFLOW_COMPANION` selects the sibling theme checkout.
