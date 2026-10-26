---
phase: "04"
slug: "alert-dismiss-adapter"
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-26"
---

# Phase 04 — Validation Strategy

## Test Infrastructure

| Property | Value |
|----------|-------|
| Framework | Existing pytest/Django and Vitest/jsdom |
| Config | pyproject.toml; vitest.config.js; tests/js/helpers/setup.js |
| Quick Python | `.venv/bin/pytest tests/test1/test_alerts.py tests/test1/test_messages.py -q` |
| Quick JS | `npm --prefix . test -- tests/js/adapters.test.js tests/js/viewset.test.js` |
| Full Python | `.venv/bin/pytest tests -n auto` |
| Full JS | `npm --prefix . test` |
| Docs | `.venv/bin/mkdocs build --strict` |
| Estimated quick runtime | Under 10 seconds; research baseline 50 Python and 25 JS tests passed |

Installed JS/Ruff versions differ from manifests; execution must record the actual versions and disposition,
without claiming manifest-version validation. See 04-RESEARCH.md. No new framework is required.

## Sampling Rate

- After each task commit: run relevant quick suite; every baseline golden comparison runs without update mode.
- After each implementation wave: run both quick suites and full JS tests.
- Before phase verification: full Python/JS, strict docs, Ruff check/format, source audit and example smoke.
- Max focused feedback latency: 10 seconds.

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 04-01 | 1 | ALRT-01 | T-04-01 | Exact baseline before product edits | golden/history | `.venv/bin/pytest tests/test1/test_alerts.py tests/test1/test_messages.py -q` | Suite exists; new golden/test | pending |
| 04-01-02 | 04-01 | 1 | ALRT-02, ALRT-03 | T-04-02 | Marker selects nearest frame; fallback belongs to adapter; message assertions move with template | rendered tracer | Quick Python followed by Quick JS | Suites exist; new tracer | pending |
| 04-01-03 | 04-01 | 1 | ALRT-02 | T-04-01 | Escaping, translated name and non-dismissible behavior | render/response | Quick Python | Extend existing suites | pending |
| 04-02-01 | 04-02 | 2 | ALRT-03 | T-04-03 | Present component owns no-op/throw; lazy namespace preserved | JS regression | Quick JS | Extend existing suite | pending |
| 04-02-02 | 04-02 | 2 | ALRT-02, ALRT-03 | T-04-03, T-04-04 | Dynamic/nearest selection; two controls; surfaced errors/missing key; repeated clicks | JS regression | Quick JS followed by `npm --prefix . test` | Extend suite; reuse listenerErrors | pending |
| 04-03-01 | 04-03 | 3 | ALRT-04 | T-04-05 | Recipe preserves colour/escaping; core-only nonempty subset audit; settings hook list | render/docs/audit | Quick Python and `.venv/bin/mkdocs build --strict` | Suite/docs exist; new recipe/guard tests | pending |
| 04-03-02 | 04-03 | 3 | ALRT-04 | T-04-06 | Paired migration states scripts and legacy behavior accurately | docs | `.venv/bin/mkdocs build --strict` | Existing | pending |
| 04-03-03 | 04-03 | 3 | ALRT-01..04 | T-04-01..06 | Real browser behavior and all quality gates evidenced | smoke/full suite/history | Full gates below | Existing tools; new acceptance artifact | pending |

Regression matrix: Bootstrap instance close; no component removal; late global/object/function namespaces;
preassigned and call-time replacement adapters; no-op and throwing custom adapters (including mutation before
throw); throwing present Bootstrap component; nested click, nearest role, orphan marker, unrelated/non-Element
targets; dynamic modal-like insertion; non-dismissible output; escaping, translated labels and frame/body overrides.
For listener exceptions and ignored targets reuse listenerErrors from tests/js/helpers/errors.js; assert
original errors or an empty array. Include two controls in one frame, outer/sibling retention and the
missing-adapter TypeError and an unmarked alert-body click with no call/error/removal. Each new JS case owns
a fresh cv/adapters object before nested mutation; restore untouched original descriptors and console spies,
preserving shared jQuery stubs.

## Wave 0 Requirements

