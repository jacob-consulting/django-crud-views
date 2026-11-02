"""Theme label floors preserve public owner precedence and live project settings."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from django import forms
from django.conf import settings
from django.template import Context, Template
from django.test import override_settings
from lxml import html

from crud_views.lib.crispy import Submit
from crud_views.lib.settings import crud_views_settings
from crud_views.lib.view import ContextButton, label_mode
from tests.test1.app.views import AuthorCreateView, AuthorDetailView, AuthorUpdateView, cv_author

PACKAGE = {"context": "icon", "list": "icon", "card": "both", "form": "label"}


@pytest.fixture(autouse=True)
def no_project_floor():
    with override_settings():
        if hasattr(settings, "CRUD_VIEWS_LABEL_MODE_DEFAULTS"):
            del settings.CRUD_VIEWS_LABEL_MODE_DEFAULTS
        yield


def register(defaults):
    api = getattr(label_mode, "register_label_mode_defaults", None)
    assert callable(api), "themes need the public register_label_mode_defaults API"
    return api(defaults)


def render_submit(owner=None):
    form = forms.Form()
    if owner is not None:
        form.cv_view = owner
    helper = FormHelper()
    helper.form_tag = False
    helper.layout = Layout(Submit("submit", "Save"))
    markup = Template("{% load crispy_forms_tags %}{% crispy form helper %}").render(
        Context({"form": form, "helper": helper})
    )
    return html.fragment_fromstring(markup, create_parent="div").cssselect("button")[0]


def assert_both(button):
    assert button.cssselect("i, svg")
    assert button.xpath("./span[not(@class)]/text()") == ["Save"]
    assert not button.cssselect(".visually-hidden")


def test_theme_registration_render():
    assert register({"form": "both"}) is None
    assert_both(render_submit())
    assert label_mode.default_label_mode("form") == "both"
    assert dict(label_mode.LABEL_MODE_DEFAULTS) == PACKAGE


def test_registration_merge_copy_and_snapshot():
    supplied = {"form": "both", "list": "label"}
    register(supplied)
    previous = label_mode._THEME_LABEL_MODE_DEFAULTS
    supplied["form"] = "icon"
    assert label_mode.default_label_mode("form") == "both"
    register({"context": "both", "form": "label"})
    assert previous == {"form": "both", "list": "label"}
    assert {key: label_mode.default_label_mode(key) for key in PACKAGE} == {
        "context": "both",
        "list": "label",
        "card": "both",
        "form": "label",
    }


@pytest.mark.parametrize("strict", [False, True])
@pytest.mark.parametrize(
    "invalid",
    [
        None,
        [],
        "both",
        1,
        {"form": None},
        {"form": "Both"},
        {"form": []},
        {"form": "both", "toolbar": "icon"},
        {"list": "label", "form": "bad"},
        {1: "both"},
    ],
)
def test_registration_atomicity(strict, invalid):
    register({"form": "icon", "list": "both"})
    with (
        override_settings(CRUD_VIEWS_STRICT=strict),
        pytest.raises(ValueError, match="register_label_mode_defaults") as error,
    ):
        register(invalid)
    assert "label" in str(error.value) and "icon" in str(error.value) and "both" in str(error.value)
    assert {key: label_mode.default_label_mode(key) for key in PACKAGE} == {**PACKAGE, "form": "icon", "list": "both"}


def test_registration_concurrent_merges_keep_all_keys():
    barrier = Barrier(4)

    def add(location):
        barrier.wait(timeout=5)
        register({location: "label"})

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(add, PACKAGE))
    assert {key: label_mode.default_label_mode(key) for key in PACKAGE} == dict.fromkeys(PACKAGE, "label")


def test_registration_card_theme_floor_nested_settings():
    register({"card": "icon"})
    assert label_mode.default_label_mode("card") == "icon"
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"card": "label"}):
        assert label_mode.default_label_mode("card") == "label"
        with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"form": "both"}):
            assert label_mode.default_label_mode("card") == "icon"
        assert label_mode.default_label_mode("card") == "label"
    assert label_mode.default_label_mode("card") == "icon"


def test_registration_isolation_first():
    register({"form": "both", "card": "label"})
    assert label_mode.default_label_mode("form") == "both"


def test_registration_isolation_second():
    # Consecutive tests in the serial registration run never request the isolation fixture.
    assert {key: label_mode.default_label_mode(key) for key in PACKAGE} == PACKAGE


def test_theme_setting_fallback(caplog):
    register({"form": "both"})
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS=None, CRUD_VIEWS_STRICT=False):
        assert label_mode.default_label_mode("form") == "both"
        assert_both(render_submit())
    assert len(caplog.records) == 1
    assert "the form button uses 'both'" in caplog.records[0].getMessage()


@pytest.mark.parametrize("theme", [True, False])
@pytest.mark.parametrize("configured", [None, [], "bad-map", {"form": None}, {"form": "bad-mode"}])
def test_theme_setting_fallback_strict_and_package(theme, configured, caplog):
    if theme:
        register({"form": "both"})
    with (
        override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS=configured, CRUD_VIEWS_STRICT=True),
        pytest.raises(ValueError, match="setting CRUD_VIEWS_LABEL_MODE_DEFAULTS"),
    ):
        label_mode.default_label_mode("form")
    assert caplog.records == []
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS=configured, CRUD_VIEWS_STRICT=False):
        expected = "both" if theme else "label"
        assert label_mode.default_label_mode("form") == expected
        assert label_mode.default_label_mode("form") == expected
    assert len(caplog.records) == 1
    assert f"the form button uses {expected!r}" in caplog.records[0].getMessage()


@pytest.mark.parametrize("owner_map", [["owner-bad"], {"submit": "owner-bad"}])
def test_composed_invalid_owner_and_setting_use_effective_theme(owner_map, monkeypatch, caplog):
    register({"form": "both"})
    monkeypatch.setattr(AuthorCreateView, "cv_form_actions_label_mode", owner_map)
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS=["project-bad"], CRUD_VIEWS_STRICT=False):
        for _ in range(2):
            assert label_mode.form_label_mode(owner_map, "submit") == "both"
            assert_both(render_submit(AuthorCreateView))
    messages = [r.getMessage() for r in caplog.records if r.name == label_mode.__name__]
    assert len(messages) == 2
    assert any("setting CRUD_VIEWS_LABEL_MODE_DEFAULTS" in message for message in messages)
    assert any("form actions label mode" in message for message in messages)
    assert all("the form button uses 'both'" in message for message in messages)


@pytest.mark.parametrize("owner_map", [["owner-bad"], {"submit": "owner-bad"}])
def test_composed_invalid_owner_strict_never_resolves_setting(owner_map, monkeypatch, caplog):
    register({"form": "both"})
    monkeypatch.setattr(AuthorCreateView, "cv_form_actions_label_mode", owner_map)

    def forbidden():
        pytest.fail("strict owner rejection must happen before entering settings fallback")

    monkeypatch.setattr(label_mode, "_raw_label_mode_defaults", forbidden)
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS=["project-bad"], CRUD_VIEWS_STRICT=True):
        with pytest.raises(ValueError, match="form actions label mode"):
            label_mode.form_label_mode(owner_map, "submit")
        with pytest.raises(ValueError, match="form actions label mode"):
            render_submit(AuthorCreateView)
    assert caplog.records == []


def test_project_and_whole_owner_maps_keep_precedence(monkeypatch):
    register({"form": "both", "context": "both"})
    monkeypatch.setattr(cv_author, "form_actions_label_mode", {"submit": "icon"})
    monkeypatch.setattr(crud_views_settings, "form_actions_label_mode", {"submit": "label"})
    monkeypatch.setattr(AuthorCreateView, "cv_form_actions_label_mode", {"cancel": "label"})
    # The chosen view map excludes submit: it uses the floor, never the lower owner's explicit entry.
    assert_both(render_submit(AuthorCreateView))
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"form": "icon"}):
        assert render_submit(AuthorCreateView).cssselect("span.visually-hidden")
        monkeypatch.setattr(AuthorCreateView, "cv_form_actions_label_mode", {"submit": "label"})
        assert not render_submit(AuthorCreateView).cssselect("i, svg, .visually-hidden")
    monkeypatch.setattr(AuthorCreateView, "cv_form_actions_label_mode", {})
    assert_both(render_submit(AuthorCreateView))
    explicit = ContextButton(key="update", label_mode="label")
    assert AuthorDetailView.cv_get_action_label_mode("context", "update", explicit) == "label"
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_label_mode", {"update": "icon"})
    assert AuthorDetailView.cv_get_action_label_mode("context", "update", explicit) == "icon"


def test_theme_effective_checks_context(monkeypatch):
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions", ["update"])
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_label_mode", {})
    monkeypatch.setattr(AuthorUpdateView, "cv_context_action_label_mode", None)
    monkeypatch.setattr(AuthorUpdateView, "cv_icon_action", None)

    def warnings():
        return [m for c in AuthorDetailView.checks() for m in c.messages() if m.id == "viewset.W292"]

    register({"context": "label"})
    assert warnings() == []
    register({"context": "icon"})
    assert len(warnings()) == 1
    with override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS={"context": "both"}):
        assert warnings() == []
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_label_mode", {"update": "label"})
    assert warnings() == []
    monkeypatch.setattr(AuthorDetailView, "cv_context_actions_label_mode", {})
    monkeypatch.setattr(AuthorUpdateView, "cv_icon_action", "fa-solid fa-pen")
    assert warnings() == []
