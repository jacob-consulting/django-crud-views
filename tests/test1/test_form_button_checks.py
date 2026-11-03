"""Phase 06 form-button diagnostics (06-06): form label-mode maps and missing form icons.

Form-only policy (D-16): the view's own ``cv_form_actions_label_mode`` reports a malformed shape (non-dict,
non-string keys) as one viewset.E211, each invalid mode of a string-keyed map as one viewset.E210 in insertion order,
and form kinds outside the finite ``FORM_KINDS`` with valid modes as one viewset.W291. The settings map is checked by
its E106 owner, the ViewSet map by its construction validator; neither emits W291. The context / list checks stay
byte-compatible.
"""

import logging
import re

import pytest
from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from django import forms
from django.contrib.contenttypes.models import ContentType
from django.core.checks import ERROR, WARNING
from django.template import Context, Template
from django.test import override_settings
from django.utils.html import format_html
from lxml import html as lxml_html
from pydantic import ValidationError

from crud_views.checks import check_viewsets
from crud_views.lib import icons as icons_module
from crud_views.lib.button_classes import FORM_KINDS
from crud_views.lib.crispy import Button, CrispyDeleteForm, Submit
from crud_views.lib.icons import icon_check_messages
from crud_views.lib.settings import CrudViewsSettings, crud_views_settings
from crud_views.lib.view.button_data import FORM_LEAF_KEYS, cv_button_data
from crud_views.lib.view.label_mode import LABEL_MODES
from crud_views.lib.views.list import ListViewFilterFormHelper
from crud_views.lib.viewset import ViewSet
from tests.lib.helper.icons import HOST_ICONS, HOST_LIBRARY
from tests.test1.app.models import Author, Car, Truck
from tests.test1.app.views import (
    AuthorCreateView,
    AuthorDeleteView,
    AuthorDetailView,
    AuthorForm,
    AuthorListView,
    CampaignWorkflowView,
    CarForm,
    PublisherFilterFormHelper,
    PublisherListView,
    TruckForm,
    VehicleCreateView,
    VehicleUpdateView,
    cv_author,
)

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


def test_map_checks_do_not_resolve_the_mode(form_map, monkeypatch):
    # the map checks inspect the view's own attribute only; the resolver (which may raise in strict mode) is never
    # called by them (the W292 icon check resolves modes through it on purpose, see below)
    from crud_views.lib.view.action_menu import cv_form_label_mode_checks

    def boom(*args, **kwargs):
        raise AssertionError("resolver called during the map checks")

    form_map({"submit": "nope"})
    monkeypatch.setattr(AuthorCreateView, "cv_get_form_actions_label_mode", classmethod(boom))
    monkeypatch.setattr(AuthorCreateView, "cv_get_action_label_mode", classmethod(boom))
    messages = [m for c in cv_form_label_mode_checks(AuthorCreateView) for m in c.messages()]
    assert [(m.id, m.msg) for m in messages] == [("viewset.E210", _e210("submit", "nope"))]


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


# ======================================================================================================================
# Missing form icons (FORM-12, D-14 / D-16): static W292 reach, the shared availability predicate and the runtime
# strict / log-and-label policy. Availability never renders: no renderer runs during checks or the predicate.
# ======================================================================================================================

BUTTON_LOGGER = "crud_views.lib.view.button_data"
FORM_HOST_ICONS = {**HOST_ICONS, "save": "ui:floppy", "delete": "ui:trash", "cancel": "ui:x"}
W292_RE = re.compile(r"^form button '([a-z-]+)' of (\w+) renders icon-only")

RENDER_CALLS: list[str] = []


def counting_renderer(name, *, css, config):
    """A custom inline renderer that counts its calls; each output carries the call number (no shared cache)."""
    RENDER_CALLS.append(name)
    return format_html('<svg data-icon="{}" data-n="{}"></svg>', name, len(RENDER_CALLS))


def empty_renderer(name, *, css, config):
    RENDER_CALLS.append(name)
    return ""


COUNTING_LIBRARY = {
    "cnt": {"renderer": "tests.test1.test_form_button_checks.counting_renderer"},
    "nil": {"renderer": "tests.test1.test_form_button_checks.empty_renderer"},
}


@pytest.fixture
def calls():
    RENDER_CALLS.clear()
    yield RENDER_CALLS
    RENDER_CALLS.clear()


@pytest.fixture
def font_calls(monkeypatch):
    """Counts every built-in font_renderer call (the renderer cache is rebuilt around the patch)."""
    seen = []
    real = icons_module.font_renderer

    def spy(name, *, css, config):
        seen.append(name)
        return real(name, css=css, config=config)

    monkeypatch.setattr(icons_module, "font_renderer", spy)
    icons_module.reset_icon_cache()
    yield seen
    icons_module.reset_icon_cache()


def _strict(strict):
    return override_settings(CRUD_VIEWS_STRICT=strict)


def _floor(mode):
    return override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"form": mode})


