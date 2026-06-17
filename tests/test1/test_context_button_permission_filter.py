"""view|cv_context_has_permission:'key' for {% if %} gating."""

import pytest
from django.template import Context, Template
from django.urls import reverse

from tests.lib.helper.user import user_viewset_permission


@pytest.fixture
def client_author_view_change(client, cv_author):
    from django.contrib.auth.models import User

    user = User.objects.create_user(username="user_author_view_change_filter", password="password")
    user_viewset_permission(user, cv_author, "view")
    user_viewset_permission(user, cv_author, "change")
    client.force_login(user)
    return client


def _detail_view(client, cv_author, author):
    url = reverse(cv_author.get_router_name("detail"), kwargs={"pk": author.pk})
    resp = client.get(url)
    assert resp.status_code == 200
    return resp.context["view"], resp.context["request"]


def _render(view, request, key):
    tpl = Template(
        "{% load crud_views %}{% if view|cv_context_has_permission:'" + key + "' %}YES{% else %}NO{% endif %}"
    )
    return tpl.render(Context({"view": view, "request": request})).strip()


@pytest.mark.django_db
def test_true_for_permitted(client_author_view_change, cv_author, author_douglas_adams):
    view, request = _detail_view(client_author_view_change, cv_author, author_douglas_adams)
    assert _render(view, request, "update") == "YES"


@pytest.mark.django_db
def test_false_for_forbidden(client_user_author_view, cv_author, author_douglas_adams):
    view, request = _detail_view(client_user_author_view, cv_author, author_douglas_adams)
    assert _render(view, request, "update") == "NO"


@pytest.mark.django_db
def test_false_for_unknown_key(client_author_view_change, cv_author, author_douglas_adams):
    view, request = _detail_view(client_author_view_change, cv_author, author_douglas_adams)
    assert _render(view, request, "nope") == "NO"
