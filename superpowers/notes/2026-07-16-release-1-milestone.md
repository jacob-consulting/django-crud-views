# Release 1.0.0 Milestone

**Date:** 2026-07-16
**Status:** Approved milestone outline — each sub-milestone gets its own brainstorm → spec → plan → implementation cycle.
**Source prompt:** `superpowers/prompts/2027-07-16-release-1-milestone.md`

## Purpose

django-crud-views is approaching production state. This document breaks the road to 1.0.0
into ordered sub-milestones. It is **not** a spec or implementation plan. Each sub-milestone
section carries enough context (current state, decisions already made, open questions) for a
fresh session to brainstorm it standalone, one after the other, in order.

## Starting point (facts as of 2026-07-16)

- Current version **0.12.1**, live on PyPI, main branch CI green.
- Distribution ships five Django apps from `src/`: `crud_views`, `crud_views_plain`,
  `crud_views_polymorphic`, `crud_views_workflow`, `crud_views_guardian`.
- The June 2026 repository audit (`AUDIT.md`) is **fully complete**; remaining follow-ups
  live as GitHub issues. Only three are open: **#28** (expand system checks),
  **#31** (workflow: configurable transaction behavior), **#34** (deprecate
  `CrispyModelViewMixin` alias).
- Test suite: ~320 tests in `tests/test1/`, total coverage ~95%, CI-gated at
  `fail_under = 88`. Nox matrix: Python 3.12/3.13/3.14 × Django 4.2/5.2/6.0.
- `README.md` was recently reworked and already has a strong teaser + minimal code sample.
  `docs/index.md` still has the older, drier framing and still advertises the plain theme.
- Sibling repo `django-crud-views-extensions` (crud_views_widget_* apps) depends on this
  package; API changes ripple there.

## Decisions already made (2026-07-16 brainstorm)

1. **`crud_views_plain` is removed; theme pluggability stays.** The theme-override
   mechanism remains a documented feature ("bring your own theme"); bootstrap5 becomes the
   only shipped theme.
2. **The removal ships in the next 0.x minor (0.13.0)**, not in 1.0.0 itself. 1.0.0 ships
   clean rather than as a bundle of removals. No deprecation period — the theme is unused.
3. **Examples layout: one Django project, one app per feature.** Single runnable project
   `examples/bootstrap5/` with self-contained feature apps (own models/views/templates each).
4. **Four additional 1.0 gaps are in scope:** public-API definition + deprecation cleanup,
   open-issues triage, version policy + English sweep, pre-1.0 security review.
5. **API work (M2) comes before the examples rewrite (M3)** so the new examples are written
   against the final 1.0 API.

## Sub-milestone order and rationale

| # | Sub-milestone | Ships as | Why this position |
|---|---------------|----------|-------------------|
| M1 | Remove `crud_views_plain` + examples groundwork | 0.13.0 | Mechanical; clears the ground for everything after |
| M2 | API stability & backlog triage | 0.14.0 (or with M3) | Examples must be written against the final API |
| M3 | Examples rewrite | — | The big one; docs tutorial will align to it |
| M4 | Documentation refinement | — | Tutorial follows the M3 `library/` app step by step |
| M5 | README & marketing surface | — | References the final example-run instructions |
| M6 | Release readiness → 1.0.0 | 1.0.0 | Security pass, version policy, changelog, cut release |

M3–M5 can ship as further 0.x releases as convenient; only M1 (breaking removal) and
M6 (1.0.0) have fixed release semantics.

---

## M1 — Groundwork: remove `crud_views_plain` (0.13.0)

**Goal:** the plain theme and its example are gone; theme pluggability is still a documented,
supported concept; `examples/shared/` is folded into the bootstrap5 example.

**Why:** the plain theme is unused (not even by the maintainer), undocumented, untested,
unmaintained, and it clutters `examples/`.

**Current state — known reference sites (verified by grep, re-verify at implementation time):**

- `src/crud_views_plain/` — the app itself (apps.py, static/, templates/ — 25 HTML templates)
- `pyproject.toml` — packages list (~line 97), coverage source (~line 114),
  bump-my-version file entry (~line 138)
