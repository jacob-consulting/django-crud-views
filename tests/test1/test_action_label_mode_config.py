"""#216: label-mode maps — settings, ViewSet fields, view attributes, resolution and checks."""

import pytest
from pydantic import ValidationError

from crud_views.lib.settings import CrudViewsSettings
from crud_views.lib.view.label_mode import is_label_mode_map
from crud_views.lib.viewset import ViewSet
from tests.test1.app.models import Author


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, True),
        ({}, True),
        ({"create": "both"}, True),
        ({"a": "label", "b": "icon"}, True),
        (["create"], False),
        ("both", False),
        ({"create": "text"}, False),
        ({1: "both"}, False),
        ({"create": None}, False),
    ],
)
def test_is_label_mode_map(value, expected):
    assert is_label_mode_map(value) is expected


def test_settings_defaults():
    s = CrudViewsSettings()
    assert s.context_actions_label_mode == {}
    assert s.list_actions_label_mode == {}


@pytest.mark.parametrize("field", ["context_actions_label_mode", "list_actions_label_mode"])
@pytest.mark.parametrize("value", [None, ["create"], "both", {"create": "text"}, {1: "both"}])
def test_invalid_setting_e106(field, value):
    messages = CrudViewsSettings(**{field: value}).check_messages
    assert [m.id for m in messages] == ["crud_views.E106"]
    assert f"CRUD_VIEWS_{field.upper()}" in messages[0].msg


@pytest.mark.parametrize("value", [{}, {"create": "both"}, {"create": "label", "home": "icon"}])
def test_valid_setting_values(value):
    assert CrudViewsSettings(context_actions_label_mode=value).check_messages == []


@pytest.mark.parametrize("field", ["context_actions_label_mode", "list_actions_label_mode"])
@pytest.mark.parametrize("value", [["create"], {"create": "text"}, "both"])
def test_viewset_rejects_bad_value(field, value):
    with pytest.raises(ValidationError):
        ViewSet(model=Author, name=f"author_bad_{field}_216", **{field: value})


def test_viewset_accepts_map_and_defaults_to_none():
    vs = ViewSet(model=Author, name="author_label_mode_216", context_actions_label_mode={"create": "both"})
    assert vs.context_actions_label_mode == {"create": "both"}
    assert vs.list_actions_label_mode is None
