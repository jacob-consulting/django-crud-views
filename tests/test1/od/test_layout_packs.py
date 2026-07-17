import pytest
from django.template import Template, Context
from django.test import override_settings

from crud_views_object_detail.lib.resolvers import ResolvedGroup, ResolvedProperty


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


# Each marker is a substring that appears in exactly one layout pack's templates
# (verified with `grep -rl <marker> src/crud_views_object_detail/templates/crud_views_object_detail/`)
# and is rendered unconditionally by that pack's group.html (i.e. not gated behind an
# optional `prop.detail` / `prop.link_url` block), so it is present regardless of which
# properties happen to be rendered. This makes the assertions fail if the pack override
# silently falls back to the wrong (or a cached) template.
LAYOUT_PACKS = [
    ("split-card", "border-end"),
    ("card-rows", 'data-bs-toggle="tooltip"'),
    ("table-inline", "table table-borderless mb-0"),
    ("list-group-3col", "list-group-item"),
    ("accordion", "accordion-item"),
    ("tabs-vertical", "tab-pane"),
    ("striped-rows", "table-striped"),
]


@pytest.mark.parametrize("pack,marker", LAYOUT_PACKS)
class TestLayoutPackSmoke:
    def test_render_object_detail(self, groups, pack, marker):
        with override_settings(CRUD_VIEWS_OBJECT_DETAIL_TEMPLATE_PACK_LAYOUT=pack):
            tpl = Template("{% load crud_views_object_detail %}{% render_object_detail obj groups %}")
            html = tpl.render(Context({"obj": None, "groups": groups}))
            assert "General" in html
            assert "Test" in html
            assert marker in html

    def test_render_group(self, groups, pack, marker):
        with override_settings(CRUD_VIEWS_OBJECT_DETAIL_TEMPLATE_PACK_LAYOUT=pack):
            tpl = Template("{% load crud_views_object_detail %}{% render_group group %}")
            html = tpl.render(Context({"group": groups[0]}))
            assert "General" in html
            assert "Name" in html
            assert marker in html

    def test_render_property(self, groups, pack, marker):
        with override_settings(CRUD_VIEWS_OBJECT_DETAIL_TEMPLATE_PACK_LAYOUT=pack):
            tpl = Template("{% load crud_views_object_detail %}{% render_property prop %}")
            html = tpl.render(Context({"prop": groups[0].properties[0]}))
            assert "Name" in html
            assert "Test" in html

    def test_detail_rendered(self, groups, pack, marker):
        with override_settings(CRUD_VIEWS_OBJECT_DETAIL_TEMPLATE_PACK_LAYOUT=pack):
            tpl = Template("{% load crud_views_object_detail %}{% render_property prop %}")
            html = tpl.render(Context({"prop": groups[0].properties[1]}))
            assert "Currently active" in html

    def test_link_rendered(self, groups, pack, marker):
        with override_settings(CRUD_VIEWS_OBJECT_DETAIL_TEMPLATE_PACK_LAYOUT=pack):
            tpl = Template("{% load crud_views_object_detail %}{% render_property prop %}")
            html = tpl.render(Context({"prop": groups[0].properties[2]}))
            assert "/items/1/" in html
            assert "linked" in html
