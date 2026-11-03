---
phase: 04-alert-dismiss-adapter
plan: "01"
subsystem: ui
tags: [alerts, adapters, javascript, templates, golden, vitest, pytest]

requires:
  - phase: 03-filter-toggle-label-mode
    provides: stable branch state; no direct code dependency
provides:
  - Committed raw-byte golden of the stock dismissible alert, captured before the hook change (ALRT-01)
  - Stock alert frame close control marked with data-cv-alert-dismiss (ALRT-02)
  - cv.bootstrapAdapters(ns).alert.close(el) default adapter with component-local el.remove() fallback (ALRT-03)
  - Delegated document click listener in viewset.js routing the marker's nearest role="alert" frame to globalThis.cv.adapters.alert.close
  - Rendered-golden-to-handler-to-adapter JS tracer and Python frame/escaping/translation regressions
affects: [04-02 adapter regression matrix, 04-03 docs/migration/changelog and browser smoke]

actuals:
  tokens: 3879
  tasks: 3
  commits: 4
plan_head_before: 1b77934c5f528c3e63c08d2121906a6fbf8ed105
plan_head_after: 3d63404a824734d361402ac2e18bc6a753284f5e

tech-stack:
  added: []
  patterns:
    - "Raw-byte golden (encode('utf-8') vs read_bytes(), no normalization, no appended newline) for byte-exact frame evidence"
    - "Shared golden fixture: Python proves the bytes, jsdom consumes the same file for interaction tests"
    - "Per-case fresh real defaults in JS tests: snapshot/clear/restore only window.cv and window.bootstrap descriptors"

key-files:
  created:
    - tests/test1/golden/alerts/dismissible.html
  modified:
    - src/crud_views/templates/crud_views/tags/alert.html
    - src/crud_views/static/crud_views/js/adapters.js
    - src/crud_views/static/crud_views/js/viewset.js
    - tests/test1/test_alerts.py
    - tests/test1/test_messages.py
    - tests/js/viewset.test.js

key-decisions:
  - "Golden render uses heading 'Saved:' and text 'The record was saved.' with dismissible=True under translation.override('en'); bytes include the template's leading/trailing newlines exactly as rendered"
  - "Delegated listener ignores a marker without an enclosing role=alert frame (no preventDefault), and calls globalThis.cv.adapters.alert.close at click time with no catch, log or fallback (D-03/D-04/D-08)"
  - "Task 3 regressions use lxml (already a test dependency) for parsed assertions; translation is checked by patching django.utils.translation._trans.gettext via monkeypatch.context()"

patterns-established:
  - "Alert dismissal hook: data-cv-alert-dismiss on the control + role=alert on the frame; themes customize behavior via cv.adapters.alert.close"

requirements-completed: [ALRT-01, ALRT-02, ALRT-03]

coverage:
  - id: D1
    description: "Baseline-only commit f6982bfef24f4322cfd01f9f21c3bbed517462fe records today's dismissible alert before any product edit; later golden diff is only the attribute"
    requirement: ALRT-01
    verification:
      - kind: unit
        ref: "tests/test1/test_alerts.py#test_dismissible_alert_golden"
        status: pass
      - kind: other
        ref: "git show --name-only f6982bf (only test_alerts.py + golden); git diff f6982bf HEAD -- tests/test1/golden/alerts/dismissible.html (one line: data-bs-dismiss=\"alert\" -> data-cv-alert-dismiss)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Rendered stock dismissible alert closes through the delegated listener and default adapter: present Alert -> getOrCreateInstance(frame).close() once, frame left attached; absent Alert -> frame removed, sibling kept"
    requirement: ALRT-03
    verification:
      - kind: unit
        ref: "tests/js/viewset.test.js#rendered alert dismissal tracer > delegates to a present Alert component with the nearest frame"
        status: pass
      - kind: unit
        ref: "tests/js/viewset.test.js#rendered alert dismissal tracer > removes the frame when no Alert component is loaded"
        status: pass
    human_judgment: false
  - id: D3
    description: "Explicit alerts and real create-response flash messages render the new hook with unchanged role, classes, escaping, translated close label and non-dismissible output"
    requirement: ALRT-02
    verification:
      - kind: unit
        ref: "tests/test1/test_alerts.py#test_dismissible_alert_preserves_frame_contract"
        status: pass
      - kind: unit
        ref: "tests/test1/test_alerts.py#test_dismissible_alert_close_label_is_translated"
        status: pass
      - kind: unit
        ref: "tests/test1/test_alerts.py#test_dismissible_alert_escapes_heading_text_and_extra_tags"
        status: pass
      - kind: unit
        ref: "tests/test1/test_alerts.py#test_cv_alert_is_not_dismissible_by_default"
        status: pass
      - kind: integration
        ref: "tests/test1/test_messages.py#test_create_message_renders_as_an_alert"
        status: pass
    human_judgment: false
  - id: D4
    description: "Real example-project flash messages close in a browser (Bootstrap, missing Alert, dynamically inserted)"
    requirement: ALRT-02
    verification: []
    human_judgment: true
    rationale: "Browser smoke is owned by plan 04-03 (04-ACCEPTANCE.md); jsdom and server render tests cannot establish real Bootstrap transition behavior"

