"""Import-pure companion evidence tooling. All source discovery and execution is explicit.

Original repositories are read-only. Archives, patches and test processes operate in disposable sibling copies.
Reports contain complete sanitized logs; private preservation snapshots never enter either repository.
"""

import argparse
import ast
import hashlib
import io
import json
import os
import re
import subprocess
import tarfile
import tempfile
import time
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

COMPANION_ROOT = "/home/alex/projects/alex/tabler-test"
COMPANION_REVISION = "885dfc791a150fdc715d6fb34c2e6181d6b92f3c"
COMPANION_ORIGIN = "https://github.com/alexander-jacob/tabler-test.git"
CORE_BASE = "cb26af4dfef2afb31d774a219abfad1c675cdff1"
COMPONENTS = {
    "theme": "src/crud_views_tabler",
    "pack": "src/django_tabler/templates/crispy_tabler",
    "layout": "src/django_tabler/crispy",
}
PHASE_DIR = ".planning/phases/06.6-theme-adoption-seams-from-the-tabler-sync"
BASELINE_NAME = "06-companion-baseline.json"
REPLAY_NAME = "07-tabler-replay.json"
ADOPTION_CLASSES = {
    "form:actions": "d-flex flex-wrap gap-2",
    "form:filter-actions": "d-flex flex-wrap gap-1",
    "alert:dismissible": "alert-dismissible fade show",
    "alert:close": "btn-close",
}
ADOPTION_ICONS = {"save": "tabler:check", "cancel": "tabler:arrow-left", "filter-reset": "tabler:filter-x"}
ACTION_ICONS = {
    "submit": "check",
    "delete": "trash",
    "cancel": "arrow-left",
    "filter-submit": "filter",
    "filter-reset": "filter-x",
}
SCENARIOS = {
    "owned-form",
    "csrf-post",
    "label-floor",
    "action-groups",
    "alert-dismiss",
    "modal-replace",
    "conditional-formset",
    "cancel-navigation",
}
FOCUSED_TESTS = [
    "crud_views_tabler.tests.MessagesParityTests",
    "crud_views_tabler.tests.ButtonClassTests.test_table_values",
    "crud_views_tabler.tests.ThemeAdoptionTests",
    "django_tabler.tests.PackageTests",
]
RUNTIME_EXCLUDES = {
    ".git",
    ".venv",
    ".nox",
    ".planning",
    ".codegraph",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
}


class EvidenceError(ValueError):
    """A required source or evidence predicate is not established."""


def require(condition, message):
    if not condition:
        raise EvidenceError(message)


def digest(value):
    if not isinstance(value, bytes):
        value = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(value).hexdigest()


def core_root():
    return Path(__file__).resolve().parents[2]


def git(root, *args):
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=False)
    require(
        result.returncode == 0, f"git {args[0]} failed for verified source: {result.stderr.decode(errors='replace')}"
    )
    return result.stdout


def absolute_path(value, name, *, resolve=True):
    require(isinstance(value, str) and value and Path(value).is_absolute(), f"{name} must be a nonempty absolute path")
    # Executable paths deliberately retain the final venv symlink.
    return Path(value).resolve() if resolve else Path(os.path.abspath(value))


def archive_files(root, revision):
    require(re.fullmatch(r"[0-9a-f]{40}", revision or ""), "revision must be a full commit identity")
    require(git(root, "rev-parse", f"{revision}^{{commit}}").decode().strip() == revision, "wrong source revision")
    files = {}
    with tarfile.open(fileobj=io.BytesIO(git(root, "archive", revision))) as archive:
        for member in archive:
            path = Path(member.name)
            require(not path.is_absolute() and ".." not in path.parts, "unsafe archive path")
            require(member.isfile() or member.isdir() or member.issym(), f"unsupported archive entry: {member.name}")
            if member.issym():
                target = path.parent / member.linkname
                require(not target.is_absolute() and ".." not in target.parts, "unsafe archive symlink")
                try:
                    linked = archive.getmember(target.as_posix())
                except KeyError as exc:
                    raise EvidenceError("missing archive symlink target") from exc
                require(linked.isfile(), "archive symlink target must be a regular file")
                # Materialize repository-local documentation links; never follow host filesystem links.
                files[member.name] = archive.extractfile(linked).read()
            if member.isfile():
                files[member.name] = archive.extractfile(member).read()
    require(files, "empty source archive")
    return files


def inventory(files):
    return {name: digest(content) for name, content in sorted(files.items())}


def write_tree(files, target):
    target = Path(target)
    require(not target.exists(), "archive target already exists")
    target.mkdir(parents=True)
    for name, data in files.items():
        path = target / name
        require(not Path(name).is_absolute() and ".." not in Path(name).parts, "unsafe tree path")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


def working_files(root):
    root = Path(root)
    files = {}
    for directory, directories, names in os.walk(root):
        directories[:] = [
            name for name in directories if name not in RUNTIME_EXCLUDES and not name.endswith(".egg-info")
        ]
        for name in directories + names:
            path = Path(directory) / name
            rel = path.relative_to(root)
            if path.is_symlink() and rel.as_posix() == "AGENTS.md" and os.readlink(path) == "CLAUDE.md":
                target = root / "CLAUDE.md"
                require(target.is_file() and not target.is_symlink(), "invalid internal documentation link")
                files[rel.as_posix()] = target.read_bytes()
                continue
            require(not path.is_symlink(), f"unexpected source symlink: {rel}")
            if name not in {"db.sqlite3", ".coverage"} and path.is_file():
                files[rel.as_posix()] = path.read_bytes()
    return files


def preservation(root):
    """Public digests only; do not expose the user's settings or diff contents."""
    base_files = archive_files(root, git(root, "rev-parse", "HEAD").decode().strip())
    tracked = git(root, "ls-files", "-z").decode().split("\0")
    dirty = {}
    for name in filter(None, tracked):
        path = Path(root) / name
        head = base_files.get(name)
        data = path.read_bytes() if path.is_file() else None
        if data != head:
            dirty[name] = digest(data) if data is not None else None
    return {
        "head": git(root, "rev-parse", "HEAD").decode().strip(),
        "dirty_paths": dirty,
        "dirty_diff_sha256": digest(git(root, "diff", "--binary", "HEAD")),
        "index_sha256": digest(git(root, "ls-files", "--stage", "-z")),
        "status_sha256": digest(git(root, "status", "--porcelain=v1", "-z")),
    }


def inspect_sources(root, revision, origin):
    root = absolute_path(str(root), "source root")
    require(root.is_dir(), "source root is missing")
    require(
        Path(git(root, "rev-parse", "--show-toplevel").decode().strip()).resolve() == root,
        "source is not its Git top-level",
    )
    require(git(root, "remote", "get-url", "origin").decode().strip() == origin, "source origin mismatch")
    files = archive_files(root, revision)
    for name, part in COMPONENTS.items():
        require(any(path.startswith(part + "/") for path in files), f"source component missing: {name}")
    return {
        "companion_root": str(root),
        "revision": revision,
        "origin": origin,
        "components": dict(COMPONENTS),
        "tracked_tree": inventory(files),
        "content_sha256": digest(inventory(files)),
    }


def load_json(path):
    try:
        value = json.loads(Path(path).read_text())
    except (OSError, ValueError) as exc:
        raise EvidenceError(f"missing or invalid evidence: {path}") from exc
    require(isinstance(value, dict), "evidence must be an object")
    return value


def resolve_recorded_source(operand="recorded", *, manifest=None, env=None):
    env = os.environ if env is None else env
    manifest = load_json(core_root() / PHASE_DIR / BASELINE_NAME) if manifest is None else manifest
    expected = absolute_path(manifest.get("companion_root"), "recorded companion_root")
    selected = expected if operand == "recorded" else absolute_path(operand, "delivered-source")
    require(selected == expected, "delivered source does not match recorded root")
    for key in ("CV_THEME_SOURCE", "CV_PACK_SOURCE"):
        if key in env:
            require(absolute_path(env[key], key) == expected, f"conflicting {key}")
    require(manifest.get("components") == COMPONENTS, "recorded component paths mismatch")
    inspect_sources(selected, manifest["revision"], manifest["origin"])
    return selected


RUNTIME_PROBE = """import importlib.util,importlib.metadata,json,sys
names=['Django','django-crispy-forms','crispy-bootstrap5','pytest','pytest-django','pytest-xdist','tblib']
versions={}
for name in names:
 try: versions[name]=importlib.metadata.version(name)
 except importlib.metadata.PackageNotFoundError: versions[name]=None
print(json.dumps({'python':list(sys.version_info[:3]),'prefix':sys.prefix,'versions':versions,
 'missing':[name for name in ['django','crispy_forms','crispy_bootstrap5','pytest','pytest_django','xdist','tblib']
            if importlib.util.find_spec(name) is None]}))
"""


