---
phase: 05
review_cycle: 2
reviewers: [fable-review, grok-review, gemini-review]
reviewed_at: 2026-10-27T12:15:16.443213+00:00
plans_reviewed: [05-01-PLAN.md, 05-02-PLAN.md, 05-03-PLAN.md]
plan_commit: 8ef4a1b
previous_review_commit: 95163e2
models:
  fable-review: "claude-fable-5-1 (reasoning=high)"
  grok-review: "openrouter/x-ai/grok-4.7 (reasoning=high)"
  gemini-review: "openrouter/google/gemini-4-argon (reasoning=high)"
model_sources:
  fable-review: "pinned"
  grok-review: "pinned"
  gemini-review: "pinned"
---

> Note: grok-review and gemini-review share the opencode adapter; their consensus is cross-model, not cross-tool.

# Cross-AI Plan Review — Phase 05

<!-- gsd:plan-revision-conflicts:begin -->
## Plan-Revision Conflicts

<!-- gsd:plan-revision-conflicts:end -->

## Claude Review (fable-review)

# Cross-AI Plan Review — Phase 5, Cycle 2

Verified against the working tree on `introduce-gsd` (Django 5.2.14, django-tables2 3.0.0 in `.venv`). I read both pagination templates, the class registry, the template tags, the existing test modules, the docs and catalog targets, the installed django-tables2 internals, and the full cycle-1 review. I ran no tests and executed no Python (the sandbox required approval for interpreter runs), so test counts are not re-verified.

## 05-01

### Summary

Every mechanism the plan relies on exists where it says. The cycle-1 HIGH (H01) is closed correctly: django-tables2 copies `DJANGO_TABLES2_TEMPLATE` into `TableOptions` at class creation (`.venv/.../django_tables2/tables.py:121-152`), the instance property falls back to `_meta.template_name` (`tables.py:627-634`), and `ListViewTableMixin.get_table_kwargs` passes only `view` (`src/crud_views/lib/views/mixins.py:295-296`), so monkeypatching `AuthorTable._meta.template_name` is the right seam and nothing overrides it downstream. The origin assertion before golden IO makes the baseline trustworthy. The remaining items are small.

### Strengths

- **H01 fix is the correct seam.** `AuthorTable` declares no `Meta` (`tests/test1/app/views.py:56-60`); `_meta` is a `TableOptions` instance, so `monkeypatch.setattr` on it is restored per test. `response.templates` entries carry `origin.name`, so the "rendered-template origin equals tracked path" check is a real guard against the upstream template.
- **Four literal classes, byte-identical substitution.** `snippets/pagination.html:7,11,25,29` are the only `visually-hidden` literals; `cv_button_class` returns a plain autoescaped str (`src/crud_views/templatetags/crud_views.py:525-527`) and the default is `"visually-hidden"`, so the raw-byte card test can only pass if nothing else changes.
- **No W362 grammar change needed, and the W362 assertion is precise.** `button_class_check_messages` skips any key in `DEFAULT_BUTTON_CLASSES` (`src/crud_views/lib/button_classes.py:280`); `pagination:hidden-label:icon` falls to the "not a known key" branch (`:290-297`) because `_action_key_parts` admits only variant locations and form kinds (`:222-223`). The plan asserts the ID only, matching the `list:hidden-label:icon` precedent (`tests/test1/test_button_classes_checks.py:88`).
- **Count arithmetic and doc guard.** 70 today (`tests/test1/test_button_classes.py:87`; `docs/reference/buttons.md` "The default table has 70 keys"); the regex requires exactly one such sentence (`test_button_classes.py:96-97`), and the plan's placement rule keeps `### Container element and label` intact for `test_label_mode_docs.py:502-504`.
- **Raw card render context matches the real tag.** `cv_pagination` hands the snippet `page_obj`, `paginator`, `is_paginated`, `base_qs` (`templatetags/crud_views.py:429-440`); the plan's direct render uses exactly those keys.
- **`paginate_by=1` reaches the table.** Inherited from `mixins.py:293`; django-tables2 reads it with `getattr(self, "paginate_by", None)` (`django_tables2/views.py:71`).

### Concerns

- **LOW — The pre-existing test's docstring is now known to be false.** `test_list_renders_with_crud_views_table_template` (`tests/test1/test_table_template.py:20-30`) claims to render the crud_views template, but by the H01 mechanism it renders `django_tables2/bootstrap5.html` and only checks row count. The plan leaves it untouched. Not a phase defect, but a reader of the module will see two contradictory approaches side by side.
- **LOW — The ellipsis item stays an `<a>` without `href`.** `bootstrap5.html:79` renders `...` as `<a class="page-link">`; the plan preserves that. It is not focusable, so no accessibility regression, but it is the one placeholder in the new markup that is neither a link nor a `<span>` like the current page.
- **LOW — Visible text disappears.** Today the table shows the words "previous" / "next" visibly (`bootstrap5.html:70,90`); after the change they are visually hidden. This is covered by the DOM-breaking entry in principle, but 05-03 should name it (see 05-03 concerns).

### Suggestions

- Have the executor switch the old test at `test_table_template.py:21` to the new `paginated_author_client` fixture, or add a one-line comment that it exercises the upstream template. Zero production impact.
- Optional, non-blocking: render the ellipsis as `<span class="page-link">` for symmetry with the current-page span. Out of the "consistency with card" scope, so only if the maintainer wants it.

### Risk Assessment

**LOW.** The cycle-1 HIGH is closed with the right mechanism and a self-checking assertion. Everything else is verified in source.

## 05-02

### Summary

The verification matrix is grounded. The block set, the querystring node, the page-range filter and the isolated-engine reasoning all match the installed code. H02's rejection is correct: `QuerystringReplaceNode.render` builds `dict(context["request"].GET)` and encodes with `doseq=True` (`django_tables2/templatetags/django_tables2.py:58,70`), so repeated values survive and I found no contradictory evidence. The one real gap is that the plan tests only *guarded* overrides, so the breaking behaviour the phase documents (an unguarded legacy block raising on an end page) is never demonstrated.

### Strengths

- **Block contract list is exact.** `bootstrap5.html:5,7,9,28,31,40,47,61,66,76,87`.
- **A02 fix is sound.** `Table.as_html` uses the global `get_template` (`django_tables2/tables.py:447`), so rendering through `engine.get_template(...).render(Context)` is the only way a locmem child is visible to an isolated `Engine`. `before_render(request)` exists (`tables.py:418`). Configuring `RequestConfig` before attaching spies is correct since `configure` replaces `table.page`.
- **Hostile query values cannot inject.** `urlencode` percent-encodes `"`, `<`, `>`, `&` and the result is passed through `escape()` (`django_tables2.py:70`); parsing the DOM and comparing decoded values is the right assertion level.
- **Long-range case is non-vacuous.** `table_page_range` with 30 pages, range 10, page 15 yields `[1, '...', 12..17, '...', 30]` (`django_tables2.py:251-270`), so "at least one ellipsis" holds and deriving tokens from the filter avoids hard-coding.
- **A03 fix produces a real middle page.** `paginate_by = 2` (`tests/test1/app/views.py:372`) with five records gives three pages; page 2 has both directions with targets 1 and 3.
- **Sentinel-gettext has a precedent.** `tests/test1/test_alerts.py:255-285` patches `_trans.gettext` after reading the original, which is required because the attribute is lazily resolved.

### Concerns

- **MEDIUM — No test proves the breaking behaviour that D-05 and the migration text assert.** 05-02-01 spies on page-number calls inside *guarded* child blocks and asserts zero calls. Nothing renders a legacy, unguarded copy of today's block body (`bootstrap5.html:67-72` without the `if`) on page 1 and asserts `django.core.paginator.EmptyPage`. That exception is exactly what 05-03-01 tells theme authors will happen. Django re-raises it because `EmptyPage` lacks `silent_variable_failure`, but that is an inference, not evidence in the suite. Without the negative test, the Breaking entry rests on prose.
- **LOW — `PaginationTable` base class is ambiguous.** The crud_views `Table` adds an `ActionColumn` and its base `__init__` raises without `view=` (`src/crud_views/lib/table/table.py:15-20,23-34`). The plan says "plain value Column" but never says "subclass `django_tables2.Table`". If an executor picks the crud_views base, the isolated engine would also have to resolve the action column's inclusion template.
- **LOW — Invalid-page semantics are hand-waved.** "preserve framework semantics for invalid/missing page inputs" in `test_card_pagination_empty_cases` is open-ended. Django's `MultipleObjectMixin.paginate_queryset` raises `Http404` for a bad page; if the test asserts anything here it should expect 404, not an empty nav. Otherwise drop the clause.
- **LOW — `_trans.gettext` must be read before it is patched.** Not stated in the plan; the Phase 4 precedent does it (`test_alerts.py:258`). An executor who patches first gets a sentinel that is never consulted.

### Suggestions

- Add `test_legacy_unguarded_direction_override_raises_on_end_page` to 05-02-01: a locmem child whose `pagination.previous` is today's stock body with no guard, rendered on page 1 via the isolated helper, wrapped in `pytest.raises(EmptyPage)`. Mirror it for `next` on the last page. This is the executable form of the Breaking entry and lets 05-03 cite a test instead of a claim.
- State explicitly: `class PaginationTable(django_tables2.Table)` with one `tables.Column()`.
- Replace the invalid-page clause with either an explicit `Http404` assertion or nothing.

### Risk Assessment

**LOW–MEDIUM.** Nothing here touches production except on regression. The missing negative test is the only item that weakens the phase's documented contract.

## 05-03

### Summary

Docs, catalog and acceptance targets are real and the cycle-1 fixes (A04, A05, A06) are incorporated correctly. The A05 fix, however, introduces an audience mismatch: the recipe now depends on a project setting but sits under the "A downstream theme" part of the migration guide, and a theme package cannot set that setting. The catalog procedure is sound, and the msgfmt byte comparison is valid because Django's `compilemessages` runs the same `msgfmt --check-format -o` invocation.

### Strengths

- **Section and fence extraction will work.** `_section` matches a level-3 heading once and stops at `## Silent breaks` (`tests/test1/test_label_mode_docs.py:35-45`; `docs/migrating-1.0.md:405`). `TEMPLATE_FENCE` requires an unindented ```` ```django ```` or ```` ```html ```` fence (`tests/test1/test_alerts.py:23`), so a separate ```` ```python ```` settings fence is correctly excluded.
- **Catalog facts hold.** `pagination` / `previous` / `next` are at `django.po:277-291`; "Table navigation" was never a msgid; `taskfile.yaml:98` is the exact command; `settings_i18n.py` lists all five apps so scoping to `src/crud_views` is what keeps the diff local; `/usr/bin/msgfmt` exists.
- **A05 is consistent with existing docs.** `docs/reference/settings.md:244-249` and `examples/bootstrap5/project/settings.py:138` already present `DJANGO_TABLES2_TEMPLATE` as the selection seam.
- **Doc targets exist.** `CHANGELOG.md:7` `### Breaking` with the #241 card entry as a model; `docs/reference/icons.md:61` still says card-only; `docs/reference/list_view.md:71` `## Table with django-tables2` is the natural home and has no pagination text today.
- **Formatting debt is reported honestly.** `04-ACCEPTANCE.md:40,44` records the same eight-file failure; the plan requires a fresh run and forbids calling it green.

### Concerns

- **MEDIUM — The recipe's audience does not match its placement.** The new heading goes under `## A downstream theme` (`migrating-1.0.md:212`), yet the recipe requires `DJANGO_TABLES2_TEMPLATE = "myproject/table.html"`, a project setting. The reference theme ships a whole copy at the same path `crud_views/table/bootstrap5.html` (concept review ledger, `superpowers/notes/2026-10-24-icons-buttons-theme-concept-review.md:436`), which gets no inheritance at all. The plan's sentence "retained structural copies must adopt the shared key and accessible structure" is the only nod to that case. A theme author following the heading will look for a way to point the setting and find none.
- **LOW — The CHANGELOG entry needs two concrete DOM facts.** The visible words "previous" / "next" become visually hidden, and the current page changes from `<a class="page-link" href>` to `<span class="page-link">` (`bootstrap5.html:78-81`). Both break CSS and test selectors; the #241 card entry names its equivalents, this one should too.
- **LOW — The strict build does not validate the CHANGELOG link.** `CHANGELOG.md` is not in the MkDocs tree; existing entries link `docs/migrating-1.0.md#...` as repo-relative paths. The acceptance line "strict build has no broken links introduced" therefore does not cover the new anchor. The docs test should assert the heading slug exists.
- **LOW — Reverting unrelated references leaves the catalog knowingly stale.** `makemessages` will also pick up references for msgids added since 2026-10-22 (for example `gettext_noop("Actions")` at `button_classes.py:46-47`). Reverting them is in scope, but the acceptance record should list "reference comments for other msgids remain stale" as a deferred item rather than leaving it implicit.

### Suggestions

- Split the recipe's lead-in into two sentences: a project extends through a distinct child template plus the setting; a theme that ships a same-path copy gets no inheritance and must carry the guards and `pagination:hidden-label` inside the copy. If the maintainer wants to endorse Django's same-name recursive `{% extends %}` for themes, say so explicitly; otherwise say it is not the recommended path.
- Add the two DOM facts above to the CHANGELOG bullet and to the `### CSS and tests that select on markup` list (`migrating-1.0.md:180`), next to the #241 bullet at `:187`.
- In `test_pagination_docs.py`, assert `"#table-pagination-overrides"` appears in `CHANGELOG.md` and that the heading exists in the migration guide.
- Record the stale-reference decision in 05-ACCEPTANCE.md.

