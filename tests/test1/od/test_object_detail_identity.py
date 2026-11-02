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
    structural = (
        {"nav-link", "text-start", "active"} if layout == "tabs-vertical" else {"accordion-button", "collapsed"}
    )
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


def test_accordion_targets_belong_to_their_component():
    groups = [ResolvedGroup(title=title) for title in ["A B", "A-B", "", gettext_lazy("日本語")]]
    doc = render(groups, layout="accordion", repeat=True)
    ids = doc.xpath("//@id")
    assert len(ids) == len(set(ids))
    for root in doc.cssselect(".accordion"):
        controls = root.cssselect(".accordion-button")
        panels = root.cssselect(".accordion-collapse")
        assert len(controls) == len(panels) == len(groups)
        for control, panel in zip(controls, panels, strict=True):
            assert control.get("id")
            assert control.get("aria-controls") == panel.get("id")
            assert control.get("data-bs-target") == "#" + panel.get("id")
            assert panel.get("aria-labelledby") == control.get("id")
            assert panel.get("data-bs-parent") == "#" + root.get("id")
            assert control.get("aria-expanded") == "false"
            assert "show" not in panel.classes


def test_standalone_accordion_omits_unrendered_parent():
    doc = render([ResolvedGroup(title="Same")], layout="accordion", standalone=True, repeat=True)
    ids = doc.xpath("//@id")
    assert len(ids) == len(set(ids))
    assert not doc.cssselect("[data-bs-parent]")
    for control, panel in zip(doc.cssselect("button"), doc.cssselect(".accordion-collapse"), strict=True):
        assert panel.get("aria-labelledby") == control.get("id")
        assert control.get("aria-controls") == panel.get("id")


def test_duplicate_supplied_component_in_direct_scope_fails():
    from crud_views_object_detail.templatetags.crud_views_object_detail import render_object_detail

    context = Context()
    render_object_detail(context, None, [ResolvedGroup(title="One")], layout="accordion", component_id="stable")
    with pytest.raises(ImproperlyConfigured, match="stable"):
        render_object_detail(context, None, [ResolvedGroup(title="Two")], layout="tabs-vertical", component_id="stable")


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
    from django.urls import reverse

    from crud_views.lib.view.base import cv_is_modal_request
    from tests.test1.app.views import AuthorDetailView

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
            ("django.template.loaders.locmem.Loader", {
                "crud_views_object_detail/layouts/identity-native/group.html":
                    '{% load crud_views_object_detail %}<section id="{{ presentation.panel_id }}" '
                    'data-root="{{ component.id }}"><h2 id="{{ presentation.control_id }}">{{ group.title }}</h2>'
                    '{% for prop in group.properties %}{% render_property prop layout="table-inline" %}{% endfor %}'
                    '</section>',
            }),
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
        doc = html.fromstring(response.content)
        assert set(doc.xpath('//@id[starts-with(., "cvod-")]')) == expected("author-page")

        def identity(view):
            return "author-modal" if cv_is_modal_request(view.request) else "author-page"

        monkeypatch.setattr(AuthorDetailView, "cv_get_object_detail_id", identity, raising=False)
        for repeated in range(2):
            if repeated:
                monkeypatch.setattr(AuthorDetailView, "cv_property_display", [
                    {**group, "title": gettext_lazy("日本語 <translated>")} for group in reversed(groups)
                ])
            for modal, token in [(False, "author-page"), (True, "author-modal")]:
                response = client_user_author_view.get(url, **({"HTTP_X_CV_MODAL": "true"} if modal else {}))
                assert response.status_code == 200
                assert response.context["object"].pk == author_douglas_adams.pk
                assert response.context["object_detail_id"] == token
                assert {group.id for group in response.context["object_detail_groups"]} == {"bio", "dates"}
                doc = html.fromstring(response.content)
                assert set(doc.xpath('//@id[starts-with(., "cvod-")]')) == expected(token)
                assert author_douglas_adams.first_name in doc.text_content()
                assert not doc.cssselect("translated")
                if native:
                    assert set(doc.xpath("//@data-root")) == {f"cvod-c{len(token)}-{token}-root"}
