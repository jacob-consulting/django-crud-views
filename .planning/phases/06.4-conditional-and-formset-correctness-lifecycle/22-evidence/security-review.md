---
phase: 06.4-conditional-and-formset-correctness-lifecycle
plan: "22"
status: OPEN_THREATS
reviewed: 2026-11-01T19:43:33.367307+00:00
actor: /root/execute_22/security_review
agent_type: gsd-security-auditor
model: gpt-6-astra
reasoning_effort: xhigh
model_attribution: dispatch configuration confirmed by executor; runtime not independently introspected
asvs_level: 1
block_on: high
threats_total: 41
threats_closed: 38
threats_open: 3
open_total: 3
open_blocking_high: 3
open_nonblocking_medium: 0
accepted_risks: []
source_sha256: d896bc53d2b9bd51be66ddf93282727a72518270ba535ab9a19eae3e33da8490
runner_sha256: dc0594d2ccac677c2e2a45b7eaf1ba8d56cd29bf3c675229e848ab9d9aedf6d5
packet_sha256: 717f3495fbf3a11c4a23f037bece1136727082314854ad3fd371b56ffce40ab0
---

# Plan22 independent ASVS1/high mitigation reassessment

**OPEN_THREATS: 38/41 closed; three high open, zero medium open. No accepted risks or transfers.**

This is the genuine terminal assessment returned by `/root/execute_22/security_review`, typed `gsd-security-auditor`, with executor-confirmed dispatch `gpt-6-astra/xhigh`. Runtime model identity was not independently introspected. Recorded UTC is the auditor's own timestamp above. The auditor independently confirmed `/home/alex/projects/alex/django-crud-views` with `git rev-parse --show-toplevel` and wrote, staged and committed no files. Its developer single-writer contract required the executor to persist this report; the following is a faithful condensed persistence of its returned scope, evidence and dispositions. The executor's subsequent preparation corrections do not retroactively change this review snapshot.

P means `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle`. The authored register contains41 distinct mitigate dispositions. This audit verified that register, rather than performing an unrestricted vulnerability scan. It read repository guidance/configuration, plans20–22 and relevant threat registers, summaries20/21, applicability21, original18/current21 evidence, original19 independent reports, canonical security history, complete current runner/tests and relevant implementation boundaries. No configured auditor skills or project-local skills were present. Config confirms ASVS1/high. It fulfills the actual independent secure-phase lane; final canonical verification remains separately owned.

## Evidence bindings

| Binding | SHA-256 |
|---|---|
| Current logical source map | `d896bc53d2b9bd51be66ddf93282727a72518270ba535ab9a19eae3e33da8490` |
| Current runner | `dc0594d2ccac677c2e2a45b7eaf1ba8d56cd29bf3c675229e848ab9d9aedf6d5` |
| Current checker tests | `530ab85446dfa9fd4c702b3c521066e07b63a2beaaf7ed4426ded142e33e8725` |
| Current21 results | `717f3495fbf3a11c4a23f037bece1136727082314854ad3fd371b56ffce40ab0` |
| Current21 manifest file | `61321dd218c3bfcead5d89eac5f126498ffb09123dabb3c8559f09f1214f1646` |
| Applicability21 | `6720be038f098013989d4f1b3aefea756e13ba44f7480b63ecebd226ed7c338c` |
| Original logical source map | `bc68bdd3b135d8919f400da204eeb6dda6ebbb01f2ceee47d50f2d6655d41601` |
| Original18 results | `a2ae7e5116683ae54b80243ac7c394909512ea922a3c4fe1b72cd7f633b6e674` |
| Original18 manifest file | `160d004bec9883e920b78ea5eacb8c98e1d42903b8b88ec8da9362d47b78f4cf` |
| Original19 security report | `9b68043dfa5eb54bc351c28b5dcc0dfa52fe2b52d655e24ca883dad5f9d4984b` |
| Original19 code report | `1e4e1384618101b31fafb8f24b5c50fa045baa594a35630cf4f57020de4822e4` |
| Prepared22 handoff reviewed | `7f838769155c2cc2257c1f46a40225cda0bbbc8dd8730905a29d202e788d4a08` |
| Preparation script reviewed | `9eef02a87b5373621865f84833a39b484adf7a128acd5cb49b8172f6ed6f8e31` |
| Canonical verification reviewed | `ff6bd89f315e8b664bf5c2c4ffee8129c012cac5dc9a8a5afc7785f015460b10` |

Source/runner/packet/prepared-handoff hashes remained unchanged at the auditor's final snapshot. Later executor metadata changes must carry their own hash/recheck, not this historical snapshot's attribution.