- [ ] Add deterministic dismissible golden/test and commit BEFORE any template change (ALRT-01).
- [ ] Add meaningful regressions to existing adapter/delegation suites.
- [ ] Update message and alert attribute assertions together; preserve all other output.
- [x] Final planner task IDs and phase-unique threat references replace provisional mapping above.

The before-change golden is task 04-01-01's separate first commit. The product tracer is 04-01-02 and
shares that exact golden between Python rendering and jsdom interaction. Both message assertion updates
belong to the tracer, whose combined Python/JS gates must pass before its commit. The six-file tracer is
deliberate; 04-01-03 adds broader regressions afterward. No framework/scaffold installation is needed.

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Real example flash messages close | ALRT-02, ALRT-04 | Browser transition and script integration | Create/update an object in examples/bootstrap5; inspect new marker and core script order; click and wait for close; repeat with namespace lacking Alert and a dynamically inserted alert. Record observations or an actual browser blocker. |
| Golden chronology | ALRT-01 | Commit ordering | Confirm a baseline-only commit precedes template change; final golden diff changes only dismissal attribute. |

Run example docs sync from examples/bootstrap5: `../../.venv/bin/pytest test_docs_sync.py -q`.
The plain `rg -n 'data-bs-' src/crud_views/templates` command is an audit: validate its output against
the exact dropdown paths named in theme.md, not merely its exit status.

Automated allowlist coverage is planned in `test_stock_bootstrap_data_attributes_are_dropdown_only`:
scan exactly `src/crud_views/templates`, using paths relative to that root. Only
`crud_views/tags/actions_menu.html`, `crud_views/tags/actions_menu_toggle.html` and
`crud_views/snippets/language_selector.html` are allowed; require nonempty matches and matches <= ALLOWED,
not equality. The wrapper need not match. Report forbidden paths. For historical red, copy the core tree
to a temporary directory and replace its alert template with the baseline commit's snapshot via git show;
invoke the same helper there and confirm the alert path fails, without changing the checkout. Baseline:
four matching lines in alert.html, actions_menu_toggle.html and language_selector.html.

Permanent negative coverage: `test_core_bootstrap_data_attribute_guard_rejects_forbidden_path` builds an
allowed tree under tmp_path and confirms success, adds a forbidden alert file, and requires AssertionError
naming that relative path. This lasts independently of the one-time historical git-show probe.

## Final Execution Gates and Evidence

Run from repository root unless stated otherwise:

- `.venv/bin/pytest tests -n auto`
- `npm --prefix . test`
- `.venv/bin/mkdocs build --strict`
- `.venv/bin/ruff check`
- `.venv/bin/ruff format --check`
- `.venv/bin/python examples/bootstrap5/manage.py check`
- From examples/bootstrap5: `../../.venv/bin/pytest test_docs_sync.py -q`

Record actual browser/version, page/action, rendered marker/script order, Bootstrap transition close,
fresh-message missing-Alert close and post-load inserted message close in `04-ACCEPTANCE.md`.
Plan 04-03 contains the exact reproducible browser procedure. Missing browser/server/CDN evidence stays
unverified and routes to end-of-phase human verification. System check/docs sync are not browser evidence.
Retain all five unresolved classifier assumptions from `04-SOURCE-AUDIT.md`; two resolved ALRT-03
repeated-call/click predicates are explicit 04-02 must-haves. No new lifecycle guarantee is claimed.

Planning verification: all three plans passed frontmatter/structure checks; baseline focused suites passed
50 Python / 25 JS tests. Product implementation and browser acceptance remain pending. Installed-tool drift
and any pre-existing full-gate failures must be recorded honestly, without weakening gates or changing manifests.

## Validation Sign-Off

- [x] All tasks have automated verification or Wave 0 dependencies.
- [x] No three consecutive tasks lack automated feedback.
- [x] Wave 0 covers all missing references; no watch flags.
- [ ] Focused feedback latency stays under 10 seconds.
- [ ] Required quality gates and example smoke have evidence.
- [ ] Set nyquist_compliant only after validation is actually complete.

**Approval:** pending execution validation.
