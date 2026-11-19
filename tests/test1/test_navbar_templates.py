"""Template seams, request-local laziness and accessible object section links."""

from copy import copy
from unittest.mock import Mock

import pytest
from django.contrib.auth.models import AnonymousUser
from django.template import Context, Template, TemplateDoesNotExist
from django.template.library import SimpleNode
from django.template.loader import get_template
from django.test import Client, RequestFactory, override_settings
from django.urls import reverse
from django.utils.functional import SimpleLazyObject
from django.utils.safestring import mark_safe
from django.utils.translation import override
from lxml import html

from crud_views.lib import navbar
from tests.test1.app.models import Publisher
from tests.test1.test_navbar import (
    get_owner,
    navbar_routes,
    navbar_templates,
    owner_routes,
    section_objects,
    section_routes,
    section_url,
)

TEMPLATES = ["navbar", "navbar_identity", "navbar_items"]
TAG = "{% load crud_views %}{% cv_navbar %}"
IDENTITY = "{% load crud_views %}{% cv_navbar_identity %}"
ITEMS = "{% load crud_views %}{% cv_navbar_items %}"
COMPONENTS = IDENTITY + "<main>Page content</main>" + ITEMS
SPLIT = (
    '{% include "crud_views/tags/navbar_identity.html" %}'
    "<main>Page content</main>"
    '{% include "crud_views/tags/navbar_items.html" %}'
)


def render(source, data):
    return Template(source).render(data if isinstance(data, Context) else Context(data))


def view_context(ns, *, name="Owner", user=None, modal=False):
    view = ns.view()
    request = RequestFactory().get("/", HTTP_X_CV_MODAL="true" if modal else "false")
    request.user = user or AnonymousUser()
    view.setup(request, pk=1)
    view.object = Publisher(pk=1, name=name)
    return view, view.get_context_data()


@pytest.mark.parametrize("name", TEMPLATES)
def test_each_template_is_a_public_rendering_seam(name):
    try:
        template = get_template(f"crud_views/tags/{name}.html")
    except TemplateDoesNotExist:
        template = None
    assert template is not None, f"Missing public navbar template: {name}"


@pytest.mark.parametrize("name", TEMPLATES)
@pytest.mark.parametrize("data", [{}, {"cv_navbar": None}, {"cv_navbar": SimpleLazyObject(lambda: None)}])
def test_each_template_emits_exactly_nothing_when_absent(name, data):
    assert render('{% include "crud_views/tags/' + name + '.html" %}', data) == ""


@pytest.mark.parametrize("mode", ["wrapper", "identity", "items", "per-bar", "split"])
def test_overrides_receive_the_same_named_context(mode, monkeypatch):
    build = Mock(wraps=navbar._build)
    monkeypatch.setattr(navbar, "_build", build)
    with navbar_routes(owner_routes) as ns:
        overrides = {}
        marker = '<aside data-custom="yes">{{ cv_navbar.label }}:{{ cv_navbar.items.0.label }}</aside>'
        if mode in {"wrapper", "identity", "items"}:
            name = "navbar" if mode == "wrapper" else "navbar_" + mode
            overrides[f"crud_views/tags/{name}.html"] = marker
        if mode == "per-bar":
            ns.bar.template = "custom/bar.html"
            overrides[ns.bar.template] = marker + SPLIT
        with navbar_templates(overrides):
            view, data = view_context(ns)
            lazy = data["cv_navbar"]
            assert isinstance(lazy, SimpleLazyObject)
            assert view.get_context_data()["cv_navbar"] is lazy
            assert build.call_count == 0
            output = render(SPLIT if mode == "split" else TAG, data)
            tree = html.fragment_fromstring(output, create_parent="div")
            if mode == "split":
                assert not tree.xpath('.//*[@class="cv-navbar mb-3"]')
                assert [node.tag for node in tree] == ["div", "main", "nav"]
            else:
                assert tree.xpath('.//*[@data-custom="yes"]')[0].text_content().startswith("Owner:")
            if mode == "identity":
                assert tree.xpath(".//nav//a")
            if mode == "items":
                assert tree.xpath('.//*[contains(@class,"cv-navbar-identity")]')
            assert build.call_count == 1
            assert data["cv_navbar"] is lazy


