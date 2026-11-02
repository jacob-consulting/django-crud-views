# Cross-AI Plan Review — Phase 06.1 (Cycle 2 at `af5ecdf`)

## Prior Findings Closure Verification (`H1`–`H3`, `A1`–`A10`)

All three prior **HIGH** findings (`H1`, `H2`, `H3`) and all ten non-HIGH findings (`A1`–`A10`) from `06.1-REVIEWS.md:54-69` have been verified against the revised plan actions and the live repository source:

- **H1 (`tests/test1/test_button_classes_templates.py:123-124, 241-265`) — CLOSED:** Plan `06.1-01` now owns `tests/test1/test_button_classes_templates.py` in `files_modified` (`06.1-01-PLAN.md:16`) and Task 2 (`06.1-01-PLAN.md:116, 129-136`). Task 2 assigns `SENTINEL_CLASSES["form:cancel-tag"] = "button"`, excludes that structural tag value from the CSS-only `SENTINELS` frozenset (`test_button_classes_templates.py:124, 137, 147`), preserves all CSS token assertions in `_styled()` / `_offenders()`, and executes `.venv/bin/pytest tests/test1/test_button_classes_templates.py -q` in Task 2's `<verify>` block (`06.1-01-PLAN.md:136`).
- **H2 (`tests/test1/test_form_button_checks.py:894-895`) — CLOSED:** Plan `06.1-01` now owns `tests/test1/test_form_button_checks.py` (`06.1-01-PLAN.md:17, 141`). Task 3 (`06.1-01-PLAN.md:143-150`) removes only `"cv_tag"` from the `action_only` exclusion tuple in `test_non_strict_missing_icon_logs_and_uses_the_label` (`test_form_button_checks.py:894`), adds a positive assertion that `first["cv_tag"] == "button"`, and runs `.venv/bin/pytest tests/test1/test_form_button_checks.py tests/test1/test_label_mode_docs.py -q` before Plan 01 completes.
- **H3 (`tests/test1/test_label_mode_docs.py:759-765` vs `docs/reference/buttons.md:475-496`) — CLOSED:** Plan `06.1-01` Task 3 (`06.1-01-PLAN.md:145-150`) updates `### The form leaf contract` in `docs/reference/buttons.md:475-496` to include the `cv_tag` row and remove `cv_tag` from the action-only exclusion sentence at `docs/reference/buttons.md:476` in the same plan that adds `"cv_tag"` to `FORM_LEAF_KEYS` (`src/crud_views/lib/view/button_data.py:49-67`), and verifies `test_label_mode_docs.py` in Task 3.
- **A1–A10 — CLOSED:**
  - **A1** (`src/crud_views/lib/crispy/buttons.py:128-174`): Addressed in `06.1-01-PLAN.md:101-103` and `06.1-03-PLAN.md:84` by validating explicit `tag` options in `_TableClassMixin.__init__` without invoking `_cv_form_kind()` when `tag` is `None` or `"button"`, preserving quiet `helper.add_input()` slots (`tests/test1/test_crispy_buttons.py:1647`).
  - **A2** (`06.1-01-PLAN.md:105`): Addressed with explicit scope justification in Task 1.
  - **A3** (`06.1-03-PLAN.md:84`): Addressed with explicit `target="_blank"` / `rel="noopener"` recipe guidance and test coverage.
  - **A4** (`src/crud_views/checks.py:406`, `tests/test1/test_button_classes_checks.py:1`): Addressed in `06.1-01-PLAN.md:12, 133, 145`.
  - **A5** (`tests/test1/test_form_buttons_golden.py:120-144`): Addressed in `06.1-02-PLAN.md:94, 108-110` via owning-`<form>` and `a#button-id-reset` scoping.
  - **A6** (`06.1-03-PLAN.md:24, 71, 88, 109`): Addressed by adding `crud_views.E365` as the fourth Phase 7 handoff item.
  - **A7** (`tests/js/viewset.test.js:569-580`): Addressed in `06.1-03-PLAN.md:99, 102` by placing new cancel-link JS tests before `it("loads without jQuery")`.
  - **A8** (`src/crud_views/lib/button_classes.py:122-125`): Addressed in `06.1-02-PLAN.md:112` (scoped `override_settings` in golden page tests) and `06.1-03-PLAN.md:86` (theme registry snapshot/restore in doc tests).
  - **A9** (`.planning/ROADMAP.md:332`): Explicitly disposed in `06.1-01-PLAN.md:184` as orchestrator metadata maintenance.
  - **A10** (`docs/reference/buttons.md:152-153`): Addressed in `06.1-01-PLAN.md:133-135` and `06.1-03-PLAN.md:82`.

