---
phase: 06-form-button-leaf
plan: "08"
subsystem: docs
tags: [mkdocs, crispy-forms, django-filter, changelog, migration, label-mode, icons]

# Dependency graph
requires:
  - phase: 06-02
    provides: form leaf, FORM_LEAF_KEYS, literal normalizer, finite layout slots, defaults/key-count docs
  - phase: 06-03
    provides: owner-first form label-mode resolution, form maps, startup snapshot vs lazy floor
  - phase: 06-04
    provides: save/cancel/filter-reset icons, icon= / submit_icon / delete_icon precedence
  - phase: 06-05
    provides: filter helper get_form_actions hook, layout Apply/Reset, hidden-wrapper ordering
  - phase: 06-06
    provides: form-only E210/E211/W291, E106 / ViewSet validation, W292 static reach, missing-icon policy
provides:
  - Canonical form-button reference (buttons.md Forms, Literal text, The form leaf contract)
  - Form label-mode resolution and Form checks sections (action_menus.md), form knobs in settings.md
  - Form icon precedence (icons.md), custom form-button templates (theme.md), custom filter helpers (list_view.md)
  - Paired CHANGELOG Breaking entry and docs/migrating-1.0.md "Form buttons" section
  - Executable recipe tests (tests/test1/test_form_button_docs.py) and E108 inventory guards
  - Example project with CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"form": "both"}
affects: [06-09]

actuals:
  tokens: 23090
  tasks: 3
  commits: 3
plan_head_before: b1244b06ae3a113148ab27d323e22ffe95f02ae9
plan_head_after: b9b9f924f3a356ac6054bed99004c2fc57504a03

tech-stack:
  added: []
  patterns:
    - "Docs recipes executed, not mirrored: exec only the imports and named ClassDefs of a fence, literal_eval settings"
    - "Row-scoped and paragraph-scoped inventory guards with in-memory mutations proving they fail"

key-files:
  created:
    - tests/test1/test_form_button_docs.py
  modified:
    - docs/reference/buttons.md
    - docs/reference/action_menus.md
    - docs/reference/settings.md
    - docs/reference/icons.md
    - docs/reference/theme.md
    - docs/reference/list_view.md
    - docs/reference/javascript.md
    - docs/getting_started/tutorial-5-filters-permissions.md
    - docs/migrating-1.0.md
    - CHANGELOG.md
    - examples/bootstrap5/project/settings.py
    - src/crud_views/static/crud_views/js/tooltip.js
    - tests/test1/test_label_mode_docs.py

key-decisions:
  - "Form resolution prose lives once in action_menus.md (Form label-mode resolution, Form checks); settings.md extends the one merge/replace table with separate form rows so the existing row guards stay byte-stable"
  - "Each commit keeps mkdocs --strict green: Task 1 linked only existing anchors and Tasks 2/3 repointed buttons.md once the icons/theme/list_view/migration anchors existed"
  - "The migration guide gets a top-level ## Form buttons section placed before ## A downstream theme, because the pagination guard requires ### Table pagination overrides to end exactly at ## Silent breaks"
  - "The example sets only the form floor; the per-location merge keeps context/list/card at their package floors, guarded by test_example_enables_form_both_only"

patterns-established:
  - "Form-button docs tests render through {% crispy form helper %} and read the mode from the DOM (hidden span + title + tooltip = icon, <i> = both)"

requirements-completed: [FORM-05, FORM-08, FORM-09, FORM-10, FORM-11, FORM-12, FORM-13]

coverage:
  - id: D1
    description: "Canonical form contract in buttons.md, action_menus.md and settings.md: FORM_LEAF_KEYS, literal text, finite slots, owner-first whole-map resolution, lazy floor vs startup map, form diagnostics"
    requirement: FORM-11
    verification:
      - kind: unit
        ref: "tests/test1/test_label_mode_docs.py#test_form_label_mode_reference_contract"
        status: pass
      - kind: integration
        ref: "tests/test1/test_label_mode_docs.py#test_documented_form_map_renders_and_only_the_floor_is_live"
        status: pass
      - kind: integration
        ref: "tests/test1/test_label_mode_docs.py#test_documented_view_form_map_renders"
        status: pass
    human_judgment: false
  - id: D2
    description: "Both System checks E108 rows and the migration Step zero E108 paragraph list exactly button_data.LOCATIONS (context/list/card/form)"
    requirement: FORM-12
    verification:
      - kind: unit
        ref: "tests/test1/test_label_mode_docs.py#test_e108_rows_list_exactly_the_button_locations"
        status: pass
      - kind: unit
        ref: "tests/test1/test_label_mode_docs.py#test_migration_e108_location_inventory"
        status: pass
    human_judgment: false
  - id: D3
    description: "Executed helper and template recipes: field-only filter helper, replacement and None hooks, helper.inputs = [] changed-behavior regression, pill custom template with a hostile literal and template selection"
    requirement: FORM-08
    verification:
      - kind: integration
        ref: "tests/test1/test_form_button_docs.py"
        status: pass
    human_judgment: false
  - id: D4
    description: "Paired CHANGELOG Breaking / docs/migrating-1.0.md Form buttons migration and the example's form both setting"
    requirement: FORM-13
    verification:
      - kind: unit
        ref: "tests/test1/test_label_mode_docs.py#test_form_buttons_breaking_entry_pairs_with_migration"
        status: pass
      - kind: unit
        ref: "tests/test1/test_label_mode_docs.py#test_example_enables_form_both_only"
        status: pass
      - kind: other
        ref: ".venv/bin/mkdocs build --strict"
        status: pass
    human_judgment: false
  - id: D5
    description: "Readability and accuracy of the migration prose for downstream consumers"
    verification: []
    human_judgment: true
    rationale: "Tests pin facts and links; whether a consumer can migrate without guessing is a reading judgment for the 06-09 acceptance review"

