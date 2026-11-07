"""Real object-detail renders share identities and initial selection across contexts."""

from copy import deepcopy

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.template import Context, Template
from django.test import override_settings
from django.utils.translation import gettext_lazy
from lxml import html

from crud_views_object_detail.lib.resolvers import ResolvedGroup, ResolvedProperty


def render(groups, layout="tabs-vertical", repeat=False, standalone=False, **context):
    tag = (
        "{% render_group group layout=layout %}"
        if standalone
        else "{% render_object_detail obj groups layout=layout %}"
    )
    template = Template("{% load crud_views_object_detail %}" + tag * (2 if repeat else 1))
    markup = template.render(
        Context({"groups": groups, "group": groups[0] if groups else None, "layout": layout, **context})
    )
    return html.fromstring(f"<main>{markup}</main>")


@pytest.mark.parametrize("count", [0, 1, 2])
@pytest.mark.parametrize("focusable", [False, True])
def test_tabs_initial_selection(count, focusable):
    prop = ResolvedProperty(path="name", label="Name", value="Value", link_url="/next/" if focusable else None)
    doc = render([ResolvedGroup(title="Same", properties=[prop]) for _ in range(count)])
    tabs = doc.cssselect('[role="tab"]')
    panels = doc.cssselect('[role="tabpanel"]')
    assert len(tabs) == len(panels) == count
    assert len(doc.cssselect(".tab-pane.active.show")) == min(1, count)
    assert len(doc.cssselect('[role="tab"].active[aria-selected="true"]')) == min(1, count)
    assert len(doc.cssselect('[data-cv-od-tabs][aria-orientation="vertical"]')) == 1
    for index, (tab, panel) in enumerate(zip(tabs, panels, strict=True)):
        assert tab.get("aria-controls") == panel.get("id")
        assert tab.get("data-bs-target") == "#" + panel.get("id")
        assert panel.get("aria-labelledby") == tab.get("id")
        assert tab.get("tabindex") == ("0" if index == 0 else "-1")
        assert tab.get("aria-selected") == ("true" if index == 0 else "false")
        assert panel.get("tabindex") == "0"


def test_generated_targets_ignore_titles_and_do_not_mutate_groups():
    groups = [ResolvedGroup(title=title) for title in ["A B", "A-B", "", "", gettext_lazy("日本語"), '<img src="x">']]
    before = deepcopy(groups)
    doc = render(groups, repeat=True)
    ids = doc.xpath("//@id")
    assert len(ids) == len(set(ids))
    assert all(value.startswith("cvod-c33-g") for value in ids)
    assert groups == before
    assert not doc.cssselect("img")
    assert set(ids).isdisjoint(render(groups).xpath("//@id"))


def test_standalone_tab_has_label_without_missing_control():
    doc = render([ResolvedGroup(title='<Title " &>')], standalone=True)
    (panel,) = doc.cssselect('[role="tabpanel"]')
    assert panel.get("aria-labelledby") is None
    assert panel.get("aria-label") == '<Title " &>'
    assert "active" in panel.classes and "show" in panel.classes


@pytest.mark.parametrize("layout", ["tabs-vertical", "accordion"])
@pytest.mark.parametrize("icon", ["host:edit", "fas:pen", "", None, "disabled"])
@pytest.mark.parametrize("hostile", [False, True])
def test_interactive_title_button_owns_icon(icon, hostile, layout):
    group = ResolvedGroup(title='<em>Title & "text"</em>', icon=icon)
    with override_settings(
        CRUD_VIEWS_ICON_LIBRARIES={"host": {"renderer": "font", "placement": "host", "class": "icon-{name}"}},
        CRUD_VIEWS_ICONS={"disabled": None},
        CRUD_VIEWS_BUTTON_CLASSES={
            "heading-group:icon-host": '{name_class}" onclick="attack' if hostile else "group {name_class}",
            "heading-group:icon-inline": 'inline" onerror="attack' if hostile else "group-inline",
        },
    ):
        doc = render([group], layout=layout)
    (button,) = doc.cssselect("button[data-bs-toggle]")
    assert group.title in button.text_content()
    assert not doc.cssselect("em, [onclick], [onerror]")
    structural = {"nav-link", "text-start", "active"} if layout == "tabs-vertical" else {"accordion-button"}
    assert structural <= button.classes
    assert len(button.cssselect("i")) == (1 if icon == "fas:pen" else 0)
    assert ("icon-edit" in button.get("class")) == (icon == "host:edit")
    if icon == "fas:pen":
        assert button.cssselect("i")[0].get("aria-hidden") == "true"
    assert not any("icon-edit" in heading.get("class", "") for heading in doc.cssselect("h2, h5"))


