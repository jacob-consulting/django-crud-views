"""Execute published theme-prefix recipes against the real template tags."""

import sys
from types import ModuleType

from django.template import Context, Template

from crud_views.lib import register_data_prefix
from tests.test1.test_heading_docs import ROOT, recipe

THEME = ROOT / "docs/reference/theme.md"


def test_data_prefix_documented_registration(isolate_data_prefix, monkeypatch):
    module = ModuleType("prefix_theme")
    module.__file__ = str(THEME)
    monkeypatch.setitem(sys.modules, "prefix_theme", module)
    namespace = {}
    exec(compile(recipe(THEME, "### Data-attribute prefix", "python"), str(THEME), "exec"), namespace)
    config = namespace["PrefixThemeConfig"]("prefix_theme", module)
    tag = Template("{% load crud_views %}{% cv_data_prefix %}")
    assert tag.render(Context()) == "bs"
    config.ready()
    assert tag.render(Context()) == "coreui"
    config.ready()
    assert tag.render(Context()) == "coreui"
    register_data_prefix("later-theme")
    assert tag.render(Context()) == "later-theme"
