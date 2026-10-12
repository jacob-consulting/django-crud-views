"""#174: with every inline value None, the action containers render exactly the pre-#174 HTML.

Golden files were captured from main before the container templates changed. Regenerate ONLY when a change to the
default (None) markup is intended: CV_UPDATE_GOLDEN=1 pytest tests/test1/test_action_menus_golden.py
"""

import os
import re
import uuid
from pathlib import Path

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from lxml import html as lxml_html

from crud_views.lib.view import CardAction
from tests.lib.helper.user import user_viewset_permission
from tests.test1.app.models import Author, Publisher
from tests.test1.app.views import (
    AuthorCardListView,
    AuthorDeleteView,
    AuthorListView,
    AuthorPingView,
    AuthorUpdateView,
    AuthorUpView,
    cv_author,
    cv_book,
    cv_publisher,
)

GOLDEN_DIR = Path(__file__).parent / "golden" / "action_menus"
AUTHOR_PK = uuid.UUID("00000000-0000-4000-8000-000000000174")
PUBLISHER_PK = 174
LIST_ACTIONS = ["detail", "update", "delete", "up", "down", "ping"]


def _norm(markup: str) -> str:
    markup = re.sub(r'name="csrfmiddlewaretoken" value="[^"]*"', 'name="csrfmiddlewaretoken" value="CSRF"', markup)
    markup = re.sub(r">\s+<", "><", markup)
    return re.sub(r"\s+", " ", markup).strip()


def _client(grants) -> Client:
    user = User.objects.create_user(username=f"golden_174_{uuid.uuid4().hex[:8]}", password="pw")
    for viewset, perms in grants:
        for perm in perms:
            user_viewset_permission(user, viewset, perm)
    client = Client()
    client.force_login(user)
    return client


def _fragments(client, url, xpath) -> str:
    resp = client.get(url)
    assert resp.status_code == 200
    doc = lxml_html.fromstring(resp.content)
    nodes = doc.xpath(xpath)
    assert nodes, f"no node for {xpath} at {url}"
    return "\n".join(_norm(lxml_html.tostring(n, encoding="unicode")) for n in nodes)


def _compare(name: str, actual: str):
    path = GOLDEN_DIR / f"{name}.html"
    if os.environ.get("CV_UPDATE_GOLDEN") == "1":
        GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(actual + "\n")
    assert actual == path.read_text().strip()


LIST_TD = "//td[.//fieldset[@cv-list-container]]"
TOOLBAR = "//fieldset[@cv-context-container]"
CARD = "//div[contains(@class, 'card') and contains(@class, 'mb-3')]"
FULL = (cv_author, ("view", "add", "change", "delete"))
VIEW_ONLY = (cv_author, ("view",))


@pytest.fixture
def objects(db):
    Author.objects.create(id=AUTHOR_PK, first_name="Douglas", last_name="Adams")
    Publisher.objects.create(id=PUBLISHER_PK, name="Penguin")


def _ping_labels(monkeypatch):
    # AuthorPingView renders no label snippet of its own; rows and cards need one.
    monkeypatch.setattr(AuthorPingView, "cv_action_label_template_code", "Ping")
    monkeypatch.setattr(AuthorPingView, "cv_action_short_label_template_code", "Ping")


@pytest.fixture
def list_actions(monkeypatch):
    monkeypatch.setattr(AuthorListView, "cv_list_actions", LIST_ACTIONS)
    monkeypatch.setattr(AuthorDeleteView, "cv_modal", True)
    _ping_labels(monkeypatch)


@pytest.mark.django_db
def test_list_rows_full(objects, list_actions):
    _compare("list_full", _fragments(_client([FULL]), reverse(cv_author.get_router_name("list")), LIST_TD))


@pytest.mark.django_db
def test_list_rows_disabled(objects, list_actions, monkeypatch):
    monkeypatch.setattr(AuthorUpdateView, "cv_inaccessible_actions", "disable")
    monkeypatch.setattr(AuthorUpView, "cv_inaccessible_actions", "disable")
    _compare("list_disabled", _fragments(_client([VIEW_ONLY]), reverse(cv_author.get_router_name("list")), LIST_TD))


@pytest.mark.django_db
def test_toolbar_detail_full(objects):
    url = reverse(cv_author.get_router_name("detail"), kwargs={"pk": AUTHOR_PK})
    _compare("toolbar_detail_full", _fragments(_client([FULL]), url, TOOLBAR))


@pytest.mark.django_db
def test_toolbar_detail_disabled(objects, monkeypatch):
    monkeypatch.setattr(AuthorDeleteView, "cv_inaccessible_actions", "disable")
    url = reverse(cv_author.get_router_name("detail"), kwargs={"pk": AUTHOR_PK})
    _compare("toolbar_detail_disabled", _fragments(_client([VIEW_ONLY]), url, TOOLBAR))


@pytest.mark.django_db
def test_toolbar_list_with_filter(objects):
    url = reverse(cv_publisher.get_router_name("list"))
    _compare("toolbar_publisher_list", _fragments(_client([(cv_publisher, ("view", "add"))]), url, TOOLBAR))


@pytest.mark.django_db
def test_cards_author_full(objects, monkeypatch):
    _ping_labels(monkeypatch)
    monkeypatch.setattr(
        AuthorCardListView,
        "cv_card_actions",
        [*AuthorCardListView.cv_card_actions, CardAction(key="ping", label="Ping")],
    )
    _compare("cards_author_full", _fragments(_client([FULL]), reverse(cv_author.get_router_name("card")), CARD))


@pytest.mark.django_db
def test_cards_author_disabled(objects, monkeypatch):
    monkeypatch.setattr(AuthorUpdateView, "cv_inaccessible_actions", "disable")
    url = reverse(cv_author.get_router_name("card"))
    _compare("cards_author_disabled", _fragments(_client([VIEW_ONLY]), url, CARD))


@pytest.mark.django_db
def test_cards_publisher_child(objects):
    client = _client([(cv_publisher, ("view",)), (cv_book, ("view",))])
    _compare("cards_publisher_child", _fragments(client, reverse(cv_publisher.get_router_name("card")), CARD))
