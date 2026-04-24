# django-crud-views: django-guardian Integration Design

**Date:** 2026-04-24  
**Status:** Approved  
**Scope:** New `crud_views_guardian` sub-package providing per-object permissions via django-guardian

---

## Overview

Add optional per-object permission support to django-crud-views using django-guardian. The integration lives in a new `crud_views_guardian` sub-package, following the same pattern as `crud_views_polymorphic` and `crud_views_workflow`. Users opt in by swapping `ViewSet` → `GuardianViewSet` and `*ViewPermissionRequired` → `Guardian*ViewPermissionRequired`.

**Default strict mode:** Per-object checks default to `accept_global_perms=False` — a user with the global `view_author` Django permission but no per-object grant is denied access to individual author instances. This is configurable per view via `cv_guardian_accept_global_perms = True` to allow model-level fallback where needed. The sole exception is top-level create views, where no target object exists yet (see §Create Views).

---

## Package Structure

```
crud_views_guardian/
    __init__.py
    apps.py               # CrudViewsGuardianConfig
    lib/
        __init__.py
        mixins.py         # GuardianObjectPermissionMixin, GuardianQuerysetMixin,
                          # GuardianParentPermissionMixin
        views.py          # Guardian*ViewPermissionRequired drop-in classes
        viewset.py        # GuardianViewSet
```

Installed via:

```toml
# pyproject.toml
[project.optional-dependencies]
guardian = ["django-guardian>=2.4"]
```

---

## User Setup

```python
INSTALLED_APPS = [
    ...
    "guardian",
    "crud_views_guardian",
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "guardian.backends.ObjectPermissionBackend",
]

ANONYMOUS_USER_NAME = None  # disable anonymous user support
```

Then `python manage.py migrate` to create guardian's `UserObjectPermission` / `GroupObjectPermission` tables.

---

## Core Mixins (`lib/mixins.py`)

### `GuardianObjectPermissionMixin`

Used by single-object views (Detail, Update, Delete, Action). Hooks into `get_object()` — after the object is loaded, checks per-object permission. Raises 403 on denial.

`cv_guardian_accept_global_perms = False` (default) uses `ObjectPermissionChecker` which checks object-level permissions only, with no model-level fallback. Set to `True` to use `user.has_perm(perm, obj)` which includes model-level fallback via guardian's `ObjectPermissionBackend`.

