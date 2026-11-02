# Cross-AI Plan Review — Phase 06.1, Cycle 2 (plans at `af5ecdf`)

**Method.** Repository HEAD is `af5ecdf` (`docs(06.1): incorporate cycle-one plan review findings`). I read the three plans, CONTEXT/RESEARCH/PATTERNS/VALIDATION and REVIEWS.md, then opened every production and test file the plans cite and traced each closure claim to the mechanism in source. `git diff --exit-code 2a94f24 -- src/crud_views/static/crud_views/js/viewset.js tests/test1/golden/form_buttons/` is clean, so Plan 03's invariant baseline is currently satisfied. No tests were run and no repository file was edited. Requirements `[]`/TBD is accepted as intentional per `ROADMAP.md:314`.

**Headline.** All three prior HIGHs (H1, H2, H3) are **closed by executable plan content**, not just ledger entries: each now has a named owning task, a named file, a concrete edit and an automated verify shard that collects the affected test. A1–A10 are each either incorporated with a verifiable mechanism or explicitly deferred with a defensible reason (A9). I found **no new HIGH**. I found one new MEDIUM (a docs-parser precision in Plan 03) and a handful of LOW precisions.

---

## 06.1-01

### Summary

Plan 01 is the load-bearing plan: it adds the `tag=` keyword, the raw→effective `cv_tag` resolution in `_form_button_data`, the anchor branch in the bundled leaf, the exact `form:cancel-tag` registry key, the E365 diagnostic, and now also owns the three collateral test/doc consumers the first cycle flagged. The architecture matches the real seams: `_TableClassMixin.__init__` already separates configuration (`slot`, `icon`) from HTML kwargs (`src/crud_views/lib/crispy/buttons.py:128-137`), `_cv_button_context()` hands `cv_key`/`cv_type` separately (`:151-164`), the normalizer already owns reserved attributes and the cancel URL (`src/crud_views/lib/view/button_data.py:268-280`), and the registry merge is `{**DEFAULT, **_THEME, **settings}` with cache reset on `setting_changed` (`src/crud_views/lib/button_classes.py:116-138`). The revised tasks are executable and the H1/H2/H3 closures are real.

### Prior findings owned by this plan — verified

| ID | Status | Evidence |
|---|---|---|
| **H1** | **CONFIRMED closed by design** | `tests/test1/test_button_classes_templates.py:123` is `SENTINEL_CLASSES = {key: "x-" + key.replace(":", "-") for key in DEFAULT_BUTTON_CLASSES}`; `:241-251` and `:264-266` render every `FORM_KINDS × LABEL_MODES` cancel through `cv_button_data(..., "form")` under that table with `CRUD_VIEWS_STRICT=True` (`tests/test1/conftest.py:41`) and `_form_contract` always supplies a cancel URL (`:195`). Adding `form:cancel-tag` would yield `"x-form-cancel-tag"` → strict raise under D-01. Task 2 now owns this file, pins `form:cancel-tag` to `"button"` in `SENTINEL_CLASSES`, excludes it from `SENTINELS`, and runs `test_button_classes_templates.py` in its verify. The `_tokens(button) == [SENTINEL_CLASSES[f"form:{kind}"]]` assertion at `:267` is unaffected because class resolution is by kind, not by the structural key. |
| **H2** | **CONFIRMED closed by design** | `tests/test1/test_form_button_checks.py:894-895` iterates `("cv_href", "cv_submit_target", "cv_modal", "cv_tag", "cv_variant", "cv_disabled")` and asserts absence. Task 3 owns the file, removes only `cv_tag` and adds a positive `== "button"` assertion. The sibling `assert set(first) <= FORM_LEAF_KEYS` at `:890` is a subset check and stays green once `cv_tag` joins the set. Verify shard names the file. |
| **H3** | **CONFIRMED closed at plan level** | `tests/test1/test_label_mode_docs.py:759-765` builds `documented_keys` from the `### The form leaf contract` table rows and asserts `== set(FORM_LEAF_KEYS)`. Task 3 adds the `cv_tag` row in `docs/reference/buttons.md` (table at `:478-494`) in the same plan and runs `test_label_mode_docs.py`. See LOW concern below on intra-plan commit ordering. |
| **A1** | Incorporated, mechanism sound | crispy's `BaseInput.__init__` ends with `self.flat_attrs = flatatt(kwargs)` (`.venv/.../crispy_forms/layout.py:248`), so any `tag` that reached `**kwargs` would render as a literal `tag="a"` attribute on legacy `add_input()` inputs. Task 1's keyword-only `tag=None` consumed before `super().__init__` is exactly the right boundary. Construction-time validation (`None`/`"button"` quiet; `"a"` requires `self._cv_slot == "form:cancel"` and `input_type == "button"`; other values `ValueError`) uses attributes available before `super().__init__` (`buttons.py:129`; `input_type` is a crispy class attribute). The retained quiet-legacy test `tests/test1/test_crispy_buttons.py:1636-1660` (`Button("custom", "Custom", slot="formset:control")` via `add_input`) stays valid because `None` triggers no slot validation. |
| **A2** | Disposed with rationale in PLAN | Task 1 explicitly retains the matrix and caps itself at five files; acceptable. |
| **A4** | Incorporated | `src/crud_views/checks.py:405-407` docstring `"E360/E361/W362/E363/E364 ..."` → Task 3; `tests/test1/test_button_classes_checks.py:1` → Task 2. |
| **A10** | Incorporated | `docs/reference/buttons.md:152-153` ("not configurable here: the element, …") → Task 2 amends. |
| **A9** | Deferred, acceptable | `.planning/ROADMAP.md:332` still reads `- [ ] TBD (run $gsd-plan-phase 6.1 to break down)`. The checkbox inventory and `**Plans**: 0/3` are what the progress handler counts; the stale bullet is cosmetic. Deferral to phase-management maintenance is reasonable. |

