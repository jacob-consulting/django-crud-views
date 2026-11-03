---
phase: 05-table-pagination-parity
plan: "03"
subsystem: docs
tags: [django-tables2, pagination, migration, changelog, i18n, gettext, acceptance]

requires:
  - phase: 05-table-pagination-parity
    provides: "05-01 accessible table pagination and pagination:hidden-label; 05-02 isolated table renderer and override regressions"
provides:
  - CHANGELOG Breaking entry and migrating-1.0.md "Table pagination overrides" section, in one commit (09549b2)
  - Executed theme recipe (myproject/table.html child) extracted from the migration guide and rendered on pages 1/2/3
  - list_view.md Pagination section; icons.md and buttons.md references covering table and card pagination
  - German catalog references for the shared pagination/previous/next msgids; compiled catalog verified current
  - 05-ACCEPTANCE.md with gate results, baseline chronology and downstream-theme follow-up
affects: [phase-07-theme-surface-freeze, verify-work]

actuals:
  tokens: 9584
  tasks: 3
  commits: 3
plan_head_before: 08463726f29d8547a316baa9e1985620406b18ca
plan_head_after: 1f77caccfa4cdeff666848777718ade46df575b5

tech-stack:
  added: []
  patterns:
    - "Documentation recipe test: extract the one django fence under a heading (_section + TEMPLATE_FENCE), check the documented path/setting agree, render it as a locmem child through the 05-02 isolated engine"
    - "Catalog refresh: snapshot the .po, run makemessages, restore the snapshot and reapply only the in-scope reference hunks, then compile and compare against an independent msgfmt build"

key-files:
  created:
    - tests/test1/test_pagination_docs.py
    - .planning/phases/05-table-pagination-parity/05-ACCEPTANCE.md
    - .planning/phases/05-table-pagination-parity/deferred-items.md
  modified:
    - CHANGELOG.md
    - docs/migrating-1.0.md
    - docs/reference/list_view.md
    - docs/reference/icons.md
    - docs/reference/buttons.md
    - src/crud_views/locale/de/LC_MESSAGES/django.po

key-decisions:
  - "05-03: the migration recipe adds rel=prev/rel=next to the enabled links, so it shows a real customization while keeping every stock hook; the test asserts rel only on enabled ends"
  - "05-03: stock icon classes in the recipe test come from a stock render (fa-solid fa-chevron-* in the test project), not hard-coded fas fa-* strings"
  - "05-03: django.mo stays byte-identical; only reference comments changed, which msgfmt omits"
  - "05-03: unrelated makemessages churn (Actions/Cancel/Filter references, POT-Creation-Date) reverted and logged in deferred-items.md"

patterns-established:
  - "Migration recipes for template overrides live under their own ### heading with exactly one unindented django fence and are executed by a test"

requirements-completed: [PAGE-01, PAGE-02, PAGE-03, PAGE-04]

coverage:
  - id: D1
    description: "Documented guarded direction-override recipe renders as myproject/table.html on pages 1/2/3 with stock li classes, disabled-anchor contract, inherited range, and honors sr-only/Bootstrap-arrow overrides with registry restoration"
    requirement: PAGE-04
    verification:
      - kind: integration
        ref: "tests/test1/test_pagination_docs.py#test_documented_pagination_direction_overrides"
        status: pass
    human_judgment: false
  - id: D2
    description: "CHANGELOG Breaking entry names guarded page-number calls, the shared key and EmptyPage, and links the migration section; paired with migrating-1.0.md in one commit"
    requirement: PAGE-04
    verification:
      - kind: unit
        ref: "tests/test1/test_pagination_docs.py#test_pagination_breaking_entry_links_migration"
        status: pass
      - kind: other
        ref: "git show --name-only 09549b2 (CHANGELOG.md and docs/migrating-1.0.md)"
        status: pass
    human_judgment: false
  - id: D3
    description: "list_view.md, icons.md and buttons.md describe pagination:hidden-label and page-previous/page-next for both paginations; strict docs build has no anchor warnings"
    requirement: PAGE-04
    verification:
      - kind: other
        ref: ".venv/bin/mkdocs build --strict"
        status: pass
    human_judgment: true
    rationale: "Prose accuracy and readability of the reference and migration text need a maintainer read; the build only proves links and anchors"
  - id: D4
    description: "German catalog references both pagination templates for pagination/previous/next; the .mo equals a fresh msgfmt build; German renders on enabled and disabled ends"
    requirement: PAGE-04
    verification:
      - kind: integration
        ref: ".venv/bin/pytest tests/test1/test_table_template.py tests/test1/test_card_order.py -q -k translated"
        status: pass
      - kind: other
        ref: "msgfmt --check-format temp compile == src/crud_views/locale/de/LC_MESSAGES/django.mo"
        status: pass
    human_judgment: false
  - id: D5
    description: "Acceptance record with gates, baseline chronology (be7daa5 before 0b0f9ba, 0275218), unchanged card goldens, the unresolved PAGE-01 classifier item and downstream follow-up"
    requirement: PAGE-01
    verification:
      - kind: other
        ref: ".planning/phases/05-table-pagination-parity/05-ACCEPTANCE.md"
        status: pass
    human_judgment: true
    rationale: "PAGE-01 classifier item is deliberately unresolved and must be judged at verification; the record itself is evidence, not a test"

