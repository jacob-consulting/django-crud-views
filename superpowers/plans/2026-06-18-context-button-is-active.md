# `cv_is_active` for All Context Buttons Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Populate `cv_is_active` for every context button (not just view-key buttons) by computing it once in the shared `cv_get_dict` funnel, so `{% cv_context_button "..." %}` can highlight when it points at the current page.

**Architecture:** Move the router-name comparison (`target router name == current url_name`) out of the view-key-only branch and into the classmethod `CrudView.cv_get_dict()`, which every navigational button (`ContextButton`/`Parent`/`Child`/`Sibling` + the view-key branch) funnels through. No new variable; the default button template already consumes `cv_is_active`.

**Tech Stack:** Python, Django (template tags, URL resolver), Pydantic, pytest.

## Global Constraints

- Line length 120; double quotes; ruff format.
- Reuse the existing `cv_is_active` var — do NOT introduce a second var.
- Router-name match semantics: `cls.cv_viewset.get_router_name(cls.cv_key) == context.router_name`.
- Match the existing `resolver_match` exposure — no defensive guarding (raises if `resolver_match` is `None`, exactly as the old line did).
- `FilterContextButton` deliberately does NOT get `cv_is_active` (it bypasses `cv_get_dict`) — do not change that.
- Tests live in `tests/test1/`; run from the `tests/` directory.
- Existing behaviour for the view-key branch must be unchanged.

---

## File Structure

| File | Responsibility |
|---|---|
| `src/crud_views/lib/view/base.py` | compute `cv_is_active` in `cv_get_dict`; remove the redundant view-key-branch line |
| `tests/test1/test_context_button_active.py` | new: context-button `cv_is_active` true/false + view-key regression |
| `docs/reference/context_buttons.md` | note `cv_is_active` is available in button templates |
| `CHANGELOG.md` | Unreleased entry |

Note: `docs/faq.md` already lists `cv_is_active` in the button-template context (line ~32, "True when the button points at the current view"). That statement becomes accurate after this change — **no FAQ edit required**.

---

## Task 1: Move `cv_is_active` into the shared funnel

**Files:**
- Modify: `src/crud_views/lib/view/base.py` (`cv_get_dict` ~line 188-208; remove line ~345)
- Test: `tests/test1/test_context_button_active.py` (new)

**Interfaces:**
- Consumes: `CrudView.cv_get_dict(cls, context, **extra)` (classmethod); `context.router_name` (property → `view.request.resolver_match.url_name`); `cls.cv_viewset.get_router_name(key)`; `ContextButton(key, key_target)` from `crud_views.lib.view`.
- Produces: every button context dict now contains `cv_is_active: bool`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test1/test_context_button_active.py`:

```python
"""cv_is_active is populated for context buttons, true only on the target page."""

import pytest
from django.urls import reverse

from crud_views.lib.view import ContextButton


def _list_view(client, cv_author):
    url = reverse(cv_author.get_router_name("list"))
    resp = client.get(url)
    assert resp.status_code == 200
    return resp.context["view"]


def _detail_view(client, cv_author, author):
    url = reverse(cv_author.get_router_name("detail"), kwargs={"pk": author.pk})
    resp = client.get(url)
    assert resp.status_code == 200
    return resp.context["view"]


@pytest.mark.django_db
def test_context_button_active_on_target_page(client_user_author_view, cv_author):
    # on the list page, a button targeting "list" is active
    view = _list_view(client_user_author_view, cv_author)
    btn = ContextButton(key="home", key_target="list")
    ctx = btn.get_context(view.cv_get_view_context())
    assert ctx["cv_is_active"] is True


@pytest.mark.django_db
def test_context_button_inactive_off_target_page(client_user_author_view, cv_author, author_douglas_adams):
    # on a detail page, the same "list"-targeting button is not active
    view = _detail_view(client_user_author_view, cv_author, author_douglas_adams)
    btn = ContextButton(key="home", key_target="list")
    ctx = btn.get_context(view.cv_get_view_context())
    assert ctx["cv_is_active"] is False


@pytest.mark.django_db
def test_view_key_branch_still_sets_cv_is_active(client_user_author_view, cv_author, author_douglas_adams):
    # regression: the view-key branch keeps the correct value after the line-345 removal
    view = _list_view(client_user_author_view, cv_author)
    user = view.request.user
    list_ctx = view.cv_get_context(key="list", user=user)
    assert list_ctx["cv_is_active"] is True
    detail_ctx = view.cv_get_context(key="detail", obj=author_douglas_adams, user=user)
    assert detail_ctx["cv_is_active"] is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd tests && pytest test1/test_context_button_active.py -v`
Expected: the two context-button tests FAIL with `KeyError: 'cv_is_active'` (the button dict has no such key yet). The view-key regression test PASSES already (that branch sets it today).

- [ ] **Step 3: Compute `cv_is_active` in `cv_get_dict`**

In `src/crud_views/lib/view/base.py`, in `cv_get_dict` (after the `data = dict(...)` literal, immediately before `data.update(extra)`), add:

```python
        data["cv_is_active"] = cls.cv_viewset.get_router_name(cls.cv_key) == context.router_name
        data.update(extra)
        return data
