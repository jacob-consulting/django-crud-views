---
phase: 04-alert-dismiss-adapter
reviewed: 2026-10-26T21:04:34Z
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
  warning: 0
  info: 4
  total: 4
status: issues_found
---

# Phase 04: Code Review Report

**Reviewed:** 2026-10-26T21:04:34Z
**Depth:** deep
**Files Reviewed:** 14
**Status:** issues_found

## Summary

Incremental re-review after the disposition of the first pass (2026-10-26T20:51:14Z). The only non-planning change
since `6228776` is commit `b7b49ae` (`docs/reference/theme.md`, `docs/reference/messages.md`,
`tests/test1/test_alerts.py`; `git diff --stat 6228776..HEAD -- . ':!.planning'` shows nothing else). This pass
re-read those three files in full and re-verified every claim they make against the shipped sources
(`src/crud_views/static/crud_views/js/viewset.js`, `adapters.js`, `modal.js`, `formset.js`, `tooltip.js`,
`src/crud_views/lib/settings.py`, and every `*.html` under `src/`). Findings against files unchanged since the first
pass are carried over and were re-checked at the cited lines in the current working tree.

Verification of the two fixes:

- **WR-01 (theme.md data-bs-* claim) — resolved.** `grep -rn "data-bs-" src/ --include=*.html` returns exactly
  `crud_views/snippets/language_selector.html:6`, `crud_views/tags/actions_menu_toggle.html:4-5`,
  `crud_views_object_detail/.../layouts/accordion/group.html:5,15` (collapse) and
  `crud_views_object_detail/.../layouts/tabs-vertical/object_detail.html:10-11` (pill, i.e. Bootstrap's Tab plugin).
  The rewritten paragraph (`theme.md:212-216`) scopes "the only ones" to the core `crud_views` templates, which is
  now true, and names both object-detail layouts with the right component families. The guard docstring
  (`test_alerts.py:328`) now asserts the same core-only fact as the doc and as `CORE_TEMPLATES` (line 22). Dropped.
- **IN-03 (messages.md "does nothing") — resolved.** `messages.md:41-43` now separates the two cases. Both are
  accurate: with neither script the `type="button"` control has no handler; with `viewset.js` alone,
  `viewset.js:54` evaluates `globalThis.cv.adapters.alert.close(frame)`. If no other core script ran,
  `globalThis.cv` is `undefined` (TypeError reading `adapters`); if `modal.js:143`, `formset.js:617` or
  `tooltip.js:70` created the namespace, `cv.adapters` is `undefined` (TypeError reading `alert`). Either way an
  uncaught `TypeError` surfaces in the console on every click, after `e.preventDefault()` at line 53. Dropped.

Other checks on the change: the two anchors the edited text links to (`javascript.md#what-the-scripts-need`,
`javascript.md#dismissible-alerts`) resolve to headings at `javascript.md:7` and `:188`; `{% cv_js %}` still renders
`adapters.js` before `viewset.js` (`settings.py:288-289`); `tests/test1/test_alerts.py` passes (34 tests,
`pytest tests/test1/test_alerts.py -q -n auto`). No correctness or security defect in the shipped JavaScript or
template; all remaining findings are robustness and doc/test-drift items.

## Info

### IN-01: `[role="alert"]` matches only a single-token role attribute

**File:** `src/crud_views/static/crud_views/js/viewset.js:51`
**Issue:** `control.closest('[role="alert"]')` is an exact-value match. The WAI-ARIA `role` attribute is a
space-separated token list (fallback roles, e.g. `role="alert status"`); such a frame would be silently ignored
(no adapter call, no error), even though it is a valid alert. The docs consistently say `role="alert"`, so this is
a robustness nit, not a contract breach. Unchanged since the first pass.
**Fix:** `control.closest('[role~="alert"]')` accepts the token form at no cost; update the three doc mentions if
you adopt it.

### IN-02: The `BOOTSTRAP_DATA_ALLOWED` allowlist is hand-copied from `theme.md` rather than derived from it

**File:** `tests/test1/test_alerts.py:24-30`; docstring at line 328 says "named in theme.md"
**Issue:** The allowlist duplicates the bullet list under `## Templates that follow Bootstrap's DOM`
(`theme.md:205-207`). If the doc list changes (a template is added or renamed) the guard keeps passing and the two
drift apart silently. The suite already parses doc sections with `_section` (used in this same file for the frame
recipe, line 251). Unchanged since the first pass; only the line numbers moved.
**Fix:** Build the allowlist from the doc: `_section(THEME_MD.read_text(), "## Templates that follow Bootstrap's DOM")`
and extract the backticked `tags/...` / `snippets/...` paths, prefixing `crud_views/`.

### IN-04: The new `theme.md` sentence about non-core `data-bs-*` templates has no guard

**File:** `docs/reference/theme.md:214-216`; guard at `tests/test1/test_alerts.py:319-329`
**Issue:** The WR-01 fix added a factual claim about the distribution outside core ("the `crud_views_object_detail`
layouts `layouts/accordion/group.html` and `layouts/tabs-vertical/object_detail.html` still use Bootstrap's collapse
and tab attributes"). It is true today (those are the only two non-core templates with `data-bs-*`), but
`test_stock_bootstrap_data_attributes_are_dropdown_only` only walks `CORE_TEMPLATES`, so a `data-bs-*` attribute
added to a workflow, polymorphic, guardian or third object-detail layout template, or removed from one of the two
named layouts, leaves the sentence stale with no failing test. This is the same drift class as IN-02, now with a
second doc location. `_assert_core_bootstrap_data_attributes` is already root-parametrised, so the extension is
cheap.
**Fix:** Add a second guard over the object-detail package and assert the other packages carry none:

```python
OBJECT_DETAIL_TEMPLATES = ROOT / "src" / "crud_views_object_detail" / "templates"
OBJECT_DETAIL_DATA_ALLOWED = frozenset(
    {
        "crud_views_object_detail/layouts/accordion/group.html",
        "crud_views_object_detail/layouts/tabs-vertical/object_detail.html",
    }
)


def test_non_core_bootstrap_data_attributes_are_the_two_object_detail_layouts():
    """theme.md: outside core, only the accordion and tabs-vertical layouts carry data-bs-*."""
    found = {
        p.relative_to(p.parents[len(p.relative_to(ROOT / "src").parts) - 2]).as_posix()
        for p in (ROOT / "src").glob("crud_views_*/templates/**/*.html")
        if "data-bs-" in p.read_text()
    }
    assert found == OBJECT_DETAIL_DATA_ALLOWED
```

(or, simpler, pass `OBJECT_DETAIL_TEMPLATES` to a variant of `_assert_core_bootstrap_data_attributes` that takes
the allowlist as a parameter, and assert `"data-bs-"` is absent under the workflow/polymorphic/guardian roots).

### IN-05: `messages.md` enumerates two of the three missing-script combinations

**File:** `docs/reference/messages.md:41-43`
**Issue:** The IN-03 fix reads "with neither script it does nothing, and with `viewset.js` but no `adapters.js`
each click throws a `TypeError`". The third combination, `adapters.js` without `viewset.js`, also does nothing
(no delegated click handler is registered; `adapters.js` only builds `cv.adapters`), but a reader in that
situation matches neither named case. The behaviour is correct; the sentence just reads as a complete enumeration
and is not one.
**Fix:** Fold the two no-op cases together: "...but the X does not close it: without `viewset.js` it does nothing,
and with `viewset.js` but no `adapters.js` each click throws a `TypeError` in the console."

---

_Reviewed: 2026-10-26T21:04:34Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
