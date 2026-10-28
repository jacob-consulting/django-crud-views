---
phase: "06"
slug: "form-button-leaf"
status: validated
nyquist_compliant: true
wave_0_complete: true
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
| Runtime | Measured in 06-09: full Python 57.25 s (4445 tests, `-n auto`); full JS 2.90 s (223 tests); focused repair shard 1.79 s; crispy_floor 42 s for both sessions |

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

All tasks map to executable PLAN commands and immediate fails_when conditions. Status values come from 06-09 measurements at HEAD `e40b0de` (06-ACCEPTANCE.md); a row says passed only when its gate was re-run there.

| Task | Wave | Requirements | Threat Ref | Verification target | Status |
|---|---|---|---|---|---|
| 06-01-1..3 | 1 | FORM-01/02/05/06/08/11 | T-06-01 | Real crispy tracer; spec and executing-branch prerequisite evidence (D-18); five golden captures and commit history | passed (06-09 re-verified: baselines `2956f3e`/`98b71ed` ancestral, `src` tree `dcc38f4` unchanged in both, ACCEPTANCE §3) |
| 06-02-1 | 2 | FORM-02/03/04/06/07 | T-06-02/03 | Real leaf plus atomic location consumers, utilities, exhaustive EXPECTED_KEYS and docs count | passed (full suite 4445, 06-09) |
| 06-02-2 | 2 | FORM-05/07 | T-06-02/03/04 | Custom templates, literal/SafeString/lazy attrs; floor invariant | passed (full suite; high-threat shard 109 passed; crispy_floor 1877×2) |
| 06-02-3 | 2 | FORM-06 | T-06-04 | Golden diffs, CRUD and cancel payloads | passed (ACCEPTANCE §3/§4) |
| 06-03-1..2 | 3 | FORM-10/11 | T-06-05/06 | Singleton maps versus lazy floor overrides; whole maps, actual render-form identity, multiple FormActions and nested formset rows | passed (full suite; repair shard ACCEPTANCE §5) |
| 06-04-1 | 4 | FORM-03/04/09/10 | T-06-07 | Host/inline modes, class grammar and key count | passed (full suite) |
| 06-04-2 | 4 | FORM-09/10 | T-06-08 | Workflow/custom icon precedence | passed (full suite) |
| 06-05-1 | 5 | FORM-06/08/10 | T-06-09/10 | Filter endpoint/golden, retained GET controls and pack-owned trailing wrapper | passed (full suite) |
| 06-05-2 | 5 | FORM-05/08 | T-06-09 | Empty/nonempty layout replacement before dispatch, isolation, helper.form identity, hook omission and quiet legacy inputs | passed (repair shard: guards `(True, True, 0, False)`) |
| 06-06-1 | 6 | FORM-11/12 | T-06-11 | Documented form-specific diagnostics, truthful messages and unchanged context/list checks | passed (full suite) |
| 06-06-2 | 6 | FORM-02/10/12 | T-06-12 | Provider-aware delete/polymorphic W292, semantic availability, single inline-render counts, host opt-outs and disabled-icon strict/log fallback | passed (repair shard: unknown prefix W292, one call per icon/both render) |
| 06-07-1 | 7 | FORM-06/07 | T-06-13/SC | Locked-JS native modal SubmitEvent/FormData | passed (06-js-verify.sh 223/223, lock re-asserted) |
| 06-07-2 | 7 | FORM-06/08 | T-06-14 | Nested cancel and encoded filter reset | passed (06-js-verify.sh 223/223) |
| 06-07-3 | 7 | FORM-05/07/08 | T-06-SC | Expanded nox crispy_floor suite | passed (Django 4.2.30 and 6.0.9: 1877 each) |
| 06-08-1 | 7 | FORM-10/11/12/13 | T-06-15 | Canonical config recipe render and live key count | passed (full suite) |
| 06-08-2 | 7 | FORM-05/08/09/13 | T-06-15 | Executable helper/custom-template recipes, including clearing-inputs suppression migration to None hook with preserved hidden controls | passed (full suite) |
| 06-08-3 | 7 | FORM-13 | T-06-16 | Strict docs, paired Breaking/migration and example | passed (mkdocs --strict exit 0; example gates ACCEPTANCE §8) |
| 06-09-1 | 8 | FORM-01..13 | T-06-17 | Full suites, history, security, payload, cycle-3 repairs | passed (ACCEPTANCE §2–§7) |
| 06-09-2 | 8 | FORM-04/06/08/10/13 | T-06-17 | Docs/lint, URLconf-registered example checks, German form values, feature landing pages, doc links and browser evidence | passed except: whole-repo `ruff format --check` exit 1 (9 pre-existing planning Markdown files, WINDOWS #4); hover tooltip, visual quality, screen reader and migration readability pending human (ACCEPTANCE §8–§11) |

## Threat verification (06-09, measured)

| Threats | Severity | Evidence | Status |
|---|---|---|---|
| T-06-02, T-06-03, T-06-15 | high | Literal/hostile/`{{ request.user }}` leaf and recipe tests (high-threat shard 109 passed) | mitigated |
| T-06-05, T-06-09 | high | Owner and filter-layout isolation tests, including the cycle-3 repair shard (102 passed) | mitigated |
| T-06-13 | high | Native SubmitEvent/FormData modal suite on the locked jsdom runtime (JS shard 123 passed) | mitigated |
| T-06-SC | high | Lock sha256 and 71 lock-matched packages re-asserted by 06-js-verify.sh; floor sessions install declared pins only; no install in 06-09 | mitigated; WINDOWS #6 dev-only `undici` audit advisory stays open (not a form-render finding) |
| T-06-01, 04, 06, 07, 08, 10, 11, 12, 14, 16, 17 | medium | ACCEPTANCE §3/§4/§7 | mitigated |

No high or critical threat is unresolved. The medium items are listed with their dispositions above, not omitted.

## Wave 0 Requirements

- [x] Capture and commit before-change form goldens before any product edits. (`2956f3e`, `98b71ed`)
- [x] Add real `{% crispy %}` fixture coverage, including helper context shadowing and no-layout helpers.
- [x] Preserve custom helper constructor signatures; test class layout cloning, two instances and repeated render.
- [x] Cover replacement/omission via `get_form_actions()` and legacy `add_input()` without new warnings.
- [x] Exercise empty caller Layout() replacement before/between real crispy renders; preparation must precede both helper and layout truthiness guards; real-tag dispatch must occur even when len(helper) is zero.
- [x] Distinguish singleton-map monkeypatch tests from nested live-floor override_settings tests.
- [x] Count custom inline renderer calls and preserve host placement/opt-outs while testing semantic disabled-icon strict/log fallback.
- [x] Execute the documented helper.inputs=[] suppression migration to a None-returning hook with unchanged fields/hidden GET values.
- [x] Establish a reproducible oldest-crispy session without raising declared floors or replacing the existing matrix.
- [x] Before wave 1 sampling, obtain the compatible isolated Node and exact locked packages, or record the blocker; create the absolute-runtime wrapper and evidence without changing dependency declarations.
- [x] Test native SubmitEvent/FormData behavior without replacing it with a polyfill that hides failures.

## Manual-Only Verifications

| Behavior | Requirement | Why manual | Instructions | 06-09 status |
|----------|-------------|------------|--------------|--------------|
| Final appearance and focus/tooltip behavior | FORM-04/10/13 | DOM tests cannot establish visual quality | Inspect example save/delete/cancel/filter controls in label, both and icon modes; use keyboard and tooltip interactions | Keyboard focus, `:focus-visible`, accessible names and focus tooltips observed in real headless Chromium in all three modes (ACCEPTANCE §9). **Pending human:** hover tooltips (not observed in the harness), visual quality and the screen-reader announcement |
| Integrated example flows | FORM-06/08 | Complements automated payload assertions | Submit a modal form, cancel a form, apply and reset a filter; confirm navigation and retained sort/order | Observed in real headless Chromium in all three modes: modal delete submit through a nested child, pointer and keyboard cancel, filter apply, and a reset that keeps `sort`/`dir` (ACCEPTANCE §9) |

## Validation Sign-Off

- [x] Every task has automated verification or explicit Wave 0 dependency.
- [x] No three consecutive tasks lack automated verification.
- [x] All missing test targets are created before use.
- [x] Commands terminate (no watch mode), with explicit failure signals.
- [x] Focused-shard feedback timing measured (repair shard 1.79 s; JS full 2.90 s).
- [x] Expanded tests pass at declared dependency floors (crispy_floor, Django 4.2.30 and 6.0.9, 1877 each).
- [x] `nyquist_compliant: true` reflects actual coverage, not merely this draft.

**Approval:** automated coverage is complete and measured (06-ACCEPTANCE.md, HEAD `e40b0de`). Two gates stay
open and are not reported as passed:
- the whole-repo `ruff format --check`, which fails on 9 pre-existing planning Markdown files (WINDOWS #4).
  Code and every Phase 06 changed file are formatted.
- the human-only checks in ACCEPTANCE §9: hover tooltip, visual quality, screen reader, migration readability.

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

## Manual revision after cycle 3 — fcc404f

User chose manual revision after the automatic three-cycle cap. No fourth review was run. The report's
cycle-3 counts remain historical; the following plan repairs have structural validation only, with execution
and independent re-review pending.

| Finding | Plan ownership | Required execution evidence |
|---|---|---|
| H-HELPER-TRUTHINESS | 06-01 spec; 06-05 tasks 1/2; 06-09 audit | Both helper and prepared layout truthy at len(helper)==0; actual tag reaches render_layout for default/None/empty groups before/between replacement renders |
| M-OUTER-HELPER-PAGE | 06-01 spec; 06-03 task 2 | Distinct page P/enclosing helper H/current helper None fixture chooses P; page None uses settings; ordinary/falsey owners stop lookup |
| L-FORMSET-PAGE-CONTEXT | 06-03 task 2 | Actual Formsets -> inclusion -> row crispy and recursive child dispatch retain scoped page fallback without copying whole context or leaking state |
| L-UNREGISTERED-FORM-ICON | 06-01 spec; 06-06 task 2 | Direct unknown-prefix and unusable renderer produce W292/strict/log fallback; no renderer probe; raw class/valid inline/host opt-out behavior preserved |

Manual planning checks: all 9 frontmatter/structure validations passed; 18/18 decisions and 13/13 requirements covered; dependency waves, task file ownership and same-wave isolation passed; 28 verification blocks have failure conditions. The command-path tool returned no findings but marks Python commands not_applicable. An installed-crispy probe reproduced the layout-only false helper and confirmed both local __bool__ methods admit dispatch with len(helper)==0. These checks do not constitute feature implementation or independent convergence.

## Validation Audit 2026-10-28

| Metric | Count |
|---|---|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |
