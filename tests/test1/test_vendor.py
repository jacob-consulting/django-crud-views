import json
from pathlib import Path

import pytest

from crud_views.lib.vendor import STAMP_NAME, VendorSpec, check_vendored, vendor


@pytest.fixture
def spec(tmp_path) -> VendorSpec:
    return VendorSpec(
        key="picker",
        version="1.2.3",
        base_url="https://cdn.example.com/pkg@{version}/build/",
        files=("plugin.js", "plugin.css"),
        target=tmp_path / "picker" / "1.2.3",
    )


def test_resolved_base_url(spec):
    assert spec.resolved_base_url == "https://cdn.example.com/pkg@1.2.3/build/"


def test_vendor_downloads_and_stamps(spec, mocker):
    fake = mocker.patch("crud_views.lib.vendor.urllib.request.urlopen")
    fake.return_value.__enter__.return_value.read.return_value = b"content"

    written = vendor(spec)

    assert [p.name for p in written] == ["plugin.js", "plugin.css"]
    assert (spec.target / "plugin.js").read_bytes() == b"content"
    fake.assert_any_call("https://cdn.example.com/pkg@1.2.3/build/plugin.js")
    stamp = json.loads((spec.target / STAMP_NAME).read_text())
    assert stamp == {"key": "picker", "version": "1.2.3"}


def test_check_missing_stamp_warns_W330(spec):
    messages = check_vendored(spec)
    assert len(messages) == 1
    assert messages[0].id == "crud_views.W330"


def test_check_version_mismatch_warns_W331(spec):
    spec.target.mkdir(parents=True)
    (spec.target / STAMP_NAME).write_text(json.dumps({"key": "picker", "version": "9.9.9"}))
    messages = check_vendored(spec)
    assert len(messages) == 1
    assert messages[0].id == "crud_views.W331"


def test_check_ok_is_silent(spec):
    spec.target.mkdir(parents=True)
    (spec.target / STAMP_NAME).write_text(json.dumps({"key": "picker", "version": "1.2.3"}))
    assert check_vendored(spec) == []
