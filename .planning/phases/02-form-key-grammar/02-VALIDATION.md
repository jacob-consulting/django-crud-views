---
phase: "02"
slug: "form-key-grammar"
status: executed
nyquist_compliant: true
wave_0_complete: true
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
| KEYS-01 | 02-01-03 | T-02-03 | Accurate grammar; unchanged rendering | Docs build + prose review | `.venv/bin/mkdocs build --strict` | Yes | Automated pass; human prose review pending |
| KEYS-02 | 02-01-01, 02-01-02 | T-02-01, T-02-03 | Finite grammar; malformed keys diagnose safely; escaping retained | Real check tracer + matrix | `.venv/bin/pytest tests/test1/test_button_classes_checks.py -q` | Yes | Pass |
| KEYS-03 | 02-01-01, 02-01-02 | T-02-02 | Future button-data locations cannot broaden grammar | Unit + import smoke | Quick command above; import command below | Yes | Pass |
| KEYS-04 | 02-01-03 | — | One exact count equals the actual table | Documentation contract | `.venv/bin/pytest tests/test1/test_button_classes.py -q` | Yes | Pass; missing/duplicate/off-by-one mutations rejected |

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

- [x] Finalized tasks each have automated verification
- [x] No three consecutive tasks without automated checks
- [x] All planned test references exist or are created by an earlier task
- [x] No watch-mode flags
- [x] Focused feedback latency under 30 seconds
- [x] nyquist_compliant: true set after validation

**Approval:** Automated task acceptance complete; end-of-phase prose review and the two unclassified probe assumptions remain visible for review.

## Execution Evidence — 2026-10-26

- Tracer RED: one intentional W362 acceptance failure; `02-01-RED-tracer.json` classified `RED_EVIDENCE_OK`.
- Tracer GREEN: 28 checks passed in 0.05s; fresh bare-settings module import passed.
- Matrix: 501 focused checks passed in 0.52s; 26 rendering/crispy/golden/docs regressions passed in 2.99s.
- Boundary sensitivity: exact pre-phase helper loaded only in an isolated interpreter makes the future-location
  test fail (15 warnings versus 8); `02-01-RED-matrix.json` classified `RED_EVIDENCE_OK`. Current implementation
  passed this test in the focused and full runs. No source file was replaced for this probe.
- Count RED: exact integer assertion 64 versus 70 failed; `02-01-RED-count.json` classified `RED_EVIDENCE_OK`.
- Count/docs GREEN: 53 tests passed in 0.10s; missing, duplicate, one-below and one-above claims were each rejected
  by invoking the actual guard with an in-memory document replacement.
- Strict MkDocs build passed in 0.60s.
- Full Python suite: 3360 passed, 1 skipped in 22.17s on Python 3.12.3 / Django 5.2.14. The existing
  `test_django6_builtin_csp_nonce_roundtrip` requires Django 6.0 and remains skipped. Other matrix environments
  were not executed in this plan.
- Vitest: 8 files / 126 tests passed in 4.62s.
- Ruff 0.16.10 lint passed; `ruff format --check src tests` passed (287 files). Repository-wide format check
  reports seven existing planning Markdown files, listed in `deferred-items.md`. This is not a manifest-aligned
  Ruff >=0.17,<0.18 gate; no dependency constraint or package installation changed.
- Preservation: `DEFAULT_BUTTON_CLASSES` and `get_button_class` ASTs are identical to the plan-start revision;
  templates, goldens, crispy adapters, button-data locations and label floors have no diff. Branch is introduce-gsd.
