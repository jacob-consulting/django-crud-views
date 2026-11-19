"""Execute the published navbar recipes and its documented context inventory."""

import re
from pathlib import Path
from unittest.mock import Mock

import pytest
from django.template import Context, Template
from django.template.loader import get_template
from lxml import html

from crud_views.lib import navbar
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


@pytest.mark.parametrize(
    "mode", ["tag", "wrapper", "identity", "split", "per-bar", "identity-tag", "items-tag", "split-includes"]
)
def test_published_override_recipes_render_real_context(mode, monkeypatch):
    build = Mock(wraps=navbar._build)
    monkeypatch.setattr(navbar, "_build", build)
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
            source = (
                snippets[mode] if mode in {"split", "split-includes", "identity-tag", "items-tag"} else snippets["tag"]
            )
            output = Template(source).render(Context(context))
            tree = html.fragment_fromstring(output, create_parent="div")
            if mode == "items-tag":
                assert tree.xpath(".//nav")[0].get("aria-label") == "Sections for A <b>plain</b> owner"
            else:
                assert "A <b>plain</b> owner" in tree.text_content()
            assert not tree.xpath(".//b")
            links = tree.xpath(".//nav//a")
            assert len(links) == (0 if mode == "identity-tag" else 1)
            if links:
                assert links[0].text_content().strip() == "Details"
                assert links[0].get("href") == context["cv_navbar"]["items"][0]["url"]
                assert links[0].get("aria-current") == "true"
            assert build.call_count == 1
            assert bool(tree.xpath('.//*[contains(@class,"cv-navbar-identity")]')) == (
                mode not in {"items-tag", "identity"}
            )
            if mode in {"identity-tag", "items-tag", "split", "split-includes"}:
                assert not tree.xpath('.//*[@class="cv-navbar mb-3"]')
            assert Template(source).render(Context({"cv_navbar": None})).strip() == (
                "<main></main>" if mode in {"split", "split-includes"} else ""
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


@pytest.mark.parametrize("mode", ["wrapper", "split", "per-bar"])
def test_published_wrappers_use_component_tags(mode):
    from django.template.library import SimpleNode

    from crud_views.templatetags.crud_views import cv_navbar_identity, cv_navbar_items

    template = Template(recipes()[mode])
    assert [node.func for node in template.nodelist.get_nodes_by_type(SimpleNode)] == [
        cv_navbar_identity,
        cv_navbar_items,
    ]


def test_component_recipe_order_and_direct_include_compatibility(monkeypatch):
    snippets = recipes()
    build = Mock(wraps=navbar._build)
    monkeypatch.setattr(navbar, "_build", build)
    with navbar_routes(lambda sfx: owner_routes(sfx, label="Details")) as ns:
        _, data = view_context(ns)
        direct = Template(snippets["split-includes"]).render(Context(data))
        components = Template(snippets["split"]).render(Context(data))
        assert direct.strip() == components.strip()
        reversed_output = Template(snippets["items-tag"] + snippets["identity-tag"]).render(Context(data))
        tree = html.fragment_fromstring(reversed_output, create_parent="div")
        assert [node.tag for node in tree] == ["nav", "div"]
        assert build.call_count == 1


@pytest.mark.parametrize("mode", ["identity-tag", "items-tag", "split", "split-includes", "per-bar"])
@pytest.mark.parametrize("empty", ["missing", "hidden", "modal"])
def test_component_recipes_preserve_empty_and_modal_contracts(mode, empty, monkeypatch):
    with navbar_routes(owner_routes) as ns:
        if empty == "hidden":
            monkeypatch.setattr(ns.view, "cv_has_access", lambda *args: False)
        _, data = view_context(ns, modal=empty == "modal")
        if empty == "missing":
            data = {}
        output = Template(recipes()[mode]).render(Context(data))
        assert output.strip() == ("<main></main>" if mode in {"split", "split-includes"} else "")
