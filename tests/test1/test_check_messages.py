from crud_views.lib.check import CheckEitherAttribute, CheckTemplate


class BothSet:
    attr_a = "x"
    attr_b = "y"


class NeitherSet:
    attr_a = None
    attr_b = None


def test_check_either_attribute_both_set_emits_both_message():
    check = CheckEitherAttribute(context=BothSet, id="E999", attribute1="attr_a", attribute2="attr_b")
    messages = list(check.messages())
    assert len(messages) == 1
    assert "Both attributes" in messages[0].msg
    assert "attr_a" in messages[0].msg
    assert "attr_b" in messages[0].msg


def test_check_either_attribute_neither_set_emits_neither_message():
    check = CheckEitherAttribute(context=NeitherSet, id="E999", attribute1="attr_a", attribute2="attr_b")
    messages = list(check.messages())
    assert len(messages) == 1
    assert "Neither attribute" in messages[0].msg
    assert "nor" in messages[0].msg


def test_crud_views_checks_registered_under_crud_views_tag():
    from django.core.checks.registry import registry

    assert "crud_views" in registry.tags_available()
    assert "my_new_tag" not in registry.tags_available()


class ExtendsValid:
    extends = "app/index.html"  # exists in the test app


class ExtendsMissing:
    extends = "does-not-exist.html"


class ExtendsUnset:
    extends = None


def test_check_template_unset_emits_no_message():
    check = CheckTemplate(context=ExtendsUnset, id="E111", attribute="extends")
    assert list(check.messages()) == []


def test_check_template_existing_emits_no_message():
    check = CheckTemplate(context=ExtendsValid, id="E111", attribute="extends")
    assert list(check.messages()) == []


def test_check_template_missing_emits_error():
    check = CheckTemplate(context=ExtendsMissing, id="E111", attribute="extends")
    messages = list(check.messages())
    assert len(messages) == 1
    assert "does-not-exist.html" in messages[0].msg
    assert messages[0].id == "viewset.E111"
