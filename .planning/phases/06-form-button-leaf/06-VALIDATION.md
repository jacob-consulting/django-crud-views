---
phase: "06"
slug: "form-button-leaf"
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-27"
---

# Phase 06 — Validation Strategy

## Test Infrastructure

| Property | Value |
|----------|-------|
| Python | Existing pytest/Django harness in `tests/test1/conftest.py` |
| JavaScript | Existing Vitest/jsdom harness in `vitest.config.js` |
| Quick Python | `.venv/bin/pytest tests/test1/test_crispy_buttons.py tests/test1/test_button_data.py -q` |
| Quick JavaScript | `bash .planning/phases/06-form-button-leaf/06-js-verify.sh tests/js/modal.test.js tests/js/viewset.test.js tests/js/list.filter.test.js` |
| Full suites | `.venv/bin/pytest tests -n auto` and `bash .planning/phases/06-form-button-leaf/06-js-verify.sh` |
| Runtime | Not measured; measure during execution, do not infer from inherited research |

## Sampling Rate

- After each task commit, run its targeted Python or JavaScript shard.
- After an integrated wave, run the full Python and JavaScript suites.
- 06-01 task 1 creates the selected-runtime wrapper/evidence before the first JS gate. Each invocation
  reasserts absolute Node/npm paths, locked engine ranges, package identities and lock hash; bare ambient npm
  is not a substitute in fresh shells. Compatible runtime/artifact acquisition failure blocks the gate.
- D-18 resolves the former main prerequisite: verify completed Phase 1/2 contracts on the executing working
  branch and record HEAD plus test evidence before the spec. These planning changes do not mark any execution
  or runtime acceptance result passed; missing or invalid dependencies still halt 06-01.
- Before phase verification, run the declared-floor session, strict docs build, lint and formatting,
  example checks and documentation synchronization.
- Target feedback latency: under 60 seconds for a focused shard; split if measurement exceeds it.

## Per-Task Verification Map

All tasks map to executable PLAN commands and immediate fails_when conditions. Pending means planned, not passed.

| Task | Wave | Requirements | Threat Ref | Verification target | Status |
|---|---|---|---|---|---|
| 06-01-1..3 | 1 | FORM-01/02/05/06/08/11 | T-06-01 | Real crispy tracer; spec and executing-branch prerequisite evidence (D-18); five golden captures and commit history | pending |
| 06-02-1 | 2 | FORM-02/03/04/06/07 | T-06-02/03 | Real leaf plus atomic location consumers, utilities, exhaustive EXPECTED_KEYS and docs count | pending |
| 06-02-2 | 2 | FORM-05/07 | T-06-02/03/04 | Custom templates, literal/SafeString/lazy attrs; floor invariant | pending |
| 06-02-3 | 2 | FORM-06 | T-06-04 | Golden diffs, CRUD and cancel payloads | pending |
| 06-03-1..2 | 3 | FORM-10/11 | T-06-05/06 | Singleton maps versus lazy floor overrides; whole maps, actual render-form identity, multiple FormActions and nested formset rows | pending |
| 06-04-1 | 4 | FORM-03/04/09/10 | T-06-07 | Host/inline modes, class grammar and key count | pending |
| 06-04-2 | 4 | FORM-09/10 | T-06-08 | Workflow/custom icon precedence | pending |
| 06-05-1 | 5 | FORM-06/08/10 | T-06-09/10 | Filter endpoint/golden, retained GET controls and pack-owned trailing wrapper | pending |
| 06-05-2 | 5 | FORM-05/08 | T-06-09 | Empty/nonempty layout replacement before dispatch, isolation, helper.form identity, hook omission and quiet legacy inputs | pending |
| 06-06-1 | 6 | FORM-11/12 | T-06-11 | Documented form-specific diagnostics, truthful messages and unchanged context/list checks | pending |
| 06-06-2 | 6 | FORM-02/10/12 | T-06-12 | Provider-aware delete/polymorphic W292, semantic availability, single inline-render counts, host opt-outs and disabled-icon strict/log fallback | pending |
| 06-07-1 | 7 | FORM-06/07 | T-06-13/SC | Locked-JS native modal SubmitEvent/FormData | pending |
| 06-07-2 | 7 | FORM-06/08 | T-06-14 | Nested cancel and encoded filter reset | pending |
| 06-07-3 | 7 | FORM-05/07/08 | T-06-SC | Expanded nox crispy_floor suite | pending |
| 06-08-1 | 7 | FORM-10/11/12/13 | T-06-15 | Canonical config recipe render and live key count | pending |
| 06-08-2 | 7 | FORM-05/08/09/13 | T-06-15 | Executable helper/custom-template recipes, including clearing-inputs suppression migration to None hook with preserved hidden controls | pending |
| 06-08-3 | 7 | FORM-13 | T-06-16 | Strict docs, paired Breaking/migration and example | pending |
| 06-09-1..2 | 8 | FORM-01..13 | T-06-17 | Full suites, history, security, docs/lint, URLconf-registered example checks, German form values, feature landing pages, doc links and browser evidence | pending |

