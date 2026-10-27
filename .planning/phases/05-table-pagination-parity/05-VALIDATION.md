---
phase: "05"
slug: "table-pagination-parity"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: validated
nyquist_compliant: true
wave_0_complete: true
created: "2026-10-27"
updated: "2026-10-27"
---

# Phase 05 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution. Reconstructed from PLAN and SUMMARY artifacts
> after execution (validate-phase state B).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (pytest-django, pytest-xdist); vitest for JS; mkdocs strict build for docs |
| **Config file** | `pyproject.toml` (`tests/test1/conftest.py` configures Django in-memory) |
| **Quick run command** | `.venv/bin/pytest tests/test1/test_table_template.py tests/test1/test_card_order.py tests/test1/test_button_classes.py tests/test1/test_button_classes_checks.py tests/test1/test_pagination_docs.py -q` |
| **Full suite command** | `.venv/bin/pytest tests -q -n auto` |
| **Estimated runtime** | ~13 seconds quick (465 tests), ~21 seconds full (3583 tests) |

---

## Sampling Rate

- **After every task commit:** Run the task's `<automated>` command (see map below)
- **After every plan wave:** Run `.venv/bin/pytest tests -q -n auto`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 25 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | PAGE-01, PAGE-02, PAGE-03 | T-05-01 / T-05-02 | Prefixed page href via `cv_querystring`; hidden-label class autoescaped | golden + unit | `.venv/bin/pytest tests/test1/test_table_template.py -q` | ✅ | ✅ green |
| 05-01-02 | 01 | 1 | PAGE-03, PAGE-04 | T-05-02 | Card hidden-label class autoescaped; default card bytes frozen | golden + unit | `.venv/bin/pytest tests/test1/test_card_order.py -q` | ✅ | ✅ green |
| 05-01-03 | 01 | 1 | PAGE-03 | — | N/A | unit | `.venv/bin/pytest tests/test1/test_table_template.py tests/test1/test_card_order.py tests/test1/test_button_classes.py tests/test1/test_button_classes_checks.py -q` | ✅ | ✅ green |
| 05-02-01 | 02 | 2 | PAGE-02 | T-05-03 | Direction overrides never call an unavailable page-number method on first/middle/last pages | integration | `.venv/bin/pytest tests/test1/test_table_template.py -q` | ✅ | ✅ green |
| 05-02-02 | 02 | 2 | PAGE-02, PAGE-03, PAGE-04 | T-05-01 / T-05-02 / T-05-04 | Hostile/multivalue query values preserved without injection; scoped page key; hostile class stays one attribute | integration | `.venv/bin/pytest tests/test1/test_table_template.py tests/test1/test_card_order.py -q` | ✅ | ✅ green |
| 05-03-01 | 03 | 3 | PAGE-04 | T-05-05 | Documented override recipe extracted and rendered on pages 1/2/3 with guarded calls | integration + docs | `.venv/bin/pytest tests/test1/test_pagination_docs.py tests/test1/test_table_template.py -q` and `.venv/bin/mkdocs build --strict` | ✅ | ✅ green |
| 05-03-02 | 03 | 3 | PAGE-04 | T-05-06 (accept) | German catalog scoped to core; `.mo` matches fresh `msgfmt` build | unit + build | `.venv/bin/pytest tests/test1/test_table_template.py tests/test1/test_card_order.py -q -k translated` | ✅ | ✅ green |
| 05-03-03 | 03 | 3 | PAGE-01, PAGE-04 | — | N/A | full gates | `.venv/bin/pytest tests -n auto`, `npm --prefix . test`, `.venv/bin/mkdocs build --strict`, `.venv/bin/ruff check` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

Requirement coverage: PAGE-02, PAGE-03 and PAGE-04 are fully COVERED by automated tests. PAGE-01's golden content is
covered by `test_table_pagination_golden`; the commit ordering (golden before markup change) is manual-only, below.

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Table golden baseline committed before the markup change | PAGE-01 | A property of git history, not of the code; a pytest check on commit order would break when the branch is squash-merged | Confirm `git merge-base --is-ancestor be7daa5 0b0f9ba` succeeds, `be7daa5` touches only the capture test and the two goldens, and `0b0f9ba` updates those same goldens. Evidence is recorded in `05-ACCEPTANCE.md` §3. |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 25s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-10-27