---

## 06.1-01

### 1. Summary
Plan `06.1-01` delivers the end-to-end vertical slice for rendering a cancel control as a native `<a>` link through `_TableClassMixin`, `_form_button_data()`, and `crud_views/tags/button/form.html`, registers the `form:cancel-tag` default key and `crud_views.E365` system check in `button_classes.py`, and updates all Wave 1 collateral contract/test/documentation consumers (`test_button_classes_templates.py`, `test_form_button_checks.py`, `docs/reference/buttons.md`, and `checks.py`). The Cycle 2 revisions resolve all three prior blocker findings (`H1`, `H2`, `H3`) and cleanly separate constructor-time explicit-argument validation from render-time inherited table resolution.

### 2. Strengths
- **Clean constructor vs. render validation boundary (`src/crud_views/lib/crispy/buttons.py:128-164`):** Validating explicit `tag` at `_TableClassMixin.__init__` by accepting `None` and `"button"` without calling `_cv_form_kind()`, rejecting non-`"a"` values with `ValueError`, and requiring `self._cv_slot == "form:cancel"` and `self.input_type == "button"` for `tag="a"` enforces D-01/D-09 on both layout controls and `helper.add_input()` while keeping legacy non-form slots like `Button("custom", "Custom", slot="formset:control")` in `tests/test1/test_crispy_buttons.py:1647` completely quiet.
- **Provenance-aware tag selection and fallback ordering (`src/crud_views/lib/view/button_data.py:215-307`):** `_form_button_data()` validates explicit `cv_tag` first, reads `get_button_classes().get("form:cancel-tag")` only when an eligible cancel (`key == "cancel" and button_type == "button"`) has `cv_tag is None`, validates the selected tag before checking `cancel_url` or `disabled` (satisfying D-04 and D-12), and computes effective `cv_tag` for `FORM_LEAF_KEYS` (`src/crud_views/lib/view/button_data.py:49-67`).
- **Complete collateral consumer alignment in Wave 1 (`tests/test1/test_button_classes_templates.py:123-124`, `tests/test1/test_form_button_checks.py:894-895`, `docs/reference/buttons.md:146, 476-496`):** Tasks 2 and 3 update `SENTINEL_CLASSES`/`SENTINELS`, `EXPECTED_KEYS` (`tests/test1/test_button_classes.py:21, 93`), the 73→74 key count in `docs/reference/buttons.md:146`, the `### The form leaf contract` table (`tests/test1/test_label_mode_docs.py:759-765`), and the missing-icon fallback exclusion list (`tests/test1/test_form_button_checks.py:894`) in the same plan where `DEFAULT_BUTTON_CLASSES` and `FORM_LEAF_KEYS` change.
- **Disjoint `E361` and `E365` check branches (`src/crud_views/lib/button_classes.py:251-281`):** Placing `crud_views.E365` as an `elif key == "form:cancel-tag" and isinstance(value, str) and value not in ...` branch after `E361` (`value is not None and not isinstance(value, str)`) ensures non-string values (`3`, `True`, `[]`) emit only `E361`, `None` is accepted, and invalid strings (including `""`) emit `E365`.

### 3. Concerns
- **[LOW] Direct `FORM_LEAF` rendering in `tests/test1/test_button_classes_templates.py:248-251` only exercises the `<button>` branch unless `cv_tag="a"` is also checked:** Once Task 2 sets `SENTINEL_CLASSES["form:cancel-tag"] = "button"` (`06.1-01-PLAN.md:129`), the loop in `test_button_chain_renders_only_table_classes` (`tests/test1/test_button_classes_templates.py:248-251`) renders `FORM_LEAF` for all `FORM_KINDS × LABEL_MODES` using `<button>`, leaving the new `<a>` branch in `src/crud_views/templates/crud_views/tags/button/form.html:1-2` unvisited by the `_offenders(doc)` CSS-token guard.

### 4. Suggestions
- In `tests/test1/test_button_classes_templates.py:248-251`, also call `check(f"form.html:cancel:a:{mode}", html.fromstring(f"<div>{markup}</div>"))` with `cv_button_data(_form_contract("cancel", mode, cv_tag="a"), "form")` for each `mode in sorted(LABEL_MODES)` so the rendering guard verifies that the `<a>` branch in `form.html` likewise emits only table or `cv-` classes.

