"""#216: label-mode maps — settings, ViewSet fields, view attributes, resolution and checks."""

import logging
import re

import pytest
from django.conf import settings
from django.core.checks import ERROR
from django.test import override_settings
from pydantic import ValidationError

from crud_views.lib.settings import CrudViewsSettings, crud_views_settings
from crud_views.lib.view.label_mode import LABEL_MODES, is_label_mode_map
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


# CRUD_VIEWS_LABEL_MODE_DEFAULTS["list"]: the floor for keys the selected whole-layer map does not name

LIST_LABEL = {"list": "label"}
INVALID_FLOORS = pytest.mark.parametrize("floor", [{"list": "nope"}, None], ids=["bad-mode", "non-dict"])


def _list_mode(key):
    return AuthorListView.cv_get_action_label_mode("list", key)


def _no_list_maps(monkeypatch):
    monkeypatch.setattr(AuthorListView, "cv_list_actions_label_mode", None)
    monkeypatch.setattr(cv_author, "list_actions_label_mode", None)
    monkeypatch.setattr(crud_views_settings, "list_actions_label_mode", {})


@pytest.mark.parametrize(
    "layer",
    [
        lambda mp: mp.setattr(AuthorListView, "cv_list_actions_label_mode", {"detail": "both"}),
        lambda mp: mp.setattr(cv_author, "list_actions_label_mode", {"detail": "both"}),
        lambda mp: mp.setattr(crud_views_settings, "list_actions_label_mode", {"detail": "both"}),
    ],
    ids=["view", "viewset", "setting"],
)
def test_list_floor_used_only_for_unmapped_key(monkeypatch, layer):
    _no_list_maps(monkeypatch)
    layer(monkeypatch)
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS=LIST_LABEL):
        assert _list_mode("detail") == "both"  # the named key wins over the floor
        assert _list_mode("update") == "label"  # the floor for keys the map does not name
        # the context floor is independent
        assert AuthorDetailView.cv_get_action_label_mode("context", "update") == "icon"
    assert _list_mode("update") == "icon"  # unconfigured: the package floor


def test_list_floor_unconfigured_layers(monkeypatch):
    _no_list_maps(monkeypatch)
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS=LIST_LABEL):
        assert [_list_mode(k) for k in ("detail", "update", "delete")] == ["label", "label", "label"]
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"context": "both", "card": "label"}):
        assert _list_mode("detail") == "icon"


def test_list_floor_preserves_whole_map_replacement(monkeypatch):
    _no_list_maps(monkeypatch)
    monkeypatch.setattr(crud_views_settings, "list_actions_label_mode", {"detail": "both"})
    monkeypatch.setattr(cv_author, "list_actions_label_mode", {"update": "icon"})
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS=LIST_LABEL):
        # the ViewSet map replaces the setting map whole: detail is unnamed and takes the floor
        assert AuthorListView.cv_get_list_actions_label_mode() == {"update": "icon"}
        assert _list_mode("detail") == "label"
        assert _list_mode("update") == "icon"
        # an empty view map replaces the ViewSet map whole, then the floor supplies every key
        monkeypatch.setattr(AuthorListView, "cv_list_actions_label_mode", {})
        assert AuthorListView.cv_get_list_actions_label_mode() == {}
        assert _list_mode("update") == "label"
        assert _list_mode("detail") == "label"


def test_list_malformed_mapped_value_keeps_selection(monkeypatch, caplog):
    # a named key is returned as configured; viewset.E211 and the button leaf validate it, not the floor
    _no_list_maps(monkeypatch)
    monkeypatch.setattr(AuthorListView, "cv_list_actions_label_mode", {"detail": "text", "update": ""})
    with (
        caplog.at_level(logging.WARNING, logger="crud_views.lib.view.label_mode"),
        override_settings(CRUD_VIEWS_STRICT=True, CRUD_VIEWS_LABEL_MODE_DEFAULTS={"list": "nope"}),
    ):
        assert _list_mode("detail") == "text"
        assert _list_mode("update") == ""
    assert caplog.records == []