@pytest.mark.parametrize("source", [SPLIT, COMPONENTS, ITEMS + IDENTITY])
@pytest.mark.parametrize("copied", ["copy", "new", "flatten", "include-only"])
def test_context_copies_and_repeated_calls_reuse_one_lazy_build(copied, source, monkeypatch):
    build = Mock(wraps=navbar._build)
    monkeypatch.setattr(navbar, "_build", build)
    with navbar_routes(owner_routes) as ns:
        view, data = view_context(ns)
        context = Context(data)
        other = {
            "copy": lambda: copy(context),
            "new": lambda: context.new(data),
            "flatten": lambda: Context(context.flatten()),
            "include-only": lambda: context,
        }[copied]()
        assert other["cv_navbar"] is context["cv_navbar"]
        assert build.call_count == 0
        source = (
            '{% include "crud_views/tags/navbar_identity.html" with cv_navbar=cv_navbar only %}'
            if copied == "include-only"
            else source
        )
        assert "Owner" in render(source, other)
        assert "Owner" in render(TAG, view.get_context_data())
        assert build.call_count == 1


@pytest.mark.parametrize("modal", [False, True])
def test_omitted_consumers_and_modal_direct_includes_do_no_work(modal, monkeypatch):
    forbidden = Mock(side_effect=AssertionError("Navbar work must stay lazy"))
    monkeypatch.setattr(navbar, "_build", forbidden)
    with navbar_routes(owner_routes) as ns:
        monkeypatch.setattr(ns.view, "cv_has_access", forbidden)
        monkeypatch.setattr(ns.view, "_cv_action_enabled_for_rendering", forbidden)
        view, data = view_context(ns, modal=modal)
        assert render("Page without navigation", data) == "Page without navigation"
        view.get_context_data()
        if modal:
            assert data["cv_navbar"] is None
            assert render(TAG + IDENTITY + ITEMS, data) == ""
            for name in TEMPLATES:
                assert render('{% include "crud_views/tags/' + name + '.html" %}', data) == ""
        forbidden.assert_not_called()


@pytest.mark.parametrize("denial", ["access", "state", "empty"])
def test_all_hidden_renders_exactly_empty_and_is_cached(denial, monkeypatch):
    build = Mock(wraps=navbar._build)
    monkeypatch.setattr(navbar, "_build", build)
    with navbar_routes(owner_routes) as ns:
        if denial == "empty":
            ns.bar.items = []
        else:
            method = "cv_has_access" if denial == "access" else "_cv_action_enabled_for_rendering"
            monkeypatch.setattr(ns.view, method, lambda *args: False)
        view, data = view_context(ns)
        for name in TEMPLATES:
            assert render('{% include "crud_views/tags/' + name + '.html" %}', data) == ""
        assert render(TAG + IDENTITY + ITEMS, view.get_context_data()) == ""
        assert build.call_count == 1


def test_separate_requests_do_not_share_users_or_results(monkeypatch):
    with navbar_routes(owner_routes) as ns:
        allowed, denied = object(), object()
        calls = []

        def access(user, owner):
            calls.append((user, owner.name))
            return user is allowed

        monkeypatch.setattr(ns.view, "cv_has_access", access)
        _, first = view_context(ns, name="First", user=allowed)
        _, second = view_context(ns, name="Second", user=denied)
        assert first["cv_navbar"] is not second["cv_navbar"]
        assert calls == []
        assert "First" in render(IDENTITY + ITEMS, first)
        assert render(ITEMS + IDENTITY, second) == ""
        assert calls == [(allowed, "First"), (denied, "Second")]
        assert "First" in render(IDENTITY + ITEMS, first)
        assert len(calls) == 2


@pytest.mark.django_db
def test_split_real_request_keeps_header_placement():
    obj = Publisher.objects.create(name="Owner")
    with navbar_routes(owner_routes) as ns:
        base = get_template("navbar/base.html").template.source
        with navbar_templates({"navbar/base.html": base.replace("{% cv_navbar %}", SPLIT)}):
            tree = html.fromstring(get_owner(ns, obj).content)
            identity = tree.xpath('.//*[contains(@class,"cv-navbar-identity")]')[0]
            nav = tree.xpath('.//nav[@aria-label="Sections for Owner"]')[0]
            header = tree.xpath(".//*[@data-test-page-title]")[0]
            nodes = list(tree.iter())
            assert nodes.index(identity) < nodes.index(nav) < nodes.index(header)
            assert header.text_content().strip() == "Unchanged page header"


@pytest.mark.parametrize("source", ['{% include "crud_views/tags/navbar_items.html" %}', ITEMS])
def test_german_landmark_uses_shipped_translation(source):
    with navbar_routes(owner_routes) as ns:
        _, data = view_context(ns)
        with override("de"):
            tree = html.fromstring(render(source, data))
        assert tree.get("aria-label") == "Abschnitte für Owner"