### Risk Assessment

**LOW.** Executable recipe plus paired commit removes the usual drift risk. The audience fix is a wording change.

---

## Cross-plan assessment and cycle-1 closure

**Cycle-1 dispositions verified.** H01 closed with the correct mechanism (`tables.py:121-152`, `:627-634`, `mixins.py:295-296`). H02 correctly rejected; I re-read the node and found list-preserving `dict(QueryDict)` plus `doseq=True` (`django_tables2.py:58,70`), so no reopening. A01 through A06 are each incorporated in the task that owns them, and none of the fixes regressed another plan. The one side effect is the A05 audience mismatch raised above.

**Dependency ordering.** Unchanged and sound: 05-01 writes production and goldens, 05-02 adds tests, 05-03 documents after behaviour is fixed. No same-wave writers. The Phase 2 rebase note is moot; the count is already 70 on this branch.

**Scope.** No creep since cycle 1. The raw JSON capture and the isolated Engine remain deliberate infrastructure choices with recorded rationale; neither affects production.

**Security.** Both trust boundaries route through existing, tested escaping (`django_tables2.py:70`; `tests/test1/test_button_classes.py:164-169`). No new input path.

**Does the phase meet its goal?** Yes. PAGE-01 through PAGE-04 and D-01 through D-09 each map to an observable artifact. The weakest link is evidentiary, not functional: the breaking override behaviour is documented and guarded against but never demonstrated by a failing render.

**Actionable findings, ranked:**

1. 05-02: add the unguarded-legacy-override negative test (MEDIUM).
2. 05-03: fix the recipe's audience statement for theme copies (MEDIUM).
3. 05-03: name the visible-text and current-page `<span>` changes in the CHANGELOG and selector list (LOW).
4. 05-02: pin `PaginationTable` to `django_tables2.Table` and clarify the invalid-page clause (LOW).
5. 05-03: cover the CHANGELOG anchor in the docs test and record the stale-reference decision (LOW).

**Overall risk: LOW–MEDIUM.** No HIGH findings remain. The plans are faithful to the codebase and ready to execute once the negative test and the recipe wording are added.

CYCLE_SUMMARY: current_high=0 current_actionable=5


---

## OpenCode Review (grok-review)

I'll verify each plan against the current templates, class table, tests, and docs before writing the review.
The plans exist. Next I’ll check the templates, class table, and tests the tasks actually depend on.
Cycle 1’s template-selection and repeated-query findings are closed against the current source. The remaining gap is that the public override recipe is not locked to the shared class key.

## 05-01

The baseline, shared key, and card byte pin are executable. `AuthorTable` still captures `DJANGO_TABLES2_TEMPLATE` at class creation (`django_tables2/tables.py:121-152`, `conftest.py:116`, `views.py:56-60`). `Table.__init__` stores `template_name=None` as `_template` (`tables.py:363-635`), so monkeypatching `AuthorTable._meta.template_name` before the request selects the tracked file, and `render_table` records that origin (`django_tables2.py:151-168`). Seventy keys today (`test_button_classes.py:87`, `buttons.md:144`); one utility key makes 71. `pagination:hidden-label:icon` is W362 as an unknown key, not an unknown mode (`button_classes.py:211-297`).

**Strengths**
- Origin is checked before golden IO, so the capture cannot be the upstream `&laquo;` template.
- Card labels stay byte-identical if the tag is inlined the way `tags/card.html:4` already does: `{% cv_button_class "card" "root" %}` renders with no extra space.
- Disabled lists are explicit (`previous page-item disabled` / `next page-item disabled`), matching enabled hooks at `bootstrap5.html:67` and `:88`.

**Concerns**
- **LOW** — The list page also has a breadcrumb `<nav>` (`tags/breadcrumb.html:2`). “The nav fragment” is ambiguous. Select `nav > ul.pagination`, as `_pagination` does (`test_card_order.py:208-212`), or the baseline commit can record the breadcrumb.
- **LOW** — `test_documented_default_key_count_matches_table` requires exactly one `The default table has (\d+) keys` match (`test_button_classes.py:96-97`). A second copy of that sentence in the new paragraph fails the task-3 gate.

**Suggestions**
- Name the pagination-ul selector in the capture helper.
- Keep the canonical count sentence unique, and extend its arithmetic clause so “71” still adds up after the new singleton row.

**Risk Assessment:** LOW. H01 is actually fixed; the rest is capture and doc-test precision.

## 05-02

The override and parity matrix matches the templates and the paginator. Direction blocks today sit inside `has_previous` / `has_next` (`bootstrap5.html:65-94`), so a child never runs on a disabled end. Moving the `{% if %}` inside the named block is the right fix. `previous_page_number` raises `EmptyPage`, which has no `silent_variable_failure` (`paginator.py:23-24`, `:214-218`), so an unguarded call fails the render; the spy still proves the call was not made. `dict(QueryDict("tag=a&tag=b"))` keeps both values, and `urlencode(..., doseq=True)` emits both (`django_tables2.py:58-70`). Do not reopen that. Three publishers at `paginate_by=2` is only two pages (`test_card_order.py:32-39`, `views.py:372`); `publishers_five` is the right fix. Invalid `authors-sort` is dropped, not raised (`tables.py:527-531`), so the prefixed href test can still preserve it.

**Strengths**
- Direct `engine.get_template().render()` avoids `RenderTableNode`’s global `get_template` (`django_tables2.py:154-168`).
- `RequestConfig` before spies matches `configure()` replacing `table.page` (`config.py:51-67`).
- Page 2 of a real three-page card response cannot be faked by a two-page endpoint.

**Concerns**
- **LOW** — `PaginationTable` must subclass `django_tables2.Table`. `crud_views.lib.table.Table` raises without a `view` and adds an actions column (`table.py:16-28`). This file’s imported `Table` is an HTML parser (`tests/lib/helper/boostrap5.py:1`), not a tables2 table.

**Suggestions**
- State that subclass in the helper sentence so the first implementation does not grow a fake view context.

**Risk Assessment:** LOW. The extension, query, range, and parity paths are specified against the code that will run.

## 05-03

Paired Breaking/migration text, the distinct child name, and catalog ordering are in the right place. `myproject/templates/myproject/table.html` plus startup `DJANGO_TABLES2_TEMPLATE = "myproject/table.html"` matches how `TableOptions` freezes the setting (`tables.py:152`, `settings.md:244-249`). `TEMPLATE_FENCE` only matches an unindented `django`/`html` fence (`test_alerts.py:23`). Inserting `### Table pagination overrides` after the contract-changes section (`migrating-1.0.md:331-403`) and before `## Silent breaks` (`:405`) does not split that list. `msgfmt` is available; restoring `POT-Creation-Date` (`django.po:9`) before compile is required because that header is compiled and `#:` lines are not.

**Strengths**
- The extracted fence is rendered on pages 1/2/3, so an unguarded `previous_page_number` fails the docs test instead of only the prose.
- Disabled class lists are the same strings as 05-01, so the recipe cannot drift from the stock template on that point.
- German `pagination` / `previous` / `next` already exist (`django.po:277-291`); this phase only refreshes references.

**Concerns**
- **MEDIUM** — The docs test does not lock the shared key or the registry icons. Acceptance checks class lists, href, and `tabindex` only. A recipe that hardcodes `visually-hidden` and omits `{% cv_icon "page-previous" %}` / `{% cv_button_class "pagination" "hidden-label" %}` still passes. The action puts the hidden-label contract on the disabled branch only, so the enabled branch can ship as a bare link. That is the copy theme authors will use, and it would miss D-02.
- **MEDIUM** — `EmptyPage` is not on the indexes those authors already read. Step zero still says only two runtime exceptions exist (`migrating-1.0.md:38-43`). The theme checklist (`:429-456`) has no pagination-block item. The step-zero link jumps to `#silent-breaks` (`:56`), which skips a heading placed immediately above it.

**Suggestions**
- In the extracted-recipe test, override `pagination:hidden-label` to `sr-only` and assert both branches render that class plus `page-previous` / `page-next` on enabled and disabled ends.
- Add one step-zero bullet and one “In a theme” checklist item that name `EmptyPage` and link `#table-pagination-overrides`.
- Say in the 05-03 action that `list_view.md` links to that heading; the key link requires it, the action text does not.

**Risk Assessment:** MEDIUM. Implementation and locale steps are sound; the published recipe can still omit the contract this phase exists to freeze.

## Cross-plan

05-01 adds the key before 05-02 and 05-03 consume it. 05-03’s renderer is the 05-02 helper, and that helper’s direct-engine path is now specified. No plan reopens H02, the table-named key, or a separate nav msgid. Card default bytes stay pinned in 05-01 and are a non-regression in 05-02. The only contract that is written in one plan and not enforced by a later test is the shared class key inside the migration recipe.

**Overall risk: MEDIUM.** Template selection, block placement, repeated query values, and the 71-key count match the source. Do not treat the phase as done until the extracted recipe fails if it hardcodes `visually-hidden` or drops the registry icons, and until `EmptyPage` is listed where the migration doc already lists runtime breaks.


---

## OpenCode Review (gemini-review)

# Cross-AI Plan Review (Cycle 2): Phase 5 — Table Pagination Parity

All three revised plans (`05-01`, `05-02`, `05-03`) were verified directly against the repository source and the Cycle 1 review ledger in `.planning/phases/05-table-pagination-parity/05-REVIEWS.md`. All Cycle 1 actionable items (`H01`, `A01`–`A06`) are cleanly resolved in the updated plans with no regressions introduced.

---

## 05-01

### Summary
Plan `05-01` is ready for execution. The Cycle 1 `H01` blocker—where `AuthorTable` (`tests/test1/app/views.py:56`) freezes `_meta.template_name = "django_tables2/bootstrap5.html"` at class definition time from `tests/test1/conftest.py:116`—is fully resolved in `05-01-01` by monkeypatching `AuthorTable._meta.template_name = "crud_views/table/bootstrap5.html"` alongside `AuthorListView.paginate_by = 1` and asserting both `response.context["table"].template_name` and the rendered template's `origin.name` in `response.templates` before any golden I/O. Concerns `A01` (explicit UTF-8 file I/O) and `A06` (explicit disabled `<li>` class lists `previous page-item disabled` / `next page-item disabled` and active `page-item active`) are also explicitly locked in.

### Strengths
- **Closure of `H01` with dual template-origin verification (`05-01-01`)**: Monkeypatching `AuthorTable._meta.template_name` in `paginated_author_client` overrides the class-creation default captured from `tests/test1/conftest.py:116`, and checking both `response.context["table"].template_name` and `Path(t.origin.name).resolve()` against `src/crud_views/templates/crud_views/table/bootstrap5.html` guarantees that `PAGE-01`'s baseline and post-change goldens cannot accidentally record the upstream `django_tables2/bootstrap5.html` template.
- **Explicit class lists and UTF-8 golden I/O (`05-01-01`, `05-01-02`, `A01`, `A06`)**: Locking enabled (`previous page-item` / `next page-item`), disabled (`previous page-item disabled` / `next page-item disabled`), and current (`page-item active` with `aria-current="page"` and `span.page-link`) class contracts in `src/crud_views/templates/crud_views/table/bootstrap5.html:66-95`, and requiring `encoding="utf-8"` across `_check_table_golden`, `raw_pages.json` (`ensure_ascii=False`), and `_check_golden` (`tests/test1/test_card_order.py:215-221`), removes locale sensitivity and class-list ambiguity.
- **Safe `buttons.md` placement and key-count synchronization (`05-01-03`)**: Adding `"pagination:hidden-label": "visually-hidden"` to `DEFAULT_BUTTON_CLASSES` (`src/crud_views/lib/button_classes.py:84-86`) increments the key count from `70` to `71` (`tests/test1/test_button_classes.py:87`, `docs/reference/buttons.md:144`), and placing the prose explanation beside `docs/reference/buttons.md:152-156` (before `### Button row as a list` at `line 163`) preserves the `### Container element and label` slice (`lines 196-225`) asserted by `tests/test1/test_label_mode_docs.py:502-504`.

### Concerns
- None. All Cycle 1 findings for `05-01` (`H01`, `A01`, `A06`, baseline chronology, and `buttons.md` section boundaries) are resolved.

### Suggestions
- None.

### Risk Assessment
**LOW** — The template-origin check, baseline-first git chronology verification, and raw-byte card regression check provide deterministic guardrails for every file modified in Wave 1.

---

## 05-02

### Summary
Plan `05-02` is well-specified and resolves all Cycle 1 concerns (`A02`, `A03`). Task `05-02-01` now specifies the exact standalone `django.template.Engine` rendering sequence—configuring `table` via `RequestConfig` before attaching `previous_page_number` / `next_page_number` spies, setting `table.context`, calling `table.before_render(request)`, and calling `engine.get_template(template_name).render(context)` directly instead of `{% render_table %}`—while Task `05-02-02` defines the `publishers_five` fixture in `tests/test1/test_card_order.py` so page 2 of `/publisher_order/card/` is a genuine middle page (`num_pages == 3`, `has_previous` and `has_next` both true) and pins `DJANGO_TABLES2_PAGE_RANGE=10` for the ellipsis test.

