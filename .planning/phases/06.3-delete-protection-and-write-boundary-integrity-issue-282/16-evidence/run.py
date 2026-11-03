"""Capture completed, source-bound plan-16 gates using cached runtimes only."""

import argparse
import datetime
import hashlib
import importlib.metadata
import importlib.util
import json
import os
import platform
import shlex
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SERIES = {
    "4.2": ".nox/crispy_floor-3-12-django-4-2/bin/python",
    "5.2": ".nox/tests-3-12-django-5-2/bin/python",
    "6.0": ".nox/crispy_floor-3-12-django-6-0/bin/python",
}
RETAINED = [
    "test_delete_inspection.py",
    "test_delete_provenance.py",
    "test_delete_databases.py",
    "test_delete_migration_docs.py",
    "test_delete.py",
    "test_guardian_delete.py",
    "test_guardian.py",
    "test_guardian_inactive.py",
    "test_polymorphic.py",
    "test_transactions.py",
    "test_authorization_matrix.py",
    "test_authorization_templates.py",
    "test_guardian_policy.py",
]
REPAIRS = ["test_delete_join_identity.py", "test_guardian_content_types.py", "test_guardian_content_type_docs.py"]
GOLDEN = "tests/test1/test_form_buttons_golden.py::test_filter_form_baseline"
CSP = "tests/test1/test_assets.py::test_django6_builtin_csp_nonce_roundtrip"
QUALITY = {
    "javascript": ["bash", ".planning/phases/06-form-button-leaf/06-js-verify.sh"],
    "strict-docs": [".venv/bin/mkdocs", "build", "--strict"],
    "ruff-check": [".venv/bin/ruff", "check", "src", "tests"],
    "ruff-format": [".venv/bin/ruff", "format", "--check", "src", "tests"],
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT).decode().strip()


def source():
    paths = [
        path
        for directory in ("src", "tests", "docs")
        for path in (ROOT / directory).rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    ]
    paths += [
        ROOT / name
        for name in (
            "CHANGELOG.md",
            "pyproject.toml",
            "noxfile.py",
            "package.json",
            "package-lock.json",
            "vitest.config.js",
            "mkdocs.yml",
        )
    ]
    paths += [
        ROOT / ".planning/phases/06-form-button-leaf" / name for name in ("06-js-verify.sh", "06-JS-RUNTIME.json")
    ]
    files = {str(path.relative_to(ROOT)): sha(path) for path in sorted(paths)}
    return {"files": files, "sha256": hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()}


def runtime():
    import django
    import django.db.models.deletion as deletion

    packages = {}
    for name in (
        "crud_views",
        "crud_views_object_detail",
        "crud_views_workflow",
        "crud_views_polymorphic",
        "crud_views_guardian",
    ):
        path = Path(importlib.util.find_spec(name).origin).resolve()
        assert path == ROOT / "src" / name / "__init__.py", (name, path)
        packages[name] = {"path": str(path), "sha256": sha(path)}
    imports = {}
    for name, module in list(sys.modules.items()):
        filename = getattr(module, "__file__", None)
        if filename and name.startswith(tuple(packages)):
            path = Path(filename).resolve()
            assert path.is_relative_to(ROOT / "src"), (name, path)
            imports[name] = {"path": str(path), "sha256": sha(path)}
    return {
        "executable": sys.executable,
        "python": platform.python_version(),
        "django": django.get_version(),
        "packages": packages,
        "imports": imports,
        "django_deletion_sha256": sha(deletion.__file__),
        "versions": {
            name: importlib.metadata.version(name)
            for name in (
                "django",
                "django-guardian",
                "django-polymorphic",
                "django-ordered-model",
                "django-crispy-forms",
                "crispy-bootstrap5",
                "pytest",
                "pytest-django",
                "pydantic",
            )
        },
    }


class Capture:
    def __init__(self):
        self.nodes = []
        self.deselected = []
        self.outcomes = []

    def pytest_collection_finish(self, session):
        self.nodes = [item.nodeid for item in session.items]

    def pytest_deselected(self, items):
        self.deselected.extend(item.nodeid for item in items)

    def pytest_runtest_logreport(self, report):
        if report.when == "call" or report.failed or report.skipped:
            self.outcomes.append(
                {
                    "node": report.nodeid,
                    "when": report.when,
                    "outcome": report.outcome,
                    "xfail": getattr(report, "wasxfail", None),
                    "reason": str(report.longrepr) if report.skipped or report.failed else None,
                }
            )


