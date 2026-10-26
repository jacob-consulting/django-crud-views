import copy

import pytest
from django.test import override_settings

from crud_views.lib.view.button_data import LEAF_KEYS, cv_button_data
from tests.lib.helper.icons import HOST_ICONS, HOST_LIBRARY

LOCATIONS = ["context", "list", "card"]


def base(**kw):
    ctx = {
        "cv_url": "/u/",
        "cv_key": "detail",
        "cv_action_label": "Show",
        "cv_action_short_label": "Detail",
        "cv_list_action_method": "get",
        "cv_disabled": False,
        "cv_oid": "o1",
        "cv_icon_action": "detail",
        "cv_variant": "primary",
    }
    ctx.update(kw)
    return ctx


@pytest.mark.parametrize("location", LOCATIONS)
def test_get(location):
    data = cv_button_data(base(), location)
    assert data["cv_location"] == location
    assert data["cv_tag"] == "a"
    assert data["cv_href"] == "/u/"
    assert "cv_submit_target" not in data
    assert data["cv_modal"] is False
    assert data["cv_modal_size"] == ""
    assert data["cv_variant"] == "primary"
    assert data["cv_icon"] == "detail"
    assert data["cv_key"] == "detail"
    assert data["cv_disabled"] is False
    assert data["cv_disabled_reason"] == ""
    if location == "card":
        assert data["cv_label"] == "Detail"
        assert data["cv_short_label"] == "Detail"
    else:
        assert data["cv_title"] == "Show"
        assert data["cv_label"] == "Show"
        assert data["cv_short_label"] == "Detail"


@pytest.mark.parametrize("location", LOCATIONS)
def test_post_without_modal(location):
    data = cv_button_data(base(cv_list_action_method="post"), location)
    assert data["cv_tag"] == "button"
    assert data["cv_submit_target"] == "cv_form_o1"
    assert "cv_href" not in data


@pytest.mark.parametrize("location", LOCATIONS)
def test_post_with_modal(location):
    data = cv_button_data(base(cv_list_action_method="post", cv_modal=True, cv_modal_size="lg"), location)
    assert data["cv_tag"] == "a"
    assert data["cv_href"] == "/u/"
    assert data["cv_modal"] is True
    assert data["cv_modal_size"] == "lg"
    assert "cv_submit_target" not in data


@pytest.mark.parametrize("location", LOCATIONS)
def test_disabled(location):
    ctx = base(cv_disabled=True, cv_disabled_reason="permission", cv_url=None, cv_modal=True, cv_is_active=True)
    data = cv_button_data(ctx, location)
    assert data["cv_tag"] == "button"
    assert "cv_href" not in data
    assert "cv_submit_target" not in data
    assert data["cv_modal"] is False
    assert data["cv_active"] is False
    assert data["cv_disabled"] is True
    assert data["cv_disabled_reason"] == "permission"


@pytest.mark.parametrize("location", LOCATIONS)
def test_active(location):
    assert cv_button_data(base(cv_is_active=True), location)["cv_active"] is True
    assert cv_button_data(base(), location)["cv_active"] is False


def test_card_label_mode_defaults_to_both():
    data = cv_button_data(base(cv_label="Details"), "card")
    assert data["cv_label"] == "Details"
    assert data["cv_label_mode"] == "both"
    assert "cv_title" not in data


@pytest.mark.parametrize("mode", ["label", "icon", "both"])
def test_card_label_mode_passes_through(mode):
    data = cv_button_data(base(cv_label="Details", cv_label_mode=mode), "card")
    assert data["cv_label_mode"] == mode


def test_card_icon_mode_gets_title():
    data = cv_button_data(base(cv_label="Details", cv_label_mode="icon"), "card")
    assert data["cv_title"] == "Details"


def test_card_empty_label_forces_icon():
    ctx = {"cv_label": "", "cv_key": "", "cv_url": "/u/", "cv_label_mode": "both", "cv_icon_action": "detail"}
    data = cv_button_data(ctx, "card")
    assert data["cv_label_mode"] == "icon"


@pytest.mark.parametrize("value", [True, False])
def test_cv_no_label_in_ctx_raises(value):
    # presence, not truthiness: cv_no_label=False is the shape the old card-label tests passed
    ctx = base(cv_label="Details", cv_no_label=value)
    with pytest.raises(ValueError, match="cv_no_label"):
        cv_button_data(ctx, "card")


