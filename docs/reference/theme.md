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

## Themeable column helpers

`Column1` through `Column12` keep their existing imports and field/layout API. Their Bootstrap defaults are
`col-md-N`; themes and projects can replace each width's **complete class string**, including responsive strings,
through the existing class registry. See the canonical [column utility inventory](buttons.md#the-class-table)
and [column contract](buttons.md#numbered-column-classes). These utility keys have no label-mode suffix.

### Column theme registration

Register only the widths your theme changes in its `AppConfig.ready()`:

```python
from django.apps import AppConfig


class MyAppThemeConfig(AppConfig):
    name = "myapp_theme"

    def ready(self):
        from crud_views.lib.button_classes import register_button_classes

        register_button_classes(
            {
                "form:column-6": "col-12 col-lg-6",
                "form:column-4": "col-12 col-lg-4",
            }
        )
```

With this app installed, `Column6("name", css_class="extra")` renders `col-12 col-lg-6 extra`, while an
unconfigured `Column2` keeps `col-md-2`. Classes resolve at each render, so layouts constructed before
registration also use the theme. Repeated rendering reads current configuration without accumulating classes
or mutating the layout. Later registration calls replace earlier values per key.

### Column project overrides

In project settings, override just the selected keys; all other widths retain their theme or package defaults:

```python
CRUD_VIEWS_BUTTON_CLASSES = {
    "form:column-4": "col-12 col-xl-4",
    "form:column-6": "",
    "form:column-12": None,
}
```

Precedence is package defaults → theme registration → project settings, independently for each key.
Here `Column4` uses `col-12 col-xl-4` instead of the theme string. Both `""` and `None` suppress the configured
width classes: `Column6("name", css_class="extra")` and `Column12("name", css_class="extra")` each retain only
`extra`. Constructor `css_class` adds caller classes to the resolved width; it does not replace that width.

### Column ownership boundaries

An explicitly authored subclass `css_class` default takes precedence over registry defaults, including inherited
custom defaults and explicit empty/`None` values. Direct instance assignment to `css_class` owns the whole class
string, replacing any previously assembled caller extras. These ordinary customization paths remain supported;
arbitrary metaprogramming is outside this contract.

For the audited installed Bootstrap 5 column template, the numbered helpers suppress its implicit `col-md`
fallback, so empty values and non-Bootstrap class strings stay intact. Current crispy 2.7 / crispy-bootstrap5
2026.9 and the declared crispy 2.0 / crispy-bootstrap5 2023.10 floor are tested. Intentional custom templates,
subclass templates, template-name hooks, same-name project overrides, alternate packs and changed stock source
retain ownership of their markup and any classes they emit. They must consume the column's `css_class` to show
the configured value; future pack compatibility is not assumed. Plain crispy `Column` is unchanged.

The active crispy pack's `Row`, surrounding layout templates and the theme's CSS/assets still determine the rest
of the grid. These twelve keys configure column classes; they do not provide a complete alternate-framework grid
or guarantee its visual layout.

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

The create, update, custom-form, delete and full-page workflow actions share one frame,
`crud_views/snippets/form_frame.html`:

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

Workflow fills `cv_form_body` around its complete choices/empty branch: both the “Workflow Action” heading and
actionable form are inside the frame. With no choices, the frame contains only the existing no-transitions
message, without a heading, form, CSRF input or controls. The workflow form keeps its implicit current-page
target. History stays before and outside the action frame; only its table is wrapped for local scrolling.
An empty history omits the whole history section. Wrapper and table classes are independent registry keys.

### Workflow transition widget

`cv_transition_presentation="buttons"` opts a WorkflowView into the public template override
`crud_views_workflow/widgets/transitions.html`. Its **`actions`** block encloses the ordered action loop.
The widget renders inside the existing shared page/modal form: it must not add a form, CSRF token, hidden/radio
transition input or generic submit. The page/helper keeps ownership; the no-choice page and generic modal branches
remain as documented above. The default radio presentation and its submit customization remain available.

| Context | Contract |
| --- | --- |
| `widget.name` | Actual submitted field name, including a form prefix |
| `widget.attrs` | Group ID, classes, invalid marker and composed description references; preserve these attributes |
| `widget.label` | Escaped final configured label; render normally as the group's `aria-label`, without a second force-escape |
| `widget.help_text`, `widget.help_id` | Optional raw general guidance and unique description ID; render once before actions, with literal escaping |
| `widget.comment_required` | Whether any offered action requires a comment; controls the one translated legend |
| `widget.actions` | Ordered offered actions, excluding state/condition/permission-unavailable actions |
| `action.name`, `action.id` | Exact submitted transition method and unique control ID |
| `action.label` | Full literal caption; force-escape, never interpret as HTML/templates |
| `action.variant`, `action.icon` | Raw transition `custom` metadata, or `None` when absent; do not interpolate variants into class names |
| `action.button_class` | Complete registry-resolved classes for a supported variant or the submit-label fallback; `""` is intentional suppression |
| `action.icon_class` | Resolved form host-icon classes; append to the button when nonempty |
| `action.icon_inline` | `False` for a host icon (including a suppressed host slot); otherwise render a truthy `action.icon` once through `cv_icon` |
| `action.help_text`, `action.help_id` | Optional literal guidance and unique target ID |
| `action.blockers`, `action.blockers_id` | Every ordered literal business message and its unique list ID |
| `action.comment_required` | Requires a comment when this action is submitted, independent of preview availability |
| `action.describedby` | Preserved external IDs plus general guidance, field errors and this action's help/blockers |

Keep native `button type="submit"`, `name=widget.name`, `value=action.name` and disable for blockers or a disabled
widget. Empty required comments do not disable actions. Preserve `role="group"`, its configured translated escaped
`aria-label`, and the visible crispy field label **without an activating `for`**. A group label must never focus or
activate a submit button. Preserve `is-invalid` without adding text-input `form-control`/`form-select` styling.

The field-label asterisk means an action must be selected. Only a REQUIRED action has its own visible asterisk
(hidden from assistive technology), the translated accessible **Comment required** suffix, and the conditional
**\* Comment required** legend. OPTIONAL/NONE actions can accept empty comments while the transition field stays
required. Absent help renders nothing; nonempty help and blockers are literal escaped text, not tooltips or HTML.

Buttons use eight base keys: `workflow:transition-primary`, `workflow:transition-secondary`,
`workflow:transition-success`, `workflow:transition-danger`, `workflow:transition-warning`,
`workflow:transition-info`, `workflow:transition-light`, and `workflow:transition-dark`. Their defaults are
`btn btn-<variant>`; see the [complete inventory](buttons.md#optional-workflow-defaults). The workflow app supplies
defaults, theme registration overrides them, and project settings override the theme. An explicit `""` or `None`
suppresses the selected classes. Missing, empty, non-string and unsupported variants use `form:submit:label`,
including its normal mode/base lookup and overrides, regardless of icon presence. There are no workflow mode-suffixed keys.

Append `action.icon_class` for host placement. For a truthy `action.icon` whose `action.icon_inline` is not `False`,
render `{% cv_icon action.icon %}` once, followed by a separating space and the force-escaped full `action.label`.
The existing `form:icon-host` slot controls host classes; empty/null values suppress the host icon without inline
fallback. Missing/unavailable icons retain the caption; a truthy unusable icon may leave harmless edge whitespace.
Use `form:hidden-label` for the accessible comment suffix and `form:cancel` for navigation Cancel. Generic form
label modes must not hide transition captions. Preserve full visible/accessibility captions and local wrapping, with ordinary page/modal
scrolling. The stock layout wraps transition/comment columns in button mode; custom layouts own equivalent wrapping.
All offered policies NONE removes the visible comment wrapper/label/help in both presentations; a hidden comment
input may remain. Button-mode controls/descriptions and Cancel use an instance namespace even with unprefixed forms.
Preserve generated IDs and reference crispy's explicit error paragraphs, not version-specific wrapper IDs. Django
4.2/crispy-bootstrap5 2026.3 can emit duplicate unreferenced `_error` wrappers; owned IDs and every full-document
description target must still be unique. This is not permission to duplicate control/error paragraph IDs.

Custom `get_layout_fields()` implementations can keep extra fields alongside `"transition"` and `"comment"`; see the
[workflow custom-form recipe](workflow_view.md#custom-forms-and-native-keyboard-behavior). Radio mode retains
`get_submit_button()` customization. Replacing `get_form_actions()` or the whole helper means adopting the no-generic-submit
contract and eligible Cancel yourself. Previously cached/rendered HTML bypasses normal refresh; arbitrary rewritten
markup is not automatically repaired. Python `_TransitionButtons`, private execution/refusal helpers and `_workflow_*`
members are implementation details, not public extension APIs. The template path, `actions` block and context above
are public theme surfaces for the stability freeze. Copied templates adopt the five added action fields above
(`variant`, `icon`, `button_class`, `icon_class`, `icon_inline`) to show transition metadata; existing copies retain
their own rendering until updated. Preserve the `actions` block, native submits, description targets and escaping.

Native Enter in a single-line input can activate the **first submit control in tree order when enabled**, sending its
valid transition name. Browsers do not skip a disabled first submit to find another enabled action. Enter in the stock
comment Textarea inserts a newline. Keep these native semantics: no hidden sentinel/default transition or workflow
JavaScript. Missing/invalid-name rejection still applies, but cannot distinguish valid implicit activation from a click.

### Optional workflow classes

In a theme's `AppConfig.ready`, check app availability after discovery. Keep ordinary theme registrations in
either case, and omit all workflow keys when workflow is absent to avoid W362. This complete recipe uses the
existing registration API; use it as the theme config's `ready` method:

```python
from django.apps import apps
from crud_views.lib.button_classes import register_button_classes


def ready(self):
    register_button_classes({"form:actions": "d-flex flex-wrap gap-2"})
    if apps.is_installed("crud_views_workflow"):
        register_button_classes(
            {
                "workflow:badge-primary": "badge bg-primary-lt",
                "workflow:badge-secondary": "badge bg-secondary-lt",
                "workflow:badge-success": "badge bg-success-lt",
                "workflow:badge-danger": "badge bg-danger-lt",
                "workflow:badge-warning": "badge bg-warning-lt",
                "workflow:badge-info": "badge bg-info-lt",
                "workflow:badge-light": "badge bg-light-lt",
                "workflow:badge-dark": "badge bg-dark-lt",
                "workflow:badge-purple": "badge custom-purple",
                "workflow:history-wrapper": "table-responsive",
                "workflow:history-table": "table table-hover",
                "workflow:transition-success": "btn btn-success-lt",
                "workflow:transition-danger": "btn btn-danger-lt",
            }
        )
```

The conditional belongs inside `ready`, not at module import. Workflow's app-owned defaults are a lower layer;
theme authors do not change that declaration or call private cache getters. Supply complete classes without
template evaluation or colour formatting. A custom colour is recognized only with workflow installed.
See [project overrides and disabled values](workflow_view.md#project-workflow-classes).

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
the full-page branch and implicit current-page target. Extend the shared frame around both branches and remove
its unused `crispy_forms_tags` load:

```django
{% extends "crud_views/snippets/form_frame.html" %}
{% load i18n crud_views %}
{% block cv_form_body %}
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
{% endblock %}
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
| `crud_views/view_delete.content.html`, `snippets/delete/related_objects.html` | Every delete page has independent `has_protected_objects`; omit the whole form while true. Detailed context has selected `protected_objects` and `related_objects`, independent full `related_summary` and `delete_preview_truncated`; these are absent when previews are off. |
| `crud_views/snippets/delete/protected_objects.html` | Independent body inside the shared alert frame, consuming caller-context `items` with model instance `obj` and always `url=None`. Render escaped plain text; model fields use `item.obj.field`. |
| `crud_views/view_guardian_manage.html` | Shared `manage_*` cards, including each `manage_views` row's `guardian_policy` and `manage_guardian.get_objects_for_user`; legacy dictionaries remain available. See [manage contracts](#structured-manage-contracts). |
| Formset templates | The editor's rows and choices, only on a page or row request the user passed the editor's gates for. |

The blocked-deletion notice is the one place where the list and the state differ. Decide whether to show the notice
from the flag and list the filtered labels, so the notice stays when every label is hidden:

```django
{% load crud_views i18n %}
{% if delete_preview_truncated %}
    {% cv_alert "warning" text=_("This preview is shortened. Additional objects are not shown.") %}
{% endif %}
{% if has_protected_objects %}
    {% if protected_objects %}
        {% with items=protected_objects %}
            {% cv_alert "error" heading=_("Deletion is blocked by protected relationships:") body_template="crud_views/snippets/delete/protected_objects.html" %}
        {% endwith %}
    {% else %}
        {% cv_alert "error" heading=_("Deletion is blocked by protected relationships") text=_("Other objects still reference this one; remove or reassign them before deleting it.") %}
    {% endif %}
{% endif %}
{% if related_summary %}
    {% if delete_preview_incomplete %}
        {% cv_alert "warning" heading=_("Some related objects that will also be deleted (partial counts):") items=related_summary_items %}
    {% else %}
        {% cv_alert "warning" heading=_("The following related objects will also be deleted:") items=related_summary_items %}
    {% endif %}
{% endif %}
{% if related_objects %}
    {% with items=related_objects %}
        {% cv_alert "warning" heading=_("Details about the related objects to be deleted:") body_template="crud_views/snippets/delete/related_objects_tree.html" %}
    {% endwith %}
{% endif %}
```

The protected body explicitly enables autoescape for labels. Do not pass these dictionaries through generic alert
`items=` normalization. The shared frame still owns heading, icon, role and dismissal. Protected URLs are always
`None`; existing `if item.url`/`else` bodies remain compatible and take the text branch. Selected cascade links keep
ordinary full-page navigation from a delete modal and their existing hook behavior; actual requests enforce access.
See [cascade linking and preview cost](delete_view.md#linking-related-objects).
Wrap the include of this snippet in
`{% if related_summary or has_protected_objects or related_objects or delete_preview_truncated %}`.
Keep summary and detail guards independent: a selected solo root renders even with an empty summary, and the root
counts toward the shared limit. Root alone at limit one is exact-at-cap; root plus a visible child overflows.
Application-redacted summaries do not suppress selected details; empty details omit their heading and list.
The shortening notice appears once above the lists on actual visible overflow; preserve the separate incomplete
warning in the content template. A copy that tests `protected_objects` instead loses the notice
for a user who may view none of the protected objects. The flag is present even with previews disabled. Render the
confirmation form only inside `{% if not has_protected_objects %}` (and retain the custom-protection branch); this
also removes the form-contained cancel control. A copied alert leaf must render `alert.text` or
`alert.body_template` as well as heading/items to show the generic sentence. See
[Protected objects](delete_view.md#protected-objects).

## Structured manage contracts

Core `crud_views/view_manage.html` owns the shared page; Guardian's
`crud_views/view_guardian_manage.html` extends it. The [manage reference](manage.md) explains the visible
semantics. This inventory is the public theme surface before the 1.0 freeze, including the default-off
[Access check](manage.md#access-check) card and [cv_access](manage.md#cv_access) command (#370).
#371's configuration-dump command remains a separate follow-up.

### Manage blocks

Each block replaces its whole card/strip at the stated position. Existing overrides keep their own markup;
they do not acquire actor/superuser enhancements until migrated. `cv_content` remains the enclosing page block.

| Block | Position and prepared context |
|---|---|
| `manage_checks` | Main-column issues from `manage_checks` |
| `permission_holders` | Main Permissions card from `manage_permissions` |
| `manage_access_trace` | Main Access check card below Permissions and above Views, only when `manage_access_trace` is not `None` |
| `manage_views` | Main Views card from `manage_views` |
| `manage_presentation` | Main collapsed Presentation from `manage_presentation` |
| `manage_checks_clean` | Side-column clean strip from `manage_checks` |
| `manage_viewset` | Side ViewSet card from `manage_facts` |
| `manage_hierarchy` | Side Hierarchy card from `manage_hierarchy` |
| `manage_urls` | Side URL names card from `manage_routes` |
| `ancestor_policy` | Side Ancestor policy from `manage_ancestor_policy`; anchor `cv-ancestor-policy` |
| `guardian_config` | Side Guardian card from `manage_guardian`, when present |

Keep both checks blocks when relocating checks: failures and clean results occupy different columns.

### Prepared manage context

Strings are plain data for Django autoescaping, not trusted HTML. Do not mark labels, class representations,
check messages or route text safe. Keep visibility policy intact, including omitting user names when disabled.

| Context key | Shape |
|---|---|
| `manage_permissions` | Dict: `columns`, `actor`, `groups`, `users`, `users_overflow`, `show_users`, `superusers` |
| `manage_access_trace` | `None` with tracing disabled; enabled mapping described below, shared by core and Guardian |
| `manage_views` | Ordered list of view dicts: `key`, `class_path`, `route_name`, `route`, `route_error`, `requirement`, `permission`, `parent_requirement`, `requirement_metadata_error`, `guardian_policy`, `sections`; Guardian also adds `parent_only_requirement` |
| `manage_checks` | Dict: `count`, `messages`; each message has `id`, `severity`, `message`, `hint` |
| `manage_facts` | Ordered list of field rows: `key`, `value`, `source`, `is_default`; the icon row also has `icon` |
| `manage_hierarchy` | Dict: `parents`, `children`, `route_error`; entries have `name`, `model`, `resource`, `route_name`, `route`, `route_error`, `url` (links upwards only) |
| `manage_routes` | Ordered list of `key`, `name`, `route`, `route_error` dicts |
| `manage_ancestor_policy` | Dict: `as_ancestor`, `requests`; the same structure as the legacy ancestor key below |
| `manage_presentation` | Dict: `sections`, `set_count`, `default_count`; section dicts have `key`, `label`, `entries`, `default_count` |
| `manage_guardian` | Guardian-only dict: `get_objects_for_user` with `policy`, `accept_global_perms`, `use_groups` |
| `manage_docs_base_url` | One URL string, supplied by the manage class attribute, for every help link |

Permission columns have `key`, `permission` (full Django string) and `codename`. Actor/holder rows have `id`,
`label`, `member_count`, `cells`; cells have `key`, `model` (boolean), `object_count` (integer or `None`).
`superusers` has `count` and `names`; users are split at 20 rows. Core object counts are `None`.
Guardian actor counts use strict effective access, while direct holder counts use configured grant tables.
The actor defaults to the viewer. Only a successful this-ViewSet trace selection replaces it with the supplied
user's row, marked `(checked below)`; path mode, invalid submissions and disabled tracing retain `(you)`.
The selected user never replaces `request.user`, the session or the holder rows. Guardian inherits this adapter
and uses its own `get_manage_actor_row` override, preserving strict counts independently of endpoint fallback.

View sections have `key`, `label`, `entries`, `default_count`; ordinary entries have `key`, `value`, `source`,
`is_default`, `unknown`. Configuration source and default classification are separate. Presentation rows use
the field-row shape, with button-specific metadata for context-button entries. Explicit empty `extends` keeps
its effective setting fallback and an additional `declared_value` of `"''"`. Normal ViewSet constructor keys
are recorded before validators infer defaults. Pydantic `model_construct` bypasses that record and is unsupported
for declaration provenance; this is not a general guarantee about other Pydantic construction paths.

### Access trace mapping

The enabled context always contains the eight base fields below. The web adapter adds the optional `error_field`
only for user/path validation failures. Data remains escaped text; exception messages are deliberately disclosed
by this opt-in feature. The direct builder returns only the base fields for valid inputs, using the supplied
username; the web adapter preserves the user's typed selector.

| Field | Meaning |
|---|---|
| `mode` | `viewset` or `path` for a valid selection; raw/empty mode before validation. |
| `user_input` | Typed username/PK selector; the direct builder uses the supplied user's username. |
| `pk_input` | Optional object PK, or empty string. |
| `path_input` | Typed path/full URL, or empty string. |
| `error` | Validation/unknown-user message, or `None`. |
| `actor` | Selected user identity: string `pk`, string `username`, boolean `active` and `anonymous`; `None` before a valid selection. |
| `rows` | All registered view rows in ViewSet mode; empty otherwise. |
| `trace` | Version-1 scalar trace dictionary in path mode; `None` otherwise. |
| `error_field` | Optional web-adapter field: `user` for an empty/unknown selector, or `path` for an empty/invalid path. It is absent before submission, on valid input, for invalid-mode errors, and from the direct builder. Use it with `mode` to associate `error` with the submitted form's input. |

### Access trace rows

| Field | Meaning |
|---|---|
| `key` | Registered view key, including backend-only and POST-only views. |
| `path` | Reversed path using supplied parent coordinates and optional own PK, or `None`. |
| `instruction` | `needs an object pk`, `use the path field`, or `None` when a trace exists. |
| `trace` | Version-1 scalar trace dictionary, or `None` when coordinates cannot be supplied. |

There is no per-row HTTP-method selector. Parent coordinates come from the hosting URL in web mode;
extra contributed arguments require the path form. See [trace limits](manage.md#diagnostic-limits).

### Request-free manage builders

Every method below takes explicit `(viewset, user)` and does not read `self.request`:

| Method | Result |
|---|---|
| `get_manage_actor_row` | The supplied actor row |
| `get_manage_permissions` | Permission matrix |
| `get_manage_access_trace` | Explicit-user path or ViewSet trace mapping; keyword-only `mode`, `object_pk=None`, `path=None`, `route_kwargs=None` |
| `get_manage_views` | View inventory and requirement metadata |
| `get_manage_checks` | Scoped check results |
| `get_manage_facts` | Identity rows |
| `get_manage_hierarchy` | Hierarchy; optional keyword-only `route_kwargs=None` supplies current URL coordinates |
| `get_manage_routes` | Generated relative routes |
| `get_manage_ancestor_policy` | Ancestor configuration |
| `get_manage_presentation` | Shared presentation configuration |
| `get_manage_guardian` | Guardian-only helper policy |

The trace builder's full signature is
`(self, viewset, user, *, mode, object_pk=None, path=None, route_kwargs=None)`.
Call it on a manage instance without `request`, supplying a resolved user, `mode="path"` with `path`, or
`mode="viewset"` with optional object PK and parent route kwargs. It delegates actual authorization to
`crud_views.lib.access_trace.trace_access(path, user)` and returns the scalar `AccessTrace.to_dict()` projection;
`resolve_trace_user(identifier)` selects fresh users. `AccessTrace` and `AccessStep` and their complete
[version-1 fields](manage.md#version-1-document) are public. The request adapter, recorder observations,
queryset captures and runner helpers are internal implementation details, not theme APIs.

Configuration/matrix builders describe policy; the trace builder runs the bounded diagnostic gates. None
authorizes the hosting request. The web adapter remains responsible for admission,
active-account/group/mode checks and actual ancestor authorization. Auth-reading builders use the **supplied**
ViewSet's registered manage class for the existing nested database/auth guard before diagnostic reads. If that
class is absent, they raise the fixed
`ImproperlyConfigured("Manage diagnostics require a registered manage view")`. A Resource ViewSet is an actual
absence example; this does not add Resource diagnostics. `manage_views_enabled="no"` still registers model
AutoManageView/URLs and controls availability/context actions. Pure configuration/route projections have no
auth-read dependency. View metadata that needs permission maps, and Guardian's enriched inventory, also use
the auth guard. Pass `route_kwargs` explicitly for hierarchy links instead of inventing an object or request.
For traces, pass those coordinates explicitly to the trace builder too. It does not enforce the web opt-in setting
or host admission itself, matching the always-available command; callers own their exposure policy.

### Requirement descriptions

The public `CrudView.cv_get_requirement()` classmethod returns a small dictionary:

```python
{"kind": "permission", "value": "change", "ancestor_applies": True}
```

`kind` is `permission`, `group`, `none` or `custom`. `value` is a permission-map key for `permission`, a group
name for `group`, and `None` for `none`/`custom`. `ancestor_applies` says whether the ancestor policy contributes
to the description; it is not an opt-out from enforcement. The manage page derives the parent badge from
the policy rather than duplicating it in this method. This describes configuration, not a user's access result.

Shipped owning gates describe themselves. If a project overrides `has_permission()`, override
`cv_get_requirement()` alongside it to describe the actual gate; otherwise it is reported as custom. Arbitrary
project `dispatch()`/`get_object()` changes cannot be inferred from metadata. Use the separate bounded trace
for observed access; changing the requirement description does not grant access.

### Shared access trace partial

Both the path result and expanded ViewSet rows include `crud_views/includes/access_trace.html` with `trace`
set to a version-1 dictionary. It also accepts `step` for a plan/step facts row or `result` for a status badge;
nonempty `result` takes precedence, then `step`, then the full `trace`. Pass only the relevant input using
Django's `only` include option. `unavailable` reuses the `manage:trace-not-evaluated` class.
Core and Guardian use the same partial and `manage_access_trace` block. Override
the shared partial rather than copying Guardian's page; for example, a theme-owned minimal textual projection
can use this template at that path (theme CSS supplies the class):

```django
{% if result %}
  <span class="theme-trace-result">{{ result }}</span>
{% elif step %}
  <span>{{ step.n }} {{ step.kind }} {{ step.result }} {{ step.message }}</span>
  {% if step.exception %}<span>{{ step.exception.class }}: {{ step.exception.message }}</span>{% endif %}
{% else %}
<section class="theme-access-trace">
  <p>{{ trace.path }} — {{ trace.outcome }}</p>
  {% for step in trace.steps %}
    <p>{{ step.n }}. {{ step.kind }}: {{ step.result }} {{ step.message }}
      {% if step.exception %}{{ step.exception.class }}: {{ step.exception.message }}{% endif %}
    </p>
  {% endfor %}
  {% for limitation in trace.untraced %}<p>{{ limitation }}</p>{% endfor %}
</section>
{% endif %}
```

For the full stock presentation, retain planned/reached provenance, deciding step, counts and limitations from
the shared partial. Whole-card overrides own both GET forms and their feedback; preserve the enabled/disabled
guard, labels, help link, escaping and actor/viewer separation. Do not call permission gates from templates.

### Legacy manage context and includes

The following keys remain for existing overrides. Stock templates do not evaluate the lazy legacy getters.
Overriding `get_view_data()` or `get_permission_holders()` affects only the old keys, not the new card builders.

| Context key | Preserved shape and evaluation |
|---|---|
| `cv` | ViewSet instance |
| `data` | Lazy list of `viewset` (key), `django` (permission string), `has_permission` rows |
| `views` | Lazy ordered mapping keyed by view key, containing `base`, `templates`, `icons` mappings; Guardian adds `base.guardian_mixin` and `guardian_policy` |
| `permission_holders` | Lazy list of `group`, `permission`, `has_model_perm`, `object_count`, `users` dicts; legacy Guardian counts still use generic `GroupObjectPermission` |
| `show_users` | Existing boolean setting value |
| `ancestor_policy` | Dict: `as_ancestor` has `provider`, `effective_provider`, `accept_global_perms`; `requests` is `None` at top level, otherwise `cascade`, `read`, `write` declared/effective dicts and exact `actions` pairs |
| `guardian_config` | Guardian-only dict: `parent_viewset` (description or `None`), `ancestor_policy` (`provider`, `accept_global_perms`), `get_objects_for_user` (strict helper policy) |

Legacy `views.<key>.guardian_policy` retains `global_fallback_applicable`, `cv_guardian_accept_global_perms`
(`None` if inapplicable) and `effective_policy`. New rows instead use `guardian_policy.applicable`,
`accept_global_perms`, `effective_policy`, `tooltip`. The removed ViewSet-level
`guardian_config.cv_guardian_accept_global_perms` is not restored.

The legacy `crud_views/snippets/guardian/config_table.html` remains unchanged for explicit project includes,
fed by the preserved `guardian_config` shape. This compatibility example is for an existing override;
new themes should use the prepared cards:

```django
{% extends "crud_views/view_guardian_manage.html" %}
{% block guardian_config %}
    <div class="table-responsive">
        {% include "crud_views/snippets/guardian/config_table.html" %}
    </div>
{% endblock guardian_config %}
```

Manage additions require no optional app in core. Guardian behavior remains in its extension. Review the
[paired migration](../migrating-1.0.md#structured-manage-cards) when replacing complete cards or copying markup.

### Manage class registration

Use the existing registry in your theme's `AppConfig.ready()`. These example class names are supplied by the
theme's own CSS; all unmentioned keys retain their defaults:

```python
def ready(self):
    from crud_views.lib.button_classes import register_button_classes

    register_button_classes({"manage:help": "theme-help", "manage:row-default": "theme-default"})
```

All nineteen keys are inventoried with exact defaults in [Buttons](buttons.md#the-class-table): `manage:badge-model`,
`manage:badge-objects`, `manage:badge-permission`, `manage:badge-group`, `manage:badge-policy-global`,
`manage:badge-policy-strict`, `manage:badge-policy-na`, `manage:row-default`, `manage:help`,
`manage:trace-allowed`, `manage:trace-denied`, `manage:trace-not-found`, `manage:trace-login-redirect`,
`manage:trace-error`, `manage:trace-no-such-route`, `manage:trace-passed`, `manage:trace-skipped`,
`manage:trace-not-reached`, `manage:trace-not-evaluated`.
Project `CRUD_VIEWS_BUTTON_CLASSES` entries override theme registrations per key; `""` or `None` clears classes.
Replacing the default-row class also replaces its CSS muting without affecting the switch's data markers.

Retain the [external manage assets](javascript.md#manage-defaults) through the existing asset loader.
`data-cv-manage` scopes the page; one `data-cv-show-defaults` control in `data-cv-defaults-control` handles both
Views and Presentation. `data-cv-config-row`, `data-cv-default-row`, `data-cv-section` and
`data-cv-default-count` connect rows and server-translated hidden counts. Start with all rows visible and hide
the control until initialization succeeds. `data-cv-manage-help` identifies documentation links;
`data-cv-tooltip` delegates badge tooltip behavior to the existing adapter. No JS persistence or inline assets
are introduced, and native disclosures work without JavaScript.

German translation sources are `src/crud_views/locale/de/LC_MESSAGES/django.po` and
`src/crud_views_guardian/locale/de/LC_MESSAGES/django.po`. Keep both catalogs in translation verification when
changing shared or Guardian-only diagnostics copy. This inventory names their ownership; browser/translation
acceptance must verify the rendered locale rather than infer it from a catalog filename.
