# Phase 1: Label-mode defaults - Research

**Researched:** 2026-10-25
**Domain:** Django settings resolution, system checks and button label-mode resolution inside `crud_views` (in-repo only)
**Confidence:** HIGH. Every in-repo literal below was read this session. No external package is involved.

## Summary

The phase is code and docs inside the repo, with no new dependencies. The package lives under `src/` (`src/crud_views/lib/...`), so the acceptance grep path `src/crud_views/lib/view/*.py` is correct [VERIFIED: `ls src` → `crud_views crud_views_guardian ...`]. All literals and line numbers cited in CONTEXT.md match the source:
- `button_data.py:83`
- `base.py:312`, `:317`
- `views/card.py:28/46-52/112`
- `buttons.py:405`
- `settings.py:61-66/98-132`

There are three planning hazards that CONTEXT.md does not cover:
1. **Circular import.** `label_mode.py` would need `LOCATIONS` from `button_data.py`, but `button_data.py` already imports `label_mode.py`.
2. **Strict raise during system checks.** W292 calls `cv_get_action_label_mode()` at check time. If the accessor raises in strict mode (dev default `DEBUG=True`), a bad setting crashes `check_viewsets` before E108 is ever shown.
3. **Unhashable values.** A "warn once" seen-set keyed on the raw value raises `TypeError` for `["both"]`, and the existing tests already use `["both"]` as a bad value.

**Primary recommendation:** Put `LABEL_MODE_DEFAULTS`, `label_mode_defaults()` (lazy, called on every use) and `default_label_mode()` in `label_mode.py`. Import `LOCATIONS` inside the function. Key the warn-once set by `(source, location, repr(value))` and clear it from a `setting_changed` receiver. Make W292 tolerate a `ValueError` coming from the floor. Change the three literal sites and the card attribute in one atomic task, then handle the docs and CHANGELOG.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Read and merge `CRUD_VIEWS_LABEL_MODE_DEFAULTS` | Backend (Python, `lib/view/label_mode.py`) | — | Settings are read lazily at call time (D-13) |
| Floor per location (context/list) | Backend (`CrudView.cv_get_action_label_mode`, `base.py:291-317`) | — | Stamps `cv_label_mode` before the template runs |
| Floor for cards | Backend (`CardListView.cv_get_card_actions_label_mode`, new) | — | Stamps `cv_label_mode` on every card action |
| Leaf fallback / bad stamped mode | Backend (`cv_button_data`, `button_data.py:83-85`) | — | Last fallback for raw `{% cv_button %}` contexts |
| Validation | Django system checks (`settings.py` `_action_settings_messages`) | — | E108 runs next to E105 and E106 |
| Rendering | Templates (`tags/button/action.html`) | — | **Unchanged.** They only branch on the stamped `cv_label_mode` |

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### E108: setting validation
- **D-01:** `crud_views.E108` is an **Error** both for an unknown location key and for an invalid mode value. There is
  no Warning tier and no new W-ID. A typo must fail loudly. The cost is accepted: a setting written for a newer
  minor version fails on an older one. — **Reversibility:** one-way — projects put check IDs in
  `SILENCED_SYSTEM_CHECKS`, and Phase 7 freezes the ID and its severity.
- **D-02:** Valid keys are **derived from `LOCATIONS`** (`button_data.py:12`), never from a literal. `"form"` is **not**
  accepted in Phase 1. Phase 6 adds `"form"` to `LOCATIONS`, and E108 then accepts it automatically. Between Phase 1
  and Phase 6, `{"form": ...}` fails E108. Add a test pinning `set(LABEL_MODE_DEFAULTS) == LOCATIONS`, so that the
  package map and the location set cannot drift. (Phase 2/1C may split `LOCATIONS` into explicit sets. E108 must
  follow the button-data / label-mode location set, not the class-key `VARIANT_LOCATIONS` set.)
- **D-03:** A non-dict value is reported under E108. This includes `None`, a string or a list. There is no special case
  for `None`: an unset setting means the package defaults, but an explicit `None` is invalid. This mirrors how E106
  treats the label-mode maps.
- **D-04:** E108 emits **one message per bad entry**, naming the key and the value. A non-dict value gives one message
  for the whole setting.
- **D-05:** Use the **E106/E210 message wording** and no hint. Example shape: `setting CRUD_VIEWS_LABEL_MODE_DEFAULTS key
  'cotext' must be one of ['card', 'context', 'list'], got ...` and `... key 'card' must be one of ['both', 'icon',
  'label'], got ...`. No did-you-mean hint.
- **D-06:** A nested dict value (e.g. `{"context": {"filter": "both"}}`) is an invalid mode. Nested per-key forms are
  not supported, because the per-key maps already exist.
- **D-07:** E108 goes into `CrudViewsSettings._action_settings_messages` (`settings.py:98-132`) next to E105/E106,
  with deferred imports (settings.py must not import the view package at module level). E108 reads the raw setting
  the same lazy way the accessor does.

#### Runtime fallback for bad modes (LMOD-05)
- **D-08:** If the setting holds an invalid mode for a location, `default_label_mode(location)` falls back to the
  **package default for that location** (`LABEL_MODE_DEFAULTS[location]`), never to the setting itself. An unknown
  key in the setting is ignored at render.
