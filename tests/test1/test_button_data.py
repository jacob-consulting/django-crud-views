import copy
import logging

import pytest
from django.test import override_settings

from crud_views.lib.view.button_data import FORM_LEAF_KEYS, LEAF_KEYS, cv_button_data
from tests.lib.helper.icons import HOST_ICONS, HOST_LIBRARY

# the action locations; "form" (Phase 6) has its own contract, tested below
ACTION_LOCATIONS = ["context", "list", "card"]


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


@pytest.mark.parametrize("location", ACTION_LOCATIONS)
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


@pytest.mark.parametrize("location", ACTION_LOCATIONS)
def test_post_without_modal(location):
    data = cv_button_data(base(cv_list_action_method="post"), location)
    assert data["cv_tag"] == "button"
    assert data["cv_submit_target"] == "cv_form_o1"
    assert "cv_href" not in data


@pytest.mark.parametrize("location", ACTION_LOCATIONS)
def test_post_with_modal(location):
    data = cv_button_data(base(cv_list_action_method="post", cv_modal=True, cv_modal_size="lg"), location)
    assert data["cv_tag"] == "a"
    assert data["cv_href"] == "/u/"
    assert data["cv_modal"] is True
    assert data["cv_modal_size"] == "lg"
    assert "cv_submit_target" not in data


@pytest.mark.parametrize("location", ACTION_LOCATIONS)
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


@pytest.mark.parametrize("location", ACTION_LOCATIONS)
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


@pytest.mark.parametrize("location", ACTION_LOCATIONS)
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


@pytest.mark.parametrize("location", ACTION_LOCATIONS)
def test_variant_defaults_to_secondary(location):
    ctx = base()
    del ctx["cv_variant"]
    assert cv_button_data(ctx, location)["cv_variant"] == "secondary"


def test_invalid_location():
    with pytest.raises(ValueError):
        cv_button_data(base(), "toolbar")


@pytest.mark.parametrize("location", ACTION_LOCATIONS)
def test_pure_and_within_leaf_keys(location):
    ctx = base(cv_list_action_method="post", cv_modal=True, cv_is_active=True, cv_flex=True)
    before = copy.deepcopy(ctx)
    data = cv_button_data(ctx, location)
    assert ctx == before
    assert set(data) <= LEAF_KEYS


# host-placed icons (#258)

host_icons = override_settings(CRUD_VIEWS_ICON_LIBRARIES=HOST_LIBRARY, CRUD_VIEWS_ICONS=HOST_ICONS)


@host_icons
@pytest.mark.parametrize("location", ACTION_LOCATIONS)
def test_host_icon_keys(location):
    data = cv_button_data(base(), location)
    assert data["cv_icon_class"] == "icon-eye"
    assert data["cv_icon_inline"] is False


@pytest.mark.parametrize("location", ACTION_LOCATIONS)
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


@pytest.mark.parametrize("location", ACTION_LOCATIONS)
@pytest.mark.parametrize("icon", [None, ""])
def test_icon_mode_without_icon_raises_strict(location, icon):
    with override_settings(CRUD_VIEWS_STRICT=True), pytest.raises(ValueError, match=r"'detail'.*icon"):
        cv_button_data(base(cv_icon_action=icon, cv_label_mode="icon"), location)


@pytest.mark.parametrize("location", ACTION_LOCATIONS)
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


@pytest.mark.parametrize("location", ACTION_LOCATIONS)
def test_icon_present_unchanged(location):
    with override_settings(CRUD_VIEWS_STRICT=True):
        data = cv_button_data(base(cv_label_mode="icon"), location)
    assert data["cv_label_mode"] == "icon"


@pytest.mark.parametrize("location", ACTION_LOCATIONS)
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


def _label_mode_records(caplog) -> list:
    return [record for record in caplog.records if record.name == LABEL_MODE_LOGGER]


@pytest.mark.parametrize("location", ACTION_LOCATIONS)
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


