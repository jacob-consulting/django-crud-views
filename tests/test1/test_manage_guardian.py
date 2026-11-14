"""Guardian matrices distinguish direct assignments from reachable actor objects."""

import pytest
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from guardian.models import UserObjectPermission
from guardian.shortcuts import assign_perm
from lxml import html

from crud_views.lib.settings import crud_views_settings
from crud_views_guardian.lib.views import GuardianManageView
from crud_views_guardian.lib.viewset import GuardianViewSet
from tests.test1.app.models import Publisher, Shelf
from tests.test1.test_ancestor_authorization import isolated_routes

pytestmark = pytest.mark.django_db


@pytest.fixture(params=[Publisher, Shelf], ids=["generic", "direct"])
def matrix_setup(request, django_user_model, monkeypatch):
    def build(sfx):
        vs = GuardianViewSet(model=request.param, name="matrix" + sfx)
        return vs, [vs]

    monkeypatch.setattr(crud_views_settings, "manage_show_users", True)
    with isolated_routes(build) as vs:
        actor = django_user_model.objects.create_user(username="matrix actor")
        actor.groups.add(Group.objects.get_or_create(name=crud_views_settings.manage_group)[0])
        first = request.param.objects.create(name="first")
        second = request.param.objects.create(name="second")
        yield vs, actor, first, second


def cell(row, key="view"):
    return next(c for c in row["cells"] if c["key"] == key)


def model_grant(holder, vs, key="view"):
    app, codename = vs.permissions[key].split(".")
    perm = Permission.objects.get(content_type__app_label=app, codename=codename)
    (holder.permissions if isinstance(holder, Group) else holder.user_permissions).add(perm)


def test_direct_holder_union_uses_pk_and_actor_deduplicates(matrix_setup, django_user_model):
    vs, actor, first, second = matrix_setup
    group = Group.objects.create(name="same label")
    direct_user = django_user_model.objects.create_user(username="same label")
    other = django_user_model.objects.create_user(username="second holder")
    actor.groups.add(group)
    for holder in (group, direct_user):
        model_grant(holder, vs)
        assign_perm(vs.permissions["view"], holder, first)
        assign_perm(vs.permissions["change"], holder, second)
    assign_perm(vs.permissions["view"], actor, first)
    assign_perm(vs.permissions["view"], other, second)
    manage = GuardianManageView()
    data = manage.get_manage_permissions(vs, actor)
    groups = {r["id"]: r for r in data["groups"]}
    users = {r["id"]: r for r in data["users"]}
    assert cell(data["actor"]) == {"key": "view", "model": True, "object_count": 1}
    assert len(groups) == 1 and groups[group.pk]["member_count"] == 1
    assert set(users) == {actor.pk, direct_user.pk, other.pk}
    for row in (groups[group.pk], users[direct_user.pk]):
        assert cell(row) == {"key": "view", "model": True, "object_count": 1}
        assert cell(row, "change") == {"key": "change", "model": False, "object_count": 1}
    assert cell(users[actor.pk])["model"] is False  # group rights are effective only in the actor row
    assert groups[group.pk]["label"] == users[direct_user.pk]["label"]
    group.name = "renamed group"
    group.save()
    direct_user.username = "renamed user"
    direct_user.save()
    renamed = manage.get_manage_permissions(vs, actor)
    for collection, holder in (("groups", group), ("users", direct_user)):
        row = next(r for r in renamed[collection] if r["id"] == holder.pk)
        old = groups[holder.pk] if collection == "groups" else users[holder.pk]
        assert row["cells"] == old["cells"] and row["label"].startswith("renamed")


def test_actor_uses_strict_helper_once_per_permission(matrix_setup, monkeypatch):
    vs, actor, _first, _second = matrix_setup
    model_grant(actor, vs)
    original = GuardianViewSet.get_objects_for_user
    calls = []

    def count(self, user, key, qs=None):
        calls.append((self, user, key))
        return original(self, user, key, qs=qs)

    monkeypatch.setattr(GuardianViewSet, "get_objects_for_user", count)
    row = GuardianManageView().get_manage_actor_row(vs, actor)
    assert calls == [(vs, actor, key) for key in vs.permissions]
    assert cell(row) == {"key": "view", "model": True, "object_count": 0}
    actor.is_superuser = True
    actor.save()
    row = GuardianManageView().get_manage_actor_row(vs, actor)
    assert all(c["object_count"] == 2 and c["model"] for c in row["cells"])
    actor.is_active = False
    actor.save()
    row = GuardianManageView().get_manage_actor_row(vs, actor)
    assert all(c["object_count"] == 0 and not c["model"] for c in row["cells"])


