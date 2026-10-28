"""Phase 06 form-button diagnostics (06-06): form label-mode maps and missing form icons.

Form-only policy (D-16): the view's own ``cv_form_actions_label_mode`` reports a malformed shape (non-dict,
non-string keys) as one viewset.E211, each invalid mode of a string-keyed map as one viewset.E210 in insertion order,
and form kinds outside the finite ``FORM_KINDS`` with valid modes as one viewset.W291. The settings map is checked by
its E106 owner, the ViewSet map by its construction validator; neither emits W291. The context / list checks stay
byte-compatible.
"""

import pytest
from django.core.checks import ERROR, WARNING
from django.test import override_settings
from pydantic import ValidationError

from crud_views.checks import check_viewsets
from crud_views.lib.button_classes import FORM_KINDS
from crud_views.lib.settings import CrudViewsSettings, crud_views_settings
from crud_views.lib.view.label_mode import LABEL_MODES
from crud_views.lib.viewset import ViewSet
from tests.test1.app.models import Author
from tests.test1.app.views import AuthorCreateView, AuthorDetailView, AuthorListView, cv_author

ATTR = "cv_form_actions_label_mode"
KINDS = sorted(FORM_KINDS)
MODES = sorted(LABEL_MODES)
FLOOR_HINT = "kinds not named take the form floor CRUD_VIEWS_LABEL_MODE_DEFAULTS['form']"


def _e211(value) -> str:
    return (
        f"{ATTR} must be None or a dict of form kind -> one of {MODES}, got {value!r} "
        f"(form kinds: {KINDS}; {FLOOR_HINT}) at {AuthorCreateView}"
    )


def _e210(kind, value) -> str:
    return f"{ATTR} form kind {kind!r} must be one of {MODES}, got {value!r} at {AuthorCreateView}"


def _w291(unknown) -> str:
    return f"{ATTR} names {unknown!r}, which are not form kinds {KINDS} (typo?); {FLOOR_HINT} at {AuthorCreateView}"


def _form_messages(messages) -> list[tuple[str, int, str]]:
    return [(m.id, m.level, m.msg) for m in messages if ATTR in m.msg or "CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE" in m.msg]


def _view_messages(view_cls=AuthorCreateView) -> list[tuple[str, int, str]]:
    return _form_messages(m for c in view_cls.checks() for m in c.messages())


def _system_messages() -> list[tuple[str, int, str]]:
    return _form_messages(check_viewsets())


@pytest.fixture
def form_map(monkeypatch):
    def set_map(value):
        monkeypatch.setattr(AuthorCreateView, ATTR, value)

    return set_map


# --- the view's own map: E211 shape, E210 per invalid mode, W291 unknown kinds ------------------------------------


@pytest.mark.parametrize(
    "value",
    [None, {}, {"submit": "both"}, dict.fromkeys(KINDS, "icon"), {"cancel": "label", "delete": "both"}],
    ids=repr,
)
def test_valid_view_maps_are_silent(form_map, value):
    form_map(value)
    assert _view_messages() == []
    assert _system_messages() == []


@pytest.mark.parametrize("value", ["both", ["submit"], ("submit", "both"), 1, ""], ids=repr)
def test_non_dict_view_map_is_one_e211(form_map, value):
    form_map(value)
    expected = [("viewset.E211", ERROR, _e211(value))]
    assert _view_messages() == expected
    assert _system_messages() == expected


@pytest.mark.parametrize(
    "value",
    [{1: "both"}, {None: "nope", "submit": "nope"}, {"submit": "both", ("a",): "x", "submti": "both"}],
    ids=repr,
)
def test_non_string_keys_are_one_e211_and_stop_traversal(form_map, value):
    form_map(value)
    # no E210 for the invalid modes and no W291 for the unknown kinds: the shape error stops the traversal
    assert _system_messages() == [("viewset.E211", ERROR, _e211(value))]


def test_invalid_modes_are_one_e210_each_in_insertion_order(form_map):
    form_map({"delete": "nope", "submit": "both", "cancel": None, "filter-reset": {"x": 1}})
    expected = [
        ("viewset.E210", ERROR, _e210("delete", "nope")),
        ("viewset.E210", ERROR, _e210("cancel", None)),
        ("viewset.E210", ERROR, _e210("filter-reset", {"x": 1})),
    ]
    assert _view_messages() == expected
    assert _system_messages() == expected


def test_unknown_kinds_with_valid_modes_are_one_w291(form_map):
    form_map({"submti": "both", "cancel": "icon", "primary": "label"})
    expected = [("viewset.W291", WARNING, _w291(["submti", "primary"]))]
    assert _view_messages() == expected
    assert _system_messages() == expected