def _w292(view_cls) -> list[tuple[str, str]]:
    found = []
    for check in view_cls.checks():
        for message in check.messages():
            match = W292_RE.match(message.msg)
            if message.id == "viewset.W292" and match:
                assert message.level == WARNING
                found.append(match.groups())
    return found


def _system_w292(view_cls) -> list[tuple[str, str]]:
    suffix = f" at {view_cls}"
    return [
        W292_RE.match(m.msg).groups()
        for m in check_viewsets()
        if m.id == "viewset.W292" and W292_RE.match(m.msg) and m.msg.endswith(suffix)
    ]


# --- the availability predicate --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "icons", "libraries", "expected"),
    [
        (None, None, None, False),
        ("", None, None, False),
        ("   ", None, None, False),
        ("save", None, None, True),
        ("save", {"save": None}, None, False),
        ("save", {"save": ""}, None, False),
        ("far:floppy-disk", None, None, True),
        ("my-raw icon-save", None, None, True),
        ("unknown:save", None, None, False),
        ("nope:save", None, {"nope": {"renderer": "tests.does.not.exist"}}, False),
        ("nope:save", None, {"nope": {"renderer": 5}}, False),
        ("nd:save", None, {"nd": "not-a-dict"}, False),
        ("cnt:save", None, COUNTING_LIBRARY, True),
        ("nil:save", None, COUNTING_LIBRARY, True),
        ("ui:floppy", None, HOST_LIBRARY, True),
        ("save", FORM_HOST_ICONS, HOST_LIBRARY, True),
        ("save", {**FORM_HOST_ICONS, "save": None}, HOST_LIBRARY, False),
    ],
    ids=repr,
)
def test_icon_availability_predicate(calls, font_calls, value, icons, libraries, expected):
    settings = {}
    if icons is not None:
        settings["CRUD_VIEWS_ICONS"] = icons
    if libraries is not None:
        settings["CRUD_VIEWS_ICON_LIBRARIES"] = libraries
    with override_settings(**settings):
        assert icons_module._icon_available(value) is expected
    # resolving a renderer is allowed, invoking one is not
    assert calls == [] and font_calls == []


FONT_CLASS_CASES = [
    pytest.param({}, "Icon library 'bad' uses the font renderer but has no 'class'.", id="omitted"),
    pytest.param({"class": None}, "Icon library 'bad' uses the font renderer but has no 'class'.", id="none"),
    pytest.param({"class": ""}, "Icon library 'bad' uses the font renderer but has no 'class'.", id="empty"),
    pytest.param({"class": 5}, "Icon library 'bad': 'class' must be a str format string, got int.", id="non-str"),
    pytest.param({"class": "x-{nam}"}, "Icon library 'bad': 'class' 'x-{nam}' is not a valid format", id="field"),
    pytest.param({"class": "x-{name"}, "Icon library 'bad': 'class' 'x-{name' is not a valid format", id="brace"),
]
FONT_RENDERERS = pytest.mark.parametrize("renderer", [{"renderer": "font"}, {}], ids=["font", "default"])


def _bad_library(config, renderer):
    return override_settings(CRUD_VIEWS_ICON_LIBRARIES={"bad": {**renderer, **config}})


@FONT_RENDERERS
@pytest.mark.parametrize(("config", "e354"), FONT_CLASS_CASES)
def test_invalid_builtin_font_class_is_unavailable_and_keeps_e354(font_calls, config, e354, renderer):
    with _bad_library(config, renderer):
        assert icons_module._icon_available("bad:save") is False
        messages = [m for m in icon_check_messages() if m.id == "crud_views.E354"]
    assert len(messages) == 1
    assert messages[0].level == ERROR
    assert messages[0].msg.startswith(e354)
    assert font_calls == []


@FONT_RENDERERS
@pytest.mark.parametrize(
    "config",
    [
        {"class": "x-{name}"},
        {"class": "{name}", "placement": "host"},
        {"class": "icon-{name}", "placement": "host", "standalone": "icon {name_class}"},
    ],
    ids=["element", "host", "host-standalone"],
)
def test_usable_builtin_font_class_is_available(font_calls, config, renderer):
    with _bad_library(config, renderer):
        assert icons_module._icon_available("bad:save") is True
        assert [m for m in icon_check_messages() if m.id == "crud_views.E354"] == []
    assert font_calls == []


def test_custom_renderer_needs_no_class(calls):
    with override_settings(CRUD_VIEWS_ICON_LIBRARIES={"xy": {"renderer": counting_renderer}}):
        assert icons_module._icon_available("xy:save") is True
    assert calls == []


# --- static W292: concrete package providers only --------------------------------------------------------------------


class _NoSubmitIcon(AuthorForm):
    submit_icon = None


class _UnknownPrefixForm(AuthorForm):
    submit_icon = "unknown:save"


class _BadFontForm(AuthorForm):
    submit_icon = "bad:save"


class _CountingForm(AuthorForm):
    submit_icon = "cnt:save"


class _RawClassForm(AuthorForm):
    submit_icon = "my-raw icon-save"


