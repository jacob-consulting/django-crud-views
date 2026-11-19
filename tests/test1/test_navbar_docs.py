"""Execute the published navbar recipes and its documented context inventory."""

import re
from pathlib import Path

import pytest
from django.template import Context, Template
from django.template.loader import get_template
from lxml import html

from crud_views.lib.navbar import CrudViewNavBarMixin, NavBar, NavItem
from tests.test1.test_navbar import navbar_routes, navbar_templates, owner_routes
from tests.test1.test_navbar_templates import view_context

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs/reference/navbar.md"


def recipes():
    return dict(re.findall(r"<!-- navbar-recipe: ([\w-]+) -->\n```django\n(.*?)\n```", REFERENCE.read_text(), re.S))


def test_documented_declarations_construct_with_translated_labels():
    blocks = re.findall(r"```python\n(.*?)\n```", REFERENCE.read_text(), re.S)
    namespace = {}
    exec(blocks[0], namespace)
    exec(blocks[2], namespace)
    bar = namespace["customer_navbar"]
    assert isinstance(bar, NavBar)
    assert all(isinstance(item, NavItem) for item in bar.items)
    assert issubclass(namespace["CustomerNavbarMixin"], CrudViewNavBarMixin)
    assert namespace["CustomerNavbarMixin"].cv_navbar is bar
    assert str(bar.items[0].label) == "Details"
    assert bar.items[1].icon == ""
    assert [(item.child, item.key) for item in namespace["alternative_navbar"].items][-2:] == [
        ("order", "create"),
        ("address", "directory"),
    ]


@pytest.mark.parametrize("mode", ["tag", "wrapper", "identity", "split", "per-bar"])
def test_published_override_recipes_render_real_context(mode):
    snippets = recipes()
    with navbar_routes(lambda sfx: owner_routes(sfx, label="Details")) as ns:
        overrides = {}
        if mode in {"wrapper", "identity"}:
            name = "navbar" if mode == "wrapper" else "navbar_identity"
            overrides[f"crud_views/tags/{name}.html"] = snippets[mode]
        elif mode == "per-bar":
            ns.bar.template = "myapp/customer_navbar.html"
            overrides[ns.bar.template] = snippets[mode]
        with navbar_templates(overrides):
            _, context = view_context(ns, name="A <b>plain</b> owner")
            source = snippets["split"] if mode == "split" else snippets["tag"]
            output = Template(source).render(Context(context))
            tree = html.fragment_fromstring(output, create_parent="div")
            assert "A <b>plain</b> owner" in tree.text_content()
            assert not tree.xpath(".//b")
            links = tree.xpath(".//nav//a")
            assert len(links) == 1
            assert links[0].text_content().strip() == "Details"
            assert links[0].get("href") == context["cv_navbar"]["items"][0]["url"]
            assert links[0].get("aria-current") == "true"
            assert Template(source).render(Context({"cv_navbar": None})).strip() == (
                "<main></main>" if mode == "split" else ""
            )


def test_split_recipe_preserves_inherited_crud_content():
    with navbar_templates({"project/split.html": recipes()["split"]}):
        child = Template('{% extends "project/split.html" %}{% block cv_content %}Page body{% endblock %}')
        assert child.render(Context({"cv_navbar": None})).strip() == "<main>Page body</main>"


def test_documented_context_inventory_resolves_real_render_data():
    text = (ROOT / "docs/reference/templates.md").read_text()
    assert "## ViewSet Navigation context" in text, "The navbar needs a separate documented context contract"
    section = text.split("## ViewSet Navigation context", 1)[1].split("\n## ", 1)[0]
    expressions = re.findall(r"^\| `((?:cv_navbar|item)\.[a-z_]+)` \|", section, re.M)
    with navbar_routes(lambda sfx: owner_routes(sfx, label="Details")) as ns:
        _, context = view_context(ns)
        data = context["cv_navbar"]
        assert {e.split(".")[1] for e in expressions if e.startswith("cv_navbar.")} == set(data)
        assert {e.split(".")[1] for e in expressions if e.startswith("item.")} == set(data["items"][0])
        context["item"] = data["items"][0]
        for expression in expressions:
            value = Template("{{ " + expression + " }}").render(Context(context))
            assert value != "", expression
    paths = re.findall(r"`(crud_views/tags/navbar(?:_identity|_items)?\.html)`", section)
    assert set(paths) == {
        "crud_views/tags/navbar.html",
        "crud_views/tags/navbar_identity.html",
        "crud_views/tags/navbar_items.html",
    }
    for path in paths:
        assert get_template(path).render({"cv_navbar": None}) == ""
