import pytest
from django.conf import settings
from django.test import override_settings

from crud_views.lib.view import label_mode
from crud_views.lib.view.button_data import LOCATIONS
from crud_views.lib.view.label_mode import (
    LABEL_MODE_DEFAULTS,
    LABEL_MODES,
    LabelMode,
    default_label_mode,
    is_label_mode,
    label_mode_check,
)

LOGGER = "crud_views.lib.view.label_mode"
PACKAGE = {"context": "icon", "list": "icon", "card": "both"}


def test_label_modes():
    assert sorted(LABEL_MODES) == ["both", "icon", "label"]
    assert sorted(LABEL_MODES) == sorted(mode.value for mode in LabelMode)
    assert LabelMode.LABEL == "label"
    assert LabelMode.ICON == "icon"
    assert LabelMode.BOTH == "both"


@pytest.mark.parametrize("value", ["label", "icon", "both"])
def test_is_label_mode_true(value):
    assert is_label_mode(value) is True


@pytest.mark.parametrize("value", ["Both", "", None, True, "no_label"])
def test_is_label_mode_false(value):
    assert is_label_mode(value) is False


def test_label_mode_check_message():
    check = label_mode_check(object(), "card action 'detail'", "nope")
    assert check.expression is False
    assert "card action 'detail'" in check.msg
    assert "'nope'" in check.msg


# CRUD_VIEWS_LABEL_MODE_DEFAULTS: the per-location floor, merged per key over the package defaults


@pytest.fixture
def warned(monkeypatch):
    """A fresh once-per-pair warning register for this test (the production register lives for the process)."""
    fresh: set = set()
    monkeypatch.setattr(label_mode, "_warned", fresh)
    return fresh


@pytest.fixture
def no_setting():
    """CRUD_VIEWS_LABEL_MODE_DEFAULTS absent, whatever the test settings say."""
    with override_settings():
        del settings.CRUD_VIEWS_LABEL_MODE_DEFAULTS
        yield


def _resolved() -> dict:
    return {location: default_label_mode(location) for location in sorted(LOCATIONS)}


def _records(caplog) -> list:
    return [record for record in caplog.records if record.name == LOGGER]


def test_defaults_match_locations():
    assert set(LABEL_MODE_DEFAULTS) == LOCATIONS
    assert dict(LABEL_MODE_DEFAULTS) == PACKAGE
    assert all(is_label_mode(mode) for mode in LABEL_MODE_DEFAULTS.values())
    with pytest.raises(TypeError):
        LABEL_MODE_DEFAULTS["card"] = "label"  # type: ignore[index]
    with pytest.raises(TypeError):
        del LABEL_MODE_DEFAULTS["card"]  # type: ignore[attr-defined]
    assert dict(LABEL_MODE_DEFAULTS) == PACKAGE


def test_default_label_mode_absent_setting(no_setting):
    assert _resolved() == PACKAGE


@pytest.mark.parametrize(
    "configured,expected",
    [
        ({}, PACKAGE),
        ({"context": "both"}, {**PACKAGE, "context": "both"}),
        ({"list": "label"}, {**PACKAGE, "list": "label"}),
        ({"card": "icon"}, {**PACKAGE, "card": "icon"}),
        # an override equal to its package value replaces only that entry and changes nothing
        ({"card": "both"}, PACKAGE),
        ({"context": "icon"}, PACKAGE),
        ({"context": "label", "list": "both", "card": "label"}, {"context": "label", "list": "both", "card": "label"}),
        # an unknown key (E108 reports it) is ignored at render
        ({"cotext": "both"}, PACKAGE),
        ({"form": "label", "list": "both"}, {**PACKAGE, "list": "both"}),
    ],
)
def test_default_label_mode_merge(configured, expected):
    supplied = dict(configured)
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS=supplied):
        assert _resolved() == expected
    assert supplied == configured
    assert dict(LABEL_MODE_DEFAULTS) == PACKAGE


@pytest.mark.parametrize(
    "configured",
    [
        {"context": "label", "list": "both", "card": "icon"},
        {"context": "both", "card": "label"},
        {"list": "label", "cotext": "both"},
    ],
)
def test_default_label_mode_order_independent(configured):
    reversed_order = dict(reversed(list(configured.items())))
    assert list(reversed_order) != list(configured)
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS=configured):
        forward = _resolved()
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS=reversed_order):
        backward = _resolved()
    assert forward == backward


