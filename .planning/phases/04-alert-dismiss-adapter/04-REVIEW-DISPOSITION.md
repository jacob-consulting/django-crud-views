---
phase: 04
review: 04-REVIEW.md
titles: json
findings:
  - id: IN-01
    severity: info
    disposition: open
    title: "`[role=\"alert\"]` matches only a single-token role attribute"
  - id: IN-02
    severity: info
    disposition: open
    title: "The `BOOTSTRAP_DATA_ALLOWED` allowlist is hand-copied from `theme.md` rather than derived from it"
  - id: IN-04
    severity: info
    disposition: open
    title: "The new `theme.md` sentence about non-core `data-bs-*` templates has no guard"
  - id: IN-05
    severity: info
    disposition: open
    title: "`messages.md` enumerates two of the three missing-script combinations"
  - id: WR-01
    severity: warning
    disposition: fixed
    title: "`theme.md` claims the dropdown templates are the only stock templates with `data-bs-*`, but the object-detail layouts also carry them"
  - id: IN-03
    severity: info
    disposition: fixed
    title: "`messages.md` understates the `viewset.js`-without-`adapters.js` case"
open: 4
total: 6
recorded: 2026-10-26T21:05:36.956Z
---

# Phase 04: Code Review Disposition

| Finding | Severity | Disposition | Source |
|---------|----------|-------------|--------|
| IN-01 | info | open | - |
| IN-02 | info | open | - |
| IN-04 | info | open | - |
| IN-05 | info | open | - |
| WR-01 | warning | fixed | b7b49ae (user decision in UAT) (not in the current review) |
| IN-03 | info | fixed | b7b49ae (user decision in UAT) (not in the current review) |

Dispositions: `open` (recorded, not yet triaged), `fixed`, `skipped`, `deferred`.
Set `deferred` by hand and put the reason in the Source cell; both are preserved. A `|` in the reason is kept as prose and escaped on the next run.
Re-running the gate keeps every row it can. A row the current review no longer reports is kept and its Source cell flagged, so a finding does not leave this record silently. ONE exception: when a finding id is REUSED by a different finding, the earlier decision cannot keep a row — the id is taken — and it is dropped. A RECORDED decision (anything but `open`) is named on the console when that happens; a row still at `open` is replaced silently, because `open` records no decision to lose.
