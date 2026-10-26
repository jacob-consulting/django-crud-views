---
phase: 01-label-mode-defaults
plan: "04"
subsystem: docs
tags: [django, label-mode, documentation, mkdocs, changelog, contract-tests]

requires:
  - phase: 01-label-mode-defaults (plan 01-01)
    provides: "default_label_mode, LABEL_MODE_DEFAULTS, strict/log recovery, crud_views.E108"
  - phase: 01-label-mode-defaults (plan 01-02)
    provides: "context/list resolution order through the configured floor; E211 'string or None' wording"
  - phase: 01-label-mode-defaults (plan 01-03)
    provides: "CardListView.cv_get_card_actions_label_mode(), CHANGELOG/migration card entries"
provides:
  - "settings.md#label-mode-configuration: the single merge-or-replace table for every label-mode knob, plus public API, E108 and strict behaviour"
  - "action_menus.md#context-label-mode-resolution / #list-label-mode-resolution / #card-label-mode-resolution: the canonical resolution order, one section per location"
  - "tests/test1/test_label_mode_docs.py: the documented card recipe renders through {% cv_button %}; table, section, link, diagram, changelog-release and check-table contracts"
  - "PROJECT.md: renaming the context pair rejected (not deferred); the Phase 7 no_label wording made exact"
affects: [phase-02 class keys (buttons.md class-table prose now names resolved modes), phase-03 filter toggle (documented as outside the configuration), phase-07 API freeze]

actuals:
  tokens: 13860
  tasks: 2
  commits: 2
plan_head_before: c3ffc307f928743f951efb9613b71555d20f7b12
plan_head_after: 07d76f2d27a9084acf03d2e89a78b976a1d1529d

tech-stack:
  added: []
  patterns:
    - "Docs contract tests: select by content (ast.literal_eval over fences that mention the setting), section-scoped and fence-aware heading parsing, whitespace/backtick normalization before phrase checks"
    - "Changelog release selected by a stable bullet, not by heading name; tested against the real text and an in-memory renamed-release variant"

key-files:
  created:
    - tests/test1/test_label_mode_docs.py
    - .planning/phases/01-label-mode-defaults/deferred-items.md
    - .planning/phases/01-label-mode-defaults/01-04-SUMMARY.md
  modified:
    - docs/reference/settings.md
    - docs/reference/action_menus.md
    - docs/reference/card-list-view.md
    - docs/reference/context_buttons.md
    - docs/reference/buttons.md
    - docs/migrating-1.0.md
    - CHANGELOG.md
    - .planning/PROJECT.md

key-decisions:
  - "The three canonical resolution headings sit under the existing ## Label mode section, ahead of ### Target-view default, so the #label-mode and #target-view-default anchors stay valid"
  - "Secondary pages (card-list-view, context_buttons, buttons, migration guide, changelog) link the canonical sections; their old broad #label-mode links stay only where they point at the map overview"
  - "The E108 link in migrating-1.0.md's check list was also retargeted to #label-mode-configuration (phase-owned link, same anchor family)"
  - "Docs tests use small private helpers (section, row, bullets, anchors) with fence-aware heading detection, because '# settings.py' comments inside code fences otherwise end a section"

patterns-established:
  - "Label-mode precedence is stated once per location in action_menus.md; any other page links to it instead of restating the order"

requirements-completed: [LMOD-01, LMOD-02, LMOD-03, LMOD-04, LMOD-05, LMOD-06]