duration: 9min
completed: 2026-10-27
status: complete
---

# Phase 5 Plan 03: Pagination Release, Migration and Acceptance Summary

**The table pagination change now ships with a paired CHANGELOG Breaking entry and a migration section. The section's guarded `myproject/table.html` override recipe is extracted from the guide and rendered by a test on first, middle and last pages, with and without class and icon overrides. The German catalog references both pagination templates, with the compiled catalog proven current. The acceptance record has every gate result and the baseline chronology.**

## Performance

- **Duration:** about 9 min
- **Started:** 2026-10-27T12:54:31Z
- **Completed:** 2026-10-27T13:03:21Z
- **Tasks:** 3
- **Files modified:** 9 (3 created, 6 modified)

## Accomplishments

- `docs/migrating-1.0.md` has a new `### Table pagination overrides` section, placed after the complete contract-changes
  section and before `## Silent breaks`. It explains that `pagination.previous`/`next` now run on unavailable
  directions and that an unguarded `previous_page_number`/`next_page_number` call raises `EmptyPage`. It covers the
  arrow-only versus structural copy choice and the accessible structure. It shows the `myproject/templates/myproject/table.html`
  child with `DJANGO_TABLES2_TEMPLATE = "myproject/table.html"` (read when the table class is created; `Meta.template_name`
  or an instance `template_name` takes precedence), and gives one guarded `django` recipe. A table markup bullet joins
  "CSS and tests that select on markup". The card migration history is untouched.
- The CHANGELOG has a Breaking entry for the table DOM change, the shared key and the guard requirement. It is in the
  same commit as the migration section (`09549b2`).
- `list_view.md` has a new `### Pagination` section: shared markup, the `pagination` msgid, `page-*` icons,
  `pagination:hidden-label` with the `sr-only` settings example, a class-table link, and unchanged query, prefix and
  range handling. The `icons.md` `page-*` row now covers table and card. The `buttons.md` explanation links
  `list_view.md#pagination`.
- `tests/test1/test_pagination_docs.py` (4 tests) runs the actual documented fence. Seven temporary doc mutations were
  all caught, and the guide was restored byte-identical.
- German catalog: only the three pagination reference updates were kept. `django.mo` is unchanged and equals an
  independent `msgfmt --check-format` build. The 4 German render tests pass.
- `05-ACCEPTANCE.md`: gates, tool drift, chronology, paired commit, recipe mutations, catalog procedure, the
  requirement/decision matrix, five explicit edge items plus the unresolved PAGE-01 classifier item, and the
  downstream-theme follow-up.

## Task Commits

1. **Task 1 (tracer): publish a tested direction-override migration and accurate references**: `09549b2` (docs). The
   tracer gate re-ran its verify after the commit: 60 passed, mkdocs exit 0.
2. **Task 2: refresh the shared German catalog and verify rendered translations**: `dd72032` (chore)
3. **Task 3: record baseline chronology, downstream follow-up and all project gates**: `1f77cac` (docs)

**Plan metadata:** recorded in the docs commit that follows this summary.

## Command Results

- `.venv/bin/pytest tests/test1/test_pagination_docs.py tests/test1/test_table_template.py -q`: 60 passed
- `.venv/bin/mkdocs build --strict`: exit 0, 0 warnings. The `table-pagination-overrides` and `pagination` anchors
  exist in the built site.
- `.venv/bin/pytest tests/test1/test_table_template.py tests/test1/test_card_order.py -q -k translated`: 4 passed
- The plan's `msgfmt --check-format` byte-comparison: exit 0
- `.venv/bin/pytest tests -n auto`: 3583 passed, 1 skipped (22.4 s)
- `npm --prefix . test`: 8 files, 183 tests passed
- `.venv/bin/ruff check`: passed
- `.venv/bin/ruff format --check`: **exit 1**, the 8 known pre-existing planning files. Phase-owned files: 30 already
  formatted.
