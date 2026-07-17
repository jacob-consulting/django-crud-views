from crud_views.lib.check import CheckAttributeType, CheckMapping, ContextActionCheck
from django.db.models import Model
from tests.test1.app.models import Book
from crud_views.lib.formsets.formsets import FormSets
from tests.test1.app.views_formset import PublisherFormSetCreateView


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


def test_formset_create_view_yields_e204_typed_check():
    checks = list(PublisherFormSetCreateView.checks())
    e204 = [c for c in checks if getattr(c, "id", None) == "E204"]
    assert len(e204) == 1
    assert isinstance(e204[0], CheckAttributeType)
    assert e204[0].attribute == "cv_formsets"
    assert e204[0].expected_type is FormSets


def test_formset_checks_do_not_reuse_e200_for_formsets():
    # E200 belongs to cv_key; formsets must not collide with it
    checks = list(PublisherFormSetCreateView.checks())
    e200_attrs = {getattr(c, "attribute", None) for c in checks if getattr(c, "id", None) == "E200"}
    assert "cv_formsets" not in e200_attrs
    assert "cv_formsets_required" not in e200_attrs


class FakeViewset:
    def __init__(self, keys):
        self._keys = keys

    def has_view(self, name):
        return name in self._keys


class CtxActionsValid:
    cv_viewset = FakeViewset(["update", "delete"])
    cv_context_actions = ["update", "delete"]


class CtxActionsBad:
    cv_viewset = FakeViewset(["update"])
    cv_context_actions = ["update", "does_not_exist"]


class CtxActionsNone:
    cv_viewset = FakeViewset(["update"])
    cv_context_actions = None


def test_context_action_check_valid_emits_no_message():
    check = ContextActionCheck(context=CtxActionsValid, id="E203")
    assert list(check.messages()) == []


def test_context_action_check_missing_view_emits_error():
    check = ContextActionCheck(context=CtxActionsBad, id="E203")
    messages = list(check.messages())
    assert len(messages) == 1
    assert messages[0].id == "viewset.E203"
    assert "does_not_exist" in messages[0].msg


def test_context_action_check_none_emits_no_message():
    check = ContextActionCheck(context=CtxActionsNone, id="E203")
    assert list(check.messages()) == []
