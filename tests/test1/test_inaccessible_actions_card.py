"""#149: card actions (key and child) in disable mode; child card actions check child permission."""

import pytest
from django.test import Client
from lxml import html as lxml_html

from crud_views.lib.view import CardAction
from tests.lib.helper.user import user_viewset_permission
from tests.test1.app.views import AuthorCardListView, AuthorUpdateView, AuthorUpView, BookListView


def _card(client, url):
    resp = client.get(url)
    assert resp.status_code == 200
    doc = lxml_html.fromstring(resp.content)
    return resp.content.decode(), doc.cssselect(".card.mb-3")[0]


def _by_text(card, text):
    return [a for a in card.cssselect("a.btn") if text in a.text_content()]


@pytest.mark.django_db
def test_card_hide_is_default(client_user_author_view, author_douglas_adams):
    _, card = _card(client_user_author_view, "/author/card/")
    assert _by_text(card, "Edit") == []


@pytest.mark.django_db
def test_card_key_action_disabled(client_user_author_view, author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorUpdateView, "cv_inaccessible_actions", "disable")
    content, card = _card(client_user_author_view, "/author/card/")
    (btn,) = _by_text(card, "Edit")
    assert "disabled" in btn.get("class").split()
    assert btn.get("aria-disabled") == "true"
    assert btn.get("data-cv-disabled") == "permission"
    assert btn.get("href") is None
    assert f"/author/{author_douglas_adams.pk}/update/" not in content


@pytest.mark.django_db
def test_card_post_action_disabled_has_no_form(client_user_author_view, author_douglas_adams, monkeypatch):
    monkeypatch.setattr(
        AuthorCardListView,
        "cv_card_actions",
        [CardAction(key="detail", label="Details"), CardAction(key="up", label="Up")],
    )
    monkeypatch.setattr(AuthorUpView, "cv_inaccessible_actions", "disable")
    _, card = _card(client_user_author_view, "/author/card/")
    (btn,) = _by_text(card, "Up")
    assert btn.get("href") is None
    assert btn.get("data-cv-action") is None
    assert card.cssselect('form[id^="cv_form_"]') == []


@pytest.fixture
def client_publisher_view_only(cv_publisher):
    from django.contrib.auth.models import User

    user = User.objects.create_user(username="user_pub_no_book_149", password="password")
    user_viewset_permission(user, cv_publisher, "view")
    client = Client()
    client.force_login(user)
    return client


@pytest.mark.django_db
def test_child_card_action_disabled_without_child_permission(
    client_publisher_view_only, cv_book, publisher_penguin, monkeypatch
):
    monkeypatch.setattr(BookListView, "cv_inaccessible_actions", "disable")
    content, card = _card(client_publisher_view_only, "/publisher/card/")
    (btn,) = _by_text(card, "Books")
    assert btn.get("aria-disabled") == "true"
    assert btn.get("data-cv-disabled") == "permission"
    assert btn.get("href") is None
    assert f"/publisher/{publisher_penguin.pk}/book/" not in content


@pytest.fixture
def client_user_publisher_card_149(cv_publisher, cv_book):
    from django.contrib.auth.models import User

    user = User.objects.create_user(username="user_pub_card_149", password="password")
    user_viewset_permission(user, cv_publisher, "view")
    user_viewset_permission(user, cv_book, "view")
    client = Client()
    client.force_login(user)
    return client


@pytest.mark.django_db
def test_child_card_action_disabled_for_state(client_user_publisher_card_149, cv_book, publisher_penguin, monkeypatch):
    monkeypatch.setattr(BookListView, "cv_inaccessible_actions", "disable")
    monkeypatch.setattr(BookListView, "cv_action_enabled", classmethod(lambda cls, user, obj=None: False))
    _, card = _card(client_user_publisher_card_149, "/publisher/card/")
    (btn,) = _by_text(card, "Books")
    assert btn.get("data-cv-disabled") == "state"


@pytest.mark.django_db
def test_card_action_truthy_non_bool_access_renders_normal_link(
    client_user_author_view, author_douglas_adams, monkeypatch
):
    monkeypatch.setattr(AuthorUpdateView, "cv_has_access", classmethod(lambda cls, user, obj=None: 1))
    _, card = _card(client_user_author_view, "/author/card/")
    (btn,) = _by_text(card, "Edit")
    assert btn.get("href") == f"/author/{author_douglas_adams.pk}/update/"
    assert "disabled" not in btn.get("class").split()
    assert btn.get("aria-disabled") is None
