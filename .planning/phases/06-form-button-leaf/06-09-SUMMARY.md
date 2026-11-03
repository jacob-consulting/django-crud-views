---
phase: 06-form-button-leaf
plan: "09"
subsystem: testing
tags: [acceptance, validation, crispy-forms, chromium, cdp, nox, mkdocs, ruff, accessibility]

requires:
  - phase: 06-form-button-leaf
    provides: "form leaf and goldens (06-01/02), ownership and maps (06-03), icons (06-04), filter actions (06-05), diagnostics (06-06), JS/floor gates (06-07), docs/example both mode (06-08)"
provides:
  - 06-ACCEPTANCE.md with measured gates, baseline history, payload, cycle-3 repair, FORM/D/threat traceability, browser observations and downstream follow-up
  - 06-VALIDATION.md task/wave/threat rows and sign-off from measured results
affects: [phase-06-verification, ship]

actuals:
  tokens: 9400
  tasks: 2
  commits: 2
plan_head_before: e40b0ded5daea3b7b60a11f72636a75119afbce3
plan_head_after: 0357ff2320b35b5643efdd6bc758783bd6eded5b

tech-stack:
  added: []
  patterns:
    - "Browser acceptance through Chrome DevTools Protocol with Node built-ins only (no package install): per-mode scratch settings, DB copy, server port and profile"
    - "Pre-existing gate failures proven by piping the phase-start blob through the same checker"

key-files:
  created:
    - .planning/phases/06-form-button-leaf/06-ACCEPTANCE.md
  modified:
    - .planning/phases/06-form-button-leaf/06-VALIDATION.md
    - .planning/WINDOWS.md

key-decisions:
  - "Whole-repo ruff format --check is recorded as not green (9 planning Markdown files that already failed at 49f44cd); code and every Phase 06 changed file are proven formatted separately"
  - "Hover tooltip, visual quality, screen-reader announcement and migration readability stay pending human; focus tooltips and AX-tree names are the automated evidence"
  - "Downstream follow-up recorded generically (device-floppy / x / filter-off glyphs, input-to-button selectors, delete assertions, no new template override)"

patterns-established:
  - "Acceptance records measure every gate at a named HEAD and cite earlier summaries only for history"

requirements-completed: [FORM-01, FORM-02, FORM-03, FORM-04, FORM-05, FORM-06, FORM-07, FORM-08, FORM-09, FORM-10, FORM-11, FORM-12, FORM-13]

coverage:
  - id: D1
    description: "Full Python suite, both-order one-process isolation runs and crispy floors pass at HEAD e40b0de"
    requirement: FORM-06
    verification:
      - kind: integration
        ref: ".venv/bin/pytest tests -n auto (4445 passed); .venv/bin/pytest tests -p no:randomly (4445 passed)"
        status: pass
      - kind: integration
        ref: ".venv/bin/nox -s crispy_floor (Django 4.2.30 / 6.0.9, 1877 each)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Baselines 2956f3e/98b71ed are ancestral with unchanged src tree dcc38f4; only the five form-button goldens changed"
    requirement: FORM-01
    verification:
      - kind: other
        ref: "git merge-base --is-ancestor; git rev-parse B^:src B:src; git diff --name-only 49f44cd HEAD over 29 other goldens"
        status: pass
    human_judgment: false
  - id: D3
    description: "Delete payload cited separately and cycle-3 repairs re-run"
    requirement: FORM-06
    verification:
      - kind: integration
        ref: "repair/payload shard (102 passed): test_delete_author, test_delete_control_submits_delete_name_and_value, test_delete_post_with_clicked_submitter, test_filter_empty_layout_replacement_dispatches_through_the_tag, test_enclosing_helper_overlays_are_never_page_layers, test_formset_page_tier_is_transported_exactly, test_unknown_direct_prefix_and_unusable_renderer_are_w292, test_counting_inline_renderer_runs_once_per_icon_render"
        status: pass
    human_judgment: false
  - id: D4
    description: "Docs, JS, lint and example consumer gates"
    requirement: FORM-13
    verification:
      - kind: other
        ref: ".venv/bin/mkdocs build --strict; 06-js-verify.sh (223); ruff check; example SystemChecksTest (1), test_docs_sync.py (36), test_i18n.py + landing + test_doc_links.py (72)"
        status: pass
      - kind: other
        ref: ".venv/bin/ruff format --check (whole repo; 9 pre-existing planning Markdown files)"
        status: fail
    human_judgment: false
  - id: D5
    description: "Real Chromium label/both/icon: accessible names, keyboard focus, focus tooltips, pointer/keyboard cancel, filter apply/reset keeping sort/dir, modal delete submit"
    requirement: FORM-10
    verification:
      - kind: e2e
        ref: "scratch CDP driver against examples/bootstrap5 runserver (ACCEPTANCE §9)"
        status: pass
    human_judgment: false
  - id: D6
    description: "Hover tooltip, visual quality, screen-reader announcement, migration-prose readability"
    requirement: FORM-04
    verification: []
    human_judgment: true
    rationale: "Hover did not register in the headless harness; appearance and assistive-technology output need a human observer"

duration: 22min
completed: 2026-10-28
status: complete
---

# Phase 06 Plan 09: Form-button acceptance Summary

**Phase 06 is accepted on measured evidence at HEAD `e40b0de`. 4445 Python tests pass in parallel and in one process. The crispy floor passes on Django 4.2 and 6.0 (1877 tests each), and the JS suite passes 223 of 223. The baselines are proven to precede every `src` change, and only the five form-button goldens moved. A real Chromium run of the example confirmed accessible save, delete, cancel and filter buttons, keyboard focus, tooltips, cancel, filter reset and modal submit in label, both and icon modes. Two items stay explicitly open: the pre-existing whole-repo format drift, and four checks only a human can make.**

## Performance

- **Duration:** 22 min
- **Started:** 2026-10-28T08:26:38Z
- **Completed:** 2026-10-28T08:48:15Z
- **Tasks:** 2
- **Files modified:** 3 (1 created)

## Accomplishments

- Measured every gate fresh at HEAD `e40b0de`:
  - Python: `pytest -n auto` 4445 passed in 57.25 s; the one-process run 4445 passed in 343.82 s; the phase modules in one process, forward and reversed, 762 passed each.
  - Floors: `nox -s crispy_floor` passed 1877 tests on each of Django 4.2.30 and 6.0.9.
  - Other gates: JS 223 passed, `mkdocs --strict` exit 0, `ruff check` clean.
  - Example project: SystemChecksTest 1 passed, docs-sync 36, and i18n/landing/doc-links 72 (11 + 1 + 60 collected, including the German `value="Sichern"`).
- Proved the baseline history. `2956f3e` and `98b71ed` are ancestors of HEAD and have the same `src` tree as their parents and as `49f44cd`, and the first `src` change is `df2308b`. The final golden diffs touch only the five `form_buttons/*.html` files; the 29 other goldens are unchanged.
- Recorded delete-payload evidence in three separate pieces: the unchanged confirmation-only POST, the rendered submitter, and confirmation plus the clicked submitter. None of them claims that a POST with only the submitter is valid.
- Re-ran the cycle-3 repairs (102 passed together with the payload tests): the helper and layout dispatch guards `(True, True, 0, False)`, distinct page and enclosing-helper owners, recursive formset page transport, and unknown-prefix W292 with renderer call counts.
- Mapped FORM-01..13, D-01..D-18 and all 18 threats to tests, commits and docs. The high threats were re-run (109 Python and 123 JS passed). The two unclassified edge assumptions stay flagged.
- Ran a real browser check without installing anything. A Chrome DevTools Protocol driver built on Node built-ins drove the locally installed headless Chromium. Each mode had its own example server, settings, seeded database and profile.
- Recorded the generic downstream-theme follow-up without naming or editing a downstream project.

## Task Commits

1. **Task 1 (tracer): Verify integrated real forms and record baseline-to-button evidence** - `9058cc6` (docs). Tracer gate (interactive, end-of-phase, automated-only verify): re-ran `pytest tests -n auto` after the commit (4445 passed in 54.34 s), then expanded.
2. **Task 2: Record browser and downstream acceptance with final quality gates** - `0357ff2` (docs)

**Plan metadata:** the docs commit that adds this SUMMARY.

## Files Created/Modified

- `.planning/phases/06-form-button-leaf/06-ACCEPTANCE.md`: the acceptance record, sections §1–§11
- `.planning/phases/06-form-button-leaf/06-VALIDATION.md`: measured task, wave and threat rows, manual-check status, sign-off, `nyquist_compliant: true`
- `.planning/WINDOWS.md`: entry for the pending human checks (unrun-verify)

## Decisions Made

See `key-decisions` in the frontmatter.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] The protected-branch query returns the base branch name**
- **Found during:** Task 1 commit
- **Issue:** `gsd-tools query git.base-branch --is-protected introduce-gsd` prints `main` rather than a boolean, so the stock Step 0 guard refused to commit on a branch that is not protected.
- **Fix:** The guard now compares the current branch with that base branch and with the fallback list (`main`/`master`/`develop`/`trunk`/`release/*`), and fails closed on a match. `introduce-gsd` is neither, and SEQUENTIAL=true applies.
- **Files modified:** none (commit procedure only)

**2. [Rule 3 - Blocking] Browser harness adjustments**
- **Found during:** Task 2
- **Issue:** The host forbids unprivileged user namespaces, so headless Chromium aborted ("No usable sandbox").
- **Fix:** Ran it with `--no-sandbox`. It loaded only the local example server and the example's own CDN assets, with a scratch profile.
- **Driver bugs fixed:** a listener-array mutation during dispatch; Enter needing `text: "\r"`; a comma-list selector; tooltips being read globally instead of per trigger.
- **Files modified:** scratch only (not tracked)

**Total deviations:** 2, both blocking issues in tooling or procedure. Product, test, docs and lock files are unchanged.

## Issues Encountered

- **Not green and recorded, not repaired:**
  - The whole-repo `ruff format --check` exits 1 on 9 planning Markdown files. All 9 already failed at `49f44cd`, and none changed in the phase (WINDOWS #4).
  - The dev-only `undici` audit advisory stays open (WINDOWS #6). It is not a form-render finding.
- **Hover tooltips were not observed.** Synthetic pointer moves did not set `:hover` on the lower-page form buttons, although clicks at the same coordinates worked. Focus tooltips were observed instead. This is recorded as pending human.

## Known Stubs

None.

## Threat Flags

None. No new surface was added; this plan wrote planning documents only.

## User Setup Required

None.

## Next Phase Readiness

- Phase verification can use 06-ACCEPTANCE.md directly. Still open: the four human-only checks in §9, and the two recorded non-green items (WINDOWS #4, #6).

## Self-Check: PASSED

- FOUND: `.planning/phases/06-form-button-leaf/06-ACCEPTANCE.md`, `.planning/phases/06-form-button-leaf/06-VALIDATION.md`
- FOUND: `9058cc6`, `0357ff2` (ancestors of HEAD). Measured `git rev-list --count e40b0de..HEAD` = 2 before this SUMMARY commit.

---
*Phase: 06-form-button-leaf*
*Completed: 2026-10-28*
