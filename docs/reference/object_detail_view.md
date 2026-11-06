# ObjectDetailView

`ObjectDetailView` (and its permission-required variant `ObjectDetailViewPermissionRequired`)
is the rich, structured property-display detail view, shipped as the optional
`crud_views_object_detail` app. It introspects model fields and renders them as configurable
property groups — no custom template required.

!!! example "Try it live"
    The [Object Detail example](https://django-crud-views-demo.onrender.com/object-detail/product/) in the live demo
    shows this in action — log in as `alice` / `alice`. See [Live demo](../getting_started/demo.md) for data resets and wake-up
    time.

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
| `ObjectDetailView` | Complete view: subclass directly for structured rendering (no permission check) |
| `ObjectDetailViewPermissionRequired` | Complete view: subclass directly for structured rendering with model-level permission check |
| `ObjectDetailMixin` | Put first before core `DetailViewPermissionRequired`, `GuardianDetailViewPermissionRequired` or `PolymorphicDetailViewPermissionRequired`; do not prepend to complete object-detail views |

## Minimal Pattern

```python
from crud_views_object_detail.lib import ObjectDetailViewPermissionRequired
from crud_views.lib.viewset import ViewSet
from .models import Book

cv_book = ViewSet(
    model=Book,
    name="book",
    icon_header="fas:book",
)


class BookDetailView(ObjectDetailViewPermissionRequired):
    cv_viewset = cv_book
    cv_property_display = [
        {
            "title": "Basic Info",
            "description": "Core book metadata",
            "icon": "bi:book",
            "properties": [
                "title",
                "author__name",
            ],
        },
    ]
```

## The `cv_property_display` DSL

`cv_property_display` accepts a list of **groups**, or a [model-to-groups mapping](#model-mappings).
Each group is a dict (or `PropertyGroupConfig`) with a title and a list of properties.
Raw and typed groups can be mixed in either order in the same list:

| Parameter     | Description |
|---------------|-------------|
| `title`       | Group heading (required) |
| `description` | Subtitle or help text |
| `icon`        | Icon value: `prefix:name` (`bi:book`, `fas:user`), a semantic name from `CRUD_VIEWS_ICONS`, or a raw CSS class. No auto-prefix; see [Icons](icons.md) |
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
            "title",  # plain string
            {"path": "state_badge", "title": "State"},  # dict
            x("author__name", title="Writer"),  # x() shorthand
            PropertyConfig(path="isbn", detail="ISBN"),  # PropertyConfig
        ],
    },
]
```

| `PropertyConfig` parameter | Description |
|------------|-------------|
| `path`     | Field name or `__`-separated path (required) |
| `title`    | Override the auto-derived label |
| `detail`   | Inherit (`None`), force model help (`True`), suppress (`False`/`""`), or explicit text; see [help precedence](object_detail_settings.md#help-text-precedence) |
| `type`     | Override the auto-detected type (e.g. `"date"`, `"boolean"`) |
| `template` | Path to a custom template for rendering the value |
| `link`     | `LinkConfig` or URL name string (see [Links](object_detail_links.md)) |
| `badge`    | `BadgeConfig` or color string (see [Badges](object_detail_badges.md)) |
| `choices_display` | `True` (default) displays scalar model choice labels; `False` restores raw presentation |

See [Configuration](object_detail_configuration.md) for property-path traversal rules and the
view-callable fallback, [Supported Field Types](object_detail_field_types.md) for the
auto-detected type table, [Links](object_detail_links.md) and [Badges](object_detail_badges.md)
for rendering property values as links/badges, and [Layout Packs](object_detail_layout_packs.md)
for the seven included visual layouts with screenshots.

## Model mappings

To vary groups by the resolved model, set `cv_property_display` to a mapping whose keys are
Django model classes and whose values are group lists. Each value uses the same format as the
ordinary list above: raw dicts, typed `PropertyGroupConfig` objects, or a mixture. Existing typed
group objects are retained. The [complete polymorphic recipe](polymorphic_view.md#basic-usage)
shows declared models, a shared group, subtype fields, the supported view composition and URLs.

Selection uses exactly `type(self.object)` after the view resolves the object. There is no
superclass/MRO search, default key, fallback group list or automatic subtype discovery. If your
view serves a base-model or proxy instance, that exact class needs its own entry. A mapping
missing the actual type raises `django.core.exceptions.ImproperlyConfigured`, naming the model
and qualified view, for example:

```text
myapp.views.VehicleDetailView.cv_property_display has no entry for myapp.Truck
```

An empty mapping `{}` is structurally valid but matches no object at runtime. An explicit entry
such as `{Car: []}` intentionally renders no property groups for that model. The existing empty
list `[]` also renders no groups; `None` still reports missing configuration at startup.

Selection stays local to the view instance and does not mutate the class mapping. It adds no
object or content-type queries; normal property resolution may still query relationships.
The selected list goes through the existing parser, resolver and layout/rendering path.
Ordinary Django model mappings work without installing `django-polymorphic` or
`crud_views_polymorphic`; the optional package is needed only for polymorphic view behavior.

The direct template-tag API `render_object_detail(property_display=...)` continues to accept a
**group list**, not a model mapping. Mapping selection belongs to the view configuration path;
pass a selected list when calling the tag directly.

### Startup checks and runtime boundaries

Checks inspect the declared `cv_property_display` on the class, including every mapping entry.
They validate values even when their keys are invalid. They do not instantiate models or views,
load objects, evaluate `property_display`, or make object queries to select groups. Existing
list diagnostics and inherited view checks continue to apply.

| ID | What is checked |
|----|-----------------|
| `viewset.E240` | `cv_property_display` is declared and not `None` |
| `viewset.E241` | The outer value is a list or mapping, and each mapped value is a list |
| `viewset.E242` | A raw group is a dict with a `title` key |
| `viewset.E243` | A raw group is a dict with a `properties` key |
| `viewset.E244` | A raw group's `properties` value is a list |
| `viewset.E245` | Each property is a string, dict or `PropertyConfig` |
| `viewset.W246` | A raw or typed group icon has no unregistered library prefix |
| `viewset.E247` | Each mapping key is a Django model class |

Mapped diagnostics include the model label, group index and property index where applicable,
for example `cv_property_display[myapp.Truck][1]['properties'][0]`, followed by the view context.
Invalid keys use an entry position and safe type description, such as
`cv_property_display[entry 1 (str)]`, without stringifying model instances.

These are structural checks. They do not resolve property paths, prove that every possible
subtype has an entry, or validate the result of a dynamic override. Typed groups have already
passed their Pydantic validation; raw dicts are parsed at runtime through the same parser.
Test representative real objects and an unmapped-type failure in your application as well.

### Dynamic property escape hatch

Keep a `property_display` override for groups that genuinely depend on the request or object,
rather than only its model. The view reads that effective property once, then applies the same
list/mapping selection and parsing rules. Existing overrides returning lists continue to work:

```python
class VehicleDetailView(ObjectDetailMixin, PolymorphicDetailViewPermissionRequired):
    cv_viewset = cv_vehicle
    cv_property_display = [{"title": "Vehicle", "properties": ["name"]}]

    @property
    def property_display(self):
        if self.request.user.is_staff:
            return [{"title": "Staff view", "properties": ["name", "pk"]}]
        return self.cv_property_display
