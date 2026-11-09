---
last_mapped_at: 2026-11-09
last_mapped_commit: 910d8bb98ea06a21ff838dacd56704c0ce31e4de
---
# Technology Stack

**Analysis Date:** 2026-11-09

## Languages

**Primary:**
- Python >=3.12 - distributable Django package, five apps in `src/crud_views*/`, examples in `examples/bootstrap5/`, tests in `tests/`

**Secondary:**
- JavaScript - browser behavior in `src/crud_views/static/crud_views/js/` (`adapters.js`, `formset.js`, `modal.js`, `toggle.js`, `tooltip.js`); tests under `tests/js*/`. Node >=20 (`package.json`), CI uses Node 22 (`.github/workflows/js.yml`)
- HTML (Django templates), CSS, gettext PO/MO translations (locale `de`, `taskfile.yaml` vars `LOCALES`, `I18N_PACKAGES`)

## Runtime

**Environment:**
- Python >=3.12; matrix 3.12, 3.13, 3.14, 3.15 (`noxfile.py`, `.github/workflows/tests.yml`)
- Django >=4.2; matrix 4.2, 5.2, 6.0. Django 4.2 sessions skip Python 3.14+ (`noxfile.py`)
- Node >=20 for the JS harness only

**Package Manager:**
- Python: `uv` (dev, nox `venv_backend="uv"`); pip for installation
- Lockfile: `uv.lock` present
- JavaScript: npm, `package-lock.json` present
- Pinned hashed CI/docs locks: `.github/requirements/ci.txt`, `docs/requirements.txt` (kept fresh by `.github/dependabot.yml`, 7-day cooldown)

## Frameworks

**Core:**
- Django >=4.2 - host framework and ORM
- Pydantic >=2.2.1 - ViewSet models and settings (`src/crud_views/lib/settings.py`, `src/crud_views/lib/viewset/__init__.py`)
- django-crispy-forms >=2.0 + crispy-bootstrap5 >=2023.10 - form rendering (`src/crud_views/lib/crispy/`)
- django-tables2 >=2.5.3, django-filter >=21.1 - list tables and filters

**Testing:**
- pytest, pytest-django, pytest-cov, pytest-xdist, pytest-mock, pytest-random-order; nox matrix (`noxfile.py`)
- lxml, cssselect, polib (test extras); Vitest ^5.0.5 + jsdom ^30.1.3 + jquery ~3.7.1 (`package.json`, `vitest.config.js`, `vitest.integration.config.js`)

**Build/Dev:**
- Hatchling - build backend; wheel packages the five `src/` apps, sdist uses `only-include` allowlist verified by `scripts/check_dist.py`
- Ruff >=0.17,<0.18 - format and lint (line length 120, rules E,F,I,UP,B,C4,SIM,RUF)
- MkDocs (readthedocs theme) with awesome-pages and pymdown-extensions (`mkdocs.yml`)
- bump-my-version, pre-commit (`ruff-format`), Task (`taskfile.yaml`)

## Key Dependencies

**Critical:**
- `django`, `pydantic`, `python-box`, `typing-extensions`, `django-tables2`, `django-filter`, `django-crispy-forms`, `crispy-bootstrap5` (`pyproject.toml`)

**Optional extras:**
- `[workflow]`: `django-fsm-2>=4.0.0`, `django-fsm-2-admin>=2.0.1` (`src/crud_views_workflow/`)
- `[polymorphic]`: `django-polymorphic>=3.1.0` (`src/crud_views_polymorphic/`)
- `[ordered]`: `django-ordered-model>=3.4.3`
- `[guardian]`: `django-guardian>=2.4` (`src/crud_views_guardian/`)
- `[all]` combines the four; `[examples]`: `pygments`; `[test]` also pulls `django-guardian`, `django-pipeline`

**Demo-only (`requirements/demo.txt`):** `gunicorn>=23`, `whitenoise>=6.9`, `django-ratelimit>=4.1`

## Configuration

**Environment:**
- Package config from host Django settings with `CRUD_VIEWS_*` names, modeled in `src/crud_views/lib/settings.py` (e.g. `CRUD_VIEWS_EXTENDS`, `CRUD_VIEWS_MANAGE_VIEWS_ENABLED`, `CRUD_VIEWS_MANAGE_GROUP`, `CRUD_VIEWS_SESSION_DATA_KEY`, `CRUD_VIEWS_ORIGIN_PARAM`, `CRUD_VIEWS_CSP_NONCE_ATTR`, `CRUD_VIEWS_ASSETS_BUNDLED`, `CRUD_VIEWS_INACCESSIBLE_ACTIONS`, `CRUD_VIEWS_HEADER_LEVEL`, `CRUD_VIEWS_DELETE_PREVIEW_LIMIT`, `CRUD_VIEWS_BREADCRUMB_PREFIX`, `CRUD_VIEWS_*_LABEL_MODE`, `CRUD_VIEWS_*_CONTEXT_ACTIONS`, filter persistence/pinned)
- Object-detail settings cached separately in `src/crud_views_object_detail/lib/conf.py` (`CRUD_VIEWS_OBJECT_DETAIL_*`)
- Asset registration with CSP nonce and SRI, optional django-pipeline bundling (`src/crud_views/lib/assets.py`, `src/crud_views/lib/pipeline.py`, `src/crud_views/management/commands/cv_assets.py`)
- i18n extraction settings: `settings_i18n.py`, `src/` locale dirs
- No dotenv loading in the package; `dev/.env` (tunnel token) exists for local dev only and is not read

**Build:**
- `pyproject.toml` (metadata, extras, hatch, ruff, pytest `--strict-markers`, coverage), `noxfile.py` (sessions: `tests`, `crispy_floor`, `examples`, `package`), `taskfile.yaml`, `codecov.yml`, `mkdocs.yml`, `.readthedocs.yaml`

## Platform Requirements

**Development:**
- Python >=3.12, `uv`, Task; Node/npm for JS tests; optional Docker for Cloudflare tunnel (`dev/docker-compose.yaml`)

**Production:**
- A host Django project; no database or host mandated. Demo runs on Render free plan with Gunicorn, WhiteNoise, ephemeral SQLite (`render.yaml`)

---

*Stack analysis: 2026-11-09*
