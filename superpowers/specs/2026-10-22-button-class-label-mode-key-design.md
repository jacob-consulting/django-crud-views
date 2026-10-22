# The button class table learns the label mode

Issue: #209. Siblings: #213 (landed — the three-state label mode this design keys on), #216 (the same three
states in the context toolbar and list rows, open, and explicitly waiting on this).

Date: 2026-10-22

## Intent

`crud_views/tags/button/action.html` asks the class table for a key that leaves out the one thing it already
knows:

```django
class="{% cv_button_class cv_location cv_variant %}{% if cv_active %} active{% endif %}{% if cv_flex %} flex-grow-1{% endif %}"
```

Three lines later the same template branches on `cv_label_mode` to decide whether the button renders an icon, a
text label, or both. So one class string has to serve all three renderings of a button in the same location and
variant, and a theme cannot say "square and padding-free when it is an icon, normally padded when it carries
text".

**Where it bites.** `@tabler/core@1.6.1`:

```css
.btn-icon{min-width:calc(var(--tblr-btn-line-height) + var(--tblr-btn-padding-y) * 2 + var(--tblr-btn-border-width) * 2);padding-inline-start:0;padding-inline-end:0}
```

`btn-icon` is required for a square icon button and wrong on a labelled one, whose text then sits on the
button's edges. The Tabler theme prototype (`crud_views_tabler` in the `tabler-test` project) has to guess per
variant, and its table says so out loud:

```python
"card:tertiary": "btn btn-sm btn-icon btn-ghost-secondary",  # the demo's only tertiary card action is icon-only
```

**Why now.** The issue was filed when a card button's label mode was a property of the theme author's knowledge:
`CardAction.no_label` was set in the view and a theme could read it off. #213 changed that. `label_mode` is now a
three-valued knob on `CardAction` and on the view (`cv_card_actions_label_mode`), so a project flips a card
action from `icon` to `both` and the theme's `btn-icon` becomes wrong with no theme change involved and no way
for the theme to have anticipated it. The guess is no longer merely inelegant; it is unsound.

The same gap is also the stated blocker for #216 — `context:primary` and `list:primary` in the Tabler table are
`btn-icon` throughout, so a labelled toolbar button is unstylable until this lands.

## Goals

- A theme or a project can give the same `location:variant` different classes per label mode, without overriding
  `tags/button/action.html`.
- Tables and `CRUD_VIEWS_BUTTON_CLASSES` written before this change keep working byte-identically.
- The mode vocabulary is #213's, used verbatim — no second spelling of the same three states.
- The key shape is final: #216 consumes it for `context` and `list` and invents nothing.
- A theme defines only the modes that differ from its base entry.

## Non-goals

- **Changing any default.** `DEFAULT_BUTTON_CLASSES` gains no mode keys. Bootstrap 5's `btn btn-*` classes work
  in all three modes, which is exactly why the gap was invisible until a second theme existed. No rendered
  output changes for anyone who does not add a mode key, and no golden moves.
- **Making labels reachable in `context` and `list`.** That is #216. This design makes `context:primary:both` a
  *valid and resolvable* key today; nothing can produce a `both` button outside cards until #216 lands, so the
  key is simply never hit.
- **The hard-coded utility classes in the leaf.** `{% if cv_active %} active{% endif %}` and
  `{% if cv_flex %} flex-grow-1{% endif %}` are Bootstrap names in a template that is supposed to hold none.
  #209's "Related, same leaf" section raises them; they are a separate change with a separate key shape question
  (`*:active`, `*:flex`) and must not be smuggled in here. File as a follow-up.
- **Mode keys on non-action slots.** `card:container`, `menu:item`, `card:menu-toggle`, `form:submit`,
  `card-order:toggle` and the rest do not vary by label mode — a container wraps buttons of mixed modes, a menu
  item always renders icon + label. The shape rule below rejects a mode segment on them rather than silently
  accepting a key that can never be read.