class _HookedSubmitForm(AuthorForm):
    submit_icon = None

    def get_submit_button_kwargs(self):
        return {"name": "submit", "value": "Hooked", "icon": None}


class _HookedCancelForm(AuthorForm):
    submit_icon = None

    def get_cancel_button(self):
        return Button("reset", "Back", icon=None, data_cv_cancel_url="/back/")


class _CustomHelperForm(AuthorForm):
    submit_icon = None

    @property
    def helper(self):
        helper = FormHelper()
        helper.layout = Layout(FormActions(Submit("submit", "Custom", icon=None)))
        return helper


class _DeleteNoSubmitIcon(CrispyDeleteForm):
    submit_icon = None


class _DeleteNoDeleteIcon(CrispyDeleteForm):
    delete_icon = None


class _DeleteCustomHelper(CrispyDeleteForm):
    delete_icon = None

    @property
    def helper(self):
        helper = FormHelper()
        helper.layout = Layout(FormActions(Submit("delete", "Remove", slot="form:delete", icon=None)))
        return helper


class _DeleteHookedKwargs(CrispyDeleteForm):
    delete_icon = None

    def get_delete_button_kwargs(self):
        return {"name": "delete", "value": "Remove", "icon": "delete"}


@pytest.fixture
def create_form(monkeypatch):
    def use(form_class, mode="icon"):
        monkeypatch.setattr(AuthorCreateView, "form_class", form_class)
        monkeypatch.setattr(AuthorCreateView, ATTR, {"submit": mode, "cancel": mode} if mode else None)

    return use


def test_default_package_forms_have_no_w292_in_icon_mode():
    with _floor("icon"):
        for view_cls in (AuthorCreateView, AuthorDeleteView, PublisherListView, CampaignWorkflowView):
            assert _w292(view_cls) == []
        assert [m for m in check_viewsets() if m.id == "viewset.W292"] == []


@pytest.mark.parametrize("mode", ["label", "both", None])
def test_missing_icons_outside_icon_mode_are_silent(create_form, mode):
    create_form(_NoSubmitIcon, mode)
    with override_settings(CRUD_VIEWS_ICONS={"cancel": None}):
        assert _w292(AuthorCreateView) == []


def test_missing_submit_icon_is_w292_through_check_viewsets(create_form):
    create_form(_NoSubmitIcon)
    assert _w292(AuthorCreateView) == [("submit", "_NoSubmitIcon")]
    assert _system_w292(AuthorCreateView) == [("submit", "_NoSubmitIcon")]
    (message,) = [m for m in check_viewsets() if m.id == "viewset.W292"]
    assert message.msg == (
        "form button 'submit' of _NoSubmitIcon renders icon-only but its icon None is not available; set a usable "
        "icon (submit_icon or CRUD_VIEWS_ICONS) or the form label mode 'label' or 'both' "
        f"at {AuthorCreateView}"
    )


@pytest.mark.parametrize(
    ("icons", "expected"),
    [
        ({"save": None}, [("submit", "AuthorForm")]),
        ({"save": ""}, [("submit", "AuthorForm")]),
        ({"cancel": None}, [("cancel", "AuthorForm")]),
        ({"save": "", "cancel": ""}, [("submit", "AuthorForm"), ("cancel", "AuthorForm")]),
    ],
    ids=repr,
)
def test_registry_disabled_semantic_icons_are_w292(create_form, icons, expected):
    create_form(AuthorForm)
    with override_settings(CRUD_VIEWS_ICONS=icons):
        assert _w292(AuthorCreateView) == expected


def test_unknown_direct_prefix_and_unusable_renderer_are_w292(create_form, calls):
    create_form(_UnknownPrefixForm)
    assert _w292(AuthorCreateView) == [("submit", "_UnknownPrefixForm")]
    create_form(_CountingForm)
    with override_settings(CRUD_VIEWS_ICON_LIBRARIES={"cnt": {"renderer": "tests.does.not.exist"}}):
        assert _w292(AuthorCreateView) == [("submit", "_CountingForm")]
        assert "crud_views.E351" in [m.id for m in icon_check_messages()]
    assert calls == []


def test_available_icons_are_silent_without_renderer_calls(create_form, calls, font_calls):
    for form_class, libraries in ((_RawClassForm, None), (_CountingForm, COUNTING_LIBRARY), (AuthorForm, None)):
        create_form(form_class)
        with override_settings(CRUD_VIEWS_ICON_LIBRARIES=libraries or {}):
            assert _w292(AuthorCreateView) == []
            assert [m for m in check_viewsets() if m.id == "viewset.W292"] == []
    assert calls == [] and font_calls == []


@FONT_RENDERERS
@pytest.mark.parametrize(("config", "e354"), FONT_CLASS_CASES)
def test_invalid_builtin_font_class_is_w292_and_e354(create_form, font_calls, config, e354, renderer):
    create_form(_BadFontForm)
    with _bad_library(config, renderer):
        assert _w292(AuthorCreateView) == [("submit", "_BadFontForm")]
        assert next(m.msg for m in icon_check_messages() if m.id == "crud_views.E354").startswith(e354)
    assert font_calls == []


