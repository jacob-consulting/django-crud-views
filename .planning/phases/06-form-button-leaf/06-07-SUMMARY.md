---
phase: 06-form-button-leaf
plan: "07"
subsystem: testing
tags: [vitest, jsdom, submitevent, formdata, nox, crispy-forms, crispy-bootstrap5, django-6, tracer]

requires:
  - phase: 06-form-button-leaf
    provides: "06-js-verify.sh / 06-JS-RUNTIME.json locked JS gate (06-01); form-button leaf bodies (06-02); filter helper leaf Reset/Apply (06-05); missing-icon policy and checks (06-06)"
provides:
  - "Native SubmitEvent.submitter + FormData(form, submitter) regression suite for modal and non-modal form submission across label/icon/both bodies"
  - "Nested-click cancel and filter-reset regressions on the real rendered button shapes (type=reset inside #filter-form)"
  - "crispy_floor nox session: Python 3.12 x Django 4.2/6.0 at django-crispy-forms==2.0 / crispy-bootstrap5==2023.10, version assertion and format_html argument audit"
  - "test_filter_form_controls_match_golden: byte-exact leaf/field/hidden control comparison of the filter region, independent of pack wrapper whitespace"
  - "Green full JS gate (223/223): pre-existing jsdom 30.1.2 selector failure resolved test-only"
affects: [06-08, 06-09]

actuals:
  tokens: 6982
  tasks: 3
  commits: 3
plan_head_before: 4caa3dc4e5b452eed6ab265a49c5017d99198bd6
plan_head_after: 242f3d74bfb45d59f61e986630666ac60aabb1a0

tech-stack:
  added: []
  patterns:
    - "Prove an already-correct handler with discriminating tests: mutate the source, confirm the new tests fail, restore by edit and verify the sha256 is unchanged"
    - "Count navigations by temporarily replacing nav.href with an accessor that records every write"
    - "Floor sessions pin the floor packages in the same install call as the project extras and assert the resolved versions before running tests"

key-files:
  created: []
  modified:
    - tests/js/modal.test.js
    - tests/js/viewset.test.js
    - tests/js/list.filter.test.js
    - noxfile.py
    - tests/test1/test_form_buttons_golden.py
    - .planning/phases/06-form-button-leaf/deferred-items.md
    - .planning/WINDOWS.md

key-decisions:
  - "modal.js, viewset.js and list.filter.js stay byte-identical: every new regression passed on the existing handlers, and mutation runs (dropped submitter; direct-target-only cancel; stopPropagation; preventDefault on reset; dropped dir; double wiring) each failed 6-18 tests"
  - "The filter region golden is byte-exact over crispy-bootstrap5's own label / FormActions wrapper whitespace, which differs at 2023.10; crispy_floor deselects only that test and relies on a new control-level byte comparison that runs in every environment"
  - "crispy_floor is a separate nox session; CI selects sessions by explicit name, so the supported tests/examples matrix and the declared floors in pyproject.toml are unchanged"
  - "list.filter.test.js:159 now uses the equivalent :scope selector; no lockfile, manifest or product JS change"

patterns-established:
  - "Native browser contract tests assert that FormData/SubmitEvent are the jsdom window's own constructors (no polyfill), spying only on fetch"

requirements-completed: [FORM-05, FORM-06, FORM-07, FORM-08]