```

(The `data.update(extra)` and `return data` lines already exist — insert the `cv_is_active` line directly above them.)

- [ ] **Step 4: Remove the redundant view-key-branch line**

In the same file, in `cv_get_context`, delete this line from the `dict_kwargs = dict(...)` block (~line 345):

```python
            cv_is_active=self.cv_viewset.get_router_name(key) == context.router_name,
```

The block should then read:

```python
        dict_kwargs = dict(
            cv_access=False,
            cv_oid=self.cv_get_oid(key=key, obj=obj),
            cv_url=self.cv_get_url(key=key, obj=obj),
            cv_template=crud_views_settings.context_button_template,
        )
```

- [ ] **Step 5: Run the new tests to verify they pass**

Run: `cd tests && pytest test1/test_context_button_active.py -v`
Expected: all three PASS.

- [ ] **Step 6: Run the full suite to confirm no regressions**

Run: `cd tests && pytest -q`
Expected: PASS (no failures). Existing context-button and guardian tests still pass; the guardian test at `test_guardian.py:379` that stubs `resolver_match.url_name` for `cv_is_active` remains valid.

- [ ] **Step 7: Lint**

Run: `.venv/bin/ruff check src/crud_views/lib/view/base.py tests/test1/test_context_button_active.py`
Expected: `All checks passed!`

- [ ] **Step 8: Commit**

```bash
git add src/crud_views/lib/view/base.py tests/test1/test_context_button_active.py
git commit -m "feat(buttons): populate cv_is_active for all context buttons"
```

---

## Task 2: Documentation

**Files:**
- Modify: `docs/reference/context_buttons.md` (after the `ContextButton` section, ~line 48)
- Modify: `CHANGELOG.md` (Unreleased entry)

- [ ] **Step 1: Add an "Active state" note to the reference**

In `docs/reference/context_buttons.md`, immediately after the `ContextButton` section's closing paragraph (the line ending `see the [FAQ](../faq.md).`, ~line 48) and before `## ParentContextButton`, insert:

```markdown
### Active state

Every context button's template context includes `cv_is_active` — `True` when the button
points at the view currently being displayed (matched by URL router name). The default button
template uses it to add the `active` CSS class, so a button highlights on its own page:

```django
{% cv_context_button "home" %}
```

This applies to all context button types except `FilterContextButton` (a filter toggle is not a
navigation target).
```

- [ ] **Step 2: Add a CHANGELOG entry**

In `CHANGELOG.md`, under the `Unreleased` section's `Added` (or `Changed`) list, add:

```markdown
- `cv_is_active` is now populated for all context buttons (previously only view-key buttons), so `{% cv_context_button %}` highlights when it points at the current page. Matched by URL router name.
```

(If no `Unreleased` section exists, create `## [Unreleased]` with the appropriate subsection at the top, matching the file's existing heading style.)

- [ ] **Step 3: Verify docs build**

Run: `.venv/bin/mkdocs build -s`
Expected: build succeeds with zero warnings.

- [ ] **Step 4: Commit**

```bash
git add docs/reference/context_buttons.md CHANGELOG.md
git commit -m "docs: document cv_is_active for context buttons"
```

---

## Self-Review (completed)

**Spec coverage:**
- compute `cv_is_active` in `cv_get_dict` → Task 1 Step 3 ✓
- remove redundant line 345 → Task 1 Step 4 ✓
- router-name semantics → Task 1 Step 3 (verbatim) ✓
- `FilterContextButton` left alone → not modified; documented in Task 2 ✓
- resolver-match exposure unchanged → no guarding added ✓
- tests (context-button true/false + view-key regression) → Task 1 Step 1 ✓
- docs (reference + CHANGELOG; FAQ already accurate) → Task 2 ✓

**Placeholder scan:** none — all steps contain literal code/commands.

**Type consistency:** `cv_is_active` (bool) named identically in implementation, tests, and docs; `cls.cv_viewset.get_router_name(cls.cv_key)` matches the existing `get_router_name(key)` signature; `ContextButton(key=, key_target=)` matches the constructor in `buttons.py`.
