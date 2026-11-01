"""Resumable, stdlib-only final verification; reuse cached runtimes without installs.

Run from any directory with --run/--check and --output. Passing gates are reused
only while their exact source manifest and command/environment contract agree.
Python subprocesses have private temporary plugins/JUnit; evidence writes are serial.
"""

import argparse
import copy
import datetime
import hashlib
import json
import math
import os
import re
import shlex
import shutil
import signal
import socket
import struct
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PHASE = HERE.parent
SERIES = {
    "4.2": ".nox/crispy_floor-3-12-django-4-2/bin/python",
    "5.2": ".nox/tests-3-12-django-5-2/bin/python",
    "6.0": ".nox/crispy_floor-3-12-django-6-0/bin/python",
}
TRACER = "tests/test1/test_conditional_layout.py::test_tracer_rendered_conditional_round_trip"
GOLDEN = "tests/test1/test_form_buttons_golden.py::test_filter_form_baseline"
CSP = "tests/test1/test_assets.py::test_django6_builtin_csp_nonce_roundtrip"
CSP_REASON = "built-in CSP middleware requires Django 6.0"
FOCUSED = [
    "tests/test1/" + name
    for name in (
        "test_conditional_group.py",
        "test_conditional_formset.py",
        "test_conditional_layout.py",
        "test_conditional_checks.py",
        "test_conditional_persistence.py",
        "test_formsets_policy.py",
        "test_formsets_validation_gate.py",
        "test_formsets_controls.py",
        "test_formsets_bugs.py",
        "test_formset_pk_boundary.py",
        "test_fragment_authorization.py",
        "test_conditional_migration_docs.py",
    )
]
ROUTES = ("focused", "enabled-full", "disabled-full", "missing-runtime")
QUALITY = ("javascript", "javascript-integration", "strict-docs", "ruff-check", "ruff-format", "evidence-self-tests")
BROWSERS = ("conditional-browser", "modal-browser")
PAYLOAD_CORRUPTIONS = (
    "exit-code",
    "required-case-list",
    "raw-balance-assertion",
    "inline-clear-assertion",
    "source-hash",
    "tracer-absent",
    "tracer-skipped",
    "tracer-failed",
    "tracer-zero-selected",
    "disabled-opt-in",
    "disabled-node-absence",
    "negative-control-setup-error",
    "js-filtered-command",
    "js-wrong-executable",
    "js-missing-file",
    "js-duplicate-file",
    "js-missing-case",
    "js-duplicate-case",
    "js-failed-case",
    "js-skipped-case",
    "js-false-counts",
    "integration-missing",
    "docs-non-strict",
    "ruff-wrong-subcommand",
    "ruff-format-missing-check",
    "capture-missing",
    "capture-digest",
    "capture-observation",
)
RECORD_CORRUPTIONS = (
    "control-missing-evidence",
    "control-missing-summary",
    "control-success-outcome",
    "control-wrong-command",
    "control-wrong-diagnostic",
)
CORRUPTIONS = PAYLOAD_CORRUPTIONS + RECORD_CORRUPTIONS
# Exact predicates, rather than any failure bearing a rejection label. Several
# mutations intentionally exercise the same predicate with different inputs.
CONTROL_DIAGNOSTICS = {
    "exit-code": "django4.2-focused: green suite failed/empty",
    "required-case-list": "Corrupted required-case list",
    "raw-balance-assertion": "Missing/false assertion fragment-raw-balance",
    "inline-clear-assertion": "Missing/false assertion inline-file-clear-unchanged",
    "source-hash": "Missing/stale source manifest",
    "tracer-absent": "django4.2-focused: required tracer missing/skipped/failed",
    "tracer-skipped": "django4.2-focused: unexpected skip/reason",
    "tracer-failed": "django4.2-focused: green suite failed/empty",
    "tracer-zero-selected": "django4.2-focused: inconsistent/empty counts",
    "disabled-opt-in": "django4.2-disabled-full: forged Node-free environment",
    "disabled-node-absence": "django4.2-disabled-full: forged Node-free environment",
    "negative-control-setup-error": "django4.2-missing-runtime: setup/collection failure is not runtime proof",
    "js-filtered-command": "javascript: wrong quality command",
    "js-wrong-executable": "javascript: wrong quality command",
    "js-missing-file": "JS missing/duplicate file",
    "js-duplicate-file": "JS missing/duplicate file",
    "js-missing-case": "JS missing/duplicate case selection",
    "js-duplicate-case": "JS missing/duplicate case selection",
    "js-failed-case": "JS failed/skipped required case",
    "js-skipped-case": "JS failed/skipped required case",
    "js-false-counts": "JS inconsistent counts",
    "integration-missing": "Missing/extra matrix gates",
    "docs-non-strict": "strict-docs: wrong quality command",
    "ruff-wrong-subcommand": "ruff-check: wrong quality command",
    "ruff-format-missing-check": "ruff-format: wrong quality command",
    "capture-missing": "Conditional capture inventory invalid: stock",
    "capture-digest": "Conditional capture digest mismatch: desktop",
    "capture-observation": "Conditional capture icon observations invalid: desktop",
    "control-missing-evidence": "Checker control evidence inventory incomplete",
    "control-missing-summary": "Checker control summary inventory incomplete",
    "control-success-outcome": "Checker control exit invalid: exit-code",
    "control-wrong-command": "Checker control command invalid: exit-code",
    "control-wrong-diagnostic": "Checker control diagnostic mismatch: exit-code",
}
RUNTIME_MANIFEST = ".planning/phases/06-form-button-leaf/06-JS-RUNTIME.json"
BASE = "74dcd53ad425d7a97a8a1249a41e23092723edfc"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def source():
    # Track declared source only: no generated caches, evidence or planning Markdown.
    paths = git("ls-files", "src", "tests", "docs", "examples").splitlines()
    paths += [
        "CHANGELOG.md",
        "README.md",
        "pyproject.toml",
        "noxfile.py",
        "package.json",
        "package-lock.json",
        "vitest.config.js",
        "vitest.integration.config.js",
        ".github/workflows/js.yml",
        str(HERE.relative_to(ROOT) / "run.py"),
        str(HERE.relative_to(ROOT) / "test_runner.py"),
        "mkdocs.yml",
        RUNTIME_MANIFEST,
        ".planning/phases/06.3-delete-protection-and-write-boundary-integrity-issue-282/17-evidence/server.py",
    ]
    files = {p: sha(ROOT / p) for p in sorted(set(paths))}
    return {"files": files, "sha256": hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()}


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def now():
    return datetime.datetime.now(datetime.UTC).isoformat()


def need(condition, message):
    if not condition:
        raise ValueError(message)


def load_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            need(key not in result, f"Duplicate JSON key: {key}")
            result[key] = value
        return result

    return json.loads(Path(path).read_text(), object_pairs_hook=unique)


def node_path():
    selected = os.environ.get("CV_FOCUS_NODE")
    if selected is None:
        selected = json.loads((ROOT / RUNTIME_MANIFEST).read_text())["node"]["path"]
    found = shutil.which(selected) if selected else None
    need(found, f"Selected Node unavailable: {selected!r}")
    return str(Path(found).resolve())


def touched_python():
    paths = git("diff", "--name-only", BASE, "--", "src", "tests", "examples").splitlines()
    return sorted(
        set(
            [p for p in paths if p.endswith(".py")]
            + [str(HERE.relative_to(ROOT) / n) for n in ("run.py", "test_runner.py")]
        )
    )


def expected_ids():
    return [f"django{series}-{route}" for series in SERIES for route in ROUTES] + list(QUALITY + BROWSERS)


def overrides():
    return {
        key: value
        for key, value in os.environ.items()
        if key.startswith("CV_FOCUS_") or key in ("CV_CONDITIONAL_PORT", "CV_FRAGMENT_PYTHON")
    }


def selected_path(variable, default, executable=True):
    raw = os.environ.get(variable, default)
    found = shutil.which(raw) if raw else None
    if not executable:
        found = raw if raw and Path(raw).is_dir() else None
    need(found, f"{variable}={raw!r}: selected runtime unavailable")
    path = os.path.abspath(found)
    need(not executable or os.access(path, os.X_OK), f"{variable}={raw!r}: selected path is not executable")
    return path if "PYTHON" in variable or variable.startswith("Django") else str(Path(path).resolve())


def runtime_probe(variable, path, argv, env):
    try:
        result = subprocess.run([path, *argv], cwd=ROOT, env=env, capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError) as error:
        raise ValueError(f"{variable}={path!r}: runtime probe failed: {error}") from error
    need(result.returncode == 0 and result.stdout.strip(), f"{variable}={path!r}: runtime/version probe failed")
    return {"path": path, "realpath": str(Path(path).resolve()), "sha256": sha(path), "version": result.stdout.strip()}


