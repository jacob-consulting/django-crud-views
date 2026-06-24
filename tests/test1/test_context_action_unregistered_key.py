"""Regression: a list+detail-only ViewSet (cv_contract) must not raise
ViewSetKeyFoundError on its own pages because the default *_CONTEXT_ACTIONS
reference unregistered create/delete view keys. The bug only bites under strict
mode (CRUD_VIEWS_STRICT, which defaults to DEBUG); tests run DEBUG=False, so the
integration test forces strict mode to reproduce it."""

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


@pytest.fixture
def strict_mode(monkeypatch):
    from django.conf import settings as dj_settings

    monkeypatch.setattr(dj_settings, "CRUD_VIEWS_STRICT", True, raising=False)


@pytest.mark.django_db
def test_pages_render_with_unregistered_default_keys_in_strict(
    strict_mode, client_user_contract_view, cv_contract, publisher_penguin
):
    # list: default list_context_actions includes "create" (not registered on cv_contract)
    list_url = reverse(cv_contract.get_router_name("list"), kwargs={"publisher_pk": publisher_penguin.pk})
    resp = client_user_contract_view.get(list_url)
    assert resp.status_code == 200
    assert b'cv-key="create"' not in resp.content

    # detail: default detail_context_actions includes "update"/"delete" (not registered)
    from tests.test1.app.models import Contract

    contract = Contract.objects.create(publisher=publisher_penguin, title="ACME")
    detail_url = reverse(
        cv_contract.get_router_name("detail"),
        kwargs={"publisher_pk": publisher_penguin.pk, "pk": contract.pk},
    )
    resp = client_user_contract_view.get(detail_url)
    assert resp.status_code == 200
    assert b'cv-key="update"' not in resp.content
    assert b'cv-key="delete"' not in resp.content


@pytest.mark.django_db
def test_get_context_buttons_skips_unregistered_keys(client_user_contract_view, cv_contract, publisher_penguin):
    url = reverse(cv_contract.get_router_name("list"), kwargs={"publisher_pk": publisher_penguin.pk})
    resp = client_user_contract_view.get(url)
    view = resp.context["view"]
    keys = [b.get("cv_key") for b in view.cv_get_context_buttons(keys=["create", "list"])]
    assert "create" not in keys
    assert "list" in keys
