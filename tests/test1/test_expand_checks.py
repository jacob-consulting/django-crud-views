from crud_views.lib.check import CheckAttributeType


class GoodType:
    attr = "a string"


class BadType:
    attr = 123


class NoneType:
    attr = None


def test_check_attribute_type_correct_emits_no_message():
    check = CheckAttributeType(context=GoodType, id="E101", attribute="attr", expected_type=str)
    assert list(check.messages()) == []


def test_check_attribute_type_wrong_emits_error():
    check = CheckAttributeType(context=BadType, id="E101", attribute="attr", expected_type=str)
    messages = list(check.messages())
    assert len(messages) == 1
    assert messages[0].id == "viewset.E101"
    assert "is not of type" in messages[0].msg


def test_check_attribute_type_none_defers_to_existence_only():
    # nullable=True so the existence check passes; type check must not fire on None
    check = CheckAttributeType(context=NoneType, id="E101", attribute="attr", expected_type=str, nullable=True)
    assert list(check.messages()) == []
