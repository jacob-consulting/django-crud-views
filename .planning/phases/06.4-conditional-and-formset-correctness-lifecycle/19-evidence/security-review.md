---
phase: "06.4"
plan: "19"
actor: gsd-security-auditor independent ASVS1 mitigation re-audit
recorded: 2026-11-01T17:14:15Z
source_sha256: bc68bdd3b135d8919f400da204eeb6dda6ebbb01f2ceee47d50f2d6655d41601
runner_sha256: cc9f3a7c4e99408267d0f0b4b731c6ceb6f7e6b6070faf90fee634743690fc4c
status: OPEN_THREATS
threats_total: 37
threats_closed: 31
threats_open: 5
threats_open_total: 6
asvs_level: 1
block_on: high
---

# Independent security re-audit — plan 19

Recorded from the terminal structured return of delegated gsd-security-auditor, model gpt-6-astra,
effort xhigh. The auditor changed no files; the executor records its outcome here as required by
the secure-phase workflow. All 37 authored obligations have disposition mitigate. No risk was
accepted or transferred. Five high threats block advancement; one open medium threat does not
count toward threats_open. This is neither canonical goal verification nor phase approval.

## Open obligations

| Threat | Severity | Independent disposition and evidence |
|---|---|---|
| T-06.4-22 | high | OPEN: WR-03/04; aggregate acceptance does not reject missing/contradictory corruption records or missing/stale conditional screenshots. |
| T-06.4-28 | high | OPEN: run.py:984–985 validates checker_controls labels but never checker_control_evidence; deleting all 25 records or rewriting all outcomes to exit 0 is accepted. |
| T-06.4-33 | high | OPEN: plan18 requires absent/failed controls and altered capture provenance to fail, but actual validator accepts both counterexamples. |
| T-06.4-35 | high | OPEN: attribution/readiness guards exist at run.py:1249,1287; actual H1/H2 and all required independent dispositions remain incomplete. |
| T-06.4-36 | high | OPEN: H2 has no genuine enforcement descriptor or attributed human disposition; canonical status remains flagged-unverified. |
| T-06.4-31 | medium | OPEN, below high threshold: run.py:853–923 omits conditional capture-count/hash checks present in conditional-formsets.cjs:91–98. Actual fixture repairs/screenshots and honest H1-pending state verified. |

Exact H2 prohibition: **Switching a conditional file field off must not silently authorize deletion
of the stored file content.** Native storage-spy/reference observations do not establish general enforcement.

## Closed authored mitigations

Paths below are repository-relative: lib/ means src/crud_views/lib/, js/ means
src/crud_views/static/crud_views/js/, test Python files are under tests/test1/, and run.py is
the current phase's 15-evidence/run.py. Closure is individually bounded; the overall audit is OPEN_THREATS.

