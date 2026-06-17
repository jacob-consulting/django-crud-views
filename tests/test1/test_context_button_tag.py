"""{% cv_context_button %} renders one button by key, hiding on no-access."""

import pytest
from django.template import Context, Template
from django.urls import reverse

from tests.lib.helper.user import user_viewset_permission


@pytest.fixture
def client_author_view_change(client, cv_author):
    from django.contrib.auth.models import User

    user = User.objects.create_user(username="user_author_view_change", password="password")
    user_viewset_permission(user, cv_author, "view")
    user_viewset_permission(user, cv_author, "change")
    client.force_login(user)
    return client


def _render(view, request, snippet):
    tpl = Template("{% load crud_views %}" + snippet)
    return tpl.render(Context({"view": view, "request": request})).strip()


def _detail_view(client, cv_author, author):
    url = reverse(cv_author.get_router_name("detail"), kwargs={"pk": author.pk})
    resp = client.get(url)
    assert resp.status_code == 200
    return resp.context["view"], resp.context["request"]


@pytest.mark.django_db
def test_button_rendered_when_access(client_author_view_change, cv_author, author_douglas_adams):
    view, request = _detail_view(client_author_view_change, cv_author, author_douglas_adams)
    html = _render(view, request, "{% cv_context_button 'update' %}")
    assert 'cv-key="update"' in html


@pytest.mark.django_db
def test_button_hidden_without_access(client_user_author_view, cv_author, author_douglas_adams):
    view, request = _detail_view(client_user_author_view, cv_author, author_douglas_adams)
    html = _render(view, request, "{% cv_context_button 'update' %}")
    assert html == ""


@pytest.mark.django_db
def test_unknown_key_is_empty(client_user_author_view, cv_author, author_douglas_adams):
    view, request = _detail_view(client_user_author_view, cv_author, author_douglas_adams)
    html = _render(view, request, "{% cv_context_button 'does_not_exist' %}")
    assert html == ""