def test_generic_orphan_counts_are_assignments_not_reachable(cv_guardian_publisher, django_user_model, monkeypatch):
    monkeypatch.setattr(crud_views_settings, "manage_show_users", True)
    actor = django_user_model.objects.create_user(username="orphan actor")
    obj = Publisher.objects.create(name="dangling")
    assign_perm("app.view_publisher", actor, obj)
    obj.delete()
    assert UserObjectPermission.objects.filter(user=actor).count() == 1
    data = GuardianManageView().get_manage_permissions(cv_guardian_publisher, actor)
    assert cell(data["actor"])["object_count"] == 0
    assert cell(next(r for r in data["users"] if r["id"] == actor.pk))["object_count"] == 1


def test_builders_are_request_free_and_hidden_names_are_not_queried(matrix_setup, django_user_model, monkeypatch):
    vs, actor, first, second = matrix_setup
    hidden = django_user_model.objects.create_user(username="hidden object user")
    django_user_model.objects.create_user(username="hidden superuser", is_superuser=True)
    assign_perm(vs.permissions["view"], hidden, first)
    assign_perm(vs.permissions["view"], actor, second)
    monkeypatch.setattr(crud_views_settings, "manage_show_users", False)

    def forbidden(self):
        raise AssertionError("Builder read self.request")

    monkeypatch.setattr(GuardianManageView, "request", property(forbidden), raising=False)
    manage = GuardianManageView()
    with CaptureQueriesContext(connection) as queries:
        data = manage.get_manage_permissions(vs, actor)
        manage.get_manage_views(vs, actor)
        manage.get_manage_guardian(vs, actor)
    assert data["users"] == data["users_overflow"] == data["superusers"]["names"] == []
    assert cell(data["actor"])["object_count"] == 1
    assert data["superusers"]["count"] == 1
    selects = [q["sql"].split(" FROM ", 1)[0] for q in queries]
    assert not any('"auth_user"."username"' in q for q in selects)


def test_holder_queries_do_not_grow_with_holder_count(matrix_setup, django_user_model):
    vs, actor, first, _second = matrix_setup
    manage = GuardianManageView()
    # Warm identity/permission/backend caches for both measurements.
    manage.get_manage_permissions(vs, actor)
    with CaptureQueriesContext(connection) as before:
        manage.get_manage_permissions(vs, actor)
    for index in range(12):
        group = Group.objects.create(name=f"extra group {index}")
        user = django_user_model.objects.create_user(username=f"extra user {index}")
        for holder in (group, user):
            model_grant(holder, vs)
            assign_perm(vs.permissions["view"], holder, first)
    with CaptureQueriesContext(connection) as after:
        data = manage.get_manage_permissions(vs, actor)
    assert len(data["groups"]) == len(data["users"]) == 12
    assert len(after) <= len(before) + 1  # core member-count query is absent when no groups exist
    assert len(after) <= 35


def test_object_users_fold_after_twenty(matrix_setup, django_user_model):
    vs, actor, first, _second = matrix_setup
    for index in range(21):
        user = django_user_model.objects.create_user(username=f"object holder {index:02}")
        assign_perm(vs.permissions["view"], user, first)
    data = GuardianManageView().get_manage_permissions(vs, actor)
    assert len(data["users"]) == 20 and len(data["users_overflow"]) == 1
    assert data["users_overflow"][0]["label"] == "object holder 20"


def test_exact_permission_identity_excludes_same_codename(cv_guardian_publisher, django_user_model, monkeypatch):
    monkeypatch.setattr(crud_views_settings, "manage_show_users", True)
    actor = django_user_model.objects.create_user(username="identity actor")
    obj = Publisher.objects.create(name="identity")
    wrong_ct = ContentType.objects.create(app_label="other_app", model="publisher")
    wrong_permission = Permission.objects.create(content_type=wrong_ct, codename="view_publisher", name="Other view")
    # bulk_create intentionally creates foreign-namespace grant records without Guardian's save validation.
    UserObjectPermission.objects.bulk_create(
        [UserObjectPermission(user=actor, permission=wrong_permission, content_type=wrong_ct, object_pk=str(obj.pk))]
    )
    data = GuardianManageView().get_manage_permissions(cv_guardian_publisher, actor)
    assert data["users"] == [] and cell(data["actor"])["object_count"] == 0


def test_hidden_user_names_never_reach_html(matrix_setup, django_user_model, monkeypatch, client):
    vs, actor, first, _second = matrix_setup
    hidden = django_user_model.objects.create_user(username="secret direct account")
    django_user_model.objects.create_user(username="secret super account", is_superuser=True)
    assign_perm(vs.permissions["view"], hidden, first)
    monkeypatch.setattr(crud_views_settings, "manage_show_users", False)
    client.force_login(actor)
    response = client.get(reverse(vs.get_router_name("manage")))
    assert response.status_code == 200
    assert b"secret direct account" not in response.content and b"secret super account" not in response.content
    assert not html.fromstring(response.content).xpath("//*[@data-manage-users]")
