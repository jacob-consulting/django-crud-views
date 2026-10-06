# Development

This section describes how to setup the development environment and how to create themes and extensions.

## Requirements

You need these tools development:

- [uv](https://docs.astral.sh/uv/guides/install-python/)
- [taskfile](https://taskfile.dev/installation/)

## Setup

Set up your local development environment:

```bash
git clone git@github.com:jacob-consulting/django-crud-views.git
cd django-crud-views
task dev
```

## JS tests

The package's static JavaScript (`formset.js`, `modal.js`, `toggle.js`, `tooltip.js`, …) has a
[Vitest](https://vitest.dev/) unit-test suite. It needs [Node.js](https://nodejs.org/) 20+:

```bash
task test-js
```

## Run example application

Now let's run the example application with the `bootstrap5` theme:

```bash
cd examples/bootstrap5
task run
```
> **Note:** This will run the migrations, seed demo data, and start the dev server. It creates the demo users `alice` / `alice` and `bob` / `bob` (see `project/seeding.py`). To use the Django admin at `/admin/`, create a superuser first: `python manage.py createsuperuser`.

[Then open the app in your browser at http://localhost:8000](http://localhost:8000)

## Deploying the demo

The public demo runs `examples/bootstrap5` on Render's free plan, as described by `render.yaml` at the repo root,
with `project.settings_demo` (no admin, reset banner, per-IP write rate limit). The workflow
`.github/workflows/demo.yml` drives it:

- **pushing a `v*` tag** deploys exactly that commit
- **Run workflow** (manual) deploys the selected ref; tick *reset_only* to just wipe the data
- **daily at 03:00 UTC** it restarts the service, which gives it a fresh database

Each run ends with a smoke test: `/login/` must return 200 and `/admin/` 404.

One-time setup:

1. In Render: **New → Blueprint**, select this repository. This creates the `django-crud-views-demo` service.
2. Create an API key (Account settings → API keys).
3. In GitHub (Settings → Secrets and variables → Actions) add the secrets `RENDER_API_KEY` and
   `RENDER_SERVICE_ID` (the `srv-…` id from the service URL) and the variable `DEMO_URL`
   (e.g. `https://django-crud-views-demo.onrender.com`, no trailing slash).
4. Run the `demo` workflow manually once.

To rehearse the demo settings locally: `DJANGO_SETTINGS_MODULE=project.settings_demo SECRET_KEY=x
RENDER_EXTERNAL_HOSTNAME=localhost python manage.py collectstatic --noinput`, then start gunicorn as in
`render.yaml`.

## Claude Code skill

A [Claude Code](https://docs.claude.com/en/docs/claude-code) skill for building with `django-crud-views`
is maintained in a separate repository: [jacob-consulting/skills](https://github.com/jacob-consulting/skills).
It is no longer bundled inside this repository.
