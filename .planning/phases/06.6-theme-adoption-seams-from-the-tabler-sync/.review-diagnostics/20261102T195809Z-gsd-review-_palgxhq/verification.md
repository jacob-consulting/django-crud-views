## Verification coverage

`plan_review.source_grounding=true`. `drift-guard authority --raw` returned **intel** despite the configured grep string. `.planning/intel/API-SURFACE.md:5–6` explicitly says the index is empty; api-map.json is absent. Python/template/framework/CLI semantics and every signature remain **UNCHECKABLE** under that authority. Supplementary physical-path checks and actual source reads support findings without pretending the empty adapter verifies signatures. New phase artifacts are excluded from missing-symbol assertions.

Severity seam results: VERIFIED → none/false; MISSING → needs-acknowledgement/false; AMBIGUOUS → MEDIUM/false; UNCHECKABLE → INFO/false (severity/hardBlock). No hard block or missing-symbol acknowledgment is fabricated from empty intel. `git diff 1c21a3a -- src tests docs examples noxfile.py` is empty; unchanged source evidence is reused with refreshed plan citations. The inventory below has 391 coalesced references, quotes current plan lines and adds revised identifiers/paths. No implementation tests were claimed to have run during this plan review.

Refreshed `/tmp/phase066-paths.json` and `/tmp/phase066-directions.json` each cover 33 task commands: paths are `not_applicable` (not proof of path/command resolution), failure directions `ok`. Future test files/utilities remain phase outputs; runtime availability is not a passing test result.

### Cross-artifact fact drift

| Axis | Compared evidence/result | Authority |
|---|---|---|
| Phase status | `drift-guard phase-status --phase 06.6`: **lag**, STATE Ready to plan / ROADMAP Planned, nonterminal ranks 0/1. Not a finding. | STATE.md |
| Success criteria / truths | ROADMAP.md:731–746 versus all ten must-have truths: ownership, layered modes, four keys, default preservation, companion verification/delivery and migration agree. | ROADMAP.md |
| Requirement IDs | ROADMAP.md:728 and REQUIREMENTS.md:160–165 versus all ten plan scopes preserve THEME-01–06 meanings. | ROADMAP.md |
| Defined decisions | CONTEXT.md D-01–D-19 and its explicit 2026-11-02 amendment versus current tasks retain immediate helper errors, no wrapper transfer, atomic registration, native pack behavior and actual scoped companion delivery after isolated replay. | CONTEXT.md |

No contradictory authoritative fact pair found. Historical temporary-only D-11/D-14 language is explicitly superseded by the user's current amendment. Historical missing runtime statements are superseded by recorded availability, without implying passing suites. STATE and CONTEXT are present. Fact-drift findings are advisory and contribute to neither convergence count.

### External reviewer plan coverage

Final coverage is checked against all ten manifest IDs for every lane. Core source is available to reviewers; companion source is supplied as numbered excerpts in the common prompt. No fresh implementation, browser, baseline or replay pass is claimed.


