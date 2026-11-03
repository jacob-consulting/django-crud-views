---
phase: 05-table-pagination-parity
plan: "02"
subsystem: testing
tags: [django-tables2, pagination, accessibility, template-blocks, i18n, escaping, regression-tests]

requires:
  - phase: 05-table-pagination-parity
    provides: "05-01 accessible table pagination, guards inside the direction blocks, shared pagination:hidden-label"
provides:
  - Isolated table-render API (_render_table_pagination over locmem children plus the package templates), reusable by 05-03's recipe test
  - Proof that inherited pagination.previous/next overrides run on disabled ends without unsafe page-number calls
  - Block-name and nesting contract for all eleven stock table blocks, each reachable through a block.super override
  - One accessibility contract (_assert_pagination_accessibility) applied to card and table on first, middle and last pages
  - Query, range, empty, translation, icon and class-value edge regressions for both components
affects: [05-03, phase-07-theme-surface-freeze]

actuals:
  tokens: 7227
  tasks: 2
  commits: 2
plan_head_before: a8f27c8bfe262fd90381851e72735ca77c852a0e
plan_head_after: 72101d47e07ec2ff51f8089b908bd496dd5cf83b

tech-stack:
  added: []
  patterns:
    - "Isolated django.template.Engine (locmem children over a filesystem loader rooted at crud_views/templates) for theme-override tests, with no global loader mutation"
    - "Page-number spies are plain callables attached after RequestConfig.configure(); a MagicMock would expose a truthy do_not_call_in_templates and the template engine would never call it"
    - "Shared cross-module assertion helpers: test_card_order.py imports the table module's contract helpers, so both components are held to one definition"

key-files:
  created: []
  modified:
    - tests/test1/test_table_template.py
    - tests/test1/test_card_order.py

key-decisions:
  - "05-02: no production change was needed. Both pagination templates, every golden and the raw card bytes are untouched (git diff a8f27c8..HEAD -- src tests/test1/golden is empty)"
  - "05-02: invalid page inputs are pinned to each framework's own semantics. On the table, django-tables2 RequestConfig maps a non-integer page to page 1 and an empty page to the last page. On the card, Django ListView maps a missing page to page 1, 'last' to the last page, and an out-of-range or non-integer page to 404"
  - "05-02: the sentinel-translation check patches django.utils.translation._trans.gettext through monkeypatch, which is the function {% translate %} reaches via gettext_lazy. It is restored automatically"

patterns-established:
  - "Theme-override test recipe: _pagination_table(rows, page, ...) followed by _render_table_pagination(table, request, child_name, {child_name: source})"
  - "Class-value edge matrix HIDDEN_LABEL_CASES (no setting, key omitted, sr-only, None, empty, Unicode, hostile) shared by table and card tests"

requirements-completed: [PAGE-02, PAGE-03, PAGE-04]

coverage:
  - id: D1
    description: "Inherited pagination.previous/next overrides render once each on first/middle/last pages, enabled and disabled; unavailable page-number methods are never called (child and stock)"
    requirement: PAGE-04
    verification:
      - kind: integration
        ref: "tests/test1/test_table_template.py#test_table_pagination_direction_overrides"
        status: pass
    human_judgment: false
  - id: D2
    description: "pagination.range override replaces only the range; all 11 stock block names and their nesting preserved; every block reachable"
    requirement: PAGE-04
    verification:
      - kind: integration
        ref: "tests/test1/test_table_template.py#test_table_pagination_range_override"
        status: pass
      - kind: unit
        ref: "tests/test1/test_table_template.py#test_table_template_block_contract"
        status: pass
      - kind: integration
        ref: "tests/test1/test_table_template.py#test_table_template_block_reachable"
        status: pass
    human_judgment: false
  - id: D3
    description: "Prefixed table links replace only authors-page; sorting, other-table page, repeated tag values and a hostile non-ASCII filter value survive URL decoding without DOM injection"
    requirement: PAGE-02
    verification:
      - kind: integration
        ref: "tests/test1/test_table_template.py#test_table_pagination_prefixed_query_preservation"
        status: pass
    human_judgment: false
  - id: D4
    description: "Long range keeps django-tables2's tokens (1 ... 12-17 ... 30) with non-navigable ellipses; unpaginated, empty and single-page tables and cards render no pagination; invalid page inputs follow framework semantics"
    requirement: PAGE-02
    verification:
      - kind: integration
        ref: "tests/test1/test_table_template.py#test_table_pagination_range_and_empty_cases"
        status: pass
      - kind: integration
        ref: "tests/test1/test_table_template.py#test_table_pagination_invalid_page_inputs"
        status: pass
      - kind: integration
        ref: "tests/test1/test_card_order.py#test_card_pagination_empty_cases"
        status: pass
      - kind: integration
        ref: "tests/test1/test_card_order.py#test_card_pagination_invalid_page_inputs"
        status: pass
    human_judgment: false
  - id: D5
    description: "Card (real three-page endpoint) and table share one accessibility structure on pages 1/2/3; page 2 has both arrows enabled with targets 1 and 3"
    requirement: PAGE-02
    verification:
      - kind: integration
        ref: "tests/test1/test_card_order.py#test_pagination_component_parity"
        status: pass
    human_judgment: false
  - id: D6
    description: "German labels (Seitennavigation/zurück/weiter) and sentinel gettext labels in both components; page-* registry icon overrides on enabled and disabled ends"
    requirement: PAGE-02
    verification:
      - kind: integration
        ref: "tests/test1/test_table_template.py#test_table_pagination_labels_translated"
        status: pass
      - kind: integration
        ref: "tests/test1/test_card_order.py#test_card_pagination_labels_translated"
        status: pass
      - kind: integration
        ref: "tests/test1/test_table_template.py#test_table_pagination_registry_overrides"
        status: pass
      - kind: integration
        ref: "tests/test1/test_card_order.py#test_card_pagination_arrows_from_icon_registry"
        status: pass
    human_judgment: false
  - id: D7
    description: "pagination:hidden-label edge values: omitted uses visually-hidden; None and empty render class=\"\" without losing labels; Unicode round-trips; hostile strings stay one escaped attribute"
    requirement: PAGE-03
    verification:
      - kind: integration
        ref: "tests/test1/test_table_template.py#test_table_pagination_hidden_label_values"
        status: pass
      - kind: integration
        ref: "tests/test1/test_card_order.py#test_card_pagination_hidden_label_values"
        status: pass
    human_judgment: false