coverage:
  - id: D1
    description: "Clicking a modal form's submit button, its icon or its (hidden or visible) label posts only that submitter's name/value with CSRF and hidden confirm kept; sibling submitters and the type=button cancel are absent, in all three body modes"
    requirement: FORM-07
    verification:
      - kind: unit
        ref: "tests/js/modal.test.js#native submitters (form-button leaf) > a %s-body click on the button, icon or text posts only that submitter"
        status: pass
      - kind: unit
        ref: "tests/js/modal.test.js#native submitters (form-button leaf) > posts the sibling submitter instead when that one is clicked"
        status: pass
      - kind: unit
        ref: "tests/js/modal.test.js#native submitters (form-button leaf) > runs on the browser's own SubmitEvent and FormData"
        status: pass
    human_judgment: false
  - id: D2
    description: "No-submitter fallback, hostile/Unicode value decoded literally, and non-modal native submission with the same submitter payload"
    requirement: FORM-07
    verification:
      - kind: unit
        ref: "tests/js/modal.test.js#native submitters (form-button leaf) > keeps the no-button fallback when the form is submitted without a submitter"
        status: pass
      - kind: unit
        ref: "tests/js/modal.test.js#native submitters (form-button leaf) > transmits a hostile / Unicode button value as its decoded literal text"
        status: pass
      - kind: unit
        ref: "tests/js/modal.test.js#native submitters (form-button leaf) > leaves a form outside the modal to native submission with the same submitter payload"
        status: pass
    human_judgment: false
  - id: D3
    description: "Nested clicks on a cancel button in label/icon/both bodies navigate exactly once, prevented but still propagating, never submitting; encoded cancel URLs decode literally"
    requirement: FORM-06
    verification:
      - kind: unit
        ref: "tests/js/viewset.test.js#data-cv-cancel-url > a %s-body form cancel button > a click on %s navigates once, prevented but still propagating"
        status: pass
      - kind: unit
        ref: "tests/js/viewset.test.js#data-cv-cancel-url > navigates to the decoded attribute value of an encoded, non-ASCII cancel url"
        status: pass
    human_judgment: false
  - id: D4
    description: "Filter reset (type=reset, id filter-button-reset, inside #filter-form) resets fields natively and navigates once, keeping sort/order/dir for empty, encoded and non-ASCII values, with or without filter fields"
    requirement: FORM-08
    verification:
      - kind: unit
        ref: "tests/js/list.filter.test.js#a %s-body filter reset > a click on %s resets the fields natively and navigates once"
        status: pass
      - kind: unit
        ref: "tests/js/list.filter.test.js#reset keeps the ordering parameters: %s"
        status: pass
      - kind: unit
        ref: "tests/js/list.filter.test.js#the label-mode toggle stays safe next to the reset (an empty icon loop)"
        status: pass
    human_judgment: false
  - id: D5
    description: "Form-button leaf feature suite passes at django-crispy-forms 2.0 / crispy-bootstrap5 2023.10 on Python 3.12 with Django 4.2 and 6.0, versions asserted, format_html always called with arguments"
    requirement: FORM-05
    verification:
      - kind: integration
        ref: ".venv/bin/nox -s crispy_floor"
        status: pass
      - kind: unit
        ref: "tests/test1/test_form_buttons_golden.py#test_filter_form_controls_match_golden"
        status: pass
    human_judgment: false

duration: 14min
completed: 2026-10-28
status: complete
---

# Phase 06 Plan 07: Native Submitter, Cancel/Reset and Crispy Floor Validation Summary

**Native SubmitEvent/FormData submitter regressions on locked jsdom 30.1.2, nested cancel and filter-reset coverage in all three button body modes, and a crispy_floor nox session proving the form-button suite at crispy 2.0 / crispy-bootstrap5 2023.10 on Django 4.2 and 6.0.**

## Performance

- **Duration:** about 14 min
- **Started:** 2026-10-28T07:51:00Z
- **Completed:** 2026-10-28T08:05:00Z
- **Tasks:** 3
- **Files modified:** 7

## Accomplishments

- Modal tracer proven on the locked runtime: node v24.21.0 / npm 11.19.0, jquery 3.7.1, jsdom 30.1.2, vitest 5.0.3, lock sha256 567bff55...5d2e, 71 installed packages matching the lock. With real button clicks (on the button, its icon or its label), `SubmitEvent.submitter` is the clicked button and `FormData(form, submitter)` carries only that button's name/value, with CSRF and the hidden confirm kept.
- Cancel and filter-reset handlers covered on the actual rendered shapes, including native `type=reset` field reset and retained `sort`/`order`/`dir` encoding.
- Full JS gate green for the first time in Phase 06: 223/223 passed (was 182/183). The fix for list.filter.test.js:159 is test-only.
- `crispy_floor` runs 1870 tests in each environment and passes: Django 4.2.30 (about 13s of pytest) and Django 6.0.9 (about 21s), both with django-crispy-forms 2.0 and crispy-bootstrap5 2023.10. The single `format_html` call in src passes an argument. Focused JS feedback takes about 2.5s; the full Python suite (4429 tests) takes about 54s.

## Task Commits

1. **Task 1: Validate native modal submitters on the locked browser test environment** - `e009205` (test)
2. **Task 2: Verify nested cancel clicks and filter reset behavior** - `2bfefb1` (test)
3. **Task 3: Run expanded feature tests at the declared crispy floors** - `242f3d7` (chore)

## Files Created/Modified

