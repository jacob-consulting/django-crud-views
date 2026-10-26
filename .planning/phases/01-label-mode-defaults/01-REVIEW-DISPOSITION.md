---
phase: 01
review: 01-REVIEW.md
titles: json
findings:
  - id: CR-01
    severity: critical
    disposition: open
    title: "Card label mode set on the view instance is now ignored"
  - id: WR-01
    severity: warning
    disposition: open
    title: "Strict-mode \"icon-only without icon\" error points at the wrong fix for floor-driven buttons"
  - id: WR-02
    severity: warning
    disposition: open
    title: "No system check for icon-only buttons created by the card or list floor"
  - id: WR-03
    severity: warning
    disposition: open
    title: "10-second subprocess timeouts are likely to flake under xdist or Windows CI"
  - id: IN-01
    severity: info
    disposition: open
    title: "Warn-once register drops the stamp diagnostic when stamp and floor share a bad value"
  - id: IN-02
    severity: info
    disposition: open
    title: "E108 unknown-key message reports the value as what was \"got\""
  - id: IN-03
    severity: info
    disposition: open
    title: "Mapping types other than dict are rejected, including MappingProxyType"
  - id: IN-04
    severity: info
    disposition: open
    title: "W292 guard catches every ValueError, not just the floor's"
  - id: IN-05
    severity: info
    disposition: open
    title: "LOCATIONS and LABEL_MODE_DEFAULTS are two sources of truth"
  - id: IN-06
    severity: info
    disposition: open
    title: "Floor is read live but the label-mode maps are frozen at import"
  - id: IN-07
    severity: info
    disposition: open
    title: "Some floor tests depend on the test app's default maps instead of clearing them"
open: 11
total: 11
recorded: 2026-10-26T08:59:26.046Z
---

# Phase 01: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| CR-01 | critical | open | - |
| WR-01 | warning | open | - |
| WR-02 | warning | open | - |
| WR-03 | warning | open | - |
| IN-01 | info | open | - |
| IN-02 | info | open | - |
| IN-03 | info | open | - |
| IN-04 | info | open | - |
| IN-05 | info | open | - |
| IN-06 | info | open | - |
| IN-07 | info | open | - |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