@pytest.mark.parametrize("location", LOCATIONS)
@pytest.mark.parametrize("value", ["lable", "icons", "Both", 1, ["both"]])
def test_unknown_cv_label_mode_raises_everywhere(location, value):
    ctx = base(cv_label="Details", cv_label_mode=value)
    with pytest.raises(ValueError, match="cv_label_mode"):
        cv_button_data(ctx, location)


def test_card_label_falls_back_to_key():
    data = cv_button_data({"cv_label": None, "cv_key": "book", "cv_url": "/u/"}, "card")
    assert data["cv_label"] == "book"
    assert data["cv_short_label"] == "book"
    assert "None" not in [str(v) for k, v in data.items() if k != "cv_icon"]


@pytest.mark.parametrize("location", ["context", "list"])
@pytest.mark.parametrize("mode", ["both", "label"])
def test_label_mode_stamped_off_cards_shows_short_label(location, mode):
    data = cv_button_data(base(cv_label_mode=mode), location)
    assert data["cv_label_mode"] == mode
    assert data["cv_label"] == "Detail"
    assert data["cv_short_label"] == "Detail"
    assert "cv_title" not in data


@pytest.mark.parametrize("location", ["context", "list"])
def test_label_mode_icon_off_cards_keeps_full_label_and_title(location):
    data = cv_button_data(base(cv_label_mode="icon"), location)
    assert data["cv_label_mode"] == "icon"
    assert data["cv_label"] == "Show"
    assert data["cv_title"] == "Show"


@pytest.mark.parametrize("location,expected", [("card", True), ("context", False), ("list", False)])
def test_flex(location, expected):
    assert cv_button_data(base(cv_flex=True), location)["cv_flex"] is expected


@pytest.mark.parametrize("location", LOCATIONS)
def test_variant_defaults_to_secondary(location):
    ctx = base()
    del ctx["cv_variant"]
    assert cv_button_data(ctx, location)["cv_variant"] == "secondary"


def test_invalid_location():
    with pytest.raises(ValueError):
        cv_button_data(base(), "toolbar")


@pytest.mark.parametrize("location", LOCATIONS)
def test_pure_and_within_leaf_keys(location):
    ctx = base(cv_list_action_method="post", cv_modal=True, cv_is_active=True, cv_flex=True)
    before = copy.deepcopy(ctx)
    data = cv_button_data(ctx, location)
    assert ctx == before
    assert set(data) <= LEAF_KEYS


# host-placed icons (#258)

host_icons = override_settings(CRUD_VIEWS_ICON_LIBRARIES=HOST_LIBRARY, CRUD_VIEWS_ICONS=HOST_ICONS)


@host_icons
@pytest.mark.parametrize("location", LOCATIONS)
def test_host_icon_keys(location):
    data = cv_button_data(base(), location)
    assert data["cv_icon_class"] == "icon-eye"
    assert data["cv_icon_inline"] is False


@pytest.mark.parametrize("location", LOCATIONS)
def test_element_icon_keys(location):
    data = cv_button_data(base(), location)
    assert data["cv_icon_class"] == ""
    assert data["cv_icon_inline"] is True


@host_icons
def test_host_label_mode_no_class():
    data = cv_button_data(base(cv_label="Details", cv_label_mode="label"), "card")
    assert data["cv_icon_class"] == ""
    assert data["cv_icon_inline"] is False


@host_icons
def test_menu_item_uses_menu_slot_and_ignores_label_mode():
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"menu:icon-host": "m {name_class}"}):
        data = cv_button_data(base(cv_label="Details", cv_label_mode="label"), "card", kind="menu-item")
    assert data["cv_icon_class"] == "m icon-eye"
    assert data["cv_icon_inline"] is False


@host_icons
def test_host_slot_none_switches_icon_off():
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"context:icon-host": None}):
        data = cv_button_data(base(), "context")
    assert data["cv_icon_class"] == ""
    assert data["cv_icon_inline"] is False


@host_icons
@override_settings(CRUD_VIEWS_STRICT=False)  # icon mode without an icon is a strict error (#264)
def test_host_without_icon():
    data = cv_button_data(base(cv_icon_action=None), "context")
    assert data["cv_icon_class"] == ""
    assert data["cv_icon_inline"] is True


def test_unknown_kind_raises():
    with pytest.raises(ValueError):
        cv_button_data(base(), "context", kind="pill")


# #264: an icon-only action button needs an icon


@pytest.mark.parametrize("location", LOCATIONS)
@pytest.mark.parametrize("icon", [None, ""])
def test_icon_mode_without_icon_raises_strict(location, icon):
    with override_settings(CRUD_VIEWS_STRICT=True), pytest.raises(ValueError, match=r"'detail'.*icon"):
        cv_button_data(base(cv_icon_action=icon, cv_label_mode="icon"), location)


