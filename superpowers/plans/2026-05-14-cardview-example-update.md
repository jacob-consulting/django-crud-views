# CardView Bootstrap5 Example Update — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move CardListView from the Author viewset to the Book viewset in the bootstrap5 example, change the default card icon, and add a title filter to demonstrate filter+card integration.

**Architecture:** Four files change. The default card icon in `crud_views/lib/views/card.py` is updated. In the example app, `author.py` loses its CardListView and card-related imports; `book.py` gains a CardListView with a django-filter title search. Two navigation references in `author.py` (`LinkChildColumn` and `RedirectBooksView`) are updated to point at the card key instead of the list key.

**Tech Stack:** Django, django-crud-views, django-filter, django-crispy-forms, django-guardian

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `crud_views/lib/views/card.py` | Modify line 28 | Change default `cv_icon_action` |
| `examples/bootstrap5/app/views/author.py` | Modify | Remove `AuthorCardListView`, update imports, fix child nav links |
| `examples/bootstrap5/app/views/book.py` | Modify | Replace `BookListView` with `BookCardListView`, add filter, remove table |

---

### Task 1: Change default CardView icon

**Files:**
- Modify: `crud_views/lib/views/card.py:28`

- [ ] **Step 1: Update the icon**

In `crud_views/lib/views/card.py`, change line 28 from:
```python
    cv_icon_action = "fa-regular fa-grip"
```
to:
```python
    cv_icon_action = "fa-solid fa-rectangle-list"
```

- [ ] **Step 2: Run existing card tests to verify nothing breaks**

Run: `cd tests && pytest test1/test_card.py test1/test_guardian_card.py -v`
Expected: All tests PASS (the icon change doesn't affect HTML assertions in existing tests).

- [ ] **Step 3: Commit**

```bash
git add crud_views/lib/views/card.py
git commit -m "feat: change default CardView icon to fa-solid fa-rectangle-list"
```

---

### Task 2: Remove CardView from Author viewset

**Files:**
- Modify: `examples/bootstrap5/app/views/author.py`

- [ ] **Step 1: Remove CardListView-related imports**

In `examples/bootstrap5/app/views/author.py`, remove these from the imports:

Remove `CardAction` from line 11:
```python
from crud_views.lib.view import CardAction
```

Remove `CardListViewPermissionRequired` from the `crud_views.lib.views` import block (line 16):
```python
    CardListViewPermissionRequired,
```

- [ ] **Step 2: Remove `"card"` from AuthorListView.cv_context_actions**

Change line 93 from:
```python
    cv_context_actions = ["card"] + GuardianListViewPermissionRequired.cv_context_actions
```
to:
```python
    cv_context_actions = GuardianListViewPermissionRequired.cv_context_actions
```

- [ ] **Step 3: Delete the AuthorCardListView class**

Delete lines 96–104 (the entire `AuthorCardListView` class):
```python
class AuthorCardListView(ListViewTableFilterMixin, CardListViewPermissionRequired):
    cv_viewset = cv_author
    filterset_class = AuthorFilter
    formhelper_class = AuthorFilterFormHelper
    cv_card_actions = [
        CardAction(key="detail", label="Details", variant="primary", flex=True),
        CardAction(key="update", label="Edit"),
        CardAction(key="delete", no_label=True, variant="tertiary"),
    ]
```

- [ ] **Step 4: Update LinkChildColumn to point to card key**

Change line 77 from:
```python
    books = LinkChildColumn(name="book", verbose_name=_("Books"), attrs=Table.ca.w10)
```
to:
```python
    books = LinkChildColumn(name="book", key="card", verbose_name=_("Books"), attrs=Table.ca.w10)
```

- [ ] **Step 5: Update RedirectBooksView to redirect to card key**

Change line 175 from:
```python
    cv_redirect_key = "list"
```
to:
```python
    cv_redirect_key = "card"
```

- [ ] **Step 6: Run format check**

Run: `task check && task format`
Expected: Clean output.

- [ ] **Step 7: Commit**

```bash
git add examples/bootstrap5/app/views/author.py
git commit -m "refactor: remove CardView from Author viewset in bootstrap5 example"
```

---

### Task 3: Add CardView to Book viewset

**Files:**
- Modify: `examples/bootstrap5/app/views/book.py`

- [ ] **Step 1: Update imports**

Replace the entire import block at the top of `examples/bootstrap5/app/views/book.py` with:

```python
import django_filters
from crispy_forms.layout import Row, Layout
from django.utils.translation import gettext_lazy as _

from app.models import Book
from crud_views.lib.crispy import CrispyModelForm, Column4, Column2, CrispyModelViewMixin, CrispyDeleteForm
from crud_views.lib.view import CardAction
from crud_views.lib.views import (
    ListViewTableFilterMixin,
    CreateViewParentMixin,
    MessageMixin,
)
from crud_views.lib.views.list import ListViewFilterFormHelper
from crud_views.lib.viewset import ParentViewSet
from crud_views_guardian.lib.viewset import GuardianViewSet
from crud_views_guardian.lib.views import (
    GuardianCardListViewPermissionRequired,
    GuardianDetailViewPermissionRequired,
    GuardianCreateViewPermissionRequired,
    GuardianUpdateViewPermissionRequired,
    GuardianDeleteViewPermissionRequired,
)
```

Removed: `django_tables2`, `Table`, `UUIDLinkDetailColumn`, `ListViewTableMixin`, `GuardianListViewPermissionRequired`.
Added: `django_filters`, `Layout`, `CardAction`, `ListViewTableFilterMixin`, `ListViewFilterFormHelper`, `GuardianCardListViewPermissionRequired`.

- [ ] **Step 2: Add BookFilter and BookFilterFormHelper**

After the `BookUpdateForm` class (line 48), add:

```python
class BookFilterFormHelper(ListViewFilterFormHelper):
    layout = Layout(
        Row(Column4("title")),
    )


class BookFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Book
        fields = ["title"]
```

- [ ] **Step 3: Remove BookTable class**

Delete the `BookTable` class entirely:
```python
class BookTable(Table):
    id = UUIDLinkDetailColumn()
    title = tables.Column()
    price = tables.Column()
    author = tables.Column()
```

- [ ] **Step 4: Replace BookListView with BookCardListView**

Replace:
```python
class BookListView(ListViewTableMixin, GuardianListViewPermissionRequired):
    cv_viewset = cv_book
    # cv_list_actions = ["detail", "update", "delete"]

    table_class = BookTable
```

With:
```python
class BookCardListView(ListViewTableFilterMixin, GuardianCardListViewPermissionRequired):
    cv_viewset = cv_book
    filterset_class = BookFilter
    formhelper_class = BookFilterFormHelper
    cv_card_actions = [
        CardAction(key="detail", label="Details", variant="primary", flex=True),
        CardAction(key="update", label="Edit"),
        CardAction(key="delete", no_label=True, variant="tertiary"),
    ]
```

- [ ] **Step 5: Run format check**

Run: `task check && task format`
Expected: Clean output.

- [ ] **Step 6: Commit**

```bash
git add examples/bootstrap5/app/views/book.py
git commit -m "feat: add CardView with title filter to Book viewset in bootstrap5 example"
```

---

### Task 4: Verify the full test suite

- [ ] **Step 1: Run all tests**

Run: `cd tests && pytest -v`
Expected: All tests pass. The example app is not part of the test suite, but the card icon change in `crud_views/lib/views/card.py` is covered by existing card tests.

- [ ] **Step 2: Run lint**

Run: `task check`
Expected: Clean output.
