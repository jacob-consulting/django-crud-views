---
phase: 02-form-key-grammar
plan: "01"
subsystem: ui
tags: [django, form-key-grammar, system-checks, documentation, pytest]
requires:
  - phase: 01-label-mode-defaults
    provides: Shared mode vocabulary, configurable label floors, and rendering regressions
provides:
  - Independent finite variant-location and form-kind class-key grammar
  - Complete dual-source form mode validation and exact warning coverage
  - Canonical grammar documentation with a live integer default-key count guard
affects: [06-form-button-leaves, theme-authors, system-checks]
tech-stack:
  added: []
  patterns: [Finite immutable class-key vocabularies, two-stage shape and mode validation]
key-files:
  created:
    - .planning/phases/02-form-key-grammar/02-01-RED-tracer.json
    - .planning/phases/02-form-key-grammar/02-01-RED-count.json
    - .planning/phases/02-form-key-grammar/02-01-RED-matrix.json
  modified:
    - src/crud_views/lib/button_classes.py
    - tests/test1/test_button_classes_checks.py
    - tests/test1/test_button_classes.py
    - docs/reference/buttons.md
    - CHANGELOG.md
key-decisions:
  - "Implement locked Option A: form kinds accept all three modes; context/list/card retain variants."
  - "Class-key locations stay independent of button-data locations; form label floors and rendering remain Phase 6 work."
requirements-completed: [KEYS-01, KEYS-02, KEYS-03, KEYS-04]
coverage:
  - id: grammar
    description: All five form kinds accept icon, both and label through theme and settings sources
    requirement: KEYS-02
    verification:
      - kind: unit
        ref: tests/test1/test_button_classes_checks.py#test_all_form_kind_modes_are_accepted_without_icons
        status: pass
    human_judgment: false
  - id: boundaries
    description: Class-key locations remain independent of button-data locations and label floors
    requirement: KEYS-03
    verification:
      - kind: unit
        ref: tests/test1/test_button_classes_checks.py#test_future_button_data_locations_cannot_widen_class_key_grammar
        status: pass
      - kind: unit
        ref: tests/test1/test_action_label_mode_config.py
        status: pass
    human_judgment: false
  - id: count
    description: Exactly one decimal default-key count equals the live table length
    requirement: KEYS-04
    verification:
      - kind: unit
        ref: tests/test1/test_button_classes.py#test_documented_default_key_count_matches_table
        status: pass
    human_judgment: false
  - id: documentation
    description: Canonical grammar table, examples, presence fallback and unchanged form rendering explanation
    requirement: KEYS-01
    verification:
      - kind: other
        ref: .venv/bin/mkdocs build --strict
        status: pass
    human_judgment: true
    rationale: Prose accuracy and the two unclassified source-probe assumptions require end-of-phase review
actuals:
  tokens: 10696
  tasks: 3
  commits: 5
commits: 5
plan_head_before: aa968eca769c3678fe1f21da986f188c23f86874
plan_head_after: d3c63f2124ea2502f793ebdb41acc67e4873fde1
duration: 20min
completed: 2026-10-26
status: complete
---

# Phase 02 Plan 01: Form key grammar Summary

**Form-kind mode keys now pass the existing validator, with independent location allow-lists and a documented 70-key default table.**

## Performance

- Started: 2026-10-26T12:22:39Z; implementation/verification completed about 2026-10-26T12:42:00Z.
- Duration: approximately 20 minutes, including interrupted commit approval and resumption.
- Tasks: 3; product files changed: 5; dependencies installed: none.
- Actual tokens: 42,782 realized diff characters / 4, rounded up; product changes and execution evidence included,
  unrelated config/state edits excluded. Commit count measured from persisted plan ledger through plan_head_after.

## Accomplishments

- Immutable `VARIANT_LOCATIONS` and `FORM_KINDS` recognize action variants or form kinds before shared mode validation.
- Every form kind/mode is accepted independently through settings and theme registration, with no icon prerequisite.
  Exact warning class, ID, message and hint remain covered for malformed shapes and unknown modes; E361 stays independent.
- Future button-data locations cannot broaden class-key acceptance. Presence-based fallback, explicit None/empty
  suppression and exact-key settings precedence are covered without changing the resolver.
- The canonical class-table anchor documents valid/invalid examples, fallback and the Phase 6 rendering boundary.
  One integer guard pins the shipped count to the actual default table. Changelog records a compatible extension.

## Task Commits

