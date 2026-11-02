# Phase 06.4 deferred repair findings

## Independent plan 19 review — 2026-11-01

These are unresolved requirements discovered in the existing successor checker during bounded
independent review. They were not introduced by plan19 documentation, and no repair or risk
acceptance is inferred. G6 and security remain open. See 19-evidence/code-review.md and
19-evidence/security-review.md; WINDOWS entries20/21 keep them visible across phases.

- **WR-03:** 15-evidence/run.py:984–985 accepts absent or success-rewritten
  checker_control_evidence. Enforce exact control inventory/command/rejection outcomes and
  test missing/contradictory records. T22/T28/T33 remain high blockers.
- **WR-04:** 15-evidence/run.py:857,890–924 omits current conditional screenshot
  inventory/hash/observations. Enforce the canonical capture contract and missing/stale-capture
  rejection controls. T22/T33 remain high blockers; T31 remains medium open.

Required follow-up: focused checker repairs, independent code/security re-review, fresh applicable
provenance checks, parent canonical verification and actual H1/H2 outcomes. Source/runtime changes
must invalidate affected evidence; unchanged genuine product runs may be reused only when the
strengthened checker proves their provenance. No broad automatic recapture is prescribed here.