@pytest.mark.parametrize("slot", [None, ""])
def test_host_icons_and_host_slot_opt_outs_are_not_missing(create_form, calls, slot):
    create_form(AuthorForm)
    with override_settings(CRUD_VIEWS_ICON_LIBRARIES=HOST_LIBRARY, CRUD_VIEWS_ICONS=FORM_HOST_ICONS):
        assert _w292(AuthorCreateView) == []
        with override_settings(CRUD_VIEWS_BUTTON_CLASSES={"form:icon-host": slot}):
            assert _w292(AuthorCreateView) == []
            with override_settings(CRUD_VIEWS_ICONS={**FORM_HOST_ICONS, "save": None}):
                # the opt-out is placement; a disabled semantic icon is still missing
                assert _w292(AuthorCreateView) == [("submit", "AuthorForm")]
    assert calls == []


@pytest.mark.parametrize("form_class", [_HookedSubmitForm, _CustomHelperForm])
def test_overridden_submit_providers_are_dynamic(create_form, form_class):
    create_form(form_class)
    # the submit control is request-dependent now; the inherited cancel stays statically known
    assert _w292(AuthorCreateView) == []
    with override_settings(CRUD_VIEWS_ICONS={"cancel": None}):
        expected = [] if form_class is _CustomHelperForm else [("cancel", form_class.__name__)]
        assert _w292(AuthorCreateView) == expected


def test_overridden_cancel_hook_is_dynamic(create_form):
    create_form(_HookedCancelForm)
    assert _w292(AuthorCreateView) == [("submit", "_HookedCancelForm")]


def test_request_dependent_form_class_is_skipped(create_form, monkeypatch):
    create_form(_NoSubmitIcon)

    def get_form_class(self):
        raise AssertionError("get_form_class called during checks")

    monkeypatch.setattr(AuthorCreateView, "get_form_class", get_form_class)
    assert _w292(AuthorCreateView) == []


def test_checks_never_instantiate_forms_or_helpers(create_form, monkeypatch):
    create_form(_NoSubmitIcon)

    def boom(*args, **kwargs):
        raise AssertionError("instantiated during checks")

    monkeypatch.setattr(_NoSubmitIcon, "__init__", boom)
    monkeypatch.setattr(PublisherFilterFormHelper, "__init__", boom)
    with _floor("icon"), override_settings(CRUD_VIEWS_ICONS={"filter": None}):
        assert _system_w292(AuthorCreateView) == [("submit", "_NoSubmitIcon")]
        assert _system_w292(PublisherListView) == [("filter-submit", "PublisherFilterFormHelper")]


@pytest.fixture
def delete_form(monkeypatch):
    def use(form_class):
        monkeypatch.setattr(AuthorDeleteView, "form_class", form_class)
        monkeypatch.setattr(AuthorDeleteView, ATTR, {"delete": "icon", "cancel": "icon", "submit": "icon"})

    return use


def test_delete_form_inspects_delete_and_cancel_never_submit(delete_form):
    delete_form(_DeleteNoSubmitIcon)
    assert _w292(AuthorDeleteView) == []
    delete_form(_DeleteNoDeleteIcon)
    assert _w292(AuthorDeleteView) == [("delete", "_DeleteNoDeleteIcon")]
    assert _system_w292(AuthorDeleteView) == [("delete", "_DeleteNoDeleteIcon")]
    with override_settings(CRUD_VIEWS_ICONS={"cancel": None}):
        assert _w292(AuthorDeleteView) == [("delete", "_DeleteNoDeleteIcon"), ("cancel", "_DeleteNoDeleteIcon")]
    with override_settings(CRUD_VIEWS_ICONS={"delete": None}):
        delete_form(CrispyDeleteForm)
        assert _w292(AuthorDeleteView) == [("delete", "CrispyDeleteForm")]


@pytest.mark.parametrize("form_class", [_DeleteCustomHelper, _DeleteHookedKwargs])
def test_overridden_delete_providers_are_dynamic(delete_form, form_class):
    delete_form(form_class)
    assert _w292(AuthorDeleteView) == []


def test_workflow_form_submit_uses_the_workflow_icon(monkeypatch):
    monkeypatch.setattr(CampaignWorkflowView, ATTR, {"submit": "icon"})
    assert _w292(CampaignWorkflowView) == []
    with override_settings(CRUD_VIEWS_ICONS={"workflow": None}):
        assert _w292(CampaignWorkflowView) == [("submit", "CampaignWorkflowForm")]
    with override_settings(CRUD_VIEWS_ICONS={"save": None}):
        assert _w292(CampaignWorkflowView) == []


class _NoActionsHelper(PublisherFilterFormHelper):
    def get_form_actions(self):
        return FormActions(Submit("submit", "Go", slot="form:filter-submit", icon=None))


