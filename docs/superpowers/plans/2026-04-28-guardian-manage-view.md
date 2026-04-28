# GuardianManageView Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enhance ManageView with group-based access control and permission holder display, and add a new GuardianManageView showing guardian-specific configuration and per-object permission stats.

**Architecture:** `ManageView` gains group-based `has_permission()` and `get_permission_holders()`. `GuardianManageView(ManageView)` in `crud_views_guardian/` overrides both to add guardian config and per-object counts. `GuardianViewSet.register()` wires in `GuardianManageView` instead of `ManageView`. `AutoManageView` is always registered (URL access gated by `has_permission()` rather than conditional class creation).

**Tech Stack:** Python, Django, django-guardian, pytest-django, Django templates

---

## File Structure

| File | Change |
|---|---|
| `crud_views/lib/settings.py` | Add `manage_group` and `manage_show_users` settings |
| `crud_views/lib/views/manage.py` | Update `has_permission()`, add `get_permission_holders()`, update `get_context_data()` |
| `crud_views/lib/viewset/__init__.py` | Remove conditional `if switch ==` guard — always create `AutoManageView` |
| `crud_views/templates/crud_views/view_manage.html` | Add `{% block guardian_config %}` placeholder and `{% block permission_holders %}` section |
| `crud_views_guardian/lib/views.py` | Add `GuardianManageView(ManageView)` |
| `crud_views_guardian/lib/viewset.py` | Override `register()` to wire `GuardianManageView` |
| `crud_views_guardian/templates/crud_views/view_guardian_manage.html` | New template extending base; adds guardian config section and Objects column |
| `tests/test1/test_manage.py` | 4 new tests |
| `tests/test1/test_guardian.py` | 4 new tests |
| `docs/reference/settings.md` | Document 2 new settings |
| `docs/reference/guardian.md` | Add GuardianManageView section |
| `skills/django-crud-views/SKILL.md` | Update ManageView entry + add GuardianManageView under guardian section |

---

### Task 1: Add settings + always register AutoManageView

**Files:**
- Modify: `crud_views/lib/settings.py`
- Modify: `crud_views/lib/viewset/__init__.py:114-120`

- [ ] **Step 1: Add two new settings to CrudViewsSettings**

In `crud_views/lib/settings.py`, add after the `manage_views_enabled` line (line 34):

```python
    manage_group: str = from_settings("CRUD_VIEWS_MANAGE_GROUP", default="CRUD_VIEWS_MANAGE")
    manage_show_users: bool = from_settings("CRUD_VIEWS_MANAGE_SHOW_USERS", default=False)
```

- [ ] **Step 2: Always create AutoManageView in ViewSet.register()**

In `crud_views/lib/viewset/__init__.py`, replace lines 114–120:

```python
        switch = crud_views_settings.manage_views_enabled
        if switch == "yes" or switch == "debug_only" and settings.DEBUG:

            class AutoManageView(ManageView):
                model = self.model
                cv_viewset = self
```

with:

```python
        class AutoManageView(ManageView):
            model = self.model
            cv_viewset = self
```

Also remove the now-unused `from django.conf import settings` import on line 6 — `settings.DEBUG` was only used in the removed conditional and is no longer referenced in this file.

- [ ] **Step 3: Run existing manage tests to verify nothing broke**

```bash
pytest tests/test1/test_manage.py -v
```

Expected: 9 passed (all existing tests still pass — `has_permission()` still returns `True`, `AutoManageView` is always registered).

- [ ] **Step 4: Commit**

```bash
git add crud_views/lib/settings.py crud_views/lib/viewset/__init__.py
git commit -m "feat: always register AutoManageView, add manage_group and manage_show_users settings"
```

---

### Task 2: ManageView group-based access + permission holders (TDD)

**Files:**
- Modify: `crud_views/lib/views/manage.py`
- Test: `tests/test1/test_manage.py`

- [ ] **Step 1: Write 4 failing tests**