coverage:
  - id: D1
    description: "The documented {'card': 'label'} setting, selected from settings.md by content, renders a label-only card action through the real cv_button tag; the same raw context renders icon + text under empty defaults"
    requirement: LMOD-03
    verification:
      - kind: integration
        ref: "tests/test1/test_label_mode_docs.py#test_documented_card_floor_renders_label_only"
        status: pass
    human_judgment: false
  - id: D2
    description: "One settings table separates the per-location merge of CRUD_VIEWS_LABEL_MODE_DEFAULTS from whole-layer replacement of the per-action maps; the existing context/list map rows name the configurable floor; public API, lazy reads, strict/non-strict and E108 documented"
    requirement: LMOD-01
    verification:
      - kind: unit
        ref: "tests/test1/test_label_mode_docs.py#test_label_mode_configuration_table"
        status: pass
    human_judgment: false
  - id: D3
    description: "action_menus.md has exactly one canonical section each for the context, list and card resolution, plus the E108 error row, E211 'string or None' wording and filter-toggle scope"
    requirement: LMOD-02
    verification:
      - kind: unit
        ref: "tests/test1/test_label_mode_docs.py#test_canonical_label_mode_resolution_sections"
        status: pass
    human_judgment: false
  - id: D4
    description: "Card reference, migration guide, changelog, context_buttons diagram (MICON) and buttons.md link the canonical sections; card docs describe raw None / floor both / resolver"
    requirement: LMOD-04
    verification:
      - kind: unit
        ref: "tests/test1/test_label_mode_docs.py#test_label_mode_reference_links_and_diagram"
        status: pass
      - kind: command
        ref: ".venv/bin/mkdocs build --strict"
        status: pass
    human_judgment: false
  - id: D5
    description: "The release carrying the card disclosure (selected by its stable bullet) keeps the setting-first #213 recipe, the attribute disclosure, the Fixed repair and the #269 configurable-floor bullet, also after an in-memory rename; the migration guide matches"
    requirement: LMOD-05
    verification:
      - kind: unit
        ref: "tests/test1/test_label_mode_docs.py#test_card_migration_contract"
        status: pass
    human_judgment: false
  - id: D6
    description: "buttons.md System checks lists E106/E108 as errors, E210 accepts None as unset, E211 matches action_menus.md's 'string or None' wording"
    requirement: LMOD-06
    verification:
      - kind: unit
        ref: "tests/test1/test_label_mode_docs.py#test_button_label_mode_check_reference"
        status: pass
    human_judgment: false
  - id: D7
    description: "PROJECT.md records the stable context-name pair (rename rejected) and the pre-1.0 no_label removal with exact Phase 7 wording"
    verification:
      - kind: command
        ref: "01-04-02 one-off PROJECT.md grep (verify block 3)"
        status: pass
    human_judgment: true
    rationale: "Planning-state decision record; permanent tests deliberately never read .planning (A13), so a reviewer confirms the wording"

duration: 10min
completed: 2026-10-26
status: complete
---

# Phase 1 Plan 04: Label-mode configuration contract and reference links Summary

**`settings.md#label-mode-configuration` is now the single merge-or-replace table for every label-mode knob, and `action_menus.md` states the context, list and card resolution once each. A docs contract test renders the documented `{"card": "label"}` recipe through the real `{% cv_button %}` tag, and every secondary page, the migration guide and the changelog link to these sections.**

## Performance

- **Duration:** 10 min
- **Started:** 2026-10-26T08:38:53Z
- **Completed:** 2026-10-26T08:48:57Z
- **Tasks:** 2
- **Files modified:** 9 (plus this summary and deferred-items.md)

## Accomplishments

- **settings.md:** a new `CRUD_VIEWS_LABEL_MODE_DEFAULTS` row with the exact effective defaults and E108. The existing context-map row now names the target-view step and the configurable floor; the old "keys not named are `icon`" wording is gone. The list-map row has its own description with no target-view step. The new `### Label-mode configuration` section holds a Knob / merge or replace / layer / keys table with 7 rows, including a separate row for the singular target-view scalar. It also states "Existing per-action maps keep whole-dict replacement semantics.", gives two independent setting examples, documents the public API at its exact module path, and covers E108 plus strict and non-strict behaviour.
- **action_menus.md:** `### Context label-mode resolution`, `### List label-mode resolution` and `### Card label-mode resolution` sit under `## Label mode` and replace the duplicated ordering prose. The target-view default is described as sitting just above the project floor. A filter-toggle scope note was added, along with an E108 row whose Meaning includes "error". The E211 row now uses "string or None".
- **Link retargeting:** card-list-view.md, migrating-1.0.md (attribute bullet and E108 list), CHANGELOG.md, context_buttons.md and buttons.md now point at the canonical anchors.
- **context_buttons.md:** MICON now displays `defaults map (default icon)`. The prose below the diagram names the `"context"` entry of the setting, links the context section, and tells the plural attribute apart from the singular one.
- **buttons.md:**
  - The leaf `cv_label_mode` cell links the context and list sections.
  - The class-table intro calls `icon` the package floor, and the applicability prose describes modes as they are resolved today (no more "waiting for #216"). Grammar, rows and counts are unchanged.
  - The theme-recipe card prose explains the raw `None`, the floor `"both"` and the resolver.
  - The System checks table gains E106/E108 error rows, the E210 None-as-unset note, and the E211 "string or None" wording.
- **CHANGELOG.md:** the #269 bullet now names `CRUD_VIEWS_LABEL_MODE_DEFAULTS["context"]` (package default `"icon"`) instead of a fixed `"icon"` fallback.
- **PROJECT.md:** renaming the context pair is recorded as rejected rather than deferred. The no_label row carries the exact Phase 7 wording, "deprecated, removed in 1.0.0". No rows were duplicated.

## Task Commits

1. **Task 01-04-01 (tracer):** `031642e` (docs): canonical table, resolution sections, link retargeting and the first 4 docs tests. Tracer gate (auto mode): the verify was re-run after the commit (4 passed, strict build clean), and "Tracer verified end-to-end — expanding" was logged.
2. **Task 01-04-02:** `07d76f2` (docs): remaining references, PROJECT.md handoff, and the remaining 2 tests plus the extended links/diagram test.

