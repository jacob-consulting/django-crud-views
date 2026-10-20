import pytest
from django.template import Context, Template
from django.test import override_settings

from crud_views.lib import button_classes as bc
from crud_views.lib.button_classes import (
    DEFAULT_BUTTON_CLASSES,
    get_button_class,
    get_button_classes,
    register_button_classes,
    reset_button_classes_cache,
)

EXPECTED_KEYS = {
    *(f"{loc}:{slot}" for loc in ("context", "list") for slot in ("primary", "secondary", "tertiary", "danger")),
    "card:primary",
    "card:secondary",
    "card:danger",
    "card:tertiary",
    "context:container",
    "list:container",
    "card:container",
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
    assert len(EXPECTED_KEYS) == 34
    assert set(DEFAULT_BUTTON_CLASSES) == EXPECTED_KEYS
    assert get_button_class("context", "primary") == "btn btn-outline-primary btn-lg"
    assert get_button_class("card", "danger") == "btn btn-secondary btn-sm"
    assert get_button_class("menu", "item") == "dropdown-item"


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
