"""Startup registrations reach both inert page-config aliases."""

import json
from unittest.mock import patch

import pytest
from django.template import Context, Template
from django.test import RequestFactory
from lxml import html

from crud_views.lib import js_config, register_js_namespace, register_tooltip_placements


@pytest.fixture(autouse=True)
def isolate_js_config(monkeypatch):
    monkeypatch.setattr(js_config, "_js_namespace", js_config._js_namespace)
    monkeypatch.setattr(js_config, "_tooltip_placements", js_config._tooltip_placements.copy())


def render_config(alias="cv_config", *, autoescape=True):
    request = RequestFactory().get("/theme/?a=1&b=2")
    with patch("django.middleware.csrf.get_token", return_value="fixed-csrf-token"):
        rendered = Template("{% load crud_views %}{% " + alias + " %}").render(
            Context({"request": request}, autoescape=autoescape)
        )
    return rendered, html.fromstring(rendered).get_element_by_id("cv-config")


@pytest.mark.parametrize("alias", ["cv_config", "cv_const_js"])
def test_config_defaults(alias):
    rendered, config = render_config(alias)
    assert config.get("data-js-namespace") == "bootstrap"
    assert json.loads(config.get("data-tooltip-placements")) == {}
    assert rendered.count('data-js-namespace="bootstrap"') == 1
    assert rendered.count('data-tooltip-placements="{}"') == 1


@pytest.mark.parametrize("alias", ["cv_config", "cv_const_js"])
def test_registered_config(alias, isolate_data_prefix):
    from crud_views.lib import register_data_prefix

    register_data_prefix("coreui")
    register_js_namespace("tabler")
    register_tooltip_placements({"context": "bottom"})
    rendered, config = render_config(alias)
    assert config.get("data-data-prefix") == "coreui"
    assert config.get("data-js-namespace") == "tabler"
    assert json.loads(config.get("data-tooltip-placements")) == {"context": "bottom"}
    assert "&quot;context&quot;: &quot;bottom&quot;" in rendered


@pytest.mark.parametrize("name", ["bootstrap", "coreui", "tabler", "_theme", "$theme", "Theme_1$", "a0"])
def test_namespace_accepts_identifiers_and_last_valid_wins(name):
    register_js_namespace("previous")
    register_js_namespace(name)
    assert js_config.get_js_namespace() == name


@pytest.mark.parametrize(
    "name",
    ["", "a.b", "a-b", "1a", " a", "a ", "a\nb", "a\n", "é", None, 1, True, [], {}, b"bootstrap"],
)
def test_invalid_namespace_preserves_state(name):
    register_js_namespace("tabler")
    with pytest.raises(ValueError):
        register_js_namespace(name)
    assert js_config.get_js_namespace() == "tabler"


LOCATIONS = ["context", "list", "card", "card-order", "formset", "object-detail", "form", ""]


@pytest.mark.parametrize("location", LOCATIONS)
@pytest.mark.parametrize("placement", ["top", "bottom", "left", "right", "auto"])
def test_all_location_placement_pairs(location, placement):
    register_tooltip_placements({location: placement})
    assert js_config.get_tooltip_placements() == {location: placement}


@pytest.mark.parametrize("placements", [None, [], [("context", "bottom")], "context", 1, True, set()])
def test_invalid_mapping_container_preserves_state(placements):
    register_tooltip_placements({"form": "left"})
    with pytest.raises(ValueError):
        register_tooltip_placements(placements)
    assert js_config.get_tooltip_placements() == {"form": "left"}


@pytest.mark.parametrize("location", ["unknown", "Context", "context\n", 1, None, ("context",)])
def test_invalid_location_is_atomic_after_valid_pair(location):
    register_tooltip_placements({"form": "left"})
    with pytest.raises(ValueError):
        register_tooltip_placements({"context": "bottom", location: "top"})
    assert js_config.get_tooltip_placements() == {"form": "left"}


@pytest.mark.parametrize("placement", ["unknown", "Top", "top\n", "", None, 1, True, [], {}, set()])
def test_invalid_placement_is_atomic_after_valid_pair(placement):
    register_tooltip_placements({"form": "left"})
    with pytest.raises(ValueError):
        register_tooltip_placements({"context": "bottom", "list": placement})
    assert js_config.get_tooltip_placements() == {"form": "left"}


def test_mapping_replacement_reset_and_snapshot_isolation():
    original = {"context": "bottom"}
    register_tooltip_placements(original)
    original["context"] = "invalid"
    snapshot = js_config.get_tooltip_placements()
    snapshot["list"] = "right"
    assert js_config.get_tooltip_placements() == {"context": "bottom"}
    register_tooltip_placements({"form": "left"})
    assert js_config.get_tooltip_placements() == {"form": "left"}
    register_tooltip_placements({})
    assert js_config.get_tooltip_placements() == {}


@pytest.mark.parametrize("prefix_first", [True, False])
def test_namespace_and_prefix_are_independent(prefix_first, isolate_data_prefix):
    from crud_views.lib import register_data_prefix
    from crud_views.lib.data_prefix import get_data_prefix

    calls = [(register_data_prefix, "coreui"), (register_js_namespace, "tabler")]
    for register, value in calls if prefix_first else reversed(calls):
        register(value)
    assert get_data_prefix() == "coreui"
    assert js_config.get_js_namespace() == "tabler"


@pytest.mark.parametrize("alias", ["cv_config", "cv_const_js"])
@pytest.mark.parametrize("autoescape", [True, False])
def test_render_time_snapshots_and_escaped_round_trip(alias, autoescape):
    mapping = dict(zip(LOCATIONS, ["top", "bottom", "left", "right", "auto", "top", "bottom", "left"], strict=True))
    for namespace, placements in [("coreui", {"context": "bottom"}), ("tabler", mapping), ("bootstrap", {})]:
        register_js_namespace(namespace)
        register_tooltip_placements(placements)
        rendered, config = render_config(alias, autoescape=autoescape)
        assert config.get("data-js-namespace") == namespace
        assert json.loads(config.get("data-tooltip-placements")) == placements
        if placements:
            assert "&quot;context&quot;" in rendered
            assert "&quot;: &quot;" in rendered
        assert config.get("data-request-path") == "/theme/"
        assert config.get("data-query-string") == "a=1&b=2"
        assert config.get("data-csrf-token") == "fixed-csrf-token"
