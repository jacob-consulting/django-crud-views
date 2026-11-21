---
last_mapped_commit: 9034acda91f5af049a0d38f41c84e6bfd1c823f4
last_mapped_at: 2026-11-21
---
# External Integrations

**Analysis Date:** 2026-11-21

The package makes no outbound network calls during request handling. An explicit asset-vendoring management command may download configured files from a supplied URL using the Python standard library; integrations, database configuration, and resource backends otherwise belong to the host project (`src/crud_views/lib/vendor.py`, `docs/reference/assets.md`).

## APIs & External Services

**Django ecosystem:**
- django-tables2 and django-filter - list tables and filtering (`src/crud_views/lib/table/`)
- django-crispy-forms and crispy-bootstrap5 - form rendering and Bootstrap layout integration (`src/crud_views/lib/crispy/`)
- django-fsm-2 and django-fsm-2-admin - workflow transitions and admin integration (`src/crud_views_workflow/`)
- django-polymorphic - model-aware create flow (`src/crud_views_polymorphic/`)
- django-guardian - per-object permissions (`src/crud_views_guardian/`)
- django-ordered-model - ordered up/down actions (`src/crud_views/lib/views/action_ordered.py`)
- django-pipeline - optional asset bundling through `cv_sources`; exercised by tests (`src/crud_views/lib/assets.py`)
- Bulk actions use existing Django ORM/queryset/transaction APIs, django-tables2, Django messages, and Crispy forms; the implementation requires no external service or additional package dependency (`src/crud_views/lib/bulk/__init__.py`)
- Stock table headers consume django-tables2 bound-column `is_ordered` and `order_by_alias` to render sorting icons and `aria-sort` from effective ordering, covering URL, default, constructor, and prefixed ordering. Non-orderable headers omit generated sorting controls; use the `table.thead` block for alternate semantics and avoid caller-supplied `aria-sort` collisions (`src/crud_views/templates/crud_views/table/bootstrap5.html`, `docs/reference/list_view.md`, `tests/test1/test_table_template.py`)
- Theme native data-API prefix integration is an in-process extension point: `register_data_prefix()` in `src/crud_views/lib/data_prefix.py` validates and stores the prefix, default `bs`; a theme calls it from `AppConfig.ready()` (`docs/reference/theme.md`). Last valid startup registration wins; invalid values raise `ValueError` without changing the prior value. It does not enable runtime theme switching or select a JavaScript adapter.

**Host application extension points:**
- `Resource` lets a host supply non-ORM data (including API or object-store-backed data); the package bundles no S3, HTTP, or cloud SDK (`src/crud_views/lib/resource.py`)
- Bootstrap 5 theme templates, a configurable semantic icon registry, and shared ViewSet navbar rendering are package-side UI integration points (`src/crud_views/templates/crud_views/`, `src/crud_views/lib/icons.py`, `src/crud_views/lib/navbar.py`)
- `cv_data_prefix` and `#cv-config` expose the registered prefix to markup and JavaScript (`src/crud_views/templatetags/crud_views.py`, `src/crud_views/templates/crud_views/tags/cv_config.html`). Prefix-sensitive native attributes are limited to actions-menu toggles, the language selector, vertical object-detail tabs, and accordion groups; object-detail `tabs.js` also discovers prefixed tab triggers only within `data-cv-od-tabs` tablists (`src/crud_views_object_detail/static/crud_views_object_detail/js/tabs.js`). A theme overriding `cv_config.html` must preserve `data-data-prefix` for custom-prefix tab discovery; absent config/attribute falls back to `bs`. Registration does not change host markup, CSS classes, DOM structure, or the tab adapter (`docs/reference/theme.md`, `docs/reference/javascript.md`)
- Navbar declarations are configured on ViewSets and rendered through `cv_navbar`, `cv_navbar_identity`, and `cv_navbar_items` template tags (`src/crud_views/lib/navbar.py`, `src/crud_views/templatetags/crud_views.py`, `src/crud_views/templates/crud_views/tags/navbar.html`)
- Manage pages and formsets use six optional `--cv-*` CSS custom properties, each with Bootstrap-property and literal fallbacks. Themes may map these aliases on every theme root for nested color modes; the package does not declare global token values (`src/crud_views/static/crud_views/css/manage.css`, `src/crud_views/static/crud_views/css/formset.css`, `docs/reference/theme.md`)
- Bulk actions are opt-in per ORM ViewSet: a table/card list declares destination keys and a permission-required bulk form re-resolves submitted keys in the destination queryset/scope before review and execution (`src/crud_views/lib/bulk/__init__.py`)
- `bulk.js` enhances the native bulk form with current-page selection, selected count, and disabled action buttons for empty selections. It initializes once per form at document readiness and refreshes browser-restored selections on `pageshow`; record ownership comes from the native `form` association. It has no third-party dependency, persistence, or requests. Without JavaScript or required enhancement controls, native submission remains available (`src/crud_views/static/crud_views/js/bulk.js`, `docs/reference/javascript.md`, `tests/js/bulk.test.js`)
- The stock breadcrumb template resolves `breadcrumb:list`, `breadcrumb:item`, and `breadcrumb:item-active` through `cv_button_class`. Register theme defaults with `register_button_classes()` during startup; project `CRUD_VIEWS_BUTTON_CLASSES` values override them. Class overrides preserve breadcrumb escaping, links, and current-page semantics (`src/crud_views/lib/button_classes.py`, `src/crud_views/templates/crud_views/tags/breadcrumb.html`, `docs/reference/theme.md`, `tests/test1/test_breadcrumb.py`)

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
- Nox includes a Crispy dependency-floor matrix for Django 4.2 and 6.0, with bulk flow, execution, source, scope, and return tests included (`noxfile.py`, `tests/test1/test_bulk_flow.py`, `tests/test1/test_bulk_execution.py`, `tests/test1/test_bulk_source.py`, `tests/test1/test_bulk_scope.py`, `tests/test1/test_bulk_return.py`)
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

*Integration audit: 2026-11-21*