def capture_request():
    """Resolve current intent. Validate ALL paths before any process or output write.

    Keep a virtualenv's invocation path as well as its realpath: resolving a Python
    symlink before invocation would silently discard its environment's packages.
    """
    node_default = json.loads((ROOT / RUNTIME_MANIFEST).read_text())["node"]["path"]
    paths = {
        "node": ("CV_FOCUS_NODE", selected_path("CV_FOCUS_NODE", node_default)),
        "focus_python": ("CV_FOCUS_PYTHON", selected_path("CV_FOCUS_PYTHON", str(ROOT / SERIES["6.0"]))),
        "fragment_python": ("CV_FRAGMENT_PYTHON", selected_path("CV_FRAGMENT_PYTHON", str(ROOT / SERIES["6.0"]))),
        "chromium": (
            "CV_FOCUS_CHROMIUM",
            selected_path("CV_FOCUS_CHROMIUM", "/home/alex/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome"),
        ),
        "ruff": ("ruff", selected_path("ruff", str(ROOT / ".venv/bin/ruff"))),
        "mkdocs": ("mkdocs", selected_path("mkdocs", str(ROOT / ".venv/bin/mkdocs"))),
        **{
            f"python{series}": (f"Django {series}", selected_path(f"Django {series}", str(ROOT / path)))
            for series, path in SERIES.items()
        },
    }
    playwright = selected_path(
        "CV_FOCUS_PLAYWRIGHT", "/home/alex/.npm/_npx/e41f203b7505f1fb/node_modules/playwright", executable=False
    )
    need((Path(playwright) / "package.json").is_file(), f"CV_FOCUS_PLAYWRIGHT={playwright!r}: package.json missing")
    port_text = os.environ.get("CV_CONDITIONAL_PORT", "8144")
    need(bool(re.fullmatch(r"[0-9]+", port_text)), f"CV_CONDITIONAL_PORT={port_text!r}: invalid port")
    port = int(port_text)
    need(1024 <= port <= 65535 and port != 8143, f"CV_CONDITIONAL_PORT={port_text!r}: invalid/reserved port")
    env = dict(os.environ, PYTHONPATH=f"{ROOT}/src:{ROOT}")
    runtimes = {}
    python_probe = (
        'import json,platform,django,importlib.util; print(json.dumps({"python":platform.python_version(),'
        '"django":django.get_version(),"packages":{n:importlib.util.find_spec(n).origin for n in '
        '["crud_views","crud_views_guardian","crud_views_polymorphic","crud_views_workflow",'
        '"crud_views_object_detail"]}},sort_keys=True))'
    )
    for key, (variable, path) in paths.items():
        argv = ["-c", python_probe] if "python" in key else ["--version"]
        runtimes[key] = runtime_probe(variable, path, argv, env)
        if "python" in key:
            details = json.loads(runtimes[key]["version"])
            need(
                all(
                    Path(origin).resolve() == ROOT / "src" / name / "__init__.py"
                    for name, origin in details["packages"].items()
                ),
                f"{variable}: imports outside checkout",
            )
        elif key == "node":
            need(bool(re.fullmatch(r"v\d+\.\d+\.\d+", runtimes[key]["version"])), f"{variable}={path!r}: not Node")
        elif key == "chromium":
            need(
                runtimes[key]["version"].startswith(("Chromium ", "Google Chrome ")),
                f"{variable}={path!r}: not Chromium",
            )
    playwright_probe = runtime_probe(
        "CV_FOCUS_PLAYWRIGHT",
        paths["node"][1],
        ["-e", "const p=require(process.argv[1]); console.log(p.version)", str(Path(playwright) / "package.json")],
        env,
    )
    runtimes["playwright"] = {
        "path": playwright,
        "realpath": str(Path(playwright).resolve()),
        "sha256": sha(Path(playwright) / "package.json"),
        "version": playwright_probe["version"],
    }
    runtimes["vitest"] = {
        "path": str(ROOT / "node_modules/vitest/vitest.mjs"),
        "sha256": sha(ROOT / "node_modules/vitest/package.json"),
        "version": json.loads((ROOT / "node_modules/vitest/package.json").read_text())["version"],
    }
    common = {
        "PYTHONPATH": env["PYTHONPATH"],
        "PATH": env.get("PATH"),
        "NODE_OPTIONS": env.get("NODE_OPTIONS"),
        "CI": env.get("CI"),
    }
    selections = {}
    for series in SERIES:
        for route in ROUTES:
            selected = {"python": runtimes[f"python{series}"], "environment": {"PYTHONPATH": common["PYTHONPATH"]}}
            if route in ("focused", "enabled-full"):
                selected.update(node=runtimes["node"], environment=common)
            selections[f"django{series}-{route}"] = selected
    for label in ("javascript", "javascript-integration"):
        selections[label] = {"node": runtimes["node"], "vitest": runtimes["vitest"], "environment": common}
    selections["javascript-integration"]["fragment_python"] = runtimes["fragment_python"]
    for label in BROWSERS:
        selections[label] = {key: runtimes[key] for key in ("node", "focus_python", "playwright", "chromium")}
        selections[label].update(port=port if label == "conditional-browser" else 8143, environment=common)
    selections["strict-docs"] = {"executable": runtimes["mkdocs"], "environment": {"PATH": common["PATH"]}}
    selections["ruff-check"] = selections["ruff-format"] = {"executable": runtimes["ruff"]}
    selections["evidence-self-tests"] = {**runtimes, "environment": common, "port": port}
    return {"selections": selections, "runtime_overrides": overrides()}


def can_reuse(record, manifest, selection):
    if record.get("selection") != selection:
        return False
    try:
        validate_gate(record, manifest)
    except (ValueError, KeyError, TypeError, OSError):
        return False
    return True


def command_record(argv, env, timeout=2400):
    started = time.monotonic()
    record = {
        "command": argv,
        "shell_command": shlex.join(argv),
        "started": now(),
        "revision": git("rev-parse", "HEAD"),
        "source_sha256": source()["sha256"],
        "runner_sha256": sha(__file__),
    }
    proc = subprocess.Popen(
        argv, cwd=ROOT, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True
    )
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        # This newly created process group is the only group this runner owns.
        os.killpg(proc.pid, signal.SIGTERM)
        try:
            stdout, stderr = proc.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            stdout, stderr = proc.communicate()
        record["timeout"] = True
    record.update(
        returncode=proc.returncode,
        stdout=stdout,
        stderr=stderr,
        finished=now(),
        duration_seconds=round(time.monotonic() - started, 3),
        process_completed=proc.poll() is not None,
    )
    record["source_after_sha256"] = source()["sha256"]
    return record


# A passive plugin captures facts in the actual pytest subprocess, never a separate
# interpreter probe. It observes collection and reports without changing outcomes.
PLUGIN = r"""
import importlib.metadata, importlib.util, json, os, platform, shutil, sys
from pathlib import Path
import pytest
state = {"collected": [], "selected": [], "deselected": [], "reports": []}
@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(session, config, items):
    state["collected"] = [item.nodeid for item in items]
def pytest_deselected(items):
    state["deselected"].extend(item.nodeid for item in items)
def pytest_collection_finish(session):
    state["selected"] = [item.nodeid for item in session.items]
def pytest_runtest_logreport(report):
    state["reports"].append({"nodeid": report.nodeid, "when": report.when,
                             "outcome": report.outcome, "diagnostic": str(report.longrepr) if report.failed else ""})
def pytest_sessionfinish(session, exitstatus):
    root = Path(os.environ["CV_PHASE_ROOT"])
    packages = {}
    for name in ["crud_views", "crud_views_guardian", "crud_views_polymorphic",
                 "crud_views_workflow", "crud_views_object_detail"]:
        packages[name] = str(Path(importlib.util.find_spec(name).origin).resolve())
    state["runtime"] = {"executable": sys.executable, "python": platform.python_version(),
        "django": importlib.metadata.version("django"), "packages": packages,
        "versions": {n: importlib.metadata.version(n) for n in
                     ["django", "django-crispy-forms", "crispy-bootstrap5", "pytest", "pytest-django"]}}
    state["environment"] = {"tracer_present": "CV_CONDITIONAL_TRACER" in os.environ,
        "tracer_value": os.environ.get("CV_CONDITIONAL_TRACER"),
        "node_override_present": "CV_FOCUS_NODE" in os.environ,
        "node_override": os.environ.get("CV_FOCUS_NODE"), "PATH": os.environ.get("PATH"),
        "node_which": shutil.which("node"), "npm_which": shutil.which("npm")}
    state["exitstatus"] = int(exitstatus)
    Path(os.environ["CV_PHASE_CAPTURE"]).write_text(json.dumps(state))
"""


