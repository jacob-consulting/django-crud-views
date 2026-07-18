# ObjectDetailView

`ObjectDetailView` (and its permission-required variant `ObjectDetailViewPermissionRequired`)
is the rich, structured property-display detail view, shipped as the optional
`crud_views_object_detail` app. It introspects model fields and renders them as configurable
property groups — no custom template required.

For a simple, fully-custom-template detail view, see [DetailView](detail_view.md).

## Installation

Add `crud_views_object_detail` to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    "crud_views_object_detail",
]
```

No migrations are required.

## Quick Reference

| View class | Use for |
|---|---|
| `ObjectDetailView` | Structured property-group detail rendering (no permission check) |
| `ObjectDetailViewPermissionRequired` | Structured property-group detail rendering with model-level permission check |
| `ObjectDetailMixin` | Composable mixin — mix into `GuardianDetailViewPermissionRequired` / `PolymorphicDetailViewPermissionRequired` for rich detail on extension-package views |

## Minimal Pattern

```python
from crud_views_object_detail.lib import ObjectDetailViewPermissionRequired
from crud_views.lib.viewset import ViewSet
from .models import Book

cv_book = ViewSet(
    model=Book,
    name="book",
    icon_header="fa-regular fa-book",
)


class BookDetailView(ObjectDetailViewPermissionRequired):
    cv_viewset = cv_book
    cv_property_display = [
        {
            "title": "Basic Info",
            "description": "Core book metadata",
            "icon": "bi bi-book",
            "properties": [
                "title",
                "author__name",
            ],
        },
    ]
```

## The `cv_property_display` DSL

`cv_property_display` is a list of **groups**. Each group is a dict (or `PropertyGroupConfig`)
with a title and a list of properties:

| Parameter     | Description |
|---------------|-------------|
| `title`       | Group heading (required) |
| `description` | Subtitle or help text |
| `icon`        | CSS class for an icon (e.g. Bootstrap Icons) |
| `properties`  | List of strings, dicts, or `PropertyConfig` objects |

Each entry in `properties` can be:

- a **plain string** — field name or `__`-separated path (`"title"`, `"author__name"`)
- a **dict** with `PropertyConfig` fields (`{"path": "state_badge", "title": "State"}`)
- an `x()` shorthand call, or a `PropertyConfig` instance directly

```python
from crud_views_object_detail.lib import x, PropertyConfig

cv_property_display = [
    {
        "title": "Basic Info",
        "properties": [
            "title",                                          # plain string
            {"path": "state_badge", "title": "State"},        # dict
            x("author__name", title="Writer"),                # x() shorthand
            PropertyConfig(path="isbn", detail="ISBN"),        # PropertyConfig
        ],
    },
]
```

| `PropertyConfig` parameter | Description |
|------------|-------------|
| `path`     | Field name or `__`-separated path (required) |
| `title`    | Override the auto-derived label |
| `detail`   | Help text shown below the value |
| `type`     | Override the auto-detected type (e.g. `"date"`, `"boolean"`) |
| `template` | Path to a custom template for rendering the value |
| `link`     | `LinkConfig` or URL name string (see [Links](object_detail_links.md)) |
| `badge`    | `BadgeConfig` or color string (see [Badges](object_detail_badges.md)) |

See [Configuration](object_detail_configuration.md) for property-path traversal rules and the
view-callable fallback, [Supported Field Types](object_detail_field_types.md) for the
auto-detected type table, [Links](object_detail_links.md) and [Badges](object_detail_badges.md)
for rendering property values as links/badges, and [Layout Packs](object_detail_layout_packs.md)
for the seven included visual layouts with screenshots.

## Compose Pattern (Guardian / Polymorphic)

Extension-package detail views (`GuardianDetailViewPermissionRequired`,
`PolymorphicDetailViewPermissionRequired`) are simple template-driven views by default, just
like core `DetailView`. To get rich property-group rendering on them, mix in
`ObjectDetailMixin`:

```python
from crud_views_object_detail.lib import ObjectDetailMixin
from crud_views_guardian.lib.views import GuardianDetailViewPermissionRequired


class BookDetailView(ObjectDetailMixin, GuardianDetailViewPermissionRequired):
    cv_viewset = cv_book  # must be a GuardianViewSet
    cv_property_display = [
        {"title": "Basic Info", "properties": ["title", "author__name"]},
    ]
```

```python
from crud_views_object_detail.lib import ObjectDetailMixin
from crud_views_polymorphic.lib import PolymorphicDetailViewPermissionRequired


class VehicleDetailView(ObjectDetailMixin, PolymorphicDetailViewPermissionRequired):
    cv_viewset = cv_vehicle
    cv_property_display = [
        {"title": "Attributes", "properties": ["name"]},
    ]
```

`ObjectDetailMixin` must come first in the MRO so it can override `get_context_data` and
`cv_content_template` / `cv_modal_supported` ahead of the base view.

## Modal Support

Unlike core `DetailView`, `ObjectDetailView` sets `cv_modal_supported = True` and can opt in to
Bootstrap 5 modal rendering — see [Modals](modals.md).

## Settings

`crud_views_object_detail` settings (layout pack, icon library, etc.) are documented in
[ObjectDetailView settings](object_detail_settings.md).