@pytest.mark.parametrize("location", ACTION_LOCATIONS)
@pytest.mark.parametrize("value", [{"filter": "both"}, ["both"], 1, "Both", " both ", "b\u03bfth", "lable"], ids=repr)
def test_invalid_stamped_mode_falls_back(location, value, caplog):
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
@pytest.mark.parametrize("location", ACTION_LOCATIONS)
@pytest.mark.parametrize("value", [None, "", [], {}], ids=repr)
def test_falsey_stamped_mode_uses_floor(strict, location, value, caplog):
    # a falsey stamp means unset, as before: the floor, no malformed-stamp warning
    ctx = base(cv_label="Details", cv_label_mode=value)
    with override_settings(CRUD_VIEWS_STRICT=strict):
        assert cv_button_data(ctx, location)["cv_label_mode"] == {"card": "both"}.get(location, "icon")
        with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS=CONFIGURED):
            assert cv_button_data(ctx, location)["cv_label_mode"] == CONFIGURED[location]
    assert _label_mode_records(caplog) == []


@pytest.mark.parametrize("location", ACTION_LOCATIONS)
def test_strict_stamped_error_precedes_invalid_floor(location):
    # the stamp is named, not the (also malformed) floor it would fall back to
    ctx = base(cv_label="Details", cv_label_mode="Both")
    strict = override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={location: "nope"}, CRUD_VIEWS_STRICT=True)
    with strict, pytest.raises(ValueError, match="cv_label_mode") as excinfo:
        cv_button_data(ctx, location)
    assert "CRUD_VIEWS_LABEL_MODE_DEFAULTS" not in str(excinfo.value)
    assert "'Both'" in str(excinfo.value)


def test_same_bad_pair_warns_once_across_sources(caplog):
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


# --- the form location (Phase 6, D-13/D-14): a separate finite contract -----------------------------------------

FORM_TYPES = {
    "submit": "submit",
    "cancel": "button",
    "delete": "submit",
    "filter-submit": "submit",
    "filter-reset": "reset",
}
# keys only an action / menu item has; a form result never carries them
ACTION_ONLY_KEYS = LEAF_KEYS - FORM_LEAF_KEYS


def form_ctx(key="submit", **kw):
    # an available icon by default: an icon-mode form button without one is the missing-icon policy (06-06,
    # tests/test1/test_form_button_checks.py), not the contract these tests pin
    ctx = {
        "cv_key": key,
        "cv_type": FORM_TYPES[key],
        "cv_name": "submit",
        "cv_value": "Save",
        "cv_id": "submit-id-submit",
        "cv_icon": "save",
    }
    ctx.update(kw)
    return ctx


def test_form_location_contract_constants():
    from crud_views.lib.button_classes import FORM_KINDS, VARIANT_LOCATIONS
    from crud_views.lib.view.button_data import LOCATIONS

    assert set(FORM_TYPES) == FORM_KINDS
    assert VARIANT_LOCATIONS | {"form"} == LOCATIONS
    assert set(ACTION_LOCATIONS) == VARIANT_LOCATIONS
    assert {
        "cv_location",
        "cv_key",
        "cv_type",
        "cv_name",
        "cv_value",
        "cv_label",
        "cv_id",
        "cv_label_mode",
        "cv_icon",
        "cv_icon_class",
        "cv_icon_inline",
        "cv_css_class",
        "cv_flat_attrs",
        "cv_title",
        "cv_cancel_url",
    } == FORM_LEAF_KEYS
    assert "cv_tag" not in FORM_LEAF_KEYS


@pytest.mark.parametrize("key", sorted(FORM_TYPES))
def test_form_default_and_explicit_action_kind_are_identical(key):
    ctx = form_ctx(key)
    assert cv_button_data(ctx, "form") == cv_button_data(ctx, "form", "action")
    assert cv_button_data(ctx, "form", kind="action") == cv_button_data(ctx, "form")


@pytest.mark.parametrize("strict", [True, False])
@pytest.mark.parametrize("kind", ["menu-item", "pill", "submit", "cancel", ""])
@pytest.mark.parametrize("key", sorted(FORM_TYPES))
def test_form_rejects_a_non_action_third_kind(key, kind, strict):
    # the third argument is the rendering category, not the semantic form kind: only cv_key selects that
    with override_settings(CRUD_VIEWS_STRICT=strict), pytest.raises(ValueError, match="kind"):
        cv_button_data(form_ctx(key), "form", kind)


