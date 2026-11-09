---
phase: quick-261109-bvq
plan: "01"
type: execute
wave: 1
depends_on: []
files_modified:
  - .planning/phases/06.18-ancestor-authorization-for-nested-viewsets/06.18-COSTS.md
  - .planning/phases/06.18-ancestor-authorization-for-nested-viewsets/deferred-items.md
  - .planning/phases/06.18-ancestor-authorization-for-nested-viewsets/evidence/261109-bvq/check_costs_md.py
  - .planning/phases/06.18-ancestor-authorization-for-nested-viewsets/evidence/261109-bvq/check-costs-md-before.txt
  - .planning/phases/06.18-ancestor-authorization-for-nested-viewsets/evidence/261109-bvq/check-costs-md.txt
  - .planning/WINDOWS.md
autonomous: true
requirements: [ANCE-08]
estimate:
  tokens: 55000
  raw_tokens: 55000
  tasks: 2
  confidence: low
must_haves:
  truths:
    - "Every number in the 24-cell table, the categories table, the top-level control table and the render-helper totals of 06.18-COSTS.md equals the value in evidence/261109-bf5/cost-observations/*.json (and the Baseline column equals evidence/06.18-01/baseline-observations/*.json); a committed stdlib-only script proves this with exit 0, and the same script fails (exit 1) against the pre-refresh file."
    - "The two causes that moved the numbers since the plan 12 record (5829cae7) are attributed separately in the doc: WR-01 76fdc7ff moved Guardian actor admission into the ancestor guard (session 1 + user 1 count as guard in all 28 Guardian observations; totals unchanged), and quick task 261109-bf5 8b11572a removed the core vocabulary N+1 (plain cold django_content_type 1 per gated ancestor; depth 3 full cascade 3 instead of 15). WR-02 a17823d9 is named as the third commit in the src diff range and as changing no count."
    - "The doc states that Depth is the number of ancestors above the leaf (depth 1 = one nested level, Publisher -> Book) and that every table row is a nested request while top-level requests do zero ancestor work, linking the top-level control."
    - "The 5829cae7 record (its 24-cell table, categories table and render-helper totals) is kept verbatim under a History heading, and the history 24-cell table is script-checked against evidence/06.18-12/cost-observations/*.json."
    - "The deferred item '06.18-COSTS.md no longer matches the current source' is status: resolved with the refresh commit SHA, and WINDOWS.md row 43 is fixed through the gsd-tools windows ledger command (open_count 0), with no hand-edited counts."
  artifacts:
    - path: .planning/phases/06.18-ancestor-authorization-for-nested-viewsets/06.18-COSTS.md
      provides: "post-fix numbers for the current source 8b11572a (src identical to HEAD), separate WR-01 and bf5 attribution, Depth definition, History section with the 5829cae7 record"
    - path: .planning/phases/06.18-ancestor-authorization-for-nested-viewsets/evidence/261109-bvq/check_costs_md.py
      provides: "stdlib-only checker binding every table number of COSTS.md to the JSON evidence; exit 0 on match, exit 1 with a mismatch list otherwise"
    - path: .planning/phases/06.18-ancestor-authorization-for-nested-viewsets/evidence/261109-bvq/check-costs-md-before.txt
      provides: "the checker's failing output against the pre-refresh COSTS.md (RED record)"
    - path: .planning/phases/06.18-ancestor-authorization-for-nested-viewsets/evidence/261109-bvq/check-costs-md.txt
      provides: "the checker's passing output against the refreshed COSTS.md (GREEN record)"
    - path: .planning/phases/06.18-ancestor-authorization-for-nested-viewsets/deferred-items.md
      provides: "the COSTS.md item marked resolved with the refresh commit SHA and the WINDOWS 43 closure"
    - path: .planning/WINDOWS.md
      provides: "row 43 status fixed, open_count 0, written by gsd-tools windows fixed 43"
  key_links:
    - from: evidence/261109-bf5/cost-observations/depth{1,3}-{plain,guardian}.json observations[mode/op][cold|warm]
      to: 06.18-COSTS.md 24-cell table (Now, Guard, Rest, Delta, Gates columns)
      via: "check_costs_md.py maps row (Depth, Provider, Operation, Mode) to file depth{D}-{provider}.json key {mode}/{op}; Delta = total - baseline total from evidence/06.18-01/baseline-observations key legacy-no-mode/{op}; Gates = model suffix of each gate tuple's permission codename"
    - from: evidence/261109-bf5/cost-replay-comparison.txt section A (fix vs c67c841d) and section B (fix vs 5829cae7)
      to: 06.18-COSTS.md source-changes section
      via: "A shows only plain cold ct differs across the bf5 fix; B shows the additional Guardian guard/rest shift, therefore present before bf5, attributed to 76fdc7ff"
    - from: gsd-tools windows fixed 43
      to: .planning/WINDOWS.md row 43 and front-matter counts and trailing JSON ledger
      via: "the ledger CLI rewrites both the Markdown row and the JSON block; no manual edit"
