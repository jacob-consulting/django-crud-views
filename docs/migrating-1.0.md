# Migrating to 1.0.0

1.0.0 collects the breaking changes and theme-compatibility work of 0.30.0 and of the releases since. This page is
the route from **0.29.x** to 1.0.0. The [CHANGELOG](https://github.com/jacob-consulting/django-crud-views/blob/main/CHANGELOG.md)
stays the complete record, ordered by release and issue; this page orders the same changes by what you have to
touch.

## Who this is for

- **An app on the stock bootstrap5 theme.** You override no crud_views template, but you have a base template,
  settings, views, maybe a Python override or some JavaScript, and CSS or tests that select on the markup. Read
  [Step zero](#step-zero-run-the-checks), [An app on the stock bootstrap5 theme](#an-app-on-the-stock-bootstrap5-theme)
  and [Silent breaks](#silent-breaks).
- **A downstream theme**, such as `crud_views_tabler`, that ships its own copies of crud_views templates. Read all of
  it: a theme is also an app.

Each step says what changed between 0.29.x and 1.0.0, not the route through 0.30.0. Steps marked **[0.30]** came
with the icon registry in 0.30.0: if you are already on 0.30.0, skip them.

## Step zero: run the checks

Upgrade, then run

```shell
python manage.py check
```

and fix everything it reports. Most removed settings and renamed values fail a system check with the replacement in
the message:

| Code | Raised when | Do this |
|---|---|---|
| `crud_views.E350` **[0.30]** | a removed icon setting is still defined: `CRUD_VIEWS_ACTIONS_MENU_ICON`, `CRUD_VIEWS_FILTER_ICON`, `CRUD_VIEWS_OBJECT_DETAIL_ICONS_LIBRARY`, `_ICONS_CLASS`, `_ICONS_TYPE`, `_ICONS_PREFIX`, `CRUD_VIEWS_OBJECT_DETAIL_NAMED_ICONS` | move the value into `CRUD_VIEWS_ICONS`, see [Settings](#settings) |
| `crud_views.E360` | `CRUD_VIEWS_FILTER_RESET_BUTTON_CSS_CLASS` is still defined | `CRUD_VIEWS_BUTTON_CLASSES = {"form:filter-reset": "..."}` |
| `viewset.E250` | `cv_modal_size` is a Bootstrap class such as `"modal-lg"` | use the token: `""`, `"sm"`, `"lg"` or `"xl"` |
| `viewset.W246` **[0.30]** | an object detail group `icon` uses a `prefix:` that is not registered | register the library in `CRUD_VIEWS_ICON_LIBRARIES`, or fix the prefix |

Two removals raise at runtime instead, the first time the page renders:

- `TypeError` from a `cv_get_context()` override with the old signature: see
  [Views and Python code](#views-and-python-code).
- `ValueError: cv_no_label is no longer a leaf input`: see [Views and Python code](#views-and-python-code).

The new features bring their own checks. They only fire on a misconfigured new setting or attribute, so an upgraded
project that uses none of them never sees them: `crud_views.E351`, `E354`, `E355`, `E356`, `W352`, `W353`
([icon libraries](reference/icons.md)), `crud_views.E361`, `W362` ([button classes](reference/buttons.md)),
`viewset.E209` ([variants](reference/buttons.md)), `viewset.E210` ([card label mode](reference/card-list-view.md)),
`crud_views.E106`, `viewset.E211`, `W291` ([toolbar and row label modes](reference/action_menus.md)),
`crud_views.E108` ([label-mode defaults](reference/settings.md#label-mode-configuration)). The form label-mode maps
reuse `crud_views.E106`, `viewset.E210`, `E211`, `W291` and `W292` ([Form checks](reference/action_menus.md#form-checks)).

`crud_views.E108` reports a `CRUD_VIEWS_LABEL_MODE_DEFAULTS` that is not a dict, a key that is not a button location
(`"context"`, `"list"`, `"card"`, `"form"`) and a mode that is not exactly `"label"`, `"icon"` or `"both"`. At render an
unknown key is ignored. An invalid mode raises `ValueError` in strict mode (`CRUD_VIEWS_STRICT`, which defaults to
`DEBUG`); otherwise it logs one warning and the location falls back to its package floor.

A clean `check` is not the end: some changes render differently and raise nothing. They are collected under
[Silent breaks](#silent-breaks).

## An app on the stock bootstrap5 theme

Your base template, settings, views, JavaScript, and the CSS and tests that select on markup.

### Base template and your own templates

- **If your base template uses `django_bootstrap5`:** crud_views no longer depends on `django-bootstrap5`, so it is
  no longer installed for you. Replace `{% bootstrap_messages %}` with `{% cv_messages %}` from the `crud_views` tag
  library; it renders the same `django.contrib.messages` queue as Bootstrap 5 alerts
  ([Flash messages](reference/messages.md), #221). If you keep other tags such as `{% bootstrap_css %}` or
  `{% bootstrap_javascript %}`, add `django-bootstrap5` to your own dependencies and keep `django_bootstrap5` in
  `INSTALLED_APPS`. Without either, `{% load django_bootstrap5 %}` raises `TemplateSyntaxError`.
- **If you list crud_views' static files by hand** instead of rendering `{% cv_css %}` / `{% cv_js %}` or using
  `cv_sources()`: add `crud_views/css/icons.css` **[0.30]** (it provides `.cv-icon-fw` for the menu icons) and put
  `crud_views/js/adapters.js` before every other crud_views script ([JavaScript](reference/javascript.md#what-the-scripts-need)).
- **If your templates use `{% cv_submit_button %}`, `{% cv_cancel_button %}` or `{% cv_delete_button %}`:** the tags
  and their templates are gone. The crispy forms build their buttons with `Submit`, `Button` and `Reset` from
  `crud_views.lib.crispy` ([Forms](reference/buttons.md#forms)).
- **If your templates use `{% cv_filter_icon %}`, `{% cv_header_icon_class %}` or `{% cv_filter_icon_class %}`,
  or `{% include "crud_views/tags/icon.html" %}` [0.30]:** render the icon with `{% cv_icon "filter" %}`, or
  `{% cv_icon value css="me-2" %}` for any icon value ([Icons](reference/icons.md)).
- **If your templates use the `cv_is_true`, `cv_is_false` or `cv_is_list` filters:** they are removed together with
  the unused `crud_views/detail/` templates (#217).

### Settings

**Icon settings [0.30]** (`crud_views.E350`). The icons now come from one table, `CRUD_VIEWS_ICONS`
([Icons](reference/icons.md#crud_views_icons)). Before, in 0.29:

```python
CRUD_VIEWS_ACTIONS_MENU_ICON = "fa-solid fa-bars"
CRUD_VIEWS_FILTER_ICON = "fa-solid fa-magnifying-glass"
```

After, in 1.0:

```python
CRUD_VIEWS_ICONS = {"actions-menu": "fas:bars", "filter": "fas:magnifying-glass"}
```

The `CRUD_VIEWS_OBJECT_DETAIL_ICONS_*` settings and `CRUD_VIEWS_OBJECT_DETAIL_NAMED_ICONS` are gone too. Object
detail now uses Font Awesome like the rest of the package. To keep Bootstrap Icons there:

```python
from crud_views.lib.icons import BOOTSTRAP_ICONS

CRUD_VIEWS_ICONS = {k: BOOTSTRAP_ICONS[k] for k in ("boolean-true", "boolean-false", "property-detail", "text-icon")}
```

`CRUD_VIEWS_ICONS = BOOTSTRAP_ICONS` switches every icon of the package to Bootstrap Icons
([Bootstrap Icons preset](reference/icons.md#bootstrap-icons-preset)).

**`CRUD_VIEWS_FILTER_RESET_BUTTON_CSS_CLASS`** (`crud_views.E360`) moves into the button class table:
  `CRUD_VIEWS_BUTTON_CLASSES = {"form:filter-reset": "btn btn-secondary"}` ([Buttons](reference/buttons.md#crud_views_button_classes)).

### Views and Python code

**If you override `cv_get_context()`:** it takes a keyword-only `location`, and every button path passes it. An
override with the old signature raises `TypeError` on the first toolbar. Accept it and pass it on (#216):

```python
def cv_get_context(self, key=None, obj=None, user=None, request=None, *, location=None):
    context = super().cv_get_context(key, obj, user, request, location=location)
    ...
    return context
```

The other changes to views:

- **`cv_modal_size`** (`viewset.E250`) takes the tokens `""`, `"sm"`, `"lg"` and `"xl"`: `cv_modal_size = "modal-lg"`
  becomes `cv_modal_size = "lg"` ([Modals](reference/modals.md)).
- **If anything puts `cv_no_label` into a button's context** (a `cv_get_context()` override, a dict passed to
  `{% cv_render_button %}`, or a `cv_no_label` variable in the page's template context): it raises `ValueError`.
  Use `cv_label_mode` (`"label"`, `"icon"` or `"both"`) instead. `CardAction(no_label=True)` keeps working.
- **Card buttons show their icon next to their label** (#213). To get the 0.29 label-only buttons back on every card
  view of the project, set `CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"card": "label"}` in your settings. For one view, set
  `cv_card_actions_label_mode = "label"` on the card view; for one button, `CardAction(label_mode="label")`
  ([Label mode](reference/card-list-view.md#label-mode)). An unknown value fails `viewset.E210`, an unknown setting
  entry `crud_views.E108`.
- **Card label-mode attribute:** `CardListView.cv_card_actions_label_mode` now reads `None` by default instead of
  the resolved string `"both"`; `None` means the `"card"` entry of `CRUD_VIEWS_LABEL_MODE_DEFAULTS`
  ([setting](reference/settings.md#label-mode-configuration),
  [resolution](reference/action_menus.md#card-label-mode-resolution)). Without
  configuration cards still resolve to `"both"` and render as before, but this is a Python-level change: a subclass,
  override or template that reads the raw attribute as a mode now gets `None`.
  `cv_get_card_actions_label_mode()` resolves class-level defaults and stays callable on the class; calling it
  through an instance still reads class configuration. Read the effective per-action `cv_label_mode` stamped on
  the button context or returned by `cv_get_card_action_data()`. A view that assigns the attribute on a class or
  instance keeps its choice, including `as_view()` and per-request assignment. `CardAction(no_label=True)` still
  renders icon-only.
- **`CardAction.variant` defaults to the target view's variant.** A card action pointing at a create view without an
  explicit `variant` now renders `btn-primary`; set `variant="secondary"` to keep the 0.29 look
  ([Variants](reference/buttons.md#variants)).
- **Object detail group icons [0.30] are no longer prefixed for you.** `icon="truck"` must become
  `icon="fas:truck"` (or `"bi:truck"`), or `"truck"` must be added to `CRUD_VIEWS_ICONS`. Nothing flags a bare name:
  it is read as a raw CSS class and renders an invisible `<i class="truck">`
  ([Groups](reference/object_detail_configuration.md#groups)).
- **If you override `cv_get_filter_icon()` on a list or card view [0.30]:** nothing calls it any more, and nothing
  says so. The filter toggle and the filter panel header both use the `filter` icon; set
  `CRUD_VIEWS_ICONS["filter"]` instead.
- `cv_icon_action` and `cv_icon_header` on your views need no change: a raw CSS class such as
  `"fa-solid fa-truck"` still renders as before. Semantic names (`"detail"`) and `prefix:name` values
  (`"fas:truck"`) work too ([Icon values](reference/icons.md#icon-values)).

### JavaScript

- **`cv.cvModalOpen(url, size)` and hand-written `data-cv-modal-size`** take the same tokens as `cv_modal_size`:
  `cv.cvModalOpen(url, "lg")`, `data-cv-modal-size="lg"`. No check can see these; an old `"modal-lg"` silently opens
  the default size.
- **jQuery** is only needed on pages with formsets and by jQuery-based extensions
  ([jQuery](reference/javascript.md#jquery)). The core scripts use the DOM API and talk to Bootstrap through
  `cv.adapters` ([`cv.adapters`](reference/javascript.md#cvadapters)).
- **Tooltips.** Icon-only buttons, the filter toggle, the card-order toggles and the formset controls carry
  `data-cv-tooltip`. With Bootstrap's JavaScript loaded they now show Bootstrap tooltips instead of the browser's
  `title` tooltip (#202). To keep the browser tooltip: `cv.adapters.tooltip = {init() {}}`
  ([Tooltips](reference/javascript.md#tooltips)).
- **Dismissible alerts** close through `cv.adapters.alert`, called by `viewset.js` after `adapters.js`; with
  `{% cv_js %}` there is nothing to do. A script of yours that replaces the whole `cv.adapters` map after core loads
  must provide `alert` as well ([Hooks instead of copies](#hooks-instead-of-copies)), and a copied alert frame
  needs the new close hook ([Contract changes](#contract-changes-in-templates-you-still-override)).

### CSS and tests that select on markup

None of these raise anything. Check your stylesheets, your JavaScript selectors and any test that asserts on HTML:

- **Table sort icons [0.30]** are Font Awesome 6 (`table-sort-asc` = `fas:angles-up`, `table-sort-desc` =
  `fas:angles-down`), and ascending now points up.
- **Icons [0.30]** render with `aria-hidden="true"`; the menu icons use `cv-icon-fw` instead of `fa-fw`.
- **Card list pagination** (#241): the arrows are the `page-previous` / `page-next` icons followed or preceded by a
  visually hidden "previous" / "next", not `&laquo;` / `&raquo;`. A disabled end is
  `<a class="page-link" aria-disabled="true">` without `href`, not a `<span>`. The current page carries
  `aria-current="page"`.
- **Table pagination**: the stock django-tables2 template uses the same markup. The visible "previous" / "next"
  text with `&laquo;` / `&raquo;` becomes the icons with hidden labels. The current page is a
  `<span class="page-link">` in `li.active[aria-current="page"]` instead of a link. The missing direction is now
  rendered as a disabled `li` instead of being left out, and the `<nav>`'s label is the translated "pagination"
  instead of "Table navigation" ([Table pagination overrides](#table-pagination-overrides)).
- **`hidden` instead of `d-none`** (#232): the filter toggle's icon spans and the hidden POST forms behind list and
  card actions use the `hidden` attribute. The filter toggle carries `aria-expanded`, `aria-controls="filter-collapse"`
  and `cv-key="filter"`.
- **Buttons:** one attribute order for every button; card buttons carry `cv-key`; card POST actions render
  `<button type="button">`; the active toolbar action carries `aria-current="page"`; a list or card button whose
  target is the current view renders `active`; the card row carries `cv-card-container`; card menu forms render
  before the row.
- **Form buttons:** the crispy form buttons are `<button>` elements instead of `<input>`
  ([Form buttons](#form-buttons)). The cancel button renders `btn btn-secondary` (was `btn btn btn-secondary`), the
  filter reset `btn btn-secondary` (was `btn btn-inverse btn btn-secondary`), and the Delete label is translated.
- **Tooltip markup** (#202): the formset controls' `title` is the translated text of their `aria-label` ("Move up",
  "Move down", "Add row", "Delete row"), no longer `up` / `down` / `add` / `delete`. The object-detail
  property-detail button uses `title` instead of `data-bs-title`.
- **Alerts** (#250): the delete page's protection and related-objects alerts and the guardian manage page's config
  alert gain `role="alert"` and an icon before the heading.
- **Alert close control:** the dismissible alert's close button carries `data-cv-alert-dismiss` instead of
  `data-bs-dismiss="alert"` ([Contract changes](#contract-changes-in-templates-you-still-override)).
- **Empty button containers** (#265): a toolbar, list row or card whose actions are all hidden for the user renders
  no container at all, so `[cv-list-container]` (or `cv-context-container`, `cv-card-container`) is not in every row
  any more. Selectors that expect it must handle its absence.
- **Container label** (#266): the toolbar and list row `aria-label` is translated ("Aktionen" on a German page).

## Form buttons

The `Submit`, `Button` and `Reset` of `crud_views.lib.crispy` render through the form-button leaf
`crud_views/tags/button/form.html` when they sit in a crispy layout ([Forms](reference/buttons.md#forms)). Every
package form does that: create, update, custom form, delete, workflow and the list filter. Nothing raises for the
changes below unless noted.

### Markup and submitted data

- Each button is a `<button>` instead of an `<input>`, with its text in a `<span>`:

    ```html
    <!-- before -->
    <input type="submit" name="submit" value="Create" class="btn btn-primary" id="submit-id-submit"/>
    <!-- after -->
    <button type="submit" name="submit" value="Create" id="submit-id-submit" class="btn btn-primary"><span>Create</span></button>
    ```

    The names, values, ids, classes and the cancel button's `data-cv-cancel-url` stay as they were, and so do the
    filter's `filter-button` and `filter-button-reset` ids. Selectors and tests that match `input[type="submit"]`,
    `input[name="reset"]`, `input#filter-button` or the attribute order must match `button` instead.
    Extra attributes passed to a button (`Submit("submit", "Go", data_b="1", data_a="2")`) render after `type`,
    `name`, `value`, `id` and `class` (and the cancel URL and icon-only title, when present) in sorted order, as
    Django's `flatatt` emits them, with boolean attributes last; crispy kept the keyword order. The example renders
    `data-a` before `data-b`.
- A click posts the clicked button's `name=value`, as the input did, and in the modal `modal.js` sends the same
  submitter. The delete view still needs only its confirmation field: a click posts `confirm` and `delete=Delete`,
  and a test that posts `{"confirm": True}` alone keeps working.
- A name of several words is still submitted slugified, as crispy did (`"Search the Site"` becomes
  `search-the-site`); a one-word name is submitted as written. The generated ids keep crispy's `<type>-id-<name>`.
- The filter's Apply and Reset now render in their own `FormActions` group (`<div class="mb-3">`) after the fields.
  The template pack's inputs wrapper follows it with only the hidden `sort`, order and direction inputs, with
  unchanged names and values and its own `mb-3` margin. No global crispy template override is needed or shipped.

### Values are literal text

Crispy rendered the value of a layout button as a Django template. The leaf does not: values, labels, names, ids and
attribute values are escaped once and shown as written. `Submit("submit", "{{ request.user }}")` used to show the
user's name and now shows `{{ request.user }}`. Compute such a label in Python instead, for example in
`get_submit_button_kwargs()`, where the form's view and its request are at hand (`self.cv_view.request`).

Each reserved attribute is set once ([Literal text](reference/buttons.md#literal-text)): an extra `type`, `name` or
`value` keyword is dropped, `css_id` wins over an extra `id`, and an extra `class` is appended after the table
classes and `css_class`. In `"icon"` mode the generated `title` and `data-cv-tooltip="form"` win over yours.

### Custom button templates

A `template=` argument and a `template` attribute on your subclass keep working, `%s` pack names included, in this
order: `template=`, the subclass attribute, the bundled leaf. The template now receives the form leaf contract
instead of crispy's `input` object, and nothing of the surrounding page:

| Before | After |
|---|---|
| `{{ input.value }}` | `{{ cv_value }}` (submitted), `{{ cv_label }}` (shown) |
| `{{ input.name }}` | `{{ cv_name }}` |
| `{{ input.id }}` | `{{ cv_id }}` |
| `{{ input.input_type }}` | `{{ cv_type }}` |
| `{{ input.field_classes }}` | `{% cv_button_class "form" cv_key cv_label_mode %}` and `{{ cv_css_class }}` |
| `{{ input.flat_attrs }}` | `{{ cv_flat_attrs }}` |

A template that still reads `input.*` renders empty attributes and raises nothing. The full recipe is
[Custom form-button templates](reference/theme.md#custom-form-button-templates). A theme that restyled the package
buttons by overriding crispy's `layout/baseinput.html` no longer reaches them: register `form:*` classes or override
`crud_views/tags/button/form.html`.

### Slots

A button in a layout needs `slot="form:<kind>"` with one of the five form kinds `submit`, `cancel`, `delete`,
`filter-submit` and `filter-reset`; any other slot (`"formset:control"`, `"form:primary"`) raises `ValueError` when
the button renders. Pick the kind that matches what the button does and restyle it with `css_class`, or for every
button of that kind with a `form:<kind>` or `form:<kind>:<mode>` key in `CRUD_VIEWS_BUTTON_CLASSES`. There are no
other kinds or variants. Buttons added with `helper.add_input()` are not checked.

### Filter helpers

A `ListViewFilterFormHelper` subclass that declares only its fields keeps working: Apply and Reset are appended once
after them ([Custom filter helpers](reference/list_view.md#custom-filter-helpers)).

- **If you cleared `helper.inputs = []` (or `self.inputs = []`) to hide Apply and Reset:** that no longer hides them,
  it only drops the hidden sort, order and direction inputs. Nothing warns. Override `get_form_actions()` to return
  `None` and leave the inputs alone, see
  [Removing the filter buttons](reference/list_view.md#removing-the-filter-buttons).
- **If you added your own buttons with `add_input(Submit(...))`:** they keep rendering as crispy inputs with their old
  markup, in the inputs wrapper after the visible actions, without label mode or icon and without a warning. To give
  them the new leaf, return them from `get_form_actions()` in a `FormActions`; keep hidden inputs as inputs.

### Label modes and icons

Form buttons show their text by default: the `"form"` floor of `CRUD_VIEWS_LABEL_MODE_DEFAULTS` is `"label"`, so
nothing gains an icon until a project asks for one with the floor or a form map
([Form label-mode resolution](reference/action_menus.md#form-label-mode-resolution)). In `"icon"` mode a button
without a usable icon raises `ValueError` under `CRUD_VIEWS_STRICT` and otherwise logs a warning and keeps its label;
see [Form buttons](reference/icons.md#form-buttons) for the icons and their order.

## A downstream theme

Templates to delete or move, the hooks that replace copied templates, and contract changes in templates you still override.

Most of 1.0's theme work replaces copied templates with registered values and small leaves: the
[button class table](reference/buttons.md#the-class-table), the [icon registry](reference/icons.md#registering-icons-from-a-theme),
the [form frame](reference/theme.md#framing-the-form-pages), the [alert frame](reference/theme.md#alerts) and the
[card blocks](reference/card-list-view.md#custom-card-template). Upgrading a theme is mostly deleting copies.
`crud_views_tabler` ships its own update for 1.0.

### Templates to delete

Go through your theme's `templates/crud_views/` directory. Delete each of these copies:

- **`tags/messages.html`** (#250). It is a loop over `tags/alert.html` now, and the dicts it receives have `level`
  and `text` instead of `css_class` and `message`. A copy that reads the old keys renders `class="alert alert-"` with
  an empty body. Override `tags/alert.html` (box, icon, heading, close button), `snippets/alert/text.html` or
  `snippets/alert/list.html`, and register the colours as `alert:error`, `alert:warning`, `alert:success`,
  `alert:info` and `alert:debug` ([Alerts](reference/theme.md#alerts)). A `tags/alert.html` override uses the new close
  hook ([Contract changes](#contract-changes-in-templates-you-still-override)). Python code that imports
  `ALERT_CLASSES` or `ICON_NAMES` from `crud_views.lib.messages` uses `LEVELS` and the `message-<level>` icon names
  instead.
- **`tags/button_submit.html`, `tags/button_cancel.html`, `tags/button_delete.html`.** Nothing renders them any more;
  the form buttons come from crispy's `Submit`, `Button` and `Reset` and take their classes from the `form:*` keys
  ([Forms](reference/buttons.md#forms)).
- **`tags/icon.html` [0.30]** and **`crud_views/detail/`** (#217). Nothing renders them.
- **`view_create.content.html`, `view_update.content.html`, `view_custom_form.content.html`,
  `view_delete.content.html`**, if you copied them to wrap the form in a card or similar (#239). They extend
  `snippets/form_frame.html` now: override its `cv_form_frame` block instead
  ([Framing the form pages](reference/theme.md#framing-the-form-pages)). A 0.29 copy also misses two fixes: its
  `<form>` has no `enctype="multipart/form-data"`, so file fields upload nothing on create and custom-form pages
  (#236), and the create copy renders `{{ form.media }}` twice (#191). The delete page's protection alert moved to
  `snippets/delete/protection_errors.html`.
- **Copies made only to change a heading level** (#251): `tags/card.html`, `modal/content.html`,
  `crud_views_workflow/view_workflow.action.html` and `view_workflow.history.html`, and the object-detail
  `crud_views_object_detail/layouts/*/group.html`. Set `CRUD_VIEWS_HEADER_LEVEL` to the level of your
  `{% cv_header %}` instead. These headings then render one level below it and keep their look
  ([Heading levels](reference/templates.md#heading-levels)).
- **Copies of `tags/button/action.html`, `tags/button/menu_item.html`, `tags/actions_menu_toggle.html` or
  `tags/context_action_filter.html` made only to put the icon class on the button itself** (an icon library that
  paints `::before` on the button, #258). Register the library with `placement: "host"` instead; the stock leaves
  then add the icon's class to the button, and the `*:icon-host` button classes add a base class where a kind of
  button needs one ([Host placement](reference/icons.md#host-placement)).
- **`snippets/pagination.html`**, if you overrode it only for the arrows (#241). Register the `page-previous` and
  `page-next` icons instead. If you keep it for other markup, take over the accessible markup described under
  [CSS and tests](#css-and-tests-that-select-on-markup).

### Templates to move

The 0.29 templates that rendered one button are **logic templates** now: one line that calls a tag. Old copies still
render, but they bypass the leaf contract, so new options (label modes, variants, disabled actions) don't reach
them. Move the markup into the leaves and delete the copies
([Logic templates and leaves](reference/buttons.md#logic-templates-and-leaves)).

The leaves receive the flat [leaf contract](reference/buttons.md#the-leaf-contract), not the keys your 0.29 copy
reads. Markup moved over unchanged renders `href=""` and no icon, and raises nothing. Rename as you move:

| 0.29 key | Leaf key |
|---|---|
| `cv_url` | `cv_href` (present only when `cv_tag` is `"a"`) |
| `cv_icon_action` | `cv_icon`, rendered with `{% cv_icon cv_icon %}` |
| `cv_action_label`, `cv_label` | `cv_label` |
| `cv_action_short_label` | `cv_short_label` |
| `cv_is_active` | `cv_active` |
| `cv_form_{{ cv_oid }}`, `cv_list_action_method` | `cv_submit_target` (present only for a POST action) |
| `cv_access`, `cv_action_enabled` | gone: an action the user may not see never reaches the leaf; `cv_disabled` and `cv_disabled_reason` mark a disabled one |
| `cv_no_label` | `cv_label_mode` |

Which template takes the markup:

| 0.29 copy | Move the markup to |
|---|---|
| `tags/context_action.html`, `tags/list_action.html`, `tags/card_action.html` | `tags/button/action.html`, one leaf for all three locations (`cv_location`) |
| `tags/actions_menu_item.html` | `tags/button/menu_item.html` |
| `tags/actions_menu_item_label.html` | `tags/button/menu_item_label.html`; the stock menu no longer includes the old one |
| `tags/context_actions.html`, `columns/actions.html` | `tags/button/container.html` (receives `cv_buttons`, `cv_group`, `cv_location`; the element is the `<location>:container-tag` key) |

- **`tags/card_action.html` copies that branch on `cv_no_label`** break silently. The card action context no longer
  carries `cv_no_label`; it carries `cv_label_mode`. So a copy renders the label on every button, the icon-only ones
  (`CardAction(no_label=True)`) included. The leaf branches on `cv_label_mode` (`"label"`, `"icon"`, `"both"`)
  ([The leaf contract](reference/buttons.md#the-leaf-contract)).

### Hooks instead of copies

Register these from your theme's `AppConfig.ready()`; a project's own settings still win over them.

- **Button classes:** `register_button_classes({...})` with `location:slot` keys, optionally
  `location:variant:mode` ([The class table](reference/buttons.md#the-class-table)). 1.0 adds the utility slots
  `*:active`, `card:flex` and `*:hidden-label` (#227), the card keys `card:root`, `card:body`, `card:title` (#243),
  the alert keys `alert:*` (#250), the `*:icon-host` keys for host-placed icons (#258), and the `form:*` keys for the
  crispy buttons. A theme on a framework that spells
  `active` or `visually-hidden` differently registers its own words and overrides no leaf
  ([A theme recipe](reference/buttons.md#a-theme-recipe)).
- **Icons [0.30]:** `register_icon_library(prefix, renderer=..., **config)` and `register_icons({...})`
  ([Registering icons from a theme](reference/icons.md#registering-icons-from-a-theme)). 1.0 adds the names
  `page-previous`, `page-next` and `message-success`, `message-info`, `message-warning`, `message-error`,
  `message-debug` ([Default table](reference/icons.md#default-table)), and the library keys `placement` and
  `standalone` for an icon library that puts the icon class on the button itself (#258,
  [Host placement](reference/icons.md#host-placement)).
- **The form frame:** `snippets/form_frame.html`, block `cv_form_frame` (#239).
- **The card:** extend `tags/card.html` and fill `card_title`, `card_content` and `card_actions` (#243). A copy of
  `view_card.content.html` misses the translated empty state, "No items found." (#246).
- **The alert frame:** `tags/alert.html` and its two bodies (#250). Its close control carries
  `data-cv-alert-dismiss` ([Contract changes](#contract-changes-in-templates-you-still-override)); a styled copy
  starts from the [Custom alert frame](reference/theme.md#custom-alert-frame) recipe.
- **Heading levels:** `CRUD_VIEWS_HEADER_LEVEL`, plus `{% cv_heading %}` for the headings in your theme's own
  templates, so they follow the same setting (#251, [Heading levels](reference/templates.md#heading-levels)).
- **JavaScript:** `cv.adapters.modal`, `cv.adapters.tooltip`, `cv.adapters.collapse` and `cv.adapters.alert` replace
  Bootstrap's API for a theme on another framework ([`cv.adapters`](reference/javascript.md#cvadapters)).
  `alert.close(el)` is new: it closes a dismissible alert
  ([Dismissible alerts](reference/javascript.md#dismissible-alerts)). How the theme assigns its adapters matters:
    - A partial map assigned **before** `adapters.js` loads needs nothing: every entry it leaves out, `alert`
      included, gets its default while `adapters.js` loads.
    - A theme that replaces the **whole map after** core loads (`cv.adapters = {...}`) discards the defaults, and
      core does not fill them in again. Its map must provide `alert` with `close(el)`, or every alert close button
      throws a `TypeError` and the alert stays. Replace single entries (`cv.adapters.modal = {...}`) or merge into
      the existing map (`Object.assign(cv.adapters, {...})`) instead; a map for a Bootstrap-compatible namespace
      takes the entry from the factory, `alert: cv.bootstrapAdapters(ns).alert`.

### Contract changes in templates you still override

- **Icon values [0.30].** `cv_icon_action`, `cv_icon_header` and `cv_menu_icon` hold icon values (`"detail"`,
  `"fas:truck"`), not CSS classes. Render them with `{% cv_icon cv_icon_action %}`; `<i class="{{ cv_icon_action }}">`
  renders an invisible icon for every stock action. The object-detail filters `icon_class` and `named_icon_class`
  are gone: an old copy of an object-detail layout or type template fails with `TemplateSyntaxError`. Use
  `{% cv_icon group.icon css="me-2" %}` and `{% cv_icon "boolean-true" %}`.
- **`fa-fw` [0.30]** in menu icons becomes `cv-icon-fw` from `crud_views/css/icons.css`.
- **Host-placed icons** (#258). A leaf you still override renders today's markup for every library without
  `placement: "host"`. To support a host library too, take over what the stock leaves do: append
  `{{ cv_icon_class }}` to the button's `class` when it is set, and render `{% cv_icon cv_icon %}` only when
  `cv_icon_inline` is true ([The leaf contract](reference/buttons.md#the-leaf-contract)). The menu toggle reads
  `cv_menu_icon_class` / `cv_menu_icon_inline`. A filter-toggle copy renders, for a host library and in the
  icon-bearing modes, the current state's class on the button plus `data-cv-filter-icon-open` /
  `data-cv-filter-icon-close` instead of the two spans
  ([The filter toggle contract](reference/javascript.md#the-filter-toggle-contract)).
- **Action menus:** `cv_menu_wrapper_class` and `cv_toggle_class` are no longer in the context of
  `tags/actions_menu.html` and `tags/actions_menu_toggle.html`; use `{% cv_button_class cv_location "menu-wrapper" %}`
  and `"menu-toggle"`. These two templates are still the ones to override for a framework with a different dropdown
  ([Templates that follow Bootstrap's DOM](reference/theme.md#templates-that-follow-bootstraps-dom)).
- **The filter toggle** (`tags/context_action_filter.html`). Its context carries the resolved `cv_label_mode`
  (#262), which decides whether the toggle has icons; a copy that ignores it renders the icon form in every mode.
  The icon instructions below apply to the icon-bearing modes, `"icon"` and `"both"`. A 0.29 copy renders one
  `<i class="{{ cv_icon_action }}">`, and 0.29's `list.filter.js` swapped its Font Awesome classes. In 1.0
  `cv_icon_action` is the icon name `"filter"`, so that `<i>` is invisible, and the script toggles two marked spans
  instead: render `<span data-cv-filter-icon="open">{% cv_icon "filter" %}</span>` and
  `<span data-cv-filter-icon="close">{% cv_icon "filter-close" %}</span>`, and hide the inactive one with the
  `hidden` attribute (#232). A 0.30 copy already has the two spans but hides them with `class="d-none"`: switch to
  `hidden`. In `"label"` mode the stock toggle renders its constant visible label without icon spans, host icon
  classes or `data-cv-filter-icon-*` attributes. In every mode render `aria-expanded` and
  `aria-controls="filter-collapse"`; the `#filter-collapse` id is a contract
  ([The filter toggle contract](reference/javascript.md#the-filter-toggle-contract)). For adopting the resolved modes,
  constant labels and optional icon hooks, see [The filter toggle](reference/context_buttons.md#the-filter-toggle).
- **The alert frame** (`tags/alert.html`). The close control carries `data-cv-alert-dismiss` instead of Bootstrap's
  `data-bs-dismiss="alert"`; `viewset.js` hands its nearest `role="alert"` frame to `cv.adapters.alert.close`.
  Replace the attribute completely, so the control carries only the new hook:

    ```django
    {# before #}
    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="{% translate 'Close' %}"></button>
    {# after #}
    <button type="button" class="btn-close" data-cv-alert-dismiss aria-label="{% translate 'Close' %}"></button>
    ```

    Keep `role="alert"` on the frame. Closing needs the core scripts `adapters.js` and then `viewset.js`, which
    `{% cv_js %}` renders in that order ([What the scripts need](reference/javascript.md#what-the-scripts-need)). The
    default adapter uses Bootstrap's `Alert` when its JavaScript is loaded and otherwise removes the alert
    ([Dismissible alerts](reference/javascript.md#dismissible-alerts), [Flash messages](reference/messages.md)).
    Migrate even if you keep Bootstrap. A copy that keeps only `data-bs-dismiss="alert"` still closes through
    Bootstrap's own data API, as long as it keeps Bootstrap's frame markup (the `alert` class) and Bootstrap's
    JavaScript is loaded; it never reaches `cv.adapters.alert`, so it gains neither a theme's adapter nor the removal
    without Bootstrap's `Alert` until you switch it. Do not keep both attributes: such a control is dismissed by
    Bootstrap and by core. The frame's `alert-dismissible fade show` and `btn-close` classes are still literal
    Bootstrap CSS; to style them your way, start from the tested
    [Custom alert frame](reference/theme.md#custom-alert-frame) recipe.

- **The modal:** the close button in `modal/content.html` uses `data-cv-modal-dismiss`. A copy with `data-bs-dismiss`
  keeps working under the Bootstrap adapter only. `{% cv_config %}` renders the modal shell from `modal/shell.html`,
  which you can override on its own ([Theming the modal](reference/modals.md#theming-the-modal)).
- **Formset controls** (`formsets/control.html`): add `data-cv-class` and `data-cv-class-danger` to the delete
  toggle (`formset.js` reads the classes from them), or it is no longer recoloured. Add `data-cv-tooltip="formset"`
  and the translated `title`s.
- **Object detail property-detail button:** `title` and `data-cv-tooltip="object-detail"` instead of `data-bs-title`,
  classes from the `object-detail:property-detail` key.
- **Table sort icons [0.30]** in `table/bootstrap5.html`: `{% cv_icon "table-sort-asc" %}` and
  `{% cv_icon "table-sort-desc" %}` instead of Font Awesome 4 classes.
- **Button container** (`tags/button/container.html`, #266): `cv_container_tag` is gone; the three logic templates
  no longer pass it. A copy of the container leaf that reads it renders `<>`: read `cv_layout.tag` and
  `cv_layout.label` from `{% cv_container_layout %}`, and render nothing when `cv_layout.empty`. A copy of
  `context_actions.html`, `columns/actions.html` or `card.html` that passed another tag sets
  `<location>:container-tag` instead ([Container element and label](reference/buttons.md#container-element-and-label)).
- **Active state:** `snippets/card_order.html` and the leaves take `active` from the `*:active` keys (#227). A copy
  with a hard-coded `active` keeps working.

### Table pagination overrides

`crud_views/table/bootstrap5.html` keeps the django-tables2 block names `pagination`, `pagination.previous`,
`pagination.range` and `pagination.next`. What changed is when `pagination.previous` and `pagination.next` run. Before
1.0 each block sat inside an availability test, so it rendered only when the page existed. In 1.0 it runs on every
paginated page, available direction or not, and holds the test itself, so a theme can restyle the disabled end in
the same block. A copied override that calls `table.page.previous_page_number` or `table.page.next_page_number`
without a test now raises `django.core.paginator.EmptyPage` on the first or the last page. Test
`table.page.has_previous` before calling `previous_page_number`, and `table.page.has_next` before calling
`next_page_number`.

If you overrode the blocks only to swap the `&laquo;` / `&raquo;` arrows, delete the override instead. Map the
`page-previous` and `page-next` icons in `CRUD_VIEWS_ICONS` and style the hidden labels with the
`pagination:hidden-label` key. This works for table and card pagination alike ([Pagination](reference/list_view.md#pagination)).
A structural copy that you keep has to adopt the shared key and the accessible structure:

- The `<nav>` label is the translated msgid `pagination`, which the stock `pagination` block already renders.
- An available direction is an `li` with the classes `previous page-item` or `next page-item` and a link. A missing
  direction is an `li` with `previous page-item disabled` or `next page-item disabled` and
  `<a class="page-link" aria-disabled="true">` without `href` or `tabindex`.
- Both states render `{% cv_icon "page-previous" %}` before the translated hidden `previous` label, and the hidden
  `next` label before `{% cv_icon "page-next" %}`. The label's class comes from
  `{% cv_button_class "pagination" "hidden-label" %}`; `cv_icon` supplies the decorative `aria-hidden` icon.
- The current page in `pagination.range` is a `<span class="page-link">` in an `li` with `aria-current="page"`. Leave
  the range block alone unless you need a different range; an override of `pagination.range` works as before.

Save the override as a child template under its own name, for example
`myproject/templates/myproject/table.html`. It extends `crud_views/table/bootstrap5.html`. A copy saved at
`crud_views/table/bootstrap5.html` in your project's `DIRS` also works, because Django resolves `{% extends %}` to the
package's template, but it then replaces the stock template for every table that uses it. Select your own template at
startup in your settings:

```python
DJANGO_TABLES2_TEMPLATE = "myproject/table.html"
```

django-tables2 reads that setting when a table class is created, so changing it later does not retarget an existing
class. A `Meta.template_name` on a table class, or a `template_name` passed to the table, takes precedence; if you
set one, it must name the same child. This copy overrides both direction blocks, adds `rel` to the available links,
and keeps every hook of the stock markup:

```django
{% extends "crud_views/table/bootstrap5.html" %}
{% load crud_views i18n %}

{% block pagination.previous %}
{% if table.page.has_previous %}
    <li class="previous page-item">
        <a href="{% cv_querystring table.prefixed_page_field=table.page.previous_page_number %}" class="page-link" rel="prev">{% cv_icon "page-previous" %}<span class="{% cv_button_class 'pagination' 'hidden-label' %}">{% translate 'previous' %}</span></a>
    </li>
{% else %}
    <li class="previous page-item disabled">
        <a class="page-link" aria-disabled="true">{% cv_icon "page-previous" %}<span class="{% cv_button_class 'pagination' 'hidden-label' %}">{% translate 'previous' %}</span></a>
    </li>
{% endif %}
{% endblock pagination.previous %}

{% block pagination.next %}
{% if table.page.has_next %}
    <li class="next page-item">
        <a href="{% cv_querystring table.prefixed_page_field=table.page.next_page_number %}" class="page-link" rel="next"><span class="{% cv_button_class 'pagination' 'hidden-label' %}">{% translate 'next' %}</span>{% cv_icon "page-next" %}</a>
    </li>
{% else %}
    <li class="next page-item disabled">
        <a class="page-link" aria-disabled="true"><span class="{% cv_button_class 'pagination' 'hidden-label' %}">{% translate 'next' %}</span>{% cv_icon "page-next" %}</a>
    </li>
{% endif %}
{% endblock pagination.next %}
```

The card pagination (`crud_views/snippets/pagination.html`) has no blocks, and its default markup is unchanged by
this; its earlier migration is under [CSS and tests that select on markup](#css-and-tests-that-select-on-markup).

## Silent breaks

Everything that renders differently and raises nothing, as one checklist. A clean `manage.py check` says nothing
about these.

**In your project:**

- [ ] **[0.30]** Object detail group icons with a bare name (`icon="truck"`) render an invisible `<i class="truck">`:
  use `"fas:truck"` ([Views and Python code](#views-and-python-code)).
- [ ] `cv.cvModalOpen(url, "modal-lg")` and `data-cv-modal-size="modal-lg"` open the default size: use `"lg"`
  ([JavaScript](#javascript)).
- [ ] Hand-listed static files without `crud_views/js/adapters.js` lose the modal, filter and tooltip behaviour and
  alert dismissal ([Base template and your own templates](#base-template-and-your-own-templates)).
- [ ] A script that replaces the whole `cv.adapters` map after core loads without an `alert` entry makes every alert
  close button throw ([Hooks instead of copies](#hooks-instead-of-copies)).
- [ ] **[0.30]** Hand-listed static files without `crud_views/css/icons.css` lose the menu icon width.
- [ ] **[0.30]** An overridden `cv_get_filter_icon()` is no longer called ([Views and Python code](#views-and-python-code)).
- [ ] CSS, JavaScript selectors and tests that match the old markup: sort icons, pagination
  (`.disabled > span.page-link`, `&laquo;` / `&raquo;`), `d-none`, button attribute order and class strings,
  formset control titles, empty button containers that no longer render, the alert close control's
  `data-bs-dismiss="alert"` ([CSS and tests that select on markup](#css-and-tests-that-select-on-markup)).
- [ ] Card buttons show their icon next to the label, and card actions without a `variant` take the target view's
  variant ([Views and Python code](#views-and-python-code)).
- [ ] Form buttons are `<button>` elements: selectors and tests on `input[type="submit"]` or `input[name="reset"]` find
  nothing ([Markup and submitted data](#markup-and-submitted-data)).
- [ ] A form button value or label written as template code (`{{ request.user }}`) shows that text
  ([Values are literal text](#values-are-literal-text)).
- [ ] `helper.inputs = []` on a filter helper no longer hides Apply and Reset and drops the hidden sort inputs
  ([Filter helpers](#filter-helpers)).

**In a theme, or in project template overrides:**

- [ ] A `tags/messages.html` copy renders `class="alert alert-"` with an empty body
  ([Templates to delete](#templates-to-delete)).
- [ ] A `tags/alert.html` copy with `data-bs-dismiss="alert"` closes only through Bootstrap's JavaScript and ignores
  `cv.adapters.alert` ([Contract changes](#contract-changes-in-templates-you-still-override)).
- [ ] A copy of a form page's content template uploads no files on create and custom-form pages
  ([Templates to delete](#templates-to-delete)).
- [ ] Copies of `tags/button_submit.html`, `tags/button_cancel.html`, `tags/button_delete.html` and `tags/icon.html`
  are no longer rendered ([Templates to delete](#templates-to-delete)).
- [ ] A `tags/button/container.html` copy that reads `cv_container_tag` renders `<>`, and a logic-template copy that
  passes `cv_container_tag` loses its tag ([Contract changes](#contract-changes-in-templates-you-still-override)).
- [ ] A `tags/card_action.html` copy that branches on `cv_no_label` shows the label on icon-only buttons
  ([Templates to move](#templates-to-move)).
- [ ] Markup moved into a leaf with its 0.29 keys renders `href=""` and no icon ([Templates to move](#templates-to-move)).
- [ ] A `tags/actions_menu_item_label.html` copy no longer changes the stock menu
  ([Templates to move](#templates-to-move)).
- [ ] **[0.30]** `<i class="{{ cv_icon_action }}">` (or `cv_icon_header`, `cv_menu_icon`) renders an invisible icon
  ([Contract changes](#contract-changes-in-templates-you-still-override)).
- [ ] `tags/actions_menu.html` and `tags/actions_menu_toggle.html` copies that read `cv_menu_wrapper_class` or
  `cv_toggle_class` render an empty `class` ([Contract changes](#contract-changes-in-templates-you-still-override)).
- [ ] A `tags/context_action_filter.html` copy shows no icon (0.29) or the wrong icon after the first click (0.30),
  and a copy that still ignores `cv_label_mode` stays icon-only where the project configures `"both"` or `"label"`
  for the toggle ([Contract changes](#contract-changes-in-templates-you-still-override),
  [The filter toggle](reference/context_buttons.md#the-filter-toggle)).
- [ ] A `formsets/control.html` copy without `data-cv-class` / `data-cv-class-danger` no longer recolours the delete
  toggle ([Contract changes](#contract-changes-in-templates-you-still-override)).
- [ ] A custom form-button template that reads `input.value` renders empty attributes, and an override of crispy's
  `layout/baseinput.html` no longer styles the package form buttons ([Custom button templates](#custom-button-templates)).
- [ ] A `view_card.content.html` copy keeps the untranslated "No items found." ([Hooks instead of copies](#hooks-instead-of-copies)).
