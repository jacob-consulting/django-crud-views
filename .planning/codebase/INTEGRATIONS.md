---
last_mapped_commit: 7d9b74dc51306d98ce007cd001f416463982c456
last_mapped_at: 2026-11-26
---
# External Integrations

**Analysis Date:** 2026-11-26

## APIs & External Services

**Django ecosystem:**
- No mandatory third-party business API client is declared by `pyproject.toml`; application integration uses host Django ORM/views/auth/templates.
- django-tables2/django-filter and crispy forms/Bootstrap integrate lists and forms (`src/crud_views/lib/table/`, `src/crud_views/lib/views/mixins.py`, `src/crud_views/lib/crispy/`).
- Optional django-fsm-2 workflow transitions/history (`src/crud_views_workflow/lib/`, `src/crud_views_workflow/models.py`), django-polymorphic create flows (`src/crud_views_polymorphic/lib/`), and django-ordered-model actions (`src/crud_views/lib/views/action_ordered.py`) use local Django integrations, without external API credentials.
- Optional django-guardian adapts object permissions (`src/crud_views_guardian/lib/`); its grant tables are host database tables, not a remote identity service.
- `Resource` lets hosts supply non-ORM data; backing API/object-storage clients remain host-owned (`src/crud_views/lib/resource.py`).

**Browser/static integration:**
- Example host loads Bootstrap 5.3.3 from jsDelivr, Font Awesome 6.7.2 from cdnjs, and jQuery 3.7.1 from code.jquery.com (`examples/bootstrap5/project/templates/project/base.html`). These browser requests do not require API credentials.
- `src/crud_views/lib/assets.py` supports local paths and external URL entries; `src/crud_views/lib/pipeline.py` supplies lazy local sources to optional django-pipeline. Bundled mode continues emitting external URLs separately.
- Optional `vendor(spec)` uses standard-library `urllib.request` to download explicit asset files into a host project static directory and writes a version stamp (`src/crud_views/lib/vendor.py`). Normal rendering does not automatically invoke downloads.
- Browser modal/filter fetches target host application endpoints (`src/crud_views/static/crud_views/js/modal.js`, `src/crud_views/static/crud_views/js/list.filter.js`).
- UI libraries/adapters belong to the host; formsets require jQuery, while bulk selection enhancement uses native APIs (`src/crud_views/static/crud_views/js/adapters.js`, `src/crud_views/static/crud_views/js/formset.js`, `src/crud_views/static/crud_views/js/bulk.js`).
- Documentation loads Mermaid 11.4.1 from jsDelivr (`mkdocs.yml`).

**Deployment API:**
- Render REST API deploy/restart calls are implemented with shell curl/jq (`.github/workflows/demo.yml`).
  - SDK/Client: curl to Render v1 endpoints.
  - Auth: GitHub secrets `RENDER_API_KEY` and `RENDER_SERVICE_ID`; repository variable `DEMO_URL` supplies the smoke-test origin. No secret values are recorded.

## Data Storage

**Databases:**
- Host Django `DATABASES` supplies ordinary ORM connections; the library declares no database driver requirement (`pyproject.toml`, `src/crud_views/lib/viewset/__init__.py`).
- Concrete example storage is SQLite at `examples/bootstrap5/db.sqlite3` (`examples/bootstrap5/project/settings.py`).
- Render uses ephemeral filesystem storage and recreates/seeds the demo database on startup (`render.yaml`).
- Tests configure `default` and `shard` SQLite in-memory databases (`tests/test1/conftest.py`); this does not establish production backend compatibility.
- WorkflowInfo persists user FK, JSON data, content type and generic object reference (`src/crud_views_workflow/models.py`); migrations are in `src/crud_views_workflow/migrations/`.
- Guardian adapters resolve generic/direct user and group grant models (`src/crud_views_guardian/lib/ancestors.py`).

