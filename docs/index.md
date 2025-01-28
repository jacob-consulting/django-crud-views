# Django CRUD Views - An app for creating CRUD views

Features:

- a ViewSet is a collection of CRUD-Views for the same Django model the Views are aware of their siblings
- designed for HTML
- built on top of Django's class-based generic views
- and Django's permission system
- uses these excellent packages:
    - [django-tables2](https://django-tables2.readthedocs.io/en/latest/)
    - [django-filter](https://django-filter.readthedocs.io/en/stable/)
    - [django-crispy-forms](https://django-crispy-forms.readthedocs.io/en/latest/)
    - [django-polymorphic](https://django-polymorphic.readthedocs.io/en/stable/)
    - [django-ordered-model](https://github.com/django-ordered-model/django-ordered-model)
- ViewSets can be nested with deep URLs (multiple levels) if models are related via ForeignKey
- includes basic ic CRUD operations: list, create, update, delete, detail, up/down 
- a ViewSet generates all urlpatterns for its Views
- Themes are pluggable, so you can easily customize the look and feel to your needs, includes themes
    - `plain` no CSS, minimal HTML and JavaScript
    - `bootstrap5` with Bootstrap 5
- Django system checks to fail early on startup

What it is not:

- a replacement for Django's admin interface
- a complete page building system with navigations and lots of widgets

# Version
Current version: 0.0.1
