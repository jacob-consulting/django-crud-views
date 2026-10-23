# Context Button Label Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `ContextButton.label_mode` sets a toolbar button's label mode, and an icon-mode action button with an
empty icon is reported by a check, raises under strict mode, and renders as a text button otherwise.

**Architecture:** One strict-mode helper shared with `ignore_exception`; the button step added inside the existing
`cv_get_action_label_mode()` (so the render path and the check share one precedence); the guard at the end of the
mode resolution in `cv_button_data()`; `E210` for the field in `context_button_checks()`; a new view-level warning
`W292` next to `cv_label_mode_checks()`.

**Tech Stack:** Django, Pydantic, pytest + pytest-django (+ xdist), lxml.

**Spec:** `superpowers/specs/2026-10-23-context-button-label-mode-design.md` (issue #264)

## Global Constraints

- Precedence for a context key, first match wins: the view's own `cv_context_actions_label_mode` if set **and naming
  the key** → the button's `label_mode` → today's resolution (first non-`None` map of view → ViewSet → setting,
  by key, `"icon"` if not named).
- `location="list"` never reads the button's `label_mode`.
- "Empty icon" means `cv_icon_action` is `None` or `""`, nothing else.
- Strict means `getattr(settings, "CRUD_VIEWS_STRICT", settings.DEBUG)`, read at call time.
- With no button `label_mode` set and every icon-mode button having an icon, output is byte-for-byte unchanged;
  goldens under `tests/test1/golden/` are never regenerated in this work.
- Menu items (`kind="menu-item"`) are not touched by the guard.
- CHANGELOG: Added (`ContextButton.label_mode`, `viewset.W292`), Changed (the guard). No `### Breaking`;
  `docs/migrating-1.0.md` not touched.
- Never name downstream / client projects in code, docs, changelog or tests.
- Python 3.12+, line length 120, double quotes, ruff. Run tests with `pytest tests -n auto`.

## Review Focus

- A view map that is set but does not name the key must not hide the button's mode, and without a button mode must
  still give `"icon"` (no fall-through to the ViewSet map) → Task 2 `test_view_map_without_key_yields_to_button`,
  `test_view_map_without_key_and_no_button_mode_is_icon`.
- A toolbar key whose button says `"label"` but that also appears in `cv_list_actions` must render as the list maps
  say in rows → Task 2 `test_button_label_mode_does_not_reach_rows`.
- `cv_icon_action = ""` (not only `None`) triggers the guard and `W292` → Task 3 / Task 4 parametrised over
  `[None, ""]`.
- Empty label and empty icon together: strict raises, non-strict stays `"icon"` and logs → Task 3
  `test_empty_label_and_icon`.
- A key folded into the action menu must not get `W292` → Task 4 `test_w292_skips_menu_folded_key`.

---

### Task 1: Strict on in the test suite, one strict helper

**Files:**
- Modify: `src/crud_views/lib/exceptions.py` (helper; `ignore_exception` uses it)
- Modify: `tests/test1/conftest.py` (add `CRUD_VIEWS_STRICT=True` next to `DEBUG=True`, line ~27)
- Modify: `docs/reference/settings.md` (new `CRUD_VIEWS_STRICT` entry)
- Modify: tests that break (see Step 3)
- Test: `tests/test1/test_strict_mode.py`

**Interfaces:**
- Produces: `is_strict() -> bool` in `crud_views.lib.exceptions`.

- [ ] **Step 1: Write the failing test** in `tests/test1/test_strict_mode.py`

```python
from crud_views.lib.exceptions import is_strict

def test_is_strict_follows_setting_then_debug():
    with override_settings(CRUD_VIEWS_STRICT=False, DEBUG=True):
        assert is_strict() is False
    with override_settings(CRUD_VIEWS_STRICT=True, DEBUG=False):
        assert is_strict() is True

def test_suite_runs_strict():
    from django.conf import settings
    assert settings.CRUD_VIEWS_STRICT is True
```

The two existing `test_strict_defaults_*` tests take pytest-django's `settings` fixture and run
`del settings.CRUD_VIEWS_STRICT` first, so they still prove the `DEBUG` default once the suite sets strict on.

- [ ] **Step 2:** Run `pytest tests/test1/test_strict_mode.py -v`. Expected: FAIL (`is_strict` not defined).

- [ ] **Step 3: Implement** `is_strict()` (`bool(getattr(settings, "CRUD_VIEWS_STRICT", settings.DEBUG))`), use it in
  `ignore_exception`, set `CRUD_VIEWS_STRICT=True` in the conftest. Run `pytest tests -n auto`. For each new failure:
  a real misconfiguration in the test project → fix it; a test that deliberately exercises the quiet path → pin it
  with `override_settings(CRUD_VIEWS_STRICT=False)`. Record every one (test id, cause, fix) for the acceptance
  report.

- [ ] **Step 4:** `pytest tests -n auto` → all pass.

- [ ] **Step 5: Docs.** `docs/reference/settings.md`: `CRUD_VIEWS_STRICT` — when true, misconfigurations that are
  otherwise logged and skipped raise (unresolved keys in tags, and from Task 3 icon-mode buttons without an icon);
  default `DEBUG`; set it to `True` in test settings, because pytest-django runs tests with `DEBUG=False`.

- [ ] **Step 6: Commit** `test: run the suite in strict mode; is_strict() helper (#264)`

### Task 2: `ContextButton.label_mode`, precedence and E210

**Files:**
- Modify: `src/crud_views/lib/view/buttons.py` (field; `context_button_checks()`)
- Modify: `src/crud_views/lib/view/base.py:278-290` (`cv_get_action_label_mode`), `:507` (`cv_get_context_button`)
- Modify: `docs/reference/context_buttons.md`, `docs/reference/action_menus.md` (#label-mode),
  `docs/reference/buttons.md` (E210 row wording), `CHANGELOG.md` (Added)
- Test: `tests/test1/test_context_button_label_mode.py` (new)

**Interfaces:**
- Consumes: nothing from Task 1.
- Produces:
  - `ContextButton.label_mode: str | None = None` (comment: `# None: the view's context label-mode maps; one of
    LABEL_MODES (#264)`)
  - `CrudView.cv_get_context_button(cls, key: str) -> ContextButton | None` becomes a `@classmethod` (same lookup:
    view `cv_context_buttons`, then ViewSet `context_buttons`).
  - `CrudView.cv_get_action_label_mode(cls, location, key) -> str`: signature unchanged; for `"context"` applies the
    Global Constraints precedence. `cv_get_context()` keeps calling it, so the toolbar, the menu split and
    `{% cv_context_button %}` follow without further change.

- [ ] **Step 1: Write the failing tests** (monkeypatch style of `test_action_label_mode_render.py`; buttons via
  `monkeypatch.setattr(AuthorDetailView, "cv_context_buttons", [...])` or a `cv_author.model_copy`):

```python
def test_button_label_mode_wins_over_viewset_map():          # ViewSet map {"update": "icon"}, button "label" → "label"
def test_view_map_naming_key_beats_button():                 # view map {"update": "both"}, button "label" → "both"
def test_view_map_without_key_yields_to_button():            # view map {"detail": "both"}, button on "update" "label" → "label"
def test_view_map_without_key_and_no_button_mode_is_icon():  # view map {"detail": "both"}, ViewSet {"update": "label"} → "icon"
def test_no_button_mode_unchanged():                         # existing #216 results, button label_mode None
def test_view_level_button_beats_viewset_button():           # both define key, only view-level sets "both" → "both"
def test_list_location_ignores_button():                     # cv_get_action_label_mode("list", key) unaffected
def test_toolbar_renders_button_mode():                      # GET detail page; toolbar <a cv-key="update"> has <span>label</span>, no hidden-label span
def test_button_label_mode_does_not_reach_rows():            # list page, button "label" on "detail"; row button still hidden-label
def test_cv_context_button_tag_follows_button():             # {% cv_context_button "update" %} renders text
def test_e210_invalid_button_label_mode():                   # ContextButton(..., label_mode="text") → viewset.E210 at ViewSet and view level, msg names "context button 'update'"
def test_e210_on_default_button():                           # ContextButton(key="home", key_target="list", label_mode="text") still checked
```

- [ ] **Step 2:** `pytest tests/test1/test_context_button_label_mode.py -v` → FAIL.

- [ ] **Step 3: Implement.** Field; `@classmethod` on `cv_get_context_button`; in `cv_get_action_label_mode` for
  `"context"`: view map step, then `cls.cv_get_context_button(key)` and its `label_mode`, then the existing mapping
  lookup. In `context_button_checks()`, next to `variant_check` and before the `button in defaults` skip:
  `if button.label_mode is not None: yield label_mode_check(context, f"context button {button.key!r}", button.label_mode)`.

- [ ] **Step 4:** `pytest tests -n auto` → all pass, goldens unchanged.

- [ ] **Step 5: Docs.** `context_buttons.md`: the field, the precedence, one sentence "applies to the toolbar, the
  action menu and `{% cv_context_button %}`, not to row actions, which follow the list maps". `action_menus.md`
  label-mode section: the button as step 2 for context keys. `buttons.md` checks table: E210 also covers
  `ContextButton.label_mode`. `CHANGELOG.md` Added: `ContextButton.label_mode` (#264).

- [ ] **Step 6: Commit** `feat(buttons): label mode per context button (#264)`

### Task 3: Render-time guard in `cv_button_data()`

**Files:**
- Modify: `src/crud_views/lib/view/button_data.py` (after the "empty label forces icon" rule, ~line 82)
- Modify: `docs/reference/buttons.md` (`cv_label_mode` row of the leaf table), `docs/reference/action_menus.md`
  (one paragraph), `CHANGELOG.md` (Changed)
- Test: `tests/test1/test_button_data.py`

**Interfaces:**
- Consumes: `is_strict()` (Task 1).
- Produces: no new names. Module-level `logger = logging.getLogger(__name__)` in `button_data.py`.

- [ ] **Step 1: Write the failing tests** (use the file's `base()` helper):

```python
@pytest.mark.parametrize("location", LOCATIONS)
@pytest.mark.parametrize("icon", [None, ""])
def test_icon_mode_without_icon_raises_strict(location, icon):
    with override_settings(CRUD_VIEWS_STRICT=True), pytest.raises(ValueError, match=r"detail.*icon"):
        cv_button_data(base(cv_icon_action=icon, cv_label_mode="icon"), location)

@pytest.mark.parametrize("location", LOCATIONS)
@pytest.mark.parametrize("icon", [None, ""])
def test_icon_mode_without_icon_falls_back_to_label(location, icon, caplog):
    with override_settings(CRUD_VIEWS_STRICT=False):
        data = cv_button_data(base(cv_icon_action=icon, cv_label_mode="icon"), location)
    assert data["cv_label_mode"] == "label"
    assert "cv_title" not in data
    assert data["cv_label"] == "Detail"  # short label off-card; on cards the short label comes first too
    assert "detail" in caplog.text

def test_menu_item_without_icon_untouched():   # kind="menu-item", strict on → no raise, mode as before
def test_icon_present_unchanged():             # strict on, icon "detail" → "icon"
def test_label_and_both_without_icon_untouched():  # "label" / "both" with icon None → no raise, unchanged

@pytest.mark.parametrize("strict", [True, False])
def test_empty_label_and_icon(strict, caplog):  # cv_action_label "" + icon None: strict raises; else mode "icon" + log
```

Card note: card context without `cv_label_mode` defaults to `"both"`, so the card cases pass `cv_label_mode="icon"`
explicitly.

- [ ] **Step 2:** `pytest tests/test1/test_button_data.py -v` → new tests FAIL.

- [ ] **Step 3: Implement.** For `kind == "action"` only, when the mode is `"icon"` and `ctx.get("cv_icon_action")` is
  falsy: if `is_strict()` raise `ValueError` with a message naming location, key and the remedy ("give the action an
  icon, or a label mode of 'label' or 'both' (ContextButton.label_mode or a label-mode map)"); else, if a label
  exists, set the mode to `"label"` (and re-apply the short-label rule for non-card), log a warning with key and
  location; if no label, keep `"icon"` and log.

- [ ] **Step 4:** `pytest tests -n auto`. Test-project views with no icon in icon mode now raise (strict is on
  suite-wide, Task 1). For each: give the test view an icon or a label mode, unless the test is about exactly that.
  Record each for the acceptance report. All pass, goldens unchanged.

- [ ] **Step 5: Docs + CHANGELOG.** `buttons.md` leaf table `cv_label_mode` row: "an `"icon"` mode with an empty
  icon raises under `CRUD_VIEWS_STRICT`, otherwise renders as `"label"` and logs a warning". Same rule in one
  paragraph in `action_menus.md#label-mode`, linking the settings entry. `CHANGELOG.md` Changed: the rule, plus
  "pytest-django runs with `DEBUG=False`; set `CRUD_VIEWS_STRICT = True` in test settings so such buttons fail
  tests" (#264).

- [ ] **Step 6: Commit** `feat(buttons): no invisible icon-mode buttons (#264)`

### Task 4: System check `viewset.W292`

**Files:**
- Modify: `src/crud_views/lib/view/action_menu.py` (new check function next to `cv_label_mode_checks`)
- Modify: `src/crud_views/lib/view/base.py:178` (call it after the context `cv_label_mode_checks`)
- Modify: `docs/reference/buttons.md` (checks table), wherever the docs list all check ids (grep `W291`),
  `CHANGELOG.md` (Added)
- Test: `tests/test1/test_context_button_label_mode.py`

**Interfaces:**
- Consumes: `cv_get_action_label_mode`, `cv_get_context_button` (Task 2); `_is_registered`,
  `ContextButton._resolve_container_key`, `ContextButton.get_context` (buttons.py).
- Produces: `cv_icon_mode_checks(cls) -> Iterator[Check]`, one `CheckWarningExpression(id="W292")` per offending
  context key.

Static rule per key in `cls.cv_context_actions` (skip, i.e. yield nothing, on any "skip"):
1. mode `cls.cv_get_action_label_mode("context", key)` is not `"icon"` → skip;
2. `inline = cls.cv_get_context_actions_inline()`; `inline is not None and key not in inline` → skip (folds into the
   menu);
3. button `cls.cv_get_context_button(key)`: if present and (`type(button).get_context is not
   ContextButton.get_context`, or `button.template`, or `button.template_code`, or `button.key_target is None`) →
   skip; target = `_resolve_container_key(viewset, button.key_target)`; without a button, target = `key`;
4. `not _is_registered(viewset, target)` → skip;
5. icon = `viewset.get_view_class(target).cv_icon_action`; warn when `not icon`.

Message: `f"context action {key!r} of {cls.__name__} renders icon-only but has no icon; give it an icon or a label
mode ('label' or 'both')"`.

- [ ] **Step 1: Write the failing tests** (collect
  `[m for c in View.checks() for m in c.messages() if m.id == "viewset.W292"]`, as `test_context_button_check.py` does
  for `viewset.E255`):

```python
@pytest.mark.parametrize("icon", [None, ""])
def test_w292_key_without_button(monkeypatch, icon):       # AuthorUpdateView.cv_icon_action = icon; AuthorDetailView has "update" → 1 warning naming 'update'
def test_w292_plain_button_target_without_icon(monkeypatch):  # ContextButton(key="edit", key_target="update"), target icon None → warning
def test_w292_silent_with_button_label_mode(monkeypatch):     # same, label_mode="label" → none
def test_w292_silent_with_map(monkeypatch):                   # same, view map {"update": "both"} → none
def test_w292_silent_with_icon():                              # stock AuthorDetailView → none
def test_w292_skips_menu_folded_key(monkeypatch):             # cv_context_actions_inline=["detail"], "update" icon None → none
def test_w292_skips_custom_template_button(monkeypatch):      # ContextButton(..., template_code="x") → none
def test_w292_skips_get_context_override(monkeypatch):        # ParentContextButton / FilterContextButton → none
def test_w292_skips_unregistered_target(monkeypatch):         # key not registered → none (no crash)
```

- [ ] **Step 2:** run the new tests → FAIL.

- [ ] **Step 3: Implement** `cv_icon_mode_checks` and call it from `CrudView.checks()` inside
  `if cls.cv_viewset is not None:`. Confirm `W292` is unused (`grep -rn W292 src docs`).

- [ ] **Step 4:** `pytest tests -n auto` → all pass. If an existing "no warnings on the test project" test now sees
  `W292`, fix the test-project view (icon or label mode) and record it.

- [ ] **Step 5: Docs + CHANGELOG.** `buttons.md` checks table row: `viewset.W292` | warning | a context toolbar key
  resolves to `"icon"` while its target view has no `cv_icon_action` (keys in the action menu, buttons with their own
  template and buttons overriding `get_context()` are not checked; the render-time rule covers them). Add W292 to any
  other check list found by grep. `CHANGELOG.md` Added: `viewset.W292` (#264).

- [ ] **Step 6: Commit** `feat(checks): viewset.W292 for icon-only toolbar buttons without an icon (#264)`

### Task 5: Acceptance report

**Files:**
- Create: `superpowers/notes/2026-10-23-context-button-label-mode-acceptance.md`

- [ ] **Step 1:** `task check && task format` clean; `pytest tests -n auto` all pass; `git diff main --stat -- tests/test1/golden` empty.
- [ ] **Step 2:** Write the report: each spec goal → the test(s) that prove it; every test-project fix and every
  test pinned to `CRUD_VIEWS_STRICT=False` from Tasks 1, 3 and 4, with its cause.
- [ ] **Step 3: Commit** `docs: acceptance note for #264`
