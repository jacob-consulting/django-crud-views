# Bi-directional links between the live demo and the documentation

Date: 2026-10-07
Status: approved design, pending spec review

## Goal

Readers of the documentation (Read the Docs) can jump to the matching example in the live demo
(Render, `https://django-crud-views-demo.onrender.com`), and visitors of the demo can jump from an example
to the documentation sections that explain it. Both directions are checked by tests, so renamed headings,
moved pages or a missing return link fail CI instead of rotting silently.

## Decisions

| # | Question | Decision |
|---|----------|----------|
| 1 | Granularity of example → docs references | **Per example app** (`Feature`), like "The code behind this page". All pages of one app show the same references. |
| 2 | Docs version linked from the demo | **`/en/stable/`** — the newest release tag, matching the demo, which runs the latest release. |
| 3/4 | Automated checks | **Integrity + backlinks**: every reference resolves to an existing docs page and heading anchor; every referenced docs page links back to the app's demo landing page. |
| 5/6 | Presentation in the docs | **`!!! example "Try it live"` admonition** near the top of each referenced page. |
| 7 | Translation | Section heading translated (en + de). **Link labels stay English, untranslated** — consistent with `Feature.title` / `look_at`, which quote package terms and are deliberately not translated. |
| 8 | Which docs pages get a demo link | Exactly the pages referenced by some `Feature.docs` entry (see mapping). Pages without an example get nothing. |

## Examples side

### Data model — `examples/bootstrap5/project/features.py`

```python
DOCS_BASE = "https://django-crud-views.readthedocs.io/en/stable"


@dataclass(frozen=True)
class DocRef:
    page: str  # path under docs/, e.g. "reference/nested.md"
    label: str  # English link text, deliberately not translated (like Feature.title / look_at)
    anchor: str = ""  # heading slug on that page, e.g. "creating-children"

    @property
    def url(self) -> str: ...
```

`DocRef.url` follows mkdocs' default `use_directory_urls`:

- `"reference/nested.md"` → `f"{DOCS_BASE}/reference/nested/"`
- `"getting_started/index.md"` → `f"{DOCS_BASE}/getting_started/"`
- with `anchor="creating-children"` → `.../reference/nested/#creating-children`

`Feature` gains `docs: tuple[DocRef, ...] = ()`. It is a tuple because `Feature` is frozen, and it comes after
the existing defaulted `badge` field.

### Rendering

`snippet_panels` (`project/templatetags/example_tags.py`) already resolves the view's `Feature`. It also
returns `docs` (`feature.docs`, or `()` for non-feature views). `project/snippet_panels.html` renders a new
section **after** the accordion, still inside `#snippet-panels`, only when `docs` is non-empty:

```html
<h5 class="mt-3"><i class="fa-solid fa-book"></i> {% translate "References to documentation" %}</h5>
<ul>
    {% for ref in docs %}
        <li><a href="{{ ref.url }}" target="_blank" rel="noopener">{{ ref.label }}</a></li>
    {% endfor %}
</ul>
```

The whole include only renders under `{% if panels %}`. That is fine: every feature app has panels. The docs
section stays inside that block.

### Translation

- Add the msgid `"References to documentation"` → `"Verweise auf die Dokumentation"` to
  `examples/bootstrap5/locale/de/LC_MESSAGES/django.po` (via `makemessages`).
- Recompile `django.mo` and **verify it is non-empty and contains the new entry**. A zero-byte `.mo` slipped
  into PR #144 before.

## Mapping (initial set)

Anchors are the slugs mkdocs generates from today's headings.

| App (`Feature.app`) | `docs` entries (`page` [`#anchor`]) | Demo landing (`reverse(url_name)`) |
|---|---|---|
| `library` | `getting_started/index.md`; `reference/list_view.md#table-with-django-tables2`; `reference/list_view.md#filtering-with-django-filter`; `reference/ordered_view.md` | `/library/author/` |
| `nested` | `reference/nested.md`; `reference/nested.md#creating-children` | `/nested/company/` |
| `formsets` | `reference/formsets.md` | `/formsets/questionnaire/` |
| `workflow` | `reference/workflow_view.md`; `reference/workflow_view.md#workflowmodelmixin` | `/workflow/campaign/` |
| `polymorphic_demo` | `reference/polymorphic_view.md#two-step-create-flow`; `reference/polymorphic_view.md#polymorphic_forms` | `/polymorphic/vehicle/` |
| `guardian_demo` | `reference/guardian.md`; `reference/guardian.md#working-example` | `/guardian/document/` |
| `resources` | `reference/resources.md` | `/resources/s3file/` |
| `showcase` | `reference/card-list-view.md#signed-choices-single-combo-no-buttons`; `reference/object_detail_view.md#the-cv_property_display-dsl`; `reference/modals.md`; `reference/action_view.md` | `/showcase/recipe/` |
| `object_detail` | `reference/object_detail_view.md`; `reference/object_detail_layout_packs.md`; `reference/object_detail_badges.md`; `reference/object_detail_links.md` | `/object-detail/product/` |
| `breadcrumbs` | `reference/breadcrumb.md`; `reference/breadcrumb.md#hooking-into-your-site-navigation` | `/breadcrumbs/workspace/` |
| `conditional` | `reference/conditional.md#kind-1-conditional-field-group-in-a-form`; `reference/conditional.md#kind-2-conditional-formset` | `/conditional/registration/` |