def test_mixed_map_reports_invalid_modes_then_unknown_kinds(form_map):
    # an unknown kind with an invalid mode is reported once, as E210; W291 names only valid-mode unknown kinds
    form_map({"submti": "nope", "zz": "both", "cancel": "bad", "delete": "icon"})
    assert _system_messages() == [
        ("viewset.E210", ERROR, _e210("submti", "nope")),
        ("viewset.E210", ERROR, _e210("cancel", "bad")),
        ("viewset.W291", WARNING, _w291(["zz"])),
    ]


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ({"": "both"}, [("viewset.W291", WARNING, _w291([""]))]),
        ({"": ""}, [("viewset.E210", ERROR, _e210("", ""))]),
        ({"sübmit": "both"}, [("viewset.W291", WARNING, _w291(["sübmit"]))]),
        ({"submit": "bïth"}, [("viewset.E210", ERROR, _e210("submit", "bïth"))]),
        ({"ünknown": "ïcon", "cancel": "both"}, [("viewset.E210", ERROR, _e210("ünknown", "ïcon"))]),
    ],
    ids=repr,
)
def test_empty_and_non_ascii_entries_are_deterministic(form_map, value, expected):
    form_map(value)
    assert _system_messages() == expected
    assert _system_messages() == expected


def test_repeated_check_runs_report_the_same_messages(form_map):
    form_map({"submti": "both", "cancel": "nope"})
    first = _system_messages()
    assert first == [("viewset.E210", ERROR, _e210("cancel", "nope")), ("viewset.W291", WARNING, _w291(["submti"]))]
    # no warn-once register: every run reports again
    assert _system_messages() == first
    assert _system_messages() == first


def test_form_messages_do_not_name_view_actions_or_card_scalars(form_map):
    for value in ("both", {"submti": "both"}):
        form_map(value)
        for _id, _level, msg in _view_messages():
            assert "this view's actions" not in msg
            assert "cv_card_actions_label_mode" not in msg
            assert "cv_context_action_label_mode" not in msg


def test_checks_do_not_resolve_the_mode(form_map, monkeypatch):
    # checks inspect the map only; the resolver (which may raise in strict mode) is never called
    def boom(*args, **kwargs):
        raise AssertionError("resolver called during checks")

    form_map({"submit": "nope"})
    monkeypatch.setattr(AuthorCreateView, "cv_get_form_actions_label_mode", classmethod(boom))
    assert [m[0] for m in _system_messages()] == ["viewset.E210"]


# --- context / list checks unchanged (byte-compatible E211 / W291) ------------------------------------------------


@pytest.mark.parametrize(
    ("view_cls", "attr"),
    [(AuthorListView, "cv_list_actions_label_mode"), (AuthorDetailView, "cv_context_actions_label_mode")],
)
@pytest.mark.parametrize("value", ["both", {"create": "text"}, {1: "both"}], ids=repr)
def test_context_list_e211_is_unchanged(monkeypatch, view_cls, attr, value):
    monkeypatch.setattr(view_cls, attr, value)
    ids = ("viewset.E210", "viewset.E211")
    messages = [(m.id, m.msg) for c in view_cls.checks() for m in c.messages() if m.id in ids]
    assert messages == [
        (
            "viewset.E211",
            f"{attr} must be None or a dict of action key -> one of {MODES}, got {value!r} "
            "(cv_card_actions_label_mode is the string or None default of card views, cv_context_action_label_mode "
            f"the string or None default of a target view) at {view_cls}",
        )
    ]


def test_context_w291_is_unchanged(monkeypatch):
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions", ["home", "update"])
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_label_mode", {"home": "both", "udpate": "both"})
    messages = [m.msg for c in AuthorDetailView.checks() for m in c.messages() if m.id == "viewset.W291"]
    assert messages == [
        "cv_context_actions_label_mode names ['udpate'], which are not among this view's actions "
        f"['home', 'update'] (typo?) at {AuthorDetailView}"
    ]


def test_context_list_maps_keep_open_action_keys(monkeypatch):
    # finite form kinds never leak into the open context / list key policy
    vs = ViewSet(model=Author, name="author_open_keys_0606", context_actions_label_mode={"anything": "both"})
    assert vs.context_actions_label_mode == {"anything": "both"}
    assert CrudViewsSettings(list_actions_label_mode={"anything": "icon"}).check_messages == []


# --- settings map: the E106 owner, never W291 ---------------------------------------------------------------------


def _e106(value) -> str:
    return (
        f"setting CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE must be a dict of form kind (one of {KINDS}) -> one of {MODES}, "
        f"got {value!r}"
    )


