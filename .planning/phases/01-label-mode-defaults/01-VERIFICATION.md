---
phase: 01-label-mode-defaults
verified: 2026-10-26T09:20:00Z
status: gaps_found
score: 26/28 must-haves verified
covered_files: [".planning/phases/01-label-mode-defaults/01-01-PLAN.md", ".planning/phases/01-label-mode-defaults/01-01-SUMMARY.md", ".planning/phases/01-label-mode-defaults/01-02-PLAN.md", ".planning/phases/01-label-mode-defaults/01-02-SUMMARY.md", ".planning/phases/01-label-mode-defaults/01-03-PLAN.md", ".planning/phases/01-label-mode-defaults/01-03-SUMMARY.md", ".planning/phases/01-label-mode-defaults/01-04-PLAN.md", ".planning/phases/01-label-mode-defaults/01-04-SUMMARY.md", "CHANGELOG.md", "docs/migrating-1.0.md", "docs/reference/action_menus.md", "docs/reference/buttons.md", "docs/reference/card-list-view.md", "docs/reference/context_buttons.md", "docs/reference/settings.md", "src/crud_views/lib/settings.py", "src/crud_views/lib/view/action_menu.py", "src/crud_views/lib/view/base.py", "src/crud_views/lib/view/button_data.py", "src/crud_views/lib/view/buttons.py", "src/crud_views/lib/view/card.py", "src/crud_views/lib/view/label_mode.py", "src/crud_views/lib/views/card.py", "tests/test1/conftest.py", "tests/test1/test_action_label_mode_config.py", "tests/test1/test_action_label_mode_render.py", "tests/test1/test_button_data.py", "tests/test1/test_button_leaves.py", "tests/test1/test_card_label_mode_render.py", "tests/test1/test_card_label_modes.py", "tests/test1/test_context_action_label_mode.py", "tests/test1/test_context_button_label_mode.py", "tests/test1/test_import_safety.py", "tests/test1/test_label_mode.py", "tests/test1/test_label_mode_docs.py"]
covered_digest: "v3:sha256:38d95f79a74551c69b70fcb535d3a21954af3fdeca03798fd3ba758f9409f7aa"
behavior_unverified: 0
overrides_applied: 0
gaps:
  - truth: "With no configuration, output is unchanged (phase goal): an explicit card label mode a project already sets on the view keeps rendering as before"
    status: failed
    reason: >-
      CR-01 confirmed. cv_get_card_action_data now calls the classmethod cv_get_card_actions_label_mode(), which reads
      cls.cv_card_actions_label_mode only. Before the phase it read self.cv_card_actions_label_mode. A mode set on the
      instance (CardListView.as_view(cv_card_actions_label_mode=...) initkwargs, or assignment in setup/dispatch/
      get_queryset) is silently dropped, and the card floor is used instead. Verifier probe with NO
      CRUD_VIEWS_LABEL_MODE_DEFAULTS configured: AuthorCardListView.as_view(cv_card_actions_label_mode="label")
      renders the detail card action with 0 icons at base 06a8b81 and with 1 icon (floor "both") at HEAD. So
      unconfigured output changes for this path.
    artifacts:
      - path: "src/crud_views/lib/views/card.py"
        issue: "line 54: label_mode = self.cv_get_card_actions_label_mode(); the classmethod at lines 109-115 reads cls.cv_card_actions_label_mode, so the instance value is ignored"
      - path: "CHANGELOG.md"
        issue: "line 53 promises 'A view that assigns the attribute keeps its value', which is false for instance-level assignment"
      - path: "tests/test1/test_card_label_mode_render.py"
        issue: "no test sets cv_card_actions_label_mode on an instance or via as_view(**initkwargs); this is why the regression passed the suite"
    missing:
      - "Read the instance in the render path: own = self.cv_card_actions_label_mode; label_mode = own if own is not None else default_label_mode('card') (or make the resolver honor the instance: an instance method, or a hybrid that works on both class and instance)"
      - "Regression tests: instance assignment and as_view(cv_card_actions_label_mode='label') render label-only with no setting; as_view(cv_card_actions_label_mode='both') beats {'card': 'label'}"
      - "Keep the CHANGELOG/migration 'keeps its value' statement true, or correct it"
  - truth: "Card chain: CardAction.label_mode wins over no_label, no_label maps to icon, a non-None view attribute wins next, then cv_get_card_actions_label_mode uses the configured card floor (01-03 must-have; also LMOD-03 'an explicit both still wins')"
    status: partial
    reason: >-
      Holds for a class-level attribute (tested: test_card_mode_precedence_with_floor, test_card_explicit_mode_bypasses_floor).
      Does not hold when the non-None view attribute is set on the view instance. It loses to the floor, so
      as_view(cv_card_actions_label_mode="both") under {"card": "label"} renders label-only. Same root cause as the gap
      above (CR-01). This also breaks the 01-01 prohibition "MUST NOT override explicit project/view/button choices".
    artifacts:
      - path: "src/crud_views/lib/views/card.py"
        issue: "classmethod resolver used from an instance render path"
    missing:
      - "Same fix as above; one change closes both gaps"
