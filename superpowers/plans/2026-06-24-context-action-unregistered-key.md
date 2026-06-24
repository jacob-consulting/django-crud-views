# Unify Action Rendering (skip unregistered keys, drop greyed buttons) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A ViewSet that omits some CRUD views must render its pages without raising `ViewSetKeyFoundError` (incl. `DEBUG=True`), and inaccessible actions must be hidden rather than greyed-out — consistently across the context-action toolbar and list-row actions.

**Architecture:** One resolver change — `CrudView.cv_get_context` returns `{}` for an unregistered key instead of raising — fixes every render path at the source (toolbar, list rows, list-row forms, context buttons, button loop). Render templates then hide inaccessible/disabled actions (drop the greyed `{% else %}` branches). `get_view_class` keeps raising (URL routing depends on it).

**Tech Stack:** Django, pytest / pytest-django, django-crud-views (`src/` layout), two template themes (`crud_views`, `crud_views_plain`).

## Global Constraints

- Line length 120, double quotes; `task format` and `task check` must pass.
- `cv_` prefix on CrudView attributes; public tag names unchanged.
- Tests run from `tests/`: `cd tests && pytest`. Django's test runner forces `DEBUG=False`, so `CRUD_VIEWS_STRICT` defaults **off** in tests — any test reproducing the dev-time bug MUST force `CRUD_VIEWS_STRICT=True` (monkeypatch).
- Keep both themes in sync: `crud_views` and `crud_views_plain` each have `tags/context_action.html` and `tags/list_action.html`; only `crud_views` has `tags/list_action_form.html`.
- Branch `fix/context-action-unregistered-key-strict` already holds commit `6bef1a5` (a `cv_get_context_buttons` guard + a test file). Task 1 supersedes that guard.

---

### Task 1: Central resolver skip — fix the unregistered-key 500

**Files:**
- Modify: `src/crud_views/lib/view/base.py` — `cv_get_context` (~line 376) and `cv_get_context_buttons` (~line 330)
- Modify: `src/crud_views/templatetags/crud_views.py` — `cv_context_action` (~line 77)
- Modify: `tests/test1/test_context_action_unregistered_key.py` (exists from `6bef1a5`)

**Interfaces:**
- Consumes: `ViewSet.is_view_registered`, `cv_get_cls_assert_object`, `ViewSetKeyFoundError` (`crud_views.lib.exceptions`).
- Produces: `cv_get_context(key, …)` returns `{}` for an unregistered, non-button key (never raises `ViewSetKeyFoundError`). All five tags and `cv_get_context_buttons` therefore skip such keys.

- [ ] **Step 1: Add the failing strict-mode page test**

Replace the body of `tests/test1/test_context_action_unregistered_key.py` with (keeps the existing fixtures + unit test, adds the real RED integration test):

```python
"""Regression: a list+detail-only ViewSet (cv_contract) must not raise
ViewSetKeyFoundError on its own pages because the default *_CONTEXT_ACTIONS
reference unregistered create/delete view keys. The bug only bites under strict
mode (CRUD_VIEWS_STRICT, which defaults to DEBUG); tests run DEBUG=False, so the
integration test forces strict mode to reproduce it."""

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


@pytest.fixture
def strict_mode(monkeypatch):
    from django.conf import settings as dj_settings

    monkeypatch.setattr(dj_settings, "CRUD_VIEWS_STRICT", True, raising=False)


@pytest.mark.django_db
def test_pages_render_with_unregistered_default_keys_in_strict(
    strict_mode, client_user_contract_view, cv_contract, publisher_penguin
):
    # list: default list_context_actions includes "create" (not registered on cv_contract)
    list_url = reverse(cv_contract.get_router_name("list"), kwargs={"publisher_pk": publisher_penguin.pk})
    resp = client_user_contract_view.get(list_url)
    assert resp.status_code == 200
    assert b'cv-key="create"' not in resp.content

    # detail: default detail_context_actions includes "update"/"delete" (not registered)
    from tests.test1.app.models import Contract

    contract = Contract.objects.create(publisher=publisher_penguin, title="ACME")
    detail_url = reverse(
        cv_contract.get_router_name("detail"),
        kwargs={"publisher_pk": publisher_penguin.pk, "pk": contract.pk},
    )
    resp = client_user_contract_view.get(detail_url)
    assert resp.status_code == 200
    assert b'cv-key="update"' not in resp.content
    assert b'cv-key="delete"' not in resp.content


@pytest.mark.django_db
def test_get_context_buttons_skips_unregistered_keys(client_user_contract_view, cv_contract, publisher_penguin):
    url = reverse(cv_contract.get_router_name("list"), kwargs={"publisher_pk": publisher_penguin.pk})
    resp = client_user_contract_view.get(url)
    view = resp.context["view"]
    keys = [b.get("cv_key") for b in view.cv_get_context_buttons(keys=["create", "list"])]
    assert "create" not in keys
    assert "list" in keys
```

