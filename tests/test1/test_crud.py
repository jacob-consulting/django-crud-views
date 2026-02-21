import pytest
from django.test.client import Client

from tests.test1.app.models import Author


@pytest.mark.django_db
def test_create_author(client_user_author_add: Client, cv_author):
    # GET create form
    response = client_user_author_add.get("/author/create/")
    assert response.status_code == 200

    # POST valid data
    response = client_user_author_add.post(
        "/author/create/",
        {
            "first_name": "Isaac",
            "last_name": "Asimov",
            "pseudonym": "",
        },
    )
    assert response.status_code == 302
    assert response.url == "/author/"

    # Verify author created in DB
    assert Author.objects.filter(first_name="Isaac", last_name="Asimov").exists()


@pytest.mark.django_db
def test_update_author(client_user_author_change: Client, cv_author, author_douglas_adams):
    pk = author_douglas_adams.pk

    # GET update form
    response = client_user_author_change.get(f"/author/{pk}/update/")
    assert response.status_code == 200

    # POST updated data
    response = client_user_author_change.post(
        f"/author/{pk}/update/",
        {
            "first_name": "Douglas",
            "last_name": "Adams",
            "pseudonym": "DNA",
        },
    )
    assert response.status_code == 302
    assert response.url == "/author/"

    # Verify author updated in DB
    author_douglas_adams.refresh_from_db()
    assert author_douglas_adams.pseudonym == "DNA"


@pytest.mark.django_db
def test_delete_author(client_user_author_delete: Client, cv_author, author_douglas_adams):
    pk = author_douglas_adams.pk

    # GET delete confirmation
    response = client_user_author_delete.get(f"/author/{pk}/delete/")
    assert response.status_code == 200

    # POST to confirm deletion (form requires confirm checkbox)
    response = client_user_author_delete.post(f"/author/{pk}/delete/", {"confirm": True})
    assert response.status_code == 302
    assert response.url == "/author/"

    # Verify author deleted from DB
    assert not Author.objects.filter(pk=pk).exists()


@pytest.mark.django_db
def test_detail_author(client_user_author_view: Client, cv_author, author_douglas_adams):
    pk = author_douglas_adams.pk

    # GET detail page
    response = client_user_author_view.get(f"/author/{pk}/detail/")
    assert response.status_code == 200

    # Verify content contains author name
    content = response.content.decode("utf-8")
    assert "Douglas" in content
    assert "Adams" in content
