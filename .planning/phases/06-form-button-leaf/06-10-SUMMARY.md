---
phase: 06-form-button-leaf
plan: "10"
subsystem: ui
tags: [django-crispy-forms, form-buttons, icons, deepcopy, gap-closure]

requires:
  - phase: 06-form-button-leaf
    provides: "06-04 kind-default icons (_KIND_ICONS, icon= sentinel), 06-05 filter-helper per-instance layout deepcopy, 06-06 form missing-icon policy"
provides:
  - "Copy-stable omitted-icon state on Submit/Button/Reset (private bool _cv_kind_icon)"
  - "Form normalizer cv_icon contract enforced: nonblank str or None"
  - "Real-crispy regressions for copied class-level and assigned filter layouts, direct copied adapters and icon normalization"
  - "Measured closure of 06-REVIEW CR-01, WR-01, WR-02"
affects: [06-verification, phase-07, downstream-themes]

actuals:
  tokens: 7741
  tasks: 3
  commits: 5
plan_head_before: 0f768b06a58ecabc17d1163babf23df635bfb680
plan_head_after: 3e6a4503ad822089cc0886f689ed4154e6f5c354

tech-stack:
  added: []
  patterns:
    - "Constructor-only sentinel comparison: record omission as a bool so copies keep their meaning"
    - "Normalize leaf-contract types at the normalizer boundary before diagnostics"

key-files:
  created:
    - .planning/phases/06-form-button-leaf/06-10-SUMMARY.md
  modified:
    - src/crud_views/lib/crispy/buttons.py
    - src/crud_views/lib/view/button_data.py
    - tests/test1/test_crispy_buttons.py
    - tests/test1/test_button_data.py
    - .planning/phases/06-form-button-leaf/06-REVIEW-DISPOSITION.md
    - .planning/phases/06-form-button-leaf/06-ACCEPTANCE.md
    - .planning/phases/06-form-button-leaf/06-VALIDATION.md

key-decisions:
  - "06-10: icon= omission is stored as the private bool _cv_kind_icon (sentinel compared in __init__ only); deepcopy isolation of filter layouts is kept, no copy-stable sentinel class"
  - "06-10: _form_button_data treats any non-str or whitespace-only cv_icon as None before availability, diagnostics, host classes and the leaf; accepted strings are kept exactly (never stripped)"

patterns-established:
  - "Copied-layout regression: render package adapters placed in class-level and assigned ListViewFilterFormHelper layouts through the real {% crispy %} tag under both/icon, strict and lenient"

requirements-completed: [FORM-02, FORM-05, FORM-08, FORM-09, FORM-10, FORM-12]

coverage:
  - id: D1
    description: "Copied class-level and assigned filter layouts render package Submit/Reset with fa-filter / fa-rotate-left in both and icon modes, strict and lenient, with no warning or exception and isolated layouts"
    requirement: FORM-08
    verification:
      - kind: integration
        ref: "tests/test1/test_crispy_buttons.py#test_copied_filter_layout_keeps_kind_icons"
        status: pass
    human_judgment: false
  - id: D2
    description: "Direct copy/deepcopy of every adapter kind keeps its named str icon independent of the submitted name; explicit None, empty, workflow and prefixed icons survive copying"
    requirement: FORM-09
    verification:
      - kind: unit
        ref: "tests/test1/test_crispy_buttons.py#test_copied_adapter_keeps_icon_contract"
        status: pass
      - kind: unit
        ref: "tests/test1/test_crispy_buttons.py#test_copied_adapter_preserves_explicit_icon"
        status: pass
    human_judgment: false
  - id: D3
    description: "Form normalizer emits cv_icon as a nonblank str or None; invalid icons are quiet in label/both, raise naming None in strict icon mode and log naming None in lenient icon mode; input never mutated"
    requirement: FORM-02
    verification:
      - kind: unit
        ref: "tests/test1/test_button_data.py#test_form_icon_normalization_*"
        status: pass
      - kind: unit
        ref: ".venv/bin/pytest tests/test1/test_button_data.py tests/test1/test_form_button_checks.py -q"
        status: pass
    human_judgment: false
  - id: D4
    description: "Review disposition, acceptance and validation records show measured CR-01/WR-01/WR-02 closure; IN-01/IN-02 and human checks preserved"
    requirement: FORM-12
    verification:
      - kind: other
        ref: "06-10-PLAN.md Task 3 disposition YAML/table gate (exit 0)"
        status: pass
    human_judgment: false

duration: 13min
completed: 2026-10-28
status: complete
---

# Phase 06 Plan 10: Copied-layout icon gap closure Summary

**Deep-copied crispy Submit/Button/Reset adapters now keep their kind icons because an omitted `icon=` is stored as a bool, and the form normalizer only lets a nonblank `str` or None through as `cv_icon`. Before these fixes, a custom filter layout lost its icons in both mode and failed with a false `ValueError` in strict icon mode.**

## Performance

- **Duration:** about 13 min
- **Started:** 2026-10-28T10:26:00Z
- **Completed:** 2026-10-28T10:39:00Z
- **Tasks:** 3
- **Files modified:** 7 (2 source, 2 test, 3 planning records), plus this summary

