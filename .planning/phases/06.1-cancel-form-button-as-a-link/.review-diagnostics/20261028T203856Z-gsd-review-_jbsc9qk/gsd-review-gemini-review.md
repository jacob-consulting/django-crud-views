## 06.1-01

### 1. Summary
Plan `06.1-01` introduces the end-to-end cancel-link rendering path across the crispy form button adapter (`src/crud_views/lib/crispy/buttons.py`), the form button normalizer (`src/crud_views/lib/view/button_data.py`), the bundled form-button leaf template (`src/crud_views/templates/crud_views/tags/button/form.html`), and the layered button class registry (`src/crud_views/lib/button_classes.py`). The design cleanly separates explicit configuration capture (`tag=None` on `_TableClassMixin`), normalizer-level eligibility and validation (`cv_key == "cancel"` and `cv_type == "button"`), fallback resolution (`cv_cancel_url` and HTML `disabled` presence), and static class-table diagnostics (`crud_views.E365`). However, adding `"cv_tag"` to `FORM_LEAF_KEYS` in `06.1-01` while deferring the `### The form leaf contract` table update in `docs/reference/buttons.md` to `06.1-03` will break `tests/test1/test_label_mode_docs.py::test_form_label_mode_reference_contract` across Waves 1 and 2.

### 2. Strengths
- **Clean configuration capture without polluting legacy crispy `flat_attrs` (`src/crud_views/lib/crispy/buttons.py:128-137`):** Consuming `tag=None` as a keyword-only argument on `_TableClassMixin.__init__` before constructing `self._cv_attrs` (line 136) and before calling `super().__init__(name, value, **kwargs)` (line 137) prevents `tag` from being serialized into crispy's `self.flat_attrs`. This preserves both `test_legacy_helper_inputs_stay_inputs_without_warnings` (`tests/test1/test_crispy_buttons.py:289-314`) and `test_constructor_visible_legacy_state_is_crispys` (`tests/test1/test_crispy_buttons.py:623-636`).
- **Raw class-table lookup avoids CSS string coercion (`src/crud_views/lib/button_classes.py:132-152`):** `get_button_class()` (line 152) coerces `None` and non-strings to `""`. Reading `get_button_classes().get("form:cancel-tag")` directly in `_form_button_data()` (`src/crud_views/lib/view/button_data.py:215-307`) is the only way to satisfy D-02 (`None` inherits `"button"`, whereas `""` is an invalid tag value).
- **W362 acceptance without widening the finite mode-key grammar (`src/crud_views/lib/button_classes.py:212-240, 284-302`):** Because `button_class_check_messages()` checks `if key in DEFAULT_BUTTON_CLASSES or _is_action_mode_key(key): continue` (line 285), adding `"form:cancel-tag": "button"` to `DEFAULT_BUTTON_CLASSES` automatically allows the exact structural key while `_action_key_parts()` (lines 216-231) and `FORM_KINDS` (line 213) continue to reject `form:cancel-tag:icon` with `crud_views.W362` (matching `test_form_utility_keys_take_no_mode_suffix` at `tests/test1/test_button_classes.py:342-353`).
- **Two-part eligibility check preserves re-slotted native actions (`src/crud_views/lib/crispy/buttons.py:153-164`):** Requiring both `cv_key == "cancel"` and `cv_type == "button"` ensures that a `Submit` re-slotted to `slot="form:cancel"` (already tested in `test_delete_button_kwargs_may_choose_the_slot` at `tests/test1/test_crispy_buttons.py:80-92` and `CancelSlotForm` at `tests/test1/test_crispy_buttons.py:1315-1336`) remains a native `<button type="submit">` even when a theme registers `form:cancel-tag = "a"`.