---

<objective>
Refresh `06.18-COSTS.md` so it stands for the current source instead of the plan 12 record `5829cae7`. Two source
changes since then moved its numbers and are attributed separately: (a) the 06.18 code-review fix WR-01 `76fdc7ff`
moved Guardian actor admission into the ancestor guard, so `django_session` 1 and `auth_user` 1 count as guard instead
of rest in every Guardian cell (guard +2, rest -2, totals and by_table unchanged); (b) quick task 261109-bf5
`8b11572a` removed the core `ViewSet.default_permissions` vocabulary N+1, so plain cold `django_content_type` is 1 per
gated ancestor (depth 3 full cascade 3 instead of 15) and plain cold totals drop by 4 per gated ancestor. The 5829cae7
values stay in the file as history. Every table number is bound to the JSON evidence by a committed checker script,
so nothing is hand-typed. The deferred item and WINDOWS.md row 43 are closed.

Purpose: 06.18-COSTS.md is the ANCE-08 / acceptance row A25 cost record (decisions D-02, D-20, D-22, D-25). After
quick task 261109-bf5 it contradicted the source in 20 of 24 cells (its plan stopped rather than edit around the
unexpected Guardian shift). The user also misread the depth-1 rows as non-nested requests, so the table intro must
define Depth explicitly and point at the top-level control.

Output: refreshed `06.18-COSTS.md`; `evidence/261109-bvq/check_costs_md.py` with its RED (before) and GREEN (after)
outputs; `deferred-items.md` item resolved; WINDOWS.md row 43 fixed via the ledger CLI. Docs and evidence only: no
`src/`, `tests/` or `docs/` change.
</objective>

<execution_context>
@~/.claude/gsd-core/workflows/execute-plan.md
@~/.claude/gsd-core/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@CLAUDE.md
@.planning/phases/06.18-ancestor-authorization-for-nested-viewsets/06.18-COSTS.md
@.planning/phases/06.18-ancestor-authorization-for-nested-viewsets/deferred-items.md
@.planning/phases/06.18-ancestor-authorization-for-nested-viewsets/evidence/261109-bf5/cost-replay-comparison.txt
@.planning/quick/261109-bf5-fix-core-viewset-default-permissions-voc/261109-bf5-SUMMARY.md
@.planning/WINDOWS.md
@~/.claude/gsd-core/references/gsd-run-resolver.md

Grounding facts verified while planning (HEAD ba7f79ee):
- `git diff 8b11572a HEAD -- src` is empty and `git status --porcelain -- src tests` is empty: HEAD's `src/` is the
  source the 261109-bf5 evidence measured, so `evidence/261109-bf5/cost-observations/` (nine files, `meta.source_sha`
  `8b11572a3767e3942830c9d588d715975d0a3b96`, `src_dirty` false, Python 3.12.3, Django 5.2.19) is usable without a
  re-run. `git log --oneline 5829cae7..HEAD -- src` lists exactly three commits: `8b11572a` (bf5 fix,
  `src/crud_views/lib/viewset/__init__.py`), `a17823d9` (WR-02, `src/crud_views/lib/ancestors.py`), `76fdc7ff`
  (WR-01, `src/crud_views_guardian/lib/mixins.py`). WR-01's diff moves the anonymous/inactive actor checks out of
  `GuardianParentPermissionMixin.dispatch` for nested views; the guard now calls `_cv_ancestor_actor_response` after
  static validation, which is where `request.user` is first loaded (hence session + user inside the guard).
