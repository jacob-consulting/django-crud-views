"""#216: label-mode maps — settings, ViewSet fields, view attributes, resolution and checks."""

import logging
import re

import pytest
from django import forms
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


# --- form actions (Phase 6, FORM-11): whole-map selection view -> ViewSet -> setting, then the lazy form floor ----

FORM_KIND_KEYS = ("submit", "cancel", "delete", "filter-submit", "filter-reset")
FORM_LABEL = {"form": "label"}


def _form_mode(kind, view_cls=None):
    from tests.test1.app.views import AuthorCreateView

    return (view_cls or AuthorCreateView).cv_get_action_label_mode("form", kind)


def _no_form_maps(monkeypatch):
    from tests.test1.app.views import AuthorCreateView

    monkeypatch.setattr(AuthorCreateView, "cv_form_actions_label_mode", None)
    monkeypatch.setattr(cv_author, "form_actions_label_mode", None)
    monkeypatch.setattr(crud_views_settings, "form_actions_label_mode", {})


def test_form_settings_default_and_explicit_construction():
    assert CrudViewsSettings().form_actions_label_mode == {}
    assert CrudViewsSettings(form_actions_label_mode={"submit": "both"}).form_actions_label_mode == {"submit": "both"}
    # the import-time singleton follows the context / list maps
    assert crud_views_settings.form_actions_label_mode == {}


def test_form_viewset_field_and_view_attribute_default_to_none():
    from tests.test1.app.views import AuthorCreateView

    assert cv_author.form_actions_label_mode is None
    assert AuthorCreateView.cv_form_actions_label_mode is None
    vs = ViewSet(model=Author, name="author_form_label_mode_06", form_actions_label_mode={"submit": "icon"})
    assert vs.form_actions_label_mode == {"submit": "icon"}


@pytest.mark.parametrize("value", [["submit"], "both", {"submit": "text"}, {"submit": None}])
def test_form_viewset_rejects_bad_value(value):
    with pytest.raises(ValidationError):
        ViewSet(model=Author, name="author_bad_form_label_mode_06", form_actions_label_mode=value)


def test_form_default_resolves_to_empty_and_label(monkeypatch):
    _no_form_maps(monkeypatch)
    from tests.test1.app.views import AuthorCreateView

    assert AuthorCreateView.cv_get_form_actions_label_mode() == {}
    assert [_form_mode(k) for k in FORM_KIND_KEYS] == ["label"] * 5


@pytest.mark.parametrize(
    "layer",
    [
        lambda mp, cls: mp.setattr(cls, "cv_form_actions_label_mode", {"submit": "both"}),
        lambda mp, cls: mp.setattr(cv_author, "form_actions_label_mode", {"submit": "both"}),
        lambda mp, cls: mp.setattr(crud_views_settings, "form_actions_label_mode", {"submit": "both"}),
    ],
    ids=["view", "viewset", "setting"],
)
def test_form_floor_used_only_for_unmapped_kind(monkeypatch, layer):
    from tests.test1.app.views import AuthorCreateView

    _no_form_maps(monkeypatch)
    layer(monkeypatch, AuthorCreateView)
    assert _form_mode("submit") == "both"
    assert _form_mode("cancel") == "label"
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"form": "icon"}):
        assert _form_mode("submit") == "both"  # the named kind wins over the floor
        assert _form_mode("cancel") == "icon"  # the floor for kinds the map does not name
        # the other floors are independent
        assert _list_mode("update") == "icon"
    assert _form_mode("cancel") == "label"  # restored: the package floor


def test_form_maps_are_selected_whole(monkeypatch):
    from tests.test1.app.views import AuthorCreateView

    _no_form_maps(monkeypatch)
    monkeypatch.setattr(crud_views_settings, "form_actions_label_mode", {"submit": "both", "cancel": "both"})
    monkeypatch.setattr(cv_author, "form_actions_label_mode", {"cancel": "icon"})
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS=FORM_LABEL):
        # the ViewSet map replaces the setting map whole: submit is unnamed and takes the floor
        assert AuthorCreateView.cv_get_form_actions_label_mode() == {"cancel": "icon"}
        assert (_form_mode("submit"), _form_mode("cancel")) == ("label", "icon")
        # an empty view map replaces the ViewSet map whole: every kind takes the floor
        monkeypatch.setattr(AuthorCreateView, "cv_form_actions_label_mode", {})
        assert AuthorCreateView.cv_get_form_actions_label_mode() == {}
        assert (_form_mode("submit"), _form_mode("cancel")) == ("label", "label")
    # an empty ViewSet map suppresses the setting map the same way
    monkeypatch.setattr(AuthorCreateView, "cv_form_actions_label_mode", None)
    monkeypatch.setattr(cv_author, "form_actions_label_mode", {})
    assert (_form_mode("submit"), _form_mode("cancel")) == ("label", "label")