deferred:
  - truth: "SC-1 'every unmapped toolbar button renders icon + text on every page': the filter toggle (cv-key=filter / #cv-filter-toggle, custom template) still renders icon-only under {'context': 'both'}"
    addressed_in: "Phase 3"
    evidence: "ROADMAP Phase 3: 'plan 1B (#262): the filter toggle honours icon / both / label'; FILT-01 'CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE = {\"filter\": \"both\"} renders icon + \"Filter\"'"
---

# Phase 1: Label-mode defaults Verification Report

**Phase Goal:** A project sets the label-mode default for each location in one place, and every location reads that floor from a single accessor. With no configuration, output is unchanged.
**Verified:** 2026-10-26T09:20:00Z
**Status:** gaps_found
**Re-verification:** No (initial verification)

## Goal Achievement

The configuration mechanism is complete and correct. That covers the setting, the single accessor at all three
resolution sites, lazy reads, strict/log recovery, E108, docs and goldens. The last clause of the goal does not
fully hold. Code review finding CR-01 is a real, reproducible regression: with nothing configured, a card view whose
label mode is set on the instance (`as_view()` initkwargs or per-request assignment) now renders differently than at
the diff base. The byte-comparison goldens do not catch it, because the stock test views set the attribute on the
class.

### Observable Truths

