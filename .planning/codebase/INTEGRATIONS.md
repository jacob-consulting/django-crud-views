---
last_mapped_commit: 782d6f34fc2adf2509ab8a8a150e69266a3e7e2a
last_mapped_at: 2026-11-19
---
# External Integrations

**Analysis Date:** 2026-11-19

The package itself makes no outbound network calls. It integrates with Django ecosystem packages and leaves application services, database configuration, and resource backends to the host project.

## APIs & External Services

**Django ecosystem:**
- django-tables2 and django-filter - list tables and filtering (`src/crud_views/lib/table/`)
- django-crispy-forms and crispy-bootstrap5 - form rendering and Bootstrap layout integration (`src/crud_views/lib/crispy/`)
- django-fsm-2 and django-fsm-2-admin - workflow transitions and admin integration (`src/crud_views_workflow/`)
- django-polymorphic - model-aware create flow (`src/crud_views_polymorphic/`)
- django-guardian - per-object permissions (`src/crud_views_guardian/`)
- django-ordered-model - ordered up/down actions (`src/crud_views/lib/views/action_ordered.py`)
- django-pipeline - optional asset bundling through `cv_sources`; exercised by tests (`src/crud_views/lib/assets.py`)

**Host application extension points:**
- `Resource` lets a host supply non-ORM data (including API or object-store-backed data); the package bundles no S3, HTTP, or cloud SDK (`src/crud_views/lib/resource.py`)
- Bootstrap 5 theme templates, a configurable semantic icon registry, and shared ViewSet navbar rendering are package-side UI integration points (`src/crud_views/templates/crud_views/`, `src/crud_views/lib/icons.py`, `src/crud_views/lib/navbar.py`)
- Navbar declarations are configured on ViewSets and rendered through `cv_navbar`, `cv_navbar_identity`, and `cv_navbar_items` template tags (`src/crud_views/lib/navbar.py`, `src/crud_views/templatetags/crud_views.py`, `src/crud_views/templates/crud_views/tags/navbar.html`)

## Data Storage

**Databases:**
- Uses any database configured by the host Django project; the library provides no database connection configuration
- Example project uses SQLite (`examples/bootstrap5/project/settings.py`); package tests configure in-memory Django test databases (`tests/test1/conftest.py`)
- django-guardian stores object permission grants through its Django models when the optional integration is installed (`src/crud_views_guardian/`)

**File Storage:**
- No package-managed file/object storage. Demo static files are served with whitenoise (`requirements/demo.txt`, `examples/bootstrap5/project/settings_demo.py`)

**Caching:**
- No external cache service configured by the package

## Authentication & Identity

**Auth Provider:**
- Django `django.contrib.auth` users and model permissions are the core permission integration (`src/crud_views/lib/`)
- django-guardian adds optional per-object permission checks (`src/crud_views_guardian/`)
- No third-party identity provider is bundled; authentication setup belongs to the host project

## Monitoring & Observability

**Error Tracking:**
- No runtime error-tracking service integrated

**Logs:**
- Python/Django logging and Django system checks (`src/crud_views/checks.py`)
- Coverage reports are uploaded to Codecov in CI (`.github/workflows/tests.yml`, `codecov.yml`); SonarCloud settings are present (`.sonarcloud.properties`)

## CI/CD & Deployment

**Hosting:**
- PyPI package publishing via GitHub Actions (`.github/workflows/publish.yml`)
- Read the Docs builds the MkDocs documentation (`.readthedocs.yaml`, `mkdocs.yml`)
- Render hosts the example demo; `render.yaml` declares manual workflow-driven deploys and an ephemeral SQLite filesystem
- Optional remote-development tunnel uses the Cloudflare `cloudflared` container (`dev/docker-compose.yaml`, `task cf`)

**CI Pipeline:**
- GitHub Actions workflows cover Python/Django tests, linting, JavaScript tests, docs, package publishing, demo deploys, and README examples (`.github/workflows/`)
- Python test workflow uses nox compatibility sessions and Codecov upload (`.github/workflows/tests.yml`, `noxfile.py`); JavaScript checks use npm/Vitest (`.github/workflows/js.yml`)
- Demo deploy workflow invokes the Render API (`.github/workflows/demo.yml`); package publishing uses PyPI trusted publishing action (`.github/workflows/publish.yml`)

## Environment Configuration

**Required env vars:**
- Runtime library: values are optional Django settings prefixed `CRUD_VIEWS_` (`src/crud_views/lib/settings.py`)
- Demo: `DJANGO_SETTINGS_MODULE` and generated `SECRET_KEY` (`render.yaml`)
- Cloudflare tunnel: `TUNNEL_TOKEN` when starting `task cf` (`dev/docker-compose.yaml`)
- CI/deploy credentials are configured as GitHub Actions secrets for relevant workflows; names are referenced in workflow configuration and values are not documented here

**Secrets location:**
- GitHub Actions secrets for CI and Render deployment
- Local tunnel token in `dev/.env` (file existence only; template: `dev/.env.example`)
- Render generates the demo `SECRET_KEY` from its blueprint (`render.yaml`)

## Webhooks & Callbacks

**Incoming:**
- No package webhook endpoints. The demo exposes the Django application's `/login/` health-check path (`render.yaml`)

**Outgoing:**
- Demo deployment workflow calls Render's API (`.github/workflows/demo.yml`)
- No outbound service callbacks from the library runtime

---

*Integration audit: 2026-11-19*