def case_nodeid(classname, name):
    """JUnit classname includes nested test classes after the actual module path."""
    parts = classname.split(".")
    for boundary in range(len(parts), 0, -1):
        module = "/".join(parts[:boundary]) + ".py"
        if (ROOT / module).is_file():
            return module + "::" + "::".join([*parts[boundary:], name])
    raise ValueError(f"JUnit classname has no checkout module: {classname}")


def junit(path):
    cases = []
    for case in ET.parse(path).getroot().iter("testcase"):
        classname = case.get("classname", "")
        nodeid = case_nodeid(classname, case.get("name", ""))
        result = {
            "nodeid": nodeid,
            "status": "passed",
            "duration_seconds": float(case.get("time", "0")),
            "properties": {p.get("name"): p.get("value") for p in case.findall("properties/property")},
        }
        for kind, status in (("failure", "failed"), ("error", "error"), ("skipped", "skipped")):
            child = case.find(kind)
            if child is not None:
                result.update(status=status, message=child.get("message", ""), diagnostic=child.text or "")
        cases.append(result)
    return cases


def python_gate(series, route):
    env = dict(os.environ, PYTHONPATH=f"{ROOT}/src:{ROOT}")
    if route == "disabled-full":
        env.pop("CV_CONDITIONAL_TRACER", None)
        env.pop("CV_FOCUS_NODE", None)
        env["PATH"] = ""
    else:
        env["CV_CONDITIONAL_TRACER"] = "1"
    with tempfile.TemporaryDirectory(prefix=f"cv64-{series}-{route}-") as directory:
        temporary = Path(directory)
        (temporary / "phase64_capture.py").write_text(PLUGIN)
        missing = str(temporary / "guaranteed-nonexistent-node")
        if route == "missing-runtime":
            need(not Path(missing).exists(), "Negative-control path exists")
            env["CV_FOCUS_NODE"] = missing
        env.update(
            PYTHONPATH=f"{temporary}:{ROOT}/src:{ROOT}",
            CV_PHASE_ROOT=str(ROOT),
            CV_PHASE_CAPTURE=str(temporary / "capture.json"),
        )
        tests = FOCUSED if route == "focused" else [TRACER] if route == "missing-runtime" else ["tests"]
        pytest_argv = [
            *tests,
            "-q",
            "-p",
            "no:cacheprovider",
            "-p",
            "phase64_capture",
            "--junitxml",
            str(temporary / "junit.xml"),
            "-o",
            "junit_family=legacy",
            "-ra",
        ]
        if route.endswith("full") and series in ("4.2", "6.0"):
            pytest_argv += ["--deselect", GOLDEN]
        record = command_record([str(ROOT / SERIES[series]), "-m", "pytest", *pytest_argv], env)
        record.update(series=series, route=route, pytest_argv=pytest_argv, runtime_overrides=overrides())
        if (temporary / "capture.json").exists():
            record.update(json.loads((temporary / "capture.json").read_text()))
        record["junit"] = junit(temporary / "junit.xml") if (temporary / "junit.xml").exists() else []
        record["counts"] = {
            kind: sum(c["status"] == kind for c in record["junit"]) for kind in ("passed", "failed", "error", "skipped")
        }
        record["counts"].update(
            collected=len(record.get("collected", [])),
            selected=len(record.get("selected", [])),
            deselected=len(record.get("deselected", [])),
        )
        if route == "missing-runtime":
            record.update(missing_node_path=missing, missing_node_existed=False)
        record["id"] = f"django{series}-{route}"
        return record


def required_browser():
    text = (ROOT / "tests/browser/conditional-formsets.cjs").read_text()
    literal = re.search(r"const REQUIRED = (\{.*?\n\});", text, re.S).group(1)
    return json.loads(re.sub(r",\s*}", "}", literal.replace("'", '"')))


def port_available(port):
    with socket.socket() as probe:
        # Match Node's listener semantics: TIME_WAIT from completed owned HTTP
        # connections is not a leaked listener. A live listener still blocks bind.
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def browser_gate(name, selection=None):
    conditional = name == "conditional-browser"
    port = int(os.environ.get("CV_CONDITIONAL_PORT", "8144")) if conditional else 8143
    need(port_available(port), f"Occupied port {port}; refusing to touch unrelated process")
    runner = "tests/browser/conditional-formsets.cjs" if conditional else "tests/browser/modal-focus.cjs"
    with tempfile.TemporaryDirectory(prefix="cv64-browser-") as directory:
        output = str(Path(directory) / "browser.json")
        command = [node_path(), runner, "--case", "all", "--output", output]
        env = dict(os.environ)
        if selection:
            env.update(
                {
                    "CV_FOCUS_" + key: selection[field]["path"]
                    for key, field in (
                        ("NODE", "node"),
                        ("PYTHON", "focus_python"),
                        ("PLAYWRIGHT", "playwright"),
                        ("CHROMIUM", "chromium"),
                    )
                }
            )
            env["CV_CONDITIONAL_PORT"] = str(
                selection["port"] if conditional else os.environ.get("CV_CONDITIONAL_PORT", "8144")
            )
        record = command_record(command, env, timeout=600)
        record.update(
            id=name,
            port=port,
            port_free_before=True,
            port_free_after=port_available(port),
            runtime_overrides=overrides(),
        )
        if Path(output).exists():
            record["browser"] = json.loads(Path(output).read_text())
        if Path(output + ".server.log").exists():
            record["server_log"] = Path(output + ".server.log").read_text()
        record["canonical_check"] = command_record(
            [node_path(), runner, "--case", "all", "--check-evidence", output], env, timeout=60
        )
        return record


def expected_quality(name, selection=None, report="<vitest-report>", collection=False):
    """Only the report filename is a transport slot; every semantic token is fixed."""
    if name in ("javascript", "javascript-integration"):
        node = selection["node"]["path"] if selection else node_path()
        args = [node, "node_modules/vitest/vitest.mjs", "list" if collection else "run"]
        if name == "javascript-integration":
            args += ["--config", "vitest.integration.config.js"]
        return args + (
            ["--json", "--staticParse=false"]
            if collection
            else ["--reporter=default", "--reporter=json", "--outputFile.json", report]
        )
    commands = {
        "strict-docs": [str(ROOT / ".venv/bin/mkdocs"), "build", "--strict"],
        "ruff-check": [str(ROOT / ".venv/bin/ruff"), "check", *touched_python()],
        "ruff-format": [str(ROOT / ".venv/bin/ruff"), "format", "--check", *touched_python()],
        "evidence-self-tests": [
            str(ROOT / SERIES["6.0"]),
            "-m",
            "unittest",
            "discover",
            "-s",
            str(HERE.relative_to(ROOT)),
            "-p",
            "test_runner.py",
            "-v",
        ],
    }
    return commands[name]


def quality_gate(name, selection=None):
    selection = selection or capture_request()["selections"][name]
    env = dict(os.environ)
    if selection.get("environment", {}).get("PYTHONPATH"):
        env["PYTHONPATH"] = selection["environment"]["PYTHONPATH"]
    if name == "javascript-integration":
        env["CV_FRAGMENT_PYTHON"] = (selection or {}).get("fragment_python", {}).get("path", str(ROOT / SERIES["6.0"]))
        env["PYTHONPATH"] = f"{ROOT}/src:{ROOT}"
    with tempfile.TemporaryDirectory(prefix="cv64-quality-") as directory:
        report = str(Path(directory) / "vitest.json")
        record = command_record(expected_quality(name, selection, report=report), env, timeout=300)
        if name in ("javascript", "javascript-integration"):
            record["vitest"] = json.loads(Path(report).read_text()) if Path(report).exists() else {}
            record["inventory"] = command_record(expected_quality(name, selection, collection=True), env, timeout=300)
            record["counts"] = vitest_counts(record["vitest"])
        if name == "evidence-self-tests":
            record["selected_tests"] = self_test_ids()
    record["id"] = name
    record["selection"] = selection or {"node": {"path": node_path()}}
    return record


def vitest_counts(report):
    cases = [case for file in report.get("testResults", []) for case in file["assertionResults"]]
    return {
        "passed": sum(c["status"] == "passed" for c in cases),
        "collected": len(cases),
        "files": len(report.get("testResults", [])),
    }


def self_test_ids():
    import ast

    tree = ast.parse((HERE / "test_runner.py").read_text())
    return sorted(
        f"test_runner.{cls.name}.{method.name}"
        for cls in tree.body
        if isinstance(cls, ast.ClassDef)
        for method in cls.body
        if isinstance(method, ast.FunctionDef) and method.name.startswith("test_")
    )


def normalized_js_command(command):
    args = list(command)
    need(
        len(args) >= 2
        and args[-2] == "--outputFile.json"
        and isinstance(args[-1], str)
        and Path(args[-1]).is_absolute()
        and Path(args[-1]).name == "vitest.json",
        "JS command: invalid reporter transport",
    )
    args[-1] = "<vitest-report>"
    return args


