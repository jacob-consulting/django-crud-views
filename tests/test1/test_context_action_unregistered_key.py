"""Regression: a list+detail-only ViewSet (cv_contract) must not 500 on its own
pages because the default *_CONTEXT_ACTIONS reference unregistered create/delete
view keys. DEBUG=True in the test settings, so CRUD_VIEWS_STRICT is on by default."""

import pytest
from django.urls import reverse

from tests.lib.helper.user import user_viewset_permission


@pytest.fixture
def cv_contract():
    from tests.test1.app.views import cv_contract as ret

    return ret


@pytest.fixture
def client_user_contract_view(client, cv_contract):
    from django.contrib.auth.models import User

    user = User.objects.create_user(username="user_contract_view", password="password")
    user_viewset_permission(user, cv_contract, "view")
    client.force_login(user)
    return client


@pytest.mark.django_db
def test_contract_list_renders_without_create_view(client_user_contract_view, cv_contract, publisher_penguin):
    # cv_contract registers only list + detail; default list_context_actions
    # includes "create" (not a registered view). Must render, not raise.
    url = reverse(cv_contract.get_router_name("list"), kwargs={"publisher_pk": publisher_penguin.pk})
    resp = client_user_contract_view.get(url)
    assert resp.status_code == 200
    # the unregistered create button is simply absent
    assert b'cv-key="create"' not in resp.content


@pytest.mark.django_db
def test_contract_detail_renders_without_update_delete_views(client_user_contract_view, cv_contract, publisher_penguin):
    from tests.test1.app.models import Contract

    contract = Contract.objects.create(publisher=publisher_penguin, title="ACME")
    url = reverse(
        cv_contract.get_router_name("detail"),
        kwargs={"publisher_pk": publisher_penguin.pk, "pk": contract.pk},
    )
    resp = client_user_contract_view.get(url)
    assert resp.status_code == 200
    assert b'cv-key="update"' not in resp.content
    assert b'cv-key="delete"' not in resp.content


@pytest.mark.django_db
def test_get_context_buttons_skips_unregistered_keys(client_user_contract_view, cv_contract, publisher_penguin):
    url = reverse(cv_contract.get_router_name("list"), kwargs={"publisher_pk": publisher_penguin.pk})
    resp = client_user_contract_view.get(url)
    view = resp.context["view"]
    # explicit mix of unregistered ("create") and registered ("list") keys
    keys = [b.get("cv_key") for b in view.cv_get_context_buttons(keys=["create", "list"])]
    assert "create" not in keys
    assert "list" in keys