Append to `tests/test1/test_manage.py`:

```python
# ── Group-based access and permission holders ──────────────────────────────────


@pytest.mark.django_db
def test_manage_accessible_via_crud_views_manage_group(client, cv_author, monkeypatch):
    """User in CRUD_VIEWS_MANAGE group can access manage view even when setting is 'no'."""
    from django.contrib.auth.models import User, Group
    from crud_views.lib.settings import crud_views_settings

    monkeypatch.setattr(crud_views_settings, "manage_views_enabled", "no")

    group = Group.objects.create(name="CRUD_VIEWS_MANAGE")
    user = User.objects.create_user(username="manage_user", password="password")
    user.groups.add(group)
    client.force_login(user)

    response = client.get("/author/manage/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_manage_blocked_without_group_or_setting(client, cv_author, monkeypatch):
    """Authenticated user without CRUD_VIEWS_MANAGE group gets 403 when setting is 'no'."""
    from django.contrib.auth.models import User
    from crud_views.lib.settings import crud_views_settings

    monkeypatch.setattr(crud_views_settings, "manage_views_enabled", "no")

    user = User.objects.create_user(username="plain_user", password="password")
    client.force_login(user)

    response = client.get("/author/manage/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_manage_context_has_permission_holders(client_user_author_view, cv_author):
    """Manage view context includes permission_holders list."""
    response = client_user_author_view.get("/author/manage/")
    assert "permission_holders" in response.context
    assert isinstance(response.context["permission_holders"], list)


@pytest.mark.django_db
def test_manage_permission_holders_shows_groups(client_user_author_view, cv_author):
    """Groups with model-level permissions appear in permission_holders."""
    from django.contrib.auth.models import Group, Permission
    from django.contrib.contenttypes.models import ContentType
    from tests.test1.app.models import Author

    ct = ContentType.objects.get_for_model(Author)
    perm = Permission.objects.get(content_type=ct, codename="view_author")
    group = Group.objects.create(name="viewers")
    group.permissions.add(perm)

    response = client_user_author_view.get("/author/manage/")
    holders = response.context["permission_holders"]

    viewer_rows = [r for r in holders if r["group"] == "viewers" and r["permission"] == "view"]
    assert len(viewer_rows) == 1
    assert viewer_rows[0]["has_model_perm"] is True
```

- [ ] **Step 2: Run the 4 tests to verify they fail**

```bash
pytest tests/test1/test_manage.py::test_manage_accessible_via_crud_views_manage_group tests/test1/test_manage.py::test_manage_blocked_without_group_or_setting tests/test1/test_manage.py::test_manage_context_has_permission_holders tests/test1/test_manage.py::test_manage_permission_holders_shows_groups -v
```

Expected: 4 FAIL — `has_permission()` still returns `True` (no group check), `permission_holders` not in context.

- [ ] **Step 3: Implement has_permission() and get_permission_holders() in ManageView**

Replace `crud_views/lib/views/manage.py` with:

```python
from collections import OrderedDict

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views import generic

from crud_views.lib.settings import crud_views_settings
from crud_views.lib.view import CrudView


class ManageView(PermissionRequiredMixin, CrudView, generic.TemplateView):
    template_name = "crud_views/view_manage.html"

    cv_pk: bool = False  # does not need primary key
    cv_key = "manage"
    cv_path = "manage"
    cv_object = False

    cv_context_actions = crud_views_settings.manage_context_actions

    # texts and labels
    cv_header_template: str | None = "crud_views/snippets/header/manage.html"
    cv_paragraph_template: str | None = "crud_views/snippets/paragraph/manage.html"
    cv_action_label_template: str | None = "crud_views/snippets/action/manage.html"
    cv_action_short_label_template: str | None = "crud_views/snippets/action_short/manage.html"

    # icons
    cv_icon_action = "fa-solid fa-gear"
    cv_icon_header = "fa-solid fa-gear"

    def has_permission(self):
        if crud_views_settings.manage_views_enabled == "yes":
            return True
        from django.conf import settings as django_settings
        if crud_views_settings.manage_views_enabled == "debug_only" and django_settings.DEBUG:
            return True
        return self.request.user.groups.filter(
            name=crud_views_settings.manage_group
        ).exists()

    def get_permission_holders(self):
        from django.contrib.auth.models import Group
        rows = []
        for key, perm in self.cv_viewset.permissions.items():
            codename = perm.split(".")[1]
            for group in Group.objects.filter(permissions__codename=codename).order_by("name"):
                rows.append({
                    "group": group.name,
                    "permission": key,
                    "has_model_perm": True,
                    "object_count": None,
                })
        return rows

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        permissions = self.cv_viewset.permissions
        rows = []
        for short, long in permissions.items():
            rows.append(dict(viewset=short, django=long, has_permission=self.request.user.has_perm(long)))
        views = self.get_view_data()
        permission_holders = self.get_permission_holders()
        context.update({
            "cv": self.cv_viewset,
            "data": rows,
            "views": views,
            "permission_holders": permission_holders,
        })
        return context

    def get_view_data(self):
        data = OrderedDict()
        for key, view in self.cv_viewset.get_all_views().items():
            view_data = OrderedDict(
                {
                    "base": OrderedDict(
                        {
                            "class": str(view.__class__),
                            "cv_key": view.cv_key,
                            "cv_path": view.cv_path,
                            "cv_backend_only": view.cv_backend_only,
                            "cv_list_actions": view.cv_list_actions,
                            "cv_list_action_method": view.cv_list_action_method,
                            "cv_context_actions": view.cv_context_actions,
                            "cv_home_key": view.cv_home_key,
                            "cv_success_key": view.cv_success_key,
                            "cv_cancel_key": view.cv_cancel_key,
                            "cv_parent_key": view.cv_parent_key,
                        }
                    ),
                    "templates": OrderedDict(
                        {
                            "cv_header_template": view.cv_header_template,
                            "cv_header_template_code": view.cv_header_template_code,
                            "cv_paragraph_template": view.cv_paragraph_template,
                            "cv_paragraph_template_code": view.cv_paragraph_template_code,
                            "cv_action_label_template": view.cv_action_label_template,
                            "cv_action_label_template_code": view.cv_action_label_template_code,
                            "cv_action_short_label_template": view.cv_action_short_label_template,
                            "cv_action_short_label_template_code": view.cv_action_short_label_template_code,
                        }
                    ),
                    "icons": OrderedDict(
                        {
                            "cv_icon_action": view.cv_icon_action,
                            "cv_icon_header": view.cv_icon_header,
                        }
                    ),
                }
            )
            data[key] = view_data
        return data
```

- [ ] **Step 4: Run the 4 new tests to verify they pass**

```bash
pytest tests/test1/test_manage.py::test_manage_accessible_via_crud_views_manage_group tests/test1/test_manage.py::test_manage_blocked_without_group_or_setting tests/test1/test_manage.py::test_manage_context_has_permission_holders tests/test1/test_manage.py::test_manage_permission_holders_shows_groups -v
```

Expected: 4 PASS.

- [ ] **Step 5: Run the full manage test suite**

```bash
pytest tests/test1/test_manage.py -v
```

Expected: 13 passed (9 existing + 4 new).

- [ ] **Step 6: Commit**

```bash
git add crud_views/lib/views/manage.py tests/test1/test_manage.py
git commit -m "feat: add group-based ManageView access and permission holders"
```

---

### Task 3: Update base template

**Files:**
- Modify: `crud_views/templates/crud_views/view_manage.html`

- [ ] **Step 1: Update view_manage.html**

Replace `crud_views/templates/crud_views/view_manage.html` with:

