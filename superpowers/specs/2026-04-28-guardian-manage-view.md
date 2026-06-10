# GuardianManageView — Design Spec

**Date:** 2026-04-28
**Status:** Approved
**Scope:** Enhance ManageView with group-based access, permission holder display, and a new GuardianManageView for guardian-enabled viewsets

---

## Problem

ManageView currently has two gaps:

1. **Access control is all-or-nothing.** `CRUD_VIEWS_MANAGE_VIEWS_ENABLED` is a global setting — there is no way to grant specific users manage access without turning it on for everyone. Sharing the manage page with a client or QA team member requires changing a deployment setting.

2. **No permission holder visibility.** The permissions table shows whether the *current user* has each permission, but nothing about which groups or users hold those permissions. For guardian-enabled viewsets there is no display of guardian config or per-object permission stats at all.

---

## Solution

### 1. Group-based ManageView access

Always register `AutoManageView` (remove the conditional creation). Move all gating into `has_permission()`:

```python
def has_permission(self):
    if crud_views_settings.manage_views_enabled == "yes":
        return True
    if crud_views_settings.manage_views_enabled == "debug_only" and settings.DEBUG:
        return True
    group_name = crud_views_settings.manage_group  # default: "CRUD_VIEWS_MANAGE"
    return self.request.user.groups.filter(name=group_name).exists()
```

A new setting `CRUD_VIEWS_MANAGE_GROUP` (default `"CRUD_VIEWS_MANAGE"`) lets the group name be changed. The URL always exists but returns 403 for users who don't qualify — standard Django pattern.

### 2. Permission Holders section (base ManageView)

A new "Permission Holders" section appears below the existing Permissions table. It lists every group that holds each permission, distinguishing model-level grants from guardian per-object grants:

| Group | Permission | Model-level | Objects (guardian) |
|---|---|---|---|
| admins | delete | ✓ | — |
| editors | change | — | 12 objects |
| editors | view | ✓ | 8 objects |
| viewers | view | ✓ | — |

For non-guardian viewsets the "Objects (guardian)" column is omitted. A `show_users` flag (default `False`, controlled by `CRUD_VIEWS_MANAGE_SHOW_USERS` setting) optionally adds a Users column.

`ManageView` gains a `get_permission_holders()` method:

```python
def get_permission_holders(self):
    rows = []
    ct = ContentType.objects.get_for_model(self.cv_viewset.model)
    for key, perm in self.cv_viewset.permissions.items():
        codename = perm.split(".")[1]
        for group in Group.objects.filter(permissions__codename=codename):
            rows.append({"group": group.name, "permission": key, "has_model_perm": True, "object_count": None})
    return rows
```

### 3. GuardianManageView

`GuardianManageView(ManageView)` lives in `crud_views_guardian/lib/views.py`. It adds three things to the manage page:

**Guardian Configuration section** (highlighted block, after Properties):

| Attribute | Value |
|---|---|
| cv_guardian_parent_permission | view |
| cv_guardian_parent_create_permission | change |
| cv_guardian_accept_global_perms | False |
| Parent viewset | publisher (change_publisher → guardian) |

**Permission Holders** — overrides `get_permission_holders()` to include guardian per-object counts via `GroupObjectPermission`:

```python
from guardian.models import GroupObjectPermission
from django.db.models import Count

GroupObjectPermission.objects.filter(
    permission__content_type=ct,
    permission__codename=codename,
).values("group__name").annotate(object_count=Count("object_pk", distinct=True))
```

Rows with model-level grants and guardian grants are merged: a group can appear once with both `has_model_perm=True` and `object_count=12`.

**Views table** — adds a "Guardian Mixin" column showing which mixin(s) each view uses (e.g. `QuerysetMixin`, `ObjectPermissionMixin + ParentMixin`, `ParentMixin`). Derived by inspecting the view's MRO for guardian mixin classes.

### 4. GuardianViewSet.register() wiring

`GuardianViewSet` overrides `register()` to create `AutoManageView` subclassing `GuardianManageView`:

```python
@model_validator(mode="after")
def register(self) -> Self:
    result = super().register()
    from crud_views_guardian.lib.views import GuardianManageView

    class AutoManageView(GuardianManageView):
        model = self.model
        cv_viewset = self

    return result
```

The base `ViewSet.register()` always creates `AutoManageView(ManageView)` now (no conditional). `GuardianViewSet.register()` replaces it with `AutoManageView(GuardianManageView)`.

---

## Files Changed

| File | Change |
|---|---|
| `crud_views/lib/settings.py` | Add `manage_group: str = "CRUD_VIEWS_MANAGE"` and `manage_show_users: bool = False` |
| `crud_views/lib/views/manage.py` | Update `has_permission()`, add `get_permission_holders()`, update `get_context_data()` |
| `crud_views/lib/viewset/__init__.py` | Always create `AutoManageView` (remove conditional `if switch ==` guard) |
| `crud_views_guardian/lib/views.py` | Add `GuardianManageView(ManageView)` |
| `crud_views_guardian/lib/viewset.py` | Override `register()` to wire `GuardianManageView` |
| `crud_views/templates/crud_views/view_manage.html` | Add Permission Holders section |
| `crud_views_guardian/templates/crud_views/view_guardian_manage.html` | New template, extends base, adds Guardian Config section and Guardian Mixin column |
| `tests/test1/test_manage.py` | 4 new tests (see Testing) |
| `tests/test1/test_guardian.py` | 4 new tests (see Testing) |
| `docs/reference/settings.md` | Document `CRUD_VIEWS_MANAGE_GROUP`, `CRUD_VIEWS_MANAGE_SHOW_USERS` |
| `docs/reference/guardian.md` | Add GuardianManageView section |
| `skills/django-crud-views/SKILL.md` | Update ManageView entry; add GuardianManageView under guardian section |

---

## New Settings

| Setting | Type | Default | Description |
|---|---|---|---|
| `CRUD_VIEWS_MANAGE_GROUP` | `str` | `"CRUD_VIEWS_MANAGE"` | Django group name that grants manage view access |
| `CRUD_VIEWS_MANAGE_SHOW_USERS` | `bool` | `False` | Whether to include a Users column in Permission Holders |

---

## Templates

**`view_manage.html`** gains a Permission Holders section using a `{% block permission_holders %}` so `GuardianManageView`'s template can extend it with the Objects column.

**`view_guardian_manage.html`** extends `view_manage.html` and:
- Inserts `{% block guardian_config %}` (the highlighted Guardian Configuration table) after Properties
- Overrides `{% block permission_holders %}` to add the Objects (guardian) column
- Overrides the Views table block to add the Guardian Mixin column

---

## Testing

### `tests/test1/test_manage.py` — 4 new tests

| Test | Assertion |
|---|---|
| `test_manage_accessible_via_crud_views_manage_group` | User in `CRUD_VIEWS_MANAGE` group gets 200 even when setting is `"no"` |
| `test_manage_blocked_without_group_or_setting` | User not in group and setting `"no"` gets 403 |
| `test_manage_context_has_permission_holders` | `context["permission_holders"]` is present and non-empty |
| `test_manage_permission_holders_shows_groups` | Groups with model-level perms appear correctly in the list |

### `tests/test1/test_guardian.py` — 4 new tests

| Test | Assertion |
|---|---|
| `test_guardian_manage_view_registered` | `GuardianManageView` is registered on `cv_guardian_author` |
| `test_guardian_manage_context_has_guardian_config` | `context["guardian_config"]` contains `cv_guardian_parent_permission` etc. |
| `test_guardian_manage_permission_holders_has_object_count` | After assigning per-object perm to a group, row shows correct object count |
| `test_guardian_manage_views_have_mixin_info` | `context["views"]` rows include `guardian_mixin` key |

---

## Skill Symlink

The project-local skill at `skills/django-crud-views/` is the source of truth. The global skill is replaced with a symlink:

```bash
rm -rf ~/.claude/skills/django-crud-views
ln -s /home/alex/projects/alex/django-crud-views/skills/django-crud-views ~/.claude/skills/django-crud-views
```

This is a one-time setup step included in the implementation plan.
