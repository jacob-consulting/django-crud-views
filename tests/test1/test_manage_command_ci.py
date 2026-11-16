"""Exercise the floor session without installing packages or launching subprocesses."""

import importlib.metadata
import runpy
import sys
import sysconfig
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_TESTS = {
    "tests/test1/test_manage_report.py",
    "tests/test1/test_manage_command.py",
    "tests/test1/test_manage_export.py",
    "tests/test1/test_manage_preservation.py",
    "tests/test1/test_manage_command_docs.py",
    "tests/test1/test_manage_command_locales.py",
}


def floor_calls(monkeypatch, tmp_path, *, export=True):
    configurations = {}

    def session(**options):
        def decorate(function):
            configurations[function.__name__] = options
            return function

        return decorate

    monkeypatch.setitem(sys.modules, "nox", SimpleNamespace(session=session, parametrize=lambda *args: lambda fn: fn))
    namespace = runpy.run_path(str(ROOT / "noxfile.py"))
    assert callable(namespace.get("manage_report_floor")), "Missing executable Pydantic floor session"
    calls = []

    def record(kind):
        def invoke(*args, **kwargs):
            calls.append((kind, args, deepcopy(kwargs)))
            if kind == "error":
                raise RuntimeError(args[0])

        return invoke

    monkeypatch.setenv("PYTHONPATH", "src:.")
    monkeypatch.setenv("CV_ACCESS_RECORD_REQUESTS", "1")
    if export:
        monkeypatch.setenv("CV_MANAGE_SCHEMA_EXPORT_DIR", str(tmp_path))
    else:
        monkeypatch.delenv("CV_MANAGE_SCHEMA_EXPORT_DIR", raising=False)
    namespace["manage_report_floor"](
        SimpleNamespace(install=record("install"), run=record("run"), error=record("error"), posargs=())
    )
    return configurations, namespace, calls


def assert_floor_contract(configurations, namespace, calls, export_directory):
    assert configurations["manage_report_floor"] == {"python": "3.12", "venv_backend": "uv", "default": False}
    assert [kind for kind, _, _ in calls] == ["install", "run", "run"]
    assert calls[0][1:] == (("django~=5.2.0", ".[polymorphic,workflow,ordered,test]", "pydantic==2.2.1"), {})
    _, probe, probe_options = calls[1]
    _, suite, suite_options = calls[2]
    assert probe[:2] == ("python", "-c") and len(probe) == 3
    assert probe_options == {"env": {"PYTHONPATH": "", "CV_ACCESS_RECORD_REQUESTS": "0"}}
    assert set(namespace["MANAGE_REPORT_TESTS"]) == EXPECTED_TESTS
    assert suite == ("pytest", *namespace["MANAGE_REPORT_TESTS"], "-n", "4", "-q")
    assert suite_options == {
        "env": {
            "PYTHONPATH": "",
            "CV_ACCESS_RECORD_REQUESTS": "0",
            "CV_MANAGE_SCHEMA_EXPORT_DIR": str(export_directory),
        }
    }
    assert all((ROOT / path).is_file() for path in EXPECTED_TESTS)


def test_floor_session_pins_and_runs_installed_contract(monkeypatch, tmp_path):
    assert_floor_contract(*floor_calls(monkeypatch, tmp_path), tmp_path)


@pytest.mark.parametrize("mutation", ["split_install", "checkout", "missing_exports", "import_only", "no_probe"])
def test_floor_wiring_rejects_weakened_verification(monkeypatch, tmp_path, mutation):
    configurations, namespace, calls = floor_calls(monkeypatch, tmp_path)
    assert_floor_contract(configurations, namespace, calls, tmp_path)
    if mutation == "split_install":
        calls[0] = ("install", calls[0][1][:-1], {})
        calls.insert(1, ("install", ("pydantic==2.2.1",), {}))
    elif mutation == "checkout":
        calls[2][2]["env"]["PYTHONPATH"] = "src:."
    elif mutation == "missing_exports":
        calls[2][2]["env"].pop("CV_MANAGE_SCHEMA_EXPORT_DIR")
    elif mutation == "import_only":
        calls[2] = ("run", ("python", "-c", "import crud_views"), calls[2][2])
    else:
        calls.pop(1)
    with pytest.raises(AssertionError):
        assert_floor_contract(configurations, namespace, calls, tmp_path)


@pytest.mark.parametrize("version, location", [("2.2.1", "installed"), ("2.14.3", "installed"), ("2.2.1", "checkout")])
def test_floor_probe_checks_resolved_version_and_origin(monkeypatch, tmp_path, capsys, version, location):
    _, _, calls = floor_calls(monkeypatch, tmp_path)
    site = tmp_path / "site-packages"
    origin = (site if location == "installed" else ROOT / "src") / "crud_views/__init__.py"
    monkeypatch.setitem(sys.modules, "crud_views", SimpleNamespace(__file__=str(origin)))
    monkeypatch.setitem(sys.modules, "pydantic", SimpleNamespace(__version__=version))
    monkeypatch.setattr(sysconfig, "get_paths", lambda: {"purelib": str(site), "platlib": str(site)})
    versions = {"pydantic": version, "django": "5.2.19", "typing-extensions": "4.15.0"}
    monkeypatch.setattr(importlib.metadata, "version", versions.__getitem__)
    probe = calls[1][1][2]
    if version == "2.2.1" and location == "installed":
        exec(probe, {})
        output = capsys.readouterr().out
        assert str(origin) in output
        assert all(name in output and value in output for name, value in versions.items())
        assert "python" in output.lower()
    else:
        with pytest.raises(AssertionError):
            exec(probe, {})


def test_floor_requires_caller_supplied_export_directory(monkeypatch, tmp_path):
    with pytest.raises(RuntimeError, match="CV_MANAGE_SCHEMA_EXPORT_DIR"):
        floor_calls(monkeypatch, tmp_path, export=False)
