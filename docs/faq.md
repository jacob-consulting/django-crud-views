# FAQ

## How to template context buttons

Every [context button](reference/context_buttons.md) is rendered through a Django template.
By default that template is the theme's `crud_views/tags/context_action.html`, configurable
project-wide via the `CRUD_VIEWS_CONTEXT_BUTTON_TEMPLATE` setting.

A `ContextButton` can override the template *for that button only* with two fields:

| Field           | Type          | Description                                              |
|-----------------|---------------|----------------------------------------------------------|
| `template`      | `str \| None` | Path to a Django template for the whole button           |
| `template_code` | `str \| None` | Inline Django template string for the whole button       |

`template_code` takes precedence over `template`; if neither is set, the
`CRUD_VIEWS_CONTEXT_BUTTON_TEMPLATE` default is used.

!!! note
    These template the **whole button**. The existing `label_template` /
    `label_template_code` fields only template the button's **label** inside the default
    button markup.

The button template is rendered with the resolved button context, which includes:

- `cv_url` — the target URL
- `cv_key` — the action key
- `cv_action_label` — the rendered label
- `cv_icon_action` — the icon CSS class
- `cv_access` — `True` when the user may access the target
- `cv_action_enabled` — `False` hides the button
- `cv_is_active` — `True` when the button points at the current view

### Give a button a different shape in one view

Define a variant button in the viewset with its own template, then reference it only from
the view that needs the different shape:

```python
from crud_views.lib.viewset import ViewSet, context_buttons_default
from crud_views.lib.view import ContextButton
from crud_views.lib.views import DetailViewPermissionRequired, ListViewPermissionRequired

cv_author = ViewSet(
    model=Author,
    name="author",
    context_buttons=context_buttons_default() + [
        # the standard edit button, plus a variant with a custom template
        ContextButton(key="edit", key_target="update"),
        ContextButton(
            key="edit_detail",
            key_target="update",
            template_code=(
                '<a href="{{ cv_url }}" class="btn btn-primary btn-lg" cv-key="{{ cv_key }}">'
                '<i class="{{ cv_icon_action }}"></i> {{ cv_action_label }}</a>'
            ),
        ),
    ],
)


class AuthorListView(ListViewPermissionRequired):
    cv_viewset = cv_author
    cv_context_actions = ["edit", "delete"]          # default-shaped edit button


class AuthorDetailView(DetailViewPermissionRequired):
    cv_viewset = cv_author
    cv_context_actions = ["edit_detail", "delete"]   # custom-shaped edit button
```

To change the layout of *all* context buttons project-wide, override
`crud_views/tags/context_action.html` in your project's templates, or point
`CRUD_VIEWS_CONTEXT_BUTTON_TEMPLATE` at your own template.

## I need to render a context button manually in a template

Use the `cv_context_button` tag to place a single button anywhere in your own layout,
referenced by its key:

```django
{% load crud_views %}

<div class="my-toolbar">
    {% cv_context_button "edit_detail" %}
    {% cv_context_button "delete" %}
</div>
```

The object defaults to the view's current object, so you don't normally pass it. To target
a different object explicitly:

```django
{% cv_context_button "edit_detail" some_object %}
```

!!! note "Hidden when there is no access"
    `cv_context_button` renders **nothing** when the user lacks access to the target or the
    action is disabled. This differs from the default `{% cv_context_actions %}` container,
    which renders inaccessible buttons as *disabled/greyed*. Reach for the manual tag when
    you want the button to disappear entirely.

### Get the target URL only (no markup)

When you build your own link/tile markup but still want the permission-gated target
URL, use `cv_context_url`. It resolves the same context as `cv_context_button` but
returns just the URL string — or `None` when the user lacks access or the action is
disabled (the same visibility rule as `cv_context_button`):

```django
{% load crud_views %}

{% cv_context_url "edit_detail" as edit_url %}
{% if edit_url %}
    <a href="{{ edit_url }}" class="my-tile">Edit</a>
{% endif %}
```

Like `cv_context_button`, the object defaults to the view's current object; pass a
second argument to target a different object. Unknown keys return `None`.

### Gate surrounding markup by permission

Use the `cv_context_has_permission` filter to render wrappers, headings, or separators only
when the user may access a key:

```django
{% load crud_views %}

{% if view|cv_context_has_permission:"edit_detail" %}
    <h3>Edit</h3>
    {% cv_context_button "edit_detail" %}
{% endif %}
```

