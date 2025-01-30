import pytest
from django.contrib.auth import get_user_model
from django.test.client import Client

from tests.lib.helper.boostrap5 import Table

User = get_user_model()

@pytest.mark.django_db
def test_debug_view(user_author_view: User, cv_author, author_douglas_adams, author_terry_pratchett):
    client = Client()

    client.force_login(user_author_view)
    response = client.get("/author/")
    assert response.status_code == 200

    lst = Table(response)
    headers = lst.headers

    for header in headers:
        print(header.text, header.orderable)
    for row in lst.rows:
        for action in row.actions:
            print(action.title, action.href)
        # for col in row.columns:
        #    col.text

        # if header.is_action:
        #    for action in header.actions:
        #        print(action.text, action.href)

    x = 1

@pytest.mark.skip(reason="disabled")
def test_fail():
    assert False, "this is a test"