def validate_quality(r, manifest):
    label = r["id"]
    selection = r.get("selection")
    command = normalized_js_command(r["command"]) if label in ("javascript", "javascript-integration") else r["command"]
    need(command == expected_quality(label, selection), f"{label}: wrong quality command")
    need(r.get("runner_sha256") == sha(__file__), f"{label}: runner source changed")
    if label == "evidence-self-tests":
        selected = self_test_ids()
        text = r["stdout"] + r["stderr"]
        observed = re.findall(r"^(test_\w+) \((test_runner\.\w+\.test_\w+)\) \.\.\. ok$", text, re.M)
        need(
            r.get("selected_tests") == selected
            and sorted(identity for _, identity in observed) == selected
            and f"Ran {len(selected)} tests" in text
            and text.rstrip().endswith("OK"),
            "Self-tests missing/failed/skipped",
        )
    if label not in ("javascript", "javascript-integration"):
        return
    inventory = r.get("inventory", {})
    need(
        inventory.get("command") == expected_quality(label, selection, collection=True), "JS inventory command changed"
    )
    need(
        inventory.get("source_sha256") == inventory.get("source_after_sha256") == manifest["sha256"]
        and inventory.get("process_completed") is True
        and inventory.get("returncode") == 0
        and not inventory.get("timeout"),
        "JS inventory stale/failed",
    )
    collected = json.loads(inventory.get("stdout", ""))
    expected = [(str(Path(c["file"]).resolve().relative_to(ROOT)), c["name"]) for c in collected]
    # Native it.each cases can deliberately share a display name. Preserve their
    # independent collection multiplicity; any additional copy is a duplicate.
    need(expected, "JS inventory empty")
    report = r.get("vitest", {})
    files, cases = [], []
    for file in report.get("testResults", []):
        path = str(Path(file["name"]).resolve().relative_to(ROOT))
        files.append(path)
        need(file.get("status") == "passed" and not file.get("message"), f"JS failed file: {path}")
        for case in file.get("assertionResults", []):
            need(case.get("status") == "passed" and not case.get("failureMessages"), "JS failed/skipped required case")
            cases.append((path, " > ".join([*case["ancestorTitles"], case["title"]])))
    need(len(files) == len(set(files)) and set(files) == {f for f, _ in expected}, "JS missing/duplicate file")
    need(Counter(cases) == Counter(expected), "JS missing/duplicate case selection")
    counts = vitest_counts(report)
    need(r.get("counts") == counts and counts["passed"] == counts["collected"] > 0, "JS inconsistent counts")
    need(
        report.get("success") is True
        and report.get("numTotalTests") == report.get("numPassedTests") == len(cases)
        and report.get("numFailedTests") == report.get("numPendingTests") == report.get("numTodoTests") == 0,
        "JS summary disagrees with case outcomes",
    )
    plain = re.sub(r"\x1b\[[0-9;]*m", "", r["stdout"])
    match = re.search(r"Tests\s+(\d+) passed\s*\((\d+)\)", plain)
    need(match and int(match[1]) == int(match[2]) == len(cases), "JS console/count mismatch")


def validate_gate(record, manifest):
    label = record["id"]
    need(
        record.get("source_sha256") == record.get("source_after_sha256") == manifest["sha256"],
        f"{label}: stale/changed source",
    )
    need(record.get("process_completed") is True and not record.get("timeout"), f"{label}: unfinished/timeout")
    need(
        record.get("started") and record.get("finished") and record.get("revision") and record.get("command"),
        f"{label}: missing command/time/revision",
    )
    if label.startswith("django"):
        validate_python(record)
    else:
        need(record.get("returncode") == 0, f"{label}: command failed")
        if label in QUALITY:
            validate_quality(record, manifest)
        if label in BROWSERS:
            validate_browser(record)
    if record.get("selection"):
        for key, runtime in record["selection"].items():
            if not isinstance(runtime, dict) or "path" not in runtime:
                continue
            path = Path(runtime["path"])
            digest_path = (
                path / "package.json"
                if key == "playwright"
                else ROOT / "node_modules/vitest/package.json"
                if key == "vitest"
                else path
            )
            need(
                path.exists() and runtime.get("sha256") == sha(digest_path),
                f"{label}: recorded runtime bytes changed: {key}",
            )
            need(runtime.get("version"), f"{label}: missing recorded runtime version: {key}")


def validate_python(r):
    label, series, route = r["id"], r["series"], r["route"]
    need(series in SERIES and route in ROUTES and label == f"django{series}-{route}", "Invalid Python route")
    need(
        r["command"][0] == str(ROOT / SERIES[series]) and r["command"][1:3] == ["-m", "pytest"],
        f"{label}: wrong interpreter/command",
    )
    argv = r.get("pytest_argv", [])
    selected_paths = FOCUSED if route == "focused" else [TRACER] if route == "missing-runtime" else ["tests"]
    prefix = [*selected_paths, "-q", "-p", "no:cacheprovider", "-p", "phase64_capture", "--junitxml"]
    suffix = ["-o", "junit_family=legacy", "-ra"]
    if route.endswith("full") and series in ("4.2", "6.0"):
        suffix += ["--deselect", GOLDEN]
    need(
        argv == r["command"][3:]
        and argv[: len(prefix)] == prefix
        and len(argv) == len(prefix) + 1 + len(suffix)
        and argv[len(prefix) + 1 :] == suffix,
        f"{label}: selection/exclusion command changed",
    )
    runtime = r.get("runtime", {})
    need(
        runtime.get("django", "").startswith(series + ".") and runtime.get("python", "").startswith("3.12."),
        f"{label}: wrong/missing runtime",
    )
    expected = {
        name: str(ROOT / "src" / name / "__init__.py")
        for name in (
            "crud_views",
            "crud_views_guardian",
            "crud_views_workflow",
            "crud_views_polymorphic",
            "crud_views_object_detail",
        )
    }
    need(runtime.get("packages") == expected, f"{label}: imports outside checkout")
    cases = r.get("junit", [])
    ids = [c["nodeid"] for c in cases]
    need(len(ids) == len(set(ids)) and set(ids) == set(r.get("selected", [])), f"{label}: JUnit/selection mismatch")
    counts = {kind: sum(c["status"] == kind for c in cases) for kind in ("passed", "failed", "error", "skipped")}
    counts.update(collected=len(r["collected"]), selected=len(r["selected"]), deselected=len(r["deselected"]))
    need(
        all(case["status"] in ("passed", "failed", "error", "skipped") for case in cases)
        and sum(counts[kind] for kind in ("passed", "failed", "error", "skipped")) == counts["selected"]
        and counts["collected"] == counts["selected"] + counts["deselected"],
        f"{label}: unknown outcome or duplicate/lost collection",
    )
    need(r.get("counts") == counts and counts["selected"] > 0, f"{label}: inconsistent/empty counts")
    need(set(r["collected"]) == set(r["selected"]) | set(r["deselected"]), f"{label}: lost collection")
    env = r.get("environment", {})
    need(
        set(env)
        == {
            "tracer_present",
            "tracer_value",
            "node_override_present",
            "node_override",
            "PATH",
            "node_which",
            "npm_which",
        },
        f"{label}: incomplete environment facts",
    )
    tracer = [c for c in cases if c["nodeid"] == TRACER]
    if route == "missing-runtime":
        need(r["returncode"] == r.get("exitstatus") == 1, f"{label}: expected test failure required")
        need(
            counts
            == {"passed": 0, "failed": 1, "error": 0, "skipped": 0, "collected": 1, "selected": 1, "deselected": 0},
            f"{label}: invalid negative-control outcome",
        )
        need(len(tracer) == 1 and tracer[0]["status"] == "failed", f"{label}: tracer did not fail")
        path = r.get("missing_node_path", "")
        need(
            path and r.get("missing_node_existed") is False and env.get("node_override") == path,
            f"{label}: missing-path override not honored",
        )
        need(
            path in tracer[0].get("diagnostic", "") and "unavailable; set CV_FOCUS_NODE" in tracer[0]["diagnostic"],
            f"{label}: missing selected-path runtime diagnostic",
        )
        need(
            any(
                p["nodeid"] == TRACER and p["when"] == "call" and p["outcome"] == "failed" for p in r.get("reports", [])
            ),
            f"{label}: setup/collection failure is not runtime proof",
        )
        need(env.get("tracer_value") == "1", f"{label}: tracer not enabled")
        return
    need(
        r["returncode"] == r.get("exitstatus") == 0
        and counts["passed"] > 0
        and counts["failed"] == counts["error"] == 0,
        f"{label}: green suite failed/empty",
    )
    skips = [c for c in cases if c["status"] == "skipped"]
    allowed = [CSP] if route.endswith("full") and series in ("4.2", "5.2") else []
    need(
        [c["nodeid"] for c in skips] == allowed and all(CSP_REASON in c["message"] for c in skips),
        f"{label}: unexpected skip/reason",
    )
    deselected = [GOLDEN] if route.endswith("full") and series in ("4.2", "6.0") else []
    need(r["deselected"] == deselected, f"{label}: unexpected deselection")
    if route == "disabled-full":
        need(
            not tracer
            and env.get("tracer_present") is False
            and env.get("tracer_value") is None
            and env.get("node_override_present") is False
            and env.get("node_override") is None
            and env.get("PATH") == ""
            and env.get("node_which") is None
            and env.get("npm_which") is None,
            f"{label}: forged Node-free environment",
        )
    else:
        need(env.get("tracer_present") is True and env.get("tracer_value") == "1", f"{label}: opt-in absent")
        need(len(tracer) == 1 and tracer[0]["status"] == "passed", f"{label}: required tracer missing/skipped/failed")
        props = tracer[0].get("properties", {})
        need(
            all(props.get(k) for k in ("tracer_node_path", "tracer_node_version", "tracer_jsdom_version")),
            f"{label}: tracer runtime provenance absent",
        )
        selected = r.get("selection", {}).get("node", {}).get("path") or r.get("runtime_overrides", {}).get(
            "CV_FOCUS_NODE"
        )
        if selected is None:
            selected = json.loads((ROOT / RUNTIME_MANIFEST).read_text())["node"]["path"]
        selected = shutil.which(selected) if selected else None
        need(
            selected and Path(props["tracer_node_path"]).resolve() == Path(selected).resolve(),
            f"{label}: selected tracer runtime mismatch",
        )
        need(
            props["tracer_jsdom_version"]
            == json.loads((ROOT / "node_modules/jsdom/package.json").read_text())["version"],
            f"{label}: jsdom provenance mismatch",
        )
    if route == "focused":
        need({node.split("::")[0] for node in ids} == set(FOCUSED), f"{label}: missing required focused file")
        for family in (
            "test_unchanged_inline_file_reference_clears_without_deleting_content",
            "test_policy_routes_accept_valid_posts",
            "test_reclean_invalid_existing_ids_never_save",
            "test_two_child_declaration_round_trips_emitted_index_and_keeps_gates",
            "test_fragment_raw_wrappers_balance_before_dom_parsing",
            "test_deeper_second_sibling_fragment_posts",
        ):
            need(any(family in c["nodeid"] and c["status"] == "passed" for c in cases), f"{label}: missing {family}")