The filter checks access for `view`'s current object (or `None` for list-type views) and
returns `False` for unknown keys.

### Render a custom loop of buttons

`view.cv_get_context_buttons` returns the resolved, **access-filtered** button contexts (so
your loop never emits empty wrappers). Render each with `cv_render_context_button`:

```django
{% load crud_views %}

{% for ctx in view.cv_get_context_buttons %}
    <span class="my-wrap">{% cv_render_context_button ctx %}</span>
{% endfor %}
```

By default it iterates the view's `cv_context_actions`. Pass an explicit key list from your
own view method to control which buttons appear and in what order:

```python
class AuthorDetailView(DetailViewPermissionRequired):
    cv_viewset = cv_author
    cv_context_actions = ["edit_detail", "delete"]

    def get_toolbar_buttons(self):
        return self.cv_get_context_buttons(keys=["edit_detail", "delete"])
```

## How do I link from one child collection to a sibling collection?

When you have a parent with several children (e.g. `Author` → `Book`, `Article`) and want a
button on one child's pages that jumps to a sibling collection under the *same* parent, use
[`SiblingContextButton`](reference/context_buttons.md#siblingcontextbutton). Place it on the
child viewset; it reuses the parent PK from the current URL:

```python
from crud_views.lib.viewset import ViewSet, ParentViewSet, context_buttons_default
from crud_views.lib.view import SiblingContextButton

cv_book = ViewSet(
    model=Book,
    name="book",
    parent=ParentViewSet(name="author"),
    context_buttons=context_buttons_default() + [
        SiblingContextButton(key="articles", sibling_name="article", label_template_code="Articles"),
    ],
)
```

```python
class BookListView(ListViewPermissionRequired):
    cv_viewset = cv_book
    cv_context_actions = ["parent", "create", "articles"]
```

Use `ChildContextButton` on the parent view to go *down* to a child, and
`SiblingContextButton` on a child view to go *sideways* to a sibling.
<<<<<<< HEAD

## Why is the last breadcrumb item not a link

The last item is the page the user is on. Bootstrap and WAI-ARIA both mark the current page
as `active` with `aria-current="page"` and no link — linking a page to itself only invites a
pointless reload. `{% cv_breadcrumb %}` therefore always renders the last item unlinked,
even when the underlying `BreadcrumbItem` carries a URL.

## How do I hook the breadcrumb into my site's navigation

Use `CRUD_VIEWS_BREADCRUMB_PREFIX` for a static, site-wide prefix, or override
`cv_breadcrumb_prefix()` in a project base view for dynamic items — see
[Breadcrumb](reference/breadcrumb.md). The breadcrumb deliberately covers only the
crud-views hierarchy; it is not a navigation framework.
=======
```

## How do I make a group of fields required only when a checkbox is on?

When a group of fields should be editable and (some of them) required only while a
checkbox is ticked — and must **not** fail validation when the checkbox is off and the
group is hidden — use a [conditional field-group](reference/conditional.md). The rule is
enforced server-side, so an off group never fails validation even if its fields are
declared required; JavaScript only hides the group.

```python
from crispy_forms.layout import Row
from crud_views.lib.conditional import (
    ConditionalGroupModelForm, ConditionalGroup, ToggleGroup, ModelFieldToggle,
)
from crud_views.lib.crispy import Column6

class RegistrationForm(ConditionalGroupModelForm):
    cv_conditional_groups = [
        ConditionalGroup(
            toggle=ModelFieldToggle("with_company"),  # or UIFieldToggle("...") for a non-model checkbox
            fields=["company_name", "vat_id"],
            required=["company_name"],                 # only this is required when on
        ),
    ]

    class Meta:
        model = Registration
        fields = ["name", "with_company", "company_name", "vat_id"]

    def get_layout_fields(self):
        return [
            Row(Column6("name")),
            Row(Column6("with_company")),
            ToggleGroup(
                "with_company",
                Row(Column6("company_name"), Column6("vat_id")),
                legend="Company details",
            ),
        ]
```

When the checkbox is off the group fields are cleared on save (they must be
`null=True, blank=True`). To toggle an **entire first-level formset** instead of a
field-group, use `ConditionalFormSet` — see the
[reference page](reference/conditional.md).
>>>>>>> origin/main
