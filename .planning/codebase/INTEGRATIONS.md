---
last_mapped_at: 2026-11-10
last_mapped_commit: 83fb88014f76f3c500964a822b06e3ff8c5f4c7b
---
# External Integrations

**Analysis Date:** 2026-11-10

## APIs & External Services

**Django host application:**
- Uses Django's app registry, URL routing, templates, settings, ORM, auth/permissions, content types, messages, and system checks (`src/crud_views/apps.py`, `src/crud_views/lib/viewset/`, `src/crud_views/checks.py`).
  - SDK/Client: Django APIs
  - Auth: Host project configures identity, middleware, and permissions

**Forms, tables, and filtering:**
- django-crispy-forms with crispy-bootstrap5 renders forms; django-tables2 and django-filter provide list table/filter integration (`src/crud_views/lib/crispy/`, `src/crud_views/lib/table/`, `src/crud_views/lib/views/mixins.py`).
  - SDK/Client: `crispy_forms`, `crispy_bootstrap5`, `django_tables2`, `django_filters`
  - Auth: None; these use host Django configuration

**Optional Django extensions:**
- django-fsm-2 and django-fsm-2-admin power workflow transitions and admin integration (`src/crud_views_workflow/`). `run_transition()` validates actor/object/transition state and writes workflow history atomically on the chosen DB alias (`src/crud_views_workflow/lib/execution.py`); direct FSM method calls bypass this helper behavior.
- django-polymorphic supports polymorphic querysets and type-specific creation (`src/crud_views_polymorphic/`).
- django-guardian adds per-object permission checks and requires host auth backends/configuration (`src/crud_views_guardian/`).
- django-ordered-model supports ordering actions for host models that opt into it (`pyproject.toml`).

**Icons and frontend assets:**
- `Icon` in `src/crud_views/lib/icons.py` is a namespace of plain Python values: `Icon.VIEWSET_DEFAULT` is `None`, and `Icon.NONE` is `""`. The package adds no icon SDK or runtime dependency for these constants.
- Built-in icon values resolve through the semantic icon table and `far`, `fas`, and `bi` library configurations; the host template must load matching icon-font CSS for those classes to display (`src/crud_views/lib/icons.py`, `docs/reference/icons.md`). Projects and theme apps can register mappings/renderers with `register_icons()` and `register_icon_library()`.
- Core static assets are emitted through Django static URLs. Optional django-pipeline integration exposes lazy `cv_sources()` values; setting `CRUD_VIEWS_ASSETS_BUNDLED` makes package tags emit external entries while the host bundler delivers local files (`src/crud_views/lib/assets.py`, `src/crud_views/lib/pipeline.py`, `docs/reference/assets.md`). The package does not install or import django-pipeline at runtime.
- Registered assets may use external CDN URLs and can carry SRI and CSP nonce attributes (`src/crud_views/lib/assets.py`). The host project owns Bootstrap/icon CSS delivery and CSP policy.

**Caller-provided resource sources:**
- `Resource` and `ResourceViewMixin` let applications supply non-ORM data via `cv_get_items()` and optionally `cv_get_item()`; there is no provider SDK or built-in API/filesystem adapter (`src/crud_views/lib/resource.py`).
- Resource views default to `cv_atomic = False`; opting into a database transaction cannot roll back external API or storage writes (`src/crud_views/lib/resource.py`).

## Data Storage

**Databases:**
- Provider is selected by the Django host through `DATABASES`; package ORM operations use Django connections.
- Workflow audit history is stored in the host database and transition/history writes share a transaction (`src/crud_views_workflow/models.py`, `src/crud_views_workflow/lib/execution.py`).
- Example demo uses SQLite (`examples/bootstrap5/project/settings_demo.py`, `render.yaml`).

**File Storage:**
- No package-managed file-storage service; Django host owns storage backends. Demo static files are collected and served by WhiteNoise (`render.yaml`, `requirements/demo.txt`).

**Caching:**
- No external cache or package-managed caching service detected.

## Authentication & Identity

**Auth Provider:**
- Django's configured authentication and permission system (`src/crud_views/lib/view/`). Host project owns users, auth middleware, and permission grants.
- Optional `src/crud_views_guardian/` integrates django-guardian object permissions and its configured authentication backend.
- No login implementation or external identity-provider client is included.

## Monitoring & Observability

**Error Tracking:**
- No error-tracking SDK detected in package dependencies or source.

**Logs:**
- No package-specific logging backend; host Django deployment manages logs. Demo process runs under Gunicorn (`render.yaml`).

## CI/CD & Deployment

**Hosting:**
- The package is built as a Python wheel/sdist using Hatchling; hosting is not prescribed (`pyproject.toml`).
- Public example is hosted on Render with Gunicorn and WhiteNoise (`render.yaml`, `requirements/demo.txt`).
- Documentation is built with MkDocs on Read the Docs (`mkdocs.yml`, `.readthedocs.yaml`).

**CI Pipeline:**
- GitHub Actions cover Python/Django tests, lint, docs, JavaScript, release publication, demo deployment, and README examples (`.github/workflows/`).
- Release workflow uses PyPI trusted publishing; test coverage uploads to Codecov (`.github/workflows/publish.yml`, `.github/workflows/tests.yml`).
- Demo workflow deploys release tags to Render through the Render API; credentials are configured in GitHub/Render settings (`.github/workflows/demo.yml`).
- Local tunnel tooling uses Cloudflare Tunnel through Docker Compose; `.env` file presence is noted without reading contents (`dev/docker-compose.yaml`, `dev/.env`).

## Environment Configuration

**Required env vars:**
- None for the reusable library. Host Django settings provide project-specific database and secret configuration; Render generates the demo secret in its service config (`render.yaml`).

**Secrets location:**
- Host/deployment environment or local env files; `.env` contents are not inspected.

## Webhooks & Callbacks

**Incoming:**
- None provided by the package; host applications define request endpoints.

**Outgoing:**
- No package-managed webhook delivery. Workflow views register follow-up work with Django `transaction.on_commit()` (`src/crud_views_workflow/lib/views.py`).

---

*Integration audit: 2026-11-10*
