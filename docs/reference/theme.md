# Custom themes (bring your own theme)

crud_views ships one theme, **bootstrap5** (the `crud_views` app). The look and feel is
defined entirely by templates under the `crud_views/` template namespace, and you can replace
any of them by shipping a **theme app** of your own. There is no theme *setting* — theming is
template override by name, resolved through Django's app template loader.

!!! note "Two different mechanisms"
    This page is about replacing crud_views' **own** templates (buttons, list/detail/form
    partials) to restyle the framework. To choose which **base template** your CRUD pages
    extend (your site chrome), use `cv_extends` instead — see
    [Base template](templates.md).

!!! example "Try it live"
    The [Theme example](https://django-crud-views-demo.onrender.com/theming/) in the live demo points from here and, once it is live, to the
    Tabler theme demo — log in as `alice` / `alice`. See [Live demo](../getting_started/demo.md) for data resets and wake-up time.

## How resolution works

Every crud_views template lives under a `crud_views/` directory, e.g.
`crud_views/view_list_table.html`, `crud_views/tags/button/action.html`. Django's
`app_directories` template loader searches each app in `INSTALLED_APPS` **in order** and
returns the first template matching a given name.

This assumes Django's default template configuration (`APP_DIRS: True`, or an explicit
`django.template.loaders.app_directories.Loader`); a project with a custom `loaders` list
resolves templates however that list dictates.

So to override a template, an app earlier in `INSTALLED_APPS` ships a template with the
**same name** under its own `templates/crud_views/` directory. That copy wins; crud_views'
own copy is the fallback for every template the theme app does not override.

## What a theme app must provide

A theme app is an ordinary Django app:

1. An `AppConfig` (so it can appear in `INSTALLED_APPS`).
2. A `templates/crud_views/` directory containing the same-named templates you want to
   override. You only need to ship the templates you actually change — anything you omit
   falls through to bootstrap5.
3. Optionally, static assets under `static/` (register JS/CSS via the asset registry — see
   [Assets](assets.md) — if your theme needs its own).

## JavaScript

The scripts call Bootstrap through replaceable adapters (`cv.adapters`), so a theme for a Bootstrap-compatible or
non-Bootstrap UI library swaps them from its own registered asset. See [JavaScript](javascript.md).

## INSTALLED_APPS ordering (the one rule that matters)

Your theme app **must be listed before `crud_views`** so its templates are found first:

```python
INSTALLED_APPS = [
    # ...
    "myapp_theme.apps.MyAppThemeConfig",  # <-- before crud_views
    "crud_views.apps.CrudViewsConfig",
    # ...
]
```

If it is listed *after* `crud_views`, crud_views' own templates are found first and your
overrides never render.

!!! warning "`CRUD_VIEWS_THEME` is not a setting"
    There is no theme setting. If `CRUD_VIEWS_THEME` is set, crud_views' system checks emit
    `crud_views.W110` and ignore it. Do theming with a template-override app as described
    here.

## Icons

A theme registers its icon library and default icons from `AppConfig.ready()`, so projects need no
configuration. Project settings (`CRUD_VIEWS_ICONS`, `CRUD_VIEWS_ICON_LIBRARIES`) still win over a theme:

```python
def ready(self):
    from crud_views.lib.icons import register_icon_library, register_icons

    register_icon_library("tabler", renderer="myapp_theme.icons.render")
    register_icons({"detail": "tabler:eye", "delete": "tabler:trash"})
```

