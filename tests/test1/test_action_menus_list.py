"""#174: overflow menu in list rows."""

import pytest
from django.contrib.auth.models import User
from django.test import Client, override_settings
from django.urls import reverse
from django.utils import translation
from lxml import html as lxml_html

from crud_views.lib.settings import crud_views_settings
from tests.lib.helper.user import user_viewset_permission
from tests.test1.app.views import AuthorDeleteView, AuthorListView, AuthorUpdateView, cv_author


@pytest.fixture
def client_full(db):
    user = User.objects.create_user(username="menu_full_174", password="pw")
    for perm in ("view", "add", "change", "delete"):
        user_viewset_permission(user, cv_author, perm)
    client = Client()
    client.force_login(user)
    return client


@pytest.fixture
def menu_list(monkeypatch):
    monkeypatch.setattr(AuthorListView, "cv_list_actions", ["detail", "update", "delete", "up", "ping"])
    monkeypatch.setattr(AuthorListView, "cv_list_actions_inline", ["detail"])


def _rows(client):
    resp = client.get(reverse(cv_author.get_router_name("list")))
    assert resp.status_code == 200
    doc = lxml_html.fromstring(resp.content)
    return doc.xpath("//td[.//fieldset[@cv-list-container]]")


@pytest.mark.django_db
def test_inline_and_menu(client_full, author_douglas_adams, menu_list):
    (td,) = _rows(client_full)
    fieldset = td.cssselect("fieldset")[0]
    inline = [el.get("cv-key") for el in fieldset.xpath("./*[@cv-key]")]
    assert inline == ["detail"]
    toggle = fieldset.cssselect("button.cv-menu-toggle")[0]
    assert toggle.get("data-bs-toggle") == "dropdown"
    assert "dropdown-toggle" in toggle.get("class")
    assert toggle.get("aria-expanded") == "false"
    assert toggle.get("aria-label") == "More actions"
    assert toggle.get("data-bs-popper-config") == '{"strategy":"fixed"}'
    assert toggle.cssselect("i")[0].get("class") == crud_views_settings.actions_menu_icon
    items = fieldset.cssselect("ul.dropdown-menu.dropdown-menu-end .dropdown-item")
    assert [i.get("cv-key") for i in items] == ["update", "delete", "up", "ping"]
    # wrapper is a nested button group so borders join the inline buttons
    assert toggle.getparent().get("class") == "btn-group"


@pytest.mark.django_db
def test_menu_items_have_visible_labels_and_fixed_width_icons(client_full, author_douglas_adams, menu_list):
    (td,) = _rows(client_full)
    update = td.cssselect('.dropdown-item[cv-key="update"]')[0]
    assert update.tag == "a"
    assert update.get("href").endswith("/update/")
    assert "fa-fw" in update.cssselect("i")[0].get("class")
    assert update.text_content().strip() != ""


@pytest.mark.django_db
def test_post_item_targets_hidden_form(client_full, author_douglas_adams, menu_list):
    (td,) = _rows(client_full)
    ping = td.cssselect('.dropdown-item[cv-key="ping"]')[0]
    assert ping.tag == "button"
    assert ping.get("data-cv-action") == "submit-form"
    target = ping.get("data-cv-target")
    forms = td.xpath(f'.//form[@id="{target}"]')
    assert len(forms) == 1
    assert forms[0].getparent().tag == "td"  # outside the menu
    assert forms[0].cssselect('input[name="csrfmiddlewaretoken"]')


@pytest.mark.django_db
def test_two_rows_post_targets_distinct(client_full, author_douglas_adams, author_terry_pratchett, menu_list):
    # Review Focus 5
    targets = []
    for td in _rows(client_full):
        target = td.cssselect('.dropdown-item[cv-key="ping"]')[0].get("data-cv-target")
        assert td.xpath(f'.//form[@id="{target}"]')
        targets.append(target)
    assert len(set(targets)) == 2


@pytest.mark.django_db
def test_modal_item(client_full, author_douglas_adams, menu_list, monkeypatch):
    monkeypatch.setattr(AuthorDeleteView, "cv_modal", True)
    (td,) = _rows(client_full)
    delete = td.cssselect('.dropdown-item[cv-key="delete"]')[0]
    assert delete.get("data-cv-modal") == "true"
    assert delete.get("href")


@pytest.mark.django_db
def test_disabled_item(client_user_author_view, author_douglas_adams, menu_list, monkeypatch):
    monkeypatch.setattr(AuthorUpdateView, "cv_inaccessible_actions", "disable")
    (td,) = _rows(client_user_author_view)
    update = td.cssselect('.dropdown-item[cv-key="update"]')[0]
    assert update.tag == "button"
    assert update.get("disabled") is not None
    assert update.get("data-cv-disabled") == "permission"
    assert update.get("href") is None
    assert update.get("data-cv-action") is None
    assert update.get("data-cv-modal") is None


@pytest.mark.django_db
def test_disabled_post_item_has_no_form(client_user_author_view, author_douglas_adams, menu_list, monkeypatch):
    from tests.test1.app.views import AuthorPingView

    monkeypatch.setattr(AuthorPingView, "cv_inaccessible_actions", "disable")
    (td,) = _rows(client_user_author_view)
    ping = td.cssselect('.dropdown-item[cv-key="ping"]')[0]
    assert ping.tag == "button"
    assert ping.get("disabled") is not None
    assert ping.get("data-cv-action") is None
    assert td.xpath('.//form[starts-with(@id, "cv_form_")]') == []


@pytest.mark.django_db
def test_no_toggle_when_menu_empty(client_user_author_view, author_douglas_adams, menu_list):
    # view-only user, default hide mode: every menu candidate is hidden
    (td,) = _rows(client_user_author_view)
    assert td.cssselect(".cv-menu-toggle") == []
    assert td.cssselect(".dropdown-menu") == []


@pytest.mark.django_db
def test_toggle_shown_when_all_menu_items_disabled(client_user_author_view, author_douglas_adams, monkeypatch):
    monkeypatch.setattr(AuthorListView, "cv_list_actions", ["detail", "update"])
    monkeypatch.setattr(AuthorListView, "cv_list_actions_inline", ["detail"])
    monkeypatch.setattr(AuthorUpdateView, "cv_inaccessible_actions", "disable")
    (td,) = _rows(client_user_author_view)
    assert td.cssselect(".cv-menu-toggle")
    assert td.cssselect('.dropdown-item[cv-key="update"][disabled]')


@pytest.mark.django_db
def test_custom_menu_icon(client_full, author_douglas_adams, menu_list, monkeypatch):
    monkeypatch.setattr(crud_views_settings, "actions_menu_icon", "fa-solid fa-bars")
    (td,) = _rows(client_full)
    assert td.cssselect(".cv-menu-toggle i")[0].get("class") == "fa-solid fa-bars"


@pytest.mark.django_db
@override_settings(LANGUAGES=[("en", "English"), ("de", "German")])
def test_german_label(client_full, author_douglas_adams, menu_list):
    # the test project has no LocaleMiddleware: activate German around the request (as test_i18n.py does)
    with translation.override("de"):
        resp = client_full.get(reverse(cv_author.get_router_name("list")))
    assert 'aria-label="Weitere Aktionen"' in resp.content.decode()


def test_caret_rule_shipped():
    from pathlib import Path

    import crud_views

    css = (Path(crud_views.__file__).parent / "static/crud_views/css/table.css").read_text()
    assert ".cv-menu-toggle.dropdown-toggle::after" in css