@pytest.mark.parametrize("token", ["", "1bad", "bad token", "with.dot", "é", 'x" onclick="bad', 123, False])
def test_invalid_component_token_rejected(token):
    from crud_views_object_detail.templatetags.crud_views_object_detail import render_object_detail

    with pytest.raises(ImproperlyConfigured, match="component_id"):
        render_object_detail(Context(), None, [], layout="tabs-vertical", component_id=token)


@pytest.mark.parametrize("count", [0, 1, 5])
def test_accordion_targets_belong_to_their_component(count):
    groups = [
        ResolvedGroup(title=title) for title in ["Same", "Same", "", gettext_lazy("日本語"), '<img src="x">'][:count]
    ]
    before = deepcopy(groups)
    doc = render(groups, layout="accordion", repeat=True)
    assert groups == before
    assert not doc.cssselect("img")
    ids = doc.xpath("//@id")
    assert len(ids) == len(set(ids))
    for root in doc.cssselect(".accordion"):
        controls = root.cssselect(".accordion-button")
        panels = root.cssselect(".accordion-collapse")
        assert len(controls) == len(panels) == len(groups)
        assert len(root.cssselect(".accordion-collapse.show")) == min(1, count)
        for index, (control, panel) in enumerate(zip(controls, panels, strict=True)):
            assert control.get("id")
            assert control.get("aria-controls") == panel.get("id")
            assert control.get("data-bs-target") == "#" + panel.get("id")
            assert panel.get("aria-labelledby") == control.get("id")
            assert panel.get("data-bs-parent") == "#" + root.get("id")
            assert control.get("aria-expanded") == ("true" if index == 0 else "false")
            assert ("collapsed" in control.classes) is (index != 0)
            assert ("show" in panel.classes) is (index == 0)


def test_standalone_accordion_omits_unrendered_parent():
    doc = render([ResolvedGroup(title="Same")], layout="accordion", standalone=True, repeat=True)
    ids = doc.xpath("//@id")
    assert len(ids) == len(set(ids))
    assert not doc.cssselect("[data-bs-parent]")
    for control, panel in zip(doc.cssselect("button"), doc.cssselect(".accordion-collapse"), strict=True):
        assert panel.get("aria-labelledby") == control.get("id")
        assert control.get("aria-controls") == panel.get("id")
        assert control.get("aria-expanded") == "true"
        assert "collapsed" not in control.classes
        assert "show" in panel.classes


def test_direct_calls_without_active_render_have_independent_scopes():
    from crud_views_object_detail.templatetags.crud_views_object_detail import render_object_detail

    context = Context()
    first = render_object_detail(context, None, [ResolvedGroup(title="One")], layout="accordion", component_id="stable")
    second = render_object_detail(
        context, None, [ResolvedGroup(title="One")], layout="accordion", component_id="stable"
    )
    assert first == second


@pytest.mark.parametrize("token", [False, 0, "", " ", "with.dot", "1bad", "é", 'x" onclick="bad'])
def test_group_config_rejects_invalid_identity_before_coercion(token):
    from crud_views_object_detail.lib.config import PropertyGroupConfig

    with pytest.raises(ImproperlyConfigured, match="group id"):
        PropertyGroupConfig(title="Title", properties=[], id=token)


def test_group_identity_preserved_by_resolution_and_positional_compatibility():
    from crud_views_object_detail.lib.config import PropertyGroupConfig
    from crud_views_object_detail.lib.resolvers import resolve_group

    config = PropertyGroupConfig(title="Title", properties=[], id="Biography_2")
    assert getattr(resolve_group(None, config), "id", None) == "Biography_2"
    assert getattr(ResolvedGroup("Title", None, None, []), "id", "missing") is None


