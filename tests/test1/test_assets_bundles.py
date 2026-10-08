import pytest
from django.core.exceptions import ImproperlyConfigured

CORE_JS = [
    "crud_views/js/viewset.js",
    "crud_views/js/formset.js",
    "crud_views/js/list.filter.js",
    "crud_views/js/modal.js",
    "crud_views/js/toggle.js",
    "crud_views/js/tooltip.js",
]
CORE_CSS = ["crud_views/css/property.css", "crud_views/css/table.css", "crud_views/css/formset.css"]


def test_core_bundle_mirrors_settings(asset_registry):
    bundle = asset_registry.core_bundle()
    assert bundle.key == "crud_views" == asset_registry.CORE_KEY
    assert [a.path for a in bundle.js] == CORE_JS
    assert [a.path for a in bundle.css] == CORE_CSS
    assert bundle.emit is True


def test_iter_bundles_core_first(asset_registry):
    asset_registry.register_assets(key="a", js=["a/one.js"])
    assert [b.key for b in asset_registry.iter_bundles()] == ["crud_views", "a"]


def test_collect_core_first_then_registration_order(asset_registry):
    asset_registry.register_assets(key="a", js=["a/one.js"])
    asset_registry.register_assets(key="b", js=["b/two.js"], css=["b/two.css"])
    entries = asset_registry.collect("js")
    assert [e.asset.path for e in entries] == [*CORE_JS, "a/one.js", "b/two.js"]
    assert [e.key for e in entries] == ["crud_views"] * 6 + ["a", "b"]
    assert [e.asset.path for e in asset_registry.collect("css")] == [*CORE_CSS, "b/two.css"]


def test_collect_emit_false(asset_registry):
    asset_registry.register_assets(key="hidden", js=["h/x.js"], emit=False)
    all_paths = [e.asset.path for e in asset_registry.collect("js")]
    emitting = [e.asset.path for e in asset_registry.collect("js", only_emitting=True)]
    assert "h/x.js" in all_paths
    assert "h/x.js" not in emitting
    assert asset_registry.collect("js")[-1].emit is False


def test_collect_invalid_kind(asset_registry):
    with pytest.raises(ValueError, match="'js' or 'css'"):
        asset_registry.collect("svg")


def test_core_key_is_reserved(asset_registry):
    with pytest.raises(ImproperlyConfigured, match="reserved"):
        asset_registry.register_assets(key="crud_views", js=["x.js"])


def test_tag_entries_default_equals_emitting_collect(asset_registry):
    asset_registry.register_assets(key="a", js=["a/one.js", "https://cdn.example.com/x.js"])
    asset_registry.register_assets(key="hidden", js=["h/x.js"], emit=False)
    paths = [e.asset.path for e in asset_registry.tag_entries("js")]
    assert paths == [*CORE_JS, "a/one.js", "https://cdn.example.com/x.js"]
