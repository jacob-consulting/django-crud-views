import pytest
from django.template import Template, Context
from django.test import override_settings

from crud_views_object_detail.lib import conf
from crud_views_object_detail.lib.conf import CrudViewsObjectDetailSettings
from crud_views_object_detail.lib.resolvers import ResolvedGroup, ResolvedProperty
from crud_views_object_detail.templatetags import crud_views_object_detail as tags


@pytest.fixture(autouse=True)
def _fresh_singleton(monkeypatch):
    """Both conf.py and the templatetags module hold their own bound reference to the
    settings singleton (the latter via `from ... import crud_views_object_detail_settings`),
    and cached_property values persist across tests. Reset both before each test so
    @override_settings actually takes effect through the templatetags module."""
    monkeypatch.setattr(conf, "crud_views_object_detail_settings", CrudViewsObjectDetailSettings())
    monkeypatch.setattr(tags, "crud_views_object_detail_settings", CrudViewsObjectDetailSettings())


@pytest.fixture
def groups():
    return [
        ResolvedGroup(
            title="General",
            description="General info",
            icon="info-circle",
            properties=[
                ResolvedProperty(path="name", label="Name", value="Test", type="char"),
                ResolvedProperty(
                    path="status",
                    label="Status",
                    value="Active",
                    type="char",
                    detail="Currently active",
                ),
                ResolvedProperty(
                    path="link",
                    label="Link",
                    value="linked",
                    type="char",
                    link_url="/items/1/",
                ),
            ],
        ),
        ResolvedGroup(
            title="Stats",
            properties=[
                ResolvedProperty(path="count", label="Count", value=42, type="integer"),
            ],
        ),
    ]


LAYOUT_PACKS = [
    "split-card",
    "card-rows",
    "table-inline",
    "list-group-3col",
    "accordion",
    "tabs-vertical",
    "striped-rows",
]


@pytest.mark.parametrize("pack", LAYOUT_PACKS)
class TestLayoutPackSmoke:
    def test_render_object_detail(self, groups, pack):
        with override_settings(CRUD_VIEWS_OBJECT_DETAIL_TEMPLATE_PACK_LAYOUT=pack):
            tpl = Template("{% load crud_views_object_detail %}{% render_object_detail obj groups %}")
            html = tpl.render(Context({"obj": None, "groups": groups}))
            assert "General" in html
            assert "Test" in html

    def test_render_group(self, groups, pack):
        with override_settings(CRUD_VIEWS_OBJECT_DETAIL_TEMPLATE_PACK_LAYOUT=pack):
            tpl = Template("{% load crud_views_object_detail %}{% render_group group %}")
            html = tpl.render(Context({"group": groups[0]}))
            assert "General" in html
            assert "Name" in html

    def test_render_property(self, groups, pack):
        with override_settings(CRUD_VIEWS_OBJECT_DETAIL_TEMPLATE_PACK_LAYOUT=pack):
            tpl = Template("{% load crud_views_object_detail %}{% render_property prop %}")
            html = tpl.render(Context({"prop": groups[0].properties[0]}))
            assert "Name" in html
            assert "Test" in html

    def test_detail_rendered(self, groups, pack):
        with override_settings(CRUD_VIEWS_OBJECT_DETAIL_TEMPLATE_PACK_LAYOUT=pack):
            tpl = Template("{% load crud_views_object_detail %}{% render_property prop %}")
            html = tpl.render(Context({"prop": groups[0].properties[1]}))
            assert "Currently active" in html

    def test_link_rendered(self, groups, pack):
        with override_settings(CRUD_VIEWS_OBJECT_DETAIL_TEMPLATE_PACK_LAYOUT=pack):
            tpl = Template("{% load crud_views_object_detail %}{% render_property prop %}")
            html = tpl.render(Context({"prop": groups[0].properties[2]}))
            assert "/items/1/" in html
            assert "linked" in html
