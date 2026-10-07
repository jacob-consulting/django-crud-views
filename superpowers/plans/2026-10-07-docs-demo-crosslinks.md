# Docs ↔ Live-Demo Cross-Links Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Every example app in the live demo lists the documentation sections that explain it, and every one of
those documentation pages links back to the example in the live demo. Tests keep both directions in sync.

**Architecture:** A `DocRef` dataclass and a `Feature.docs` tuple in the examples' feature registry are the single
source of truth. The existing `snippet_panels` inclusion tag renders them under a new translated heading. On the
docs side, each referenced mkdocs page gets a hand-written `!!! example` admonition linking to the app's demo
landing page. A new examples test module checks that every reference resolves to an existing page and heading
anchor, and that every referenced page links back.

**Tech Stack:** Django 4.2–6.0 templates + i18n (gettext), pytest / pytest-django, mkdocs (readthedocs theme) with
Python-Markdown's `admonition` extension.

**Spec:** `superpowers/specs/2026-10-07-docs-demo-crosslinks-design.md`

## Global Constraints

- Docs links from the demo use `DOCS_BASE = "https://django-crud-views.readthedocs.io/en/stable"`.
- Demo links in the docs use `DEMO_BASE = "https://django-crud-views-demo.onrender.com"` + `reverse(feature.url_name)`
  (app landing pages only, never detail/edit pages).
- Section heading text: `References to documentation` (en) / `Verweise auf die Dokumentation` (de).
- `DocRef.label` is English and NOT wrapped in `gettext` (like `Feature.title` / `look_at`).
- Doc URLs follow mkdocs `use_directory_urls`: `x/y.md` → `x/y/`, `x/index.md` → `x/`.
- No new dependencies. The `examples` nox session installs `.[all,test,examples]` + `requirements/demo.txt`, which
  does NOT include `markdown`, so slugify is a local copy.
- No changes under `src/`.
- Line length 120, double quotes, `ruff format` + `ruff check` clean.
- Run all examples tests from `examples/bootstrap5/` (its `pytest.ini` sets `DJANGO_SETTINGS_MODULE=project.settings`).
- Never commit a zero-byte or stale `django.mo`.

## Review Focus

- **Non-feature pages (home, login)** must not show a "References to documentation" heading. Pinned in Task 3
  (`test_docs_empty_for_non_feature_view`, `test_home_has_no_doc_refs_heading`).
- **A feature with `docs=()`** renders no heading and no empty `<ul>`. Pinned in Task 3
  (`test_no_heading_when_docs_empty`).
- **German UI**: the heading is translated, labels stay English, and links still point at `/en/stable/`. Pinned
  in Task 3 (`test_heading_translated_de_labels_stay_english`).
- **A docs page shared by two apps** (`reference/object_detail_view.md`: Object Detail and Showcase) must link
  to both demos. **A page referenced twice by one app** (nested, list_view) is checked once. Pinned in Task 4 by
  the per-(feature, distinct page) parametrization of `test_docs_page_links_back_to_demo`.
- **`#` lines inside fenced code** (`# urls.py` in `workflow_view.md`, Python comments) must not count as
  headings, or a bogus anchor could pass the integrity check. Pinned in Task 2 (`test_heading_slugs_ignore_fenced_code`).

---

## File Structure

| File | Change | Responsibility |
|---|---|---|
| `examples/bootstrap5/project/features.py` | modify | `DOCS_BASE`, `DocRef`, `Feature.docs`, the per-app mapping |
| `examples/bootstrap5/project/templatetags/example_tags.py` | modify | `snippet_panels` also returns `docs` |
| `examples/bootstrap5/project/templates/project/snippet_panels.html` | modify | render the references section |
| `examples/bootstrap5/locale/de/LC_MESSAGES/django.po` / `.mo` | modify | German heading |
| `examples/bootstrap5/test_doc_links.py` | create | slugify copy, heading extraction, integrity + backlink tests |
| `examples/bootstrap5/project/tests.py` | modify | `DocRef.url` unit tests, rendering + i18n tests |
| `mkdocs.yml` | modify | enable `admonition` |
| `docs/getting_started/index.md`, 17 × `docs/reference/*.md` | modify | "Try it live" boxes |
| `CHANGELOG.md` | modify | Unreleased → Added entry |

---

### Task 1: `DocRef` data model and URL builder

