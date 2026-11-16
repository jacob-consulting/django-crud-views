---
last_mapped_commit: a78b63db1f637b6b8b4cf6b4aaa24885a061ae26
last_mapped_at: 2026-11-16
---
# Technology Stack

**Analysis Date:** 2026-11-16

## Languages

**Primary:**
- Python (>=3.12) - Django package implementation, test suite, example site, and developer scripts (`pyproject.toml`, `src/`, `tests/`, `examples/`, `scripts/`)

**Secondary:**
- JavaScript (Node >=20 for the dev test harness) - browser assets under `src/crud_views/static/` and Vitest tests/configuration (`package.json`, `vitest.config.js`)
- HTML/Django templates and CSS - package and example UI (`src/*/templates/`, `src/*/static/`, `examples/bootstrap5/`)

## Runtime

**Environment:**
- Python >=3.12 for the distributable package (`pyproject.toml`); the Nox matrix covers Python 3.12–3.15 and Django 4.2, 5.2, and 6.0, skipping Django 4.2 on Python 3.14+ (`noxfile.py`)
- Node.js >=20 only for the separate JavaScript test harness (`package.json`)

**Package Manager:**
- Python: `uv` for local development and Nox environment creation; `pip` is used in CI and Render builds (`taskfile.yaml`, `noxfile.py`, `.github/workflows/`)
- Lockfiles: `uv.lock`, `package-lock.json`; hashed requirements are maintained in `.github/requirements/ci.txt`, `docs/requirements.txt`, and `requirements/demo.txt`

## Frameworks

**Core:**
- Django >=4.2 - reusable CRUD class-based view package and example project (`pyproject.toml`, `src/crud_views/`)
- Pydantic >=2.2.1 - typed `CrudViewsSettings` configuration (`src/crud_views/lib/settings.py`)
- django-tables2 and django-filter - list tables and filtering (`pyproject.toml`, `src/crud_views/lib/`)
- django-crispy-forms with crispy-bootstrap5 - form rendering and Bootstrap 5 templates (`src/crud_views/lib/crispy/`)
- Optional integration extras: `workflow` (django-fsm-2, django-fsm-2-admin), `polymorphic` (django-polymorphic), `ordered` (django-ordered-model), and `guardian` (django-guardian); `all` enables all four (`pyproject.toml`)

**Testing:**
- pytest with pytest-django, pytest-cov, pytest-random-order, pytest-mock, and pytest-xdist (`pyproject.toml`, `tests/`)
- Nox provides the Python/Django compatibility matrix and installs the project as a built distribution (`noxfile.py`)
- Vitest + jsdom + jQuery for the standalone JS test suite (`package.json`, `vitest.config.js`)

**Build/Dev:**
- Hatchling is the Python build backend; wheel and source-distribution contents are explicitly configured (`pyproject.toml`)
- Ruff formats and lints Python (120-character lines, double quotes); Task runs common developer commands (`pyproject.toml`, `taskfile.yaml`)
- MkDocs with the awesome-pages plugin and pymdown-extensions builds documentation (`mkdocs.yml`, `docs/requirements.in`)
- bump-my-version synchronizes package version references (`pyproject.toml`)

## Key Dependencies

**Critical:**
- `Django` - web framework and host-project runtime; package itself does not own a Django project or deployment (`pyproject.toml`)
- `pydantic` - validates and stores package settings (`src/crud_views/lib/settings.py`)
- `python-box` - configuration/context mapping support (`pyproject.toml`)
- `django-tables2`, `django-filter`, `django-crispy-forms`, `crispy-bootstrap5` - optional UI ecosystem integration used by the core app (`pyproject.toml`)

**Infrastructure:**
- `django-guardian`, `django-polymorphic`, `django-fsm-2`, and `django-ordered-model` are opt-in extension dependencies, not mandatory for core users (`pyproject.toml`)
- `gunicorn` and `whitenoise` are used by the hosted example demo, not declared as core runtime dependencies (`render.yaml`, `requirements/demo.txt`, `examples/bootstrap5/project/settings_demo.py`)
- `django-pipeline` appears in test extras for asset-bundling coverage (`pyproject.toml`)

## Configuration

**Environment:**
- Core configuration is read from Django settings with the `CRUD_VIEWS_` prefix and defaults in `src/crud_views/lib/settings.py`; the model validates values through Pydantic
- The package has no required environment variables. Host applications provide Django settings, database configuration, auth backends, and deployment secrets
- The public example uses `SECRET_KEY` and Render-provided `RENDER_EXTERNAL_HOSTNAME` in `examples/bootstrap5/project/settings_demo.py`; only variable names are documented here
- `.env` files are not inspected; `taskfile.yaml` references an optional `dev/.env` for the local Cloudflare tunnel

**Build:**
- Python metadata, dependency extras, Hatchling targets, pytest, coverage, Ruff, and bump-my-version are in `pyproject.toml`
- Nox compatibility and targeted floor-test sessions are in `noxfile.py`
- Node test commands and dev dependencies are in `package.json`; Python JS assets are not a separate published Node package
- Task command definitions are in `taskfile.yaml`; documentation settings are in `mkdocs.yml` and `.readthedocs.yaml`

## Platform Requirements

**Development:**
- Python >=3.12, `uv`, and Task for the documented full workflow; Node >=20 and npm are needed for JS tests (`taskfile.yaml`, `package.json`)
- The primary Django test project uses in-memory SQLite databases (`tests/test1/conftest.py`)

**Production:**
- The package runs inside a consumer's Django deployment and supports the database/backends configured by that project; it does not prescribe hosting or database services
- The repository's public demo runs on Render with Python 3.13, Gunicorn, WhiteNoise, and SQLite on the free plan (`render.yaml`, `examples/bootstrap5/project/settings_demo.py`)

---

*Stack analysis: 2026-11-16*
