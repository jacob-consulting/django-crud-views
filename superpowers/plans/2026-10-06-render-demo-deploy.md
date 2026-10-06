# Public Demo on Render Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run `examples/bootstrap5` as a public, self-resetting demo on Render's free plan, deployed from GitHub
Actions on release tags or a manual trigger, and wiped daily.

**Architecture:** The example project gains a `settings_demo.py` that hardens it (env-driven secret and host,
whitenoise, no admin URL, a reset banner, a per-IP write rate limit). A `render.yaml` blueprint runs it on gunicorn
and re-seeds SQLite on every start. A `demo.yml` workflow drives Render's REST API: deploy a specific commit, or
restart for a fresh filesystem. The seeded users become alice/bob only, everywhere, and the guardian example gains
a document shared with edit rights.

**Tech Stack:** Django 4.2–6.0, gunicorn, whitenoise, django-ratelimit (`core.is_ratelimited` only), Render
Blueprint + REST API v1, GitHub Actions, curl + jq.

**Spec:** `superpowers/specs/2026-10-06-render-demo-deploy-design.md`

## Global Constraints

- Branch: `feature/render-demo-deploy` (exists, spec already committed). Never commit to `main`; never merge.
- Local `task run` behaviour stays the same apart from the seeded users. `project/settings.py` must not import any
  demo-only dependency.
- Demo-only dependencies live in `requirements/demo.txt`. No new package extra; `pyproject.toml` stays unchanged.
- Demo users everywhere: `alice/alice`, `bob/bob`, both regular users. No `admin` user is seeded.
- Rate limits: `("30/m", "300/d")` per client IP, on every method except GET, HEAD, OPTIONS, login included.
- Client IP: `True-Client-IP` header, falling back to `REMOTE_ADDR`. Never `X-Forwarded-For`.
- Render: free plan, `autoDeploy: false`, service name `django-crud-views-demo`, Python 3.13.
- Workflow: tags `v*` and `workflow_dispatch` deploy; `schedule` `0 3 * * *` and `workflow_dispatch` with
  `reset_only: true` restart. Secrets `RENDER_API_KEY`, `RENDER_SERVICE_ID`; repository variable `DEMO_URL`.
- Line length 120, double quotes, ruff format runs as a pre-commit hook.
- Never name customer projects anywhere (repo rule).

## Review Focus

1. **Spoofed client IP**: a client that rotates `X-Forwarded-For` while its `True-Client-IP` stays the same must
   still be limited. Pinned in Task 3 (`test_rotating_x_forwarded_for_does_not_escape_the_limit`).
2. **Shared bucket**: two visitors with different `True-Client-IP` must not share one counter, which would happen if
   the key were Render's proxy address. Pinned in Task 3 (`test_other_client_ip_is_unaffected`).
3. **Reads after the limit**: a limited visitor must still be able to browse with GET. Pinned in Task 3
   (`test_get_is_never_limited`).
4. **Base settings mutated by the demo settings**: `settings_demo` must build new lists, not append to the imported
   `MIDDLEWARE`. Otherwise the local settings in the same process would get whitenoise and the rate limit. Pinned in
   Task 4 (`test_base_middleware_is_not_mutated`).
5. **Deploy API returns no deploy id** (for example when Render queues a deploy): the workflow must fail loudly
   rather than poll `deploys/null` forever. Pinned in Task 5 by the explicit `null`/empty check in the deploy
   script.

---

### Task 1: Demo users are alice and bob only

**Files:**
- Modify: `examples/bootstrap5/project/seeding.py:5-10`
- Modify: `examples/bootstrap5/workflow/seed.py`
- Modify: `examples/bootstrap5/project/management/commands/seed.py:14`
- Modify: `examples/bootstrap5/project/templates/project/home.html:37-40`
- Modify: `examples/bootstrap5/project/templates/registration/login.html:13-17`
- Modify: `docs/development/index.md:39`
- Modify: `docs/getting_started/tutorial-5-filters-permissions.md:94-96`
- Test: `examples/bootstrap5/project/tests.py`

**Interfaces:**
- Produces: `project.seeding.DEMO_USERS` = `[("alice", "alice", False), ("bob", "bob", False)]`;
  `ensure_demo_users()` keeps its signature and return type (`dict[str, User]`).

- [ ] **Step 1: Write the failing tests**

In `examples/bootstrap5/project/tests.py`, replace the body of `SeedCommandTest.test_seed_twice_is_idempotent`
and add login/home assertions:

```python
class SeedCommandTest(TestCase):
    def test_seed_twice_is_idempotent(self):
        call_command("seed")
        call_command("seed")
        User = get_user_model()
        self.assertTrue(User.objects.filter(username="alice", is_superuser=False).exists())
        self.assertTrue(User.objects.filter(username="bob", is_superuser=False).exists())

    def test_seed_creates_no_admin_user(self):
        call_command("seed")
        User = get_user_model()
        self.assertFalse(User.objects.filter(username="admin").exists())
        self.assertFalse(User.objects.filter(is_superuser=True).exists())
```

In `HomePageTest`, add:

