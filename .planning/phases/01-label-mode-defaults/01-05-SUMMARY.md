---
phase: 01-label-mode-defaults
plan: "05"
subsystem: ui
tags: [django, card-actions, label-mode, request-isolation, regression-tests]
requires:
  - phase: 01-label-mode-defaults (01-03)
    provides: Public classmethod card resolver and optional card default
  - phase: 01-label-mode-defaults (01-04)
    provides: Canonical resolution documentation and docs contracts
provides:
  - Instance-aware card stamping for as_view kwargs and request-time assignment
  - Rendered precedence, request isolation, reset-to-None and subclass-hook coverage
  - Accurate class-level versus effective per-action resolver documentation
affects: [phase-03 filter toggle, phase-07 theme API freeze, phase-01 re-verification]
actuals:
  tokens: 24448
  tasks: 3
  commits: 4
plan_head_before: 6549b9c27f734bb74b94e482b362cf12c4f44df7
plan_head_after: 36c86b9e185b544bb6693188a676e9eb9b342c94
tech-stack:
  added: []
  patterns:
    - Own instance values resolve before the existing zero-argument class-level fallback hook
    - RequestFactory render tests attach the real URL resolver_match and render TemplateResponse before DOM checks
key-files:
  created:
    - .planning/phases/01-label-mode-defaults/01-05-RED.json
    - .planning/phases/01-label-mode-defaults/01-05-RED-matrix.json
  modified:
    - src/crud_views/lib/views/card.py
    - tests/test1/test_card_label_mode_render.py
    - tests/test1/test_card_label_modes.py
    - tests/test1/test_label_mode_docs.py
    - docs/reference/action_menus.md
    - docs/reference/card-list-view.md
    - docs/migrating-1.0.md
    - CHANGELOG.md
key-decisions:
  - Own instance None opts directly into the live card floor, bypassing inherited class values and fallback hooks
  - Instances without an own mode still call the existing resolver, preserving classmethod super() and instance-method overrides
  - The classmethod remains callable with no arguments on the class; effective per-action data comes from stamped cv_label_mode
patterns-established:
  - Action mode then no_label then own instance value then class resolver; no shared class mutation
requirements-completed: [LMOD-02, LMOD-03, LMOD-04]
coverage:
  - id: D1
    description: as_view instance label renders visible text and no icon with the setting genuinely absent
    requirement: LMOD-03
    verification:
      - kind: integration
        ref: tests/test1/test_card_label_mode_render.py#test_card_initkwargs_label_without_setting
        status: pass
    human_judgment: false
  - id: D2
    description: Explicit instance choices, own None, subclass hooks and child permissions retain precedence and request isolation
    requirement: LMOD-04
    verification:
      - kind: integration
        ref: .venv/bin/pytest tests/test1/test_card_label_modes.py tests/test1/test_card_label_mode_render.py -q
        status: pass
    human_judgment: false
  - id: D3
    description: Card defaults retain the single lazy accessor, existing validation and protected rendering output
    requirement: LMOD-02
    verification:
      - kind: other
        ref: .venv/bin/pytest tests -n auto
        status: pass
      - kind: other
        ref: git diff --exit-code ebc7c23259ae35b2e4f34047d0da903e68a48ac8 -- tests/test1/golden src/crud_views/templates examples
        status: pass
    human_judgment: false
  - id: D4
    description: Four documentation surfaces distinguish class-level defaults from effective stamped mode and preserve migration disclosure
    requirement: LMOD-03
    verification:
      - kind: unit
        ref: tests/test1/test_label_mode_docs.py
        status: pass
      - kind: other
        ref: .venv/bin/mkdocs build --strict
        status: pass
    human_judgment: false
duration: 8min
completed: 2026-10-26
status: complete
---

# Phase 1 Plan 05: Instance-aware card label modes Summary

**Card actions now honor as_view and request-local modes while preserving the public classmethod resolver, subclass fallback hooks and permission-aware rendering.**

## Performance

