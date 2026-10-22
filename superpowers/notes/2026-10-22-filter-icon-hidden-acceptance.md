# #232 acceptance — behaviour words in the button chain

Rescoped in https://github.com/jacob-consulting/django-crud-views/issues/232#issuecomment-6339837493: the dropdown
words stay (a theme with a different dropdown DOM overrides the template, so class-table keys would buy nothing);
`d-none` goes, replaced by the native `hidden` attribute.

## Done

- `tags/context_action_filter.html` renders `hidden` on the inactive icon span; `list.filter.js` flips `icon.hidden`.
- `BEHAVIOUR_TOKENS` drops `d-none`; the `dropdown-toggle` reason now reads as markup a theme replaces, not debt.
- `docs/reference/theme.md` gains "Templates that follow Bootstrap's DOM" (the two menu templates and the language
  selector).
- CHANGELOG: Breaking entry for overrides of `context_action_filter.html` that still render `d-none`.
- Golden `toolbar_publisher_list.html` regenerated (`CV_UPDATE_GOLDEN=1`); the only change is the close span.

## Verification

- `pytest tests -n auto`: 2451 passed, 2 skipped. vitest `list.filter.test.js`: 12 passed. ruff format/check clean.
- Guard mutation: putting `class="d-none"` back on the close span fails the guard on `/publisher/` and both card
  orders.

## Observed, not changed

- Putting it back on the *open* span is not caught: the guard renders only the collapsed panel, where that span
  carries no class. The blind spot existed before; the HTTP tests in `test_filter.py` cover both states for `hidden`.
- `tags/list_action_form.html` still hides its POST forms with `class="d-none"`. That is outside the button chain
  (the guard does not scan it) and could become `hidden` the same way.
