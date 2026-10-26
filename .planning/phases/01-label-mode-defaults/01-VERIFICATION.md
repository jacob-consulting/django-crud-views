---
phase: 01-label-mode-defaults
verified: 2026-10-26T11:18:45Z
status: human_needed
score: 35/35 must-haves verified
covered_files: [".planning/phases/01-label-mode-defaults/01-01-PLAN.md",".planning/phases/01-label-mode-defaults/01-01-SUMMARY.md",".planning/phases/01-label-mode-defaults/01-02-PLAN.md",".planning/phases/01-label-mode-defaults/01-02-SUMMARY.md",".planning/phases/01-label-mode-defaults/01-03-PLAN.md",".planning/phases/01-label-mode-defaults/01-03-SUMMARY.md",".planning/phases/01-label-mode-defaults/01-04-PLAN.md",".planning/phases/01-label-mode-defaults/01-04-SUMMARY.md",".planning/phases/01-label-mode-defaults/01-05-PLAN.md",".planning/phases/01-label-mode-defaults/01-05-SUMMARY.md","CHANGELOG.md","docs/migrating-1.0.md","docs/reference/action_menus.md","docs/reference/buttons.md","docs/reference/card-list-view.md","docs/reference/context_buttons.md","docs/reference/settings.md","src/crud_views/lib/settings.py","src/crud_views/lib/view/action_menu.py","src/crud_views/lib/view/base.py","src/crud_views/lib/view/button_data.py","src/crud_views/lib/view/buttons.py","src/crud_views/lib/view/card.py","src/crud_views/lib/view/label_mode.py","src/crud_views/lib/views/card.py","src/crud_views/templates/crud_views/tags/button/action.html","src/crud_views/templates/crud_views/tags/card.html","src/crud_views/templatetags/crud_views.py","tests/test1/conftest.py","tests/test1/test_action_label_mode_config.py","tests/test1/test_action_label_mode_render.py","tests/test1/test_action_menus_golden.py","tests/test1/test_button_data.py","tests/test1/test_button_leaves.py","tests/test1/test_card_label_mode_render.py","tests/test1/test_card_label_modes.py","tests/test1/test_context_action_label_mode.py","tests/test1/test_context_button_label_mode.py","tests/test1/test_import_safety.py","tests/test1/test_label_mode.py","tests/test1/test_label_mode_docs.py"]
covered_digest: "v3:sha256:c4516ecd39bbebaaf8259898aea89551ba3f80969d29b588248abd7722090ce1"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 26/28
  gaps_closed:
    - "CR-01: With no configuration, explicit instance card modes preserve pre-phase rendered output."
    - "CR-01: CardAction and no_label precedence, explicit instance choice, then card floor."
  gaps_remaining: []
  regressions: []
deferred:
  - truth: "SC-1 every unmapped toolbar button includes the custom filter toggle, which still renders icon-only."
    addressed_in: "Phase 3"
    evidence: "ROADMAP Phase 3: the filter toggle honours icon / both / label; FILT-01 covers filter both/label and unchanged icon output."
decision_coverage:
  honored: 26
  total: 26
  not_honored: []
flagged_prohibitions:
  - statement: "Label-mode defaults MUST NOT become theme-owned policy or override explicit project/view/button choices."
    status: unverified
    flag: "unverified-prohibition — human review recommended"
    judgment: "NON-AUTHORITATIVE: source and rendered regressions support satisfaction; explicit human disposition remains required."
  - statement: "Unchanged rendered output MUST NOT be presented as absence of a breaking Python attribute change."
    status: unverified
    flag: "unverified-prohibition — human review recommended"
    judgment: "NON-AUTHORITATIVE: Breaking/migration text explicitly discloses the change; explicit human disposition remains required."
flagged_assumptions:
  - id: EDGE-LMOD-02-unclassified
    status: unresolved
    subject: "Consumer-set completeness"
  - id: EDGE-LMOD-04-unclassified
    status: unresolved
    subject: "Lifecycle-case completeness"
