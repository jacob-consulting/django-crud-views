# Acceptance: label mode as a target-view default for the context toolbar (#269)

Branch `feat/context-action-label-mode`, spec `superpowers/specs/2026-10-23-context-action-label-mode-design.md`,
plan `superpowers/plans/2026-10-23-context-action-label-mode.md`. Executed natively, one whole-branch review at the
end.

## Runs

- `pytest tests -n auto` → 2826 passed, 2 skipped; goldens under `tests/test1/golden/` unchanged
- `examples/bootstrap5`: `pytest -n auto` → 301 passed; `manage.py check` → no issues
- `mkdocs build --strict` → ok; `ruff check` / `ruff format --check` → clean

## Goals

All tests in `tests/test1/test_context_action_label_mode.py`.

| Goal | Test |
|---|---|
| `cv_context_action_label_mode` on the target sets the toolbar mode | `test_toolbar_follows_target_mode`, `test_cv_get_dict_carries_target_mode`, `test_cv_context_button_tag_follows_target` |
| precedence: view map naming the key → button → resolved map naming the key → target → `"icon"` | `test_target_default_used_when_nothing_else_names_key`, `test_view_map_naming_key_beats_target`, `test_button_mode_beats_target`, `test_viewset_map_beats_target`, `test_setting_beats_target`, `test_view_map_without_key_yields_to_target` |
| toolbar only: rows ignore it | `test_target_default_ignored_for_list`, `test_target_mode_does_not_reach_rows` |
| every button that opens the view follows it, across ViewSets | `test_registered_button_follows_target` (with / without own `label_mode`), `test_home_button_follows_list_view`, `test_parent_button_follows_parent_list_view`, `test_child_button_follows_child_list_view`, `test_sibling_button_follows_sibling_list_view` |
| menu items keep icon + short label | `test_menu_folded_key_keeps_icon_and_short_label` |
| `viewset.E210` / `E211` point at each other's name | `test_e210_invalid_target_attribute`, `test_e210_dict_on_target_attribute_names_the_map`, `test_no_e210_for_valid_or_unset_target_attribute`, `test_e211_string_on_map_names_target_attribute` |
| `viewset.W292` uses the same fallback | `test_w292_silent_with_target_label_mode`, `test_w292_explicit_target_icon_still_warns`, `test_w292_registered_button_follows_target`, `test_w292_invalid_target_attribute_does_not_crash` |
| nothing set → unchanged output | the golden suite |

## Naming

Kept as proposed: `cv_context_action_label_mode` (str, set on the view the button opens) beside
`cv_context_actions_label_mode` (dict, set on the page showing the toolbar). The "Set on / Meaning" pair is in both
comments in `base.py` and as a table in `docs/reference/action_menus.md#target-view-default`.

## Rulings

- Dropped a planned byte-identity test: the goldens already prove it with nothing set.
- A menu-folded item drops its `title` when its target says `"label"` — the existing #216 rule for labelled actions;
  icon and short label stay, which is what the spec promises.
- Reviewer's "no child/sibling test" re-graded to Important (the spec lists it) and fixed.

## Deferred minor

- An invalid `cv_context_action_label_mode` raises `ValueError` at render even without strict mode — only reachable
  when `viewset.E210` is silenced, and the same as an invalid map or button `label_mode` today.
