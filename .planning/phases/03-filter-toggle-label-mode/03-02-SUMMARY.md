---
phase: 03-filter-toggle-label-mode
plan: "02"
subsystem: docs
tags: [mkdocs, label-mode, filter-toggle, changelog, migration-guide, pytest]

requires:
  - phase: 03-filter-toggle-label-mode
    provides: "03-01: FilterContextButton stamps cv_label_mode; context_action_filter.html renders icon/both/label; translated Filter"
provides:
  - Compact filter-toggle contract in docs/reference/context_buttons.md (settings-map and FilterContextButton examples, declared key, no target-view default, three modes, constant translated label, template ownership)
  - Corrected icon-only filter claims in context_buttons.md, action_menus.md, buttons.md, javascript.md and icons.md
  - Optional-icon browser contract (element/host/none) with collapse-first and non-rollback semantics
  - CHANGELOG Unreleased Fixed entry for #262, including the already-configured context-floor impact
  - Migration guide detailed contract and checklist for copied context_action_filter.html templates
  - test_filter_toggle_reference_contract plus the updated Rendering assertion in test_label_mode_docs.py
affects: [downstream themes overriding context_action_filter.html, 07 stability theme surface]

actuals:
  tokens: 4275
  tasks: 3
  commits: 3
plan_head_before: bc672c5e25c519a29bf10362967f54542bd35ed8
plan_head_after: 2482c5f7497180765b0dd3544f9691a799ca77f1

tech-stack:
  added: []
  patterns:
    - "Doc contract tests check paired prose edits and are run against the pre-change docs to show they reject them"
    - "Compact contract links the canonical resolution order instead of restating it (no numbered steps in the section)"

key-files:
  created:
    - .planning/phases/03-filter-toggle-label-mode/deferred-items.md
  modified:
    - docs/reference/context_buttons.md
    - docs/reference/action_menus.md
    - docs/reference/buttons.md
    - docs/reference/javascript.md
    - docs/reference/icons.md
    - docs/migrating-1.0.md
    - tests/test1/test_label_mode_docs.py
    - CHANGELOG.md

key-decisions:
  - "Release note stays under Fixed (no Breaking entry): default output is unchanged, and the change applies configuration the toggle used to ignore. The migration guide still gets a contract and checklist update for copied templates."
  - "View-level cv_context_buttons = [FilterContextButton(label_mode=...)] is the documented per-page override. FilterContextButton is imported from crud_views.lib.view.buttons; the plan scoped out adding a re-export."
  - "Docs state the A1 limitation as behavior: a mode the stock template does not know renders the icon form with context:<variant>:icon"

patterns-established:
  - "Mode-qualified icon prose: every filter icon instruction names the icon-bearing modes (icon/both); label mode says no spans, no host classes, no icon-swap attributes"

requirements-completed: [FILT-01, FILT-02, FILT-03, FILT-04]

coverage:
  - id: D1
    description: "Filter configuration contract: settings-map and FilterContextButton examples with the real import, declared-key case, no target-view default, linked canonical order and settings table, startup map vs lazy floor"
    requirement: FILT-01
    verification:
      - kind: unit
        ref: "tests/test1/test_label_mode_docs.py#test_filter_toggle_reference_contract"
        status: pass
      - kind: unit
        ref: "tests/test1/test_label_mode_docs.py#test_canonical_label_mode_resolution_sections"
        status: pass
      - kind: other
        ref: ".venv/bin/mkdocs build --strict"
        status: pass
    human_judgment: false
  - id: D2
    description: "Corrected renderer contract across reference pages: filter follows the resolved mode and passes it to class lookup; CUSTOM node; icon-bearing-only host fallback; never folded; MICON and post-diagram paragraph preserved"
    requirement: FILT-02
    verification:
      - kind: unit
        ref: "tests/test1/test_label_mode_docs.py#test_filter_toggle_reference_contract"
        status: pass
      - kind: unit
        ref: "tests/test1/test_label_mode_docs.py#test_label_mode_reference_links_and_diagram"
        status: pass
    human_judgment: false
  - id: D3
    description: "Optional-icon browser contract in javascript.md/icons.md: tooltip marker in icon mode only, element/host/no-icon forms, mixed placement, constant labels never icon hooks, collapse-first and non-rollback semantics"
    requirement: FILT-03
    verification:
      - kind: unit
        ref: "tests/js/list.filter.test.js"
        status: pass
      - kind: other
        ref: ".venv/bin/mkdocs build --strict"
        status: pass
    human_judgment: true
    rationale: "No doc test pins javascript.md/icons.md prose; whether it matches the label, both/element, both/host and mixed fixtures is the plan's end-of-phase human check"
  - id: D4
    description: "CHANGELOG Fixed entry (#262) with translated constant Filter, unchanged default and already-configured floor impact; migrating-1.0.md detailed contract and checklist link the compact contract"
    requirement: FILT-04
    verification:
      - kind: integration
        ref: ".venv/bin/pytest tests -n auto"
        status: pass
    human_judgment: true
    rationale: "Plan human-check: confirm the Fixed entry matches observed behavior and both migration entry points cover resolved mode and optional icons"