@pytest.mark.parametrize("strict", [True, False])
@pytest.mark.parametrize("kind", ["action", "menu-item"])
@pytest.mark.parametrize("location", ACTION_LOCATIONS)
def test_action_locations_keep_both_kinds(location, kind, strict):
    with override_settings(CRUD_VIEWS_STRICT=strict):
        data = cv_button_data(base(), location, kind)
    assert set(data) <= LEAF_KEYS
    assert data["cv_location"] == location


@pytest.mark.parametrize("strict", [True, False])
@pytest.mark.parametrize("location", ACTION_LOCATIONS)
def test_action_locations_reject_unknown_kind(location, strict):
    with override_settings(CRUD_VIEWS_STRICT=strict), pytest.raises(ValueError, match="kind"):
        cv_button_data(base(), location, "pill")


@pytest.mark.parametrize("strict", [True, False])
@pytest.mark.parametrize("bad", ["primary", "detail", "hidden-label", "icon-host", "", None, "Submit"])
def test_form_rejects_unknown_cv_key(bad, strict):
    with override_settings(CRUD_VIEWS_STRICT=strict), pytest.raises(ValueError, match="cv_key"):
        cv_button_data(form_ctx(cv_key=bad), "form")
    ctx = form_ctx()
    del ctx["cv_key"]
    with pytest.raises(ValueError, match="cv_key"):
        cv_button_data(ctx, "form")


@pytest.mark.parametrize("strict", [True, False])
@pytest.mark.parametrize("bad", ["image", "hidden", "", None, "Submit", "text"])
def test_form_rejects_unknown_cv_type(bad, strict):
    with override_settings(CRUD_VIEWS_STRICT=strict), pytest.raises(ValueError, match="cv_type"):
        cv_button_data(form_ctx(cv_type=bad), "form")
    # an invalid semantic field raises whatever the third argument says
    with pytest.raises(ValueError):
        cv_button_data(form_ctx(cv_type=bad), "form", "menu-item")


@pytest.mark.parametrize("key", sorted(FORM_TYPES))
@pytest.mark.parametrize("mode", ["label", "both", "icon"])
def test_form_result_keys_and_presence(key, mode):
    data = cv_button_data(form_ctx(key, cv_label_mode=mode, data_cv_cancel_url="/x/"), "form")
    assert set(data) <= FORM_LEAF_KEYS
    assert not set(data) & ACTION_ONLY_KEYS
    required = FORM_LEAF_KEYS - {"cv_title", "cv_cancel_url"}
    assert required <= set(data)
    assert ("cv_title" in data) is (mode == "icon")
    assert ("cv_cancel_url" in data) is (key == "cancel")
    assert data["cv_location"] == "form"
    assert data["cv_key"] == key
    assert data["cv_type"] == FORM_TYPES[key]
    assert data["cv_label_mode"] == mode


def test_form_default_mode_is_the_lazy_form_floor():
    assert cv_button_data(form_ctx(), "form")["cv_label_mode"] == "label"
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"form": "icon"}):
        data = cv_button_data(form_ctx(), "form")
        assert data["cv_label_mode"] == "icon"
        assert data["cv_title"] == "Save"
        with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"form": "both"}):
            assert cv_button_data(form_ctx(), "form")["cv_label_mode"] == "both"
    # other locations' floors never reach the form
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"context": "icon", "card": "icon", "list": "icon"}):
        assert cv_button_data(form_ctx(), "form")["cv_label_mode"] == "label"
    assert cv_button_data(form_ctx(), "form")["cv_label_mode"] == "label"