def runtime_probe(executable):
    path = absolute_path(str(executable), "companion_python", resolve=False)
    require(path.is_file() and os.access(path, os.X_OK), "companion Python executable missing")
    result = subprocess.run([str(path), "-c", RUNTIME_PROBE], capture_output=True, text=True, check=False)
    require(result.returncode == 0, "companion runtime probe failed")
    try:
        return json.loads(result.stdout)
    except ValueError as exc:
        raise EvidenceError("invalid runtime probe output") from exc


def validate_runtime(runtime):
    require(tuple(runtime.get("python", [])) >= (3, 14), "companion requires Python >=3.14")
    versions = runtime.get("versions", {})
    require(re.match(r"^6\.1\.", versions.get("Django") or ""), "companion requires Django >=6.1,<6.2")
    require(not runtime.get("missing"), "missing companion dependencies: " + ", ".join(runtime.get("missing", [])))
    require(
        all(
            versions.get(name)
            for name in ("django-crispy-forms", "crispy-bootstrap5", "pytest", "pytest-django", "pytest-xdist")
        ),
        "incomplete companion dependency versions",
    )
    require(Path(runtime.get("prefix", "")).is_absolute(), "invalid runtime prefix")
    for package, minimum in (("django-crispy-forms", (2, 4)), ("crispy-bootstrap5", (2026, 9))):
        parts = re.match(r"^(\d+)\.(\d+)", versions[package])
        require(parts and tuple(map(int, parts.groups())) >= minimum, f"incompatible companion extra: {package}")


def resolve_companion_python(manifest, *, env=None, probe=runtime_probe):
    env = os.environ if env is None else env
    selected = absolute_path(manifest.get("companion_python"), "recorded companion_python", resolve=False)
    for name in ("CV_THEME_PYTHON", "CV_FOCUS_PYTHON"):
        if name in env:
            require(absolute_path(env[name], name, resolve=False) == selected, f"conflicting {name}")
    runtime = probe(selected)
    validate_runtime(runtime)
    require(runtime == manifest.get("runtime"), "recorded runtime prefix/version identity changed")
    return selected


def _registration_only(node):
    calls = [n for n in ast.walk(node) if isinstance(n, ast.Call)]
    return bool(calls) and all(
        isinstance(n.func, ast.Name)
        and n.func.id
        in {
            "register_assets",
            "register_icons",
            "register_icon_library",
            "register_button_classes",
            "register_label_mode_defaults",
        }
        for n in calls
    )


def source_sections(path, data):
    """Conservative independent source classification, including mixed module symbol coverage."""
    if path.startswith(("tests/", "docs/")) or path.endswith("/tests.py"):
        return [
            {"symbol": "file", "kind": "non-customization", "reason": "test or documentation, not runtime behavior"}
        ]
    if not path.startswith(("src/", "example/", "scripts/")):
        return [
            {"symbol": "file", "kind": "non-customization", "reason": "repository metadata or dependency configuration"}
        ]
    if path.endswith(".py"):
        tree = ast.parse(data, filename=path)
        sections = []
        for node in tree.body:
            symbol = getattr(node, "name", f"lines:{node.lineno}-{node.end_lineno}")
            targets = [t.id for t in getattr(node, "targets", []) if isinstance(t, ast.Name)]
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                targets.append(node.target.id)
            if targets:
                symbol = ",".join(targets)
            if isinstance(node, (ast.Import, ast.ImportFrom)) or (
                isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
            ):
                kind, reason = "non-customization", "imports or module documentation"
            elif any(t in {"TABLER_ICONS", "TABLER_BUTTON_CLASSES"} for t in targets):
                try:
                    ast.literal_eval(node.value)
                    kind, reason = "adoption", "data-only supported registry values"
                except (ValueError, TypeError):
                    kind, reason = "required", "computed registry behavior"
            elif _registration_only(node):
                kind, reason = "adoption", "supported registration calls; renderer callbacks classified separately"
            else:
                kind, reason = "required", "bespoke Python behavior or application integration"
            sections.append({"symbol": symbol, "kind": kind, "reason": reason})
        return sections or [{"symbol": "file", "kind": "non-customization", "reason": "empty package marker"}]
    if path.endswith((".html", ".js", ".css")):
        return [{"symbol": "file", "kind": "required", "reason": "template or client behavior/style implementation"}]
    return [{"symbol": "file", "kind": "non-customization", "reason": "non-executable package data"}]


def discover_shadows(files, core_files):
    logical = {path.split("/templates/", 1)[1] for path in core_files if "/templates/" in path}
    return {
        path: {"template": path.split("/templates/", 1)[1], "sha256": digest(data)}
        for path, data in files.items()
        if "/templates/" in path and path.split("/templates/", 1)[1] in logical
    }


def classify_tree(files, core_files):
    rows = {}
    for path, data in sorted(files.items()):
        sections = source_sections(path, data)
        for section in sections:
            if section["kind"] == "required":
                section["purpose_id"] = f"{path}#{section['symbol']}"
        rows[path] = {"path": path, "sha256": digest(data), "sections": sections}
    return {"tracked_tree": inventory(files), "classifications": rows, "shadows": discover_shadows(files, core_files)}


def validate_classifications(report, files, core_files):
    require(report.get("tracked_tree") == inventory(files), "independent source tree does not match inventory")
    rows = report.get("classifications", {})
    require(set(rows) == set(files), "missing or additional source classification")
    purposes = {}
    for path, data in files.items():
        row = rows[path]
        require(row.get("path") == path and row.get("sha256") == digest(data), f"classification identity: {path}")
        expected = {s["symbol"]: s["kind"] for s in source_sections(path, data)}
        sections = row.get("sections", [])
        require(len(sections) == len(expected), f"missing source symbol/section: {path}")
        require(
            {s.get("symbol"): s.get("kind") for s in sections} == expected,
            f"behavior cannot be relabeled adoption: {path}",
        )
        for section in sections:
            require(bool(section.get("reason")), f"missing classification reason: {path}")
            if section["kind"] == "required":
                pid = section.get("purpose_id")
                require(isinstance(pid, str) and pid, f"missing required purpose: {path}")
                purposes.setdefault(pid, set()).add(path)
    require(
        report.get("shadows") == discover_shadows(files, core_files), "independent template shadow inventory mismatch"
    )
    return purposes


def compare_purposes(before, after, before_files, after_files, core_files, retired=None):
    old = validate_classifications(before, before_files, core_files)
    new = validate_classifications(after, after_files, core_files)
    require(set(new) <= set(old), "new required customization purpose")
    old_sections = {
        (path, section["symbol"]): section["purpose_id"]
        for path, row in before["classifications"].items()
        for section in row["sections"]
        if section["kind"] == "required"
    }
    for path, row in after["classifications"].items():
        for section in row["sections"]:
            if section["kind"] != "required":
                continue
            identity = (path, section["symbol"])
            if identity in old_sections:
                require(section["purpose_id"] == old_sections[identity], "retained purpose ID changed")
            else:
                require(
                    any(
                        pid == section["purpose_id"]
                        and symbol == section["symbol"]
                        and before_files[old_path] == after_files[path]
                        for (old_path, symbol), pid in old_sections.items()
                    ),
                    "new behavior cannot borrow an existing purpose ID",
                )
    retired = retired or {}
    require(set(retired) == set(old) - set(new), "every retired purpose needs rendered adoption evidence")
    for pid, record in retired.items():
        require(
            record.get("passed") is True and record.get("assertions") and record.get("adoption_paths"),
            f"unproven retired purpose: {pid}",
        )
        require(all(a.get("passed") is True for a in record["assertions"]), "retirement render failed")
        for path in record["adoption_paths"]:
            require(
                path in after_files
                and any(s["kind"] == "adoption" for s in after["classifications"][path]["sections"]),
                "retirement has no public API adoption",
            )
    return {"before": len(old), "after": len(new), "retired": sorted(retired)}


def sanitize(text, secrets=()):
    for secret in secrets:
        if secret:
            text = text.replace(secret, "[REDACTED]")
    return re.sub(r"(?i)((?:secret_key|password|api_key|authorization)\s*[:=]\s*)[^\s,;]+", r"\1[REDACTED]", text)


