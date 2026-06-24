# Context Buttons

Context buttons are the action buttons rendered in the header area of a view — controlled by
the `cv_context_actions` attribute on each view class. They provide navigation between views
within and across viewsets.

Every ViewSet has a `context_buttons` list that defines which buttons are available. The
default set is provided by `context_buttons_default()`:

- **`home`** — links to the list view of the current viewset
- **`parent`** — links up to the parent viewset's list view (only rendered when a parent exists)
- **`filter`** — toggles the filter form (only rendered when the view uses `ListViewTableFilterMixin`). The `filter` button's label (default `Filter`) can be customized with `label_template` / `label_template_code` like any other button.

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
    template=None,                 # path to a Django template for the whole button
    template_code=None,            # inline Django template string for the whole button
)
```

| Parameter             | Type          | Default  | Description                                      |
|-----------------------|---------------|----------|--------------------------------------------------|
| `key`                 | `str`         | required | Action key referenced in `cv_context_actions`    |
| `key_target`          | `str \| None` | `None`   | Target view key within the same viewset          |
| `label_template`      | `str \| None` | `None`   | Path to a Django template for the button label   |
| `label_template_code` | `str \| None` | `None`   | Inline Django template string for the label      |
| `template`            | `str \| None` | `None`   | Path to a Django template for the whole button   |
| `template_code`       | `str \| None` | `None`   | Inline Django template string for the whole button |

Access is checked via the target view's `cv_has_access(user, obj)`.

When neither `template` nor `template_code` is set, the button uses the
`CRUD_VIEWS_CONTEXT_BUTTON_TEMPLATE` setting (default
`crud_views/tags/context_action.html`). For placing buttons by hand in a custom layout, see
[Manual Placement (Template Tags)](#manual-placement-template-tags) below.

### Active state

Every context button's template context includes `cv_is_active` — `True` when the button
points at the view currently being displayed (matched by URL router name). The default button
template uses it to add the `active` CSS class, so a button highlights on its own page:

```django
{% cv_context_button "home" %}
```

This applies to all context button types except `FilterContextButton` (a filter toggle is not a
navigation target).

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

## SiblingContextButton

Placed on a **child** view, links sideways to a **sibling** collection — another child of the
same parent — reusing the parent PK from the current URL. It is the composition of
`ParentContextButton` (resolve the parent) and `ChildContextButton` (hop to a named child):
use `ChildContextButton` on the *parent* view and `SiblingContextButton` on its *children*.

```python
from crud_views.lib.view import SiblingContextButton

SiblingContextButton(
    key="articles",                # action key referenced in cv_context_actions
    sibling_name="article",        # registry name of the sibling viewset (same parent)
    sibling_key="list",            # target view key in the sibling viewset (default: "list")
    label_template_code="Articles",
)
```

| Parameter             | Type          | Default  | Description                                       |
|-----------------------|---------------|----------|---------------------------------------------------|
| `key`                 | `str`         | required | Action key referenced in `cv_context_actions`     |
| `sibling_name`        | `str`         | required | Registry name of the sibling viewset (same parent)|
| `sibling_key`         | `str`         | `"list"` | Target view key in the sibling viewset            |
| `label_template`      | `str \| None` | `None`   | Path to a Django template for the button label    |
| `label_template_code` | `str \| None` | `None`   | Inline Django template string for the label       |

Renders nothing when the current view has **no parent**. The URL is built from the current
view's kwargs (the sibling shares the same parent chain), so no current object is required.
Access is checked via the sibling view's `cv_has_access(user, None)` — model-level on the
sibling collection; object-level/Guardian permissions keyed on the parent are not consulted.

### Example

Given `Author` with children `Book` and `Article`:

```python
from crud_views.lib.viewset import ViewSet, ParentViewSet, context_buttons_default
from crud_views.lib.view import SiblingContextButton
from crud_views.lib.views import ListViewPermissionRequired

cv_book = ViewSet(
    model=Book,
    name="book",
    parent=ParentViewSet(name="author"),
    context_buttons=context_buttons_default() + [
        SiblingContextButton(key="articles", sibling_name="article", label_template_code="Articles"),
    ],
)


class BookListView(ListViewPermissionRequired):
    cv_viewset = cv_book
    cv_context_actions = ["parent", "create", "articles"]
```

On `/author/<author_pk>/book/`, the `"articles"` button links to `/author/<author_pk>/article/`.

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

## Manual Placement (Template Tags)

The `cv_context_actions` attribute renders the configured buttons automatically in the view
header. When you build a custom layout — a detail template, a dashboard tile, a card — you can
place a single button (or just its URL) anywhere using template tags. All of them resolve the
same context as the configured buttons, so access and the `cv_action_enabled` state are honored.

| Tag / filter                              | Returns                                              |
|-------------------------------------------|------------------------------------------------------|
| `{% cv_context_button "key" %}`           | Rendered button markup, or **nothing** when no access |
| `{% cv_context_url "key" as url %}`       | The target URL string, or `None` when no access      |
| `view\|cv_context_has_permission:"key"`   | `True`/`False` — may the user access the key?        |

In every case the object defaults to the view's current object; pass a second argument to
target a different object, and unknown keys resolve to nothing/`None` rather than raising.

### `cv_context_url` — get the target URL only

Use `cv_context_url` when you write your own link/tile markup but still want the
permission-gated target URL. It returns the URL string, or `None` when the user lacks access
to the target **or** the action is disabled (`cv_action_enabled` is `False`) — the same
visibility rule as `cv_context_button`:

```django
{% load crud_views %}

{% cv_context_url "update" as edit_url %}
{% if edit_url %}
    <a href="{{ edit_url }}" class="my-tile">Edit</a>
{% endif %}
```

Target a different object by passing it as the second argument:

```django
{% cv_context_url "detail" book as book_url %}
```

!!! note "`None` means hidden"
    Because `cv_context_url` returns `None` for both "no access" and "action disabled", gating
    your markup with `{% if url %}` makes the link disappear entirely — matching
    `cv_context_button`, and unlike the `{% cv_context_actions %}` container, which greys
    inaccessible buttons out instead.

### `cv_context_button` — render the full button

When you want the library to render the complete button markup (not just the URL), use
`cv_context_button`. It renders **nothing** when the user lacks access or the action is
disabled:

```django
{% load crud_views %}

{% cv_context_button "update" %}
```

### `cv_context_has_permission` — gate surrounding markup

To render wrappers, headings, or separators only when the user may access a key, use the
`cv_context_has_permission` filter:

```django
{% load crud_views %}

{% if view|cv_context_has_permission:"update" %}
    <div class="toolbar">{% cv_context_button "update" %}</div>
{% endif %}
```

## Import Paths

```python
from crud_views.lib.view import ContextButton, ParentContextButton, ChildContextButton
from crud_views.lib.viewset import context_buttons_default
```