- **D-09:** **Strict mode raises, otherwise log and fall back.** This is the same rule as the icon-less guard (#264):
  `is_strict()` (`CRUD_VIEWS_STRICT`, defaults to `DEBUG`) raises `ValueError` at render. Non-strict logs a warning and
  falls back.
- **D-10:** LMOD-05 **also fixes the existing crash** in `cv_button_data` (`button_data.py:84-85`), where a bad stamped
  `cv_label_mode` raises `ValueError` even in production. It follows the same strict/log rule. In non-strict mode it
  falls back to `default_label_mode(location)`, the configured floor. The `cv_no_label` ValueError (`:62-66`) stays as
  it is.
- **D-11:** The fallback warning is logged **once per process per bad `(location, value)` pair**, not on every render
  (renders are hot paths). The mechanism is the agent's choice (see Discretion).
- **D-12:** `default_label_mode(location)` **raises `ValueError` in every mode** for a location outside `LOCATIONS`. A
  wrong location argument is a caller bug, not configuration. This matches `cv_button_data`'s existing contract
  (`:58-59`).
- **D-13 (locked by STATE.md/research):** The setting is read **lazily at call time** from `django.conf.settings`, not
  as an import-time Pydantic snapshot, so `override_settings` works (LMOD-04). At least one test must use
  `override_settings`, not monkeypatch. Never mutate `LABEL_MODE_DEFAULTS` when merging.

#### Card view default becomes `None` (LMOD-03)
- **D-14:** `CardListView.cv_card_actions_label_mode: str | None = None`. `None` means "the defaults map". Resolution
  order: `CardAction.label_mode` → `CardAction.no_label` (`"icon"`) → view attribute (if not None) →
  `default_label_mode("card")`. An explicitly set `"both"` still wins over `{"card": "label"}`. E210 on the attribute
  (`card.py:112`) must accept `None`. Fix the type in the code, the docs (`card-list-view.md:71`) and the check
  together.
- **D-15:** Add a **public resolver `cv_get_card_actions_label_mode()`**. It returns the attribute if it is set,
  otherwise `default_label_mode("card")`. `cv_get_card_action_data` uses it. The docs point subclasses and templates
  to this method or to the stamped `cv_label_mode`, never to the raw attribute. — **Reversibility:** one-way — new
  public API that Phase 7 freezes.
- **D-16:** The CHANGELOG gets a **`### Breaking` entry** (code reading the attribute now gets `None`; the rendered
  output is unchanged) plus a bullet in `docs/migrating-1.0.md`, per the AGENTS.md rule. It also gets an `Added` entry
  for the setting, the accessor, the resolver and E108.
- **D-17:** In the `docs/migrating-1.0.md` recipe "restore the 0.29 card look", the **setting comes first**
  (`CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"card": "label"}`). `cv_card_actions_label_mode = "label"` (per view) and
  `CardAction(label_mode="label")` (per button) follow as the finer alternatives.
- **D-18:** `CardAction.no_label` stays **untouched** in Phase 1. It keeps its place in the chain and still maps to
  `"icon"`, with no DeprecationWarning. Removal is LATER-01.

#### Names that Phase 7 will freeze
- **D-19:** The `cv_context_actions_label_mode` (per-key dict) / `cv_context_action_label_mode` (target-view default
  string) pair **keeps its names and is frozen as stable**. LATER-02 closes as "won't rename". The Phase 1 docs make
  the distinction clear wherever both names appear. — **Reversibility:** one-way — Phase 7 freezes both names at 1.0.0.
- **D-20:** `CardAction.no_label` / the `cv_no_label` guard is **removed before 1.0** (LATER-01, outside this phase).
  Phase 7 lists it as "deprecated, removed in 1.0.0", never as stable.
- **D-21:** All new Phase 1 names are **public**: the setting `CRUD_VIEWS_LABEL_MODE_DEFAULTS`,
  `default_label_mode(location)`, `LABEL_MODE_DEFAULTS` (documented as read-only) and
  `CardListView.cv_get_card_actions_label_mode()`. — **Reversibility:** one-way — semver surface at 1.0.0.
- **D-22:** The setting name is confirmed as **`CRUD_VIEWS_LABEL_MODE_DEFAULTS`**.
- **D-23:** Record D-19 and D-20 in the PROJECT.md Key Decisions table during this phase, so that Phase 7 finds them
  as decided (PITFALLS: "Decision recorded in PROJECT.md Key Decisions before Phase 4").

#### Docs placement
- **D-24:** **One table in `docs/reference/settings.md`** with one row per label-mode knob and the columns "merge or
  replace", "layer" and "keys". The rows are: `CRUD_VIEWS_LABEL_MODE_DEFAULTS` (per-key merge over the package
  defaults), `CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE` / `CRUD_VIEWS_LIST_ACTIONS_LABEL_MODE` and the ViewSet/view maps
  (whole replacement per layer), and the card attribute. `action_menus.md` and `card-list-view.md` link to it. Phase 6
  adds the form row. The docs state explicitly that the existing maps' semantics do not change.
- **D-25:** **One canonical resolution-order section** per location (context / list / card) in
  `docs/reference/action_menus.md`. The Mermaid `MICON["icon"]` node in `docs/reference/context_buttons.md` (not
  `action_menus.md` as the plan says) becomes "defaults map" and links to that section. Other pages link instead of
  restating the order.
- **D-26:** The example project stays **untouched** in Phase 1.

