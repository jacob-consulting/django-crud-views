# UpdateView

The `UpdateView` handles updating existing model instances. It works the same way as
the [CreateView](create_view.md), using Django's form handling and
[django-crispy-forms](https://django-crispy-forms.readthedocs.io/en/latest/) for layout.

## Basic Usage

```python
from django.utils.translation import gettext as _
from crud_views.lib.crispy import CrispyModelForm, CrispyModelViewMixin, Column4
from crud_views.lib.views import UpdateViewPermissionRequired, MessageMixin
from crispy_forms.layout import Row


class AuthorUpdateForm(CrispyModelForm):
    submit_label = _("Update")

    class Meta:
        model = Author
        fields = ["first_name", "last_name", "pseudonym"]

    def get_layout_fields(self):
        return Row(Column4("first_name"), Column4("last_name"), Column4("pseudonym"))


class AuthorUpdateView(CrispyModelViewMixin, MessageMixin, UpdateViewPermissionRequired):
    model = Author
    form_class = AuthorUpdateForm
    cv_viewset = cv_author
    cv_message = "Updated author »{object}«"
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
| `model` | `Model` | — | The Django model to update |
| `form_class` | `Form` | — | The form class for the update form |
| `cv_viewset` | `ViewSet` | — | The ViewSet this view belongs to |
| `cv_success_key` | `str` | `"list"` | ViewSet key to redirect to after success |
| `cv_context_actions` | `list[str]` | `["home"]` | Actions shown in the header area |

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
class AuthorUpdateView(CrispyModelViewMixin, MessageMixin, UpdateViewPermissionRequired):
    model = Author
    form_class = AuthorUpdateForm
    cv_viewset = cv_author
    cv_message = "Updated author »{object}«"
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