- Observation JSON layout: `observations["{mode}/{op}"]["cold"|"warm"]` with keys `total`, `guard`, `rest`,
  `by_table`, `guard_by_table`, `rest_by_table`, `gates` (list of `[phase, viewset_name, "app.view_<model>", pk]`),
  `querysets`, `guard_calls`, `status`. Modes `full`/`nearest`, ops `list`/`object`/`create`. The
  `*-list-with-create-button.json` files have only `full/list` and `nearest/list`. `top-level.json` has flat
  `observations["plain/list" | "plain/detail" | "guardian/list" | "guardian/detail"]` with `total`, `guard`, `rest`,
  `by_table`, `gates`. Baseline files `evidence/06.18-01/baseline-observations/depth{1,3}-{plain,guardian}.json` use
  `observations["legacy-no-mode/{op}"]["cold"|"warm"]["total"]`. Plan 12's record is
  `evidence/06.18-12/cost-observations/` (same nine file names, same layout).
- Table abbreviations already defined in COSTS.md: session = `django_session`, user = `auth_user`, ct =
  `django_content_type`, perm = `auth_permission`, leaf = `app_ancestorobservationleaf`; also publisher =
  `app_publisher`, book = `app_book`, booknote = `app_booknote`.
- Post-fix values for orientation only (the checker, not this list, is the source for the doc): plain depth 1 cold/warm
  totals 8/6 (list, object) and 7/5 (create), guard 7/5; plain depth 3 full 14/8 (list, object), 13/7 (create), guard
  13/7; plain depth 3 nearest 10/8, 9/7, guard 9/7; Guardian totals unchanged from 5829cae7 (depth 1: 11/6, 10/6,
  12/8, 12/8, 7/5, 7/5; depth 3 full 21/12, 22/14, 17/11; nearest 12/8, 14/10, 9/7) with guard 7/5 at depth 1,
  17/11 depth 3 full, 9/7 depth 3 nearest; the Guardian list cold order effect is now rest 4 (full) vs 3 (nearest).
  Top-level totals 1, 1, 4, 5 with guard 0 are unchanged.
- Grep baselines at HEAD in COSTS.md: the stale depth-1 Guardian sentence fragment the deferred item quotes occurs
  once (must become 0); `number of ancestors` 0; a `## History` heading 0; `8b11572a` 0; `76fdc7ff` 0; `5829cae7` 3.
  deferred-items.md: the item heading "no longer matches the current source" is followed by `status: open`.
  WINDOWS.md: row 43 is `open`, front matter `open_count: 1`, and the file ends with a JSON ledger block that the
  CLI maintains.
- Ledger CLI: `gsd-tools windows` has subcommands `status`, `append`, `waive`, `fixed`; `fixed` takes one positional
  id. Resolve `gsd-tools.cjs` with the standard resolver (at planning time: `$HOME/.claude/gsd-core/bin/gsd-tools.cjs`,
  run with `node`). `windows status --pick ledger.open_count` prints the open count.
- Environments: `.nox/tests-3-12-django-5-2` exists (Python 3.12.3, Django 5.2.19). `pytest` is not on PATH; invoke
  `<env>/bin/python -m pytest`. `python3` (system) is on PATH and is enough for the stdlib-only checker.
  `guardian` has no `__version__`; use `importlib.metadata.version("django-guardian")` if the runtime row needs it.
- deferred-items.md resolved pattern (06.18-07 and 261109-bf5 items): change the `status:` line to `resolved`, then add
  a `**Resolved in ...**` paragraph naming the commit(s) and the evidence, keeping the original What/Scope text.
