# Buttons

django-crud-views gives every action button a **semantic variant** (`primary`, `secondary`, `tertiary`, `danger`) and
resolves the CSS classes of every button from one layered table keyed `location:slot`. A theme restyles all buttons by
registering classes, and only needs a template when the markup itself differs. The button templates are split into
one-line **logic templates** and three presentation-only **leaves**.

The public module is `crud_views.lib.button_classes`.

## Variants

A variant says how prominent or dangerous an action is, independent of the theme. The four values are the members of
`crud_views.lib.view.variant.Variant`:

| Value | Meaning |
|---|---|
| `primary` | the main action of a page or row |
| `secondary` | an ordinary action |
| `tertiary` | a low-key action |
| `danger` | an action that destroys data |

The variant of an action button comes from the view the button targets, through the class attribute
`cv_action_variant`:

| View | Default `cv_action_variant` |
|---|---|
| `CreateView` (key `create`) | `primary` |
| `PolymorphicCreateSelectView` (key `create_select`) | `primary` |
| `DeleteView` (key `delete`) | `danger` |
| every other view | `secondary` |

```python
class AuthorDetailView(DetailViewPermissionRequired):
    cv_action_variant = "tertiary"  # every button that targets this view
```

A single button can override the variant of its target:

- `ContextButton.variant` is `str | None`, default `None` (the target view's variant). See
  [Context buttons](context_buttons.md).
- `CardAction.variant` is `str | None`, default `None` (the target view's variant). See
  [Card list view](card-list-view.md#cardaction-fields).

A value other than the four variants fails the system check `viewset.E209`.

## The class table

The classes of a button are looked up by a `location:slot` key. The **location** says where the button sits, the
**slot** says which part of it.

Action buttons take a third segment, the label mode: `location:variant:mode` with `mode` one of `label`, `icon`, `both`
(see [Card list view](card-list-view.md) for how a card button gets its mode; toolbar and row buttons are `icon`). The
lookup reads `location:variant:mode` when that key is defined and falls back to `location:variant` otherwise — one
step, no chaining. No default defines a mode key: the table below is still the full list of shipped keys. A theme
defines only the modes that differ from its base entry.

Because every toolbar and row button is `icon` today, `context:<variant>:icon` and `list:<variant>:icon` take effect
immediately — registering them restyles every toolbar and row button — while their `:label` and `:both` keys are read
only once #216 lets those locations show a label.

| Key | Default |
|---|---|
| `context:primary` / `context:secondary` / `context:tertiary` / `context:danger` | `btn btn-outline-primary btn-lg` |
| `list:primary` / `list:secondary` / `list:tertiary` / `list:danger` | `btn btn-outline-primary btn-xs` |
| `card:primary` | `btn btn-primary btn-sm` |
| `card:secondary` | `btn btn-secondary btn-sm` |
| `card:tertiary` | `btn btn-outline-secondary btn-sm` |
| `card:danger` | `btn btn-secondary btn-sm` |
| `context:container` | `btn-group btn-group-lg` |
| `list:container` | `btn-group btn-group-xs` |
| `card:container` | `d-flex gap-2` |
| `context:container-list` / `list:container-list` / `card:container-list` | `None` |
| `context:container-item` / `list:container-item` / `card:container-item` | `""` |
| `context:container-single` / `list:container-single` / `card:container-single` | `"container"` |
| `context:container-tag` / `list:container-tag` | `"fieldset"` |
| `card:container-tag` | `"div"` |
| `context:container-label` / `list:container-label` | `"Actions"` (translated) |
| `card:container-label` | `None` |
| `context:menu-toggle` | `btn btn-outline-primary btn-lg` |
| `list:menu-toggle` | `btn btn-outline-primary btn-xs` |
| `card:menu-toggle` | `btn btn-secondary btn-sm` |
| `context:menu-wrapper` / `list:menu-wrapper` | `btn-group` |
| `card:menu-wrapper` | `dropdown` |
| `menu:item` | `dropdown-item` |
| `form:submit` | `btn btn-primary` |
| `form:cancel` | `btn btn-secondary` |
| `form:delete` | `btn btn-primary` |
| `form:filter-submit` | `btn btn-primary` |
| `form:filter-reset` | `btn btn-secondary` |
| `formset:control` | `btn btn-light` |
| `formset:container` | `btn-group` |
| `formset:control-danger` | `btn btn-danger` |
| `card-order:toggle` | `btn btn-outline-secondary` |
| `card-order:container` | `btn-group btn-group-sm` |
| `language:toggle` | `btn btn-outline-secondary` |
| `object-detail:property-detail` | `btn btn-link p-0 ms-1 align-baseline text-muted` |
| `context:active` / `list:active` / `card:active` | `active` |
| `menu:active` | `active` |
| `card-order:active` | `active` |
| `card:flex` | `flex-grow-1` |
| `context:hidden-label` / `list:hidden-label` / `card:hidden-label` | `visually-hidden` |
| `card:root` | `card mb-3` |
| `card:body` | `card-body` |
| `card:title` | `card-title` |
| `alert:error` | `alert alert-danger` |
| `alert:warning` | `alert alert-warning` |
| `alert:success` | `alert alert-success` |
| `alert:info` | `alert alert-info` |
| `alert:debug` | `alert alert-secondary` |
| `context:icon-host` / `list:icon-host` / `card:icon-host` / `menu:icon-host` | `{name_class}` |

The default table has 64 keys: the rows with four variants stand for four keys each, the rows with three locations
for three, the `*:icon-host` row for four. The `context` and `list`
buttons look the same for every variant by default, the `card` buttons distinguish them. Mode keys (`card:tertiary:icon`
and the like) are addressable but not shipped: none is in the default table, and the count stays 64.

The table holds what a theme restyles: classes. What the markup needs to work stays in the templates and is not
configurable here: the element, `href`, `type`, `disabled`, the `data-cv-*` attributes, `aria-*`, `cv-key`,
`dropdown-toggle`, `data-bs-toggle` and the like. The presentational words the leaves used to hard-code are keys:
`<location>:active` for the button that points at the current page, `card:flex` for a stretched card action and
`<location>:hidden-label` for the screen-reader text of an icon-only button. A theme on another framework registers
its own words there (`is-active`, `is-sr-only`, `sr-only`) and overrides no leaf. `None` on a `hidden-label` key
makes that text visible; set the key to your framework's screen-reader-only utility instead.

Three keys style the stock card itself rather than a button: `card:root` is the outer `<div>`, `card:body` the
`<div>` inside it, and `card:title` the `<h5>` heading. The actions inside the card keep `card:container`. Where the
actions sit (in the body or in a footer) is structure, not classes: see
[Custom Card Template](card-list-view.md#custom-card-template).

### Button row as a list

Three keys per container location (`context`, `list`, `card`) set the structure of the button container, for design
systems that build a button row as a list and leave the row out for a single button:

| Key | Default | Meaning |
|---|---|---|
| `<location>:container` | see above | class of the outer element (unchanged) |
| `<location>:container-list` | `None` | `None`: the buttons are direct children of the container. A str: they sit in a `<ul>` with that class inside the container; `""` renders `<ul>` without a `class` attribute |
| `<location>:container-item` | `""` | class of each `<li>`; read only when `container-list` is a str |
| `<location>:container-single` | `"container"` | `"container"`: a single item renders inside the container as usual. `"bare"`: a single item renders on its own, with no container and no list |

With `container-list` set, two buttons and a menu render as:

```html
<fieldset class="btn-row" aria-label="Actions" cv-context-container="true">
    <ul class="btn-row-list">
        <li class="btn-row-item"><a class="btn …" cv-key="update">…</a></li>
        <li class="btn-row-item"><a class="btn …" cv-key="delete">…</a></li>
        <li class="btn-row-item"><div class="btn-group">… the "More actions" menu …</div></li>
    </ul>
</fieldset>
```

An item is an inline button or the [action menu](action_menus.md) toggle, which gets its own `<li>` only when the
group has menu items. "Single" means one *rendered* item: inaccessible actions that are hidden don't count, and one
inline button plus a menu are two items and keep the container. A group whose only item is the menu renders the
menu bare. A group with no items renders nothing: no container, no list (#265). A bare item carries no `cv-<location>-container` attribute.

The `<li>` comes from the container leaf, never from a button leaf, so a button rendered on its own with
`{% cv_context_button %}` never gets one. A `container-single` value other than `"container"` or `"bare"` is the
system check error `crud_views.E364`. These keys have no label-mode variants.

### Container element and label

Two more keys per container location set the container's element and its accessible name (#266):

| Key | Default | Meaning |
|---|---|---|
| `<location>:container-tag` | `"fieldset"` for `context` and `list`, `"div"` for `card` | element of the container; `None`, `""` or a non-str renders `div` |
| `<location>:container-label` | `"Actions"` for `context` and `list`, `None` for `card` | `aria-label` of the container; `None` or `""` renders none |

The label is passed through `gettext` when the container renders, so the default reads "Aktionen" on a German page,
and a label of your own is translated when your catalogue has it as a msgid: mark it with `gettext_noop("…")` so
`makemessages` finds it (a `gettext_lazy` value is not a str and fails check `crud_views.E361`). The label renders
whatever the tag: a theme that switches a location to `div` sets its label to `None` too, since `aria-label` on a
plain `div` has no role to name.

```python
CRUD_VIEWS_BUTTON_CLASSES = {"list:container-tag": "div", "list:container-label": None}
```

The five `alert:*` keys colour the one alert frame, `tags/alert.html`, which renders every alert in the package:
the slot is the alert's level (`error`, `warning`, `success`, `info`, `debug`). See [Flash messages](messages.md).

The four `*:icon-host` keys are format strings: the class a [host-placed icon](icons.md#host-placement) adds to
its button, with `{name_class}` standing for the icon library's name class. `"card:icon-host": "icon {name_class}"`
adds a base class on card buttons only; `None` or `""` switches host icons off at that location (no class and
nothing inline). The filter toggle is the exception: with `context:icon-host` off it falls back to its two icon spans,
which show the standalone icons. The keys have no effect for an icon library without `placement: "host"`.

## `CRUD_VIEWS_BUTTON_CLASSES`

A dict of `location:slot` key to a string of CSS classes. It is merged per key over the package defaults (and over theme
registrations), so list only what you change:

```python
CRUD_VIEWS_BUTTON_CLASSES = {
    "form:filter-reset": "btn btn-outline-secondary",  # override a default
    "card:primary": "btn btn-success btn-sm",
    "list:danger": "btn btn-outline-danger btn-xs",
    "form:cancel": None,  # no classes at all
}
```

`None` (or `""`) switches the classes of that key off. Any other non-string value renders nothing and is reported by
`crud_views.E361`. A key that is neither in the table above nor a valid `location:variant:mode` is reported by
`crud_views.W362` (a typo, or an unknown label mode).

A mode key set to `None` switches that mode off; it does not fall back to the base key.

Layers merge per key before the mode fallback runs, so key specificity beats layer order. Given a
theme that registers `card:tertiary:icon`, a project setting `"card:tertiary": "btn btn-sm btn-success"` recolours the
labelled tertiary card buttons and **not** the icon-only one — override `card:tertiary:icon` as well.

Project entries win per key. `CRUD_VIEWS_FILTER_RESET_BUTTON_CSS_CLASS` was replaced by
`CRUD_VIEWS_BUTTON_CLASSES["form:filter-reset"]`; while the old setting is defined the system check
`crud_views.E360` fails.

`get_button_classes()` returns the resolved, cached dict; do not mutate it. `get_button_class(location, slot, mode=None)`
returns one resolved string (`""` for `None`, an unknown key or a non-string value), reading `location:slot:mode` when
`mode` is given and that key is present.

## Registering classes from a theme

A theme app registers its default classes from `AppConfig.ready()`, so projects need no configuration:

```python
# myapp_theme/apps.py
from django.apps import AppConfig


class MyAppThemeConfig(AppConfig):
    name = "myapp_theme"

    def ready(self):
        from crud_views.lib.button_classes import register_button_classes

        register_button_classes(
            {
                "card:primary": "button is-primary is-small",
                "card:secondary": "button is-light is-small",
                "form:submit": "button is-primary",
            }
        )
```

`register_button_classes(classes)` takes a dict of key to classes and resets the resolved cache.

### Precedence

```
button classes = package defaults + theme registrations + CRUD_VIEWS_BUTTON_CLASSES
```

Later wins per key, so project settings always win over a theme, and a theme wins over the package. If two theme apps
register the same key, the one whose `ready()` runs later wins, which is the one later in `INSTALLED_APPS`.

## Rendering

`{% cv_button_class location slot [mode] %}` renders the resolved classes of one key (autoescaped). It is available in
`{% load crud_views %}` and in `{% load crud_views_object_detail %}`:

```html+django
{% load crud_views %}
<button type="button" class="{% cv_button_class 'card' 'primary' %}">...</button>
<a href="{{ url }}" class="{% cv_button_class cv_location cv_variant %}">...</a>
<a href="{{ url }}" class="{% cv_button_class cv_location cv_variant cv_label_mode %}">...</a>
```

The bundled action leaf passes `cv_label_mode` as the third argument; the filter toggle
(`crud_views/tags/context_action_filter.html`) passes `"icon"`, so `context:<variant>:icon` reaches it like any other
icon-only context button.

Use it in templates you write or override instead of a literal class, and the button follows the table. A literal
class in a `template_code` keeps working; it is simply not themed.

## Logic templates and leaves

The action buttons are rendered in two layers.

**Logic templates** are one-line templates that call a tag. **Do not copy them**; override a leaf instead. They stay
in the package so that a change to the logic reaches every theme:

| Template | Renders |
|---|---|
| `crud_views/tags/context_action.html` | one context toolbar button |
| `crud_views/tags/list_action.html` | one list row button |
| `crud_views/tags/card_action.html` | one card button (and its POST form) |
| `crud_views/tags/actions_menu_item.html` | one [action menu](action_menus.md) item |
| `crud_views/tags/context_actions.html` | the context toolbar container |
| `crud_views/columns/actions.html` | the list row container |
| `crud_views/tags/card.html` | the card |

**Leaves** are the presentation-only templates a theme overrides. They receive a flat contract (below), never raw
view data:

| Leaf | Renders |
|---|---|
| `crud_views/tags/button/action.html` | one action button (`<a>` or `<button>`) |
| `crud_views/tags/button/menu_item.html` | one dropdown item |
| `crud_views/tags/button/container.html` | the group of buttons plus the menu; receives `cv_buttons`, `cv_group` and `cv_location`, and reads its structure, element and label with `{% cv_container_layout cv_location cv_buttons cv_group %}` (see [Button row as a list](#button-row-as-a-list) and [Container element and label](#container-element-and-label)) |
| `crud_views/tags/button/menu_item_label.html` | icon and label of a menu item, included by `menu_item.html`; reads `cv_icon` and `cv_short_label` |

`crud_views/tags/actions_menu_item_label.html` is kept with its 0.30 body (raw keys `cv_icon_action`,
`cv_action_short_label`, `cv_action_label`, `cv_label`), minus the `d-inline-block` on its icon placeholder that
`.cv-icon-fw` already provides, only for 0.30 overrides of `tags/actions_menu_item.html` that include it. The stock
menu item does not use it, so an override of it no longer changes the stock menu; override
`tags/button/menu_item_label.html` instead.

### The leaf contract

`crud_views.lib.view.button_data.cv_button_data(ctx, location, kind="action")` (`kind` is `"action"` or
`"menu-item"`) turns a resolved action into the flat dict the leaves
receive. Every decision (element, disabled, form post or modal, label mode, title) is taken there once. The
keys are `LEAF_KEYS`:

| Key | Meaning |
|---|---|
| `cv_location` | `"context"`, `"list"` or `"card"` |
| `cv_disabled` | the action is rendered disabled (see [Hide or disable inaccessible actions](inaccessible_actions.md)) |
| `cv_disabled_reason` | the text for `data-cv-disabled` when the button is disabled, else `""` |
| `cv_tag` | `"a"` for a link or modal trigger, `"button"` for a POST action or a disabled action |
| `cv_href` | the target URL; present only when `cv_tag` is `"a"` |
| `cv_submit_target` | the id of the form the button submits (`cv_form_<oid>`); present only for an enabled POST action |
| `cv_modal` | the button opens a modal; never true for a disabled button |
| `cv_modal_size` | the semantic modal size (`""`, `"sm"`, `"lg"`, `"xl"`) |
| `cv_active` | the target is the current view; the leaf adds the `<location>:active` classes; never true for a disabled button |
| `cv_key` | the action key, rendered as `cv-key` |
| `cv_label` | the label the leaf prints: on cards the explicit `label`, else the short label, else the key; on `context` and `list` the full label in `icon` mode (hidden text and `title`) and the short label in `label` / `both` (the visible text) |
| `cv_short_label` | the short label, used for menu items |
| `cv_label_mode` | how the label shows: `"label"` (text only), `"icon"` (icon with a hidden label, classes `<location>:hidden-label`) or `"both"` (icon and text); always present. On `"context"` and `"list"` it is the view's resolved [label mode](action_menus.md#label-mode) for the key (`"icon"` unless a map names it); on cards it is the resolved [card action label mode](card-list-view.md#label-mode), and an empty label forces `"icon"` |
| `cv_title` | the `title` text, which also marks the button with `data-cv-tooltip="<cv_location>"` for `tooltip.js`; present only when `cv_label_mode` is `"icon"` |
| `cv_icon` | the icon value (see [Icons](icons.md)) |
| `cv_variant` | the resolved variant; falls back to `"secondary"` |
| `cv_flex` | the leaf adds the `card:flex` classes; true only on cards |
| `cv_icon_class` | the class a [host-placed icon](icons.md#host-placement) adds to the button (the `<location>:icon-host` slot, `menu:icon-host` for a menu item), else `""`; `""` for an action button in `"label"` mode |
| `cv_icon_inline` | render `{% cv_icon cv_icon %}` inside the button; `False` for a host-placed icon. The leaves test `is not False`, so a dict without the key renders the icon as before |

A renderer registered through the icon library config must emit `aria-hidden="true"` on the icon, as `render_icon()` does.
The `"both"` branch of the bundled leaf relies on it: the visible `<span>` must be the button's only accessible name.
A `cv_no_label` key in the context passed to `cv_button_data()` raises `ValueError`; use `cv_label_mode`.

`cv_key` is the key of the view a button targets, not the button's own key: `ContextButton(key="home",
key_target="list")` renders `cv-key="list"`. The filter toggle is the exception — it toggles the filter of the page the
user is already on and has no target view, so it renders its own key, `cv-key="filter"` (a `FilterContextButton`
subclass with another `key` renders that key).

### `cv_button` and `cv_render_button`

`{% cv_button "context" %}` renders the action data in the template context as one button through the leaf
`tags/button/action.html`. `{% cv_button cv_location kind="menu-item" %}` renders a dropdown item through
`tags/button/menu_item.html`. A hidden (inaccessible) action renders nothing. The logic templates are exactly these
calls.

`{% cv_render_button ctx location %}` renders already resolved action data the way the logic templates do (a context
button with its own `template` or `template_code` keeps rendering that); it renders nothing for empty data. The
container leaf uses it in its loop.

## Forms

The crispy form buttons take their classes from the table. `crud_views.lib.crispy` provides `Submit`, `Button` and
`Reset`, drop-in subclasses of the crispy layout objects:

| Class | Default `slot` |
|---|---|
| `Submit` | `form:submit` |
| `Button` | `form:cancel` |
| `Reset` | `form:filter-reset` |

The `slot` keyword picks another key, `Submit(name="delete", value="Delete", slot="form:delete")`; a `css_class` you
pass is appended to the table classes.

`CrispyFormMixin` builds its buttons through hooks you can override: `get_submit_button_kwargs()` /
`get_submit_button()` and `get_cancel_button_kwargs()` / `get_cancel_button()`. `CrispyDeleteForm` adds
`get_delete_button_kwargs()` / `get_delete_button()` (slot `form:delete`); see [Delete view](delete_view.md).

The removed tags `cv_submit_button`, `cv_cancel_button` and `cv_delete_button` and their templates are replaced by
these classes.

## Formsets

The row controls of [formsets](formsets.md) use `formset:control`, `formset:control-danger` and `formset:container`.
`formsets/control.html` writes the two delete-toggle classes into data attributes of the delete button:

- `data-cv-class` - the classes of the normal state (`formset:control`),
- `data-cv-class-danger` - the classes of the row marked for deletion (`formset:control-danger`).

`formset.js` reads them in `set_delete` and swaps the classes; it contains no class literals. A project override of
`formsets/control.html` that omits the attributes no longer recolours the delete toggle.

## A theme recipe

Register the classes; override a leaf only where the markup itself differs. Classes that differ by label mode need
no override at all — register `card:tertiary:icon` and the like instead. Which toolbar and row buttons show text is not
a theme decision either: the project names them in a [label mode map](action_menus.md#label-mode). This example
restyles the buttons for a framework that wants `button is-*` classes, with a square variant for the icon-only
toolbar buttons and the label shown on the primary action:

```python
# settings.py
CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE = {"create": "both"}
```

```python
# myapp_theme/apps.py
def ready(self):
    from crud_views.lib.button_classes import register_button_classes

    register_button_classes(
        {
            "context:primary": "button is-primary",
            "context:primary:icon": "button is-primary is-square",
            "context:secondary": "button is-link is-light is-square",
            "context:tertiary": "button is-text is-square",
            "context:danger": "button is-danger is-square",
            "context:active": "is-active",
            "context:hidden-label": "is-sr-only",
        }
    )
```

Nothing is overridden: the active state and the hidden label come from the two extra keys. Showing a label is not a
reason to override either: a card shows icon and text with `CardListView.cv_card_actions_label_mode = "both"` (the
default), a toolbar or row button with its key in the label mode map.

When you do override the leaf, for markup that differs, remember it is shared by the context toolbar, list rows and
cards: branch on `cv_label_mode` (`"icon"`, `"both"` and `"label"`; the bundled leaf treats `"label"` as the fallback
branch and shows the icon in `"both"` only when `cv_icon` is set), and keep `cv_active` and `cv_flex` through their
table keys and `cv_title`, as the bundled `crud_views/tags/button/action.html` does. `cv_title` is present only in
`"icon"` mode; the visible label is the accessible name otherwise. Keep the
`data-cv-*` attributes and `cv-key`: the bundled scripts use them; `data-cv-tooltip="{{ cv_location }}"` next to
`title` is what gives the button a tooltip through `cv.adapters.tooltip`, see [JavaScript](javascript.md#tooltips). Keep the `cv_disabled` handling when you
override the leaf, otherwise an action disabled by `CRUD_VIEWS_INACCESSIBLE_ACTIONS = "disable"` looks enabled.

## System checks

| ID | Level | Meaning |
|---|---|---|
| `crud_views.E360` | error | a removed setting is still defined (`CRUD_VIEWS_FILTER_RESET_BUTTON_CSS_CLASS`); the hint names the replacement |
| `crud_views.E361` | error | a `CRUD_VIEWS_BUTTON_CLASSES` value or registered theme value is neither a str nor `None` |
| `crud_views.E363` | error | an `*:icon-host` value is not a valid format string with `{name_class}` as its only placeholder |
| `crud_views.E364` | error | a `*:container-single` value is neither `"container"` nor `"bare"` (`None` and `""` mean `"container"`) |
| `crud_views.W362` | warning | a `CRUD_VIEWS_BUTTON_CLASSES` or theme key is neither in the default table nor a valid `location:variant:mode` (typo, or an unknown label mode) |
| `viewset.E209` | error | a `cv_action_variant`, `ContextButton.variant` or `CardAction.variant` is not one of the four variants |
| `viewset.E210` | error | a `CardAction.label_mode` or `cv_card_actions_label_mode` is not one of `"label"`, `"icon"`, `"both"` |
| `viewset.E211` | error | a `cv_context_actions_label_mode` or `cv_list_actions_label_mode` is not `None` or a dict of action key → label mode |
| `viewset.W291` | warning | a view's own `cv_*_actions_label_mode` names a key that is not among that location's actions |