Labels are short English phrases naming the topic, e.g. `"Nested ViewSets — creating children"`. The exact
wording is left to implementation. Implementation must verify each anchor against the slugify helper (the
integrity test does this). It must not trust this table blindly.

## Docs side

- `mkdocs.yml`: add `markdown_extensions: [admonition]`. The admonition extension is built into
  Python-Markdown, so it needs no new docs dependency.
- Each page in the mapping gets **one** admonition, placed after the page's intro paragraph (before the first
  `##`). If several apps reference the same page (`reference/object_detail_view.md`: Object Detail and
  Showcase), the box lists all of them:

  ```markdown
  !!! example "Try it live"
      [Nested example](https://django-crud-views-demo.onrender.com/nested/company/) in the live demo —
      log in as `alice` / `alice`. See [Live demo](../getting_started/demo.md) for resets and wake-up time.
  ```

  The relative link to `demo.md` is adjusted per page depth (`getting_started/index.md` uses `demo.md`).
- The existing repo-path sections ("Working Example" in `guardian.md`, "Examples" in `conditional.md`) stay
  as they are.

## Tests — new `examples/bootstrap5/test_doc_links.py`

It sits next to `test_docs_sync.py`, uses the same `DOCS_DIR` resolution, and runs in the nox `examples`
session.

1. **Slugify helper.** A local copy of Python-Markdown's `markdown.extensions.toc.slugify` (the mkdocs
   default): NFKD-normalize, drop non-ASCII, strip `[^\w\s-]`, strip, lowercase, collapse `[-\s]+` to `-`.
   It is copied with a comment naming the source, because `markdown` is not installed in the
   `examples` nox session (`.[all,test,examples]` + `requirements/demo.txt`) and is not worth adding as a
   dependency. Unit-tested against real headings, e.g. ``Down: table links and `ChildContextButton` `` →
   `down-table-links-and-childcontextbutton`, `` `polymorphic_forms` `` → `polymorphic_forms`,
   `Kind 1 — Conditional field-group in a form` → `kind-1-conditional-field-group-in-a-form`.
2. **Heading extraction** ignores lines inside fenced code blocks (`workflow_view.md` has `# urls.py` inside a
   fence). Covered by a unit test on a fixture string.
3. **Integrity** (parametrized per `DocRef`): `DOCS_DIR / ref.page` exists. If `ref.anchor` is set, it equals
   the slug of some heading on that page.
4. **Backlink** (parametrized per feature × distinct referenced page): the page text contains
   `DEMO_BASE + reverse(feature.url_name)` with `DEMO_BASE = "https://django-crud-views-demo.onrender.com"`.
   This catches both a missing box and a stale path. The box format itself is not asserted.

Additions to `project/tests.py`:

5. A feature page (e.g. `nested` company list) renders the "References to documentation" heading and an
   `<a href>` for each of its `DocRef.url`s.
6. `DocRef.url` builds the plain page, `index.md` and anchor cases correctly.
7. With the `de` language active, the heading renders as "Verweise auf die Dokumentation".

## Out of scope / known limitations

- **`stable` lags `main`.** Anchors or pages added in a PR only resolve on Read the Docs after the next release
  tag. The tests check against the repo's `docs/`, not the live site. There is no network link check.
- Links in older Read the Docs versions point at the *current* demo. That is accepted.
- Docs→demo links target app landing pages only. Detail/edit pages have PKs that change on every reseed.
- Anonymous visitors following a docs link land on the login page first. The box tells them the credentials.
- Per-view references are not supported (decision 1).
- No package (`src/`) code changes.

## Housekeeping

- `CHANGELOG.md` → "Unreleased" → "Added": documentation ↔ live-demo cross-links.
- `ruff format` / `ruff check` clean; full examples test suite green across the nox matrix.
