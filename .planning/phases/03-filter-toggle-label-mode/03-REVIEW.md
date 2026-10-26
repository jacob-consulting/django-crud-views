---
phase: 03-filter-toggle-label-mode
reviewed: 2026-10-26T16:14:31Z
depth: deep
files_reviewed: 16
files_reviewed_list:
  - CHANGELOG.md
  - docs/migrating-1.0.md
  - docs/reference/action_menus.md
  - docs/reference/buttons.md
  - docs/reference/context_buttons.md
  - docs/reference/icons.md
  - docs/reference/javascript.md
  - src/crud_views/lib/view/buttons.py
  - src/crud_views/locale/de/LC_MESSAGES/django.po
  - src/crud_views/templates/crud_views/tags/context_action_filter.html
  - tests/js/list.filter.test.js
  - tests/test1/test_button_leaves.py
  - tests/test1/test_context_action_label_mode.py
  - tests/test1/test_filter_toggle_label_mode.py
  - tests/test1/test_i18n.py
  - tests/test1/test_label_mode_docs.py
findings:
  critical: 0
  warning: 2
  info: 4
  total: 6
status: issues_found
---

# Phase 03: Code Review Report

**Reviewed:** 2026-10-26T16:14:31Z
**Depth:** deep
**Files Reviewed:** 16
**Status:** issues_found

## Summary

Scope: the phase's product change is small — `FilterContextButton.get_context()` now stamps `cv_label_mode` and a
translated default label, and `tags/context_action_filter.html` branches on that mode — surrounded by a large test
and documentation surface. The review traced the full render path across modules: `FilterContextButton.get_context()`
→ `CrudView._cv_get_action_context()` → `CrudView.cv_get_context()` (the pipeline stamp) → `cv_context_action` /
`cv_context_action_group` → `_render_context_action()` → the leaf, and compared it with the stock leaf path through
`cv_button_data()`.

Verified independently: the full Python suite (3457 passed, 1 skipped, `-n auto`), the JS suite (36 passed),
`mkdocs build --strict`, `ruff check` and `ruff format --check` all pass; `tests/test1/golden/` and
`list.filter.js` are byte-identical to the diff base; every doc anchor the new sections link to exists; the German
catalog entry is present, non-fuzzy, compiled into `django.mo`, and the `.po` location comment
(`lib/view/buttons.py:330`) matches the source; `string_if_invalid` cannot leak into the leaf because every
`{% if %}` on an undefined variable resolves to `None` in Django's if-evaluation; label escaping is covered by
`test_filter_label_escaping`. No security issue was found: the only new rendered inputs are the translated label
(autoescaped) and host class strings from trusted settings.

Two warnings remain. Both come from the filter toggle living outside the stock-leaf pipeline: its label mode is
resolved twice by two different call sites that merely happen to agree today, and the strict-mode guarantee for a
malformed stamped `cv_label_mode` that the stock leaf enforces (and the CHANGELOG promises) does not hold for the
filter leaf. The tests pin both behaviours instead of catching them.

## Narrative Findings (AI reviewer)

## Warnings

### WR-01: `cv_label_mode` is resolved and stamped twice on every filter render, by two call sites that only coincidentally agree

