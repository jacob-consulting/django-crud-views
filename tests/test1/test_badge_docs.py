"""Compile the published native badge recipe through actual property rendering."""

import re
from pathlib import Path
from unittest.mock import Mock

import pytest
from django.test import override_settings
from lxml import html

from crud_views_object_detail.lib.conf import CrudViewsObjectDetailSettings
from crud_views_object_detail.lib.config import BadgeConfig, x
from crud_views_object_detail.lib.resolvers import resolve_property
from crud_views_object_detail.templatetags import crud_views_object_detail as tags
from tests.test1.od.test_badge_semantics import render, template_settings
from tests.test1.od_app.models import Report

DOC = Path(__file__).resolve().parents[2] / "docs/reference/object_detail_badges.md"


def published_template():
    text = DOC.read_text()
    heading = "## Native semantic badge template"
    assert text.count(heading) == 1, "Missing or duplicated published native recipe"
    section = text.split(heading, 1)[1].split("\n## ", 1)[0]
    fences = re.findall(r"^```django\n(.*?)^```", section, re.MULTILINE | re.DOTALL)
    assert len(fences) == 1
    return fences[0]


@pytest.mark.parametrize("pill", [False, True])
@pytest.mark.parametrize("label", [None, "", '<img src=x onerror="label">'])
@pytest.mark.parametrize("color", ["brand-custom", 'unknown" onclick="alert(1)<img>'])
def test_badge_docs_native_recipe_maps_color_and_pill_once(monkeypatch, pill, label, color):
    template = published_template()
    monkeypatch.setattr(tags, "crud_views_object_detail_settings", CrudViewsObjectDetailSettings())
    value = '<script>alert("value")</script>'
    callback = Mock(return_value=color)
    prop = resolve_property(
        Report(title=value),
        x("title", template="explicit.html", badge=BadgeConfig(color_fn=callback, pill=pill, label_map={value: label})),
    )
    templates = {"crud_views_object_detail/types/native/badge.html": template, "explicit.html": "EXPLICIT"}
    with override_settings(
        TEMPLATES=template_settings(templates), CRUD_VIEWS_OBJECT_DETAIL_TEMPLATE_PACK_TYPES="native"
    ):
        node = html.fromstring(render(prop))
    assert node.tag == "span"
    expected_classes = ["status"] + (["status-brand"] if color == "brand-custom" else [])
    assert node.get("class").split() == expected_classes + (["status-pill"] if pill else [])
    assert set(node.attrib) == {"class"}
    assert len(node) == 0
    assert node.text_content().strip() == (label or value)
    callback.assert_called_once_with(value)


@pytest.mark.parametrize("missing", ["map", "callback", "value"])
@pytest.mark.parametrize("explicit", [False, True])
def test_badge_docs_unresolved_colors_keep_ordinary_path(monkeypatch, missing, explicit):
    template = published_template()
    monkeypatch.setattr(tags, "crud_views_object_detail_settings", CrudViewsObjectDetailSettings())
    callback = Mock(return_value=None)
    badge = (
        BadgeConfig(color="fixed", color_map={"other": "brand-custom"})
        if missing == "map"
        else BadgeConfig(color_fn=callback)
    )
    value = None if missing == "value" else "Active"
    prop = resolve_property(
        Report(title=value), x("title", badge=badge, template="explicit.html" if explicit else None)
    )
    templates = {
        "crud_views_object_detail/types/native/badge.html": template,
        "crud_views_object_detail/types/native/char.html": "ORDINARY {{ value }}",
        "explicit.html": "EXPLICIT {{ value }}",
    }
    with override_settings(
        TEMPLATES=template_settings(templates), CRUD_VIEWS_OBJECT_DETAIL_TEMPLATE_PACK_TYPES="native"
    ):
        rendered = render(prop)
    assert rendered == ("EXPLICIT " if explicit else "ORDINARY ") + str(value)
    assert (prop.badge_color, prop.badge_pill) == (None, False)
    if missing == "callback":
        callback.assert_called_once_with(value)
    else:
        callback.assert_not_called()
