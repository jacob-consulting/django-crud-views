---
phase: 01-label-mode-defaults
reviewed: 2026-10-26T08:58:11Z
depth: deep
files_reviewed: 20
files_reviewed_list:
  - src/crud_views/lib/settings.py
  - src/crud_views/lib/view/action_menu.py
  - src/crud_views/lib/view/base.py
  - src/crud_views/lib/view/button_data.py
  - src/crud_views/lib/view/buttons.py
  - src/crud_views/lib/view/card.py
  - src/crud_views/lib/view/label_mode.py
  - src/crud_views/lib/views/card.py
  - tests/test1/conftest.py
  - tests/test1/test_action_label_mode_config.py
  - tests/test1/test_action_label_mode_render.py
  - tests/test1/test_button_data.py
  - tests/test1/test_button_leaves.py
  - tests/test1/test_card_label_mode_render.py
  - tests/test1/test_card_label_modes.py
  - tests/test1/test_context_action_label_mode.py
  - tests/test1/test_context_button_label_mode.py
  - tests/test1/test_import_safety.py
  - tests/test1/test_label_mode.py
  - tests/test1/test_label_mode_docs.py
findings:
  critical: 1
  warning: 3
  info: 7
  total: 11
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-10-26T08:58:11Z
**Depth:** deep
**Files Reviewed:** 20
**Status:** issues_found

## Summary

Reviewed the diff `06a8b81..HEAD` for the `CRUD_VIEWS_LABEL_MODE_DEFAULTS` floor: `default_label_mode()` and
`_invalid_label_mode()` in `label_mode.py`, the floor at the three resolution sites (`cv_button_data`,
`CrudView.cv_get_action_label_mode`, `CardListView.cv_get_card_actions_label_mode`), the E108 settings check, the
W292 strict-mode guard, and the new tests. Call chains were traced from the `cv_button` template tag and
`cv_get_context(location=...)` down to the floor, and from `checks.py` to E108 and W292. The full suite passes
(`pytest tests -n auto`: 3056 passed, 1 skipped). Each finding below was checked with a scratch probe or a temporary
test, which was then deleted.

The core precedence logic is correct. The floor is read only for keys nothing names, strict mode raises before the
fallback runs, the lock does not deadlock on re-entry, and `settings.py` stays import-safe. Main findings:

- The card resolver became a classmethod, so a per-instance `cv_card_actions_label_mode` is now silently ignored.
- The configurable floor can make every card or list button icon-only, but there is no system check for that and
  the strict-mode error hint points at knobs that do not apply.
- Two subprocess tests have a tight 10 s timeout.

## Critical Issues

### CR-01: Card label mode set on the view instance is now ignored

**File:** `src/crud_views/lib/views/card.py:54` and `src/crud_views/lib/views/card.py:109-115`
**Issue:** Before this phase, `cv_get_card_action_data` read `self.cv_card_actions_label_mode`, so a value set on
the instance worked. That covers `CardListView.as_view(cv_card_actions_label_mode="label")` initkwargs and assignment
in `setup()`, `dispatch()` or `get_queryset()` (for example a per-user preference). The method now calls the
classmethod `cv_get_card_actions_label_mode()`, which reads `cls.cv_card_actions_label_mode` only. Any instance-level
value is silently dropped and the card floor is used instead. Confirmed with a temporary test:

```
v = AuthorCardListView(); v.cv_card_actions_label_mode = "label"
v.cv_get_card_actions_label_mode()   # -> "both"
AuthorCardListView.as_view(cv_card_actions_label_mode="label")  # accepted by Django, no effect at render
```

This contradicts the CHANGELOG promise "A view that assigns the attribute keeps its value" (CHANGELOG.md, Breaking,
"Card label-mode attribute"). Nothing errors or warns, so the regression is invisible. ViewSet-generated URLs call
`as_view()` without kwargs, so the impact is limited to hand-written URL confs and per-request assignment. It is
still a silent behaviour change on a path that worked before.
**Fix:** Read the instance in the render path and keep the classmethod for class-level callers:

```python
# cv_get_card_action_data
else:
    own = self.cv_card_actions_label_mode  # instance first: initkwargs / per-request assignment
    label_mode = own if own is not None else default_label_mode("card")
```

Or turn `cv_get_card_actions_label_mode` into an instance method (it has no class-level caller in `src/`). Add a
regression test that sets the attribute on an instance and through `as_view(**initkwargs)`.

