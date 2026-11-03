---
phase: 05-table-pagination-parity
plan: "01"
subsystem: ui
tags: [django-tables2, pagination, accessibility, button-classes, templates, golden-tests]

requires:
  - phase: 02-form-key-grammar
    provides: class-key grammar, W362 unknown-key check and the live default-key count guard
provides:
  - Accessible stock table pagination (registry arrows, translated hidden labels, aria-current span, aria-disabled ends)
  - Public class key pagination:hidden-label (default visually-hidden) shared by table and card pagination
  - Baseline-before-change table goldens (be7daa5) and frozen raw card render bytes (0275218)
affects: [05-02, 05-03, phase-07-theme-surface-freeze]

actuals:
  tokens: 6810
  tasks: 3
  commits: 7
plan_head_before: 7dcfa76f98ca858433dce66c1480f82eb3dbcc39
plan_head_after: 4b9a619289ee92e0edf9e01fbf9cda35b52baea5

tech-stack:
  added: []
  patterns:
    - "Direction blocks enclose their own availability guard so overrides run on disabled ends too"
    - "Rendered-template origin asserted before golden IO for real-view template captures"
    - "Raw-byte JSON baseline (no normalization) to prove a class-table substitution preserves default bytes"

key-files:
  created:
    - tests/test1/golden/table_pagination/page1.html
    - tests/test1/golden/table_pagination/page2.html
    - tests/test1/golden/card_pagination/raw_pages.json
  modified:
    - src/crud_views/templates/crud_views/table/bootstrap5.html
    - src/crud_views/templates/crud_views/snippets/pagination.html
    - src/crud_views/lib/button_classes.py
    - tests/test1/test_table_template.py
    - tests/test1/test_card_order.py
    - tests/test1/test_button_classes.py
    - docs/reference/buttons.md

key-decisions:
  - "05-01: the template-origin check compares against the crud_views package's own template path (Path(crud_views.__file__)), which is the tracked src/ file in a dev checkout and its installed copy under nox"
  - "05-01: table baseline commit be7daa5 holds only the capture test and two goldens; production blob IDs equal its parent's. Card raw baseline commit 0275218 predates the card template edit"
  - "05-01: the table nav keeps no mt-3 class; only its aria-label changes to the translated 'pagination' msgid, so non-pagination markup is preserved"

patterns-established:
  - "Pagination direction li class lists: 'previous page-item' / 'previous page-item disabled' and 'next page-item' / 'next page-item disabled'"
  - "pagination:hidden-label is a plain utility key: no button location, no mode keys, default -> theme -> project"

requirements-completed: [PAGE-01, PAGE-02, PAGE-03, PAGE-04]

coverage:
  - id: D1
    description: "Baseline-only commit of today's first/last-page table pagination goldens before any markup change, then visibly updated"
    requirement: PAGE-01
    verification:
      - kind: integration
        ref: "tests/test1/test_table_template.py#test_table_pagination_golden"
        status: pass
      - kind: other
        ref: "git diff --name-only be7daa5^ be7daa5 (3 capture files only; template/registry blob IDs equal parent)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Stock table pagination: page-previous/page-next icons, translated hidden labels, li[aria-current=page] span, aria-disabled ends without href/tabindex, translated nav label"
    requirement: PAGE-02
    verification:
      - kind: integration
        ref: "tests/test1/test_table_template.py#test_table_pagination_accessible_structure"
        status: pass
    human_judgment: false
  - id: D3
    description: "pagination:hidden-label styles both table and card arrow labels; default card render bytes unchanged"
    requirement: PAGE-03
    verification:
      - kind: integration
        ref: "tests/test1/test_table_template.py#test_table_pagination_shared_hidden_label"
        status: pass
      - kind: integration
        ref: "tests/test1/test_card_order.py#test_card_pagination_shared_hidden_label"
        status: pass
      - kind: unit
        ref: "tests/test1/test_card_order.py#test_card_pagination_raw_bytes"
        status: pass
    human_judgment: false
  - id: D4
    description: "Class table has 71 default keys; buttons.md count, row and shared-pagination explanation agree; registry contract and W362 grammar unchanged"
    requirement: PAGE-04
    verification:
      - kind: unit
        ref: "tests/test1/test_button_classes.py#test_pagination_hidden_label_registry_contract"
        status: pass
      - kind: unit
        ref: "tests/test1/test_button_classes.py#test_documented_default_key_count_matches_table"
        status: pass
    human_judgment: false

duration: 5min
completed: 2026-10-27
status: complete
---

# Phase 5 Plan 01: Table Pagination Parity Summary

**The stock django-tables2 pagination now has the card's accessibility contract: `page-previous`/`page-next` registry arrows, translated hidden labels, an `aria-current` span for the current page, and `aria-disabled` ends with no href. One new `pagination:hidden-label` class key styles the arrow labels of both paginations, and the default card render stays byte-identical.**

