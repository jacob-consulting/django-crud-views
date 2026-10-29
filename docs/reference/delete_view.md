# DeleteView

The `DeleteView` handles deleting model instances. It renders a confirmation form before
deleting.

## Basic Usage

```python
from crud_views.lib.crispy import CrispyViewMixin, CrispyDeleteForm
from crud_views.lib.views import DeleteViewPermissionRequired, MessageMixin


class AuthorDeleteView(CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_author
    cv_message_template_code = "Deleted author »{{ object }}«"
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
| `cv_success_key` | `str` | `"list"` | ViewSet key to redirect to after success; must not be an object view such as `detail`, the object is gone (`viewset.E254`) |
| `cv_cancel_key` | `str` | `"list"` | ViewSet key the cancel button returns to (static fallback) |
| `cv_cancel_keys` | `list[str] \| None` | `None` | Origin keys the cancel button may return to dynamically. See [UpdateView](update_view.md#dynamic-cancel-target) |
| `cv_success_keys` | `list[str] \| None` | `None` | Origin keys the success redirect may return to dynamically; object views such as `detail` are rejected (`viewset.E254`). See [UpdateView](update_view.md#dynamic-success-target) |
| `cv_context_actions` | `list[str]` | `["home", "detail", "update", "delete"]` | Actions shown in the header area |
| `cv_show_related_objects` | `bool` | `False` | Show cascading deletes display |
| `cv_link_related_objects` | `bool` | `False` | Link related objects to their detail views |

## HTTP methods

A delete view answers GET (the confirmation page) and POST (the validated deletion). Deletion only runs through the
POST: the form must validate and `cv_check_delete_protection()` must return no errors.

HTTP `DELETE` is rejected with **405 Method Not Allowed** on every package delete view: the core
`DeleteView` / `DeleteViewPermissionRequired`, the Guardian and the polymorphic delete views. Earlier releases
inherited Django's `DeletionMixin.delete()`, which deleted the object without the form, the protection check or the
form hooks. That was never a documented package API.

The rejection comes after the gates that already ran before it, so it reveals nothing they would hide:

- An anonymous user is still redirected to the login page (or gets the Guardian view's configured 403/404).
- On a core view, a user without the `delete` permission gets 403. The core permission phase also loads the object,
  so a missing object is a 404, and a disabled action state is a 403.
- On a Guardian child view the parent gate runs first (404 for a missing parent, 403 without the parent permission).
  An inactive user gets 403 (see [Inactive users](guardian.md#inactive-users)).
- An active user on a top-level Guardian view gets the 405 before any object lookup, with or without a grant and
  whether or not the object exists.

The 405 response's `Allow` header and an `OPTIONS` response never list `DELETE`, also on a subclass that puts
`"delete"` back into `http_method_names`: the request is still rejected. A modal delete view keeps its
`Vary: X-CV-Modal` header on the 405. The guard sits in `dispatch` and leaves Django's `delete()` method as it is,
so Django 4.2 emits no `DeleteViewCustomDeleteWarning`.

Send a POST with the confirmation field, as the bundled form does. A client or test that sent `DELETE` must post the
form instead; see [Migrating to 1.0.0](../migrating-1.0.md).

## Confirmation Form

`CrispyDeleteForm` provides a confirmation checkbox that the user must check before
the object is deleted:

```python
from crud_views.lib.crispy import CrispyDeleteForm


