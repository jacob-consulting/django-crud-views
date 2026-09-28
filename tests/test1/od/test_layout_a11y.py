"""Accessible markup of the object-detail layout packs."""

import pytest
from django.template import Context, Template
from django.test import override_settings
from lxml import html

from crud_views_object_detail.lib.resolvers import ResolvedProperty


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
    assert trigger.tag == "button" and trigger.get("type") == "button"
    assert trigger.get("aria-label") == "Currently active"
    assert trigger.get("role") is None and trigger.get("tabindex") is None
    assert all(i.get("aria-hidden") == "true" for i in trigger.cssselect("i"))


def test_card_rows_detail_trigger_is_marked_for_tooltip_js():
    """#125: the trigger carries data-cv-tooltip (initialised by crud_views/js/tooltip.js),
    not data-bs-toggle, so app-level `[data-bs-toggle=tooltip]` initialisers don't collide."""
    prop = ResolvedProperty(path="s", label="Status", value="Active", type="char", detail="Currently active")
    with override_settings(CRUD_VIEWS_OBJECT_DETAIL_TEMPLATE_PACK_LAYOUT="card-rows"):
        rendered = Template("{% load crud_views_object_detail %}{% render_property prop %}").render(
            Context({"prop": prop})
        )
    (trigger,) = html.fromstring(rendered).cssselect("[data-cv-tooltip]")
    assert trigger.get("data-bs-toggle") is None
    assert trigger.get("data-bs-title") == "Currently active"


def test_tooltip_js_is_a_core_script():
    from crud_views.lib.settings import crud_views_settings

    assert crud_views_settings.javascript()["tooltip"] == "crud_views/js/tooltip.js"