### Strengths

- **E365 is genuinely free.** `grep -rn E365 src docs tests CHANGELOG.md` returns nothing; the existing chain in `button_class_check_messages` is E361 (non-str) → E363 (icon-host) → E364 (container-single) at `button_classes.py:251-280`, and the plan's "after E361 handles nonstrings" ordering drops into that `elif` chain cleanly. `None` passes the E361 guard (`value is not None and …`) and must be accepted by the new branch; `""` is a `str` and reaches the new branch → E365. Consistent with D-02.
- **W362 needs no grammar change.** `button_classes.py:284-285` skips any key present in `DEFAULT_BUTTON_CLASSES`; `form:cancel-tag:icon` splits to `("form", "cancel-tag", "icon")`, `"cancel-tag" ∉ FORM_KINDS` (`:228`), so `_action_key_parts` returns `None` and the key falls to the "not a known key" W362 at `:296-301`. Exactly the plan's claim.
- **Raw-table read, not `get_button_class`.** The plan correctly avoids the CSS accessor, which coerces non-str to `""` (`button_classes.py:152`) and would turn a `None` inheritance into an invalid empty string.
- **Count guard is correctly identified.** `tests/test1/test_button_classes.py:93` `assert len(EXPECTED_KEYS) == 73`; the docs say 73 at `docs/reference/buttons.md:146`; both move to 74 in Task 2 together with `test_label_mode_docs`-style docs equality.
- **Obsolete exclusion correctly located.** `tests/test1/test_button_data.py:484` `assert "cv_tag" not in FORM_LEAF_KEYS` plus the exact set at `:468-483` are owned by Task 1.
- **JS marker is leaf-emitted, not flat-attr-emitted.** `data-cv-cancel-url` is consumed into `cv_cancel_url` at `button_data.py:275` and emitted by the leaf (`form.html:2`), so the anchor branch simply omits it; `viewset.js:40-43` then never intercepts the anchor.

### Concerns

- **LOW — Intra-plan red commits.** Task 1 changes `FORM_LEAF_KEYS` and adds `cv_tag` to every normalized result, which immediately fails `test_form_button_checks.py:894` and `test_label_mode_docs.py:765`; Task 2 adds the registry key, which fails `test_button_classes_templates.py` until the same task's fixture edit lands (fine). The two H2/H3 fixes are in Task 3. Because the executor commits per task, the Task 1 and Task 2 commits are red on two existing shards. Plan-level closure is intact and the plan's `<verification>` reruns all shards, so this is a bisect-hygiene issue only.
- **LOW — Leaf branch polarity unspecified.** The plan says "branch the bundled leaf on final `cv_tag`" without stating the test direction. If the template branches on `cv_tag == "button"`, any caller that renders `crud_views/tags/button/form.html` with a pre-6.1 dict lacking `cv_tag` (custom code following the documented contract table, `docs/reference/theme.md:160-170` shows users build such templates) gets neither branch. Branching on `cv_tag == "a"` with `<button>` as the `else` keeps missing-key contexts byte-identical for free.
- **LOW — Task 1 verify shard does not include the template-byte guard.** `test_form_buttons_golden.py` is only in the plan-level `<verification>`. Since Task 1 edits a two-line leaf whose second line's leading four spaces are golden bytes (`form.html:2`; `tests/test1/golden/form_buttons/create.html:3-4`), it would be cheaper to catch a whitespace slip at Task 1 than at plan close.