### 5. Risk Assessment
**LOW** — All three prior HIGH collateral test/documentation blockers (`H1`, `H2`, `H3`) and the constructor/legacy validation boundary (`A1`) are directly resolved in the task file ownership, actions, and verification commands.

---

## 06.1-02

### 1. Summary
Plan `06.1-02` completes the anchor-only attribute filtering and presentation parity in `_form_button_data()` and `form.html`, verifies custom template compatibility and shared/deepcopied adapter isolation in `tests/test1/test_crispy_buttons.py`, and adds opt-in real-page cancel-link integration tests in `tests/test1/test_form_buttons_golden.py` while keeping all default golden files byte-identical.

### 2. Strengths
- **Scoped, case-insensitive anchor attribute filtering (`src/crud_views/lib/view/button_data.py:268-280`):** Running `_form_attrs()` alias normalization first, resolving reserved fields (`id`, `class`, `data-cv-cancel-url`, and icon-mode `title`/`data-cv-tooltip`), determining `effective_tag`, and then stripping the full WHATWG button-only set plus `href`, `data-cv-cancel-url`, and case-variant generated attributes (`id`, `class`, and icon-mode `title`/`data-cv-tooltip`) only when `effective_tag == "a"` guarantees single-`href` anchor safety (D-05, D-07, D-15) while leaving `<button>` attribute serialization untouched (D-17).
- **Form- and ID-scoped page assertions (`tests/test1/test_form_buttons_golden.py:120-134`):** Locating the expected native action (`#submit-id-submit` or `#submit-id-delete`), taking its enclosing `<form>`, and asserting a unique `a#button-id-reset` (and no `button#button-id-reset`) inside that `<form>` prevents false positives from context-toolbar `<a href="/author/">` links on the same page (`A5`) and avoids passing anchor markup through the `<input>`/`<button>`-only `_extract_controls()` helper (`tests/test1/test_form_buttons_golden.py:42-65`).
- **Process-global registry safety in page tests (`tests/test1/test_form_buttons_golden.py`, `src/crud_views/lib/button_classes.py:116-125`):** Using `override_settings(CRUD_VIEWS_BUTTON_CLASSES={"form:cancel-tag": "a"})` with before/inside/after assertions (`06.1-02-PLAN.md:112`) relies on the `setting_changed` cache-reset signal (`button_classes.py:116-119`) and avoids mutating `_THEME_BUTTON_CLASSES` in a module that lacks `_isolate_registry` (`A8`).

### 3. Concerns
- **[LOW] Existing `CUSTOM` template string in `tests/test1/test_crispy_buttons.py:346-350` is asserted by positional index in `test_custom_template_gets_only_normalized_fields` (`test_crispy_buttons.py:407-432`):** If `CUSTOM` itself were edited to insert `{{ cv_tag }}`, `fields[5]` / `fields[10]` and the 15-element list equality in `test_custom_template_gets_only_normalized_fields` would shift. Task 2 (`06.1-02-PLAN.md:90, 105`) rightly specifies keeping `CUSTOM` unchanged and adding a separate tag-aware template fixture.

### 4. Suggestions
- When adding the tag-aware custom template entry to the `custom_templates` locmem loader (`tests/test1/test_crispy_buttons.py:360-370`), add a distinct template key (e.g. `"custom/tag_aware.html"`) rather than modifying `CUSTOM`, so `test_custom_template_gets_only_normalized_fields` (`test_crispy_buttons.py:407-432`) remains an unmodified regression test for pre-existing custom templates.

### 5. Risk Assessment
**LOW** — Attribute filtering, custom-template compatibility, deepcopy isolation, and form-scoped page integration tests are well-bounded and verified against existing fixtures without touching committed golden files.

---

## 06.1-03

### 1. Summary
Plan `06.1-03` publishes the canonical documentation and executable recipes in `docs/reference/buttons.md`, `docs/reference/theme.md`, `docs/migrating-1.0.md`, and `CHANGELOG.md`, adds executable documentation tests in `tests/test1/test_form_button_docs.py`, adds delegated click noninterference tests in `tests/js/viewset.test.js`, and records the full quality gates, browser UAT status, and four-item Phase 7 stability handoff in `06.1-VALIDATION.md`.

