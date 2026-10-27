# Roadmap: django-crud-views — Concept Review Follow-ups

## Overview

This milestone lands the five ranked findings of the icons/buttons/theming concept review before 1.0.0. It follows
the phase plan in `superpowers/plans/2026-10-24-concept-review-followups.md`, one roadmap phase per plan phase and one
branch/PR each. The work starts with two foundations that can run in parallel: a single label-mode floor (plan 1A) and
the `form:*` key grammar (plan 1C). Three independent fixes follow in parallel: the filter toggle (1B), the alert
dismiss adapter (3A) and table pagination (3B). Then comes the one large breaking change, form buttons through a
crud_views leaf (plan 2). The milestone closes by freezing the whole theme surface in `stability.md` with a guard test
(plan 4). The ordering exists so that no public theme name changes twice.

## Phases

**Phase Numbering:**

- Integer phases (1–7): planned milestone work. Each maps to one source-plan phase (noted as "plan 1A" etc.).
- Decimal phases (2.1, 2.2): urgent insertions (marked with INSERTED).

Numeric order is a valid execution order. The dependency graph also allows parallel waves (see Progress).

- [x] **Phase 1: Label-mode defaults** - plan 1A: one project-wide label-mode floor per location (`CRUD_VIEWS_LABEL_MODE_DEFAULTS`, E108) (completed 2026-10-26)
- [x] **Phase 2: Form key grammar** - plan 1C: Option A form kinds implemented, reviewed and verified (completed 2026-10-26)
- [x] **Phase 3: Filter toggle label mode** - plan 1B (#262): the filter toggle honours `icon` / `both` / `label` (completed 2026-10-26)
- [x] **Phase 4: Alert dismiss adapter** - plan 3A: alerts close through `cv.adapters.alert` with no Bootstrap data API (droppable) (completed 2026-10-26)
- [ ] **Phase 5: Table pagination parity** - plan 3B: table pagination gets the same registry icons and accessible markup as card pagination (droppable)
- [ ] **Phase 6: Form-button leaf** - plan 2 (#257): crispy form buttons render as `<button>` through `tags/button/form.html`
- [ ] **Phase 7: Theme-surface stability policy** - plan 4: `stability.md` freezes the theme surface; a guard test checks it in both directions

## Phase Details

### Phase 1: Label-mode defaults

**Goal**: A project sets the label-mode default for each location in one place, and every location reads that floor
from a single accessor. With no configuration, output is unchanged.
**Source**: plan 1A · branch `feat/label-mode-defaults`
**Depends on**: Nothing (first phase). Can run in parallel with Phase 2.
**Parallel with**: Phase 2
**Research/spec**: Not needed (standard pattern: copy the class table's lazy per-key merge). Raise these in the
discussion because Phase 7 depends on them: the `cv_context_action(s)_label_mode` pair, `no_label`, and E108 severity
for unknown keys.
**Requirements**: LMOD-01, LMOD-02, LMOD-03, LMOD-04, LMOD-05, LMOD-06
**Success Criteria** (what must be TRUE):

  1. With `CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"context": "both"}`, every unmapped toolbar button renders icon + text on
     every page. Rows and cards are unchanged, and W292 stops firing for those keys.
  2. `{"card": "label"}` restores the 0.29 card look without touching a view. An explicit
     `cv_card_actions_label_mode = "both"` on a view still wins.
  3. A test using `override_settings` changes the resolved default. An invalid mode outside strict mode logs and falls
     back instead of raising.
  4. An unknown location key or an invalid mode in the setting is reported by `crud_views.E108`. Valid keys come from
     the set of locations, not from a literal.
  5. `grep -n '"both" if card\|or "icon"\|get(key, "icon")' src/crud_views/lib/view/*.py` returns nothing. Goldens
     stay byte-identical, and the docs state per-key merge vs whole-dict replacement for each knob.
**Plans**: 5/5 plans complete (4 executed; 1 gap-closure plan ready)

Plans:
**Wave 1**

- [x] 01-01-PLAN.md — Lazy defaults through the real button leaf, strict/log recovery and E108

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 01-02-PLAN.md — Toolbar/list integration, precedence preservation and W292 check safety
- [x] 01-03-PLAN.md — Card resolver, None attribute and compatibility migration

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 01-04-PLAN.md — Canonical configuration docs, decision handoff and final quality gates

**Wave 4** *(gap closure after completed Waves 1–3)*

- [x] 01-05-PLAN.md — Restore instance card modes, preserve resolver hooks and clarify effective-mode guidance

**UI hint**: no (settings and resolution only; no markup change)

### Phase 2: Form key grammar

**Goal**: The class table has one documented, check-enforced rule for what the second key segment means and which
keys take a mode, so form buttons can get mode keys without loosening W362.
**Source**: plan 1C · branch `feat/form-key-grammar`
**Depends on**: Nothing. Can run in parallel with Phase 1.
**Parallel with**: Phase 1
**Research/spec**: Decision settled in 02-CONTEXT.md: Option A `form:<kind>:<mode>` retains form kinds;
context/list/card retain variants. Implementation, external review, human prose UAT and phase verification are complete.
**Requirements**: KEYS-01, KEYS-02, KEYS-03, KEYS-04
**Success Criteria** (what must be TRUE):

  1. `docs/reference/buttons.md#the-class-table` states the chosen grammar: the meanings of the second segment and
     which of them take a mode.
  2. W362 accepts form mode keys of the chosen shape and rejects malformed ones such as `form:submitt:icon` and
     `form:container:icon`.
  3. The location sets are split explicitly (e.g. `VARIANT_LOCATIONS`, `FORM_KINDS`), so adding `"form"` to the
     button-data locations cannot make W362 accept `form:<variant>:<mode>`.
  4. The key count quoted in `buttons.md` is correct, and a test fails whenever it drifts from
     `len(DEFAULT_BUTTON_CLASSES)`. There is no runtime or golden change.
**Plans**: 1/1 plans complete
- [x] 02-01-PLAN.md

**UI hint**: no (checks and docs only)

### Phase 3: Filter toggle label mode

**Goal**: The list filter toggle follows the configured label mode like every other context button, and stays
accessible in each mode.
**Source**: plan 1B (#262) · branch `feat/filter-toggle-label-mode`
**Depends on**: Phase 1
**Parallel with**: Phases 4 and 5
**Research/spec**: Decisions settled in 03-CONTEXT.md; mode/placement, target-default, constant-label and
disclosure contracts implemented and verified. Human UAT passed all four checks; review fixes preserve
independent list-row modes and the shared runtime validation policy.
**Requirements**: FILT-01, FILT-02, FILT-03, FILT-04
**Success Criteria** (what must be TRUE):

  1. `CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE = {"filter": "both"}` renders icon + "Filter" with no `title`. `"label"`
     renders the text only. The default `icon` output is byte-identical (`toolbar_publisher_list.html` golden).
  2. In `label` mode (no icon spans), clicking the toggle still flips `aria-expanded` and persists the open/closed
     state (vitest label-only case).
  3. The toggle's visible text never changes between states. Only `aria-expanded` and the icon change.
  4. "Filter" is a translated msgid and renders in German with the German catalog.

**Plans**: 2/2 plans complete
**Wave 1**
- [x] 03-01-PLAN.md

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 03-02-PLAN.md

**UI hint**: no (template branch in an existing component; no new screens)

### Phase 4: Alert dismiss adapter

**Goal**: Dismissible alerts close through the `cv.adapters` seam, so a non-Bootstrap theme no longer copies the
alert frame for a single `data-bs-*` attribute.
**Source**: plan 3A · branch `feat/alert-dismiss-adapter`
**Depends on**: Nothing (independent). Must merge before Phase 7.
**Parallel with**: Phases 3 and 5 (and with anything else)
**Droppable**: Yes. If 1.0.0 must ship early, drop this phase; Phase 7 then lists `tags/alert.html` as a known
Bootstrap-DOM template in `theme.md`.
**Research/spec**: Not needed. Decide in the discussion: add `alert:*` class keys for the frame's literal classes, or
document the frame override in `theme.md` (LATER-06 tracks the keys).
**Requirements**: ALRT-01, ALRT-02, ALRT-03, ALRT-04
**Success Criteria** (what must be TRUE):

  1. A golden of today's dismissible alert is committed first, so the PR shows the markup diff.
  2. Clicking an alert's close button closes it through `cv.adapters.alert.close`, with Bootstrap's `Alert` present.
     Without it, the alert is removed. Alerts injected after page load (e.g. inside a modal) close too.
  3. The stock frame renders `data-cv-alert-dismiss` and no `data-bs-dismiss`. `grep -rn 'data-bs-'
     src/crud_views/templates` lists only the dropdown templates named in `theme.md`.
  4. The example project's flash messages still close. `javascript.md`, `messages.md`, `theme.md`, the CHANGELOG
     Breaking entry and the migration bullet are updated.
**Plans**: 3/3 plans complete

Plans:
**Wave 1**
- [x] 04-01-PLAN.md — Commit the current golden, deliver the rendered dismiss tracer and preserve message rendering

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 04-02-PLAN.md — Prove namespace, dynamic-content and custom/component ownership contracts

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 04-03-PLAN.md — Publish references and migration, then record browser acceptance and final quality gates

Execution waves: 1 = 04-01; 2 = 04-02; 3 = 04-03. The first task commits only the baseline before product edits.

**UI hint**: no (one DOM attribute and JS adapter; no new screens)

### Phase 5: Table pagination parity

**Goal**: Table and card pagination look and behave the same: registry icons, hidden labels and the same accessible
structure.
**Source**: plan 3B · branch `feat/table-pagination-icons`
**Depends on**: Nothing (independent). Rebase after Phase 2 (the key-count line). Must merge before Phase 7.
**Parallel with**: Phases 3 and 4 (and with anything else)
**Droppable**: Yes. If 1.0.0 must ship early, drop this phase; Phase 7 then documents the surface as it is.
**Research/spec**: Not needed. The hidden-label key name is the maintainer's call (PAGE-03 says shared
`pagination:hidden-label`; the plan suggested `table:hidden-label`). Confirm it in the discussion, before Phase 7
freezes it.
**Requirements**: PAGE-01, PAGE-02, PAGE-03, PAGE-04
**Success Criteria** (what must be TRUE):

  1. A golden of today's paginated table is committed first, so the PR shows the markup diff.
  2. A paginated table shows `page-previous` / `page-next` registry icons with translated hidden labels,
     `aria-current="page"` on the active page, non-focusable disabled ends (`aria-disabled="true"`), and a translated
     `<nav>` label. Existing tables2 block names still work for overrides.
  3. One shared hidden-label class key (default `visually-hidden`) is read by both table and card pagination.
     Changing it changes both.
  4. Table and card pagination produce the same accessible structure. The CHANGELOG Breaking (DOM) entry, the
     migration bullet and the `.po` files are updated.
**Plans**: 3 plans
**Wave 1**
- [ ] 05-01-PLAN.md — Commit table baselines, deliver accessible pagination and the shared hidden-label key.

**Wave 2** *(blocked on Wave 1 completion)*
- [ ] 05-02-PLAN.md — Verify overrides, query/range behavior and table/card accessibility parity.

**Wave 3** *(blocked on Wave 2 completion)*
- [ ] 05-03-PLAN.md — Publish migration guidance, refresh catalogs and record acceptance checks.

**UI hint**: no (markup parity in an existing template; no new screens)

### Phase 6: Form-button leaf

**Goal**: Crispy form buttons render as real `<button>` elements through a crud_views leaf, share the action-button
label-mode and class-table contract, and are safe against template injection. With no configuration, POST data is
unchanged.
**Source**: plan 2 (#257) · branch `feat/form-button-leaf`
**Depends on**: Phase 1 (the `"form"` floor) and Phase 2 (form mode keys, location split)
**Parallel with**: None. This is the last code phase. Start its spec only after Phases 1 and 2 are on `main`.
**Research/spec**: **Needs its own spec** (brainstorm) before implementation; highest risk. The spec must settle:

  - the filter buttons' move from `add_input()` into `FormActions`, and a user `formhelper_class` that still calls
    `add_input`
  - the view lookup order
  - dropping value templating
  - one `LEAF_KEYS` set or a separate `FORM_LEAF_KEYS`
  - `form:icon-host`
  - whether an explicit `template=` kwarg is honoured or rejected
  - the crispy floor session

It must also verify Django 6.0's `format_html` removal and jsdom `SubmitEvent.submitter` support.
**Requirements**: FORM-01, FORM-02, FORM-03, FORM-04, FORM-05, FORM-06, FORM-07, FORM-08, FORM-09, FORM-10,
FORM-11, FORM-12, FORM-13
**Success Criteria** (what must be TRUE):

  1. With nothing configured, create, update, delete, cancel and both filter buttons render as `<button type="…">`
     with the same text, classes, `name`, `value` and `id`. `test_delete` posts `{"delete": "Delete"}` unchanged, and
     `#filter-button-reset` is preserved. Before-change goldens show the diff.
  2. `CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"form": "both"}` shows icon + text on save, delete, cancel and both filter
     buttons. `{"form": "icon"}` shows icon-only buttons with a visually hidden label, `title` and
     `data-cv-tooltip="form"`. Setting → ViewSet → view per-key maps and `form:<kind>:<mode>` class keys apply.
  3. A button label or value containing `<b>`, `"><script>` or `{{ request.user }}` renders as escaped plain text in
     both the button body and the `value` attribute.
  4. The workflow submit shows the `workflow` icon and a per-form `submit_icon` wins. An icon-only form button with no
     icon is reported by W292, raises in strict mode, and otherwise logs and renders the label. E210/E211/W291 cover
     the form maps.
  5. The CHANGELOG `### Breaking` entry and the "Form buttons" section of `docs/migrating-1.0.md` exist. The example
     project shows `both` for submit, delete and cancel, and the Tabler follow-up is written into the acceptance note.
**Plans**: TBD
**UI hint**: no (new leaf template replaces existing button markup; no new screens)

### Phase 7: Theme-surface stability policy

**Goal**: Theme authors can see exactly which names they may rely on at 1.0.0, and a test stops any public theme name
from shipping undocumented or being documented without existing.
**Source**: plan 4 · branch `docs/stability-theme-surface`
**Depends on**: Phase 6, Phase 4 and Phase 5 (and so, transitively, Phases 1 and 2). It merges last, before the 1.0.0
bump. If Phases 4/5 are dropped, it depends on Phase 6 only and documents the surface as it is.
**Parallel with**: None
**Research/spec**: **Needs a maintainer decision/spec**:

  - the tier assignments
  - a public `is_library_renderer` helper
  - whether the reference theme's private imports are acceptable
  - how to mark the undecided label-mode pair and `no_label` (done, or provisional/deprecated)

**Requirements**: STAB-01, STAB-02, STAB-03, STAB-04, STAB-05, STAB-06
**Success Criteria** (what must be TRUE):

  1. `docs/development/stability.md` names every theme-surface item explicitly, with no wildcards, and classifies each
     as stable, provisional or internal. Items: icons, class-table keys, leaf templates and their context, alerts,
     `cv.adapters` methods, events, DOM contract, theme hooks, check IDs, `CRUD_VIEWS_*` settings and dependency
     floors.
  2. `tests/test1/test_stability_doc.py` fails if a documented name no longer exists, or if a code-derived public name
     is undocumented. Code-derived sources: `DEFAULT_ICONS`, `DEFAULT_BUTTON_CLASSES`, `LEAF_KEYS`, `LOCATIONS`,
     leaf files on disk and JS adapter keys.
  3. A theme can detect a library renderer through a public helper (`is_library_renderer` or equivalent) instead of
     importing `_get_renderers` / `_icon_str`.
  4. `theme.md` links to "what a theme may rely on", `mkdocs build --strict` passes, and the theme part of #89 is
     closed.
**Plans**: TBD
**UI hint**: no (docs and tests only)

## Progress

**Execution Order:**
Numeric order (1 → 2 → 3 → 4 → 5 → 6 → 7) is valid. With parallelization, run in waves:

| Wave | Phases | Notes |
|------|--------|-------|
| 1 | 1 (plan 1A) ∥ 2 (plan 1C) | Disjoint files; both are preconditions of Phase 6 |
| 2 | 3 (plan 1B) ∥ 4 (plan 3A) ∥ 5 (plan 3B) | 3 needs 1; 4 and 5 are independent (5 rebases after 2 for the key count) |
| 3 | 6 (plan 2) | Needs 1 and 2 on `main`; spec first |
| 4 | 7 (plan 4) | Needs 6, 4 and 5 merged; last change before the 1.0.0 bump |

Droppable if 1.0.0 must ship early: Phases 4 and 5 (plan 3A/3B).

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Label-mode defaults | 5/5 | Complete    | 2026-10-26 |
| 2. Form key grammar | 1/1 | Complete    | 2026-10-26 |
| 3. Filter toggle label mode | 2/2 | Complete    | 2026-10-26 |
| 4. Alert dismiss adapter | 3/3 | Complete    | 2026-10-26 |
| 5. Table pagination parity | 0/TBD | Not started | - |
| 6. Form-button leaf | 0/TBD | Not started | - |
| 7. Theme-surface stability policy | 0/TBD | Not started | - |