def validate_conditional_captures(case):
    """Recheck present artifacts; historical browser exit codes confer no authority.

    Full-page PNG height is independent of the recorded CSS viewport height.
    Empty native captures are intentional and supply no visual acceptance.
    """
    theme = case["theme"]
    captures = case.get("captures")
    devices = {
        identity: {
            "id": identity,
            "width": width,
            "height": height,
            "deviceScaleFactor": 1,
            "hasTouch": identity == "mobile",
            "isMobile": identity == "mobile",
        }
        for identity, width, height in (("desktop", 1440, 900), ("mobile", 375, 812), ("tablet", 768, 1024))
    }
    need(
        isinstance(captures, list)
        and all(isinstance(c, dict) and isinstance(c.get("device"), dict) for c in captures)
        and (
            captures == []
            if theme == "native"
            else len(captures) == 3 and Counter(c["device"].get("id") for c in captures) == Counter(devices.keys())
        ),
        f"Conditional capture inventory invalid: {theme}",
    )
    base = ROOT / ".planning/ui-reviews/06.4-gap-repair"
    need(base.resolve().is_relative_to(ROOT), "Conditional capture path escape")
    paths = set()
    observations = []
    for capture in captures:
        device = capture["device"]
        identity = device["id"]
        expected = devices[identity]
        need(
            device == expected and all(type(device[k]) is type(v) for k, v in expected.items()),
            f"Conditional capture device mismatch: {identity}",
        )
        need(
            capture.get("viewport") == "width=device-width, initial-scale=1",
            f"Conditional capture viewport mismatch: {identity}",
        )
        document = capture.get("document")
        need(
            isinstance(document, dict)
            and all(
                type(document.get(k)) is int and document[k] == device["width"]
                for k in ("clientWidth", "innerWidth", "scrollWidth")
            ),
            f"Conditional capture containment invalid: {identity}",
        )
        observations.append({"device": device, **document})
        icons = capture.get("icons")
        need(
            isinstance(icons, dict)
            and icons.get("loaded") is True
            and isinstance(icons.get("glyphs"), list)
            and icons["glyphs"]
            and all(
                isinstance(g, dict)
                and isinstance(g.get("content"), str)
                and g["content"].strip() not in ("", "none", "normal", '""', "''")
                and isinstance(g.get("family"), str)
                and g["family"].strip()
                and all(
                    type(g.get(k)) in (int, float) and math.isfinite(g[k]) and g[k] > 0 for k in ("width", "height")
                )
                for g in icons["glyphs"]
            ),
            f"Conditional capture icon observations invalid: {identity}",
        )
        reference = capture.get("path")
        need(isinstance(reference, str) and reference, f"Conditional capture path invalid: {identity}")
        relative = Path(reference)
        need(
            not relative.is_absolute()
            and ".." not in relative.parts
            and relative.is_relative_to(base.relative_to(ROOT))
            and relative.suffix == ".png",
            f"Conditional capture path escape: {identity}",
        )
        path = (ROOT / relative).resolve()
        need(
            path.is_relative_to(base.resolve()) and path not in paths,
            f"Conditional capture path escape/duplicate: {identity}",
        )
        paths.add(path)
        need(path.is_file() and path.stat().st_size > 0, f"Conditional capture bytes missing: {identity}")
        digest = capture.get("sha256")
        need(
            isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest) and sha(path) == digest,
            f"Conditional capture digest mismatch: {identity}",
        )
        png = path.read_bytes()
        need(
            len(png) > 33 and png[:8] == b"\x89PNG\r\n\x1a\n" and png[12:16] == b"IHDR",
            f"Conditional capture PNG invalid: {identity}",
        )
        width, height = struct.unpack(">II", png[16:24])
        need(width == device["width"] and height > 0, f"Conditional capture PNG dimensions invalid: {identity}")
    assertions = {a["id"]: a for a in case["assertions"]}
    need(
        assertions["responsive-containment"].get("detail") == observations,
        "Conditional capture containment observations disagree",
    )
    need(
        all(
            assertions[key].get("passed") is True
            for key in ("responsive-containment", "loaded-rendered-glyphs", "screenshot-provenance")
        ),
        "Conditional capture observations missing/false",
    )
    human = case.get("humanReview", {})
    need(
        isinstance(human, dict) and human.get("H1") == human.get("H2") == "pending",
        "Conditional capture human review must remain pending",
    )