def command_record(argv, cwd, *, env=None, secrets=()):
    started = time.time()
    result = subprocess.run([str(a) for a in argv], cwd=cwd, env=env, capture_output=True, text=True, check=False)
    effective_env = os.environ if env is None else env
    private_values = tuple(secrets) + tuple(
        value
        for key, value in effective_env.items()
        if re.search(r"SECRET|PASSWORD|TOKEN|API_KEY|AUTHORIZATION", key, re.I) and value
    )
    record = {
        "argv": [str(a) for a in argv],
        "cwd": str(cwd),
        "exit_code": result.returncode,
        "stdout": sanitize(result.stdout, private_values),
        "stderr": sanitize(result.stderr, private_values),
        "duration_seconds": round(time.time() - started, 3),
    }
    record["log_sha256"] = digest({key: record[key] for key in ("argv", "cwd", "exit_code", "stdout", "stderr")})
    return record


def validate_log(record):
    keys = ("argv", "cwd", "exit_code", "stdout", "stderr")
    require(all(key in record for key in keys), "missing embedded command logs")
    require(
        isinstance(record["argv"], list) and record["argv"] and all(isinstance(a, str) for a in record["argv"]),
        "invalid command argv",
    )
    require(isinstance(record["stdout"], str) and isinstance(record["stderr"], str), "missing full log text")
    require(record.get("log_sha256") == digest({key: record[key] for key in keys}), "tampered embedded logs")
    return record["stdout"] + "\n" + record["stderr"]


def suite_result(record, *, passing=False):
    output = validate_log(record)
    django_count = re.findall(r"Ran (\d+) tests? in", output)
    lines = [line for line in output.splitlines() if line.strip()]
    pytest_count = re.findall(r"\b(\d+) (?:passed|failed|error|errors)\b", lines[-1] if lines else "")
    count = int(django_count[-1]) if django_count else sum(map(int, pytest_count))
    # Django parallel tracebacks name the individual test in FAIL/ERROR headers.
    failures = re.findall(r"^(?:FAIL|ERROR): (.+)$", output, flags=re.M)
    failures += re.findall(r"^(?:FAILED|ERROR) ([^\s(]\S*)", output, flags=re.M)
    require(count > 0, "zero collected tests or missing suite results")
    require(record["exit_code"] in (0, 1), "suite infrastructure/collection failed")
    require(record["exit_code"] == 0 or failures, "failed suite lacks failure identities")
    require(not passing or (record["exit_code"] == 0 and not failures), "required suite failed")
    return {"count": count, "outcome": "passed" if record["exit_code"] == 0 else "failed", "failures": failures}


def compare_suite_failures(current, baseline, before_files, after_files):
    """D-13: retain failed outcomes, accepting only unchanged source-bound baseline test failures."""
    result = suite_result(current["command"])
    if not result["failures"]:
        return {"retained_failures": [], "outcome": result["outcome"]}
    require(baseline is not None, "missing baseline for failing suite")
    original = suite_result(baseline["command"])
    require(result["count"] >= original["count"], "companion test collection shrank")
    require(set(result["failures"]) <= set(original["failures"]), "new companion regression")
    for failure in result["failures"]:
        match = re.fullmatch(r"test_\w+ \(([^)]+)\)", failure)
        require(match, "unrecognized baseline failure identity")
        qualified = match[1]
        require(not any(qualified.startswith(name) for name in FOCUSED_TESTS), "required phase test failed")
        module, klass, method = qualified.rsplit(".", 2)
        suffix = module.replace(".", "/") + ".py"
        paths = [p for p in before_files if p == suffix or p.endswith("/" + suffix)]
        require(len(paths) == 1 and paths[0] in after_files, "missing baseline test source")
        classes = []
        for files in (before_files, after_files):
            candidates = [n for n in ast.parse(files[paths[0]]).body if isinstance(n, ast.ClassDef) and n.name == klass]
            require(len(candidates) == 1, "missing baseline test class")
            require(
                any(isinstance(n, ast.FunctionDef) and n.name == method for n in candidates[0].body),
                "missing baseline test method",
            )
            classes.append(ast.dump(candidates[0], include_attributes=False))
        require(classes[0] == classes[1], "changed baseline test cannot be grandfathered")
    return {"retained_failures": result["failures"], "outcome": result["outcome"]}


def suite_commands(executable):
    return [
        [
            str(executable),
            "example/manage.py",
            "test",
            "django_tabler",
            "crud_views_tabler",
            "dashboard",
            "catalog",
            "customers",
            "--parallel",
            "4",
        ],
        [str(executable), "-m", "pytest", "tests", "-n", "4", "-q"],
    ]


def validate_suite_commands(report, executable):
    suites = report.get("suites", [])
    require(len(suites) == 2, "missing exact companion suites")
    companion = report.get("isolated_roots", {}).get("companion")
    require(companion and Path(companion).is_absolute(), "missing isolated suite root")
    for suite, argv in zip(suites, suite_commands(executable), strict=True):
        command = suite.get("command", {})
        require(command.get("argv") == argv and command.get("cwd") == companion, "wrong suite command/runtime/root")


def literal_assignment(data, name):
    for node in ast.walk(ast.parse(data)):
        targets = getattr(node, "targets", []) if isinstance(node, ast.Assign) else [getattr(node, "target", None)]
        if any(isinstance(t, ast.Name) and t.id == name for t in targets):
            try:
                return ast.literal_eval(node.value)
            except (ValueError, TypeError) as exc:
                raise EvidenceError(f"nonliteral adoption data: {name}") from exc
    raise EvidenceError(f"missing adoption data: {name}")


def validate_adoption(files, baseline_files):
    buttons_path = "src/crud_views_tabler/buttons.py"
    expected = {**literal_assignment(baseline_files[buttons_path], "TABLER_BUTTON_CLASSES"), **ADOPTION_CLASSES}
    require(literal_assignment(files[buttons_path], "TABLER_BUTTON_CLASSES") == expected, "wrong exact class defaults")
    mappings = literal_assignment(files["src/crud_views_tabler/icons.py"], "TABLER_ICONS")
    require(
        all(mappings.get(key) == value for key, value in ADOPTION_ICONS.items()), "missing native icon registration"
    )
    calls = [
        n
        for n in ast.walk(ast.parse(files["src/crud_views_tabler/apps.py"]))
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "register_label_mode_defaults"
    ]
    require(
        len(calls) == 1 and len(calls[0].args) == 1 and ast.literal_eval(calls[0].args[0]) == {"form": "both"},
        "form label floor registration must be exactly both",
    )
    classes = {
        n.name: n for n in ast.parse(files["src/crud_views_tabler/tests.py"]).body if isinstance(n, ast.ClassDef)
    }
    require("ThemeAdoptionTests" in classes and "ButtonClassTests" in classes, "missing adoption test class")
    methods = [
        n for n in classes["ButtonClassTests"].body if isinstance(n, ast.FunctionDef) and n.name == "test_table_values"
    ]
    require(len(methods) == 1 and len(methods[0].body) == 2, "weakened exact table equality test")
    assignment, assertion = methods[0].body
    require(
        isinstance(assignment, ast.Assign) and ast.literal_eval(assignment.value) == expected,
        "exact table expected dictionary changed",
    )
    call = assertion.value if isinstance(assertion, ast.Expr) else None
    require(
        isinstance(call, ast.Call)
        and isinstance(call.func, ast.Attribute)
        and call.func.attr == "assertEqual"
        and len(call.args) == 2
        and all(isinstance(a, ast.Name) for a in call.args)
        and {a.id for a in call.args} == {"TABLER_BUTTON_CLASSES", "expected"},
        "weakened exact table equality",
    )
    return literal_assignment(files["src/django_tabler/icons.py"], "ICONS")


def validate_action_records(records, native_icons):
    expected = {(kind, mode) for kind in ACTION_ICONS for mode in ("both", "icon", "label")}
    require(len(records) == len(expected), "missing action kind/mode records")
    require({(r.get("kind"), r.get("mode")) for r in records} == expected, "missing action kind/mode records")
    for row in records:
        mode, kind = row["mode"], row["kind"]
        require(
            row.get("passed") is True and row.get("accessible_name") and row.get("source_sha256"),
            "failed or unbound action record",
        )
        expected_paths = [] if mode == "label" else native_icons[ACTION_ICONS[kind]]
        require(row.get("svg_paths") == expected_paths and (mode == "label" or all(expected_paths)), "wrong native SVG")
        require(
            row.get("visible_text") is (mode != "icon") and row.get("hidden_text") is (mode == "icon"),
            "wrong action label presentation",
        )
        require(row.get("font_awesome") is False, "Font Awesome fallback is not native adoption")
        if kind == "filter-reset":
            require(
                row.get("type") == "reset"
                and row.get("value")
                and row.get("reset_restored") is True
                and row.get("submit_events") == 0,
                "missing native reset evidence",
            )


