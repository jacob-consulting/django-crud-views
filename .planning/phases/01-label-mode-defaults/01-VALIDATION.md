---
phase: "01"
slug: "label-mode-defaults"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: true) (#2117)
status: validated
nyquist_compliant: true
wave_0_complete: true
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
| 01-01-01 | 01-01 | 1 | LMOD-01, LMOD-02, LMOD-04, LMOD-05 | T-01-01/02/03 | Safe malformed modes, deduplicated warnings, real leaf rendering | unit + tracer render | `.venv/bin/pytest tests/test1/test_button_leaves.py::test_defaults_setting_reaches_button_leaf tests/test1/test_label_mode.py tests/test1/test_button_data.py -q` | ✅ files; tracer test added by task | ✅ green |
| 01-01-02 | 01-01 | 1 | LMOD-06 | T-01-03 | E108 validates raw settings; new subprocess directly tests the deferred settings import boundary | checks + import | `.venv/bin/pytest tests/test1/test_action_label_mode_config.py tests/test1/test_settings_checks.py tests/test1/test_import_safety.py -q` | ✅ files; subprocess test added by task | ✅ green |
| 01-01-02 / 01-02-02 | 01-01 / 01-02 | 1 / 2 | LMOD-05 | T-01-02 | Shared autouse fixture isolates warnings across randomized worker tests without resetting within tests | unit + isolation | `.venv/bin/pytest tests/test1/test_label_mode.py tests/test1/test_button_data.py tests/test1/test_action_label_mode_config.py -q -n 2 --random-order --random-order-seed=4711` | ✅ files; fixture added by 01-01-02 | ✅ green |
| 01-02-01 | 01-02 | 2 | LMOD-02, LMOD-05, LMOD-06 | T-01-04/05/06 | W292 cannot hide E108; explicit choices preserved | HTTP render + checks | `.venv/bin/pytest tests/test1/test_context_action_label_mode.py tests/test1/test_context_button_label_mode.py -q` | ✅ | ✅ green |
| 01-02-02 | 01-02 | 2 | LMOD-01, LMOD-02, LMOD-04 | T-01-05 | No eager invalid-floor read over explicit mode | unit + HTTP render | `.venv/bin/pytest tests/test1/test_action_label_mode_config.py tests/test1/test_action_label_mode_render.py -q` | ✅ | ✅ green |
| 01-02-02 | 01-02 | 2 | LMOD-02 | T-01-05 | Single accessor replaces obsolete literals | shell | Exact grep wrapper in 01-02-PLAN.md accepts only grep status 1; status 0 or 2 is non-zero at wrapper | ✅ | ✅ green |
| 01-03-01 | 01-03 | 2 | LMOD-02, LMOD-03, LMOD-04, LMOD-05 | T-01-07/08 | Optional attribute resolves safely; accessibility/precedence retained | unit + HTTP render | `.venv/bin/pytest tests/test1/test_card_label_modes.py tests/test1/test_card_label_mode_render.py -q` | ✅ | ✅ green |
| 01-03-02 | 01-03 | 2 | LMOD-03 | T-01-09 | Attribute break disclosed with resolver migration | doc source assertions | Exact pathlib assertion command in 01-03-PLAN.md; non-zero or missing success line rejects | ✅ | ✅ green (superseded) |
| 01-03 final | 01-03 | 2 | LMOD-03 | T-01-09 | Card documentation links existing anchors before wave 3 creates canonical targets | docs build | `.venv/bin/mkdocs build --strict` | ✅ | ✅ green |
| 01-04-01 | 01-04 | 3 | LMOD-01–LMOD-06 | T-01-10/11 | Documentation example parsed as data, rendered through real tag | executable docs + build | `.venv/bin/pytest tests/test1/test_label_mode_docs.py -q`; `.venv/bin/mkdocs build --strict` | New test file created in task | ✅ green |
| 01-04-02 | 01-04 | 3 | LMOD-01–LMOD-06 | T-01-10/12 | Accurate migration, release-name-independent selector and checked changelog anchors | doc contracts + build | `.venv/bin/pytest tests/test1/test_label_mode_docs.py -q`; `.venv/bin/mkdocs build --strict` | Created by 01-04-01 | ✅ green |
| 01-04-02 | 01-04 | 3 | LMOD-03 | T-01-12 | D-23 handoff verified without permanent tests depending on planning state | one-off planning grep | Exact PROJECT.md row-count/outcome grep in 01-04-PLAN.md, with its own fails_when | ✅ | ✅ green |
| 01-04 final | 01-04 | 3 | all | T-01-10 | Protected paths have no new/untracked or modified files | git status | `git status --porcelain -- tests/test1/golden src/crud_views/templates examples` must print nothing, in addition to baseline diff | ✅ | ✅ green |
| 01-05-01 | 01-05 | 4 | LMOD-02, LMOD-03 | T-01-13/14 | Real as_view instance mode reaches the leaf; unchanged no-setting control | tracer render | `.venv/bin/pytest tests/test1/test_card_label_mode_render.py::test_card_initkwargs_label_without_setting -q` | ✅ | ✅ green (1 passed; valid RED captured first) |
| 01-05-02 | 01-05 | 4 | LMOD-02, LMOD-03, LMOD-04 | T-01-13/14/15/16 | Request isolation, strict-floor bypass, own None, subclass hooks and child permissions | unit + HTTP render | `.venv/bin/pytest tests/test1/test_card_label_modes.py tests/test1/test_card_label_mode_render.py -q` | ✅ | ✅ green (45 passed) |
| 01-05-03 | 01-05 | 4 | LMOD-03 | T-01-13 | Class-level resolver distinguished from effective stamped mode in all four docs surfaces | docs contracts + build | `.venv/bin/pytest tests/test1/test_label_mode_docs.py -q`; `.venv/bin/mkdocs build --strict` | ✅ | ✅ green (6 passed; strict build clean) |
| All tasks / final 01-04 | 01-01–04 | 1–3 | all | T-01-06/08 | Existing permission/rendering contracts preserved | golden | `.venv/bin/pytest tests/test1/test_action_menus_golden.py tests/test1/test_card_label_mode_render.py tests/test1/test_card_blocks.py tests/test1/test_card_order.py tests/test1/test_form_frame.py tests/test1/test_heading_level.py -q` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

Task IDs cover the eight tasks in 01-01 through 01-04 and three gap-closure tasks in 01-05. Every PLAN automated command has an adjacent fails_when signal. A non-zero pytest exit or zero passed tests rejects a test gate. Plan 01-05's automated results are recorded; independent phase re-verification remains pending.

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. No infrastructure scaffold is needed. Task 01-04-01 creates the new docs-contract test before invoking it; the existing leaf test file gains the tracer before its targeted command runs.

Review revision c1546c2: 01-01-01 adds a timeout-bounded subprocess regression for simultaneous invalid stamp/floor recovery; a lock held across fallback must fail rather than hang the suite. 01-01-02 adds shared function-scoped isolate_label_mode_warnings and the fresh-process settings-boundary test. 01-04-01 explicitly supplies access and icon context to the docs tracer and selects the card example by dict content; 01-04-02 tests check-reference completeness and both setting-first migration recipes. These are planned tests, not executed feature evidence.

Review revision bbbf16a: child assertLogs makes nested warning counts deterministic; whole-setting/location/stamp cases and 1/2/3 location fanout are distinct. 01-02 adds the invalid-target scalar HTTP regression and a concrete filter selector. 01-03's one-off script now enforces recipe order, None disclosure, Fixed placement and existing-anchor links before wave 3. 01-04 tests canonical links including root CHANGELOG.md, filters relevant Python fences, survives the release heading rename and checks the simple diagram label. D-23 is a one-off planning grep, not a permanent test dependency. No new feature test is claimed to have run during planning.

---

## Execution Evidence (2026-10-26)

All map commands were re-run after execution on `feat/label-mode-defaults`: 213 / 122 / 298 (seeded random order, -n 2) / 97 / 102 / 25 / 6 / 93 passed; literal grep gate exit 1 as required; `mkdocs build --strict` clean; protected paths unchanged; D-23 PROJECT.md grep passes. Full suite: 3056 passed, 1 skipped.

01-03-02's one-off pathlib script was a pre-wave-3 interim contract: its line-20 link assertion (`settings.md#action-menus`, `action_menus.md#label-mode`) now fails by design because 01-04 retargeted the card entry to the canonical `settings.md#label-mode-configuration` and `action_menus.md#card-label-mode-resolution` anchors. Those targets, and every other clause of the 01-03 contract, are pinned permanently by `tests/test1/test_label_mode_docs.py`. Status: superseded, not a gap.

## Gap-Closure Execution Evidence (01-05, 2026-10-26)

The new as_view tracer failed its intended icon-count assertion before the repair, then passed. The expanded
matrix was green on that repair; all 18 new rendered cases failed against the exact recorded pre-fix card.py.
Both persisted JUnit evidence records were accepted as RED_EVIDENCE_OK. The current card suite passes 45 tests.
Final gates: 112 focused rendering/golden tests passed; full suite 3076 passed with one existing Django<6 CSP
skip; Vitest 126 passed across 8 files; docs contracts 6 passed; strict MkDocs build clean; repository ruff check
and the four owned Python-file format checks clean; protected-path diff and status empty. No golden regeneration.
CR-01 is ready for independent re-verification. This does not certify the two carried assumptions/prohibitions,
change nyquist_compliant, or mark Phase 1 complete.

## Manual-Only Verifications

All specified phase behaviors have automated verification. Spec-less probe retains two unclassified edges (LMOD-02 consumer completeness, LMOD-04 lifecycle completeness) as flagged assumptions and two descriptor-less product-intent prohibitions as flagged-unverified. They require explicit review disposition, not a silent green. See 01-SOURCE-AUDIT.md.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 60s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** validated 2026-10-26 (validate-phase audit after execution)

## Validation Audit 2026-10-26

| Metric | Count |
|---|---|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

## Gap-Closure Coverage Audit

All six requirements retain automated behavioral coverage across completed plans 01-01 through 01-05. The new three-task map includes passing rendered, class-API, lifecycle and documentation checks, with RED evidence for the regression. No automated validation gap remains. The separate product-intent prohibitions and unclassified completeness assumptions remain explicitly flagged for phase verification; Nyquist compliance does not certify them.
