---
phase: 05-table-pagination-parity
plan: "03"
type: acceptance
created: "2026-10-27"
status: evidence-recorded
---

# Phase 05: Acceptance evidence

Everything below was observed on 2026-10-27 on branch `introduce-gsd`, after the final 05-03 documentation and
catalog commits (`09549b2`, `dd72032`). No result is inferred, and no historical outcome is reused for a current
check. Each section ends with its limits.

## 1. Environment and installed-tool drift

| Tool | Installed (observed) | Declared | Disposition |
|------|----------------------|----------|-------------|
| Python | 3.12.3 (`.venv`) | matrix 3.12-3.15 | in range |
| Django | 5.2.14 | matrix 4.2 / 5.2 / 6.0 | in range; covers one matrix row only |
| django-tables2 | 3.0.0 | 2.x and 3.x supported | 3.x only exercised locally |
| Ruff | 0.16.10 | `pyproject.toml` `ruff>=0.17,<0.18` | **drift carried forward** from Phase 2/4, not changed |
| Vitest | 4.1.10 | `package.json` `^5.0.3` | **drift carried forward**, not changed |
| jsdom | 29.1.1 | `package.json` `^30.1.2` | **drift carried forward**, not changed |
| Node | v20.20.2 | `engines` `>=20` | in range |
| MkDocs | 1.6.1 | n/a | recorded |
| GNU msgfmt | 0.21 | n/a | recorded |

No manifest, lockfile or tool version was changed. The Ruff and JS results below are valid for the installed versions
only.

## 2. Final gates (D-09)

All commands ran from the repository root with `CV_UPDATE_GOLDEN` and `CV_UPDATE_CARD_PAGINATION_RAW` unset (`env -u`),
after the last product, documentation and catalog edit (HEAD `dd72032`).

| Command | Result | Elapsed | Exit |
|---------|--------|---------|------|
| `.venv/bin/pytest tests -n auto` | 3583 passed, 1 skipped | 22.4 s | 0 |
| `npm --prefix . test` | 8 test files, 183 tests passed, no unhandled errors | 2.2 s | 0 |
| `.venv/bin/mkdocs build --strict` (output to a scratch directory) | built, 0 warnings (`validation.anchors: warn` is active) | 0.7 s | 0 |
| `.venv/bin/ruff check` | All checks passed | <0.1 s | 0 |
| `.venv/bin/ruff format --check` | **8 files would be reformatted**, 667 already formatted | <0.1 s | **1** |
| `.venv/bin/python examples/bootstrap5/manage.py check` | System check identified no issues (0 silenced) | 0.4 s | 0 |
| `cd examples/bootstrap5 && ../../.venv/bin/pytest test_docs_sync.py -q` | 36 passed | 0.5 s | 0 |

The full suite grew from 3578 passed (05-02) to 3583 passed. A collection diff against `0846372` shows the five
new ids: four in `test_pagination_docs.py` and the per-file `test_no_django_bootstrap5_reference` case for it.

**`ruff format --check` is not green.** It flags the same 8 pre-existing planning files that Phases 2 and 4 recorded.
This phase touched none of them:

- `.planning/codebase/CONVENTIONS.md`
- `.planning/codebase/TESTING.md`
- `.planning/phases/01-label-mode-defaults/01-PATTERNS.md`
- `.planning/phases/01-label-mode-defaults/01-RESEARCH.md`
- `.planning/phases/02-form-key-grammar/02-RESEARCH.md`
- `.planning/phases/02-form-key-grammar/02-VERIFICATION.md`
- `.planning/research/ARCHITECTURE.md`
- `.planning/research/STACK.md`

Formatting of the files this phase changed was checked separately. `ruff format --check` on
`tests/test1/test_pagination_docs.py`, `test_table_template.py`, `test_card_order.py`, `test_button_classes.py`,
`CHANGELOG.md`, `docs/migrating-1.0.md`, `docs/reference/list_view.md`, `icons.md`, `buttons.md` and the
`05-table-pagination-parity/` planning directory reported 30 files already formatted (exit 0), this record and
`deferred-items.md` included. The global failure is
reported here. It is not fixed, and it is not counted as a pass.

Scoped suites rerun after the catalog commit: `test_pagination_docs.py`, `test_table_template.py`,
`test_card_order.py`, `test_button_classes.py`, `test_label_mode_docs.py`, `test_i18n.py` gave 181 passed (exit 0).

## 3. Baseline chronology (PAGE-01, D-06)

| Role | Commit | Parent | Files in commit |
|------|--------|--------|-----------------|
| Table baseline (before markup) | `be7daa55ddc2bb1e7bf5f93d01ddd796a4421d4d` | `7dcfa76f98ca858433dce66c1480f82eb3dbcc39` | `tests/test1/golden/table_pagination/page1.html`, `page2.html`, `tests/test1/test_table_template.py` |
| Table markup change | `0b0f9ba2ee2f677eb4b31acd892f847b38d99d1b` | `97c9dc4` (RED tests) | `table/bootstrap5.html`, `lib/button_classes.py`, both table goldens |
| Card raw-byte baseline | `0275218710e3742ed91cf1995010cec6deb0004c` | `0b0f9ba` | `tests/test1/golden/card_pagination/raw_pages.json`, `tests/test1/test_card_order.py` |
| Card class-key edit | `d7142ae` | `7b293b8` (RED test) | `snippets/pagination.html` |

