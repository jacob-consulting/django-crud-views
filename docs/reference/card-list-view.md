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

## CardAction Fields

| Field | Type | Default | Description |
|---|---|---|---|
| `key` | `str` | (required) | View key in the ViewSet (`"detail"`, `"update"`, `"delete"`, etc.) |
| `label` | `str \| None` | `None` | Explicit button label. If None, falls back to the target view's short label. |
| `no_label` | `bool` | `False` | Render as icon-only button |
| `variant` | `str` | `"secondary"` | Button style: `"primary"`, `"secondary"`, `"tertiary"` |
| `flex` | `bool` | `False` | If True, button gets `flex-grow-1` |

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
