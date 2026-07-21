import pytest
from django.core.exceptions import ImproperlyConfigured
from django.template import Context, Template


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
    from crud_views.lib.assets import Asset

    asset_registry.register_assets(key="a", js=["a/one.js"], css=["a/one.css"])
    asset_registry.register_assets(key="b", js=["b/two.js"])

    bundles = asset_registry.get_registered()
    assert [b.key for b in bundles] == ["a", "b"]  # registration order
    assert bundles[0].js == (Asset(path="a/one.js"),)
    assert bundles[0].css == (Asset(path="a/one.css"),)
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
    assert "/static/crud_views/js/toggle.js" in html
    assert html.count("<script") == 5


def test_asset_normalization(asset_registry):
    from crud_views.lib.assets import Asset

    asset_registry.register_assets(
        key="mixed",
        js=[
            "plain/path.js",
            Asset(path="https://cdn.example.com/x.js", integrity="sha384-abc"),
        ],
        css=[Asset(path="plain/path.css")],
    )
    bundle = asset_registry.get_registered()[0]
    assert bundle.js == (
        Asset(path="plain/path.js"),
        Asset(path="https://cdn.example.com/x.js", integrity="sha384-abc"),
    )
    assert bundle.css == (Asset(path="plain/path.css"),)
    assert bundle.js[0].integrity is None
    assert bundle.js[0].crossorigin is None


def test_normalize_entries(asset_registry):
    from crud_views.lib.assets import Asset, normalize_entries

    asset = Asset(path="a.js", integrity="sha384-abc", crossorigin="anonymous")
    assert normalize_entries(["a.js", asset]) == (Asset(path="a.js"), asset)
    assert normalize_entries([]) == ()


class _FakeLazyNonce:
    """Mimics Django 6 LazyNonce: falsy until first evaluated via str()."""

    def __init__(self, value="lazy123"):
        self.value = value
        self.evaluated = False

    def __bool__(self):
        return self.evaluated

    def __str__(self):
        self.evaluated = True
        return self.value


def _request(**attrs):
    from django.test import RequestFactory

    request = RequestFactory().get("/")
    for name, value in attrs.items():
        setattr(request, name, value)
    return request


def test_resolve_nonce_absent():
    from crud_views.templatetags.crud_views import _resolve_nonce

    assert _resolve_nonce({}) is None
    assert _resolve_nonce({"request": _request()}) is None


def test_resolve_nonce_request_attr_django_csp_convention():
    from crud_views.templatetags.crud_views import _resolve_nonce

    assert _resolve_nonce({"request": _request(csp_nonce="abc123")}) == "abc123"


def test_resolve_nonce_forces_lazy_evaluation():
    # Django 6 LazyNonce is falsy until evaluated — truthiness checks would drop it.
    from crud_views.templatetags.crud_views import _resolve_nonce

    lazy = _FakeLazyNonce()
    assert _resolve_nonce({"request": _request(csp_nonce=lazy)}) == "lazy123"
    assert lazy.evaluated is True


def test_resolve_nonce_context_var_fallback():
    from crud_views.templatetags.crud_views import _resolve_nonce

    assert _resolve_nonce({"csp_nonce": _FakeLazyNonce("ctx456")}) == "ctx456"


def test_resolve_nonce_request_attr_beats_context_var():
    from crud_views.templatetags.crud_views import _resolve_nonce

    context = {"request": _request(csp_nonce="fromrequest"), "csp_nonce": "fromcontext"}
    assert _resolve_nonce(context) == "fromrequest"


def test_resolve_nonce_configurable_attr(settings):
    from crud_views.lib.settings import crud_views_settings
    from crud_views.templatetags.crud_views import _resolve_nonce

    assert crud_views_settings.csp_nonce_attr == "csp_nonce"
    original = crud_views_settings.csp_nonce_attr
    crud_views_settings.csp_nonce_attr = "my_nonce"
    try:
        assert _resolve_nonce({"request": _request(my_nonce="custom789")}) == "custom789"
    finally:
        crud_views_settings.csp_nonce_attr = original
