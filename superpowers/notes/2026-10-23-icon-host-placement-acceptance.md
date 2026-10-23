# Acceptance: icon host placement (#258)

Branch `feat/icon-host-placement`, spec `superpowers/specs/2026-10-23-icon-host-placement-design.md`, plan
`superpowers/plans/2026-10-23-icon-host-placement.md`.

## Runs

- `pytest tests -n auto` → 2674 passed, 2 skipped
- `npx -y -p node@22 -- node node_modules/vitest/vitest.mjs run` → 126 passed
- `mkdocs build --strict` → ok; `ruff format --check` / `ruff check` → clean
- Goldens unchanged; the stock filter toggle renders byte-identical output without a host library (checked by diff)

## Review Focus

| Item | Test |
|---|---|
| `both` mode without icon, host library active | `test_icon_host_leaves.py::test_host_both_mode_without_icon` |
| host and `fas:` icons on one page | `test_icon_host_leaves.py::test_host_mixed_page_keeps_element_icons_inline` |
| disabled host button | `test_icon_host_leaves.py::test_host_disabled_button_keeps_class` |
| standalone icon keeps `css` | `test_icons_registry.py::test_host_standalone_with_css` |
| `*:icon-host` set to `None` | `test_icon_host_leaves.py::test_host_slot_none_switches_icon_off`, `test_button_data.py::test_host_slot_none_switches_icon_off` |

## Final review

One Important finding fixed: a leaf dict without `cv_icon_inline` lost its icon even without a host library; the
leaves now test `is not False` (`test_leaf_dict_without_icon_inline_keeps_the_icon`,
`test_menu_toggle_without_inline_key_keeps_the_icon`). Three minors deferred (see PR).
