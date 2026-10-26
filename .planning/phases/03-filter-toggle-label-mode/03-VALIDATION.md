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
| Quick JavaScript | `npm --prefix . test -- tests/js/list.filter.test.js` |
| Full suite | `.venv/bin/pytest tests -n auto` and `npm --prefix . test` |
| Other gates | `.venv/bin/mkdocs build --strict`; `.venv/bin/ruff check`; `.venv/bin/ruff format --check` |
| Runtime | Focused checks target under 60 seconds; measure full-suite time during execution |

## Sampling Rate

- After each task: run the focused Python and/or JavaScript command for the touched behavior.
- After each wave: run both focused suites and pinned-filter regressions.
- Before verification: run all project gates; report pre-existing environment failures separately.
- Feedback target: 60 seconds for focused checks, excluding full-suite gates.

## Per-Task Verification Map

Final plan mapping: 03-01 runs in Wave 1; 03-02 depends on it and runs in Wave 2. Each task includes automated
verification with an immediate fails_when sibling. These commands are acceptance gates to execute, not claimed passes.

| Task | Requirement | Threat Ref | Secure Behavior | Type | Command | Exists | Status |
|------|-------------|------------|-----------------|------|---------|--------|--------|
| 03-01-01 | FILT-01, FILT-02, FILT-03 | T-03-02 | Existing CSRF-bearing POST; raw output preservation | Python + JS | `.venv/bin/pytest tests/test1/test_filter_toggle_label_mode.py tests/test1/test_action_menus_golden.py tests/test1/test_button_leaves.py -q`; `npm --prefix . test -- tests/js/list.filter.test.js` | New Python module created first in task | Pending |
| 03-01-02 | FILT-01, FILT-02, FILT-03 | T-03-01, T-03-02, T-03-03, T-03-04 | Escaping, visibility, exact request, collapse-first and rejection behavior | Python + JS | Full focused matrix command in 03-01-PLAN.md; `npm --prefix . test -- tests/js/list.filter.test.js` | Existing files plus Task 1 module | Pending |
| 03-01-03 | FILT-04 | T-03-01 | Ordinary interpolation; catalog/runtime proof | Python + gettext | `msgfmt --check --check-format -o /dev/null src/crud_views/locale/de/LC_MESSAGES/django.po`; `.venv/bin/pytest tests/test1/test_i18n.py tests/test1/test_filter_toggle_label_mode.py tests/test1/test_context_button_template.py tests/test1/test_action_menus_golden.py -q` | Existing files plus Task 1 module | Pending |
| 03-02-01 | FILT-01, FILT-02, FILT-03, FILT-04 | T-03-05 | Accurate optional-hook and failure contract | Docs + Python | `.venv/bin/mkdocs build --strict`; `.venv/bin/pytest tests/test1/test_filter_toggle_label_mode.py tests/test1/test_label_mode_docs.py -q` | Existing files plus Wave 1 module | Pending |
| 03-02-02 | FILT-01, FILT-02, FILT-03, FILT-04 | T-03-SC | No installs or unreported failing gates | Focused + full phase gates | Focused commands and all five full project commands in 03-02-PLAN.md | Existing harnesses | Pending |

## Wave 0 Requirements

- [ ] 03-01-01 creates the dedicated module before invoking it, captures two raw default strings and commits the passing baseline before production edits.
- [ ] 03-01-01 writes and observes the failing both-mode integration test before implementing the tracer.
- [ ] 03-01-02 extends existing JS fixtures for label-only/visible labels, both initial states, adapter errors and outstanding requests.
- [ ] 03-01-03 adds explicit PO/MO membership and a distinct Unicode translation sentinel before catalog edits.

Existing frameworks are installed. Record manifest/environment mismatches from research; dependency upgrades are
outside this phase. No framework installation or separate scaffold plan is needed. The baseline and failing tests
are the opening steps of their owning tasks; wave_0_complete remains false until execution supplies evidence.

## Edge and Decision Coverage

03-SOURCE-AUDIT.md maps all 14 spec-less probe items to explicit must-have truths and tests; none was dropped or
auto-dismissed. All 11 locked decisions and all four requirements have task owners. Raw golden compatibility and
translation invocation are independent of normalized HTML and identical English/German spelling. Prohibition
precision retained zero bespoke items; canonical encoding/CSRF concerns are covered by the threats above.

## Manual-Only Verifications

All required behaviors can be checked automatically. Optional visual smoke testing may inspect host/mixed icons
and translated/custom labels, but does not replace automated assertions.

## Validation Sign-Off

- [x] Every task has automated verification or explicit Wave 0 dependency.
- [x] No three consecutive tasks lack automated verification.
- [x] All new test references have explicit creation before use in task ordering.
- [x] No watch-mode flags.
- [ ] Focused feedback time measured.
- [ ] Nyquist compliance recorded after execution validation.

**Approval:** Planning mapping complete; execution evidence and final sign-off pending.
