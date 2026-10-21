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

The default table has 34 keys: the rows with four variants stand for four keys each. The `context` and `list`
buttons look the same for every variant by default, the `card` buttons distinguish them.

The table holds what a theme restyles: classes. What the markup needs to work stays in the templates and is not
configurable here: the element, `href`, `type`, `disabled`, the `data-cv-*` attributes, `aria-*`, `cv-key`, the
`active` and `flex-grow-1` modifiers, `dropdown-toggle`, `data-bs-toggle` and the like.

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
`crud_views.E361`. A key that is not in the table above is reported by `crud_views.W362` (a typo, most likely).

Project entries always win. `CRUD_VIEWS_FILTER_RESET_BUTTON_CSS_CLASS` was replaced by
`CRUD_VIEWS_BUTTON_CLASSES["form:filter-reset"]`; while the old setting is defined the system check
`crud_views.E360` fails.

`get_button_classes()` returns the resolved, cached dict; do not mutate it. `get_button_class(location, slot)` returns
one resolved string (`""` for `None`, an unknown key or a non-string value).

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

`{% cv_button_class location slot %}` renders the resolved classes of one key (autoescaped). It is available in
`{% load crud_views %}` and in `{% load crud_views_object_detail %}`:

```html+django
{% load crud_views %}
<button type="button" class="{% cv_button_class 'card' 'primary' %}">...</button>
<a href="{{ url }}" class="{% cv_button_class cv_location cv_variant %}">...</a>
```

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
| `crud_views/tags/button/container.html` | the group of buttons plus the menu; receives `cv_buttons`, `cv_group`, `cv_location` and `cv_container_tag` |
| `crud_views/tags/button/menu_item_label.html` | icon and label of a menu item, included by `menu_item.html`; reads `cv_icon` and `cv_short_label` |

`crud_views/tags/actions_menu_item_label.html` is kept with its 0.30 body (raw keys `cv_icon_action`,
`cv_action_short_label`, `cv_action_label`, `cv_label`) only for 0.30 overrides of `tags/actions_menu_item.html` that
include it. The stock menu item does not use it, so an override of it no longer changes the stock menu; override
`tags/button/menu_item_label.html` instead.

### The leaf contract

`crud_views.lib.view.button_data.cv_button_data(ctx, location)` turns a resolved action into the flat dict the leaves
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
| `cv_active` | the target is the current view; never true for a disabled button |
| `cv_key` | the action key, rendered as `cv-key` |
| `cv_label` | the full label (on cards the explicit `label`, else the short label, else the key) |
| `cv_short_label` | the short label, used for menu items |
| `cv_label_mode` | how the label shows: `"label"` (text only), `"icon"` (icon with a visually hidden label) or `"both"` (icon and text); always present. Always `"icon"` for `"context"` and `"list"`; on cards it comes from [`CardAction.label_mode`](card-list-view.md#label-mode), and an empty label forces `"icon"` |
| `cv_title` | the `title` text, which also marks the button with `data-cv-tooltip="<cv_location>"` for `tooltip.js`; present only when `cv_label_mode` is `"icon"` |
| `cv_icon` | the icon value (see [Icons](icons.md)) |
| `cv_variant` | the resolved variant; falls back to `"secondary"` |
| `cv_flex` | add `flex-grow-1`; true only on cards |

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

Register the classes, then override one leaf where the markup differs. This example restyles the buttons for a
framework that wants `button is-*` classes and shows the label of `primary` buttons next to the icon:

```python
# myapp_theme/apps.py
def ready(self):
    from crud_views.lib.button_classes import register_button_classes

    register_button_classes(
        {
            "context:primary": "button is-primary",
            "context:secondary": "button is-link is-light",
            "context:tertiary": "button is-text",
            "context:danger": "button is-danger",
        }
    )
```

```html+django
{# myapp_theme/templates/crud_views/tags/button/action.html #}
{% load crud_views %}<{{ cv_tag }}{% if cv_tag == "a" %} href="{{ cv_href }}"{% else %} type="button"{% endif %}
    class="{% cv_button_class cv_location cv_variant %}{% if cv_active %} is-active{% endif %}{% if cv_flex %} flex-grow-1{% endif %}"
    {% if cv_disabled %}disabled data-cv-disabled="{{ cv_disabled_reason }}"{% endif %}
    {% if cv_submit_target %}data-cv-action="submit-form" data-cv-target="{{ cv_submit_target }}"{% endif %}
    {% if cv_modal %}data-cv-modal="true" data-cv-modal-size="{{ cv_modal_size }}"{% endif %}
    {% if cv_active %}aria-current="page"{% endif %}
    {% if cv_title %}title="{{ cv_title }}" data-cv-tooltip="{{ cv_location }}"{% endif %}
    cv-key="{{ cv_key }}">{% if cv_label_mode == "icon" %}{% cv_icon cv_icon %}<span{% if cv_variant != "primary" %} class="visually-hidden"{% endif %}>{{ cv_label }}</span>{% else %}<span>{{ cv_label }}</span>{% endif %}</{{ cv_tag }}>
```

The `primary` guard works because every non-card location resolves `cv_label_mode` to `"icon"`, so the `"icon"` branch
is the one the toolbar and list rows take. The card half of this trick is no longer a reason to override the leaf: a
card shows icon and text with `CardListView.cv_card_action_label_mode = "both"` (the default). The toolbar half stops
being one when #216 lands.

The leaf is shared by the context toolbar, list rows and cards: branch on `cv_label_mode` (`"icon"`, `"both"` and
`"label"`; the bundled leaf treats `"label"` as the fallback branch and shows the icon in `"both"` only when `cv_icon`
is set), and keep `cv_flex` and `cv_title`, as the bundled `crud_views/tags/button/action.html` does. `cv_title` is
present only in `"icon"` mode; the visible label is the accessible name otherwise. Keep the
`data-cv-*` attributes and `cv-key`: the bundled scripts use them; `data-cv-tooltip="{{ cv_location }}"` next to
`title` is what gives the button a tooltip through `cv.adapters.tooltip`, see [JavaScript](javascript.md#tooltips). Keep the `cv_disabled` handling when you
override the leaf, otherwise an action disabled by `CRUD_VIEWS_INACCESSIBLE_ACTIONS = "disable"` looks enabled.

## System checks

| ID | Level | Meaning |
|---|---|---|
| `crud_views.E360` | error | a removed setting is still defined (`CRUD_VIEWS_FILTER_RESET_BUTTON_CSS_CLASS`); the hint names the replacement |
| `crud_views.E361` | error | a `CRUD_VIEWS_BUTTON_CLASSES` value or registered theme value is neither a str nor `None` |
| `crud_views.W362` | warning | a `CRUD_VIEWS_BUTTON_CLASSES` or theme key is not in the default table (typo?) |
| `viewset.E209` | error | a `cv_action_variant`, `ContextButton.variant` or `CardAction.variant` is not one of the four variants |
