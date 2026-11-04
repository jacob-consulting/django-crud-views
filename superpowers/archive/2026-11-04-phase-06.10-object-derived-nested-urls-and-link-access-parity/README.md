# Retired phase 06.10 — historical planning evidence

**Cancelled before implementation on 2026-11-04. Do not execute these plans.**

The [maintainer decision](../../notes/2026-11-04-opt-in-url-helper-decision.md) replaces the integrated phase with the unscheduled opt-in helper in [#314](https://github.com/jacob-consulting/django-crud-views/issues/314). Permission/visibility bugs remain separately tracked in #312. This archive is outside `.planning/phases` so planning tools cannot select it for execution.

## Contents

- [Discussion log](phase/06.10-DISCUSSION-LOG.md) and [context/decisions](phase/06.10-CONTEXT.md).
- [Research](phase/06.10-RESEARCH.md) and [existing patterns](phase/06.10-PATTERNS.md).
- Plans [01](phase/06.10-01-PLAN.md), [02](phase/06.10-02-PLAN.md), [03](phase/06.10-03-PLAN.md), [04](phase/06.10-04-PLAN.md), [05](phase/06.10-05-PLAN.md), and [06](phase/06.10-06-PLAN.md).
- [Review cycles](phase/06.10-REVIEWS.md), [validation strategy](phase/06.10-VALIDATION.md), and the complete `.review-diagnostics/` directory beneath `phase/`.
- [Roadmap](planning-before-retirement/ROADMAP.md), [requirements](planning-before-retirement/REQUIREMENTS.md), [state](planning-before-retirement/STATE.md), and [machine-readable state](planning-before-retirement/state.json) as they stood before retirement.
- [Provenance manifest](provenance.json), recording every archived phase file's SHA-256 and the imported discussion/design documents' source commit and hashes.

All 114 phase files were copied byte for byte, including the local first-review diagnostics that had not yet been committed. The original tracked phase snapshot was `f2c271a5087eaea370c10bb4da305ae22f06c9e6`. Original internal paths and status statements are retained as historical text; paths beginning `.planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/` now resolve within this archive's `phase/` directory.

No product code was implemented by the retired phase. Its successful plan reviews do not establish implementation, query-count, browser, or regression-test results. See the [critical review](../../notes/2026-11-04-datapanel-and-prerequisites-review.md) for the baseline tests actually run.
