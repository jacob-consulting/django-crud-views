---
phase: 03-filter-toggle-label-mode
verified: 2026-10-26T16:56:17Z
status: passed
score: 22/22 must-haves verified
covered_files: [".planning/phases/03-filter-toggle-label-mode/03-01-PLAN.md",".planning/phases/03-filter-toggle-label-mode/03-01-SUMMARY.md",".planning/phases/03-filter-toggle-label-mode/03-02-PLAN.md",".planning/phases/03-filter-toggle-label-mode/03-02-SUMMARY.md",".planning/phases/03-filter-toggle-label-mode/03-REVIEW-DISPOSITION.md",".planning/phases/03-filter-toggle-label-mode/03-REVIEW-FIX.iter2.md",".planning/phases/03-filter-toggle-label-mode/03-REVIEW-FIX.md",".planning/phases/03-filter-toggle-label-mode/03-REVIEW.md",".planning/phases/03-filter-toggle-label-mode/03-SECURITY.md",".planning/phases/03-filter-toggle-label-mode/03-UAT.md",".planning/phases/03-filter-toggle-label-mode/03-UI-REVIEW.md",".planning/phases/03-filter-toggle-label-mode/03-VALIDATION.md","CHANGELOG.md","docs/migrating-1.0.md","docs/reference/action_menus.md","docs/reference/buttons.md","docs/reference/context_buttons.md","docs/reference/icons.md","docs/reference/javascript.md","src/crud_views/lib/view/base.py","src/crud_views/lib/view/buttons.py","src/crud_views/lib/view/label_mode.py","src/crud_views/lib/views/mixins.py","src/crud_views/locale/de/LC_MESSAGES/django.mo","src/crud_views/locale/de/LC_MESSAGES/django.po","src/crud_views/static/crud_views/js/list.filter.js","src/crud_views/templates/crud_views/tags/context_action_filter.html","src/crud_views/templatetags/crud_views.py","tests/js/list.filter.test.js","tests/test1/golden/action_menus/toolbar_publisher_list.html","tests/test1/test_action_menus_golden.py","tests/test1/test_button_leaves.py","tests/test1/test_context_action_label_mode.py","tests/test1/test_filter_toggle_label_mode.py","tests/test1/test_i18n.py","tests/test1/test_label_mode_docs.py"]
covered_digest: "v3:sha256:4fb3cb353bd45b9ca562ce8105caee12181a3f538c79d0d6b4899c0792031f24"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: human_needed
  previous_score: 22/22
  gaps_closed: []
  gaps_remaining: []
  regressions: []
  human_checks_closed: 4
decision_coverage:
  honored: 11
  total: 11
  not_honored: []
requirements:
  FILT-01: satisfied
  FILT-02: satisfied
  FILT-03: satisfied
  FILT-04: satisfied
human_verification: []
---

# Phase 3: Filter toggle label mode Verification Report

**Phase Goal:** The list filter toggle follows the configured label mode like every other context button, and stays accessible in each mode.
**Verified:** 2026-10-26T16:56:17Z
**Status:** passed
**Re-verification:** Yes — refresh after completed UAT and review fixes, at HEAD `b78b3d101d5880203d3c414d135a02ed5c0b2746`.

The previous report had no implementation gaps or overrides; its four human checks are now recorded as passed in `03-UAT.md` (committed in `87903c8`). Since that report, review fixes changed the resolver pipeline. This refresh re-established the roadmap and PLAN contract, read the current source, and ran named behavioral checks against the current checkout. It does not treat SUMMARY claims as implementation evidence.

The old PLAN/SUMMARY A1 and A11 dispositions are historical: malformed resolved configuration is now validated before custom labels render, and a filter's toolbar mode is resolved once. `03-REVIEW-FIX.md`, `03-REVIEW-FIX.iter2.md`, current source and fresh regressions establish the superseding behavior. Compatibility fallback for hand-built direct template contexts remains intact. No must-have override is needed.

## Goal Achievement

### Observable Truths

The four roadmap criteria remain the contract. The fourteen 03-01 truths and four 03-02 truths add specific edge and documentation checks; all are retained below for continuity with the previous 22-truth report.

