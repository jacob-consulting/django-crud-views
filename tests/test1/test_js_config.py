"""Startup registrations reach both inert page-config aliases."""

import json
from unittest.mock import patch

import pytest
from django.template import Context, Template
from django.test import RequestFactory
from lxml import html


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