### Suggestions

- Move the two one-line test edits (`test_form_button_checks.py:894`, and the `cv_tag` docs row) into Task 1, or at least append `tests/test1/test_form_button_checks.py tests/test1/test_label_mode_docs.py tests/test1/test_form_buttons_golden.py` to Task 1's `<verify>` so the tracer gate sees the collateral.
- State explicitly: the leaf tests `{% if cv_tag == "a" %}` and falls through to the existing `<button>` markup otherwise.
- In Task 2, add an assertion that `SENTINELS` does not contain `"button"` (guards the exclusion the plan promises) and that `form:cancel-tag` is the only non-CSS-valued key in `SENTINEL_CLASSES`.

### Risk Assessment

**MEDIUM.** The design is sound and every prior HIGH is closed by owned, verified edits. Residual risk is intrinsic: a one-way public keyword/context addition plus byte-sensitive edits to a two-line leaf. The LOW items above are precision, not direction.

---

## 06.1-02

### Summary

Plan 02 completes anchor-only attribute filtering and proves the opt-in path on real package pages and custom templates. The revised Task 2 fixes A5 and A8 with concrete, source-consistent mechanisms: the cancel control's id is deterministically `button-id-reset` (crispy generates `f"{input_type}-id-{slug}"`, `layout.py:240-241`; `CANCEL["id"]` at `tests/test1/test_form_buttons_golden.py:89`), the native actions are `submit-id-submit` / `submit-id-delete` (`:87-88`), and `override_settings(CRUD_VIEWS_BUTTON_CLASSES=…)` resets the merged cache through the `setting_changed` receiver (`button_classes.py:116-119`). The removal inventory comes from the research's WHATWG-derived list and the alias/precedence rules it must preserve are the ones at `button_data.py:196-205` and `:268-280`.

### Prior findings owned by this plan — verified

| ID | Status | Evidence |
|---|---|---|
| **A5** | Incorporated, selector is sound | `_buttons()` at `test_crispy_buttons.py:160` and `_page_buttons()` at `:1165` are button-only; `_extract_controls` (`test_form_buttons_golden.py:46-66`) matches only `<input|button>` start tags and asserts each name exactly once, so it cannot be reused for anchors. Task 2 now locates the owning `<form>` through the unique native-action id and requires exactly one `a#button-id-reset` and zero `button#button-id-reset` inside it. A toolbar `<a href="/author/">` elsewhere on the page cannot satisfy that. |
| **A8** | Incorporated | Task 2 forbids `register_button_classes()` in the golden module and requires before/inside/after `override_settings`; the receiver at `button_classes.py:116-119` guarantees the cache flips both ways. The only test modules that mutate the theme layer (`test_button_classes.py`, `test_button_classes_checks.py`, `test_button_leaves.py`) already snapshot/restore (`test_button_classes.py:82-89`, `test_button_leaves.py:281-285`). |

### Strengths

- **Duplicate-attribute hazard handled correctly.** The plan mandates a raw opening-tag uniqueness check, mirroring the existing pattern at `test_crispy_buttons.py:490-492` (`names = re.findall(...)`; `len(names) == len(set(names))`). lxml would silently drop a second `href`.
- **Alias precedence preserved.** `_form_attrs` (`button_data.py:196-205`) is run first; filtering happens after reserved-field resolution, so the hyphen-wins rule tested at `:466-504` is untouched for buttons.
- **Filtering is conditional on effective tag.** D-17 byte-identity for buttons holds because `cv_flat_attrs` for `cv_tag == "button"` is computed on the unchanged path.
- **Floor session coverage is real.** `noxfile.py:28-52` lists `test_crispy_buttons.py`, `test_button_data.py`, `test_form_buttons_golden.py`, `test_button_classes_templates.py`, `test_form_button_checks.py`, `test_label_mode_docs.py`, `test_crud.py`, `test_cancel_origin.py`; so "no new module needed" does keep the new cases inside `crispy_floor`.
- **Repeat-render isolation reuses proven fixtures.** `test_crispy_buttons.py:1855-1895` already copies/deep-copies adapters across `override_settings`; adding `tag` to that matrix is a natural extension and `_cv_tag` as `str|None` deep-copies trivially (the Phase 06 `_cv_kind_icon` bool lesson applies).