duration: 7min
completed: 2026-10-26
status: complete
---

# Phase 3 Plan 02: Filter Toggle Docs and Release Notes Summary

**The reference docs now describe the filter toggle's three label modes (configured through the existing maps or `FilterContextButton(label_mode=...)`, with no target-view default). They also cover its optional element/host icon hooks and its unchanged disclosure semantics. A #262 Fixed entry names the context-floor impact, the migration guide tells copied templates to branch on `cv_label_mode`, and doc tests that reject the old icon-only prose pin all of this.**

## Performance

- **Duration:** 7 min
- **Started:** 2026-10-26T15:51:39Z
- **Completed:** 2026-10-26T15:58:30Z
- **Tasks:** 3
- **Files modified:** 8 (plus `deferred-items.md`)

## Accomplishments
- `context_buttons.md` gained a `### The filter toggle` section, placed after the custom-template paragraph and before `### Active state`. It covers:
  - a `CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE = {"filter": "both"}` example
  - a view-level `FilterContextButton(label_mode="label")` example with `from crud_views.lib.view.buttons import FilterContextButton`
  - the `key="search"` case, and the rule that there is no target-view default
  - the startup map versus the per-render floor, and the effect of an existing floor
  - a three-mode table and constant translated labels
  - custom-template ownership, with links to the canonical order, the settings table, the JS contract, the never-folded rule and host placement

  The import was also added to Import Paths.
- Several pages described the stock filter as icon-only. These spots were corrected:
  - the custom-template paragraph
  - the Mermaid `CUSTOM` node (now: resolved data including `cv_label_mode`, and the template owns the markup)
  - `action_menus.md` Rendering and never-folded
  - `buttons.md` class lookup (now `context:<variant>:<mode>`)
  - `buttons.md` icon-host fallback (now icon/both only; label mode renders no icons, even with `None`/`""` host slots)
- `javascript.md` now documents:
  - collapse-first behavior: an adapter that returns false or throws changes nothing
  - no rollback after a failed POST
  - optional icons in element or host form; label mode has neither
  - mixed and switched-off placements fall back to element spans
  - the tooltip marker appears only in icon mode
  - labels are constant and never icon hooks

  `icons.md` describes filter host placement by mode and by whether the host pair is usable.
