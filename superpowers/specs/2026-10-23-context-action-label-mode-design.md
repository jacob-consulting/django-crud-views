# Context toolbar: label mode as a target-view default

Issue: #269

Date: 2026-10-23

## Intent

A context toolbar button already takes three of its four appearance properties from the view it points to (the
*target view*): weight (`cv_action_variant`), icon (`cv_icon_action`) and visible text
(`cv_action_short_label_template[_code]`). The label mode is the only one it cannot: it comes from the calling view's
map, the context button's `label_mode` (#264), the ViewSet map or the setting, and a key none of them names is
`"icon"`.

In the maintainer's project the toolbar rule is regular and belongs to the target view, not to the key or the page:

- standard keys pointing at update / detail / delete / list views → text, tertiary
- keys pointing at create views → icon + text, primary
- icon-only appears nowhere in a toolbar, only in table rows (edit and delete, pointing at the *same* update/delete
  views as the toolbar buttons)
- the few exceptions are per page (a detail page without a form makes its single "Edit" the loud, icon + text,
  primary button) or per custom key ("Edit public profile")

Today that takes a registered `ContextButton` for every standard key on every ViewSet (`list`, `home`, `detail`,
`update`, `delete`, `create`, plus the tab-heading keys) only to carry `variant` and `label_mode`. Because `detail`,
`update` and `delete` are row actions too and row actions resolve through a registered context button first, those
buttons also shape the rows, so the project has to take care that nothing toolbar-specific leaks into them.

With a fourth target-view attribute, the two rules become two attributes on two view base classes, and registered
buttons stay for the real exceptions (custom targets, tab keys, per-page overrides).

Series focus words: maintainability, low complexity, easy to theme downstream, no more upstream surface than the
issue needs.

## Goals

- A `CrudView` attribute `cv_context_action_label_mode: str | None = None` (`"label"`, `"icon"`, `"both"`) sets the
  label mode a context toolbar button gets when it points at that view.
- It is the most generic level: anything configured for a page, a button, a ViewSet or the setting overrides it.
- A project that sets nothing sees no change, byte for byte.
- An invalid value fails a system check; `viewset.W292` takes the new fallback into account.
- The difference to the existing, near-identically named `cv_context_actions_label_mode` is spelled out in the code
  comment and in the docs (see "Naming").

## Non-goals

- **Rows.** Table rows (location `"list"`) never read the attribute; they keep following the list maps (default
  `"icon"`). A view can be text in the toolbar and icon-only in a row.
- **Cards.** Cards resolve per `CardAction` and do not come through this path.
- **Action-menu items.** A key folded into the action menu renders icon and short label in every mode, as today.
- **Form buttons**, wildcards in the maps (`{"*": "label"}`), or a new setting.

## Anti-goals

- A configured page/button/ViewSet/setting mode that loses to the target-view default.
- Any change for projects that do not set the attribute.
- Toolbar appearance leaking into rows through the new attribute.

## Naming (decided by the maintainer)

The name stays as proposed in the issue: `cv_context_action_label_mode`. It differs by one letter from the existing
dict `cv_context_actions_label_mode`. The maintainer wants the difference stated where both are read:

| Attribute | Type | Set on | Meaning |
|---|---|---|---|
| `cv_context_actions_label_mode` (existing) | dict | the page showing the toolbar | "on my toolbar, key X looks like this" |
| `cv_context_action_label_mode` (new) | str | the view the button opens | "wherever a toolbar points at me, I look like this" |

