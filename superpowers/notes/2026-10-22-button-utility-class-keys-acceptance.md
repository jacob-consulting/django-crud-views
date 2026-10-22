# Acceptance report — the button chain's utility classes move into the class table (#227)

Spec: `superpowers/specs/2026-10-22-button-utility-class-keys-design.md`. Plan:
`superpowers/plans/2026-10-22-button-utility-class-keys.md`. Tracker #228, last open child; after #216 (PR #230).

## Goals (spec)

1. **A theme restyles the active state, the stretched card button and the hidden label of an icon-only button
   from the class table, with no template override.** Nine keys with the Bootstrap words as defaults
   (`test_utility_slots_default_to_the_bootstrap_word`, `test_default_table_is_complete` at 43 keys,
   `tests/test1/test_button_classes.py`). Each key proven wired with a non-default value: `context:active`,
   `card:active`, `card:flex` (`test_active_and_flex_come_from_the_table`), `menu:active`
   (`test_menu_item_active_comes_from_the_table`), `list:hidden-label` on a row button
   (`test_hidden_label_comes_from_the_table`), `list:hidden-label` on the row menu toggle and
   `context:hidden-label` on the filter toggle (`test_toggles_hidden_label_comes_from_the_table`),
   `card:hidden-label` on an icon-mode card action (`test_card_icon_mode_hidden_label_comes_from_the_table`), all in
   `tests/test1/test_button_leaves.py`; `card-order:active` on the selected sort toggle
   (`test_card_order_toolbar_active_class_comes_from_the_table`, `tests/test1/test_card_order.py`). The three
   leaves, the menu toggle and the filter toggle hold no literal word (`grep -rn "visually-hidden\|d-inline-block"
   src/crud_views/templates/crud_views/tags` is empty; `active` and `flex-grow-1` appear only as table defaults).
2. **The rendered output is unchanged for a project that sets none of the new keys; `d-inline-block` goes.** The
   eight goldens under `tests/test1/golden/action_menus/` are untouched (`git status --short tests/test1/golden/`
   empty after every task; `test_action_menus_golden.py` green, never regenerated). `test_template_a11y.py` is
   unchanged and green: the default hidden-label word is still `visually-hidden`.
   `test_menu_item_without_icon_renders_the_fixed_width_placeholder` pins the placeholder as
   `<span class="cv-icon-fw" aria-hidden="true">`.
3. **A rendering guard proves every class on a table-styled button element comes from the table or the `cv-`
   namespace.** `test_button_chain_renders_only_table_classes` (`tests/test1/test_button_classes_templates.py`):
   a sentinel table for all 43 keys, the action leaf at every location × mode with `cv_active` and `cv_flex` on,
   the menu item leaf, and five pages over six URLs (publisher list with the active `list` button and the filter toggle, author
   list with row menus, author cards with the `flex` action, the order card page in both directions, author
   detail). Mutation evidence during Task 4: a literal ` active` put back into the action leaf fails it with
   `('a', 'active')` on every page and leaf render; emptying `BEHAVIOUR_TOKENS` surfaces exactly
   `('button', 'dropdown-toggle')` and `('span', 'd-none')`, nothing else. The `btn` regex test stays as it was
   (it still covers `.py` and `.js`); the literal-pair bound rose from 15 to 20.
4. **The theme recipe no longer overrides a leaf.** Commit `f5c4be1`: `buttons.md` registers `context:active` and
   `context:hidden-label` instead and the `html+django` block is gone; `theme.md`'s worked example overrides
   nothing for looks; `action_menus.md`'s split-toggle example renders its hidden label through the key;
   `card-list-view.md` and `javascript.md` name the keys; `CHANGELOG.md` has the Added and Changed entries.

## Review Focus (plan)

1. `context:active` set to `None` renders the base classes only: `test_utility_key_set_to_none_renders_no_token[context:active-…]`.
2. `card:flex` set to `None`: the second case of the same test.
3. A menu item without an icon renders exactly the `cv-icon-fw` placeholder:
   `test_menu_item_without_icon_renders_the_fixed_width_placeholder`.
4. A card action in `icon` mode reaches `card:hidden-label`: `test_card_icon_mode_hidden_label_comes_from_the_table`.
5. The guard bites after the chain is clean: the two mutations above (Task 4, Step 4; recorded in the ledger).

