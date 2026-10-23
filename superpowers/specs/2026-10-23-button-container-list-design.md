# Button container: list markup per button and a lone button without a container

Issue: #261.

Date: 2026-10-23

## Intent

`tags/button/container.html` renders every button group (context toolbar, list row, card) as one element with the
buttons as direct children. Some design systems build a button row as a list, and leave the row out entirely when
there is only one button:

```html
<!-- two or more items -->
<div class="btn-row">
    <ul>
        <li><a class="btn …">…</a></li>
        <li><a class="btn …">…</a></li>
    </ul>
</div>

<!-- exactly one item: no row, the bare button -->
<a class="btn …">…</a>
```

The row styles apply to `.btn-row > ul > li`; a lone button inside a row is drawn as the first/last segment of a
group, which is wrong for a single action. Today a theme can only get this by copying `tags/context_actions.html`,
`columns/actions.html` and the card's `card_actions` block and counting visible actions in its own template tags —
the copy-the-template situation 1.0 otherwise removes. The theme should get it from its class table instead.

The maintainer's focus words for this series apply: maintainability, low complexity, easy to theme downstream, and
no more upstream surface than the issue needs.

## Goals

- A theme switches a location's container to list markup (`<ul>` inside the container, one `<li>` per item) with
  class-table keys only, no template override.
- A theme can make a group of exactly one rendered item render bare: no container, no list, just the item.
- Both work for the three container locations `context`, `list` and `card`. All three use the list shape in the
  motivating theme. The single-item rule matters for `context` and `list`; `card` gets it for the same design rule
  but has lower priority (in practice every card there has several actions).
- With nothing configured, the markup is byte-for-byte what it is today.

## Non-goals

- `menu`, `formset` and `card-order` containers: not affected.
- Buttons rendered on their own outside a container (`{% cv_context_button %}`, `{% cv_context_action %}`,
  `{% cv_list_action %}`): they never get an `<li>`. The `<li>` comes from `container.html`, never from a button leaf.
- A marker on a bare lone button. The issue proposed moving `cv-<location>-container="true"` onto the button when the
  container is dropped. Nothing in the package reads that attribute (no JS, no test; `container.html` is the only
  place that writes it), and putting it on the button would have to reach every button leaf including
  `template_code` buttons such as the filter toggle. **Decided with the maintainer: a bare lone button carries no
  marker; add one later if something needs it.**
- Changing the zero-item case. A group with no items renders exactly as today.

## Anti-goals

- A second copy of the button / menu rendering inside `container.html` that can drift from the normal path: the list
  and bare branches render items with the same `cv_render_button` / `cv_actions_menu` calls as today.
- Counting by rendered HTML. The count is by item data (see below), not by inspecting output.

## Decided: class-table keys (not an overridable template)

**Decided with the maintainer.** The alternative — pass the item count into `container.html` and let a theme override
that one file — adds less upstream, but every theme would re-write the loop, the menu's placement and the bare
branch, and that copy would drift. Keys keep the behaviour in the package and tested there.

### The keys

For each `<location>` in `context`, `list`, `card`:

| Key | Default | Meaning |
|---|---|---|
| `<location>:container` | today's value | class of the outer element (unchanged) |
| `<location>:container-list` | `None` | `None`: no list (today). A str (including `""`): the items sit in a `<ul>` inside the container, `class` = the value; `""` renders `<ul>` with no `class` attribute |
| `<location>:container-item` | `""` | class of each `<li>`; only read when `container-list` is a str. `""` renders `<li>` with no `class` attribute |
| `<location>:container-single` | `"container"` | `"container"`: one item renders inside the container as now. `"bare"`: one item renders with no container and no list |

All nine new keys go into `DEFAULT_BUTTON_CLASSES` so W362 (unknown key) does not fire when a theme or settings set
them. `DEFAULT_BUTTON_CLASSES` is annotated `dict[str, str]`; widen it to `dict[str, str | None]` for the `None`
defaults.

`container-list` needs the None-vs-`""` distinction that `get_button_class()` collapses (it returns `""` for both).
Read the raw value from `get_button_classes()` for this key; do not change `get_button_class()`.