```python
    def test_pages_do_not_advertise_admin_user(self):
        for name in ("home", "login"):
            resp = self.client.get(reverse(name))
            self.assertNotContains(resp, "admin/admin")
            self.assertContains(resp, "alice/alice")
            self.assertContains(resp, "bob/bob")
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run: `cd examples/bootstrap5 && ../../.venv/bin/python -m pytest project/tests.py -k "Seed or advertise" -v`
Expected: `test_seed_creates_no_admin_user` and `test_pages_do_not_advertise_admin_user` FAIL (an admin user exists;
the pages contain `admin/admin`).

- [ ] **Step 3: Implement**

`project/seeding.py`:

```python
#: username, password, is_superuser — shown on the home and login pages
DEMO_USERS = [
    ("alice", "alice", False),
    ("bob", "bob", False),
]
```

`workflow/seed.py`: rename the actor (WorkflowInfo rows are written only by the workflow view, so this is only the
`by=` argument):

```python
def seed():
    User = get_user_model()
    actor = User.objects.get(username="alice")
    for username in ("alice", "bob"):
        grant_model_perms(User.objects.get(username=username), Campaign)

    Campaign.objects.get_or_create(name="Spring Newsletter")  # stays in draft

    summer, created = Campaign.objects.get_or_create(name="Summer Sale")
    if created:
        summer.wf_activate(by=actor)
        summer.save()

    winter, created = Campaign.objects.get_or_create(name="Winter Launch")
    if created:
        winter.wf_activate(by=actor)
        winter.save()
        winter.wf_complete(by=actor, comment="Wrapped up early")
        winter.save()
```

`project/management/commands/seed.py` line 14:

```python
        self.stdout.write("users: alice/alice, bob/bob")
```

`home.html` alert:

```html
    <div class="alert alert-info mt-4">
        Demo users (created by <code>manage.py seed</code>): <code>alice/alice</code> and <code>bob/bob</code>
        (regular users — the Guardian example shows them different documents).
    </div>
```

`login.html` alert:

```html
                    <div class="alert alert-info mb-0 mt-3">
                        Demo users: <code>alice/alice</code>, <code>bob/bob</code> —
                        run <code>manage.py seed</code> first.
                    </div>
```

`docs/development/index.md` line 39:

```markdown
> **Note:** This will run the migrations, seed demo data, and start the dev server. It creates the demo users `alice` / `alice` and `bob` / `bob` (see `project/seeding.py`). To use the Django admin at `/admin/`, create a superuser first: `python manage.py createsuperuser`.
```

`docs/getting_started/tutorial-5-filters-permissions.md`, replace the sentence ending "…try revoking one via the
Django admin to see the create button and the 403 for yourself." with:

```markdown
full `Author` and `Book` permissions this way. To see the create button disappear and the 403 for
yourself, create a superuser (`python manage.py createsuperuser`), revoke one of alice's permissions in
the Django admin at `/admin/`, and log in as alice again.
```

- [ ] **Step 4: Run the full example suite**

Run: `cd examples/bootstrap5 && ../../.venv/bin/python -m pytest -q`
Expected: all pass (this includes `test_docs_sync.py` and the workflow seed test, which now runs without an
`admin` user).

- [ ] **Step 5: Commit**

```bash
git add examples/bootstrap5/project examples/bootstrap5/workflow/seed.py docs/development/index.md docs/getting_started/tutorial-5-filters-permissions.md
git commit -m "feat(examples): seed alice and bob only, no admin superuser"
```

---

### Task 2: Guardian document shared with edit rights

**Files:**
- Modify: `examples/bootstrap5/guardian_demo/seed.py`
- Modify: `examples/bootstrap5/project/features.py:107-115` (guardian `description` and `about`)
- Modify: `docs/reference/guardian.md:218-219`
- Test: `examples/bootstrap5/guardian_demo/tests.py`

**Interfaces:**
- Consumes: the `alice`/`bob` users from Task 1; `cv_document.assign_perm(action, user, obj)`.
- Produces: a seeded `Document` titled `"Release Checklist"`, owned by bob; alice has `view` and `change` on it.

- [ ] **Step 1: Write the failing test**

Append to `guardian_demo/tests.py`:

```python
class GuardianSeedEditShareTest(TestCase):
    """The seed shares one of bob's documents with alice: she may edit it, not delete it."""

    def setUp(self):
        from django.core.management import call_command

        call_command("seed")
        User = get_user_model()
        self.alice = User.objects.get(username="alice")
        self.bob = User.objects.get(username="bob")
        self.doc = Document.objects.get(title="Release Checklist")

    def test_owned_by_bob(self):
        self.assertEqual(self.doc.owner, self.bob)

    def test_alice_can_view_and_edit(self):
        self.client.force_login(self.alice)
        self.assertContains(self.client.get(reverse("document-list")), "Release Checklist")
        self.assertEqual(self.client.get(reverse("document-update", kwargs={"pk": self.doc.pk})).status_code, 200)

    def test_alice_cannot_delete(self):
        self.client.force_login(self.alice)
        self.assertEqual(self.client.get(reverse("document-delete", kwargs={"pk": self.doc.pk})).status_code, 403)

    def test_bob_has_full_rights(self):
        self.client.force_login(self.bob)
        for key in ("document-detail", "document-update", "document-delete"):
            self.assertEqual(self.client.get(reverse(key, kwargs={"pk": self.doc.pk})).status_code, 200, key)
