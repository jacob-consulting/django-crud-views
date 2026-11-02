"""Real object-detail renders share identities and initial selection across contexts."""

from copy import deepcopy

import pytest
from django.template import Context, Template
from django.utils.translation import gettext_lazy
from lxml import html

from crud_views_object_detail.lib.resolvers import ResolvedGroup, ResolvedProperty


def render(groups, layout="tabs-vertical", repeat=False, standalone=False, **context):
    tag = "{% render_group group layout=layout %}" if standalone else "{% render_object_detail obj groups layout=layout %}"
    template = Template("{% load crud_views_object_detail %}" + tag * (2 if repeat else 1))
    markup = template.render(Context({"groups": groups, "group": groups[0] if groups else None, "layout": layout, **context}))
    return html.fromstring(f"<main>{markup}</main>")


@pytest.mark.parametrize("count", [0, 1, 2])
@pytest.mark.parametrize("focusable", [False, True])
def test_tabs_initial_selection(count, focusable):
    prop = ResolvedProperty(path="name", label="Name", value="Value", link_url="/next/" if focusable else None)
    doc = render([ResolvedGroup(title="Same", properties=[prop]) for _ in range(count)])
    tabs = doc.cssselect('[role="tab"]')
    panels = doc.cssselect('[role="tabpanel"]')
    assert len(tabs) == len(panels) == count
    assert len(doc.cssselect('.tab-pane.active.show')) == min(1, count)
    assert len(doc.cssselect('[role="tab"].active[aria-selected="true"]')) == min(1, count)
    assert len(doc.cssselect('[data-cv-od-tabs][aria-orientation="vertical"]')) == 1
    for index, (tab, panel) in enumerate(zip(tabs, panels)):
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