def test_filter_helper_with_default_actions_is_statically_known(monkeypatch):
    monkeypatch.setattr(PublisherListView, ATTR, {"filter-submit": "icon", "filter-reset": "icon"})
    assert _w292(PublisherListView) == []
    with override_settings(CRUD_VIEWS_ICONS={"filter": None, "filter-reset": ""}):
        assert _w292(PublisherListView) == [
            ("filter-submit", "PublisherFilterFormHelper"),
            ("filter-reset", "PublisherFilterFormHelper"),
        ]
        monkeypatch.setattr(PublisherListView, "formhelper_class", _NoActionsHelper)
        assert _w292(PublisherListView) == []
        monkeypatch.setattr(PublisherListView, "formhelper_class", None)
        assert _w292(PublisherListView) == []


class _CarNoIcon(CarForm):
    submit_icon = None


class _TruckNoIcon(TruckForm):
    submit_icon = None


class _CarHooked(CarForm):
    def get_submit_button_kwargs(self):
        return {"name": "submit", "value": "Hooked", "icon": None}


@pytest.mark.parametrize("view_cls", [VehicleCreateView, VehicleUpdateView])
def test_concrete_polymorphic_forms_are_each_inspected_once(monkeypatch, view_cls):
    monkeypatch.setattr(view_cls, ATTR, {"submit": "icon", "cancel": "icon"})
    assert _w292(view_cls) == []
    monkeypatch.setattr(view_cls, "polymorphic_forms", {Car: _CarNoIcon, Truck: _CarNoIcon})
    assert _w292(view_cls) == [("submit", "_CarNoIcon")]
    monkeypatch.setattr(view_cls, "polymorphic_forms", {Car: _CarNoIcon, Truck: _TruckNoIcon})
    assert _w292(view_cls) == [("submit", "_CarNoIcon"), ("submit", "_TruckNoIcon")]
    assert _system_w292(view_cls) == [("submit", "_CarNoIcon"), ("submit", "_TruckNoIcon")]
    with override_settings(CRUD_VIEWS_ICONS={"cancel": None}):
        assert _w292(view_cls) == [
            ("submit", "_CarNoIcon"),
            ("cancel", "_CarNoIcon"),
            ("submit", "_TruckNoIcon"),
            ("cancel", "_TruckNoIcon"),
        ]
    for forms_value in (None, {Car: _CarHooked}, [(Car, _CarNoIcon)]):
        monkeypatch.setattr(view_cls, "polymorphic_forms", forms_value)
        assert _w292(view_cls) == []


def test_mode_errors_survive_and_hide_no_w292(create_form):
    create_form(_NoSubmitIcon)
    for strict in (True, False):
        with _strict(strict):
            # a malformed own map: E211 only, never a W292 or an exception
            AuthorCreateView.cv_form_actions_label_mode = "icon"
            ids = [m.id for m in check_viewsets()]
            assert "viewset.E211" in ids and "viewset.W292" not in ids
            AuthorCreateView.cv_form_actions_label_mode = None
            with _floor("nope"):
                ids = [m.id for m in check_viewsets()]
            assert "crud_views.E108" in ids and "viewset.W292" not in ids


# --- runtime: the dynamic guard in cv_button_data and real crispy renders ----------------------------------------


def _form_ctx(kind="submit", **kw):
    types = {"cancel": "button", "filter-reset": "reset"}
    data = {
        "cv_key": kind,
        "cv_type": types.get(kind, "submit"),
        "cv_name": kind,
        "cv_value": "Gö <b>",
        "cv_id": f"id-{kind}",
        "cv_label_mode": "icon",
        "cv_icon": None,
        "cv_attrs": {"data_cv_cancel_url": "/back/"} if kind == "cancel" else {},
    }
    data.update(kw)
    return data


