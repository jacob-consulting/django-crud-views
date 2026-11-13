"""Bounded, source-bound release checks for phase 06.30; no dependency installation."""

import argparse
import copy
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
PHASE = ROOT / ".planning/phases/06.30-queryset-driven-conditional-fields-360"
BRIDGE = """
const fs=require('node:fs'), r=require(process.argv[1]);
const x=JSON.parse(fs.readFileSync(0,'utf8'));
if(x.record) r.validateEvidence(x.record,x.target,x.sources,r.fingerprint(x.sources));
else console.log(JSON.stringify(r.fingerprint(x.sources,!!x.docs)));
"""
VERSIONS = """
import importlib.metadata as m, json, pathlib, platform, crud_views
print(json.dumps({'python':platform.python_version(),'source':str(pathlib.Path(crud_views.__file__).resolve()),
    **{n:m.version(n) for n in ['Django','django-crispy-forms','crispy-bootstrap5']}}))
"""


def invoke(command, cwd=ROOT, env=None, data=None):
    return subprocess.run(command, cwd=cwd, env=env, input=data, text=True, capture_output=True, check=False)


def bridge(sources, **kwargs):
    result = invoke(
        ["node", "-e", BRIDGE, str(ROOT / "tests/browser/queryset-conditional.cjs")],
        data=json.dumps({"sources": sources, **kwargs}),
    )
    if result.returncode:
        raise ValueError(result.stderr)
    return json.loads(result.stdout) if result.stdout.strip() else None


def sources_from(downstream=None):
    upstream = Path(os.environ.get("CV_QUERYSET_UPSTREAM", ROOT)).resolve()
    if upstream != ROOT:
        raise ValueError("CV_QUERYSET_UPSTREAM must identify the executing checkout")
    downstream = Path(downstream or os.environ.get("CV_QUERYSET_DOWNSTREAM", ROOT.parent / "tabler-test")).resolve()
    for root in [upstream, downstream]:
        result = invoke(["git", "rev-parse", "--show-toplevel"], cwd=root)
        if result.returncode or Path(result.stdout.strip()).resolve() != root:
            raise ValueError(f"Not a repository root: {root}")
    return {"upstream": str(upstream), "downstream": str(downstream)}


def environment(sources):
    return {
        **os.environ,
        # Command specs own test selection; shell defaults must not narrow a release gate.
        "PYTEST_ADDOPTS": "",
        "PYTHONDONTWRITEBYTECODE": "1",
        "NO_COLOR": "1",
        "CV_QUERYSET_UPSTREAM": sources["upstream"],
        "CV_QUERYSET_DOWNSTREAM": sources["downstream"],
        "CV_FRAGMENT_PYTHON": str(ROOT / ".nox/tests-3-12-django-5-2/bin/python"),
        "PYTHONPATH": os.pathsep.join(
            [str(ROOT / "src"), str(Path(sources["downstream"]) / "src"), str(ROOT / "examples/bootstrap5")]
        ),
    }