def validate_cancel_records(records, native_icons):
    expected = {
        (destination, tag, mode, activation)
        for destination in ("absent", "none", "empty")
        for tag in ("button", "a")
        for mode in ("both", "icon", "label")
        for activation in ("click", "Enter", "Space")
    }
    require(len(records) == len(expected), "missing cancel-no-url branches")
    require(
        {(r.get("destination"), r.get("requested_tag"), r.get("mode"), r.get("activation")) for r in records}
        == expected,
        "missing cancel-no-url mode/tag/activation",
    )
    for row in records:
        require(
            row.get("passed") is True
            and row.get("tag") == "button"
            and row.get("type") == "button"
            and row.get("href") is None
            and row.get("accessible_name") == "Cancel",
            "invalid URL-less cancel control",
        )
        require(
            row.get("svg_paths") == ([] if row["mode"] == "label" else native_icons["arrow-left"]), "wrong cancel icon"
        )
        require(
            row.get("submit_events") == row.get("reset_events") == row.get("post_requests") == 0,
            "cancel submitted or reset",
        )
        require(
            row.get("navigation_intercepted") is False and "input_after" in row, "missing actual activation evidence"
        )
        if row["destination"] == "empty":
            require(
                row.get("attribute_present") is True
                and row.get("attribute_value") == ""
                and row.get("navigation") == "same-url-get"
                and row.get("document_replaced") is True
                and row.get("document_method") == "GET"
                and row.get("document_status") == 200,
                "empty cancel requires completed same-URL document GET",
            )
            require(
                row.get("url_before") and row.get("url_before") == row.get("url_after") and "#" not in row["url_after"],
                "empty cancel changed target",
            )
        else:
            require(
                row.get("attribute_present") is False
                and row.get("attribute_value") is None
                and row.get("navigation") == "none"
                and row.get("document_replaced") is False
                and row.get("input_after") == row.get("input_before")
                and row.get("input_before"),
                "absent cancel must preserve edits without navigation",
            )


def validate_phase_evidence(report, files, baseline_files, *, complete=True):
    native_icons = validate_adoption(files, baseline_files)
    cases = report.get("cases", [])
    expected = SCENARIOS if complete else {"label-floor"}
    require({c.get("id") for c in cases} >= expected, "missing named phase scenario")
    for case in cases:
        require(
            case.get("passed") is True
            and case.get("assertions")
            and all(a.get("passed") is True for a in case["assertions"]),
            "failed phase scenario",
        )
    validate_action_records(report.get("actions", []), native_icons)
    validate_cancel_records(report.get("cancel_no_url", []), native_icons)
    source_id = digest(inventory(files))
    require(
        all(row.get("source_sha256") == source_id for row in report["actions"] + report["cancel_no_url"]),
        "unbound action/cancel source identity",
    )
    require(
        report.get("adoption")
        == {"label_modes": {"form": "both"}, "icons": ADOPTION_ICONS, "classes": ADOPTION_CLASSES},
        "wrong effective adoption values",
    )
    for required in FOCUSED_TESTS:
        require(
            any(
                node.get("id", "").startswith(required) and node.get("outcome") == "passed"
                for node in report.get("test_nodes", [])
            ),
            f"missing focused test outcome: {required}",
        )
    if complete:
        expected = {
            (modal, choices, method)
            for modal in (False, True)
            for choices in (False, True)
            for method in ("GET", "POST")
        }
        branches = report.get("workflow_branches", [])
        require(
            {(r.get("modal"), r.get("has_workflow_choices"), r.get("method")) for r in branches} >= expected,
            "missing distinct workflow branch evidence",
        )
        for row in branches:
            modal, choices, method = row["modal"], row["has_workflow_choices"], row["method"]
            require(
                row.get("passed") is True and row.get("status") == (422 if modal and method == "POST" else 200),
                "workflow branch failed",
            )
            names = {t.get("name"): t.get("origin") for t in row.get("templates", [])}
            required = (
                ["crud_views/view_custom_form.content.html"]
                if modal
                else ["crud_views_workflow/view_workflow.content.html", "crud_views_workflow/view_workflow.action.html"]
            )
            for name in required:
                origin = names.get(name)
                require(
                    origin and Path(origin).is_absolute() and origin.endswith("/templates/" + name),
                    "workflow template origin missing",
                )
            require(
                not modal or not any(n and n.startswith("crud_views_workflow/") for n in names),
                "modal workflow conflated with full-page body",
            )
            owners = [f for f in row.get("forms", []) if "cv-form" in f.get("attrs", {}).get("class", "").split()]
            require(not row.get("nested") and len(owners) == int(modal or choices), "workflow owner branch mismatch")
            require(all(f.get("tokens") == 1 for f in owners), "workflow token ownership mismatch")
        expected_alerts = {
            (native, variant, activation)
            for native in (False, True)
            for variant in (("default",) if native else ("default", "custom", "empty"))
            for activation in ("click", "Enter", "Space")
        }
        alerts = report.get("alert_branches", [])
        require(
            {(r.get("native"), r.get("variant"), r.get("activation")) for r in alerts} == expected_alerts,
            "missing distinct native/CRUD alert dismissal evidence",
        )
        for row in alerts:
            hook = row.get("hook", {})
            require(
                row.get("passed") is True and hook.get("name") == "Close" and hook.get("type") == "button",
                "failed alert activation",
            )
            require(
                (hook.get("native") == "alert" and hook.get("crud") is None)
                if row["native"]
                else (hook.get("native") is None and hook.get("crud") == "" and row.get("adapter_calls") == 1),
                "wrong native/CRUD alert dispatch",
            )


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, prefix=f".{path.name}.", delete=False) as stream:
        temporary = Path(stream.name)
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def merge_delivery(path, slot, record):
    require(slot in {"form_probe", "delivered_probe", "committed_probe"}, "unknown delivery slot")
    bundle = load_json(path) if Path(path).exists() else {"schema": 1}
    require(record.get("commands"), "delivery requires embedded command logs")
    for command in record["commands"]:
        validate_log(command)
    require(record.get("bindings") and record.get("assertions"), "delivery requires source/runtime/config bindings")
    require(
        not (bundle.get("status") == "complete" and slot != "committed_probe"),
        "partial result cannot overwrite completed delivery",
    )
    bundle[slot] = record
    bundle["status"] = "complete" if slot == "committed_probe" and record.get("status") == "passed" else "provisional"
    if record.get("status") != "passed":
        bundle["status"] = "failed"
    if bundle["status"] == "complete":
        validate_bundle(bundle, record["bindings"], committed=True)
    atomic_json(path, bundle)
    return bundle


def validate_bundle(bundle, expected_bindings, *, committed=False):
    slots = ("form_probe", "delivered_probe", "committed_probe") if committed else ("form_probe", "delivered_probe")
    require(bundle.get("status") == ("complete" if committed else "provisional"), "partial delivery is not complete")
    for slot in slots:
        record = bundle.get(slot, {})
        require(record.get("status") == "passed" and record.get("commands"), f"missing/failing {slot}")
        require(record.get("bindings") == expected_bindings, "stale delivery source/runtime/config hashes")
        require(
            record.get("assertions") and all(a.get("passed") is True for a in record["assertions"]),
            "missing delivery assertions",
        )
        for command in record["commands"]:
            validate_log(command)
            require(command["exit_code"] == 0, "failed delivery command")
    return True


ORIGIN_PROBE = """import django,json,importlib,sys,hashlib
django.setup()
from django.template.loader import get_template
names=json.loads(sys.argv[1])
modules={name:importlib.import_module(name).__file__ for name in
 ['crud_views','crud_views_tabler','django_tabler','django_tabler.crispy']}
templates={}
for name in names:
 origin=get_template(name).origin.name
 templates[name]={'origin':origin,'sha256':hashlib.sha256(open(origin,'rb').read()).hexdigest()}
print(json.dumps({'modules':modules,'templates':templates}))
"""


def isolated_env(companion, core):
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(map(str, [companion / "src", core / "src", companion, companion / "example"]))
    env["DJANGO_SETTINGS_MODULE"] = "config.settings"
    env["DJANGO_SECRET_KEY"] = "isolated-theme-adoption-test-only"
    env["DJANGO_DEBUG"] = "1"
    env["DJANGO_ALLOWED_HOSTS"] = "testserver,127.0.0.1"
    return env


