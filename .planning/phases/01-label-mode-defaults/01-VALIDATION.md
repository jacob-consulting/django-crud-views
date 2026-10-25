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
| 01-xx | TBD | TBD | LMOD-01 | — | N/A | unit | `.venv/bin/pytest tests/test1/test_label_mode.py -q` | ✅ | ⬜ pending |
| 01-xx | TBD | TBD | LMOD-02 | — | N/A | unit + render | `.venv/bin/pytest tests/test1/test_context_action_label_mode.py tests/test1/test_action_label_mode_config.py -q` | ✅ | ⬜ pending |
| 01-xx | TBD | TBD | LMOD-02 | — | N/A | shell | `! grep -n '"both" if card\|or "icon"\|get(key, "icon")' src/crud_views/lib/view/*.py` | n/a | ⬜ pending |
| 01-xx | TBD | TBD | LMOD-03 | — | N/A | unit + render | `.venv/bin/pytest tests/test1/test_card_label_modes.py tests/test1/test_card_label_mode_render.py -q` | ✅ | ⬜ pending |
| 01-xx | TBD | TBD | LMOD-04 | — | N/A | unit | `.venv/bin/pytest tests/test1/test_button_data.py -q` | ✅ | ⬜ pending |
| 01-xx | TBD | TBD | LMOD-05 | — | invalid config falls back, no crash in production | unit | `.venv/bin/pytest tests/test1/test_button_data.py tests/test1/test_label_mode.py -q` | ✅ | ⬜ pending |
| 01-xx | TBD | TBD | LMOD-06 | — | invalid config reported at startup | unit | `.venv/bin/pytest tests/test1/test_action_label_mode_config.py tests/test1/test_settings_checks.py -q` | ✅ | ⬜ pending |
| 01-xx | TBD | TBD | all | — | N/A | golden | `.venv/bin/pytest tests/test1/test_action_menus_golden.py tests/test1/test_card_label_mode_render.py tests/test1/test_card_blocks.py tests/test1/test_card_order.py tests/test1/test_form_frame.py tests/test1/test_heading_level.py -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

Task IDs are filled in once plans exist.

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements.

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
