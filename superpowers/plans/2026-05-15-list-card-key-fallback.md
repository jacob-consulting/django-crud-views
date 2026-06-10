# List-to-Card Key Fallback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** When a ViewSet has no ListView but has a CardListView, automatically fall back from key `"list"` to `"card"` instead of raising `ViewSetKeyFoundError`.

**Architecture:** Modify `ViewSet.get_view_class()` — the single chokepoint for all key resolution — to check for a `"list"` → `"card"` fallback before raising the error. This fixes `cv_success_key`, `cv_cancel_key`, `cv_home_key`, and the default "home" ContextButton all at once.

**Tech Stack:** Django class-based views, pytest

---

### Task 1: Implement the fallback in `get_view_class()`

**Files:**
- Modify: `crud_views/lib/viewset/__init__.py:253-258`
- Test: `tests/test1/test_card.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test1/test_card.py`:

```python
def test_get_view_class_fallback_list_to_card(cv_author_wide_card):
    """When 'list' is not registered but 'card' is, get_view_class('list') returns the card view."""
    view_class = cv_author_wide_card.get_view_class("list")
    assert view_class.cv_key == "card"


def test_get_view_class_no_fallback_when_list_exists(cv_author):
    """When 'list' is registered, get_view_class('list') returns the list view, not card."""
    view_class = cv_author.get_view_class("list")
    assert view_class.cv_key == "list"


def test_get_view_class_raises_when_neither_list_nor_card(cv_author):
    """When key is not registered and no fallback applies, raises ViewSetKeyFoundError."""
    from crud_views.lib.exceptions import ViewSetKeyFoundError

    with pytest.raises(ViewSetKeyFoundError):
        cv_author.get_view_class("nonexistent")
```

Note: `cv_author_wide_card` is a ViewSet with a CardListView but no ListView (already defined in the test app). `cv_author` has both ListView and CardListView. Both fixtures already exist.

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/alex/projects/alex/django-crud-views/tests && pytest test1/test_card.py::test_get_view_class_fallback_list_to_card -v`
Expected: FAIL with `ViewSetKeyFoundError: key list not registered at author_wide_card`

- [ ] **Step 3: Implement the fallback**

In `crud_views/lib/viewset/__init__.py`, replace the current `get_view_class` method:

```python
def get_view_class(self, key: str) -> Type[CrudView]:
    cv_raise(self.is_view_registered(key), f"key {key} not registered at {self}", ViewSetKeyFoundError)
    return self._views[key]
```

with:

```python
def get_view_class(self, key: str) -> Type[CrudView]:
    if not self.is_view_registered(key) and key == "list" and self.is_view_registered("card"):
        return self._views["card"]
    cv_raise(self.is_view_registered(key), f"key {key} not registered at {self}", ViewSetKeyFoundError)
    return self._views[key]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/alex/projects/alex/django-crud-views/tests && pytest test1/test_card.py -v`
Expected: All tests pass (the 3 new tests + all existing card tests).

- [ ] **Step 5: Run full test suite for regressions**

Run: `cd /home/alex/projects/alex/django-crud-views/tests && pytest -v`
Expected: All tests pass.

- [ ] **Step 6: Commit**

```bash
git add crud_views/lib/viewset/__init__.py tests/test1/test_card.py
git commit -m "feat: fall back from list to card key in ViewSet.get_view_class()"
```

---

### Task 2: Add integration test for CreateView redirect in card-only ViewSet

**Files:**
- Modify: `tests/test1/app/views.py` (add CreateView to `cv_author_wide_card`)
- Modify: `tests/test1/test_card.py` (add integration test)

- [ ] **Step 1: Add a CreateView to the card-only ViewSet**

In `tests/test1/app/views.py`, after `AuthorWideCardDetailView` (line 177), add:

```python
class AuthorWideCardCreateView(CrispyModelViewMixin, CreateViewPermissionRequired):
    form_class = AuthorForm
    cv_viewset = cv_author_wide_card
```

This uses the existing `AuthorForm` and `CrispyModelViewMixin` imports already in the file. The `cv_success_key` defaults to `"list"`, which will now fall back to `"card"`.

- [ ] **Step 2: Write the integration test**

Append to `tests/test1/test_card.py`:

```python
@pytest.fixture
def user_author_wide_card_add(cv_author_wide_card):
    from django.contrib.auth.models import User
    from tests.lib.helper.user import user_viewset_permission

    user = User.objects.create_user(username="user_wide_card_add", password="password")
    user_viewset_permission(user, cv_author_wide_card, "view")
    user_viewset_permission(user, cv_author_wide_card, "add")
    return user


@pytest.fixture
def client_user_author_wide_card_add(client, user_author_wide_card_add) -> Client:
    client.force_login(user_author_wide_card_add)
    return client


@pytest.mark.django_db
def test_create_view_redirects_to_card_in_card_only_viewset(
    client_user_author_wide_card_add: Client, cv_author_wide_card
):
    """CreateView in a card-only ViewSet redirects to the card view after success."""
    response = client_user_author_wide_card_add.post(
        "/author_wide_card/create/",
        {"first_name": "Isaac", "last_name": "Asimov", "pseudonym": ""},
    )
    assert response.status_code == 302
    assert "/author_wide_card/card/" in response.url
```

- [ ] **Step 3: Run the integration test**

Run: `cd /home/alex/projects/alex/django-crud-views/tests && pytest test1/test_card.py::test_create_view_redirects_to_card_in_card_only_viewset -v`
Expected: PASS (the fallback from Task 1 makes `get_success_url()` resolve `"list"` → `"card"`)

- [ ] **Step 4: Run full test suite**

Run: `cd /home/alex/projects/alex/django-crud-views/tests && pytest -v`
Expected: All tests pass.

- [ ] **Step 5: Commit**

```bash
git add tests/test1/app/views.py tests/test1/test_card.py
git commit -m "test: add integration test for CreateView redirect in card-only ViewSet"
```

---

### Task 3: Update documentation and skill reference

**Files:**
- Modify: `docs/reference/card-list-view.md`
- Modify: `skills/django-crud-views/SKILL.md`

- [ ] **Step 1: Add fallback documentation to card-list-view.md**

In `docs/reference/card-list-view.md`, add a new section before the "## Guardian" section:

```markdown
## List Key Fallback

When a ViewSet has a `CardListView` but no `ListView`, keys that reference `"list"` 
(such as `cv_success_key`, `cv_cancel_key`, and the default "home" context button) 
automatically fall back to `"card"`. No manual overrides needed.

This means a ViewSet with only a `CardListView` works out of the box — CreateView, 
UpdateView, and DeleteView all redirect to the card view after success.
```

- [ ] **Step 2: Update skill reference**

In `skills/django-crud-views/SKILL.md`, in the CardListView section, after the "Card Container Class" subsection, add:

```markdown
### List Key Fallback

ViewSets with only a `CardListView` (no `ListView`) automatically resolve `"list"` keys to `"card"`. No need to
override `cv_success_key` or `cv_cancel_key` on sibling views.
```

- [ ] **Step 3: Commit**

```bash
git add docs/reference/card-list-view.md skills/django-crud-views/SKILL.md
git commit -m "docs: document list-to-card key fallback"
```

---

### Task 4: Final verification

- [ ] **Step 1: Run full test suite**

Run: `cd /home/alex/projects/alex/django-crud-views/tests && pytest -v`
Expected: All tests pass.

- [ ] **Step 2: Run linter**

Run: `task check && task format`
Expected: No issues.