@pytest.mark.django_db
@pytest.mark.parametrize("native", [False, True])
def test_real_detail_stable_page_modal_identity(client_user_author_view, author_douglas_adams, monkeypatch, native):
    from django.conf import settings
    from django.db import connection
    from django.test.utils import CaptureQueriesContext
    from django.urls import reverse

    from crud_views.lib.view.base import cv_is_modal_request
    from tests.test1.app.views import AuthorDetailView

    authorized_objects = []
    get_object_for_detail = AuthorDetailView.get_object_for_detail

    def record_object(view):
        with CaptureQueriesContext(connection) as queries:
            obj = get_object_for_detail(view)
        assert len(queries) == 0
        assert obj is view.object
        authorized_objects.append(obj)
        return obj

    monkeypatch.setattr(AuthorDetailView, "get_object_for_detail", record_object)
    monkeypatch.setattr(AuthorDetailView, "cv_object_detail_layout", "identity-native" if native else "tabs-vertical")
    monkeypatch.setattr(AuthorDetailView, "cv_object_detail_id", "author-page", raising=False)
    groups = [
        {"title": "Biography", "id": "bio", "properties": ["first_name"]},
        {"title": "Dates", "id": "dates", "properties": ["first_name"]},
    ]
    monkeypatch.setattr(AuthorDetailView, "cv_property_display", groups)
    templates = deepcopy(settings.TEMPLATES)
    if native:
        templates[0]["APP_DIRS"] = False
        templates[0]["OPTIONS"]["loaders"] = [
            (
                "django.template.loaders.locmem.Loader",
                {
                    "crud_views_object_detail/layouts/identity-native/group.html": (
                        '{% load crud_views_object_detail %}<section id="{{ presentation.panel_id }}" '
                        'data-root="{{ component.id }}"><h2 id="{{ presentation.control_id }}">{{ group.title }}</h2>'
                        '{% for prop in group.properties %}{% render_property prop layout="table-inline" %}{% endfor %}'
                        "</section>"
                    ),
                },
            ),
            "django.template.loaders.app_directories.Loader",
        ]

    def expected(token):
        base = f"cvod-c{len(token)}-{token}"
        ids = {f"{base}-s{len(key)}-{key}-{kind}" for key in ("bio", "dates") for kind in ("control", "panel")}
        if not native:
            ids |= {f"{base}-{kind}" for kind in ("root", "tabs", "content")}
        return ids

    url = reverse("author-detail", kwargs={"pk": author_douglas_adams.pk})
    with override_settings(TEMPLATES=templates):
        # Attribute default must reach the actual content template, with no implicit suffix.
        response = client_user_author_view.get(url)
        assert response.status_code == 200
        assert len(authorized_objects) == 1
        assert response.context["object"] is authorized_objects[-1]
        doc = html.fromstring(response.content)
        assert set(doc.xpath('//@id[starts-with(., "cvod-")]')) == expected("author-page")

        def identity(view):
            return "author-modal" if cv_is_modal_request(view.request) else "author-page"

        monkeypatch.setattr(AuthorDetailView, "cv_get_object_detail_id", identity, raising=False)
        for repeated in range(2):
            if repeated:
                monkeypatch.setattr(
                    AuthorDetailView,
                    "cv_property_display",
                    [{**group, "title": gettext_lazy("日本語 <translated>")} for group in reversed(groups)],
                )
            for modal, token in [(False, "author-page"), (True, "author-modal")]:
                previous_count = len(authorized_objects)
                response = client_user_author_view.get(url, **({"HTTP_X_CV_MODAL": "true"} if modal else {}))
                assert response.status_code == 200
                assert len(authorized_objects) == previous_count + 1
                assert response.context["object"] is authorized_objects[-1]
                assert response.context["object"].pk == author_douglas_adams.pk
                assert response.context["object_detail_id"] == token
                assert {group.id for group in response.context["object_detail_groups"]} == {"bio", "dates"}
                doc = html.fromstring(response.content)
                assert set(doc.xpath('//@id[starts-with(., "cvod-")]')) == expected(token)
                assert author_douglas_adams.first_name in doc.text_content()
                assert not doc.cssselect("translated")
                if native:
                    assert set(doc.xpath("//@data-root")) == {f"cvod-c{len(token)}-{token}-root"}


_STABLE_TAG = (
    "{% load crud_views_object_detail %}"
    '{% render_object_detail obj groups layout="tabs-vertical" component_id="stable" %}'
)


def _identity_engine(templates):
    from django.template import Engine

    return Engine(
        loaders=[("django.template.loaders.locmem.Loader", templates)],
        libraries={"crud_views_object_detail": "crud_views_object_detail.templatetags.crud_views_object_detail"},
    )


@pytest.mark.parametrize(
    "outer",
    [
        _STABLE_TAG + _STABLE_TAG,
        '{% include "piece" %}{% include "piece" %}',
        '{% include "piece" only %}{% include "piece" only %}',
        '{% extends "base" %}{% block second %}{% include "piece" %}{% endblock %}',
    ],
)
def test_duplicate_component_detected_across_outer_render(outer):
    engine = _identity_engine(
        {"outer": outer, "piece": _STABLE_TAG, "base": '{% include "piece" %}{% block second %}{% endblock %}'}
    )
    with pytest.raises(ImproperlyConfigured, match="stable"):
        engine.get_template("outer").render(Context({"groups": [ResolvedGroup("One", id="bio")]}))


