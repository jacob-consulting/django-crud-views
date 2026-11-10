---
last_mapped_at: 2026-11-10
last_mapped_commit: c9c1ea19f7dd2a5f8bc90cede38d0051717ef9e7
---
# External Integrations

**Analysis Date:** 2026-11-10

## APIs & External Services

**Django host application:**
- Integrates with Django app registry, URL routing, templates, settings, auth, content types, messages, ORM, and system checks (`src/crud_views/apps.py`, `src/crud_views/checks.py`, `src/crud_views/lib/viewset/`).
  - SDK/Client: Django APIs
  - Auth: Host project's configured authentication and permissions

**Forms, tables, and filters:**
- django-crispy-forms and crispy-bootstrap5 render forms with the Bootstrap 5 pack (`src/crud_views/lib/crispy/`).
  - SDK/Client: `crispy_forms`, `crispy_bootstrap5`
  - Auth: Host Django configuration; no credentials
- django-tables2 and django-filter adapt list views (`src/crud_views/lib/table/`, `src/crud_views/lib/views/mixins.py`).
  - SDK/Client: `django_tables2`, `django_filters`
  - Auth: None

**Optional Django extensions:**
- django-fsm-2 and django-fsm-2-admin provide workflow transitions and admin integration (`src/crud_views_workflow/`).
  - SDK/Client: `django_fsm`
  - Auth: Django permissions and workflow view configuration.
  - `run_transition(object, name, *, user, comment=None)` is lazily exported from `src/crud_views_workflow/lib/__init__.py`; it checks transition availability and business/comment validation, requires the authenticated actor and object to be saved on the selected write alias, then saves state and `WorkflowInfo` history atomically on that alias (`src/crud_views_workflow/lib/execution.py`). `WorkflowView` schedules follow-up work with `transaction.on_commit()` on that alias (`src/crud_views_workflow/lib/views.py`). Direct decorated-method calls bypass these helper checks and history behavior.
- django-polymorphic supports polymorphic querysets and subtype create forms (`src/crud_views_polymorphic/`).
  - SDK/Client: `polymorphic`
  - Auth: Django permissions
- django-guardian provides object-level permissions (`src/crud_views_guardian/`).
  - SDK/Client: `guardian`
  - Auth: Host user model, auth backends, and Guardian permissions
- django-ordered-model enables ordered actions when host models use it (`pyproject.toml`).
- django-pipeline optionally bundles registered assets; with `CRUD_VIEWS_ASSETS_BUNDLED` tags emit only external entries (`src/crud_views/lib/pipeline.py`, `src/crud_views/lib/assets.py`, `src/crud_views/management/commands/cv_assets.py`). CSP nonce attribute via `CRUD_VIEWS_CSP_NONCE_ATTR`; SRI hashes supported on registered assets.

**Caller-provided resource sources:**
- `Resource` and `ResourceViewMixin` expose caller-defined data, including external API or filesystem sources (`src/crud_views/lib/resource.py`). The package supplies no provider SDK or adapter; callers implement `cv_get_items()` and optionally `cv_get_item()`.
- Resource views default to `cv_atomic = False`; callers can opt into a transaction for ORM writes, while external side effects such as API or object-storage writes remain outside database rollback semantics (`src/crud_views/lib/resource.py`).

## Model Metadata and Detail Rendering

- Object-detail choice labels use Django's `get_FIELD_display()` on the terminal scalar model owner, including scalar FK/O2O paths; collections and terminal relation fields retain their normal behavior (`src/crud_views_object_detail/lib/resolvers.py`). Raw `value` remains available to badge/link callbacks and custom templates, while `display_value` supplies the presentation label (`src/crud_views_object_detail/templatetags/crud_views_object_detail.py`). Django escaping and localization remain the rendering boundary.
- Help descriptions use terminal model field metadata with property, view, and project precedence. Lazy help remains unevaluated until rendering; choice labels resolve under the active language (`src/crud_views_object_detail/lib/resolvers.py`, `docs/reference/object_detail_configuration.md`). Object-detail settings are separately cached in `src/crud_views_object_detail/lib/conf.py`; `CRUD_VIEWS_OBJECT_DETAIL_SHOW_HELP_TEXT` defaults to false.

## Data Storage

**Databases:**
- No provider is selected by the reusable package; ORM connections come from host `DATABASES` settings.
  - Connection: Host Django `DATABASES`
  - Client: Django ORM
- Workflow audit history is stored in the host database (`src/crud_views_workflow/models.py`, `src/crud_views_workflow/migrations/`). Transition and history writes share a database transaction (`src/crud_views_workflow/lib/execution.py`).
- Demo uses SQLite (`examples/bootstrap5/project/settings_demo.py`, `render.yaml`).

**File Storage:**
- No package-managed storage integration; host Django owns storage backends. Demo serves collected static assets with WhiteNoise (`requirements/demo.txt`, `render.yaml`).

**Caching:**
- No external caching service or package-managed cache detected.

## Authentication & Identity

**Auth Provider:**
- Django's configured authentication and permission system (`src/crud_views/lib/view/`).
  - Implementation: Host configures identity, middleware, and permissions; optional `src/crud_views_guardian/` adds per-object permissions.
- No login implementation or external identity-provider client is included.

## Monitoring & Observability

**Error Tracking:**
- No error-tracking SDK detected in package dependencies or source.

**Logs:**
- No package-specific logging backend; host Django deployment manages logs. Demo runs under Gunicorn (`render.yaml`).

## CI/CD & Deployment

**Hosting:**
- Package builds as a Python wheel with Hatchling (`pyproject.toml`); no hosting imposed.
- Demo deploys to Render (`render.yaml`) using Gunicorn and WhiteNoise (`requirements/demo.txt`).
- Documentation uses Read the Docs and MkDocs (`.readthedocs.yaml`, `mkdocs.yml`).

**CI Pipeline:**
- GitHub Actions (`tests.yml`, `lint.yml`, `docs.yml`, `js.yml`, `publish.yml`, `demo.yml`, `readme-examples.yml`) run test matrices; actions are SHA-pinned and Dependabot-managed (`.github/dependabot.yml`)
- `demo.yml` deploys release tags to Render via the Render API (secrets `RENDER_API_KEY`, `RENDER_SERVICE_ID`, var `DEMO_URL`) and resets demo data daily by cron
- Local dev: Cloudflare tunnel via `cloudflare/cloudflared` container, token `TUNNEL_TOKEN` in `dev/.env` (`dev/docker-compose.yaml`, `task cf`)
- GitHub Actions under `.github/workflows/` run test matrices, lint, docs, JS checks, and release publication.
- Ruff formats Markdown Python fences as well as Python modules; CI runs `ruff format --check .` and `ruff check .` (`.github/workflows/lint.yml`).
- Release uses PyPI trusted publishing (`.github/workflows/publish.yml`); coverage uploads to Codecov (`.github/workflows/tests.yml`).

## Environment Configuration

**Required env vars:**
- The library defines no required environment variables. Host Django settings supply database and secrets. Demo deployment defines its settings module, secret key, and public demo URL in Render configuration (`render.yaml`).

**Secrets location:**
- Host/deployment environment; `.env` files, if present, are not inspected.

## Webhooks & Callbacks

**Incoming:**
- None provided by the package. Django host applications supply URL endpoints.

**Outgoing:**
- No package-managed webhooks. Django workflow callbacks use `transaction.on_commit()` for post-commit work (`src/crud_views_workflow/lib/views.py`).

---

*Integration audit: 2026-11-10*