def probe_origins(executable, companion, core, files, core_files, *, runner=command_record):
    shadows = discover_shadows(files, core_files)
    names = {row["template"] for row in shadows.values()}
    names |= {p.split("/templates/", 1)[1] for p in files if p.startswith(COMPONENTS["pack"] + "/")}
    record = runner(
        [executable, "-c", ORIGIN_PROBE, json.dumps(sorted(names))], companion, env=isolated_env(companion, core)
    )
    require(record["exit_code"] == 0, "isolated module/template origin probe failed")
    try:
        origins = json.loads(record["stdout"])
    except ValueError as exc:
        raise EvidenceError("invalid origin probe") from exc
    validate_origins(origins, companion, core, files, core_files)
    return origins, record


def validate_origins(origins, companion, core, files, core_files):
    roots = {
        "crud_views": Path(core) / "src",
        "crud_views_tabler": Path(companion) / "src",
        "django_tabler": Path(companion) / "src",
        "django_tabler.crispy": Path(companion) / "src",
    }
    require(set(origins.get("modules", {})) == set(roots), "missing actual module origins")
    for module, root in roots.items():
        path = Path(origins["modules"][module])
        require(path.is_relative_to(root), f"wrong imported core/pack: {module}")
    expected = discover_shadows(files, core_files)
    expected.update(
        {
            p: {"template": p.split("/templates/", 1)[1], "sha256": digest(v)}
            for p, v in files.items()
            if p.startswith(COMPONENTS["pack"] + "/")
        }
    )
    for path, row in expected.items():
        observed = origins.get("templates", {}).get(row["template"], {})
        require(
            observed.get("origin") == str(Path(companion) / path) and observed.get("sha256") == row["sha256"],
            f"wrong template origin/hash: {path}",
        )


def _capture_inputs(env, *, probe=runtime_probe):
    root = absolute_path(env.get("CV_THEME_SOURCE", COMPANION_ROOT), "CV_THEME_SOURCE")
    require(
        root == absolute_path(env.get("CV_PACK_SOURCE", COMPANION_ROOT), "CV_PACK_SOURCE"),
        "ambiguous theme/pack source roots",
    )
    require(root == Path(COMPANION_ROOT).resolve(), "source overrides must match supplied identity")
    identity = inspect_sources(root, COMPANION_REVISION, COMPANION_ORIGIN)
    capture_continuity(root, COMPANION_REVISION)
    require(env.get("CV_THEME_CORE_BASE", CORE_BASE) == CORE_BASE, "wrong pinned pre-change core revision")
    executable = absolute_path(
        env.get("CV_THEME_PYTHON", str(root / ".venv/bin/python")), "CV_THEME_PYTHON", resolve=False
    )
    runtime = probe(executable)
    validate_runtime(runtime)
    return root, identity, executable, runtime


def capture_continuity(root, revision, head=None):
    """Keep the pinned archive while preserving the user's settings-only descendant commit."""
    head = head or git(root, "rev-parse", "HEAD").decode().strip()
    require(git(root, "merge-base", revision, head).decode().strip() == revision, "baseline is not an ancestor")
    before, after = archive_files(root, revision), archive_files(root, head)
    changed = {path for path in before.keys() | after.keys() if before.get(path) != after.get(path)}
    require(changed <= {"example/config/settings.py"}, "baseline source continuity changed outside private settings")
    require(set(before) == set(after), "baseline source continuity changed tracked paths")
    return {"head": head, "preserved_committed_paths": {path: digest(after[path]) for path in sorted(changed)}}


def capture_baseline(output, *, env=None, runner=command_record, probe=runtime_probe):
    env = dict(os.environ) if env is None else env
    root, identity, executable, runtime = _capture_inputs(env, probe=probe)
    before = preservation(root)
    companion_files = archive_files(root, COMPANION_REVISION)
    base_core_files = archive_files(core_root(), CORE_BASE)
    report = {
        "schema": 1,
        **identity,
        "core_root": str(core_root()),
        "core_revision": CORE_BASE,
        "core_tracked_tree": inventory(base_core_files),
        "companion_python": str(executable),
        "runtime": runtime,
        "preserved": before,
        "source_continuity": capture_continuity(root, COMPANION_REVISION, before["head"]),
        "inventory": classify_tree(companion_files, base_core_files),
        "test_configuration": {
            "DJANGO_SECRET_KEY": "isolated-theme-adoption-test-only",
            "DJANGO_ALLOWED_HOSTS": "testserver,127.0.0.1",
            "DJANGO_DEBUG": "1",
        },
        "asset_references": sorted(
            {
                url.decode()
                for value in companion_files.values()
                for url in re.findall(rb"https://[^\s\"\'<>]+", value)
                if b"cdn" in url or b"jsdelivr" in url
            }
        ),
        "status": "capturing",
        "suites": [],
    }
    with tempfile.TemporaryDirectory(prefix="cv-plan06-baseline-") as temporary:
        companion = Path(temporary) / "baseline/tabler-test"
        core = Path(temporary) / "baseline/django-crud-views"
        write_tree(companion_files, companion)
        write_tree(base_core_files, core)
        origins, origin_command = probe_origins(
            executable, companion, core, companion_files, base_core_files, runner=runner
        )
        report.update(
            origins=origins,
            origin_command=origin_command,
            isolated_roots={"companion": str(companion), "core": str(core)},
        )
        for argv in suite_commands(executable):
            process_env = isolated_env(companion, core)
            if "pytest" in argv:
                process_env.pop("DJANGO_SETTINGS_MODULE")  # retain the copy's pytest configuration
            command = runner(argv, companion, env=process_env)
            report["suites"].append({"command": command, **suite_result(command)})
    require(preservation(root) == before, "original companion changed during isolated capture")
    report["status"] = "captured"
    report["tests_outcome"] = "passed" if all(s["outcome"] == "passed" for s in report["suites"]) else "failed"
    atomic_json(output, report)
    return report


def check_baseline(report, *, env=None, probe=runtime_probe):
    root = resolve_recorded_source(manifest=report, env=env)
    resolve_companion_python(report, env=env, probe=probe)
    files = archive_files(root, report["revision"])
    base_core = archive_files(core_root(), report["core_revision"])
    require(report["core_revision"] == CORE_BASE, "wrong pre-phase core baseline")
    require(
        report.get("tracked_tree") == inventory(files) and report.get("content_sha256") == digest(inventory(files)),
        "changed companion source fingerprint",
    )
    require(report.get("core_tracked_tree") == inventory(base_core), "changed core source fingerprint")
    require(
        report.get("source_continuity") == capture_continuity(root, report["revision"], report["preserved"]["head"]),
        "changed recorded source continuity",
    )
    validate_classifications(report.get("inventory", {}), files, base_core)
    require(report.get("status") == "captured" and len(report.get("suites", [])) == 2, "incomplete baseline capture")
    validate_suite_commands(report, report["companion_python"])
    for suite in report["suites"]:
        require(
            suite_result(suite["command"]) == {key: suite[key] for key in ("count", "outcome", "failures")},
            "suite outcome differs from embedded logs",
        )
    require(
        report.get("tests_outcome")
        == ("passed" if all(s["outcome"] == "passed" for s in report["suites"]) else "failed"),
        "failed baseline relabeled passing",
    )
    validate_log(report["origin_command"])
    require(json.loads(report["origin_command"]["stdout"]) == report["origins"], "origin report differs from raw probe")
    validate_origins(
        report["origins"], report["isolated_roots"]["companion"], report["isolated_roots"]["core"], files, base_core
    )
    return True


def validate_core_receipt(receipt, root):
    require(receipt.get("repository_root") == str(root), "missing separate core receipt")
    # Task 10-02 proves the companion commit before task 10-03 commits these very bytes.
    # The resulting core commit belongs in SUMMARY, avoiding a self-referential manifest.
    parent = receipt.get("before_head", "")
    require(re.fullmatch(r"[0-9a-f]{40}", parent), "missing core evidence parent")
    git(root, "merge-base", "--is-ancestor", parent, "HEAD")
    require(
        set(receipt.get("evidence_paths", []))
        == {PHASE_DIR + "/10-companion-delivery.json", PHASE_DIR + "/07-TABLER-HANDOFF.md"},
        "core receipt must identify both scoped evidence paths",
    )


