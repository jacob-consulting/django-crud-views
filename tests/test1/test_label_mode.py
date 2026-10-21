import pytest

from crud_views.lib.view.label_mode import LABEL_MODES, is_label_mode, label_mode_check


def test_label_modes():
    assert {"label", "icon", "both"} == LABEL_MODES


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