- CHANGELOG has an Unreleased Fixed bullet, **Filter toggle label mode** (#262). The migration guide's detailed filter contract (formerly lines 331–339) and its checklist bullet both cover the resolved `cv_label_mode`. Both now limit the icon instructions to icon-bearing modes and link the compact contract. The adjacent host-icon sentence was qualified the same way.

## Task Commits

1. **Task 03-02-01: Document filter configuration and pin the new renderer contract** - `a4c4335` (docs)
2. **Task 03-02-02: Publish the optional-icon and browser interaction contract** - `cf6264b` (docs)
3. **Task 03-02-03: Record the public correction and complete all phase quality gates** - `2482c5f` (docs)

**Plan metadata:** see the docs(03-02) commit that adds this file

## Files Created/Modified
- `docs/reference/context_buttons.md` - compact filter contract, corrected custom paragraph and CUSTOM node, Import Paths
- `docs/reference/action_menus.md` - Rendering: the filter follows the resolved mode and has no target-view default. Never-folded bullet updated.
- `docs/reference/buttons.md` - class lookup passes the resolved mode (unknown mode → icon form); host fallback only for icon/both
- `docs/reference/javascript.md` - tooltip row, failure semantics, optional icon forms, constant labels
- `docs/reference/icons.md` - filter host placement qualified by mode and by a usable host pair
- `docs/migrating-1.0.md` - detailed filter-toggle contract, host-icon sentence, checklist bullet
- `tests/test1/test_label_mode_docs.py` - Rendering assertion replaced with positive checks plus never-folded checks; new `test_filter_toggle_reference_contract`
- `CHANGELOG.md` - Unreleased Fixed entry for #262
- `.planning/phases/03-filter-toggle-label-mode/deferred-items.md` - out-of-scope formatting and tooling-drift items

## Decisions Made
- The entry is classified Fixed, not Breaking. Nothing in implementation revealed a separate public break, so `migrating-1.0.md` gets the planned checklist and contract notes and no Breaking entry.
- The per-page override example uses view-level `cv_context_buttons`, because view buttons take precedence over ViewSet buttons (`_cv_find_context_button`). `crud_views.lib.view` does not re-export the class, and the doc test asserts that.
- The A1 fallback is documented as behavior (an unknown mode renders the icon form). It is not presented as a validation path.

## Deviations from Plan

None - plan executed exactly as written. Additions within task scope:
- `migrating-1.0.md`'s host-icon sentence (line ~324) was qualified to icon-bearing modes. A review note (Gemini LOW) asked for this, to keep it consistent with the detailed bullet.
- `javascript.md` mentions that the reset button `#filter-button-reset` does not depend on the label mode (D-10).

**Total deviations:** 0 auto-fixed.
**Impact on plan:** None.

## Issues Encountered
- The first draft of the javascript.md label sentence said the script "never looks for an icon hook in the label". That is not quite true: `querySelectorAll("[data-cv-filter-icon]")` would also match label markup. The sentence now tells authors to keep `data-cv-filter-icon` out of custom labels. This was fixed before the Task 2 commit.

## Verification Evidence

Branch: `introduce-gsd`. This is the existing branch the current workflow kept; it was observed, not freshly approved for this plan. STATE.md's stay-on-branch note is Phase 1 history. No branch was created or switched. Branch and PR splitting into `feat/filter-toggle-label-mode` is left to the surrounding workflow.

Tooling: Python 3.12.3, Django 5.2.14, pytest 9.1.1, MkDocs 1.6.1, Ruff 0.16.10 (manifest `>=0.17,<0.18`), Node v20.20.2, Vitest 4.1.10 (manifest `^5.0.3`), jsdom 29.1.1 (manifest `^30.1.2`). No supported-matrix (nox) run.

| Gate | Command | Result |
|---|---|---|
| Task 1 focused | `.venv/bin/pytest tests/test1/test_filter_toggle_label_mode.py tests/test1/test_label_mode_docs.py -q` | 95 passed, 6.6 s |
| Task 1 RED check | new assertions run (temporary harness, deleted) against `HEAD` copies of the docs | Rendering and filter-contract tests FAIL on the old docs; links/diagram test still passes (MICON and paragraph invariants preserved) |
| Task 2 focused | `npm --prefix . test -- tests/js/list.filter.test.js` | 36 passed, ~1.1 s |
| Task 3 focused | `.venv/bin/pytest tests/test1/test_filter_toggle_label_mode.py tests/test1/test_i18n.py tests/test1/test_action_menus_golden.py tests/test1/test_filter_pinned.py -q` | 114 passed, 9.8 s wall |
| Full Python | `.venv/bin/pytest tests -n auto` | 3457 passed, 1 skipped (pre-existing Django 6.0-only CSP test), 21.5 s |
| Full JS | `npm --prefix . test` | 8 files, 149 passed, ~3 s |
| Docs | `.venv/bin/mkdocs build --strict` | exit 0, 0 warnings (run after each task and at the end) |
| Lint | `.venv/bin/ruff check` | All checks passed |
| Format | `.venv/bin/ruff format --check` | **FAIL (pre-existing, exit 1):** 8 planning Markdown files would be reformatted: the 7 from Phase 2's `deferred-items.md` plus `.planning/phases/02-form-key-grammar/02-VERIFICATION.md` (`6ce34b2`). No Phase 3 file is listed. `ruff format --check src tests` passes (288 files). Not counted as green. |

- All focused checks ran in under the 60 s target.
- `git diff bc672c5..HEAD -- tests/test1/golden/ src/ package.json package-lock.json pyproject.toml uv.lock` is empty, so goldens, source and dependency manifests are unchanged.
- The final diff touches only the 8 planned files. `.planning/config.json` (the user's uncommitted `auto_advance` change) and the untracked `.planning/` files were left alone.

## Downstream-Theme Follow-up (record only)

Consumers that override `crud_views/tags/context_action_filter.html` should:
- branch on the resolved `cv_label_mode` in their context
- render a constant label: visible in `both`/`label`, hidden text plus `title`/tooltip in `icon`
- treat the icon hooks as optional: element spans or host classes with `data-cv-filter-icon-open/close` in `icon`/`both`, none in `label`
- verify their host and mixed placements against the [filter toggle contract](../../../docs/reference/javascript.md#the-filter-toggle-contract)

This repository contains no downstream implementation work.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Phase 3 is complete (2/2 plans) and ready for verification.
- The end-of-phase human checks from the plan are open:
  - compact examples against D-01..D-10
  - optional-icon prose against the label, both/element, both/host and mixed fixtures
  - the Fixed entry and both migration entry points against observed behavior
- Repository-wide `ruff format --check` stays red because of pre-existing planning Markdown files (see `deferred-items.md`).

---
*Phase: 03-filter-toggle-label-mode*
*Completed: 2026-10-26*

## Self-Check: PASSED

All 8 modified files and `deferred-items.md` exist on disk. Commits `a4c4335`, `cf6264b` and `2482c5f` are ancestors of HEAD, and `check evaluation-scope --plan 03-02 --commits-only` resolved all three. Every artifact `contains` pattern is present. Task 1 acceptance (strict MkDocs, focused pytest, assertions that reject the old docs, preserved MICON/paragraph checks) and Task 3 acceptance (Fixed entry with floor impact, both migration locations, branch provenance, recorded gates, no golden/dependency change) were re-checked. The only failing gate is the pre-existing repository-wide `ruff format --check`, reported above.
