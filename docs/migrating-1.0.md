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

### Base template

### Settings

### Views and Python code

### JavaScript

### CSS and tests that select on markup

## A downstream theme

Templates to delete or move, the hooks that replace copied templates, and contract changes in templates you still override.

## Silent breaks

Everything that renders differently and raises nothing, as one checklist.
