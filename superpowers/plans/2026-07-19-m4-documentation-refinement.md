# M4 Documentation Refinement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite the docs so the tutorial verifiably matches `examples/bootstrap5/library/`, every shipped feature has a reference page, the index teaser sells, and drift is CI-gated.

**Architecture:** Three phases, one PR each. Phase 1: a `cv-sync` pytest that pins marked docs code blocks to example source, a Playwright screenshot script, and a six-part tutorial series replacing `tutorial.md`/`tutorial2.md`. Phase 2: reference audit, new `nested.md` + `formsets.md` pages, staleness sweep, grouped `reference/.pages` nav. Phase 3: `index.md` teaser rewrite, FAQ cross-links, final done-when sweep.

**Tech Stack:** mkdocs (readthedocs theme, awesome-pages), pytest (examples suite), Playwright (manual screenshot script only), existing CI (`docs.yml` already gates `mkdocs build --strict`).

**Spec:** `superpowers/specs/2026-07-19-m4-documentation-refinement-design.md`

## Global Constraints

- All work on branch `feature/m4-docs` (already created off `origin/main`, spec committed as `bf1dc5e`). One PR per phase; squash-merge; docs-only, **no version bump**.
- **Worktree venv gotcha:** every `uv`/`task`/`pytest` invocation MUST be prefixed `env -u VIRTUAL_ENV` (inherited VIRTUAL_ENV otherwise targets the main checkout's venv).
- Sync-marker syntax, exactly: `<!-- cv-sync: <path relative to examples/bootstrap5> -->` on its own line immediately before a fenced code block. Marked blocks must exist verbatim (whitespace-normalized, blank lines ignored, contiguous) in the target file. Progressive/simplified blocks stay **unmarked**.
- `mkdocs build --strict` must pass after every task that touches `docs/` (CI gates it in `docs.yml`). Run locally: `env -u VIRTUAL_ENV uv run --with mkdocs --with mkdocs-awesome-pages-plugin mkdocs build --strict`.
- Current API only: `cv_viewset = ...` (never `vs = ...`), imports as in `examples/bootstrap5/library/views.py`. Django doc links use `/en/stable/`, never a pinned version.
- Python files: ruff, 120 chars, double quotes. Run `env -u VIRTUAL_ENV uvx ruff format <file> && env -u VIRTUAL_ENV uvx ruff check --fix <file>` before committing any `.py`.
- Example app URL map (needed for links/screenshots): list `/library/author/`, create `/library/author/create/`, detail `/library/author/<pk>/detail/`, update `.../update/`, delete `.../delete/`; same pattern for `/library/book/` plus `<pk>/up/`, `<pk>/down/`. Demo logins: `admin`/`admin` (superuser), `alice`/`alice`, `bob`/`bob`.
- Commit messages: conventional commits (`docs(...)`, `feat(...)`, `test(...)`).

---

## Phase 1 — Tutorial rewrite (PR 1)

### Task 1: cv-sync check test

**Files:**
- Create: `examples/bootstrap5/test_docs_sync.py`

**Interfaces:**
- Consumes: nothing (self-contained).
- Produces: the CI contract every later docs task relies on — `find_sync_blocks(markdown: str) -> list[tuple[str, str]]`, `significant_lines(text: str) -> list[str]`, `contains_contiguous(haystack: list[str], needle: list[str]) -> bool`, and the parametrized `test_marked_block_matches_source`. Collected automatically by the examples pytest suite (`pytest.ini` has `python_files = test_*.py ...`), which CI runs via the nox `examples` sessions.

- [ ] **Step 1: Write the test module**

````python
"""Docs <-> examples sync check (M4).

A fenced code block in ``docs/`` immediately preceded by a marker comment::

    <!-- cv-sync: library/views.py -->

must appear verbatim (whitespace-normalized, blank lines ignored) as a
contiguous run of lines in the referenced file. Paths are relative to
``examples/bootstrap5/``. Blocks without a marker are exempt -- the tutorial
uses unmarked blocks for progressive intermediate states.
"""

import re
from pathlib import Path

import pytest

EXAMPLES_DIR = Path(__file__).resolve().parent
DOCS_DIR = EXAMPLES_DIR.parents[1] / "docs"

SYNC_BLOCK_RE = re.compile(
    r"<!--\s*cv-sync:\s*(?P<target>\S+)\s*-->\s*```[a-z0-9]*\n(?P<code>.*?)^```",
    re.DOTALL | re.MULTILINE,
)


def find_sync_blocks(markdown: str) -> list[tuple[str, str]]:
    """Return (target, code) tuples for all marked fenced blocks."""
    return [(m["target"], m["code"]) for m in SYNC_BLOCK_RE.finditer(markdown)]


def significant_lines(text: str) -> list[str]:
    """Lines with trailing whitespace stripped, blank lines dropped."""
    return [line.rstrip() for line in text.splitlines() if line.strip()]


def contains_contiguous(haystack: list[str], needle: list[str]) -> bool:
    if not needle:
        return False
    return any(haystack[i : i + len(needle)] == needle for i in range(len(haystack) - len(needle) + 1))


MARKDOWN_FIXTURE = """
Intro text.

<!-- cv-sync: library/views.py -->
```python
cv_author = ViewSet(model=Author, name="author", icon_header="fa-regular fa-user")
```

Unmarked blocks are exempt:

```python
print("scratch")
```
"""


def test_find_sync_blocks_extracts_marked_only():
    blocks = find_sync_blocks(MARKDOWN_FIXTURE)
    assert blocks == [
        ("library/views.py", 'cv_author = ViewSet(model=Author, name="author", icon_header="fa-regular fa-user")\n')
    ]


def test_significant_lines_drops_blanks_and_trailing_ws():
    assert significant_lines("a  \n\n  b\n") == ["a", "  b"]


def test_contains_contiguous():
    haystack = ["a", "b", "c", "d"]
    assert contains_contiguous(haystack, ["b", "c"])
    assert not contains_contiguous(haystack, ["b", "d"])
    assert not contains_contiguous(haystack, [])


def iter_marked_blocks():
    params = []
    for md_file in sorted(DOCS_DIR.rglob("*.md")):
        for target, code in find_sync_blocks(md_file.read_text(encoding="utf-8")):
            rel = md_file.relative_to(DOCS_DIR)
            params.append(pytest.param(md_file, target, code, id=f"{rel}:{target}"))
    return params


@pytest.mark.parametrize("md_file, target, code", iter_marked_blocks())
def test_marked_block_matches_source(md_file, target, code):
    source = EXAMPLES_DIR / target
    assert source.is_file(), f"{md_file}: cv-sync target {target!r} does not exist under examples/bootstrap5/"
    assert contains_contiguous(
        significant_lines(source.read_text(encoding="utf-8")), significant_lines(code)
    ), f"{md_file}: marked block not found contiguously in {target} (whitespace-normalized)"
````

Note: the fixture uses a real line from `library/views.py` so the fixture itself doubles as an end-to-end sanity check of the marker format.

- [ ] **Step 2: Run — unit tests pass, docs scan is skipped/empty (no markers in docs yet)**

Run: `cd examples/bootstrap5 && env -u VIRTUAL_ENV uv run pytest test_docs_sync.py -v`
Expected: 3 PASS (`test_find_sync_blocks...`, `test_significant_lines...`, `test_contains_contiguous`); `test_marked_block_matches_source` collects 0 params (shown as skipped or absent).

- [ ] **Step 3: Prove RED — a wrong marked block must fail**

Create `docs/getting_started/_sync_smoke.md` containing:

````markdown
<!-- cv-sync: library/views.py -->
```python
this_line_is_not_in_the_source = True
```
````

Run: `cd examples/bootstrap5 && env -u VIRTUAL_ENV uv run pytest test_docs_sync.py -v`
Expected: 1 FAIL (`_sync_smoke.md:library/views.py` — "marked block not found").

Then change the block body to exactly `cv_author = ViewSet(model=Author, name="author", icon_header="fa-regular fa-user")`, re-run, expect PASS. Delete `docs/getting_started/_sync_smoke.md`.

- [ ] **Step 4: Format & lint**

Run: `env -u VIRTUAL_ENV uvx ruff format examples/bootstrap5/test_docs_sync.py && env -u VIRTUAL_ENV uvx ruff check --fix examples/bootstrap5/test_docs_sync.py`

- [ ] **Step 5: Commit**

```bash
git add examples/bootstrap5/test_docs_sync.py
git commit -m "test(docs): cv-sync check pins marked docs code blocks to example source"
```

---

### Task 2: Screenshot generation script

**Files:**
- Create: `scripts/generate_screenshots.py`
- Create: `docs/getting_started/assets/tutorial-*.png` (script output)
- Delete: `scripts/generate_mockups.py`, `docs/img/` (both verified unreferenced)

**Interfaces:**
- Consumes: the running example app (`examples/bootstrap5`), demo user `alice`/`alice`.
- Produces: PNGs named `tutorial-<page>.png` in `docs/getting_started/assets/` that Tasks 3–5 embed. Names produced: `tutorial-home.png`, `tutorial-author-list.png`, `tutorial-author-create.png`, `tutorial-author-detail.png`, `tutorial-author-update.png`, `tutorial-author-delete.png`, `tutorial-book-list.png`.

- [ ] **Step 1: Verify the old mockup artifacts are unreferenced**

Run: `grep -rn "img/view_\|generate_mockups" docs mkdocs.yml taskfile.yaml .github --include="*" 2>/dev/null`
Expected: no output. (If a reference exists, keep the referenced artifact and note it in the task report instead of deleting.)

- [ ] **Step 2: Write the script**

```python
"""Regenerate tutorial screenshots from the live example app.

Usage (from the repo root):

    cd examples/bootstrap5
    env -u VIRTUAL_ENV uv run --with playwright playwright install chromium   # once
    env -u VIRTUAL_ENV uv run --with playwright python ../../scripts/generate_screenshots.py

Boots the seeded dev server on a scratch port, logs in as the demo user
``alice`` and captures the tutorial pages into docs/getting_started/assets/.
Re-run whenever the UI changes; commit the PNGs like normal files.
"""

import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

PORT = 8123
BASE = f"http://127.0.0.1:{PORT}"
EXAMPLES_DIR = Path(__file__).resolve().parents[1] / "examples" / "bootstrap5"
ASSETS_DIR = Path(__file__).resolve().parents[1] / "docs" / "getting_started" / "assets"

#: (output name, path) -- pages reachable by direct URL
STATIC_PAGES = [
    ("tutorial-home", "/"),
    ("tutorial-author-list", "/library/author/"),
    ("tutorial-author-create", "/library/author/create/"),
    ("tutorial-book-list", "/library/book/"),
]


def wait_for_server(timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"{BASE}/login/", timeout=1)
            return
        except OSError:
            time.sleep(0.3)
    raise RuntimeError(f"server on {BASE} did not come up")


def main() -> None:
    subprocess.run(["uv", "run", "manage.py", "migrate"], cwd=EXAMPLES_DIR, check=True)
    subprocess.run(["uv", "run", "manage.py", "seed"], cwd=EXAMPLES_DIR, check=True)
    server = subprocess.Popen(
        ["uv", "run", "manage.py", "runserver", f"127.0.0.1:{PORT}", "--noreload"],
        cwd=EXAMPLES_DIR,
    )
    try:
        wait_for_server()
        ASSETS_DIR.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 800})

            page.goto(f"{BASE}/login/")
            page.fill("input[name=username]", "alice")
            page.fill("input[name=password]", "alice")
            page.click("input[type=submit], button[type=submit]")
            page.wait_for_load_state("networkidle")

            for name, path in STATIC_PAGES:
                page.goto(f"{BASE}{path}")
                page.wait_for_load_state("networkidle")
                page.screenshot(path=ASSETS_DIR / f"{name}.png")
                print(f"captured {name}.png  ({path})")

            # object pages: derive the first author's detail URL from the list table
            page.goto(f"{BASE}/library/author/")
            detail_href = page.locator("table tbody a").first.get_attribute("href")
            if not detail_href:
                raise RuntimeError("no detail link found on the author list page")
            for name, path in [
                ("tutorial-author-detail", detail_href),
                ("tutorial-author-update", detail_href.replace("/detail/", "/update/")),
                ("tutorial-author-delete", detail_href.replace("/detail/", "/delete/")),
            ]:
                page.goto(f"{BASE}{path}")
                page.wait_for_load_state("networkidle")
                page.screenshot(path=ASSETS_DIR / f"{name}.png")
                print(f"captured {name}.png  ({path})")

            browser.close()
    finally:
        server.terminate()
        server.wait(timeout=10)


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: Run it and inspect output**

Run (from `examples/bootstrap5/`):
```bash
env -u VIRTUAL_ENV uv run --with playwright playwright install chromium
env -u VIRTUAL_ENV uv run --with playwright python ../../scripts/generate_screenshots.py
```
Expected: 7 "captured ..." lines; 7 new PNGs in `docs/getting_started/assets/`. Open 2–3 PNGs (Read tool) and verify they show real rendered pages with seeded data (Ursula Le Guin etc.), not error pages. If a selector misses (e.g. the login submit button), inspect the rendered HTML and adjust the selector — then re-run until all 7 pages capture correctly.

- [ ] **Step 4: Format, lint, delete old artifacts**

```bash
env -u VIRTUAL_ENV uvx ruff format scripts/generate_screenshots.py
env -u VIRTUAL_ENV uvx ruff check --fix scripts/generate_screenshots.py
git rm scripts/generate_mockups.py
git rm -r docs/img
```
Do NOT delete the old `docs/getting_started/assets/*.png` yet — `tutorial.md`/`tutorial2.md` still reference them until Task 6.

- [ ] **Step 5: Verify docs still build, commit**

Run: `env -u VIRTUAL_ENV uv run --with mkdocs --with mkdocs-awesome-pages-plugin mkdocs build --strict`
Expected: build succeeds.

```bash
git add scripts/generate_screenshots.py docs/getting_started/assets/tutorial-*.png
git commit -m "feat(docs): scripted Playwright screenshots for the tutorial; drop PIL mockups"
```

---

### Task 3: Tutorial parts 1–2 (setup & first ViewSet; the list view)

**Files:**
- Create: `docs/getting_started/tutorial-1-setup.md`
- Create: `docs/getting_started/tutorial-2-list.md`

**Interfaces:**
- Consumes: cv-sync marker convention (Task 1), screenshots (Task 2).
- Produces: pages that Task 6 wires into `.pages` nav under the titles "Part 1 — Setup & first ViewSet" and "Part 2 — The list view". Old `tutorial.md`/`tutorial2.md` stay untouched until Task 6.

**Content rules for all tutorial tasks (3–5):**
- The tutorial narrates building the `library/` app *inside the bundled example project* — "we" build `library/models.py`, `library/views.py`, `library/urls.py` step by step. Code blocks showing **final** code are copied verbatim from those files and carry a `cv-sync` marker. Blocks showing **intermediate** states (a view before its filter is added, a subset of `INSTALLED_APPS`) are unmarked and introduced with wording like "for now" / "we'll extend this in Part N".
- Settings/urls blocks are derived subsets of `project/settings.py` / `project/urls.py` → unmarked, but must use the real values (`CRISPY_TEMPLATE_PACK = "bootstrap5"`, `CRUD_VIEWS_EXTENDS`, etc.).
- Every part ends with an embedded screenshot (`![...](assets/tutorial-....png)`) and a one-line "Next" link to the following part.
- After writing each part: run the sync test and `mkdocs build --strict` (mkdocs warns about pages not in nav — pages get into nav in Task 6, so until then expect and tolerate exactly the "not in nav" INFO, not warnings; if `--strict` fails only because of orphan pages, add the new files to `docs/getting_started/.pages` incrementally in the same task instead).

- [ ] **Step 1: Write `tutorial-1-setup.md`**

Sections and blocks:
1. `# Part 1 — Setup & first ViewSet` — one-paragraph promise: by Part 6 you'll have built the `library/` app of the bundled example project; link to `examples/bootstrap5/` on GitHub. Prereqs: basic Django (link `https://docs.djangoproject.com/en/stable/intro/tutorial01/`).
2. **Install** — unmarked block: `pip install django-crud-views` (core deps already include django-tables2, django-filter, django-crispy-forms, crispy-bootstrap5, django-bootstrap5). Note: Part 6 needs `pip install django-crud-views[ordered]`.
3. **Settings** — unmarked block, derived from `project/settings.py`: add to `INSTALLED_APPS`: `"django.contrib.humanize"`, `"django_bootstrap5"`, `"crispy_forms"`, `"crispy_bootstrap5"`, `"django_tables2"`, `"crud_views.apps.CrudViewsConfig"`, `"library"`; plus `CRISPY_TEMPLATE_PACK = "bootstrap5"`, `CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"`, `CRUD_VIEWS_EXTENDS = "project/crud_views.html"` — with a sentence explaining `CRUD_VIEWS_EXTENDS` points at *your* base template and a link to `../reference/templates.md`; mention the example's base template lives at `examples/bootstrap5/project/templates/project/crud_views.html`.
4. **The model** — marked block `<!-- cv-sync: library/models.py -->` containing the `Author` class exactly as in `library/models.py` (UUID pk through `__str__`, including the `Meta.ordering`). Then `makemigrations library` / `migrate` commands.
5. **The ViewSet** — marked block `<!-- cv-sync: library/views.py -->` with the single line `cv_author = ViewSet(model=Author, name="author", icon_header="fa-regular fa-user")`, preceded by an unmarked import block. Prose: a ViewSet is the registry/URL router for all sibling views of one model; pk type auto-detected (UUID here).
6. **First view + urls** — unmarked simplified list view (progressive):

    ```python
    class AuthorListView(ListViewTableMixin, ListViewPermissionRequired):
        cv_viewset = cv_author
        table_class = AuthorTable  # defined in Part 2
    ```

   and the urls wiring, marked `<!-- cv-sync: library/urls.py -->` reduced form is NOT possible (real file wires both viewsets) — use unmarked `urlpatterns = cv_author.urlpatterns` here; Part 6 shows the final marked version.
7. Screenshot `tutorial-home.png` (the example project home) with a sentence that the bundled example is what the finished result looks like; "Next: Part 2".

- [ ] **Step 2: Write `tutorial-2-list.md`**

Sections and blocks:
1. `# Part 2 — The list view` — what you get for free: sortable table, pagination, permission-gated buttons.
2. **The table** — marked `<!-- cv-sync: library/views.py -->` block: the `AuthorTable` class verbatim (4 columns incl. `UUIDLinkDetailColumn(attrs=Table.ca.ID)`). Prose: `Table` extends django-tables2, `UUIDLinkDetailColumn` renders the pk as a link to the sibling detail view.
3. **The view** — unmarked intermediate (`table_class` only; the filter attributes arrive in Part 5): repeat wording "final version in Part 5".
4. **Permissions note** — `ListViewPermissionRequired` = Django `generic.ListView` + `PermissionRequiredMixin`; list/detail→view, create→add, update→change, delete→delete. Quick way to try it: create a superuser, or run the bundled example (`task run`, login `alice`/`alice`).
5. **Seed some data** — unmarked shell block creating an Author (mirror `seed.py` data, e.g. Ursula Le Guin).
6. Screenshot `tutorial-author-list.png`. "Next: Part 3".

- [ ] **Step 3: Run sync test — the new marked blocks must pass**

Run: `cd examples/bootstrap5 && env -u VIRTUAL_ENV uv run pytest test_docs_sync.py -v`
Expected: PASS, with ≥3 collected `test_marked_block_matches_source` params (Author model, ViewSet line, AuthorTable).

- [ ] **Step 4: mkdocs build**

Run: `env -u VIRTUAL_ENV uv run --with mkdocs --with mkdocs-awesome-pages-plugin mkdocs build --strict`
Expected: success (see content rules above re orphan pages).

- [ ] **Step 5: Commit**

```bash
git add docs/getting_started/tutorial-1-setup.md docs/getting_started/tutorial-2-list.md docs/getting_started/.pages
git commit -m "docs(tutorial): parts 1-2 — setup, first ViewSet, list view (cv-sync marked)"
```

---

### Task 4: Tutorial parts 3–4 (forms; the detail view)

**Files:**
- Create: `docs/getting_started/tutorial-3-forms.md`
- Create: `docs/getting_started/tutorial-4-detail.md`

**Interfaces:**
- Consumes: Task 3 conventions; screenshots `tutorial-author-create/update/delete/detail.png`.
- Produces: pages for Task 6 nav, titles "Part 3 — Create, update, delete" and "Part 4 — The detail view".

- [ ] **Step 1: Write `tutorial-3-forms.md`**

Sections and blocks:
1. `# Part 3 — Create, update, delete`.
2. **The form** — marked `cv-sync: library/views.py`: `AuthorForm` verbatim (CrispyModelForm, `submit_label`, `get_layout_fields` with `Row(Column4(...) ...)`). Prose: crispy layout helpers `Column2/4/6` are Bootstrap grid columns.
3. **Create/Update views** — marked blocks: `AuthorCreateView` and `AuthorUpdateView` verbatim (each includes `BreadcrumbMixin` — one sentence forward-referencing Part 6, "ignore it until then", plus `MessageMixin`/`cv_message` explanation with the `»{object}«` interpolation).
4. **Delete view** — marked block: `AuthorDeleteView` verbatim; explain `CrispyDeleteForm` (confirmation form) and `cv_show_related_objects = True` (shows what cascades).
5. Screenshots: `tutorial-author-create.png`, `tutorial-author-update.png`, `tutorial-author-delete.png` at the matching sections. "Next: Part 4".

- [ ] **Step 2: Write `tutorial-4-detail.md`**

Sections and blocks:
1. `# Part 4 — The detail view` — the modern object-detail app.
2. **Install** — add `"crud_views_object_detail"` to `INSTALLED_APPS` (unmarked; it ships in the same distribution — no extra pip install).
3. **The view** — marked block: `AuthorDetailView` verbatim including the full `cv_property_display` dict and the `book_count` method. Prose: property groups render as cards; a path not found on the model falls back to a view callable (`book_count`); link `../reference/object_detail_view.md` and `../reference/object_detail_configuration.md` for the full options.
4. Screenshot `tutorial-author-detail.png`. "Next: Part 5".

- [ ] **Step 3: Run sync test + mkdocs**

Run both commands as in Task 3 steps 3–4.
Expected: all marked blocks pass (now including AuthorForm, AuthorCreateView, AuthorUpdateView, AuthorDeleteView, AuthorDetailView); build clean.

- [ ] **Step 4: Commit**

```bash
git add docs/getting_started/tutorial-3-forms.md docs/getting_started/tutorial-4-detail.md docs/getting_started/.pages
git commit -m "docs(tutorial): parts 3-4 — crispy forms and object-detail view"
```

---

### Task 5: Tutorial parts 5–6 (filters & permissions; second model & polish)

**Files:**
- Create: `docs/getting_started/tutorial-5-filters-permissions.md`
- Create: `docs/getting_started/tutorial-6-books.md`

**Interfaces:**
- Consumes: Task 3 conventions; screenshots `tutorial-author-list.png`, `tutorial-book-list.png`.
- Produces: pages for Task 6 nav, titles "Part 5 — Filters & permissions" and "Part 6 — A second model: ordering & breadcrumbs".

- [ ] **Step 1: Write `tutorial-5-filters-permissions.md`**

Sections and blocks:
1. `# Part 5 — Filters & permissions`.
2. **The filter** — marked blocks: `AuthorFilter` and `AuthorFilterFormHelper` verbatim. Prose: plain django-filter `FilterSet`; the form helper lays the filter form out with crispy.
3. **The final list view** — marked block: `AuthorListView` verbatim (now with `ListViewTableFilterMixin`, `filterset_class`, `formhelper_class` — and `BreadcrumbMixin`, again forward-referenced to Part 6). This resolves the Part 2 "final version later" promise.
4. **Permissions in practice** — prose + unmarked snippet: the `*PermissionRequired` classes map CRUD→Django perms (table from Part 2 repeated in one line); what a user without `library.add_author` sees (create button hidden, direct URL → 403); how the example grants perms: marked block `<!-- cv-sync: library/seed.py -->` containing the complete `seed()` function verbatim (the `grant_model_perms` loop alone is not contiguous in the source — mark the whole function).
5. Screenshot `tutorial-author-list.png` (filter form visible). "Next: Part 6".

- [ ] **Step 2: Write `tutorial-6-books.md`**

Sections and blocks:
1. `# Part 6 — A second model: ordering & breadcrumbs`.
2. **The model** — `pip install django-crud-views[ordered]`; marked `cv-sync: library/models.py` block: the `Book` class verbatim (OrderedModel, FK to Author).
3. **Views** — marked blocks: `cv_book = ViewSet(...)` line, `BookForm`, `BookTable`, `BookListView` (prose: `cv_list_actions = ["detail", "update", "delete", "up", "down"]` adds the reorder arrows), `BookUpView` + `BookDownView` verbatim. Link `../reference/ordered_view.md`.
4. **Breadcrumbs** — resolve the running `BreadcrumbMixin` mystery: marked block `cv-sync: project/views.py` with the mixin's class definition from `examples/bootstrap5/project/views.py` (read the file; the class subclasses `CrudViewBreadcrumbMixin`), plus the unmarked settings line `CRUD_VIEWS_BREADCRUMB_PREFIX = [{"title": "Home", "url_name": "home"}]`. Link `../reference/breadcrumb.md`.
5. **Final urls** — marked `cv-sync: library/urls.py`: the complete 2-line file verbatim.
6. Screenshot `tutorial-book-list.png` (up/down arrows + breadcrumb trail visible). Closing paragraph: where to go next — reference section, the other 11 example apps, FAQ.

- [ ] **Step 3: Run sync test + mkdocs**

As Task 3 steps 3–4. Expected: all marked blocks pass; build clean.

- [ ] **Step 4: Commit**

```bash
git add docs/getting_started/tutorial-5-filters-permissions.md docs/getting_started/tutorial-6-books.md docs/getting_started/.pages
git commit -m "docs(tutorial): parts 5-6 — filters, permissions, ordered books, breadcrumbs"
```

---

### Task 6: Getting-started index, nav, old tutorial removal — close PR 1

**Files:**
- Modify: `docs/getting_started/index.md` (full rewrite)
- Modify: `docs/getting_started/.pages` (final form)
- Delete: `docs/getting_started/tutorial.md`, `docs/getting_started/tutorial2.md`
- Delete: `docs/getting_started/assets/author.png`, `create.png`, `home.png`, `list-create-author.png`, `list-create.png`, `list.png` (superseded; verify nothing else references them first: `grep -rn "assets/author.png\|assets/create.png\|assets/home.png\|assets/list" docs/`)

**Interfaces:**
- Consumes: all six tutorial pages (Tasks 3–5).
- Produces: the merged Phase-1 PR; Phase 2 starts from updated `main`.

- [ ] **Step 1: Rewrite `docs/getting_started/index.md`**

````markdown
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
````

- [ ] **Step 2: Final `docs/getting_started/.pages`**

```yaml
nav:
    - index.md
    - Part 1 — Setup & first ViewSet: tutorial-1-setup.md
    - Part 2 — The list view: tutorial-2-list.md
    - Part 3 — Create, update, delete: tutorial-3-forms.md
    - Part 4 — The detail view: tutorial-4-detail.md
    - Part 5 — Filters & permissions: tutorial-5-filters-permissions.md
    - Part 6 — Ordering & breadcrumbs: tutorial-6-books.md
```

- [ ] **Step 3: Delete old files, verify, build**

```bash
git rm docs/getting_started/tutorial.md docs/getting_started/tutorial2.md
git rm docs/getting_started/assets/author.png docs/getting_started/assets/create.png docs/getting_started/assets/home.png docs/getting_started/assets/list-create-author.png docs/getting_started/assets/list-create.png docs/getting_started/assets/list.png
grep -rn "tutorial.md\|tutorial2.md" docs/ mkdocs.yml   # fix any dangling links (expect hits only in getting_started/.pages history — none after step 2)
env -u VIRTUAL_ENV uv run --with mkdocs --with mkdocs-awesome-pages-plugin mkdocs build --strict
cd examples/bootstrap5 && env -u VIRTUAL_ENV uv run pytest test_docs_sync.py -v && cd ../..
```
Expected: no dangling links, strict build clean, sync test green.

- [ ] **Step 4: Commit and open PR 1**

```bash
git add -A docs/getting_started
git commit -m "docs(tutorial): replace stale 2-page tutorial with 6-part series synced to library/ example"
git push -u origin feature/m4-docs
gh pr create --title "M4 phase 1: tutorial rewrite with cv-sync CI check and scripted screenshots" --body "Phase 1 of the M4 documentation-refinement spec (superpowers/specs/2026-07-19-m4-documentation-refinement-design.md): cv-sync pytest, Playwright screenshot script, 6-part tutorial replacing tutorial.md/tutorial2.md."
```
Then follow the PR lifecycle (project memory): wait for CI, fix ruff if needed, squash-merge, wait for main CI. After merge: `git fetch origin main && git merge origin/main` (or rebase) so Phase 2 continues on `feature/m4-docs` from updated main.

---

## Phase 2 — Reference audit, gaps & nav (PR 2)

### Task 7: `docs/reference/nested.md`

**Files:**
- Create: `docs/reference/nested.md`
- Modify: `docs/faq.md` (section "How do I link from one child collection to a sibling collection?" — add link to the new page)
- Modify: `docs/reference/.pages` (insert `nested.md` after `custom_form_view.md` for now; Task 10 regroups)

**Interfaces:**
- Consumes: `examples/bootstrap5/nested/` app source (read `models.py`, `views.py`, `urls.py` first — the marked blocks come from there); FAQ section at `docs/faq.md:164`.
- Produces: reference page `nested.md` that Task 10's nav and Task 12's FAQ links point at.

- [ ] **Step 1: Read the nested example app**

Read `examples/bootstrap5/nested/models.py`, `views.py`, `urls.py` fully. Identify: the parent model, the child model, the child ViewSet's `parent=ParentViewSet(name=...)` declaration, and any `CreateViewParentMixin` usage.

- [ ] **Step 2: Write `docs/reference/nested.md`**

Structure (marked blocks all `cv-sync: nested/views.py` or `nested/models.py`, verbatim from what Step 1 found):
1. `# Nested ViewSets (parent/child)` — concept: a child ViewSet declares its parent; URLs nest (`parent_prefix/<parent_pk>/child_prefix/...`); child querysets are automatically filtered to the parent.
2. **Declaring the relationship** — marked block: the child `ViewSet(... parent=ParentViewSet(name="..."), ...)` from the example.
3. **URL structure** — unmarked block showing the generated URL shapes for the example's models.
4. **Creating children** — `CreateViewParentMixin` sets the parent FK automatically; marked block from the example if it uses it, otherwise a short unmarked snippet plus a note.
5. **Navigating between parent and child** — `ChildContextButton` (parent → child) and `ParentViewSet` context (`cv_context_actions = ["parent", ...]`); absorb the FAQ's sibling-collection snippet (`docs/faq.md:164-193`) as a subsection "Linking to a sibling child collection".
6. See also: link the nested example app and `context_buttons.md`.

- [ ] **Step 3: Trim the FAQ section**

In `docs/faq.md` section "How do I link from one child collection to a sibling collection?": keep the question, first paragraph and code block, and append: `Full documentation of parent/child ViewSets: [Nested ViewSets](reference/nested.md).`

- [ ] **Step 4: Verify + commit**

```bash
cd examples/bootstrap5 && env -u VIRTUAL_ENV uv run pytest test_docs_sync.py -v && cd ../..
env -u VIRTUAL_ENV uv run --with mkdocs --with mkdocs-awesome-pages-plugin mkdocs build --strict
git add docs/reference/nested.md docs/reference/.pages docs/faq.md
git commit -m "docs(reference): nested parent/child ViewSets page"
```

---

### Task 8: `docs/reference/formsets.md`

**Files:**
- Create: `docs/reference/formsets.md`
- Modify: `docs/reference/.pages` (insert `formsets.md` before the conditional entry for now)

**Interfaces:**
- Consumes: `examples/bootstrap5/formsets/` app source; `docs/development/stability.md` (read its formsets/internal-API wording first and mirror it); `docs/reference/conditional.md` (links to it).
- Produces: reference page `formsets.md` for Task 10 nav and the conditional page's "formsets" mentions.

- [ ] **Step 1: Read sources**

Read `examples/bootstrap5/formsets/views.py` (and its models/forms), `docs/development/stability.md`, and skim `docs/reference/conditional.md`'s formset section for terminology consistency.

- [ ] **Step 2: Write `docs/reference/formsets.md`**

Structure:
1. `# Formsets` — inline child-object editing on create/update views.
2. **Stability note** (early, one short admonition): the supported surface is what this page documents — the mixin and declaration style used below; formset *internals* are not part of the public API covered by semver (link `../development/stability.md`). Use the stability doc's own wording.
3. **Usage** — marked blocks (`cv-sync: formsets/views.py` etc., verbatim from the example): the form/formset declaration and the view using the formset mixin, exactly as the example app does it.
4. **The AJAX template endpoint** — how empty-form rows are fetched for "add another" (describe behavior; no internals).
5. **Conditional formsets** — one paragraph + link to `conditional.md`.
6. See also: formsets example app link.

- [ ] **Step 3: Verify + commit**

Same verification commands as Task 7 step 4.

```bash
git add docs/reference/formsets.md docs/reference/.pages
git commit -m "docs(reference): formsets page documenting the supported usage surface"
```

---

### Task 9: Reference audit & staleness sweep

**Files:**
- Modify: any `docs/**/*.md` with findings (expected small diffs across several files)
- Create (scratch, not committed): audit inventory in the task report

**Interfaces:**
- Consumes: the 12 example apps as the feature inventory; all 29 reference pages.
- Produces: a clean reference set for Task 10's regrouping; any too-big-to-fix findings filed as GitHub issues.

- [ ] **Step 1: Build the inventory**

Table: rows = example apps (library, nested, formsets, workflow, polymorphic_demo, guardian_demo, resources, showcase, object_detail, conditional, breadcrumbs) + cross-cutting features (cards/`card-list-view`, actions, context buttons, modals, ordered, templates/theming, assets, settings, i18n). Columns: reference page(s), verdict (ok / stale / missing). After Tasks 7–8, `missing` should be empty — if the audit still finds a missing feature, write the page in this task if it fits in ~1 page of content following the Task 7/8 pattern; otherwise file a GitHub issue (`gh issue create`) describing the gap and record the issue number in the report.

- [ ] **Step 2: Mechanical staleness greps — fix every hit**

```bash
grep -rn "vs = vs_\|vs=vs_\|crud_views_plain" docs/
grep -rn "docs.djangoproject.com/en/[0-9]" docs/
grep -rn "boostrap\|font-awsome\|awsome" docs/
grep -rn "examples/shared\|app/views\|app/models" docs/
```
Expected after fixing: all four greps return nothing. Fixes use current API/paths; Django links → `/en/stable/`.

- [ ] **Step 3: Per-page skim**

Open each `docs/reference/*.md` (and `docs/development/*.md`) and check: imports match the current public API surface (compare against `examples/bootstrap5/*/views.py` usage); no references to removed functionality; internal links resolve. Fix in place. This is a correctness pass — do not restyle prose.

- [ ] **Step 4: Verify + commit**

```bash
env -u VIRTUAL_ENV uv run --with mkdocs --with mkdocs-awesome-pages-plugin mkdocs build --strict
cd examples/bootstrap5 && env -u VIRTUAL_ENV uv run pytest test_docs_sync.py -v && cd ../..
git add docs
git commit -m "docs: staleness sweep — current API, stable Django links, no removed-feature mentions"
```

---

### Task 10: Reference nav grouping — close PR 2

**Files:**
- Modify: `docs/reference/.pages` (full rewrite)

**Interfaces:**
- Consumes: `nested.md` (Task 7), `formsets.md` (Task 8); awesome-pages section syntax.
- Produces: the merged Phase-2 PR.

- [ ] **Step 1: Rewrite `docs/reference/.pages`**

```yaml
nav:
    - index.md
    - Core views:
        - list_view.md
        - detail_view.md
        - create_view.md
        - update_view.md
        - delete_view.md
        - custom_form_view.md
        - nested.md
    - Object detail:
        - object_detail_view.md
        - object_detail_configuration.md
        - object_detail_field_types.md
        - object_detail_links.md
        - object_detail_badges.md
        - object_detail_layout_packs.md
        - object_detail_settings.md
    - Lists & tables:
        - card-list-view.md
        - ordered_view.md
    - Forms & formsets:
        - formsets.md
        - Conditional groups & formsets: conditional.md
    - Actions & navigation:
        - action_enabled.md
        - action_view.md
        - context_buttons.md
        - breadcrumb.md
        - modals.md
    - Extensions:
        - workflow_view.md
        - polymorphic_view.md
        - guardian.md
        - resources.md
    - Theming:
        - templates.md
        - theme.md
        - assets.md
    - settings.md
```

- [ ] **Step 2: Build and eyeball the nav**

Run: `env -u VIRTUAL_ENV uv run --with mkdocs --with mkdocs-awesome-pages-plugin mkdocs build --strict`
Expected: clean. Then `env -u VIRTUAL_ENV uv run --with mkdocs --with mkdocs-awesome-pages-plugin mkdocs serve -a localhost:8001` briefly (or inspect `site/` output) to confirm the section grouping renders in the readthedocs theme sidebar and every page is reachable. If the readthedocs theme renders the nested sections poorly (it collapses to two levels), fall back to flat ordering in the same sequence with the group names as comment lines, and note the fallback in the report.

- [ ] **Step 3: Commit and open PR 2**

```bash
git add docs/reference/.pages
git commit -m "docs(reference): group nav — core views, object detail, forms, extensions, theming"
git push
gh pr create --title "M4 phase 2: reference audit, nested + formsets pages, grouped nav" --body "Phase 2 of the M4 spec: new nested.md and formsets.md reference pages, staleness sweep (current API, /en/stable/ links), grouped reference nav."
```
PR lifecycle as in Task 6, then sync the branch with main again.

---

## Phase 3 — Teaser, FAQ cross-links & final sweep (PR 3)

### Task 11: `docs/index.md` teaser rewrite

**Files:**
- Modify: `docs/index.md` (full rewrite except the API-stability, "What it is not" and Version sections)

**Interfaces:**
- Consumes: README.md's teaser voice; cv-sync marker (marked blocks from `library/`).
- Produces: the docs landing page; Task 13 verifies it against the milestone done-when.

- [ ] **Step 1: Rewrite `docs/index.md`**

````markdown
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
````

Keep the existing "## API stability", "## What it is not" and "# Version" sections verbatim below this (Version stays last — bump-my-version rewrites it).

Adjust the two marked view/urls blocks to the *exact* current content of `library/views.py` / `library/urls.py` (verify with the sync test — if `AuthorListView` gained or lost a line since this plan was written, the docs block follows the source, not this plan).

- [ ] **Step 2: Verify + commit**

```bash
cd examples/bootstrap5 && env -u VIRTUAL_ENV uv run pytest test_docs_sync.py -v && cd ../..
env -u VIRTUAL_ENV uv run --with mkdocs --with mkdocs-awesome-pages-plugin mkdocs build --strict
git add docs/index.md
git commit -m "docs(index): teaser rewrite sharing the README voice, cv-sync-marked code sample"
```

---

### Task 12: FAQ ↔ examples cross-links

**Files:**
- Modify: `docs/faq.md`

**Interfaces:**
- Consumes: FAQ sections (headings as of planning: context-button templating `:3`, manual context-button rendering `:76`, sibling child collections `:164` — already linked in Task 7, breadcrumb last-item `:195`, breadcrumb host-nav hook `:202`, conditional required-checkbox `:211`); reference pages and example apps.
- Produces: FAQ with "see it running / full docs" pointers; Task 13 verifies.

- [ ] **Step 1: Add cross-links per section**

For each FAQ section append one short italic line — *See it running: [`examples/bootstrap5/<app>/`](<github tree link>) · Full docs: [<Page>](reference/<page>.md)* — using this mapping (verify each app actually demonstrates the topic by skimming its `views.py` before linking; adjust if not):

| FAQ section | Reference page | Example app |
|---|---|---|
| How to template context buttons | `reference/context_buttons.md` | `showcase/` |
| Render a context button manually | `reference/context_buttons.md` | `showcase/` |
| Sibling child collections | `reference/nested.md` (done in Task 7) | `nested/` |
| Why is the last breadcrumb item not a link | `reference/breadcrumb.md` | `breadcrumbs/` |
| Hook breadcrumb into site navigation | `reference/breadcrumb.md` | `breadcrumbs/` |
| Group of fields required when checkbox on | `reference/conditional.md` | `conditional/` |

Where a section's answer merely duplicates reference-page content at length, trim to the short answer + the links (expected candidate: the manual context-button rendering section if `context_buttons.md` covers it — check before trimming; if reference doesn't cover it, leave the FAQ full and instead ensure `context_buttons.md` links to the FAQ).

- [ ] **Step 2: Verify + commit**

```bash
env -u VIRTUAL_ENV uv run --with mkdocs --with mkdocs-awesome-pages-plugin mkdocs build --strict
git add docs/faq.md
git commit -m "docs(faq): cross-link answers to example apps and reference pages"
```

---

### Task 13: Final sweep, milestone update — close PR 3

**Files:**
- Modify: `superpowers/notes/2026-07-16-release-1-milestone.md` (M4 status)
- Modify: any file the sweep flags

**Interfaces:**
- Consumes: everything above; the milestone's done-when list.
- Produces: M4 complete.

- [ ] **Step 1: Run the full done-when verification**

```bash
# no removed functionality / dead API anywhere in docs
grep -rn "crud_views_plain\|vs = vs_\|vs=vs_" docs/            # expect: nothing
grep -rn "docs.djangoproject.com/en/[0-9]" docs/               # expect: nothing
# tutorial matches library/ exactly (marked blocks) + docs build
cd examples/bootstrap5 && env -u VIRTUAL_ENV uv run pytest test_docs_sync.py -v && cd ../..
env -u VIRTUAL_ENV uv run --with mkdocs --with mkdocs-awesome-pages-plugin mkdocs build --strict
# full example suite still green
cd examples/bootstrap5 && env -u VIRTUAL_ENV uv run pytest && cd ../..
```
Check each milestone done-when bullet explicitly: new teaser on index ✓ (Task 11), tutorial matches `library/` ✓ (sync test), nav deliberate ✓ (Tasks 6+10), every feature has a reference page ✓ (Tasks 7–9 inventory), no removed-functionality mentions ✓ (greps). Fix anything that fails before proceeding.

- [ ] **Step 2: Update the milestone document**

In `superpowers/notes/2026-07-16-release-1-milestone.md`: table row M4 → `M4 | Documentation refinement | — ✅ DONE | ...`, and prepend a short **Shipped:** paragraph to the M4 section (mirroring the M2/M3 pattern: what shipped, PR numbers, date).

- [ ] **Step 3: Commit and open PR 3**

```bash
git add superpowers/notes/2026-07-16-release-1-milestone.md docs
git commit -m "docs: M4 final sweep; mark milestone M4 done"
git push
gh pr create --title "M4 phase 3: index teaser, FAQ cross-links, final sweep" --body "Phase 3 (final) of the M4 spec: index.md teaser with cv-sync-marked sample, FAQ cross-links to example apps and reference pages, done-when verification, milestone status update."
```
PR lifecycle as in Task 6. After the squash-merge of PR 3 and green main CI, M4 is complete.
