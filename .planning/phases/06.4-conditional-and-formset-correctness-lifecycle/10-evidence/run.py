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
import os
import re
import shlex
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
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
QUALITY = ("javascript", "strict-docs", "ruff-check", "ruff-format")
BROWSERS = ("conditional-browser", "modal-browser")
CORRUPTIONS = (
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
)
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


def node_path():
    selected = os.environ.get("CV_FOCUS_NODE")
    if selected is None:
        selected = json.loads((ROOT / RUNTIME_MANIFEST).read_text())["node"]["path"]
    found = shutil.which(selected) if selected else None
    need(found, f"Selected Node unavailable: {selected!r}")
    return str(Path(found).resolve())


def touched_python():
    paths = git("diff", "--name-only", BASE, "--", "src", "tests", "examples").splitlines()
    return [p for p in paths if p.endswith(".py")] + [str(HERE.relative_to(ROOT) / "run.py")]


def expected_ids():
    return [f"django{series}-{route}" for series in SERIES for route in ROUTES] + list(QUALITY + BROWSERS)


def overrides():
    return {
        key: value for key, value in os.environ.items() if key.startswith("CV_FOCUS_") or key == "CV_CONDITIONAL_PORT"
    }


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


def browser_gate(name):
    conditional = name == "conditional-browser"
    port = int(os.environ.get("CV_CONDITIONAL_PORT", "8144")) if conditional else 8143
    need(port_available(port), f"Occupied port {port}; refusing to touch unrelated process")
    runner = "tests/browser/conditional-formsets.cjs" if conditional else "tests/browser/modal-focus.cjs"
    with tempfile.TemporaryDirectory(prefix="cv64-browser-") as directory:
        output = str(Path(directory) / "browser.json")
        command = [node_path(), runner, "--case", "all", "--output", output]
        record = command_record(command, dict(os.environ), timeout=600)
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
            [node_path(), runner, "--case", "all", "--check-evidence", output], dict(os.environ), timeout=60
        )
        return record


def quality_gate(name):
    commands = {
        "javascript": [node_path(), "node_modules/vitest/vitest.mjs", "run"],
        "strict-docs": [str(ROOT / ".venv/bin/mkdocs"), "build", "--strict"],
        "ruff-check": [str(ROOT / ".venv/bin/ruff"), "check", *touched_python()],
        "ruff-format": [str(ROOT / ".venv/bin/ruff"), "format", "--check", *touched_python()],
    }
    record = command_record(commands[name], dict(os.environ), timeout=300)
    record["id"] = name
    if name == "javascript":
        # The human reporter is kept verbatim, including individual files and totals.
        plain = re.sub(r"\x1b\[[0-9;]*m", "", record["stdout"])
        match = re.search(r"Tests\s+(\d+) passed\s*\((\d+)\)", plain)
        record["counts"] = {"passed": int(match[1]), "collected": int(match[2])} if match else {}
    return record


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
        if label in ("ruff-check", "ruff-format"):
            need(record.get("runner_sha256") == sha(__file__), f"{label}: runner source changed since lint")
            need(record["command"][0] == str(ROOT / ".venv/bin/ruff"), f"{label}: wrong lint executable")
            offset = 2 if label == "ruff-check" else 3
            need(record["command"][offset:] == touched_python(), f"{label}: missing touched Python files")
        if label == "javascript":
            counts = record.get("counts", {})
            need(counts.get("passed", 0) > 0 and counts["passed"] == counts.get("collected"), "JS empty/partial")
        if label in BROWSERS:
            validate_browser(record)


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
        selected = r.get("runtime_overrides", {}).get("CV_FOCUS_NODE")
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
            "test_invalid_existing_ids_never_save",
            "test_two_child_declaration_round_trips_emitted_index_and_keeps_gates",
            "test_fragment_raw_wrappers_balance_before_dom_parsing",
            "test_deeper_second_sibling_fragment_posts",
        ):
            need(any(family in c["nodeid"] and c["status"] == "passed" for c in cases), f"{label}: missing {family}")


def validate_browser(r):
    label = r["id"]
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
        "NODE": node_path(),
        "PYTHON": str(ROOT / SERIES["6.0"]),
        "PLAYWRIGHT": "/home/alex/.npm/_npx/e41f203b7505f1fb/node_modules/playwright",
        "CHROMIUM": "/home/alex/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome",
    }
    for key, default in defaults.items():
        selected = r.get("runtime_overrides", {}).get("CV_FOCUS_" + key, default)
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