### Claude's Discretion
- How "log once per bad (location, value)" is implemented (e.g. a module-level seen-set, `functools.lru_cache` on a
  warn helper, or a cache cleared by a `setting_changed` receiver). It must stay correct under `override_settings` in
  tests.
- Whether the merged map is computed per call or cached behind a `setting_changed` receiver (as
  `reset_button_classes_cache()` does). Either is fine as long as D-13 holds.
- Exact test file split among the files the plan names.

### Deferred Ideas (OUT OF SCOPE)
- Removing `CardAction.no_label` / the `cv_no_label` guard: LATER-01, decided "remove before 1.0" (D-20), outside
  this phase.
- LATER-02 (rename of the label-mode pair): decided "won't rename" (D-19). Nothing to implement.
- A did-you-mean hint for E108 unknown keys was considered and rejected (D-05).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| LMOD-01 | `CRUD_VIEWS_LABEL_MODE_DEFAULTS`, merged per key over `{"context": "icon", "list": "icon", "card": "both"}`; docs state per-key merge vs whole replacement | Pattern 1 (lazy merge); Docs map (settings.md table at the "Action menus" section, lines 71-79) |
| LMOD-02 | `default_label_mode(location)` is the single floor used by `cv_button_data`, `cv_get_action_label_mode`, `CardListView`; no literals remain | Integration-points table; acceptance grep verified against the current matches |
| LMOD-03 | Card attribute defaults to `None`; explicit `"both"` wins; `{"card": "label"}` restores the 0.29 look | Pattern 3 (resolver); Pitfall 4 (existing test asserts `"both"`) |
| LMOD-04 | Read at call time; `override_settings` works | Pattern 1; Pitfall 5 (no Pydantic field) |
| LMOD-05 | Invalid mode outside strict logs and falls back | Pattern 2 (warn-once); Pitfalls 2, 3 |
| LMOD-06 | E108 for unknown key or invalid mode; keys derived from `LOCATIONS` | Pattern 4 (E108); Pitfall 1 (circular import) |
</phase_requirements>

## Project Constraints (from AGENTS.md)

- All `CrudView` class attributes use the `cv_` prefix. The new resolver `cv_get_card_actions_label_mode` follows the `cv_get_*` convention.
- Line length is 120 and the quote style is double quotes (ruff). Pre-commit runs `ruff-format`.
- Until 1.0.0, a change that adds a `### Breaking` entry to `CHANGELOG.md` also updates `docs/migrating-1.0.md`. This applies to D-16.
- Tests live in `tests/test1/`. Fixture naming is `cv_<model>`, `user_<model>_<perm>`, `client_user_<model>_<perm>`.
- Settings live in `crud_views/lib/settings.py` with the `CRUD_VIEWS_*` prefix. This phase reads its new setting lazily outside the Pydantic model (D-13). That is an intentional, documented exception.
- Global constraints (plan §"Global constraints"):
  - goldens stay byte-identical;
  - `pytest tests -n auto`, vitest, `mkdocs build --strict`, `ruff check`, `ruff format --check` are green before push;
  - no downstream project names in any file;
  - the Tabler follow-up goes in the acceptance note, not in this repo.

## Standard Stack

No new packages. Existing in-repo building blocks:

| Component | Location | Purpose |
|-----------|----------|---------|
| `LabelMode`, `LABEL_MODES`, `is_label_mode`, `label_mode_check` | `src/crud_views/lib/view/label_mode.py:6-35` | Home of the new constant and accessor |
| `is_strict()` | `src/crud_views/lib/exceptions.py:32-36` | Strict/log switch |
| Lazy merge + `setting_changed` receiver | `src/crud_views/lib/button_classes.py:103-133` | Pattern to copy |
| E105/E106 | `src/crud_views/lib/settings.py:98-132` | Where E108 goes |
| Golden harness | `tests/test1/test_action_menus_golden.py` (+ 5 other golden tests) | Byte-identical guard |

## Package Legitimacy Audit

Not applicable: this phase installs no external packages.

## Verified In-Repo Literals (source of truth, read this session)

- `src/crud_views/lib/view/button_data.py:12`: `LOCATIONS = frozenset({"context", "list", "card"})` [VERIFIED]
- `button_data.py:8`: `from .label_mode import LABEL_MODES, is_label_mode`. This module imports label_mode, so label_mode must not import button_data at module level. [VERIFIED]
- `button_data.py:82-85` [VERIFIED]:
  ```python
  # cards default to both; context and list to icon, unless the view stamped a mode for the key (#216)
  label_mode = ctx.get("cv_label_mode") or ("both" if card else "icon")
  if not is_label_mode(label_mode):
      raise ValueError(f"cv_label_mode must be one of {sorted(LABEL_MODES)}, got {label_mode!r}")
  ```
- `button_data.py:58-59`: `if location not in LOCATIONS: raise ValueError(f"location must be one of {sorted(LOCATIONS)}, got {location!r}")` [VERIFIED]
- `button_data.py:88-101`: the icon-less guard. It uses `if is_strict(): raise ValueError(...)` and otherwise `logger.warning(...)`, with `logger = logging.getLogger(__name__)` at `:10`. [VERIFIED]
- `src/crud_views/lib/view/base.py:282`: `"""Row action key -> label mode; keys not named are "icon" (#216)."""` [VERIFIED]
- `base.py:287`: `"""Context toolbar action key -> label mode (#216); keys not named fall to the target view's default (#269)."""` [VERIFIED]
- `base.py:294`: `"""The label mode of one configured context or list action key; "icon" when nothing names it (#216).` [VERIFIED]
- `base.py:312`: `return target_default or "icon"` [VERIFIED]
- `base.py:313-317` [VERIFIED]:
  ```python
  elif location == "list":
      mapping = cls.cv_get_list_actions_label_mode()
  else:
      raise ValueError(f"location must be 'context' or 'list', got {location!r}")
  return mapping.get(key, "icon")
  ```
