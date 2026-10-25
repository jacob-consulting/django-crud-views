# Phase 1: Label-mode defaults - Pattern Map

**Mapped:** 2026-10-25
**Files analyzed:** 21 (8 source, 7 test, 6 docs/meta), all modified and none created
**Analogs found:** 21 / 21. Every change has an in-repo analog, most of them in the same file.

All paths below are git-tracked source under `src/` and `tests/`. There are no mirror paths.

## File Classification

| Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `src/crud_views/lib/view/label_mode.py` | utility (constant + accessor + signal receiver) | request-response (lazy settings read) | `src/crud_views/lib/button_classes.py:101-133` (lazy layered merge + `setting_changed` receiver) | exact |
| `src/crud_views/lib/view/button_data.py` | utility (leaf normaliser) | transform | same file `:88-101` (strict raise / log guard #264) | exact |
| `src/crud_views/lib/view/base.py` | model mixin (`CrudView` classmethods) | request-response | same file `:291-317` (literal replacement only) | exact |
| `src/crud_views/lib/views/card.py` | controller (`CardListView`) | request-response | same file `:102-105` `cv_get_card_actions_inline` classmethod resolver | exact |
| `src/crud_views/lib/view/card.py` | model (pydantic `CardAction`) | — (comment only) | same file `:12` | exact |
| `src/crud_views/lib/view/buttons.py` | check generator (W292) | batch (check time) | same file `:401-404` ("invalid value counts as unset") | exact |
| `src/crud_views/lib/settings.py` | config + system check (E108) | validation | same file `:98-132` (E105/E106 in `_action_settings_messages`) | exact |
| `tests/test1/test_label_mode.py` | test (unit) | — | same file + `tests/test1/test_button_data.py:238-288` (override_settings + caplog) | exact |
| `tests/test1/test_button_data.py` | test (unit) | — | same file `:88-92`, `:120-125`, `:245-253` | exact |
| `tests/test1/test_card_label_modes.py` | test (unit/check) | — | same file `:14-48` | exact |
| `tests/test1/test_action_label_mode_config.py` | test (settings check E108 + resolution) | — | same file `:37-47` (E106), `:66-75` | exact |
| `tests/test1/test_context_action_label_mode.py` | test (resolution + render) | — | same file `:47-90` | exact |
| `tests/test1/test_context_button_label_mode.py` | test (W292 no-crash) | — | same file `:161-185` (`_w292`) | exact |
| `tests/test1/test_card_label_mode_render.py` | test (render) | — | same file `:28-80` | exact |
| `docs/reference/settings.md` | docs | — | same file `:71-79` "## Action menus" table | exact |
| `docs/reference/action_menus.md` | docs | — | same file `:58-122` "## Label mode" + `:236-246` checks table | exact |
| `docs/reference/context_buttons.md` | docs (Mermaid) | — | same file `:251-262` | exact |
| `docs/reference/card-list-view.md` | docs | — | same file `:50`, `:67-78` | exact |
| `docs/reference/buttons.md` | docs | — | same file `:423-424` | exact |
| `docs/migrating-1.0.md` | docs | — | same file `:44-48` (checks list), `:127-129` (card recipe) | exact |
| `CHANGELOG.md` | docs | — | same file `:7` `### Breaking`, `:167-177` `### Added` | exact |
| `.planning/PROJECT.md` | planning meta | — | same file `:87-95` Key Decisions table | exact |

`AGENTS.md` already contains the Breaking→migrating rule at line 105 (`- Until 1.0.0 ships, a change that adds a ### Breaking entry ...`). The planner should verify that the rule is there and leave the file alone. No edit is needed.

---

## Pattern Assignments

### `src/crud_views/lib/view/label_mode.py` (utility, lazy settings read)

**Analog:** `src/crud_views/lib/button_classes.py`

**Current file imports** (lines 1-3). Keep these and add to them:
```python
from enum import StrEnum

from ..check import CheckExpression
```

**Imports to copy** (`button_classes.py:8,11-12`):
```python
from django.conf import settings
from django.core.signals import setting_changed
from django.dispatch import receiver
```
Add `import logging` + `logger = logging.getLogger(__name__)`, as `button_data.py:3,10` does. For the read-only constant, optionally add `from types import MappingProxyType` and `from collections.abc import Mapping` (RESEARCH A1).

**Cache-reset + receiver pattern** (`button_classes.py:103-114`). Copy its shape for `_warned` / `reset_label_mode_warnings()`:
```python
_button_classes_cache: dict[str, str | None] | None = None


def reset_button_classes_cache() -> None:
    global _button_classes_cache
    _button_classes_cache = None


@receiver(setting_changed)
def _on_setting_changed(sender, setting, **kwargs):
    if setting == "CRUD_VIEWS_BUTTON_CLASSES":
        reset_button_classes_cache()
```
Adaptation: `if setting in ("CRUD_VIEWS_LABEL_MODE_DEFAULTS", "CRUD_VIEWS_STRICT"): reset_label_mode_warnings()`. `_warned` is a `set` that gets cleared, so no `global` statement is needed.

**Lazy raw read** (`button_classes.py:123-124`):
```python
def _settings_layer() -> dict[str, str | None]:
    return getattr(settings, "CRUD_VIEWS_BUTTON_CLASSES", None) or {}
```
**Do not copy the `or {}` part.** D-03 requires that an explicit `None` stays visible to E108. Use a sentinel instead: `getattr(settings, "CRUD_VIEWS_LABEL_MODE_DEFAULTS", _UNSET)` (RESEARCH Pattern 1, lines 279-285).

**Per-key merge without mutating the defaults** (`button_classes.py:131`): `{**DEFAULT_BUTTON_CLASSES, **_THEME_BUTTON_CLASSES, **_settings_layer()}`. It builds a new dict, and the module constant is never touched (D-13).

**Location guard to copy verbatim** (`button_data.py:58-59`). It raises in every mode (D-12):
```python
if location not in LOCATIONS:
    raise ValueError(f"location must be one of {sorted(LOCATIONS)}, got {location!r}")
```
**Deferred import of LOCATIONS** (Pitfall 1: `button_data.py:8` imports this module). This is the same approach `button_classes.py` uses for its deferred `from .view.button_data import LOCATIONS` (around line 213):
```python
def default_label_mode(location: str) -> str:
    from .button_data import LOCATIONS  # deferred: button_data imports this module
```

**Strict switch** (`exceptions.py:32-36`). Import it inside the function body: `from ..exceptions import is_strict`. `exceptions.py` itself imports `django.conf` lazily, so a module-level import also works, but `button_data.py:6` already does `from ..exceptions import is_strict` at module level, so either form is fine.

**Existing message style to mirror** (`label_mode.py:34`): `f"{owner} label_mode must be one of {sorted(LABEL_MODES)}, got {value!r}{hint}"`.

**Full target sketch:** RESEARCH.md Pattern 1 (lines 266-314) and Pattern 2 (lines 320-331). Key the warn-once set by `(source, location, repr(value))` (Pitfall 3: `["both"]` is unhashable). The helper is semi-private (`_invalid_label_mode`) and imported by `button_data.py`.

---

### `src/crud_views/lib/view/button_data.py` (utility, transform)

**Analog:** the same file's icon-less guard.

**Import line to extend** (line 8):
```python
from .label_mode import LABEL_MODES, is_label_mode
```
→ add `default_label_mode, _invalid_label_mode` (whatever name the planner pins). `LABEL_MODES` may become unused after this change; ruff `F401` flags it then.

**Lines to replace** (82-85):
```python
    # cards default to both; context and list to icon, unless the view stamped a mode for the key (#216)
    label_mode = ctx.get("cv_label_mode") or ("both" if card else "icon")
    if not is_label_mode(label_mode):
        raise ValueError(f"cv_label_mode must be one of {sorted(LABEL_MODES)}, got {label_mode!r}")
```
**Strict/log model to follow** (lines 88-101):
```python
    if kind == "action" and label_mode == "icon" and not ctx.get("cv_icon_action"):
        where = f"{location} action {ctx.get('cv_action_key') or ctx.get('cv_key', '')!r}"
        if is_strict():
            raise ValueError(...)
        if label:
            label_mode = "label"
            logger.warning("%s has no icon; rendered with its label instead", where)
```
Target (RESEARCH lines 335-337): keep the `or`, which treats an empty string as unset, so the goldens do not change. The strict-mode message must still contain the substring `cv_label_mode`, because `test_button_data.py:124` uses `match="cv_label_mode"`. Leave the `cv_no_label` raise at `:62-66` untouched (D-10).

---

### `src/crud_views/lib/view/base.py` (CrudView classmethods)

**Analog:** the same method. Only literals and docstrings change.

Lines 312 and 317, to be replaced with `default_label_mode("context")` / `default_label_mode("list")`:
```python
            return target_default or "icon"            # :312
        ...
        return mapping.get(key, "icon")                # :317
```
For `:317` use `mapping[key] if key in mapping else default_label_mode("list")`, or `mapping.get(key) or default_label_mode("list")`. Do not use `mapping.get(key, default_label_mode("list"))`: the default argument is evaluated eagerly, so the accessor would run, and could warn, even when the key is mapped. That matters for D-11 log noise and for the strict raise.

Docstrings to reword (the acceptance grep does not catch these, but they are in scope):
- `:282` `"""Row action key -> label mode; keys not named are "icon" (#216)."""`
- `:287` `... keys not named fall to the target view's default (#269)."""`
- `:294` `"""The label mode of one configured context or list action key; "icon" when nothing names it (#216).`

Import: `base.py` lives in `lib/view/`, so add `from .label_mode import default_label_mode` next to its other relative imports. Read the top of `base.py` to find the right position in the import block.

---

### `src/crud_views/lib/views/card.py` (controller, CardListView)

**Analog:** `cv_get_card_actions_inline` in the same file (lines 102-105):
```python
    @classmethod
    def cv_get_card_actions_inline(cls):
        """Card action keys (CardAction.key, or child_name) kept as buttons; None: no menu (#174)."""
        return cls.cv_first_inline_keys(cls.cv_card_actions_inline, "card_actions_inline")
```
→ New sibling `cv_get_card_actions_label_mode(cls) -> str` (RESEARCH Pattern 3, lines 343-351).

**Imports** (line 11), to extend:
```python
from crud_views.lib.view.label_mode import label_mode_check
```
→ add `default_label_mode`. This file uses absolute `crud_views.lib...` imports, so follow that style.

**Attribute** (line 28): `cv_card_actions_label_mode: str = "both"  # view default ... (#213)` → `str | None = None` plus a comment that `None` means the defaults map.

**Resolution branch** (lines 46-52). Only the `else` changes: `label_mode = self.cv_get_card_actions_label_mode()`. Keep the `no_label` → `"icon"` branch at `:50` (D-18). Update the comment at `:46`.

**Check** (line 112). Use the conditional-yield pattern from the same method, lines 117-118:
```python
            if action.label_mode is not None:
                yield label_mode_check(cls, owner, action.label_mode)
```
→ `if cls.cv_card_actions_label_mode is not None: yield label_mode_check(cls, "cv_card_actions_label_mode", cls.cv_card_actions_label_mode)`.

---

### `src/crud_views/lib/view/card.py` (CardAction model, comment only)

Line 12: `label_mode: str | None = None  # None: the view's cv_card_actions_label_mode; one of LABEL_MODES`. Append "then CRUD_VIEWS_LABEL_MODE_DEFAULTS['card']" and stay within 120 columns.

---

### `src/crud_views/lib/view/buttons.py` (W292 check generator)

**Analog:** the same block, lines 401-406:
```python
        # the target view's own toolbar mode (#269); an invalid value counts as unset, viewset.E210 reports it
        target_default = target_cls.cv_context_action_label_mode
        if not is_label_mode(target_default):
            target_default = None
        if cls.cv_get_action_label_mode("context", key, button, target_default) != "icon":
            continue
```
Pitfall 2: in strict mode a bad floor makes `cv_get_action_label_mode` raise, and that kills `check_viewsets` (`checks.py:20-28`) before E108 is shown. Wrap the call in the same style:
```python
        try:
            mode = cls.cv_get_action_label_mode("context", key, button, target_default)
        except ValueError:
            continue  # an invalid floor is reported by crud_views.E108
        if mode != "icon":
            continue
```
The early-return guards at `:377-380` (`# viewset.E211 / crud_views.E106 report it`) are the comment style to match.

---

### `src/crud_views/lib/settings.py` (config + E108)

**Analog:** E106 in the same method, lines 98-132. The deferred import pattern is at lines 100-102:
```python
        # deferred imports: settings.py must not import the view package at module level
        from crud_views.lib.view.action_menu import cv_is_inline_keys
        from crud_views.lib.view.label_mode import LABEL_MODES, is_label_mode_map
```
**E106 message to mirror** (lines 122-131):
```python
            if not isinstance(value, dict) or not is_label_mode_map(value):
                messages.append(
                    Error(
                        id="crud_views.E106",
                        msg=(
                            f"setting {setting} must be a dict of action key -> one of {sorted(LABEL_MODES)}, "
                            f"got {value!r}"
                        ),
                    )
                )
        return messages
```
E108 goes before the `return messages` at line 132 and reads `_raw_label_mode_defaults()`, not a Pydantic field (D-13, STACK.md). Full body: RESEARCH Pattern 4 (lines 356-374). Add `from crud_views.lib.view.button_data import LOCATIONS` and `is_label_mode`, `_UNSET`, `_raw_label_mode_defaults` to the deferred imports.

**Do not add** a field like `label_mode_defaults: Any = from_settings(...)`. The `from_settings` fields at lines 61-66 are import-time snapshots (Anti-pattern, Pitfall 6). Do update the comment at `:61-64` ("keys not named are "icon"" → "keys not named fall to CRUD_VIEWS_LABEL_MODE_DEFAULTS"). If you want discoverability, add a short comment near those lines saying that `CRUD_VIEWS_LABEL_MODE_DEFAULTS` is read lazily in `view/label_mode.py`.

---

### `tests/test1/test_label_mode.py` (unit)

**Analog imports and parametrize style** (lines 1-21):
```python
import pytest

from crud_views.lib.view.label_mode import LABEL_MODES, LabelMode, is_label_mode, label_mode_check


@pytest.mark.parametrize("value", ["label", "icon", "both"])
def test_is_label_mode_true(value):
    assert is_label_mode(value) is True
```
**override_settings + caplog + strict pattern** (`test_button_data.py:4`, `:240-253`):
```python
from django.test import override_settings

def test_icon_mode_without_icon_raises_strict(location, icon):
    with override_settings(CRUD_VIEWS_STRICT=True), pytest.raises(ValueError, match=r"'detail'.*icon"):
        ...

def test_icon_mode_without_icon_falls_back_to_label(location, icon, caplog):
    with override_settings(CRUD_VIEWS_STRICT=False):
        data = ...
    assert "'detail'" in caplog.text
```
New tests to add here:
- `set(LABEL_MODE_DEFAULTS) == LOCATIONS` (D-02);
- the merge keeps unnamed keys;
- `LABEL_MODE_DEFAULTS` is not mutated;
- an unknown location raises in both modes (D-12);
- a bad mode raises in strict mode, and in non-strict mode returns the package default and warns once (a second call adds no log record, Pitfall 5);
- an unhashable value such as `["both"]` works;
- an explicit `None` setting is handled.

The suite runs with `CRUD_VIEWS_STRICT=True` (`conftest.py:27-29`), so non-strict tests must wrap themselves in `override_settings(CRUD_VIEWS_STRICT=False, CRUD_VIEWS_LABEL_MODE_DEFAULTS=...)`.

---

### `tests/test1/test_button_data.py` (unit)

**Analogs to extend:**
- `:88-92` `test_card_label_mode_defaults_to_both`: add an `override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"card": "label"})` variant, which also covers the LMOD-04 "override_settings, not monkeypatch" requirement.
- `:120-125` `test_unknown_cv_label_mode_raises_everywhere`: keep it. It runs strict and still raises with `match="cv_label_mode"`. Add a non-strict twin that asserts the fallback to `default_label_mode(location)` and a single warning (D-10).
- The fixture helper `base(**kw)` at `:12-25` and `LOCATIONS = ["context", "list", "card"]` at `:9` are reused as they are.

---

### `tests/test1/test_card_label_modes.py` (unit/check)

**Analog:** the same file. These tests must change:
```python
def test_default_is_both():                                         # :14-15, rewrite (Pitfall 4)
    assert CardListView.cv_card_actions_label_mode == "both"
```
→ the attribute is `None`, `CardListView.cv_get_card_actions_label_mode() == "both"`, and under `override_settings({"card": "label"})` it returns `"label"`. With an explicit `"both"` attribute plus `{"card": "label"}`, the result is `"both"` (D-14).

`:38-48` `test_good_values_yield_no_check`: extend the `for mode in (...)` tuple with `None`. Keep the `monkeypatch.setattr(AuthorCardListView, ...)` + `e210(...)` helper pattern (`:10-11`).

---

### `tests/test1/test_action_label_mode_config.py` (settings check E108 + resolution)

**Analog for E106** (lines 37-47):
```python
@pytest.mark.parametrize("field", ["context_actions_label_mode", "list_actions_label_mode"])
@pytest.mark.parametrize("value", [None, ["create"], "both", {"create": "text"}, {1: "both"}])
def test_invalid_setting_e106(field, value):
    messages = CrudViewsSettings(**{field: value}).check_messages
    assert [m.id for m in messages] == ["crud_views.E106"]
    assert f"CRUD_VIEWS_{field.upper()}" in messages[0].msg
```
E108 differs because it reads django settings, not kwargs. Use `with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS=value): messages = CrudViewsSettings().check_messages`. Cases to cover:
- `None`, `"both"` and `["x"]`, each giving one message;
- `{"cotext": "both"}`, `{"form": "both"}`, `{1: "both"}`, `{"card": "nope"}` and `{"context": {"filter": "both"}}`;
- two bad entries, giving two messages (D-04);
- unset, or `{"card": "label"}`, giving `[]`.

Pin the exact unknown-key wording here (RESEARCH Open Question 2).

**Resolution analog** (lines 66-75): `test_default_resolves_to_empty_and_icon` / `test_setting_is_last_fallback`. Add `override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"list": "both"})` → `AuthorListView.cv_get_action_label_mode("list", "update") == "both"`, while a mapped key still wins.

---

### `tests/test1/test_context_action_label_mode.py` (resolution + render)

**Analog:** lines 47-49:
```python
def test_target_default_used_when_nothing_else_names_key():
    assert AuthorDetailView.cv_get_action_label_mode("context", "update", target_default="label") == "label"
    assert AuthorDetailView.cv_get_action_label_mode("context", "update") == "icon"
```
Add tests for these points:
- `{"context": "both"}` moves the unmapped floor to `"both"`, and `target_default="icon"` still beats it (Pitfall 6).
- A render test for success criterion 1 (toolbar shows icon+text, rows unchanged). It reuses `_client`, `_detail_url`, `_toolbar`, `_rows` and `_has_icon_and_text` imported at `:23-41` from `test_action_label_mode_render.py`.

---

### `tests/test1/test_context_button_label_mode.py` (W292)

**Analog** (lines 161-185):
```python
def _w292(view=AuthorDetailView):
    return _messages(view.checks(), W292)

def test_w292_silent_with_button_label_mode(monkeypatch):
    monkeypatch.setattr(_target("update"), "cv_icon_action", None)
    ...
    assert _w292() == []
```
Add two tests:
1. With `{"context": "both"}` and an icon-less target, `_w292() == []`.
2. With `override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"context": "nope"}, CRUD_VIEWS_STRICT=True)`, listing `AuthorDetailView.checks()` messages does not raise (Pitfall 2).

---

### `tests/test1/test_card_label_mode_render.py` (render)

**Analog helpers** (lines 28-64): `_client(grants)`, `_card(client, url)`, `_inline(card, key)`, `_icons`, `_text`, `_author_card(client, actions, monkeypatch)`; `@pytest.mark.django_db` with the `author_douglas_adams` fixture. Add a test for `override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"card": "label"})`: a `CardAction(key="detail", label="Details")` with no `label_mode` renders text with no `<i>`.

---

### Docs (D-24, D-25, D-16, D-17)

| File | Analog excerpt (verbatim) | Change |
|---|---|---|
| `docs/reference/settings.md:73-79` | `\| CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE \| Label mode per context toolbar action key (...); keys not named are \`icon\`, ... Invalid values raise \`crud_views.E106\`. \| \`dict[str, str]\` \| \`{}\` \|` | Add a `CRUD_VIEWS_LABEL_MODE_DEFAULTS` row in the same 4-column shape (it ends "Invalid values raise `crud_views.E108`."). Below the rows, add the "merge or replace / layer / keys" table (D-24). Reword "keys not named are `icon`" in line 78. |
| `docs/reference/action_menus.md:58-90` | `Any key not named is "icon", so an empty dict is today's markup` (line 70); `then the target view's cv_context_action_label_mode, then "icon"` (lines 83-84) | Replace `"icon"` with a link to the defaults map. Add one canonical `### Resolution order` section per location (context/list/card) with a stable anchor before other pages link to it (Pitfall 7). Add a `crud_views.E108` row to the checks table at `:238-246`, shaped like the E106 row: `\| \`crud_views.E106\` \| a \`CRUD_VIEWS_*_ACTIONS_LABEL_MODE\` setting is not a dict ... \|`. The `cv_context_actions_label_mode` / `cv_context_action_label_mode` table at `:117-120` is already in place (D-19). |
| `docs/reference/context_buttons.md:256` | `M4 -- "no" --> MICON["icon"]` | Change only the node label, e.g. `MICON["defaults map<br/>CRUD_VIEWS_LABEL_MODE_DEFAULTS['context']<br/>(default icon)"]`. Keep the id `MICON`, which is referenced at `:262` and in the class list. Add a prose link to the action_menus section under the diagram. |
| `docs/reference/card-list-view.md:50,71,73-78` | `\| \`cv_card_actions_label_mode\` \| \`str\` \| \`"both"\` \| Label mode of every card action ... \|`; `The order is CardAction.label_mode, then "icon" when no_label=True, then cv_card_actions_label_mode.` | Change the type to `str \| None`, the default to `None`, and document `cv_get_card_actions_label_mode()`. Replace the restated order with a link (D-25). In the tip at `:77-78`, list the setting `{"card": ...}` first. |
| `docs/reference/buttons.md:423-424` | `a card shows icon and text with CardListView.cv_card_actions_label_mode = "both" (the default)` | Reword to say the default comes from `CRUD_VIEWS_LABEL_MODE_DEFAULTS["card"]` (`"both"`). |
| `docs/migrating-1.0.md:127-129` | `To get the 0.29 label-only buttons back, set cv_card_actions_label_mode = "label" on the card view, or CardAction(label_mode="label") on one button` | Put the setting first (D-17), then the per-view setting, then the per-button setting. Add a Breaking bullet in the same `- **...**` style as `:124-126`: the attribute now reads `None` and the resolver should be used. Also append `crud_views.E108` to the checks list at `:44-48`. |
| `CHANGELOG.md:7` `### Breaking` / `:167` `### Added` | Added style (`:173-177`): `` - `cv_context_action_label_mode` (`"label"`, `"icon"` or `"both"`; `None` by default) on a view sets ... An invalid value fails `viewset.E210`; ...`` | Add one Breaking bullet (attribute → `None`, rendering unchanged) and one Added bullet (setting, `default_label_mode`, `LABEL_MODE_DEFAULTS` read-only, `cv_get_card_actions_label_mode()`, E108). Add a Fixed bullet for the D-10 production crash (`### Fixed` is at `:136`). |
| `.planning/PROJECT.md:89-95` | `\| Label-mode defaults are a project-wide floor, not per-ViewSet/view \| Per-ViewSet/view knobs already exist \| — Pending \|` | Add D-19 (keep the label-mode pair names, frozen; LATER-02 won't rename) and D-20 (`no_label` removed before 1.0, LATER-01) rows with the same 3 columns. |

---

## Shared Patterns

### Strict raise / non-strict log
**Source:** `src/crud_views/lib/exceptions.py:32-36` + `src/crud_views/lib/view/button_data.py:88-101`
**Apply to:** `default_label_mode` (D-09), the bad stamped `cv_label_mode` in `cv_button_data` (D-10)
```python
def is_strict() -> bool:
    from django.conf import settings
    return bool(getattr(settings, "CRUD_VIEWS_STRICT", settings.DEBUG))
```
Logging: create `logger = logging.getLogger(__name__)` at module level and use the `logger.warning("%s ...", arg)` %-style. Do not use f-strings in log calls (`button_data.py:99`).

### Lazy setting + `setting_changed` invalidation
**Source:** `src/crud_views/lib/button_classes.py:103-133`
**Apply to:** `label_mode.py` (the warn-once set; an optional merged-map cache). Tests rely on `override_settings` firing `setting_changed` on enter and exit.

### Deferred imports to break cycles
**Source:** `src/crud_views/lib/settings.py:100-102` (`# deferred imports: settings.py must not import the view package at module level`) and `button_classes.py` (deferred `from .view.button_data import LOCATIONS`)
**Apply to:** `label_mode.default_label_mode` (imports `LOCATIONS`) and E108 in `settings.py`.

### "Invalid counts as unset; the check reports it"
**Source:** `src/crud_views/lib/view/buttons.py:377-380`, `:401-404`
**Apply to:** the W292 `try/except ValueError` (Pitfall 2), with the comment `# ... crud_views.E108 reports it`.

### Check-message wording
**Source:** `settings.py:127-128` (`f"setting {setting} must be a dict of action key -> one of {sorted(LABEL_MODES)}, got {value!r}"`) and `label_mode.py:34`
**Apply to:** every E108 message. Use `sorted(...)` for the allowed set and `!r` for the value, with no hint (D-05).

### Classmethod `cv_get_*` resolvers
**Source:** `src/crud_views/lib/views/card.py:102-105`, `src/crud_views/lib/view/base.py:280-288`
**Apply to:** `CardListView.cv_get_card_actions_label_mode()`.

### Test conventions
- The suite runs strict (`tests/test1/conftest.py:27-29`: `DEBUG=True`, `CRUD_VIEWS_STRICT=True`).
- Use `override_settings` (from `django.test`) for setting-driven behaviour.
- Use `monkeypatch.setattr` for class attributes and Pydantic settings fields (`test_action_label_mode_config.py:72-88`).
- The xdist + random-order plugins mean warn-once state must be reset through the receiver or `reset_label_mode_warnings()` (Pitfall 5).
- Golden tests must stay unchanged. Never run them with `CV_UPDATE_GOLDEN=1`.

## No Analog Found

None. Every new symbol extends an existing module, and its pattern is in the same file or a sibling.

| File | Role | Data Flow | Reason |
|---|---|---|---|
| — | — | — | — |

## Metadata

**Analog search scope:** `src/crud_views/lib/{view,views}/`, `src/crud_views/lib/{settings,exceptions,button_classes}.py`, `src/crud_views/checks.py`, `tests/test1/`, `docs/`, `CHANGELOG.md`, `.planning/PROJECT.md`, `AGENTS.md`
**Files scanned:** 24
**Pattern extraction date:** 2026-10-25
