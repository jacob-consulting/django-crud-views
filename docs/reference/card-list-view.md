# CardListView

Render objects as cards instead of table rows. Each card shows the object name
and configurable action buttons. The card body template is overridable per view.

## Quick Reference

| View class | Use for |
|---|---|
| `CardListView` | Card grid (no permission check) |
| `CardListViewPermissionRequired` | Card grid with model-level permission check |
| `GuardianCardListViewPermissionRequired` | Card grid with per-object permissions (django-guardian) |

## Minimal Pattern

```python
from crud_views.lib.view import CardAction
from crud_views.lib.views import CardListViewPermissionRequired

class AuthorCardListView(CardListViewPermissionRequired):
    cv_viewset = cv_author
    cv_card_actions = [
        CardAction(key="detail", label="Details", variant="primary", flex=True),
        CardAction(key="update", label="Edit"),
        CardAction(key="delete", no_label=True, variant="tertiary"),
    ]
```

URLs auto-register at `/<prefix>/card/`.

Actions are rendered to match their target view automatically, exactly as table-list actions are:

- A `key` pointing at a **GET** view (detail, update) renders a plain link.
- A `key` pointing at a **POST-only** view — ordered up/down or any custom `ActionView` — renders a hidden POST form plus a submit-form trigger button (no bare GET link, so no `405 Method Not Allowed`).
- A `key` pointing at a **modal-enabled** view (`cv_modal = True`) renders a modal trigger.

You do not configure this on `CardAction`; the method and modal behaviour derive from the target view.

## CardAction Fields

| Field | Type | Default | Description |
|---|---|---|---|
| `key` | `str` | (required) | View key in the ViewSet (`"detail"`, `"update"`, `"delete"`, etc.) |
| `label` | `str \| None` | `None` | Explicit button label. If None, falls back to the target view's short label. |
| `no_label` | `bool` | `False` | Render as icon-only button |
| `variant` | `str` | `"secondary"` | Button style: `"primary"`, `"secondary"`, `"tertiary"` |
| `flex` | `bool` | `False` | If True, button gets `flex-grow-1` |
| `child_name` | `str \| None` | `None` | Child viewset name for cross-viewset links (like `LinkChildColumn`). When set, `key` is ignored for URL resolution. |
| `child_key` | `str` | `"list"` | View key within the child viewset (e.g., `"list"`, `"card"`) |

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

## Child ViewSet Actions

Link to a child viewset from a card button — the card equivalent of `LinkChildColumn` in tables.

```python
from crud_views.lib.view import CardAction

class PublisherCardListView(CardListViewPermissionRequired):
    cv_viewset = cv_publisher
    cv_card_actions = [
        CardAction(key="detail", label="Details", variant="primary", flex=True),
        CardAction(child_name="book", child_key="card", label="Books"),
    ]
```

Child actions always render (no permission check on the card). The target view handles its own permissions. This matches `LinkChildColumn` behavior for tables.

| Field | Required | Description |
|---|---|---|
| `child_name` | Yes | The child viewset's `name` |
| `child_key` | No (default `"list"`) | Which view in the child viewset to link to |
| `label` | Yes (for child actions) | Button text — no auto-label for child actions |

## Custom Card Template

Override `cv_card_template` to render model-specific content:

```python
class ProjektCardListView(CardListViewPermissionRequired):
    cv_viewset = cv_projekt
    cv_card_template = "myapp/tags/projekt_card.html"
    cv_card_actions = [...]
```

The custom template receives `object`, `view`, and `request` in its context.
Use `{% cv_card_action action object %}` to render action buttons:

```html
{% load crud_views %}

<div class="card mb-3">
    <div class="card-body">
        <h5 class="card-title">{{ object.name }}</h5>
        <p>{{ object.description|truncatewords:20 }}</p>
        <div class="d-flex gap-2">
            {% for action in view.cv_card_actions %}
                {% cv_card_action action object %}
            {% endfor %}
        </div>
    </div>
</div>
```

## Filter Integration

Add `ListViewTableFilterMixin` for django-filter support (same pattern as table list views):

```python
from crud_views.lib.views import CardListViewPermissionRequired, ListViewTableFilterMixin

class AuthorCardListView(ListViewTableFilterMixin, CardListViewPermissionRequired):
    cv_viewset = cv_author
    filterset_class = AuthorFilter
    formhelper_class = AuthorFilterFormHelper
    cv_card_actions = [...]
```

### Pinned filter

`CardListView` shares `ListViewTableFilterMixin` with `ListView`, so `cv_filter_pinned = True`
works the same way: the filter renders always-open and the toggle button is hidden. See
[ListView → Always-visible (pinned) filter](list_view.md).

## Ordering

Declare orderable fields with `cv_order_fields`. The card view then renders an
"Order by" combo plus an ascending/descending toggle above the grid.

```python
from crud_views.lib.views import CardListViewPermissionRequired

class BookCardListView(CardListViewPermissionRequired):
    cv_viewset = cv_book
    cv_order_fields = ["title", ("price", "Price")]  # str or (name, label)
    cv_order_default = "title"                        # leading "-" => descending
    cv_card_actions = [...]
```

| Attribute | Type | Default | Description |
|---|---|---|---|
| `cv_order_fields` | `list[str \| tuple[str, str]]` | `[]` | Orderable fields. A string uses the model field's verbose name as the label; a `(name, label)` tuple sets an explicit label. The combo is hidden when empty. |
| `cv_order_default` | `str \| None` | `None` | Ordering applied when no `order` parameter is present. Leading `-` means descending (e.g. `"-created"`). |
| `cv_order_param` | `str` | `"order"` | GET parameter name for the field. Change it if a model field is literally named `order`. |
| `cv_order_dir_param` | `str` | `"dir"` | GET parameter name for the direction (`asc`/`desc`). |

The selected field is **whitelisted** against `cv_order_fields`, so an arbitrary
`?order=` value can never reach `order_by()`. To apply a sort, pick a field and click
the ↑ or ↓ button.

## Paging

Set Django's `paginate_by` to enable pagination. A Bootstrap pagination control renders
below the grid; its links preserve the active filter and order.

```python
class BookCardListView(CardListViewPermissionRequired):
    cv_viewset = cv_book
    paginate_by = 12
    cv_card_actions = [...]
```

## Filter, Order & Paging Coexistence

Filter, order, and page all live in the URL query string and never clobber each other:

- The order toolbar carries the active filter as hidden inputs.
- The filter form carries the active order/direction as hidden inputs.
- Pagination links carry both the filter and the order.

When `cv_filter_persistence` is enabled (the default), the whole query string — filter
**and** order — is stored in the session and restored on the next visit. Resetting the
filter keeps the active order.

## List Key Fallback

When a ViewSet has a `CardListView` but no `ListView`, keys that reference `"list"`
(such as `cv_success_key`, `cv_cancel_key`, and the default "home" context button)
automatically fall back to `"card"`. No manual overrides needed.

This means a ViewSet with only a `CardListView` works out of the box — CreateView,
UpdateView, and DeleteView all redirect to the card view after success.

## Guardian (Per-Object Permissions)

```python
from crud_views_guardian.lib.views import GuardianCardListViewPermissionRequired

class AuthorCardListView(GuardianCardListViewPermissionRequired):
    cv_viewset = cv_author  # must be a GuardianViewSet
    cv_card_actions = [...]
```

The queryset is automatically filtered to objects the user has per-object view permission on.
