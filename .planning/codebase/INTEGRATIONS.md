---
last_mapped_commit: 38b0100683fa71412b8bc00dd0eeb7f985efb459
last_mapped_at: 2026-10-25
---
# External Integrations

**Analysis Date:** 2026-10-25

This repository is a reusable Django library. The package code (`src/`) makes no network calls at request time and talks to no external SaaS. Integrations fall into three groups: (1) Django ecosystem libraries the package plugs into, (2) one opt-in download helper for vendoring static assets, (3) CI/CD, hosting and quality services around the repo.

## APIs & External Services

**Django ecosystem integrations (in-process libraries):**

- django-tables2 — list rendering; `Table` base in `src/crud_views/lib/table/table.py`, columns in `src/crud_views/lib/table/columns.py`, template `crud_views/table/bootstrap5.html`.
  - SDK/Client: `django-tables2`
  - Auth: Not applicable
- django-filter — filter forms on list views (`ListViewTableFilterMixin` in `src/crud_views/lib/views/mixins.py`; session-persisted filters, keyed by `CRUD_VIEWS_SESSION_DATA_KEY`).
- django-crispy-forms + crispy-bootstrap5 — `CrispyViewMixin`, `CrispyModelForm`, `CrispyDeleteForm` in `src/crud_views/lib/crispy/`.
- django-fsm-2 — state transitions rendered as form actions in `src/crud_views_workflow/lib/`.
- django-polymorphic — content-type picker and per-type forms in `src/crud_views_polymorphic/lib/create_select.py`, `src/crud_views_polymorphic/lib/utils.py`.
- django-ordered-model — up/down actions in `src/crud_views/lib/ordered.py`, `src/crud_views/lib/views/action_ordered.py`.
- django-guardian — per-object permissions in `src/crud_views_guardian/lib/viewset.py`, `src/crud_views_guardian/lib/views.py`, `src/crud_views_guardian/lib/mixins.py`.
- django-pipeline (optional, never imported) — `src/crud_views/lib/pipeline.py` produces `source_filenames` values (`cv_sources()` / `LazySources`) and reads `settings.PIPELINE` as plain data; `CRUD_VIEWS_ASSETS_BUNDLED=True` makes `{% cv_js %}`/`{% cv_css %}` emit only external entries (`tag_entries()` in `src/crud_views/lib/assets.py`).
- django-csp / Django 6 CSP middleware (optional) — nonce auto-detection in `_resolve_nonce()` in `src/crud_views/templatetags/crud_views.py` (request attribute named by `CRUD_VIEWS_CSP_NONCE_ATTR`, then `django.middleware.csp.get_nonce`, then `csp_nonce` context var).

**Non-ORM data sources (extension point, no bundled client):**

- `Resource` / `ResourceViewMixin` in `src/crud_views/lib/resource.py` let ViewSets serve rows from any backend (S3, HTTP APIs). Host code implements `cv_get_items(cls, request, **url_kwargs)`. The only shipped example is a fake in-memory S3 bucket in `examples/bootstrap5/resources/views.py` (no boto3/AWS dependency).

**Asset vendoring (outbound HTTP, opt-in, management-command time only):**

- `vendor()` in `src/crud_views/lib/vendor.py` downloads third-party JS/CSS via `urllib.request.urlopen` from a `VendorSpec.base_url` template into a project `STATICFILES_DIRS` directory and writes a `.vendored` stamp. `check_vendored()` raises `crud_views.W330`/`W331` on missing/drifted files. No integrity verification on download.
- Asset registry (`register_assets()` in `src/crud_views/lib/assets.py`) accepts external CDN URLs with SRI metadata (`Asset(path, integrity, crossorigin)`); checks E330/W332 cover SRI.
- Management command: `src/crud_views/management/commands/cv_assets.py`.

**Front-end CDNs (example project only, `examples/bootstrap5/project/templates/project/base.html`):**

- jsDelivr — Bootstrap 5.3.3 CSS + JS bundle
- cdnjs (Cloudflare) — Font Awesome 6.7.2
- code.jquery.com — jQuery 3.7.1

## Data Storage

**Databases:**

- Package: whatever the host Django project configures; uses the Django ORM only. `Resource` respects `DEFAULT_DB_ALIAS` (`src/crud_views/lib/resource.py`).
- Package migrations: `src/crud_views/migrations/` (and per-extension `migrations/` dirs; excluded from Codecov and Sonar).
- Tests: SQLite in-memory (`"NAME": ":memory:"` in `tests/test1/conftest.py`).
- Example/demo: SQLite file `examples/bootstrap5/db.sqlite3` (`examples/bootstrap5/project/settings.py`); demo re-migrates and re-seeds on every start (`render.yaml`).
  - Connection: Django `DATABASES` setting (no env var)
  - Client: Django ORM

**File Storage:**

- Local filesystem only. Demo uses `FileSystemStorage` + `whitenoise.storage.CompressedManifestStaticFilesStorage` (`examples/bootstrap5/project/settings_demo.py`).

**Caching:**

- None in the package. Demo uses `LocMemCache` for rate-limit counters (`examples/bootstrap5/project/settings_demo.py`).

**Session:**

- Django sessions store per-ViewSet UI state (filters etc.) under `CRUD_VIEWS_SESSION_DATA_KEY` (default `"viewset"`) — `src/crud_views/lib/session.py`.

