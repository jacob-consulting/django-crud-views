"""#243: the stock card has card_title / card_content / card_actions blocks and card:root / card:body / card:title
class keys. The stock markup itself is pinned by the action_menus card goldens."""

import re
import uuid

import pytest
from django.contrib.auth.models import User
from django.test import Client, override_settings
from django.urls import reverse
from lxml import html as lxml_html

from crud_views.lib.view import CardAction
from tests.lib.helper.user import user_viewset_permission
from tests.test1.app.views import AuthorCardListView, cv_author

# a menu next to the inline buttons, so the card_actions block carries both the menu forms and the container
ACTIONS = [*AuthorCardListView.cv_card_actions, CardAction(key="ping", label="Ping")]


@pytest.fixture
def client_full() -> Client:
    user = User.objects.create_user(username=f"card_243_{uuid.uuid4().hex[:8]}", password="pw")
    for perm in ("view", "add", "change", "delete"):
        user_viewset_permission(user, cv_author, perm)
    client = Client()
    client.force_login(user)
    return client


@pytest.fixture
def actions(monkeypatch):
    monkeypatch.setattr(AuthorCardListView, "cv_card_actions", ACTIONS)
    monkeypatch.setattr(AuthorCardListView, "cv_card_actions_inline", ["detail", "update"])


def _card(client):
    resp = client.get(reverse(cv_author.get_router_name("card")))
    assert resp.status_code == 200
    (card,) = lxml_html.fromstring(resp.content).cssselect(".row > div > div")
    return card


def _markup(element) -> str:
    # the CSRF token is masked differently on every render
    markup = lxml_html.tostring(element, encoding="unicode")
    return re.sub(r'(name="csrfmiddlewaretoken" value=")[^"]*"', r'\1CSRF"', markup)


@pytest.mark.django_db
def test_extending_template_fills_content_and_keeps_actions(client_full, actions, author_douglas_adams, monkeypatch):
    stock = _markup(_card(client_full))

    monkeypatch.setattr(AuthorCardListView, "cv_card_template", "app/author_card_blocks.html")
    card = _card(client_full)
    (content,) = card.cssselect("p.cv-test-content")
    assert content.text == "Adams"
    assert len(card.cssselect("[cv-card-container]")) == 1
    assert card.cssselect("form")  # the menu's hidden action forms
    # remove the filled block and what is left is the stock card, actions included
    content.drop_tree()
    assert _markup(card) == stock


@pytest.mark.django_db
@override_settings(
    CRUD_VIEWS_BUTTON_CLASSES={"card:root": "theme-card", "card:body": "theme-body", "card:title": "theme-title h3"}
)
def test_class_keys(client_full, author_douglas_adams):
    card = _card(client_full)
    assert card.get("class") == "theme-card"
    (body,) = card.cssselect(".theme-body")
    (title,) = body.cssselect("h5")
    assert title.get("class") == "theme-title h3"
    assert title.text == "Douglas Adams"