- Started: 2026-10-26T10:55:59Z
- Implementation and final verification completed: 2026-10-26T11:03:08Z
- Duration: 8 min including execution bookkeeping
- Tasks: 3
- Files: 8 planned implementation/documentation files and 2 RED evidence records, plus execution metadata
- Actual tokens: 24,448, measured as ceil(characters / 4) over the realized task-commit diff.
- Commits: 4 measured from the persisted plan ledger before the separate metadata commit.

## Accomplishments

- The real card render path honors own instance values after action.label_mode and no_label. An own None reads default_label_mode("card") lazily; an instance without its own value still calls the existing subclass resolver.
- Rendered regressions cover initkwargs, setup, dispatch, get_queryset, strict-floor bypass, sequential requests, nested live settings, reset-to-None, class and instance resolver overrides, action accessibility and child permissions.
- The canonical resolution section, card reference, migration guide and changelog explain class-level defaults separately from effective per-action cv_label_mode. The original raw-None Python break and setting-first #213 recipe remain disclosed.

## Task Commits

1. Task 01-05-01: `8f661d3` — RED tracer and persisted JUnit evidence; `e1bd559` — instance-aware render resolution.
2. Task 01-05-02: `107117f` — expanded request/precedence/subclass/child coverage and pre-fix matrix evidence.
3. Task 01-05-03: `36c86b9` — class-resolver versus effective-mode documentation and extended existing contracts.

Normal commit hooks ran. No branch, branching configuration, dependency, template, example or golden was changed.

## RED / GREEN / REFACTOR Evidence

- **Task 1 RED:** the target executed through as_view and a rendered 200 response, then failed the planned `_icons(button) == []` assertion: the Details action contained one icon. The persisted unchanged JUnit report in `01-05-RED.json` returned `RED_EVIDENCE_OK`; semantic inspection confirmed the intended assertion failed.
- The first helper attempt stopped on missing RequestFactory resolver_match. This was invalid RED, corrected in test setup before recording the accepted assertion evidence or changing production code.
- **Task 1 GREEN:** the focused target passed; the complete card suite passed 26 tests. After the implementation commit, both tracer verify commands were rerun successfully: 1 and 26 passed. Tracer verified end-to-end before expansion.
- **Task 2:** all 45 card tests were initially green because Task 1 already implemented the complete planned branch. Investigation against exact pre-fix source `6549b9c:src/crud_views/lib/views/card.py` produced 18 failing rendered cases. The own-None target failed its planned one-icon assertion, and the unchanged complete JUnit report in `01-05-RED-matrix.json` returned `RED_EVIDENCE_OK`. The pre-fix source was restored to the Task 1 repair in a finally block; all 45 tests then passed. No extra production change was needed.
- **Task 3:** the expanded documentation contracts first failed 3 tests against the old guidance; after the prose changes, all 6 passed and the strict documentation build succeeded.
- **Refactor:** none needed; the production change adds only the own-instance branch and clarifies its existing comments/docstring.

## Assignment and Settings Matrix

| Path | Settings / class arrangement | Rendered evidence |
|------|------------------------------|-------------------|
| as_view(label), setup(label) | Setting genuinely absent | Visible Details, zero icons |
| as_view(both), setup(both) | card=label; invalid strict card floor | One aria-hidden icon and visible Details; no eager-floor exception |
| setup, dispatch, get_queryset | Absent setting and card=label | Successive label, both and unset requests each get their own expected appearance; class stays None |
| Action label_mode; no_label | Explicit instance label/both | Action mode wins, including defensive label_mode+no_label arrangement; no_label stays icon-only without DeprecationWarning |
| Own instance None | Conflicting inherited class label/both | Live configured floor wins; same instance follows nested override_settings entry/exit and reset; later request retains class mode |
| No own instance mode | Classmethod override with super(); instance-method request-dependent override; inherited class both | Fallback hook renders label; own both overrides the hook |
| Child action | Publisher instance label, floor both | Books renders text only with child permission and is absent without it |
| Class API | Class and subclass calls, nested settings | Public zero-argument classmethod remains callable; E210/exact-mode/empty-action tests pass |

