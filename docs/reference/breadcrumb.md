# Breadcrumb

`CrudViewBreadcrumbMixin` adds a Bootstrap 5.3 breadcrumb to any CrudView. The trail follows
the ViewSet hierarchy — `[prefix] › (ancestors …) › container › object › action` — and
respects nested ViewSets: for a chain Company › Department › Employee, an employee's update
page shows `Companies › ACME › Departments › Sales › Employees › Jane Doe › Edit`.

!!! example "Try it live"
    The [Breadcrumbs example](https://django-crud-views-demo.onrender.com/breadcrumbs/workspace/) in the live demo shows this in
    action — log in as `alice` / `alice`. See [Live demo](../getting_started/demo.md) for data resets and wake-up time.

## Usage

```python
from crud_views.lib.breadcrumb import CrudViewBreadcrumbMixin
from crud_views.lib.views import DetailViewPermissionRequired


class EmployeeDetailView(CrudViewBreadcrumbMixin, DetailViewPermissionRequired):
    cv_viewset = cv_employee
```

Render it in your `CRUD_VIEWS_EXTENDS` template:

```html
{% load crud_views %}
{% cv_breadcrumb %}
```

The tag renders nothing when the current view does not use the mixin, so it is safe to place
unconditionally. The last item is always rendered as the active, unlinked current page
(Bootstrap/ARIA convention).

## Hooking into your site navigation

The breadcrumb covers the crud-views hierarchy only; leading items for your host
application come from either:

**Setting** (global default):

```python
CRUD_VIEWS_BREADCRUMB_PREFIX = [
    {"title": "Home", "url_name": "home"},
    {"title": "Admin area", "url_name": "admin-dashboard"},
]
```

**Method override** (dynamic, e.g. per request):

```python
from crud_views.lib.breadcrumb import BreadcrumbItem, CrudViewBreadcrumbMixin


class MyBreadcrumbMixin(CrudViewBreadcrumbMixin):
    def cv_breadcrumb_prefix(self):
        return super().cv_breadcrumb_prefix() + [
            BreadcrumbItem(title=self.request.user.team.name, url_name="team-home"),
        ]
```

## Current-page label

The last item of an action page (create, update, delete, …) is the view's short action label, the same text as
every button that opens the view. When the breadcrumb should read differently, set a breadcrumb label on the view:

```python
class NoteCreateView(CrudViewBreadcrumbMixin, CreateView):
    cv_viewset = cv_note
    cv_action_short_label_template_code = "New note"  # every button pointing here
    cv_breadcrumb_label_template_code = "Create"  # Notes › Create
```

The template gets the same variables as the short label: `verbose_name`, `verbose_name_plural` (and their
`*_translate` variants), `viewset`, and `object` on object views (`"Edit {{ object }}"`). It labels the view's own
item only, so it has no effect on detail and container (list/card) views, which have none.

## Reference

| Member | Default | Description |
|---|---|---|
| `cv_breadcrumb_key_object` | `"detail"` | View key object items link to. A typo'd override triggers check `viewset.W270`. |
| `cv_breadcrumb_container_label` | `None` | Overrides the container (list/card) label; set it on the container view — it also applies where the viewset appears as an ancestor. |
| `cv_breadcrumb_label_template` / `cv_breadcrumb_label_template_code` | `None` | Label of the view's own current-page item, as a template snippet or template code (code wins). Unset, the view's short action label is used. A missing template triggers check `viewset.E111`. |
| `cv_get_breadcrumb_label(context)` | short label | Classmethod rendering the current-page label. |
| `cv_breadcrumb_prefix()` | reads setting | Returns the leading `BreadcrumbItem` list. |
| `cv_breadcrumb_object_label(obj)` | `str(obj)` | Label for object items. |
| `cv_breadcrumb_get()` | — | Builds the `Breadcrumb`; override for full control. |

`BreadcrumbItem(title, url_name=None, args=(), kwargs={})` resolves its URL lazily via
`reverse()`; `title` accepts `gettext_lazy` strings. Pass `args` or `kwargs`, not both.

## Behavior notes

- Viewsets without a detail view render object items without a link; card-only viewsets use
  the card view as container.
- Each ancestor level costs one database query, scoped to the URL's parent chain — a
  tampered parent pk in the URL yields 404. The trail is built once per request.
