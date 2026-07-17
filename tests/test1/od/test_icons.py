from django.template import Context, Template
from django.test import override_settings

from crud_views_object_detail.lib.conf import (
    CrudViewsObjectDetailSettings,
    build_icon_class,
    build_named_icon_class,
)
from crud_views_object_detail.lib.resolvers import ResolvedGroup, ResolvedProperty


# ---------------------------------------------------------------------------
# Conf field tests
# ---------------------------------------------------------------------------


class TestIconsLibrary:
    def test_default(self):
        assert CrudViewsObjectDetailSettings().icons_library == "bootstrap"

    @override_settings(CRUD_VIEWS_OBJECT_DETAIL_ICONS_LIBRARY="fontawesome")
    def test_override(self):
        assert CrudViewsObjectDetailSettings().icons_library == "fontawesome"


class TestIconsClass:
    def test_default_bootstrap(self):
        assert CrudViewsObjectDetailSettings().icons_class == "bi"

    @override_settings(CRUD_VIEWS_OBJECT_DETAIL_ICONS_LIBRARY="fontawesome")
    def test_default_fontawesome(self):
        assert CrudViewsObjectDetailSettings().icons_class == "fa"

    @override_settings(CRUD_VIEWS_OBJECT_DETAIL_ICONS_CLASS="custom")
    def test_override(self):
        assert CrudViewsObjectDetailSettings().icons_class == "custom"


class TestIconsType:
    def test_default_bootstrap(self):
        assert CrudViewsObjectDetailSettings().icons_type is None

    @override_settings(CRUD_VIEWS_OBJECT_DETAIL_ICONS_LIBRARY="fontawesome")
    def test_default_fontawesome(self):
        assert CrudViewsObjectDetailSettings().icons_type == "regular"

    @override_settings(CRUD_VIEWS_OBJECT_DETAIL_ICONS_TYPE="solid")
    def test_override(self):
        assert CrudViewsObjectDetailSettings().icons_type == "solid"

    @override_settings(CRUD_VIEWS_OBJECT_DETAIL_ICONS_TYPE=None)
    def test_explicit_none(self):
        """Explicitly setting type to None should return None, not library default."""
        assert CrudViewsObjectDetailSettings().icons_type is None


class TestIconsPrefix:
    def test_default_bootstrap(self):
        assert CrudViewsObjectDetailSettings().icons_prefix == "bi"

    @override_settings(CRUD_VIEWS_OBJECT_DETAIL_ICONS_LIBRARY="fontawesome")
    def test_default_fontawesome(self):
        assert CrudViewsObjectDetailSettings().icons_prefix == "fa"

    @override_settings(CRUD_VIEWS_OBJECT_DETAIL_ICONS_PREFIX="icon")
    def test_override(self):
        assert CrudViewsObjectDetailSettings().icons_prefix == "icon"


class TestNamedIcons:
    def test_default_bootstrap(self):
        icons = CrudViewsObjectDetailSettings().named_icons
        assert icons["boolean-true"] == "check-circle-fill"
        assert icons["boolean-false"] == "x-circle-fill"
        assert icons["property-detail"] == "info-circle"
        assert icons["text-icon"] == "journal-text"

    @override_settings(CRUD_VIEWS_OBJECT_DETAIL_ICONS_LIBRARY="fontawesome")
    def test_default_fontawesome(self):
        icons = CrudViewsObjectDetailSettings().named_icons
        assert icons["boolean-true"] == "circle-check"
        assert icons["boolean-false"] == "circle-xmark"
        assert icons["property-detail"] == "circle-info"
        assert icons["text-icon"] == "file-lines"

    @override_settings(CRUD_VIEWS_OBJECT_DETAIL_NAMED_ICONS={"boolean-true": "my-check"})
    def test_override(self):
        icons = CrudViewsObjectDetailSettings().named_icons
        assert icons == {"boolean-true": "my-check"}


# ---------------------------------------------------------------------------
# build_icon_class tests
# ---------------------------------------------------------------------------


class TestBuildIconClass:
    def test_bootstrap(self):
        assert build_icon_class("check-circle-fill") == "bi bi-check-circle-fill"

    @override_settings(CRUD_VIEWS_OBJECT_DETAIL_ICONS_LIBRARY="fontawesome")
    def test_fontawesome(self):
        assert build_icon_class("circle-check") == "fa-regular fa-circle-check"

    @override_settings(
        CRUD_VIEWS_OBJECT_DETAIL_ICONS_CLASS="icon",
        CRUD_VIEWS_OBJECT_DETAIL_ICONS_TYPE=None,
        CRUD_VIEWS_OBJECT_DETAIL_ICONS_PREFIX="icon",
    )
    def test_custom(self):
        assert build_icon_class("star") == "icon icon-star"

    @override_settings(
        CRUD_VIEWS_OBJECT_DETAIL_ICONS_CLASS="fa",
        CRUD_VIEWS_OBJECT_DETAIL_ICONS_TYPE="solid",
        CRUD_VIEWS_OBJECT_DETAIL_ICONS_PREFIX="fa",
    )
    def test_with_type(self):
        assert build_icon_class("house") == "fa-solid fa-house"


# ---------------------------------------------------------------------------
# build_named_icon_class tests
# ---------------------------------------------------------------------------


