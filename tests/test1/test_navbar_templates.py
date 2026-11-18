"""Template seams, request-local laziness and accessible object section links."""

from copy import copy
from unittest.mock import Mock

import pytest
from django.contrib.auth.models import AnonymousUser
from django.template import Context, Template, TemplateDoesNotExist
from django.template.loader import get_template
from django.test import RequestFactory, override_settings
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
)

TEMPLATES = ["navbar", "navbar_identity", "navbar_items"]
TAG = "{% load crud_views %}{% cv_navbar %}"
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


@pytest.mark.parametrize("copied", ["copy", "new", "flatten", "include-only"])
def test_context_copies_and_repeated_calls_reuse_one_lazy_build(copied, monkeypatch):
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
            else SPLIT
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
            assert render(TAG, data) == ""
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
        assert render(TAG, view.get_context_data()) == ""
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
        assert "First" in render(TAG, first)
        assert render(TAG, second) == ""
        assert calls == [(allowed, "First"), (denied, "Second")]
        assert "First" in render(TAG, first)
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


def test_german_landmark_uses_shipped_translation():
    with navbar_routes(owner_routes) as ns:
        _, data = view_context(ns)
        with override("de"):
            tree = html.fromstring(render('{% include "crud_views/tags/navbar_items.html" %}', data))
        assert tree.get("aria-label") == "Abschnitte für Owner"


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
def test_plain_labels_and_accessible_names_are_escaped_once(language, prefix, default_label, text, monkeypatch):
    monkeypatch.setattr(Publisher, "__str__", lambda self: text)
    options = {"template_code": "{{ object }}"} if default_label else {"label": text}
    with navbar_routes(lambda sfx: owner_routes(sfx, **options)) as ns:
        _, data = view_context(ns)
        with override(language):
            output = render(TAG, data)
        tree = html.fromstring(output)
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


@pytest.mark.parametrize("name", TEMPLATES)
def test_configuration_errors_propagate_without_retry_or_placeholder(name):
    from django.core.exceptions import ImproperlyConfigured

    with navbar_routes(owner_routes) as ns:
        ns.bar.items[0].key = "unregistered"
        _, data = view_context(ns)
        with pytest.raises(ImproperlyConfigured, match="unregistered destination"):
            render('{% include "crud_views/tags/' + name + '.html" %}', data)
