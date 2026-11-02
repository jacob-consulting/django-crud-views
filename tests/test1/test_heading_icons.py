"""Heading icon projection through real modal markup and the shared registry."""

from pathlib import Path
from unittest.mock import Mock

import pytest
from django.template import Context, Engine
from django.test import override_settings
from django.utils.html import format_html
from lxml import html

from crud_views.lib import button_classes as bc
from crud_views.lib.settings import crud_views_settings
from crud_views.lib.view import CrudView
from crud_views.templatetags.crud_views import cv_heading_icon

HOST_LIBRARY = {"host": {"renderer": "font", "placement": "host", "class": "icon-{name}"}}


def render_modal(icon="host:edit", title="Edit <title>"):
    source = Path("src/crud_views/templates/crud_views/modal/content.html").read_text()
    engine = Engine(
        loaders=[("django.template.loaders.locmem.Loader", {"modal.html": source, "body.html": "Body"})],
        libraries={"crud_views": "crud_views.templatetags.crud_views", "i18n": "django.templatetags.i18n"},
    )
    view = Mock(spec=CrudView)
    view.do_not_call_in_templates = True
    view.cv_get_header_icon = Mock(spec=lambda: None, return_value=icon)
    view.cv_header = title
    view.cv_content_template = "body.html"
    result = engine.get_template("modal.html").render(Context({"view": view}))
    view.cv_get_header_icon.assert_called_once_with()
    return result


def test_modal_host_icon_is_on_title(monkeypatch):
    monkeypatch.setattr(crud_views_settings, "header_level", 2)
    with override_settings(
        CRUD_VIEWS_ICON_LIBRARIES=HOST_LIBRARY,
        CRUD_VIEWS_BUTTON_CLASSES={"heading:size-5": "title-small"},
    ):
        result = render_modal()
    assert '<h2 class="title-small modal-title icon-edit"> Edit &lt;title&gt;</h2>' in result
    assert "<i " not in result


@pytest.mark.parametrize("location", ["page", "modal", "group"])
@pytest.mark.parametrize("slot", ["icon-host", "icon-inline"])
@pytest.mark.parametrize(
    "project,theme,expected",
    [
        ({"shared": "project"}, {"local": "theme-local"}, "project"),
        ({"shared": "project", "local": "project-local"}, {"local": "theme-local"}, "project-local"),
        ({}, {"shared": "theme", "local": "theme-local"}, "theme-local"),
        ({}, {"shared": "theme"}, "theme"),
        ({"shared": None}, {"local": "theme-local"}, ""),
        ({"local": "", "shared": "project"}, {}, ""),
        ({}, {"local": None, "shared": "theme"}, ""),
    ],
)
def test_heading_layer_precedes_specificity(monkeypatch, location, slot, project, theme, expected):
    def expand(values):
        return {
            f"heading-{location}:{slot}" if key == "local" else f"heading:{slot}": value
            for key, value in values.items()
        }

    monkeypatch.setattr(bc, "_THEME_BUTTON_CLASSES", expand(theme))
    with override_settings(CRUD_VIEWS_BUTTON_CLASSES=expand(project)):
        assert bc._heading_class(location, slot) == expected


@pytest.mark.parametrize("location,spacing", [("page", ""), ("modal", ""), ("group", "me-2")])
def test_heading_builtin_icon_slots(location, spacing):
    with override_settings(CRUD_VIEWS_ICON_LIBRARIES=HOST_LIBRARY):
        host = cv_heading_icon("host:edit", location)
        assert (host.host_class, host.inline_html) == ("icon-edit", "")
    inline = cv_heading_icon("detail", location)
    assert inline.host_class == ""
    icon = html.fromstring(inline.inline_html)
    assert icon.get("class") == "fa-regular fa-eye" + (f" {spacing}" if spacing else "")


@pytest.mark.parametrize("value", [None, "", "  ", 42, "missing:icon"])
def test_empty_heading_icons(value):
    icon = cv_heading_icon(value)
    assert (icon.host_class, icon.inline_html) == ("", "")


