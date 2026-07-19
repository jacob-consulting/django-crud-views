# Breadcrumb

`CrudViewBreadcrumbMixin` adds a Bootstrap 5.3 breadcrumb to any CrudView. The trail follows
the ViewSet hierarchy — `[prefix] › container › (ancestors …) › object › action` — and
respects nested ViewSets: for a chain Company › Department › Employee, an employee's update
page shows `Companies › ACME › Departments › Sales › Employees › Jane Doe › Edit`.

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
class MyBreadcrumbMixin(CrudViewBreadcrumbMixin):
    def cv_breadcrumb_prefix(self):
        return super().cv_breadcrumb_prefix() + [
            BreadcrumbItem(title=self.request.user.team.name, url_name="team-home"),
        ]
```

## Reference

| Member | Default | Description |
|---|---|---|
| `cv_breadcrumb_key_object` | `"detail"` | View key object items link to. A typo'd override triggers check `viewset.W270`. |
| `cv_breadcrumb_container_label` | `None` | Overrides the container (list/card) label; set it on the container view — it also applies where the viewset appears as an ancestor. |
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
