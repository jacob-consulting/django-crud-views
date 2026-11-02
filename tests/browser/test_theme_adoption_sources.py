"""Hermetic companion evidence tests; no production companion or Django imports."""

import importlib.util
import sys
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location("theme_adoption_sources", Path(__file__).with_name("theme_adoption_sources.py"))
sources = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = sources
SPEC.loader.exec_module(sources)


@pytest.fixture(autouse=True)
def no_companion_environment(monkeypatch):
    for key in ("CV_THEME_SOURCE", "CV_PACK_SOURCE", "CV_THEME_CORE_BASE", "CV_THEME_PYTHON", "CV_FOCUS_PYTHON"):
        monkeypatch.delenv(key, raising=False)


def test_missing_sources_fail_closed(tmp_path):
    with pytest.raises(sources.EvidenceError, match="source"):
        sources.inspect_sources(tmp_path / "absent", "abc", "https://example.invalid/theme.git")
