import pytest
from django.template import Context, Template
from django.test import override_settings

from crud_views.lib import button_classes as bc
from crud_views.lib.button_classes import (
    DEFAULT_BUTTON_CLASSES,
    get_button_class,
    get_button_classes,
    get_icon_host_class,
    register_button_classes,
    reset_button_classes_cache,
)
from tests.lib.helper.icons import HOST_ICONS, HOST_LIBRARY

EXPECTED_KEYS = {
    *(f"{loc}:{slot}" for loc in ("context", "list") for slot in ("primary", "secondary", "tertiary", "danger")),
    "card:primary",
    "card:secondary",
    "card:danger",
    "card:tertiary",
    "context:container",
    "list:container",
    "card:container",
    *(f"{loc}:container-{slot}" for loc in ("context", "list", "card") for slot in ("list", "item", "single")),
    "context:menu-toggle",
    "list:menu-toggle",
    "card:menu-toggle",
    "context:menu-wrapper",
    "list:menu-wrapper",
    "card:menu-wrapper",
    "menu:item",
    "form:submit",
    "form:cancel",
    "form:delete",
    "form:filter-submit",
    "form:filter-reset",
    "formset:control",
    "formset:container",
    "formset:control-danger",
    "card-order:toggle",
    "card-order:container",
    "language:toggle",
    "object-detail:property-detail",
    "context:active",
    "list:active",
    "card:active",
    "menu:active",
    "card-order:active",
    "card:flex",
    "context:hidden-label",
    "list:hidden-label",
    "card:hidden-label",
    "card:root",
    "card:body",
    "card:title",
    "alert:error",
    "alert:warning",
    "alert:success",
    "alert:info",
    "alert:debug",
    "context:icon-host",
    "list:icon-host",
    "card:icon-host",
    "menu:icon-host",
}


@pytest.fixture(autouse=True)
def _isolate_registry():
    snapshot = dict(bc._THEME_BUTTON_CLASSES)
    reset_button_classes_cache()
    yield
    bc._THEME_BUTTON_CLASSES.clear()
    bc._THEME_BUTTON_CLASSES.update(snapshot)
    reset_button_classes_cache()


def test_default_table_is_complete():
    assert len(EXPECTED_KEYS) == 64
    assert set(DEFAULT_BUTTON_CLASSES) == EXPECTED_KEYS
    assert get_button_class("context", "primary") == "btn btn-outline-primary btn-lg"
    assert get_button_class("card", "danger") == "btn btn-secondary btn-sm"
    assert get_button_class("menu", "item") == "dropdown-item"


@pytest.mark.parametrize(
    ("location", "slot", "default"),
    [
        ("context", "active", "active"),
        ("list", "active", "active"),
        ("card", "active", "active"),
        ("menu", "active", "active"),
        ("card-order", "active", "active"),
        ("card", "flex", "flex-grow-1"),
        ("context", "hidden-label", "visually-hidden"),
        ("list", "hidden-label", "visually-hidden"),
        ("card", "hidden-label", "visually-hidden"),
    ],
)
def test_utility_slots_default_to_the_bootstrap_word(location, slot, default):
    # the words the leaves used to hard-code (#227)
    assert get_button_class(location, slot) == default


@pytest.mark.parametrize(
    ("level", "default"),
    [
        ("error", "alert alert-danger"),
        ("warning", "alert alert-warning"),
        ("success", "alert alert-success"),
        ("info", "alert alert-info"),
        ("debug", "alert alert-secondary"),
    ],
)
def test_alert_levels_default_to_bootstrap_alerts(level, default):
    # the alert frame's colours (#250); the level is the slot
    assert get_button_class("alert", level) == default


def test_unknown_key_renders_nothing():
    assert get_button_class("context", "nope") == ""


def test_none_and_empty_switch_off():
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"form:submit": None, "form:cancel": ""}):
        assert get_button_class("form", "submit") == ""
        assert get_button_class("form", "cancel") == ""


def test_non_str_value_renders_nothing():
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"form:submit": 3}):
        assert get_button_class("form", "submit") == ""


def test_theme_layer_then_settings_win():
    register_button_classes({"list:danger": "btn btn-ghost-danger"})
    assert get_button_class("list", "danger") == "btn btn-ghost-danger"
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"list:danger": "btn btn-x"}):
        assert get_button_class("list", "danger") == "btn btn-x"
    assert get_button_class("list", "danger") == "btn btn-ghost-danger"


def test_cache_resets_on_registration():
    get_button_classes()
    register_button_classes({"form:submit": "btn btn-new"})
    assert get_button_class("form", "submit") == "btn btn-new"


