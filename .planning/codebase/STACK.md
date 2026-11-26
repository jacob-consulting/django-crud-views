---
last_mapped_commit: 7d9b74dc51306d98ce007cd001f416463982c456
last_mapped_at: 2026-11-26
---
# Technology Stack

**Analysis Date:** 2026-11-26

## Languages

**Primary:**
- Python >=3.12: five Django apps under `src/`; library requirements and Python classifiers are in `pyproject.toml`.

**Secondary:**
- Django templates/HTML and CSS: `src/*/templates/` and `src/crud_views/static/crud_views/css/`.
- JavaScript: native browser enhancements in `src/crud_views/static/crud_views/js/` and object-detail tabs in `src/crud_views_object_detail/static/crud_views_object_detail/js/tabs.js`.
- Markdown documentation built through `mkdocs.yml`.

## Runtime

**Environment:**
- Reusable Django distribution version 0.30.0, shipping core, object-detail, workflow, polymorphic, and Guardian apps (`pyproject.toml`).
- Python classifiers: 3.12, 3.13, 3.14, 3.15; Django classifiers: 4.2, 5.2, 6.0 (`pyproject.toml`). The dependency range `django>=4.2.0` is broader than those explicit compatibility targets.
- `noxfile.py` configures Python 3.12–3.15 × Django 4.2/5.2/6.0, skipping Django 4.2 on Python 3.14/3.15. Configured sessions do not prove every lane passed; this mapping inspects source without running environments.
- Developer setup defaults to Python 3.12 (`taskfile.yaml`); Render demo selects Python 3.13 (`render.yaml`).
- Node >=20 is development-only (`package.json`); JavaScript CI selects Node 22 (`.github/workflows/js.yml`). Node is not needed to serve the Python package.

**Package Manager:**
- uv creates environments and installs/builds Python packages (`taskfile.yaml`); nox uses the uv backend (`noxfile.py`). No uv version pin is declared there.
- No root Python lockfile detected. Library dependencies use ranges in `pyproject.toml`; CI tooling and docs use hash-pinned `.github/requirements/ci.txt` and `docs/requirements.txt`.
- npm has committed `package-lock.json`; CI installs it with `npm ci --ignore-scripts` (`.github/workflows/js.yml`).

## Frameworks

**Core:**
- Django >=4.2.0: generic class-based views, ORM, auth, forms, templates, sessions, system checks and commands (`pyproject.toml`, `src/crud_views/lib/views/`).
- Pydantic >=2.2.1: ViewSet/configuration models (`src/crud_views/lib/viewset/__init__.py`, `src/crud_views/lib/settings.py`).
- Bootstrap 5 theme templates ship under `src/crud_views/templates/`; the example host supplies Bootstrap 5.3.3 in `examples/bootstrap5/project/templates/project/base.html`.
- Browser adapters are shipped in `src/crud_views/static/crud_views/js/adapters.js`; UI framework assets belong to the host. Formset enhancement requires host-supplied jQuery (`src/crud_views/static/crud_views/js/formset.js`).

**Testing:**
- pytest, pytest-django, pytest-cov, pytest-xdist, pytest-mock, pytest-random-order, nox: test extras in `pyproject.toml`; Django setup in `tests/test1/conftest.py`.
- Vitest ^5.1.0, jsdom ^31.0.0, jQuery ~3.7.1: `package.json`; unit and separate integration configurations in `vitest.config.js` and `vitest.integration.config.js`. jsdom is not real-browser verification.
- lxml, cssselect, polib and django-pipeline support markup, translation, and integration assertions (`pyproject.toml`).

**Build/Dev:**
- Hatchling builds the five apps; explicit wheel and sdist allowlists are in `pyproject.toml`, validated by `scripts/check_dist.py`.
- Ruff >=0.17,<0.18: 120-character lines, double quotes, format/lint configuration in `pyproject.toml`. `.pre-commit-config.yaml` pins v0.17.1 and runs both ruff-check and ruff-format.
- bump-my-version synchronizes `pyproject.toml`, `src/crud_views/__init__.py`, `docs/index.md`, and `README.md`.
- Go Task command aliases in `taskfile.yaml`; schema version 3 is declared, a Task binary version is not pinned.
- MkDocs >=1.6.1, awesome-pages >=2.10.1, mkdocs-get-deps >=0.2.0, pymdown-extensions >=10.0 are development extras (`pyproject.toml`); docs use the Read the Docs theme (`mkdocs.yml`).

## Key Dependencies

