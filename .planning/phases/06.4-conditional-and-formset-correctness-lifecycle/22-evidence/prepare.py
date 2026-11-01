"""Prepare plan22's qualified handoff without changing historical attribution."""

import copy
import datetime
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
P = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent


def ref(path):
    return {"path": str(path.relative_to(ROOT)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


old = json.loads((P / "19-evidence/handoff.json").read_text())
data = copy.deepcopy(old)
packet = json.loads((P / "21-evidence/results.json").read_text())
data.update(
    version="06.4-22/v1",
    recorded=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    source_sha256=packet["source_manifest"]["sha256"],
    runner_sha256=packet["runner_sha256"],
    packet=ref(P / "21-evidence/results.json"),
    source_manifest=ref(P / "21-evidence/source-manifest.json"),
    ready=False,
)
data["history"] = {
    "handoff": ref(P / "19-evidence/handoff.json"),
    "reports": copy.deepcopy(old["reports"]),
    "findings": copy.deepcopy(old["findings"]),
    "new_findings": copy.deepcopy(old["new_findings"]),
    "security_accounting": copy.deepcopy(old["security_accounting"]),
    "qualification": "Original actor/time/source and bounded dispositions remain historical; none is relabeled current.",
}
data["applicability"] = ref(P / "21-evidence/applicability.md")
data["reports"] = {
    name: {
        **ref(P / filename),
        "status": "pending" if name != "verification" else "open",
        "context": context,
    }
    for name, filename, context in (
        ("code", "06.4-REVIEW.md", "Current independent review pending; original bounded closures preserved under history."),
        ("security", "06.4-SECURITY.md", "Current independent ASVS1/high reassessment pending; no automatic risk acceptance."),
        ("ui", "06.4-UI-REVIEW.md", "24/24 historical scope only; original attribution preserved under history; H1 pending."),
        ("verification", "06.4-VERIFICATION.md", "Historical gaps_found 8/10; orchestrator owns independent re-verification and final hash rebind."),
    )
}
for identity, item in data["findings"].items():
    historical = copy.deepcopy(item)
    for key in ("actor", "recorded", "response", "source_sha256", "evidence_files", "review"):
        item.pop(key, None)
    item["status"] = "pending" if historical["status"] == "closed" else "open"
    item["historical_status"] = historical["status"]
    item["context"] = "Original bounded disposition preserved in history; awaiting actual independent current-source applicability outcome."
    item["plans"] = list(dict.fromkeys(item.get("plans", []) + ["20", "21", "22"]))
for identity, item in data["new_findings"].items():
    item["current_disposition"] = "pending-independent-review"
    item["repair_evidence"] = [data["packet"], data["applicability"]]
    data["findings"][identity] = {
        "status": "open", "review_ids": [identity], "gap": "G6",
        "threats": copy.deepcopy(data["findings"]["G6"]["threats"]),
        "plans": ["20", "21", "22"], "requirements": ["LIFE-01", "LIFE-02"],
        "evidence": [{"gate": "evidence-self-tests"}, {"gate": "conditional-browser"}],
        "context": "Repaired in plan20/21; awaiting actual independent outcome.",
    }
data["findings"]["G6"]["review_ids"] = ["WR-01", "WR-02", "WR-03", "WR-04"]
for identity in ("G6", "WR-01", "WR-02", "WR-03", "WR-04"):
    data["findings"][identity]["threats"] = [f"T-06.4-{n}" for n in ("22", "28", "29", "31", "33")]
for identity, item in data["threats"].items():
    item["historical_independent_disposition"] = item.get("independent_disposition", "open")
    item["current_review"] = "pending"
for number, component in (
    (37, "corruption subprocess evidence and control bootstrap"),
    (38, "conditional screenshot file/path/hash/device observations"),
    (39, "bounded source-diff retained execution refresh"),
    (40, "independent report attribution and canonical handoff"),
):
    data["threats"][f"T-06.4-{number}"] = {
        "status": "open", "severity": "high", "independent_disposition": "pending",
        "component": component, "current_review": "pending",
    }
data["checker_controls"] = {
    "packet_field": "checker_control_evidence", "control_count": len(packet["checker_control_evidence"]),
    "self_test_gate": "evidence-self-tests", "selected_tests": packet["gates"]["evidence-self-tests"].get("selected", []),
    "bootstrap": "Each mutation is checked by a real --check subprocess under record-local mode; clean complete positive control is separate.",
}
data["security_accounting"] = {
    "total": len(data["threats"]), "historical_total": 37, "historical_closed": 31,
    "historical_open_total": 6, "historical_open_blocking_high": 5, "historical_open_nonblocking_medium": 1,
    "current_independent_review": "pending", "new_threats": [f"T-06.4-{i}" for i in range(37, 41)],
    "machine_status_qualification": "Historical individually closed threats remain pending at schema1 machine level while overall security remains open; no attribution is refreshed by copying.",
}
data["independent_reports"] = {"historical": copy.deepcopy(old["independent_reports"]), "current": "pending"}
data["next_gate"] = "Independent code/security reassessment, then orchestrator-owned canonical verification/hash rebind and actual H1/H2 dispositions; all31 flags remain unresolved."
data["canonical_reverification"] = {
    "owner": "orchestrator independent gsd-verifier after plan22 SUMMARY",
    "status": "pending", "preserve_historical_report": True,
    "exclude_from_covered_files": str((OUT / "handoff.json").relative_to(ROOT)),
    "reason": "Handoff embeds canonical report digest; including it in that report's covered_files would create circular binding.",
    "final_rebind_owner": "orchestrator, after canonical report is written",
}
(OUT / "handoff.json").write_text(json.dumps(data, indent=2) + "\n")

appendices = {
    "06.4-MATRIX.md": """\n\n## Plan22 reconciliation — 2026-11-01\n\nThe repaired [plan21 packet](21-evidence/results.json) resolves20 gates: **17 retained,3 fresh**, not another product matrix. [Applicability](21-evidence/applicability.md) binds824 source paths:822 unchanged, only15-evidence/run.py and test_runner.py changed; no additions/deletions. Retained gate objects are JSON-identical to18-evidence, with original commands, times, counts and runtime facts. The fresh checker gate has62 tests; Ruff check/format and33 real rejected corruption subprocesses plus a clean positive control are fresh. Historical48,220 Python passes, JS347/integration2 and browser36/305 retain their original execution windows.\n\n[Plan22 handoff](22-evidence/handoff.json) links concrete gate/case identities, the source/runner manifests and original report hashes. WR-03/04 and T22/28/31/33 plus new37–40 await genuine independent reassessment; preparation closes none. H1 pending, H2 flagged-unverified and all31 fallback assumptions remain explicit; ready=false. UI24/24 remains historical. Canonical verification and final digest rebind belong to the orchestrator.\n""",
    "06.4-VALIDATION.md": """\n\n## Plan22 executed mapping — 2026-11-01\n\n22-01 validates the qualified current [handoff](22-evidence/handoff.json) using15-evidence/run.py --check-handoff;22-02 independently reassesses checker/capture predicates and the bounded refresh, then checks21-evidence/results.json and handoff;22-03 hands H1/H2 and canonical verification to their actual owners and checks the final handoff. These mappings grant no compliance verdict: **status partial; nyquist_compliant false** remain until independent reassessment.\n\nFresh plan21 work is62 checker tests, two Ruff gates and33 negative subprocess controls plus a positive check.17 product/browser/docs/integration gate records remain exact historical executions; [applicability](21-evidence/applicability.md) describes the complete824-path continuity proof. No new matrix/browser run, physical-device test, assistive-technology approval or H2 enforcement descriptor is claimed.\n""",
    "06.4-ACCEPTANCE.md": """\n\n## Plan22 review preparation — 2026-11-01\n\nThe [current qualified handoff](22-evidence/handoff.json) binds the [repaired packet](21-evidence/results.json), [source applicability](21-evidence/applicability.md), all19 decisions and all31 flagged-unresolved assumptions. Original G1–G5/CR-01–05/WR-01–02 closures remain historical within their exact scope; actual current independent confirmation is pending. WR-03/04/G6 and linked threats are not closed by a green packet. Six previously open threats comprise five high and one medium; new37–40 require separate accounting.\n\nD-01–03 exact name/ambiguity/ancestor ownership; D-04–07 native visibility, focus, unsaved values and actions; D-08–10 field-aware persistence, server-disabled precedence and errors; D-11–12 validation/identity before saves; D-13–14 initialization/retry; D-15 carried behavior; D-16 A19-only; D-17 coordinates/{html, rows}/{prefix, rows}/outer-event/projection; D-18 jQuery/authorization/atomic/skip-purge boundaries; D-19 leaves/labels/escaping/Cancel/focus/paired migrations and Phase7 inventory all remain retained. No implementation is reworked.\n\nH1 stays pending actual stock/native usability and accessibility judgment. H2 stays **flagged-unverified**: **Switching a conditional file field off must not silently authorize deletion of the stored file content.** UI24/24, stock screenshots, storage spies and prior-phase approval supply no human disposition. ImageField remains reference-only and application save/signal/storage/custom hooks remain outside demonstrated guarantees. Keep A8/A25/#210/jQuery, broader Guardian#286/custom-PK/backend bounds. Ready=false; no phase completion, Phase7 advancement, merge or release follows preparation.\n""",
}
for filename, text in appendices.items():
    path = P / filename
    if text not in path.read_text():
        path.write_text(path.read_text() + text)