## Open blocking outcomes

| Threat | Category | Severity | Independent outcome |
|---|---|---|---|
| T-06.4-35 | Repudiation | high | OPEN. Attribution/readiness guards exist at runner:1654,1692, but actual H1/H2 and required final independent outcomes remain incomplete. Prepared H1 pending/H2 flagged-unverified/all31 unresolved are honest; guards do not supply outcomes. |
| T-06.4-36 | Tampering | high | OPEN. No genuine H2 enforcement descriptor, demonstrated enforcement route or attributed human disposition. Native storage/reference evidence remains bounded. Conditional implementation/tests and actual handoff H2 were inspected. |
| T-06.4-40 | Repudiation | high | OPEN. Attribution guards/preparation exist, but independent canonical verification and final report hash rebind are still pending. Preparation assigns these steps to the orchestrator; assignment is not execution. Two metadata discrepancies below also require correction. |

Exact unresolved H2 prohibition: **Switching a conditional file field off must not silently authorize deletion of the stored file content.**

No medium threat remains open. The previously open six were five high and one medium; T22/28/33 high and T31 medium are now bounded closed, T35/36 high continue open. New T37 high/T38 medium/T39 high close; new T40 high stays open. Totals: **24 high +14 medium closed;3 high open =41**.

## Newly verified closures

| Threat | Category | Severity | Independent evidence |
|---|---|---|---|
| T-06.4-22 | Repudiation | high | CLOSED, bounded. Exact source/command/selection/outcome checks and detailed-control/capture predicates reached from aggregate and handoff. Four original mutations independently reject through both CLIs. |
| T-06.4-28 | Repudiation | high | CLOSED. runner:1141,1161,1285 validates complete inventories, exact commands, integer exit1, empty stdout and case-specific stderr. Absent/all-success records reject. |
| T-06.4-31 | Repudiation | medium | CLOSED, bounded. runner:919,1089 revalidates stock/native capture inventories, bytes/digests and observations. H1/H2 remain pending; no accessibility judgment granted. |
| T-06.4-33 | Repudiation | high | CLOSED, bounded. Fresh checker gates/controls bind current source; product gates retain original provenance. Missing/corrupt controls/captures reject; exact source and retained-gate continuity independently confirmed. |
| T-06.4-37 | Repudiation | high | CLOSED. Strict duplicate loader runner:190; exact records:1141; staged inventories:1161; actual subprocess generation/positive check:1569. All33 records and captured62test evidence inspected, including duplicate/staging tests. |
| T-06.4-38 | Tampering | medium | CLOSED, bounded. runner:919 validates capture identity/types, viewport/containment/glyph/font, confined distinct paths, current PNG bytes/digests/dimensions. Negative observation/path probes reject. WR-05 below remains fail-closed diagnostic limitation. |
| T-06.4-39 | Repudiation | high | CLOSED. runner:1182,1195,1229,1285 fixes two-file exception, complete source paths/digests, bounded hash-bound origins, exact retained records, selections, fresh gates and controls. Altered origin/runtime/timestamp/fresh completeness probes reject. |

## Retained original31 closures: actual current applicability

Independently recomputed complete maps:824 paths each; zero added/deleted;822 unchanged digests; only runner/tests differ. All17 retained gate objects are JSON-identical to origin18, including commands/times/revisions/selections/nested outcomes. This confirms applicability of prior bounded closures without changing their historical execution provenance. Current implementation reads confirmed the cited mitigations; changed-runner T29 received fresh probes.

Abbreviations: lib = `src/crud_views/lib/`; js = `src/crud_views/static/crud_views/js/`; Python tests in `tests/test1/`. All rows below are CLOSED within their original scope, with disposition mitigate.

