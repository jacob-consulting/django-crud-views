# Conditionally Disabling an Action

`cv_action_enabled` is a secondary gate that runs **after** `cv_has_access` (permission) has
already passed. The two hooks answer different questions:

| Hook | Question |
|------|----------|
| `cv_has_access` | "May this user perform this action at all?" (permission) |
| `cv_action_enabled` | "Is this action currently applicable to this object?" (state) |

A typical use case: a "locked" group that prevents members from being added or removed, even
though the user would normally have permission to do so.

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

- The action's button is **hidden entirely** (not greyed out) in list actions, context actions,
  and card actions.
- A direct GET or POST to the action's URL returns **403** for an authenticated user
  (anonymous users receive a login redirect, as usual).

## The `obj` Parameter

`obj` is the model instance the action concerns. Its value depends on the view type:

| View type | `obj` value |
|-----------|-------------|
| Object views (detail, update, delete, action, custom form) | The model instance being acted on |
| Child create view | The **parent** instance (since no child instance exists yet) |
| Top-level create with no parent | `None` |

The helper `cv_get_action_object()` resolves this: it returns `self.get_object()` for object
views and `self.cv_get_parent_object()` for child-create views.

## Example: Locked Group Disables Member Add/Remove

```python
class PersonDeleteView(CrispyModelViewMixin, MessageMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_person
    cv_message = "Deleted person »{object}«"

    @classmethod
    def cv_action_enabled(cls, user, obj=None):
        # obj is the Person row; members of a locked group cannot be removed.
        return not (obj and obj.group.filter(locked=True).exists())


class PersonCreateView(CrispyModelViewMixin, MessageMixin, CreateViewParentMixin, CreateViewPermissionRequired):
    cv_viewset = cv_person

    @classmethod
    def cv_action_enabled(cls, user, obj=None):
        # obj is the parent Group; a locked group cannot gain members.
        return not (obj and obj.locked)
```

See `examples/bootstrap5/app/views/group_members.py` for the full working example.

## Enforcement Points

`cv_action_enabled` is enforced at two layers — button rendering and request dispatch:

**Button hiding** — all action templates (`list_action.html`, `context_action.html`,
`card_action.html`) guard their output with `{% if cv_action_enabled is not False %}`.
The `cv_action_enabled` flag is injected into the template context by the rendering
infrastructure.

**Request enforcement (plain views)** — `CrudViewPermissionRequiredMixin.has_permission()`
calls `cv_get_action_object()` then `cv_action_enabled()`. Returning `False` causes
`PermissionDenied` (HTTP 403) for the authenticated user.

**Request enforcement (guardian views)** — two mixins handle the guardian path:

- `GuardianObjectPermissionMixin.get_object()` — for object actions (detail, update, delete,
  action views). After the per-object guardian check, it calls `cv_action_enabled()` and raises
  `PermissionDenied` if it returns `False`.
- `GuardianParentPermissionMixin.dispatch()` — for child-create views. After checking the parent
  permission, it calls `cv_action_enabled()` with the resolved parent and raises `PermissionDenied`
  if it returns `False`.

## See Also

- [ListView](list_view.md) — `cv_list_actions` controls which per-row action buttons are shown
- [DeleteView](delete_view.md) — `cv_check_delete_protection()` for form-level delete blocking
- [Per-Object Permissions](guardian.md) — `cv_has_access` and guardian integration
