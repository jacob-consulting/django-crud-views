# Context Actions Must Not 500 on Unregistered View Keys Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A ViewSet that registers only some CRUD views (e.g. list + detail) must render its list/detail/update pages without raising `ViewSetKeyFoundError`, including in development (`DEBUG=True`).

**Architecture:** The default `*_CONTEXT_ACTIONS` settings reference view keys (`create`, `delete`, `update`) that a ViewSet may legitimately not register. The base template renders context actions via `{% cv_context_actions object %}` → the `cv_context_actions` inclusion tag → `tags/context_actions.html`, which loops `cv_context_actions` and resolves each key through `cv_get_context` → `get_view_class`, raising on an unregistered key. The fix routes the toolbar through `CrudView.cv_get_context_buttons`, adds an unregistered-key guard there, and renders the resolved list with the existing `{% cv_render_context_button %}` tag. Strict-mode raising is preserved for direct `cv_context_action` calls.

**Tech Stack:** Django, pytest / pytest-django, django-crud-views (src layout).

## Global Constraints

- Line length 120, double quotes, ruff format/check must pass (`task format`, `task check`).
- `cv_` prefix on all CrudView attributes; existing tag/method names unchanged.
- Tests run from `tests/` with `pytest`; settings have `DEBUG=True` (so `CRUD_VIEWS_STRICT` defaults on).
- Single PR → CI → fix ruff → squash-merge to `main` → wait main CI; then bump `0.8.0`→`0.8.1`.
- Both themes must stay in sync: `crud_views` and `crud_views_plain` ship parallel copies of `tags/context_actions.html`.

---

### Task 1: Guard `cv_get_context_buttons` against unregistered keys + reroute the toolbar template

**Files:**
- Modify: `src/crud_views/lib/view/base.py` — `cv_get_context_buttons` (~line 321)
- Modify: `src/crud_views/templatetags/crud_views.py` — `cv_context_actions` inclusion tag (~line 116)
- Modify: `src/crud_views/templates/crud_views/tags/context_actions.html`
- Modify: `src/crud_views_plain/templates/crud_views/tags/context_actions.html`
- Test: `tests/test1/test_context_action_unregistered_key.py` (create)

**Interfaces:**
- Consumes (existing, unchanged signatures):
  - `CrudView.cv_get_context_button(key: str) -> ContextButton | None` (`base.py:311`)
  - `ViewSet.is_view_registered(key: str) -> bool` (`viewset/__init__.py:257`)
  - `CrudView.cv_get_context(key, obj, user, request) -> dict` (`base.py:346`)
  - tag `cv_render_context_button(context, ctx) -> str` (`crud_views.py:110`)
- Produces:
  - `cv_get_context_buttons` now silently skips keys that are neither a context button nor a registered view (never raises `ViewSetKeyFoundError` for them).
  - `cv_context_actions` inclusion-tag context dict gains `context_buttons: list[dict]` (resolved, access-filtered).

- [ ] **Step 1: Write the failing test**

Create `tests/test1/test_context_action_unregistered_key.py`:

```python
"""Regression: a list+detail-only ViewSet (cv_contract) must not 500 on its own
pages because the default *_CONTEXT_ACTIONS reference unregistered create/delete
view keys. DEBUG=True in the test settings, so CRUD_VIEWS_STRICT is on by default."""

import pytest
from django.urls import reverse

from tests.lib.helper.user import user_viewset_permission


@pytest.fixture
def cv_contract():
    from tests.test1.app.views import cv_contract as ret

    return ret


@pytest.fixture
def client_user_contract_view(client, cv_contract):
    from django.contrib.auth.models import User

    user = User.objects.create_user(username="user_contract_view", password="password")
    user_viewset_permission(user, cv_contract, "view")
    client.force_login(user)
    return client


@pytest.mark.django_db
def test_contract_list_renders_without_create_view(
    client_user_contract_view, cv_contract, publisher_penguin
):
    # cv_contract registers only list + detail; default list_context_actions
    # includes "create" (not a registered view). Must render, not raise.
    url = reverse(cv_contract.get_router_name("list"), kwargs={"publisher_pk": publisher_penguin.pk})
    resp = client_user_contract_view.get(url)
    assert resp.status_code == 200
    # the unregistered create button is simply absent
    assert b'cv-key="create"' not in resp.content


@pytest.mark.django_db
def test_contract_detail_renders_without_update_delete_views(
    client_user_contract_view, cv_contract, publisher_penguin
):
    from tests.test1.app.models import Contract

    contract = Contract.objects.create(publisher=publisher_penguin, title="ACME")
    url = reverse(
        cv_contract.get_router_name("detail"),
        kwargs={"publisher_pk": publisher_penguin.pk, "pk": contract.pk},
    )
    resp = client_user_contract_view.get(url)
    assert resp.status_code == 200
    assert b'cv-key="update"' not in resp.content
    assert b'cv-key="delete"' not in resp.content


@pytest.mark.django_db
def test_get_context_buttons_skips_unregistered_keys(
    client_user_contract_view, cv_contract, publisher_penguin
):
    url = reverse(cv_contract.get_router_name("list"), kwargs={"publisher_pk": publisher_penguin.pk})
    resp = client_user_contract_view.get(url)
    view = resp.context["view"]
    # explicit mix of unregistered ("create") and registered ("list") keys
    keys = [b.get("cv_key") for b in view.cv_get_context_buttons(keys=["create", "list"])]
    assert "create" not in keys
    assert "list" in keys
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd tests && pytest test1/test_context_action_unregistered_key.py -v`
Expected: FAIL — `test_contract_list_renders_*` and `test_contract_detail_renders_*` error with `crud_views.lib.exceptions.ViewSetKeyFoundError: key create not registered ...` (the test client re-raises). `test_get_context_buttons_skips_unregistered_keys` cannot reach its assertions because the GET that obtains the view raises.