@pytest.mark.parametrize("value", [{}, {"submit": "both"}, dict.fromkeys(KINDS, "label")], ids=repr)
def test_valid_settings_form_map(value):
    assert CrudViewsSettings(form_actions_label_mode=value).check_messages == []


@pytest.mark.parametrize(
    "value",
    [None, [], ["submit"], "both", {"submit": "text"}, {1: "both"}, {"submti": "both"}, {"": "both"}, {"sübmit": "x"}],
    ids=repr,
)
def test_invalid_settings_form_map_is_one_e106(value):
    messages = CrudViewsSettings(form_actions_label_mode=value).check_messages
    assert [(m.id, m.level, m.msg) for m in messages] == [("crud_views.E106", ERROR, _e106(value))]


def test_settings_form_map_reaches_check_viewsets(monkeypatch):
    monkeypatch.setattr(crud_views_settings, "form_actions_label_mode", {"submti": "both"})
    assert _system_messages() == [("crud_views.E106", ERROR, _e106({"submti": "both"}))]


def test_context_list_e106_messages_are_unchanged():
    (message,) = CrudViewsSettings(context_actions_label_mode={"create": "text"}).check_messages
    assert message.msg == (
        f"setting CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE must be a dict of action key -> one of {MODES}, "
        "got {'create': 'text'}"
    )


# --- ViewSet map: the construction validator, never W291 ----------------------------------------------------------


@pytest.mark.parametrize("value", [None, {}, {"submit": "icon", "filter-reset": "both"}], ids=repr)
def test_viewset_accepts_valid_form_maps(value):
    # ViewSet names are registered process-wide: one name per parameter
    name = f"author_form_ok_0606_{len(value) if value is not None else 'none'}"
    vs = ViewSet(model=Author, name=name, form_actions_label_mode=value)
    assert vs.form_actions_label_mode == value


@pytest.mark.parametrize(
    "value",
    [["submit"], "both", {"submit": "text"}, {"submit": None}, {"submti": "both"}, {"": "both"}, {"sübmit": "icon"}],
    ids=repr,
)
def test_viewset_rejects_invalid_form_maps(value):
    with pytest.raises(ValidationError) as info:
        ViewSet(model=Author, name="author_form_bad_0606", form_actions_label_mode=value)
    assert "form_actions_label_mode" in str(info.value)


def test_viewset_form_map_error_names_form_kinds():
    with pytest.raises(ValidationError) as info:
        ViewSet(model=Author, name="author_form_kinds_0606", form_actions_label_mode={"submti": "both"})
    assert f"must map form kinds {KINDS} to one of {MODES}" in str(info.value)


def test_w291_never_for_viewset_or_setting_form_maps(monkeypatch):
    # bypass the constructor/E106 owners to prove the view check never examines the selected lower maps
    monkeypatch.setattr(cv_author, "form_actions_label_mode", {"submti": "both"})
    monkeypatch.setattr(crud_views_settings, "form_actions_label_mode", {"zz": "both"})
    for view_cls in (AuthorCreateView, AuthorListView, AuthorDetailView):
        assert [m for m in _view_messages(view_cls) if m[0] == "viewset.W291"] == []


# --- the form floor stays E108 ------------------------------------------------------------------------------------


def _e108() -> list[str]:
    return [m.msg for m in check_viewsets() if m.id == "crud_views.E108"]


@pytest.mark.parametrize(
    ("floor", "value"), [({"form": None}, None), ({"form": ["label"]}, ["label"]), ({"form": {"a": 1}}, {"a": 1})]
)
def test_malformed_form_floor_is_e108_and_lazy(floor, value):
    assert _e108() == []
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS=floor):
        assert _e108() == [f"setting CRUD_VIEWS_LABEL_MODE_DEFAULTS key 'form' must be one of {MODES}, got {value!r}"]
    assert _e108() == []


def test_form_floor_typo_is_e108_unknown_location():
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"from": "both"}):
        (message,) = _e108()
    assert "key 'from' must be one of ['card', 'context', 'form', 'list']" in message


@pytest.mark.parametrize("strict", [True, False])
def test_nested_floor_recovery_under_strict(form_map, strict):
    form_map({"submit": "nope"})
    with override_settings(CRUD_VIEWS_STRICT=strict, CRUD_VIEWS_LABEL_MODE_DEFAULTS={"form": "both"}):
        assert _e108() == []
        with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"form": "nope"}):
            # checks never raise, even in strict mode: both the floor and the map are reported
            messages = check_viewsets()
            assert [m.id for m in messages if m.id == "crud_views.E108"] == ["crud_views.E108"]
            assert [m[0] for m in _form_messages(messages)] == ["viewset.E210"]
        assert _e108() == []