```

- [ ] **Step 2: Run it and confirm it fails**

Run: `cd examples/bootstrap5 && ../../.venv/bin/python -m pytest guardian_demo/tests.py -k EditShare -v`
Expected: FAIL with `Document.DoesNotExist` in `setUp`.

- [ ] **Step 3: Implement**

`guardian_demo/seed.py`: add the document to bob's list and grant alice view and change after the existing
handbook share:

```python
    "bob": [
        ("Meeting Notes", "Standup summaries."),
        ("Release Checklist", "Steps before every release."),
    ],
```

```python
    # alice shares the handbook with bob, view-only
    cv_document.assign_perm("view", users["bob"], docs["Team Handbook"])
    # bob shares the release checklist with alice: she may edit it, not delete it
    for action in ("view", "change"):
        cv_document.assign_perm(action, users["alice"], docs["Release Checklist"])
```

`project/features.py`, guardian `Feature`:

```python
        description="Per-object permissions: alice and bob each see their own documents, plus shared ones.",
        about=(
            "Per-object permissions with django-guardian. Documents are owned by individual users: sign in as "
            "alice or bob (password same as the username) and each sees only their own documents, plus two that "
            "are shared — alice's Team Handbook with bob, view-only, and bob's Release Checklist with alice, "
            "editable but not deletable. Creating a document grants its creator full object-level rights."
        ),
```

`docs/reference/guardian.md`, replace "This creates `alice` and `bob` demo users and assigns per-object
permissions on the seeded `Document` objects (see `guardian_demo/seed.py`)." with:

```markdown
This creates the `alice` and `bob` demo users and assigns per-object permissions on the
seeded `Document` objects (see `guardian_demo/seed.py`):

| Document          | Owner | alice                | bob                  |
|-------------------|-------|----------------------|----------------------|
| Roadmap 2027      | alice | view, change, delete | —                    |
| Team Handbook     | alice | view, change, delete | view                 |
| Meeting Notes     | bob   | —                    | view, change, delete |
| Release Checklist | bob   | view, change         | view, change, delete |
```

- [ ] **Step 4: Run the guardian and project tests**

Run: `cd examples/bootstrap5 && ../../.venv/bin/python -m pytest guardian_demo project -q`
Expected: all pass, including the existing `GuardianSeedTest` (seed idempotency, handbook share).

- [ ] **Step 5: Commit**

```bash
git add examples/bootstrap5/guardian_demo examples/bootstrap5/project/features.py docs/reference/guardian.md
git commit -m "feat(examples): guardian seed shares an editable document with alice"
```

---

### Task 3: Per-IP write rate-limit middleware

**Files:**
- Create: `requirements/demo.txt`
- Create: `examples/bootstrap5/project/ratelimit.py`
- Create: `examples/bootstrap5/project/templates/project/429.html`
- Modify: `noxfile.py:27` (examples session also installs `requirements/demo.txt`)
- Modify: `taskfile.yaml:25` (dev install also installs `requirements/demo.txt`)
- Test: `examples/bootstrap5/project/test_ratelimit.py`

**Interfaces:**
- Produces:
  - `project.ratelimit.client_ip(request: HttpRequest) -> str`
  - `project.ratelimit.WriteRateLimitMiddleware` (standard Django middleware callable)
  - reads `settings.DEMO_WRITE_RATES: tuple[str, ...]`; responds 429 with template `project/429.html`

- [ ] **Step 1: Add the demo requirements and install them**

`requirements/demo.txt`:

```text
# Deploy-only dependencies of the public demo (render.yaml). Not part of the package.
gunicorn>=23
whitenoise>=6.9
django-ratelimit>=4.1
```

`noxfile.py`, examples session:

```python
    session.install(".[all,test,examples]", "-r", "requirements/demo.txt")
```

`taskfile.yaml`, `dev-install`:

```yaml
      - uv pip install --upgrade .[all,dev,test,examples] -r requirements/demo.txt
```

Run: `uv pip install -p .venv/bin/python -r requirements/demo.txt` (from the repo root; unset `VIRTUAL_ENV` first
if it points at another checkout: `env -u VIRTUAL_ENV uv pip install ...`)
Expected: installs gunicorn, whitenoise, django-ratelimit.

- [ ] **Step 2: Write the failing tests**

`examples/bootstrap5/project/test_ratelimit.py`:

```python
from unittest import mock

from django.core.cache import cache
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from project.ratelimit import client_ip
from project.settings import MIDDLEWARE as BASE_MIDDLEWARE

RATELIMITED_MIDDLEWARE = [*BASE_MIDDLEWARE, "project.ratelimit.WriteRateLimitMiddleware"]
FIXED_NOW = 1_700_000_000  # pin django-ratelimit's window so a test never straddles a minute boundary


class ClientIpTest(SimpleTestCase):
    def test_prefers_true_client_ip(self):
        request = RequestFactory().get("/", HTTP_TRUE_CLIENT_IP="203.0.113.7", REMOTE_ADDR="10.0.0.1")
        self.assertEqual(client_ip(request), "203.0.113.7")

    def test_falls_back_to_remote_addr(self):
        request = RequestFactory().get("/", REMOTE_ADDR="198.51.100.2")
        self.assertEqual(client_ip(request), "198.51.100.2")

    def test_ignores_x_forwarded_for(self):
        request = RequestFactory().get("/", HTTP_X_FORWARDED_FOR="1.2.3.4", REMOTE_ADDR="198.51.100.2")
        self.assertEqual(client_ip(request), "198.51.100.2")


