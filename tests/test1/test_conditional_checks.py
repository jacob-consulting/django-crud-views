from crud_views.checks import _conditional_messages
from crud_views.lib.conditional.formset import ConditionalFormSet
from crud_views.lib.conditional.toggle import ModelFieldToggle


def test_nested_conditional_formset_flagged():
    msgs = _conditional_messages(
        nested_conditionals=[("child", ConditionalFormSet(toggle=ModelFieldToggle("x")))],
        missing_toggles=[],
        non_nullable_clears=[],
    )
    assert any(m.id == "crud_views.E310" for m in msgs)


def test_missing_toggle_field_flagged():
    msgs = _conditional_messages(
        nested_conditionals=[],
        missing_toggles=[("SomeForm", "with_x")],
        non_nullable_clears=[],
    )
    assert any(m.id == "crud_views.E311" for m in msgs)


def test_non_nullable_clear_warned():
    msgs = _conditional_messages(
        nested_conditionals=[],
        missing_toggles=[],
        non_nullable_clears=[("SomeForm", "email")],
    )
    assert any(m.id == "crud_views.W320" for m in msgs)
