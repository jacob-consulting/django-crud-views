import pytest
from django.core.exceptions import ImproperlyConfigured


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
