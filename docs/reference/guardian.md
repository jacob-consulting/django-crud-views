# Per-Object Permissions (django-guardian)

The `crud_views_guardian` sub-package adds per-object permission support via
[django-guardian](https://django-guardian.readthedocs.io/). Users opt in by
swapping `ViewSet` → `GuardianViewSet` and `*ViewPermissionRequired` →
`Guardian*ViewPermissionRequired`.

!!! example "Try it live"
    The [Guardian example](https://django-crud-views-demo.onrender.com/guardian/document/) in the live demo shows
    this in action — log in as `alice` / `alice` and as `bob` / `bob` to compare what each of them sees. See
    [Live demo](../getting_started/demo.md) for data resets and wake-up time.

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

The fallback is a **view** setting and nothing else. Each view class reads its own `cv_guardian_accept_global_perms`,
so two views of one `GuardianViewSet` can follow different policies. The ViewSet does not pass a value on to its views.

`GuardianViewSet` no longer accepts a `cv_guardian_accept_global_perms` key. The key never changed access, and
passing it now (as `True` or `False`, as a keyword or in `GuardianViewSet.model_validate({...})`) fails with a
Pydantic `ValidationError` that names the per-view replacement, and nothing is registered. Set the attribute on each
view class that should accept global permissions instead; see
[Migrating to 1.0.0](../migrating-1.0.md#the-guardianviewset-global-permission-key).

### The ViewSet helper is always strict

`GuardianViewSet.get_objects_for_user(user, perm)` has a fixed policy of its own and no option to change it. It never
accepts global model permissions. It does count object grants and group grants. An active superuser gets every
object, and an inactive user gets none. A view's `cv_guardian_accept_global_perms` does not change what the helper
returns, so a list view with the fallback can show rows the helper does not return.

### Inactive users

A user who is logged in but whose account is inactive (`is_active = False`, possible with a backend such as
`AllowAllUsersModelBackend`) gets no authority from any Guardian path. That applies to ordinary users, users with
object or group grants, users with only global permissions, and superusers. Every `Guardian*ViewPermissionRequired` view
answers such a user with 403 before it resolves a parent, an object or a formset fragment. That includes list and card
views, which return no rows, and an HTTP DELETE, which gets 403 rather than 405. The callable helpers deny such a user too:
`cv_has_access`, `cv_create_has_access`, `get_objects_for_user` (an empty queryset) and the delete-preview label
filter. Anonymous users keep their configured `cv_guardian_anonymous_behavior`. Deactivating a user or revoking a
grant takes effect on that user's next request.

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
standard case. It applies the same rule as the create view's dispatch, including the view's
`cv_guardian_accept_global_perms` fallback and a `None` permission key.

The URL-bound list override above is unchanged. On a child list page the parent comes from the URL, so `cv_access`
and `cv_action_enabled` of the create control are both computed from that parent. If the parent cannot be resolved
late (`Http404` or `KeyError`), both fields are `False` and no custom `cv_action_enabled` hook is called with `None`.

### What the create access helpers accept

`cv_has_access(user, obj)` and `cv_create_has_access(user, rendering_view, parent_obj)` on a nested
`GuardianCreateViewPermissionRequired` check **permission only**. The action state (`cv_action_enabled`) is a
separate field; see [Conditionally disabling an action](action_enabled.md). The object you pass decides which parent
the permission is checked on:

| Input | Result |
|---|---|
| An instance of the parent model | The permission is checked on that parent. |
| An instance of the create view's own model, with a `ForeignKey` to its parent | The parent is read through the configured attribute (`ParentViewSet.get_attribute()`, the `attribute` you declared or the parent ViewSet's name), and the permission is checked on it. For a Book the helpers answer exactly as they would for that Book's Publisher. |
| An own-model instance of a `ManyToMany` nesting (`many_to_many_through_attribute`) | Denied. The object exposes a related manager, not one parent, so it cannot tell which URL parent a create would use. |
| `None`, an instance of an unrelated model, or an own-model instance whose parent relation is empty or missing | Denied, superusers included. |

Before 1.0 these helpers returned `True` for any object that was not a parent instance, so a Book was granted
"add book" whatever the user held on its Publisher. Now an own child honors its actual parent's permission, and an
unrelated object denies. See [Migrating to 1.0.0](../migrating-1.0.md#nested-guardian-create-access).

The `ManyToMany` case fails closed on purpose. A helper, filter or control that only receives the child object has no
selected parent, and picking the first or only related parent would invent authority the URL never granted. What
does work for `ManyToMany` nesting:

- the helpers with an explicit parent instance, `Genre` create checked against `publisher_a`;
- the URL-bound child list, whose create control resolves the parent from the URL;
- direct create GET and POST under an authorized URL parent, including the `None` parent policy and the independent
  state rule.

On list pages, place the control through the URL-aware
[resolved button loop](../faq.md#render-a-custom-loop-of-buttons). Route-aware create controls for a `ManyToMany`
child's own page would need an explicit selected-parent contract. They are a possible future enhancement and are not
part of 1.0.

Top-level creates are unchanged: `cv_has_access(user, obj)` checks the model-level `add_<model>` permission, and
object grants never stand in for it.

## Parent Viewsets

When a child viewset has `parent=ParentViewSet(...)`, guardian checks permission
on the parent instance before dispatching any child view.

Configure what permission is required on the parent:

```python
cv_book = GuardianViewSet(
    model=Book,
    name="book",
    parent=ParentViewSet(name="author"),
    cv_guardian_parent_permission="view",  # for list/detail/update/delete
    cv_guardian_parent_create_permission="change",  # for create (None = use above)
)
```

`cv_guardian_parent_create_permission=None` (the default) means create views use
`cv_guardian_parent_permission` as well. Setting `cv_guardian_parent_permission=None`
disables the parent **permission** check, for create views too unless they have their own
`cv_guardian_parent_create_permission`.

`None` disables only that permission check. The rest still applies:

- The URL parent is still resolved, and a missing parent is a 404 for every child view, list included.
- A create view still runs its `cv_action_enabled(user, parent)` state check with the URL parent, so a disabled
  parent answers GET and POST with 403 and writes nothing.
- With `CreateViewParentMixin`, the created child is bound to the URL parent, whatever parent value the POST
  contains.
- No child-model `add_<model>` permission is required instead.
- The create access helpers return `True` for the parent and for a `ForeignKey` own child without any grant, and keep
  denying `None`, unrelated objects and `ManyToMany` own children.

The parent check follows the child view's `cv_guardian_accept_global_perms`: in
strict mode (the default) only a per-object grant on the parent counts; with the
flag set, a model-level permission on the parent model (e.g. `app.view_author`) is
accepted as a fallback.

## Formset fragments

The AJAX request that adds a formset row runs the same gates as the editor page it belongs to. On a Guardian update
view, a user without the object permission, with a revoked grant, or whose action state is disabled gets 403 and no
row, so the row's choices are never rendered for them. A missing target, or a target under another URL parent, gets
404. See [The AJAX template endpoint](formsets.md#the-ajax-template-endpoint).

## Group Permissions

Guardian group permissions are respected by default (`use_groups=True`).

```python
from guardian.shortcuts import assign_perm

assign_perm(cv_author.permissions["view"], group, author_instance)
```

## Cascading Deletes with Per-Object Permissions

When `cv_show_related_objects = True` on a Guardian delete view, the related objects
list is filtered using per-object `view` permissions instead of model-level permissions:

- Objects the user has per-object `view` permission for: shown with full details
- Objects the user lacks per-object `view` permission for: shown as aggregated counts

The same filter applies to the labels of protected objects (`on_delete=PROTECT`), the objects that block the
deletion. A protected object's label reaches the template only when the user holds `view` on that object, through an
object grant or a group grant. Labels of objects the user may not view are dropped before the template gets its
context, while the page still shows one generic "blocked" notice through `has_protected_objects`. The summary counts
are unchanged. See [Delete protection previews](delete_view.md#protected-objects).

The **delete view's** own `cv_guardian_accept_global_perms` decides whether a global `view_<model>` permission also
shows the labels of each related or protected model, not only whether it opens the deletion target. An object grant
shows its label without any global permission. The removed ViewSet key and the strict `get_objects_for_user` helper
play no part here.

`GuardianDeleteRelatedObjectsMixin` replaces the core model-level filter rather than adding to it. A custom
`cv_filter_related_objects` on a Guardian delete view should call `super()` (which applies the Guardian filter) and
narrow its result further, never re-run the core model-level filter after it or return the raw collection; see
[Custom related-object filters](delete_view.md#custom-related-object-filters).

```python
class PublisherDeleteView(CrispyViewMixin, GuardianDeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_publisher
    cv_show_related_objects = True
```

Performance: uses `guardian.shortcuts.get_objects_for_user` for bulk queryset filtering —
one query per related model, not one per object.

## Working Example

See `examples/bootstrap5/guardian_demo/` for a complete working example. After running
migrations, use the seed management command to set up demo users and data:

```bash
python manage.py seed
```

This creates the `alice` and `bob` demo users and assigns per-object permissions on the
seeded `Document` objects (see `guardian_demo/seed.py`):

| Document          | Owner | alice                | bob                  |
|-------------------|-------|----------------------|----------------------|
| Roadmap 2027      | alice | view, change, delete | —                    |
| Team Handbook     | alice | view, change, delete | view                 |
| Meeting Notes     | bob   | —                    | view, change, delete |
| Release Checklist | bob   | view, change         | view, change, delete |

## GuardianManageView

When `CRUD_VIEWS_MANAGE_VIEWS_ENABLED` is enabled (or a user is in the `CRUD_VIEWS_MANAGE` group), guardian-enabled viewsets show an enhanced manage page at `/<prefix>/manage/`.

In addition to the standard ManageView content, GuardianManageView adds:

**Guardian Configuration** — a table showing:
- `cv_guardian_parent_permission` — permission key checked on parent object for child views
- `cv_guardian_parent_create_permission` — permission key for child create views (falls back to `cv_guardian_parent_permission` if None)
- `parent_viewset` — parent viewset name and the permission used to grant access
- `GuardianViewSet.get_objects_for_user()` — the helper's fixed strict policy (object and group grants only)

**Global permission fallback** — one row per registered view with its own `cv_guardian_accept_global_perms` and the
effective policy:

| Effective policy | When |
|---|---|
| strict | the view checks object permissions (object or queryset mixin, or a parent check), and its flag is `False` |
| global fallback | the same, with the flag `True` |
| not applicable | the view never consults the flag: a plain or manage view, a top-level create, or a parent-only view whose parent permission key is `None` |

The values come from each view class, never from the ViewSet. Below the table the page states that
`get_objects_for_user()` is independent of these view policies and always strict.

A template that overrides the manage page reads the values from the context: `guardian_config.get_objects_for_user`
holds `{"policy": "strict", "accept_global_perms": False, "use_groups": True}`, and each `views.<key>.guardian_policy`
holds `global_fallback_applicable`, `cv_guardian_accept_global_perms` (`None` when not applicable) and
`effective_policy` (`"strict"`, `"global fallback"` or `"not applicable"`). The `guardian_config` key
`cv_guardian_accept_global_perms` is gone.

Who may open the manage page has not changed: `CRUD_VIEWS_MANAGE_VIEWS_ENABLED` (`"yes"`, `"debug_only"` with
`DEBUG`, or `"no"`) and membership of the `CRUD_VIEWS_MANAGE_GROUP` group (default `CRUD_VIEWS_MANAGE`) still
decide, not object permissions.

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

---

> To disable an action the user *is* permitted to perform, based on object state
> (e.g. a locked/open parent), see [Conditionally disabling an action](action_enabled.md).
