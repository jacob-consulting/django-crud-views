"""Independent bounded plan22 reviewer controls; never acceptance capture."""

import copy
import datetime
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path("/home/alex/projects/alex/django-crud-views")
assert subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=ROOT, text=True).strip() == str(ROOT)
P = ROOT / ".planning/phases/06.4-conditional-and-formset-correctness-lifecycle"
D = Path(__file__).resolve().parent
RUNNER = P / "15-evidence/run.py"
PY = ROOT / ".nox/crispy_floor-3-12-django-6-0/bin/python"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load(p):
    return json.loads(Path(p).read_text())


def dump(p, x):
    return Path(p).write_text(json.dumps(x, sort_keys=True))


packet = load(P / "21-evidence/results.json")
original = load(P / "18-evidence/results.json")
handoff = load(P / "22-evidence/handoff.json")
spec = importlib.util.spec_from_file_location("reviewed_runner", RUNNER)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
manifest = runner.source()
results = {
    "actor": "/root/execute_22/code_review",
    "started": datetime.datetime.now(datetime.UTC).isoformat(),
    "commands": [],
}
protected = [
    P / x
    for x in [
        "15-evidence/run.py",
        "15-evidence/test_runner.py",
        "18-evidence/results.json",
        "18-evidence/source-manifest.json",
        "21-evidence/results.json",
        "21-evidence/source-manifest.json",
        "22-evidence/handoff.json",
    ]
]
protected += list((ROOT / ".planning/ui-reviews/06.4-gap-repair").glob("*.png"))
results["baseline_hashes"] = {str(p.relative_to(ROOT)): sha(p) for p in protected}
oldfiles = original["source_manifest"]["files"]
newfiles = manifest["files"]
results["continuity"] = {
    "source_sha256": manifest["sha256"],
    "paths": len(newfiles),
    "added": sorted(set(newfiles) - set(oldfiles)),
    "removed": sorted(set(oldfiles) - set(newfiles)),
    "changed": [p for p in oldfiles if oldfiles[p] != newfiles.get(p)],
    "identical_gate_ids": [k for k in original["gates"] if original["gates"][k] == packet["gates"][k]],
}
gate = packet["gates"]["evidence-self-tests"]
observed = re.findall(r"^test_\w+ \((test_runner\.\w+\.test_\w+)\) \.\.\. ok$", gate["stdout"] + gate["stderr"], re.M)
results["fresh_self_tests"] = {
    "selected": len(gate["selected_tests"]),
    "observed_ok": len(observed),
    "exact_current_identity_match": sorted(observed) == runner.self_test_ids() == gate["selected_tests"],
    "started": gate["started"],
    "finished": gate["finished"],
    "command": gate["command"],
    "returncode": gate["returncode"],
}
results["historical_controls"] = {
    "fresh_count": len(packet["checker_control_evidence"]),
    "original_count": len(original["checker_control_evidence"]),
    "positive_observation": packet["checker_positive_control"],
}


def execute(name, argv, expectation, env=None):
    start = datetime.datetime.now(datetime.UTC).isoformat()
    result = subprocess.run([str(v) for v in argv], cwd=ROOT, env=env, capture_output=True, text=True, timeout=60)
    row = {
        "name": name,
        "command": result.args,
        "started": start,
        "finished": datetime.datetime.now(datetime.UTC).isoformat(),
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "expected": expectation,
    }
    row["matched"] = (
        (result.returncode == 0 and result.stderr == "" and expectation in result.stdout)
        if expectation.startswith(("PHASE64", "{"))
        else (
            result.returncode == 1 and result.stdout == "" and result.stderr == "MATRIX_REJECTED: " + expectation + "\n"
        )
    )
    results["commands"].append(row)
    dump(D / "outcomes.json", results)
    print(name, result.returncode, row["matched"], result.stderr.strip() or result.stdout.strip(), flush=True)
    return result


def stock(p):
    return next(
        c
        for c in p["gates"]["conditional-browser"]["browser"]["cases"]
        if c["id"] == "gap-ambiguity" and c["theme"] == "stock"
    )