### 3. Concerns
- **[MEDIUM] Cross-wave test regression in `tests/test1/test_label_mode_docs.py:757-766` when `FORM_LEAF_KEYS` gains `cv_tag` in Plan 01:**
  `test_form_label_mode_reference_contract` (`tests/test1/test_label_mode_docs.py:759-765`) parses the markdown table under `### The form leaf contract` in `docs/reference/buttons.md:479-495` and asserts `documented_keys == set(FORM_LEAF_KEYS)`. Plan `06.1-01` Task 1 adds `"cv_tag"` to `FORM_LEAF_KEYS` (`src/crud_views/lib/view/button_data.py:49-67`), while Task 2 only updates the key count (`docs/reference/buttons.md:146`) and class-table row in `docs/reference/buttons.md`, deferring the `### The form leaf contract` update to Plan `06.1-03` Task 1. Although `06.1-01`'s task verification shards do not run `test_label_mode_docs.py`, the full test suite and `nox -s crispy_floor` (`noxfile.py:39`) will fail after Wave 1 and Wave 2 until Wave 3 runs.
- **[MEDIUM] Direct `cv_button_data(ctx, "form")` callers omit `cv_tag` while `_cv_button_context()` supplies `cv_tag: None` (`src/crud_views/lib/view/button_data.py:215-228`, `tests/test1/test_button_data.py:445-457`):**
  In `tests/test1/test_button_data.py:445-457`, `form_ctx()` constructs raw dicts without a `"cv_tag"` key, whereas `_TableClassMixin._cv_button_context()` (`src/crud_views/lib/crispy/buttons.py:151-164`) will include `"cv_tag": self._cv_tag` (`None` by default). In `_form_button_data()`, `ctx.get("cv_tag")` returns `None` in both cases, which works for inheritance, but if a caller passes `cv_tag=None` explicitly vs omitting `cv_tag`, both must be treated identically as "not explicitly set" so that `form_ctx("submit")` does not trigger explicit-tag validation or read `form:cancel-tag`. Specifically, for non-eligible controls (`not (key == "cancel" and button_type == "button")`), when `ctx.get("cv_tag") is None`, `_form_button_data()` must immediately resolve `effective_tag = "button"` without reading `get_button_classes().get("form:cancel-tag")`, otherwise an invalid `form:cancel-tag` in settings would break `Submit` and `Reset` rendering.
- **[LOW] Check ordering between `E361` and `E365` in `src/crud_views/lib/button_classes.py:251-281` and stale docstring in `src/crud_views/checks.py:406`:**
  In `button_class_check_messages()` (`src/crud_views/lib/button_classes.py:252-280`), `if value is not None and not isinstance(value, str):` emits `crud_views.E361`. Unlike `E364` at line 272 (`and value and value not in CONTAINER_SINGLE_MODES`, which intentionally ignores `""`), the new `E365` branch for `key == "form:cancel-tag"` must check `value is not None and value not in ("button", "a")` so that `""` is flagged by `E365` per D-02. Additionally, `src/crud_views/checks.py:406` (`"""E360/E361/W362/E363/E364 from the button class table."""`) and `tests/test1/test_button_classes_checks.py:1` are not updated to mention `E365`.
- **[LOW] Whitespace sensitivity in `src/crud_views/templates/crud_views/tags/button/form.html:1-2`:**
  `tests/test1/golden/form_buttons/create.html:1-4` pins the exact two-line `<button ...>\n    class="...">` output. Any newline or space introduced inside the `{% if cv_tag == "a" %}...{% else %}...{% endif %}` tags on line 1 or 2 of `form.html` will break `test_form_button_baselines` (`tests/test1/test_form_buttons_golden.py:149-153`).

### 4. Suggestions
- Update `### The form leaf contract` in `docs/reference/buttons.md:476, 479-495` (removing `cv_tag` from the action-only exclusion list on line 476 and adding the `| \`cv_tag\` |` row to the contract table) in `06.1-01` Task 2 (which already modifies `docs/reference/buttons.md`), and include `tests/test1/test_label_mode_docs.py` in `06.1-01` Task 2's verification command.
- In `_form_button_data()` (`src/crud_views/lib/view/button_data.py`), structure tag resolution explicitly as:
  1. Read `raw_tag = ctx.get("cv_tag")` and `eligible = key == "cancel" and button_type == "button"`.
  2. If `raw_tag is not None`: validate `isinstance(raw_tag, str) and raw_tag in ("button", "a")` (else raise `ValueError`), and if `raw_tag == "a" and not eligible`, raise `ValueError`. Set `selected_tag = raw_tag`.
  3. Else if `not eligible`: set `selected_tag = "button"` (never reading `form:cancel-tag`).
  4. Else (`eligible` and `raw_tag is None`): read `table_tag = get_button_classes().get("form:cancel-tag")`; if `table_tag is None`, `selected_tag = "button"`; elif `isinstance(table_tag, str) and table_tag in ("button", "a")`, `selected_tag = table_tag`; else raise `ValueError` if `is_strict()` or `logger.warning(...)` and fall back to `"button"`.
