"""Resource manage pages reuse the developer gate without reading Resource items."""

import re
from collections import Counter
from unittest.mock import Mock

import pytest
from django.contrib.auth.models import AnonymousUser, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import resolve, reverse
from guardian.shortcuts import clear_ct_cache
from lxml import html

from crud_views.lib.resource import Resource
from crud_views.lib.settings import crud_views_settings
from crud_views.lib.views import ListView, ListViewPermissionRequired
from crud_views.lib.views.manage import ManageView
from crud_views.lib.viewset import ViewSet
from tests.test1.test_ancestor_authorization import isolated_routes

pytestmark = pytest.mark.django_db


class ManageItem(Resource):
    key: str

    class Meta:
        pk_field = "key"
        verbose_name = "managed item"
        verbose_name_plural = "managed items"

    @classmethod
    def cv_get_items(cls, request, **kwargs):
        raise AssertionError("Manage must not list Resource items")

    @classmethod
    def cv_get_item(cls, request, pk, **kwargs):
        raise AssertionError("Manage must not load a Resource item")


def make_developer(django_user_model, username):
    actor = django_user_model.objects.create_user(username=username)
    actor.groups.add(Group.objects.get_or_create(name=crud_views_settings.manage_group)[0])
    return actor


@pytest.mark.parametrize("fixture", ["cv_author", "cv_guardian_author"])
def test_resource_manage_model_query_preservation(request, fixture, client, django_user_model, monkeypatch):
    vs = request.getfixturevalue(fixture)
    actor = make_developer(django_user_model, "baseline developer")
    # Login/setup are outside measurement; the actual request resolves a fresh actor.
    client.force_login(actor)
    # Shared ViewSet fixtures retain vocabulary caches across tests. Reproduce the
    # original cold baseline independently of worker scheduling, then restore it.
    ContentType.objects.clear_cache()
    clear_ct_cache()
    previous_permissions = vs._default_permissions
    with monkeypatch.context() as cache_patch:
        cache_patch.setattr(vs, "_default_permissions", None)
        with CaptureQueriesContext(connection) as queries:
            response = client.get(reverse(vs.get_router_name("manage")))
    assert response.status_code == 200
    counts = Counter(table for query in queries for table in set(re.findall(r'(?:FROM|JOIN) "([^"]+)"', query["sql"])))
    expected = {
        "auth_group": 3,
        "auth_group_permissions": 2,
        "auth_permission": 4,
        "auth_user": 2,
        "auth_user_groups": 2,
        "auth_user_user_permissions": 1,
        "django_content_type": 5,
        "django_session": 1,
    }
    if fixture == "cv_guardian_author":
        expected.update(
            app_author=5,
            auth_group=9,
            auth_permission=15,
            auth_user_groups=8,
            django_content_type=11,
            guardian_groupobjectpermission=6,
            guardian_userobjectpermission=5,
        )
    assert len(queries) == (21 if fixture == "cv_guardian_author" else 9)
    assert counts == expected
    assert getattr(vs, "_default_permissions", object()) is previous_permissions, "Restore shared vocabulary cache"


def test_resource_manage_tracer(client, django_user_model):
    def build(sfx):
        vs = ViewSet(model=ManageItem, name="managed" + sfx, resource_permissions={"view": "app.view_author"})
        assert vs.has_view("manage"), "Resource ViewSets must automatically register manage"
        return vs, [vs]

    with isolated_routes(build) as vs:
        assert vs.has_view("manage"), "Resource ViewSets must automatically register manage"
        url = reverse(vs.get_router_name("manage"))
        actor = make_developer(django_user_model, "developer without grants")
        client.force_login(actor)
        response = client.get(url)
        assert response.status_code == 200
        assert response.context["manage_permissions"]["actor"]["cells"] == [
            {"key": "view", "model": False, "object_count": None}
        ]
        doc = html.fromstring(response.content)
        assert doc.cssselect("#cv-manage-permissions, #cv-manage-views, #cv-manage-urls")
        assert "Resource" in doc.get_element_by_id("cv-manage-viewset").text_content()
        assert "tests.test1.test_resource_manage.ManageItem" in response.content.decode()
        assert response.context["manage_checks"] is not None

        granted = make_developer(django_user_model, "developer with grant")
        granted.user_permissions.add(Permission.objects.get(content_type__app_label="app", codename="view_author"))
        client.force_login(django_user_model.objects.get(pk=granted.pk))
        response = client.get(url)
        assert response.status_code == 200
        badge = html.fromstring(response.content).cssselect("[data-manage-actor] [data-permission=view] span")[0]
        assert badge.text == "resource"
        assert badge.get("class") == "badge bg-info text-dark"
        assert not ContentType.objects.filter(model="manageitem").exists()


class SettingsManageView(ManageView):
    pass


class OverrideManageView(ManageView):
    pass