| # | Truth | Status | Evidence |
|---|---|---|---|
| SC-1 | `CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE = {"filter": "both"}` renders icon + "Filter" with no `title`; `"label"` renders text only; default icon output is byte-identical to the toolbar golden. | VERIFIED | `context_action_filter.html:1-14` branches on the resolved mode. Fresh `test_filter_both_tracer`, `test_filter_raw_default_bytes`, `test_toolbar_list_with_filter` and the full named presentation matrix pass. The pre-phase golden and production JS diff is empty. |
| SC-2 | In label mode, without icon spans, clicking still flips `aria-expanded` and persists open/closed state. | VERIFIED | Fresh JS two-click label cases assert collapse calls, ARIA and one exact boolean POST per accepted click. `list.filter.js:15-38` tolerates zero icon children. Fresh Python tracer exercises the actual session POST→GET path in `mixins.py:322-355`. Completed browser UAT also covers label mode and reload. |
| SC-3 | The visible text never changes between states; only `aria-expanded` and the icon change. | VERIFIED | Fresh JS `keeps the label` cases check node identity and exact text through two clicks, both starting states, default/Unicode labels, label-only and both element/host layouts. Failure and reordered-request cases also pass. |
| SC-4 | "Filter" is a translated msgid and renders in German with the German catalog. | VERIFIED | `FilterContextButton.get_context` calls `_("Filter")` at runtime. Fresh PO/MO membership, distinct Unicode gettext sentinel and German rendering tests all pass; German page context includes `Aktionen`. Identical English/German spelling alone is not used as catalog proof. |
| 01-1 | EDGE-FILT-01-empty: None override and empty/unrelated maps reach the live floor; selected maps replace lower maps; direct instances use their own override/key and no target default. | VERIFIED | `base.py:299-328` implements whole-map selection and lazy floor; `buttons.py:333` passes the explicit button with no target default. Fresh named resolution matrix, renamed/direct-button, singular-default exclusion and nested live-floor tests pass. |
| 01-2 | EDGE-FILT-01-encoding: mode-less/icon raw strings and toolbar golden remain unchanged; unsupported direct modes retain icon classes; icon has hidden label/title/tooltip and both has spaced text without them. | VERIFIED | Fresh raw-baseline, direct-mode fallback, golden and presentation tests pass. Literal `"icon"` class lookup remains in the compatibility branch; both has a literal separator. Baseline test commit `cf17af2` contains only the test file and predates production changes; golden/handler diff against `3a51f81` is empty. |
| 01-3 | EDGE-FILT-02-adjacency: shared host class tokens survive swaps; mixed/unusable host placements use children; label has no icons/hooks. | VERIFIED | Template requires both usable host classes. Fresh 24-case mode/state/placement matrix plus 12 host-slot fallback cases pass. Fresh JS host two-click tests use overlapping `icon` tokens and assert active/inactive classes and unrelated button classes. |
| 01-4 | EDGE-FILT-02-empty: label-only toggles collapse and persist; no-filter/pinned pages have no toggle and scripts remain harmless. | VERIFIED | Fresh `test_filter_visibility` checks both absent page cases and direct visibility contexts. Fresh JS label cases and `loads harmlessly` check the unchanged handler. Both early `cv_access=False` returns remain before mode resolution in the builder. |
| 01-5 | EDGE-FILT-02-encoding: each accepted click uses the existing path, POST, CSRF and JSON headers and boolean payload, never label characters. | VERIFIED | Fresh JS `expectPost` checks the full fetch tuple for every default/Unicode two-click case. Production `list.filter.js:33-38` constructs only `{filter_expanded: next}`. |
| 01-6 | EDGE-FILT-02-ordering: collapse precedes DOM/persistence; throw/false leaves state and requests unchanged; rejected POST preserves a successful toggle. | VERIFIED | Fresh `collapses before`, label-only throw/refusal and rejected-POST tests pass. The adapter executes before ARIA/icon mutation and fetch; rejection handler does not alter the DOM. |
| 01-7 | EDGE-FILT-02-idempotency: two accepted clicks restore either initial state with exactly one opposite-state POST per click; refusal emits none. | VERIFIED | Fresh two-click tests assert call counts and state after each click for both initial states; fresh refusal test asserts no fetch. |
| 01-8 | EDGE-FILT-02-concurrency: outstanding requests retain their click's boolean; out-of-order settlement never rolls back the latest local state; no server ordering guarantee is introduced. | VERIFIED | Fresh `never rolls back` cases reject the latest request first, resolve the earlier one late, and assert final ARIA/icons/label and both request bodies. Production has no response-driven DOM update. Server write ordering remains outside this local-state contract. |
| 01-9 | EDGE-FILT-03-empty: empty custom labels preserve the translated seed and a nonempty accessible label without icon hooks. | VERIFIED | `buttons.py:69-80` only replaces the seed for a truthy rendered label. Fresh gettext sentinel test verifies empty-result preservation; fresh label presentation cases verify visible name and no icon hooks. |
| 01-10 | EDGE-FILT-03-encoding: default/Unicode labels retain exact text through toggles and ordinary untrusted text is escaped. | VERIFIED | Fresh JS two-click cases compare exact text; six fresh `test_filter_label_escaping` cases reject injected `<b>` elements and compare decoded text. The template uses ordinary Django interpolation without safe-marking. |
| 01-11 | EDGE-FILT-03-idempotency: both element/host and label-only toggles preserve visible label node and text through two clicks from either state. | VERIFIED | Twelve fresh `keeps the label` cases assert the same node with `toBe(f.label)` and unchanged text after each click. |
| 01-12 | EDGE-FILT-03-concurrency: refusal/throw and delayed/rejected/reordered persistence never replace or alter the visible label. | VERIFIED | Fresh failure and out-of-order tests assert text and, where applicable, node identity. The handler only selects icon hooks; labels have none in the server-rendered template. |
| 01-13 | EDGE-FILT-04-empty: core German PO has a non-fuzzy Filter translation and compiled catalog explicitly contains the key. | VERIFIED | Fresh `test_filter_catalog_entry` parses the PO, checks occurrence/non-obsolete/non-fuzzy text and checks membership in the compiled MO catalog. It ran and passed; optional `polib` was available. |
| 01-14 | EDGE-FILT-04-encoding: Unicode sentinel proves runtime gettext, German rendering proves active language, PO/MO checks prove catalog membership and custom labels override the seed. | VERIFIED | Fresh `test_filter_gettext_at_render_time` uses two different sentinels and custom/empty labels; all three `test_filter_german_render` cases assert `Aktionen`, `Filter`, custom `Suchen` and language restoration. |
| 02-1 | Projects can configure a settings-map or FilterContextButton override; declared key/no target default are explained and canonical precedence linked. | VERIFIED | Read `context_buttons.md:85-130` and `action_menus.md:87-111`: real import, both settings/per-view examples, renamed key and canonical link exist. Fresh `test_filter_toggle_reference_contract` passes; completed UAT item 1 confirms editorial fidelity. |
| 02-2 | Theme authors find all modes, host/mixed placement, constant translated/custom labels, optional hooks and whole-template ownership in a compact contract. | VERIFIED | `context_buttons.md:115-130`, `buttons.md:218-224,306-312`, `icons.md:173-179` match current source. Runtime validation prose includes the review fix. UAT items 1–2 passed; fresh template/JS checks exercise the described shapes. |
| 02-3 | Docs preserve stable disclosure IDs, collapse/error behavior, persistence, reset and never-folded rules. | VERIFIED | `javascript.md:187-219` matches the unchanged handler, including reset and persistence failure handling. `action_menus.md:182-186` retains never-folded behavior. UAT item 2 passed and fresh JS ordering/error tests pass. |
| 02-4 | Unreleased Fixed explains the configured floor effect; migration contract/checklist guide copied templates; default goldens remain unchanged and every quality gate has an explicit result. | VERIFIED | Read `CHANGELOG.md:156-167` and both migration locations (`migrating-1.0.md:332-343,404-407`). UAT item 3 passed. Golden diff is empty. Historical gate outcomes are explicit, including the pre-existing global Markdown-format failure; fresh targeted checks and orchestrator regression results are distinguished below. |