`container-single` is a mode word, not classes, in the class table. Precedent: `*:icon-host` is a format string and
has its own check (E363). Add a check (next free id, E364): a `*:container-single` value that is not `"container"`
or `"bare"` is an Error. `None` / `""` are treated as `"container"` (no error) — builder's call whether to warn.

The `:container-*` keys are base keys only; no label-mode variants (`card:container-list:icon` means nothing).

### Counting items

An item is one inline button or the menu toggle:

```
items = len(cv_buttons) + (1 if cv_group and cv_group.menu else 0)
```

Hidden actions are already dropped before the split (`cv_resolve_action` in `cv_get_*_action_group`;
`cv_split_actions` documents it), so this is the count of rendered items with no extra visibility logic. A context
button whose own `template_code` happens to render nothing still counts as one item; that is accepted (rendering to
inspect output is an anti-goal).

- `container-single = "bare"` applies only when `items == 1`. One inline button **plus** a menu is two items and
  keeps the container. A group whose only item is the menu (everything folded) renders the menu bare.
- `items == 0`: as today (empty container), regardless of keys. This includes a card whose group is `None` (a view
  with no card actions).

### Markup

List mode, two buttons and a menu (`container-list = "x"`, `container-item = "y"`):

```html
<fieldset class="{container}" aria-label="Actions" cv-context-container="true">
    <ul class="x">
        <li class="y">{button}</li>
        <li class="y">{button}</li>
        <li class="y">{menu}</li>
    </ul>
</fieldset>
```

- The menu's `<li>` is emitted only when the group has menu items (no empty `<li>`).
- The outer tag stays what the caller passes (`fieldset` with `aria-label` for context and list, `div` for card),
  and `cv-<location>-container="true"` stays on it. List semantics are added inside, not replacing the fieldset.
- Bare: the single item's own markup (the button leaf output, or the `actions_menu.html` output), nothing around it.
- Default (no keys): exactly today's output, including whitespace, so existing golden files don't change. Golden
  files under `tests/test1/golden/` that include a container must still pass unchanged.

### Where the logic lives (builder's call, within these limits)

The three call sites (`tags/context_actions.html`, `columns/actions.html`, `tags/card.html` `card_actions` block) keep
their single `{% include "crud_views/tags/button/container.html" with … %}` line unchanged; all new behaviour is in
`container.html` plus whatever small Python helper it uses. A simple tag that returns the resolved layout for a
location and group (list class or None, item class, bare yes/no) is the expected shape; keep the template readable
and the Python small. Themes that already override `container.html` keep working (they just don't get the feature).

## Constraints

- Django 4.2 / 5.2 / 6.0, Python 3.12+. Line length 120, ruff.
- Not breaking: defaults reproduce today's markup. No `### Breaking` changelog entry, so `docs/migrating-1.0.md` is
  not touched.
- Don't name downstream / client projects anywhere in code, docs, changelog or tests.

## Tests

- Default keys: context, list and card containers render as today (existing golden files unchanged).
- `container-list` set to a class, and to `""` (`<ul>` with no class attribute); `container-item` set and unset.
- Menu as its own `<li>`; no `<li>` for an absent menu.
- `container-single = "bare"`: one inline button → bare button; one inline button + menu → container; only the menu
  → bare menu; a hidden action does not count (two configured, one hidden → bare).
- `container-single` and `container-list` together with one item → bare (no list either).
- Each of `context`, `list`, `card`.
- `{% cv_context_button %}` outside a container never gets an `<li>` with `container-list` set.
- E364 for a bad `container-single` value; no W362 for the new keys.

## Docs

- `docs/reference/buttons.md`: the three new slots in the key table, with the list / bare markup example.
- `docs/reference/theme.md`: a short "button row as a list" recipe using `register_button_classes`.
- `CHANGELOG.md` Unreleased → Added: one entry referencing #261.

## Left to the builder

- Exact helper name and whether it is a simple tag or a context computed in Python.
- Whether `None` / `""` for `container-single` warns.
- The check id if E364 is taken.
