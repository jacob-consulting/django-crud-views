"""System checks crud_views.E360/E361/W362/E363/E364 for the button class table."""

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


@pytest.mark.parametrize("key", ["card:tertiary:icon", "context:primary:both", "list:danger:label"])
def test_w362_accepts_action_mode_keys(key):
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={key: "btn"}):
        assert check_button_classes() == []
    register_button_classes({key: "btn"})
    assert check_button_classes() == []


@pytest.mark.parametrize(
    "key",
    [
        "card:tertiary:iconn",
        "card:container:icon",
        "menu:item:both",
        "card:tertiary:icon:extra",
        "card:tertiary:",
        "form:submit:icon",
        "context:active:icon",
        "card:flex:both",
        "list:hidden-label:icon",
        "context:flex",
    ],
)
def test_w362_rejects_bad_mode_shape(key):
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={key: "btn"}):
        messages = check_button_classes()
    assert ids(messages) == ["crud_views.W362"]
    assert key in messages[0].msg


def test_w362_names_the_bad_mode():
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"card:tertiary:iconn": "btn"}):
        (message,) = check_button_classes()
    assert "'iconn'" in message.msg
    assert "both" in message.hint and "icon" in message.hint and "label" in message.hint


def test_mode_key_non_str_is_e361_only():
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"card:tertiary:icon": 3}):
        assert ids(check_button_classes()) == ["crud_views.E361"]


@pytest.mark.parametrize("key", [3, None, ("card", "tertiary")])
def test_w362_non_str_key_warns_instead_of_raising(key):
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={key: "btn"}):
        messages = check_button_classes()
    assert ids(messages) == ["crud_views.W362"]


def test_e363_icon_host_bad_placeholder():
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"list:icon-host": "{name}"}):
        messages = check_button_classes()
    assert ids(messages) == ["crud_views.E363"]
    assert "'list:icon-host'" in messages[0].msg


def test_icon_host_none_and_base_are_valid():
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"list:icon-host": None, "card:icon-host": "icon {name_class}"}):
        assert check_button_classes() == []


def test_e364_container_single_bad_value():
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"list:container-single": "naked"}):
        messages = check_button_classes()
    assert ids(messages) == ["crud_views.E364"]
    assert "'list:container-single'" in messages[0].msg
    assert "bare" in messages[0].hint and "container" in messages[0].hint


def test_container_keys_valid_no_messages():
    register_button_classes(
        {
            "context:container-list": "",
            "context:container-item": "li",
            "context:container-single": "bare",
            "card:container-single": None,
        }
    )
    assert check_button_classes() == []
