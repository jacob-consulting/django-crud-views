# DeleteView

The `DeleteView` handles deleting model instances. It renders a confirmation form before
deleting.

## Basic Usage

```python
from crud_views.lib.crispy import CrispyModelViewMixin, CrispyDeleteForm
from crud_views.lib.views import DeleteViewPermissionRequired, MessageMixin


class AuthorDeleteView(CrispyModelViewMixin, MessageMixin, DeleteViewPermissionRequired):
    model = Author
    form_class = CrispyDeleteForm
    cv_viewset = cv_author
    cv_message = "Deleted author »{object}«"
```

## View Classes

| Class | Description |
|-------|-------------|
| `DeleteView` | Base delete view without permission checks |
| `DeleteViewPermissionRequired` | Delete view with `delete` permission required |

Both inherit from Django's `generic.DeleteView` and `CrudView`.

## Configuration

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | `Model` | — | The Django model to delete |
| `form_class` | `Form` | — | The form class (typically `CrispyDeleteForm`) |
| `cv_viewset` | `ViewSet` | — | The ViewSet this view belongs to |
| `cv_success_key` | `str` | `"list"` | ViewSet key to redirect to after success |
| `cv_context_actions` | `list[str]` | `["home"]` | Actions shown in the header area |

## Confirmation Form

`CrispyDeleteForm` provides a confirmation checkbox that the user must check before
the object is deleted:

```python
from crud_views.lib.crispy import CrispyDeleteForm

class AuthorDeleteView(CrispyModelViewMixin, MessageMixin, DeleteViewPermissionRequired):
    model = Author
    form_class = CrispyDeleteForm
    cv_viewset = cv_author
```

You can create a custom delete form if you need additional fields or different confirmation
logic.

## Messages

Add `MessageMixin` to show a success message after deletion:

```python
class AuthorDeleteView(CrispyModelViewMixin, MessageMixin, DeleteViewPermissionRequired):
    model = Author
    form_class = CrispyDeleteForm
    cv_viewset = cv_author
    cv_message = "Deleted author »{object}«"
```

The `{object}` placeholder is replaced with the string representation of the deleted instance.

## Form Processing Hooks

The same hooks as [CreateView](create_view.md#form-processing-hooks) are available, since
`DeleteView` also uses `CrudViewProcessFormMixin`.
