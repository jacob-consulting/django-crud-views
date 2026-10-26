# Settings

## Basic settings

All keys below are flat, module-level Django settings (set them in `settings.py`), each
named exactly as shown — there is no `CRUD_VIEWS = {...}` dict.

| Key                  | Description                                              | Type  | Default      |
|----------------------|----------------------------------------------------------|-------|--------------|
| CRUD_VIEWS_EXTENDS              | Base template that crud_views templates extend (required; can be overridden per ViewSet/view — see [Base template](templates.md))     | `str` | `None`       |
| CRUD_VIEWS_MANAGE_VIEWS_ENABLED | Show manage view button, values are: `yes,no,debug_only` | `str` | `debug_only` |
| CRUD_VIEWS_MANAGE_GROUP | Django group name that grants manage view access regardless of CRUD_VIEWS_MANAGE_VIEWS_ENABLED | `str` | `CRUD_VIEWS_MANAGE` |
| CRUD_VIEWS_MANAGE_SHOW_USERS | Whether to show a Users column in the Permission Holders section of ManageView | `bool` | `False` |
| CRUD_VIEWS_MANAGE_VIEW_CLASS | Dotted import path to a custom `ManageView` subclass used as the base for auto-registered manage views. When `None`, uses `ManageView`. | `str \| None` | `None` |
| CRUD_VIEWS_GUARDIAN_MANAGE_VIEW_CLASS | Dotted import path to a custom `GuardianManageView` subclass used as the base for auto-registered guardian manage views. When `None`, uses `GuardianManageView`. | `str \| None` | `None` |
| CRUD_VIEWS_BREADCRUMB_PREFIX | List of dicts with `title`, `url_name`, optional `args`/`kwargs` prepended to every breadcrumb (see [Breadcrumb](breadcrumb.md)); malformed entries fail system check `crud_views.E102`. | `list` | `[]` |
| CRUD_VIEWS_STRICT | Strict mode: misconfigurations that are otherwise logged and skipped raise instead (an unregistered key in a button tag, an icon-only button without an icon). pytest-django runs tests with `DEBUG=False`, so set it to `True` in your test settings to make such mistakes fail the tests. | `bool` | `DEBUG` |

## Session

Session settings.

| Key              | Description                                                | Type  | Default   |
|------------------|------------------------------------------------------------|-------|-----------|
| CRUD_VIEWS_SESSION_DATA_KEY | The session key used to store data for `django-crud-views` | `str` | `viewset` |

## Origin parameter

