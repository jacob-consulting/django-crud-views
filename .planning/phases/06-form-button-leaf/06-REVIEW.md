---
phase: 06-form-button-leaf
reviewed: 2026-10-28T10:45:34Z
depth: deep
files_reviewed: 4
files_reviewed_list:
  - src/crud_views/lib/crispy/buttons.py
  - src/crud_views/lib/view/button_data.py
  - tests/test1/test_button_data.py
  - tests/test1/test_crispy_buttons.py
findings:
  critical: 0
  warning: 0
  info: 3
  total: 3
status: issues_found
---

# Phase 06: Code Review Report

**Reviewed:** 2026-10-28T10:45:34Z
**Depth:** deep
**Files Reviewed:** 4
**Status:** issues_found

## Summary

Incremental re-review of plan 06-10 (gap closure), scoped to `git diff 97dcaac..HEAD` on the four files it changed.
The prior full-phase review (2026-10-28T09:51:51Z, 51 files) found one blocker (CR-01), two warnings (WR-01, WR-02)
and two info items (IN-01, IN-02). This review confirms or refutes the three claimed fixes and carries forward
whatever is still present.

Cross-file traces performed (deep): `ListViewFilterFormHelper.__init__` → `_cv_prepare_layout` (`copy.deepcopy`,
`src/crud_views/lib/views/list.py:139-159`) → `render_layout` (`_CV_HELPER_OWNER` push) → adapter `render()` →
`_cv_button_context` → `cv_button_data(ctx, "form")` → `_form_button_data` → `form.html`; the icon predicates
`_icon_available`, `resolve_icon_name_class`, `resolve_icon` and `_icon_str` (`src/crud_views/lib/icons.py`); the
static check readers of `_KIND_ICONS` (`src/crud_views/lib/view/buttons.py:491-532`); and a repo-wide search for
readers of the renamed private state (`_cv_icon`, `_KIND_ICON`) — none exist outside `crispy/buttons.py` and its
test module, so no stale consumer of the old sentinel-identity contract remains.

Runtime verification (not just reading): the changed test files pass (720 tests), `ruff check` and `ruff format
--check` are clean on all four files, and an independent probe outside the test suite confirmed each prior finding's
scenario (details under each finding below).

### Disposition of the prior review's findings

| Finding | Prior severity | Status now | Evidence |
|---|---|---|---|
| CR-01 `_KIND_ICON` sentinel lost by `deepcopy` | Critical | **FIXED** | `buttons.py:131-132`, `:163`; probe below; `test_copied_filter_layout_keeps_kind_icons`, `test_copied_adapter_keeps_icon_contract` |
| WR-01 no test renders a deep-copied adapter in icon/both | Warning | **FIXED** | `test_crispy_buttons.py:1784-1877` |
| WR-02 normalizer admits any truthy non-str `cv_icon` | Warning | **FIXED** | `button_data.py:246-248`; `test_button_data.py:809-907` |
| IN-01 per-request `deepcopy` of user layouts undocumented / unguarded | Info | **OPEN** (carried forward as IN-01) | `list.py:153`; `docs/reference/list_view.md:170-172` |
| IN-02 extra attributes emitted in sorted order, migration note silent | Info | **OPEN** (carried forward as IN-02) | `button_data.py:280`; `docs/migrating-1.0.md:239` |

**CR-01 — confirmed fixed.** `_TableClassMixin.__init__` now records the omission as `self._cv_kind_icon = icon is
_KIND_ICON` and stores `None` in `_cv_icon` for an omitted argument; `_cv_button_context` selects
`_KIND_ICONS[kind]` from that bool. The sentinel is compared only in the constructor, so no copied instance ever
holds it. Probe (outside pytest, Django configured via `conftest.pytest_configure()`): a `ListViewFilterFormHelper`
subclass with class-level `layout = Layout("name", FormActions(Submit("submit", "Go", slot="form:filter-submit"),
Reset("reset", "Clear")))` and `get_form_actions()` returning `None`, rendered through the real `{% crispy form
helper %}` under `CRUD_VIEWS_LABEL_MODE_DEFAULTS={"form": mode}` and `CRUD_VIEWS_STRICT=True`, yields
`['fa-solid fa-filter', 'fa-solid fa-rotate-left']` for both `mode="both"` and `mode="icon"`, with no warning and no
exception — the exact scenario that previously dropped the icon (both) or raised (icon, strict). `copy.copy`,
`copy.deepcopy` and a `pickle` round-trip of `Submit("submit", "Go")` all produce `cv_icon == "save"` (a `str`).
Explicit `icon=None` → `None`, `icon=""` → `""`, and an explicitly passed `icon=_KIND_ICON` → the kind default, so
the omission/suppression/override distinctions survive. `_KIND_ICONS` keys equal `FORM_KINDS` exactly, so the
`_KIND_ICONS[kind]` lookup after `_cv_form_kind()` validation cannot `KeyError`.

