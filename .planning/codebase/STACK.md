---
last_mapped_commit: ce3903c37a05b334ded3d3c655a4534836fc6132
last_mapped_at: 2026-11-23
---
# Technology Stack

**Analysis Date:** 2026-11-23

## Languages

**Primary:**
- Python >=3.12 (tested on 3.12–3.15) - five installable Django apps under `src/`: `crud_views`, `crud_views_object_detail`, `crud_views_workflow`, `crud_views_polymorphic`, and `crud_views_guardian`
- Django templates with Bootstrap 5 markup - theme templates under `src/crud_views/templates/`

**Secondary:**
- JavaScript - browser-side enhancement scripts shipped as Django static files; the optional Node >=20 Vitest/jsdom harness is development-only (`package.json`, `vitest.config.js`, `vitest.integration.config.js`)
- YAML - CI, task automation, deployment, docs, and dependency update configuration (`.github/workflows/`, `taskfile.yaml`, `render.yaml`, `mkdocs.yml`, `.github/dependabot.yml`)

## Runtime

**Environment:**
- CPython >=3.12; nox covers 3.12, 3.13, 3.14, and 3.15 (`noxfile.py`)
- Django >=4.2; CI/nox matrix covers Django 4.2, 5.2, and 6.0 (`pyproject.toml`, `noxfile.py`); Django 4.2 is skipped on Python 3.14+
- Bulk action flows are implemented inside the core Python package and use the existing Django ORM and django-tables2 dependencies; no additional runtime dependency is required (`src/crud_views/lib/bulk/`)
- Demo runs Python 3.13 on Render (`render.yaml`)

**Package Manager:**
- uv for Python environments, installs, and builds (`taskfile.yaml`); nox uses its uv backend (`noxfile.py`)
- npm for JavaScript checks (`package-lock.json`)
- Lockfiles: `package-lock.json` present; no `uv.lock` present. Docs and CI dependencies are hash-pinned in `docs/requirements.txt` and `.github/requirements/ci.txt`; runtime Python dependencies use lower bounds in `pyproject.toml`

## Frameworks

