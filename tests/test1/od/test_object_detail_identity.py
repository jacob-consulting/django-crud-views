"""Real object-detail renders share identities and initial selection across contexts."""

from copy import deepcopy

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.template import Context, Template
from django.test import override_settings
from django.utils.translation import gettext_lazy
from lxml import html

from crud_views_object_detail.lib.resolvers import ResolvedGroup, ResolvedProperty


def render(groups, layout="tabs-vertical", repeat=False, standalone=False, **context):
    tag = (
        "{% render_group group layout=layout %}"
        if standalone
        else "{% render_object_detail obj groups layout=layout %}"
    )
    template = Template("{% load crud_views_object_detail %}" + tag * (2 if repeat else 1))
    markup = template.render(
        Context({"groups": groups, "group": groups[0] if groups else None, "layout": layout, **context})
    )
    return html.fromstring(f"<main>{markup}</main>")


@pytest.mark.parametrize("count", [0, 1, 2])
@pytest.mark.parametrize("focusable", [False, True])
def test_tabs_initial_selection(count, focusable):
    prop = ResolvedProperty(path="name", label="Name", value="Value", link_url="/next/" if focusable else None)
    doc = render([ResolvedGroup(title="Same", properties=[prop]) for _ in range(count)])
    tabs = doc.cssselect('[role="tab"]')
    panels = doc.cssselect('[role="tabpanel"]')
    assert len(tabs) == len(panels) == count
    assert len(doc.cssselect(".tab-pane.active.show")) == min(1, count)
    assert len(doc.cssselect('[role="tab"].active[aria-selected="true"]')) == min(1, count)
    assert len(doc.cssselect('[data-cv-od-tabs][aria-orientation="vertical"]')) == 1
    for index, (tab, panel) in enumerate(zip(tabs, panels, strict=True)):
        assert tab.get("aria-controls") == panel.get("id")
        assert tab.get("data-bs-target") == "#" + panel.get("id")
        assert panel.get("aria-labelledby") == tab.get("id")
        assert tab.get("tabindex") == ("0" if index == 0 else "-1")
        assert tab.get("aria-selected") == ("true" if index == 0 else "false")
        assert panel.get("tabindex") == "0"


def test_generated_targets_ignore_titles_and_do_not_mutate_groups():
    groups = [ResolvedGroup(title=title) for title in ["A B", "A-B", "", "", gettext_lazy("日本語"), '<img src="x">']]
    before = deepcopy(groups)
    doc = render(groups, repeat=True)
    ids = doc.xpath("//@id")
    assert len(ids) == len(set(ids))
    assert all(value.startswith("cvod-c33-g") for value in ids)
    assert groups == before
    assert not doc.cssselect("img")
    assert set(ids).isdisjoint(render(groups).xpath("//@id"))


def test_standalone_tab_has_label_without_missing_control():
    doc = render([ResolvedGroup(title='<Title " &>')], standalone=True)
    (panel,) = doc.cssselect('[role="tabpanel"]')
    assert panel.get("aria-labelledby") is None
    assert panel.get("aria-label") == '<Title " &>'
    assert "active" in panel.classes and "show" in panel.classes


@pytest.mark.parametrize("icon", ["host:edit", "fas:pen", "", None, "disabled"])
@pytest.mark.parametrize("hostile", [False, True])
def test_tabs_title_button_owns_icon(icon, hostile):
    group = ResolvedGroup(title='<em>Title & "text"</em>', icon=icon)
    with override_settings(
        CRUD_VIEWS_ICON_LIBRARIES={"host": {"renderer": "font", "placement": "host", "class": "icon-{name}"}},
        CRUD_VIEWS_ICONS={"disabled": None},
        CRUD_VIEWS_BUTTON_CLASSES={
            "heading-group:icon-host": '{name_class}" onclick="attack' if hostile else "group {name_class}",
            "heading-group:icon-inline": 'inline" onerror="attack' if hostile else "group-inline",
        },
    ):
        doc = render([group])
    (button,) = doc.cssselect('[role="tab"]')
    assert button.text_content().strip() == group.title
    assert not doc.cssselect("em, [onclick], [onerror]")
    assert {"nav-link", "text-start", "active"} <= button.classes
    assert len(button.cssselect("i")) == (1 if icon == "fas:pen" else 0)
    assert ("icon-edit" in button.get("class")) == (icon == "host:edit")
    if icon == "fas:pen":
        assert button.cssselect("i")[0].get("aria-hidden") == "true"


@pytest.mark.parametrize("token", ["", "1bad", "bad token", "with.dot", "é", 'x" onclick="bad', 123, False])
def test_invalid_component_token_rejected(token):
    from crud_views_object_detail.templatetags.crud_views_object_detail import render_object_detail

    with pytest.raises(ImproperlyConfigured, match="component_id"):
        render_object_detail(Context(), None, [], layout="tabs-vertical", component_id=token)