| Threat | Category | Severity | Current applicability evidence |
|---|---|---|---|
| T-06.4-01 | Tampering | medium | js/toggle.js:23,88,152 exact ownership/retained state/stale listener detachment. |
| T-06.4-02 | Information disclosure | medium | conditional/layout.py:29 bound name; toggle_group.html:5,10 escaped attributes. |
| T-06.4-03 | Tampering | high | conditional/group.py:163,181,193 native persistence/trusted disabled. |
| T-06.4-04 | Tampering | high | group.py:69,181; persistence tests:276,333 storage spies/retained bytes. Native reference scope; T36 separate. |
| T-06.4-05 | Tampering | high | checks.py:82,164 E312; group.py:74,140 refuses unsupported clearing. |
| T-06.4-06 | Elevation of privilege | high | group.py:142,153,184,195 inherited cleaning/model validation/disabled precedence. |
| T-06.4-07 | Tampering | high | render_tree.py:202,247 reapplies policy after native validation, changed/nested extras. |
| T-06.4-08 | Elevation of privilege | high | render_tree.py:223 authorized queryset/native PK/bound-instance equality. |
| T-06.4-09 | Information disclosure | medium | render_tree.py:246,260 generic deduplicated Invalid row. |
| T-06.4-10 | Tampering | high | formsets.py:359,385 inactive skip/scoped purge; mixins.py:114 routed atomic save. |
| T-06.4-11 | Tampering | medium | js/toggle.js:31,78,99 independent baseline/ancestors. |
| T-06.4-12 | Denial of service | medium | js/toggle.js:68,124 focus fallback/cancelled reset. |
| T-06.4-13 | Tampering | high | js/formset.js:76,507,590 owning form/controller. |
| T-06.4-14 | Tampering | high | js/formset.js:536 reorder; js/modal.js:227 honors cancellation before serialization. |
| T-06.4-15 | Tampering | medium | js/formset.js:10,20,267,329,529 immutable bound identity/native DELETE. |
| T-06.4-16 | Information disclosure | high | formsets/mixins.py:49,71, Guardian auth and formsets.py:411 ancestry before rendering. |
| T-06.4-17 | Tampering | high | formsets.py:455,467,528 sibling/deeper coordinates; original actual round trips. |
| T-06.4-18 | Repudiation | medium | conditional-formsets.cjs:80 exact case/status/source; aggregate additionally checks captures. |
| T-06.4-19 | Tampering | high | conditional-formsets.cjs:243,554 both-theme real markup/forged POST/zero saves. |
| T-06.4-20 | Tampering | medium | migration_docs tests:42,67,92,114,137,184 actual published recipes. |
| T-06.4-21 | Repudiation | medium | PUBLIC-SURFACE:64,89,95 A19-only projection/internal/exclusions; original source unchanged. |
| T-06.4-23 | Tampering | high | views/mixins.py:41,54; formsets/mixins.py:104,114 validation before atomic save. |
| T-06.4-24 | Tampering | high | render_tree.py:202; formsets.py:365 second traversal; original zero-save tests applicable. |
| T-06.4-25 | Repudiation | high | Separate Vitest configs; js-integration test:92 mandatory selected interpreter and retained bridge/runtime cases. |
| T-06.4-26 | Tampering | medium | js/formset.js:10,20,329 and actual DELETE field preserve eligibility. |
| T-06.4-27 | Tampering | medium | js/toggle.js:17,88,152 zero/two/one matches and owned-state recovery. |
| T-06.4-29 | Repudiation | high | runner:252,351 runtime preflight/reuse. Invalid Python fails before subprocess; changed port selection not reusable. |
| T-06.4-30 | Tampering | high | conditional-formsets.cjs:243 both-theme capabilities/ordered POST/database/reclean zero saves. |
| T-06.4-32 | Tampering | medium | migration_docs tests:114,137,184 actual capability/reclean and bounded file semantics. |
| T-06.4-34 | Tampering | high | Unchanged auth/queryset/rollback/skip-purge; exact retained full suites; AUTH-02 A19-only. |
| T-06.4-SC | Tampering | high | Existing stack; dependency/lock inputs unchanged, no installs. Future-install review unexercised. |

## Independent executions

All commands used the existing `.nox/crispy_floor-3-12-django-6-0/bin/python`, current `P/15-evidence/run.py`, confirmed root and `PYTHONDONTWRITEBYTECODE=1`.

Clean actual commands:

```text
run.py --check --output P/21-evidence/results.json
run.py --check-handoff P/22-evidence/handoff.json
```

Both exit0: `PHASE64_MATRIX_OK 20 gates source=d896bc53d2b9bd51be66ddf93282727a72518270ba535ab9a19eae3e33da8490` and `{"disposition":"not-ready","ready":false,"structurally_valid":true}`.

The code-review lane created immutable diagnostic inputs under `22-evidence/code-controls/shared-fixtures/`. This auditor independently verified original packet/handoff hashes, byte-identical current sidecar, exact declared mutation equality, copied handoff differences restricted to packet ref/hash, and fixture inventory hashes before executing. Shared fixture authorship does not replace this auditor's independent observation. No provenance was rewritten to manufacture controls.

For each stem, independently ran both unchanged CLIs: `run.py --check --output <stem>.json` and `run.py --check-handoff <stem>-handoff.json` in that fixture directory.