def test_default_label_mode_override_settings(no_setting):
    # read at call time: override_settings applies at once and exiting restores the previous result (LMOD-04)
    assert default_label_mode("context") == "icon"
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"context": "both"}):
        assert default_label_mode("context") == "both"
        with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"context": "label", "card": "icon"}):
            assert default_label_mode("context") == "label"
            assert default_label_mode("card") == "icon"
        assert default_label_mode("context") == "both"
        assert default_label_mode("card") == "both"
    assert _resolved() == PACKAGE


@pytest.mark.parametrize("strict", [True, False])
@pytest.mark.parametrize("location", ["toolbar", "form", "filter", "", "Context"])
def test_default_label_mode_invalid_location(strict, location):
    # a wrong location argument is a caller bug, not configuration: it raises in every mode
    with override_settings(CRUD_VIEWS_STRICT=strict), pytest.raises(ValueError, match="location must be one of"):
        default_label_mode(location)


WHOLE_SETTING_INVALID = [None, "", [], ["both"], 1, "Both", " both ", "b\u03bfth"]
PER_LOCATION_INVALID = [None, "", [], {}, {"filter": "both"}, ["both"], 1, "Both", " both ", "b\u03bfth"]


@pytest.mark.parametrize("configured", WHOLE_SETTING_INVALID, ids=repr)
def test_default_label_mode_invalid_setting_whole(configured, warned, caplog):
    strict = override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS=configured, CRUD_VIEWS_STRICT=True)
    with strict, pytest.raises(ValueError, match="CRUD_VIEWS_LABEL_MODE_DEFAULTS must be a dict"):
        default_label_mode("context")
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS=configured, CRUD_VIEWS_STRICT=False):
        assert _resolved() == PACKAGE
    assert len(_records(caplog)) == 3  # one per location queried


@pytest.mark.parametrize("value", PER_LOCATION_INVALID, ids=repr)
def test_default_label_mode_invalid_setting(value, warned, caplog):
    configured = {"context": value, "list": "label"}
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS=configured, CRUD_VIEWS_STRICT=True):
        with pytest.raises(ValueError, match="CRUD_VIEWS_LABEL_MODE_DEFAULTS key 'context' must be one of"):
            default_label_mode("context")
        # only the requested location is validated at render
        assert default_label_mode("list") == "label"
        assert default_label_mode("card") == "both"
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS=configured, CRUD_VIEWS_STRICT=False):
        # the package default for that location, never the setting's other entries
        assert default_label_mode("context") == "icon"
        assert default_label_mode("list") == "label"
    records = _records(caplog)
    assert len(records) == 1
    assert records[0].levelname == "WARNING"
    assert repr(value) in records[0].getMessage()
    assert "'context'" in records[0].getMessage()


def test_default_label_mode_warns_once(warned, caplog):
    # a non-dict setting: one warning per distinct location queried, repeats add none
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS="both", CRUD_VIEWS_STRICT=False):
        counts = []
        for location in ("context", "list", "card"):
            for _ in range(2):
                assert default_label_mode(location) == PACKAGE[location]
            counts.append(len(_records(caplog)))
    assert counts == [1, 2, 3]

    # a bad per-location value: once per (location, value) pair, also across settings changes
    caplog.clear()
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"card": "nope"}, CRUD_VIEWS_STRICT=False):
        for _ in range(3):
            assert default_label_mode("card") == "both"
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"card": "nope", "list": "label"}, CRUD_VIEWS_STRICT=False):
        assert default_label_mode("card") == "both"
    assert len(_records(caplog)) == 1

    # a different value or a different location warns again
    with override_settings(
        CRUD_VIEWS_LABEL_MODE_DEFAULTS={"card": "nope2", "context": "nope"}, CRUD_VIEWS_STRICT=False
    ):
        default_label_mode("card")
        default_label_mode("context")
        default_label_mode("card")
        default_label_mode("context")
    assert len(_records(caplog)) == 3


@pytest.mark.parametrize("mode", ["label", "icon", "both"])
def test_default_label_mode_exact_strings_valid(mode):
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"list": mode}, CRUD_VIEWS_STRICT=True):
        assert default_label_mode("list") == mode


@pytest.mark.parametrize(
    "value", ["Both", "BOTH", " both ", "both\n", "b\u03bfth", "ic\u043en", "label\u200b"], ids=repr
)
def test_default_label_mode_exact_strings(value, warned, caplog):
    # modes are exact, case-sensitive strings: no strip, no casefold, no Unicode normalisation
    strict = override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"list": value}, CRUD_VIEWS_STRICT=True)
    with strict, pytest.raises(ValueError, match=r"key 'list' must be one of \['both', 'icon', 'label'\]"):
        default_label_mode("list")
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"list": value}, CRUD_VIEWS_STRICT=False):
        assert default_label_mode("list") == "icon"
    assert len(_records(caplog)) == 1