- [ ] **Step 2: Run the tests; confirm the strict test fails for the right reason**

Run: `cd tests && pytest test1/test_context_action_unregistered_key.py -v`
Expected: `test_pages_render_with_unregistered_default_keys_in_strict` FAILS with `crud_views.lib.exceptions.ViewSetKeyFoundError: key create not registered ...` (toolbar renders via `cv_context_action`, which re-raises under forced strict). `test_get_context_buttons_skips_unregistered_keys` passes (the `6bef1a5` guard is still present at this point).

- [ ] **Step 3: Soften `cv_get_context` to skip unregistered keys**

In `src/crud_views/lib/view/base.py`, ensure `ViewSetKeyFoundError` is imported from `crud_views.lib.exceptions` (add to the existing exceptions import if absent). Replace the single resolution line in `cv_get_context`:

```python
        # get target view class
        cls = self.cv_get_cls_assert_object(key, obj)
```

with:

```python
        # get target view class; an unregistered key is not a misconfiguration here -> skip
        try:
            cls = self.cv_get_cls_assert_object(key, obj)
        except ViewSetKeyFoundError:
            return {}
```

- [ ] **Step 4: Remove the now-redundant guard in `cv_get_context_buttons`**

In the `cv_get_context_buttons` loop, delete the three lines added in `6bef1a5`:

```python
            if self.cv_get_context_button(key) is None and not self.cv_viewset.is_view_registered(key):
                continue
```

(and their comment). The remaining `if not ctx or … continue` now skips unregistered keys because `cv_get_context` returns `{}`.

- [ ] **Step 5: Short-circuit empty context in `cv_context_action`**

In `src/crud_views/templatetags/crud_views.py`, in `cv_context_action`, after `ctx = cv_get_context(context=context, key=key, obj=obj)` add:

```python
    if not ctx:
        return ""
```

- [ ] **Step 6: Run the new tests; confirm pass**

Run: `cd tests && pytest test1/test_context_action_unregistered_key.py -v`
Expected: 2 passed.

- [ ] **Step 7: Run the full suite (greyed buttons still present — existing tests unaffected)**

Run: `cd tests && pytest -q`
Expected: all green (templates untouched in this task, so greyed-button tests still pass).

- [ ] **Step 8: Lint**

Run: `task format && task check`
Expected: clean.

- [ ] **Step 9: Commit**

```bash
git add src/crud_views/lib/view/base.py src/crud_views/templatetags/crud_views.py \
        tests/test1/test_context_action_unregistered_key.py
git commit -m "fix: skip unregistered keys in cv_get_context (no 500 on partial ViewSets)"
```

---

### Task 2: Drop greyed-out rendering — hide inaccessible actions (toolbar + rows, both themes)

**Files:**
- Modify: `src/crud_views/templates/crud_views/tags/context_action.html`
- Modify: `src/crud_views_plain/templates/crud_views/tags/context_action.html`
- Modify: `src/crud_views/templates/crud_views/tags/list_action.html`
- Modify: `src/crud_views_plain/templates/crud_views/tags/list_action.html`
- Modify: `src/crud_views/templates/crud_views/tags/list_action_form.html`
- Modify: `tests/test1/test_context_action_unregistered_key.py` (add hidden-action test)
- Modify: `tests/test1/test_permissions.py` (`test_author_view`)
- Possibly modify: `tests/test1/test_workflow.py`, `tests/test1/test_filter_pinned.py`, `tests/lib/helper/boostrap5.py`

**Interfaces:**
- Consumes: resolved context dicts carrying `cv_access`, `cv_action_enabled`, `cv_key`, `cv_url`.
- Produces: inaccessible/disabled actions emit no markup on either surface.

- [ ] **Step 1: Add the failing hidden-action test**

Append to `tests/test1/test_context_action_unregistered_key.py`:

