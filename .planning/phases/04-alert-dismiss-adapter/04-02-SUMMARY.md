---
phase: 04-alert-dismiss-adapter
plan: "02"
subsystem: ui
tags: [alerts, adapters, javascript, vitest, jsdom, regression]

requires:
  - phase: 04-alert-dismiss-adapter
    provides: "04-01 cv.adapters.alert.close default adapter, data-cv-alert-dismiss marker, delegated viewset.js listener, DISMISSIBLE_ALERT_HTML"
provides:
  - "Default alert adapter regression matrix: absent/falsey/alert-less namespaces, call-time namespace resolution, preassigned identity, present no-op/throwing component ownership, repeated closes (ALRT-03)"
  - "Delegated alert ownership regressions: nearest-frame dispatch for descendants, nested frames and post-load modal-like content; ignored targets; adapter swap; error, missing-key and repeated-click ownership (ALRT-02, ALRT-03)"
affects: [04-03 docs/migration/changelog and browser smoke]

actuals:
  tokens: 7468
  tasks: 2
  commits: 2
plan_head_before: e3dac1528531f61413638ff0d1e35205443a54f9
plan_head_after: 3990826cc9389524ae2f219e55ca7557eeb008e0

tech-stack:
  added: []
  patterns:
    - "Case-owned cv object per test (fresh window.cv before loading defaults), restoring only the cv/bootstrap descriptors so shared $/jQuery stubs survive"
    - "Fail-capability shown by temporary, uncommitted production mutants when regression tests characterize already-shipped behavior"

key-files:
  created: []
  modified:
    - tests/js/adapters.test.js
    - tests/js/viewset.test.js

key-decisions:
  - "No product change was needed: every 04-02 case passed against the 04-01 adapter and listener, and every production mutant tried was caught"
  - "Non-Element ignored target is exercised as a click dispatched on a text node inside a marked control, which separates the instanceof guard from the marker lookup"
  - "The detached-subtree edge is observed with a temporary document click listener (removed in finally) in addition to the adapter spy, so the propagation boundary is shown directly"

patterns-established:
  - "Alert adapter tests assert exact frame identity (mock.calls[n][0] toBe frame), isConnected of the frame and its siblings, and original error identity"

requirements-completed: [ALRT-02, ALRT-03]

