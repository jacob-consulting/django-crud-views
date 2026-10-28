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


# the form leaf (Phase 6): icon / both / label bodies with inline (element) and host-placed icons

FORM_LEAF = "crud_views/tags/button/form.html"

# kind -> (native type, semantic icon name, Font Awesome default classes, Bootstrap Icons preset classes)
FORM_KIND_ICONS = {
    "submit": ("submit", "save", "fa-regular fa-floppy-disk", "bi bi-floppy"),
    "delete": ("submit", "delete", "fa-regular fa-trash-can", "bi bi-trash"),
    "cancel": ("button", "cancel", "fa-solid fa-xmark", "bi bi-x-lg"),
    "filter-submit": ("submit", "filter", "fa-solid fa-filter", "bi bi-funnel"),
    "filter-reset": ("reset", "filter-reset", "fa-solid fa-rotate-left", "bi bi-arrow-counterclockwise"),
}

FORM_HOST_ICONS = {
    **HOST_ICONS,
    "save": "ui:floppy",
    "delete": "ui:trash",
    "cancel": "ui:x",
    "filter-reset": "ui:filter-off",
}


def form_ctx(kind="submit", **kw):
    button_type, icon = FORM_KIND_ICONS[kind][:2]
    data = {
        "cv_key": kind,
        "cv_type": button_type,
        "cv_name": kind,
        "cv_value": "Go",
        "cv_id": f"{button_type}-id-{kind}",
        "cv_icon": icon,
    }
    data.update(kw)
    return data


def render_form(kind="submit", **kw):
    markup = render_to_string(FORM_LEAF, cv_button_data(form_ctx(kind, **kw), "form"))
    (node,) = lxml_html.fromstring(f"<div>{markup}</div>").xpath("./*")
    return node


def base_classes(kind, mode):
    from crud_views.lib.button_classes import get_button_class

    return get_button_class("form", kind, mode).split()


# the package defaults only: every form kind's icon renders as an element
ELEMENT_ICONS = override_settings(CRUD_VIEWS_ICONS={})


@pytest.mark.parametrize("kind", sorted(FORM_KIND_ICONS))
def test_form_element_icon_mode(kind):
    fa = FORM_KIND_ICONS[kind][2]
    with ELEMENT_ICONS:
        button = render_form(kind, cv_label_mode="icon")
    assert button.tag == "button"
    assert button.get("class").split() == base_classes(kind, "icon")
    assert button.get("title") == "Go"
    assert button.get("data-cv-tooltip") == "form"
    assert inner(button) == f'<i class="{fa}" aria-hidden="true"></i><span class="visually-hidden">Go</span>'


@pytest.mark.parametrize("kind", sorted(FORM_KIND_ICONS))
def test_form_element_both_mode(kind):
    fa = FORM_KIND_ICONS[kind][2]
    with ELEMENT_ICONS:
        button = render_form(kind, cv_label_mode="both")
    assert button.get("class").split() == base_classes(kind, "both")
    assert button.get("title") is None and button.get("data-cv-tooltip") is None
    assert inner(button) == f'<i class="{fa}" aria-hidden="true"></i> <span>Go</span>'


@pytest.mark.parametrize("kind", sorted(FORM_KIND_ICONS))
def test_form_label_mode_suppresses_every_icon(kind):
    for icons in (None, FORM_HOST_ICONS):
        with override_settings(CRUD_VIEWS_ICONS=icons or HOST_ICONS):
            button = render_form(kind, cv_label_mode="label")
        assert button.get("class").split() == base_classes(kind, "label")
        assert button.get("title") is None and button.get("data-cv-tooltip") is None
        assert not button.cssselect("i")
        assert inner(button) == "<span>Go</span>"


@pytest.mark.parametrize("kind", sorted(FORM_KIND_ICONS))
def test_form_bootstrap_preset(kind):
    from crud_views.lib.icons import BOOTSTRAP_ICONS

    bi = FORM_KIND_ICONS[kind][3]
    with override_settings(CRUD_VIEWS_ICONS=BOOTSTRAP_ICONS):
        button = render_form(kind, cv_label_mode="both")
    assert button.cssselect("i")[0].get("class") == bi


