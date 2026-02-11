import pytest
from django.test.client import Client

from crud_views.lib.viewset import ViewSet
from tests.lib.helper.boostrap5 import Table
from tests.test1.app.models import Publisher


@pytest.mark.django_db
def test_viewset_has_views(cv_publisher: ViewSet):
    expected_views = ["list", "detail", "create", "update", "delete"]
    for view_name in expected_views:
        assert cv_publisher.has_view(view_name), f"ViewSet missing view: {view_name}"


@pytest.mark.django_db
def test_viewset_url_patterns(cv_publisher: ViewSet):
    patterns = cv_publisher.urlpatterns
    assert len(patterns) >= 5

    # Verify INT pk regex is used (not UUID)
    routes = [p.pattern.regex.pattern for p in patterns]
    has_int_pk = any(r"\d+" in route for route in routes)
    assert has_int_pk, f"Expected INT pk regex in patterns, got: {routes}"

    has_uuid = any("4[0-9a-f]" in route for route in routes)
    assert not has_uuid, "Should not have UUID pk regex"


@pytest.mark.django_db
def test_viewset_router_names(cv_publisher: ViewSet):
    assert cv_publisher.get_router_name("list") == "publisher-list"
    assert cv_publisher.get_router_name("detail") == "publisher-detail"
    assert cv_publisher.get_router_name("create") == "publisher-create"
    assert cv_publisher.get_router_name("update") == "publisher-update"
    assert cv_publisher.get_router_name("delete") == "publisher-delete"


@pytest.mark.django_db
def test_create_publisher(client_user_publisher_add: Client, cv_publisher):
    response = client_user_publisher_add.get("/publisher/create/")
    assert response.status_code == 200

    response = client_user_publisher_add.post("/publisher/create/", {
        "name": "Penguin Random House",
    })
    assert response.status_code == 302
    assert response.url == "/publisher/"

    assert Publisher.objects.filter(name="Penguin Random House").exists()


@pytest.mark.django_db
def test_update_publisher(client_user_publisher_change: Client, cv_publisher, publisher_penguin):
    pk = publisher_penguin.pk

    response = client_user_publisher_change.get(f"/publisher/{pk}/update/")
    assert response.status_code == 200

    response = client_user_publisher_change.post(f"/publisher/{pk}/update/", {
        "name": "Penguin Classics",
    })
    assert response.status_code == 302
    assert response.url == "/publisher/"

    publisher_penguin.refresh_from_db()
    assert publisher_penguin.name == "Penguin Classics"


@pytest.mark.django_db
def test_delete_publisher(client_user_publisher_delete: Client, cv_publisher, publisher_penguin):
    pk = publisher_penguin.pk

    response = client_user_publisher_delete.get(f"/publisher/{pk}/delete/")
    assert response.status_code == 200

    response = client_user_publisher_delete.post(f"/publisher/{pk}/delete/", {"confirm": True})
    assert response.status_code == 302
    assert response.url == "/publisher/"

    assert not Publisher.objects.filter(pk=pk).exists()


@pytest.mark.django_db
def test_detail_publisher(client_user_publisher_view: Client, cv_publisher, publisher_penguin):
    pk = publisher_penguin.pk

    response = client_user_publisher_view.get(f"/publisher/{pk}/detail/")
    assert response.status_code == 200

    content = response.content.decode("utf-8")
    assert "Penguin" in content


@pytest.mark.django_db
def test_list_publisher(client_user_publisher_view: Client, cv_publisher, publisher_penguin):
    response = client_user_publisher_view.get("/publisher/")
    assert response.status_code == 200

    table = Table(response)
    assert len(table.rows) == 1
    assert table.rows[0].columns[1].text == "Penguin"
