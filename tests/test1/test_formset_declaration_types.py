"""Nested declarations contain FormSet nodes across supported Pydantic versions."""

import pytest
from pydantic import ValidationError

from crud_views.lib.formsets import FormSet
from tests.test1.app.views_formset import BookFormSet


@pytest.mark.parametrize(
    "fields,location",
    [
        ({"parent": object()}, ("parent",)),
        ({"children": {"bad": object()}}, ("children", "bad")),
        (
            {"children": {"nested": {"klass": BookFormSet, "children": {"bad": object()}}}},
            ("children", "nested", "children", "bad"),
        ),
    ],
)
def test_nested_declarations_reject_non_formset_nodes(fields, location):
    with pytest.raises(ValidationError) as caught:
        FormSet(klass=BookFormSet, **fields)
    assert location in [error["loc"] for error in caught.value.errors()]


@pytest.mark.parametrize("specialized_parent", [False, True])
@pytest.mark.parametrize("specialized_child", [False, True])
def test_nested_declarations_accept_mixed_base_and_subclass_nodes(specialized_parent, specialized_child):
    class Specialized(FormSet):
        pass

    parent_type = Specialized if specialized_parent else FormSet
    child_type = Specialized if specialized_child else FormSet
    parent = parent_type(klass=BookFormSet)
    child = child_type(klass=BookFormSet, parent=parent)
    tree = parent_type(klass=BookFormSet, children={"books": child})
    assert child.parent is parent
    assert tree.children["books"] is child
