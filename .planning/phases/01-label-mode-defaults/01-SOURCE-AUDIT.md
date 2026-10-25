# Phase 01 — Source coverage and execution graph

Planning only. No implementation, branch operation or commit performed. Existing dirty `.gitignore`, `.planning/config.json` and `.planning/intel/` are outside this plan set.

## Dependency graph and ownership

| Task | Needs | Creates / user-visible result | Checkpoint |
|---|---|---|---|
| 01-01-01 | Existing raw cv_button/leaf and strict-mode patterns | Setting-to-render tracer; lazy floors; safe invalid-mode fallback | No; D-21/D-22 already locked |
| 01-01-02 | Accessor raw reader and sentinel | Operators receive E108 for malformed settings | No; D-01 already locked |
| 01-02-01 | 01-01 accessor and E108 | Real toolbars use context floor; full startup checks survive invalid strict floors | No |
| 01-02-02 | Same accessor and context integration | Real table rows use independent list floor; existing map precedence preserved | No |
| 01-03-01 | 01-01 accessor/leaf | Real cards use configured floor; public resolver and matching reference docs | No; D-15/D-21 already locked |
| 01-03-02 | Card API and existing release docs | Consumers can migrate raw attribute reads and restore card appearance | No |
| 01-04-01 | Both wave-2 consumer integrations | Executable documented setting and canonical precedence sections | No |
| 01-04-02 | Canonical sections and card migration docs | Linked diagram/reference pages, settled decisions and final gates | No; D-19 already locked |

Wave 1: 01-01. Wave 2: 01-02 and 01-03 in parallel, with zero modified-file overlap. Wave 3: 01-04.
01-02 reuses the configuration test file from 01-01, so it explicitly depends on that earlier plan.
01-04 consumes all prior runtime contracts and retargets card documentation links only when their canonical anchors exist. 01-03 uses existing anchors and verifies a strict docs build before wave 3.
All plans have two tasks; no task modifies more than five files. Estimates use calibration factor 1 and low confidence from zero samples, not self-rated certainty.

## Multi-source coverage audit