MISSING_ICONS = [
    pytest.param({"cv_icon": None}, {}, id="none"),
    pytest.param({"cv_icon": ""}, {}, id="empty"),
    pytest.param({"cv_icon": "save"}, {"CRUD_VIEWS_ICONS": {"save": None}}, id="registry-none"),
    pytest.param({"cv_icon": "save"}, {"CRUD_VIEWS_ICONS": {"save": ""}}, id="registry-empty"),
    pytest.param({"cv_icon": "unknown:save"}, {}, id="unknown-prefix"),
    pytest.param(
        {"cv_icon": "cnt:save"},
        {"CRUD_VIEWS_ICON_LIBRARIES": {"cnt": {"renderer": "tests.does.not.exist"}}},
        id="unusable-renderer",
    ),
    pytest.param({"cv_icon": "bad:save"}, {"CRUD_VIEWS_ICON_LIBRARIES": {"bad": {"class": None}}}, id="font-class"),
]


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize(("ctx", "settings"), MISSING_ICONS)
def test_strict_missing_icon_raises_naming_the_kind(calls, font_calls, kind, ctx, settings):
    with override_settings(CRUD_VIEWS_STRICT=True, **settings), pytest.raises(ValueError) as info:
        cv_button_data(_form_ctx(kind, **ctx), "form")
    assert f"form button {kind!r} renders icon-only" in str(info.value)
    assert calls == [] and font_calls == []


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize(("ctx", "settings"), MISSING_ICONS)
def test_non_strict_missing_icon_logs_and_uses_the_label(caplog, calls, font_calls, kind, ctx, settings):
    caplog.set_level(logging.WARNING, logger=BUTTON_LOGGER)
    with override_settings(CRUD_VIEWS_STRICT=False, **settings):
        first = cv_button_data(_form_ctx(kind, **ctx), "form")
        second = cv_button_data(_form_ctx(kind, **ctx), "form")
    records = [r for r in caplog.records if r.name == BUTTON_LOGGER]
    # one warning per render, never a warn-once register
    assert len(records) == 2
    assert all(f"form button {kind!r} renders icon-only" in r.getMessage() for r in records)
    assert first == second
    assert first["cv_label_mode"] == "label"
    assert (first["cv_icon_class"], first["cv_icon_inline"]) == ("", True)
    assert "cv_title" not in first
    assert (first["cv_label"], first["cv_value"]) == ("Gö <b>", "Gö <b>")
    assert type(first["cv_label"]) is str
    assert set(first) <= FORM_LEAF_KEYS
    assert ("cv_cancel_url" in first) is (kind == "cancel")
    if kind == "cancel":
        assert first["cv_cancel_url"] == "/back/"
    for action_only in ("cv_href", "cv_submit_target", "cv_modal", "cv_tag", "cv_variant", "cv_disabled"):
        assert action_only not in first
    assert calls == [] and font_calls == []


def test_non_strict_fallback_keeps_caller_title_as_a_plain_attribute(caplog):
    with _strict(False):
        data = cv_button_data(_form_ctx(cv_attrs={"title": "Mine", "data_cv_tooltip": "x"}), "form")
    assert data["cv_label_mode"] == "label"
    assert data["cv_flat_attrs"] == ' data-cv-tooltip="x" title="Mine"'


def test_non_strict_missing_icon_and_label_keeps_the_empty_payload(caplog):
    caplog.set_level(logging.WARNING, logger=BUTTON_LOGGER)
    with _strict(False):
        data = cv_button_data(_form_ctx(cv_value="", cv_label=""), "form")
    assert (data["cv_label"], data["cv_value"], data["cv_label_mode"]) == ("", "", "label")
    assert "cv_title" not in data
    (record,) = [r for r in caplog.records if r.name == BUTTON_LOGGER]
    assert "neither an available icon" in record.getMessage()


@pytest.mark.parametrize("strict", [True, False])
@pytest.mark.parametrize("mode", ["both", "label"])
def test_missing_icon_outside_icon_mode_is_no_error(caplog, strict, mode):
    caplog.set_level(logging.WARNING, logger=BUTTON_LOGGER)
    with _strict(strict):
        data = cv_button_data(_form_ctx(cv_label_mode=mode, cv_icon="unknown:save"), "form")
    assert data["cv_label_mode"] == mode
    assert [r for r in caplog.records if r.name == BUTTON_LOGGER] == []


@pytest.mark.parametrize("strict", [True, False])
def test_caller_kind_and_type_stay_validated(strict):
    with _strict(strict):
        for bad in ({"cv_key": "primary"}, {"cv_type": "image"}):
            with pytest.raises(ValueError):
                cv_button_data(_form_ctx(**bad), "form")
        with pytest.raises(ValueError):
            cv_button_data(_form_ctx(), "form", kind="menu-item")


class _OwnerlessForm(forms.Form):
    pass


CRISPY = Template("{% load crispy_forms_tags %}{% crispy form helper %}")


def _crispy(*controls) -> list:
    helper = FormHelper()
    helper.form_tag = False
    helper.layout = Layout(FormActions(*controls))
    markup = CRISPY.render(Context({"form": _OwnerlessForm(), "helper": helper}))
    return lxml_html.fragment_fromstring(markup, create_parent="div").cssselect("button")


@pytest.mark.parametrize("mode", ["icon", "both"])
def test_counting_inline_renderer_runs_once_per_icon_render(calls, mode):
    with override_settings(CRUD_VIEWS_ICON_LIBRARIES=COUNTING_LIBRARY), _floor(mode):
        (first,) = _crispy(Submit("submit", "Save", icon="cnt:save"))
        assert calls == ["save"]
        assert [svg.get("data-n") for svg in first.cssselect("svg")] == ["1"]
        (second,) = _crispy(Submit("submit", "Save", icon="cnt:save"))
    # a second render calls the renderer again and shares no cached output
    assert calls == ["save", "save"]
    assert [svg.get("data-n") for svg in second.cssselect("svg")] == ["2"]


def test_counting_renderer_is_not_called_in_label_mode_or_checks(calls, create_form):
    with override_settings(CRUD_VIEWS_ICON_LIBRARIES=COUNTING_LIBRARY):
        with _floor("label"):
            (button,) = _crispy(Submit("submit", "Save", icon="cnt:save"))
        assert not button.cssselect("svg")
        create_form(_CountingForm)
        assert _w292(AuthorCreateView) == []
        check_viewsets()
    assert calls == []


