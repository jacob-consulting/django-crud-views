"""Bounded canonical verifier checks; only temporary diagnostic fixtures are written."""

import copy
import datetime
import hashlib
import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
P = ROOT / ".planning/phases/06.4-conditional-and-formset-correctness-lifecycle"
PY = ROOT / ".nox/crispy_floor-3-12-django-6-0/bin/python"
RUNNER = P / "15-evidence/run.py"
assert subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip() == str(ROOT)
spec = importlib.util.spec_from_file_location("canonical_runner", RUNNER)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
packet = runner.load_json(P / "21-evidence/results.json")
origin = runner.load_json(P / "18-evidence/results.json")
handoff = runner.load_json(P / "22-evidence/handoff.json")
manifest = runner.source()
old = origin["source_manifest"]["files"]
new = manifest["files"]
changed = sorted(k for k in old.keys() & new.keys() if old[k] != new[k])
retained = [k for k, v in packet["gate_origins"].items() if v == "retained"]
assert packet["source_manifest"] == manifest
assert set(old) == set(new)
assert changed == sorted(str(P.relative_to(ROOT) / "15-evidence" / f) for f in ("run.py", "test_runner.py"))
assert len(retained) == 17 and all(packet["gates"][k] == origin["gates"][k] for k in retained)
result = {
    "actor": "/root/canonical_verify",
    "started": datetime.datetime.now(datetime.UTC).isoformat(),
    "source_sha256": manifest["sha256"],
    "packet_sha256": hashlib.sha256((P / "21-evidence/results.json").read_bytes()).hexdigest(),
    "continuity": {
        "paths": len(new),
        "unchanged": len(new) - len(changed),
        "changed": changed,
        "added": [],
        "deleted": [],
        "retained_exact": len(retained),
    },
    "runs": [],
}


def execute(name, args, expected):
    started = datetime.datetime.now(datetime.UTC).isoformat()
    run = subprocess.run([str(PY), str(RUNNER), *map(str, args)], cwd=ROOT, capture_output=True, text=True, timeout=10)
    item = {
        "name": name,
        "command": run.args,
        "started": started,
        "finished": datetime.datetime.now(datetime.UTC).isoformat(),
        "returncode": run.returncode,
        "stdout": run.stdout,
        "stderr": run.stderr,
    }
    if expected == "positive":
        assert run.returncode == 0, item
    elif expected == "overflow":
        assert (
            run.returncode == 1 and not run.stdout and "OverflowError: int too large to convert to float" in run.stderr
        ), item
        assert "MATRIX_REJECTED:" not in run.stderr, item
    else:
        assert run.returncode == 1 and not run.stdout and run.stderr == "MATRIX_REJECTED: " + expected + "\n", item
    result["runs"].append(item)


execute("clean-aggregate", ["--check", "--output", P / "21-evidence/results.json"], "positive")
execute("clean-handoff-before-report-replacement", ["--check-handoff", P / "22-evidence/handoff.json"], "positive")
mutations = [
    ("missing-controls", "Checker control evidence inventory incomplete"),
    ("successful-controls", "Checker control exit invalid: exit-code"),
    ("missing-captures", "Conditional capture inventory invalid: stock"),
    ("stale-capture", "Conditional capture digest mismatch: desktop"),
    ("oversized-glyph", "overflow"),
]
with tempfile.TemporaryDirectory(prefix="canonical-probe-", dir=Path(__file__).parent) as td:
    temp = Path(td)
    (temp / "source-manifest.json").write_text(json.dumps(manifest))
    for name, expected in mutations:
        mutated = copy.deepcopy(packet)
        if name == "missing-controls":
            mutated.pop("checker_control_evidence")
        elif name == "successful-controls":
            for value in mutated["checker_control_evidence"].values():
                value.update(returncode=0, stdout="PHASE64_MATRIX_OK", stderr="")
        else:
            case = next(
                c
                for c in mutated["gates"]["conditional-browser"]["browser"]["cases"]
                if c["id"] == "gap-ambiguity" and c["theme"] == "stock"
            )
            if name == "missing-captures":
                case["captures"] = []
            elif name == "stale-capture":
                case["captures"][0]["sha256"] = "0" * 64
            else:
                case["captures"][0]["icons"]["glyphs"][0]["width"] = 10**400
        out = temp / "packet.json"
        out.write_text(json.dumps(mutated))
        bound = copy.deepcopy(handoff)
        bound["packet"] = {"path": str(out.relative_to(ROOT)), "sha256": hashlib.sha256(out.read_bytes()).hexdigest()}
        hp = temp / "handoff.json"
        hp.write_text(json.dumps(bound))
        execute(name + ":aggregate", ["--check", "--output", out], expected)
        execute(name + ":handoff", ["--check-handoff", hp], expected)
result["finished"] = datetime.datetime.now(datetime.UTC).isoformat()
print(json.dumps(result, indent=2))
