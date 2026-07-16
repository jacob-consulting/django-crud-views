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
`crud_views/view_list_table.html`, `crud_views/tags/button_submit.html`. Django's
`app_directories` template loader searches each app in `INSTALLED_APPS` **in order** and
returns the first template matching a given name.

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

## INSTALLED_APPS ordering (the one rule that matters)

Your theme app **must be listed before `crud_views`** so its templates are found first:

```python
INSTALLED_APPS = [
    # ...
    "myapp_theme.apps.MyAppThemeConfig",   # <-- before crud_views
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

## Worked example: restyle the submit button

Give your theme app a template at
`myapp_theme/templates/crud_views/tags/button_submit.html`:

```html
<button type="submit" class="my-fancy-button">{{ label }}</button>
```

With `myapp_theme` listed before `crud_views` in `INSTALLED_APPS`, every crud_views form now
renders your button, while all other templates keep the bootstrap5 defaults.