def validate_browser(r):
    label = r["id"]
    need(r.get("port") == r.get("selection", {}).get("port", r.get("port")), f"{label}: captured port mismatch")
    need(r.get("port_free_before") is True and r.get("port_free_after") is True, f"{label}: occupied/leaked port")
    need(r.get("canonical_check", {}).get("returncode") == 0, f"{label}: canonical browser checker failed")
    b = r.get("browser", {})
    need(
        b.get("completed") is True
        and b.get("passed") is True
        and not b.get("error")
        and not b.get("cleanupError")
        and b.get("pageErrors") == [],
        f"{label}: failed browser record",
    )
    hashes = b.get("sourceHashes", {})
    need(
        hashes and all((ROOT / p).is_file() and sha(ROOT / p) == value for p, value in hashes.items()),
        f"{label}: stale browser source",
    )
    runtime = b.get("runtime", {})
    for key in ("nodePath", "pythonPath", "playwrightPath", "chromiumPath", "node", "python"):
        need(runtime.get(key), f"{label}: missing runtime {key}")
    defaults = {
        "NODE": json.loads((ROOT / RUNTIME_MANIFEST).read_text())["node"]["path"],
        "PYTHON": str(ROOT / SERIES["6.0"]),
        "PLAYWRIGHT": "/home/alex/.npm/_npx/e41f203b7505f1fb/node_modules/playwright",
        "CHROMIUM": "/home/alex/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome",
    }
    for key, default in defaults.items():
        field = {"NODE": "node", "PYTHON": "focus_python", "PLAYWRIGHT": "playwright", "CHROMIUM": "chromium"}[key]
        selected = r.get("selection", {}).get(field, {}).get("path") or r.get("runtime_overrides", {}).get(
            "CV_FOCUS_" + key, default
        )
        actual = runtime[key.lower() + "Path"]
        need(Path(actual).resolve() == Path(selected).resolve(), f"{label}: runtime override mismatch {key}")
    if label == "conditional-browser":
        need(b.get("scope") == "all" and b.get("cleanup", {}).get("reaped") is True, "Conditional cleanup/scope")
        required = required_browser()
        expected = sorted(f"{theme}:{case}" for theme in ("stock", "native") for case in required)
        need(sorted(f"{c['theme']}:{c['id']}" for c in b["cases"]) == expected, "Missing/duplicate browser case")
        for case in b["cases"]:
            need(case.get("passed") is True and not case.get("skipped"), "Failed/skipped browser case")
            need(
                sorted(a["id"] for a in case["assertions"]) == sorted(required[case["id"]])
                and all(a.get("passed") is True for a in case["assertions"]),
                f"Missing/false assertion {case['id']}",
            )
            if case["id"] == "gap-ambiguity":
                validate_conditional_captures(case)
            if case["id"] == "inline-file-clear-unchanged":
                for key in ("referenceState", "uploadState"):
                    state = case.get(key, {})
                    need(
                        state.get("records")
                        and state.get("storage")
                        and state.get("storageContent")
                        and state.get("observed")
                        and state.get("events")
                        and state.get("received"),
                        f"Missing refreshed DB/storage observations: {case['theme']} {key}",
                    )
            if case["id"] == "fragment-raw-balance":
                need(case.get("requests") and case.get("state", {}).get("memos"), "Missing raw fragment/DB evidence")
                fragments = [item for item in case["requests"] if item.get("status") == 200 and "html" in item]
                need(fragments, "No raw pre-parser fragment")
                for fragment in fragments:
                    stack = []
                    for token, tag in re.findall(r"(<\/?(div|fieldset)\b[^>]*>)", fragment["html"], re.I):
                        if token.startswith("</"):
                            need(stack and stack.pop() == tag.lower(), "Unbalanced original raw fragment")
                        else:
                            stack.append(tag.lower())
                    need(not stack, "Unclosed original raw fragment")
    else:
        expected = [
            "unchecked",
            "blocked",
            "close",
            "escape",
            "removed-opener",
            "disabled-opener",
            "hidden-opener",
            "repeated-open",
            "native-dialog",
            "pending-close",
            "native-pending-close",
            "controls",
        ]
        need(sorted(c["id"] for c in b["cases"]) == sorted(expected), "Missing modal preservation cases")
        for case in b["cases"]:
            need(
                case.get("passed") is True
                and len(case.get("assertions", [])) >= 2
                and all(a.get("passed") is True for a in case["assertions"]),
                "Modal assertion failure",
            )
            for shot in case.get("screenshots", []):
                need(sha(ROOT / shot["path"]) == shot["sha256"], "Stale modal screenshot")


def validate_control_record(kind, record):
    need(isinstance(record, dict), f"Checker control evidence malformed: {kind}")
    need(type(record.get("returncode")) is int and record["returncode"] == 1, f"Checker control exit invalid: {kind}")
    command = record.get("command")
    need(
        isinstance(command, list)
        and len(command) == 5
        and all(isinstance(arg, str) for arg in command)
        and command[:4] == [sys.executable, str(Path(__file__).resolve()), "--check", "--output"]
        and Path(command[4]).is_absolute()
        and Path(command[4]).name == f"{kind}.json"
        and ".." not in Path(command[4]).parts,
        f"Checker control command invalid: {kind}",
    )
    need(
        record.get("stdout") == "" and record.get("stderr") == f"MATRIX_REJECTED: {CONTROL_DIAGNOSTICS[kind]}\n",
        f"Checker control diagnostic mismatch: {kind}",
    )


def validate_controls(data):
    summary = data.get("checker_controls")
    details = data.get("checker_control_evidence")
    # Stage two mutations operate on real stage one outcomes. Validate those
    # first, before asking for the stage two records which do not yet exist.
    need(
        isinstance(details, dict) and set(PAYLOAD_CORRUPTIONS) <= set(details),
        "Checker control evidence inventory incomplete",
    )
    need(
        isinstance(summary, dict) and set(PAYLOAD_CORRUPTIONS) <= set(summary),
        "Checker control summary inventory incomplete",
    )
    for kind in PAYLOAD_CORRUPTIONS:
        validate_control_record(kind, details[kind])
    need(set(details) == set(CORRUPTIONS), "Checker control evidence inventory incomplete")
    need(summary == dict.fromkeys(CORRUPTIONS, "rejected"), "Checker control summary inventory incomplete")
    for kind in RECORD_CORRUPTIONS:
        validate_control_record(kind, details[kind])


def validate(data, manifest, require_controls=True, only=None):
    need(data.get("schema") == 2, "Unsupported successor schema")
    need(data.get("completed") is (only is None) and data.get("only") == only, "Incomplete matrix / scoped packet")
    need(data.get("runner_sha256") == sha(__file__), "Evidence checker source changed since capture")
    need(data.get("source_manifest") == manifest, "Missing/stale source manifest")
    need(data.get("required_gate_ids") == expected_ids(), "Corrupted required-case list")
    need(sorted(data.get("gates", {})) == sorted([only] if only else expected_ids()), "Missing/extra matrix gates")
    for label, gate in data["gates"].items():
        need(gate.get("id") == label, f"{label}: contradictory gate identity")
        need(
            gate.get("selection") == data.get("capture_request", {}).get("selections", {}).get(label)
            and gate.get("selection"),
            f"{label}: contradictory captured runtime selection",
        )
        validate_gate(gate, manifest)
    if only:
        return
    for series in SERIES:
        focus = set(data["gates"][f"django{series}-focused"]["selected"])
        enabled = set(data["gates"][f"django{series}-enabled-full"]["selected"])
        disabled = set(data["gates"][f"django{series}-disabled-full"]["selected"])
        need(focus <= enabled and enabled - {TRACER} == disabled, f"{series}: full route/required node mismatch")
    for route in ROUTES:
        sets = []
        for series in SERIES:
            gate = data["gates"][f"django{series}-{route}"]
            sets.append(set(gate["selected"]) | set(gate["deselected"]))
        need(all(nodes == sets[0] for nodes in sets), f"{route}: unequal three-series collection")
    first, second = [data["gates"][key] for key in BROWSERS]
    need(
        first["finished"] <= second["started"] and first["port"] != second["port"] == 8143,
        "Browser runners collided or did not run sequentially",
    )
    if require_controls:
        validate_controls(data)
    return {"complete": require_controls, "scope": only}


def corrupt(data, kind):
    first = data["gates"]["django4.2-focused"]
    conditional = data["gates"]["conditional-browser"]["browser"]
    js = data["gates"]["javascript"]
    if kind.startswith("capture-"):
        case = next(c for c in conditional["cases"] if c["id"] == "gap-ambiguity" and c["theme"] == "stock")
        if kind == "capture-missing":
            case["captures"].pop()
        elif kind == "capture-digest":
            case["captures"][0]["sha256"] = "0" * 64
        else:
            case["captures"][0].pop("icons")
    elif kind == "control-missing-evidence":
        data.pop("checker_control_evidence", None)
    elif kind == "control-missing-summary":
        data.pop("checker_controls", None)
    elif kind == "control-success-outcome":
        data["checker_control_evidence"]["exit-code"]["returncode"] = 0
    elif kind == "control-wrong-command":
        data["checker_control_evidence"]["exit-code"]["command"][0] = "/bin/true"
    elif kind == "control-wrong-diagnostic":
        data["checker_control_evidence"]["exit-code"]["stderr"] = "MATRIX_REJECTED: Missing/stale source manifest\n"
    elif kind == "js-filtered-command":
        js["command"].insert(3, "-t=renders")
        js["counts"] = {"passed": 1, "collected": 1, "files": 1}
    elif kind == "js-wrong-executable":
        js["command"][0] = "/bin/true"
    elif kind == "js-missing-file":
        js["vitest"]["testResults"].pop()
    elif kind == "js-duplicate-file":
        js["vitest"]["testResults"].append(copy.deepcopy(js["vitest"]["testResults"][0]))
    elif kind == "js-missing-case":
        js["vitest"]["testResults"][0]["assertionResults"].pop()
    elif kind == "js-duplicate-case":
        js["vitest"]["testResults"][0]["assertionResults"].append(
            copy.deepcopy(js["vitest"]["testResults"][0]["assertionResults"][0])
        )
    elif kind in ("js-failed-case", "js-skipped-case"):
        js["vitest"]["testResults"][0]["assertionResults"][0]["status"] = (
            "failed" if kind == "js-failed-case" else "pending"
        )
    elif kind == "js-false-counts":
        js["counts"]["passed"] = 1
    elif kind == "integration-missing":
        data["gates"].pop("javascript-integration")
    elif kind == "docs-non-strict":
        data["gates"]["strict-docs"]["command"].remove("--strict")
    elif kind == "ruff-wrong-subcommand":
        data["gates"]["ruff-check"]["command"][1] = "format"
    elif kind == "ruff-format-missing-check":
        data["gates"]["ruff-format"]["command"].remove("--check")
    elif kind == "exit-code":
        first["returncode"] = 9
    elif kind == "required-case-list":
        data["required_gate_ids"].pop()
    elif kind in ("raw-balance-assertion", "inline-clear-assertion"):
        caseid = "fragment-raw-balance" if kind.startswith("raw") else "inline-file-clear-unchanged"
        next(c for c in conditional["cases"] if c["id"] == caseid)["assertions"].pop()
    elif kind == "source-hash":
        data["source_manifest"]["files"][next(iter(data["source_manifest"]["files"]))] = "stale"
    elif kind.startswith("tracer-"):
        tracer = next(c for c in first["junit"] if c["nodeid"] == TRACER)
        if kind == "tracer-absent":
            first["junit"].remove(tracer)
            first["selected"].remove(TRACER)
            first["collected"].remove(TRACER)
            first["reports"] = [p for p in first["reports"] if p["nodeid"] != TRACER]
        elif kind == "tracer-zero-selected":
            first["junit"] = []
            first["selected"] = []
            first["collected"] = []
            first["reports"] = []
        else:
            tracer["status"] = "skipped" if kind.endswith("skipped") else "failed"
        # Keep the aggregate internally consistent: these controls must fail the
        # required-tracer contract even when an altered suite still claims green.
        first["counts"] = {
            status: sum(c["status"] == status for c in first["junit"])
            for status in ("passed", "failed", "error", "skipped")
        }
        first["counts"].update(
            collected=len(first["collected"]), selected=len(first["selected"]), deselected=len(first["deselected"])
        )
    elif kind.startswith("disabled-"):
        env = data["gates"]["django4.2-disabled-full"]["environment"]
        if kind == "disabled-opt-in":
            env.update(tracer_present=True, tracer_value="1")
        else:
            env["node_which"] = "/forged/node"
    else:
        control = data["gates"]["django4.2-missing-runtime"]
        control["reports"] = [p for p in control["reports"] if p["when"] != "call"]