@pytest.mark.parametrize("source", [TAG, COMPONENTS])
@pytest.mark.parametrize("language,prefix", [("en", "Sections for "), ("de", "Abschnitte für ")])
@pytest.mark.parametrize("default_label", [False, True])
@pytest.mark.parametrize(
    "text",
    [
        'A & B\'s "branch"',
        "literal &amp; &#39; 50% %(object)s",
        '<b>ordinary & "markup"</b>',
        mark_safe('<script>alert("x")</script><b title="bad">Safe &amp; text</b>'),
        mark_safe('" onmouseover="alert(1)" & <img src=x onerror=alert(1)>'),
    ],
)
def test_plain_labels_and_accessible_names_are_escaped_once(source, language, prefix, default_label, text, monkeypatch):
    monkeypatch.setattr(Publisher, "__str__", lambda self: text)
    options = {"template_code": "{{ object }}"} if default_label else {"label": text}
    with navbar_routes(lambda sfx: owner_routes(sfx, **options)) as ns:
        _, data = view_context(ns)
        with override(language):
            output = render(source, data)
        tree = html.fragment_fromstring(output, create_parent="div")
        identity = tree.xpath('.//*[contains(@class,"cv-navbar-identity")]')[0]
        link = tree.xpath(".//a")[0]
        nav = tree.xpath(".//nav")[0]
        # A safe snippet is already rendered HTML; its entity text is decoded once
        # by the owner default-label contract. Raw overrides retain literal entities.
        from html import unescape

        expected = unescape(str(text)) if default_label and hasattr(text, "__html__") else str(text)
        assert identity.text_content().strip() == str(text)
        assert link.text_content().strip() == expected
        assert nav.get("aria-label") == prefix + str(text)
        assert not tree.xpath(".//script | .//b | .//img | .//*[@onmouseover] | .//*[@onerror]")
        assert type(data["cv_navbar"]["label"]) is str
        assert type(data["cv_navbar"]["items"][0]["label"]) is str


@pytest.mark.django_db
@pytest.mark.parametrize("hidden", [[], [0], [1], [0, 1, 2], [0, 1, 2, 3]])
@pytest.mark.parametrize("reason", ["access", "state"])
def test_zero_one_many_and_partial_links_have_static_navigation_semantics(hidden, reason, monkeypatch):
    with navbar_routes(section_routes) as ns:
        owner, _, _ = section_objects(ns)
        for index in hidden:
            item = ns.bar.items[index]
            target = (ns.child if item.child else ns.owner).get_view_class(item.key or "list")
            method = (
                ("_cv_child_link_has_access" if item.child else "cv_has_access")
                if reason == "access"
                else ("_cv_action_enabled_for_rendering")
            )
            monkeypatch.setattr(target, method, lambda *args: False)
        # A nonparticipating destination avoids confusing request permission with
        # link admission; the same owner/detail key is still the current section.
        view = ns.views[(ns.owner.name, "detail")]()
        request = RequestFactory().get("/")
        request.user = AnonymousUser()
        view.setup(request, owner_pk=owner.pk)
        view.object = owner
        data = view.get_context_data()
        output = render(TAG, data)
        if len(hidden) == 4:
            assert output == ""
            return
        tree = html.fromstring(output)
        nav = tree.xpath(".//nav")[0]
        links = nav.xpath("./ul/li/a")
        expected = [label for i, label in enumerate(["Customer details", "Edit", "Notes", "Orders"]) if i not in hidden]
        assert [a.text_content().strip() for a in links] == expected
        assert len(nav.xpath("./ul/li")) == len(expected)
        assert nav.get("aria-label") == "Sections for Customer"
        assert len(nav.xpath('.//a[@aria-current="true"]')) == (0 if 0 in hidden else 1)
        assert all(a.get("href") and a.get("tabindex") is None for a in links)
        assert not tree.xpath('.//*[@role="tab" or @role="tablist" or @aria-selected or @data-bs-toggle]')
        assert not tree.xpath(".//script | .//button | .//form | .//*[@aria-busy] | .//*[@tabindex]")
        assert not tree.xpath('.//*[contains(@class,"spinner") or contains(@class,"placeholder")]')
        identity = tree.xpath('.//*[contains(@class,"cv-navbar-identity")]')[0]
        assert identity.text_content().strip() == "Customer"
        assert not identity.xpath(".//a | .//button | .//h1 | .//h2")
        assert "flex-wrap" in nav.xpath("./ul")[0].get("class").split()
        assert "nav-fill" not in nav.xpath("./ul")[0].get("class").split()
        for li in nav.xpath("./ul/li"):
            assert "mw-100" in li.get("class").split()
        assert "text-break" in identity.get("class").split()


