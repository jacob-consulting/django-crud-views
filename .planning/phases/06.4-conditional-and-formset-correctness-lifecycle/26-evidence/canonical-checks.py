"""Independent plan26 replay: capture first, check immutable records, then check a rebound handoff."""

import argparse
import copy
import datetime
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
P = ROOT / ".planning/phases/06.4-conditional-and-formset-correctness-lifecycle"
HERE = Path(__file__).resolve().parent
PY = ROOT / ".nox/crispy_floor-3-12-django-6-0/bin/python"
RUNNER = P / "15-evidence/run.py"
PACKET = P / "24-evidence/results.json"
HANDOFF = P / "24-evidence/handoff.json"
CANONICAL = P / "06.4-VERIFICATION.md"
BEFORE = HERE / "pre-wr05-verification.md"
HANDOFF_BEFORE = HERE / "pre-canonical-handoff.json"
OUTCOMES = HERE / "canonical-outcomes.json"
ACTOR = "/root/canonical_26"
GSD = Path.home() / ".codex/gsd-core/bin/gsd-tools.cjs"
MUTATIONS = {
    "missing-controls": "Checker control evidence inventory incomplete",
    "successful-controls": "Checker control exit invalid: exit-code",
    "missing-captures": "Conditional capture inventory invalid: stock",
    "stale-capture": "Conditional capture digest mismatch: desktop",
    "oversized-width": "Conditional capture icon observations invalid: desktop",
    "oversized-height": "Conditional capture icon observations invalid: desktop",
}
EXCLUDED = {
    str(path.relative_to(ROOT))
    for path in (
        HANDOFF,
        HERE / "final-rebind.json",
        P / "06.4-ACCEPTANCE.md",
        P / "06.4-REVIEW-DISPOSITION.md",
        CANONICAL,
    )
}
STABLE = [
    RUNNER,
    P / "15-evidence/test_runner.py",
    PACKET,
    P / "24-evidence/source-manifest.json",
    P / "24-evidence/applicability.md",
    P / "18-evidence/results.json",
    P / "18-evidence/source-manifest.json",
    P / "25-evidence/code-review.md",
    P / "25-evidence/security-review.md",
    P / "25-evidence/independent-outcomes.json",
    P / "06.4-REVIEW.md",
    P / "06.4-SECURITY.md",
    P / "06.4-VALIDATION.md",
    P / "06.4-UI-REVIEW.md",
    P / "06.4-25-SUMMARY.md",
    Path(__file__).resolve(),
]


def need(condition, message):
    if not condition:
        raise ValueError(message)


def now():
    return datetime.datetime.now(datetime.UTC).isoformat()


def stamp(value):
    parsed = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    need(parsed.utcoffset() == datetime.timedelta(0), "Timestamp must be actual UTC")
    return parsed


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def reference(path):
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path)}


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def metadata(path):
    # Canonical reports use one-line JSON values in YAML frontmatter, as the prior report does.
    result = {}
    for line in path.read_text().split("---", 2)[1].splitlines():
        if line.strip():
            key, value = line.split(":", 1)
            result[key] = json.loads(value.strip())
    return result