| Threat | Severity | Independently inspected mitigation / evidence |
|---|---|---|
| T-06.4-01 | medium | CLOSED: js/toggle.js:23,88,152 exact ownership, last own state and obsolete-listener detachment; tests/js/toggle.test.js:198. |
| T-06.4-02 | medium | CLOSED: lib/conditional/layout.py:29, escaped conditional/toggle_group.html attributes and executable escaping tests. |
| T-06.4-03 | high | CLOSED: lib/conditional/group.py:163,181,193 refreshed persistence and trusted disabled precedence. |
| T-06.4-04 | high | CLOSED bounded native reference mitigation: group.py:69,181; test_conditional_persistence.py:276, zero storage deletion and retained bytes; H2 remains open. |
| T-06.4-05 | high | CLOSED: src/crud_views/checks.py:82,162 and group.py:74,141 configuration refusal. |
| T-06.4-06 | high | CLOSED: group.py:142,153,184,195 inherited clean/model validation and disabled-field preservation. |
| T-06.4-07 | high | CLOSED: lib/formsets/render_tree.py:202,247 policy after every native traversal; test_formsets_policy.py:313 repeated-cleaning HTTP zero-save controls. |
| T-06.4-08 | high | CLOSED: render_tree.py:223–244 queryset membership, native PK conversion/bound-instance equality; int/UUID, DELETE, selected-alias controls. |
| T-06.4-09 | medium | CLOSED: render_tree.py:245,260; test_formsets_policy.py:424 generic deduplicated Invalid row after reclean. |
| T-06.4-10 | high | CLOSED: lib/formsets/formsets.py:359,385 and mixins.py:114 retain skip/scoped purge/rollback. |
| T-06.4-11 | medium | CLOSED: js/toggle.js:31,78,99 ancestor/external baseline composition and management exception. |
| T-06.4-12 | medium | CLOSED: js/toggle.js:68,124 usable focus fallback and cancelled-reset preservation; JS/browser cases. |
| T-06.4-13 | high | CLOSED: js/formset.js:76,507,590 actual owning-form controller/exact lookup scope. |
| T-06.4-14 | high | CLOSED: js/formset.js:536; js/modal.js:227 reorder before serialization, cancellation stops submission. |
| T-06.4-15 | medium | CLOSED: js/formset.js:10,20,267,329,529 immutable bound identity/optional DELETE; formset.test.js:531,558,568,580. |
| T-06.4-16 | high | CLOSED: lib/formsets/mixins.py:49,71, Guardian mixins.py:68 and formsets.py:411 authorization/ancestry before rendering. |
| T-06.4-17 | high | CLOSED: formsets.py:455,467,528 sibling/deeper coordinates and real fragment/FormData round trips. |
| T-06.4-18 | medium | CLOSED bounded original case/runtime/status contract: conditional-formsets.cjs:80–102; new capture omission belongs to T31/T33. |
| T-06.4-19 | high | CLOSED: real stock/native shipped-JS/forged-POST zero-save cases at conditional-formsets.cjs:243,554. |
| T-06.4-20 | medium | CLOSED: test_conditional_migration_docs.py:42,67,92,114,137,184 executable actual-API/paired migration recipes. |
| T-06.4-21 | medium | CLOSED: exact emitted projection/second siblings; PUBLIC-SURFACE:64,96,114 A19-only and exclusions. |
| T-06.4-23 | high | CLOSED: lib/views/mixins.py:37,41,54; lib/formsets/mixins.py:104,114 preserved auth/queryset/atomic/skip-purge matrix. |
| T-06.4-24 | high | CLOSED: render_tree.py:202; test_formsets_validation_gate.py:90 later sibling/child full_clean restores policy, zero saves/unchanged DB. |
| T-06.4-25 | high | CLOSED: separate Vitest configurations; tests/js-integration/formset.test.js:91 requires selected interpreter; runtime-contract.test.js:63,86 Node-only/missing/invalid runtime. |
| T-06.4-26 | medium | CLOSED: js/formset.js:10,20,329; control.html:25 actual native DELETE and moved/inserted rows. |
| T-06.4-27 | medium | CLOSED: js/toggle.js:17,88,152 zero/two/one matches, ancestors/external ownership/recovery/disposal. |
| T-06.4-29 | high | CLOSED: run.py:170,190,289,1075 current-runtime preflight and changed-selection reuse independently verified. |
| T-06.4-30 | high | CLOSED: conditional-formsets.cjs:243–285 native DELETE presence, ordered persisted POST and reclean zero saves, both themes. |
| T-06.4-32 | medium | CLOSED: migration_docs.py:114,137,184 native capability/reclean recipes and explicit ImageField/H2 limits. |
| T-06.4-34 | high | CLOSED: retained authorized/scoped atomic boundaries and actual full selections, no expanded AUTH-02. |
| T-06.4-SC | high | CLOSED exercised no-install route: run.py:190,516 uses existing stack; no dependency/lock installs, package.json adds only integration command. Future-install audit unexercised. |

## Independently executed checks

From repository root, PYTHONDONTWRITEBYTECODE=1 and the existing Django6 interpreter:

- 15-evidence/run.py --check --output 18-evidence/results.json: exit 0,
  PHASE64_MATRIX_OK 20 gates, matching the recorded current source digest.
- Same runner --check-handoff 19-evidence/handoff.json: exit 0, structurally_valid=true,
  ready=false, disposition=not-ready. This checked the initial pending packet.
- Python stdin probes imported the actual runner and modified only deep in-memory copies:
  all 25 original corruption variants rejected; missing selected Python failed before subprocess;
  changed runtime selection was not reusable; false readiness/unattributed H1/H2 rejected.
- WR-03 independently reproduced: removing all checker_control_evidence, or rewriting all records
  to returncode=0/stdout=PHASE64_MATRIX_OK/stderr empty, is accepted by actual validate().
- WR-04 independently reproduced: stock gap-ambiguity captures=[] and stale capture SHA-256
  are accepted by actual validate_browser(). All three original stock screenshot hashes match.

The actual packet contains all 25 genuine failed subprocess records (exit 1, MATRIX_REJECTED).
No fabricated capture is alleged. The defect is missing enforcement during subsequent checking.
Auditor inspected concrete reclean/identity zero-save, native-capability and ownership cases,
and all required negative controls, without a full suite/browser replay.

Reused current evidence: 48,220 Python passes, JS347/integration2/self-tests37, browser36/305.
Scope remains Python3.12.3, Django4.2.30/5.2.18/6.0.9 and cached Chromium, ImageField reference-only,
A19-only AUTH-02; A8/A25/#210/broader Guardian/custom-PK/backend exclusions remain. No new
unregistered surface was identified; described fixtures/runtime boundaries map to T25/T30/T31.

**Required next action:** repair WR-03/04, independently re-review the checker and rerun the
security audit; obtain genuine H1/H2 outcomes or a real H2 enforcement route. Preserve all
high blockers until independently verified. Do not infer canonical goal or phase completion.
