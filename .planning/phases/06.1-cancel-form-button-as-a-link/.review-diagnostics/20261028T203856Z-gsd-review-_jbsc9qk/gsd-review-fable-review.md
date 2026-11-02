Review complete. The plans are architecturally sound and match the real seams, but I found three existing tests outside every plan's file list that will fail once Plan 01 lands, plus one cross-wave docs/code equality test that goes red between Wave 1 and Wave 3.

# Phase 6.1 plan review (verified against source)

**Headline.** The adapter → normalizer → leaf design in all three plans matches the code exactly: `_TableClassMixin.__init__` forwards `**kwargs` to crispy at `src/crud_views/lib/crispy/buttons.py:137`, crispy turns them into `flat_attrs` at `crispy_forms/layout.py:248`, `_form_button_data` owns reserved attributes at `src/crud_views/lib/view/button_data.py:268-280`, and the leaf is a two-line template at `src/crud_views/templates/crud_views/tags/button/form.html:1-2`. The layered table and W362 membership gate (`src/crud_views/lib/button_classes.py:136,284-285`) will accept an exact new default key without grammar changes, as Plan 01 claims. What the plans miss is collateral breakage in tests they do not list.

## 06.1-01

**Summary.** Plan 01 puts tag selection, validation and fallback in the right place and its ordering (validate selected tag before URL/disabled fallback, explicit-first over table) is implementable on the current normalizer. However, it adds `cv_tag` to `FORM_LEAF_KEYS` and `form:cancel-tag` to the default table while three existing tests that pin the old contract live in files no plan edits, and its own verify shards would not surface them.

**Strengths**
- The eligibility rule "kind `cancel` and native type `button`" is grounded: kind comes from the slot at `buttons.py:139-149`, native type from `self.input_type` at `buttons.py:156`, and `FORM_TYPES` is validated first at `button_data.py:225-227`. Re-slotted `Submit(slot="form:cancel")` is correctly ineligible.
- Reading the raw table instead of `get_button_class` is necessary and the plan says so: `get_button_class` collapses non-str to `""` at `button_classes.py:152`, which would make `None` and `""` indistinguishable, contradicting D-02.
- E365 is genuinely free (only E360, E361, E363, E364 exist in `button_classes.py`), and the if/elif chain at `button_classes.py:251-280` already routes non-str values to E361 first, so "no duplicate diagnostic" is achievable by appending an `elif` on the exact key.
- `ACTION_ONLY_KEYS = LEAF_KEYS - FORM_LEAF_KEYS` at `tests/test1/test_button_data.py:442` and `required = FORM_LEAF_KEYS - {...}` at line 547 self-adjust once `cv_tag` is added, so the "always present" rule of D-10 is enforced for free.
- Deepcopy safety is handled by design: `None` means inherit, so no sentinel object is needed (the CR-01 class of bug from Phase 6).

**Concerns**
- **HIGH: `tests/test1/test_button_classes_templates.py` will fail and is not in any plan.** `SENTINEL_CLASSES` maps every default key to `"x-<key>"` at line 123. Once `form:cancel-tag` is a default key, `test_form_leaf_classes_and_bodies[cancel-*]` (lines 261-266) and `test_button_chain_renders_only_table_classes` (lines 241-255, which renders the cancel kind and real create pages) run with `form:cancel-tag = "x-form-cancel-tag"` under `CRUD_VIEWS_STRICT=True` (`tests/test1/conftest.py:41`). Under D-01 that configured invalid value raises at render. The file is also in `CRISPY_FLOOR_TESTS` (`noxfile.py:31-52`). Plan 01's verify commands never run it, so the break first surfaces in Plan 03 Task 2's full-suite gate.
- **HIGH: `tests/test1/test_form_button_checks.py:894` asserts `"cv_tag" not in first`** for a normalized form result. With `cv_tag` always present it fails. Not in any plan's file list; also in `CRISPY_FLOOR_TESTS`.
- **HIGH: cross-wave red docs test.** `tests/test1/test_label_mode_docs.py:759-765` extracts the `### The form leaf contract` table rows and asserts equality with `set(FORM_LEAF_KEYS)`. Plan 01 adds `cv_tag` to the set; the table row is scheduled for Plan 03 Task 1. Plan 01 Task 2 touches `buttons.md` only for the count and class row. The tree is red from Wave 1 until Wave 3 on a test Plan 03 itself lists as a verify command.
- **MEDIUM: D-01/D-09 are unenforceable on the legacy `add_input()` path as planned.** The plan consumes `tag` in `__init__` (correct, otherwise it leaks via `layout.py:248`) but validates only in the normalizer, which only runs on the layout path (`buttons.py:166-174`). `Submit("x", "y", tag="a")` added with `helper.add_input()` would be silently accepted. Both inputs needed for the check are available at construction: `self.input_type` and `self._cv_slot`.
- **LOW: the tracer is the whole feature.** Task 1's behavior list is the full cross-product (eligibility, seven disabled variants, alias orders, both strictness modes). A tracer should be one thin end-to-end slice; the matrix belongs in a follow-on task.
- **LOW: intermediate W362 noise.** Task 1 reads `form:cancel-tag` from settings before Task 2 registers the default. That works (`button_classes.py:136` merges any settings key) but `check_button_classes()` warns W362 on the key until Task 2 (`button_classes.py:284-302`).