def test_form_invalid_mode_stamp(caplog):
    with override_settings(CRUD_VIEWS_STRICT=True), pytest.raises(ValueError, match="cv_label_mode"):
        cv_button_data(form_ctx(cv_label_mode="Both"), "form")
    with override_settings(CRUD_VIEWS_STRICT=False):
        assert cv_button_data(form_ctx(cv_label_mode="Both"), "form")["cv_label_mode"] == "label"
    assert any("'Both'" in r.getMessage() for r in caplog.records)


def test_form_values_are_exact_plain_strings():
    from django.utils.safestring import SafeData, mark_safe
    from django.utils.translation import gettext_lazy

    data = cv_button_data(
        form_ctx(cv_name=mark_safe("go"), cv_value=mark_safe("<b>x</b>"), cv_id=gettext_lazy("an-id")), "form"
    )
    for field in ("cv_name", "cv_value", "cv_label", "cv_id", "cv_css_class"):
        assert type(data[field]) is str, field
        assert not isinstance(data[field], SafeData), field
    assert data["cv_value"] == data["cv_label"] == "<b>x</b>"
    assert data["cv_id"] == "an-id"


def test_form_missing_none_and_falsey_values():
    ctx = {"cv_key": "submit", "cv_type": "submit"}
    data = cv_button_data(ctx, "form")
    assert (data["cv_name"], data["cv_value"], data["cv_label"], data["cv_id"]) == ("", "", "", "")
    data = cv_button_data(form_ctx(cv_value=None, cv_name=None, cv_id=None), "form")
    assert (data["cv_name"], data["cv_value"], data["cv_label"], data["cv_id"]) == ("", "", "", "")
    data = cv_button_data(form_ctx(cv_value=0), "form")
    assert (data["cv_value"], data["cv_label"]) == ("0", "0")
    data = cv_button_data(form_ctx(cv_value=False), "form")
    assert data["cv_value"] == "False"
    # a valid empty label stays empty: no text is manufactured from the name or the kind
    data = cv_button_data(form_ctx(cv_value="", cv_label_mode="label"), "form")
    assert (data["cv_value"], data["cv_label"], data["cv_label_mode"]) == ("", "", "label")
    data = cv_button_data(form_ctx(cv_value="v", cv_label=""), "form")
    assert (data["cv_value"], data["cv_label"]) == ("v", "")
    data = cv_button_data(form_ctx(cv_value="v", cv_label=None), "form")
    assert data["cv_label"] == ""


@pytest.mark.parametrize(
    "name,emitted",
    [
        ("submit", "submit"),
        ("reset", "reset"),
        ("a.b!", "a.b!"),
        ("Search the Site", "search-the-site"),
        ("Search  the Site!", "search-the-site"),
        ("Ünïcode name", "unicode-name"),
    ],
)
def test_form_emitted_name_follows_crispy_wordcount_rule(name, emitted):
    assert cv_button_data(form_ctx(cv_name=name), "form")["cv_name"] == emitted


def test_form_attrs_reserved_and_aliases():
    data = cv_button_data(
        form_ctx(
            "submit",
            cv_css_class="extra",
            cv_attrs={
                "data_x": "u",
                "data-x": "h",
                "type": "image",
                "name": "evil",
                "value": "evil",
                "class": "more",
                "aria_label": 'a "q"',
                "formnovalidate": True,
                "hidden": False,
                "none": None,
            },
        ),
        "form",
    )
    flat = str(data["cv_flat_attrs"])
    assert flat.count("data-x=") == 1 and 'data-x="h"' in flat
    assert "type=" not in flat and "name=" not in flat and "value=" not in flat and "class=" not in flat
    assert 'aria-label="a &quot;q&quot;"' in flat
    assert " formnovalidate" in flat
    assert "hidden" not in flat and "none" not in flat
    assert data["cv_css_class"] == "extra more"
    assert data["cv_type"] == "submit"


@pytest.mark.parametrize(
    "ctx,expected",
    [
        ({"cv_id": "gen"}, "gen"),
        ({"cv_id": "gen", "cv_attrs": {"id": "extra"}}, "extra"),
        ({"cv_id": "css", "cv_css_id": "css", "cv_attrs": {"id": "extra"}}, "css"),
        ({"cv_id": "gen", "cv_attrs": {"id": None}}, "gen"),
    ],
)
def test_form_id_precedence(ctx, expected):
    data = cv_button_data(form_ctx(**ctx), "form")
    assert data["cv_id"] == expected
    assert "id=" not in str(data["cv_flat_attrs"])