- `tests/js/modal.test.js` - native submitter/FormData suite (label/icon/both bodies, sibling submitters, no submitter, hostile values, non-modal native path)
- `tests/js/viewset.test.js` - nested-click cancel suite with navigation-write counting, propagation and reset-typed cancel
- `tests/js/list.filter.test.js` - real `#filter-form` reset fixture, encoded/empty/non-ASCII retained ordering, and the `:scope` selector fix
- `noxfile.py` - `crispy_floor` session (pins, version assertion, format_html audit, feature test list)
- `tests/test1/test_form_buttons_golden.py` - `test_filter_form_controls_match_golden`
- `.planning/phases/06-form-button-leaf/deferred-items.md`, `.planning/WINDOWS.md` - jsdom selector item resolved (WINDOWS entry 5 fixed)

## Decisions Made

- None of the JS handlers changed. Every new test passed on the existing handlers, and mutation runs showed the tests catch regressions. Dropping the submitter in modal.js failed 6 tests. Cancel mutations (direct-target-only, stopPropagation) failed 8 and 9. Reset mutations (preventDefault, dropped `dir`, double wiring) failed 9, 14 and 18. All mutations were restored by editing, and the original sha256 was confirmed.
- crispy_floor deselects exactly one test (`test_filter_form_baseline`). Its byte golden covers crispy-bootstrap5's own field-label and FormActions wrapper whitespace, which differs at 2023.10. Those differences are in pack-owned markup: the leaf `<button>`s and hidden inputs are byte-identical. A new control-level byte comparison covers them in every environment.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Filter region golden is bound to the locked crispy-bootstrap5 wrapper whitespace**
- **Found during:** Task 3 (first crispy_floor run: 1 failed, 1869 passed in both environments)
- **Issue:** `test_filter_form_baseline` compares the raw filter region byte for byte. At crispy-bootstrap5 2023.10, the pack renders `<label for=...>` on one line and the FormActions wrapper as `<div class="mb-3">`, not `class="mb-3  "` split over lines. This is pack-owned markup, not a leaf regression.
- **Fix:** Added `test_filter_form_controls_match_golden`, which compares the raw field, Apply/Reset and hidden controls of the live region byte for byte against the golden, using the module's existing `_extract_controls` convention with no normalization. crispy_floor deselects only the region golden. The golden file and the region test are unchanged and still run in the normal sessions.
- **Files modified:** tests/test1/test_form_buttons_golden.py, noxfile.py
- **Verification:** crispy_floor passes in both environments, and the new test passes on the dev venv (crispy 2.7 / bootstrap5 2026.9) and at the floor.
- **Committed in:** 242f3d7

**2. [Assigned by orchestrator] Pre-existing jsdom 30.1.2 failure at list.filter.test.js:159**
- **Fix:** Changed the assertion to the equivalent `:scope > span:not([data-cv-filter-icon])` (test-only). Recorded in deferred-items.md and marked fixed in WINDOWS.md (entry 5).
- **Committed in:** 2bfefb1

---

**Total deviations:** 2 (1 blocking auto-fix, 1 assigned pre-existing fix)
**Impact on plan:** Neither weakens evidence. The leaf-owned markup is still byte-checked at the floor. No product source, manifest or lockfile changed.

## Issues Encountered

- The existing "delegated handlers" modal tests print 4 "Not implemented: navigation to another Document" lines from jsdom. This is pre-existing noise; the new tests add none.
- On the first floor attempt, overriding the label mode needed `CRUD_VIEWS_LABEL_MODE_DEFAULTS={"form": mode}`, not the form map setting. This only affected the throwaway markup-capture probe (deleted, never committed).

## TDD Gate Compliance

The tasks are tdd="true" verification tasks on behavior that already existed. The plan requires the JS sources to stay byte-identical when the regressions pass. So there is no RED/GREEN pair: each task is a single `test(...)` commit. Mutation runs of the targeted source (listed above) stand in for RED evidence that the tests discriminate.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- The JS gate is green, so later Phase 06 plans can sample `06-js-verify.sh` without a known failure.
- Still open: transitive dev-only `undici` audit advisories (WINDOWS entry 6), deferred to a separate dependency-update change.

## Self-Check: PASSED

- FOUND: tests/js/modal.test.js, tests/js/viewset.test.js, tests/js/list.filter.test.js, noxfile.py, tests/test1/test_form_buttons_golden.py
- FOUND: e009205, 2bfefb1, 242f3d7 (ancestors of HEAD)
- src/, pyproject.toml, package.json, package-lock.json, uv.lock unchanged since 4caa3dc

---
*Phase: 06-form-button-leaf*
*Completed: 2026-10-28*
