---
phase: 01-label-mode-defaults
plan: "02"
subsystem: ui
tags: [django, label-mode, context-toolbar, table-rows, system-checks, override_settings]

requires:
  - phase: 01-label-mode-defaults (plan 01-01)
    provides: "default_label_mode(location), LABEL_MODE_DEFAULTS, strict/log recovery, crud_views.E108, isolate_label_mode_warnings autouse fixture"
provides:
  - "CrudView.cv_get_action_label_mode: context fallback is target_default, then default_label_mode('context'); list fallback is membership in the selected map, then default_label_mode('list')"
  - "cv_icon_mode_checks (viewset.W292): catches ValueError around mode resolution only, so an invalid strict floor leaves E108 and every other check result in check_viewsets"
  - "viewset.E211 message: cv_card_actions_label_mode and cv_context_action_label_mode described as 'string or None' scalar overrides"
affects: [01-03 card resolver, 01-04 docs (E211 'string or None' counterpart, resolution-order sections), phase-03 filter toggle, phase-07 API freeze]

actuals:
  tokens: 8168
  tasks: 2
  commits: 4
plan_head_before: 30d069011b70a5f4dc0359a7fe2bd83c511de914
plan_head_after: cd583f568fc31a659cce78433965f88a692f8050

tech-stack:
  added: []
  patterns:
    - "Lazy floor read: the accessor is called only in the final fallback branch (short-circuit `or` for context, explicit membership branch for list), never as an eager dict.get default"
    - "Check generators catch ValueError narrowly around the single resolution call and `continue`; the setting check (E108) owns the report"

key-files:
  created:
    - .planning/phases/01-label-mode-defaults/01-02-SUMMARY.md
  modified:
    - src/crud_views/lib/view/base.py
    - src/crud_views/lib/view/buttons.py
    - src/crud_views/lib/view/action_menu.py
    - tests/test1/test_context_action_label_mode.py
    - tests/test1/test_context_button_label_mode.py
    - tests/test1/test_action_label_mode_config.py
    - tests/test1/test_action_label_mode_render.py

key-decisions:
  - "Context floor uses `target_default or default_label_mode(\"context\")`: a falsey target value still means unset (existing semantics), and the accessor runs only when nothing earlier names the key"
  - "List floor uses an explicit `if key in mapping` branch, so a mapped key (even a malformed one) never reads the floor; E211 and the button leaf keep validating mapped values"
  - "Invalid target-view modes are NOT sanitized in the resolver: the raw value is stamped and cv_button_data recovers it to the configured floor (D-10); only W292 treats an invalid target as unset"
  - "Filter toggle (cv-key=filter / #cv-filter-toggle) is excluded from the toolbar tests by XPath predicate; its fixed icon mode stays Phase 3 scope"

patterns-established:
  - "Floor-reading resolvers: every unmapped context/list key goes through default_label_mode(location); no literal icon floor remains in src/crud_views/lib/view/*.py"
  - "Precedence tests pair each earlier tier with a conflicting floor, plus an invalid strict floor that must never be read"

requirements-completed: [LMOD-01, LMOD-02, LMOD-04, LMOD-05, LMOD-06]

