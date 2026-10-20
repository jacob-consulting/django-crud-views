"""#174: group methods resolve on the rendering view and split by configured key."""

import pytest
from django.urls import reverse

from crud_views.lib.exceptions import ViewSetKeyFoundError
from crud_views.lib.view import CardAction
from tests.test1.app.views import (
    AuthorCardListView,
    AuthorDeleteView,
    AuthorDetailView,
    AuthorListView,
    PublisherCardListView,
    cv_author,
    cv_publisher,
)


def _view(client, url):
    resp = client.get(url)
    assert resp.status_code == 200
    return resp.context["view"]


def _keys(ctxs):
    return [c["cv_key"] for c in ctxs]


@pytest.fixture
def list_view(client_user_author_view, author_douglas_adams):
    return _view(client_user_author_view, reverse(cv_author.get_router_name("list")))


@pytest.fixture
def detail_view(client_user_author_view, author_douglas_adams):
    url = reverse(cv_author.get_router_name("detail"), kwargs={"pk": author_douglas_adams.pk})
    return _view(client_user_author_view, url)


@pytest.mark.django_db
def test_list_group_all_inline_by_default(list_view, author_douglas_adams):
    group = list_view.cv_get_list_action_group(author_douglas_adams)
    assert _keys(group.inline) == ["detail"]  # view-only user: update and delete are hidden
    assert group.menu == []


@pytest.mark.django_db
def test_list_group_hidden_actions_absent(list_view, author_douglas_adams, monkeypatch):
    # view-only user: update/delete are hidden (default "hide") -> appear nowhere (Review Focus 2)
    monkeypatch.setattr(AuthorListView, "cv_list_actions_inline", ["detail", "update"])
    group = list_view.cv_get_list_action_group(author_douglas_adams)
    assert _keys(group.inline) == ["detail"]
    assert group.menu == []


@pytest.mark.django_db
def test_list_group_disabled_go_to_menu(list_view, author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorListView, "cv_list_actions_inline", ["detail"])
    monkeypatch.setattr(AuthorDeleteView, "cv_inaccessible_actions", "disable")
    group = list_view.cv_get_list_action_group(author_douglas_adams)
    assert _keys(group.menu) == ["delete"]
    assert group.menu[0]["cv_disabled"] is True


@pytest.mark.django_db
def test_list_group_unregistered_key_skipped(list_view, author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorListView, "cv_list_actions", ["detail", "not_registered"])
    monkeypatch.setattr(AuthorListView, "cv_list_actions_inline", [])
    group = list_view.cv_get_list_action_group(author_douglas_adams)
    assert _keys(group.menu) == ["detail"]


@pytest.mark.django_db
def test_context_group_home_matches_configured_key(detail_view, author_douglas_adams, monkeypatch):
    # Review Focus 1: "home" resolves to cv_key "list" but is matched by its configured key
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions", ["home", "detail"])
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_inline", ["home"])
    group = detail_view.cv_get_context_action_group(author_douglas_adams)
    assert _keys(group.inline) == ["list"]
    assert _keys(group.menu) == ["detail"]


@pytest.mark.django_db
def test_context_group_resolves_on_rendering_view(detail_view, author_douglas_adams, monkeypatch):
    # an inline value on the TARGET (list) view must not matter for the detail toolbar
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions", ["home", "detail"])
    monkeypatch.setattr(AuthorListView, "cv_context_actions_inline", [])
    group = detail_view.cv_get_context_action_group(author_douglas_adams)
    assert _keys(group.inline) == ["list", "detail"]
    assert group.menu == []


@pytest.mark.django_db
def test_card_group_by_key_and_child_name(client, user_publisher_view, publisher_penguin, monkeypatch, cv_book):
    from tests.lib.helper.user import user_viewset_permission

    # grant the child (book) permission BEFORE the request, so the child card action is accessible
    user_viewset_permission(user_publisher_view, cv_book, "view")
    client.force_login(user_publisher_view)
    view = _view(client, reverse(cv_publisher.get_router_name("card")))
    monkeypatch.setattr(PublisherCardListView, "cv_card_actions_inline", ["detail"])
    group = view.cv_get_card_action_group(publisher_penguin)
    assert [c["cv_label"] for c in group.inline] == ["Details"]
    assert [c["cv_label"] for c in group.menu] == ["Books"]


@pytest.mark.django_db
def test_card_tag_and_group_share_data(client_user_author_view, author_douglas_adams, monkeypatch):
    view = _view(client_user_author_view, reverse(cv_author.get_router_name("card")))
    action = CardAction(key="detail", label="Details", variant="primary", flex=True)
    data = view.cv_get_card_action_data(action, author_douglas_adams, view.request.user)
    assert data["cv_label"] == "Details"
    assert data["cv_variant"] == "primary"
    monkeypatch.setattr(AuthorCardListView, "cv_card_actions", [action])
    monkeypatch.setattr(AuthorCardListView, "cv_card_actions_inline", [])
    group = view.cv_get_card_action_group(author_douglas_adams)
    assert group.menu[0]["cv_url"] == data["cv_url"]


@pytest.mark.django_db
def test_list_group_skips_unregistered_key(list_view, author_douglas_adams, monkeypatch):
    # defensive guard: a key whose context cannot be resolved is skipped, not raised
    monkeypatch.setattr(AuthorListView, "cv_list_actions", ["detail", "update"])
    monkeypatch.setattr(AuthorListView, "cv_list_actions_inline", [])
    original = list_view.cv_get_context

    def raising(*args, key=None, **kwargs):
        if key == "update":
            raise ViewSetKeyFoundError(key)
        return original(*args, key=key, **kwargs)

    monkeypatch.setattr(list_view, "cv_get_context", raising)
    group = list_view.cv_get_list_action_group(author_douglas_adams)
    assert _keys(group.menu) == ["detail"]
