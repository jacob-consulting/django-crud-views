"""#213: the three label modes as rendered by crud_views/tags/button/action.html on card buttons."""

import uuid

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
AUTHOR_FULL = (cv_author, ("view", "add", "change", "delete"))
AUTHOR_VIEW_ONLY = (cv_author, ("view",))


def _client(grants) -> Client:
    user = User.objects.create_user(username=f"card_213_{uuid.uuid4().hex[:8]}", password="pw")
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


def _inline(card, key):
    """The one inline card button for a CardAction key (or child_name)."""
    (button,) = card.xpath(f'.//*[@cv-card-container]/*[@cv-key="{key}"]')
    return button


def _icons(button) -> list:
    return button.xpath(".//i")


def _text(button) -> str:
    return button.text_content().strip()


def _markup(button) -> str:
    return lxml_html.tostring(button, encoding="unicode")


def _author_card(client, actions, monkeypatch):
    monkeypatch.setattr(AuthorCardListView, "cv_card_actions", actions)
    return _card(client, reverse(cv_author.get_router_name("card")))


@pytest.mark.django_db
def test_three_states_on_one_card(author_douglas_adams, monkeypatch):
    card = _author_card(
        _client([AUTHOR_FULL]),
        [
            CardAction(key="detail", label="Details", label_mode="both"),
            CardAction(key="update", label="Edit", label_mode="label"),
            CardAction(key="delete", label="Delete", label_mode="icon"),
        ],
        monkeypatch,
    )

    both = _inline(card, "detail")
    assert len(_icons(both)) == 1
    # the visible span is the only accessible name: the icon is hidden, and nothing duplicates or overrides it
    assert all(i.get("aria-hidden") == "true" for i in _icons(both))
    assert _text(both) == "Details"
    assert both.cssselect("span.visually-hidden") == []
    assert both.get("aria-label") is None
    assert both.get("title") is None
    # the literal space between glyph and text is invisible to the whitespace-normalising goldens
    assert _icons(both)[0].tail == " "

    label = _inline(card, "update")
    assert _icons(label) == []
    assert _text(label) == "Edit"
    assert label.cssselect("span.visually-hidden") == []
    assert label.get("title") is None

    icon = _inline(card, "delete")
    assert len(_icons(icon)) == 1
    (hidden,) = icon.cssselect("span.visually-hidden")
    assert hidden.text_content().strip() == "Delete"
    assert icon.get("title") == "Delete"


@pytest.mark.django_db
def test_no_label_still_means_icon_only(author_douglas_adams, monkeypatch):
    client = _client([AUTHOR_FULL])
    legacy = _inline(
        _author_card(client, [CardAction(key="delete", label="Delete", no_label=True)], monkeypatch), "delete"
    )
    explicit = _inline(
        _author_card(client, [CardAction(key="delete", label="Delete", label_mode="icon")], monkeypatch), "delete"
    )

    assert len(_icons(legacy)) == 1
    assert legacy.cssselect("span.visually-hidden")[0].text_content().strip() == "Delete"
    assert legacy.get("title") == "Delete"
    assert _markup(legacy) == _markup(explicit)


@pytest.mark.django_db
def test_view_default_applies_and_action_overrides_it(author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorCardListView, "cv_card_action_label_mode", "label")
    card = _author_card(
        _client([AUTHOR_FULL]),
        [
            CardAction(key="detail", label="Details"),
            CardAction(key="update", label="Edit", label_mode="both"),
        ],
        monkeypatch,
    )

    inherited = _inline(card, "detail")
    assert _icons(inherited) == []
    assert _text(inherited) == "Details"

    override = _inline(card, "update")
    assert len(_icons(override)) == 1
    assert _text(override) == "Edit"


@pytest.mark.django_db
def test_both_without_an_icon_renders_label_only(author_douglas_adams, monkeypatch):
    # ActionView leaves cv_icon_action unset, but pin it so the iconless case is arranged, not inherited
    monkeypatch.setattr(AuthorPingView, "cv_icon_action", None)
    client = _client([AUTHOR_FULL])

    both = _inline(_author_card(client, [CardAction(key="ping", label="Ping", label_mode="both")], monkeypatch), "ping")
    assert _icons(both) == []
    assert _text(both) == "Ping"

    label = _inline(
        _author_card(client, [CardAction(key="ping", label="Ping", label_mode="label")], monkeypatch), "ping"
    )
    assert _markup(both) == _markup(label)


@pytest.mark.django_db
def test_child_name_card_action_resolves_label_mode(publisher_penguin, monkeypatch):
    client = _client([(cv_publisher, ("view",)), (cv_book, ("view",))])
    url = reverse(cv_publisher.get_router_name("card"))

    def books(label_mode):
        action = CardAction(child_name="book", child_key="list", label="Books", label_mode=label_mode)
        monkeypatch.setattr(PublisherCardListView, "cv_card_actions", [action])
        return _inline(_card(client, url), "book")

    # a non-default mode: the child branch has to resolve it, the "both" fallback cannot supply it
    label = books("label")
    assert _icons(label) == []
    assert _text(label) == "Books"

    both = books("both")
    assert len(_icons(both)) == 1
    assert _text(both) == "Books"


@pytest.mark.django_db
def test_disabled_card_action_in_both_mode(author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorUpdateView, "cv_inaccessible_actions", "disable")
    card = _author_card(
        _client([AUTHOR_VIEW_ONLY]), [CardAction(key="update", label="Edit", label_mode="both")], monkeypatch
    )

    button = _inline(card, "update")
    assert button.tag == "button"
    assert button.get("disabled") is not None
    assert button.get("data-cv-disabled") == "permission"
    assert button.get("href") is None
    assert len(_icons(button)) == 1
    assert _text(button) == "Edit"


@pytest.mark.django_db
def test_post_only_card_action_in_both_mode(author_douglas_adams, monkeypatch):
    card = _author_card(_client([AUTHOR_FULL]), [CardAction(key="up", label="Up", label_mode="both")], monkeypatch)

    button = _inline(card, "up")
    assert button.tag == "button"
    assert button.get("data-cv-action") == "submit-form"
    assert button.get("href") is None
    assert len(_icons(button)) == 1
    assert _text(button) == "Up"


@pytest.mark.django_db
def test_menu_item_ignores_label_mode(author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorCardListView, "cv_card_actions_inline", ["detail"])
    card = _author_card(
        _client([AUTHOR_FULL]),
        [
            CardAction(key="detail", label="Details"),
            CardAction(key="delete", label="Delete", label_mode="icon"),
        ],
        monkeypatch,
    )

    (item,) = card.cssselect(".dropdown-item")
    assert item.get("cv-key") == "delete"
    assert len(_icons(item)) == 1
    assert _text(item) == "Delete"
    assert item.cssselect("span.visually-hidden") == []
    assert item.get("title") is None