duration: 8min
completed: 2026-10-27
status: complete
---

# Phase 5 Plan 02: Table Pagination Override and Edge Regressions Summary

**This plan adds tests only; no product file changed. Theme overrides of `pagination.previous`/`pagination.next` now provably run on disabled ends without unsafe page-number calls. The block set is pinned. Card and table pagination are held to one accessibility contract on a real three-page card endpoint. Query, range, empty, translation, icon and class-value edges are covered for both components.**

## Performance

- **Duration:** about 8 min
- **Started:** 2026-10-27T12:44:07Z
- **Completed:** 2026-10-27T12:52:00Z
- **Tasks:** 2
- **Files modified:** 2 (test modules only)

## Accomplishments

- `PaginationTable(django_tables2.Table)` with one plain `value` column. `_render_table_pagination` renders it through an isolated `Engine`: locmem children over a filesystem loader rooted at the package's templates, the `crud_views`/`django_tables2`/`i18n` libraries, an explicit request, a temporary `table.context` (restored in `finally`) and `before_render`. The base origin is asserted to be the package's own `table/bootstrap5.html`. No global loader is touched.
- Direction overrides on pages 1, 2 and 3: each guarded child block renders exactly once in its enabled or disabled form. `_PageNumberSpy` records zero `previous_page_number`/`next_page_number` calls for unavailable directions and exactly one for available ones. It shows the same for the stock blocks.
- The `pagination.range` override replaces only the range, and the stock previous/next items survive. The block contract test pins all 11 block names and their nesting. A `block.super` override of each block reaches the rendered output.
- Prefixed query handling: links on `authors-page` keep `authors-sort`, `books-page`, `tag=a&tag=b` and a hostile non-ASCII `q` exactly. Each href has a single `authors-page` value (targets 1, 1, 3, 3). No `script`/`b` element or extra attribute appears.
- Range and empty states: with `DJANGO_TABLES2_PAGE_RANGE=10` scoped, 30 pages at page 15 render exactly what `table_page_range` returns (`1 … 12–17 … 30`). Ellipses have no href or tabindex, and the current page is a span inside `li[aria-current=page].active`. Unpaginated, zero-record, one-record and one-full-page tables render no pagination, and the empty-text row is kept. Cards with `is_paginated=False`, 0, 1 or 2 records render no pagination either.
- The parity matrix uses `publishers_five` with the real card endpoint (`num_pages == 3`; page 2 has previous and next) and the isolated table renderer with five rows. Both pass `_assert_pagination_accessibility` on pages 1/2/3, with identical range tokens. Page 2 arrows decode to 1 and 3 in both.
- Translations: German labels on both ends in both components. A sentinel gettext proves the labels are translated, not literal. `bi:arrow-left`/`bi:arrow-right` registry overrides reach enabled and disabled arrows.
- The `HIDDEN_LABEL_CASES` matrix runs in both modules: no setting and an omitted key both give `visually-hidden`; `sr-only`; `None` and `""` both render `class=""` with labels and icons intact; Unicode round-trips, as decoded text and as UTF-8 bytes; the hostile string stays one attribute.
- The real card current-page and disabled-end tests now also assert the non-link span and the absence of `tabindex`.

## Task Commits

1. **Task 1 (tracer): exercise real inherited pagination overrides on both ends**, `2822ae4` (test)
2. **Task 2: close query, range, empty, encoding and accessible-parity regressions**, `72101d4` (test)

**Plan metadata:** recorded in the docs commit that follows this summary.

## Command Results