The baseline commit changed only capture tests and goldens. Its production blobs equal its parent's:

| Production file | `be7daa5^` | `be7daa5` |
|-----------------|-----------|-----------|
| `src/crud_views/templates/crud_views/table/bootstrap5.html` | `4e37650` | `4e37650` |
| `src/crud_views/templates/crud_views/snippets/pagination.html` | `50cebe8` | `50cebe8` |
| `src/crud_views/lib/button_classes.py` | `294c794` | `294c794` |

The card snippet blob is `50cebe8` both in `0275218^` and in `0275218`, so the raw card bytes were frozen before the
card template changed. `raw_pages.json` is blob `2555640` both in `0275218` and in HEAD.
`test_card_pagination_raw_bytes` passes at HEAD without the update switch. The same run included both golden tests
and the docs tests: 9 passed.

The table golden changed between the baseline and HEAD (`git diff be7daa5 HEAD -- tests/test1/golden/table_pagination/`).
Both files are one line each:

- `page1.html`: `aria-label="Table navigation"` becomes `"pagination"`. A disabled
  `li.previous.page-item.disabled > a[aria-disabled=true]` appears with the `fa-solid fa-chevron-left` icon and the
  `visually-hidden` label. The current page `1` changes from a link to `li[aria-current=page] > span.page-link`.
  `next <span aria-hidden>»</span>` becomes a hidden `next` label plus the `fa-solid fa-chevron-right` icon.
- `page2.html`: the mirror image. The enabled previous gets the icon and hidden label, the current page `2` becomes a
  span, and a disabled `next` end appears where the old markup omitted it.

Existing card golden identities are unchanged from the phase start (`7dcfa76`) to HEAD:
`card_pagination/page1.html` is `db43370` and `page2.html` is `19d5b8e`. `git diff --stat 7dcfa76 HEAD --
tests/test1/golden/` lists only the three files this phase added, and nothing modified.

## 4. Paired release and migration (PAGE-04, D-05, D-08)

- `09549b2` "docs(05-03): publish tested table pagination override migration and references" contains both
  `CHANGELOG.md` (the Unreleased Breaking entry) and `docs/migrating-1.0.md` (the new `### Table pagination overrides`
  section and the table bullet under "CSS and tests that select on markup"). They share one commit.
- The Breaking entry says that `pagination.previous`/`pagination.next` now run on the first and the last page, and that
  an override must test `table.page.has_previous`/`has_next` before calling the page-number methods, or that end raises
  `EmptyPage`. It links `docs/migrating-1.0.md#table-pagination-overrides`. The link is asserted by
  `test_pagination_breaking_entry_links_migration`.
- The migration section sits after the complete "### Contract changes in templates you still override" section and
  immediately before "## Silent breaks" (asserted). It contains one unindented `django` fence and one `python` fence
  with `DJANGO_TABLES2_TEMPLATE = "myproject/table.html"`. The child is named `myproject/templates/myproject/table.html`
  and extends `crud_views/table/bootstrap5.html`.
- References: `list_view.md` has a new `### Pagination` section. `icons.md` now gives the `page-previous`/`page-next`
  row as "table and card list pagination". The existing explanation in `buttons.md` now links `list_view.md#pagination`.
  All three name `pagination:hidden-label` or the `page-*` icons for both components.
- Catalog: `pagination`, `previous` and `next` reference both templates, and their translations are unchanged
  (`Seitennavigation`, `zurück`, `weiter`). See section 6.

## 5. Executed recipe (D-05, T-05-05)

`test_documented_pagination_direction_overrides` extracts the single template fence from the migration section. It
checks that the documented child path, the startup setting and the rendered child agree on `myproject/table.html`, and
that this name differs from the extends target. It registers the fence under that name in the 05-02 isolated
locmem engine, selects it as the table's `template_name`, and renders five rows at two per page on pages 1, 2 and 3.
For each page it asserts:

- Page-number methods are spied, and unavailable directions are never asked for.
- The `li` class lists equal the stock template's.
- Enabled links decode to the right target and carry `rel`.
- Disabled ends have `aria-disabled="true"` and no `href`, `tabindex` or `rel`.
- The nav label, current page and range items equal the stock render.
- With `CRUD_VIEWS_BUTTON_CLASSES={"pagination:hidden-label": "sr-only"}` and Bootstrap arrow icons scoped by
  `override_settings`, both arrows render one `sr-only` label and one `bi bi-arrow-left`/`bi bi-arrow-right` icon in
  stock order, with no `visually-hidden` and no chevron left over.
- After the scope, the direction markup, `get_button_class` and `get_icons()` equal their earlier snapshots.

