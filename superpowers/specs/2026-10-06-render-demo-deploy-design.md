# Design: Public Demo of the Example Project on Render

## Goal

Host `examples/bootstrap5` as a public, click-around demo for people evaluating django-crud-views.
It runs on Render's free plan with a disposable SQLite database. GitHub Actions deploys it on release tags or a
manual trigger and wipes its data daily.

Non-goals: user registration, persistent user data, a staging environment, any personal data.

## Constraints (verified against Render docs, 2026-10-06)

- Free web services spin down after 15 min without traffic; the next request wakes them in ~1 min.
- The filesystem — including SQLite — is lost on every redeploy, restart and spin-down. Seeding on start is
  therefore mandatory, not just a daily concern.
- No pre-deploy command and no cron jobs on the free plan → migrate + seed run in the start command; the daily
  reset is driven from GitHub Actions.
- 750 free instance hours per workspace per month; spun-down time does not count. One service fits.
- API: `POST /v1/services/{id}/deploys` with `{"commitId": "<sha>"}` deploys a specific commit and does **not**
  disable auto-deploy → the service must have `autoDeploy: false`. `POST /v1/services/{id}/restart` starts a new
  instance on the same commit and config (fresh filesystem, no rebuild).

## 1. Demo users: alice and bob only, everywhere

The `admin/admin` superuser is removed from the example project — locally and on the demo.

- `project/seeding.py`: `DEMO_USERS` = `alice/alice`, `bob/bob` (both regular users).
- `workflow/seed.py`: uses `alice` as the transition actor instead of `admin`.
- Text updates: home page alert, login page hint, `seed` command output, `project/features.py` guardian text.
- `/admin/` stays mounted locally but has no seeded login; the docs point to `python manage.py createsuperuser`.
- Docs: `docs/development/index.md` (line 39 currently promises `admin/admin`), the tutorial-5 sentence about
  revoking a permission in the Django admin (now: create a superuser first), `docs/reference/guardian.md`
  (describe the four seeded documents).

### Guardian: add a document shared with edit rights

`guardian_demo/seed.py` gains one document owned by bob that alice may view and change, but not delete:

| Document        | Owner | alice                | bob                  |
|-----------------|-------|----------------------|----------------------|
| Roadmap 2027    | alice | view, change, delete | —                    |
| Team Handbook   | alice | view, change, delete | view                 |
| Meeting Notes   | bob   | —                    | view, change, delete |
| Release Checklist | bob | view, change         | view, change, delete |

## 2. Demo settings

New `examples/bootstrap5/project/settings_demo.py` does `from project.settings import *` and overrides:

- `DEBUG = False`
- `SECRET_KEY = os.environ["SECRET_KEY"]` — import fails loudly if unset.
- `ALLOWED_HOSTS = [os.environ.get("RENDER_EXTERNAL_HOSTNAME", "")]`, `CSRF_TRUSTED_ORIGINS = ["https://<that host>"]`.
- `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`.
- whitenoise: `WhiteNoiseMiddleware` right after `SecurityMiddleware`, `STATIC_ROOT = BASE_DIR / "staticfiles"`,
  compressed manifest storage.
- `DEMO_MODE = True` (base settings get `DEMO_MODE = False`); a `project.context_processors.demo` context
  processor exposes it to templates.
- Rate-limit middleware appended to `MIDDLEWARE`; `CACHES` = local memory.

`DEMO_MODE` controls exactly two things; the rate-limit middleware is simply only listed in `settings_demo`:

1. `/admin/` is not mounted: `settings_demo` sets `ROOT_URLCONF = "project.urls_demo"`, which re-exports
   `project.urls.urlpatterns` without the admin entry (testable via `override_settings`, no module reload).
2. The base template shows a banner: "Public demo — data resets daily and after inactivity. Log in as alice/alice
   or bob/bob."

Deploy-only dependencies live in a new `requirements/demo.txt` (`gunicorn`, `whitenoise`, `django-ratelimit`),
not in a package extra, so the published package metadata is unchanged.

## 3. Rate limiting on writes

`project/ratelimit.py` — a middleware built on `django_ratelimit.core.is_ratelimited`:

- Applies only to methods other than GET, HEAD, OPTIONS. Login POSTs count like any other write.
- Key: client IP. Per-user keys are wrong here because everyone shares alice and bob.
- Limits: **30 writes/minute and 300 writes/day per IP** (both checked; either trips it).
- Over the limit: HTTP 429 rendering `project/429.html` inside the site layout ("Too many changes — please try
  again in a minute.").
- Counters live in the local-memory cache; losing them on restart is acceptable.

Client IP: Render sits behind Cloudflare plus its own proxy, and both append to `X-Forwarded-For`. The leftmost
entries are client-controlled (spoofable), and the rightmost is a Render-internal 10.x address shared by every
visitor. Neither works as a key. Render sets `True-Client-IP` to the real client address and overwrites a
client-sent one, so `client_ip(request)` reads `True-Client-IP`, falling back to `REMOTE_ADDR` (local runs,
tests). This is confirmed against a live request on the first deploy.

## 4. Render service

`render.yaml` at the repo root (a Render Blueprint), created once by hand from the Render dashboard:

```yaml
services:
  - type: web
    name: django-crud-views-demo
    runtime: python
    plan: free
    autoDeploy: false
    buildCommand: >-
      pip install ".[all,examples]" -r requirements/demo.txt &&
      cd examples/bootstrap5 && DJANGO_SETTINGS_MODULE=project.settings_demo
      python manage.py collectstatic --noinput
    startCommand: >-
      cd examples/bootstrap5 && python manage.py migrate --noinput && python manage.py seed &&
      gunicorn project.wsgi --bind 0.0.0.0:$PORT
    healthCheckPath: /login/
    envVars:
      - key: DJANGO_SETTINGS_MODULE
        value: project.settings_demo
      - key: SECRET_KEY
        generateValue: true
      - key: PYTHON_VERSION
        value: "3.13"
```

The extras match what `readme-examples.yml` installs. `SECRET_KEY` (a blueprint env var) is available at build
time. `RENDER_EXTERNAL_HOSTNAME` may not be, so `settings_demo` reads it with `os.environ.get(..., "")`. An empty
value at runtime makes every request a 400, which the workflow's smoke test catches.

## 5. GitHub Actions: `.github/workflows/demo.yml`

Triggers:

- `push` of tags `v*` → **deploy** job.
- `workflow_dispatch` with a boolean input `reset_only` (default false) → deploy, or reset when ticked.
- `schedule: cron "0 3 * * *"` (03:00 UTC) → **reset** job.

Jobs (each a short `curl` script against `https://api.render.com/v1`, bearer `RENDER_API_KEY`):

- **deploy**: `POST /services/$RENDER_SERVICE_ID/deploys` with `commitId: ${{ github.sha }}`; poll the deploy
  until `live` (fail on `build_failed`/`update_failed`/`canceled`, time out after 15 min).
- **reset**: `POST /services/$RENDER_SERVICE_ID/restart`; then wait until the service answers.
- **smoke test** (after either): `GET $DEMO_URL/login/` → 200 (retry up to ~3 min to cover a cold start);
  `GET $DEMO_URL/admin/` → 404.

Configuration: secrets `RENDER_API_KEY`, `RENDER_SERVICE_ID`; repository variable `DEMO_URL`. The workflow uses
`concurrency: demo` so a reset and a deploy never overlap.

The deploy is not gated on the test workflow; release tags are only cut from a green `main`.

## 6. Documentation

- New page `docs/getting_started/demo.md`: link to the live demo, alice/bob logins, what differs between them
  (guardian), resets (daily at 03:00 UTC and after ~15 min idle, first request may take ~1 min), write rate limit,
  no admin site.
- `docs/development/` gains a short "Deploying the demo" section: one-time Render blueprint setup, the two secrets
  and one variable, how to trigger a manual deploy or reset.
- README: one line linking to the live demo (outside the "Run the example project" section, which is in lockstep
  with `readme-examples.yml`).

## 7. Testing

In the example project's test suite (runs in the existing `examples` nox session):

- Seed creates alice and bob only; no `admin` user (flips the assertion at `project/tests.py:39`).
- Workflow seed runs without an `admin` user; history actor is alice.
- Guardian seed: alice can change but not delete "Release Checklist"; bob has all three; the existing
  visibility assertions still hold.
- Demo settings (with `SECRET_KEY` and `RENDER_EXTERNAL_HOSTNAME` set via the test's environment):
  - `/admin/` returns 404, the banner renders on the home page.
  - The 31st POST within a minute from one IP returns 429; GETs are never limited; a second IP is unaffected.
  - Importing `settings_demo` without `SECRET_KEY` raises.

The live deployment is verified by the workflow's smoke test, not by unit tests.

## Manual steps (not automatable)

1. In Render: New → Blueprint → select this repository → creates the service from `render.yaml`.
2. Create a Render API key; add `RENDER_API_KEY` and `RENDER_SERVICE_ID` as GitHub secrets and `DEMO_URL` as a
   repository variable.
3. Run `demo.yml` manually once to deploy the current release.
