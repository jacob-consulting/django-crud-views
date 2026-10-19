"""Task 4: core views and templates render icons through the registry."""

from pathlib import Path

import pytest
from django.contrib.auth.models import User
from django.test import Client, override_settings
from django.urls import reverse
from lxml import html as lxml_html

from tests.lib.helper.user import user_viewset_permission
from tests.test1.app.views import AuthorListView, cv_author


@pytest.fixture
def client_full(db):
    user = User.objects.create_user(username="icons_full", password="pw")
    for perm in ("view", "add", "change", "delete"):
        user_viewset_permission(user, cv_author, perm)
    client = Client()
    client.force_login(user)
    return client


def _list(client) -> str:
    resp = client.get(reverse(cv_author.get_router_name("list")))
    assert resp.status_code == 200
    return resp.content.decode()


@pytest.mark.django_db
def test_detail_action_default_icon(client_full, author_douglas_adams):
    html = _list(client_full)
    assert '<i class="fa-regular fa-eye" aria-hidden="true"></i>' in html


@pytest.mark.django_db
def test_detail_action_icon_override(client_full, author_douglas_adams):
    with override_settings(CRUD_VIEWS_ICONS={"detail": "bi:search"}):
        html = _list(client_full)
    assert "bi bi-search" in html
    assert "fa-eye" not in html


@pytest.mark.django_db
def test_actions_menu_toggle_icon(client_full, author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorListView, "cv_list_actions_inline", ["detail"])
    doc = lxml_html.fromstring(_list(client_full))
    toggle = doc.cssselect("button.cv-menu-toggle")[0]
    assert toggle.cssselect("i")[0].get("class") == "fa-solid fa-ellipsis"


@pytest.mark.django_db
def test_menu_item_label_icon_is_fixed_width(client_full, author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorListView, "cv_list_actions_inline", ["detail"])
    html = _list(client_full)
    assert "cv-icon-fw" in html
    assert "fa-fw" not in html


def test_no_hardcoded_icon_classes_in_templates_and_js():
    src = Path(__file__).resolve().parents[2] / "src"
    files = list(src.glob("*/templates/**/*.html")) + list((src / "crud_views/static/crud_views/js").rglob("*.js"))
    assert files
    offenders = [
        str(f.relative_to(src))
        for f in files
        if any(token in f.read_text(encoding="utf-8") for token in ('"fa-', "fa-", '"bi-', "bi-"))
    ]
    assert offenders == []


@pytest.mark.django_db
def test_card_no_label_has_visually_hidden_label(client_full, author_douglas_adams):
    resp = client_full.get(reverse(cv_author.get_router_name("card")))
    assert resp.status_code == 200
    doc = lxml_html.fromstring(resp.content)
    (card,) = doc.xpath("//div[contains(@class, 'card') and contains(@class, 'mb-3')]")
    delete = next(a for a in card.cssselect("a.btn") if a.get("title"))
    assert delete.cssselect("i[aria-hidden='true']")
    hidden = delete.cssselect("span.visually-hidden")
    assert hidden and hidden[0].text_content().strip() == delete.get("title")


@pytest.mark.django_db
def test_filter_header_and_toggle_share_the_filter_icon(client_user_publisher_view, cv_publisher, publisher_penguin):
    with override_settings(CRUD_VIEWS_ICONS={"filter": "fas:magnifying-glass"}):
        resp = client_user_publisher_view.get("/publisher/")
    assert resp.status_code == 200
    doc = lxml_html.fromstring(resp.content)
    header = doc.cssselect("#filter-collapse .card-header i")
    toggle = doc.cssselect("#cv-filter-toggle [data-cv-filter-icon='open'] i")
    assert [i.get("class") for i in header] == ["fa-solid fa-magnifying-glass"]
    assert [i.get("class") for i in toggle] == ["fa-solid fa-magnifying-glass"]
    assert doc.xpath("//i[@class='fa-solid fa-filter']") == []  # no second source of the open icon


def test_cv_filter_icon_tag_and_hook_removed():
    from django.template import Template, TemplateSyntaxError

    from crud_views.lib.views import CardListView, ListView

    assert not hasattr(ListView, "cv_get_filter_icon")
    assert not hasattr(CardListView, "cv_get_filter_icon")
    with pytest.raises(TemplateSyntaxError):
        Template("{% load crud_views %}{% cv_filter_icon %}")
