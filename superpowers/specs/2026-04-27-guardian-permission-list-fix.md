# Guardian Permission Fix: List Button Visibility

**Date:** 2026-04-27
**Status:** Approved
**Scope:** Fix broken "list" and "parent" context action buttons in guardian-integrated views; revert a regression in `base.py`

---

## Problem

Two bugs cause context action buttons to disappear when using `crud_views_guardian`:

### Bug 1: "list" button hidden on pages without an object

`ContextButton` always calls `cv_has_access(user, context.object)`. On pages without an object (create views, the list view itself), `context.object` is `None`. The base `CrudViewPermissionRequiredMixin.cv_has_access` then calls `user.has_perms(["app.view_model"])` — a model-level check. Guardian users have no model-level grants, so the check returns `False` and the "list" button disappears.

### Bug 2: "parent" button passes wrong-type object

`ParentContextButton` calls the parent list view's `cv_has_access` with `context.object` — which is the *child* model instance (e.g. a `Book`). Checking `view_author` permission on a `Book` object via guardian returns `False`, so the "parent" button disappears.

### Regression: base.py obj-passing breaks non-guardian views

A change was made to `CrudViewPermissionRequiredMixin.cv_has_access` in `crud_views/lib/view/base.py` to pass `obj` to `user.has_perms`. Django's `ModelBackend` explicitly returns an empty permission set when `obj is not None`, so this breaks per-row button visibility for all non-guardian views. This change must be reverted.

---

## Root Cause

The guardian list view is *always* accessible — queryset filtering (via `get_objects_for_user`) is the access gate, not `cv_has_access`. But `cv_has_access` for list views was never overridden in the guardian layer, so the base model-level check ran and failed for guardian-only users.

---

## Solution

Three targeted changes:

### 1. Revert `crud_views/lib/view/base.py`

Remove the `obj=` argument from `user.has_perms` in `CrudViewPermissionRequiredMixin.cv_has_access`:

```python
@classmethod
def cv_has_access(cls, user: User, obj: Model | None = None) -> bool:
    perm = cls.cv_viewset.permissions.get(cls.cv_permission)
    perms = (perm,) if perm else tuple()
    has_access = user.has_perms(perms)  # model-level only; guardian overrides handle per-object
    return has_access
```

The base class stays model-level only. Per-object checks belong exclusively in the guardian layer via overrides.

### 2. Override `cv_has_access` in `GuardianQuerysetMixin`

In `crud_views_guardian/lib/mixins.py`, add:

```python
@classmethod
def cv_has_access(cls, user, obj=None):
    return True
```

**Why always `True`:** The guardian list view is inherently accessible — `get_objects_for_user` filters the queryset to what the user can see. Gating button visibility with a model-level check is wrong (guardian users don't have model-level grants), and gating it with a per-object check is wrong (no single object represents "can you see the list"). The list button should always appear; an empty list is the correct result when the user has no grants.

This single override fixes both bugs:
- Bug 1: `cv_has_access(user, None)` → `True`
- Bug 2: `cv_has_access(user, book_instance)` → `True` (wrong-type object is ignored)

### 3. `GuardianObjectPermissionMixin.cv_has_access` — no change

Already correct: checks per-object guardian permission when `obj` is provided, returns `False` when `obj=None` (conservative — no object context means no access known).

---

## Files Changed

| File | Change |
|---|---|
| `crud_views/lib/view/base.py` | Revert obj-passing in `cv_has_access` |
| `crud_views_guardian/lib/mixins.py` | Add `cv_has_access` override to `GuardianQuerysetMixin` |

---

## Tests

| Scenario | Expected |
|---|---|
| "list" context button on create view (no object) | Visible (True) |
| "list" context button on detail view (has object) | Visible (True) |
| "parent" context button on child detail view | Visible (True) |
| Per-row detail/update/delete buttons for non-guardian user with model perm | Visible (True) — base.py revert must not break this |
| Per-row detail/update/delete buttons for guardian user with per-object grant | Visible (True) |
| Per-row detail/update/delete buttons for guardian user without per-object grant | Hidden (False) |
