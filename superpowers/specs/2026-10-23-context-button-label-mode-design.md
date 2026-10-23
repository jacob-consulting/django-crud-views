# Context buttons: a label mode per button, and no invisible icon buttons

Issue: #264

Date: 2026-10-23

## Intent

A context toolbar button's label mode comes only from per-key maps: the view's `cv_context_actions_label_mode`, the
ViewSet's `context_actions_label_mode` or `CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE`. A key none of them names is
`"icon"`. A `ContextButton` type cannot carry its own mode, although cards already can (`CardAction.label_mode`). A
project whose toolbar buttons are mostly text has to name every key on every ViewSet and keep the map in step with
the buttons it registers.

The worse half: a key that is forgotten resolves to `"icon"`, and if the button has no icon it renders an empty box
whose only content is the visually hidden label. Nothing raises, and tests that look for the label text pass because
the text is there. The maintainer found the risk while planning a move of text-only toolbar buttons onto the stock
leaf, and then hit a real instance on list rows: a button type set the icon to `None`, overwriting the target view's
icon, and the icon-mode row buttons rendered as empty boxes. It was found only by comparing the page visually with
the previous version.

The maintainer's priorities, in their order:

1. **Be told as early as possible.** A system check where the outcome is known statically; where it is only known
   at render time, raise under `CRUD_VIEWS_STRICT` (as unresolved targets already do), so dev and test runs fail.
2. **In production, degrade to the label rather than an empty button.** A visible text button with the wrong look is
   a styling bug; an invisible one is a broken page.

Quietly falling back to the label without any signal is explicitly unwanted: the page then looks *almost* right and
hides the mistake.

Series focus words: maintainability, low complexity, easy to theme downstream, no more upstream surface than the
issue needs.

## Goals

- `ContextButton.label_mode` sets a button's mode in the context toolbar for every view of the ViewSet.
- An invalid `label_mode` value fails a system check.
- A toolbar button that statically resolves to `"icon"` with an empty icon is reported by a system check.
- At render time, an action button (context, list or card) whose mode is `"icon"` and whose icon is empty raises
  under strict mode and renders as `"label"` otherwise.
- With no `label_mode` set on any button and every icon-mode button having an icon, the output is byte-for-byte what
  it is today.

## Non-goals

- **Row actions do not read the button's `label_mode`.** Row actions resolve through the registered context button
  for their key, but the maintainer chose toolbar only (alternatives below): rows keep following the list maps
  (`cv_list_actions_label_mode`, `list_actions_label_mode`, `CRUD_VIEWS_LIST_ACTIONS_LABEL_MODE`). The render-time
  guard still covers rows.
- A separate `list_label_mode` (or similar) field on the button.
- A wildcard key in the label-mode maps (`{"*": "label"}`).
- Statically following buttons that override `get_context()` (`ParentContextButton`, `ChildContextButton`,
  `SiblingContextButton`, `FilterContextButton`, project subclasses): they are skipped by the static check, as `E255`
  skips them. The render-time guard covers them.
- Icons that are non-empty but render nothing (an unknown prefix, a broken library config). "Empty" means the icon
  value is `None` or `""`.
- Menu items (`kind="menu-item"`): they always show their label, so they are not affected.

## Anti-goals

