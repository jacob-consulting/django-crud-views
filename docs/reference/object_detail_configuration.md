# Configuration

## Property Paths

Properties are referenced by field name. Use `__` to traverse relationships:

```python
"properties": [
    "title",                    # simple field
    "author__name",             # FK traversal
    "author__country__code",    # multi-hop FK
    "tags",                     # M2M (renders all related objects)
    "get_absolute_url",         # method or property
]
```

## The `x()` Helper

For more control over individual properties, use the `x()` shorthand to build a `PropertyConfig`:

```python
from crud_views_object_detail.lib import x

"properties": [
    "title",
    x("author__name", title="Writer"),
    x("published_date", detail="When the book was first published"),
    x("rating", type="integer"),
    x("notes", template="myapp/custom_notes.html"),
]
```

| Parameter  | Description |
|------------|-------------|
| `path`     | Field name or `__`-separated path (required) |
| `title`    | Override the auto-derived label |
| `detail`   | Help text shown below the value |
| `type`     | Override the auto-detected type (e.g. `"date"`, `"boolean"`) |
| `template` | Path to a custom template for rendering the value |
| `link`     | `LinkConfig` or URL name string (see [Links](object_detail_links.md)) |
| `badge`    | `BadgeConfig` or color string (see [Badges](object_detail_badges.md)) |

## Groups

Each entry in `cv_property_display` is a group with a title and a list of properties:

```python
cv_property_display = [
    {
        "title": "Basic Info",
        "description": "Core book metadata",
        "icon": "bi bi-book",
        "properties": [
            "title",
            "author__name",
            x("isbn", detail="International Standard Book Number"),
        ],
    },
]
```

| Parameter     | Description |
|---------------|-------------|
| `title`       | Group heading (required) |
| `description` | Subtitle or help text |
| `icon`        | CSS class for an icon (e.g. Bootstrap Icons) |
| `properties`  | List of strings, dicts, or `PropertyConfig` objects |

Properties can be mixed freely — plain strings, dicts with `PropertyConfig` fields, or `x()` / `PropertyConfig` instances.

## View-Callable Fallback

If a `path` cannot be resolved on the model instance (the first segment is not an attribute or method on the instance), the resolver will try to call `view.<path>(instance)` instead.

This lets you compute display values using view-level context (e.g. `self.request`, view kwargs, or logic that doesn't belong on the model):

```python
from crud_views_object_detail.lib import ObjectDetailViewPermissionRequired

class BookDetailView(ObjectDetailViewPermissionRequired):
    cv_viewset = cv_book
    cv_property_display = [
        {
            "title": "View-Computed",
            "properties": [
                x("view_computed_summary", title="Summary"),
            ],
        },
    ]

    def view_computed_summary(self, instance):
        return f"{instance.title} by {instance.author_list()} ({instance.pages} pages)"
```

**Rules:**

- The view method must be callable — non-callable attributes on the view are ignored (value becomes `None`)
- If the path **is** found on the model (even as `None`), the view fallback never runs — model always takes priority
- This works automatically when using `ObjectDetailView` / `ObjectDetailMixin`, or when using the
  `{% render_object_detail %}` template tag from within a Django CBV template (Django adds `view`
  to context via `ContextMixin`)
