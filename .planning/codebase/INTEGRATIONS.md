---
last_mapped_commit: 987dfa68448cfa57d77daedf0504e872423ea4e5
last_mapped_at: 2026-11-24
---
# External Integrations

**Analysis Date:** 2026-11-24

No third-party service client is bundled for server request handling. The reusable `vendor(spec)` helper downloads explicitly configured assets using `urllib.request`; extension apps can wrap it in a management command. Browser filter and modal scripts use `fetch()` against host application endpoints. Integrations, database configuration, and resource backends otherwise belong to the host project (`src/crud_views/lib/vendor.py`, `src/crud_views/static/crud_views/js/list.filter.js`, `src/crud_views/static/crud_views/js/modal.js`, `docs/reference/assets.md`).

## APIs & External Services

**Django ecosystem:**
- The distribution exposes five Django apps: `crud_views` (core), `crud_views_object_detail`, `crud_views_workflow`, `crud_views_polymorphic`, and `crud_views_guardian` (`pyproject.toml`, `src/crud_views*/apps.py`)
- django-tables2 and django-filter - list tables and filtering (`src/crud_views/lib/table/`)
- django-crispy-forms and crispy-bootstrap5 - form rendering and Bootstrap layout integration (`src/crud_views/lib/crispy/`)
- django-fsm-2 and django-fsm-2-admin - workflow transitions and admin integration (`src/crud_views_workflow/`)
- django-polymorphic - model-aware create flow (`src/crud_views_polymorphic/`)
- django-guardian - per-object permissions (`src/crud_views_guardian/`)
- Link visibility checks are an internal Django authorization integration: link rendering uses supplied target objects and known ancestors with the existing model or guardian permission providers, without performing ancestor lookups or changing request authorization (`src/crud_views/lib/link_access.py`, `src/crud_views/lib/ancestor_db.py`)
- django-ordered-model - ordered up/down actions (`src/crud_views/lib/views/action_ordered.py`)
- django-pipeline - optional asset bundling through `cv_sources`; exercised by tests (`src/crud_views/lib/assets.py`)
- Bulk actions use existing Django ORM/queryset/transaction APIs, django-tables2, Django messages, and Crispy forms; the implementation requires no external service or additional package dependency (`src/crud_views/lib/bulk/__init__.py`)
- Stock table headers consume django-tables2 bound-column `is_ordered` and `order_by_alias` to render sorting icons and `aria-sort` from effective ordering, covering URL, default, constructor, and prefixed ordering. Non-orderable headers omit generated sorting controls; use the `table.thead` block for alternate semantics and avoid caller-supplied `aria-sort` collisions (`src/crud_views/templates/crud_views/table/bootstrap5.html`, `docs/reference/list_view.md`, `tests/test1/test_table_template.py`)
- Theme JavaScript integration is an in-process startup extension point. A theme may call `register_data_prefix()`, `register_js_namespace()`, and `register_tooltip_placements()` from `AppConfig.ready()` (`src/crud_views/lib/data_prefix.py`, `src/crud_views/lib/js_config.py`, `docs/reference/theme.md`). Defaults are `bs`, `bootstrap`, and `{}`; each registry is independent, the last valid startup registration wins, and invalid values raise `ValueError` without replacing prior state. These are process-level settings, not request-scoped theme switching.
- `{% cv_config %}` / `{% cv_const_js %}` writes the registered data prefix, JS namespace, and escaped tooltip-placement JSON to `#cv-config` (`src/crud_views/templates/crud_views/tags/cv_config.html`, `src/crud_views/templatetags/crud_views.py`). Preserve those attributes when overriding the config template.
- Core browser scripts use `cv.adapters`; `adapters.js` resolves Bootstrap-compatible components from the registered global namespace (default `bootstrap`) and supplies the default tooltip adapter and the modal lifecycle observers, which listen to `hide.{prefix}.modal` / `hidden.{prefix}.modal` with the registered data prefix from `#cv-config` `data-data-prefix` (fallback `bs`); the missing-component error names no library (PR #405) (`src/crud_views/static/crud_views/js/adapters.js`, `tests/js/adapters.test.js`). The host app supplies the UI library bundle or replaces adapter entries; Bootstrap JavaScript is not a package runtime dependency.
- `tooltip.js` initializes only package-marked `[data-cv-tooltip]` triggers through `cv.adapters.tooltip`, on page readiness and modal/formset insertion. Registered placement defaults are applied only when the trigger has no native `data-{prefix}-placement` attribute; app-owned Bootstrap tooltip triggers are left to the host (`src/crud_views/static/crud_views/js/tooltip.js`, `src/crud_views/static/crud_views/js/adapters.js`, `docs/reference/javascript.md`).

**Host application extension points:**
- `Resource` lets a host supply non-ORM data (including API or object-store-backed data); the package bundles no S3, HTTP, or cloud SDK (`src/crud_views/lib/resource.py`)
- Bootstrap 5 theme templates, a configurable semantic icon registry, and shared ViewSet navbar rendering are package-side UI integration points (`src/crud_views/templates/crud_views/`, `src/crud_views/lib/icons.py`, `src/crud_views/lib/navbar.py`)
- `cv_data_prefix` and `#cv-config` expose the registered prefix to markup and JavaScript (`src/crud_views/templatetags/crud_views.py`, `src/crud_views/templates/crud_views/tags/cv_config.html`). Prefix-sensitive native attributes are limited to actions-menu toggles, the language selector, vertical object-detail tabs, and accordion groups; object-detail `tabs.js` also discovers prefixed tab triggers only within `data-cv-od-tabs` tablists (`src/crud_views_object_detail/static/crud_views_object_detail/js/tabs.js`). A theme overriding `cv_config.html` must preserve `data-data-prefix` for custom-prefix tab discovery; absent config/attribute falls back to `bs`. Registration does not change host markup, CSS classes, DOM structure, or the tab adapter (`docs/reference/theme.md`, `docs/reference/javascript.md`)
- Navbar declarations are configured on ViewSets and rendered through `cv_navbar`, `cv_navbar_identity`, and `cv_navbar_items` template tags (`src/crud_views/lib/navbar.py`, `src/crud_views/templatetags/crud_views.py`, `src/crud_views/templates/crud_views/tags/navbar.html`)
- Manage pages and formsets use six optional `--cv-*` CSS custom properties, each with Bootstrap-property and literal fallbacks. Themes may map these aliases on every theme root for nested color modes; the package does not declare global token values (`src/crud_views/static/crud_views/css/manage.css`, `src/crud_views/static/crud_views/css/formset.css`, `docs/reference/theme.md`)
- Bulk actions are opt-in per ORM ViewSet: a table/card list declares destination keys and a permission-required bulk form re-resolves submitted keys in the destination queryset/scope before review and execution (`src/crud_views/lib/bulk/__init__.py`)
- `bulk.js` enhances the native bulk form with current-page selection, selected count, and disabled action buttons for empty selections. It initializes once per form at document readiness and refreshes browser-restored selections on `pageshow`; record ownership comes from the native `form` association. It has no third-party dependency, persistence, or requests. Without JavaScript or required enhancement controls, native submission remains available (`src/crud_views/static/crud_views/js/bulk.js`, `docs/reference/javascript.md`, `tests/js/bulk.test.js`)
- Theme bulk action styling uses `crud_views/tags/button/bulk.html`, whose native POST fields and `formaction` preserve the selection/review transport. Each destination supplies `cv_action_variant` (default `secondary`); configure `bulk:primary`, `bulk:secondary`, `bulk:tertiary`, and `bulk:danger` through `register_button_classes()` or project `CRUD_VIEWS_BUTTON_CLASSES`. All stock variant classes are `btn btn-primary`; set theme classes explicitly for a distinct danger appearance (`src/crud_views/lib/bulk/__init__.py`, `src/crud_views/templates/crud_views/tags/button/bulk.html`, `src/crud_views/lib/button_classes.py`)
- The bulk toolbar offers destinations only to viewers who pass `cv_has_access`/`cv_action_enabled`; the `view.cv_bulk_buttons` guard applies this, and overridden templates must not re-expose unauthorized destinations (`docs/reference/theme.md`, `tests/test1/test_bulk_docs.py`)
- Bulk buttons use `CRUD_VIEWS_LABEL_MODE_DEFAULTS['bulk']` (default `both`), with effective-mode class overrides such as `bulk:danger:label` taking precedence over base variant keys, including empty or `None` values. Missing/disabled icons fall back to label mode. Preserve the shared `form:hidden-label`, `form:icon-host`, and `data-cv-tooltip="form"` conventions when overriding the bulk leaf. Review Confirm remains governed by `form:submit`; toolbar buttons use the bulk keys (`src/crud_views/lib/view/label_mode.py`, `src/crud_views/lib/button_classes.py`, `src/crud_views/templates/crud_views/tags/button/bulk.html`, `docs/reference/bulk_actions.md`)
- The bulk default per-object permission hook returns `True`. Guardian hosts must implement `cv_bulk_has_permission(obj)` for their policy; system check `crud_views_guardian.W002` warns about an inherited default. Bulk actions accept unsliced model querysets with scalar primary keys on the default database only; application writes must honor `cv_get_db_alias()` (`src/crud_views/lib/bulk/__init__.py`, `src/crud_views_guardian/checks.py`, `docs/reference/guardian.md`, `docs/reference/bulk_actions.md`)
- Formset browser enhancement requires host-supplied jQuery. Bootstrap-compatible adapters and `bulk.js` use native browser APIs; do not infer a jQuery requirement for every script from the test harness (`src/crud_views/static/crud_views/js/formset.js`, `src/crud_views/static/crud_views/js/adapters.js`, `src/crud_views/static/crud_views/js/bulk.js`, `package.json`)
- The stock breadcrumb template resolves `breadcrumb:list`, `breadcrumb:item`, and `breadcrumb:item-active` through `cv_button_class`. Register theme defaults with `register_button_classes()` during startup; project `CRUD_VIEWS_BUTTON_CLASSES` values override them. Class overrides preserve breadcrumb escaping, links, and current-page semantics (`src/crud_views/lib/button_classes.py`, `src/crud_views/templates/crud_views/tags/breadcrumb.html`, `docs/reference/theme.md`, `tests/test1/test_breadcrumb.py`)

**Sibling theme repositories (development only):**
- The Acme example is kept in sync across the tabler, coreui, and adminlte theme repos by a prompt-driven workflow; `drift.py` shells out to `git` against sibling checkouts. A shared-demo alternative is evaluated in `superpowers/specs/2026-11-22-shared-acme-demo-design.md` (`superpowers/prompts/acme-example-sync/`)

## Data Storage

**Databases:**
- Ordinary ORM views use database configuration supplied by the host Django project; the package defines no connection credentials. Bulk actions specifically require the default database (`src/crud_views/lib/view/base.py`, `src/crud_views/lib/bulk/__init__.py`)
- Example project uses SQLite (`examples/bootstrap5/project/settings.py`); package tests configure in-memory Django test databases (`tests/test1/conftest.py`)
- django-guardian stores object permission grants through its Django models when the optional integration is installed (`src/crud_views_guardian/`)

**File Storage:**
- No package-managed object-storage service. Asset vendoring writes downloaded static files and a `.vendored` stamp into a project-owned target directory; demo static files are served with whitenoise (`src/crud_views/lib/vendor.py`, `requirements/demo.txt`, `examples/bootstrap5/project/settings_demo.py`)

**Caching:**
- No external cache service configured by the package; the demo uses Django's process-local `LocMemCache` for rate limiting (`examples/bootstrap5/project/settings_demo.py`)

## Authentication & Identity

**Auth Provider:**
- Django `django.contrib.auth` users and model permissions are the core permission integration (`src/crud_views/lib/`)
- django-guardian adds optional per-object permission checks (`src/crud_views_guardian/`)
- No third-party identity provider is bundled; authentication setup belongs to the host project (`examples/bootstrap5/project/settings.py`)

## Monitoring & Observability

**Error Tracking:**
- No runtime error-tracking service detected in package dependencies (`pyproject.toml`)

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
- Nox defines a Crispy dependency-floor matrix for Django 4.2 and 6.0, including bulk variant, flow, execution, source, scope, and return tests. The main Python workflow invokes the normal compatibility and example sessions; floor sessions require a separate nox invocation (`noxfile.py`, `.github/workflows/tests.yml`, `tests/test1/test_bulk_variants.py`)
- JavaScript CI installs the npm lock with scripts disabled and runs the unit configuration on Node 22. `npm run test:integration` selects the separate integration configuration; the JS workflow does not invoke that script (`.github/workflows/js.yml`, `package.json`, `vitest.config.js`, `vitest.integration.config.js`)
- Demo deploy workflow invokes the Render API (`.github/workflows/demo.yml`); package publishing uses PyPI trusted publishing action (`.github/workflows/publish.yml`)

## Environment Configuration

**Required env vars:**
- Runtime library: values are optional Django settings prefixed `CRUD_VIEWS_` (`src/crud_views/lib/settings.py`)
- Demo: `DJANGO_SETTINGS_MODULE` and generated `SECRET_KEY` (`render.yaml`)
- Cloudflare tunnel: `TUNNEL_TOKEN` when starting `task cf` (`dev/docker-compose.yaml`)
- CI/deploy credentials: `CODECOV_TOKEN`, `RENDER_API_KEY`, and `RENDER_SERVICE_ID` are GitHub Actions secret references; `DEMO_URL` is a repository variable. PyPI uses OIDC trusted publishing with `id-token: write` (`.github/workflows/tests.yml`, `.github/workflows/demo.yml`, `.github/workflows/publish.yml`)

**Secrets location:**
- GitHub Actions secrets for CI and Render deployment (`.github/workflows/tests.yml`, `.github/workflows/demo.yml`)
- Local tunnel configuration is expected in `dev/.env`; a tracked `dev/.env.example` template exists. Environment-file contents are not read (`taskfile.yaml`)
- Render generates the demo `SECRET_KEY` from its blueprint (`render.yaml`)

## Webhooks & Callbacks

**Incoming:**
- No package webhook endpoints. The demo exposes the Django application's `/login/` health-check path (`render.yaml`)

**Outgoing:**
- Demo deployment workflow calls Render's API (`.github/workflows/demo.yml`)
- No third-party outbound service callbacks detected in the package; UI fetch calls target host application endpoints (`src/crud_views/static/crud_views/js/modal.js`, `src/crud_views/static/crud_views/js/list.filter.js`)

## Guardian Grant Ownership

`src/crud_views_guardian/lib/permissions.py` owns the private `_get_guardian_checker(user)` accessor. `GuardianObjectPermissionMixin` request and callable object checks and the ancestor provider reuse that checker through the actual supplied user. Guardian's loaded object grants are reused; each destination still tests its permission and action state.

Fresh normal requests receive fresh users/checkers. Retaining a Python user also retains loaded positive/negative grants across grant mutations; see `docs/reference/guardian.md`. Queryset filtering and independent auth backend paths do not populate this shared checker. Configured anonymous users, model fallback, inactive actors and default-database checks retain their existing provider rules (`src/crud_views_guardian/lib/mixins.py`, `ancestors.py`).

---

*Integration audit: 2026-11-24*
