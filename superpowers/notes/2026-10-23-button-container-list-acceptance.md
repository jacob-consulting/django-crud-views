# Acceptance: button container list markup and lone item (#261)

Branch `feat/261-button-container-list`, spec `superpowers/specs/2026-10-23-button-container-list-design.md`, plan
`superpowers/plans/2026-10-23-button-container-list.md`.

## Runs

- `pytest tests -n auto` → 2708 passed, 2 skipped
- `mkdocs build --strict` → ok; `ruff format --check` / `ruff check` → clean
- Goldens unchanged; the final reviewer rendered the detail and list pages through the old and the new
  `container.html` and got byte-identical container fragments (no menu, one button + menu, everything in the menu)

## Review Focus

| Item | Test |
|---|---|
| `container-list = ""` still renders a `<ul>` | `test_button_container_list.py::test_list_empty_class_renders_bare_ul`, `test_button_container_layout.py::test_layout_empty_list_class_is_list` |
| one inline button plus a menu keeps the container | `test_button_container_list.py::test_bare_one_button_plus_menu_keeps_container` |
| a hidden action does not count | `test_button_container_list.py::test_bare_ignores_hidden_action` |
| no empty `<li>` without a menu | `test_button_container_list.py::test_list_no_menu_no_empty_li` |
| zero items render as today whatever the keys | `test_button_container_list.py::test_zero_items_render_as_today_whatever_the_keys`, `test_button_container_layout.py::test_layout_zero_items_never_bare` |

## Final review

No Critical or Important findings. One Minor regraded to Important and fixed: with `container-list` set, an empty
container rendered an empty `<ul>`, against the spec's "zero items render as today regardless of keys"
(`test_zero_items_render_as_today_whatever_the_keys`). Two minors deferred (see PR).