def patched_files(base_files, patch, *, commands=None):
    require(isinstance(patch, str) and patch, "missing exact candidate patch")
    with tempfile.TemporaryDirectory(prefix="cv-plan06-replay-") as temporary:
        target = Path(temporary) / "tabler-test"
        write_tree(base_files, target)
        patch_path = Path(temporary) / "adaptation.patch"
        patch_path.write_text(patch)
        for arguments in (["--check"], []):
            result = command_record(["git", "apply", *arguments, "--whitespace=nowarn", str(patch_path)], target)
            if commands is not None:
                commands.append(result)
            require(result["exit_code"] == 0, "candidate patch does not apply to pinned archive")
        return working_files(target)


def verify_replay(report, baseline, *, env=None, probe=runtime_probe):
    check_baseline(baseline, env=env, probe=probe)
    root = resolve_recorded_source(manifest=baseline, env=env)
    before_files = archive_files(root, baseline["revision"])
    core_files = archive_files(core_root(), baseline["core_revision"])
    require(report.get("baseline_sha256") == digest(baseline), "replay baseline binding changed")
    patch = report.get("patch")
    require(isinstance(patch, str) and patch, "missing exact candidate patch")
    require(report.get("patch_sha256") == digest(patch.encode()), "candidate patch fingerprint changed")
    after_files = patched_files(before_files, patch)
    # All relevant live core bytes, including test/docs/config assets, must match tested candidate identity.
    current_core = {
        p: v
        for p, v in working_files(core_root()).items()
        if p.startswith(("src/", "tests/", "docs/")) or p in {"pyproject.toml", "package.json", "package-lock.json"}
    }
    require(report.get("core_inventory") == inventory(current_core), "candidate core fingerprint changed")
    validate_log(report.get("origin_command", {}))
    require(json.loads(report["origin_command"]["stdout"]) == report.get("origins"), "replay origin raw probe mismatch")
    validate_origins(
        report["origins"],
        report["isolated_roots"]["companion"],
        report["isolated_roots"]["core"],
        after_files,
        current_core,
    )
    compare_purposes(
        baseline["inventory"],
        report.get("inventory", {}),
        before_files,
        after_files,
        core_files,
        report.get("retired_purposes"),
    )
    require(report.get("runtime") == baseline["runtime"], "replay runtime identity mismatch")
    require(len(report.get("suites", [])) == 2, "missing replay suites")
    validate_suite_commands(report, baseline["companion_python"])
    for index, suite in enumerate(report["suites"]):
        original = baseline.get("suites", [])[index] if index < len(baseline.get("suites", [])) else None
        compare_suite_failures(suite, original, before_files, after_files)
    validate_phase_evidence(report, after_files, before_files)
    require(
        all(row.get("source_sha256") == digest(inventory(after_files)) for row in report["actions"]),
        "unbound action source identity",
    )
    require(report.get("status") == "passed", "replay is not passing")
    return after_files


def private_snapshot(root, directory):
    """Plan 10 can capture this before delivery. The returned path is private, never a report dependency."""
    directory = absolute_path(str(directory), "private snapshot directory")
    require(
        not directory.is_relative_to(Path(root).resolve()) and not directory.is_relative_to(core_root()),
        "private preservation snapshot must be outside both repositories",
    )
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    staged = set(filter(None, git(root, "diff", "--cached", "--name-only", "-z").decode().split("\0")))
    entries = {
        entry.split("\t", 1)[1]: entry.split("\t", 1)[0]
        for entry in git(root, "ls-files", "--stage", "-z").decode().split("\0")
        if entry
    }
    record = {
        "root": str(Path(root).resolve()),
        "preserved": preservation(root),
        "worktree_patch": git(root, "diff", "--binary", "HEAD").decode(),
        "staged_entries": {p: entries.get(p) for p in staged},
    }
    target = directory / "preservation.json"
    atomic_json(target, record)
    target.chmod(0o600)
    return target


def verify_receipt(root, receipt, expected_files, expected_parent):
    require(receipt.get("repository_root") == str(Path(root).resolve()), "wrong repository-qualified receipt")
    after = receipt.get("after_head", "")
    require(re.fullmatch(r"[0-9a-f]{40}", after), "absent scoped source commit")
    parent = git(root, "rev-parse", f"{after}^").decode().strip()
    require(parent == expected_parent == receipt.get("before_head"), "wrong scoped commit parent")
    require(git(root, "rev-parse", f"{after}^{{tree}}").decode().strip() == receipt.get("tree"), "wrong receipt tree")
    require(
        inventory(archive_files(root, after)) == inventory(expected_files), "commit contains unapproved source delta"
    )
    delta = git(root, "diff", "--binary", parent, after)
    require(receipt.get("delta_sha256") == digest(delta), "commit delta fingerprint mismatch")
    require(git(root, "rev-parse", "HEAD").decode().strip() == after, "source HEAD differs from scoped receipt")


def check_delivery_tree(root, candidate_files, baseline, snapshot, *, receipt=None):
    require(snapshot.get("root") == str(Path(root).resolve()), "private snapshot root mismatch")
    require(
        all(
            snapshot["preserved"]["dirty_paths"].get(path) == value
            for path, value in baseline["preserved"]["dirty_paths"].items()
        ),
        "original private settings changed",
    )
    committed_files = dict(candidate_files)
    # The user's settings-only commit predates this task and is not part of the replay patch.
    preserved_committed = baseline.get("source_continuity", {}).get("preserved_committed_paths", {})
    if preserved_committed:
        parent_files = archive_files(root, snapshot["preserved"]["head"])
        for path, fingerprint in preserved_committed.items():
            require(path == "example/config/settings.py", "unexpected preserved committed path")
            require(digest(parent_files.get(path)) == fingerprint, "original committed private settings changed")
            committed_files[path] = parent_files[path]
    expected = (
        patched_files(committed_files, snapshot["worktree_patch"]) if snapshot["worktree_patch"] else committed_files
    )
    actual = working_files(root)
    require(
        inventory(actual) == inventory(expected), "unaccounted changed/new/missing delivered source or private settings"
    )
    entries = {
        entry.split("\t", 1)[1]: entry.split("\t", 1)[0]
        for entry in git(root, "ls-files", "--stage", "-z").decode().split("\0")
        if entry
    }
    require(
        all(entries.get(p) == value for p, value in snapshot["staged_entries"].items()),
        "unrelated staged index entry changed",
    )
    if receipt is not None:
        verify_receipt(root, receipt, committed_files, snapshot["preserved"]["head"])
        staged = set(git(root, "diff", "--cached", "--name-only").decode().splitlines())
        require(staged <= set(snapshot["staged_entries"]), "uncommitted task or new staged hunk remains")
    return {
        "source_sha256": digest(inventory(candidate_files)),
        "preserved_dirty_sha256": digest(baseline["preserved"]),
        "index_preserved": True,
    }


