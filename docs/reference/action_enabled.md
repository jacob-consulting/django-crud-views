# Conditionally Disabling an Action

`cv_action_enabled` is a state gate beside permission. Package link consumers check permission first and skip
state after denial, as listed under [Enforcement Points](#enforcement-points). Calling this hook directly does
not grant permission. A direct state call is independent of package permission admission: it can return `True`
even when a link is denied by actor or permission gates.
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
for nested views without an own object; otherwise it returns `None`. A permitted link passes the same action
object, separately from the own object supplied to `cv_has_access`. For non-object targets own permission
receives `None`, while state receives the URL parent (for example, the Book of a nested list of notes).
Child links use the row their URL is built from;
own-ViewSet links use the resolved guard state. The immediate and known higher ancestors are aligned to the
target's declared ancestry; unknown levels stay unknown and are not fetched. A missing immediate parent denies
a nested link without calling state, even on a custom or non-CRUD view without guard state.

Cancel (core and Guardian) alone retains the `cv_get_parent_object` hook for its immediate parent, including nested object
targets. Guarded requests reuse the resolved parent without a query; unguarded views retain the existing
lookup. A missing built-in parent row means unavailable; custom-hook exceptions propagate. Higher ancestors
still come only from guard state. Move parent annotations needed by ordinary create controls to the parent
ViewSet's queryset. The create permission hook receives the real rendering view only on its own ViewSet,
including row, card, object and navbar consumers; otherwise it receives `None`.

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
Context, parent, sibling and child buttons, view-key context/table actions, own/child card actions, navbar
items, core/Guardian Cancel and the bulk toolbar use the shared permission-first check. Known ancestor gates precede
own access and state. A permission denial skips the state hook and leaves the context flag
`cv_action_enabled=True`, meaning not evaluated; the permission result still hides or disables the control.
The `cv_context_has_permission` filter checks ancestors and own permission but never evaluates state; it can
return true for an action that state would disable. All known-parent Guardian create controls and Guardian
Cancel check declared immediate and known higher gates; queryset-only Guardian links and Cancel now check
the declared immediate policy too. Nested Guardian actor admission and parent gates run before any create
override. The default create hook deliberately repeats its bounded immediate-parent check and never evaluates
state itself. Parent-only non-create Guardian Cancel omits `cv_has_access`, including overrides, but keeps
actor, ancestor and state checks; ordinary links keep their own hook and its
[documented limitation](guardian.md#parent-only-non-create-limitation). No state adapter resolves a parent from
a page object: ordinary consumers use supplied ancestry, while Cancel retains the parent hook above.
See [Link consumer migration](../migrating-1.0.md#link-access-hooks).

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