def command_specs(sources):
    downstream = Path(sources["downstream"])
    selection = sorted(str(p.relative_to(ROOT)) for p in (ROOT / "tests/test1").glob("test_conditional*.py"))
    selection += sorted(str(p.relative_to(ROOT)) for p in (ROOT / "tests/test1").glob("test_formsets_compact*.py"))
    specs = []

    def add(name, command, kind=None, cwd=ROOT, python=None, series=None, floor=False):
        specs.append(
            {
                "id": name,
                "command": [str(x) for x in command],
                "cwd": str(cwd),
                "kind": kind,
                "python": str(python) if python else None,
                "series": series,
                "floor": floor,
            }
        )

    for session, series, floor in [
        ("tests-3-12-django-5-2", "5.2", False),
        ("tests-3-12-django-4-2", "4.2", False),
        ("tests-3-12-django-6-0", "6.0", False),
        ("crispy_floor-3-12-django-4-2", "4.2", True),
        ("crispy_floor-3-12-django-6-0", "6.0", True),
    ]:
        python = ROOT / ".nox" / session / "bin/python"
        targets = ["tests"] if series == "5.2" else selection
        add(
            session,
            [python, "-m", "pytest", *targets, "-n", "4", "-q", "-rs", "-p", "no:cacheprovider"],
            "pytest",
            python=python,
            series=series,
            floor=floor,
        )
    python = ROOT / ".nox/tests-3-12-django-6-0/bin/python"
    add(
        "django6-csp",
        [
            python,
            "-m",
            "pytest",
            "tests/test1/test_assets.py::test_django6_builtin_csp_nonce_roundtrip",
            "-q",
            "-p",
            "no:cacheprovider",
        ],
        "pytest",
        python=python,
        series="6.0",
    )
    for name, command, kind in [
        ("npm-tree", ["npm", "ls", "--depth=0"], None),
        ("javascript-unit", ["npm", "test"], "vitest"),
        ("javascript-integration", ["npm", "run", "test:integration"], "vitest"),
    ]:
        add(name, command, kind)
    python = ROOT / ".venv/bin/python"
    pytest = [python, "-m", "pytest", "-c", "examples/bootstrap5/pytest.ini"]
    add(
        "examples", [*pytest, "examples/bootstrap5", "-n", "2", "-q", "-p", "no:cacheprovider"], "pytest", python=python
    )
    add(
        "docs-links",
        [
            *pytest,
            "examples/bootstrap5/test_docs_sync.py",
            "examples/bootstrap5/test_doc_links.py",
            "-n",
            "2",
            "-q",
            "-p",
            "no:cacheprovider",
        ],
        "pytest",
        python=python,
    )
    add(
        "mkdocs-strict",
        [
            python,
            "-c",
            "import subprocess,sys,tempfile; "
            "\nwith tempfile.TemporaryDirectory(prefix='cv-docs-') as d: "
            "subprocess.run([sys.executable,'-m','mkdocs','build','--strict','--site-dir',d],check=True)",
        ],
        python=python,
    )
    migration = (
        "import os; os.environ['DJANGO_SETTINGS_MODULE']='project.settings'; "
        "from django.conf import settings; settings.DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3',"
        "'NAME':':memory:'}}; import django; django.setup(); from django.core.management import call_command; "
        "call_command('makemigrations',check=True,dry_run=True)"
    )
    add("migrations", [python, "-c", migration], python=python)
    scoped = [
        "src/crud_views/lib/conditional",
        "src/crud_views/lib/formsets/compact.py",
        "src/crud_views/checks.py",
        *selection,
        "tests/browser/verify_queryset_release.py",
        "tests/browser/queryset_conditional_server.py",
        "tests/browser/queryset_downstream_server.py",
        "examples/bootstrap5/queryset_conditional",
        "examples/bootstrap5/project/features.py",
        "examples/bootstrap5/project/templatetags/example_tags.py",
    ]
    for name, mode in [("ruff", ["check"]), ("ruff-format", ["format", "--check"])]:
        add(name, [python, "-m", "ruff", *mode, *scoped])
    python = downstream / ".venv/bin/python"
    add(
        "downstream-apps",
        [
            python,
            "example/manage.py",
            "test",
            "django_tabler",
            "dashboard",
            "sales",
            "catalog",
            "roastery",
            "shipping",
            "showcase",
            "--parallel",
            "2",
        ],
        "django",
        cwd=downstream,
        python=python,
    )
    add(
        "downstream-checks",
        [python, "example/manage.py", "check", "--fail-level", "WARNING"],
        cwd=downstream,
        python=python,
    )
    add(
        "downstream-theme",
        [
            python,
            "-m",
            "pytest",
            "tests/crud_views_tabler",
            "--ds",
            "tests.crud_views_tabler.settings",
            "-q",
            "-p",
            "no:cacheprovider",
        ],
        "pytest",
        cwd=downstream,
        python=python,
    )
    return specs


def counts(output, kind):
    output = re.sub(r"\x1b\[[0-9;]*m", "", output)
    patterns = {"pytest": r"(\d+) passed", "django": r"Ran (\d+) tests?", "vitest": r"Tests\s+(\d+) passed"}
    matches = re.findall(patterns[kind], output)
    return int(matches[-1]) if matches else 0


def validate_result(result):
    if result.get("environment", {}).get("PYTEST_ADDOPTS") != "":
        raise ValueError("Missing or unsafe effective PYTEST_ADDOPTS policy")
    if result["exit"] != 0:
        raise ValueError(f"Failed command: {result.get('id')}: exit {result['exit']}")
    if result["kind"]:
        actual = counts(result["output"], result["kind"])
        if actual < 1 or actual != result["tests"]:
            raise ValueError("Missing, zero or inconsistent test count")
        output = result["output"]
        # The full 5.2 suite cannot exercise Django 6's CSP middleware. Require the exact existing reason;
        # every affected feature/downstream selection still rejects all skips, and django6-csp runs it on 6.0.
        if result.get("id") == "tests-3-12-django-5-2" and re.search(
            r"SKIPPED \[1\] tests/test1/test_assets.py:\d+: built-in CSP middleware requires Django 6.0", output
        ):
            output = re.sub(r"\b1 skipped\b", "known Django 6-only CSP skip", output)
        if re.search(r"\b[1-9]\d* (skipped|failed|errors?|xfailed|xpassed|todo)\b|skipped=[1-9]", output):
            raise ValueError("Required tests skipped or failed")