@override_settings(MIDDLEWARE=RATELIMITED_MIDDLEWARE, DEMO_WRITE_RATES=("30/m", "300/d"))
@mock.patch("django_ratelimit.core.time.time", return_value=FIXED_NOW)
class WriteRateLimitTest(TestCase):
    def setUp(self):
        cache.clear()
        self.url = reverse("login")

    def post(self, ip, **extra):
        return self.client.post(self.url, {"username": "x", "password": "y"}, HTTP_TRUE_CLIENT_IP=ip, **extra)

    def test_31st_write_in_a_minute_is_429(self, _time):
        for i in range(30):
            self.assertEqual(self.post("203.0.113.7").status_code, 200, f"write {i + 1}")
        resp = self.post("203.0.113.7")
        self.assertEqual(resp.status_code, 429)
        self.assertContains(resp, "Too many changes", status_code=429)

    def test_get_is_never_limited(self, _time):
        for _ in range(31):
            self.post("203.0.113.7")
        self.assertEqual(self.client.get(self.url, HTTP_TRUE_CLIENT_IP="203.0.113.7").status_code, 200)

    def test_other_client_ip_is_unaffected(self, _time):
        for _ in range(31):
            self.post("203.0.113.7")
        self.assertEqual(self.post("203.0.113.8").status_code, 200)

    def test_rotating_x_forwarded_for_does_not_escape_the_limit(self, _time):
        for i in range(30):
            self.post("203.0.113.7", HTTP_X_FORWARDED_FOR=f"10.9.9.{i}")
        self.assertEqual(self.post("203.0.113.7", HTTP_X_FORWARDED_FOR="10.9.9.250").status_code, 429)

    @override_settings(DEMO_WRITE_RATES=("1000/m", "5/d"))
    def test_daily_limit_applies(self, _time):
        for _ in range(5):
            self.assertEqual(self.post("203.0.113.7").status_code, 200)
        self.assertEqual(self.post("203.0.113.7").status_code, 429)
```

- [ ] **Step 3: Run them and confirm they fail**

Run: `cd examples/bootstrap5 && ../../.venv/bin/python -m pytest project/test_ratelimit.py -v`
Expected: collection error, `ModuleNotFoundError: No module named 'project.ratelimit'`.

- [ ] **Step 4: Implement**

`examples/bootstrap5/project/ratelimit.py`:

```python
"""Per-client-IP rate limit on writes for the public demo. Installed by ``settings_demo`` only."""

from django.conf import settings
from django.http import HttpRequest
from django.shortcuts import render
from django_ratelimit.core import is_ratelimited

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def client_ip(request: HttpRequest) -> str:
    """The visitor's IP address.

    On Render, Cloudflare and Render's proxy both append to X-Forwarded-For: its left entries are client-controlled
    and its right entry is an internal address shared by every visitor. Render sets True-Client-IP to the real
    client address and overwrites a client-sent one. REMOTE_ADDR covers local runs and tests.
    """
    return request.META.get("HTTP_TRUE_CLIENT_IP") or request.META.get("REMOTE_ADDR", "")


def _key(group, request):
    return client_ip(request)


class WriteRateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method not in SAFE_METHODS and self._limited(request):
            return render(request, "project/429.html", status=429)
        return self.get_response(request)

    @staticmethod
    def _limited(request) -> bool:
        return any(
            is_ratelimited(request, group=f"demo-writes-{rate}", key=_key, rate=rate, increment=True)
            for rate in settings.DEMO_WRITE_RATES
        )
```

`examples/bootstrap5/project/templates/project/429.html`:

```html
{% extends "project/base.html" %}

{% block title %}Too many changes — django-crud-views examples{% endblock title %}

{% block content %}
    <div class="alert alert-warning mt-4">
        <h4 class="alert-heading">Too many changes</h4>
        <p class="mb-0">This public demo limits how often one visitor can save. Please try again in a minute.</p>
    </div>
{% endblock content %}
```

`django_ratelimit` is deliberately **not** added to `INSTALLED_APPS`: only `core.is_ratelimited` is used, and its
system check rejects the local-memory cache, which is correct here because the demo runs a single gunicorn worker
(see Task 5).

- [ ] **Step 5: Run the tests and confirm they pass**

Run: `cd examples/bootstrap5 && ../../.venv/bin/python -m pytest project/test_ratelimit.py -v`
Expected: 8 passed.

- [ ] **Step 6: Commit**

```bash
git add requirements/demo.txt noxfile.py taskfile.yaml examples/bootstrap5/project/ratelimit.py examples/bootstrap5/project/templates/project/429.html examples/bootstrap5/project/test_ratelimit.py
git commit -m "feat(examples): per-IP write rate limit for the public demo"
```

---

### Task 4: Demo settings, admin-free URLconf and reset banner

**Files:**
- Create: `examples/bootstrap5/project/settings_demo.py`
- Create: `examples/bootstrap5/project/urls_demo.py`
- Create: `examples/bootstrap5/project/context_processors.py`
- Modify: `examples/bootstrap5/project/settings.py` (add `DEMO_MODE = False` and the context processor)
- Modify: `examples/bootstrap5/project/templates/project/base.html` (banner inside `<main>`)
- Modify: `.gitignore` (add `examples/bootstrap5/staticfiles/`)
- Test: `examples/bootstrap5/project/test_demo.py`

**Interfaces:**
- Consumes: `project.ratelimit.WriteRateLimitMiddleware` (Task 3).
- Produces: settings module `project.settings_demo` (reads env `SECRET_KEY`, required, and
  `RENDER_EXTERNAL_HOSTNAME`, optional); URLconf `project.urls_demo`; template variable `demo_mode: bool`.

- [ ] **Step 1: Write the failing tests**

`examples/bootstrap5/project/test_demo.py`:

```python
import importlib
import os
import sys
from unittest import mock

