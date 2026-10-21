# Card buttons: a three-state label mode

Issue: #213. Siblings: #209 (class table cannot tell the modes apart), #216 (the same gap in the
context toolbar and list rows, split out of #213 and out of scope here).

Date: 2026-10-21

## Intent

`crud_views/tags/button/action.html` ends in an exclusive choice:

```django
cv-key="{{ cv_key }}">{% if cv_label_visible %}<span>{{ cv_label }}</span>{% else %}{% cv_icon cv_icon %}<span class="visually-hidden">{{ cv_label }}</span>{% endif %}
```

A labelled card button renders text and throws away the `cv_icon` that `cv_button_data()` computed two lines
earlier (`src/crud_views/lib/view/button_data.py:51,65`). There is no way to get text *and* icon on an inline card
button without overriding the leaf, and `no_label=True` only flips the choice the other way.

The package already disagrees with itself about this. The same card action, with the same label, renders icon +
text when it is folded into the overflow menu (`tags/button/menu_item_label.html`) and text only when it is kept
inline. "On cards, buttons with text never have an icon" is one downstream project's UI/UX verdict. It is right
for that project; it should not be a hard rule in the shared leaf that every project renders through.

**Why now.** The Tabler theme prototype (`crud_views_tabler` in the `tabler-test` project) used to carry its own
leaf override and gave up icons-with-text when it dropped it in favour of stock markup. Its own documentation
records the loss as an accepted difference (`docs/crud_views_tabler.md:90`):

| Where | Before | Now |
|---|---|---|
| Labelled card buttons ("Open", "Edit") | icon plus label | label only |

Those are `CardAction(key="detail", label="Open", variant="primary", flex=True)` and
`CardAction(key="update", label="Edit")` on `CustomerCardListView`; the third action,
`CardAction(key="delete", no_label=True, variant="tertiary")`, must stay icon-only on the same card. That is why
the knob has to be reachable per action and not only per view.

## Goals

- An inline card button can render label and icon together, configured from the project, without overriding
  `tags/button/action.html`.
- The three states are one concept with one vocabulary, from the author-facing API through the leaf contract to
  #209's class-table key.
- A card view sets the default for its buttons; an individual `CardAction` overrides it.
- `CardAction(no_label=True)` keeps working.

## Non-goals

- Context (toolbar) and list (row) buttons. `cv_label_visible` is hard-wired to `card`
  (`button_data.py:36,51`), and lifting that is #216. Nothing here should make #216 harder, and #216 is expected
  to reuse this vocabulary rather than invent a second mechanism.