def check(output, only=None):
    manifest = source()
    data = load_json(output)
    validate(data, manifest, only=only)
    need(load_json(output.parent / "source-manifest.json") == manifest, "Sidecar source manifest stale")
    print(
        f"PHASE64_{'SCOPED' if only else 'MATRIX'}_OK {len(data['gates'])} gates source={manifest['sha256']}",
        flush=True,
    )


def run(output, only=None):
    # Preflight is intentionally before reading or modifying any capture metadata.
    request = capture_request()
    manifest = source()
    data = load_json(output) if output.exists() else {}
    if data.get("source_manifest") != manifest:
        need(not data, "Source changed: preserve old results elsewhere before beginning a new evidence capture")
    need(not data or data.get("only") == only, "Cannot reinterpret a scoped/full capture")
    selections = request["selections"]
    # Drop affected records before replacing the top-level contract. An interrupted
    # capture must never pair a new requested runtime with contradictory old gates.
    data["gates"] = {
        label: gate for label, gate in data.get("gates", {}).items() if gate.get("selection") == selections.get(label)
    }
    data.update(
        schema=2,
        only=only,
        source_manifest=manifest,
        required_gate_ids=expected_ids(),
        completed=False,
        runner_sha256=sha(__file__),
        runtime_overrides=overrides(),
        capture_request=request,
    )
    data.setdefault("started", now())
    data.setdefault("gates", {})
    # Earlier captures retain actual classname-derived names and selected node IDs.
    # Correct their reversible module/class split without re-executing green tests.
    for gate in data["gates"].values():
        for case in gate.get("junit", []):
            stem, name = case["nodeid"].split(".py::", 1)
            if "::" not in name and not (ROOT / (stem + ".py")).is_file():
                fixed = case_nodeid(stem.replace("/", "."), name)
                need(fixed in gate["selected"], "JUnit repair has no selected-node match")
                case["nodeid"] = fixed
                gate["junit_normalization"] = (
                    "Actual module path plus nested class names; outcomes/properties unchanged"
                )
    need(
        not data["gates"] or set(data["gates"]) <= set([only] if only else expected_ids()),
        "Cannot mix scoped and full captures",
    )
    write_json(output.parent / "source-manifest.json", manifest)

    def reusable(label):
        if label not in data["gates"]:
            return False
        if not can_reuse(data["gates"][label], manifest, selections[label]):
            return False
        print(f"REUSE {label}", flush=True)
        return True

    def save(record):
        record["selection"] = selections[record["id"]]
        data["gates"][record["id"]] = record
        write_json(output, data)
        validate_gate(record, manifest)
        print(f"PASS {record['id']} {record['duration_seconds']}s {record.get('counts', '')}", flush=True)

    # Short focused and expected-failure gates settle before lengthy suites start.
    for route in ("focused", "missing-runtime"):
        for series in SERIES:
            label = f"django{series}-{route}"
            if only and only != label:
                continue
            if not reusable(label):
                print(f"START {label}", flush=True)
                save(python_gate(series, route))
    # Each test process owns in-memory databases and pytest-generated temporary roots.
    # No browser process or evidence writer runs inside this bounded worker pool.
    with ThreadPoolExecutor(max_workers=2) as pool:
        pending = {}
        for route in ("enabled-full", "disabled-full"):
            for series in SERIES:
                label = f"django{series}-{route}"
                if only and only != label:
                    continue
                if not reusable(label):
                    print(f"QUEUE {label}", flush=True)
                    pending[pool.submit(python_gate, series, route)] = label
        failures = []
        for future in as_completed(pending):
            try:
                save(future.result())
            except (ValueError, KeyError, TypeError, OSError, subprocess.SubprocessError) as error:
                # Every other queued result is still saved before surfacing a failed
                # gate. Resuming cannot throw away unrelated successful long suites.
                failures.append(f"{pending[future]}: {error}")
                print(f"FAILED {failures[-1]}", flush=True)
        need(not failures, "; ".join(failures))
    for label in QUALITY:
        if only and only != label:
            continue
        if not reusable(label):
            print(f"START {label}", flush=True)
            save(quality_gate(label, selections[label]))
    # A failed modal packet does not invalidate a completed conditional packet.
    # If conditional must run anew, modal must follow it to prove cleanup order.
    if only in (None, BROWSERS[0]) and not reusable(BROWSERS[0]):
        print(f"START {BROWSERS[0]}", flush=True)
        save(browser_gate(BROWSERS[0], selections[BROWSERS[0]]))
    modal_reuse = reusable(BROWSERS[1]) if only in (None, BROWSERS[1]) else True
    if only in (None, BROWSERS[1]) and (
        not modal_reuse
        or (only is None and data["gates"][BROWSERS[1]]["started"] < data["gates"][BROWSERS[0]]["finished"])
    ):
        print(f"START {BROWSERS[1]}", flush=True)
        save(browser_gate(BROWSERS[1], selections[BROWSERS[1]]))
    data.update(completed=only is None, finished=now())
    validate(data, manifest, require_controls=False, only=only)
    write_json(output, data)
    if only:
        check(output, only=only)
        return
    generate_controls(data, manifest, output)
    check(output)