| Source | ID | Feature / constraint | Plan / task | Status | Notes |
|---|---|---|---|---|---|
| GOAL | Phase 1 | One project floor per location, one accessor, unchanged default output | 01-01 through 01-04 | COVERED | Leaf, toolbar/row, card, docs and full goldens |
| GOAL | SC-1 | context=both on unmapped toolbar actions; rows/cards unchanged; W292 silent | 01-02-01 | COVERED | Eligible ordinary inline actions; filter custom template explicitly Phase 3 |
| GOAL | SC-2 | card=label; explicit both still wins | 01-03-01 | COVERED | HTTP test and resolver tests |
| GOAL | SC-3 | override_settings freshness and non-strict recovery | 01-01-01 | COVERED | Includes enter/exit and bad stamp |
| GOAL | SC-4 | E108 keys/modes derived from location set | 01-01-02 | COVERED | Dynamic location-set test |
| GOAL | SC-5 | No three old literals; unchanged goldens; merge docs | 01-02-02, 01-04 | COVERED | Exact source grep, docs contract and protected-path diff |
| REQ | LMOD-01 | Per-key project merge; existing maps replace whole | 01-01-01, 01-02-02, 01-04-01 | COVERED | Scope and semantics preserved |
| REQ | LMOD-02 | All three consumers use one accessor | 01-01-01, 01-02, 01-03-01 | COVERED | Direct source and end-to-end tests |
| REQ | LMOD-03 | None card attribute; explicit overrides and restoration | 01-03 | COVERED | Type, check, docs, migration together |
| REQ | LMOD-04 | Call-time settings read | 01-01-01 | COVERED | No value cache or Pydantic snapshot |
| REQ | LMOD-05 | Strict raise / non-strict log and fallback | 01-01-01 | COVERED | Settings and stamps; unhashable values |
| REQ | LMOD-06 | E108 invalid key/value and complete check reporting | 01-01-02, 01-02-01 | COVERED | W292 integration prevents exception loss |
| RESEARCH | R-01 | Circular imports / deferred LOCATIONS | 01-01-02 | COVERED | New subprocess settings import test asserts button_data absent before checks and loaded by E108 checks |
| RESEARCH | R-02 | W292 exception can discard E108 | 01-02-01 | COVERED | Full check_viewsets test, not only view-level checks |
| RESEARCH | R-03 | Unhashable values and hot-path warning flood | 01-01-01 | COVERED | repr key plus Lock only around check/add; fallback and logging outside lock; bounded nested-recovery test |
| RESEARCH | R-04 | Lazy settings and unset-versus-None distinction | 01-01 | COVERED | Sentinel; same settings object reads new values |
| RESEARCH | R-05 | Eager dict.get fallback can defeat explicit mode | 01-02-02 | COVERED | Membership branch, invalid-floor bypass test |
| RESEARCH | R-06 | Falsey stamp and empty-label/icon-less compatibility | 01-01-01 | COVERED | Existing behavior retained and exercised |
| RESEARCH | R-07 | Card old-default tests, None check and model comment | 01-03-01 | COVERED | All updated with new resolver |
| RESEARCH | R-08 | Cross-test log-state isolation / random order | 01-01-01/02, 01-02-02 | COVERED | Initial warning tests isolate private seen-set; shared conftest autouse fixture covers all later tests, with seeded xdist gate and no production reset |
| RESEARCH | R-09 | Target-view mode beats floor; filter separate | 01-02-01, 01-04-01 | COVERED | Explicit precedence tests and scope note |
| RESEARCH | R-10 | All docs touchpoints and valid anchors | 01-03, 01-04 | COVERED | Includes buttons.md, corrected Mermaid file and PROJECT.md |
| RESEARCH | R-11 | E108 exact wording, level and no hint | 01-01-02 | COVERED | Unknown-key message ends with repr(value) |
| RESEARCH | R-12 | Read-only constant; no extra public helper | 01-01-01 | COVERED | MappingProxyType chosen; helper stays private |
| RESEARCH | R-13 | Security boundary / no raw invalid mode reaches leaf | 01-01, 01-02, 01-03 | COVERED | Per-plan threat models; no new template logic |
| RESEARCH | R-14 | Global quality gates and external theme note | 01-04 verification, 01-03/04 outputs | COVERED | Existing local npm test verified; no package-fetching npx |
| RESEARCH | R-15 | No DB/service/OS/secrets migration | All plans | COVERED | No such tasks added |
| CONTEXT | D-01 | E108 Error for bad key and bad value | 01-01-02 | COVERED | One-way decision already made |
| CONTEXT | D-02 | LOCATIONS-derived keys; form rejected; default-set equality | 01-01-01/02 | COVERED | No location set relocation |
| CONTEXT | D-03 | All non-dicts incl. explicit None invalid | 01-01-02 | COVERED | One Error per non-dict |
| CONTEXT | D-04 | One message per bad entry | 01-01-02 | COVERED | Unknown key wins over bad value on same entry |
| CONTEXT | D-05 | E106/E210 wording, no hint | 01-01-02 | COVERED | Exact message assertions |
| CONTEXT | D-06 | Nested dictionaries invalid | 01-01-01/02 | COVERED | Render-safe and check-invalid |
| CONTEXT | D-07 | E108 beside E106, deferred imports, raw lazy read | 01-01-02 | COVERED | No new model field |
| CONTEXT | D-08 | Bad setting value uses package floor; unknown keys ignored at render | 01-01-01 | COVERED | Requested-location lookup only |
| CONTEXT | D-09 | is_strict raises; otherwise warns and falls back | 01-01-01 | COVERED | Existing strict helper reused |
| CONTEXT | D-10 | Bad stamped mode recovers; cv_no_label guard intact | 01-01-01 | COVERED | Lazy callback preserves strict error source |
| CONTEXT | D-11 | One warning per process per bad location/value pair | 01-01-01 | COVERED | No source dimension or settings reset; lock ensures check/add atomicity |
| CONTEXT | D-12 | Bad caller location always raises | 01-01-01 | COVERED | Strict and non-strict tests |
| CONTEXT | D-13 | Lazy override_settings support; never mutate defaults | 01-01-01 | COVERED | Immutable constant and no value cache |
| CONTEXT | D-14 | Card attribute None; exact chain; E210 and docs together | 01-03-01 | COVERED | Five-file coherent slice |
| CONTEXT | D-15 | Public card resolver used by stamping | 01-03-01 | COVERED | One-way decision already made |
| CONTEXT | D-16 | Breaking plus migration; Added public surface | 01-03-02 | COVERED | Also Fixed for production crash |
| CONTEXT | D-17 | Setting-first 0.29 recipe | 01-03-02, 01-04-02 | COVERED | Order pinned in docs test |
| CONTEXT | D-18 | no_label untouched and no new warning | 01-01-01, 01-03-01 | COVERED | Existing compatibility chain kept |
| CONTEXT | D-19 | Keep singular/plural names, stable | 01-02, 01-04 | COVERED | Docs distinction; PROJECT decision retained |
| CONTEXT | D-20 | Removal before 1.0 recorded, not implemented | 01-04-02 | COVERED | Phase 7 handoff only |
| CONTEXT | D-21 | Four new names public, constant read-only | 01-01-01, 01-03, 01-04 | COVERED | No accidental extra public helper |
| CONTEXT | D-22 | Exact setting name | 01-01, 01-04 | COVERED | No alternate spelling |
| CONTEXT | D-23 | PROJECT Key Decisions | 01-04-02 | COVERED | Rows already exist; update without duplication |
| CONTEXT | D-24 | Canonical merge/replace table and links | 01-04-01, 01-03-01 | COVERED | Existing map semantics unchanged; card links retargeted in 01-04-01 with anchor creation |
| CONTEXT | D-25 | Canonical orders; Mermaid MICON defaults map | 01-04 | COVERED | Correct context_buttons.md target |
| CONTEXT | D-26 | Example project untouched | All plans; 01-04 final diff | COVERED | Protected path |