1. Task 1 RED: `8876078` — reproduce form mode key rejection.
2. Task 1 GREEN: `a6322d0` — accept finite form kind mode class grammar.
3. Task 2: `340d29a` — cover form mode grammar diagnostics and precedence.
4. Task 3 RED: `ea81ead` — expose stale documented default key count.
5. Task 3 GREEN: `d3c63f2` — publish form kind grammar and correct key count.

## Verification

- Task 1: 28 checks passed; fresh interpreter import under bare configured Django settings passed.
- Task 2: 501 focused tests passed in 0.52s; 26 rendering/crispy/golden/docs regressions passed in 2.99s.
- Task 3: 53 button/documentation tests passed in 0.10s; strict MkDocs build passed in 0.60s.
- The actual count guard rejected in-memory missing, duplicate, one-below and one-above canonical count mutations.
- Full Python suite: **3360 passed, 1 skipped in 22.17s**, Python 3.12.3 / Django 5.2.14.
- Vitest: **126 tests passed across 8 files**, 4.62s.
- Ruff 0.16.10 lint passed. Product formatting passed (`ruff format --check src tests`, 287 files).
- Repository-wide format check reports seven pre-existing planning Markdown files; Ruff also differs from the
  manifest range >=0.17,<0.18. These exact limitations are in `deferred-items.md` and WINDOWS entry 4.
- AST comparison proves `DEFAULT_BUTTON_CLASSES` and `get_button_class` unchanged. Templates, goldens, crispy
  adapters, button-data locations and label floors have no diff. Active branch remains `introduce-gsd`.

## TDD Gate Compliance

| Task | RED evidence | Semantic assessment | GREEN |
|---|---|---|---|
| 1 | `02-01-RED-tracer.json`, RED_EVIDENCE_OK | Target executes and fails at acceptance because form:submit:icon raises W362 | 28 checks pass; a6322d0 |
| 2 | `02-01-RED-matrix.json`, RED_EVIDENCE_OK | Exact pre-phase helper in an isolated process admits added-location variants and rejects form kinds, failing 15 versus 8 warnings | Current implementation passes in focused/full runs; 340d29a |
| 3 | `02-01-RED-count.json`, RED_EVIDENCE_OK | Target executes and fails the intended integer comparison, 64 versus 70 | 53 tests and strict docs build pass; d3c63f2 |

Task 2 expands coverage of behavior implemented by Task 1 and was already green. Its sensitivity probe was
recorded afterward against the exact pre-phase helper, without replacing workspace source. It has no separate
production implementation or fabricated RED-before-GREEN claim. No refactor commit was needed.

## Decisions Made

Followed D-01–D-11 and locked Option A. No new product or architectural decision was introduced.

## Deviations from Plan

- Task 2 is a coverage-only expansion after Task 1 supplied its implementation; retrospective pre-phase helper
  evidence demonstrates boundary sensitivity. The first probe setup lacked configured settings and produced no
  report; it did not authorize implementation. The corrected isolated pytest hook produced valid assertion RED.
- The first RED commit approval was interrupted. Parent committed the preserved RED artifacts after the user
  explicitly resumed execution. The absent ledger was then populated from that commit's authoritative parent.
- Two newly added assertion comparisons were adjusted to satisfy Ruff SIM300 before finalizing Task 2.
- Existing environment/format limitations were documented rather than expanding package or planning-file scope.

## Deferred Issues

- Existing `test_django6_builtin_csp_nonce_roundtrip` skips because installed Django is 5.2.14; built-in CSP
  middleware requires Django 6.0. Registered as WINDOWS entry 3. Other Python/Django matrix combinations were not run.
- Installed Ruff mismatch and seven planning-document format findings remain open in `deferred-items.md` / WINDOWS entry 4.

## Known Stubs

None. Stub-pattern review found only existing changelog history and legitimate icon format placeholders.
No new endpoints, auth paths, file-access APIs or trust-boundary schemas were introduced.

## User Setup Required

None.

## Next Phase Readiness

Plan implementation is complete. Phase 02 remains awaiting external-AI review, phase verification and human prose
review; do not infer phase approval from this plan SUMMARY. Both flagged unclassified KEYS-01/KEYS-02 source-probe
assumptions remain visible in the plan and validation document. No next phase was started.

## Self-Check: PASSED

All five product files, three RED records, validation evidence and this SUMMARY exist. All five task commits
are ancestors of HEAD. Diff whitespace checks pass; no unexpected tracked deletion or generated artifact was added.
