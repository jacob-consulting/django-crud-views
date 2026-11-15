"""Execute nox's wiring with a recording session; never install or launch nox."""

import runpy
import sys
import sysconfig
from contextlib import suppress
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]


class SkippedSession(Exception):
    pass


def session_calls(monkeypatch, *, python="3.12", django="5.2", posargs=()):
    def identity(function):
        return function

    monkeypatch.setitem(
        sys.modules, "nox", SimpleNamespace(session=lambda **kwargs: identity, parametrize=lambda *args: identity)
    )
    namespace = runpy.run_path(str(ROOT / "noxfile.py"))
    calls = []

    def record(kind):
        def invoke(*args, **kwargs):
            calls.append((kind, args, deepcopy(kwargs)))
            if kind == "skip":
                raise SkippedSession

        return invoke

    session = SimpleNamespace(
        python=python, posargs=posargs, install=record("install"), run=record("run"), skip=record("skip")
    )
    with suppress(SkippedSession):
        namespace["tests"](session, django)
    return calls


def assert_suite_contract(calls, *, python, django, posargs):
    assert [kind for kind, _, _ in calls] == ["install", "install", "run", "run", "run"]
    assert calls[0][1:] == ((f"django~={django}.0",), {})
    assert calls[1][1:] == ((".[polymorphic,workflow,ordered,test]",), {})
    _, probe, probe_options = calls[2]
    _, normal, normal_options = calls[3]
    _, recorded, recorded_options = calls[4]
    assert probe[:2] == ("python", "-c") and len(probe) == 3
    assert probe_options == {"env": {"PYTHONPATH": "", "CV_ACCESS_RECORD_REQUESTS": "0"}}
    assert normal_options == probe_options
    assert recorded_options == {"env": {"PYTHONPATH": "", "CV_ACCESS_RECORD_REQUESTS": "1"}}
    assert normal == (
        "pytest",
        "tests",
        "-n",
        "auto",
        "--cov",
        "--cov-report=term-missing",
        f"--cov-report=xml:coverage-py{python}-dj{django}.xml",
        *posargs,
    )
    assert recorded == ("pytest", "tests", "-n", "auto", "--no-cov", *posargs)


@pytest.mark.parametrize("python", ["3.12", "3.13", "3.14", "3.15"])
@pytest.mark.parametrize("django", ["4.2", "5.2", "6.0"])
def test_nox_complete_off_on_runs_same_installed_origin(monkeypatch, python, django):
    # Neither an inherited source override nor inherited recording may leak into the normal run.
    monkeypatch.setenv("PYTHONPATH", "src:.")
    monkeypatch.setenv("CV_ACCESS_RECORD_REQUESTS", "1")
    posargs = ("--maxfail=3", "--durations=5")
    calls = session_calls(monkeypatch, python=python, django=django, posargs=posargs)
    if django == "4.2" and python in {"3.14", "3.15"}:
        assert calls == [("skip", (f"Django 4.2 does not support Python {python}",), {})]
    else:
        assert_suite_contract(calls, python=python, django=django, posargs=posargs)


@pytest.mark.parametrize("mutation", ["checkout", "mismatched_environment", "same_flags", "narrowed", "coverage"])
def test_wiring_assertions_reject_regressions(monkeypatch, mutation):
    calls = session_calls(monkeypatch)
    assert_suite_contract(calls, python="3.12", django="5.2", posargs=())
    if mutation == "checkout":
        for _, _, options in calls[2:]:
            options["env"]["PYTHONPATH"] = "src:."
    elif mutation == "mismatched_environment":
        calls[4][2]["env"]["OTHER_CONTEXT"] = "different"
    elif mutation == "same_flags":
        calls[3][2]["env"]["CV_ACCESS_RECORD_REQUESTS"] = "1"
    elif mutation == "narrowed":
        calls[4] = ("run", ("pytest", "tests/test1/test_access_trace.py", "-n", "auto", "--no-cov"), calls[4][2])
    else:
        calls[4] = ("run", ("pytest", "tests", "-n", "auto", "--cov"), calls[4][2])
    with pytest.raises(AssertionError):
        assert_suite_contract(calls, python="3.12", django="5.2", posargs=())


@pytest.mark.parametrize("location", ["purelib", "platlib", "checkout", "sibling", "elsewhere"])
def test_installed_origin_probe_checks_real_path_boundaries(monkeypatch, tmp_path, capsys, location):
    calls = session_calls(monkeypatch)
    assert_suite_contract(calls, python="3.12", django="5.2", posargs=())
    purelib, platlib = tmp_path / "purelib", tmp_path / "platlib"
    roots = {
        "purelib": purelib,
        "platlib": platlib,
        "checkout": ROOT / "src",
        "sibling": tmp_path / "purelib-neighbor",
        "elsewhere": tmp_path / "unrelated",
    }
    origin = roots[location] / "crud_views" / "__init__.py"
    monkeypatch.setitem(sys.modules, "crud_views", SimpleNamespace(__file__=str(origin)))
    monkeypatch.setattr(sysconfig, "get_paths", lambda: {"purelib": str(purelib), "platlib": str(platlib)})
    probe = calls[2][1][2]
    if location in {"purelib", "platlib"}:
        exec(probe, {})
        assert str(origin) in capsys.readouterr().out
    else:
        with pytest.raises(AssertionError):
            exec(probe, {})


def test_workflow_labels_both_runs_and_preserves_coverage_accounting():
    workflow = (ROOT / ".github/workflows/tests.yml").read_text()
    assert "name: Full suite (recorder off and on)" in workflow
    assert "\"tests-${{ matrix.python-version }}(django='4.2')\"" in workflow
    assert "\"tests-${{ matrix.python-version }}(django='5.2')\"" in workflow
    assert "\"tests-${{ matrix.python-version }}(django='6.0')\"" in workflow
    assert "\"examples-${{ matrix.python-version }}(django='6.0')\"" in workflow
    assert "ls coverage-py*.xml" in workflow
    assert "files: ${{ steps.coverage-files.outputs.files }}" in workflow
    assert "disable_search: true" in workflow
    assert "flags: py${{ matrix.python-version }}" in workflow
    config = (ROOT / "pyproject.toml").read_text()
    assert "[tool.coverage.paths]" in config
    assert '"*/site-packages"' in config