duration: 5min
completed: 2026-10-26
status: complete
---

# Phase 4 Plan 01: Alert dismiss adapter tracer Summary

**Stock alert close control now carries `data-cv-alert-dismiss`. A delegated `viewset.js` click listener hands the nearest `role="alert"` frame to `cv.adapters.alert.close`. That calls Bootstrap `Alert` when it is loaded and otherwise removes the frame. All of this is proven against a raw-byte golden committed before the change.**

## Performance

- **Duration:** about 5 min
- **Started:** 2026-10-26T20:15:25Z
- **Completed:** 2026-10-26T20:20:30Z
- **Tasks:** 3
- **Files modified:** 7 (1 created, 6 modified)

## Accomplishments

- ALRT-01 evidence in history. The baseline-only commit is `f6982bfef24f4322cfd01f9f21c3bbed517462fe`; it holds only `tests/test1/test_alerts.py` and the new golden. The golden's later diff is exactly `data-bs-dismiss="alert"` -> `data-cv-alert-dismiss`.
- Default `alert.close(el)` adapter in `cv.bootstrapAdapters(ns)`. It resolves `component(ns, "Alert")` on every call. The lazy global callback and the shallow `Object.assign` preservation merge are unchanged, and the header comment now says "all four".
- Delegated document click listener: Element guard, `closest("[data-cv-alert-dismiss]")`, then the nearest `[role="alert"]`, `preventDefault`, and `globalThis.cv.adapters.alert.close(frame)` at call time. It has no catch, logging, fallback or init step.
- Golden-to-jsdom tracer, plus Python regressions for the frame contract, the translated close label, escaping, non-dismissible output and the real create response.

## Task Commits

1. **04-01-01: Baseline golden.** `f6982bf` (test). Full SHA: `f6982bfef24f4322cfd01f9f21c3bbed517462fe`.
2. **04-01-02: Tracer.** RED `ca2069c` (test, only `tests/js/viewset.test.js`), GREEN `910625b` (feat; template, adapters.js, viewset.js, golden, test_messages.py).
3. **04-01-03: Frame/message regressions.** `3d63404` (test).

## TDD / Tracer Evidence

- **RED (04-01-02):** `NO_COLOR=1 npx vitest run tests/js/viewset.test.js --reporter=tap-flat` exited 1; 9 tests, 7 passed, 2 failed.
  - Both target tests failed: "rendered alert dismissal tracer > delegates to a present Alert component with the nearest frame" and "... > removes the frame when no Alert component is loaded".
  - Both failed on the planned marker-presence assertion (`expected null not to be null`), because the committed legacy golden has no `[data-cv-alert-dismiss]`.
  - `gsd-tools check tdd-red-evidence` returned `RED_EVIDENCE_OK` (reason `target_test_failed`) for each target.
  - **Semantic assessment:** both targets ran and failed on the planned behavior assertion. There was no load, setup or collection fault and no unrelated failure. Valid RED.