@pytest.mark.parametrize("key", ["cancel", "submit"])
def test_form_hyphen_spelling_wins_in_any_order(key):
    for attrs in (
        {"data_x": "u", "data-x": "h", "data_cv_cancel_url": "/u/", "data-cv-cancel-url": "/h/"},
        {"data-x": "h", "data_x": "u", "data-cv-cancel-url": "/h/", "data_cv_cancel_url": "/u/"},
    ):
        data = cv_button_data(form_ctx(key, cv_attrs=attrs), "form")
        flat = str(data["cv_flat_attrs"])
        assert 'data-x="h"' in flat and flat.count("data-x=") == 1
        if key == "cancel":
            assert data["cv_cancel_url"] == "/h/"
        else:
            assert 'data-cv-cancel-url="/h/"' in flat and flat.count("data-cv-cancel-url=") == 1


def test_form_cancel_url_only_for_cancel():
    data = cv_button_data(
        form_ctx("cancel", cv_attrs={"data_cv_cancel_url": "/u/", "data-cv-cancel-url": "/h/"}), "form"
    )
    assert data["cv_cancel_url"] == "/h/"
    assert "cancel-url" not in str(data["cv_flat_attrs"])
    data = cv_button_data(form_ctx("cancel"), "form")
    assert data["cv_cancel_url"] is None
    # any other kind keeps it an ordinary escaped extra attribute
    data = cv_button_data(form_ctx("submit", cv_attrs={"data_cv_cancel_url": "/a?b=1&c=2"}), "form")
    assert "cv_cancel_url" not in data
    assert 'data-cv-cancel-url="/a?b=1&amp;c=2"' in str(data["cv_flat_attrs"])


@pytest.mark.parametrize("mode", ["label", "both", "icon"])
def test_form_title_and_tooltip_collisions(mode):
    data = cv_button_data(form_ctx(cv_label_mode=mode, cv_attrs={"title": "T", "data_cv_tooltip": "x"}), "form")
    flat = str(data["cv_flat_attrs"])
    if mode == "icon":
        assert data["cv_title"] == "Save"
        assert "title=" not in flat and "data-cv-tooltip" not in flat
    else:
        assert "cv_title" not in data
        assert 'title="T"' in flat and 'data-cv-tooltip="x"' in flat


host_icons_form = override_settings(CRUD_VIEWS_ICON_LIBRARIES=HOST_LIBRARY, CRUD_VIEWS_ICONS=HOST_ICONS)


@host_icons_form
@pytest.mark.parametrize("mode", ["label", "both", "icon"])
def test_form_host_icon_classes(mode):
    data = cv_button_data(form_ctx(cv_label_mode=mode, cv_icon="update"), "form")
    if mode == "label":
        assert (data["cv_icon_class"], data["cv_icon_inline"]) == ("", True)
    else:
        assert (data["cv_icon_class"], data["cv_icon_inline"]) == ("icon-edit", False)
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"form:icon-host": "icon {name_class}"}):
        if mode != "label":
            assert cv_button_data(form_ctx(cv_label_mode=mode, cv_icon="update"), "form")["cv_icon_class"] == (
                "icon icon-edit"
            )


@pytest.mark.parametrize("mode", ["label", "both", "icon"])
def test_form_element_icon(mode):
    data = cv_button_data(form_ctx(cv_label_mode=mode, cv_icon="detail"), "form")
    assert data["cv_icon"] == "detail"
    assert (data["cv_icon_class"], data["cv_icon_inline"]) == ("", True)


def test_form_never_mutates_ctx():
    ctx = form_ctx("cancel", cv_attrs={"data_cv_cancel_url": "/u/", "id": "x", "class": "c"}, cv_css_class="e")
    before = copy.deepcopy(ctx)
    cv_button_data(ctx, "form")
    cv_button_data(ctx, "form")
    assert ctx == before


