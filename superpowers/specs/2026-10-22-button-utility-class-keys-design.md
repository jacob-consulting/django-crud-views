# The button chain stops hard-coding Bootstrap utility classes

Issue: #227. Tracker: #228 (last open child). Siblings, all landed: #213 (three-state `LabelMode`), #209 (the
class table's `location:variant[:mode]` key, PR #229), #216 (context and list buttons learn the label mode,
PR #230).

Date: 2026-10-22

## Intent

#201 moved every class a theme restyles out of the shipped templates and into the class table. Seven Bootstrap
words survived in the button chain, all in templates the table already styles:

| Template | Word | Where |
|---|---|---|
| `tags/button/action.html` | `active` | appended when `cv_active` |
| `tags/button/action.html` | `flex-grow-1` | appended when `cv_flex` |
| `tags/button/action.html` | `visually-hidden` | the hidden label text in `icon` mode |
| `tags/button/menu_item.html` | `active` | appended when `cv_active` |
| `snippets/card_order.html` | `active` | the selected sort direction, twice |
| `tags/button/menu_item_label.html`, `tags/actions_menu_item_label.html` | `d-inline-block` | the icon placeholder span |
| `tags/actions_menu_toggle.html`, `tags/context_action_filter.html` | `visually-hidden` | the hidden label text |

The issue names the first two. The maintainer widened the scope to all four words on 2026-10-22, because every
one of them leaves the same hole: a theme on a framework that spells the word differently (Bulma `is-active`,
`is-sr-only`; Tailwind `sr-only`) has to copy the whole leaf to change one token. That copy is the recipe
`docs/reference/buttons.md` shows today, and every later change to the bundled leaf silently misses it.

The guard that exists for this, `test_no_button_class_literal_in_shipped_templates_python_or_js`, scans for
`btn`-prefixed tokens only, so it claims to forbid theme literals in templates while seven sit there. A word list
can never be that guard: the issue counted four words and the design recon found three more in the same leaves.

**Why now.** #209 and #216 made the table the single place a theme styles a button in every location and every
label mode. These seven words are the last reason a theme still overrides a leaf for looks. With them gone, the
theme recipe is classes only, and 1.0.0 can say so.

## Goals

- A theme restyles the active state, the stretched card button and the hidden label of an icon-only button from
  the class table, with no template override.
- The rendered output is unchanged for a project that sets none of the new keys. The one token that goes,
  `d-inline-block` on the icon placeholder, was dead weight: `.cv-icon-fw` already declares the display, and no
  golden holds it.
- A rendering guard proves that every class on a table-styled button element comes from the table or the `cv-`
  namespace, and keeps proving it for words nobody has listed yet.
- The theme recipe in the docs no longer overrides a leaf.

## Non-goals

- **The behaviour-bearing Bootstrap hooks in the same chain.** `dropdown-toggle` and `data-bs-toggle="dropdown"`
  on the menu toggle, `data-bs-popper-config`, `dropdown-menu dropdown-menu-end` on the menu list, and `d-none`
  on the filter toggle's two icon spans (toggled by `list.filter.js`). The issue draws the line at these and the
  maintainer kept it. They are named exemptions in the new guard and go to a follow-up issue (see Issues).
- **Bootstrap words outside the button chain.** `card mb-3` / `card-body` / `card-title` in `tags/card.html`,
  the `d-flex ... form-select` layout of the sort form, pagination, breadcrumb, the table template, the language
  selector's `dropdown-item ... active` items, and the `visually-hidden` table heads in the object-detail
  layouts. A whole-page theme audit is a separate decision the maintainer deferred on 2026-10-22.
- **A Bulma theme or a Bulma integration test.** Raised and deferred the same day. The guard below uses sentinel
  class names, not a real framework.
- **New check IDs.** `crud_views.W362` already reports an unknown key.

## Anti-goals

- A second spelling of any state. `active` and `flex` are table slots; nothing else learns them.
- A wildcard or shared key (`*:active`). #209 settled: no wildcards, no chaining. One key per location, like
  `container`.
- A mode segment on the new keys. `context:active:icon` is not a key and stays a `W362` typo, as today.
- Package CSS for a look a theme may want to swap. No rule joins the package stylesheets; a Bootstrap utility
  the markup uses is a table key with that utility as its default. (`.cv-icon-fw` stays: it is a sizing rule no
  framework utility provides, and it is not a look.)
- Changing what `cv_active` or `cv_flex` mean, or growing `LOCATIONS`.

## Decisions already taken

From tracker #228, binding here:

1. One vocabulary, `LabelMode`, three values. Untouched by this design.
2. The key shape is `location:slot` or `location:variant:mode`, resolved in one fallback step. The new keys are
   two-segment `location:slot` keys.
3. No default ships a mode key. Unchanged.
4. Nothing in the rendered output changes for a project that adds no key. Held: every new key defaults to the
   word the template wrote before.

From the maintainer on 2026-10-22: option A of #227 (keys in the table); `visually-hidden` and `d-inline-block`
are in scope; no Bulma work now; and, on the reviewer's finding that a package stylesheet rule would reach a
page only through `{% cv_css %}`, the Bootstrap class names go into the table rather than rules into the
package CSS.