human_verification:
  - test: "Confirm operator control and theme independence"
    expected: "Accept or reject the prohibition that label-mode defaults remain project/view/button policy and do not override explicit choices."
    why_human: "Descriptor-less product-intent prohibition; the precedence tests prove concrete behaviors, not the broader policy. LLM judgment is non-authoritative."
  - test: "Confirm migration transparency"
    expected: "Accept or reject that CHANGELOG Breaking and migrating-1.0.md clearly disclose raw None versus resolved both and class-resolver versus instance/per-action semantics."
    why_human: "Descriptor-less product-intent prohibition; text-presence tests cannot certify whether the disclosure communicates the breaking change adequately."
  - test: "Disposition EDGE-LMOD-02 consumer completeness"
    expected: "Confirm the three declared consumers cover Phase 1, with filter toggle explicitly deferred to Phase 3 and form location to Phase 6, or name a missing in-scope consumer."
    why_human: "Source scan supports the enumerated set; the source audit deliberately leaves completeness unclassified and unresolved."
  - test: "Disposition EDGE-LMOD-04 lifecycle completeness"
    expected: "Confirm absent settings, nested override entry/exit, same-instance fallback, instance clearing and subsequent requests cover the intended lifecycle, or name an additional required case."
    why_human: "Passing transition tests prove those cases; the source audit deliberately leaves broader lifecycle completeness unclassified and unresolved."
---

# Phase 1: Label-mode defaults Verification Report

**Phase Goal:** A project sets the label-mode default for each location in one place, and every location reads that floor from a single accessor. With no configuration, output is unchanged.
**Verified:** 2026-10-26T11:18:45Z
**Status:** human_needed
**Re-verification:** Yes — after Plan 01-05 closes CR-01.
**Branch:** feat/label-mode-defaults

## Goal Achievement

Both carried-forward code gaps are closed. The rendering method now reads an own instance override before its class-level fallback, preserves action/no_label precedence and subclass hooks, and reads the live floor for an own None. Independent named behavioral tests pass for the actual rendered path, including settings restoration and request isolation. No implementation blocker or regression was found.

This is **not a passed verdict**: two descriptor-less product-intent prohibitions and two explicitly unresolved completeness assumptions need human disposition. Automated coverage and the LLM's favorable judgment do not silently certify them. The filter toggle remains the specifically documented Phase 3 deferral.

The previous 28 truths are preserved below; previously passing items received source/existence regression checks, while both failed truths and seven Plan 01-05 refinements received focused re-verification. Historical results are identified as retained evidence, not claimed as fresh runs. No override exists or was invented.

### Observable Truths


**Roadmap contract and phase goal**

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| R1 | SC-1: `{"context": "both"}` makes every unmapped toolbar button icon + text; rows/cards unchanged; W292 stops firing for those keys | ✓ VERIFIED (filter toggle deferred to Phase 3) | `base.py:322` `target_default or default_label_mode("context")`. Tests passed: `test_context_floor_renders_unmapped_toolbar` (list/card/create/detail/update routes), `test_context_floor_does_not_change_rows_or_cards`, `test_w292_silent_with_context_floor`, `test_w292_explicit_icon_still_warns_with_floor` |
| R2 | SC-2: `{"card": "label"}` restores the 0.29 card look without touching a view; explicit `both` on a view still wins | ✓ VERIFIED | Fresh `test_card_floor_renders_label_only` and six `test_card_instance_mode_precedence` cases; class-level bypass retained in `test_card_explicit_mode_bypasses_floor` |
| R3 | SC-3: `override_settings` changes the resolved default; an invalid mode outside strict mode logs and falls back | ✓ VERIFIED | Independent probe: absent → `{context: icon, list: icon, card: both}`; `{"card": "label"}` → card `label`; restores `both` on exit; `{"context": "Both"}` non-strict → `icon` twice with exactly one WARNING; strict → ValueError |
| R4 | SC-4: E108 reports unknown location key or invalid mode; valid keys come from LOCATIONS | ✓ VERIFIED | `settings.py:142-172` imports `button_data.LOCATIONS` lazily. Probe: `{"cotext":…, "card":"nope", "list":"label"}` → 2 Errors (level 40) in insertion order; `None` → 1; absent → 0. `test_e108_uses_button_locations` monkeypatches LOCATIONS |
| R5 | SC-5: literal grep empty; goldens byte-identical; docs state per-key merge vs whole-dict replacement | ✓ VERIFIED | `grep -n '"both" if card\|or "icon"\|get(key, "icon")' src/crud_views/lib/view/*.py` exits 1 (also exits 1 across all of src/). `git diff 06a8b81..HEAD -- tests/test1/golden src/crud_views/templates examples` is empty, as is porcelain status. `settings.md#label-mode-configuration` table rows 90-96 + "Existing per-action maps keep whole-dict replacement semantics" |
| G1 | Every location reads the floor from a single accessor | ✓ VERIFIED | `default_label_mode` called at `button_data.py:87/93`, `base.py:322/328`, `views/card.py:121`; no other label-mode floor literal in `src/` (extension packages have no label_mode code) |
| G2 | With no configuration, output is unchanged, including explicit card modes already set on a view | ✓ VERIFIED | CR-01 closed: `views/card.py:53-58` reads own instance value; fresh `test_card_initkwargs_label_without_setting` and absent-setting request-hook cases assert real label-only DOM and unchanged control |

