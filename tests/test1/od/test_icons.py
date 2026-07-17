import pytest
from django.test import override_settings

from crud_views_object_detail.lib import conf
from crud_views_object_detail.lib.conf import (
    CrudViewsObjectDetailSettings,
    build_icon_class,
    build_named_icon_class,
)


@pytest.fixture(autouse=True)
def _fresh_singleton(monkeypatch):
    """build_icon_class/build_named_icon_class read the module-level singleton, whose
    cached_property values persist across tests. Reset it before each test so
    @override_settings actually takes effect through those module functions."""
    monkeypatch.setattr(conf, "crud_views_object_detail_settings", CrudViewsObjectDetailSettings())


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
