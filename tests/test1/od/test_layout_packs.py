from copy import deepcopy

import pytest
from django.conf import settings
from django.template import Context, Template
from django.template.loader import get_template
from django.test import override_settings
from lxml import html as lxml_html

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
    ("card-rows", "data-cv-tooltip"),
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


@pytest.mark.parametrize("pack", ["split-card", "card-rows", "table-inline", "list-group-3col", "striped-rows"])
@pytest.mark.parametrize("count", [0, 2])
@pytest.mark.parametrize("component_id", [None, "page-details"])
def test_group_only_copy_reuses_enclosing_projection(pack, count, component_id):
    """Only group.html is copied; the actual shipped fallback supplies the projection."""
    templates = deepcopy(settings.TEMPLATES)
    templates[0]["APP_DIRS"] = False
    group_path = f"crud_views_object_detail/layouts/{pack}/group.html"
    templates[0]["OPTIONS"]["loaders"] = [
        (
            "django.template.loaders.locmem.Loader",
            {
                group_path: """{% load crud_views_object_detail %}
<section data-panel="{{ presentation.panel_id }}" data-control="{{ presentation.control_id }}"
         data-component="{{ component.id }}" data-selected="{{ presentation.selected|yesno:'true,false' }}">
    <header>{{ group.title }}</header>
    {% for prop in group.properties %}{% render_property prop layout=layout %}{% endfor %}
</section>""",
            },
        ),
        "django.template.loaders.app_directories.Loader",
    ]
    groups = [
        ResolvedGroup(
            title=f"Title {index} <script>bad</script>",
            properties=[ResolvedProperty(path="name", label="Label <text>", value=f"Value {index} <img>")],
        )
        for index in range(count)
    ]
    with override_settings(TEMPLATES=templates):
        fallback = get_template("crud_views_object_detail/object_detail.html")
        assert fallback.origin.name.endswith(
            "src/crud_views_object_detail/templates/crud_views_object_detail/object_detail.html"
        )
        tpl = Template(
            "{% load crud_views_object_detail %}"
            "{% render_object_detail obj groups layout=layout component_id=component_id %}"
        )
        context = {"groups": groups, "layout": pack, "component_id": component_id}
        docs = [lxml_html.fromstring("<main>" + tpl.render(Context(context)) + "</main>") for _ in range(2)]
    first, second = [doc.cssselect("section") for doc in docs]
    assert len(first) == len(second) == count
    for doc in docs:
        assert not doc.cssselect("script, img, [aria-labelledby], [data-bs-parent]")
        for index in range(count):
            assert f"Title {index} <script>bad</script>" in doc.text_content()
            assert f"Value {index} <img>" in doc.text_content()
            assert "Label <text>" in doc.text_content()
    for index, (entry, again) in enumerate(zip(first, second, strict=True)):
        component = entry.get("data-component")
        assert component.endswith("-root")
        assert entry.get("data-panel") == component.removesuffix("-root") + f"-i{index}-panel"
        assert entry.get("data-control") == component.removesuffix("-root") + f"-i{index}-control"
        assert entry.get("data-selected") == ("true" if index == 0 else "false")
        if component_id:
            assert component == "cvod-c12-page-details-root"
            assert dict(entry.attrib) == dict(again.attrib)
        else:
            assert component != again.get("data-component")
    if count:
        assert len({entry.get("data-component") for entry in first}) == 1
        assert len({entry.get("data-panel") for entry in first}) == count
