"""Accessible markup of the object-detail layout packs."""

import pytest
from django.template import Context, Template
from django.test import override_settings
from lxml import html

from crud_views_object_detail.lib.resolvers import ResolvedGroup, ResolvedProperty


@pytest.mark.parametrize("pack", ["accordion", "table-inline", "striped-rows"])
def test_object_detail_row_labels_are_row_headers(pack):
    prop = ResolvedProperty(path="name", label="Name", value="Test", type="char")
    with override_settings(CRUD_VIEWS_OBJECT_DETAIL_TEMPLATE_PACK_LAYOUT=pack):
        rendered = Template("{% load crud_views_object_detail %}{% render_property prop %}").render(
            Context({"prop": prop})
        )
    (th,) = html.fromstring(f"<table>{rendered}</table>").cssselect("th")
    assert th.get("scope") == "row"
    assert th.text_content().strip() == "Name"


def test_card_rows_detail_tooltip_trigger_is_a_labelled_button():
    prop = ResolvedProperty(path="s", label="Status", value="Active", type="char", detail="Currently active")
    with override_settings(CRUD_VIEWS_OBJECT_DETAIL_TEMPLATE_PACK_LAYOUT="card-rows"):
        rendered = Template("{% load crud_views_object_detail %}{% render_property prop %}").render(
            Context({"prop": prop})
        )
    (trigger,) = html.fromstring(rendered).cssselect("[data-cv-tooltip]")
    assert trigger.tag == "button"
    assert trigger.get("type") == "button"
    assert trigger.get("aria-label") == "Currently active"
    assert trigger.get("role") is None
    assert trigger.get("tabindex") is None
    assert all(i.get("aria-hidden") == "true" for i in trigger.cssselect("i"))


def test_card_rows_detail_trigger_is_marked_for_tooltip_js():
    """#125: the trigger carries data-cv-tooltip (initialised by crud_views/js/tooltip.js),
    not data-bs-toggle, so app-level `[data-bs-toggle=tooltip]` initialisers don't collide.
    #202: the text is in `title` (driver-neutral), the marker value names the location."""
    prop = ResolvedProperty(path="s", label="Status", value="Active", type="char", detail="Currently active")
    with override_settings(CRUD_VIEWS_OBJECT_DETAIL_TEMPLATE_PACK_LAYOUT="card-rows"):
        rendered = Template("{% load crud_views_object_detail %}{% render_property prop %}").render(
            Context({"prop": prop})
        )
    (trigger,) = html.fromstring(rendered).cssselect("[data-cv-tooltip]")
    assert trigger.get("data-bs-toggle") is None
    assert trigger.get("data-cv-tooltip") == "object-detail"
    assert trigger.get("title") == "Currently active"
    assert trigger.get("aria-label") == "Currently active"
    assert trigger.get("data-bs-title") is None


def test_tooltip_js_is_a_core_script():
    from crud_views.lib.settings import crud_views_settings

    assert crud_views_settings.javascript()["tooltip"] == "crud_views/js/tooltip.js"


@pytest.mark.parametrize("pack", ["accordion", "tabs-vertical"])
@pytest.mark.parametrize("count", [0, 1, 2])
def test_interactive_layout_aria_references_resolve_to_unique_elements(pack, count):
    groups = [ResolvedGroup(title="Repeated") for _ in range(count)]
    markup = Template("{% load crud_views_object_detail %}{% render_object_detail obj groups layout=pack %}").render(
        Context({"groups": groups, "pack": pack})
    )
    doc = html.fromstring(markup)
    for element in doc.cssselect("[aria-controls], [aria-labelledby]"):
        for attribute in ("aria-controls", "aria-labelledby"):
            if target := element.get(attribute):
                assert len(doc.xpath("//*[@id=$target]", target=target)) == 1
    if not count:
        assert not doc.cssselect("[aria-controls], [aria-labelledby], button")
    elif pack == "tabs-vertical":
        (selected,) = doc.cssselect('[role="tab"][aria-selected="true"]')
        (visible,) = doc.cssselect('[role="tabpanel"].active.show')
        assert selected.get("aria-controls") == visible.get("id")
    else:
        (root,) = doc.cssselect(".accordion")
        controls = root.cssselect("button.accordion-button")
        panels = root.cssselect(".accordion-collapse")
        assert len(controls) == len(panels) == count
        for index, (control, panel) in enumerate(zip(controls, panels, strict=True)):
            assert control.get("type") == "button"
            assert control.get("aria-controls") == panel.get("id")
            assert panel.get("aria-labelledby") == control.get("id")
            assert panel.get("data-bs-parent") == "#" + root.get("id")
            assert control.get("aria-expanded") == ("true" if index == 0 else "false")
            assert ("collapsed" in control.classes) is (index != 0)
            assert ("show" in panel.classes) is (index == 0)
