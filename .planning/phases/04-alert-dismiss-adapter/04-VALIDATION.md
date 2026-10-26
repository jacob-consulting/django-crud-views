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

The planner replaces provisional task IDs with its final decomposition while retaining every behavior below.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| baseline | TBD | 1 | ALRT-01 | — | Escaped rendering preserved | golden/history | `.venv/bin/pytest tests/test1/test_alerts.py -q` | Suite exists; add golden | pending |
| tracer | TBD | 1 | ALRT-02, ALRT-03 | planner assigns | Only marked control dismisses nearest alert | render/DOM/unit | Quick Python and Quick JS above | Extend existing suites | pending |
| expansion | TBD | subsequent | ALRT-02, ALRT-03 | planner assigns | Ignore unrelated targets; custom errors surface without forced removal | JS regression | Quick JS above | Add cases | pending |
| documentation | TBD | subsequent | ALRT-04 | — | Accurate public hook and escaping contract | docs/audit | `.venv/bin/mkdocs build --strict` | Existing | pending |
| example | TBD | final | ALRT-04 | — | Real message remains safely rendered | smoke | `.venv/bin/python examples/bootstrap5/manage.py check` | Existing | pending |

Regression matrix: Bootstrap instance close; no component removal; late global/object/function namespaces;
preassigned and call-time replacement adapters; no-op and throwing custom adapters (including mutation before
throw); throwing present Bootstrap component; nested click, nearest role, orphan marker, unrelated/non-Element
targets; dynamic modal-like insertion; non-dismissible output; escaping, translated labels and frame/body overrides.
For listener exceptions use a temporary window error listener and cleanup, following list.filter.test.js.

## Wave 0 Requirements

- [ ] Add deterministic dismissible golden/test and commit BEFORE any template change (ALRT-01).
- [ ] Add meaningful regressions to existing adapter/delegation suites.
- [ ] Update message and alert attribute assertions together; preserve all other output.
- [ ] Final planner task IDs and phase-unique threat references replace provisional mapping above.

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Real example flash messages close | ALRT-02, ALRT-04 | Browser transition and script integration | Create/update an object in examples/bootstrap5; inspect new marker and core script order; click and wait for close; repeat with namespace lacking Alert and a dynamically inserted alert. Record observations or an actual browser blocker. |
| Golden chronology | ALRT-01 | Commit ordering | Confirm a baseline-only commit precedes template change; final golden diff changes only dismissal attribute. |

Run example docs sync from examples/bootstrap5: `../../.venv/bin/pytest test_docs_sync.py -q`.
The plain `rg -n 'data-bs-' src/crud_views/templates` command is an audit: validate its output against
the exact dropdown paths named in theme.md, not merely its exit status.

## Validation Sign-Off

- [ ] All tasks have automated verification or Wave 0 dependencies.
- [ ] No three consecutive tasks lack automated feedback.
- [ ] Wave 0 covers all missing references; no watch flags.
- [ ] Focused feedback latency stays under 10 seconds.
- [ ] Required quality gates and example smoke have evidence.
- [ ] Set nyquist_compliant only after validation is actually complete.

**Approval:** pending execution validation.
