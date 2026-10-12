"""#174: overflow menu on cards."""

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from lxml import html as lxml_html

from crud_views.lib.view import CardAction
from tests.lib.helper.user import user_viewset_permission
from tests.test1.app.views import (
    AuthorCardListView,
    AuthorPingView,
    AuthorUpdateView,
    PublisherCardListView,
    cv_author,
    cv_book,
    cv_publisher,
)

CARD = "//div[contains(@class, 'card') and contains(@class, 'mb-3')]"


def _client(grants) -> Client:
    user = User.objects.create_user(username=f"card_174_{len(grants)}", password="pw")
    for viewset, perms in grants:
        for perm in perms:
            user_viewset_permission(user, viewset, perm)
    client = Client()
    client.force_login(user)
    return client


def _card(client, url):
    resp = client.get(url)
    assert resp.status_code == 200
    return lxml_html.fromstring(resp.content).xpath(CARD)[0]


@pytest.fixture
def author_card_actions(monkeypatch):
    monkeypatch.setattr(
        AuthorCardListView,
        "cv_card_actions",
        [
            CardAction(key="detail", label="Details", variant="primary", flex=True),
            CardAction(key="update", label="Edit", variant="primary", flex=True, no_label=True),
            CardAction(key="ping", label="Ping"),
        ],
    )
    monkeypatch.setattr(AuthorCardListView, "cv_card_actions_inline", ["detail"])
    # AuthorPingView has no label templates of its own (test-app quirk)
    monkeypatch.setattr(AuthorPingView, "cv_action_label_template_code", "Ping", raising=False)
    monkeypatch.setattr(AuthorPingView, "cv_action_short_label_template_code", "Ping", raising=False)


@pytest.mark.django_db
def test_inline_card_button_unchanged_and_menu(db, author_douglas_adams, author_card_actions):
    card = _card(_client([(cv_author, ("view", "change"))]), reverse(cv_author.get_router_name("card")))
    row = card.cssselect(".d-flex.gap-2")[0]
    detail = row.xpath("./a")[0]
    assert "btn-primary" in detail.get("class") and "flex-grow-1" in detail.get("class")
    wrapper = row.xpath("./div[contains(@class, 'dropdown')]")[0]
    toggle = wrapper.cssselect(".cv-menu-toggle")[0]
    assert "btn-secondary" in toggle.get("class") and "btn-sm" in toggle.get("class")
    items = wrapper.cssselect(".dropdown-item")
    # variant / flex / no_label are ignored in the menu; CardAction.label is the item text
    assert [i.text_content().strip() for i in items] == ["Edit", "Ping"]
    assert all("btn" not in i.get("class") for i in items)


@pytest.mark.django_db
def test_post_card_item_has_form_outside_menu(db, author_douglas_adams, author_card_actions):
    card = _card(_client([(cv_author, ("view", "change"))]), reverse(cv_author.get_router_name("card")))
    ping = next(i for i in card.cssselect(".dropdown-item") if i.text_content().strip() == "Ping")
    assert ping.get("data-cv-action") == "submit-form"
    form = card.xpath(f'.//form[@id="{ping.get("data-cv-target")}"]')[0]
    assert not form.xpath("ancestor::ul")
    assert form.cssselect('input[name="csrfmiddlewaretoken"]')


@pytest.mark.django_db
def test_disabled_card_item(db, author_douglas_adams, author_card_actions, monkeypatch):
    monkeypatch.setattr(AuthorUpdateView, "cv_inaccessible_actions", "disable")
    card = _card(_client([(cv_author, ("view",))]), reverse(cv_author.get_router_name("card")))
    edit = next(i for i in card.cssselect(".dropdown-item") if i.text_content().strip() == "Edit")
    assert edit.tag == "button" and edit.get("disabled") is not None
    assert edit.get("data-cv-disabled") == "permission"


@pytest.mark.django_db
def test_child_card_action_folds_by_child_name(db, publisher_penguin, monkeypatch):
    monkeypatch.setattr(PublisherCardListView, "cv_card_actions_inline", ["detail"])
    client = _client([(cv_publisher, ("view",)), (cv_book, ("view",))])
    card = _card(client, reverse(cv_publisher.get_router_name("card")))
    items = card.cssselect(".dropdown-item")
    assert [i.text_content().strip() for i in items] == ["Books"]
    assert items[0].get("href")
    monkeypatch.setattr(PublisherCardListView, "cv_card_actions_inline", ["detail", "book"])
    card = _card(client, reverse(cv_publisher.get_router_name("card")))
    assert card.cssselect(".cv-menu-toggle") == []
