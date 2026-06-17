# README improvement — design

**Date:** 2026-06-17
**Status:** approved (pending user review of this spec)

## Goal

Rewrite `README.md` as a benefit-first landing page for Django developers. The
current README opens with generic prose and then dumps a long, jargon-heavy
feature list (`CrudView`, `ViewSet`, "sibling views") and a full dependency list
before the reader sees what they get or what their code looks like. The new
README leads with the pain it removes, proves the claim with one short snippet,
and pushes exhaustive detail to the docs.

## Audience & positioning

- **Audience:** Django developers who hand-write repetitive class-based CRUD
  views and `urls.py` wiring for every model.
- **Lead hook:** *less boilerplate*. First 2–3 lines name that pain and the
  payoff — define a model, register a ViewSet, get the screens, URLs, and
  cross-links for free, using your own templates and permissions.

## Section structure (top to bottom)

1. **Title + badges** — unchanged (tests, lint, coverage, PyPI, license, docs).
2. **Hook** — 2–3 lines on the boilerplate pain and the payoff.
3. **"This is all you write" snippet** — one compact `ViewSet` + five one-line
   `CrudView` classes, plus the one-line URL wiring, then a single sentence
   describing what was generated.
4. **Why developers use it** — ~5 benefit-framed bullets (replaces the old
   mixed feature list):
   - **Skip the CRUD boilerplate** — one ViewSet replaces a pile of
     near-identical CBVs and `urls.py` entries.
   - **Views that know their siblings** — automatic cross-linking that respects
     Django's permission system; no hand-written `reverse()` wiring.
   - **Your app, your control** — your templates, URLs and permissions; not
     locked inside `/admin`.
   - **Batteries included** — sortable/filterable/paginated tables, crispy
     forms, per-object permissions, all integrated.
   - **Grows with you** — nested parent/child URLs from ForeignKeys, plus
     optional workflow (FSM) and polymorphic support; Django system checks fail
     fast on misconfiguration.
5. **Built on** — one line crediting the integrated packages, each name
   hyperlinked to **its own hosted documentation** (e.g. django-tables2 →
   django-tables2.readthedocs.io): django-tables2, django-filter,
   django-crispy-forms, django-polymorphic, django-guardian,
   django-ordered-model, django-object-detail. Reuse the canonical doc URLs the
   current README already links to.
6. **Install** — `pip install django-crud-views`, with a note on extras
   (`[guardian]`, `[ordered]`, `[all]`).
7. **What it is not** — keep the two existing lines.
8. **Docs** — prominent link to the full tutorial/reference
   (https://django-crud-views.readthedocs.io).
9. **Current version** — keep the `Current version: X.Y.Z` line verbatim in
   form.

## Draft snippet (to verify before merge)

```python
# app/views.py
from crud_views.lib.viewset import ViewSet
from crud_views.lib.views import (
    ListViewPermissionRequired,
    DetailViewPermissionRequired,
    CreateViewPermissionRequired,
    UpdateViewPermissionRequired,
    DeleteViewPermissionRequired,
)
from .models import Author

cv_author = ViewSet(model=Author, name="author")

class AuthorList(ListViewPermissionRequired):
    cv_viewset = cv_author

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

> One sentence after the snippet: "You get list, detail, create, update and
> delete pages, every URL wired up, the views cross-linked, and access gated by
> Django's permission system."

## Constraints

- **Keep the `Current version: X.Y.Z` line.** `bump-my-version` rewrites it on
  every release (`[[tool.bumpversion.files]]` for `README.md` searches
  `Current version: {current_version}`). Removing or reformatting it breaks the
  release tooling.
- **Snippet must be copy-paste runnable — hard, blocking requirement.** The
  README must not ship code that doesn't run. The minimal list view may require
  a `table_class`/mixin (the `examples/` always pair `ListView*` with
  `ListViewTableMixin` + a `Table`); determine the true minimal runnable form
  against the codebase and, if a bare list view needs a table, the snippet must
  include it rather than imply it works without. Verify by actually wiring the
  snippet's pattern against the example app before merge.
- **Spec location:** `superpowers/specs/`, never under `docs/` (mkdocs-only).
- Keep `docs/index.md` consistent in spirit, but this change targets
  `README.md` only.

## What gets cut

- The long mixed feature/terminology list.
- The full clickable dependency bullet list (condensed to the one-line "Built
  on" mention; exhaustive detail stays in the docs).
- The generic opening prose paragraphs.

## Out of scope

- Restructuring the docs site.
- Changing `docs/index.md` content (beyond keeping it from contradicting the
  README).
- Any code or API changes.

## Acceptance criteria

- A new reader understands, within the first screen, what the package does and
  why they'd use it.
- The snippet is accurate and runnable.
- The `Current version:` line is preserved so `bump-my-version` still works.
- The "Built on" one-line mention links each package to its project page.