def _delivered_probe(root, baseline, replay, output, *, require_committed=False, env=None, runner=command_record):
    env = dict(os.environ) if env is None else env
    candidate = verify_replay(replay, baseline, env=env)
    executable = resolve_companion_python(baseline, env=env)
    bundle = load_json(output)
    if env.get("CV_THEME_PRIVATE_SNAPSHOT"):
        snapshot = load_json(absolute_path(env["CV_THEME_PRIVATE_SNAPSHOT"], "CV_THEME_PRIVATE_SNAPSHOT"))
        # Clean initial trees need only public hashes; never embed a user's private patch.
        if not snapshot["worktree_patch"] and not snapshot["staged_entries"]:
            bundle["preservation_snapshot"] = snapshot
            atomic_json(output, bundle)
    else:
        snapshot = bundle.get("preservation_snapshot")
        require(
            isinstance(snapshot, dict) and snapshot.get("worktree_patch") == "" and not snapshot.get("staged_entries"),
            "missing private snapshot or complete public clean-tree preservation evidence",
        )
    if bundle.get("status") == "complete":
        historical = {key: value for key, value in bundle.items() if key != "history"}
        bundle.setdefault("history", []).append(historical)
        bundle["status"] = "provisional"
        atomic_json(output, bundle)
    receipt = bundle.get("companion_receipt") if require_committed else None
    require(not require_committed or receipt is not None, "missing companion scoped commit receipt")
    binding = check_delivery_tree(root, candidate, baseline, snapshot, receipt=receipt)
    if require_committed:
        validate_core_receipt(bundle.get("core_receipt", {}), core_root())
    before_files = archive_files(root, baseline["revision"])
    core_files = {p: v for p, v in working_files(core_root()).items() if p in replay["core_inventory"]}
    commands = []
    run_id = uuid.uuid4().hex
    with tempfile.TemporaryDirectory(prefix="cv-plan06-delivered-") as temporary:
        companion, core = Path(temporary) / "tabler-test", Path(temporary) / "django-crud-views"
        write_tree(candidate, companion)  # delivered bytes matched above; excludes preserved private configuration
        write_tree(core_files, core)
        _, origin_command = probe_origins(executable, companion, core, candidate, core_files, runner=runner)
        commands.append(origin_command)
        focused = runner(
            [executable, "example/manage.py", "test", *FOCUSED_TESTS, "--parallel", "4", "--verbosity", "2"],
            companion,
            env=isolated_env(companion, core),
        )
        commands.append(focused)
        suite_result(focused, passing=True)
        # Always rerun owned-form AND label-floor. The browser loads the same script-root baseline/runtime record.
        for case in ("owned-form", "label-floor"):
            browser = runner(
                [
                    "node",
                    str(core_root() / "tests/browser/theme-adoption.cjs"),
                    "--case",
                    case,
                    "--delivered-source",
                    str(root),
                    "--output",
                    str(output),
                ],
                core_root(),
                env={**env, "CV_THEME_PROBE_RUN_ID": run_id},
            )
            commands.append(browser)
            require(browser["exit_code"] == 0, f"delivered {case} browser failed")
    bundle = load_json(output)  # browser merged its partial form_probe
    form = bundle.get("form_probe", {})
    require(form.get("run_id") == run_id, "stale partial form probe: missing current execution identity")
    validate_phase_evidence(form, candidate, before_files, complete=False)
    bindings = {
        **binding,
        "runtime_sha256": digest(baseline["runtime"]),
        "config_sha256": digest(baseline["test_configuration"]),
        "core_sha256": digest(replay["core_inventory"]),
    }
    require(form.get("bindings") == bindings, "stale partial form probe")
    require(
        check_delivery_tree(root, candidate, baseline, snapshot, receipt=receipt) == binding,
        "delivered source changed during verification",
    )
    record = {
        "status": "passed",
        "run_id": run_id,
        "bindings": bindings,
        "commands": commands,
        "assertions": [{"id": "complete-delivered-source-and-fresh-probes", "passed": True}],
        "actions": form["actions"],
        "cancel_no_url": form["cancel_no_url"],
        "cases": form["cases"],
        "test_nodes": form["test_nodes"],
        "adoption": form["adoption"],
    }
    slot = "committed_probe" if require_committed else "delivered_probe"
    merged = merge_delivery(output, slot, record)
    validate_bundle(merged, bindings, committed=require_committed)
    return merged


def delivered_probe(root, baseline, replay, output, *, require_committed=False, env=None, runner=command_record):
    """Retain truthful failed attempts without promoting prior partial evidence."""
    commands = []

    def recording_runner(*args, **kwargs):
        record = runner(*args, **kwargs)
        commands.append(record)
        return record

    try:
        return _delivered_probe(
            root, baseline, replay, output, require_committed=require_committed, env=env, runner=recording_runner
        )
    except (EvidenceError, KeyError, OSError, ValueError) as exc:
        bundle = load_json(output) if Path(output).exists() else {"schema": 1}
        slot = "committed_probe" if require_committed else "delivered_probe"
        bundle[slot] = {"status": "failed", "commands": commands, "error": sanitize(str(exc))}
        bundle["status"] = "failed"
        atomic_json(output, bundle)
        raise


FINAL_PYTHONS = {
    "django42-current": ("tests-3-12-django-4-2", "4.2", False),
    "django52-current": ("tests-3-12-django-5-2", "5.2", False),
    "django42-floor": ("crispy_floor-3-12-django-4-2", "4.2", True),
    "django60-floor": ("crispy_floor-3-12-django-6-0", "6.0", True),
    "example": ("tests-3-12-django-5-2", "5.2", False),
}
FINAL_COMMANDS = {
    "javascript": ["node", "node_modules/vitest/vitest.mjs", "run", "--maxWorkers=2"],
    "fragments": ["node", "node_modules/vitest/vitest.mjs", "run", "--config", "vitest.integration.config.js"],
    "modal-focus": ["node", "tests/browser/modal-focus.cjs", "--output", PHASE_DIR + "/09-evidence/modal-focus.json"],
    "conditional-formsets": [
        "node",
        "tests/browser/conditional-formsets.cjs",
        "--case",
        "lifecycle",
        "--output",
        PHASE_DIR + "/09-evidence/conditional-formsets.json",
    ],
    "docs": [".venv/bin/mkdocs", "build", "--strict"],
    "lint": [".venv/bin/ruff", "check", "src", "tests", "examples"],
    "format": [".venv/bin/ruff", "format", "--check", "src", "tests", "examples"],
    "whitespace": ["git", "diff", "--check"],
    "configuration": [
        "env",
        "-u",
        "CV_THEME_PYTHON",
        "-u",
        "CV_FOCUS_PYTHON",
        "node",
        "--test",
        "tests/browser/theme-adoption-config.test.cjs",
    ],
}
FLOOR_EXCLUSION = "tests/test1/test_form_buttons_golden.py::test_filter_form_baseline"


def final_inventory():
    return inventory(
        {
            p: v
            for p, v in working_files(core_root()).items()
            if p.startswith(("src/", "tests/", "docs/", "examples/"))
            or p
            in {
                "noxfile.py",
                "pyproject.toml",
                "package.json",
                "package-lock.json",
                "mkdocs.yml",
                "vitest.config.js",
                "vitest.integration.config.js",
                "CHANGELOG.md",
            }
        }
    )


def final_commands():
    commands = dict(FINAL_COMMANDS)
    for name, (environment, _series, floor) in FINAL_PYTHONS.items():
        selection = ["-c", "examples/bootstrap5/pytest.ini", "examples/bootstrap5"] if name == "example" else ["tests"]
        commands[name] = [f".nox/{environment}/bin/python", "-m", "pytest", *selection, "-n", "4", "-q"]
        if floor:
            commands[name] += ["--deselect", FLOOR_EXCLUSION]
        commands[name] += [f"--junitxml={PHASE_DIR}/09-evidence/{name}.xml"]
    return commands


def validate_final_gates(report, expected_inventory):
    require(report.get("source_inventory") == expected_inventory, "stale final source inventory")
    gates = report.get("gates", {})
    for name, argv in final_commands().items():
        gate = gates.get(name, {})
        require(gate.get("source_sha256") == digest(expected_inventory), f"stale {name} source binding")
        record = gate.get("command", {})
        log = validate_log(record)
        require(record.get("argv") == argv and record.get("cwd") == str(core_root()), f"substituted {name} command")
        require(record["exit_code"] == 0 and gate.get("status") == "passed", f"nonpassing {name}")
        require(record.get("duration_seconds", -1) >= 0, f"missing {name} duration")
        if name in FINAL_PYTHONS:
            environment, series, floor = FINAL_PYTHONS[name]
            runtime = gate.get("runtime", {})
            preflight = gate.get("preflight", {})
            validate_log(preflight)
            require(
                preflight["exit_code"] == 0 and json.loads(preflight["stdout"]) == runtime,
                f"missing actual {name} runtime probe",
            )
            require(
                runtime.get("executable") == str(core_root() / f".nox/{environment}/bin/python"),
                f"wrong {name} interpreter",
            )
            require(
                runtime.get("core_module") == str(core_root() / "src/crud_views/__init__.py"),
                f"unsupported {name} source import",
            )
            versions = runtime.get("versions", {})
            require(versions.get("Django", "").startswith(series + "."), f"wrong {name} Django series")
            if floor:
                require(
                    versions.get("django-crispy-forms") == "2.0" and versions.get("crispy-bootstrap5") == "2023.10",
                    f"wrong {name} floor",
                )
            xml = gate.get("junit", "")
            require(gate.get("junit_sha256") == digest(xml.encode()), f"tampered {name} JUnit")
            try:
                cases = ET.fromstring(xml).findall(".//testcase")
            except ET.ParseError as exc:
                raise EvidenceError(f"invalid {name} JUnit") from exc
            require(
                cases and not any(c.find("failure") is not None or c.find("error") is not None for c in cases),
                f"zero/failing {name} cases",
            )
            skipped = [c for c in cases if c.find("skipped") is not None]
            require(
                all(
                    name != "example"
                    and series != "6.0"
                    and c.get("classname") == "tests.test1.test_assets"
                    and c.get("name") == "test_django6_builtin_csp_nonce_roundtrip"
                    for c in skipped
                ),
                f"required {name} case skipped",
            )
            require(len(cases) - len(skipped) > 0, f"zero passing {name} cases")
            if name != "example":
                for module in (
                    "theme_form_ownership",
                    "theme_label_modes",
                    "theme_action_groups",
                    "theme_form_requests",
                    "theme_adoption_docs",
                    "alerts",
                    "button_classes",
                ):
                    require(
                        any(c.get("classname") == "tests.test1.test_" + module for c in cases),
                        f"missing {name} required module {module}",
                    )
                require(
                    not floor
                    or not any(
                        c.get("classname") == "tests.test1.test_form_buttons_golden"
                        and c.get("name") == "test_filter_form_baseline"
                        for c in cases
                    ),
                    "floor exclusion differs",
                )
            require(
                gate.get("passed") == len(cases) - len(skipped) and gate.get("skipped") == len(skipped),
                f"incorrect {name} counts",
            )
        elif name in {"javascript", "fragments"}:
            require(re.search(r"Tests\s+\d+ passed", log), f"zero {name} cases")
        elif name == "configuration":
            require(re.search(r"# pass [1-9]\d*", log) and "# fail 0" in log, "nonpassing fresh-shell configuration")
        elif name in {"modal-focus", "conditional-formsets"}:
            browser = gate.get("browser", {})
            require(browser and gate.get("browser_sha256") == digest(browser), f"missing {name} browser evidence")
            require(browser.get("passed") is True, f"failed {name} browser evidence")
            require(
                browser.get("completed") is True and not browser.get("error") and browser.get("pageErrors") == [],
                f"incomplete {name} browser evidence",
            )
            cases = browser.get("cases", [])
            expected = (
                {
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
                }
                if name == "modal-focus"
                else {"stock:lifecycle", "native:lifecycle"}
            )
            identities = [c.get("id") if name == "modal-focus" else f"{c.get('theme')}:{c.get('id')}" for c in cases]
            require(len(identities) == len(expected) and set(identities) == expected, f"missing {name} cases")
            for case in cases:
                require(
                    case.get("passed") is True
                    and not case.get("skipped")
                    and case.get("assertions")
                    and all(a.get("passed") is True for a in case["assertions"]),
                    f"skipped/failing {name} case",
                )
            hashes = browser.get("sourceHashes", {})
            require(
                hashes
                and all(
                    (core_root() / path).is_file() and digest((core_root() / path).read_bytes()) == value
                    for path, value in hashes.items()
                ),
                f"stale {name} browser source",
            )
    require(
        report.get("coverage_limits", {}).get("django60_current_pack") == "untested-no-cached-runtime",
        "current-pack Django 6.0 limit missing",
    )
    return True


