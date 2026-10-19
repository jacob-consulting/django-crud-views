import pytest
from django.test import override_settings
from django.utils.html import format_html

from crud_views.lib import icons as icons_module
from crud_views.lib.icons import (
    BOOTSTRAP_ICONS,
    DEFAULT_ICONS,
    get_icons,
    register_icon_library,
    register_icons,
    render_icon,
    reset_icon_cache,
    resolve_icon,
)


def xy_renderer(name, *, css, config):
    return format_html('<svg data-icon="{}" class="{}"></svg>', name, css)


@pytest.fixture(autouse=True)
def _isolate_registry():
    icons_snapshot = dict(icons_module._THEME_ICONS)
    libs_snapshot = dict(icons_module._THEME_LIBRARIES)
    reset_icon_cache()
    yield
    icons_module._THEME_ICONS.clear()
    icons_module._THEME_ICONS.update(icons_snapshot)
    icons_module._THEME_LIBRARIES.clear()
    icons_module._THEME_LIBRARIES.update(libs_snapshot)
    reset_icon_cache()


def test_default_semantic_name_renders_font_awesome():
    assert render_icon("detail") == '<i class="fa-regular fa-eye" aria-hidden="true"></i>'


def test_prefixed_value_and_extra_css():
    assert render_icon("bi:person", css="me-2") == '<i class="bi bi-person me-2" aria-hidden="true"></i>'


def test_raw_class_fallback():
    assert render_icon("fa-solid fa-truck") == '<i class="fa-solid fa-truck" aria-hidden="true"></i>'


@pytest.mark.parametrize("value", [None, ""])
def test_empty_renders_nothing(value):
    assert render_icon(value) == ""


def test_unknown_prefix_renders_nothing():
    assert render_icon("xy:rocket") == ""


def test_escaping():
    out = render_icon('bi:x"><script>', css='"><b>')
    assert "<script>" not in out and "<b>" not in out


def test_resolve_splits_on_first_colon_only():
    assert resolve_icon("xy:a:b") == ("xy", "a:b")


def test_one_lookup_step_only():
    with override_settings(CRUD_VIEWS_ICONS={"alias": "detail"}):
        assert resolve_icon("alias") == ("", "detail")


def test_precedence_package_theme_project():
    register_icons({"detail": "bi:eye", "update": "bi:pencil"})
    with override_settings(CRUD_VIEWS_ICONS={"detail": "fas:magnifying-glass", "person": "far:user"}):
        icons = get_icons()
        assert icons["detail"] == "fas:magnifying-glass"
        assert icons["update"] == "bi:pencil"
        assert icons["delete"] == "far:trash-can"
        assert icons["person"] == "far:user"


def test_override_settings_refreshes_cache():
    assert get_icons()["detail"] == "far:eye"
    with override_settings(CRUD_VIEWS_ICONS={"detail": "bi:eye"}):
        assert get_icons()["detail"] == "bi:eye"
    assert get_icons()["detail"] == "far:eye"


def test_library_entry_replaced_whole():
    with override_settings(CRUD_VIEWS_ICON_LIBRARIES={"far": {"renderer": "font", "class": "x-{name}"}}):
        assert render_icon("far:eye") == '<i class="x-eye" aria-hidden="true"></i>'


def test_custom_renderer_dotted_path():
    with override_settings(
        CRUD_VIEWS_ICON_LIBRARIES={"xy": {"renderer": "tests.test1.test_icons_registry.xy_renderer"}}
    ):
        assert render_icon("xy:rocket", css="big") == '<svg data-icon="rocket" class="big"></svg>'


def test_theme_library_registration():
    register_icon_library("tb", renderer="font", **{"class": "ti ti-{name}"})
    assert render_icon("tb:eye") == '<i class="ti ti-eye" aria-hidden="true"></i>'


def test_bootstrap_preset_covers_exactly_default_names():
    assert BOOTSTRAP_ICONS.keys() == DEFAULT_ICONS.keys()
    assert all(v.startswith("bi:") for v in BOOTSTRAP_ICONS.values())


def test_defaults_are_font_awesome_only():
    assert all(v.split(":", 1)[0] in ("far", "fas") for v in DEFAULT_ICONS.values())


def test_font_library_without_class_renders_empty():
    with override_settings(CRUD_VIEWS_ICON_LIBRARIES={"xy": {"renderer": "font"}}):
        assert render_icon("xy:rocket") == ""


def test_none_settings_do_not_raise():
    with override_settings(CRUD_VIEWS_ICONS=None, CRUD_VIEWS_ICON_LIBRARIES=None):
        assert render_icon("detail") == '<i class="fa-regular fa-eye" aria-hidden="true"></i>'


def test_failing_dotted_renderer_import_renders_empty():
    with override_settings(CRUD_VIEWS_ICON_LIBRARIES={"xy": {"renderer": "no.such.module.render"}}):
        assert render_icon("xy:rocket") == ""


def test_dotted_renderer_imported_once(monkeypatch):
    calls = []
    real = icons_module.import_string

    def counting(path):
        calls.append(path)
        return real(path)

    monkeypatch.setattr(icons_module, "import_string", counting)
    with override_settings(
        CRUD_VIEWS_ICON_LIBRARIES={"xy": {"renderer": "tests.test1.test_icons_registry.xy_renderer"}}
    ):
        render_icon("xy:a")
        render_icon("xy:b")
    assert calls.count("tests.test1.test_icons_registry.xy_renderer") == 1


def test_get_icons_never_returns_none_on_concurrent_reset(monkeypatch):
    real = icons_module.DEFAULT_ICONS

    class Resetting(dict):
        def __iter__(self):
            icons_module.reset_icon_cache()
            return super().__iter__()

    monkeypatch.setattr(icons_module, "DEFAULT_ICONS", Resetting(real))
    icons_module.reset_icon_cache()
    assert icons_module.get_icons() is not None
    icons_module.reset_icon_cache()
    assert icons_module.get_libraries() is not None


@pytest.mark.parametrize("value", [None, "", "  "])
def test_table_value_blank_renders_nothing(value):
    with override_settings(CRUD_VIEWS_ICONS={"field-marker": value}):
        assert render_icon("field-marker", css="cv-icon-fw") == ""


@pytest.mark.parametrize("value", [5, ("xy:eye",), object()])
def test_non_str_value_renders_nothing(value):
    assert render_icon(value) == ""


def test_non_str_table_value_renders_nothing():
    with override_settings(CRUD_VIEWS_ICONS={"detail": 5}):
        assert render_icon("detail") == ""