## Calls from the spec, and where each landed

- Per-location keys for `active` and `hidden-label`: nine rows in `DEFAULT_BUTTON_CLASSES`, documented as such.
- Slot name `hidden-label`: in the table, the leaves, the docs and the CHANGELOG.
- `'card' 'flex'` as a literal pair: `tags/button/action.html`; covered by `test_every_literal_slot_in_templates_is_a_default_key`.
- `d-inline-block` dropped, relying on `.cv-icon-fw`: both label templates; the placeholder test.
- Goldens byte-identical: the golden test is the proof.
- Regex guard kept, rendering guard added beside it: `test_button_classes_templates.py`.
- `dropdown-toggle` and `d-none` exempt and tracked: `BEHAVIOUR_TOKENS`, issue #232 (which also lists
  `data-bs-toggle`, `data-bs-popper-config`, `dropdown-menu dropdown-menu-end` and the language selector items).
- No new check id: `context:active:icon`, `card:flex:both`, `list:hidden-label:icon` and `context:flex` are
  `W362` (`test_w362_rejects_bad_mode_shape`).
- Table keys with Bootstrap defaults instead of a package stylesheet rule (the maintainer's answer to the builder
  check): no file under `src/crud_views/static/` changed.

## Final review (fresh reviewer, whole branch)

No Critical findings. The reviewer reproduced the guard's bite with six mutations of its own in a detached worktree
(literal `active` in the leaf, `visually-hidden` on the menu toggle, on the filter toggle and in the leaf's icon
branch, `d-inline-block` on the placeholder, `active` on a sort toggle), each failing the guard with the tag and
token named, and confirmed the ledger's "no deviation from the plan" claim against the diff.

Fixed in one pass (commit `356cf2c`, docs only): `CHANGELOG.md` and `buttons.md` said the legacy
`tags/actions_menu_item_label.html` "keeps its 0.30 body", which commit `dc735b1` had made false by dropping
`d-inline-block` from its placeholder. Both sentences now say "minus the `d-inline-block` on its icon placeholder".
Verified by grep (prose has no unit test): the old wording is gone, the amended wording is present in both files;
`ruff format --check` and `mkdocs build` clean.

Deferred as minor (the maintainer decides): `BEHAVIOUR_TOKENS` exempts by token alone, so a future literal `d-none` on
a hidden-label span or `dropdown-toggle` on any styled element would pass; keying the two exemptions by
`(selector, token)` would close that. The legacy include's placeholder branch (`cv_icon_action=None` through
`actions_menu_item_label.html`) has no test of its own; the stock placeholder has one. `buttons.md` lines 92–93 wrap a
sentence mid-way (renders fine). The "four pages" wording in Goal 3 above was corrected to five pages over six URLs.

Rulings on what the reviewer set aside: the Bootstrap words outside the button chain (pagination, breadcrumb, the
table pager, the language selector items, the object-detail tabs and table heads), the dropdown's behaviour hooks
(#232), `.cv-icon-fw` reaching a page only through `{% cv_css %}` (#231), the menu toggle's `aria-label` beside its
hidden span, the example project's own markup and the leading space when a variant key is `None` all stand as
pre-existing or named non-goals. The guard renders `container.html` and `card_order.html` at page level rather than
leaf level as the spec's guard step listed; the plan made that call and the reviewer's sort-toggle mutation confirms
the coverage is equivalent.

## Verification

- `pytest tests -n auto -q` → 2451 passed, 2 skipped (2441 at the end of Task 1, 2446 after Task 2, 2450 after
  Task 3). Unchanged by the review fix, which touched prose only.
- `ruff check src tests` and `ruff format --check src tests docs` clean; pre-commit ran on every commit.
- `mkdocs build -q` clean after the docs commit.
- `git diff main --stat -- src/crud_views/static src/crud_views/lib` lists `button_classes.py` only.

## Noted, not fixed

- The suite's base template renders no `{% cv_css %}` and links a stale stylesheet path: #231, filed during the
  design review.
- A `hidden-label` key set to `None` makes the label text visible; documented in `buttons.md`, not guarded.
