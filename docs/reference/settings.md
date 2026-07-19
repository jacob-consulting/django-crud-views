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

## Session

Session settings.

| Key              | Description                                                | Type  | Default   |
|------------------|------------------------------------------------------------|-------|-----------|
| CRUD_VIEWS_SESSION_DATA_KEY | The session key used to store data for `django-crud-views` | `str` | `viewset` |

## Filter

Settings for filter.

| Key                           | Description                                     | Type   | Default            |
|-------------------------------|-------------------------------------------------|--------|--------------------|
| CRUD_VIEWS_FILTER_PERSISTENCE            | Store filter in Django session                  | `bool` | True               |
| CRUD_VIEWS_FILTER_PINNED                 | When `True`, list/card filters render always-open and the filter toggle button is hidden. Per-view override via `cv_filter_pinned`. | `bool` | False |
| CRUD_VIEWS_FILTER_ICON                   | Filter icon (bootstrap5 only)                    | `str`  | fa-solid fa-filter |
| CRUD_VIEWS_FILTER_RESET_BUTTON_CSS_CLASS | Filter reset button css class (bootstrap5 only) | `str`  | btn btn-secondary  |

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

## List Actions

Default list actions for list view.

| Key          | Description   | Type        | Default                  |
|--------------|---------------|-------------|--------------------------|
| CRUD_VIEWS_LIST_ACTIONS | Global switch | `List[str]` | `detail, update, delete` |

## Content Security Policy (CSP)

django-crud-views is compatible with strict Content Security Policy headers. The package does not use inline scripts, inline event handlers, inline styles, or `javascript:` URIs.

Projects can enforce a CSP without `unsafe-inline` for both `script-src` and `style-src` directives.

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

All interactive behavior (list action form submissions, cancel button navigation, filter toggling) is handled via event delegation in the external `viewset.js` static file. Dynamic data is passed from Django to JavaScript through `data-*` attributes:

- `#cv-config` element carries `data-request-path` and `data-query-string`
- `[data-cv-action="submit-form"]` elements trigger form submission
- `[data-cv-cancel-url]` elements trigger navigation

No nonces or hashes are required.

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
