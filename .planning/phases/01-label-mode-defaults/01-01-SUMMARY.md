---
phase: 01-label-mode-defaults
plan: "01"
subsystem: ui
tags: [django, label-mode, settings, system-checks, override_settings, logging]

requires: []
provides:
  - "crud_views.lib.view.label_mode.LABEL_MODE_DEFAULTS: read-only MappingProxyType package floor {context: icon, list: icon, card: both}"
  - "crud_views.lib.view.label_mode.default_label_mode(location: str) -> str: public lazy floor accessor"
  - "crud_views.lib.view.label_mode._invalid_label_mode(source, location, value, fallback) -> str: private strict-raise / warn-once helper"
  - "cv_button_data: unstamped buttons use the configured floor; malformed truthy stamps recover in non-strict mode"
  - "crud_views.E108 system check (Error) for CRUD_VIEWS_LABEL_MODE_DEFAULTS"
  - "tests/test1/conftest.py::isolate_label_mode_warnings: function-scoped autouse warning-register isolation"
affects: [01-02 toolbar/list resolver, 01-03 card resolver, 01-04 docs, phase-06 form location, phase-07 API freeze]

actuals:
  tokens: 9464
  tasks: 2
  commits: 4
plan_head_before: e87a904b15be4801cb15e3fcbac844550b66b4cc
plan_head_after: e52d7d36be3e904c34627d6bd61090541d784061

tech-stack:
  added: []
  patterns:
    - "Lazy raw-setting read per call through _raw_label_mode_defaults() with a private _UNSET sentinel (no Pydantic field, no cache)"
    - "Strict raises before evaluating a lazy fallback callable; non-strict resolves the fallback outside the lock and logs after releasing it"
    - "Process-lifetime warn-once register keyed by (location, repr(value)), isolated per test by an autouse monkeypatch fixture"

key-files:
  created:
    - .planning/phases/01-label-mode-defaults/01-01-SUMMARY.md
  modified:
    - src/crud_views/lib/view/label_mode.py
    - src/crud_views/lib/view/button_data.py
    - src/crud_views/lib/settings.py
    - tests/test1/test_label_mode.py
    - tests/test1/test_button_data.py
    - tests/test1/test_button_leaves.py
    - tests/test1/test_action_label_mode_config.py
    - tests/test1/conftest.py
    - tests/test1/test_import_safety.py

key-decisions:
  - "Warn-once dedup is process-lifetime, keyed by (location, repr(value)), with no source dimension and no setting_changed reset (D-11 discretion choice); tests isolate it with an autouse fixture"
  - "No merged-map cache: default_label_mode reads django.conf.settings on every call, so override_settings needs no invalidation"
  - "Setting-recovery fallbacks return LABEL_MODE_DEFAULTS[location] directly; only the malformed-stamp path calls default_label_mode, so nested recovery terminates at the package floor"
  - "_invalid_label_mode takes a full source description (\"cv_label_mode must be one of [...]\"), so button_data.py still references LABEL_MODES and keeps that import"

patterns-established:
  - "Label-mode floor: every location reads default_label_mode(location); no literal \"icon\"/\"both\" floors in resolvers"
  - "E108 wording: 'setting CRUD_VIEWS_LABEL_MODE_DEFAULTS key <repr> must be one of <sorted>, got <repr>', no hint, insertion order"

requirements-completed: [LMOD-01, LMOD-02, LMOD-04, LMOD-05, LMOD-06]

