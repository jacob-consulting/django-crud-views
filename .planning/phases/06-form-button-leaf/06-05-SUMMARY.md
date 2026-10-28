---
phase: 06-form-button-leaf
plan: "05"
subsystem: ui
tags: [django-crispy-forms, crispy-bootstrap5, django-filter, form-buttons, filter-helper]

requires:
  - phase: 06-form-button-leaf
    provides: "06-02 form-button leaf and Submit/Button/Reset adapters; 06-03 owner recovery with the private _cv_helper_owner entry; 06-04 filter / filter-reset kind icons; 06-01 filter-form baseline 98b71ed and its region extractor"
provides:
  - "ListViewFilterFormHelper.get_form_actions() -> FormActions | None (default Apply/Reset leaf buttons)"
  - "Per-instance, always-truthy private layout copy; prepared in get_attributes() before crispy's dispatch guard"
  - "Exactly-once action group keyed on the prepared layout identity; no-layout helpers render the actual form fields first"
  - "Private helper-owner context entry pushed for the duration of render_layout"
  - "filter.html golden updated to leaf-button markup with the unchanged 06-01 extractor"
affects: [06-06 diagnostics (W292 filter-helper reach), 06-07 JS/floor gates, 06-08 docs and migration notes]

actuals:
  tokens: 9780
  tasks: 2
  commits: 5
plan_head_before: b19de0206121eb0c08daee2cd1feb2fa7a9074f0
plan_head_after: 6471ffc1e87256e289783def99ca409c7d845151

tech-stack:
  added: []
  patterns:
    - "Helper-local truthiness: ListViewFilterFormHelper.__bool__ True plus a private Layout subclass (or a cached truthy subclass of a custom layout class), so crispy's `if helper and helper.layout` dispatches without global overrides"
    - "Replacement detection by identity in get_attributes(), which crispy's get_response_dict calls before the guard"

key-files:
  created:
    - .planning/phases/06-form-button-leaf/06-05-RED-task1.json
  modified:
    - src/crud_views/lib/views/list.py
    - tests/test1/test_filter.py
    - tests/test1/test_crispy_buttons.py
    - tests/test1/test_form_buttons_golden.py
    - tests/test1/golden/form_buttons/filter.html

key-decisions:
  - "Filter helper calls FormHelper.__init__() without the form and sets helper.form afterwards; crispy's own initializer would replace a declared layout with every form field"
  - "A caller-selected layout is deep-copied and its class swapped for an always-truthy variant (_PreparedLayout for Layout, a cached subclass for custom layout classes), so custom render behavior and nested nodes survive"
  - "No-layout helpers rebuild the prepared fields from the actual render form on every render_layout; an explicit Layout() never resurrects constructor or inferred fields"
  - "Exactly-once actions are keyed on the prepared layout's identity, not a helper-lifetime flag; a replacement triggers one fresh get_form_actions() call"
  - "Hidden sort/order/dir stay add_input(Hidden) in the pack's trailing inputs wrapper after the visible FormActions group (L-HIDDEN-WRAPPER)"

patterns-established:
  - "Filter actions hook: override get_form_actions() to replace (any FormActions), keep an empty group (FormActions()) or omit (None)"

requirements-completed: [FORM-05, FORM-06, FORM-08, FORM-10]