- `base.py:631`: `mode = self.cv_get_action_label_mode(location, key, button, data.get("cv_context_label_mode"))`. Every context/list button built through `cv_get_context(location=...)` gets a stamped mode. [VERIFIED]
- `src/crud_views/lib/views/card.py:28`: `cv_card_actions_label_mode: str = "both"  # view default for CardAction.label_mode: label, icon or both (#213)` [VERIFIED]
- `views/card.py:46-52` [VERIFIED]:
  ```python
  if action.label_mode is not None:
      label_mode = action.label_mode
  elif action.no_label:
      label_mode = "icon"
  else:
      label_mode = self.cv_card_actions_label_mode
  ```
- `views/card.py:102-105`: `cv_get_card_actions_inline` is a `@classmethod`. That is the sibling pattern for the new resolver. [VERIFIED]
- `views/card.py:112`: `yield label_mode_check(cls, "cv_card_actions_label_mode", cls.cv_card_actions_label_mode)` [VERIFIED]
- `src/crud_views/lib/view/card.py:12`: `label_mode: str | None = None  # None: the view's cv_card_actions_label_mode; one of LABEL_MODES`. Update the comment ("then the defaults map"). [VERIFIED]
- `src/crud_views/lib/view/buttons.py:400-405` [VERIFIED]:
  ```python
  # the target view's own toolbar mode (#269); an invalid value counts as unset, viewset.E210 reports it
  target_default = target_cls.cv_context_action_label_mode
  if not is_label_mode(target_default):
      target_default = None
  if cls.cv_get_action_label_mode("context", key, button, target_default) != "icon":
  ```
- `src/crud_views/lib/settings.py:61-66` [VERIFIED]: the comment `keys not named are "icon"` and `context_actions_label_mode: Any = from_settings("CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE", default={})`
- `settings.py:117-131`: E106 message `f"setting {setting} must be a dict of action key -> one of {sorted(LABEL_MODES)}, got {value!r}"` [VERIFIED]
- `src/crud_views/lib/exceptions.py:32-36`: `return bool(getattr(settings, "CRUD_VIEWS_STRICT", settings.DEBUG))` [VERIFIED]
- `src/crud_views/lib/button_classes.py:111-114`: `@receiver(setting_changed) def _on_setting_changed(sender, setting, **kwargs): if setting == "CRUD_VIEWS_BUTTON_CLASSES": reset_button_classes_cache()` [VERIFIED]
- `src/crud_views/checks.py:20-28` [VERIFIED]: `check_viewsets` runs `errors = crud_views_settings.check_messages` first, then iterates `ViewSet.checks_all()` in the **same function**. An exception in the W292 generator therefore discards E108.
- `tests/test1/conftest.py:27-29` [VERIFIED]: `DEBUG=True,` and `CRUD_VIEWS_STRICT=True,`. The test suite runs strict, so non-strict tests need `override_settings(CRUD_VIEWS_STRICT=False)`.

**Current acceptance-grep matches** (all must disappear) [VERIFIED: grep]: `button_data.py:83`, `base.py:312`, `base.py:317`. Hits that are *not* in the grep but are in scope: `views/card.py:28` (`= "both"`). Leave `views/card.py:50` (`no_label` → `"icon"`) as it is (D-18).

**Templates:** no template in `src/` or in the local Tabler checkout (`../tabler-test/crud_views_tabler`) reads `cv_card_actions_label_mode` [VERIFIED: grep, empty]. `tags/button/action.html:8` reads only the stamped `cv_label_mode`. The Tabler acceptance note can say "no template change needed".

## Architecture Patterns

### Data flow

```
settings.CRUD_VIEWS_LABEL_MODE_DEFAULTS (raw, read on each call)
        │
        ▼
label_mode_defaults()  ── {**LABEL_MODE_DEFAULTS, **valid entries} ──► default_label_mode(location)
        │                                                    │  bad entry: strict → ValueError
        │                                                    │             non-strict → warn once, package default
        ▼                                                    ▼
E108 (settings._action_settings_messages)        ┌──────────┼───────────────────────────┐
                                                 ▼          ▼                           ▼
                           cv_get_action_label_mode   CardListView.                cv_button_data
                           (context/list floor,       cv_get_card_actions_         (leaf fallback when no
                            base.py:312/317)          label_mode() → stamped        cv_label_mode stamped;
                                 │                    cv_label_mode                 bad stamped mode → D-10)
                                 ▼
                  cv_get_context(location=…) stamps cv_label_mode ──► leaf template (unchanged)
                  cv_icon_mode_checks / W292 (check time)
```

