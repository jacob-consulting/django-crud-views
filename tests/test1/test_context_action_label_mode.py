"""#269: cv_context_action_label_mode — the target view's label mode in the context toolbar."""

import pytest
from django.urls import reverse
from lxml import html as lxml_html

from crud_views.lib.settings import crud_views_settings
from crud_views.lib.view import ContextButton
from tests.test1.app.views import (
    AuthorDeleteView,
    AuthorDetailView,
    AuthorListView,
    AuthorUpdateView,
    PublisherListView,
    cv_author,
    cv_book,
    cv_publisher,
)
from tests.test1.test_action_label_mode_render import (
    AUTHOR_FULL,
    _button,
    _client,
    _detail_url,
    _detail_view,
    _render,
    _rows,
    _toolbar,
)
from tests.test1.test_context_button_label_mode import _is_text_only, _messages, _target, _w292, _with_viewset_buttons


def _set_target(monkeypatch, view, mode):
    monkeypatch.setattr(view, "cv_context_action_label_mode", mode)


def _has_icon_and_text(el) -> bool:
    return bool(el.xpath("./*[@aria-hidden='true']")) and bool(el.xpath("./span[not(@class)]"))


# resolution: view map naming the key -> button -> resolved map naming the key -> target view -> "icon"


def test_target_default_used_when_nothing_else_names_key():
    assert AuthorDetailView.cv_get_action_label_mode("context", "update", target_default="label") == "label"
    assert AuthorDetailView.cv_get_action_label_mode("context", "update") == "icon"


def test_target_default_ignored_for_list():
    assert AuthorListView.cv_get_action_label_mode("list", "update", target_default="label") == "icon"


def test_view_map_naming_key_beats_target(monkeypatch):
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_label_mode", {"update": "both"})
    assert AuthorDetailView.cv_get_action_label_mode("context", "update", target_default="label") == "both"


def test_button_mode_beats_target(monkeypatch):
    _with_viewset_buttons(monkeypatch, ContextButton(key="update", key_target="update", label_mode="both"))
    assert AuthorDetailView.cv_get_action_label_mode("context", "update", target_default="label") == "both"


def test_viewset_map_beats_target(monkeypatch):
    monkeypatch.setattr(cv_author, "context_actions_label_mode", {"update": "both"})
    assert AuthorDetailView.cv_get_action_label_mode("context", "update", target_default="label") == "both"


def test_setting_beats_target(monkeypatch):
    monkeypatch.setattr(crud_views_settings, "context_actions_label_mode", {"update": "both"})
    assert AuthorDetailView.cv_get_action_label_mode("context", "update", target_default="label") == "both"


def test_view_map_without_key_yields_to_target(monkeypatch):
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_label_mode", {"detail": "both"})
    assert AuthorDetailView.cv_get_action_label_mode("context", "update", target_default="label") == "label"


# action data


@pytest.mark.django_db
def test_cv_get_dict_carries_target_mode(author_douglas_adams, monkeypatch):
    _set_target(monkeypatch, AuthorUpdateView, "label")
    view, request = _detail_view(_client([AUTHOR_FULL]), author_douglas_adams)
    data = view.cv_get_context("update", author_douglas_adams, request.user, location="context")
    assert data["cv_context_label_mode"] == "label"
    assert data["cv_label_mode"] == "label"


# rendering


@pytest.mark.django_db
def test_toolbar_follows_target_mode(author_douglas_adams, monkeypatch):
    _set_target(monkeypatch, AuthorUpdateView, "label")
    _set_target(monkeypatch, AuthorDeleteView, "both")
    toolbar = _toolbar(_client([AUTHOR_FULL]), _detail_url(author_douglas_adams))
    assert _is_text_only(_button(toolbar, "update"))
    assert _has_icon_and_text(_button(toolbar, "delete"))
    assert _button(toolbar, "detail").get("title")  # still icon-only


@pytest.mark.django_db
def test_target_mode_does_not_reach_rows(author_douglas_adams, monkeypatch):
    _set_target(monkeypatch, AuthorDetailView, "label")
    (td,) = _rows(_client([AUTHOR_FULL]))
    detail = _button(td.cssselect("fieldset")[0], "detail")
    assert detail.get("title")
    assert detail.xpath("./span[contains(@class, 'visually-hidden')]")


@pytest.mark.django_db
@pytest.mark.parametrize(("button_mode", "text_only"), [(None, True), ("icon", False)])
def test_registered_button_follows_target(author_douglas_adams, monkeypatch, button_mode, text_only):
    _set_target(monkeypatch, AuthorUpdateView, "label")
    _with_viewset_buttons(monkeypatch, ContextButton(key="edit", key_target="update", label_mode=button_mode))
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions", ["edit"])
    toolbar = _toolbar(_client([AUTHOR_FULL]), _detail_url(author_douglas_adams))
    (el,) = toolbar.xpath("./*[@cv-key]")
    assert _is_text_only(el) is text_only