**Roadmap contract and phase goal**

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| R1 | SC-1: `{"context": "both"}` makes every unmapped toolbar button icon + text; rows/cards unchanged; W292 stops firing for those keys | ✓ VERIFIED (filter toggle deferred to Phase 3) | `base.py:322` `target_default or default_label_mode("context")`. Tests passed: `test_context_floor_renders_unmapped_toolbar` (list/card/create/detail/update routes), `test_context_floor_does_not_change_rows_or_cards`, `test_w292_silent_with_context_floor`, `test_w292_explicit_icon_still_warns_with_floor` |
| R2 | SC-2: `{"card": "label"}` restores the 0.29 card look without touching a view; explicit `cv_card_actions_label_mode = "both"` on a view still wins | ✓ VERIFIED (class-level) | `test_card_floor_renders_label_only` (stock AuthorCardListView, delete stays icon-only via no_label). The class-attribute "both" precedence is tested. The instance-level case is gap G2 below |
| R3 | SC-3: `override_settings` changes the resolved default; an invalid mode outside strict mode logs and falls back | ✓ VERIFIED | Independent probe: absent → `{context: icon, list: icon, card: both}`; `{"card": "label"}` → card `label`; restores `both` on exit; `{"context": "Both"}` non-strict → `icon` twice with exactly one WARNING; strict → ValueError |
| R4 | SC-4: E108 reports unknown location key or invalid mode; valid keys come from LOCATIONS | ✓ VERIFIED | `settings.py:142-172` imports `button_data.LOCATIONS` lazily. Probe: `{"cotext":…, "card":"nope", "list":"label"}` → 2 Errors (level 40) in insertion order; `None` → 1; absent → 0. `test_e108_uses_button_locations` monkeypatches LOCATIONS |
| R5 | SC-5: literal grep empty; goldens byte-identical; docs state per-key merge vs whole-dict replacement | ✓ VERIFIED | `grep -n '"both" if card\|or "icon"\|get(key, "icon")' src/crud_views/lib/view/*.py` exits 1 (also exits 1 across all of src/). `git diff 06a8b81..HEAD -- tests/test1/golden src/crud_views/templates examples` is empty, as is porcelain status. `settings.md#label-mode-configuration` table rows 90-96 + "Existing per-action maps keep whole-dict replacement semantics" |
| G1 | Every location reads the floor from a single accessor | ✓ VERIFIED | `default_label_mode` called at `button_data.py:87/93`, `base.py:322/328`, `views/card.py:115`; no other label-mode floor literal in `src/` (extension packages have no label_mode code) |
| G2 | With no configuration, output is unchanged, including explicit card modes already set on a view | ✗ FAILED | CR-01. See Gaps. Probe at base 06a8b81: `as_view(cv_card_actions_label_mode="label")` → detail action 0 icons; at HEAD → 1 icon |

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
| P3-2 | Card chain: CardAction.label_mode → no_label → non-None view attribute → card floor (01-03) | ✗ PARTIAL | Holds for class attributes; a non-None instance attribute loses to the floor (CR-01). See Gaps |
| P3-3 | `None` valid; empty string → E210; empty action list renders nothing (01-03) | ✓ VERIFIED | `views/card.py:122-123` guarded E210; `test_good_values_yield_no_check`, `test_empty_card_actions_with_floor` |
| P3-4 | Only exact modes valid on the card attribute; lookalikes → E210 (01-03) | ✓ VERIFIED | `test_card_attribute_exact_modes` |
| P3-5 | Raw attribute None; resolver returns `both` unconfigured; goldens identical (01-03) | ✓ VERIFIED | `test_default_attribute_is_none_and_resolves_both`; golden diff empty |
| P3-6 | Release/migration notes disclose the attribute break; setting-first recipe (01-03) | ✓ VERIFIED (with inaccuracy noted) | CHANGELOG.md:47-53, migrating-1.0.md:138-; `test_card_migration_contract`. The sentence "A view that assigns the attribute keeps its value" is untrue for instance assignment (part of G2) |
| P4-1 | Documented card setting example renders label-only through the real tag (01-04) | ✓ VERIFIED | `test_documented_card_floor_renders_label_only` (ast.literal_eval, no exec) |
| P4-2 | One settings table distinguishes merge vs whole-layer replacement (01-04) | ✓ VERIFIED | settings.md:82-98; `test_label_mode_configuration_table` |
| P4-3 | Canonical context/list/card resolution sections in action_menus.md; secondary pages link (01-04) | ✓ VERIFIED | `test_canonical_label_mode_resolution_sections`, `test_label_mode_reference_links_and_diagram` |
| P4-4 | Public accessor, constant, setting, resolver documented with lazy/strict/E108 behavior (01-04) | ✓ VERIFIED | settings.md; docs tests passed; mkdocs `--strict` builds clean |
| P4-5 | Stable context names kept; PROJECT.md records no_label removal outside this phase (01-04) | ✓ VERIFIED | one-off PROJECT.md grep: 1 / 1 / 1 matching rows |
| P4-6 | Full Python, JS, strict docs, ruff gates pass; templates/goldens/examples unchanged (01-04) | ✓ VERIFIED | pytest 3056 passed / 1 skipped; vitest 8 files / 126 passed; mkdocs strict OK; `ruff check src tests` and `ruff format --check src tests` clean (repo-wide format check flags 6 pre-existing `.planning/*.md` files, recorded in deferred-items.md and outside package code) |

**Score:** 26/28 truths verified (0 present, behavior-unverified)

### Prohibitions (judgment-tier; LLM-judge verdict, not authoritative)

| Plan | Prohibition | Verdict | Notes |
|------|-------------|---------|-------|
| 01-01 | Label-mode defaults MUST NOT become theme-owned policy or override explicit project/view/button choices | ✗ VIOLATED (partial) | No theme layer exists (setting only; settings table has no theme row). But the card floor now overrides an explicit view choice set on the instance (CR-01). Closes with the G2 fix |
| 01-03 | Unchanged rendered output MUST NOT be presented as absence of a breaking Python attribute change | ✓ judged satisfied, unverified-prohibition, human review recommended | The CHANGELOG Breaking entry and migration bullet both say "this is a Python-level change", and name raw `None` vs resolved `both` and the resolver |

### Flagged probe edges (carried from plans)

- **EDGE-LMOD-02-unclassified (consumer completeness):** source scan finds no label-mode floor outside the three
  sites. `cv_button_data`, `cv_get_action_label_mode` and `CardListView` are the only consumers. Extension packages
  and templates have no fallback logic; the filter toggle is Phase 3. Evidence supports the assumption. CR-01 shows
  that the card consumer is wired with the wrong receiver (class instead of instance).
