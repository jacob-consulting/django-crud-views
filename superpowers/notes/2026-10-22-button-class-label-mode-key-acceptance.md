# Acceptance report — the class table learns the label mode (#209)

Spec: `superpowers/specs/2026-10-22-button-class-label-mode-key-design.md`. Plan:
`superpowers/plans/2026-10-22-button-class-label-mode-key.md`. Tracker #228; follow-ups #216, #227.

## Acceptance criteria

1. **A theme can give an icon-only and a labelled button in the same location and variant different classes
   without overriding `tags/button/action.html`.** `test_card_same_variant_different_modes_get_different_classes`
   (`tests/test1/test_button_class_label_mode.py`): two `CardAction`s, both `variant="secondary"`, one `both` and
   one `icon`, with only `card:secondary:icon` registered — the `both` button renders the default
   `btn btn-secondary btn-sm`, the `icon` button `btn btn-sm btn-icon x-icon`. Lookup level:
   `test_mode_key_wins_when_present_else_base`, `test_settings_base_key_does_not_beat_theme_mode_key`
   (`tests/test1/test_button_classes.py`).
2. **Tables and `CRUD_VIEWS_BUTTON_CLASSES` written before the change keep working unchanged.**
   `test_default_table_is_complete` still asserts 34 keys and the same `EXPECTED_KEYS`; `test_tag_accepts_variables`
   and `test_tag_in_both_libraries_escapes` still use the two-argument form; the eight goldens under
   `tests/test1/golden/action_menus/` are byte-identical (`git status --short tests/test1/golden/` empty after
   every task's run, `test_action_menus_golden.py` green) — including `toolbar_publisher_list.html`, which carries
   the filter toggle whose template changed.
3. **A system check rejects an unknown mode segment and a mode segment on a non-action key.**
   `test_w362_rejects_bad_mode_shape` over `card:tertiary:iconn`, `card:container:icon`, `menu:item:both`,
   `card:tertiary:icon:extra`, `card:tertiary:`, `form:submit:icon`; `test_w362_names_the_bad_mode` pins the
   mode-specific message and hint; `test_w362_accepts_action_mode_keys` pins the three valid shapes in both layers;
   `test_mode_key_non_str_is_e361_only` pins that a valid mode key with a bad value is `E361` alone.
4. **Card with `both` and `icon` in one variant renders two class strings; the filter toggle resolves
   `context:<variant>:icon`; no golden changes.** Criterion 1's test; `test_filter_toggle_resolves_icon_mode`
   (`x-icon` applied, `context:secondary:both` ignored); goldens as in 2. Also pinned because it is live today, not
   after #216: `test_list_row_buttons_resolve_icon_mode` — every row button on `/publisher/` takes `list:*:icon`.
5. **Docs.** Commit `dee5645`: `buttons.md` (key shape in "The class table", the 34-key sentence, `None` and
   layer-vs-specificity rules under `CRUD_VIEWS_BUTTON_CLASSES`, three-argument form under "Rendering", the recipe
   and the `W362` row); `context_buttons.md` (custom templates pass their own mode); `theme.md` (one clause);
   `CHANGELOG.md` under Added.

## Verification

- `pytest tests -n auto -q` → 2346 passed, 2 skipped (Task 5 and Task 6 runs, same tree plus this note).
- `ruff check src tests` and `ruff format --check .` clean; pre-commit ran on every commit.
- `test_button_classes_module_has_no_module_level_view_import` pins the spec's import constraint; the three
  frozensets are imported inside `_action_key_parts()` / `_is_action_mode_key()` / the check, never at module
  level. The guard also rejects relative `.view` imports (stricter than the plan's version).

## Noted, not fixed

- `context:*:icon` and `list:*:icon` keys are reachable now (every non-card button is `icon`), so a theme that
  registers them restyles toolbars and rows immediately. Documented in `buttons.md`; tested as above.
- A dedicated `context:filter-toggle` slot was considered and rejected (spec, Non-goals): the filter borrows the
  action key shape and passes `"icon"`.
- No `crud_views.W363` for a settings base key shadowed by a theme mode key — documented with a worked example
  instead (spec, decision 7).
- The leaf's hard-coded `active` / `flex-grow-1` are #227.