| Key              | Description                                                | Type  | Default   |
|------------------|------------------------------------------------------------|-------|-----------|
| CRUD_VIEWS_ORIGIN_PARAM | Query-string parameter that carries the origin view key for views with `cv_cancel_keys` or `cv_success_keys` (see [Dynamic cancel target](update_view.md#dynamic-cancel-target) and [Dynamic success target](update_view.md#dynamic-success-target)). Must match `^[a-z][a-z0-9_]*$`; otherwise system check `crud_views.E103` fails. Renamed from `CRUD_VIEWS_CANCEL_ORIGIN_PARAM` in 0.26.0. | `str` | `cv_from` |

## Filter

Settings for filter.

| Key                           | Description                                     | Type   | Default            |
|-------------------------------|-------------------------------------------------|--------|--------------------|
| CRUD_VIEWS_FILTER_PERSISTENCE            | Store filter in Django session                  | `bool` | True               |
| CRUD_VIEWS_FILTER_PINNED                 | When `True`, list/card filters render always-open and the filter toggle button is hidden. Per-view override via `cv_filter_pinned`. | `bool` | False |

## View Context Actions

Default context actions for CRUD views.

| Key                           | Description   | Type        | Default                  |
|-------------------------------|---------------|-------------|--------------------------|
| CRUD_VIEWS_LIST_CONTEXT_ACTIONS          | Global switch | `List[str]` | `parent, list, filter, create` |
| CRUD_VIEWS_DETAIL_CONTEXT_ACTIONS        | Global switch | `List[str]` | `home, detail, update, delete` |
| CRUD_VIEWS_CREATE_CONTEXT_ACTIONS        | Global switch | `List[str]` | `home, create`                 |
| CRUD_VIEWS_UPDATE_CONTEXT_ACTIONS        | Global switch | `List[str]` | `home, detail, update, delete` |
| CRUD_VIEWS_DELETE_CONTEXT_ACTIONS        | Global switch | `List[str]` | `home, detail, update, delete` |
| CRUD_VIEWS_MANAGE_CONTEXT_ACTIONS        | Global switch | `List[str]` | `home`                         |
| CRUD_VIEWS_CREATE_SELECT_CONTEXT_ACTIONS | Global switch | `List[str]` | `home, create_select`          |
| CRUD_VIEWS_POLYMORPHIC_CREATE_CONTEXT_ACTIONS | Global switch | `List[str]` | `home`                    |

## List Actions

Default list actions for list view.

| Key          | Description   | Type        | Default                  |
|--------------|---------------|-------------|--------------------------|
| CRUD_VIEWS_LIST_ACTIONS | Global switch | `List[str]` | `detail, update, delete` |

## Inaccessible actions

| Key | Description | Type | Default |
|-----|-------------|------|---------|
| CRUD_VIEWS_INACCESSIBLE_ACTIONS | `"hide"` or `"disable"`: how actions the user may not use are rendered. Overridable per ViewSet (`inaccessible_actions`) and per view (`cv_inaccessible_actions`). See [Hide or disable inaccessible actions](inaccessible_actions.md). Invalid values raise `crud_views.E104`. | `str` | `hide` |

## Action menus

| Key | Description | Type | Default |
|-----|-------------|------|---------|
| CRUD_VIEWS_LIST_ACTIONS_INLINE | List row actions kept as buttons; the rest go into a `⋯` menu. `None`: no menu. See [Action menus](action_menus.md). Invalid values raise `crud_views.E105`. | `list[str] \| None` | `None` |
| CRUD_VIEWS_CONTEXT_ACTIONS_INLINE | The same for the context toolbar. | `list[str] \| None` | `None` |
| CRUD_VIEWS_CARD_ACTIONS_INLINE | The same for card actions. | `list[str] \| None` | `None` |
| CRUD_VIEWS_LABEL_MODE_DEFAULTS | Label-mode floor per button location (`"context"`, `"list"`, `"card"`), merged per location over the package defaults: a location you leave out keeps its package default. Read at call time. See [Label-mode configuration](#label-mode-configuration). Invalid values raise `crud_views.E108`. | `dict[str, str]` | `{"context": "icon", "list": "icon", "card": "both"}` |
| CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE | Label mode per context toolbar action key (`"label"`, `"icon"`, `"both"`), used whole when neither the view nor its ViewSet sets a map. A key not named falls through to the target view's `cv_context_action_label_mode`, then to the `"context"` entry of `CRUD_VIEWS_LABEL_MODE_DEFAULTS` (package default `"icon"`). See [Label-mode configuration](#label-mode-configuration). Invalid values raise `crud_views.E106`. | `dict[str, str]` | `{}` |
| CRUD_VIEWS_LIST_ACTIONS_LABEL_MODE | Label mode per list row action key, used whole when neither the view nor its ViewSet sets a map. A key not named takes the `"list"` entry of `CRUD_VIEWS_LABEL_MODE_DEFAULTS` (package default `"icon"`). See [Label-mode configuration](#label-mode-configuration). Invalid values raise `crud_views.E106`. | `dict[str, str]` | `{}` |

### Label-mode configuration

A button shows its label as text only (`"label"`), as an icon with a visually hidden label and a tooltip (`"icon"`) or
as both (`"both"`). Several knobs choose the mode, and they do not combine the same way: the defaults setting is
merged per location, every per-action map replaces the layer below it whole.

| Knob | merge or replace | layer | keys |
|---|---|---|---|
| `CRUD_VIEWS_LABEL_MODE_DEFAULTS` | merged per location over the package defaults `{"context": "icon", "list": "icon", "card": "both"}` | project floor (setting) | button location: `"context"`, `"list"`, `"card"` |
| `CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE` | replace: used whole when no ViewSet or view map is set | setting | context toolbar action key |
| `CRUD_VIEWS_LIST_ACTIONS_LABEL_MODE` | replace: used whole when no ViewSet or view map is set | setting | list row action key |
| `ViewSet` `context_actions_label_mode` / `list_actions_label_mode` | replace the setting whole; `None` inherits, `{}` selects an empty map | ViewSet | action key |
| `CrudView` `cv_context_actions_label_mode` / `cv_list_actions_label_mode` | replace the ViewSet and the setting whole; `None` inherits, `{}` selects an empty map | view rendering the group | action key |
| `cv_context_action_label_mode` | scalar override, nothing merged; `None` means unset | target view (the view a toolbar button opens) | none: one string |
| `cv_card_actions_label_mode` | scalar override, nothing merged; `None` means the `"card"` floor | card view | none: one string |

Existing per-action maps keep whole-dict replacement semantics. Only `CRUD_VIEWS_LABEL_MODE_DEFAULTS` merges, and it
merges per location, not per action key. The singular `cv_context_action_label_mode` (a string, set on the view a
button opens) is not the plural `cv_context_actions_label_mode` (a dict, set on the page showing the toolbar); see
[Target-view default](action_menus.md#target-view-default). In which order the knobs apply is described once per
location: [context](action_menus.md#context-label-mode-resolution),
[list](action_menus.md#list-label-mode-resolution) and [card](action_menus.md#card-label-mode-resolution).

To get the 0.29 label-only card buttons back on every card view of the project:

```python
# settings.py
CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"card": "label"}
```

Independently of that, to show icon and text on every toolbar button that no map, button or target view decides:

```python
# settings.py
CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"context": "both"}
```

The resolved values are available in Python:

- `crud_views.lib.view.label_mode.default_label_mode(location)` returns the floor of `"context"`, `"list"` or
  `"card"`: the setting's entry for it, else the package default. It reads the setting on every call, so
  `override_settings` in tests applies without a reset. An unknown `location` is a caller bug and raises `ValueError`
  in every mode.
- `crud_views.lib.view.label_mode.LABEL_MODE_DEFAULTS` is the read-only package default map (a `MappingProxyType`);
  change the floor with the setting, not by assigning to it.
- `CardListView.cv_get_card_actions_label_mode()` returns the mode a card action without its own `label_mode` gets:
  `cv_card_actions_label_mode` when set, else `default_label_mode("card")`.

System check `crud_views.E108` (error) reports a setting that is not a dict, a key that is not a button location and a
mode that is not exactly `"label"`, `"icon"` or `"both"`. At render an unknown key is ignored. A setting that is not a
dict, or an invalid mode for the location being rendered, raises `ValueError` in strict mode
([`CRUD_VIEWS_STRICT`](#basic-settings), default `DEBUG`); otherwise it logs one warning per location and value and
the location falls back to its package default.

## Icons

| Key | Description | Type | Default |
|-----|-------------|------|---------|
| CRUD_VIEWS_ICONS | Semantic icon name to icon value; merged per key over the defaults. Includes `actions-menu` and `filter`, which replace the removed `CRUD_VIEWS_ACTIONS_MENU_ICON` and `CRUD_VIEWS_FILTER_ICON`. See [Icons](icons.md). | `dict[str, str]` | `{}` |
| CRUD_VIEWS_ICON_LIBRARIES | Library prefix to library config (renderer, class, ...); merged per prefix over the built-ins `far`, `fas`, `bi`. See [Icons](icons.md#libraries). | `dict[str, dict]` | `{}` |

## Headings

| Key | Description | Type | Default |
|-----|-------------|------|---------|
| CRUD_VIEWS_HEADER_LEVEL | The level of your `{% cv_header %}` in the base template (1–5). The package's own headings (card titles, workflow sections, object-detail groups, the accordion) render one level below it and keep their look; the modal title renders at it. `None` leaves every heading at its stock level. See [Heading levels](templates.md#heading-levels). Invalid values raise `crud_views.E107`. | `int \| None` | `None` |

## Buttons

| Key | Description | Type | Default |
|-----|-------------|------|---------|
| CRUD_VIEWS_BUTTON_CLASSES | `location:slot` key to the CSS classes of a button; merged per key over the defaults, `None` switches the classes off. Replaces the removed `CRUD_VIEWS_FILTER_RESET_BUTTON_CSS_CLASS` (`form:filter-reset`). See [Buttons](buttons.md). | `dict[str, str \| None]` | `{}` |

## Content Security Policy (CSP)

django-crud-views is compatible with strict Content Security Policy headers. The package does not use inline scripts, inline event handlers, inline styles, or `javascript:` URIs.

Projects can enforce a CSP without `unsafe-inline` for both `script-src` and `style-src` directives. For nonce-based strict CSP (`'strict-dynamic'`), the asset tags emit nonces automatically — see [Nonce support](#nonce-support).

### Template tags

The `{% cv_config %}` template tag renders server-side request data as `data-*` attributes on a hidden DOM element. Place it in your base template where `{% cv_const_js %}` was previously used:

```html
{% load crud_views %}

{% cv_config %}
{% cv_css %}
{% cv_js %}
```

The `{% cv_const_js %}` tag still works as a backwards-compatible alias but renders the same CSP-safe output as `{% cv_config %}`.

!!! warning "Upgrading from < 0.4.0: `{% cv_csrf_token %}` was removed"

    The `{% cv_csrf_token %}` template tag was removed in the 0.4.0 CSP refactor. If you upgrade from
    an earlier version you will get `TemplateSyntaxError: Invalid block tag 'cv_csrf_token'`. Remove the
    tag from your templates — CSRF/config data is now provided by `{% cv_config %}` (or its alias
    `{% cv_const_js %}`) in your base template, as shown above.

### JavaScript architecture

All interactive behavior is handled via event delegation in external static files: list action form submissions and cancel button navigation in `viewset.js`, the filter toggle in `list.filter.js`, modals in `modal.js`. Calls into Bootstrap go through `cv.adapters`, see [JavaScript](javascript.md). Dynamic data is passed from Django to JavaScript through `data-*` attributes:

- `#cv-config` element carries `data-request-path` and `data-query-string`
- `[data-cv-action="submit-form"]` elements trigger form submission
- `[data-cv-cancel-url]` elements trigger navigation

For host-allowlist policies (`script-src 'self'`) no nonces or hashes are required. Nonce-based policies are supported automatically — see below.

### Nonce support

Under a strict CSP (`script-src 'nonce-…' 'strict-dynamic'`), browsers ignore host allowlists, so every `<script>` tag needs a `nonce` attribute. `{% cv_js %}` and `{% cv_css %}` detect the request's CSP nonce automatically and render it on every tag — no configuration needed:

- **Django 6.0+ built-in CSP**: enable `django.middleware.csp.ContentSecurityPolicyMiddleware` and include the `CSP.NONCE` sentinel in `SECURE_CSP`. The tags use `django.middleware.csp.get_nonce()`.
- **Django 4.2/5.2 with [django-csp](https://django-csp.readthedocs.io/)**: the tags read the `request.csp_nonce` attribute set by `CSPMiddleware`.
- **Custom setups**: store the nonce on the request under the attribute named by `CRUD_VIEWS_CSP_NONCE_ATTR` (default `csp_nonce`), or expose it as a `csp_nonce` template context variable.

Without CSP middleware the output is unchanged — no nonce attributes are rendered. The tags need the `django.template.context_processors.request` context processor (part of Django's default template configuration).

!!! warning "Nonces and cached HTML"

    A nonce is generated per request. If rendered pages are cached (Django's cache
    middleware, a reverse proxy, or a CDN), the cached HTML keeps the nonce it was
    rendered with while each new response carries a fresh header nonce — and the
    browser then blocks the assets. Exclude nonce-bearing pages from HTML caching,
    or use a host-allowlist policy instead of a nonce-based one.

| Key                        | Description                                                        | Type  | Default     |
|----------------------------|--------------------------------------------------------------------|-------|-------------|
| CRUD_VIEWS_CSP_NONCE_ATTR  | Request attribute the asset tags read the CSP nonce from           | `str` | `csp_nonce` |

### Subresource integrity (SRI)

Asset bundles registered via `register_assets()` accept `Asset` instances alongside plain path strings, carrying `integrity` and `crossorigin` attributes for external URLs:

```python
from crud_views.lib.assets import Asset, register_assets

register_assets(
    key="my_widget",
    js=[
        "my_widget/widget.js",  # own static file — no SRI needed
        Asset(
            path="https://cdn.example.com/lib.min.js",
            integrity="sha384-…",  # crossorigin="anonymous" is added automatically
        ),
    ],
)
```

System checks validate SRI metadata at startup: `crud_views.E330` rejects integrity values without a `sha256-`/`sha384-`/`sha512-` prefix, and `crud_views.W332` warns when integrity is set on a same-origin static path (SRI there breaks on every asset edit and adds no security value).

## Asset bundling

| Key                       | Description                                                                                       | Type   | Default |
|---------------------------|---------------------------------------------------------------------------------------------------|--------|---------|
| CRUD_VIEWS_ASSETS_BUNDLED | `{% cv_js %}`/`{% cv_css %}` emit only external (CDN) entries; a bundler such as django-pipeline delivers all local assets. See [Bundling with django-pipeline](assets.md#bundling-with-django-pipeline). | `bool` | `False` |

## django-tables2 compatibility

The list view table template `crud_views/table/bootstrap5.html` works with **both django-tables2 2.x and 3.x**.

django-tables2 3.0 renamed the `{% querystring %}` template tag to `{% querystring_replace %}` (to avoid shadowing Django 5.1's built-in `querystring` tag). To stay compatible across versions, the crud_views template uses the `{% cv_querystring %}` template tag, which delegates to whichever tag the installed django-tables2 version provides. No manual `DJANGO_TABLES2_TEMPLATE` switching is needed — just point it at the template:

```python
DJANGO_TABLES2_TEMPLATE = "crud_views/table/bootstrap5.html"
```

If you write your own table template, use `{% cv_querystring %}` (after `{% load crud_views %}`) in place of django-tables2's `{% querystring %}` / `{% querystring_replace %}` to keep it version-agnostic.

## crud_views_object_detail

Settings for the rich property-display [ObjectDetailView](object_detail_view.md), shipped
in-tree as the optional `crud_views_object_detail` app. These are prefixed with
`CRUD_VIEWS_OBJECT_DETAIL_` — see [ObjectDetailView settings](object_detail_settings.md) for
the full reference.

## Permission caching

`ViewSet` derives its permission map (`view`, `add`, `change`, `delete`, plus custom model permissions) from the `Permission` table via the `default_permissions` property. This property is a `cached_property`: the database is queried once per `ViewSet` and the result is **cached for the lifetime of the process**.

Consequences:

- Permissions added or renamed at runtime (e.g. via the admin) are not picked up until the process restarts.
- The first access requires migrations to have run (the `Permission` and `ContentType` tables must exist).
