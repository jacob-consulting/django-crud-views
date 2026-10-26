---
phase: 04-alert-dismiss-adapter
reviewed: 2026-10-26T20:51:14Z
depth: deep
files_reviewed: 14
files_reviewed_list:
  - CHANGELOG.md
  - docs/migrating-1.0.md
  - docs/reference/javascript.md
  - docs/reference/messages.md
  - docs/reference/settings.md
  - docs/reference/theme.md
  - src/crud_views/static/crud_views/js/adapters.js
  - src/crud_views/static/crud_views/js/viewset.js
  - src/crud_views/templates/crud_views/tags/alert.html
  - tests/js/adapters.test.js
  - tests/js/viewset.test.js
  - tests/test1/golden/alerts/dismissible.html
  - tests/test1/test_alerts.py
  - tests/test1/test_messages.py
findings:
  critical: 0
  warning: 1
  info: 3
  total: 4
status: issues_found
---

# Phase 04: Code Review Report

**Reviewed:** 2026-10-26T20:51:14Z
**Depth:** deep
**Files Reviewed:** 14
**Status:** issues_found

## Summary

Reviewed the phase diff (`1b77934..HEAD`, 8 commits) for the alert-dismiss adapter: the new `alert.close(el)`
entry in `cv.bootstrapAdapters`, the delegated `[data-cv-alert-dismiss]` click handler in `viewset.js`, the
`tags/alert.html` attribute swap, the golden, the Python and vitest coverage, and the six documentation files.
Both test suites were executed against the working tree (57 Python tests in `test_alerts.py`/`test_messages.py`
and 59 vitest cases in `adapters.test.js`/`viewset.test.js` pass).

Cross-file tracing done at deep depth:

- `{% cv_js %}` order (`src/crud_views/lib/settings.py:288-289`) renders `adapters.js` before `viewset.js`, matching
  the claim in `messages.md`, `javascript.md` and `CHANGELOG.md`.
- `viewset.js:54` resolves `globalThis.cv.adapters.alert` at click time, the same convention as
  `list.filter.js:15`; the preassigned-adapter merge at `adapters.js:52` keeps a partial early map and fills `alert`.
- No `data-bs-dismiss="alert"` survives in `src/`, `examples/` or the reference docs outside the deliberate
  before/after migration snippet; the core-template guard in `test_alerts.py` confirms the attribute set under
  `src/crud_views/templates`.
- Every intra-doc anchor the phase introduced (`#dismissible-alerts`, `#custom-alert-frame`, `#cvadapters`,
  `#what-the-scripts-need`, `#contract-changes-in-templates-you-still-override`, `#hooks-instead-of-copies`, and
  the checklist anchors) resolves to an existing heading.
- The `cv.adapters` "Added" wording change in `CHANGELOG.md` (line ~306) sits under `## Unreleased`, not a
  released section.
- Locked decisions D-03/D-04 (no catch/log/fallback after a custom-adapter or component failure, `el.remove()`
  only inside the default adapter) are implemented as specified and are not reported as defects.

No correctness or security defect was found in the shipped JavaScript or template. The one warning is a
documentation claim that is false for the distribution as shipped and that the accompanying test guard is scoped
too narrowly to catch.

## Warnings

### WR-01: `theme.md` claims the dropdown templates are the only stock templates with `data-bs-*`, but the object-detail layouts also carry them

**File:** `docs/reference/theme.md:212-214`; guard at `tests/test1/test_alerts.py:306-313,320-327`
**Issue:** The new paragraph states "These dropdown templates are the only stock templates with Bootstrap
`data-bs-*` attributes." That is only true for `src/crud_views/templates`. The distribution also ships
`src/crud_views_object_detail/templates/crud_views_object_detail/layouts/accordion/group.html:5,15`
(`data-bs-toggle="collapse"`, `data-bs-target`, `data-bs-parent`) and
`layouts/tabs-vertical/object_detail.html:10-11` (`data-bs-toggle="pill"`, `data-bs-target`). A theme author on a
non-Bootstrap framework who trusts this sentence will override the three dropdown templates and still get
non-functional accordion/tab layouts from `ObjectDetailView`. The guard test
`test_stock_bootstrap_data_attributes_are_dropdown_only` only walks `CORE_TEMPLATES`
(`src/crud_views/templates`), so it validates the narrower fact while the docstring and the doc assert the
broader one; `theme.md` never mentions the object-detail package at all (grep for `object_detail`, `accordion`,
`tabs-vertical`, `pill` returns nothing).
**Fix:** Either scope the sentence or widen the truth. Minimal doc fix:

```markdown
These dropdown templates are the only `crud_views` core templates with Bootstrap `data-bs-*` attributes. The
alert frame has none: its close control uses `data-cv-alert-dismiss` and the alert adapter, see
[Dismissible alerts](javascript.md#dismissible-alerts). `crud_views_object_detail`'s `accordion` and
`tabs-vertical` layouts still use Bootstrap's collapse and pill data API; override those layout templates
on another framework.
```

And align the guard's docstring with its actual scope (or extend it to the object-detail root with those two
layouts in `BOOTSTRAP_DATA_ALLOWED`) so the test and the doc assert the same fact.

## Info

### IN-01: `[role="alert"]` matches only a single-token role attribute

**File:** `src/crud_views/static/crud_views/js/viewset.js:51`
**Issue:** `control.closest('[role="alert"]')` is an exact-value match. The WAI-ARIA `role` attribute is a
space-separated token list (fallback roles, e.g. `role="alert status"`); such a frame would be silently ignored
(no adapter call, no error), even though it is a valid alert. The docs consistently say `role="alert"`, so this is
a robustness nit, not a contract breach.
**Fix:** `control.closest('[role~="alert"]')` accepts the token form at no cost; update the three doc mentions if
you adopt it.

### IN-02: The `BOOTSTRAP_DATA_ALLOWED` allowlist is hand-copied from `theme.md` rather than derived from it

**File:** `tests/test1/test_alerts.py:19-25`; docstring at line 334 says "named in theme.md"
**Issue:** The allowlist duplicates the bullet list under `## Templates that follow Bootstrap's DOM`. If the doc
list changes (a template is added or renamed) the guard keeps passing and the two drift apart silently. The suite
already parses doc sections with `_section` (used in this same file for the frame recipe).
**Fix:** Build the allowlist from the doc: `_section(THEME_MD.read_text(), "## Templates that follow Bootstrap's DOM")`
and extract the backticked `tags/...` / `snippets/...` paths, prefixing `crud_views/`.

### IN-03: `messages.md` understates the `viewset.js`-without-`adapters.js` case

**File:** `docs/reference/messages.md:40-41`
**Issue:** "Without the core scripts the alert still renders and reads correctly; only the X does nothing." is
accurate when both scripts are absent, but a page that hand-lists `viewset.js` without `adapters.js` gets an
uncaught `TypeError` (`globalThis.cv` is undefined at `viewset.js:54`) on every click, not a silent no-op. The
migration checklist (`docs/migrating-1.0.md:133-134`) says such pages "lose ... alert dismissal" without naming
the error; only the whole-map-replacement case names the `TypeError`.
**Fix:** One clause: "...only the X does nothing (with `viewset.js` but no `adapters.js` the click throws a
`TypeError`, see [What the scripts need](javascript.md#what-the-scripts-need))."

---

_Reviewed: 2026-10-26T20:51:14Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