**Plan must-haves (deduplicated against the roadmap rows above)**

| # | Truth (plan) | Status | Evidence |
|---|-------|--------|----------|
| P1-1 | Raw cv_button context renders the configured floor through the real leaf (01-01) | ✓ VERIFIED | `test_defaults_setting_reaches_button_leaf` passed |
| P1-2 | Override replaces only its entry; insertion order irrelevant (01-01) | ✓ VERIFIED | `test_default_label_mode_merge`, `test_default_label_mode_order_independent` |
| P1-3 | Absent / {} / singleton resolve correctly; explicit None invalid (01-01) | ✓ VERIFIED | `label_mode.py:97-101` `_UNSET` sentinel vs `isinstance(raw, dict)`; tests + probe |
| P1-4 | Invalid setting values raise strict / warn once otherwise; falsey stamps keep unset behavior (01-01) | ✓ VERIFIED | `button_data.py:85-94`; `test_default_label_mode_invalid_setting`, `test_falsey_stamped_mode_uses_floor` |
| P1-5 | Exact case-sensitive modes; unhashable values do not crash (01-01) | ✓ VERIFIED | dedup key `repr(value)` (`label_mode.py:74`); `test_default_label_mode_exact_strings` |
| P1-6 | E108: absent/{}/valid → none; non-dict → one; one Error per bad entry (01-01) | ✓ VERIFIED | `if/elif` per entry at `settings.py:157-163`; probe + `test_e108_*` |
| P1-7 | E108 insertion order, sorted allowed values, key/value repr (01-01) | ✓ VERIFIED | probe output; `test_e108_entry_order` |
| P2-2 | Context floor consulted only after view map, button, whole-layer map, target default; list floor only for unnamed keys (01-02) | ✓ VERIFIED | `base.py:312-328`, membership branch for list; `test_context_floor_preserves_precedence`, `test_list_floor_used_only_for_unmapped_key`, `test_explicit_*_bypasses_invalid_floor` |
| P2-3 | `list=label` renders unmapped rows text-only; mapped keep modes; context independent (01-02) | ✓ VERIFIED | `test_list_floor_renders_unmapped_rows` |
| P2-4 | Invalid strict floor → E108 through check_viewsets, not a W292 traceback (01-02) | ✓ VERIFIED | `buttons.py:407-411` narrow try/except; `test_invalid_floor_check_viewsets_returns_e108` |
| P3-2 | Card chain: CardAction.label_mode → no_label → non-None view attribute → card floor (01-03) | ✓ VERIFIED | Fresh six-case `test_card_instance_mode_precedence` matrix proves action/no_label priority and explicit instance choice over conflicting/invalid strict floor |
| P3-3 | `None` valid; empty string → E210; empty action list renders nothing (01-03) | ✓ VERIFIED | `views/card.py:122-123` guarded E210; `test_good_values_yield_no_check`, `test_empty_card_actions_with_floor` |
| P3-4 | Only exact modes valid on the card attribute; lookalikes → E210 (01-03) | ✓ VERIFIED | `test_card_attribute_exact_modes` |
| P3-5 | Raw attribute None; resolver returns `both` unconfigured; goldens identical (01-03) | ✓ VERIFIED | `test_default_attribute_is_none_and_resolves_both`; golden diff empty |
| P3-6 | Release/migration notes disclose the attribute break; setting-first recipe (01-03) | ✓ VERIFIED | CHANGELOG Breaking and migration now distinguish class resolver from effective per-action stamp; fresh `test_card_migration_contract` passes |
| P4-1 | Documented card setting example renders label-only through the real tag (01-04) | ✓ VERIFIED | `test_documented_card_floor_renders_label_only` (ast.literal_eval, no exec) |
| P4-2 | One settings table distinguishes merge vs whole-layer replacement (01-04) | ✓ VERIFIED | settings.md:82-98; `test_label_mode_configuration_table` |
| P4-3 | Canonical context/list/card resolution sections in action_menus.md; secondary pages link (01-04) | ✓ VERIFIED | `test_canonical_label_mode_resolution_sections`, `test_label_mode_reference_links_and_diagram` |
| P4-4 | Public accessor, constant, setting, resolver documented with lazy/strict/E108 behavior (01-04) | ✓ VERIFIED | settings.md; docs tests passed; mkdocs `--strict` builds clean |
| P4-5 | Stable context names kept; PROJECT.md records no_label removal outside this phase (01-04) | ✓ VERIFIED | one-off PROJECT.md grep: 1 / 1 / 1 matching rows |
| P4-6 | Full Python, JS, strict docs, ruff gates pass; templates/goldens/examples unchanged (01-04) | ✓ VERIFIED (retained verification evidence) | Prior independent full run: 3056 passed/1 skipped and 126 JS passed; no implementation change outside eight 01-05 files. Current executor reports 3076/1 and 126; independent code/UI reviews add 51/96 passes. This verifier did not rerun full suites; fresh protected-path diff/status and one card golden pass |