- **Wildcards.** No `card:*:icon`, no `*:*:icon`. A theme that wants one string across four variants writes a
  dict comprehension; `register_button_classes()` takes a plain dict.
- **A dedicated slot for the filter toggle.** `context:filter-toggle` would be conceptually cleaner than having
  a non-leaf button borrow the action key shape, but it is a new default key and it changes the filter's classes
  for any theme or project already styling it through `context:secondary`. Rejected as out of scope; revisit
  only with a reason of its own.

## Anti-goals

These would make the change a failure even if the acceptance criteria passed:

- **A second mode vocabulary.** Anything coarser than `LABEL_MODES` — an `icon` / `text` binary, a boolean, an
  `icon-only` flag — reintroduces the exact defect being fixed: the leaf knows one set of states and the table
  speaks another. It is also not retrofittable; widening a binary later means two vocabularies forever.
- **A silently unreadable key.** A theme writes `card:tertiery:icon` or `card:container:both` and sees no
  warning, then spends an afternoon on why its classes do not apply.
- **A fallback chain.** `both` → `label` → base, or mode → variant → location, is clever and undebuggable. One
  step.

## Decisions already taken

Settled in the brainstorming conversation and not open:

1. **Option A, a third key segment**, not option B's additive `icon-only` modifier key. B is smaller and covers
   Tabler's `btn-icon` case, which is purely additive — but the same Tabler table already has a non-additive
   case (`btn-ghost-danger` for an icon-only delete against a solid `btn-danger` for a labelled one), and with
   the fallback A costs the same number of keys today. B's advantage is one table entry; A's is the one that is
   hard to retrofit.
2. **The segment is the three `LabelMode` values** — `label`, `icon`, `both` — not a coarser split. `both` is
   the only mode with an icon beside text and is the one that might want a gap or flex utility the others have
   no use for. A theme for which `label` and `both` coincide writes the string twice, or builds the dict in a
   comprehension; that cost is local and does not leak into the mechanism.
3. **One fallback step, no chaining**: `location:variant:mode`, then `location:variant`.
4. **The mode segment is valid in all three locations from day one**, not card-only, so #216 inherits a working
   mechanism instead of widening one. Costs nothing: the leaf passes whatever `cv_label_mode` holds, and off
   cards that is always `"icon"`.
5. **#209 and #216 stay separate issues.** #216 has four unsettled questions of its own (where the knob lives,
   whether `list` and `context` are decided together, the tooltip, `cv_short_label`) and changes rendered
   markup. This one changes no markup and has a known blast radius. A tracking issue links #213, this, #216 and
   the leaf-utilities follow-up.
6. **The filter toggle passes a literal `"icon"`.** See "The filter toggle" below. It is the second caller of a
   `location:variant` key, and the decision settles what a theme's base `context:*` entry means.
7. **No `crud_views.W363`.** A check warning that a project's settings override of a base key is shadowed by a
   theme's mode key is deliberately not built. It needs a theme with mode keys *and* a project overriding
   exactly that base, and it would fire on configurations that are often deliberate. Documented instead, with
   the worked example under "Lookup". If it later turns out to bite, note that
   `button_class_check_messages()` already iterates `_THEME_BUTTON_CLASSES` and `_settings_layer()` separately,
   so the layers are available without restructuring.

## Design

### The key shape

```
location:slot            # unchanged, every key that exists today
location:variant:mode    # new, action buttons only
```

with `location ∈ LOCATIONS` (`context`, `list`, `card`), `variant ∈ VARIANTS` (`primary`, `secondary`,
`tertiary`, `danger`) and `mode ∈ LABEL_MODES` (`label`, `icon`, `both`). All three frozensets already exist
(`lib/view/button_data.py`, `lib/view/variant.py`, `lib/view/label_mode.py`); nothing new is defined.

That is 36 addressable mode keys over the 12 action keys. None of them is defined by default, and a theme
defines only the ones that differ from its base entry.

### Lookup

