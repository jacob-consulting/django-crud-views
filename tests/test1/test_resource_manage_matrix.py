"""Explicit Resource permissions retain effective actor and direct-holder semantics."""

import pytest
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import override_settings
from django.urls import reverse
from guardian.shortcuts import assign_perm
from lxml import html

from crud_views.lib.settings import crud_views_settings
from crud_views.lib.viewset import ViewSet
from tests.test1.app.models import Author
from tests.test1.test_ancestor_authorization import isolated_routes
from tests.test1.test_resource_manage import ManageItem, make_developer

pytestmark = pytest.mark.django_db

RESOURCE_LEGEND = (
    "resource: explicitly mapped Django permission; no per-item grants. The access row includes effective permissions."
)
MODEL_LEGEND = (
    "model: model-level permission · objects: object grants; "
    "the access row includes effective permissions and reachable objects"
)
EMPTY_COPY = "No permissions configured. Review this ViewSet's permission configuration."


@pytest.mark.parametrize("mapping", [None, {}])
def test_resource_manage_matrix_empty(client, django_user_model, mapping):
    def build(sfx):
        vs = ViewSet(model=ManageItem, name="empty_matrix" + sfx, resource_permissions=mapping)
        return vs, [vs]

    with isolated_routes(build) as vs:
        client.force_login(make_developer(django_user_model, "empty map developer"))
        response = client.get(reverse(vs.get_router_name("manage")))
        assert response.status_code == 200
        matrix = response.context["manage_permissions"]
        assert matrix["columns"] == matrix["actor"]["cells"] == matrix["groups"] == []
        card = html.fromstring(response.content).get_element_by_id("cv-manage-permissions")
        assert "No Resource permissions declared" in card.text_content()
        assert (
            "Developer-group access, ancestor checks and custom view restrictions apply separately."
            in card.text_content()
        )
        assert RESOURCE_LEGEND in card.text_content()
        assert EMPTY_COPY not in card.text_content() and MODEL_LEGEND not in card.text_content()
        assert not card.cssselect("table, [data-permission]")


