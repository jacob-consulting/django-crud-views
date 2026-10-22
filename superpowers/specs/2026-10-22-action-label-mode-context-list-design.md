# Context and list buttons learn the label mode

Issue: #216. Tracker: #228. Siblings: #213 (landed, the three-state label mode on cards), #209 (landed in #229,
the class table's `location:variant:mode` key this design relies on), #227 (open, the leaf's hard-coded utility
classes, sequenced after this).

Date: 2026-10-22

## Intent

`cv_button_data()` decides the label mode of a context (toolbar) and list (row) button with one line:

```python
    else:
        label_mode = "icon"
```

(`src/crud_views/lib/view/button_data.py:58-59`). So every toolbar and row button is icon-only by construction:
the leaf renders the icon plus a visually hidden label, and `cv_title` carries the name as a tooltip. A project
that wants a toolbar whose primary action reads "Create" with its icon, while the secondary actions stay
icon-only, has to override `tags/button/action.html` — which is what the Tabler theme prototype did, then gave up
and recorded the loss as an accepted difference.

**The picture the maintainer described.** A toolbar where the primary "Create" button shows icon and text and
every other button stays icon-only. That is Tabler's own demo shape, GitHub's and the Django admin's.

**Why now.** #213 gave cards a three-valued `LabelMode` and #209 made the class table able to style the three
modes differently in every location — so `context:primary:both` is a valid, resolvable key today that nothing can
produce. This design is the step that produces it. It adds no mechanism: it lets the state #213 established reach
the two locations #213 left out, driven from settings, the ViewSet and the view, exactly where the equivalent
inline-keys knob already lives.

## Goals

- A project can give a toolbar or row button a visible text label, alongside its icon or instead of it, without
  overriding `tags/button/action.html`.
- It is set once for the project and overridable per ViewSet and per view, with the same three-layer resolution
  as the inline keys.
- The default markup for context and list buttons is byte-identical to today's: no golden moves for a project that
  does not opt in.
- The mechanism is #213's `LabelMode`, the leaf's existing `cv_label_mode` branch and #209's class table key.
  Nothing new is invented between the view and the markup.
- A labelled button has exactly one accessible name (its visible text) and no tooltip.

## Non-goals

- **Changing any default.** Both new settings default to an empty mapping. Nothing renders differently until a
  project names a key.
- **A per-action object for context and list actions.** `cv_context_actions` and `cv_list_actions` stay lists of
  key strings. A `ContextAction` class in the image of `CardAction` would be the "right" long-term shape but is a
  migration of every project's view configuration for the sake of one attribute; the inline keys solved the same
  problem with a parallel key-based knob, and this design does the same. Revisit only if a third per-key attribute
  appears.
- **`ContextButton.label_mode`.** `ContextButton` objects (`home`, `parent`, `filter`, child links) do carry
  per-button fields such as `variant`, so a field there is tempting. It would not reach the one button the
  maintainer named: `create` is a plain view key, not a `ContextButton`. One knob that covers every key beats two
  that cover different halves.
- **A string shorthand** (`cv_context_actions_label_mode = "both"` meaning every action). It is one more branch
  and one more thing to document for a shape nobody asked for; a project that wants it writes the dict.
- **Mode on menu items.** An action folded into the overflow menu renders icon and short label in every mode, as
  it does today (`menu_item_label.html` prints `cv_short_label` and never reads `cv_label_mode`). One thing does
  follow the mode there: a context menu item's `title`, which `menu_item.html:7` prints from `cv_title`, and
  `cv_title` exists only in `icon` mode. So a key configured `both` or `label` has no tooltip inline *and* no
  `title` when it is folded. That is the rule "a labelled action has no tooltip" holding everywhere, not a gap,
  and it is chosen over neutralising the mode for menu items (a line in the `cv_button` tag or a `kind` parameter
  on `cv_button_data()`) because it needs no mechanism. Nothing changes for a key left at `icon`.
