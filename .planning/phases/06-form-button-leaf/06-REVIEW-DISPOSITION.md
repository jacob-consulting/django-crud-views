---
phase: 06
review: 06-REVIEW.md
titles: json
findings:
  - id: CR-01
    severity: critical
    disposition: open
    title: "`_KIND_ICON` sentinel does not survive `copy.deepcopy`, so deep-copied layout buttons lose their kind icon"
  - id: WR-01
    severity: warning
    disposition: open
    title: "No test renders a deep-copied adapter in `\"icon\"` or `\"both\"` mode"
  - id: WR-02
    severity: warning
    disposition: open
    title: "The form normalizer admits any truthy non-`str` `cv_icon` into the leaf contract"
  - id: IN-01
    severity: info
    disposition: open
    title: "Per-request `deepcopy` of arbitrary user layout objects is a new failure surface that the docs do not state"
  - id: IN-02
    severity: info
    disposition: open
    title: "Extra attributes are emitted in sorted order, not insertion order"
open: 5
total: 5
recorded: 2026-10-28T09:53:59.225Z
---

# Phase 06: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| CR-01 | critical | open | - |
| WR-01 | warning | open | - |
| WR-02 | warning | open | - |
| IN-01 | info | open | - |
| IN-02 | info | open | - |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
