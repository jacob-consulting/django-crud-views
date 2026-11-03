---
phase: 06-form-button-leaf
fixed_at: 2026-10-28T12:00:00Z
review_path: .planning/phases/06-form-button-leaf/06-REVIEW.md
iteration: 1
findings_in_scope: 3
fixed: 3
skipped: 0
status: all_fixed
---

# Phase 06: Code Review Fix Report

**Fixed at:** 2026-10-28T12:00:00Z
**Source review:** .planning/phases/06-form-button-leaf/06-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 3 (fix_scope: all; the review had 0 critical, 0 warning, 3 info)
- Fixed: 3
- Skipped: 0

## Fixed Issues

### IN-01: Per-request `deepcopy` of arbitrary user layout objects is a new failure surface that the docs do not state

**Files modified:** `src/crud_views/lib/views/list.py`, `docs/reference/list_view.md`, `tests/test1/test_crispy_buttons.py`
**Commit:** aed6003
**Applied fix:** `ListViewFilterFormHelper._cv_prepare_layout` now wraps `copy.deepcopy(current)`. A
`TypeError`/`copy.Error` is re-raised as a `TypeError` that names the helper class
(`"<Helper>.layout must be deep-copyable (each helper renders its own copy): ..."`), chained with `from exc`. The
docstring states the requirement. The "Custom filter helpers" section of `docs/reference/list_view.md` now says the
layout must be deep-copyable and when the error is raised: when the helper is created, or for an assigned layout,
when it next renders. A new test, `test_filter_layout_that_cannot_be_deep_copied_names_the_helper`, covers a
class-level layout and an assigned one, both holding a `threading.Lock`. It checks the message, the chained cause and
that the caller's layout is not mutated.
**Deviation from the suggestion:** the review suggested `ValueError`. I kept `TypeError`, the type `deepcopy` already
raised, so existing `except TypeError` handlers keep working. Only the message changes. The `__class__` reassignment
is not wrapped. `_prepared_layout_class` always builds a plain subclass, so it only fails for exotic `__slots__`
layouts, and those already fail at the deepcopy step.

### IN-02: Extra attributes are emitted in sorted order, not insertion order

**Files modified:** `docs/migrating-1.0.md`
**Commit:** 92d5430
**Applied fix:** Added a paragraph to the first bullet of "Markup and submitted data". Extra button attributes render
after `type`, `name`, `value`, `id` and `class` (and after the cancel URL and icon-only title when present). They come
in Django `flatatt`'s sorted order with boolean attributes last, while crispy kept the keyword order. It gives the
`data_b="1", data_a="2"` example. A runtime probe of
`Submit("submit", "Go", data_b="1", data_a="2", formnovalidate=True)` confirmed this order:
`... class="btn btn-primary" data-a="2" data-b="1" formnovalidate`. The change is docs-only and adds no `### Breaking`
changelog entry.

### IN-03: Adaptive assertion in `test_form_icon_normalization_keeps_nonblank_strings_exactly` has an unreachable branch

**Files modified:** `tests/test1/test_button_data.py`
**Commit:** d75fb31
**Applied fix:** Removed the `if/else` that branched on the outcome. The test now asserts unconditionally that
`cv_label_mode == mode`, that `cv_icon is icon` and that no warnings were logged, for all 15 parameter combinations.
A comment points to the following test, which covers the unavailable-string case.

## Verification

All gates ran inside the isolated worktree (`.claude/worktrees/rf-06-...`) against the worktree sources
(`PYTHONPATH=<worktree>/src`, the main checkout's `.venv`). The worktree has since been fast-forwarded into
`introduce-gsd` and removed, so the same commits can be re-checked from the main checkout.

- IN-01: `pytest tests/test1/test_crispy_buttons.py tests/test1/test_filter.py`: 289 passed. `ruff check` and
  `ruff format --check` were clean on both changed Python files.
- IN-02: docs-only (Tier 1 re-read), plus the runtime probe described above.
- IN-03: `pytest tests/test1/test_button_data.py`: 458 passed. `ruff check` and `ruff format --check` were clean.
- The pre-commit `ruff-format` hook passed on every commit.
- After all three commits, one full-suite run in the worktree (`pytest tests`): 4633 passed.

---

_Fixed: 2026-10-28T12:00:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