coverage:
  - id: D1
    description: "With CRUD_VIEWS_LABEL_MODE_DEFAULTS={'context': 'both'}, every eligible unmapped toolbar action on the author list, card, create, detail and update pages renders icon + visible short label with no title or hidden label; unconfigured toolbars stay icon-only"
    requirement: LMOD-02
    verification:
      - kind: integration
        ref: "tests/test1/test_context_action_label_mode.py#test_context_floor_renders_unmapped_toolbar"
        status: pass
    human_judgment: false
  - id: D2
    description: "The context floor leaves table-row and card action bodies byte-identical; only the card page's own toolbar changes"
    requirement: LMOD-02
    verification:
      - kind: integration
        ref: "tests/test1/test_context_action_label_mode.py#test_context_floor_does_not_change_rows_or_cards"
        status: pass
    human_judgment: false
  - id: D3
    description: "View map, button label_mode, ViewSet map, setting map and target view each beat a conflicting context floor; an empty view map suppresses the lower map but the target view still wins; explicit modes bypass an invalid strict floor"
    requirement: LMOD-01
    verification:
      - kind: unit
        ref: "tests/test1/test_context_action_label_mode.py#test_context_floor_preserves_precedence"
        status: pass
      - kind: unit
        ref: "tests/test1/test_context_action_label_mode.py#test_explicit_context_mode_bypasses_invalid_floor"
        status: pass
      - kind: unit
        ref: "tests/test1/test_context_action_label_mode.py#test_unmapped_context_key_reads_invalid_floor"
        status: pass
    human_judgment: false
  - id: D4
    description: "An invalid truthy target-view mode reaches the leaf unchanged; non-strict HTTP rendering recovers to the configured context floor and warns exactly once across two GETs"
    requirement: LMOD-05
    verification:
      - kind: integration
        ref: "tests/test1/test_context_action_label_mode.py#test_invalid_target_mode_renders_configured_floor"
        status: pass
    human_judgment: false
  - id: D5
    description: "W292 follows the resolved floor (silent under context=label/both, still warns for explicit icon at view map, ViewSet map, target view or button); full check_viewsets under strict mode returns E108 and the unrelated W291 instead of raising"
    requirement: LMOD-06
    verification:
      - kind: unit
        ref: "tests/test1/test_context_button_label_mode.py#test_w292_silent_with_context_floor"
        status: pass
      - kind: unit
        ref: "tests/test1/test_context_button_label_mode.py#test_w292_explicit_icon_still_warns_with_floor"
        status: pass
      - kind: integration
        ref: "tests/test1/test_context_button_label_mode.py#test_invalid_floor_check_viewsets_returns_e108"
        status: pass
    human_judgment: false
  - id: D6
    description: "list=label applies only to keys the selected whole-layer map does not name; whole-map replacement (empty view map, ViewSet over setting) is unchanged; mapped keys bypass an invalid strict list floor; unmapped keys raise strict and warn once non-strict"
    requirement: LMOD-04
    verification:
      - kind: unit
        ref: "tests/test1/test_action_label_mode_config.py#test_list_floor_used_only_for_unmapped_key"
        status: pass
      - kind: unit
        ref: "tests/test1/test_action_label_mode_config.py#test_list_floor_preserves_whole_map_replacement"
        status: pass
      - kind: unit
        ref: "tests/test1/test_action_label_mode_config.py#test_explicit_list_mode_bypasses_invalid_floor"
        status: pass
      - kind: unit
        ref: "tests/test1/test_action_label_mode_config.py#test_list_malformed_mapped_value_keeps_selection"
        status: pass
      - kind: integration
        ref: ".venv/bin/pytest tests/test1/test_label_mode.py tests/test1/test_button_data.py tests/test1/test_action_label_mode_config.py -q -n 2 --random-order --random-order-seed=4711"
        status: pass
    human_judgment: false
  - id: D7
    description: "A real table-row GET renders unmapped keys text-only under list=label, keeps an explicitly mapped icon key icon-only, and leaves the context toolbar icon-only"
    requirement: LMOD-02
    verification:
      - kind: integration
        ref: "tests/test1/test_action_label_mode_render.py#test_list_floor_renders_unmapped_rows"
        status: pass
    human_judgment: false
  - id: D8
    description: "E211 describes cv_card_actions_label_mode and cv_context_action_label_mode as 'string or None'; the three obsolete floor literals have zero matches in src/crud_views/lib/view/*.py; unconfigured goldens unchanged"
    requirement: LMOD-01
    verification:
      - kind: unit
        ref: "tests/test1/test_action_label_mode_config.py#test_e211_describes_optional_scalar_modes"
        status: pass
      - kind: other
        ref: "grep -n '\"both\" if card\\|or \"icon\"\\|get(key, \"icon\")' src/crud_views/lib/view/*.py  (exit 1, no output)"
        status: pass
      - kind: integration
        ref: ".venv/bin/pytest tests/test1/test_action_menus_golden.py tests/test1/test_card_label_mode_render.py tests/test1/test_card_blocks.py tests/test1/test_card_order.py tests/test1/test_form_frame.py tests/test1/test_heading_level.py -q"
        status: pass
    human_judgment: false
  - id: D9
    description: "EDGE-LMOD-02-unclassified: the in-scope consumer set is assumed to be the raw leaf, the context/list resolver and CardListView (01-03); the filter toggle stays Phase 3"
    requirement: LMOD-02
    verification: []
    human_judgment: true
    rationale: "The plan flags this spec-less classification as unresolved; a reviewer must confirm no further consumer of the label-mode floor exists. Never auto-dismissed."

duration: 6min
completed: 2026-10-26
status: complete
---

# Phase 1 Plan 02: Context and list label-mode floors Summary

