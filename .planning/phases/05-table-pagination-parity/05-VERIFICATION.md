---
phase: 05-table-pagination-parity
verified: 2026-10-27T13:51:03Z
status: passed
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
  - "examples/bootstrap5/library/seed.py"
  - "examples/bootstrap5/project/features.py"
  - "examples/bootstrap5/showcase/seed.py"
  - "examples/bootstrap5/showcase/views.py"
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
covered_digest: "v4:sha256:e777aaec9308d836dc0eff3a466bfb823547ed2b3643c1e6ad21e6fe4b7dd727"
behavior_unverified: 0
overrides_applied: 0
decision_coverage:
  honored: 9
  total: 9
  not_honored: []
re_verification:
  previous_status: human_needed
  previous_score: 19/19
  previous_verified: 2026-10-27T13:35:33Z
  gaps_closed: []
  gaps_remaining: []
  regressions: []
  human_items_resolved:
    - "Visual and assistive-technology parity of table and card pagination in a browser — 05-UAT.md test 1: pass"
    - "Maintainer read of the new documentation prose — 05-UAT.md test 2: pass"
human_verification: []
---

# Phase 5: Table Pagination Parity Verification Report

**Phase Goal:** Table and card pagination look and behave the same: registry icons, hidden labels and the same accessible structure.
**Verified:** 2026-10-27T13:51:03Z
**Status:** passed
**Re-verification:** Yes — regeneration after the previous `human_needed` report (3fc43bc, 2026-10-27T13:35:33Z) went
stale and both of its human items passed UAT (`05-UAT.md`, status `complete`, 2 passed / 0 issues).

## Goal Achievement

All checks were run against the working tree at HEAD `38fd74c` on `introduce-gsd` (clean tracked tree). The previous
report had no `gaps:` section, so every must-have was re-verified at full scope rather than regression-checked.
SUMMARY and UAT claims were not used as evidence for code truths; every row cites a file, a git object or a command I
ran in this pass.

**Delta since the previous report (3fc43bc..HEAD, non-planning):** `git diff --stat` lists exactly five files: a
3-line `CHANGELOG.md` `### Internal` entry, `examples/bootstrap5/library/seed.py` (+22 authors, 25 total),
`examples/bootstrap5/showcase/seed.py` (+10 recipes, 14 total), `examples/bootstrap5/showcase/views.py`
(`RecipeCardListView.paginate_by = 6`) and `examples/bootstrap5/project/features.py` (hint text). No package source,
test, golden, catalog or `docs/` file changed. The orchestrator's description of the delta is confirmed.

### Observable Truths

Sources: ROADMAP Success Criteria (SC-1..SC-4, the contract) merged with the PLAN `must_haves.truths` of 05-01,
05-02 and 05-03. Plan truths that restate an SC are folded into that SC row.