## Verification Results

| Command / gate | Result |
|----------------|--------|
| Card unit/render suite | 45 passed |
| Docs contracts | 6 passed |
| Strict MkDocs build | Successful, no warnings |
| Plan rendering/golden/card/frame/heading regression command | 112 passed |
| `.venv/bin/pytest tests -n auto` | 3076 passed, 1 existing version-gated skip, 27.13s |
| `npm --prefix . test` | 8 files, 126 tests passed |
| `.venv/bin/ruff check` | All checks passed |
| Owned Python-file `ruff format --check` | 4 files already formatted |
| Protected-path diff against ebc7c23259ae35b2e4f34047d0da903e68a48ac8 | Empty, exit 0 |
| Protected-path porcelain status | Empty |
| Branch assertions before all tasks and commits | feat/label-mode-defaults |

The existing skip is `tests/test1/test_assets.py:332`, built-in CSP middleware requiring Django 6.0; this run uses Django 5.2.14. No skipped test was introduced. Prior unrelated planning-Markdown formatting findings remain outside this plan's targeted formatting gate.

## Decisions Made

Followed the plan's receiver distinction: own instance None is meaningful configuration, while an absent own value preserves the shipped fallback customization seam. The classmethod signature and implementation remain intact; rendered per-action stamping supplies the instance-sensitive result.

## Deviations from Plan

1. **[Rule 3 - Blocking] RequestFactory resolver context:** the real toolbar requires request.resolver_match. The helper now resolves the actual reversed URL before invoking as_view; accepted RED evidence was collected only after this setup correction. File: `tests/test1/test_card_label_mode_render.py`; commit `8f661d3`.
2. **[Execution adjustment] Task 2 needed tests only:** its initially green result was investigated against the exact recorded pre-fix source, producing 18 baseline failures. The already-complete Task 1 implementation was retained and the expanded matrix committed without an artificial second implementation change. Files: card test modules and matrix evidence; commit `107117f`.

Both entries are recorded as fixed in `.planning/WINDOWS.md`; no open defect remains from these adjustments. State task progress and the validation map were updated. Phase-wide advancement, ROADMAP completion and requirement certification remain with the parent orchestrator's independent review/verification, as dispatched.

## Threat Model Compliance

- T-01-13: explicit instance and action precedence proven through actual rendered leaves.
- T-01-14: implementation never writes class state; sequential requests and reset tests prove isolation.
- T-01-15: explicit instance choices render with an invalid strict card floor, proving lazy fallback.
- T-01-16: existing disabled/POST/menu tests pass; child access granted/denied cases render correctly.
- T-01-SC: no dependencies installed or changed.

Stub scan found no new incomplete behavior. Empty action groups are intentional existing behavior. No new endpoint, auth path, schema or file-access trust boundary was introduced.

## Flagged Items Carried to Re-verification

- EDGE-LMOD-02-unclassified: completeness of the three-consumer set remains flagged; the receiver bug inside the known card consumer is repaired.
- EDGE-LMOD-04-unclassified: lifecycle completeness beyond the concrete nested-setting and request-isolation cases remains unclassified.
- Product-intent prohibition, flagged-unverified: label-mode defaults must not become theme-owned policy or override explicit project/view/button choices.
- Product-intent prohibition, flagged-unverified: unchanged rendered output must not be presented as absence of a breaking Python attribute change.

These carried items are not machine-certified by this summary.

## User Setup Required

None. Git writes required normal filesystem escalation; all commits used the current branch and normal hooks.

## Next Phase Readiness

Both actionable CR-01 gaps are ready for independent re-verification. Phase 1 remains awaiting parent review and verification. The deferred filter toggle remains Phase 3; no_label removal and name changes remain outside this plan. Existing completed summaries and verification findings were preserved.

## Self-Check: PASSED

The summary and both evidence files exist. Commits 8f661d3, e1bd559, 107117f and 36c86b9 are ancestors of HEAD; the persisted ledger measures 4 task commits between plan_head_before and plan_head_after. Protected paths are unchanged, and all planned implementation files exist.
