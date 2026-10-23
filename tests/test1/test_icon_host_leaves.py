"""Host-placed icons (#258) in the action and menu-item leaves: the icon class goes on the button, no <i> inside."""

import pytest
from django.template.loader import render_to_string
from django.test import override_settings
from lxml import html as lxml_html

from crud_views.lib.view.button_data import cv_button_data
from tests.lib.helper.icons import HOST_ICONS, HOST_LIBRARY

ACTION_LEAF = "crud_views/tags/button/action.html"
MENU_ITEM_LEAF = "crud_views/tags/button/menu_item.html"

pytestmark = pytest.mark.usefixtures("_host_icons")


@pytest.fixture
def _host_icons():
    with override_settings(CRUD_VIEWS_ICON_LIBRARIES=HOST_LIBRARY, CRUD_VIEWS_ICONS=HOST_ICONS):
        yield


def ctx(**kw):
    data = {
        "cv_url": "/author/1/detail/",
        "cv_key": "detail",
        "cv_action_label": "Details",
        "cv_action_short_label": "Details",
        "cv_oid": "o1",
        "cv_icon_action": "detail",
    }
    data.update(kw)
    return data


def render(leaf, location, kind="action", **kw):
    markup = render_to_string(leaf, cv_button_data(ctx(**kw), location, kind=kind))
    (node,) = lxml_html.fromstring(f"<div>{markup}</div>").xpath("./*")
    return node


def inner(node) -> str:
    return (node.text or "") + "".join(lxml_html.tostring(c, encoding="unicode") for c in node)


@pytest.mark.parametrize("location", ["context", "list", "card"])
def test_host_icon_mode(location):
    a = render(ACTION_LEAF, location, cv_label_mode="icon")
    assert a.get("class").split()[-1] == "icon-eye"
    assert a.get("title") == "Details"
    assert not a.cssselect("i")
    assert inner(a) == '<span class="visually-hidden">Details</span>'


@pytest.mark.parametrize("location", ["context", "list", "card"])
def test_host_both_mode(location):
    a = render(ACTION_LEAF, location, cv_label_mode="both")
    assert a.get("class").split()[-1] == "icon-eye"
    assert inner(a) == "<span>Details</span>"


@pytest.mark.parametrize("location", ["context", "list", "card"])
def test_host_label_mode(location):
    a = render(ACTION_LEAF, location, cv_label_mode="label")
    assert "icon-eye" not in a.get("class")
    assert inner(a) == "<span>Details</span>"


def test_host_both_mode_without_icon():
    a = render(ACTION_LEAF, "card", cv_label_mode="both", cv_icon_action=None)
    assert a.get("class") == "btn btn-secondary btn-sm"
    assert inner(a) == "<span>Details</span>"


def test_host_disabled_button_keeps_class():
    button = render(ACTION_LEAF, "context", cv_disabled=True, cv_disabled_reason="permission")
    assert button.tag == "button"
    assert button.get("disabled") is not None
    assert button.get("data-cv-disabled") == "permission"
    assert button.get("class").split()[-1] == "icon-eye"


def test_host_mixed_page_keeps_element_icons_inline():
    host = render(ACTION_LEAF, "context")
    element = render(ACTION_LEAF, "context", cv_key="create", cv_icon_action="fas:plus")
    assert "icon-eye" in host.get("class") and not host.cssselect("i")
    assert element.get("class") == "btn btn-outline-primary btn-lg"
    assert element.cssselect("i")[0].get("class") == "fa-solid fa-plus"


def test_host_icon_class_with_base_from_the_table():
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"card:icon-host": "icon {name_class}"}):
        a = render(ACTION_LEAF, "card")
    assert a.get("class").split()[-2:] == ["icon", "icon-eye"]


def test_host_slot_none_switches_icon_off():
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"context:icon-host": None}):
        a = render(ACTION_LEAF, "context")
    assert a.get("class") == "btn btn-outline-primary btn-lg"
    assert not a.cssselect("i")


def test_host_menu_item():
    a = render(MENU_ITEM_LEAF, "list", kind="menu-item")
    assert a.get("class") == "dropdown-item icon-eye"
    assert not a.cssselect("i")
    assert not a.cssselect(".cv-icon-fw")
    assert a.text_content().strip() == "Details"


def test_host_menu_item_uses_menu_slot():
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"menu:icon-host": "link-icon {name_class}"}):
        a = render(MENU_ITEM_LEAF, "context", kind="menu-item")
    assert a.get("class") == "dropdown-item link-icon icon-eye"
