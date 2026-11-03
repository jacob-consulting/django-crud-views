import json
from collections import UserDict

import pytest
from pydantic import ValidationError

from crud_views.lib.view import CardAction


def test_label_mode_defaults_to_none():
    assert CardAction(key="detail").label_mode is None


@pytest.mark.parametrize("mode", ["label", "icon", "both"])
def test_label_mode_accepted(mode):
    assert CardAction(key="detail", label_mode=mode).label_mode == mode


def test_unknown_label_mode_rejected():
    with pytest.raises(ValidationError, match="label_mode"):
        CardAction(key="detail", label_mode="nope")


@pytest.mark.parametrize("entry", ["constructor", "mapping", "json"])
@pytest.mark.parametrize("value", [True, False, None, "", 0, "icon"])
@pytest.mark.parametrize("mode", [None, "label", "icon", "both"])
def test_removed_no_label_presence_rejected(entry, value, mode):
    data = {"key": "detail", "no_label": value}
    if mode is not None:
        data["label_mode"] = mode
    with pytest.raises(ValidationError) as error:
        if entry == "constructor":
            CardAction(**data)
        elif entry == "mapping":
            CardAction.model_validate(UserDict(data))
        else:
            CardAction.model_validate_json(json.dumps(data))
    assert "CardAction.no_label" in str(error.value)
    assert 'label_mode="icon"' in str(error.value)


def test_removed_alias_absent_from_fields_schema_and_dump():
    action = CardAction(key="detail")
    assert "no_label" not in CardAction.model_fields
    assert "no_label" not in CardAction.model_json_schema()["properties"]
    assert "no_label" not in action.model_dump()
    assert not hasattr(action, "no_label")


@pytest.mark.parametrize("key", ["unrelated", "", "NO_LABEL", "no_label ", "no_labe\u0131", "cv_no_label"])
def test_unrelated_extra_policy_preserved(key):
    data = {"key": "detail", key: True}
    expected = CardAction(key="detail")
    assert CardAction(**data) == expected
    assert CardAction.model_validate(UserDict(data)) == expected
    assert CardAction.model_validate_json(json.dumps(data)) == expected


def test_existing_instance_validation_preserved():
    action = CardAction(key="detail", label_mode="icon")
    assert CardAction.model_validate(action) is action


@pytest.mark.parametrize("data", [None, 42, [], "detail"])
def test_invalid_non_mapping_retains_pydantic_validation_error(data):
    with pytest.raises(ValidationError, match="valid dictionary or instance"):
        CardAction.model_validate(data)