coverage:
  - id: D1
    description: "CRUD_VIEWS_LABEL_MODE_DEFAULTS reaches the real action leaf through {% cv_button %}; absent configuration preserves output"
    requirement: LMOD-02
    verification:
      - kind: integration
        ref: "tests/test1/test_button_leaves.py#test_defaults_setting_reaches_button_leaf"
        status: pass
      - kind: integration
        ref: ".venv/bin/pytest tests/test1/test_action_menus_golden.py tests/test1/test_card_label_mode_render.py tests/test1/test_card_blocks.py tests/test1/test_card_order.py tests/test1/test_form_frame.py tests/test1/test_heading_level.py -q"
        status: pass
    human_judgment: false
  - id: D2
    description: "default_label_mode per-key merge, order independence, immutable package floor, call-time override_settings freshness"
    requirement: LMOD-01
    verification:
      - kind: unit
        ref: "tests/test1/test_label_mode.py#test_default_label_mode_merge"
        status: pass
      - kind: unit
        ref: "tests/test1/test_label_mode.py#test_default_label_mode_order_independent"
        status: pass
      - kind: unit
        ref: "tests/test1/test_label_mode.py#test_default_label_mode_override_settings"
        status: pass
      - kind: unit
        ref: "tests/test1/test_label_mode.py#test_defaults_match_locations"
        status: pass
    human_judgment: false
  - id: D3
    description: "Malformed setting and stamped modes: strict raises, non-strict warns once per (location, value) and falls back; no deadlock on re-entrant recovery"
    requirement: LMOD-05
    verification:
      - kind: unit
        ref: "tests/test1/test_label_mode.py#test_default_label_mode_invalid_setting"
        status: pass
      - kind: unit
        ref: "tests/test1/test_label_mode.py#test_default_label_mode_warns_once"
        status: pass
      - kind: unit
        ref: "tests/test1/test_label_mode.py#test_default_label_mode_exact_strings"
        status: pass
      - kind: unit
        ref: "tests/test1/test_button_data.py#test_invalid_stamped_mode_falls_back"
        status: pass
      - kind: unit
        ref: "tests/test1/test_button_data.py#test_same_bad_pair_warns_once_across_sources"
        status: pass
      - kind: integration
        ref: "tests/test1/test_button_data.py#test_invalid_stamp_and_floor_recovers_without_deadlock"
        status: pass
    human_judgment: false
  - id: D4
    description: "crud_views.E108 per-entry Error diagnostics, keys from button_data.LOCATIONS, lazy import boundary"
    requirement: LMOD-06
    verification:
      - kind: unit
        ref: "tests/test1/test_action_label_mode_config.py#test_e108_bad_entries"
        status: pass
      - kind: unit
        ref: "tests/test1/test_action_label_mode_config.py#test_e108_uses_button_locations"
        status: pass
      - kind: integration
        ref: "tests/test1/test_import_safety.py#test_settings_defers_button_data_until_checks"
        status: pass
    human_judgment: false
  - id: D5
    description: "EDGE-LMOD-04-unclassified: confirm no further intended lifecycle case beyond nested override_settings enter/exit and unchanged imported constants"
    requirement: LMOD-04
    verification:
      - kind: unit
        ref: "tests/test1/test_label_mode.py#test_default_label_mode_override_settings"
        status: pass
    human_judgment: true
    rationale: "The plan flags this spec-less edge as unresolved; a reviewer must confirm there is no further intended lifecycle case"

duration: 7min
completed: 2026-10-26
status: complete
---

# Phase 1 Plan 01: Label-mode defaults floor, recovery and E108 Summary

**`CRUD_VIEWS_LABEL_MODE_DEFAULTS` is now read lazily through `default_label_mode(location)` over a read-only `LABEL_MODE_DEFAULTS` floor. `cv_button_data` renders that floor for unstamped buttons. Malformed modes raise in strict mode; otherwise they warn once per `(location, repr(value))` and fall back. `crud_views.E108` reports each bad setting entry.**

## Performance

- **Duration:** 7 min
- **Started:** 2026-10-26T08:14:09Z
- **Completed:** 2026-10-26T08:21:19Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments
- A tracer test renders a raw context button through the real `{% cv_button "context" %}` tag. Under `{"context": "both"}` it shows the icon and the visible short label "Detail", with no title and no hidden-label span. With `{}` it still renders icon-only with a title, so output is unchanged when nothing is configured.
- New public exports `default_label_mode(location: str) -> str` and `LABEL_MODE_DEFAULTS: Mapping[str, str]`. The accessor merges the setting per key. Locations outside `LOCATIONS` raise `ValueError` in every mode. Unknown setting keys are ignored at render. Exact, case-sensitive strings are validated through `is_label_mode`.
- `cv_button_data` no longer crashes production renders on a malformed truthy `cv_label_mode`. Strict mode still raises and names `cv_label_mode`, even when the floor is also malformed. Falsey stamps keep the existing unset behavior. The `cv_no_label` and icon-less guards are unchanged.
- `crud_views.E108` (Error, no hint) gives one message for a non-dict value and one per bad dict entry, in insertion order. An unknown location is reported before an invalid mode. It reads the raw setting on every check and imports `button_data.LOCATIONS` only when the check runs.

