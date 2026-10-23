# Acceptance: button container empty and label (#265, #266)

Branch `feat/button-container-empty-label`, spec `superpowers/specs/2026-10-23-button-container-empty-label-design.md`,
plan `superpowers/plans/2026-10-23-button-container-empty-label.md`.

## Runs

- `pytest tests -n auto` → 2739 passed, 2 skipped
- `mkdocs build --strict` → ok; `ruff format --check` / `ruff check` → clean
- Goldens unchanged; the final reviewer ran the new view tests against the old source: 15 of 16 fail there, the
  16th (`test_menu_only_group_keeps_container`) is a regression guard and passes on both

## Review Focus

| Item | Test |
|---|---|
| a menu-only group is not empty | `test_button_container_list.py::test_menu_only_group_keeps_container` |
| zero items render `""` whatever the #261 keys | `test_button_container_list.py::test_zero_items_render_nothing_whatever_the_keys` |
| a label with HTML characters is escaped | `test_button_container_list.py::test_label_is_escaped` |
| the German label through a real view | `test_button_container_list.py::test_context_label_german`, `test_button_container_layout.py::test_layout_label_translated` |
| a `None` tag renders `div` | `test_button_container_layout.py::test_layout_tag_fallback_div`, `test_button_container_list.py::test_tag_none_renders_div` |

## Final review

Ready to merge, no Critical or Important findings. One Minor regraded and fixed: the docs said a custom label is
translated when the catalogue has it, without saying how it gets there (`gettext_noop`; `gettext_lazy` fails E361).
Three minors deferred (see PR).
