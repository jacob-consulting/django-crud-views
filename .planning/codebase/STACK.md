---
last_mapped_commit: 4feb0196e169745b7ec9bf879abfbfa45c647e92
last_mapped_at: 2026-11-21
---
# Technology Stack

**Analysis Date:** 2026-11-21

## Languages

**Primary:**
- Python >=3.12 (tested on 3.12–3.15) - five installable Django apps under `src/`
- Django templates with Bootstrap 5 markup - theme templates under `src/crud_views/templates/`

**Secondary:**
- JavaScript (Node >=20) - development-only Vitest harness (`package.json`, `vitest.config.js`, `vitest.integration.config.js`); package scripts in `src/*/static/`
- YAML - CI, task automation, deployment, docs, and dependency update configuration

## Runtime

**Environment:**
- CPython >=3.12; nox covers 3.12, 3.13, 3.14, and 3.15 (`noxfile.py`)
- Django >=4.2; CI/nox matrix covers Django 4.2, 5.2, and 6.0 (`pyproject.toml`, `noxfile.py`); Django 4.2 is skipped on Python 3.14+
- Bulk action flows are implemented inside the core Python package and use the existing Django ORM and django-tables2 dependencies; no additional runtime dependency is required (`src/crud_views/lib/bulk/`)
- Demo runs Python 3.13 on Render (`render.yaml`)

**Package Manager:**
- uv for Python environments and lockfile (`uv.lock`); nox uses its uv backend (`noxfile.py`)
- npm for JavaScript checks (`package-lock.json`)
- Lockfiles: `uv.lock`, `package-lock.json`; docs and CI dependencies are hash-pinned in `docs/requirements.txt` and `.github/requirements/ci.txt`

## Frameworks

**Core:**
- Django >=4.2 - generic class-based views and reusable app integration (`src/crud_views/`)
- Pydantic >=2.2.1 - ViewSet/settings and typed configuration (`src/crud_views/lib/viewset/`, `src/crud_views/lib/settings.py`)
- django-tables2 >=2.5.3 and django-filter >=21.1 - table rendering and filtering
- django-crispy-forms >=2.0 with crispy-bootstrap5 >=2023.10 - Bootstrap form rendering (`src/crud_views/lib/crispy/`)

**Testing:**
- pytest, pytest-django, pytest-xdist, pytest-cov, pytest-mock, pytest-random-order - Python test suite (`pyproject.toml` test extra)
- nox - Python/Django compatibility matrix and installed-distribution checks (`noxfile.py`)
- Vitest 5, jsdom 31, and jQuery 3.7 - static JavaScript unit and integration tests (`package.json`)

**Build/Dev:**
- hatchling - wheel and sdist backend; package allowlist in `pyproject.toml`, verified by `scripts/check_dist.py`
- Ruff >=0.17,<0.18 - lint and format, 120-character lines (`pyproject.toml`)
- pre-commit, bump-my-version, go-task - hooks, version updates, and task commands (`.pre-commit-config.yaml`, `pyproject.toml`, `taskfile.yaml`)
- MkDocs with awesome-pages and pymdown-extensions; Read the Docs theme (`mkdocs.yml`)

## Key Dependencies

**Critical:**
- `python-box` >=6.0.2 and `typing-extensions` >=4.7.1 - core runtime support (`pyproject.toml`)
- Django, Pydantic, django-tables2, django-filter, django-crispy-forms, crispy-bootstrap5 - core view and form API (`pyproject.toml`)
- Bulk selection/action support composes Django ORM transactions and querysets, django-tables2 selection columns, Django messages, and the existing Crispy form/theme layer (`src/crud_views/lib/bulk/__init__.py`)
- The classic `bulk.js` script enhances current-page table/card selection through native form controls, without jQuery, a UI adapter, a network request, or persistent storage; the core JavaScript settings include it (`src/crud_views/static/crud_views/js/bulk.js`, `src/crud_views/lib/settings.py`, `docs/reference/javascript.md`)
- Stock table sorting uses django-tables2 bound-column effective ordering for icons and `aria-sort`, including default and prefixed ordering; preserve the existing `table.thead` override for custom header semantics (`src/crud_views/templates/crud_views/table/bootstrap5.html`, `docs/reference/list_view.md`)

**Optional extras (one app/feature group each):**
- `workflow`: django-fsm-2 >=4.0.0 and django-fsm-2-admin >=2.0.1 (`src/crud_views_workflow/`)
- `polymorphic`: django-polymorphic >=3.1.0 (`src/crud_views_polymorphic/`)
- `ordered`: django-ordered-model >=3.4.3 (`src/crud_views/lib/views/action_ordered.py`)
- `guardian`: django-guardian >=2.4 (`src/crud_views_guardian/`)
- `all` aggregates those extras; `object_detail` is included in the distribution without an extra (`pyproject.toml`)
- Test extras include django-pipeline for asset-pipeline integration coverage (`pyproject.toml`)

**Demo infrastructure:**
- gunicorn, whitenoise, and django-ratelimit are declared in `requirements/demo.txt`

## Configuration

**Environment:**
- Library configuration is Django settings with `CRUD_VIEWS_*` names, parsed by `CrudViewsSettings` in `src/crud_views/lib/settings.py`; includes theme/template and manage-view options
- Compatible theme native data-API attributes use the process-level prefix registry in `src/crud_views/lib/data_prefix.py`, defaulting to `bs`; a theme registers its prefix during `AppConfig.ready()` through the public `crud_views.lib.register_data_prefix` API. This is startup configuration, not a `CRUD_VIEWS_*` setting or runtime theme switch
- Breadcrumb styling uses the existing button-class registry keys `breadcrumb:list`, `breadcrumb:item`, and `breadcrumb:item-active`. Theme startup registration and project `CRUD_VIEWS_BUTTON_CLASSES` overrides share the existing class lookup (`src/crud_views/lib/button_classes.py`, `src/crud_views/templates/crud_views/tags/breadcrumb.html`, `docs/reference/theme.md`)
- Tests set `CV_ACCESS_RECORD_REQUESTS` from `noxfile.py`
- Local Cloudflare tunnel reads `TUNNEL_TOKEN` from `dev/.env`; only the existence of local env files was checked (`dev/.env.example`, `dev/docker-compose.yaml`)
- Demo uses `DJANGO_SETTINGS_MODULE=project.settings_demo` and a generated `SECRET_KEY` (`render.yaml`)

**Build:**
- `pyproject.toml` defines dependencies and wheel/sdist file inclusion; `scripts/check_dist.py` checks the sdist allowlist
- `noxfile.py`, `taskfile.yaml`, `codecov.yml`, `.sonarcloud.properties`, `mkdocs.yml`, and `vitest.config.js` configure development and CI tooling
- Demo deployment dependencies are separated into `requirements/demo.txt`; CI, docs, and package publishing dependencies are hash-pinned in `.github/requirements/ci.txt` and `docs/requirements.txt`

## Platform Requirements

**Development:**
- uv, go-task, Python 3.12+, and Node >=20 for JavaScript tests
- Optional Docker for Cloudflare tunnel in `dev/docker-compose.yaml`
- Example application lives in `examples/bootstrap5/` and uses SQLite (`examples/bootstrap5/project/settings.py`)

**Production:**
- Package distribution to PyPI using GitHub Actions (`.github/workflows/publish.yml`)
- Documentation hosted by Read the Docs (`.readthedocs.yaml`)
- Public example demo hosted on Render (`render.yaml`)

---

*Stack analysis: 2026-11-21*
