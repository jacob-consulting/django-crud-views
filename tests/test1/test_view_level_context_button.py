"""View-level context buttons: CrudView.cv_context_buttons defines buttons; view overrides ViewSet."""

import pytest
from django.urls import reverse

from crud_views.lib.view.buttons import ContextButton


def _book_list_view(client, publisher):
    from tests.test1.app.views import cv_book

    url = reverse(cv_book.get_router_name("list"), kwargs={"publisher_pk": publisher.pk})
    resp = client.get(url)
    assert resp.status_code == 200
    return resp.context["view"]


@pytest.mark.django_db
def test_view_level_overrides_viewset(client_user_book_view, cv_book, publisher_penguin, book_hitchhiker):
    view = _book_list_view(client_user_book_view, publisher_penguin)
    # ViewSet provides a default "home" button
    assert view.cv_get_context_button("home").key == "home"
    override = ContextButton(key="home", key_target="list", label_template_code="VIEWLEVEL")
    view.cv_context_buttons = [override]
    # view-level button with the same key wins (identity check)
    assert view.cv_get_context_button("home") is override


@pytest.mark.django_db
def test_falls_back_to_viewset(client_user_book_view, cv_book, publisher_penguin, book_hitchhiker):
    view = _book_list_view(client_user_book_view, publisher_penguin)
    view.cv_context_buttons = [ContextButton(key="custom", key_target="list")]
    # a key not defined at view level falls back to the ViewSet's buttons
    assert view.cv_get_context_button("home").key == "home"


@pytest.mark.django_db
def test_none_default_unchanged(client_user_book_view, cv_book, publisher_penguin, book_hitchhiker):
    view = _book_list_view(client_user_book_view, publisher_penguin)
    assert view.cv_context_buttons is None
    assert view.cv_get_context_button("home").key == "home"
    assert view.cv_get_context_button("does_not_exist") is None


@pytest.mark.django_db
def test_explicit_render_only_listed_keys(client_user_book_view, cv_book, publisher_penguin, book_hitchhiker):
    view = _book_list_view(client_user_book_view, publisher_penguin)
    view.cv_context_buttons = [ContextButton(key="custom", key_target="list", label_template_code="UNLISTED")]

    # "custom" defined but NOT in cv_context_actions -> not rendered
    view.cv_context_actions = ["home"]
    labels = [c.get("cv_action_label") for c in view.cv_get_context_buttons()]
    assert "UNLISTED" not in labels

    # listing the key in cv_context_actions renders it
    view.cv_context_actions = ["home", "custom"]
    labels = [c.get("cv_action_label") for c in view.cv_get_context_buttons()]
    assert "UNLISTED" in labels