## Design

### The keys

Nine rows join `DEFAULT_BUTTON_CLASSES`; the table grows from 34 to 43 keys:

| Key | Default |
|---|---|
| `context:active` / `list:active` / `card:active` | `active` |
| `menu:active` | `active` |
| `card-order:active` | `active` |
| `card:flex` | `flex-grow-1` |
| `context:hidden-label` / `list:hidden-label` / `card:hidden-label` | `visually-hidden` |

Per location, not shared, because a utility-first framework has no single word for "active": a highlighted
toolbar button, a highlighted menu item and a pressed sort toggle take different utilities there. `flex` exists
for `card` only: `cv_button_data()` sets `cv_flex` only at that location, and `CardAction.flex` is a card
concept. `context:flex` is not a key (`W362`).

`hidden-label` is the screen-reader text of an icon-only button: the action leaf in `icon` mode, the menu
toggle and the filter toggle. Every framework has one utility for it (`visually-hidden`, `is-sr-only`,
`sr-only`), so the three keys will usually hold the same value; they are still per location so the table keeps
one shape, and a theme lists only what it changes. The slot is named for its role, not for any framework's word.

The new keys are plain two-segment keys. `_action_key_parts()` requires the second segment to be a variant, so
`context:active:icon` falls through to the "not a known key" warning with no code change.

### The leaves

Every literal becomes a table lookup, the space moving inside the `if` with it:

```django
{# tags/button/action.html #}
class="{% cv_button_class cv_location cv_variant cv_label_mode %}{% if cv_active %} {% cv_button_class cv_location 'active' %}{% endif %}{% if cv_flex %} {% cv_button_class 'card' 'flex' %}{% endif %}"
```

```django
{# tags/button/menu_item.html #}
class="{% cv_button_class "menu" "item" %}{% if cv_active %} {% cv_button_class 'menu' 'active' %}{% endif %}"
```

```django
{# snippets/card_order.html, both toggles #}
class="{% cv_button_class 'card-order' 'toggle' %}{% if cv_order_dir == 'asc' %} {% cv_button_class 'card-order' 'active' %}{% endif %}"
```

`'card' 'flex'` is a literal pair on purpose: it documents that the slot is card-only and lets
`test_every_literal_slot_in_templates_is_a_default_key` cover it. A key a project sets to `None` or `""` leaves a
trailing space in the attribute. That is harmless HTML and the goldens canonicalise tokens; the leaf does not
work around it.

The hidden label span asks the table as well:

```django
{# tags/button/action.html, icon mode; tags/actions_menu_toggle.html #}
<span class="{% cv_button_class cv_location 'hidden-label' %}">{{ cv_label }}</span>

{# tags/context_action_filter.html, which is context-only #}
<span class="{% cv_button_class 'context' 'hidden-label' %}">{{ cv_action_label }}</span>
```

The icon placeholder in `tags/button/menu_item_label.html` and `tags/actions_menu_item_label.html` becomes
`<span class="cv-icon-fw" aria-hidden="true">`: `.cv-icon-fw` already declares `display: inline-block`, so
`d-inline-block` was dead weight and goes without replacement.

### Why not the package stylesheet

The first draft put a `.cv-visually-hidden` rule into `icons.css`. The builder check showed that a package rule
reaches a page only through `{% cv_css %}`, which the docs list as a tag the project places and which the
suite's own base template does not render, so the rename would have made every icon-only label visible in such
a project. The maintainer's answer, which also fits the rest of the design better: the markup keeps using
Bootstrap's utility by default and the table owns the name, so a theme swaps it like any other class and no
project loads anything new.

### The guard

`tests/test1/test_button_classes_templates.py` keeps its `btn` regex test unchanged: it still covers `.py` and
`.js`, which rendering cannot reach. It gains a rendering guard:

1. Build a sentinel table that maps every key of `DEFAULT_BUTTON_CLASSES` to one unmistakable token, for
   instance `x-card-flex` for `card:flex`, and install it with `override_settings(CRUD_VIEWS_BUTTON_CLASSES=...)`
   (the cache resets on `setting_changed`).
2. Render the chain with every flag on. At leaf level: `tags/button/action.html` for each location and each
   label mode with `cv_active=True` and (for `card`) `cv_flex=True`; `tags/button/menu_item.html` with
   `cv_active=True`; `tags/button/container.html`; `snippets/card_order.html` with `cv_order_dir` set to `asc`
   and to `desc`, unsigned. At page level, through the test client as a fully permitted user: a list page whose
   toolbar carries both the active `list` button and the filter toggle (the publisher list, as the
   `toolbar_publisher_list` golden shows; the default toolbar is `parent`, `list`, `filter`, `create`), with its
   row buttons and overflow menus; the author card page (the `flex=True` card action); the publisher order card
   page (the sort toggles); and the author detail page.
3. Assert the rule: for every element whose `class` contains a sentinel token, every class token on that element
   and on each of its descendant `span` elements is either a sentinel or starts with `cv-`. Under the sentinel
   table the hidden label spans carry a sentinel themselves, so a literal `visually-hidden` anywhere in the chain
   fails. Icon elements (`<i>`) are skipped: icons come from the icon registry, which has its own theme path.
