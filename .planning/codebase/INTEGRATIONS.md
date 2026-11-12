---
last_mapped_at: 2026-11-12
last_mapped_commit: c92671d066e71dbbfb372a17161d08532a01b3f8
---
# External Integrations

**Analysis Date:** 2026-11-12

## APIs & External Services

**Django host application:**
- Uses Django app registration, URL routing, templates, settings, ORM, auth/permissions, content types, messages, and system checks (`src/crud_views/apps.py`, `src/crud_views/lib/viewset/`, `src/crud_views/checks.py`).
  - SDK/Client: Django APIs
  - Auth: The host project configures users, middleware, backends, and permissions.

**Forms, tables, and filtering:**
- django-crispy-forms and crispy-bootstrap5 render Bootstrap forms; django-tables2 and django-filter integrate list tables and filters (`src/crud_views/lib/crispy/`, `src/crud_views/lib/table/`, `src/crud_views/lib/views/mixins.py`).
  - SDK/Client: `crispy_forms`, `crispy_bootstrap5`, `django_tables2`, `django_filters`
  - Auth: None; these use host Django configuration.
- Bootstrap is a host-delivered frontend dependency, not a Python runtime dependency. The getting-started guide shows Bootstrap 5.3.3 CSS and JS from jsDelivr; host projects may instead provide local assets and own version/CSP policy (`docs/getting_started/tutorial-1-setup.md`).
- Compact formsets explicitly support the exact stock Django `CheckboxInput` with standard template and input type, including Bootstrap styling for package-owned crispy markup. A marked subclass may receive that styling incidentally, but custom widgets/templates are not certified and own accessibility and responsive behavior (`docs/reference/formsets.md`).
- Theme styling for the `ToggleGroup` and formset `<legend>` elements is exposed through the `conditional:legend` and `formset:legend` button-class slots; it adds no dependency or service integration (`src/crud_views/templates/crud_views/conditional/toggle_group.html`, `src/crud_views/templates/crud_views/formsets/formset.html`, `src/crud_views/lib/button_classes.py`).
- Compact formsets add explicit `CompactColumn` and `CompactLayout` presentation metadata on top of Django inline formsets and crispy helpers; they introduce no service or package dependency (`src/crud_views/lib/formsets/compact.py`, `src/crud_views/lib/formsets/formsets.py`, `docs/reference/formsets.md`).

**Optional Django extensions:**
- Install extras independently as `django-crud-views[workflow]`, `[polymorphic]`, `[guardian]`, or `[ordered]`; `[all]` combines them. The apps are shipped in the distribution, but each optional integration requires its corresponding third-party package and app setup (`pyproject.toml`, `src/crud_views_workflow/`, `src/crud_views_polymorphic/`, `src/crud_views_guardian/`).
- django-fsm-2 and django-fsm-2-admin provide workflow transitions and admin integration (`src/crud_views_workflow/`). `run_transition()` validates actor, object, and transition state and writes history atomically on the selected DB alias (`src/crud_views_workflow/lib/execution.py`); direct FSM method calls bypass that helper behavior.
- django-polymorphic supports polymorphic querysets and type-specific creation (`src/crud_views_polymorphic/`).
- django-guardian adds per-object permission checks and uses the host project's auth backend configuration (`src/crud_views_guardian/lib/mixins.py`).
- django-ordered-model supports ordering actions for host models that opt in (`src/crud_views/lib/ordered.py`, `pyproject.toml`).