| #  | Truth | Status | Evidence |
|----|-------|--------|----------|
| 1  | SC-1: A golden of today's paginated table is committed first, so the PR shows the markup diff (05-01 T1) | ✓ VERIFIED | `git merge-base --is-ancestor be7daa5 0b0f9ba` → YES. `git diff --name-only be7daa5^ be7daa5` = exactly `tests/test1/golden/table_pagination/page1.html`, `page2.html`, `tests/test1/test_table_template.py`. Blob IDs of `table/bootstrap5.html` (`4e37650`), `snippets/pagination.html` (`50cebe8`), `button_classes.py` (`294c794`) identical in `be7daa5^` and `be7daa5`. `git diff be7daa5 HEAD -- …/page1.html` shows `aria-label="Table navigation"` / `»` markup becoming the accessible markup. Commit order `be7daa5 → 97c9dc4 (RED) → 0b0f9ba (feat)` confirmed by `git log 7dcfa76..HEAD`. |
| 2  | SC-2: A paginated table shows `page-previous`/`page-next` registry icons with translated hidden labels, `aria-current="page"` on the active page, non-focusable disabled ends (`aria-disabled="true"`) and a translated `<nav>` label; tables2 block names still work (05-01 T2) | ✓ VERIFIED | `src/crud_views/templates/crud_views/table/bootstrap5.html` read in full (105 lines): line 63 `<nav aria-label="{% translate 'pagination' %}">`; blocks `pagination` (61), `pagination.previous` (65), `pagination.range` (77), `pagination.next` (89) preserved; `has_previous`/`has_next` guards at 66/90 *inside* the blocks; disabled branches 71-73/95-97 `<a class="page-link" aria-disabled="true">` with no `href`/`tabindex`; `cv_icon "page-previous"`/`"page-next"` at 68/72/92/96; current page line 80 `<li class="page-item active" aria-current="page"><span class="page-link">`. Goldens `page1.html`/`page2.html` at HEAD show exactly this. `test_table_pagination_accessible_structure`, `test_table_template_block_contract`, `test_table_template_block_reachable`, `test_table_pagination_direction_overrides` enumerated and passing (run below). |
| 3  | SC-3: One shared hidden-label class key (default `visually-hidden`) is read by both table and card pagination; changing it changes both (05-01 T3) | ✓ VERIFIED | `button_classes.py:88` `"pagination:hidden-label": "visually-hidden"`. Table template lines 68/72/92/96 and card snippet lines 7/11/25/29 all call `{% cv_button_class 'pagination' 'hidden-label' %}`; `templatetags/crud_views.py:525-527` `cv_button_class` → `get_button_class` (imported at :11). `test_table_pagination_shared_hidden_label` and `test_card_pagination_shared_hidden_label` (override to `sr-only`) plus both `*_hidden_label_values` matrices pass. |
| 4  | SC-4: Table and card pagination produce the same accessible structure; CHANGELOG Breaking (DOM) entry, migration bullet and `.po` files updated | ✓ VERIFIED | `test_pagination_component_parity` applies one `_assert_pagination_accessibility` helper to the real card endpoint and the table on pages 1/2/3 (passes). CHANGELOG `## Unreleased` > `### Breaking` lines 42-54 describe the table DOM change, the shared key, the guard requirement and link `docs/migrating-1.0.md#table-pagination-overrides`. `docs/migrating-1.0.md:410` `### Table pagination overrides` precedes `## Silent breaks` (:483). `django.po:277-294` references both templates for `pagination`/`previous`/`next` with `Seitennavigation`/`zurück`/`weiter`. Visual/AT parity confirmed by a human: `05-UAT.md` test 1 pass. |
| 5  | 05-01 T4: Default card render byte-identical to raw first/last-page captures made before editing the card template; the two normalized card goldens unchanged | ✓ VERIFIED | `git diff --name-only 0275218^ 0275218` = `raw_pages.json` + `test_card_order.py` only; card snippet blob `50cebe8` in both `0275218^` and `0275218`, `335e613` at HEAD (edited afterwards in `d7142ae`). `raw_pages.json` blob `2555640` in `0275218` and HEAD. Card goldens `page1.html` `db43370`, `page2.html` `19d5b8e` identical from `7dcfa76` to HEAD. `git diff --stat 7dcfa76 HEAD -- tests/test1/golden/` lists only the three added files. `test_card_pagination_raw_bytes` passes; no `CV_UPDATE_CARD_PAGINATION_RAW` branch exists outside planning history. |
| 6  | 05-01 T5: Class table has 71 default keys; documentation count and completeness test agree; pagination represented only as a utility key | ✓ VERIFIED | `test_button_classes.py:63` lists `pagination:hidden-label` in `EXPECTED_KEYS`, `:90` `assert len(EXPECTED_KEYS) == 71`; `buttons.md:145` "The default table has 71 keys"; `test_documented_default_key_count_matches_table` passes. `test_pagination_hidden_label_registry_contract` (:125-145) asserts `pagination:hidden-label:icon` yields W362. |
| 7  | 05-02: A theme overriding `pagination.previous`/`pagination.next` renders its override on enabled and disabled ends; guarded overrides call page-number methods only when available | ✓ VERIFIED | Behavior-dependent (call-count invariant). `test_table_pagination_direction_overrides` enumerated and passes in this run (spy counts 0 for unavailable, 1 for available directions over pages 1/2/3). |
| 8  | 05-02: Parity matrix includes a real middle card page (five publishers, two per page, page 2 with arrows to 1 and 3) | ✓ VERIFIED | `test_pagination_component_parity` passes (`publishers_five` fixture, `num_pages == 3`, page 2 `has_previous and has_next`, arrow hrefs decode to `[1, 3]`). |
| 9  | 05-02: `pagination.range` override still renders; stock range retains django-tables2's numeric sequence and non-navigable ellipses | ✓ VERIFIED | Template line 82 (WR-02): `<li class="page-item disabled"><a class="page-link" aria-disabled="true">{{ p }}</a></li>`; line 78 `table_page_range` filter retained. `test_table_pagination_range_override` and `test_table_pagination_range_and_empty_cases` pass. |
| 10 | 05-02: With no paginator/page or zero/one page, pagination is absent; established empty/unpaginated rendering retained | ✓ VERIFIED | Template line 62 guard `{% if table.page and table.paginator.num_pages > 1 %}`; snippet line 2 `{% if is_paginated %}`. `test_table_pagination_range_and_empty_cases` and `test_card_pagination_empty_cases` pass. |
| 11 | 05-02: Navigation links replace only the selected table's prefixed page parameter, preserving filter/sort/other-table page/repeated values | ✓ VERIFIED | Template lines 68/84/92 use `cv_querystring table.prefixed_page_field=…`; `cv_querystring` registered at `templatetags/crud_views.py:288`. `test_table_pagination_prefixed_query_preservation` passes. |
| 12 | 05-02: German renders `Seitennavigation`/`zurück`/`weiter`; decoded Unicode text and overridden `page-*` icons agree in both components | ✓ VERIFIED | `django.po:279-294` msgstr values; `msgfmt --check-format` temp build byte-equal to tracked `django.mo` (`mo equal: True`). `test_table_pagination_labels_translated`, `test_card_pagination_labels_translated`, `test_table_pagination_registry_overrides`, `test_card_pagination_arrows_from_icon_registry` pass. |
| 13 | 05-02: Omitted shared-class mapping uses `visually-hidden`; `None`/empty yield an empty class attribute without losing either translated label | ✓ VERIFIED | Behavior-dependent (settings override + restoration). `test_table_pagination_hidden_label_values`, `test_card_pagination_hidden_label_values` and `test_pagination_hidden_label_registry_contract` pass. |
| 14 | 05-02: Unicode class strings keep their code points; quotes/angle brackets are escaped into a single class attribute and never become markup | ✓ VERIFIED | Hostile-string case in both `*_hidden_label_values` matrices; neither template disables autoescape (grep of both files: no `autoescape off`). Passes. |
| 15 | 05-03: Theme authors can select the distinct `myproject/table.html` child and copy guarded previous/next blocks that render on enabled and disabled ends, honoring the shared class and registry icon overrides | ✓ VERIFIED | Behavior-dependent (cache/settings restoration). `docs/migrating-1.0.md` section contains exactly one `django` fence extending `crud_views/table/bootstrap5.html`, guards inside both blocks, stock li class lists, `cv_button_class`/`cv_icon` in both states, and the `DJANGO_TABLES2_TEMPLATE = "myproject/table.html"` python fence. `test_documented_pagination_direction_overrides` passes (renders the extracted fence on pages 1/2/3 with `sr-only`/`bi bi-arrow-*` overrides and compares registry snapshots). |
| 16 | 05-03: CHANGELOG Breaking and migration guidance explain the DOM change and the new requirement to guard page-number calls | ✓ VERIFIED | CHANGELOG lines 50-54 (`has_previous`/`has_next`, `EmptyPage`, migration link); `migrating-1.0.md` section paragraph 1 states the guard requirement and `EmptyPage`; WR-01 wording present ("also works … but it then replaces the stock template"). `test_pagination_breaking_entry_links_migration` passes. Prose accuracy confirmed by maintainer read: `05-UAT.md` test 2 pass. |
| 17 | 05-03: Buttons/list/icons references describe `pagination:hidden-label` and `page-previous`/`page-next` for both paginations; German catalog reuses `pagination`/`previous`/`next` | ✓ VERIFIED | `buttons.md:134,159-163`; `list_view.md` `### Pagination` section (shared key, `CRUD_VIEWS_BUTTON_CLASSES` example, link to `../migrating-1.0.md#table-pagination-overrides`); `icons.md:61` "table and card list pagination"; `card-list-view.md:284-285` names the shared key. `.po` adds references only, no new msgids. `mkdocs build --strict` exit 0. |
| 18 | 05-03: Documentation and locale updates serialized after implementation; Breaking and migration edits share a commit | ✓ VERIFIED | `git log 7dcfa76..HEAD`: implementation commits `be7daa5`..`72101d4` precede `09549b2` (docs) and `dd72032` (catalog). `git show --name-only 09549b2` lists `CHANGELOG.md` and `docs/migrating-1.0.md` together. |
| 19 | 05-03: Acceptance record reports actual project-gate results, both baseline commit identities, unchanged existing card goldens and the unresolved PAGE-01 classifier item | ✓ VERIFIED | `05-ACCEPTANCE.md` sections 1-8 present; section 2 line 43/50 reports the honest red `ruff format --check` (8 pre-existing planning files); section 3 lines 76-94 give `be7daa5`, `0b0f9ba`, `0275218`, blob table and card golden identities; line 190 "PAGE-01 / unclassified: UNRESOLVED". All SHAs/blobs match what I recomputed above. |

