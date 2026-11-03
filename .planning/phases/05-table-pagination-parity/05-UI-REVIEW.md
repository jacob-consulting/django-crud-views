# Phase 05 — UI Review

**Audited:** 2026-10-27
**Baseline:** abstract 6-pillar standards (no UI-SPEC.md for this phase); parity target = `snippets/pagination.html` (card)
**Screenshots:** not captured (no dev server on localhost:3000, 5173, 8080 or 8000 — code-only audit of templates and committed goldens)
**Interaction captures:** off (workflow.ui_interaction_capture is false) — all interaction findings below are code-derived

---

## Pillar Scores

| Pillar | Score | Key Finding |
|--------|-------|-------------|
| 1. Copywriting | 3/4 | Arrow labels and nav label are translated and shared with the card; the ellipsis page token `...` has no accessible name or disabled semantics |
| 2. Visuals | 3/4 | Icon-only arrows carry hidden labels; the range anchors render padded text (`> 2 <`) that the card does not, and the ellipsis looks like a clickable page-link |
| 3. Color | 3/4 | Pure Bootstrap pagination palette, no hardcoded colors; ellipsis item misses `.disabled` so it gets the active link colour and hover state |
| 4. Typography | 4/4 | Inherits Bootstrap `.pagination` sizes/weights; no extra size or weight classes introduced |
| 5. Spacing | 2/4 | Table `<nav>` deliberately omits the `mt-3` the card `<nav>` has — the one visible layout difference left between the two paginations the phase set out to unify |
| 6. Experience Design | 3/4 | Disabled ends, `aria-current`, no stray `href`/`tabindex`, override-safe blocks all verified by tests; ellipsis is an `<a>` with neither `href` nor `aria-disabled`, and nothing was screenshot-verified |

**Overall: 18/24**

---

## Top 3 Priority Fixes