`get_button_class()` (`src/crud_views/lib/button_classes.py:85-89`) gains an optional third argument:

```python
def get_button_class(location: str, slot: str, mode: str | None = None) -> str:
    """Resolved classes for ``location:slot``, preferring ``location:slot:mode`` when that key is present."""
```

Resolution, against the already-merged dict from `get_button_classes()`:

1. If `mode` is truthy and `f"{location}:{slot}:{mode}"` is **present** in the dict, that entry is the answer.
   (Truthy, not "not `None`": a template that passes an undefined variable hands the tag `""`, and that must
   count as no mode rather than look up `card:tertiary:`.)
2. Otherwise `f"{location}:{slot}"`.
3. The existing value rule applies to whichever entry won: a `str` is returned as-is, `None` / `""` / a
   non-string yields `""`.

**Presence decides, not truthiness.** A mode key explicitly set to `None` means "no classes for this mode", the
same as `None` means everywhere else in this table, and does *not* fall through to the base. One rule for `None`
across every key beats a special case that only mode keys have.

**Specificity beats layer, and this needs saying out loud in the docs.** The three layers (defaults, theme,
settings) are merged per key *first*; the mode fallback runs on the result. So a project that sets
`CRUD_VIEWS_BUTTON_CLASSES = {"card:tertiary": "btn btn-sm btn-success"}` against a theme that defines
`card:tertiary:icon` does **not** recolour the icon-only tertiary card button — the theme's more specific key
still wins. The project overrides the mode key too, or sets it to the same string. This is the one genuinely
surprising consequence of the fallback and belongs in `buttons.md` as a worked example, not a footnote.

### The leaf

```django
class="{% cv_button_class cv_location cv_variant cv_label_mode %}{% if cv_active %} active{% endif %}{% if cv_flex %} flex-grow-1{% endif %}"
```

`cv_label_mode` is already in `LEAF_KEYS` and already validated: `cv_button_data()` raises `ValueError` for a
value outside `LABEL_MODES` and forces `"icon"` for every non-card location and for an empty label. The lookup
can therefore trust it and needs no validation of its own; an unknown mode would simply miss and fall back,
which is the right failure anyway.

### The filter toggle

`tags/context_action_filter.html:3` is the **second** caller that resolves a `location:variant` key:

```django
class="{% cv_button_class "context" cv_variant|default:"secondary" %}"
```

It is a `FilterContextButton` (`lib/view/buttons.py:296`) with its own `template`, rendered by
`_render_context_action()` (`templatetags/crud_views.py:162`) directly from the resolved action ctx. It never
passes through `cv_button_data()`, so it has no `cv_label_mode` — and it is permanently icon-only: two
`{% cv_icon %}` spans (open and close) plus a `visually-hidden` label.

It is also not a one-off. `ContextButton.template` and `template_code` are a documented, public mechanism
(`docs/reference/context_buttons.md:39,51,56`), and every custom context-button template a project writes is
rendered the same way: from the raw ctx, with no `cv_label_mode`. The filter toggle is simply the shipped
instance of that pattern, which is why the docs guidance below is about custom context templates in general,
with the filter toggle as the example.

**It passes a literal `"icon"`:**

```django
class="{% cv_button_class "context" cv_variant|default:"secondary" "icon" %}"
```

This is the decision that fixes what a theme's base `context:*` entry is *for*. If the filter kept reading the
base key while rendering icon-only, a theme would be forced to leave `btn-icon` in its base `context:*` entries
and express labelled buttons as mode keys — inverting the migration this design predicts for #216 (clean the
base, add mode keys for the exceptions), and making the base entry permanently unable to be the labelled form
in any location that has a non-leaf button. Passing `"icon"` keeps the base a pure fallback, and it states a
fact about the markup rather than working around one.

Consequence to document: a theme that defines `context:secondary:icon` restyles the filter toggle too. That is
correct — it is a square icon button and wants the same treatment as every other icon-only context button.

### Other callers

