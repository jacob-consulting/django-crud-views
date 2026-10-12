"""#174: overflow menu in the context toolbar."""

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from lxml import html as lxml_html

from tests.lib.helper.user import user_viewset_permission
from tests.test1.app.views import (
    AuthorDeleteView,
    AuthorDetailView,
    AuthorUpdateView,
    PublisherListView,
    cv_author,
    cv_publisher,
)


@pytest.fixture
def client_full(db):
    user = User.objects.create_user(username="toolbar_full_174", password="pw")
    for perm in ("view", "add", "change", "delete"):
        user_viewset_permission(user, cv_author, perm)
    client = Client()
    client.force_login(user)
    return client


def _toolbar(client, url):
    resp = client.get(url)
    assert resp.status_code == 200
    return lxml_html.fromstring(resp.content).xpath("//fieldset[@cv-context-container]")[0]


def _detail_url(author):
    return reverse(cv_author.get_router_name("detail"), kwargs={"pk": author.pk})


@pytest.mark.django_db
def test_active_item_in_menu(client_full, author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions", ["home", "detail", "update", "delete"])
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_inline", ["update"])
    toolbar = _toolbar(client_full, _detail_url(author_douglas_adams))
    assert [el.get("cv-key") for el in toolbar.xpath("./*[@cv-key]")] == ["update"]
    toggle = toolbar.cssselect(".cv-menu-toggle")[0]
    assert "btn-lg" in toggle.get("class")
    assert toggle.get("data-bs-popper-config") is None
    detail = toolbar.cssselect('.dropdown-item[cv-key="detail"]')[0]
    assert "active" in detail.get("class").split()
    assert detail.get("aria-current") == "page"
    assert detail.get("title")  # cv_action_label as title
    home = toolbar.cssselect('.dropdown-item[cv-key="list"]')[0]
    assert home.get("aria-current") is None


@pytest.mark.django_db
def test_active_item_inline_keeps_active_class(client_full, author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorUpdateView, "cv_context_actions", ["home", "detail", "update"])
    monkeypatch.setattr(AuthorUpdateView, "cv_context_actions_inline", ["update"])
    url = reverse(cv_author.get_router_name("update"), kwargs={"pk": author_douglas_adams.pk})
    toolbar = _toolbar(client_full, url)
    update = toolbar.xpath('./a[@cv-key="update"]')[0]
    assert "active" in update.get("class").split()


@pytest.mark.django_db
def test_disabled_item(client_user_author_view, author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions", ["home", "detail", "delete"])
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_inline", ["home"])
    monkeypatch.setattr(AuthorDeleteView, "cv_inaccessible_actions", "disable")
    toolbar = _toolbar(client_user_author_view, _detail_url(author_douglas_adams))
    delete = toolbar.cssselect('.dropdown-item[cv-key="delete"]')[0]
    assert delete.tag == "button"
    assert delete.get("disabled") is not None
    assert delete.get("data-cv-disabled") == "permission"
    assert delete.get("href") is None


@pytest.mark.django_db
def test_filter_toggle_never_folded(client_user_publisher_view, publisher_penguin, monkeypatch):
    monkeypatch.setattr(PublisherListView, "cv_context_actions_inline", [])
    toolbar = _toolbar(client_user_publisher_view, reverse(cv_publisher.get_router_name("list")))
    assert toolbar.xpath('./button[@id="cv-filter-toggle"]')
    assert not toolbar.cssselect('.dropdown-menu [cv-key="filter"]')


@pytest.mark.django_db
def test_custom_template_button_never_folded(client_full, author_douglas_adams, monkeypatch):
    from crud_views.lib.view import ContextButton

    custom = ContextButton(
        key="edit_big",
        key_target="update",
        template_code='<a href="{{ cv_url }}" class="cv-big" cv-key="{{ cv_key }}">Big</a>',
    )
    monkeypatch.setattr(AuthorDetailView, "cv_context_buttons", [custom])
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions", ["detail", "edit_big"])
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_inline", [])
    toolbar = _toolbar(client_full, _detail_url(author_douglas_adams))
    assert toolbar.xpath('./a[contains(@class, "cv-big")]')
    assert [i.get("cv-key") for i in toolbar.cssselect(".dropdown-item")] == ["detail"]


@pytest.mark.django_db
def test_modal_item(client_full, author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions", ["detail", "delete"])
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_inline", ["detail"])
    monkeypatch.setattr(AuthorDeleteView, "cv_modal", True)
    toolbar = _toolbar(client_full, _detail_url(author_douglas_adams))
    delete = toolbar.cssselect('.dropdown-item[cv-key="delete"]')[0]
    assert delete.get("data-cv-modal") == "true"