- **Python:** a comment on both attributes in `src/crud_views/lib/view/base.py` carrying the "Set on" and "Meaning"
  of each, e.g.

  ```python
  # label mode per action key (#216), set on the page showing the toolbar: "on my toolbar, key X looks like this"
  cv_context_actions_label_mode: dict[str, str] | None = None
  # label mode as a target view (#269), set on the view the button opens: "wherever a toolbar points at me, I look
  # like this"; "label" / "icon" / "both"; None: "icon". The last fallback after the maps and the button's label_mode
  cv_context_action_label_mode: str | None = None
  ```

  (The existing shared comment above `cv_list_actions_label_mode` stays for the list map; wording is the builder's.)
- **Docs:** the table above in the "Label mode" section of `docs/reference/action_menus.md`.

## Behaviour

### Precedence (context toolbar only)

First non-`None` wins:

1. the calling view's `cv_context_actions_label_mode`, if it names the key
2. the context button's `label_mode` (#264)
3. the resolved map (ViewSet `context_actions_label_mode`, else `CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE`), if it
   names the key
4. **the target view's `cv_context_action_label_mode`**
5. `"icon"`

Consequence to document: a map that does not name a key no longer means "icon" for it when the target view sets the
attribute. The sentence in `action_menus.md` saying `{}` on a view "makes every action of that view icon-only
whatever its ViewSet says" stays true about the ViewSet but needs a qualifier for the target-view default. Not a
breaking change: only projects that set the new attribute see a difference, so `docs/migrating-1.0.md` is unchanged.

### Where the value comes from

The target class is resolved where the action data is built, not in `cv_get_action_label_mode()` on the calling view.
Both paths build that data through the target's `cv_get_dict()`:

- a plain key: `CrudView._cv_get_action_context()` → `cls.cv_get_dict(...)`
- a registered button: `ContextButton.get_context()` → `cls.cv_get_dict(...)`

So `cv_get_dict()` adds the target's value to the action data (under a new key, the way `cv_variant` travels), and
`cv_get_context(..., location="context")` uses it as step 4 when it stamps `cv_label_mode`. Steps 1–3 and 5 stay in
`cv_get_action_label_mode()`; how that method learns about the fallback (an extra argument, a `None` return for "not
named", or a sibling helper) is the builder's choice, as long as the static caller in `W292` and the render-time caller
in `cv_get_context()` share one resolution.

Because the value lives in `cv_get_dict()`, every built-in button follows its target view, across ViewSets too:
the default `home` (→ `list`), `parent` (`ParentContextButton` → the parent ViewSet's `list`), and
`ChildContextButton` / `SiblingContextButton`, all of which build their data through the target's `cv_get_dict()`.
This matches how `cv_variant`, the icon and the short label already travel ("wherever the button appears"): giving
list views `"label"` turns every `home` and `parent` toolbar button into text. `W292` keeps skipping these subclasses
(own `get_context()`); the render-time guard still covers them.

This covers every way a toolbar button is rendered through `location="context"`: the toolbar itself, keys kept inline,
and the heading button `{% cv_context_button key %}` (it calls `cv_get_context(..., location="context")`). A button
with its own `get_context()` that does not call `cv_get_dict()` simply has no value in its data and falls through to
`"icon"`, as today.

### Checks

- **`viewset.E210`**: `cv_context_action_label_mode` must be `None` or one of the label modes, via
  `label_mode_check(cls, "cv_context_action_label_mode", value)` in the `CrudView` checks next to
  `variant_check(cls, "cv_action_variant", ...)`. The message should help someone who put a dict there (the map
  attribute's name is one letter away), as `E211` already points at `cv_card_actions_label_mode`.
- **`viewset.E211`**: if someone sets a string on `cv_context_actions_label_mode`, E211 already fires; its message
  should name `cv_context_action_label_mode` as the string-valued target default, like it names
  `cv_card_actions_label_mode` today.
- **`viewset.W292`** (toolbar key renders icon-only although its target has no icon): it already resolves the target
  class for the keys it can see statically. It must use the full precedence above, so a key whose target sets
  `"label"` or `"both"` is no longer reported, and a key whose target sets `"icon"` explicitly is still reported when
  the target has no icon. Skipped cases (menu-folded keys, custom templates, own `get_context()`, unregistered
  targets) stay skipped.
- The render-time icon-without-icon guard in `cv_button_data()` (raise under `CRUD_VIEWS_STRICT`, else render as
  label with a warning) needs no change; it sees the stamped `cv_label_mode`.

## Tests (what must be covered)

- Target attribute `"label"` / `"both"` on an update view: its toolbar button renders in that mode; the row action of
  the same key on a list page stays `"icon"`.
- Each higher level overrides it: calling view's map, button `label_mode`, ViewSet map, setting.
- A calling map that names *other* keys does not hide the target default for unnamed keys.
- Registered `ContextButton` whose target is a CrudView picks up the target's attribute unless it sets `label_mode`.
- `home`, `parent`, a `ChildContextButton` and a `SiblingContextButton` follow their target view (cross-ViewSet).
- Heading button via `{% cv_context_button %}` follows the attribute.
- A key folded into the action menu is unaffected.
- Nothing set anywhere: existing goldens unchanged.
- E210 for an invalid value (including a dict); E211 message mentions the new attribute; W292 silenced by a target
  `"label"`/`"both"`, still raised for an explicit target `"icon"` without icon.

## Docs and changelog

- `docs/reference/action_menus.md` "Label mode": the new attribute, the precedence list with the target level, the
  naming table, the `{}` qualifier, the "toolbar only" note, and an example in the maintainer's shape (update view →
  `"label"`, create view → `"both"`), generic names only.
- `docs/reference/context_buttons.md`: where `label_mode` is explained, note the target-view default below it (and that
  parent, child, sibling and `home` buttons follow their target view) and link
  to the table.
- `CHANGELOG.md` under `### Added`.
- Docs and code must not name client or downstream projects.

## Calls made by Claude (check while reading)

- The heading button follows the attribute (it shares the `location="context"` path).
- Action-menu items ignore it (they always show their label).
- A registered `ContextButton` pointing at a CrudView inherits the target's attribute unless it sets `label_mode`.
- Parent, child, sibling and the default `home` buttons inherit it too, across ViewSets (builder check question;
  settled for consistency with variant, icon and label).
- `cv_get_action_label_mode(location, key)` keeps returning a `str`; the fallback comes in as an optional argument.
- Not breaking; `docs/migrating-1.0.md` untouched.
- The E211 message gains a pointer to the new attribute.

## Left to the builder

- The name of the action-data key carrying the target's value (the issue suggests `cv_context_label_mode`; it must
  not collide with the leaf input `cv_label_mode`).
- How the fallback is wired inside `cv_get_action_label_mode()`, within the constraint above.
- Exact wording of comments, check messages and docs.