## Wave 0 Requirements

- [ ] Capture and commit before-change form goldens before any product edits.
- [ ] Add real `{% crispy %}` fixture coverage, including helper context shadowing and no-layout helpers.
- [ ] Preserve custom helper constructor signatures; test class layout cloning, two instances and repeated render.
- [ ] Cover replacement/omission via `get_form_actions()` and legacy `add_input()` without new warnings.
- [ ] Exercise empty caller Layout() replacement before/between real crispy renders; preparation must precede the dispatch truthiness guard.
- [ ] Distinguish singleton-map monkeypatch tests from nested live-floor override_settings tests.
- [ ] Count custom inline renderer calls and preserve host placement/opt-outs while testing semantic disabled-icon strict/log fallback.
- [ ] Execute the documented helper.inputs=[] suppression migration to a None-returning hook with unchanged fields/hidden GET values.
- [ ] Establish a reproducible oldest-crispy session without raising declared floors or replacing the existing matrix.
- [ ] Before wave 1 sampling, obtain the compatible isolated Node and exact locked packages, or record the blocker; create the absolute-runtime wrapper and evidence without changing dependency declarations.
- [ ] Test native SubmitEvent/FormData behavior without replacing it with a polyfill that hides failures.

## Manual-Only Verifications

| Behavior | Requirement | Why manual | Instructions |
|----------|-------------|------------|--------------|
| Final appearance and focus/tooltip behavior | FORM-04/10/13 | DOM tests cannot establish visual quality | Inspect example save/delete/cancel/filter controls in label, both and icon modes; use keyboard and tooltip interactions |
| Integrated example flows | FORM-06/08 | Complements automated payload assertions | Submit a modal form, cancel a form, apply and reset a filter; confirm navigation and retained sort/order |

## Validation Sign-Off

- [ ] Every task has automated verification or explicit Wave 0 dependency.
- [ ] No three consecutive tasks lack automated verification.
- [ ] All missing test targets are created before use.
- [ ] Commands terminate (no watch mode), with explicit failure signals.
- [ ] Focused-shard feedback timing measured.
- [ ] Expanded tests pass at declared dependency floors.
- [ ] `nyquist_compliant: true` reflects actual coverage, not merely this draft.

**Approval:** pending execution evidence. Research probes establish feasibility only.

## Round 1 review traceability

The nine PLAN files contain append-only Round 1 ledgers anchored to REVIEWS commit 6089258. H-LOCATIONS,
H-KEYSET and H-EARLY-UTILITIES are produced in 06-02; diagnostic/provider findings are executable in 06-06;
the remaining consumer/helper/docs/runtime findings are assigned to their affected tasks. Existing confirmation
POST and new clicked-submitter evidence stay separate. H-MAIN is resolved by the explicit user decision
D-18; actual working-branch prerequisite verification remains pending execution.

## Round 2 review traceability — b883e7b

All five actionable findings from the cycle 2 snapshot are assigned to executable PLAN content; their tests
remain pending implementation. Affected plans append Round 2 ledgers without modifying Round 1 dispositions.

| Finding | Executable coverage | Required evidence |
|---|---|---|
| M-SETTINGS-LIFECYCLE | 06-01 spec; 06-03 task 1; 06-08 task 1 | Snapshot map unchanged by post-import Django map override; singleton monkeypatch changes rendered controls; live floor changes/restores unmapped kinds |
| M-EMPTY-REPLACEMENT | 06-01 spec; 06-05 tasks 1/2 | get_attributes preparation before dispatch; real tag renders with Layout() before/between renders, default/None/empty groups, caller identity isolation and no restored discarded fields |
| L-SUPPRESSION-MIGRATION | 06-05 explicit disposition; 06-08 tasks 2/3 | Old clearing-inputs case retains stock layout actions; documented None-hook recipe omits them and preserves fields/hidden controls; paired Breaking/migration |
| M-ICON-AVAILABILITY | 06-01 spec; 06-06 task 2 | Semantic resolution without renderer probes, one inline call per icon/both control, zero label/static/host calls, host opt-outs preserved and disabled-host strict/log fallback |
| L-EXAMPLE-COVERAGE | 06-08 example change; 06-09 task 2/additional gate | Example-settings execution of test_i18n.py, feature landing renders and test_doc_links.py alongside the retained system-check/docs-sync gates |

H-OVERLAY-PROVENANCE remains a single-reviewer unconfirmed missing-API claim, explicitly dispositioned in
06-03's Round 2 ledger. The spec and nested owner regressions still must prove the current invocation/page
boundary; no new provenance API or ownership redesign is introduced. Locked D-01 through D-18, exact crispy
floors, before-change goldens and all prior review repairs remain required. Planning validation does not mark
any feature, floor or browser acceptance gate passed.