def check_browser(record, target, sources):
    selected = {**sources, "downstream": sources["downstream"] if target == "downstream" else None}
    bridge(selected, record=record, target=target)
    import hashlib

    for capture in record["captures"]:
        if hashlib.sha256(Path(capture["path"]).read_bytes()).hexdigest() != capture["sha256"]:
            raise ValueError("Capture changed")
    if Path(record["isolation"]["temporary"]).exists():
        raise ValueError("Browser temporary directory still exists")


def check_evidence(record, sources):
    if record["sources"] != sources or record["sourceHashes"] != bridge(sources):
        raise ValueError("Stale runtime source hashes or different checkout")
    if record["docsHashes"] != bridge(sources, docs=True):
        raise ValueError("Stale documentation checks")
    expected = command_specs(sources)
    if [r["id"] for r in record["commands"]] != [s["id"] for s in expected]:
        raise ValueError("Missing, duplicate or substituted required command")
    for result, spec in zip(record["commands"], expected, strict=True):
        if any(result[key] != value for key, value in spec.items()):
            raise ValueError(f"Command specification changed: {spec['id']}")
        if result["environment"]["CV_QUERYSET_UPSTREAM"] != sources["upstream"]:
            raise ValueError("Required source-binding environment changed")
        validate_result(result)
        if spec["python"]:
            validate_runtime(result["runtime"], spec)
    for target in ("upstream", "downstream"):
        check_browser(record["browsers"][target], target, sources)
    if record["selfTests"]["exit"] != 0 or record["selfTests"]["assertions"] < 30:
        raise ValueError("Release negative controls missing")


def validate_runtime(runtime, spec):
    if runtime["source"] != str(ROOT / "src/crud_views/__init__.py"):
        raise ValueError("Imported crud_views is not this checkout")
    if spec["series"] and not runtime["Django"].startswith(spec["series"] + "."):
        raise ValueError("Wrong Django series")
    if spec["floor"] and (runtime["django-crispy-forms"], runtime["crispy-bootstrap5"]) != ("2.0", "2023.10"):
        raise ValueError("Wrong crispy floor pins")


def run_command(spec, sources):
    env = environment(sources)
    if spec["id"].startswith(("tests-", "crispy_floor-", "django6-")):
        env["PYTHONPATH"] = str(ROOT / "src")
    result = {
        **spec,
        "started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "environment": {
            k: env[k]
            for k in (
                "PYTHONPATH",
                "PYTEST_ADDOPTS",
                "PYTHONDONTWRITEBYTECODE",
                "CV_QUERYSET_UPSTREAM",
                "CV_QUERYSET_DOWNSTREAM",
                "CV_FRAGMENT_PYTHON",
            )
        },
    }
    print(f"RUN {spec['id']}", flush=True)
    if spec["python"]:
        probe = invoke([spec["python"], "-c", VERSIONS], cwd=spec["cwd"], env=env)
        if probe.returncode:
            raise ValueError(probe.stderr)
        result["runtime"] = json.loads(probe.stdout)
        validate_runtime(result["runtime"], spec)
    started = time.monotonic()
    process = invoke(spec["command"], cwd=spec["cwd"], env=env)
    result.update(
        exit=process.returncode, output=process.stdout + process.stderr, seconds=round(time.monotonic() - started, 2)
    )
    result["tests"] = counts(result["output"], spec["kind"]) if spec["kind"] else None
    print(f"RESULT {spec['id']}: exit={result['exit']} tests={result['tests']} seconds={result['seconds']}", flush=True)
    return result


def check_resume(previous, current):
    if previous["sources"] != current["sources"] or previous["docsHashes"] != current["docsHashes"]:
        raise ValueError("Cannot resume different source/documentation inputs")
    changed = {
        p
        for p in previous["sourceHashes"] | current["sourceHashes"]
        if previous["sourceHashes"].get(p) != current["sourceHashes"].get(p)
    }
    if changed - {"upstream/tests/browser/verify_queryset_release.py"}:
        raise ValueError("Cannot reuse results after product/test/asset changes")
    for result in previous.get("commands", []):
        if result.get("environment", {}).get("PYTEST_ADDOPTS") != "":
            raise ValueError("Cannot resume results without safe effective PYTEST_ADDOPTS policy")
    return sorted(changed)


