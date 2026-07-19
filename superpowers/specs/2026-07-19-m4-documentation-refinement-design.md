# M4 — Documentation Refinement: Design

**Date:** 2026-07-19
**Status:** Approved design (brainstormed with maintainer)
**Milestone source:** `superpowers/notes/2026-07-16-release-1-milestone.md`, section M4
**Acceptance bar (from milestone):** index has the new teaser, tutorial matches `library/`
exactly, nav order is deliberate, every feature has a reference page, and no doc mentions
removed functionality.

## Context

`docs/index.md` still opens with the dry pre-README framing while the README has strong,
current copy. The tutorial (`tutorial.md` 102 lines + `tutorial2.md` 40 lines) predates the
M3 examples rewrite: it uses the removed `vs = vs_author` attribute (current API:
`cv_viewset`), links to the Django 3.2 tutorial, references the removed `app/` monolith,
and its screenshots show the pre-M3 app. Since the milestone doc was written the feature
inventory has grown: `examples/bootstrap5/` now has 12 apps (library, nested, formsets,
workflow, polymorphic_demo, guardian_demo, resources, showcase, breadcrumbs, conditional,
object_detail) and `docs/reference/` has 27 pages.

Verified gaps: **nested parent/child ViewSets** and **formsets** have no reference page
(nested exists only as a FAQ snippet; formsets only inside `conditional.md`).
`scripts/generate_mockups.py` draws artificial PIL mockups, not real screenshots.
Top-level nav order already matches the target (Home → Getting started → Reference → FAQ
→ Development); only the grouping *inside* reference/ needs work.

## Decisions (brainstorm, 2026-07-19)

1. **Tutorial↔example sync: CI check.** Tutorial code blocks are hand-written; a pytest
   verifies each *marked* block appears (whitespace-normalized) in `library/` source.
2. **Tutorial form: multi-part numbered series** replacing `tutorial.md`/`tutorial2.md`.
3. **Screenshots: real and scripted** — Playwright against the seeded example server,
   regenerable on demand; not CI-gated.
4. **Reference gaps: write all missing pages** in M4, including formsets (documented at
   supported-usage level, consistent with the stability doc).
5. **Nav shape: keep the single `reference/` section** serving both guide and reference
   roles; fix grouping/ordering within it. No separate guides/ section.
6. **Packaging: one spec, three phases**, one PR per phase.

## Phase 1 — Tutorial rewrite

**Structure.** A numbered series under `docs/getting_started/` builds the `library/`
example app from scratch. Provisional part cut (boundaries fixed at plan time after a
full read of `library/`):

1. Project setup & first ViewSet — install, `INSTALLED_APPS`, minimal settings, the
   `Author` model, `ViewSet(model=Author, name="author")`, urlpatterns, first list page
2. The list view — `Table`, columns, `UUIDLinkDetailColumn`, `ListViewTableMixin`
3. Forms — create/update/delete with `CrispyModelForm`, layout, `MessageMixin`
4. The detail view — `ObjectDetailViewPermissionRequired` (object_detail app)
5. Filters & permissions — django-filter integration, `*PermissionRequired` behavior
6. Second model & polish — `Book`, ordered up/down, breadcrumbs (whatever `library/`
   demonstrates beyond Author)

Every part ends with a screenshot of the running state. All stale content dies with the
old files. `docs/getting_started/index.md` gets a short honest preface plus two entry
paths: "follow the tutorial" and "run the finished example app" (fixing the current
mislink to `development/index.md`).

**Sync check.** A pytest in the existing CI-wired suite (exact location at plan time)
parses docs pages (the tutorial series and `docs/index.md`) for fenced code blocks
preceded by a marker comment, e.g. `<!-- cv-sync: library/views.py -->`, and asserts the
block appears whitespace-normalized in that file. Final-form blocks carry the marker; progressive
intermediate states are unmarked and allowed (the milestone's "exist in, or be derived
from"). Drift in a marked block fails CI.

**Screenshots.** New `scripts/generate_screenshots.py`: boots the seeded
`examples/bootstrap5` dev server, drives Playwright over a declared list of
(URL, output-name) steps, writes PNGs to `docs/getting_started/assets/`. Run manually
when the UI changes. `scripts/generate_mockups.py` is removed if it has no remaining
consumers.

## Phase 2 — Reference audit, gaps & nav

**Audit.** The 12 example apps plus shipped-but-unexampled capabilities form the
inventory; each row gets a verdict (page exists / missing / stale). Known new pages:

- `docs/reference/nested.md` — `ParentViewSet`, URL nesting, automatic queryset
  filtering, `CreateViewParentMixin`, parent/child context buttons; absorbs the FAQ
  snippet (FAQ then links here).
- `docs/reference/formsets.md` — supported usage surface as the examples use it
  (`FormSetMixin`, template endpoint, conditional-formsets tie-in), with an explicit
  stability-doc note on which internals are not covered by semver.

Further audit findings get pages in the same PR; genuinely large discoveries become
issues flagged to the maintainer instead of ballooning the phase.

**Staleness sweep.** Every existing reference page checked against the current API
(`cv_viewset`, import paths, no removed-functionality mentions, no stale Django version
links). Correctness pass, not a rewrite.

**Nav.** Top-level nav unchanged. `reference/.pages` gets deliberate awesome-pages
grouping, roughly: Core views → Object detail → Lists & tables → Forms → Actions &
navigation → Extensions → Theming → Settings. Principle: reading order follows learning
order, extensions cluster, settings last. Exact grouping at plan time.

## Phase 3 — Teaser, FAQ cross-links & final sweep

**Teaser.** `docs/index.md` opens with the README's framing ("Stop hand-writing the
same…") reworded so docs and README share one voice without being byte-identical.
Structure: hook paragraph → trimmed "this is all you write" sample (linking to the
tutorial) → feature list rewritten as benefit-oriented prose bullets → API-stability
section (kept) → "what it is not" (kept) → version line (kept, bump-my-version-managed).
The code sample participates in the `cv-sync` check.

**FAQ.** Answers demonstrating a feature link to the matching example app and reference
page; answers duplicating reference content get trimmed to a short answer + link.

**Final sweep.** Closing pass over all of `docs/`: no removed functionality, no
`vs =`-era API, no stale Django links, screenshots current, `mkdocs build --strict`
clean; each milestone done-when bullet explicitly verified. Milestone doc M4 status line
updated.

## Delivery

Fresh branch `feature/m4-docs` off `origin/main`; one PR per phase; normal PR lifecycle
(wait CI → fix → squash-merge → wait main CI). Docs-only, no version bump.

## Testing

- New sync-check pytest runs in existing CI and fails on marked-block drift.
- `mkdocs build --strict` must pass (add to CI if not already gated there).
- Screenshot script is manually run; its output committed as normal files.
