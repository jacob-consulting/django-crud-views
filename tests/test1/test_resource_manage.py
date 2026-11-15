"""Resource manage pages reuse the developer gate without reading Resource items."""

import re
from collections import Counter

import pytest
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from lxml import html

from crud_views.lib.resource import Resource
from crud_views.lib.settings import crud_views_settings
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
def test_resource_manage_model_query_preservation(request, fixture, client, django_user_model):
    vs = request.getfixturevalue(fixture)
    actor = make_developer(django_user_model, "baseline developer")
    # Login/setup are outside measurement; the actual request resolves a fresh actor.
    client.force_login(actor)
    ContentType.objects.clear_cache()
    with CaptureQueriesContext(connection) as queries:
        response = client.get(reverse(vs.get_router_name("manage")))
    assert response.status_code == 200
    counts = Counter(
        table for query in queries for table in set(re.findall(r'(?:FROM|JOIN) "([^"]+)"', query["sql"]))
    )
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
            {"key": "view", "model": False, "object_count": 0}
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
