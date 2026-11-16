---
last_mapped_commit: a78b63db1f637b6b8b4cf6b4aaa24885a061ae26
last_mapped_at: 2026-11-16
---
# External Integrations

**Analysis Date:** 2026-11-16

## APIs & External Services

**Runtime library integrations:**
- Django framework APIs - generic class-based views, ORM, auth, forms, templates, URL routing, messages, and system checks (`src/crud_views/`)
  - SDK/Client: Django itself (`pyproject.toml`)
  - Auth: supplied by the consuming Django project; core package has no independent credentials
- django-tables2, django-filter, django-crispy-forms / crispy-bootstrap5 - in-process optional UI packages; there are no remote service calls (`pyproject.toml`, `src/crud_views/`)
- Asset vendor helper - explicit management-command downloads through Python `urllib.request`; extension packages configure a versioned `VendorSpec` and destination (`src/crud_views/lib/vendor.py`). This is a build/maintenance operation, not an automatic request on normal page handling.

**Third-party browser assets:**
- Bootstrap 5.3.3, Font Awesome 6.7.2, and jQuery 3.7.1 are referenced from public CDNs by the example site's base template (`examples/bootstrap5/project/templates/project/base.html`)
- Mermaid 11.4.1 is loaded from jsDelivr for documentation rendering (`mkdocs.yml`)
- Core templates can emit configured external asset URLs through `src/crud_views/lib/assets.py`; the helper renders URLs and does not fetch them

**Build, hosting, and project services:**
- Render API - GitHub Actions deploy and restart the public demo via `https://api.render.com/v1` (`.github/workflows/demo.yml`)
  - Client: `curl` in the workflow
  - Auth: GitHub Actions secrets `RENDER_API_KEY`, `RENDER_SERVICE_ID`; public URL uses the `DEMO_URL` repository variable. No secret values are stored in this document.
- Codecov - receives coverage reports from GitHub Actions (`.github/workflows/tests.yml`, `.github/workflows/publish.yml`)
  - Client: pinned `codecov/codecov-action`
  - Auth: GitHub Actions secret `CODECOV_TOKEN`
- PyPI - release publishing through the trusted-publishing GitHub Action (`.github/workflows/publish.yml`)
  - Client: `pypa/gh-action-pypi-publish`
  - Auth: GitHub Actions OIDC (`id-token: write`) and the `pypi` environment
- Read the Docs - hosts built MkDocs documentation; Python/docs configuration is in `.readthedocs.yaml` and `mkdocs.yml`
- GitHub Actions - CI, release, docs, linting, example checks, and demo automation (`.github/workflows/`)

## Data Storage

**Databases:**
- No database engine or connection is selected by the reusable package. CRUD views use the consumer's Django ORM configuration (`src/crud_views/`)
- Tests use two in-memory SQLite aliases (`default` and `shard`) configured by `tests/test1/conftest.py`
- Local example uses SQLite at `examples/bootstrap5/db.sqlite3`; the public Render demo recreates a SQLite database at startup because its filesystem is ephemeral (`examples/bootstrap5/project/settings.py`, `render.yaml`)

**File Storage:**
- The core package does not provide an external file-storage service
- Render example uses local filesystem storage and WhiteNoise compressed manifest static files (`examples/bootstrap5/project/settings_demo.py`)
- The vendor helper writes downloaded assets under an explicitly configured project static directory (`src/crud_views/lib/vendor.py`)

**Caching:**
- Core package does not require a cache service
- Public demo uses Django's process-local `LocMemCache` for rate-limit counters, matching its single Gunicorn worker (`examples/bootstrap5/project/settings_demo.py`)

## Authentication & Identity

**Auth Provider:**
- Django `contrib.auth` is the core integration; projects configure authentication middleware and backends (`src/crud_views/lib/`, `examples/bootstrap5/project/settings.py`)
- Optional per-object authorization uses django-guardian and `guardian.backends.ObjectPermissionBackend` (`src/crud_views_guardian/`, `examples/bootstrap5/project/settings.py`)
- No external identity provider or OAuth/OIDC login integration is detected

## Monitoring & Observability

**Error Tracking:**
- No runtime error-tracking SDK is configured
- Codecov reports test coverage from CI (`.github/workflows/tests.yml`)

**Logs:**
- Runtime logging uses Django/Python logging facilities; no centralized logging service is configured
- The Render demo's scheduled reset/deploy and HTTP smoke checks are implemented in GitHub Actions (`.github/workflows/demo.yml`)

## CI/CD & Deployment

**Hosting:**
- Reusable library is published to PyPI (`.github/workflows/publish.yml`)
- Documentation is built/hosted through Read the Docs (`.readthedocs.yaml`)
- The example/demo site is hosted on Render (`render.yaml`)

**CI Pipeline:**
- GitHub Actions runs Nox Python/Django matrices, examples, JS tests, Ruff, and docs builds; coverage uploads to Codecov (`.github/workflows/`)
- Release tags trigger package build/publish and Render demo deployment (`.github/workflows/publish.yml`, `.github/workflows/demo.yml`)

## Environment Configuration

**Required env vars:**
- Core library: none; settings are supplied by the host Django project (`src/crud_views/lib/settings.py`)
- Render demo: `SECRET_KEY` and Render-provided `RENDER_EXTERNAL_HOSTNAME` (`examples/bootstrap5/project/settings_demo.py`)
- GitHub workflows: `CODECOV_TOKEN`, `RENDER_API_KEY`, `RENDER_SERVICE_ID`, and repository variable `DEMO_URL` as applicable (`.github/workflows/tests.yml`, `.github/workflows/demo.yml`)

**Secrets location:**
- Deployment and CI credentials are referenced by name from GitHub Actions secrets; the Render demo key is generated by the Render Blueprint (`.github/workflows/`, `render.yaml`)
- Local tunnel setup can use `dev/.env`; its contents are intentionally not inspected (`taskfile.yaml`)

## Webhooks & Callbacks

**Incoming:**
- No external webhook endpoint is provided by the reusable package. The example site exposes ordinary Django URLs only (`examples/bootstrap5/project/urls.py`, `examples/bootstrap5/project/urls_demo.py`)

**Outgoing:**
- No runtime webhook delivery is implemented
- CI workflow calls Render's deploy/restart API during release or scheduled demo maintenance (`.github/workflows/demo.yml`)

---

*Integration audit: 2026-11-16*
