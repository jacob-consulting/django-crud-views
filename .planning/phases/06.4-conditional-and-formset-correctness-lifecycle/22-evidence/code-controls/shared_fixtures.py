"""Create retained, explicitly corrupted reviewer fixtures for independent replay."""

import copy
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path("/home/alex/projects/alex/django-crud-views")
assert subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=ROOT, text=True).strip() == str(ROOT)
P = ROOT / ".planning/phases/06.4-conditional-and-formset-correctness-lifecycle"
D = Path(__file__).resolve().parent / "shared-fixtures"
D.mkdir(exist_ok=True)


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def dump(p, x):
    return p.write_text(json.dumps(x, sort_keys=True))


packet = json.loads((P / "21-evidence/results.json").read_text())
handoff = json.loads((P / "22-evidence/handoff.json").read_text())
(D / "source-manifest.json").write_bytes((P / "21-evidence/source-manifest.json").read_bytes())
inventory = {
    "fixture_author": "/root/execute_22/code_review",
    "purpose": "Corrupted reviewer diagnostic inputs; never acceptance evidence",
    "original_packet_sha256": sha(P / "21-evidence/results.json"),
    "original_handoff_sha256": sha(P / "22-evidence/handoff.json"),
    "fixtures": [],
}
for case in ["missing-control-evidence", "all-success-control-evidence", "empty-stock-captures", "stale-stock-digest"]:
    p = copy.deepcopy(packet)
    if case == "missing-control-evidence":
        p.pop("checker_control_evidence")
    elif case == "all-success-control-evidence":
        for r in p["checker_control_evidence"].values():
            r.update(returncode=0, stdout="PHASE64_MATRIX_OK", stderr="")
    else:
        stock = next(
            c
            for c in p["gates"]["conditional-browser"]["browser"]["cases"]
            if c["id"] == "gap-ambiguity" and c["theme"] == "stock"
        )
        if case == "empty-stock-captures":
            stock["captures"] = []
        else:
            stock["captures"][0]["sha256"] = "0" * 64
    target = D / (case + ".json")
    dump(target, p)
    h = copy.deepcopy(handoff)
    h["packet"] = {"path": str(target.relative_to(ROOT)), "sha256": sha(target)}
    hp = D / (case + "-handoff.json")
    dump(hp, h)
    inventory["fixtures"].append(
        {"case": case, "packet": h["packet"], "handoff": {"path": str(hp.relative_to(ROOT)), "sha256": sha(hp)}}
    )
dump(D / "inventory.json", inventory)
print(json.dumps(inventory, indent=2))