**Additional 01-05 acceptance refinements** (seven explicit plan truths; retained alongside the original 28 so the gap-closure contract is auditable)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| P5-1 | Absent setting: as_view(label) and request-time assignment render visible labels with zero icons | ✓ VERIFIED | Fresh initkwargs test, precedence matrix and request-hook matrix; actual TemplateResponse rendered |
| P5-2 | Action mode/no_label precede instance; explicit both beats label floor and bypasses invalid strict floor | ✓ VERIFIED | Fresh six-case precedence matrix checks detail/update/delete/up DOM, hidden labels and no DeprecationWarning |
| P5-3 | Own instance None uses floor despite class mode; no own mode preserves resolver hooks and super() | ✓ VERIFIED | Fresh own-None (2), hook-render (2) and superclass compatibility (1) cases |
| P5-4 | Public zero-argument classmethod, class defaults, nested override restoration, E210, exact modes and empty actions remain valid | ✓ VERIFIED | Signature/code at card.py:113-130; fresh superclass/nested tests; existing exact-mode/E210/empty-action tests inspected and preserved; independent reviewer ran all 45 card cases |
| P5-5 | Changing/clearing request mode never mutates class or later request; fallback reads current settings | ✓ VERIFIED | Fresh six request-hook cases and two same-instance reset/nested-settings cases assert transitions and later request output |
| P5-6 | Docs distinguish class resolver/effective per-action stamp and preserve None disclosure/setting-first recipe | ✓ VERIFIED | Four docs diffs inspected; fresh migration contract test; independent docs suite six cases passed |
| P5-7 | Unconfigured card/menu/accessibility goldens unchanged; permission/method behavior retained | ✓ VERIFIED | Fresh legacy card golden and granted/denied child cases; permission/POST branches unchanged; existing disabled/POST/menu tests inspected, independently run by reviewers |

**Score:** 35/35 implementation truths verified (0 present, behavior-unverified). Four review items below remain UNCERTAIN (WARNING); they are separate from the positive implementation-truth score and prevent a passed verdict.

### Prohibitions and Flagged Assumptions