coverage:
  - id: D1
    description: "The real filter endpoint renders Apply/Reset as layout leaf <button>s with the original type/name/value/id/classes, then the unchanged hidden sort/order/dir wrapper"
    requirement: FORM-08
    verification:
      - kind: integration
        ref: "tests/test1/test_filter.py#test_filter_endpoint_renders_apply_and_reset_as_leaf_buttons"
        status: pass
      - kind: integration
        ref: "tests/test1/test_filter.py#test_filter_endpoint_fields_then_actions_then_hidden_wrapper"
        status: pass
      - kind: integration
        ref: "tests/test1/test_filter.py#test_filter_hidden_controls_unchanged"
        status: pass
      - kind: integration
        ref: "tests/test1/test_form_buttons_golden.py#test_filter_form_baseline"
        status: pass
      - kind: integration
        ref: "tests/test1/test_form_buttons_golden.py#test_filter_form_defaults"
        status: pass
    human_judgment: false
  - id: D2
    description: "Filter actions follow the list view's form map in label/both/icon modes with the filter and filter-reset icons; the helper's view owns them through the pushed private owner entry"
    requirement: FORM-05
    verification:
      - kind: integration
        ref: "tests/test1/test_filter.py#test_filter_actions_honor_the_list_view_form_modes"
        status: pass
      - kind: unit
        ref: "tests/test1/test_crispy_buttons.py#test_filter_helper_pushes_its_owner_for_its_render_only"
        status: pass
    human_judgment: false
  - id: D3
    description: "Declared, explicit-form, no-layout and replaced layouts are isolated per instance with exactly one action group across repeated and interleaved renders; class and caller layouts are never mutated; helper.form identity is kept"
    requirement: FORM-08
    verification:
      - kind: unit
        ref: "tests/test1/test_crispy_buttons.py#test_filter_class_layout_is_cloned_per_instance_and_actions_appear_once"
        status: pass
      - kind: unit
        ref: "tests/test1/test_crispy_buttons.py#test_filter_explicit_form_never_overwrites_the_declared_layout"
        status: pass
      - kind: unit
        ref: "tests/test1/test_crispy_buttons.py#test_filter_helper_without_layout_renders_the_actual_form_fields"
        status: pass
      - kind: unit
        ref: "tests/test1/test_crispy_buttons.py#test_filter_layout_replacement_is_respected_with_one_action_group"
        status: pass
      - kind: unit
        ref: "tests/test1/test_crispy_buttons.py#test_filter_custom_layout_class_keeps_its_behavior_while_isolated"
        status: pass
      - kind: integration
        ref: "tests/test1/test_filter.py#test_filter_endpoint_repeated_requests_never_accumulate_actions"
        status: pass
    human_judgment: false
  - id: D4
    description: "An empty Layout() replacement (before the first render or between renders) still dispatches through the real {% crispy %} tag for default, None and empty FormActions hooks; None omits, empty keeps an explicit empty group, equal labels are not deduplicated"
    requirement: FORM-06
    verification:
      - kind: unit
        ref: "tests/test1/test_crispy_buttons.py#test_filter_empty_layout_replacement_dispatches_through_the_tag"
        status: pass
      - kind: unit
        ref: "tests/test1/test_crispy_buttons.py#test_filter_action_hook_none_empty_and_equal_labels"
        status: pass
    human_judgment: false
  - id: D5
    description: "Legacy add_input controls stay quiet pack inputs; custom two-argument constructors still work; private lifecycle state is not published; renamed order/dir params keep their hidden-input logic"
    requirement: FORM-10
    verification:
      - kind: unit
        ref: "tests/test1/test_crispy_buttons.py#test_filter_legacy_add_input_controls_stay_quiet_inputs"
        status: pass
      - kind: integration
        ref: "tests/test1/test_filter.py#test_custom_helper_constructor_without_form_keyword"
        status: pass
      - kind: unit
        ref: "tests/test1/test_crispy_buttons.py#test_filter_helper_private_state_is_not_published"
        status: pass
      - kind: unit
        ref: "tests/test1/test_filter.py#test_filter_hidden_controls_follow_renamed_order_params"
        status: pass
    human_judgment: false

duration: 15min
completed: 2026-10-28
status: complete
---

# Phase 06 Plan 05: Filter helper actions through the form-button leaf Summary

**`ListViewFilterFormHelper` now renders the stock Apply/Reset filter actions as one layout `FormActions` group of form-leaf `<button>`s. They keep their ids `filter-button` / `filter-button-reset` and follow the list view's form modes and icons. A new `get_form_actions()` hook can replace the group, keep it empty, or omit it (`None`). Each helper instance renders a private, always-truthy deep copy of its declared or caller-assigned layout. That copy is prepared in `get_attributes()`, before crispy's `if helper and helper.layout` guard, so field-only subclasses, `form=` construction, `Layout()` replacements and legacy `add_input()` controls all keep working without crispy template overrides.**

## Performance

- **Duration:** 15 min
- **Started:** 2026-10-28T07:09:26Z
- **Completed:** 2026-10-28T07:24:36Z
- **Tasks:** 2
- **Files modified:** 5 (plus the RED evidence record)

## Accomplishments