from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

DEMO_ENV = {"SECRET_KEY": "test-secret", "RENDER_EXTERNAL_HOSTNAME": "demo.example.org"}


def load_demo_settings(env):
    sys.modules.pop("project.settings_demo", None)
    with mock.patch.dict(os.environ, env, clear=False):
        for name in {"SECRET_KEY", "RENDER_EXTERNAL_HOSTNAME"} - env.keys():
            os.environ.pop(name, None)
        return importlib.import_module("project.settings_demo")


class DemoSettingsTest(SimpleTestCase):
    def test_hardened_values(self):
        demo = load_demo_settings(DEMO_ENV)
        self.assertFalse(demo.DEBUG)
        self.assertEqual(demo.SECRET_KEY, "test-secret")
        self.assertEqual(demo.ALLOWED_HOSTS, ["demo.example.org"])
        self.assertEqual(demo.CSRF_TRUSTED_ORIGINS, ["https://demo.example.org"])
        self.assertTrue(demo.SESSION_COOKIE_SECURE)
        self.assertTrue(demo.CSRF_COOKIE_SECURE)
        self.assertTrue(demo.DEMO_MODE)
        self.assertEqual(demo.DEMO_WRITE_RATES, ("30/m", "300/d"))
        self.assertEqual(demo.ROOT_URLCONF, "project.urls_demo")

    def test_middleware_order(self):
        demo = load_demo_settings(DEMO_ENV)
        self.assertEqual(demo.MIDDLEWARE[0], "django.middleware.security.SecurityMiddleware")
        self.assertEqual(demo.MIDDLEWARE[1], "whitenoise.middleware.WhiteNoiseMiddleware")
        self.assertEqual(demo.MIDDLEWARE[-1], "project.ratelimit.WriteRateLimitMiddleware")

    def test_base_middleware_is_not_mutated(self):
        from project import settings as base

        load_demo_settings(DEMO_ENV)
        self.assertNotIn("whitenoise.middleware.WhiteNoiseMiddleware", base.MIDDLEWARE)
        self.assertNotIn("project.ratelimit.WriteRateLimitMiddleware", base.MIDDLEWARE)
        self.assertFalse(base.DEMO_MODE)

    def test_missing_secret_key_fails(self):
        with self.assertRaises(KeyError):
            load_demo_settings({"RENDER_EXTERNAL_HOSTNAME": "demo.example.org"})

    def test_missing_hostname_allows_no_host(self):
        demo = load_demo_settings({"SECRET_KEY": "test-secret"})
        self.assertEqual(demo.ALLOWED_HOSTS, [])
        self.assertEqual(demo.CSRF_TRUSTED_ORIGINS, [])


class DemoUrlsTest(TestCase):
    def test_admin_mounted_locally(self):
        self.assertEqual(self.client.get("/admin/").status_code, 302)  # redirect to the admin login

    @override_settings(ROOT_URLCONF="project.urls_demo")
    def test_admin_not_mounted_on_demo(self):
        self.assertEqual(self.client.get("/admin/").status_code, 404)

    @override_settings(ROOT_URLCONF="project.urls_demo")
    def test_rest_of_site_still_routed(self):
        self.assertEqual(self.client.get(reverse("login")).status_code, 200)
        self.assertEqual(self.client.get(reverse("home")).status_code, 200)


class DemoBannerTest(TestCase):
    def test_no_banner_locally(self):
        self.assertNotContains(self.client.get(reverse("home")), 'id="demo-banner"')

    @override_settings(DEMO_MODE=True)
    def test_banner_on_demo(self):
        resp = self.client.get(reverse("login"))
        self.assertContains(resp, 'id="demo-banner"')
        self.assertContains(resp, "resets daily")
```

- [ ] **Step 2: Run them and confirm they fail**

Run: `cd examples/bootstrap5 && ../../.venv/bin/python -m pytest project/test_demo.py -v`
Expected: `DemoSettingsTest` fails with `ModuleNotFoundError: project.settings_demo`; the `urls_demo` tests fail
with `ModuleNotFoundError`; `test_banner_on_demo` fails (no banner). `test_admin_mounted_locally` and
`test_no_banner_locally` already pass.

- [ ] **Step 3: Implement**

`project/settings.py`: add after `CRUD_VIEWS_BREADCRUMB_PREFIX`:

```python
# public demo (see settings_demo.py); False for local runs
DEMO_MODE = False
```

and append `"project.context_processors.demo"` to the `context_processors` list in `TEMPLATES`.

`project/context_processors.py`:

```python
from django.conf import settings


def demo(request):
    return {"demo_mode": getattr(settings, "DEMO_MODE", False)}