@pytest.mark.parametrize("disabled", [None, ""])
def test_disabled_semantic_icon_keeps_modal_text(monkeypatch, disabled):
    monkeypatch.setattr(crud_views_settings, "header_level", None)
    with override_settings(CRUD_VIEWS_ICONS={"detail": disabled}):
        result = render_modal("detail")
    assert '<h5 class="modal-title"> Edit &lt;title&gt;</h5>' in result


def test_heading_mixed_libraries_and_single_renderer_evaluation():
    renderer = Mock(side_effect=lambda name, **kwargs: format_html('<svg class="{}">{}</svg>', kwargs["css"], name))
    with override_settings(
        CRUD_VIEWS_ICON_LIBRARIES={**HOST_LIBRARY, "svg": {"renderer": renderer}},
        CRUD_VIEWS_ICONS={"edit": "host:edit", "detail": "svg:eye"},
        CRUD_VIEWS_BUTTON_CLASSES={"heading:icon-inline": "inline-spacing"},
    ):
        assert cv_heading_icon("edit").host_class == "icon-edit"
        renderer.assert_not_called()
        icon = cv_heading_icon("detail")
        assert icon.host_class == ""
        assert icon.inline_html == '<svg class="inline-spacing">eye</svg>'
        renderer.assert_called_once_with("eye", css="inline-spacing", config={"renderer": renderer})
        assert '<i class="raw-icon inline-spacing"' in cv_heading_icon("raw-icon").inline_html


def test_heading_settings_are_read_after_button_cache_is_warmed(monkeypatch, settings):
    monkeypatch.setattr(bc, "_THEME_BUTTON_CLASSES", {"heading-modal:icon-host": "theme {name_class}"})
    with override_settings(CRUD_VIEWS_ICON_LIBRARIES=HOST_LIBRARY, CRUD_VIEWS_BUTTON_CLASSES={}):
        bc.get_button_classes()
        assert cv_heading_icon("host:edit", "modal").host_class == "theme icon-edit"
        settings.CRUD_VIEWS_BUTTON_CLASSES["heading:icon-host"] = "project {name_class}"
        assert cv_heading_icon("host:edit", "modal").host_class == "project icon-edit"


def test_hostile_heading_classes_and_titles_stay_in_their_dom_attributes(monkeypatch):
    monkeypatch.setattr(crud_views_settings, "header_level", 2)
    with override_settings(
        CRUD_VIEWS_ICON_LIBRARIES=HOST_LIBRARY,
        CRUD_VIEWS_BUTTON_CLASSES={
            "heading:size-5": 'size" onload="attack',
            "heading:icon-host": '{name_class}" onclick="attack',
        },
    ):
        result = render_modal('host:edit" onerror="attack', "<script>attack</script>")
    heading = html.fromstring(result).xpath(".//h2")[0]
    assert set(heading.attrib) == {"class"}
    assert heading.text == " <script>attack</script>"
    assert len(heading) == 0


def test_modal_element_icon_preserves_default_bytes(monkeypatch):
    monkeypatch.setattr(crud_views_settings, "header_level", None)
    assert (
        '<h5 class="modal-title"><i class="fa-regular fa-eye" aria-hidden="true"></i> Edit &lt;title&gt;</h5>'
        in render_modal("detail")
    )


@pytest.mark.parametrize("disabled", [None, ""])
@pytest.mark.parametrize("level,classes", [(None, "modal-title"), (2, "h5 modal-title")])
def test_modal_disabled_host_retains_title(monkeypatch, disabled, level, classes):
    monkeypatch.setattr(crud_views_settings, "header_level", level)
    with override_settings(
        CRUD_VIEWS_ICON_LIBRARIES=HOST_LIBRARY,
        CRUD_VIEWS_BUTTON_CLASSES={"heading:icon-host": disabled},
    ):
        result = render_modal()
    assert f'class="{classes}"> Edit &lt;title&gt;</h' in result
    assert "<i " not in result