## Performance

- **Duration:** about 5 min (recorded start 2026-10-27T12:36:43Z after the context reads)
- **Started:** 2026-10-27T12:36:43Z
- **Completed:** 2026-10-27T12:41:26Z
- **Tasks:** 3
- **Files modified:** 10 (3 created, 7 modified)

## Accomplishments

- PAGE-01 chronology: `be7daa5` captures the old table markup through the real `/author/` view (template origin verified). `0b0f9ba` later updates those same two goldens.
- In the table template, `pagination.previous` and `pagination.next` now enclose their own `has_previous`/`has_next` guards and render disabled ends. All tables2 block names are preserved (`pagination`, `pagination.previous`, `pagination.range`, `pagination.next`).
- In `pagination.range`, the current page is `li.page-item.active[aria-current=page] > span.page-link`. Other pages keep their `cv_querystring table.prefixed_page_field` links, and the ellipsis still renders with no href.
- `pagination:hidden-label` (default `visually-hidden`) is read through `cv_button_class` in both templates. Setting it to `sr-only` changes the table and card labels alike.
- `raw_pages.json` freezes the exact card snippet output for both pages (UTF-8, no normalization). The output still matches after the four literals were replaced. Both normalized card goldens are unchanged.
- The default class table is now 71 keys. The test, the canonical sentence in buttons.md and the new row all agree. The explanation sits beside the hidden-label utility text, and the "Container element and label" section is intact.

## Task Commits

1. **Task 1 (tracer): table pagination end to end**
   - `be7daa5` test: baseline capture of the old table goldens (baseline-only commit, D-06)
   - `97c9dc4` test: RED, accessible structure and shared hidden label
   - `0b0f9ba` feat: GREEN, table template, registry key, regenerated table goldens
2. **Task 2: card shares the utility, default bytes pinned**
   - `0275218` test: raw card byte baseline, plus UTF-8 IO in the normalized golden helper (before the card edit)
   - `7b293b8` test: RED, shared label on the card
   - `d7142ae` feat: GREEN, four literals replaced with `cv_button_class 'pagination' 'hidden-label'`
3. **Task 3: registry/doc contract**
   - `4b9a619` test: EXPECTED_KEYS/71, utility-slot parametrization, registry contract test, buttons.md row/count/explanation

### Baseline chronology evidence

| Baseline | SHA | Files in commit | Production blobs vs parent |
|---|---|---|---|
| Table goldens | `be7daa55ddc2bb1e7bf5f93d01ddd796a4421d4d` | test_table_template.py, table_pagination/page1.html, page2.html | table template `4e37650`, card snippet `50cebe8`, button_classes.py `294c794`: all equal |
| Card raw bytes | `0275218710e3742ed91cf1995010cec6deb0004c` | test_card_order.py, card_pagination/raw_pages.json | card snippet `50cebe8`: equal |

## TDD Evidence

- **Task 1 RED (`97c9dc4`):** 4/4 targets failed on planned-behavior assertions. The nav label was `'Table navigation' != 'pagination'`, page 1 had no disabled previous anchor, and the label span had no class where `sr-only` was expected. Semantic assessment: valid RED. The targets were collected and executed, with no import, fixture or collection errors.
- **Task 1 GREEN (`0b0f9ba`):** 10/10 in test_table_template.py after the intentional table-only golden regeneration. The tracer gate re-ran verify and passed.
- **Task 2 RED (`7b293b8`):** both pages failed only after the `sr-only` override (`('visually-hidden', True) != ('sr-only', True)`). The default-state assertion in the same test passed. Valid RED.
- **Task 2 GREEN (`d7142ae`):** 29/29 in test_card_order.py, with no golden variable set.
- The machine classifier (`check tdd-red-evidence`) was not run. pytest's console format is not one of its adapters, and the plan is `type: execute` with `workflow.tdd_mode: false`, so the format gate does not apply. The RED evidence above is from the actual runs.

## Command Results

- Baseline before edits: `.venv/bin/pytest tests/test1/test_table_template.py tests/test1/test_card_order.py tests/test1/test_button_classes.py -q`: 77 passed (matches the planning baseline).
- Task 1 verify: `.venv/bin/pytest tests/test1/test_table_template.py -q`: 6 passed at baseline, 10 passed after GREEN.
- Negative check: rendering the upstream `django_tables2/bootstrap5.html` (no template monkeypatch) fails at the `table.template_name` assertion before any golden IO.
- Task 2 verify: `.venv/bin/pytest tests/test1/test_card_order.py -q`: 27 passed at the baseline commit, 29 passed after GREEN.
- Task 3 verify: `.venv/bin/pytest tests/test1/test_table_template.py tests/test1/test_card_order.py tests/test1/test_button_classes.py tests/test1/test_button_classes_checks.py -q`: 391 passed.
- Full suite: `.venv/bin/pytest tests -q -n auto`: 3508 passed, 1 skipped.
- `ruff check .`: all checks passed. `ruff format --check src tests`: 288 files already formatted.
- `mkdocs build --strict`: succeeded (output to the scratchpad, not the repo).

