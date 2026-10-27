---
phase: 05-table-pagination-parity
verified: 2026-10-27T13:35:33Z
status: human_needed
score: 19/19 must-haves verified
covered_files:
  - ".planning/phases/05-table-pagination-parity/05-01-PLAN.md"
  - ".planning/phases/05-table-pagination-parity/05-01-SUMMARY.md"
  - ".planning/phases/05-table-pagination-parity/05-02-PLAN.md"
  - ".planning/phases/05-table-pagination-parity/05-02-SUMMARY.md"
  - ".planning/phases/05-table-pagination-parity/05-03-PLAN.md"
  - ".planning/phases/05-table-pagination-parity/05-03-SUMMARY.md"
  - "CHANGELOG.md"
  - "docs/migrating-1.0.md"
  - "docs/reference/buttons.md"
  - "docs/reference/card-list-view.md"
  - "docs/reference/icons.md"
  - "docs/reference/list_view.md"
  - "src/crud_views/lib/button_classes.py"
  - "src/crud_views/locale/de/LC_MESSAGES/django.po"
  - "src/crud_views/templates/crud_views/snippets/pagination.html"
  - "src/crud_views/templates/crud_views/table/bootstrap5.html"
  - "tests/lib/helper/golden.py"
  - "tests/test1/golden/card_pagination/raw_pages.json"
  - "tests/test1/golden/table_pagination/page1.html"
  - "tests/test1/golden/table_pagination/page2.html"
  - "tests/test1/test_button_classes.py"
  - "tests/test1/test_card_order.py"
  - "tests/test1/test_pagination_docs.py"
  - "tests/test1/test_table_template.py"
covered_digest: "v4:sha256:3c35024e375bb39a50d7fca876ba6f4f276360b3b13d505fa0f9d6f45faad87f"
behavior_unverified: 0
overrides_applied: 0
decision_coverage:
  honored: 9
  total: 9
  not_honored: []
human_verification:
  - test: "Run the example app (examples/bootstrap5), open a paginated django-tables2 list (e.g. an author list with paginate_by set low) and a paginated card list (e.g. /publisher_order/card/) in a browser. Compare the two pagination bars on a first, a middle and a last page, with and without a screen reader."
    expected: "Both bars look the same: chevron arrows at each end, no visible 'previous'/'next' text, the same Bootstrap page-item/page-link styling, the active page rendered as a non-link pill, and the unavailable end greyed out and not focusable (Tab skips it). A screen reader announces 'pagination' for the nav, 'previous'/'next' for the arrows and the current page."
    why_human: "The phase goal is that the two paginations 'look and behave the same'. Tests prove structural parity (same tags, attributes, classes and order) but cannot see rendered CSS, focus ring behavior, or assistive-technology announcements."
  - test: "Read the new prose: CHANGELOG Unreleased > Breaking (table pagination entry), docs/migrating-1.0.md '### Table pagination overrides', docs/reference/list_view.md '### Pagination', the pagination:hidden-label paragraph in docs/reference/buttons.md, the page-* row in docs/reference/icons.md and the pagination paragraph in docs/reference/card-list-view.md."
    expected: "The prose is accurate against the shipped templates (direction blocks run on disabled ends, guard has_previous/has_next, ellipsis is a disabled item, one shared key styles both components) and reads clearly for a theme author."
    why_human: "The recipe fence, the migration link and the strict docs build are tested; readability and accuracy of the surrounding explanation need a maintainer read. The 05-03 executor itself flagged this as human_judgment."
---

# Phase 5: Table Pagination Parity Verification Report

**Phase Goal:** Table and card pagination look and behave the same: registry icons, hidden labels and the same accessible structure.
**Verified:** 2026-10-27T13:35:33Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

All checks were run against the working tree at HEAD `2f1491b` on `introduce-gsd` (phase range `7dcfa76..HEAD`, which
includes the seven post-plan code-review fixes WR-01/WR-02/IN-01..IN-05). SUMMARY claims were not used as evidence;
every row below cites a file, a git object or a command I ran.

### Observable Truths

