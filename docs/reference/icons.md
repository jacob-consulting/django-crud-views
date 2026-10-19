# Icons

django-crud-views refers to every icon it renders by a **semantic name** (`detail`, `delete`, `filter`, ...), never by a
library class. What a name looks like comes from a layered table (package defaults, then theme, then your settings), and
how an icon becomes HTML is decided by a renderer registered per **library prefix**. Everything renders through one
template tag, `{% cv_icon %}`.

The public module is `crud_views.lib.icons`.

## Icon values

Wherever the package accepts an icon (`cv_icon_action`, `cv_icon_header`, `ViewSet(icon_header=...)`, the `icon` of an
object detail group, the `CRUD_VIEWS_ICONS` table) the value is a string in one of three forms. They are tried in this
order:

1. **Semantic name** - no colon and present in the resolved icon table (`"detail"`, `"person"`). The table value is
   looked up and then read as either a `prefix:name` value or, when it has no colon, a raw CSS class. Only one lookup
   step is made: a table entry pointing to
   another semantic name is not followed (system check `crud_views.W352` flags it).
2. **`prefix:name`** - `prefix` is looked up in the library registry and its renderer receives `name`
   (`far:eye`, `bi:person`, `xy:rocket`).
3. **Raw CSS class** - anything else without a colon (`"fa-solid fa-truck"`) renders as `<i class="...">`.

An empty value or `None` renders nothing.

!!! warning "Colons and raw classes"
    A value containing a colon is always read as `prefix:name`. A raw CSS class that contains a colon (for example a
    Tailwind variant such as `hover:text-red-500`) therefore does not work as a raw class: the part before the colon
    is taken as a library prefix. This also applies to a `CRUD_VIEWS_ICONS` value, so `"x": "hover:text-red-500"` does
    not work either. The only route is a registered library, for example
    `{"tw": {"renderer": "font", "class": "{name}"}}` used as `tw:hover:text-red-500`, or a custom renderer. A value
    with an unknown prefix renders nothing, and the system checks `crud_views.W352` / `crud_views.W353` warn about it.

Icons are rendered with `aria-hidden="true"`; labels are provided as visually hidden text where needed.

## Default table

The defaults use free Font Awesome 6 only (the `far` and `fas` prefixes). Load Font Awesome in your base template
yourself.

| Name | Default | Used for |
|---|---|---|
| `list` | `far:rectangle-list` | list view action |
| `card` | `fas:rectangle-list` | card list view action |
| `detail` | `far:eye` | detail view action |
| `create` | `far:square-plus` | create view action |
| `update` | `far:pen-to-square` | update view action |
| `delete` | `far:trash-can` | delete view action |
| `order-up` | `far:circle-up` | ordered view, move up |
| `order-down` | `far:circle-down` | ordered view, move down |
| `manage` | `fas:gear` | manage view action and header |
| `workflow` | `fas:diagram-project` | workflow view action and header |
| `actions-menu` | `fas:ellipsis` | toggle of the [action menu](action_menus.md) |
| `filter` | `fas:filter` | filter button, panel closed |
| `filter-close` | `fas:filter-circle-xmark` | filter button, panel open |
| `language` | `fas:language` | language selector |
| `sort-asc` / `sort-desc` | `fas:arrow-up-short-wide` / `fas:arrow-down-wide-short` | card list ordering |
| `table-sort-asc` / `table-sort-desc` | `fas:angles-up` / `fas:angles-down` | sortable table headers |
| `formset-up` / `formset-down` | `fas:caret-up` / `fas:caret-down` | formset row controls |
| `formset-add` / `formset-delete` | `fas:plus` / `fas:square-xmark` | formset row controls |
| `field-marker` | `fas:angles-right` | detail widgets |
| `boolean-true` / `boolean-false` | `fas:circle-check` / `fas:circle-xmark` | boolean values (core widget and object detail) |
| `property-detail` | `fas:circle-info` | object detail, card-rows layout |
| `text-icon` | `far:file-lines` | object detail, list-group-3col layout |

The filter button renders both `filter` and `filter-close` and toggles which one is visible, so the icon reflects the
state of the filter panel (`filter` = closed, click to open; `filter-close` = open, click to close). On reload the
icon matches the panel state stored in the session.

## `CRUD_VIEWS_ICONS`

A dict of semantic name to icon value. It is merged per key over the package defaults (and over theme registrations),
so list only what you change or add:

```python
CRUD_VIEWS_ICONS = {
    "detail": "fas:magnifying-glass",   # override a default
    "person": "far:user",               # your own name, usable anywhere an icon value is accepted
}
```

```python
class AuthorDetailView(DetailViewPermissionRequired):
    cv_icon_action = "person"
```

Project entries always win. If a later release of the package introduces a name you already defined yourself, your
entry keeps winning; there is no conflict detection.

In templates use the tag, which resolves any icon value:

```html+django
{% load crud_views %}
{% cv_icon "detail" %}
{% cv_icon cv_icon_action css="me-2" %}
```