**Score:** 22/22 truths verified; 0 present-but-behavior-unverified; 0 overrides.

No prohibition items are declared in either PLAN. No backstop-only truths or coincidental-reliance flags were identified. Production establishes the IDs, mode values and label/icon structure used by the interaction fixtures; fixtures are input providers, not an otherwise-missing production precondition.

### Review Fix Verification

| Finding | Current implementation | Fresh evidence | Result |
|---|---|---|---|
| WR-01: duplicate filter resolution | `buttons.py:333-347` resolves before custom labels; `base.py:646-650` preserves a pre-resolved toolbar mode. | `test_filter_toolbar_resolves_mode_once`: 3 modes, exact call count, conflicting subclass target default, matching label/leaf mode. | VERIFIED |
| WR-02: silent malformed runtime mode | `buttons.py:334-341` uses `is_label_mode` / `_invalid_label_mode` before the label hook; strict raises, otherwise warn-once and configured floor. | Named `test_filter_malformed_resolved_mode[label-text-settings]` passes direct and toolbar strict exceptions, repeated fallback, custom label and warning-dedup assertions. The full source matrix covers four sources, two invalid strings and three floors; the orchestrator ran it in the 281-case focused gate. | VERIFIED |
| CR-01: toolbar stamp overrides row map | `base.py:646` preserves stamps only at `location == "context"`; list rows resolve their own map/floor. | `test_filter_context_mode_does_not_override_row_mode`: all 3 distinct context/row pairs pass, including normalized row button data. | VERIFIED |

