"""Heading icon projection through real modal markup and the shared registry."""

import re
from pathlib import Path
from unittest.mock import Mock

import pytest
from django.template import Context, Engine, Template
from django.test import override_settings
from django.utils.html import format_html
from django.utils.translation import gettext_lazy
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


def example_title_source():
    source = Path("examples/bootstrap5/project/templates/project/crud_views.html").read_text()
    fragments = re.findall(
        r'{% cv_heading_icon [^%]*location="page"[^%]*%}\s*{% cv_heading .*?{% endcv_heading %}',
        source,
        re.DOTALL,
    )
    assert len(fragments) == 1, "The actual example must contain exactly one complete page title fragment"
    assert "{% block cv_header %}" in fragments[0]
    return "{% load crud_views %}" + fragments[0]


@pytest.mark.django_db
@pytest.mark.parametrize("site", ["page", "example"])
@pytest.mark.parametrize("level,size", [(None, "h3"), (2, "native-size"), (3, "")])
@pytest.mark.parametrize("icon", ["host:edit", "fas:pen", "", None, "disabled"])
def test_page_title_contract(monkeypatch, site, level, size, icon):
    from tests.test1.app.views import AuthorListView, cv_author
    from tests.test1.test_heading_level import _client

    title = gettext_lazy('<script>Title & "name"</script>')
    monkeypatch.setattr(crud_views_settings, "header_level", level)
    monkeypatch.setattr(AuthorListView, "cv_header", title)
    monkeypatch.setattr(AuthorListView, "cv_get_header_icon", lambda self: icon)
    overrides = {} if size == "h3" else {"heading:size-3": size}
    with override_settings(
        CRUD_VIEWS_ICON_LIBRARIES=HOST_LIBRARY,
        CRUD_VIEWS_ICONS={"disabled": None},
        CRUD_VIEWS_BUTTON_CLASSES=overrides,
    ):
        if site == "page":
            response = _client(cv_author, ("view",)).get("/author/")
            assert response.status_code == 200
            (wrapper,) = html.fromstring(response.content).cssselect("[data-test-page-title]")
        else:
            view = AuthorListView()
            wrapper = html.fromstring(
                "<div>" + Template(example_title_source()).render(Context({"view": view})) + "</div>"
            )
    (heading,) = wrapper.xpath(".//*[self::h1 or self::h2 or self::h3 or self::h4 or self::h5 or self::h6]")
    assert heading.tag == f"h{level or 1}"
    assert heading.text_content().strip() == str(title)
    expected = [
        value
        for value in (size, "mb-0" if site == "example" else "", "icon-edit" if icon == "host:edit" else "")
        if value
    ]
    assert heading.get("class", "").split() == expected
    assert len(heading.cssselect("i")) == (1 if icon == "fas:pen" else 0)
    assert not heading.xpath(".//script")
    assert all(node.get("aria-hidden") == "true" for node in heading.cssselect("i"))


@pytest.mark.django_db
@pytest.mark.parametrize("site", ["page", "example"])
def test_page_title_hostile_classes(monkeypatch, site):
    from tests.test1.app.views import AuthorListView, cv_author
    from tests.test1.test_heading_level import _client

    monkeypatch.setattr(crud_views_settings, "header_level", 2)
    monkeypatch.setattr(AuthorListView, "cv_header", "<em>Title</em>")
    monkeypatch.setattr(AuthorListView, "cv_get_header_icon", lambda self: 'host:edit" onerror="attack')
    with override_settings(
        CRUD_VIEWS_ICON_LIBRARIES=HOST_LIBRARY,
        CRUD_VIEWS_BUTTON_CLASSES={
            "heading:size-3": 'size" onload="attack',
            "heading:icon-host": '{name_class}" onclick="attack',
        },
    ):
        if site == "page":
            response = _client(cv_author, ("view",)).get("/author/")
            assert response.status_code == 200
            (heading,) = html.fromstring(response.content).cssselect("[data-test-page-title] h2")
        else:
            heading = html.fromstring(Template(example_title_source()).render(Context({"view": AuthorListView()})))
    assert set(heading.attrib) == {"class"}
    assert heading.text_content().strip() == "<em>Title</em>"
    assert len(heading) == 0


@pytest.mark.parametrize("layout", ["split-card", "striped-rows"])
@pytest.mark.parametrize("icon", ["host:edit", "fas:pen", "", None, "disabled"])
@pytest.mark.parametrize("hostile", [False, True])
def test_plain_group_icon_belongs_to_title(monkeypatch, layout, icon, hostile):
    from crud_views_object_detail.lib.resolvers import ResolvedGroup, ResolvedProperty

    monkeypatch.setattr(crud_views_settings, "header_level", 2)
    title = gettext_lazy('<em>Translated & "title"</em>')
    group = ResolvedGroup(
        title=title,
        description="Description <text>",
        icon=icon,
        properties=[ResolvedProperty(path="name", label="Name", value="Value <text>", type="char")],
    )
    with override_settings(
        CRUD_VIEWS_ICON_LIBRARIES=HOST_LIBRARY,
        CRUD_VIEWS_ICONS={"disabled": None},
        CRUD_VIEWS_BUTTON_CLASSES={
            "heading:size-5": "native-size",
            "heading-group:icon-host": '{name_class}" onclick="attack' if hostile else "group {name_class}",
            "heading-group:icon-inline": 'inline" onerror="attack' if hostile else "group-inline",
        },
    ):
        markup = Template("{% load crud_views_object_detail %}{% render_group group layout=layout %}").render(
            Context({"group": group, "layout": layout})
        )
    doc = html.fromstring(markup)
    (heading,) = doc.cssselect("h3")
    assert heading.text_content() == str(title)
    assert set(heading.attrib) == {"class"}
    assert "native-size" in heading.get("class").split()
    assert "mb-0" in heading.get("class").split()
    assert not heading.cssselect("em")
    assert len(doc.cssselect("i")) == (1 if icon == "fas:pen" else 0)
    if icon == "host:edit":
        assert "icon-edit" in heading.get("class")
    if icon == "fas:pen":
        (inline,) = heading.cssselect("i")
        assert set(inline.attrib) == {"class", "aria-hidden"}
        assert inline.get("aria-hidden") == "true"
        assert (
            "group-inline" in inline.get("class") if not hostile else 'inline" onerror="attack' in inline.get("class")
        )
    assert "Value <text>" in doc.text_content()
    if layout == "split-card":
        assert "Description <text>" in doc.text_content()
