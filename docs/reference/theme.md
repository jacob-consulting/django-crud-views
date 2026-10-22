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

## Worked example: restyle the buttons

Register the classes as above — the `*:active` and `*:hidden-label` keys included when your framework spells those
utilities differently — and override nothing for looks (the worked registration is in
[Buttons](buttons.md#a-theme-recipe)). Override a leaf only where the markup itself differs: give your theme app a
template at `myapp_theme/templates/crud_views/tags/button/action.html`, and with `myapp_theme` listed before
`crud_views` in `INSTALLED_APPS` every action button renders your leaf with the registered classes, while all other
templates keep the bootstrap5 defaults.

The thin templates `tags/context_action.html`, `tags/list_action.html`, `tags/card_action.html` and
`tags/actions_menu_item.html` are logic templates: do not copy them, override the leaves instead.

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

## Disabled actions in overridden templates

The leaves `tags/button/action.html` and `tags/button/menu_item.html` receive `cv_disabled` and
`cv_disabled_reason`. If you override one of them, keep the `disabled data-cv-disabled` handling to support
`CRUD_VIEWS_INACCESSIBLE_ACTIONS = "disable"`; without it a disabled action looks enabled. The logic templates no
longer carry a branch of their own. See [Hide or disable inaccessible actions](inaccessible_actions.md).
