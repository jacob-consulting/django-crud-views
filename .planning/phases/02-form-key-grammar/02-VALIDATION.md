---
phase: "02"
slug: "form-key-grammar"
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-26"
---

# Phase 02 — Validation Strategy

## Test Infrastructure

| Property | Value |
|----------|-------|
| Framework | pytest 9.1.1 with pytest-django 4.14.0 |
| Config file | pyproject.toml; tests/test1/conftest.py |
| Quick run command | `.venv/bin/pytest tests/test1/test_button_classes.py tests/test1/test_button_classes_checks.py tests/test1/test_label_mode.py tests/test1/test_action_label_mode_config.py -q` |
| Full suite command | `.venv/bin/pytest tests -n auto` |
| Feedback target | Focused tests under 30 seconds; full-suite duration measured at execution |

## Sampling Rate

- After each task: run the quick command and task-specific automated checks.
- After each wave: run the full Python suite.
- Before verification: full suite, Vitest, strict docs build, Ruff lint and format checks must pass.
- Maximum focused feedback latency target: 30 seconds.

## Per-Requirement Verification Map

Plan 02-01 executes three serial tasks in wave 1. Every task gate includes an explicit failure predicate.

| Requirement | Task | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|-------------|------|------------|-----------------|-----------|-------------------|-------------|--------|
| KEYS-01 | 02-01-03 | T-02-03 | Accurate grammar; unchanged rendering | Docs build + prose review | `.venv/bin/mkdocs build --strict` | Yes | Pending execution |
| KEYS-02 | 02-01-01, 02-01-02 | T-02-01, T-02-03 | Finite grammar; malformed keys diagnose safely; escaping retained | Real check tracer + matrix | `.venv/bin/pytest tests/test1/test_button_classes_checks.py -q` | Yes; add cases | Pending execution |
| KEYS-03 | 02-01-01, 02-01-02 | T-02-02 | Future button-data locations cannot broaden grammar | Unit + import smoke | Quick command above; import command below | Yes; add isolation case | Pending execution |
| KEYS-04 | 02-01-03 | — | One exact count equals the actual table | Documentation contract | `.venv/bin/pytest tests/test1/test_button_classes.py -q` | Yes; add count assertion | Pending execution |

## Per-Task Verification Map

| Task | First proof | Automated gate | Failure predicate |
|------|-------------|----------------|-------------------|
| 02-01-01 | New settings/check/lookup tracer first fails with W362 | `.venv/bin/pytest tests/test1/test_button_classes_checks.py::test_form_submit_icon_key_reaches_checks_and_lookup tests/test1/test_button_classes_checks.py -q` | Tracer/existing checks fail after implementation; new test is created first |
| 02-01-02 | Complete dual-source kind/mode and boundary matrix | Quick command above; rendering regression below | Accepted key warns; invalid shape passes/crashes; diagnostics/floors/fallback/rendering drift |
| 02-01-03 | Count guard first fails with 64 versus live 70 | `.venv/bin/pytest tests/test1/test_button_classes.py tests/test1/test_label_mode_docs.py -q`; strict docs build | Count missing/duplicate/unequal or documentation/build regressions |

Five classified edge predicates are explicit in the plan. KEYS-01 and KEYS-02 remain flagged unresolved
unclassified probe assumptions for end-of-phase review. See `02-SOURCE-AUDIT.md` for all seven rows
and the zero-kept-prohibitions precision result.

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. Add the finite kind/mode acceptance matrix in both theme
and settings layers, malformed-key diagnostics, future-location isolation, form-mode fallback cases, and the
numeric documentation guard during the planned tasks. No framework installation is required.

## Regression and Import Checks

- `.venv/bin/python -c 'from django.conf import settings; settings.configure(); import crud_views.lib.button_classes'`
- `.venv/bin/pytest tests/test1/test_button_classes_templates.py tests/test1/test_crispy_buttons.py tests/test1/test_action_menus_golden.py tests/test1/test_label_mode_docs.py -q`
- Preserve exact W362 warning type, ID, messages and hints; known form kind plus invalid mode uses the mode branch.
- Preserve explicit None/empty mode overrides, existing variant keys, and the E108 rejection of form defaults.
- No templates or golden files change, and golden regeneration stays disabled.

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Instructions |
|----------|-------------|------------|--------------|
| Canonical grammar explanation is accurate | KEYS-01 | A docs build cannot establish prose meaning | Review the grammar table, valid/invalid examples, one fallback example, and Phase 6 boundary against D-01–D-11 |

## Environment Note

Research observed Ruff 0.16.10 while pyproject.toml requests >=0.17,<0.18. Resolve through the normal environment
workflow or report the exact limitation before claiming a manifest-aligned lint gate; do not alter dependency
constraints as part of this phase.

## Validation Sign-Off

- [ ] Finalized tasks each have automated verification
- [ ] No three consecutive tasks without automated checks
- [ ] All planned test references exist or are created by an earlier task
- [ ] No watch-mode flags
- [ ] Focused feedback latency under 30 seconds
- [ ] nyquist_compliant: true set after validation

**Approval:** Pending execution and validation.