duration: 16min
completed: 2026-10-28
status: complete
---

# Phase 06 Plan 08: Form-Button Documentation and Migration Summary

**The form-button contract is published end to end: owner-first form label-mode resolution, the FORM_LEAF_KEYS leaf, literal text, finite slots and form-only diagnostics. Helper and template recipes are executed through real crispy, a paired Breaking/migration entry ships, and the example renders forms in `both` mode.**

## Performance

- **Duration:** 16 min
- **Started:** 2026-10-28T08:07:46Z
- **Completed:** 2026-10-28T08:24:13Z
- **Tasks:** 3
- **Files modified:** 14 (1 created)

## Accomplishments

- `buttons.md` documents the form contract.
  - It explains the layout and `add_input()` paths, and that a slot outside `form:<kind>` raises ValueError.
  - It covers the literal-text boundary, the reserved-attribute rules and the `FORM_LEAF_KEYS` table.
  - It shows the three leaf bodies and the strict/fallback missing-icon rule.
  - The `{% cv_button "form" %}` rejection is documented.
  - The E106, E108, E210, E211, W291 and W292 rows now name the form rules. E108 lists context, list, card and form.
- `action_menus.md` adds the following:
  - a Form column with its getter
  - a Form label-mode resolution section: select the owner first, then the whole map, then the lazy floor. It covers an empty map versus None, and ordinary or absent owners.
  - a Form checks section: the form-only E211/E210/W291 policy against the unchanged context/list rule, E106 and construction-time validation, and the W292 static reach (providers checked, icons treated as unavailable).
- `settings.md` adds a `CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE` row, three form rows in the single merge/replace table, the startup-snapshot versus lazy-floor rule with the matching test approach, and a form recipe.
- `icons.md` documents the `save`, `cancel` and `filter-reset` names, the kind icons, the `icon=` > `submit_icon`/`delete_icon` > kind order, `form:icon-host` and the missing-icon policy.
- `theme.md` documents custom form-button templates: `template=` > subclass > bundled, `%s` pack substitution, an `input.*` → `cv_*` table and an escaped pill recipe.
- `list_view.md` documents custom filter helpers:
  - the `get_form_actions()` hook: replace, return `FormActions()`, or return None
  - why `helper.inputs = []` no longer suppresses the buttons, and the None-hook recipe
  - the legacy `add_input()` path, and the empty-Layout fallback
- The tutorial now says the filter helper appends Apply and Reset, and links to the recipe.
- `CHANGELOG.md` has one coherent Breaking entry. It covers:
  - the DOM change and the submitter/delete payload
  - multi-word name slugging and literal values
  - the `cv_*` template context and the M-SLOT rule
  - the `add_input` path, the filter wrapper and `helper.inputs`
  - the missing-icon policy

  One Added entry lists the new public API.
- `docs/migrating-1.0.md` has a `## Form buttons` section with six subsections, the Step zero E108 inventory and new silent-break items.
- `javascript.md` and the `tooltip.js` header comment list `form` as a tooltip location. The runtime logic is unchanged.
- The example project sets `CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"form": "both"}`.

## Task Commits

1. **Task 1: Document the form contract with a working configuration example** - `1a316d4` (docs). Tracer: verify re-run green before expansion.
2. **Task 2: Document and render custom helper and template migration recipes** - `b738604` (docs)
3. **Task 3: Pair Breaking notes with the migration and enable example both mode** - `b9b9f92` (docs)

## Files Created/Modified

- `tests/test1/test_form_button_docs.py`: runs the documented filter helpers (field-only, replacement, None hook) and the theme.md pill template through `{% crispy %}`. It uses an isolated locmem loader and a hostile literal, and includes the `helper.inputs = []` changed-behavior regression.
- `tests/test1/test_label_mode_docs.py`: adds these tests:
  - E108 inventory guards, row-scoped for the two tables and paragraph-scoped for Step zero, each with in-memory mutations that fail
  - rendering of the documented form maps
  - the form reference contract
  - Breaking/migration pairing and the example-setting guard