- Update the docstrings in `tests/test1/test_button_classes_checks.py:1` and `src/crud_views/checks.py:406` to include `E365`.

### 5. Risk Assessment
- **Risk Level:** **LOW**
- **Justification:** All architectural seams already exist in `buttons.py`, `button_data.py`, `button_classes.py`, and `form.html`. The only material risks are the cross-wave doc-test invariant in `test_label_mode_docs.py:759-765` and subtle branching order in `_form_button_data()`, both of which are straightforward to guard.

---

## 06.1-02

### 1. Summary
Plan `06.1-02` hardens anchor attribute filtering and escaping in `src/crud_views/lib/view/button_data.py` and verifies compatibility across custom templates, shared/deep-copied adapters, and real package form endpoints (`tests/test1/test_crispy_buttons.py`, `tests/test1/test_button_data.py`, `tests/test1/test_form_buttons_golden.py`). It scopes button-only attribute removal (`command`, `commandfor`, `disabled`, `form*`, `name`, `popovertarget*`, `type`, `value`, plus extra `href` and `data-cv-cancel-url`) strictly to effective anchor output (`cv_tag == "a"`) after underscore-to-hyphen normalization. The plan is thorough and well-targeted, with minor edge cases around case-insensitive attribute collisions and selector scoping on full endpoint pages.

### 2. Strengths
- **Scoped post-normalization filtering preserves button compatibility (`src/crud_views/lib/view/button_data.py:196-205, 268-280`):** Running `_form_attrs()` first (so hyphenated spellings win over underscore spellings per `test_form_hyphen_spelling_wins_in_any_order` at `tests/test1/test_button_data.py:672-685`), resolving `effective_tag`, and only then filtering `attrs` when `effective_tag == "a"` guarantees that `<button>` output (including disabled/missing-URL cancel fallbacks) keeps `formnovalidate` and other button attributes untouched (`tests/test1/test_button_data.py:640, 651`).
- **Raw opening-tag uniqueness checks catch duplicate `href` attributes (`tests/test1/test_crispy_buttons.py:490-492`):** HTML parsers like `lxml.html` silently collapse duplicate attributes on an element. Following the regex pattern in `test_reserved_attributes_resolve_to_one` (`tests/test1/test_crispy_buttons.py:490-492`) on `<a\b[^>]*>` ensures an extra `href` or `HREF` kwarg cannot emit a second `href` attribute alongside `href="{{ cv_cancel_url }}"`.
- **Preserves existing `CUSTOM` template fixture while adding a tag-aware fixture (`tests/test1/test_crispy_buttons.py:346-350, 407-432`):** Keeping `CUSTOM` unchanged proves D-16 (existing custom templates that hardcode `<button>` and read `cv_type`/`cv_name`/`cv_value`/`cv_cancel_url` keep working even when `form:cancel-tag = "a"` is active), while a second fixture proves custom templates can branch on `cv_tag`.
- **Explicit awareness of `_extract_controls` limitations (`tests/test1/test_form_buttons_golden.py:42-65`):** `_extract_controls` only matches `<(input|button)\b` with `name="..."` (lines 42-43). Plan `06.1-02` Task 2 rightly forbids modifying `_extract_controls` or the golden files and instead parses rendered cancel links separately.

