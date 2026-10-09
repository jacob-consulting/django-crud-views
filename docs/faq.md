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

A button template is only rendered when the user may access the target and the action is
enabled, so your template needs no `cv_access` check of its own.

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
    context_buttons=context_buttons_default()
    + [
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
    cv_context_actions = ["edit", "delete"]  # default-shaped edit button


class AuthorDetailView(DetailViewPermissionRequired):
    cv_viewset = cv_author
    cv_context_actions = ["edit_detail", "delete"]  # custom-shaped edit button
```

To change the layout of *all* context buttons project-wide, override
`crud_views/tags/context_action.html` in your project's templates, or point
`CRUD_VIEWS_CONTEXT_BUTTON_TEMPLATE` at your own template.

*See it running: [`examples/bootstrap5/context_buttons/`](https://github.com/jacob-consulting/django-crud-views/tree/main/examples/bootstrap5/context_buttons) ·
Full docs: [Context Buttons](reference/context_buttons.md).*

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
    action is disabled — the same rule as the `{% cv_context_actions %}` header container, so a
    button never shows up in one place and not the other.

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

*See it running: [`examples/bootstrap5/context_buttons/`](https://github.com/jacob-consulting/django-crud-views/tree/main/examples/bootstrap5/context_buttons) ·
Full docs: [Context Buttons § Manual Placement](reference/context_buttons.md#manual-placement-template-tags).*

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
    context_buttons=context_buttons_default()
    + [
        SiblingContextButton(key="articles", sibling_name="article", label_template_code="Articles"),
    ],
)
```

Full documentation of parent/child ViewSets: [Nested ViewSets](reference/nested.md).

## How do I send Cancel and Save back to the page the user came from?

Form views go back to the list by default, both on **Cancel** (`cv_cancel_key`) and after a
successful **Save** (`cv_success_key`). When a form can be opened from several places, typically
the list and the detail page, list those places as allowed origins instead:

<!-- cv-sync: library/views.py -->
```python
class AuthorUpdateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_author
    form_class = AuthorForm
    cv_message_template_code = _("Updated author “{{ object }}”")
    cv_cancel_keys = ["list", "detail"]  # cancel returns to where the user came from
    cv_success_keys = ["list", "detail"]  # so does save
```

The two options are independent; set either one, or both:

| Attribute         | Controls                          | Falls back to    |
|-------------------|-----------------------------------|------------------|
| `cv_cancel_keys`  | the target of the Cancel button   | `cv_cancel_key`  |
| `cv_success_keys` | the redirect after a valid submit | `cv_success_key` |

Links into the form carry the origin view key as `?cv_from=detail` (parameter name:
`CRUD_VIEWS_ORIGIN_PARAM`). The value is a **view key**, never a URL, and is only used when it is
listed and registered on the ViewSet, so it cannot redirect elsewhere. Anything else falls back to
the static key.

Two limits follow from that:

- An origin that needs an object is skipped when there is none: Cancel on a create view never
  returns to `detail`, and Save on a delete view never does (system check `viewset.E254`).
- Returning to the list drops its filter, sort order and page.

*See it running: [`examples/bootstrap5/library/`](https://github.com/jacob-consulting/django-crud-views/tree/main/examples/bootstrap5/library) ·
Full docs: [Dynamic cancel target](reference/update_view.md#dynamic-cancel-target) ·
[Dynamic success target](reference/update_view.md#dynamic-success-target).*

## Why is the last breadcrumb item not a link

The last item is the page the user is on. Bootstrap and WAI-ARIA both mark the current page
as `active` with `aria-current="page"` and no link — linking a page to itself only invites a
pointless reload. `{% cv_breadcrumb %}` therefore always renders the last item unlinked,
even when the underlying `BreadcrumbItem` carries a URL.

*See it running: [`examples/bootstrap5/breadcrumbs/`](https://github.com/jacob-consulting/django-crud-views/tree/main/examples/bootstrap5/breadcrumbs) ·
Full docs: [Breadcrumb](reference/breadcrumb.md).*

## How do I hook the breadcrumb into my site's navigation

Use `CRUD_VIEWS_BREADCRUMB_PREFIX` for a static, site-wide prefix, or override
`cv_breadcrumb_prefix()` in a project base view for dynamic items — see
[Breadcrumb](reference/breadcrumb.md). The breadcrumb deliberately covers only the
crud-views hierarchy; it is not a navigation framework.

*See it running: [`examples/bootstrap5/breadcrumbs/`](https://github.com/jacob-consulting/django-crud-views/tree/main/examples/bootstrap5/breadcrumbs) ·
Full docs: [Breadcrumb § Hooking into your site navigation](reference/breadcrumb.md#hooking-into-your-site-navigation).*

## How do I make a group of fields required only when a checkbox is on?

When a group of fields should be editable and (some of them) required only while a
checkbox is ticked — and must **not** fail validation when the checkbox is off and the
group is hidden — use a [conditional field-group](reference/conditional.md). The rule is
enforced server-side, so an off group never fails validation even if its fields are
declared required; JavaScript only hides the group.

```python
from crispy_forms.layout import Row
from crud_views.lib.conditional import (
    ConditionalGroupModelForm,
    ConditionalGroup,
    ToggleGroup,
    ModelFieldToggle,
)
from crud_views.lib.crispy import Column6


class RegistrationForm(ConditionalGroupModelForm):
    cv_conditional_groups = [
        ConditionalGroup(
            toggle=ModelFieldToggle("with_company"),  # or UIFieldToggle("...") for a non-model checkbox
            fields=["company_name", "vat_id"],
            required=["company_name"],  # only this is required when on
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

*See it running: [`examples/bootstrap5/conditional/`](https://github.com/jacob-consulting/django-crud-views/tree/main/examples/bootstrap5/conditional) ·
Full docs: [Conditional Field-Groups & Conditional FormSets](reference/conditional.md).*

## How do I send an email or start a Celery task after a save?

Override `cv_on_commit(context)`. It runs after the database transaction has committed, and never
after a rollback. Don't use `cv_form_valid_hook`: it runs inside the transaction.

```python
def cv_on_commit(self, context):
    send_welcome_mail.delay(self.object.pk)
```

See [Side effects after commit](reference/request_lifecycle.md#side-effects-after-commit).

## Why does my Celery task sometimes raise `DoesNotExist`?

The task was started inside the transaction (from `cv_form_valid_hook`, `action()` or
`on_transition`), and the worker ran it before the commit made the row visible. Start it from
`cv_on_commit` instead. See [Side effects after commit](reference/request_lifecycle.md#side-effects-after-commit)
and [when `cv_on_commit` runs](reference/request_lifecycle.md#transactions).

## How do I undo an action's changes when `action()` returns `False`?

Returning `False` shows the error message but keeps what `action()` already wrote. Call
`transaction.set_rollback(True)` before returning. See
[Rolling back a failed action](reference/request_lifecycle.md#rolling-back-a-failed-action).

## Why do I get `TransactionManagementError` after catching `IntegrityError`?

`cv_form_valid` runs inside a transaction. On PostgreSQL a caught database error breaks it. Wrap
the statement that may fail in its own `transaction.atomic()`. See
[Catching IntegrityError](reference/request_lifecycle.md#catching-integrityerror).

## How do I turn off the transaction for one view?

Set `cv_atomic = False` on the view. To change the boundary instead (another database,
`durable=True` services), override `cv_get_db_alias()` or `cv_get_atomic()`. See
[Transactions](reference/request_lifecycle.md#transactions) and
[Durable services](reference/request_lifecycle.md#durable-services).

## Where does each hook run, and which one should I override?

The [hook reference](reference/request_lifecycle.md#hook-reference) lists every overridable method
with its phase (outside, in the transaction, after the commit) and what it is meant for.

## Why did my context button disappear? (check E255)

Since 0.24.2 a context button whose target view is not registered is skipped at render time
instead of raising, so the default `home` button can vanish on a detail-only ViewSet. The
downside: a typo such as `ChildContextButton(key="members", child_name="member", child_key="lsit")`
also just makes the button disappear.

The `viewset.E255` system check reports such a button at startup, naming the button key, its
class and the view key or ViewSet name that does not resolve. Fix the name, or register the
missing view. See [Target check](reference/context_buttons.md#target-check-e255) for the rules.

## Why is my `cv_*` attribute silently ignored? (check W280)

`CrudView` config attributes use the `cv_` prefix and are read via `getattr`, so a typo or a
stale name left over from a rename — e.g. `cv_message` when the real attribute is
`cv_message_template_code` — is never an error at import time. It just gets ignored, and
your setting has no effect.

The `viewset.W280` system check catches this: it warns about any `cv_*` **data attribute**
(methods and properties are not checked) whose name is not part of the package vocabulary —
i.e. not declared by any `crud_views` class, core or one of the workflow / polymorphic /
guardian / object_detail / `crud_views_widget_*` extensions. The warning names the attribute
and suggests the closest real attribute on that view.

W280 only answers "is this a real `crud_views` attribute name?" A real attribute that's
valid on the package but doesn't apply to this particular view type is a separate concern,
covered by other checks — W280 is purely about unknown or typo'd names.

Only *data* attributes are checked. An attribute whose value is callable — a method, or a
class assigned directly (e.g. `cv_something = SomeForm`) — is skipped, so those typos are not
caught. This keeps the check from flagging your own helper methods.

**Silencing a legitimate custom attribute (recommended):** declare it in the per-class
allowlist:

```python
class MyView(UpdateView):
    cv_check_ignore_attributes = frozenset({"cv_my_custom_flag"})
    cv_my_custom_flag = True
```

The allowlist is unioned across the class hierarchy, so a mixin and the concrete view can
each contribute their own exemptions.

**Global silencing (coarse):** add `SILENCED_SYSTEM_CHECKS = ["viewset.W280"]` to your
Django settings to suppress the warning everywhere; prefer the per-class allowlist above for
targeted exemption.
