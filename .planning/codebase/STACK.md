---
last_mapped_commit: 54c18a1b65f038e5fcdb5dc0038782133f93ffb8
last_mapped_at: 2026-11-17
---
# Technology Stack

**Analysis Date:** 2026-11-17

## Languages

**Primary:**
- Python >=3.12 (tested 3.12, 3.13, 3.14, 3.15) - all package code in `src/`
- Django templates (HTML, Bootstrap 5) - `src/crud_views/templates/`

**Secondary:**
- JavaScript (Node >=20) - dev-only unit-test harness (`package.json`, `vitest.config.js`, `vitest.integration.config.js`); package static JS under `src/*/static/`
- YAML - CI (`.github/workflows/*.yml`), `taskfile.yaml`, `mkdocs.yml`, `render.yaml`

## Runtime

**Environment:**
- CPython 3.12 baseline (`taskfile.yaml` var `PYTHON`, `.readthedocs.yaml`); demo deploy pins 3.13 (`render.yaml`)
- Django 4.2 / 5.2 / 6.0 supported (Django 4.2 skipped on Python 3.14+ in `noxfile.py`)

**Package Manager:**
- uv (venv, `uv.lock`, nox `venv_backend="uv"`); pip with hashes in CI (`.github/requirements/ci.txt`)
- npm for JS tests (`package-lock.json`)
- Lockfile: present (`uv.lock`, `package-lock.json`, `docs/requirements.txt` hashed)

## Frameworks

**Core:**
- Django >=4.2 - web framework; class-based views
- Pydantic >=2.2.1 - ViewSet and settings models (`src/crud_views/lib/viewset/__init__.py`, `src/crud_views/lib/settings.py`)
- django-tables2 >=2.5.3 - list tables
- django-filter >=21.1 - list filtering
- django-crispy-forms >=2.0 + crispy-bootstrap5 >=2023.10 - forms (`src/crud_views/lib/crispy/`)

**Testing:**
- pytest, pytest-django, pytest-xdist, pytest-cov, pytest-mock, pytest-random-order; lxml, cssselect, polib (`pyproject.toml` `test` extra)
- nox - Python x Django matrix (`noxfile.py`)
- vitest ^5.1 + jsdom ^31 + jquery ~3.7 - JS tests

**Build/Dev:**
- hatchling - build backend (`pyproject.toml`)
- ruff >=0.17,<0.18 - lint/format (line length 120, rules E,F,I,UP,B,C4,SIM,RUF)
- pre-commit (`.pre-commit-config.yaml`), bump-my-version, go-task (`taskfile.yaml`)
- mkdocs + awesome-pages + pymdown-extensions, readthedocs theme (`mkdocs.yml`)

## Key Dependencies

**Critical:**
- python-box >=6.0.2, typing-extensions >=4.7.1 - core runtime deps

**Optional extras (one Django app each):**
- `workflow`: django-fsm-2 >=4.0.0, django-fsm-2-admin >=2.0.1 (`src/crud_views_workflow`)
- `polymorphic`: django-polymorphic >=3.1.0 (`src/crud_views_polymorphic`)
- `ordered`: django-ordered-model >=3.4.3
- `guardian`: django-guardian >=2.4 (`src/crud_views_guardian`)
- `all` aggregates the above; `object_detail` app has no extra (`src/crud_views_object_detail`)
- Test-only: django-pipeline (asset bundling tests)

**Infrastructure (demo only, `requirements/demo.txt`):**
- gunicorn >=23, whitenoise >=6.9, django-ratelimit >=4.1

## Configuration

**Environment:**
- Library settings: Pydantic `CrudViewsSettings` reading `CRUD_VIEWS_*` Django settings (`src/crud_views/lib/settings.py`), e.g. `CRUD_VIEWS_EXTENDS`, `CRUD_VIEWS_THEME`, `CRUD_VIEWS_MANAGE_VIEWS_ENABLED`, `CRUD_VIEWS_MANAGE_ACCESS_TRACE`
- Test env flag `CV_ACCESS_RECORD_REQUESTS` (set in `noxfile.py`)
- `.env`-style file for dev tunnel at `dev/.env` (not read; template `dev/.env.example`)
- Demo: `DJANGO_SETTINGS_MODULE=project.settings_demo`, `SECRET_KEY` (`render.yaml`)

**Build:**
- `pyproject.toml` (wheel packages: five `src/` apps; sdist allowlist checked by `scripts/check_dist.py`)
- `noxfile.py`, `taskfile.yaml`, `codecov.yml`, `.sonarcloud.properties`

## Platform Requirements

**Development:**
- uv, go-task, Python 3.12+, Node >=20 (JS tests), optional Docker for `dev/docker-compose.yaml`
- Example project: `examples/bootstrap5/` (SQLite `db.sqlite3`)

**Production:**
- Library published to PyPI via `pypa/gh-action-pypi-publish` (`.github/workflows/publish.yml`)
- Docs on Read the Docs (`.readthedocs.yaml`); public demo on Render free plan (`render.yaml`)

---

*Stack analysis: 2026-11-17*
