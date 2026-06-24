# View-level Context Buttons Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let a `CrudView` declare its own context buttons via a new `cv_context_buttons` attribute (overriding ViewSet-level buttons on key collision), and make `FilterContextButton`'s label templatable.

**Architecture:** Purely additive. Part A adds a `cv_context_buttons: List[ContextButton] | None = None` attribute to `CrudView` and makes `cv_get_context_button` check it before the ViewSet's list. Rendering is unchanged — a button still only renders when its key is in `cv_context_actions` — so no template changes. Part B routes `FilterContextButton`'s label through the shared `_apply_label` helper.

**Tech Stack:** Python 3.12+, Django 4.2–6.0, Pydantic v2 (button classes), pytest (tests/test1 project).

**Spec:** `superpowers/specs/2026-06-24-view-level-context-buttons-design.md` (issue #27, target v0.8.0).

## Global Constraints

- Line length 120, double quotes, ruff-formatted (pre-commit runs `ruff format` + `ruff check`).
- All `CrudView` class attributes use the `cv_` prefix.
- New mutable-collection class attributes default to `None`, never `[]` (audit finding M6 — shared mutable class lists).
- No new third-party dependencies; no new Django system checks (deferred to issue #28).
- Tests live in `tests/test1/`, run with `cd tests && pytest`. Fixture conventions: `cv_<model>` ViewSets, `client_user_<model>_<perm>` clients, `user_viewset_permission(user, viewset, perm)` helper.
- Backwards compatible: defaults reproduce current behavior exactly.

---

### Task 1: View-level button attribute + resolution (Part A)

**Files:**
- Modify: `src/crud_views/lib/view/base.py:43` (add attribute) and `src/crud_views/lib/view/base.py:310-315` (`cv_get_context_button`)
- Test: `tests/test1/test_view_level_context_button.py` (create)

**Interfaces:**
- Consumes: `ContextButton` (already imported in `base.py`; `key` attribute, `label_template_code` field), `CrudView.cv_get_context_button(key)`, `CrudView.cv_get_context_buttons(keys=None, obj=None)`, `self.cv_viewset.context_buttons` (list of `ContextButton`).
- Produces: `CrudView.cv_context_buttons: List[ContextButton] | None` (default `None`). `cv_get_context_button(key)` now returns the first matching view-level button, else the first matching ViewSet-level button, else `None`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test1/test_view_level_context_button.py`:

```python
"""View-level context buttons: CrudView.cv_context_buttons defines buttons; view overrides ViewSet."""

import pytest
from django.urls import reverse

from crud_views.lib.view.buttons import ContextButton


def _book_list_view(client, publisher):
    from tests.test1.app.views import cv_book

    url = reverse(cv_book.get_router_name("list"), kwargs={"publisher_pk": publisher.pk})
    resp = client.get(url)
    assert resp.status_code == 200
    return resp.context["view"]


@pytest.mark.django_db
def test_view_level_overrides_viewset(client_user_book_view, cv_book, publisher_penguin, book_hitchhiker):
    view = _book_list_view(client_user_book_view, publisher_penguin)
    # ViewSet provides a default "home" button
    assert view.cv_get_context_button("home").key == "home"
    override = ContextButton(key="home", key_target="list", label_template_code="VIEWLEVEL")
    view.cv_context_buttons = [override]
    # view-level button with the same key wins (identity check)
    assert view.cv_get_context_button("home") is override


@pytest.mark.django_db
def test_falls_back_to_viewset(client_user_book_view, cv_book, publisher_penguin, book_hitchhiker):
    view = _book_list_view(client_user_book_view, publisher_penguin)
    view.cv_context_buttons = [ContextButton(key="custom", key_target="list")]
    # a key not defined at view level falls back to the ViewSet's buttons
    assert view.cv_get_context_button("home").key == "home"


@pytest.mark.django_db
def test_none_default_unchanged(client_user_book_view, cv_book, publisher_penguin, book_hitchhiker):
    view = _book_list_view(client_user_book_view, publisher_penguin)
    assert view.cv_context_buttons is None
    assert view.cv_get_context_button("home").key == "home"
    assert view.cv_get_context_button("does_not_exist") is None


@pytest.mark.django_db
def test_explicit_render_only_listed_keys(client_user_book_view, cv_book, publisher_penguin, book_hitchhiker):
    view = _book_list_view(client_user_book_view, publisher_penguin)
    view.cv_context_buttons = [ContextButton(key="custom", key_target="list", label_template_code="UNLISTED")]

    # "custom" defined but NOT in cv_context_actions -> not rendered
    view.cv_context_actions = ["home"]
    labels = [c.get("cv_action_label") for c in view.cv_get_context_buttons()]
    assert "UNLISTED" not in labels

    # listing the key in cv_context_actions renders it
    view.cv_context_actions = ["home", "custom"]
    labels = [c.get("cv_action_label") for c in view.cv_get_context_buttons()]
    assert "UNLISTED" in labels
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd tests && pytest test1/test_view_level_context_button.py -v`
Expected: FAIL — `test_view_level_overrides_viewset` and `test_explicit_render_only_listed_keys` fail because `cv_get_context_button` ignores `cv_context_buttons` (setting `view.cv_context_buttons` has no effect yet). `test_none_default_unchanged` may error on `view.cv_context_buttons` if the attribute does not exist.

- [ ] **Step 3: Add the attribute**

In `src/crud_views/lib/view/base.py`, immediately after the `cv_context_actions` line (line 43):

```python
    cv_context_actions: List[str] | None = None  # context actions for the view (top right)
    cv_context_buttons: List[ContextButton] | None = None  # view-level context button definitions (issue #27)
```

(`List` and `ContextButton` are already imported in this module.)

- [ ] **Step 4: Update the resolution method**

Replace `cv_get_context_button` (`base.py:310-315`):

```python
    def cv_get_context_button(self, key: str) -> ContextButton | None:
        # view-level buttons take precedence over ViewSet-level buttons (issue #27)
        for cb in self.cv_context_buttons or []:
            if cb.key == key:
                return cb
        for cb in self.cv_viewset.context_buttons:
            if cb.key == key:
                return cb
        return None
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd tests && pytest test1/test_view_level_context_button.py -v`
Expected: PASS (4 passed)

- [ ] **Step 6: Run the full context-button suite to check for regressions**

Run: `cd tests && pytest test1/ -k "context_button or context_actions" -q`
Expected: PASS (all existing context-button tests still green)

- [ ] **Step 7: Format and commit**

```bash
uv run ruff format src/crud_views/lib/view/base.py tests/test1/test_view_level_context_button.py
git add src/crud_views/lib/view/base.py tests/test1/test_view_level_context_button.py
git commit -m "feat: view-level context buttons via cv_context_buttons (#27)"
```

---

### Task 2: FilterContextButton label templating (Part B)

**Files:**
- Modify: `src/crud_views/lib/view/buttons.py:236-257` (`FilterContextButton.get_context`)
- Test: `tests/test1/test_context_button_template.py` (append)

**Interfaces:**
- Consumes: `ContextButton._apply_label(data, context)` (already defined at `buttons.py:34`; overrides `data["cv_action_label"]` when `label_template`/`label_template_code` is set, no-op otherwise), `FilterContextButton`, `CrudView.cv_get_view_context()` → `ViewContext`, `PublisherListView` (a `ListViewTableFilterMixin` view in the test app), fixture `client_user_publisher_view`, `cv_publisher`.
- Produces: `FilterContextButton.get_context` now honors `label_template`/`label_template_code`, defaulting to `"Filter"`.

- [ ] **Step 1: Write the failing tests**

First add these imports to the **top** of `tests/test1/test_context_button_template.py` (after
the existing imports on lines 1-4), so they are not flagged as mid-file imports (ruff E402):

```python
import pytest
from django.urls import reverse
```

Then append the helper and tests to the end of the file:

```python
def _publisher_list_view(client, cv_publisher):
    url = reverse(cv_publisher.get_router_name("list"))
    resp = client.get(url)
    assert resp.status_code == 200
    return resp.context["view"]


@pytest.mark.django_db
def test_filter_button_default_label(client_user_publisher_view, cv_publisher):
    view = _publisher_list_view(client_user_publisher_view, cv_publisher)
    ctx = FilterContextButton().get_context(view.cv_get_view_context())
    assert ctx["cv_action_label"] == "Filter"


@pytest.mark.django_db
def test_filter_button_templated_label(client_user_publisher_view, cv_publisher):
    view = _publisher_list_view(client_user_publisher_view, cv_publisher)
    ctx = FilterContextButton(label_template_code="Suchen").get_context(view.cv_get_view_context())
    assert ctx["cv_action_label"] == "Suchen"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd tests && pytest test1/test_context_button_template.py -k filter_button -v`
Expected: `test_filter_button_templated_label` FAILS — label stays `"Filter"` because `FilterContextButton.get_context` does not call `_apply_label`. `test_filter_button_default_label` may already pass.

- [ ] **Step 3: Wire the label helper**

In `src/crud_views/lib/view/buttons.py`, in `FilterContextButton.get_context`, add the `_apply_label` call after setting the default label (between the `cv_url` assignment and `_inject_template`):

```python
        data = dict()
        data["cv_action_label"] = "Filter"
        data["cv_icon_action"] = crud_views_settings.filter_icon
        data["cv_url"] = list_url
        self._apply_label(data, context)
        self._inject_template(data)

        return data
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd tests && pytest test1/test_context_button_template.py -k filter_button -v`
Expected: PASS (3 passed — the two new tests plus the existing `test_filter_button_default_template`)

- [ ] **Step 5: Format and commit**

```bash
uv run ruff format src/crud_views/lib/view/buttons.py tests/test1/test_context_button_template.py
git add src/crud_views/lib/view/buttons.py tests/test1/test_context_button_template.py
git commit -m "feat: support label templating on FilterContextButton (#27)"
```

---

### Task 3: Documentation, skill & CHANGELOG

**Files:**
- Modify: `docs/reference/context_buttons.md` (add a "View-level context buttons" section)
- Modify: `skills/django-crud-views/SKILL.md` (add a `cv_context_buttons` subsection after `SiblingContextButton`, ~line 311)
- Modify: `skills/django-crud-views/references/api-reference.md` (note `cv_context_buttons` in the context-button catalog, ~line 308)
- Modify: `CHANGELOG.md` (add an `Unreleased` section with two `Added` entries)

**Interfaces:**
- Consumes: nothing (docs only).
- Produces: published documentation of the Task 1 + Task 2 behavior.

- [ ] **Step 1: Add the reference section**

In `docs/reference/context_buttons.md`, add a new section (place it before "## Manual Placement (Template Tags)"):

```markdown
## View-level Context Buttons

By default, context buttons are defined on the **ViewSet** (`context_buttons`) and shared by
every view in it. To define a button on a **single view**, set `cv_context_buttons` on the
`CrudView` — a list of the same `ContextButton` types.

```python
from crud_views.lib.view import ChildContextButton
from crud_views.lib.views import DetailViewPermissionRequired

class BookDetailView(DetailViewPermissionRequired):
    cv_viewset = cv_book
    cv_context_actions = ["update", "delete", "reviews"]   # "reviews" listed -> it renders
    cv_context_buttons = [                                  # defines "reviews" for this view only
        ChildContextButton(key="reviews", child_name="review", label_template_code="Reviews"),
    ]
```

Two rules:

- **Rendering is unchanged:** a button appears only when its `key` is listed in
  `cv_context_actions`. `cv_context_buttons` only *defines* buttons; `cv_context_actions`
  controls what renders and in what order.
- **View overrides ViewSet:** if a view-level button has the same `key` as a ViewSet-level
  button, the view-level one wins for that view. Declare a same-key button in
  `cv_context_buttons` to customize a single view without touching the ViewSet.
```

Then, in the `FilterContextButton` discussion (the default-buttons list near the top mentions
`filter`), note that its label is now templatable: add a sentence —
"The `filter` button's label (default `Filter`) can be customized with `label_template` /
`label_template_code` like any other button."

- [ ] **Step 2: Add the skill subsection**

In `skills/django-crud-views/SKILL.md`, after the `SiblingContextButton` parameters block
(~line 311), add:

```markdown
### View-level context buttons (cv_context_buttons)

Context buttons are normally defined on the ViewSet and shared by all its views. To define a
button on a single view, set `cv_context_buttons` on the `CrudView`:

```python
class BookDetailView(DetailViewPermissionRequired):
    cv_viewset = cv_book
    cv_context_actions = ["update", "delete", "reviews"]   # list the key to render it
    cv_context_buttons = [
        ChildContextButton(key="reviews", child_name="review", label_template_code="Reviews"),
    ]
```

- A button renders only when its `key` is in `cv_context_actions` (definition vs. rendering
  stay separate).
- A view-level button overrides a ViewSet-level button with the same `key`, for that view only.
```

- [ ] **Step 3: Note it in the api-reference catalog**

In `skills/django-crud-views/references/api-reference.md`, in the context-button section
(~line 308), append a line after the description of `context_buttons`:

```markdown
A single view can also define its own buttons via `cv_context_buttons` (a list of `ContextButton`s); view-level buttons override ViewSet-level ones with the same key. Buttons still render only when their key is listed in `cv_context_actions`.
```

- [ ] **Step 4: Add the CHANGELOG entries**

In `CHANGELOG.md`, add a new section directly under the `# Django CRUD Views - Changelog`
title (above `## 0.7.1`):

```markdown
## Unreleased

### Added

- View-level context buttons: set `cv_context_buttons` on a `CrudView` (a list of `ContextButton`s) to define buttons for a single view instead of the whole ViewSet. View-level buttons override ViewSet-level ones with the same `key`; they render only when the key is listed in `cv_context_actions`, matching existing button behavior.
- `FilterContextButton` now honors `label_template` / `label_template_code`, so the filter toggle's label (default `Filter`) can be customized like any other context button.
```

- [ ] **Step 5: Verify the docs build (strict, same as CI)**

Run: `uv run --with-requirements docs/requirements.txt mkdocs build --strict`
Expected: "Documentation built" with no warnings; then `rm -rf site`.

- [ ] **Step 6: Commit**

```bash
git add docs/reference/context_buttons.md skills/django-crud-views/SKILL.md skills/django-crud-views/references/api-reference.md CHANGELOG.md
git commit -m "docs: document view-level context buttons and filter label (#27)"
```

---

### Task 4: Full-suite verification

**Files:** none (verification only).

- [ ] **Step 1: Run the whole test suite**

Run: `cd tests && pytest -q`
Expected: all pass (previous baseline was 410 passed, 1 skipped; this adds 6 tests → ~416 passed, 1 skipped).

- [ ] **Step 2: Lint check (matches CI)**

Run: `uv run ruff format --check . && uv run ruff check .`
Expected: no changes needed, no errors.

- [ ] **Step 3: Confirm clean tree**

Run: `git status --short`
Expected: empty (all work committed across Tasks 1–3).

---

## Notes for the implementer

- Do **not** edit either `context_actions.html` template — the explicit rendering model means
  the existing `{% for key in view.cv_context_actions %}` loop is unchanged. If you find
  yourself editing a template, re-read the spec's "Rendering pipeline impact" section.
- Do **not** add a `cv_has_access` check to `FilterContextButton` — that was explicitly scoped
  out (a filter toggle is not access-controlled).
- The `cv_context_buttons` default MUST be `None`, not `[]` (audit M6: shared mutable class
  attributes). Tests assert `view.cv_context_buttons is None` by default.
