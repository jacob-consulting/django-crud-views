---
phase: 05
review_cycle: 1
reviewers: [fable-review, grok-review, gemini-review]
reviewed_at: 2026-10-27T11:50:48.721113+00:00
plans_reviewed: [05-01-PLAN.md, 05-02-PLAN.md, 05-03-PLAN.md]
plan_commit: f2358c5
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

# Cross-AI Plan Review: Phase 5 — Table pagination parity

Verified against the working tree of `introduce-gsd` (Django 5.2.14, django-tables2 3.0.0 installed). I read every production file, test module, doc and catalog the plans name. Two things I could not run in this sandbox: `ruff format --check` (needed approval) and the pytest baseline. Both are marked as open questions where relevant.

## 05-01

### Summary

The plan's mechanisms all check out against source. The table template's blocks, the card template's four literal classes, the registry's accept-any-default-key rule, the count sentence, the `paginate_by` monkeypatch path and the `DJANGO_TABLES2_TEMPLATE` override are all real and work the way the plan says. The baseline-first commit mirrors the Phase 4 precedent exactly. The one design choice I would push back on is the second golden mechanism for the card snippet: it adds a new env flag and a JSON container that no other golden in the repo uses, to protect against a change the existing normalized goldens already catch in every case except pure whitespace.

### Strengths

- **Baseline-first has a verified precedent.** `git log` shows `f6982bf test(04-01): commit dismissible alert golden baseline` preceding `910625b feat(04-01)`. The plan's "commit ONLY this capture test and the two table goldens" reproduces that chronology.
- **No W362 grammar change is needed, as claimed.** `button_class_check_messages` skips any key present in the default table (`src/crud_views/lib/button_classes.py:280`), so `pagination:hidden-label` is accepted from theme and settings the moment it joins `DEFAULT_BUTTON_CLASSES`. A mode suffix on it falls to the "not a known key" warning (`button_classes.py:290-297`) because `_action_key_parts` only admits variant locations and form kinds (`button_classes.py:222-223`).
- **The template override is necessary and already used.** Test settings pin `DJANGO_TABLES2_TEMPLATE="django_tables2/bootstrap5.html"` (`tests/test1/conftest.py:116`); the existing table tests already override it (`tests/test1/test_table_template.py:21,51`).
- **The `paginate_by` monkeypatch reaches the table.** `AuthorListView` declares no `paginate_by` (`tests/test1/app/views.py:63-71`); it inherits `paginate_by: int = 10` from `ListViewTableMixin` (`src/crud_views/lib/views/mixins.py:293`), and django-tables2 reads it via `getattr(self, "paginate_by", None)` (`django_tables2/views.py:61-71`). Setting the class attribute to 1 with two author fixtures yields two pages.
- **"Exactly four literal hidden-label classes" is accurate.** `snippets/pagination.html:7,11,25,29`.
- **The count arithmetic is right.** `test_default_table_is_complete` asserts 70 (`tests/test1/test_button_classes.py:87`) and the doc sentence reads "The default table has 70 keys" (`docs/reference/buttons.md:144`); one new key gives 71 in both.
- **Escaping of the class attribute is already proven.** `cv_button_class` is a `simple_tag` returning a plain str (`src/crud_views/templatetags/crud_views.py:524-527`); `test_tag_in_both_libraries_escapes` shows `"><x` renders as `&quot;&gt;&lt;x` (`tests/test1/test_button_classes.py:164-169`).
- **Icon/label ordering matches the card.** Card renders icon then label for previous and label then icon for next (`pagination.html:7,25`); the plan prescribes the same.

### Concerns