No other caller passes a mode, and none of their keys is `location:variant`: `actions_menu_toggle.html`
(`menu-toggle`), `menu_item.html` (`menu:item`), `container.html` (`container`), `actions_menu.html`
(`menu-wrapper`), `card_order.html` (`card-order:*`), `language_selector.html` (`language:toggle`),
`formsets/control.html` (`formset:*`) and the object-detail property button (`object-detail:property-detail`)
keep their two-argument calls.

`lib/crispy/buttons.py:17` calls `get_button_class(*(slot or self.slot).split(":", 1))` for `form:*` slots. A
trailing optional parameter leaves it working untouched; leave it alone rather than teach form slots about
modes.

### The template tag

`cv_button_class` is defined twice — `crud_views/templatetags/crud_views.py:425` and
`crud_views_object_detail/templatetags/crud_views_object_detail.py:108` (a deliberate copy so the
object-detail templates need no second `{% load %}`). Both gain the same optional third argument and keep
delegating to `get_button_class`. Keeping the two signatures identical matters more than the fact that
object-detail will never pass a mode.

### The check

`crud_views.W362` today warns for any theme or settings key not in `DEFAULT_BUTTON_CLASSES`. It becomes
shape-aware:

```
valid if key in DEFAULT_BUTTON_CLASSES
      or key == f"{location}:{variant}:{mode}" with location in LOCATIONS
                                               and variant  in VARIANTS
                                               and mode     in LABEL_MODES
```

So `card:tertiary:icon` passes, while `card:tertiary:iconn`, `card:container:icon`, `menu:item:both` and
`card:tertiary:icon:extra` all warn, as does every typo W362 catches today. The message should distinguish the
two failures — an unknown base key reads differently from a good base key with a bad mode segment — but it
stays one warning id. `DEFAULT_BUTTON_CLASSES` does not grow; it is still the list of keys the package ships
values for, and the docs table still prints it.

`crud_views.E361` (non-string value) is unchanged and already iterates the merged dict, so it covers mode keys
for free.

## Constraints

- Line length 120, double quotes, ruff format. `cv_` prefix on `CrudView` attributes.
- `get_button_class`, `get_button_classes` and `register_button_classes` are listed as public API in
  `docs/development/stability.md:30`. Adding an optional third parameter is backward compatible; removing or
  reordering the first two is not.
- `get_button_classes()` is cached and reset by `reset_button_classes_cache()` on `setting_changed`. The
  fallback must read through that cached dict, not add a second cache keyed by mode.
- **`button_classes.py` must not import `lib.view.*` at module level.** Verified, not hypothetical: importing
  any `crud_views.lib.view.<module>` runs `lib/view/__init__.py`, which imports `.base`, which needs the app
  registry (`AppRegistryNotReady` under bare settings). `button_classes.py` today imports only `django.*` and is
  importable with nothing but settings configured — `test_button_classes.py` and `crispy/buttons.py` rely on that
  lightness. There is no import *cycle* today (`lib/view` and `lib/viewset` never reach `button_classes`), but a
  module-level import of `LOCATIONS` / `VARIANTS` / `LABEL_MODES` would make the whole class table depend on
  `CrudView`'s import chain for the sake of one check. Resolve it one of two ways: a function-local import inside
  `button_class_check_messages()` (checks run after `django.setup()`, and `FilterContextButton.get_context()` at
  `lib/view/buttons.py:304` already uses the same house pattern), or move the three frozensets to a leaf module
  with no `lib.view` dependency. Either is fine; a module-level import is not.
- Django 4.2 / 5.2 / 6.0, Python 3.12–3.15. A `simple_tag` with a trailing optional argument is fine on all of
  them.

## Work

### Code

- `src/crud_views/lib/button_classes.py` — the third parameter and the fallback in `get_button_class()`; the
  shape rule in `button_class_check_messages()`.
- `src/crud_views/templatetags/crud_views.py` and
  `src/crud_views_object_detail/templatetags/crud_views_object_detail.py` — the third argument on both
  `cv_button_class` tags.
