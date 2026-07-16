# Django CRUD Views

![Tests](https://github.com/jacob-consulting/django-crud-views/actions/workflows/tests.yml/badge.svg)
![Lint](https://github.com/jacob-consulting/django-crud-views/actions/workflows/lint.yml/badge.svg)
![Coverage](https://codecov.io/gh/jacob-consulting/django-crud-views/branch/main/graph/badge.svg)
![PyPI](https://img.shields.io/pypi/v/django-crud-views)
![License](https://img.shields.io/pypi/l/django-crud-views)
![Docs](https://readthedocs.org/projects/django-crud-views/badge/?version=latest)

**Stop hand-writing the same list, detail, create, update and delete views for every model.**
Define your model, register a `ViewSet`, and Django CRUD Views generates the pages, wires up
every URL, and cross-links the views — using *your* templates and *your* permissions, right
inside your own app.

## This is all you write

```python
# app/views.py
import django_tables2 as tables

from crud_views.lib.viewset import ViewSet
from crud_views.lib.table import Table
from crud_views.lib.views import (
    ListViewTableMixin,
    ListViewPermissionRequired,
    DetailViewPermissionRequired,
    CreateViewPermissionRequired,
    UpdateViewPermissionRequired,
    DeleteViewPermissionRequired,
)
from .models import Author

cv_author = ViewSet(model=Author, name="author")


class AuthorTable(Table):
    first_name = tables.Column()
    last_name = tables.Column()


class AuthorList(ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_author
    table_class = AuthorTable


class AuthorDetail(DetailViewPermissionRequired):
    cv_viewset = cv_author


class AuthorCreate(CreateViewPermissionRequired):
    cv_viewset = cv_author
    fields = ["first_name", "last_name"]


class AuthorUpdate(UpdateViewPermissionRequired):
    cv_viewset = cv_author
    fields = ["first_name", "last_name"]


class AuthorDelete(DeleteViewPermissionRequired):
    cv_viewset = cv_author
```

```python
# app/urls.py
urlpatterns = cv_author.urlpatterns
```

You get list, detail, create, update and delete pages, every URL wired up, the views
cross-linked, and access gated by Django's permission system.

## Why developers use it

- **Skip the CRUD boilerplate** — one ViewSet replaces a pile of near-identical class-based views and `urls.py` entries.
- **Views that know their siblings** — automatic cross-linking that respects Django's permissions; no hand-written `reverse()` wiring.
- **Your app, your control** — your templates, URLs and permissions; not locked inside `/admin`.
- **Batteries included** — sortable, filterable, paginated tables, crispy forms and per-object permissions, integrated out of the box.
- **Grows with you** — nested parent/child URLs from ForeignKeys, plus optional workflow (FSM) and polymorphic models; Django system checks catch misconfiguration at startup.
- **Resources** — render non-ORM data (S3 listings, API results) through ViewSets: list, detail and custom actions without a Django model. See [docs](https://django-crud-views.readthedocs.io/en/latest/reference/resources/).

Built on [django-tables2](https://django-tables2.readthedocs.io/en/latest/), [django-filter](https://django-filter.readthedocs.io/en/stable/), [django-crispy-forms](https://django-crispy-forms.readthedocs.io/en/latest/), [django-polymorphic](https://django-polymorphic.readthedocs.io/en/stable/), [django-guardian](https://django-guardian.readthedocs.io/), [django-ordered-model](https://github.com/django-ordered-model/django-ordered-model) and [django-object-detail](https://django-object-detail.readthedocs.io/en/latest/).

## Install

```bash
pip install django-crud-views
```

Optional extras: `django-crud-views[guardian]` (per-object permissions), `django-crud-views[ordered]` (up/down ordering), `django-crud-views[all]` (everything).

## What it is not

- a replacement for Django's admin interface
- a complete page building system with navigations and lots of widgets

## Documentation

Full tutorial and reference: <https://django-crud-views.readthedocs.io>

## Current version
Current version: 0.12.1
