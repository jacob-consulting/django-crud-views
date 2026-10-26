"""#269: cv_context_action_label_mode — the target view's label mode in the context toolbar."""

import logging

import pytest
from django.test import override_settings
from django.urls import reverse
from lxml import html as lxml_html

from crud_views.lib.settings import crud_views_settings
from crud_views.lib.view import ChildContextButton, ContextButton, SiblingContextButton
from tests.test1.app.views import (
    AuthorDeleteView,
    AuthorDetailView,
    AuthorListView,
    AuthorUpdateView,
    BookListView,
    ContractListView,
    PublisherDetailView,
    PublisherListView,
    cv_author,
    cv_book,
    cv_contract,
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
def test_child_button_follows_child_list_view(publisher_penguin, monkeypatch):
    _set_target(monkeypatch, BookListView, "label")
    monkeypatch.setattr(PublisherDetailView, "cv_context_buttons", [ChildContextButton(key="books", child_name="book")])
    monkeypatch.setattr(PublisherDetailView, "cv_context_actions", ["books"])
    client = _client([(cv_publisher, ("view",)), (cv_book, ("view",))])
    toolbar = _toolbar(client, reverse(cv_publisher.get_router_name("detail"), kwargs={"pk": publisher_penguin.pk}))
    (el,) = toolbar.xpath("./*[@cv-key]")
    assert _is_text_only(el)


@pytest.mark.django_db
def test_sibling_button_follows_sibling_list_view(publisher_penguin, monkeypatch):
    _set_target(monkeypatch, ContractListView, "label")
    button = SiblingContextButton(key="contracts", sibling_name="contract")
    monkeypatch.setattr(BookListView, "cv_context_buttons", [button])
    monkeypatch.setattr(BookListView, "cv_context_actions", ["contracts"])
    client = _client([(cv_publisher, ("view",)), (cv_book, ("view",)), (cv_contract, ("view",))])
    toolbar = _toolbar(client, reverse(cv_book.get_router_name("list"), kwargs={"publisher_pk": publisher_penguin.pk}))
    (el,) = toolbar.xpath("./*[@cv-key]")
    assert _is_text_only(el)


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


# CRUD_VIEWS_LABEL_MODE_DEFAULTS["context"]: the floor after the view map, button, resolved map and target view

BOTH = {"context": "both"}
# ordinary toolbar actions only: the filter toggle renders its own leaf with its own markup, so its resolved modes,
# floor and placements are covered in test_filter_toggle_label_mode.py (#262)
ELIGIBLE = './*[@cv-key][not(@cv-key="filter") and not(@id="cv-filter-toggle")]'
ROUTES = ["list", "card", "create", "detail", "update"]


def _route_url(route, author):
    kwargs = {"pk": author.pk} if route in ("detail", "update") else {}
    return reverse(cv_author.get_router_name(route), kwargs=kwargs)


def _unmapped(monkeypatch):
    """No view map, ViewSet map, setting map, button or target view names an author toolbar key."""
    monkeypatch.setattr(cv_author, "context_actions_label_mode", None)
    monkeypatch.setattr(crud_views_settings, "context_actions_label_mode", {})
    for view in cv_author.get_all_views().values():
        monkeypatch.setattr(view, "cv_context_actions_label_mode", None)
        monkeypatch.setattr(view, "cv_context_action_label_mode", None)
    assert all(button.label_mode is None for button in cv_author.context_buttons)


def _icon_only(el) -> bool:
    return bool(el.get("title")) and bool(el.xpath("./span[contains(@class, 'visually-hidden')]"))


def _icon_and_short_label(el) -> bool:
    spans = el.xpath("./span[not(@class)]")
    return (
        _has_icon_and_text(el)
        and el.get("title") is None
        and el.xpath("./span[contains(@class, 'visually-hidden')]") == []
        and len(spans) == 1
        and bool((spans[0].text or "").strip())
    )


def _bodies(doc, container: str) -> list[bytes]:
    return [lxml_html.tostring(el) for el in doc.xpath(f"//*[@{container}]")]


@pytest.mark.django_db
@pytest.mark.parametrize("route", ROUTES)
def test_context_floor_renders_unmapped_toolbar(author_douglas_adams, monkeypatch, route):
    _unmapped(monkeypatch)
    client = _client([AUTHOR_FULL])
    url = _route_url(route, author_douglas_adams)
    before = _toolbar(client, url).xpath(ELIGIBLE)
    assert before
    assert all(_icon_only(el) for el in before)  # unconfigured: unchanged
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS=BOTH):
        actions = _toolbar(client, url).xpath(ELIGIBLE)
    assert [el.get("cv-key") for el in actions] == [el.get("cv-key") for el in before]
    for el in actions:
        assert _icon_and_short_label(el), lxml_html.tostring(el)


@pytest.mark.django_db
def test_context_floor_does_not_change_rows_or_cards(author_douglas_adams, monkeypatch):
    _unmapped(monkeypatch)
    client = _client([AUTHOR_FULL])
    list_url, card_url = _route_url("list", author_douglas_adams), _route_url("card", author_douglas_adams)

    def pages():
        list_doc = lxml_html.fromstring(client.get(list_url).content)
        card_doc = lxml_html.fromstring(client.get(card_url).content)
        toolbar = card_doc.xpath("//fieldset[@cv-context-container]")[0]
        return _bodies(list_doc, "cv-list-container"), _bodies(card_doc, "cv-card-container"), toolbar

    rows, cards, card_toolbar = pages()
    assert rows
    assert cards
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS=BOTH):
        rows_after, cards_after, card_toolbar_after = pages()
    assert rows_after == rows
    assert cards_after == cards
    # the card page's own toolbar follows the floor
    assert lxml_html.tostring(card_toolbar_after) != lxml_html.tostring(card_toolbar)
    assert all(_icon_and_short_label(el) for el in card_toolbar_after.xpath(ELIGIBLE))


