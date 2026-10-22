# Acceptance — create view emits widget media once (#191)

Light workflow: the issue is the spec; no spec or plan.

## Change

`src/crud_views/templates/crud_views/view_create.content.html` drops the trailing `{{ form.media }}`. crispy's
`FormHelper.include_media` (default `True`) already renders the media inside `{% cv_render_form %}`.

## Acceptance

| Criterion (issue #191)                                                         | Evidence                                                                                                                                  |
| ------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `{{ form.media }}` is gone from `view_create.content.html`                     | Diff above; `grep -rn "form.media" src --include=*.html` finds nothing                                                                    |
| Create, update and custom-form each render a `Media` widget's JS and CSS once | `tests/test1/test_form_media.py` (parametrised over the three templates); before the fix the create case failed with `assert 2 == 1`     |
| Nothing else moves                                                             | `pytest tests -n auto`: 2455 passed, 2 skipped; no golden file changed                                                                    |

## Out of scope

Create and custom-form forms lack `enctype="multipart/form-data"` (update has it), so file fields cannot upload
there. Filed as #236.
