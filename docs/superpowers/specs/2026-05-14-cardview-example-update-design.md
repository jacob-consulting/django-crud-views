# CardView Bootstrap5 Example Update

## Summary

Move the CardListView from the Author viewset to the Book viewset in the bootstrap5 example app. This better demonstrates the feature: an author has a manageable number of books, making cards a natural fit, whereas the top-level author list is better served by a table.

Also change the default CardView icon and add a title filter to demonstrate filter+card integration.

## Changes

### 1. Remove CardView from Author viewset (`examples/bootstrap5/app/views/author.py`)

- Delete `AuthorCardListView` class
- Remove `"card"` from `AuthorListView.cv_context_actions`
- Remove unused `CardListViewPermissionRequired` and `CardAction` imports

### 2. Add CardView to Book viewset (`examples/bootstrap5/app/views/book.py`)

Replace `BookListView` (table-based) with `BookCardListView` using:
- `ListViewTableFilterMixin` + `GuardianCardListViewPermissionRequired`
- `cv_card_actions` with detail (primary, flex), update, and delete (tertiary, no_label) — matching the pattern from the former AuthorCardListView
- `BookFilter` with a single `title` field using `icontains` lookup
- `BookFilterFormHelper` with a single-row crispy layout

Import additions: `django_filters`, `CardAction`, `ListViewTableFilterMixin`, `ListViewFilterFormHelper`, `GuardianCardListViewPermissionRequired`.

The `BookTable` class becomes unused and is removed.

### 3. Change default CardView icon (`crud_views/lib/views/card.py`)

Change `cv_icon_action` from `"fa-regular fa-grip"` to `"fa-solid fa-rectangle-list"`.

### 4. Fix child navigation links (`examples/bootstrap5/app/views/author.py`)

CardListView uses `cv_key = "card"`, not `"list"`. Two references in the Author viewset need updating:

- `AuthorTable.books = LinkChildColumn(name="book")` — add `key="card"` since `LinkChildColumn` defaults to `key="list"`
- `RedirectBooksView.cv_redirect_key` — change from `"list"` to `"card"`

### 5. No model or URL changes

Book is already a child of Author via `ParentViewSet`. URL routing updates automatically through the ViewSet when the new card view registers.