- [ ] **Step 3: Add the unregistered-key guard in `cv_get_context_buttons`**

In `src/crud_views/lib/view/base.py`, the loop in `cv_get_context_buttons` (currently starts ~line 330):

```python
        result: list[dict] = []
        for key in keys:
            # an unregistered view key that is also not a context button is not a
            # misconfiguration here — default context-action lists legitimately
            # reference optional views (create/delete) a ViewSet may not register.
            if self.cv_get_context_button(key) is None and not self.cv_viewset.is_view_registered(key):
                continue
            ctx = self.cv_get_context(key=key, obj=obj, user=self.request.user, request=self.request)
            if not ctx or ctx.get("cv_action_enabled") is False or ctx.get("cv_access") is not True:
                continue
            result.append(ctx)
        return result
```

(Only the `if self.cv_get_context_button(...) ...: continue` line is new; the rest is unchanged.)

- [ ] **Step 4: Reroute the inclusion tag through the filtered list**

In `src/crud_views/templatetags/crud_views.py`, replace the `cv_context_actions` inclusion tag body (~line 116):

```python
@register.inclusion_tag(f"{crud_views_settings.theme_path}/tags/context_actions.html", takes_context=True)
def cv_context_actions(context, obj=None):
    view: CrudView = cv_get_view(context)
    buttons = view.cv_get_context_buttons(obj=obj)
    return {"view": view, "request": context["request"], "object": obj, "context_buttons": buttons}
```

- [ ] **Step 5: Update both `context_actions.html` templates to render the resolved list**

`src/crud_views/templates/crud_views/tags/context_actions.html`:

```html
{% load crud_views %}

{% if context_buttons %}

    <div class="btn-group btn-group-lg" role="group" aria-label="Actions" cv-context-container="true">
        {% for ctx in context_buttons %}
            {% cv_render_context_button ctx %}
        {% endfor %}
    </div>

{% endif %}
```

`src/crud_views_plain/templates/crud_views/tags/context_actions.html`:

```html
{% load crud_views %}

{% if context_buttons %}
    {% for ctx in context_buttons %}
        {% cv_render_context_button ctx %}
    {% endfor %}
    <br>
{% endif %}
```

- [ ] **Step 6: Run the new test to verify it passes**

Run: `cd tests && pytest test1/test_context_action_unregistered_key.py -v`
Expected: PASS (3 tests).

- [ ] **Step 7: Run the full suite to confirm no regressions**

Run: `cd tests && pytest -q`
Expected: all green (existing context-button tests still pass — accessible registered keys render identical markup via `cv_render_context_button`).

- [ ] **Step 8: Lint**

Run: `task format && task check`
Expected: no changes / no errors.

- [ ] **Step 9: Commit**

```bash
git add src/crud_views/lib/view/base.py \
        src/crud_views/templatetags/crud_views.py \
        src/crud_views/templates/crud_views/tags/context_actions.html \
        src/crud_views_plain/templates/crud_views/tags/context_actions.html \
        tests/test1/test_context_action_unregistered_key.py
git commit -m "fix: context actions no longer 500 on unregistered view keys (strict/DEBUG)"
```

---

### Task 2: Lock the strict-mode boundary for direct `cv_context_action` calls

**Files:**
- Test: `tests/test1/test_context_action_unregistered_key.py` (append)