| Item | Status | Evidence and limit |
|---|---|---|
| Operator/theme-control prohibition | UNCERTAIN — WARNING | NON-AUTHORITATIVE LLM judgment: satisfied by setting ownership, explicit precedence and CR-01 repair; **unverified-prohibition — human review recommended** |
| Migration-transparency prohibition | UNCERTAIN — WARNING | NON-AUTHORITATIVE LLM judgment: explicit Breaking/migration notice and accurate class/instance guidance; **unverified-prohibition — human review recommended** |
| EDGE-LMOD-02 consumer completeness | UNCERTAIN — WARNING | Source scan finds the three declared consumers; no consumer outside them was found. Broader completeness remains an explicit planning assumption |
| EDGE-LMOD-04 lifecycle completeness | UNCERTAIN — WARNING | Named tests exercise override restoration, same-instance clearing and later requests. Broader lifecycle completeness remains an explicit planning assumption |

The prohibitions have no test/judgment descriptor in the plans and no wired enforcement certification. They retain their unresolved, judgment-review treatment. No backstop-tagged truth or deferred human-check XML block was found.

### Deferred Items

| Item | Addressed In | Evidence |
|---|---|---|
| Filter toggle remains icon-only under context=both | Phase 3 | ROADMAP Phase 3 goal and FILT-01 explicitly introduce filter icon/both/label behavior; no expansion of this deferral |
| Form location | Phase 6 (scope boundary, not a newly found gap) | FORM-02/FORM-10 add the form location and its floor |

Full roadmap analysis found no other later-phase deferral relevant to the repaired truths.

### Required Artifacts

All five artifact-verifier invocations exited 0: plan counts 6/6, 4/4, 5/5, 4/4 and 5/5 (24 declarations, with shared paths repeated). Presence checks were supplemented by substantive source/wiring inspection.

| Artifact | Expected | Status | Details |
|---|---|---|---|
| src/crud_views/lib/view/label_mode.py | Immutable defaults, lazy accessor, strict/warn-once recovery | VERIFIED | MappingProxyType; raw settings getter per call; bounded fallback; imported and called by all three consumer paths |
| src/crud_views/lib/view/button_data.py | Leaf floor and stamp validation | VERIFIED | Lines 85–94 call accessor/recovery; cv_button calls the normalizer and renders its returned data |
| src/crud_views/lib/settings.py | E108 from raw setting and LOCATIONS | VERIFIED | Deferred imports; one message per invalid entry; wired into settings checks |
| src/crud_views/lib/view/base.py; buttons.py | Context/list precedence and safe W292 checks | VERIFIED | Final fallbacks at base.py:322/328; narrow resolver exception boundary remains |
| src/crud_views/lib/views/card.py | Instance-aware stamping and preserved class API | VERIFIED | Lines 49–58 resolve; lines 74/92 stamp both branches; classmethod 113–121 retains zero-argument API; no class mutation |
| tests/test1/test_card_label_mode_render.py; test_card_label_modes.py | Rendered receiver/precedence/isolation/hook checks | VERIFIED | 20 new cases freshly run; helper calls actual as_view, renders TemplateResponse and asserts exact action DOM |
| tests/test1/test_button_leaves.py; conftest.py; test_import_safety.py | Leaf tracer, warning isolation, deferred import boundary | VERIFIED (regression check) | Existing substantive tests/fixture retained; no edits in gap round |
| tests/test1/test_context_action_label_mode.py; test_action_label_mode_render.py | Toolbar/row rendering and precedence | VERIFIED (regression check) | Existing real HTTP/DOM tests retained; no edits in gap round |
| docs/reference/settings.md; action_menus.md; card-list-view.md; docs/migrating-1.0.md; CHANGELOG.md | Single configuration table, canonical order, accurate migration | VERIFIED | Four gap-round docs changes match actual class/instance semantics; None break and setting-first recipe preserved |
| tests/test1/test_label_mode_docs.py; .planning/PROJECT.md | Executable docs contract and decision handoff | VERIFIED | Fresh migration contract pass; decision gate 26/26; no permanent test depends on planning state |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| button_data.py | label_mode.py | default_label_mode/_invalid_label_mode | WIRED | Imported, called, returned mode emitted in normalized data |
| settings.py | button_data.py/label_mode.py | Deferred LOCATIONS/raw defaults | WIRED | Runtime checks use shared location set and live configuration |
| base.py | label_mode.py | Final context/list fallbacks | WIRED | Higher explicit layers return before accessor |
| buttons.py | base.py | cv_get_action_label_mode | WIRED | W292 resolves effective mode, guards ValueError |
| Django as_view/request hooks | views/card.py | Own instance value to cv_get_card_action_data | WIRED — manual/runtime proof | Initkwargs and setup/dispatch/get_queryset named tests pass |
| views/card.py | label_mode.py | Own None/class default reads card floor | WIRED | Lazy reads only when needed, no cache/class write |
| views/card.py | card group/tag → cv_button → action.html | cv_label_mode stamping | WIRED | Ordinary and child data carry value; rendered tests inspect resulting visible/hidden labels and icon counts |
| Reference/docs test links | Canonical settings/action sections | Anchors plus parsed example | WIRED | Existing link tests and current section contents retained |