## Verification Results

| Gate | Result |
|---|---|
| `.venv/bin/pytest tests/test1/test_label_mode_docs.py -q` | 6 passed |
| `.venv/bin/pytest tests -n auto` | 3056 passed, 1 skipped |
| `npm --prefix . test` | 8 files, 126 tests passed |
| `.venv/bin/mkdocs build --strict` | built, no warnings |
| `.venv/bin/ruff check` | All checks passed |
| `.venv/bin/ruff format --check` | **6 files would be reformatted, all pre-existing `.planning/` markdown** (see Issues). Package code and tests are clean; with `--exclude .planning`, 521 files are already formatted |
| `git diff --exit-code ebc7c23 -- tests/test1/golden src/crud_views/templates examples` | empty (rc 0) |
| `git status --porcelain -- tests/test1/golden src/crud_views/templates examples` | empty |
| 01-04-02 PROJECT.md decision grep | both rows printed, counts 1/1 |

**Mutation checks** (each doc edit was reverted in place, the docs tests run, then the file restored): reverting the #269 wording, the leaf-row parenthetical, the MICON label, the E108 level, the migration recipe order or the documented card value each made exactly one docs test fail.

## Decisions Made

- The canonical headings sit before `### Target-view default` inside `## Label mode`, so the existing anchors still resolve.
- The migrating-1.0.md E108 link was retargeted to `#label-mode-configuration` along with the attribute-bullet links.
- The test helpers ignore headings inside code fences, because the `# settings.py` comment in the recipe fences would otherwise end a section early.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fence-aware heading parsing in the docs test**
- **Found during:** Task 01-04-01
- **Issue:** The `# settings.py` comment lines inside the Python fences matched the heading regex, so `### Label-mode configuration` appeared to end at the first example.
- **Fix:** Headings inside fenced code are ignored, and phrase checks run on whitespace-normalized text so line wrapping does not matter.
- **Files modified:** tests/test1/test_label_mode_docs.py
- **Commit:** 031642e

**2. [Scope note] Private helper functions in the test module**
- The plan says no custom helpers are *required*. A few small private helpers (`_section`, `_row`, `_bullets`, `_subsection`, `_anchors`, `_flat`, `_card_release_contract`) keep the region-scoped assertions readable. No permanent test reads `.planning/`.

---

**Total deviations:** 1 auto-fixed (blocking), 1 scope note. **Impact:** test-internal only; no behaviour or doc-scope change.

## Issues Encountered

- **Pre-existing `ruff format --check` failure (not introduced here):** the repo-wide gate flags 6 `.planning/` markdown files (codebase map, research, 01-PATTERNS, 01-RESEARCH) whose Python fences ruff now formats. This plan did not modify any of them. It is logged in `deferred-items.md` and was not fixed (scope boundary). This gate is **not** reported as green.

## Source-audit reconciliation

- D-19/D-23: the stable-name pair and the no_label removal are recorded in PROJECT.md, and removal stays outside Phase 1 (no code or DeprecationWarning).
- D-21/D-22: setting row, effective defaults and E108 are documented.
- D-24: the merge/replace table is present.
- D-25: one canonical chain per location; secondary pages link to it.
- D-26: no example, template or golden file was edited (protected-path gates are empty).
- Carried to verification as flagged items, as the plan requires: the two unclassified probe edges and the two descriptor-less prohibitions from the phase source audit. None of them was re-certified here.

## Acceptance note (external reference theme)

The external reference theme should audit:
- direct reads of `cv_card_actions_label_mode`, switching to `cv_get_card_actions_label_mode()` or the stamped `cv_label_mode`;
- any registered `context:*:label|both` / `list:*:label|both` class keys, which now take effect as soon as a project sets `CRUD_VIEWS_LABEL_MODE_DEFAULTS`.

No other repository was edited.

## Threat Model Compliance

- T-01-10 (tampering, configuration docs): mitigated. The named sections are bound to exact precedence and defaults, and the setting example is rendered for real.
- T-01-11 (EoP, docs test): mitigated. The test uses `ast.parse` and `ast.literal_eval` only and never calls exec.
- T-01-12 (information disclosure): mitigated. Examples are generic, with no downstream project names.

## User Setup Required

None.

## Next Phase Readiness

Phase complete, ready for the next step: all four plans of Phase 1 have summaries, and LMOD-01 through LMOD-06 are satisfied.

## Self-Check: PASSED

- Created and modified files exist: tests/test1/test_label_mode_docs.py, deferred-items.md and the 8 modified docs/planning files.
- Commits 031642e and 07d76f2 are ancestors of HEAD. The ledger count is 2 commits from c3ffc30 to 07d76f2.