- **The filter toggle and custom context-button templates.** `context_action_filter.html` is icon-only by
  construction and passes a literal `"icon"` to the class table (#209). A project's own `template` /
  `template_code` renders whatever it renders. The knob changes the bundled action leaf's output and nothing else.
- **The hard-coded `active` / `flex-grow-1` in the leaf.** #227, after this.

## Anti-goals

These would make the change a failure even if the acceptance criteria passed:

- **A second vocabulary.** A list of "labelled keys" (`["create"]`) is a boolean in disguise and cannot say
  `label`. Anything other than the three `LabelMode` values as the configured state is the defect #228 exists to
  prevent.
- **Merging layers.** View, ViewSet and setting dicts are not merged key by key. The first layer that is not
  `None` is used whole, as the inline lists are. A merge is more convenient for exactly one configuration and
  undebuggable for every other.
- **A leaf change.** `tags/button/action.html` already branches on all three modes. If this design needs to edit
  it, something upstream is wrong. Theme overrides of the leaf (the recipe in `buttons.md`) must keep working
  unchanged.
- **A quiet failure that is not icon-only.** If a code path forgets to resolve the mode, the button must render
  as it does today (icon-only), never crash and never show text by accident.

## Decisions already taken

Settled in the brainstorming conversation:

1. **The toolbar shape**: primary "Create" with icon and text, the rest icon-only. (Maintainer.)
2. **Project-wide default with a per-view override.** (Maintainer.) The ViewSet layer in between is my call, see
   below.
3. **The same knob, under the same names, for list rows**, defaulting to icon-only. (Maintainer.)
4. **The knob is a mapping from action key to `LabelMode`**, not a list of labelled keys. Any key not in the
   mapping is `icon`. (My call, following #228's one-vocabulary rule.)
5. **Keys are the configured keys**, the strings written in `cv_context_actions` / `cv_list_actions`, exactly as
   the inline lists match them: `"home"`, not its target `"list"`. (My call; the alternative is inconsistent with
   the inline lists and ambiguous for `ContextButton`s, whose `cv_key` is the target view's key —
   `lib/view/buttons.py:108` via `cv_get_dict`, except the filter toggle at line 322.)
6. **The visible text is the short label** (`cv_action_short_label`: "Create", not "Create new author"). (My
   guess, stated in the conversation and not contradicted; it is what the maintainer's words say and what cards
   show.)
7. **No tooltip and no hidden duplicate on a labelled button.** This is not a new rule: `cv_title` is set only in
   `icon` mode today (`button_data.py:94`), and the leaf's `both` / `label` branches render one visible span.
   Keeping the existing rule satisfies #216's acceptance criterion by construction.

## Design

### Names

| Layer | Context toolbar | List rows |
|---|---|---|
| Django settings | `CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE` | `CRUD_VIEWS_LIST_ACTIONS_LABEL_MODE` |
| `ViewSet` | `context_actions_label_mode` | `list_actions_label_mode` |
| `CrudView` | `cv_context_actions_label_mode` | `cv_list_actions_label_mode` |

Each holds `dict[str, str] | None`: action key → one of `"label"`, `"icon"`, `"both"`. The settings default to
`{}`; the ViewSet fields and view attributes default to `None`, meaning "ask the next layer".

Known wart, chosen with eyes open: `cv_card_actions_label_mode` is a *string* (the default for every card action,
with `CardAction.label_mode` as the per-action override), while these two are *dicts*. The suffix is the same
because the concept is the same — the view's label-mode policy for that location — and the type differs because
cards have a per-action object to carry the override and the other two locations do not. The system check for
the view attribute names the card attribute in its message so that a value of `"both"` by analogy gets a precise
error, not a cryptic one.

### Resolution

```python
@classmethod
def cv_get_context_actions_label_mode(cls) -> dict[str, str]: ...
@classmethod
def cv_get_list_actions_label_mode(cls) -> dict[str, str]: ...
```

First value that is not `None`: view attribute, then ViewSet field, then setting. `cv_first_inline_keys()`
(`lib/view/base.py:235`) already does precisely this for the inline lists and is reusable as it stands; its name
is the only thing about it that is inline-specific. Renaming it is in scope if the builder wants to, with the
three existing callers updated.

`{}` at any layer is a value, not an absence: a view that sets `cv_context_actions_label_mode = {}` under a
ViewSet that labels `create` gets an icon-only toolbar. Same as `[]` for the inline lists.

```python
def cv_get_action_label_mode(self, location: str, key: str) -> str:
    """The label mode of one configured context or list action key; "icon" for a key not in the mapping."""
```

`location` is `"context"` or `"list"`. Cards are not routed through this: they resolve their mode in
`cv_get_card_action_data()` (`lib/views/card.py:47-52`) and that stays as it is.

### Where the mode enters the data

The mode has to be stamped where the **location** and the **configured key** are both known, and the action
context must carry it as `cv_label_mode` by the time `cv_button_data()` sees it. Five paths produce a context or
list leaf, and all five already call the same view method with the configured key:

| Path | Calls |
|---|---|
| `{% cv_context_action key %}` (per-key tag, `templatetags/crud_views.py:211`) | `view.cv_get_context(key, ...)` |
| `{% cv_context_button key %}` (manual placement, line 242; documented in `context_buttons.md` and the FAQ) | `view.cv_get_context(key, ...)` |
| `{% cv_list_action key obj %}` (per-key tag, line 115) | `view.cv_get_context(key, ...)` |
| `cv_get_context_action_group()` / `cv_get_list_action_group()` → `cv_resolved_actions()` (`base.py:496`) | `self.cv_get_context(key, ...)` |
| `cv_get_context_buttons()` for custom loops (`base.py:481`) | `self.cv_get_context(key, ...)` |

**My call: one funnel.** `cv_get_context()` (`base.py:535`) gains a keyword-only `location: str | None = None`.
When it is `"context"` or `"list"`, the returned dict carries
`cv_label_mode = self.cv_get_action_label_mode(location, key)`; when it is `None` (every other caller:
breadcrumbs, origin links, the manage view, the hidden POST-form tags) nothing changes. The five callers above
pass their location. `cv_resolved_actions()` needs to learn its location too; its two callers know it.

Manual placement honours the knob: `{% cv_context_button "create" %}` in a project template renders the same
button the toolbar would. The alternative, a documented tag that silently ignores a documented setting, is
exactly the kind of difference a project would spend an afternoon on.

**Overrides of `cv_get_context()` must accept and forward the keyword.** There is one in the package:
`src/crud_views_guardian/lib/mixins.py:111` overrides it with the four positional parameters and calls `super()`
with explicit keywords. Left as it is, every guardian view raises `TypeError` the moment a toolbar renders; the
guardian tests render pages, so it fails loudly, but it is part of this change, not a discovery to make later.
Worth one sentence in the CHANGELOG for projects that override `cv_get_context()` themselves.

Why not the `cv_button` tag, which is the single place every inline button of every location passes through
(`templatetags/crud_views.py:191`)? Because by then the view is gone — the leaf templates render from the action
dict alone, which has no `view` entry (`cv_get_dict`, `base.py:347`), and `cv_key` is the target key, not the
configured one (decision 5). Stamping upstream, where both are known, is the only option that is also
consistent with how the inline split is matched.

A consequence to state in the docs: a `ContextButton`'s custom `template` / `template_code` now also receives
`cv_label_mode` in its context, resolved for its key. The bundled filter toggle ignores it, as it should; a
project template may honour it.

### `cv_button_data()`

```python
    label_mode = ctx.get("cv_label_mode") or ("both" if card else "icon")
    if not is_label_mode(label_mode):
        raise ValueError(...)
    if not label:
        label_mode = "icon"
```

The card branch keeps its default of `"both"` and its validation; the other two locations stop forcing `"icon"`
and read the stamped value instead, with `"icon"` as the default when nothing was stamped. That default is the
anti-goal's safety net: any path that does not stamp renders exactly today's markup.

The visible label for context and list in a text-showing mode (decision 6):

```python
    if not card and label_mode != "icon":
        label = short_label
```

So for `context` and `list`, `cv_label` is the full label in `icon` mode — where it is the hidden text and the
`title`, as today — and the short label in `label` / `both` mode, where it is the visible text. `cv_short_label`
is unchanged. The leaf keeps rendering `{{ cv_label }}` in every branch and is not edited. The alternative,
teaching the leaf to print `cv_short_label` in the visible branches, would be a leaf change every theme override
has to mirror; this one is invisible to them.

`cv_title` keeps its existing rule (`icon` mode only), so the labelled button has no `title` and no
`data-cv-tooltip`, and the `both` / `label` branches render one visible `<span>`: one accessible name.

### The class table

Nothing to build. The leaf already passes `cv_label_mode` to `{% cv_button_class %}` (#209), so a labelled
toolbar button resolves `context:primary:both` with its one-step fallback to `context:primary`. This is the
reason the Tabler theme can now keep `btn-icon` out of a labelled button: it registers
`"context:primary:icon": "btn btn-primary btn-icon"` and lets `"context:primary"` be the labelled form — or the
inverse, whichever its table prefers. Nothing in the shipped defaults changes.

### Checks

Three new ids; all three exist as unused numbers today (`crud_views.E100`–`E105`, `viewset.E200`–`E210`,
`viewset.W290` are taken).

| ID | Level | Fires when |
|---|---|---|
| `crud_views.E106` | error | `CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE` or `CRUD_VIEWS_LIST_ACTIONS_LABEL_MODE` is not a dict of `str` → `"label"` / `"icon"` / `"both"` |
| `viewset.E211` | error | a view's `cv_context_actions_label_mode` / `cv_list_actions_label_mode` is not `None` or such a dict; the message names `cv_card_actions_label_mode` as the string-valued card attribute |
| `viewset.W291` | warning | a view's **own** `cv_*_actions_label_mode` names a key that is not among that location's actions (typo?) — same rule and same reasoning as `W290`: ViewSet and setting values are shared defaults and may legitimately name keys some views lack |

The ViewSet fields are validated by Pydantic at construction, as the inline fields are: a wrong value raises
`ValidationError`. The value check (membership in `LABEL_MODES`) must be there too, not only the dict shape;
whether that is `dict[str, LabelMode]` (the `StrEnum` from `lib/view/label_mode.py`, which compares equal to the
plain strings) or a field validator is the builder's choice.

`settings.py` must not import the view package at module level (`settings.py:133`, existing comment); the
check imports `is_label_mode` deferred, as the inline check imports `cv_is_inline_keys`.

## Constraints

- Line length 120, double quotes, ruff format. `cv_` prefix on `CrudView` attributes.
- `cv_get_context()` is called from the template-tag wrapper of the same name (`templatetags/crud_views.py:77`),
  from the manage view and from the breadcrumb and origin-link code. The new parameter is keyword-only with a
  `None` default, so every existing caller is untouched.
- `cv_button_data()` is public in the sense that theme leaves consume its output and `test_button_data.py`
  pins its contract. `LEAF_KEYS` does not change; the meaning of `cv_label` for context and list widens as
  described and the docs row changes with it.
- Django 4.2 / 5.2 / 6.0, Python 3.12–3.15.
- Goldens: **none move**. The eight files under `tests/test1/golden/action_menus/` are rendered with no mode
  configured. A diff there is a bug, not a regeneration; say so in the PR description because the regeneration
  command rewrites all eight.

## Work

### Code

- `src/crud_views/lib/settings.py` — the two settings (default `{}`) and the `E106` check.
- `src/crud_views/lib/viewset/__init__.py` — the two fields, validated.
- `src/crud_views/lib/view/base.py` — the two attributes, the two dict getters, `cv_get_action_label_mode()`,
  the `location` parameter on `cv_get_context()` and `cv_resolved_actions()`, the four callers passing their
  location, the `E211` / `W291` checks in `cv_checks()` next to the inline checks (`base.py:166-167`).
- `src/crud_views/templatetags/crud_views.py` — `cv_context_action`, `cv_context_button` and `cv_list_action`
  pass their location through the `cv_get_context` wrapper.
- `src/crud_views_guardian/lib/mixins.py` — the `cv_get_context()` override takes and forwards `location`.
- `src/crud_views/lib/view/button_data.py` — the mode read for all locations, the short-label rule.
- Nothing in `src/crud_views/templates/`.

### Tests

`tests/test1/test_button_data.py`:

- `context` and `list` honour a stamped `cv_label_mode` of `"both"` and `"label"`: `cv_label` is the short label,
  `cv_title` is absent, `cv_short_label` unchanged.
- Without a stamp they are `"icon"` with today's exact output (the existing `test_get` already pins it; keep it
  passing unchanged).
- `test_label_mode_always_icon_off_cards` (`test_button_data.py:131`) pins the behaviour this design removes —
  a stamped `"both"` forced back to `"icon"` off cards. Invert it, do not delete it: it becomes the test that the
  stamp is honoured.
- An invalid stamped value raises `ValueError` in all three locations, not only on cards.

A new config module in the image of `tests/test1/test_action_menus_config.py`:

- settings defaults are `{}`; `E106` for a list, a non-string key, an unknown mode; valid values pass.
- ViewSet rejects a bad shape and a bad mode value with `ValidationError`; accepts a good dict.
- Resolution: view beats ViewSet beats setting; `{}` on a view overrides a ViewSet dict; `None` falls through.
- `E211` for a string value on the view (the card-analogy mistake) and for a bad mode; `W291` for an unknown key
  on the view's own attribute and **not** for the same key on a ViewSet or setting.

Rendering, through the client as `test_action_menus_context.py` does:

- The publisher list toolbar with `{"create": "both"}`: the create button contains the icon and a visible
  `<span>Create</span>`, has no `title`, no `data-cv-tooltip` and no `visually-hidden` span; every other toolbar
  button is byte-identical to the unconfigured render. This is #216's "labelled and icon-only in the same
  toolbar" criterion.
- A `ContextButton` key (`home`) labelled via its configured key, proving decision 5.
- `"label"` mode on the toolbar renders the text without an icon.
- A list row with `{"detail": "both"}`: the detail button labelled, `update` and `delete` unchanged.
- The class table: with `list:secondary:both` registered and two secondary row buttons of different modes, the
  two render different `class` attributes. (Two same-variant buttons are easier to find in a row than in the
  toolbar, where `create` is usually the only primary.)
- A labelled key that is folded into the menu (inline keys exclude it) renders as a normal menu item: icon and
  short label, no error, and no `title` (the non-goal above, pinned as intended). An icon-mode key folded next
  to it keeps its `title`, which is what `test_active_item_in_menu` (`test_action_menus_context.py:53`) already
  asserts for an unconfigured toolbar; that test stays as it is.
- `{% cv_context_button "create" %}` in a project template renders the labelled button when the view labels
  `create`.
- The guardian test pages still render (they exercise the override).
- The eight goldens pass unchanged.

### Docs

- `docs/reference/settings.md` — two rows after the three `*_ACTIONS_INLINE` rows, pointing at `action_menus.md`
  and naming `E106`.
- `docs/reference/action_menus.md` — "Configuration" (line 22) gains the label-mode trio as a second table and a
  short example, with the resolution order and `{}` semantics stated once for both knobs; "Labels, icons and the
  active action" (line 79) stops saying toolbar items carry the full label as `title` — that is `icon` mode — and
  says which locations can show labels, that menu items render icon and short label in every mode, and that a
  labelled action has no `title` inline or folded; the system-check table (line 151) gains `E106`, `E211`,
  `W291`. This is the page #216 names.
- `docs/reference/buttons.md` — the leaf contract rows for `cv_label`, `cv_label_mode` and `cv_title`
  (lines 235-238): `cv_label_mode` is no longer "always `icon` for context and list"; `cv_label` for those two
  is the full label in `icon` mode and the short label otherwise. "A theme recipe" (line 295): the parenthetical
  "for the toolbar and rows only the `:icon` keys are read until #216" goes, and the recipe's `primary` guard —
  a leaf override whose whole purpose was to show the primary toolbar label — is replaced by the knob plus a
  `context:primary:both` class entry, which is the recipe this issue was filed to make possible. The system-check
  table (line 342) gains the three ids if it lists view-level checks (it lists `E210`, so yes).
- `docs/reference/card-list-view.md`, after "Label mode" (line 57) — one sentence: the toolbar and rows have
  their own, key-based knob, with a link.
- `docs/reference/context_buttons.md` — the custom-template paragraph (line 66): it now receives
  `cv_label_mode` for its key; the bundled filter toggle stays icon-only and passes the literal. The manual
  placement section: `{% cv_context_button %}` follows the view's label mode for that key.
- `CHANGELOG.md`, Unreleased → Added. Not Breaking: no default and no existing output changes, and theme leaf
  overrides keep working. One sentence for projects that override `cv_get_context()`: it has a new keyword-only
  `location` parameter that an override must accept and pass on.

### Issues

- **Before the PR opens**, #216's body is brought in line with what ships: its "Things to settle" list is
  settled (knob location, both locations, tooltip, short label) and should say so, with the names above. The
  acceptance criteria stay as written; they are met.
- The PR closes #216. #228 stays open; its checklist is ticked for #216 by whoever merges.
- `tabler-test` is downstream and out of scope; it is the first consumer. Its change is to set
  `CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE = {"create": "both"}` and move `btn-icon` from `context:primary` into
  `context:primary:icon`, and to drop the "accepted difference" row from its docs.

## Left to the builder

- `dict[str, LabelMode]` versus `dict[str, str]` plus a validator on the ViewSet fields.
- Whether to rename `cv_first_inline_keys()` to something location-neutral, and the exact signature by which
  `cv_resolved_actions()` learns its location.
- The exact wording of the three check messages.
- Whether `cv_get_action_label_mode()` raises for `"card"` or simply returns the icon default; nothing calls it
  with `"card"`.
- Test placement: a new module for config and rendering, or extending the `test_action_menus_*` modules.

## Calls I made (check these while reading)

- **A ViewSet layer**, which you did not ask for. The inline trio has it, the resolver exists, and a ViewSet
  that groups one model's views is the natural place for "every toolbar in this ViewSet labels `create`".
  Leaving it out would make this the one knob of its family with two layers.
- **The visible text is the short label.** "Create", not "Create new author". The long form is still the
  `title` in `icon` mode and the hidden text there, as today.
- **Keyed by configured key, not target key.** `{"home": "both"}` labels the home button, even though its
  `cv_key` is `"list"`.
- **No string shorthand** for "every action in this location".
- **The stamp lives in `cv_get_context(location=...)`**, so custom context-button templates see the mode too.
- **A labelled key folded into the menu loses its `title`.** The builder check found that the stamp travels
  into the menu and `menu_item.html` prints `cv_title`, which a labelled action does not have. I chose to keep
  that rather than add a mechanism that strips the mode for menu items: "a labelled action has no tooltip" then
  holds everywhere, and nothing changes for a key left at `icon`.
- **Manual placement honours the knob.** `{% cv_context_button %}` passes `location="context"` like the toolbar
  does. Raised by the builder check; the alternative is a documented tag that ignores a documented setting.
- **Three new check ids** rather than widening `E105` / `E208` / `W290`, whose messages describe a list shape.