`css` adds extra classes (spacing, colour, size). The tag is also available as `{% load crud_views_object_detail %}`.
In Python use `crud_views.lib.icons.render_icon(value, css="")`.

`get_icons()` and `get_libraries()` return the resolved, cached dicts. Do not mutate them.

## Libraries

A library maps a prefix to a renderer. `CRUD_VIEWS_ICON_LIBRARIES` is a dict of prefix to library config, merged per
prefix over the built-ins. The unit is the whole entry: a project entry for `far` replaces the built-in `far` config,
it is not merged field by field.

Built-in libraries:

| Prefix | Config |
|---|---|
| `far` | `{"renderer": "font", "class": "fa-regular fa-{name}"}` |
| `fas` | `{"renderer": "font", "class": "fa-solid fa-{name}"}` |
| `bi` | `{"renderer": "font", "class": "bi bi-{name}"}` |

### Font renderer

`"renderer": "font"` is the built-in CSS-class renderer. `class` is a format string with `{name}`; extra `css` classes
are appended: `far:eye` with `css="me-2"` renders `<i class="fa-regular fa-eye me-2" aria-hidden="true"></i>`. Add
more Font Awesome styles or another font library as more entries:

```python
CRUD_VIEWS_ICON_LIBRARIES = {
    "fal": {"renderer": "font", "class": "fa-light fa-{name}"},
}
```

### Custom renderer

A renderer is a callable with this contract and returns a `SafeString`:

```python
renderer(name: str, *, css: str, config: dict) -> SafeString
```

`name` is the part after the colon, `css` the extra classes (possibly empty) and `config` the library's config dict.
A renderer is the only place markup is produced, so it must escape what it embeds. The `renderer` value may be
`"font"`, a dotted path to a callable, or (via `register_icon_library`) the callable itself.

```python
# myproject/icons.py
from django.utils.html import format_html


def render_svg(name, *, css, config):
    return format_html(
        '<svg class="icon {}" aria-hidden="true"><use href="{}#{}"/></svg>',
        css,
        config["sprite"],
        name,
    )
```

```python
CRUD_VIEWS_ICON_LIBRARIES = {
    "svg": {"renderer": "myproject.icons.render_svg", "sprite": "/static/icons.svg"},
}
CRUD_VIEWS_ICONS = {"detail": "svg:eye"}
```

Extra keys in the library config (here `sprite`) are passed to the renderer in `config`.

## Bootstrap Icons preset

`crud_views.lib.icons.BOOTSTRAP_ICONS` maps **every** name of the default table to a `bi:` value. Load Bootstrap
Icons in your base template and use it as the table:

```python
from crud_views.lib.icons import BOOTSTRAP_ICONS

CRUD_VIEWS_ICONS = {**BOOTSTRAP_ICONS, "detail": "bi:search"}
```

A test keeps `BOOTSTRAP_ICONS` and the default table in sync, so a new semantic name always comes with a Bootstrap
equivalent.

## Registering icons from a theme

A theme app registers its libraries and default icons from `AppConfig.ready()`, so projects need no configuration:

```python
# myapp_theme/apps.py
from django.apps import AppConfig


class MyAppThemeConfig(AppConfig):
    name = "myapp_theme"

    def ready(self):
        from crud_views.lib.icons import register_icon_library, register_icons

        register_icon_library("tabler", renderer="myapp_theme.icons.render")
        register_icons({"detail": "tabler:eye", "delete": "tabler:trash"})
```

`register_icon_library(prefix, renderer="font", **config)` takes `"font"`, a dotted path or a callable;
`register_icons(icons)` takes a dict of name to icon value. Both reset the resolved cache. `class` is a Python
keyword, so pass it with the dict form: `register_icon_library("ti", **{"class": "ti ti-{name}"})`.

### Precedence

```
icons     = package defaults  + theme registrations + CRUD_VIEWS_ICONS
libraries = package built-ins + theme registrations + CRUD_VIEWS_ICON_LIBRARIES
```

Later wins per key, so project settings always win over a theme, and a theme wins over the package. If two theme apps
register the same key, the one whose `ready()` runs later wins, which is the one later in `INSTALLED_APPS`.

## System checks

| ID | Level | Meaning |
|---|---|---|
| `crud_views.E350` | error | a removed setting is still defined (see the changelog); the hint names the replacement |
| `crud_views.E351` | error | the `renderer` dotted path of a library cannot be imported |
| `crud_views.E354` | error | a library with the `font` renderer has no `class` entry |
| `crud_views.W352` | warning | a `CRUD_VIEWS_ICONS` entry uses an unregistered library prefix, or points to another semantic name |
| `crud_views.W353` | warning | `cv_icon_action`, `cv_icon_header` or `ViewSet.icon_header` uses an unregistered library prefix |

Bare values that are neither a known name nor contain a colon are raw CSS classes and are not flagged.

## CSS

The package ships `crud_views/css/icons.css` with `.cv-icon-fw`, a library-neutral fixed-width helper used for icons in
action menus.