def test_tag_in_both_libraries_escapes():
    for lib in ("crud_views", "crud_views_object_detail"):
        tpl = Template("{% load " + lib + ' %}{% cv_button_class "form" "submit" %}')
        assert tpl.render(Context()) == "btn btn-primary"
        with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"form:submit": '"><x'}):
            assert tpl.render(Context()) == "&quot;&gt;&lt;x"


def test_tag_accepts_variables():
    tpl = Template("{% load crud_views %}{% cv_button_class cv_location cv_variant %}")
    assert tpl.render(Context({"cv_location": "card", "cv_variant": "primary"})) == "btn btn-primary btn-sm"


def test_mode_key_wins_when_present_else_base():
    register_button_classes({"card:tertiary:icon": "btn btn-sm btn-icon"})
    assert get_button_class("card", "tertiary", "icon") == "btn btn-sm btn-icon"
    assert get_button_class("card", "tertiary", "both") == "btn btn-outline-secondary btn-sm"
    assert get_button_class("card", "tertiary") == "btn btn-outline-secondary btn-sm"


def test_mode_key_none_switches_off_and_does_not_fall_through():
    register_button_classes({"card:tertiary:icon": "btn btn-sm btn-icon"})
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"card:tertiary:icon": None}):
        assert get_button_class("card", "tertiary", "icon") == ""
        assert get_button_class("card", "tertiary") == "btn btn-outline-secondary btn-sm"


@pytest.mark.parametrize("mode", ["", "iconn", None, True, 3])
def test_unknown_or_empty_mode_falls_back(mode):
    register_button_classes({"card:tertiary:icon": "btn btn-sm btn-icon"})
    assert get_button_class("card", "tertiary", mode) == "btn btn-outline-secondary btn-sm"


def test_settings_base_key_does_not_beat_theme_mode_key():
    register_button_classes({"card:tertiary:icon": "btn btn-sm btn-icon"})
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"card:tertiary": "btn btn-sm btn-success"}):
        assert get_button_class("card", "tertiary", "icon") == "btn btn-sm btn-icon"
        assert get_button_class("card", "tertiary", "both") == "btn btn-sm btn-success"
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"card:tertiary:icon": "btn x"}):
        assert get_button_class("card", "tertiary", "icon") == "btn x"


def test_tag_third_argument_in_both_libraries():
    for lib in ("crud_views", "crud_views_object_detail"):
        tpl = Template("{% load " + lib + ' %}{% cv_button_class "card" "tertiary" "icon" %}')
        assert tpl.render(Context()) == "btn btn-outline-secondary btn-sm"
        with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"card:tertiary:icon": "x-icon"}):
            assert tpl.render(Context()) == "x-icon"


def test_tag_accepts_mode_variable():
    tpl = Template("{% load crud_views %}{% cv_button_class cv_location cv_variant cv_label_mode %}")
    ctx = {"cv_location": "card", "cv_variant": "tertiary", "cv_label_mode": "icon"}
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"card:tertiary:icon": "x-icon"}):
        assert tpl.render(Context(ctx)) == "x-icon"
        assert tpl.render(Context({**ctx, "cv_label_mode": "both"})) == "btn btn-outline-secondary btn-sm"


def test_button_classes_module_has_no_module_level_view_import():
    import ast
    from pathlib import Path

    tree = ast.parse(Path(bc.__file__).read_text())
    offenders = [
        node.module
        for node in tree.body
        if isinstance(node, ast.ImportFrom)
        and ("lib.view" in (node.module or "") or (node.level and (node.module or "").split(".")[0] == "view"))
    ]
    assert offenders == []


# icon-host slots (#258)

host_icons = override_settings(CRUD_VIEWS_ICON_LIBRARIES=HOST_LIBRARY, CRUD_VIEWS_ICONS=HOST_ICONS)


def test_icon_host_default_slots():
    for location in ("context", "list", "card", "menu"):
        assert DEFAULT_BUTTON_CLASSES[f"{location}:icon-host"] == "{name_class}"


@host_icons
def test_get_icon_host_class():
    assert get_icon_host_class("context", "update") == "icon-edit"
    assert get_icon_host_class("menu", "ui:trash") == "icon-trash"
    assert get_icon_host_class("context", "fas:pen") == ""
    assert get_icon_host_class("context", "create") == ""  # the default table: an element icon
    assert get_icon_host_class("context", None) == ""


@host_icons
def test_get_icon_host_class_with_base():
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"card:icon-host": "icon {name_class}"}):
        assert get_icon_host_class("card", "update") == "icon icon-edit"
        assert get_icon_host_class("list", "update") == "icon-edit"


@host_icons
def test_get_icon_host_class_slot_none():
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"menu:icon-host": None}):
        assert get_icon_host_class("menu", "update") == ""


@host_icons
def test_get_icon_host_class_unusable_slot():
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"list:icon-host": "{name}"}):
        assert get_icon_host_class("list", "update") == ""