def validate_committed_delivery(bundle, baseline, replay, candidate, *, env=None):
    root = resolve_recorded_source(manifest=baseline, env=env)
    binding = check_delivery_tree(
        root, candidate, baseline, bundle.get("preservation_snapshot", {}), receipt=bundle.get("companion_receipt", {})
    )
    bindings = {
        **binding,
        "runtime_sha256": digest(baseline["runtime"]),
        "config_sha256": digest(baseline["test_configuration"]),
        "core_sha256": digest(replay["core_inventory"]),
    }
    validate_bundle(bundle, bindings, committed=True)
    before = archive_files(root, baseline["revision"])
    for slot in ("form_probe", "delivered_probe", "committed_probe"):
        validate_phase_evidence(bundle[slot], candidate, before, complete=False)
    receipt = bundle.get("core_receipt", {})
    validate_core_receipt(receipt, core_root())
    paths = receipt["evidence_paths"]
    delivery_path = PHASE_DIR + "/10-companion-delivery.json"
    commit = git(core_root(), "log", "-1", "--format=%H", "--", delivery_path).decode().strip()
    require(
        set(git(core_root(), "diff-tree", "--no-commit-id", "--name-only", "-r", commit).decode().splitlines())
        == set(paths),
        "core evidence commit swept unrelated paths",
    )
    require(
        git(core_root(), "rev-parse", commit + "^").decode().strip() == receipt["before_head"],
        "wrong core evidence parent",
    )
    for path in paths:
        require(
            git(core_root(), "show", commit + ":" + path) == (core_root() / path).read_bytes(),
            "uncommitted/tampered core delivery evidence",
        )
    require(load_json(core_root() / delivery_path) == bundle, "substituted delivery bundle")
    return {"core_evidence_commit": commit, "companion_commit": bundle["companion_receipt"]["after_head"]}


def validate_final_sources(baseline, browser, replay, delivery, *, env=None):
    candidate = verify_replay(replay, baseline, env=env)
    # Candidate and fresh replay must independently satisfy the complete source/suite/branch contract.
    verify_replay({**browser, "patch": replay["patch"], "patch_sha256": replay["patch_sha256"]}, baseline, env=env)
    require(browser.get("core_inventory") == replay["core_inventory"], "stale candidate core evidence")
    validate_final_assets(browser.get("assets", []), replay.get("assets", []))
    return validate_committed_delivery(delivery, baseline, replay, candidate, env=env)


def validate_final_assets(candidate, replay):
    expected = {
        "https://cdn.jsdelivr.net/npm/@tabler/core@1.6.1/dist/" + path
        for path in ("css/tabler.min.css", "js/tabler-theme.min.js", "js/tabler.min.js")
    }
    expected.add("https://code.jquery.com/jquery-3.7.1.js")
    maps = []
    for rows in (candidate, replay):
        by_url = {row.get("url"): row for row in rows}
        require(len(rows) == len(by_url) and set(by_url) == expected, "missing/duplicate actual asset")
        require(
            all(
                row.get("status") == 200
                and re.fullmatch(r"[a-f0-9]{64}", row.get("sha256", ""))
                and row.get("sri256")
                and row.get("sri384")
                for row in rows
            ),
            "incomplete actual asset content",
        )
        maps.append(by_url)
    require(maps[0] == maps[1], "candidate/replay asset mismatch")


def check_final(report, *, env=None):
    validate_final_gates(report, final_inventory())
    for name in FINAL_PYTHONS:
        recorded = report["gates"][name]["runtime"]
        actual = runtime_probe(recorded["executable"])
        require(
            actual["prefix"] == recorded["prefix"]
            and all(actual["versions"].get(k) == v for k, v in recorded["versions"].items()),
            f"changed {name} runtime since execution",
        )
    phase = core_root() / PHASE_DIR
    receipts = validate_final_sources(
        load_json(phase / BASELINE_NAME),
        load_json(phase / "07-browser-results.json"),
        load_json(phase / REPLAY_NAME),
        load_json(phase / "10-companion-delivery.json"),
        env=env,
    )
    artifacts = {
        name: digest((phase / name).read_bytes())
        for name in (
            BASELINE_NAME,
            REPLAY_NAME,
            "07-browser-results.json",
            "10-companion-delivery.json",
            "07-TABLER-HANDOFF.md",
            "07-tabler-adaptation.patch",
        )
    }
    require(report.get("artifacts") == artifacts, "stale final evidence artifact binding")
    return {"status": "automated-passed", "acceptance": "pending-human-observations", **receipts}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--capture-baseline", action="store_true")
    modes.add_argument("--check-baseline", action="store_true")
    modes.add_argument("--verify-replay", action="store_true")
    modes.add_argument("--check-final", action="store_true")
    parser.add_argument("--delivered-source")
    parser.add_argument("--require-committed", action="store_true")
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        require(
            args.capture_baseline
            or args.check_baseline
            or args.verify_replay
            or args.delivered_source
            or args.check_final,
            "choose baseline, replay or delivered-source validation",
        )
        require(
            not args.delivered_source or not (args.capture_baseline or args.check_baseline),
            "baseline modes cannot validate delivery",
        )
        require(not args.require_committed or args.delivered_source, "require-committed needs delivered-source")
        if args.check_final:
            result = check_final(load_json(args.output))
        elif args.capture_baseline:
            result = capture_baseline(args.output)
        elif args.check_baseline:
            check_baseline(load_json(args.output))
            result = {"status": "baseline-validated"}
        else:
            baseline = load_json(core_root() / PHASE_DIR / BASELINE_NAME)
            if args.verify_replay and not args.delivered_source:
                verify_replay(load_json(args.output), baseline)
                result = {"status": "replay-validated"}
            else:
                root = resolve_recorded_source(args.delivered_source, manifest=baseline)
                replay = load_json(core_root() / PHASE_DIR / REPLAY_NAME)
                result = delivered_probe(root, baseline, replay, args.output, require_committed=args.require_committed)
        print(json.dumps({"status": result["status"]}))
        return 0
    except (EvidenceError, KeyError, OSError, ValueError, SyntaxError) as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