```

`project/urls_demo.py`:

```python
"""URLconf of the public demo: the local URLconf without the Django admin."""

from project.urls import urlpatterns as _local_urlpatterns

urlpatterns = [p for p in _local_urlpatterns if str(p.pattern) != "admin/"]
```

`project/settings_demo.py`:

```python
"""Settings for the public demo on Render (see render.yaml at the repo root).

Extends the local example settings. Requires the env var SECRET_KEY; RENDER_EXTERNAL_HOSTNAME is set by Render.
"""

import os

from project.settings import *  # noqa: F403
from project.settings import BASE_DIR, MIDDLEWARE

DEBUG = False
SECRET_KEY = os.environ["SECRET_KEY"]

_host = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "")
ALLOWED_HOSTS = [_host] if _host else []
CSRF_TRUSTED_ORIGINS = [f"https://{_host}"] if _host else []

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# new list: never mutate the imported base MIDDLEWARE
MIDDLEWARE = [
    MIDDLEWARE[0],  # SecurityMiddleware
    "whitenoise.middleware.WhiteNoiseMiddleware",
    *MIDDLEWARE[1:],
    "project.ratelimit.WriteRateLimitMiddleware",
]

STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

# single gunicorn worker → a process-local cache is enough for the rate-limit counters
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

ROOT_URLCONF = "project.urls_demo"
DEMO_MODE = True
DEMO_WRITE_RATES = ("30/m", "300/d")
```

`base.html`, inside `<main class="container">` before `{% bootstrap_messages %}`:

```html
    {% if demo_mode %}
        <div class="alert alert-warning mt-3" id="demo-banner" role="status">
            Public demo — data resets daily and after inactivity.
            Log in as <code>alice/alice</code> or <code>bob/bob</code>.
        </div>
    {% endif %}
```

`.gitignore`: add the line `examples/bootstrap5/staticfiles/`.

- [ ] **Step 4: Run the tests**

Run: `cd examples/bootstrap5 && ../../.venv/bin/python -m pytest project/test_demo.py -v`
Expected: 10 passed.

- [ ] **Step 5: Exercise the demo settings for real**

Run (from `examples/bootstrap5`, scratch DB so the dev DB is untouched):

```bash
export DJANGO_SETTINGS_MODULE=project.settings_demo SECRET_KEY=x RENDER_EXTERNAL_HOSTNAME=localhost
../../.venv/bin/python manage.py check --deploy
../../.venv/bin/python manage.py collectstatic --noinput
```

Expected: `collectstatic` succeeds (populates `staticfiles/`, ignored by git). `check --deploy` may warn about
HSTS (`security.W004`) and `SECURE_SSL_REDIRECT` (`security.W008`); both are acceptable because Render terminates
TLS and redirects to HTTPS. Any other warning or error must be fixed. Then `rm -rf staticfiles`.

- [ ] **Step 6: Run the whole example suite and commit**

Run: `cd examples/bootstrap5 && ../../.venv/bin/python -m pytest -q` → all pass.

```bash
git add .gitignore examples/bootstrap5/project
git commit -m "feat(examples): demo settings without admin, with reset banner"
```

---

### Task 5: Render blueprint and the `demo` workflow

**Files:**
- Create: `render.yaml`
- Create: `.github/workflows/demo.yml`

**Interfaces:**
- Consumes: `project.settings_demo` (Task 4), `requirements/demo.txt` (Task 3), the `seed` command.
- Produces: GitHub secrets/variables contract `RENDER_API_KEY`, `RENDER_SERVICE_ID`, `DEMO_URL` (documented in
  Task 6).

- [ ] **Step 1: Write `render.yaml`**

```yaml
# Render Blueprint for the public demo of examples/bootstrap5.
# Deploys are driven by .github/workflows/demo.yml through the Render API, never by pushes (autoDeploy: false).
# The free plan's filesystem is ephemeral: every start migrates and seeds a fresh SQLite database.
services:
  - type: web
    name: django-crud-views-demo
    runtime: python
    plan: free
    autoDeploy: false
    buildCommand: >-
      pip install ".[all,examples]" -r requirements/demo.txt &&
      cd examples/bootstrap5 && python manage.py collectstatic --noinput
    startCommand: >-
      cd examples/bootstrap5 && python manage.py migrate --noinput && python manage.py seed &&
      gunicorn project.wsgi --workers 1 --bind 0.0.0.0:$PORT
    healthCheckPath: /login/
    envVars:
      - key: DJANGO_SETTINGS_MODULE
        value: project.settings_demo
      - key: SECRET_KEY
        generateValue: true
      - key: PYTHON_VERSION
        value: "3.13"
```

- [ ] **Step 2: Write `.github/workflows/demo.yml`**

```yaml
# Public demo on Render (render.yaml). Deploys a release tag's exact commit; wipes the demo data daily.
# Needs secrets RENDER_API_KEY, RENDER_SERVICE_ID and the repository variable DEMO_URL.
name: demo

on:
  push:
    tags: ["v*"]
  workflow_dispatch:
    inputs:
      reset_only:
        description: "Only wipe the demo data (restart on the current version), do not deploy"
        type: boolean
        default: false
  schedule:
    - cron: "0 3 * * *"

concurrency:
  group: demo
  cancel-in-progress: false