Sources: ROADMAP Success Criteria (SC-1..SC-4, the contract) merged with the PLAN `must_haves.truths` of 05-01, 05-02
and 05-03. Plan truths that restate an SC are folded into that SC row.

| #  | Truth | Status | Evidence |
|----|-------|--------|----------|
| 1  | SC-1: A golden of today's paginated table is committed first, so the PR shows the markup diff (05-01 T1) | ✓ VERIFIED | `git merge-base --is-ancestor be7daa5 0b0f9ba` succeeds. `git diff --name-only be7daa5^ be7daa5` lists only `tests/test1/golden/table_pagination/page1.html`, `page2.html`, `tests/test1/test_table_template.py`. Blob IDs of `table/bootstrap5.html` (`4e37650`), `snippets/pagination.html` (`50cebe8`) and `button_classes.py` (`294c794`) are identical in `be7daa5^` and `be7daa5`. `git diff be7daa5 HEAD -- tests/test1/golden/table_pagination/` shows the old `Table navigation` / `»` markup becoming the accessible markup. |
| 2  | SC-2: A paginated table shows `page-previous`/`page-next` registry icons with translated hidden labels, `aria-current="page"` on the active page, non-focusable disabled ends (`aria-disabled="true"`, no href/tabindex) and a translated `<nav>` label; tables2 block names still work (05-01 T2) | ✓ VERIFIED | `src/crud_views/templates/crud_views/table/bootstrap5.html` lines 61-103: `<nav aria-label="{% translate 'pagination' %}">`; blocks `pagination`, `pagination.previous`, `pagination.range`, `pagination.next` preserved; each direction block encloses its own `has_previous`/`has_next` guard; disabled branch `<a class="page-link" aria-disabled="true">` with no href; `cv_icon "page-previous"`/`"page-next"`; current page `<li class="page-item active" aria-current="page"><span class="page-link">`. Goldens `page1.html`/`page2.html` match. Tests `test_table_pagination_accessible_structure`, `test_table_template_block_contract`, `test_table_template_block_reachable`, `test_table_pagination_direction_overrides` pass (run below). |
| 3  | SC-3: One shared hidden-label class key (default `visually-hidden`) is read by both table and card pagination; changing it changes both (05-01 T3) | ✓ VERIFIED | `button_classes.py:88` `"pagination:hidden-label": "visually-hidden"`. Table template lines 68/72/92/96 and card snippet lines 7/11/25/29 all use `{% cv_button_class 'pagination' 'hidden-label' %}`. `templatetags/crud_views.py:525-527` `cv_button_class` returns `get_button_class(location, slot, mode)`. `test_table_pagination_shared_hidden_label` and `test_card_pagination_shared_hidden_label` (override to `sr-only`) pass. |
| 4  | SC-4: Table and card pagination produce the same accessible structure; CHANGELOG Breaking (DOM) entry, migration bullet and `.po` files updated | ✓ VERIFIED | `test_pagination_component_parity` applies one `_assert_pagination_accessibility` helper to the real card endpoint and the table on pages 1/2/3 (passes). CHANGELOG `## Unreleased` > `### Breaking` lines 42-54 describe the table DOM change, the shared key, the guard requirement and link `docs/migrating-1.0.md#table-pagination-overrides`. `docs/migrating-1.0.md:410` `### Table pagination overrides` (before `## Silent breaks` at :483) plus a table bullet at :189. `django.po` references `table/bootstrap5.html:63/68/72/94/98` for `pagination`/`previous`/`next` with `Seitennavigation`/`zurück`/`weiter`. |
| 5  | 05-01 T4: Default card render byte-identical to raw first/last-page captures made before editing the card template; the two normalized card goldens unchanged | ✓ VERIFIED | `raw_pages.json` blob `2555640` in `0275218` and HEAD; card snippet blob `50cebe8` in `0275218^` and `0275218` (frozen before the edit, `0275218` is an ancestor of `d7142ae`). Card goldens `page1.html` `db43370`, `page2.html` `19d5b8e` identical from `7dcfa76` to HEAD. `git diff --stat 7dcfa76 HEAD -- tests/test1/golden/` lists only the three added files. `test_card_pagination_raw_bytes` passes with no regenerate switch (IN-02: the `CV_UPDATE_CARD_PAGINATION_RAW` branch is gone; grep finds the name only in planning history). |
| 6  | 05-01 T5: Class table has 71 default keys; documentation count and completeness test agree; pagination represented only as a utility key | ✓ VERIFIED | `test_button_classes.py:89-91` asserts `len(EXPECTED_KEYS) == 71` and `set(DEFAULT_BUTTON_CLASSES) == EXPECTED_KEYS`; `buttons.md:145` "The default table has 71 keys"; `test_documented_default_key_count_matches_table` passes. `test_pagination_hidden_label_registry_contract` asserts `pagination:hidden-label:icon` yields only `crud_views.W362`. |
| 7  | 05-02: A theme overriding `pagination.previous`/`pagination.next` renders its override on enabled and disabled ends; guarded overrides call page-number methods only when available | ✓ VERIFIED | `test_table_pagination_direction_overrides` renders a locmem child through an isolated Engine rooted at the package templates (origin asserted), with `_PageNumberSpy` call counts 0 for unavailable / 1 for available directions. Passes. |
| 8  | 05-02: Parity matrix includes a real middle card page (five publishers, two per page, page 2 with arrows to 1 and 3) | ✓ VERIFIED | `test_card_order.py:351-382`: `publishers_five`, asserts `paginator.num_pages == 3`, `has_previous() and has_next()` on page 2, arrow hrefs decode to `[1, 3]` in both components. Passes. |
| 9  | 05-02: `pagination.range` override still renders; stock range retains django-tables2's numeric sequence and non-navigable ellipses | ✓ VERIFIED | Template line 82 (WR-02 fix): `<li class="page-item disabled"><a class="page-link" aria-disabled="true">{{ p }}</a></li>`. `test_table_pagination_range_override` and `test_table_pagination_range_and_empty_cases[long range]` (30 pages, `DJANGO_TABLES2_PAGE_RANGE=10`, tokens `1 ... 12-17 ... 30`, two ellipses each `disabled` + `aria-disabled="true"` + no href) pass. |
| 10 | 05-02: With no paginator/page or zero/one page, pagination is absent; established empty/unpaginated rendering retained | ✓ VERIFIED | `test_table_pagination_range_and_empty_cases` (unpaginated, 0, 1, one full page) and `test_card_pagination_empty_cases` pass; template guard `{% if table.page and table.paginator.num_pages > 1 %}` at line 62 unchanged. |
| 11 | 05-02: Navigation links replace only the selected table's prefixed page parameter, preserving filter/sort/other-table page/repeated values | ✓ VERIFIED | Template uses `cv_querystring table.prefixed_page_field=...` (lines 68, 84, 92); `cv_querystring` is `templatetags/crud_views.py:288`. `test_table_pagination_prefixed_query_preservation` (prefix `authors-`, `books-page`, `tag=a&tag=b`, hostile non-ASCII `q`) passes. |
| 12 | 05-02: German renders `Seitennavigation`/`zurück`/`weiter`; decoded Unicode text and overridden `page-*` icons agree in both components | ✓ VERIFIED | `django.po:277-294` msgstr values; `msgfmt --check-format` temp compile equals tracked `django.mo` (True). `test_table_pagination_labels_translated`, `test_card_pagination_labels_translated` (incl. sentinel gettext), `test_table_pagination_registry_overrides`, `test_card_pagination_arrows_from_icon_registry` pass. |
| 13 | 05-02: Omitted shared-class mapping uses `visually-hidden`; `None`/empty yield an empty class attribute without losing either translated label | ✓ VERIFIED | `HIDDEN_LABEL_CASES` matrix (no setting, key omitted, sr-only, None, "", Unicode, hostile) run by `test_table_pagination_hidden_label_values` and `test_card_pagination_hidden_label_values`; registry contract test covers None/"" returning "". All pass. |
| 14 | 05-02: Unicode class strings keep their code points; quotes/angle brackets are escaped into a single class attribute and never become markup | ✓ VERIFIED | `HOSTILE_CLASS = 'x" onclick="alert(1)" data-injected=\'<b>z</b>\''` case in both modules; templates run autoescaped (no `autoescape off`). Passes. |
| 15 | 05-03: Theme authors can select the distinct `myproject/table.html` child and copy guarded previous/next blocks that render on enabled and disabled ends, honoring the shared class and registry icon overrides | ✓ VERIFIED | `test_pagination_docs.py` extracts the single `django` fence under `### Table pagination overrides` via `_section`/`TEMPLATE_FENCE`, asserts child path == `DJANGO_TABLES2_TEMPLATE` != extends target, renders it on pages 1/2/3 through the 05-02 isolated engine with spies, stock li classes, `sr-only` + `bi bi-arrow-*` overrides, and compares `get_button_class`/`get_icons()` snapshots before/after (lines 147-148). Passes. |
| 16 | 05-03: CHANGELOG Breaking and migration guidance explain the DOM change and the new requirement to guard page-number calls | ✓ VERIFIED | CHANGELOG lines 50-54 (`has_previous`/`has_next`, `EmptyPage`, link); `migrating-1.0.md:417-418`. WR-01 fix present at :437-439 (same-name copy "also works ... but replaces the stock template", no "extend itself" claim). `test_pagination_breaking_entry_links_migration` passes. |
| 17 | 05-03: Buttons/list/icons references describe `pagination:hidden-label` and `page-previous`/`page-next` for both paginations; German catalog reuses `pagination`/`previous`/`next` | ✓ VERIFIED | `buttons.md:134,159-163`; `list_view.md:102-129` (`### Pagination`, links `../migrating-1.0.md#table-pagination-overrides`); `icons.md:61` "table and card list pagination"; `card-list-view.md:284` names the shared key (IN-05). `.po` has no new msgids, only added references. |
| 18 | 05-03: Documentation and locale updates serialized after implementation; Breaking and migration edits share a commit | ✓ VERIFIED | `git log 7dcfa76..HEAD`: implementation commits (`be7daa5`..`72101d4`) precede `09549b2` (docs) and `dd72032` (catalog). `git show --name-only 09549b2` contains both `CHANGELOG.md` and `docs/migrating-1.0.md`. |
| 19 | 05-03: Acceptance record reports actual project-gate results, both baseline commit identities, unchanged existing card goldens and the unresolved PAGE-01 classifier item | ✓ VERIFIED | `05-ACCEPTANCE.md` section 2 (gates incl. the honest red `ruff format --check` on 8 pre-existing planning files), section 3 (SHAs `be7daa5`, `0b0f9ba`, `0275218`, card golden blobs), section 7 (PAGE-01 / unclassified: UNRESOLVED). The record's SHAs and blob IDs match what I recomputed above. |

