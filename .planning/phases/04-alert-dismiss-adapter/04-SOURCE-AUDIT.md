# Phase 04 — Source Coverage Audit

All in-scope source items are planned. Discovery uses the current source and the completed 04-RESEARCH.md
verification of the existing Bootstrap component; no new dependency or separate discovery document is needed.
The stale generated API-SURFACE.md (zero symbols) is not source authority.

## Multi-source coverage

| Source | ID | Required outcome / constraint | Plan/task | Status |
|---|---|---|---|---|
| GOAL | Phase 4 | Dismiss through the adapter seam without copying the frame for a framework attribute | 04-01-02; 04-02 | COVERED |
| GOAL | SC1 | Before-change golden committed first | 04-01-01 | COVERED |
| GOAL | SC2 | Present/absent Alert and post-load content close | 04-01-02; 04-02 | COVERED |
| GOAL | SC3 | New hook; stock framework attributes restricted to documented dropdowns | 04-01-02; 04-03-01 | COVERED |
| GOAL | SC4 | Example flash closes; references and paired release/migration changes | 04-03 | COVERED |
| REQ | ALRT-01 | Golden history precedes product change | 04-01-01; 04-03-03 history evidence | COVERED |
| REQ | ALRT-02 | Shared hook and one delegated current-adapter call | 04-01-02/03; 04-02-02 | COVERED |
| REQ | ALRT-03 | Present-component close and absent-only default removal with Vitest | 04-01-02; 04-02-01/02 | COVERED |
| REQ | ALRT-04 | Dropdown audit, three references, Breaking and migration | 04-03-01/02 | COVERED |
| CONTEXT | D-01 | Literal default classes; no new frame class keys | 04-01-02/03; 04-03-01 | COVERED |
| CONTEXT | D-02 | Complete compact custom-class frame recipe retaining hooks | 04-03-01 | COVERED |
| CONTEXT | D-03 | Custom errors surface; no core log/removal/rollback | 04-01-02; 04-02-02; 04-03-01 | COVERED |
| CONTEXT | D-04 | Removal only in default adapter when Alert absent | 04-01-02; 04-02-01/02 | COVERED |
| CONTEXT | D-05 | Before/after migration, scripts and reference links | 04-03-02 | COVERED |
| CONTEXT | D-06 | Recommend migration with Bootstrap; explain legacy behavior | 04-03-02 | COVERED |
| CONTEXT | D-07 | Separate baseline commit; preserved other output | 04-01-01/02/03; 04-03-03 | COVERED |
| CONTEXT | D-08 | Dynamic nearest-role delegation; current lookup; namespace/preassignment | 04-01-02; 04-02 | COVERED |
| CONTEXT | D-09 | Three references, four adapters, paired Breaking/migration, dropdown boundary | 04-03-01/02 | COVERED |
| CONTEXT | D-10 | All paths/errors tested, real example browser, quality gates | 04-01 through 04-03 | COVERED |
| RESEARCH | R1 | Existing classic scripts, factory, shallow merge and fixed selectors | 04-01-02; 04-02 | COVERED |
| RESEARCH | R2 | Present no-op/throw never selects fallback; Bootstrap owns transitions | 04-02-01/02; 04-03-03 | COVERED |
| RESEARCH | R3 | Missing namespace vs missing component; object/function/late globals | 04-02-01 | COVERED |
| RESEARCH | R4 | Existing listenerErrors, error identity/no-call assertions and scoped cleanup; reload case remains last | 04-02-02 | COVERED |
| RESEARCH | R5 | Raw fixed-locale golden, unchanged non-dismissible/escaping/translated labels | 04-01-01/03 | COVERED |
| RESEARCH | R6 | Real message response and complete documented override render | 04-01-03; 04-03-01 | COVERED |
| RESEARCH | R7 | Script needs table; factory count distinct from lifecycle events; existing settings/migration lists aligned | 04-03-01/02 | COVERED |
| RESEARCH | R8 | No persistent state/schema/secret migration, installs or new framework | All plans remain existing local DOM scope | COVERED |
| RESEARCH | R9 | Exact dropdown allowlist and non-vacuous audit | 04-03-01 | COVERED |
| RESEARCH | R10 | Installed JS/Ruff drift disclosed, not inferred incompatibility | 04-03-03 | COVERED |
| RESEARCH | R11 | System check/docs sync cannot establish browser close | 04-03-03 | COVERED |
| RESEARCH | R12 | ASVS1 encoding/frontend boundaries; high findings block | Each threat_model; 04-01-03; 04-03-01 | COVERED |
| RESEARCH | R13 | No hand-built animation, initialization observer or browser HTML reconstruction | 04-01-02; 04-02-02 | COVERED |
| RESEARCH | R14 | Generic downstream follow-up in acceptance only; no downstream edits/names | 04-03-03 | COVERED |