@pytest.mark.parametrize(
    "layer",
    [
        lambda mp: mp.setattr(AuthorListView, "cv_list_actions_label_mode", {"detail": "both"}),
        lambda mp: mp.setattr(cv_author, "list_actions_label_mode", {"detail": "both"}),
        lambda mp: mp.setattr(crud_views_settings, "list_actions_label_mode", {"detail": "both"}),
    ],
    ids=["view", "viewset", "setting"],
)
@INVALID_FLOORS
def test_explicit_list_mode_bypasses_invalid_floor(monkeypatch, caplog, layer, floor):
    _no_list_maps(monkeypatch)
    layer(monkeypatch)
    with caplog.at_level(logging.WARNING, logger="crud_views.lib.view.label_mode"):
        with override_settings(CRUD_VIEWS_STRICT=True, CRUD_VIEWS_LABEL_MODE_DEFAULTS=floor):
            assert _list_mode("detail") == "both"  # the floor is never read for a mapped key
        assert caplog.records == []
        # a genuinely unmapped key reads the floor: strict raises ...
        with (
            override_settings(CRUD_VIEWS_STRICT=True, CRUD_VIEWS_LABEL_MODE_DEFAULTS=floor),
            pytest.raises(ValueError, match="CRUD_VIEWS_LABEL_MODE_DEFAULTS"),
        ):
            _list_mode("update")
        # ... non-strict falls back to the package floor and warns once, across calls and settings contexts
        with override_settings(CRUD_VIEWS_STRICT=False, CRUD_VIEWS_LABEL_MODE_DEFAULTS=floor):
            assert _list_mode("update") == "icon"
            assert _list_mode("delete") == "icon"
            assert _list_mode("detail") == "both"
        with override_settings(CRUD_VIEWS_STRICT=False, CRUD_VIEWS_LABEL_MODE_DEFAULTS=floor):
            assert _list_mode("update") == "icon"
    records = [r for r in caplog.records if r.name == "crud_views.lib.view.label_mode"]
    assert len(records) == 1
    assert "CRUD_VIEWS_LABEL_MODE_DEFAULTS" in records[0].getMessage()


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


@pytest.mark.parametrize(
    ("view_cls", "attr"),
    [(AuthorListView, "cv_list_actions_label_mode"), (AuthorDetailView, "cv_context_actions_label_mode")],
)
def test_e211_describes_optional_scalar_modes(monkeypatch, view_cls, attr):
    # both scalar knobs are optional (None: the defaults map); the exact phrase is pinned in the docs tests too
    monkeypatch.setattr(view_cls, attr, "both")
    (message,) = [m for c in view_cls.checks() for m in c.messages() if m.id == "viewset.E211"]
    assert message.level == ERROR
    assert message.msg.startswith(f"{attr} must be None or a dict of action key -> one of {sorted(LABEL_MODES)}")
    for scalar in ("cv_card_actions_label_mode", "cv_context_action_label_mode"):
        assert re.search(rf"{scalar} (is )?the string or None ", message.msg), (scalar, message.msg)
    assert "string-valued" not in message.msg


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


# E108: CRUD_VIEWS_LABEL_MODE_DEFAULTS, the per-location floor (read raw, at check time)

E108_LOCATIONS = "['card', 'context', 'form', 'list']"
E108_MODES = "['both', 'icon', 'label']"


def _e108(configured=None, *, absent=False) -> list:
    if absent:
        with override_settings():
            del settings.CRUD_VIEWS_LABEL_MODE_DEFAULTS
            messages = crud_views_settings.check_messages
    else:
        with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS=configured):
            messages = crud_views_settings.check_messages
    return [m for m in messages if m.id == "crud_views.E108"]


def _key_msg(key, allowed, value) -> str:
    return f"setting CRUD_VIEWS_LABEL_MODE_DEFAULTS key {key!r} must be one of {allowed}, got {value!r}"


