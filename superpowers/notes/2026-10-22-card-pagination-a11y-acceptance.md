# Acceptance — card pagination: accessible markup and arrows from the icon registry (#241)

Light workflow: the issue is the spec; no spec or plan.

## Change

`src/crud_views/templates/crud_views/snippets/pagination.html` (rendered by `{% cv_pagination %}` in
`view_card.content.html`):

- previous / next render `{% cv_icon "page-previous" %}` / `{% cv_icon "page-next" %}` plus a
  `<span class="visually-hidden">` with the translated `previous` / `next` (both msgids already existed for the
  django-tables2 pagination, so German needed no new entries for them);
- the current page's `.page-item` carries `aria-current="page"`; its `<span class="page-link">` stays;
- a disabled end is `<a class="page-link" aria-disabled="true">` without `href`, as Bootstrap's docs show;
- the `<nav>`'s `aria-label` is `{% translate 'pagination' %}` (new msgid, German "Seitennavigation").

`src/crud_views/lib/icons.py`: `page-previous` / `page-next` are `fas:chevron-left` / `fas:chevron-right` in
`DEFAULT_ICONS` and `chevron-left` / `chevron-right` in `BOOTSTRAP_ICONS`. Nav and list classes are unchanged
(`mt-3`, `pagination justify-content-center`).

## Effect on crud_views_tabler

The override in `crud_views_tabler/templates/crud_views/snippets/pagination.html` can be deleted. The theme maps
`page-previous` / `page-next` to `tabler:chevron-left` / `tabler:chevron-right` in its icon table. Two differences
remain, both of them markup the theme chose and the issue does not ask upstream to adopt: the override passes
`css="icon-sm"` to the icon, and it renders the current page as an `<a href>` rather than a `<span>`. If the theme
wants the smaller icon, its icon renderer or CSS has to supply that size once the override is gone.

## Acceptance

| Criterion (issue #241)                                                                     | Evidence                                                                                                                                                                                                                         |
| ------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| The card list view's pagination carries `aria-current`, `aria-disabled` and translated hidden labels | `tests/test1/test_card_order.py`: `test_card_pagination_current_page_aria_current`, `test_card_pagination_disabled_end_is_aria_disabled_link` (both ends), `test_card_pagination_labels_translated` (German `nav` label and hidden labels) |
| A theme changes the arrows through `CRUD_VIEWS_ICONS` / `register_icons`, without a template override | `test_card_pagination_arrows_from_icon_registry` maps both names to `bi:` icons through `CRUD_VIEWS_ICONS`                                                                                                                         |
| Golden update for the card pagination                                                       | `tests/test1/golden/card_pagination/page1.html` and `page2.html` (first and last page), checked by `test_card_pagination_golden`                                                                                                 |
| CHANGELOG entry (DOM change)                                                                | `CHANGELOG.md`, Unreleased → Breaking                                                                                                                                                                                           |
| Docs                                                                                        | `docs/reference/icons.md` lists the two names; `docs/reference/card-list-view.md` → Paging describes the markup. `mkdocs build --strict` passes                                                                                  |
| Nothing else moves                                                                          | `pytest tests -n auto`: 2494 passed, 2 skipped. All six new tests failed before the template change; `test_card_pagination_links_preserve_order_and_filter` now selects `a.page-link[href]`, since a disabled end is an `<a>` without `href` |