## Task Commits

1. **Task 01-01-01: tracer + floor recovery** — RED `87ae025` (test), GREEN `935fce3` (feat)
2. **Task 01-01-02: lazy E108 system check** — RED `ff41f2b` (test), GREEN `e52d7d3` (feat)

No REFACTOR commits were needed.

## TDD Evidence

- **01-01-01 RED (`87ae025`):** the target `test_defaults_setting_reaches_button_leaf` failed on its planned assertion, `['Details'] == ['Detail']`, because the package `icon` floor rendered the full hidden label. `test_configured_leaf_floor` failed with `'icon' == 'both'` and similar, and the subprocess recovery test failed with exit 1. The warning-fixture tests errored in setup because `label_mode._warned` did not exist yet. `test_label_mode.py` failed at collection with an ImportError on `LABEL_MODE_DEFAULTS`. That collection failure is not valid RED, so the tracer and button_data assertion failures are the RED evidence. Semantic assessment: the target ran and failed for the intended reason, with the floor not configurable. Machine classification via `gsd-tools check tdd-red-evidence` was not run: the project uses pytest, a report format the classifier does not support, and `workflow.tdd_mode` is false.
- **01-01-02 RED (`ff41f2b`):** every E108 test failed on assertions, such as `assert 0 == 1` and `assert [] == [<expected message>]`. The subprocess boundary test failed on `check did not load button_data`. The before-setup assertions in that test already passed, showing that `crud_views.lib.settings` does not import the view package.
- **GREEN:** after each feat commit the full suite passed. The final run was `pytest tests -q -n auto`: 2983 passed, 1 skipped. It also passed with `--random-order-seed=1234`.

## Verification Results

| Command | Result |
|---|---|
| `.venv/bin/pytest tests/test1/test_button_leaves.py::test_defaults_setting_reaches_button_leaf tests/test1/test_label_mode.py tests/test1/test_button_data.py -q` | 211 passed (task 1 gate, before task 2 additions) |
| `.venv/bin/ruff check` (the five task-1 files) | All checks passed (no F401, no RUF001) |
| `.venv/bin/pytest tests/test1/test_action_label_mode_config.py tests/test1/test_settings_checks.py tests/test1/test_import_safety.py -q` | 108 passed |
| `.venv/bin/pytest tests/test1/test_label_mode.py tests/test1/test_button_data.py tests/test1/test_action_label_mode_config.py -q -n 2 --random-order --random-order-seed=4711` | 284 passed |
| Plan verification 1: label-mode / card / context / config tests | 318 passed |
| Plan verification 2: goldens, card render, card blocks/order, form frame, heading level | 89 passed (no golden mismatch, `CV_UPDATE_GOLDEN` not enabled) |
| `pytest tests -q -n auto` | 2983 passed, 1 skipped |
| `ruff check src tests` / `ruff format --check src tests` | clean |

Templates, goldens and the example project are untouched (D-26).

## Files Created/Modified
- `src/crud_views/lib/view/label_mode.py`: adds `LABEL_MODE_DEFAULTS`, `default_label_mode`, `_UNSET`, `_raw_label_mode_defaults`, `logger`, `_warned`, `_warned_lock`, `_invalid_label_mode`
- `src/crud_views/lib/view/button_data.py`: unstamped buttons get the floor from `default_label_mode`; malformed stamps go through `_invalid_label_mode` with a deferred floor fallback; the obsolete floor comment is replaced
- `src/crud_views/lib/settings.py`: E108 added in `_action_settings_messages` with deferred imports; the label-map comment now describes the configurable floor and whole-layer selection
- `tests/test1/test_label_mode.py`: floor, merge, order, override_settings, invalid location, whole-setting and per-location invalid matrices, warn-once, exact strings, isolation probe
- `tests/test1/test_button_data.py`: configured leaf floor, invalid / falsey stamps, strict precedence, cross-source dedup, bounded subprocess recovery
- `tests/test1/test_button_leaves.py`: `test_defaults_setting_reaches_button_leaf` tracer
- `tests/test1/test_action_label_mode_config.py`: E108 valid / non-dict / bad entries / order / same-instance / LOCATIONS tracking
- `tests/test1/conftest.py`: autouse `isolate_label_mode_warnings(monkeypatch)`
- `tests/test1/test_import_safety.py`: `test_settings_defers_button_data_until_checks`