coverage:
  - id: D1
    description: "Without an Alert component (missing global, null/undefined/{} or null-returning callback namespace, or a build without the alert component) the default adapter removes exactly the supplied frame and touches no other component"
    requirement: ALRT-03
    verification:
      - kind: unit
        ref: "tests/js/adapters.test.js#alert adapter ownership > removes exactly the supplied frame when no bootstrap global exists"
        status: pass
      - kind: unit
        ref: "tests/js/adapters.test.js#alert adapter ownership > removes exactly the supplied frame for %s as the namespace (5 cases)"
        status: pass
      - kind: unit
        ref: "tests/js/adapters.test.js#alert adapter ownership > removes the frame for a build without the alert component and touches no other component"
        status: pass
    human_judgment: false
  - id: D2
    description: "Object, changing-callback and late or replaced global namespaces resolve Alert at call time on the same adapter; a preassigned alert adapter keeps its identity and the other defaults are filled"
    requirement: ALRT-03
    verification:
      - kind: unit
        ref: "tests/js/adapters.test.js#alert adapter ownership > hands the frame to a present Alert component of an explicit object namespace"
        status: pass
      - kind: unit
        ref: "tests/js/adapters.test.js#alert adapter ownership > resolves a changing callback namespace on every call of the same adapter"
        status: pass
      - kind: unit
        ref: "tests/js/adapters.test.js#alert adapter ownership > uses a bootstrap global assigned or replaced after the defaults were built"
        status: pass
      - kind: unit
        ref: "tests/js/adapters.test.js#alert adapter ownership > keeps a preassigned alert adapter by identity and fills the other defaults"
        status: pass
    human_judgment: false
  - id: D3
    description: "A present Alert component owns close: a no-op keeps the frame; a throwing getOrCreateInstance or close surfaces the original error with no fallback removal and no console logging; repeated closes add no core teardown or de-duplication"
    requirement: ALRT-03
    verification:
      - kind: unit
        ref: "tests/js/adapters.test.js#alert adapter ownership > leaves the frame attached when a present component's close does nothing"
        status: pass
      - kind: unit
        ref: "tests/js/adapters.test.js#alert adapter ownership > surfaces the original error from a present component's %s and keeps the frame (lookup, close)"
        status: pass
      - kind: unit
        ref: "tests/js/adapters.test.js#alert adapter ownership > repeats the missing-component fallback harmlessly on the same detached element"
        status: pass
      - kind: unit
        ref: "tests/js/adapters.test.js#alert adapter ownership > hands every repeated close of an attached frame to a present no-op component"
        status: pass
    human_judgment: false
  - id: D4
    description: "Delegated dispatch reaches the nearest role=alert frame for control descendants, two controls in one frame, nested frames (outer and siblings kept) and alerts inserted into modal-like content after load, with custom classes and no initialization"
    requirement: ALRT-02
    verification:
      - kind: unit
        ref: "tests/js/viewset.test.js#delegated alert ownership > routes a click on a control descendant to the nearest frame, without Bootstrap classes"
        status: pass
      - kind: unit
        ref: "tests/js/viewset.test.js#delegated alert ownership > closes an alert inserted into modal-like content after the scripts loaded"
        status: pass
      - kind: unit
        ref: "tests/js/viewset.test.js#delegated alert ownership > removes an inserted modal alert through the fallback and keeps the modal"
        status: pass
      - kind: unit
        ref: "tests/js/viewset.test.js#delegated alert ownership > dispatches each of two controls in one frame exactly once with that frame"
        status: pass
      - kind: unit
        ref: "tests/js/viewset.test.js#delegated alert ownership > closes only the nearest of nested frames and keeps the outer frame and siblings"
        status: pass
    human_judgment: false
  - id: D5
    description: "Unmarked alert-body, outside, orphan marked and text-node targets make no adapter call, emit no error, change no DOM and leave defaultPrevented=false"
    requirement: ALRT-02
    verification:
      - kind: unit
        ref: "tests/js/viewset.test.js#delegated alert ownership > ignores %s: no adapter call, no error, no DOM change (4 cases)"
        status: pass
      - kind: unit
        ref: "tests/js/viewset.test.js#delegated alert ownership > leaves a cancelable click on an orphan marked control un-prevented"
        status: pass
    human_judgment: false
  - id: D6
    description: "Theme ownership through the listener: an adapter swapped after load drives the next click; custom and component throws surface the original error and keep prior mutations, with no logging or forced removal; a missing alert key surfaces TypeError with no repair; rapid attached clicks call once each; a detached subtree's click never reaches document delegation"
    requirement: ALRT-03
    verification:
      - kind: unit
        ref: "tests/js/viewset.test.js#delegated alert ownership > uses the alert adapter assigned after load for the next click, success or no-op"
        status: pass
      - kind: unit
        ref: "tests/js/viewset.test.js#delegated alert ownership > surfaces a custom adapter's error after its own mutation, with no logging or forced removal"
        status: pass
      - kind: unit
        ref: "tests/js/viewset.test.js#delegated alert ownership > surfaces a present component's error through the default adapter and keeps the frame"
        status: pass
      - kind: unit
        ref: "tests/js/viewset.test.js#delegated alert ownership > surfaces a TypeError when the alert adapter key is missing and adds no repair"
        status: pass
      - kind: unit
        ref: "tests/js/viewset.test.js#delegated alert ownership > calls the current adapter once per rapid click while the frame stays attached"
        status: pass
      - kind: unit
        ref: "tests/js/viewset.test.js#delegated alert ownership > does not reach document delegation from a frame the fallback already detached"
        status: pass
    human_judgment: false

duration: 5min
completed: 2026-10-26
status: complete
---

# Phase 4 Plan 02: Alert adapter ownership regressions Summary