```

Startup checks still inspect only the declared class configuration; exercise each dynamic
branch separately. For differences based solely on exact model type, use the mapping directly.

## Compose Pattern (Guardian / Polymorphic)

**`ObjectDetailView` and `ObjectDetailViewPermissionRequired` already include
`ObjectDetailMixin`: subclass these complete views directly.** Redundantly prepending the
mixin to either complete view creates an inconsistent MRO and fails at Python class creation,
before Django system checks can run. No extra mixin or runtime detector is needed.

These two independent examples use an existing Book `cv_book` ViewSet:

<!-- object-detail-value-recipe: complete -->
```python
from crud_views_object_detail.lib import ObjectDetailView


class BookDetailView(ObjectDetailView):
    cv_viewset = cv_book
    cv_property_display = [{"title": "Book", "properties": ["title", "publisher__name"]}]
```

<!-- object-detail-value-recipe: complete-permission -->
```python
from crud_views_object_detail.lib import ObjectDetailViewPermissionRequired


class BookDetailView(ObjectDetailViewPermissionRequired):
    cv_viewset = cv_book
    cv_property_display = [{"title": "Book", "properties": ["title", "publisher__name"]}]
```

For a base that does not already include the mixin, put it first. The core composition is:

<!-- object-detail-value-recipe: core -->
```python
from crud_views.lib.views import DetailViewPermissionRequired
from crud_views_object_detail.lib import ObjectDetailMixin


class BookDetailView(ObjectDetailMixin, DetailViewPermissionRequired):
    cv_viewset = cv_book
    cv_property_display = [{"title": "Book", "properties": ["title", "publisher__name"]}]
```

Extension-package detail views (`GuardianDetailViewPermissionRequired`,
`PolymorphicDetailViewPermissionRequired`) are simple template-driven views by default, just
like core `DetailView`. To get rich property-group rendering on them, mix in
`ObjectDetailMixin`:

<!-- object-detail-value-recipe: guardian -->
```python
from crud_views_object_detail.lib import ObjectDetailMixin
from crud_views_guardian.lib.views import GuardianDetailViewPermissionRequired


class BookDetailView(ObjectDetailMixin, GuardianDetailViewPermissionRequired):
    cv_viewset = cv_book  # must be a GuardianViewSet
    cv_property_display = [
        {"title": "Basic Info", "properties": ["title", "publisher__name"]},
    ]
```

Construct that `cv_book` with `GuardianViewSet(model=Book, name="book")`, imported from
`crud_views_guardian.lib.viewset`, to retain object-permission ownership.

<!-- object-detail-value-recipe: polymorphic -->
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

`cv_object_detail_show_help_text = None` inherits
`CRUD_VIEWS_OBJECT_DETAIL_SHOW_HELP_TEXT=False`; a boolean view override selects automatic
terminal-field help. Property instructions win over both. See the exact
[help precedence table](object_detail_settings.md#help-text-precedence), including lazy text,
raw-tag forwarding, cached settings and already-resolved groups.

`crud_views_object_detail` settings (layout pack, text newlines, etc.) are documented in
[ObjectDetailView settings](object_detail_settings.md).