Temporary mutations of `docs/migrating-1.0.md`, each restored and checked byte-identical with `cmp`, were all caught:

| Mutation | Result |
|----------|--------|
| disabled previous anchor reads `table.page.previous_page_number` | page 1 fails (`EmptyPage`) |
| literal `visually-hidden` instead of `cv_button_class` in the disabled next anchor | page 3 fails |
| disabled next `li` without `disabled` | page 3 fails |
| literal Font Awesome chevron instead of `cv_icon` in the enabled previous anchor | pages 2 and 3 fail |
| `DJANGO_TABLES2_TEMPLATE` set to the base template name | all pages fail |
| a second `django` fence in the section | all pages fail |
| `tabindex="-1"` on the disabled next anchor | page 3 fails |

## 6. Catalog (D-03, D-08)

- Before extraction, a fresh `msgfmt --check-format` build of the tracked `.po` equaled the tracked `.mo`.
- `makemessages -l de --settings=settings_i18n` ran from `src/crud_views` with `PYTHONPATH=../..` and the repo
  interpreter. Besides the three pagination references, it changed `POT-Creation-Date`, moved and re-referenced
  `Actions`, and shifted the `Cancel`/`Filter` line references. That churn was reverted in the working file from the
  pre-extraction snapshot, and only the three reference updates were reapplied: `pagination` gains
  `table/bootstrap5.html:63`, `previous` gets `:68`/`:72`, `next` gets `:94`/`:98`.
- `compilemessages -l de` then left `django.mo` byte-identical to the pre-extraction file, as expected when only
  reference comments change. The plan's independent temporary `msgfmt --check-format` compile equals the tracked `.mo`
  (exit 0).
- German render tests (`-k translated`, table and card): 4 passed. Both components render `Seitennavigation`,
  `zurück` and `weiter` on enabled and disabled ends.
- The unrelated stale references are recorded in `deferred-items.md` and were not swept here.

## 7. Requirements, decisions and edge items

| Item | Evidence |
|------|----------|
| PAGE-01 | Section 3 baseline chronology (`be7daa5` before `0b0f9ba`) |
| PAGE-02 | 05-01 structure tests; 05-02 override, range, empty, translation and icon matrix; section 5 |
| PAGE-03 | `pagination:hidden-label` styles both components (05-01/05-02), raw card bytes unchanged (section 3) |
| PAGE-04 | Sections 4 and 6; 05-01 class-table count/doc guard |
| D-01 / D-02 | Key spelled `pagination:hidden-label` in code, docs, CHANGELOG and recipe; both templates read it |
| D-03 | Table nav label is the `pagination` msgid; catalog references both templates |
| D-04 / D-05 | Guards inside the direction blocks (05-01); disabled-end override tests (05-02); guarded recipe (section 5) |
| D-06 | Section 3 |
| D-07 | 05-01/05-02 structure tests; recipe keeps the same contract |
| D-08 | Paired commit `09549b2`; references and catalog (sections 4 and 6) |
| D-09 | Section 2 gates |

Edge items from the probe: five explicit, one unresolved, none dismissed.

- **PAGE-01 / unclassified: UNRESOLVED.** The probe supplied no classified edge beyond "review manually". The
  baseline chronology is enforced and evidenced in section 3, but that does not settle the classifier result. It stays
  open for verification.
- PAGE-02 / empty: `test_table_pagination_range_and_empty_cases` and `test_card_pagination_empty_cases` (05-02).
- PAGE-02 / encoding: decoded label text and `parse_qs` href comparison, plus exact raw card bytes (05-02).
- PAGE-03 / empty: omitted, `None` and `""` class values (`HIDDEN_LABEL_CASES`, 05-02).
- PAGE-03 / encoding: Unicode and hostile class values stay one escaped attribute (05-02).
- PAGE-04 / concurrency: documentation and locale edits ran sequentially after the implementation plans. The 05-02
  close-out `0846372` came before `09549b2` and `dd72032`, and no two writers shared a wave. Breaking and migration
  are one commit (`09549b2`). This record was written only after the paired commit, the scoped checks and every gate
  in section 2 were present.

Research and Nyquist validation were skipped for this run by request. No RESEARCH.md or VALIDATION.md was created.

## 8. Follow-up for downstream themes

Not acted on here; no downstream repository was changed. A downstream theme should:

- set `pagination:hidden-label` to its framework's screen-reader utility instead of hard-coding `visually-hidden`;
- map the `page-previous` / `page-next` registry icons instead of copying pagination markup for arrows;
- keep any structural override of `pagination.previous` / `pagination.next` it needs, and add the
  `table.page.has_previous` / `has_next` guards, because those blocks now also run at the disabled ends;
- keep the accessible structure: `aria-current="page"` on the current item, and `aria-disabled` anchors with no
  `href` or `tabindex` at the ends.

For Phase 7 (theme-surface freeze): the class key `pagination:hidden-label`, the icon names `page-previous` /
`page-next`, and the block behavior (direction blocks cover enabled and disabled states, `pagination.range` unchanged)
are settled. They should enter the stability document as they are.