- `src/crud_views/templates/crud_views/tags/button/action.html` — pass `cv_label_mode`.
- `src/crud_views/templates/crud_views/tags/context_action_filter.html` — pass the literal `"icon"`.

### Tests

`tests/test1/test_button_classes.py`:

- `get_button_class("card", "tertiary", "icon")` returns the mode entry when it is registered and the base entry
  when it is not.
- A mode key registered as `None` returns `""` and does **not** fall back to a non-empty base.
- A mode of `None` (the two-argument call) never reads a mode key, even when one is registered.
- An unknown mode value falls back to the base rather than raising.
- Layer order: a settings mode key beats a theme mode key; a settings *base* key does not beat a theme *mode*
  key (the surprising case above, pinned as intended behaviour).
- W362 accepts `card:tertiary:icon` / `context:primary:both` / `list:danger:label` and warns for
  `card:tertiary:iconn`, `card:container:icon`, `menu:item:both`, `card:tertiary:icon:extra`.
- `EXPECTED_KEYS` at `test_button_classes.py:14` is unchanged — the defaults do not grow.

Rendering, in the card tests: one card view with two actions of the **same variant** and different label modes,
with a mode key registered for one of them, asserting the two buttons render different `class` attributes. This
is the acceptance criterion and the only test that proves the leaf passes the mode at all. The per-action
`CardAction.label_mode` beats the view's `cv_card_actions_label_mode` (`lib/views/card.py:47-52`), so one view
can hold both modes.

The filter toggle: with `context:secondary:icon` registered, `#cv-filter-toggle` renders the mode entry, and
with only `context:secondary` registered it renders the base. Worth its own test because the literal `"icon"`
there is a decision, not a mechanical consequence, and a future edit to that template could silently drop it.

`tests/test1/test_button_classes_templates.py:17` — `LITERAL` matches two quoted literal arguments and is used
by `test_every_literal_slot_in_templates_is_a_default_key`. `action.html` passes variables, so it is not matched
and the test keeps passing; confirm rather than assume, and leave the regex alone unless a shipped template
later passes a literal mode.

### Goldens

**None should move.** No default gains a mode key, so every rendered `class` attribute is byte-identical —
including the filter toggle, whose new literal `"icon"` finds no `context:*:icon` default and falls back.
`toolbar_publisher_list.html` contains `#cv-filter-toggle`, so the filter template edit is already covered by an
existing golden and needs no new one. A diff
in any of the eight `tests/test1/golden/action_menus/*.html` means the fallback is not returning the base entry
and is a bug, not a golden to regenerate. Worth a line in the PR description, because the regeneration command
rewrites all eight unconditionally.

### Docs

- `docs/reference/buttons.md`, "The class table" (line 46) — the key shape `location:variant[:mode]`, the three
  mode values with a pointer to the card label mode, the one-step fallback, and that no default defines a mode
  key. The "34 keys" sentence at line 77 stays true and should say so explicitly: mode keys are addressable, not
  shipped.
- `docs/reference/buttons.md`, "`CRUD_VIEWS_BUTTON_CLASSES`" (line 88) — the worked specificity-beats-layer
  example, and that `None` on a mode key means no classes rather than fall-through.
- `docs/reference/buttons.md`, "Rendering" (line 149) — the three-argument tag form.
- `docs/reference/buttons.md`, "A theme recipe" (line 271) and the system-check table (line 322) — the recipe's
  leaf override exists partly to vary classes by mode; say which part of it the mode key now replaces. Update
  the W362 row to "is not a known key or a valid `location:variant:mode`".
- `docs/reference/buttons.md` — one sentence that the filter toggle resolves `context:<variant>:icon`, so a
  theme's icon-only context classes reach it like any other icon-only context button.