**Suggestions**
- Add `tests/test1/test_button_classes_templates.py` and `tests/test1/test_form_button_checks.py` to Task 1's files and verify command. Exempt `form:cancel-tag` from `SENTINEL_CLASSES` (it is a structural value like `container-tag`, not a class) and update line 894.
- Move the one-row `cv_tag` addition to the leaf-contract table in `buttons.md` into Plan 01 Task 1, and add `tests/test1/test_label_mode_docs.py` to its verify shard. Leave the full prose rewrite in Plan 03.
- Validate the `tag` domain and the "explicit `a` requires cancel kind and native button" rule in `_TableClassMixin.__init__`, keeping the render-time check as the authoritative one. Skip the kind check when the slot is not `form:<kind>` so legacy non-form slots stay quiet per D-17.
- Register the default `form:cancel-tag: "button"` in Task 1 (one line) and leave E365 and its tests to Task 2.

**Risk: MEDIUM.** The design is right; the risk is three certain test failures outside the plan's blast radius plus a two-wave red window.

## 06.1-02

**Summary.** Plan 02 correctly scopes anchor-only attribute filtering after effective-tag selection and reuses the existing raw-opening-tag uniqueness technique. Its claims about existing fixtures are accurate. The main risks are a small button/anchor asymmetry it introduces on purpose and reliance on Plan 01 having fixed the collateral tests above.

**Strengths**
- The raw opening-tag duplicate check it prescribes already exists as a pattern at `tests/test1/test_crispy_buttons.py:490-492`; copying it for `<a` is straightforward.
- The template-precedence and scoped-context fixtures it reuses exist and are thorough (`test_crispy_buttons.py:386-431`, including the outer-context leak check at 427-431).
- Golden extractors stay valid: `_extract_controls` only matches `<input|button` start tags with a `name` (`tests/test1/test_form_buttons_golden.py:42-65`), so anchors are invisible to the default goldens, and the plan explicitly parses links separately.
- The filter region golden (`test_form_buttons_golden.py:241-268`) is a byte-exact slice that includes whitespace between controls, so any stray newline from restructuring `form.html` with `{% if %}` branches is caught automatically.
- Modal interplay is a verified non-issue: `modal.js` intercepts only `[data-cv-modal='true']` clicks and `submit` events inside `#cv-modal-content` (`modal.js:108-136`), so a cancel anchor inside a modal form behaves exactly like today's button, which also does a full `location.href` navigation (`viewset.js:43`).

**Concerns**
- **MEDIUM: depends on Plan 01 fixing the three unlisted tests.** Plan 02's second verify shard is `test_crispy_buttons.py` + `test_import_safety.py`; neither `test_button_classes_templates.py` nor `test_form_button_checks.py` is run here either.
- **LOW: intentional asymmetry.** Case-insensitive stripping of `Href`, `ID`, `Class`, `Title` only on anchors leaves the button path popping exact-case names (`button_data.py:271-279`). Defensible under D-17, but worth one sentence in the docs so a theme author is not surprised that `Button(..., ID="x")` behaves differently per tag.
- **LOW: `disabled` in the removal set is dead code.** Any emitted `disabled` forces `cv_tag="button"` (D-06), so the anchor branch never sees it. Keep it for completeness but do not spend a test on it.
- **LOW: `test_filter.py` and `test_workflow.py` are in the verify shard but the plan adds no cases there.** Fine as regressions; just do not report them as link coverage.

**Suggestions**
- Add `tests/test1/test_button_classes_templates.py tests/test1/test_form_button_checks.py tests/test1/test_label_mode_docs.py` to Task 2's second verify shard as a belt-and-braces check.
- For the real-page integration cases, override `CRUD_VIEWS_BUTTON_CLASSES={"form:cancel-tag": "a"}` and assert the anchor `href` equals the `data-cv-cancel-url` the default golden records (`/author/` and `/campaign/` per `test_form_buttons_golden.py:97-107`), which ties the link to the existing destination hooks without a new route.