**Icons and frontend assets:**
- `src/crud_views/lib/icons.py` provides plain icon constants and a semantic icon registry; the host template supplies matching icon-font CSS (`docs/reference/icons.md`). Applications and theme apps can register icon mappings/renderers.
- Django serves package static assets. Optional django-pipeline support is lazy and is not a runtime dependency; with `CRUD_VIEWS_ASSETS_BUNDLED`, package tags emit external bundle entries for the host bundler (`src/crud_views/lib/assets.py`, `src/crud_views/lib/pipeline.py`, `docs/reference/assets.md`).
- Asset registrations may use external CDN URLs and SRI/CSP nonce attributes; the host owns Bootstrap/icon CSS delivery and CSP policy (`src/crud_views/lib/assets.py`).
- Formset client behavior is bundled in `src/crud_views/static/crud_views/js/formset.js`; its supported page integration uses jQuery, while compact layout uses package CSS (`src/crud_views/static/crud_views/css/formset.css`).

**Caller-provided resource sources:**
- `Resource` and `ResourceViewMixin` accept application data through `cv_get_items()` and optionally `cv_get_item()`; no provider SDK or built-in API/filesystem adapter is included (`src/crud_views/lib/resource.py`).
- Resource views default to `cv_atomic = False`; database transactions cannot roll back external API or storage writes (`src/crud_views/lib/resource.py`).

## Data Storage

**Databases:**
- The Django host selects database providers through `DATABASES`; package ORM operations use Django connections.
- Workflow audit history is stored in the host database, and transition/history writes share a transaction (`src/crud_views_workflow/models.py`, `src/crud_views_workflow/lib/execution.py`).
- The demo uses SQLite (`examples/bootstrap5/project/settings_demo.py`, `render.yaml`).

**File Storage:**
- No package-managed file-storage service; the Django host owns storage backends. Demo static files are collected and served by WhiteNoise (`render.yaml`, `requirements/demo.txt`).

**Caching:**
- No external cache or package-managed caching service detected.

## Authentication & Identity

**Auth Provider:**
- Django's configured authentication and permission system (`src/crud_views/lib/view/`); the host owns user models, auth middleware, and permission grants.
- Optional `src/crud_views_guardian/` integrates django-guardian object permissions and its configured backend.
- No login implementation or external identity-provider client is included.

## Monitoring & Observability

**Error Tracking:**
- No error-tracking SDK detected in package dependencies or source.

**Logs:**
- No package-specific logging backend; the host Django deployment manages logs. The demo runs under Gunicorn (`render.yaml`).

## CI/CD & Deployment

**Hosting:**
- Hatchling builds the Python wheel and sdist; the reusable library does not prescribe hosting (`pyproject.toml`).
- The public example deploys to Render with Gunicorn and WhiteNoise (`render.yaml`, `requirements/demo.txt`).
- Documentation is built with MkDocs on Read the Docs (`mkdocs.yml`, `.readthedocs.yaml`).

**CI Pipeline:**
- GitHub Actions cover Python/Django tests, lint, docs, JavaScript tests, release publication, demo deployment, and README examples (`.github/workflows/`).
- Release publication uses PyPI trusted publishing; coverage uploads to Codecov (`.github/workflows/publish.yml`, `.github/workflows/tests.yml`).
- The demo workflow deploys release tags through the Render API; credentials are configured in GitHub/Render settings (`.github/workflows/demo.yml`).
- Optional local tunnel uses Cloudflare Tunnel through Docker Compose (`dev/docker-compose.yaml`); `dev/.env.example` documents local configuration keys. No populated `dev/.env` file is present.

## Environment Configuration

**Required env vars:**
- None for the reusable package. Host Django settings provide project database and secret configuration; demo settings require `SECRET_KEY` and optionally read `RENDER_EXTERNAL_HOSTNAME` (`examples/bootstrap5/project/settings_demo.py`).

**Secrets location:**
- Host/deployment environment; `dev/.env.example` is a template only. Secret file contents are not inspected. Deployment secret names are documented in `docs/development/index.md`.

## Webhooks & Callbacks

**Incoming:**
- None provided by the package; host applications define their request endpoints.

**Outgoing:**
- No package-managed webhook delivery. Workflow views register follow-up work with Django `transaction.on_commit()` (`src/crud_views_workflow/lib/views.py`).

---

*Integration audit: 2026-11-12*
