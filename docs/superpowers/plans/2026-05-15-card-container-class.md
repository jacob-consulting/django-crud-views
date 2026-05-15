# Card Container Class Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Allow users to configure the Bootstrap grid class on card container divs via `cv_card_container_class`.

**Architecture:** Add a `cv_card_container_class` class attribute to `CardListView` (default `"col-md-6"`). The template reads it via `{{ view.cv_card_container_class }}`. No context data override needed — `view` is already in the template context.

**Tech Stack:** Django class-based views, Django templates, pytest

---

### Task 1: Add `cv_card_container_class` attribute and update template

**Files:**
- Modify: `crud_views/lib/views/card.py:8-17` (add attribute to `CardListView`)
- Modify: `crud_views/templates/crud_views/view_card.content.html:5` (use attribute in template)

- [ ] **Step 1: Add the class attribute to `CardListView`**

In `crud_views/lib/views/card.py`, add `cv_card_container_class` after `cv_card_actions`:

```python
cv_card_container_class: str = "col-md-6"
```

- [ ] **Step 2: Update the template to use the attribute**

In `crud_views/templates/crud_views/view_card.content.html`, replace:

```html
<div class="col-md-6">
```

with:

```html
<div class="{{ view.cv_card_container_class }}">
```

- [ ] **Step 3: Run the existing test suite to confirm no regressions**

Run: `cd tests && pytest test1/test_card.py -v`
Expected: All 5 existing tests pass — the default value matches the old hardcoded class.

- [ ] **Step 4: Commit**

```bash
git add crud_views/lib/views/card.py crud_views/templates/crud_views/view_card.content.html
git commit -m "feat: add cv_card_container_class to CardListView"
```

---

### Task 2: Add tests for `cv_card_container_class`

**Files:**
- Modify: `tests/test1/test_card.py` (add two tests)

- [ ] **Step 1: Write test for default container class**

Append to `tests/test1/test_card.py`:

```python
@pytest.mark.django_db
def test_card_container_class_default(client_user_author_view: Client, cv_author, author_douglas_adams):
    """Default card container uses col-md-6."""
    response = client_user_author_view.get("/author/card/")
    assert response.status_code == 200
    doc = html.fromstring(response.content)
    containers = doc.cssselect(".row > .col-md-6")
    assert len(containers) == 1
```

- [ ] **Step 2: Run the test to verify it passes**

Run: `cd tests && pytest test1/test_card.py::test_card_container_class_default -v`
Expected: PASS

- [ ] **Step 3: Write test for custom container class**

This test needs a view with a custom `cv_card_container_class`. Add a new view class to `tests/test1/app/views.py` and register it with the author ViewSet, then test it. However, since adding a new view to an existing ViewSet changes URL routing for all tests, a cleaner approach is to inspect the view attribute directly and verify the template renders whatever class the view provides.

Instead, use a separate ViewSet to avoid side effects. Append to `tests/test1/test_card.py`:

```python
@pytest.fixture
def cv_author_wide_card():
    from tests.test1.app.models import Author

    cv = ViewSet(model=Author, name="author_wide_card")

    class AuthorWideCardListView(CardListViewPermissionRequired):
        cv_viewset = cv
        cv_card_container_class = "col-md-12"
        cv_card_actions = [
            CardAction(key="detail", label="Details", variant="primary", flex=True),
        ]

    class AuthorDetailView(DetailViewPermissionRequired):
        cv_viewset = cv

    return cv


@pytest.fixture
def user_author_wide_card_view(cv_author_wide_card):
    from django.contrib.auth.models import User
    from tests.lib.helper.user import user_viewset_permission

    user = User.objects.create_user(username="user_wide_card", password="password")
    user_viewset_permission(user, cv_author_wide_card, "view")
    return user


@pytest.fixture
def client_user_author_wide_card(client, user_author_wide_card_view) -> Client:
    client.force_login(user_author_wide_card_view)
    return client


@pytest.mark.django_db
def test_card_container_class_custom(client_user_author_wide_card: Client, cv_author_wide_card, author_douglas_adams):
    """Custom cv_card_container_class renders in the template."""
    response = client_user_author_wide_card.get("/author_wide_card/card/")
    assert response.status_code == 200
    doc = html.fromstring(response.content)
    containers = doc.cssselect(".row > .col-md-12")
    assert len(containers) == 1
    # Verify the default class is NOT present
    default_containers = doc.cssselect(".row > .col-md-6")
    assert len(default_containers) == 0
```

Add the required imports at the top of the test file:

```python
from crud_views.lib.view import CardAction
from crud_views.lib.viewset import ViewSet
from crud_views.lib.views import CardListViewPermissionRequired, DetailViewPermissionRequired
```

- [ ] **Step 4: Run the new test to verify it passes**

Run: `cd tests && pytest test1/test_card.py::test_card_container_class_custom -v`
Expected: PASS

- [ ] **Step 5: Run full card test suite**

Run: `cd tests && pytest test1/test_card.py -v`
Expected: All tests pass (5 existing + 2 new = 7 total).

- [ ] **Step 6: Commit**

```bash
git add tests/test1/test_card.py
git commit -m "test: add tests for cv_card_container_class"
```

---

### Task 3: Update documentation

**Files:**
- Modify: `docs/reference/card-list-view.md` (add section)

- [ ] **Step 1: Add Card Container Class section to docs**

In `docs/reference/card-list-view.md`, add a new section after "## CardAction Fields" (after line 39):

```markdown
## Card Container Class

Control the Bootstrap grid class on each card's wrapper `<div>`. Defaults to `col-md-6` (two cards per row).

```python
class ProjectCardListView(CardListViewPermissionRequired):
    cv_viewset = cv_project
    cv_card_container_class = "col-md-12"  # full-width cards
    cv_card_actions = [...]
```

| Value | Layout |
|---|---|
| `col-md-4` | Three cards per row |
| `col-md-6` | Two cards per row (default) |
| `col-md-12` | One card per row |
```

- [ ] **Step 2: Commit**

```bash
git add docs/reference/card-list-view.md
git commit -m "docs: document cv_card_container_class property"
```

---

### Task 4: Update skill reference

**Files:**
- Modify: `skills/django-crud-views/SKILL.md:60-82` (add to CardListView section)

- [ ] **Step 1: Add `cv_card_container_class` to skill docs**

In `skills/django-crud-views/SKILL.md`, in the CardListView section (after line 82, after the paragraph about `cv_card_actions`), add:

```markdown
### Card Container Class

Override `cv_card_container_class` to control the Bootstrap grid width of each card wrapper. Default is `"col-md-6"` (two cards per row). Set to `"col-md-12"` for full-width or `"col-md-4"` for three per row.
```

- [ ] **Step 2: Commit**

```bash
git add skills/django-crud-views/SKILL.md
git commit -m "docs: add cv_card_container_class to skill reference"
```

---

### Task 5: Final verification

- [ ] **Step 1: Run the full test suite**

Run: `cd tests && pytest -v`
Expected: All tests pass (no regressions).

- [ ] **Step 2: Run linter**

Run: `task check && task format`
Expected: No issues.