**Risk: LOW to MEDIUM.** Mechanically sound; inherits Plan 01's gaps.

## 06.1-03

**Summary.** Plan 03 publishes the surface with executable recipes and records acceptance honestly (jsdom non-interference is kept distinct from browser navigation). Its biggest practical hazard is the existing single-fence recipe parser, which it acknowledges but does not resolve concretely.

**Strengths**
- The JS gate script forwards test paths after `--` (`.planning/phases/06-form-button-leaf/06-js-verify.sh`, final lines), and both `tests/js/viewset.test.js` and `tests/js/list.filter.test.js` exist, so the stated command is valid.
- The baseline `2a94f24` for the `git diff --exit-code` invariant is the validation-strategy docs commit (one `.md` file), so `viewset.js` and the goldens are genuinely unchanged at that point.
- The documented default key count is already guarded by `tests/test1/test_button_classes.py:100-104` with a single-sentence regex, and the plan updates it in Plan 01 where it belongs.
- Keeping the `viewset.js` cancel handler untouched is correct: it selects on `[data-cv-cancel-url]` only (`viewset.js:40`), and the anchor omits that attribute by D-15.

**Concerns**
- **MEDIUM: the theme recipe parser only tolerates one python fence, one template fence and one saved path per section.** `_theme_recipe()` at `tests/test1/test_form_button_docs.py:166-172` does `(code,) = FENCE.findall(section)`, `(template,) = TEMPLATE_FENCE.findall(section)` and `(saved,) = re.findall(...)` on `_section(text, "## Custom form-button templates")`. `_section` (`tests/test1/test_label_mode_docs.py:35-46`) ends only at a heading of level two or higher, so a `###` subsection inside `## Custom form-button templates` with a second recipe breaks all three unpackings. The plan says "keep extraction scoped" but does not say how.
- **MEDIUM: process traceability.** All three plans have `requirements: []`. `requirements-completed` in each SUMMARY will be empty, and Phase 7's freeze handoff and `verify-work` lose the ID join. The roadmap still says `Requirements: TBD` (`.planning/ROADMAP.md:314`).
- **LOW: stale roadmap bullet.** `.planning/ROADMAP.md:331-332` lists `06.1-01-PLAN.md` and a leftover "TBD (run $gsd-plan-phase 6.1 to break down)" under Wave 1 even though three plans exist.
- **LOW: D-14 "new tab" and `rel`.** The anchor passes `target` and `rel` through. Browsers imply `noopener` for `_blank` today, but the docs should still say to set `rel` explicitly when targeting another tab.

**Suggestions**
- Put the cancel-capable recipe in its own `## Cancel links in custom form-button templates` section in `theme.md`, with its own python fence, template fence and "Save it as" path, and give it its own extractor in `test_form_button_docs.py` rather than widening `_theme_recipe`.
- Assign four requirement IDs (one per roadmap success criterion, e.g. `LINK-01..04`) in `REQUIREMENTS.md` and the three plan frontmatters before executing Wave 1. This is a five-minute edit that makes every downstream GSD step traceable.
- Fix the roadmap Wave 1 placeholder line in the same commit.

**Risk: LOW.** Docs and acceptance work; the parser constraint is the only thing that can bite, and it is known.

## Cross-plan assessment

**Dependency ordering** is correct (01 → 02 → 03, no same-wave overlap) and the product seams are disjoint per wave. The one ordering defect is the docs/code equality test going red across Waves 1 and 2.

**Scope** is tight. No new modules, dependencies or JS changes; the anchor-only case-insensitive filtering in Plan 02 is the only mild over-reach and it is bounded.

**Security** holds: `href` comes from `_attr_text` plain-str normalization (`button_data.py:208-212,275`) and is autoescaped in the leaf; extra `href` is dropped; invalid tags never reach the template. The "trusted destination, not URL-scheme validation" boundary is documented rather than silently assumed.

**Performance** is negligible: one cached dict lookup per cancel render (`button_classes.py:132-138`).

**Overall risk: MEDIUM.** The plans achieve the four phase goals and nothing in the locked decisions is unimplementable. The rating is driven entirely by three verified collateral test failures (`test_button_classes_templates.py:123,241,264`, `test_form_button_checks.py:894`, `test_label_mode_docs.py:765`) that no plan lists and no early verify shard runs. Adding those three files to Plan 01's scope and moving the one-row contract-table edit into Wave 1 drops the risk to LOW.