@pytest.mark.parametrize("location", LOCATIONS)
@pytest.mark.parametrize("icon", [None, ""])
def test_icon_mode_without_icon_falls_back_to_label(location, icon, caplog):
    with override_settings(CRUD_VIEWS_STRICT=False):
        data = cv_button_data(base(cv_icon_action=icon, cv_label_mode="icon"), location)
    assert data["cv_label_mode"] == "label"
    assert "cv_title" not in data
    assert data["cv_label"] == "Detail"  # the short label, as for any labelled button
    assert "'detail'" in caplog.text


def test_menu_item_without_icon_untouched():
    with override_settings(CRUD_VIEWS_STRICT=True):
        data = cv_button_data(base(cv_icon_action=None, cv_label_mode="icon"), "context", kind="menu-item")
    assert data["cv_label_mode"] == "icon"


@pytest.mark.parametrize("location", LOCATIONS)
def test_icon_present_unchanged(location):
    with override_settings(CRUD_VIEWS_STRICT=True):
        data = cv_button_data(base(cv_label_mode="icon"), location)
    assert data["cv_label_mode"] == "icon"


@pytest.mark.parametrize("location", LOCATIONS)
@pytest.mark.parametrize("mode", ["label", "both"])
def test_label_and_both_without_icon_untouched(location, mode):
    with override_settings(CRUD_VIEWS_STRICT=True):
        data = cv_button_data(base(cv_icon_action=None, cv_label_mode=mode), location)
    assert data["cv_label_mode"] == mode


def test_empty_label_and_icon_raises_strict():
    ctx = base(cv_icon_action=None, cv_action_label="", cv_action_short_label="", cv_label_mode="label")
    with override_settings(CRUD_VIEWS_STRICT=True), pytest.raises(ValueError, match="'detail'"):
        cv_button_data(ctx, "context")


def test_empty_label_and_icon_stays_icon_and_logs(caplog):
    ctx = base(cv_icon_action=None, cv_action_label="", cv_action_short_label="", cv_label_mode="label")
    with override_settings(CRUD_VIEWS_STRICT=False):
        data = cv_button_data(ctx, "context")
    assert data["cv_label_mode"] == "icon"
    assert "'detail'" in caplog.text


# CRUD_VIEWS_LABEL_MODE_DEFAULTS: the configured floor of an unstamped button, and malformed stamps (LMOD-05)

LABEL_MODE_LOGGER = "crud_views.lib.view.label_mode"
CONFIGURED = {"context": "both", "list": "label", "card": "icon"}


@pytest.fixture
def warned(monkeypatch):
    """A fresh once-per-pair warning register for this test (the production register lives for the process)."""
    from crud_views.lib.view import label_mode

    fresh: set = set()
    monkeypatch.setattr(label_mode, "_warned", fresh)
    return fresh


def _label_mode_records(caplog) -> list:
    return [record for record in caplog.records if record.name == LABEL_MODE_LOGGER]


@pytest.mark.parametrize("location", LOCATIONS)
def test_configured_leaf_floor(location):
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS=CONFIGURED):
        assert cv_button_data(base(), location)["cv_label_mode"] == CONFIGURED[location]
        # an explicit valid stamp wins over the floor
        assert cv_button_data(base(cv_label_mode="both"), location)["cv_label_mode"] == "both"
    # an explicit valid stamp never reads the floor, even an invalid one in strict mode
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={location: "nope"}, CRUD_VIEWS_STRICT=True):
        assert cv_button_data(base(cv_label_mode="label"), location)["cv_label_mode"] == "label"
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={location: "label"}):
        data = cv_button_data(base(), location)
    assert data["cv_label_mode"] == "label"
    assert "cv_title" not in data


@pytest.mark.parametrize("location", LOCATIONS)
@pytest.mark.parametrize("value", [{"filter": "both"}, ["both"], 1, "Both", " both ", "b\u03bfth", "lable"], ids=repr)
def test_invalid_stamped_mode_falls_back(location, value, warned, caplog):
    ctx = base(cv_label="Details", cv_label_mode=value)
    strict = override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS=CONFIGURED, CRUD_VIEWS_STRICT=True)
    with strict, pytest.raises(ValueError, match="cv_label_mode must be one of"):
        cv_button_data(ctx, location)
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS=CONFIGURED, CRUD_VIEWS_STRICT=False):
        # production renders with the configured floor instead of crashing
        assert cv_button_data(ctx, location)["cv_label_mode"] == CONFIGURED[location]
        assert cv_button_data(ctx, location)["cv_label_mode"] == CONFIGURED[location]
    records = _label_mode_records(caplog)
    assert len(records) == 1
    assert "cv_label_mode" in records[0].getMessage()
    assert repr(value) in records[0].getMessage()


