# DetailCustomView

A detail view for displaying a single object with a fully custom template. Unlike
[`DetailView`](detail_view.md), it does **not** use `ObjectDetailMixin` or
`cv_property_display` — you provide the entire template yourself.

## Quick Reference

| View class | Use for |
|---|---|
| `DetailCustomView` | Custom detail template (no permission check) |
| `DetailCustomViewPermissionRequired` | Custom detail template with model-level permission check |
| `GuardianDetailCustomViewPermissionRequired` | Custom detail template with per-object permissions (django-guardian) |

## When to Use

- **`DetailView`** — when you want structured property groups rendered automatically
  via django-object-detail. Configure `cv_property_display` and you're done.
- **`DetailCustomView`** — when you need full control over the detail page layout.
  You provide a custom `template_name` with your own HTML.

Both register with `cv_key = "detail"` and `cv_path = "detail"` — they fill the
same role in a ViewSet. Use one or the other, not both.

## Minimal Pattern

```python
from crud_views.lib.views import DetailCustomViewPermissionRequired

class BookDetailView(DetailCustomViewPermissionRequired):
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
from crud_views_guardian.lib.views import GuardianDetailCustomViewPermissionRequired

class BookDetailView(GuardianDetailCustomViewPermissionRequired):
    cv_viewset = cv_book  # must be a GuardianViewSet
    template_name = "myapp/book_detail.html"
```

## Class Hierarchy

`DetailCustomView` is the base class for `DetailView`:

```
DetailCustomView          ← custom template, no ObjectDetailMixin
└── DetailView            ← adds ObjectDetailMixin + cv_property_display
```

Both share the same key, path, icons, and snippet templates.
