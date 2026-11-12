---
last_mapped_at: 2026-11-12
last_mapped_commit: 848ceddd54ff9f2e49313b862927900726d28346
---
# Technology Stack

**Analysis Date:** 2026-11-12

## Languages

**Primary:**
- Python >=3.12 - reusable Django package, split into five apps under `src/`

**Secondary:**
- JavaScript - browser behaviors and Vitest tests (`src/crud_views/static/crud_views/js/`, `tests/js/`)
- HTML, CSS, gettext catalogs - Django templates, assets, and translations under `src/`

## Runtime

**Environment:**
- Python >=3.12 is the package metadata floor (`pyproject.toml`). Nox declares Python 3.12–3.15 against Django 4.2, 5.2, and 6.0, with unsupported combinations skipped (`noxfile.py`).
- `uv.lock` records one resolved development environment (currently Django 6.1.2); those lock resolutions do not expand the declared Django support matrix or dependency bounds.
- Node.js >=20 for the dev-only browser test harness (`package.json`)

**Package Manager:**
- Python: `uv` for development and Nox environments; standard installs use Python package metadata
- Lockfile: `uv.lock` present
- JavaScript: npm with `package-lock.json`

## Frameworks

**Core:**
- Django >=4.2 - host framework for URL routing, ORM, auth, templates, and app integration
- Pydantic >=2.2.1 - typed ViewSet and settings models (`src/crud_views/lib/viewset/__init__.py`, `src/crud_views/lib/settings.py`)
- django-crispy-forms >=2.0 and crispy-bootstrap5 >=2023.10 - Bootstrap form rendering (`src/crud_views/lib/crispy/`)
- django-tables2 >=2.5.3 and django-filter >=21.1 - list tables and filtering (`src/crud_views/lib/table/`, `src/crud_views/lib/views/mixins.py`)

**Testing:**
- pytest, pytest-django, pytest-cov, pytest-xdist, pytest-mock, pytest-random-order - Python tests (`pyproject.toml`, `noxfile.py`)
- Vitest, jsdom, and jQuery - dev-only JavaScript tests (`package.json`)

**Build/Dev:**
- Hatchling - wheel and sdist backend; the wheel contains five apps and the sdist uses an explicit allowlist (`pyproject.toml`)
- Ruff - lint and format; 120-character lines and double quotes (`pyproject.toml`)
- MkDocs with awesome-pages and pymdown-extensions - documentation (`mkdocs.yml`)
- Nox, Task, pre-commit, and bump-my-version - test matrix and maintenance (`noxfile.py`, `taskfile.yaml`, `.pre-commit-config.yaml`, `pyproject.toml`)

## Key Dependencies

**Critical:**
- Required runtime dependencies and declared minimums: `django>=4.2.0`, `pydantic>=2.2.1`, `python-box>=6.0.2`, `django-tables2>=2.5.3`, `django-filter>=21.1`, `typing-extensions>=4.7.1`, `django-crispy-forms>=2.0`, and `crispy-bootstrap5>=2023.10` (`pyproject.toml`).
- `uv.lock` contains a current resolution, while `noxfile.py` verifies the crispy minimum floor in dedicated sessions; neither should be read as changing package metadata bounds.

**Infrastructure:**
- `[workflow]`: `django-fsm-2`, `django-fsm-2-admin`; `[polymorphic]`: `django-polymorphic`; `[ordered]`: `django-ordered-model`; `[guardian]`: `django-guardian` (`pyproject.toml`)
- `[all]` combines the four extension extras; `[test]` adds test tooling and Django integrations; `[examples]` adds Pygments (`pyproject.toml`)
- Demo-only dependencies are Gunicorn, WhiteNoise, and django-ratelimit (`requirements/demo.txt`)
- Formset layouts, including compact layouts, use existing Django forms and crispy APIs; no additional package dependency is introduced (`src/crud_views/lib/formsets/compact.py`, `src/crud_views/lib/formsets/layout.py`)
- Compact formsets support Django's exact stock `CheckboxInput` widget without an opt-in marker. Custom widgets and templates need the documented compatibility marker and remain responsible for their markup (`docs/reference/formsets.md`).

## Configuration

**Environment:**
- The package reads runtime options from host Django settings; core settings are modeled in `src/crud_views/lib/settings.py` and use the `CRUD_VIEWS_*` prefix
- Object-detail settings are modeled in `src/crud_views_object_detail/lib/conf.py`; the library does not require environment variables or dotenv loading
- Host projects supply database, authentication, static-file, and deployment settings; the demo has separate local and Render settings (`examples/bootstrap5/project/settings.py`, `examples/bootstrap5/project/settings_demo.py`)

**Build:**
- `pyproject.toml` - package metadata, extras, Hatchling, Ruff, pytest, and coverage configuration
- `uv.lock` - resolved Python environment
- `noxfile.py` and `taskfile.yaml` - matrix sessions and task shortcuts
- `package.json` and `package-lock.json` - JavaScript test harness
- `mkdocs.yml`, `.readthedocs.yaml`, and `settings_i18n.py` - docs and translation tooling
- `.github/workflows/` - test, lint, docs, JavaScript, package publishing, example, and demo automation

## Platform Requirements

**Development:**
- Python >=3.12, `uv`, and Task; Node/npm for JavaScript tests; Docker is optional for the local tunnel (`dev/docker-compose.yaml`)

**Production:**
- Any Django host project; the package selects no database, cache, storage, or hosting provider
- Public demo deploys to Render with Gunicorn, WhiteNoise, and SQLite (`render.yaml`, `requirements/demo.txt`)

---

*Stack analysis: 2026-11-12*