@pytest.mark.parametrize("strict", [True, False])
@pytest.mark.parametrize("location", LOCATIONS)
@pytest.mark.parametrize("value", [None, "", [], {}], ids=repr)
def test_falsey_stamped_mode_uses_floor(strict, location, value, warned, caplog):
    # a falsey stamp means unset, as before: the floor, no malformed-stamp warning
    ctx = base(cv_label="Details", cv_label_mode=value)
    with override_settings(CRUD_VIEWS_STRICT=strict):
        assert cv_button_data(ctx, location)["cv_label_mode"] == {"card": "both"}.get(location, "icon")
        with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS=CONFIGURED):
            assert cv_button_data(ctx, location)["cv_label_mode"] == CONFIGURED[location]
    assert _label_mode_records(caplog) == []


@pytest.mark.parametrize("location", LOCATIONS)
def test_strict_stamped_error_precedes_invalid_floor(location):
    # the stamp is named, not the (also malformed) floor it would fall back to
    ctx = base(cv_label="Details", cv_label_mode="Both")
    strict = override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={location: "nope"}, CRUD_VIEWS_STRICT=True)
    with strict, pytest.raises(ValueError, match="cv_label_mode") as excinfo:
        cv_button_data(ctx, location)
    assert "CRUD_VIEWS_LABEL_MODE_DEFAULTS" not in str(excinfo.value)
    assert "'Both'" in str(excinfo.value)


def test_same_bad_pair_warns_once_across_sources(warned, caplog):
    from crud_views.lib.view.label_mode import default_label_mode

    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"context": "Both"}, CRUD_VIEWS_STRICT=False):
        assert default_label_mode("context") == "icon"
        assert len(_label_mode_records(caplog)) == 1
        # the same (location, value) pair reached from a stamp adds nothing
        data = cv_button_data(base(cv_label_mode="Both"), "context")
        assert data["cv_label_mode"] == "icon"
        cv_button_data(base(cv_label_mode="Both"), "context")
        assert len(_label_mode_records(caplog)) == 1
    # nor across a settings change
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"list": "label"}, CRUD_VIEWS_STRICT=False):
        assert cv_button_data(base(cv_label_mode="Both"), "context")["cv_label_mode"] == "icon"
        assert len(_label_mode_records(caplog)) == 1
        # another location or another value is its own pair
        assert cv_button_data(base(cv_label_mode="Both"), "list")["cv_label_mode"] == "label"
        assert len(_label_mode_records(caplog)) == 2
        cv_button_data(base(cv_label_mode="BOTH"), "context")
        assert len(_label_mode_records(caplog)) == 3


RECOVERY_CHILD = """
import unittest

from django.conf import settings

settings.configure(
    INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
    CRUD_VIEWS_STRICT=False,
    CRUD_VIEWS_LABEL_MODE_DEFAULTS={{"context": {floor!r}}},
)

import django

django.setup()

from crud_views.lib.view.button_data import cv_button_data

ctx = {{
    "cv_key": "detail",
    "cv_url": "/author/1/detail/",
    "cv_action_label": "Details",
    "cv_action_short_label": "Detail",
    "cv_icon_action": "detail",
    "cv_list_action_method": "get",
    "cv_oid": "author_detail_1",
    "cv_label_mode": {stamp!r},
}}
with unittest.TestCase().assertLogs("crud_views.lib.view.label_mode", level="WARNING") as logs:
    data = cv_button_data(ctx, "context")
assert data["cv_label_mode"] == "icon", data
assert len(logs.records) == {expected}, logs.output
print("LABEL-MODE-RECOVERY-OK")
"""


@pytest.mark.parametrize(
    "stamp,floor,expected",
    [("Both", "Both", 1), ("Both", "nope", 2), (["both"], ["both"], 1), (["both"], {"x": 1}, 2)],
    ids=["equal", "distinct", "equal-unhashable", "distinct-unhashable"],
)
def test_invalid_stamp_and_floor_recovers_without_deadlock(stamp, floor, expected):
    # a bad stamp falls back to a bad floor, which re-enters the warning helper: must finish, not deadlock
    import subprocess
    import sys

    code = RECOVERY_CHILD.format(stamp=stamp, floor=floor, expected=expected)
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert "LABEL-MODE-RECOVERY-OK" in result.stdout