**Real toolbars and table rows now read `CRUD_VIEWS_LABEL_MODE_DEFAULTS`. `cv_get_action_label_mode` consults `default_label_mode("context")` only after the view map, button, resolved map and target view, and `default_label_mode("list")` only for keys the selected whole-layer row map does not name. W292 catches the strict-mode `ValueError` around that one call, so `check_viewsets` returns `crud_views.E108` instead of a traceback.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-10-26T08:24:04Z
- **Completed:** 2026-10-26T08:30:49Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- With `{"context": "both"}`, each ordinary unmapped toolbar action renders an icon and a visible short label, with no title and no hidden label. This holds on all five tested author routes. Unconfigured toolbars stay icon-only, and the goldens are unchanged.
- The context floor leaves table-row and card action bodies byte-identical. Only the card page's own toolbar changes.
- Every earlier precedence tier beats a conflicting floor. An empty view map suppresses a populated ViewSet map but still lets the target view win. Valid explicit modes never read an invalid strict floor, for both a malformed mode and a non-dict setting.
- An invalid target-view mode (`"nope"`) is stamped raw. With `CRUD_VIEWS_STRICT=False` it renders the configured `both` floor and logs exactly one warning across two real GETs.
- `list=label` gives text-only unmapped row actions through a real GET. An explicit `{"update": "icon"}` row key keeps its icon and hidden label, and the toolbar stays icon-only.
- E211 now calls both scalar overrides "string or None". The three obsolete floor literals have zero source matches.

## Task Commits

1. **Task 01-02-01 (tracer): context floor through an HTTP toolbar, E108 reachable**: RED `12b53eb` (test), GREEN `e1e8e24` (feat)
2. **Task 01-02-02: independent list floor, whole-map compatibility**: RED `1c38339` (test), GREEN `cd583f5` (feat)

No REFACTOR commits were needed.

## TDD Evidence

- **01-02-01 RED (`12b53eb`):** 18 failed and 79 passed. All 18 failures were assertions on the planned behavior. `_icon_and_short_label(...)` was False on all five routes. Precedence returned `'icon' == 'both'`. W292 still warned under the floor (`["context action 'update' ..."] == []`). The explicit-icon W292 cases got two warnings because `delete` ignored the floor. The strict accessor checks reported `DID NOT RAISE ValueError`. No collection, import or fixture errors. Semantic assessment: every target ran and failed because the resolver still returned the literal icon floor.
- **Pitfall 2 confirmation (intermediate, not committed):** with only the resolver change applied, `test_invalid_floor_check_viewsets_returns_e108` failed. A `ValueError: setting CRUD_VIEWS_LABEL_MODE_DEFAULTS must be a dict ...` escaped `check_viewsets`, so the narrow W292 catch is necessary.
- **01-02-02 RED (`1c38339`):** 14 failed and 88 passed. All 14 failures were assertions. List precedence returned `'icon' == 'label'`. The row-render test failed on `_text_only(...)` for `detail`. The strict list cases reported `DID NOT RAISE ValueError`. The E211 regex found no `string or None`. `test_list_malformed_mapped_value_keeps_selection` passed at RED as intended: it guards the existing selection semantics against regression.
- **GREEN:** `gsd-tools check tdd-red-evidence` was not run. The project's pytest report format is not a supported classifier format, and `workflow.tdd_mode` is false. The RED assessment above is a manual semantic inspection.

## Verification Results

| Command | Result |
|---|---|
| `.venv/bin/pytest tests/test1/test_context_action_label_mode.py tests/test1/test_context_button_label_mode.py -q` (task 1 verify, tracer gate re-run) | 97 passed |
| `.venv/bin/pytest tests/test1/test_action_label_mode_config.py tests/test1/test_action_label_mode_render.py -q` | 102 passed |
| `.venv/bin/pytest tests/test1/test_label_mode.py tests/test1/test_button_data.py tests/test1/test_action_label_mode_config.py -q -n 2 --random-order --random-order-seed=4711` | 298 passed |
| Same seed plus the three context/render test modules (cross-module leakage) | 411 passed |
| Literal gate `grep -n '"both" if card\|or "icon"\|get(key, "icon")' src/crud_views/lib/view/*.py` | no output, grep exit 1, wrapper exit 0 |
| Plan verification: goldens, card render, card blocks/order, form frame, heading level | 89 passed (no golden regenerated) |
| `pytest tests -q -n auto` (and `--random-order-seed=1234`) | 3036 passed, 1 skipped (both) |
| `ruff check` / `ruff format --check` on all changed files, before each commit | clean |

## Tested Routes

The toolbar tests use authorized `django.test.Client` GETs with real fixtures (`author_douglas_adams`, a user with view/add/change/delete). The tested routes are:

- `author-list` (`/author/`)
- `author-card`
- `author-create`
- `author-detail`
- `author-update`