**Score:** 19/19 truths verified (0 present, behavior-unverified)

**PAGE-01 classifier item (carried as UNRESOLVED by 05-01/05-02/05-03):** the probe only said "review manually". That
manual review is now done: the baseline chronology is proven by deterministic git evidence (row 1). I treat the item as
resolved by this verification; it is not a gap and does not need a further human decision.

**Behavior-dependent truths:** rows 7, 13 and 15 assert runtime state (spy call counts, settings override and cache
restoration). Each has a passing named test exercising the transition, so none is left PRESENT_BEHAVIOR_UNVERIFIED.

**Reliance check:** no `coincidental-reliance` flags. Row 1 relies on git history, which is the declared mechanism
(D-06); row 5's byte freeze is a committed fixture compared by the production render path, not a fixture-only setup.

### Required Artifacts

`gsd_run query verify.artifacts` for all three plans: exit 0, 12/12 passed (6 + 2 + 4). Levels 2-4 checked manually.

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/crud_views/templates/crud_views/table/bootstrap5.html` | Accessible table markup with guards inside preserved direction blocks | ✓ VERIFIED | 105 lines; guards at 66/90 inside blocks 65-75/89-99; wired via `cv_icon`, `cv_button_class`, `cv_querystring`; rendered by the real `/author/` view (origin asserted in `_table_nav`) |
| `src/crud_views/templates/crud_views/snippets/pagination.html` | Shared hidden-label lookup with unchanged default bytes | ✓ VERIFIED | Four `cv_button_class` calls; raw render bytes equal frozen `raw_pages.json` |
| `src/crud_views/lib/button_classes.py` | `"pagination:hidden-label": "visually-hidden"` | ✓ VERIFIED | Line 88; read through `get_button_class` (line 138) |
| `tests/test1/golden/table_pagination/page1.html`, `page2.html` | Historically captured then updated table markup | ✓ VERIFIED | Blob `ec6bc06`/`e9e89c3` at `be7daa5`, `868cd58`/`236a1e8` at HEAD; IN-01 removed anchor whitespace |
| `tests/test1/golden/card_pagination/raw_pages.json` | Frozen exact card render strings | ✓ VERIFIED | Blob `2555640` unchanged since `0275218` |
| `tests/test1/test_table_template.py` | Override, range/query, empty, translation, cross-component tests | ✓ VERIFIED | 40+ test ids; `_table_nav(response)` single-response helper (IN-04); imports shared `check_golden` (IN-03) |
| `tests/test1/test_card_order.py` | Real-request card accessibility and shared-class edge coverage | ✓ VERIFIED | `publishers_five`, parity, empty, invalid-page, hidden-label matrix |
| `docs/migrating-1.0.md` | Guarded direction override recipe and DOM guidance | ✓ VERIFIED | Section at 410-482, one django fence, one python fence |
| `tests/test1/test_pagination_docs.py` | Executable check of the documented recipe | ✓ VERIFIED | 4 test ids, extracts the real fence, no hand copy |
| `src/crud_views/locale/de/LC_MESSAGES/django.po` | Shared msgids with refreshed table/card references | ✓ VERIFIED | References both templates; `.mo` byte-equal to fresh `msgfmt` build |
| `.planning/phases/05-table-pagination-parity/05-ACCEPTANCE.md` | Gate evidence, chronology, scope, follow-up | ✓ VERIFIED | Sections 1-8 present; figures cross-checked against git |
| `tests/lib/helper/golden.py` (post-plan, IN-03) | Shared normalized golden helper | ✓ VERIFIED | `check_golden` used by both test modules |

### Key Link Verification

`gsd_run query verify.key-links` reported 1/9 links verified (exit 1). The eight "Target not referenced in source"
results are false negatives: the tool looks for the target *path* inside the source file, but Django templates reference
Python through registered tag names (`{% cv_button_class %}`), not module paths, and test modules reference templates
by template name. Each link was traced manually.

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `table/bootstrap5.html` | `lib/button_classes.py` | `cv_button_class 'pagination' 'hidden-label'` | ✓ WIRED | Template lines 68/72/92/96 → `templatetags/crud_views.py:525` `cv_button_class` → `get_button_class` (imported at :11) |
| `snippets/pagination.html` | `lib/button_classes.py` | same | ✓ WIRED | Snippet lines 7/11/25/29, same tag |
| `table/bootstrap5.html` | `templatetags/crud_views.py` | `cv_icon` and `cv_querystring table.prefixed_page_field` | ✓ WIRED | `cv_icon` at :513, `cv_querystring` tag at :288; used at template lines 68/72/84/92/96 |
| `test_table_template.py` | `table/bootstrap5.html` | Isolated inherited templates override dotted block names | ✓ WIRED | `_pagination_engine` filesystem loader rooted at `TEMPLATES_ROOT`; `_render_table_pagination` asserts `base.origin.name == TABLE_TEMPLATE_PATH` |
| `test_table_template.py` | `templatetags/crud_views.py` | Real rendered hrefs exercise `cv_querystring` | ✓ WIRED | Engine `libraries={"crud_views": "crud_views.templatetags.crud_views", ...}`; hrefs parsed with `parse_qs` |
| `test_card_order.py` | `snippets/pagination.html` | Real card endpoint and frozen raw render | ✓ WIRED | `render_to_string("crud_views/snippets/pagination.html", ...)` plus `/publisher_order/card/` requests |
| `test_pagination_docs.py` | `docs/migrating-1.0.md` | Extract and render the recipe | ✓ WIRED | Tool-verified; `MIGRATING_MD` read, `TEMPLATE_FENCE.findall(section)` |
| `docs/reference/list_view.md` | `docs/migrating-1.0.md` | Migration link | ✓ WIRED | `list_view.md:129` → `../migrating-1.0.md#table-pagination-overrides`; `mkdocs build --strict` exit 0 |
| `django.po` | `django.mo` | compilemessages / German render tests | ✓ WIRED | `msgfmt --check-format` build byte-equal to tracked `.mo`; `-k translated` tests pass |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `table/bootstrap5.html` | hidden-label `class` | `cv_button_class` → `get_button_classes()` = defaults ∪ theme ∪ `CRUD_VIEWS_BUTTON_CLASSES` | Yes (override to `sr-only` changes output in tests) | ✓ FLOWING |
| `table/bootstrap5.html` | arrow icons | `cv_icon "page-previous"/"page-next"` → icon registry (`CRUD_VIEWS_ICONS` override reaches output) | Yes | ✓ FLOWING |
| `table/bootstrap5.html` | page hrefs | `cv_querystring table.prefixed_page_field=…` over `request.GET` | Yes (prefixed query preserved in tests) | ✓ FLOWING |
| `table/bootstrap5.html` | nav/arrow labels | `{% translate %}` → gettext (`de` catalog) | Yes (German and sentinel labels render) | ✓ FLOWING |
| `snippets/pagination.html` | hidden-label `class` | same `cv_button_class` path | Yes | ✓ FLOWING |