**Score:** 19/19 truths verified (0 present, behavior-unverified)

**PAGE-01 classifier item:** carried as UNRESOLVED by the plans because the probe only said "review manually". The
manual review is the deterministic chronology in row 1; treated as resolved by verification, not a gap.

**Behavior-dependent truths:** rows 7, 13 and 15 assert runtime state (spy call counts, settings override and
registry-cache restoration). Each has a named test that was enumerated (`--collect-only`) and passed in this run, so
none is PRESENT_BEHAVIOR_UNVERIFIED.

**Reliance check:** no `coincidental-reliance` flags. Row 1 relies on git history, the declared mechanism (D-06).
Row 5's byte freeze is a committed fixture compared through the production render path.

### Deferred Items

None.

### Advisory (New Scope, Unevidenced)

None. Step 7 produced no blocker candidates on any file, so the re-verification evidence gate had nothing to
downgrade.

### Required Artifacts

`gsd_run query verify.artifacts` for all three plans: exit 0 each, 12/12 passed (6 + 2 + 4). Levels 2-4 checked
manually.

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/crud_views/templates/crud_views/table/bootstrap5.html` | Accessible table markup with guards inside preserved direction blocks | ✓ VERIFIED | 105 lines; guards at 66/90 inside blocks 65-75/89-99; wired via `cv_icon`, `cv_button_class`, `cv_querystring`; rendered by the real `/author/` view in `test_table_pagination_golden` |
| `src/crud_views/templates/crud_views/snippets/pagination.html` | Shared hidden-label lookup with unchanged default bytes | ✓ VERIFIED | Four `cv_button_class` calls (7/11/25/29); raw render bytes equal frozen `raw_pages.json` |
| `src/crud_views/lib/button_classes.py` | `"pagination:hidden-label": "visually-hidden"` | ✓ VERIFIED | Line 88 (tool `contains` check passed); read through `get_button_class` |
| `tests/test1/golden/table_pagination/page1.html`, `page2.html` | Historically captured then updated table markup | ✓ VERIFIED | Blob `ec6bc06` at `be7daa5` → `868cd58` at HEAD (page1); content shows the accessible markup |
| `tests/test1/golden/card_pagination/raw_pages.json` | Frozen exact card render strings | ✓ VERIFIED | Blob `2555640` unchanged since `0275218`; two raw page strings |
| `tests/test1/test_table_template.py` | Override, range/query, empty, translation, cross-component tests | ✓ VERIFIED | 12 named phase tests enumerated; imports shared `check_golden` |
| `tests/test1/test_card_order.py` | Real-request card accessibility and shared-class edge coverage | ✓ VERIFIED | 7 named phase tests enumerated (parity, raw bytes, empty, matrix, translations, icons) |
| `docs/migrating-1.0.md` | Guarded direction override recipe and DOM guidance | ✓ VERIFIED | Section 410-482, one django fence, one python fence |
| `tests/test1/test_pagination_docs.py` | Executable check of the documented recipe | ✓ VERIFIED | 2 named tests enumerated; extracts the real fence |
| `src/crud_views/locale/de/LC_MESSAGES/django.po` | Shared msgids with refreshed table/card references | ✓ VERIFIED | References both templates; `.mo` byte-equal to fresh `msgfmt` build |
| `.planning/phases/05-table-pagination-parity/05-ACCEPTANCE.md` | Gate evidence, chronology, scope, follow-up | ✓ VERIFIED | Sections 1-8; figures cross-checked against git |
| `tests/lib/helper/golden.py` (post-plan, IN-03) | Shared normalized golden helper | ✓ VERIFIED | 16 lines, `check_golden` with explicit UTF-8 IO |

### Key Link Verification

`gsd_run query verify.key-links` reported 1/9 verified (exit 1 on all three plans). The eight "Target not
referenced in source" results are false negatives of the path-substring heuristic: Django templates reach Python
through registered tag names, test modules reference templates by template name, and `.po` → `.mo` is a build
relation. Each link was traced manually.

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `table/bootstrap5.html` | `lib/button_classes.py` | `cv_button_class 'pagination' 'hidden-label'` | ✓ WIRED | Template lines 68/72/92/96 → `templatetags/crud_views.py:525` → `get_button_class` (import at :11) |
| `snippets/pagination.html` | `lib/button_classes.py` | same | ✓ WIRED | Snippet lines 7/11/25/29, same tag |
| `table/bootstrap5.html` | `templatetags/crud_views.py` | `cv_icon` and `cv_querystring table.prefixed_page_field` | ✓ WIRED | `cv_icon` def at :513, `cv_querystring` tag at :288; used at template lines 68/72/84/92/96 |
| `test_table_template.py` | `table/bootstrap5.html` | Isolated inherited templates override dotted block names | ✓ WIRED | `test_table_pagination_direction_overrides`, `test_table_pagination_range_override`, `test_table_template_block_reachable` pass against the package template path |
| `test_table_template.py` | `templatetags/crud_views.py` | Real rendered hrefs exercise `cv_querystring` | ✓ WIRED | `test_table_pagination_prefixed_query_preservation` passes |
| `test_card_order.py` | `snippets/pagination.html` | Real card endpoint and frozen raw render | ✓ WIRED | `test_card_pagination_raw_bytes` and `test_pagination_component_parity` pass |
| `test_pagination_docs.py` | `docs/migrating-1.0.md` | Extract and render the recipe | ✓ WIRED | Tool-verified (`Target referenced in source`); test passes |
| `docs/reference/list_view.md` | `docs/migrating-1.0.md` | Migration link | ✓ WIRED | `list_view.md` Pagination section → `../migrating-1.0.md#table-pagination-overrides`; `mkdocs build --strict` exit 0 |
| `django.po` | `django.mo` | compilemessages / German render tests | ✓ WIRED | `msgfmt --check-format` build byte-equal to tracked `.mo`; `*_labels_translated` tests pass |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `table/bootstrap5.html` | hidden-label `class` | `cv_button_class` → `get_button_class` (defaults ∪ theme ∪ `CRUD_VIEWS_BUTTON_CLASSES`) | Yes — `sr-only` override changes output in tests | ✓ FLOWING |
| `table/bootstrap5.html` | arrow icons | `cv_icon "page-previous"/"page-next"` → icon registry | Yes — `CRUD_VIEWS_ICONS` override reaches output | ✓ FLOWING |
| `table/bootstrap5.html` | page hrefs | `cv_querystring table.prefixed_page_field=…` over `request.GET` | Yes — prefixed query preserved in tests | ✓ FLOWING |
| `table/bootstrap5.html` | nav/arrow labels | `{% translate %}` → gettext (`de` catalog) | Yes — German and sentinel labels render | ✓ FLOWING |
| `snippets/pagination.html` | hidden-label `class` | same `cv_button_class` path | Yes | ✓ FLOWING |