**32 new jsdom regressions pin the alert dismissal contract. The default adapter removes the frame only when no `Alert` component exists, and resolves the namespace on every call. A present component, or a theme's own adapter, owns removal, no-ops and errors. The delegated listener reaches only the nearest `role="alert"` frame for marked controls, including content inserted after load. No product change was needed.**

## Performance

- **Duration:** about 5 min
- **Started:** 2026-10-26T20:22:51Z
- **Completed:** 2026-10-26T20:27:30Z
- **Tasks:** 2
- **Files modified:** 2 (test files only)

## Accomplishments

- `fakeNamespace()` now carries an `Alert` component with a no-op instance `close` spy, and the factory enumeration test covers `alert`. `namespaceWithoutAlert()` builds a fresh fake with `Alert` deleted, named as "a build without the alert component".
- The "alert adapter ownership" group in `adapters.test.js` has 16 cases. They use the real `bootstrapAdapters` and real `loadScript("adapters")` defaults inside a case-owned `window.cv`.
- The "delegated alert ownership" group in `viewset.test.js` has 16 cases against the real listener registered once in `beforeAll`. It sits before the keep-it-last reload test, whose comment now explains that a second listener would break the once-per-click alert counts.
- Both edge-probe truths are explicit tests:
  - **EDGE-ALRT-03-idempotency:** the repeated absent-component close on a retained detached element, and the repeated present no-op close.
  - **EDGE-ALRT-03-concurrency:** two rapid attached clicks call the adapter once each, and a click in a subtree the fallback already detached never reaches `document`.

## Regression Matrix

| Case | Where | Observation |
|------|-------|-------------|
| No `bootstrap` global | adapters | frame removed; other frame and sibling attached |
| `null` / `undefined` / `{}` / callback returning `null` or `undefined` | adapters | exactly the supplied frame removed |
| Build without the alert component | adapters | frame removed; Modal/Tooltip/Collapse untouched |
| Explicit object namespace | adapters | `getOrCreateInstance(frame)` once, `close` once, frame attached |
| Changing callback namespace | adapters | null -> fallback; ns1 -> ns1; ns2 -> ns2 only; no-Alert -> fallback, all on one adapter |
| Late / replaced global | adapters | adapter built first; the assigned then replaced global is used; identity of `cv.adapters.alert` unchanged |
| Preassigned alert | adapters | same object kept; modal/tooltip/collapse filled; component not consulted |
| Present no-op close | adapters | frame and siblings attached |
| Throwing lookup / throwing close | adapters | thrown value `toBe` the original error; frame attached; no console.error/warn |
| Repeated absent close (detached ref) | adapters | no throw; DOM unchanged after the first removal |
| Repeated present no-op close | adapters | two lookups with the same frame; two closes; frame attached |
| Descendant `<i>` in marked `<a>` with custom classes | listener | one call with the exact `<section role="alert">`, `defaultPrevented` true |
| Alert inserted into modal-like content (component / fallback) | listener | component called with the inserted frame / frame removed, modal kept |
| Unmarked body, outside element, orphan control, text-node target | listener | `listenerErrors` empty, zero calls, body HTML identical, `defaultPrevented` false, no console calls |
| Orphan cancelable click | listener | `cancelable` true, `defaultPrevented` false |
| Two controls in one frame | listener | each click makes exactly one call with that frame |
| Nested frames | listener | inner detached; outer, its text, inner's sibling and page attached |
| Adapter swapped after load (remover, then no-op) | listener | next click uses the current adapter; replaced default never consulted |
| Custom adapter throws after mutating | listener | `errors[0]` toBe the original; class and data mutation kept; frame attached; no logging |
| Present component throws via default adapter | listener | original error surfaced; frame attached; no logging |
| `cv.adapters.alert` deleted (case-owned map) | listener | one `TypeError`; frame attached; key still absent; no logging |
| Two rapid attached clicks | listener | two lookups and two closes with the same frame |
| Detached subtree re-click | listener | `document` listener and adapter each still at 1 call; no error |

## Task Commits

1. **04-02-01: Default adapter absence, namespace and component ownership.** `c5327b9` (test)
2. **04-02-02: Dynamic semantic dispatch and custom adapter error ownership.** `3990826` (test)