permissions:
  contents: read

env:
  RENDER_API: https://api.render.com/v1

jobs:
  deploy:
    if: github.event_name == 'push' || (github.event_name == 'workflow_dispatch' && !inputs.reset_only)
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - name: Deploy this commit to Render and wait until live
        env:
          RENDER_API_KEY: ${{ secrets.RENDER_API_KEY }}
          RENDER_SERVICE_ID: ${{ secrets.RENDER_SERVICE_ID }}
        run: |
          set -euo pipefail
          auth="Authorization: Bearer $RENDER_API_KEY"
          deploy_id=$(curl -fsS -X POST "$RENDER_API/services/$RENDER_SERVICE_ID/deploys" \
            -H "$auth" -H "Content-Type: application/json" \
            -d "{\"commitId\": \"$GITHUB_SHA\"}" | jq -r '.id // empty')
          if [ -z "$deploy_id" ]; then
            echo "::error::Render returned no deploy id"; exit 1
          fi
          echo "deploy $deploy_id for $GITHUB_SHA"
          for _ in $(seq 1 100); do
            status=$(curl -fsS "$RENDER_API/services/$RENDER_SERVICE_ID/deploys/$deploy_id" -H "$auth" | jq -r .status)
            echo "status: $status"
            case "$status" in
              live) exit 0 ;;
              build_failed|update_failed|pre_deploy_failed|canceled|deactivated)
                echo "::error::deploy ended as $status"; exit 1 ;;
            esac
            sleep 10
          done
          echo "::error::deploy not live after ~17 minutes"; exit 1

  reset:
    if: github.event_name == 'schedule' || (github.event_name == 'workflow_dispatch' && inputs.reset_only)
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - name: Restart the service (fresh filesystem, fresh database)
        env:
          RENDER_API_KEY: ${{ secrets.RENDER_API_KEY }}
          RENDER_SERVICE_ID: ${{ secrets.RENDER_SERVICE_ID }}
        run: |
          set -euo pipefail
          curl -fsS -X POST "$RENDER_API/services/$RENDER_SERVICE_ID/restart" \
            -H "Authorization: Bearer $RENDER_API_KEY"
          echo "restart requested"

  smoke:
    needs: [deploy, reset]
    if: always() && (needs.deploy.result == 'success' || needs.reset.result == 'success')
    runs-on: ubuntu-latest
    timeout-minutes: 10
    env:
      DEMO_URL: ${{ vars.DEMO_URL }}
    steps:
      - name: Login page answers, admin is not mounted
        run: |
          set -uo pipefail
          code=000
          for _ in $(seq 1 18); do  # a free instance may need ~1 minute to wake up
            code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 90 "$DEMO_URL/login/")
            [ "$code" = 200 ] && break
            sleep 10
          done
          [ "$code" = 200 ] || { echo "::error::/login/ returned $code"; exit 1; }
          admin=$(curl -s -o /dev/null -w '%{http_code}' --max-time 30 "$DEMO_URL/admin/")
          [ "$admin" = 404 ] || { echo "::error::/admin/ returned $admin, expected 404"; exit 1; }
          echo "demo OK"
```

- [ ] **Step 3: Validate both files**

Run: `python3 -c "import yaml; yaml.safe_load(open('render.yaml')); yaml.safe_load(open('.github/workflows/demo.yml'))"`
Expected: no output.

Run: `uvx --from actionlint-py actionlint .github/workflows/demo.yml`
Expected: no findings. (actionlint runs shellcheck on the `run:` blocks when shellcheck is installed. Fix any
finding it reports.)

- [ ] **Step 4: Rehearse the start command locally**

The demo settings use `examples/bootstrap5/db.sqlite3`, the dev database, so back it up first. From
`examples/bootstrap5`:

```bash
cp db.sqlite3 /tmp/db.sqlite3.bak
export DJANGO_SETTINGS_MODULE=project.settings_demo SECRET_KEY=x RENDER_EXTERNAL_HOSTNAME=localhost
../../.venv/bin/python manage.py collectstatic --noinput
../../.venv/bin/python manage.py migrate --noinput && ../../.venv/bin/python manage.py seed
../../.venv/bin/gunicorn project.wsgi --workers 1 --bind 127.0.0.1:8765 &
../../.venv/bin/python ../../scripts/wait_for_server.py http://localhost:8765/login/ 60
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8765/admin/            # expect 404
curl -s http://localhost:8765/login/ | grep -c 'id="demo-banner"'                 # expect 1
curl -s -o /dev/null -w '%{http_code}\n' "http://localhost:8765$(curl -s http://localhost:8765/login/ | grep -o '/static/[^\"]*\.css' | head -1)"  # expect 200
kill %1
unset DJANGO_SETTINGS_MODULE SECRET_KEY RENDER_EXTERNAL_HOSTNAME
rm -rf staticfiles && cp /tmp/db.sqlite3.bak db.sqlite3
```

Expected: `/admin/` 404, banner present, a hashed static CSS file served with 200 (whitenoise works with
`DEBUG=False`). If `wait_for_server.py` times out, read gunicorn's output: a 500 here usually means a missing
static file in the manifest.

- [ ] **Step 5: Commit**

```bash
git add render.yaml .github/workflows/demo.yml
git commit -m "ci(demo): Render blueprint and deploy/reset workflow"
```

---

### Task 6: Documentation and changelog

**Files:**
- Create: `docs/getting_started/demo.md`
- Modify: `docs/getting_started/.pages` (add the page after `index.md`)
- Modify: `docs/development/index.md` (new section "Deploying the demo", after "Run example application")
- Modify: `README.md` (one line before `## Run the example project`)
- Modify: `CHANGELOG.md` (new `## Unreleased` section at the top)