@pytest.mark.parametrize("selection", ["default", "settings", "viewset"])
@pytest.mark.parametrize("mapping", [None, {}])
@pytest.mark.parametrize("actions", [[], ["manage"]])
def test_resource_manage_registration(monkeypatch, selection, mapping, actions):
    module = __name__
    monkeypatch.setattr(
        crud_views_settings, "manage_view_class", f"{module}.SettingsManageView" if selection != "default" else None
    )
    shared = list(actions)

    def build(sfx):
        vs = ViewSet(
            model=ManageItem,
            name="registration" + sfx,
            resource_permissions=mapping,
            manage_view_class=f"{module}.OverrideManageView" if selection == "viewset" else None,
        )
        type("ResourceList", (ListView,), {"cv_viewset": vs, "cv_context_actions": shared})
        return vs, [vs]

    with isolated_routes(build) as vs:
        expected = {"default": ManageView, "settings": SettingsManageView, "viewset": OverrideManageView}[selection]
        assert issubclass(vs.get_view_class("manage"), expected)
        assert vs.get_view_class("manage").cv_pk is False
        assert "manage" not in (vs.get_view_class("manage").cv_context_actions or [])
        assert vs.get_view_class("list").cv_context_actions.count("manage") == 1
        assert shared == actions
        assert "viewset.E260" not in [message.id for check in vs.checks() for message in check.messages()]
        type("UnmappedEndpoint", (ListViewPermissionRequired,), {"cv_viewset": vs, "cv_key": "unmapped"})
        assert "viewset.E260" in [message.id for check in vs.checks() for message in check.messages()]


@pytest.mark.parametrize(
    "mode,debug",
    [("yes", False), ("yes", True), ("no", False), ("no", True), ("debug_only", False), ("debug_only", True)],
)
@pytest.mark.parametrize(
    "identity",
    ["anonymous", "inactive-member", "member", "grant-only", "staff", "superuser", "member-staff", "member-superuser"],
)
@pytest.mark.parametrize("inaccessible", ["hide", "disable"])
def test_resource_manage_admission(
    client, rf, django_user_model, monkeypatch, settings, mode, debug, identity, inaccessible
):
    settings.DEBUG = debug
    monkeypatch.setattr(crud_views_settings, "manage_views_enabled", mode)
    loaders = [Mock(side_effect=AssertionError("Unexpected Resource read")) for _ in range(2)]
    monkeypatch.setattr(ManageItem, "cv_get_items", loaders[0])
    monkeypatch.setattr(ManageItem, "cv_get_item", loaders[1])

    def build(sfx):
        vs = ViewSet(
            model=ManageItem,
            name="admission" + sfx,
            resource_permissions={"view": "app.view_author"},
            inaccessible_actions=inaccessible,
        )
        type(
            "ResourceList",
            (ListView,),
            {
                "cv_viewset": vs,
                "cv_context_actions": [],
                "cv_inaccessible_actions": inaccessible,
            },
        )
        return vs, [vs]

    with isolated_routes(build) as vs:
        actor = AnonymousUser()
        if identity != "anonymous":
            actor = django_user_model.objects.create_user(
                username=identity,
                is_active=identity != "inactive-member",
                is_staff="staff" in identity,
                is_superuser="superuser" in identity,
            )
            if "member" in identity:
                actor.groups.add(Group.objects.get_or_create(name=crud_views_settings.manage_group)[0])
            if identity == "grant-only":
                actor.user_permissions.add(
                    Permission.objects.get(content_type__app_label="app", codename="view_author")
                )
            client.force_login(actor)
        allowed = "member" in identity and actor.is_active and (mode == "yes" or (mode == "debug_only" and debug))
        manage = vs.get_view_class("manage")
        assert manage.cv_has_access(actor) is allowed
        diagnostics = Mock(side_effect=AssertionError("Denied request reached holder diagnostics"))
        if not allowed:
            monkeypatch.setattr(manage, "get_manage_permissions", diagnostics)
        response = client.get(reverse(vs.get_router_name("manage")))
        assert response.status_code == (
            200 if allowed else 302 if identity in {"anonymous", "inactive-member"} else 403
        )
        if not allowed:
            diagnostics.assert_not_called()
        for loader in loaders:
            loader.assert_not_called()
        view = vs.get_view_class("list")()
        request = rf.get(reverse(vs.get_router_name("list")))
        request.resolver_match = resolve(request.path)
        request.user = actor
        view.setup(request)
        buttons = view.cv_get_context_buttons()
        assert ("manage" in view.cv_context_actions) is (mode != "no")
        # ManageView deliberately hides denied diagnostics even under a disable policy.
        assert manage.cv_get_inaccessible_actions() == "hide"
        if mode == "no" or not allowed:
            assert buttons == []
        else:
            assert len(buttons) == 1
            assert bool(buttons[0].get("cv_disabled")) is (not allowed)
