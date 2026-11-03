---
phase: 05-table-pagination-parity
reviewed: 2026-10-27T13:20:00Z
depth: deep
files_reviewed: 16
files_reviewed_list:
  - CHANGELOG.md
  - docs/migrating-1.0.md
  - docs/reference/buttons.md
  - docs/reference/icons.md
  - docs/reference/list_view.md
  - src/crud_views/lib/button_classes.py
  - src/crud_views/locale/de/LC_MESSAGES/django.po
  - src/crud_views/templates/crud_views/snippets/pagination.html
  - src/crud_views/templates/crud_views/table/bootstrap5.html
  - tests/test1/golden/card_pagination/raw_pages.json
  - tests/test1/golden/table_pagination/page1.html
  - tests/test1/golden/table_pagination/page2.html
  - tests/test1/test_button_classes.py
  - tests/test1/test_card_order.py
  - tests/test1/test_pagination_docs.py
  - tests/test1/test_table_template.py
findings:
  critical: 0
  warning: 2
  info: 5
  total: 7
status: issues_found
---

# Phase 05: Code Review Report

**Reviewed:** 2026-10-27T13:20:00Z
**Depth:** deep
**Files Reviewed:** 16
**Status:** issues_found

## Summary

Reviewed the full diff against `7dcfa76` (table pagination parity): the two templates, the one-key addition to
`DEFAULT_BUTTON_CLASSES`, the German catalog, four docs pages, the CHANGELOG entry, three goldens and four test
modules. The 162 tests in the four modules pass (`pytest -n auto`), ruff check/format are clean, and the German
`.mo` is byte-for-byte in sync with the `.po` (the new `#:` references are comment-only; `pagination`,
`previous`, `next` were already translated).

Cross-file facts verified against the installed django-tables2 3.0.0 and Django 5.2.14:

- The block contract claim holds: upstream `bootstrap5.html` defines `pagination`, `pagination.previous`,
  `pagination.range`, `pagination.next`, `table`, `table.thead`, `table.tbody`, `table.tbody.row`, `table.tfoot`;
  the crud_views copy keeps all of them (plus its own `table-wrapper` and `table.tbody.empty_text`).
- `DJANGO_TABLES2_TEMPLATE` is read in `TableOptions.__init__` at class-creation time, exactly as the migration
  guide says; `cv_querystring` output is `escape()`d upstream; `cv_button_class` is an autoescaped `simple_tag`.
  The hostile-query and hostile-class tests prove both (no injection surface found).
- The `EmptyPage` claim in CHANGELOG/migration is correct: `Page.previous_page_number()` calls
  `validate_number(number - 1)`, which raises on page 1.
- The card default markup is genuinely unchanged: `raw_pages.json` was committed (0275218) before the snippet
  edit (d7142ae) and the snippet still renders those bytes.
- All five cross-document anchors used by the new text exist (`#default-table`, `#crud_views_icons`,
  `#the-class-table`, `#pagination`, `#css-and-tests-that-select-on-markup`); the `.po` line references
  (63/68/72/94/98) match the template.

UI-audit items checked against source:

- **`mt-3` on the table `<nav>`** - not a defect. No project CSS touches `.table-container` or `.table`, so
  Bootstrap's `.table { margin-bottom: 1rem }` applies; adjacent sibling margins collapse, so the card
  (`.card.mb-3` + `nav.mt-3`) and the table (`table` 1rem + `nav` 0) both show a 1rem gap. The audit's "sits
  flush" is wrong, and 05-01 recorded the omission as deliberate. Not reported.
- **Range anchor whitespace** - real but cosmetic only: `.page-link` is `display: block`, so line-edge
  whitespace is trimmed and nothing renders wider. Reported as INFO (IN-01), not WARNING.
- **Ellipsis item** - real quality defect (WR-02). The audit's screen-reader claim ("link, dot dot dot") is
  overstated - an `<a>` without `href` has the generic role - but the visual affordance problem is real.

Two warnings: one factually wrong statement in the migration guide, and the ellipsis item that this phase's
range rewrite left styled as a live link. No blockers.

## Warnings

### WR-01: Migration guide claims a same-name child template "would extend itself" - Django resolves it

**File:** `docs/migrating-1.0.md:437-439`
**Issue:** The text says: "Do not save it at `crud_views/table/bootstrap5.html` itself, where it would extend
itself." That is false. Since Django 1.9 (recursive template loading), `{% extends "crud_views/table/bootstrap5.html" %}`
inside a project template of the same name skips the current origin and resolves to the next loader's copy - the
package's own template. Verified on Django 5.2.14 with two `locmem` loaders: a same-named child containing
`{% extends "x/t.html" %}{% block b %}CHILD({{ block.super }}){% endblock %}` renders `<p>CHILD(BASE)</p>`. The
recommendation (use your own template name) is fine as a style choice, but the stated reason is wrong, and readers
who already override `crud_views/table/bootstrap5.html` in `DIRS` will doubt a setup that in fact works. The test
helper encodes the same misconception in its assertion message (`tests/test1/test_table_template.py:243`,
"a child must extend the stock template, not shadow it") - the assertion itself is harmless, the wording is not.
**Fix:** State the real trade-off instead of a non-existent failure:

```markdown
Save the override as a child template under its own name, for example
`myproject/templates/myproject/table.html`, and select it with `DJANGO_TABLES2_TEMPLATE`. A copy saved at
`crud_views/table/bootstrap5.html` in your project's `DIRS` also works (Django resolves `{% extends %}` to the
package's template), but it then replaces the stock template for every table, including ones with their own
`Meta.template_name`.
```