### Behavioral Spot-Checks

Run once, four phase-owned modules only (not the full suite), with `CV_UPDATE_GOLDEN` unset.

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| All table/card/docs/registry pagination tests (goldens, structure, parity, overrides, edges, recipe, count) | `env -u CV_UPDATE_GOLDEN .venv/bin/pytest tests/test1/test_table_template.py tests/test1/test_card_order.py tests/test1/test_pagination_docs.py tests/test1/test_button_classes.py -q -p no:randomly` | `162 passed in 11.75s`, exit 0 | ✓ PASS |
| Strict docs build (links/anchors for new sections) | `.venv/bin/mkdocs build --strict -d <scratch>` | built, exit 0 | ✓ PASS |
| Compiled catalog current | `msgfmt --check-format` temp build vs `django.mo` | `mo equal: True` | ✓ PASS |
| Baseline chronology | `git merge-base --is-ancestor be7daa5 0b0f9ba`; `git diff --name-only be7daa5^ be7daa5`; blob IDs | ancestor YES; 3 capture files; prod blobs equal | ✓ PASS |
| All 17 documented commits exist | `gsd_run query verify.commits …` | `all_valid: true`, 17/17 | ✓ PASS |

### Probe Execution

No `scripts/*/tests/probe-*.sh` exist and no PLAN/SUMMARY declares a probe script. Not applicable.