### Concerns

- **LOW — Asymmetric case-variant stripping.** Task 1 says to "discard leftover case variants of generated id/class, and of title/tooltip in icon mode" on anchors. Today the button path pops `id`/`class`/`title` case-sensitively (`button_data.py:271,274,278`), and HTML attribute names are case-insensitive, so `Id="x"` already produces a duplicate on buttons. Doing it anchor-only is correct for D-17 but creates a documented asymmetry; the executor should either scope the new case-insensitive rule to `href` and the button-only inventory, or record the asymmetry in the SUMMARY so Phase 7 doesn't freeze it unknowingly.
- **LOW — `disabled` in the removal inventory is dead on arrival.** D-06 routes any emitted `disabled` to the button fallback, so an anchor can never carry it; harmless defensive entry, but the test matrix should not count it as a proven anchor removal.

### Suggestions

- For the page tests, parse the owning form with `lxml` and assert both `form.cssselect("a#button-id-reset")` length 1 and `form.cssselect("button#button-id-reset")` length 0, and compare the anchor `href` to the control case's `data-cv-cancel-url` (`/author/`, `/campaign/`), which is already the expected destination at `golden.py:89-96`.
- Keep the `extra href` test's raw assertion aligned with `test_reserved_attributes_resolve_to_one`'s regex so the two tests share one tag-tokenizer.

### Risk Assessment

**LOW.** The mechanisms are grounded in existing helpers; the only risk is test over-breadth, not design.

---

## 06.1-03

### Summary

Plan 03 publishes the surface, adds the JS non-interference regression, runs the final gates, and records browser acceptance honestly as pending until observed. The A3/A6/A7 incorporations check out against source. The one gap is that the theme.md recipe test is stricter than the plan's language acknowledges: it unpacks exactly one Python fence, one Django fence and one saved-path backtick from the `## Custom form-button templates` section, and the shared `_section()` helper does not end a section at a `###` subheading. "Keep extraction scoped" is not executable enough to guarantee the executor avoids breaking that parser.

### Prior findings owned by this plan — verified

| ID | Status | Evidence |
|---|---|---|
| **A3** | Incorporated | Task 1 documents explicit `rel="noopener"` for caller-supplied `target="_blank"` and verifies both attributes survive; the renderer does not invent `rel`. Reasonable and consistent with D-07/D-15. |
| **A6** | Incorporated | Plan 03 artifacts, Task 1 and Task 2 name `crud_views.E365` as the fourth freeze input; `06.1-VALIDATION.md:143-148` already carries it. |
| **A7** | Incorporated, constraint real | `tests/js/viewset.test.js:569-580`: the comment "reloads the script (adds listeners), so keep it last" precedes `it("loads without jQuery")`, the final test in the top-level `describe`. Task 2 inserts anchor cases in the `describe("data-cv-cancel-url")` block (`:92-180`) before it and forbids reloading. |

### Strengths

- **JS claim is mechanically true.** `viewset.js:40-41` does `closest("[data-cv-cancel-url]")` and returns early; an anchor without the marker is never `preventDefault`ed. The existing test at `viewset.test.js:93-99` already proves the inverse (a marked `<a href>` *is* intercepted), which is exactly why D-15 omits the marker.
- **JS wrapper passes paths through.** `06-js-verify.sh` ends with `exec "$NODE_BIN" "$NPM_CLI" --prefix . test -- "$@"`, so naming both files is honoured; the plan's "both files must appear in the runner summary" fails_when is the right guard against the research's pitfall 6.
- **Baseline invariant is currently clean** (verified above) and stated as an invariant, not as feature evidence.
- **Browser acceptance is honest.** Automated jsdom claims are explicitly separated from no-JS/new-tab/disabled observations; `VALIDATION.md:58-64` lists them as manual.

### Concerns