Adjust the helper's message to `"the test renders a child under its own name; the stock template is the base"`.

### WR-02: Ellipsis range item is a non-navigable anchor styled and structured as a live page link

**File:** `src/crud_views/templates/crud_views/table/bootstrap5.html:82-86`
**Issue:** For `p == '...'` the range renders `<li class="page-item"><a class="page-link">...</a></li>`: the
`href` is omitted, but the `li` has no `disabled` and the anchor no `aria-disabled`. Bootstrap therefore paints it
with `--bs-pagination-color` and the `:hover` background like a real page link, so it promises a click it cannot
deliver. This phase rewrote the same `for` body to add the `aria-current` branch and gave the disabled direction
ends `li.disabled` + `aria-disabled="true"` (lines 71-73, 97-99), so the ellipsis is now the single non-navigable
item in the nav without state markup - inconsistent with the contract `list_view.md:102-114` documents ("A direction
with no page is still rendered, as `<a class="page-link" aria-disabled="true">`"). Pre-existing from upstream, but
the phase's goal and its own range edit make this the place to fix it.
**Fix:**

```django
{% if table.page.number == p %}
<li class="page-item active" aria-current="page"><span class="page-link">{{ p }}</span></li>
{% elif p == '...' %}
<li class="page-item disabled"><a class="page-link" aria-disabled="true">{{ p }}</a></li>
{% else %}
<li class="page-item"><a class="page-link" href="{% cv_querystring table.prefixed_page_field=p %}">{{ p }}</a></li>
{% endif %}
```

`_assert_pagination_accessibility` keeps passing (it only asserts `href is None` for `...` tokens and `active`
absent); extend `test_table_pagination_range_and_empty_cases` (`tests/test1/test_table_template.py:554-563`) to
assert `"disabled" in classes` and `aria-disabled == "true"` for the two ellipsis items. The 2-page goldens contain
no ellipsis and need no regeneration.

## Info

### IN-01: Range anchors keep template whitespace that the card's do not

**File:** `src/crud_views/templates/crud_views/table/bootstrap5.html:83-85`
**Issue:** `{{ p }}` sits on its own indented line, so the goldens pin `<a class="page-link" href="?page=2"> 2 </a>`
while the card snippet emits `>2<`. Not visible (`.page-link` is `display: block`, so edge whitespace is trimmed),
but it is the one byte-level difference between two components the docs describe as sharing markup, and every
test needs `.strip()` to compare tokens.
**Fix:** Collapse to one line (see the WR-02 snippet) and regenerate the two goldens with
`CV_UPDATE_GOLDEN=1 pytest tests/test1/test_table_template.py -k test_table_pagination_golden`.

### IN-02: "Never regenerate" baseline ships with a regenerate switch

**File:** `tests/test1/test_card_order.py:252-267`
**Issue:** The comment says the raw card bytes were "captured once ... never regenerate it to absorb a change",
yet `test_card_pagination_raw_bytes` rewrites the file whenever `CV_UPDATE_CARD_PAGINATION_RAW` is set. The guard's
purpose (detect any drift of the stock card bytes) is defeated by a one-line env var, and the comment and code
disagree.
**Fix:** Remove the `if os.environ.get("CV_UPDATE_CARD_PAGINATION_RAW")` branch (the file is committed), or
reword the comment to "regenerate only when a card markup change is intended".

### IN-03: Golden-check helper duplicated across two test modules

**File:** `tests/test1/test_card_order.py:237-243`, `tests/test1/test_table_template.py:114-120`
**Issue:** `_check_golden` and `_check_table_golden` are the same seven lines with a different directory; the
normalisation regex (`>\s+<` then `\s+`) must stay identical for the two goldens to remain comparable, and today
nothing enforces that. `test_card_order.py` already imports eight helpers from `test_table_template.py`, so the
cross-module coupling exists either way.
**Fix:** Move one `check_golden(path: Path, element)` into `tests/lib/helper/` and call it from both modules.

### IN-04: Hidden-label test asserts on two different responses

**File:** `tests/test1/test_table_template.py:660-668`
**Issue:** `test_table_pagination_hidden_label_values` issues `paginated_author_client.get(...)` for `raw` and then
`_table_pagination(...)` for `nav`, two separate requests under the same settings. `_assert_hidden_labels` then
checks the parsed nav from one response against the raw bytes of another. Harmless today, but the test no longer
proves that one rendering has both properties.
**Fix:** Parse `nav` from `response.content` (as `test_card_pagination_hidden_label_values` does at
`test_card_order.py:355`) and drop the second request; keep the template-origin check by calling the origin
assertions on `response` directly.

### IN-05: Card list reference omits the new shared key

**File:** `docs/reference/card-list-view.md:280-284`
**Issue:** The "Paging" section explains the icon registry and the "visually hidden, translated label" but does
not say the label's class is the `pagination:hidden-label` key introduced in this phase; only `list_view.md` and
`buttons.md` do. A card-only reader finds no path from this page to the shared setting.
**Fix:** Append: "The label's class is the `pagination:hidden-label` key of the
[class table](buttons.md#the-class-table) (default `visually-hidden`), shared with the
[table pagination](list_view.md#pagination)."

---

_Reviewed: 2026-10-27T13:20:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
