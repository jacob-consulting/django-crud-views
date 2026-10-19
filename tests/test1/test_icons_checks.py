"""System checks crud_views.E350/E351/W352/W353 for the icon registry."""

import pytest
from django.test import override_settings

from crud_views.checks import check_icons
from crud_views.lib.viewset import _REGISTRY, ViewSet
from tests.test1.app.models import Publisher


def ids(messages) -> list[str]:
    return [m.id for m in messages]


def test_default_config_has_no_icon_messages():
    assert check_icons() == []


@pytest.mark.parametrize(
    "name",
    [
        "CRUD_VIEWS_ACTIONS_MENU_ICON",
        "CRUD_VIEWS_FILTER_ICON",
        "CRUD_VIEWS_OBJECT_DETAIL_ICONS_LIBRARY",
        "CRUD_VIEWS_OBJECT_DETAIL_ICONS_CLASS",
        "CRUD_VIEWS_OBJECT_DETAIL_ICONS_TYPE",
        "CRUD_VIEWS_OBJECT_DETAIL_ICONS_PREFIX",
        "CRUD_VIEWS_OBJECT_DETAIL_NAMED_ICONS",
    ],
)
def test_e350_removed_setting(name):
    with override_settings(**{name: "x"}):
        messages = check_icons()
    assert ids(messages) == ["crud_views.E350"]
    assert name in messages[0].msg


def test_e350_one_message_per_setting():
    with override_settings(CRUD_VIEWS_ACTIONS_MENU_ICON="x", CRUD_VIEWS_FILTER_ICON="y"):
        assert ids(check_icons()) == ["crud_views.E350", "crud_views.E350"]


def test_e350_hint_points_to_icons_setting():
    with override_settings(CRUD_VIEWS_FILTER_ICON="x"):
        assert 'CRUD_VIEWS_ICONS["filter"]' in check_icons()[0].hint


def test_e351_renderer_not_importable():
    with override_settings(CRUD_VIEWS_ICON_LIBRARIES={"xy": {"renderer": "no.such.module.render"}}):
        messages = check_icons()
    assert ids(messages) == ["crud_views.E351"]
    assert "no.such.module.render" in messages[0].msg


def test_e351_importable_renderer_ok():
    with override_settings(CRUD_VIEWS_ICON_LIBRARIES={"xy": {"renderer": "crud_views.lib.icons.font_renderer"}}):
        assert check_icons() == []


def test_w352_unregistered_prefix():
    with override_settings(CRUD_VIEWS_ICONS={"list": "zz:rows"}):
        messages = check_icons()
    assert ids(messages) == ["crud_views.W352"]
    assert "zz" in messages[0].msg


def test_w352_registered_prefix_ok():
    with override_settings(
        CRUD_VIEWS_ICON_LIBRARIES={"zz": {"renderer": "font", "class": "zz-{name}"}},
        CRUD_VIEWS_ICONS={"list": "zz:rows"},
    ):
        assert check_icons() == []


def test_w352_name_to_name():
    with override_settings(CRUD_VIEWS_ICONS={"list": "detail"}):
        messages = check_icons()
    assert ids(messages) == ["crud_views.W352"]
    assert "detail" in messages[0].msg


def test_w352_raw_class_ok():
    with override_settings(CRUD_VIEWS_ICONS={"list": "fa-solid fa-list"}):
        assert check_icons() == []


def test_w353_viewset_and_view_attributes():
    from crud_views.lib.view import CrudView

    name = "icon_check_probe"
    viewset = ViewSet(model=Publisher, name=name, icon_header="xy:truck")
    try:

        class ProbeView(CrudView):
            cv_viewset = viewset
            cv_key = "probe"
            cv_path = "probe"
            cv_icon_action = "xy:eye"
            cv_icon_header = "fa-regular fa-eye"

        messages = [m for m in check_icons() if m.id == "crud_views.W353"]
        assert len(messages) == 2
        text = " ".join(m.msg for m in messages)
        assert name in text
        assert "icon_header" in text
        assert "cv_icon_action" in text
        assert "cv_icon_header" not in text
    finally:
        _REGISTRY.pop(name, None)


def test_e354_font_library_without_class():
    with override_settings(CRUD_VIEWS_ICON_LIBRARIES={"xy": {"renderer": "font"}}):
        messages = check_icons()
    assert ids(messages) == ["crud_views.E354"]
    assert "'xy'" in messages[0].msg


def test_e354_not_for_custom_renderer_or_with_class():
    libs = {"xy": {"renderer": "crud_views.lib.icons.font_renderer"}, "ab": {"renderer": "font", "class": "a-{name}"}}
    with override_settings(CRUD_VIEWS_ICON_LIBRARIES=libs):
        assert "crud_views.E354" not in ids(check_icons())


def test_w353_skips_non_str_values():
    from crud_views.lib.view import CrudView

    name = "icon_check_probe_nonstr"
    viewset = ViewSet(model=Publisher, name=name)
    try:

        class ProbeView(CrudView):
            cv_viewset = viewset
            cv_key = "probe"
            cv_path = "probe"
            cv_icon_action = 5
            cv_icon_header = ("xy:eye",)

        assert [m for m in check_icons() if m.id == "crud_views.W353"] == []
    finally:
        _REGISTRY.pop(name, None)


def _boom(path):
    raise RuntimeError("boom")


def test_e355_library_config_not_a_dict():
    with override_settings(CRUD_VIEWS_ICON_LIBRARIES={"xy": "font"}):
        messages = check_icons()
    assert ids(messages) == ["crud_views.E355"]
    assert "'xy'" in messages[0].msg


def test_e355_renderer_not_callable():
    with override_settings(CRUD_VIEWS_ICON_LIBRARIES={"xy": {"renderer": None}}):
        assert ids(check_icons()) == ["crud_views.E355"]


def test_e355_via_register_icon_library(monkeypatch):
    from crud_views.lib import icons as icons_module

    monkeypatch.setattr(icons_module, "_THEME_LIBRARIES", {})
    icons_module.register_icon_library("xy", renderer=None)
    try:
        assert ids(check_icons()) == ["crud_views.E355"]
    finally:
        icons_module.reset_icon_cache()


@pytest.mark.parametrize("template", ["x-{} {name}", "x-{size} {name}", "x-{"])
def test_e354_class_not_a_format_string(template):
    with override_settings(CRUD_VIEWS_ICON_LIBRARIES={"xy": {"renderer": "font", "class": template}}):
        messages = check_icons()
    assert ids(messages) == ["crud_views.E354"]
    assert "format string" in messages[0].msg


def test_e351_renderer_import_raises_other_exception(monkeypatch):
    from crud_views.lib import icons as icons_module

    monkeypatch.setattr(icons_module, "import_string", _boom)
    with override_settings(CRUD_VIEWS_ICON_LIBRARIES={"xy": {"renderer": "some.module.render"}}):
        messages = check_icons()
    assert ids(messages) == ["crud_views.E351"]
    assert "RuntimeError: boom" in messages[0].msg