### Behavioral Spot-Checks

Run once, the four phase-owned modules only (not the full suite), with both golden-update switches unset.

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| All table/card/docs/registry pagination tests | `env -u CV_UPDATE_GOLDEN -u CV_UPDATE_CARD_PAGINATION_RAW .venv/bin/pytest tests/test1/test_table_template.py tests/test1/test_card_order.py tests/test1/test_pagination_docs.py tests/test1/test_button_classes.py -q -p no:randomly` | `162 passed in 11.70s`, exit 0 | ✓ PASS |
| 23 named phase tests exist | `pytest … --collect-only -q` filtered by name | all 23 ids listed | ✓ PASS |
| Strict docs build | `.venv/bin/mkdocs build --strict -d <scratch>` | built in 0.55 s, exit 0 | ✓ PASS |
| Compiled catalog current | `msgfmt --check-format` temp build vs `django.mo` | `mo equal: True` | ✓ PASS |
| Example app (new seed/view edits) | `.venv/bin/python examples/bootstrap5/manage.py check` | `System check identified no issues`, exit 0 | ✓ PASS |
| Baseline chronology | `git merge-base --is-ancestor be7daa5 0b0f9ba`; `git diff --name-only be7daa5^ be7daa5`; blob IDs | ancestor YES; 3 capture files; prod blobs equal | ✓ PASS |
| Documented commits exist | `gsd_run query verify.commits` over 26 hashes from the SUMMARYs | 23 commits valid; the 3 "invalid" (`294c794`, `4e37650`, `50cebe8`) are blob IDs (`git cat-file -t` → `blob`), cited as such | ✓ PASS |

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
| PAGE-04 | 05-01, 05-02, 05-03 | Same accessible structure; CHANGELOG Breaking (DOM), migration bullet, `.po` updated | ✓ SATISFIED | Truths 4, 8, 15-18; UAT test 1 (visual/AT parity) |

