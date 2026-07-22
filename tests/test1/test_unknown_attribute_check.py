from functools import cached_property

from crud_views.lib.check import CheckUnknownAttributes
from crud_views.lib.view.base import CrudView


# Bare CrudView subclasses do NOT register (metaclass registers only when
# cv_viewset is in the class body), so these are safe, unregistered fixtures
# whose MRO still includes the package classes that populate the known-set.


class DeadAttrView(CrudView):
    cv_message = "Created {{ object }}"  # dead: real API is cv_message_template_code


class GoodOverrideView(CrudView):
    cv_message_template_code = "Created {{ object }}"  # legitimate override of a known attr


class MethodView(CrudView):
    def cv_helper(self):  # user cv_* method — not a data attribute, must not warn
        return 1

    @property
    def cv_computed(self):  # descriptor — must not warn
        return 2

    @cached_property
    def cv_cached(self):  # descriptor — must not warn
        return 3


class ExemptView(CrudView):
    cv_check_ignore_attributes = frozenset({"cv_custom"})
    cv_custom = 1  # custom data attr, exempted by the allowlist


class UnexemptView(CrudView):
    cv_custom = 1  # same custom data attr, but NOT exempted -> must warn


class _ExemptMixin(CrudView):
    cv_check_ignore_attributes = frozenset({"cv_from_mixin"})
    cv_from_mixin = 1


class UnionExemptView(_ExemptMixin):
    cv_check_ignore_attributes = frozenset({"cv_from_leaf"})
    cv_from_leaf = 2


def _w280(context):
    return list(CheckUnknownAttributes(context=context).messages())


def test_dead_attribute_warns_and_suggests_near_match():
    messages = _w280(DeadAttrView)
    assert len(messages) == 1
    m = messages[0]
    assert m.id == "viewset.W280"
    assert "cv_message" in m.msg
    # cv_message_template and cv_message_template_code are both valid near-matches;
    # "cv_message_template" is a substring of both, so this tolerates either suggestion.
    assert "cv_message_template" in m.msg


def test_legitimate_override_does_not_warn():
    assert _w280(GoodOverrideView) == []


def test_cv_methods_and_descriptors_do_not_warn():
    assert _w280(MethodView) == []


def test_allowlisted_custom_attribute_does_not_warn():
    assert _w280(ExemptView) == []


def test_unlisted_custom_attribute_warns():
    messages = _w280(UnexemptView)
    assert len(messages) == 1
    assert "cv_custom" in messages[0].msg


def test_allowlist_is_unioned_across_the_mro():
    # If the check used getattr (leaf shadows), cv_from_mixin would leak a warning.
    assert _w280(UnionExemptView) == []
