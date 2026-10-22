# Base template

Every crud_views frontend template renders `{% extends cv_extends %}`, where
`cv_extends` is resolved per view. This lets you control which base template
your CRUD pages extend — globally, per ViewSet, or per view.

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
headings of every object-detail layout. They keep their look: Bootstrap sizes headings by tag, so a heading that
moves to another level also gets the size class of its stock level, e.g. `<h2 class="h5 card-title">`. In a
[modal](modals.md) the modal title is the view header, so it renders at the setting's level and the content one
below, the same outline as the full page.

Render the view title with `{% cv_heading "header" %}` and it follows the same setting, so the two cannot drift
apart:

```django
{% load crud_views %}
<div class="d-flex justify-content-between align-items-center mb-2">
    {% cv_heading "header" level=1 class="h3 mb-0" %}
        {% cv_header_icon %} {% cv_header %}
    {% endcv_heading %}
    {% cv_context_actions object %}
</div>
```

`{% cv_heading ["header"] level=N [class=…] %}…{% endcv_heading %}`:

- `level` (an int 1–6) is the level the heading has while `CRUD_VIEWS_HEADER_LEVEL` is unset.
- Without `"header"` (a content heading) it renders at `CRUD_VIEWS_HEADER_LEVEL + 1`; with `"header"`, at
  `CRUD_VIEWS_HEADER_LEVEL`.
- When the rendered level differs from `level`, `h{level}` is prepended to `class`.
- `class` takes a literal or a variable and is escaped. The body renders with the template's context, and blocks
  inside it can be overridden as usual.

A theme or project template that writes its own headings can use the same tag.

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
