# Acceptance — create and custom-form post as multipart/form-data (#236)

Light workflow: the issue is the spec; no spec or plan.

## Change

`src/crud_views/templates/crud_views/view_create.content.html` and `view_custom_form.content.html` add
`enctype="multipart/form-data"` to their `<form>`, matching `view_update.content.html`. The attribute is unconditional
rather than gated on `form.is_multipart()`: that check sees only the main form, not file fields in its formsets.

crispy's `{% crispy %}` renders its own inner `<form>` (with `enctype` when the form is multipart), but a browser
ignores a nested form start tag, so only the outer tag decides how the POST is encoded.

## Acceptance

| Criterion (issue #236)                                                     | Evidence                                                                                                                                      |
| -------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| Create, update and custom-form `<form>` tags all carry the multipart enctype | Diff above                                                                                                                                    |
| A test renders each form content template with a `FileField` form          | `tests/test1/test_form_enctype.py`, parametrised over the three templates; it checks the outermost `<form>` tag. Before the fix the create and custom-form cases failed |
| Nothing else moves                                                         | `pytest tests -n auto`: 2459 passed, 2 skipped; no golden file changed                                                                        |