@pytest.mark.parametrize("token", [False, 0, "", " ", "with.dot", 'x" onclick="bad'])
def test_direct_resolved_group_ids_are_validated(token):
    with pytest.raises(ImproperlyConfigured, match="group id"):
        render([ResolvedGroup("Title", id=token)])


def test_duplicate_group_identity_rejected_before_scope_is_reserved():
    from crud_views_object_detail.lib.presentation import _project_component

    scope = set()
    with pytest.raises(ImproperlyConfigured, match="bio"):
        _project_component([ResolvedGroup("One", id="bio"), ResolvedGroup("Two", id="bio")], "stable", scope)
    assert scope == set()
    _project_component([ResolvedGroup("One", id="bio")], "stable", scope)


def test_compiled_template_reused_context_and_request_allow_repeated_identity():
    from django.test import RequestFactory

    template = Template(_STABLE_TAG)
    request = RequestFactory().get("/")
    context = Context({"request": request, "groups": [ResolvedGroup("One", id="bio")]})
    first = template.render(context)
    assert template.render(context) == first
    assert template.render(Context({"request": request, "groups": context["groups"]})) == first
    assert context.render_context.dicts == [{"True": True, "False": False, "None": None}]


def test_concurrent_independent_renders_share_no_registry():
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    template = Template(_STABLE_TAG)
    barrier = Barrier(4)

    def run(_):
        barrier.wait(timeout=10)
        return template.render(Context({"groups": [ResolvedGroup("One", id="bio")]}))

    with ThreadPoolExecutor(max_workers=4) as pool:
        outputs = list(pool.map(run, range(4)))
    assert len(set(outputs)) == 1


def test_nested_independent_template_render_has_its_own_scope():
    from django.template import Library

    library = Library()

    @library.simple_tag
    def independent():
        return Template(_STABLE_TAG).render(Context({"groups": []}))

    engine = _identity_engine({})
    engine.template_builtins.append(library)
    output = engine.from_string(_STABLE_TAG + "{% independent %}").render(Context({"groups": []}))
    assert output.count('id="cvod-c6-stable-root"') == 2


def test_nested_property_template_shares_explicitly_transported_scope():
    from django.conf import settings

    templates = deepcopy(settings.TEMPLATES)
    templates[0]["APP_DIRS"] = False
    templates[0]["OPTIONS"]["loaders"] = [
        ("django.template.loaders.locmem.Loader", {"nested-identity.html": _STABLE_TAG}),
        "django.template.loaders.app_directories.Loader",
    ]
    prop = ResolvedProperty("name", "Name", "Value", template="nested-identity.html")
    with override_settings(TEMPLATES=templates), pytest.raises(ImproperlyConfigured, match="stable"):
        Template(_STABLE_TAG).render(Context({"groups": [ResolvedGroup("One", properties=[prop], id="bio")]}))


def test_failed_render_releases_registry_for_next_render():
    context = Context({"groups": [ResolvedGroup("One", id="bio")]})
    with pytest.raises(ImproperlyConfigured, match="stable"):
        Template(_STABLE_TAG * 2).render(context)
    assert 'id="cvod-c6-stable-root"' in Template(_STABLE_TAG).render(context)


def test_adversarial_component_group_pairs_remain_disjoint_and_unchanged():
    from crud_views_object_detail.lib.presentation import _project_component

    pairs = [("a", "b-c"), ("a-b", "c"), ("a-s1-b", "c"), ("a", "b-s1-c"), ("a", "i0")]
    projections = [_project_component([ResolvedGroup("Same", id=group)], component) for component, group in pairs]
    targets = [
        value
        for projection in projections
        for entry in projection.groups
        for value in (entry.control_id, entry.panel_id)
    ]
    assert len(targets) == len(set(targets))
    for (component, group), projection in zip(pairs, projections, strict=True):
        assert projection.groups[0].panel_id == f"cvod-c{len(component)}-{component}-s{len(group)}-{group}-panel"
    positional = _project_component([ResolvedGroup("Same")], "a")
    assert positional.groups[0].panel_id == "cvod-c1-a-i0-panel"
    assert positional.groups[0].panel_id not in targets