## Authentication & Identity

**Auth Provider:**

- Django built-in auth (`django.contrib.auth`) — no external identity provider.
  - Implementation: model permissions mapped per view key (list/detail→view, create→add, update→change, delete→delete) via `CrudViewPermissionRequiredMixin` (`src/crud_views/lib/view/`); optional per-object permissions via `guardian.backends.ObjectPermissionBackend` (configured in `AUTHENTICATION_BACKENDS` in `tests/test1/conftest.py` and `examples/bootstrap5/project/settings.py`).
  - Manage views gated by group `CRUD_VIEWS_MANAGE_GROUP` (default `CRUD_VIEWS_MANAGE`) and `CRUD_VIEWS_MANAGE_VIEWS_ENABLED`.

## Monitoring & Observability

**Error Tracking:**

- None (no Sentry or similar).

**Logs:**

- stdlib `logging` with module loggers (`logging.getLogger(__name__)`) in `src/crud_views/lib/exceptions.py`, `src/crud_views/lib/views/delete.py`, `src/crud_views/lib/view/button_data.py`, `src/crud_views_guardian/lib/mixins.py`. No `LOGGING` config shipped; host project decides.
- Configuration problems surface as Django system checks (`src/crud_views/checks.py`, IDs like `crud_views.E100`, `viewset.W280`).

**Code quality / coverage services:**

- Codecov — XML coverage per Python×Django session uploaded by `codecov/codecov-action` (SHA-pinned) in `.github/workflows/tests.yml` and `publish.yml`; config `codecov.yml` (advisory, `after_n_builds: 4`, ignores migrations).
- SonarQube Cloud — automatic analysis via GitHub app; `.sonarcloud.properties` (Python 3.12–3.14, excludes migrations).

## CI/CD & Deployment

**Hosting:**

- PyPI — package releases via `pypa/gh-action-pypi-publish` (trusted publishing, GitHub environment `pypi`) in `.github/workflows/publish.yml`.
- Read the Docs — documentation (`.readthedocs.yaml`, `mkdocs.yml`, `https://django-crud-views.readthedocs.io/`).
- Render — public demo web service `django-crud-views-demo` (`render.yaml`, `autoDeploy: false`), deployed via Render REST API (`https://api.render.com/v1`) from `.github/workflows/demo.yml`.

**CI Pipeline (GitHub Actions, `.github/workflows/`):**

- `tests.yml` — push/PR to main: nox tests + examples across Python 3.12–3.15 × Django 4.2/5.2/6.0, Codecov upload.
- `lint.yml` — `ruff format --check .` + `ruff check .`.
- `docs.yml` — `mkdocs build --strict` on PRs and tags.
- `js.yml` — Node 22, `npm ci --ignore-scripts`, `npm test` (Vitest).
- `readme-examples.yml` — runs README "tool-free" setup on ubuntu/macos/windows; polls with `scripts/wait_for_server.py`.
- `publish.yml` — on `v*` tags: tests + docs + lint, then build and publish to PyPI.
- `demo.yml` — on `v*` tags deploys the tag commit to Render; daily cron (03:00 UTC) restarts the service to wipe data; smoke test checks `/login/` = 200 and `/admin/` = 404.
- Dependabot (`.github/dependabot.yml`) — weekly updates with 7-day cooldown for GitHub Actions, pip locks (`/docs`, `/.github/requirements`), npm (jQuery major bumps ignored).

## Environment Configuration

**Required env vars:**

- Package: none.
- Demo (`examples/bootstrap5/project/settings_demo.py`, `render.yaml`): `SECRET_KEY` (generated by Render), `DJANGO_SETTINGS_MODULE=project.settings_demo`, `PYTHON_VERSION=3.13`, `RENDER_EXTERNAL_HOSTNAME` (set by Render; drives `ALLOWED_HOSTS` / `CSRF_TRUSTED_ORIGINS`), `PORT` (gunicorn bind).
- CI secrets/vars: `CODECOV_TOKEN`, `RENDER_API_KEY`, `RENDER_SERVICE_ID` (secrets), `DEMO_URL` (repository variable).

**Secrets location:**

- GitHub Actions secrets and the `pypi` environment; Render dashboard env vars. `.env` file present at repo root (local environment configuration; contents not inspected, not referenced by package code). The example `examples/bootstrap5/project/settings.py` uses a hard-coded `django-insecure-...` key for local runs only.

## Webhooks & Callbacks

**Incoming:**

- None. (Demo exposes only app pages; `/admin/` is intentionally unmounted in `project.urls_demo`.)

**Outgoing:**

- Render API calls from `.github/workflows/demo.yml`: `POST /services/{id}/deploys`, `GET /services/{id}/deploys[/{deploy_id}]`, `POST /services/{id}/restart`.
- Demo middleware adds response header `X-Demo-Boot` (`examples/bootstrap5/project/boot.py`) used by the reset job to detect a new instance.
- Demo write rate limiting via django-ratelimit keyed on `True-Client-IP` (Cloudflare/Render) in `examples/bootstrap5/project/ratelimit.py` (`DEMO_WRITE_RATES = ("30/m", "300/d")`).

---

*Integration audit: 2026-10-25*