## Warnings

### WR-01: Strict-mode "icon-only without icon" error points at the wrong fix for floor-driven buttons

**File:** `src/crud_views/lib/view/button_data.py:97-105`
**Issue:** Before this phase, cards could only become icon-only through an explicit `CardAction` or view attribute,
and the toolbar or row floor was fixed at "icon". Now `CRUD_VIEWS_LABEL_MODE_DEFAULTS` can set any location to
"icon". With `{"card": "icon"}` and a card action whose target has no `cv_icon_action` (for example a custom
`ActionView`), strict mode, the default under `DEBUG`, raises:

```
card action 'publish' renders icon-only but has no icon; give it an icon (...), or a label mode of 'label' or
'both' (ContextButton.label_mode or a label-mode map)
```

(confirmed with a probe). For a card button, neither `ContextButton.label_mode` nor a label-mode map has any effect.
Card modes come from `CardAction.label_mode`, `cv_card_actions_label_mode` or the floor setting. The message also
never names `CRUD_VIEWS_LABEL_MODE_DEFAULTS`, which is the actual cause. A developer following the hint cannot fix
the error.
**Fix:** Make the hint location-aware and name the floor:

```python
knobs = (
    "CardAction.label_mode, cv_card_actions_label_mode"
    if location == "card"
    else "ContextButton.label_mode or a label-mode map"
)
raise ValueError(
    f"{where} renders icon-only but has no icon; give it an icon (...), or a label mode of 'label' or 'both'"
    f" ({knobs}, or the {location!r} entry of CRUD_VIEWS_LABEL_MODE_DEFAULTS)"
)
```

### WR-02: No system check for icon-only buttons created by the card or list floor

**File:** `src/crud_views/lib/view/buttons.py:368-421`, `src/crud_views/lib/views/card.py:117-129`
**Issue:** W292 statically flags icon-only context keys whose target has no icon. Its resolution now includes the
context floor, so a setting change is covered there. The new card floor, and the list floor (now configurable), have
no equivalent check. `CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"card": "icon"}` passes `manage.py check` cleanly. Every
card action pointing to an icon-less target then raises at render in strict mode and logs a fallback warning
otherwise. Before this phase, cards defaulted to "both", so the setting opens a new route to a render-time
`ValueError` that only W292-style checking would catch early.
**Fix:** Add a W292-style check in `CardListView.checks()`. For each `CardAction`, resolve
`action.label_mode` → `no_label` → `cv_get_card_actions_label_mode()` the same way the render path does, with
`try/except ValueError` for an invalid strict floor, and warn when the result is "icon" and the target or child view
has no `cv_icon_action`. A list-row equivalent over `cv_list_actions` would close the same gap for
`{"list": "icon"}`.

### WR-03: 10-second subprocess timeouts are likely to flake under xdist or Windows CI

**File:** `tests/test1/test_button_data.py:425`, `tests/test1/test_import_safety.py:319`
**Issue:** Each test starts a fresh interpreter, imports Django, runs `django.setup()` and imports the crud_views
package, all within `timeout=10`. The suite is meant to run with `-n auto`, and CI includes Windows rows that already
have an unexplained subprocess flake (see project memory). A cold start under full parallel load can exceed 10 s.
The test then fails with `TimeoutExpired`, which looks like a deadlock that is not there.
`test_invalid_stamp_and_floor_recovers_without_deadlock` runs this four times. The other subprocess tests in
`test_import_safety.py` use no timeout at all.
**Fix:** A deadlock hangs forever, so any finite bound still detects it. Raise the bound to 60 s, or use a shared
constant such as `SUBPROCESS_TIMEOUT = 60`. The deadlock check can also run in-process with a thread and
`thread.join(timeout=5)` instead of a subprocess.

## Info

### IN-01: Warn-once register drops the stamp diagnostic when stamp and floor share a bad value

**File:** `src/crud_views/lib/view/label_mode.py:73-80`
**Issue:** Dedup is keyed by `(location, repr(value))` with no source (D-11). When a malformed stamp such as
`cv_label_mode="Both"` falls back to a floor that is also `"Both"`, the inner `default_label_mode` call registers
the pair first. Only the setting's warning is logged, and the `cv_label_mode` warning is permanently suppressed for
the process (confirmed with a probe). This is the documented design and E210/E211 cover most stamp sources
statically. A stamp from a custom `get_context()` or template context is covered by no check, though, so after the
setting is fixed it stays silent until restart.
**Fix:** If D-11 is revisited, key by `(source_kind, location, repr(value))` with `source_kind` in
`{"stamp", "setting"}`. That keeps the process-wide once guarantee per source.