```html
{% extends cv_extends %}

{% load crud_views %}
{% load django_tables2 %}

{% block cv_content %}

    <h4>Properties</h4>

    <table class="table table-striped">

        <tr>
            <th scope="col">
                Name
            </th>
            <td>
                {{ cv.name }}
            </td>
        </tr>
        <tr>
            <th scope="col">
                Prefix
            </th>
            <td>
                {{ cv.prefix }}
            </td>
        </tr>
        <tr>
            <th scope="col">
                app
            </th>
            <td>
                {{ cv.app }}
            </td>
        </tr>
        <tr>
            <th scope="col">
                pk
            </th>
            <td>
                {{ cv.pk }}
            </td>
        </tr>
        <tr>
            <th scope="col">
                pk_name
            </th>
            <td>
                {{ cv.pk_name }}
            </td>
        </tr>
        <tr>
            <th scope="col">
                parent
            </th>
            <td>
                {{ cv.parent }}
            </td>
        </tr>
    </table>

    {% block guardian_config %}{% endblock guardian_config %}

    <h4>Permissions</h4>

    <table class="table table-striped">
        <tr>
            <th scope="col">Permission</th>
            <th scope="col">Django Permission</th>
            <th scope="col">Access</th>
        </tr>
        {% for row in data %}
            <tr>
                <td>
                    {{ row.viewset }}
                </td>
                <td>
                    {{ row.django }}
                </td>
                <td>
                    {{ row.has_permission }}
                </td>
            </tr>
        {% endfor %}
    </table>

    {% block permission_holders %}
    <h4>Permission Holders</h4>
    {% if permission_holders %}
    <table class="table table-striped">
        <tr>
            <th scope="col">Group</th>
            <th scope="col">Permission</th>
            <th scope="col">Model-level</th>
        </tr>
        {% for row in permission_holders %}
        <tr>
            <td>{{ row.group }}</td>
            <td>{{ row.permission }}</td>
            <td>{% if row.has_model_perm %}✓{% else %}—{% endif %}</td>
        </tr>
        {% endfor %}
    </table>
    {% else %}
    <p>No permission holders found.</p>
    {% endif %}
    {% endblock permission_holders %}

    <br><hr><br>

    <h3>Views</h3>

    <br>

    {% for view_key, view in views.items %}

        <h4>{{ view_key }}</h4>

        <table class="table table-striped">
            {% for section, section_data in view.items %}

                <tr>
                    <th scope="col" colspan="2">{{ section }}</th>
                </tr>

                {% for key, value in section_data.items %}
                    <tr>
                        <td>{{ key }}</td>
                        <td>{{ value }}</td>
                    </tr>
                {% endfor %}
            {% endfor %}
        </table>

        <br>

    {% endfor %}

{% endblock cv_content %}
```

- [ ] **Step 2: Add optional users list to get_permission_holders()**

In `crud_views/lib/views/manage.py`, update `get_permission_holders()` to optionally include users when `manage_show_users` is True:

```python
    def get_permission_holders(self):
        from django.contrib.auth.models import Group
        from django.contrib.auth import get_user_model
        User = get_user_model()
        rows = []
        for key, perm in self.cv_viewset.permissions.items():
            codename = perm.split(".")[1]
            users = []
            if crud_views_settings.manage_show_users:
                users = list(
                    User.objects.filter(user_permissions__codename=codename).values_list("username", flat=True).order_by("username")
                )
            for group in Group.objects.filter(permissions__codename=codename).order_by("name"):
                rows.append({
                    "group": group.name,
                    "permission": key,
                    "has_model_perm": True,
                    "object_count": None,
                    "users": users,
                })
        return rows
```

Also update the base template to show a Users column when `manage_show_users` is True. Replace the `{% block permission_holders %}` section in `view_manage.html` with:

