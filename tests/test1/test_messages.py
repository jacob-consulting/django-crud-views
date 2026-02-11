import pytest
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.test.client import Client

from tests.lib.helper.user import user_viewset_permission
from tests.test1.app.models import Publisher


@pytest.fixture
def client_publisher_add_view(client, cv_publisher) -> Client:
    """Client with both add and view permissions (needed to follow redirect to list)."""
    user = User.objects.create_user(username="user_pub_add_view", password="password")
    user_viewset_permission(user, cv_publisher, "add")
    user_viewset_permission(user, cv_publisher, "view")
    client.force_login(user)
    return client


@pytest.fixture
def client_publisher_change_view(client, cv_publisher) -> Client:
    """Client with both change and view permissions."""
    user = User.objects.create_user(username="user_pub_change_view", password="password")
    user_viewset_permission(user, cv_publisher, "change")
    user_viewset_permission(user, cv_publisher, "view")
    client.force_login(user)
    return client


@pytest.fixture
def client_publisher_delete_view(client, cv_publisher) -> Client:
    """Client with both delete and view permissions."""
    user = User.objects.create_user(username="user_pub_delete_view", password="password")
    user_viewset_permission(user, cv_publisher, "delete")
    user_viewset_permission(user, cv_publisher, "view")
    client.force_login(user)
    return client


@pytest.mark.django_db
def test_create_message(client_publisher_add_view: Client, cv_publisher):
    response = client_publisher_add_view.post(
        "/publisher/create/", {"name": "Penguin"}, follow=True
    )
    assert response.status_code == 200

    messages = list(get_messages(response.wsgi_request))
    assert len(messages) == 1
    assert "Created" in str(messages[0])
    assert "Penguin" in str(messages[0])


@pytest.mark.django_db
def test_update_message(client_publisher_change_view: Client, cv_publisher, publisher_penguin):
    pk = publisher_penguin.pk
    response = client_publisher_change_view.post(
        f"/publisher/{pk}/update/", {"name": "Penguin Classics"}, follow=True
    )
    assert response.status_code == 200

    messages = list(get_messages(response.wsgi_request))
    assert len(messages) == 1
    assert "Updated" in str(messages[0])
    assert "Penguin Classics" in str(messages[0])


@pytest.mark.django_db
def test_delete_message(client_publisher_delete_view: Client, cv_publisher, publisher_penguin):
    pk = publisher_penguin.pk
    response = client_publisher_delete_view.post(
        f"/publisher/{pk}/delete/", {"confirm": True}, follow=True
    )
    assert response.status_code == 200

    messages = list(get_messages(response.wsgi_request))
    assert len(messages) == 1
    assert "Deleted" in str(messages[0])
    assert "Penguin" in str(messages[0])


@pytest.mark.django_db
def test_no_message_on_get(client_user_publisher_view: Client, cv_publisher, publisher_penguin):
    """GET requests should not produce any flash messages."""
    pk = publisher_penguin.pk
    response = client_user_publisher_view.get(f"/publisher/{pk}/detail/")
    assert response.status_code == 200

    messages = list(get_messages(response.wsgi_request))
    assert len(messages) == 0
