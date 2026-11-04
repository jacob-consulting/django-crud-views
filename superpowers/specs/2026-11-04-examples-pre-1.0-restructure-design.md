# Example app restructure before 1.0 — design

Date: 2026-11-04
Branch: `feature/examples-pre-1.0-restructure` (rebased on `origin/main` after PR #305 / phase 06.8 merged)
Scope: `examples/bootstrap5/` and the `docs/` pages it links to. **No changes to the package itself** (`src/`).

## Intent

The example app is the first thing people see of the package. For 1.0 it should be organised so that
**each example teaches one feature**, examples that belong together sit together, and every documented
feature people need when building an app has a live example that links to its documentation and back.

Today's issues:

- "Showcase" mixes four unrelated features (card list, detail fieldsets, modal delete, custom action).
- Some important documented features have no example: delete previews/protection, custom form view,
  label modes/icons, flash messages, disabled actions, theming.
- Formsets and conditional forms are only shown separately; the complex real-world case (both together) is missing.
- "NEW" badges make no sense in a 1.0 release.

## Goals

1. Dissolve Showcase; move each of its parts to the example where it teaches best.
2. Add a **Card View** example under Basics that shows the **same data as Library** (Author/Book models)
   through a second ViewSet whose list is a card grid. Library and Card View are a pair: same data,
   different list.
3. Add new examples: **Delete**, **Formsets + Conditional** (combined), **Label modes & icons**,
   **Messages / disabled actions**, **Custom Form View**, **Theme** (pointer page).
4. Remove the "NEW" badges and the `Feature.badge` mechanism.
5. Keep the **two-way links between examples and docs** for everything added, moved or removed:
   every `Feature.docs` entry points to a real docs page and heading, and every page it points to
   has a "Try it live" (`!!! example`) box linking back to the example's landing page.
   `examples/bootstrap5/test_doc_links.py` enforces this and must stay green.
6. All of it ships as **one batch before 1.0**: one feature branch, one PR into main (the user asked for
   one feature branch). Removing Showcase and relinking its docs therefore land together.

## Non-goals

- **No package changes before 1.0.** If an example hits a package limitation, the example works within
  it. A real package bug found along the way gets a GitHub issue (and, per project practice, a fix in the
  package in a separate change), never a workaround hidden in an example.
- No lifting of `crud_views.E310` (conditional formsets are first-level only).
- No Tabler theme code in this repo; the Tabler theme app is a separate project.
- No live, per-request label-mode switcher (would need settings that change per request).

## Anti-goals (would be a failure even if it "works")

- An example that again bundles several unrelated features under one card.
- A new or moved example without its docs link in both directions.
- Delete example text that suggests alice is *not permitted* to delete. The point is that the deletion
  is *blocked by data alice cannot see*, and the page reveals nothing about that data.
- Translated feature titles. Feature titles stay English (they name package features as in the docs);
  group titles and page chrome stay translated as today.

## Target structure

Navbar groups and home page sections (order within each group is the builder's call unless stated):

| Group | Examples |
|---|---|
| Basics | Library, **Card View** (new, right after Library), Nested, Resources, **Delete** (new) |
| Forms | Formsets, Conditional, **Formsets + Conditional** (new), **Custom Form View** (new) |
| UI | Breadcrumbs, Context Buttons, Action Menus (+ favorite action), **Label modes & icons** (new), **Messages & disabled actions** (new), **Theme** (new, pointer page) |
| Extensions | Workflow, Polymorphic, Guardian, Object Detail (+ fieldsets) |

Custom Form View sits under Forms (my call; it is a form without a model).

## Parts

### 1. Remove "NEW" badges

- Remove `badge=` from Breadcrumbs and Conditional, the `Feature.badge` field, the badge markup in
  `project/templates/project/home.html` and `nav.html`, and `test_badges_shown_in_dropdown`
  in `project/tests.py`. Remove the now-unused "NEW" msgid from the locale files.

### 2. Dissolve Showcase

The `showcase` app (Recipe model, seed, views, urls, templates, tests, migrations, `INSTALLED_APPS`
entry, URL include, `Feature` entry) is deleted. Its parts move:

| Showcase part | New home |
|---|---|
| Card grid with signed ordering (`CardListView`, `cv_order_fields`, pagination) | **Card View** (part 3) |
| Detail fieldsets (`cv_property_display` groups) | **Object Detail** — only if it does not already show labelled fieldset groups; otherwise drop |
| Modal delete (`cv_modal = True`) | **Delete** (part 4) |
| Custom "favorite" toggle (`ActionView`, `cv_backend_only`) | **Action Menus** — a toggle action on the chore (e.g. "pin"/"favorite") |

Docs pages that link to Showcase today must be relinked to the new homes:
`docs/reference/card-list-view.md`, `modals.md`, `action_view.md`, `object_detail_view.md`.
Also check `test_doc_links.py`'s own fixtures (it contains a Showcase URL in a test string) and any
other reference in `docs/`, `README.md`, `render.yaml` and the demo settings.

The old `/showcase/...` URLs stop working. No redirect (my call: pre-1.0 demo, no external promise).

### 3. Card View (Basics)

- Uses the **Library models** (`library.Author`, `library.Book`). It defines its own ViewSet(s) with a
  unique `name` and URL prefix; the list view is a card grid.
- Must show: card grid, signed ordering in one combo (e.g. "Newest first", "Last name A–Z"),
  pagination visible with the seed data, card actions, permission-aware buttons.
- Whether it lives as a new app (e.g. `card_view`) or inside `library` is the builder's call; a separate
  app keeps the "one example = one feature" rule and its own "code behind this page" panel.
- Risk to verify first with a small spike: two ViewSets over one model. Nothing in the system checks
  forbids it, but links, permissions, breadcrumbs and URL names must behave. If something breaks, it is
  a package bug → GitHub issue; the example then falls back to a Card View over Book only, or whatever works.
- The `about` text says explicitly that this is the same data as Library, listed differently.
- Seed: Library's seed must produce enough authors (or books) for at least two card pages.

### 4. Delete (Basics)

A delete example built on **Guardian** (per-object visibility is the point), with users alice and bob.
Must show three cases, each reachable from seeded data:

1. **Blocked by your own objects:** alice deletes an object that has `PROTECT`ed children she owns →
   the blocked page lists them, with links.
2. **Blocked by objects you cannot see:** alice deletes an object blocked by `PROTECT`ed children owned
   by bob that she cannot view → the generic "blocked" notice, no labels, nothing about bob's data.
3. **Blocked by a business rule:** `cv_check_delete_protection()` refuses (e.g. "cannot delete while
   shared").

Plus: an object that *can* be deleted, showing the cascade preview (`cv_show_related_objects`) and the
**modal delete** moved from Showcase.

- Models are new (my call: a small parent/child pair with an owner FK and `on_delete=PROTECT`, e.g.
  Project → Task or Document → Attachment). Whether this extends `guardian_demo` or is a new app is
  the builder's call; a new app is preferred so Guardian stays focused on visibility.
- Docs: `docs/reference/delete_view.md` (sections "Cascading Deletes Display", "Protected objects",
  "Permission Filtering", "Delete Protection") and `modals.md`, plus `guardian.md` if relevant.
- `about` text: use the wording "blocked by objects you cannot see", not "not allowed".
- Seed bob's blocking objects **only as `PROTECT` children, never as cascade children** of alice's
  object. The stock page shows unfiltered cascade counts, so cascade children would leak their existence
  (my call; no package change).

### 5. Formsets + Conditional (Forms)

Complex, real-world form within the current limit (conditional formsets on the first level only, E310):

- Parent form with a **conditional field group** (`ModelFieldToggle`, optionally a `UIFieldToggle`).
- A **first-level conditional formset** (toggled by a parent checkbox) whose rows have a
  **nested, unconditional formset** (e.g. Event → toggled Sessions → Speakers per session).
- A second first-level conditional formset contrasting `on_off="purge"` and `on_off="skip"` is
  optional if the existing Conditional example already covers it.
- New models in a new app (my call); domain is the builder's call (event/conference fits).
- Must pass server-side validation without JavaScript, like the existing Conditional example.
- Docs: `docs/reference/formsets.md` and `docs/reference/conditional.md` (including the first-level
  limitation section, so the example shows people the supported pattern).

### 6. Custom Form View (Forms)

- A `CustomFormView` with a non-model form, both object-bound (e.g. "send reminder" for an object) and
  non-object (e.g. "import" or "invite"), with a success message and form hooks.
- Docs: `docs/reference/custom_form_view.md`.

### 7. Label modes & icons (UI)

- Shows the same set of actions in **label**, **icon** and **both** modes side by side, using the per-view
  / per-context-button label-mode settings (no per-request switcher). Shows hover tooltips in icon mode
  and the accessible labels, **as they behave after phase 06.8 (PR #305)**: short action tooltips and
  visible-label suppression. Read #305's docs changes (`buttons.md`, `action_menus.md`,
  `context_buttons.md`) before designing this page.
- May show icon configuration (`CRUD_VIEWS_ICONS`, heading icons) if it fits without crowding.
- Docs: `docs/reference/buttons.md`, `icons.md`, and the label-mode section of `settings.md`.

### 8. Messages & disabled actions (UI)

- Flash messages at all levels (`docs/reference/messages.md`), and `cv_action_enabled` for a
  conditionally disabled action (`action_enabled.md`), plus disabled-vs-hidden for inaccessible actions
  (`inaccessible_actions.md`) where Action Menus does not already cover it.
- Whether this is one example or two is the builder's call; keep each one about one idea.

### 9. Theme (UI, pointer page)

- A landing page with no CRUD of its own: what can be themed, links to `docs/reference/theme.md`,
  `templates.md`, `buttons.md`, `icons.md`, and a link to the **Tabler theme app** (the end-to-end
  demo app). The Tabler app is unfinished; the user finishes it before 1.0. It will be a public demo
  deployed on onrender.com.
- Ship the Tabler part as a **dummy**: a clearly marked placeholder (e.g. a "Tabler theme demo — coming
  soon" card) with the link target kept in one constant so the real onrender.com URL is a one-line change
  later. No dead external link; tests must not require the URL to resolve.
- The "how Tabler was themed" write-up lives in the **Tabler theme app's repo**, not here; this page
  links to it once it exists. (Reason: code copied here would go stale as the theme changes.)
- `docs/reference/theme.md` gets the "Try it live" box back to this page.

## Cross-cutting requirements

- Every new example follows the existing pattern: one `Feature` entry in `project/features.py`
  (`app`, `group`, `title`, `description`, `about`, `look_at`, `url_name`, `icon`, `docs`), a `seed.py`
  with an idempotent `seed()`, `urls.py` included in `project/urls.py`, tests in the app.
- **Two-way docs links** for every `Feature.docs` entry (goal 5). Docs anchors must be real headings.
- i18n: new user-facing strings in `gettext_lazy`, German translations added (the demo runs en + de).
- Seeded users alice/bob are reused; the existing "password = username" convention stays.
- Render demo (`render.yaml`, `settings_demo.py`, `urls_demo.py`) must keep working; check for
  hard-coded app lists.
- Tests: example tests run in parallel (`pytest -n auto`); `test_doc_links.py`, `test_docs_sync.py`
  and `test_i18n.py` must pass.
- CHANGELOG: one entry under `### Internal` (examples are not package API). No `### Breaking` entry,
  so `docs/migrating-1.0.md` is not touched.
- No customer project names anywhere.

## Left to the builder

- App names, model names, seed content, icons, `about`/`look_at` wording (within the anti-goals).
- Order of examples inside a group (except Card View right after Library).
- Whether Messages and disabled actions are one example or two.
- Exact screens/layout of each example.
