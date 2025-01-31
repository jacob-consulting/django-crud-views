import pytest
from django.contrib.auth import get_user_model

from tests.lib.helper.boostrap5 import Table

User = get_user_model()


@pytest.mark.django_db
def test_author_view(client_user_author_view, cv_author, author_douglas_adams):
    client = client_user_author_view

    response = client.get("/author/")
    assert response.status_code == 200

    # list
    table = Table(response)
    row = table.rows[0]
    assert row.columns[1].text == author_douglas_adams.first_name

    # detail
    action_detail = row.get_action("detail")
    assert not action_detail.is_disabled
    response = client.get(action_detail.href)
    assert response.status_code == 200

    # create
    action_create = table.get_context_action("create")
    assert action_create.is_disabled
    response = client.get(action_create.href)
    assert response.status_code == 403

    # delete
    action_delete = row.get_action("delete")
    assert action_delete.is_disabled
    response = client.get(action_delete.href)
    assert response.status_code == 403

    # update
    action_update = row.get_action("update")
    assert action_update.is_disabled
    response = client.get(action_update.href)
    assert response.status_code == 403