## Accomplishments

- **CR-01 fixed (`f33d396`).** `_TableClassMixin.__init__` sets `self._cv_kind_icon = icon is _KIND_ICON` and
  stores `None` in `_cv_icon` when `icon=` is omitted. `_cv_button_context` picks `_KIND_ICONS[kind]` from that
  bool. A bool survives `copy.deepcopy` unchanged, so class-level and caller-assigned filter layouts, which
  `ListViewFilterFormHelper._cv_prepare_layout` copies for each helper, keep `fa-filter` / `fa-rotate-left`. The
  constructor signature, explicit `None` / `""` suppression and icon overrides behave as before.
- **WR-02 fixed (`61103dd`).** `_form_button_data` replaces `cv_icon` with None unless it is a `str` with
  non-whitespace content. This happens before `_icon_available`, the strict/lenient diagnostics,
  `icon_host_keys` and the returned leaf data. Strict errors and lenient warnings now name `None`, never an
  object repr. Valid strings are kept byte-for-byte. A nonblank string that does not resolve still goes through
  the existing missing-icon policy under its own value.
- **WR-01 fixed (`ae83e62`).** New tests render real `{% crispy form helper %}` copied layouts:
  - class-level, assigned before the first render, and assigned between renders
  - both and icon modes, strict and lenient
  - two helper instances with interleaved renders, checking source-layout immutability, distinct copies,
    stable ids and classes, one action group and the hidden `sort` control

  Further tests cover direct copies of all five kinds and explicit-icon copies.
- **Records updated (`3e6a450`).** The REVIEW-DISPOSITION YAML and table, ACCEPTANCE §11/§12 and VALIDATION now
  record the measured closure.

## TDD evidence

| Cycle | RED commit | RED result (measured) | GREEN commit | GREEN result |
|---|---|---|---|---|
| Task 1 copied adapters | `ae83e62` | `-k "copied_filter_layout or copied_adapter"`: exit 1, 17 failed / 5 passed. Both mode: `assert [] == ['fa-solid fa-filter']`. Strict icon: `ValueError … its icon <object object at 0x…> is not available`. Direct deepcopy: `cv_icon` of type `object` | `f33d396` | 22 passed |
| Task 2 icon normalization | `7f974ad` | `-k form_icon_normalization`: exit 1, 92 failed / 72 passed. `assert <object …> is None`, `assert '   ' is None`, and messages naming reprs | `61103dd` | 164 passed; Task 2 gate 731 passed |

**RED evidence check.** The `tdd-red-evidence` classifier read each run's pytest JUnit XML and returned
`RED_EVIDENCE_OK` for five single-target runs:

- `test_copied_adapter_keeps_icon_contract[submit]`
- `test_copied_filter_layout_keeps_kind_icons[class-both-strict]`
- `test_copied_filter_layout_keeps_kind_icons[class-icon-strict]`
- `test_form_icon_normalization_label_and_both_are_quiet[object-label-lenient]`
- `test_form_icon_normalization_strict_icon_mode_raises_naming_none[spaces-filter-submit]`

A first multi-case run was rejected with `no_target_test_failure` because the target name was not
parametrize-qualified. It was rerun with qualified single targets.

**What each RED failure showed.** Every target ran and failed on the planned icon/DOM assertion or on the
defect's own `ValueError`. None failed on collection, import or fixture errors. Some cases passed before the fix,
as intended, because they guard behavior that was already correct:

- explicit-icon copies
- falsey invalid icons
- nonblank strings

## Task Commits

1. **Task 1: Render copied custom filter actions with their semantic icons** (tracer, TDD)
   - `ae83e62` test(06-10): add failing copied-layout icon regressions
   - `f33d396` fix(06-10): keep kind icons on deep-copied form button adapters
   - Tracer gate: the `<verify>` re-run passed (22 passed) before Task 2 started.
2. **Task 2: Enforce the form icon type contract before applying the missing-icon policy** (TDD)
   - `7f974ad` test(06-10): add failing form icon normalization regressions
   - `61103dd` fix(06-10): normalize non-str and blank form icons to None
3. **Task 3: Record measured gap closure and update only the resolved review findings**
   - `3e6a450` docs(06-10): record measured closure of CR-01, WR-01 and WR-02

## Measured gates (HEAD `61103dd` for code; `3e6a450` for records)

