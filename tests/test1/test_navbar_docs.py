"""Execute the published navbar recipes and its documented context inventory."""

import re
from pathlib import Path
from unittest.mock import Mock

import pytest
from django.template import Context, Template
from django.template.loader import get_template
from django.test import Client, override_settings
from django.urls import resolve, reverse
from lxml import html

from crud_views.lib import navbar
from crud_views.lib.breadcrumb import Breadcrumb, BreadcrumbItem
from crud_views.lib.navbar import CrudViewNavBarMixin, NavBar, NavItem
from crud_views.lib.view import ChildContextButton
from tests.test1.app.models import Publisher
from tests.test1.test_navbar import navbar_routes, navbar_templates, owner_routes
from tests.test1.test_navbar_permissions import grant, permission_routes
from tests.test1.test_navbar_templates import view_context

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs/reference/navbar.md"


def recipes():
    return dict(re.findall(r"<!-- navbar-recipe: ([\w-]+) -->\n```django\n(.*?)\n```", REFERENCE.read_text(), re.S))


def owner_heading_recipe():
    snippets = recipes()
    assert "owner-heading" in snippets, "Publish the owner-heading recipe"
    return snippets["owner-heading"]


@pytest.mark.parametrize("header_level", [None, 3])
@pytest.mark.parametrize("state", ["present", "missing", "unconfigured", "hidden", "modal"])
def test_owner_heading_recipe_preserves_header_actions_and_fallback(header_level, state):
    source = owner_heading_recipe()

    def routes(sfx):
        ns, viewsets = owner_routes(sfx, configured=state != "unconfigured")
        if state == "hidden":
            type(
                "HiddenSection",
                (ns.view,),
                {
                    "cv_viewset": ns.owner,
                    "cv_key": "hidden",
                    "cv_path": "hidden",
                    "cv_has_access": classmethod(lambda cls, *args: False),
                },
            )
            ns.bar.items = [NavItem(key="hidden")]
        return ns, viewsets

    with navbar_routes(routes) as ns:
        ns.view.cv_context_actions = ["detail"]
        ns.view.cv_paragraph_template = None
        ns.view.cv_paragraph_template_code = "View subtitle"
        ns.owner.icon_header = "host:building"
        view, data = view_context(ns, name='Owner <img src=x onerror="bad">', modal=state == "modal")
        view.request.resolver_match = resolve(reverse(ns.owner.get_router_name("detail"), kwargs={"pk": 1}))
        data["request"] = view.request
        if state == "missing":
            data.pop("cv_navbar")
        libraries = {"host": {"renderer": "font", "class": "host-{name}"}}
        with (
            override_settings(CRUD_VIEWS_HEADER_LEVEL=header_level, CRUD_VIEWS_ICON_LIBRARIES=libraries),
            navbar_templates({"owner.html": source}),
        ):
            output = Template('{% extends "owner.html" %}{% block cv_content %}Page body{% endblock %}').render(
                Context(data)
            )
        tree = html.fragment_fromstring(output, create_parent="div")
        headings = tree.xpath(".//h1 | .//h2")
        assert [node.tag for node in headings] == (["h1", "h2"] if state == "present" else ["h1"])
        assert headings[-1].text_content().strip() == "Unchanged page header"
        assert "View subtitle" in tree.text_content()
        assert "Page body" in tree.text_content()
        assert not tree.xpath(".//img | .//*[@onerror]")
        actions = tree.xpath('.//a[@cv-key="detail"]')
        assert len(actions) == 1
        assert actions[0].get("href") == reverse(ns.owner.get_router_name("detail"), kwargs={"pk": 1})
        assert actions[0].text_content().strip()
        navs = tree.xpath('.//nav[starts-with(@aria-label,"Sections for ")]')
        assert len(navs) == (state == "present")
        if state == "present":
            assert headings[0].text_content().strip() == 'Owner <img src=x onerror="bad">'
            icon = headings[0].xpath(".//i")[0]
            assert "host-building" in icon.classes
            assert icon.get("aria-hidden") == "true"
            link = navs[0].xpath(".//a")[0]
            assert link.get("aria-current") == "true"
            assert link.get("href") == actions[0].get("href")


@pytest.mark.parametrize("present", [False, True])
def test_owner_heading_recipe_retains_equal_titles_and_inherited_blocks(present):
    source = owner_heading_recipe()
    blocks = ["cv_breadcrumb", "cv_header", "cv_context", "cv_paragraph", "cv_filter", "cv_content"]
    assert re.findall(r"{% block (\w+) %}", source) == blocks
    with navbar_routes(lambda sfx: owner_routes(sfx, configured=present)) as ns:
        view, data = view_context(ns, name="Unchanged page header")
        view.request.resolver_match = resolve(reverse(ns.owner.get_router_name("detail"), kwargs={"pk": 1}))
        data["request"] = view.request
        with navbar_templates({"owner.html": source}):
            plain = html.fragment_fromstring(Template(source).render(Context(data)), create_parent="div")
            assert [h.text_content().strip() for h in plain.xpath(".//h1 | .//h2")] == ["Unchanged page header"] * (
                2 if present else 1
            )
            child = '{% extends "owner.html" %}' + "".join(
                "{% block " + block + " %}override-" + block + "{% endblock %}" for block in blocks
            )
            output = Template(child).render(Context(data))
        for block in blocks:
            assert output.count("override-" + block) == 1