- **MEDIUM — Recipe parser will break on a second fence in the same `##` section.** `tests/test1/test_form_button_docs.py:166-171`: `_theme_recipe()` does `(code,) = FENCE.findall(section)`, `(template,) = TEMPLATE_FENCE.findall(section)`, `(saved,) = re.findall(r"`[\w/]+/templates/([\w/.-]+\.html)`", section)` over `_section(THEME_MD, "## Custom form-button templates")`. `_section` (`tests/test1/test_label_mode_docs.py:35-45`) terminates only at a heading of level ≤ 2, so a `### Cancel links` subsection placed inside that `##` section adds a second Python/Django fence and a second `templates/....html` path and all three unpacks raise. The plan says "keep extraction scoped so adding a second example does not break the existing single-fence parser," but does not say *how*. The executable fix is one of: place the cancel-capable recipe under a new `##` heading (or in `buttons.md`), or change `_theme_recipe` to select the pill fence by `class PillSubmit` and the pill path by name in the same task.
- **LOW — `_exec_classes` cannot execute the new registration recipes.** `test_form_button_docs.py:36-47` compiles only `Import`/`ImportFrom`/`ClassDef` nodes, so a fence containing `register_button_classes({"form:cancel-tag": "a"})` or `CRUD_VIEWS_BUTTON_CLASSES = {...}` is silently a no-op under that helper. Task 1 should name the extraction style it expects (`ast.literal_eval` of the call argument/assignment, as `test_label_mode_docs.py:586-594` does for settings), so the executor does not `exec` doc fences with registry side-effects.
- **LOW — Custom-template docs should say the anchor branch must omit the marker.** Task 1 says old templates "opt into native anchors by consulting `cv_tag`" but not that a custom `<a>` branch must not emit `data-cv-cancel-url`. Given `viewset.test.js:93-99`, a theme author who copies the PillSubmit template (`theme.md:166-170` keeps `data-cv-cancel-url`) and merely swaps the tag will have JS override native navigation and break open-in-new-tab. One sentence in theme.md closes it.

### Suggestions

- Add to Task 1's action: "The cancel-capable recipe lives under its own `##` heading (or extend `_theme_recipe` to select by class name); `test_documented_pill_template_renders_literal_text` must remain green unchanged."
- Add to the theme.md guidance: "A custom template's `<a>` branch must not render `data-cv-cancel-url`; `viewset.js` intercepts any element carrying it."
- In Task 2's VALIDATION record, keep the three manual rows at `VALIDATION.md:60-64` as the checklist and mark each individually observed/pending.

### Risk Assessment

**LOW.** One MEDIUM planning precision (parser scoping) with a one-line fix; everything else is grounded in existing gates.

---

## Cross-plan assessment

**Dependency ordering.** Waves 1 → 2 → 3 are correct and necessary: Plan 02's filtering edits the same `_form_button_data` branch Plan 01 creates; Plan 03's recipes need the public names from Plan 01 and the anchor behaviour from Plan 02. No same-wave file overlap. The transient Plan 01 state (anchor without href dedupe) is acceptable only because no standalone Plan 01 release is authorised, as REVIEWS.md already records.

**Scope.** No scope creep. The only addition beyond #275's four roadmap criteria is E365, which D-01 ("diagnosed") requires. Nothing migrates `add_input()` controls or touches `viewset.js`.

**Security.** Unchanged escaping boundary (`_literal` → `flatatt` → autoescape); one authoritative `href`; destination trust explicitly transferred to application hooks in Plan 03 (`T-06.1-08`). The `javascript:` URL exposure is identical to today's `location.href = …` path in `viewset.js:43`, so the phase does not widen it.

**Performance.** One extra dict lookup per eligible cancel render; nil.

**Do the plans achieve the phase goal?** Yes. Criterion 1 (key, layers, W362) → Plan 01 Task 2; criterion 2 (override, fallback) → Plan 01 Task 1; criterion 3 (attributes, native navigation) → Plan 02 Task 1 + Plan 03 Task 2 browser check; criterion 4 (`cv_tag`, docs, default bytes, JS unchanged, old templates) → Plan 01 Task 3, Plan 02 Task 2, Plan 03 Task 1.

### Prior-finding closure ledger (cycle 2)