def test_form_floor_is_read_per_normalization():
    ctx = form_ctx()
    seen = []
    for floor in ({}, {"form": "icon"}, {"form": "both"}, {"form": "icon", "card": "label"}, {}):
        with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS=floor):
            seen.append(cv_button_data(ctx, "form")["cv_label_mode"])
    assert seen == ["label", "icon", "both", "icon", "label"]


@pytest.mark.parametrize("mode", ["label", "both", "icon"])
def test_form_explicit_mode_never_reads_an_invalid_strict_floor(mode):
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"form": "nope"}, CRUD_VIEWS_STRICT=True):
        assert cv_button_data(form_ctx(cv_label_mode=mode), "form")["cv_label_mode"] == mode
        with pytest.raises(ValueError, match="key 'form'"):
            cv_button_data(form_ctx(), "form")


def test_form_invalid_floor_non_strict_falls_back_to_label(caplog):
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"form": "nope"}, CRUD_VIEWS_STRICT=False):
        assert cv_button_data(form_ctx(), "form")["cv_label_mode"] == "label"
        assert cv_button_data(form_ctx(), "form")["cv_label_mode"] == "label"
    assert len([r for r in caplog.records if "'form'" in r.getMessage()]) == 1


# --- the form icon type contract (06-10: WR-02): cv_icon is a nonblank str or None -----------------------------------

BUTTON_LOGGER = "crud_views.lib.view.button_data"
_NO_ICON = object()  # the cv_icon key is absent

# never a usable icon: not a str, or a str that is blank; each normalizes to None before the missing-icon policy
INVALID_ICONS = [
    pytest.param(_NO_ICON, id="missing"),
    pytest.param(None, id="none"),
    pytest.param("", id="empty"),
    pytest.param("   ", id="spaces"),
    pytest.param(" \t\n ", id="tab-newline"),
    pytest.param(object(), id="object"),
    pytest.param(True, id="true"),
    pytest.param(False, id="false"),
    pytest.param(1, id="one"),
    pytest.param(0, id="zero"),
    pytest.param(b"save", id="bytes"),
    pytest.param(["save"], id="list"),
    pytest.param({"save": "save"}, id="dict"),
]


def _icon_ctx(icon, key="submit", **kw) -> dict:
    ctx = form_ctx(key, **kw)
    if icon is _NO_ICON:
        del ctx["cv_icon"]
    else:
        ctx["cv_icon"] = icon
    return ctx


def _warnings(caplog) -> list[str]:
    return [r.getMessage() for r in caplog.records if r.levelno >= logging.WARNING]


@pytest.mark.parametrize("strict", [True, False], ids=["strict", "lenient"])
@pytest.mark.parametrize("mode", ["label", "both"])
@pytest.mark.parametrize("icon", INVALID_ICONS)
def test_form_icon_normalization_label_and_both_are_quiet(icon, mode, strict, caplog):
    caplog.set_level(logging.DEBUG)
    with override_settings(CRUD_VIEWS_STRICT=strict):
        data = cv_button_data(_icon_ctx(icon, cv_label_mode=mode), "form")
    assert data["cv_icon"] is None
    assert data["cv_label_mode"] == mode
    assert (data["cv_icon_class"], data["cv_icon_inline"]) == ("", True)
    assert "cv_title" not in data
    assert _warnings(caplog) == []


@pytest.mark.parametrize("key", sorted(FORM_TYPES))
@pytest.mark.parametrize("icon", INVALID_ICONS)
def test_form_icon_normalization_strict_icon_mode_raises_naming_none(icon, key):
    with override_settings(CRUD_VIEWS_STRICT=True), pytest.raises(ValueError) as info:
        cv_button_data(_icon_ctx(icon, key, cv_label_mode="icon"), "form")
    message = str(info.value)
    assert f"form button {key!r} renders icon-only but its icon None is not available" in message
    assert "object at" not in message