### Decision Coverage

`gsd_run query check.decision-coverage-verify`: 9/9 CONTEXT.md decisions (D-01..D-09) honored by shipped artifacts;
`not_honored: []`. Non-blocking gate, recorded for drift tracking.

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
|-----------|-----------|--------|---------|----------|-----------------|---------|
| `tests/test1/test_table_template.py` | PAGE-01/02/03/04 | all | 0 | post-change goldens self-generated (regression snapshots); correctness carried by semantic DOM assertions | Behavioral (spies, DOM structure, decoded hrefs) | OK |
| `tests/test1/test_card_order.py` | PAGE-03/04 | all | 0 | raw baseline captured from the pre-change template, no regenerate switch | Behavioral / Value | OK |
| `tests/test1/test_pagination_docs.py` | PAGE-04 | all | 0 | none (renders the documented fence) | Behavioral | OK |
| `tests/test1/test_button_classes.py` | PAGE-03 | all | 0 | none | Value | OK |

**Disabled tests on requirements:** 0. **Circular patterns detected:** 0 blocking (the PAGE-01 *baseline* goldens
have valid provenance: captured from the pre-change template at `be7daa5`). **Insufficient assertions:** 0.

### Anti-Patterns Found

Scanned all 22 non-planning files changed in `7dcfa76..HEAD`. No `TBD`/`FIXME`/`XXX` debt markers. No skipped or
xfail tests in the four phase test modules.

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `CHANGELOG.md` | 1091, 1222 | word `TODO` | ℹ️ Info | Historical release-note text about past TODO cleanup, not a marker in this phase's entries |
| `src/crud_views/lib/button_classes.py` | 264 | word `placeholder` | ℹ️ Info | Check hint text for E363 (`{name_class}` format placeholder), pre-existing |
| `src/crud_views/locale/de/LC_MESSAGES/django.po` | 291-292 | reference comments `table/bootstrap5.html:94` / `:98` for `next` | ℹ️ Info | The `{% translate 'next' %}` calls are now at lines 92/96 (the later WR-02 ellipsis fix removed two lines). Reference comments are not compiled (`.mo` byte-equal), so no runtime effect; will self-correct on the next `makemessages`. |