def test_form_resolver_honors_subclass_override(monkeypatch):
    from tests.test1.app.views import AuthorCreateView

    _no_form_maps(monkeypatch)
    monkeypatch.setattr(AuthorCreateView, "cv_get_form_actions_label_mode", classmethod(lambda cls: {"cancel": "icon"}))
    assert (_form_mode("submit"), _form_mode("cancel")) == ("label", "icon")


@pytest.mark.parametrize(
    "layer",
    [
        lambda mp, cls: mp.setattr(cls, "cv_form_actions_label_mode", {"submit": "both"}),
        lambda mp, cls: mp.setattr(cv_author, "form_actions_label_mode", {"submit": "both"}),
        lambda mp, cls: mp.setattr(crud_views_settings, "form_actions_label_mode", {"submit": "both"}),
    ],
    ids=["view", "viewset", "setting"],
)
@pytest.mark.parametrize("floor", [{"form": "nope"}, None], ids=["bad-mode", "non-dict"])
def test_explicit_form_mode_bypasses_invalid_floor(monkeypatch, caplog, layer, floor):
    from tests.test1.app.views import AuthorCreateView

    _no_form_maps(monkeypatch)
    layer(monkeypatch, AuthorCreateView)
    with caplog.at_level(logging.WARNING, logger="crud_views.lib.view.label_mode"):
        with override_settings(CRUD_VIEWS_STRICT=True, CRUD_VIEWS_LABEL_MODE_DEFAULTS=floor):
            assert _form_mode("submit") == "both"  # the floor is never read for a mapped kind
        assert caplog.records == []
        with (
            override_settings(CRUD_VIEWS_STRICT=True, CRUD_VIEWS_LABEL_MODE_DEFAULTS=floor),
            pytest.raises(ValueError, match="CRUD_VIEWS_LABEL_MODE_DEFAULTS"),
        ):
            _form_mode("cancel")
        with override_settings(CRUD_VIEWS_STRICT=False, CRUD_VIEWS_LABEL_MODE_DEFAULTS=floor):
            assert _form_mode("cancel") == "label"


@pytest.mark.parametrize(
    ("selected", "kind"),
    [
        ({"submit": "text"}, "submit"),
        ({"submit": None}, "submit"),
        (["submit"], "submit"),
        ("both", "submit"),
        (7, "submit"),
    ],
    ids=["bad-mode", "none-mode", "list", "str", "int"],
)
def test_invalid_selected_form_map_uses_shared_fallback(monkeypatch, caplog, selected, kind):
    from tests.test1.app.views import AuthorCreateView

    _no_form_maps(monkeypatch)
    monkeypatch.setattr(AuthorCreateView, "cv_form_actions_label_mode", selected)
    with override_settings(CRUD_VIEWS_STRICT=True), pytest.raises(ValueError, match="form"):
        _form_mode(kind)
    with (
        caplog.at_level(logging.WARNING, logger="crud_views.lib.view.label_mode"),
        override_settings(CRUD_VIEWS_STRICT=False, CRUD_VIEWS_LABEL_MODE_DEFAULTS={"form": "both"}),
    ):
        assert _form_mode(kind) == "both"  # the floor, never a membership crash
    records = [r for r in caplog.records if r.name == "crud_views.lib.view.label_mode"]
    assert len(records) <= 1


def test_form_location_does_not_change_other_locations(monkeypatch):
    _no_form_maps(monkeypatch)
    monkeypatch.setattr(crud_views_settings, "form_actions_label_mode", {"create": "label", "update": "label"})
    assert AuthorDetailView.cv_get_action_label_mode("context", "update") == "icon"
    assert AuthorListView.cv_get_action_label_mode("list", "update") == "icon"
    with pytest.raises(ValueError, match="'form'"):
        AuthorDetailView.cv_get_action_label_mode("card", "detail")


