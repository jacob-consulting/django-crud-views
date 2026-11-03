# CardListView

Render objects as cards instead of table rows. Each card shows the object name
and configurable action buttons. The card body template is overridable per view.

!!! example "Try it live"
    The [Showcase example](https://django-crud-views-demo.onrender.com/showcase/recipe/) in the live demo shows this in
    action — log in as `alice` / `alice`. See [Live demo](../getting_started/demo.md) for data resets and wake-up time.

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
        CardAction(key="delete", label_mode="icon", variant="tertiary"),
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
| `label_mode` | `str \| None` | `None` | `"label"`, `"icon"` or `"both"`. If None (and `no_label` is not set), the button uses the effective view mode, including instance choices and the class-level `cv_get_card_actions_label_mode()` fallback. The action's `cv_label_mode` records the result. See [Card label-mode resolution](action_menus.md#card-label-mode-resolution). |
| `no_label` | `bool` | `False` | Superseded by `label_mode="icon"`, which it equals. Setting it together with `label_mode` is a validation error. |
| `variant` | `str \| None` | `None` | Button style: `"primary"`, `"secondary"`, `"tertiary"`, `"danger"`. If None, falls back to the target view's `cv_action_variant` (`primary` for create, `danger` for delete, else `secondary`). See [Buttons](buttons.md#variants). |
| `flex` | `bool` | `False` | If True, the button gets the `card:flex` classes (`flex-grow-1` by default) |
| `child_name` | `str \| None` | `None` | Child viewset name for cross-viewset links (like `LinkChildColumn`). When set, `key` is ignored for URL resolution. |
| `child_key` | `str` | `"list"` | View key within the child viewset (e.g., `"list"`, `"card"`) |

## Label mode

`label_mode` decides how an inline card button shows its label:

| Mode | Renders |
|---|---|
| `"label"` | the text only |
| `"icon"` | the icon only; the label becomes a visually hidden text and the `title` tooltip |
| `"both"` | the icon followed by the text |

To set one look for every card page of the project, use the setting; the package card floor is `"both"`:

```python
# settings.py
CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"card": "label"}
```

See [Label-mode configuration](settings.md#label-mode-configuration) for the setting. A view attribute overrides
it for one view, and `CardAction.label_mode` overrides both for one button:

| Attribute | Type | Default | Description |
|---|---|---|---|
| `cv_card_actions_label_mode` | `str \| None` | `None` | Label mode of every card action without its own `label_mode`. None uses the `"card"` entry of `CRUD_VIEWS_LABEL_MODE_DEFAULTS`, else `"both"` |

The raw attribute stays `None` unless a view sets it. The public classmethod `cv_get_card_actions_label_mode()`
resolves class-level configuration and stays callable on the class. Calling it through an instance still reads
class configuration; it does not incorporate instance or per-action choices. Read the effective per-action
`cv_label_mode` returned by `cv_get_card_action_data()` or stamped on the button context in a template.

Django's `as_view()` can select a mode for one URL configuration:

```python
card_view = ProjectCardListView.as_view(cv_card_actions_label_mode="label")
```

For a per-request choice, assign `self.cv_card_actions_label_mode` in `setup`, `dispatch` or `get_queryset`.
Assigning `None` opts that instance into the project floor even when the class sets a mode. Each request keeps its
own choice; the class attribute is unchanged. Subclass resolver overrides remain fallback hooks for instances
without their own value.

How explicit choices and defaults combine is described in
[Card label-mode resolution](action_menus.md#card-label-mode-resolution). For cards,
`CardAction(no_label=True)` currently still renders icon-only, ahead of the view attribute and the setting. An action
with an empty label is always rendered `"icon"`, and a `"both"` button whose view has no icon renders like `"label"`.
`viewset.E210` rejects an unknown `label_mode`, or a `cv_card_actions_label_mode` that is set but not exactly
`"label"`, `"icon"` or `"both"`.

Toolbar and row buttons have their own, key-based knob — a map of action key to mode in settings, on the ViewSet or
on the view; see [Action menus](action_menus.md#label-mode).

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

Child actions check the child view's permission (`cv_has_access` and `cv_action_enabled` on the `child_key` view of
the child ViewSet), like `ChildContextButton`. A user who may not open the child view does not see the button, or sees
it disabled when the child view resolves to `"disable"` (see [Hide or disable inaccessible actions](inaccessible_actions.md)).
Before 0.28.0 child actions always rendered and the target view answered with 403. `LinkChildColumn` in tables still
renders without a permission check. With a `GuardianViewSet` child, the child list view's `cv_has_access` is always
`True` (access to the parent is checked per request), so such child card actions keep rendering — the same as
`ChildContextButton`.

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

The template receives `object`, `view`, and `request` in its context. Extend the stock card and fill only the blocks
you need; the card's actions (inline buttons and overflow menu) keep rendering without being repeated:

```html
{% extends "crud_views/tags/card.html" %}

{% block card_title %}{{ object.name }}{% endblock card_title %}

{% block card_content %}
    <p>{{ object.description|truncatewords:20 }}</p>
{% endblock card_content %}
```

| Block | Default | Contains |
|---|---|---|
| `card_title` | `{{ object }}` | the text of the `<h5>` heading |
| `card_content` | empty | anything between the heading and the actions, inside the card body |
| `card_actions` | the menu's hidden action forms and the actions container | override only to move or drop the actions |

The card's own classes are keys in the [button class table](buttons.md): `card:root` (`card mb-3`), `card:body`
(`card-body`) and `card:title` (`card-title`); the actions container is `card:container`. A theme that puts the actions
in a footer overrides `crud_views/tags/card.html` with its own structure and keeps the three block names, so a
project template that extends `crud_views/tags/card.html` works unchanged under that theme.

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

Declare orderable fields with `cv_order_fields`. Depending on how the entries are
written, the card view renders one of two toolbars above the grid.

### Signed choices (single combo, no buttons)

Prefix a field name with `-` (descending) or `+` (ascending) and the direction becomes
part of the choice. The toolbar is then a single "Order by" combo that submits as soon
as a choice is picked. No ascending/descending buttons are rendered.

```python
from crud_views.lib.views import CardListViewPermissionRequired


class BookCardListView(CardListViewPermissionRequired):
    cv_viewset = cv_book
    cv_order_fields = [
        ("-created", "Newest first"),
        ("+created", "Oldest first"),
        ("title", "Title A-Z"),  # plain name in signed mode == ascending
        "-title",  # auto-labelled "Title (descending)"
    ]
    cv_order_default = "-created"
    cv_card_actions = [...]
```

- A list is in **signed mode** as soon as one entry starts with `+` or `-`. Plain names
  in a signed list mean ascending.
- The URL carries the direction in the value: `?order=-created`. Ascending is always
  emitted as the bare name (`?order=created`), never `+created`, because a literal `+`
  in a query string decodes to a space. The `dir` parameter is ignored in signed mode.
- The whitelist is exact: with only `-created` declared, `?order=created` is rejected and
  the default ordering applies.
- The combo preselects the active choice, including the `cv_order_default` when no
  `order` parameter is present.
- Auto-labels for bare signed strings are built from the field's verbose name plus a
  translated "(ascending)" / "(descending)" suffix.
- The auto-submit is wired by `viewset.js` through `data-cv-action="submit-on-change"`,
  so it works under a strict CSP without inline handlers.

### Field plus direction buttons

Plain names keep the classic toolbar: an "Order by" combo plus an ascending/descending
button pair. To apply a sort, pick a field and click the ↑ or ↓ button.

```python
class BookCardListView(CardListViewPermissionRequired):
    cv_viewset = cv_book
    cv_order_fields = ["title", ("price", "Price")]  # str or (name, label)
    cv_order_default = "title"  # leading "-" => descending
    cv_card_actions = [...]
```

### Attributes

| Attribute | Type | Default | Description |
|---|---|---|---|
| `cv_order_fields` | `list[str \| tuple[str, str]]` | `[]` | Orderable fields. A string uses the model field's verbose name as the label; a `(name, label)` tuple sets an explicit label. A `+`/`-` prefix on the name encodes the direction and switches the view to signed mode. The combo is hidden when empty. |
| `cv_order_default` | `str \| None` | `None` | Ordering applied when no valid `order` parameter is present. Leading `-` means descending (e.g. `"-created"`). |
| `cv_order_param` | `str` | `"order"` | GET parameter name for the field (signed mode: the signed value). Change it if a model field is literally named `order`. |
| `cv_order_dir_param` | `str` | `"dir"` | GET parameter name for the direction (`asc`/`desc`). Only used with plain names. |

The selected value is **whitelisted** against `cv_order_fields`, so an arbitrary
`?order=` value can never reach `order_by()`.

## Paging

Set Django's `paginate_by` to enable pagination. A Bootstrap pagination control renders
below the grid; its links preserve the active filter and order.

The previous and next arrows are the `page-previous` and `page-next` [icons](icons.md), so a theme swaps them through
`CRUD_VIEWS_ICONS` or `register_icons()` without overriding the template. Each arrow carries a visually hidden,
translated label; the current page has `aria-current="page"`, and a disabled end is a link without `href` and with
`aria-disabled="true"`.

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
(such as `cv_success_key`, `cv_success_keys`, `cv_cancel_key`, `cv_cancel_keys`, and the default "home"
context button) automatically fall back to `"card"`. No manual overrides needed. Card actions carry the
`card` origin key into views that list it in `cv_cancel_keys` or `cv_success_keys`
(see [Dynamic cancel target](update_view.md#dynamic-cancel-target)).

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

!!! tip "Many actions?"
    Fold the less common actions into a `⋯` dropdown: see [Action menus](action_menus.md).