Excluded by source scope: LATER-06 class keys, focus management, auto-dismiss, new lifecycle events,
downstream implementation, version bump, and other phases' requirements. These are exclusions, not missing rows.
The older source plan places removal in the handler; D-04 explicitly supersedes that sentence.

## Dependency and ownership graph

| Task | Needs | Creates/proves | Checkpoint |
|---|---|---|---|
| 04-01-01 | Current frame and pytest renderer | Standalone legacy golden/test commit | none |
| 04-01-02 | Baseline commit | Complete rendered-to-adapter tracer and new hook; both message assertion updates in the same green commit | none; settled public decision |
| 04-01-03 | Tracer | Message/escaping/translated control regression coverage | none |
| 04-02-01 | 04-01 | Namespace and present/absent ownership matrix | none |
| 04-02-02 | 04-02-01 and 04-01 listener | Dynamic/error/repeated click matrix | none |
| 04-03-01 | Implemented contract and 04-02 | References and executable recipe/allowlist guard | none |
| 04-03-02 | Canonical references | Paired release/migration guidance | none; settled public decision |
| 04-03-03 | All preceding work | Full gates and real browser acceptance record | end-phase human-check only |

Waves: 1 = 04-01; 2 = 04-02; 3 = 04-03. No same-wave overlap. Shared test/product files force
the 04-01→04-02 edge; final combined quality evidence waits for both. Each plan has 2–3 tasks.
The tracer deliberately modifies six files to keep both message assertions green with the template;
other tasks modify at most five. The baseline is an explicitly required evidence prerequisite
before the single product tracer, not a layer of unfinished product scaffolding.

## Spec-less Edge Coverage

Source: /tmp/phase04-edge-coverage.json; seven rows received. No SPEC exists.

| Requirement | Category | Disposition | Verification / carried assumption |
|---|---|---|---|
| ALRT-01 | unclassified | unresolved, flagged A04-01 | Plan 04-01 flags classifier limitation; D-07 gives explicit golden chronology |
| ALRT-02 | unclassified | unresolved, flagged A04-02 | Plan 04-01 flags classifier limitation; D-08 gives explicit delegation semantics |
| ALRT-03 | idempotency | resolved | Explicit 04-02 truth and tests: repeated absent-component close is harmless; present component retains ownership |
| ALRT-03 | concurrency | resolved | Explicit 04-02 truth and tests: once per attached click; detached subtree stops document propagation; no added lifecycle guarantee |
| ALRT-04 | adjacency | unresolved, flagged A04-04-adjacency | Appears nonapplicable: documentation/allowlist has no geometric adjacency; not auto-dismissed |
| ALRT-04 | empty | unresolved, flagged A04-04-empty | Appears nonapplicable: requirement defines no nullable collection function; keep documentation/allowlist acceptance without inventing one |
| ALRT-04 | ordering | unresolved, flagged A04-04-ordering | Appears nonapplicable: no sorting contract; migration script order is separately explicit in D-05 |

No-silent-drop accounting: 7 input rows = 2 explicit must-have truths + 5 flagged assumptions.
No backstop truth or invented product behavior is needed. Unclassified rows remain unresolved.

## Prohibition recall and precision

