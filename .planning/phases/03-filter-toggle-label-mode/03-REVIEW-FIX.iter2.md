---
phase: 03-filter-toggle-label-mode
iteration: 2
findings_in_scope: 1
fixed: 1
skipped: 0
status: all_fixed
---

# Phase 03: Verification Review Fix

## Fixed Issues

### CR-01: A context-mode stamp overrides the explicitly configured list-row mode

**Status:** fixed; independently re-reviewed clean.
**Files:** `src/crud_views/lib/view/base.py`, `tests/test1/test_filter_toggle_label_mode.py`.

Restricted preservation of a pre-resolved context mode to `location="context"`.
List rows again resolve their own map/floor even when the registered context button
has already stamped a toolbar mode. The existing single-resolution toolbar behavior remains intact.

Added a regression test covering context/row pairs label/both, both/icon, and icon/label.
It checks the toolbar context, list context, and normalized list button data.
All three cases failed before the fix and passed afterwards.

## Verification

- Focused filter, context-button, target-context and label-mode modules: 281 passed.
- Regression gate: 896 passed across 16 test modules referenced by Phases 1 and 2.
- Ruff check and formatting of the two changed Python files: passed.
- Independent code reviewer reran the original reproduction and returned a clean review.
- All four human UAT checks passed before this additional row-action correction.

No changes to the filter template, JavaScript, translations, or dependency manifests.
