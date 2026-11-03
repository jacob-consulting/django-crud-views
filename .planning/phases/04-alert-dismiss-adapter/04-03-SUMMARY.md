---
phase: 04-alert-dismiss-adapter
plan: "03"
subsystem: docs
tags: [alerts, adapters, javascript, theme, migration, changelog, acceptance, browser]

requires:
  - phase: 04-alert-dismiss-adapter
    provides: "04-01 data-cv-alert-dismiss marker, cv.adapters.alert default adapter, delegated viewset.js listener, raw-byte golden; 04-02 adapter ownership regressions"
provides:
  - "Canonical alert adapter contract in javascript.md: alert.close(el) row, Dismissible alerts section, four-adapter factory, viewset.js use-time need, pre-load default filling vs post-load whole-map replacement"
  - "messages.md and settings.md describe the new hook, the core-script requirement and the delegated data-cv-alert-dismiss hook"
  - "Tested '### Custom alert frame' recipe in theme.md, executed by test_documented_alert_frame_override"
  - "Core-only data-bs-* allowlist guard plus a lasting tmp_path rejection regression"
  - "Paired CHANGELOG Breaking entry and migrating-1.0.md before/after, with the four-adapter Added enumeration"
  - "04-ACCEPTANCE.md: gate outcomes, tool drift, golden chronology, historical probe and three-message browser evidence"
affects: [phase verification for 04, downstream themes copying tags/alert.html, Phase 7 surface assessment]

actuals:
  tokens: 8860
  tasks: 3
  commits: 3
plan_head_before: 5864cf04a689575b81d9074f08c48eeef2809071
plan_head_after: e31221c65fb68547d91f7dc1cdff571d19b19b30

tech-stack:
  added: []
  patterns:
    - "Executable documentation recipe: fence-aware _section extraction of exactly one django/html fence, rendered as a locmem theme override"
    - "Allowlist guard as a helper over a supplied root, so a tmp_path negative test and a one-time historical probe exercise the same code"

key-files:
  created:
    - .planning/phases/04-alert-dismiss-adapter/04-ACCEPTANCE.md
  modified:
    - docs/reference/javascript.md
    - docs/reference/messages.md
    - docs/reference/theme.md
    - docs/reference/settings.md
    - tests/test1/test_alerts.py
    - CHANGELOG.md
    - docs/migrating-1.0.md
    - .planning/phases/04-alert-dismiss-adapter/04-VALIDATION.md

key-decisions:
  - "Whole-map guidance: a partial cv.adapters assigned before adapters.js needs nothing; a post-load whole-map replacement must provide alert.close(el) or the click throws TypeError; fix with per-entry assignment, Object.assign or cv.bootstrapAdapters(ns).alert"
  - "Browser messages A/B/C were generated through the Author update form with unchanged values, so the gitignored local example DB gains no rows"
  - "The in-list before/after fence in migrating-1.0.md is indented four spaces and followed by a blank line; two-space indentation closed the list in Python-Markdown"

patterns-established:
  - "Docs recipes that users copy get an executable render test keyed on the full heading string"

requirements-completed: [ALRT-01, ALRT-02, ALRT-03, ALRT-04]

