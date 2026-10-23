"""#261: button containers as <ul>/<li> lists, and a lone item rendered bare."""

import pytest
from django.contrib.auth.models import User
from django.template import Context, Template
from django.test import Client, override_settings
from django.urls import reverse
from lxml import html as lxml_html

from crud_views.lib.view import CardAction
from tests.lib.helper.user import user_viewset_permission
from tests.test1.app.views import AuthorCardListView, AuthorDetailView, AuthorListView, cv_author

CONTAINER_TAG = {"context": "fieldset", "list": "fieldset", "card": "div"}
CONTAINER_CLASS = {"context": "btn-group btn-group-lg", "list": "btn-group btn-group-xs", "card": "d-flex gap-2"}


def _list_keys(loc, list_class="btn-list", item_class="btn-item"):
    return {f"{loc}:container-list": list_class, f"{loc}:container-item": item_class}


def _bare(loc):
    return {f"{loc}:container-single": "bare"}


@pytest.fixture
def client_full(db):
    user = User.objects.create_user(username="container_list_261", password="pw")
    for perm in ("view", "add", "change", "delete"):
        user_viewset_permission(user, cv_author, perm)
    client = Client()
    client.force_login(user)
    return client


def _context_actions(monkeypatch, actions, inline=None):
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions", actions)
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_inline", inline)


def _list_actions(monkeypatch, actions, inline=None):
    monkeypatch.setattr(AuthorListView, "cv_list_actions", actions)
    monkeypatch.setattr(AuthorListView, "cv_list_actions_inline", inline)


def _card_actions(monkeypatch, keys, inline=None):
    monkeypatch.setattr(AuthorCardListView, "cv_card_actions", [CardAction(key=key) for key in keys])
    monkeypatch.setattr(AuthorCardListView, "cv_card_actions_inline", inline)


def _setup(loc, monkeypatch, count):
    """``count`` inline actions at ``loc``; returns the URL of the page that renders them."""
    if loc == "context":
        _context_actions(monkeypatch, ["home", "update", "delete"][:count])
        return "detail"
    if loc == "list":
        _list_actions(monkeypatch, ["detail", "update", "delete"][:count])
        return "list"
    _card_actions(monkeypatch, ["detail", "update", "delete"][:count])
    return "card"


def _page(client, view, author=None):
    kwargs = {"pk": author.pk} if view == "detail" else {}
    resp = client.get(reverse(cv_author.get_router_name(view), kwargs=kwargs))
    assert resp.status_code == 200
    return lxml_html.fromstring(resp.content)


def _containers(doc, loc):
    return doc.xpath(f"//*[@cv-{loc}-container]")


@pytest.mark.django_db
@pytest.mark.parametrize("loc", ["context", "list", "card"])
def test_list_markup(client_full, author_douglas_adams, monkeypatch, loc):
    view = _setup(loc, monkeypatch, 2)
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES=_list_keys(loc)):
        doc = _page(client_full, view, author_douglas_adams)
    (container,) = _containers(doc, loc)
    assert container.tag == CONTAINER_TAG[loc]
    assert container.get("class") == CONTAINER_CLASS[loc]
    assert container.get(f"cv-{loc}-container") == "true"
    (ul,) = container
    assert ul.tag == "ul" and ul.get("class") == "btn-list"
    assert [li.tag for li in ul] == ["li", "li"]
    for li in ul:
        assert li.get("class") == "btn-item"
        (button,) = li
        assert button.get("cv-key")


@pytest.mark.django_db
def test_list_menu_gets_own_li(client_full, author_douglas_adams, monkeypatch):
    _context_actions(monkeypatch, ["home", "detail", "update"], inline=["update"])
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES=_list_keys("context")):
        doc = _page(client_full, "detail", author_douglas_adams)
    (ul,) = _containers(doc, "context")[0]
    first, second = ul
    assert first[0].get("cv-key") == "update"
    assert second.cssselect(".cv-menu-toggle")