**File:** `src/crud_views/lib/view/buttons.py:329` and `src/crud_views/lib/view/base.py:642-645`
**Issue:** `FilterContextButton.get_context()` stamps
`data["cv_label_mode"] = context.view.cv_get_action_label_mode("context", self.key, self)`. The result then flows
back into `CrudView.cv_get_context()`, which unconditionally re-resolves
`self.cv_get_action_label_mode(location, key, button, data.get("cv_context_label_mode"))` and overwrites the key
with `{**data, "cv_label_mode": mode, ...}`. The leaf therefore renders the pipeline's value while
`_apply_label()` (which runs inside `get_context()`, before the overwrite) rendered any `label_template` with the
button's value. The two agree today only because three independent facts line up: `_cv_find_context_button(key)`
returns the same instance as `self`, the configured key equals `self.key`, and the filter data never carries
`cv_context_label_mode` (it does not go through `cv_get_dict()`), so the pipeline's `target_default` is `None`.
None of those is asserted anywhere; a `FilterContextButton` subclass that overrides `get_context()` to merge
`cls.cv_get_dict()` (as the other four button classes do) would silently pick up the list view's
`cv_context_action_label_mode` in the pipeline stamp while the label template still saw the D-01 resolution, and
`test_filter_ignores_list_singular_default` would not notice because it reads the direct `get_context()` value and
the rendered body — both of which it would still pass for the stock class. Side effects today: with an invalid
`CRUD_VIEWS_LABEL_MODE_DEFAULTS["context"]` the floor resolver runs twice per toggle (raise-twice in strict mode,
once-deduplicated warning otherwise), and the filter is now the only button whose `label_template` can read
`cv_label_mode` (`cv_get_dict()` at `base.py:431-450` does not seed it for ordinary buttons) — a contract that
`test_filter_customization` pins (`"{{ cv_label_mode }}:{{ cv_key }}"` → `"label:filter"`) but no reference page
documents.
**Fix:** Resolve once. Either let the pipeline honour a mode a button has already stamped, so the leaf and the label
template are guaranteed to see the same value:

```python
# base.py, cv_get_context()
if location is not None and data:
    if "cv_label_mode" in data:  # a button that resolved its own mode (FilterContextButton, #262)
        mode = data["cv_label_mode"]
    else:
        button = self.cv_get_context_button(key) if location == "context" else None
        mode = self.cv_get_action_label_mode(location, key, button, data.get("cv_context_label_mode"))
    data = {**data, "cv_label_mode": mode, "cv_action_key": key}
```

and add a test that patches `CrudView.cv_get_action_label_mode` to count calls during one toolbar render of the
publisher list (expect one call for the filter key). Then either document in `context_buttons.md#the-filter-toggle`
that the filter's `label_template` receives `cv_label_mode`, or drop that assertion from `test_filter_customization`
so it does not become an accidental public contract.

### WR-02: A malformed stamped `cv_label_mode` is silently rendered as the icon form, in strict mode too, contradicting the documented strict-mode policy

**File:** `src/crud_views/templates/crud_views/tags/context_action_filter.html:3,7,11,13`; `src/crud_views/lib/view/buttons.py:329`; `CHANGELOG.md:153-155`
**Issue:** The stock leaf path validates the stamped mode in `cv_button_data()` (`button_data.py:85-91`): a value
outside `LABEL_MODES` raises `ValueError` under `CRUD_VIEWS_STRICT` and otherwise logs once and falls back to the
floor. The CHANGELOG entry just above this phase's entry states that contract for "a malformed truthy
`cv_label_mode` on a button context" — "strict mode still raises `ValueError` naming `cv_label_mode`". The filter
toggle never passes through `cv_button_data()`: `_render_context_action()` (`templatetags/crud_views.py:178-184`)
renders its `cv_template` directly, and the leaf's branches (`!= "label"`, `== "both" or == "label"`,
`!= "both" and != "label"`) classify any unknown value as the icon body with `context:<variant>:icon`. So
`{"filter": "text"}` (or `"Label"`, a capitalisation typo) reaching render time produces no error in strict mode,
no warning in non-strict mode, and a hidden-label icon button whose `title`/tooltip the author never asked for.
`test_filter_invalid_configuration_policy` asserts exactly this (`_rendered_mode(...) == "icon"` after
`_select_settings_map(monkeypatch, {"filter": "text"})`) and calls it "a limitation, not a supported
configuration"; `buttons.md` now documents it as behaviour ("A mode it does not know renders the icon form"). The
startup checks (E210/E211/E106, pydantic on the ViewSet map) cover the four static configuration paths, but they
are bypassed by `SILENCED_SYSTEM_CHECKS`, by maps mutated after startup, by a direct `get_context()` caller, and by
`manage.py` commands run with `--skip-checks` — the same gap `cv_button_data()` was given its runtime guard for.
**Fix:** Apply the existing policy at the stamp, so the filter and the stock leaves agree in every mode:

