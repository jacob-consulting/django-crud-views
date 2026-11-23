# Conditionally Disabling an Action

`cv_action_enabled` is a state gate beside permission: requests, child context buttons, card child actions,
object navbar child items and links to a nested Guardian create ask it only after permission passes.
Other buttons evaluate it independently of permission, as listed under [Enforcement Points](#enforcement-points).
The two hooks answer different questions:

| Hook | Question |
|------|----------|
| `cv_has_access` | "May this user perform this action at all?" (permission) |
| `cv_action_enabled` | "Is this action currently applicable to this object?" (state) |

A typical use case: a "locked" group that prevents members from being added or removed, even
though the user would normally have permission to do so.

!!! example "Try it live"
    The [Disabled Actions example](https://django-crud-views-demo.onrender.com/disabled-actions/lockable_ticket/) in the
    live demo disables update and delete for locked tickets — log in as `alice` / `alice`. See
    [Live demo](../getting_started/demo.md) for data resets and wake-up time.

## Default and Override Signature

```python
@classmethod
def cv_action_enabled(cls, user, obj=None) -> bool:
    return True  # always enabled by default
```

Override on any view class to add state-based conditions:

```python
class PersonDeleteView(DeleteViewPermissionRequired):
    cv_viewset = cv_person

    @classmethod
    def cv_action_enabled(cls, user, obj=None):
        return not (obj and obj.group.filter(locked=True).exists())
```

## Behavior When `False`

When `cv_action_enabled` returns `False`:

- The action's button is **hidden** in list actions, context actions and card actions — or rendered
  **disabled** when the target view resolves to `"disable"` (see
  [Hide or disable inaccessible actions](inaccessible_actions.md)).
- A direct GET or POST to the action's URL returns **403** for an authenticated user
  (anonymous users receive a login redirect, as usual).

## The `obj` Parameter

`obj` is the model instance the action concerns. Its value depends on the view type:

| View type | `obj` value |
|-----------|-------------|
| Object views (detail, update, delete, action, custom form) | The model instance being acted on |
| Nested view without an own object (list or create) | The **immediate parent** instance |
| Top-level view without an own object (list or create) | `None` |

The request's `cv_get_action_object()` returns `self.get_object()` for object views and the immediate parent
for nested views without an own object; otherwise it returns `None`. A link passes the same action object,
with one exception: on a hosting view that did not run the ancestor guard (a custom or non-CRUD view), a
nested list's state hook receives `None`. Core controls do not disappear on such a view.

## Example: Locked Group Disables Member Add/Remove

```python
class PersonDeleteView(CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_person
    cv_message_template_code = "Deleted person »{{ object }}«"

    @classmethod
    def cv_action_enabled(cls, user, obj=None):
        # obj is the Person row; members of a locked group cannot be removed.
        return not (obj and obj.group.filter(locked=True).exists())


class PersonCreateView(CrispyViewMixin, MessageMixin, CreateViewParentMixin, CreateViewPermissionRequired):
    cv_viewset = cv_person

    @classmethod
    def cv_action_enabled(cls, user, obj=None):
        # obj is the parent Group; a locked group cannot gain members.
        return not (obj and obj.locked)
```

## Enforcement Points

`cv_action_enabled` is enforced at two layers — button rendering and request dispatch:

**Button hiding** — all action templates (`list_action.html`, `context_action.html`,
`card_action.html`) guard their output with `{% if cv_action_enabled is not False %}`.
The `cv_action_enabled` flag is injected into the template context by the rendering
infrastructure.
Child context buttons, card child actions, object navbar child items and links to a nested Guardian create
run parent gate, own access, then state. A permission denial skips the state hook and leaves the context flag
`cv_action_enabled=True`, meaning not evaluated; the permission result still hides or disables the control.
Context buttons, row actions, parent buttons, sibling buttons and non-child card actions to other targets
keep evaluating state independently of permission. The `cv_context_has_permission` filter never evaluates state.

**Request enforcement (plain views)** — `CrudViewPermissionRequiredMixin.has_permission()`
calls `cv_get_action_object()` then `cv_action_enabled()`. Returning `False` causes
`PermissionDenied` (HTTP 403) for the authenticated user.

**Request enforcement (guardian views)** — two mixins handle the guardian path:

- `GuardianObjectPermissionMixin.get_object()` — for object actions (detail, update, delete,
  action views). After the per-object guardian check, it calls `cv_action_enabled()` and raises
  `PermissionDenied` if it returns `False`.
- `GuardianParentPermissionMixin.dispatch()` — for every nested view without an own object, including list
  and create. After checking the parent
  permission, it calls `cv_action_enabled()` with the resolved parent and raises `PermissionDenied`
  if it returns `False`.

## See Also

- [ListView](list_view.md) — `cv_list_actions` controls which per-row action buttons are shown
- [DeleteView](delete_view.md) — `cv_check_delete_protection()` for form-level delete blocking
- [Per-Object Permissions](guardian.md) — `cv_has_access` and guardian integration