Automated key-link counts: 2/2, 2/2, 2/2, 3/3, then 2/3. The last invocation exited 1 because Plan 01-05's first `from` is prose (`AuthorCardListView.as_view initkwargs and request-time instance assignments`), not a relative file path. This is a plan metadata limitation, **not a missing implementation link**: the actual link is directly proven by the fresh request/render tests and source trace above. The remaining eleven declared links passed the automated pattern check.

### Data-Flow Trace (Level 4)

| Artifact | Data variable | Real source | Produces real data | Status |
|---|---|---|---|---|
| Toolbar/list action leaf | cv_label_mode | Explicit action/view/map choices → live Django setting → immutable package floor | Yes | FLOWING |
| Card action leaf | cv_label_mode | CardAction → own request-instance value → subclass/class resolver → live card floor | Yes | FLOWING |
| Card action labels/URLs/access | cv_label, cv_url, cv_access | Real model object, target ViewSet/view, user permission checks | Yes | FLOWING |

The declared package floor is intentional configuration, not a placeholder data source. Empty action containers and permission-hidden returns are real branches, not stubs.

### Behavioral Spot-Checks

All commands below were run by this verifier in its own process. Each selected test function completed in under two seconds; parameterized cases are one named-test invocation. Tests use isolated Django test state; no application server or external service was started.

| Behavior | Command (prefix: .venv/bin/pytest) | Result | Status |
|---|---|---|---|
| Genuine absent-setting initkwargs regression | tests/test1/test_card_label_mode_render.py::test_card_initkwargs_label_without_setting -q | 1 passed, 0.41s | PASS |
| Action/instance/floor precedence incl. strict malformed floor | tests/test1/test_card_label_mode_render.py::test_card_instance_mode_precedence -q | 6 passed, 1.22s | PASS |
| Three request hooks, next-request isolation | tests/test1/test_card_label_mode_render.py::test_card_request_assignment_is_local -q | 6 passed, 1.18s | PASS |
| Own None, nested settings restoration, clearing/reuse | tests/test1/test_card_label_mode_render.py::test_card_instance_none_uses_floor -q | 2 passed, 0.62s | PASS |
| Classmethod/instance resolver hooks | tests/test1/test_card_label_mode_render.py::test_card_resolver_hook_reaches_render -q | 2 passed, 0.54s | PASS |
| Child action and permission preservation | tests/test1/test_card_label_mode_render.py::test_card_instance_mode_reaches_child_action -q | 2 passed, 0.54s | PASS |
| Public class API, super(), nested restoration | tests/test1/test_card_label_modes.py::test_card_resolver_subclass_super_compatibility -q | 1 passed, 0.04s | PASS |
| Current migration contract | tests/test1/test_label_mode_docs.py::test_card_migration_contract -q | 1 passed, 0.03s | PASS |
| Setting-only card appearance | tests/test1/test_card_label_mode_render.py::test_card_floor_renders_label_only -q | 1 passed, 0.40s | PASS |
| Legacy card golden | tests/test1/test_action_menus_golden.py::test_cards_author_full -q | 1 passed, 0.41s; CV_UPDATE_GOLDEN checked not 1 | PASS |
| No obsolete fallback literals | rg for the three roadmap patterns in src/crud_views/lib/view | No matches, exit 1 | PASS |
| Protected outputs unchanged | git diff --stat 06a8b81 -- tests/test1/golden src/crud_views/templates examples; git status --porcelain on same paths | Both empty | PASS |

