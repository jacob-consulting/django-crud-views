"""System checks crud_views.E360/E361/W362/E363/E364 for the button class table."""

import pytest
from django.core.checks import Warning as DjangoWarning
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


def test_form_submit_icon_key_reaches_checks_and_lookup():
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"form:submit:icon": "btn-form-submit-icon"}):
        assert check_button_classes() == []
        assert bc.get_button_class("form", "submit", "icon") == "btn-form-submit-icon"


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


FORM_KINDS = ("submit", "cancel", "delete", "filter-submit", "filter-reset")
MODES = ("icon", "both", "label")
VARIANTS = ("primary", "secondary", "tertiary", "danger")


def messages_for(classes, source):
    if source == "settings":
        with override_settings(CRUD_VIEWS_BUTTON_CLASSES=classes):
            return check_button_classes()
    register_button_classes(classes)
    return check_button_classes()


def test_class_key_vocabularies_are_finite_and_immutable():
    assert isinstance(bc.VARIANT_LOCATIONS, frozenset)
    assert {"context", "list", "card"} == bc.VARIANT_LOCATIONS
    assert isinstance(bc.FORM_KINDS, frozenset)
    assert set(FORM_KINDS) == bc.FORM_KINDS


@pytest.mark.parametrize("source", ["settings", "theme"])
@pytest.mark.parametrize("kind", FORM_KINDS)
@pytest.mark.parametrize("mode", MODES)
def test_all_form_kind_modes_are_accepted_without_icons(source, kind, mode):
    assert messages_for({f"form:{kind}:{mode}": "btn-form-mode"}, source) == []


@pytest.mark.parametrize("source", ["settings", "theme"])
@pytest.mark.parametrize("kind", FORM_KINDS)
@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("value", [None, ""])
def test_form_mode_none_and_empty_values_are_valid(source, kind, mode, value):
    assert messages_for({f"form:{kind}:{mode}": value}, source) == []


@pytest.mark.parametrize("source", ["settings", "theme"])
@pytest.mark.parametrize("location", ["context", "list", "card"])
@pytest.mark.parametrize("variant", VARIANTS)
@pytest.mark.parametrize("mode", MODES)
def test_all_action_variant_modes_remain_accepted(source, location, variant, mode):
    assert messages_for({f"{location}:{variant}:{mode}": "btn-action-mode"}, source) == []


@pytest.mark.parametrize("source", ["settings", "theme"])
@pytest.mark.parametrize(
    "key",
    [
        *(f"form:{variant}:icon" for variant in VARIANTS),
        "form:submitt:icon",
        "form:container:icon",
        "form:menu-toggle:icon",
        "form:active:icon",
        "form:hidden-label:icon",
        "form:icon-host:icon",
        "card:container:icon",
        "card:flex:both",
        "list:hidden-label:icon",
        "menu:item:both",
        "form",
        "form:",
        "form:submitt",
        "form::icon",
        ":submit:icon",
        "form:submit:icon:extra",
        "Form:submit:icon",
        "form:Submit:icon",
        " form:submit:icon",
        "form:submit :icon",
        3,
        None,
        ("form", "submit", "icon"),
    ],
)
def test_unknown_shapes_retain_exact_warning(source, key):
    (message,) = messages_for({key: "btn"}, source)
    assert type(message) is DjangoWarning
    assert message.id == "crud_views.W362"
    assert message.msg == f"Button class {key!r} is not a known key (typo?)."
    assert message.hint == "See the buttons documentation page for the list of keys."


@pytest.mark.parametrize("source", ["settings", "theme"])
@pytest.mark.parametrize("kind", FORM_KINDS)
@pytest.mark.parametrize("mode", ["iconn", "", "Icon", "icon "])
def test_known_form_kind_with_bad_mode_retains_exact_warning(source, kind, mode):
    key = f"form:{kind}:{mode}"
    (message,) = messages_for({key: "btn"}, source)
    assert type(message) is DjangoWarning
    assert message.id == "crud_views.W362"
    assert message.msg == f"Button class {key!r} has an unknown label mode {mode!r}."
    assert message.hint == "Use one of ['both', 'icon', 'label']."


@pytest.mark.parametrize("source", ["settings", "theme"])
@pytest.mark.parametrize("kind", FORM_KINDS)
def test_valid_form_mode_bad_value_is_e361_only(source, kind):
    assert ids(messages_for({f"form:{kind}:icon": 3}, source)) == ["crud_views.E361"]


@pytest.mark.parametrize("configured", [None, {}])
def test_none_or_empty_settings_add_no_overrides(configured):
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES=configured):
        assert bc.get_button_classes() == bc.DEFAULT_BUTTON_CLASSES
        assert check_button_classes() == []


@pytest.mark.parametrize("source", ["settings", "theme"])
@pytest.mark.parametrize("reverse", [False, True])
def test_unknown_mode_hint_is_sorted_independently_of_registration(source, reverse):
    modes = reversed(MODES) if reverse else MODES
    classes = {f"form:submit:{mode}": "btn" for mode in modes}
    classes["form:submit:iconn"] = "btn"
    (message,) = messages_for(classes, source)
    assert message.hint == "Use one of ['both', 'icon', 'label']."


@pytest.mark.parametrize("source", ["settings", "theme"])
def test_future_button_data_locations_cannot_widen_class_key_grammar(monkeypatch, source):
    from crud_views.lib.view import button_data

    monkeypatch.setattr(button_data, "LOCATIONS", button_data.LOCATIONS | {"form", "test-location"})
    invalid = [f"{location}:{variant}:icon" for location in ("form", "test-location") for variant in VARIANTS]
    valid = [f"form:{kind}:{mode}" for kind in FORM_KINDS for mode in MODES]
    valid += [
        f"{location}:{variant}:{mode}"
        for location in ("context", "list", "card")
        for variant in VARIANTS
        for mode in MODES
    ]
    messages = messages_for(dict.fromkeys([*invalid, *valid], "btn"), source)
    assert len(messages) == len(invalid)
    for key, message in zip(invalid, messages, strict=True):
        assert type(message) is DjangoWarning
        assert message.id == "crud_views.W362"
        assert message.msg == f"Button class {key!r} is not a known key (typo?)."
        assert message.hint == "See the buttons documentation page for the list of keys."


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
