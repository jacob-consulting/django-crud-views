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
- [x] **Phase 5: Table pagination parity** - plan 3B: table pagination gets the same registry icons and accessible markup as card pagination (droppable) (completed 2026-10-27)
- [x] **Phase 6: Form-button leaf** - plan 2 (#257): crispy form buttons render as `<button>` through `tags/button/form.html` (completed 2026-10-28)
- [x] **Phase 6.1: Cancel form button as a link (INSERTED)** - #275: themes can opt into native cancel links while preserving the button default (completed 2026-10-29)
- [x] **Phase 6.2: Request authorization and write integrity (INSERTED)** - analysis B1–B7: secure request paths, safe delete previews and truthful Guardian configuration before the freeze (completed 2026-10-30)
- [x] **Phase 6.3: Delete protection and write-boundary integrity (INSERTED)** - issue #282 (completed 2026-11-01)
- [x] **Phase 6.4: Conditional and formset correctness/lifecycle (INSERTED)** - analysis A1–A7: correct conditional state, server save behavior and dynamic formset initialization before the freeze (completed 2026-11-02)
- [x] **Phase 6.5: Remaining presentation contracts and decided cleanup (INSERTED)** - analysis #259/C1/C2 and decided alias cleanup before the freeze (completed 2026-11-02)
- [x] **Phase 6.6: Theme-adoption seams from the Tabler sync (INSERTED)** - issues #277–#280 before the freeze (completed 2026-11-03)
- [x] **Phase 6.7: Dynamic cancel navigation and origin query state (INSERTED)** - #302: dynamic defaults and reliable origin query restoration before the freeze (completed 2026-11-03)
- [x] **Phase 6.8: Action tooltips: short captions and visible-label suppression (INSERTED)** - #304: concise icon tooltips and no redundant generated tooltips on visible labels before the freeze (completed 2026-11-04)
- [x] **Phase 6.9: Protected delete-preview object links (INSERTED)** - #307: link visible protected blockers when related-object linking is enabled (completed 2026-11-04)
- [x] **Phase 6.10: Simplify protected-object previews and cap total displayed objects (INSERTED)** - #316: plain-text protected blockers and one shared preview display budget before the freeze (completed 2026-11-05)
- [x] **Phase 6.13: Workflow permissions: opt-in per-transition access (INSERTED)** - #320: document and test the existing view-gated recipe while preserving the default change gate (completed 2026-11-05)
- [x] **Phase 06.13.1: Workflow validation and execution (INSERTED)** - #322: business blockers, opt-in transition buttons, and a reusable execution helper (completed 2026-11-06)
- [x] **Phase 06.14: Card template insertion blocks and cards-first ViewSets (INSERTED)** - #325: empty card blocks and tested cards-first navigation (completed 2026-11-06)
- [x] **Phase 06.15: Polymorphic labels and per-model detail groups (INSERTED)** - #326: capitalize selector labels, validate model-specific groups, and adopt in tabler-test (completed 2026-11-06)
- [ ] **Phase 7: Theme-surface stability policy** - plan 4: `stability.md` freezes the theme surface; a guard test checks it in both directions

## Backlog decisions

The opt-in URL helper is tracked in [#314](https://github.com/jacob-consulting/django-crud-views/issues/314), outside this milestone.
The integrated URL/access phase was cancelled before implementation. Its plans and discussions remain in the
[retired archive](../superpowers/archive/2026-11-04-phase-06.10-object-derived-nested-urls-and-link-access-parity/README.md). The [maintainer decision](../superpowers/notes/2026-11-04-opt-in-url-helper-decision.md)
supersedes the old integration and prerequisite assumptions. #312 remains a separate open bug issue; neither issue
is a Phase 7 dependency. Phase 7 inventories the implemented surface only.

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
**Plans**: 3/3 plans complete
**Wave 1**

- [x] 05-01-PLAN.md — Commit table baselines, deliver accessible pagination and the shared hidden-label key.

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 05-02-PLAN.md — Verify overrides, query/range behavior and table/card accessibility parity.

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 05-03-PLAN.md — Publish migration guidance, refresh catalogs and record acceptance checks.

**UI hint**: no (markup parity in an existing template; no new screens)

### Phase 6: Form-button leaf

**Goal**: Crispy form buttons render as real `<button>` elements through a crud_views leaf, share the action-button
label-mode and class-table contract, and are safe against template injection. With no configuration, POST data is
unchanged.
**Source**: plan 2 (#257) · branch `feat/form-button-leaf`
**Depends on**: Phase 1 (the `"form"` floor) and Phase 2 (form mode keys, location split)
**Parallel with**: None. This is the last code phase. Before its spec, verify completed Phases 1 and 2 on the
current working branch and record its HEAD SHA plus contract evidence (user decision D-18; no merge to `main` required).
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
**Plans**: 10/10 plans complete

**Wave 1**

- [x] 06-01-PLAN.md

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 06-02-PLAN.md

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 06-03-PLAN.md

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 06-04-PLAN.md

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 06-05-PLAN.md

**Wave 6** *(blocked on Wave 5 completion)*

- [x] 06-06-PLAN.md

**Wave 7** *(blocked on Wave 6 completion)*

- [x] 06-07-PLAN.md
- [x] 06-08-PLAN.md

**Wave 8** *(blocked on Wave 7 completion)*

- [x] 06-09-PLAN.md

**Wave 9** *(blocked on Wave 8 completion; prerequisite complete)*

- [x] 06-10-PLAN.md — Preserve copied-layout icon defaults and normalize form icon values (gap closure)

**UI hint**: no (new leaf template replaces existing button markup; no new screens)

### Phase 06.14: Card template insertion blocks and cards-first ViewSets (#325) (INSERTED)

**Goal:** Consumers can extend cards at two empty insertion blocks and configure cards as a ViewSet's landing page with a secondary table, with executable documentation preserving existing rendering, actions, permissions and independent navigation/query-state behavior.
**Requirements**: TBD
**Depends on:** Phase 6
**Plans:** 2/2 plans complete

**Acceptance:** `card_root` is first inside the card root and `card_header` precedes the heading inside the body; unused blocks preserve output and inherited actions/forms. The complete tested recipe registers cards as `list` at the root and table as `table` at `table/`, with switching, home/breadcrumbs, default Save, static Cancel and explicitly allowed table-origin Cancel verified. Card-only fallback and table-first defaults remain unchanged. No routing redesign or downstream-theme implementation.

Plans:
**Wave 1**
- [x] 06.14-01-PLAN.md — Add and verify empty card insertion blocks and the five-block inheritance contract (wave 1)

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 06.14-02-PLAN.md — Publish executable cards-first/table-secondary configuration, prove navigation and preserve compatibility (wave 2)

### Phase 6.1: Cancel form button as a link (INSERTED)

**Goal**: Themes and individual forms can render cancel controls as native navigation links without copying the form
leaf, while unconfigured forms retain today's button markup and behavior.
**Source**: [Issue #275 — Render the cancel form button as a link](https://github.com/jacob-consulting/django-crud-views/issues/275)
**Requirements**: TBD
**Depends on**: Phase 6. Must complete before Phase 7 freezes the theme surface.
**Parallel with**: None
**Success Criteria** (what must be TRUE):

  1. `form:cancel-tag` accepts `button` (default) or `a`, is registrable through `register_button_classes()` and
     overridable through `CRUD_VIEWS_BUTTON_CLASSES`, and participates in the existing W362 key validation.
  2. An explicit `Button(tag=...)` overrides the class-table choice. A cancel control with a URL and resolved tag `a`
     renders a native `<a href>`; without a cancel URL it remains a button regardless of the configured tag.
  3. The link retains the button's id, classes, label mode, icon and applicable extra attributes, omits `name`,
     `value`, `type` and `data-cv-cancel-url`, and navigates without JavaScript, including opening in a new tab.
  4. `cv_tag` is included in `FORM_LEAF_KEYS` and documented with the new key and per-button override. Default button
     markup and behavior remain unchanged, `viewset.js` stays unchanged, and existing custom templates remain usable.
**Plans**: 3/3 plans complete

Plans:
**Wave 1**
- [x] 06.1-01-PLAN.md

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 06.1-02-PLAN.md

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 06.1-03-PLAN.md

**UI hint**: no (tag choice in the existing form leaf; no new screens)

### Phase 6.2: Request authorization and write integrity (INSERTED)

**Goal**: Close the request authorization and write-integrity gaps in B1–B6 and settle B7's effective Guardian
configuration before the theme-surface freeze. Authorization and safe context construction remain library-owned.
**Source**: `superpowers/notes/2026-10-28-pre-1.0-before-theme-freeze-analysis.md`, §3 (B1–B7), §8 (slice 6.2), §9 (decisions 1 and 4).
**Canonical refs**: `superpowers/notes/2026-10-28-pre-1.0-before-theme-freeze-analysis.md`; `docs/reference/guardian.md`; `docs/migrating-1.0.md`.
**Requirements**: AUTH-01, AUTH-02, AUTH-03, AUTH-04, AUTH-05, AUTH-06, AUTH-07
**Depends on**: Phase 6.1 for execution order; uses existing core delete/formset and Guardian composition.
Must complete before Phase 7 freezes the affected contracts.
**Parallel with**: None
**Research/spec**: Discuss HTTP DELETE policy (reject or equivalent validated lifecycle), safe protected-object
preview context, and Guardian global-permission configuration/helper/manage-display semantics. The source note's
recommendations are proposals, not locked decisions.
**Success Criteria** (what must be TRUE):

  1. B1: Every allowed deletion method preserves permission, action-state, confirmation/form validation,
     deletion-protection, hooks and transaction/rollback boundaries. HTTP DELETE is explicitly rejected or follows
     the complete validated lifecycle; it cannot inherit a direct-delete bypass.
  2. B2: Formset fragments authorize the target and validate URL-parent/fragment coordinates before rendering.
     Ungranted, revoked, inactive, state-disabled, wrong-parent and missing-object requests disclose no form data
     or choices; authorized fragments retain the documented request and `{html, rows}` protocol.
  3. B3: Protected related objects are filtered before entering template context. No/partial/full related-view
     grants reveal only permitted labels, while deletion remains visibly blocked even if all labels are hidden.
  4. B4/B6: Parent permission `None` retains parent resolution and independent action-state checks. Create
     visibility/access helpers and direct GET/POST agree without crashes or requiring a new child-add grant.
  5. B5: Inactive users, including inactive superusers and group/object grant holders, receive no unauthorized
     rows or object access even when an authentication backend permits inactive sessions.
  6. B7: Guardian has a documented effective global-permission policy. View behavior, the ViewSet helper and
     manage diagnostics are truthful; removal/clarification or inheritance of the inert ViewSet flag is
     explicitly decided and covered by regressions.
  7. Direct-request actor-matrix regressions and native list/card/action/manage/alert/formset overrides prove
     server enforcement independently of presentation. Preserve intentional aggregate purge authority and
     existing parent/global safeguards. Document changed access/config/context behavior; every Breaking entry
     has a paired `docs/migrating-1.0.md` update.

**Scope exclusions**: Conditional/formset lifecycle work A1–A7 (proposed 6.4), presentation/alias cleanup
(proposed 6.5), Tabler theme-adoption seams (proposed 6.6), the jQuery port, and the final stability inventory. Do not reopen completed Phase 6/6.1 acceptance.
**Transfer closure (2026-11-01)**: Phase 6.3 passed 91/91 and completes the transferred deletion and bounded Guardian obligations. Broader Guardian identity compatibility remains unverified under issue #286. The following 2026-10-30 transfer table is historical; A19/A25 and other separate exclusions retain their own dispositions.

**Acceptance reconciliation (2026-10-30)**: All nine plans executed; retained 6.2 scope verified and UAT completed on 2026-10-30, including the final Playwright blocked-delete check. [Issue #282](https://github.com/jacob-consulting/django-crud-views/issues/282) defers
**unresolved CR-02–CR-04 to Phase 6.3** as remediation of this phase's existing promises, not scope erasure.

| Existing criterion / requirement | Retained 6.2 evidence | Outstanding acceptance |
| --- | --- | --- |
| 1 / AUTH-01 | DELETE 405 and named POST lifecycle controls | Callback-safe inspection, unknown converter propagation, database alignment → 6.3 DEL-02/03/04 |
| 3 / AUTH-03 | Filtered protected labels, independent notice, fixed CR-01/WR-02 scope | Callback-free, target-database blocked-state determination → 6.3 DEL-02/04/05 |
| 7 / AUTH-07 | Actor/native-template replay, paired docs | Real-preview/error/routing evidence, preserved authorization and re-review → 6.3 DEL-01–06 |
| 4 / AUTH-04 | Parent-None dispatch and Guardian helper/state cases | WR-01 core rendered-state agreement fixed in quick 261030-csg; final post-fix Playwright UAT passed |
| 2, 5, 6 / AUTH-02/05/06 | Named fragment/inactive/configuration cases | Preserve A19 (proposed 6.4); AUTH-06 residual review and IN-02/03 → 6.3 GUA-01; other findings retain separate dispositions |

See [REQUIREMENTS](REQUIREMENTS.md#acceptance-ownership-split-2026-10-30),
[06.2-ACCEPTANCE](phases/06.2-request-authorization-and-write-integrity/06.2-ACCEPTANCE.md#acceptance-ownership-split-for-issue-282)
and [06.2-REVIEW-DISPOSITION](phases/06.2-request-authorization-and-write-integrity/06.2-REVIEW-DISPOSITION.md).
AUTH-06 residual review and IN-02/IN-03 are explicitly transferred unresolved to 6.3 GUA-01.
WR-01 is fixed by quick 261030-csg (bd31992). IN-01/IN-04 are closed with explicit policy/limitation rationale; IN-05 is fixed.
The revised analysis §8 puts conditional/formset, presentation and Tabler proposals at 6.4/6.5/6.6; only 6.3 is
inserted here. Phase 7 remains last and cannot freeze the affected promises before remediation.

**Plans**: 9/9 plans complete; final automated gates refreshed; canonical verification passed; final Playwright UAT passed; 6.3 transfers completed within reconciled scope on 2026-11-01

Plans:
**Wave 1**
- [x] 06.2-01-PLAN.md — Reject DELETE and secure protected preview context; retain POST integrity

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 06.2-02-PLAN.md — Enforce parent-None state and inactive actor denial

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 06.2-03-PLAN.md — Authorize fragments and validate saved/unsaved ancestry
- [x] 06.2-04-PLAN.md — Remove inert configuration and report per-view manage policy

**Wave 4** *(blocked on Wave 3 completion)*
- [x] 06.2-05-PLAN.md — Replay direct actor and native template matrices

**Wave 5** *(blocked on Wave 4 completion)*
- [x] 06.2-06-PLAN.md — Document migrations and record supported-version evidence

**Gap closure** *(UAT 2026-10-29, gaps G-06.2-1 and G-06.2-3; sequential waves 1-3)*
- [x] 06.2-07-PLAN.md — Guardian delete preview fails closed per model: _PermittedPks resolves against guardian's content type (G-06.2-1 / CR-01)
- [x] 06.2-08-PLAN.md — Blocked deletions: notice without a form, blocked POST 200/422 with exception backstop, flag on every delete page, copy and German catalog (G-06.2-3 / WR-02)
- [x] 06.2-09-PLAN.md — Document both closures, pair CHANGELOG with migrating-1.0.md, update ACCEPTANCE/disposition and re-measure both cached environments

**UI hint**: no (backend enforcement and safe existing template contexts; no new screens)

### Phase 06.3: Delete protection and write-boundary integrity — issue #282 (INSERTED)

**Acceptance scope (2026-11-01):** Guardian identity review is bounded to the tested integer/UUID, exact-key,
queryset/model/type and same-alias predicates in
[06.3-SCOPE-RECONCILIATION](phases/06.3-delete-protection-and-write-boundary-integrity-issue-282/06.3-SCOPE-RECONCILIATION.md).
Broader custom-PK/backend-cast/collation compatibility remains unverified follow-up in issue #286,
outside this phase's completion gate. Four unclassified detector fallbacks are dismissed with recorded reasons.

**Goal**: Remediate unresolved Phase 6.2 CR-02–CR-04: protection inspection respects confirmation/write
boundaries, unknown application failures propagate, and inspection/deletion use the same target database.
Also complete a bounded Guardian policy review of the residual AUTH-06 detector flag and IN-02/IN-03,
preserving 6.2’s implemented and tested policy behavior.
**Source**: [Issue #282](https://github.com/jacob-consulting/django-crud-views/issues/282);
`superpowers/notes/2026-10-28-pre-1.0-before-theme-freeze-analysis.md` addendum 2026-10-30 and §8;
[06.2-REVIEW](phases/06.2-request-authorization-and-write-integrity/06.2-REVIEW.md).
**Requirements**: DEL-01, DEL-02, DEL-03, DEL-04, DEL-05, DEL-06, GUA-01; completes affected AUTH-01/03/07 obligations and owns the residual AUTH-06 review.
**Depends on**: Phase 6.2 implementation/evidence baseline; this dependency does not assert 6.2 verification passed.
**Parallel with**: None
**Planning gate**: Detailed design/implementation plan and maintainer review before implementation. Settle safe
inspection, supported custom behavior, exception translation, routing and override compatibility together.
No architecture is chosen; do not run a blanket automatic `--fix` pass.
**Success Criteria** (all verified within reconciled scope, 2026-11-01):

  1. Real-preview GET, invalid confirmation and custom-protected POST execute no deletion callbacks (including
     SET/default factories); failed valid POST preserves the write boundary. Rollback alone cannot undo external effects.
  2. Established native PROTECT/RESTRICT remains friendly; unknown handlers/converters/model methods/hooks/commit
     callback failures propagate. Nested cascades and stale previews have real commit/rollback evidence in both atomic modes.
  3. Two-database colliding-PK tests, protection on only one alias and instance-aware routing prove alignment of
     protection inspection, deletion, transactions and commit hooks. CR-04's demonstrated impact is false blocking.
  4. Core/Guardian/polymorphic authorization, filtered labels, independent notices and full-page/modal blocked
     responses remain coherent. Real-preview safety tests do not replace the real collector with an empty preview.
  5. Reproduce fixes on Django 4.2/6.0, add supported 5.2 evidence, replay deletion/transaction/authorization suites,
     update deletion/override docs and changelog (Breaking paired with migrating-1.0.md), re-review and reconcile
     affected 6.2 acceptance before closure. Existing green suites are not proof of these uncovered cases.

  6. Bounded Guardian review (GUA-01): examine AUTH-06 policy boundaries, mutable strict-helper policy (IN-02)
     and unknown permission-key diagnostics (IN-03). Give each actionable gap a concrete scenario/expected outcome,
     fix and test confirmed defects, and record explicit dispositions. If the unclassified detector flag identifies
     no additional gap, close it with a documented rationale. Replay policy tests on cached Django 4.2/6.0;
     preserve the completed AUTH-06 implementation. Escalate any substantial policy redesign as a separate scope decision.

**Disposition (2026-11-01)**: Transferred CR-02–CR-04 are repaired and independently verified.
IN-02/IN-03 and bounded CT-01 are fixed; the AUTH-06 detector fallback is dismissed with recovered-source
evidence. CR-01/WR-02 remain fixed in their earlier scope. GUA-01 was added on 2026-10-30 alongside #282;
its broader custom-PK/backend/collation follow-up remains unverified in issue #286.
WR-01 was fixed separately in 6.2 by quick 261030-csg. IN-01/IN-04 are closed with rationale and IN-05 is fixed in 6.2.
**Plans**: 20/20 complete. Final goal verification passed 91/91 with no overrides and no in-scope human checks outstanding. Original owner responses and subsequent scope dispositions are preserved. Phase 06.3 completed on 2026-11-01; broader Guardian compatibility remains in issue #286. No release or merge is inferred.

Plans:
**Wave 1**
- [x] 06.3-01-PLAN.md — Blocking maintainer review of the integrated design

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 06.3-02-PLAN.md — Callback-safe confirmation and native deletion tracer

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 06.3-03-PLAN.md — Graph inspection, safe provider and partial notices
- [x] 06.3-06-PLAN.md — Strict-helper diagnostics and bounded Guardian review

**Wave 4** *(blocked on Wave 3 completion)*
- [x] 06.3-04-PLAN.md — Native provenance and real write-boundary evidence

**Wave 5** *(blocked on Wave 4 completion)*
- [x] 06.3-05-PLAN.md — Pinned alias, two databases and Guardian label projection

**Wave 6** *(blocked on Wave 5 completion)*
- [x] 06.3-07-PLAN.md — Authorization, templates and actual polymorphic deletion

**Wave 7** *(blocked on Wave 6 completion)*
- [x] 06.3-08-PLAN.md — Executable migration examples and paired release guidance

**Wave 8** *(blocked on Wave 7 completion)*
- [x] 06.3-09-PLAN.md — Three-series matrix and affected acceptance reconciliation

**Wave 9** *(blocked on Wave 8 completion)*
- [x] 06.3-10-PLAN.md — Reviewable repair contract and maintainer approval

**Wave 10** *(plans 11 and 12 complete)*
- [x] 06.3-11-PLAN.md — CR-01 selected-database native target and parent identity
- [x] 06.3-12-PLAN.md — CT-01 configured Guardian content-type access

**Wave 11** *(plan 13 complete)*
- [x] 06.3-13-PLAN.md — CR-02 independent relationship boundaries and provider migration

**Wave 12** *(ready after Wave 11 completion)*
- [x] 06.3-14-PLAN.md — CR-03 native null-join semantics and truthful previews

**Wave 13** *(blocked on Wave 12 completion)*
- [x] 06.3-15-PLAN.md — Executable migration and reference guidance

**Wave 14** *(plan 16 complete; source-bound focused/full and quality evidence ready)*
- [x] 06.3-16-PLAN.md — Fresh three-series automated evidence

**Wave 15** *(executed; human dispositions, UI-F01 and independent acceptance review remain pending)*
- [x] 06.3-17-PLAN.md — Human review and acceptance reconciliation

**Wave 16** *(complete; actual bound focus-contract approval recorded)*
- [x] 06.3-18-PLAN.md — Bound focus lifecycle contract and maintainer decision

**Wave 17** *(complete; focus repair and current verification independently reviewed)*
- [x] 06.3-19-PLAN.md — Modal focus repair, actual browser regressions and adapter migration

**Wave 18** *(task 20-01 complete; task 20-02 awaits twelve individual owner dispositions)*
- [x] 06.3-20-PLAN.md — Current review packet and twelve individual human dispositions

### Phase 06.4: Conditional and formset correctness/lifecycle (INSERTED)

**Goal**: Conditional groups and formsets bind to the correct row, preserve disabled-state ownership, enforce
server-side save semantics and initialize reliably across page/modal/dynamic-row lifecycles before Phase 7 freezes
their theme contracts.
**Source**: `superpowers/notes/2026-10-28-pre-1.0-before-theme-freeze-analysis.md` §4 (A1–A7), §8 slice 6.4 and §9 item 2.
**Requirements**: COND-01, COND-02, COND-03, COND-04, COND-05, FSET-01, FSET-02, FSET-03, LIFE-01, LIFE-02, AUTH-02 (A19 handoff only).
**Depends on**: Phase 6.3; retain Phase 6.2's formset-fragment authorization and request/write boundaries.
**Parallel with**: None in the current roadmap.
**Research/spec**: Settle bound toggle identity and copied-template compatibility, disabled-state ownership,
supported field-clearing semantics, and successful initialization/root/visibility contracts. The source recommends
native immediate visibility; decide whether a downstream theme needs a presentation-only callback/adapter before
the freeze. That seam must not own disabled-state or authorization decisions. Recommendations are not locked design.
**Success Criteria** (what must be TRUE):

  1. A1: Each conditional group binds to its own intended toggle across sibling/nested rows, shared suffixes,
     prefixes, multiple forms, modal content and dynamically added rows; compatibility for old markup is explicit.
  2. A2/A3: Baseline disabled reasons and all enclosing groups compose correctly in both nesting orders. Native
     reset recomputes state after a non-cancelled reset, remains scoped to its form and preserves management inputs.
  3. A4: Inactive supported fields clear with correct persistence semantics, including existing FileField references
     (without promising storage-file deletion), explicit empty values, Boolean and M2M cases. Unsupported shapes
     have an explicit guard. Documentation accurately describes inherited clean/model validation and suppressed errors.
  4. A5: Active `edit_only` formsets cannot create rows through forged extras, including custom control templates;
     stock Add controls agree with server policy and ordinary edits still work. Assess forged initial-row IDs and
     document reject/ignore behavior without claiming an unproven cross-parent mutation.
  5. A6/A7: Formsets and toggles initialize automatically and idempotently on initial load, modal load/422 replacement
     and nested added rows. Initialization can retry after a missing toggle appears, includes supported root elements
     and handles scripts loaded after DOMContentLoaded. Add/delete/order/submit and widget lifecycle work without
     duplicate bindings or reliance on undocumented controller constructors/private flags.
  6. Stock and minimal non-Bootstrap crispy/group/formset templates pass lifecycle and keyboard/focus acceptance,
     including two forms, disabled widgets, reset, hidden-content focus, management POST/re-render and JS-off/tampered
     POST. Preserve fragment authorization, parent denial, restricted querysets, atomic rollback and documented
     skip/opt-in aggregate purge semantics. Keep jQuery in this slice; the #210 port remains deferred.
  7. Document the usable formset template projection and any changed identity/root/visibility hooks for Phase 7.
     Preserve event detail `{prefix, rows}`, one event per outer inserted row, request coordinates and `{html, rows}`.
     Pair any Breaking changelog entry with `docs/migrating-1.0.md`. A8 `commit=False` public/internal classification
     remains a final-policy decision; it is not silently added to this repair scope.

**Plans**:26/26 executed. Plans23–26 closed G6/WR-05 within scope. Human UAT complete: Chrome/Orca checks pass and H2 bounded contract accepted. Independent security44/44closed at ASVS1. Canonical10/10, validation compliant and final handoff ready. Completed2026-11-02. Next: `$gsd-discuss-phase 7`.

Plans:
**Wave 1**
- [x] 06.4-01-PLAN.md — Exact conditional identity from rendered form to submitted values (wave 1)

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 06.4-02-PLAN.md — Field-aware conditional persistence (wave 2)
- [x] 06.4-05-PLAN.md — Composed conditional state, native reset and focus (wave 2)

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 06.4-03-PLAN.md — Static and runtime clearing configuration contract (wave 3)
- [x] 06.4-04-PLAN.md — Mandatory active formset row-policy validation (wave 3)

**Wave 4** *(blocked on Wave 3 completion)*
- [x] 06.4-06-PLAN.md — Form-scoped formset initialization and modal submit ordering (wave 4)

**Wave 5** *(blocked on Wave 4 completion)*
- [x] 06.4-07-PLAN.md — Successful non-first sibling fragment round trips (wave 5)

**Wave 6** *(blocked on Wave 5 completion)*
- [x] 06.4-08-PLAN.md — Real HTTP and browser conditional/formset acceptance (wave 6)

**Wave 7** *(blocked on Wave 6 completion)*
- [x] 06.4-09-PLAN.md — Tested migration and Phase 7 public contract handoff (wave 7)

**Wave 8** *(blocked on Wave 7 completion)*
- [x] 06.4-10-PLAN.md — Supported-series regression evidence and acceptance handoff (wave 8)

**Wave 9** *(gap closure; dependencies in PLAN frontmatter)*
- [x] 06.4-11-PLAN.md — Reapply mandatory row policy after native recleaning (wave 9)
- [x] 06.4-12-PLAN.md — Separate the mandatory Django bridge from ordinary Node tests (wave 9)
- [x] 06.4-14-PLAN.md — Preserve conditional ownership while a binding is unresolved (wave 9)

**Wave 10** *(gap closure; dependencies in PLAN frontmatter)*
- [x] 06.4-13-PLAN.md — Keep row deletion eligibility stable through insertion and reordering (wave 10)
- [x] 06.4-15-PLAN.md — Enforce evidence selection and current runtime requests (wave 10)

**Wave 11** *(gap closure; dependencies in PLAN frontmatter)*
- [x] 06.4-16-PLAN.md — Exercise repaired lifecycle in a representative browser host (wave 11)
- [x] 06.4-17-PLAN.md — Reconcile repaired contracts and required test commands in documentation (wave 11)

**Wave 12** *(gap closure; dependencies in PLAN frontmatter)*
- [x] 06.4-18-PLAN.md — Capture and validate current-source gap repair evidence (wave 12)

**Wave 13** *(gap closure; dependencies in PLAN frontmatter)*
- [x] 06.4-19-PLAN.md — Reconcile independent reviews and gather the outstanding human dispositions (wave 13)

**Wave 14** *(blocked on Wave 13 completion)*
- [x] 06.4-20-PLAN.md — Reject missing control records and stale conditional captures

**Wave 15** *(blocked on Wave 14 completion)*
- [x] 06.4-21-PLAN.md — Refresh affected evidence with verified source applicability and original provenance

**Wave 16** *(blocked on Wave 15 completion)*
- [x] 06.4-22-PLAN.md — Independent reassessment and end-of-phase acceptance handoff

**Wave 17** *(blocked on Wave 16 completion)*
- [x] 06.4-23-PLAN.md — Reject oversized capture dimensions with exact diagnostics through both CLIs

**Wave 18** *(blocked on Wave 17 completion)*
- [x] 06.4-24-PLAN.md — Refresh checker evidence with immutable source and gate provenance

**Wave 19** *(blocked on Wave 18 completion)*
- [x] 06.4-25-PLAN.md — Obtain independent code/security reviews and reconcile validation

**Wave 20** *(blocked on Wave 19 completion)*
- [x] 06.4-26-PLAN.md — Replay canonical controls, reassess and rebind the final handoff

**WR-05 execution result (2026-11-01):** Plans23–26/nine tasks complete. Checker67/Ruff/35controls/clean positive pass,17original gates retained; two independent14-probe reviews and14canonical observations close G6/WR-05. Canonical human_needed9/10, final handoff structurally valid/not-ready; H1/H2 and31flags remain. Security40/44closed with4highopen at independent snapshot. Two UAT checks pending; no Phase7 advancement. Next: `$gsd-verify-work 06.4`.

**WR-05 planning result (2026-11-01):** Plans 23–26 / nine tasks passed independent checking after one revision. Coverage: 11/11 requirements, 19/19 decisions. Canonical gaps_found, H1/H2, 31 flags and open security obligations remain explicit. Next: `$gsd-execute-phase 06.4 --gaps-only`.

**Execution result (2026-11-01):** Plans 20–22 complete; WR-03/04 independently closed, new WR-05 remains fail-closed diagnostic gap. Canonical 8/10; security 38/41 closed with 3 high open; H1/H2 and 31 flags unresolved. Final handoff structurally valid and not ready. Next: `$gsd-plan-phase 06.4 --gaps`.

**Planning result (2026-11-01):** Plans 20–22 passed the independent checker. Canonical verification remains gaps_found (8/10 merged truths): G6/WR-03/04, H1/H2 and six security obligations (five high) remain open. No phase acceptance is inferred. Next: `$gsd-execute-phase 06.4 --gaps-only`.

Shared-path sequencing: 01 precedes 02, then 04 (render tree/formsets); 01 precedes 05 (toggle JS);
02 precedes 03 (clearing); 06 precedes 07 (formset JS tests). Browser 08 integrates all repairs,
09 publishes tested contracts, and 10 records the final supported-series evidence.

### Phase 06.5: Remaining presentation contracts and decided cleanup (INSERTED)

**Goal**: Settle the remaining heading and object-detail presentation contracts and complete the already-decided
label alias cleanup before Phase 7 freezes the public theme surface.
**Source**: `superpowers/notes/2026-10-28-pre-1.0-before-theme-freeze-analysis.md` §2 heading-host probe (#259),
§5 C1/C2, §6 alias dispositions and §8 slice 6.5.
**Requirements**: PRES-01, PRES-02, PRES-03, PRES-04, PRES-05, PRES-06.
**Depends on**: Phase 6.4 for final integration after completed Phases 6.2–6.4; preserves Phase 6/6.1 form-leaf contracts.
**Parallel with**: None in the remaining execution sequence.
**Research/spec**: Settle heading slot/tag/context names and shared control/panel ID projection before implementation.
Decide the response to the removed Python constructor keyword and document heading sizing-class constraints.
The discussion selects semantic badge color/pill context now, retaining existing Bootstrap defaults and badge
precedence. CONTEXT.md D-01–D-17 locks configurable headings, immediate migration and optional stable IDs.
**Success Criteria** (what must be TRUE):

  1. #259: Stock page, modal and icon-bearing object-detail group headings support element and host icons with
     accessible headings and no duplicate icon. Cover mixed libraries, empty/disabled icons, escaped classes and
     heading-level changes; define the public heading contract and its sizing-class constraints.
  2. C1: One- and two-group vertical tabs have matching selected triggers and visible initial panels, and switch
     correctly in a real browser. Keep trigger/panel state together through the documented template projection.
  3. C2: Accordion and tab controls target unique panels for colliding, repeated, empty and translated titles,
     repeated detail components and page/modal coexistence. Document the shared per-render/group ID contract.
  4. A minimal native layout override retains escaped titles/values and the supported resolved-property context.
     Record actual browser/keyboard acceptance for corrected tabs; identify any untested non-Bootstrap visual or
     assistive-technology behavior explicitly. Expose resolved semantic badge color/pill context alongside existing
     classes, preserving custom color names, ordinary-value fallback and badge-template precedence.
  5. Remove Python `CardAction.no_label` and the obsolete template `cv_no_label` rejection guard as already decided;
     migrate fixtures/docs/tests to `label_mode="icon"` and `cv_label_mode`, with clear old-keyword behavior.
     Preserve both accepted singular/plural label-mode APIs and existing form-leaf contracts.
  6. Document intentional stock markup and copied-template changes, pairing every Breaking changelog entry with
     `docs/migrating-1.0.md`. Hand the settled heading, ID/context and alias contracts to Phase 7's inventory.

**Scope exclusions**: Completed authorization/deletion/conditional/formset acceptance, proposed Phase 6.6 Tabler
seams (#277–#280), unrelated CSS cleanup, the jQuery port, optional diagnostics and the final stability policy.
**Plans**: 9/9 plans complete; UAT 28/28 passed, canonical verification passed and security 20/20 closed. Completed 2026-11-02.

Plans:

**Wave 1**

- [x] 06.5-01-PLAN.md — Make a real modal heading consume theme sizing and one host/element icon projection.
- [x] 06.5-06-PLAN.md — Expose semantic badge color and pill from the existing single resolution.

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 06.5-02-PLAN.md — Apply the shared heading contract to page and plain group titles and publish its exact recipe.
- [x] 06.5-07-PLAN.md — Remove the alias while rejecting its presence with an actionable migration error.

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 06.5-03-PLAN.md — Render generated identities and first selection through tabs and accordion from one projection.

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 06.5-04-PLAN.md — Expose stable application identity and prove the rendering collision boundary.
- [x] 06.5-05-PLAN.md — Initialize stock tabs before first page or modal keyboard interaction.

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 06.5-08-PLAN.md — Prove stock keyboard behavior and native projection in a real browser.

**Wave 6** *(blocked on Wave 5 completion)*

- [x] 06.5-09-PLAN.md — Publish tested migrations and hand settled presentation contracts to Phase 7.

**UI hint**: existing heading and object-detail markup/behavior; browser acceptance required, no new screens.

### Phase 06.6: Theme-adoption seams from the Tabler sync (INSERTED)

**Goal**: Close the theme-adoption gaps from the Tabler sync before Phase 7 freezes the affected public names.
**Source**: [Pre-1.0 analysis](../superpowers/notes/2026-10-28-pre-1.0-before-theme-freeze-analysis.md),
2026-10-29 addendum, §8 slice 6.6 and §9 decisions 5–6; issues #277–#280.
**Depends on**: Phase 6.5 for final integration. Builds on Phases 1, 4 and 6; check delete-page integration
against Phase 6.3. Must complete before Phase 7.
**Requirements**: THEME-01, THEME-02, THEME-03, THEME-04, THEME-05, THEME-06
**Success Criteria** (what must be TRUE):

  1. Create/update/custom/delete/workflow pages render one `<form>` and one CSRF input with POST behavior
     unchanged (#277). Document the user-supplied crispy-helper policy; page templates own the form.
  2. `register_label_mode_defaults()` supplies package → theme → project-setting precedence per key;
     explicit view modes retain precedence (#278). Validate consistently with E108 and include the theme layer
     in W292 diagnostics.
  3. `form:actions` and `form:filter-actions` independently style action groups, with empty-string defaults;
     update W362 and the documented key inventory (#279).
  4. Add `alert:dismissible` / `alert:close` utility keys with byte-identical defaults and preserved accessible
     names/dismissal behavior, as selected by D-08/D-17.
  5. Re-run the reference Tabler theme; required overrides shrink or stay unchanged. Preserve stock defaults
     except removal of the nested form, record that DOM fix, and hand every new name to Phase 7.
     Pair any Breaking changelog entry with `docs/migrating-1.0.md`.

**Decisions settled**: D-01–D-19 in 06.6-CONTEXT.md require immediate incompatible-helper errors, unused-wrapper
warning/strict errors, atomic theme registration and both alert keys. The 2026-11-02 D-11/D-14 amendment
authorizes verified companion delivery/local commits while retaining isolated baseline/replay and unrelated-work preservation.
**Scope exclusions**: Reopening completed authorization/deletion/conditional/formset/presentation acceptance,
full jQuery removal, and final stability-policy inventory.
**Plans**: 10/10 plans complete

Plans:
**Wave 1**
- [x] 06.6-01-PLAN.md — Single-form/CSRF tracer and helper diagnostics (wave 1)
- [x] 06.6-04-PLAN.md — Alert utility classes and preserved dismissal (wave 1)
- [x] 06.6-06-PLAN.md — Real companion acquisition and exact-source baseline (wave 1)

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 06.6-02-PLAN.md — Atomic theme label defaults and effective checks (wave 2)
- [x] 06.6-03-PLAN.md — Supported-pack action-group styling (wave 2)
- [x] 06.6-05-PLAN.md — Full stock/workflow request and DOM preservation (wave 2)

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 06.6-07-PLAN.md — Real Tabler/browser acceptance and replayable patch (wave 3)
- [x] 06.6-08-PLAN.md — Executable adoption and paired migrations (wave 3)

**Wave 4** *(blocked on Wave 3 completion)*
- [x] 06.6-10-PLAN.md — Verified companion source delivery and local commit (wave 4)

**Wave 5** *(blocked on Wave 4 completion)*
- [x] 06.6-09-PLAN.md — Final regression evidence and Phase 7 handoff (wave 5)

**UI hint**: yes (forms, action groups and alerts across stock and reference themes).

### Phase 06.7: Dynamic cancel navigation and origin query state (INSERTED)

**Goal:** Cancel returns to the originating allowed sibling view with its filters, sorting and pagination preserved,
independently of session changes in another tab or parent context. Standard forms enable dynamic cancellation by
default while retaining explicit static overrides and the List fallback.
**Source**: [Issue #302 — Dynamic cancel navigation by default, preserving origin query state](https://github.com/jacob-consulting/django-crud-views/issues/302)
**Requirements**: CAN-01, CAN-02, CAN-03, CAN-04, CAN-05, CAN-06, CAN-07
**Depends on:** Phase 06.6
**Parallel with**: None (settle the cancel contract before Phase 7 freezes the public surface).
**Decisions settled**: Create and no-object custom forms accept registered list/card origins; update, delete and
object-based custom forms also accept detail. `cv_cancel_key` remains the fallback (default `"list"`, with existing
card fallback); explicit `cv_cancel_keys=None` keeps static cancellation and explicit lists select allowed keys.
Unspecified defaults must remain distinguishable from explicit static overrides. Destinations stay within the same
ViewSet; detail destinations use the form's existing object.
**Success Criteria** (what must be TRUE):

  1. List → update/create/delete → Cancel restores the originating list query; detail → update/delete → Cancel
     returns to the same object's detail without changing or deleting it. Equivalent custom form flows work.
  2. List/card origins preserve repeated query values, filters, sorting and page. Explicitly unfiltered origins
     remain unfiltered despite stored session filters, another tab cannot overwrite the captured destination,
     and nested ViewSets retain the correct parent context. Internal navigation parameters do not accumulate.
  3. Origin information survives invalid submissions for all supported form types and polymorphic type selection.
     Crispy buttons, native cancel links, supported modals and the documented custom-template URL helper resolve
     the same destination.
  4. Missing, malformed, disallowed or unusable origin information falls back safely. Explicit static cancellation
     remains supported; Save and successful deletion redirects retain their existing behavior.
  5. Tests cover issue #302's acceptance checklist. Documentation covers defaults, overrides, query state and the
     URL-level API; the default change has a `### Breaking` changelog entry and paired `docs/migrating-1.0.md` guidance.

**Scope exclusions**: Detail → create → detail (Create uses its configured fallback), cross-ViewSet navigation,
history stacks, browser-only state, success redirect changes, new modal support and new Cancel controls on protected
deletion pages that currently hide the form.
**Plans:** 5/5 plans complete

Plans:
**Wave 1**
- [x] 06.7-01-PLAN.md — Capture and restore independent cancel destinations with automatic form defaults

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 06.7-02-PLAN.md — Resolve permission-aware destinations and actionable fallback diagnostics
- [x] 06.7-03-PLAN.md — Preserve origin across selectors and unify custom-template/modal rendering

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 06.7-04-PLAN.md — Publish executable immediate migrations and updated examples

**Wave 4** *(blocked on Wave 3 completion)*
- [x] 06.7-05-PLAN.md — Prove browser cancellation and record supported-runtime preservation

**UI hint**: yes (cancel navigation across existing form surfaces; no layout redesign).

### Phase 06.8: Action tooltips: short captions and visible-label suppression (#304) (INSERTED)

**Goal:** Context/list icon-only actions use existing short captions with full-caption fallback, while preserving full hidden accessible labels and suppressing package-generated tooltips on visible labels.
**Source:** [Issue #304](https://github.com/jacob-consulting/django-crud-views/issues/304) — implementation handoff with existing maintainer decisions and investigation context.
**Depends on:** Phase 6.7; complete before Phase 7 freezes the theme surface.
**Requirements**: TIP-01, TIP-02, TIP-03, TIP-04, TIP-05
**Scope:** Reuse existing caption APIs; preserve card overrides, form captions, translations/escaping, permissions, POST/modal hooks and tooltip lifecycle. Include the issue's recommended removal of automatic titles from visibly labelled overflow items; this recommendation is distinct from the selected short-caption decision.
**Investigation:** Reproduce the reported labelled list-action tooltip behavior in rendered UI/DOM. It remains unconfirmed; record an unavailable/not-reproduced application observation honestly without blocking the confirmed short-caption improvement.
**Success Criteria**:

1. Context/list icon tooltips use short captions with full-caption fallback; full hidden captions remain unchanged, and empty tooltips emit neither title nor marker.
2. Label/both modes and visible missing-icon fallbacks emit no generated tooltip; visibly labelled overflow items omit automatic titles across context/list/card locations.
3. The labelled list-action report has a documented investigation outcome, with a regression test for any reproduced package defect.
4. Relevant caption, accessibility, permission, submission, escaping and lifecycle contracts remain covered; affected docs and changelog describe the changed defaults, with migration guidance if classified as breaking.

**Plans:** 3/3 plans complete

Plans:
**Wave 1**
- [x] 06.8-01-PLAN.md

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 06.8-02-PLAN.md

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 06.8-03-PLAN.md

### Phase 06.9: Protected delete-preview object links (INSERTED)

**Goal:** When `cv_link_related_objects` is enabled, users can navigate from visible protected blockers in the delete preview to their permitted detail views.
**Source:** [Issue #307](https://github.com/jacob-consulting/django-crud-views/issues/307). The issue proposed post-1.0 work; this insertion schedules it before the Phase 7 freeze.
**Requirements**: PDL-01, PDL-02, PDL-03, PDL-04, PDL-05, PDL-06
**Depends on:** Phase 06.8; preserve the delete-preview and Guardian permission contracts established in Phase 6.3. Complete before Phase 7 freezes the affected surface.
**Scope:** Resolve protected-object URLs through the existing `cv_get_related_object_url()` path after visibility filtering. Preserve generic notices for hidden blockers, plain-text fallbacks, and existing cascade-preview behavior. Retain copied-template compatibility or document the migration; update `docs/reference/delete_view.md` and relevant example guidance.
**Success Criteria**:

1. With related-object linking enabled, visible protected blockers link to permitted detail views; missing or inaccessible destinations remain plain text.
2. Disabled linking and hidden-blocker notices preserve existing behavior without exposing objects or URLs the user cannot view.
3. Regression coverage verifies core and Guardian behavior, escaping, and cascade-preview preservation; affected context/template contracts and documentation are updated, with paired changelog/migration guidance if breaking.

**Plans:** 4/4 plans complete

Plans:
**Wave 1**
- [x] 06.9-01-PLAN.md

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 06.9-02-PLAN.md

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 06.9-03-PLAN.md

**Wave 4** *(blocked on Wave 3 completion)*
- [x] 06.9-04-PLAN.md

### Phase 06.10: Simplify protected-object previews and cap total displayed objects (INSERTED)

**Goal:** Reduce delete-preview maintenance and per-object presentation cost: protected blockers render as readable,
permission-filtered plain text, existing cascade links remain available for displayed entries, and one configurable
budget defaults to 50 entries across the entire displayed related-object preview, with explicit `None` for unlimited
display, without truncating deletion enforcement.
**Source:** [Issue #316](https://github.com/jacob-consulting/django-crud-views/issues/316), a targeted follow-up to completed Phase 06.9 / #307.
**Requirements**: DPV-01, DPV-02, DPV-03, DPV-04, DPV-05, DPV-06
**Depends on:** Phase 06.9. Complete before Phase 7 freezes the affected public surface.
**Scope:** Remove protected-link destination request/view simulation and exclusively owned support code after auditing
callers. Preserve deletion safeguards, visibility filtering, escaping, useful preview customization, and existing
cascade URL generation/overrides for displayed entries. Apply a single shared display budget across sections, model
groups and nesting levels after visibility filtering and before optional URL generation/presentation work.
**Explicit limits:** The cap bounds display only; complete inspection and write-time enforcement remain unchanged,
with no claim of bounded full-graph memory/query cost. No replacement destination-policy framework, general URL
resolver, pagination, lazy loading or show-all endpoint. No dependency on #312, #314 or the retired URL/access phase.
This new use of phase number 06.10 does not reactivate the archived resolver plans.
**Decisions settled:** See [06.10-CONTEXT.md](phases/06.10-simplify-protected-object-previews-and-cap-total-displayed-o/06.10-CONTEXT.md).
Default 50; `CRUD_VIEWS_DELETE_PREVIEW_LIMIT` plus per-view `cv_delete_preview_limit`; explicit `None` means unlimited,
while an unspecified view override inherits. Positive integers otherwise required. Blockers first, depth-first
cascades, every displayed occurrence/root counts; omit hidden rows and promote visible children. Preserve `obj`/`url`
entries with `url=None`, existing summary policy, and one shared truncation notice above the lists.
**Success Criteria**:

1. Protected blockers remain escaped, permission-filtered text; their presentation performs no destination request/view construction or protected-link destination checks.
2. A finite configured N caps visible entries across mixed models, sections and deeply nested data; explicit `None` is unlimited. Tests cover precedence, unlimited display, invalid values, and below, at and well above the cap; optional cascade URL/presentation hooks run only for selected entries, verified through hook and query counts.
3. Hidden objects neither consume the visible-item budget nor leak labels or new counts; existing summary/redaction policy remains unchanged. Empty, hidden-only and truncated previews use truthful messaging and retain a coherent readable structure.
4. Hidden or undisplayed blockers still prevent deletion and omit the confirmation form as appropriate in real core and Guardian requests. Existing write safeguards and supported cascade-link overrides remain covered.
5. Stock/copied templates, full pages and modals follow the decided contract. Before/after measurements separate inspection, visibility and presentation and demonstrate removal of adapter cost without claiming bounded total inspection cost.
6. Delete reference, examples and copied-template guidance are updated. Any documented breaking contract change has paired CHANGELOG.md and docs/migrating-1.0.md guidance; Phase 7 inventories the final public configuration and template surface.

**Plans:** 5/5 plans complete — automated gates and independent verification passed; all seven human UAT checks accepted on 2026-11-05. Phase complete.

Plans:
- [x] 06.10-01-PLAN.md — Plain protected-blocker tracer, adapter removal and component measurements (wave 1)
- [x] 06.10-02-PLAN.md — Strict finite/None configuration, visible selection and enforcement regressions (wave 2)
- [x] 06.10-03-PLAN.md — Executable copied recipes, public guidance and Phase 7 handoff (wave 3)
- [x] 06.10-04-PLAN.md — Runnable examples and translated shortened notice (wave 3, parallel with 03)
- [x] 06.10-05-PLAN.md — Existing browser harness migration and final source-bound acceptance (wave 4)

**UI hint:** yes (plain-text protected blockers and truncated delete previews across full pages and modals).

### Phase 06.13: Workflow permissions: document and test opt-in per-transition access (#320) (INSERTED)

**Goal**: Document and regression-test an opt-in workflow page gated by view permission, with explicit
per-transition permissions controlling execution, while preserving the default change-permission gate.
**Source**: [Issue #320](https://github.com/jacob-consulting/django-crud-views/issues/320)
**Requirements**: WFP-01, WFP-02, WFP-03, WFP-04, WFP-05
**Depends on**: Phase 6.10. Independently deliverable from Phase 06.12 presentation work and the separate
workflow validation/execution design. Scheduled before Phase 7; no new public permission API is required.
**Scope**: A self-contained recipe in `docs/reference/workflow_view.md`, focused workflow regression tests,
and a documentation changelog entry. Keep `cv_permission = "change"` as the default; the recipe opts into
`cv_permission = "view"` and explicit django-fsm `permission=` rules. Present the basic accessible-empty-page
recipe separately from the optional `cv_action_enabled` request gate with disabled rendering via
`workflow_has_any_possible_transition(user)`. Preserve applicable object/parent access checks. The corrected
2026-11-05 CONTEXT decisions D-01–D-15 are authoritative.
**Success Criteria** (from issue #320):

  1. Default workflow views still require change permission. A view-only user with a dedicated step permission
     can GET and POST that permitted transition, changing state and recording history.
  2. A different role's transition available from the same source state is omitted; forged POSTs are rejected
     without state/history changes. A user lacking page permission cannot GET or POST even if a transition permits them.
  3. Without the optional hook, a page viewer with no permitted steps receives GET 200 and the existing empty message.
     With the hook, the action renders disabled on an accessible sibling page and direct authenticated GET/POST
     return 403; a user with a permitted step still succeeds. Rejected attempts preserve state and history.
  4. Execution-time `workflow_has_transition` authorization is rechecked independently of display and form choices.
  5. Docs distinguish page access, optional action-enabled request enforcement, state/user transition filtering,
     submitted-choice validation, execution rechecks, and object/parent checks. Disabled rendering alone is not
     authorization; the server also enforces the hook. Lowering the page gate alone adds no transition restrictions.
  6. Focused tests, appropriate broader multicore regression checks, and documentation validation pass.

**Exclusions**: No automatic any-transition page gate, new permission framework, Guardian integration mode,
execution helper, refusal-message API, default-permission change, or finding 7 execution redesign.
**Plans**: 2/2 plans complete
**UI hint**: no (documentation and regression tests)

Plans:
**Wave 1**
- [x] 06.13-01-PLAN.md — Isolated opt-in permission requests, no-step variants, and execution recheck regressions.

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 06.13-02-PLAN.md — Complete workflow recipe, documentation changelog, and bounded compatibility validation.

### Phase 06.13.1: Workflow validation and execution: business blockers, transition buttons, and reusable helper (#322) (INSERTED)

**Goal:** Workflow users see actionable business-blocker explanations and per-transition comment requirements;
web and programmatic execution share a bounded helper that enforces permissions, comments and business checks
while preserving atomic state/history writes and request lifecycle hooks. Transition buttons are opt-in;
existing radio/custom forms and the default page permission remain supported.
**Source:** [Issue #322](https://github.com/jacob-consulting/django-crud-views/issues/322)
**Requirements**: WFX-01, WFX-02, WFX-03, WFX-04, WFX-05
**Depends on:** Phase 06.13
**Integration notes:** Reuse #319's shared workflow form frame (issue closed); preserve #320's permission
regressions. Backend validation/helper work is independent of presentation. Settle any new public theme
contracts before Phase 7's stability freeze. Plans preserve the locked public contracts and bounded workflow scope.
**Plans:** 5/5 plans complete
**UI hint:** yes (accessible transition buttons, visible help/blockers, and bound error redisplay without workflow JS)

Plans:
**Wave 1**
- [x] 06.13.1-01-PLAN.md — Shared business validation/execution and origin-aware bound refusal recovery (wave 1).

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 06.13.1-02-PLAN.md — Real routed state/history identity and atomic failure guarantees (wave 2).
- [x] 06.13.1-03-PLAN.md — Opt-in accessible transition buttons and custom page/modal forms (wave 2).

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 06.13.1-04-PLAN.md — Owned browser fixture, no-JS page flow and complete UI state acceptance (wave 3).
- [x] 06.13.1-05-PLAN.md — Public contracts, release guidance and bounded regression evidence (wave 3).

### Phase 06.15: Polymorphic: capitalize type labels and validate per-model detail groups; update tabler-test (#326) (INSERTED)

**Goal:** Resolve polymorphic findings 10–11 in one bounded phase: capitalize default selector labels without
changing remaining casing or translation behavior, support explicit model-to-groups detail configuration with
startup validation of every entry, and adopt and verify the changes in the sibling `../tabler-test` project.
**Source:** [Issue #326](https://github.com/jacob-consulting/django-crud-views/issues/326)
**Requirements**: POLY-01, POLY-02, POLY-03, POLY-04, POLY-05
**Depends on:** Existing polymorphic and object-detail configuration paths. Follows Phase 06.14 numerically;
no implementation dependency on its card work is established by #326.
**Settled scope:** The issue's agreed design and acceptance criteria are the planning contract. Preserve existing
list configuration and working dynamic overrides; mapped groups use exact `type(self.object)` lookup and fail
clearly for unmapped types. Reuse existing parsing and structural/icon checks for every mapping entry, with
model-specific diagnostics and no request/object evaluation, extra database queries, or new polymorphic dependency
for object-detail configuration. No inheritance matching, fallback keys, subtype discovery, or completeness proof.
**Downstream completion:** Remove only the selector capitalization workaround and redundant detail override/dummy
configuration in `tabler-test`; retain the custom crispy layout and Continue button. Verify Beans, Equipment and
Subscription behavior and permissions; update the findings report and documentation, and record validation from
both repositories. Finding 16 and unrelated object-detail findings remain deferred.
**Planning handoff:** Carry the settled issue decisions into CONTEXT.md when planning; do not reopen approach
selection. Routine implementation mechanics are delegated to the planner. Settle these contracts before Phase 7.
**Plans:** 4/4 plans complete

Plans:
**Wave 1**
- [x] 06.15-01-PLAN.md — Exact-model detail groups and complete structural checks
- [x] 06.15-02-PLAN.md — Capitalized selector labels with selection/access compatibility

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 06.15-03-PLAN.md — Public contract, release guidance and supported-series validation

**Wave 3** *(blocked on Wave 2 completion)*
- [x] 06.15-04-PLAN.md — Required downstream adoption, catalog validation and findings resolution

### Phase 7: Theme-surface stability policy

**Goal**: Theme authors can see exactly which names they may rely on at 1.0.0, and a test stops any public theme name
from shipping undocumented or being documented without existing.
**Source**: plan 4 · branch `docs/stability-theme-surface`
**Depends on**: Phase 6.10, Phase 4 and Phase 5 (and so, transitively, Phases 6.9, 6.8, 6.7, 6.6, 6.5, 6.4, 6.3, 6.2, 6.1, 6, 1 and 2). It merges last, before the 1.0.0
bump. If Phases 4/5 are dropped, it depends on Phase 6.10 only and documents the surface as it is. Include the cancel
tag key, `Button(tag=...)` and form-leaf `cv_tag` contract introduced by #275, plus the settled request,
protected-preview and Guardian configuration contracts from Phase 6.2, qualified by the unresolved acceptance
split above until Phase 6.3 remediation is verified. Include the settled conditional/formset contracts from Phase 6.4.
Include the settled heading, object-detail ID/context and alias cleanup contracts from Phase 6.5.
Include the settled form ownership, label-mode registration, action-group and alert contracts from Phase 6.6.
Include the dynamic cancel defaults, origin query preservation and custom-template URL API settled by Phase 6.7.
Include the tooltip caption and visible-label rendering contracts settled by Phase 6.8.
Include the final protected-preview text, shared display-limit configuration and context/template contracts settled
by Phase 6.10, which supersede the protected-link portion of Phase 6.9.
**Parallel with**: None
**Research/spec**: **Needs a maintainer decision/spec**:

  - the tier assignments
  - a public `is_library_renderer` helper
  - whether the reference theme's private imports are acceptable
  - document both accepted label-mode APIs and the completed Phase 6.5 alias removal; do not reopen those decisions

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
Numeric order (1 → 2 → 3 → 4 → 5 → 6 → 6.1 → 6.2 → 6.3 → 6.4 → 6.5 → 6.6 → 6.7 → 6.8 → 6.9 → 6.10 → 6.13 → 6.13.1 → 6.14 → 6.15 → 7) is valid. With parallelization, run in waves:

| Wave | Phases | Notes |
|------|--------|-------|
| 1 | 1 (plan 1A) ∥ 2 (plan 1C) | Disjoint files; both are preconditions of Phase 6 |
| 2 | 3 (plan 1B) ∥ 4 (plan 3A) ∥ 5 (plan 3B) | 3 needs 1; 4 and 5 are independent (5 rebases after 2 for the key count) |
| 3 | 6 (plan 2) | Verify completed 1 and 2 on the working branch; spec first (D-18) |
| 4 | 6.1 (#275) | Extends Phase 6 with a theme-selectable cancel link before the stability freeze |
| 5 | 6.2 (analysis B1–B7) | Secures request/write boundaries and safe contexts before the freeze |
| 6 | 6.3 (#282) | Delete protection and write-boundary integrity before the freeze |
| 7 | 6.4 (analysis A1–A7) | Conditional/formset correctness and lifecycle before freezing their theme contracts |
| 8 | 6.5 (analysis #259/C1/C2) | Remaining presentation contracts and decided alias cleanup before the freeze |
| 9 | 6.6 (#277–#280) | Theme-adoption seams from the Tabler sync before the freeze |
| 10 | 6.7 (#302) | Dynamic cancel defaults and origin query preservation before the freeze |
| 11 | 6.8 (#304) | Short icon tooltips and visible-label suppression before the freeze |
| 12 | 6.9 (#307) | Protected delete-preview links before the freeze |
| 13 | 6.10 (#316) | Simplify protected previews and settle the shared display cap before the freeze |
| 14 | 6.13 (#320) | Document and test opt-in workflow permissions; independently deliverable from presentation work |
| 15 | 6.13.1 (#322) | Workflow validation/helper and opt-in buttons; settle new theme contracts before the freeze |
| 16 | 6.14 (#325) | Empty card blocks and tested cards-first navigation |
| 17 | 6.15 (#326) | Polymorphic labels and per-model groups, including tabler-test adoption and verification |
| 18 | 7 (plan 4) | Needs 6.10, 4 and 5 merged and 6.13.1/6.15 contracts settled; last change before the 1.0.0 bump |

Droppable if 1.0.0 must ship early: Phases 4 and 5 (plan 3A/3B).

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Label-mode defaults | 5/5 | Complete    | 2026-10-26 |
| 2. Form key grammar | 1/1 | Complete    | 2026-10-26 |
| 3. Filter toggle label mode | 2/2 | Complete    | 2026-10-26 |
| 4. Alert dismiss adapter | 3/3 | Complete    | 2026-10-26 |
| 5. Table pagination parity | 3/3 | Complete    | 2026-10-27 |
| 6. Form-button leaf | 10/10 | Complete    | 2026-10-28 |
| 6.1. Cancel form button as a link | 3/3 | Complete    | 2026-10-29 |
| 6.2. Request authorization and write integrity | 9/9 | Complete    | 2026-10-30 |
| 6.3. Delete protection and write-boundary integrity | 20/20 | Complete    | 2026-11-01 |
| 6.4. Conditional and formset correctness/lifecycle | 26/26 | Complete    | 2026-11-02 |
| 6.5. Remaining presentation contracts and decided cleanup | 9/9 | Complete    | 2026-11-02 |
| 6.6. Theme-adoption seams from the Tabler sync | 10/10 | Complete    | 2026-11-03 |
| 6.7. Dynamic cancel navigation and origin query state | 5/5 | Complete    | 2026-11-03 |
| 6.8. Action tooltips: short captions and visible-label suppression | 3/3 | Complete    | 2026-11-04 |
| 6.9. Protected delete-preview object links | 4/4 | Complete    | 2026-11-04 |
| 6.10. Simplify protected-object previews and cap total displayed objects | 5/5 | Complete    | 2026-11-05 |
| 6.13. Workflow permissions: opt-in per-transition access | 2/2 | Complete    | 2026-11-05 |
| 6.13.1. Workflow validation and execution | 5/5 | Complete    | 2026-11-06 |
| 6.14. Card template insertion blocks and cards-first ViewSets | 2/2 | Complete | 2026-11-06 |
| 6.15. Polymorphic labels and per-model detail groups | 4/4 | Complete    | 2026-11-06 |
| 7. Theme-surface stability policy | 0/TBD | Not started | - |