- **GREEN (04-01-02):**
  - Focused Python: `.venv/bin/pytest tests/test1/test_alerts.py tests/test1/test_messages.py -q` gave 51 passed.
  - Focused JS: `npm --prefix . test -- tests/js/adapters.test.js tests/js/viewset.test.js` gave 27 passed, both tracer cases `ok`.
  - Full JS gave 151 passed. Full Python (`pytest tests -q -n auto`) gave 3489 passed, 1 skipped.
- **Tracer feedback gate:** interactive run, `human_verify_mode=end-of-phase`, automated-only verify. Verify was re-run and passed, so the plan continued to 04-01-03 without a checkpoint.
- **04-01-03 (regression task, `tdd="true"`):** these tests characterize behavior that 04-01-02 already shipped, so they passed on first run. That is expected for regression tests, not a broken RED. The fail-capability was shown with temporary mutations that were not committed:
  - With the baseline `alert.html` restored via `git show f6982bf`: 5 failures (golden, frame contract, escaping-with-hook, both message tests).
  - With `{% translate 'Close' %}` replaced by a literal `Close`: the translation-sentinel test fails.
  - The template was restored with `git checkout --` and verified clean.

## Files Created/Modified

- `tests/test1/golden/alerts/dismissible.html`: exact rendered bytes of the stock dismissible success alert.
- `tests/test1/test_alerts.py`: `test_dismissible_alert_golden` (docstring covers the byte convention and `CV_UPDATE_GOLDEN`), `test_dismissible_alert_preserves_frame_contract`, `test_dismissible_alert_close_label_is_translated`, `test_dismissible_alert_escapes_heading_text_and_extra_tags`, plus extended non-dismissible assertions.
- `tests/test1/test_messages.py`: both dismiss assertions moved to the new hook. The legacy attribute is asserted absent. The real create/redirect response gets parsed frame and control checks.
- `tests/js/viewset.test.js`: `DISMISSIBLE_ALERT_HTML`, read from `../test1/golden/alerts/dismissible.html`, and the "rendered alert dismissal tracer" group, placed before the final reload test.
- `src/crud_views/templates/crud_views/tags/alert.html`: dismiss attribute replaced. Nothing else changed.
- `src/crud_views/static/crud_views/js/adapters.js`: `alert.close` added to the factory.
- `src/crud_views/static/crud_views/js/viewset.js`: delegated alert-dismiss click listener.

## Decisions Made

- Golden content is a success alert with heading `Saved:` and text `The record was saved.`, rendered under `translation.override("en")`.
- An orphan marker (no enclosing `role="alert"`) is ignored without `preventDefault`. 04-02 expands the invalid-target cases.
- lxml is used for parsed assertions; it is an existing test dependency. bs4 is not installed.

## Deviations from Plan

None. The plan was executed as written.

## Issues Encountered

- `ruff format --check` at repo level reports 8 pre-existing files that would be reformatted. All are `.planning/` Markdown documents (codebase/research/phase docs) that this plan did not touch, so they are out of scope here. The 04-03 final gates should record this. `ruff check` passes, and every file this plan changed is formatted.
- Installed ruff is 0.16.10 while pre-commit pins v0.17.1. Recorded only; no manifest change.

## User Setup Required

None. No external service configuration is required.

## Next Phase Readiness

- Ready for 04-02, the adapter regression matrix: no-op/throwing components, namespaces, dynamic insertion, orphan and nested targets.
- 04-03 still owns the docs (javascript.md, messages.md, theme.md), the CHANGELOG Breaking entry, the migration guide and the browser smoke.
- Carried classifier assumptions A04-01 and A04-02 (ALRT-01 and ALRT-02 unclassified by the edge probe) remain flagged for verification.

## Self-Check: PASSED

- All 7 key files exist on disk.
- All 4 task commits (f6982bf, ca2069c, 910625b, 3d63404) are ancestors of HEAD on `introduce-gsd`.
- Artifact contents were confirmed: the test symbols, `DISMISSIBLE_ALERT_HTML`, `adapters.alert.close` and `Alert`.
- No stubs, TODOs or placeholders in the changed product files.

---
*Phase: 04-alert-dismiss-adapter*
*Completed: 2026-10-26*
