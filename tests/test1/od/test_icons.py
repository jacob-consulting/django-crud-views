import pytest
from django.template import Context, Template
from django.test import override_settings

from crud_views.lib.icons import BOOTSTRAP_ICONS
from crud_views_object_detail.lib.resolvers import ResolvedGroup, ResolvedProperty

ICON_GROUP_LAYOUTS = ["accordion", "split-card", "striped-rows"]


def render_group(icon, layout):
    group = ResolvedGroup(title="Test", properties=[], icon=icon)
    tpl = Template("{% load crud_views_object_detail %}{% render_group group %}")
    with override_settings(CRUD_VIEWS_OBJECT_DETAIL_TEMPLATE_PACK_LAYOUT=layout):
        return tpl.render(Context({"group": group}))


def render_prop(**kwargs):
    prop = ResolvedProperty(path="t", label="T", **kwargs)
    tpl = Template("{% load crud_views_object_detail %}{% render_property_value prop %}")
    return tpl.render(Context({"prop": prop}))


@pytest.mark.parametrize("layout", ICON_GROUP_LAYOUTS)
def test_group_icon_prefixed(layout):
    html = render_group("fas:truck", layout)
    assert "fa-solid fa-truck" in html
    assert 'aria-hidden="true"' in html


@pytest.mark.parametrize("layout", ICON_GROUP_LAYOUTS)
def test_group_icon_raw_class(layout):
    html = render_group("truck", layout)
    assert '<i class="truck' in html
    assert "fa-truck" not in html


def test_group_icon_tabs_vertical():
    tpl = Template("{% load crud_views_object_detail %}{% cv_icon icon css='me-2' %}")
    assert "fa-solid fa-truck" in tpl.render(Context({"icon": "fas:truck"}))


def test_tabs_vertical_template_uses_cv_icon():
    from django.template.loader import get_template

    tpl = get_template("crud_views_object_detail/layouts/tabs-vertical/object_detail.html")
    assert "cv_icon" in tpl.template.source


def test_no_icon():
    assert "<i " not in render_group(None, "split-card")


def test_boolean_true():
    html = render_prop(value=True, type="boolean")
    assert "fa-solid fa-circle-check text-success" in html


def test_boolean_false():
    html = render_prop(value=False, type="boolean")
    assert "fa-solid fa-circle-xmark text-danger" in html


@override_settings(CRUD_VIEWS_ICONS=BOOTSTRAP_ICONS)
def test_boolean_bootstrap_preset():
    html = render_prop(value=True, type="boolean")
    assert "bi bi-check-circle-fill" in html
    assert "text-success" in html


def test_property_detail_icon():
    prop = ResolvedProperty(path="t", label="T", value="x", detail="More info")
    tpl = Template("{% load crud_views_object_detail %}{% render_property prop %}")
    with override_settings(CRUD_VIEWS_OBJECT_DETAIL_TEMPLATE_PACK_LAYOUT="card-rows"):
        html = tpl.render(Context({"prop": prop}))
    assert "fa-solid fa-circle-info" in html
    assert 'aria-label="More info"' in html


def test_text_icon_list_group_3col():
    prop = ResolvedProperty(path="t", label="T", value="x", detail="More info")
    tpl = Template("{% load crud_views_object_detail %}{% render_property prop %}")
    with override_settings(CRUD_VIEWS_OBJECT_DETAIL_TEMPLATE_PACK_LAYOUT="list-group-3col"):
        html = tpl.render(Context({"prop": prop}))
    assert "fa-regular fa-file-lines" in html


def test_legacy_filters_removed():
    from crud_views_object_detail.templatetags import crud_views_object_detail as tags

    assert not hasattr(tags, "icon_class")
    assert not hasattr(tags, "named_icon_class")
