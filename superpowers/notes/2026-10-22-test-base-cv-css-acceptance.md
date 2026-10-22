# Acceptance — test project base template renders `{% cv_css %}` (#231)

Light workflow: the issue is the spec; no spec or plan.

## Change

`tests/test1/app/templates/app/base.html` replaces
`<link rel="stylesheet" href="{% static "viewset/css/property.css" %}">` with `{% cv_css %}`.

## Acceptance

| Criterion (issue #231)                                          | Evidence                                                                                                                                                                                               |
| --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| The stale `viewset/css/property.css` link is gone               | Diff above; a rendered `/publisher/` page contains no `viewset/css`                                                                                                                                     |
| The test pages load the package stylesheets via `{% cv_css %}`  | The `<head>` of a rendered `/publisher/` page links `crud_views/css/property.css`, `table.css`, `formset.css` and `icons.css` (throwaway client test, not committed)                                      |
| No test moves; the goldens are the check that markup is unchanged | `pytest tests -n auto`: 2451 passed, 2 skipped; no golden file changed                                                                                                                                  |
