"""Execute published theme-prefix recipes against the real template tags."""

import sys
from types import ModuleType

import pytest
from django.template import Context, Template
from django.test import override_settings
from lxml import html

from crud_views.lib import register_data_prefix
from crud_views_object_detail.lib.resolvers import ResolvedGroup, ResolvedProperty
from tests.test1.od.test_badge_semantics import template_settings
from tests.test1.test_heading_docs import ROOT, recipe
from tests.test1.test_presentation_migration_docs import copied_templates, render

THEME = ROOT / "docs/reference/theme.md"
ACTIONS = ROOT / "docs/reference/action_menus.md"
HOSTILE = '<img src=x onerror="bad"> & text'
ICON_SETTINGS = {
    "CRUD_VIEWS_ICON_LIBRARIES": {"host": {"renderer": "font", "placement": "host", "class": "icon-{name}"}},
    "CRUD_VIEWS_BUTTON_CLASSES": {"heading-group:icon-host": '{name_class}" onclick="attack'},
}


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


@pytest.mark.parametrize("prefix", ["bs", "coreui"])
@pytest.mark.parametrize("location", ["list", "context", "card"])
def test_data_prefix_documented_action_toggle(isolate_data_prefix, prefix, location):
    register_data_prefix(prefix)
    output = Template(recipe(ACTIONS, "### Example: a split-style toggle")).render(Context({"cv_location": location}))
    button = html.fromstring(output)
    assert button.get(f"data-{prefix}-toggle") == "dropdown"
    assert button.get(f"data-{prefix}-popper-config") == ('{"strategy":"fixed"}' if location == "list" else None)
    assert button.get("type") == "button"
    assert button.get("aria-expanded") == "false"
    assert button.get("aria-label") == "More actions"
    assert button.text_content().strip() == "More actions"
    if prefix != "bs":
        assert "data-bs-" not in output


@pytest.mark.parametrize("prefix", ["bs", "coreui"])
@pytest.mark.parametrize("pack", ["tabs-vertical", "accordion"])
@pytest.mark.parametrize("count", [0, 1, 2])
def test_data_prefix_documented_layouts(isolate_data_prefix, prefix, pack, count):
    register_data_prefix(prefix)
    groups = [
        ResolvedGroup(HOSTILE, id=key, icon="host:edit", properties=[ResolvedProperty("name", HOSTILE, HOSTILE)])
        for key in ["first", "second"][:count]
    ]
    with override_settings(TEMPLATES=template_settings(copied_templates(pack)), **ICON_SETTINGS):
        output = render(groups, pack)
        assert render(groups, pack) == output
        other = html.fromstring(render(groups, pack, "author-modal"))
    tree = html.fromstring(output)
    controls = tree.cssselect(f"button[data-{prefix}-toggle]")
    assert len(controls) == count
    assert not tree.cssselect("img, [onerror], [onclick]")
    if count:
        assert HOSTILE in tree.text_content()
    ids = tree.xpath("descendant-or-self::*/@id")
    assert len(ids) == len(set(ids))
    assert set(ids).isdisjoint(other.xpath("descendant-or-self::*/@id"))
    if prefix != "bs":
        assert "data-bs-" not in output
    for index, control in enumerate(controls):
        expected = f"cvod-c11-author-page-s{len(groups[index].id)}-{groups[index].id}"
        assert control.get("id") == expected + "-control"
        assert control.get("aria-controls") == expected + "-panel"
        assert control.get(f"data-{prefix}-target") == "#" + expected + "-panel"
        assert 'icon-edit" onclick="attack' in control.get("class")
        (panel,) = tree.xpath(".//*[@id=$id]", id=control.get("aria-controls"))
        assert panel.get("aria-labelledby") == control.get("id")
        assert ("show" in panel.classes) is (index == 0)
        if pack == "tabs-vertical":
            assert control.get(f"data-{prefix}-toggle") == "pill"
            assert control.get("aria-selected") == ("true" if index == 0 else "false")
            assert control.get("tabindex") == ("0" if index == 0 else "-1")
            assert ("active" in control.classes) is (index == 0)
            assert ("active" in panel.classes) is (index == 0)
            assert panel.get("tabindex") == "0"
            assert panel.get("role") == "tabpanel"
            assert len(tree.cssselect('[data-cv-od-tabs][role="tablist"]')) == 1
        else:
            assert control.get(f"data-{prefix}-toggle") == "collapse"
            assert control.get("aria-expanded") == ("true" if index == 0 else "false")
            assert ("collapsed" in control.classes) is (index != 0)
            assert panel.get(f"data-{prefix}-parent") == "#cvod-c11-author-page-root"


@pytest.mark.parametrize("prefix", ["bs", "coreui"])
def test_data_prefix_documented_standalone_accordion(isolate_data_prefix, prefix):
    register_data_prefix(prefix)
    group = ResolvedGroup(HOSTILE, icon="host:edit", properties=[ResolvedProperty("name", HOSTILE, HOSTILE)])
    with override_settings(TEMPLATES=template_settings(copied_templates("accordion")), **ICON_SETTINGS):
        output = Template('{% load crud_views_object_detail %}{% render_group group layout="accordion" %}').render(
            Context({"group": group})
        )
    tree = html.fromstring(output)
    (control,) = tree.cssselect("button")
    (panel,) = tree.cssselect(".accordion-collapse")
    assert control.get(f"data-{prefix}-toggle") == "collapse"
    assert control.get(f"data-{prefix}-target") == "#" + panel.get("id")
    assert control.get("aria-controls") == panel.get("id")
    assert panel.get("aria-labelledby") == control.get("id")
    assert control.get("aria-expanded") == "true"
    assert "collapsed" not in control.classes
    assert "show" in panel.classes
    assert panel.get(f"data-{prefix}-parent") is None
    assert HOSTILE in tree.text_content()
    assert 'icon-edit" onclick="attack' in control.get("class")
    assert not tree.cssselect("img, [onerror], [onclick]")
    if prefix != "bs":
        assert "data-bs-" not in output
