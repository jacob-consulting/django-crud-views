# Base template

Every crud_views frontend template renders `{% extends cv_extends %}`, where
`cv_extends` is resolved per view. This lets you control which base template
your CRUD pages extend — globally, per ViewSet, or per view.

!!! example "Try it live"
    The [Theme example](https://django-crud-views-demo.onrender.com/theming/) in the live demo points to this page and, once it is live, to
    the Tabler theme demo — log in as `alice` / `alice`. See [Live demo](../getting_started/demo.md) for data resets and wake-up time.

## What to put in it

The base template is yours; crud_views only extends it. A few of its features are rendered by
tags *you* place, so they stay silent until you do:

| Tag | Put it | For |
|---|---|---|
| `{% cv_css %}` / `{% cv_js %}` | in `<head>` / before `</body>` | the [registered CSS and JS bundles](assets.md) |
| `{% cv_config %}` | in `<head>`, before `{% cv_js %}` | the [JavaScript config and modal shell](javascript.md) |
| `{% cv_messages %}` | top of the content area | [flash messages](messages.md), including the ones create, update, delete and action views emit themselves |
| `{% cv_breadcrumb %}` | above the content | the [breadcrumb trail](breadcrumb.md) |

All four `{% load crud_views %}` and render nothing when they have nothing to show, so they are
safe to place unconditionally. Bootstrap's own CSS and JavaScript are not a Python dependency —
load them in this template from a CDN or your own static files.

## Heading levels

The base template renders the view title (`{% cv_header %}`) in whatever element you choose. Tell crud_views which
level that is, and its own headings fit under it:

```python
CRUD_VIEWS_HEADER_LEVEL = 1  # my {% cv_header %} is the page h1
```

| Your view title is… | Setting | crud_views headings |
|---|---|---|
| the page `h1` | `1` | `h2` |
| an `h2` under a site `h1` | `2` | `h3` |
| not set | `None` | unchanged (`h5`; the object-detail accordion `h2`) |

This covers card titles in a card list, the workflow page's "Workflow Action" and "Workflow History", and the group
headings of every object-detail layout. By default a heading that moves to another level gets the size class of
its stock level, e.g. `<h2 class="h5 card-title">`. Themes can replace or clear that size class. In a
[modal](modals.md) the modal title is the view header, so it renders at the setting's level and the content one
below, the same outline as the full page.

Render the view title with `{% cv_heading "header" level=1 %}` and it follows the same setting. Semantic level and
visual size are independent:

`{% cv_heading ["header"] level=N [size=N] [class=…] [icon_class=…] %}…{% endcv_heading %}`

- `level` is a required literal integer 1–6, used while `CRUD_VIEWS_HEADER_LEVEL` is unset.
  It must still be supplied when that setting is configured; there is no implicit default.
- Without `"header"` it renders at `CRUD_VIEWS_HEADER_LEVEL + 1`; with `"header"`, at the configured level.
- Explicit `size` is a literal integer 1–6 and always resolves `heading:size-N`. Without it, the tag uses
  `heading:size-{level}` only when the semantic level differs from `level`, preserving the original default markup.
- The six class-table keys are `heading:size-1`, `heading:size-2`, `heading:size-3`, `heading:size-4`,
  `heading:size-5` and `heading:size-6`, defaulting to `h1` through `h6`. Project
  `CRUD_VIEWS_BUTTON_CLASSES` overrides theme registration, which overrides builtins. `None` or `""` removes only
  that size contribution; caller utility classes and semantic level remain intact.
- `class` and `icon_class` each take a literal or variable. The size, caller and icon contributions are
  independently escaped and joined in that order, with no separator for an empty contribution. Django's usual
  explicit safe-value behavior still applies; never mark untrusted classes or title text safe.
- The body retains the template context and overridable blocks. A theme's own headings can use the same tag.

### Page title recipe

Use a non-heading wrapper around this title and any context actions. Resolve the icon once, place host classes
on the heading with `icon_class`, and render only the projection's `inline_html` inside it:

```django
{% load crud_views %}
{% cv_heading_icon view.cv_get_header_icon location="page" as title_icon %}
{% cv_heading "header" level=1 size=3 class="mb-0" icon_class=title_icon.host_class %}
    {{ title_icon.inline_html }}
    {% block cv_header %}{% cv_header %}{% endblock cv_header %}
{% endcv_heading %}
```

The visible-title `cv_header` body block remains supported. Override it with ordinary escaped template content.
Keep any `{% cv_context_actions object %}` alongside the heading in the surrounding flex container.

### Modal title recipe

The modal uses the same projection at its own location. Preserve the literal space between the inline icon and
title, including when the icon is empty:

```django
{% load crud_views %}
{% cv_heading_icon view.cv_get_header_icon location="modal" as title_icon %}
{% cv_heading "header" level=5 class="modal-title" icon_class=title_icon.host_class %}{{ title_icon.inline_html }} {{ view.cv_header }}{% endcv_heading %}
```

### Migrating copied heading templates

Migrate incompatible copies immediately before 1.0: replace literal sizing such as `class="h3 mb-0"` with
`size=3 class="mb-0"`, remove nested heading wrappers, and replace standalone title icons with the projection
shown above. Keep application utility classes; the tag does not strip classes by prefix.

`cv_header_icon` still renders an icon, but it is a standalone renderer and cannot put a host-library icon on
the title-bearing heading. The old separate `cv_header_icon` block placement is replaced by this contract;
customize the icon through `view.cv_get_header_icon`, the registry and heading class slots. Preserve the
`cv_header` block for visible-title overrides. Empty/disabled icons must leave the title visible.

See [heading icon placement](icons.md#heading-icons) and the [native class table](theme.md#native-heading-class-table).
These recipes exercise markup, semantics and escaping; they do not certify screen-reader behavior or the visual
appearance of a complete non-Bootstrap theme.

## Resolution order

`cv_extends` is resolved from the first of these that is set:

1. **View** — `cv_extends_template` on the `CrudView` subclass
2. **ViewSet** — `extends` on the `ViewSet`
3. **Global** — the `CRUD_VIEWS_EXTENDS` setting (required; final fallback)

### Per ViewSet

Set it once and every view in the ViewSet inherits it:

```python
cv_author = ViewSet(
    model=Author,
    name="author",
    extends="myapp/author_base.html",
)
```

### Per view

```python
class AuthorListView(ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_author
    cv_extends_template = "myapp/author_list_base.html"
```

### Shared base via a mixin

To share a base across several ViewSets (or vary it within one), put it on a
mixin and inherit:

```python
class MySpecialBase(CrudView):
    cv_extends_template = "myapp/special_base.html"


class FooListView(MySpecialBase, ListView): ...
```

!!! warning "The override template must be a real base template"
    The template named by `cv_extends_template` / ViewSet `extends` is itself
    the base that crud_views extends. It **MUST NOT** contain
    `{% extends cv_extends %}` (nor otherwise re-extend `cv_extends`) — that
    makes the template extend itself and raises
    `django.template.exceptions.TemplateDoesNotExist`.

    Point the override at a normal base template — one that extends your own
    site base (e.g. `{% extends "base.html" %}`) or none at all.

## Validation

If a ViewSet `extends` or a view `cv_extends_template` names a template that
cannot be loaded, Django's system checks report it at startup
(`crud_views.viewset.E111`).