**Files:**
- Modify: `examples/bootstrap5/project/features.py:1-17`
- Test: `examples/bootstrap5/project/tests.py` (append a new class)

**Interfaces:**
- Produces: `project.features.DOCS_BASE: str`; `project.features.DocRef(page: str, label: str, anchor: str = "")`,
  frozen dataclass with `url -> str` property; `Feature.docs: tuple[DocRef, ...] = ()` (last field, after `badge`).

- [ ] **Step 1: Write the failing test**

Append to `examples/bootstrap5/project/tests.py`:

```python
class DocRefTest(SimpleTestCase):
    def test_url_plain_page(self):
        from project.features import DOCS_BASE, DocRef

        ref = DocRef(page="reference/nested.md", label="Nested")
        self.assertEqual(ref.url, f"{DOCS_BASE}/reference/nested/")

    def test_url_with_anchor(self):
        from project.features import DOCS_BASE, DocRef

        ref = DocRef(page="reference/nested.md", label="Nested", anchor="creating-children")
        self.assertEqual(ref.url, f"{DOCS_BASE}/reference/nested/#creating-children")

    def test_url_index_pages(self):
        from project.features import DOCS_BASE, DocRef

        self.assertEqual(DocRef(page="getting_started/index.md", label="x").url, f"{DOCS_BASE}/getting_started/")
        self.assertEqual(DocRef(page="index.md", label="x").url, f"{DOCS_BASE}/")

    def test_docs_base_is_stable(self):
        from project.features import DOCS_BASE

        self.assertEqual(DOCS_BASE, "https://django-crud-views.readthedocs.io/en/stable")

    def test_feature_docs_defaults_to_empty_tuple(self):
        from project.features import Feature

        feature = Feature(
            app="x", title="X", description="d", about="a", look_at="l", url_name="home", icon="fa-solid fa-x"
        )
        self.assertEqual(feature.docs, ())
```

Change the import at the top of the file from `from django.test import TestCase, override_settings` to:

```python
from django.test import SimpleTestCase, TestCase, override_settings
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd examples/bootstrap5 && pytest project/tests.py::DocRefTest -v`
Expected: FAIL with `ImportError: cannot import name 'DOCS_BASE' from 'project.features'`. `test_feature_docs_defaults_to_empty_tuple` fails with `AttributeError: 'Feature' object has no attribute 'docs'`.

- [ ] **Step 3: Write minimal implementation**

In `examples/bootstrap5/project/features.py`, insert between the imports and `@dataclass(frozen=True) class Feature`:

```python
#: Read the Docs version linked from the demo. "stable" is the newest release tag, which is what the demo runs.
DOCS_BASE = "https://django-crud-views.readthedocs.io/en/stable"


@dataclass(frozen=True)
class DocRef:
    page: str  # path under docs/, e.g. "reference/nested.md"
    label: str  # English link text, deliberately not translated (like Feature.title / look_at)
    anchor: str = ""  # heading slug on that page, e.g. "creating-children"

    @property
    def url(self) -> str:
        """Read the Docs URL, following mkdocs' use_directory_urls: x/y.md -> x/y/, x/index.md -> x/."""
        path = self.page.removesuffix(".md")
        if path == "index" or path.endswith("/index"):
            path = path.removesuffix("index")
        else:
            path += "/"
        url = f"{DOCS_BASE}/{path}"
        return f"{url}#{self.anchor}" if self.anchor else url
```

Add as the last field of `Feature`, after `badge`:

```python
    docs: tuple[DocRef, ...] = ()  # documentation sections listed under "References to documentation"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd examples/bootstrap5 && pytest project/tests.py::DocRefTest -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add examples/bootstrap5/project/features.py examples/bootstrap5/project/tests.py
git commit -m "feat(examples): DocRef model for documentation references"
```

---

### Task 2: Slugify helper, integrity test, and the per-app mapping

**Files:**
- Create: `examples/bootstrap5/test_doc_links.py`
- Modify: `examples/bootstrap5/project/features.py` (add `docs=(...)` to each of the 11 `Feature(...)` entries)

**Interfaces:**
- Consumes: `DocRef`, `Feature.docs`, `FEATURES` from Task 1.
- Produces (in `test_doc_links.py`, reused by Task 4): `EXAMPLES_DIR`, `DOCS_DIR`, `slugify(value: str) -> str`,
  `heading_slugs(markdown: str) -> set[str]`.

