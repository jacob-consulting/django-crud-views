"""Badge semantics reach native and stock templates from one resolution."""

from copy import deepcopy
from unittest.mock import Mock

import pytest
from django.conf import settings
from django.template import Context, Template
from django.test import override_settings
from lxml import html

from crud_views_object_detail.lib.config import BadgeConfig, x
from crud_views_object_detail.lib.resolvers import ResolvedProperty, resolve_property
from tests.test1.od_app.models import Report


def render(prop):
    return Template("{% load crud_views_object_detail %}{% render_property_value prop %}").render(Context({"prop": prop}))


def template_settings(templates):
    engines = deepcopy(settings.TEMPLATES)
    engines[0]["APP_DIRS"] = False
    engines[0]["OPTIONS"]["loaders"] = [
        ("django.template.loaders.locmem.Loader", templates),
        "django.template.loaders.app_directories.Loader",
    ]
    return engines


@pytest.mark.parametrize("pill", [False, True])
def test_badge_semantics_callback_once_in_stock_and_native_templates(pill):
    callback = Mock(return_value="brand-custom")
    prop = resolve_property(
        Report(title="Active"),
        x("title", template="explicit.html", badge=BadgeConfig(color_fn=callback, pill=pill)),
    )
    assert getattr(prop, "badge_color", None) == "brand-custom"
    assert prop.badge_pill is pill
    assert prop.badge_css == "text-bg-brand-custom" + (" rounded-pill" if pill else "")
    assert render(prop).strip() == f'<span class="badge {prop.badge_css}">Active</span>'
    templates = {
        "explicit.html": "EXPLICIT",
        "crud_views_object_detail/types/default/badge.html": (
            '<b data-color="{{ prop.badge_color }}" data-pill="{{ prop.badge_pill|yesno:\"yes,no\" }}">'
            "{{ value }}</b>"
        ),
    }
    with override_settings(TEMPLATES=template_settings(templates)):
        node = html.fromstring(render(prop))
    assert node.tag == "b"
    assert node.get("data-color") == "brand-custom"
    assert node.get("data-pill") == ("yes" if pill else "no")
    assert node.text == "Active"
    callback.assert_called_once_with("Active")


@pytest.mark.parametrize(
    "badge,color",
    [
        (None, None),
        (BadgeConfig(color="fixed"), "fixed"),
        (BadgeConfig(color="fixed", color_map={"Active": "mapped"}), "mapped"),
        (BadgeConfig(color="fixed", color_map={}), "fixed"),
        (BadgeConfig(color="fixed", color_map={"other": "mapped"}, pill=True), None),
        (BadgeConfig(color="fixed", color_fn=lambda value: None, pill=True), None),
        (BadgeConfig(color="fixed", color_map={"Active": "mapped"}, color_fn=lambda value: "function"), "function"),
        (BadgeConfig(color="", pill=True), ""),
    ],
)
def test_badge_semantics_resolution_and_ordinary_fallback(badge, color):
    prop = resolve_property(Report(title="Active"), x("title", badge=badge))
    assert hasattr(prop, "badge_color")
    assert prop.badge_color == color
    assert prop.badge_pill is (badge.pill if color is not None else False)
    if color is None:
        assert prop.badge_css is None
        assert "badge" not in render(prop)
        assert "Active" in render(prop)
        prop.template = "explicit.html"
        with override_settings(TEMPLATES=template_settings({"explicit.html": "EXPLICIT {{ value }}"})):
            assert render(prop) == "EXPLICIT Active"
    else:
        assert prop.badge_css == f"text-bg-{color}" + (" rounded-pill" if badge.pill else "")


def test_badge_semantics_none_value_skips_callback_and_keeps_defaults():
    callback = Mock(return_value="unused")
    prop = resolve_property(Report(title=None), x("title", badge=BadgeConfig(color_fn=callback, pill=True)))
    assert hasattr(prop, "badge_color")
    assert (prop.badge_color, prop.badge_pill, prop.badge_css, prop.badge_label) == (None, False, None, None)
    assert "badge" not in render(prop)
    callback.assert_not_called()


def test_badge_semantics_preserves_positional_constructor():
    prop = ResolvedProperty("path", "Label", "value", "detail", "char", "custom.html", False, "/", "css", "label")
    assert prop.badge_label == "label"
    assert hasattr(prop, "badge_color")
    assert prop.badge_color is None
    assert prop.badge_pill is False


@pytest.mark.parametrize("label", [None, "", '<img src=x onerror="label">'])
def test_badge_semantics_stock_escapes_color_label_and_value(label):
    value = '<script>alert("value")</script>'
    color = 'custom" onclick="alert(1)<img>'
    callback = Mock(return_value=color)
    prop = resolve_property(
        Report(title=value),
        x("title", badge=BadgeConfig(color_fn=callback, label_map={value: label}, pill=True)),
    )
    assert getattr(prop, "badge_color", None) == color
    node = html.fromstring(render(prop))
    assert node.tag == "span"
    assert len(node) == 0
    assert set(node.attrib) == {"class"}
    assert node.get("class") == f"badge text-bg-{color} rounded-pill"
    assert node.text == (label or value)
    callback.assert_called_once_with(value)
