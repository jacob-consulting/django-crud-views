"""System checks crud_views.E360/E361/W362 for the button class table."""

import pytest
from django.test import override_settings

from crud_views.checks import check_button_classes
from crud_views.lib import button_classes as bc
from crud_views.lib.button_classes import register_button_classes, reset_button_classes_cache


@pytest.fixture(autouse=True)
def _isolate_registry():
    snapshot = dict(bc._THEME_BUTTON_CLASSES)
    reset_button_classes_cache()
    yield
    bc._THEME_BUTTON_CLASSES.clear()
    bc._THEME_BUTTON_CLASSES.update(snapshot)
    reset_button_classes_cache()


def ids(messages) -> list[str]:
    return [m.id for m in messages]


def test_default_config_has_no_messages():
    assert check_button_classes() == []


def test_e360_removed_setting():
    with override_settings(CRUD_VIEWS_FILTER_RESET_BUTTON_CSS_CLASS="x"):
        messages = check_button_classes()
    assert ids(messages) == ["crud_views.E360"]
    assert "CRUD_VIEWS_FILTER_RESET_BUTTON_CSS_CLASS" in messages[0].msg
    assert "form:filter-reset" in messages[0].hint


def test_e361_non_str():
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"form:submit": 3}):
        messages = check_button_classes()
    assert ids(messages) == ["crud_views.E361"]
    assert "form:submit" in messages[0].msg


def test_none_is_valid():
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"form:submit": None}):
        assert check_button_classes() == []


def test_w362_unknown_key_in_settings():
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"form:sumbit": "btn"}):
        messages = check_button_classes()
    assert ids(messages) == ["crud_views.W362"]
    assert "form:sumbit" in messages[0].msg


def test_w362_unknown_key_in_theme():
    register_button_classes({"form:sumbit": "btn"})
    messages = check_button_classes()
    assert ids(messages) == ["crud_views.W362"]
    assert "form:sumbit" in messages[0].msg
