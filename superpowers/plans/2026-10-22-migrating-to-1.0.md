# Migrating to 1.0.0 Guide Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** One docs page, `docs/migrating-1.0.md`, that takes a 0.29.x project or downstream theme to 1.0.0 behaviour.

**Architecture:** First an inventory: every user-visible change in `## 0.30.0` and `## Unreleased` of `CHANGELOG.md`
is checked against the code and mapped to a guide section, and a private, read-only scan of the downstream projects
looks for gaps. Then the page is written section by section from that inventory. Last come the pointers (nav,
CHANGELOG, `CLAUDE.md`) and the acceptance note.

**Tech Stack:** MkDocs 1.6 with `awesome-pages` (`.pages` nav files) and `admonition`; Markdown.

**Spec:** `superpowers/specs/2026-10-22-migrating-to-1.0-design.md` (issue #253)

## Global Constraints

- **Confidentiality.** No committed file, commit message, PR title or PR body names a downstream project or the
  client. Before every `git commit`, run the guard and expect no output:
  `git diff --cached | grep -i -n -E '\bBA\b|DPL|AMM|Arbeitsagentur|Arbeitsmarktmonitor|dpl-|gas2gas|weaver|munoreqa|tabler-test|lm/application'`.
  `crud_views_tabler` and "Tabler" are allowed.
- **Downstream projects are read-only.** Nothing under the downstream project paths or their `submodules/` is
  written, not even a scratch edit. The paths come from the private memory note
  `never-name-client-projects-in-docs`; the most important one is listed there first.
- **Private findings stay out of the repo.** The scan results go to `<scratchpad>/migrating-1.0-scan.md`, where
  `<scratchpad>` is the executing session's scratchpad directory. Never commit them, never quote them in the
  acceptance note or the PR.
- **Starting point is 0.29.x.** Steps from 0.30.0 are marked so a 0.30.0 reader can skip them.
- **Net change only.** Each step describes the state from 0.29.x to 1.0.0, not the route through 0.30.0.
- **Every step is backed by a CHANGELOG bullet and the code.** A real break with no bullet gets one under
  `## Unreleased` → `### Breaking` in the same task that adds its step. Where the CHANGELOG and the code disagree,
  the code wins and the mismatch goes in the acceptance note.
- **Link, don't copy.** Each step ends with a link to the reference page and the issue number(s).
- A linked reference page that is wrong about the code is fixed in the task that links to it, and listed in the
  acceptance note.
- Branch `feat/migrating-1.0` off `main` in place (no worktree); one commit per task; PR closes #253; squash merge.
- Not in scope: `docs/development/stability.md`, version bump, classifiers, releases before 0.29.x.

## Review Focus

1. **A 0.30.0 note that later work overtook, written as if still true.** Examples: `detail/widgets/bool.html`
   (deleted in #217), `tags/actions_menu_item_label.html` (no longer used by the stock menu), `tags/messages.html`
   (replaced by `tags/alert.html` in #250). Task 1's inventory has a "net state" column; Task 5 checks every
   *0.30* step against it.
2. **A silent break missing from the checklist.** Every inventory row flagged `silent` must appear in the
   checklist of section 5. Task 5 checks this row by row.
3. **A check code in the step-zero table that the code doesn't raise, or says something different.** Task 2 checks
   every code against `src/` with grep before writing its row.
4. **A downstream override with no step.** Every template a downstream theme overrides that 0.30.0 or Unreleased
   touches must map to a step. Task 1's scan lists them, and Task 4 ticks them off.
5. **A dead link or anchor.** `mkdocs build --strict` in every writing task.

---

### Task 1: Inventory and private downstream scan

Nothing is committed in this task except the start of the acceptance note.

**Files:**
- Create: `superpowers/notes/2026-10-22-migrating-to-1.0-acceptance.md` (inventory table only; public)
- Create: `<scratchpad>/migrating-1.0-scan.md` (private, never committed)

**Interfaces:**
- Produces: the inventory table in the acceptance note, with columns
  `# | release (0.30 / unreleased) | CHANGELOG bullet (first words) | net state at 1.0 (verified where: file path) | reader (app / theme / both) | loud (check code or exception) / silent | guide section (2–5)`.
  Tasks 2–6 write from this table and nothing else.

- [ ] **Step 1: Branch.** `git checkout -b feat/migrating-1.0`.
- [ ] **Step 2: One row per user-visible bullet.** Include every bullet of `## 0.30.0` → `### Breaking` and of
  `## Unreleased` → `### Breaking`, `### Removed` and `### Changed`. A `### Changed` bullet only gets a row if it
  asks the reader to do something or changes markup a reader may select on (for example the filter toggle's
  `aria-*`, `hidden` on `tags/list_action_form.html`). For each row, verify the net state in `src/` (grep the
  template, setting, tag or check code) and write the file path you checked.
- [ ] **Step 3: Overtaken 0.30 notes.** For each 0.30 row, record in "net state" whether Unreleased changed it
  again. At least these three: `detail/widgets/bool.html` gone (#217), the stock menu uses
  `tags/button/menu_item_label.html`, and messages render through `tags/alert.html` (#250).
- [ ] **Step 4: Private scan (read-only).** For each downstream project in the memory note, starting with the
  first, list in the scratch file:
  - every template under a `templates/crud_views/` or `templates/crud_views_object_detail/` directory it ships;
  - every hit for `CRUD_VIEWS_ACTIONS_MENU_ICON|CRUD_VIEWS_FILTER_ICON|CRUD_VIEWS_OBJECT_DETAIL_.*ICON|CRUD_VIEWS_FILTER_RESET_BUTTON_CSS_CLASS|cv_modal_size|modal-(sm|lg|xl)|cvModalOpen|cv_get_context|cv_no_label|cv_label_visible|cv_icon_action|cv_icon_header|cv_menu_icon|cv_header_icon_class|cv_filter_icon|bootstrap_messages|django_bootstrap5|cv_submit_button|cv_cancel_button|cv_delete_button|fa-fw|d-none|data-bs-dismiss|icon="`
    outside `.venv`, `node_modules`, `staticfiles` and the vendored `django-crud-views` copy.

  Map each hit to an inventory row number. A hit with no row is a **gap**: add a row to the inventory, flagged
  `no CHANGELOG bullet` if that's the case.
- [ ] **Step 5: Verify.** Every inventory row has a section number, and the scratch file has no unmapped hit.
  Run the confidentiality guard over the acceptance note:
  `grep -i -n -E '\bBA\b|DPL|AMM|Arbeitsagentur|Arbeitsmarktmonitor|dpl-|gas2gas|weaver|munoreqa|tabler-test|lm/application' superpowers/notes/2026-10-22-migrating-to-1.0-acceptance.md`
  → no output.

### Task 2: Page skeleton, nav, step zero

**Files:**
- Create: `docs/migrating-1.0.md`
- Modify: `docs/.pages` (add `- Migrating to 1.0.0: migrating-1.0.md` right after `- Home: index.md`)
- Modify: `CHANGELOG.md` (one line under `## Unreleased`, before `### Breaking`:
  `Upgrading from 0.29.x? See [Migrating to 1.0.0](docs/migrating-1.0.md).`)

**Interfaces:**
- Consumes: the inventory (Task 1).
- Produces: the page with these H2 headings, which later tasks fill in and link to:
  `## Who this is for`, `## Step zero: run the checks`, `## An app on the stock bootstrap5 theme`,
  `## A downstream theme`, `## Silent breaks`. The 0.30 marker convention chosen here (builder's call: a
  `*(0.30)*` suffix on the step heading, or an admonition) is used by every later task.

- [ ] **Step 1: Write `## Who this is for`.** Coming from 0.29.x. Explain the 0.30 marker. One sentence that the
  CHANGELOG stays the full record.
- [ ] **Step 2: Write `## Step zero: run the checks`.** Upgrade, run `python manage.py check`, fix everything.
  A table with the columns `Code | Raised when | Replaces / do this`, with a row for each of `crud_views.E350`,
  `E351`, `E354`, `E355`, `E356`, `W352`, `W353`, `E360`, `E361`, `W362`, `E106`, and `viewset.E209`, `E210`,
  `E211`, `E250`, `W246`, `W291`. Copy each meaning from its definition: `src/crud_views/lib/icons.py`,
  `src/crud_views/checks.py`, `src/crud_views/lib/button_classes.py`, `src/crud_views/lib/settings.py`,
  `src/crud_views/lib/view/{variant,label_mode,action_menu,base}.py`,
  `src/crud_views_object_detail/lib/mixins.py`. Below the table: runtime errors, the `TypeError` from an old
  `cv_get_context()` signature (#216) and the `ValueError` from `cv_no_label`, each with its fix.
- [ ] **Step 3: Leave stub headings** for sections 3–5, each with one line saying what it covers.
- [ ] **Step 4: Verify.** `.venv/bin/mkdocs build --strict -d <scratchpad>/site` exits 0. The page shows second in
  the nav.
- [ ] **Step 5: Commit** after the confidentiality guard:
  `docs(migrating): page skeleton, nav entry and step zero (#253)`.

### Task 3: An app on the stock bootstrap5 theme

**Files:**
- Modify: `docs/migrating-1.0.md` (`## An app on the stock bootstrap5 theme`)
- Modify, only if wrong: the reference pages the section links to; `CHANGELOG.md` for gap rows

**Interfaces:**
- Consumes: the inventory rows with reader `app` or `both`.

- [ ] **Step 1: Write the subsections in this order:** `### Base template`, `### Settings`,
  `### Views and Python code`, `### JavaScript`, `### CSS and tests that select on markup`. Each step reads
  "if you have X, do Y", has a before/after only where it saves a lookup, and ends with a reference link and
  `(#nnn)`. Required content, as rows:
  - Base template: `django-bootstrap5` dropped and `{% cv_messages %}` (#221); `crud_views/css/icons.css` for
    hand-listed CSS *(0.30)*.
  - Settings: the removed icon settings → `CRUD_VIEWS_ICONS` and the `BOOTSTRAP_ICONS` recipe *(0.30)*;
    `CRUD_VIEWS_FILTER_RESET_BUTTON_CSS_CLASS` → `CRUD_VIEWS_BUTTON_CLASSES = {"form:filter-reset": ...}`.
  - Views and Python: `cv_modal_size` tokens; `cv_get_context(..., location=...)`; `cv_no_label` →
    `cv_label_mode`; card buttons now render their icon too, and `cv_card_actions_label_mode = "label"` restores
    the old markup; `CardAction.variant` defaults to the target view's variant; object-detail group icons need a
    prefix *(0.30)*; the removed tags `cv_submit_button`, `cv_cancel_button`, `cv_delete_button`, and
    `cv_filter_icon` / `cv_get_filter_icon()` *(0.30)*.
  - JavaScript: `cv.cvModalOpen` and `data-cv-modal-size` tokens; jQuery only for formsets; Bootstrap tooltips and
    the opt-out `cv.adapters.tooltip = {init() {}}`.
  - CSS and tests: the DOM changes rows, sort icons *(0.30)*, pagination (#241), `hidden` instead of `d-none`
    (#232), formset control titles (#202).
- [ ] **Step 2: Gap rows** of reader `app` flagged `no CHANGELOG bullet`: add the bullet under
  `## Unreleased` → `### Breaking`, then the step.
- [ ] **Step 3: Verify.** Every `app`/`both` inventory row is cited in this section (tick them off in the
  acceptance note); `mkdocs build --strict` exits 0.
- [ ] **Step 4: Commit** after the guard: `docs(migrating): the stock bootstrap5 app section (#253)`.

### Task 4: A downstream theme

**Files:**
- Modify: `docs/migrating-1.0.md` (`## A downstream theme`)
- Modify, only if wrong: `docs/reference/theme.md`, `buttons.md`, `icons.md`, `messages.md`, `javascript.md`,
  `card-list-view.md`; `CHANGELOG.md` for gap rows

**Interfaces:**
- Consumes: the inventory rows with reader `theme` or `both`, and the scan's override list (private).

- [ ] **Step 1: Write the subsections in this order:** `### Templates you can delete` (a hook now does it, e.g.
  `snippets/pagination.html` overridden only for arrows → map `page-previous` / `page-next`),
  `### Templates to move` (the logic templates → `tags/button/action.html`, `menu_item.html`, `container.html`;
  `tags/actions_menu_item_label.html` → `tags/button/menu_item_label.html`; `tags/messages.html` →
  `tags/alert.html`), `### Hooks instead of copies` (class table keys including `alert:*`, `card:*` and the utility
  slots; `register_icon_library` / `register_icons` and the icon names; `snippets/form_frame.html` and its
  `cv_form_frame` block; the card blocks `card_title` / `card_content` / `card_actions`; `tags/alert.html` with
  `snippets/alert/text.html` and `list.html`; `cv.adapters`), and `### Contract changes in templates you still
  override` (`cv_icon_action` / `cv_icon_header` / `cv_menu_icon` through `{% cv_icon %}` *(0.30)*;
  `cv_label_mode`; `tags/icon.html`, `cv_header_icon_class`, `cv_filter_icon_class` removed *(0.30)*;
  `fa-fw` → `cv-icon-fw` *(0.30)*; `#filter-collapse` and the filter toggle's `aria-expanded` / `aria-controls`
  and `hidden`; `data-cv-modal-dismiss` and `modal/shell.html`; `data-cv-class` / `data-cv-class-danger` on
  `formsets/control.html`; `cv_menu_wrapper_class` / `cv_toggle_class` gone → `{% cv_button_class %}`). One
  sentence that `crud_views_tabler` ships its own update for 1.0.
- [ ] **Step 2: Coverage against the private scan.** Every scanned override touched by an inventory row maps to a
  step here or in Task 3. Tick them off in the scratch file only.
- [ ] **Step 3: Gap rows** of reader `theme`: CHANGELOG bullet plus step, as in Task 3.
- [ ] **Step 4: Verify.** Every `theme`/`both` inventory row is cited; `mkdocs build --strict` exits 0.
- [ ] **Step 5: Commit** after the guard: `docs(migrating): the downstream theme section (#253)`.

### Task 5: Silent breaks, the keep-current rule, the CHANGELOG entry

**Files:**
- Modify: `docs/migrating-1.0.md` (`## Silent breaks`)
- Modify: `CLAUDE.md` (one bullet under `## Conventions`)
- Modify: `CHANGELOG.md` (`### Added`)

- [ ] **Step 1: Write `## Silent breaks`** as a `- [ ]` checklist: one line per inventory row flagged `silent`,
  each linking to its step. It must include at least the spec's eight: the old `tags/messages.html` override; the
  `modal-lg` size from JS or HTML; `class="d-none"` in `context_action_filter.html`; the
  `tags/actions_menu_item_label.html` override; bare group icon `icon="truck"`; `<i class="{{ cv_icon_action }}">`;
  `formsets/control.html` without `data-cv-class`; CSS or tests on `.disabled > span.page-link`, the
  `&laquo;`/`&raquo;` arrows or old button class strings.
- [ ] **Step 2: `CLAUDE.md` rule**, verbatim:
  `- Until 1.0.0 ships, a change that adds a \`### Breaking\` entry to \`CHANGELOG.md\` also updates \`docs/migrating-1.0.md\`.`
- [ ] **Step 3: CHANGELOG** under `## Unreleased` → `### Added`, first bullet:
  `- [Migrating to 1.0.0](docs/migrating-1.0.md): the route from 0.29.x for an app on the stock theme and for a downstream theme, with a checklist of the breaks that raise nothing (#253).`
- [ ] **Step 4: Verify.** Every `silent` inventory row appears in the checklist. Every *(0.30)* step agrees with
  the "net state" column (Review Focus 1). `.venv/bin/mkdocs build --strict` exits 0. `task format` leaves the
  Markdown unchanged after re-staging (see memory `ci-ruff-formats-markdown`).
- [ ] **Step 5: Commit** after the guard: `docs(migrating): silent-break checklist and the keep-current rule (#253)`.

### Task 6: Acceptance note, review, PR

**Files:**
- Modify: `superpowers/notes/2026-10-22-migrating-to-1.0-acceptance.md`

- [ ] **Step 1: Finish the note.** The inventory with every row ticked and its section; CHANGELOG/code mismatches
  found; reference pages fixed; CHANGELOG bullets added for gaps. Mention that a private downstream scan was run
  and how many gaps it closed, but don't name or describe the projects.
- [ ] **Step 2: Whole-branch review** by one fresh reviewer, given the spec, the plan and `git diff main...` (not
  the scratch file). Fix what it confirms.
- [ ] **Step 3: Final guard over the whole branch:**
  `git diff main... | grep -i -n -E '\bBA\b|DPL|AMM|Arbeitsagentur|Arbeitsmarktmonitor|dpl-|gas2gas|weaver|munoreqa|tabler-test|lm/application'`
  → no output. `pytest tests -n auto` passes (nothing in `src/` changed, so this only guards the docs-adjacent
  tests such as `tests/test1/test_no_django_bootstrap5.py`).
- [ ] **Step 4: Commit the note, push, open the PR** with `.github/PULL_REQUEST_TEMPLATE.md`, "Closes #253", and
  the guard run once more over the PR title and body.