**Interfaces:**
- Consumes: tag `cv_context_action(context, key, obj=None)` (`crud_views.py:74`, unchanged) — still raises `ViewSetKeyFoundError` for an unknown key under strict mode.

This task guards against a future over-broad "fix" that suppresses errors in `cv_context_action` itself. The toolbar no longer calls it, but it remains a public tag whose strict-mode contract (fail loud on a genuinely bad key) must hold.

- [ ] **Step 1: Write the test**

Append to `tests/test1/test_context_action_unregistered_key.py`:

```python
from django.template import Context, Template

from crud_views.lib.exceptions import ViewSetKeyFoundError


@pytest.mark.django_db
def test_direct_cv_context_action_still_raises_on_unknown_key_in_strict(
    client_user_contract_view, cv_contract, publisher_penguin
):
    # DEBUG=True -> CRUD_VIEWS_STRICT on. A direct {% cv_context_action %} with a
    # key that is neither a context button nor a registered view still fails loud.
    url = reverse(cv_contract.get_router_name("list"), kwargs={"publisher_pk": publisher_penguin.pk})
    resp = client_user_contract_view.get(url)
    view = resp.context["view"]
    tpl = Template("{% load crud_views %}{% cv_context_action 'frobnicate' %}")
    with pytest.raises(ViewSetKeyFoundError):
        tpl.render(Context({"view": view, "request": resp.context["request"]}))
```

- [ ] **Step 2: Run the test to verify it passes**

Run: `cd tests && pytest test1/test_context_action_unregistered_key.py::test_direct_cv_context_action_still_raises_on_unknown_key_in_strict -v`
Expected: PASS (behavior unchanged by Task 1; this locks it).

- [ ] **Step 3: Commit**

```bash
git add tests/test1/test_context_action_unregistered_key.py
git commit -m "test: lock strict-mode raise for direct cv_context_action on unknown key"
```

---

### Task 3: Changelog entry

**Files:**
- Modify: `CHANGELOG.md` (or `docs/` changelog source — match the file the project actually promotes on release)

**Interfaces:** none.

- [ ] **Step 1: Locate the changelog and its Unreleased section**

Run: `ls CHANGELOG.md docs/changelog.md 2>/dev/null; grep -rn "Unreleased\|## \[" CHANGELOG.md docs/*.md 2>/dev/null | head`
Expected: identify the file with an `Unreleased` / top section (the one promoted in prior release commits, e.g. `49062fb`).

- [ ] **Step 2: Add the entry under Unreleased (Fixed)**

Add a line such as:

```markdown
### Fixed

- Context actions no longer raise `ViewSetKeyFoundError` (HTTP 500 in `DEBUG`) when a
  ViewSet omits a view referenced by the default `*_CONTEXT_ACTIONS` (e.g. a list+detail-only
  ViewSet and the default `create`/`delete` keys). Unregistered keys are now skipped; strict
  mode still fails loud for explicit `{% cv_context_action %}` calls with unknown keys.
```

- [ ] **Step 3: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs(changelog): note context-action unregistered-key fix"
```

---

## Self-Review

**Spec coverage:**
- Root-cause fix (skip unregistered keys, in all modes for the toolbar path) → Task 1 (guard + reroute). ✓
- Both theme templates updated → Task 1 Step 5. ✓
- `cv_get_context_buttons` "access-filtered" promise honored for default lists → Task 1 (guard before access filter). ✓
- TDD RED = list+detail-only ViewSet renders 200 under DEBUG/strict → Task 1 Steps 1–2 (`cv_contract`). ✓
- Detail/update variant (delete/update keys) → Task 1 `test_contract_detail_renders_*`. ✓
- Unregistered key omitted; registered key still renders → Task 1 `test_get_context_buttons_skips_unregistered_keys`. ✓
- Strict still strict for genuine errors → Task 2. ✓
- Access filtering unchanged → covered by existing `test_context_button_loop.py` (full suite, Task 1 Step 7). ✓
- Single PR + 0.8.1 release → out of plan scope (handled at handoff/merge); changelog prepared in Task 3. ✓

**Placeholder scan:** none — all code/commands concrete. CHANGELOG path is the one explicitly-discovered ambiguity; Task 3 Step 1 resolves it before editing.

**Type consistency:** `cv_get_context_buttons` returns `list[dict]`; entries carry `cv_key` (asserted in tests and produced by `cv_get_dict`), `cv_access`, `cv_action_enabled`. The inclusion tag adds `context_buttons` consumed by both templates. `is_view_registered`/`cv_get_context_button` signatures match their definitions. Consistent.