The current `03-REVIEW.md` is clean. Four historical INFO findings remain recorded in `03-REVIEW-DISPOSITION.md`; neither fixed warnings nor CR-01 are carried as open findings.

### Required Artifacts

Fresh owner checks: `verify.artifacts` reports 6/6 for each plan (both exit 0). Existence, substantive implementation and wiring were also checked directly.

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `src/crud_views/lib/view/buttons.py` | Filter context, resolution and gettext | VERIFIED | Real builder, early visibility guards, declared key, runtime validation and customization chain; invoked through `_cv_get_action_context`. |
| `src/crud_views/templates/crud_views/tags/context_action_filter.html` | Accessible three-mode renderer | VERIFIED | Real mode branches, mode classes, host/element icons and stable disclosure attributes; default template of FilterContextButton. |
| `tests/test1/test_filter_toggle_label_mode.py` | Compatibility, resolution/customization and presentation evidence | VERIFIED | Active direct/integration assertions plus all three review regressions; selected tests freshly passed. |
| `tests/js/list.filter.test.js` | Optional-icon and invariant evidence | VERIFIED | Loads production handler and asserts exact requests, ordering, node identity and asynchronous outcomes; 22 selected cases freshly passed. |
| `src/crud_views/locale/de/LC_MESSAGES/django.po` | Non-fuzzy Filter msgid | VERIFIED | Actual translated entry, source occurrence and non-obsolete status freshly checked. |
| `src/crud_views/locale/de/LC_MESSAGES/django.mo` | Compiled Filter key | VERIFIED | GNUTranslations membership assertion freshly passed. |
| `docs/reference/context_buttons.md` | Compact mode/configuration contract | VERIFIED | Real configuration examples and cross-links; test and human UAT evidence. |
| `docs/reference/action_menus.md` | Canonical precedence and never-folded rules | VERIFIED | Resolution section and filter rendering relationship match source. |
| `docs/reference/javascript.md` | Optional hooks and failure contract | VERIFIED | Documented IDs and handler ordering match production. |
| `CHANGELOG.md` | Public correction and unchanged default | VERIFIED | Unreleased Fixed entry covers modes, translation, floor impact and copied templates. |
| `tests/test1/test_label_mode_docs.py` | Executable documentation contract | VERIFIED | Fresh filter reference test passes; existing assertions preserve canonical-order/diagram coverage. |
| `docs/migrating-1.0.md` | Copied-template contract and checklist | VERIFIED | Both entry points cover modes, optional icons and stable ARIA/IDs. |
| `src/crud_views/lib/view/base.py` | Correct toolbar/row handling after review | VERIFIED | Context-only stamp preservation and list resolver remain wired to public rendering paths; fresh regressions pass. |