### Human Verification Required

None outstanding. The two items raised by the previous report were executed and recorded in `05-UAT.md`
(status `complete`, updated 2026-10-27T13:47:22Z, committed in `38fd74c` after the example-app seed commit
`2a6b885` the browser check relied on):

1. Visual and assistive-technology parity of table and card pagination in the example app on first/middle/last
   pages — **pass**.
2. Maintainer read of the new documentation prose (CHANGELOG Breaking, `migrating-1.0.md`, `list_view.md`,
   `buttons.md`, `icons.md`, `card-list-view.md`) — **pass**.

No PLAN declares `<human-check>` blocks, and the only post-UAT code delta is example-app seed data already covered by
`manage.py check` and by the UAT itself.

### Gaps Summary

No gaps. Every roadmap success criterion and every plan must-have resolves to VERIFIED with codebase or git
evidence, including the seven post-plan review fixes (WR-01 migration prose, WR-02 disabled ellipsis item at
template line 82, IN-01 whitespace-free range anchors, IN-02 regenerate switch removed, IN-03 shared
`tests/lib/helper/golden.py`, IN-04 single-response hidden-label helper, IN-05 `card-list-view.md`). The PAGE-01
"review manually" classifier item is closed by the deterministic chronology in truth 1. Both human verification items
from the previous report passed UAT, so the phase goal — table and card pagination look and behave the same — is
achieved both structurally (tests) and visually (human check).

Informational notes, not gaps: the global `ruff format --check` stays red on eight pre-existing planning files this
phase did not touch (reported honestly in 05-ACCEPTANCE.md); `deferred-items.md` records unrelated German-catalog
reference churn deliberately left out of scope; the `.po` `next` line references are two lines stale (comment-only).

---

_Verified: 2026-10-27T13:51:03Z_
_Verifier: Claude (gsd-verifier)_