def test_custom_renderer_with_empty_markup_is_called_once_and_not_a_missing_icon(calls, caplog):
    caplog.set_level(logging.WARNING, logger=BUTTON_LOGGER)
    with override_settings(CRUD_VIEWS_ICON_LIBRARIES=COUNTING_LIBRARY), _floor("icon"), _strict(True):
        (button,) = _crispy(Submit("submit", "Save", icon="nil:save"))
    assert calls == ["save"]
    assert button.get("title") == "Save"
    assert [r for r in caplog.records if r.name == BUTTON_LOGGER] == []


@pytest.mark.parametrize("strict", [True, False])
@pytest.mark.parametrize("mode", ["icon", "both"])
def test_disabled_semantic_icon_never_calls_a_renderer(calls, font_calls, caplog, strict, mode):
    icons = {"save": None}
    registry = override_settings(CRUD_VIEWS_ICONS=icons, CRUD_VIEWS_ICON_LIBRARIES=COUNTING_LIBRARY)
    with registry, _floor(mode), _strict(strict):
        if strict and mode == "icon":
            with pytest.raises(ValueError):
                _crispy(Submit("submit", "Save"))
        else:
            (button,) = _crispy(Submit("submit", "Save"))
            assert not button.cssselect("i, svg")
            assert button.cssselect("span")[-1].text == "Save"
    assert calls == [] and font_calls == []


@pytest.mark.parametrize("strict", [True, False])
@pytest.mark.parametrize("slot", ["default", None, ""])
def test_host_form_renders_without_inline_probes_or_false_fallback(calls, font_calls, caplog, strict, slot):
    caplog.set_level(logging.WARNING, logger=BUTTON_LOGGER)
    classes = {} if slot == "default" else {"CRUD_VIEWS_BUTTON_CLASSES": {"form:icon-host": slot}}
    host = override_settings(CRUD_VIEWS_ICON_LIBRARIES=HOST_LIBRARY, CRUD_VIEWS_ICONS=FORM_HOST_ICONS, **classes)
    with host, _floor("icon"), _strict(strict):
        data = cv_button_data(_form_ctx(cv_icon="save"), "form")
        (button,) = _crispy(Submit("submit", "Save"))
    assert data["cv_icon_inline"] is False
    assert data["cv_icon_class"] == ("icon-floppy" if slot == "default" else "")
    assert ("icon-floppy" in button.get("class").split()) is (slot == "default")
    assert not button.cssselect("i, svg")
    assert button.get("title") == "Save"
    assert [r for r in caplog.records if r.name == BUTTON_LOGGER] == []
    assert calls == [] and font_calls == []


@pytest.mark.parametrize("strict", [True, False])
def test_disabled_host_semantic_icon_follows_the_missing_icon_policy(caplog, strict):
    caplog.set_level(logging.WARNING, logger=BUTTON_LOGGER)
    icons = {**FORM_HOST_ICONS, "save": None}
    host = override_settings(CRUD_VIEWS_ICON_LIBRARIES=HOST_LIBRARY, CRUD_VIEWS_ICONS=icons)
    with host, _floor("icon"), _strict(strict):
        if strict:
            with pytest.raises(ValueError, match="form button 'submit'"):
                _crispy(Submit("submit", "Save"))
            return
        (button,) = _crispy(Submit("submit", "Save"))
    assert button.get("class").split() == ["btn", "btn-primary"]
    assert button.get("title") is None and button.get("data-cv-tooltip") is None
    assert [s.text for s in button.cssselect("span")] == ["Save"]
    assert len([r for r in caplog.records if r.name == BUTTON_LOGGER]) == 1


@pytest.mark.parametrize("strict", [True, False])
@FONT_RENDERERS
@pytest.mark.parametrize(("config", "e354"), FONT_CLASS_CASES)
def test_invalid_font_class_runtime_fallback(font_calls, caplog, strict, renderer, config, e354):
    caplog.set_level(logging.WARNING, logger=BUTTON_LOGGER)
    with _bad_library(config, renderer), _floor("icon"), _strict(strict):
        if strict:
            with pytest.raises(ValueError, match="form button 'submit'"):
                _crispy(Submit("submit", "Save", icon="bad:save"))
        else:
            (button,) = _crispy(Submit("submit", "Save", icon="bad:save"))
            assert button.get("title") is None and button.get("data-cv-tooltip") is None
            assert [s.text for s in button.cssselect("span")] == ["Save"]
            assert len([r for r in caplog.records if r.name == BUTTON_LOGGER]) == 1
    assert font_calls == []


