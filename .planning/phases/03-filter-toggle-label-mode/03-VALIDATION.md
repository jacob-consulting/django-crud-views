---
phase: "03"
slug: "filter-toggle-label-mode"
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-26"
---

# Phase 03 — Validation Strategy

## Test Infrastructure

| Property | Value |
|----------|-------|
| Framework | Existing pytest/pytest-django and Vitest/jsdom; observed versions in 03-RESEARCH.md |
| Config | pyproject.toml; vitest.config.js |
| Quick Python | `.venv/bin/pytest tests/test1/test_filter_toggle_label_mode.py tests/test1/test_i18n.py tests/test1/test_action_menus_golden.py -q` |
| Quick JavaScript | `npm test -- tests/js/list.filter.test.js` |
| Full suite | `.venv/bin/pytest tests -n auto` and `npm test` |
| Other gates | `.venv/bin/mkdocs build --strict`; `.venv/bin/ruff check`; `.venv/bin/ruff format --check` |
| Runtime | Focused checks target under 60 seconds; measure full-suite time during execution |

## Sampling Rate

- After each task: run the focused Python and/or JavaScript command for the touched behavior.
- After each wave: run both focused suites and pinned-filter regressions.
- Before verification: run all project gates; report pre-existing environment failures separately.
- Feedback target: 60 seconds for focused checks, excluding full-suite gates.

## Per-Task Verification Map

Task IDs below are provisional until the planner assigns the final plan/task layout.

| Task | Requirement | Threat Ref | Secure Behavior | Type | Command | Exists | Status |
|------|-------------|------------|-----------------|------|---------|--------|--------|
| Mode tracer/matrix | FILT-01 | Assigned in plan | Preserve escaping and visibility | Python | `.venv/bin/pytest tests/test1/test_filter_toggle_label_mode.py tests/test1/test_action_menus_golden.py -q` | New module required | Pending |
| Icon-less/state tests | FILT-02, FILT-03 | Assigned in plan | Preserve CSRF and collapse failure behavior | JS | `npm test -- tests/js/list.filter.test.js` | Yes; extend cases | Pending |
| Translation | FILT-04 | — | No raw HTML interpolation | Python | `.venv/bin/pytest tests/test1/test_i18n.py tests/test1/test_filter_toggle_label_mode.py -q` | New module required | Pending |
| Documentation | FILT-01–04 | — | N/A | Docs | `.venv/bin/mkdocs build --strict` | Yes | Pending |

## Wave 0 Requirements

- [ ] Add dedicated filter-mode test module before commands reference its new tests.
- [ ] Capture raw pre-change filter output before implementation; normalized toolbar goldens alone are insufficient.
- [ ] Add label-only and visible-label JS fixtures with both initial states and error paths.
- [ ] Add translation assertions that distinguish gettext use from identical English/German spelling.

Existing frameworks are installed. Record manifest/environment mismatches from research; dependency upgrades are
outside this phase. The planner must replace provisional task IDs with its final task and threat mapping.

## Manual-Only Verifications

All required behaviors can be checked automatically. Optional visual smoke testing may inspect host/mixed icons
and translated/custom labels, but does not replace automated assertions.

## Validation Sign-Off

- [ ] Every task has automated verification or explicit Wave 0 dependency.
- [ ] No three consecutive tasks lack automated verification.
- [ ] All new test references are created before use.
- [ ] No watch-mode flags.
- [ ] Focused feedback time measured.
- [ ] Nyquist compliance recorded after execution validation.

**Approval:** Pending.
