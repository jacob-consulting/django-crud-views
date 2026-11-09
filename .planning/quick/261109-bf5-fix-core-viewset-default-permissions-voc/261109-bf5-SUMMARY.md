---
phase: quick-261109-bf5
plan: "01"
subsystem: core viewset permissions
status: complete
tags: [performance, permissions, n+1, ancestor-authorization, 06.18]
requires: []
provides:
  - "ViewSet.default_permissions: one ContentType lookup + one Permission query on a cold ViewSet"
  - "regression test pinning the cold query shape and exact mapping"
  - "post-fix and pre-fix 06.18 cost observations under evidence/261109-bf5/"
affects:
  - src/crud_views/lib/viewset/__init__.py (every *PermissionRequired view and ViewSet._ancestor_has_permission consume the mapping)
tech-stack:
  added: []
  patterns: ["mirror GuardianViewSet.default_permissions: read model/app_label from the resolved content_type"]
key-files:
  created:
    - .planning/phases/06.18-ancestor-authorization-for-nested-viewsets/evidence/261109-bf5/cost-observations/*.json (9)
    - .planning/phases/06.18-ancestor-authorization-for-nested-viewsets/evidence/261109-bf5/prefix-c67c841d-cost-observations/*.json (9)
    - .planning/phases/06.18-ancestor-authorization-for-nested-viewsets/evidence/261109-bf5/cost-replay-comparison.txt
  modified:
    - src/crud_views/lib/viewset/__init__.py
    - tests/test1/test_viewset.py
    - .planning/phases/06.18-ancestor-authorization-for-nested-viewsets/deferred-items.md
    - CHANGELOG.md
decisions:
  - "06.18-COSTS.md left unchanged: the re-measurement against 06.18-12 also differs in every Guardian cell (session/user moved from rest to guard), traced to WR-01 76fdc7ff, not this fix; the plan said to stop and report rather than edit COSTS.md around it. Logged as a new open deferred item."
  - "Added a pre-fix measurement at c67c841d (clean detached worktree) so the fix's own effect is isolated: only plain cold django_content_type changes."
metrics:
  duration: "~12 min"
  completed: 2026-11-09
actuals:
  tokens: 51300
  tasks: 3
  commits: 4
plan_head_before: c67c841d093781ae4c2e7090ad3fe9421fe8b62a
plan_head_after: 741830cf9f1b658a9535fced7ee1ad55366f3e92
---

# Quick 261109-bf5: Fix core ViewSet.default_permissions vocabulary N+1 Summary

Cold core `ViewSet.default_permissions` now reads `model`/`app_label` from the already-resolved `ContentType` (as
`GuardianViewSet` does): one `django_content_type` + one `auth_permission` query instead of 1 + N ContentType reads,
with a byte-identical mapping. Re-measured: plain cold ct is 1 per gated ancestor (depth 3 full cascade 15 -> 3).
06.18-COSTS.md was NOT updated (see Deviations).

## Commits

| Task | Commit | Message |
|------|--------|---------|
| 1 RED | 913973a4 | test(quick-261109-bf5): pin one ContentType query for the core default_permissions vocabulary |
| 1 GREEN | 8b11572a | fix(quick-261109-bf5): read the resolved ContentType once in ViewSet.default_permissions |
| 2 | dc97f821 | docs(quick-261109-bf5): re-measure 06.18 costs after the core vocabulary fix and resolve the deferred item |
| 3 | 741830cf | docs(quick-261109-bf5): changelog entry for the core default_permissions vocabulary fix |

## Task 1 (tracer, TDD)

- RED at c67c841d: the two new parametrized cases failed only on the category assertion, `django_content_type` 5
  (Publisher) and 6 (Book + `change_book_status`); the mapping and warm-zero assertions already passed.
- GREEN: two attribute reads changed (`permission.content_type.model` / `.app_label` -> `content_type.model` /
  `.app_label`). Docstring, #33 suffix stripping, #151 `if permissions:` and the Resource `cv_raise` guard untouched.
  Non-comment grep for `permission.content_type` in the module: 0 (was 2).
- test_viewset.py 8 passed; costs + missing-permission + guardian-content-types 133 passed; ruff clean.
- Tracer gate re-run end-to-end: 47 passed, grep 0, ruff check/format clean.

## Task 2 (measurement)

- `CV_ANCESTOR_COSTS_DIR=.../evidence/261109-bf5/cost-observations` on `.nox/tests-3-12-django-5-2`: 9 passed, nine
  JSON files, `meta.source_sha` 8b11572a, `src_dirty` false, Python 3.12.3, Django 5.2.19.
- Comparison `evidence/261109-bf5/cost-replay-comparison.txt`:
  - **A. Fix isolation** vs a pre-fix run at `c67c841d` (clean detached worktree, removed afterwards;
    `evidence/261109-bf5/prefix-c67c841d-cost-observations/`): only plain cold cells differ, only in guard
    `django_content_type`: depth 1 and depth 3 nearest 5 -> 1, depth 3 full 15 -> 3. All warm cells, all Guardian
    cells and top-level are identical. Plain cold totals: cells 1-4 12 -> 8, 5-6 11 -> 7, 13/15 26 -> 14, 17 25 -> 13,
    14/16 14 -> 10, 18 13 -> 9; create-button lists 12 -> 8 (depth 1), 26 -> 14 / 14 -> 10 (depth 3 full/nearest).
  - **B. vs 06.18-12** (5829cae7), as the plan asked: the same plain differences, PLUS every Guardian observation
    (28 cold/warm cells, matrix and create-button) moves session 1 + user 1 from rest to guard (guard +2, rest -2,
    totals and by_table unchanged).
- `deferred-items.md`: core vocabulary item set to `status: resolved` with test `913973a4` and fix `8b11572a`; new open
  item "06.18-COSTS.md no longer matches the current source" with the measured deltas and the refresh recipe.

## Task 3

- CHANGELOG `## Unreleased > ### Fixed` new top bullet (contains "once per `Permission` row"); not Breaking, so
  `docs/migrating-1.0.md` is unchanged (verified `git diff --quiet HEAD`).
- Focused `test_viewset.py` + `test_ancestor_costs.py`: 17 passed on Django 4.2.30 and 17 passed on 6.0.10
  (Python 3.12.3).
- Full suite multicore (`-n auto`) on Django 5.2.19: **12175 passed, 1 skipped** in 213s. More than the plan's
  expected 12165 because the 06.18 code-review commits (76fdc7ff, a17823d9) added tests after plan 12; nothing asserted
  the old cold counts.
- `uv run ruff check` / `ruff format --check` clean on the two touched code files.

## Deviations from Plan

**1. [Plan stop condition] 06.18-COSTS.md not edited (Task 2 step 3 skipped)**
- **Found during:** Task 2 step 2.
- **Issue:** The plan assumed `git diff 5829cae7 <fix> -- src` touches only the two reads. It also contains the
  06.18 code-review fixes 76fdc7ff (WR-01, `crud_views_guardian/lib/mixins.py`) and a17823d9 (WR-02,
  `crud_views/lib/ancestors.py`). WR-01 moved Guardian actor admission into the ancestor guard, so every Guardian
  cell's Guard/Rest split differs from COSTS.md and from 06.18-12. COSTS.md's sentence "Session and user loading
  stays in the rest of the request" is therefore already stale, independent of this fix. The plan said "If anything
  else differs, stop and report it in the SUMMARY instead of editing COSTS.md around it", and step 3i forbids changing
  the Guardian attribution.
- **Action:** Did not edit COSTS.md. Committed the evidence, added the pre-fix c67c841d measurement that isolates
  this fix, resolved the core N+1 deferred item, and logged a new open deferred item plus a WINDOWS.md `deviation`
  entry for the COSTS.md refresh.
- **Consequence:** Task 2's automated verify (COSTS rows == new JSON; Guardian guard == 06.18-12) was not run to
  green and cannot pass until COSTS.md is refreshed, because the Guardian guard values intentionally differ. The
  `deferred-items.md` and `Core vocabulary fix replay` parts of that verify: the deferred check passes; the
  `Core vocabulary fix replay` heading does not exist.
- **Decision needed (user):** refresh 06.18-COSTS.md from `evidence/261109-bf5/cost-observations/` covering both the
  plain cold numbers (this fix) and the Guardian guard/rest re-attribution (WR-01), keeping the 5829cae7 values as
  history. It is a small docs-only follow-up.

**2. [Scope] Extra evidence directory `evidence/261109-bf5/prefix-c67c841d-cost-observations/`**, not in
`files_modified`, added to attribute the differences. Its `meta.crud_views_path` points at the removed scratch worktree.

## Known Stubs

None.

## Threat Flags

None. T-QBF5-01..03 mitigations hold: exact ordered mapping asserted for Publisher and Book + `change_book_status`;
#33 and #151 tests unchanged and green; Resource guard untouched (full suite green).

## Self-Check: PASSED

- FOUND: src/crud_views/lib/viewset/__init__.py, tests/test1/test_viewset.py, CHANGELOG.md, deferred-items.md,
  evidence/261109-bf5/cost-observations (9 files), evidence/261109-bf5/cost-replay-comparison.txt
- FOUND commits: 913973a4, 8b11572a, dc97f821, 741830cf (ancestors of HEAD)
