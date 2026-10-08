# UpdateView

The `UpdateView` handles updating existing model instances. It works the same way as
the [CreateView](create_view.md), using Django's form handling and
[django-crispy-forms](https://django-crispy-forms.readthedocs.io/en/latest/) for layout.

## Basic Usage

```python
from django.utils.translation import gettext as _
from crud_views.lib.crispy import CrispyModelForm, CrispyViewMixin, Column4
from crud_views.lib.views import UpdateViewPermissionRequired, MessageMixin
from crispy_forms.layout import Row


class AuthorUpdateForm(CrispyModelForm):
    submit_label = _("Update")

    class Meta:
        model = Author
        fields = ["first_name", "last_name", "pseudonym"]

    def get_layout_fields(self):
        return Row(Column4("first_name"), Column4("last_name"), Column4("pseudonym"))


class AuthorUpdateView(CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired):
    form_class = AuthorUpdateForm
    cv_viewset = cv_author
    cv_message_template_code = "Updated author »{{ object }}«"
```

## View Classes

| Class | Description |
|-------|-------------|
| `UpdateView` | Base update view without permission checks |
| `UpdateViewPermissionRequired` | Update view with `change` permission required |

Both inherit from Django's `generic.UpdateView` and `CrudView`.

## Configuration

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | `Model` | from `cv_viewset` | The Django model to update (auto-derived from ViewSet) |
| `form_class` | `Form` | — | The form class for the update form |
| `cv_viewset` | `ViewSet` | — | The ViewSet this view belongs to |
| `cv_success_key` | `str` | `"list"` | ViewSet key to redirect to after success |
| `cv_cancel_key` | `str` | `"list"` | ViewSet key the cancel button returns to (static fallback) |
| `cv_cancel_keys` | `list[str] \| None` | `None` | Origin keys the cancel button may return to dynamically; see [Dynamic cancel target](#dynamic-cancel-target) |
| `cv_success_keys` | `list[str] \| None` | `None` | Origin keys the success redirect may return to dynamically; see [Dynamic success target](#dynamic-success-target) |
| `cv_context_actions` | `list[str]` | `["home", "detail", "update", "delete"]` | Actions shown in the header area |

## Dynamic cancel target

*Available since 0.21.0.*

By default the cancel button always returns to `cv_cancel_key` (`"list"`). With `cv_cancel_keys`
the button returns to the sibling view the user came from instead:

<!-- cv-sync: library/views.py -->
```python
class AuthorUpdateView(BreadcrumbMixin, CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_author
    form_class = AuthorForm
    cv_message_template_code = _("Updated author “{{ object }}”")
    cv_cancel_keys = ["list", "detail"]  # cancel returns to where the user came from
    cv_success_keys = ["list", "detail"]  # so does save
```

How it works:

- Links **into** a view with `cv_cancel_keys` carry the current view's key as a query parameter
  when that key is listed: `/author/<pk>/update/?cv_from=detail` from the detail page,
  `?cv_from=list` from the list. Links into views without `cv_cancel_keys` or `cv_success_keys`
  are unchanged. The parameter name is `CRUD_VIEWS_ORIGIN_PARAM` (default `cv_from`, see
  [Settings](settings.md#origin-parameter)).
- The view resolves the target with `cv_get_cancel_key()`: the value must match `^[a-z][a-z0-9_]*$`,
  be listed in `cv_cancel_keys`, be registered on the ViewSet, and, for object views such as `detail`,
  the current view must have an object (a create view falls back). Anything else falls back to
  `cv_cancel_key`. The parameter is a **view key**, never a URL, so it cannot redirect elsewhere.
- The origin survives validation errors: the form posts to `request.get_full_path`, so an invalid
  submit re-renders with the same cancel target, in full-page and modal mode.
- System check `viewset.E252` fails at startup when an entry of `cv_cancel_keys` is not a registered
  view key (`"list"` is accepted when only a card view is registered).

Code that builds sibling links itself (themes, custom columns) should call
`view.cv_get_link_url(target_cls, key, obj)` instead of `view.cv_get_url(key, obj)` so the link
carries the origin. On a ViewSet without a list view, the card page counts as the `list` origin,
the same fallback `cv_get_cancel_key()` and `viewset.E252` already apply.

Works the same on `CreateView`, `DeleteView`, `CustomFormView` and `CustomFormNoObjectView`.

## Dynamic success target

*Available since 0.26.0.*

By default a successful submit redirects to `cv_success_key` (`"list"`). With `cv_success_keys`
it redirects to the sibling view the user came from instead, so saving from the detail page
lands back on the detail page (see the example above).

It shares the origin parameter with `cv_cancel_keys` and resolves it the same way:

- A link into the view carries the origin when the key is listed in `cv_cancel_keys` **or**
  `cv_success_keys`. Both lists are resolved independently, so a view can return Cancel to the
  detail page while Save always goes to the list.
- `cv_get_success_key()` returns the origin when it is valid, listed in `cv_success_keys` and
  registered; otherwise `cv_success_key`. The form posts to `request.get_full_path`, so the origin
  reaches the POST without extra fields.
- An object view such as `detail` needs a persisted object. That is always true after an update
  or a custom form on an object, and after a create (the new object). It is never true after a
  delete: `DeleteView` falls back to `cv_success_key`, and system check `viewset.E254` rejects
  object views in a delete view's `cv_success_keys` at startup.
- Modal forms use the resolved URL in their `X-CV-Redirect` header. `ActionView` and the ordered
  up/down views honour `cv_success_keys` too, so an action started from the detail page can return there.
- System check `viewset.E253` fails at startup when an entry of `cv_success_keys` is not a
  registered view key (`"list"` is accepted when only a card view is registered).

!!! note "The list loses its state"
    Both targets are view keys, never URLs, so returning to the list drops its filter, sort
    order and page. That is the price of not accepting arbitrary redirect URLs.
Custom templates that build a back link from the cancel key should use
`{% cv_context_url view.cv_get_cancel_key as url %}` rather than `view.cv_cancel_key`.

## Reusing the Create Form

Often the update form has the same fields as the create form. You can inherit from the
create form and just change the submit label:

```python
class AuthorCreateForm(CrispyModelForm):
    submit_label = _("Create")

    class Meta:
        model = Author
        fields = ["first_name", "last_name", "pseudonym"]

    def get_layout_fields(self):
        return Row(Column4("first_name"), Column4("last_name"), Column4("pseudonym"))


class AuthorUpdateForm(AuthorCreateForm):
    submit_label = _("Update")
```

## Messages

Add `MessageMixin` to show a success message after updating:

```python
class AuthorUpdateView(CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired):
    form_class = AuthorUpdateForm
    cv_viewset = cv_author
    cv_message_template_code = "Updated author »{{ object }}«"
```

## Form Processing Hooks

The same hooks as [CreateView](create_view.md#form-processing-hooks) are available:

| Hook | Description |
|------|-------------|
| `cv_post_hook(context)` | Called at the start of POST processing |
| `cv_form_is_valid(context)` | Override to add custom validation |
| `cv_form_valid(context)` | Called when the form is valid (saves the instance) |
| `cv_form_valid_hook(context)` | Called after `cv_form_valid` (used by `MessageMixin`) |
| `cv_form_invalid(context)` | Called when the form is invalid |
| `cv_form_invalid_hook(context)` | Called after form invalid handling |
