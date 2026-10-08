def _ids(messages):
    return [m.id for m in messages]


def _check():
    from crud_views.checks import check_asset_pipeline

    return check_asset_pipeline()


def test_no_pipeline_not_bundled_is_clean(asset_registry, pipeline_setting):
    pipeline_setting({})
    assert _check() == []


def test_w340_bundled_without_cv_sources(asset_registry, bundled, pipeline_setting):
    pipeline_setting({"JAVASCRIPT": {"main": {"source_filenames": ["js/app.js"]}}})
    assert _ids(_check()) == ["crud_views.W340"]


def test_w341_gap(asset_registry, bundled, pipeline_setting):
    from crud_views.lib.pipeline import cv_sources

    asset_registry.register_assets(key="dtp", js=["dtp/init.js"])
    pipeline_setting(
        {
            "JAVASCRIPT": {"main": {"source_filenames": cv_sources("js", exclude=["dtp"])}},
            "STYLESHEETS": {"main": {"source_filenames": cv_sources("css")}},
        }
    )
    messages = _check()
    assert _ids(messages) == ["crud_views.W341"]
    assert "dtp/init.js" in messages[0].msg
    assert "'dtp'" in messages[0].msg


def test_w341_clean_when_fully_covered(asset_registry, bundled, pipeline_setting):
    from crud_views.lib.pipeline import cv_sources

    pipeline_setting(
        {
            "JAVASCRIPT": {"main": {"source_filenames": cv_sources("js")}},
            "STYLESHEETS": {"main": {"source_filenames": cv_sources("css")}},
        }
    )
    assert _check() == []


def test_w342_double_load(asset_registry, pipeline_setting):
    from crud_views.lib.pipeline import cv_sources

    pipeline_setting({"JAVASCRIPT": {"main": {"source_filenames": cv_sources("js")}}})
    assert _ids(_check()) == ["crud_views.W342"]


def test_w342_not_for_emit_false_only(asset_registry, pipeline_setting):
    from crud_views.lib.pipeline import cv_sources

    asset_registry.register_assets(key="hidden", js=["h/x.js"], emit=False)
    pipeline_setting({"JAVASCRIPT": {"main": {"source_filenames": cv_sources("js", keys=["hidden"])}}})
    assert _check() == []


def test_w343_unknown_keys(asset_registry, pipeline_setting):
    from crud_views.lib.pipeline import cv_sources

    asset_registry.register_assets(key="hidden", js=["h/x.js"], emit=False)
    pipeline_setting(
        {"JAVASCRIPT": {"main": {"source_filenames": cv_sources("js", keys=["hidden", "typo"], exclude=["gone"])}}}
    )
    messages = _check()
    assert _ids(messages) == ["crud_views.W343", "crud_views.W343"]
    assert "'typo'" in messages[0].msg
    assert "'gone'" in messages[1].msg


def test_w344_kind_mismatch(asset_registry, pipeline_setting):
    from crud_views.lib.pipeline import cv_sources

    pipeline_setting({"JAVASCRIPT": {"main": {"source_filenames": cv_sources("css", keys=[])}}})
    assert _ids(_check()) == ["crud_views.W344"]


def test_w345_mixed_bundle(asset_registry, bundled, pipeline_setting):
    from crud_views.lib.pipeline import cv_sources

    asset_registry.register_assets(key="dtp", js=["https://cdn.example.com/dtp.js", "dtp/init.js"])
    asset_registry.register_assets(key="cdnonly", js=["https://cdn.example.com/only.js"])
    pipeline_setting(
        {
            "JAVASCRIPT": {"main": {"source_filenames": cv_sources("js")}},
            "STYLESHEETS": {"main": {"source_filenames": cv_sources("css")}},
        }
    )
    messages = _check()
    assert _ids(messages) == ["crud_views.W345"]
    assert "'dtp'" in messages[0].msg
    assert "cv_assets --external" in messages[0].hint


def test_w345_not_without_bundled_mode(asset_registry, pipeline_setting):
    asset_registry.register_assets(key="dtp", js=["https://cdn.example.com/dtp.js", "dtp/init.js"])
    pipeline_setting({})
    assert _check() == []


def test_check_registered_under_crud_views_tag():
    from django.core.checks import registry

    from crud_views.checks import check_asset_pipeline

    assert check_asset_pipeline in registry.registry.get_checks()
    assert "crud_views" in check_asset_pipeline.tags