```html
    {% block permission_holders %}
    <h4>Permission Holders</h4>
    {% if permission_holders %}
    <table class="table table-striped">
        <tr>
            <th scope="col">Group</th>
            <th scope="col">Permission</th>
            <th scope="col">Model-level</th>
            {% if crud_views.manage_show_users %}<th scope="col">Users</th>{% endif %}
        </tr>
        {% for row in permission_holders %}
        <tr>
            <td>{{ row.group }}</td>
            <td>{{ row.permission }}</td>
            <td>{% if row.has_model_perm %}✓{% else %}—{% endif %}</td>
            {% if crud_views.manage_show_users %}<td>{{ row.users|join:", " }}</td>{% endif %}
        </tr>
        {% endfor %}
    </table>
    {% else %}
    <p>No permission holders found.</p>
    {% endif %}
    {% endblock permission_holders %}
```

Note: `crud_views` template context variable is the settings box injected by `crud_views_context` context processor. Check how other templates access settings — if they use `crud_views.manage_show_users`, use that. If not available in context, pass `show_users` explicitly from `get_context_data()` instead:

Add to `get_context_data()` in `ManageView`:
```python
context["show_users"] = crud_views_settings.manage_show_users
```

And in template use `{% if show_users %}` instead of `{% if crud_views.manage_show_users %}`.

- [ ] **Step 3: Run the full manage test suite**

```bash
pytest tests/test1/test_manage.py -v
```

Expected: 13 passed.

- [ ] **Step 4: Commit**

```bash
git add crud_views/lib/views/manage.py crud_views/templates/crud_views/view_manage.html
git commit -m "feat: add guardian_config block, permission_holders section, and optional users display"
```

---

### Task 4: GuardianManageView + GuardianViewSet.register() (TDD)

**Files:**
- Modify: `crud_views_guardian/lib/views.py`
- Modify: `crud_views_guardian/lib/viewset.py`
- Test: `tests/test1/test_guardian.py`

- [ ] **Step 1: Write 4 failing guardian manage tests**

Append to `tests/test1/test_guardian.py`:

```python
# ── GuardianManageView ────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_guardian_manage_view_registered(cv_guardian_author):
    """GuardianManageView should be auto-registered on guardian viewsets."""
    from crud_views_guardian.lib.views import GuardianManageView

    assert cv_guardian_author.has_view("manage")
    assert issubclass(cv_guardian_author.get_all_views()["manage"], GuardianManageView)


@pytest.mark.django_db
def test_guardian_manage_context_has_guardian_config(client_guardian, cv_guardian_author):
    """GuardianManageView context includes guardian_config dict."""
    response = client_guardian.get("/guardian_author/manage/")
    assert response.status_code == 200
    assert "guardian_config" in response.context
    config = response.context["guardian_config"]
    assert "cv_guardian_parent_permission" in config
    assert "cv_guardian_parent_create_permission" in config


@pytest.mark.django_db
def test_guardian_manage_permission_holders_has_object_count(client_guardian, cv_guardian_author):
    """Permission holders includes guardian object count after assigning per-object group perm."""
    from django.contrib.auth.models import Group
    from guardian.shortcuts import assign_perm
    from tests.test1.app.models import Author

    group = Group.objects.create(name="editors")
    author = Author.objects.create(first_name="Test", last_name="Author")
    assign_perm("app.change_author", group, author)

    response = client_guardian.get("/guardian_author/manage/")
    holders = response.context["permission_holders"]

    editor_rows = [r for r in holders if r["group"] == "editors" and r["permission"] == "change"]
    assert len(editor_rows) == 1
    assert editor_rows[0]["object_count"] == 1
    assert editor_rows[0]["has_model_perm"] is False


@pytest.mark.django_db
def test_guardian_manage_views_have_mixin_info(client_guardian, cv_guardian_author):
    """Each view in context includes guardian_mixin info derived from MRO."""
    response = client_guardian.get("/guardian_author/manage/")
    views = response.context["views"]
    assert "list" in views
    assert "guardian_mixin" in views["list"]["base"]
    assert "QuerysetMixin" in views["list"]["base"]["guardian_mixin"]
    assert "guardian_mixin" in views["detail"]["base"]
    assert "ObjectPermissionMixin" in views["detail"]["base"]["guardian_mixin"]
```