@pytest.mark.parametrize("actor_grant", ["none", "direct", "group", "superuser"])
@pytest.mark.parametrize("classes", [None, "project-resource", ""])
def test_resource_manage_matrix(client, django_user_model, monkeypatch, actor_grant, classes):
    monkeypatch.setattr(crud_views_settings, "manage_show_users", True)
    actor = make_developer(django_user_model, "<script>actor</script>")
    view = Permission.objects.get(content_type__app_label="app", codename="view_author")
    group = Group.objects.create(name="<script>group</script>")
    group.permissions.add(view)
    holders = []
    for index in range(21):
        holder = django_user_model.objects.create_user(username=f"holder {index:02} <script>label</script>")
        holder.user_permissions.add(view)
        holders.append(holder)
    root = django_user_model.objects.create_user(username="secret root", is_superuser=True)
    django_user_model.objects.create_user(username="inactive root", is_superuser=True, is_active=False)
    inherited = django_user_model.objects.create_user(username="group-only user")
    inherited.groups.add(group)
    if actor_grant == "direct":
        actor.user_permissions.add(view)
    elif actor_grant == "group":
        actor.groups.add(group)
    elif actor_grant == "superuser":
        actor.is_superuser = True
        actor.save(update_fields=["is_superuser"])

    def build(sfx):
        vs = ViewSet(
            model=ManageItem,
            name="matrix_resource" + sfx,
            resource_permissions={"inspect": "app.view_author", "edit": "app.change_author"},
        )
        return vs, [vs]

    overrides = {} if classes is None else {"manage:badge-resource": classes}
    with isolated_routes(build) as vs, override_settings(CRUD_VIEWS_BUTTON_CLASSES=overrides):
        client.force_login(actor)
        response = client.get(reverse(vs.get_router_name("manage")))
        assert response.status_code == 200
        matrix = response.context["manage_permissions"]
        assert matrix["columns"] == [
            {"key": "inspect", "permission": "app.view_author", "codename": "view_author"},
            {"key": "edit", "permission": "app.change_author", "codename": "change_author"},
        ]
        assert matrix["actor"]["cells"] == [
            {"key": "inspect", "model": actor_grant != "none", "object_count": None},
            {"key": "edit", "model": actor_grant == "superuser", "object_count": None},
        ]
        direct = [*matrix["users"], *matrix["users_overflow"]]
        assert {row["id"] for row in direct} == {holder.pk for holder in holders} | (
            {actor.pk} if actor_grant == "direct" else set()
        )
        assert len(matrix["users"]) == 20 and len(matrix["users_overflow"]) == (2 if actor_grant == "direct" else 1)
        for row in [*matrix["groups"], *direct]:
            assert row["cells"] == [
                {"key": "inspect", "model": True, "object_count": None},
                {"key": "edit", "model": False, "object_count": None},
            ]
        doc = html.fromstring(response.content)
        card = doc.get_element_by_id("cv-manage-permissions")
        assert RESOURCE_LEGEND in card.text_content() and MODEL_LEGEND not in card.text_content()
        expected_class = "badge bg-info text-dark" if classes is None else classes
        selectors = ["[data-manage-groups]", "[data-manage-users]", "[data-manage-users-overflow]"]
        if actor_grant != "none":
            selectors.append("[data-manage-actor]")
        for selector in selectors:
            badges = card.cssselect(selector + " [data-permission=inspect] span")
            assert badges and all(badge.text == "resource" and badge.get("class") == expected_class for badge in badges)
        for cell in card.cssselect(
            "[data-manage-groups] [data-permission=edit], [data-manage-users] [data-permission=edit]"
        ):
            assert "No permission or object grant" in cell.text_content() and "resource" not in cell.text_content()
        assert not card.cssselect("script")
        assert actor.username in card.text_content() and holders[0].username in card.text_content()
        assert "group-only user" not in card.text_content() and "inactive root" not in card.text_content()
        assert matrix["superusers"]["count"] == (2 if actor_grant == "superuser" else 1)
        assert root.username in card.text_content()
        assert not ContentType.objects.filter(model="manageitem").exists()

        monkeypatch.setattr(crud_views_settings, "manage_show_users", False)
        response = client.get(reverse(vs.get_router_name("manage")))
        matrix = response.context["manage_permissions"]
        assert matrix["users"] == matrix["users_overflow"] == matrix["superusers"]["names"] == []
        card = html.fromstring(response.content).get_element_by_id("cv-manage-permissions")
        assert not card.cssselect("[data-manage-users], [data-manage-users-overflow]")
        assert "holder 00" not in card.text_content() and root.username not in card.text_content()
        assert actor.username in card.text_content()


@pytest.mark.parametrize("fixture", ["cv_author", "cv_guardian_author"])
def test_resource_manage_matrix_preserves_model_labels(request, fixture, client, django_user_model, monkeypatch):
    vs = request.getfixturevalue(fixture)
    actor = make_developer(django_user_model, "model matrix developer")
    actor.user_permissions.add(Permission.objects.get(content_type__app_label="app", codename="view_author"))
    if fixture == "cv_guardian_author":
        author = Author.objects.create(first_name="Object", last_name="grant")
        assign_perm("app.view_author", actor, author)
    client.force_login(actor)
    response = client.get(reverse(vs.get_router_name("manage")))
    assert response.status_code == 200
    card = html.fromstring(response.content).get_element_by_id("cv-manage-permissions")
    assert MODEL_LEGEND in card.text_content() and RESOURCE_LEGEND not in card.text_content()
    badges = card.cssselect("[data-manage-actor] [data-permission=view] span")
    assert badges[0].text == "model"
    if fixture == "cv_guardian_author":
        assert badges[1].text.strip() == "1 object"
    monkeypatch.setattr(ViewSet, "permissions", property(lambda self: {}))
    response = client.get(reverse(vs.get_router_name("manage")))
    assert EMPTY_COPY in response.content.decode()