- **Hook.** `get_form_actions()` returns `FormActions(Submit("submit", _("Apply Filter"), css_id="filter-button", slot="form:filter-submit"), Reset("reset", _("Reset Filter"), css_id="filter-button-reset"))` by default. Returning None omits the group. An empty `FormActions()` stays an explicit empty group. The group is resolved and appended once per prepared layout.
- **Construction.** `__init__(view, request, form=None)` is unchanged for callers, and `ListViewTableFilterMixin.get_filterset` is untouched. `FormHelper.__init__()` is now called without the form, then `helper.form = form`, so `form=` no longer replaces a declared layout with every field. The visible actions left `helper.inputs`. The hidden sort/order/dir controls stay `add_input(Hidden(...))` with the same naming and value logic.
- **Dispatch.** `__bool__` returns True, and the prepared layout is `_PreparedLayout`, a private `Layout` whose `__bool__` is True. A custom layout class gets a cached truthy subclass. `len(helper)` is still the real field count, for example 0 for an empty replacement before actions. `get_attributes()` prepares the layout first. It detects a caller replacement by identity and deep-copies it, and is idempotent across calls.
- **No-layout helpers.** They rebuild the prepared fields from the actual render form on each render, then add the action group. Zero, one and many fields all work, and a second form through the same helper renders its own fields.
- **Owner.** `render_layout` pushes `{_cv_helper_owner: helper.view}` for its own render and pops it afterwards. All lifecycle state is `_cv_`-prefixed, so crispy publishes nothing new.
- **Golden.** `filter.html` now holds the leaf markup: fields, then one `div.mb-3 > div[class=""]` group of two buttons, then the pack's unchanged hidden-input wrapper.

## Task Commits

1. **Task 1 (tracer): Render stock filter actions through FormActions with unchanged GET controls.** RED `db8f33a` (test), GREEN `d43a206` (feat). Tracer gate (interactive, end-of-phase, automated-only verify): after GREEN I re-ran the Task 1 verify (266 passed), then moved on to Task 2.
2. **Task 2: Preserve custom layouts, replacement actions and quiet legacy inputs.** Regressions `66c5e9c` (test), REFACTOR `2271e0d` (refactor), custom-layout coverage `6471ffc` (test).

**Plan metadata:** the docs commit that adds this SUMMARY.

## Files Created/Modified

- `src/crud_views/lib/views/list.py`: `_PreparedLayout`, `_prepared_layout_class`, and in `ListViewFilterFormHelper` the `get_form_actions`, `__bool__`, `_cv_prepare_layout`, `get_attributes` and `render_layout` members plus the form-less crispy init.
- `tests/test1/test_filter.py`: endpoint tests for buttons, order, hidden wrapper and values, modes/icons, no-layout helper, two-argument constructor, repeated requests, and renamed order params.
- `tests/test1/test_crispy_buttons.py`: `test_filter_buttons` now looks for `<button>`. New real-`{% crispy form helper %}` lifecycle tests: isolation, explicit form, no-layout, replacement, empty replacement with spies, hooks, legacy inputs, private state, owner push, and custom layout class.
- `tests/test1/test_form_buttons_golden.py`: docstring and `test_filter_form_defaults` cover the new group and wrapper structure. The extractor is unchanged.
- `tests/test1/golden/form_buttons/filter.html`: the leaf-button region.
- `.planning/phases/06-form-button-leaf/06-05-RED-task1.json`: Task 1 RED evidence (`RED_EVIDENCE_OK`).

## Golden evidence (D-17 / L-FILTER-GOLDEN-SCOPE)

- **Extractor equality.** The AST source segments of `_extract_filter_form_region`, `_filter_region`, `_FORM_TAG`, `_FILTER_FORM_ID`, `FILTER_PATH` and `FILTER_HIDDEN` in HEAD are byte-identical to `git show 98b71ed:tests/test1/test_form_buttons_golden.py`. Both hash to sha256 `8e555e40…74676`. The capture scope, raw-byte handling and `GET /publisher/?sort=name&order=name&dir=desc` fixture are all unchanged.
- **Same-region diff against 98b71ed.** Only the two action `<input>`s changed: they became a `FormActions` `div` with two `<button>`s and their `<span>` labels, placed after the field row and before the inputs wrapper. The field markup and the hidden `sort`/`order`/`dir` inputs and values are byte-identical. The wrapper opening is the same `<div class="mb-3"> <div class="">`, which now holds only the hidden inputs.
- Hidden names and values are asserted separately from the new order. The wrapper classes, its position after the group, and the absence of visible actions inside it are pinned by `test_filter_form_defaults` and `test_filter_endpoint_fields_then_actions_then_hidden_wrapper`.

## TDD Gate Compliance