- `examples/bootstrap5/manage.py check`: no issues. `test_docs_sync.py`: 36 passed.

## Files Created/Modified

- `tests/test1/test_pagination_docs.py`: `_pagination_override_recipe`, `test_documented_pagination_direction_overrides`
  and `test_pagination_breaking_entry_links_migration`
- `docs/migrating-1.0.md`: the `Table pagination overrides` section and the table markup bullet
- `CHANGELOG.md`: the Unreleased Breaking entry
- `docs/reference/list_view.md`: the `Pagination` section
- `docs/reference/icons.md`: the `page-*` row
- `docs/reference/buttons.md`: the pagination link target
- `src/crud_views/locale/de/LC_MESSAGES/django.po`: the shared msgid references
- `.planning/phases/05-table-pagination-parity/05-ACCEPTANCE.md`, `deferred-items.md`

## Decisions Made

- The recipe adds `rel="prev"`/`rel="next"` to the enabled links. That gives a copyable example a real reason to
  exist and keeps every stock hook. The test asserts the stock `li` classes and checks `rel` only on enabled ends.
- The stock icon classes come from a stock render, because the test project registers `fa-solid fa-chevron-*` rather
  than the `fas fa-*` spelling.
- `django.mo` was not regenerated, because its compiled content did not change.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical] `buttons.md` now links the new Pagination section**
- **Found during:** Task 1
- **Issue:** `buttons.md` was in read_first but not in the task's file list. Its `pagination:hidden-label` paragraph
  linked the general `list_view.md#table-with-django-tables2` section, so the three references would not have pointed
  at one pagination description.
- **Fix:** I retargeted that link to `list_view.md#pagination`. One line changed.
- **Files modified:** docs/reference/buttons.md
- **Verification:** strict mkdocs build, 0 warnings. No test pinned the old anchor.
- **Committed in:** 09549b2

**2. [Rule 2 - Missing critical] Table markup bullet under "CSS and tests that select on markup"**
- **Found during:** Task 1
- **Issue:** The migration guide listed the card's DOM change for stylesheets and tests, but not the table's.
- **Fix:** I added one bullet with the old and new table markup, linking the overrides section. The card bullet is
  unchanged.
- **Files modified:** docs/migrating-1.0.md
- **Committed in:** 09549b2

**3. [Rule 2 - Missing critical] Extra `test_pagination_breaking_entry_links_migration`**
- **Found during:** Task 1
- **Issue:** Nothing tested that the Breaking entry names the guard and links the migration anchor.
- **Fix:** I added a small test that asserts the entry's link, `pagination:hidden-label`, `has_previous`/`has_next`
  and `EmptyPage`.
- **Committed in:** 09549b2

---

**Total deviations:** 3 auto-fixed (3 missing critical). **Impact:** keeps the references and release notes
consistent. No product code changed and the scope did not grow.

## Issues Encountered

- The first recipe-test run compared `li` serializations that included lxml tails, which differ only in trailing
  whitespace. I fixed it with `with_tail=False`. A hard-coded `fas fa-chevron-left` expectation also failed, because
  the project renders `fa-solid`. The expectation is now derived from the stock render.
- `makemessages` also produced unrelated reference churn. I reverted it before compiling and logged it in
  `deferred-items.md`.
- The global `ruff format --check` stays red on 8 pre-existing planning files, as it was before this phase. The Ruff
  0.16.10 and Vitest/jsdom version drift is still present.

## Flagged Probe Assumption

PAGE-01 / unclassified stays **UNRESOLVED**, and it is carried in `05-ACCEPTANCE.md` section 7 for verification.

## User Setup Required

None. No external service configuration required.

## Next Phase Readiness

- Phase 5 is complete: 3/3 plans. It is ready for `/gsd-verify-work 05`. The PAGE-01 classifier item and the D3/D5
  prose need a human read.
- Phase 7 inherits the settled names: `pagination:hidden-label`, `page-previous`/`page-next`, and direction blocks
  that cover both states.

---
*Phase: 05-table-pagination-parity*
*Completed: 2026-10-27*

## Self-Check: PASSED

- FOUND: tests/test1/test_pagination_docs.py, .planning/phases/05-table-pagination-parity/05-ACCEPTANCE.md,
  .planning/phases/05-table-pagination-parity/deferred-items.md
- FOUND (ancestors of HEAD): 09549b2, dd72032, 1f77cac
- commits measured: `git rev-list --count 0846372..1f77cac` = 3
