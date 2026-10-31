---
phase: 06.3-delete-protection-and-write-boundary-integrity-issue-282
reviewed: 2026-10-31T08:45:40Z
depth: deep
diff_base: b6e7b89
revision_at_final_read: cabab7837c7e039cf6950f74ce2bfcffe20b42a0
files_reviewed: 9
files_reviewed_list:
  - src/crud_views/static/crud_views/js/modal.js
  - src/crud_views/static/crud_views/js/adapters.js
  - tests/js/modal.test.js
  - tests/js/adapters.test.js
  - tests/browser/modal-focus.cjs
  - docs/reference/javascript.md
  - docs/reference/modals.md
  - docs/migrating-1.0.md
  - CHANGELOG.md
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Focus repair: targeted code review

## Narrative Findings (AI reviewer)

No unresolved BLOCKER or WARNING remains in the source snapshot listed below. Counts describe the final snapshot, including fixes made by the parent during this review. This is a targeted code review, not phase acceptance, a new backend verification, or a disposition of the retained human decisions.

Reviewed the changes since `b6e7b89`, including uncommitted tracked edits, against `06.3-FOCUS-DESIGN.md` and `06.3-19-PLAN.md`. Read repository guidance and the unchanged fixture server; traced controller, adapter, published native-dialog recipe, test setup, browser assertions, evidence checker, and child-process cleanup. No structural pre-pass or external reviewer evidence was supplied. No reviewed file is ignored. The reviewer modified only this report.

## Findings corrected during review

### CR-01 — BLOCKER, resolved: old dismissal consumed a replacement session

**Files:** `/home/alex/projects/alex/django-crud-views/src/crud_views/static/crud_views/js/adapters.js:15-67`; `/home/alex/projects/alex/django-crud-views/src/crud_views/static/crud_views/js/modal.js:129-143`; `/home/alex/projects/alex/django-crud-views/docs/reference/javascript.md:159`.

**Issue and reproduction:** Show session A, start hiding it, and immediately open B with a fast response. In actual Chromium with Bootstrap 5.3.3, the initial implementation injected B, called `show()` during the hide transition, and consumed A's subsequent `hidden` event as B's dismissal. Observed `{visible:false, active:'two', sessionActive:false}` with no second show event. With the actual published native-dialog adapter, a queued `close` event from A instead left B visibly open with no active controller session: `{open:true, sessionActive:false}`. Calling an old callback directly in a unit test did not exercise either event-delivery race.

**Fix reviewed:** The Bootstrap adapter now tracks public hide/hidden events per shell, postpones show until the pending hide completes, skips that old hide for the replacement subscription, and cancels an abandoned pending show. Prevented dismissal is reconciled after event dispatch. The native recipe ignores a queued close while `modalEl.open` is true. Tests cover these transitions.

**Independent recheck:** Actual Chromium now shows B, retains its session, then hides B and restores its exact opener. Bootstrap events were `show, shown, hide, hidden, show, shown`, followed by B's own `hide, hidden`. Native recheck returned `{before:{open:true,sessionActive:true}, after:{open:false,sessionActive:false,active:'two'}}`.

### CR-02 — BLOCKER, resolved: replacing a visible shell lost keyboard focus

**File:** `/home/alex/projects/alex/django-crud-views/src/crud_views/static/crud_views/js/modal.js:105-143`.

**Issue and reproduction:** While A is fully shown, activate an in-modal link to B. Initial injection did not request recovery, and Bootstrap's second show call did not refocus an already shown modal. Actual Chromium left BODY active while the dialog remained visible. This was a retained focus defect, not a newly introduced baseline regression. The first correction still failed when an intermediate B GET remained pending and C replaced it: B's `shown:false` forgot that the shared shell remained visible.

**Fix reviewed:** Preserve `replacingVisible` separately across pending replacements, verify current shell usability before injection, and use the existing recovery path for destroyed dialog focus. Initial hidden opening still leaves focus to the adapter. Regression tests include an unresolved intermediate GET.

**Independent recheck:** Actual Chromium returned `{single:{active:'field'}, overlap:{active:'INPUT',id:'latest',visible:true,sessionActive:true}}` for simple replacement and A → pending B → C, respectively.