@pytest.mark.parametrize("icon", [None, "", "fas:building", "host:building"])
def test_icons_are_decorative_or_absent_without_losing_labels(icon):
    libraries = {
        "host": {
            "renderer": "font",
            "class": "host-{name}",
            "placement": "host",
            "standalone": "host-icon {name_class}",
        }
    }
    with override_settings(CRUD_VIEWS_ICON_LIBRARIES=libraries), navbar_routes(owner_routes) as ns:
        ns.owner.icon_header = icon
        ns.bar.items[0].icon = icon
        ns.view.cv_icon_action = icon
        _, data = view_context(ns)
        tree = html.fromstring(render(TAG, data))
        identity = tree.xpath('.//*[contains(@class,"cv-navbar-identity")]')[0]
        assert identity.text_content().strip() == "Owner"
        assert tree.xpath(".//a")[0].text_content().strip()
        icons = tree.xpath(".//i")
        assert len(icons) == (2 if icon else 0)
        assert all(i.get("aria-hidden") == "true" and i.get("tabindex") is None for i in icons)
        if icon == "host:building":
            assert all(i.get("class") == "host-icon host-building" for i in icons)


def test_long_text_is_complete_and_uses_wrapping_utilities():
    caption = "Customer " * 20 + "X" * 100
    label = "Section " * 15 + "Y" * 100
    with navbar_routes(lambda sfx: owner_routes(sfx, label=label)) as ns:
        _, data = view_context(ns, name=caption)
        tree = html.fromstring(render(TAG, data))
        identity = tree.xpath('.//*[contains(@class,"cv-navbar-identity")]')[0]
        link = tree.xpath(".//a")[0]
        assert identity.text_content().strip() == caption
        assert link.text_content().strip() == label
        assert tree.xpath(".//nav")[0].get("aria-label") == "Sections for " + caption
        assert "text-break" in link.get("class").split()
        assert not tree.xpath('.//*[contains(@class,"text-truncate") or contains(@class,"overflow-hidden")]')


@pytest.mark.parametrize("name", TEMPLATES + ["identity-tag", "items-tag"])
def test_configuration_errors_propagate_without_retry_or_placeholder(name):
    from django.core.exceptions import ImproperlyConfigured

    with navbar_routes(owner_routes) as ns:
        ns.bar.items[0].key = "unregistered"
        _, data = view_context(ns)
        with pytest.raises(ImproperlyConfigured, match="unregistered destination"):
            source = {"identity-tag": IDENTITY, "items-tag": ITEMS}.get(
                name, '{% include "crud_views/tags/' + name + '.html" %}'
            )
            render(source, data)


@pytest.mark.django_db
@pytest.mark.parametrize("modal", [False, True])
def test_real_response_omits_all_navbar_work_without_consumers_or_in_custom_modal(modal, monkeypatch):
    forbidden = Mock(side_effect=AssertionError("Navbar work in omitted/modal response"))
    monkeypatch.setattr(navbar, "_build", forbidden)
    obj = Publisher.objects.create(name="Owner")
    with navbar_routes(owner_routes) as ns:
        ns.view.cv_modal = modal
        ns.view.cv_extends_template = "navbar/without.html"
        monkeypatch.setattr(ns.view, "cv_has_access", forbidden)
        monkeypatch.setattr(ns.view, "_cv_action_enabled_for_rendering", forbidden)
        custom_modal = IDENTITY + ITEMS + "".join('{% include "crud_views/tags/' + name + '.html" %}' for name in TEMPLATES)
        with navbar_templates({"crud_views/modal/content.html": custom_modal}):
            url = reverse(ns.owner.get_router_name("detail"), kwargs={ns.owner.pk_name: obj.pk})
            response = Client().get(url, HTTP_X_CV_MODAL="true" if modal else "false")
        assert response.status_code == 200
        if modal:
            assert response.content == b""
            assert response.context["cv_navbar"] is None
        else:
            assert b"Unchanged page header" in response.content
        forbidden.assert_not_called()