### 2. Strengths
- **Complete Phase 7 freeze handoff (`06.1-03-PLAN.md:24, 71, 88, 109`, `06.1-VALIDATION.md:145-148`):** Naming all four public surface additions—`form:cancel-tag`, `Button(tag=...)` (with shared adapter eligibility rules), `cv_tag` in `FORM_LEAF_KEYS`, and `crud_views.E365`—ensures Phase 7's bidirectional `test_stability_doc.py` guard will cover the new check ID alongside the class-table and leaf-context additions (`A6`).
- **Preservation of single-listener ordering in `tests/js/viewset.test.js:92-191, 569-580`:** Task 2 (`06.1-03-PLAN.md:99, 102`) places the new unmarked-anchor and nested-icon/span click tests inside `describe("data-cv-cancel-url", ...)` before the final `it("loads without jQuery")` test (`tests/js/viewset.test.js:571`), preserving the single-listener invariant required by the alert-adapter call-count tests (`A7`).
- **Explicit `target="_blank"` / `rel="noopener"` and legacy `add_input()` documentation (`06.1-03-PLAN.md:84`):** Task 1 documents and tests caller-supplied `target="_blank"` with `rel="noopener"` (`A3`) and accurately documents the constructor-only explicit validation vs. pack-owned rendering boundary for `helper.add_input()` (`A1`).

### 3. Concerns
- **[LOW] `_theme_recipe()` in `tests/test1/test_form_button_docs.py:166-172` uses 1-tuple unpacking over `_section(THEME_MD.read_text(), "## Custom form-button templates")`:** Because `_section()` (`tests/test1/test_label_mode_docs.py:35-45`) stops only at a heading of the same or higher level (`<= 2` for `##`), adding a `###` subheading with a second `python` fence, `django` fence, or `` `.../templates/...html` `` path inside `## Custom form-button templates` in `docs/reference/theme.md:136-190` will cause `(code,) = FENCE.findall(section)`, `(template,) = TEMPLATE_FENCE.findall(section)`, or `(saved,) = re.findall(...)` in `_theme_recipe()` (`test_form_button_docs.py:168-171`) to fail with `ValueError: too many values to unpack` unless `_theme_recipe()` or the heading structure is scoped.
- **[LOW] Substring guards in `tests/test1/test_label_mode_docs.py:842-862` pin exact phrases in `docs/migrating-1.0.md` under `## Form buttons`:** `test_form_buttons_breaking_entry_pairs_with_migration` asserts exact substrings in `_flat(_section(MIGRATING_MD.read_text(), "## Form buttons"))`, including `"raises ValueError when the button renders"`, `"Nothing warns"`, and `"add_input(Submit(...))"`. Editing `### Slots` or `### Filter helpers` in `docs/migrating-1.0.md:284-304` to mention `tag=` must keep those exact phrases intact.

### 4. Suggestions
- In `tests/test1/test_form_button_docs.py:166-172`, either scope `_theme_recipe()` to the introductory block before the first `###` subheading (`section.split("\n### ", 1)[0]`) when adding a `###` subsection for the cancel-capable template recipe in `docs/reference/theme.md`, or place the cancel-link template branch in `docs/reference/buttons.md` / a dedicated `###` helper so `test_documented_pill_template_renders_literal_text` (`test_form_button_docs.py:201`) continues to unpack the `PillSubmit` recipe cleanly.
- In `docs/migrating-1.0.md:264-291`, add the optional `cv_tag` / `Button(tag=...)` note additively without altering the existing sentences pinned by `tests/test1/test_label_mode_docs.py:842-862`.

### 5. Risk Assessment
**LOW** — Plan `06.1-03` already anticipates the recipe-extraction scoping (`06.1-03-PLAN.md:86`) and runs both `test_form_button_docs.py` and `test_label_mode_docs.py` in Task 1's `<verify>` block (`06.1-03-PLAN.md:91`), ensuring any markdown extraction mismatch is caught immediately.

---

## Overall Assessment

- **Plan Coverage:** 3 / 3 plans reviewed (`06.1-01`, `06.1-02`, `06.1-03`).
- **Prior Blockers (`H1`, `H2`, `H3`):** All 3 confirmed **CLOSED** with concrete file ownership, executable actions, and verification shards in `06.1-01-PLAN.md`.
- **Prior Actionable Warnings (`A1`–`A10`):** All 10 confirmed **CLOSED**.
- **Overall Phase Risk:** **LOW** — The three plans are ready for execution.
