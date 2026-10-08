from pathlib import Path

import pytest

pytest.importorskip("pipeline.packager")

CORE_JS = [
    "crud_views/js/viewset.js",
    "crud_views/js/formset.js",
    "crud_views/js/list.filter.js",
    "crud_views/js/modal.js",
    "crud_views/js/toggle.js",
    "crud_views/js/tooltip.js",
]


@pytest.fixture
def noop_compressors(monkeypatch):
    """Pipeline's default compressor (yuglify) needs a binary; patch pipeline.conf without setting_changed."""
    from pipeline.conf import settings as pipeline_settings

    monkeypatch.setitem(pipeline_settings, "JS_COMPRESSOR", "pipeline.compressors.NoopCompressor")
    monkeypatch.setitem(pipeline_settings, "CSS_COMPRESSOR", "pipeline.compressors.NoopCompressor")
    monkeypatch.setitem(pipeline_settings, "DISABLE_WRAPPER", True)


@pytest.fixture
def finder_storage(monkeypatch):
    """Pipeline's compressor reads sources via the global staticfiles_storage (needs STATIC_ROOT); read via finders."""
    from django.contrib.staticfiles import finders
    from django.core.files.base import File

    class FinderStorage:
        def open(self, name, mode="rb"):
            return File(open(finders.find(name), mode))

    monkeypatch.setattr("pipeline.compressors.staticfiles_storage", FinderStorage())


def _js_packages():
    from crud_views.lib.pipeline import cv_sources

    return {
        "main": {
            "source_filenames": cv_sources("js", after=["pipeline_test/app.js"]),
            "output_filename": "out/main.js",
        }
    }


def test_package_sources_resolve_from_registry(asset_registry):
    from pipeline.packager import Packager

    asset_registry.register_assets(key="extra", js=["pipeline_test/extra.js", "https://cdn.example.com/x.js"])
    package = Packager(js_packages=_js_packages(), css_packages={}).package_for("js", "main")
    assert package.sources == [*CORE_JS, "pipeline_test/extra.js", "pipeline_test/app.js"]


def test_pack_concatenates_in_registry_order(asset_registry, noop_compressors, finder_storage, tmp_path):
    from django.contrib.staticfiles import finders
    from django.core.files.storage import FileSystemStorage
    from pipeline.packager import Packager

    asset_registry.register_assets(key="extra", js=["pipeline_test/extra.js", "https://cdn.example.com/x.js"])
    storage = FileSystemStorage(location=str(tmp_path), base_url="/static/")
    packager = Packager(storage=storage, js_packages=_js_packages(), css_packages={})
    packager.pack_javascripts(packager.package_for("js", "main"))

    output = (tmp_path / "out" / "main.js").read_text()
    expected = [*CORE_JS, "pipeline_test/extra.js", "pipeline_test/app.js"]
    positions = [output.index(Path(finders.find(path)).read_text()[:60]) for path in expected]
    assert positions == sorted(positions)
    assert "cdn.example.com" not in output