- [ ] **Step 1: Write the failing tests**

Create `examples/bootstrap5/test_doc_links.py`:

```python
"""Examples <-> docs cross-link checks.

Each ``Feature.docs`` entry (project/features.py) must point at an existing ``docs/`` page and, if it has an
anchor, at a real heading on that page. Each referenced page must link back to the feature's live-demo landing
page. Checked against the repo's ``docs/``, not the published site: the demo links to Read the Docs ``stable``,
so anchors added on main only resolve online after the next release.
"""

import re
import unicodedata
from pathlib import Path

import pytest

from project.features import FEATURES

EXAMPLES_DIR = Path(__file__).resolve().parent
DOCS_DIR = EXAMPLES_DIR.parents[1] / "docs"

HEADING_RE = re.compile(r"^#{1,6}\s+(?P<text>.+?)\s*#*\s*$")


def slugify(value: str, separator: str = "-") -> str:
    """Copy of Python-Markdown's ``markdown.extensions.toc.slugify`` -- the mkdocs default anchor algorithm.

    Copied rather than imported: ``markdown`` is not installed in the ``examples`` nox session.
    """
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    return re.sub(rf"[{separator}\s]+", separator, value)


def heading_slugs(markdown: str) -> set[str]:
    """Anchor slugs of all ATX headings, skipping lines inside fenced code blocks."""
    slugs, in_fence = set(), False
    for line in markdown.splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        if not in_fence and (m := HEADING_RE.match(line)):
            slugs.add(slugify(m["text"]))
    return slugs


@pytest.mark.parametrize(
    "heading, slug",
    [
        ("Down: table links and `ChildContextButton`", "down-table-links-and-childcontextbutton"),
        ("`polymorphic_forms`", "polymorphic_forms"),
        ("Kind 1 — Conditional field-group in a form", "kind-1-conditional-field-group-in-a-form"),
        ("The `cv_property_display` DSL", "the-cv_property_display-dsl"),
        ("Signed choices (single combo, no buttons)", "signed-choices-single-combo-no-buttons"),
    ],
)
def test_slugify_matches_mkdocs(heading, slug):
    assert slugify(heading) == slug


def test_heading_slugs_ignore_fenced_code():
    markdown = "# Title\n\n## Real heading\n\n```python\n# urls.py\n## not a heading\n```\n\n### After fence\n"
    assert heading_slugs(markdown) == {"title", "real-heading", "after-fence"}


def test_every_feature_declares_doc_refs():
    for feature in FEATURES:
        assert feature.docs, f"{feature.app} has no documentation references"


def iter_doc_refs():
    return [
        pytest.param(feature, ref, id=f"{feature.app}:{ref.page}#{ref.anchor}")
        for feature in FEATURES
        for ref in feature.docs
    ]


@pytest.mark.parametrize("feature, ref", iter_doc_refs())
def test_doc_ref_resolves(feature, ref):
    page = DOCS_DIR / ref.page
    assert page.is_file(), f"{feature.app}: docs page {ref.page!r} does not exist under docs/"
    if ref.anchor:
        slugs = heading_slugs(page.read_text(encoding="utf-8"))
        assert ref.anchor in slugs, f"{feature.app}: no heading with anchor #{ref.anchor} in {ref.page}"
```

- [ ] **Step 2: Run tests to verify the right ones fail**

Run: `cd examples/bootstrap5 && pytest test_doc_links.py -v`
Expected: the slugify and fence tests PASS (they pin the copied algorithm). `test_every_feature_declares_doc_refs` FAILS with `library has no documentation references`. `test_doc_ref_resolves` collects 0 items.

- [ ] **Step 3: Add the mapping**

In `examples/bootstrap5/project/features.py`, add a `docs=(...)` keyword as the last argument of each `Feature(...)`, matched by `app`:

`app="library"`:
```python
        docs=(
            DocRef(page="getting_started/index.md", label="Getting started — the tutorial builds this app"),
            DocRef(
                page="reference/list_view.md",
                label="ListView — table with django-tables2",
                anchor="table-with-django-tables2",
            ),
            DocRef(
                page="reference/list_view.md",
                label="ListView — filtering with django-filter",
                anchor="filtering-with-django-filter",
            ),
            DocRef(page="reference/ordered_view.md", label="OrderedView — manual up/down ordering"),
        ),