### 3. Concerns
- **[MEDIUM] Case-variant `id`, `class`, `data_cv_cancel_url`, and `disabled` interaction before anchor filtering (`src/crud_views/lib/view/button_data.py:268-280`):**
  In `_form_button_data()`, lines 269-279 currently use exact lowercase `.pop()` calls (`attrs.pop("id", None)`, `attrs.pop("class", None)`, `attrs.pop("data-cv-cancel-url", None)`, `attrs.pop("title", None)`, `attrs.pop("data-cv-tooltip", None)`).
  - If a caller passes `HREF="/evil/"` or `FormNoValidate=True` or `ID="dup"` on an anchor, filtering `attrs` case-insensitively (`k.lower() not in ANCHOR_DROP_ATTRS`) when `effective_tag == "a"` will drop `HREF` and `FormNoValidate`.
  - However, `id` and `class` are ALWAYS emitted by `src/crud_views/templates/crud_views/tags/button/form.html:1-2` on `<a>` (`id="{{ cv_id }}" class="..."`). If `"id"` and `"class"` are not included in the case-insensitive anchor drop set (or popped case-insensitively), passing `ID="upper"` in `cv_attrs` would survive into `cv_flat_attrs` and produce a duplicate `id` attribute (`id="button-id-reset" ... ID="upper"`) on the `<a>` element! Similarly, in `"icon"` mode (`label_mode == "icon"`), `"title"` and `"data-cv-tooltip"` must be dropped case-insensitively on anchors so `TITLE="x"` cannot duplicate the generated `title="{{ cv_title }}"`.
- **[LOW] Selecting the cancel link on full endpoint pages in `tests/test1/test_form_buttons_golden.py:120-145`:**
  Full endpoint responses from `/author/create/`, `/author/{pk}/update/`, `/author/{pk}/delete/`, and `/campaign/{pk}/workflow/` contain multiple `<a>` elements in the navbar, breadcrumbs, and context toolbar — including a context toolbar "List" action `<a href="/author/" ... cv-key="list">` that shares the exact same `href` as the form's cancel destination! A test that selects `doc.cssselect('a[href="/author/"]')` on the page will match both the context toolbar button and the form cancel link.
- **[LOW] Deep-copied `Button` in `ListViewFilterFormHelper` custom `get_form_actions()` (`tests/test1/test_crispy_buttons.py:1461-1484, 1810-1852`):**
  `ListViewFilterFormHelper` deep-copies its layout per instance. While stock filter actions use `Submit` (`form:filter-submit`) and `Reset` (`form:filter-reset`), a custom filter helper could include a `Button` (`form:cancel`) or subclass. Storing `self._cv_tag = tag` (`None`, `"button"`, or `"a"`) as a primitive/None on `_TableClassMixin` is inherently `copy.copy`- and `copy.deepcopy`-safe (unlike an `object()` sentinel, which caused `CR-01` in Phase 6 Plan 10), provided no `object()` sentinel is used for `tag`.

### 4. Suggestions
- Define the anchor attribute removal set in `src/crud_views/lib/view/button_data.py` to include `{"id", "class", "href", "data-cv-cancel-url"}` alongside the 14 button-only attributes (`{"command", "commandfor", "disabled", "form", "formaction", "formenctype", "formmethod", "formnovalidate", "formtarget", "name", "popovertarget", "popovertargetaction", "type", "value"}`), plus `{"title", "data-cv-tooltip"}` when `label_mode == "icon"`, and filter `attrs` with `k.lower() not in ...` when `effective_tag == "a"`.
- In `tests/test1/test_form_buttons_golden.py`, scope configured cancel-link queries to `<form>` (e.g., `doc.cssselect("form a#button-id-reset")` or extracting controls inside the form element) so context-toolbar links to `/author/` or `/campaign/` are never confused with the form's cancel control.
- Avoid any `object()` sentinel for `tag=` in `_TableClassMixin.__init__` (`src/crud_views/lib/crispy/buttons.py:128`): because D-02 defines `tag=None` and omitted `tag` identically as inheritance, `tag: str | None = None` stored directly as `self._cv_tag = tag` is both simpler and immune to `deepcopy` identity drift.

### 5. Risk Assessment
- **Risk Level:** **LOW**
- **Justification:** Filtering is isolated to `effective_tag == "a"` in `_form_button_data()`, leaving default `<button>` rendering and existing golden baselines completely untouched.

---

## 06.1-03