- **EDGE-LMOD-04-unclassified (call-time freshness):** nested `override_settings` enter/exit is verified by probe and
  by `test_default_label_mode_override_settings`. The import-time constant is unchanged (`MappingProxyType` raises
  TypeError on assignment). No further lifecycle case found.

### Deferred Items

| # | Item | Addressed In | Evidence |
|---|------|-------------|----------|
| 1 | Filter toggle stays icon-only under `{"context": "both"}` (custom template, excluded from SC-1 tests) | Phase 3 | "the filter toggle honours icon / both / label"; FILT-01 |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/crud_views/lib/view/label_mode.py` | Lazy accessor, immutable defaults, strict/warn-once helper | ✓ VERIFIED | 82 added lines, substantive; imported by button_data, base, views/card, settings |
| `src/crud_views/lib/view/button_data.py` | Leaf floor + malformed stamp recovery | ✓ VERIFIED | lines 82-94 |
| `src/crud_views/lib/settings.py` | Lazy E108 | ✓ VERIFIED | deferred imports; import-safety subprocess test passes |
| `src/crud_views/lib/view/base.py` | Context/list floor at final fallback | ✓ VERIFIED | lines 322, 325-328 |
| `src/crud_views/lib/view/buttons.py` | W292 survives invalid strict floor | ✓ VERIFIED | lines 407-411 |
| `src/crud_views/lib/views/card.py` | Optional attribute + public resolver | ⚠️ WIRED INCORRECTLY | Resolver exists and works at class level; render path calls it so instance values are lost (CR-01) |
| `tests/test1/test_label_mode_docs.py` | Executable docs contract | ✓ VERIFIED | 402 lines, passing |
| docs (`settings.md`, `action_menus.md`, `card-list-view.md`, `migrating-1.0.md`, CHANGELOG) | Merge/replace table, canonical sections, migration | ✓ VERIFIED | strict build + docs tests pass |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| button_data.py | label_mode.py | `default_label_mode`, `_invalid_label_mode` | ✓ WIRED | line 8 import, 87/89-94 use |
| settings.py | button_data.py | deferred `LOCATIONS` import | ✓ WIRED | line 105; fresh-process test proves deferral |
| base.py | label_mode.py | final-fallback `default_label_mode` | ✓ WIRED | lines 322, 328 |
| buttons.py | base.py | `cv_get_action_label_mode` in narrow try | ✓ WIRED | lines 407-410 |
| views/card.py | label_mode.py | `default_label_mode("card")` only when attribute None | ⚠️ PARTIAL | Wired, but the "attribute" checked is the class's, not the rendering instance's |
| context_buttons.md / action_menus.md / docs test → settings.md | canonical anchors | ✓ WIRED | docs link tests pass |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| action leaf `cv_label_mode` (context/list) | stamped mode or floor | `django.conf.settings.CRUD_VIEWS_LABEL_MODE_DEFAULTS` read per call | Yes | ✓ FLOWING |
| card action `cv_label_mode` | `label_mode` in `cv_get_card_action_data` | class attribute → setting | Yes for class config; instance config never reaches it | ⚠️ PARTIAL (CR-01) |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Accessor merge / override_settings / restore / warn-once / strict / unknown location / E108 / immutability | `python -I scratchpad/probe_lmod.py` (standalone settings.configure) | All outputs as specified (see truths R3, R4) | ✓ PASS |
| Phase test modules + goldens | `pytest <12 phase modules> -n auto` | 469 passed | ✓ PASS |
| Seeded random + xdist warning isolation | `pytest test_label_mode test_button_data test_action_label_mode_config -n 2 --random-order --random-order-seed=4711` | 298 passed | ✓ PASS |
| Full suite (run once) | `pytest tests -q -n auto` | 3056 passed, 1 skipped | ✓ PASS |
| CR-01 instance-level card mode, no configuration | temporary probe test (deleted) via `AuthorCardListView.as_view(cv_card_actions_label_mode="label")`, HEAD vs base worktree | base: 0 icons (label-only); HEAD: 1 icon; `v.cv_card_actions_label_mode="label"; v.cv_get_card_actions_label_mode()` → `"both"` | ✗ FAIL |

### Probe Execution

Step 7c: not applicable. The phase declares no `scripts/*/tests/probe-*.sh` probes, and none exist.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| LMOD-01 | 01-01, 01-02, 01-04 | Setting merged per key over package defaults; docs state merge vs whole-dict replacement | ✓ SATISFIED | label_mode.py; settings.md table |
| LMOD-02 | 01-01, 01-02, 01-03, 01-04 | `default_label_mode` single source used by cv_button_data, cv_get_action_label_mode, CardListView; no literals | ✓ SATISFIED | call sites + literal gate exit 1 |
| LMOD-03 | 01-03, 01-04 | Card attribute defaults None; explicit "both" still wins; `{"card":"label"}` restores 0.29 look | ⚠️ PARTIAL | Class-level satisfied and tested. An explicit value on the view instance does not win (CR-01) |
| LMOD-04 | 01-01, 01-02, 01-03, 01-04 | Read at call time; override_settings works | ✓ SATISFIED | probe + tests |
| LMOD-05 | 01-01, 01-02, 01-03, 01-04 | Invalid mode outside strict logs and falls back | ✓ SATISFIED | probe + tests |
| LMOD-06 | 01-01, 01-02, 01-04 | E108 for unknown key / invalid mode; keys from LOCATIONS | ✓ SATISFIED | settings.py; probe |

All six IDs are claimed by plans; there are no orphaned requirements. REQUIREMENTS.md already marks LMOD-03 `Complete`,
but the code does not fully support that while G2 is open.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/crud_views/lib/views/card.py` | 54, 109-115 | Classmethod resolver called from instance render path; the instance attribute is shadowed and ignored (CR-01) | 🛑 Blocker | Silent output change for unconfigured projects using initkwargs or per-request card modes |
| `CHANGELOG.md` | 53 | Claim "A view that assigns the attribute keeps its value" is false for instance assignment | ⚠️ Warning | Misleading release note; resolves with the fix |
| `src/crud_views/lib/view/button_data.py` | 97-105 | Strict "icon-only without icon" hint names knobs that do not apply to cards or the floor (WR-01) | ⚠️ Warning | Not a must-have; diagnostic quality |
| `src/crud_views/lib/views/card.py`, `buttons.py` | — | No W292-style check for icon-only card/list buttons created by the floor (WR-02) | ⚠️ Warning | New floor path to a render-time ValueError; outside the roadmap SCs |
| `tests/test1/test_button_data.py:425`, `test_import_safety.py:319` | — | 10 s subprocess timeouts (WR-03) | ℹ️ Info | Flake risk under xdist / Windows CI |

No TBD/FIXME/XXX/TODO/HACK markers in lines added by the phase.

### Human Verification Required

None needed to settle the status (it is gaps_found on code evidence). Optional reviewer confirmation, carried from the
plans:

1. **01-03 transparency prohibition.** The LLM judge rates it satisfied, but the verdict is not authoritative.
   Confirm that the CHANGELOG Breaking and migration bullets read as an honest Python-level break notice.
2. **Probe edges EDGE-LMOD-02 / EDGE-LMOD-04.** Confirm the consumer set and lifecycle cases listed above are complete.

### Gaps Summary

One root cause produces both failed truths. `CardListView.cv_get_card_action_data` (an instance method) used to read
`self.cv_card_actions_label_mode`. It now delegates to the classmethod `cv_get_card_actions_label_mode()`, which can
only see `cls.cv_card_actions_label_mode`. Any card mode supplied per instance is dropped:

- `as_view(cv_card_actions_label_mode=...)` initkwargs, which Django accepts because the class has the attribute
- assignment in `setup()`, `dispatch()` or `get_queryset()`, for example a per-user preference

This happens with or without `CRUD_VIEWS_LABEL_MODE_DEFAULTS`. It breaks the goal clause "With no configuration,
output is unchanged" (reproduced against base 06a8b81). It also breaks the "explicit choices still win" promise of
LMOD-03, D-14 ("view attribute (if not None)"), D-16 ("rendered output is unchanged"), the CHANGELOG sentence "keeps
its value" and the 01-01 prohibition. No CONTEXT decision accepted dropping instance-level support. D-15 only
requires that a public resolver exists, and an instance-aware read in the render path satisfies D-15 as well.
ViewSet-generated URLs call `as_view()` without kwargs, so the blast radius is hand-written URL confs and per-request
assignment. The change is still silent: nothing errors or warns.

Fix scope is small: read the instance in the render path (or make the resolver instance-aware). Add regression tests
for instance assignment and `as_view(**initkwargs)`, both unconfigured and against `{"card": "label"}`. Everything
else in the phase is verified with code and test evidence.

---

_Verified: 2026-10-26T09:20:00Z_
_Verifier: Claude (gsd-verifier)_