### WR-01 — WARNING, resolved: focus tests depended on another suite's setup

**File:** `/home/alex/projects/alex/django-crud-views/tests/js/modal.test.js:24`; related probe isolation at lines 414-429.

**Issue and reproduction:** Running `bash .planning/phases/06-form-button-leaf/06-js-verify.sh tests/js/modal.test.js -t 'modal focus lifecycle'` initially failed all 21 selected tests because `window.cv` was undefined. The suite relied on a sibling describe's `beforeAll`. Full-file execution additionally left a second controller's delegated listeners from the jQuery-independence probe installed before the new focus suite.

**Fix reviewed:** Load the controller in a shared top-level setup; remove the probe's listeners and restore the original namespace after that probe.

**Independent recheck:** The same targeted command passed all 21 then-existing focus tests, with 31 skipped. Subsequent visible-replacement cases were separately reviewed and independently reproduced in Chromium; the parent's final full-suite run covers their current unit assertions.

### WR-02 — WARNING, resolved: browser cleanup failure bypassed child cleanup

**File:** `/home/alex/projects/alex/django-crud-views/tests/browser/modal-focus.cjs:288-307`.

**Issue:** The previous sequential finally block awaited `browser.close()` before stopping the fixture child or writing evidence. A rejection bypassed both actions.

**Fix reviewed:** Nested finally blocks now attempt child termination and evidence writing regardless of browser-close failure; that failure marks the run failed and exits nonzero. Termination remains scoped to the runner's own ChildProcess. No unrelated process-kill command was added. This correction was checked by control-flow inspection, not a live process-failure injection.

## Evidence and limits

The browser reproductions above used the installed Chromium and actual Bootstrap/native dialog lifecycles with deterministic fetch responses to isolate races. They are reviewer diagnostics, not substitutes for the plan's genuine HTTP fixture evidence. The parent owns the final all-case browser, visual capture, and evidence-refresh runs.

The final evidence checker requires the exact unique case IDs, per-case named assertions, required HTTP statuses, repeated-dismissal counts, no page errors, current input hashes, and screenshot existence/hashes. Input binding now includes the unit tests, migration/changelog, exercised deletion/view code, fixture server, and relevant templates. The repeated-open case also performs a rapid reopen and subsequent genuine 422. Earlier loose assertion-count/source-binding concerns were addressed in the reviewed runner and are not outstanding findings. The final source-bound browser packet must be regenerated after these edits; this report does not declare old captures current.

No unchanged backend suite was rerun or requested by this reviewer. No source/test files were edited by this reviewer, and no commit was made.

## Reviewed working-tree hashes

| File | SHA-256 |
|---|---|
| `src/crud_views/static/crud_views/js/modal.js` | `d83524a2ec90670d9df82aac7cd0b69c0af37fc4093176dcbfdd79944c7cf9cb` |
| `src/crud_views/static/crud_views/js/adapters.js` | `6134473b5f0fb183aae7f4b035ad38a56a902b8f58c8b5c688c9638d1cef2580` |
| `tests/js/modal.test.js` | `c35c243ba1b667e24191c0cd057e6d54518562717e48cc28e7955ca36357d40f` |
| `tests/js/adapters.test.js` | `d62b08bb9fd113b5cbdf83b1a9922b864b4d702e3011cc515a8f32116c68121c` |
| `tests/browser/modal-focus.cjs` | `d03f5870180fba3e7b2d3879ccf774b848892547d84de45de92ca73c158cdd13` |
| `docs/reference/javascript.md` | `a898961e7176fd76db7fa4c32979ea4a1be6dbfdd076030262377aff1eea6a56` |
| `docs/reference/modals.md` | `1db9b5176a5b5e8e9067f5ba42b0900f079577764e03a5ea655117b9c47af573` |
| `docs/migrating-1.0.md` | `1e39865fb95377a77403a99473e2fd96f91c7f85ee10388afdd2f7de90cb2b76` |
| `CHANGELOG.md` | `ceae060f1272f3c7994fcf7afdf68a9ea63f7b63b1de41a3379aba0916daa2d1` |

_Reviewer: gsd-code-reviewer; targeted focus repair only._
