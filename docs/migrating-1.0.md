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
`crud_views.E106`, `viewset.E211`, `W291` ([toolbar and row label modes](reference/action_menus.md)).

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

- **Icon settings [0.30]** (`crud_views.E350`). The icons now come from one table, `CRUD_VIEWS_ICONS`
  ([Icons](reference/icons.md#crud_views_icons)):

    ```python
    # 0.29
    CRUD_VIEWS_ACTIONS_MENU_ICON = "fa-solid fa-bars"
    CRUD_VIEWS_FILTER_ICON = "fa-solid fa-magnifying-glass"

    # 1.0
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

- **`CRUD_VIEWS_FILTER_RESET_BUTTON_CSS_CLASS`** (`crud_views.E360`) moves into the button class table:
  `CRUD_VIEWS_BUTTON_CLASSES = {"form:filter-reset": "btn btn-secondary"}` ([Buttons](reference/buttons.md#crud_views_button_classes)).

### Views and Python code

- **`cv_modal_size`** (`viewset.E250`) takes the tokens `""`, `"sm"`, `"lg"` and `"xl"`: `cv_modal_size = "modal-lg"`
  becomes `cv_modal_size = "lg"` ([Modals](reference/modals.md)).
- **If you override `cv_get_context()`:** it takes a keyword-only `location`, and every button path passes it. An
  override with the old signature raises `TypeError` on the first toolbar. Accept it and pass it on (#216):

    ```python
    def cv_get_context(self, key=None, obj=None, user=None, request=None, *, location=None):
        context = super().cv_get_context(key, obj, user, request, location=location)
        ...
        return context
    ```

- **If anything puts `cv_no_label` into a button's context** (a `cv_get_context()` override, a dict passed to
  `{% cv_render_button %}`, or a `cv_no_label` variable in the page's template context): it raises `ValueError`.
  Use `cv_label_mode` (`"label"`, `"icon"` or `"both"`) instead. `CardAction(no_label=True)` keeps working.
- **Card buttons show their icon next to their label** (#213). To get the 0.29 label-only buttons back, set
  `cv_card_actions_label_mode = "label"` on the card view, or `CardAction(label_mode="label")` on one button
  ([Label mode](reference/card-list-view.md#label-mode)). An unknown value fails `viewset.E210`.
- **`CardAction.variant` defaults to the target view's variant.** A card action pointing at a create view without an
  explicit `variant` now renders `btn-primary`; set `variant="secondary"` to keep the 0.29 look
  ([Variants](reference/buttons.md#variants)).
- **Object detail group icons [0.30] are no longer prefixed for you.** `icon="truck"` must become
  `icon="fas:truck"` (or `"bi:truck"`), or `"truck"` must be added to `CRUD_VIEWS_ICONS`. Nothing flags a bare name:
  it is read as a raw CSS class and renders an invisible `<i class="truck">`
  ([Groups](reference/object_detail_configuration.md#groups)).
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

### CSS and tests that select on markup

None of these raise anything. Check your stylesheets, your JavaScript selectors and any test that asserts on HTML:

- **Table sort icons [0.30]** are Font Awesome 6 (`table-sort-asc` = `fas:angles-up`, `table-sort-desc` =
  `fas:angles-down`), and ascending now points up.
- **Icons [0.30]** render with `aria-hidden="true"`; the menu icons use `cv-icon-fw` instead of `fa-fw`.
- **Card list pagination** (#241): the arrows are the `page-previous` / `page-next` icons followed or preceded by a
  visually hidden "previous" / "next", not `&laquo;` / `&raquo;`. A disabled end is
  `<a class="page-link" aria-disabled="true">` without `href`, not a `<span>`. The current page carries
  `aria-current="page"`.
- **`hidden` instead of `d-none`** (#232): the filter toggle's icon spans and the hidden POST forms behind list and
  card actions use the `hidden` attribute. The filter toggle carries `aria-expanded`, `aria-controls="filter-collapse"`
  and `cv-key="filter"`.
- **Buttons:** one attribute order for every button; card buttons carry `cv-key`; card POST actions render
  `<button type="button">`; the active toolbar action carries `aria-current="page"`; a list or card button whose
  target is the current view renders `active`; the card row carries `cv-card-container`; card menu forms render
  before the row.
- **Form buttons:** the crispy cancel button renders `btn btn-secondary` (was `btn btn btn-secondary`), the filter
  reset `btn btn-secondary` (was `btn btn-inverse btn btn-secondary`), and the Delete label is translated.
- **Tooltip markup** (#202): the formset controls' `title` is the translated text of their `aria-label` ("Move up",
  "Move down", "Add row", "Delete row"), no longer `up` / `down` / `add` / `delete`. The object-detail
  property-detail button uses `title` instead of `data-bs-title`.
- **Alerts** (#250): the delete page's protection and related-objects alerts and the guardian manage page's config
  alert gain `role="alert"` and an icon before the heading.

## A downstream theme

Templates to delete or move, the hooks that replace copied templates, and contract changes in templates you still override.

## Silent breaks

Everything that renders differently and raises nothing, as one checklist.