### Pattern 1: Lazy per-key merge (LMOD-01/04)
```python
# src/crud_views/lib/view/label_mode.py (additions)
import logging

from django.conf import settings
from django.core.signals import setting_changed
from django.dispatch import receiver

logger = logging.getLogger(__name__)

# read-only package floor; Phase 6 adds "form"
LABEL_MODE_DEFAULTS: Mapping[str, str] = MappingProxyType({"context": "icon", "list": "icon", "card": "both"})

_UNSET = object()
_warned: set[tuple[str, str, str]] = set()


def _raw_label_mode_defaults():
    """The raw setting, _UNSET when absent (an explicit None is invalid, D-03)."""
    return getattr(settings, "CRUD_VIEWS_LABEL_MODE_DEFAULTS", _UNSET)


def reset_label_mode_warnings() -> None:
    _warned.clear()


@receiver(setting_changed)
def _on_setting_changed(sender, setting, **kwargs):
    if setting in ("CRUD_VIEWS_LABEL_MODE_DEFAULTS", "CRUD_VIEWS_STRICT"):
        reset_label_mode_warnings()


def default_label_mode(location: str) -> str:
    from .button_data import LOCATIONS  # deferred: button_data imports this module

    if location not in LOCATIONS:
        raise ValueError(f"location must be one of {sorted(LOCATIONS)}, got {location!r}")
    raw = _raw_label_mode_defaults()
    if raw is _UNSET:
        return LABEL_MODE_DEFAULTS[location]
    if not isinstance(raw, dict):
        return _invalid("setting", location, raw, LABEL_MODE_DEFAULTS[location])
    if location not in raw:
        return LABEL_MODE_DEFAULTS[location]
    mode = raw[location]
    if is_label_mode(mode):
        return mode
    return _invalid("setting", location, mode, LABEL_MODE_DEFAULTS[location])
```
Sources: `button_classes.py:103-133` (receiver and lazy read), `exceptions.py:32` (`is_strict`) [VERIFIED]. `MappingProxyType` is a suggestion for "documented as read-only" (D-21) [ASSUMED: a plain `dict` with a docstring also satisfies D-21; the planner picks one]. If a proxy is used, `{**LABEL_MODE_DEFAULTS}` and `set(LABEL_MODE_DEFAULTS)` still work.

Merging on every call costs nothing measurable. The accessor runs only on fallback paths and once per card action. A cache is not needed and would add staleness risk (ARCHITECTURE.md Pattern 1 agrees).

### Pattern 2: Warn once, strict raise (D-09/D-10/D-11)
```python
def _invalid(source: str, location: str, value, fallback: str) -> str:
    from ..exceptions import is_strict

    msg = f"label mode for {location!r} must be one of {sorted(LABEL_MODES)}, got {value!r} ({source})"
    if is_strict():
        raise ValueError(msg)
    key = (source, location, repr(value))  # repr: values like ["both"] / {"x": 1} are unhashable
    if key not in _warned:
        _warned.add(key)
        logger.warning("%s; using %r", msg, fallback)
    return fallback
```
In `cv_button_data`:
```python
label_mode = ctx.get("cv_label_mode") or default_label_mode(location)
if not is_label_mode(label_mode):
    label_mode = invalid_label_mode("cv_label_mode", location, label_mode, default_label_mode(location))
```
For D-10, keep the existing message substring `cv_label_mode` in the strict `ValueError`. `test_unknown_cv_label_mode_raises_everywhere` matches on `match="cv_label_mode"` (`test_button_data.py:122-125`) [VERIFIED]. `_invalid` therefore needs a public or semi-private name importable from `button_data` (e.g. `invalid_label_mode`). Keep the `or` (not `is None`). An empty string stamped today falls to the default, and this behaviour must stay so the goldens do not change.

### Pattern 3: Card resolver (LMOD-03, D-14/D-15)
```python
cv_card_actions_label_mode: str | None = None  # None: CRUD_VIEWS_LABEL_MODE_DEFAULTS["card"] (default "both")

@classmethod
def cv_get_card_actions_label_mode(cls) -> str:
    """The view's default mode for card actions: the attribute if set, else default_label_mode("card")."""
    if cls.cv_card_actions_label_mode is not None:
        return cls.cv_card_actions_label_mode
    return default_label_mode("card")
```
Use `@classmethod`, matching `cv_get_card_actions_inline` (`card.py:102-105`) and `cv_get_*` in `base.py`. `cv_get_card_action_data`'s `else` branch calls `self.cv_get_card_actions_label_mode()`. Change E210 to `if cls.cv_card_actions_label_mode is not None: yield label_mode_check(...)`.

### Pattern 4: E108 (LMOD-06, D-01…D-07)
```python
# inside _action_settings_messages, after E106; deferred imports
from crud_views.lib.view.button_data import LOCATIONS
from crud_views.lib.view.label_mode import _UNSET, _raw_label_mode_defaults

raw = _raw_label_mode_defaults()
name = "CRUD_VIEWS_LABEL_MODE_DEFAULTS"
if raw is not _UNSET:
    if not isinstance(raw, dict):
        messages.append(Error(id="crud_views.E108",
            msg=f"setting {name} must be a dict of location -> one of {sorted(LABEL_MODES)}, got {raw!r}"))
    else:
        for key, value in raw.items():
            if key not in LOCATIONS:
                messages.append(Error(id="crud_views.E108",
                    msg=f"setting {name} key {key!r} must be one of {sorted(LOCATIONS)}, got {value!r}"))
            elif not is_label_mode(value):
                messages.append(Error(id="crud_views.E108",
                    msg=f"setting {name} key {key!r} must be one of {sorted(LABEL_MODES)}, got {value!r}"))
```
The D-05 example wording is ambiguous for an unknown key. "key 'cotext' must be one of [locations], got ..." should end with `got` plus the value or the key. The planner should pin one wording in a test. A non-str key (e.g. `1`) falls under "unknown key". `sorted(LOCATIONS)` is `['card', 'context', 'list']`. Because E108 reads from django settings (not from `self`), its tests use `override_settings` + `CrudViewsSettings().check_messages`. This differs from the E106 tests, which pass kwargs (`test_action_label_mode_config.py:37-42`).

