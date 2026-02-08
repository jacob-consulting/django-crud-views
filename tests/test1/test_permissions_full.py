import pytest
from django.test.client import Client

from tests.test1.app.models import Author


@pytest.mark.django_db
def test_anonymous_redirected(client: Client, cv_author, author_douglas_adams):
    pk = author_douglas_adams.pk

    urls = [
        "/author/",
        f"/author/{pk}/detail/",
        "/author/create/",
        f"/author/{pk}/update/",
        f"/author/{pk}/delete/",
    ]
    for url in urls:
        response = client.get(url)
        assert response.status_code == 302, f"Expected 302 for anonymous on {url}, got {response.status_code}"


@pytest.mark.django_db
def test_no_permission_denied(client_user_a: Client, cv_author, author_douglas_adams):
    pk = author_douglas_adams.pk

    urls = [
        "/author/",
        f"/author/{pk}/detail/",
        "/author/create/",
        f"/author/{pk}/update/",
        f"/author/{pk}/delete/",
    ]
    for url in urls:
        response = client_user_a.get(url)
        assert response.status_code == 403, f"Expected 403 for no-perm user on {url}, got {response.status_code}"


@pytest.mark.django_db
def test_add_permission_can_create_only(client_user_author_add: Client, cv_author, author_douglas_adams):
    pk = author_douglas_adams.pk

    # Can access create
    response = client_user_author_add.get("/author/create/")
    assert response.status_code == 200

    # Cannot access update or delete
    response = client_user_author_add.get(f"/author/{pk}/update/")
    assert response.status_code == 403

    response = client_user_author_add.get(f"/author/{pk}/delete/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_change_permission_can_update_only(client_user_author_change: Client, cv_author, author_douglas_adams):
    pk = author_douglas_adams.pk

    # Can access update
    response = client_user_author_change.get(f"/author/{pk}/update/")
    assert response.status_code == 200

    # Cannot access create or delete
    response = client_user_author_change.get("/author/create/")
    assert response.status_code == 403

    response = client_user_author_change.get(f"/author/{pk}/delete/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_delete_permission_can_delete_only(client_user_author_delete: Client, cv_author, author_douglas_adams):
    pk = author_douglas_adams.pk

    # Can access delete
    response = client_user_author_delete.get(f"/author/{pk}/delete/")
    assert response.status_code == 200

    # Cannot access create or update
    response = client_user_author_delete.get("/author/create/")
    assert response.status_code == 403

    response = client_user_author_delete.get(f"/author/{pk}/update/")
    assert response.status_code == 403
