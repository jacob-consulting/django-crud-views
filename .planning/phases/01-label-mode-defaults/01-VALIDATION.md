---
phase: "01"
slug: "label-mode-defaults"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-25"
---

# Phase 01 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + pytest-django (configured in `tests/test1/conftest.py` `pytest_configure`, strict mode on) |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command** | `.venv/bin/pytest tests/test1/test_label_mode.py tests/test1/test_button_data.py tests/test1/test_card_label_modes.py tests/test1/test_context_action_label_mode.py tests/test1/test_action_label_mode_config.py -q` |
| **Full suite command** | `.venv/bin/pytest tests -n auto` |
| **Estimated runtime** | ~60 seconds |

---

## Sampling Rate

- **After every task commit:** Run the quick run command plus the golden tests
- **After every plan wave:** Run `.venv/bin/pytest tests -n auto`, `ruff check`, `ruff format --check`
- **Before `/gsd-verify-work`:** Full suite, `mkdocs build --strict` and vitest must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01-01 | 1 | LMOD-01, LMOD-02, LMOD-04, LMOD-05 | T-01-01/02/03 | Safe malformed modes, deduplicated warnings, real leaf rendering | unit + tracer render | `.venv/bin/pytest tests/test1/test_button_leaves.py::test_defaults_setting_reaches_button_leaf tests/test1/test_label_mode.py tests/test1/test_button_data.py -q` | ✅ files; tracer test added by task | ⬜ pending |
| 01-01-02 | 01-01 | 1 | LMOD-06 | T-01-03 | E108 validates raw settings without import-time crash | checks + import | `.venv/bin/pytest tests/test1/test_action_label_mode_config.py tests/test1/test_settings_checks.py tests/test1/test_import_safety.py -q` | ✅ | ⬜ pending |
| 01-02-01 | 01-02 | 2 | LMOD-02, LMOD-05, LMOD-06 | T-01-04/05/06 | W292 cannot hide E108; explicit choices preserved | HTTP render + checks | `.venv/bin/pytest tests/test1/test_context_action_label_mode.py tests/test1/test_context_button_label_mode.py -q` | ✅ | ⬜ pending |
| 01-02-02 | 01-02 | 2 | LMOD-01, LMOD-02, LMOD-04 | T-01-05 | No eager invalid-floor read over explicit mode | unit + HTTP render | `.venv/bin/pytest tests/test1/test_action_label_mode_config.py tests/test1/test_action_label_mode_render.py -q` | ✅ | ⬜ pending |
| 01-02-02 | 01-02 | 2 | LMOD-02 | T-01-05 | Single accessor replaces obsolete literals | shell | Exact grep wrapper in 01-02-PLAN.md accepts only grep status 1; status 0 or 2 is non-zero at wrapper | ✅ | ⬜ pending |
| 01-03-01 | 01-03 | 2 | LMOD-02, LMOD-03, LMOD-04, LMOD-05 | T-01-07/08 | Optional attribute resolves safely; accessibility/precedence retained | unit + HTTP render | `.venv/bin/pytest tests/test1/test_card_label_modes.py tests/test1/test_card_label_mode_render.py -q` | ✅ | ⬜ pending |
| 01-03-02 | 01-03 | 2 | LMOD-03 | T-01-09 | Attribute break disclosed with resolver migration | doc source assertions | Exact pathlib assertion command in 01-03-PLAN.md; non-zero or missing success line rejects | ✅ | ⬜ pending |
| 01-04-01 | 01-04 | 3 | LMOD-01–LMOD-06 | T-01-10/11 | Documentation example parsed as data, rendered through real tag | executable docs + build | `.venv/bin/pytest tests/test1/test_label_mode_docs.py -q`; `.venv/bin/mkdocs build --strict` | New test file created in task | ⬜ pending |
| 01-04-02 | 01-04 | 3 | LMOD-01–LMOD-06 | T-01-10/12 | Accurate migration/decision handoff, no project data | doc contracts + build | `.venv/bin/pytest tests/test1/test_label_mode_docs.py -q`; `.venv/bin/mkdocs build --strict` | Created by 01-04-01 | ⬜ pending |
| All tasks / final 01-04 | 01-01–04 | 1–3 | all | T-01-06/08 | Existing permission/rendering contracts preserved | golden | `.venv/bin/pytest tests/test1/test_action_menus_golden.py tests/test1/test_card_label_mode_render.py tests/test1/test_card_blocks.py tests/test1/test_card_order.py tests/test1/test_form_frame.py tests/test1/test_heading_level.py -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

Task IDs match the eight tasks in 01-01 through 01-04. Every PLAN automated command has an adjacent fails_when signal. A non-zero pytest exit or zero passed tests rejects a test gate. Status remains draft until execution/validation; planning is not evidence that the new tests pass.

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. No infrastructure scaffold is needed. Task 01-04-01 creates the new docs-contract test before invoking it; the existing leaf test file gains the tracer before its targeted command runs.

---

## Manual-Only Verifications

All specified phase behaviors have automated verification. Spec-less probe retains two unclassified edges (LMOD-02 consumer completeness, LMOD-04 lifecycle completeness) as flagged assumptions and two descriptor-less product-intent prohibitions as flagged-unverified. They require explicit review disposition, not a silent green. See 01-SOURCE-AUDIT.md.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