- `src/crud_views/lib/settings.py` — mentions `crud_views_plain`
- `tests/test1/test_assets.py` — plain-theme assertions
- `examples/plain/` — full example project
- `docs/index.md` (features list: "plain no CSS…") and `docs/reference/modals.md`

**Scope:**

- Delete `src/crud_views_plain/`, `examples/plain/`, and all packaging/coverage/bump entries.
- Clean settings/tests/docs references; adjust or remove plain-specific asset tests.
- Keep and document the theme-override mechanism: how template resolution finds theme
  templates, what a third-party theme app must provide. Likely lands in
  `docs/reference/templates.md`.
- Fold `examples/shared/` (models + migrations + taskfile) into `examples/bootstrap5/` —
  after M1 it has exactly one consumer. Keep this a mechanical move; the didactic
  restructuring happens in M3.
- CHANGELOG entry marking the removal as breaking; release 0.13.0.

**Open questions for the sub-brainstorm:**

- Does any template in the bootstrap5 theme or test suite *extend* a plain template
  (inheritance chains), or are the two theme trees fully parallel?
- Where exactly should the "write your own theme" documentation live, and how much of it
  already exists in `docs/reference/templates.md`?

**Done when:** package builds and installs without `crud_views_plain`; full test suite green;
no grep hits for `crud_views_plain` outside CHANGELOG/history; 0.13.0 on PyPI.

---

## M2 — API stability & backlog triage

**Goal:** 1.0.0's semver promise has a defined object: a documented public API surface, no
lingering deprecations, and an explicitly triaged backlog.

