---
phase: quick-261109-bvq
plan: "01"
subsystem: planning-evidence
status: complete
tags: [06.18, ANCE-08, costs, evidence, docs]
requires:
  - evidence/261109-bf5/cost-observations (source 8b11572a)
  - evidence/06.18-12/cost-observations (plan 12 record, 5829cae7)
  - evidence/06.18-01/baseline-observations
provides:
  - 06.18-COSTS.md standing for source 8b11572a (HEAD src) with separate WR-01 / bf5 attribution
  - evidence/261109-bvq/check_costs_md.py (stdlib checker, --facts, --emit)
affects:
  - .planning/phases/06.18-ancestor-authorization-for-nested-viewsets/06.18-COSTS.md
  - .planning/phases/06.18-ancestor-authorization-for-nested-viewsets/deferred-items.md
  - .planning/WINDOWS.md
tech-stack:
  added: []
  patterns: ["doc tables bound to JSON evidence by a committed stdlib checker (RED before / GREEN after)"]
key-files:
  created:
    - .planning/phases/06.18-ancestor-authorization-for-nested-viewsets/evidence/261109-bvq/check_costs_md.py
    - .planning/phases/06.18-ancestor-authorization-for-nested-viewsets/evidence/261109-bvq/check-costs-md-before.txt
    - .planning/phases/06.18-ancestor-authorization-for-nested-viewsets/evidence/261109-bvq/check-costs-md.txt
  modified:
    - .planning/phases/06.18-ancestor-authorization-for-nested-viewsets/06.18-COSTS.md
    - .planning/phases/06.18-ancestor-authorization-for-nested-viewsets/deferred-items.md
    - .planning/WINDOWS.md
decisions:
  - "COSTS.md tables are generated from and checked against the JSON evidence; the categories table uses a machine-checkable Cells | Temperature | Guard | Rest layout (23 rows covering all 48 observations)"
  - "The WR-01 guard/rest shift covers 32 Guardian observations (12 matrix cells x cold/warm + 4 create-button requests x cold/warm), not 28 as the plan and the bf5 SUMMARY stated"
metrics:
  duration: "~4 min (from plan-start record; reading before that not counted)"
  completed: 2026-11-09
requirements: [ANCE-08]
actuals:
  tokens: 17500
  tasks: 2
  commits: 2
plan_head_before: ec08d6c21b7fe8656cf9a857a5a926c480f7b82b
plan_head_after: a39efcc7d4c352f6d557852ed75970eb559c33aa
---

# Quick 261109-bvq Plan 01: Refresh 06.18-COSTS.md from post-fix evidence Summary

06.18-COSTS.md now stands for source `8b11572a` (HEAD's `src/`), with WR-01 (`76fdc7ff`, Guardian session+user
counted as guard) and quick task 261109-bf5 (`8b11572a`, plain cold ct 1 per gated ancestor) attributed separately,
Depth defined, the plan 12 record kept as History, and every table number bound to JSON by a committed checker
(820 checks, exit 0; 65 mismatches against the pre-refresh file).

## Commits

| Task | Commit | Message |
|------|--------|---------|
| 1 | `bc5ad6dd` | docs(quick-261109-bvq): refresh 06.18-COSTS.md from the post-fix evidence (WR-01 guard/rest, bf5 plain cold ct) |
| 2 | `a39efcc7` | docs(quick-261109-bvq): resolve the COSTS.md deferred item and fix WINDOWS 43 |

## Task 1

- Step 0: `git diff --quiet 8b11572a HEAD -- src` and `git status --porcelain -- src` both empty, so
  `evidence/261109-bf5/cost-observations/` was used without a re-run.
- `evidence/261109-bvq/check_costs_md.py` (json/re/sys/pathlib only): checks the current 24-cell table (Now, Baseline,
  Delta, Guard, Rest, status, Gates), the History 24-cell table against `evidence/06.18-12`, the 48 category
  observations, the four top-level rows, both render-helper fixed-form sentences (plus the plain = matrix cells 1, 2,
  13, 14 claim and the Guardian "depth 1 warm total is 6" statement) and the Sources SHA/runtime against all nine
  `meta` blocks. `--facts` prints the prose numerals; `--emit` prints the 24 rows and the grouped categories rows.
- RED: `check-costs-md-before.txt` — FAIL, 65 mismatches (Sources column name, plain cold Now/Delta/Guard, Guardian
  Guard/Rest, categories header, render-helper sentences, missing History heading).
- GREEN: `check-costs-md.txt` — `PASS: checks=820 mismatches=0 (current cells 24, history cells 24, category
  observations 48, top-level rows 4, render-helper sentences 2, sources files 9)`.
- Additionally mutation-tested the checker on scratch copies: a single changed number in the current table, the
  categories table, the Guardian render-helper sentence and the History table each produced exactly one MISMATCH.
- COSTS.md edits (a-l of the plan): intro, Sources ("Current measurement", full SHA, HEAD `ec08d6c2`), new
  "Source changes since the plan 12 record", Depth definition with top-level link, 24 rows from `--emit`, new
  categories layout, plain cold-vocabulary bullet, Guardian depth-1 actor sentence and order-effect values (rest 4 vs
  3), repeated-work row, nearest control "(ct 1 instead of 3)", render-helper sentences, mutation note, History
  section (old replay paragraph, old 24-cell table and old categories table verbatim, old create-button totals line).
- Task 1 verify command: passed.

## Task 2

- deferred-items.md item set to `status: resolved` with a "Resolved in quick task 261109-bvq (`bc5ad6dd`)" paragraph;
  What/Scope text unchanged.
- `node ~/.claude/gsd-core/bin/gsd-tools.cjs windows fixed 43` → row 43 `fixed`, resolved_at
  2026-11-09T08:48:22.336Z; `windows status --pick ledger.open_count` → 0. No hand edit of WINDOWS.md.
- `git status --porcelain -- src tests docs` empty; Task 2 verify command passed.

## Deviations from Plan

1. **[Rule 1 - Bug] Guardian observation count 32, not 28.** The plan (and the bf5 SUMMARY) said the WR-01 shift
   affects "all 28 Guardian observations". The `--facts` output compares 32: 12 Guardian matrix cells x cold/warm (24)
   plus the 4 Guardian create-button requests x cold/warm (8). Per the plan's rule that prose numerals come from the
   facts output, COSTS.md says 32. Commit `bc5ad6dd`.
2. **Emit helper kept.** The plan allowed a temporary emit helper; it is kept as `--emit` so the table rows can be
   regenerated from JSON in future refreshes. The check path does not depend on it.

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: evidence/261109-bvq/check_costs_md.py, check-costs-md-before.txt, check-costs-md.txt; 06.18-COSTS.md
- FOUND: bc5ad6dd, a39efcc7 (ancestors of HEAD)
