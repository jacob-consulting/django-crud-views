---
phase: 06
review: 06-REVIEW.md
titles: json
findings:
  - id: CR-01
    severity: critical
    disposition: fixed
    title: "`_KIND_ICON` sentinel does not survive `copy.deepcopy`, so deep-copied layout buttons lose their kind icon"
  - id: WR-01
    severity: warning
    disposition: fixed
    title: "No test renders a deep-copied adapter in `\"icon\"` or `\"both\"` mode"
  - id: WR-02
    severity: warning
    disposition: fixed
    title: "The form normalizer admits any truthy non-`str` `cv_icon` into the leaf contract"
  - id: IN-01
    severity: info
    disposition: open
    title: "Per-request `deepcopy` of arbitrary user layout objects is a new failure surface that the docs do not state"
  - id: IN-02
    severity: info
    disposition: open
    title: "Extra attributes are emitted in sorted order, not insertion order"
  - id: IN-03
    severity: info
    disposition: open
    title: "Adaptive assertion in `test_form_icon_normalization_keeps_nonblank_strings_exactly` has an unreachable branch"
open: 3
total: 6
recorded: 2026-10-28T10:50:00.000Z
---

# Phase 06: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| CR-01 | critical | fixed | 06-10-SUMMARY.md; fix `f33d396` (omitted icon= recorded as the deep-copy-stable bool `_cv_kind_icon`); RED `ae83e62` then green: `test_copied_filter_layout_keeps_kind_icons` (12), `test_copied_adapter_keeps_icon_contract` (5) |
| WR-01 | warning | fixed | 06-10-SUMMARY.md; regressions `ae83e62` (`tests/test1/test_crispy_buttons.py`: real `{% crispy %}` class-level and assigned copied filter layouts, both/icon x strict/lenient; direct copy/deepcopy of all five kinds; explicit-icon copies), red before and green after `f33d396` |
| WR-02 | warning | fixed | 06-10-SUMMARY.md; fix `61103dd` (non-str or blank `cv_icon` becomes None before availability, diagnostics and the leaf); RED `7f974ad` then green: `test_form_icon_normalization_*` (164) in `tests/test1/test_button_data.py` |
| IN-01 | info | open | - |
| IN-02 | info | open | - |
| IN-03 | info | open | - |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
