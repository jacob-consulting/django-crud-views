# Modals

Views can opt in to Bootstrap 5 modal rendering: action buttons then open the view in a modal
dialog instead of navigating to a full page.

```python
class AuthorDeleteView(CrispyModelViewMixin, MessageMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_author
    cv_modal = True                 # opt in
    cv_modal_size = "modal-lg"      # optional: "", "modal-sm", "modal-lg", "modal-xl"
```

## Supported views

`DeleteView`, `DetailView`, `CustomFormView` and `CustomFormNoObjectView` (and their
permission-required and extension-package variants). Setting `cv_modal = True` on other view
types raises system check error `viewset.E251`. Create/update support is planned.

## Behavior

- Buttons linking to a modal-enabled view fetch the view with the `X-CV-Modal: true` header and
  show the returned partial in a shared modal shell (rendered by `{% cv_config %}` — no template
  changes needed in your project).
- On successful POST the server answers `204` with an `X-CV-Redirect` header and the browser
  navigates to the view's success URL — messages and `cv_success_key` work exactly as without
  modals.
- Validation errors (and delete protection) re-render inside the open modal (status 422).
- Progressive enhancement: direct links, middle-click, disabled JavaScript and custom themes
  that ship no modal JavaScript all render the normal full page.

## Requirements

Your base template must load Bootstrap 5's JavaScript bundle and jQuery (both are already
required for the Bootstrap 5 theme), plus the standard `{% cv_config %}` / `{% cv_js %}` tags.

## Extending

After every content injection the shell dispatches a `cv:modal:loaded` CustomEvent on
`#cv-modal` — use it to initialize custom scripts inside modal content:

```javascript
document.getElementById("cv-modal").addEventListener("cv:modal:loaded", function () {
    // initialize widgets inside the injected modal content
});
```