def run(output, sources, resume_harness=False):
    record = {
        "sources": sources,
        "sourceHashes": bridge(sources),
        "docsHashes": bridge(sources, docs=True),
        "commands": [],
        "browsers": {},
        "provenance": {},
    }
    previous = json.loads(output.read_text()) if resume_harness else None
    if previous:
        record["resumedFrom"] = {
            "changed": check_resume(previous, record),
            "sourceHashes": previous["sourceHashes"],
            "provenance": previous["provenance"],
            "reused": [],
            "reason": "Harness-only correction; all product and test inputs remain byte-identical.",
        }
    for label, root in sources.items():
        record["provenance"][label] = {
            "head": invoke(["git", "rev-parse", "HEAD"], root).stdout.strip(),
            "status": invoke(["git", "status", "--short"], root).stdout,
            "diff": invoke(["git", "diff", "HEAD", "--", ".", ":(exclude).planning"], root).stdout,
        }
    try:
        for index, spec in enumerate(command_specs(sources)):
            old = previous["commands"][index] if previous and index < len(previous["commands"]) else None
            if (
                old
                and old["exit"] == 0
                and spec["id"] not in {"javascript-integration", "ruff", "ruff-format"}
                and all(old.get(k) == v for k, v in spec.items())
            ):
                result = old
                record["resumedFrom"]["reused"].append(spec["id"])
                print(f"REUSE byte-identical inputs: {spec['id']}", flush=True)
            else:
                result = run_command(spec, sources)
            record["commands"].append(result)
            validate_result(result)
        for target in ("upstream", "downstream"):
            browser_path = PHASE / f"evidence/08-{target}.json"
            try:
                check_browser(json.loads(browser_path.read_text()), target, sources)
            except (ValueError, KeyError, OSError):
                print(f"REFRESH stale {target} browser evidence", flush=True)
                process = invoke(
                    [
                        "node",
                        "tests/browser/queryset-conditional.cjs",
                        "--target",
                        target,
                        "--output",
                        str(browser_path),
                    ],
                    env=environment(sources),
                )
                if process.returncode:
                    raise ValueError(process.stdout + process.stderr) from None
            record["browsers"][target] = json.loads(browser_path.read_text())
            check_browser(record["browsers"][target], target, sources)
        record["selfTests"] = {"exit": 0, "assertions": self_test(sources)}
        check_evidence(record, sources)
    except Exception as error:
        record["failure"] = str(error)
        raise
    finally:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(record, indent=2) + "\n")
    print(f"ACCEPTANCE_OK {output}")