@pytest.mark.django_db
def test_owner_heading_recipe_orders_real_actions_after_navigation(django_user_model):
    source = owner_heading_recipe()
    with navbar_routes(permission_routes) as ns:
        owner = Publisher.objects.create(name="Owner heading")
        actor = django_user_model.objects.create_user(username="owner-heading")
        grant(ns, actor, owner)
        ns.host.cv_context_buttons = [ChildContextButton(key="children", child_name=ns.child.name, label_mode="label")]
        ns.host.cv_context_actions = ["children", "detail"]
        ns.host.cv_extends_template = "owner.html"
        ns.host.extra_context = {"cv_breadcrumb": Breadcrumb(items=[BreadcrumbItem(title="Owner heading")])}
        client = Client()
        client.force_login(actor)
        with navbar_templates({"owner.html": source}):
            response = client.get(reverse(ns.owner.get_router_name("host"), kwargs={"pk": owner.pk}))
        assert response.status_code == 200
        tree = html.fromstring(response.content)
        actions = tree.xpath("//a[@cv-key]")
        assert [a.get("cv-key") for a in actions] == ["list", "detail"]
        assert [a.get("href") for a in actions] == [
            reverse(ns.child.get_router_name("list"), kwargs={ns.child.parent.get_pk_name(): owner.pk}),
            reverse(ns.owner.get_router_name("detail"), kwargs={"pk": owner.pk}),
        ]
        assert all(a.text_content().strip() for a in actions)
        breadcrumbs = tree.xpath('//nav[@aria-label="breadcrumb"]')
        assert len(breadcrumbs) == 1
        nav = tree.xpath('//nav[starts-with(@aria-label,"Sections for ")]')[0]
        title = tree.xpath("//h2")[0]
        ordered = list(tree.iter())
        assert ordered.index(breadcrumbs[0]) < ordered.index(tree.xpath("//h1")[0]) < ordered.index(nav)
        assert ordered.index(nav) < ordered.index(title) < ordered.index(actions[0]) < ordered.index(actions[1])


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


def test_navbar_docs_explain_same_page_guardian_create_alignment():
    from tests.test1.test_label_mode_docs import _flat, _section
    from tests.test1.test_navbar_permissions import test_navbar_child_create_own_viewset_higher_denial as regression

    section = _flat(_section(REFERENCE.read_text(), "## Labels, access and empty output"))
    assert regression.__name__ in section
    for phrase in (
        "even on the create target's own ViewSet page (D-55)",
        "Page create controls now apply the same known higher gates",
        "stage 3b does not migrate the navbar again",
        "both its navbar item and context create button hidden",
        "actor admission and declared parent gates run before any create override",
        "create request returns 403",
        "rendering_view.cv_viewset is target.cv_viewset",
        "unknown levels stay None",
        "No ancestor/membership lookup is added",
    ):
        assert phrase in section


def test_navbar_cost_docs_separate_stage_three_receipts_from_historical_savings():
    from tests.test1.test_label_mode_docs import _flat, _section

    section = _flat(_section(REFERENCE.read_text(), "## Measured costs"))
    for phrase in (
        "Remeasured for stage 3a on 2026-11-25",
        "one immediate-parent gate with the exact owner object",
        "zero delta against the stage-3a before receipt",
        "fixture has a top-level owner",
        "warm user is different from this table's warm Django model cache",
        "historical stage-2 Django 6 before/after receipts",
        "06.50-COST-BASELINE.md#after-measurements",
        "normal next request gets a distinct user/checker",
        "historical stage-3a observations, not fresh stage-3b measurements",
    ):
        assert phrase in section
    assert "| guardian | warm | warm | 2 / 2 | 0 / 0 | 0 |" in section


@pytest.mark.parametrize(
    ("path", "heading", "statements"),
    (
        (
            "reference/guardian.md",
            "### Known ancestry and Cancel",
            (
                "Every known-parent create consumer now checks the aligned known higher ancestors",
                "Navbar child items already used that ancestry on every page (D-55)",
                "Guardian object/list/create Cancel uses the shared check",
                "queryset-only list also checks the declared immediate-parent policy",
                "Higher ancestors come only from guard state",
            ),
        ),
        (
            "reference/nested.md",
            "### Visible links and buttons",
            (
                "immediate parent and known higher ancestors",
                "permission-only filter never calls it",
                "parent ViewSet's get_queryset()",
                "custom-hook exceptions propagate",
                "No request response or login redirect changes",
                "standalone queryset-only compositions",
                "Parent-only non-create Cancel omits cv_has_access",
                "Historical stage-2 child cases",
                "historical two-level costs do not measure stage 3b",
            ),
        ),
        (
            "faq.md",
            "### Gate surrounding markup by permission",
            (
                "never calls the state hook",
                "cv_create_has_access(user, view, parent)",
                "immediate and known higher parent gates before the create hook",
                "Child-list and M2M filters can now return True",
                "ambiguous M2M child still denies",
            ),
        ),
    ),
)
def test_related_references_keep_target_specific_stage_three_contracts(path, heading, statements):
    from tests.test1.test_label_mode_docs import _flat, _section

    section = _flat(_section((ROOT / "docs" / path).read_text(), heading))
    for statement in statements:
        assert statement in section