def load_runner():
    need(
        subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=ROOT, text=True).strip() == str(ROOT),
        "Checkout root mismatch",
    )
    spec = importlib.util.spec_from_file_location("canonical_runner_26", RUNNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def continuity(runner, packet, manifest):
    origin = runner.load_json(P / "18-evidence/results.json")
    old, new = origin["source_manifest"]["files"], manifest["files"]
    changed = sorted(key for key in old.keys() & new.keys() if old[key] != new[key])
    retained = sorted(key for key, value in packet["gate_origins"].items() if value == "retained")
    need(
        packet["source_manifest"] == manifest == runner.load_json(P / "24-evidence/source-manifest.json"),
        "Current source/packet/sidecar mismatch",
    )
    need(set(old) == set(new), "Source paths added/deleted")
    need(
        changed == sorted(str(P.relative_to(ROOT) / "15-evidence" / name) for name in ("run.py", "test_runner.py")),
        "Source changed beyond exact two checker files",
    )
    need(
        len(retained) == 17 and all(packet["gates"][key] == origin["gates"][key] for key in retained),
        "Retained gates are not exactly equal",
    )
    need(
        packet["capture_request"]["selections"] == origin["capture_request"]["selections"],
        "Effective runtime selections changed",
    )
    return {
        "paths": len(new),
        "unchanged": len(new) - len(changed),
        "changed": changed,
        "added": [],
        "deleted": [],
        "retained_exact": retained,
        "retained_gate_sha256": {key: digest(packet["gates"][key]) for key in retained},
        "source_manifest": manifest,
        "origin_source_manifest": origin["source_manifest"],
        "effective_selections_sha256": digest(packet["capture_request"]["selections"]),
    }


def mutate(packet, name):
    value = copy.deepcopy(packet)
    if name == "missing-controls":
        value.pop("checker_control_evidence")
    elif name == "successful-controls":
        for control in value["checker_control_evidence"].values():
            control.update(returncode=0, stdout="PHASE64_MATRIX_OK", stderr="")
    else:
        case = next(
            case
            for case in value["gates"]["conditional-browser"]["browser"]["cases"]
            if case["id"] == "gap-ambiguity" and case["theme"] == "stock"
        )
        if name == "missing-captures":
            case["captures"] = []
        elif name == "stale-capture":
            case["captures"][0]["sha256"] = "0" * 64
        else:
            dimension = "width" if name == "oversized-width" else "height"
            case["captures"][0]["icons"]["glyphs"][0][dimension] = 10**400
    return value


def inspect_result(item, source_sha, actor=ACTOR):
    name = item["name"]
    need(item["actor"] == actor, "Wrong observation actor")
    need(stamp(item["started"]) <= stamp(item["finished"]), "Reversed execution window")
    need(type(item["returncode"]) is int, "Invalid exit code")
    if name == "clean-aggregate":
        need(
            (item["returncode"], item["stdout"], item["stderr"])
            == (0, f"PHASE64_MATRIX_OK 20 gates source={source_sha}\n", ""),
            "Wrong clean aggregate result",
        )
    elif name in ("clean-handoff-before-report-replacement", "clean-handoff-after-report-rebind"):
        need(item["returncode"] == 0 and item["stderr"] == "", "Clean handoff failed")
        need(
            json.loads(item["stdout"]) == {"structurally_valid": True, "ready": False, "disposition": "not-ready"},
            "Wrong clean handoff result",
        )
    else:
        mutation, mode = name.split(":")
        need(mode in ("aggregate", "handoff"), "Unknown mode")
        need(
            (item["returncode"], item["stdout"], item["stderr"])
            == (1, "", "MATRIX_REJECTED: " + MUTATIONS[mutation] + "\n"),
            "Wrong rejection: " + name,
        )


def execute(name, args, bindings, actor=ACTOR):
    started = now()
    completed = subprocess.run(
        [str(PY), str(RUNNER), *map(str, args)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=10,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    return {
        "name": name,
        "actor": actor,
        "command": completed.args,
        "started": started,
        "finished": now(),
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "bindings": bindings,
    }


def snapshot_bindings(runner):
    handoff = runner.load_json(HANDOFF_BEFORE)
    need(
        handoff["reports"]["verification"]["path"] == str(CANONICAL.relative_to(ROOT))
        and handoff["reports"]["verification"]["sha256"] == sha(BEFORE),
        "Prior canonical binding mismatch",
    )
    for key, report in handoff["reports"].items():
        if key != "verification":
            need(sha(ROOT / report["path"]) == report["sha256"], "Stable snapshot report changed: " + key)
    return handoff


def capture(runner):
    need(not OUTCOMES.exists(), "Completed record exists; never overwrite actual outcomes")
    handoff = snapshot_bindings(runner)
    need(BEFORE.read_bytes() == CANONICAL.read_bytes(), "Live canonical differs before capture")
    need(HANDOFF_BEFORE.read_bytes() == HANDOFF.read_bytes(), "Live handoff differs before capture")
    packet, manifest = runner.load_json(PACKET), runner.source()
    record = {
        "schema": 1,
        "actor": ACTOR,
        "mode": "capture",
        "completed": False,
        "started": now(),
        "command": [str(PY), str(Path(__file__).resolve()), "--capture"],
        "source_sha256": manifest["sha256"],
        "runner_sha256": sha(RUNNER),
        "packet_sha256": sha(PACKET),
        "manifest_sha256": sha(P / "24-evidence/source-manifest.json"),
        "canonical_before": reference(BEFORE),
        "handoff_before": reference(HANDOFF_BEFORE),
        "live_before": {"canonical": reference(CANONICAL), "handoff": reference(HANDOFF), "packet": reference(PACKET)},
        "stable_inputs": [reference(path) for path in STABLE],
        "continuity": continuity(runner, packet, manifest),
        "runs": [],
    }
    try:
        clean = {"packet": reference(PACKET), "handoff": reference(HANDOFF), "canonical": reference(CANONICAL)}
        for name, args in (
            ("clean-aggregate", ["--check", "--output", PACKET]),
            ("clean-handoff-before-report-replacement", ["--check-handoff", HANDOFF]),
        ):
            item = execute(name, args, clean)
            record["runs"].append(item)
            inspect_result(item, manifest["sha256"])
        with tempfile.TemporaryDirectory(prefix="canonical26-", dir=ROOT / ".git") as directory:
            base = Path(directory)
            (base / "source-manifest.json").write_bytes((P / "24-evidence/source-manifest.json").read_bytes())
            for name in MUTATIONS:
                out, hp = base / (name + ".json"), base / (name + "-handoff.json")
                out.write_bytes(encoded(mutate(packet, name)))
                bound = copy.deepcopy(handoff)
                bound["packet"] = reference(out)
                hp.write_bytes(encoded(bound))
                bindings = {
                    "packet": reference(out),
                    "handoff": reference(hp),
                    "sidecar": reference(base / "source-manifest.json"),
                    "canonical": reference(CANONICAL),
                }
                for mode, args in (("aggregate", ["--check", "--output", out]), ("handoff", ["--check-handoff", hp])):
                    item = execute(name + ":" + mode, args, bindings)
                    record["runs"].append(item)
                    inspect_result(item, manifest["sha256"])
        need(record["stable_inputs"] == [reference(path) for path in STABLE], "Capture inputs changed during execution")
        need(
            BEFORE.read_bytes() == CANONICAL.read_bytes() and HANDOFF_BEFORE.read_bytes() == HANDOFF.read_bytes(),
            "Canonical/handoff changed during capture",
        )
        record.update(completed=True, finished=now())
        record["record_sha256"] = digest(record)
        with OUTCOMES.open("xb") as stream:
            stream.write(encoded(record))
    except Exception as error:
        record.update(completed=False, finished=now(), error=str(error))
        failure = HERE / (
            "failed-capture-" + datetime.datetime.now(datetime.UTC).strftime("%Y%m%dT%H%M%S%fZ") + ".json"
        )
        with failure.open("xb") as stream:
            stream.write(encoded(record))
        raise
    return check_recorded(runner)


def check_report(path, record):
    data = metadata(path)
    need(data["status"] in ("passed", "gaps_found", "human_needed"), "Invalid canonical status")
    need(stamp(str(data["verified"])) > stamp(record["finished"]), "Canonical assessment must follow actual replay")
    need(
        data["canonical_replay"]
        == {
            "outcomes": reference(OUTCOMES),
            "canonical_before": reference(BEFORE),
            "handoff_before": reference(HANDOFF_BEFORE),
            "actor": ACTOR,
            "started": record["started"],
            "finished": record["finished"],
        },
        "Canonical report lacks exact immutable replay linkage",
    )
    covered = data["covered_files"]
    need(isinstance(covered, list) and not EXCLUDED.intersection(covered), "Cyclic canonical coverage")
    required = {item["path"] for item in record["stable_inputs"]} | {
        reference(OUTCOMES)["path"],
        reference(BEFORE)["path"],
        reference(HANDOFF_BEFORE)["path"],
    }
    need(required <= set(covered), "Stable evidence omitted from fingerprint")
    need(re.fullmatch(r"v3:sha256:[0-9a-f]{64}", data["covered_digest"]), "Invalid fingerprint metadata")
    result = subprocess.run(
        ["node", str(GSD), "query", "verification.fingerprint", str(P), *covered],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=10,
    )
    need(result.returncode == 0, "Installed fingerprint owner failed: " + result.stderr)
    actual = json.loads(result.stdout)
    need(
        actual["covered_files"] == covered and actual["covered_digest"] == data["covered_digest"],
        "Canonical fingerprint stale",
    )
    return data


def check_recorded(runner, canonical_report=None):
    record = runner.load_json(OUTCOMES)
    sealed = {key: value for key, value in record.items() if key != "record_sha256"}
    need(record["record_sha256"] == digest(sealed), "Recorded observation digest changed")
    need(
        record["schema"] == 1
        and record["completed"] is True
        and record["actor"] == ACTOR
        and record["mode"] == "capture",
        "Missing actual completed capture attribution",
    )
    need(record["command"] == [str(PY), str(Path(__file__).resolve()), "--capture"], "Capture argv changed")
    need(
        record["canonical_before"] == reference(BEFORE) and record["handoff_before"] == reference(HANDOFF_BEFORE),
        "Immutable snapshot bytes changed",
    )
    need(record["stable_inputs"] == [reference(path) for path in STABLE], "Stable source/evidence/report changed")
    packet, manifest = runner.load_json(PACKET), runner.source()
    handoff = snapshot_bindings(runner)
    need(record["continuity"] == continuity(runner, packet, manifest), "Full source/retained continuity changed")
    need(
        record["source_sha256"] == manifest["sha256"]
        and record["runner_sha256"] == sha(RUNNER)
        and record["packet_sha256"] == sha(PACKET)
        and record["manifest_sha256"] == sha(P / "24-evidence/source-manifest.json"),
        "Current logical source/runner/packet/manifest mismatch",
    )
    live = record["live_before"]
    need(
        live
        == {
            "canonical": {"path": str(CANONICAL.relative_to(ROOT)), "sha256": sha(BEFORE)},
            "handoff": {"path": str(HANDOFF.relative_to(ROOT)), "sha256": sha(HANDOFF_BEFORE)},
            "packet": reference(PACKET),
        },
        "Actual pre-replacement live bindings incorrect",
    )
    expected = ["clean-aggregate", "clean-handoff-before-report-replacement"] + [
        name + ":" + mode for name in MUTATIONS for mode in ("aggregate", "handoff")
    ]
    need([item["name"] for item in record["runs"]] == expected, "Missing/extra/reordered observation inventory")
    cursor = stamp(record["started"])
    for item in record["runs"]:
        need(
            cursor <= stamp(item["started"]) <= stamp(item["finished"]) <= stamp(record["finished"]),
            "Observation outside actual sequential capture window",
        )
        cursor = stamp(item["finished"])
        inspect_result(item, manifest["sha256"])
        bindings = item["bindings"]
        if item["name"].startswith("clean-"):
            need(bindings == live, "Clean execution binding differs from actual snapshot")
        else:
            name = item["name"].split(":")[0]
            need(bindings["packet"]["sha256"] == digest(mutate(packet, name)), "Mutation packet digest changed")
            bound = copy.deepcopy(handoff)
            bound["packet"] = bindings["packet"]
            need(bindings["handoff"]["sha256"] == digest(bound), "Mutation handoff binding changed")
            need(bindings["sidecar"]["sha256"] == record["manifest_sha256"], "Mutation sidecar changed")
            need(bindings["canonical"] == live["canonical"], "Mutation canonical binding changed")
            for key in ("packet", "handoff", "sidecar"):
                path = ROOT / bindings[key]["path"]
                need(
                    path.resolve().is_relative_to(ROOT / ".git") and path.parent.name.startswith("canonical26-"),
                    "Unowned mutation transport",
                )
        aggregate = item["name"] == "clean-aggregate" or item["name"].endswith(":aggregate")
        arguments = (
            ["--check", "--output", str(ROOT / bindings["packet"]["path"])]
            if aggregate
            else ["--check-handoff", str(ROOT / bindings["handoff"]["path"])]
        )
        need(item["command"] == [str(PY), str(RUNNER), *arguments], "Recorded command does not exercise binding")
    # Deliberately no validate_handoff or live subprocess here. The old report resolves only to BEFORE.
    if canonical_report:
        check_report(canonical_report, record)
    return {
        "recorded_valid": True,
        "observations": 14,
        "source_sha256": manifest["sha256"],
        "outcomes": reference(OUTCOMES),
        "canonical_report_checked": bool(canonical_report),
    }


def final_handoff(runner, actor):
    check_recorded(runner, CANONICAL)
    record = runner.load_json(OUTCOMES)
    handoff = runner.load_json(HANDOFF)
    data = check_report(CANONICAL, record)
    report = handoff["reports"]["verification"]
    need(
        report["path"] == str(CANONICAL.relative_to(ROOT)) and report["sha256"] == sha(CANONICAL),
        "Live handoff does not bind actual new canonical bytes",
    )
    need(report.get("verdict") == data["status"], "Live canonical verdict mismatch")
    need(report["status"] == ("passed" if data["status"] == "passed" else "open"), "Wrong canonical status mapping")
    bindings = {"canonical": reference(CANONICAL), "handoff": reference(HANDOFF), "packet": reference(PACKET)}
    started = now()
    runs = [
        execute("clean-aggregate", ["--check", "--output", PACKET], bindings, actor),
        execute("clean-handoff-after-report-rebind", ["--check-handoff", HANDOFF], bindings, actor),
    ]
    for item in runs:
        inspect_result(item, record["source_sha256"], actor)
    return {
        "schema": 1,
        "actor": actor,
        "mode": "final-handoff",
        "started": started,
        "finished": now(),
        "canonical": {**reference(CANONICAL), "verdict": data["status"]},
        "handoff": reference(HANDOFF),
        "source_sha256": record["source_sha256"],
        "runner": reference(RUNNER),
        "packet": reference(PACKET),
        "manifest": reference(P / "24-evidence/source-manifest.json"),
        "stable_inputs": record["stable_inputs"],
        "runs": runs,
        "result": json.loads(runs[1]["stdout"]),
        "digest_cycle_exclusions": sorted(EXCLUDED),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--capture", action="store_true")
    mode.add_argument("--check-recorded", action="store_true")
    mode.add_argument("--final-handoff", action="store_true")
    parser.add_argument("--canonical-report", type=Path)
    parser.add_argument("--actor", default=ACTOR, help="Actual invoking actor for the final-handoff observations")
    args = parser.parse_args()
    try:
        need(not args.canonical_report or args.check_recorded, "--canonical-report requires --check-recorded")
        need(args.actor == ACTOR or args.final_handoff, "Only final-handoff permits a different actor")
        runner = load_runner()
        result = (
            capture(runner)
            if args.capture
            else (
                check_recorded(runner, args.canonical_report)
                if args.check_recorded
                else final_handoff(runner, args.actor)
            )
        )
        print(json.dumps(result, indent=2, sort_keys=True))
    except (ValueError, KeyError, TypeError, OSError, subprocess.SubprocessError) as error:
        print("CANONICAL_REJECTED: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
