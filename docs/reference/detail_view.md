# DetailView

The `DetailView` displays the properties of a single model instance. It uses
[django-object-detail](https://django-object-detail.readthedocs.io/en/latest/)
for rendering property groups.

## Basic Usage

```python
from crud_views.lib.views import DetailViewPermissionRequired
from crud_views.lib.viewset import ViewSet
from .models import Author

cv_author = ViewSet(
    model=Author,
    name="author",
    pk=ViewSet.PK.UUID,
    icon_header="fa-regular fa-user",
)


class AuthorDetailView(DetailViewPermissionRequired):
    cv_viewset = cv_author

    property_display = [
        {
            "title": "Attributes",
            "icon": "tag",
            "description": "Core author information",
            "properties": [
                "full_name",
                "first_name",
                "last_name",
            ],
        },
    ]
```

## `property_display`

The `property_display` attribute is a list of groups. Each group is a dictionary with the
following keys:

| Key            | Required | Description                                            |
|----------------|----------|--------------------------------------------------------|
| `title`        | yes      | Group heading                                          |
| `icon`         | no       | Icon name (resolved by django-object-detail, see below)|
| `description`  | no       | Subtitle shown below the group heading                 |
| `properties`   | yes      | List of properties to display                          |

### Properties

Each entry in `properties` can be:

- a **string** — the field name or `@property` method name
- a **dict** — with `path` (required) and optional overrides
- a **`PropertyConfig`** or **`x()`** instance from django-object-detail

```python
from django_object_detail import x

property_display = [
    {
        "title": "Attributes",
        "properties": [
            "first_name",                                      # simple field
            "full_name",                                       # model @property
            {"path": "id", "title": "UUID"},                   # dict with title override
            {"path": "book_count", "detail": "Total books"},   # dict with detail tooltip
            x("rating", badge="success"),                      # x() helper with badge
        ],
    },
]
```

### Property Options

| Key        | Description                                               |
|------------|-----------------------------------------------------------|
| `path`     | Field name or `__`-separated path for FK traversal        |
| `title`    | Override the auto-derived label                           |
| `detail`   | Help text shown as tooltip next to the value              |
| `type`     | Override auto-detected type (e.g. `"date"`, `"boolean"`)  |
| `template` | Path to a custom template for rendering the value         |
| `link`     | URL name string or `LinkConfig` for clickable values      |
| `badge`    | Color string or `BadgeConfig` for badge rendering         |

### FK and M2M Traversal

Use `__` to traverse relationships:

```python
"properties": [
    "author",                      # ForeignKey (renders str())
    "author__email",               # FK field traversal
    "author__country__name",       # multi-hop FK
    "tags",                        # ManyToMany (renders all related objects)
]
```

## Configuring django-object-detail

Add `django_object_detail` to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ...
    "django_object_detail",
    "crud_views",
    # ...
]
```

Then configure the layout and icons in your Django settings:

```python
# Layout pack — controls how groups and properties are rendered
OBJECT_DETAIL_TEMPLATE_PACK_LAYOUT = "split-card"

