"""Execute presentation migration fences through the real rendering pipeline."""

from pathlib import Path

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.template import Context, Library, Template, engines
from django.template.loader import render_to_string
from django.test import RequestFactory, override_settings
from django.utils.translation import gettext_lazy, override
from lxml import html

from crud_views_object_detail.lib.conf import crud_views_object_detail_settings
from crud_views_object_detail.lib.config import parse_property_display
from crud_views_object_detail.lib.resolvers import ResolvedGroup, ResolvedProperty, resolve_all
from tests.test1.od.test_badge_semantics import template_settings
from tests.test1.od_app.models import Report
from tests.test1.test_heading_docs import recipe

ROOT = Path(__file__).resolve().parents[2]
LAYOUTS = ROOT / "docs/reference/object_detail_layout_packs.md"
CONFIGURATION = ROOT / "docs/reference/object_detail_configuration.md"
TAG = "{% load crud_views_object_detail %}{% render_object_detail obj groups layout=layout component_id=token %}"


def copied_templates(pack):
    parts = ("object_detail", "group", "property") if pack == "native" else ("object_detail", "group")
    templates = {
        f"crud_views_object_detail/layouts/{pack}/{part}.html": recipe(LAYOUTS, f"### {pack} {part}") for part in parts
    }
    if pack == "native":
        templates["native-value.html"] = recipe(LAYOUTS, "### native value")
    return templates


def render(groups, pack, token="author-page"):
    return Template(TAG).render(Context({"groups": groups, "layout": pack, "token": token}))


@pytest.mark.parametrize("pack", ["tabs-vertical", "accordion"])
@pytest.mark.parametrize("count", [1, 2])
@pytest.mark.parametrize("language", ["en", "de"])
def test_copied_interactive_recipes(pack, count, language):
    groups = [
        ResolvedGroup(
            title=gettext_lazy(month), id=key, properties=[ResolvedProperty("name", "Name", "<script>x</script>")]
        )
        for month, key in [("January", "jan"), ("February", "feb")][:count]
    ]
    with override_settings(TEMPLATES=template_settings(copied_templates(pack))), override(language):
        output = render(groups, pack)
        assert render(groups, pack) == output
    tree = html.fromstring(output)
    controls = tree.cssselect("button[data-bs-toggle]")
    assert len(controls) == count
    assert ("Januar" if language == "de" else "January") in tree.text_content()
    assert not tree.cssselect("script")
    assert "<script>x</script>" in tree.text_content()
    ids = tree.xpath("descendant-or-self::*/@id")
    assert len(ids) == len(set(ids))
    for index, control in enumerate(controls):
        key = groups[index].id
        expected = f"cvod-c11-author-page-s3-{key}"
        assert control.get("id") == expected + "-control"
        assert control.get("aria-controls") == expected + "-panel"
        assert control.get("data-bs-target") == "#" + expected + "-panel"
        (panel,) = tree.xpath(".//*[@id=$id]", id=control.get("aria-controls"))
        assert panel.get("aria-labelledby") == control.get("id")
        if pack == "tabs-vertical":
            assert control.get("aria-selected") == ("true" if index == 0 else "false")
            assert control.get("tabindex") == ("0" if index == 0 else "-1")
            assert panel.get("tabindex") == "0"
            assert ("active" in panel.classes) is (index == 0)
            assert ("show" in panel.classes) is (index == 0)
        else:
            assert control.get("aria-expanded") == "false"
            assert panel.get("data-bs-parent") == "#cvod-c11-author-page-root"


@pytest.mark.parametrize("pack", ["tabs-vertical", "accordion", "native"])
def test_copied_recipes_preserve_hostile_resolved_context(pack):
    hostile = '<img src=x onerror="bad"> & text'
    configs = parse_property_display(
        [
            {
                "title": hostile,
                "id": "bio",
                "properties": [
                    {"path": "title", "title": hostile, "template": "native-value.html" if pack == "native" else None}
                ],
            }
        ]
    )
    groups = resolve_all(Report(title=hostile), configs)
    with override_settings(TEMPLATES=template_settings(copied_templates(pack))):
        tree = html.fromstring(render(groups, pack))
    assert not tree.cssselect("img, [onerror]")
    assert hostile in tree.text_content()
    if pack == "native":
        assert tree.cssselect("section > h3")
        assert tree.cssselect("dt")[0].text == hostile
        value = tree.cssselect("dd > span")[0]
        assert value.text == hostile
        assert value.get("data-path") == "title"
        assert value.get("data-newline") == crud_views_object_detail_settings.property_text_newline