# the maps reach the real crispy leaf

MODE_CLASSES = {f"form:{k}:{m}": f"m-{m}" for k in FORM_KIND_KEYS for m in LABEL_MODES}


def _crispy_modes(form) -> dict[str, str]:
    """name -> rendered mode of each layout control of a real {% crispy %} render."""
    from crispy_forms.bootstrap import FormActions
    from crispy_forms.helper import FormHelper
    from crispy_forms.layout import Layout
    from django.template import Context, Template
    from lxml import html as lxml_html

    from crud_views.lib.crispy import Button, Submit

    helper = FormHelper()
    helper.form_tag = False
    helper.layout = Layout(FormActions(Submit("submit", "Save"), Button("cancel", "Back", data_cv_cancel_url="/b/")))
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES=MODE_CLASSES):
        markup = Template("{% load crispy_forms_tags %}{% crispy form helper %}").render(
            Context({"form": form, "helper": helper})
        )
    doc = lxml_html.fragment_fromstring(markup, create_parent="div")
    return {el.get("name"): el.get("class").removeprefix("m-") for el in doc.cssselect("button")}


class _OwnedForm(forms.Form):
    def __init__(self, cv_view=None):
        super().__init__()
        if cv_view is not None:
            self.cv_view = cv_view


def test_settings_map_reaches_the_leaf_and_only_the_floor_is_live(monkeypatch):
    _no_form_maps(monkeypatch)
    monkeypatch.setattr(crud_views_settings, "form_actions_label_mode", {"submit": "both"})
    assert _crispy_modes(_OwnedForm()) == {"submit": "both", "cancel": "label"}
    # the map is captured at import (startup) time: a post-import override_settings of the map alone changes nothing
    with override_settings(CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE={"submit": "icon"}):
        assert _crispy_modes(_OwnedForm()) == {"submit": "both", "cancel": "label"}
        # the form floor is read per render: it changes the unmapped cancel only
        with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"form": "icon"}):
            assert _crispy_modes(_OwnedForm()) == {"submit": "both", "cancel": "icon"}
        assert _crispy_modes(_OwnedForm()) == {"submit": "both", "cancel": "label"}
    assert _crispy_modes(_OwnedForm()) == {"submit": "both", "cancel": "label"}


@pytest.mark.parametrize("instance", [False, True], ids=["class", "instance"])
def test_view_and_viewset_maps_reach_the_leaf(monkeypatch, instance):
    from tests.test1.app.views import AuthorCreateView

    _no_form_maps(monkeypatch)
    owner = AuthorCreateView() if instance else AuthorCreateView
    monkeypatch.setattr(crud_views_settings, "form_actions_label_mode", {"submit": "icon", "cancel": "icon"})
    monkeypatch.setattr(cv_author, "form_actions_label_mode", {"cancel": "both"})
    assert _crispy_modes(_OwnedForm(owner)) == {"submit": "label", "cancel": "both"}
    monkeypatch.setattr(AuthorCreateView, "cv_form_actions_label_mode", {"submit": "icon"})
    assert _crispy_modes(_OwnedForm(owner)) == {"submit": "icon", "cancel": "label"}
    monkeypatch.setattr(AuthorCreateView, "cv_form_actions_label_mode", {})
    assert _crispy_modes(_OwnedForm(owner)) == {"submit": "label", "cancel": "label"}


@pytest.mark.django_db
def test_view_map_reaches_the_endpoint(monkeypatch, client_user_author_add):
    from django.urls import reverse
    from lxml import html as lxml_html

    from tests.test1.app.views import AuthorCreateView

    _no_form_maps(monkeypatch)
    monkeypatch.setattr(AuthorCreateView, "cv_form_actions_label_mode", {"submit": "icon"})
    page = client_user_author_add.get(reverse(cv_author.get_router_name("create"))).content.decode()
    doc = lxml_html.fromstring(page)
    (submit,) = doc.cssselect('button[name="submit"]')
    (cancel,) = doc.cssselect('button[name="reset"]')
    assert [s.text for s in submit.cssselect("span.visually-hidden")] == ["Create"]
    assert (submit.get("title"), submit.get("data-cv-tooltip")) == ("Create", "form")
    assert not cancel.cssselect("span.visually-hidden") and cancel.get("title") is None