def self_test(sources=None):
    assertions = 0

    def rejects(callback, name):
        nonlocal assertions
        try:
            callback()
        except (ValueError, AssertionError):
            assertions += 1
            return
        raise AssertionError(f"Accepted {name}")

    sources = sources or sources_from()
    # Run pytest itself: xdist can omit deselection counts, so output text cannot prove scope.
    with tempfile.TemporaryDirectory(prefix="cv-pytest-options-") as temporary:
        fixture = Path(temporary) / "test_selection.py"
        fixture.write_text("def test_selected(): pass\ndef test_required(): pass\n")
        with patch.dict(os.environ, {"PYTEST_ADDOPTS": "-k test_selected"}):
            result = invoke(
                [sys.executable, "-m", "pytest", "-c", os.devnull, str(fixture), "-q", "-p", "no:cacheprovider"],
                cwd=temporary,
                env=environment(sources),
            )
        assert result.returncode == 0 and counts(result.stdout, "pytest") == 2, result.stdout + result.stderr
        assertions += 1
    valid = {
        "exit": 0,
        "kind": "pytest",
        "output": "2 passed in 0.1s",
        "tests": 2,
        "environment": {"PYTEST_ADDOPTS": ""},
    }
    validate_result(valid)
    for name, changes in [
        ("failed exit", {"exit": 1}),
        ("zero tests", {"tests": 0, "output": "no tests ran"}),
        ("skipped behavior", {"output": "2 passed, 1 skipped"}),
        ("invented count", {"tests": 3}),
        ("unrecorded pytest policy", {"environment": {}}),
        ("inherited pytest selection", {"environment": {"PYTEST_ADDOPTS": "-k test_selected"}}),
    ]:
        result = copy.deepcopy(valid)
        result.update(changes)
        rejects(lambda result=result: validate_result(result), name)
    known_skip = {
        **valid,
        "id": "tests-3-12-django-5-2",
        "output": "2 passed, 1 skipped\nSKIPPED [1] tests/test1/test_assets.py:332: "
        "built-in CSP middleware requires Django 6.0",
    }
    validate_result(known_skip)
    assertions += 1
    rejects(lambda: validate_result({**known_skip, "id": "downstream-apps"}), "skip outside full core")
    rejects(
        lambda: validate_result({**known_skip, "output": known_skip["output"].replace("1 skipped", "2 skipped")}),
        "additional skip beside known CSP",
    )
    rejects(lambda: validate_result({**known_skip, "output": "2 passed, 1 skipped\nunrelated reason"}), "unknown skip")
    sources = sources or sources_from()
    for target in ("upstream", "downstream"):
        original = json.loads((PHASE / f"evidence/08-{target}.json").read_text())
        selected = {**sources, "downstream": sources["downstream"] if target == "downstream" else None}
        original["sourceHashes"] = bridge(selected)
        for name in ("missing scenario", "failed assertion", "stale hash"):
            changed = copy.deepcopy(original)
            if name == "missing scenario":
                changed["scenarios"].pop()
            elif name == "failed assertion":
                changed["scenarios"][0]["assertions"][0]["passed"] = False
            else:
                changed["sourceHashes"] = {}
            rejects(lambda changed=changed, target=target: check_browser(changed, target, sources), f"{target} {name}")
    # Real temporary Git manifests prove content, additions and deletions; never edit the working repositories.
    with tempfile.TemporaryDirectory(prefix="cv-fingerprint-") as temporary:
        fixture = Path(temporary)
        subprocess.run(["git", "init", "-q", temporary], check=True)
        roots = {"upstream": temporary, "downstream": None}
        families = [
            "src/module.py",
            "src/templates/test.html",
            "src/static/app.js",
            "tests/test_probe.py",
            "tests/browser/host.py",
            "examples/app/models.py",
            "examples/app/migrations/0001.py",
            "examples/project/settings.py",
            "examples/project/urls.py",
            "example/sales/forms.py",
            "package.json",
            "package-lock.json",
            "pyproject.toml",
            "uv.lock",
            "noxfile.py",
        ]
        for name in families:
            file = fixture / name
            file.parent.mkdir(parents=True, exist_ok=True)
            before = bridge(roots)
            file.write_text("initial")
            added = bridge(roots)
            assert before != added, name
            file.write_text("changed")
            assert bridge(roots) != added, name
            file.unlink()
            assert bridge(roots) == before, name
            assertions += 1
        for name in ["CHANGELOG.md", "docs/crud_views_upstream_findings_roastery.md", ".planning/report.json"]:
            file = fixture / name
            file.parent.mkdir(parents=True, exist_ok=True)
            before = bridge(roots)
            file.write_text("report-only reconciliation")
            assert bridge(roots) == before, name
            assertions += 1
        before = bridge(roots, docs=True)
        (fixture / "docs/guide.md").write_text("changed prose")
        assert bridge(roots, docs=True) != before
        assert bridge(roots) == {}
        assertions += 1
    wrong = {"source": "/wrong/src/crud_views/__init__.py"}
    rejects(lambda: validate_runtime(wrong, {"series": None, "floor": False}), "wrong import path")
    fixture = {"sources": sources, "docsHashes": {}, "sourceHashes": {"upstream/src/a.py": "old"}}
    for env in ({}, {"PYTEST_ADDOPTS": "-m selected"}):
        previous = {**fixture, "commands": [{**valid, "environment": env}]}
        rejects(lambda previous=previous: check_resume(previous, fixture), "resume unverified pytest policy")
    rejects(
        lambda: check_resume(fixture, {**fixture, "sourceHashes": {"upstream/src/a.py": "new"}}),
        "resume product change",
    )
    rejects(lambda: check_resume(fixture, {**fixture, "docsHashes": {"docs/a.md": "new"}}), "resume docs change")
    print(f"SELF_TEST_OK release: {assertions} named checks", flush=True)
    return assertions


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test", action="store_true")
    mode.add_argument("--run", action="store_true")
    mode.add_argument("--check-evidence", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--resume-harness", action="store_true", help="Reuse successful commands only after a harness-only correction"
    )
    args = parser.parse_args()
    try:
        if args.self_test:
            self_test()
        elif args.run:
            if not args.output:
                parser.error("--run requires --output")
            run(args.output, sources_from(), args.resume_harness)
        else:
            evidence = json.loads(args.check_evidence.read_text())
            check_evidence(evidence, sources_from(evidence["sources"]["downstream"]))
            print("EVIDENCE_OK: complete, current and source-bound")
    except (ValueError, KeyError, OSError, AssertionError) as error:
        print(f"ACCEPTANCE_FAILED: {error}", file=sys.stderr)
        sys.exit(1)