def test_form_repeated_renders_follow_the_current_registry():
    from crud_views.lib.button_classes import DEFAULT_BUTTON_CLASSES
    from crud_views.lib.icons import BOOTSTRAP_ICONS, DEFAULT_ICONS

    snapshot = (dict(DEFAULT_ICONS), dict(BOOTSTRAP_ICONS), dict(DEFAULT_BUTTON_CLASSES))
    seen = []
    for icons, mode in (
        (HOST_ICONS, "icon"),
        (BOOTSTRAP_ICONS, "icon"),
        (FORM_HOST_ICONS, "icon"),
        (HOST_ICONS, "both"),
        (FORM_HOST_ICONS, "label"),
        (HOST_ICONS, "icon"),
    ):
        with override_settings(CRUD_VIEWS_ICONS=icons):
            button = render_form("submit", cv_label_mode=mode)
        seen.append((button.get("class"), inner(button)))
    hidden = '<span class="visually-hidden">Go</span>'
    assert seen == [
        ("btn btn-primary", '<i class="fa-regular fa-floppy-disk" aria-hidden="true"></i>' + hidden),
        ("btn btn-primary", '<i class="bi bi-floppy" aria-hidden="true"></i>' + hidden),
        ("btn btn-primary icon-floppy", hidden),
        ("btn btn-primary", '<i class="fa-regular fa-floppy-disk" aria-hidden="true"></i> <span>Go</span>'),
        ("btn btn-primary", "<span>Go</span>"),
        seen[0],
    ]
    assert (dict(DEFAULT_ICONS), dict(BOOTSTRAP_ICONS), dict(DEFAULT_BUTTON_CLASSES)) == snapshot


def test_form_raw_class_and_custom_renderer_prefixes():
    raw = render_form("submit", cv_label_mode="both", cv_icon="my-raw icon-save")
    assert raw.cssselect("i")[0].get("class") == "my-raw icon-save"
    libraries = {**HOST_LIBRARY, "xy": {"renderer": "tests.test1.test_icon_host_leaves.xy_renderer"}}
    with override_settings(CRUD_VIEWS_ICON_LIBRARIES=libraries):
        for mode in ("icon", "both"):
            button = render_form("cancel", cv_label_mode=mode, cv_icon="xy:close")
            (svg,) = button.cssselect("svg")
            assert svg.get("data-icon") == "close"
            assert "xy-close" not in button.get("class")
        assert not render_form("cancel", cv_label_mode="label", cv_icon="xy:close").cssselect("svg")


def xy_renderer(name, *, css, config):
    from django.utils.html import format_html

    return format_html('<svg data-icon="{}"></svg>', name)


@pytest.mark.parametrize("kind", sorted(FORM_KIND_ICONS))
@pytest.mark.parametrize("mode", ["icon", "both"])
def test_form_host_icon_goes_on_the_button(kind, mode):
    name_class = "icon-" + FORM_HOST_ICONS[FORM_KIND_ICONS[kind][1]].split(":", 1)[1]
    with override_settings(CRUD_VIEWS_ICONS=FORM_HOST_ICONS):
        data = cv_button_data(form_ctx(kind, cv_label_mode=mode), "form")
        button = render_form(kind, cv_label_mode=mode)
    assert (data["cv_icon_class"], data["cv_icon_inline"]) == (name_class, False)
    assert button.get("class").split() == [*base_classes(kind, mode), name_class]
    assert not button.cssselect("i")
    if mode == "icon":
        assert inner(button) == '<span class="visually-hidden">Go</span>'
        assert (button.get("title"), button.get("data-cv-tooltip")) == ("Go", "form")
    else:
        assert inner(button) == "<span>Go</span>"
        assert button.get("title") is None


def test_form_host_icon_follows_the_mode_class_and_suffix():
    overrides = {"form:submit:icon": "btn btn-icon", "form:icon-host": "icon {name_class}"}
    with override_settings(CRUD_VIEWS_ICONS=FORM_HOST_ICONS, CRUD_VIEWS_BUTTON_CLASSES=overrides):
        button = render_form("submit", cv_label_mode="icon", cv_css_class="extra")
    assert button.get("class") == "btn btn-icon extra icon icon-floppy"


@pytest.mark.parametrize("value", [None, ""])
@pytest.mark.parametrize("mode", ["icon", "both"])
def test_form_host_slot_none_or_empty_switches_the_icon_off(value, mode):
    with override_settings(CRUD_VIEWS_ICONS=FORM_HOST_ICONS, CRUD_VIEWS_BUTTON_CLASSES={"form:icon-host": value}):
        data = cv_button_data(form_ctx("submit", cv_label_mode=mode), "form")
        button = render_form("submit", cv_label_mode=mode)
    assert (data["cv_icon_class"], data["cv_icon_inline"]) == ("", False)
    assert button.get("class") == "btn btn-primary"
    assert not button.cssselect("i")
    assert button.text_content() == "Go"