```

`app="nested"`:
```python
        docs=(
            DocRef(page="reference/nested.md", label="Nested ViewSets (parent/child)"),
            DocRef(page="reference/nested.md", label="Nested ViewSets — creating children", anchor="creating-children"),
        ),
```

`app="formsets"`:
```python
        docs=(DocRef(page="reference/formsets.md", label="Formsets"),),
```

`app="workflow"`:
```python
        docs=(
            DocRef(page="reference/workflow_view.md", label="WorkflowView"),
            DocRef(
                page="reference/workflow_view.md",
                label="WorkflowView — WorkflowModelMixin (audit history)",
                anchor="workflowmodelmixin",
            ),
        ),
```

`app="polymorphic_demo"`:
```python
        docs=(
            DocRef(
                page="reference/polymorphic_view.md",
                label="PolymorphicView — two-step create flow",
                anchor="two-step-create-flow",
            ),
            DocRef(
                page="reference/polymorphic_view.md",
                label="PolymorphicView — polymorphic_forms",
                anchor="polymorphic_forms",
            ),
        ),
```

`app="guardian_demo"`:
```python
        docs=(
            DocRef(page="reference/guardian.md", label="Per-object permissions (django-guardian)"),
            DocRef(
                page="reference/guardian.md",
                label="Guardian — working example and seeded permissions",
                anchor="working-example",
            ),
        ),
```

`app="resources"`:
```python
        docs=(DocRef(page="reference/resources.md", label="Resources — non-ORM data in ViewSets"),),
```

`app="showcase"`:
```python
        docs=(
            DocRef(
                page="reference/card-list-view.md",
                label="CardListView — signed ordering choices",
                anchor="signed-choices-single-combo-no-buttons",
            ),
            DocRef(
                page="reference/object_detail_view.md",
                label="ObjectDetailView — the cv_property_display DSL",
                anchor="the-cv_property_display-dsl",
            ),
            DocRef(page="reference/modals.md", label="Modals"),
            DocRef(page="reference/action_view.md", label="ActionView — custom actions"),
        ),
```

`app="object_detail"`:
```python
        docs=(
            DocRef(page="reference/object_detail_view.md", label="ObjectDetailView"),
            DocRef(page="reference/object_detail_layout_packs.md", label="Object detail — layout packs"),
            DocRef(page="reference/object_detail_badges.md", label="Object detail — badges"),
            DocRef(page="reference/object_detail_links.md", label="Object detail — links"),
        ),
```

`app="breadcrumbs"`:
```python
        docs=(
            DocRef(page="reference/breadcrumb.md", label="Breadcrumb"),
            DocRef(
                page="reference/breadcrumb.md",
                label="Breadcrumb — hooking into your site navigation",
                anchor="hooking-into-your-site-navigation",
            ),
        ),
```

`app="conditional"`:
```python
        docs=(
            DocRef(
                page="reference/conditional.md",
                label="Conditional field-groups",
                anchor="kind-1-conditional-field-group-in-a-form",
            ),
            DocRef(
                page="reference/conditional.md",
                label="Conditional formsets",
                anchor="kind-2-conditional-formset",
            ),
        ),
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd examples/bootstrap5 && pytest test_doc_links.py -v`
Expected: all pass. `test_doc_ref_resolves` collects 26 items (4+2+1+2+2+2+1+4+4+2+2).

Then prove the integrity check actually bites: temporarily change `anchor="creating-children"` to
`anchor="creating-childrenX"` and re-run. Expected: exactly one FAIL, `no heading with anchor #creating-childrenX in reference/nested.md`. Revert.

- [ ] **Step 5: Lint and commit**

```bash
ruff format examples/bootstrap5 && ruff check examples/bootstrap5
git add examples/bootstrap5/test_doc_links.py examples/bootstrap5/project/features.py
git commit -m "feat(examples): map each example app to its documentation sections"
```

---

### Task 3: Render "References to documentation" (en + de)

**Files:**
- Modify: `examples/bootstrap5/project/templatetags/example_tags.py:44-62` (`snippet_panels`)
- Modify: `examples/bootstrap5/project/templates/project/snippet_panels.html`
- Modify: `examples/bootstrap5/locale/de/LC_MESSAGES/django.po`, `django.mo`
- Test: `examples/bootstrap5/project/tests.py` (append a new class)

**Interfaces:**
- Consumes: `Feature.docs`, `DocRef.url`, `DocRef.label` (Tasks 1–2).
- Produces: `snippet_panels(context)` returns `{"panels": [...], "look_at": str, "docs": tuple[DocRef, ...]}`.