# Type templates — controls how individual field types are rendered
OBJECT_DETAIL_TEMPLATE_PACK_TYPES = "default"
```

### Layout Packs

django-object-detail ships with seven layout packs:

| Pack                 | Setting value       | Description                                  |
|----------------------|---------------------|----------------------------------------------|
| Split card (default) | `"split-card"`      | Title on the left, properties on the right   |
| Accordion            | `"accordion"`       | Collapsible panels per group                 |
| Tabs (vertical)      | `"tabs-vertical"`   | Vertical tabs with property content area     |
| Card rows            | `"card-rows"`       | Standalone card per group with stacked rows  |
| Striped rows         | `"striped-rows"`    | Alternating row backgrounds                  |
| Table inline         | `"table-inline"`    | Classic table with label and value columns   |
| List group (3-col)   | `"list-group-3col"` | Three-column list: label, value, and detail  |

### Icon Configuration

When using Font Awesome (recommended with Bootstrap 5):

```python
OBJECT_DETAIL_ICONS_LIBRARY = "fontawesome"
OBJECT_DETAIL_ICONS_TYPE = "solid"  # or "regular", "light", "thin", "duotone"
```

With this configuration, icon names in `property_display` are short names like `"tag"`, `"book"`,
or `"circle-info"`, and django-object-detail builds the full CSS class automatically
(e.g. `fa-solid fa-tag`).

When using Bootstrap Icons (the default):

```python
OBJECT_DETAIL_ICONS_LIBRARY = "bootstrap"
```

Icon names then follow Bootstrap Icons conventions (e.g. `"book"` becomes `bi bi-book`).

### All Settings

| Setting                              | Default        | Description                          |
|--------------------------------------|----------------|--------------------------------------|
| `OBJECT_DETAIL_TEMPLATE_PACK_LAYOUT` | `"split-card"` | Layout pack for group/property structure |
| `OBJECT_DETAIL_TEMPLATE_PACK_TYPES`  | `"default"`    | Type template pack for value rendering   |
| `OBJECT_DETAIL_ICONS_LIBRARY`        | `"bootstrap"`  | Icon library: `"bootstrap"` or `"fontawesome"` |
| `OBJECT_DETAIL_ICONS_CLASS`          | per library    | Base CSS class (`"bi"` or `"fa"`)        |
| `OBJECT_DETAIL_ICONS_TYPE`           | per library    | Icon type (`None` for Bootstrap, `"regular"` for FA) |
| `OBJECT_DETAIL_ICONS_PREFIX`         | per library    | Icon name prefix (`"bi"` or `"fa"`)     |
| `OBJECT_DETAIL_NAMED_ICONS`         | per library    | Dict mapping named icons to icon names   |

For the full django-object-detail documentation, see
[django-object-detail.readthedocs.io](https://django-object-detail.readthedocs.io/en/latest/).

## Complete Example

A model with a `@property`:

```python
from django.db import models

class Author(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    pseudonym = models.CharField(max_length=100, blank=True, null=True)
    created_dt = models.DateTimeField(auto_now_add=True)
    modified_dt = models.DateTimeField(auto_now=True)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def book_count(self):
        return self.book_set.count()
```

The detail view:

```python
from django.utils.translation import gettext as _
from crud_views.lib.views import DetailViewPermissionRequired
from crud_views.lib.viewset import ViewSet

cv_author = ViewSet(
    model=Author,
    name="author",
    pk=ViewSet.PK.UUID,
    icon_header="fa-regular fa-user",
)


class AuthorDetailView(DetailViewPermissionRequired):
    cv_viewset = cv_author

    property_display = [
        {
            "title": _("Attributes"),
            "icon": "tag",
            "description": _("Core author information"),
            "properties": [
                {"path": "full_name", "detail": _("Computed from first and last name")},
                "first_name",
                "last_name",
            ],
        },
        {
            "title": _("Extra"),
            "icon": "circle-info",
            "description": _("Additional metadata and computed values"),
            "properties": [
                {"path": "id", "title": "UUID", "detail": _("Unique identifier")},
                "pseudonym",
                {"path": "book_count", "detail": _("Total number of books by this author")},
            ],
        },
    ]
```

Settings (`settings.py`):

```python
INSTALLED_APPS = [
    # ...
    "django_object_detail",
    "crud_views",
    "crud_views_bootstrap5",
    # ...
]

OBJECT_DETAIL_TEMPLATE_PACK_LAYOUT = "split-card"
OBJECT_DETAIL_TEMPLATE_PACK_TYPES = "default"
OBJECT_DETAIL_ICONS_LIBRARY = "fontawesome"
OBJECT_DETAIL_ICONS_TYPE = "solid"
```