def test_form_host_classes_are_escaped_attributes():
    icons = {**FORM_HOST_ICONS, "save": 'ui:x" onmouseover="alert(1)'}
    overrides = {"form:icon-host": '{name_class} "><b>', "form:hidden-label": '"><i>sr'}
    with override_settings(CRUD_VIEWS_ICONS=icons, CRUD_VIEWS_BUTTON_CLASSES=overrides):
        markup = render_to_string(FORM_LEAF, cv_button_data(form_ctx(cv_label_mode="icon"), "form"))
    doc = lxml_html.fromstring(f"<div>{markup}</div>")
    (button,) = doc.xpath("./*")
    assert set(button.attrib) == {"type", "name", "value", "id", "class", "title", "data-cv-tooltip"}
    assert button.get("class") == 'btn btn-primary icon-x" onmouseover="alert(1) "><b>'
    assert not doc.cssselect("b, i")
    (span,) = button.cssselect("span")
    assert span.get("class") == '"><i>sr'


def test_form_hidden_label_class_override():
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"form:hidden-label": "sr-only"}):
        button = render_form("delete", cv_label_mode="icon")
    assert button.cssselect("span")[0].get("class") == "sr-only"


@pytest.mark.parametrize("mode", ["icon", "both", "label"])
def test_form_unicode_and_lazy_labels_are_exact(mode):
    from django.utils import translation
    from django.utils.functional import lazy

    text = "Spéichern ✓ <b>&amp; 日本"
    label = lazy(lambda: text, str)()
    for icons in (HOST_ICONS, FORM_HOST_ICONS):
        with override_settings(CRUD_VIEWS_ICONS=icons):
            button = render_form("submit", cv_label_mode=mode, cv_value=label, cv_label=label)
        (span,) = button.cssselect("span")
        assert span.text == text and button.get("value") == text
        assert button.get("title") == (text if mode == "icon" else None)

    from django.utils.translation import gettext, gettext_lazy

    for language in ("en", "de", "en"):
        with translation.override(language):
            expected = gettext("Save")
            button = render_form("submit", cv_label_mode=mode, cv_value=gettext_lazy("Save"))
        assert button.cssselect("span")[0].text == expected
        assert button.get("title") == (expected if mode == "icon" else None)


def test_form_empty_label_in_icon_mode():
    for icons, inline in ((HOST_ICONS, True), (FORM_HOST_ICONS, False)):
        with override_settings(CRUD_VIEWS_ICONS=icons):
            button = render_form("submit", cv_label_mode="icon", cv_value="")
        assert button.get("title") is None and button.get("data-cv-tooltip") is None
        assert button.cssselect("span.visually-hidden")[0].text is None
        assert bool(button.cssselect("i")) is inline


def test_form_utility_keys_and_finite_grammar():
    from django.core.checks import Warning as DjangoWarning

    from crud_views.lib.button_classes import (
        DEFAULT_BUTTON_CLASSES,
        FORM_KINDS,
        VARIANT_LOCATIONS,
        _action_key_parts,
        _is_action_mode_key,
        button_class_check_messages,
    )

    assert DEFAULT_BUTTON_CLASSES["form:hidden-label"] == "visually-hidden"
    assert DEFAULT_BUTTON_CLASSES["form:icon-host"] == "{name_class}"
    assert FORM_KINDS == {"submit", "cancel", "delete", "filter-submit", "filter-reset"}
    assert VARIANT_LOCATIONS == {"context", "list", "card"}
    for kind in FORM_KINDS:
        assert all(_is_action_mode_key(f"form:{kind}:{mode}") for mode in ("label", "both", "icon"))
    for key in (
        "form:hidden-label:icon",
        "form:icon-host:both",
        "form:primary:both",
        "form:save:icon",
        "form:submit:icon:x",
    ):
        assert not _is_action_mode_key(key)
    assert _action_key_parts("form:icon-host:label") is None
    bad = {"form:hidden-label:icon": "x", "form:icon-host:both": "x", "form:primary:both": "x", "form:submit:big": "x"}
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES=bad):
        messages = [m for m in button_class_check_messages() if m.id == "crud_views.W362"]
    assert all(isinstance(m, DjangoWarning) for m in messages)
    assert sorted(m.msg for m in messages) == [
        "Button class 'form:hidden-label:icon' is not a known key (typo?).",
        "Button class 'form:icon-host:both' is not a known key (typo?).",
        "Button class 'form:primary:both' is not a known key (typo?).",
        "Button class 'form:submit:big' has an unknown label mode 'big'.",
    ]