Also overrides `cv_has_access(user, obj=None)`:
- When `obj` is provided: checks per-object permission (respecting `cv_guardian_accept_global_perms`) → drives per-row action button visibility
- When `obj=None`: returns `False` conservatively (no object context, can't determine access)

> **Confirmed:** The row object is already passed to `cv_has_access` by the existing infrastructure.
> `ActionColumn` receives `record` from django-tables2 → template passes it to `{% cv_list_action key record %}`
> → `cv_get_context()` calls `cls.cv_has_access(user, obj)` at `crud_views/lib/view/base.py:325`.
> Context action buttons on object pages also pass `context.object`. No template changes are required.

```python
from guardian.core import ObjectPermissionChecker

class GuardianObjectPermissionMixin:
    cv_guardian_accept_global_perms: bool = False

    def _check_object_perm(self, user, perm: str, obj) -> bool:
        if self.cv_guardian_accept_global_perms:
            return user.has_perm(perm, obj)
        checker = ObjectPermissionChecker(user)
        return checker.has_perm(perm.split('.')[1], obj)

    def get_object(self):
        obj = super().get_object()
        perm = self.cv_viewset.permissions.get(self.cv_permission)
        if not self._check_object_perm(self.request.user, perm, obj):
            raise PermissionDenied
        return obj

    @classmethod
    def cv_has_access(cls, user, obj=None):
        perm = cls.cv_viewset.permissions.get(cls.cv_permission)
        if obj is not None:
            if cls.cv_guardian_accept_global_perms:
                return user.has_perm(perm, obj)
            checker = ObjectPermissionChecker(user)
            return checker.has_perm(perm.split('.')[1], obj)
        return False
```

### `GuardianQuerysetMixin`

Used by list views. Replaces `get_queryset()` with a guardian-filtered version using `get_objects_for_user`. Defaults to `accept_global_perms=False` (strict) — only objects with an explicit per-object grant are returned. Set `cv_guardian_accept_global_perms = True` to also include objects the user can access via model-level permission.

```python
class GuardianQuerysetMixin:
    cv_guardian_accept_global_perms: bool = False

    def get_queryset(self):
        from guardian.shortcuts import get_objects_for_user
        qs = super().get_queryset()
        perm = self.cv_viewset.permissions.get(self.cv_permission)
        return get_objects_for_user(
            self.request.user, perm, qs,
            accept_global_perms=self.cv_guardian_accept_global_perms,
            use_groups=True,
        )
```

### `GuardianParentPermissionMixin`

Used by all child viewset views (list, detail, create, update, delete, action) when `cv_viewset.parent` is set. Checks per-object permission on the parent instance before dispatching.

The permission key to check is read from the child `GuardianViewSet`:
- For create views: `cv_guardian_parent_create_permission` (falls back to `cv_guardian_parent_permission`)
- For all other views: `cv_guardian_parent_permission`

When `cv_viewset.parent` is `None`, this mixin is a no-op.

```python
class GuardianParentPermissionMixin:
    def dispatch(self, request, *args, **kwargs):
        if self.cv_viewset.parent is not None:
            is_create = getattr(self, 'cv_permission', None) == 'add'
            perm_key = None
            if is_create:
                perm_key = getattr(self.cv_viewset, 'cv_guardian_parent_create_permission', None)
            if perm_key is None:
                perm_key = getattr(self.cv_viewset, 'cv_guardian_parent_permission', 'view')
            if perm_key is not None:
                parent_vs = self.cv_viewset.parent
                parent_pk = kwargs.get(parent_vs.pk_url_kwarg)
                parent_obj = get_object_or_404(parent_vs.model, pk=parent_pk)
                parent_perm = parent_vs.viewset.permissions.get(perm_key)
                if not request.user.has_perm(parent_perm, parent_obj):
                    raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
```

> **Implementation note:** `parent_vs.pk_url_kwarg` and `parent_vs.viewset` are assumed attribute names.
> Confirm exact names against the real `ParentViewSet` class before implementing.

---

## View Classes (`lib/views.py`)

Drop-in replacements. Guardian mixins are leftmost in MRO.

```python
# Single-object views
class GuardianDetailViewPermissionRequired(
    GuardianParentPermissionMixin, GuardianObjectPermissionMixin, DetailViewPermissionRequired
): pass

class GuardianUpdateViewPermissionRequired(
    GuardianParentPermissionMixin, GuardianObjectPermissionMixin, UpdateViewPermissionRequired
): pass

class GuardianDeleteViewPermissionRequired(
    GuardianParentPermissionMixin, GuardianObjectPermissionMixin, DeleteViewPermissionRequired
): pass

class GuardianActionViewPermissionRequired(
    GuardianParentPermissionMixin, GuardianObjectPermissionMixin, ActionViewPermissionRequired
): pass

# List view
class GuardianListViewPermissionRequired(
    GuardianParentPermissionMixin, GuardianQuerysetMixin, ListViewPermissionRequired
): pass

# Create view — no object exists; parent permission only for child creates,
# model-level add_<model> for top-level creates
class GuardianCreateViewPermissionRequired(
    GuardianParentPermissionMixin, CreateViewPermissionRequired
): pass
```

---

## Create Views: The Object-Existence Exception

`CreateView` has no target object. Guardian per-object enforcement is impossible on an object that does not yet exist. This is a hard constraint of the permission model.

**Top-level creates (e.g., Author, no parent):**  
`GuardianParentPermissionMixin` is a no-op. Django's standard `PermissionRequiredMixin` checks model-level `add_author`. Grant this permission globally to users or groups who should be allowed to create authors.

**Child creates (e.g., Book under Author):**  
The parent author instance exists. `GuardianParentPermissionMixin` checks `cv_guardian_parent_create_permission` on the parent author. No model-level `add_book` check is performed. This allows fine-grained control: "only users with `change` permission on author X can add books to author X".

---

## `GuardianViewSet` (`lib/viewset.py`)

Extends `ViewSet` with guardian configuration and convenience helpers.

```python
class GuardianViewSet(ViewSet):
    # Permission key checked on parent object for child list/detail/update/delete
    cv_guardian_parent_permission: str | None = "view"
    # Permission key checked on parent object for child create views
    # None = fall back to cv_guardian_parent_permission
    cv_guardian_parent_create_permission: str | None = None

    def assign_perm(self, perm: str, user_or_group, obj):
        """Assign per-object permission. perm is a short key: "view", "change", etc."""
        from guardian.shortcuts import assign_perm
        assign_perm(self.permissions[perm], user_or_group, obj)

    def remove_perm(self, perm: str, user_or_group, obj):
        from guardian.shortcuts import remove_perm
        remove_perm(self.permissions[perm], user_or_group, obj)

    def get_objects_for_user(self, user, perm: str, qs=None):
        from guardian.shortcuts import get_objects_for_user
        return get_objects_for_user(
            user, self.permissions[perm],
            qs or self.model.objects.all(),
            accept_global_perms=False,
            use_groups=True,
        )
```

---

## Tests (`tests/test1/test_guardian.py`)

A new `user_guardian_perm(user, viewset, perm, obj)` helper assigns per-object permissions via `guardian.shortcuts.assign_perm`.

| Scenario | Expected |
|---|---|
| Object-level perm granted → detail/update/delete | 200 |
| No per-object perm → detail/update/delete | 403 |
| Model-level perm only (no per-object grant) → detail | 403 (strict mode) |
| List view: only returns objects with per-object view perm | queryset filtered |
| Top-level create with model-level `add_<model>` | 200 |
| Top-level create without model-level perm | 403 |
| Child create with parent per-object perm | 200 |
| Child create without parent per-object perm | 403 |
| `cv_guardian_parent_create_permission` differs from `cv_guardian_parent_permission` | correct perm checked per view type |
| Group with per-object perm grants access | 200 |
| `cv_has_access(user, obj)` with grant | True |
| `cv_has_access(user, obj)` without grant | False |
| `cv_has_access(user)` no object | False |

---

## Documentation (`docs/guardian.md`)

New page covering:
- Installation and setup
- Swapping `ViewSet` → `GuardianViewSet` and view classes
- Assigning and revoking per-object permissions
- The create exception
- Parent permission configuration
- Strict mode explanation
- Group permissions

Added to `mkdocs.yml` navigation.

---

## README

One section added to the optional integrations area:

```markdown
### Per-Object Permissions (django-guardian)

pip install django-crud-views[guardian]
```

With a link to the docs page.

---

## Example (`examples/bootstrap5`)

Extend the existing Author/Book example:
- `cv_author` → `GuardianViewSet`
- All author views → `Guardian*` variants
- `cv_book` gets `cv_guardian_parent_permission = "view"` and `cv_guardian_parent_create_permission = "change"`
- Management command or fixture assigns per-object permissions to example users
- Note in example README explaining what permissions to assign to observe the behaviour
