# Per-Object Permissions (django-guardian)

The `crud_views_guardian` sub-package adds per-object permission support via
[django-guardian](https://django-guardian.readthedocs.io/). Users opt in by
swapping `ViewSet` → `GuardianViewSet` and `*ViewPermissionRequired` →
`Guardian*ViewPermissionRequired`.

## Installation

```bash
pip install django-crud-views[guardian]
```

## Setup

```python
INSTALLED_APPS = [
    ...
    "guardian",
    "crud_views_guardian.apps.CrudViewsGuardianConfig",
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "guardian.backends.ObjectPermissionBackend",
]

ANONYMOUS_USER_NAME = None
```

Then run migrations:

```bash
python manage.py migrate
```

## Usage

Replace `ViewSet` with `GuardianViewSet` and each `*ViewPermissionRequired` with
its `Guardian*` equivalent:

```python
from crud_views_guardian.lib.viewset import GuardianViewSet
from crud_views_guardian.lib.views import (
    GuardianListViewPermissionRequired,
    GuardianDetailViewPermissionRequired,
    GuardianCreateViewPermissionRequired,
    GuardianUpdateViewPermissionRequired,
    GuardianDeleteViewPermissionRequired,
)

cv_author = GuardianViewSet(model=Author, name="author")

class AuthorListView(ListViewTableMixin, GuardianListViewPermissionRequired):
    cv_viewset = cv_author
    ...

class AuthorDetailView(GuardianDetailViewPermissionRequired):
    cv_viewset = cv_author
    ...
```

## Assigning Per-Object Permissions

```python
# Grant user permission to view a specific author
cv_author.assign_perm("view", user, author_instance)

# Grant a group permission
cv_author.assign_perm("change", group, author_instance)

# Revoke permission
cv_author.remove_perm("view", user, author_instance)

# Get all objects a user can view
qs = cv_author.get_objects_for_user(user, "view")
```

## Strict Mode (Default)

By default, `cv_guardian_accept_global_perms = False`: a user with a model-level
`view_author` Django permission is **not** granted access to individual objects.
Only explicit per-object grants (via `assign_perm`) count.

To allow model-level permissions as a fallback for a specific view:

```python
class AuthorDetailView(GuardianDetailViewPermissionRequired):
    cv_viewset = cv_author
    cv_guardian_accept_global_perms = True
```

## Create Views

`CreateView` cannot check per-object permission on an object that does not exist
yet. Two cases:

**Top-level creates** (no parent viewset): Django's standard model-level
`add_<model>` permission is checked. Grant this globally to users who should
be able to create objects.

**Child creates** (with parent viewset): The parent object exists. Guardian
checks per-object permission on the parent using
`cv_guardian_parent_create_permission`. No model-level check is made on the
child model.

## Parent Viewsets

When a child viewset has `parent=ParentViewSet(...)`, guardian checks permission
on the parent instance before dispatching any child view.

Configure what permission is required on the parent:

```python
cv_book = GuardianViewSet(
    model=Book,
    name="book",
    parent=ParentViewSet(name="author"),
    cv_guardian_parent_permission="view",          # for list/detail/update/delete
    cv_guardian_parent_create_permission="change", # for create (None = use above)
)
```

Setting either to `None` disables the parent check for that view type.

## Group Permissions

Guardian group permissions are respected by default (`use_groups=True`).

```python
from guardian.shortcuts import assign_perm

assign_perm(cv_author.permissions["view"], group, author_instance)
```

## Working Example

See `examples/bootstrap5/` for a complete working example. After running
migrations, use the management command to set up demo users with per-object
permissions:

```bash
python manage.py setup_guardian_demo
```

This creates `editor` (full access) and `reader` (view only) users with
per-object permissions assigned to all existing objects.