- [ ] **Step 1: Write the failing tests**

Append to `examples/bootstrap5/project/tests.py`:

```python
class DocRefsPanelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser(username="docs-admin", password="pw")

    def setUp(self):
        self.client.force_login(self.admin)

    def test_every_feature_page_lists_its_doc_refs(self):
        from django.utils.html import escape

        for feature in FEATURES:
            with self.subTest(app=feature.app):
                resp = self.client.get(reverse(feature.url_name))
                self.assertContains(resp, "References to documentation")
                for ref in feature.docs:
                    self.assertContains(resp, f'<a href="{ref.url}" target="_blank" rel="noopener">')
                    self.assertContains(resp, escape(ref.label))

    def test_heading_translated_de_labels_stay_english(self):
        from django.utils.html import escape

        feature = next(f for f in FEATURES if f.app == "nested")
        resp = self.client.get(reverse(feature.url_name), HTTP_ACCEPT_LANGUAGE="de")
        self.assertContains(resp, "Verweise auf die Dokumentation")
        self.assertNotContains(resp, "References to documentation")
        self.assertContains(resp, escape(feature.docs[1].label))
        self.assertContains(resp, f'href="{feature.docs[1].url}"')

    def test_docs_empty_for_non_feature_view(self):
        from project.templatetags.example_tags import snippet_panels
        from project.views import HomeView

        self.assertEqual(snippet_panels({"view": HomeView()})["docs"], ())

    def test_home_has_no_doc_refs_heading(self):
        resp = self.client.get(reverse("home"))
        self.assertNotContains(resp, "References to documentation")

    def test_no_heading_when_docs_empty(self):
        from django.template.loader import render_to_string

        html = render_to_string(
            "project/snippet_panels.html",
            {"panels": [{"id": "p", "title": "t", "html": "h"}], "look_at": "", "docs": ()},
        )
        self.assertIn("snippet-panels", html)
        self.assertNotIn("References to documentation", html)
        self.assertNotIn("<ul", html)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd examples/bootstrap5 && pytest project/tests.py::DocRefsPanelTest -v`
Expected: `test_every_feature_page_lists_its_doc_refs` and `test_heading_translated_de_labels_stay_english` FAIL
(heading not in response). `test_docs_empty_for_non_feature_view` FAILS with `KeyError: 'docs'`. The other two
pass already; they guard against regressions.

- [ ] **Step 3: Implement the tag change**

In `examples/bootstrap5/project/templatetags/example_tags.py`, replace the final line of `snippet_panels`:

```python
    return {"panels": panels, "look_at": feature.look_at if feature else ""}
```

with:

```python
    return {
        "panels": panels,
        "look_at": feature.look_at if feature else "",
        "docs": feature.docs if feature else (),
    }
```

- [ ] **Step 4: Implement the template change**

In `examples/bootstrap5/project/templates/project/snippet_panels.html`, insert after the accordion's closing
`</div>` (the one closing `<div class="accordion" id="snippetAccordion">`) and before the closing `</div>` of
`#snippet-panels`:

```html
        {% if docs %}
            <h5 class="mt-3"><i class="fa-solid fa-book"></i> {% translate "References to documentation" %}</h5>
            <ul>
                {% for ref in docs %}
                    <li><a href="{{ ref.url }}" target="_blank" rel="noopener">{{ ref.label }}</a></li>
                {% endfor %}
            </ul>
        {% endif %}
```

- [ ] **Step 5: Add the German translation**

```bash
cd examples/bootstrap5
python manage.py makemessages -l de
```

Open `locale/de/LC_MESSAGES/django.po`, find the new entry and set its msgstr:

```
msgid "References to documentation"
msgstr "Verweise auf die Dokumentation"
```

Check `git diff locale/de/LC_MESSAGES/django.po`. Expected: the new entry plus `#:` source-line comment updates
only. No other msgstr may change, and no entry may become `#, fuzzy`. If makemessages marked anything fuzzy,
fix it before continuing.

```bash
python manage.py compilemessages
python -c "import gettext; t = gettext.GNUTranslations(open('locale/de/LC_MESSAGES/django.mo', 'rb')); print(t.gettext('References to documentation'))"
```