@pytest.mark.parametrize("icon", INVALID_ICONS)
def test_form_icon_normalization_lenient_icon_mode_logs_and_uses_the_label(icon, caplog):
    caplog.set_level(logging.WARNING, logger=BUTTON_LOGGER)
    ctx = _icon_ctx(icon, "filter-submit", cv_label_mode="icon", cv_value="Go")
    with override_settings(CRUD_VIEWS_STRICT=False):
        first = cv_button_data(ctx, "form")
        second = cv_button_data(ctx, "form")
    # one warning per render, naming None
    assert (
        _warnings(caplog)
        == [
            "form button 'filter-submit' renders icon-only but its icon None is not available; rendered with its label"
            " instead"
        ]
        * 2
    )
    assert first == second
    assert first["cv_label_mode"] == "label" and first["cv_icon"] is None
    assert (first["cv_icon_class"], first["cv_icon_inline"]) == ("", True)
    assert "cv_title" not in first and first["cv_label"] == "Go"
    assert "data-cv-tooltip" not in str(first["cv_flat_attrs"])


@pytest.mark.parametrize("icon", INVALID_ICONS)
def test_form_icon_normalization_lenient_without_a_label_keeps_the_empty_path(icon, caplog):
    caplog.set_level(logging.WARNING, logger=BUTTON_LOGGER)
    with override_settings(CRUD_VIEWS_STRICT=False):
        data = cv_button_data(_icon_ctx(icon, cv_label_mode="icon", cv_value="", cv_label=""), "form")
    assert (data["cv_label"], data["cv_value"], data["cv_label_mode"], data["cv_icon"]) == ("", "", "label", None)
    assert _warnings(caplog) == [
        "form button 'submit' has neither an available icon (None) nor a label and renders empty"
    ]


@pytest.mark.parametrize("mode", ["label", "both", "icon"])
@pytest.mark.parametrize("icon", ["save", " save ", "\tfilter\n", "fas:rocket", "my-raw icon-save"])
def test_form_icon_normalization_keeps_nonblank_strings_exactly(icon, mode, caplog):
    caplog.set_level(logging.WARNING, logger=BUTTON_LOGGER)
    with override_settings(CRUD_VIEWS_STRICT=False):
        data = cv_button_data(_icon_ctx(icon, cv_label_mode=mode), "form")
    if data["cv_label_mode"] == mode:
        # usable (or not consulted outside icon mode): the very string, never stripped or replaced
        assert data["cv_icon"] is icon
    else:
        # an unavailable nonblank string in icon mode keeps the existing missing-icon policy and its value
        assert mode == "icon" and data["cv_label_mode"] == "label"
        assert data["cv_icon"] is icon
        assert _warnings(caplog) == [
            f"form button 'submit' renders icon-only but its icon {icon!r} is not available; rendered with its label"
            " instead"
        ]


@pytest.mark.parametrize("strict", [True, False], ids=["strict", "lenient"])
def test_form_icon_normalization_unavailable_nonblank_string_is_not_none(strict, caplog):
    """A nonblank string that does not resolve stays the caller's value: the missing-icon policy names it."""
    ctx = _icon_ctx("unknown:save", cv_label_mode="icon")
    with override_settings(CRUD_VIEWS_STRICT=strict):
        if strict:
            with pytest.raises(ValueError, match=r"its icon 'unknown:save' is not available"):
                cv_button_data(ctx, "form")
        else:
            assert cv_button_data(ctx, "form")["cv_icon"] == "unknown:save"
    with override_settings(CRUD_VIEWS_STRICT=strict):
        assert cv_button_data({**ctx, "cv_label_mode": "both"}, "form")["cv_icon"] == "unknown:save"


@pytest.mark.parametrize("icon", [["save"], {"save": "save"}, b"save", "   "], ids=["list", "dict", "bytes", "blank"])
def test_form_icon_normalization_never_mutates_the_input(icon):
    ctx = _icon_ctx(icon, cv_label_mode="both")
    before = copy.deepcopy(ctx)
    for _ in range(2):
        assert cv_button_data(ctx, "form")["cv_icon"] is None
    assert ctx == before
    assert ctx["cv_icon"] is icon
