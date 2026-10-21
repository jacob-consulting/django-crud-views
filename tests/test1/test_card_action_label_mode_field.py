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


def test_no_label_with_explicit_label_mode_rejected():
    with pytest.raises(ValidationError, match="no_label"):
        CardAction(key="detail", no_label=True, label_mode="label")


def test_no_label_alone_still_allowed():
    assert CardAction(key="detail", no_label=True).no_label is True
