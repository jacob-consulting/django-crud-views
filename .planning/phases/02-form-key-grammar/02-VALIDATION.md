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

Task IDs and threat references will be reconciled with the finalized plans.

| Requirement | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|-------------|-----------------|-----------|-------------------|-------------|--------|
| KEYS-01 | No new rendering or template evaluation | Docs build + prose review | `.venv/bin/mkdocs build --strict` | Yes | Pending |
| KEYS-02 | Finite key grammar; malformed/non-string keys do not crash checks | Unit/check integration | `.venv/bin/pytest tests/test1/test_button_classes_checks.py -q` | Yes; add cases | Pending |
| KEYS-03 | Future location additions do not broaden the class grammar | Unit + import smoke | Quick command above | Yes; add future-location guard | Pending |
| KEYS-04 | Documented count matches actual shipped keys | Documentation contract | `.venv/bin/pytest tests/test1/test_button_classes.py -q` | Yes; add count assertion | Pending |

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