**File Storage:**
- No cloud storage SDK is declared by `pyproject.toml`; upload storage belongs to the host Django configuration.
- Demo uses filesystem storage and WhiteNoise compressed-manifest static serving (`examples/bootstrap5/project/settings_demo.py`).
- Optional asset vendoring writes to host project directories, not installed package static directories (`src/crud_views/lib/vendor.py`).

**Caching:**
- Demo uses Django LocMemCache for rate limiting (`examples/bootstrap5/project/settings_demo.py`); no Redis/Memcached service is configured there.
- Guardian's private accessor retains ObjectPermissionChecker as `_cv_guardian_checker` on the supplied user (`src/crud_views_guardian/lib/permissions.py`). This is in-process grant reuse, not an external cache. Fresh normal request users obtain fresh checkers.
- View/session data and filters use host Django sessions (`src/crud_views/lib/session.py`, `src/crud_views/lib/views/mixins.py`).

## Authentication & Identity

**Auth Provider:**
- Django users/groups/model permissions and host sessions are the core integration (`src/crud_views/lib/views/mixins.py`); no OAuth/OIDC identity SDK is declared by `pyproject.toml`.
- Example host enables ModelBackend and Guardian ObjectPermissionBackend, with `ANONYMOUS_USER_NAME=None` (`examples/bootstrap5/project/settings.py`).
- Guardian endpoint views use strict object checks by default; accepting global model permissions is an explicit view-class option, `cv_guardian_accept_global_perms` (`src/crud_views_guardian/lib/mixins.py`). GuardianViewSet rejects that removed constructor/class setting (`src/crud_views_guardian/lib/viewset.py`).
- Shared nested authorization composes explicit ancestor policies with core/Guardian providers (`src/crud_views/lib/ancestors.py`, `src/crud_views/lib/ancestor_policy.py`, `src/crud_views_guardian/lib/ancestors.py`).
- For custom Python link presentation, import `check_link_access` and `LinkAccess` from `src/crud_views/lib/link_access.py`. The checker validates caller inputs, then evaluates selected parent gates, own permission, and state; only `LinkAccess.ALLOWED` is truthy. It adds no identity provider, middleware, request, or rendering-view dependency (`docs/reference/link_access.md`).
- Supply already-known objects; the public checker does not load objects/ancestors, prove child membership, or authorize requests. Missing immediate parents deny nested links; unknown higher levels remain unchecked. Reached backend/hooks can still query or raise, so callers must preserve ordinary request authorization (`src/crud_views/lib/link_access.py`, `docs/reference/link_access.md`).
- Reached nested authorization gates support the `default` database only, with provider-specific actor/auth-table/object checks. This is not a blanket validation of all supplied objects; top-level checks and unreached gates retain their existing behavior (`src/crud_views/lib/ancestor_db.py`, `docs/reference/link_access.md`).
- Public demo enables secure cookies/proxy configuration, disables manage access-trace forms, and uses a restricted URLconf (`examples/bootstrap5/project/settings_demo.py`, `examples/bootstrap5/project/urls_demo.py`).

## Monitoring & Observability

**Error Tracking:**
- No external runtime error-tracking SDK detected in `pyproject.toml`.
- Django startup checks report configuration issues (`src/crud_views/checks.py` and extension `checks.py` modules).
- Manage access-trace/report export is local diagnostic functionality, not hosted telemetry (`src/crud_views/lib/access_trace_runner.py`, `src/crud_views/lib/access_trace_export.py`, `src/crud_views/lib/views/manage.py`).

**Logs:**
- Standard Python module loggers; host Django controls output destinations (`src/crud_views/lib/exceptions.py`, `src/crud_views/lib/view/label_mode.py`, `src/crud_views/lib/views/delete.py`, `src/crud_views/templatetags/crud_views.py`).
- CI uploads per-session coverage XML to Codecov using `CODECOV_TOKEN` (`.github/workflows/tests.yml`, `.github/workflows/publish.yml`, `codecov.yml`).

## CI/CD & Deployment