def generate_controls(data, manifest, output):
    """Run payload controls, record controls, then an uncorrupted positive check.

    No seed outcome is invented. Payload validation precedes controls in validate;
    thus stage one fails on its mutation, and stage two on real stage one records.
    """
    data["checker_controls"] = {}
    data["checker_control_evidence"] = {}
    # Actual --check subprocesses read temporary corrupted copies; real evidence is untouched.
    with tempfile.TemporaryDirectory(prefix="cv64-checker-controls-") as directory:
        for kind in CORRUPTIONS:
            altered = copy.deepcopy(data)
            corrupt(altered, kind)
            path = Path(directory) / f"{kind}.json"
            write_json(path, altered)
            write_json(path.parent / "source-manifest.json", manifest)
            result = subprocess.run(
                [sys.executable, str(Path(__file__).resolve()), "--check", "--output", str(path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=60,
            )
            record = {
                "command": result.args,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
            validate_control_record(kind, record)
            data["checker_controls"][kind] = "rejected"
            data["checker_control_evidence"][kind] = record
            print(f"REJECTED corruption {kind}", flush=True)
    write_json(output, data)
    positive = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--check", "--output", str(output)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    need(
        positive.returncode == 0
        and positive.stderr == ""
        and positive.stdout == f"PHASE64_MATRIX_OK {len(data['gates'])} gates source={manifest['sha256']}\n",
        f"Final positive checker control failed: {positive.stderr}",
    )
    # This is an observation of the preceding complete check, not a prerequisite
    # for that same check (which would require inventing a self-referential seed).
    data["checker_positive_control"] = {
        "command": positive.args,
        "returncode": positive.returncode,
        "stdout": positive.stdout,
        "stderr": positive.stderr,
    }
    write_json(output, data)


GAP_REVIEWS = {
    "G1": ["CR-01"],
    "G2": ["CR-02"],
    "G3": ["CR-03"],
    "G4": ["CR-04"],
    "G5": ["CR-05"],
    "G6": ["WR-01", "WR-02", "WR-03", "WR-04"],
}
GAP_THREATS = {
    "G1": ["07", "08", "09", "24"],
    "G2": ["22", "25"],
    "G3": ["15", "26"],
    "G4": ["15", "26"],
    "G5": ["01", "27"],
    "G6": ["22", "28", "29", "31", "33"],
}
PROHIBITION = "Switching a conditional file field off must not silently authorize deletion of the stored file content."


def bound_file(reference):
    need(isinstance(reference, dict) and isinstance(reference.get("path"), str), "Missing file reference")
    path = (ROOT / reference["path"]).resolve()
    need(path.is_relative_to(ROOT) and path.is_file(), f"Missing/outside handoff file: {reference['path']}")
    need(reference.get("sha256") == sha(path), f"Stale handoff file hash: {reference['path']}")
    return path


def attributed(record, source_sha):
    need(
        all(
            isinstance(record.get(key), str) and record[key].strip()
            for key in ("actor", "recorded", "response", "context")
        ),
        "Unattributed accepted/closed disposition",
    )
    datetime.datetime.fromisoformat(record["recorded"].replace("Z", "+00:00"))
    need(record.get("source_sha256") == source_sha, "Disposition source provenance stale")
    references = record.get("evidence_files", record.get("evidence"))
    need(references, "Accepted/closed disposition lacks evidence")
    for reference in references:
        bound_file(reference)


def evidence_link(reference, matrix):
    need(isinstance(reference, dict) and reference.get("gate") in matrix["gates"], "Missing handoff gate reference")
    gate = matrix["gates"][reference["gate"]]
    case = reference.get("case")
    if case is None:
        need(gate["returncode"] == 0, "Failed gate cannot close a finding")
        return
    cases = {c["nodeid"] for c in gate.get("junit", []) if c["status"] == "passed"}
    cases.update(
        str(Path(file["name"]).resolve().relative_to(ROOT)) + "::" + c["fullName"]
        for file in gate.get("vitest", {}).get("testResults", [])
        for c in file["assertionResults"]
        if c["status"] == "passed"
    )
    for c in gate.get("browser", {}).get("cases", []):
        if c.get("passed"):
            identity = (c["theme"] + ":" if "theme" in c else "") + c["id"]
            cases.add(identity)
            cases.update(identity + ":" + a.get("id", a.get("name", "")) for a in c["assertions"] if a.get("passed"))
    need(case in cases, f"Missing/failed handoff case: {case}")


def validate_handoff(data):
    """Structural validity is distinct from readiness; pending humans stay pending.

    Plan19 packet contract: schema=1, packet/report file references {path,sha256},
    findings keyed by all G/CR/WR IDs, threats, decisions D-01..19, fallback_edges
    1..31 and explicit human_checks.H1/H2. Closed items require attributed,
    current-source report evidence. This function never invents a disposition.
    """
    need(isinstance(data, dict) and data.get("schema") == 1, "Malformed handoff schema")
    manifest = source()
    need(
        data.get("source_sha256") == manifest["sha256"] and data.get("runner_sha256") == sha(__file__),
        "Handoff source/runner provenance stale",
    )
    packet_path = bound_file(data.get("packet"))
    matrix = load_json(packet_path)
    validate(matrix, manifest)
    need(
        load_json(packet_path.parent / "source-manifest.json") == manifest,
        "Handoff matrix sidecar stale",
    )
    reports = data.get("reports", {})
    need(isinstance(reports, dict) and all(isinstance(value, dict) for value in reports.values()), "Malformed reports")
    need(set(reports) >= {"code", "security", "ui", "verification"}, "Missing independent report")
    ready = True
    for name, report in reports.items():
        bound_file(report)
        need(report.get("status") in ("pending", "open", "passed"), f"Invalid report disposition: {name}")
        if report["status"] == "passed":
            attributed(report, manifest["sha256"])
        else:
            ready = False
    findings = data.get("findings", {})
    need(
        isinstance(findings, dict) and all(isinstance(value, dict) for value in findings.values()), "Malformed findings"
    )
    required = set(GAP_REVIEWS) | {review for reviews in GAP_REVIEWS.values() for review in reviews}
    need(set(findings) == required, "Missing/extra G/CR/WR handoff finding")
    for gap, reviews in GAP_REVIEWS.items():
        need(findings[gap].get("review_ids") == reviews, f"Missing canonical finding links: {gap}")
        expected_threats = {"T-06.4-" + number for number in GAP_THREATS[gap]}
        for identity in [gap, *reviews]:
            finding = findings[identity]
            need(expected_threats <= set(finding.get("threats", [])), f"Missing threat links: {identity}")
            need(finding.get("status") in ("pending", "open", "closed"), f"Invalid finding disposition: {identity}")
            need(finding.get("evidence"), f"Missing regression evidence: {identity}")
            for reference in finding["evidence"]:
                evidence_link(reference, matrix)
            if finding["status"] == "closed":
                review = reports.get(finding.get("review"), {})
                need(review.get("status") == "passed", f"Closed finding without independent passed report: {identity}")
                attributed(finding, manifest["sha256"])
            else:
                ready = False
    threats = data.get("threats", {})
    need(isinstance(threats, dict) and all(isinstance(value, dict) for value in threats.values()), "Malformed threats")
    required_threats = {"T-06.4-" + number for numbers in GAP_THREATS.values() for number in numbers} | {
        "T-06.4-35",
        "T-06.4-36",
    }
    need(required_threats <= set(threats), "Missing reopened/new high threat dispositions")
    for identity, threat in threats.items():
        need(threat.get("status") in ("pending", "open", "verified"), f"Invalid threat disposition: {identity}")
        if threat["status"] == "verified":
            need(reports["security"]["status"] == "passed", "High threat closure lacks independent security report")
            attributed(threat, manifest["sha256"])
        else:
            ready = False
    need(set(data.get("decisions", [])) == {f"D-{i:02}" for i in range(1, 20)}, "Missing decision reconciliation")
    edges = data.get("fallback_edges", [])
    need(
        isinstance(edges, list)
        and all(isinstance(e, dict) for e in edges)
        and len(edges) == 31
        and {e.get("id") for e in edges} == set(range(1, 32)),
        "Missing fallback edge reconciliation",
    )
    for edge in edges:
        need(
            edge.get("status") in ("flagged-unresolved", "verified", "human-disposition"),
            "Invalid fallback disposition",
        )
        if edge["status"] == "flagged-unresolved":
            ready = False
        else:
            attributed(edge, manifest["sha256"])
    humans = data.get("human_checks", {})
    need(
        isinstance(humans, dict) and all(isinstance(value, dict) for value in humans.values()), "Malformed human states"
    )
    need(set(humans) == {"H1", "H2"}, "Missing explicit H1/H2 states")
    need(humans["H2"].get("prohibition") == PROHIBITION, "File-deletion prohibition changed/missing")
    for identity, human in humans.items():
        need(human.get("status") in ("pending", "accepted", "closed"), f"Invalid human disposition: {identity}")
        if human["status"] == "pending":
            need(
                not any(human.get(key) for key in ("actor", "recorded", "response", "evidence")),
                "Pending human has an invented response",
            )
            if identity == "H2":
                need(
                    human.get("canonical_status") == "flagged-unverified",
                    "Descriptor-less prohibition silently resolved",
                )
            ready = False
        else:
            attributed(human, manifest["sha256"])
            kind = human.get("kind")
            need(
                kind == "human" or (identity == "H2" and kind == "enforcement"),
                "Missing genuine human/enforcement disposition",
            )
            if kind == "enforcement":
                for field in ("descriptor", "red_evidence", "green_evidence"):
                    bound_file(human.get(field))
    need(data.get("ready", False) is ready, "Handoff readiness contradicts open obligations")
    return {"structurally_valid": True, "ready": ready, "disposition": "ready" if ready else "not-ready"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--run", action="store_true")
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--check-handoff", type=Path, metavar="JSON")
    parser.add_argument("--output", type=Path, default=HERE / "results.json")
    parser.add_argument("--only", choices=expected_ids())
    args = parser.parse_args()
    try:
        if args.check_handoff:
            need(not args.only, "--only is not a handoff mode")
            print(json.dumps(validate_handoff(load_json(args.check_handoff)), sort_keys=True))
        elif args.run:
            run(args.output.resolve(), only=args.only)
        else:
            check(args.output.resolve(), only=args.only)
    except (ValueError, KeyError, TypeError, OSError, ET.ParseError, subprocess.SubprocessError) as error:
        print(f"MATRIX_REJECTED: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