@pytest.mark.django_db
def test_descendant_current_section_is_still_a_clickable_collection_link():
    with navbar_routes(section_routes) as ns:
        owner, child, grand = section_objects(ns)
        response = Client().get(section_url(ns, ns.grand, "update", owner, child, grand))
        tree = html.fromstring(response.content)
        nav = tree.xpath('.//nav[@aria-label="Sections for Customer"]')[0]
        current = nav.xpath('.//a[@aria-current="true"]')
        assert len(current) == 1
        assert current[0].text_content().strip() == "Orders"
        assert current[0].get("href") == section_url(ns, ns.child, "list", owner, child, grand)
        assert current[0].get("tabindex") is None


@pytest.mark.django_db
@pytest.mark.parametrize("components", [("identity",), ("items",), ("identity", "items"), ("items", "identity")])
def test_component_tags_render_independently_in_real_response(components):
    obj = Publisher.objects.create(name="Owner")
    sources = {"identity": IDENTITY, "items": ITEMS}
    source = '<main data-body="yes">Page content</main>'.join(sources[name] for name in components)
    with navbar_routes(owner_routes) as ns:
        base = get_template("navbar/base.html").template.source
        with navbar_templates({"navbar/base.html": base.replace("{% cv_navbar %}", source)}):
            response = get_owner(ns, obj)
        assert response.status_code == 200
        tree = html.fromstring(response.content)
        identities = tree.xpath('.//*[contains(@class,"cv-navbar-identity")]')
        navs = tree.xpath('.//nav[@aria-label="Sections for Owner"]')
        assert len(identities) == ("identity" in components)
        assert len(navs) == ("items" in components)
        assert not tree.xpath('.//*[@class="cv-navbar mb-3"]')
        nodes = list(tree.iter())
        if len(components) == 2:
            parts = {"identity": identities[0], "items": navs[0]}
            body = tree.xpath('.//*[@data-body="yes"]')[0]
            assert nodes.index(parts[components[0]]) < nodes.index(body) < nodes.index(parts[components[1]])
        header = tree.xpath('.//*[@data-test-page-title]')[0]
        assert header.text_content().strip() == "Unchanged page header"


def test_default_wrapper_delegates_to_component_tags():
    from crud_views.templatetags.crud_views import cv_navbar_identity, cv_navbar_items

    template = get_template("crud_views/tags/navbar.html").template
    functions = [node.func for node in template.nodelist.get_nodes_by_type(SimpleNode)]
    assert functions == [cv_navbar_identity, cv_navbar_items]


@pytest.mark.parametrize("theme", ["crud_views", "alternate"])
@pytest.mark.parametrize("with_request", [False, True])
def test_component_tags_preserve_caller_context_and_theme_overrides(theme, with_request, monkeypatch):
    from crud_views.lib.settings import crud_views_settings

    monkeypatch.setattr(crud_views_settings, "theme_path", theme)
    with navbar_routes(owner_routes) as ns:
        ns.bar.template = "custom/component-wrapper.html"
        _, data = view_context(ns)
        data["marker"] = "caller"
        request = RequestFactory().get("/original/")
        if with_request:
            data["request"] = request
        seen = []

        def observe(value):
            seen.append(value)
            return ""

        data["observe"] = lambda: observe((data["cv_navbar"], data["view"], data.get("request")))
        leaf = '{{ observe }}{{ marker }}:{{ view.cv_key }}:{{ request.path }}:{{ cv_navbar.label }}'
        overrides = {
            f"{theme}/tags/navbar_identity.html": "identity:" + leaf,
            f"{theme}/tags/navbar_items.html": "items:" + leaf,
            ns.bar.template: 'wrapper:{% load crud_views %}{% cv_navbar_items %}|{% cv_navbar_identity %}',
        }
        with navbar_templates(overrides):
            suffix = "caller:detail:" + ("/original/" if with_request else "") + ":Owner"
            assert render(IDENTITY, data) == "identity:" + suffix
            assert render(ITEMS, data) == "items:" + suffix
            assert render(TAG, data) == "wrapper:items:" + suffix + "|identity:" + suffix
        assert len(seen) == 4
        for lazy, view, original_request in seen:
            assert lazy is data["cv_navbar"]
            assert view is data["view"]
            assert original_request is (request if with_request else None)


@pytest.mark.parametrize("source", [IDENTITY, ITEMS, IDENTITY + ITEMS])
@pytest.mark.parametrize("data", [{}, {"cv_navbar": None}, {"cv_navbar": SimpleLazyObject(lambda: None)}])
def test_component_tags_emit_exactly_nothing_when_absent(source, data):
    assert render(source, data) == ""