Recall considered ten failure candidates per requirement:
- ALRT-01: late capture, amended baseline, mixed product commit, normalized bytes, unstable locale, broad regeneration,
  uncommitted fixture, stale render, wrong fixture, missing history.
- ALRT-02: CSS-based target, wrong ancestor, stale adapter, per-element setup, missed descendants, orphan deletion,
  duplicate dispatch, inline handler, new focus behavior, new lifecycle events.
- ALRT-03: forced removal, swallowed errors, core logging, mutation rollback, eager namespace, lost preassignment,
  no-op treated as failure, component throw treated as absence, added teardown timers, detached re-dispatch.
- ALRT-04: omitted script, wrong factory count, misleading legacy claim, absent migration example, dropped semantic hook,
  unsafe snippet interpolation, untested complete recipe, broad CSS promises, false browser pass, hidden tool drift.

Precision: routine engineering/verification concerns and already locked scope constraints belong to tasks,
tests and review; they are not new bespoke values/safety/ethics prohibitions. Injection is canon and stays
with the security threat model and $gsd-secure-phase, not a minted prohibition. Zero bespoke prohibitions
survive; all plans correctly emit prohibitions: []. No wired-check descriptors are fabricated.

## Hook and planning evidence

- API detector run on the three plans plus Phase 4 ROADMAP section: detected=false, signals=[]; no external
  API coverage matrix needed. Bootstrap is an existing local browser component.
- Assumption-delta scan 4: detected=false, signals=[]; no new architecture question.
- Schema scan: no in-scope ORM/schema paths; no push task.
- Security: ASVS level 1, high blocking threshold; unique T-04-01 through T-04-06, reserved T-04-SC repeated.
- Graph status: absent; project source is authority. No configured planner/project skills.
- Calibration: factor=1, sample_count=0, confidence=low; projections 24000 / 18000 / 18000 tokens.
- Frontmatter and plan-structure validation passed for all three plans. Only one-way warnings are the
  existing D-05/D-06/D-09 public DOM decision; already-settled exception applies, no checkpoint inserted.
- Focused baseline rerun: 50 Python tests passed; 25 JS tests passed. These are pre-change results, not feature evidence.
- Stock attribute audit baseline: four matching lines, three paths (alert, actions_menu_toggle, language_selector).
  Final guard scans exactly src/crud_views/templates and requires a nonempty subset of the three allowed
  relative paths; actions_menu.html need not match. A temporary copy with the baseline alert template
  proves historical red without changing the checkout or giving lasting tests a Git-history dependency.
- Existing implementation/docs/test command paths were checked against git-tracked files. New files/symbols/tests
  are declared in each PLAN's "Artifacts this phase produces" section.
- Planning commits and branch management belong to the orchestrator; this planner made no product edits or commits.

## Round 1 review incorporation — a8f425e

Executable PLAN ledgers cover H1 and A1–A10. H1 fixes core-only scan scope, subset semantics and historical
red. A1 keeps the tracer commit green; A2 rejects a branch switch and preserves introduce-gsd. A3/A4 use
scoped globals and the existing listenerErrors helper. A5/A6 add multiple-control, nested-survivor and
missing-adapter cases. A7 updates existing settings/migration lists; A8 preserves recipe imports and
the colour accessor; A9 requires only the new hook on migrated controls; A10 names Django's actual
translation delegate. Refuted or already-covered suggestions and extension-hook scope debt have explicit
PLAN ledger dispositions. Three plans and their wave dependencies remain unchanged. Review conflict
markers in 04-REVIEWS.md remain untouched.

## Round 2 review incorporation — ddb9461

C2-A1 adds a lasting tmp_path allowed/forbidden-tree regression for the core audit helper, separate from
historical evidence. C2-A2 requires each new JS case to own a fresh cv/adapters map before nested mutations,
so restoring global descriptors cannot retain a deleted original key. C2-A3 explicitly verifies an
unmarked body click inside role=alert causes no call, error or removal. Round 2 ledgers are appended in
04-02/04-03; the three-plan structure, locked decisions and all prior dispositions remain intact.