**Hosting:**
- PyPI trusted publishing via GitHub OIDC, with `id-token: write` and GitHub environment `pypi` (`.github/workflows/publish.yml`).
- Read the Docs configuration builds MkDocs documentation (`.readthedocs.yaml`, `mkdocs.yml`).
- Render demo uses Python 3.13, one Gunicorn worker, WhiteNoise, ephemeral SQLite and health path `/login/` (`render.yaml`).
- Demo push auto-deploy is disabled; tag workflow calls the API for the exact commit and schedules daily restart/reset at 03:00 UTC (`.github/workflows/demo.yml`).
- Optional developer tunnel runs Docker Compose from `dev/` through the `cf` task; `dev/.env.example` exists and is not inspected (`taskfile.yaml`).

**CI Pipeline:**
- Python/Django and example matrix configuration lives in `.github/workflows/tests.yml` and `noxfile.py`. Django 4.2/Python 3.14+ combinations are skipped. Configured lanes are not evidence that every lane passed at the mapped commit.
- Nox tests verify installed distribution origin and run recorder-off/on suites; targeted crispy-floor and manual Pydantic-floor sessions are separately defined (`noxfile.py`).
- JS CI uses Node 22, npm lock installation, and the unit Vitest configuration; the separate `test:integration` script is not invoked there (`.github/workflows/js.yml`, `package.json`). jsdom does not certify real browsers.
- Ruff and distribution allowlist checks run in `.github/workflows/lint.yml`; strict docs builds run in `.github/workflows/docs.yml`.
- README example startup runs on Linux/macOS/Windows using Python 3.13 (`.github/workflows/readme-examples.yml`).
- Tag publishing requires test/docs/lint jobs (`.github/workflows/publish.yml`); package deployment differs from host application deployment.

## Environment Configuration

**Required env vars:**
- Core package requires no dedicated environment variable; configure optional `CRUD_VIEWS_*` attributes on host Django settings (`src/crud_views/lib/settings.py`).
- Demo requires `SECRET_KEY`; `RENDER_EXTERNAL_HOSTNAME` configures allowed hosts/CSRF origins (`examples/bootstrap5/project/settings_demo.py`). Render also sets `DJANGO_SETTINGS_MODULE`, `PYTHON_VERSION`, and runtime `PORT` (`render.yaml`).
- CI/deploy secret references: `CODECOV_TOKEN`, `RENDER_API_KEY`, `RENDER_SERVICE_ID`; `DEMO_URL` is a repository variable (`.github/workflows/tests.yml`, `.github/workflows/demo.yml`).
- Test-only controls: `CV_ACCESS_RECORD_REQUESTS` selects off/on runs; manual report-floor export requires `CV_MANAGE_SCHEMA_EXPORT_DIR` (`noxfile.py`).

**Secrets location:**
- Host-managed Django configuration; Render generates the demo secret (`render.yaml`, `examples/bootstrap5/project/settings_demo.py`).
- GitHub encrypted secrets are referenced by workflows (`.github/workflows/demo.yml`, `.github/workflows/tests.yml`); no values are inspected or documented.
- Local tunnel environment file is expected by `taskfile.yaml`; tracked `dev/.env.example` existence is noted only.

## Webhooks & Callbacks

**Incoming:**
- No package webhook receiver detected under `src/`; host mounts generated Django ViewSet routes (`src/crud_views/lib/viewset/__init__.py`).
- Demo `/login/` health/smoke path is not a webhook (`render.yaml`, `.github/workflows/demo.yml`).

**Outgoing:**
- No mandatory runtime webhook sender detected under `src/`.
- Optional explicit asset downloads use `src/crud_views/lib/vendor.py`; UI fetches target host endpoints (`src/crud_views/static/crud_views/js/modal.js`, `src/crud_views/static/crud_views/js/list.filter.js`).
- CI calls Render and uploads coverage to Codecov (`.github/workflows/demo.yml`, `.github/workflows/tests.yml`).

---

*Integration audit: 2026-11-26*
