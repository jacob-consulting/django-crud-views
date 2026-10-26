---
phase: 03
review: 03-REVIEW.md
titles: json
findings:
  - id: WR-01
    severity: warning
    disposition: fixed
    title: "`cv_label_mode` is resolved and stamped twice on every filter render, by two call sites that only coincidentally agree"
  - id: WR-02
    severity: warning
    disposition: fixed
    title: "A malformed stamped `cv_label_mode` is silently rendered as the icon form, in strict mode too, contradicting the documented strict-mode policy"
  - id: IN-01
    severity: info
    disposition: open
    title: "The leaf spells the same three-way mode decision five different ways"
  - id: IN-02
    severity: info
    disposition: open
    title: "CHANGELOG sentence reads as if `FilterContextButton(label_mode=\"label\")` selects `\"icon\"`"
  - id: IN-03
    severity: info
    disposition: open
    title: "Catalog test reaches into `GNUTranslations._catalog`"
  - id: IN-04
    severity: info
    disposition: open
    title: "`FilterContextButton` is now a documented configuration surface but is not re-exported with its siblings"
open: 4
total: 6
recorded: 2026-10-26T16:34:04.598Z
---

# Phase 03: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| WR-01 | warning | fixed | 03-REVIEW-FIX.md |
| WR-02 | warning | fixed | 03-REVIEW-FIX.md |
| IN-01 | info | open | - |
| IN-02 | info | open | - |
| IN-03 | info | open | - |
| IN-04 | info | open | - |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