coverage:
  - id: D1
    description: "theme.md '### Custom alert frame' recipe renders as a real override: custom classes, level colour from the class table, extra_tags, translated accessible type=button control with only data-cv-alert-dismiss, no control when not dismissible, escaped hostile content; missing/duplicate heading or fence fails"
    requirement: ALRT-04
    verification:
      - kind: unit
        ref: "tests/test1/test_alerts.py#test_documented_alert_frame_override"
        status: pass
      - kind: other
        ref: "8 temporary theme.md mutants (marker, translate, colour seam, condition, role, duplicate fence, renamed and duplicated heading) all failed the test; 04-ACCEPTANCE.md §5"
        status: pass
    human_judgment: false
  - id: D2
    description: "Core templates keep data-bs-* only in the theme.md dropdown allowlist; the guard rejects a forbidden path in a tmp tree and rejected the baseline alert.html in a one-time historical probe"
    requirement: ALRT-04
    verification:
      - kind: unit
        ref: "tests/test1/test_alerts.py#test_stock_bootstrap_data_attributes_are_dropdown_only"
        status: pass
      - kind: unit
        ref: "tests/test1/test_alerts.py#test_core_bootstrap_data_attribute_guard_rejects_forbidden_path"
        status: pass
      - kind: other
        ref: "historical probe against f6982bfef24f4322cfd01f9f21c3bbed517462fe:alert.html rejected crud_views/tags/alert.html; 04-ACCEPTANCE.md §4"
        status: pass
    human_judgment: false
  - id: D3
    description: "javascript.md, messages.md, theme.md, settings.md, CHANGELOG and migrating-1.0.md describe the hook, scripts, four adapters, legacy Bootstrap-only path and load-order distinction consistently"
    requirement: ALRT-04
    verification:
      - kind: other
        ref: ".venv/bin/mkdocs build --strict (anchors validated)"
        status: pass
    human_judgment: true
    rationale: "Semantic accuracy of upgrade prose is beyond a build; executor review passed (04-ACCEPTANCE.md §7), maintainer review pending at end of phase"
  - id: D4
    description: "Real example flash messages close in a browser: Bootstrap transition (A), missing-Alert fallback (B), post-load clone with restored Bootstrap (C)"
    requirement: ALRT-02
    verification:
      - kind: e2e
        ref: "headless Chrome 156 + playwright-core 1.60.0 scratch script against examples/bootstrap5; 04-ACCEPTANCE.md §6"
        status: pass
    human_judgment: true
    rationale: "Automated headless run, not a person observing the fade; end-of-phase human verification may repeat the procedure"
  - id: D5
    description: "Golden chronology: baseline-only commit precedes the hook change and the later golden diff is only the attribute"
    requirement: ALRT-01
    verification:
      - kind: other
        ref: "git show --name-only f6982bf; git diff f6982bf HEAD -- tests/test1/golden/alerts/dismissible.html; 04-ACCEPTANCE.md §3"
        status: pass
    human_judgment: false
  - id: D6
    description: "Final project gates on the combined phase"
    requirement: ALRT-03
    verification:
      - kind: unit
        ref: ".venv/bin/pytest tests -n auto (3495 passed, 1 skipped)"
        status: pass
      - kind: unit
        ref: "npm --prefix . test (183 passed)"
        status: pass
      - kind: other
        ref: "ruff check, manage.py check, test_docs_sync.py (36 passed)"
        status: pass
    human_judgment: true
    rationale: "ruff format --check exits 1 on 8 pre-existing .planning Markdown files, and installed Vitest/jsdom/Ruff are below their manifests; both are recorded, not green"

duration: 10min
completed: 2026-10-26
status: complete
---

# Phase 4 Plan 03: Alert upgrade contract and acceptance Summary

**Four references now publish the `data-cv-alert-dismiss` / `cv.adapters.alert.close(el)` contract, and the theme.md
custom-frame recipe is rendered by a test. A paired Breaking entry and a migration before/after cover copied templates
and post-load whole-map replacement. Real example flash messages closed in headless Chrome in all three cases: the
Bootstrap transition, the missing-Alert fallback, and a clone inserted after load.**

## Performance

- **Duration:** about 10 min
- **Started:** 2026-10-26T20:29:47Z
- **Completed:** 2026-10-26T20:40Z
- **Tasks:** 3
- **Files modified:** 9 (1 created, 8 modified)

## Accomplishments

- **`javascript.md`:**
  - an `alert.close(el)` row and a new "Dismissible alerts" section: delegation, nearest frame, call-time lookup,
    post-load content, and surfaced errors with no forced removal or rollback
  - the factory is now "all four", and the `viewset.js` "Needs at use" cell names `cv.adapters.alert`
  - the R04-01 whole-map paragraph, with the `cv.bootstrapAdapters(ns).alert` entry
  - the "All three" lifecycle-events sentence is untouched
- **`messages.md`:** the new markup. Closing needs `adapters.js` and then `viewset.js`, both from `cv_js`. The CSS
  classes are unchanged and Bootstrap's `Alert` is optional.
- **`settings.md`:** alert dismissal is listed in `viewset.js`, and `data-cv-alert-dismiss` joins the delegated
  hooks.
- **`theme.md`:**
  - the "### Custom alert frame" recipe, using `notice` / `notice-close` classes, `cv_button_class` and
    `extra_tags`
  - a sentence confining `data-bs-*` to the dropdown templates
- **`CHANGELOG.md`:** an Unreleased Breaking entry, and the Added `cv.adapters` enumeration corrected to four
  adapters.
- **`migrating-1.0.md`:**
  - a before/after of the close control, the required scripts, and advice to migrate even with Bootstrap
  - an accurate legacy Bootstrap-only path, and replace-not-add guidance
  - the pre-load vs post-load whole-map guidance
  - updated adapter, markup, alert-frame, copied-template and silent-break lists
- **Three new tests** in `test_alerts.py`: the recipe render, the core allowlist guard (via
  `_assert_core_bootstrap_data_attributes(root)`) and a lasting `tmp_path` rejection test.

## Task Commits

1. **04-03-01: Adapter, message and frame-override contract.** `d3ec24b` (docs + tests)
2. **04-03-02: Paired Breaking and migration guidance.** `57da26a` (docs)
3. **04-03-03: Final gates and browser acceptance.** `e31221c` (docs: 04-ACCEPTANCE.md, 04-VALIDATION.md)

## Verification Results

