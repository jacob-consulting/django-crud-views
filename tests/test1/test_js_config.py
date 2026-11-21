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
