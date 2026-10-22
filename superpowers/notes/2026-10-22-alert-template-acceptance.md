# Acceptance: one data-driven alert template (#250)

Spec: `superpowers/specs/2026-10-22-alert-template-design.md`. Plan: `superpowers/plans/2026-10-22-alert-template.md`.

## Change

- `crud_views.lib.messages`: `LEVELS` (message level → `error|warning|success|info|debug`) and `alert_data()`,
  which escapes the heading, text and items, picks the body template, and falls back to `info`. `message_alerts()`
  is built on it. `ALERT_CLASSES` and `ICON_NAMES` are removed (a clean breaking change, as the maintainer decided
  on 2026-10-22).
- Templates: the frame `tags/alert.html`, the bodies `snippets/alert/text.html` and `snippets/alert/list.html`.
  `tags/messages.html` is now a loop that includes the frame.
- `{% cv_alert %}` (simple tag) renders the frame with `alert` pushed onto the caller's context, so a body template
  sees the caller's variables.
- The class table gains five keys, `alert:error|warning|success|info|debug`, taking it from 46 to 51.
- The delete snippets and the guardian manage page call `{% cv_alert %}`. The delete view adds
  `related_summary_items`. The guardian config table moved to `crud_views/snippets/guardian/config_table.html`.

## Acceptance

| Criterion | Evidence |
|---|---|
| One frame renders every alert; no template outside `tags/alert.html` and the body snippets contains `class="alert` | `test_only_the_alert_templates_write_alert_markup` walks every `src/crud_views*/templates/**/*.html` |
| A theme changes frame, list body and colours independently | `test_frame_is_overridable_on_its_own`, `test_list_body_is_overridable_on_its_own`, `test_alert_colours_follow_the_class_table` |
| `cv_messages` keeps its escaping guarantees; unknown levels render as info | `test_messages.py`: only the dict-key names changed, every rendering assertion is unchanged; `test_alert_data_unknown_level_is_info` |
| Stock message output is equivalent | Whitespace-normalised render of the old `messages.html` against the new loop: identical (checked during Task 2); `test_cv_messages_*` class strings unchanged |
| Delete and guardian alerts go through the frame; DOM changes listed | `test_delete_alerts_render_through_the_frame`, `test_guardian_manage_config_renders_in_an_alert`; golden `delete_protection.html` gains only `role="alert"` and the icon; CHANGELOG `### Changed` |
| `alert` in a caller's context survives the tag | `test_cv_alert_restores_the_callers_alert` |
| Escaping under `{% autoescape off %}`; hostile `__str__` items | `test_cv_alert_escapes_with_autoescape_off`, `test_alert_data_escapes_items` |
| German headings still translate | `test_delete_alert_headings_translate`; the `.po` files changed only in `#:` references and ordering (no fuzzy or obsolete entries) |
| Docs | `messages.md` ("A single alert", "Theming"), `theme.md` ("Alerts"), `delete_view.md`, `buttons.md` (five keys, count 51); CHANGELOG Breaking/Added/Changed |
| Nothing else moves | `pytest tests -n auto`: 2542 passed, 2 skipped; `task check` clean; `mkdocs build` 0 warnings |

## Follow-up: crud_views_tabler

Ship this with the release that carries #250:

- Add `templates/crud_views/tags/alert.html`: the icon goes in `.alert-icon`, the heading in
  `<h4 class="alert-heading">`, and the body include is wrapped in `.alert-description`. Keep `alert-dismissible`
  and the close button when `alert.dismissible` is set.
- Delete `templates/crud_views/tags/messages.html` and `templates/crud_views/snippets/delete/protection_errors.html`.
- Adapt the two tests that check the Tabler alert markup. The related-objects and guardian alerts then get the
  Tabler layout with no override.