**Plan metadata:** recorded in the final docs commit.

## TDD / Fail-Capability Evidence

Both tasks are `tdd="true"`, but they characterize behavior 04-01 already shipped and that this plan did not change, so every new case passed on its first run. That is the expected outcome for this expansion plan, not a broken RED. It matches the 04-01-03 precedent. Fail-capability was shown with temporary production mutants. Each was reverted with `git checkout --` and checked byte-identical against a scratch copy, and none was committed.

**`adapters.js`, against `tests/js/adapters.test.js`:**

| Mutant | Failing cases |
|--------|---------------|
| M1: namespace resolved once at factory time | 2 (changing callback, late global) |
| M2: catch, log and remove around the component | 2 (both throwing cases) |
| M3: always remove after the component close | 5 |
| M4: defaults overwrite preassigned adapters | 2 (existing modal case and the new alert identity case) |
| M5: present component ignored | 7 |

**`viewset.js`, against `tests/js/viewset.test.js`:**

| Mutant | Failing cases |
|--------|---------------|
| V1: adapter cached on first click | 7 |
| V2: `preventDefault` before frame matching | 2 (orphan cases) |
| V3: catch, log and remove | 3 |
| V4: missing-key repair | 1 |
| V5: outermost instead of nearest frame | 1 (nested) |
| V6: non-Element target promoted to its parent | 1 (text node) |
| V7: unmarked click accepted | 1 (unmarked body) |

The first V1 attempt cached the adapter at script load. It crashed `beforeAll` and skipped the whole suite, so it was not a valid mutant. It was replaced by the first-click cache shown above.

Because no RED run was produced, the `tdd-red-evidence` classifier was not applicable. `workflow.tdd_mode` is false for this project.

## Verification Results

- `npm --prefix . test -- tests/js/adapters.test.js tests/js/viewset.test.js`: 2 files, 59 passed (27 before this plan).
- `npm --prefix . test`: 8 files, 183 passed, with no unhandled errors.
- Python alert/message command: not re-run, because no product file changed. The 04-01 golden and Python regressions are untouched.
- Fake components do not prove Bootstrap's real transition behavior. That evidence belongs to the 04-03 browser smoke.

## Files Created/Modified

- `tests/js/adapters.test.js`: Alert in `fakeNamespace`, the `namespaceWithoutAlert`, `alertFixture` and `thrownBy` helpers, the `alert` key in the enumeration test, and the "alert adapter ownership" group with its case-owned `withCaseCv` helper.
- `tests/js/viewset.test.js`: the "delegated alert ownership" group with the `withCaseAdapters` and `withConsoleSpies` helpers, plus the extended keep-it-last comment.

## Decisions Made

- No product correction: no case exposed a defect in `adapters.js` or `viewset.js`.
- The non-Element target is a click dispatched on a text node inside a marked control. That isolates the `instanceof Element` guard from the marker lookup; mutant V6 proves the case discriminates.
- The detached-subtree case uses a temporary `document` listener as well as the adapter spy, so the propagation boundary itself is observed. The listener is removed in `finally`.

## Deviations from Plan

None. The plan was executed as written.

## Issues Encountered

None.

## User Setup Required

None. No external service configuration is required.

## Next Phase Readiness

- Ready for 04-03: docs (javascript.md, messages.md, theme.md), the CHANGELOG Breaking entry, the migration guide with R04-01 whole-map replacement guidance, and the example browser smoke.
- Missing-key `TypeError` is intentional D-03/D-04 behavior and is now pinned. The migration guidance for whole-map replacement is assigned to 04-03.

## Self-Check: PASSED

- Both modified files exist, and they hold the "alert adapter ownership" and "delegated alert ownership" groups, `Alert` and `data-cv-alert-dismiss`.
- Task commits c5327b9 and 3990826 are ancestors of HEAD on `introduce-gsd`.
- Measured commits since `plan_head_before`: 2.
- No stubs, TODOs or placeholders were added.

---
*Phase: 04-alert-dismiss-adapter*
*Completed: 2026-10-26*
