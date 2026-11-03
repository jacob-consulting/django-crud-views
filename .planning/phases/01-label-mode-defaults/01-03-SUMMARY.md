---
phase: 01-label-mode-defaults
plan: "03"
subsystem: ui
tags: [django, label-mode, card-list-view, system-checks, override_settings, migration]

requires:
  - phase: 01-label-mode-defaults (plan 01-01)
    provides: "default_label_mode(location), LABEL_MODE_DEFAULTS, strict/log recovery in cv_button_data, crud_views.E108"
provides:
  - "CardListView.cv_card_actions_label_mode: str | None = None (raw attribute unset by default)"
  - "CardListView.cv_get_card_actions_label_mode() -> str: public classmethod; attribute when set, else default_label_mode('card')"
  - "E210 on the view attribute only when it is set; per-action checks unchanged"
  - "CHANGELOG Breaking/Added/Fixed entries and migrating-1.0.md attribute bullet + setting-first 0.29 card recipe"
affects: [01-04 docs (retargets action_menus.md#label-mode / settings.md#action-menus links), phase-07 API freeze]

actuals:
  tokens: 3946
  tasks: 2
  commits: 3
plan_head_before: ecc0ee320f02cf6b5305208dea0fd2ba4b03c691
plan_head_after: f03933cd23c391f2256f7144700b9ee2acbebeb9

tech-stack:
  added: []
  patterns:
    - "Classmethod resolver next to cv_get_card_actions_inline: raw optional attribute, floor read lazily only when it is None"

key-files:
  created:
    - .planning/phases/01-label-mode-defaults/01-03-SUMMARY.md
  modified:
    - src/crud_views/lib/views/card.py
    - src/crud_views/lib/view/card.py
    - tests/test1/test_card_label_modes.py
    - tests/test1/test_card_label_mode_render.py
    - docs/reference/card-list-view.md
    - docs/migrating-1.0.md
    - CHANGELOG.md

key-decisions:
  - "Card chain is CardAction.label_mode, then no_label -> icon, then cv_get_card_actions_label_mode() (attribute, then default_label_mode('card')); no_label untouched and warning-free (D-18)"
  - "A valid explicit view attribute short-circuits the resolver, so an invalid strict card floor never raises for that view"
  - "card-list-view.md links the existing action_menus.md#label-mode and settings.md#action-menus anchors; 01-04 retargets them to canonical sections"

patterns-established:
  - "Resolved reads of the card mode go through cv_get_card_actions_label_mode() or the stamped cv_label_mode, never the raw attribute"

requirements-completed: [LMOD-02, LMOD-03, LMOD-04, LMOD-05]

coverage:
  - id: D1
    description: "Project setting {'card': 'label'} renders stock Author card detail/update label-only; no_label delete stays icon-only with hidden label and title, no DeprecationWarning"
    requirement: LMOD-03
    verification:
      - kind: integration
        ref: "tests/test1/test_card_label_mode_render.py#test_card_floor_renders_label_only"
        status: pass
    human_judgment: false
  - id: D2
    description: "Precedence: CardAction.label_mode over no_label, no_label over view/floor, explicit view attribute over floor"
    requirement: LMOD-03
    verification:
      - kind: integration
        ref: "tests/test1/test_card_label_mode_render.py#test_card_mode_precedence_with_floor"
        status: pass
      - kind: unit
        ref: "tests/test1/test_card_label_modes.py#test_card_explicit_mode_bypasses_floor"
        status: pass
    human_judgment: false
  - id: D3
    description: "Raw attribute None, resolver returns both unconfigured and follows/restores override_settings"
    requirement: LMOD-04
    verification:
      - kind: unit
        ref: "tests/test1/test_card_label_modes.py#test_default_attribute_is_none_and_resolves_both"
        status: pass
      - kind: unit
        ref: "tests/test1/test_card_label_modes.py#test_card_resolver_reads_setting"
        status: pass
    human_judgment: false
  - id: D4
    description: "E210 accepts None, rejects empty, case, whitespace and Greek-omicron lookalike attribute values; empty action list stays empty; context/list floors leave card body unchanged"
    requirement: LMOD-05
    verification:
      - kind: unit
        ref: "tests/test1/test_card_label_modes.py#test_card_attribute_exact_modes"
        status: pass
      - kind: unit
        ref: "tests/test1/test_card_label_modes.py#test_good_values_yield_no_check"
        status: pass
      - kind: integration
        ref: "tests/test1/test_card_label_mode_render.py#test_empty_card_actions_with_floor"
        status: pass
      - kind: integration
        ref: "tests/test1/test_card_label_mode_render.py#test_context_override_keeps_card_action_body"
        status: pass
    human_judgment: false
  - id: D5
    description: "Release and migration notes disclose the Python attribute break (raw None, resolved both), setting-first restoration recipe, Added names, Fixed non-strict repair"
    requirement: LMOD-02
    verification:
      - kind: command
        ref: "01-03-02 <verify> card migration contract script"
        status: pass
      - kind: command
        ref: ".venv/bin/mkdocs build --strict"
        status: pass
    human_judgment: true
    rationale: "Prohibition 'unchanged rendered output MUST NOT be presented as absence of a breaking Python attribute change' is flagged-unverified; a reviewer must judge the migration wording"

duration: 4min
completed: 2026-10-26
status: complete
---

# Phase 1 Plan 03: Card label-mode resolver and migration disclosure Summary

**`CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"card": "label"}` now restores the 0.29 label-only card look project-wide through the new public `CardListView.cv_get_card_actions_label_mode()`. The raw `cv_card_actions_label_mode` defaults to `None`, and that Python-level break is disclosed in CHANGELOG and the migration guide.**

## Performance

- **Duration:** 4 min
- **Started:** 2026-10-26T08:32:57Z
- **Completed:** 2026-10-26T08:37:02Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- `CardListView.cv_card_actions_label_mode: str | None = None`. The classmethod `cv_get_card_actions_label_mode()` returns the attribute when it is set, otherwise `default_label_mode("card")`, which falls back to the package floor `"both"`.
- `cv_get_card_action_data` resolves in this order: `CardAction.label_mode`, then `no_label` (rendered as icon), then the resolver. `no_label` itself is unchanged and emits no new warning (D-18).
- E210 checks the view attribute only when it is set. `None` is valid. Empty strings, wrong case, padded whitespace and the Greek-omicron lookalike `"bοth"` are rejected; the lookalike is escaped in source, so ruff raises no RUF001.
- `card-list-view.md`: the setting is documented first. The attribute is shown as `str | None` / `None`, and resolved reads point at the resolver or the stamped `cv_label_mode`. The CardAction `label_mode` row points at the resolver. Links use only anchors that already exist.
- CHANGELOG Unreleased gets a Breaking "Card label-mode attribute" entry, an Added entry naming the setting, `default_label_mode`, `LABEL_MODE_DEFAULTS`, the resolver and E108, and a Fixed entry, "Malformed stamped label modes". The #213 recipe is now ordered setting, then per-view, then per-button. The migration guide has the matching attribute bullet and recipe order, adds E108 to the check list, and explains strict versus non-strict behaviour.

## Task Commits

1. **Task 01-03-01 (tracer, TDD):** RED `67deeae` (test), GREEN `9c03f73` (feat). No refactor was needed.
2. **Task 01-03-02:** `f03933c` (docs)

## TDD Evidence

- **RED (`67deeae`):** 6 tests failed on assertions. The resolver did not exist (`AttributeError`). `test_good_values_yield_no_check` got an E210 for `None`. The two render tests found an `<i>` icon on detail/update because the floor was never read. The exact-mode, empty-action and context-body tests already passed: those guards held before this change.
- **GREEN (`9c03f73`):** 25/25 card tests passed. The full suite gave 3049 passed, 1 skipped.
- **Tracer gate (auto mode):** the task verify was re-run after the GREEN commit (25 passed). Logged "Tracer verified end-to-end — expanding".

## Verification Results

| Command | Result |
|---|---|
| `.venv/bin/pytest tests/test1/test_card_label_modes.py tests/test1/test_card_label_mode_render.py -q` | 25 passed |
| `.venv/bin/ruff check` / `ruff format --check` (changed py files) | clean |
| Plan verification: goldens, card render/blocks/order, form frame, heading level | 93 passed, goldens unchanged |
| `.venv/bin/mkdocs build --strict` | built, no warnings |
| 01-03-02 contract script | `card migration contract present` |
| `pytest tests -q -n auto` | 3049 passed, 1 skipped |

## Files Created/Modified
- `src/crud_views/lib/views/card.py`: optional attribute, resolver classmethod, resolver used in the action-data chain, E210 guard
- `src/crud_views/lib/view/card.py`: the `CardAction.label_mode` comment now names the view resolver and the defaults map
- `tests/test1/test_card_label_modes.py`: tests for the resolver default, setting, explicit bypass (including an invalid strict floor), exact modes and the omicron runtime value, plus `None` in the good-values check
- `tests/test1/test_card_label_mode_render.py`: the four HTTP tests for floor, precedence, empty actions and context body
- `docs/reference/card-list-view.md`, `docs/migrating-1.0.md`, `CHANGELOG.md`: guidance as described above

## Decisions Made
- A valid explicit view attribute short-circuits the floor read, so the project setting cannot break a view that already chose its mode (T-01-07).
- The empty-action test asserts there is no `cv-key`, `<a>` or `<button>` inside the card. The context-body test compares the whole card markup under `{}` and under `{"context": "both", "list": "label"}`.
- The DeprecationWarning assertion in the floor render test is strict: it allows no DeprecationWarning of any kind during the request.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Accuracy] E210 changelog bullet wording**
- **Found during:** Task 01-03-02
- **Issue:** The existing Unreleased bullet said E210 rejects "an unknown `cv_card_actions_label_mode`". With `None` now valid, that was imprecise.
- **Fix:** It now reads "a set `cv_card_actions_label_mode`".
- **Files modified:** CHANGELOG.md
- **Commit:** f03933c

**2. [Scope] Extra test `test_card_lookalike_is_greek_omicron`**
- This test proves that the escaped source literal really evaluates to U+03BF at runtime, as B1 requires. It is test-only.

---

**Total deviations:** 1 auto-fixed (wording accuracy), plus 1 extra test. **Impact:** none on behavior or scope.

## Issues Encountered
None.

## Acceptance note (external theme)
The external reference theme should audit any direct reads of `cv_card_actions_label_mode` and switch to `cv_get_card_actions_label_mode()` or the stamped `cv_label_mode`. Research found no direct template reads. No other repository was edited.

## Flagged items carried to verification
- **Prohibition (flagged-unverified):** "Unchanged rendered output MUST NOT be presented as absence of a breaking Python attribute change." Both Breaking/migration bullets name the raw `None` and the resolved `"both"`. The migration bullet calls it "a Python-level change" explicitly. A reviewer must still judge this; it is not machine-certified.

## Threat Model Compliance
- T-01-07 (DoS, card fallback): mitigated. `None` resolves through `default_label_mode`, and a valid explicit attribute bypasses an invalid strict floor (`test_card_explicit_mode_bypasses_floor`).
- T-01-08 (tampering, precedence / accessible label): mitigated. The render tests check explicit modes, the unchanged `no_label` chain, and the text-only DOM with a real nonempty label. Icon-only delete keeps its hidden label and title.
- T-01-09 (consumer raw attribute access): mitigated. The break is disclosed in CHANGELOG Breaking and in `docs/migrating-1.0.md`, both naming the resolver.

## User Setup Required
None.

## Next Phase Readiness
- Plan 01-04 can create the canonical resolution and settings sections and retarget the `action_menus.md#label-mode` / `settings.md#action-menus` links in card-list-view.md, migrating-1.0.md and CHANGELOG.md.

## Self-Check: PASSED
- All 7 modified files exist.
- Commits 67deeae, 9c03f73 and f03933c are ancestors of HEAD. The ledger count is 3 commits from ecc0ee3 to f03933c.