No source items are missing. Excluded by scope: real form location/button leaf (Phase 6), filter toggle (Phase 3), form key grammar (Phase 2), removal of no_label (LATER-01), rejected rename (LATER-02), theme repository edits, version bump, branch/PR operations.

### Selected discretion / research reconciliation

- Read settings per call without a merged-map cache. MappingProxyType enforces the documented read-only package floor.
- Use private `_invalid_label_mode` with a lazy fallback callback; this prevents an invalid floor from masking a strict malformed-stamp error.
- Unlike the research sketch, warning identity has no source dimension and is not reset on setting_changed. This honors D-11 literally across sources and override_settings; isolated tests monkeypatch `_warned`, with a shared function-scoped autouse fixture added in 01-01-02. No receiver or public warning-reset API is needed. Fallback and logging stay outside the dedup lock.
- Non-dict runtime configuration follows strict raise / non-strict package-floor fallback (research A2, chosen explicitly).
- E108 unknown-key wording ends with repr(value); one diagnostic per entry, input order; choices sorted.
- Research's optional merged-map helper is not introduced: all consumers require only the location accessor. No required capability is omitted.
- Research branch uncertainty is overridden by the invocation: do not create, rename or switch branches.
- Existing local npm test passed; use that non-installing command rather than fetching a Node package.

## Spec-less edge accounting

The input report contained 12 applicable items. Ten are resolved by explicit acceptance criteria and plain must_haves.truths; the two unclassified items remain flagged assumptions, as required. No dismissal or backstop claim is invented.

| Requirement | Category | Disposition | Predicate location |
|---|---|---|---|
| LMOD-01 | adjacency | resolved / explicit | 01-01 truths; equal/single-entry override changes only that location |
| LMOD-01 | empty | resolved / explicit | 01-01 truths; absent/empty/singleton/None distinction |
| LMOD-01 | ordering | resolved / explicit | 01-01 truths; dict insertion order does not alter resolved modes |
| LMOD-02 | unclassified | unresolved / FLAGGED | 01-02 Flagged assumptions; consumer-set completeness review |
| LMOD-03 | empty | resolved / explicit | 01-03 truths; None inheritance, empty-string E210, empty action list |
| LMOD-03 | encoding | resolved / explicit | 01-03 truths; exact strings, no Unicode/case normalization |
| LMOD-04 | unclassified | unresolved / FLAGGED | 01-01 Flagged assumptions; override-settings lifecycle completeness review |
| LMOD-05 | empty | resolved / explicit | 01-01 truths; malformed setting versus falsey-stamp compatibility |
| LMOD-05 | encoding | resolved / explicit | 01-01 truths; exact string validation, safe repr-based dedup |
| LMOD-06 | adjacency | resolved / explicit | 01-01 truths; one message per entry, not separate key/value messages |
| LMOD-06 | empty | resolved / explicit | 01-01 truths; no messages for absent/empty/valid singleton, one for non-dict |
| LMOD-06 | ordering | resolved / explicit | 01-01 truths; entry-order diagnostics and sorted allowed choices |

Equality: 12 = 10 authored explicit predicates + 2 flagged assumptions.

## Prohibition recall

Recall considered each requirement's unwanted expansions: theme-owned label policy, overriding deliberate user choices, broader per-variant scope, renaming public knobs, undisclosed attribute break, auto-migration of configuration, false compatibility claims, changing existing map semantics, hard-coded defaults, staleness, input mutation, warning flood, unhashable crashes, normalization and error suppression. Ordinary correctness candidates are assigned to edge tests/code review rather than minted as prohibitions. Injection/access-control canon is referred to per-plan threat models and /gsd-secure-phase.

Two product-intent prohibitions remain after precision filtering, projected using the installed `projectProhibitions` serializer:

1. **01-01 must_haves.prohibitions:** label-mode defaults must not become theme-owned policy or override explicit project/view/button choices.
2. **01-03 must_haves.prohibitions:** unchanged rendered output must not be presented as absence of a breaking Python attribute change.

Both are descriptor-less, status unresolved, explicitly flagged-unverified. No check_kind/check_target or invented enforcement fixture is attached. Carry these to verification for review; neither is claimed machine-certified by planning.

## Grounding and baseline evidence

