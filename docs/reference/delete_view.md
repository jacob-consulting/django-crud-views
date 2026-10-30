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
| `cv_show_related_objects` | `bool` | `False` | Show filtered cascade/protected labels and summaries; collection and blocked state run even when false |
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
form instead; see [Migrating to 1.0.0](../migrating-1.0.md#http-delete-on-delete-views).

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

`PROTECT` and `RESTRICT` relationships can block deletion. Every delete GET and POST context includes the blocked
state, even with the default `cv_show_related_objects = False`. The stock page omits the whole form while blocked:
confirmation, submit and the form-contained cancel control are absent, just as with custom protection errors.
Permitted labels use the heading "Deletion is blocked by protected relationships:" and a list. With no labels,
the heading has no colon and the notice says "Other objects still reference this one; remove or reassign them before
deleting it." Hidden labels never change the blocked state.

| Key | Contents |
|---|---|
| `has_protected_objects` | Present on every delete GET/POST context, computed from the unfiltered protected collection. Use it for the notice and form guard. |
| `protected_objects` | Present only with previews enabled: the protected objects the user may view, in original order. It can be empty while the flag is true. |

A confirmed POST whose target is genuinely blocked returns the protection page with **200**, or **422** in a modal,
without deleting anything. Custom protection runs first; the unfiltered database collection supplies the early
pre-check. A narrow race backstop also handles `ProtectedError` / `RestrictedError` from native target collection
after the existing lifecycle transaction unwinds. See [Execution Order](#execution-order) for its limits.

#### Collection cost and overrides

The default `cv_get_related_objects()` runs once per context on every GET/POST, including when previews are off.
It uses `router.db_for_write` and `NestedObjects`, which disables fast deletion and materializes the complete cascade
rows, tree and summary. A POST that reaches deletion additionally performs the actual deletion collection. There is
no large-cascade bound or benchmark claim. Hiding labels cannot safely omit the blocked-state check.

Existing `cv_get_related_objects()` overrides now run with previews disabled too. They must return an accurate,
unfiltered protected collection and keep those instances local; only the boolean enters context when previews are
off. Apply display authorization in `cv_filter_related_objects`, which still runs only with previews enabled. This
cost and override compatibility change introduces no new configuration option.

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
copy of `related_objects.html` must use both notice branches: colon heading with `items=protected_objects` when
labels exist, colon-free heading with the generic `text=` sentence otherwise. A copy that still tests
`protected_objects` loses the notice whenever every label is hidden. Guard the entire confirmation form too:

```django
{% if not has_protected_objects %}
    <form method="post">
        {% csrf_token %}
        {% cv_render_form %}
    </form>
{% endif %}
```

Keep the existing custom-protection branch around this content. The complete two-branch notice and migration steps
are in [Blocked deletions](../migrating-1.0.md#blocked-deletions); a copied alert leaf must render `alert.text` or
`alert.body_template` as well as its heading and items.

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

1. **GET/POST context**: run `cv_check_delete_protection()` and collect database protection, regardless of previews.
   Custom errors take presentation precedence; either block omits the form.
2. **POST**: run `cv_post_hook`, then validate the confirmation form. An invalid form follows the existing invalid
   hook/response path.
3. **Valid POST**: custom protection errors become non-field errors; custom or database protection returns the
   protection page (200 full page / 422 modal), with no write hooks or deletion.
4. **Unblocked POST**: run the existing write lifecycle and real `self.object.delete()`. Native target collection
   protection discovered here can use the race backstop after the transaction unwinds.
5. **Successful deletion**: run the normal success hook, commit callbacks and redirect/204 behavior.

The backstop requires both native-graph eligibility captured **before** invoking deletion and exact target
`Model.delete` / `Collector.collect` frame identity. Collector frames alone are insufficient: Django can aggregate a
custom relationship handler's `ProtectedError` and discard its traceback. The native allowlist excludes custom
handlers anywhere in possible cascade/parent paths, every `SET(...)` closure, `SET_DEFAULT`, private bulk-related
callbacks and nonstandard row loaders, including unknown relations with no current rows. Unknown collector types
also propagate. These exclusions govern exception translation only: real `model.delete()` still runs, visible
protection still uses the early pre-check, and no new transaction is introduced.

Errors from those unknown collection paths, `cv_post_hook`, a custom `cv_form_valid`, `cv_form_valid_hook`,
`cv_on_commit`, model overrides or signals continue to propagate. A callback failure after commit leaves the target
deleted; it must not report that the target survived. With `cv_atomic=False`, committed side effects of a custom
collection callback remain committed even if collection then fails. This is not support for arbitrary application
collector extensions. A custom `post` must delegate to the standard `post` path to receive its response handling and
preserve the documented lifecycle; direct `cv_form_valid_process` calls do not automatically receive an HTTP
protection response.

---

> To disable an action the user *is* permitted to perform, based on object state
> (e.g. a locked/open parent), see [Conditionally disabling an action](action_enabled.md).
