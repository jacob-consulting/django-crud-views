---
phase: 06.4-conditional-and-formset-correctness-lifecycle
plan: "25"
reviewed: 2026-11-01T20:56:45.272080+00:00
actor: /root/execute_25/code_25
agent_type: gsd-code-reviewer
depth: deep
source_sha256: 5140a723bcffd78d4920086beff692c03935969545226467767b5dd34706e97d
packet_sha256: 0584675c935c5d7a81043a3c412a9bb43df5072532db49682aa5604e575effbd
runner_sha256: 75f8057f55d869ccb9591a0a9868e57d606f9e65f2f0eebffa5fca8d5313ad66
files_reviewed: 2
files_reviewed_list:
  - .planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py
  - .planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/test_runner.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
verdict: passed-bounded
original_findings:
  CR-01: closed-bounded
  CR-02: closed-bounded
  CR-03: closed-bounded
  CR-04: closed-bounded
  CR-05: closed-bounded
  WR-01: closed-bounded
  WR-02: closed-bounded
  WR-03: closed-bounded
  WR-04: closed-bounded
  WR-05: closed-bounded
remaining_gap: G6-canonical-pending
human_checks:
  H1: pending
  H2: flagged-unverified
phase_acceptance: pending
---

# Plan25 independent code review

**WR-05 is closed within its rejection-diagnostic scope.** Both separate oversized dimensions now reject through both real CLI entry points with the exact required diagnostic. The four original WR-03/04 mutations also reject through both entry points. No new code defect was demonstrated in the two reviewed files. This is a passed bounded code report; G6 remains canonical-pending until plan26 independently reassesses it. Phase acceptance remains pending.

Actor `/root/execute_25/code_25` independently read both current checker files in full and traced strict JSON loading → aggregate/retained-origin validation → browser/capture predicate, and handoff → contained bound packet → the same validator. The explicit plan scope includes these runner sources under `.planning`; generic planning exclusions do not remove them. No structural pre-pass was supplied. Project AGENTS.md, plan25, CONTEXT, summaries23/24, applicability24, gap coverage23–26, prior22 code review/recipe, canonical REVIEW/VERIFICATION and existing UI report/spec supplied context. Reviewer-specific configured skills were empty; no project skill directories were present. Source files are not ignored. The applicable gsd-code-review workflow was read; no additional delegation, install or commit occurred.

## Narrative Findings (AI reviewer)

No new BLOCKER or WARNING finding. The following are dispositions of already registered findings, retaining their original classifications.

| Finding / original classification | Current disposition and source evidence |
|---|---|
| WR-05 — WARNING | **Closed, bounded.** `15-evidence/run.py:923–929` accepts only exact int/float, tests finite positivity and catches OverflowError locally. `:999` applies it independently to both glyph dimensions; `:1847` retains the original outer CLI exception boundary. Separate width/height10**400 probes returned exit1, empty stdout and the exact capture diagnostic through both actual modes. No coercion, clamping, new viewport cap or broad exception suppression was introduced. |
| WR-03 — WARNING | **Closed, bounded; preserved.** `run.py:1152–1190` validates exact summary/detail inventories and each control's integer exit1, semantic argv, empty stdout and precise stderr. Strict duplicate-key loading remains at `:194–202`. Own missing-detail and all-success mutations each rejected through both CLIs. |
| WR-04 — WARNING | **Closed, bounded; preserved.** `run.py:932–1049` retains exact stock/native inventories, typed metadata, containment, icon observations, confined distinct paths, current digests and PNG dimensions. Own empty-stock and stale-digest mutations rejected through both CLIs, even though historical browser canonical exit stays successful. |
| WR-01/02 — WARNING | **Closed, bounded; preserved by continuity and inspection.** Exact command/case validation remains at `run.py:582–731`; capture-request preflight and effective selection reuse remain at `:256–362,1466–1483`. Their original counterexamples and prior independent22 executions retain attribution. No new product-runtime execution is claimed here. |
| CR-01–05 / G1–G5 — BLOCKER | **Closed within original bounds; preserved by full source and record continuity.** Product, tests, templates, docs and UI inputs are among822 identical mapped digests, with17 complete original gate objects unchanged. Prior independent22 source tracing, Python12 and JS36 executions remain their reviewer's observations. No generalized application-hook, concurrency or new theme guarantee is inferred. |

All source references above resolve under `/home/alex/projects/alex/django-crud-views/.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/`.

## Actual independent CLI observations