**Core:**
- Django >=4.2 - generic class-based views and reusable app integration (`src/crud_views/`)
- Django app package group: core CRUD views plus object detail, workflow, polymorphic, and guardian extensions (`src/crud_views*/apps.py`)
- Pydantic >=2.2.1 - ViewSet/settings and typed configuration (`src/crud_views/lib/viewset/`, `src/crud_views/lib/settings.py`)
- django-tables2 >=2.5.3 and django-filter >=21.1 - table rendering and filtering (`pyproject.toml`, `src/crud_views/lib/views/mixins.py`)
- django-crispy-forms >=2.0 with crispy-bootstrap5 >=2023.10 - Bootstrap form rendering (`src/crud_views/lib/crispy/`)
- Bootstrap 5-compatible JavaScript adapters - host-supplied UI library components; the package ships adapter code, not Bootstrap itself; the stock modal adapter derives its hide/hidden event names from the registered data prefix, so a fork such as CoreUI works without a custom adapter (PR #405) (`src/crud_views/static/crud_views/js/adapters.js`)
- jQuery is required for the optional formset enhancement; the script reports a missing library and does not initialize formsets without it. The development harness declares jQuery ~3.7.1 (`src/crud_views/static/crud_views/js/formset.js`, `package.json`)

**Testing:**
- pytest, pytest-django, pytest-xdist, pytest-cov, pytest-mock, pytest-random-order - Python test suite (`pyproject.toml` test extra)
- nox - Python/Django compatibility matrix and installed-distribution checks (`noxfile.py`)
- Vitest ^5.1.0, jsdom ^31.0.0, and jQuery ~3.7.1 - static JavaScript unit and integration tests (`package.json`, `vitest.config.js`, `vitest.integration.config.js`)

**Build/Dev:**
- hatchling - wheel and sdist backend; package allowlist in `pyproject.toml`, verified by `scripts/check_dist.py`
- Ruff >=0.17,<0.18 - lint and format, 120-character lines (`pyproject.toml`)
- pre-commit, bump-my-version, go-task - hooks, version updates, and task commands (`.pre-commit-config.yaml`, `pyproject.toml`, `taskfile.yaml`)
- MkDocs with awesome-pages and pymdown-extensions; Read the Docs theme (`mkdocs.yml`)

## Key Dependencies

**Critical:**
- `python-box` >=6.0.2 and `typing-extensions` >=4.7.1 - core runtime support (`pyproject.toml`)
- The five Django apps are built into one distribution; `object_detail` ships in the base install, while `workflow`, `polymorphic`, `ordered`, and `guardian` dependency groups are opt-in extras (`pyproject.toml`)
- Django, Pydantic, django-tables2, django-filter, django-crispy-forms, crispy-bootstrap5 - core view and form API (`pyproject.toml`)
- Bulk selection/action support composes Django ORM transactions and querysets, django-tables2 selection columns, Django messages, and the existing Crispy form/theme layer (`src/crud_views/lib/bulk/__init__.py`)
- Bulk toolbar variants use a dedicated template leaf and existing semantic class registry. Read the variant from each destination's `cv_action_variant` (inherited default `secondary`), and configure `bulk:primary`, `bulk:secondary`, `bulk:tertiary`, or `bulk:danger`; all stock values are `btn btn-primary`. Review Confirm retains the separate `form:submit` contract (`src/crud_views/templates/crud_views/tags/button/bulk.html`, `src/crud_views/lib/button_classes.py`, `docs/reference/bulk_actions.md`)
- Bulk toolbar buttons are built in Python (cached `cv_bulk_buttons`, evaluated in `get_context_data` so presentation errors surface) and offered only for destinations that pass `cv_has_access`/`cv_action_enabled` for the viewer; no extra runtime dependency (PR #404, `src/crud_views/lib/bulk/__init__.py`)
- Bulk label mode uses the lazy `bulk` location floor (default `both`) in `CRUD_VIEWS_LABEL_MODE_DEFAULTS`. Mode-specific class keys such as `bulk:danger:icon` use the effective mode after missing/disabled icons fall back to `label`; the leaf reuses form tooltip, hidden-label, and host-icon conventions (`src/crud_views/lib/bulk/__init__.py`, `src/crud_views/lib/view/label_mode.py`, `src/crud_views/templates/crud_views/tags/button/bulk.html`)
- Manage pages and formsets consume six optional `--cv-*` CSS custom properties with Bootstrap and literal fallbacks; the package does not define these tokens globally (`src/crud_views/static/crud_views/css/manage.css`, `src/crud_views/static/crud_views/css/formset.css`, `docs/reference/theme.md`)
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
- Bootstrap-compatible themes can independently register the JavaScript global namespace and tooltip placement defaults during `AppConfig.ready()` with `register_js_namespace()` and `register_tooltip_placements()` (`src/crud_views/lib/js_config.py`, `src/crud_views/lib/__init__.py`). Defaults are `bootstrap` and `{}`; the three values are rendered on `#cv-config` and consumed by the adapter (`src/crud_views/templates/crud_views/tags/cv_config.html`, `src/crud_views/static/crud_views/js/adapters.js`)
- Breadcrumb styling uses the existing button-class registry keys `breadcrumb:list`, `breadcrumb:item`, and `breadcrumb:item-active`. Theme startup registration and project `CRUD_VIEWS_BUTTON_CLASSES` overrides share the existing class lookup (`src/crud_views/lib/button_classes.py`, `src/crud_views/templates/crud_views/tags/breadcrumb.html`, `docs/reference/theme.md`)
- Tests set `CV_ACCESS_RECORD_REQUESTS` from `noxfile.py`
- Local Cloudflare tunnel setup uses a local `dev/.env` file; `task cf` checks that it exists before Docker Compose starts. `dev/.env.example` is tracked; environment-file contents are not read (`taskfile.yaml`, `dev/docker-compose.yaml`)
- Demo uses `DJANGO_SETTINGS_MODULE=project.settings_demo` and a generated `SECRET_KEY` (`render.yaml`)

**Build:**
- `pyproject.toml` defines dependencies and wheel/sdist file inclusion; `scripts/check_dist.py` checks the sdist allowlist
- `noxfile.py`, `taskfile.yaml`, `codecov.yml`, `.sonarcloud.properties`, `mkdocs.yml`, and `vitest.config.js` configure development and CI tooling
- Demo deployment dependencies are separated into `requirements/demo.txt`; CI, docs, and package publishing dependencies are hash-pinned in `.github/requirements/ci.txt` and `docs/requirements.txt`
- Package version is `0.30.0`; bump-my-version synchronizes `pyproject.toml`, `src/crud_views/__init__.py`, `docs/index.md`, and `README.md`. Wheel contents contain five `src/` apps; sdist uses an explicit allowlist (`pyproject.toml`)

## Platform Requirements

**Development:**
- uv, go-task, Python 3.12+, and Node >=20 for JavaScript tests (`taskfile.yaml`, `pyproject.toml`, `package.json`); JavaScript CI selects Node 22 (`.github/workflows/js.yml`)
- Cross-repo Acme example sync tooling in `superpowers/prompts/acme-example-sync/` (`drift.py` is standard-library Python that reads git blob ids from sibling theme checkouts and compares them to `baseline.json`; `PROMPT.md` drives the sync). Development-only, not shipped in the wheel
- Optional Docker for Cloudflare tunnel in `dev/docker-compose.yaml`
- Example application lives in `examples/bootstrap5/` and uses SQLite (`examples/bootstrap5/project/settings.py`)

**Production:**
- Package distribution to PyPI using GitHub Actions (`.github/workflows/publish.yml`)
- Documentation hosted by Read the Docs (`.readthedocs.yaml`)
- Public example demo hosted on Render (`render.yaml`)

---

*Stack analysis: 2026-11-23*