- Docs: `buttons.md`, `action_menus.md`, `settings.md`, `icons.md`, `theme.md`, `list_view.md`, `javascript.md`, `tutorial-5-filters-permissions.md`, `migrating-1.0.md`, `CHANGELOG.md`
- `examples/bootstrap5/project/settings.py`: the form `both` floor
- `src/crud_views/static/crud_views/js/tooltip.js`: header comment only

## Decisions Made

See `key-decisions` in the frontmatter.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Forward anchors would break the strict docs build per commit**
- **Found during:** Task 1
- **Issue:** `mkdocs.yml` has `validation.anchors: warn`, so with `--strict` a Task 1 link to an anchor first created in Task 2 or 3 fails the build. Those anchors are `icons.md#form-buttons`, `theme.md#custom-form-button-templates`, `list_view.md#custom-filter-helpers` and `migrating-1.0.md#form-buttons`.
- **Fix:** Task 1 linked only anchors that already existed. Tasks 2 and 3 repointed the `buttons.md` links once their targets existed, so `buttons.md` also appears in those two commits.
- **Files modified:** `docs/reference/buttons.md`
- **Verification:** `mkdocs build --strict` exited 0 after each task
- **Committed in:** `b738604`, `b9b9f92`

**2. [Rule 1 - Bug] Two Unreleased Added bullets had become inaccurate**
- **Found during:** Task 3
- **Issue:** The Phase 2 grammar bullet said "Existing form rendering is unchanged". The `CRUD_VIEWS_LABEL_MODE_DEFAULTS` bullet listed only context, list and card. Both are false after Phase 06.
- **Fix:** The grammar bullet now says layout form buttons look up the keys with their resolved mode. The defaults bullet lists `"form"` with its `"label"` floor. The unique `` - `CRUD_VIEWS_LABEL_MODE_DEFAULTS` sets`` prefix is kept, and its existing assertions still pass.
- **Files modified:** `CHANGELOG.md`
- **Committed in:** `b9b9f92`

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 documentation bug)
**Impact on plan:** Both were needed to keep the docs correct and every commit buildable. Scope did not grow.

## Issues Encountered

- Most new recipe tests passed on their first run, because they exercise behavior built in 06-02 through 06-06. To show they can fail, I mutated the docs in place and restored each file from a scratch copy before committing:
  - replacing the None hook with `super().get_form_actions()` failed the omission test
  - `{{ cv_label|safe }}` in the pill recipe failed the literal and icon tests
  - removing the title/tooltip line failed the icon-mode test
  - dropping `form` from an E108 row, or adding `menu`, failed the row guard

## Verification

- `.venv/bin/pytest tests/test1/test_label_mode_docs.py tests/test1/test_button_classes.py -q`: 70 passed (Task 1). Re-run as the tracer gate before Task 2.
- `.venv/bin/pytest tests/test1/test_form_button_docs.py -q`: 8 passed (Task 2)
- `.venv/bin/pytest tests/test1/test_label_mode_docs.py -q`: 15 passed (Task 3)
- `.venv/bin/mkdocs build --strict`: exit 0 after each task, with no warnings
- `examples/bootstrap5/test_docs_sync.py`: 36 passed
- Example project: `pytest` 301 passed with the new form floor, and `manage.py check` found no issues. The full example acceptance is 06-09.
- `06-js-verify.sh tests/js/tooltip.test.js`: 19 passed
- Full `pytest tests -n auto`: 4445 passed. `ruff check` and `ruff format --check` on `src` and `tests` are clean.

## Known Stubs

None.

## Threat Flags

None. T-06-15 is mitigated: the documented custom template runs with a hostile literal in its value, label and an extra attribute. The test asserts that the parsed DOM equals the literal, that there is no `<script>`, no extra attributes and no `{{ request.user }}` evaluation. T-06-16 is mitigated by the Breaking/migration pair in one commit, checked by `test_form_buttons_breaking_entry_pairs_with_migration`. T-06-SC: no dependency was installed.

## User Setup Required

None. No external service configuration required.

## Next Phase Readiness

- 06-09 can run the integrated acceptance. That covers the example under `form: both` (German form rendering, feature landing renders, doc-link tests), the full gates, and generic downstream-theme follow-up notes.
- Still open: the transitive dev-only `undici` audit advisories (WINDOWS entry 6).

## Self-Check: PASSED

- FOUND: `tests/test1/test_form_button_docs.py`, `docs/migrating-1.0.md`, `examples/bootstrap5/project/settings.py`
- FOUND: `1a316d4`, `b738604`, `b9b9f92` (ancestors of HEAD). Measured `git rev-list --count b1244b0..HEAD` = 3.

---
*Phase: 06-form-button-leaf*
*Completed: 2026-10-28*
