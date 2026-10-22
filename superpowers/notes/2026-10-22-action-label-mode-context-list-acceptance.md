# Acceptance report — context and list buttons learn the label mode (#216)

Spec: `superpowers/specs/2026-10-22-action-label-mode-context-list-design.md`. Plan:
`superpowers/plans/2026-10-22-action-label-mode-context-list.md`. Tracker #228; after #209 (PR #229), before #227.

## Acceptance criteria (#216)

1. **A project can give a context (toolbar) button a visible text label alongside its icon, configured from the
   view, without overriding `tags/button/action.html`.**
   `test_toolbar_labelled_create_leaves_the_other_buttons_byte_identical`
   (`tests/test1/test_action_label_mode_render.py`): `cv_context_actions_label_mode = {"create": "both"}` on the
   list view renders the icon and a visible `<span>Create</span>`; `test_toolbar_label_mode_renders_text_without_icon`
   covers `"label"`. The three layers: `test_setting_is_last_fallback`, `test_viewset_beats_setting`,
   `test_view_empty_map_beats_viewset` (`tests/test1/test_action_label_mode_config.py`). No template changed
   (`git diff main -- src/crud_views/templates` is empty).
2. **The default markup for context and list buttons is unchanged (icon-only); no golden churn for projects that
   do not opt in.** The same test compares every non-`create` toolbar button byte for byte before and after the
   map is set; `test_get` and `test_label_mode_icon_off_cards_keeps_full_label_and_title`
   (`tests/test1/test_button_data.py`) pin the unstamped and the `icon` contract; the eight goldens under
   `tests/test1/golden/action_menus/` are untouched (`git status --short tests/test1/golden/` empty after every
   task's run, `test_action_menus_golden.py` green). Both settings default to `{}`
   (`test_settings_defaults`).
3. **The mechanism is the one #213 establishes, not a parallel one.** The map's values are the three `LabelMode`
   words, validated with `is_label_mode()` at every layer (`crud_views.E106`, the ViewSet `field_validator`,
   `viewset.E211`); the leaf is unchanged and branches on the same `cv_label_mode`; the class table resolves
   `location:variant:mode` from #209 — `test_row_same_variant_different_modes_get_different_classes` shows two
   secondary row buttons of different modes taking different classes.
4. **A labelled context button gets no duplicate accessible name and no tooltip.** The toolbar test asserts no
   `title`, no `data-cv-tooltip`, no `visually-hidden` span and exactly one visible span;
   `test_label_mode_stamped_off_cards_shows_short_label` pins `cv_title` absent off cards in `both` / `label`.
5. **Tests cover a labelled and an icon-only context button in the same toolbar.** Criterion 1's test (`create`
   labelled, `list` icon-only with its `title`); `test_context_button_is_matched_by_its_configured_key` (`home`
   labelled, `detail` icon-only); `test_row_labelled_detail_next_to_icon_only_update` for rows.
6. **`docs/reference/buttons.md` and `action_menus.md` describe which locations can show labels.** Commit
   `e50fe35`: `action_menus.md` gains "Label mode" (the three-row table, resolution order, configured keys, the
   getters, the folded-item rule, `E106` / `E211` / `W291` rows); `buttons.md` updates the `cv_label` and
   `cv_label_mode` contract rows, rewrites the theme recipe around the map instead of a leaf override, and adds
   the `E211` / `W291` rows; `settings.md`, `card-list-view.md`, `context_buttons.md` and `CHANGELOG.md` as the
   plan lists.

## Decisions from the builder check

- **A labelled key folded into the menu loses its `title`.** `test_folded_labelled_key_has_no_title_and_icon_key_keeps_it`:
  the folded `detail` (`both`) item has no `title` and still shows icon and short label; the folded `delete`
  (`icon`) item keeps its `title`. Documented under "Labels, icons and the active action".
- **Manual placement honours the map.** `test_manual_placement_follows_the_view`: `{% cv_context_button 'update' %}`
  renders the labelled button. Documented in `context_buttons.md`.
- **The guardian override forwards `location`.** `test_guardian_override_forwards_the_location`: a labelled row
  on the guardian list page, whose rows go through `GuardianQuerysetMixin.cv_get_context()`; it fails when the
  override drops `location=location` (checked by mutation during the final review).

## Review Focus (plan)

1. Labelled key without access → hidden, no error: `test_labelled_key_without_access_is_hidden`.
2. Labelled key rendered disabled: `test_labelled_key_rendered_disabled` (`<button disabled>`, visible text, no
   `title`).
3. Labelled POST row action keeps `data-cv-action="submit-form"`: `test_labelled_post_row_action_keeps_submit_target`.
4. Custom `template_code` under a labelled key sees `cv_label_mode`: `test_custom_template_code_sees_label_mode`.
5. `cv_get_context()` without `location` is unstamped; `{}` stays `{}`; `cv_get_context_buttons()` stamps:
   `test_cv_get_context_without_location_is_unstamped`.

## Final review (fresh reviewer, whole branch)

No Critical findings. Fixed in one pass, each test proven by mutation (the test fails when the line it pins is
reverted):

- The two per-key tags were unpinned: `test_plain_list_view_rows_render_through_the_per_key_tag` (a plain
  `ListView` renders rows through `{% cv_list_action %}`) and `test_per_key_context_action_tag_follows_the_view`
  (`{% cv_context_action 'update' object %}`).
- The guardian override was unpinned: the test above.
- `action_menus.md`: the new "Label mode" section had landed between "Configuration" and its "Resolved on the
  rendering view" subsection; moved after it.
- `CHANGELOG.md`: a Breaking line for projects that override `cv_get_context()` with the old signature — they
  get a `TypeError` on the first toolbar after upgrading, which is where they will look. The spec had filed the
  whole change under Added.

Deferred as minor (the maintainer decides): `viewset.W291` warns on a view with `cv_context_actions = []` that
places a labelled key by hand with `{% cv_context_button %}`; the POST row-action test does not assert the hidden
`<form id="cv_form_…">` exists on the page; a `cv_label_mode` variable in a project's own page context is now
honoured by `{% cv_button %}` for toolbar and row buttons, where it used to be forced to `icon`.

## Verification

- `pytest tests -n auto -q` → 2428 passed, 2 skipped after the review fixes (2425 before them).
- `ruff check src tests` and `ruff format --check src tests docs` clean; pre-commit ran on every commit.
- `mkdocs build -q` clean after the docs commit.

## Noted, not fixed

- `cv_first_inline_keys()` keeps its name although it now also resolves the label-mode maps; its docstring says so.
  A rename touches three unrelated call sites for no behaviour change.
- `cv_get_context()` now delegates to a private `_cv_get_action_context()` holding the old body; the public
  signature and every existing call are unchanged.
- The leaf's hard-coded `active` / `flex-grow-1` are #227.
- `tabler-test` (downstream) is the first consumer: `CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE = {"create": "both"}`
  plus `btn-icon` moved from `context:primary` into `context:primary:icon`.
