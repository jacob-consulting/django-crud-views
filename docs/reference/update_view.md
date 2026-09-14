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
    cv_message_template_code = "Updated author »{{ object }}«"
    cv_cancel_keys = ["list", "detail"]  # cancel returns to where the user came from
```

How it works:

- Links **into** a view with `cv_cancel_keys` carry the current view's key as a query parameter
  when that key is listed: `/author/<pk>/update/?cv_from=detail` from the detail page,
  `?cv_from=list` from the list. Links into views without `cv_cancel_keys` are unchanged.
  The parameter name is `CRUD_VIEWS_CANCEL_ORIGIN_PARAM` (default `cv_from`, see [Settings](settings.md#cancel-button)).
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
