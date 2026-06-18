"""cv_is_active is populated for context buttons, true only on the target page."""

import pytest
from django.urls import reverse

from crud_views.lib.view import ContextButton


def _list_view(client, cv_author):
    url = reverse(cv_author.get_router_name("list"))
    resp = client.get(url)
    assert resp.status_code == 200
    return resp.context["view"]


def _detail_view(client, cv_author, author):
    url = reverse(cv_author.get_router_name("detail"), kwargs={"pk": author.pk})
    resp = client.get(url)
    assert resp.status_code == 200
    return resp.context["view"]


@pytest.mark.django_db
def test_context_button_active_on_target_page(client_user_author_view, cv_author):
    # on the list page, a button targeting "list" is active
    view = _list_view(client_user_author_view, cv_author)
    btn = ContextButton(key="home", key_target="list")
    ctx = btn.get_context(view.cv_get_view_context())
    assert ctx["cv_is_active"] is True


@pytest.mark.django_db
def test_context_button_inactive_off_target_page(client_user_author_view, cv_author, author_douglas_adams):
    # on a detail page, the same "list"-targeting button is not active
    view = _detail_view(client_user_author_view, cv_author, author_douglas_adams)
    btn = ContextButton(key="home", key_target="list")
    ctx = btn.get_context(view.cv_get_view_context())
    assert ctx["cv_is_active"] is False


@pytest.mark.django_db
def test_view_key_branch_still_sets_cv_is_active(client_user_author_view, cv_author, author_douglas_adams):
    # regression: the view-key branch keeps the correct value after the line-345 removal
    view = _list_view(client_user_author_view, cv_author)
    user = view.request.user
    list_ctx = view.cv_get_context(key="list", user=user)
    assert list_ctx["cv_is_active"] is True
    detail_ctx = view.cv_get_context(key="detail", obj=author_douglas_adams, user=user)
    assert detail_ctx["cv_is_active"] is False