### Strengths
- **Complete standalone `Engine` protocol (`05-02-01`, `A02`)**: Rendering directly via `engine.get_template(template_name).render(context)` with `Context({"table": table, "request": request}, autoescape=True)`, `table.context` cleanup, and registered `crud_views`, `django_tables2`, and `i18n` libraries avoids `RenderTableNode`'s global `get_template()` lookup while still exercising `{% extends "crud_views/table/bootstrap5.html" %}`, `{% cv_querystring %}` (`src/crud_views/templatetags/crud_views.py:289-296`), and `table_page_range`.
- **True three-page parity matrix (`05-02-02`, `A03`)**: Extending `publishers` (`tests/test1/test_card_order.py:32-39`, 3 rows) with `publishers_five` (adding `Delta` and `Echo` under `PublisherOrderCardListView.paginate_by = 2` at `tests/test1/app/views.py:372`) produces 3 real pages on `/publisher_order/card/` without disturbing the existing 3-record card goldens (`tests/test1/test_card_order.py:224-227`).
- **Comprehensive edge and security verification (`05-02-02`)**: Covers prefixed multi-table query preservation (`T-05-01`, `T-05-04`), `DJANGO_TABLES2_PAGE_RANGE=10` ellipsis rendering, German `translation.override("de")` plus `_trans.gettext` sentinel patching (`src/crud_views/locale/de/LC_MESSAGES/django.po:277-291`, `tests/test1/test_alerts.py:208-216`), and `pagination:hidden-label` attribute escaping (`T-05-02`).

### Concerns
- None. All Cycle 1 findings for `05-02` (`A02`, `A03`, active class parity, and `DJANGO_TABLES2_PAGE_RANGE` pinning) are resolved.

### Suggestions
- None.

### Risk Assessment
**LOW** — All test seams, fixtures, and template rendering mechanics are explicitly specified and verified against the codebase.

---

## 05-03

