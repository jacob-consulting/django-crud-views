from crud_views.lib.check import CheckAttributeType, CheckMapping
from django.db.models import Model
from tests.test1.app.models import Book


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


class NotADict:
    attr = ["not", "a", "dict"]


class NonClassKey:
    attr = {"strkey": "v"}


class NonSubclassKey:
    attr = {int: "v"}


class BadValue:
    attr = {Book: 123}


class ValidMapping:
    attr = {Book: "v"}


def test_check_mapping_not_a_dict_errors():
    check = CheckMapping(context=NotADict, id="E205", attribute="attr", key_type=Model, value_type=str)
    messages = list(check.messages())
    assert len(messages) == 1
    assert messages[0].id == "viewset.E205"


def test_check_mapping_non_class_key_errors_without_raising():
    check = CheckMapping(context=NonClassKey, id="E205", attribute="attr", key_type=Model, value_type=str)
    messages = list(check.messages())
    assert len(messages) == 1
    assert messages[0].id == "viewset.E205"


def test_check_mapping_non_subclass_key_errors():
    check = CheckMapping(context=NonSubclassKey, id="E205", attribute="attr", key_type=Model, value_type=str)
    assert len(list(check.messages())) == 1


def test_check_mapping_bad_value_errors():
    check = CheckMapping(context=BadValue, id="E205", attribute="attr", key_type=Model, value_type=str)
    assert len(list(check.messages())) == 1


def test_check_mapping_valid_emits_no_message():
    check = CheckMapping(context=ValidMapping, id="E205", attribute="attr", key_type=Model, value_type=str)
    assert list(check.messages()) == []