### Anti-Patterns to Avoid
- **A Pydantic field `label_mode_defaults = from_settings(...)`:** an import-time snapshot breaks `override_settings` (Pitfall 6 in PITFALLS.md). A strict type would also raise `ValidationError` at import before E108 runs (STACK.md).
- **`getattr(settings, NAME, None) or {}`:** this hides an explicit `None`, `""` or `[]` from E108 (violates D-03). Use a sentinel.
- **Mutating `LABEL_MODE_DEFAULTS`** in the merge (D-13).
- **Restating the resolution order** on several docs pages (D-25). Link to the one section in `action_menus.md`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Strict detection | own `settings.DEBUG` read | `crud_views.lib.exceptions.is_strict()` | honours `CRUD_VIEWS_STRICT` |
| Mode validity | `value in ("label", …)` literal | `is_label_mode()` / `LABEL_MODES` | one source of truth |
| Location validity | literal tuple | `button_data.LOCATIONS` (deferred import) | D-02; Phase 6 adds `"form"` automatically |
| Cache invalidation in tests | manual resets in each test | `setting_changed` receiver | `override_settings` fires it on enter and exit |

## Runtime State Inventory

This phase changes code and settings only. There is no rename or data migration.
- Stored data: none, verified (no DB fields involved).
- Live service config: none.
- OS-registered state: none.
- Secrets/env vars: none. The new Django setting is optional.
- Build artifacts: none. The `__pycache__` files are regenerated automatically.

## Common Pitfalls

### Pitfall 1: Circular import between `label_mode.py` and `button_data.py`
**What goes wrong:** `from .button_data import LOCATIONS` at the top of `label_mode.py` creates an import cycle, because `button_data.py:8` imports `label_mode` [VERIFIED].
**How to avoid:** Import inside `default_label_mode()` and inside E108. This is the same approach as `button_classes.py:213`, which defers `from .view.button_data import LOCATIONS` [VERIFIED]. Do not move `LOCATIONS` into `label_mode.py`: Phase 2/1C may split it, and `button_classes` imports it from `button_data`.

### Pitfall 2: A strict raise inside the W292 check kills E108
**What goes wrong:** `cv_icon_mode_checks` → `cv_get_action_label_mode` → `default_label_mode("context")` raises in strict mode, which is the default under `DEBUG=True`. `check_viewsets` (`checks.py:20-28`) builds E108 first and then iterates the viewset checks in the same function. The exception escapes and `manage.py check` / `runserver` show a traceback instead of E108 [VERIFIED by reading `checks.py`].
**How to avoid:** In `buttons.py` around `:405`, wrap the call in `try/except ValueError: continue`, with the comment "an invalid floor is reported by crud_views.E108". This mirrors the existing "invalid value counts as unset" at `:400-403`. Add a test: `override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"context": "nope"}, CRUD_VIEWS_STRICT=True)` and list `AuthorDetailView.checks()` messages without raising.

### Pitfall 3: Unhashable bad values in the warn-once set
**What goes wrong:** `test_unknown_cv_label_mode_raises_everywhere` already uses `["both"]` as a bad value (`test_button_data.py:121`). `set().add(("card", ["both"]))` → `TypeError: unhashable type: 'list'` [VERIFIED: ran in `.venv/bin/python`]. `lru_cache` on the value fails in the same way.
**How to avoid:** Key the set by `repr(value)`.

### Pitfall 4: Existing tests pin the old card default
`tests/test1/test_card_label_modes.py:14-15` contains `def test_default_is_both(): assert CardListView.cv_card_actions_label_mode == "both"` [VERIFIED]. Rewrite it so that the attribute is `None` and `CardListView.cv_get_card_actions_label_mode() == "both"`. `test_good_values_yield_no_check` (`:38-48`) should also cover `None`. `test_button_data.py:88-92` `test_card_label_mode_defaults_to_both` gains an `override_settings({"card": "label"})` variant (plan).

### Pitfall 5: Warn-once state leaking across tests (xdist and random order)
The suite uses `pytest-random-order` and `pytest-xdist` [VERIFIED: pyproject.toml:74,77]. A `caplog` test for the non-strict warning passes only if the pair has not been warned yet in that worker. Clearing on `setting_changed` covers tests that enter `override_settings(...)`, because entering fires the signal. Tests that warn under the D-10 path (stamped value, setting untouched) need `override_settings(CRUD_VIEWS_STRICT=False)`, which also clears thanks to the receiver above. Otherwise they should call `reset_label_mode_warnings()` explicitly. Add a "second call does not log again" assertion.

### Pitfall 6: `target_default` still beats the floor
With `{"context": "both"}`, a target view that sets `cv_context_action_label_mode = "icon"` stays icon-only. This is correct: the floor is the *last* step (`base.py:312`). Success criterion 1 says "unmapped" buttons. The test should use keys with no target default, and docs should state the order. The filter toggle has its own template (`context_action_filter.html`) and does **not** follow the floor until Phase 3 (1B). Write that in the docs or the acceptance note, so that "every toolbar button" is not misread.

