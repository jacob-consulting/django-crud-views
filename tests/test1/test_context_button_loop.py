"""cv_get_context_buttons (access-filtered list) + {% cv_render_context_button %}."""

import pytest
from django.template import Context, Template
from django.urls import reverse

from tests.lib.helper.user import user_viewset_permission


@pytest.fixture
def client_author_view_change(client, cv_author):
    from django.contrib.auth.models import User

    user = User.objects.create_user(username="user_author_view_change_loop", password="password")
    user_viewset_permission(user, cv_author, "view")
    user_viewset_permission(user, cv_author, "change")
    client.force_login(user)
    return client


def _detail_view(client, cv_author, author):
    url = reverse(cv_author.get_router_name("detail"), kwargs={"pk": author.pk})
    resp = client.get(url)
    assert resp.status_code == 200
    return resp.context["view"], resp.context["request"]


@pytest.mark.django_db
def test_list_filters_inaccessible(client_user_author_view, cv_author, author_douglas_adams):
    # view-only user: 'update'/'delete' must be filtered out of the list
    view, _ = _detail_view(client_user_author_view, cv_author, author_douglas_adams)
    keys = [b.get("cv_key") for b in view.cv_get_context_buttons()]
    assert "update" not in keys
    assert "delete" not in keys


@pytest.mark.django_db
def test_explicit_keys_order(client_author_view_change, cv_author, author_douglas_adams):
    view, _ = _detail_view(client_author_view_change, cv_author, author_douglas_adams)
    buttons = view.cv_get_context_buttons(keys=["update", "detail"])
    assert [b.get("cv_key") for b in buttons] == ["update", "detail"]


@pytest.mark.django_db
def test_render_tag_renders_entry(client_author_view_change, cv_author, author_douglas_adams):
    view, request = _detail_view(client_author_view_change, cv_author, author_douglas_adams)
    tpl = Template(
        "{% load crud_views %}"
        "{% for ctx in view.cv_get_context_buttons %}"
        "<span>{% cv_render_context_button ctx %}</span>{% endfor %}"
    )
    html = tpl.render(Context({"view": view, "request": request}))
    assert 'cv-key="update"' in html