Fresh total: **23 cases across ten named test functions**. No full-suite rerun. Prior full-suite results remain historical; the current independent code review reports 51 focused passes, UI review 96, and executor broader gates 3076 Python/1 existing skip plus 126 JS. Those reports corroborate coverage; direct source and fresh behavioral tests establish gap closure.

### Probe Execution

No phase-declared shell probe, probe script path, or conventional scripts/*/tests/probe-*.sh entry was found. Plan references to probe-derived assumptions are planning evidence, not runnable probe claims. No SUMMARY PASS-marker claim substitutes for execution.

### Requirements Coverage

| Requirement | Source plans | Description | Status | Evidence |
|---|---|---|---|---|
| LMOD-01 | 01-01/02/04 | Per-key merge; documented whole-layer distinction | SATISFIED | Lazy accessor and canonical settings table; prior merge/order tests retained |
| LMOD-02 | 01-01/02/03/04/05 | Single accessor in all declared consumers; no obsolete literals | SATISFIED | Fresh source scan and card runtime path; completeness assumption remains separately flagged |
| LMOD-03 | 01-03/04/05 | None default; explicit both wins; setting restores label look | SATISFIED | Both CR-01 gaps closed by fresh rendered precedence/no-setting tests |
| LMOD-04 | 01-01/02/03/04/05 | Call-time setting and override_settings | SATISFIED | Fresh same-instance nested override/restore and classmethod tests; broader lifecycle assumption remains separately flagged |
| LMOD-05 | 01-01/02/03/04 | Strict/non-strict invalid-mode recovery | SATISFIED | Source regression check; retained prior behavioral evidence for warn-once/fallback |
| LMOD-06 | 01-01/02/04 | E108 invalid location/mode, keys from LOCATIONS | SATISFIED | Deferred import and raw-setting iteration inspected; retained prior E108 behavioral evidence |

All six Phase 1 IDs are claimed by plans; no orphaned requirement. REQUIREMENTS.md still tracks the phase as Gaps Found pending orchestration; this verifier owns only this report and has not altered project tracking.

### Decision Coverage

All trackable CONTEXT.md decisions are honored by shipped artifacts.

The read-only decision gate returned **26/26**, no not_honored entries, exit 0. It is advisory and does not certify the four unresolved review items.

### Test Quality Audit

| Test files | Linked requirements | Active | Skipped | Circular | Strongest assertion | Verdict |
|---|---|---|---|---|---|---|
| Card render/mode modules | LMOD-02/03/04 | New 20 cases freshly passed; existing contracts retained | 0 | No | Real rendered values plus multi-request/settings transitions | Sufficient |
| Label-mode/action config/context/list/button leaf/data modules | LMOD-01–06 | Existing requirement tests retained | 0 | No | Exact values, log counts, E108 and actual DOM | Sufficient (regression check) |
| Import-safety module | LMOD-04/06 | Existing tests retained | 0 | No | Fresh subprocess boundary assertions | Sufficient; temp app writes create inputs |
| Docs contract module | LMOD-01–06 | Six cases present; migration case freshly passed | 0 | No | Parsed data through real tag, exact contract text | Sufficient for text contract; human clarity judgment separate |
| Legacy action-menu goldens | Compatibility | One card case freshly passed | 0 | No new circular oracle | Normalized DOM comparison to pre-phase snapshots | Sufficient for supported captured cases |

Disabled requirement-test scan found no skip markers. Import-safety write_text calls build temporary input apps, not expected outputs. Golden regeneration exists behind CV_UPDATE_GOLDEN=1; it was disabled, and baseline fixtures/templates are unchanged. Their header identifies pre-container legacy captures; they prove regression consistency for those cases, not every possible project configuration. The new instance tests use independent literal expectations and control cases, so the original golden blind spot cannot hide CR-01.

### Anti-Patterns Found

No unreferenced TBD/FIXME/XXX marker, stub, orphaned artifact or disconnected data source was found. The scan's only TODO matches are historical changelog entries about removed TODOs; return nullcontext() is the existing context manager, not a null implementation.

CR-01 and its inaccurate documentation are fixed. The ten historical findings remain open in 01-REVIEW-DISPOSITION.md and are not claimed fixed by this re-verification:

| IDs | Classification | Concern | Status impact |
|---|---|---|---|
| WR-01 | Historical warning | Strict icon-less diagnostic points at incomplete knobs | Outside repaired truths |
| WR-02 | Historical warning | No startup check for icon-less card/list floor combinations | No new blocking evidence; existing runtime guard unchanged |
| WR-03 | Historical warning | 10-second subprocess timeout sensitivity | No observed failure |
| IN-01–07 | Historical info | Dedup diagnostic source; unknown-key wording; dict-only input; broad ValueError catch; dual constants; differing map lifecycle; fixture-map dependence | Preserved, no new classification or claimed repair |

Source-history check since the previous verification found only e1bd559 touching card.py among the inspected regression/advisory files. The new instance branch has deterministic passing evidence. No new failing artifact was found.

### Advisory (New Scope, Unevidenced)

None newly raised. Historical WR-01–03 and IN-01–07 remain in their disposition ledger. The malformed Plan 01-05 link source is documented above and manually resolved for verification; no implementation gap is inferred from that metadata.

### Disconfirmation and Reliance Check

- **Potential partial requirement:** SC-1's literal “every” includes the filter toggle; the specific Phase 3 goal/FILT-01 supports the retained deferral. No other missing consumer was observed.
- **Potential misleading test:** Legacy stock-view goldens never exercised as_view initkwargs. Fresh request-level tests now supply a different explicit mode than the floor and assert the actual DOM, closing that blind spot.
- **Potential uncovered/error path:** Strict-invalid-floor evaluation could defeat explicit instance choices; the fresh parameterized test covers that branch. Broader lifecycle completeness remains honestly flagged rather than inferred.
- **Reliance:** New tests provide real caller inputs (request/user/object/choice) and production establishes request-local instances. No new verified truth relies on undeclared state or incidental ordering. Historical fixture-map concern IN-07 remains advisory; targeted production-path proof does not depend on an invented map precondition.

### Human Verification Required

#### 1. Confirm operator control and theme independence

**Test:** Confirm operator control and theme independence.
**Expected:** Accept or reject the prohibition that label-mode defaults remain project/view/button policy and do not override explicit choices.
**Why human:** Descriptor-less product-intent prohibition; the precedence tests prove concrete behaviors, not the broader policy. LLM judgment is non-authoritative.

#### 2. Confirm migration transparency

**Test:** Confirm migration transparency.
**Expected:** Accept or reject that CHANGELOG Breaking and migrating-1.0.md clearly disclose raw None versus resolved both and class-resolver versus instance/per-action semantics.
**Why human:** Descriptor-less product-intent prohibition; text-presence tests cannot certify whether the disclosure communicates the breaking change adequately.

#### 3. Disposition EDGE-LMOD-02 consumer completeness

**Test:** Disposition EDGE-LMOD-02 consumer completeness.
**Expected:** Confirm the three declared consumers cover Phase 1, with filter toggle explicitly deferred to Phase 3 and form location to Phase 6, or name a missing in-scope consumer.
**Why human:** Source scan supports the enumerated set; the source audit deliberately leaves completeness unclassified and unresolved.

#### 4. Disposition EDGE-LMOD-04 lifecycle completeness

**Test:** Disposition EDGE-LMOD-04 lifecycle completeness.
**Expected:** Confirm absent settings, nested override entry/exit, same-instance fallback, instance clearing and subsequent requests cover the intended lifecycle, or name an additional required case.
**Why human:** Passing transition tests prove those cases; the source audit deliberately leaves broader lifecycle completeness unclassified and unresolved.

No browser observation is claimed. This phase changes configuration/resolution and preserves templates; the UI audit is code/markup evidence only. Optional consumer visual, keyboard and external-theme checks remain its stated limitations, not newly invented implementation blockers.

### Gaps Summary

No code gap remains; both CR-01 failed truths are verified. There are zero behavior-unverified implementation truths. The status is human_needed solely because four explicit review items remain unresolved, including **two flagged prohibitions**. Resolve those items explicitly before a passed conclusion; do not create another code gap-closure plan solely from this report. No phase-completion tracking or implementation file was changed, and no commit was made.

---

_Verified: 2026-10-26T11:18:45Z_
_Verifier: the agent (gsd-verifier)_