### Requirements Coverage

Plan frontmatter: 05-01 `[PAGE-01, PAGE-02, PAGE-03, PAGE-04]`, 05-02 `[PAGE-02, PAGE-03, PAGE-04]`, 05-03
`[PAGE-01, PAGE-02, PAGE-03, PAGE-04]`. REQUIREMENTS.md maps exactly PAGE-01..PAGE-04 to Phase 5 (lines 61-64,
125-128). No orphaned requirements.

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| PAGE-01 | 05-01, 05-03 | Golden of today's paginated table committed before the change | ✓ SATISFIED | Truth 1 (git chronology, blob IDs) |
| PAGE-02 | 05-01, 05-02, 05-03 | `table/bootstrap5.html` renders `page-previous`/`page-next` icons, translated hidden labels, `aria-current="page"`, disabled ends as `<a class="page-link" aria-disabled="true">`, translated nav label; tables2 block names kept | ✓ SATISFIED | Truths 2, 7, 9-12 |
| PAGE-03 | 05-01, 05-02, 05-03 | One shared `pagination:hidden-label` key (default `visually-hidden`) read by both paginations | ✓ SATISFIED | Truths 3, 5, 6, 13, 14 |
| PAGE-04 | 05-01, 05-02, 05-03 | Same accessible structure; CHANGELOG Breaking (DOM), migration bullet, `.po` updated | ✓ SATISFIED | Truths 4, 8, 15-18 |