- A silent fallback with no signal in dev or test.
- Changing what the maps mean today. A view map that is set still replaces the ViewSet map and the setting as a
  whole (#216 layering); the button only slots in between.
- A button's `label_mode` leaking into list rows.

## Design

### The field (`src/crud_views/lib/view/buttons.py`)

```python
class ContextButton(BaseModel):
    ...
    label_mode: str | None = None  # None: the view's context label-mode maps; one of LABEL_MODES (#264)
```

Inherited by every subclass. It is a plain field like `variant`; it is never stamped into the button's data by
`get_context()`, so a row action going through the same button does not see it.

### Precedence (context location only)

For a context-toolbar key, first match wins:

1. the **view's own** `cv_context_actions_label_mode`, if it is set **and names the key**;
2. the **button's** `label_mode`, if the key has a registered context button (view-level `cv_context_buttons` first,
   then the ViewSet's, as `cv_get_context_button()` already does) and its `label_mode` is not `None`;
3. today's resolution, unchanged: the first map that is not `None` of view → ViewSet → setting, looked up by key,
   `"icon"` for a key it does not name.

So the issue's order "view map → button → ViewSet map → setting → `icon`" holds, and today's layering is kept: when a
view map is set but does not name the key, step 3 still uses that view map (→ `"icon"`) rather than falling through
to the ViewSet map. With no button `label_mode` set, the result is what `cv_get_action_label_mode()` returns today.
*(My call, so that the behaviour of projects that don't change anything stays the same.)*

For `location="list"` nothing changes: the button is not consulted.

Where it is wired is left to the builder. The natural place is `cv_get_context(..., location="context")`, which
already stamps the mode, plus whatever the static check needs to resolve the same order without a request (a
classmethod that takes the button, or the view class and key). One function decides the order; the check and the
render path both call it.

### Render-time guard (`src/crud_views/lib/view/button_data.py`, `cv_button_data()`)

After the mode is settled (including the existing "empty label forces `icon`" rule), for `kind="action"` at any
location:

- if the mode is `"icon"` and the icon value (`ctx["cv_icon_action"]`) is `None` or `""`:
  - under strict mode (`getattr(settings, "CRUD_VIEWS_STRICT", settings.DEBUG)`, the same test as
    `ignore_exception`), raise. The message names the location, the key and the remedy (give it an icon, or a
    `label_mode` / map entry of `"label"` or `"both"`). *Exception type: builder's call; `ValueError` matches the other
    errors `cv_button_data()` raises.*
  - otherwise, set the mode to `"label"` and log a warning naming the key and location (builder's call: a production
    log line is the signal that remains when strict is off).
- The label that the `"label"` mode then shows is the short label for context and list, as for any labelled button
  today.
- If the label is empty as well, there is nothing to fall back to: strict raises the same way; non-strict leaves the
  mode at `"icon"` (the button is empty either way) and logs. *(Builder's call.)*

**Strict mode and test runs (maintainer's decision).** pytest-django forces `DEBUG=False`, so with the default
trigger a test suite takes the quiet path. The trigger stays as it is (no new setting); instead:

- this repo's test settings (`tests/test1/conftest.py`) set `CRUD_VIEWS_STRICT=True`. Turning it on suite-wide may
  make other `ignore_exception` paths raise in existing tests; the builder fixes real misconfigurations, pins tests
  that deliberately exercise the quiet path to `CRUD_VIEWS_STRICT=False` (as `test_strict_mode.py` already does), and
  lists each in the acceptance report;
- the docs and the CHANGELOG tell projects to set `CRUD_VIEWS_STRICT = True` in their test settings, because
  pytest-django turns `DEBUG` off.

This covers the maintainer's real case (rows, a subclass setting the icon to `None`), cards with
`CardAction(label_mode="icon")` and no icon, and `{% cv_context_button %}`, which all go through `cv_button_data()`.

### System checks

- **Invalid `label_mode` → `viewset.E210`** (reuse `label_mode_check()` from `lib/view/label_mode.py`), run from
  `context_button_checks()` for every configured button whose `label_mode` is not `None`, next to the existing
  `variant_check`. This includes buttons equal to a default (they are skipped only for `E255`). The owner string is
  `f"context button {button.key!r}"`. View-level `cv_context_buttons` get the same check wherever they are checked
  today (builder: confirm where that is, and add it there if they are not checked).
- **Invisible toolbar button → new warning `viewset.W292`** (next free number after `W291`; builder confirms it is
  unused). For each view and each key in its `cv_context_actions`:
  - resolve the mode with the precedence above;
  - if it is `"icon"`, find the icon statically: for a key with a plain `ContextButton` (its class does not override
    `get_context()`), the `cv_icon_action` of the target view class at `key_target` (with the `list` → `card`
    fallback); for a key without a context button, the `cv_icon_action` of the view registered under the key;
  - warn when that icon is `None` or `""`. Skip a key whose button overrides `get_context()`, and a key whose target
    is not registered (`E255` / unregistered-key handling already covers those).
  - Also skip keys that never render through the action leaf, matching the render-time guard: a key that folds into
    the action menu (`cv_get_context_actions_inline()` is set and the key is foldable and not named in it, as
    `cv_split_actions` / `cv_context_button_foldable` decide) renders as a menu item, which always shows its label;
    a plain `ContextButton` with its own `template` / `template_code` renders its own markup. *(My call: otherwise
    projects using action menus get false positives.)* Where the split needs request-time data, err on the side of
    not warning; the render-time guard remains the backstop.
  - Message: names the view, the key and the remedy.
  It is a warning, not an error, because the production fallback makes the page usable; the strict raise makes it
  loud in dev and test.

### CHANGELOG

Under **Added**: `ContextButton.label_mode`, `viewset.W292`. Under **Changed**: an icon-mode action button with an
empty icon now renders as a text button (with a logged warning), and raises under `CRUD_VIEWS_STRICT` (default
`DEBUG`). pytest-django turns `DEBUG` off, so a test suite only fails on such a button with `CRUD_VIEWS_STRICT = True`
in its test settings; the entry recommends that. Not filed under **Breaking**, because only pages that render an invisible
button change; `docs/migrating-1.0.md` is therefore not touched. *(My call; the maintainer may move it.)*

## Tests

- Precedence unit tests: each of the three steps winning; a view map set but not naming the key with a button
  `label_mode` (→ button); a view map set and not naming the key without a button `label_mode` (→ `"icon"`, as
  today); view-level `cv_context_buttons` beating the ViewSet's.
- Through the views: a toolbar button with `label_mode="label"` renders as text with no map; the same key in a list
  row renders as the list maps say (not as the button says); `{% cv_context_button %}` follows the button's mode.
- `cv_button_data()`: icon mode with `cv_icon_action` `None` / `""` raises under `CRUD_VIEWS_STRICT=True`; falls back
  to `"label"` and logs under `False`, for `context`, `list` and `card`; menu items untouched; an icon present →
  unchanged.
- Checks: `E210` for an invalid button `label_mode` (ViewSet-level and view-level buttons); `W292` for a plain
  button / no-button key resolving to `"icon"` with an empty target icon; no `W292` when the button or a map gives
  `"label"` / `"both"`, when the icon is set, or for a button overriding `get_context()`.
- Existing goldens under `tests/test1/golden/` stay unchanged. With `CRUD_VIEWS_STRICT=True` suite-wide, existing
  tests that render an icon-mode button without an icon will raise; adjust those deliberately (give them an icon, a
  label mode, or pin strict off) and note each one in the acceptance report.

## Docs

- `docs/reference/context_buttons.md`: the `label_mode` field, the precedence, and one sentence that it applies to
  the toolbar and `{% cv_context_button %}` but not to row actions, which follow the list maps.
- `docs/reference/action_menus.md#label-mode`: the button as the second step of the context precedence; the
  icon-without-icon rule (strict raises, otherwise label).
- `docs/reference/buttons.md`: the `cv_label_mode` row of the leaf contract table (the new rule) and `W292` (plus the
  wider `E210` wording) in the checks table.
- `CRUD_VIEWS_STRICT` is documented nowhere yet: add it to `docs/reference/settings.md` (what it does, default `DEBUG`,
  and the advice to set it `True` in test settings because pytest-django turns `DEBUG` off).
- `CHANGELOG.md` as above.

## Alternatives considered

- **Button `label_mode` applies to rows too.** One knob per button type, but a toolbar-driven `"label"` would widen
  every row's actions column, would beat the ViewSet's list map silently, and would only reach row keys that have a
  context button, so one row could mix styles. Rejected by the maintainer in favour of toolbar only.
- **Runtime fallback only, or check only.** Fallback alone hides the mistake; a check alone misses buttons whose icon
  is only known at render time (the real case). Both, plus strict.

## Left to the builder

- Where the precedence function lives and its signature; it is shared by the render path and `W292`.
- The exception type for the strict raise, and the log message wording.
- Test file placement and names.
- Whether `W292` is reported once per view or once per (view, key).

Settled by the builder check: `context_button_checks()` already runs for view-level and ViewSet-level buttons, so
`E210` goes next to `variant_check` in both; `W292` is unused; the new `label_mode=None` field does not break the
`button in defaults` equality skip.
