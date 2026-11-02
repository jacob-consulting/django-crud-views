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
from crud_views.lib.view import label_mode

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