def test_published_request_identity_hook():
    namespace = {}
    exec(compile(recipe(CONFIGURATION, "### Page and modal identity", "python"), str(CONFIGURATION), "exec"), namespace)
    view_class = namespace["AuthorIdentityMixin"]
    targets = []
    for modal in (False, True):
        view = view_class()
        view.request = RequestFactory().get("/author/", **({"HTTP_X_CV_MODAL": "true"} if modal else {}))
        token = view.cv_get_object_detail_id()
        assert token == ("author-modal" if modal else "author-page")
        with override_settings(TEMPLATES=template_settings(copied_templates("tabs-vertical"))):
            first = render([ResolvedGroup("Author", id="bio")], "tabs-vertical", token)
            assert render([ResolvedGroup("Author", id="bio")], "tabs-vertical", token) == first
        targets.append(html.fromstring(first).cssselect('[role="tabpanel"]')[0].get("id"))
    assert targets == ["cvod-c11-author-page-s3-bio-panel", "cvod-c12-author-modal-s3-bio-panel"]


@pytest.mark.parametrize(
    "outer",
    [
        '{% include "piece.html" %}{% include "piece.html" %}',
        '{% extends "base.html" %}{% block second %}{% include "piece.html" %}{% endblock %}',
    ],
)
def test_copied_recipe_detects_sibling_and_inherited_collisions(outer):
    templates = copied_templates("tabs-vertical") | {
        "piece.html": TAG,
        "base.html": '{% include "piece.html" %}{% block second %}{% endblock %}',
    }
    with (
        override_settings(TEMPLATES=template_settings(templates)),
        pytest.raises(ImproperlyConfigured, match="author-page"),
    ):
        Template(outer).render(
            Context({"groups": [ResolvedGroup("One")], "layout": "tabs-vertical", "token": "author-page"})
        )


def test_copied_recipe_transported_nested_collision_and_fresh_backend_boundary():
    templates = copied_templates("tabs-vertical")
    stable_tag = TAG.replace("layout=layout", 'layout="tabs-vertical"').replace(
        "component_id=token", 'component_id="author-page"'
    )
    templates["nested.html"] = stable_tag
    nested = [ResolvedGroup("One", properties=[ResolvedProperty("name", "Name", "Value", template="nested.html")])]
    with override_settings(TEMPLATES=template_settings(templates)):
        with pytest.raises(ImproperlyConfigured, match="author-page"):
            render(nested, "tabs-vertical")
        library = Library()

        @library.simple_tag
        def fresh_backend():
            # A new dict deliberately does not transport the library's private scope.
            return render_to_string("nested.html", {"groups": [ResolvedGroup("Independent")]})

        engine = engines["django"].engine
        engine.template_builtins.append(library)
        output = engine.from_string(stable_tag + "{% fresh_backend %}").render(
            Context({"groups": [ResolvedGroup("Outer")]})
        )
        assert output.count('id="cvod-c11-author-page-root"') == 2


def test_copied_recipe_rejects_duplicate_group_keys_and_documents_focus_boundary():
    with (
        override_settings(TEMPLATES=template_settings(copied_templates("tabs-vertical"))),
        pytest.raises(ImproperlyConfigured, match="group id"),
    ):
        render([ResolvedGroup("One", id="bio"), ResolvedGroup("Two", id="bio")], "tabs-vertical")
    text = LAYOUTS.read_text()
    for phrase in (
        "tabindex=0",
        "first focusable descendant",
        "plain text",
        "Template.render",
        "render_to_string",
        "private scope",
    ):
        assert phrase in text


MIGRATION = ROOT / "docs/migrating-1.0.md"


def test_published_removed_keyword_replacement():
    from pydantic import ValidationError

    from crud_views.lib.view.card import CardAction

    namespace = {}
    exec(compile(recipe(MIGRATION, "### Removed card label keyword", "python"), str(MIGRATION), "exec"), namespace)
    assert namespace["action"].label_mode == "icon"
    assert namespace["inherited"].label_mode is None
    for value in (False, True, None):
        with pytest.raises(ValidationError, match='label_mode="icon"'):
            CardAction(key="detail", no_label=value)
    from tests.test1.test_button_data import base

    context = base(cv_label='<img src=x onerror="bad">', cv_no_label=False, cv_access=True)
    output = Template(recipe(MIGRATION, "### Removed card label keyword")).render(Context(context))
    node = html.fromstring(output)
    assert node.tag == "a" and node.get("href") == "/u/"
    assert node.get("title") == '<img src=x onerror="bad">'
    assert node.cssselect(".visually-hidden")
    assert not node.cssselect("img, [onerror]")


def test_published_filtered_object_detail_assets():
    from crud_views.lib.pipeline import cv_sources

    namespace = {}
    exec(compile(recipe(MIGRATION, "### Filtered object-detail assets", "python"), str(MIGRATION), "exec"), namespace)
    path = "crud_views_object_detail/js/tabs.js"
    assert list(namespace["sources"]).count(path) == 1
    assert list(cv_sources("js")).count(path) == 1
    assert path not in list(cv_sources("js", keys=["crud_views"]))