**Interfaces:**
- Consumes: the demo URL `https://django-crud-views-demo.onrender.com/` (assumed from the service name; Task 7
  corrects it if Render assigns a different hostname).

- [ ] **Step 1: Write `docs/getting_started/demo.md`**

```markdown
# Live demo

The example project runs as a public demo at
**[django-crud-views-demo.onrender.com](https://django-crud-views-demo.onrender.com/)**.

Log in as `alice` / `alice` or `bob` / `bob`. Both have full model permissions in every example. They differ in
the **Guardian** example, which uses per-object permissions: each sees their own documents plus the ones the other
shared with them.

Things to know:

- **The data resets.** Every day at 03:00 UTC, and whenever the demo has been idle for about 15 minutes, it starts
  again from freshly seeded data. Feel free to change and delete things.
- **The first request after a pause can take about a minute** while the free instance wakes up.
- **Saving is rate-limited** to 30 changes per minute and 300 per day per visitor.
- **The Django admin is not available** on the demo.

The demo always runs the latest release. To run the same project on your machine, see
[Run the finished result first](index.md#or-run-the-finished-result-first).
```

`docs/getting_started/.pages`:

```yaml
nav:
    - index.md
    - Live demo: demo.md
    - Part 1 — Setup & first ViewSet: tutorial-1-setup.md
```

(The remaining entries stay unchanged.)

- [ ] **Step 2: Add "Deploying the demo" to `docs/development/index.md`**

Insert after the "Run example application" section (before "## Claude Code skill"):

```markdown
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
```

- [ ] **Step 3: README line**

Directly before `## Run the example project`:

```markdown
**Try it online:** the [live demo](https://django-crud-views-demo.onrender.com/) runs the example project (log in as `alice` / `alice` or `bob` / `bob`; data resets daily).

```

(This sits outside the "Run the example project" section, so `readme-examples.yml` does not need to change.)

- [ ] **Step 4: CHANGELOG**

Insert after the title line:

```markdown
## Unreleased

### Added

- Public demo of the example project on Render's free plan (`render.yaml`, `.github/workflows/demo.yml`):
  deployed on release tags or manually, data wiped daily. Demo-only settings `project.settings_demo` disable the
  admin, show a reset banner and rate-limit writes per client IP. See the docs, *Live demo* and
  *Deploying the demo*.

### Changed

- Example project: the seeded users are `alice/alice` and `bob/bob` only; the `admin/admin` superuser is gone
  (use `manage.py createsuperuser` for the Django admin). The Guardian example also shares an editable document
  with alice.

```

- [ ] **Step 5: Build the docs and run the example suite**

Run: `.venv/bin/mkdocs build --strict -q` (from the repo root)
Expected: builds without warnings (the `index.md#or-run-the-finished-result-first` anchor resolves).

Run: `cd examples/bootstrap5 && ../../.venv/bin/python -m pytest -q` → all pass (docs sync).

- [ ] **Step 6: Commit**

```bash
git add docs README.md CHANGELOG.md
git commit -m "docs: live demo page, demo deployment guide, changelog"
```

---

### Task 7: Push, PR, and live verification (needs the user)

**Files:** possibly `docs/getting_started/demo.md`, `README.md`, `docs/development/index.md` (URL correction only).

- [ ] **Step 1: Push and open the PR; wait for CI**

```bash
git push -u origin feature/render-demo-deploy
gh pr create --title "Public demo of the example project on Render" --body "<summary of tasks 1-6, link to spec>"
```

Wait for all checks, including `codecov/patch` (`gh pr checks` omits it; query the check-runs API). Fix ruff or
test failures on the branch. **Do not merge**: merging needs the user's explicit request.

- [ ] **Step 2: Hand the one-time Render setup to the user**

The user does the setup in "Deploying the demo" (Task 6 Step 2). The blueprint must point at the PR branch for the
first rehearsal, or at `main` after merging. Ask the user which.

- [ ] **Step 3: First deploy and checks (once the user has finished the setup)**

- Trigger: `gh workflow run demo.yml --ref feature/render-demo-deploy` (the workflow file only exists on the
  branch until merged). Watch it with `gh run watch`. Expected: deploy `live`, smoke test green.
- If Render's hostname differs from `django-crud-views-demo.onrender.com`, correct the URL in
  `docs/getting_started/demo.md`, `README.md` and `docs/development/index.md`, and commit.
- **Client-IP check:** log in, then submit ~31 failing login attempts in quick succession from one browser. Expect
  the 429 page on the 31st. From a second network (e.g. phone off Wi-Fi), the login must still work. If the 429 hits
  everyone, `True-Client-IP` is not being set: stop and report back. Do not switch to `X-Forwarded-For`.
- **Reset check:** `gh workflow run demo.yml --ref feature/render-demo-deploy -f reset_only=true`, then create a
  document as alice beforehand and confirm it is gone afterwards.