- Task 1 verify: `.venv/bin/pytest tests/test1/test_table_template.py -q`: 28 passed (was 10 before the plan). The tracer gate re-ran it after commit: 28 passed.
- Task 2 verify: `.venv/bin/pytest tests/test1/test_table_template.py tests/test1/test_card_order.py -q`: 109 passed (56 + 53).
- Full suite: `.venv/bin/pytest tests -q -n auto`: 3578 passed, 1 skipped. A seeded random-order run over the two modules plus test_i18n.py passed, so the patches leave no state that pollutes other tests.
- `ruff check .`: all checks passed. `ruff format --check src tests`: 288 files already formatted.
- Goldens and raw card bytes: `test_table_pagination_golden`, `test_card_pagination_golden` and `test_card_pagination_raw_bytes` pass without regeneration. `git diff a8f27c8..HEAD -- src tests/test1/golden` is empty.

### Non-vacuity evidence (temporary template mutations, each restored and verified with `cmp`)

| Mutation | Caught by |
|---|---|
| Availability guard moved back outside `pagination.previous` (pre-05-01 shape) | `test_table_pagination_direction_overrides[1-None-2]`, `test_table_pagination_range_override[1]` |
| Stock disabled previous anchor calls `previous_page_number` | `test_table_pagination_direction_overrides[1-None-2]` (EmptyPage propagates) |
| Ellipsis given an href | `test_table_pagination_range_and_empty_cases[long range]` |
| `{% autoescape off %}` around the table pagination block | `test_table_pagination_hidden_label_values[hostile-1/2]` |
| Range links use an unprefixed `?page=` | `test_table_pagination_prefixed_query_preservation` |
| Card current page rendered as a link | 6 card tests (parity, invalid-page inputs, current-page span) |

With autoescape off, the hostile query still did not inject: django-tables2's querystring tag escapes its own output. The class-value mutation is the one that catches a missing autoescape.

## Edge coverage lift

| Probe item | Resolution | Evidence |
|---|---|---|
| PAGE-02 empty | Resolved | `test_table_pagination_range_and_empty_cases` (4 empty cases), `test_card_pagination_empty_cases` |
| PAGE-02 encoding | Resolved | German and sentinel labels compared as decoded text; hrefs compared after `parse_qs`; raw card bytes still compared byte for byte |
| PAGE-03 empty | Resolved | `no setting`/`key omitted` give `visually-hidden`; `None`/`""` give `class=""` with labels kept |
| PAGE-03 encoding | Resolved | Unicode classes round-trip (DOM and UTF-8 bytes); the hostile class stays one escaped attribute |

## Files Created/Modified

- `tests/test1/test_table_template.py`: `PaginationTable`, `_pagination_table`, `_pagination_engine`, `_render_table_pagination`, `_PageNumberSpy`, `_assert_pagination_accessibility`, `_assert_hidden_labels`, `HIDDEN_LABEL_CASES`, `patch_sentinel_translations`, plus 10 new test functions (direction/range overrides, block contract and reachability, prefixed query, range/empty, invalid page inputs, translations, registry overrides, hidden-label values).
- `tests/test1/test_card_order.py`: `publishers_five`, `test_pagination_component_parity`, `test_card_pagination_empty_cases`, `test_card_pagination_invalid_page_inputs`, `test_card_pagination_hidden_label_values`. The translation and icon tests are now parametrized over both pages (translation adds the sentinel check). The current/disabled tests are strengthened.

## Decisions Made

- No production change was needed; every regression passed against the 05-01 templates. That matches the plan's constraint that templates change only if a test exposes a regression.
- Two extras beyond the named functions: `test_table_template_block_reachable` (the plan's "structural reachability" behavior) and `test_table_pagination_invalid_page_inputs`/`test_card_pagination_invalid_page_inputs`. The latter pin each framework's existing invalid-page semantics instead of inventing an algorithm.
- `_PageNumberSpy` is a plain class, not a `Mock`. A `Mock`'s auto-created `do_not_call_in_templates` attribute is truthy, so Django's template engine would never call it and the spy would count nothing.

## Deviations from Plan

None. The plan executed as written. The two extra test functions above are within the plan's stated behaviors (block reachability, preserving framework invalid-page semantics).

## Issues Encountered

- The first draft's single-line child templates broke the 120-column limit (E501). I reflowed them to multiline; only whitespace changed, and the markers and guards are the same.

## User Setup Required

None. No external service configuration required.

## Next Phase Readiness

- 05-03 can reuse `_pagination_table` + `_render_table_pagination(table, request, child_name, {child_name: source})` for the documented guarded-override recipe in `docs/migrating-1.0.md`.
- For 05-03's documentation pass: `docs/reference/icons.md` still lists `page-previous`/`page-next` only under "card list pagination". The table pagination uses them too since 05-01.
- PAGE-01 / unclassified stays UNRESOLVED as flagged in 05-01. Carry it to the 05-03 acceptance record.

---
*Phase: 05-table-pagination-parity*
*Completed: 2026-10-27*

## Self-Check: PASSED

- FOUND: tests/test1/test_table_template.py, tests/test1/test_card_order.py
- FOUND (ancestors of HEAD): 2822ae4, 72101d4
- commits measured: `git rev-list --count a8f27c8..72101d4` = 2