@pytest.mark.parametrize("strict", [True, False])
def test_raw_class_and_valid_font_icons_render_once_without_fallback(font_calls, caplog, strict):
    caplog.set_level(logging.WARNING, logger=BUTTON_LOGGER)
    with _floor("icon"), _strict(strict), override_settings(CRUD_VIEWS_ICONS={}):
        (raw,) = _crispy(Submit("submit", "Save", icon="my-raw icon-save"))
        (fa,) = _crispy(Submit("submit", "Save"))
    assert raw.cssselect("i")[0].get("class") == "my-raw icon-save"
    assert fa.cssselect("i")[0].get("class") == "fa-regular fa-floppy-disk"
    # the raw class renders through font_renderer once, the far prefix once
    assert font_calls == ["my-raw icon-save", "floppy-disk"]
    assert [r for r in caplog.records if r.name == BUTTON_LOGGER] == []


# real endpoints: request-dependent and custom providers that the static check skips


def _endpoint_buttons(client, path, name):
    response = client.get(path)
    assert response.status_code == 200
    return lxml_html.fromstring(response.content.decode()).cssselect(f'button[name="{name}"]')


def _assert_label_fallback(button, text):
    assert button.get("title") is None and button.get("data-cv-tooltip") is None
    assert not button.cssselect("span.visually-hidden, i, svg")
    assert [s.text for s in button.cssselect("span")] == [text]


@pytest.mark.django_db
@pytest.mark.parametrize("strict", [True, False])
@pytest.mark.parametrize("form_class", [_HookedSubmitForm, _CustomHelperForm])
def test_custom_submit_hooks_follow_the_runtime_policy(client_user_author_add, create_form, strict, form_class):
    create_form(form_class)
    text = "Hooked" if form_class is _HookedSubmitForm else "Custom"
    with _strict(strict):
        if strict:
            with pytest.raises(ValueError, match="form button 'submit'"):
                client_user_author_add.get("/author/create/")
            return
        (button,) = _endpoint_buttons(client_user_author_add, "/author/create/", "submit")
    _assert_label_fallback(button, text)


@pytest.mark.django_db
@pytest.mark.parametrize("strict", [True, False])
def test_custom_delete_helper_follows_the_runtime_policy(
    client_user_author_delete, delete_form, author_douglas_adams, strict
):
    delete_form(_DeleteCustomHelper)
    path = f"/author/{author_douglas_adams.pk}/delete/"
    with _strict(strict):
        if strict:
            with pytest.raises(ValueError, match="form button 'delete'"):
                client_user_author_delete.get(path)
            return
        (button,) = _endpoint_buttons(client_user_author_delete, path, "delete")
    _assert_label_fallback(button, "Remove")


@pytest.mark.django_db
@pytest.mark.parametrize("strict", [True, False])
@pytest.mark.parametrize("form_class", [_CarNoIcon, _CarHooked])
def test_polymorphic_create_follows_the_runtime_policy(client_user_vehicle_add, monkeypatch, strict, form_class):
    monkeypatch.setattr(VehicleCreateView, "polymorphic_forms", {Car: form_class})
    monkeypatch.setattr(VehicleCreateView, ATTR, {"submit": "icon"})
    path = f"/vehicle/create/ct/{ContentType.objects.get_for_model(Car).id}/"
    with _strict(strict):
        if strict:
            with pytest.raises(ValueError, match="form button 'submit'"):
                client_user_vehicle_add.get(path)
            return
        (button,) = _endpoint_buttons(client_user_vehicle_add, path, "submit")
    _assert_label_fallback(button, "Hooked" if form_class is _CarHooked else button.get("value"))


@pytest.mark.django_db
@pytest.mark.parametrize("strict", [True, False])
def test_polymorphic_update_follows_the_runtime_policy(client_user_vehicle_change, monkeypatch, car_sedan, strict):
    monkeypatch.setattr(VehicleUpdateView, "polymorphic_forms", {Car: _CarNoIcon})
    monkeypatch.setattr(VehicleUpdateView, ATTR, {"submit": "icon"})
    path = f"/vehicle/{car_sedan.pk}/update/"
    with _strict(strict):
        if strict:
            with pytest.raises(ValueError, match="form button 'submit'"):
                client_user_vehicle_change.get(path)
            return
        (button,) = _endpoint_buttons(client_user_vehicle_change, path, "submit")
    _assert_label_fallback(button, button.get("value"))


@pytest.mark.django_db
@pytest.mark.parametrize("strict", [True, False])
def test_filter_helper_follows_the_runtime_policy(client_user_publisher_view, monkeypatch, strict):
    monkeypatch.setattr(PublisherListView, ATTR, {"filter-submit": "icon"})
    with _strict(strict), override_settings(CRUD_VIEWS_ICONS={"filter": None}):
        if strict:
            with pytest.raises(ValueError, match="form button 'filter-submit'"):
                client_user_publisher_view.get("/publisher/")
            return
        (button,) = _endpoint_buttons(client_user_publisher_view, "/publisher/", "submit")
    _assert_label_fallback(button, "Apply Filter")


def test_filter_helper_class_is_never_the_package_base():
    # sanity: the static reach reads the configured subclass, inheriting the default get_form_actions
    assert PublisherFilterFormHelper.get_form_actions is ListViewFilterFormHelper.get_form_actions