**Critical:**
- django-tables2 >=2.5.3 and django-filter >=21.1: tables/filter integration (`src/crud_views/lib/table/`, `src/crud_views/lib/views/mixins.py`, `pyproject.toml`).
- django-crispy-forms >=2.0 and crispy-bootstrap5 >=2023.10: form layout/action integration (`src/crud_views/lib/crispy/`, `pyproject.toml`).
- python-box >=6.0.2 and typing-extensions >=4.7.1: runtime support (`pyproject.toml`, `src/crud_views/lib/settings.py`).
- Object detail ships with the base distribution; dependency extras enable workflow, polymorphic, ordered and Guardian integrations (`pyproject.toml`).
- Bulk actions compose existing ORM/form/table dependencies rather than adding a service or runtime package (`src/crud_views/lib/bulk/__init__.py`).
- Public `check_link_access` and `LinkAccess` use the existing Django permission/state machinery and Python's `Enum`; no additional dependency or service is required. Import them directly from `src/crud_views/lib/link_access.py`; there is no convenience export from `src/crud_views/lib/__init__.py` (`docs/reference/link_access.md`).

**Infrastructure:**
- Optional workflow: django-fsm-2 >=4.0.0 and django-fsm-2-admin >=2.0.1 (`pyproject.toml`, `src/crud_views_workflow/lib/`).
- Optional polymorphic: django-polymorphic >=3.1.0 (`pyproject.toml`, `src/crud_views_polymorphic/lib/`).
- Optional ordered: django-ordered-model >=3.4.3 (`pyproject.toml`, `src/crud_views/lib/views/action_ordered.py`).
- Optional guardian: django-guardian >=2.4 (`pyproject.toml`, `src/crud_views_guardian/lib/`). The `all` extra aggregates these four groups.
- django-pipeline is a test extra, not a mandatory runtime dependency; opt-in bundling uses `src/crud_views/lib/pipeline.py`.
- Demo-only Gunicorn >=23, WhiteNoise >=6.9, django-ratelimit >=4.1 (`requirements/demo.txt`); Pygments is an examples extra (`pyproject.toml`).

## Configuration

**Environment:**
- Configure host Django settings; `src/crud_views/lib/settings.py` reads `CRUD_VIEWS_*` attributes into a module-level Pydantic model. No package-specific dotenv loader is used.
- Key controls include `CRUD_VIEWS_EXTENDS`, manage visibility/access tracing, strictness, button/icon values, ancestor permissions, and `CRUD_VIEWS_ASSETS_BUNDLED` (`src/crud_views/lib/settings.py`, `docs/reference/settings.md`). Theme templates override the `crud_views/` namespace; `CRUD_VIEWS_THEME` is ignored and produces warning W110 (`src/crud_views/lib/settings.py`, `docs/reference/theme.md`).
- Direct link checking is opt-in and needs no new setting: pass a target view class, user, own object when required, and a nearest-first list/tuple of known ancestors. `LinkAccess.ALLOWED` is truthy; both denial members are false (`src/crud_views/lib/link_access.py`, `docs/reference/link_access.md`).
- Host apps, auth/messages/request context processors, crispy Bootstrap pack and tables2 template are demonstrated by `examples/bootstrap5/project/settings.py` and `tests/test1/conftest.py`.
- Demo reads `SECRET_KEY` and `RENDER_EXTERNAL_HOSTNAME`; Render selects `DJANGO_SETTINGS_MODULE=project.settings_demo` (`examples/bootstrap5/project/settings_demo.py`, `render.yaml`).
- `dev/.env.example` exists for optional tunnel configuration; its contents are not inspected (`taskfile.yaml`).

**Build:**
- `pyproject.toml`: metadata, dependencies/extras, Hatchling, Ruff, pytest, coverage threshold 88, and version bump configuration.
- `noxfile.py`: installed-distribution verification, recorder-off/on suites, targeted crispy floor sessions, manual Pydantic 2.2.1 report-floor session.
- `mkdocs.yml`, `docs/requirements.txt`, `.readthedocs.yaml`: docs configuration; Read the Docs selects Python 3.12, docs CI selects 3.13 (`.github/workflows/docs.yml`).
- `package.json`, `vitest.config.js`, `vitest.integration.config.js`: development-only JS harness, separate from distribution building.

## Platform Requirements

**Development:**
- Python >=3.12; uv/Task for the task workflow (`pyproject.toml`, `taskfile.yaml`). Node/npm are needed only for JS checks (`package.json`).
- SQLite in-memory databases are configured for Python tests (`tests/test1/conftest.py`); broad test runs use xdist per `CLAUDE.md` and `noxfile.py`.
- GNU gettext tools support translation extraction/compilation tasks (`taskfile.yaml`).
- Prefer bounded, opt-in integrations that the developer can trace and maintain, as required by `CLAUDE.md`.

**Production:**
- Install into a host Django deployment, configure its database/auth/templates, and serve collected static assets (`docs/reference/assets.md`, `examples/bootstrap5/project/settings.py`).
- Public demo uses Render, one Gunicorn worker, WhiteNoise, and ephemeral SQLite; startup migrates/seeds (`render.yaml`, `examples/bootstrap5/project/settings_demo.py`). This demo architecture is not required for consuming applications.
- Package publication uses PyPI trusted publishing; documentation uses Read the Docs (`.github/workflows/publish.yml`, `.readthedocs.yaml`).

---

*Stack analysis: 2026-11-26*
