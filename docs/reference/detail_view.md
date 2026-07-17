# DetailView

`DetailView` displays a single model instance with a fully custom template — you provide the
entire template yourself. It does not introspect model fields or render structured property
groups.

!!! note "Looking for structured property-display detail?"
    Rich, structured property-group rendering (previously built into core `DetailView`) now
    lives in the optional `crud_views_object_detail` app as `ObjectDetailView`
    (`from crud_views_object_detail.lib import ObjectDetailView`). Add `crud_views_object_detail`
    to `INSTALLED_APPS` and use `cv_property_display` on `ObjectDetailView` for that use case.

## Quick Reference

| View class | Use for |
|---|---|
| `DetailView` | Custom detail template (no permission check) |
| `DetailViewPermissionRequired` | Custom detail template with model-level permission check |
| `GuardianDetailViewPermissionRequired` | Custom detail template with per-object permissions (django-guardian) |

## Minimal Pattern

```python
from crud_views.lib.views import DetailViewPermissionRequired
from crud_views.lib.viewset import ViewSet
from .models import Book

cv_book = ViewSet(
    model=Book,
    name="book",
    icon_header="fa-regular fa-book",
)


class BookDetailView(DetailViewPermissionRequired):
    cv_viewset = cv_book
    template_name = "myapp/book_detail.html"
```

The template receives `object`, `view`, and `cv_extends` in its context:

```html
{% extends cv_extends %}

{% block cv_content %}
<h2>{{ object.title }}</h2>
<p>{{ object.description }}</p>
{% endblock cv_content %}
```

## Guardian (Per-Object Permissions)

```python
from crud_views_guardian.lib.views import GuardianDetailViewPermissionRequired

class BookDetailView(GuardianDetailViewPermissionRequired):
    cv_viewset = cv_book  # must be a GuardianViewSet
    template_name = "myapp/book_detail.html"
```