- **Task 1.** RED `db8f33a` came before GREEN `d43a206`. The RED run (pre-plan `list.py`, `--junitxml`) had 13 failures, all target assertions about the missing leaf buttons and the changed golden, and 253 other tests passed. The classifier returned `RED_EVIDENCE_OK` (`target_test_failed`) for `test_filter_endpoint_renders_apply_and_reset_as_leaf_buttons`. Semantic check: no collection, import or fixture faults.
- **Task 2 has no GREEN commit. This is a deviation.** As the plan requires, Task 1's action included the whole lifecycle (M-EMPTY-REPLACEMENT in `get_attributes`, identity-keyed exactly-once state, `form=` handling). So Task 2's regressions passed on their first run against `d43a206`. Instead of a pre-implementation RED, I proved them with in-place mutations, each restored by writing the saved file back (never `git checkout`/`restore`). Each mutation was confirmed to fail:
  - removing the `get_attributes` preparation fails 6 `test_filter_empty_layout_replacement_dispatches_through_the_tag` cases
  - removing `__bool__` fails 10 (empty replacement and no-layout tests)
  - removing the deepcopy fails 22 (isolation, replacement, endpoint and golden)
  - replacing the identity check with a lifetime flag fails the replacement and empty-replacement tests
  - passing the form to crispy's init fails `test_filter_explicit_form_never_overwrites_the_declared_layout`
  - removing the owner push fails `test_filter_helper_pushes_its_owner_for_its_render_only`
  - taking default fields from a constant instead of the render form fails the no-layout parametrized tests
- One mutation survived: removing the action-state resets in `_cv_prepare_layout`. It was equivalent, because the identity key already forces a fresh resolution, so `2271e0d` removed those lines as a refactor.

## Decisions Made

- I swap the class of the deep copy (`_PreparedLayout`, or a cached `_Prepared<Name>` subclass) instead of wrapping it in a new `Layout`. This keeps a custom layout's `render` and attributes, keeps `len(helper)` equal to the selected field count, and leaves the user's class with crispy's len-based truthiness.
- No-layout helpers are tracked with `_cv_default_fields`, separately from an explicit `Layout()`. Only `layout is None` takes the default-fields path; an empty replacement never brings back discarded fields.
- The pushed owner is `getattr(self, "view", None)`, so a subclass that skips setting `view` still renders, falling back to the page tier.

## Deviations from Plan

### Process deviations

**1. Task 2 committed as regressions plus a refactor, with no GREEN commit.** See TDD Gate Compliance. Task 1's action owned the whole implementation, so Task 2 had no new product behavior to implement. The mutation evidence replaces a pre-implementation RED.

**2. Extra REFACTOR and coverage commits (`2271e0d`, `6471ffc`).** The refactor removes the equivalent-mutant resets. The coverage commit pins the "preserve selected nested/custom layout nodes" clause for a custom `Layout` subclass, which had no test.

---

**Total deviations:** 0 auto-fixed (Rules 1–3); 2 process deviations, both documented above.
**Impact on plan:** None on product scope. All required behavior and verification are in place.

## Issues Encountered

- Filter persistence redirects a bare `/publisher/` to the stored query string after a filtered request in the same session. The repeated-request test therefore uses only explicit query strings.
- In the explicit empty-`Layout()` plus `None`-hook case, crispy's `display_form.html` falls back to `uni_form.html` because `form_html` is empty, so all form fields render. As specified, this pack-owned fallback is kept. The test asserts the selected layout stays empty and no action group appears, not that fields are absent.

## Known Stubs

None.

## User Setup Required

None. No external service configuration required.

## Next Phase Readiness

- 06-06 can treat filter helpers that inherit the default `get_form_actions` as statically reachable for W292.
- 06-08 must document three things: `helper.inputs = []` no longer suppresses the stock actions (the migration is `get_form_actions()` returning None, L-SUPPRESSION-MIGRATION); the hidden wrapper now comes after the actions (L-HIDDEN-WRAPPER); and the `display_form.html` fallback. `docs/getting_started/tutorial-5-filters-permissions.md` still says the helper has "no submit button of its own — the list view renders one". That sentence is now inaccurate and should be corrected there.
- Full suite: 4154 passed. `ruff check src tests` is clean. The pre-existing JS failure (`tests/js/list.filter.test.js:159`, jsdom 30.1.2) is still owned by 06-07. The real filter reset button is still `#filter-button-reset`, so `list.filter.js` needs no change.

## Self-Check: PASSED

- All modified files exist. Commits `db8f33a`, `d43a206`, `66c5e9c`, `2271e0d` and `6471ffc` are ancestors of HEAD. Measured `git rev-list --count b19de02..HEAD` = 5, and `check evaluation-scope --plan 06-05 --commits-only` resolves them.
- Plan verify: `.venv/bin/pytest tests/test1/test_filter.py tests/test1/test_crispy_buttons.py tests/test1/test_form_buttons_golden.py -q` gave 288 passed. Task 2 verify (`test_filter.py` and `test_crispy_buttons.py`) passed. The extractor matches `98b71ed`.

---
*Phase: 06-form-button-leaf*
*Completed: 2026-10-28*