**Why:** 1.0 is a stability contract. The package has never stated what its public API is —
the audit declared the formsets API "semi-private" (maintainer decision #1, 2026-06-10), and
issue #34 has a deprecation alias waiting for a breaking-change window.

**Current state:**

- Public-ish surface today: `ViewSet`, the `CrudView` view classes and their
  `*PermissionRequired` variants, crispy/table/filter mixins, settings
  (`CRUD_VIEWS_*`), template tags, and the extension apps (workflow, polymorphic, guardian).
- Formsets API: semi-private per audit decision; renames were allowed without shims.
- Open issues: #28 (expand system checks), #31 (workflow transaction behavior),
  #34 (deprecate `CrispyModelViewMixin` alias).
- Downstream consumer: `django-crud-views-extensions` (must be checked against any removal).

**Scope:**

- Write a "public API / stability" statement: what is covered by semver from 1.0 on, what is
  explicitly internal (e.g. formsets internals), what the deprecation policy is post-1.0.
- Resolve #34: remove the alias in a 0.x minor (breaking window is still open pre-1.0);
  update django-crud-views-extensions if it uses the alias.
- Triage #28 and #31: for each, decide *in 1.0* or *deferred to 1.x*, and record the
  decision on the issue. An untriaged backlog at 1.0 is fine; an undecided one is not.
- Sweep for other unstated deprecations/TODO-style API warts while the breaking window is
  open (the audit's TODO triage already ran, so expect few).

**Open questions for the sub-brainstorm:**

- Is the formsets API promoted to public for 1.0 or does it stay documented-as-internal?
- Where does the stability statement live — `docs/index.md`, a dedicated
  `docs/development/stability.md`, or both?
- Do #28/#31 have user-visible API implications that would argue for doing them pre-1.0?

**Done when:** stability statement merged; #34 closed; #28 and #31 carry an explicit
in/out-of-1.0 decision; extensions repo verified compatible.

---

## M3 — Examples rewrite (the big one)

**Goal:** didactically clean examples — one self-contained app per feature inside a single
runnable project, real-life domains, English only, tested, and structured so the docs
tutorial (M4) can follow one of the apps step by step.

**Why:** the current example grew organically during package development and it shows:
`app/views/` contains `foo.py`, `bar.py`, `baz.py`, `qux.py` next to `author.py`,
`book.py`, `campaign.py`, `s3.py`, `formset/`, `poly/`; models are split between
`examples/shared/models.py` and the app; shared models carry German strings
("Vorname", verbose_name "Autor"/"Autoren").

**Approved target layout:**

```
examples/bootstrap5/
  project/            # settings, root urls, home page listing all feature apps
  library/            # basic CRUD — Author/Book; doubles as the tutorial app
  nested/             # parent/child ViewSets (FK-nested URLs)
  formsets/
  workflow/           # FSM transitions
  polymorphic/
  guardian/           # per-object permissions
  resources/          # non-ORM data (S3 listing / API results)
  manage.py
```

(App list is indicative — the sub-brainstorm fixes the exact set; every shipped feature must
be covered by exactly one app.)

**Scope and quality bar (from the milestone prompt, refined):**

- One example app per feature; each app self-contained (own models, views, templates,
  fixtures/seed data, tests).
- Each feature app's landing page is mostly its list view **plus rendered code snippets**
  showing the code behind the page.
- Real-life domains that make sense out of the box — no Foo/Bar/Baz. Specifically:
  - **fieldsets**: current examples are the most complex, likely *too* complex — simplify.
  - **guardian**: current example demonstrates guardian mechanics but isn't a believable
    scenario — design a genuinely real-life per-object-permission use case (e.g. documents
    shared per-user).
- English only (removes the German strings); i18n as a *demonstrated feature* is a separate
  decision, not mixed into every model.
- All features covered and unit tested; examples aligned with the documentation tutorial —
  the tutorial builds `library/` step by step, and docs FAQ items should point at (or be
  drawn from) example apps.

**Open questions for the sub-brainstorm:**

- Exact feature→app mapping (do fieldsets/cards/actions get own apps or live inside
  `library/`? does ordered up/down demo live in `library/` or `nested/`?).
- How are code snippets rendered on landing pages — read from source files at runtime,
  duplicated into templates, or generated? (Runtime reading keeps them honest.)
- Test strategy: pytest against the example project (second test target next to
  `tests/test1/`) vs. Django `manage.py test` per app; CI wiring either way.
- Seed data strategy so `task run` shows populated lists immediately (migrations,
  fixtures, or a management command).
- One shared DB with per-app models, or does any feature (guardian users/groups,
  workflow states) need special seeding?
- What happens to the existing `db.sqlite3`, `locale/`, and `management/` bits of the
  current example?

**Done when:** `examples/bootstrap5/` matches the approved layout, every shipped feature has
exactly one example app, all example tests pass in CI, no German strings remain, and the
home page navigates to every feature app.

---

## M4 — Documentation refinement

**Goal:** docs that sell and teach: a catchy teaser, a tutorial that is fun and verifiably
in sync with the `library/` example app, logical ordering, and a reference that covers every
feature.

**Why:** `docs/index.md` still opens with generic framing ("Managing CRUD operations is a
common requirement…") while the README already has much stronger copy. The tutorial
(`docs/getting_started/tutorial.md` + `tutorial2.md`) predates the examples rewrite and
references a Django 3.2 tutorial link. Nav is `awesome-pages`-driven; order needs a check.

**Current state:**

- `docs/`: `index.md`, `faq.md`, `getting_started/` (index, tutorial, tutorial2, assets/
  with screenshots), `reference/` (21 pages incl. settings, templates, assets, resources,
  guardian, workflow, polymorphic), `development/`.
- mkdocs: readthedocs theme, `awesome-pages` plugin, published on Read the Docs.

**Scope:**

- **Teaser** on `docs/index.md` — the hard one; take time. The README's "Stop hand-writing
  the same list, detail, create, update and delete views…" framing is the starting material;
  index.md and README should share one voice without being byte-identical.
- **Tutorial rewrite**: builds the `library/` example app step by step (model → ViewSet →
  urls → first list page → detail/create/update/delete → tables/filters → permissions …).
  Every tutorial code block must exist in, or be derived from, the example app so they
  cannot drift. Fix stale links (Django 3.2 → current). Refresh screenshots in
  `getting_started/assets/`.
- **Order of appearance**: home → getting started/tutorial → per-feature guides → reference
  → FAQ → development. Verify `.pages` files produce that nav.
- **Reference completeness audit**: enumerate shipped features (from the M3 app list — that
  list *is* the feature inventory) and check each has a reference page; plain-theme
  mentions are gone (M1); the theming/"bring your own theme" page exists.
- FAQ ↔ examples cross-links (per the milestone prompt: FAQ items can contribute examples).

**Open questions for the sub-brainstorm:**

- Mechanism for tutorial↔example sync (manual discipline, snippet-include tooling, or a CI
  check that tutorial code blocks appear in the example source)?
- Do `tutorial.md`/`tutorial2.md` merge into one progressive tutorial or stay split?
- Screenshot tooling: `scripts/generate_mockups.py` exists — reuse for reproducible
  screenshots?

**Done when:** index has the new teaser, tutorial matches `library/` exactly, nav order is
deliberate, every feature has a reference page, and no doc mentions removed functionality.

---

## M5 — README & marketing surface

**Goal:** the GitHub home page catches experienced Django developers who are fed up writing
the same CRUD code — and gets them to a running example in minutes, on Linux, macOS **and
Windows**, with instructions that are short, precise and *verified working*.

**Why:** README is the #1 marketing surface. It was recently reworked (teaser, "This is all
you write" code sample, "Why developers use it" bullets) — good base, but the
run-the-examples story must be rewritten for the M3 layout and actually tested per platform.

**Scope:**

- Update the examples section for the new `examples/bootstrap5/` layout.
- "Run the examples" instructions: shortest honest path per OS. Current tooling assumes
  `uv` + `task` (go-task) — decide whether Windows instructions use the same tools
  (both support Windows) or a plain `python -m venv` + `pip` fallback. **Do not guess:
  execute the instructions on each platform (or the closest available proxy) before
  publishing them.**
- Screenshot or GIF of the example app near the top (marketing).
- Align README copy with the M4 docs teaser (one voice); check the PyPI long description
  renders correctly.

**Open questions for the sub-brainstorm:**

- Minimum entry path: is `task dev && task run` acceptable as the *only* path (requires
  installing uv + task), or should the README offer a tool-free `pip install -e . && python
  manage.py …` path? What is actually verifiable on Windows (native vs. WSL)?
- Does the README get a features/screenshot section per extension app, or stay minimal and
  defer to docs?

**Done when:** a fresh reader on each OS can go from `git clone` to a browsable example
following the README verbatim, and the README/PyPI/docs speak with one voice about the same
1.0-era package.

---

## M6 — Release readiness → 1.0.0

**Goal:** stamp 1.0.0 with confidence: security reviewed, support policy stated, changelog
telling the story, release cut and published.

**Scope:**

- **Security review pass** focused on the package's actual risk surface: permission
  enforcement paths (`*PermissionRequired` variants, context-button permission gating),
  the AJAX formset template endpoint, guardian per-object checks, and anything
  user-input-driven in template tags. Use the `/security-review` skill as the driver;
  findings either fixed or explicitly accepted before 1.0.
- **Version support policy**: state the supported Python × Django matrix (currently tested:
  3.12/3.13/3.14 × 4.2/5.2/6.0) as *policy* in docs + PyPI classifiers, including how the
  matrix will evolve (e.g. follow Django's supported-versions schedule).
- **CHANGELOG**: 1.0.0 entry that summarizes the road (plain removal, examples, API
  stability statement) and a short "what 1.0.0 means" note (semver promise, link to the M2
  stability statement).
- Final sweep: version bump via bump-my-version, tag, publish workflow to PyPI (existing
  release process — see project memory `release-process`), announce (README badge row,
  Read the Docs default version).
- Verify `django-crud-views-extensions` installs and passes against 1.0.0.

**Open questions for the sub-brainstorm:**

- Ship a 1.0.0rc1 to PyPI first, or cut 1.0.0 directly from the last green 0.x?
- Any announcement beyond GitHub/PyPI (Django forum, r/django, blog post)?

**Done when:** security findings resolved/accepted, policy + changelog merged, 1.0.0 live on
PyPI, extensions repo green against it.

---

## How to use this document

Work the sub-milestones **in order**. For each one, start a fresh session with:

> Brainstorm sub-milestone M*n* from `superpowers/notes/2026-07-16-release-1-milestone.md`.

The section's *current state*, *decisions already made*, and *open questions* are the
brainstorm inputs; its *done when* is the acceptance bar. Update this document's status line
as sub-milestones complete.