### 1. Summary
Plan `06.1-03` publishes the reference documentation (`docs/reference/buttons.md`, `docs/reference/theme.md`, `docs/migrating-1.0.md`, `CHANGELOG.md`), adds executable documentation recipe tests (`tests/test1/test_form_button_docs.py`), adds a JS non-interception test (`tests/js/viewset.test.js`), and records full quality-gate and browser acceptance in `.planning/phases/06.1-cancel-form-button-as-a-link/06.1-VALIDATION.md`. The plan aligns well with the repository's executable-docs testing pattern, but needs careful handling of `_section()`'s heading-level parser in `tests/test1/test_form_button_docs.py:166-172` and listener-reload ordering in `tests/js/viewset.test.js:569-580`.

### 2. Strengths
- **Executable documentation fences prevent doc drift (`tests/test1/test_form_button_docs.py:36-47, 166-234`):** Extracting and executing the published Python and Django template fences from `docs/reference/buttons.md` and `docs/reference/theme.md` through real `{% crispy %}` rendering guarantees the documented `register_button_classes({"form:cancel-tag": "a"})`, `CRUD_VIEWS_BUTTON_CLASSES`, `Button(..., tag="button")`, and custom-template `cv_tag` recipes stay accurate.
- **Git invariant check against baseline commit `2a94f24b80ae451d63530369d7ef40375a1a2604` (`.git/logs/HEAD:85`):** The baseline SHA referenced in `06.1-03` is verified in `.git/logs/HEAD:85` and guarantees that `src/crud_views/static/crud_views/js/viewset.js` and `tests/test1/golden/form_buttons/` have zero unintended edits at phase completion.
- **Honest separation of jsdom handler tests from real-browser navigation acceptance (`src/crud_views/static/crud_views/js/viewset.js:37-44`, `tests/js/viewset.test.js:92-191`):** Because `viewset.js:40` delegates on `e.target.closest("[data-cv-cancel-url]")`, an `<a>` without `data-cv-cancel-url` is ignored by `viewset.js`. The plan rightly treats the vitest test as proof of non-interception (`event.defaultPrevented === false` and no `nav.href` write) while requiring real-browser verification for no-JS navigation and opening in a new tab.

### 3. Concerns
- **[MEDIUM] `_section(THEME_MD.read_text(), "## Custom form-button templates")` in `tests/test1/test_form_button_docs.py:166-172` includes `###` subsections and will fail on a second fence:**
  In `tests/test1/test_label_mode_docs.py:35-45` (imported by `test_form_button_docs.py:24`), `_section(text, heading)` slices from `heading` (`## Custom form-button templates`, level 2) up to the next heading of `len(m.group(1)) <= level` (i.e., the next `##` or `#` heading, `## Framing the form pages` at `docs/reference/theme.md:191`). It does **not** stop at `###` subheadings! Meanwhile, `_theme_recipe()` (`tests/test1/test_form_button_docs.py:166-172`) unpacks:
  ```python
  (code,) = FENCE.findall(section)
  (template,) = TEMPLATE_FENCE.findall(section)
  (pill,) = _exec_classes(code).values()
  (saved,) = re.findall(r"`[\w/]+/templates/([\w/.-]+\.html)`", section)
  ```
  If a second Python fence, Django template fence, or `` `myapp_theme/templates/...` `` path is added anywhere inside `## Custom form-button templates` (even under a `###` subheading), `_theme_recipe()` will raise `ValueError: too many values to unpack (expected 1)`.
- **[MEDIUM] `crud_views.E365` missing from the `## System checks` table in `docs/reference/buttons.md:571-586` and `docs/migrating-1.0.md:44-50`:**
  `docs/reference/buttons.md:575-580` has an explicit table of button-class system checks (`crud_views.E360`, `E361`, `E363`, `E364`, `W362`), and `docs/migrating-1.0.md:46` lists the button-class check IDs. While Plan `06.1-03` Task 1 mentions documenting configuration errors and adding the Phase 7 freeze handoff (`form:cancel-tag`, `Button(tag=...)`, `FORM_LEAF_KEYS.cv_tag`), neither the `## System checks` table row for `crud_views.E365` nor `crud_views.E365` in the Phase 7 freeze handoff is explicitly called out. Phase 7's `STAB-01` ("check IDs" in `stability.md`) will require `crud_views.E365` to be documented.