1. **Table pagination has no top margin while the card pagination has `mt-3`** — in a list page the table's `<nav>` sits flush against the table's bottom border, whereas the card list gets 1rem breathing room; the two paginations the phase was meant to bring into parity look differently placed. — Add `class="mt-3"` to the `<nav>` in `src/crud_views/templates/crud_views/table/bootstrap5.html:63` (the 05-01 decision "the table nav keeps no mt-3" was a scope choice, not a design one; Bootstrap's `.table` has `margin-bottom: 1rem` but inside `.table-container` the visual gap still differs from the card). Regenerate `tests/test1/golden/table_pagination/*.html`.
2. **Ellipsis token is a live-looking link with no accessible state** — `bootstrap5.html:82-86` renders `...` as `<li class="page-item"><a class="page-link">...</a></li>`: no `href`, no `aria-disabled`, no `.disabled` on the `li`. Visually it takes the link colour and hover background; to a screen reader it is an anchor named "...". — Render it as `<li class="page-item disabled"><span class="page-link" aria-hidden="true">…</span></li>` (or keep `<a aria-disabled="true">` with `li.disabled` for symmetry with the direction ends). `test_table_pagination_range_and_empty_cases` already pins "no href/tabindex" and would keep passing.
3. **Range anchors contain whitespace padding that the card's do not** — `bootstrap5.html:83-85` puts `{{ p }}` on its own indented line, so the golden shows `<a class="page-link" href="?page=2"> 2 </a>` while the card renders `>2<`. Inline whitespace inside an inline-block link renders as an extra space on each side, making table page numbers visibly wider than card page numbers. — Collapse to `<a class="page-link" ...>{{ p }}</a>` on one line and regenerate the table goldens.

---

## Detailed Findings

### Pillar 1: Copywriting (3/4)

Verified in `src/crud_views/templates/crud_views/table/bootstrap5.html`:
- Line 63: `aria-label="{% translate 'pagination' %}"` — replaces the old hard-coded `Table navigation` (pre-change golden at `be7daa5`), matches the card's msgid (D-03). German catalog `django.po:278-294` references the table template for `pagination`/`previous`/`next` and renders `Seitennavigation`/`zurück`/`weiter` (05-02 `test_table_pagination_labels_translated`).
- Lines 68/72/94/98: hidden `previous`/`next` labels present on enabled and disabled ends.

Findings:
- WARNING — Ellipsis `...` (line 82-86) has no accessible text beyond three ASCII periods; screen readers announce "link, dot dot dot". Use a typographic `…` with `aria-hidden` or a hidden "more pages" label.
- Minor — English msgids are lowercase (`pagination`, `previous`, `next`) and render as-is in English. As hidden text this is acceptable, but `aria-label="pagination"` on the landmark is announced as "pagination navigation" — fine, though a capitalised msgstr in an `en` catalog would read more naturally. Not a defect, carried from the card.
- Docs copy in `docs/reference/list_view.md` "Pagination" section and `docs/migrating-1.0.md` is specific and accurate to the markup; no generic labels found. `grep` for `Submit|Click Here|OK` in the pagination templates: 0 hits.

### Pillar 2: Visuals (3/4)

- Arrows come from the `page-previous`/`page-next` registry (`fa-solid fa-chevron-left/right` in the test project) with `aria-hidden="true"` and a paired hidden label — icon-only controls are correctly labelled (lines 68, 72, 94, 98). Registry overrides proven by `test_table_pagination_registry_overrides`.
- Current page is a non-link `span.page-link` inside `li.active[aria-current=page]` — clear focal state (line 80), identical to the card (snippet line 16).

Findings:
- WARNING — Whitespace inside range anchors (`> 2 <` in `tests/test1/golden/table_pagination/page1.html`) vs the card's `>2<`: table page-number cells render wider than card ones. Pre-existing from the upstream django-tables2 template, but the phase goal was parity and this was left in.
- WARNING — Ellipsis item styled as an ordinary `page-link` (no `.disabled`), so it visually promises a click it cannot deliver.
- Note — `li` class order is `previous page-item` / `next page-item` on the table but plain `page-item` on the card. Harmless for CSS, but theme selectors written for one will not match the other; documented pattern in 05-01 SUMMARY, not a visual defect.

### Pillar 3: Color (3/4)

- `grep` for hex/`rgb(`/`style=` in `table/bootstrap5.html` and `snippets/pagination.html`: 0 hits. All colour comes from Bootstrap `.pagination`, `.page-link`, `.active`, `.disabled` tokens.
- Accent usage: `.active` on exactly one item per page (current page) — correct single focal accent.

Findings:
- WARNING — Because the ellipsis `li` lacks `.disabled`, it receives `--bs-pagination-color` (link blue) and the `:hover` background instead of `--bs-pagination-disabled-color`. One non-interactive element wearing the interactive colour.

### Pillar 4: Typography (4/4)

- No `fs-*`, `fw-*`, `h*`, `small` or `lead` classes in either pagination template; all sizing comes from Bootstrap `.pagination` (1 size, 1 weight). No findings beyond confirming the contract.

### Pillar 5: Spacing (2/4)

- Card `<nav>` (snippet line 3): `class="mt-3"`. Table `<nav>` (bootstrap5.html line 63): no spacing class. 05-01 SUMMARY records this as a deliberate choice ("The table `<nav>` gains no `mt-3`") to keep non-pagination markup unchanged, and the goldens pin it.

Findings:
- BLOCKER-adjacent WARNING (scored 2) — The phase's stated goal is table/card pagination parity, and `test_pagination_component_parity` asserts structural parity, yet the only *layout* class that differs between the two navs was explicitly excluded. In a page that switches between card and table modes (Phase 3 filter toggle), the pagination jumps vertically by 1rem. This is the single most visible divergence left. Fix: add `mt-3` or, if the table's own `margin-bottom: 1rem` is judged sufficient, document why the card keeps `mt-3` and the table does not in `list_view.md#pagination` (today the docs say both "paginate with the same accessible markup" without mentioning the spacing difference).
- Minor — Range anchor inner whitespace (see Visuals) is also an unintended spacing artefact.
- `justify-content-center` on `<ul>` matches the card. No arbitrary spacing values introduced.

### Pillar 6: Experience Design (3/4)

State coverage (code-verified; tests in `tests/test1/test_table_template.py`, `tests/test1/test_card_order.py`, `tests/test1/test_pagination_docs.py`):
- First page: previous end rendered disabled (`li.disabled > a.page-link[aria-disabled=true]`, no `href`, no `tabindex`) — line 71-73; golden page1 confirms.
- Last page: next end disabled symmetrically — line 97-99; golden page2 confirms.
- Middle page: both arrows enabled with correct targets (05-02 parity matrix, page 2 of 3).
- Empty / single-page: no pagination rendered (`num_pages > 1` guard, line 62; `test_table_pagination_range_and_empty_cases`).
- Long range: ellipses rendered without `href`/`tabindex`.
- Override safety: `pagination.previous`/`.next` blocks enclose their own guards so theme overrides run on disabled ends without `EmptyPage` (D-04/D-05; `test_table_pagination_direction_overrides`, `_PageNumberSpy`). The documented migration recipe is executed by `test_documented_pagination_direction_overrides`.
- Query preservation and prefixed tables: `cv_querystring table.prefixed_page_field` keeps sort/filter/other-table params (`test_table_pagination_prefixed_query_preservation`).

Findings:
- WARNING — Ellipsis anchor lacks `aria-disabled="true"` and `li.disabled`, so it is the one non-navigable item whose state is neither announced nor styled. Direction ends got this treatment; the range did not.
- WARNING — No visual or interaction verification: no dev server was running, so focus rings on `.page-link`, hover on disabled ends, and the actual rendered gap between table and nav were not observed. Score capped at 3 on code evidence alone.
- Minor — Disabled `<a>` without `href` is not focusable (correct per D-07), but Bootstrap 5 also recommends `tabindex="-1"` for anchors styled disabled; the current markup relies on the missing `href`. Acceptable, matches the card.

Registry audit: skipped (no `components.json`; project is Django/Bootstrap, not shadcn).

---

## Files Audited

- `/home/alex/projects/alex/django-crud-views/src/crud_views/templates/crud_views/table/bootstrap5.html`
- `/home/alex/projects/alex/django-crud-views/src/crud_views/templates/crud_views/snippets/pagination.html`
- `/home/alex/projects/alex/django-crud-views/src/crud_views/lib/button_classes.py` (lines 84-88)
- `/home/alex/projects/alex/django-crud-views/src/crud_views/locale/de/LC_MESSAGES/django.po` (pagination msgids)
- `/home/alex/projects/alex/django-crud-views/tests/test1/golden/table_pagination/page1.html`, `page2.html` (current and `be7daa5` baseline)
- `/home/alex/projects/alex/django-crud-views/tests/test1/golden/card_pagination/page1.html`
- `/home/alex/projects/alex/django-crud-views/docs/reference/list_view.md` (Pagination section)
- Phase artefacts: `05-CONTEXT.md`, `05-01/02/03-SUMMARY.md`, `05-01/02/03-PLAN.md`
