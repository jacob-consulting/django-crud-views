# Phase 02 — Source Coverage Audit

Plan **02-01**, wave **1**, three serial tasks. No source requirement is missing.
D-01 settles Option A and supersedes older undecided roadmap/state wording.
Discovery level 0: existing helpers/fixtures suffice; no dependencies or external integrations.
Calibration: factor 1, zero samples, confidence low; raw/calibrated estimate 24,000 tokens.

## Multi-source coverage

| Source | ID | Obligation | Task | Status |
|---|---|---|---|---|
| GOAL | Phase 2 | One documented/check-enforced segment and mode grammar without loosening W362 | 02-01-01–03 | COVERED |
| REQ | KEYS-01 | Approved Option A at canonical class-table anchor | 02-01-03 | COVERED |
| REQ | KEYS-02 | Form-kind modes accepted; malformed keys rejected | 02-01-01–02 | COVERED |
| REQ | KEYS-03 | Independent grammar sets; future-location isolation | 02-01-01–02 | COVERED |
| REQ | KEYS-04 | Parse count and compare to actual table | 02-01-03 | COVERED |
| CONTEXT | D-01 | Preserve base form keys/crispy slots; Option A | 02-01-01–03 | COVERED |
| CONTEXT | D-02 | All five kinds × three modes, both sources | 02-01-01–02 | COVERED |
| CONTEXT | D-03 | Action variants/form kinds; reject structural/utility suffixes | 02-01-01–03 | COVERED |
| CONTEXT | D-04 | Presence fallback, None/empty suppression, unchanged defaults | 02-01-01–03 | COVERED |
| CONTEXT | D-05 | W362 Warning and exact diagnostic distinction | 02-01-01–02 | COVERED |
| CONTEXT | D-06 | Retain existing diagnostic wording | 02-01-01–03 | COVERED |
| CONTEXT | D-07 | Icons do not determine class-key validity | 02-01-02–03 | COVERED |
| CONTEXT | D-08 | Compact table, examples and form fallback | 02-01-03 | COVERED |
| CONTEXT | D-09 | Actual count and guard; exclude addressable combinations | 02-01-03 | COVERED |
| CONTEXT | D-10 | E108/floors follow button-data LOCATIONS; no form floor | 02-01-01–02 | COVERED |
| CONTEXT | D-11 | Preserve rendering/goldens; compatible release note | 02-01-02–03 | COVERED |
| RESEARCH | Ownership/imports | Immutable independent sets; exact segments; local shared vocabularies; bare-settings import | 02-01-01–02 | COVERED |
| RESEARCH | Matrix/values | Independent expected vocabulary; both layers; E361-only invalid value; None/empty acceptance | 02-01-02 | COVERED |
| RESEARCH | Precedence | Settings exact key beats theme; theme mode beats settings base | 02-01-02 | COVERED |
| RESEARCH | Documentation | Correct canonical 70; remove redundant number; update W362 row; accurate Phase 6 boundary | 02-01-03 | COVERED |
| RESEARCH | Regressions | Floor/location invariants, E108, escaping, crispy, templates and unchanged goldens | 02-01-02 | COVERED |
| RESEARCH | Environment/gates | Proven commands; report Ruff mismatch without dependency changes | Final verification | COVERED |
| RESEARCH | Security | Scoped STRIDE; ASVS level 1; high blocks; no package installation | Threat model/tasks 01–02 | COVERED |

Excluded: form leaves/rendering, utility additions, form floors and missing-icon checks (Phase 6);
variants everywhere and enhanced form-specific warnings (rejected).

## Edge-probe reconciliation

No SPEC supplied this section. Resolved predicates are plain-string must_haves.truths; unclassified rows remain
flagged_assumptions. This table preserves every row of the orchestrator's seven-row deterministic report.

| Requirement | Category | Status | Verification | Acceptance / disposition |
|---|---|---|---|---|
| KEYS-01 | unclassified | unresolved | — | Flagged assumption; canonical prose is reviewed against D-01/D-08. Requirement coverage does not resolve classifier uncertainty. |
| KEYS-02 | unclassified | unresolved | — | Flagged assumption; explicit full matrix still required. Never auto-resolve this probe row. |
| KEYS-03 | adjacency | resolved | explicit | Adding form/new locations to button-data LOCATIONS cannot admit their variant-mode keys; original action variants and form kinds stay distinct (truth 3/task 02). |
| KEYS-03 | empty | resolved | explicit | None/empty settings add no overrides; singleton valid key passes; non-string and malformed/empty segments diagnose safely (truth 2/task 02). |
| KEYS-03 | ordering | resolved | explicit | Membership does not depend on registration order; invalid-mode hint remains sorted both/icon/label (truth 4/task 02). |
| KEYS-04 | boundary | resolved | explicit | Exactly one sentence and integer equality; missing/duplicate count or count ±1 fail (truth 6/task 03). |
| KEYS-04 | precision | resolved | explicit | Decimal capture uses exact Python int equality against live len; no floating arithmetic/rounding/fixed substitute (truth 6/task 03). |

Accounting: **7 surfaced = 5 explicit resolved predicates + 2 flagged unresolved assumptions**.
No auto-dismissals, invented backstops or omitted rows. Related predicates share a truth where appropriate.

## Prohibition recall and precision

The adversarial pass considered the following candidates. Routine correctness/hygiene and already explicit
scope constraints were dropped by precision filtering. No bespoke values/privacy/ethics prohibition survived;
must_haves.prohibitions is intentionally empty.

| Requirement | Raw candidates considered | Precision outcome |
|---|---|---|
| KEYS-01 | Wrong option; misleading segments; omitted kinds; omitted modes; contradictory examples; inaccurate fallback; false rendering claim; stale checks prose; changed anchor; missing release note | Existing locked constraints or documentation correctness; zero kept |
| KEYS-02 | Broad prefixes; wrong modes; structural admission; unknown-kind admission; changed severity; changed message; changed hint; value-error conflation; icon prerequisite; class-string injection | Grammar correctness is in tasks; injection is canon; zero kept |
| KEYS-03 | Aliased locations; derived-prefix broadening; duplicate variants; duplicate modes; mutated shared sets; missing kinds; order dependence; early imports; changed floors; changed E108 | Existing locked constraints or ordinary engineering correctness; zero kept |
| KEYS-04 | Stale integer; duplicate count; absent count; mode combinations counted; table rows counted; fixed-number test; wrong path; rounding; truncation; generated-doc expansion | Ordinary count/path correctness and existing scope; zero kept |

Canon breadcrumb: HTML injection/output encoding belongs to the scoped threat model and $gsd-secure-phase;
retain existing escaping regression, without minting a duplicate prohibition.

## Evidence and limits

All five product edit paths, referenced test files and package.json are git-tracked. Source reads and the pattern
map establish interfaces; the incomplete API index was not absence evidence. Research's successful baseline is
reused; no product tests were rerun during planning. No graph exists. Branch remains introduce-gsd.
No source/config/dependency changes or commits were made. Orchestrator handles roadmap integration/checker.