class AuthorDeleteView(CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_author
```

You can create a custom delete form if you need additional fields or different confirmation
logic.

### Delete button

The submit button of `CrispyDeleteForm` is built by two hooks. `get_delete_button_kwargs()` returns the crispy
arguments (default `{"name": "delete", "value": _("Delete")}`) and `get_delete_button()` returns the `Submit` from them,
with its classes from the button class key `form:delete`. Override the kwargs to change the label:

```python
class AuthorDeleteForm(CrispyDeleteForm):
    def get_delete_button_kwargs(self) -> dict:
        return {**super().get_delete_button_kwargs(), "value": _("Delete author")}
```

See [Buttons](buttons.md#forms).

## Messages

Add `MessageMixin` to show a success message after deletion:

```python
class AuthorDeleteView(CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_author
    cv_message_template_code = "Deleted author »{{ object }}«"
```

`cv_message_template_code` is a Django template string; `{{ object }}` renders to the string representation of the deleted instance.
Your base template renders the queued messages with `{% cv_messages %}` — see [Flash messages](messages.md).

## Form Processing Hooks

The same hooks as [CreateView](create_view.md#form-processing-hooks) are available, since
`DeleteView` also uses `CrudViewProcessFormMixin`.

`self.object.delete()` and `cv_form_valid_hook` run in one transaction; side effects belong in
`cv_on_commit`. See [Request lifecycle, transactions & hooks](request_lifecycle.md#call-chains).

## Cascading Deletes Display

Show users what related objects will be deleted when they delete an object (similar to Django Admin).
This feature is opt-in.

```python
class PublisherDeleteView(CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
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
class PublisherDeleteView(CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
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
The summary counts (`related_summary`) are deliberately not filtered: they show how much a deletion removes, which is
the existing aggregate policy. (A [conditional formset](conditional.md) with `on_off="purge"` follows its own,
separately documented deletion policy.)

The core view checks the model-level `view_<model>` permission. A Guardian delete view checks per-object grants
instead, with the delete view's own `cv_guardian_accept_global_perms` as the global fallback; see
[Cascading Deletes with Per-Object Permissions](guardian.md#cascading-deletes-with-per-object-permissions).

### Protected objects

An object that a `PROTECT` foreign key points at blocks the deletion. The confirmation page shows one generic
"Deletion is blocked by protected relationships" notice, followed only by the labels of protected objects the user may
view. Labels of objects the user may not view are dropped before the template gets its context, and no placeholder
stands in for them. If the user may view none of them, the notice still shows, with no labels.

Two context keys carry this, both set when `cv_show_related_objects` is on:

| Key | Contents |
|---|---|
| `has_protected_objects` | `True` when protected objects block the deletion, computed from the unfiltered collection before any filtering. Decide whether to show the notice from this key. |
| `protected_objects` | A list of only the protected objects the user may view, in their original order. It can be empty while `has_protected_objects` is `True`. |

Hiding labels never makes a deletion look possible and never weakens the protection itself. A POST still runs
Django's `PROTECT` check and raises `ProtectedError` as before.

### Custom related-object filters

`cv_filter_related_objects(user, related)` receives the `RelatedObjects` tuple (`tree`, `summary`, `protected`) and
returns the tuple the template context is built from. It is the hook for narrowing what the preview shows. An override
must keep these guarantees:

- Filter `related.protected` as well as the tree, and return only protected objects the user may view. Never return
  the raw `related.protected`.
- Start from the right superclass: call `super().cv_filter_related_objects(user, related)` and narrow its result, so a
  core view keeps the model-level check and a Guardian view keeps its object-grant check. If you replace the filter
  entirely, apply an equivalent authorization check. On a Guardian view, do not run the core model-level filter after
  the Guardian one: it would hide labels that an object grant permits without a global permission.
- Leave `has_protected_objects` alone. It is computed before your hook runs, so a filter that hides every label
  cannot hide the block.
- Keep the summary counts as they are, unless you deliberately change the aggregate policy for your view.

```python
class PublisherDeleteView(CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_publisher
    cv_show_related_objects = True

    def cv_filter_related_objects(self, user, related):
        related = super().cv_filter_related_objects(user, related)
        # narrow further: never show archived contracts by name
        return related._replace(protected=[obj for obj in related.protected if not obj.is_archived])
```

### Template Customization

The related objects display uses two overridable templates:

- `crud_views/snippets/delete/related_objects.html` — main container with summary, tree, and warnings
- `crud_views/snippets/delete/related_objects_tree.html` — recursive nested tree of individual objects

Each alert in `related_objects.html` is a `{% cv_alert %}` call, so it renders through the one alert frame,
`crud_views/tags/alert.html` (see [Flash messages](messages.md)). The summary alert lists
`related_summary_items`, the summary as ready strings (`"book: 3"`); `related_summary` (a `{verbose_name: count}`
dict) stays in the context for overrides that read it.

Override these in your project's template directory to customize the rendering. A copy of
`crud_views/view_delete.content.html` must include the snippet when `related_summary or has_protected_objects`, and a
copy of `related_objects.html` must show the blocked notice when `has_protected_objects`, listing
`protected_objects`. A copy that still tests `protected_objects` loses the notice whenever every label is hidden. See
[Migrating to 1.0.0](../migrating-1.0.md).

## Delete Protection

Add custom business logic to prevent deletion.

### View Hook

Override `cv_check_delete_protection()` to return error messages:

```python
class PublisherDeleteView(CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_publisher

    def cv_check_delete_protection(self) -> list[str]:
        if self.object.books.filter(is_published=True).exists():
            return ["Cannot delete a publisher with published books."]
        return []
```

When the method returns errors, the delete confirmation form is **not shown at all**. Instead, the user sees the error messages in an alert. This runs on GET, so the user immediately knows the object cannot be deleted.

The check also runs on POST as defense in depth — if a protection error is returned, the object is not deleted.

### Form Hook

For validation that should happen at submit time, use standard Django form validation:

```python
class ProtectedDeleteForm(CrispyDeleteForm):
    def clean(self):
        cleaned_data = super().clean()
        # custom validation logic
        if some_condition:
            raise ValidationError("Cannot delete.")
        return cleaned_data
```

### Execution Order

1. **GET**: `cv_check_delete_protection()` runs — if errors, show errors instead of form
2. **POST**: Form validates (checkbox confirmed, `clean()` passes)
3. **POST**: `cv_check_delete_protection()` runs again (defense in depth)
4. If errors from either, form re-renders with non-field errors: status 200 on a full page, 422 in the modal, and
   nothing is deleted
5. If no errors, object is deleted

`cv_check_delete_protection()` is separate from the database's `on_delete=PROTECT`. A protected foreign key is not
turned into a form error: the POST lets Django raise `ProtectedError` as before, and the transaction keeps the data.
Show the block on GET with `cv_show_related_objects` (see [Protected objects](#protected-objects)), or return a
message from `cv_check_delete_protection()` when you want the form-error behavior.

---

> To disable an action the user *is* permitted to perform, based on object state
> (e.g. a locked/open parent), see [Conditionally disabling an action](action_enabled.md).