mutations = [
    (
        "original-missing-controls",
        lambda p: p.pop("checker_control_evidence"),
        "Checker control evidence inventory incomplete",
    ),
    (
        "original-all-success",
        lambda p: [
            r.update(returncode=0, stdout="PHASE64_MATRIX_OK", stderr="")
            for r in p["checker_control_evidence"].values()
        ],
        "Checker control exit invalid: exit-code",
    ),
    (
        "original-empty-stock",
        lambda p: stock(p).__setitem__("captures", []),
        "Conditional capture inventory invalid: stock",
    ),
    (
        "original-stale-stock",
        lambda p: stock(p)["captures"][0].__setitem__("sha256", "0" * 64),
        "Conditional capture digest mismatch: desktop",
    ),
    (
        "boolean-exit",
        lambda p: p["checker_control_evidence"]["exit-code"].__setitem__("returncode", True),
        "Checker control exit invalid: exit-code",
    ),
    (
        "wrong-command",
        lambda p: p["checker_control_evidence"]["exit-code"]["command"].__setitem__(0, "/bin/true"),
        "Checker control command invalid: exit-code",
    ),
    (
        "wrong-diagnostic",
        lambda p: p["checker_control_evidence"]["exit-code"].__setitem__(
            "stderr", "MATRIX_REJECTED: Missing/stale source manifest\n"
        ),
        "Checker control diagnostic mismatch: exit-code",
    ),
    (
        "extra-record",
        lambda p: p["checker_control_evidence"].__setitem__("extra", {}),
        "Checker control evidence inventory incomplete",
    ),
    (
        "boolean-device",
        lambda p: stock(p)["captures"][0]["device"].__setitem__("deviceScaleFactor", True),
        "Conditional capture device mismatch: desktop",
    ),
    (
        "path-traversal",
        lambda p: stock(p)["captures"][0].__setitem__(
            "path", ".planning/ui-reviews/06.4-gap-repair/../06.4-gap-repair/desktop.png"
        ),
        "Conditional capture path escape: desktop",
    ),
    (
        "font-observation-missing",
        lambda p: stock(p)["captures"][0]["icons"]["glyphs"][0].__setitem__("family", ""),
        "Conditional capture icon observations invalid: desktop",
    ),
    (
        "nonfinite-glyph",
        lambda p: stock(p)["captures"][0]["icons"]["glyphs"][0].__setitem__("width", float("nan")),
        "Conditional capture icon observations invalid: desktop",
    ),
    (
        "retained-timestamp",
        lambda p: p["gates"]["javascript"].__setitem__("started", "2026-11-01T19:00:00Z"),
        "Retained gate changed: javascript",
    ),
    (
        "filtered-js",
        lambda p: p["gates"]["javascript"]["command"].insert(3, "-t=one"),
        "javascript: wrong quality command",
    ),
    (
        "non-strict-docs",
        lambda p: p["gates"]["strict-docs"]["command"].remove("--strict"),
        "strict-docs: wrong quality command",
    ),
]
execute(
    "clean-check", [PY, RUNNER, "--check", "--output", P / "21-evidence/results.json"], "PHASE64_MATRIX_OK 20 gates"
)
execute(
    "clean-handoff",
    [PY, RUNNER, "--check-handoff", P / "22-evidence/handoff.json"],
    '{"disposition": "not-ready", "ready": false, "structurally_valid": true}',
)
with tempfile.TemporaryDirectory(prefix="owned-", dir=D) as tmp:
    temp = Path(tmp)
    out = temp / "packet.json"
    hp = temp / "handoff.json"
    dump(temp / "source-manifest.json", manifest)
    for name, mutate, diagnostic in mutations:
        changed = copy.deepcopy(packet)
        mutate(changed)
        dump(out, changed)
        hc = copy.deepcopy(handoff)
        hc["packet"] = {"path": str(out.relative_to(ROOT)), "sha256": sha(out)}
        dump(hp, hc)
        execute(name + ":check", [PY, RUNNER, "--check", "--output", out], diagnostic)
        execute(name + ":handoff", [PY, RUNNER, "--check-handoff", hp], diagnostic)
    dump(out, packet)
    out.write_text(out.read_text().replace('"schema": 3', '"schema": 3, "schema": 3', 1))
    hc["packet"]["sha256"] = sha(out)
    dump(hp, hc)
    for mode, args in [("check", ["--check", "--output", out]), ("handoff", ["--check-handoff", hp])]:
        execute("duplicate-key:" + mode, [PY, RUNNER, *args], "Duplicate JSON key: schema")
    for name, mutate, diagnostic in [
        ("false-ready", lambda h: h.__setitem__("ready", True), "Handoff readiness contradicts open obligations"),
        (
            "invented-human",
            lambda h: h["human_checks"]["H1"].__setitem__("actor", "invented reviewer"),
            "Pending human has an invented response",
        ),
    ]:
        hc = copy.deepcopy(handoff)
        mutate(hc)
        dump(hp, hc)
        execute(name, [PY, RUNNER, "--check-handoff", hp], diagnostic)
    env = dict(os.environ, CV_FOCUS_PYTHON="/missing/plan22-review-python")
    execute(
        "invalid-runtime-preflight",
        [PY, RUNNER, "--run", "--only", "strict-docs", "--output", temp / "never-created.json"],
        "CV_FOCUS_PYTHON='/missing/plan22-review-python': selected runtime unavailable",
        env=env,
    )
    assert not (temp / "never-created.json").exists()
    execute(
        "historical-check-ignores-current-override",
        [PY, RUNNER, "--check", "--output", P / "21-evidence/results.json"],
        "PHASE64_MATRIX_OK 20 gates",
        env=env,
    )
results["finished"] = datetime.datetime.now(datetime.UTC).isoformat()
results["protected_unchanged"] = all(sha(ROOT / p) == digest for p, digest in results["baseline_hashes"].items())
dump(D / "outcomes.json", results)
print(
    "FINAL",
    len(results["commands"]),
    "matched",
    sum(r["matched"] for r in results["commands"]),
    "unchanged",
    results["protected_unchanged"],
    flush=True,
)