### IN-02: E108 unknown-key message reports the value as what was "got"

**File:** `src/crud_views/lib/settings.py:157-172`
**Issue:** `{"cards": "both"}` produces `key 'cards' must be one of ['card', 'context', 'list'], got 'both'`. The
complaint is about the key, but "got" shows the valid mode, which reads as if `'both'` were the problem. The wording
is pinned by R-11 and by tests.
**Fix:** For the unknown-location branch, phrase it as `setting CRUD_VIEWS_LABEL_MODE_DEFAULTS has unknown key
'cards'; keys must be one of [...]`.

### IN-03: Mapping types other than dict are rejected, including MappingProxyType

**File:** `src/crud_views/lib/view/label_mode.py:100`, `src/crud_views/lib/settings.py:146`
**Issue:** `isinstance(raw, dict)` rejects `MappingProxyType`, the type the package itself uses for
`LABEL_MODE_DEFAULTS`. E108 fires, and at runtime strict mode raises while non-strict falls back. Confirmed: a
proxy holding `{"card": "label"}` yields E108 "must be a dict".
**Fix:** Accept `collections.abc.Mapping` in both places, or document that only a plain `dict` is accepted.

### IN-04: W292 guard catches every ValueError, not just the floor's

**File:** `src/crud_views/lib/view/buttons.py:407-410`
**Issue:** `try: cls.cv_get_action_label_mode(...) except ValueError: continue` hides any future `ValueError` raised
inside the resolver (for example from an overridden `cv_get_context_actions_label_mode`), not only the strict floor
error. The check would then silently skip the key.
**Fix:** Before the loop, check whether the floor is valid (for example a small `_floor_is_valid("context")` helper
that never raises). Skip only when it is invalid, and let other exceptions propagate.

### IN-05: LOCATIONS and LABEL_MODE_DEFAULTS are two sources of truth

**File:** `src/crud_views/lib/view/label_mode.py:23`, `src/crud_views/lib/view/button_data.py:12`
**Issue:** `default_label_mode` validates against `button_data.LOCATIONS` and then indexes `LABEL_MODE_DEFAULTS`. If
a location is added to `LOCATIONS` (the tests mention a Phase 6 "form" location) without a package default, the
result is a `KeyError` rather than the documented `ValueError`. E108 would also accept that key.
`test_defaults_match_locations` guards this, but `test_e108_uses_button_locations` monkeypatches `LOCATIONS` into
exactly that inconsistent state.
**Fix:** Derive one from the other, for example `LOCATIONS = frozenset(LABEL_MODE_DEFAULTS)`, or assert the
invariant at import.

### IN-06: Floor is read live but the label-mode maps are frozen at import

**File:** `src/crud_views/lib/settings.py:61-68`
**Issue:** `CRUD_VIEWS_LABEL_MODE_DEFAULTS` follows `override_settings`, but `CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE`
and `CRUD_VIEWS_LIST_ACTIONS_LABEL_MODE` are pydantic fields evaluated once. That is why the tests use
`override_settings` for one and `monkeypatch.setattr(crud_views_settings, ...)` for the others. The comment
documents this, but users and test authors will expect the four label-mode settings to behave the same way.
**Fix:** Document the difference in `docs/reference/settings.md`, or move the maps to call-time reads in a later
phase.

### IN-07: Some floor tests depend on the test app's default maps instead of clearing them

**File:** `tests/test1/test_context_action_label_mode.py:329-330`, `tests/test1/test_context_action_label_mode.py:420-433`
**Issue:** `_floor_case_unmapped` and `test_unmapped_context_key_reads_invalid_floor` assume that no view, ViewSet,
setting map or context button names `"update"` or `"delete"`. Unlike the render tests, they do not call
`_unmapped(monkeypatch)`. If the test app adds such a mapping, the tests fail in a way that does not point to the
cause.
**Fix:** Call `_unmapped(monkeypatch)` at the start of both.

---

_Reviewed: 2026-10-26T08:58:11Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