### Key Link Verification

Fresh `verify.key-links`: 03-01 4/4; 03-02 2/2, both exit 0. Pattern results were corroborated by reading both ends.

| From | To | Via | Status | Details |
|---|---|---|---|---|
| FilterContextButton | CrudView resolver | `cv_get_action_label_mode("context", self.key, self)` | WIRED | No target default; current wrapper preserves context stamp and re-resolves row mode. |
| Filter template | Template tags/class and icon registries | `cv_button_class`, `cv_icon_class`, `cv_icon` | WIRED | Tags delegate to real registry accessors; fresh matrix verifies changed classes/placement reach markup. |
| Filter template | `list.filter.js` | Toggle/panel IDs, ARIA and optional icon hooks | WIRED | Exact selectors match; label branch emits no hooks and still toggles. |
| `list.filter.js` | ListViewTableFilterMixin | Existing path/CSRF JSON POST and session-backed GET | WIRED | Handler sends boolean state; mixin stores in SessionData and its property feeds the next render; fresh tracer proves round trip. |
| Context-button docs | Action-menu docs | Canonical resolution anchor | WIRED | Both link and target section read. |
| JavaScript docs | Production filter handler | Stable IDs and behavior contract | WIRED | Source ordering and documented error behavior agree; fresh invariant tests pass. |

### Data-Flow Trace (Level 4)

| Rendered value | Actual source | Produces real data | Status |
|---|---|---|---|
| `cv_label_mode` | View map → explicit button → selected ViewSet/settings map → lazy context floor, then validation | Distinct configured values reach actual toolbar; direct and rendered resolution agree | FLOWING |
| `cv_action_label` | Per-call gettext seed → optional label template | Distinct sentinels/custom text reach contexts and rendered labels | FLOWING |
| `cv_filter_expanded` | SessionData via `ListViewTableFilterMixin.cv_filter_expanded` | Fresh POST→GET changes rendered ARIA state | FLOWING |
| Host/element icon values and mode classes | Icon and button-class registries via template tags | Fresh matrix changes classes/placement and verifies output | FLOWING |
| POST boolean | Current ARIA state (panel fallback when absent), inverted after accepted collapse | Fresh per-click exact request assertions | FLOWING |

No disconnected dynamic values, hollow props or output stubs were found. This component's real sources are configuration, translation and session state; it does not require a new database query.

### Behavioral Spot-Checks

All commands below ran in this verifier's own process against the current checkout. No server, install or broad suite was started. Python tests use their isolated test DB.