| Gate | Exit | Result |
|---|---|---|
| `.venv/bin/pytest tests/test1/test_filter.py tests/test1/test_crispy_buttons.py tests/test1/test_button_data.py -q` | 0 | 745 passed in 18.49 s (planning baseline 559 with the defect) |
| `.venv/bin/pytest tests/test1/test_button_data.py tests/test1/test_form_button_checks.py -q` | 0 | 731 passed in 9.64 s |
| `.venv/bin/pytest tests -n auto -q` | 0 | 4631 passed in 60.42 s |
| `.venv/bin/nox -s crispy_floor` | 0 | 2063 passed on Django 4.2 and on 6.0.9 (crispy 2.0 / bootstrap5 2023.10) |
| `.venv/bin/ruff check` | 0 | All checks passed |
| `.venv/bin/ruff format --check` (4 changed code files) | 0 | already formatted |
| `.venv/bin/ruff format --check` (whole repo) | 1 | 10 pre-existing planning Markdown files (WINDOWS #4 set plus `06-REVIEW.md`); none touched here |
| Task 3 disposition YAML/table gate | 0 | CR-01/WR-01/WR-02 fixed, IN-01/IN-02 open, open 2 / total 5 |

## CR-01 / WR-01 / WR-02 mapping

| Finding | Disposition | Fix | Evidence |
|---|---|---|---|
| CR-01 | fixed | `f33d396` | `test_copied_filter_layout_keeps_kind_icons` (12), `test_copied_adapter_keeps_icon_contract` (5), red at `ae83e62` |
| WR-01 | fixed | `ae83e62` (tests) | The copied-adapter path is now rendered in both/icon, strict and lenient, through the real tag |
| WR-02 | fixed | `61103dd` | `test_form_icon_normalization_*` (164), red at `7f974ad` |

## Files Created/Modified

- `src/crud_views/lib/crispy/buttons.py`: a private `_cv_kind_icon` bool; the sentinel is compared in the
  constructor only.
- `src/crud_views/lib/view/button_data.py`: the form branch normalizes `cv_icon` to a nonblank `str` or None.
- `tests/test1/test_crispy_buttons.py`: copied-layout and copied-adapter regressions (22 cases).
- `tests/test1/test_button_data.py`: icon type, whitespace, diagnostic and purity regressions (164 cases).
- `.planning/phases/06-form-button-leaf/06-REVIEW-DISPOSITION.md`: three findings marked fixed, with their sources.
- `.planning/phases/06-form-button-leaf/06-ACCEPTANCE.md`: a dated §12 and a §11 status line; §1–§10 are kept
  as history.
- `.planning/phases/06-form-button-leaf/06-VALIDATION.md`: task rows 06-10-1..3, threats T-06-18..21 and a
  closure note.

## Decisions Made

- **Bool flag instead of a copy-stable sentinel class.** The plan prescribed it, and it keeps the constructor and
  the explicit-None semantics without adding a copy policy.
- **Blankness is checked with `strip()`, but accepted strings are not changed.** For example, `" save "` passes
  through exactly as given.

## Deviations from Plan

**1. The GREEN commits use the `fix` type, not `feat`.**
- **Found during:** Tasks 1 and 2
- **What changed:** The TDD reference's GREEN pattern is `feat(...)`. Both GREEN changes are defect
  corrections, so they use `fix(06-10)`, following the commit-type table.
- **Effect:** `workflow.tdd_mode` is false, so the gate is not enforced. A strict `^feat\(06-10\)` search finds
  no match, but each `fix` commit directly follows its `test` commit.

**2. An extra floor run.**
- **Found during:** Task 3
- **What changed:** I also ran `nox -s crispy_floor`, which the plan did not list. This reinstalls only the
  declared floor pins into the existing nox venvs; no new package was added. I ran it because both changed test
  files are in `CRISPY_FLOOR_TESTS`.
- **Effect:** Additive evidence only.

No other changes to the planned work, and no new `Breaking` entry was needed.

## TDD Gate Compliance

- RED `test(06-10)`: `ae83e62`, `7f974ad`. Each is followed by GREEN `fix(06-10)`: `f33d396`, `61103dd`.
- No REFACTOR commit was needed.

## Issues Encountered

- **Classifier needed qualified target names.** The RED classifier needs the exact parametrized test name;
  a multi-case selection returned `no_target_test_failure`. Single qualified targets fixed it.
- **Ruff B905.** It flagged `zip()` without `strict=` in the new test. Fixed with `strict=True` before the RED
  commit.

## Remaining advisories (unchanged by 06-10)

- **IN-01 (open):** the deep-copy requirement for filter layouts is not documented, and copy errors are not
  wrapped.
- **IN-02 (open):** extra attributes come out in sorted order, which the migration note does not mention.
- **Human-only checks are still pending:**
  - hover tooltip
  - visual quality
  - screen-reader announcement
  - migration readability
- **Whole-repo `ruff format --check` still fails** on planning Markdown files (WINDOWS #4).
- **Unclassified edge assumptions:** FORM-01 and FORM-02 stay flagged.
- **Re-verification:** the phase's D-16 truth still needs independent re-verification. This summary is executor
  evidence only.

## Known Stubs

None.

## Next Phase Readiness

Ready for independent re-verification of the phase-06 D-16 truth (`/gsd-verify-work` or a phase re-verify).

## Self-Check: PASSED

- All 7 modified files exist, and the 4 code files contain the expected symbols:
  - `_cv_kind_icon`
  - `test_copied_filter_layout_keeps_kind_icons`
  - 7 `test_form_icon_normalization_*` functions
- Commits `ae83e62`, `f33d396`, `7f974ad`, `61103dd` and `3e6a450` are ancestors of HEAD.