- The class-table key (#209). This design *decides the shape* #209 needs — a mode value it can use verbatim as a
  third key segment — but does not change `get_button_class()` or `crud_views.W362`.
- A project-wide `CRUD_VIEWS_*` setting for the default. Explicitly rejected: a downstream project that wants one
  policy everywhere writes a base card view class, which a developer cannot forget the way they can forget a
  setting.
- Menu items. `menu_item_label.html` already renders icon + label and is unaffected.

## Anti-goals

These would make the change a failure even if the acceptance criteria passed:

- Two independent booleans in the leaf contract. Two flags for three states leaves a fourth, meaningless state
  (neither label nor icon — a blank button) that has to be validated away, which is the shape this change exists
  to remove. #209's comment on this issue says the same from the class-table side.
- A labelled card button whose accessible name is duplicated, or which announces its icon.
- A default that is accidental rather than chosen. The default markup changes here; it changes because it was
  decided, and the goldens are regenerated to say so.

## Decisions already taken

These were settled in the brainstorming conversation and are not open:

1. **The default is label + icon.** A labelled inline card button renders its icon by default. This is a DOM
   change for every card with a labelled button, and the goldens are regenerated. Rationale: it is the behaviour
   the Tabler theme lost and wants back, and it matches what the overflow menu has always done for the same
   action.
2. **Two layers, no setting.** A view attribute sets the default; a `CardAction` field overrides it per action.
   The project whose designer ruled against icons-with-text sets the view attribute (on a shared base card view
   class) and is done.
3. **One tri-valued field, not a bool pair.** The author-facing field is `label_mode`, with the same three values
   as the leaf contract's `cv_label_mode`. An earlier proposal of `no_label: bool` + `icon: bool | None` was
   rejected for the reason in the anti-goals.
4. **`no_label` survives as an alias** for `label_mode="icon"`, documented as superseded, with a check that fires
   if both are set on one action.

## Design

### The three states

| `cv_label_mode` | Renders | Today's equivalent |
|---|---|---|
| `"both"` | icon, then the visible label | *new* |
| `"label"` | the visible label only | `cv_label_visible` true |
| `"icon"` | the icon, plus a `visually-hidden` label | `cv_label_visible` false |

### Author-facing API

`CardListView` gains:

```python
cv_card_actions_label_mode: str = "both"   # default label mode for this view's inline card buttons
```

`CardAction` (`src/crud_views/lib/view/card.py`) gains:

```python
label_mode: str | None = None   # None: inherit the view's cv_card_actions_label_mode
no_label: bool = False          # superseded: equivalent to label_mode="icon"
```

Written out, the Tabler case becomes:

```python
class CustomerCardListView(...):
    cv_card_actions_label_mode = "both"          # or omitted: it is the default
    cv_card_actions = [
        CardAction(key="detail", label="Open", variant="primary", flex=True),
        CardAction(key="update", label="Edit"),
        CardAction(key="delete", label_mode="icon", variant="tertiary"),
    ]
```

and the project with the designer:

```python
class ProjectCardListView(CardListViewPermissionRequired):
    cv_card_actions_label_mode = "label"
```

### Resolution

`CardListView.cv_get_card_action_data()` (`src/crud_views/lib/views/card.py:41-78`) already flattens a
`CardAction` into the unresolved context dict, and already writes `cv_no_label` in both of its branches (the
`child_name` branch at line 59 and the `action.key` branch at line 77). It resolves the mode in the same two
places and writes `cv_label_mode` instead:

```
action.label_mode if action.label_mode is not None
else "icon" if action.no_label
else self.cv_card_actions_label_mode
```

`cv_button_data()` (`button_data.py`) then:

- `"icon"` for every non-card location, unconditionally — this is what keeps #216 out of scope and keeps
  the toolbar and row goldens still.
- on cards, `ctx.get("cv_label_mode")`, falling back to `"both"`.
- forced to `"icon"` when the resolved `label` is empty. This preserves today's `bool(label)` guard in
  `label_visible`: a card action with no label text has nothing to show.
- **`cv_no_label` is no longer a leaf input.** `cv_button_data()` reads `cv_label_mode` and nothing else, and
  raises `ValueError` if `cv_no_label` is present in `ctx`, naming `CardAction.label_mode` / `cv_label_mode` as
  the replacement. The function already raises `ValueError` for an unknown `location`, so this is in character.
  Rationale: the fallback is `"both"`, so quietly ignoring the key would turn a hand-built ctx with
  `cv_no_label=True` into a silently wrong button — icon *and* text where the author asked for icon only. A
  loud failure at render time is the only way to make that impossible without carrying a legacy resolution
  rung, which #216 would then inherit and have to decide per location. The guard is transitional and can be
  dropped at 1.0. `CardAction.no_label` is unaffected: it is translated during resolution and never reaches
  `cv_button_data()`.
- `cv_title` (and with it `data-cv-tooltip`) is set when and only when the mode is `"icon"`. A `"both"` or
  `"label"` button has its name on screen and gets no tooltip, which is the behaviour that falls out of the
  existing rule rather than a new one.

### Leaf contract

`LEAF_KEYS` gains `cv_label_mode` and **loses `cv_label_visible`**. The leaf branches on the mode:

```django
cv-key="{{ cv_key }}">{% if cv_label_mode == "icon" %}{% cv_icon cv_icon %}<span class="visually-hidden">{{ cv_label }}</span>{% elif cv_label_mode == "both" %}{% if cv_icon %}{% cv_icon cv_icon %} {% endif %}<span>{{ cv_label }}</span>{% else %}<span>{{ cv_label }}</span>{% endif %}</{{ cv_tag }}>
```

Accessibility: `render_icon()` emits `<i class="…" aria-hidden="true">` (`src/crud_views/lib/icons.py:203`), so in
`"both"` mode the icon is already hidden from assistive technology and the visible `<span>` is the only
accessible name — no `visually-hidden` span, no duplication. Verified, not assumed. One caveat for the docs: a
project-supplied renderer registered through the icon library config is not forced to emit `aria-hidden`, so the
renderer contract should say it must.

Degradation: `render_icon(None)` returns `""` (`icons.py:206-209`), so a `"both"` action whose target view has no
`cv_icon_action` cannot produce a broken icon. The `{% if cv_icon %}` guard above exists only to keep the
separator space out of that case, so an iconless `"both"` button renders byte-identical to `"label"`.

Separator: a literal space between icon and label, as `menu_item_label.html` already does. The leaf gains no
class name — `#209`'s "Related, same leaf" section wants the two hard-coded Bootstrap utilities out of this
template, not a third one in.

## Constraints

- Line length 120, double quotes, ruff format; `cv_` prefix on all `CrudView` class attributes.
- `cv_button_data()` must not mutate `ctx` (its docstring promises this).
- Django 4.2 / 5.2 / 6.0, Python 3.12–3.15. `{% elif %}` with a string comparison is fine on all of them.
- The package is 0.x alpha, which is what makes removing `cv_label_visible` from the contract acceptable.

## Work

### Code

- `src/crud_views/lib/view/card.py` — `CardAction.label_mode`; a `model_validator` rejecting `no_label=True`
  together with an explicit `label_mode`, and an unknown `label_mode` value.
- `src/crud_views/lib/views/card.py` — `cv_card_actions_label_mode`; resolution in both branches of
  `cv_get_card_action_data()`.
- `src/crud_views/lib/view/button_data.py` — `cv_label_mode` in `LEAF_KEYS`, `cv_label_visible` out; the
  resolution above; `cv_title` keyed on `"icon"`.
- `src/crud_views/templates/crud_views/tags/button/action.html` — the three-way branch.
- A system check for `cv_card_actions_label_mode` on a card view, alongside the existing card checks in
  `CardListView.checks()`.

### Tests

`tests/test1/` — one card view rendering all three states, asserting per `cv-key`: `<i>` count and visible text.

- `label_mode="label"` → 0 icons, visible text, no `title`/`data-cv-tooltip`.
- `label_mode="icon"` (and separately `no_label=True`) → 1 icon, `visually-hidden` label, `title` present.
- `label_mode="both"` → 1 icon *and* visible text, no `visually-hidden` span, no `title`.
- The view default applies where no `CardAction` overrides it, and the override wins where it does.
- An action with no icon in `"both"` mode renders label-only without raising.
- The validator rejects `no_label=True, label_mode="label"`.
- `cv_button_data()` raises `ValueError` when `ctx` carries `cv_no_label`. `tests/test1/test_button_data.py:86-97`
  calls `cv_button_data(base(cv_label="Details", cv_no_label=...), "card")` directly today; rewrite those two
  tests — one asserting the raise, one driving the three modes through `cv_label_mode` instead.

### Goldens

Regenerate `tests/test1/golden/action_menus/cards_author_full.html`, `cards_author_disabled.html`,
`cards_publisher_child.html`. The toolbar and list goldens must **not** move; a diff in
`list_full.html`, `list_disabled.html`, `toolbar_*.html` means the non-card path changed and is a bug.

Mechanics, because the guard above is easy to defeat: `CV_UPDATE_GOLDEN=1 pytest
tests/test1/test_action_menus_golden.py` rewrites **all eight** goldens unconditionally
(`test_action_menus_golden.py:77-82`), card and non-card alike. So the check is a `git diff` *after*
regeneration showing changes confined to the three `cards_*.html` files. A blanket regen followed by a blanket
commit would silently absorb the very non-card regression this is guarding against.

### Docs

- `docs/reference/buttons.md` — the `LEAF_KEYS` table at line 213 (replace the `cv_label_visible` row) and the
  leaf listing. Add the renderer `aria-hidden` requirement.
- `docs/reference/buttons.md`, "A theme recipe" (lines 267-300) — **not** a stale copy of the bundled leaf. It is
  a deliberate `myapp_theme` override whose intro promises a framework that "wants `button is-*` classes and
  shows the label of `primary` buttons next to the icon", so `is-active` and the `{% if cv_variant != "primary" %}`
  guard are the example's own customizations, not drift. Port it to `cv_label_mode` and keep what it
  demonstrates: because non-card locations are forced to `"icon"`, the variant guard ports verbatim and still
  does exactly what the prose says. Add a sentence that the card half of this trick is no longer a reason to
  override the leaf, and that the toolbar half stops being one when #216 lands.
- The prose under that recipe (line 299, "keep the `cv_label_visible` branch (cards with a visible label)") is
  overrider guidance that goes stale with the key; rewrite it for `cv_label_mode`.
- `docs/reference/card-list-view.md` — `cv_card_actions_label_mode` in the view attribute table; replace the
  `no_label` row (line 50) with `label_mode` and mark `no_label` superseded; update the example at line 30.
- `docs/reference/action_menus.md:84` — `CardAction.variant`, `flex` and `label_mode` apply to inline card
  buttons only.
- `CHANGELOG` — the new default markup as a behaviour change, and `cv_label_visible` leaving the leaf contract as
  a breaking change for projects that override `action.html`.
- `tabler-test` is downstream and not part of this change, but its `docs/crud_views_tabler.md:90` row and
  `customers/views.py:89-91` are the first consumer; expect a follow-up there.

## Left to the builder

- Whether `label_mode` is a `Literal["label", "icon", "both"]` or a `str` validated in the model validator. The
  `Literal` gives a better Pydantic error for free; the `str` matches how `variant` is typed today
  (`variant: str | None`, checked by `variant_check`). Pick for consistency with whichever the package treats as
  the house style, and say which in the commit.
- The exact system-check id and message, following the existing numbering.
- Test placement: extending an existing card test module versus a new one.

## Calls I made (check these while reading)

- **The `buttons.md` theme recipe is ported, not flattened to stock.** It keeps its `button is-*` classes and
  its primary-label-next-to-icon behaviour, because the intro prose promises both and the variant guard still
  works off cards. The alternative readings — flatten it to stock, or re-point it at a different reason to
  override the leaf — are bigger docs rewrites than this change needs.
- **The view attribute is named `cv_card_actions_label_mode` (plural `actions`).** Resolved after the first
  implementation shipped under the singular `cv_card_action_label_mode`: the question was raised here, the plan
  then treated the singular as settled without answering it, and the rename landed separately once it was put
  to the author. The plural matches the neighbouring view-wide setting over all of a card's actions
  (`cv_card_actions_inline`); the singular belongs to the template tags (`cv_card_action`,
  `cv_card_action_group`). Nothing had been released under the old name, so no alias was kept.
- **`cv_label_visible` is removed from `LEAF_KEYS` rather than kept as a derived alias.** Note this is the one
  place the design contradicts #213's own text, which proposed keeping `cv_label_visible` as-is and adding a
  second flag beside it. The three-state decision is what changed it. Keeping both would mean
  documenting which one a leaf override should branch on, and the point of the change is one source of truth.
  Costs a breaking-change note for anyone overriding `action.html`. Reversible cheaply if you would rather keep
  it as `mode != "icon"`.
- **`no_label=True` plus an explicit `label_mode` is a validation error, not a precedence rule.** A silent winner
  hides a config mistake.
- **An empty label forces `"icon"`**, preserving today's `bool(label)` guard, rather than rendering an empty
  `<span>`.
- **A literal space separates icon and label**, matching `menu_item_label.html`, rather than a margin utility
  class in the leaf.
- **`"both"` gets no tooltip.** It falls out of the existing `cv_title` rule; the issue asked for this to be
  confirmed rather than assumed, and it is confirmed as intended.