If two theme apps register the same key, the one later in `INSTALLED_APPS` wins. See [Icons](icons.md#registering-icons-from-a-theme).

A design system that paints icons as a class on the button itself (`<a class="btn icon-edit">`) registers its library
with `placement: "host"` and, where a kind of button needs a base class next to the name class, the
`*:icon-host` button classes. The stock leaves then put the class on the button; no leaf is copied
([Host placement](icons.md#host-placement)):

```python
def ready(self):
    from crud_views.lib.button_classes import register_button_classes
    from crud_views.lib.icons import register_icon_library

    register_icon_library("ui", placement="host", **{"class": "icon-{name}", "standalone": "icon {name_class}"})
    register_button_classes({"context:secondary:icon": "btn btn-icon-only", "menu:icon-host": "link-icon {name_class}"})
```

## Buttons

Button classes live in one table, so a theme registers them from `AppConfig.ready()` — per-label-mode keys such as
`card:tertiary:icon` included, see [Buttons](buttons.md#the-class-table) — and overrides a template only where the
markup differs. Project settings (`CRUD_VIEWS_BUTTON_CLASSES`) still win over a theme, key by key:

```python
def ready(self):
    from crud_views.lib.button_classes import register_button_classes

    register_button_classes({"card:primary": "button is-primary is-small", "form:submit": "button is-primary"})
```

See [Buttons](buttons.md#registering-classes-from-a-theme).

A design system that builds a button row as a list, and drops the row for a single button, needs no template either:

```python
register_button_classes(
    {
        **{f"{loc}:container": "btn-row" for loc in ("context", "list", "card")},
        **{f"{loc}:container-list": "" for loc in ("context", "list", "card")},
        **{f"{loc}:container-single": "bare" for loc in ("context", "list", "card")},
    }
)
```

See [Button row as a list](buttons.md#button-row-as-a-list).

## Theme label defaults

Themes may set per-location label floors without a project setting. Effective defaults merge **package → theme →
project**, per key. Package values remain context/list `"icon"`, card `"both"`, form `"label"`.
Explicit button/view modes and selected owner maps still take precedence over this floor; owner maps are selected
whole, not merged. See the existing [resolution steps](action_menus.md#label-mode).

### Register theme defaults

Call the public registrations from your theme's `AppConfig.ready()`:

```python
def ready(self):
    from crud_views.lib.button_classes import register_button_classes
    from crud_views.lib.view.label_mode import register_label_mode_defaults

    register_label_mode_defaults({"form": "both"})
    register_button_classes(
        {
            "form:actions": "d-flex flex-wrap gap-2",
            "form:filter-actions": "d-flex flex-wrap gap-1",
            "alert:dismissible": "notice-dismissible",
            "alert:close": "notice-close",
        }
    )
```

Supply CSS for the example notice classes. Later registration calls win per key; app `ready()` order follows
`INSTALLED_APPS`. This differs from template lookup, where the first matching app wins. Registration copies the
input and validates the entire dict before changing anything: unknown locations or modes, non-string entries,
or a non-dict raise `ValueError` in every mode, without partial registration.

`register_label_mode_defaults()` accepts only `context`, `list`, `card`, `form` and the modes `label`, `icon`, `both`.
`default_label_mode(location)` reads project settings on every call: `override_settings` and restoration work
without resetting a cache. Invalid project values raise `ValueError` in strict mode; otherwise they log once per
location/value and fall back to the theme, then the package. E108 still reports malformed project configuration.
An explicit valid owner mode wins without consulting an invalid lower floor. Registration does not rename
`cv_context_action_label_mode` or the distinct plural owner-map APIs.

## Heading presentation

Heading semantic levels follow `CRUD_VIEWS_HEADER_LEVEL`; visual sizing and icon presentation use the same
class registration/settings layers as buttons. Use the [heading tag and migration recipes](templates.md#heading-levels)
to change sizes without copying templates. Keep utility classes supplied by the application separate from
`size=` and `icon_class=`. The supported `cv_header` body block can still override visible title content.

### Native heading class table

This executable project-settings example replaces all six Bootstrap sizes and both shared icon slots.
The corresponding CSS is supplied by your theme; the example establishes class/escaping behavior, not a full
non-Bootstrap visual theme or screen-reader certification:

```python
CRUD_VIEWS_BUTTON_CLASSES = {
    "heading:size-1": "native-size-1",
    "heading:size-2": "native-size-2",
    "heading:size-3": "native-size-3",
    "heading:size-4": "native-size-4",
    "heading:size-5": "native-size-5",
    "heading:size-6": "native-size-6",
    "heading:icon-host": "native-icon {name_class}",
    "heading:icon-inline": "native-inline",
}
```

A theme registers this mapping with `register_button_classes()` from `AppConfig.ready()` instead. Project
settings still win. Replace any size value with `None` or `""` to omit that sizing class; semantic level,
visible text and caller utility classes survive. An explicit `size=3` always consults its key, while an omitted
size only adds the original level's class when the semantic level changes.

Icon lookup is **layer first**: project location, project shared, theme location, theme shared, builtin location,
builtin shared. Thus a project-wide `heading:icon-inline` replaces even a theme's group-specific value.
Explicit empty/None ends inheritance; empty host styling suppresses the host icon, while empty inline styling
does not suppress the element itself. See [the complete icon key list](icons.md#heading-icons).

## Worked example: restyle the buttons

Register the classes as above — the `*:active` and `*:hidden-label` keys included when your framework spells those
utilities differently — and override nothing for looks (the worked registration is in
[Buttons](buttons.md#a-theme-recipe)). Override a leaf only where the markup itself differs: give your theme app a
template at `myapp_theme/templates/crud_views/tags/button/action.html`, and with `myapp_theme` listed before
`crud_views` in `INSTALLED_APPS` every action button renders your leaf with the registered classes, while all other
templates keep the bootstrap5 defaults.

The thin templates `tags/context_action.html`, `tags/list_action.html`, `tags/card_action.html` and
`tags/actions_menu_item.html` are logic templates: do not copy them, override the leaves instead.

## Custom form-button templates

A crispy form button in a layout renders through the leaf `crud_views/tags/button/form.html` (see
[Forms](buttons.md#forms)). A theme app that ships a template under that name restyles every form button. A single
button class, or a single button, can use its own template instead; the first that is set wins:

1. a `template=` argument: `Submit("submit", "Save", template="myapp/buttons/save.html")` (an empty string counts as
   not set);
2. the `template` attribute of your subclass of `Submit`, `Button` or `Reset`;
3. the bundled `crud_views/tags/button/form.html`.

`%s` in the name is replaced with the active crispy template pack, as crispy does: `"%s/buttons/pill.html"` loads
`bootstrap5/buttons/pill.html`.

Every one of these templates receives exactly [the form leaf contract](buttons.md#the-form-leaf-contract) and nothing
else: no crispy `input` object, no `form` and no variable of the surrounding page. A template written for crispy's
`baseinput.html` migrates its variables:

| crispy `input` | Form leaf contract |
|---|---|
| `input.value` | `cv_value` (the submitted value), `cv_label` (the text) |
| `input.name` | `cv_name` |
| `input.id` | `cv_id` |
| `input.input_type` | `cv_type` |
| `input.field_classes` | `{% cv_button_class "form" cv_key cv_label_mode %}`, then `cv_css_class` and `cv_icon_class` |
| `input.flat_attrs` | `cv_flat_attrs` |
| the cancel URL attribute | `cv_cancel_url` |

`cv_value`, `cv_label` and the other text keys are plain strings: output them with `{{ }}` and let autoescaping do
its work, never with `|safe`. `cv_flat_attrs` is already escaped and is output as it is. A value is never rendered as
template code. This recipe makes the submit buttons of a theme pill-shaped and keeps the label modes:

```python
from crud_views.lib.crispy import Submit


class PillSubmit(Submit):
    template = "%s/buttons/pill.html"
```

```django
{% load crud_views %}
<button type="{{ cv_type }}" name="{{ cv_name }}" value="{{ cv_value }}" id="{{ cv_id }}"
        class="{% cv_button_class 'form' cv_key cv_label_mode %} rounded-pill{% if cv_css_class %} {{ cv_css_class }}{% endif %}{% if cv_icon_class %} {{ cv_icon_class }}{% endif %}"
        {% if cv_cancel_url is not None %}data-cv-cancel-url="{{ cv_cancel_url }}"{% endif %}
        {% if cv_title %}title="{{ cv_title }}" data-cv-tooltip="form"{% endif %}{{ cv_flat_attrs }}>
    {% if cv_label_mode != "label" and cv_icon and cv_icon_inline is not False %}{% cv_icon cv_icon %}{% endif %}
    <span{% if cv_label_mode == "icon" %} class="{% cv_button_class 'form' 'hidden-label' %}"{% endif %}>{{ cv_label }}</span>
</button>
```

Save it as `myapp_theme/templates/bootstrap5/buttons/pill.html`. Keep `data-cv-cancel-url` on cancel buttons, where
`viewset.js` reads it, and `title` with `data-cv-tooltip="form"` in `"icon"` mode. A button added with
`helper.add_input()` is still rendered by the template pack's `baseinput.html`, never by these templates.

## Cancel links in custom form-button templates

A cancel can render as a native `<a href>` link: through its `tag=` keyword, or through the class-table key
`form:cancel-tag` (see [Cancel links](buttons.md#cancel-links)). The bundled leaf does that by itself. A custom
template decides its own markup: the package never forces a link over it. It receives the effective element as
`cv_tag`, `"a"` or `"button"`, after every fallback.

A template written before `cv_tag` existed, such as the pill template above, keeps working. On a cancel it renders
its `<button>`, and `data-cv-cancel-url` with `viewset.js` still navigate. Only the link's attribute set reaches it as
`cv_flat_attrs`, so button-only extras such as `form` or `formaction` are missing there while the option selects
`"a"`. To render the native link, the template consults `cv_tag`:

```python
from crud_views.lib.crispy import Button


class PillCancel(Button):
    template = "%s/buttons/pill_cancel.html"
```

```django
{% load crud_views %}
{% if cv_tag == "a" %}
<a href="{{ cv_cancel_url }}" id="{{ cv_id }}"
   class="{% cv_button_class 'form' cv_key cv_label_mode %} rounded-pill{% if cv_css_class %} {{ cv_css_class }}{% endif %}{% if cv_icon_class %} {{ cv_icon_class }}{% endif %}"
   {% if cv_title %}title="{{ cv_title }}" data-cv-tooltip="form"{% endif %}{{ cv_flat_attrs }}>
{% else %}
<button type="{{ cv_type }}" name="{{ cv_name }}" value="{{ cv_value }}" id="{{ cv_id }}"
        class="{% cv_button_class 'form' cv_key cv_label_mode %} rounded-pill{% if cv_css_class %} {{ cv_css_class }}{% endif %}{% if cv_icon_class %} {{ cv_icon_class }}{% endif %}"
        {% if cv_cancel_url is not None %}data-cv-cancel-url="{{ cv_cancel_url }}"{% endif %}
        {% if cv_title %}title="{{ cv_title }}" data-cv-tooltip="form"{% endif %}{{ cv_flat_attrs }}>
{% endif %}
    {% if cv_label_mode != "label" and cv_icon and cv_icon_inline is not False %}{% cv_icon cv_icon %}{% endif %}
    <span{% if cv_label_mode == "icon" %} class="{% cv_button_class 'form' 'hidden-label' %}"{% endif %}>{{ cv_label }}</span>
{% if cv_tag == "a" %}</a>{% else %}</button>{% endif %}
```

Save it as `myapp_theme/templates/bootstrap5/buttons/pill_cancel.html`. On the link branch, `cv_cancel_url` is the
only `href`. Never add `type`, `name`, `value` or `data-cv-cancel-url` there, so that `viewset.js` leaves the link to
the browser. `cv_flat_attrs` holds the link's filtered attributes, with `target` and `rel` as the caller gave them.
The button branch is the pill template unchanged. `cv_type`, `cv_name`, `cv_value` and `cv_cancel_url` keep their
values under a link, so one template serves both elements. Template precedence (`template=`, the subclass attribute,
the bundled leaf), `%s` pack substitution and literal-text escaping work as in
[Custom form-button templates](#custom-form-button-templates).

## Framing the form pages

The create, update, custom-form and delete pages share one frame, `snippets/form_frame.html`:

```django
{% block cv_form_frame %}{% block cv_form_body %}{% endblock %}{% endblock %}
```

Their content templates extend it and fill `cv_form_body` with the `<form>`, so a theme that only wants to frame the
form overrides the frame and nothing else. The form's `enctype`, its `action` (which keeps `cv_from`) and the media
handling stay upstream's. A modal request carries the `X-CV-Modal: true` header; read it to leave the modal bare:

```django
{% block cv_form_frame %}
{% if request.headers.x_cv_modal != "true" %}<div class="card"><div class="card-body">{% endif %}
{% block cv_form_body %}{% endblock %}
{% if request.headers.x_cv_modal != "true" %}</div></div>{% endif %}
{% endblock %}
```

## Page-owned form helpers

Within an actionable CRUD content region, the page owns one outer form and one CSRF input. Auxiliary sibling forms
keep their independent tokens; no nested form is valid, including an unclassed form. Protected deletion and
full-page workflows with no available choices intentionally omit their confirmation form. Supported workflow
modals retain the inherited custom-form body, including its form when no choices remain. Create/update, including
parent formsets, remain outside modal HTTP support; opting in still fails E251.

Library helpers now set `form_tag=False`. For application helpers this is mandatory when using `cv_render_form`:
`form_tag=True` raises `ImproperlyConfigured` even when strict mode is off. The page owns method, action, id,
enctype and other outer attributes. The renderer never transfers helper wrapper attributes to it.

### Computed helper recipe

Computed properties may return a fresh helper. Keep layout/field settings here and wrapper settings on the page:

```python
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from django import forms
from crud_views.lib.crispy import Submit


class ContactForm(forms.Form):
    name = forms.CharField()

    @property
    def helper(self):
        helper = FormHelper()
        helper.form_tag = False
        helper.layout = Layout("name", Submit("submit", "Send", icon="save"))
        return helper
```

`cv_render_form` selects `form.helper` once, including falsey helper objects, and exposes its render-local
adaptation as `cv_form_helper`. An absent/None helper gets a nonwrapping default. The source helper and layout
are not mutated: inner CSRF suppression applies only at this boundary, preserving custom helper hooks.

### Page-owned form recipe

In a copied content template, keep the enclosing page's attributes and token. For a custom endpoint, supply
`form_id` in context and retain the request, form and normal Django CSRF context:

```django
{% load crud_views %}
<form class="cv-form" id="{{ form_id }}" method="post" action="{{ request.get_full_path }}" enctype="multipart/form-data" novalidate>
    {% csrf_token %}
    {{ form.non_field_errors }}
    {% cv_render_form %}
</form>
```

Do not add `safe` to caller-controlled attribute or field values. The stock create/update/custom forms retain
multipart and their explicit current-page action; deletion keeps its existing attributes. Overriding only
`snippets/form_frame.html` remains sufficient when the theme only changes surrounding decoration.

### Copied inner form template

If your theme copied `crud_views/tags/form.html`, replace its helper lookup with this complete inner template:

```django
{% load crispy_forms_tags %}
{% crispy form cv_form_helper %}
```

Do not resolve `form.helper` again or use the implicit `{% crispy form %}` path here. A legacy copy ignoring
`cv_form_helper` bypasses token suppression, may emit duplicate tokens, and cannot be automatically diagnosed.
No rendered-HTML rewriting or global crispy-template override repairs such copies.

### Copied workflow action template

Migrate a copied `crud_views_workflow/view_workflow.action.html` from direct crispy to the same boundary, retaining
the full-page branch and implicit current-page target. Remove its unused `crispy_forms_tags` load:

```django
{% load i18n crud_views %}
{% if has_workflow_choices %}
    {% cv_heading level=5 %}{% translate "Workflow Action" %}{% endcv_heading %}
    <form class="cv-form" method="post" novalidate>
        {% csrf_token %}
        {{ form.non_form_errors }}
        {% cv_render_form %}
    </form>
{% else %}
    {% translate "There are no workflow steps available from the current state." %}
{% endif %}
```

This recipe does not change `WorkflowView.cv_content_template`: its supported modal response still uses
`crud_views/view_custom_form.content.html`, not this full-page workflow branch.

### Wrapper diagnostics

With `form_tag=False`, nonempty raw `form_action`, `form_id`, `attrs`, `form_class`, and `form_method` other than
`"post"` are detectable unused outer configuration. Rendering logs a warning in non-strict mode and raises
`ImproperlyConfigured` in strict mode. Move the intended attributes to the page template. Ordinary defaults
are quiet; explicitly assigning a default value is not promised detectable. The action is checked without
resolving its URL. Helper method/classes may still affect pack internals; field/label/media/layout options are
outside these wrapper diagnostics. These are render-time diagnostics, not a new startup form-construction check.

A redundant parent-form `helper` override used only to set `form_tag=False` can be removed when inheriting the
library helper. Inherited library providers recover static W292 missing-icon inspection. Intentional custom
helper/provider overrides keep the existing non-instantiating diagnostic boundary.

### Standalone library form recipe

Standalone `{% crispy form %}` for a library `CrispyModelForm` now emits fields and its existing token, without
the former helper-owned form wrapper. Add a caller-owned wrapper, but **do not add another CSRF tag**:

```django
{% load crispy_forms_tags %}
<form class="cv-form" method="post" action="{{ request.get_full_path }}" enctype="multipart/form-data" novalidate>
    {% crispy form form.helper %}
</form>
```

Use a normal request/CSRF context and retain the helper's token behavior on this standalone POST path. This differs
from `cv_render_form`, where the page emits the token and the inner renderer suppresses it. Standalone custom
helpers and GET filters keep their own policy. The ownership correction intentionally changes DOM: the reviewed
create/update/custom/delete frames lose their inner form and duplicate token; standalone library forms lose only
their helper wrapper. Field/control attributes and the outer page form remain intact. See
[immediate migration](../migrating-1.0.md#page-owned-forms-and-helpers).

## Action-group classes

`form:actions` styles the default ordinary/delete action group; `form:filter-actions` independently styles the
default filter group. Both package defaults are empty strings. They are base-only utility keys, not form kinds
or label-mode keys. See the [complete class inventory](buttons.md#the-class-table).

Classes are resolved each render and added alongside the active pack's own wrapper classes. Empty defaults
preserve that pack's bytes. Current crispy 2.7 / crispy-bootstrap5 2026.9 and the declared crispy 2.0 /
crispy-bootstrap5 2023.10 floor have been tested separately. The latter uses a library-local bridge only for
the exact audited source resolved from the installed Bootstrap pack. Different origins, modified templates
and custom packs keep their own rendering; they must consume `formactions.css_class` to display the utility.
There is no generic pack fallback, global template replacement or dependency-floor increase.

### Custom action-group opt-in

Retain the library group through `super()` and add your own class without importing private bridge machinery:

```python
class SpacedActions:
    def get_form_actions(self):
        group = super().get_form_actions()
        group.css_class = " ".join(value for value in (group.css_class, "theme-actions") if value)
        return group
```

Place this mixin before your library form or `ListViewFilterFormHelper` base. A custom hook returning a separate
layout, `None` or an empty group retains ownership and does not automatically consume these keys. The existing
[replacement/removal recipes](list_view.md#custom-filter-helpers) and tutorial guidance remain valid; retain the filter's
separate hidden sort/order/direction inputs. Pack layout and custom CSS remain the theme's responsibility.

## Alerts

Every alert in the package (flash messages, the delete page's protection and related-objects alerts, the guardian
manage page) renders through one frame, `tags/alert.html`. A theme restyles alerts in three independent places:

- **The frame**, `tags/alert.html`: box, icon, heading, close button. It includes `alert.body_template`.
- **The list body**, `snippets/alert/list.html`: every alert with `items` follows it. The text body is
  `snippets/alert/text.html`.
- **The colours**, the class keys `alert:error`, `alert:warning`, `alert:success`, `alert:info` and `alert:debug`
  (defaults `alert alert-danger` … `alert alert-secondary`).

`tags/messages.html` is a loop, and the delete snippets (`snippets/delete/protection_errors.html`,
`snippets/delete/related_objects.html`) only decide which alerts the page shows by calling
`{% cv_alert %}`; none of them needs a theme override. See [Flash messages](messages.md) for the tag and the
frame's context.

### Custom alert frame

The default frame consumes `alert:dismissible` (default `alert-dismissible fade show`) and `alert:close`
(default `btn-close`). Register replacements, or use `None`/`""` to omit those contributions, without copying
the frame. Level classes, role, translated accessible name, conditional close control and dismissal hooks remain.
To change markup itself, ship `templates/crud_views/tags/alert.html`. A complete replacement with `notice` classes:

```django
{% load crud_views i18n %}
<div class="notice {% cv_button_class "alert" alert.level %}{% if alert.dismissible %} notice-dismissible{% endif %}{% if alert.extra_tags %} {{ alert.extra_tags }}{% endif %}"
     role="alert">
    {% cv_icon alert.icon_name "notice-icon" %}{% if alert.heading %}<strong>{{ alert.heading }}</strong>{% if alert.text %} {% endif %}{% endif %}{% include alert.body_template %}
    {% if alert.dismissible %}<button type="button" class="notice-close" data-cv-alert-dismiss aria-label="{% translate 'Close' %}"><span aria-hidden="true">&times;</span></button>{% endif %}
</div>
```

The `notice` names are examples; the class names are yours. What closing and accessibility rely on stays:

- `role="alert"` on the frame and `data-cv-alert-dismiss` on the close control. These two hooks are all
  [dismissal](javascript.md#dismissible-alerts) needs, also for alerts inserted after page load; keep only the new
  hook, not `data-bs-dismiss="alert"` next to it.
- The `{% if alert.dismissible %}` condition, so non-dismissible alerts render no control, and a `type="button"`
  control with the translated `aria-label`.
- `{% cv_button_class "alert" alert.level %}`, so the level colours keep following the `alert:*` class keys, and
  `alert.extra_tags`.
- The icon, the heading and `{% include alert.body_template %}`; the values are escaped already.

## Templates that follow Bootstrap's DOM

A dropdown is more than a set of classes: the nesting, the element types and the opening script differ between
frameworks, so the class table has no keys for it. These templates carry Bootstrap 5 dropdown markup
(`dropdown-toggle`, `data-bs-toggle="dropdown"`, `dropdown-menu`, `dropdown-item`) and are the ones to override when
your framework builds dropdowns differently:

- `tags/actions_menu.html` — the menu wrapper and its `<ul>`
- `tags/actions_menu_toggle.html` — the toggle button
- `snippets/language_selector.html` — the language dropdown

The button classes they use (`*:menu-wrapper`, `*:menu-toggle`, `*:hidden-label`) still come from the table, so an
override can keep calling `{% cv_button_class %}` for them.

In the core `crud_views` templates, these dropdown templates are the only ones with Bootstrap `data-bs-*`
attributes. The alert frame has none: its close control uses `data-cv-alert-dismiss` and the alert adapter, see
[Dismissible alerts](javascript.md#dismissible-alerts). Outside core, the `crud_views_object_detail` layouts
`layouts/accordion/group.html` and `layouts/tabs-vertical/object_detail.html` still use Bootstrap's collapse and tab
attributes.

## Disabled actions in overridden templates

The leaves `tags/button/action.html` and `tags/button/menu_item.html` receive `cv_disabled` and
`cv_disabled_reason`. If you override one of them, keep the `disabled data-cv-disabled` handling to support
`CRUD_VIEWS_INACCESSIBLE_ACTIONS = "disable"`; without it a disabled action looks enabled. The logic templates no
longer carry a branch of their own. See [Hide or disable inaccessible actions](inaccessible_actions.md).

## Authorized data in overridden templates

The library decides what a user may see and do before a template renders. An overridden template receives context
that is already authorized, and it should render that context rather than fetch or recompute anything. Hiding a
control in a template is presentation, not protection: every request is checked again on the server, whatever the
page showed.

| Template | What it receives |
|---|---|
| List and card templates | Only the rows the view's queryset permits. Do not query the model again in the template. |
| Button leaves (`tags/button/action.html`, `tags/button/menu_item.html`) | Only actions the user may see. A denied action never reaches the leaf, and a disabled one arrives with `cv_disabled`. |
| `crud_views/view_delete.content.html`, `snippets/delete/related_objects.html` | Every delete page has `has_protected_objects`; the stock content omits the whole form while true. With previews enabled, `protected_objects` holds only permitted labels. |
| `crud_views/view_guardian_manage.html` | Each view's own global-fallback policy in `views.<key>.guardian_policy`, and the strict helper policy in `guardian_config.get_objects_for_user`. |
| Formset templates | The editor's rows and choices, only on a page or row request the user passed the editor's gates for. |

The blocked-deletion notice is the one place where the list and the state differ. Decide whether to show the notice
from the flag and list the filtered labels, so the notice stays when every label is hidden:

```django
{% load crud_views i18n %}
{% if has_protected_objects %}
    {% if protected_objects %}
        {% cv_alert "error" heading=_("Deletion is blocked by protected relationships:") items=protected_objects %}
    {% else %}
        {% cv_alert "error" heading=_("Deletion is blocked by protected relationships") text=_("Other objects still reference this one; remove or reassign them before deleting it.") %}
    {% endif %}
{% endif %}
```

The labels arrive escaped like any other value. Wrap the include of this snippet in
`{% if related_summary or has_protected_objects %}`. A copy that tests `protected_objects` instead loses the notice
for a user who may view none of the protected objects. The flag is present even with previews disabled. Render the
confirmation form only inside `{% if not has_protected_objects %}` (and retain the custom-protection branch); this
also removes the form-contained cancel control. A copied alert leaf must render `alert.text` or
`alert.body_template` as well as heading/items to show the generic sentence. See
[Protected objects](delete_view.md#protected-objects).
