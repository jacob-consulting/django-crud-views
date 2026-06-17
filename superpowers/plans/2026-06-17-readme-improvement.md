# README Improvement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `README.md` with a benefit-first landing page that leads with the "less boilerplate" payoff, proves it with one verified-runnable snippet, and links integrated packages to their own hosted docs — without breaking the release tooling.

**Architecture:** Two strands. (1) An empirical runnability gate: a small, isolated pytest determines the *minimal* ViewSet pattern that actually renders (specifically: does `ListViewTableMixin` auto-generate a table when `table_class` is omitted, or is an explicit `Table` required?). The README's snippet is whichever form that test proves works. (2) The README rewrite itself, transcribing the verified snippet and trimming the detail-heavy sections.

**Tech Stack:** Python, Django, django-tables2 (`SingleTableMixin`), pytest + pytest-django, the existing `tests/test1` project (model `Author`, UUID PK), Markdown.

**Spec:** `superpowers/specs/2026-06-17-readme-improvement-design.md`

---

### Task 1: Prove the minimal runnable ViewSet pattern (runnability gate)

This task answers the open question from the spec: can the README's list view omit `table_class` (cleaner snippet, "Variant A"), or must it ship an explicit `Table` ("Variant B")? The test is isolated via `@pytest.mark.urls` so it does not touch the shared `tests/test1/app/urls.py`. It also serves as a permanent regression guard that the documented minimal example keeps rendering.

**Files:**
- Create: `tests/test1/test_readme_snippet.py` (test + its own urlconf + minimal ViewSet)

- [ ] **Step 1: Write the runnability test (Variant A — no explicit Table)**

This mirrors the README's intended "this is all you write" snippet against the existing `Author` model under a unique ViewSet name (`readme`) so it does not collide with the global `author` ViewSet (duplicate names raise `ViewSetError`). It reuses the model-level Django permission granted by the existing `user_author_view` fixture (`view_author`), since crud-views permissions are per-model, not per-ViewSet.

```python
# tests/test1/test_readme_snippet.py
"""Runnability gate for the README "this is all you write" snippet.

Proves the minimal documented ViewSet pattern actually renders. If Variant A
(no explicit ``table_class``) renders, the README uses it; otherwise the README
must ship the explicit ``Table`` of Variant B.
"""
import pytest
from django.urls import path, include

from app.models import Author
from crud_views.lib.viewset import ViewSet
from crud_views.lib.views import (
    ListViewTableMixin,
    ListViewPermissionRequired,
    DetailViewPermissionRequired,
    CreateViewPermissionRequired,
    UpdateViewPermissionRequired,
    DeleteViewPermissionRequired,
)

cv_readme = ViewSet(model=Author, name="readme")


class ReadmeAuthorList(ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_readme


class ReadmeAuthorDetail(DetailViewPermissionRequired):
    cv_viewset = cv_readme


class ReadmeAuthorCreate(CreateViewPermissionRequired):
    cv_viewset = cv_readme
    fields = ["first_name", "last_name"]


class ReadmeAuthorUpdate(UpdateViewPermissionRequired):
    cv_viewset = cv_readme
    fields = ["first_name", "last_name"]


class ReadmeAuthorDelete(DeleteViewPermissionRequired):
    cv_viewset = cv_readme


urlpatterns = [path("", include(cv_readme.urlpatterns))]


@pytest.mark.urls("test_readme_snippet")
@pytest.mark.django_db
def test_readme_minimal_list_renders(client_user_author_view):
    # Author "list" view registers at the ViewSet path "readme/"
    response = client_user_author_view.get("/readme/")
    assert response.status_code == 200
```

- [ ] **Step 2: Run the test to learn the answer**

Run: `cd tests && pytest test1/test_readme_snippet.py::test_readme_minimal_list_renders -v`

Two possible outcomes — record which one happens:
- **PASS** → Variant A works. The README list view is `class AuthorList(ListViewTableMixin, ListViewPermissionRequired): cv_viewset = cv_author` (no `table_class`). Keep the test as-is.
- **FAIL** (e.g. `ImproperlyConfigured`, missing `table`/`get_table_class`, or template error referencing `table`) → Variant A does not work. Proceed to Step 3 to lock Variant B.

- [ ] **Step 3: If Step 2 FAILED, switch the test to Variant B (explicit Table) and re-run**

Add the imports and a small `Table`, and give the list view a `table_class`:

```python
import django_tables2 as tables
from crud_views.lib.table import Table


class ReadmeAuthorTable(Table):
    first_name = tables.Column()
    last_name = tables.Column()


class ReadmeAuthorList(ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_readme
    table_class = ReadmeAuthorTable
```

Run: `cd tests && pytest test1/test_readme_snippet.py::test_readme_minimal_list_renders -v`
Expected: PASS. (If it still fails, the example `examples/plain/app/views/author.py` is the known-good reference — match its list-view construction exactly.)