## Decisions Made
- **Process-lifetime dedup (selected discretion choice):** the register is a module-level set guarded by a `threading.Lock` held only for check-and-add. The key is `(location, repr(value))`, so unhashable values work. There is no source dimension, so the same bad pair reached from a stamp and from the setting warns once. There is also no `setting_changed` reset, which keeps D-11's literal once-per-process guarantee. Test isolation comes from the autouse conftest fixture.
- **No cache:** the raw setting is read on every call. There is nothing to invalidate on `override_settings`.
- **Termination of nested recovery:** setting fallbacks return `LABEL_MODE_DEFAULTS[location]` directly. Only stamp recovery calls the accessor. Strict mode raises before the fallback runs.
- A non-dict setting warns once per distinct location queried, so at most 3 runtime warnings. E108 reports the whole setting once.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] The tool layer wrote Unicode escapes as literal confusables**
- **Found during:** Task 01-01-01 (RED test authoring)
- **Issue:** File writes turned `"bοth"` and similar into literal U+03BF characters. That breaks B1, which requires the escaped ASCII source form, and would trip RUF001.
- **Fix:** A scratchpad script converted every non-ASCII character (all of them inside string literals) back to `\uXXXX` escapes. A grep confirmed both test files are pure ASCII.
- **Files modified:** tests/test1/test_label_mode.py, tests/test1/test_button_data.py
- **Committed in:** 87ae025

**2. [Rule 1 - Lint] SIM117 nested `with` in the RED commit**
- **Found during:** Task 01-01-01
- **Issue:** The RED commit went in with four SIM117 findings because the ruff check and the commit were chained with `;`.
- **Fix:** The nested `override_settings` / `pytest.raises` blocks were combined. Ruff is clean from the GREEN commit on.
- **Committed in:** 935fce3

**3. [Plan conditional] `LABEL_MODES` import kept in button_data.py**
- A4 asked to remove the import only if no references remained. `_invalid_label_mode` takes the full source description, including the allowed modes, so `button_data.py` still uses `LABEL_MODES` for the stamp message. Ruff reports no F401.

**4. [Scope] Per-module `warned` fixtures removed in task 01-01-02**
- Task 01-01-01 isolated `_warned` with per-module fixtures, as the plan specified. Task 01-01-02 replaced them with the shared conftest autouse fixture and added `test_warning_register_is_isolated_per_test` to prove the isolation.

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 lint), plus 2 documented plan-conditional choices. **Impact:** no behavior or scope change.

## Issues Encountered
None.

## Flagged items carried to verification
- **EDGE-LMOD-04-unclassified (unresolved):** tests cover nested `override_settings` enter/exit and unchanged imported constants. A reviewer must confirm there is no further intended lifecycle case. This is not auto-dismissed.
- **Prohibition (flagged-unverified):** "Label-mode defaults MUST NOT become theme-owned policy or override explicit project/view/button choices." The implementation keeps explicit stamps ahead of the floor; `test_configured_leaf_floor` covers explicit stamps winning, including over an invalid floor. No theme hook was added. This remains a flagged-unverified spec-less recall, not a machine-certified pass.

## Threat Model Compliance
- T-01-01 (DoS, render crash): mitigated. Values are validated before use. Strict mode raises; non-strict returns known floors, including for unhashable values.
- T-01-02 (log flooding / deadlock): mitigated. The lock covers only check-and-add. A bounded subprocess test with a 10 s timeout covers equal and distinct bad stamp+floor pairs, using child `assertLogs` counts.
- T-01-03 (tampering): mitigated. `is_label_mode` rejects noncanonical strings. E108 reports raw entries by repr. Templates are unchanged and autoescaped.

## User Setup Required
None.

## Next Phase Readiness
- Plans 01-02 (toolbar/list resolver) and 01-03 (card resolver) can consume `default_label_mode` in parallel. Plan 01-02 owns full `check_viewsets` strict-mode recovery for the resolver.

## Self-Check: PASSED
- All 9 modified files exist, and the SUMMARY path is created by this write.
- Commits 87ae025, 935fce3, ff41f2b and e52d7d3 are ancestors of HEAD. The ledger count is 4 commits from e87a904 to e52d7d3.

---
*Phase: 01-label-mode-defaults*
*Completed: 2026-10-26*
