# Context Buttons

Context buttons are the action buttons rendered in the header area of a view — controlled by
the `cv_context_actions` attribute on each view class. They provide navigation between views
within and across viewsets.

Every ViewSet has a `context_buttons` list that defines which buttons are available. The
default set is provided by `context_buttons_default()`:

- **`home`** — links to the list view of the current viewset
- **`parent`** — links up to the parent viewset's list view (only rendered when a parent exists)
- **`filter`** — toggles the filter form (only rendered when the view uses `ListViewTableFilterMixin`)

Views reference these buttons by key via `cv_context_actions`. Keys that don't match a context
button are resolved as sibling view keys (e.g. `"update"`, `"delete"`, `"create"`).

## ContextButton

The base class. Links to a sibling view within the same viewset.

```python
from crud_views.lib.view import ContextButton

ContextButton(
    key="my_button",               # action key referenced in cv_context_actions
    key_target="detail",           # target view key within the same viewset
    label_template=None,           # path to a Django template for the label
    label_template_code=None,      # inline Django template string for the label
)
```

| Parameter             | Type          | Default  | Description                                      |
|-----------------------|---------------|----------|--------------------------------------------------|
| `key`                 | `str`         | required | Action key referenced in `cv_context_actions`    |
| `key_target`          | `str \| None` | `None`   | Target view key within the same viewset          |
| `label_template`      | `str \| None` | `None`   | Path to a Django template for the button label   |
| `label_template_code` | `str \| None` | `None`   | Inline Django template string for the label      |

Access is checked via the target view's `cv_has_access(user, obj)`.

## ParentContextButton

Links up to the parent viewset's list view. Included by default via `context_buttons_default()`.
Returns an empty context (no button rendered) when the viewset has no parent.

```python
from crud_views.lib.view import ParentContextButton

ParentContextButton(key="parent", key_target="list")
```

## ChildContextButton

Links down to a child viewset — for example, a "Books" button on an author detail page that
navigates to the book list filtered by that author. This is the inverse of `ParentContextButton`.

```python
from crud_views.lib.view import ChildContextButton

ChildContextButton(
    key="books",                   # action key referenced in cv_context_actions
    child_name="book",             # name of the child viewset
    child_key="list",              # target view key in the child viewset (default: "list")
    label_template_code="Books",   # optional: inline Django template string for the label
)
```

| Parameter             | Type          | Default  | Description                                      |
|-----------------------|---------------|----------|--------------------------------------------------|
| `key`                 | `str`         | required | Action key referenced in `cv_context_actions`    |
| `child_name`          | `str`         | required | Name of the child viewset to link to             |
| `child_key`           | `str`         | `"list"` | Target view key in the child viewset             |
| `label_template`      | `str \| None` | `None`   | Path to a Django template for the button label   |
| `label_template_code` | `str \| None` | `None`   | Inline Django template string for the label      |

The button requires `context.object` to build the child URL (the current object becomes the
parent PK in the child's URL). It returns an empty context when there is no object.

Access is checked via the child view's `cv_has_access(user, obj)`, where `obj` is the current
(parent) object. For Guardian-based views, this means object-level permissions on the parent
are checked automatically.

### Example

Given an Author → Book parent-child relationship:

```python
from crud_views.lib.viewset import ViewSet, ParentViewSet, context_buttons_default
from crud_views.lib.view import ChildContextButton
from crud_views.lib.views import DetailViewPermissionRequired

cv_author = ViewSet(
    model=Author,
    name="author",
    context_buttons=context_buttons_default() + [
        ChildContextButton(key="books", child_name="book", label_template_code="Books"),
    ],
)

cv_book = ViewSet(
    model=Book,
    name="book",
    parent=ParentViewSet(name="author"),
)


class AuthorDetailView(DetailViewPermissionRequired):
    cv_viewset = cv_author
    cv_context_actions = ["update", "delete", "books"]
```

The `"books"` action in `cv_context_actions` renders a button linking to `/author/<pk>/book/`.

## Customizing Default Buttons

Override the default buttons by passing a custom list to the ViewSet:

```python
from crud_views.lib.viewset import ViewSet, context_buttons_default
from crud_views.lib.view import ContextButton, ChildContextButton

# Add child buttons to the defaults
cv_author = ViewSet(
    model=Author,
    name="author",
    context_buttons=context_buttons_default() + [
        ChildContextButton(key="books", child_name="book"),
        ChildContextButton(key="articles", child_name="article", label_template_code="Articles"),
    ],
)

# Or replace defaults entirely
cv_author = ViewSet(
    model=Author,
    name="author",
    context_buttons=[
        ContextButton(key="home", key_target="list"),
        ChildContextButton(key="books", child_name="book"),
    ],
)
```

## Import Paths

```python
from crud_views.lib.view import ContextButton, ParentContextButton, ChildContextButton
from crud_views.lib.viewset import context_buttons_default
```