### Pitfall 7: Docs links break `mkdocs build --strict`
New anchors (the canonical resolution section in `action_menus.md`, the table in `settings.md`) must exist before other pages link to them. Mermaid node text: change `MICON["icon"]` (`context_buttons.md:256`) to e.g. `MICON["defaults map<br/>CRUD_VIEWS_LABEL_MODE_DEFAULTS['context']<br/>(default icon)"]`. Keep the node id `MICON`, because `:262` and `:305` reference it [VERIFIED].

## Docs and changelog touchpoints (verified locations)

| File | Location | Change |
|------|----------|--------|
| `docs/reference/settings.md` | "## Action menus" table, lines 71-79 | Add a `CRUD_VIEWS_LABEL_MODE_DEFAULTS` row and the merge/replace/layer/keys table (D-24). Line 78 says "keys not named are `icon`", so update it |
| `docs/reference/action_menus.md` | "## Label mode" (58-90), "Target-view default" (91-122) | Line 70 says "Any key not named is `"icon"`" and lines 83-84 say "...then `"icon"`". Replace with the defaults map; add the canonical per-location order section (D-25) |
| `docs/reference/context_buttons.md` | Mermaid, line 256 | `MICON` label → defaults map + link |
| `docs/reference/card-list-view.md` | 50, 71, 73-78 | Type `str \| None`, default `None`; the resolver; the order; the line-77 tip ("set once on a base class") gets the setting as the first option |
| `docs/migrating-1.0.md` | 127-129 | Setting first (D-17), plus a Breaking bullet: the attribute reads `None` |
| `CHANGELOG.md` | `## Unreleased` → `### Breaking` (line 7), `### Added` (line 167) | Entries per D-16. Lines 44 and 56 mention the attribute and can stay |
| `docs/reference/buttons.md` | 423, 445 | Line 423 says "a card shows icon and text with `cv_card_actions_label_mode = "both"` (the default)". Reword |
| `.planning/PROJECT.md` | Key Decisions table, lines 89-93 | Add D-19 and D-20 rows (D-23) |
| Docstrings/comments | `settings.py:61-64`, `base.py:282/287/294`, `button_data.py:82`, `view/card.py:12`, `views/card.py:28/46` | Say "the defaults map" instead of "icon"/"both" |

## Code Examples
See Patterns 1-4 above. They are derived from the verified in-repo code (`button_classes.py:103-133`, `button_data.py:88-101`, `settings.py:117-131`).

## State of the Art

| Old | New | Impact |
|-----|-----|--------|
| Three hard-coded floors | `default_label_mode(location)` | One knob per location |
| `cv_card_actions_label_mode = "both"` | `None` + `cv_get_card_actions_label_mode()` | Breaking for readers of the attribute only |
| Bad stamped `cv_label_mode` raises in production | strict raise / warn once + fall back | Fixes a crash bug |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `LABEL_MODE_DEFAULTS` as a `MappingProxyType` (vs a plain dict) | Pattern 1 | Low. Either satisfies D-21. A proxy changes `type()` for consumers |
| A2 | A non-dict setting (incl. explicit `None`) at render: strict raise / warn once, then package defaults | Pattern 1 | Low. CONTEXT locks only E108 behaviour (D-03); the runtime behaviour is our recommendation |
| A3 | The E108 unknown-key message ends with `got {value!r}` | Pattern 4 | Low. Pin it in a test; the wording becomes frozen surface in Phase 7 |
| A4 | Clearing the warn-once set on a `CRUD_VIEWS_STRICT` change as well | Pattern 1 | None functionally; it only helps test hygiene |

## Open Questions (RESOLVED)

