from io import StringIO

import pytest
from django.contrib.auth.models import Group, Permission
from django.core.management import call_command, get_commands

from crud_views.lib.settings import crud_views_settings


pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("group_name", ["CRUD_VIEWS_MANAGE", "Project developers"])
@pytest.mark.parametrize("mode", ["yes", "no", "debug_only"])
@pytest.mark.parametrize("debug", [False, True])
def test_manage_group_creates_only_configured_group(settings, monkeypatch, django_user_model, group_name, mode, debug):
    settings.DEBUG = debug
    monkeypatch.setattr(crud_views_settings, "manage_group", group_name)
    monkeypatch.setattr(crud_views_settings, "manage_views_enabled", mode)
    other_group = Group.objects.create(name="Existing application group")
    user = django_user_model.objects.create_user(username="existing-user")
    permission = Permission.objects.get(content_type__app_label="auth", codename="view_group")
    other_group.user_set.add(user)
    other_group.permissions.add(permission)
    user.user_permissions.add(permission)
    users_before = list(django_user_model.objects.order_by("pk").values())
    memberships_before = list(user.groups.order_by("pk").values_list("pk", flat=True))
    permissions_before = list(user.user_permissions.order_by("pk").values_list("pk", flat=True))

    assert "cv_manage_group" in get_commands(), "The group setup command must be discoverable"
    for expected_status in ["Created", "Already present"]:
        output = StringIO()
        call_command("cv_manage_group", stdout=output)

        assert group_name in output.getvalue()
        assert expected_status in output.getvalue()
        group = Group.objects.get(name=group_name)
        assert not group.user_set.exists()
        assert not group.permissions.exists()
        assert set(Group.objects.values_list("name", flat=True)) == {other_group.name, group_name}
        assert list(django_user_model.objects.order_by("pk").values()) == users_before
        assert list(user.groups.order_by("pk").values_list("pk", flat=True)) == memberships_before
        assert list(user.user_permissions.order_by("pk").values_list("pk", flat=True)) == permissions_before
        assert list(other_group.permissions.values_list("pk", flat=True)) == [permission.pk]


@pytest.mark.parametrize("group_name", ["CRUD_VIEWS_MANAGE", "Project developers"])
def test_manage_group_preserves_populated_group(settings, monkeypatch, django_user_model, group_name):
    settings.DEBUG = False
    monkeypatch.setattr(crud_views_settings, "manage_group", group_name)
    group = Group.objects.create(name=group_name)
    other_group = Group.objects.create(name="Existing application group")
    user = django_user_model.objects.create_user(username="existing-developer")
    permissions = Permission.objects.filter(content_type__app_label="auth", codename__in=["view_group", "change_group"])
    group.user_set.add(user)
    group.permissions.add(*permissions)
    other_group.user_set.add(user)
    other_group.permissions.add(*permissions)
    user.user_permissions.add(*permissions)
    users_before = list(django_user_model.objects.order_by("pk").values())
    groups_before = list(Group.objects.order_by("pk").values())
    members_before = list(group.user_set.order_by("pk").values_list("pk", flat=True))
    grants_before = list(group.permissions.order_by("pk").values_list("pk", flat=True))
    user_grants_before = list(user.user_permissions.order_by("pk").values_list("pk", flat=True))

    assert "cv_manage_group" in get_commands(), "The group setup command must be discoverable"
    for _ in range(2):
        output = StringIO()
        call_command("cv_manage_group", stdout=output)

        assert group_name in output.getvalue()
        assert "Already present" in output.getvalue()
        assert list(django_user_model.objects.order_by("pk").values()) == users_before
        assert list(Group.objects.order_by("pk").values()) == groups_before
        assert list(group.user_set.order_by("pk").values_list("pk", flat=True)) == members_before
        assert list(group.permissions.order_by("pk").values_list("pk", flat=True)) == grants_before
        assert list(other_group.user_set.order_by("pk").values_list("pk", flat=True)) == members_before
        assert list(other_group.permissions.order_by("pk").values_list("pk", flat=True)) == grants_before
        assert list(user.user_permissions.order_by("pk").values_list("pk", flat=True)) == user_grants_before