| Stem / exact mutation | Both actual CLI results |
|---|---|
| missing-control-evidence: omit checker_control_evidence | exit1, empty stdout; MATRIX_REJECTED: Checker control evidence inventory incomplete |
| all-success-control-evidence: every record exit0/stdout PHASE64_MATRIX_OK/stderr empty | exit1, empty stdout; MATRIX_REJECTED: Checker control exit invalid: exit-code |
| empty-stock-captures: stock gap-ambiguity captures=[] | exit1, empty stdout; MATRIX_REJECTED: Conditional capture inventory invalid: stock |
| stale-stock-digest: first stock SHA becomes64 zeroes | exit1, empty stdout; MATRIX_REJECTED: Conditional capture digest mismatch: desktop |

Eight independent CLI runs:2026-11-01T19:41:07.423460–19:41:32.698868 UTC. Fixture inventory SHA `4a13a94748d47e35d50bbbfae561c9cf253b35869c90c95a4468e4ee75d96395`; canonical serialized eight auditor execution records SHA `4839029de83da96564502d38a6ff46f8747aa71314aca5fe9814a5ef3115ed83`. Auditor raw records remained in-memory under its no-write contract; these are its returned observations, not executor-manufactured logs.

Additional read-only inline probes used actual validators on deep in-memory copies:38 intended rejections for control types/diagnostics/commands/inventories, capture absolute/traversal/duplicate/missing paths, device/viewport/overflow/font/glyph/human markers, source product/add/delete, false readiness, unattributed reports/humans, invented pending responses, prohibition changes/resolution and stale canonical hash. Seven further refresh probes rejected missing fresh gate, changed origin hash/outside origin/classification, retained timestamp, effective runtime and incomplete packet. Invalid Python failed before subprocess; changed selection refused reuse. Symlink escape, modified/deleted/non-PNG bytes and duplicate-key CLI coverage were inspected in implementation/captured complete tests, not recreated by this no-write auditor.

## Capture and retained-execution limits

Stock current PNG hashes independently matched: desktop `6af0369c076c37eb02a9e132e6da01fd1b04a52bc1ec428f7e2fc59f8f2b81ef`; mobile `314006515ef104b3a93a7b390aec27addf67733df5b37fc53752e447b731edfe`; tablet `55c2ee11a8e16140abb64a9fe37f55feb07428322e5fa6a4ed9e76f33be16282`. Recorded CSS viewport dimensions1440×900,375×812,768×1024, scale1, client/inner/scroll widths equal;44 loaded glyph observations each with Font Awesome6 Free family. Native captures explicitly empty. These are artifact/record checks, not new visual, physical-device or assistive-technology evaluation.

Inspected plan21 captures contain62 passing checker identities, fresh Ruff check/format,33 exact rejected controls and a clean positive. Full62tests not rerun. Historical48,220 Python,347JS,2integration and36browser/305assertions remain historical. No full product matrix/browser recapture/live server/install.

## Preparation discrepancies and WR-05

The reviewed preparation snapshot had two defects: all new threats were assigned high, although authored T38 is medium; `checker_controls.selected_tests` read nonexistent `gate.selected`, emitting[] rather than the actual62 `selected_tests`. Bootstrap prose incorrectly said record-local mode rather than staged payload/record controls and an ordinary complete positive check. Correct only owned metadata, record its new hash and rerun handoff validation; product/source/plan21 execution evidence remains unaffected. These are preparation discrepancies under open T40, not newly closed outcomes.

WR-05 independently reproduced in memory: glyph width `10**400` raises OverflowError in runner:987 math.isfinite. Code lane actual dual-CLI records were inspected; both exit1/empty stdout/traceback without MATRIX_REJECTED. Boundary log SHA `a89837d0fcca4f4b6dfec0c9b4ba0546ad1e74f6044634ef00546f305f977d8c`. This diagnostic warning fails closed; no acceptance bypass was demonstrated, so authored T38 integrity mitigation remains bounded closed. G6/code warning can separately remain open. A runner fix requires affected checker tests/Ruff/control refresh and renewed complete-source continuity before any retained product reuse.

No unregistered attack surface found. New surfaces map to T37–39; WR-05 maps to the declared capture boundary. All31 fallback assumptions stay unresolved, without being counted as new security threats. Preserve Python3.12.3/Django4.2.30,5.2.18,6.0.9/cached Chromium bounds, exact prior skips/deselections, A19-only AUTH-02, reference-only ImageField and A8/A25/#210/jQuery/broader Guardian/custom-PK/backend exclusions. UI24/24 stays historical.

Persist reports, correct metadata, obtain independent canonical re-verification, then rebind to the actual report hash. Handoff exclusion from canonical covered_files is currently an instruction, not a completed outcome. Genuine H1/H2 remain required. **Final:41total/38closed/3high open/0medium open; threats_open3. No next-phase routing or automatic risk acceptance.**