def test_current_release_and_migration_claims_are_paired():
    unreleased = (ROOT / "CHANGELOG.md").read_text().split("## Unreleased", 1)[1].split("\n## ", 1)[0]
    migration = MIGRATION.read_text()
    for title, anchor in (
        ("Heading hosts and sizing", "heading-hosts-and-sizing"),
        ("Interactive object-detail templates and targets", "interactive-object-detail-templates-and-targets"),
        ("Removed card label keyword", "removed-card-label-keyword"),
    ):
        assert f"**{title}.**" in unreleased
        assert f"docs/migrating-1.0.md#{anchor}" in unreleased
        assert migration.count(f"### {title}\n") == 1
    for obsolete in (
        "CardAction(no_label=True)` keeps working",
        "CardAction(no_label=True)` is unaffected",
        "CardAction(no_label=True)` still",
        "(`CardAction(no_label=True)`)",
        "cv_no_label is no longer a leaf input",
        "cv_no_label` is no longer a `cv_button_data()` input and raises",
    ):
        assert obsolete not in unreleased
        assert obsolete not in migration
    assert "harmless" in unreleased and "unprojected" in unreleased
    assert "cv_context_actions_label_mode" in migration and "cv_context_action_label_mode" in migration
    assert "badge_color" in unreleased and "badge_pill" in unreleased
    assert "reference/object_detail_layout_packs.md#collision-detection-boundary" in migration


@pytest.mark.parametrize("icon", ["fas:pen", "", None])
def test_retained_standalone_header_icon(icon):
    from crud_views.lib.view import CrudView

    class View(CrudView):
        def cv_get_header_icon(self):
            return icon

    output = Template("{% load crud_views %}{% cv_header_icon %}").render(Context({"view": View()}))
    if icon:
        node = html.fromstring(output)
        assert node.tag == "i"
        assert node.get("class") == "fa-solid fa-pen"
        assert node.get("aria-hidden") == "true"
    else:
        assert output == ""


def test_public_surface_inventory_matches_real_contracts():
    from dataclasses import fields
    from inspect import signature

    from crud_views.lib.button_classes import DEFAULT_BUTTON_CLASSES, button_class_check_messages
    from crud_views.lib.pipeline import cv_sources
    from crud_views.lib.view.card import CardAction
    from crud_views.templatetags import crud_views as core
    from crud_views_object_detail.lib.config import PropertyGroupConfig
    from crud_views_object_detail.lib.mixins import ObjectDetailMixin
    from crud_views_object_detail.lib.presentation import ComponentPresentation, GroupPresentation
    from crud_views_object_detail.templatetags import crud_views_object_detail as detail

    inventory = (
        ROOT / ".planning/phases/06.5-remaining-presentation-contracts-and-decided-cleanup/06.5-PUBLIC-SURFACE.md"
    )
    text = inventory.read_text()
    keys = {f"heading:size-{n}" for n in range(1, 7)} | {"heading:icon-host", "heading:icon-inline"}
    assert keys <= DEFAULT_BUTTON_CLASSES.keys()
    keys |= {
        f"heading-{location}:icon-{slot}" for location in ("page", "modal", "group") for slot in ("host", "inline")
    }
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES=dict.fromkeys(keys, "")):
        assert not list(button_class_check_messages())
    for key in keys:
        assert key in text
    for tag in ("cv_heading", "cv_heading_icon", "cv_header_icon"):
        assert tag in core.register.tags and tag in text
    assert set(signature(core.cv_heading_icon).parameters) == {"value", "location"}
    assert {field.name for field in fields(core.HeadingIconPresentation)} == {"host_class", "inline_html"}
    for name in ("size", "icon_class", "host_class", "inline_html"):
        assert name in text
    for cls, prefix in ((ComponentPresentation, "component"), (GroupPresentation, "presentation")):
        for field in fields(cls):
            assert f"{prefix}.{field.name}" in text
    assert "id" in PropertyGroupConfig.model_fields
    assert "id" in {field.name for field in fields(ResolvedGroup)}
    assert "component_id" in signature(detail.render_object_detail).parameters
    assert {"presentation", "component"} <= signature(detail.render_group).parameters.keys()
    assert hasattr(ObjectDetailMixin, "cv_object_detail_id")
    assert callable(ObjectDetailMixin.cv_get_object_detail_id)
    assert {"badge_color", "badge_pill"} <= {field.name for field in fields(ResolvedProperty)}
    assert "no_label" not in CardAction.model_fields
    assert list(cv_sources("js")).count("crud_views_object_detail/js/tabs.js") == 1
    for name in (
        "PropertyGroupConfig.id",
        "ResolvedGroup.id",
        "component_id",
        "object_detail_id",
        "cv_get_object_detail_id",
        "cv_object_detail_id",
        "badge_color",
        "badge_pill",
        "cv_no_label",
        "cv.initObjectDetailTabs(root=document)",
        "data-cv-od-tabs",
        "cv:modal:loaded",
        "cv:modal:unload",
        "standalone",
        "superseded",
        "test_retained_standalone_header_icon",
        "Phase 7",
        "private",
        "docs/migrating-1.0.md#heading-hosts-and-sizing",
        "docs/migrating-1.0.md#interactive-object-detail-templates-and-targets",
        "docs/migrating-1.0.md#removed-card-label-keyword",
    ):
        assert name in text
    assert "cv:dom-updated" not in LAYOUTS.read_text()
