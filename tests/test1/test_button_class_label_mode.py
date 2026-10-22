"""#209: the action leaf and the filter toggle resolve location:variant:mode, falling back to location:variant."""

import uuid

import pytest
from django.contrib.auth.models import User
from django.test import Client, override_settings
from django.urls import reverse
from lxml import html as lxml_html

from crud_views.lib.view import CardAction
from crud_views.lib.view.variant import VARIANTS
from tests.lib.helper.user import user_viewset_permission
from tests.test1.app.views import AuthorCardListView, cv_author

CARD = "//div[contains(@class, 'card') and contains(@class, 'mb-3')]"


def _client(grants) -> Client:
    user = User.objects.create_user(username=f"card_209_{uuid.uuid4().hex[:8]}", password="pw")
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
    (button,) = card.xpath(f'.//*[@cv-card-container]/*[@cv-key="{key}"]')
    return button


@pytest.mark.django_db
def test_card_same_variant_different_modes_get_different_classes(author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorCardListView, "cv_card_actions_inline", ["detail", "update"])
    monkeypatch.setattr(
        AuthorCardListView,
        "cv_card_actions",
        [
            CardAction(key="detail", label="Details", variant="secondary", label_mode="both"),
            CardAction(key="update", label="Edit", variant="secondary", label_mode="icon"),
        ],
    )
    client = _client([(cv_author, ("view", "add", "change", "delete"))])
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"card:secondary:icon": "btn btn-sm btn-icon x-icon"}):
        card = _card(client, reverse(cv_author.get_router_name("card")))
    assert _inline(card, "detail").get("class") == "btn btn-secondary btn-sm"
    assert _inline(card, "update").get("class") == "btn btn-sm btn-icon x-icon"


@pytest.mark.django_db
def test_filter_toggle_resolves_icon_mode(cv_publisher, publisher_penguin):
    client = _client([(cv_publisher, ("view",))])

    def toggle_class() -> str:
        doc = lxml_html.fromstring(client.get("/publisher/").content)
        return doc.cssselect("#cv-filter-toggle")[0].get("class")

    assert toggle_class() == "btn btn-outline-primary btn-lg"
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"context:secondary:icon": "x-icon"}):
        assert toggle_class() == "x-icon"
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"context:secondary:both": "x-both"}):
        assert toggle_class() == "btn btn-outline-primary btn-lg"


@pytest.mark.django_db
def test_list_row_buttons_resolve_icon_mode(cv_publisher, publisher_penguin):
    client = _client([(cv_publisher, ("view", "change", "delete"))])
    keys = {f"list:{v}:icon": "x-list-icon" for v in VARIANTS}
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES=keys):
        doc = lxml_html.fromstring(client.get("/publisher/").content)
    buttons = doc.xpath("//*[@cv-list-container]/*[@cv-key]")
    assert buttons
    assert {b.get("class") for b in buttons} == {"x-list-icon"}
