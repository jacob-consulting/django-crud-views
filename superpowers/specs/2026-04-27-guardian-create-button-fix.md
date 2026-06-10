# Guardian Create Button Visibility Fix

**Date:** 2026-04-27
**Status:** Approved
**Scope:** Fix disabled "add" context action button for child create views in guardian-integrated viewsets

---

## Problem

In a child viewset (e.g. Book under Author), the "add" context button on the book list page is always disabled for guardian users. The root cause:

1. `GuardianCreateViewPermissionRequired` has no `cv_has_access` override.
2. The button renderer calls `cv_has_access(user, None)` on the book list page (list views have no object).
3. The base `CrudViewPermissionRequiredMixin.cv_has_access` calls `user.has_perms(["app.add_book"])` — a model-level check.
4. Guardian users have no model-level `add_book` — only per-object grants on parent objects.
5. Result: button disabled even though the user has `change` on the parent Author and would pass the dispatch check.

The actual access enforcement is already correct — `GuardianParentPermissionMixin.dispatch()` checks the parent object permission and raises 403 if denied. The button visibility check is simply wrong.

---

## Solution

Override `cv_has_access` in `GuardianCreateViewPermissionRequired` in `crud_views_guardian/lib/views.py`.

### Three cases

**Case 1 — Top-level create (no parent viewset):**
Fall through to the base class model-level `add_<model>` check. Top-level creates have no parent object and the guardian design intentionally requires a model-level grant to create root objects.

**Case 2 — Child create, no object available (e.g. book list page):**
`obj=None` — the button is rendered in a list context where no specific object exists. Return `True`. The actual permission check happens in `dispatch()` via `GuardianParentPermissionMixin`. A user who doesn't have the required parent permission will get a 403 on click — which is the standard guardian enforcement pattern.

**Case 3 — Child create, parent object available (e.g. author detail page):**
`obj` is provided and is an instance of the parent model. Check the guardian parent permission (`cv_guardian_parent_create_permission` or `cv_guardian_parent_permission`) on that specific parent object. This gives precise per-object button visibility — the button only shows for authors the user actually has permission to add books under.

If `obj` is provided but is NOT an instance of the parent model (unexpected type), fall back to `True` — we cannot determine access without the right object.

### Implementation

In `crud_views_guardian/lib/views.py`, add a `cv_has_access` classmethod to `GuardianCreateViewPermissionRequired`:

```python
class GuardianCreateViewPermissionRequired(GuardianParentPermissionMixin, CreateViewPermissionRequired):

    @classmethod
    def cv_has_access(cls, user, obj=None):
        """
        Three-case permission check for create button visibility.

        Case 1 — Top-level create (cv_viewset.parent is None):
            Falls through to the base class, which checks the model-level
            add_<model> permission. Top-level creates intentionally require a
            model-level grant; there is no parent object to check against.

        Case 2 — Child create, no object (obj=None, e.g. book list page):
            Returns True unconditionally. The list page has no single object, so
            we cannot check the parent permission here. The real enforcement
            happens in dispatch() via GuardianParentPermissionMixin, which checks
            the parent object permission and raises 403 if denied. A user without
            the required grant will be stopped on click — the button showing is
            correct UX.

        Case 3 — Child create, parent object available (e.g. author detail page):
            When obj is an instance of the parent model, checks
            cv_guardian_parent_create_permission (falling back to
            cv_guardian_parent_permission) on that specific parent object via
            guardian's ObjectPermissionChecker. This gives precise per-object
            button visibility: "add book" only appears for parent objects the user
            is actually allowed to create children under.

            If obj is provided but is not an instance of the parent model
            (unexpected; wrong type passed by some other render path), falls back
            to True — cannot determine access without the right object type.
        """
        if cls.cv_viewset.parent is None:
            return super().cv_has_access(user, obj)

        if obj is None:
            return True

        parent_vs = cls.cv_viewset.parent.viewset
        if isinstance(obj, parent_vs.model):
            perm_key = (
                getattr(cls.cv_viewset, "cv_guardian_parent_create_permission", None)
                or getattr(cls.cv_viewset, "cv_guardian_parent_permission", "view")
            )
            perm = parent_vs.permissions.get(perm_key)
            accept_global = getattr(cls, "cv_guardian_accept_global_perms", False)
            if accept_global and user.has_perm(perm):
                return True
            from guardian.core import ObjectPermissionChecker
            return ObjectPermissionChecker(user).has_perm(perm.split(".")[1], obj)

        return True
```

---

## Files Changed

| File | Change |
|---|---|
| `crud_views_guardian/lib/views.py` | Add `cv_has_access` to `GuardianCreateViewPermissionRequired` |
| `tests/test1/test_guardian.py` | Add tests for all three cases |

---

## Tests

| Scenario | Expected |
|---|---|
| Top-level create, user has model-level add perm | True |
| Top-level create, user has no model-level add perm | False |
| Child create, obj=None, user has parent perm | True |
| Child create, obj=None, user has no parent perm | True (enforcement in dispatch) |
| Child create, obj=parent instance, user has required perm | True |
| Child create, obj=parent instance, user has no perm | False |
| Child create, obj=wrong type | True (fallback) |
