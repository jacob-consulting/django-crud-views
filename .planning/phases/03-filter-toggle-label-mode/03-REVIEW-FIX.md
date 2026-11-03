---
phase: 03-filter-toggle-label-mode
fixed_at: 2026-10-26T16:32:43Z
review_path: .planning/phases/03-filter-toggle-label-mode/03-REVIEW.md
iteration: 1
findings_in_scope: 2
fixed: 2
skipped: 0
status: all_fixed
---

# Phase 03: Code Review Fix Report

**Fixed at:** 2026-10-26T16:32:43Z
**Source review:** `.planning/phases/03-filter-toggle-label-mode/03-REVIEW.md`
**Iteration:** 1

**Summary:**

- Findings in scope: 2
- Fixed: 2
- Skipped: 0
- Scope: warnings only; Info findings and the original review are unchanged.

## Fixed Issues

### WR-01: `cv_label_mode` is resolved and stamped twice on every filter render, by two call sites that only coincidentally agree

**Status:** fixed: requires human verification
**Files modified:** `src/crud_views/lib/view/base.py`, `tests/test1/test_filter_toggle_label_mode.py`,
`docs/reference/context_buttons.md`
**Commit:** `72c80f1`
**Applied fix:** `cv_get_context()` preserves a mode already resolved by the button. The filter's label template
and final button template therefore receive the same value, resolved once. Ordinary contexts without a stamp still
use the existing resolver. Documented that the filter's label templates receive this resolved `cv_label_mode`.
Added a three-mode toolbar regression that counts resolver calls, compares the label with the rendered mode, and
checks a subclass that adds a conflicting target-view default after resolving its label.

### WR-02: A malformed stamped `cv_label_mode` is silently rendered as the icon form, in strict mode too, contradicting the documented strict-mode policy

**Status:** fixed: requires human verification
**Files modified:** `src/crud_views/lib/view/buttons.py`, `tests/test1/test_filter_toggle_label_mode.py`,
`docs/reference/buttons.md`
**Commit:** `6c582d8`
**Applied fix:** Validate the resolved filter mode before stamping it and rendering its label template. Reused
the existing label-mode policy: strict mode raises `ValueError` identifying the filter and `cv_label_mode`;
non-strict mode warns once per location and value and uses the configured context floor. Updated the reference
and removed the regression assertion that accepted silent icon fallback from malformed runtime configuration.
Added 24 regression cases covering view, ViewSet, settings and button configuration, two invalid strings, and
all three floors. Each checks direct contexts and actual toolbar renders, strict exceptions, repeated non-strict
renders, warning deduplication, and the fallback value received by custom labels.

The status annotations above flag logic changes for human review under the fixer workflow; automated behavioral
regressions also pass. No source or test files were created.

## Verification

All verification ran in the **isolated worktree**, using the main checkout's existing `.venv` executables.
Python tests used `PYTHONPATH="$PWD/src:$PWD"` so they exercised the worktree's source and tests.

- Re-read every modified section and checked Python parsing with `ast.parse` for both findings.
- WR-01 focused filter, context/row label-mode, button-leaf and documentation tests: **256 passed**.
- WR-02 focused filter and documentation tests: **122 passed**.
- Final `pytest tests -q -n auto`: **3484 passed, 1 skipped**.
- Final `ruff check src tests`: passed.
- Final `ruff format --check src tests`: **288 files already formatted**.
- `mkdocs build --strict --site-dir /tmp/django-crud-views-reviewfix-site`: passed.
- `git diff --check`: passed. Each finding was committed separately with no remaining source changes.

The user's `introduce-gsd` branch was fast-forwarded to include both fix commits.

---

_Fixed: 2026-10-26T16:32:43Z_
_Fixer: the agent (gsd-code-fixer)_
_Iteration: 1_
