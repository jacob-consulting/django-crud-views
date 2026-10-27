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
| Quick JavaScript | `npm test -- tests/js/modal.test.js tests/js/viewset.test.js tests/js/list.filter.test.js` |
| Full suites | `.venv/bin/pytest tests -n auto` and `npm test` |
| Runtime | Not measured; measure during execution, do not infer from inherited research |

## Sampling Rate

- After each task commit, run its targeted Python or JavaScript shard.
- After an integrated wave, run the full Python and JavaScript suites.
- Before phase verification, run the declared-floor session, strict docs build, lint and formatting,
  example checks and documentation synchronization.
- Target feedback latency: under 60 seconds for a focused shard; split if measurement exceeds it.

## Per-Task Verification Map

The planner must bind these behaviors to its actual task IDs, waves and phase-unique threat IDs before finalization.
Every command must have an observable failing direction in the PLAN, and every requirement must be represented.

| Requirement | Behavior / secure behavior | Test target | Status |
|-------------|----------------------------|-------------|--------|
| FORM-01 | Baselines committed before product markup edits | Golden tests plus commit-history check | pending |
| FORM-02 | Exact form contract, no irrelevant action keys, cancel-only URL | `test_button_data.py` | pending |
| FORM-03/04 | Three modes, class lookup, host/inline icons, accessible hidden labels | `test_button_leaves.py`, class tests | pending |
| FORM-05 | Constructor/CSS/attributes, template precedence and `%s`, no legacy input alias | `test_crispy_buttons.py` | pending |
| FORM-06 | Names/values/IDs and normal/modal clicked-submitter payload unchanged | CRUD tests, modal/viewset JS tests | pending |
| FORM-07 | Literal and SafeString values cannot inject nodes/attributes or execute template syntax | Parameterized render/security cases | pending |
| FORM-08 | Filter controls once per form, hidden sort/order preserved, reset ID and behavior | Real crispy/filter tests, list.filter JS | pending |
| FORM-09 | Registry defaults, workflow icon and explicit form overrides | Icon registry and workflow render tests | pending |
| FORM-10/11 | Floors, whole-map selection and first-owner precedence through real crispy | Mode/config and integration tests | pending |
| FORM-12 | E210/E211/W291/W292 plus dynamic strict/log fallback | Check and render tests | pending |
| FORM-13 | Breaking/migration/docs/example accuracy and downstream acceptance note | Strict docs build, example checks | pending |

## Wave 0 Requirements

- [ ] Capture and commit before-change form goldens before any product edits.
- [ ] Add real `{% crispy %}` fixture coverage, including helper context shadowing and no-layout helpers.
- [ ] Preserve custom helper constructor signatures; test class layout cloning, two instances and repeated render.
- [ ] Cover replacement/omission via `get_form_actions()` and legacy `add_input()` without new warnings.
- [ ] Establish a reproducible oldest-crispy session without raising declared floors or replacing the existing matrix.
- [ ] Inspect and reconcile installed JS versions with the lockfile; do not silently change dependency declarations.
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