- **[LOW] Placement of new vitest cases relative to `it("loads without jQuery")` in `tests/js/viewset.test.js:569-580`:**
  Line 569 of `tests/js/viewset.test.js` warns: `// reloads the script (adds listeners), so keep it last: after it every click, including a marked alert control, would reach a second delegated listener`. If the new cancel-link click test is added at the end of `describe("viewset.js")` instead of inside `describe("data-cv-cancel-url")` (lines 92-191), it will run after duplicate event listeners have been attached.
- **[LOW] Rigid assertions in `tests/test1/test_label_mode_docs.py:754-867` on `docs/reference/buttons.md`, `docs/migrating-1.0.md`, and `CHANGELOG.md`:**
  `test_label_mode_docs.py` enforces strict structural invariants on the exact sections Plan `06.1-03` Task 1 edits:
  - `### The form leaf contract` in `docs/reference/buttons.md:473-511` must have one table row per `FORM_LEAF_KEYS` member (`test_label_mode_docs.py:760-765`) and retain the exact phrases `'present only in "icon" mode'` and `'present only for kind cancel'` (`test_label_mode_docs.py:772-773`).
  - `## Form buttons` in `docs/migrating-1.0.md:219-312` and `### Breaking` / `### Added` in `CHANGELOG.md` must preserve all 17 substring markers asserted in `test_form_buttons_breaking_entry_pairs_with_migration` (`test_label_mode_docs.py:819-866`).

### 4. Suggestions
- In `docs/reference/theme.md:136-190` and `tests/test1/test_form_button_docs.py:166-172`, if a cancel-capable custom template recipe is added under a `###` subheading (e.g., `### Supporting cancel links in custom templates`), update `_theme_recipe()` in `tests/test1/test_form_button_docs.py:167` to split `section` before `"\n### "` (just as `test_label_mode_docs.py:488` does with `_section(text, "## ContextButton").split("### The filter toggle")[0]`) so `_theme_recipe()` continues to see only the `PillSubmit` fences while a new helper extracts the `###` subsection.
- Add `crud_views.E365` to the `## System checks` table in `docs/reference/buttons.md:575-580`, to the button-classes check list in `docs/migrating-1.0.md:46`, and to the Phase 7 freeze handoff list in `06.1-03-PLAN.md` / `06.1-VALIDATION.md` alongside `form:cancel-tag`, `Button(tag=...)`, and `cv_tag`.
- Place the new unmarked-anchor click test inside `describe("data-cv-cancel-url", () => { ... })` in `tests/js/viewset.test.js` (around line 190), before `describe("rendered alert dismissal tracer")` and `it("loads without jQuery")`.

### 5. Risk Assessment
- **Risk Level:** **LOW**
- **Justification:** Plan `06.1-03` touches only documentation, tests, and validation artifacts, and its automated verification commands (`test_form_button_docs.py`, `test_label_mode_docs.py`, `06-js-verify.sh`, `mkdocs build --strict`) will immediately catch any fence-extraction or markdown-contract mismatch.

---

## Cross-Plan Comparison and Overall Assessment

| Dimension | Assessment |
|---|---|
| **Wave Ordering & Dependencies** | Linear (`06.1-01` → `06.1-02` → `06.1-03`) is appropriate because all three waves touch overlapping form-button files and test suites. The only cross-wave gap is `tests/test1/test_label_mode_docs.py:759-765` (`documented_keys == set(FORM_LEAF_KEYS)`), which should be kept green in `06.1-01` rather than waiting until `06.1-03`. |
| **Requirement & Decision Coverage** | All four Phase 6.1 success criteria in `ROADMAP.md` and all 18 decisions (`D-01` through `D-18`) in `06.1-CONTEXT.md` are accounted for across the three plans. |
| **Security & Escaping** | Preserves `_literal()`, `flatatt()`, and Django template autoescaping (`src/crud_views/lib/view/button_data.py:185-212, 280`), enforces authoritative `cv_cancel_url` over any extra `href`, and prevents disabled buttons or submit/reset controls from turning into links. |
| **Overall Risk** | **LOW** — The implementation builds cleanly on Phase 6's form-button leaf architecture without altering default `<button>` output, golden files, or `viewset.js`. |