| Behavior | Exact command | Result | Status |
|---|---|---|---|
| Toolbar/row isolation, single resolution, malformed-mode validation | `.venv/bin/pytest tests/test1/test_filter_toggle_label_mode.py::test_filter_context_mode_does_not_override_row_mode tests/test1/test_filter_toggle_label_mode.py::test_filter_toolbar_resolves_mode_once 'tests/test1/test_filter_toggle_label_mode.py::test_filter_malformed_resolved_mode[label-text-settings]' -q` | 7 passed, 1.42s | PASS |
| Real persistence, lazy floor/restoration, raw bytes, golden | `.venv/bin/pytest tests/test1/test_filter_toggle_label_mode.py::test_filter_both_tracer tests/test1/test_filter_toggle_label_mode.py::test_filter_live_floor tests/test1/test_filter_toggle_label_mode.py::test_filter_raw_default_bytes tests/test1/test_action_menus_golden.py::test_toolbar_list_with_filter -q` | 5 passed, 0.86s | PASS |
| Translation and documentation contract | `.venv/bin/pytest tests/test1/test_i18n.py::test_filter_catalog_entry tests/test1/test_i18n.py::test_filter_gettext_at_render_time tests/test1/test_i18n.py::test_filter_german_render tests/test1/test_label_mode_docs.py::test_filter_toggle_reference_contract -q` | 6 passed, 0.95s | PASS |
| Mode/placement, fallback, precedence, direct key, no-target default, visibility and escaping | `.venv/bin/pytest tests/test1/test_filter_toggle_label_mode.py::test_filter_mode_placement_matrix tests/test1/test_filter_toggle_label_mode.py::test_filter_host_slot_fallback tests/test1/test_filter_toggle_label_mode.py::test_filter_mode_resolution tests/test1/test_filter_toggle_label_mode.py::test_filter_declared_key_and_direct_button tests/test1/test_filter_toggle_label_mode.py::test_filter_ignores_list_singular_default tests/test1/test_filter_toggle_label_mode.py::test_filter_visibility tests/test1/test_filter_toggle_label_mode.py::test_filter_label_escaping tests/test1/test_filter_toggle_label_mode.py::test_filter_direct_mode_fallback -q` | 63 passed, 2.43s | PASS |
| Two-click labels, collapse ordering, errors and out-of-order promises | `./node_modules/.bin/vitest run tests/js/list.filter.test.js -t 'keeps the label\|collapses before\|never rolls back\|changes nothing on a label-only\|keeps a successful label-only\|loads harmlessly'` | 22 passed, 14 not selected; 603ms | PASS |
| Prior golden and production handler unchanged | `git diff 3a51f81 --stat -- tests/test1/golden/ src/crud_views/static/crud_views/js/list.filter.js` | Empty output | PASS |

Fresh targeted total: **81 Python + 22 JavaScript cases passed**. The JS filter's 14 unselected cases are selection exclusions, not disabled tests.

Additional evidence supplied by the orchestrator, not rerun here: current-fix focused modules **281 passed**, prior-phase regression gate **896 passed**, changed-file Ruff checks passed. The pre-fix full-suite results in review-fix history are historical and are not represented as a full-suite run on this HEAD. Original global `ruff format --check` failed on pre-existing planning Markdown; that recorded limitation remains explicit and is not relabeled green.

### Probe Execution

Not applicable. Neither PLAN declares an executable probe; `scripts/` contains screenshot/server-wait helpers, not `tests/probe-*.sh` probes. Named tests above supply behavioral evidence.

### Requirements Coverage

Both plans declare all four requirements. REQUIREMENTS.md maps exactly these four IDs to Phase 3; no orphaned requirement was found.

| Requirement | Source plans | Description | Status | Evidence |
|---|---|---|---|---|
| FILT-01 | 03-01, 03-02 | Configured both/label modes and byte-identical default | SATISFIED | SC-1; fresh tracer/matrix/resolution/raw/golden checks; current docs and completed UAT |
| FILT-02 | 03-01, 03-02 | Icon-less toggle updates ARIA and persists | SATISFIED | SC-2; fresh label-only JS, actual session round trip, completed browser UAT |
| FILT-03 | 03-01, 03-02 | Constant text; only state/icon changes | SATISFIED | SC-3; fresh node-identity/text/ordering/error/concurrency tests |
| FILT-04 | 03-01, 03-02 | Translated Filter msgid and German catalog | SATISFIED | SC-4; fresh PO/MO membership, sentinel and three German renders |

### Decision Coverage

All trackable CONTEXT.md decisions are honored by shipped artifacts.

Fresh owner query `check.decision-coverage-verify`: **11/11**, `not_honored: []`, exit 0. This advisory coverage check does not replace source or behavioral verification.

### Test Quality Audit