### Decision Coverage

`gsd_run query check.decision-coverage-verify`: 9/9 CONTEXT.md decisions (D-01..D-09) honored by shipped artifacts;
`not_honored: []`. Non-blocking gate, recorded for drift tracking.

### Anti-Patterns Found

Scanned all 18 non-planning files changed in `7dcfa76..HEAD`. No `TBD`/`FIXME`/`XXX` debt markers. No skipped or
xfail tests in the four phase test modules.

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `CHANGELOG.md` | 1088, 1219 | word `TODO` | ℹ️ Info | Historical release-note text about past TODO cleanup, not a marker in this phase's entry |
| `src/crud_views/lib/button_classes.py` | 222, 228 | `return None` | ℹ️ Info | `_action_key_parts` legitimately returns `None` for non-action keys (pre-existing helper, exercised by the W362 check) |
| `tests/lib/helper/golden.py` | 13 | golden regenerate under `CV_UPDATE_GOLDEN` | ℹ️ Info | Test-quality note: post-change goldens are self-generated regression snapshots (circular as a correctness proof). Correctness is carried independently by the semantic assertions (truths 2, 7-14); the PAGE-01 *baseline* goldens have valid provenance (captured from the pre-change template at `be7daa5`). The raw card baseline has no regenerate switch at all. |