def pytest_process(argv):
    import pytest

    destination, *arguments = argv
    capture = Capture()
    code = pytest.main(arguments, plugins=[capture])
    write_json(
        destination,
        {
            "exit_code": int(code),
            "nodes": capture.nodes,
            "deselected": capture.deselected,
            "outcomes": capture.outcomes,
            "runtime": runtime(),
        },
    )
    return int(code)


def recipes(group, series):
    if group == "quality":
        return [(name, argv, None) for name, argv in QUALITY.items()]
    prefix = "django" + series.replace(".", "")
    base = ["-q", "-p", "no:cacheprovider", "-ra"]

    def paths(names):
        return ["tests/test1/" + name for name in names]

    if group == "focused":
        return [
            (prefix + "-collect", [*paths(REPAIRS + RETAINED), "--collect-only", *base], "collect"),
            (prefix + "-repairs", [*paths(REPAIRS), *base], "test"),
            (prefix + "-retained", [*paths(RETAINED), *base], "test"),
        ]
    excluded = ["--deselect", GOLDEN] if series in ("4.2", "6.0") else []
    return [(prefix + "-full", ["tests/test1", *excluded, *base], "test")]


def execute(label, argv, kind, series):
    before = source()
    manifest = HERE / "source-manifest.json"
    if manifest.exists():
        assert json.loads(manifest.read_text()) == before, (
            "source changed; retain evidence and reconcile before rerunning"
        )
    else:
        write_json(manifest, before)
    for suffix in ("json", "log", "xml", "nodes.json"):
        assert not (HERE / f"{label}.{suffix}").exists(), f"refusing to overwrite {label}.{suffix}"
    environment = dict(os.environ, PYTHONPATH=str(ROOT / "src") + os.pathsep + str(ROOT), PYTHONDONTWRITEBYTECODE="1")
    command = argv
    if kind:
        if kind == "test":
            argv = [*argv, "--junitxml=" + str(HERE / f"{label}.xml")]
        command = [
            SERIES[series],
            str(Path(__file__).relative_to(ROOT)),
            "_pytest",
            str(HERE / f"{label}.nodes.json"),
            *argv,
        ]
    record = {
        "label": label,
        "series": series,
        "kind": kind,
        "status": "running",
        "head": git("rev-parse", "HEAD"),
        "source_sha256": before["sha256"],
        "tracked_diff_sha256": hashlib.sha256(
            subprocess.check_output(["git", "diff", "HEAD", "--binary"], cwd=ROOT)
        ).hexdigest(),
        "argv": command,
        "command": shlex.join(command),
        "pytest_argv": argv if kind else None,
        "environment": {name: environment[name] for name in ("PYTHONPATH", "PYTHONDONTWRITEBYTECODE")},
        "started": datetime.datetime.now(datetime.UTC).isoformat(),
        "tools": {name: sha(HERE / name) for name in ("run.py", "check.py")},
    }
    write_json(HERE / f"{label}.json", record)
    print(f"START {label}: {record['command']}", flush=True)
    start = time.monotonic()
    with (HERE / f"{label}.log").open("w") as log:
        process = subprocess.Popen(command, cwd=ROOT, env=environment, stdout=log, stderr=subprocess.STDOUT)
        record["pid"] = process.pid
        write_json(HERE / f"{label}.json", record)
        code = process.wait()
    record.update(
        exit_code=code,
        duration_seconds=round(time.monotonic() - start, 3),
        finished=datetime.datetime.now(datetime.UTC).isoformat(),
        status="complete",
        source_after_sha256=source()["sha256"],
    )
    record["artifacts"] = {
        suffix: sha(HERE / f"{label}.{suffix}")
        for suffix in ("log", "xml", "nodes.json")
        if (HERE / f"{label}.{suffix}").exists()
    }
    write_json(HERE / f"{label}.json", record)
    print(f"END {label}: exit={code}; seconds={record['duration_seconds']}", flush=True)
    assert record["source_after_sha256"] == record["source_sha256"], "source changed during gate"
    return code


def main():
    assert git("rev-parse", "--show-toplevel") == str(ROOT)
    if sys.argv[1:2] == ["_pytest"]:
        return pytest_process(sys.argv[2:])
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("group", choices=("focused", "full", "quality"))
    parser.add_argument("--series", choices=SERIES)
    args = parser.parse_args()
    if args.group != "quality" and args.series is None:
        parser.error("focused/full require --series")
    for label, argv, kind in recipes(args.group, args.series):
        code = execute(label, argv, kind, args.series)
        if code:
            return code
    return 0


if __name__ == "__main__":
    sys.exit(main())