Each route's eligible set is nonempty and is asserted against the unconfigured baseline. The row-body comparison uses `author-list`, and the card-body comparison uses `author-card`.

## Scope Boundary: filter toggle

Candidate toolbar nodes are selected with `./*[@cv-key][not(@cv-key="filter") and not(@id="cv-filter-toggle")]`. The author routes configure no filter and no other custom-template control, so nothing else was excluded. The filter template's fixed icon mode is untouched and belongs to Phase 3.

## Files Created/Modified
- `src/crud_views/lib/view/base.py`:
  - imports `default_label_mode`.
  - Context fallback is now `target_default or default_label_mode("context")`.
  - List fallback is an `if key in mapping` branch, then `default_label_mode("list")`.
  - The three label-mode attribute comments, both map-getter docstrings and the resolver docstring describe the configured floors.
- `src/crud_views/lib/view/buttons.py`: in `cv_icon_mode_checks`, `try/except ValueError` wraps only the `cv_get_action_label_mode` call and `continue`s that key. The docstring explains the E108 hand-off.
- `src/crud_views/lib/view/action_menu.py`: the E211 explanation says "string or None" for both scalars.
- `tests/test1/test_context_action_label_mode.py`: route-parametrized toolbar render, row/card byte-stability, nine precedence cases, invalid-floor bypass and fallthrough, invalid-target HTTP recovery.
- `tests/test1/test_context_button_label_mode.py`: W292 under context floors, W292 for explicit icon at four tiers, full `check_viewsets` E108 integration.
- `tests/test1/test_action_label_mode_config.py`: list floor per layer, whole-map replacement, malformed mapped value, invalid-floor bypass with warn-once across settings contexts, E211 wording.
- `tests/test1/test_action_label_mode_render.py`: `test_list_floor_renders_unmapped_rows`.

## Decisions Made
- `target_default or default_label_mode("context")` keeps the existing rule that a falsey target value means unset. Because `or` short-circuits, the floor is never read when a target mode exists.
- The list branch uses explicit membership, not `mapping.get(key, ...)`, so the accessor never runs eagerly for a mapped key. That matters for strict raises and for D-11 log noise.
- The resolver does not sanitize an invalid target-view mode. That stays W292's check-only behavior, and render-time recovery belongs to `cv_button_data` (D-10).
- The "string or None" phrase is pinned with a short regex per scalar, not the whole sentence (A9). Plan 01-04 must keep the docs counterpart consistent.

## Deviations from Plan

None. The plan was executed as written.

One addition within scope: `test_unmapped_context_key_reads_invalid_floor` covers true context fallthrough, with a strict raise and a single non-strict warning. It mirrors the list-side behavior that task 01-02-02 requires and is not in the plan's named test list.

## Issues Encountered
None.

## Flagged items carried to verification
- **EDGE-LMOD-02-unclassified (unresolved):** the assumed complete in-scope consumer set is the raw leaf, the context/list resolver and CardListView (01-03). The filter toggle remains Phase 3. Direct call-site checks and the full goldens back this assumption, but a reviewer must confirm completeness. Not auto-dismissed.
- Requirements LMOD-01/02/04/05/06 are shared with sibling plans 01-03 and 01-04. `requirements.ready-ids` reported all five as blocked, so they were not marked complete in REQUIREMENTS.md by this plan.

## Threat Model Compliance
- **T-01-04 (DoS, W292 / check_viewsets): mitigated.** The narrow catch is around the resolution call only. `test_invalid_floor_check_viewsets_returns_e108` runs the full `check_viewsets` under strict mode with `{"context": "nope"}` and with `None`. It asserts E108 and an unrelated W291 both survive, and that strict rendering still raises.
- **T-01-05 (Tampering, precedence / eager evaluation): mitigated.** Both tasks test that valid explicit overrides bypass malformed floors with zero log records. Whole-map replacement is also tested.
- **T-01-06 (EoP): accepted.** No permission code was modified. Authorized renders and the full suite's permission tests pass.

## User Setup Required
None.

## Next Phase Readiness
- Plan 01-03 (card resolver) is independent of these files.
- Plan 01-04 (docs) should describe:
  - the context and list resolution order: maps, button and target view, then the defaults-map floor
  - the "string or None" E211 wording
  - the filter-toggle exclusion

## Self-Check: PASSED
- All seven modified source and test files exist on disk.
- Commits 12b53eb, e1e8e24, 1c38339 and cd583f5 are ancestors of HEAD. The ledger counts 4 commits from 30d0690 to cd583f5.

---
*Phase: 01-label-mode-defaults*
*Completed: 2026-10-26*