- [ ] **Step 2: Run the 4 tests to verify they fail**

```bash
pytest tests/test1/test_guardian.py::test_guardian_manage_view_registered tests/test1/test_guardian.py::test_guardian_manage_context_has_guardian_config tests/test1/test_guardian.py::test_guardian_manage_permission_holders_has_object_count tests/test1/test_guardian.py::test_guardian_manage_views_have_mixin_info -v
```

Expected: 4 FAIL — `GuardianManageView` doesn't exist yet, manage view on guardian viewset uses base `ManageView`.

- [ ] **Step 3: Add GuardianManageView to crud_views_guardian/lib/views.py**

Append to `crud_views_guardian/lib/views.py` (after the existing `GuardianCreateViewPermissionRequired` class):

```python
class GuardianManageView(ManageView):
    template_name = "crud_views/view_guardian_manage.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["guardian_config"] = {
            "cv_guardian_parent_permission": self.cv_viewset.cv_guardian_parent_permission,
            "cv_guardian_parent_create_permission": self.cv_viewset.cv_guardian_parent_create_permission,
        }
        return context

    def get_permission_holders(self):
        from django.contrib.contenttypes.models import ContentType
        from guardian.models import GroupObjectPermission
        from django.db.models import Count

        holders = {
            (r["group"], r["permission"]): r
            for r in super().get_permission_holders()
        }

        ct = ContentType.objects.get_for_model(self.cv_viewset.model)
        codename_to_key = {
            perm.split(".")[1]: key
            for key, perm in self.cv_viewset.permissions.items()
        }

        qs = (
            GroupObjectPermission.objects.filter(permission__content_type=ct)
            .values("group__name", "permission__codename")
            .annotate(object_count=Count("object_pk", distinct=True))
        )
        for row in qs:
            group_name = row["group__name"]
            perm_key = codename_to_key.get(row["permission__codename"])
            if perm_key is None:
                continue
            k = (group_name, perm_key)
            if k in holders:
                holders[k]["object_count"] = row["object_count"]
            else:
                holders[k] = {
                    "group": group_name,
                    "permission": perm_key,
                    "has_model_perm": False,
                    "object_count": row["object_count"],
                }

        return sorted(holders.values(), key=lambda r: (r["group"], r["permission"]))

    def get_view_data(self):
        from crud_views_guardian.lib.mixins import (
            GuardianObjectPermissionMixin,
            GuardianQuerysetMixin,
            GuardianParentPermissionMixin,
        )

        GUARDIAN_MIXINS = [
            (GuardianObjectPermissionMixin, "ObjectPermissionMixin"),
            (GuardianQuerysetMixin, "QuerysetMixin"),
            (GuardianParentPermissionMixin, "ParentMixin"),
        ]
        data = super().get_view_data()
        for key, view_data in data.items():
            view_class = self.cv_viewset.get_all_views()[key]
            labels = [label for cls, label in GUARDIAN_MIXINS if issubclass(view_class, cls)]
            view_data["base"]["guardian_mixin"] = " + ".join(labels) if labels else "—"
        return data
```

Also add `ManageView` to the imports at the top of `crud_views_guardian/lib/views.py`. `ManageView` is not in `crud_views.lib.views.__init__` — import it directly:

```python
from crud_views.lib.views import (
    DetailViewPermissionRequired,
    UpdateViewPermissionRequired,
    DeleteViewPermissionRequired,
    CreateViewPermissionRequired,
    ListViewPermissionRequired,
    ActionViewPermissionRequired,
)
from crud_views.lib.views.manage import ManageView
```

- [ ] **Step 4: Override register() in GuardianViewSet**

Replace `crud_views_guardian/lib/viewset.py` with:

```python
from pydantic import model_validator
from typing_extensions import Self

from crud_views.lib.viewset import ViewSet


class GuardianViewSet(ViewSet):
    """
    ViewSet subclass with per-object permission support via django-guardian.

    Attributes:
        cv_guardian_parent_permission: permission key checked on parent object
            for child list/detail/update/delete views. None = skip check.
        cv_guardian_parent_create_permission: permission key checked on parent
            object for child create views. None = falls back to
            cv_guardian_parent_permission.
    """

    cv_guardian_parent_permission: str | None = "view"
    cv_guardian_parent_create_permission: str | None = None

    @model_validator(mode="after")
    def register(self) -> Self:
        result = super().register()
        from crud_views_guardian.lib.views import GuardianManageView

        class AutoManageView(GuardianManageView):
            model = self.model
            cv_viewset = self

        return result

    def assign_perm(self, perm: str, user_or_group, obj) -> None:
        """Assign per-object permission using a short key ("view", "change", etc.)."""
        from guardian.shortcuts import assign_perm

        assign_perm(self.permissions[perm], user_or_group, obj)

    def remove_perm(self, perm: str, user_or_group, obj) -> None:
        """Remove per-object permission using a short key."""
        from guardian.shortcuts import remove_perm

        remove_perm(self.permissions[perm], user_or_group, obj)

    def get_objects_for_user(self, user, perm: str, qs=None):
        """Return queryset of objects for which user has the given per-object permission."""
        from guardian.shortcuts import get_objects_for_user

        return get_objects_for_user(
            user,
            self.permissions[perm],
            qs if qs is not None else self.model.objects.all(),
            accept_global_perms=False,
            use_groups=True,
        )
```

- [ ] **Step 5: Run the 4 new tests to verify they pass**

```bash
pytest tests/test1/test_guardian.py::test_guardian_manage_view_registered tests/test1/test_guardian.py::test_guardian_manage_context_has_guardian_config tests/test1/test_guardian.py::test_guardian_manage_permission_holders_has_object_count tests/test1/test_guardian.py::test_guardian_manage_views_have_mixin_info -v
```

Expected: 4 PASS.

- [ ] **Step 6: Commit**

```bash
git add crud_views_guardian/lib/views.py crud_views_guardian/lib/viewset.py tests/test1/test_guardian.py
git commit -m "feat: add GuardianManageView with guardian config, object counts, and mixin info"
```

---

### Task 5: Guardian template

**Files:**
- Create: `crud_views_guardian/templates/crud_views/view_guardian_manage.html`

- [ ] **Step 1: Create the templates directory**

```bash
mkdir -p crud_views_guardian/templates/crud_views
```

- [ ] **Step 2: Create view_guardian_manage.html**

Create `crud_views_guardian/templates/crud_views/view_guardian_manage.html`:

```html
{% extends "crud_views/view_manage.html" %}

{% block guardian_config %}
<h4>Guardian Configuration</h4>

<table class="table table-striped">
    <tr>
        <th scope="col">Attribute</th>
        <th scope="col">Value</th>
    </tr>
    <tr>
        <td>cv_guardian_parent_permission</td>
        <td>{{ guardian_config.cv_guardian_parent_permission }}</td>
    </tr>
    <tr>
        <td>cv_guardian_parent_create_permission</td>
        <td>{{ guardian_config.cv_guardian_parent_create_permission }}</td>
    </tr>
</table>
{% endblock guardian_config %}

{% block permission_holders %}
<h4>Permission Holders</h4>
{% if permission_holders %}
<table class="table table-striped">
    <tr>
        <th scope="col">Group</th>
        <th scope="col">Permission</th>
        <th scope="col">Model-level</th>
        <th scope="col">Objects (guardian)</th>
    </tr>
    {% for row in permission_holders %}
    <tr>
        <td>{{ row.group }}</td>
        <td>{{ row.permission }}</td>
        <td>{% if row.has_model_perm %}✓{% else %}—{% endif %}</td>
        <td>{% if row.object_count is not None %}{{ row.object_count }} objects{% else %}—{% endif %}</td>
    </tr>
    {% endfor %}
</table>
{% else %}
<p>No permission holders found.</p>
{% endif %}
{% endblock permission_holders %}
```

