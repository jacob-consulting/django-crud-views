"""Additional independent staging, origin and numeric boundary controls."""

import copy
import datetime
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path("/home/alex/projects/alex/django-crud-views")
assert subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=ROOT, text=True).strip() == str(ROOT)
P = ROOT / ".planning/phases/06.4-conditional-and-formset-correctness-lifecycle"
D = Path(__file__).resolve().parent
PY = ROOT / ".nox/crispy_floor-3-12-django-6-0/bin/python"
RUNNER = P / "15-evidence/run.py"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load(p):
    return json.loads(p.read_text())


def dump(p, x):
    return p.write_text(json.dumps(x, sort_keys=True))


packet = load(P / "21-evidence/results.json")
handoff = load(P / "22-evidence/handoff.json")
origin = load(P / "18-evidence/results.json")
rows = []


def run(name, argv):
    start = datetime.datetime.now(datetime.UTC).isoformat()
    result = subprocess.run([str(a) for a in argv], cwd=ROOT, capture_output=True, text=True, timeout=60)
    rows.append(
        {
            "name": name,
            "command": result.args,
            "started": start,
            "finished": datetime.datetime.now(datetime.UTC).isoformat(),
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    )
    dump(D / "boundary-outcomes.json", rows)
    print(name, result.returncode, result.stderr.strip()[-800:] or result.stdout.strip(), flush=True)


with tempfile.TemporaryDirectory(prefix="boundary-", dir=D) as td:
    t = Path(td)
    out = t / "packet.json"
    hp = t / "handoff.json"
    dump(t / "source-manifest.json", packet["source_manifest"])
    for case in [
        "stage-one",
        "stage-two",
        "overflow-glyph",
        "origin-product-change",
        "origin-added-path",
        "origin-removed-path",
    ]:
        p = copy.deepcopy(packet)
        if case == "stage-one":
            p["checker_controls"] = {}
            p["checker_control_evidence"] = {}
            p["gates"]["django4.2-focused"]["returncode"] = 9
        elif case == "stage-two":
            for key in list(p["checker_control_evidence"]):
                if key.startswith("control-"):
                    del p["checker_control_evidence"][key]
                    del p["checker_controls"][key]
            p["checker_control_evidence"]["exit-code"]["command"][0] = "/bin/true"
        elif case == "overflow-glyph":
            c = next(
                c
                for c in p["gates"]["conditional-browser"]["browser"]["cases"]
                if c["id"] == "gap-ambiguity" and c["theme"] == "stock"
            )
            c["captures"][0]["icons"]["glyphs"][0]["width"] = 10**400
        else:
            o = copy.deepcopy(origin)
            m = o["source_manifest"]
            if case == "origin-product-change":
                m["files"]["README.md"] = "0" * 64
            elif case == "origin-added-path":
                m["files"]["tests/invented.py"] = "0" * 64
            else:
                m["files"].pop("README.md")
            m["sha256"] = hashlib.sha256(json.dumps(m["files"], sort_keys=True).encode()).hexdigest()
            od = t / "origin"
            od.mkdir(exist_ok=True)
            dump(od / "results.json", o)
            dump(od / "source-manifest.json", m)
            p["retained_from"] = {
                k: {"path": str(v.relative_to(ROOT)), "sha256": sha(v)}
                for k, v in [("results", od / "results.json"), ("source_manifest", od / "source-manifest.json")]
            }
        dump(out, p)
        h = copy.deepcopy(handoff)
        h["packet"] = {"path": str(out.relative_to(ROOT)), "sha256": sha(out)}
        dump(hp, h)
        for mode, args in [("check", ["--check", "--output", out]), ("handoff", ["--check-handoff", hp])]:
            run(case + ":" + mode, [PY, RUNNER, *args])