@pytest.mark.parametrize(
    "configured",
    [
        {},
        {"context": "both"},
        {"card": "label"},
        {"context": "label", "list": "both", "card": "icon"},
        # the form location (Phase 6) arrives through LOCATIONS
        {"form": "both"},
        {"form": "icon", "card": "label"},
    ],
)
def test_e108_valid_defaults(configured):
    assert _e108(absent=True) == []
    assert _e108(configured) == []


@pytest.mark.parametrize("configured", [None, "both", "", ["context"], [], 1, ("context", "both")], ids=repr)
def test_e108_non_dict(configured):
    messages = _e108(configured)
    assert len(messages) == 1
    (message,) = messages
    assert message.level == ERROR
    assert message.hint is None
    assert message.msg == (
        f"setting CRUD_VIEWS_LABEL_MODE_DEFAULTS must be a dict of location -> one of {E108_MODES}, got {configured!r}"
    )


@pytest.mark.parametrize(
    "configured,expected",
    [
        ({"cotext": "both"}, [_key_msg("cotext", E108_LOCATIONS, "both")]),
        # a typo of the form location is still an unknown key
        ({"from": "both"}, [_key_msg("from", E108_LOCATIONS, "both")]),
        ({"form": "nope"}, [_key_msg("form", E108_MODES, "nope")]),
        ({1: "both"}, [_key_msg(1, E108_LOCATIONS, "both")]),
        ({"card": "nope"}, [_key_msg("card", E108_MODES, "nope")]),
        ({"card": None}, [_key_msg("card", E108_MODES, None)]),
        ({"list": "Both"}, [_key_msg("list", E108_MODES, "Both")]),
        ({"context": {"filter": "both"}}, [_key_msg("context", E108_MODES, {"filter": "both"})]),
        ({"context": ["both"]}, [_key_msg("context", E108_MODES, ["both"])]),
        # an unknown key with an invalid mode: one message, for the key
        ({"cotext": "nope"}, [_key_msg("cotext", E108_LOCATIONS, "nope")]),
        (
            {"context": "both", "cotext": "nope", "card": "nope"},
            [_key_msg("cotext", E108_LOCATIONS, "nope"), _key_msg("card", E108_MODES, "nope")],
        ),
    ],
    ids=repr,
)
def test_e108_bad_entries(configured, expected):
    messages = _e108(configured)
    assert [m.msg for m in messages] == expected
    assert all(m.level == ERROR and m.hint is None for m in messages)


def test_e108_entry_order():
    forward = {"list": "x", "zzz": "both", "card": {"a": 1}}
    backward = dict(reversed(list(forward.items())))
    assert [m.msg for m in _e108(forward)] == [
        _key_msg("list", E108_MODES, "x"),
        _key_msg("zzz", E108_LOCATIONS, "both"),
        _key_msg("card", E108_MODES, {"a": 1}),
    ]
    assert [m.msg for m in _e108(backward)] == list(reversed([m.msg for m in _e108(forward)]))


def test_e108_same_settings_instance_observes_changes():
    assert _e108({"card": "nope"}) != []
    assert _e108({"card": "label"}) == []
    assert len(_e108({"card": "nope", "list": "nope"})) == 2


def test_e108_uses_button_locations(monkeypatch):
    from crud_views.lib.view import button_data

    assert len(_e108({"test_loc": "both"})) == 1
    monkeypatch.setattr(button_data, "LOCATIONS", button_data.LOCATIONS | {"test_loc"})
    assert _e108({"test_loc": "both"}) == []
    (message,) = _e108({"test_lok": "both"})
    assert message.msg == _key_msg("test_lok", sorted(button_data.LOCATIONS), "both")
    (message,) = _e108({"test_loc": "nope"})
    assert message.msg == _key_msg("test_loc", sorted(LABEL_MODES), "nope")