- All existing source, test, doc and planning paths named in the plans were checked with git ls-files; they are tracked. Installed workflow paths are intentionally described as runtime resources, not source paths.
- Only new implementation path: tests/test1/test_label_mode_docs.py. PLAN/SUMMARY artifacts are new intended planning outputs.
- Existing quick pytest command: 182 passed in 2.30s during planning.
- `npm --prefix . test`: 8 test files / 126 tests passed with local Node v20.20.2. Existing navigation-not-implemented messages were nonfatal; no package install performed.
- No prior phase history; history digest is empty. No project `.claude/skills/` or `.agents/skills/`, and no `.planning/graphs/graph.json`. The installed django-crud-views skill was read; current tracked source/locked decisions override its older package-version defaults.
- Baseline protected-path comparison uses fixed revision ebc7c23259ae35b2e4f34047d0da903e68a48ac8 (verified subject: `docs(01): capture phase context`), not a moving task HEAD. Current STATE.md records 02342703bcb65a94dcb8d1117721c828850a81fa; the earlier provenance claim was corrected during review revision.

## Reviews-mode revision — Round 1, c1546c2

All 14 current actionable findings are incorporated into the four existing plans; per-plan Review Dispositions Ledgers carry the canonical dispositions. No source coverage or probe-derived predicate/prohibition was removed. No deferred feature was implemented or added to scope.

| Finding | Coverage |
|---|---|
| R1 warning isolation | 01-01-02 shared autouse fixture; 01-02-02 explicitly consumes it; seeded xdist gates |
| R2 frozenset replacement | 01-01-02 module-attribute monkeypatch |
| R3 stock card no_label exception | 01-03-01 detail/update text-only, delete icon-only assertions |
| R4 docs anchor ordering | 01-03 existing anchors + strict build; 01-04-01 creates/retargets canonical links together |
| R5 re-entrant lock deadlock | 01-01-01 fallback/logging outside lock and timeout-bounded nested-recovery regression |
| R6 settings import boundary | 01-01-02 fresh-process before/after-check assertions |
| R7 stale settings row | 01-04-01 row rewrite and scoped negative assertion |
| R8 baseline provenance | 01-04 verification and this audit identify actual commit subject |
| R9 authorized icon-bearing doc tracer | 01-04-01 exact context fields plus icon-bearing control render |
| R10 class-attribute comments | 01-02-01/02 all three comments, no forbidden grep literals in action prose |
| R11 optional scalar wording | 01-02-02 source E211 + test; 01-04-01/02 reference wording |
| R12 check reference completeness | 01-04-02 E106/E108 error rows and E210 None note + test |
| R13 #213 recipe consistency | 01-03-02 existing bullet rewrite; 01-04-02 order assertion |
| R14 example selection stability | 01-04-01 unique card-key literal assignment rather than positional selection |

Live-source qualifications: random-order is installed but opt-in (`addopts` only enables strict markers); existing import tests cover several modules, but none directly guards the settings boundary. The deadlock and positional-selector issues are prospective plan risks because those new symbols/tests do not exist yet. The source-qualified dedup/reset alternative remains explicitly rejected in 01-01's ledger in favor of the existing D-11 contract, without blocking the test-isolation fix.

File ownership additions: 01-01 owns tests/test1/conftest.py and tests/test1/test_import_safety.py; 01-02 owns src/crud_views/lib/view/action_menu.py; 01-04 additionally owns docs/reference/card-list-view.md after 01-03. Wave 2 remains disjoint; waves and dependency IDs are unchanged. Each plan still has two tasks and no task modifies more than five files. Estimates recalibrated with factor=1, sample_count=0, confidence=low; 01-01 and 01-04 allow for their extra reads/tests.

Revision validation: all four frontmatter and structure checks pass (zero errors; only the pre-existing already-locked one-way checkpoint warnings). Every automated command retains an immediately following observable fails_when; all eight tasks retain read_first and acceptance_criteria. git ls-files --error-unmatch confirms all existing named source/doc/test inputs, including added ownership paths. git diff --check passes. The new seeded cross-module command was run against the current, unimplemented baseline: 148 passed in 0.72s. This grounds the command/plugins, not the future fixture or new regression tests. No source implementation, branch operation or commit was performed.

## Plan validation results

- All four files pass `frontmatter.validate --schema plan` and `verify.plan-structure`, with two tasks each and no errors.
- The structure validator emits generic missing-checkpoint warnings for retained one-way ratings. These are intentionally not converted into checkpoints: D-01, D-15, D-19 and D-21 are already human decisions, and the invocation explicitly forbids re-gating them.
- `git diff --check` passes. The protected-path comparison to the recorded baseline is empty and the revision exists.
- Planning changed only the four PLAN files, this audit, Phase 1 roadmap placeholders and the task verification map. No implementation file was changed and no new feature test has been claimed to pass.
- Do not commit during this planning invocation; the orchestrator commits after verification.
