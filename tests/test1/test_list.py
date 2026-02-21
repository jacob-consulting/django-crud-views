import pytest
from django.test.client import Client

from tests.lib.helper.boostrap5 import Table


@pytest.mark.django_db
def test_list_empty(client_user_author_view: Client, cv_author):
    response = client_user_author_view.get("/author/")
    assert response.status_code == 200

    table = Table(response)
    assert len(table.rows) == 0


@pytest.mark.django_db
def test_list_multiple_authors(
    client_user_author_view: Client, cv_author, author_douglas_adams, author_terry_pratchett
):
    response = client_user_author_view.get("/author/")
    assert response.status_code == 200

    table = Table(response)
    assert len(table.rows) == 2

    texts = [row.columns[1].text for row in table.rows]
    assert "Douglas" in texts
    assert "Terry" in texts


@pytest.mark.django_db
def test_list_table_headers(client_user_author_view: Client, cv_author, author_douglas_adams):
    response = client_user_author_view.get("/author/")
    assert response.status_code == 200

    table = Table(response)
    header_texts = [h.text for h in table.headers]

    assert "Id" in header_texts or "id" in [h.lower() for h in header_texts]
    assert "First name" in header_texts or "first_name" in [h.lower() for h in header_texts]
    assert "Last name" in header_texts or "last_name" in [h.lower() for h in header_texts]
    assert "Pseudonym" in header_texts or "pseudonym" in [h.lower() for h in header_texts]
    assert "Actions" in header_texts


@pytest.mark.django_db
def test_list_row_actions(client_user_author_view: Client, cv_author, author_douglas_adams):
    response = client_user_author_view.get("/author/")
    assert response.status_code == 200

    table = Table(response)
    row = table.rows[0]
    action_keys = [a.key for a in row.actions]

    assert "detail" in action_keys
    assert "update" in action_keys
    assert "delete" in action_keys