1. **Branch name.** **RESOLVED:** Keep the current branch (`introduce-gsd`); branch operations are excluded by `01-01-PLAN.md`'s context, with the same constraint in `01-02-PLAN.md` and `01-03-PLAN.md`. The revision instructions also prohibit branch changes. The source phase names `feat/label-mode-defaults` and the configured template is `gsd/phase-{phase}-{slug}`, but neither requires a branch operation in this plan set; the earlier execute-time confirmation recommendation is superseded by the current-branch constraint.
2. **E108 unknown-key wording** (A3). **RESOLVED:** `01-01-PLAN.md` task `01-01-02` pins `setting CRUD_VIEWS_LABEL_MODE_DEFAULTS key 'cotext' must be one of ['card', 'context', 'list'], got 'both'` and requires an exact-message test. The diagnostic names the key and ends with the value's repr, per D-04 and D-05.
3. **Should `invalid_label_mode` be public?** **RESOLVED:** `01-01-PLAN.md`'s artifact inventory and task `01-01-01` choose private `_invalid_label_mode`, imported within the package by `button_data`. It does not expand the D-21 public API.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python venv | tests | ✓ | 3.12.3 (`.venv`) | — |
| pytest (+ xdist, random-order, django) | tests | ✓ | label-mode subset: 216 passed in 4.9 s | — |
| ruff | lint | ✓ | 0.16.10 | — |
| mkdocs | docs gate | ✓ | 1.6.1 | — |
| node/vitest | global gate (no JS change) | not probed | — | `npx -y -p node@22` per plan |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-django (configured in `tests/test1/conftest.py` `pytest_configure`, strict mode on) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` (line 129) |
| Quick run command | `.venv/bin/pytest tests/test1/test_label_mode.py tests/test1/test_button_data.py tests/test1/test_card_label_modes.py tests/test1/test_context_action_label_mode.py tests/test1/test_action_label_mode_config.py -q` |
| Full suite command | `.venv/bin/pytest tests -n auto` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| LMOD-01 | per-key merge; unnamed keys keep package defaults; `LABEL_MODE_DEFAULTS` not mutated; `set(LABEL_MODE_DEFAULTS) == LOCATIONS` | unit | `pytest tests/test1/test_label_mode.py -q` | ✅ (extend) |
| LMOD-02 | context/list floor via `cv_get_action_label_mode`; `{"context": "both"}` toolbar renders icon+text, rows unchanged; W292 silent | unit + render | `pytest tests/test1/test_context_action_label_mode.py tests/test1/test_action_label_mode_config.py -q` | ✅ (extend) |
| LMOD-02 | acceptance grep empty | shell | `grep -n '"both" if card\|or "icon"\|get(key, "icon")' src/crud_views/lib/view/*.py; test $? -eq 1` | n/a |
| LMOD-03 | attribute `None`; resolver; explicit `"both"` beats `{"card": "label"}`; `None` passes E210; `{"card": "label"}` card render | unit + render | `pytest tests/test1/test_card_label_modes.py tests/test1/test_card_label_mode_render.py -q` | ✅ (update `test_default_is_both`) |
| LMOD-04 | `override_settings` changes `default_label_mode` and `cv_button_data` card default | unit | `pytest tests/test1/test_button_data.py -q` | ✅ (extend) |
| LMOD-05 | non-strict: bad setting mode → package default + one warning; bad stamped `cv_label_mode` → floor + one warning; strict raises; unhashable value ok | unit | `pytest tests/test1/test_button_data.py tests/test1/test_label_mode.py -q` | ✅ (extend) |
| LMOD-06 | E108 for unknown key, bad mode, nested dict, non-dict incl. `None`; one message per entry; unset → none; `{"form": ...}` fails; W292 does not crash on a bad floor | unit | `pytest tests/test1/test_action_label_mode_config.py tests/test1/test_settings_checks.py -q` | ✅ (extend) |
| all | goldens byte-identical | golden | `pytest tests/test1/test_action_menus_golden.py tests/test1/test_card_label_mode_render.py tests/test1/test_card_blocks.py tests/test1/test_card_order.py tests/test1/test_form_frame.py tests/test1/test_heading_level.py -q` (never with `CV_UPDATE_GOLDEN=1`) | ✅ |

The plan also names `test_check_messages.py`. In this repo that file tests the `Check*` helpers. Settings checks live in `test_settings_checks.py` and `test_action_label_mode_config.py` (E106) [VERIFIED]. Put the E108 tests next to E106.

### Sampling Rate
- **Per task commit:** the quick run command plus the golden tests.
- **Per wave merge:** `.venv/bin/pytest tests -n auto`, `ruff check`, `ruff format --check`.
- **Phase gate:** the full suite, `mkdocs build --strict` and vitest are green.

### Wave 0 Gaps
None. The test infrastructure exists; tests are only extended.

## Security Domain

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — |
| V3 Session Management | no | — |
| V4 Access Control | no | The label mode is presentation only. Permission gating (`cv_resolve_action`) is untouched |
| V5 Input Validation | yes (operator config) | E108 at startup; `is_label_mode()` at render; values are interpolated only through `{!r}` into logs and messages |
| V6 Cryptography | no | — |

| Pattern | STRIDE | Mitigation |
|---------|--------|------------|
| Availability: a bad config crashes production renders | DoS | D-09/D-10: non-strict falls back. This phase removes the existing production crash path |
| Log flooding from a bad config on a hot path | DoS | Warn once per `(source, location, repr(value))` |
| Markup injection via the mode value | Tampering | The mode is never rendered raw. Templates compare it against literals (`action.html:8`), and an invalid value never reaches the leaf |

## Sources

### Primary (HIGH confidence)
All read this session:
- `src/crud_views/lib/view/{label_mode,button_data,base,buttons,card}.py`
- `src/crud_views/lib/views/card.py`, `lib/settings.py`, `lib/exceptions.py`, `lib/button_classes.py`, `checks.py`
- `templatetags/crud_views.py`, `templates/crud_views/tags/button/action.html`
- tests in `tests/test1/` (`conftest.py`, `test_button_data.py`, `test_card_label_modes.py`, `test_label_mode.py`, `test_action_label_mode_config.py`, `test_settings_checks.py`, `test_action_menus_golden.py`)
- docs listed in the touchpoints table
- `.planning/research/PITFALLS.md` and `ARCHITECTURE.md`
- `superpowers/plans/2026-10-24-concept-review-followups.md` lines 40-105

No external documentation lookup was needed. The phase touches no third-party API beyond Django's long-standing `setting_changed` / `override_settings` / checks framework, and those are already used the same way in this repo.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH. In-repo only.
- Architecture: HIGH. Patterns are copied from existing verified code.
- Pitfalls: HIGH. Pitfalls 1-3 were verified by reading source or running Python.

**Research date:** 2026-10-25
**Valid until:** 2026-11-24, or until Phase 2 (1C) changes `LOCATIONS`