Machine records: [independent-outcomes.json](independent-outcomes.json), `lanes.code` (assembled from this lane's `code-outcomes.json` without altering observations). Every record contains actual argv, returncode, stdout, stderr and UTC start/finish. Window: `2026-11-01T20:56:03.794173+00:00`–`2026-11-01T20:56:45.035740+00:00`. All14 matched; two clean positives and12 precise rejections.

| Mutation / observation | Aggregate | Handoff | Exact result |
|---|---|---|---|
| clean | exit0 | exit0 | Aggregate20 gates; handoff structurally_valid=true, ready=false |
| width10**400 only | exit1 | exit1 | Conditional capture icon observations invalid: desktop |
| height10**400 only | exit1 | exit1 | Conditional capture icon observations invalid: desktop |
| Original absent detailed controls | exit1 | exit1 | Checker control evidence inventory incomplete |
| Original all detail records rewritten to success | exit1 | exit1 | Checker control exit invalid: exit-code |
| Original empty stock captures | exit1 | exit1 | Conditional capture inventory invalid: stock |
| Original stale desktop digest | exit1 | exit1 | Conditional capture digest mismatch: desktop |

Every rejection has empty stdout and stderr exactly `MATRIX_REJECTED: ` + the displayed diagnostic + newline. No traceback, stale-source/hash error, unrelated inventory failure or success marker substituted for the intended overflow result.

Recipe authorship: this lane adapted the original four mutations from prior22 `code-controls/probe.py` and the numeric mutations from current `test_runner.py:523–648`; actual executions are exclusively this actor's. Each mutation deep-copied the complete actual24 packet, retained the matching current sidecar, and bound a copied pending handoff to that mutation's actual packet digest. No synthetic self-test gate or invented control records were used. Transport adjustment: repository-contained owned `.git/code-25-owned-*` temporary files were required because `bound_file():1661–1666` rejects resolved packet paths outside ROOT; a physical /tmp packet would fail before its intended predicate. Coordinator agreed. Temporary files were removed. The unchanged runner and real CLI main were used without patches.

Additional independent direct capture checks exercised both dimensions with10 accepted values total (1,1.5,10**300, largest finite float, smallest positive subnormal) and32 rejected values total (zero, negatives, booleans, None, strings, list/dict/tuple, NaN, infinities and ±10**400). Each rejection was the exact ValueError at the capture predicate. These are bounded numeric observations, not claims of exhaustive arithmetic coverage.

## Required inventory and refresh applicability

`run.py:64–140,1357–1373` registers35 controls including distinct `capture-width-overflow` and `capture-height-overflow` payload mutations with the required capture diagnostic. AST comparison against pre23 source independently confirmed that the original33 identities, relative order and diagnostics remain unchanged. `generate_controls():1584–1637` still records real payload subprocesses, then record-level subprocesses, validates each outcome before adding it and finally executes an ordinary clean positive. No passing seed or public bypass is introduced.

`GAP_REVIEWS` at `:1640–1647` requires WR-05 in G6's exact list and `GAP_THREATS` includes41. Handoff exact finding-set/link validation at `:1740–1755` prevents dropping WR-05. The new independent width/height tests collect both CLI outcomes before asserting, preserve clean counterparts, and check direct capture/aggregate/handoff boundaries. Numeric tests cover valid preservation and invalid rejection. Control tests assert exact one-field mutations and unchanged origin/PNG digests. Handoff test `test_wr05_is_required_for_g6` checks both omission and unlinking; its isolated matrix mock is explicitly synthetic, while complete-packet tests and this review supply real end-to-end evidence.

Independently recomputed current manifest equals the packet and sidecar. Origin18/current24 maps have **824 equal paths,822 equal digests, exactly two changed files, no additions/deletions**. The only changed files are the reviewed runner/test. All captured effective selections are JSON-identical to origin18. All17 retained records are JSON-identical, including outputs, timestamps, commands, environments and provenance:

- `conditional-browser`
- `django4.2-disabled-full`
- `django4.2-enabled-full`
- `django4.2-focused`
- `django4.2-missing-runtime`
- `django5.2-disabled-full`
- `django5.2-enabled-full`
- `django5.2-focused`
- `django5.2-missing-runtime`
- `django6.0-disabled-full`
- `django6.0-enabled-full`
- `django6.0-focused`
- `django6.0-missing-runtime`
- `javascript`
- `javascript-integration`
- `modal-browser`
- `strict-docs`

The fresh24 checker record selects exactly67 AST-discovered test identities and contains exactly67 individual `... ok` outcomes, exit0, ending `Ran 67 tests in 631.064s / OK`. Its window is `2026-11-01T20:37:34.134784+00:00`–`2026-11-01T20:48:05.433651+00:00`. All35 actual recorded negative subprocess results satisfy the current control validator; the captured clean positive succeeded. The two fresh Ruff gates also validate with current source/command provenance. These are inspected plan24 capture facts, not executions by this code lane. Full exact identities remain in applicability24 and the machine lane payload. The new identities include separate width/height, numeric contract, overflow controls and WR-05 required-link tests.

Historical48,220 Python passes, JS347/integration2 and browser36 cases/305 assertions remain original executions. Only the original four CSP skip events and four crispy-floor golden deselections remain. Python3.12.3, Django4.2.30/5.2.18/6.0.9 and cached Chromium149.0.7827.55 bounds remain. Complete source, packet, canonical report and PNG protected hashes were unchanged after all14 probes.

## Bindings

| Binding | SHA-256 |
|---|---|
| Current logical source | `5140a723bcffd78d4920086beff692c03935969545226467767b5dd34706e97d` |
| Actual24 results bytes | `0584675c935c5d7a81043a3c412a9bb43df5072532db49682aa5604e575effbd` |
| Current runner | `75f8057f55d869ccb9591a0a9868e57d606f9e65f2f0eebffa5fca8d5313ad66` |
| Current test_runner | `a37d5e636ad612d9e4b3a330392bd61e31ca6290c04ba6f3fa0692a09903e7bf` |
| Actual24 manifest file | `7dc2541183e999d8709d4c173a9db50f21a0bab52312e22767db896b80a0bf9b` |
| Unchanged prior canonical VERIFICATION | `5048486226b2d48556280f99f5ae12a24d4ef581c9585ff8c4a4da7e1d9b3ced` |

This explicit two-file deep review plus current source/packet bindings supplies plan25's execute:post code-review assessment. An unchanged source scope does not need a duplicate review. Any later source change invalidates this applicability and requires affected evidence refresh/reassessment.

## UI applicability and pending acceptance

The historical UI24/24 report remains applicable **within its original scope**: full-map equality covers product/fixture/UI inputs, retained browser records are exact, and all three stock PNG hashes remain unchanged and revalidated by actual aggregate checks. V1/V2/S1 bounded closures remain historical. No new rendering, visual audit or native screenshot is claimed. Native capture arrays are explicitly empty and cannot establish native visual acceptance. Human H1 still requires actual stock/native discoverability, readability, keyboard/focus and assistive-technology judgment.

H2 remains descriptor-less **flagged-unverified**, exactly: **Switching a conditional file field off must not silently authorize deletion of the stored file content.** Native False-clear/None-no-change, retained file bytes/storage-delete spies and trusted server-disabled precedence are bounded reference behavior. ImageField remains reference-only; image decoding/dimension hooks, application save/signal/custom hooks and arbitrary storage guarantees remain unclaimed.

All19 decisions remain explicit. All31 fallback assumptions remain **flagged-unresolved**, individually retained:
1 AUTH-02 concurrency/A19 only;2–7 COND-01 boundary, adjacency, empty, encoding, ordering, precision;8–10 COND-02 adjacency, empty, ordering;11 COND-03 unclassified;12–13 COND-04 idempotency, concurrency;14–16 COND-05 adjacency, empty, ordering;17–21 FSET-01 adjacency, empty, ordering, idempotency, concurrency;22–23 FSET-02 idempotency, concurrency;24–26 FSET-03 boundary, precision, concurrency;27–29 LIFE-01 adjacency, empty, ordering;30–31 LIFE-02 empty, encoding. Exact rows remain in [gap coverage](../06.4-GAP-COVERAGE-23-26.md) and current24 handoff. Numeric checker closure does not resolve product precision assumptions.

Preserve A19-only AUTH-02 and original authorization/ancestry/queryset, routed atomic rollback, inactive skip/explicit managed purge, migration and Phase7 inventory boundaries; preserve A8, A25, #210/jQuery, broader Guardian#286/custom-PK/backend/field/theme exclusions. T35/T36/T40 and T41–43 remain individually owned by the independent security/canonical lanes; this report authors no security or validation verdict. No accepted risk, human actor/response, ready=true, phase completion or Phase7 advancement is inferred.

Only this report, the temporary lane outcomes payload and an attributed append to REVIEW were authored. Read/Write tools were unavailable: shell reads and apply_patch were used. No product source, historical evidence, canonical VERIFICATION, handoff, index staging or commit was modified by this lane.