@pytest.mark.django_db
def test_list_no_menu_no_empty_li(client_full, author_douglas_adams, monkeypatch):
    _list_actions(monkeypatch, ["detail", "update"])
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES=_list_keys("list")):
        doc = _page(client_full, "list")
    (ul,) = _containers(doc, "list")[0]
    assert len(ul) == 2
    assert all(len(li) == 1 for li in ul)


@pytest.mark.django_db
def test_list_empty_class_renders_bare_ul(client_full, author_douglas_adams, monkeypatch):
    _list_actions(monkeypatch, ["detail", "update"])
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES=_list_keys("list", list_class="", item_class="")):
        doc = _page(client_full, "list")
    (ul,) = _containers(doc, "list")[0]
    assert ul.tag == "ul" and ul.get("class") is None
    assert all(li.get("class") is None for li in ul)


@pytest.mark.django_db
@pytest.mark.parametrize("loc", ["context", "list", "card"])
def test_bare_single_button(client_full, author_douglas_adams, monkeypatch, loc):
    view = _setup(loc, monkeypatch, 1)
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES=_bare(loc)):
        doc = _page(client_full, view, author_douglas_adams)
    assert _containers(doc, loc) == []
    key = {"context": "list", "list": "detail", "card": "detail"}[loc]  # the "home" button carries cv-key="list"
    buttons = doc.xpath(f"//*[@cv-key='{key}' and contains(@class, 'btn')]")
    assert buttons
    if loc == "list":
        assert buttons[0].getparent().tag == "td"


@pytest.mark.django_db
def test_bare_one_button_plus_menu_keeps_container(client_full, author_douglas_adams, monkeypatch):
    _context_actions(monkeypatch, ["home", "update"], inline=["update"])
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES=_bare("context")):
        doc = _page(client_full, "detail", author_douglas_adams)
    (container,) = _containers(doc, "context")
    assert container.cssselect(".cv-menu-toggle")


@pytest.mark.django_db
def test_bare_only_menu(client_full, author_douglas_adams, monkeypatch):
    _list_actions(monkeypatch, ["detail", "update"], inline=[])
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES=_bare("list")):
        doc = _page(client_full, "list")
    assert _containers(doc, "list") == []
    assert doc.cssselect("td .cv-menu-toggle")


@pytest.mark.django_db
def test_bare_ignores_hidden_action(client_user_author_view, author_douglas_adams, monkeypatch):
    _context_actions(monkeypatch, ["detail", "update"])
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES=_bare("context")):
        doc = _page(client_user_author_view, "detail", author_douglas_adams)
    assert _containers(doc, "context") == []
    assert doc.xpath("//*[@cv-key='detail' and contains(@class, 'btn')]")
    assert not doc.xpath("//*[@cv-key='update']")


@pytest.mark.django_db
def test_bare_wins_over_list(client_full, author_douglas_adams, monkeypatch):
    _list_actions(monkeypatch, ["detail"])
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={**_list_keys("list"), **_bare("list")}):
        doc = _page(client_full, "list")
    assert _containers(doc, "list") == []
    assert not doc.cssselect("td ul.btn-list")


@pytest.mark.django_db
def test_single_container_mode_keeps_container(client_full, author_douglas_adams, monkeypatch):
    _list_actions(monkeypatch, ["detail"])
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES=_list_keys("list")):
        doc = _page(client_full, "list")
    (container,) = _containers(doc, "list")
    (ul,) = container
    assert len(ul) == 1


@pytest.mark.django_db
def test_standalone_context_button_never_li(client_full, author_douglas_adams):
    resp = client_full.get(reverse(cv_author.get_router_name("detail"), kwargs={"pk": author_douglas_adams.pk}))
    view, request = resp.context["view"], resp.context["request"]
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES=_list_keys("context")):
        out = Template("{% load crud_views %}{% cv_context_button 'update' %}").render(
            Context({"view": view, "request": request})
        )
    assert 'cv-key="update"' in out
    assert "<li" not in out