class TestBuildNamedIconClass:
    def test_bootstrap_boolean_true(self):
        assert build_named_icon_class("boolean-true") == "bi bi-check-circle-fill"

    def test_bootstrap_boolean_false(self):
        assert build_named_icon_class("boolean-false") == "bi bi-x-circle-fill"

    @override_settings(CRUD_VIEWS_OBJECT_DETAIL_ICONS_LIBRARY="fontawesome")
    def test_fontawesome_boolean_true(self):
        assert build_named_icon_class("boolean-true") == "fa-regular fa-circle-check"

    @override_settings(CRUD_VIEWS_OBJECT_DETAIL_ICONS_LIBRARY="fontawesome")
    def test_fontawesome_boolean_false(self):
        assert build_named_icon_class("boolean-false") == "fa-regular fa-circle-xmark"

    def test_unknown_name(self):
        assert build_named_icon_class("nonexistent") == ""

    @override_settings(CRUD_VIEWS_OBJECT_DETAIL_NAMED_ICONS={"boolean-true": "my-yes"})
    def test_user_override(self):
        assert build_named_icon_class("boolean-true") == "bi bi-my-yes"


# ---------------------------------------------------------------------------
# Filter tests
# ---------------------------------------------------------------------------


class TestIconClassFilter:
    def test_renders_bootstrap(self):
        tpl = Template('{% load crud_views_object_detail %}{{ "gear"|icon_class }}')
        html = tpl.render(Context())
        assert html == "bi bi-gear"

    @override_settings(CRUD_VIEWS_OBJECT_DETAIL_ICONS_LIBRARY="fontawesome")
    def test_renders_fontawesome(self):
        tpl = Template('{% load crud_views_object_detail %}{{ "gear"|icon_class }}')
        html = tpl.render(Context())
        assert html == "fa-regular fa-gear"


class TestNamedIconClassFilter:
    def test_renders_bootstrap(self):
        tpl = Template('{% load crud_views_object_detail %}{{ "boolean-true"|named_icon_class }}')
        html = tpl.render(Context())
        assert html == "bi bi-check-circle-fill"

    @override_settings(CRUD_VIEWS_OBJECT_DETAIL_ICONS_LIBRARY="fontawesome")
    def test_renders_fontawesome(self):
        tpl = Template('{% load crud_views_object_detail %}{{ "boolean-true"|named_icon_class }}')
        html = tpl.render(Context())
        assert html == "fa-regular fa-circle-check"

    def test_unknown_renders_empty(self):
        tpl = Template('{% load crud_views_object_detail %}{{ "nonexistent"|named_icon_class }}')
        html = tpl.render(Context())
        assert html == ""


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------


class TestBooleanTemplateIntegration:
    def test_bootstrap_boolean_true(self):
        prop = ResolvedProperty(path="t", label="T", value=True, type="boolean")
        tpl = Template("{% load crud_views_object_detail %}{% render_property_value prop %}")
        html = tpl.render(Context({"prop": prop}))
        assert "bi bi-check-circle-fill" in html
        assert "text-success" in html

    def test_bootstrap_boolean_false(self):
        prop = ResolvedProperty(path="t", label="T", value=False, type="boolean")
        tpl = Template("{% load crud_views_object_detail %}{% render_property_value prop %}")
        html = tpl.render(Context({"prop": prop}))
        assert "bi bi-x-circle-fill" in html
        assert "text-danger" in html

    @override_settings(CRUD_VIEWS_OBJECT_DETAIL_ICONS_LIBRARY="fontawesome")
    def test_fontawesome_boolean_true(self):
        prop = ResolvedProperty(path="t", label="T", value=True, type="boolean")
        tpl = Template("{% load crud_views_object_detail %}{% render_property_value prop %}")
        html = tpl.render(Context({"prop": prop}))
        assert "fa-regular fa-circle-check" in html
        assert "text-success" in html

    @override_settings(CRUD_VIEWS_OBJECT_DETAIL_ICONS_LIBRARY="fontawesome")
    def test_fontawesome_boolean_false(self):
        prop = ResolvedProperty(path="t", label="T", value=False, type="boolean")
        tpl = Template("{% load crud_views_object_detail %}{% render_property_value prop %}")
        html = tpl.render(Context({"prop": prop}))
        assert "fa-regular fa-circle-xmark" in html
        assert "text-danger" in html


class TestGroupIconIntegration:
    def test_bootstrap_group_icon(self):
        group = ResolvedGroup(title="Test", properties=[], icon="gear")
        tpl = Template("{% load crud_views_object_detail %}{% render_group group %}")
        html = tpl.render(Context({"group": group}))
        assert "bi bi-gear" in html

    @override_settings(CRUD_VIEWS_OBJECT_DETAIL_ICONS_LIBRARY="fontawesome")
    def test_fontawesome_group_icon(self):
        group = ResolvedGroup(title="Test", properties=[], icon="gear")
        tpl = Template("{% load crud_views_object_detail %}{% render_group group %}")
        html = tpl.render(Context({"group": group}))
        assert "fa-regular fa-gear" in html

    def test_no_icon(self):
        group = ResolvedGroup(title="Test", properties=[])
        tpl = Template("{% load crud_views_object_detail %}{% render_group group %}")
        html = tpl.render(Context({"group": group}))
        assert "bi bi-" not in html
