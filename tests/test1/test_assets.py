from pathlib import Path

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.template import Context, Template

import crud_views_plain


@pytest.fixture
def asset_registry():
    """Snapshot/restore the module-global registry around each test."""
    from crud_views.lib import assets

    snapshot = dict(assets._REGISTRY)
    assets._REGISTRY.clear()
    yield assets
    assets._REGISTRY.clear()
    assets._REGISTRY.update(snapshot)


def test_register_and_get(asset_registry):
    asset_registry.register_assets(key="a", js=["a/one.js"], css=["a/one.css"])
    asset_registry.register_assets(key="b", js=["b/two.js"])

    bundles = asset_registry.get_registered()
    assert [b.key for b in bundles] == ["a", "b"]  # registration order
    assert bundles[0].js == ("a/one.js",)
    assert bundles[0].css == ("a/one.css",)
    assert bundles[1].css == ()
    assert bundles[0].emit is True


def test_duplicate_key_raises(asset_registry):
    asset_registry.register_assets(key="a", js=["a/one.js"])
    with pytest.raises(ImproperlyConfigured, match="already registered"):
        asset_registry.register_assets(key="a", js=["other.js"])


def test_only_emitting_filters(asset_registry):
    asset_registry.register_assets(key="a", js=["a/one.js"], emit=False)
    asset_registry.register_assets(key="b", js=["b/two.js"])

    assert [b.key for b in asset_registry.get_registered()] == ["a", "b"]
    assert [b.key for b in asset_registry.get_registered(only_emitting=True)] == ["b"]


def test_is_external(asset_registry):
    assert asset_registry.is_external("https://cdn.example.com/x.js")
    assert asset_registry.is_external("http://cdn.example.com/x.js")
    assert asset_registry.is_external("//cdn.example.com/x.js")
    assert not asset_registry.is_external("crud_views/js/viewset.js")


def test_resolve_url(asset_registry):
    assert asset_registry.resolve_url("//cdn.example.com/x.js") == "//cdn.example.com/x.js"
    # STATIC_URL in tests/test1/conftest.py is "static/" (normalized to "/static/" by static())
    assert asset_registry.resolve_url("crud_views/js/viewset.js") == "/static/crud_views/js/viewset.js"


def _render(tag: str) -> str:
    return Template("{% load crud_views %}{% " + tag + " %}").render(Context({}))


def test_cv_js_renders_core_then_registered(asset_registry):
    asset_registry.register_assets(
        key="picker",
        js=["picker/plugin.js", "https://cdn.example.com/extra.js"],
        css=["picker/plugin.css"],
    )
    html = _render("cv_js")
    # core asset still present and resolved via static()
    assert "/static/crud_views/js/viewset.js" in html
    # registered static path resolved, external URL verbatim
    assert "/static/picker/plugin.js" in html
    assert 'src="https://cdn.example.com/extra.js"' in html
    # order: core before registered
    assert html.index("crud_views/js/viewset.js") < html.index("picker/plugin.js")


def test_cv_css_renders_registered(asset_registry):
    asset_registry.register_assets(key="picker", css=["picker/plugin.css"])
    html = _render("cv_css")
    assert "/static/crud_views/css/property.css" in html
    assert "/static/picker/plugin.css" in html
    assert html.index("property.css") < html.index("picker/plugin.css")


def test_emit_false_not_rendered(asset_registry):
    asset_registry.register_assets(key="picker", js=["picker/plugin.js"], emit=False)
    html = _render("cv_js")
    assert "picker/plugin.js" not in html


def test_empty_registry_output_unchanged(asset_registry):
    # regression guard: with nothing registered, all core assets and nothing else
    html = _render("cv_js")
    assert "/static/crud_views/js/viewset.js" in html
    assert "/static/crud_views/js/formset.js" in html
    assert "/static/crud_views/js/list.filter.js" in html
    assert "/static/crud_views/js/modal.js" in html
    assert html.count("<script") == 4


def test_plain_theme_content_templates_render_form_media():
    """Regression guard for the plain theme's widget-media bug.

    Unlike the bootstrap5 theme (whose crispy `{% crispy %}` tag auto-includes
    `{{ form.media }}`), the plain theme's `tags/form.html` renders `{{ form.as_table }}`
    with no crispy and no media anywhere. Its create/update content templates must therefore
    render `{{ form.media }}` explicitly, or widget CSS/JS is silently lost.

    This asserts the directive's presence directly in the plain templates: a behavioral
    render test cannot isolate this line in the test suite, because the active theme is
    bootstrap5 (crispy auto-includes media, contaminating any rendered output) and
    `crud_views_plain` is intentionally not in the test project's INSTALLED_APPS.

    Covers all four plain content templates that render a form via `{% cv_render_form %}`:
    create, update, custom-form, and delete.
    """
    base = Path(crud_views_plain.__file__).parent / "templates" / "crud_views"
    for name in (
        "view_create.content.html",
        "view_update.content.html",
        "view_custom_form.content.html",
        "view_delete.content.html",
    ):
        source = (base / name).read_text()
        assert "{{ form.media }}" in source, f"plain theme {name} must render {{{{ form.media }}}}"