```python
# buttons.py, FilterContextButton.get_context()
from .label_mode import LABEL_MODES, _invalid_label_mode, default_label_mode, is_label_mode  # expose _invalid_label_mode or add a public wrapper

mode = context.view.cv_get_action_label_mode("context", self.key, self)
if not is_label_mode(mode):
    mode = _invalid_label_mode(
        f"context action {self.key!r} cv_label_mode must be one of {sorted(LABEL_MODES)}",
        "context",
        mode,
        lambda: default_label_mode("context"),
    )
data["cv_label_mode"] = mode
```

Update `test_filter_invalid_configuration_policy` to expect `ValueError` in strict mode and a single warning plus
the floor otherwise (mirroring the stock-leaf test for the "Malformed stamped label modes" entry), and replace the
`buttons.md` sentence "A mode it does not know renders the icon form with `context:<variant>:icon`" with a pointer
to the strict/warn-once policy. The leaf's own `{% else %}` fallback can stay for hand-built contexts without a mode.

## Info

### IN-01: The leaf spells the same three-way mode decision five different ways

**File:** `src/crud_views/templates/crud_views/tags/context_action_filter.html:1,3,7,11,13`
**Issue:** Line 1 tests `!= "label"`, line 3 `== "both" or == "label"` with an `{% else %}`, line 7
`!= "both" and != "label"`, line 11 `!= "label"` again, line 13 `== "both"` / `elif == "label"` / `else`. Every
future change to the mode set (or to which modes are icon-bearing) must be applied to all five places in the right
polarity; a miss produces a mixed body (e.g. a `title` on a visible-label button) that only a matrix test catches.
**Fix:** Once WR-02 guarantees the stamped value is one of three modes, collapse the branches to one shape per
site, e.g. `{% if cv_label_mode == "label" %}…{% elif cv_label_mode == "both" %}…{% else %}…{% endif %}`, so the
icon body is always the `{% else %}` (which also keeps the mode-less compatibility path), and compute the two host
classes once at the top under the same `{% if cv_label_mode != "label" %}` that line 11 reuses.

### IN-02: CHANGELOG sentence reads as if `FilterContextButton(label_mode="label")` selects `"icon"`

**File:** `CHANGELOG.md:157-159`
**Issue:** "`CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE = {"filter": "both"}`, a ViewSet or view map, or
`FilterContextButton(label_mode="label")` selects `"icon"` (unchanged markup …), `"both"` (…) or `"label"` (…)"
— the two concrete examples carry their own mode values, so the list of three modes that follows contradicts them
on first read.
**Fix:** Split the sentence: name the configuration surfaces first ("The mode comes from
`CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE`, a ViewSet or view map, or `FilterContextButton(label_mode=...)`"), then
list the three modes and what each renders, and keep the `{"filter": "both"}` example as a separate example line.

### IN-03: Catalog test reaches into `GNUTranslations._catalog`

**File:** `tests/test1/test_i18n.py:109-111`
**Issue:** `compiled._catalog` is a private CPython attribute of `gettext.GNUTranslations`; the test matrix runs
Python 3.12–3.15 and the attribute is not part of the documented API, so a rename would fail this test for a reason
unrelated to the catalog. The comment explains why `gettext()` alone cannot prove membership (identical msgstr), so
the intent is right.
**Fix:** Parse the compiled file with the already-imported `polib`:
`assert polib.mofile(str(CORE_DE / "django.mo")).find("Filter") is not None`, which is public API and proves the
same thing.

### IN-04: `FilterContextButton` is now a documented configuration surface but is not re-exported with its siblings

**File:** `docs/reference/context_buttons.md:552`; `src/crud_views/lib/view/__init__.py`
**Issue:** The new contract tells users to write `from crud_views.lib.view.buttons import FilterContextButton
# not re-exported by crud_views.lib.view`, while `ContextButton`, `ParentContextButton` and `ChildContextButton` are
imported from `crud_views.lib.view` one line above. `test_filter_toggle_reference_contract` pins the absence from
`__all__`, which turns an API gap into a tested contract. The phase summary records this as deliberately scoped out.
**Fix:** Either add the re-export (and drop the `not in __all__` assertion) in the follow-up already noted in
`deferred-items.md`, or keep the comment but do not assert the gap in the docs test so adding the export later does
not break an unrelated test.

---

_Reviewed: 2026-10-26T16:14:31Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