- **Focused Python** (`tests/test1/test_alerts.py tests/test1/test_messages.py`): 57 passed.
- **Doc-reading modules:** 96 passed.
- **Final gates:** see [04-ACCEPTANCE.md](04-ACCEPTANCE.md) §2.
  - Full Python: 3495 passed, 1 skipped.
  - Full JS: 183 passed.
  - Strict docs: clean.
  - `ruff check`: passed.
  - `ruff format --check`: **exit 1**, on the 8 pre-existing `.planning/` Markdown files only.
  - Example check: no issues.
  - Docs sync: 36 passed.
- **Installed-tool drift**, recorded and not changed: Ruff 0.16.10, Vitest 4.1.10 and jsdom 29.1.1, all below their
  manifests.
- **Historical probe:** baseline `f6982bfef24f4322cfd01f9f21c3bbed517462fe`. Its `alert.html`, placed in a temporary
  copy of the core tree, was rejected as `crud_views/tags/alert.html`. The current tree passed.
- **Browser** (§6 of [04-ACCEPTANCE.md](04-ACCEPTANCE.md)), headless Google Chrome 156.0.8078.47:
  - Setup: logged in as alice/alice; each message came from a submit of
    `/library/author/<pk>/update/`, which redirected to `/library/author/`.
  - Case A: Bootstrap `Alert` 5.3.3 removed `show`, fired `closed.bs.alert`, and removed the frame after 183 ms.
  - Case B: only the alert entry was swapped to `cv.bootstrapAdapters({}).alert`. The frame was removed
    synchronously, the other adapters kept their identity, and the entry was restored.
  - Case C: a fresh page with the default adapter. The clone in the modal-like content was removed after 164 ms via
    Bootstrap, while the original C stayed attached.
  - The only console error was `/favicon.ico` 404.
- **Documentation semantic review** (04-03-02 human-check, executor-run): **pass**.
  - The migration whole-map bullet and the javascript.md `cv.adapters` section both distinguish pre-load default
    filling from post-load replacement.
  - Both require `alert.close(el)`, and both show `cv.bootstrapAdapters(ns).alert`.
  - The Added list, the reference and the Breaking entry all name four adapters.
  - A maintainer reading at end of phase is still pending.

## Files Created/Modified

- `docs/reference/javascript.md`: the adapter row, Dismissible alerts, whole-map replacement, and four adapters.
- `docs/reference/messages.md`: the new hook markup, the script requirement, and the unchanged classes.
- `docs/reference/theme.md`: the Custom alert frame recipe and the data-bs boundary.
- `docs/reference/settings.md`: the delegated hook list.
- `tests/test1/test_alerts.py`: the recipe, allowlist and negative tests.
- `CHANGELOG.md`: the Breaking entry and the four-adapter Added line.
- `docs/migrating-1.0.md`: the before/after, the load-order guidance, and the lists.
- `.planning/phases/04-alert-dismiss-adapter/04-ACCEPTANCE.md`: evidence (new).
- `.planning/phases/04-alert-dismiss-adapter/04-VALIDATION.md`: statuses and execution results.

## Decisions Made

- Messages A/B/C were produced by update submits with unchanged values, not by creates, so the local example
  database is unchanged in row count.
- The browser smoke uses the `playwright-core` already in the npx cache and the system Chrome. Nothing was installed
  (T-04-SC).
- The nested before/after fence in the migration list needed four-space indentation and a separating blank line. The
  first rendering closed the list, and the rendered HTML was checked after the fix.

## Deviations from Plan

None. The plan was executed as written. One gate, `ruff format --check`, exits 1 on pre-existing files outside this
phase. The plan requires that to be recorded rather than fixed, and it is.

## Issues Encountered

- `ruff format --check`: 8 pre-existing `.planning/` Markdown files (listed in 04-ACCEPTANCE.md §2). Out of scope and
  unchanged.
- A `pkill -f` used to stop the example server also matched its own shell, which exited with code 144. The server was
  confirmed stopped, and the evidence commands were re-run.

## Known Stubs

None.

## User Setup Required

None. No external service configuration is required.

## Next Phase Readiness

- Phase 4's plans are complete. They are ready for phase verification, where the human checks are a maintainer
  reading of the migration and reference prose, plus an optional manual repeat of browser cases A/B/C.
- Classifier assumptions A04-01, A04-02 and the three A04-04 rows remain flagged in 04-SOURCE-AUDIT.md.
- The follow-up for downstream themes (adopt the marker, keep the semantic hooks, add `alert` to any post-load
  whole map) is in 04-ACCEPTANCE.md §8. No other project was changed.

## Self-Check: PASSED

- All 9 key files exist on disk.
- Task commits d3ec24b, 57da26a and e31221c are ancestors of HEAD on `introduce-gsd`.
- 3 commits were measured since `plan_head_before`.

---
*Phase: 04-alert-dismiss-adapter*
*Completed: 2026-10-26*