def _floor_case_unmapped(monkeypatch):
    return "update", None


def _floor_case_view_map(monkeypatch):
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_label_mode", {"update": "label"})
    return "update", None


def _floor_case_button(monkeypatch):
    _with_viewset_buttons(monkeypatch, ContextButton(key="edit", key_target="update", label_mode="label"))
    return "edit", None


def _floor_case_viewset_map(monkeypatch):
    monkeypatch.setattr(cv_author, "context_actions_label_mode", {"update": "label"})
    return "update", None


def _floor_case_setting_map(monkeypatch):
    monkeypatch.setattr(crud_views_settings, "context_actions_label_mode", {"update": "label"})
    return "update", None


def _floor_case_target(monkeypatch):
    return "update", "label"


def _floor_case_target_icon(monkeypatch):
    return "update", "icon"  # an explicit "icon" on the target view still beats the floor


def _floor_case_empty_view_map(monkeypatch):
    # an empty view map replaces the ViewSet map whole: the key reaches the floor
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_label_mode", {})
    monkeypatch.setattr(cv_author, "context_actions_label_mode", {"update": "label"})
    return "update", None


def _floor_case_empty_view_map_target(monkeypatch):
    # ... but the target view still comes before the floor
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_label_mode", {})
    monkeypatch.setattr(cv_author, "context_actions_label_mode", {"update": "icon"})
    return "update", "label"


@pytest.mark.parametrize(
    ("case", "expected"),
    [
        (_floor_case_unmapped, "both"),
        (_floor_case_view_map, "label"),
        (_floor_case_button, "label"),
        (_floor_case_viewset_map, "label"),
        (_floor_case_setting_map, "label"),
        (_floor_case_target, "label"),
        (_floor_case_target_icon, "icon"),
        (_floor_case_empty_view_map, "both"),
        (_floor_case_empty_view_map_target, "label"),
    ],
    ids=lambda v: v.__name__.removeprefix("_floor_case_") if callable(v) else v,
)
def test_context_floor_preserves_precedence(monkeypatch, case, expected):
    key, target_default = case(monkeypatch)
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS=BOTH):
        assert AuthorDetailView.cv_get_action_label_mode("context", key, target_default=target_default) == expected


@pytest.mark.parametrize(
    "case",
    [
        _floor_case_view_map,
        _floor_case_button,
        _floor_case_viewset_map,
        _floor_case_setting_map,
        _floor_case_target,
        _floor_case_empty_view_map_target,
    ],
    ids=lambda v: v.__name__.removeprefix("_floor_case_"),
)
@pytest.mark.parametrize("floor", [{"context": "nope"}, None], ids=["bad-mode", "non-dict"])
def test_explicit_context_mode_bypasses_invalid_floor(monkeypatch, caplog, case, floor):
    key, target_default = case(monkeypatch)
    with (
        caplog.at_level(logging.WARNING, logger="crud_views.lib.view.label_mode"),
        override_settings(CRUD_VIEWS_STRICT=True, CRUD_VIEWS_LABEL_MODE_DEFAULTS=floor),
    ):
        assert AuthorDetailView.cv_get_action_label_mode("context", key, target_default=target_default) == "label"
    assert caplog.records == []  # the floor was never read


@pytest.mark.parametrize("floor", [{"context": "nope"}, None], ids=["bad-mode", "non-dict"])
def test_unmapped_context_key_reads_invalid_floor(monkeypatch, caplog, floor):
    with (
        override_settings(CRUD_VIEWS_STRICT=True, CRUD_VIEWS_LABEL_MODE_DEFAULTS=floor),
        pytest.raises(ValueError, match="CRUD_VIEWS_LABEL_MODE_DEFAULTS"),
    ):
        AuthorDetailView.cv_get_action_label_mode("context", "update")
    with (
        caplog.at_level(logging.WARNING, logger="crud_views.lib.view.label_mode"),
        override_settings(CRUD_VIEWS_STRICT=False, CRUD_VIEWS_LABEL_MODE_DEFAULTS=floor),
    ):
        assert AuthorDetailView.cv_get_action_label_mode("context", "update") == "icon"
        assert AuthorDetailView.cv_get_action_label_mode("context", "delete") == "icon"
    assert len(caplog.records) == 1  # once per (location, value)


@pytest.mark.django_db
def test_invalid_target_mode_renders_configured_floor(author_douglas_adams, monkeypatch, caplog):
    # the raw target-view value is stamped unchanged; cv_button_data recovers it to the configured floor (D-10)
    _unmapped(monkeypatch)
    _set_target(monkeypatch, AuthorUpdateView, "nope")
    assert AuthorUpdateView.cv_icon_action or cv_author.icon_header  # a real icon is rendered
    client = _client([AUTHOR_FULL])
    url = _detail_url(author_douglas_adams)
    with (
        caplog.at_level(logging.WARNING, logger="crud_views.lib.view.label_mode"),
        override_settings(CRUD_VIEWS_STRICT=False, CRUD_VIEWS_LABEL_MODE_DEFAULTS=BOTH),
    ):
        responses = [client.get(url), client.get(url)]
    for resp in responses:
        assert resp.status_code == 200
        (update,) = lxml_html.fromstring(resp.content).xpath('//*[@cv-key="update"]')
        assert _icon_and_short_label(update), lxml_html.tostring(update)
        assert update.xpath("./i[@aria-hidden='true']")
    records = [r for r in caplog.records if r.name == "crud_views.lib.view.label_mode"]
    assert len(records) == 1
    message = records[0].getMessage()
    assert "cv_label_mode" in message
    assert "'nope'" in message
