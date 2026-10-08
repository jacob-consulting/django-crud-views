import json
from io import StringIO

from django.core.management import call_command


def _run(*args) -> str:
    out = StringIO()
    call_command("cv_assets", *args, stdout=out)
    return out.getvalue()


def test_table_lists_core_and_registered(asset_registry, pipeline_setting):
    pipeline_setting({})
    asset_registry.register_assets(key="dtp", js=["https://cdn.example.com/dtp.js", "dtp/init.js"])
    lines = _run().splitlines()
    assert lines[0].split() == ["KEY", "KIND", "DELIVERY", "PATH"]
    assert lines[1].split() == ["crud_views", "js", "tag", "crud_views/js/viewset.js"]
    assert any(
        line.split()[:2] == ["dtp", "js"] and "tag (CDN)" in line and "cdn.example.com" in line for line in lines
    )
    assert len(lines) == 1 + 9 + 2


def test_external_filter(asset_registry, pipeline_setting):
    pipeline_setting({})
    asset_registry.register_assets(key="dtp", js=["https://cdn.example.com/dtp.js", "dtp/init.js"])
    lines = _run("--external").splitlines()
    assert len(lines) == 2
    assert "https://cdn.example.com/dtp.js" in lines[1]


def test_kind_filter(asset_registry, pipeline_setting):
    pipeline_setting({})
    lines = _run("--kind", "css").splitlines()
    assert len(lines) == 1 + 3
    assert all(line.split()[1] == "css" for line in lines[1:])


def test_integrity_shown(asset_registry, pipeline_setting):
    from crud_views.lib.assets import Asset

    pipeline_setting({})
    asset_registry.register_assets(key="cdn", js=[Asset(path="https://cdn.example.com/x.js", integrity="sha384-abc")])
    assert "[sha384-abc]" in _run("--external")


def test_json_format(asset_registry, bundled, pipeline_setting):
    from crud_views.lib.pipeline import cv_sources

    asset_registry.register_assets(key="dtp", js=["https://cdn.example.com/dtp.js", "dtp/init.js"])
    pipeline_setting({"JAVASCRIPT": {"main": {"source_filenames": cv_sources("js")}}})
    data = json.loads(_run("--format", "json", "--kind", "js"))
    by_path = {item["path"]: item for item in data}
    assert set(data[0]) == {"key", "kind", "path", "external", "integrity", "crossorigin", "emit", "delivery"}
    assert by_path["dtp/init.js"]["delivery"] == ["pipeline:main"]
    assert by_path["https://cdn.example.com/dtp.js"] == {
        "key": "dtp",
        "kind": "js",
        "path": "https://cdn.example.com/dtp.js",
        "external": True,
        "integrity": None,
        "crossorigin": None,
        "emit": True,
        "delivery": ["tag (CDN)"],
    }


def test_empty_selection_prints_header_only(asset_registry, pipeline_setting):
    pipeline_setting({})
    # no rows: each column is as wide as its header cell, columns joined by two spaces
    assert _run("--external").splitlines() == ["KEY  KIND  DELIVERY  PATH"]