4. Exemptions are a named constant, token to reason, and nothing else passes: `dropdown-toggle` on the menu
   toggle (Bootstrap's dropdown behaviour hook, kept with `data-bs-toggle`, follow-up issue) and `d-none` on the
   filter toggle's icon spans (toggled by `list.filter.js`, same follow-up).

The sweep is the negative half. The positive half, that the keys are wired, lives in the existing leaf and page
tests: register `context:active` as `is-active` and see it on the active toolbar button; `card:flex` on the
stretched card action; `menu:active` on an active menu item; `card-order:active` on the selected toggle;
`list:hidden-label` as `sr-only` on a row button's label span, the menu toggle's and the filter toggle's.

### Checks

None added. `W362` covers a typo in a new key and the mode-segment misuse. One test pins that
`context:active:icon` is reported.

## Constraints

- ruff: 120 columns, double quotes; the pre-commit hook formats on commit.
- The goldens under `tests/test1/golden/action_menus/` do not move: every default is the word the template
  wrote before, and no golden holds `d-inline-block` (every menu item there has an icon). The golden test runs
  unchanged and must pass; `CV_UPDATE_GOLDEN` is not used.
- Run the suite with `pytest tests -n auto`.
- No JavaScript and no stylesheet changes, so neither the Node 22 vitest run nor any asset work is needed.

## Work

### Code

- `src/crud_views/lib/button_classes.py`: nine rows in `DEFAULT_BUTTON_CLASSES`.
- The seven templates listed under The leaves.

### Tests

- `tests/test1/test_button_classes_templates.py`: the rendering guard; the literal-slot test picks the new
  literal pairs up by itself; the `>= 15` lower bound may rise.
- `tests/test1/test_button_leaves.py`, `test_card_order.py`, `test_context_button_active.py`, the label-mode
  render tests and `test_template_a11y.py`: their default-markup assertions stay true; the ones whose subject is
  one of the new keys register a non-default value so the test proves the wiring (the positive half above). Any
  test that asserted `d-inline-block` drops it.
- `tests/test1/test_button_classes_checks.py`: `context:active:icon` is `W362`.
- The golden test, unchanged and green.

### Docs

- `docs/reference/buttons.md`: the nine rows in the table; "34 keys" becomes 43; the paragraph that lists what
  stays in the templates drops `active` and `flex-grow-1`, keeps `dropdown-toggle` and `data-bs-toggle`; the
  leaf contract rows for `cv_active` and `cv_flex` name the keys, and the `icon` mode row names `hidden-label`;
  the theme recipe loses its leaf override entirely and registers `context:active`, `context:hidden-label` and
  friends instead, with the sentence that an override is for markup that differs, not for a word.
- `docs/reference/theme.md`: the worked example registers classes and overrides nothing.
- `docs/reference/action_menus.md`: the split-toggle example renders its hidden label through the key.
- `docs/reference/card-list-view.md`: `flex` adds the `card:flex` classes.
- `docs/reference/javascript.md`: the mention of a `visually-hidden` label, if it refers to the package's span,
  points at the key.
- `CHANGELOG.md`, Unreleased, in the file's existing sections: the nine keys and what they default to; the
  `d-inline-block` removal; the note that a project override of a leaf keeps rendering whatever it holds.

### Issues

- #227: body brought in line with what ships before the PR opens, as with #216. The PR closes it; GitHub ticks
  the tracker's checkbox.
- A follow-up issue for the Bootstrap words that remain in the button chain because they carry behaviour:
  `dropdown-toggle`, `data-bs-toggle`, `data-bs-popper-config`, `dropdown-menu dropdown-menu-end`, `d-none`
  with `list.filter.js`, and the language selector's `dropdown-item ... active`. It records that the whole-page
  audit (Bulma) is a separate decision, deferred 2026-10-22, and links the guard's exemption constant as the
  list to empty.

## Left to the builder

- Test names, helper placement and whether the page-level sweep reuses the golden test's page helpers.
- How the exemptions are keyed (token only, or token plus a selector), as long as each has a written reason.
- The exact sentinel scheme, as long as a sentinel cannot collide with a real class.
- Commit granularity, one commit per plan task as usual.
- Whether to add the positive assertions to existing tests or to one new parametrised test.

## Calls I made (check these while reading)

- Per-location keys rather than one shared key, for `active` and for `hidden-label` alike.
- The slot name `hidden-label` for the screen-reader text, named for its role rather than any framework's word.
- `'card' 'flex'` as a literal pair in the leaf; no `flex` key at other locations.
- `d-inline-block` dropped without replacement, relying on `.cv-icon-fw`, which stays a package class.
- The goldens stay byte-identical; the golden test is the proof.
- The regex guard stays as it is; the rendering guard is added beside it.
- `dropdown-toggle` and `d-none` are named exemptions and a follow-up, not part of this change.
- The language selector items stay out: they also hard-code `dropdown-item` and belong with the dropdown
  follow-up.
- No new check ID.