- `docs/reference/context_buttons.md`, the `template` / `template_code` paragraph (line 56) — a custom
  context-button template is rendered from the raw action ctx and has no `cv_label_mode`, so one that resolves
  `context:<variant>` should pass its own mode literal (`"icon"` for an icon-only button); point at the shipped
  `context_action_filter.html` as the worked example.
- `docs/reference/theme.md`, "Buttons" (line 82) — one clause that the table also takes `location:variant:mode`
  keys, linking to `buttons.md`. Optional; the section defers to `buttons.md` already.
- `docs/reference/action_menus.md` needs **no** edit: it documents only the `menu-wrapper` and `menu-toggle`
  keys, neither of which gains a mode. Verified, not assumed.
- `CHANGELOG.md`, Unreleased — a feature entry, not a breaking one. Nothing existing changes behaviour.
- `tabler-test` is downstream and out of scope, but it is the first consumer and the change it wants is
  `card:tertiary:icon` plus dropping `btn-icon` from the base entry. Expect a follow-up there.

### Issues

These are part of this unit of work, done by whoever implements it, and they are ordering constraints on the
plan rather than optional paperwork:

1. **Before the PR opens:** rewrite #209's body. It is written against the pre-#213 boolean and a card-only
   framing, and it is the issue the PR closes, so the rewrite has to land first or the closed issue will
   describe something other than what shipped. The rewrite says: the segment is `LabelMode`-valued, valid on
   every `location:variant` key, with the one-step fallback and the shape-aware W362.
2. **A tracking issue** linking #213 (done), #209, #216 and the leaf-utilities issue below, recording the shared
   state model and that the key shape is final. It becomes the parent; #209 and #216 become sub-issues. The
   tracker stays open after this PR — #209 closes, the parent does not.
3. **A follow-up issue** for the leaf's hard-coded `active` / `flex-grow-1`, required by the non-goals above.
   Note it is four occurrences in three templates, not the two in one that #209's "Related" section describes:
   `tags/button/action.html:2` (both names), `tags/button/menu_item.html:2` and
   `snippets/card_order.html:14,19`. Also note that
   `test_no_button_class_literal_in_shipped_templates_python_or_js` is written to forbid exactly this but scans
   `btn`-prefixed tokens only, so all four pass it.

Draft bodies for 2 and 3 were written during brainstorming; they are unposted and need the author's approval
before anything is created on the tracker.

## Left to the builder

- Function-local import versus a leaf module for the three frozensets (see Constraints). Both satisfy the
  constraint; pick the smaller diff and say which in the commit.
- The exact wording of the two W362 messages and whether the mode-segment case carries a different hint.
- Whether `mode` is keyword-only in `get_button_class`. The template tag passes it positionally either way.
- Test placement: extending `test_button_classes.py` and an existing card test module versus a new module for
  the rendering test.

## Calls I made (check these while reading)

- **`None` on a mode key means no classes, not fall through.** The alternative — `None` falls back, `""` means
  none — gives projects an explicit escape hatch from a theme's mode key, at the cost of a second meaning for
  `None` that exists nowhere else in the table. Reversible, but it is a documented semantic either way, so it is
  better chosen now.
- **W362 validates shape rather than growing the 12 action keys in the defaults to 48.** This is what the issue proposed and I
  agree: shipping 36 empty-ish defaults to satisfy a membership test would make the docs table unreadable and
  imply the package has an opinion about modes it does not have.
- **The object-detail copy of the tag gets the argument it will never use.** Two tags with the same name and
  different signatures is a trap for anyone reading one and using the other.
- **No change to `cv_button_data()` or `LEAF_KEYS`.** `cv_label_mode` is already there and already validated;
  this design only routes it to the lookup. The mode reaching the table is therefore exactly the mode reaching
  the markup, by construction rather than by agreement.
- **`context:*:*` and `list:*:*` keys are valid and unreachable until #216.** The alternative — reject them
  until they can be produced — means #216 reopens the check and the docs. The cost is that a theme can define a
  key that does nothing yet, which is a smaller surprise than a key shape that changes under it.