def validate(data, manifest, require_controls=True):
    need(data.get("schema") == 1 and data.get("completed") is True, "Incomplete matrix")
    need(data.get("runner_sha256") == sha(__file__), "Evidence checker source changed since capture")
    need(data.get("source_manifest") == manifest, "Missing/stale source manifest")
    need(data.get("required_gate_ids") == expected_ids(), "Corrupted required-case list")
    need(sorted(data.get("gates", {})) == sorted(expected_ids()), "Missing/extra matrix gates")
    for label, gate in data["gates"].items():
        need(gate.get("id") == label, f"{label}: contradictory gate identity")
        validate_gate(gate, manifest)
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
        need(data.get("checker_controls") == dict.fromkeys(CORRUPTIONS, "rejected"), "Checker controls incomplete")


def corrupt(data, kind):
    first = data["gates"]["django4.2-focused"]
    conditional = data["gates"]["conditional-browser"]["browser"]
    if kind == "exit-code":
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


def check(output, controls=True):
    manifest = source()
    data = json.loads(output.read_text())
    validate(data, manifest, require_controls=controls)
    need(json.loads((HERE / "source-manifest.json").read_text()) == manifest, "Sidecar source manifest stale")
    print(f"PHASE64_MATRIX_OK {len(data['gates'])} gates source={manifest['sha256']}", flush=True)


def run(output):
    manifest = source()
    data = json.loads(output.read_text()) if output.exists() else {}
    if data.get("source_manifest") != manifest:
        need(not data, "Source changed: preserve old results elsewhere before beginning a new evidence capture")
    data.update(
        schema=1,
        source_manifest=manifest,
        required_gate_ids=expected_ids(),
        completed=False,
        runner_sha256=sha(__file__),
        runtime_overrides=overrides(),
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
    write_json(HERE / "source-manifest.json", manifest)

    def reusable(label):
        if label not in data["gates"]:
            return False
        try:
            validate_gate(data["gates"][label], manifest)
        except (ValueError, KeyError, TypeError, OSError):
            return False
        print(f"REUSE {label}", flush=True)
        return True

    def save(record):
        data["gates"][record["id"]] = record
        write_json(output, data)
        validate_gate(record, manifest)
        print(f"PASS {record['id']} {record['duration_seconds']}s {record.get('counts', '')}", flush=True)

    # Short focused and expected-failure gates settle before lengthy suites start.
    for route in ("focused", "missing-runtime"):
        for series in SERIES:
            label = f"django{series}-{route}"
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
        if not reusable(label):
            print(f"START {label}", flush=True)
            save(quality_gate(label))
    # A failed modal packet does not invalidate a completed conditional packet.
    # If conditional must run anew, modal must follow it to prove cleanup order.
    if not reusable(BROWSERS[0]):
        print(f"START {BROWSERS[0]}", flush=True)
        save(browser_gate(BROWSERS[0]))
    modal_reuse = reusable(BROWSERS[1])
    if not modal_reuse or data["gates"][BROWSERS[1]]["started"] < data["gates"][BROWSERS[0]]["finished"]:
        print(f"START {BROWSERS[1]}", flush=True)
        save(browser_gate(BROWSERS[1]))
    data.update(completed=True, finished=now())
    validate(data, manifest, require_controls=False)
    write_json(output, data)
    controls = {}
    control_evidence = {}
    # Actual --check subprocesses read temporary corrupted copies; real evidence is untouched.
    with tempfile.TemporaryDirectory(prefix="cv64-checker-controls-") as directory:
        for kind in CORRUPTIONS:
            altered = copy.deepcopy(data)
            altered["checker_controls"] = dict.fromkeys(CORRUPTIONS, "rejected")
            corrupt(altered, kind)
            path = Path(directory) / f"{kind}.json"
            write_json(path, altered)
            result = subprocess.run(
                [sys.executable, __file__, "--check", "--output", str(path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=60,
            )
            need(result.returncode != 0 and "MATRIX_REJECTED" in result.stderr, f"Checker accepted corruption: {kind}")
            controls[kind] = "rejected"
            control_evidence[kind] = {
                "command": result.args,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
            print(f"REJECTED corruption {kind}", flush=True)
    data["checker_controls"] = controls
    data["checker_control_evidence"] = control_evidence
    write_json(output, data)
    check(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--run", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--output", type=Path, default=HERE / "results.json")
    args = parser.parse_args()
    try:
        if args.run:
            run(args.output.resolve())
        else:
            check(args.output.resolve())
    except (ValueError, KeyError, TypeError, OSError, ET.ParseError, subprocess.SubprocessError) as error:
        print(f"MATRIX_REJECTED: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