</context>

<tasks>

<task type="tracer">
  <name>Task 1: Checker script red against the stale doc, then refresh 06.18-COSTS.md from the post-fix evidence until it is green</name>
  <files>.planning/phases/06.18-ancestor-authorization-for-nested-viewsets/evidence/261109-bvq/check_costs_md.py, .planning/phases/06.18-ancestor-authorization-for-nested-viewsets/evidence/261109-bvq/check-costs-md-before.txt, .planning/phases/06.18-ancestor-authorization-for-nested-viewsets/evidence/261109-bvq/check-costs-md.txt, .planning/phases/06.18-ancestor-authorization-for-nested-viewsets/06.18-COSTS.md</files>
  <action>
Step 0, source check. Run `git diff --quiet 8b11572a HEAD -- src` and `git status --porcelain -- src`. Both empty (the planning-time state): use `evidence/261109-bf5/cost-observations/` as the current evidence and `8b11572a3767e3942830c9d588d715975d0a3b96` as the measured source, and skip to step 1. Otherwise re-run the documented reproduce command (COSTS.md "Sources and runtime": `CV_ANCESTOR_COSTS_DIR=<dir> PYTHONPATH="$PWD/src" .nox/tests-3-12-django-5-2/bin/python -m pytest tests/test1/test_ancestor_costs.py -n 4 -q`) with `<dir>` = `evidence/261109-bvq/cost-observations/` under the phase directory, confirm 9 passed and `meta.source_sha` = HEAD with `src_dirty` false in every file, add those nine files to the commit, and use that directory and SHA everywhere below instead of the bf5 ones; report the deviation in the SUMMARY.

Step 1, the checker (`evidence/261109-bvq/check_costs_md.py`, stdlib only: `json`, `re`, `sys`, `pathlib`; no arguments; resolves the phase directory from `__file__`; exit 0 when every check passes, exit 1 after printing every mismatch as `MISMATCH <where>: doc=<x> json=<y>`; structural problems such as a missing heading or an unparseable row are also printed as mismatches so the run completes; always ends with a summary line counting the checks performed). It locates each table by the heading that precedes it and checks:
  1. The current 24-cell table under `## The 24 cells`: for every row, file `depth{Depth}-{provider}.json` in the current evidence directory, observation `{mode}/{op}` (`object` is the op key for the "object" rows); `Now cold / warm` = `total`, `Guard` = `guard`, `Rest` = `rest`, `Delta` = Now minus the Baseline column, Baseline = `evidence/06.18-01/baseline-observations/depth{Depth}-{provider}.json` observation `legacy-no-mode/{op}` cold and warm `total`, `status` 200 for cold and warm, and `Gates evaluated` = the model names derived from each gate tuple's permission codename (`app.view_publisher` -> Publisher, `app.view_book` -> Book, `app.view_booknote` -> BookNote; cold and warm gate lists equal). Row numbering 1-24 in the existing order.
  2. The history 24-cell table (the first table under `## History: plan 12 record (5829cae7)`): the same checks against `evidence/06.18-12/cost-observations/`.
  3. The categories table under `### Categories per request`, in the machine-checkable layout defined in step 3: expand the `Cells` column (numbers and ranges, hyphen or en dash), map each cell to its JSON observation at the row's temperature, parse the Guard and Rest token lists with the abbreviation map (session, user, ct, perm, publisher, book, booknote, leaf; `nothing` = empty dict) and compare to `guard_by_table` and `rest_by_table` exactly; assert that the rows cover all 48 (cell, temperature) observations exactly once.
  4. The top-level table under `## Nearest-only and top-level controls`: four rows against `top-level.json` keys `plain/list`, `plain/detail`, `guardian/list`, `guardian/detail` (`Total` = `total`, `Guard` = `guard`, `Tables` tokens = `by_table`).
  5. The render-helper totals: two parenthetical sentences in `## Render-helper work, separate from the guard` with the fixed form "depth 1: C/W full, C/W nearest; depth 3: C/W full, C/W nearest" (one for the plain leaf, one for the Guardian leaf), checked against the four `*-list-with-create-button.json` files' `full/list` and `nearest/list` cold/warm totals, plus the claim that the plain create-button totals equal the matrix list cells (cells 1, 2, 13, 14).
  6. The Sources table: the 40-hex SHA in the "Current measurement" source cell equals `meta.source_sha` in all nine current evidence files, each has `src_dirty` false, and the Python/Django strings in the runtime row match `meta`.
