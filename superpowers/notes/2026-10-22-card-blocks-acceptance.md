# Acceptance — card template: blocks for title, content and actions, plus class keys (#243)

Light workflow: the issue is the spec; no spec or plan. The maintainer chose blocks **and** class keys over blocks
only.

## Change

`src/crud_views/templates/crud_views/tags/card.html` gains three blocks:

- `card_title` — the text of the `<h5>` heading, default `{{ object }}`;
- `card_content` — empty, between the heading and the actions;
- `card_actions` — the menu's hidden action forms and the `crud_views/tags/button/container.html` include.

The card's own classes come from the class table (`src/crud_views/lib/button_classes.py`): `card:root` (`card mb-3`),
`card:body` (`card-body`), `card:title` (`card-title`). The default table grows from 43 to 46 keys.

Two decisions within the issue's "e.g.":

- **No new `card:actions` wrapper.** The stock card has no element around its actions, and adding one would change
  the stock output. The actions container already has a key, `card:container`.
- **Footer placement stays structural.** No "footer variant" ships. A theme that wants the actions in a footer
  overrides `crud_views/tags/card.html` with its own structure and keeps the three block names. A project template
  that extends `crud_views/tags/card.html` resolves to the theme's card and fills the same blocks.

## Effect on crud_views_tabler

The theme's `tags/card.html` keeps its footer layout. It renames its `card_footer` block to `card_actions` (with
the `.card-footer` div inside the block, or around it) so that project card templates written against the upstream
blocks work under Tabler too. The `h3` heading and `card` (no `mb-3`) could move to the class keys, but the footer
still needs the override.

## Acceptance

| Criterion (issue #243)                                                                                     | Evidence                                                                                                                                                                                                                       |
| ---------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Stock card output unchanged                                                                                | The card goldens in `tests/test1/golden/action_menus/` (`cards_author_full`, `cards_author_disabled`, `cards_publisher_child`) pass untouched. They normalise whitespace; the empty `card_content` block adds a blank line in the raw HTML |
| A `cv_card_template` that extends the stock card and fills `card_content` renders the actions without repeating them | `tests/test1/test_card_blocks.py::test_extending_template_fills_content_and_keeps_actions` with `tests/test1/app/templates/app/author_card_blocks.html`: inline buttons plus a menu action; with the filled `<p>` removed the card equals the stock card |
| Class keys                                                                                                 | `test_class_keys` sets `card:root` / `card:body` / `card:title` through `CRUD_VIEWS_BUTTON_CLASSES`; `test_button_classes.py` lists the three new keys                                                                            |
| `docs/reference/card-list-view.md` documents the blocks; CHANGELOG entry                                    | Custom Card Template section rewritten around `{% extends %}` with a block table (the old example hand-rolled the action loop); `docs/reference/buttons.md` lists the keys; `CHANGELOG.md` Unreleased → Added. `mkdocs build --strict` passes |
| Nothing else moves                                                                                         | `pytest tests -n auto`: 2498 passed, 2 skipped; ruff clean                                                                                                                                                                      |
