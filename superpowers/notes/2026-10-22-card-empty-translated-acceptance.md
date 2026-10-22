# Acceptance — card list "No items found." is translated (#246)

Light workflow: the issue is the spec; no spec or plan.

## Change

`src/crud_views/templates/crud_views/view_card.content.html` loads `i18n` alongside `crud_views` and renders
`{% translate "No items found." %}`. The `<p class="text-muted">` around it is unchanged.

`src/crud_views/locale/de/LC_MESSAGES/django.po` gains one entry, `"No items found."` → `"Keine Einträge gefunden."`,
added by hand. A full `makemessages` run would also have rewritten stale line references across the catalog and
revived an unrelated `Delete` entry, so it was left out of this change. `django.mo` is recompiled.

## Acceptance

| Criterion (issue #246)                                              | Evidence                                                                                                                         |
| ------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| With the German locale active, an empty card list shows German text | `tests/test1/test_card.py::test_card_list_empty_german` requests `/author/card/` under `translation.override("de")`; it failed before the fix |
| The markup is otherwise unchanged                                   | The same test asserts the full `<p class="text-muted">Keine Einträge gefunden.</p>`; the English `test_card_list_empty` still passes |
| CHANGELOG entry                                                     | `CHANGELOG.md`, Unreleased → Fixed                                                                                               |
| Nothing else moves                                                  | `pytest tests -n auto`: 2485 passed, 2 skipped; `test_i18n.py` (no empty or fuzzy msgstr, `.mo` loads) passes                    |