@pytest.mark.django_db
def test_home_button_follows_list_view(author_douglas_adams, monkeypatch):
    _set_target(monkeypatch, AuthorListView, "label")
    toolbar = _toolbar(_client([AUTHOR_FULL]), _detail_url(author_douglas_adams))
    (home,) = toolbar.xpath("./*[@cv-key='list']")
    assert _is_text_only(home)


@pytest.mark.django_db
def test_parent_button_follows_parent_list_view(publisher_penguin, monkeypatch):
    _set_target(monkeypatch, PublisherListView, "label")
    client = _client([(cv_publisher, ("view",)), (cv_book, ("view", "add"))])
    url = reverse(cv_book.get_router_name("list"), kwargs={"publisher_pk": publisher_penguin.pk})
    toolbar = _toolbar(client, url)
    (parent,) = toolbar.xpath(f"./*[@href='{reverse(cv_publisher.get_router_name('list'))}']")
    assert _is_text_only(parent)


@pytest.mark.django_db
def test_cv_context_button_tag_follows_target(author_douglas_adams, monkeypatch):
    _set_target(monkeypatch, AuthorUpdateView, "label")
    view, request = _detail_view(_client([AUTHOR_FULL]), author_douglas_adams)
    (el,) = lxml_html.fragments_fromstring(_render(view, request, '{% cv_context_button "update" %}'))
    assert _is_text_only(el)


@pytest.mark.django_db
def test_menu_folded_key_keeps_icon_and_short_label(author_douglas_adams, monkeypatch):
    # a menu item renders icon and short label in every mode; only its title follows the mode, as documented (#216)
    _set_target(monkeypatch, AuthorUpdateView, "label")
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_inline", ["detail"])
    resp = _client([AUTHOR_FULL]).get(_detail_url(author_douglas_adams))
    (item,) = lxml_html.fromstring(resp.content).xpath("//*[contains(@class, 'dropdown-item')][@cv-key='update']")
    assert item.xpath("./i[@aria-hidden='true']")
    assert item.text_content().strip() == "Update"
    assert item.get("title") is None


# checks


def test_e210_invalid_target_attribute(monkeypatch):
    _set_target(monkeypatch, AuthorUpdateView, "text")
    (msg,) = _messages(AuthorUpdateView.checks(), "viewset.E210")
    assert "cv_context_action_label_mode" in msg
    assert "'text'" in msg


def test_e210_dict_on_target_attribute_names_the_map(monkeypatch):
    _set_target(monkeypatch, AuthorUpdateView, {"update": "label"})
    (msg,) = _messages(AuthorUpdateView.checks(), "viewset.E210")
    assert "cv_context_actions_label_mode" in msg


@pytest.mark.parametrize("mode", [None, "label", "icon", "both"])
def test_no_e210_for_valid_or_unset_target_attribute(monkeypatch, mode):
    _set_target(monkeypatch, AuthorUpdateView, mode)
    assert _messages(AuthorUpdateView.checks(), "viewset.E210") == []


def test_e211_string_on_map_names_target_attribute(monkeypatch):
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_label_mode", "label")
    (msg,) = _messages(AuthorDetailView.checks(), "viewset.E211")
    assert "cv_context_action_label_mode" in msg


@pytest.mark.parametrize("mode", ["label", "both"])
def test_w292_silent_with_target_label_mode(monkeypatch, mode):
    monkeypatch.setattr(_target("update"), "cv_icon_action", None)
    _set_target(monkeypatch, _target("update"), mode)
    assert _w292() == []


def test_w292_explicit_target_icon_still_warns(monkeypatch):
    monkeypatch.setattr(_target("update"), "cv_icon_action", None)
    _set_target(monkeypatch, _target("update"), "icon")
    (msg,) = _w292()
    assert "'update'" in msg


def test_w292_registered_button_follows_target(monkeypatch):
    monkeypatch.setattr(_target("update"), "cv_icon_action", None)
    _set_target(monkeypatch, _target("update"), "label")
    _with_viewset_buttons(monkeypatch, ContextButton(key="edit", key_target="update"))
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions", ["edit"])
    assert _w292() == []


def test_w292_invalid_target_attribute_does_not_crash(monkeypatch):
    monkeypatch.setattr(_target("update"), "cv_icon_action", None)
    _set_target(monkeypatch, _target("update"), "text")
    (msg,) = _w292()  # a non-mode value counts as unset; E210 reports it on the target view
    assert "'update'" in msg
