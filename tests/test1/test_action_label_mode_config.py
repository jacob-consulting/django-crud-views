"""#216: label-mode maps — settings, ViewSet fields, view attributes, resolution and checks."""

import pytest
from pydantic import ValidationError

from crud_views.lib.settings import CrudViewsSettings, crud_views_settings
from crud_views.lib.view.label_mode import is_label_mode_map
from crud_views.lib.viewset import ViewSet
from tests.test1.app.models import Author
from tests.test1.app.views import AuthorDetailView, AuthorListView, cv_author


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


# resolution: view -> ViewSet -> setting, first value that is not None, whole


def test_default_resolves_to_empty_and_icon():
    assert AuthorListView.cv_get_list_actions_label_mode() == {}
    assert AuthorDetailView.cv_get_context_actions_label_mode() == {}
    assert AuthorDetailView.cv_get_action_label_mode("context", "create") == "icon"


def test_setting_is_last_fallback(monkeypatch):
    monkeypatch.setattr(crud_views_settings, "list_actions_label_mode", {"detail": "both"})
    assert AuthorListView.cv_get_action_label_mode("list", "detail") == "both"
    assert AuthorListView.cv_get_action_label_mode("list", "update") == "icon"


def test_viewset_beats_setting(monkeypatch):
    monkeypatch.setattr(crud_views_settings, "context_actions_label_mode", {"create": "both"})
    monkeypatch.setattr(cv_author, "context_actions_label_mode", {"home": "label"})
    assert AuthorDetailView.cv_get_context_actions_label_mode() == {"home": "label"}
    assert AuthorDetailView.cv_get_action_label_mode("context", "create") == "icon"  # no merge across layers


def test_view_empty_map_beats_viewset(monkeypatch):
    monkeypatch.setattr(cv_author, "context_actions_label_mode", {"create": "both"})
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_label_mode", {})
    assert AuthorDetailView.cv_get_action_label_mode("context", "create") == "icon"


def test_card_location_raises():
    with pytest.raises(ValueError):
        AuthorDetailView.cv_get_action_label_mode("card", "detail")


# checks


def _ids(view_cls) -> list[str]:
    return [m.id for c in view_cls.checks() for m in c.messages()]


@pytest.mark.parametrize(
    ("view_cls", "attr"),
    [(AuthorListView, "cv_list_actions_label_mode"), (AuthorDetailView, "cv_context_actions_label_mode")],
)
@pytest.mark.parametrize("value", ["both", ["create"], {"create": "text"}, {"create": None}])
def test_e211_invalid_view_value(monkeypatch, view_cls, attr, value):
    monkeypatch.setattr(view_cls, attr, value)
    assert "viewset.E211" in _ids(view_cls)


def test_e211_message_names_the_card_attribute(monkeypatch):
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_label_mode", "both")
    (message,) = [m for c in AuthorDetailView.checks() for m in c.messages() if m.id == "viewset.E211"]
    assert "cv_card_actions_label_mode" in message.msg


def test_no_label_mode_messages_by_default():
    for view_cls in (AuthorListView, AuthorDetailView):
        ids = _ids(view_cls)
        assert "viewset.E211" not in ids
        assert "viewset.W291" not in ids


def test_w291_unknown_context_key(monkeypatch):
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions", ["home", "update", "delete"])
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_label_mode", {"home": "both", "udpate": "both"})
    messages = [m for c in AuthorDetailView.checks() for m in c.messages() if m.id == "viewset.W291"]
    assert len(messages) == 1
    assert "udpate" in messages[0].msg
    assert messages[0].level == 30  # django.core.checks.WARNING


def test_w291_known_list_keys_no_warning(monkeypatch):
    monkeypatch.setattr(AuthorListView, "cv_list_actions_label_mode", {"detail": "both", "update": "label"})
    assert "viewset.W291" not in _ids(AuthorListView)


def test_w291_never_for_viewset_or_setting(monkeypatch):
    monkeypatch.setattr(cv_author, "list_actions_label_mode", {"nonexistent": "both"})
    monkeypatch.setattr(crud_views_settings, "context_actions_label_mode", {"nonexistent": "both"})
    for view_cls in (AuthorListView, AuthorDetailView):
        assert "viewset.W291" not in _ids(view_cls)
