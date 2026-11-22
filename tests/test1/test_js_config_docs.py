"""Execute the published startup recipe through both real page-config tags."""

import json
import sys
from types import ModuleType

import pytest

from crud_views.lib import js_config, register_tooltip_placements
from tests.test1.test_heading_docs import ROOT, recipe
from tests.test1.test_js_config import render_config

THEME = ROOT / "docs/reference/theme.md"


@pytest.fixture(autouse=True)
def isolate_js_config(monkeypatch):
    monkeypatch.setattr(js_config, "_js_namespace", js_config._js_namespace)
    monkeypatch.setattr(js_config, "_tooltip_placements", js_config._tooltip_placements.copy())


@pytest.mark.parametrize("alias", ["cv_config", "cv_const_js"])
def test_documented_js_theme_registration(alias, isolate_data_prefix, monkeypatch):
    module = ModuleType("js_theme")
    module.__file__ = str(THEME)
    monkeypatch.setitem(sys.modules, "js_theme", module)
    namespace = {}
    exec(
        compile(recipe(THEME, "### JavaScript namespace and tooltip placements", "python"), str(THEME), "exec"),
        namespace,
    )
    config = namespace["JsThemeConfig"]("js_theme", module)
    assert config.name == "js_theme"

    for _ in range(2):
        config.ready()
        rendered, element = render_config(alias)
        assert element.get("data-data-prefix") == "coreui"
        assert element.get("data-js-namespace") == "coreui"
        assert json.loads(element.get("data-tooltip-placements")) == {"context": "bottom"}
        assert "&quot;context&quot;: &quot;bottom&quot;" in rendered

    for placements in ({"list": "right"}, {}):
        register_tooltip_placements(placements)
        _, element = render_config(alias)
        assert json.loads(element.get("data-tooltip-placements")) == placements
        assert element.get("data-data-prefix") == "coreui"
        assert element.get("data-js-namespace") == "coreui"
