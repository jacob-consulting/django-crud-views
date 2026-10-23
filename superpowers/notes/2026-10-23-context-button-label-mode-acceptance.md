# Acceptance: context button label mode and no invisible icon buttons (#264)

Branch `feat/context-button-label-mode`, spec `superpowers/specs/2026-10-23-context-button-label-mode-design.md`,
plan `superpowers/plans/2026-10-23-context-button-label-mode.md`.

## Runs

- `pytest tests -n auto` → 2792 passed, 2 skipped (the suite now runs with `CRUD_VIEWS_STRICT=True`)
- `examples/bootstrap5`: `pytest -n auto` → 301 passed; `manage.py check` → no issues (no `W292`)
- `mkdocs build --strict` → ok; `ruff check` / `ruff format --check` → clean

## Goals

| Goal | Test |
|---|---|
| `ContextButton.label_mode` sets the toolbar mode for every view of the ViewSet | `test_context_button_label_mode.py::test_button_label_mode_wins_over_viewset_map`, `test_toolbar_renders_button_mode`, `test_cv_context_button_tag_follows_button`, `test_instance_level_button_mode_reaches_rendering` |
| precedence view map (naming the key) → button → resolved map → `"icon"` | `test_view_map_naming_key_beats_button`, `test_view_map_without_key_yields_to_button`, `test_view_map_without_key_and_no_button_mode_is_icon`, `test_no_button_mode_unchanged`, `test_view_level_button_beats_viewset_button` |
| rows ignore the button's mode | `test_list_location_ignores_button`, `test_button_label_mode_does_not_reach_rows` |
| invalid `label_mode` → `viewset.E210` | `test_e210_invalid_button_label_mode_at_viewset`, `..._at_view`, `test_e210_on_default_button`, `test_no_e210_for_valid_or_unset_label_mode` |
| static icon-only-without-icon → `viewset.W292` | `test_w292_*` (10 tests: key without button, plain button, inline key; silent with button mode, map, icon; skips menu-folded, custom template, `get_context()` override, unregistered target) |
| render time: strict raises, otherwise `"label"` + warning; menu items untouched | `test_button_data.py::test_icon_mode_without_icon_raises_strict`, `test_icon_mode_without_icon_falls_back_to_label` (context/list/card × `None`/`""`), `test_menu_item_without_icon_untouched`, `test_icon_present_unchanged`, `test_label_and_both_without_icon_untouched`, `test_empty_label_and_icon_*` |
| test runs are strict | `test_strict_mode.py::test_suite_runs_strict`, `test_is_strict_follows_the_setting_before_debug` |

## Test-project changes caused by strict mode and the guard

- Turning `CRUD_VIEWS_STRICT` on suite-wide broke nothing by itself; the two `test_strict_defaults_*` tests now
  delete the setting first so they still prove the `DEBUG` default.
- `AuthorPingView` (`ping`) had no icon and rendered an invisible row button: given `cv_icon_action =
  "fa-solid fa-bolt"`. `AuthorOriginContactView` (`contact`) the same in the toolbar: given `"fa-solid fa-envelope"`.
  Together these were 9 failures (golden list rows, backend-only rows, cancel / success origin pages).
- Goldens `action_menus/list_full.html` and `action_menus/cards_author_full.html` regenerated: they pinned the
  invisible `ping` button. The diff is only the added `<i class="fa-bolt fa-solid">`, checked by stripping it and
  comparing with the old file.
- `test_button_data.py::test_card_empty_label_forces_icon` given an icon (it tests the empty-label rule).
- `test_button_data.py::test_host_without_icon` and `test_resource_views.py::test_list_action_icons` pinned to
  `CRUD_VIEWS_STRICT=False`: they test icon-less rendering on purpose (`touch` deliberately has no icon and now
  renders as its label).

## Deviations from the plan

- `cv_get_context_button()` stays an instance method (a classmethod hid buttons set on a view instance); the lookup
  is shared through `_cv_find_context_button()`, and `cv_get_action_label_mode()` takes an optional `button`, which
  `cv_get_context()` passes.
- `cv_icon_mode_checks()` lives in `buttons.py`, and returns nothing when the label-mode map is invalid (`E211`
  reports that).

## Final review

Fresh reviewer, whole branch: no Critical findings. Fixed in one pass (`pytest tests -n auto` → 2795 passed, 2
skipped):

- The strict error named the target's key (`'update'`, or `'list'` for a parent button) instead of the configured
  toolbar key; `cv_get_context(location=...)` now also stamps `cv_action_key`, and the remedy mentions
  `icon_header` for parent / child / sibling buttons (`test_strict_error_names_the_configured_key`).
- `W292` raised `TypeError` on an invalid `cv_context_actions_inline`, breaking the whole check run; it now returns
  early like for an invalid map (`test_w292_does_not_crash_on_invalid_inline`).
- `context_buttons.md` no longer says the button's mode applies to the action menu.

Deferred minors: a second class-level button lookup when the instance found none; one warning per button per render
in the non-strict fallback; an empty full label with a short label stays empty; an invalid `ContextButton.label_mode`
breaks pages with strict off (only `E210` catches it, as for `variant`).
