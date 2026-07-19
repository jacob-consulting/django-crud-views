# Getting started

The tutorial builds a small library application — authors and their books — step by step.
It is the `library/` app of the example project that ships in the repository, so every
code block you see is real, tested code: a CI check verifies the tutorial matches the
example source.

## Follow the tutorial

1. [Part 1 — Setup & first ViewSet](tutorial-1-setup.md)
2. [Part 2 — The list view](tutorial-2-list.md)
3. [Part 3 — Create, update, delete](tutorial-3-forms.md)
4. [Part 4 — The detail view](tutorial-4-detail.md)
5. [Part 5 — Filters & permissions](tutorial-5-filters-permissions.md)
6. [Part 6 — A second model: ordering & breadcrumbs](tutorial-6-books.md)

## Or run the finished result first

The example project contains the tutorial's `library/` app plus one app per feature:

```bash
git clone https://github.com/jacob-consulting/django-crud-views.git
cd django-crud-views
task dev   # create the venv (requires uv and task)
task run   # migrate, seed and serve http://localhost:8000/
```

Log in with `alice` / `alice` and explore.
