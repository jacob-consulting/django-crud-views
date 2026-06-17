"""SiblingContextButton: child view -> sibling collection, parent PK from the URL."""

import pytest
from django.urls import reverse

from crud_views.lib.view import SiblingContextButton
from tests.lib.helper.user import user_viewset_permission


@pytest.fixture
def cv_contract():
    from tests.test1.app.views import cv_contract as ret

    return ret


@pytest.fixture
def client_book_and_contract_view(client, cv_book, cv_contract):
    from django.contrib.auth.models import User

    user = User.objects.create_user(username="user_book_contract_view", password="password")
    user_viewset_permission(user, cv_book, "view")
    user_viewset_permission(user, cv_contract, "view")
    client.force_login(user)
    return client


def _book_list_view(client, publisher):
    from tests.test1.app.views import cv_book

    url = reverse(cv_book.get_router_name("list"), kwargs={"publisher_pk": publisher.pk})
    resp = client.get(url)
    assert resp.status_code == 200
    return resp.context["view"]


@pytest.mark.django_db
def test_links_to_sibling_with_parent_pk(
    client_book_and_contract_view, cv_contract, publisher_penguin, book_hitchhiker
):
    view = _book_list_view(client_book_and_contract_view, publisher_penguin)
    btn = SiblingContextButton(key="to_contracts", sibling_name="contract")
    ctx = btn.get_context(view.cv_get_view_context())

    expected = reverse(cv_contract.get_router_name("list"), kwargs={"publisher_pk": publisher_penguin.pk})
    assert ctx["cv_url"] == expected
    assert ctx["cv_access"] is True


@pytest.mark.django_db
def test_hidden_without_access(client_user_book_view, cv_book, publisher_penguin, book_hitchhiker):
    # user has book view but NOT contract view
    view = _book_list_view(client_user_book_view, publisher_penguin)
    btn = SiblingContextButton(key="to_contracts", sibling_name="contract")
    ctx = btn.get_context(view.cv_get_view_context())
    assert ctx.get("cv_access") is not True


@pytest.mark.django_db
def test_empty_on_parentless_view(client_user_publisher_view, cv_publisher, publisher_penguin):
    url = reverse(cv_publisher.get_router_name("list"))
    resp = client_user_publisher_view.get(url)
    assert resp.status_code == 200
    view = resp.context["view"]
    btn = SiblingContextButton(key="to_contracts", sibling_name="contract")
    assert btn.get_context(view.cv_get_view_context()) == {}


@pytest.mark.django_db
def test_unknown_sibling_raises(client_user_book_view, cv_book, publisher_penguin, book_hitchhiker):
    from crud_views.lib.exceptions import ViewSetNotFoundError

    view = _book_list_view(client_user_book_view, publisher_penguin)
    btn = SiblingContextButton(key="to_nothing", sibling_name="does_not_exist")
    with pytest.raises(ViewSetNotFoundError):
        btn.get_context(view.cv_get_view_context())
