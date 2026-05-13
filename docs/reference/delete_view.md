# DeleteView

The `DeleteView` handles deleting model instances. It renders a confirmation form before
deleting.

## Basic Usage

```python
from crud_views.lib.crispy import CrispyModelViewMixin, CrispyDeleteForm
from crud_views.lib.views import DeleteViewPermissionRequired, MessageMixin


class AuthorDeleteView(CrispyModelViewMixin, MessageMixin, DeleteViewPermissionRequired):
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
| `model` | `Model` | from `cv_viewset` | The Django model to delete (auto-derived from ViewSet) |
| `form_class` | `Form` | — | The form class (typically `CrispyDeleteForm`) |
| `cv_viewset` | `ViewSet` | — | The ViewSet this view belongs to |
| `cv_success_key` | `str` | `"list"` | ViewSet key to redirect to after success |
| `cv_context_actions` | `list[str]` | `["home"]` | Actions shown in the header area |
| `cv_show_related_objects` | `bool` | `False` | Show cascading deletes display |
| `cv_link_related_objects` | `bool` | `False` | Link related objects to their detail views |

## Confirmation Form

`CrispyDeleteForm` provides a confirmation checkbox that the user must check before
the object is deleted:

```python
from crud_views.lib.crispy import CrispyDeleteForm

class AuthorDeleteView(CrispyModelViewMixin, MessageMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_author
```

You can create a custom delete form if you need additional fields or different confirmation
logic.

## Messages

Add `MessageMixin` to show a success message after deletion:

```python
class AuthorDeleteView(CrispyModelViewMixin, MessageMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_author
    cv_message = "Deleted author »{object}«"
```

The `{object}` placeholder is replaced with the string representation of the deleted instance.

## Form Processing Hooks

The same hooks as [CreateView](create_view.md#form-processing-hooks) are available, since
`DeleteView` also uses `CrudViewProcessFormMixin`.

## Cascading Deletes Display

Show users what related objects will be deleted when they delete an object (similar to Django Admin).
This feature is opt-in.

```python
class PublisherDeleteView(CrispyModelViewMixin, MessageMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_publisher
    cv_show_related_objects = True  # show what will be cascade-deleted
```

When enabled, the delete confirmation page displays:

- A summary of related objects by type and count
- A nested tree of individual related objects
- Warnings for protected relationships (`on_delete=PROTECT`)

### Linking Related Objects

Optionally render related objects as links to their detail views:

```python
class PublisherDeleteView(CrispyModelViewMixin, MessageMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_publisher
    cv_show_related_objects = True
    cv_link_related_objects = True  # link to detail views when available
```

Links are only rendered for related objects whose model has a registered ViewSet with a `detail` view.

### Permission Filtering

Related objects are filtered based on the current user's permissions:

- Objects the user has `view` permission for: shown with full details
- Objects the user lacks `view` permission for: shown as aggregated counts (e.g., "3 book objects")

This ensures users see the full impact of deletion without leaking details of objects they can't normally access.

### Template Customization

The related objects display uses two overridable templates:

- `crud_views/snippets/delete/related_objects.html` — main container with summary, tree, and warnings
- `crud_views/snippets/delete/related_objects_tree.html` — recursive nested tree of individual objects

Override these in your project's template directory to customize the rendering.

## Delete Protection

Add custom business logic to prevent deletion.

### View Hook

Override `cv_check_delete_protection()` to return error messages:

```python
class PublisherDeleteView(CrispyModelViewMixin, MessageMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_publisher

    def cv_check_delete_protection(self) -> list[str]:
        if self.object.books.filter(is_published=True).exists():
            return ["Cannot delete a publisher with published books."]
        return []
```

When the method returns errors, the form is re-rendered with those errors as non-field errors. The object is not deleted.

### Form Hook

Alternatively, use standard Django form validation:

```python
class ProtectedDeleteForm(CrispyDeleteForm):
    def clean(self):
        cleaned_data = super().clean()
        # custom validation logic
        if some_condition:
            raise ValidationError("Cannot delete.")
        return cleaned_data
```

Both hooks are respected. The execution order is:

1. Form validates (checkbox confirmed, `clean()` passes)
2. View calls `cv_check_delete_protection()`
3. If errors from either, form re-renders with non-field errors
4. If no errors, object is deleted