| ID | Prior severity | Cycle-2 status | Owner |
|---|---|---|---|
| H1 | HIGH | **Closed** — fixture value + SENTINELS exclusion + shard in verify | 01 T2 |
| H2 | HIGH | **Closed** — exclusion removed, positive assert, shard in verify | 01 T3 |
| H3 | HIGH | **Closed** at plan level — table row + equality test in same plan | 01 T3 |
| A1 | MEDIUM | Closed — keyword-only consumption before crispy `flatatt(kwargs)` | 01 T1 |
| A2 | LOW | Disposed with rationale | 01 T1 |
| A3 | LOW | Closed | 03 T1 |
| A4 | LOW | Closed | 01 T2/T3 |
| A5 | MEDIUM | Closed — form- and id-scoped selector | 02 T2 |
| A6 | MEDIUM | Closed | 03 T1/T2 |
| A7 | LOW | Closed — ordering constraint named | 03 T2 |
| A8 | MEDIUM | Closed — `override_settings` only, receiver-backed | 02 T2 |
| A9 | LOW | Deferred (acceptable); `ROADMAP.md:332` still stale | — |
| A10 | MEDIUM | Closed | 01 T2 |

### New findings (cycle 2)

```yaml
issues:
  - id: B1
    severity: warning
    review_severity: MEDIUM
    plan: 06.1-03
    required_property: "Adding a second documented form-button recipe must not break the existing single-fence recipe parser."
    description: "tests/test1/test_form_button_docs.py:166-171 unpacks exactly one python fence, one django fence and one templates/*.html path from _section(THEME_MD, '## Custom form-button templates'); _section (tests/test1/test_label_mode_docs.py:35-45) does not end at a '###' heading. Specify that the cancel-capable recipe lives under its own '##' heading (or buttons.md), or change _theme_recipe to select by class name, in Plan 03 Task 1."
  - id: B2
    severity: info
    review_severity: LOW
    plan: 06.1-01
    required_property: "Per-task commits should not leave sibling shards red."
    description: "Task 1 changes FORM_LEAF_KEYS/output; test_form_button_checks.py:894 and test_label_mode_docs.py:765 fail until Task 3. Fold the two one-line fixes and the docs row into Task 1, or add those shards plus test_form_buttons_golden.py to Task 1's verify."
  - id: B3
    severity: info
    review_severity: LOW
    plan: 06.1-01
    required_property: "The bundled leaf must stay a <button> for contexts lacking cv_tag."
    description: "State that form.html branches on cv_tag == 'a' with the existing <button> as else, so pre-6.1 context dicts rendered against the bundled leaf remain byte-identical."
  - id: B4
    severity: info
    review_severity: LOW
    plan: 06.1-03
    required_property: "Custom anchor templates must not carry the JS cancel marker."
    description: "viewset.js:40-43 intercepts any element with data-cv-cancel-url (proved by viewset.test.js:93-99); theme.md's PillSubmit template keeps the marker. Add one sentence that a custom <a> branch omits it."
  - id: B5
    severity: info
    review_severity: LOW
    plan: 06.1-03
    required_property: "Registration recipe tests need an extractor that handles call/assignment fences."
    description: "_exec_classes (test_form_button_docs.py:36-47) runs only imports and class definitions; name the literal_eval-style extraction used at test_label_mode_docs.py:586-594 for the register_button_classes / CRUD_VIEWS_BUTTON_CLASSES fences."
  - id: B6
    severity: info
    review_severity: LOW
    plan: 06.1-02
    required_property: "Anchor-only case-insensitive stripping of generated attributes is a documented asymmetry."
    description: "button_data.py:271,274,278 pop id/class/title case-sensitively for buttons; applying case-insensitive removal only to anchors is correct for D-17 but should be recorded in the SUMMARY (or scoped to href and the button-only inventory) so Phase 7 freezes it knowingly."
```

### Overall risk

**MEDIUM, trending LOW.** No HIGH remains open; every prior HIGH is closed by an owned edit with a collecting verify command, and the mechanisms the plans rely on (keyword-only consumption before crispy's `flatatt(kwargs)`, raw-table read, default-key W362 bypass, `setting_changed` cache reset, deterministic `button-id-reset` id, JS `closest()` marker gate) all check out in source. The residual MEDIUM is the inherent one-way nature of the public `tag=` / `cv_tag` / `form:cancel-tag` / E365 surface plus byte-sensitive edits to a two-line leaf, and one docs-parser precision (B1) that should be written into Plan 03 Task 1 before execution. The plans are ready to execute once B1 is addressed; B2–B6 can be applied by the executor as deviations without replanning.
