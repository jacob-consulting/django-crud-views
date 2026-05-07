# Guardian Child Create Button Visibility

**Date:** 2026-05-07

## Problem

When a `GuardianViewSet` child viewset (e.g. `NetzwerkMember`) renders its list view, the "create" context action button is always visible to all authenticated users. The correct behaviour is: only users with the required per-object permission on the parent (e.g. `change` on the specific `Netzwerk`) should see the button.

### Root cause

`cv_has_access` is a classmethod — it has no access to the request or URL kwargs. When the create button is rendered from the member list page, `obj=None` is passed. The current `GuardianCreateViewPermissionRequired.cv_has_access` Case 2 (`obj=None`, has parent) unconditionally returns `True`. There is no parent object to check guardian permissions against.

Additionally, `NetzwerkMemberCreateView` currently extends `CreateViewPermissionRequired` instead of `GuardianCreateViewPermissionRequired`, which causes `cv_has_access` to fall through to a model-level permission check (`user.has_perms(("app.add_netzwerkmember",))`). Guardian users don't have this model-level permission, so the button never appears.

### Why model-level perms don't work

Membership roles (Mitglied / Verwalter) are per-Netzwerk guardian group object permissions. The same user can be Mitglied in one Netzwerk and Verwalter in another. A single model-level `add_netzwerkmember` flag cannot represent this — it would either grant or deny create access globally across all Netzwerke.

## Design

Three coordinated changes in `crud_views_guardian`, plus a fix in application code.

### 1. `GuardianCreateViewPermissionRequired` gets `cv_create_has_access`

A new classmethod on `GuardianCreateViewPermissionRequired` with a default implementation that checks the guardian per-object permission on the parent using `cv_guardian_parent_create_permission`:

```python
@classmethod
def cv_create_has_access(cls, user, rendering_view, parent_obj):
    if parent_obj is None:
        return False
    perm_key = (
        getattr(cls.cv_viewset, "cv_guardian_parent_create_permission", None)
        or getattr(cls.cv_viewset, "cv_guardian_parent_permission", "view")
    )
    perm = cls.cv_viewset.parent.viewset.permissions.get(perm_key)
    from guardian.core import ObjectPermissionChecker
    return ObjectPermissionChecker(user).has_perm(perm.split(".")[1], parent_obj)
```

**Signature:** `(cls, user: User, rendering_view: CrudView, parent_obj: Model | None) -> bool`

- `user` — the requesting user
- `rendering_view` — the view instance rendering the button (e.g. `NetzwerkMemberListView`); has access to `rendering_view.request`, `rendering_view.kwargs`, etc.
- `parent_obj` — the resolved parent model instance, or `None` if resolution failed

Application code overrides this classmethod on the create view class for custom logic:

```python
class NetzwerkMemberCreateView(..., GuardianCreateViewPermissionRequired):
    @classmethod
    def cv_create_has_access(cls, user, rendering_view, parent_obj):
        # e.g. check role membership, multiple conditions, etc.
        ...
```

Callable lives on the **create view class** (not the viewset) because:
- The create view already owns `cv_has_access`; all access logic stays in one place
- Plain Python classmethod override is idiomatic; a Pydantic callable field on the viewset is awkward
- The viewset remains a routing/config object, not a logic object

### 2. `GuardianQuerysetMixin` overrides `cv_get_context`

`cv_get_context` is an **instance method** with access to `self.kwargs`. This is the bridge: the list view instance can resolve the parent object from the URL, then call `cv_create_has_access` with it.

```python
def cv_get_context(self, key=None, obj=None, user=None, request=None):
    ctx = super().cv_get_context(key=key, obj=obj, user=user, request=request)

    if obj is None and key is not None and self.cv_viewset.has_parent:
        if self.cv_viewset.is_view_registered(key):
            target_cls = self.cv_viewset.get_view_class(key)
        else:
            target_cls = None
        if target_cls and getattr(target_cls, 'cv_permission', None) == 'add':
            if hasattr(target_cls, 'cv_create_has_access'):
                try:
                    parent_obj = self.cv_get_parent_object()
                except Exception:
                    parent_obj = None
                ctx['cv_access'] = target_cls.cv_create_has_access(user, self, parent_obj)

    return ctx
```

**Why post-patch:** calling `super()` first builds the full context (URL, label, icon). Only `cv_access` is replaced — no duplication of context-building logic.

**Placement in `GuardianQuerysetMixin`:** this mixin is already applied to `GuardianListViewPermissionRequired`, which is the view that renders the create context action button from the list page.

### 3. `GuardianCreateViewPermissionRequired.cv_has_access` Case 2 becomes `False`

```python
if obj is None:
    return False   # was: return True
```

The list view override (Part 2) handles the correct check. This becomes a safe fallback for any call path that bypasses the override. Fails closed.

### 4. Application fix: use `GuardianCreateViewPermissionRequired`

`NetzwerkMemberCreateView` (and `ProjektMemberCreateView`) must extend `GuardianCreateViewPermissionRequired` instead of `CreateViewPermissionRequired`. Required for:

- `GuardianParentPermissionMixin.has_permission()` bypass — so the form page actually loads for guardian users without a model-level `add_<model>` permission
- `cv_has_access` Case 3 — when the create button appears on the parent detail page and `obj` IS the parent instance, the guardian per-object check fires directly without going through the list view override
- Picking up the default `cv_create_has_access` implementation

## Data flow

| Context | `obj` | Path |
|---|---|---|
| Member list page | `None` | `GuardianQuerysetMixin.cv_get_context` resolves parent from `self.kwargs` → calls `cv_create_has_access(user, self, parent_obj)` |
| Parent detail page | Parent instance | `cv_has_access` Case 3 → guardian per-object check |
| Edge case (no parent resolvable) | `None`, no override | Case 2 → `False` (fails closed) |

## Files to change

### `crud_views_guardian`
- `crud_views_guardian/lib/views.py` — `GuardianCreateViewPermissionRequired`: add `cv_create_has_access` classmethod; change Case 2 from `return True` to `return False`
- `crud_views_guardian/lib/mixins.py` — `GuardianQuerysetMixin`: add `cv_get_context` override

### Application code (`meinamm`)
- `src/meinamm/views/netzwerk_member.py` — `NetzwerkMemberCreateView`: `CreateViewPermissionRequired` → `GuardianCreateViewPermissionRequired`
- `src/meinamm/views/projekt_member.py` — `ProjektMemberCreateView`: same change

## Tests to add

- `cv_create_has_access` default: returns True when user has required guardian perm on parent, False otherwise
- `cv_create_has_access` default: returns False when `parent_obj=None`
- `GuardianQuerysetMixin.cv_get_context`: resolves parent and calls `cv_create_has_access` when `obj=None` and key targets a child create view
- `GuardianQuerysetMixin.cv_get_context`: does not interfere with non-create keys
- `cv_has_access` Case 2: returns `False` (not `True`)
- Override of `cv_create_has_access` on a subclass is respected