Also give the script a `--facts` flag that prints, from the JSON, the per-cell totals and guard/rest splits, the per-cell guard `django_content_type` counts, the create-button totals and the guard/rest difference per Guardian observation between `evidence/06.18-12/cost-observations/` and the current evidence. Every numeral you write into prose below is copied from this output, never typed from memory or from this plan.

Step 2, RED. Run `python3 <script> | tee <phase>/evidence/261109-bvq/check-costs-md-before.txt` against the unedited COSTS.md. It must exit 1 (the plain cold and the Guardian guard/rest columns do not match the current evidence; the History heading and the new categories layout do not exist yet). Keep that file as the RED record.

Step 3, refresh COSTS.md (use Edit for scoped replacements; keep every section the deferred item does not name unchanged):
  a. Intro paragraph: it now compares the current source (post-phase fixes included) with plan 01's baseline; keep the requirement/decision references.
  b. `## Sources and runtime`: rename the second column to "Current measurement"; source = the full measured SHA with "`src/` clean, identical to HEAD `<rev-parse HEAD at refresh>` (`git diff 8b11572a <HEAD> -- src` empty)"; evidence = the current evidence directory; runtime row from `meta` (Python 3.12.3 / Django 5.2.19) plus the pydantic and django-guardian versions read from the nox environment via `importlib.metadata`; import path row unchanged; reproduce command unchanged.
  c. Replace `## Final-source replay (plan 12)` with a new `## Source changes since the plan 12 record` section: `git diff 5829cae7 8b11572a -- src` contains exactly three commits. (1) `76fdc7ff` WR-01: the guard now owns actor admission for nested Guardian views (static validation, then Guardian's anonymous/inactive rules through `_cv_ancestor_actor_response`, then the ancestors), so `request.user` is first loaded inside the guard and session 1 + user 1 count as guard in all 28 Guardian observations (24 matrix cells cold and warm plus the four create-button observations): guard +2, rest -2, totals and by_table unchanged. Evidence: `evidence/261109-bf5/cost-replay-comparison.txt` section A shows the shift is already present at `c67c841d` (before the bf5 fix), section B shows it against 5829cae7; it is therefore WR-01's, not bf5's. (2) `a17823d9` WR-02: in the range, changed no count. (3) `8b11572a` quick task 261109-bf5: core `ViewSet.default_permissions` reads the resolved content type once, so plain cold `django_content_type` is 1 per gated ancestor (depth 1 and depth 3 nearest 5 -> 1, depth 3 full 15 -> 3), plain cold totals drop by 4 per gated ancestor, warm cells and Guardian cells unchanged; regression test `tests/test1/test_viewset.py`; evidence: section A. State that the bf5 evidence stands for HEAD at refresh time and that the Django 4.2/6.0 note (counts not written out) still applies. Name the checker script and its two output files.
  d. `## The 24 cells` intro: add, before the table, that Depth = the number of ancestors above the leaf view (depth 1 = one nested level, the Book view under Publisher; depth 3 = three nested levels, the leaf under Publisher -> Book -> BookNote), that every row is a nested request, and that top-level requests (no parent ViewSet) do zero ancestor work, linking `[Nearest-only and top-level controls](#nearest-only-and-top-level-controls)`. Rewrite the 24 rows from the current evidence (the checker is the source; you may add a temporary emit helper to the script to print the rows, or run it repeatedly until exit 0). Column layout unchanged.
  e. `### Categories per request`: keep the abbreviation paragraph (add publisher/book/booknote to it) and replace the table with the machine-checkable layout: columns `| Cells | Temperature | Guard | Rest |`; `Cells` lists cell numbers or ranges; `Temperature` is `cold` or `warm`; `Guard` and `Rest` are complete comma-separated `abbrev N` lists or the word `nothing`; no back-references such as "as list" or "as full"; a row may group only cells whose guard and rest categories are both identical at that temperature; all 48 observations covered exactly once. Add one sentence saying the layout is checked by the script.
  f. `### Plain leaves`: keep the actor-load, ancestor-lookup and model-permission bullets (warm plain is unchanged); rewrite the "Cold vocabulary" bullet: one ContentType lookup and one Permission query per gated ancestor (ct 1, perm 1), depth 3 full cascade ct 3, nearest ct 1; the former per-row ContentType read (ct 5 per ancestor, ct 15 at depth 3 full in the plan 12 record) was removed after the phase by quick task 261109-bf5 (`8b11572a`); it was vocabulary only, never access state. The per-cell numerals (now 8/7 at depth 1, 14/13 full and 10/9 nearest at depth 3) come from the facts output.
  g. `### Guardian leaves`, depth 1 bullet: replace the sentence attributing session and user loading to the rest of the request (the one the deferred item quotes) with: since WR-01 (`76fdc7ff`) the guard loads the actor for nested Guardian views, so session 1 + user 1 are guard work and the warm guard is session 1, user 1, perm 2, publisher 1 (5); the legacy one-for-one replacement statement and "rest reads no ancestor table" stay. Update the cell 8 / cells 19 vs 20 order-effect bullet to the current rest values (4 vs 3 cold) and keep its explanation; keep the Guardian cold-vocabulary bullet (ct 1 per gated ancestor) and add that plain and Guardian vocabulary now cost the same. The depth-3 nearest (+2) and full (+6 warm) bullets are unchanged in substance; re-check their numerals against the facts output.
  h. `### Repeated work` row "Core vocabulary N+1 on a cold ViewSet": status "Removed after the phase (quick task 261109-bf5, `8b11572a`)", evidence: plain cold ct equals the gated-ancestor count in every cell; regression test `tests/test1/test_viewset.py`.
  i. `## Nearest-only and top-level controls`: "(ct 1 instead of 3)" for the plain nearest control; point the top-level totals at the current evidence `top-level.json` and say they are identical to the plan 10/12 record; table values from the checker.
  j. `## Render-helper work`: plain sentence in the fixed form of step 1.5 with current totals and the equality to the matrix list cells; Guardian sentence in the same fixed form (its totals are unchanged from 5829cae7), keeping the `_immediate_parent_access` explanation and the "depth 1 warm total is 6" statement.
  k. `## Mutation checks`: add one sentence that the mutations were recorded at plan 10's source and were not re-run for this refresh.
  l. Append `## History: plan 12 record (5829cae7)`: the former "Final-source replay (plan 12)" paragraph (moved verbatim), then the former 24-cell table verbatim (first table under this heading; its Guardian Guard/Rest columns predate WR-01 and its plain cold columns predate 8b11572a; say so in one line), then the former categories table verbatim (labelled as the plan 12 layout, not script-checked), then the former render-helper totals (12/6, 26/8, 14/8) as one line. Do not carry old attribution prose into History beyond that paragraph.

Step 4, GREEN. Run `python3 <script> | tee <phase>/evidence/261109-bvq/check-costs-md.txt`; iterate on COSTS.md until exit 0. Then run the Task 1 verify command. Commit the four files as `docs(quick-261109-bvq): refresh 06.18-COSTS.md from the post-fix evidence (WR-01 guard/rest, bf5 plain cold ct)`.
  </action>
  <verify>
    <automated>python3 .planning/phases/06.18-ancestor-authorization-for-nested-viewsets/evidence/261109-bvq/check_costs_md.py && ! grep -q 'stays in the rest of the request' .planning/phases/06.18-ancestor-authorization-for-nested-viewsets/06.18-COSTS.md && grep -q 'number of ancestors' .planning/phases/06.18-ancestor-authorization-for-nested-viewsets/06.18-COSTS.md && grep -q '^## History: plan 12 record (5829cae7)' .planning/phases/06.18-ancestor-authorization-for-nested-viewsets/06.18-COSTS.md && grep -q '^## Source changes since the plan 12 record' .planning/phases/06.18-ancestor-authorization-for-nested-viewsets/06.18-COSTS.md && grep -q '8b11572a3767e3942830c9d588d715975d0a3b96' .planning/phases/06.18-ancestor-authorization-for-nested-viewsets/06.18-COSTS.md && grep -q '76fdc7ff' .planning/phases/06.18-ancestor-authorization-for-nested-viewsets/06.18-COSTS.md && grep -q 'a17823d9' .planning/phases/06.18-ancestor-authorization-for-nested-viewsets/06.18-COSTS.md && test -s .planning/phases/06.18-ancestor-authorization-for-nested-viewsets/evidence/261109-bvq/check-costs-md-before.txt && grep -q MISMATCH .planning/phases/06.18-ancestor-authorization-for-nested-viewsets/evidence/261109-bvq/check-costs-md-before.txt && git diff --quiet 8b11572a HEAD -- src</automated>
  </verify>
  <done>check_costs_md.py exits 0 against the refreshed COSTS.md (24 current cells, 24 history cells, all 48 category observations, 4 top-level rows, both render-helper sentences and the Sources SHA bound to JSON) and its RED output against the pre-refresh file is committed with at least one MISMATCH line; the stale Guardian attribution fragment is gone; Depth definition, Source-changes section naming 76fdc7ff, a17823d9 and 8b11572a, and the History section exist; HEAD's src still equals the measured source. Baselines at HEAD: script absent (fails), stale fragment 1, `number of ancestors` 0, both new headings 0, full SHA 0, 76fdc7ff 0, a17823d9 0.</done>
</task>

<task type="auto">
  <name>Task 2: Resolve the deferred item and close WINDOWS.md row 43 through the ledger CLI</name>
  <files>.planning/phases/06.18-ancestor-authorization-for-nested-viewsets/deferred-items.md, .planning/WINDOWS.md</files>
  <action>
Take Task 1's commit SHA (`git rev-parse --short HEAD` right after that commit). In `deferred-items.md`, in the item whose heading starts with "`06.18-COSTS.md` no longer matches the current source", change `status: open` to `status: resolved` and insert, directly under the status line and before the existing **What** paragraph, a `**Resolved in quick task 261109-bvq** (<sha>)` paragraph: COSTS.md refreshed from `evidence/261109-bf5/cost-observations/` for source `8b11572a` (identical to HEAD at refresh), WR-01 and bf5 attributed separately, the 5829cae7 record kept under the History heading, every table number checked by `evidence/261109-bvq/check_costs_md.py` (`check-costs-md.txt` exit 0; `check-costs-md-before.txt` is the pre-refresh failure), WINDOWS 43 fixed. Leave the What/Scope text as written.

Close the ledger row with the CLI, not by editing: resolve `gsd-tools.cjs` with the standard resolver (`~/.claude/gsd-core/references/gsd-run-resolver.md`; at planning time `$HOME/.claude/gsd-core/bin/gsd-tools.cjs`) and run `node <gsd-tools.cjs> windows fixed 43`. Confirm with `node <gsd-tools.cjs> windows status --pick ledger.open_count` printing 0 and the WINDOWS.md row 43 showing `fixed` with a `resolved_at` timestamp (the CLI also updates the front matter counts and the trailing JSON block). Do not touch any other row or count. If the CLI refuses (for example a different ledger schema), stop and report instead of hand-editing.

Confirm scope: `git status --porcelain -- src tests docs` is empty. Commit the two files as `docs(quick-261109-bvq): resolve the COSTS.md deferred item and fix WINDOWS 43`. Then write the SUMMARY per the execute-plan workflow at `.planning/quick/261109-bvq-refresh-06-18-costs-md-from-post-fix-evi/261109-bvq-SUMMARY.md`, naming both commits and the two checker outputs.
  </action>
  <verify>
    <automated>grep -n -A1 'no longer matches the current source' .planning/phases/06.18-ancestor-authorization-for-nested-viewsets/deferred-items.md | grep -q 'status: resolved' && grep -q 'Resolved in quick task 261109-bvq' .planning/phases/06.18-ancestor-authorization-for-nested-viewsets/deferred-items.md && grep -E '^\| 43 \|' .planning/WINDOWS.md | grep -q '| fixed |' && grep -q '^open_count: 0' .planning/WINDOWS.md && git diff --quiet HEAD -- src tests docs</automated>
  </verify>
  <done>The COSTS.md deferred item is `status: resolved` with a "Resolved in quick task 261109-bvq" paragraph citing Task 1's commit; WINDOWS.md row 43 reads `fixed` and `open_count: 0`, written by `gsd-tools windows fixed 43`; no src/tests/docs change. Baselines at HEAD: the item is `status: open`, the resolved phrase is absent, row 43 is `open`, `open_count: 1`.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| none at runtime | This plan changes planning documents and evidence only; no `src/`, `tests/`, `docs/` or package change, so no request path, permission check or template is touched |
| evidence -> cost record | 06.18-COSTS.md is the ANCE-08 record that later work (and the user) reads to judge the guard's cost; its numbers must be the measured ones |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-QBVQ-01 | Repudiation | 06.18-COSTS.md tables | low | mitigate | every table number is bound to the JSON evidence by `check_costs_md.py` (committed with its RED and GREEN outputs); the Sources SHA is checked against `meta.source_sha` of all nine files; `git diff --quiet 8b11572a HEAD -- src` in the verify pins the evidence to HEAD's source |
| T-QBVQ-02 | Tampering | attribution of the number changes | low | mitigate | WR-01 and bf5 are attributed from `cost-replay-comparison.txt` sections A and B (the guard/rest shift is present at c67c841d, before bf5), not from reasoning about the code alone; WR-02 is named as changing no count |
| T-QBVQ-03 | Tampering | WINDOWS.md ledger | low | mitigate | row 43 is closed with `gsd-tools windows fixed 43`; counts and the JSON block are never hand-edited; Task 2 verify checks row status and `open_count: 0` |
| T-QBVQ-SC | Tampering | npm/pip/cargo installs | low | accept | no package is installed; the checker is stdlib-only on the system `python3`, and any optional re-run uses the existing `.nox/tests-3-12-django-5-2` environment |
</threat_model>

<verification>
- `python3 .planning/phases/06.18-ancestor-authorization-for-nested-viewsets/evidence/261109-bvq/check_costs_md.py` exits 0 and prints a summary covering 24 current cells, 24 history cells, 48 category observations, 4 top-level rows, 2 render-helper sentences and the Sources SHA; `check-costs-md-before.txt` shows the same script failing on the pre-refresh file.
- COSTS.md: stale Guardian attribution fragment absent; Depth definition with the top-level link present; `## Source changes since the plan 12 record` names 76fdc7ff, a17823d9 and 8b11572a with separate effects; `## History: plan 12 record (5829cae7)` holds the old tables.
- deferred-items.md item resolved with the refresh commit; WINDOWS.md row 43 fixed and `open_count: 0` via the CLI.
- `git diff --quiet 8b11572a HEAD -- src` and `git diff --quiet HEAD -- src tests docs` both hold: docs and evidence only.
</verification>

<success_criteria>
- 06.18-COSTS.md stands for source 8b11572a (HEAD's src), with WR-01 and bf5 attributed separately, Depth defined, top-level control linked, and the 5829cae7 record kept as history.
- No table number is hand-typed: the committed checker binds every number to JSON and passes; its pre-refresh failure is recorded.
- The deferred item and WINDOWS 43 are closed; two docs commits; no source, test or published-docs change.
</success_criteria>

<output>
Create `.planning/quick/261109-bvq-refresh-06-18-costs-md-from-post-fix-evi/261109-bvq-SUMMARY.md` when done
</output>
