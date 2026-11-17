---
last_mapped_commit: 54c18a1b65f038e5fcdb5dc0038782133f93ffb8
last_mapped_at: 2026-11-17
---
# External Integrations

**Analysis Date:** 2026-11-17

The package is a library; it makes no outbound network calls itself. Integrations are Django ecosystem packages plus dev/CI/deploy services.

## APIs & External Services

**Django ecosystem (library integrations):**
- django-tables2 / django-filter - list tables and filters (`ListViewTableMixin`, `ListViewTableFilterMixin` in `src/crud_views/lib/`)
- django-crispy-forms + crispy-bootstrap5 - form rendering (`src/crud_views/lib/crispy/`)
- django-fsm-2 - workflow transitions (`src/crud_views_workflow/lib/`)
- django-polymorphic - polymorphic create flow (`src/crud_views_polymorphic/lib/`)
- django-guardian - per-object permissions (`src/crud_views_guardian/lib/`)
- django-ordered-model - ordered up/down actions (`src/crud_views/lib/views/action_ordered.py`)
- django-pipeline - asset bundling via `cv_sources` (`src/crud_views/lib/assets.py`; tested only)

**Non-ORM data:**
- `Resource` abstraction lets views show non-ORM data (S3, APIs) supplied by the host project (`src/crud_views/lib/resource.py`); no SDK bundled.

**Front-end:**
- Bootstrap 5 theme and jQuery-based JS; templates in `src/crud_views/templates/`

## Data Storage

**Databases:**
- Any Django-supported DB; library defines no connection. Example project and tests use SQLite (`examples/bootstrap5/project/settings.py`, in-memory via `tests/test1/conftest.py`)

**File Storage:**
- Local filesystem only (static via whitenoise in demo)

**Caching:**
- None

## Authentication & Identity

**Auth Provider:**
- Django `django.contrib.auth` permissions (`CrudViewPermissionRequiredMixin`); optional django-guardian object permissions
- No third-party identity provider

## Monitoring & Observability

**Error Tracking:**
- None

**Logs:**
- Standard Python logging; Django system checks in `src/crud_views/checks.py`
- Coverage reporting to Codecov (`codecov.yml`); SonarCloud config (`.sonarcloud.properties`)

## CI/CD & Deployment

**Hosting:**
- PyPI (package), Read the Docs (docs), Render free web service (demo, `render.yaml`)
- Cloudflare tunnel via `cloudflare/cloudflared` Docker image for remote dev (`dev/docker-compose.yaml`, `task cf`)

**CI Pipeline:**
- GitHub Actions in `.github/workflows/`: `tests.yml` (nox matrix py3.12-3.15 x Django 4.2/5.2/6.0, examples sessions, Codecov upload), `lint.yml`, `js.yml`, `docs.yml`, `publish.yml`, `demo.yml` (Render API deploy), `readme-examples.yml`
- Actions pinned: actions/checkout@v7, actions/setup-python@v7, codecov-action, pypa/gh-action-pypi-publish

## Environment Configuration

**Required env vars:**
- CI secrets: `CODECOV_TOKEN`, `RENDER_API_KEY`, `RENDER_SERVICE_ID`
- Dev: `TUNNEL_TOKEN` (`dev/.env`)
- Demo: `DJANGO_SETTINGS_MODULE`, `SECRET_KEY`, `PYTHON_VERSION`

**Secrets location:**
- GitHub Actions secrets; `dev/.env` (local, untracked); Render generated values

## Webhooks & Callbacks

**Incoming:**
- None (demo health check `/login/` only)

**Outgoing:**
- `demo.yml` calls the Render API to trigger deploys

---

*Integration audit: 2026-11-17*