**WR-01 — confirmed fixed.** `test_copied_filter_layout_keeps_kind_icons` (12 cases) renders package adapters placed
in a class-level layout, a layout assigned before the first render, and one assigned between renders, under
`both`/`icon` x strict/lenient, through the real tag, with two helper instances and three interleaved render rounds;
it asserts the kind icons, the accessible label/title/tooltip shape per mode, one action group, stable ids/classes,
that the source layout and its button objects are never mutated or rendered directly, and that both copies hold
distinct button objects. `test_copied_adapter_keeps_icon_contract` covers `copy.copy` and `copy.deepcopy` of all
five kinds with a submitted name that suggests a different kind, asserting `type(cv_icon) is str` and the expected
name, then a real strict render in both/icon. `test_copied_adapter_preserves_explicit_icon` covers `None`, `""`,
`"workflow"` and a prefixed icon through both copiers. The `warnings.simplefilter("error")` guard follows the
module's existing convention (four prior uses).

**WR-02 — confirmed fixed.** `_form_button_data` now does `if not isinstance(icon, str) or not icon.strip(): icon =
None` immediately after reading `cv_icon`, before `_icon_available`, the strict/lenient diagnostics, `icon_host_keys`
and the returned leaf data, so `cv_icon` is always a nonblank `str` or `None` and the diagnostics name `None`
rather than an object repr. Accepted strings are kept exactly: a padded `" save "` is stored as-is and remains
consistent end to end because `_icon_available`, `resolve_icon_name_class` and `render_icon` all strip via
`_icon_str` (probe: available `True`, renders `fa-regular fa-floppy-disk`, leaf data `cv_icon=" save "`,
`cv_icon_class=""`, `cv_icon_inline=True`). A Django lazy string is rejected (`isinstance(..., str)` is `False`),
but the icon registry itself never accepted non-`str` values (`_icon_str`, `resolve_icon` docstring), so this is
consistent, not a regression. The input dict is not mutated (`test_form_icon_normalization_never_mutates_the_input`).

No new blocker or warning was found in the diff. The remaining items are the two carried-forward info findings and
one low-impact test-quality note on a new test.

## Info

### IN-01: Per-request `deepcopy` of arbitrary user layout objects is a new failure surface that the docs do not state

**File:** `src/crud_views/lib/views/list.py:153`; `docs/reference/list_view.md:170-172` ("Custom filter helpers")
**Issue:** Carried forward unchanged from the prior review; 06-10 did not touch it (by design — the plan kept
IN-01/IN-02 open). Every helper construction runs `copy.deepcopy(current)` over whatever the project put into the
class-level or assigned layout, followed by a `__class__` reassignment. A layout object holding a non-copyable member
(a lock, an open resource, a bound C object, a custom `LayoutObject` with `__slots__` and no `__dict__`) now raises
`TypeError` at `get_filterset()` on every request instead of rendering as before. The reference page says the
layout is copied but not that it must be deep-copyable, and the error is not wrapped to name the helper class.
**Fix:** State the deep-copy requirement in `docs/reference/list_view.md` next to "Each helper instance renders its
own copy", and consider:

```python
try:
    prepared = copy.deepcopy(current)
except (TypeError, copy.Error) as exc:
    raise ValueError(
        f"{type(self).__name__}.layout must be deep-copyable (each helper renders its own copy): {exc}"
    ) from exc
```

### IN-02: Extra attributes are emitted in sorted order, not insertion order

**File:** `src/crud_views/lib/view/button_data.py:280`; `docs/migrating-1.0.md:239` ("Markup and submitted data")
**Issue:** Carried forward unchanged from the prior review. Django's `flatatt` sorts key/value attributes and boolean
attributes; crispy's `flatatt` preserved keyword order. A custom `Submit(..., data_b="1", data_a="2")` therefore
renders `data-a` before `data-b`. Harmless for browsers and the package's own buttons, but a byte-level change for
projects with goldens on custom buttons. The migration page only says "the attribute order must match `button`
instead", which does not say the extra attributes are reordered.
**Fix:** Add one sentence to the "Markup and submitted data" list: extra attributes render in sorted order (Django's
`flatatt`), after `type`/`name`/`value`/`id`/`class`.

### IN-03: Adaptive assertion in `test_form_icon_normalization_keeps_nonblank_strings_exactly` has an unreachable branch

**File:** `tests/test1/test_button_data.py:866-881`
**Issue:** The test branches on the outcome it is meant to assert: `if data["cv_label_mode"] == mode:` asserts the
string is kept, `else:` asserts the missing-icon fallback. All five parametrized icons (`"save"`, `" save "`,
`"\tfilter\n"`, `"fas:rocket"`, `"my-raw icon-save"`) are available in the default registry (semantic names, a font
library prefix and a raw class), so the `else` branch is never executed under any `mode`; it is dead test code that
would silently accept a regression in which a valid padded or raw-class icon stopped resolving in `"icon"` mode
(the test would then take the `else` branch and pass). The genuinely unavailable case is already covered by
`test_form_icon_normalization_unavailable_nonblank_string_is_not_none` (`:884`).
**Fix:** Drop the `else` branch and assert unconditionally:

```python
data = cv_button_data(_icon_ctx(icon, cv_label_mode=mode), "form")
assert data["cv_label_mode"] == mode          # every param is an available icon
assert data["cv_icon"] is icon                # kept exactly, never stripped or replaced
assert _warnings(caplog) == []
```

If an unavailable padded string is also wanted, add it as a separate, explicitly-labelled parameter set.

---

_Reviewed: 2026-10-28T10:45:34Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
