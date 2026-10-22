# Acceptance — one frame template around the create/update/delete/custom-form form (#239)

Light workflow: the issue is the spec; no spec or plan.

## Change

- New `src/crud_views/templates/crud_views/snippets/form_frame.html`:
  `{% block cv_form_frame %}{% block cv_form_body %}{% endblock %}{% endblock %}`.
- `view_create.content.html`, `view_update.content.html`, `view_custom_form.content.html` and
  `view_delete.content.html` extend it and put their unchanged content in `cv_form_body`.
- Delete's protection-error alert moved verbatim to `snippets/delete/protection_errors.html`, included from
  `view_delete.content.html`; the German `.po` location comment follows it (the msgid is unchanged).
- No modal flag in the context: a theme reads `request.headers.x_cv_modal` itself, as the issue's example does
  (maintainer: do not extend upstream further than needed). `cv_modal` is already the button flag.

## Acceptance

| Criterion (issue #239)                                                              | Evidence                                                                                                                                                   |
| ----------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Stock output of all four pages is unchanged (goldens)                               | `tests/test1/golden/form_frame/` captured from the templates on `main` before the change (create, update, custom_form, delete, delete_protection); `test_stock_*` compare whitespace-normalised markup |
| A theme wraps the form of all four views with one override and no copy of `<form>`  | `test_theme_frame_wraps_the_form` overrides only `form_frame.html` (locmem loader in front); `test_theme_frame_leaves_the_modal_bare` sends `X-CV-Modal: true` |
| The protection-error alert is overridable on its own                                | `test_protection_alert_overridable_on_its_own` overrides only `protection_errors.html`; `test_theme_frame_wraps_the_protection_alert` shows the frame wraps it too |
| `docs/reference/theme.md` lists the frame and the snippet; CHANGELOG entry          | "Framing the form pages" section with the card example; `### Added` bullet under Unreleased                                                                 |
| Nothing else moves                                                                  | `pytest tests -n auto`: 2484 passed, 2 skipped; `mkdocs build --strict` clean; no existing golden changed                                                   |