| Test file | Linked requirement | Active evidence | Disabled/skipped coverage | Circular | Assertion strength | Verdict |
|---|---|---|---|---|---|---|
| `test_filter_toggle_label_mode.py` | FILT-01..03 | Named render/integration/review regressions ran | None found | No; raw oracle is pre-change output, not regenerated expected output | Exact values and state transitions | PASS |
| `tests/js/list.filter.test.js` | FILT-02..03 | 22 selected cases passed | 14 selection exclusions; no disabled declarations | No | Call ordering, exact requests, node identity and promise settlement | PASS |
| `test_i18n.py` filter cases | FILT-04 | All 5 filter cases passed | `importorskip("polib")` exists, but dependency present and catalog case executed | No | Explicit catalog membership, distinct sentinel and active language | PASS |
| `test_label_mode_docs.py` | FILT-01..04 documentation | Named filter contract passed | No disabled declarations found | No | Text/link values, supplemented by completed editorial UAT | PASS |

No disabled-only requirement, circular expected-output generator or insufficient assertion blocker was found. JS fixtures manually represent markup, but Python independently verifies those server-rendered structures and completed browser UAT covers their integration.

Disconfirmation checks specifically examined: target-default leakage into the filter; context-mode leakage into list rows; German spelling masking a missing catalog key; adapter refusal/rejection and response reordering. Current source and named tests refute those failure hypotheses. No partially met requirement or uncovered in-contract failure path was found.

### Anti-Patterns Found

Scanned phase source, tests and documentation for unresolved debt markers, placeholder/empty implementations, disabled tests and circular fixture writes. Empty visibility contexts are deliberate access gates; empty icon collections in label mode are intentional and behaviorally exercised. The JS rejection no-op deliberately preserves successful local state.

| File/location | Pattern | Severity | Impact |
|---|---|---|---|
| Filter template | Historical IN-01: repeated mode branch expressions | INFO | Readability only; matrix and raw-compatibility tests cover current branches. |
| `CHANGELOG.md:156-159` | Historical IN-02: compressed sentence may read ambiguously | INFO | Editorial issue remains recorded; UAT item 3 passed and reference examples are explicit. |
| `test_i18n.py:110` | Historical IN-03: private gettext catalog membership | INFO | Tests actual compiled key existence; no production private-API use added. |
| Context-button import surface | Historical IN-04: FilterContextButton not re-exported with siblings | INFO | Documentation uses the real `crud_views.lib.view.buttons` import; no missing promised API. |
| Historical changelog entries | Mentions of removed TODO/placeholder text | INFO | Historical release prose, not unresolved implementation debt. |

No BLOCKER or WARNING remains from implementation verification. WR-01, WR-02 and CR-01 are fixed and freshly exercised. Existing UI review is **23/24**, with no blocker; reuse was explicitly selected by the user. Its label-only visual-state affordance observation was included in the completed browser UAT.

### Advisory (New Scope, Unevidenced)

None.

### Human Verification Required

None outstanding. `03-UAT.md` records **4 passed, 0 issues, 0 pending, 0 skipped, 0 blocked**:

1. Compact documentation contract against the decisions.
2. Optional-icon prose against fixtures.
3. Fixed release note and both migration entry points.
4. Browser icon/both/label modes, constant label, persistence and German rendering.

The three PLAN-deferred documentation checks match UAT items 1–3; the prior verifier's visual/browser check matches item 4. These completed checks are not being requested again. The later row-mode correction changes only Python context precedence and its regression tests, leaving the template, JS, translation and reviewed visual contract unchanged.

### Other Phase Gates

- Current independent code review: clean; fixed review findings and four historical INFO entries remain auditable.
- Security register: ASVS level 1, six threats closed, zero open; current fixes add no new rendering/POST boundary.
- Validation artifact: validated, Nyquist compliant, zero recorded gaps.
- Existing UI review: 23/24, reused by explicit user decision; no new visual audit performed.

These artifact statuses are supporting gate records, not substitutes for the source and fresh tests above.

### Gaps Summary

No implementation gap, unverified behavior, unresolved prohibition or pending human item remains. No later-phase deferral was needed; the roadmap was checked and no Phase 3 obligation was moved elsewhere. The goal is achieved at the verified HEAD. The covered-input fingerprint was generated by `verification.fingerprint` and copied unchanged; it includes the review-modified `base.py`, implementation, regression evidence and completed UAT, while excluding mutable global planning state.

---

_Verified: 2026-10-26T16:56:17Z_
_Verifier: the agent (gsd-verifier)_
