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
    (trigger,) = html.fromstring(rendered).cssselect('[data-bs-toggle="tooltip"]')
    assert trigger.tag == "button" and trigger.get("type") == "button"
    assert trigger.get("aria-label") == "Currently active"
    assert trigger.get("role") is None and trigger.get("tabindex") is None
    assert all(i.get("aria-hidden") == "true" for i in trigger.cssselect("i"))