```python
@pytest.mark.django_db
def test_inaccessible_actions_are_hidden(client_user_author_view, cv_author, author_douglas_adams):
    # view-only user: create (toolbar) and update/delete (rows) must be ABSENT, not greyed/disabled
    resp = client_user_author_view.get("/author/")
    assert resp.status_code == 200
    # create (toolbar) + update/delete (rows) are registered but inaccessible for this user:
    # on main they render as greyed/disabled buttons WITH a cv-key; hidden -> the cv-key is gone.
    assert b'cv-key="create"' not in resp.content
    assert b'cv-key="update"' not in resp.content
    assert b'cv-key="delete"' not in resp.content
```

(Do NOT assert `b"disabled" not in resp.content` — pagination markup uses `disabled` and would false-positive. The `cv-key` absence is the precise hidden-vs-greyed signal.)

Run: `cd tests && pytest test1/test_context_action_unregistered_key.py::test_inaccessible_actions_are_hidden -v`
Expected: FAIL — `cv-key="create"`/`"update"`/`"delete"` are present (greyed buttons render them on `main`).

- [ ] **Step 2: Hide inaccessible context actions (both themes)**

`src/crud_views/templates/crud_views/tags/context_action.html` — replace entire file:

```html
{% if cv_key and cv_action_enabled is not False and cv_access is True %}
    <a href="{{ cv_url }}" class="btn btn-outline-primary {% if cv_is_active %}active{% endif %} btn-lg"
       role="button"
       title="{{ cv_action_label }}"
       cv-key="{{ cv_key }}">
        <i class="{{ cv_icon_action }}"></i>
    </a>
{% endif %}
```

`src/crud_views_plain/templates/crud_views/tags/context_action.html` — this theme has no greyed `{% else %}` branch; it currently renders the link whenever `cv_url and cv_action_enabled is not False` (i.e. even when inaccessible). Add `and cv_access is True` to that guard so inaccessible actions are hidden here too:

```html
{% if cv_url and cv_action_enabled is not False and cv_access is True %}
    <a href="{{ cv_url }}" title="{{ cv_action_label }}">{{ cv_action_short_label }}</a>
{% endif %}
```

- [ ] **Step 3: Hide inaccessible list-row actions (both themes)**

`src/crud_views/templates/crud_views/tags/list_action.html` — replace entire file:

```html
{% if cv_action_enabled is not False and cv_access is True %}
<a {% if cv_list_action_method == "get" %}
    href="{{ cv_url }}"
{% elif cv_list_action_method == "post" %}
    href="#"
    data-cv-action="submit-form"
    data-cv-target="cv_form_{{ cv_oid }}"
{% endif %}
    class="btn btn-outline-primary btn-xs"
    role="button"
    title="{{ cv_action_label }}"
    cv-key="{{ cv_key }}">
    <i class="{{ cv_icon_action }}"></i>
</a>
{% endif %}
```

`src/crud_views_plain/templates/crud_views/tags/list_action.html` — add `and cv_access is True` to its opening `{% if %}` guard (it currently renders the link regardless of access).

- [ ] **Step 4: Gate the hidden POST form on access**

`src/crud_views/templates/crud_views/tags/list_action_form.html` — change the guard to:

```html
{% if cv_action_enabled is not False and cv_access is True and cv_list_action_method == "post" %}
```

(keep the form body unchanged).

- [ ] **Step 5: Run the hidden-action test; confirm pass**

Run: `cd tests && pytest test1/test_context_action_unregistered_key.py::test_inaccessible_actions_are_hidden -v`
Expected: PASS.

- [ ] **Step 6: Update `test_author_view` for hidden (not disabled) actions**

In `tests/test1/test_permissions.py::test_author_view`, the view-only user now sees the `create` (toolbar) and `update`/`delete` (row) actions as **absent**. Replace the `is_disabled` assertions and the `action.href`-derived GETs with absence checks plus direct-URL 403 checks. Example for the `create`/`update`/`delete` blocks:

`get_context_action`/`get_action` **raise `KeyError`** when the key is absent (confirmed in `tests/lib/helper/boostrap5.py`), so assert absence with `pytest.raises(KeyError)`:

```python
    import pytest
    from django.urls import reverse

    # create (toolbar context action) is hidden for a view-only user; endpoint still 403
    with pytest.raises(KeyError):
        table.get_context_action("create")
    assert client.get(reverse(cv_author.get_router_name("create"))).status_code == 403

    # update / delete (row actions) are hidden; endpoints still 403
    with pytest.raises(KeyError):
        row.get_action("update")
    assert client.get(reverse(cv_author.get_router_name("update"), kwargs={"pk": author_douglas_adams.pk})).status_code == 403
    with pytest.raises(KeyError):
        row.get_action("delete")
    assert client.get(reverse(cv_author.get_router_name("delete"), kwargs={"pk": author_douglas_adams.pk})).status_code == 403
```

Keep the existing `detail` assertions (the view-only user can access detail). No change to the test helper is needed (its `KeyError`-on-absence is the contract used here).

- [ ] **Step 7: Re-verify the two adjacent tests**

Run: `cd tests && pytest test1/test_workflow.py::test_workflow_view_get_contains_campaign_name test1/test_filter_pinned.py::test_pinned_hides_filter_toggle_button -v`
Expected: PASS. If `test_workflow_view_get_contains_campaign_name` fails, the campaign name was being read from a now-hidden disabled button — assert it via the page header instead (the accessible `update` action / `<h*>` heading still carries `campaign_new.name`). If `test_pinned_hides_filter_toggle_button` fails, update only the selector to match the (accessible) toggle's current markup.

- [ ] **Step 8: Run the full suite**

Run: `cd tests && pytest -q`
Expected: all green.

- [ ] **Step 9: Lint**

Run: `task format && task check`
Expected: clean.

- [ ] **Step 10: Commit**

```bash
git add src/crud_views/templates/crud_views/tags/context_action.html \
        src/crud_views_plain/templates/crud_views/tags/context_action.html \
        src/crud_views/templates/crud_views/tags/list_action.html \
        src/crud_views_plain/templates/crud_views/tags/list_action.html \
        src/crud_views/templates/crud_views/tags/list_action_form.html \
        tests/test1/test_context_action_unregistered_key.py tests/test1/test_permissions.py
# add tests/test1/test_workflow.py tests/test1/test_filter_pinned.py tests/lib/helper/boostrap5.py if changed
git commit -m "feat!: hide inaccessible actions instead of rendering them greyed-out (toolbar + rows)"
```

---

### Task 3: Changelog entry

**Files:**
- Modify: the changelog source promoted on release (locate first)

- [ ] **Step 1: Locate the changelog Unreleased section**

Run: `ls CHANGELOG.md docs/changelog.md 2>/dev/null; grep -rn "Unreleased\|## \[" CHANGELOG.md docs/*.md 2>/dev/null | head`

- [ ] **Step 2: Add Fixed + Changed entries**

```markdown
### Fixed

- Context actions and list-row actions no longer raise `ViewSetKeyFoundError` (HTTP 500 in
  `DEBUG`) when a ViewSet omits a view referenced by the default `*_CONTEXT_ACTIONS`
  (e.g. a list+detail-only ViewSet and the default `create`/`delete` keys). Unregistered keys
  are skipped.

### Changed

- Actions the current user cannot access are now hidden instead of rendered as greyed-out,
  disabled buttons — applied consistently to the context-action toolbar and list-row actions.
```

- [ ] **Step 3: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs(changelog): note unregistered-key fix and hidden-vs-greyed action change"
```

---

## Self-Review

**Spec coverage:**
- Central `cv_get_context` skip (covers all render paths) → Task 1 Steps 3-5. ✓
- Remove redundant `cv_get_context_buttons` guard → Task 1 Step 4. ✓
- Drop greyed buttons, toolbar + rows + form, both themes → Task 2 Steps 2-4. ✓
- RED for the 500 under forced strict → Task 1 Steps 1-2. ✓
- RED for hidden-not-greyed → Task 2 Step 1. ✓
- Existing-test updates (`test_author_view`, workflow, pinned) + helper → Task 2 Steps 6-7. ✓
- Behavior-change changelog note → Task 3. ✓

**Placeholder scan:** none. The one ambiguity (changelog file path) is resolved by Task 3 Step 1 before editing; the conditional test fixes (Task 2 Step 7) name the concrete fallback action.

**Type consistency:** `cv_get_context` returns `Dict[str, Any]` (now possibly empty `{}`); every consumer guards on falsy `ctx` (`cv_context_action` Step 5; `cv_context_button`/`cv_context_url` already; `cv_get_context_buttons` via `if not ctx`). Template variables (`cv_access`, `cv_action_enabled`, `cv_key`, `cv_url`) match the resolved dict. `reverse(cv_author.get_router_name(<key>), …)` matches existing URL-name usage.
