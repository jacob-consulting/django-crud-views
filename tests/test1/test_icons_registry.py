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
    resolve_icon_name_class,
)
from tests.lib.helper.icons import HOST_LIBRARY


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


def _boom(path):
    raise RuntimeError("boom")


def test_non_dict_library_renders_nothing():
    with override_settings(CRUD_VIEWS_ICON_LIBRARIES={"xy": "font"}):
        assert render_icon("xy:a") == ""


def test_non_callable_renderer_renders_nothing():
    with override_settings(CRUD_VIEWS_ICON_LIBRARIES={"xy": {"renderer": None}}):
        assert render_icon("xy:a") == ""


def test_renderer_import_raising_any_exception_renders_nothing(monkeypatch):
    monkeypatch.setattr(icons_module, "import_string", _boom)
    with override_settings(CRUD_VIEWS_ICON_LIBRARIES={"xy": {"renderer": "some.module.render"}}):
        assert render_icon("xy:a") == ""


def test_dotted_path_to_non_callable_renders_nothing():
    with override_settings(CRUD_VIEWS_ICON_LIBRARIES={"xy": {"renderer": "os.sep"}}):
        assert render_icon("xy:a") == ""


@pytest.mark.parametrize("template", ["x-{size} {name}", "x-{} {name}", 5])
def test_bad_font_class_renders_nothing(template):
    with override_settings(CRUD_VIEWS_ICON_LIBRARIES={"xy": {"renderer": "font", "class": template}}):
        assert render_icon("xy:a") == ""


@pytest.mark.parametrize("value", ["  detail ", "\tdetail\n"])
def test_surrounding_whitespace_is_ignored(value):
    assert render_icon(value) == '<i class="fa-regular fa-eye" aria-hidden="true"></i>'


def test_surrounding_whitespace_in_table_value_is_ignored():
    with override_settings(CRUD_VIEWS_ICONS={"detail": "  fas:eye "}):
        assert render_icon("detail") == '<i class="fa-solid fa-eye" aria-hidden="true"></i>'


MESSAGE_ICONS = {
    "message-success": ("fas:circle-check", "bi:check-circle-fill"),
    "message-info": ("fas:circle-info", "bi:info-circle-fill"),
    "message-warning": ("fas:triangle-exclamation", "bi:exclamation-triangle-fill"),
    "message-error": ("fas:circle-exclamation", "bi:exclamation-octagon-fill"),
    "message-debug": ("fas:bug", "bi:bug-fill"),
}


@pytest.mark.parametrize("name,fa,bi", [(name, *values) for name, values in MESSAGE_ICONS.items()])
def test_message_icon_defaults(name, fa, bi):
    assert DEFAULT_ICONS[name] == fa
    assert BOOTSTRAP_ICONS[name] == bi


# the semantic defaults of the form-button kinds (Phase 6): submit -> save, cancel, filter-reset
FORM_ICONS = {
    "save": ("far:floppy-disk", "bi:floppy"),
    "cancel": ("fas:xmark", "bi:x-lg"),
    "filter-reset": ("fas:rotate-left", "bi:arrow-counterclockwise"),
}


@pytest.mark.parametrize("name,fa,bi", [(name, *values) for name, values in FORM_ICONS.items()])
def test_form_icon_defaults(name, fa, bi):
    assert DEFAULT_ICONS[name] == fa
    assert BOOTSTRAP_ICONS[name] == bi


def test_form_reset_icon_is_distinct_from_the_filter_toggle():
    # filter-reset clears the filter form; filter-close is the open state of the filter panel toggle
    assert DEFAULT_ICONS["filter-reset"] != DEFAULT_ICONS["filter-close"]
    assert BOOTSTRAP_ICONS["filter-reset"] != BOOTSTRAP_ICONS["filter-close"]


def test_message_icon_renders_font_awesome_by_default():
    assert render_icon("message-success") == '<i class="fa-solid fa-circle-check" aria-hidden="true"></i>'


def test_message_icon_can_be_switched_off():
    assert "fa-circle-info" in render_icon("message-info")  # resolves through the registry, not as a raw class
    with override_settings(CRUD_VIEWS_ICONS={"message-info": ""}):
        assert render_icon("message-info") == ""


# host placement (#258)


def test_host_standalone_renders_standalone_classes():
    with override_settings(CRUD_VIEWS_ICON_LIBRARIES=HOST_LIBRARY):
        assert render_icon("ui:check") == '<i class="icon icon-check" aria-hidden="true"></i>'


def test_host_standalone_with_css():
    with override_settings(CRUD_VIEWS_ICON_LIBRARIES=HOST_LIBRARY):
        assert render_icon("ui:check", css="me-2") == '<i class="icon icon-check me-2" aria-hidden="true"></i>'


def test_host_standalone_default_is_name_class():
    libs = {"ui": {"renderer": "font", "class": "icon-{name}", "placement": "host"}}
    with override_settings(CRUD_VIEWS_ICON_LIBRARIES=libs):
        assert render_icon("ui:check") == '<i class="icon-check" aria-hidden="true"></i>'


def test_element_library_ignores_standalone():
    libs = {"ui": {"renderer": "font", "class": "icon-{name}", "standalone": "icon {name_class}"}}
    with override_settings(CRUD_VIEWS_ICON_LIBRARIES=libs):
        assert render_icon("ui:check") == '<i class="icon-check" aria-hidden="true"></i>'


def test_host_standalone_unusable_renders_nothing():
    libs = {"ui": {"renderer": "font", "class": "icon-{name}", "placement": "host", "standalone": "{oops}"}}
    with override_settings(CRUD_VIEWS_ICON_LIBRARIES=libs):
        assert render_icon("ui:check") == ""


def test_resolve_icon_name_class():
    with override_settings(CRUD_VIEWS_ICON_LIBRARIES=HOST_LIBRARY, CRUD_VIEWS_ICONS={"detail": "ui:eye"}):
        assert resolve_icon_name_class("ui:check") == "icon-check"
        assert resolve_icon_name_class("detail") == "icon-eye"
        assert resolve_icon_name_class("fas:check") is None
        assert resolve_icon_name_class("fa-solid fa-x") is None
        assert resolve_icon_name_class("zz:check") is None
        assert resolve_icon_name_class(None) is None
        assert resolve_icon_name_class("") is None


def test_resolve_icon_name_class_needs_font_renderer():
    libs = {"ui": {"renderer": "crud_views.lib.icons.font_renderer", "class": "icon-{name}", "placement": "host"}}
    with override_settings(CRUD_VIEWS_ICON_LIBRARIES=libs):
        assert resolve_icon_name_class("ui:check") is None