- [ ] **Step 3: Run the full test suite**

```bash
pytest tests/test1/ -v
```

Expected: 203 passed, 1 skipped (195 existing + 4 manage + 4 guardian).

- [ ] **Step 4: Commit**

```bash
git add crud_views_guardian/templates/
git commit -m "feat: add guardian manage template with guardian config and objects column"
```

---

### Task 6: Docs + skill + symlink

**Files:**
- Modify: `docs/reference/settings.md`
- Modify: `docs/reference/guardian.md`
- Modify: `skills/django-crud-views/SKILL.md`

- [ ] **Step 1: Update docs/reference/settings.md**

Add two rows to the settings table after the `MANAGE_VIEWS_ENABLED` row:

```markdown
| CRUD_VIEWS_MANAGE_GROUP | Django group name that grants manage view access regardless of MANAGE_VIEWS_ENABLED | `str` | `CRUD_VIEWS_MANAGE` |
| CRUD_VIEWS_MANAGE_SHOW_USERS | Whether to show a Users column in the Permission Holders section of ManageView | `bool` | `False` |
```

- [ ] **Step 2: Update docs/reference/guardian.md**

Add a new section at the end of `docs/reference/guardian.md`:

```markdown
## GuardianManageView

When `CRUD_VIEWS_MANAGE_VIEWS_ENABLED` is enabled (or a user is in the `CRUD_VIEWS_MANAGE` group), guardian-enabled viewsets show an enhanced manage page at `/<prefix>/manage/`.

In addition to the standard ManageView content, GuardianManageView adds:

**Guardian Configuration** — a table showing:
- `cv_guardian_parent_permission` — permission key checked on parent object for child views
- `cv_guardian_parent_create_permission` — permission key for child create views (falls back to `cv_guardian_parent_permission` if None)

**Permission Holders** — extends the standard group listing with an "Objects (guardian)" column showing how many objects each group has per-object access to.

**Views table** — each registered view shows a "guardian_mixin" column listing which guardian mixins are active (`ObjectPermissionMixin`, `QuerysetMixin`, `ParentMixin`).

GuardianManageView is wired automatically by `GuardianViewSet.register()` — no manual configuration required.
```

- [ ] **Step 3: Update skills/django-crud-views/SKILL.md**

In `skills/django-crud-views/SKILL.md`, find the ManageView section and update it to mention group-based access:

Find the line(s) describing ManageView access control and add:

```
Access is controlled by CRUD_VIEWS_MANAGE_VIEWS_ENABLED ("yes"/"debug_only"/"no") OR by adding users to the CRUD_VIEWS_MANAGE Django group (configurable via CRUD_VIEWS_MANAGE_GROUP setting). The group approach lets you grant selective access without changing deployment settings.
```

In the guardian section, add a GuardianManageView entry:

```
GuardianManageView: auto-wired by GuardianViewSet.register(). Extends ManageView with a Guardian Configuration section, per-object permission holder counts (Group → Permission → N objects), and a Guardian Mixin column in the Views table. No manual configuration required — just enable manage views or add users to CRUD_VIEWS_MANAGE group.
```

- [ ] **Step 4: Replace ~/.claude/skills/django-crud-views with a symlink**

```bash
rm -rf ~/.claude/skills/django-crud-views
ln -s /home/alex/projects/alex/django-crud-views/skills/django-crud-views ~/.claude/skills/django-crud-views
```

Verify:

```bash
ls -la ~/.claude/skills/django-crud-views
```

Expected: `lrwxrwxrwx ... django-crud-views -> /home/alex/projects/alex/django-crud-views/skills/django-crud-views`

- [ ] **Step 5: Commit**

```bash
git add docs/reference/settings.md docs/reference/guardian.md skills/django-crud-views/SKILL.md
git commit -m "docs: document GuardianManageView, new settings, and update django-crud-views skill"
```
