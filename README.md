# Django CRUD Views

Managing CRUD (Create, Read, Update, Delete) operations is a common requirement in Django applications. While Django’s
class-based views provide flexibility, implementing CRUD functionality often involves repetitive code.

Django CRUD Views simplifies this process by offering reusable, customizable class-based views that streamline CRUD
operations. This package helps developers write cleaner, more maintainable code while keeping full control over their
views.

This documentation provides everything you need to get started, from installation to advanced customization. Whether
you're building a small project or a large application, Django CRUD Views can help you work more efficiently.

## Features

- a collection of **CrudView**s for the same Django model whereas these views are aware of their sibling views
- such a collection is called a **ViewSet**
- linking to sibling views is easy, respecting Django's permission system
- designed for HTML
- built on top of Django's class-based generic views
- and Django's permission system
- uses these excellent packages:
    - [django-tables2](https://django-tables2.readthedocs.io/en/latest/)
    - [django-filter](https://django-filter.readthedocs.io/en/stable/)
    - [django-crispy-forms](https://django-crispy-forms.readthedocs.io/en/latest/)
    - [django-polymorphic](https://django-polymorphic.readthedocs.io/en/stable/)
    - [django-ordered-model](https://github.com/django-ordered-model/django-ordered-model)
- **ViewSet**s can be nested with deep URLs (multiple levels) if models are related via ForeignKey
- **CrudView**s are predefined for CRUD operations: list, create, update, delete, detail, up/down
- a **ViewSet** generates all urlpatterns for its **CrudView**s
- Themes are pluggable, so you can easily customize the look and feel to your needs, includes themes
    - `plain` no CSS, minimal HTML and JavaScript
    - `bootstrap5` with Bootstrap 5
- Django system checks for configurations to fail early on startup

## What it is not

- a replacement for Django's admin interface
- a complete page building system with navigations and lots of widgets

## Current version
Current version: 0.0.10