Expected output: `Verweise auf die Dokumentation`. The `.mo` must be non-zero in size; check with `ls -l locale/de/LC_MESSAGES/django.mo`.

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd examples/bootstrap5 && pytest project/tests.py::DocRefsPanelTest test_i18n.py -v`
Expected: all pass, including `test_no_empty_or_fuzzy_msgstr` and `test_mo_files_load`.

- [ ] **Step 7: Lint and commit**

```bash
ruff format examples/bootstrap5 && ruff check examples/bootstrap5
git add examples/bootstrap5/project/templatetags/example_tags.py \
        examples/bootstrap5/project/templates/project/snippet_panels.html \
        examples/bootstrap5/locale/de/LC_MESSAGES/django.po \
        examples/bootstrap5/locale/de/LC_MESSAGES/django.mo \
        examples/bootstrap5/project/tests.py
git commit -m "feat(examples): show 'References to documentation' on every example page"
```

---

### Task 4: "Try it live" boxes in the docs + backlink test + changelog

**Files:**
- Modify: `examples/bootstrap5/test_doc_links.py` (append the backlink test)
- Modify: `mkdocs.yml`
- Modify: `docs/getting_started/index.md` and `docs/reference/{list_view,ordered_view,nested,formsets,workflow_view,polymorphic_view,guardian,resources,card-list-view,object_detail_view,modals,action_view,object_detail_layout_packs,object_detail_badges,object_detail_links,breadcrumb,conditional}.md`
- Modify: `CHANGELOG.md`

**Interfaces:**
- Consumes: `FEATURES`, `Feature.docs`, `Feature.url_name`; `DOCS_DIR` from `test_doc_links.py` (Task 2).

- [ ] **Step 1: Write the failing backlink test**

Append to `examples/bootstrap5/test_doc_links.py`:

```python
DEMO_BASE = "https://django-crud-views-demo.onrender.com"


def iter_backlinks():
    """One case per (feature, distinct referenced page); a page referenced twice by one app is checked once."""
    return [
        pytest.param(feature, page, id=f"{feature.app}:{page}")
        for feature in FEATURES
        for page in dict.fromkeys(ref.page for ref in feature.docs)
    ]


@pytest.mark.parametrize("feature, page", iter_backlinks())
def test_docs_page_links_back_to_demo(feature, page):
    from django.urls import reverse

    demo_url = DEMO_BASE + reverse(feature.url_name)
    text = (DOCS_DIR / page).read_text(encoding="utf-8")
    assert demo_url in text, f"docs/{page} does not link to the {feature.title} example ({demo_url})"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd examples/bootstrap5 && pytest test_doc_links.py -k links_back -v`
Expected: 19 collected, 19 FAIL (`does not link to the ... example`). 19 = library 3, nested 1, formsets 1,
workflow 1, polymorphic 1, guardian 1, resources 1, showcase 4, object_detail 4, breadcrumbs 1, conditional 1.

- [ ] **Step 3: Enable the admonition extension**

Append to `mkdocs.yml`:

```yaml
markdown_extensions:
    - admonition
```

- [ ] **Step 4: Add the boxes**

**Placement rule (every page):** insert the box right after the first paragraph that follows the `# ` title.
That paragraph ends at the first blank line after it. Keep one blank line before and after the box. On pages
where code or a list follows the intro paragraph (e.g. `action_view.md`, `object_detail_badges.md`), the box
goes between the intro paragraph and that code or list.

**Single-app box** (substitute `<Title>`, `<path>` and `<demo-md>` from the table below):

```markdown
!!! example "Try it live"
    The [<Title> example](https://django-crud-views-demo.onrender.com<path>) in the live demo shows this in
    action — log in as `alice` / `alice`. See [Live demo](<demo-md>) for data resets and wake-up time.
```