### Summary
Plan `05-03` cleanly resolves all Cycle 1 documentation and localization concerns (`A04`, `A05`, `A06`). Task `05-03-01` places `### Table pagination overrides` immediately before `## Silent breaks` (`docs/migrating-1.0.md:405`), names a distinct child template (`myproject/templates/myproject/table.html`) selected via `DJANGO_TABLES2_TEMPLATE = "myproject/table.html"`, matches the exact `05-01` enabled/disabled `<li>` class lists, and tests that extracted ` ```django ` fence through `05-02`'s isolated renderer in `tests/test1/test_pagination_docs.py`. Task `05-03-02` restores `makemessages` header/rewrap churn in the working `src/crud_views/locale/de/LC_MESSAGES/django.po` file before running `compilemessages -l de` and verifies byte-for-byte `.mo` freshness via `msgfmt --check-format`.

### Strengths
- **Executable child-template recipe and startup setting guidance (`05-03-01`, `A05`, `A06`)**: Reusing `_section` (`tests/test1/test_label_mode_docs.py:35`) and `TEMPLATE_FENCE` (`tests/test1/test_alerts.py:23`, which matches ` ```django ` while ignoring any ` ```python ` setting fence) to extract and render `myproject/table.html` across pages 1, 2, and 3 proves that the documented `table.page.has_previous` / `table.page.has_next` guards prevent `EmptyPage` on disabled ends (`T-05-05`).
- **Working-tree `.po` hygiene and independent `.mo` byte verification (`05-03-02`, `A04`)**: Restoring `POT-Creation-Date` (`src/crud_views/locale/de/LC_MESSAGES/django.po:9`) and unrelated reference churn in the working `.po` file *before* running `compilemessages -l de`, followed by an automated `msgfmt --check-format` byte comparison against `src/crud_views/locale/de/LC_MESSAGES/django.mo`, prevents stale or header-dirtied binary catalog diffs.
- **Complete quality-gate and provenance accounting (`05-03-03`)**: Explicitly records the baseline commit SHAs, unchanged card golden blobs, unresolved `PAGE-01` classifier item, and the known pre-existing 8-file `.planning/` `ruff format --check` status alongside clean formatting on all Phase 5 files.

### Concerns
- None. All Cycle 1 findings for `05-03` (`A04`, `A05`, `A06`, fence extraction, and section placement) are resolved.

### Suggestions
- None.

### Risk Assessment
**LOW** — Documentation, locale updates, and acceptance gates are tightly scoped and backed by automated verification (`test_pagination_docs.py`, `mkdocs build --strict`, `msgfmt --check-format`, and `examples/bootstrap5/test_docs_sync.py`).

---

## Cross-Plan Summary & Overall Risk Assessment

- **Cycle 1 Convergence**: All 1 HIGH (`H01`) and 6 MEDIUM (`A01`–`A06`) actionable items from Cycle 1 have been addressed in `05-01-PLAN.md`, `05-02-PLAN.md`, and `05-03-PLAN.md` without introducing regressions or scope drift.
- **Wave & Dependency Ordering**: Wave 1 (`05-01`) → Wave 2 (`05-02`) → Wave 3 (`05-03`) has clean file ownership and artifact handoffs (`_render_table_pagination` and `PaginationTable` from `05-02` reused by `05-03-01` in `test_pagination_docs.py`).
- **Overall Risk**: **LOW** — The plans are ready to execute.


---

## Consensus Summary

All three configured reviewers completed source-cited reviews of all three current plans. Each explicitly closes the cycle-1 template-selection blocker and the six actionable refinements after revision `8ef4a1b`. No reviewer raises a new HIGH. Gemini finds no remaining issues; Fable and Grok request additional test/documentation precision. Their proposed refinements are evaluated below against current task text and recorded deferrals rather than counted mechanically.

### Agreed Strengths

- The scoped `AuthorTable._meta.template_name` patch selects the intended template, and the required response-template origin assertion protects baseline provenance.
- Explicit UTF-8 I/O, unchanged raw/default card output, the 71-key utility contract and exact direction classes are coherent.
- The isolated Engine now has a complete direct-render protocol; five real publisher records provide the required middle page.
- Working-file PO cleanup precedes compilation, independent msgfmt comparison checks the final catalog, and the child-template selection avoids self-inheritance.
- Serial waves, baseline-first history and paired release/migration changes preserve ownership and chronology.

### Agreed Concerns

- **C2-A01, LOW — Explicitly identify the test table's base class.** Fable and Grok independently note that the existing module's `Table` name is an HTML parser, while the package's Table requires view context and supplies actions. The simple isolated test table must name `django_tables2.Table` explicitly.

### Divergent Views

- Fable requests an unguarded-legacy-override negative test; Grok considers the existing guarded override/spies sound, and Gemini finds the matrix complete. The guard contract is already exercised through call-count spies and the actual documented recipe; the extra negative regression is optional evidence, not a new executable gap.
- Grok identifies missing shared-key/icon assertions in the executable documentation recipe. Gemini accepts the planned recipe checks, but the current assertions do not themselves prevent hardcoded labels or missing icons in that copied child. C2-A02 records the specific uncovered check.
- Fable and Grok request broader migration wording/navigation checks; Gemini signs off the current prose plan. Current task text already covers the new DOM, setting/structural-copy paths and links; checklist expansion was expressly deferred. These preferences do not become new scope.

## Concern disposition and cycle counting

The consensus gate engages because three reviewers completed reviews. All have real source citations and no leading evidence-discount marker. There are no newly raised HIGHs to classify or suppress. Cycle-1 H01 is **fully resolved as a plan finding**, with explicit sign-off from all three reviewers and supplemental verification of the selection seam; this is not a claim that implementation has run. H02 remains refuted, with the real query tag re-probed this cycle. Historical HIGH mentions and the existing threat-register severities do not enter the current count.

### Prior-cycle closure

| Prior concern | Current plan evidence | Current review disposition |
|---|---|---|
| H01 — wrong table template captured | `05-01-PLAN.md:123-131`: scoped options patch, selected name and actual response origin before every capture | Closed; all three reviewers sign off, direct table selection probe passes |
| H02 — repeated values allegedly dropped | `05-02-PLAN.md` Round 1 rejection ledger; actual `dict(QueryDict)` plus `urlencode(..., doseq=True)` path | Remains refuted; direct render preserves both tag values |
| A01 — Unicode I/O | `05-01-PLAN.md:133-134`, `:195-200`: explicit UTF-8 for table, raw JSON and existing card helper | Closed |
| A02 — isolated renderer setup | `05-02-PLAN.md:96-112`: prepared table/request, named libraries, Context, before_render, direct Engine rendering and cleanup | Closed; direct isolated child probe passes |
| A03 — no real middle card page | `05-02-PLAN.md:181-194`: five records, three-page assertion and middle destinations 1/3 | Closed |
| A04 — catalog input/final bytes | `05-03-PLAN.md:173-187`, `:196`: restore working-file churn before compile and independently compare compiled bytes | Closed |
| A05 — recipe selection | `05-03-PLAN.md:107-112`, `:130-133`: distinct child name and startup selection tested through isolated renderer | Closed; optional audience wording is already covered by the project/structural-copy instructions |
| A06 — direction classes | `05-01-PLAN.md:145-148`, `05-03-PLAN.md:116-117`: exact stock/recipe class lists | Closed |

### Current actionable refinements

Each row is a distinct non-HIGH refinement not yet incorporated or explicitly deferred in the current plans. The planner may implement it or record a specific rejection/deferral rationale; no locked product choice is reopened.

| ID | Severity / reviewer | Remaining concern and required PLAN.md change |
|---|---|---|
| C2-A01 | LOW / Fable, Grok | Specify `PaginationTable(django_tables2.Table)` with a plain tables2 Column in 05-02-01 (`05-02-PLAN.md:96`). `tests/test1/test_table_template.py:6` imports an HTML parser named Table; `src/crud_views/lib/table/table.py:15-28` requires view context and adds actions. The plan's intended simple base should be explicit. |
| C2-A02 | MEDIUM / Grok | Require the documented child's enabled and disabled arrows to use `cv_button_class "pagination" "hidden-label"` and `cv_icon` page directions, and test the extracted recipe with a nondefault shared class plus overridden icons across pages 1/2/3. Current `05-03-PLAN.md:114-117` explicitly attaches the icon/label contract to the disabled branch, while `:134-136` checks classes/links/current/range without label-key or icon assertions; a hardcoded or icon-free recipe could pass. |

### Already covered, deferred, optional or refuted observations

| Observation | Disposition and evidence |
|---|---|
| Fable: add negative tests for unguarded legacy overrides | Optional additional regression. `05-02-PLAN.md:114-119` spies on unavailable page methods and `05-03-PLAN.md:128-136` renders the actual guarded recipe at both ends. These already prove the required guard contract. A direct probe this cycle also confirms that an unguarded unavailable method raises `EmptyPage`; lack of another committed negative case is not an executable plan gap. |
| Fable: recipe audience mismatch | Already incorporated: `05-03-PLAN.md:107-112` names the project child, startup setting and explicit-table precedence; `:119-120` separately says retained structural copies must adopt the shared key/accessibility. The existing heading applies to downstream themes and the guide explicitly includes project overrides (`docs/migrating-1.0.md:429`). Further lead-in wording is optional. |
| Fable: enumerate two DOM facts in CHANGELOG/selector list | Already represented by `05-03-PLAN.md:98-100` (translated hidden labels), `:118-120` (current-page span/aria-current), and `:123-124` (corresponding DOM/block Breaking entry linked to that migration section). No new behavior or documentation obligation is missing; exact prose is executor work. Existing checklist expansion remains deferred. |
| Fable: add a dedicated CHANGELOG anchor assertion | Optional additional test. `05-03-PLAN.md:124` already requires the migration link, and `:128-136` requires extracting the unique named migration heading. MkDocs does not validate root CHANGELOG links, but that limit does not make the required link invisible to execution or mandate a new test. |
| Grok: add EmptyPage to step-zero/checklist entry points | Checklist expansion was explicitly deferred in the Round 1 ledger (`05-03-PLAN.md:353`). The existing text says “Two removals” (`docs/migrating-1.0.md:38`), not that these are the only runtime exceptions; changing a block's availability is not another removal. The new dedicated section explicitly names `EmptyPage` (`05-03-PLAN.md:105-107`) and is linked by the required list-view key-link and CHANGELOG action. No new contradiction overrides the deferral. |
| Fable: existing table test's inaccurate docstring | Existing pre-phase defect (`tests/test1/test_table_template.py:20-30`), explicitly called non-phase by the reviewer. The new capture has its own enforced origin check. Updating the old test/comment is optional cleanup, not a missing phase requirement. |
| Fable: use a span for ellipses | Optional markup preference. `05-01-PLAN.md:154-157` preserves existing ellipsis semantics and `05-02-PLAN.md:169-173` tests non-navigability. Do not expand the locked pagination scope. |
| Fable: invalid-page semantics need a new 404 assertion | `05-02-PLAN.md:174-176` explicitly says preserve framework behavior rather than introduce an algorithm. It does not require an invalid-page response to contain an empty nav. An extra Http404 regression is optional, not a contradictory acceptance criterion. |
| Fable: gettext must be read before patch or sentinel is ignored | Factual premise refuted in a disposable Python probe: remove cached `_trans.gettext`, assign a sentinel without reading the original, then `gettext("previous")` returns the sentinel. `django/utils/translation/__init__.py:63-82,95-96` delegates through the assigned attribute. Reading the original is useful when the replacement delegates or must restore it; the plan already requires scoped restoration (`05-02-PLAN.md:205`). No missing patch-order requirement. |
| Fable: record unrelated stale PO references | Explicit scoped disposition already exists in `05-03-PLAN.md:175-180`: retain only the three msgids' source-reference changes and restore unrelated churn. Whole-catalog reference upkeep is deliberately excluded; no new action is needed. |
| Fable: expand existing card selector/checklist bullets | The plan's Round 1 deferred ledger explicitly rejects rewriting existing card migration bullets/checklists. Those statements remain true. The planned new section/release entry already describes the hidden labels, current-page span and DOM/block change; no additional checklist rewrite is required. |
| Grok: breadcrumb could be captured instead of pagination | `05-01-PLAN.md:122-134` requires `_table_pagination`, pagination-only captures and the existing card golden convention; the source helper selects `nav > ul.pagination` (`test_card_order.py:208-212`). Selecting the correct component is inherent in the already specified capture. An exact selector spelling is an executor detail. |
| Grok: duplicate default-count sentence/arithmetic | `05-01-PLAN.md:244-248` already says “single canonical count sentence,” adds the singleton key row, and the task runs the count guard. No uncovered change. |
| Grok: add list-view migration link to action text | Already represented by the explicit `must_haves.key_links` from `docs/reference/list_view.md` to the migration guide (`05-03-PLAN.md:43-45`). The counting contract includes key-link/artifact requirements; repeating it in action prose is not necessary. |
| PAGE-01 unclassified probe | Explicitly preserved as unresolved in the plans and acceptance task. It is not an invisible non-HIGH review task and does not enter these counts. |

The unguarded method's exception was reproduced in a disposable direct-template probe this cycle; the patch-first gettext concern was separately disproved. Neither probe is represented as a new committed test. Reviewer sandbox limitations and inference are retained in their raw sections. Counts include only the two concrete new executable refinements above, not additional reviewer preferences.

CYCLE_SUMMARY: current_high=0 current_actionable=2


## Review execution and diagnostics

- Cycle 2 reviews plan commit `8ef4a1b`; cycle 1's report remains available at git commit `95163e2`. The prior owned conflict-slot bytes are preserved exactly.
- Selection used the configured defaults `fable-review`, `grok-review`, `gemini-review`, with no reviewer flags. Claude and OpenCode were detected; this host is Codex. Instance models and adapter high effort came from the workflow seam, with no subagents spawned by this leaf orchestrator.
- All three lanes ran concurrently because `review.parallel_lanes=true`. To reuse the successful cycle-1 timeout recovery, this run used a temporary config snapshot with only `review.timeouts.opencode=1200` added. `--cwd` selected that snapshot; actual process cwd and `--repo-root` remained this repository. Persistent configuration was not changed.
- Run ID: `gsd-review-vudxefpi`. All three lanes completed on their first invocation in this cycle, through `review-lane invoke`; each result is `ok:true, stubbed:false`, with all three mandatory plan sections and concrete source citations. No lane was dropped, retried, trimmed, budget-skipped or discounted. The previous cycle's timeout does not enter this cycle's counts.
- Models and their sources above come from each current lane result, not inferred names. Reviewer-local risk/count proposals remain in their raw sections; the orchestrator's concern-disposition table and final cycle summary are the reconciled result.
- Reviewer output and nonempty stderr are preserved under a unique per-run `.review-diagnostics/` subdirectory. Duplicate plan/prompt inputs are excluded. Only `05-REVIEWS.md` is included in the review commit; diagnostics and unrelated changes are not staged.


## Verification coverage

`plan_review.source_grounding=true`; `drift-guard authority --raw` resolved **intel**. `.planning/intel/API-SURFACE.md:5` explicitly reports an empty JS-oriented index, and its referenced `api-map.json` is absent. Neither absence is evidence that a Python/template API is missing. Existing paths were checked on disk; Python/framework/template symbols and signatures remain **UNCHECKABLE** under that authority, with supplemental real-source evidence recorded below.

This cycle's inventory contains **176 audit rows**: 45 VERIFIED existing paths, 97 UNCHECKABLE symbols/flags/qualified references, and 34 explicitly excluded future-artifact rows. Every nonexcluded row was submitted to the `drift-guard severity` seam with authority `intel`: VERIFIED returned `severity=none, hardBlock=false`; UNCHECKABLE returned `severity=INFO, hardBlock=false`. No MISSING or AMBIGUOUS result, acknowledgement gate, or hard block was produced. Textual source evidence and probes do not establish supported-version signature compatibility.

The inventory quotes current plan lines. New helpers, tests, captures, acceptance records, summaries and the raw-card capture switch are excluded as declared phase outputs, including later-wave uses. Documentation's `myproject/table.html` child name is an example produced by the planned recipe, not a claim of an existing repository template. HTML attributes/CSS selectors and dotted template blocks are markup contracts, not Python declarations. No decorators or dataclass/struct declaration references require a separate declaration check. CLI flags, environment variables and standard-library calls remain explicitly UNCHECKABLE at the index authority; no unperformed CLI-help or full-suite checks are claimed.

Supplemental checks completed this cycle without product changes:

- Scoped `patch.object(AuthorTable._meta, "template_name", "crud_views/table/bootstrap5.html")` makes `AuthorTable([], view=AuthorListView()).template_name` select the tracked package template. The class-definition setting capture is visible in installed `django_tables2/tables.py:121` and `:152`; the render tag selects `table.template_name` at `django_tables2/templatetags/django_tables2.py:151`. The plan additionally requires the actual response origin assertion, so this probe is not represented as the future end-to-end baseline capture.
- A five-row plain Table configured by `RequestConfig(request, paginate={"per_page": 2})` rendered an isolated locmem child extending the tracked base, using the exact planned Engine/library/Context/before_render protocol. The child range marker rendered on page 2 of 3 and the base origin resolved to the tracked `src/crud_views/templates/crud_views/table/bootstrap5.html`. Temporary `table.context` was removed afterward.
- `dict(QueryDict("tag=a&tag=b&authors-page=1"))` returned `{'tag': ['a', 'b'], 'authors-page': ['1']}`. The real `cv_querystring` tag rendered `?tag=a&amp;tag=b&amp;authors-page=2`. This reconfirms H02's prior refutation; the repeated-query acceptance remains intact.

The orchestrator did not run the phase implementation tests, capture future goldens, compile catalogs, or claim implementation completion. Reviewer sections retain their own execution limits. Research and Nyquist artifacts were explicitly skipped by user instruction and are not missing prerequisites. Installed dependency paths below refer to the available Python 3.12 environment. All three current plans, the context, requirements, roadmap, state and prior disposition ledgers were included in this review's evidence.


| Cited symbol / kind | Plan citation and quoted line | Verdict | Source evidence / exclusion reason |
|---|---|---|---|
| Path `src/crud_views/templates/crud_views/table/bootstrap5.html` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:8`: “- src/crud_views/templates/crud_views/table/bootstrap5.html” | VERIFIED | src/crud_views/templates/crud_views/table/bootstrap5.html:1 (exists) |
| Path `src/crud_views/templates/crud_views/snippets/pagination.html` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:9`: “- src/crud_views/templates/crud_views/snippets/pagination.html” | VERIFIED | src/crud_views/templates/crud_views/snippets/pagination.html:1 (exists) |
| Path `src/crud_views/lib/button_classes.py` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:10`: “- src/crud_views/lib/button_classes.py” | VERIFIED | src/crud_views/lib/button_classes.py:1 (exists) |
| Path `tests/test1/test_table_template.py` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:11`: “- tests/test1/test_table_template.py” | VERIFIED | tests/test1/test_table_template.py:1 (exists) |
| Path `tests/test1/test_card_order.py` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:12`: “- tests/test1/test_card_order.py” | VERIFIED | tests/test1/test_card_order.py:1 (exists) |
| Path `tests/test1/test_button_classes.py` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:13`: “- tests/test1/test_button_classes.py” | VERIFIED | tests/test1/test_button_classes.py:1 (exists) |
| Path `tests/test1/golden/table_pagination/page1.html` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:14`: “- tests/test1/golden/table_pagination/page1.html” | SKIPPED — new artifact | Declared phase output; excluded from missing-symbol findings. |
| Path `tests/test1/golden/table_pagination/page2.html` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:15`: “- tests/test1/golden/table_pagination/page2.html” | SKIPPED — new artifact | Declared phase output; excluded from missing-symbol findings. |
| Path `tests/test1/golden/card_pagination/raw_pages.json` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:16`: “- tests/test1/golden/card_pagination/raw_pages.json” | SKIPPED — new artifact | Declared phase output; excluded from missing-symbol findings. |
| Path `docs/reference/buttons.md` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:17`: “- docs/reference/buttons.md” | VERIFIED | docs/reference/buttons.md:1 (exists) |
| Path `src/crud_views/templatetags/crud_views.py` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:54`: “to: src/crud_views/templatetags/crud_views.py” | VERIFIED | src/crud_views/templatetags/crud_views.py:1 (exists) |
| Path `/home/alex/.codex/gsd-core/workflows/execute-plan.md` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:65`: “@/home/alex/.codex/gsd-core/workflows/execute-plan.md” | VERIFIED | /home/alex/.codex/gsd-core/workflows/execute-plan.md:1 (exists) |
| Path `/home/alex/.codex/gsd-core/templates/summary.md` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:66`: “@/home/alex/.codex/gsd-core/templates/summary.md” | VERIFIED | /home/alex/.codex/gsd-core/templates/summary.md:1 (exists) |
| Path `CLAUDE.md` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:70`: “@CLAUDE.md” | VERIFIED | CLAUDE.md:1 (exists) |
| Path `.planning/PROJECT.md` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:71`: “@.planning/PROJECT.md” | VERIFIED | .planning/PROJECT.md:1 (exists) |
| Path `.planning/ROADMAP.md` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:72`: “@.planning/ROADMAP.md” | VERIFIED | .planning/ROADMAP.md:1 (exists) |
| Path `.planning/REQUIREMENTS.md` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:73`: “@.planning/REQUIREMENTS.md” | VERIFIED | .planning/REQUIREMENTS.md:1 (exists) |
| Path `.planning/STATE.md` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:74`: “@.planning/STATE.md” | VERIFIED | .planning/STATE.md:1 (exists) |
| Path `.planning/phases/05-table-pagination-parity/05-CONTEXT.md` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:75`: “@.planning/phases/05-table-pagination-parity/05-CONTEXT.md” | VERIFIED | .planning/phases/05-table-pagination-parity/05-CONTEXT.md:1 (exists) |
| Path `.planning/phases/05-table-pagination-parity/05-PATTERNS.md` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:76`: “@.planning/phases/05-table-pagination-parity/05-PATTERNS.md” | VERIFIED | .planning/phases/05-table-pagination-parity/05-PATTERNS.md:1 (exists) |
| Path `.planning/phases/02-form-key-grammar/02-CONTEXT.md` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:77`: “@.planning/phases/02-form-key-grammar/02-CONTEXT.md” | VERIFIED | .planning/phases/02-form-key-grammar/02-CONTEXT.md:1 (exists) |
| Path `superpowers/plans/2026-10-24-concept-review-followups.md` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:78`: “@superpowers/plans/2026-10-24-concept-review-followups.md” | VERIFIED | superpowers/plans/2026-10-24-concept-review-followups.md:1 (exists) |
| Path `superpowers/notes/2026-10-24-icons-buttons-theme-concept-review.md` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:79`: “@superpowers/notes/2026-10-24-icons-buttons-theme-concept-review.md” | VERIFIED | superpowers/notes/2026-10-24-icons-buttons-theme-concept-review.md:1 (exists) |
| Path `tests/test1/app/views.py` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:108`: “tests/test1/app/views.py” | VERIFIED | tests/test1/app/views.py:1 (exists) |
| Path `tests/test1/golden/card_pagination/page1.html` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:109`: “tests/test1/golden/card_pagination/page1.html” | VERIFIED | tests/test1/golden/card_pagination/page1.html:1 (exists) |
| Path `tests/test1/golden/card_pagination/page2.html` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:110`: “tests/test1/golden/card_pagination/page2.html” | VERIFIED | tests/test1/golden/card_pagination/page2.html:1 (exists) |
| Path `tests/test1/test_button_classes_checks.py` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:258`: “<automated>.venv/bin/pytest tests/test1/test_table_template.py tests/test1/test_card_order.py tests/test1/test_button_classes.py tests/test1/test_button_classes_checks.py -q</automated>” | VERIFIED | tests/test1/test_button_classes_checks.py:1 (exists) |
| Path `.planning/phases/05-table-pagination-parity/05-01-SUMMARY.md` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:297`: “- Execution summary .planning/phases/05-table-pagination-parity/05-01-SUMMARY.md with both baseline SHAs.” | SKIPPED — new artifact | Declared phase output; excluded from missing-symbol findings. |
| Path `docs/migrating-1.0.md` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:86`: “docs/migrating-1.0.md” | VERIFIED | docs/migrating-1.0.md:1 (exists) |
| Path `docs/reference/list_view.md` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:87`: “docs/reference/list_view.md” | VERIFIED | docs/reference/list_view.md:1 (exists) |
| Path `src/crud_views/locale/de/LC_MESSAGES/django.po` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:151`: “src/crud_views/locale/de/LC_MESSAGES/django.po” | VERIFIED | src/crud_views/locale/de/LC_MESSAGES/django.po:1 (exists) |
| Path `docs/reference/icons.md` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:152`: “docs/reference/icons.md” | VERIFIED | docs/reference/icons.md:1 (exists) |
| Path `.planning/phases/05-table-pagination-parity/05-02-SUMMARY.md` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:254`: “New execution summary .planning/phases/05-table-pagination-parity/05-02-SUMMARY.md.” | SKIPPED — new artifact | Declared phase output; excluded from missing-symbol findings. |
| Path `CHANGELOG.md` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:11`: “- CHANGELOG.md” | VERIFIED | CHANGELOG.md:1 (exists) |
| Path `tests/test1/test_pagination_docs.py` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:12`: “- tests/test1/test_pagination_docs.py” | SKIPPED — new artifact | Declared phase output; excluded from missing-symbol findings. |
| Path `src/crud_views/locale/de/LC_MESSAGES/django.mo` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:14`: “- src/crud_views/locale/de/LC_MESSAGES/django.mo” | VERIFIED | src/crud_views/locale/de/LC_MESSAGES/django.mo:1 (exists) |
| Path `.planning/phases/05-table-pagination-parity/05-ACCEPTANCE.md` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:15`: “- .planning/phases/05-table-pagination-parity/05-ACCEPTANCE.md” | SKIPPED — new artifact | Declared phase output; excluded from missing-symbol findings. |
| Path `tests/test1/test_label_mode_docs.py` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:86`: “tests/test1/test_label_mode_docs.py” | VERIFIED | tests/test1/test_label_mode_docs.py:1 (exists) |
| Path `tests/test1/test_alerts.py` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:87`: “tests/test1/test_alerts.py” | VERIFIED | tests/test1/test_alerts.py:1 (exists) |
| Path `taskfile.yaml` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:160`: “taskfile.yaml” | VERIFIED | taskfile.yaml:1 (exists) |
| Path `settings_i18n.py` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:161`: “settings_i18n.py” | VERIFIED | settings_i18n.py:1 (exists) |
| Path `.planning/phases/04-alert-dismiss-adapter/04-ACCEPTANCE.md` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:209`: “.planning/phases/04-alert-dismiss-adapter/04-ACCEPTANCE.md” | VERIFIED | .planning/phases/04-alert-dismiss-adapter/04-ACCEPTANCE.md:1 (exists) |
| Path `.planning/codebase/CONVENTIONS.md` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:229`: “The global formatter currently exits 1 on eight pre-existing planning files: .planning/codebase/CONVENTIONS.md,” | VERIFIED | .planning/codebase/CONVENTIONS.md:1 (exists) |
| Path `.planning/codebase/TESTING.md` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:230`: “.planning/codebase/TESTING.md, phase 01 PATTERNS/RESEARCH, phase 02 RESEARCH/VERIFICATION, and” | VERIFIED | .planning/codebase/TESTING.md:1 (exists) |
| Path `.planning/research/ARCHITECTURE.md` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:231`: “.planning/research/ARCHITECTURE.md and STACK.md. Report the actual global failure and changed-file formatting” | VERIFIED | .planning/research/ARCHITECTURE.md:1 (exists) |
| Path `examples/bootstrap5/manage.py` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:258`: “<automated>.venv/bin/python examples/bootstrap5/manage.py check</automated>” | VERIFIED | examples/bootstrap5/manage.py:1 (exists) |
| Path `.planning/phases/05-table-pagination-parity/05-03-SUMMARY.md` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:292`: “- New .planning/phases/05-table-pagination-parity/05-03-SUMMARY.md.” | SKIPPED — new artifact | Declared phase output; excluded from missing-symbol findings. |
| Symbol `AuthorTable._meta.template_name` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:124`: “fixtures and monkeypatch AuthorListView.paginate_by to 1 and AuthorTable._meta.template_name to” | UNCHECKABLE (intel); supplemental source evidence | tests/test1/app/views.py:56; .venv/lib/python3.12/site-packages/django_tables2/tables.py:152 (class options template_name); scoped-patch probe selects tracked package template |
| Symbol `AuthorTable` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:124`: “fixtures and monkeypatch AuthorListView.paginate_by to 1 and AuthorTable._meta.template_name to” | UNCHECKABLE (intel); supplemental source evidence | `tests/test1/app/views.py:56`: class AuthorTable(Table): |
| Symbol `response.templates` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:129`: “and a response.templates entry whose resolved origin.name equals the tracked package template's resolved path.” | UNCHECKABLE (intel); supplemental source evidence | `.venv/lib/python3.12/site-packages/django/test/client.py:1095`: response.templates = data.get("templates", []); `.venv/lib/python3.12/site-packages/django/test/client.py:1452`: response.templates = data.get("templates", []) |
| Symbol `origin.name` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:129`: “and a response.templates entry whose resolved origin.name equals the tracked package template's resolved path.” | UNCHECKABLE (intel); supplemental source evidence | Imported framework/stdlib seam; declaration not indexed. |
| Symbol `RequestConfig` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:98`: “chosen prefixed page field, then call RequestConfig(request, paginate={"per_page": 2}).configure(table).” | UNCHECKABLE (intel); supplemental source evidence | `.venv/lib/python3.12/site-packages/django_tables2/config.py:4`: class RequestConfig: |
| Symbol `configure` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:191`: “- The real card list uses the configured shared class for both available and unavailable arrows.” | UNCHECKABLE (intel); supplemental source evidence | `.venv/lib/python3.12/site-packages/django_tables2/config.py:33`: def configure(self, table): |
| Symbol `Column` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:96`: “Add a small test-only PaginationTable with a plain value Column and _render_table_pagination helper.” | UNCHECKABLE (intel); supplemental source evidence | `src/crud_views_workflow/lib/forms.py:6`: from crud_views.lib.crispy import Column8, CrispyForm; `src/crud_views_workflow/lib/forms.py:42`: return Row(Column8("transition")), Row(Column8("comment")) |
| Symbol `Context` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:106`: “django.templatetags.i18n. Build Context({"table": table, "request": request}, autoescape=True), temporarily” | UNCHECKABLE (intel); supplemental source evidence | `.venv/lib/python3.12/site-packages/django/template/context.py:138`: class Context(BaseContext): |
| Symbol `table.context` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:107`: “attach it as table.context, call table.before_render(request), and render via” | UNCHECKABLE (intel); supplemental source evidence | .venv/lib/python3.12/site-packages/django_tables2/templatetags/django_tables2.py:165 (temporary context attachment in RenderTableNode) |
| Symbol `before_render` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:107`: “attach it as table.context, call table.before_render(request), and render via” | UNCHECKABLE (intel); supplemental source evidence | `.venv/lib/python3.12/site-packages/django_tables2/tables.py:418`: def before_render(self, request):; `.venv/lib/python3.12/site-packages/django_tables2/tables.py:435`: def before_render(self, request): |
| Symbol `get_template` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:108`: “engine.get_template(template_name).render(context); restore or remove table.context in a finally block.” | UNCHECKABLE (intel); supplemental source evidence | .venv/lib/python3.12/site-packages/django/template/engine.py:172 (Engine.get_template) |
| Symbol `render` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:30`: “- "The default card render remains byte-identical to raw first/last-page captures made before editing the card template, and its two existing normalized goldens stay unchanged."” | UNCHECKABLE (intel); supplemental source evidence | `src/crud_views/templatetags/crud_views.py:333`: def render(self, context):; `src/crud_views/lib/table/columns.py:23`: def render(self, table, **kwargs): |
| Symbol `Table.Meta.template_name` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:109`: “Explain that an explicit Table.Meta.template_name or instance template_name takes precedence and must select” | UNCHECKABLE (intel); supplemental source evidence | .venv/lib/python3.12/site-packages/django_tables2/tables.py:152 (options template_name overrides global setting) |
| Symbol `EmptyPage` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:106`: “method; otherwise an end-page render can raise django.core.paginator.EmptyPage. Addresses review concern A05:” | UNCHECKABLE (intel); supplemental source evidence | `.venv/lib/python3.12/site-packages/django/core/paginator.py:23`: class EmptyPage(InvalidPage): |
| Symbol `_section` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:128`: “test_documented_pagination_direction_overrides. Reuse _section from tests.test1.test_label_mode_docs and” | UNCHECKABLE (intel); supplemental source evidence | `tests/test1/test_label_mode_docs.py:35`: def _section(text: str, heading: str) -> str: |
| Symbol `TEMPLATE_FENCE` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:129`: “TEMPLATE_FENCE from tests.test1.test_alerts to extract exactly one actual template fence under that heading;” | UNCHECKABLE (intel); supplemental source evidence | `tests/test1/test_alerts.py:23`: TEMPLATE_FENCE = re.compile(r"^(?:django\|html)\n(.*?)^", re.MULTILINE \| re.DOTALL) |
| Symbol `NamedTemporaryFile` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:196`: “<automated>.venv/bin/python -c 'from pathlib import Path; import subprocess, tempfile; root = Path("src/crud_views/locale/de/LC_MESSAGES"); output = tempfile.NamedTemporaryFile(); subprocess.run(["msgfmt", "--check-format", "-o", output.name, str(root / "django.po")], check=True); assert Path(output.name).read_bytes() == (root / "django.mo").read_bytes(), "Compiled catalog differs from final PO"; output.close()'</automated>” | UNCHECKABLE (intel); supplemental source evidence | Imported framework/stdlib seam; declaration not indexed. |
| Symbol `subprocess.run` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:196`: “<automated>.venv/bin/python -c 'from pathlib import Path; import subprocess, tempfile; root = Path("src/crud_views/locale/de/LC_MESSAGES"); output = tempfile.NamedTemporaryFile(); subprocess.run(["msgfmt", "--check-format", "-o", output.name, str(root / "django.po")], check=True); assert Path(output.name).read_bytes() == (root / "django.mo").read_bytes(), "Compiled catalog differs from final PO"; output.close()'</automated>” | UNCHECKABLE (intel); supplemental source evidence | `tests/test1/test_pipeline_sources.py:138`: result = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, check=False); `tests/test1/test_button_data.py:425`: result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=10) |
| Symbol `read_bytes` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:196`: “<automated>.venv/bin/python -c 'from pathlib import Path; import subprocess, tempfile; root = Path("src/crud_views/locale/de/LC_MESSAGES"); output = tempfile.NamedTemporaryFile(); subprocess.run(["msgfmt", "--check-format", "-o", output.name, str(root / "django.po")], check=True); assert Path(output.name).read_bytes() == (root / "django.mo").read_bytes(), "Compiled catalog differs from final PO"; output.close()'</automated>” | UNCHECKABLE (intel); supplemental source evidence | `tests/test1/test_vendor.py:30`: assert (spec.target / "plugin.js").read_bytes() == b"content"; `tests/test1/test_alerts.py:170`: locale, compared with read_bytes(). There is no whitespace normalization and no appended trailing newline, so |
| Symbol `read_text` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:133`: “explicit encoding="utf-8" for every new golden read_text/write_text call (review A01). Generate” | UNCHECKABLE (intel); supplemental source evidence | `src/crud_views/lib/vendor.py:59`: data = json.loads(stamp.read_text()); `tests/test1/test_form_frame.py:55`: assert _norm(markup) == path.read_text().strip() |
| Symbol `write_text` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:133`: “explicit encoding="utf-8" for every new golden read_text/write_text call (review A01). Generate” | UNCHECKABLE (intel); supplemental source evidence | `src/crud_views/lib/vendor.py:43`: (spec.target / STAMP_NAME).write_text(json.dumps({"key": spec.key, "version": spec.version})); `tests/test1/test_form_frame.py:54`: path.write_text(_norm(markup) + "\n") |
| Symbol `ensure_ascii` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:201`: “and set ensure_ascii=False when serializing, so stored Unicode round-trips explicitly (review A01).” | UNCHECKABLE (intel); supplemental source evidence | Imported framework/stdlib seam; declaration not indexed. |
| Symbol `encode` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:199`: “may create this file once; assertions compare rendered.encode("utf-8") to the stored string encoded as UTF-8,” | UNCHECKABLE (intel); supplemental source evidence | `src/crud_views/templatetags/crud_views.py:434`: base_qs = params.urlencode() if hasattr(params, "urlencode") else ""; `src/crud_views/lib/views/mixins.py:6`: from urllib.parse import parse_qs, urlencode |
| Symbol `Publisher` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:22`: “- "The parity matrix includes a real middle card page: five Publisher records at two per page yield page 2 with both arrows enabled and targets 1 and 3."” | UNCHECKABLE (intel); supplemental source evidence | `tests/test1/app/models.py:27`: class Publisher(models.Model): |
| Symbol `client_publisher_order` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:181`: “Publisher records named Delta and Echo. Use client_publisher_order to request /publisher_order/card/?page=1,” | UNCHECKABLE (intel); supplemental source evidence | `tests/test1/test_filter_pinned.py:16`: def client_publisher_order(client, cv_publisher_order) -> Client:; `tests/test1/test_card_order.py:24`: def client_publisher_order(client, cv_publisher_order) -> Client: |
| Symbol `publishers` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:180`: “Addresses review concern A03: add a local publishers_five fixture depending on publishers and appending two” | UNCHECKABLE (intel); supplemental source evidence | `tests/test1/test_filter_pinned.py:24`: def publishers(db):; `tests/test1/test_card_order.py:32`: def publishers(db): |
| Symbol `DEFAULT_BUTTON_CLASSES` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:142`: “cases for both pages. Add "pagination:hidden-label": "visually-hidden" to DEFAULT_BUTTON_CLASSES per D-01.” | UNCHECKABLE (intel); supplemental source evidence | `src/crud_views/lib/button_classes.py:15`: DEFAULT_BUTTON_CLASSES: dict[str, str \| None] = { |
| Symbol `EXPECTED_KEYS` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:237`: “Per D-01/D-02/D-08, add pagination:hidden-label to EXPECTED_KEYS, change the expected count to 71,” | UNCHECKABLE (intel); supplemental source evidence | `tests/test1/test_button_classes.py:19`: EXPECTED_KEYS = { |
| Symbol `AuthorListView` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:124`: “fixtures and monkeypatch AuthorListView.paginate_by to 1 and AuthorTable._meta.template_name to” | UNCHECKABLE (intel); supplemental source evidence | `tests/test1/app/views.py:63`: class AuthorListView(ListViewTableMixin, ListViewPermissionRequired): |
| Symbol `paginate_by` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:114`: “- The real /author/ list with two existing author fixtures and paginate_by=1 renders page 1 and page 2 through crud_views/table/bootstrap5.html.” | UNCHECKABLE (intel); supplemental source evidence | `src/crud_views/lib/views/card.py:25`: paginate_by = None  # set per-view to enable pagination; `src/crud_views/lib/views/mixins.py:293`: paginate_by: int = 10 |
| Symbol `DJANGO_TABLES2_TEMPLATE` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:126`: “Addresses review concern H01: AuthorTable's options capture DJANGO_TABLES2_TEMPLATE when its class is defined,” | UNCHECKABLE (intel); supplemental source evidence | `tests/test1/conftest.py:116`: DJANGO_TABLES2_TEMPLATE="django_tables2/bootstrap5.html",; `.venv/lib/python3.12/site-packages/django_tables2/tables.py:121`: DJANGO_TABLES2_TEMPLATE = getattr( |
| Symbol `CV_UPDATE_GOLDEN` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:134`: “page1.html and page2.html with CV_UPDATE_GOLDEN=1 restricted to test_table_pagination_golden, rerun with” | UNCHECKABLE (intel); supplemental source evidence | `tests/test1/test_heading_level.py:5`: CV_UPDATE_GOLDEN=1 pytest tests/test1/test_heading_level.py; `tests/test1/test_alerts.py:172`: CV_UPDATE_GOLDEN=1 pytest tests/test1/test_alerts.py::test_dismissible_alert_golden |
| Symbol `cv_button_class` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:29`: “- "Both pagination templates resolve pagination:hidden-label through cv_button_class; the default is visually-hidden and configuring sr-only changes both components."” | UNCHECKABLE (intel); supplemental source evidence | `src/crud_views_object_detail/templatetags/crud_views_object_detail.py:108`: def cv_button_class(location, slot, mode=None):; `src/crud_views/templatetags/crud_views.py:525`: def cv_button_class(location, slot, mode=None): |
| Symbol `cv_icon` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:55`: “via: "cv_icon and cv_querystring table.prefixed_page_field"” | UNCHECKABLE (intel); supplemental source evidence | `src/crud_views_object_detail/templatetags/crud_views_object_detail.py:102`: def cv_icon(value, css=""):; `src/crud_views/templatetags/crud_views.py:513`: def cv_icon(value, css=""): |
| Symbol `cv_querystring` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:55`: “via: "cv_icon and cv_querystring table.prefixed_page_field"” | UNCHECKABLE (intel); supplemental source evidence | `src/crud_views/templatetags/crud_views.py:289`: def cv_querystring(parser, token): |
| Symbol `table.prefixed_page_field` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:55`: “via: "cv_icon and cv_querystring table.prefixed_page_field"” | UNCHECKABLE (intel); supplemental source evidence | `.venv/lib/python3.12/site-packages/django_tables2/tables.py:597`: def prefixed_page_field(self): |
| Symbol `has_previous` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:144`: “enclose its own has_previous/has_next conditional per D-04. Preserve all table block names. Enabled li class” | UNCHECKABLE (intel); supplemental source evidence | `.venv/lib/python3.12/site-packages/django/core/paginator.py:208`: def has_previous(self): |
| Symbol `has_next` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:144`: “enclose its own has_previous/has_next conditional per D-04. Preserve all table block names. Enabled li class” | UNCHECKABLE (intel); supplemental source evidence | `.venv/lib/python3.12/site-packages/django/core/paginator.py:205`: def has_next(self): |
| Symbol `previous_page_number` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:148`: “previous_page_number/next_page_number calls. Each disabled li contains a.page-link with aria-disabled="true",” | UNCHECKABLE (intel); supplemental source evidence | `.venv/lib/python3.12/site-packages/django/core/paginator.py:217`: def previous_page_number(self): |
| Symbol `next_page_number` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:148`: “previous_page_number/next_page_number calls. Each disabled li contains a.page-link with aria-disabled="true",” | UNCHECKABLE (intel); supplemental source evidence | `.venv/lib/python3.12/site-packages/django/core/paginator.py:214`: def next_page_number(self): |
| Symbol `table_page_range` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:153`: “Within pagination.range keep table_page_range and its existing ellipsis semantics. Put aria-current="page"” | UNCHECKABLE (intel); supplemental source evidence | `.venv/lib/python3.12/site-packages/django_tables2/templatetags/django_tables2.py:239`: def table_page_range(page, paginator): |
| Symbol `translation.override` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:196`: “test_card_pagination_raw_bytes in test_card_order.py. Render the actual snippet under translation.override("en")” | UNCHECKABLE (intel); supplemental source evidence | `tests/test1/test_lazy_labels.py:63`: with translation.override("de"):; `tests/test1/test_button_container_layout.py:104`: with translation.override("de"): |
| Symbol `Paginator` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:197`: “with Paginator(range(3), 2), its requested Page, is_paginated=True and base_qs=""; serialize the exact two” | UNCHECKABLE (intel); supplemental source evidence | `.venv/lib/python3.12/site-packages/django/core/paginator.py:27`: class Paginator: |
| Symbol `is_paginated` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:197`: “with Paginator(range(3), 2), its requested Page, is_paginated=True and base_qs=""; serialize the exact two” | UNCHECKABLE (intel); supplemental source evidence | `src/crud_views/templatetags/crud_views.py:438`: "is_paginated": context.get("is_paginated", False),; `src/crud_views/templates/crud_views/snippets/pagination.html:2`: {% if is_paginated %} |
| Symbol `base_qs` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:197`: “with Paginator(range(3), 2), its requested Page, is_paginated=True and base_qs=""; serialize the exact two” | UNCHECKABLE (intel); supplemental source evidence | `src/crud_views/templatetags/crud_views.py:434`: base_qs = params.urlencode() if hasattr(params, "urlencode") else "" |
| Symbol `CRUD_VIEWS_BUTTON_CLASSES` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:206`: “Add failing test_card_pagination_shared_hidden_label with CRUD_VIEWS_BUTTON_CLASSES mapping” | UNCHECKABLE (intel); supplemental source evidence | `tests/test1/test_card_blocks.py:67`: CRUD_VIEWS_BUTTON_CLASSES={"card:root": "theme-card", "card:body": "theme-body", "card:title": "theme-title h3"}; `tests/test1/test_button_classes_templates.py:85`: CRUD_VIEWS_BUTTON_CLASSES={"formset:control": "x-ctrl", "formset:control-danger": "x-danger"} |
| Symbol `_isolate_registry` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:240`: “an empty class string. Reuse the existing _isolate_registry fixture. Assert button_class_check_messages()” | UNCHECKABLE (intel); supplemental source evidence | `tests/test1/test_button_container_layout.py:19`: def _isolate_registry():; `tests/test1/test_button_classes.py:77`: def _isolate_registry(): |
| Symbol `button_class_check_messages` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:240`: “an empty class string. Reuse the existing _isolate_registry fixture. Assert button_class_check_messages()” | UNCHECKABLE (intel); supplemental source evidence | `src/crud_views/lib/button_classes.py:237`: def button_class_check_messages() -> list[CheckMessage]: |
| Symbol `W362` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:241`: “accepts the exact utility key from both theme and settings, while a mode suffix still reports W362; the utility” | UNCHECKABLE (intel); supplemental source evidence | `src/crud_views/checks.py:406`: """E360/E361/W362/E363/E364 from the button class table."""; `src/crud_views/lib/button_classes.py:287`: id="crud_views.W362", |
| Symbol `Engine` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:103`: “Use an isolated Engine with a locmem loader for those children and a filesystem loader rooted at the resolved” | UNCHECKABLE (intel); supplemental source evidence | `.venv/lib/python3.12/site-packages/django/template/engine.py:13`: class Engine: |
| Symbol `RequestFactory` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:97`: “Its callers create a fresh table over deterministic dictionaries and a RequestFactory request containing the” | UNCHECKABLE (intel); supplemental source evidence | `.venv/lib/python3.12/site-packages/django/test/client.py:370`: class RequestFactory: |
| Symbol `urlsplit` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:165`: “Parse emitted hrefs with urlsplit/parse_qs: enabled numeric/direction links have exactly one authors-page” | UNCHECKABLE (intel); supplemental source evidence | `.venv/lib/python3.12/site-packages/django/test/client.py:11`: from urllib.parse import unquote_to_bytes, urljoin, urlsplit; `.venv/lib/python3.12/site-packages/django/test/client.py:646`: parsed = urlsplit(str(path))  # path can be lazy |
| Symbol `parse_qs` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:165`: “Parse emitted hrefs with urlsplit/parse_qs: enabled numeric/direction links have exactly one authors-page” | UNCHECKABLE (intel); supplemental source evidence | `src/crud_views/lib/views/mixins.py:6`: from urllib.parse import parse_qs, urlencode; `src/crud_views/lib/views/mixins.py:373`: qs = parse_qs(query_string) |
| Symbol `gettext` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:195`: “Patch gettext with distinctive sentinel translations for all three msgids as an additional real-translation” | UNCHECKABLE (intel); supplemental source evidence | `tests/test1/test_alerts.py:210`: def gettext(message):; `tests/test1/test_alerts.py:263`: def gettext(message): |
| Symbol `override_settings` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:202`: “per T-05-02. Reuse scoped override_settings and restore all test registry/translation changes. Strengthen” | UNCHECKABLE (intel); supplemental source evidence | `src/crud_views/lib/settings.py:66`: # it is read raw at call time (override_settings applies) and validated by E108; `src/crud_views/lib/view/label_mode.py:55`: """The raw CRUD_VIEWS_LABEL_MODE_DEFAULTS, read at call time (override_settings applies); _UNSET if absent.""" |
| Symbol `page-previous` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:28`: “- "Table pagination uses the page-previous/page-next registry icons, translated pagination/previous/next labels, an active li with aria-current=page and a non-link span, and disabled direction anchors with aria-disabled=true and no href or tabindex."” | UNCHECKABLE (intel); supplemental source evidence | `src/crud_views/lib/icons.py:33`: "page-previous": "fas:chevron-left",; `src/crud_views/lib/icons.py:71`: "page-previous": "chevron-left", |
| Symbol `page-next` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:28`: “- "Table pagination uses the page-previous/page-next registry icons, translated pagination/previous/next labels, an active li with aria-current=page and a non-link span, and disabled direction anchors with aria-disabled=true and no href or tabindex."” | UNCHECKABLE (intel); supplemental source evidence | `src/crud_views/lib/icons.py:34`: "page-next": "fas:chevron-right",; `src/crud_views/lib/icons.py:72`: "page-next": "chevron-right", |
| Symbol `pagination.previous` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:168`: “- pagination.previous, pagination.range and pagination.next remain overrideable with their original names.” | UNCHECKABLE (intel); supplemental source evidence | `src/crud_views/templates/crud_views/table/bootstrap5.html:66`: {% block pagination.previous %}; `src/crud_views/templates/crud_views/table/bootstrap5.html:73`: {% endblock pagination.previous %} |
| Symbol `pagination.range` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:153`: “Within pagination.range keep table_page_range and its existing ellipsis semantics. Put aria-current="page"” | UNCHECKABLE (intel); supplemental source evidence | `src/crud_views/templates/crud_views/table/bootstrap5.html:76`: {% block pagination.range %}; `src/crud_views/templates/crud_views/table/bootstrap5.html:84`: {% endblock pagination.range %} |
| Symbol `pagination.next` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:168`: “- pagination.previous, pagination.range and pagination.next remain overrideable with their original names.” | UNCHECKABLE (intel); supplemental source evidence | `src/crud_views/templates/crud_views/table/bootstrap5.html:87`: {% block pagination.next %}; `src/crud_views/templates/crud_views/table/bootstrap5.html:94`: {% endblock pagination.next %} |
| Symbol `table-wrapper` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:121`: “set remains table-wrapper, table, table.thead, table.tbody, table.tbody.row, table.tbody.empty_text, table.tfoot,” | UNCHECKABLE (intel); supplemental source evidence | `src/crud_views/templates/crud_views/table/bootstrap5.html:5`: {% block table-wrapper %}; `src/crud_views/templates/crud_views/table/bootstrap5.html:101`: {% endblock table-wrapper %} |
| Symbol `table.thead` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:121`: “set remains table-wrapper, table, table.thead, table.tbody, table.tbody.row, table.tbody.empty_text, table.tfoot,” | UNCHECKABLE (intel); supplemental source evidence | `src/crud_views/templates/crud_views/table/bootstrap5.html:9`: {% block table.thead %}; `src/crud_views/templates/crud_views/table/bootstrap5.html:27`: {% endblock table.thead %} |
| Symbol `table.tbody` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:121`: “set remains table-wrapper, table, table.thead, table.tbody, table.tbody.row, table.tbody.empty_text, table.tfoot,” | UNCHECKABLE (intel); supplemental source evidence | `src/crud_views/templates/crud_views/table/bootstrap5.html:28`: {% block table.tbody %}; `src/crud_views/templates/crud_views/table/bootstrap5.html:31`: {% block table.tbody.row %} |
| Symbol `table.tbody.row` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:121`: “set remains table-wrapper, table, table.thead, table.tbody, table.tbody.row, table.tbody.empty_text, table.tfoot,” | UNCHECKABLE (intel); supplemental source evidence | `src/crud_views/templates/crud_views/table/bootstrap5.html:31`: {% block table.tbody.row %}; `src/crud_views/templates/crud_views/table/bootstrap5.html:37`: {% endblock table.tbody.row %} |
| Symbol `table.tbody.empty_text` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:121`: “set remains table-wrapper, table, table.thead, table.tbody, table.tbody.row, table.tbody.empty_text, table.tfoot,” | UNCHECKABLE (intel); supplemental source evidence | `src/crud_views/templates/crud_views/table/bootstrap5.html:40`: {% block table.tbody.empty_text %}; `src/crud_views/templates/crud_views/table/bootstrap5.html:42`: {% endblock table.tbody.empty_text %} |
| Symbol `table.tfoot` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:121`: “set remains table-wrapper, table, table.thead, table.tbody, table.tbody.row, table.tbody.empty_text, table.tfoot,” | UNCHECKABLE (intel); supplemental source evidence | `src/crud_views/templates/crud_views/table/bootstrap5.html:47`: {% block table.tfoot %}; `src/crud_views/templates/crud_views/table/bootstrap5.html:57`: {% endblock table.tfoot %} |
| Symbol `num_pages` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:182`: “2 and 3 with these five records and the existing paginate_by=2; assert response.context["paginator"].num_pages” | UNCHECKABLE (intel); supplemental source evidence | `.venv/lib/python3.12/site-packages/django/core/paginator.py:114`: def num_pages(self):; `.venv/lib/python3.12/site-packages/django_tables2/templatetags/django_tables2.py:253`: num_pages = paginator.num_pages |
| Phase-produced artifact declaration | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:288`: “- Public class key pagination:hidden-label in DEFAULT_BUTTON_CLASSES; no new public function/class/tag.” | SKIPPED — explicitly new | Excluded by grounding contract, including cross-plan use in later waves. |
| Phase-produced artifact declaration | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:289`: “- New files tests/test1/golden/table_pagination/page1.html and tests/test1/golden/table_pagination/page2.html.” | SKIPPED — explicitly new | Excluded by grounding contract, including cross-plan use in later waves. |
| Phase-produced artifact declaration | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:290`: “- New file tests/test1/golden/card_pagination/raw_pages.json.” | SKIPPED — explicitly new | Excluded by grounding contract, including cross-plan use in later waves. |
| Phase-produced artifact declaration | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:291`: “- New test-only symbols in test_table_template.py: paginated_author_client, _table_pagination,” | SKIPPED — explicitly new | Excluded by grounding contract, including cross-plan use in later waves. |
| Phase-produced artifact declaration | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:292`: “_check_table_golden, test_table_pagination_golden, test_table_pagination_accessible_structure,” | SKIPPED — explicitly new | Excluded by grounding contract, including cross-plan use in later waves. |
| Phase-produced artifact declaration | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:293`: “test_table_pagination_shared_hidden_label.” | SKIPPED — explicitly new | Excluded by grounding contract, including cross-plan use in later waves. |
| Phase-produced artifact declaration | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:294`: “- New test-only symbols in test_card_order.py: _render_card_pagination_raw, test_card_pagination_raw_bytes,” | SKIPPED — explicitly new | Excluded by grounding contract, including cross-plan use in later waves. |
| Phase-produced artifact declaration | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:295`: “test_card_pagination_shared_hidden_label; capture environment flag CV_UPDATE_CARD_PAGINATION_RAW.” | SKIPPED — explicitly new | Excluded by grounding contract, including cross-plan use in later waves. |
| Phase-produced artifact declaration | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:296`: “- New test test_pagination_hidden_label_registry_contract in test_button_classes.py.” | SKIPPED — explicitly new | Excluded by grounding contract, including cross-plan use in later waves. |
| Phase-produced artifact declaration | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:297`: “- Execution summary .planning/phases/05-table-pagination-parity/05-01-SUMMARY.md with both baseline SHAs.” | SKIPPED — explicitly new | Excluded by grounding contract, including cross-plan use in later waves. |
| Phase-produced artifact declaration | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:246`: “No new production symbols or files. New test-only symbols in tests/test1/test_table_template.py:” | SKIPPED — explicitly new | Excluded by grounding contract, including cross-plan use in later waves. |
| Phase-produced artifact declaration | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:247`: “PaginationTable, _render_table_pagination, _assert_pagination_accessibility,” | SKIPPED — explicitly new | Excluded by grounding contract, including cross-plan use in later waves. |
| Phase-produced artifact declaration | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:248`: “test_table_pagination_direction_overrides, test_table_pagination_range_override,” | SKIPPED — explicitly new | Excluded by grounding contract, including cross-plan use in later waves. |
| Phase-produced artifact declaration | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:249`: “test_table_template_block_contract, test_table_pagination_prefixed_query_preservation,” | SKIPPED — explicitly new | Excluded by grounding contract, including cross-plan use in later waves. |
| Phase-produced artifact declaration | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:250`: “test_table_pagination_range_and_empty_cases,” | SKIPPED — explicitly new | Excluded by grounding contract, including cross-plan use in later waves. |
| Phase-produced artifact declaration | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:251`: “test_table_pagination_labels_translated and test_table_pagination_registry_overrides.” | SKIPPED — explicitly new | Excluded by grounding contract, including cross-plan use in later waves. |
| Phase-produced artifact declaration | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:252`: “New publishers_five fixture, test_pagination_component_parity and test_card_pagination_empty_cases in” | SKIPPED — explicitly new | Excluded by grounding contract, including cross-plan use in later waves. |
| Phase-produced artifact declaration | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:253`: “tests/test1/test_card_order.py.” | SKIPPED — explicitly new | Excluded by grounding contract, including cross-plan use in later waves. |
| Phase-produced artifact declaration | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:254`: “New execution summary .planning/phases/05-table-pagination-parity/05-02-SUMMARY.md.” | SKIPPED — explicitly new | Excluded by grounding contract, including cross-plan use in later waves. |
| Phase-produced artifact declaration | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:255`: “Child template fixtures live in the isolated in-memory loader; they are not installed runtime files.” | SKIPPED — explicitly new | Excluded by grounding contract, including cross-plan use in later waves. |
| Phase-produced artifact declaration | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:289`: “- New tests/test1/test_pagination_docs.py, with _pagination_override_recipe and” | SKIPPED — explicitly new | Excluded by grounding contract, including cross-plan use in later waves. |
| Phase-produced artifact declaration | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:290`: “test_documented_pagination_direction_overrides.” | SKIPPED — explicitly new | Excluded by grounding contract, including cross-plan use in later waves. |
| Phase-produced artifact declaration | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:291`: “- New .planning/phases/05-table-pagination-parity/05-ACCEPTANCE.md.” | SKIPPED — explicitly new | Excluded by grounding contract, including cross-plan use in later waves. |
| Phase-produced artifact declaration | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:292`: “- New .planning/phases/05-table-pagination-parity/05-03-SUMMARY.md.” | SKIPPED — explicitly new | Excluded by grounding contract, including cross-plan use in later waves. |
| Phase-produced artifact declaration | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:293`: “- Existing German .mo is regenerated only if its compiled content changes. No new msgid, public symbol or API.” | SKIPPED — explicitly new | Excluded by grounding contract, including cross-plan use in later waves. |
| CLI flag `--name-only` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:136`: “in the plan summary. Before product edits, inspect git diff --name-only for that SHA and its parent: the list” | UNCHECKABLE (intel) | CLI invocation/signature is outside JS index authority; existing project commands and installed help used as supplementary checks. |
| CLI flag `-q` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:171`: “<automated>.venv/bin/pytest tests/test1/test_table_template.py -q</automated>” | UNCHECKABLE (intel) | CLI invocation/signature is outside JS index authority; existing project commands and installed help used as supplementary checks. |
| CLI flag `--strict` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:150`: “<automated>.venv/bin/mkdocs build --strict</automated>” | UNCHECKABLE (intel) | CLI invocation/signature is outside JS index authority; existing project commands and installed help used as supplementary checks. |
| CLI flag `-m` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:172`: “run from src/crud_views with PYTHONPATH=../.. and ../../.venv/bin/python -m django makemessages -l de” | UNCHECKABLE (intel) | CLI invocation/signature is outside JS index authority; existing project commands and installed help used as supplementary checks. |
| CLI flag `-l` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:172`: “run from src/crud_views with PYTHONPATH=../.. and ../../.venv/bin/python -m django makemessages -l de” | UNCHECKABLE (intel) | CLI invocation/signature is outside JS index authority; existing project commands and installed help used as supplementary checks. |
| CLI flag `--settings` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:173`: “--settings=settings_i18n. Snapshot the .po content before extraction. Addresses review concern A04: retain” | UNCHECKABLE (intel) | CLI invocation/signature is outside JS index authority; existing project commands and installed help used as supplementary checks. |
| CLI flag `--check-format` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:181`: “settings and environment. Independently compile the final .po with msgfmt --check-format into a temporary” | UNCHECKABLE (intel) | CLI invocation/signature is outside JS index authority; existing project commands and installed help used as supplementary checks. |
| CLI flag `-k` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:194`: “<automated>.venv/bin/pytest tests/test1/test_table_template.py tests/test1/test_card_order.py -q -k translated</automated>” | UNCHECKABLE (intel) | CLI invocation/signature is outside JS index authority; existing project commands and installed help used as supplementary checks. |
| CLI flag `-n` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:248`: “<automated>.venv/bin/pytest tests -n auto</automated>” | UNCHECKABLE (intel) | CLI invocation/signature is outside JS index authority; existing project commands and installed help used as supplementary checks. |
| CLI flag `--prefix` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:250`: “<automated>npm --prefix . test</automated>” | UNCHECKABLE (intel) | CLI invocation/signature is outside JS index authority; existing project commands and installed help used as supplementary checks. |
| CLI flag `--check` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:256`: “<automated>.venv/bin/ruff format --check</automated>” | UNCHECKABLE (intel) | CLI invocation/signature is outside JS index authority; existing project commands and installed help used as supplementary checks. |
| Qualified symbol / environment `AuthorListView.paginate_by` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:124`: “fixtures and monkeypatch AuthorListView.paginate_by to 1 and AuthorTable._meta.template_name to” | UNCHECKABLE (intel); supplemental source evidence | tests/test1/app/views.py:63 (inherits ListView); .venv/lib/python3.12/site-packages/django/views/generic/list.py:15 (paginate_by inherited option) |
| Qualified symbol / environment `DJANGO_TABLES2_PAGE_RANGE` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:172`: “case, scope DJANGO_TABLES2_PAGE_RANGE=10 and use 30 records with per_page=1 on page 15. Derive expected page” | UNCHECKABLE (intel); supplemental source evidence | .venv/lib/python3.12/site-packages/django_tables2/templatetags/django_tables2.py:251 (setting controls range) |
| Qualified symbol / environment `response.context` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:182`: “2 and 3 with these five records and the existing paginate_by=2; assert response.context["paginator"].num_pages” | UNCHECKABLE (intel); supplemental source evidence | .venv/lib/python3.12/site-packages/django/test/client.py:1096 (response captured context) |
| Qualified symbol / environment `engine.get_template` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:108`: “engine.get_template(template_name).render(context); restore or remove table.context in a finally block.” | UNCHECKABLE (intel); supplemental source evidence | .venv/lib/python3.12/site-packages/django/template/engine.py:172 |
| Qualified symbol / environment `table.as_html` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:110`: “directly through this Engine, never through render_table or table.as_html(), whose global loader cannot see” | UNCHECKABLE (intel); supplemental source evidence | .venv/lib/python3.12/site-packages/django_tables2/tables.py:443 (API deliberately not used for isolated render) |
| Qualified symbol / environment `render_table` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:96`: “Add a small test-only PaginationTable with a plain value Column and _render_table_pagination helper.” | UNCHECKABLE (intel); supplemental source evidence | .venv/lib/python3.12/site-packages/django_tables2/templatetags/django_tables2.py:131 (RenderTableNode; global get_template at line 154) |
| Qualified symbol / environment `crud_views.templatetags.crud_views` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:105`: “crud_views.templatetags.crud_views, django_tables2 as django_tables2.templatetags.django_tables2, and i18n as” | UNCHECKABLE (intel); supplemental source evidence | src/crud_views/templatetags/crud_views.py:1 |
| Qualified symbol / environment `django_tables2.templatetags.django_tables2` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:105`: “crud_views.templatetags.crud_views, django_tables2 as django_tables2.templatetags.django_tables2, and i18n as” | UNCHECKABLE (intel); supplemental source evidence | .venv/lib/python3.12/site-packages/django_tables2/templatetags/django_tables2.py:1 |
| Qualified symbol / environment `django.templatetags.i18n` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:106`: “django.templatetags.i18n. Build Context({"table": table, "request": request}, autoescape=True), temporarily” | UNCHECKABLE (intel); supplemental source evidence | .venv/lib/python3.12/site-packages/django/templatetags/i18n.py:1 |
| Qualified symbol / environment `PYTHONPATH` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:172`: “run from src/crud_views with PYTHONPATH=../.. and ../../.venv/bin/python -m django makemessages -l de” | UNCHECKABLE (intel); supplemental source evidence | taskfile.yaml:103 (existing extraction setup; environment variable not an indexed declaration) |
| Qualified symbol / environment `output.name` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:196`: “<automated>.venv/bin/python -c 'from pathlib import Path; import subprocess, tempfile; root = Path("src/crud_views/locale/de/LC_MESSAGES"); output = tempfile.NamedTemporaryFile(); subprocess.run(["msgfmt", "--check-format", "-o", output.name, str(root / "django.po")], check=True); assert Path(output.name).read_bytes() == (root / "django.mo").read_bytes(), "Compiled catalog differs from final PO"; output.close()'</automated>” | UNCHECKABLE (intel); supplemental source evidence | Temporary file wrapper name is a stdlib runtime attribute; signature/attribute inference unavailable under intel. |
| Qualified symbol / environment `output.close` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:196`: “<automated>.venv/bin/python -c 'from pathlib import Path; import subprocess, tempfile; root = Path("src/crud_views/locale/de/LC_MESSAGES"); output = tempfile.NamedTemporaryFile(); subprocess.run(["msgfmt", "--check-format", "-o", output.name, str(root / "django.po")], check=True); assert Path(output.name).read_bytes() == (root / "django.mo").read_bytes(), "Compiled catalog differs from final PO"; output.close()'</automated>” | UNCHECKABLE (intel); supplemental source evidence | Temporary file wrapper delegates close to its file; stdlib API outside intel. |
| Qualified symbol / environment `CV_UPDATE_CARD_PAGINATION_RAW` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:198`: “strings as page1/page2 entries in raw_pages.json. A test-only CV_UPDATE_CARD_PAGINATION_RAW=1 capture switch” | SKIPPED — new test switch | New capture switch explicitly introduced by 05-01 task 2; excluded as future test artifact. |
| CLI flag `-c` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:196`: “<automated>.venv/bin/python -c 'from pathlib import Path; import subprocess, tempfile; root = Path("src/crud_views/locale/de/LC_MESSAGES"); output = tempfile.NamedTemporaryFile(); subprocess.run(["msgfmt", "--check-format", "-o", output.name, str(root / "django.po")], check=True); assert Path(output.name).read_bytes() == (root / "django.mo").read_bytes(), "Compiled catalog differs from final PO"; output.close()'</automated>” | UNCHECKABLE (intel) | CLI invocation/signature lies outside index authority; Python inline command and msgfmt output flag are explicit plan commands. |
| CLI flag `-o` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:196`: “<automated>.venv/bin/python -c 'from pathlib import Path; import subprocess, tempfile; root = Path("src/crud_views/locale/de/LC_MESSAGES"); output = tempfile.NamedTemporaryFile(); subprocess.run(["msgfmt", "--check-format", "-o", output.name, str(root / "django.po")], check=True); assert Path(output.name).read_bytes() == (root / "django.mo").read_bytes(), "Compiled catalog differs from final PO"; output.close()'</automated>” | UNCHECKABLE (intel) | CLI invocation/signature lies outside index authority; Python inline command and msgfmt output flag are explicit plan commands. |
| Path `.venv/bin/pytest` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:171`: “<automated>.venv/bin/pytest tests/test1/test_table_template.py -q</automated>” | VERIFIED | Exists on disk; directory/executable path only, no API-signature claim. |
| Path `.venv/bin/python` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:172`: “run from src/crud_views with PYTHONPATH=../.. and ../../.venv/bin/python -m django makemessages -l de” | VERIFIED | Exists on disk; directory/executable path only, no API-signature claim. |
| Path `.venv/bin/ruff` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:254`: “<automated>.venv/bin/ruff check</automated>” | VERIFIED | Exists on disk; directory/executable path only, no API-signature claim. |
| Path `.venv/bin/mkdocs` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:150`: “<automated>.venv/bin/mkdocs build --strict</automated>” | VERIFIED | Exists on disk; directory/executable path only, no API-signature claim. |
| Path `src/crud_views/templates` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:8`: “- src/crud_views/templates/crud_views/table/bootstrap5.html” | VERIFIED | Exists on disk; directory/executable path only, no API-signature claim. |
| Path `examples/bootstrap5` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:258`: “<automated>.venv/bin/python examples/bootstrap5/manage.py check</automated>” | VERIFIED | Exists on disk; directory/executable path only, no API-signature claim. |
| Symbol `Path` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:196`: “<automated>.venv/bin/python -c 'from pathlib import Path; import subprocess, tempfile; root = Path("src/crud_views/locale/de/LC_MESSAGES"); output = tempfile.NamedTemporaryFile(); subprocess.run(["msgfmt", "--check-format", "-o", output.name, str(root / "django.po")], check=True); assert Path(output.name).read_bytes() == (root / "django.mo").read_bytes(), "Compiled catalog differs from final PO"; output.close()'</automated>” | UNCHECKABLE | Framework/stdlib/pytest seam outside empty intel authority; source/probe evidence is supplementary, not signature verification. |
| Symbol `QueryDict` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:286`: “\| H02 — repeated query values are lost; weaken the assertion to the last value \| Rejected with source/probe evidence: dict(QueryDict("tag=a&tag=b&authors-page=1")) retains tag=["a", "b"], and the actual cv_querystring tag renders ?tag=a&amp;tag=b&amp;authors-page=2. The installed QuerystringReplaceNode copies those lists and calls urlencode(..., doseq=True). Keep the repeated-value criterion and existing production tag unchanged per D-09; see L374@95163e2. \|” | UNCHECKABLE | Framework/stdlib/pytest seam outside empty intel authority; source/probe evidence is supplementary, not signature verification. |
| Symbol `urlencode` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:286`: “\| H02 — repeated query values are lost; weaken the assertion to the last value \| Rejected with source/probe evidence: dict(QueryDict("tag=a&tag=b&authors-page=1")) retains tag=["a", "b"], and the actual cv_querystring tag renders ?tag=a&amp;tag=b&amp;authors-page=2. The installed QuerystringReplaceNode copies those lists and calls urlencode(..., doseq=True). Keep the repeated-value criterion and existing production tag unchanged per D-09; see L374@95163e2. \|” | UNCHECKABLE | Framework/stdlib/pytest seam outside empty intel authority; source/probe evidence is supplementary, not signature verification. |
| Symbol `monkeypatch` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:124`: “fixtures and monkeypatch AuthorListView.paginate_by to 1 and AuthorTable._meta.template_name to” | UNCHECKABLE | Framework/stdlib/pytest seam outside empty intel authority; source/probe evidence is supplementary, not signature verification. |
| Symbol `rendered.encode` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:199`: “may create this file once; assertions compare rendered.encode("utf-8") to the stored string encoded as UTF-8,” | UNCHECKABLE | Framework/stdlib/pytest seam outside empty intel authority; source/probe evidence is supplementary, not signature verification. |

## Cross-artifact fact-drift pass

The deterministic status seam returned `{"verdict":"lag","phase":"05","stateStatus":"Ready to execute","roadmapStatus":"Not started","stateRank":1,"roadmapRank":0,"authority":"STATE.md"}`. This is allowed nonterminal lag, not a finding. Both status files and CONTEXT are present; no comparison axis was skipped.

| Fact | Authoritative passage | Paired plan passage | Result |
|---|---|---|---|
| Baseline chronology | `.planning/ROADMAP.md:145`: “1. A golden of today's dismissible alert is committed first, so the PR shows the markup diff.” | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:27`: “- "A separate baseline-only commit contains today's first/last-page table goldens from the verified tracked package-template origin before any pagination markup changes, and a later commit visibly updates those same goldens."” | Consistent |
| Accessible registry markup | `.planning/ROADMAP.md:183`: “2. A paginated table shows `page-previous` / `page-next` registry icons with translated hidden labels,” | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:28`: “- "Table pagination uses the page-previous/page-next registry icons, translated pagination/previous/next labels, an active li with aria-current=page and a non-link span, and disabled direction anchors with aria-disabled=true and no href or tabindex."” | Consistent |
| Shared utility | `.planning/ROADMAP.md:186`: “3. One shared hidden-label class key (default `visually-hidden`) is read by both table and card pagination.” | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:29`: “- "Both pagination templates resolve pagination:hidden-label through cv_button_class; the default is visually-hidden and configuring sr-only changes both components."” | Consistent |
| Parity | `.planning/ROADMAP.md:188`: “4. Table and card pagination produce the same accessible structure. The CHANGELOG Breaking (DOM) entry, the” | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:159`: “- On first/middle/last pages both components expose the same arrow/current/disabled accessibility structure.” | Consistent |
| Breaking/migration/catalogs | `.planning/ROADMAP.md:189`: “migration bullet and the `.po` files are updated.” | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:27`: “- "Buttons/list/icons references describe pagination:hidden-label and page-previous/page-next for both paginations; the German catalog reuses pagination/previous/next."” | Consistent |
| Requirement IDs | `.planning/ROADMAP.md:179`: “**Requirements**: PAGE-01, PAGE-02, PAGE-03, PAGE-04” | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:19`: “requirements: [PAGE-01, PAGE-02, PAGE-03, PAGE-04]” | Consistent |
| D-01 shared name | `.planning/phases/05-table-pagination-parity/05-CONTEXT.md:22`: “- **D-01:** Use `pagination:hidden-label`, default `visually-hidden`, for hidden labels in both table and card” | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:29`: “- "Both pagination templates resolve pagination:hidden-label through cv_button_class; the default is visually-hidden and configuring sr-only changes both components."” | Consistent |
| D-02 card default | `.planning/phases/05-table-pagination-parity/05-CONTEXT.md:25`: “- **D-02:** Both pagination templates must read the shared key through the existing class-table mechanism.” | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:30`: “- "The default card render remains byte-identical to raw first/last-page captures made before editing the card template, and its two existing normalized goldens stay unchanged."” | Consistent |
| D-03 nav msgid | `.planning/phases/05-table-pagination-parity/05-CONTEXT.md:29`: “- **D-03:** Use the translated msgid `pagination` for the table navigation label, matching the existing card” | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:143`: “In the table template translate the nav msgid "pagination" per D-03. Each previous/next named block must” | Consistent |
| D-04 block coverage | `.planning/phases/05-table-pagination-parity/05-CONTEXT.md:33`: “- **D-04:** Keep `pagination.previous` and `pagination.next`, but make each block cover both its enabled and” | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:21`: “- "A theme overriding pagination.previous or pagination.next renders its override on enabled and disabled ends, and guarded overrides call page-number methods only when available."” | Consistent |
| D-05 guards | `.planning/phases/05-table-pagination-parity/05-CONTEXT.md:35`: “- **D-05:** Existing overrides must check direction availability before calling `previous_page_number` or” | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:105`: “ones; copied overrides must test table.page.has_previous/has_next before calling the corresponding page-number” | Consistent |
| D-06 baseline first | `.planning/phases/05-table-pagination-parity/05-CONTEXT.md:40`: “- **D-06:** Commit a golden of today's paginated table before changing its markup, so history exposes the DOM” | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:116`: “- Before product edits, both table captures pass against the old markup and are committed separately (D-06).” | Consistent |
| D-07 direction icons | `.planning/phases/05-table-pagination-parity/05-CONTEXT.md:42`: “- **D-07:** Use `page-previous` and `page-next` registry icons with translated hidden `previous` / `next` labels.” | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:149`: “no href and no tabindex. Render cv_icon "page-previous" then the hidden” | Consistent |
| D-08 paired documents | `.planning/phases/05-table-pagination-parity/05-CONTEXT.md:46`: “- **D-08:** Record the DOM change under CHANGELOG Breaking and update `docs/migrating-1.0.md` in the same change.” | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:124`: “link the migration section. Commit Breaking and migration together; any reference to the new utility uses” | Consistent |
| D-09 regressions | `.planning/phases/05-table-pagination-parity/05-CONTEXT.md:49`: “- **D-09:** Verify both pagination structures, shared class overrides, translated labels, registry icon” | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:47`: “Prove the preserved table extension points and shared accessible behavior, including disabled ends, configuration,” | Consistent |

All four roadmap requirement IDs are represented; 05-02 references PAGE-02/03/04 and 05-03 references all four. No contradiction found in the permitted requirement, success-truth, or glossary/decision pairs. D-01 expressly supersedes the older PROJECT/source-plan table key; that recorded decision is preserved. Agent discretion and deferred ideas are nonauthoritative and excluded. Extra plan truths are permitted; no advisory drift adds to either counter.