- [ ] **Step 4: Record the verified snippet**

Whichever variant passed in Step 2/3 is now the **canonical README snippet**. The exact class bodies in the passing test file are the source of truth for Task 2 — Task 2 transcribes them (renamed from `Readme*`/`readme` back to `Author*`/`author`).

- [ ] **Step 5: Commit**

```bash
git add tests/test1/test_readme_snippet.py
git commit -m "test: lock the minimal runnable ViewSet pattern documented in the README"
```

---

### Task 2: Rewrite README.md

**Files:**
- Modify: `README.md` (full rewrite of body; keep badge block and the `Current version:` line)

- [ ] **Step 1: Replace the README body**

Keep lines 1–8 (title + the six badges) exactly as they are. Replace everything from the old intro prose through the end with the content below. **In the `app/views.py` code block, paste the verified snippet from Task 1, Step 4** (shown here as Variant A — if Task 1 proved Variant B, include the `AuthorTable` + `table_class` form instead).

````markdown
**Stop hand-writing the same list, detail, create, update and delete views for every model.**
Define your model, register a `ViewSet`, and Django CRUD Views generates the pages, wires up
every URL, and cross-links the views — using *your* templates and *your* permissions, right
inside your own app.

## This is all you write

```python
# app/views.py
from crud_views.lib.viewset import ViewSet
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


class AuthorList(ListViewTableMixin, ListViewPermissionRequired):
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

You get list, detail, create, update and delete pages, every URL wired up, the views
cross-linked, and access gated by Django's permission system.

## Why developers use it

- **Skip the CRUD boilerplate** — one ViewSet replaces a pile of near-identical class-based views and `urls.py` entries.
- **Views that know their siblings** — automatic cross-linking that respects Django's permissions; no hand-written `reverse()` wiring.
- **Your app, your control** — your templates, URLs and permissions; not locked inside `/admin`.
- **Batteries included** — sortable, filterable, paginated tables, crispy forms and per-object permissions, integrated out of the box.
- **Grows with you** — nested parent/child URLs from ForeignKeys, plus optional workflow (FSM) and polymorphic models; Django system checks catch misconfiguration at startup.

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
Current version: 0.6.0
````

- [ ] **Step 2: Verify the `Current version:` line is intact**

Run: `grep -n "Current version: 0.6.0" README.md`
Expected: exactly one match. This line MUST remain verbatim — `bump-my-version` rewrites it on every release (`[[tool.bumpversion.files]]` searches `Current version: {current_version}` in `README.md`). If it is missing or reformatted, the release tooling breaks.

- [ ] **Step 3: Verify the snippet matches the proven test code**

Open `tests/test1/test_readme_snippet.py` and confirm the README's `app/views.py` block is the same construction (same mixins/classes; `table_class` present iff Task 1 needed Variant B). The only differences should be the `Readme`→`Author` / `readme`→`author` renames and the import of `Author` from `.models`.

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: rewrite README as a benefit-first landing page"
```

---

### Task 3: Final verification

**Files:** none modified (verification only)

- [ ] **Step 1: Confirm the full test suite still passes**

Run: `cd tests && pytest -q`
Expected: all pass, including `test1/test_readme_snippet.py`.

- [ ] **Step 2: Check every "Built on" link resolves**

Run:
```bash
grep -oE 'https?://[^)]+' README.md
```
Expected: the seven package URLs plus the docs URL. Manually confirm each points to that package's own hosted documentation (readthedocs / project site), matching the URLs the previous README used.

- [ ] **Step 3: Render-check the Markdown**

Open `README.md` in a Markdown previewer (or push the branch and view on GitHub). Confirm: badges render, both code blocks are fenced correctly, the bullet list renders, and there are no stray fences from the rewrite.

- [ ] **Step 4: Confirm `docs/index.md` does not contradict the new README**

The README and `docs/index.md` share heritage. This change targets `README.md` only, but read `docs/index.md` to ensure it does not now contradict the README (e.g. claims removed here that are wrong elsewhere). If a contradiction exists, note it for a follow-up — do **not** expand scope into a docs rewrite here.

---

## Self-Review notes

- **Spec coverage:** hook (Task 2 Step 1), verified-runnable snippet (Task 1 → Task 2), ~5 benefit bullets (Task 2), "Built on" line linking to each package's own hosted docs (Task 2 + Task 3 Step 2), Install with extras (Task 2), "What it is not" kept (Task 2), docs link (Task 2), `Current version:` preserved (Task 2 Step 2 + constraint). All covered.
- **Runnability gate:** Task 1 is the hard gate; the README snippet is never written from assumption — it is transcribed from passing test code.
- **No placeholders:** the one conditional (Variant A vs B) is fully specified with concrete code for both branches and a deterministic test to choose between them.
