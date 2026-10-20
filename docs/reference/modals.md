# Modals

Views can opt in to Bootstrap 5 modal rendering: action buttons then open the view in a modal
dialog instead of navigating to a full page.

!!! example "Try it live"
    The [Showcase example](https://django-crud-views-demo.onrender.com/showcase/recipe/) in the live demo shows this in
    action — log in as `alice` / `alice`. See [Live demo](../getting_started/demo.md) for data resets and wake-up time.

```python
class AuthorDeleteView(CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_author
    cv_modal = True  # opt in
    cv_modal_size = "lg"  # optional: "", "sm", "lg", "xl"
```

## Supported views

`DeleteView`, `ObjectDetailView` (from the optional `crud_views_object_detail` app —
core `DetailView` does not support modals), `CustomFormView` and `CustomFormNoObjectView`
(and their permission-required and extension-package variants). Setting `cv_modal = True` on
other view types raises system check error `viewset.E251`. Create/update support is planned.

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

Your base template must provide the standard `{% cv_config %}` / `{% cv_js %}` tags and either Bootstrap 5's
JavaScript bundle on `window.bootstrap` or a replacement [adapter](javascript.md#cvadapters). jQuery is not needed.

`cv_modal_size` takes the tokens `""` (default), `"sm"`, `"lg"` and `"xl"`; the adapter maps them to the dialog's
size. Bootstrap class names such as `"modal-lg"` fail system check `viewset.E250`, whose message names the replacement.

## Theming the modal

`{% cv_config %}` renders the shell through `crud_views/modal/shell.html`, with the ids `cv-modal`, `cv-modal-dialog`
and `cv-modal-content`. The partial `crud_views/modal/content.html` fills `cv-modal-content`; its close button carries
`data-cv-modal-dismiss`. Override either template by name (see [Custom themes](theme.md)); for a non-Bootstrap
dialog see [JavaScript](javascript.md#a-non-bootstrap-modal).

## Extending

After every content injection the shell dispatches a `cv:modal:loaded` CustomEvent on
`#cv-modal` — use it to initialize custom scripts inside modal content:

```javascript
document.getElementById("cv-modal").addEventListener("cv:modal:loaded", function () {
    // initialize widgets inside the injected modal content
});
```

Rows that formsets add after page load get the analogous `cv:formset:row-added` event; see
[Formsets](formsets.md#initializing-widgets-in-added-rows).
