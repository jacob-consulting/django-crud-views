import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

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

    # create (toolbar context action) is hidden for a view-only user; endpoint still 403
    with pytest.raises(KeyError):
        table.get_context_action("create")
    assert client.get(reverse(cv_author.get_router_name("create"))).status_code == 403

    # update / delete (row actions) are hidden; endpoints still 403
    with pytest.raises(KeyError):
        row.get_action("update")
    assert (
        client.get(reverse(cv_author.get_router_name("update"), kwargs={"pk": author_douglas_adams.pk})).status_code
        == 403
    )
    with pytest.raises(KeyError):
        row.get_action("delete")
    assert (
        client.get(reverse(cv_author.get_router_name("delete"), kwargs={"pk": author_douglas_adams.pk})).status_code
        == 403
    )
