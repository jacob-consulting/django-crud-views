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

Child create views **must** use `GuardianCreateViewPermissionRequired` (not
plain `CreateViewPermissionRequired`). Using the plain variant causes the
create button to always be hidden (falls back to a model-level `add_<model>`
check that guardian users typically don't have) and prevents the form page
from loading.

### Create button visibility for child viewsets

`cv_has_access` is a classmethod with no access to the request or URL kwargs.
When the create button is rendered from a child list page, `obj=None`, so the
parent cannot be looked up inside `cv_has_access` alone.

`GuardianListViewPermissionRequired` resolves this: its `cv_get_context`
override detects the child create case, fetches the parent object from the
URL kwargs via `cv_get_parent_object()`, and calls `cv_create_has_access` on
the create view class with the resolved parent.

The default `cv_create_has_access` checks `cv_guardian_parent_create_permission`
on the parent via guardian's `ObjectPermissionChecker`. Override it on the
create view class for custom logic:

```python
class BookCreateView(CreateViewParentMixin, GuardianCreateViewPermissionRequired):
    cv_viewset = cv_book
    form_class = BookCreateForm

    @classmethod
    def cv_create_has_access(cls, user, rendering_view, parent_obj):
        """
        rendering_view: the list view instance (has .request, .kwargs, etc.)
        parent_obj: resolved parent model instance, or None if lookup failed
        """
        if parent_obj is None:
            return False
        # custom logic, e.g. check role membership beyond the standard perm
        from guardian.core import ObjectPermissionChecker
        return ObjectPermissionChecker(user).has_perm("change_publisher", parent_obj)
```

When `cv_create_has_access` is not overridden, the default implementation
uses `cv_guardian_parent_create_permission` (falling back to
`cv_guardian_parent_permission`) — no extra configuration needed for the
standard case.

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

## GuardianManageView

When `CRUD_VIEWS_MANAGE_VIEWS_ENABLED` is enabled (or a user is in the `CRUD_VIEWS_MANAGE` group), guardian-enabled viewsets show an enhanced manage page at `/<prefix>/manage/`.

In addition to the standard ManageView content, GuardianManageView adds:

**Guardian Configuration** — a table showing:
- `cv_guardian_parent_permission` — permission key checked on parent object for child views
- `cv_guardian_parent_create_permission` — permission key for child create views (falls back to `cv_guardian_parent_permission` if None)
- `cv_guardian_accept_global_perms` — whether model-level permissions are accepted as a fallback
- `parent_viewset` — parent viewset name and the permission used to grant access

**Permission Holders** — extends the standard group listing with an "Objects (guardian)" column showing how many objects each group has per-object access to.

**Views table** — each registered view shows a `guardian_mixin` row listing which guardian mixins are active (`ObjectPermissionMixin`, `QuerysetMixin`, `ParentMixin`).

GuardianManageView is wired automatically by `GuardianViewSet.register()` — no manual configuration required.

### Customizing the Manage View Class

To use a custom manage view class for a specific viewset, set `manage_view_class` to a dotted import path:

```python
from crud_views_guardian.lib.viewset import GuardianViewSet

class MyCustomGuardianManageView(GuardianManageView):
    template_name = "myapp/custom_guardian_manage.html"

cv_author = GuardianViewSet(
    model=Author,
    name="author",
    manage_view_class="myapp.views.MyCustomGuardianManageView",
)
```

To apply a custom class globally to all guardian viewsets, set in `settings.py`:

```python
CRUD_VIEWS_GUARDIAN_MANAGE_VIEW_CLASS = "myapp.views.MyCustomGuardianManageView"
```

The per-viewset `manage_view_class` field takes priority over the global setting.

For plain `ViewSet` (non-guardian), the equivalent is:

```python
CRUD_VIEWS_MANAGE_VIEW_CLASS = "myapp.views.MyCustomManageView"
```