## Files Created/Modified

- `src/crud_views/templates/crud_views/table/bootstrap5.html`: accessible pagination; guards moved inside the direction blocks.
- `src/crud_views/templates/crud_views/snippets/pagination.html`: four hidden-label classes now come from `cv_button_class`, with the same default bytes.
- `src/crud_views/lib/button_classes.py`: `"pagination:hidden-label": "visually-hidden"`.
- `tests/test1/test_table_template.py`: `paginated_author_client`, `_table_pagination`, `_check_table_golden`, `_direction`, and three test functions.
- `tests/test1/test_card_order.py`: `_render_card_pagination_raw`, `test_card_pagination_raw_bytes`, `test_card_pagination_shared_hidden_label`, and UTF-8 IO in `_check_golden`.
- `tests/test1/test_button_classes.py`: key set and count, utility-slot case, `test_pagination_hidden_label_registry_contract`.
- `tests/test1/golden/table_pagination/page1.html`, `page2.html`: captured, then updated.
- `tests/test1/golden/card_pagination/raw_pages.json`: frozen raw card render.
- `docs/reference/buttons.md`: row, count 71, shared-pagination paragraph linking to list_view.md.

## Decisions Made

- The template-origin reference path comes from `crud_views.__file__`, not a hard-coded `src/` path. Locally it resolves to the tracked `src/crud_views/templates/crud_views/table/bootstrap5.html`. Under nox, which installs the package rather than linking it, it resolves to the installed copy of the same file, so the check holds across the CI matrix.
- The table `<nav>` gains no `mt-3`. Only its `aria-label` changes, which keeps the non-pagination markup as it was.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Template-origin path made install-mode independent**
- **Found during:** Task 1 (capture helper)
- **Issue:** Comparing `origin.name` with the repo's `src/` path would fail under nox, which installs the package non-editable and loads templates from site-packages.
- **Fix:** `TABLE_TEMPLATE_PATH` is resolved from `Path(crud_views.__file__)`, so it is the tracked file in a checkout and its installed copy in CI. The selected-name assertion and the negative upstream check are unchanged.
- **Files modified:** tests/test1/test_table_template.py
- **Verification:** the local origin resolves to the tracked src/ file, and the upstream template is rejected before golden IO.
- **Committed in:** be7daa5

---

**Total deviations:** 1 auto-fixed (1 bug). **Impact:** keeps the origin check valid across the CI matrix. No scope change.

## Issues Encountered

- As the plan intended, the class-key count drifted between `0b0f9ba` and `4b9a619`. `test_default_table_is_complete` and `test_documented_default_key_count_matches_table` failed (70 vs 71) in the two intermediate commits. The plan's review ledger explicitly kept the count/doc update in task 3. Every task-level verify command passed, and the full suite passes at plan end.
- A first draft of the registry contract test also asserted that the mode-suffixed key falls back to the base key. That was wrong: `get_button_class` reads a mode key whenever it is present. I removed the assertion; the contract under test is the W362 warning.

## Flagged Probe Assumption

PAGE-01 / unclassified stays **UNRESOLVED**. The probe supplies no classified edge beyond "review manually". Baseline chronology is enforced and evidenced above, but that does not resolve the classifier result automatically. Carry this item to the acceptance record and verification (05-03).

## User Setup Required

None. No external service configuration required.

## Next Phase Readiness

- 05-02 can extend override/edge/security coverage on the preserved block names. That includes inherited `pagination.previous`/`pagination.next` overrides on disabled ends, ellipsis ranges, prefixed/hostile queries, and escaped class values.
- 05-03 still owns the CHANGELOG Breaking entry, `docs/migrating-1.0.md` (guarded override example, D-05), `list_view.md` pagination guidance, the German catalog references, and a repeat of the chronology check above.

---
*Phase: 05-table-pagination-parity*
*Completed: 2026-10-27*

## Self-Check: PASSED

- FOUND: tests/test1/golden/table_pagination/page1.html, page2.html, tests/test1/golden/card_pagination/raw_pages.json
- FOUND (ancestors of HEAD): be7daa5, 97c9dc4, 0b0f9ba, 0275218, 7b293b8, d7142ae, 4b9a619
- commits measured: `git rev-list --count 7dcfa76..4b9a619` = 7
