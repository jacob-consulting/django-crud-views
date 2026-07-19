# Django CRUD Views

![Tests](https://github.com/jacob-consulting/django-crud-views/actions/workflows/tests.yml/badge.svg)
![Lint](https://github.com/jacob-consulting/django-crud-views/actions/workflows/lint.yml/badge.svg)
![Coverage](https://codecov.io/gh/jacob-consulting/django-crud-views/branch/main/graph/badge.svg)
![PyPI](https://img.shields.io/pypi/v/django-crud-views)
![License](https://img.shields.io/pypi/l/django-crud-views)
![Docs](https://readthedocs.org/projects/django-crud-views/badge/?version=latest)

![The example app's author list: sortable filtered table, permission-aware buttons and breadcrumbs](https://raw.githubusercontent.com/jacob-consulting/django-crud-views/main/docs/getting_started/assets/readme-hero.png)

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
    CreateViewPermissionRequired,
    UpdateViewPermissionRequired,
    DeleteViewPermissionRequired,
)
from crud_views_object_detail.lib import ObjectDetailViewPermissionRequired
from .models import Author

cv_author = ViewSet(model=Author, name="author")


class AuthorTable(Table):
    first_name = tables.Column()
    last_name = tables.Column()


class AuthorList(ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_author
    table_class = AuthorTable


class AuthorDetail(ObjectDetailViewPermissionRequired):
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

`ObjectDetailViewPermissionRequired` is provided by the `crud_views_object_detail` app; add it to
`INSTALLED_APPS` alongside `crud_views`.

```python
# app/urls.py
urlpatterns = cv_author.urlpatterns
```

You get list, detail, create, update and delete pages, every URL wired up, the views
cross-linked, and access gated by Django's permission system.

## Why developers use it

- **Skip the CRUD boilerplate** — one ViewSet replaces a pile of near-identical class-based views and `urls.py` entries.
- **Views that know their siblings** — automatic cross-linking that respects Django's permission system; no hand-written `reverse()` wiring.
- **Your app, your control** — your templates, URLs and permissions; built on Django's generic class-based views, not locked inside `/admin`.
- **Batteries included** — sortable, filterable, paginated tables ([django-tables2](https://django-tables2.readthedocs.io/en/latest/), [django-filter](https://django-filter.readthedocs.io/en/stable/)), crispy forms ([django-crispy-forms](https://django-crispy-forms.readthedocs.io/en/latest/)), breadcrumbs, formsets, and nested parent/child URLs.
- **Grows with your app** — optional extensions for workflows ([django-fsm-2](https://github.com/django-commons/django-fsm-2)), polymorphic models ([django-polymorphic](https://django-polymorphic.readthedocs.io/en/stable/)), per-object permissions ([django-guardian](https://django-guardian.readthedocs.io/)), ordering ([django-ordered-model](https://github.com/django-ordered-model/django-ordered-model)) and [non-ORM resources](https://django-crud-views.readthedocs.io/en/latest/reference/resources/).
- **Pluggable themes** — `bootstrap5` ships as the default; [bring your own theme](https://django-crud-views.readthedocs.io/en/latest/reference/theme/).
- **Fails early** — Django system checks validate your configuration at startup.

## Install

```bash
pip install django-crud-views
```

Optional extras: `django-crud-views[guardian]` (per-object permissions), `django-crud-views[ordered]` (up/down ordering), `django-crud-views[all]` (everything).

## Run the example project

The repository ships a runnable example project — the tutorial's library app plus one app
per feature. All you need is Python 3.12+:

```bash
git clone https://github.com/jacob-consulting/django-crud-views.git
cd django-crud-views
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[all,examples]"
cd examples/bootstrap5
python manage.py migrate
python manage.py seed
python manage.py runserver
```

Browse <http://127.0.0.1:8000/> and log in with `alice` / `alice`.
These instructions are CI-tested on Linux, macOS and Windows.

If you use [uv](https://docs.astral.sh/uv/) and [task](https://taskfile.dev/), the shortcut
is `task dev && task run` from the repository root.

## What it is not

- a replacement for Django's admin interface
- a complete page building system with navigations and lots of widgets

## Documentation

Full tutorial and reference: <https://django-crud-views.readthedocs.io>

## Current version
Current version: 0.16.0