| Page | `<Title>` | `<path>` | `<demo-md>` |
|---|---|---|---|
| `docs/getting_started/index.md` | Library | `/library/author/` | `demo.md` |
| `docs/reference/list_view.md` | Library | `/library/author/` | `../getting_started/demo.md` |
| `docs/reference/ordered_view.md` | Library | `/library/author/` | `../getting_started/demo.md` |
| `docs/reference/nested.md` | Nested | `/nested/company/` | `../getting_started/demo.md` |
| `docs/reference/formsets.md` | Formsets | `/formsets/questionnaire/` | `../getting_started/demo.md` |
| `docs/reference/workflow_view.md` | Workflow | `/workflow/campaign/` | `../getting_started/demo.md` |
| `docs/reference/polymorphic_view.md` | Polymorphic | `/polymorphic/vehicle/` | `../getting_started/demo.md` |
| `docs/reference/resources.md` | Resources | `/resources/s3file/` | `../getting_started/demo.md` |
| `docs/reference/card-list-view.md` | Showcase | `/showcase/recipe/` | `../getting_started/demo.md` |
| `docs/reference/modals.md` | Showcase | `/showcase/recipe/` | `../getting_started/demo.md` |
| `docs/reference/action_view.md` | Showcase | `/showcase/recipe/` | `../getting_started/demo.md` |
| `docs/reference/object_detail_layout_packs.md` | Object Detail | `/object-detail/product/` | `../getting_started/demo.md` |
| `docs/reference/object_detail_badges.md` | Object Detail | `/object-detail/product/` | `../getting_started/demo.md` |
| `docs/reference/object_detail_links.md` | Object Detail | `/object-detail/product/` | `../getting_started/demo.md` |
| `docs/reference/breadcrumb.md` | Breadcrumbs | `/breadcrumbs/workspace/` | `../getting_started/demo.md` |
| `docs/reference/conditional.md` | Conditional | `/conditional/registration/` | `../getting_started/demo.md` |

For example, the finished box in `docs/reference/nested.md` reads:

```markdown
!!! example "Try it live"
    The [Nested example](https://django-crud-views-demo.onrender.com/nested/company/) in the live demo shows this in
    action — log in as `alice` / `alice`. See [Live demo](../getting_started/demo.md) for data resets and wake-up time.
```

**`docs/reference/guardian.md`** (per-object permissions differ by user, so both logins are named):

```markdown
!!! example "Try it live"
    The [Guardian example](https://django-crud-views-demo.onrender.com/guardian/document/) in the live demo shows
    this in action — log in as `alice` / `alice` and as `bob` / `bob` to compare what each of them sees. See
    [Live demo](../getting_started/demo.md) for data resets and wake-up time.
```

**`docs/reference/object_detail_view.md`** (shared by two apps):

```markdown
!!! example "Try it live"
    The [Object Detail example](https://django-crud-views-demo.onrender.com/object-detail/product/) and the
    [Showcase example](https://django-crud-views-demo.onrender.com/showcase/recipe/) in the live demo show this in
    action — log in as `alice` / `alice`. See [Live demo](../getting_started/demo.md) for data resets and wake-up
    time.
```

The demo URL must stay on one unbroken line. A line break inside the `(...)` would break both the link and the
backlink test.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `cd examples/bootstrap5 && pytest test_doc_links.py test_docs_sync.py -v`
Expected: all pass. `test_docs_sync.py` must stay green; the boxes must not land between a `<!-- cv-sync: ... -->`
marker and its code block.

- [ ] **Step 6: Build the docs strictly**

Run: `mkdocs build --strict` (from the repo root; this is what `.github/workflows/docs.yml` runs).
Expected: exit 0, no warnings. Then open `site/reference/nested/index.html` and confirm the box rendered as a
`<div class="admonition example">`, not as literal `!!! example` text:

```bash
grep -c 'admonition example' site/reference/nested/index.html site/reference/object_detail_view/index.html
```

Expected: `1` for each file.

- [ ] **Step 7: CHANGELOG**

In `CHANGELOG.md`, under `## Unreleased` → `### Added`, append this bullet after the existing ones:

```markdown
- Documentation and live demo link to each other. Every example page in the demo lists the documentation
  sections that explain it under "References to documentation" (German: "Verweise auf die Dokumentation"),
  linking to the `stable` docs; every one of those docs pages has a "Try it live" box linking back to the
  example. A test in the example project checks that every reference resolves to an existing page and heading
  and that every referenced page links back.
```

- [ ] **Step 8: Full verification**

```bash
ruff format --check examples/bootstrap5 && ruff check examples/bootstrap5
cd examples/bootstrap5 && pytest
```

Expected: ruff clean. Examples suite fully green (the previous count plus the new tests). There are no `src/` changes, so the package suite is not affected.

- [ ] **Step 9: Commit**

```bash
git add mkdocs.yml docs/getting_started/index.md docs/reference/*.md CHANGELOG.md examples/bootstrap5/test_doc_links.py
git commit -m "docs: link reference pages to their live-demo examples"
```
