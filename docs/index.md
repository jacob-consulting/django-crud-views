# Django CRUD Views

**Stop hand-writing the same list, detail, create, update and delete views for every
model.** Define your model, register a `ViewSet`, and Django CRUD Views generates the
pages, wires up every URL, and cross-links the views — using *your* templates and *your*
permissions, right inside your own app.

## This is all you write

A ViewSet is the container for all sibling views of one model:

<!-- cv-sync: library/views.py -->
```python
cv_author = ViewSet(model=Author, name="author", icon_header="fa-regular fa-user")
```

One class per page — here the list view with a sortable table and filter form:

<!-- cv-sync: library/views.py -->
```python
class AuthorListView(BreadcrumbMixin, ListViewTableMixin, ListViewTableFilterMixin, ListViewPermissionRequired):
    cv_viewset = cv_author
    table_class = AuthorTable
    filterset_class = AuthorFilter
    formhelper_class = AuthorFilterFormHelper
```

And one line of URL wiring:

<!-- cv-sync: library/urls.py -->
```python
urlpatterns = cv_author.urlpatterns + cv_book.urlpatterns
```

That's the real, runnable code of the [tutorial](getting_started/index.md) — a CI check
keeps this page and the tutorial in sync with the example project.

## Why developers use it

- **Skip the CRUD boilerplate** — one ViewSet replaces a pile of near-identical
  class-based views and `urls.py` entries.
- **Views that know their siblings** — automatic cross-linking that respects Django's
  permission system; no hand-written `reverse()` wiring.
- **Your app, your control** — your templates, URLs and permissions; built on Django's
  generic class-based views, not locked inside `/admin`.
- **Batteries included** — sortable, filterable, paginated tables
  ([django-tables2](https://django-tables2.readthedocs.io/en/latest/),
  [django-filter](https://django-filter.readthedocs.io/en/stable/)), crispy forms
  ([django-crispy-forms](https://django-crispy-forms.readthedocs.io/en/latest/)),
  breadcrumbs, formsets, and nested parent/child URLs.
- **Grows with your app** — optional extensions for workflows
  ([django-fsm-2](https://github.com/django-commons/django-fsm-2)), polymorphic models
  ([django-polymorphic](https://django-polymorphic.readthedocs.io/en/stable/)),
  per-object permissions ([django-guardian](https://django-guardian.readthedocs.io/)),
  ordering ([django-ordered-model](https://github.com/django-ordered-model/django-ordered-model))
  and non-ORM resources.
- **Pluggable themes** — `bootstrap5` ships as the default;
  [bring your own theme](reference/theme.md).
- **Fails early** — Django system checks validate your configuration at startup.

## API stability

From 1.0.0 on, django-crud-views follows [semantic versioning](https://semver.org) with a
[documented public API surface](development/stability.md): breaking changes to the public
API only happen in major releases, and deprecations are announced ahead of removal.

## What it is not

- a replacement for Django's admin interface
- a complete page building system with navigations and lots of widgets

# Version

Current version: 0.17.0
