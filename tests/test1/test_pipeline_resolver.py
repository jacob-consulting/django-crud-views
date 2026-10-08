from pathlib import Path

import pytest

CORE_JS = [
    "crud_views/js/viewset.js",
    "crud_views/js/formset.js",
    "crud_views/js/list.filter.js",
    "crud_views/js/modal.js",
    "crud_views/js/toggle.js",
    "crud_views/js/tooltip.js",
]


def _rows(conf=None, kind="js"):
    from crud_views.lib.pipeline import asset_rows

    return {r.path: r for r in asset_rows(conf) if r.kind == kind}


def test_pipeline_setting_fixture_sends_no_signal(pipeline_setting):
    from django.conf import settings
    from django.test.signals import setting_changed

    calls = []

    def receiver(**kwargs):
        calls.append(kwargs)

    setting_changed.connect(receiver)
    try:
        pipeline_setting({"JAVASCRIPT": {}})
        assert settings.PIPELINE == {"JAVASCRIPT": {}}
    finally:
        setting_changed.disconnect(receiver)
    assert calls == []


def test_pipeline_sources_walks_sections(pipeline_setting):
    from crud_views.lib.pipeline import PipelineSource, cv_sources, pipeline_sources

    js = cv_sources("js")
    pipeline_setting(
        {
            "JAVASCRIPT": {"main": {"source_filenames": js, "output_filename": "m.js"}},
            "STYLESHEETS": {"main": {"source_filenames": ("css/a.css",), "output_filename": "m.css"}},
        }
    )
    assert pipeline_sources() == [
        PipelineSource(kind="js", package="main", sources=js),
        PipelineSource(kind="css", package="main", sources=("css/a.css",)),
    ]


def test_pipeline_sources_tolerates_odd_shapes(asset_registry, pipeline_setting):
    from crud_views.lib.pipeline import asset_rows, pipeline_sources

    pipeline_setting(None)
    assert pipeline_sources() == []
    assert pipeline_sources({"JAVASCRIPT": None}) == []
    conf = {"JAVASCRIPT": {"nosrc": {"output_filename": "x.js"}, "paths": {"source_filenames": (Path("x.js"),)}}}
    assert [s.package for s in pipeline_sources(conf)] == ["nosrc", "paths"]
    assert all(r.delivery == ("tag",) for r in asset_rows(conf) if r.kind == "js")


def test_delivery_default_tags(asset_registry):
    asset_registry.register_assets(key="a", js=["a/one.js", "https://cdn.example.com/x.js"])
    asset_registry.register_assets(key="hidden", js=["h/x.js"], emit=False)
    rows = _rows({})
    assert rows["crud_views/js/viewset.js"].delivery == ("tag",)
    assert rows["a/one.js"].delivery == ("tag",)
    assert rows["https://cdn.example.com/x.js"].delivery == ("tag (CDN)",)
    assert rows["https://cdn.example.com/x.js"].external is True
    assert rows["h/x.js"].delivery == ("none (emit=False)",)
    assert rows["h/x.js"].emit is False


def test_delivery_bundled(asset_registry, bundled):
    from crud_views.lib.pipeline import cv_sources

    asset_registry.register_assets(key="a", js=["a/one.js", "https://cdn.example.com/x.js"])
    asset_registry.register_assets(key="b", js=["b/two.js"])
    conf = {
        "JAVASCRIPT": {
            "main": {"source_filenames": cv_sources("js", exclude=["b"])},
            "extra": {"source_filenames": cv_sources("js", keys=["a"])},
        }
    }
    rows = _rows(conf)
    assert rows["crud_views/js/viewset.js"].delivery == ("pipeline:main",)
    assert rows["a/one.js"].delivery == ("pipeline:main", "pipeline:extra")
    assert rows["a/one.js"].delivery_label == "pipeline:main, pipeline:extra"
    assert rows["a/one.js"].bundled is True
    assert rows["https://cdn.example.com/x.js"].delivery == ("tag (CDN)",)
    assert rows["b/two.js"].delivery == ("none",)
    assert rows["b/two.js"].bundled is False


def test_delivery_double_load_when_not_bundled(asset_registry):
    from crud_views.lib.pipeline import cv_sources

    rows = _rows({"JAVASCRIPT": {"main": {"source_filenames": cv_sources("js")}}})
    assert rows["crud_views/js/viewset.js"].delivery == ("tag", "pipeline:main")


def test_plain_string_globs_count_as_coverage(asset_registry, bundled):
    rows = _rows({"JAVASCRIPT": {"main": {"source_filenames": ["crud_views/js/*.js"]}}})
    assert all(rows[p].delivery == ("pipeline:main",) for p in CORE_JS)


def test_kind_mismatch_does_not_cover(asset_registry, bundled):
    from crud_views.lib.pipeline import cv_sources

    rows = _rows({"STYLESHEETS": {"main": {"source_filenames": cv_sources("js")}}})
    assert rows["crud_views/js/viewset.js"].delivery == ("none",)


def test_rows_order_js_then_css(asset_registry):
    from crud_views.lib.pipeline import asset_rows

    rows = asset_rows({})
    kinds = [r.kind for r in rows]
    assert kinds == ["js"] * 6 + ["css"] * 3
    assert [r.path for r in rows[:6]] == CORE_JS


@pytest.mark.parametrize(
    "conf",
    [
        {"JAVASCRIPT": {"p": {"source_filenames": None}}},
        {"JAVASCRIPT": {"p": None}},
        {"JAVASCRIPT": [1]},
    ],
)
def test_odd_pipeline_shapes_are_ignored(asset_registry, conf):
    from crud_views.lib.pipeline import asset_rows

    assert all(r.delivery == ("tag",) for r in asset_rows(conf) if r.kind == "js")


def test_bare_string_source_filenames_is_one_pattern(asset_registry, bundled):
    rows = _rows({"JAVASCRIPT": {"main": {"source_filenames": "crud_views/js/viewset.js"}}})
    assert rows["crud_views/js/viewset.js"].delivery == ("pipeline:main",)
    assert rows["crud_views/js/formset.js"].delivery == ("none",)


def test_lazy_sources_kept_unresolved(monkeypatch):
    import django.apps

    from crud_views.lib.pipeline import cv_sources, pipeline_sources

    lazy = cv_sources("css", keys=[])
    monkeypatch.setattr(django.apps.apps, "ready", False)
    result = pipeline_sources({"JAVASCRIPT": {"main": {"source_filenames": lazy}}})
    assert result[0].sources is lazy
