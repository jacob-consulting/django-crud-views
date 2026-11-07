---
last_mapped_commit: 8e1298538ef8e45fcc5c6eede15e3c6c3c067271
last_mapped_at: 2026-11-07
---
# Technology Stack

**Analysis Date:** 2026-11-07

## Languages

**Primary:**
- Python >=3.12 — distributable Django package across five apps in `src/crud_views*/` and examples in `examples/`

**Secondary:**
- JavaScript — browser behavior and tests under `src/crud_views/static/` and `tests/js*/`; Node.js >=20, CI uses Node 22 (`package.json`, `.github/workflows/js-tests.yml`)
- HTML, CSS, gettext PO/MO — Django templates, static assets, and translations in `src/` and `docs/development/i18n.md`

## Runtime

**Environment:**
- Python >=3.12; CI matrix spans Python 3.12–3.15 (`noxfile.py`, `.github/workflows/tests.yml`)
- Django >=4.2; matrix covers 4.2, 5.2, and 6.0 (`pyproject.toml`, `noxfile.py`)
- Node.js >=20 for JS harness (`package.json`)

**Package Manager:**
- Python: `uv` for development and nox virtual environments; pip for installation
- Lockfile: `uv.lock` present
- JavaScript: npm; `package-lock.json` present

## Frameworks

**Core:**
- Django >=4.2 — host web framework and ORM
- Pydantic >=2.2.1 — validated settings, ViewSets, and configuration
- django-crispy-forms >=2.0 with crispy-bootstrap5 >=2023.10 — form layouts and rendering
- django-tables2 >=2.5.3 and django-filter >=21.1 — list tables and filters

**Testing:**
- pytest with pytest-django, pytest-cov, pytest-xdist, pytest-mock, pytest-random-order
- nox — Python/Django compatibility matrix (`noxfile.py`)
- Vitest 5 and jsdom 30 — JS tests (`vitest.config.js`, `vitest.integration.config.js`)

**Build/Dev:**
- Hatchling — PEP 517 build backend and wheel packaging (`pyproject.toml`)
- Ruff >=0.17,<0.18 — formatting and linting
- MkDocs with awesome-pages, get-deps, pymdown-extensions — documentation (`mkdocs.yml`)
- bump-my-version — version synchronization (`pyproject.toml`)

## Key Dependencies

**Critical:**
- `Django`, `pydantic`, `django-crispy-forms`, `crispy-bootstrap5`, `django-tables2`, `django-filter` — package runtime dependencies declared in `pyproject.toml`
- `python-box`, `typing-extensions` — core utilities (`pyproject.toml`)

**Infrastructure:**
- `django-fsm-2` and `django-fsm-2-admin` — optional `[workflow]` extra
- `django-polymorphic` — optional `[polymorphic]` extra
- `django-ordered-model` — optional `[ordered]` extra
- `django-guardian` — optional `[guardian]` extra
- `[all]` combines the four integration extras (`pyproject.toml`)
- `lxml`, `cssselect`, `polib`, `django-pipeline` — test dependencies; `gunicorn`, `whitenoise`, `django-ratelimit` — demo requirements (`requirements/demo.txt`)

## Configuration

**Environment:**
- Package configuration comes from host Django settings; core options use `CRUD_VIEWS_*` and are modeled in `src/crud_views/lib/settings.py`.
- Example settings configure their own applications and environment; package does not load dotenv files.

**Build:**
- `pyproject.toml` defines metadata, extras, Hatchling package list, Ruff, pytest, coverage, and bump settings.
- `noxfile.py` defines Python/Django, examples, crispy-floor, and package validation sessions.
- `package.json`, `vitest.config.js`, and `vitest.integration.config.js` configure the private JS harness; `mkdocs.yml` configures docs.
- CI runs `ruff format --check .` and `ruff check .` across the repository, including Python examples inside Markdown (`.github/workflows/lint.yml`).

## Platform Requirements

**Development:**
- Python >=3.12, `uv`, and Task; Node/npm for browser-side tests (`docs/development/index.md`, `package.json`).
- Django 4.2 sessions skip Python 3.14+ (`noxfile.py`).

**Production:**
- A host Django project on supported Python/Django; no database or hosting platform is mandated by the library.
- Example deployment uses Render, Gunicorn, WhiteNoise, and ephemeral SQLite (`render.yaml`, `requirements/demo.txt`).

---

*Stack analysis: 2026-11-07*