### Human Verification Required

#### 1. Visual and assistive-technology parity in a browser

**Test:** Run the example app (`examples/bootstrap5`), open a paginated django-tables2 list and a paginated card list
(e.g. `/publisher_order/card/`) on a first, middle and last page; tab through the pagination bars and listen with a
screen reader.
**Expected:** Both bars look identical (chevron arrows, no visible label text, same Bootstrap pill styling, active page
not a link, unavailable end greyed and skipped by Tab); the nav announces "pagination", arrows announce
"previous"/"next".
**Why human:** The phase goal says the paginations "look and behave the same". Tests prove identical structure; CSS
rendering, focus behavior and AT announcements are not observable programmatically.

#### 2. Maintainer read of the new prose

**Test:** Read the CHANGELOG Breaking entry, `docs/migrating-1.0.md` `### Table pagination overrides`,
`docs/reference/list_view.md` `### Pagination`, and the shared-key mentions in `buttons.md`, `icons.md`,
`card-list-view.md`.
**Expected:** Accurate against the shipped templates and clear for a theme author.
**Why human:** The recipe fence and link are tested and the strict build passes, but prose accuracy and readability
were explicitly flagged `human_judgment: true` by the 05-03 executor.

### Gaps Summary

No gaps. Every roadmap success criterion and every plan must-have resolves to VERIFIED with codebase or git evidence,
including the seven post-plan review fixes (WR-02 disabled ellipsis item at template line 82; IN-01 whitespace-free
range anchors in the regenerated goldens; IN-02 regenerate switch removed with `raw_pages.json` bytes unchanged; IN-03
shared `tests/lib/helper/golden.py`; IN-04 `_table_nav(response)`; IN-05 `card-list-view.md`; WR-01 migration prose).
The PAGE-01 "review manually" classifier item is closed by the deterministic chronology evidence in truth 1.

Informational notes, not gaps: the global `ruff format --check` stays red on eight pre-existing planning files that this
phase did not touch (reported honestly in 05-ACCEPTANCE.md); `deferred-items.md` records unrelated German-catalog
reference churn deliberately left out of scope; 05-UI-REVIEW.md (18/24) is advisory.

Status is `human_needed` solely because the goal's "look the same" is a visual property and the docs prose was flagged
for a maintainer read.

---

_Verified: 2026-10-27T13:35:33Z_
_Verifier: Claude (gsd-verifier)_
