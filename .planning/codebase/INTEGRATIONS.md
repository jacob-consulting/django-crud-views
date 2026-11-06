---
last_mapped_commit: 6a6fc57d180bee14eefae688b9553e8c31daa861
last_mapped_at: 2026-11-06
---
# External Integrations

**Analysis Date:** 2026-11-06

## APIs & External Services

**Django host application:**
- The package integrates with the importing Django project's app registry, URL configuration, templates, settings, auth, content types, messages, and system checks (`src/crud_views/apps.py`, `src/crud_views/checks.py`, `src/crud_views/lib/viewset/`).
  - SDK/Client: Django APIs; no separate service SDK
  - Auth: host project's configured Django authentication backends and permission system

**Forms, tables, and filters:**
- django-crispy-forms and crispy-bootstrap5 render forms using the Bootstrap 5 template pack (`src/crud_views/lib/crispy/`).
  - SDK/Client: `crispy_forms`, `crispy_bootstrap5`
  - Auth: Host application configuration; no credentials
- django-tables2 and django-filter provide table and filter adapters for list views (`src/crud_views/lib/table/`, `src/crud_views/lib/views/mixins.py`).
  - SDK/Client: `django_tables2`, `django_filters`
  - Auth: None; operate on host Django querysets and requests

**Optional Django extensions:**
- django-fsm-2 and django-fsm-2-admin connect workflow views to host model state transitions and admin integration (`src/crud_views_workflow/`).
  - SDK/Client: `django_fsm`
  - Auth: Django permissions and workflow view configuration
  - Execution: `run_transition(object, name, *, user, comment=None)` is exported lazily from `src/crud_views_workflow/lib/__init__.py`; `src/crud_views_workflow/lib/execution.py` checks transition availability, business validation, comment policy, and saved actor/object identity, then persists the transition and `WorkflowInfo` in one transaction on the object's write database. `WorkflowView` uses the same engine and schedules follow-up work with `transaction.on_commit()` on that alias (`src/crud_views_workflow/lib/views.py`). Direct decorated-method calls bypass these helper checks and history behavior.
- django-polymorphic supports polymorphic model querysets and type-specific create forms (`src/crud_views_polymorphic/`).
  - SDK/Client: `polymorphic`
  - Auth: Django permissions
- django-guardian provides object-level permissions through `GuardianViewSet` (`src/crud_views_guardian/`).
  - SDK/Client: `guardian`
  - Auth: Host project's user model, auth backends, and Guardian permissions
- django-ordered-model enables ordering actions when the host model uses that library; package extra is `[ordered]`.

**Developer-provided resource sources:**
- `Resource` and `ResourceViewMixin` let a ViewSet expose Pydantic rows backed by caller-defined sources such as a filesystem, object store, or API (`src/crud_views/lib/resource.py`, `src/crud_views/lib/viewset/__init__.py`). The package does not include a client SDK, credentials, or source-specific adapter; implementations supply `cv_get_items()` and may override `cv_get_item()`.
- Resource views default to no database transaction (`cv_atomic = False`); the caller can opt into a transaction for ORM writes, while external side effects remain outside database rollback semantics (`src/crud_views/lib/resource.py`).

## Data Storage

**Databases:**
- No database provider is bundled or selected by the reusable package. Views use the host project's Django ORM and configured database.
  - Connection: Host Django `DATABASES` setting
  - Client: Django ORM
- The workflow extension defines a `WorkflowInfo` model and migrations, storing audit/history data in the host database (`src/crud_views_workflow/models.py`, `src/crud_views_workflow/migrations/`).
- Workflow transition writes and history creation use one `transaction.atomic(using=...)` boundary; router-selected history reads and commit callbacks stay pinned to the persisted object's database (`src/crud_views_workflow/lib/execution.py`, `src/crud_views_workflow/lib/views.py`). The public helper requires both object and authenticated actor to be saved on that selected alias.
- The demo uses SQLite configured by the example project (`examples/bootstrap5/project/settings_demo.py`); `render.yaml` documents that its free-plan filesystem is ephemeral and the demo recreates/seeds the database on each start.

**File Storage:**
- Package has no external file-storage integration. Django's host project owns any configured storage backend; the demo uses WhiteNoise to serve collected static assets (`render.yaml`, `requirements/demo.txt`).

**Caching:**
- No package-managed cache or external caching service detected.

## Authentication & Identity

**Auth Provider:**
- Django's configured authentication and permission system; the core permission mixins check standard model permissions (`src/crud_views/lib/view/`).
  - Implementation: host project configures users, backends, middleware, and permissions; `src/crud_views_guardian/` optionally adds django-guardian object permissions.
- The library does not provide login, user identity storage, or external identity-provider clients.

## Monitoring & Observability

**Error Tracking:**
- No error-tracking SDK detected in package dependencies or source.

**Logs:**
- No package-specific logging backend integration detected; runtime logs are managed by the host Django deployment. Demo process is served by Gunicorn (`render.yaml`).

## CI/CD & Deployment

**Hosting:**
- Reusable package is built as a Python wheel with Hatchling (`pyproject.toml`). No mandatory application hosting platform is imposed.
- Public demo is configured for Render in `render.yaml`; build/start use `requirements/demo.txt` and Gunicorn.
- Documentation is configured for Read the Docs via `.readthedocs.yaml` and MkDocs (`mkdocs.yml`).

**CI Pipeline:**
- GitHub Actions workflows under `.github/workflows/` run Python/Django and example matrices, Ruff, MkDocs builds, JS tests, and release publication.
- Release workflow builds the package and publishes to PyPI using the PyPA trusted-publishing action (`.github/workflows/publish.yml`); Codecov receives coverage reports from Python CI.
- The demo deployment workflow uses Render API configuration in `.github/workflows/demo.yml` (deployment credential values are not documented here).

## Environment Configuration

**Required env vars:**
- The library itself defines no required environment variables. Host project settings control database and authentication configuration.
- The Render demo declares `DJANGO_SETTINGS_MODULE`, generated `SECRET_KEY`, and platform-provided `PORT` in `render.yaml`; deployment configuration also supplies its demo URL to the workflow.

**Secrets location:**
- Package users supply secrets through their Django host's configuration/secrets mechanism.
- Deployment credentials are configured in CI/platform secret stores; secret files and values are not inspected or recorded.

## Webhooks & Callbacks

**Incoming:**
- No external webhook endpoints are provided by the library. Django URL patterns generated by ViewSets are in-process CRUD routes (`src/crud_views/lib/viewset/`).

**Outgoing:**
- No package-initiated webhooks or external API callbacks detected.

---

*Integration audit: 2026-11-06*
