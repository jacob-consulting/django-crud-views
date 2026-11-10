---
last_mapped_at: 2026-11-10
last_mapped_commit: 83fb88014f76f3c500964a822b06e3ff8c5f4c7b
---
# Technology Stack

**Analysis Date:** 2026-11-10

## Languages

**Primary:**
- Python >=3.12 - installable Django library, split across five packages under `src/`

**Secondary:**
- JavaScript - browser behavior and tests under `src/crud_views/static/` and `tests/js*/`
- HTML, CSS, gettext catalogs - Django templates, styling, and translations in `src/crud_views/templates/`, `src/crud_views/static/`, and locale directories

## Runtime

**Environment:**
- Python >=3.12; CI/nox covers 3.12–3.15 (`pyproject.toml`, `noxfile.py`, `.github/workflows/tests.yml`)
- Django >=4.2; supported matrix is 4.2, 5.2, and 6.0 (`pyproject.toml`, `noxfile.py`); Django 4.2 sessions skip Python 3.14+
- Node.js >=20 and npm for the JavaScript test harness (`package.json`, `package-lock.json`)

**Package Manager:**
- Python: `uv` for development and nox environments; `pip` for normal installs
- Lockfile: `uv.lock` present
- JavaScript: npm; `package-lock.json` present

## Frameworks

**Core:**
- Django >=4.2 - host framework, ORM, auth, templates, and app integration
- Pydantic >=2.2.1 - typed `ViewSet` and settings models (`src/crud_views/lib/viewset/__init__.py`, `src/crud_views/lib/settings.py`)
- django-crispy-forms >=2.0 and crispy-bootstrap5 >=2023.10 - form rendering (`src/crud_views/lib/crispy/`)
- django-tables2 >=2.5.3 and django-filter >=21.1 - list tables, filtering, and pagination (`src/crud_views/lib/table/`, `src/crud_views/lib/views/mixins.py`)

**Testing:**
- pytest, pytest-django, pytest-cov, pytest-xdist, pytest-mock, pytest-random-order - Python tests (`noxfile.py`, `pyproject.toml`)
- Vitest, jsdom, and jQuery - JavaScript tests (`package.json`, `vitest.config.js`, `vitest.integration.config.js`)

**Build/Dev:**
- Hatchling - wheel and source distribution backend (`pyproject.toml`); wheel includes five `src/` apps and sdist uses an explicit allowlist
- Ruff - lint and formatting (`pyproject.toml`); line length 120, double quotes
- MkDocs with Read the Docs theme, awesome-pages, and pymdown-extensions (`mkdocs.yml`)
- Nox, Task, pre-commit, bump-my-version - test matrix and maintenance (`noxfile.py`, `taskfile.yaml`, `.pre-commit-config.yaml`, `pyproject.toml`)

## Key Dependencies

**Critical:**
- `django`, `pydantic`, `python-box`, `typing-extensions`, `django-tables2`, `django-filter`, `django-crispy-forms`, `crispy-bootstrap5` - required package dependencies (`pyproject.toml`)

**Optional extras:**
- `[workflow]`: `django-fsm-2`, `django-fsm-2-admin` - state transitions and admin support (`src/crud_views_workflow/`)
- `[polymorphic]`: `django-polymorphic` - polymorphic model support (`src/crud_views_polymorphic/`)
- `[ordered]`: `django-ordered-model` - ordering actions when host models use it
- `[guardian]`: `django-guardian` - per-object permissions (`src/crud_views_guardian/`)
- `[all]` installs the four extension extras; `[test]` adds test tools plus Guardian and django-pipeline; `[examples]` adds Pygments (`pyproject.toml`)
- Demo-only requirements include Gunicorn, WhiteNoise, and django-ratelimit (`requirements/demo.txt`)

## Configuration

**Environment:**
- Runtime configuration is read from host Django settings; core options are modeled in `src/crud_views/lib/settings.py` and use the `CRUD_VIEWS_*` prefix
- Object-detail options are modeled separately in `src/crud_views_object_detail/lib/conf.py`; settings can configure themes, assets, permissions, buttons, icons, and display behavior
- `Icon` in `src/crud_views/lib/icons.py` is a plain namespace of primitive values (`VIEWSET_DEFAULT = None`, `NONE = ""`), not a Pydantic enum or extra dependency
- Asset registration supports CSP nonce and SRI attributes; optional django-pipeline integration is implemented without importing pipeline at settings import time (`src/crud_views/lib/assets.py`, `src/crud_views/lib/pipeline.py`)
- The library defines no required environment variables and does not load dotenv files

**Build:**
- `pyproject.toml` - package metadata, dependencies, extras, Hatchling, Ruff, pytest, and coverage configuration
- `noxfile.py` - Python/Django test matrix and package checks
- `taskfile.yaml`, `mkdocs.yml`, `.readthedocs.yaml`, `settings_i18n.py` - task shortcuts, docs, and translation extraction

## Platform Requirements

**Development:**
- Python >=3.12, `uv`, and Task; Node/npm for browser JavaScript tests; Docker is optional for the local tunnel (`dev/docker-compose.yaml`)

**Production:**
- Any Django host project; the package selects no database, cache, storage, or hosting provider
- Public example deploys to Render with Gunicorn, WhiteNoise, and ephemeral SQLite (`render.yaml`, `requirements/demo.txt`)

---

*Stack analysis: 2026-11-10*