- **MEDIUM — A second, divergent golden mechanism.** Task 2 introduces `raw_pages.json` with a new flag `CV_UPDATE_CARD_PAGINATION_RAW`. Every other golden uses `CV_UPDATE_GOLDEN` and a file per capture; Phase 4 already established the raw-bytes variant with `.html` files (`tests/test1/test_alerts.py:166-181`: `markup.encode("utf-8")` vs `read_bytes()`). The byte-identity the raw test protects is one template substitution (`class="visually-hidden"` → `class="{% cv_button_class ... %}"`) that cannot change bytes unless the tag output changes, and the two normalized goldens plus `test_card_pagination_labels_translated` (`test_card_order.py:255`) already pin the class. The extra guard is defensible, but the new flag and JSON wrapper are gratuitous.
- **MEDIUM — Golden read without an explicit encoding.** The card helper uses `path.read_text()` (`test_card_order.py:221`). The before-change table golden will contain `«`/`»` (lxml serialises `&laquo;` as the character). On a non-UTF-8 locale `read_text()` decodes wrongly. The plan says "existing normalization convention" and would inherit this.
- **LOW — Task 1 is large for a tracer.** It bundles a baseline commit, a RED commit, the registry key, the template rewrite and golden regeneration. It is coherent, but the tracer feedback gate in `execute-plan.md` only re-runs `<verify>` after the whole task, so the baseline-chronology check (template blobs equal parent's) happens in 05-03, two plans later. Consider adding the `git show --stat <baseline>` check to this task's acceptance.
- **LOW — "Preserve the existing outer pagination/no-page guard" leaves a redundant inner guard.** `{% if table.page.has_previous or table.page.has_next %}` around `pagination.range` (`table/bootstrap5.html:75`) is always true under the outer `num_pages > 1` guard (`:62`). Harmless; mention only so it is not mistaken for a disabled-end condition.

### Suggestions

- Drop `raw_pages.json` and `CV_UPDATE_CARD_PAGINATION_RAW`. Capture the two raw card renders as `golden/card_pagination/raw_page1.html` / `raw_page2.html` under `CV_UPDATE_GOLDEN`, following `test_alerts.py:166-181`. Same evidence, one convention.
- Pass `encoding="utf-8"` in the new `_check_table_golden` (and consider fixing the card helper in passing, since the file is already being edited).
- Add to Task 1's acceptance: `git diff --stat <baseline>^ <baseline>` lists only the test module and the two goldens.
- Name the three tag-library requirement explicitly for anyone rendering the template outside the view: `{% load django_tables2 %}` supplies `localize`/`unlocalize` (`django_tables2/templatetags/django_tables2.py:211-212`), so no `l10n` load is needed.

### Risk Assessment

**LOW.** Every mechanism is verified in source; the only real question is test-infrastructure taste, not correctness.

## 05-02

### Summary

This is the plan that proves D-04/D-05 and the query/range/edge behaviour. Its assertions are grounded: the block list it wants to pin is exactly the template's block set, the django-tables2 `querystring_replace` node preserves repeated values and requires `request`, and the page-range filter emits `"..."` strings only beyond `DJANGO_TABLES2_PAGE_RANGE`. The two gaps are practical: the "isolated Engine" is stricter than the existing `_theme_templates` precedent and carries a small setup cost, and the "middle page" the parity test wants does not exist on either real endpoint as fixtures stand.

### Strengths

- **The block contract list is correct.** The template declares exactly `table-wrapper, table, table.thead, table.tbody, table.tbody.row, table.tbody.empty_text, table.tfoot, pagination, pagination.previous, pagination.range, pagination.next` (`table/bootstrap5.html:5,7,9,28,31,40,47,61,66,76,87`).
- **The spy approach is well founded.** `Page.previous_page_number()` raises `EmptyPage` on page 1, and Django's variable resolution only swallows exceptions with `silent_variable_failure`, so an unguarded override would actually raise. Spying on the method rather than relying on the exception path is the right call and keeps the test green even if Django's behaviour changes.
- **Query preservation claims match tables2 3.0.0.** `QuerystringNode.render` builds `dict(context["request"].GET)` (`django_tables2/templatetags/django_tables2.py:58`), which keeps list values per key, so repeated `tag=` values survive and only the updated prefixed key is replaced.
- **The range edge is understood.** `table_page_range` returns a plain `range` up to `DJANGO_TABLES2_PAGE_RANGE` (default 10) and inserts `"..."` only beyond it (`django_tables2.py:251-270`). The plan's "derive expected tokens with the existing filter" avoids hard-coding that.
- **Translation sentinel has a precedent.** Patching `_trans.gettext` with a sentinel is the Phase 4 pattern (`tests/test1/test_alerts.py:257-284`); German strings `Seitennavigation`/`zurück`/`weiter` are in the catalog (`django.po:278-291`).
- **Icon override pattern exists.** `test_card_pagination_arrows_from_icon_registry` already asserts `bi bi-arrow-left` (`test_card_order.py:259-264`); the test library default is Font Awesome (`golden/card_pagination/page1.html` shows `fa-solid fa-chevron-left`), so the override is a genuine change.

### Concerns

- **MEDIUM — Isolated `Engine` setup is under-specified and departs from precedent.** Two existing helpers already do "locmem loader in front of the real engine" via scoped `override_settings(TEMPLATES=...)` (`tests/test1/test_form_frame.py:58-68`, `tests/test1/test_filter_toggle_label_mode.py:454-464`) and are imported across modules (`test_alerts.py:16`). A standalone `Engine` must register `crud_views`, `django_tables2` and `i18n` as libraries, put `request` in the `Context` (the querystring node raises `ImproperlyConfigured` without it, `django_tables2.py:55-56`), and reproduce `builtins`/`context_processors` if any inclusion tag is ever reached. None of that is wrong, but it is extra surface for no isolation gain the `override_settings` helper does not already provide.
- **MEDIUM — No "middle page" exists on the real endpoints.** `publishers` is three records with `paginate_by = 2` (`test_card_order.py:31-39`, `views.py:372`), and the author list with `paginate_by=1` has two records. `test_pagination_component_parity` and the direction-override test both specify first/middle/last. The table side can use the test-only `PaginationTable` with any row count, but the card side needs either extra fixture rows or the direct snippet render from 05-01-02. The plan does not say which.
- **LOW — Parity assertion scope.** The plan correctly tolerates `previous page-item`/`next page-item` vs plain `page-item`, but the card `<nav>` carries `class="mt-3"` (`pagination.html:3`) and the table `<nav>` does not. The parity helper should compare semantic attributes (`aria-label`, `aria-current`, `aria-disabled`, href presence, child order) and never `class` on `nav`/`li`.
- **LOW — Hostile query values.** The threat model (T-05-01) is correct: values pass through `urlencode` inside the node, and the href is in a quoted attribute. The test as written ("inspect the parsed DOM to prove they cannot inject") is valuable, but lxml normalises attribute quoting, so also assert the raw response bytes contain no unescaped `"` inside the `href`.

### Suggestions

- Reuse `_theme_templates` from `test_form_frame.py:58` (or lift it into `tests/lib/helper/`) for inherited child templates instead of a bespoke `Engine`. Keep the child templates in a module-level dict as `test_filter_toggle_label_mode.py:467-470` does.
- State the middle-page source: `PaginationTable` over `range(N)` for the table, and either a `publishers_five` fixture or the 05-01-02 direct snippet render with `Paginator(range(5), 2)` for the card.
- Pin the `DJANGO_TABLES2_PAGE_RANGE` default in the long-range test (`override_settings(DJANGO_TABLES2_PAGE_RANGE=10)`) so a project-level change cannot make the ellipsis case vanish.

### Risk Assessment

**LOW–MEDIUM.** Nothing here can break production; the risks are test-authoring friction and one unspecified fixture. The spy-based D-05 proof is the strongest piece in the phase.

## 05-03

### Summary

The documentation, catalog and acceptance plan is well targeted: the CHANGELOG `### Breaking` heading, the migration guide's structure, the `icons.md` row, the absence of any pagination text in `list_view.md`, the taskfile's `makemessages` invocation and the Phase 4 acceptance format all match what the plan assumes. The executable-recipe test has a direct precedent and reusable helpers. The weak spots are small: a reusable helper the plan should name instead of re-implementing, makemessages header churn that "retain only phase-related changes" should address explicitly, and one gate result I could not re-verify here.

### Strengths

- **Targets exist where the plan says.** `CHANGELOG.md:7` is `### Breaking` under `## Unreleased`; the card pagination entry sits in the same list. `docs/migrating-1.0.md` has `### CSS and tests that select on markup` (`:180`) with the #241 bullet (`:187-190`) and `### Contract changes in templates you still override` (`:331`). `docs/reference/icons.md:61` reads "[card list] pagination" and needs the "both" wording.
- **`list_view.md` genuinely lacks pagination guidance.** A grep for "pagination" in it returns nothing; `## Table with django-tables2` (`:71`) is the natural home.
- **Executable recipe has a precedent and helpers.** `_documented_alert_frame` extracts the single fence under a heading using `_section` (from `test_label_mode_docs.py`) and `TEMPLATE_FENCE` (`tests/test1/test_alerts.py:17,23,249-254`), then renders it as a real override. The pagination recipe test can be a near copy.
- **Catalog tooling matches.** `taskfile.yaml:98` runs `cd "$pkg" && PYTHONPATH=../.. python -m django makemessages -l "$loc" --settings=settings_i18n`, exactly the plan's command. `settings_i18n.py` lists all five apps, so scoping to `src/crud_views` is what keeps the diff to the core catalog.
- **The ".mo may be unchanged" prediction is right.** `previous`/`next` already carry table refs (`django.po:283,289`); only `pagination` gains one (`:277`). No msgid or msgstr changes, so the compiled catalog is byte-identical. `test_mo_files_load` only checks loadability (`tests/test1/test_i18n.py:76-81`), so nothing else is sensitive.
- **Gate commands are real.** `package.json` `"test": "vitest run"`, `node_modules/.bin/vitest` present, `examples/bootstrap5/manage.py` and `test_docs_sync.py` exist. The acceptance template mirrors `04-ACCEPTANCE.md` (tool-drift table, gate table, chronology).
- **The downstream note is kept generic.** No downstream project name appears in the product docs tasks, per PROJECT.md hygiene.

### Concerns

- **MEDIUM — makemessages header churn is not addressed.** `makemessages` rewrites `POT-Creation-Date` and may rewrap or reorder reference comments throughout the file. "Retain only phase-related catalog changes" needs a rule for the header line (keep it, as Phase 3 presumably did, or revert it). Otherwise the executor has to guess.
- **MEDIUM — Recipe naming could mislead.** The recipe "extends `crud_views/table/bootstrap5.html`". A project's own table template is selected by `DJANGO_TABLES2_TEMPLATE` (`docs/reference/settings.md:244-249`, `examples/bootstrap5/project/settings.py:138`). The migration text should say the child template has its own name and is pointed at by that setting; a same-name override that extends itself only works through Django's origin-skipping extends and is not what theme authors should copy.
- **LOW — `_section` / `TEMPLATE_FENCE` reuse not named.** The plan says "do not hand-copy the example" but does not say to import the existing helpers. Re-implementing fence parsing is how the two parsers drift.
- **LOW — Open question: current `ruff format --check` state.** I could not run it here. The plan's list of eight pre-existing files matches `04-ACCEPTANCE.md` (section 2) verbatim, so the claim is consistent with the last recorded run, but the executor must observe it, not copy it.
- **LOW — Test count baseline unverified.** "77 tests passed with the focused command" in 05-01's constraints is plausible for the four modules but I did not run it.

### Suggestions

- Add one sentence to Task 2: keep the regenerated `POT-Creation-Date` header (or revert it) and list it in the summary as the only non-reference diff.
- In the migration recipe, show the child as `myproject/templates/myproject/table.html` plus `DJANGO_TABLES2_TEMPLATE = "myproject/table.html"`, and have `test_pagination_docs.py` render it under that name through the `_theme_templates` loader.
- Import `_section` from `tests.test1.test_label_mode_docs` and `TEMPLATE_FENCE` from `tests.test1.test_alerts` (or move the regex to `tests/lib/helper/`).
- Also touch `docs/reference/card-list-view.md:281`, which says the page icons belong to the card list; one clause ("and the table") keeps the three references consistent.

### Risk Assessment

**LOW.** Docs and catalog work with concrete anchors; the executable recipe test removes the usual "prose drifts from code" risk.

---

## Cross-plan assessment

**Dependency ordering** is sound: 05-01 lands the key and markup, 05-02 only adds tests (production edits allowed only on regression), 05-03 documents after behaviour is fixed. No two plans write the same file in the same wave. Rebasing after Phase 2 for the count line is already moot: Phase 2 is merged and the count is 70 on this branch.

**Does the phase achieve its goal?** Yes. PAGE-01 through PAGE-04 and D-01 through D-09 each have an observable artifact: baseline commits, the shared key read by both templates, translated nav label, blocks covering both states, and paired Breaking/migration. The one requirement wording to watch is PAGE-02's "existing tables2 block names kept": the names survive but their semantics change, and D-05 plus the executable recipe handle that honestly.

**Scope creep.** Modest. The raw-bytes card capture with its own flag (05-01) and the bespoke template `Engine` (05-02) are the two places where the plans build infrastructure the repo already has. Neither endangers the phase; both cost executor time.

**Security.** The threat registers are proportionate. Both trust boundaries (query → href, config → class attribute) route through existing escaping that is already tested (`django_tables2.py:58` with urlencode; `test_button_classes.py:164-169`). No new code path handles user input.

**Performance.** No runtime change beyond two extra `get_button_class` lookups per pagination render, served from the cached merged dict (`button_classes.py:127-133`).

**Overall risk: LOW.** The plans are faithful to the codebase. The highest-value fixes before execution are: reuse the existing golden and template-override conventions, name the middle-page fixture, and spell out the makemessages header rule.


---

## OpenCode Review (grok-review)

I'll review all three plans against the source, not the plan text alone. Loading the package skill and the files the plans cite.
The plans exist. Next I’ll check the templates, class table, and tests they depend on.
## 05-01

The accessible-markup and shared-key design matches the current templates and the class-table lookup, but the tracer never renders `crud_views/table/bootstrap5.html`. `override_settings(DJANGO_TABLES2_TEMPLATE=...)` is too late: django-tables2 freezes the template name when the table class is created.

**Strengths**

- The current previous/next blocks sit inside availability checks, so a child override cannot run on a disabled end. Moving each `{% if table.page.has_previous %}` / `has_next` inside the preserved block is the right inheritance fix.

```65:73:src/crud_views/templates/crud_views/table/bootstrap5.html
{% if table.page.has_previous %}
    {% block pagination.previous %}
    <li class="previous page-item">
        <a href="{% cv_querystring table.prefixed_page_field=table.page.previous_page_number %}" class="page-link">
            <span aria-hidden="true">&laquo;</span>
            {% trans 'previous' %}
        </a>
    </li>
    {% endblock pagination.previous %}
{% endif %}
```

- `pagination:hidden-label` needs no grammar change. W362 accepts a key that is in `DEFAULT_BUTTON_CLASSES` and rejects anything else that is not a variant/form mode key (`button_classes.py:277-297`). `pagination` is not in `VARIANT_LOCATIONS` (`button_classes.py:207-226`). 70 keys today (`test_button_classes.py:86-98`, `buttons.md:144`); 71 after one utility key is right.
- Card arrows already use `page-previous` / `page-next`, hidden `previous` / `next`, and `aria-current="page"` on the current `<li>` (`snippets/pagination.html:7-16`). `{% cv_button_class %}` returns an autoescaped string (`crud_views.py:525-527`), so `class="{% cv_button_class "pagination" "hidden-label" %}"` stays `class="visually-hidden"` and the raw-byte pin is a real check.
- German `pagination` / `previous` / `next` already exist (`django.po:277-291`). The table nav is the hardcoded `Table navigation` (`bootstrap5.html:63`).

**Concerns**

- **HIGH — the `/author/` golden does not hit the template under change.** Tests set the upstream template before app import (`conftest.py:116`), and `TableOptions` copies that into `_meta.template_name` at class creation (`.venv/.../django_tables2/tables.py:121-152`). `{% render_table table %}` then uses `table.template_name` (`view_list_table.content.html:3`, `django_tables2.py:148-151`). `AuthorTable` has no `Meta.template_name` (`views.py:56-60`). The existing override at `test_table_template.py:21-30` only checks status and row count, so it does not prove the setting works. Executed as written, PAGE-01 captures upstream markup (`&laquo;`, no disabled previous), and later edits to the crud_views template do not change that golden.
- **MEDIUM — current-page `active` is unspecified.** Stock table and card both use `page-item active` (`bootstrap5.html:78`, `pagination.html:16`). Bootstrap paints the current page with `.page-item.active`. The plan requires `aria-current` and a `span.page-link`, but not `active`, and 05-02's parity check also omits it. A literal implementation drops the highlight.
- **LOW — disabled `previous` / `next` classes are ambiguous.** Enabled items are `previous page-item` / `next page-item` (`bootstrap5.html:67`, `bootstrap5.html:88`). The disabled spec is only `li.page-item.disabled`.

**Suggestions**

- Monkeypatch `AuthorTable._meta.template_name` to `crud_views/table/bootstrap5.html` in the real-view helper. Do not treat `override_settings(DJANGO_TABLES2_TEMPLATE=...)` as sufficient. Assert the rendered nav contains a marker that upstream lacks, before trusting the golden.
- Keep `class="page-item active"` on the current `<li>`, and `previous page-item disabled` / `next page-item disabled` on disabled ends.
- Put the `EXPECTED_KEYS` / count update in the same commit as the new default key so `test_default_table_is_complete` is not red between task 1 and task 3.

**Risk Assessment:** HIGH. The shared-key and block design is sound, but the baseline the phase treats as proof can be recorded from the wrong template.

## 05-02

Override, empty-state, translation, and escaping coverage matches the seams that exist, except one acceptance check that the frozen querystring tag cannot pass.

**Strengths**

- Direction blocks that contain their own guards make the page-number spy meaningful. `Page.previous_page_number()` raises `EmptyPage` when called on the first page, and Django templates do not swallow that. Spying is stronger than hoping for an exception.
- `cv_querystring` is `querystring_replace` (`crud_views.py:22-25`). It HTML-escapes the encoded query (`django_tables2.py:70`), so quotes and angle brackets in a query value cannot break out of `href`. `{% cv_icon %}` already emits `aria-hidden="true"` (`icons.py:220`).
- `table_page_range` returns `"..."` and keeps first/last/current (`django_tables2.py:238-272`). Asserting against that filter, not a reimplemented range, is the right lock. The outer `num_pages > 1` guard (`bootstrap5.html:62`) already suppresses empty, single-page, and unpaginated controls.
- An isolated engine with a filesystem loader on `src/crud_views/templates` is the right way to exercise `{% extends %}`. Rendering through `table.as_html()` would hit the same frozen-template bug as 05-01.

**Concerns**

- **HIGH — repeated query values cannot survive, and the plan forbids the fix.** `querystring_replace` does `params = dict(context["request"].GET)` (`django_tables2.py:58`). `dict(QueryDict)` keeps only the last value for each key. `test_table_pagination_prefixed_query_preservation` requires repeated `tag` values to round-trip, while D-09 says not to change `cv_querystring`. That assertion fails on this venv. Single-value `authors-sort`, `books-page`, and non-ASCII filters can survive; repeats cannot.
- **MEDIUM — `active` is still not in the parity assertions**, so 05-02 will not catch the visual drop called out above.
- **LOW — `pagination:hidden-label:icon` is W362 "not a known key", not "unknown label mode".** `_action_key_parts` returns `None` for a non-variant location (`button_classes.py:221-226`). Assert the id, not the mode-name message. Same pattern as `list:hidden-label:icon` (`test_button_classes_checks.py:88`).

**Suggestions**

- Assert that a repeated key is preserved as the tag preserves it today: one value, the last. Keep the injection check on the parsed DOM.
- Pass `request` in the isolated context. The tag raises `ImproperlyConfigured` if it is missing (`django_tables2.py:55-56`).
- Add `active` on the current `<li>` to `_assert_pagination_accessibility`.

**Risk Assessment:** MEDIUM. The extension and accessibility matrix is the right one, but the repeated-query criterion blocks the wave if followed literally.

## 05-03

Docs, catalog, and acceptance recording match the files and msgids that already exist. This plan is executable once 05-01 and 05-02 are rendering the tracked template.

**Strengths**

- `pagination` / `previous` / `next` are already `Seitennavigation` / `zurück` / `weiter` (`django.po:277-291`), and the card test already asserts those strings (`test_card_order.py:250-256`). Reusing the msgids is correct. `makemessages` from `src/crud_views` with `PYTHONPATH=../..` matches `taskfile.yaml:94-98` and `settings_i18n.py`.
- `icons.md:61` still says card-list only. `list_view.md` has no pagination contract. `CHANGELOG.md:7` already has `### Breaking`. A new `### Table pagination overrides` heading is free (`migrating-1.0.md` has no such heading). Extracting the fenced recipe and rendering it on first/middle/last pages will catch an unguarded `previous_page_number` because that call raises.
- Carrying the eight-file format failure and the unresolved PAGE-01 classifier, instead of marking them green, matches `04-ACCEPTANCE.md`.

**Concerns**

- **LOW — `card-list-view.md:281-284` still describes a hard-coded visually hidden label and is not in `files_modified`.** After this phase the class is `pagination:hidden-label`. Card authors who only read that page will not see the new key.
- **LOW — the recipe extractor is only as stable as the heading and the first fence.** A second fence under `### Table pagination overrides` would be executed as a template.

**Suggestions**

- Add one sentence to `card-list-view.md` that the hidden class is `pagination:hidden-label`, default `visually-hidden`, shared with table pagination.
- Mark the migration example with a single `html+django` fence directly under that heading, and have the test refuse a second fence.
- Link the changelog to `#table-pagination-overrides` so `mkdocs build --strict` is checking a real anchor.

**Risk Assessment:** LOW. Documentation and catalog steps track the real files. They inherit 05-01's template-selection failure if that is not fixed first.

## Cross-plan

D-01 through D-09 are assigned to tasks that touch the right files, and the wave order is right: baseline, then markup, then overrides, then paired Breaking/migration. The class-key mechanism, German catalog, icon registry, and block-inheritance fix are verified in source.

Two claims do not survive the code. The `/author/` path in 05-01 will not render `crud_views/table/bootstrap5.html` via `DJANGO_TABLES2_TEMPLATE` alone, so PAGE-01 can freeze the wrong DOM. The repeated-query assertion in 05-02 contradicts `querystring_replace` and the ban on changing `cv_querystring`.

**Overall risk: HIGH** until those two are corrected. After that, the phase is a markup and theme-contract change with a clear baseline, not a pagination-algorithm change.


---

## OpenCode Review (gemini-review)

## 05-01

### Summary
Plan `05-01` is well-structured and accurately grounded in the existing template, tag, and button-class seams (`src/crud_views/templates/crud_views/table/bootstrap5.html:61-99`, `src/crud_views/templates/crud_views/snippets/pagination.html:1-34`, `src/crud_views/lib/button_classes.py:84-86`). It enforces the `PAGE-01` / `D-06` baseline-first git commit for table pagination goldens before modifying production templates, pins raw card pagination UTF-8 bytes before swapping literal `visually-hidden` classes for `{% cv_button_class 'pagination' 'hidden-label' %}`, and keeps the `DEFAULT_BUTTON_CLASSES` key count (`70 -> 71`) synchronized between `tests/test1/test_button_classes.py:87,94-98` and `docs/reference/buttons.md:144`. Two minor template/documentation details in `05-01-01` and `05-01-03` merit explicit care during execution so golden captures and existing doc-section regex tests do not trip.

### Strengths
- **Accurate `DJANGO_TABLES2_TEMPLATE` and `AuthorListView` wiring**: `tests/test1/conftest.py:116` sets `DJANGO_TABLES2_TEMPLATE="django_tables2/bootstrap5.html"` globally, while `AuthorListView` (`tests/test1/app/views.py:63-71`) inherits `paginate_by: int = 10` from `ListViewTableMixin` (`src/crud_views/lib/views/mixins.py:283-294`) and renders via `{% render_table table %}` (`src/crud_views/templates/crud_views/view_list_table.content.html:3`). Overriding `DJANGO_TABLES2_TEMPLATE="crud_views/table/bootstrap5.html"` and monkeypatching `AuthorListView.paginate_by = 1` with `author_douglas_adams` (`tests/test1/conftest.py:184-187`) and `author_terry_pratchett` (`tests/test1/conftest.py:226-229`) exercises the full `SingleTableMixin.get_table()` -> `RequestConfig` path (`django_tables2/views.py:41-43,118`), and extracting only the `<nav>` fragment (`src/crud_views/templates/crud_views/table/bootstrap5.html:63-97`) avoids non-deterministic `Author.id` UUIDs (`tests/test1/app/models.py:14`).
- **Dual-layer card regression protection (`05-01-02`)**: Capturing unnormalized `rendered.encode("utf-8")` in `raw_pages.json` before replacing the four `class="visually-hidden"` literals at `src/crud_views/templates/crud_views/snippets/pagination.html:7,11,25,29` proves byte-for-byte identity on top of the whitespace-normalized goldens in `tests/test1/test_card_order.py:215-227` (`tests/test1/golden/card_pagination/page1.html:1`, `page2.html:1`).
- **Zero-widening W362 integration (`05-01-03`)**: Because `button_class_check_messages()` (`src/crud_views/lib/button_classes.py:279-297`) checks `if key in DEFAULT_BUTTON_CLASSES or _is_action_mode_key(key): continue` (`line 280`) while `_action_key_parts()` (`lines 211-226`) restricts three-segment mode keys to `VARIANT_LOCATIONS = frozenset({"context", "list", "card"})` (`line 207`) and `parts[0] == "form" and parts[1] in FORM_KINDS` (`lines 208,223`), adding `"pagination:hidden-label": "visually-hidden"` to `DEFAULT_BUTTON_CLASSES` (`lines 84-86`) automatically admits theme/settings overrides for `pagination:hidden-label` and rejects `pagination:hidden-label:icon` with `crud_views.W362` (`lines 291-296`).

### Concerns
- **[MEDIUM] Ambiguity in `05-01-01` on whether disabled `<li>` elements in `table/bootstrap5.html` retain the `previous` / `next` classes**: `src/crud_views/templates/crud_views/table/bootstrap5.html:67,88` currently renders `<li class="previous page-item">` and `<li class="next page-item">` when enabled, whereas `src/crud_views/templates/crud_views/snippets/pagination.html:6,10,24,28` uses `<li class="page-item">` and `<li class="page-item disabled">`. In `05-01-01` (`<action>`), the plan states *"Preserve the previous/next li classes and all table block names"* and two sentences later states *"Disabled directions render li.page-item.disabled containing a.page-link..."*. Whether the disabled branch in `table/bootstrap5.html` should render `<li class="previous page-item disabled">` / `<li class="next page-item disabled">` or `<li class="page-item disabled">` affects both the regenerated `tests/test1/golden/table_pagination/page1.html` and `page2.html` goldens and the documented override recipe in `05-03-01`.
- **[LOW] Placement of new prose in `docs/reference/buttons.md` (`05-01-03`) must respect existing `_section()` slices in `tests/test1/test_label_mode_docs.py`**: `tests/test1/test_label_mode_docs.py:308` slices `_section(buttons, "## The class table").split("\n| Key | Default |")[0]`, and `test_label_mode_docs.py:502-504` asserts phrases inside `_section(BUTTONS_MD.read_text(), "### Container element and label")` (`docs/reference/buttons.md:196-225`), where `_section()` (`test_label_mode_docs.py:35-45`) stops at the next heading of the same or higher level (`<= ###`). Adding a new `###` subheading inside `### Container element and label` before line 218 of `docs/reference/buttons.md` would truncate `_section()` and break `test_filter_toggle_reference_contract`.
- **[LOW] Outer `{% if table.page.has_previous or table.page.has_next %}` guard around `pagination.range` in `src/crud_views/templates/crud_views/table/bootstrap5.html:75`**: Line 62 already guards the entire `<nav>` with `{% if table.page and table.paginator.num_pages > 1 %}`, and line 75 wraps `{% block pagination.range %}` in `{% if table.page.has_previous or table.page.has_next %}`. While redundant for any valid `1 <= page.number <= num_pages` when `num_pages > 1`, keeping or removing line 75 should not inadvertently alter block reachability when `pagination.range` is overridden in `05-02-01`.

### Suggestions
- In `05-01-01`, specify explicitly whether the disabled `<li>` in `src/crud_views/templates/crud_views/table/bootstrap5.html` carries `class="previous page-item disabled"` / `class="next page-item disabled"` (preserving `previous`/`next` on the `<li>` in both states) or `class="page-item disabled"`, and keep the exact same class list in `05-03-01`'s documented override fence.
- In `05-01-03`, place the `pagination:hidden-label` explanation in `docs/reference/buttons.md` alongside the `<location>:hidden-label` utility paragraph at `docs/reference/buttons.md:152-156` (after the `The default table has 71 keys` paragraph at `line 144` and before `### Button row as a list` at `line 163`), without introducing a new `###` heading inside `### Container element and label` (`lines 196-225`).

### Risk Assessment
**LOW** — All code changes are confined to two small templates, one dictionary entry in `src/crud_views/lib/button_classes.py`, and focused unit/golden tests. The baseline-first commit and raw-byte card test provide immediate regression signals if any unintended markup or whitespace change occurs.

---

## 05-02

### Summary
Plan `05-02` thoroughly exercises the template block contract (`D-04`, `D-05`), `cv_querystring` prefixed parameter replacement, `table_page_range` ellipsis handling, empty/single-page suppression, German translations, registry icon overrides, and escaping of `pagination:hidden-label` values. Tracing the template-loading and paginator mechanisms in the installed `django-tables2` and Django packages confirms why the spy on `previous_page_number` / `next_page_number` is valuable, while exposing one important implementation detail in `05-02-01` around how an isolated `django.template.Engine` interacts with `django_tables2`.

### Strengths
- **Direct verification of `D-04` / `D-05` via page-number method spies (`05-02-01`)**: In Django's `Page` (`django/core/paginator.py:214-218`), `next_page_number()` and `previous_page_number()` call `self.paginator.validate_number(...)` and raise `EmptyPage` (`paginator.py:23-24`, which does not set `silent_variable_failure = True`). Spying directly on `previous_page_number` and `next_page_number` on first, middle, and last pages proves both that unavailable page-number methods have call count zero and that the `pagination.previous` / `pagination.next` blocks themselves still execute on disabled ends.
- **Grounded multi-table query and multivalue preservation check (`05-02-02`)**: `cv_querystring` (`src/crud_views/templatetags/crud_views.py:25,288-296`) delegates to `django_tables2.templatetags.django_tables2.querystring_replace` (`django_tables2/templatetags/django_tables2.py:47-76`), which copies `dict(context["request"].GET)` (`line 58`, preserving `MultiValueDict`'s underlying `list` values per key) and formats `escape("?" + urlencode(params, doseq=True))` (`line 70`). Testing `prefix="authors-"` alongside `books-page`, repeated `tag` parameters, non-ASCII filters, and hostile query characters (`"`, `&`, `<`, `>`) directly verifies `T-05-01` and `T-05-04`.
- **Sentinel `gettext` patch in addition to `translation.override("de")` (`05-02-02`)**: Django's `TranslateNode.render()` (`django/templatetags/i18n.py:84-90`) resolves translated literals through `django.utils.translation._trans.gettext` (the exact seam already used in `tests/test1/test_alerts.py:208-216`). Combining `translation.override("de")` (`Seitennavigation`, `zurück`, `weiter` from `src/crud_views/locale/de/LC_MESSAGES/django.po:277-291`) with a sentinel patch on `_trans.gettext` guarantees that all three msgids (`pagination`, `previous`, `next`) are dynamically translated in both enabled and disabled branches.

### Concerns
- **[MEDIUM] Isolated `django.template.Engine` in `05-02-01` cannot be rendered through `{% render_table %}`**: In `05-02-01` (`<action>`), the plan specifies: *"For inherited override templates use an isolated Engine with a locmem loader for child templates and a filesystem loader rooted at tracked `src/crud_views/templates` for the base; register the existing `crud_views`, `django_tables2` and `i18n` libraries."* However, `django_tables2`'s `RenderTableNode.render()` (`django_tables2/templatetags/django_tables2.py:8,154-157`) calls `django.template.loader.get_template(template_name)` / `select_template(template_name)` against the global `settings.TEMPLATES` engine rather than `context.template.engine`. If `_render_table_pagination` invokes `{% render_table table "child.html" %}` on a standalone `Engine`, `get_template("child.html")` will raise `TemplateDoesNotExist` because `child.html` only exists in the standalone `Engine`'s `locmem.Loader`.
- **[LOW] `table.before_render(request)` / `RequestConfig` setup when rendering `table/bootstrap5.html` directly without `{% render_table %}`**: If `_render_table_pagination` instead renders `engine.get_template(...)` directly with `Context({"table": table, "request": request})`, note that `RenderTableNode.render()` (`django_tables2/templatetags/django_tables2.py:165-168`) sets `table.context = context` and calls `table.before_render(request)` before calling `template.render(context={"table": table}, request=request)`, after `RequestConfig(request, paginate=...).configure(table)` (`django_tables2/views.py:118`) has populated `table.page` and `table.paginator`.

### Suggestions
- In `05-02-01`, either:
  1. Reuse the codebase's existing `_theme_templates(overrides)` pattern (`tests/test1/test_form_frame.py:58-68`, also imported in `tests/test1/test_alerts.py:15`), which wraps `override_settings(TEMPLATES=[...])` with `django.template.loaders.locmem.Loader` in front of the filesystem and app_directories loaders so both `get_template()` and `{% render_table %}` resolve `child.html` and `crud_views/table/bootstrap5.html` without leaking state after the `with` block; or
  2. If using a standalone `django.template.Engine`, configure the table via `RequestConfig(request, paginate=paginate).configure(table)` and render `engine.get_template(template_name).render(RequestContext(request, {"table": table}))` directly rather than calling `{% render_table %}`.

### Risk Assessment
**LOW** — This plan is predominantly test and verification work over existing seams (`cv_querystring`, `table_page_range`, `cv_icon`, `cv_button_class`), with production edits restricted to fixing any edge regression uncovered in the two pagination templates.

---

## 05-03

### Summary
Plan `05-03` closes the documentation, migration, localization, and acceptance requirements (`PAGE-04`, `D-05`, `D-08`, `D-09`). In particular, `05-03-01` follows the strong precedent from Phase 4 (`tests/test1/test_alerts.py:249-316`) by extracting the fenced override template directly from `docs/migrating-1.0.md` and rendering it across first, middle, and last pages. Checking `docs/migrating-1.0.md`, `taskfile.yaml`, `src/crud_views/locale/de/LC_MESSAGES/django.po`, and the existing doc-contract tests surfaces a few concrete details to watch during execution.

### Strengths
- **Executable documentation recipe (`05-03-01`)**: Extracting the fenced template under `### Table pagination overrides` in `docs/migrating-1.0.md` and rendering it on first, middle, and last pages in `tests/test1/test_pagination_docs.py` directly prevents documentation drift and verifies that the documented `{% if table.page.has_previous %}` / `{% if table.page.has_next %}` guards work on both enabled and disabled ends (`T-05-05`).
- **Reuse of existing German msgids (`05-03-02`)**: `src/crud_views/locale/de/LC_MESSAGES/django.po:277-291` already defines `msgid "pagination"` -> `"Seitennavigation"`, `msgid "previous"` -> `"zurück"`, and `msgid "next"` -> `"weiter"`, with `table/bootstrap5.html` already referenced on `"previous"` (`line 283`) and `"next"` (`line 289`). Reusing `pagination` in `src/crud_views/templates/crud_views/table/bootstrap5.html:63` (`D-03`, `D-08`) requires no new German translation string.
- **Explicit handling of pre-existing Ruff formatting debt (`05-03-03`)**: `05-03-03` accurately accounts for the known `ruff format --check` failure on eight pre-existing `.planning/` Markdown files (tracked in `.planning/STATE.md:110,119-120`) while enforcing clean formatting on all phase-modified files.

### Concerns
- **[MEDIUM] Running `makemessages -l de` (`05-03-02`) touches unrelated entries in `src/crud_views/locale/de/LC_MESSAGES/django.po` and changes `.mo` bytes if `POT-Creation-Date` is updated**: `src/crud_views/locale/de/LC_MESSAGES/django.po:9` was last generated on `2026-10-22`. Since then, other files in `src/crud_views` have shifted lines or added `gettext_noop("Actions")` (`src/crud_views/lib/button_classes.py:46-47`, whereas `django.po:38-40` only lists `#: lib/table/table.py:28`). Furthermore, `msgfmt` (`compilemessages`) strips `#:` source-reference comments from `django.mo` but compiles the `POT-Creation-Date` header string (`django.po:9`) into `django.mo`. If `makemessages` updates `POT-Creation-Date`, `django.mo` will change bytes even when no `msgid`/`msgstr` pairs changed; if only the `#:` reference comments at `django.po:277-291` are updated and `POT-Creation-Date` is kept unchanged, `django.mo` remains byte-identical.
- **[LOW] Placement of `### Table pagination overrides` in `docs/migrating-1.0.md` (`05-03-01`) relative to existing sections and checklists**: In `docs/migrating-1.0.md`, template contract items under `## A downstream theme` (`line 212`) live as bullets inside `### Contract changes in templates you still override` (`lines 331-404`), followed by `## Silent breaks` (`lines 405-456`). Placing `### Table pagination overrides` at the end of `### Contract changes in templates you still override` (immediately before `## Silent breaks` at `line 405`) avoids splitting the bullet list in `lines 331-404`. In addition, three existing bullets in `docs/migrating-1.0.md` currently speak only of card pagination or omit the new table override break:
  - `docs/migrating-1.0.md:187-190` (`- **Card list pagination** (#241)...` under `### CSS and tests that select on markup`),
  - `docs/migrating-1.0.md:255-257` (`- **snippets/pagination.html**, if you overrode it only for the arrows (#241)...` under `### Templates to delete`),
  - `docs/migrating-1.0.md:429-456` (`**In a theme, or in project template overrides:**` under `## Silent breaks`), and `docs/migrating-1.0.md:38-43` (runtime exceptions in `## Step zero: run the checks`), since an unguarded `pagination.previous` or `pagination.next` override now raises `django.core.paginator.EmptyPage` at render time on the first or last page.
- **[LOW] Fence language tag matching in `tests/test1/test_pagination_docs.py` (`05-03-01`)**: `tests/test1/test_alerts.py:23` uses `TEMPLATE_FENCE = re.compile(r"^```(?:django|html)\n(.*?)^```", re.MULTILINE | re.DOTALL)`, while `docs/reference/buttons.md:299` uses ` ```html+django `. Ensure the fence under `### Table pagination overrides` in `docs/migrating-1.0.md` is unindented and uses ` ```django ` (or allow `(?:django|html(?:\+django)?)` in the test regex) so `_pagination_override_recipe` matches unambiguously.

### Suggestions
- In `05-03-01`, place `### Table pagination overrides` in `docs/migrating-1.0.md` right after line 404 (before `## Silent breaks` at `line 405`), explicitly mention that unguarded `table.page.previous_page_number` / `table.page.next_page_number` calls raise `django.core.paginator.EmptyPage` on the first/last page, and update the existing pagination bullets at `docs/migrating-1.0.md:187-190`, `255-257`, and `422-456` so they stay consistent with the new section.
- In `05-03-02`, after running `makemessages -l de` and `compilemessages -l de`, use `git diff src/crud_views/locale/de/LC_MESSAGES/django.po` to stage only the `pagination` / `previous` / `next` reference updates at `django.po:277-291` (leaving `POT-Creation-Date` and unrelated hunks unstaged) before running `compilemessages -l de`, which keeps `django.mo` byte-identical and the diff strictly scoped to Phase 5.

### Risk Assessment
**LOW** — Documentation, translation catalog references, and acceptance reporting are well-bounded, and the executable doc-recipe test (`tests/test1/test_pagination_docs.py`) + `mkdocs build --strict` provide automated verification of the migration guide and cross-references.

---

## Cross-Plan Summary & Overall Risk Assessment

- **Wave & Dependency Ordering**: The wave structure (`05-01` -> `05-02` -> `05-03`) is clean and free of circular or same-wave file conflicts. `05-01` establishes the baseline table golden commit (`PAGE-01`), implements the template/key changes (`PAGE-02`, `PAGE-03`), and updates `buttons.md` (`71` keys); `05-02` locks down block overrides, query/range preservation, translations, icons, and attribute escaping; `05-03` ships the paired `CHANGELOG.md` / `docs/migrating-1.0.md` update, executable doc test, German catalog reference refresh, and `05-ACCEPTANCE.md`.
- **Overall Risk**: **LOW**. Addressing the three main implementation details noted above—(1) consistent `<li>` class lists on disabled table pagination ends between `table/bootstrap5.html` (`05-01-01`) and the documented override recipe (`05-03-01`), (2) using `_theme_templates` or direct `Engine.get_template().render()` instead of `{% render_table %}` when testing in-memory child templates (`05-02-01`), and (3) scoping `django.po` hunks so `makemessages` does not pull in unrelated line-number/header churn (`05-03-02`)—will allow all three plans to execute smoothly on the first pass.


---

## Consensus Summary

All three reviewers completed source-cited reviews of all three plans; Grok succeeded on a longer-timeout retry. Fable and Gemini judge the scope low risk. Grok identified a confirmed HIGH test-template selection defect that the other reviewers missed. These are plan reviews, not claims that the unimplemented changes pass tests. The source-grounding audit below records the configured index's limitations separately from direct repository evidence.

### Agreed Strengths

- Baseline-first table history and preserved card output have explicit tasks and real test/template seams.
- The shared utility requires one default key, not broader action-key grammar; the live 70-key source baseline supports the planned 71-key count.
- The direction-block names, query-string implementation, German msgids, and existing icon settings match the plans.
- Serial waves prevent same-file writers; an executable migration recipe and paired Breaking/migration commit make the new override contract reviewable.

### Agreed Concerns

- **A02, MEDIUM — Make the isolated renderer executable as specified.** Fable flags request/context setup and deviation from existing scoped template helpers; Gemini traces `render_table` through the global template loader. Clarify direct standalone-engine rendering and explicit request/table preparation, or choose the existing scoped loader helper. Both cite the actual source mechanism.
- **A04, MEDIUM — Define catalog header handling before compilation.** Both flag `makemessages` header/reference churn. Gemini correctly distinguishes source references from compiled header strings; merely staging selected `.po` hunks does not alter the working file used by `compilemessages`.
- Fable and Gemini discuss recipe helper/fence conventions. The existing executable-recipe acceptance already requires extracting and rendering the actual documented fence; helper reuse and its exact supported tag are implementation details, not an additional blocker.

### Divergent Views

- Grok challenges the real-view template selection; Fable/Gemini accept the settings override. H01 is independently reproduced and takes precedence over that reviewer agreement.
- Grok claims repeated-query values are lost; Fable/Gemini say they survive. H02 is refuted by the direct render below.

- Fable questions the new JSON/raw-capture flag convention; Gemini calls the dual raw/normalized card regression protection a strength. Exact-byte protection is already required; The plan explicitly selects the JSON capture and a one-time switch (`05-01-PLAN.md:175-185`); using a different convention is an optional infrastructure preference, not an uncovered execution requirement.
- Gemini requests explicit disabled `previous`/`next` classes; Fable accepts the markup plan as sound. A06 is a precision improvement, not a reopened D-04/D-07 decision.
- Fable's proposed card-list reference expansion is optional: the existing page describes card behavior without claiming exclusive icon ownership. The card reference does not claim exclusive ownership, and expanding it is optional discoverability scope rather than a missing phase requirement.

## Concern disposition and cycle counting

Grok raised two HIGH concerns. H01 is independently confirmed and remains unresolved. H02 is independently disproved by a direct Django/template probe and is closed as a factual false positive, not silently suppressed by the consensus gate. All three final reviewer sections contain source citations and no evidence discount marker; the two-reviewer gate therefore engages. H01 is a correctness judgment supported by a verified source fact, so its single-reviewer origin does not suppress it. H02's premise is refuted, rather than merely uncorroborated. HIGH severity words in the plans' threat registers are not new review findings.

### HIGH concern verification

- **H01 — HIGH, unresolved, Grok:** the real-view baseline fixture in `05-01-PLAN.md:123-124` only overrides `DJANGO_TABLES2_TEMPLATE`, but the already-created `AuthorTable` retains upstream `_meta.template_name`. `TableOptions.__init__` reads settings at class construction (`.venv/lib/python3.12/site-packages/django_tables2/tables.py:121` and `:152`); `AuthorTable` is defined at `tests/test1/app/views.py:56`, after the test default is set at `tests/test1/conftest.py:116`. `RenderTableNode` uses `table.template_name` (`.venv/lib/python3.12/site-packages/django_tables2/templatetags/django_tables2.py:151`). A direct probe confirmed both `_meta.template_name` and the instantiated table's `template_name` remain `django_tables2/bootstrap5.html` within the planned settings override. **Required change:** explicitly select the tracked template on the test table/class/instance before capture and assert its origin or distinguishing markup. Keep that selection scoped/restored. Capture the baseline only after proving the real view renders the intended template.
- **H02 — HIGH, refuted/closed with verification, Grok:** the assertion that `dict(QueryDict)` drops repeated values is false in the installed environment. After the repository's `pytest_configure()`, `dict(QueryDict("tag=a&tag=b&authors-page=1"))` returns `{'tag': ['a', 'b'], 'authors-page': ['1']}`. Rendering `{% load crud_views %}{% cv_querystring "authors-page"=2 %}` with the request in `Context` emits `?tag=a&amp;tag=b&amp;authors-page=2`. This directly exercises `cv_querystring` and its installed tables2 delegate. **Do not weaken the repeated-query acceptance criterion** as Grok suggested. Fable and Gemini correctly describe the list-preserving implementation; `QuerystringNode` uses `urlencode(..., doseq=True)` (`.venv/lib/python3.12/site-packages/django_tables2/templatetags/django_tables2.py:58`, `:70`). No change to the plans is needed for H02.

The successful probe command uses `.venv/bin/python`, imports/calls `tests.test1.conftest.pytest_configure`, imports `QueryDict`, `RequestFactory`, `override_settings`, `Template`, `Context`, `AuthorTable`, and `AuthorListView`; creates the two-value request; renders the tag; and constructs `AuthorTable([], view=AuthorListView())` inside the override. It exits 0 without database or filesystem writes. An initial probe omitted the required `view` table argument and raised `ValueError`; the corrected probe supplies it. Both query outputs were identical. A remaining unclassified PAGE-01 probe is already explicitly carried by `05-01-PLAN.md:300` and `05-03-PLAN.md:202`; it is not an invisible executor task. No implementation completion is claimed.

The following non-HIGH items remain actionable because the current plans neither incorporate the specific refinement nor explicitly defer/reject it. Related execution gaps are deduplicated by required plan change; optional style/infrastructure suggestions do not create new requirements. The parent planner can adopt or reject each with rationale; this review changes no locked decision or implementation.

| ID | Severity / reviewer | Concern and required PLAN.md disposition |
|---|---|---|
| A01 | MEDIUM / Fable | New table goldens can contain Unicode arrows before implementation; the existing helper uses locale-dependent `read_text()` (`tests/test1/test_card_order.py:221`). In 05-01 specify explicit UTF-8 reads/writes for new text captures or byte-based IO, and decide whether the already-edited card helper is updated. |
| A02 | MEDIUM / Fable, Gemini | Isolated Engine rendering must resolve local child templates and supply request/pagination state. In 05-02 task 1 state direct `engine.get_template(...).render(...)` with explicit table/request setup, or scoped global loaders; cover `RequestConfig`/`before_render`/table context as needed. `render_table` uses global `get_template` in installed `django_tables2/templatetags/django_tables2.py:154`. |
| A03 | MEDIUM / Fable | Existing card fixtures yield only two pages (`tests/test1/test_card_order.py:32`, `tests/test1/app/views.py:372`). In 05-02 task 2 name the three-page fixture/paginator used for the middle-page parity assertion. |
| A04 | MEDIUM / Fable, Gemini | Specify the `POT-Creation-Date` and unrelated-reference policy in 05-03 task 2, finalize/revert working-tree `.po` hunks before compilation, and verify `.mo` against that final content. Header metadata is part of compiled messages even if only source references were intended to change. |
| A05 | MEDIUM / Fable | In 05-03 task 1 give the migration child template a distinct path and show `DJANGO_TABLES2_TEMPLATE` selection, so copying an extends recipe actually selects that child. Exercise that name in the docs test. |
| A06 | MEDIUM / Gemini | In 05-01 task 1 explicitly settle disabled direction `<li>` class lists and require the 05-03 recipe to match. “Preserve previous/next li classes” and the less-specific `li.page-item.disabled` selector currently allow differing interpretations for the newly introduced disabled branches. |

Already represented or non-actionable observations are excluded:

| Observation | Existing plan evidence / disposition |
|---|---|
| Fable: inspect baseline-only files sooner | `05-01-PLAN.md:127-129` already requires the baseline file list and unchanged production templates/registry before product edits. |
| Fable: register the three libraries | `05-02-PLAN.md:97-98` explicitly names crud_views, django_tables2, i18n. A02 retains only the unresolved render/request setup. |
| Fable: compare semantic structure, not nav spacing or table direction classes | `05-02-PLAN.md:166-167` already specifies exactly that distinction. |
| Fable/Gemini: redundant inner range guard | `05-01-PLAN.md:143-144` preserves range semantics and the outer guard; `05-02-PLAN.md:106-111` tests named-block reachability. Neither reviewer asserts a current correctness defect in the redundant condition. |
| Fable: rerun global formatter rather than copying historical results | `05-03-PLAN.md:178-201` and `:225-226` explicitly require actual outcomes and honest reporting of failures. |
| Fable: 77-test planning baseline not independently executed in reviewer sandbox | An open evidence limitation, not a claimed failure; execution commands are explicit. This review does not represent the reviewer as having rerun that baseline. |

Optional suggestions are retained in the reviewer sections but do not expand execution scope:

- Raw-card JSON versus individual HTML captures: the plan already specifies a one-time, immutable raw baseline and exact UTF-8 comparison (`05-01-PLAN.md:175-185`). Fable and Gemini disagree on convention, not the required byte-identity proof.
- Additional raw href assertions: `05-02-PLAN.md:147-153` already checks decoded hostile values and actual parsed DOM injection, the mechanism under test. Fable's extra raw assertion is optional redundancy.
- Pinning `DJANGO_TABLES2_PAGE_RANGE`: `05-02-PLAN.md:155-159` already requires a long range, deriving expected tokens from the filter and asserting at least one ellipsis. Non-vacuity is explicit; choosing test settings/row count is an executor detail.
- Section/fence parser reuse and precise prose insertion points: `05-03-PLAN.md:114-120` requires extracting and rendering the actual fence, with absent/ambiguous fences failing at `:130`; `05-03-PLAN.md:217` runs the full Python suite including existing documentation section-contract tests. No particular helper refactor or heading placement is required to satisfy those outcomes.
- Existing migration checklist wording/card-list cross-reference expansion: `05-03-PLAN.md:99-112` already requires the new guarded contract and preserving card history. The old card-specific passages remain true, and optional cross-links do not expose a contradictory public contract.

Grok's additional non-HIGH observations are already covered: `05-01-PLAN.md:28` requires an active li and `:117` requires exactly one active item; the existing card active assertion remains, and 05-02 permits strengthening it. The W362 task already specifies the warning ID (`05-01-PLAN.md:218`) without requiring an “unknown mode” message. Recipe ambiguity is a declared failure (`05-03-PLAN.md:130`), and the CHANGELOG task links the migration section (`:111-112`). Its suggestion to keep the key/count in one commit differs from the explicit task-1/task-3 sequencing acknowledged at `05-01-PLAN.md:92-93`; it does not add an unplanned requirement.

CYCLE_SUMMARY: current_high=1 current_actionable=6


## Review execution and diagnostics

- Selection: configured `review.default_reviewers` identities `fable-review`, `grok-review`, `gemini-review`; no reviewer flags. Host Codex; Claude/OpenCode are external adapters. All adapters used the workflow's `review-lane invoke` seam with pinned instance models and resolved high effort. No subagents were spawned by this orchestrator.
- Initial lanes ran concurrently because `review.parallel_lanes=true`. Fable and Gemini returned complete source-cited reviews; neither required trimming. Initial Grok attempt reached OpenCode's 660-second timeout, left `[spawn error: ETIMEDOUT]` in stderr, and only two progress sentences in its report. The runner reported `ok:true` on that partial text; this orchestrator correctly classified it as incomplete (zero of three plan IDs), not a usable verdict.
- Recovery: copied the initial Grok report/stderr to `gsd-review-grok-review-attempt1.md/.err`, then reran the same adapter/model with a 1,200-second timeout from a temporary config snapshot selected using `--cwd`; actual process working directory and `--repo-root` remained this repository. Repository configuration was not changed. Retry completed with a substantive source-cited review of all three plans and empty stderr.
- Final plan coverage: Fable 3/3, Grok 3/3, Gemini 3/3. No final discount markers, skipped lanes, trimmed inputs, or missing plan sections. The initial timeout remains part of the evidence; recovery does not erase it.
- Diagnostics are preserved in the unique run subdirectory under `.planning/phases/05-table-pagination-parity/.review-diagnostics/`; reviewer outputs and nonempty stderr only, not duplicate prompt/plan inputs. Only `05-REVIEWS.md` is committed by this workflow.


## Verification coverage

`plan_review.source_grounding` is enabled. `drift-guard authority --raw` resolved **intel**; `.planning/intel/API-SURFACE.md:5` explicitly reports an empty JS-oriented index. Absence there is unknown, not missing. Therefore Python/framework/template symbols and signatures are **UNCHECKABLE** at that authority, with supplemental real-source reads recorded below. Existing paths were verified on disk; no signature compatibility is claimed from textual search.

The inventory contains **122 audit rows**: 37 VERIFIED existing paths, 53 UNCHECKABLE symbols/flags/qualified references, and 32 explicitly excluded future-artifact declaration/path rows. Each existing verdict was submitted to `drift-guard severity --status <verdict> --authority intel`: VERIFIED returned `severity=none, hardBlock=false`; UNCHECKABLE returned `severity=INFO, hardBlock=false`. No MISSING or AMBIGUOUS verdict, acknowledgement gate, or hard block was produced. Supplemental source evidence is not promoted to index/signature verification.

All cited new test helpers, test functions, table/raw-card captures, acceptance and summary artifacts are excluded even when a later wave consumes them. HTML attributes/CSS selectors are checked as markup contracts, not language declarations. The plans cite no Python decorators or dataclass/struct declarations requiring a separate declaration check. Qualified inherited `AuthorListView.paginate_by`, table Page methods, built-in `str.encode`, CLI flags and environment setup have explicit coverage rows.

CLI help checks confirmed the installed pytest, MkDocs, Ruff and Django command families used by the plans; npm's general help returned exit 1, so its flag remains UNCHECKABLE rather than asserted verified. No phase tests or quality gates were rerun by this orchestrator; the pass is source/plan verification. The external reviewers identify their own test-execution limits. Research and Nyquist artifacts were intentionally skipped by user instruction and are not missing prerequisites.

For reproducibility, all plan references below are relative to `.planning/phases/05-table-pagination-parity/` when shortened. `file:line` evidence for dependency symbols names the installed Python 3.12 environment, not a repository API guarantee across the entire support matrix.

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
| Path `tests/test1/test_button_classes_checks.py` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:236`: “<automated>.venv/bin/pytest tests/test1/test_table_template.py tests/test1/test_card_order.py tests/test1/test_button_classes.py tests/test1/test_button_classes_checks.py -q</automated>” | VERIFIED | tests/test1/test_button_classes_checks.py:1 (exists) |
| Path `.planning/phases/05-table-pagination-parity/05-01-SUMMARY.md` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:275`: “- Execution summary .planning/phases/05-table-pagination-parity/05-01-SUMMARY.md with both baseline SHAs.” | SKIPPED — new artifact | Declared phase output; excluded from missing-symbol findings. |
| Path `docs/migrating-1.0.md` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:85`: “docs/migrating-1.0.md” | VERIFIED | docs/migrating-1.0.md:1 (exists) |
| Path `docs/reference/list_view.md` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:86`: “docs/reference/list_view.md” | VERIFIED | docs/reference/list_view.md:1 (exists) |
| Path `src/crud_views/locale/de/LC_MESSAGES/django.po` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:136`: “src/crud_views/locale/de/LC_MESSAGES/django.po” | VERIFIED | src/crud_views/locale/de/LC_MESSAGES/django.po:1 (exists) |
| Path `docs/reference/icons.md` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:137`: “docs/reference/icons.md” | VERIFIED | docs/reference/icons.md:1 (exists) |
| Path `.planning/phases/05-table-pagination-parity/05-02-SUMMARY.md` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:227`: “New execution summary .planning/phases/05-table-pagination-parity/05-02-SUMMARY.md.” | SKIPPED — new artifact | Declared phase output; excluded from missing-symbol findings. |
| Path `CHANGELOG.md` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:11`: “- CHANGELOG.md” | VERIFIED | CHANGELOG.md:1 (exists) |
| Path `tests/test1/test_pagination_docs.py` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:12`: “- tests/test1/test_pagination_docs.py” | SKIPPED — new artifact | Declared phase output; excluded from missing-symbol findings. |
| Path `src/crud_views/locale/de/LC_MESSAGES/django.mo` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:14`: “- src/crud_views/locale/de/LC_MESSAGES/django.mo” | VERIFIED | src/crud_views/locale/de/LC_MESSAGES/django.mo:1 (exists) |
| Path `.planning/phases/05-table-pagination-parity/05-ACCEPTANCE.md` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:15`: “- .planning/phases/05-table-pagination-parity/05-ACCEPTANCE.md” | SKIPPED — new artifact | Declared phase output; excluded from missing-symbol findings. |
| Path `taskfile.yaml` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:141`: “taskfile.yaml” | VERIFIED | taskfile.yaml:1 (exists) |
| Path `settings_i18n.py` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:142`: “settings_i18n.py” | VERIFIED | settings_i18n.py:1 (exists) |
| Path `.planning/phases/04-alert-dismiss-adapter/04-ACCEPTANCE.md` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:178`: “.planning/phases/04-alert-dismiss-adapter/04-ACCEPTANCE.md” | VERIFIED | .planning/phases/04-alert-dismiss-adapter/04-ACCEPTANCE.md:1 (exists) |
| Path `.planning/codebase/CONVENTIONS.md` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:198`: “The global formatter currently exits 1 on eight pre-existing planning files: .planning/codebase/CONVENTIONS.md,” | VERIFIED | .planning/codebase/CONVENTIONS.md:1 (exists) |
| Path `.planning/codebase/TESTING.md` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:199`: “.planning/codebase/TESTING.md, phase 01 PATTERNS/RESEARCH, phase 02 RESEARCH/VERIFICATION, and” | VERIFIED | .planning/codebase/TESTING.md:1 (exists) |
| Path `.planning/research/ARCHITECTURE.md` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:200`: “.planning/research/ARCHITECTURE.md and STACK.md. Report the actual global failure and changed-file formatting” | VERIFIED | .planning/research/ARCHITECTURE.md:1 (exists) |
| Path `examples/bootstrap5/manage.py` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:227`: “<automated>.venv/bin/python examples/bootstrap5/manage.py check</automated>” | VERIFIED | examples/bootstrap5/manage.py:1 (exists) |
| Path `.planning/phases/05-table-pagination-parity/05-03-SUMMARY.md` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:261`: “- New .planning/phases/05-table-pagination-parity/05-03-SUMMARY.md.” | SKIPPED — new artifact | Declared phase output; excluded from missing-symbol findings. |
| Symbol `DEFAULT_BUTTON_CLASSES` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:132`: “cases for both pages. Add "pagination:hidden-label": "visually-hidden" to DEFAULT_BUTTON_CLASSES per D-01.” | UNCHECKABLE (intel); supplemental source evidence | `src/crud_views/lib/button_classes.py:15`: DEFAULT_BUTTON_CLASSES: dict[str, str \| None] = { |
| Symbol `EXPECTED_KEYS` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:217`: “Per D-01/D-02/D-08, add pagination:hidden-label to EXPECTED_KEYS, change the expected count to 71,” | UNCHECKABLE (intel); supplemental source evidence | `tests/test1/test_button_classes.py:19`: EXPECTED_KEYS = { |
| Symbol `AuthorListView` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:123`: “fixtures, monkeypatch AuthorListView.paginate_by to 1, and override DJANGO_TABLES2_TEMPLATE to” | UNCHECKABLE (intel); supplemental source evidence | `tests/test1/app/views.py:63`: class AuthorListView(ListViewTableMixin, ListViewPermissionRequired): |
| Symbol `paginate_by` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:114`: “- The real /author/ list with two existing author fixtures and paginate_by=1 renders page 1 and page 2 through crud_views/table/bootstrap5.html.” | UNCHECKABLE (intel); supplemental source evidence | `src/crud_views/lib/views/card.py:25`: paginate_by = None  # set per-view to enable pagination; `src/crud_views/lib/views/mixins.py:293`: paginate_by: int = 10 |
| Symbol `DJANGO_TABLES2_TEMPLATE` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:123`: “fixtures, monkeypatch AuthorListView.paginate_by to 1, and override DJANGO_TABLES2_TEMPLATE to” | UNCHECKABLE (intel); supplemental source evidence | `tests/test1/conftest.py:116`: DJANGO_TABLES2_TEMPLATE="django_tables2/bootstrap5.html",; `.venv/lib/python3.12/site-packages/django_tables2/tables.py:121`: DJANGO_TABLES2_TEMPLATE = getattr( |
| Symbol `CV_UPDATE_GOLDEN` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:126`: “page1.html and page2.html with CV_UPDATE_GOLDEN=1 restricted to test_table_pagination_golden, rerun with” | UNCHECKABLE (intel); supplemental source evidence | `tests/test1/test_heading_level.py:5`: CV_UPDATE_GOLDEN=1 pytest tests/test1/test_heading_level.py; `tests/test1/test_alerts.py:172`: CV_UPDATE_GOLDEN=1 pytest tests/test1/test_alerts.py::test_dismissible_alert_golden |
| Symbol `cv_button_class` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:29`: “- "Both pagination templates resolve pagination:hidden-label through cv_button_class; the default is visually-hidden and configuring sr-only changes both components."” | UNCHECKABLE (intel); supplemental source evidence | `src/crud_views_object_detail/templatetags/crud_views_object_detail.py:108`: def cv_button_class(location, slot, mode=None):; `src/crud_views/templatetags/crud_views.py:525`: def cv_button_class(location, slot, mode=None): |
| Symbol `cv_icon` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:55`: “via: "cv_icon and cv_querystring table.prefixed_page_field"” | UNCHECKABLE (intel); supplemental source evidence | `src/crud_views_object_detail/templatetags/crud_views_object_detail.py:102`: def cv_icon(value, css=""):; `src/crud_views/templatetags/crud_views.py:513`: def cv_icon(value, css=""): |
| Symbol `cv_querystring` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:55`: “via: "cv_icon and cv_querystring table.prefixed_page_field"” | UNCHECKABLE (intel); supplemental source evidence | `src/crud_views/templatetags/crud_views.py:289`: def cv_querystring(parser, token): |
| Symbol `table.prefixed_page_field` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:55`: “via: "cv_icon and cv_querystring table.prefixed_page_field"” | UNCHECKABLE (intel); supplemental source evidence | `.venv/lib/python3.12/site-packages/django_tables2/tables.py:597`: def prefixed_page_field(self): |
| Symbol `has_previous` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:134`: “enclose its own has_previous/has_next conditional per D-04. Preserve the previous/next li classes and all” | UNCHECKABLE (intel); supplemental source evidence | `.venv/lib/python3.12/site-packages/django/core/paginator.py:208`: def has_previous(self): |
| Symbol `has_next` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:134`: “enclose its own has_previous/has_next conditional per D-04. Preserve the previous/next li classes and all” | UNCHECKABLE (intel); supplemental source evidence | `.venv/lib/python3.12/site-packages/django/core/paginator.py:205`: def has_next(self): |
| Symbol `previous_page_number` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:136`: “previous_page_number/next_page_number calls. Disabled directions render li.page-item.disabled containing” | UNCHECKABLE (intel); supplemental source evidence | `.venv/lib/python3.12/site-packages/django/core/paginator.py:217`: def previous_page_number(self): |
| Symbol `next_page_number` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:136`: “previous_page_number/next_page_number calls. Disabled directions render li.page-item.disabled containing” | UNCHECKABLE (intel); supplemental source evidence | `.venv/lib/python3.12/site-packages/django/core/paginator.py:214`: def next_page_number(self): |
| Symbol `table_page_range` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:141`: “Within pagination.range keep table_page_range and its existing ellipsis semantics. Put aria-current="page"” | UNCHECKABLE (intel); supplemental source evidence | `.venv/lib/python3.12/site-packages/django_tables2/templatetags/django_tables2.py:239`: def table_page_range(page, paginator): |
| Symbol `translation.override` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:180`: “test_card_pagination_raw_bytes in test_card_order.py. Render the actual snippet under translation.override("en")” | UNCHECKABLE (intel); supplemental source evidence | `tests/test1/test_lazy_labels.py:63`: with translation.override("de"):; `tests/test1/test_button_container_layout.py:104`: with translation.override("de"): |
| Symbol `Paginator` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:181`: “with Paginator(range(3), 2), its requested Page, is_paginated=True and base_qs=""; serialize the exact two” | UNCHECKABLE (intel); supplemental source evidence | `.venv/lib/python3.12/site-packages/django/core/paginator.py:27`: class Paginator: |
| Symbol `is_paginated` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:181`: “with Paginator(range(3), 2), its requested Page, is_paginated=True and base_qs=""; serialize the exact two” | UNCHECKABLE (intel); supplemental source evidence | `src/crud_views/templatetags/crud_views.py:438`: "is_paginated": context.get("is_paginated", False),; `src/crud_views/templates/crud_views/snippets/pagination.html:2`: {% if is_paginated %} |
| Symbol `base_qs` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:181`: “with Paginator(range(3), 2), its requested Page, is_paginated=True and base_qs=""; serialize the exact two” | UNCHECKABLE (intel); supplemental source evidence | `src/crud_views/templatetags/crud_views.py:434`: base_qs = params.urlencode() if hasattr(params, "urlencode") else "" |
| Symbol `CRUD_VIEWS_BUTTON_CLASSES` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:187`: “Add failing test_card_pagination_shared_hidden_label with CRUD_VIEWS_BUTTON_CLASSES mapping” | UNCHECKABLE (intel); supplemental source evidence | `tests/test1/test_card_blocks.py:67`: CRUD_VIEWS_BUTTON_CLASSES={"card:root": "theme-card", "card:body": "theme-body", "card:title": "theme-title h3"}; `tests/test1/test_button_classes_templates.py:85`: CRUD_VIEWS_BUTTON_CLASSES={"formset:control": "x-ctrl", "formset:control-danger": "x-danger"} |
| Symbol `_isolate_registry` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:220`: “an empty class string. Reuse the existing _isolate_registry fixture. Assert button_class_check_messages()” | UNCHECKABLE (intel); supplemental source evidence | `tests/test1/test_button_container_layout.py:19`: def _isolate_registry():; `tests/test1/test_button_classes.py:77`: def _isolate_registry(): |
| Symbol `button_class_check_messages` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:220`: “an empty class string. Reuse the existing _isolate_registry fixture. Assert button_class_check_messages()” | UNCHECKABLE (intel); supplemental source evidence | `src/crud_views/lib/button_classes.py:237`: def button_class_check_messages() -> list[CheckMessage]: |
| Symbol `W362` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:221`: “accepts the exact utility key from both theme and settings, while a mode suffix still reports W362; the utility” | UNCHECKABLE (intel); supplemental source evidence | `src/crud_views/checks.py:406`: """E360/E361/W362/E363/E364 from the button class table."""; `src/crud_views/lib/button_classes.py:287`: id="crud_views.W362", |
| Symbol `Engine` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:96`: “pagination with RequestFactory. For inherited override templates use an isolated Engine with a locmem loader” | UNCHECKABLE (intel); supplemental source evidence | `.venv/lib/python3.12/site-packages/django/template/engine.py:13`: class Engine: |
| Symbol `RequestFactory` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:96`: “pagination with RequestFactory. For inherited override templates use an isolated Engine with a locmem loader” | UNCHECKABLE (intel); supplemental source evidence | `.venv/lib/python3.12/site-packages/django/test/client.py:370`: class RequestFactory: |
| Symbol `urlsplit` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:150`: “Parse emitted hrefs with urlsplit/parse_qs: enabled numeric/direction links have exactly one authors-page” | UNCHECKABLE (intel); supplemental source evidence | `.venv/lib/python3.12/site-packages/django/test/client.py:11`: from urllib.parse import unquote_to_bytes, urljoin, urlsplit; `.venv/lib/python3.12/site-packages/django/test/client.py:646`: parsed = urlsplit(str(path))  # path can be lazy |
| Symbol `parse_qs` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:150`: “Parse emitted hrefs with urlsplit/parse_qs: enabled numeric/direction links have exactly one authors-page” | UNCHECKABLE (intel); supplemental source evidence | `src/crud_views/lib/views/mixins.py:6`: from urllib.parse import parse_qs, urlencode; `src/crud_views/lib/views/mixins.py:373`: qs = parse_qs(query_string) |
| Symbol `gettext` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:170`: “Patch gettext with distinctive sentinel translations for all three msgids as an additional real-translation” | UNCHECKABLE (intel); supplemental source evidence | `tests/test1/test_alerts.py:210`: def gettext(message):; `tests/test1/test_alerts.py:263`: def gettext(message): |
| Symbol `override_settings` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:177`: “per T-05-02. Reuse scoped override_settings and restore all test registry/translation changes. Strengthen” | UNCHECKABLE (intel); supplemental source evidence | `src/crud_views/lib/settings.py:66`: # it is read raw at call time (override_settings applies) and validated by E108; `src/crud_views/lib/view/label_mode.py:55`: """The raw CRUD_VIEWS_LABEL_MODE_DEFAULTS, read at call time (override_settings applies); _UNSET if absent.""" |
| Symbol `page-previous` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:28`: “- "Table pagination uses the page-previous/page-next registry icons, translated pagination/previous/next labels, an active li with aria-current=page and a non-link span, and disabled direction anchors with aria-disabled=true and no href or tabindex."” | UNCHECKABLE (intel); supplemental source evidence | `src/crud_views/lib/icons.py:33`: "page-previous": "fas:chevron-left",; `src/crud_views/lib/icons.py:71`: "page-previous": "chevron-left", |
| Symbol `page-next` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:28`: “- "Table pagination uses the page-previous/page-next registry icons, translated pagination/previous/next labels, an active li with aria-current=page and a non-link span, and disabled direction anchors with aria-disabled=true and no href or tabindex."” | UNCHECKABLE (intel); supplemental source evidence | `src/crud_views/lib/icons.py:34`: "page-next": "fas:chevron-right",; `src/crud_views/lib/icons.py:72`: "page-next": "chevron-right", |
| Symbol `pagination.previous` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:152`: “- pagination.previous, pagination.range and pagination.next remain overrideable with their original names.” | UNCHECKABLE (intel); supplemental source evidence | `src/crud_views/templates/crud_views/table/bootstrap5.html:66`: {% block pagination.previous %}; `src/crud_views/templates/crud_views/table/bootstrap5.html:73`: {% endblock pagination.previous %} |
| Symbol `pagination.range` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:141`: “Within pagination.range keep table_page_range and its existing ellipsis semantics. Put aria-current="page"” | UNCHECKABLE (intel); supplemental source evidence | `src/crud_views/templates/crud_views/table/bootstrap5.html:76`: {% block pagination.range %}; `src/crud_views/templates/crud_views/table/bootstrap5.html:84`: {% endblock pagination.range %} |
| Symbol `pagination.next` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:152`: “- pagination.previous, pagination.range and pagination.next remain overrideable with their original names.” | UNCHECKABLE (intel); supplemental source evidence | `src/crud_views/templates/crud_views/table/bootstrap5.html:87`: {% block pagination.next %}; `src/crud_views/templates/crud_views/table/bootstrap5.html:94`: {% endblock pagination.next %} |
| Symbol `table-wrapper` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:107`: “set remains table-wrapper, table, table.thead, table.tbody, table.tbody.row, table.tbody.empty_text, table.tfoot,” | UNCHECKABLE (intel); supplemental source evidence | `src/crud_views/templates/crud_views/table/bootstrap5.html:5`: {% block table-wrapper %}; `src/crud_views/templates/crud_views/table/bootstrap5.html:101`: {% endblock table-wrapper %} |
| Symbol `table.thead` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:107`: “set remains table-wrapper, table, table.thead, table.tbody, table.tbody.row, table.tbody.empty_text, table.tfoot,” | UNCHECKABLE (intel); supplemental source evidence | `src/crud_views/templates/crud_views/table/bootstrap5.html:9`: {% block table.thead %}; `src/crud_views/templates/crud_views/table/bootstrap5.html:27`: {% endblock table.thead %} |
| Symbol `table.tbody` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:107`: “set remains table-wrapper, table, table.thead, table.tbody, table.tbody.row, table.tbody.empty_text, table.tfoot,” | UNCHECKABLE (intel); supplemental source evidence | `src/crud_views/templates/crud_views/table/bootstrap5.html:28`: {% block table.tbody %}; `src/crud_views/templates/crud_views/table/bootstrap5.html:31`: {% block table.tbody.row %} |
| Symbol `table.tbody.row` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:107`: “set remains table-wrapper, table, table.thead, table.tbody, table.tbody.row, table.tbody.empty_text, table.tfoot,” | UNCHECKABLE (intel); supplemental source evidence | `src/crud_views/templates/crud_views/table/bootstrap5.html:31`: {% block table.tbody.row %}; `src/crud_views/templates/crud_views/table/bootstrap5.html:37`: {% endblock table.tbody.row %} |
| Symbol `table.tbody.empty_text` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:107`: “set remains table-wrapper, table, table.thead, table.tbody, table.tbody.row, table.tbody.empty_text, table.tfoot,” | UNCHECKABLE (intel); supplemental source evidence | `src/crud_views/templates/crud_views/table/bootstrap5.html:40`: {% block table.tbody.empty_text %}; `src/crud_views/templates/crud_views/table/bootstrap5.html:42`: {% endblock table.tbody.empty_text %} |
| Symbol `table.tfoot` | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:107`: “set remains table-wrapper, table, table.thead, table.tbody, table.tbody.row, table.tbody.empty_text, table.tfoot,” | UNCHECKABLE (intel); supplemental source evidence | `src/crud_views/templates/crud_views/table/bootstrap5.html:47`: {% block table.tfoot %}; `src/crud_views/templates/crud_views/table/bootstrap5.html:57`: {% endblock table.tfoot %} |
| Phase-produced artifact declaration | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:266`: “- Public class key pagination:hidden-label in DEFAULT_BUTTON_CLASSES; no new public function/class/tag.” | SKIPPED — explicitly new | Excluded by grounding contract, including cross-plan use in later waves. |
| Phase-produced artifact declaration | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:267`: “- New files tests/test1/golden/table_pagination/page1.html and tests/test1/golden/table_pagination/page2.html.” | SKIPPED — explicitly new | Excluded by grounding contract, including cross-plan use in later waves. |
| Phase-produced artifact declaration | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:268`: “- New file tests/test1/golden/card_pagination/raw_pages.json.” | SKIPPED — explicitly new | Excluded by grounding contract, including cross-plan use in later waves. |
| Phase-produced artifact declaration | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:269`: “- New test-only symbols in test_table_template.py: paginated_author_client, _table_pagination,” | SKIPPED — explicitly new | Excluded by grounding contract, including cross-plan use in later waves. |
| Phase-produced artifact declaration | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:270`: “_check_table_golden, test_table_pagination_golden, test_table_pagination_accessible_structure,” | SKIPPED — explicitly new | Excluded by grounding contract, including cross-plan use in later waves. |
| Phase-produced artifact declaration | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:271`: “test_table_pagination_shared_hidden_label.” | SKIPPED — explicitly new | Excluded by grounding contract, including cross-plan use in later waves. |
| Phase-produced artifact declaration | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:272`: “- New test-only symbols in test_card_order.py: _render_card_pagination_raw, test_card_pagination_raw_bytes,” | SKIPPED — explicitly new | Excluded by grounding contract, including cross-plan use in later waves. |
| Phase-produced artifact declaration | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:273`: “test_card_pagination_shared_hidden_label; capture environment flag CV_UPDATE_CARD_PAGINATION_RAW.” | SKIPPED — explicitly new | Excluded by grounding contract, including cross-plan use in later waves. |
| Phase-produced artifact declaration | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:274`: “- New test test_pagination_hidden_label_registry_contract in test_button_classes.py.” | SKIPPED — explicitly new | Excluded by grounding contract, including cross-plan use in later waves. |
| Phase-produced artifact declaration | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:275`: “- Execution summary .planning/phases/05-table-pagination-parity/05-01-SUMMARY.md with both baseline SHAs.” | SKIPPED — explicitly new | Excluded by grounding contract, including cross-plan use in later waves. |
| Phase-produced artifact declaration | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:220`: “No new production symbols or files. New test-only symbols in tests/test1/test_table_template.py:” | SKIPPED — explicitly new | Excluded by grounding contract, including cross-plan use in later waves. |
| Phase-produced artifact declaration | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:221`: “PaginationTable, _render_table_pagination, _assert_pagination_accessibility,” | SKIPPED — explicitly new | Excluded by grounding contract, including cross-plan use in later waves. |
| Phase-produced artifact declaration | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:222`: “test_table_pagination_direction_overrides, test_table_pagination_range_override,” | SKIPPED — explicitly new | Excluded by grounding contract, including cross-plan use in later waves. |
| Phase-produced artifact declaration | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:223`: “test_table_template_block_contract, test_table_pagination_prefixed_query_preservation,” | SKIPPED — explicitly new | Excluded by grounding contract, including cross-plan use in later waves. |
| Phase-produced artifact declaration | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:224`: “test_table_pagination_range_and_empty_cases, test_pagination_component_parity,” | SKIPPED — explicitly new | Excluded by grounding contract, including cross-plan use in later waves. |
| Phase-produced artifact declaration | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:225`: “test_table_pagination_labels_translated and test_table_pagination_registry_overrides.” | SKIPPED — explicitly new | Excluded by grounding contract, including cross-plan use in later waves. |
| Phase-produced artifact declaration | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:226`: “New test_card_pagination_empty_cases in tests/test1/test_card_order.py.” | SKIPPED — explicitly new | Excluded by grounding contract, including cross-plan use in later waves. |
| Phase-produced artifact declaration | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:227`: “New execution summary .planning/phases/05-table-pagination-parity/05-02-SUMMARY.md.” | SKIPPED — explicitly new | Excluded by grounding contract, including cross-plan use in later waves. |
| Phase-produced artifact declaration | `.planning/phases/05-table-pagination-parity/05-02-PLAN.md:228`: “Child template fixtures live in the isolated in-memory loader; they are not installed runtime files.” | SKIPPED — explicitly new | Excluded by grounding contract, including cross-plan use in later waves. |
| Phase-produced artifact declaration | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:258`: “- New tests/test1/test_pagination_docs.py, with _pagination_override_recipe and” | SKIPPED — explicitly new | Excluded by grounding contract, including cross-plan use in later waves. |
| Phase-produced artifact declaration | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:259`: “test_documented_pagination_direction_overrides.” | SKIPPED — explicitly new | Excluded by grounding contract, including cross-plan use in later waves. |
| Phase-produced artifact declaration | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:260`: “- New .planning/phases/05-table-pagination-parity/05-ACCEPTANCE.md.” | SKIPPED — explicitly new | Excluded by grounding contract, including cross-plan use in later waves. |
| Phase-produced artifact declaration | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:261`: “- New .planning/phases/05-table-pagination-parity/05-03-SUMMARY.md.” | SKIPPED — explicitly new | Excluded by grounding contract, including cross-plan use in later waves. |
| Phase-produced artifact declaration | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:262`: “- Existing German .mo is regenerated only if its compiled content changes. No new msgid, public symbol or API.” | SKIPPED — explicitly new | Excluded by grounding contract, including cross-plan use in later waves. |
| CLI flag `-q` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:155`: “<automated>.venv/bin/pytest tests/test1/test_table_template.py -q</automated>” | UNCHECKABLE (intel) | CLI invocation/signature is outside JS index authority; existing project commands and installed help used as supplementary checks. |
| CLI flag `--strict` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:131`: “<automated>.venv/bin/mkdocs build --strict</automated>” | UNCHECKABLE (intel) | CLI invocation/signature is outside JS index authority; existing project commands and installed help used as supplementary checks. |
| CLI flag `-m` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:153`: “run from src/crud_views with PYTHONPATH=../.. and ../../.venv/bin/python -m django makemessages -l de” | UNCHECKABLE (intel) | CLI invocation/signature is outside JS index authority; existing project commands and installed help used as supplementary checks. |
| CLI flag `-l` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:153`: “run from src/crud_views with PYTHONPATH=../.. and ../../.venv/bin/python -m django makemessages -l de” | UNCHECKABLE (intel) | CLI invocation/signature is outside JS index authority; existing project commands and installed help used as supplementary checks. |
| CLI flag `--settings` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:154`: “--settings=settings_i18n, then compilemessages -l de with the same interpreter/settings/environment.” | UNCHECKABLE (intel) | CLI invocation/signature is outside JS index authority; existing project commands and installed help used as supplementary checks. |
| CLI flag `-k` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:165`: “<automated>.venv/bin/pytest tests/test1/test_table_template.py tests/test1/test_card_order.py -q -k translated</automated>” | UNCHECKABLE (intel) | CLI invocation/signature is outside JS index authority; existing project commands and installed help used as supplementary checks. |
| CLI flag `-n` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:217`: “<automated>.venv/bin/pytest tests -n auto</automated>” | UNCHECKABLE (intel) | CLI invocation/signature is outside JS index authority; existing project commands and installed help used as supplementary checks. |
| CLI flag `--prefix` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:219`: “<automated>npm --prefix . test</automated>” | UNCHECKABLE (intel) | CLI invocation/signature is outside JS index authority; existing project commands and installed help used as supplementary checks. |
| CLI flag `--check` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:225`: “<automated>.venv/bin/ruff format --check</automated>” | UNCHECKABLE (intel) | CLI invocation/signature is outside JS index authority; existing project commands and installed help used as supplementary checks. |
| Qualified symbol / environment `AuthorListView.paginate_by` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:123`: “fixtures, monkeypatch AuthorListView.paginate_by to 1” | UNCHECKABLE (intel) | tests/test1/app/views.py:63; src/crud_views/lib/views/mixins.py:293 — inherited attribute on ListViewTableMixin |
| Qualified symbol / environment `table.page.has_previous` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:103`: “ones; copied overrides must test table.page.has_previous/has_next” | UNCHECKABLE (intel) | src/crud_views/templates/crud_views/table/bootstrap5.html:65 — table Page availability method |
| Qualified symbol / environment `rendered.encode` | `.planning/phases/05-table-pagination-parity/05-01-PLAN.md:180`: “assertions compare rendered.encode("utf-8") to the stored string encoded as UTF-8” | UNCHECKABLE (intel) | Python str.encode is a built-in; its signature is outside intel/grep authority |
| Qualified symbol / environment `PYTHONPATH` | `.planning/phases/05-table-pagination-parity/05-03-PLAN.md:153`: “run from src/crud_views with PYTHONPATH=../..” | UNCHECKABLE (intel) | taskfile.yaml:98 — existing i18n process environment convention |

## Cross-artifact fact-drift pass

The deterministic status seam returned `{"verdict":"lag","phase":"05","stateStatus":"Ready to execute","roadmapStatus":"Not started","stateRank":1,"roadmapRank":0,"authority":"STATE.md"}`. This is the sanctioned one-step nonterminal lag, not a finding. Both status artifacts are present.

| Fact | Authoritative passage | Paired plan passage | Result |
|---|---|---|---|
| Baseline precedes changes | `.planning/ROADMAP.md:182`: “A golden of today's paginated table is committed first” | `05-01-PLAN.md:27`: “A separate baseline-only commit ... before any pagination markup changes” | Consistent |
| Registry, labels, accessibility, blocks | `.planning/ROADMAP.md:183`: “page-previous / page-next registry icons with translated hidden labels”; `:185`: “Existing tables2 block names still work for overrides” | `05-01-PLAN.md:28` defines matching stock structure; `05-02-PLAN.md:21` preserves reachable direction overrides; `05-03-PLAN.md:26` documents guards | Consistent; CONTEXT D-04/D-05 specify the changed availability contract rather than contradicting block-name preservation |
| Shared class utility | `.planning/ROADMAP.md:186`: “One shared hidden-label class key (default visually-hidden) ... both table and card” | `05-01-PLAN.md:29`: “Both pagination templates resolve pagination:hidden-label through cv_button_class” | Consistent |
| Parity, Breaking/migration, catalogs | `.planning/ROADMAP.md:188`: “same accessible structure. The CHANGELOG Breaking (DOM) entry, the migration bullet and the .po files are updated” | `05-02-PLAN.md:184`: “Both structures pass ... across all three page positions”; `05-03-PLAN.md:26` and `:28` cover migration/catalog and paired commits | Consistent |
| Requirement IDs | `.planning/ROADMAP.md:179`: “PAGE-01, PAGE-02, PAGE-03, PAGE-04” | `05-01-PLAN.md:19`, `05-02-PLAN.md:13`, `05-03-PLAN.md:17` name only those IDs | Consistent; all four represented |
| D-01/D-02 shared name/default card | `05-CONTEXT.md:22`: “pagination:hidden-label”; `:25`: “Both pagination templates ... Preserve default card output” | `05-01-PLAN.md:29` and `:30`; actions `:179` and `:217` | Consistent |
| D-03 navigation msgid | `05-CONTEXT.md:29`: “translated msgid pagination” | `05-01-PLAN.md:133`: “translate the nav msgid pagination” | Consistent |
| D-04/D-05 override contract | `05-CONTEXT.md:33`: “each block cover both its enabled and disabled states”; `:35`: “check direction availability” | `05-02-PLAN.md:21`, `:101`; `05-03-PLAN.md:103` | Consistent |
| D-06/D-07 baseline and markup | `05-CONTEXT.md:40`: “Commit a golden ... before changing its markup”; `:42`: registry icons and hidden labels | `05-01-PLAN.md:27`, `:28`; baseline action and guarded directions in task 1 | Consistent |
| D-08/D-09 release and checks | `05-CONTEXT.md:46`: “Breaking ... migrating-1.0.md in the same change”; `:49`: verify overrides and preserve query/range | `05-03-PLAN.md:28`, `:124`; `05-02-PLAN.md:24` and task 2 | Consistent |

No contradictory pair found among the three allowed judgment axes. D-01 explicitly supersedes PROJECT.md's older table-specific key recommendation; that acknowledged historical reference does not reopen the decision. Agent discretion and deferred ideas were excluded. Cross-plan implementation issues, if raised by reviewers, are handled in concern disposition rather than double-counted here. Advisory drift contributes to neither cycle counter.
