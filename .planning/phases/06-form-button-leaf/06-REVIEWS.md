---
phase: "06"
reviewers: ["fable-review", "grok-review", "gemini-review"]
reviewed_at: "2026-10-27T18:23:05.944598+00:00"
plans_reviewed: ["06-01-PLAN.md", "06-02-PLAN.md", "06-03-PLAN.md", "06-04-PLAN.md", "06-05-PLAN.md", "06-06-PLAN.md", "06-07-PLAN.md", "06-08-PLAN.md", "06-09-PLAN.md"]
models:
  fable-review: "claude-fable-5-1 (reasoning=high)"
  grok-review: "openrouter/x-ai/grok-4.7 (reasoning=high)"
  gemini-review: "openrouter/google/gemini-4-argon (reasoning=high)"
model_sources:
  fable-review: "pinned"
  grok-review: "pinned"
  gemini-review: "pinned"
---

> Grok and Gemini share the OpenCode adapter; their agreement is cross-model, not cross-tool.

# Cross-AI Plan Review — Phase 06

<!-- gsd:plan-revision-conflicts:begin -->
## Plan-Revision Conflicts

- [x] REVISION_CONFLICT external-prerequisite/06-01 — required_property: Phase 1 and 2 prerequisites exist on authoritative main before spec/execution | conflicts with: ROADMAP.md Phase 6 main prerequisite; main remains 38b0100 | alternatives: retain main gate and wait for maintainer merge; explicitly authorize executing-branch prerequisite and update governing requirement | resolved: User selected working-branch verification (D-18); governing roadmap/context and plans updated; retain dependency evidence, spec-first and baseline-first gates.

<!-- gsd:plan-revision-conflicts:end -->

## Reviewer Execution Record

Review cycle 1 after manual revision, committed plan snapshot `58e740d9b8bf7ef1077d728ae782b9d9995ced44`. Configuration selected fable-review, grok-review and gemini-review with their pinned models and lane-owned high effort; no explicit reviewer flags were used. Lanes ran concurrently under review.parallel_lanes. No plan or product file was changed.

| Reviewer | Result | Plan coverage | Evidence quality |
|---|---|---|---|
| fable-review | Substantive external review | 9/9 | Source citations present |
| grok-review | Substantive external review | 9/9 | Source citations present |
| gemini-review | Substantive external review | 9/9 | Source citations present |

Fable completed its canonical 1,200,000 ms lane. Grok attempt 1 returned only an introductory promise, zero plan sections and no citations; stderr recorded an auto-rejected external_directory (/tmp/*) request. Its single retry used the same canonical adapter/model/effort and 660,000 ms deadline with an appended read-only instruction to inspect repository paths only; no permissions were changed. That retry produced all nine source-cited sections. Gemini attempt 1 hit its canonical 660,000 ms ETIMEDOUT with no assistant review text (stop reason tool-calls, 126 output tokens). Its single retry kept prompt/model/effort/permissions unchanged and used a process-local CommonJS wrapper to set only plan.timeoutMs to 1,200,000 ms; no installed runtime or project configuration file was edited. It completed all nine sections within that bound. Failed/incomplete attempts remain in the run diagnostics and never count as approval. No reviewer output was trimmed. Current report sections contain the successful final attempt per identity; failed attempts are separately preserved.

The writer-owned conflict block is preserved byte-for-byte (SHA256 `03f805c366d031be9c6450c8231af0fef5f5db27e2e6536b5d018c9b3505b0be`). It contains no open checklist entry.

## Claude Review (fable-review)

# Cross-AI Plan Review: Phase 06 (Form-button leaf) — plans 06-01 … 06-09

Reviewed against the working tree at HEAD `58e740d` on branch `introduce-gsd`, with the installed django-crispy-forms 2.6 / crispy-bootstrap5 2026.3 / Django 5.2.14 / Node v20.20.2. Every claim below was checked against source; where I could not verify something I say so.

**Verified ground truth the plans rest on (all confirmed):**

- Adapters are thin: `src/crud_views/lib/crispy/buttons.py:16-18` only sets `field_classes` from the class table and delegates to crispy. The only `slot=` caller in src is `src/crud_views/lib/views/list.py:71`.
- `BaseInput.render` compiles the value as a Django template and mutates the instance (`crispy_forms/layout.py:255`); `baseinput.html` emits `name` via the `wordcount > 1 → slugify` rule and the pre-generated `input.id`; the id is `f"{input_type}-id-{slugify(name)}"` (`layout.py:240-241`). Template precedence `template or self.template` and `%s` pack substitution are at `layout.py:247` and `layout.py:18-25`.
- `FormHelper(form)` unconditionally replaces the layout (`crispy_forms/helper.py:212-214`); `FormHelper.__len__` is `len(layout.fields)` (`helper.py:99-103`), there is no `__bool__`, and `LayoutObject.__len__` exists (`layout.py:38`) so an empty `Layout()` is falsy too. `get_attributes` is called in `get_response_dict` (`crispy_forms_tags.py:147`) **before** the `if helper and helper.layout` guard (`:116`), and it copies every non-underscore instance attribute into the response dict (`helper.py:340-346`), which then becomes a Context layer (`crispy_forms_tags.py:110-112`). This is exactly the `view=None` shadowing hazard.
- `inputs.html` includes `baseinput.html` directly for `helper.inputs`; `display_form.html` falls back to `uni_form.html` whenever `form.form_html` is empty.
- `LOCATIONS = {"context","list","card"}` (`button_data.py:12`), `LABEL_MODE_DEFAULTS` has three keys (`label_mode.py:23`), `default_label_mode` validates against `LOCATIONS` and indexes the defaults map (`label_mode.py:93-99`), so both must change together. `FORM_KINDS`/`VARIANT_LOCATIONS` are independent (`button_classes.py:209-226`). The class table has 71 keys today (`test_button_classes.py:90`, `docs/reference/buttons.md:145`); `form:hidden-label` and `form:icon-host` are absent (`button_classes.py:84-94`).
- Test consumers that break when `"form"` joins `LOCATIONS`: `test_action_label_mode_config.py:278,323`, `test_button_classes_templates.py:16,214`, `test_label_mode.py:17,67,94`, `test_label_mode_docs.py:126` + `docs/reference/settings.md:78,90`, `test_button_data.py:9`.
- `CrudViewsSettings` captures Django settings at import (`settings.py:13-14,67-68`), the singleton is created at `settings.py:320`, and there is no `setting_changed` receiver in that module. The floor is read lazily (`label_mode.py:54-58`).
- `DEFAULT_ICONS` lacks `save`, `cancel`, `filter-reset` but has `filter-close` (`icons.py:14-50`). `resolve_icon`/`render_icon`/`resolve_icon_name_class`/`_get_renderers` are at `icons.py:187-258,164-176`.
- `modal.js:80-83` already posts `new FormData(form, submitter || undefined)`; `tests/js/modal.test.js:195-204` already dispatches a native `SubmitEvent` with `submitter` and reads the posted value. `viewset.js:40-43` uses `closest("[data-cv-cancel-url]")`. `list.filter.js:44-57` navigates on `#filter-button-reset` click without `preventDefault`.
- JS environment: `package.json` engines `node >=20`, Node v20.20.2 installed, lock pins jsdom 30.1.2 and vitest 5.0.3, vitest 5.0.3 engines `^22.12.0 || ^24.0.0 || >=26.0.0` (`package-lock.json:1529-1531`), installed node_modules are jsdom 29.1.1 / vitest 4.1.10. The mismatch and Node-20 exclusion are real.
- No existing golden contains a form button: `golden/form_frame/*` render a plain `NameForm` via `{{ form }}` (`test_form_frame.py:34-41`), and `golden/action_menus/*` contain no `filter-button`/`type="submit"`. STATE.md's "today's goldens contain no form buttons" is correct.

---

## 06-01

**Summary.** The plan correctly sequences prerequisite verification (D-18), spec authoring, and baseline-only golden commits, and its spec content list matches the real hazards I verified above (value templating, layout replacement, get_attributes publishing, dual truthiness guard). The one structural problem is that it binds the whole phase's start to acquiring a Node ≥22 runtime, which only waves 7–8 need.

**Strengths**
- Prerequisite shard (`test_label_mode.py`, `test_action_label_mode_config.py`, `test_button_classes.py`) exists and exercises exactly the Phase 1/2 contracts (`label_mode.py:84-117`, `button_classes.py:213-236`).
- Spec sections map one-to-one onto verified mechanisms: "Helper lifecycle" names both guards at `crispy_forms_tags.py:116` and the `get_attributes` pre-dispatch hook at `:147`; "Literal text" names the `BaseInput.render` bypass (`layout.py:255`); "Ownership" names the non-underscore attribute copy (`helper.py:340-346`).
- Baseline capture via raw control extraction (not DOM re-serialization) avoids lxml normalisation noise; `git diff BASELINE^ BASELINE -- src` empty + ancestry check is a sound FORM-01 proof.
- Task 2's separate `{"confirm": True, "delete": "Delete"}` POST correctly leaves `test_crud.py:63` (`{"confirm": True}` only) untouched.

**Concerns**
- **MEDIUM — Phase-wide halt on a wave-7 dependency.** Task 1 requires `06-js-verify.sh` to run "before wave 1 completes" and the frontmatter says an "unavailable compatible runtime halt[s] execution". Node 20 is excluded by the lock (`package-lock.json:1529-1531`), so acquisition is a real download of an official Node 22/24 archive. If that fails (offline sandbox, no checksum source), nothing in 06-02…06-06 (pure Python) can proceed, even though JS is first needed in 06-07.
- **MEDIUM — Task 1 scope.** One task authors a nine-section spec settling roughly forty contracts *and* builds a runtime-verification wrapper with semver/engine/lock-hash checks. The 22 000-token estimate at "confidence: low" is optimistic; a half-written spec is the likely failure mode, and the automated verify only checks that sections are non-empty.
- **LOW — Wrapper details.** "npm's already-bundled semver resolver" lives under `<node>/lib/node_modules/npm/node_modules/semver`; the script should `require.resolve` it from that path rather than guess. Also the sort/order/dir hidden inputs are only emitted when non-empty (`list.py:84-87`); the plan already says to use non-empty query values, good.

**Suggestions**
- Make JS runtime acquisition a *recorded blocker that does not halt 06-01*; keep it blocking in 06-07 and the 06-09 gate. Move wrapper creation to a separate task (or to 06-07 Task 1) so the spec task stays a spec task.
- Add to the spec's automated verify a grep that the "Ownership" section names the discriminator keys for a crispy response overlay (see 06-03 below).

**Risk: MEDIUM** — logically sound, but the Node gate placement can stall the phase at wave 1 for a non-Python reason.

---

## 06-02

**Summary.** This is the right first tracer: a real `{% crispy %}` render through the layout path, bypassing `BaseInput.render`, with all `LOCATIONS`/defaults consumers updated atomically. The plan's file list and the "71 → 73" count are accurate. Remaining gaps are small but concrete.

**Strengths**
- Atomic update of every consumer I found (`test_action_label_mode_config.py:278,323`, `test_button_classes_templates.py:214`, `test_label_mode_docs.py:126` ↔ `settings.md:78,90`, `test_button_data.py:9`, `test_label_mode.py:67`) is correctly owned here; `default_label_mode` would `KeyError` on `LABEL_MODE_DEFAULTS["form"]` if the two edits were split (`label_mode.py:99,108`).
- Name/ID semantics match the pack exactly (`baseinput.html` `wordcount`/`slugify`; `layout.py:240-241` ID).
- Keeping `css_class` append semantics works because `_TableClassMixin` sets `field_classes` before `super().__init__` appends (`buttons.py:17` → `layout.py:244-245`).
- Early form branch before the action URL/`cv_oid` logic (`button_data.py:138-141`) is necessary: standalone forms have no `cv_url`/`cv_oid`.

**Concerns**
- **MEDIUM — `kind` parameter semantics for forms are undefined.** `cv_button_data(ctx, location, kind="action")` validates `kind in KINDS` (`button_data.py:14,60-61`). FORM-02 calls `cv_button_data(ctx, "form")`; the plan never says whether `kind` is ignored, must be `"action"`, or is rejected for forms. Left open, `cv_button_data(ctx, "form", "menu-item")` would silently take the form branch.
- **MEDIUM — `test_label_mode.py:94` changes meaning silently.** The case `({"form": "label", "list": "both"}, ...)` is currently documented as "unknown key ignored". After `form` becomes valid it still passes (because `label` equals the new package floor) but for the wrong reason, and the "unknown key ignored" coverage is lost. The plan says "update location/default assertions" generically; this line should be explicitly re-homed to a truly unknown key.
- **LOW — Task 1 verify shard omits `test_label_mode.py`** although Task 1 modifies it and `test_label_mode.py:67` (`set(LABEL_MODE_DEFAULTS) == LOCATIONS`) and `:17` (`PACKAGE`) fail the moment `form` is added. It only runs in Task 2's shard.
- **LOW — `flatatt` is conditional-escape.** Django's `flatatt` uses `format_html_join`, so a `SafeString` kwarg value passes through unescaped. The plan's "normalize to plain str first" handles it; the spec should state that this is *why* (so a future refactor doesn't re-introduce `conditional_escape` on raw kwargs).

**Suggestions**
- State in the spec: form branch ignores `kind` (or asserts `kind == "action"`), and `FORM_LEAF_KEYS` excludes `cv_tag`/`cv_href`/`cv_submit_target`/`cv_modal*`/`cv_active`/`cv_variant`/`cv_flex`.
- Add `tests/test1/test_label_mode.py` to Task 1's `<automated>` command.

**Risk: MEDIUM** — well-grounded; the open `kind` semantics is a public-contract ambiguity that Phase 7 would freeze.

---

## 06-03

**Summary.** The whole-map resolver extension is a straightforward copy of `cv_first_inline_keys` (`base.py:263-272`) and the singleton-vs-lazy-floor distinction is accurate. The ownership work is correct in mechanism but the bulk of Task 2 defends a case with no production producer.

**Strengths**
- Singleton lifecycle claim is exactly right: `from_settings` at class-body time (`settings.py:13-14,67-68`), singleton at `:320`, no `setting_changed` receiver; monkeypatching `crud_views_settings` is already the established pattern (`test_action_label_mode_config.py:79,85`).
- `cv_get_action_label_mode` currently raises for any location other than context/list (`base.py:329`); adding a `form` branch with membership-then-floor mirrors the list branch (`:323-328`).
- Reading `cv_view` from the adapter's `form` argument (not `context["form"]`) is right: crispy only sets `final_context["form"]` after layout rendering (`crispy_forms_tags.py:133`), and `node_context` may carry a helper's published `form` attribute (`helper.py:340-346`).
- "Do not re-read `form.helper`" is essential: `CrispyFormMixin.helper` is a property that builds a fresh `FormHelper` and fresh adapter instances on every access (`form.py:41-48`); crispy reads it once (`crispy_forms_tags.py:96`).

**Concerns**
- **MEDIUM — Overlay discriminator is still unspecified.** The plan says "classify response boundaries using installed crispy metadata" without naming it. The response dict always contains `template_pack`, `is_formset`, `inputs`, `form_method`, `form_tag` (`crispy_forms_tags.py:153-175`); `FormActions` layers contain only `formactions`/`fields_output` (`bootstrap.py:309`) and never `view`. The spec should fix the discriminator (e.g. a layer that has both `template_pack` and `is_formset` is a helper overlay) so two implementers would write the same code.
- **LOW — M-OUTER-HELPER-PAGE has no producer in the package.** The only helper with a `view` attribute is `ListViewFilterFormHelper` (`list.py:68`), and filter forms never contain `Formsets`; the helpers that *do* enclose formsets are bare `FormHelper()` instances (`form.py:43`, `inline_formset.py:57`). The transport through `Formsets.render` → `cv_x_formset` → recursive includes is real production code for a third-party-only scenario. I am not re-litigating the manual decision, but the implementation should be minimal (one private key, no new public context) and the plan should say so to avoid gold-plating.
- **LOW — Import safety.** `tests/test1/test_import_safety.py:299-305` asserts `crud_views.lib.view.button_data` is not imported by `settings.py` or `django.setup()`. Adding the form map to `settings.py` must keep the deferred-import pattern of `_action_settings_messages` (`settings.py:103-112`). Not mentioned in any plan.

**Suggestions**
- Name the overlay discriminator keys in the spec and assert them in a test against the installed crispy version.
- Add `tests/test1/test_import_safety.py` to Task 1's verify shard.

**Risk: MEDIUM** — correct mechanisms; the ownership design is the highest-complexity item in the phase and still has one unnamed decision.

---

## 06-04

**Summary.** Registry additions, leaf mode bodies and workflow/per-form icon precedence are correctly scoped and match the existing action leaf conventions (`tags/button/action.html:7-8`). Small, well-bounded plan.

**Strengths**
- Correctly consumes (not re-adds) the utility keys landed in 06-02; the exhaustive key test (`test_button_classes.py:90-101`) would catch double-adding.
- Sentinel-based `icon=` keyword with explicit `None` as "intentionally missing" is the right shape, and the delete-slot-vs-name regression reflects a real existing test (`test_crispy_buttons.py:67-69` chooses `form:cancel` for a `delete` payload).
- `WorkflowForm.submit_label` lives at `src/crud_views_workflow/lib/forms.py:20`; a sibling `submit_icon = "workflow"` is trivial and `workflow` exists in both registries (`icons.py:24,63`).

**Concerns**
- **MEDIUM — Where `icon` is popped matters.** `BaseInput.__init__` serialises *all* remaining kwargs via `flatatt` (`layout.py:248`), and the legacy `helper.inputs` path emits `input.flat_attrs` verbatim (`baseinput.html`). If the adapter does not pop `icon` before `super().__init__`, legacy inputs would render `icon="save"` as an HTML attribute. The plan says "never serialized" but not where; the spec should pin "popped in `_TableClassMixin.__init__` before delegation".
- **LOW — `filter-reset` vs `filter-close`.** `filter-close` already exists (`icons.py:27`, documented at `icons.md:57,72` as the open-panel toggle state). D-16 locks `filter-reset`, so no change, but Phase 7 will freeze two near-synonyms; 06-08 should document the distinction in `icons.md`.

**Suggestions**
- Add a legacy-path assertion: a package `Submit(..., icon="save")` placed via `helper.add_input` renders no `icon` attribute.

**Risk: LOW**

---

## 06-05

**Summary.** The helper-lifecycle analysis is accurate against installed crispy: both truthiness guards, `get_attributes` as the pre-dispatch hook, `FormHelper(form)` layout replacement, and shared class-level layouts (`tests/test1/app/views.py:288-289`). The accepted edge cases produce two user-visible oddities the docs should name plainly.

**Strengths**
- `get_attributes` before `if helper and helper.layout` is verified (`crispy_forms_tags.py:147` vs `:116`); `__len__` → `len(layout.fields)` (`helper.py:99-103`) and `LayoutObject.__len__` (`layout.py:38`) confirm H-HELPER-TRUTHINESS needs both fixes.
- Underscore-prefixed lifecycle state is the right call because `get_attributes` publishes every public attribute into template context (`helper.py:340-346`).
- Constructor wiring preserved: `mixins.py:319` passes only `request=`/`view=`; the plan never adds a `form` requirement.
- Hidden sort/order/dir stay on `helper.inputs` (`list.py:77-87`) per D-01.

**Concerns**
- **MEDIUM — Empty `Layout()` + `None` hook renders *all* fields anyway.** `render_layout` returns `""` → `form.form_html` is falsy → `display_form.html` includes `uni_form.html`, which loops every form field. The plan acknowledges this in Task 2 but the must-have reads "selected layout stays empty and no action group appears", which a reader will take to mean "renders nothing". The documented outcome should say "renders every filter field (pack fallback) with no actions".
- **LOW — Accepted hidden-wrapper margin is a visible change.** `whole_uni_form.html` renders `inputs.html` after `display_form.html`, so the `<div class="mb-3">` wrapper now holds only hidden inputs and sits *after* Apply/Reset, adding bottom margin. L-HIDDEN-WRAPPER pins it; 06-08 should state the visual effect, not just the ordering.
- **LOW — Published `view` attribute.** `ListViewFilterFormHelper.view` is public (`list.py:68`) and already lands in the crispy context layer today; the new private pushed key in `render_layout` is correct, but note the public one cannot be renamed without a Breaking entry.

**Suggestions**
- Replace the empty-layout must-have wording with the observable outcome. Consider an explicit test asserting the `uni_form` fallback renders the fields so nobody later "fixes" it.

**Risk: MEDIUM** — mechanism verified; the risk is in subtle lifecycle state (replacement identity, exactly-once) rather than in the analysis.

---

## 06-06

**Summary.** The form-only diagnostic policy is a reasonable resolution of the real mismatch I confirmed: `cv_label_mode_checks` folds invalid mode values into E211 (`action_menu.py:52-62`), so reusing it would mislabel. Static W292 reach is bounded sensibly; the provider-first order for delete forms is right.

**Strengths**
- Provider selection reflects source: `CrispyDeleteForm.helper` overrides the mixin property and uses `get_delete_button()` + cancel (`form.py:132-142`), never `submit_icon`; kwargs hooks can change the slot (`test_crispy_buttons.py:67-69`), so hook overrides correctly make the provider dynamic.
- Catching `ValueError` only around mode resolution mirrors `cv_icon_mode_checks` (`buttons.py:426-429`) so E108/E210/E211 survive strict checks.
- Availability via `resolve_icon` + library dict + `_get_renderers` metadata without invoking a renderer is consistent with `render_icon`'s own gates (`icons.py:227-237`).
- Polymorphic traversal of `polymorphic_forms` without instantiation matches `src/crud_views_polymorphic/lib/utils.py:35,66-72`.

**Concerns**
- **MEDIUM — E106 scope change.** `_action_settings_messages` E106 today validates shape and mode values only (`settings.py:128-140`); the plan adds unknown-finite-kind rejection for the form map under the same ID. That is fine, but the message must differ from the context/list one, and `FORM_KINDS` must be imported lazily inside the method to keep `test_import_safety.py:299-305` green and the "settings.py must not import the view package at module level" comment (`settings.py:103`) true.
- **LOW — Static checker wiring condition.** `cv_icon_mode_checks` runs only when `cls.cv_viewset is not None` (`base.py:196-197`). The new form checker should use the same condition; views without a ViewSet have no map chain to resolve.
- **LOW — W292 message shape.** The existing W292 text is action-specific (`buttons.py:436-439`); the form variant needs its own message naming form class and kind, which the plan implies but does not spell out.

**Suggestions**
- Add `tests/test1/test_import_safety.py` to Task 1's verify shard.
- State the exact E106 form message in the spec so 06-08 can document it verbatim.

**Risk: MEDIUM** — many branches; the static/dynamic agreement is the thing most likely to drift.

---

## 06-07

**Summary.** The JS tasks are mostly re-running already-proven native behaviour under the locked packages; the real work is environment reconciliation (owned by 06-01) and the new `crispy_floor` nox session. Both are feasible; the floor session has one dependency subtlety.

**Strengths**
- Native `SubmitEvent.submitter` + `FormData(form, submitter)` is already exercised at `tests/js/modal.test.js:195-204` against `modal.js:80-83`; extending it is low risk.
- `viewset.js:40` (`closest`) and `list.filter.js:57` (id-based listener) already tolerate nested spans; "leave JS byte-identical unless a test fails" is the right default.
- Session shape follows `noxfile.py:6-19` (uv backend, Django parametrize, skip logic).

**Concerns**
- **MEDIUM — Floor resolution must be a single transaction.** Installed metadata shows crispy-bootstrap5 2026.3 requires `django-crispy-forms>=2.3` and crispy 2.6 requires `django>=5.2`. If `.[extras]` is installed in one call and the pins in another (as the existing sessions do for Django, `noxfile.py:13-14`), uv may first resolve crispy 2.6 and then downgrade, or refuse. The plan already says "same resolver transaction"; make the command literal in the plan so the executor does not copy the two-call pattern.
- **MEDIUM — Node acquisition is a hard prerequisite here** (lock engines exclude Node 20). Correctly blocking in this plan; see 06-01 for the placement concern.
- **LOW — Reset fixture change.** `tests/js/list.filter.test.js:15` uses `type="button"`; switching to `type="reset"` inside a real form triggers jsdom's native `form.reset()` before navigation. That is the desired behaviour, but the test must assert field reset *and* `location.href` without ordering assumptions, since the handler does not `preventDefault` (`list.filter.js:44-54`).

**Suggestions**
- Write the nox install line verbatim: `session.install(".[polymorphic,workflow,ordered,test]", "django-crispy-forms==2.0", "crispy-bootstrap5==2023.10", f"django~={django}.0")`.
- Record `pip freeze`/`uv pip list` output for crispy and Django in the session summary (the plan asks for versions; say which command).

**Risk: MEDIUM** — environment-bound; no logic risk.

---

## 06-08

**Summary.** Documentation, migration and example changes are well matched to the existing doc-contract tests, which are strict. The plan is aware of them; the main risk is breaking those tests by editing table rows and changelog structure.

**Strengths**
- `docs/migrating-1.0.md` has no "Form buttons" section today (verified headings), so the addition is correctly scoped; CHANGELOG already has an `### Breaking` under Unreleased (`CHANGELOG.md:3-7`).
- Executable recipe tests via real `{% crispy %}` with an isolated loader follow the established `_theme_templates` pattern (`test_form_frame.py:58-68`).
- `tooltip.js` header is a comment-only edit with no stored content hash (`assets.py:17-22` applies integrity to external URLs only), so no asset test breaks.
- Example `test_demo_pages_render_german` asserts `'value="Sichern"'` (`examples/bootstrap5/test_i18n.py:135`); a `<button value="Sichern">` keeps that true.

**Concerns**
- **MEDIUM — `test_label_mode_docs.py` row contracts are exact.** `_row` requires each knob row to appear exactly once (`:48-52`), the defaults row must `literal_eval` to `LABEL_MODE_DEFAULTS` (`:126`), and the merge/replace table asserts specific cells per knob (`:145-159`). Adding a form row and a `"form"` mention in the keys column must keep `'"card"'` present in the defaults-row keys cell (`:146`). The plan says "extend assertions"; it should also say "run `test_label_mode_docs.py` after every docs edit", since Task 2 and Task 3 edit other pages without that shard in their verify.
- **LOW — Changelog structure test.** `_card_release_contract` (`test_label_mode_docs.py:336-388`) splits releases on `^## ` and asserts the file starts with the exact title; new entries must go under the existing Unreleased subsections, not a new `##`.
- **LOW — `icons.md` should distinguish `filter-reset` from `filter-close`** (see 06-04).

**Suggestions**
- Add `tests/test1/test_label_mode_docs.py` to the verify of Tasks 2 and 3, not only Task 1.

**Risk: LOW-MEDIUM** — mostly prose; the doc-contract tests are the guardrail and the plan respects them.

---

## 06-09

**Summary.** Acceptance plan is thorough and honest about inherited evidence; the example gate commands are grounded in real test names (`examples/bootstrap5/project/tests.py:97`, `test_i18n.py:121`, `test_doc_links.py`). Nothing structurally wrong; two execution notes.

**Strengths**
- Separates the three delete-payload facts (unchanged confirm-only test `test_crud.py:63`, rendered name/value, new confirm+delete POST) rather than conflating them.
- Explicitly carries the two unclassified classifier rows instead of silently resolving them.
- `ruff format --check` pre-existing red on planning files (STATE.md:114) is handled as a classified, not green, gate.

**Concerns**
- **LOW — Browser acceptance tooling.** The plan says "use browser automation where available". A Playwright MCP is present in this environment; the executor should prefer it over a pending human check so FORM-13's three-mode observation is recorded rather than deferred.
- **LOW — Golden regeneration scope.** The plan says "confirm no unrelated golden was regenerated". Since no existing golden contains form buttons (verified), the only expected golden diffs are the five phase-owned files; the acceptance note should state that fact explicitly so a reviewer does not go looking for `form_frame` diffs.

**Suggestions**
- Name the Playwright MCP as the automation path in Task 2 and list the exact three settings values to drive.

**Risk: LOW**

---

## Cross-plan assessment

**Dependency ordering.** The chain 01→02→03→04→05→06→{07,08}→09 is strictly serial where files overlap (`buttons.py`, `button_data.py`, `form.html`, `test_crispy_buttons.py` are touched by 02/03/04/05/06) and 07/08 are disjoint (verified: 07 owns `tests/js/*`, three JS handlers, `noxfile.py`; 08 owns docs, `test_label_mode_docs.py`, `test_form_button_docs.py`, CHANGELOG, migration, example settings, `tooltip.js` comment). No ordering defects. The only sequencing problem is the Node gate in 06-01 (above).

**Scope / over-engineering.** Two items exceed what the locked decisions strictly require: the formset page-owner transport in 06-03 (no in-package producer) and the full runtime wrapper in 06-01. Both are explicitly review-mandated, so I flag them as cost, not error. Everything else is tightly scoped to D-01…D-18.

**Security.** The injection boundary is correctly placed: bypass `BaseInput.render` (`layout.py:255`), normalise `SafeString`/lazy to plain `str`, autoescape once in the leaf, serialise extras after normalisation because `flatatt` is conditional-escape. The threat tables reference real tests. No gap found.

**Performance.** Owner recovery walks `Context.dicts` per button render; forms have at most a handful of buttons, so negligible. The deep-copy of a declared filter layout per helper instance is one copy per request. Fine.

**Does the plan set achieve the phase goal?** Yes, provided three things are pinned before 06-02 starts: (1) `kind` semantics for `cv_button_data(ctx, "form")`, (2) the crispy overlay discriminator keys, (3) the import-safety constraint when `settings.py` grows the form map. The remaining concerns are wording, verify-shard completeness, and gate placement.

**Overall risk: MEDIUM.** The analysis under the plans is accurate against the installed crispy internals and the package source, the baseline-first/spec-first ordering is right, and the breaking surface is contained. Residual risk sits in the wave-1 Node gate (can stall the phase for a non-Python reason) and in the two still-unnamed spec decisions above.

---

## OpenCode Review (grok-review)

I'll verify each plan against the current source, starting with the contracts the plans depend on.
Prior review findings look incorporated on paper. I'll check the mechanisms they depend on in the current source.
## 06-01

The prerequisite plan matches the current tree: Phase 1/2 contracts are present, and the spec is required before any product edit. The Node gate is heavy but correctly tied to the lock, not to the observed Node 20 runtime.

**Strengths**
- `LOCATIONS` is still `{"context", "list", "card"}` (`src/crud_views/lib/view/button_data.py:12`); `FORM_KINDS` and `VARIANT_LOCATIONS` are already finite (`src/crud_views/lib/button_classes.py:209-210`). D-18 can be checked on this branch without a merge.
- `EXPECTED_KEYS` is 71 (`tests/test1/test_button_classes.py:89-91`) and `buttons.md:145` matches. Baselines before that count changes are the right order.
- `package-lock.json` pins jsdom 30.1.2 (`node: ^22.22.2 || ^24.15.0 || >=26.0.0`) and vitest 5.0.3 (`node: ^22.12.0 || ^24.0.0 || >=26.0.0`). Rejecting a Node 20 fallback is correct. `package.json:16` only says `>=20`.

**Concerns**
- LOW: The automated spec check only requires nonempty headings and a 40-character SHA. It cannot tell a copied heading from a settled owner/escape contract.

**Suggestions**
- Keep the SHA evidence as the git object, not a string pasted into the spec and then assumed proven.

**Risk Assessment:** MEDIUM. The gate is real, but a nonempty spec can still omit a mechanism the later plans depend on.

## 06-02

This is the right first product cut. Layout rendering and helper-input rendering are different paths in the installed pack, and the plan treats them that way. Prior location/key failures are now owned here.

**Strengths**
- `BaseInput.render` compiles `Template(str(self.value))` before the template runs (`.venv/.../crispy_forms/layout.py:250-256`). Overriding only `template` cannot meet D-15. The plan bypasses that method.
- `bootstrap5/inputs.html` `{% include %}`s `baseinput.html`, so `add_input()` never calls `render()`. Leaving legacy inputs on that path until 06-05 matches D-01.
- Wire names are not stored names. `baseinput.html` slugifies only when `wordcount > 1`; `__init__` always slugifies the id (`layout.py:240-244`). Comparing old pack output to the leaf is the right test.
- H-LOCATIONS is real and now owned: `E108_LOCATIONS` is `['card', 'context', 'list']` (`tests/test1/test_action_label_mode_config.py:278,323`); `test_button_classes_templates.py:214` walks `LOCATIONS` into `action.html`; `settings.md:78` is literal-eval'd against `LABEL_MODE_DEFAULTS` (`test_label_mode_docs.py:126`).
- `form:hidden-label:icon` stays outside `_action_key_parts` (`button_classes.py:223-226`). Adding two utility keys does not widen W362. 71 to 73 is the right arithmetic (`buttons.md:143-146` currently counts four icon-host keys).

**Concerns**
- LOW: Task 1's verify command does not run `tests/test1/test_label_mode.py`, which it edits. After `"form"` joins `LOCATIONS`, these fail until updated: `{"form": "label"}` is still an ignored unknown key (`test_label_mode.py:94`); `"form"` is still an invalid location (`:137`); whole-setting warnings are pinned at 3 (`:155`). Task 2's verify does run the file.
- LOW: `tests/test1/test_button_data.py:9` has a local `LOCATIONS = ["context", "list", "card"]` used by action-contract tests. Appending `"form"` there feeds action contexts into the form branch. The plan does not say to leave that list action-only.
- LOW: `test_icon_host_default_slots` (`test_button_classes.py:303-305`) still loops only `context/list/card/menu`. `EXPECTED_KEYS` catches a missing key; that loop will not.

**Suggestions**
- Add `test_label_mode.py` to task 1's verify command, and name the three assertions above.
- State that the local list in `test_button_data.py` stays action-only.

**Risk Assessment:** MEDIUM. The rendering break is specified against the installed crispy path. The remaining misses are test pins, not a wrong architecture.

## 06-03

Owner selection is separated from map selection, and the crispy overlay hazard is real. The plan's capture-before-flatten approach matches how these templates actually render.

**Strengths**
- `cv_first_inline_keys` returns the first non-None map and does not merge (`src/crud_views/lib/view/base.py:263-272`). Empty-map-then-floor is the existing list/context rule (`:323-328`). Reusing that seam is correct.
- `from_settings` runs at class-body import (`settings.py:13-15,67-68`); `crud_views_settings = CrudViewsSettings()` is a singleton (`:320`). `override_settings` cannot refresh it. Monkeypatch plus a live floor is the right test split.
- `Formsets.render` flattens before `formsets.html` (`src/crud_views/lib/formsets/layout.py:10-17`). `cv_x_formset` returns only `{"x_formset": ...}` (`templatetags/crud_views_formsets.py:7-9`). Child rows recurse through the same tag (`formset.html:42-48`). A private key copied at that boundary is necessary; a direct include of `formset.html` would not prove it.
- `Context.update` pushes a `ContextDict` and does not pop unless used as a context manager (`django/template/context.py:14-18,167-172`). `FormActions.render` calls `context.update` and discards the return (`.venv/.../crispy_forms/bootstrap.py`). Fixed stack offsets are unsafe. `get_response_dict` always sets `is_formset`, `template_pack`, and `inputs` (`crispy_forms_tags.py:137-178`), so classification does not need a new provenance field.
- Row helpers are created by a property (`inline_formset.py:52-71`) and do not set `view`. The plan's ban on re-reading `form.helper` is required.

**Concerns**
- LOW: Page-layer classification by crispy response keys is still heuristic. The required P-versus-enclosing-helper render is the only thing that makes it safe; the plan already requires that render.

**Suggestions**
- None beyond executing the nested `{% crispy x_form.form x_form.helper %}` case the plan already names. Formset helpers set `form_tag = False` and `disable_csrf = True` (`inline_formset.py:58-59`), so not forwarding CSRF is correct.

**Risk Assessment:** MEDIUM. The mechanism matches the source, but it is the easiest part of the phase to implement with a test that never hits `InclusionNode`.

## 06-04

Icon and mode work is correctly downstream of the utility keys. Semantic kind is already independent of the submitted name.

**Strengths**
- Cancel is `Button` with `name="reset"` (`form.py:75-82`); filter reset is `Reset("reset", ...)` (`list.py:73`). Delete passes `slot="form:delete"` (`form.py:130`). Inferring kind from `name` would merge cancel and filter reset. The plan forbids that.
- `resolve_icon_name_class` returns None for non-host icons (`icons.py:240-244`), and `icon_host_keys` then renders inline (`button_data.py:41-49`). Host opt-out is already "no class, nothing inline".
- `save`, `cancel`, and `filter-reset` are absent from `DEFAULT_ICONS` (`icons.py:14-39`). `workflow` and `filter` already exist. `WorkflowForm` does not set an icon today (`crud_views_workflow/lib/forms.py:11-20`).

**Concerns**
- LOW: Label mode must not call the renderer. The counting-renderer proof is in 06-06, not here. 06-04 can still ship a leaf that renders an icon in label mode if that later test is the first check.

**Suggestions**
- Keep the 06-04 leaf tests asserting no `<i>`/`svg` and no host class in label mode, which the plan already states. Do not treat 06-06 as the first time that is true.

**Risk Assessment:** LOW. The registries and slot split are small and match the current classes.

## 06-05

The helper lifecycle plan matches crispy's actual dispatch guard. Both boolean terms are real, and preparing the layout inside `render_layout` alone cannot admit an empty helper.

**Strengths**
- `FormHelper.__len__` is `len(self.layout.fields)` (`helper.py:99-104`). There is no `__bool__`, so an empty helper is falsy. `get_render` calls `get_response_dict` (and therefore `get_attributes`) before `if helper and helper.layout` (`crispy_forms_tags.py:109-116`). The `get_attributes` preparation plus a subclass `__bool__` and a truthy empty `Layout` is the mechanism that works.
- `FormHelper.__init__` replaces `layout` whenever `form is not None` (`helper.py:208-212`). The mixin calls `formhelper_class(request=..., view=self)` with no form (`mixins.py:318-319`). Not adding a required `form` argument preserves custom constructors. Deep-copy is required because a class-level `layout` is the shared attribute when `form` is None.
- Hidden controls stay on `helper.inputs` (`list.py:75-86`). `whole_uni_form.html` includes `display_form.html` and then `inputs.html`, so the pack wrapper (`mb-3` in `inputs.html`) follows layout actions. Pinning that order is accurate.
- `get_attributes` copies every non-underscore attribute except `layout` and `inputs` (`helper.py:338-346`). Underscore-prefixed lifecycle state will not leak. `view` will still overlay the page, which is why the private owner push is required.

**Concerns**
- LOW: An explicit empty `Layout()` whose `render_layout` returns empty `form_html` still includes `uni_form.html` (`display_form.html:1-8`), so discarded fields reappear. The plan refuses to override that and tests it. 06-08 does not tell consumers.

**Suggestions**
- Add one migration sentence for that pack fallback. Do not "fix" it with a global template override.

**Risk Assessment:** MEDIUM. The truthiness fix is specified against the installed guard. The mutable class layout is the historical bug this plan is actually closing.

## 06-06

The diagnostic split is implementable without changing context/list checks, and `resolve_icon` alone is not an availability test. The plan says both.

**Strengths**
- Context/list `cv_label_mode_checks` emits one E211 for any failed `is_label_mode_map`, then stops (`action_menu.py:46-64`). Invalid modes never become E210 there. A form-only branch is required; reusing that helper unchanged would violate D-16.
- ViewSet validation is `is_label_mode_map` only (`viewset/__init__.py:105-111`), which allows any string key. Form keys need a separate validator. Putting `form_actions_label_mode` on the existing validator would accept `form:unknown`.
- W352 walks `get_icons()` entries only (`icons.py:413-431`). `resolve_icon("unknown:save")` returns `("unknown", "save")`, not None (`icons.py:187-202`). A prefix/renderer check that does not call the renderer is required. The plan says that.
- `CrispyDeleteForm.helper` does not use `get_form_actions`; it renders delete plus cancel (`form.py:132-141`). Checking delete before the mixin avoids a false submit warning. `polymorphic_forms` is a class dict (`tests/test1/app/views.py:565-576`); `get_form_class` needs the request model (`crud_views_polymorphic/lib/utils.py:64-71`). Not calling it during checks is right.
- Declaring `cv_form_actions_label_mode` on `CrudView` is enough for W280. `CheckUnknownAttributes` learns names from package class bodies (`check.py:347-355`), not a hand list.

**Concerns**
- LOW: `SystemChecksTest` only fails on `level >= ERROR` (`examples/bootstrap5/project/tests.py:113`). A bad W292 will not fail the example gate. 06-06's own check tests are the warning gate.

**Suggestions**
- Keep W292 assertions in `test_form_button_checks.py`. Do not treat the example system-check test as warning coverage.

**Risk Assessment:** MEDIUM. The ID split is precise enough to implement, and the main failure mode is a checker that instantiates a form. The plan forbids that.

## 06-07

Browser and floor checks are aimed at the handlers that exist. The JS command reasserts the lock-backed runtime from 06-01.

**Strengths**
- `cvModalSubmit` already does `new FormData(form, submitter || undefined)` (`modal.js:75-82`). The test must use the native constructors. The plan says not to polyfill them.
- Cancel uses `closest("[data-cv-cancel-url]")` (`viewset.js:37-43`), so a click on an icon child works if the attribute stays on the button. Reset is bound by id (`list.filter.js:55-57`) and does not call `preventDefault`, so a `type="reset"` control still resets natively and then navigates. The plan's "do not invent preventDefault" matches this file.
- Reset only keeps `sort`, `order`, and `dir` (`list.filter.js:46-49`). The hidden field name is `dir`, not `direction` (`list.py:80-86`).
- `noxfile.py:6-14` installs Django, then `.[polymorphic,workflow,ordered,test]` in a second transaction. The plan's single resolver transaction with `django-crispy-forms==2.0` and `crispy-bootstrap5==2023.10` is the only way those extras cannot upgrade the floor. Base constraints are `>=2.0` and `>=2023.10`, so the pins are legal.

**Concerns**
- LOW: Prose in 06-05/06-08 says "sort/order/direction". The wire name and the JS keep-list use `dir`. A test that asserts `name="direction"` will fail against current markup.

**Suggestions**
- Write the hidden-field and reset assertions against `sort`, `order`, and `dir`, plus the view's `cv_order_param` / `cv_order_dir_param` when renamed.

**Risk Assessment:** MEDIUM. The floor session is the right proof, and it is also the longest unproven dependency in the phase.

## 06-08

Documentation is scheduled after the behavior exists, and the executable recipe test is the right check. The example login button is not a package `Submit`.

**Strengths**
- `examples/bootstrap5/project/urls.py:3,17` imports `crispy_forms.layout.Submit`. Enabling form `both` will not rewrite the login control.
- `test_docs_sync.py` only checks `<!-- cv-sync: -->` fences. Changing `settings.py` does not by itself fail that test unless a marked fence includes the new line. The plan still tells the executor to keep fences in sync.
- `tooltip.js:6-7` and `javascript.md:99-107` list locations and dispatch on `[data-cv-tooltip]` generically (`tooltip.js:27-28`). Adding `form` to the inventory without changing the listener is correct.
- Clearing `helper.inputs` today removes Apply/Reset because they live there (`list.py:70-73`). After 06-05 that stops working. The None-hook recipe is the real migration.

**Concerns**
- LOW: `buttons.md:495` and `action_menus.md:289` still describe E108 locations as only `"context"`, `"list"`, `"card"`. 06-08 updates the form contract, but it does not name those two sentences. They will be wrong once `"form"` is a location.
- LOW: The empty-`form_html` field fallback from 06-05 is not in the migration section.

**Suggestions**
- Update those two E108 sentences in the same edit as the settings defaults table, and add the pack-fallback sentence next to the `inputs=[]` recipe.

**Risk Assessment:** LOW. The docs work is large, but the behavior it describes is already assigned to earlier plans.

## 06-09

Acceptance is wired to tests that exist, including the example tree the root suite does not run. It does not treat inherited probes as results.

**Strengths**
- `examples/bootstrap5/pytest.ini` sets `DJANGO_SETTINGS_MODULE = project.settings`. `test_demo_pages_render_german` (`test_i18n.py:121-135`), `HomePageTest.test_every_feature_landing_page_renders` (`project/tests.py:45`), and `SystemChecksTest` (`:97-114`) exist. Root `pytest tests` does not collect that tree.
- `SystemChecksTest` imports the URLconf before `checks.run_checks()`. The plan's refusal of bare `manage.py check` matches the test's own comment.
- The German create page asserts the substring `value="Sichern"` (`test_i18n.py:135`), not the button body. FORM-06's preserved `value` attribute is what makes that gate pass after `<input>` becomes `<button>`.
- 06-07 and 06-08 do not share files. Acceptance depending on both is the right join.

**Concerns**
- LOW: Nothing in the acceptance command checks that `value="Sichern"` survived as an attribute rather than being "fixed" into element text. The existing test does. Do not relax it.
- LOW: Browser checks stay human-only until observed. The plan already says not to mark them passed. That is a completion rule, not a missing task.

**Suggestions**
- Record the German assertion as attribute evidence in `06-ACCEPTANCE.md`, next to the golden element-type diff.

**Risk Assessment:** LOW. This plan records evidence. It cannot repair an earlier omission, and the earlier omissions that used to land here are now owned upstream.

## Cross-plan

Prior blocking findings are incorporated in the current plan text and match the source. `"form"` joining `LOCATIONS` is updated in 06-02 together with E108, the settings literal, and the action-leaf sentinel loop. `form:hidden-label` and `form:icon-host` move with `EXPECTED_KEYS` in that same task, not in 06-04. Helper truthiness, enclosing-helper versus page, formset inclusion transport, and unknown-prefix availability are specified against `FormHelper.__len__`, `get_render`'s guard, `cv_x_formset`, and `resolve_icon`.

What remains is small: three `test_label_mode.py` pins are easy to miss because task 1 does not run that file; the local `LOCATIONS` list in `test_button_data.py` can be "fixed" wrongly; E108 prose in `buttons.md:495` and `action_menus.md:289` is not named; hidden fields are `dir`, not `direction`. None of those reopen the phase design.

**Overall risk: MEDIUM.** The phase still depends on real crispy context stacks and an isolated Node 22/jsdom 30 session. The plans now name the source mechanisms those gates have to hit, instead of assuming a direct `render()` call or the current Node 20 tree is enough.

---

## OpenCode Review (gemini-review)

## 06-01

### 1. Summary
Plan `06-01` establishes the Phase 6 design specification (`06-SPEC.md`), reconciles the locked Node/jsdom test runtime (`06-js-verify.sh` and `06-JS-RUNTIME.json`), and commits raw before-change `<input>` control baselines for `create`, `update`, `delete`, `workflow`, and `filter` views before any production code is edited. The plan is well-grounded in the current repository state and cleanly implements user decision D-18 (verifying Phase 1/2 contracts on the executing branch rather than requiring a merge to `main`).

### 2. Strengths
- **Executing-branch contract verification (D-18)**: Verifies Phase 1 lazy label-mode floors (`src/crud_views/lib/view/label_mode.py:23,84-117`) and Phase 2 finite form class-key grammar (`src/crud_views/lib/button_classes.py:209-236`) on the current branch HEAD before authoring `06-SPEC.md`, running `tests/test1/test_label_mode.py`, `tests/test1/test_action_label_mode_config.py`, and `tests/test1/test_button_classes.py`.
- **Upfront JS runtime reconciliation**: Addresses the version mismatch between `package.json:15-21` (`"jsdom": "^30.1.2"`, `"vitest": "^5.0.3"`) and the ambient environment in Wave 1 before any JS verification gate runs.
- **Preservation of existing delete POST tests**: Keeps `tests/test1/test_crud.py:63` (`client_user_author_delete.post(..., {"confirm": True})`) intact while adding a separate clicked-submitter POST regression (`{"confirm": True, "delete": "Delete"}`) in `tests/test1/test_form_buttons_golden.py` to test `CrispyDeleteForm` (`src/crud_views/lib/crispy/form.py:121-130`) + `DeleteView.post` (`src/crud_views/lib/views/delete.py:199-222`).

### 3. Concerns
- **LOW — Filter baseline extraction scope vs. Plan `06-05` (`src/crud_views/lib/views/list.py:70-87`, `src/crud_views/templates/crud_views/tags/list_filter.inner.html:14-16`)**:
  Currently, `ListViewFilterFormHelper.__init__` (`src/crud_views/lib/views/list.py:70-87`) appends `Submit`, `Reset`, and `layout.Hidden("sort"|"order"|"dir")` via `self.add_input(...)`, so `crispy_bootstrap5` renders all of them inside one trailing `<div class="mb-3"><div class="controls">` wrapper from `inputs.html`. In `06-05` Task 1, Apply/Reset move into `FormActions` inside `helper.layout` while `Hidden` inputs stay in `helper.inputs`. `06-01` Task 3 says *"Extend the capture harness for workflow submit/cancel and filter Apply/Reset plus hidden sort/order/direction controls"*, whereas `06-05` Task 1 says *"Extend the filter golden harness to capture the deterministic visible-action/hidden-wrapper region, excluding CSRF"*. If `06-01` Task 3 captures only individual `<input>` tags and `06-05` Task 1 changes the extractor to capture the surrounding wrapper region, the diff in `tests/test1/golden/form_buttons/filter.html` will conflate an extractor change with the `<input>` → `<button>` markup migration.

### 4. Suggestions
- In `06-01` Task 3, use the same region/control extraction logic for `<form id="filter-form">` (`src/crud_views/templates/crud_views/tags/list_filter.inner.html:14-16`, stripping only `csrfmiddlewaretoken` if present) that `06-05` Task 1 will use, so the `tests/test1/golden/form_buttons/filter.html` diff in `06-05` reflects only the rendered DOM change.

### 5. Risk Assessment
**LOW** — Read-only/test-only prerequisite wave with clear verification gates and no production code changes.

---

## 06-02

### 1. Summary
Plan `06-02` introduces the `crud_views/tags/button/form.html` leaf, adds `"form"` to `LOCATIONS` (`src/crud_views/lib/view/button_data.py:12`) and `"form": "label"` to `LABEL_MODE_DEFAULTS` (`src/crud_views/lib/view/label_mode.py:23`), adds `form:hidden-label` and `form:icon-host` to `DEFAULT_BUTTON_CLASSES` (`src/crud_views/lib/button_classes.py:84-94`), implements the `FORM_LEAF_KEYS` branch in `cv_button_data()`, and rewrites `Submit`/`Button`/`Reset` in `src/crud_views/lib/crispy/buttons.py` to render literal escaped values through the leaf.

### 2. Strengths
- **Atomic update of location and class-table guards**: `tests/test1/test_button_classes_templates.py:50-56` scans all `{% cv_button_class "<loc>" "<slot>" %}` literals in `src/*/templates/**/*.html` against `DEFAULT_BUTTON_CLASSES`, and `tests/test1/test_button_classes.py:90,97-101` asserts `len(EXPECTED_KEYS) == 71` and checks `docs/reference/buttons.md:145`. Moving `form:hidden-label` and `form:icon-host` (bringing the count from 71 to 73) and the location consumer updates into `06-02` Task 1 keeps the test suite green at Wave 2.
- **Elimination of crispy value template evaluation (FORM-07, D-15)**: Bypassing `BaseInput.render` prevents `Template(str(self.value)).render(context)` from executing template syntax (`{{ request.user }}`) and strips `SafeData` trust markers before escaping so `mark_safe("<b>")` still renders as literal `&lt;b&gt;`.
- **Wire-compatible multi-word name normalization**: Preserves crispy's `wordcount > 1` → `slugify` rule on `cv_name` while keeping `id` generation compatible with `BaseInput.__init__`.

### 3. Concerns
- **LOW — Hardcoded warning count in `tests/test1/test_label_mode.py:155`**:
  In `tests/test1/test_label_mode.py:58-59`, `_resolved()` calls `default_label_mode(location)` for every location in `sorted(LOCATIONS)`. In `test_default_label_mode_invalid_setting_whole` (`tests/test1/test_label_mode.py:149-156`), line 155 asserts `assert len(_records(caplog)) == 3  # one per location queried`. Adding `"form"` to `LOCATIONS` increases the number of queried locations in `_resolved()` from 3 to 4, so line 155 (and `test_default_label_mode_warns_once` if iterated over `LOCATIONS`) must be updated alongside `PACKAGE` (`line 17`), `line 94`, and `line 137`.
- **LOW — Partial `docs/reference/settings.md` update in Task 1 vs. `tests/test1/test_label_mode_docs.py:146`**:
  `06-02` Task 1 updates `docs/reference/settings.md:78` (`CRUD_VIEWS_LABEL_MODE_DEFAULTS` row in `## Action menus`) so `tests/test1/test_label_mode_docs.py:126` (`assert ast.literal_eval(cells[3].strip("`")) == dict(label_mode.LABEL_MODE_DEFAULTS)`) passes. Ensure the `CRUD_VIEWS_LABEL_MODE_DEFAULTS` row in `### Label-mode configuration` (`docs/reference/settings.md:90`, checked by `test_label_mode_docs.py:146,154-156`) stays consistent with `test_label_mode_docs.py` at Wave 2.

### 4. Suggestions
- In `06-02` Task 1, include `tests/test1/test_label_mode.py:155` (`len(_records(caplog)) == 4` or `len(LOCATIONS)`) in the `test_label_mode.py` update checklist, and run `pytest tests/test1/test_label_mode.py -q` in Task 1's `<verify>` block (currently `test_label_mode.py` is only in Task 2's `<verify>` block even though Task 1 modifies `label_mode.py` and `test_label_mode.py`).

### 5. Risk Assessment
**MEDIUM** — Core rendering and escaping boundary change; well-mitigated by TDD assertions on parsed DOM nodes/attributes and golden diffs.

---

## 06-03

### 1. Summary
Plan `06-03` adds per-kind form label-mode maps (`CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE`, `ViewSet.form_actions_label_mode`, `CrudView.cv_form_actions_label_mode`, `CrudView.cv_get_form_actions_label_mode()`, and `location="form"` in `CrudView.cv_get_action_label_mode`) and implements deterministic form-owner resolution (`form.cv_view` → current helper `view` → genuine page `view`) across standard crispy forms, multiple `FormActions`, and nested formsets.

### 2. Strengths
- **Exact alignment with existing settings singleton lifecycle**: Matches `src/crud_views/lib/settings.py:67-69` (`from_settings("CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE", default={})` on `CrudViewsSettings`), `src/crud_views/lib/viewset/__init__.py:85-86,105-111`, and `src/crud_views/lib/view/base.py:263-297` (`cv_first_inline_keys`), keeping whole-map replacement distinct from the lazy `default_label_mode("form")` floor.
- **Accurate trace of formset context-loss boundaries**: Correctly accounts for both `Formsets.render` (`src/crud_views/lib/formsets/layout.py:10-17`, which calls `context.flatten()`) and `@register.inclusion_tag(takes_context=True, filename="crud_views/formsets/formset.html")` on `cv_x_formset` (`src/crud_views/templatetags/crud_views_formsets.py:6-9`, which creates a fresh isolated context via `context.new(data)`), transporting only the scoped genuine page-owner fallback.
- **Protection against enclosing-helper shadowing**: Distinguishes crispy's `get_response_dict` helper overlay (`view=None` or an enclosing form's helper `view`) from genuine page `view` layers in `context.dicts`.

### 3. Concerns
- **LOW — AJAX empty-row formset rendering path (`src/crud_views/lib/formsets/formsets.py:374-387`)**:
  When `FormSetMixinBase.get_template_html` (`src/crud_views/lib/formsets/mixins.py:47-69`) renders an empty row for `?template=...`, `FormSets.get_template` (`src/crud_views/lib/formsets/formsets.py:385`) calls `render_to_string("crud_views/formsets/formset.html", {"x_formset": x_formset})` directly without a page `Context` or `Formsets.render`. For `CrispyModelForm` row forms, `InlineFormSet.get_form_kwargs` (`src/crud_views/lib/formsets/inline_formset.py:96-99`) sets `kwargs["cv_view"] = self.formset.cv_view`, so `form.cv_view` is populated; however, if a row form does not inherit `CrispyFormMixin` (e.g. `CrispyInlineModelForm` at `inline_formset.py:153`), `form.cv_view` is absent while `x_formset.formset.cv_view` holds the view.

### 4. Suggestions
- In `06-03` Task 2, when `cv_x_formset` (`src/crud_views/templatetags/crud_views_formsets.py:6-9`) is invoked for a recursive child formset or standalone without a transported page-owner key and `context` has no `"view"`, document that it falls back to `None` (project settings/floor) unless `form.cv_view` or helper `view` is set on the row.

### 5. Risk Assessment
**MEDIUM** — Context stack inspection across nested `{% crispy %}` and inclusion tags is subtle, but the plan's explicit test matrix (multiple `FormActions`, `helper.view=None`, conflicting enclosing helper vs. page owner, and recursive `Formsets` → `cv_x_formset`) directly exercises every boundary.

---

## 06-04

### 1. Summary
Plan `06-04` adds the `save`, `cancel`, and `filter-reset` semantic icons to `DEFAULT_ICONS` and `BOOTSTRAP_ICONS` (`src/crud_views/lib/icons.py`), wires inline and host-placed icon rendering in `crud_views/tags/button/form.html`, and connects semantic icon defaults and per-form overrides (`submit_icon`, `delete_icon`, and `WorkflowForm.submit_icon = "workflow"`).

### 2. Strengths
- **Registry parity**: Updates both `DEFAULT_ICONS` (`src/crud_views/lib/icons.py:14-49`) and `BOOTSTRAP_ICONS` (`src/crud_views/lib/icons.py:51-89`), preserving the invariants enforced by `tests/test1/test_icons_registry.py:106-112` (`BOOTSTRAP_ICONS.keys() == DEFAULT_ICONS.keys()` and `far`/`fas` prefixes).
- **Slot-driven semantic kind**: Determines `cv_key` from `slot` (`form:submit`, `form:delete`, `form:cancel`, `form:filter-submit`, `form:filter-reset`) rather than `name`, preserving compatibility with `test_delete_button_kwargs_may_choose_the_slot` (`tests/test1/test_crispy_buttons.py:62-73`) and `Cancel`/`Reset` sharing `name="reset"` (`src/crud_views/lib/crispy/form.py:76`, `src/crud_views/lib/views/list.py:73`).
- **Sentinel-based `icon=` kwarg on button adapters**: Distinguishes omitted `icon` (uses the kind's default semantic icon) from explicit `icon=None` or `icon=""` (suppresses the icon and triggers missing-icon handling in `"icon"` mode).

### 3. Concerns
- **LOW — Pop `icon` before `super().__init__` in `_TableClassMixin` (`src/crud_views/lib/crispy/buttons.py:16-18`)**:
  In `django-crispy-forms`, `BaseInput.__init__(self, name, value, ..., **kwargs)` passes all remaining `kwargs` to `flatatt(kwargs)` and stores the result on `self.flat_attrs`. If `_TableClassMixin.__init__` accepts `icon=...` (or if a caller passes `icon=` on a button that is later used with legacy `helper.add_input`), failing to consume `icon` before `super().__init__` would serialize `icon="..."` as an HTML attribute in `flat_attrs`.
- **LOW — Explicit glyph values in `06-04` Task 1 (`src/crud_views/lib/icons.py:14-89`)**:
  `06-04` Task 1 says *"Add save, cancel and filter-reset to DEFAULT_ICONS and BOOTSTRAP_ICONS with matching semantic meanings"* without quoting the exact `far:`/`fas:` and `bi:` strings inline in the task text (they live in `superpowers/plans/2026-10-24-concept-review-followups.md`).

### 4. Suggestions
- Ensure `_TableClassMixin.__init__` (`src/crud_views/lib/crispy/buttons.py:16`) consumes `icon` as an explicit keyword-only argument (with sentinel default) and does not forward it to `super().__init__`.
- Quote the exact `DEFAULT_ICONS` and `BOOTSTRAP_ICONS` strings for `save`, `cancel`, and `filter-reset` from `superpowers/plans/2026-10-24-concept-review-followups.md` in `06-SPEC.md` and `06-04` Task 1 so `icons.py`, `test_icons_registry.py`, and `docs/reference/icons.md` stay identical.

### 5. Risk Assessment
**LOW** — Builds directly on the leaf and class keys from `06-02` and existing `icon_host_keys` (`src/crud_views/lib/view/button_data.py:41-50`).

---

## 06-05

### 1. Summary
Plan `06-05` migrates `ListViewFilterFormHelper` (`src/crud_views/lib/views/list.py:57-87`) from `self.add_input(Submit(...))` / `self.add_input(Reset(...))` to a `get_form_actions()` hook appended as `FormActions` to an instance-isolated `helper.layout`, while keeping hidden `sort`/`order`/`dir` inputs on `helper.inputs` and preserving legacy `add_input()` usage on custom helpers.

### 2. Strengths
- **Complete resolution of crispy's dual truthiness guard (`if helper and helper.layout`)**: `FormHelper` inherits `__len__` returning `len(self.layout.fields)`, which makes `bool(helper)` `False` when `self.layout` is empty. By defining `ListViewFilterFormHelper.__bool__` to return `True` and preparing a private truthy `Layout` in `get_attributes()` (called by `BasicNode.get_response_dict` before `if helper and helper.layout:` in `BasicNode.get_render`), the plan guarantees `render_layout` is reached for unsubclassed helpers, empty `Layout()` replacements, and `get_form_actions() -> None`.
- **Instance isolation of class-level layouts (D-03)**: Clones class-level `layout = Layout(...)` (`tests/test1/app/views.py:288-289`, `docs/reference/list_view.md:143-146`) per helper instance so repeated instantiations or renders never accumulate `FormActions` on the shared class attribute.
- **Constructor compatibility**: Preserves `self.formhelper_class(request=self.request, view=self)` in `ListViewTableFilterMixin.get_filterset` (`src/crud_views/lib/views/mixins.py:318-320`).

### 3. Concerns
- **LOW — `copy.deepcopy` interaction with custom objects attached to `helper.layout`**:
  In `ListViewFilterFormHelper`, `self.view = view` is stored on the helper (`src/crud_views/lib/views/list.py:68`). As long as `copy.deepcopy` is called only on the `Layout` object (which contains crispy layout elements like `Row`, `Column4`, field names) and never on `self` (the helper, which holds `self.view` and potentially `self.form`), `deepcopy` will not copy the Django view or request. Care should be taken that if a caller puts a button with a reference to a view/form inside a custom `layout`, `deepcopy` only copies the field layout template before actions are appended.

### 4. Suggestions
- In `ListViewFilterFormHelper`, store the deep-copied layout on a private `_prepared_layout` attribute and track action-appended state per layout object identity (`id(layout)` or an underscore attribute on the private `Layout` subclass) so `get_attributes()` is strictly idempotent across repeated renders.

### 5. Risk Assessment
**MEDIUM** — `django-crispy-forms` `FormHelper` layout dispatch has several subtle sharp edges (`__len__` truthiness, `FormHelper(form)` overwriting class `layout`, `get_attributes` ordering), all of which are now explicitly addressed in Tasks 1 and 2.

---

## 06-06

### 1. Summary
Plan `06-06` extends Django system checks (`E106`, `E210`, `E211`, `W291`, `W292`) to validate form label-mode maps and statically knowable icon-only form buttons without icons, and implements the runtime strict/non-strict missing-icon fallback in `cv_button_data()`.

### 2. Strengths
- **Provider-first static `W292` inspection (`src/crud_views/lib/crispy/form.py:116-142`)**: `CrispyDeleteForm` subclasses `CrispyForm` (`CrispyFormMixin`) and therefore inherits `submit_icon = "save"`, even though `CrispyDeleteForm.helper` only renders `delete` (`delete_icon`) and `cancel`. Checking `issubclass(form_cls, CrispyDeleteForm)` before `CrispyFormMixin` avoids false-positive `W292` warnings on `submit` for delete views.
- **Safe static traversal of `polymorphic_forms` (`src/crud_views_polymorphic/lib/utils.py:35,64-72`)**: Inspects dict-valued `polymorphic_forms` entries directly rather than calling `PolymorphicCrudViewMixin.get_form_class()`, which would fail at check time because `self.polymorphic_model` requires URL kwargs or a database object.
- **Side-effect-free icon availability check (`src/crud_views/lib/icons.py:149-203`)**: Checks semantic icon resolution, library registration, and renderer usability without invoking the renderer callable, ensuring custom renderers execute at most once per rendered button in `tags/button/form.html` and zero times during system checks.

### 3. Concerns
- **LOW — `font` renderer usability check in the private icon-availability helper (`src/crud_views/lib/icons.py:164-175,205-220`)**:
  In `src/crud_views/lib/icons.py:164-175`, `_get_renderers()` maps any dict-configured library with `"renderer": "font"` (or omitted `"renderer"`) to `font_renderer`, which is a valid callable. However, `font_renderer` (`src/crud_views/lib/icons.py:208-217`) returns `SafeString("")` if `config.get("class")` is missing, not a `str`, or fails `.format(name=name)` (and for `placement == "host"`, `resolve_icon_name_class` at `lines 251-259` returns `None` in those cases). If the new private availability helper only checks `_get_renderers().get(prefix) is not None`, a misconfigured `font` library (e.g. `{"renderer": "font"}` with no `"class"`) would be treated as available by `cv_button_data` / `W292` even though it renders nothing.

### 4. Suggestions
- In the private availability helper in `src/crud_views/lib/icons.py`, when `config.get("renderer", "font") == "font"`, verify that `config.get("class")` is a non-empty `str` that formats `{name}` without raising (matching `resolve_icon_name_class` at `src/crud_views/lib/icons.py:252-259` and `_library_check_messages` at `lines 348-375`).

### 5. Risk Assessment
**LOW** — System checks and runtime normalizer fallback follow well-established patterns in `src/crud_views/lib/view/action_menu.py` and `src/crud_views/lib/view/buttons.py`.

---

## 06-07

### 1. Summary
Plan `06-07` validates browser handler behavior (`modal.js`, `viewset.js`, `list.filter.js`) with `<button>` elements and nested icon/label spans under the locked `jsdom 30.1.2` / `vitest 5.0.3` environment, and adds a `crispy_floor` nox session testing `django-crispy-forms==2.0` and `crispy-bootstrap5==2023.10` across Django 4.2 and 6.0 on Python 3.12.

### 2. Strengths
- **Real `SubmitEvent.submitter` and `FormData(form, submitter)` verification**: Tests `src/crud_views/static/crud_views/js/modal.js:75-84` (`body: new FormData(form, submitter || undefined)`) with native `SubmitEvent` and `FormData` instances on `<button type="submit">` elements containing nested `<i>`/`<span>` children, confirming that only the clicked submitter's `name`/`value` is included alongside `confirm` and `csrfmiddlewaretoken`.
- **Delegated click target coverage**: Verifies that `e.target.closest("[data-cv-cancel-url]")` in `src/crud_views/static/crud_views/js/viewset.js:40` and `document.getElementById("filter-button-reset")?.addEventListener("click", onReset)` in `src/crud_views/static/crud_views/js/list.filter.js:57` work when clicks land on child `<i>` or `<span>` nodes inside `<button>`.
- **Single-transaction floor installation in `noxfile.py`**: Constrains `django-crispy-forms==2.0` and `crispy-bootstrap5==2023.10` in the same `session.install(...)` invocation as `.[polymorphic,workflow,ordered,test]` so `uv` does not upgrade the floor packages.

### 3. Concerns
- **LOW — Default nox session list when adding `crispy_floor` to `noxfile.py` (`noxfile.py:1-33`)**:
  Currently `noxfile.py` has no `nox.options.sessions` list, so `task test` (`nox`) runs every session defined in `noxfile.py`. Adding `@nox.session(...) def crispy_floor(...)` without specifying whether it runs by default or `default=False` will include `crispy_floor` in every bare `nox` run. Additionally, if `--cov` is used in `crispy_floor`, it must use a distinct `--cov-report=xml:...` filename so it does not collide with `tests(session, django)` (`noxfile.py:18`).

### 4. Suggestions
- In `noxfile.py`, either omit `--cov-report=xml:...` in `crispy_floor` (or give it a distinct `coverage-crispy-floor-py{session.python}-dj{django}.xml` name) and explicitly decide whether `@nox.session(..., default=True)` is intended for `task test`.

### 5. Risk Assessment
**LOW** — Production JS already uses `new FormData(form, submitter || undefined)` (`modal.js:82`) and `.closest("[data-cv-cancel-url]")` (`viewset.js:40`), so JS source edits are unlikely to be needed.

---

## 06-08

### 1. Summary
Plan `06-08` updates reference and tutorial documentation (`buttons.md`, `settings.md`, `action_menus.md`, `icons.md`, `theme.md`, `list_view.md`, `tutorial-5-filters-permissions.md`, `javascript.md`), adds executable doc-recipe tests in `tests/test1/test_form_button_docs.py`, pairs the `CHANGELOG.md` `### Breaking` entry with `docs/migrating-1.0.md`, and enables `CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"form": "both"}` in `examples/bootstrap5/project/settings.py`.

### 2. Strengths
- **Executable documentation recipes (`tests/test1/test_form_button_docs.py`)**: Tests the documented field-only `ListViewFilterFormHelper` subclass (`docs/reference/list_view.md:143-146`), the `get_form_actions() -> None` suppression recipe (migrating away from `helper.inputs = []`), and custom button template overrides using `cv_value` / `cv_flat_attrs`.
- **Preservation of `cv-sync` blocks**: Keeps the `<!-- cv-sync: library/views.py -->` fenced blocks in `docs/getting_started/tutorial-5-filters-permissions.md:11,26,41` aligned with `examples/bootstrap5/test_docs_sync.py:86-92`.
- **Paired Breaking and Migration entries**: Satisfies the `CLAUDE.md` mandate that every `### Breaking` entry in `CHANGELOG.md` updates `docs/migrating-1.0.md`.

### 3. Concerns
- **LOW — Existing strict regex/AST guards in `tests/test1/test_label_mode_docs.py:88-100,419-428`**:
  1. `test_documented_card_floor_renders_label_only` (`tests/test1/test_label_mode_docs.py:88-100`) parses every `python` code block in `docs/reference/settings.md` containing `CRUD_VIEWS_LABEL_MODE_DEFAULTS` and asserts that **exactly one** assignment dict literal contains the key `"card"`, and that its value equals `{"card": "label"}`. If `06-08` Task 1 adds a new code block in `settings.md` that includes `"card"` alongside `"form"`, `assert len(examples) == 1` (`line 99`) will fail.
  2. `test_button_label_mode_check_reference` (`tests/test1/test_label_mode_docs.py:422-427`) asserts that the `viewset.E211` table row in both `docs/reference/buttons.md` and `docs/reference/action_menus.md` contains `"string or None"` exactly twice (`assert e211.count("string or None") == 2`) and matches ``r"`cv_card_actions_label_mode` (is )?the string or None "`` and ``r"`cv_context_action_label_mode` (is )?the string or None "``. Editing the `viewset.E211` row to add `cv_form_actions_label_mode` must preserve those exact substrings and count.

### 4. Suggestions
- In `06-08` Task 1, ensure any new `CRUD_VIEWS_LABEL_MODE_DEFAULTS` example fence in `docs/reference/settings.md` uses `{"form": "both"}` (without a `"card"` key), and keep the two `"string or None"` scalar clauses in the `viewset.E211` rows of `buttons.md` and `action_menus.md`.

### 5. Risk Assessment
**LOW** — Documentation and example configuration wave with automated doc-test and `mkdocs build --strict` verification.

---

## 06-09

### 1. Summary
Plan `06-09` executes the final integrated verification gates across Python, JavaScript, documentation, linting/formatting, and the `examples/bootstrap5` project, and records the complete requirement/decision/commit/browser evidence and generic downstream-theme follow-up in `06-ACCEPTANCE.md` and `06-VALIDATION.md`.

### 2. Strengths
- **Comprehensive quality gates**: Covers `.venv/bin/pytest tests -n auto`, `bash .planning/phases/06-form-button-leaf/06-js-verify.sh`, `.venv/bin/mkdocs build --strict`, `.venv/bin/ruff check`, `.venv/bin/ruff format --check`, and example-project tests under `examples/bootstrap5`.
- **Example-settings coverage**: Explicitly runs `examples/bootstrap5/test_i18n.py` (which tests `value="Sichern"` on `/library/author/create/` in German at `line 135` under the example's `CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"form": "both"}`), `SystemChecksTest::test_no_check_errors_with_every_viewset_registered` (`examples/bootstrap5/project/tests.py:98-115`), `HomePageTest::test_every_feature_landing_page_renders` (`lines 45-51`), `test_docs_sync.py`, and `test_doc_links.py`.
- **Clean downstream hygiene**: Records the downstream theme follow-up generically in `06-ACCEPTANCE.md` without referencing downstream repository names in new files.

### 3. Concerns
- **LOW — Partial vs. full `examples/bootstrap5` pytest execution in `Additional integrated gates`**:
  `06-09` runs specific files/tests under `examples/bootstrap5` (`SystemChecksTest`, `test_docs_sync.py`, `test_i18n.py`, `HomePageTest::test_every_feature_landing_page_renders`, `test_doc_links.py`), but `examples/bootstrap5` also contains per-app CRUD/form tests (`library/tests.py`, `formsets/tests.py`, `conditional/tests.py`, `workflow/tests.py`, `polymorphic_demo/tests.py`, `guardian_demo/tests.py`, `showcase/tests.py`) that exercise create, update, delete, cancel-origin (`library/tests.py:65-80`), and `form_payload` (`project/testing.py:6-24`) under the example's settings.

### 4. Suggestions
- In `06-09` Task 2 / `Additional integrated gates`, run the full `cd examples/bootstrap5 && ../../.venv/bin/pytest -q` suite (matching `noxfile.py:32-33`) in addition to or encompassing the targeted example gates so every example app's form tests run under `CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"form": "both"}`.

### 5. Risk Assessment
**LOW** — Final verification and documentation sign-off wave.

---

## Cross-Plan Comparison & Overall Assessment

| Plan | Wave | Scope | Primary Risk | Risk Level |
|---|---|---|---|---|
| `06-01` | 1 | `06-SPEC.md`, JS runtime wrapper, 5 before-change goldens | Filter golden extractor consistency with `06-05` | LOW |
| `06-02` | 2 | `form.html` leaf, `cv_button_data("form")`, literal adapters, utility keys | `test_label_mode.py:155` warning count when adding `"form"` to `LOCATIONS` | MEDIUM |
| `06-03` | 3 | Form label-mode maps and `form.cv_view` / helper / page owner resolution | Context layer classification across nested `{% crispy %}` / formset inclusions | MEDIUM |
| `06-04` | 4 | `save`/`cancel`/`filter-reset` icons, host/inline leaf, workflow/form hooks | Consuming `icon=` kwarg before `BaseInput.__init__` `flatatt` | LOW |
| `06-05` | 5 | `ListViewFilterFormHelper` `get_form_actions()` & layout isolation | `FormHelper` + `Layout` truthiness and idempotent `get_attributes` preparation | MEDIUM |
| `06-06` | 6 | `E106`/`E210`/`E211`/`W291`/`W292` checks & strict/log missing-icon fallback | Checking `font` library `class` format validity in non-rendering icon helper | LOW |
| `06-07` | 7 | `modal.js`/`viewset.js`/`list.filter.js` tests & `crispy_floor` nox session | `noxfile.py` session defaults / coverage XML path isolation | LOW |
| `06-08` | 7 | Reference/tutorial docs, `CHANGELOG.md`, `migrating-1.0.md`, example `both` | Preserving existing `test_label_mode_docs.py:99,423` assertions | LOW |
| `06-09` | 8 | Full quality gates, browser verification, `06-ACCEPTANCE.md` | Running all `examples/bootstrap5` feature tests | LOW |

### Overall Risk Assessment: **LOW-MEDIUM**
Across three prior convergence rounds, all high-severity architectural and ordering issues (such as atomic `LOCATIONS` / `DEFAULT_BUTTON_CLASSES` updates in Wave 2, `FormHelper.__len__` truthiness on empty filter layouts, `Formsets.render` + `cv_x_formset` context flattening, `CrispyDeleteForm` inheritance in static `W292`, and non-rendering icon availability checks) have been accurately traced against the repository source and incorporated into the plans. The remaining items above are all **LOW**-severity test/assertion details that are straightforward to handle during execution.

---

## Consensus Summary

This cycle reviews the manually revised plan set at `58e740d9b8bf7ef1077d728ae782b9d9995ced44`. It does not certify implementation or execution evidence. Previous review text is retained in the history section below; historical HIGH mentions do not enter this cycle's counts.

**Current result: 0 HIGH concerns and 4 actionable non-HIGH concerns (1 MEDIUM, 3 LOW).** All three configured reviewers completed source-cited 9/9 reviews, including successful bounded retries for Grok and Gemini. The prior four manual-revision findings are closed at plan-review level; implementation evidence remains required by execution.

### Agreed strengths

All three reviewers independently confirm atomic location/key-consumer migration, the literal-render bypass, whole-map singleton versus lazy-floor behavior, the corrected dual truthiness guard, genuine-page transport through actual formset inclusions, and non-rendering registry/renderer inspection. The dependency chain serializes shared source files while 06-07/06-08 remain disjoint. The working-branch prerequisite, baseline-first ordering, native browser evidence, support-floor session and paired migration remain intact.

### Agreed concerns and divergent views

Repeated suggestions concern immediate label-mode test sharding, preserving icon kwargs off the HTML path and keeping source-bound owner tests. Their required invariants already appear in executable plans; details are mapped below. Fable alone raises the third-kind argument contract; Grok identifies the two E108 rows; Gemini identifies stable filter extraction and built-in font configuration. Non-HIGH actionability does not require corroboration. Fable recommends moving Node preparation later, whereas Grok and Gemini support its current timing; the current per-wave validation schedule resolves that disagreement in favor of the existing plans.

### Previous findings rechecked

| Finding | Current executable disposition and independently inspected mechanism |
|---|---|
| H-HELPER-TRUTHINESS | 06-05 task 1 explicitly makes both the helper and prepared layout truthy while retaining field-count `len(helper)`; 06-01 records the dual guard and 06-05 task 2 exercises actual crispy dispatch with empty replacements and omitted actions. This addresses the short-circuit at `.venv/lib/python3.12/site-packages/crispy_forms/templatetags/crispy_forms_tags.py:116` and inherited length at `.venv/lib/python3.12/site-packages/crispy_forms/helper.py:99`. |
| M-OUTER-HELPER-PAGE | 06-03:107-108 excludes all enclosing crispy overlays, defines genuine page fallback and requires distinct page P/enclosing helper H/current helper None through stacked renders. Public helper attributes enter overlays at `.venv/lib/python3.12/site-packages/crispy_forms/helper.py:340`; the plan now targets that mechanism explicitly. |
| L-FORMSET-PAGE-CONTEXT | 06-03:109-110 owns both `Formsets.render` and `cv_x_formset`, transports only the private page tier before flattening, propagates it recursively and tests the actual production inclusion chain. Existing context loss is at `src/crud_views/lib/formsets/layout.py:17` and `src/crud_views/templatetags/crud_views_formsets.py:8`; row crispy dispatch is at `src/crud_views/templates/crud_views/formsets/formset.html:42`. |
| L-UNREGISTERED-FORM-ICON | 06-06:118-120 explicitly shares a side-effect-free semantic/library/renderer availability predicate, tests direct unknown prefixes and unusable renderers, and preserves raw-class/host opt-outs plus one renderer call. This covers `src/crud_views/lib/icons.py:199` returning unknown prefixes and `:230-236` rendering them empty without relying on registry-only W352. |

### Cross-artifact fact-drift pass

The deterministic phase-status seam returned `lag`: STATE Planning and ROADMAP Planned, ranks 0/1. This is not a finding; STATE remains the status authority.

ROADMAP Phase 6 FORM-01 through FORM-13 and all nine plans' requirement claims agree. The roadmap's real-button, unchanged default payload, literal escaping, semantic icon, mode/diagnostic and paired migration success criteria agree with the must-have truths. The context's D-01 through D-18 agree with the plans' locked terminology and behavior: whole-map selection versus per-key floors, quiet legacy helper inputs, form/helper/page ownership, ordinary-owner stopping, custom-template precedence, and working-branch prerequisites. Additional detailed truth/test obligations are refinements, not contradictions.

One already-known source-fact mismatch remains advisory: ROADMAP.md:227 describes the existing delete test as posting only delete=Delete, while `tests/test1/test_crud.py:63` actually posts confirm=True. 06-01:207-211 explicitly retains that test and adds a separate confirmation-plus-clicked-submitter regression. This evidence correction is already incorporated; it does not change the required unchanged-payload outcome or enter either convergence count. No status or context axis was skipped.

### Current unresolved findings

**M-FORM-DATA-KIND — MEDIUM; 06-01 specification and 06-02 task 1.** Required property: the newly supported form location must have an explicit, tested policy for the existing third `kind` argument, without confusing that argument with the finite form kind carried in `cv_key`. Source: `src/crud_views/lib/view/button_data.py:14` defines `KINDS={action,menu-item}` and `:52,60-61` validates the third argument. 06-02:98 prescribes an early form branch and validates `cv_key`/`cv_type`, but neither that task nor 06-01's Form contract specifies whether `cv_button_data(ctx, "form", "menu-item")` and an unknown third argument are accepted, ignored or rejected. Those are separate from invalid form `cv_key` tests. Record the chosen policy in the spec and executable 06-02 normalizer tests, preserving context/list/card behavior. Accepting the default call remains required by FORM-02. Rejecting non-default form `kind` values is one possible resolution, not a mandated product decision.

**L-E108-DOC-INVENTORY — LOW; 06-08 task 1 (or the producing 06-02 task 1).** Required property: published E108 diagnostic inventories must include the new valid form location. `docs/reference/buttons.md:495` and `docs/reference/action_menus.md:289` explicitly enumerate only context/list/card. 06-02:96 updates the settings.md inventory; 06-08:83-85 addresses form behavior and map diagnostics but does not expressly cover these two E108 inventories. Name both rows in the executable documentation edit and verify their accepted-location list against the new LOCATIONS set. Existing form-map E210/E211 documentation is a separate change. This is a documentation completion detail, not a phase-design blocker.

**L-FILTER-GOLDEN-SCOPE — LOW; 06-01 task 3 and 06-05 task 1.** Required property: the before/after filter golden compares the same captured region so extractor changes cannot masquerade as product markup changes. 06-01:201-204 establishes individual raw-control extraction and :228-230 extends it to filter actions/hidden controls. 06-05:84 then explicitly extends the harness to the surrounding visible-action/hidden-wrapper region. The current input pack places all these inputs together in its trailing wrapper (`.venv/lib/python3.12/site-packages/crispy_bootstrap5/templates/bootstrap5/inputs.html:1`); after migration only hidden inputs remain there. Specify one stable extraction region before the baseline is committed, or retain separate stable control and wrapper comparisons. This requires no rewriting of recorded baseline commits and no unrelated golden regeneration.

**L-FONT-ICON-AVAILABILITY — LOW; 06-06 task 2.** Required property: the built-in font renderer's known invalid configuration must have an explicit disposition in the shared availability policy, while preserving E354 and avoiding any renderer invocation. `src/crud_views/lib/icons.py:149-152,164-175` returns a callable font renderer even for a dict missing `class`; `:208-217` then returns empty markup for missing/non-string/invalid class formatting. 06-06:118 defines availability through semantic resolution, a library dict and usable registered renderer metadata, while :120 tests unknown/unusable renderer registrations but does not name this callable-built-in/invalid-config case. Existing E354 (`icons.py:348-375`) detects the library error separately; preserving it does not establish the icon-only runtime fallback. Add non-rendering validation and strict/non-strict tests for this built-in case, or explicitly document/test a justified disposition. Do not generalize into probing arbitrary custom renderers: their empty-result contract is already expressly preserved.

### HIGH consensus gate

No current HIGH was raised by any of the three completed source-cited reviews; the previous H-HELPER-TRUTHINESS is addressed by the revised dual-guard mechanism and confirmed by all three reviewers in this cycle. Historical HIGH quotations remain only as audit history. A failed or introductory-only lane is not corroboration or approval. The gate is applied only to substantive completed reviewer sections, never to diagnostic stubs.

### Structured issues

```yaml
issues:
  - id: M-FORM-DATA-KIND
    plan: "06-02"
    related_plans: ["06-01"]
    task: 1
    dimension: task_completeness
    severity: warning
    review_severity: MEDIUM
    required_property: "The form branch has explicit tested semantics for cv_button_data's existing third kind argument independently of cv_key."
    description: "The source validates KINDS action/menu-item before normalization, while the plan introduces an early form branch without choosing the policy for explicit menu-item or unknown third arguments."
    fix_hint: "Choose and document that policy in the spec and 06-02 action/behavior tests, including default, explicit menu-item and unknown values; preserve existing action locations."
  - id: L-E108-DOC-INVENTORY
    plan: "06-08"
    related_plans: ["06-02"]
    task: 1
    dimension: task_completeness
    severity: warning
    review_severity: LOW
    required_property: "Both published E108 diagnostic location inventories include the new form location."
    description: "buttons.md:495 and action_menus.md:289 explicitly list context/list/card; only the settings.md inventory is explicitly owned by the current location-migration task."
    fix_hint: "Name and update both E108 rows alongside the new form location, preserving existing diagnostics and verifying the accepted-location list."
  - id: L-FILTER-GOLDEN-SCOPE
    plan: "06-01"
    related_plans: ["06-05"]
    task: 3
    dimension: verification_quality
    severity: warning
    review_severity: LOW
    required_property: "Before/after filter golden evidence compares a stable extraction region."
    description: "06-01 captures individual controls, but 06-05:84 extends the extractor to surrounding wrapper markup during migration."
    fix_hint: "Choose the stable filter region before baseline capture, or keep separate stable control and wrapper comparisons; preserve baseline history."
  - id: L-FONT-ICON-AVAILABILITY
    plan: "06-06"
    task: 2
    dimension: key_links_planned
    severity: warning
    review_severity: LOW
    required_property: "Known invalid built-in font configuration has an explicit tested availability/fallback disposition without renderer calls."
    description: "A font renderer remains callable with missing or invalid class configuration, but icons.py:208-217 returns empty output; metadata-only callable checks do not cover this."
    fix_hint: "Validate built-in font formatting without invoking renderers and cover strict/non-strict results, or explicitly disposition this case while preserving E354 and custom-renderer contracts."
```

### Other reviewer observations: incorporated or advisory

| Observation | Executable coverage or source-grounded disposition |
|---|---|
| Move Node acquisition later; task 01 scope | 06-VALIDATION.md:26 requires full Python and JS after every integrated wave; 06-01 explicitly prepares the runtime before the first gate and has a blocker path. Moving the gate contradicts the agreed validation schedule. Task-size estimates are advisory; splitting does not add a missing behavioral requirement. |
| Pick semver resolution and literal nox install commands | 06-01 explicitly requires npm's bundled resolver, absolute paths and engine checks; 06-07:115 requires pins and extras in one resolver transaction and measured versions. Exact code spelling is implementation work already owned. |
| Unknown-key merge test silently changes meaning | 06-02:95 explicitly owns location/default updates and retains typo coverage. `tests/test1/test_label_mode.py:93` already tests `cotext`; `:110` combines a valid list key and `cotext`. The review's claim that unknown-key coverage is lost is not supported. Re-homing the former form row is part of the assigned assertion update. |
| Add more immediate test commands for label-mode/docs/import safety | The affected label-mode shards are already assigned in 06-02 and 06-08; integrated-wave full Python validation includes `test_import_safety.py`. 06-03 explicitly follows existing settings declarations/validation patterns, and 06-06 reads `_action_settings_messages`, whose source at settings.py:103 requires deferred view imports. The finding identifies no instruction to weaken the existing constraint; repeating an already required suite after every task is optional feedback. |
| Name exact crispy overlay discriminator keys | 06-01:135-151 requires the pre-implementation Ownership spec to define actual response-boundary classification; 06-03:107-110 owns stacked-overlay proof, exact page priority and real inclusion tests. `template_pack`/`is_formset` are usable source evidence at crispy_forms_tags.py:153-175, not an absent API. Choosing that implementation spelling is already an explicit spec task; no new invisible obligation remains. |
| Limit page transport to one private value | 06-03:109 already says transport only the page fallback, never the whole context, any helper owner or a public leaf key. Third-party helper extension compatibility is locked by D-09 through D-12 and manual revision; lack of a built-in producer does not negate it. |
| Pop icon before inherited kwargs serialization | 06-04:67 declares icon configuration never serialized, and 06-02:99 preserves legacy attributes. Raw `BaseInput` serialization at layout.py:248 explains the implementation order; the invariant is already executable. |
| Distinguish filter-reset from filter-close | 06-04:82 requires matching semantic meanings and 06-08:101 owns icons.md additions. Existing icons.md:57,72-74 already defines filter-close as panel state; documenting filter-reset's assigned reset action preserves that distinction. No rename or altered meaning is planned. |
| Empty Layout plus None hook pack fallback; hidden-wrapper visible margin | 06-05:109 explicitly preserves display_form.html/uni_form.html fallback and disclaims field suppression; 06-08:120 explicitly documents the retained margin/classes after visible actions. Both are already dispositioned in executable plans. |
| Preserve public helper.view | 06-05:82 adds underscore-prefixed lifecycle state and a private owner context key while preserving helper constructor/ownership. No task renames the existing public view attribute. |
| Form E106 message and W292 class/kind shape | 06-06:86-87 requires truthful form-specific messages, exact message/ID tests and unchanged context/list diagnostics; :117 expressly identifies form class and kind in warnings. No literal wording is required before the spec task owns it. |
| Gate new W292 solely on cv_viewset | The existing resolver at base.py:268-272 explicitly handles a class with no ViewSet using settings. The review's assertion that such a class has no map chain is incorrect. 06-06 already wires checks from CrudView.checks and scopes concrete providers; existing registration/check conventions remain the implementation guide. |
| Native reset ordering and assertions | 06-07:97-99 already requires actual field reset plus navigation, retaining the handler's existing prevention/propagation semantics. It does not prescribe a brittle order. |
| Changelog/table structural guards | 06-08:85 preserves existing assertions, synced fences and unique changelog prefix, and task 3 edits existing Unreleased sections paired with migration. Required doc tests plus full integrated gates cover the cited source guards. |
| Prefer a specific browser tool; state exactly five goldens | 06-09:85 already prefers available browser automation, forbids claimed unobserved acceptance and lists label/both/icon flows; :69 explicitly checks the final five golden diffs and no unrelated regeneration. A transient tool name is not a new acceptance condition. |

Fable's introductory claim that list.py:71 is the only source `slot=` call is inaccurate: `src/crud_views/lib/crispy/form.py:130` also passes the delete slot (and Fable cites the delete behavior later). It does not support a finding and does not change the slot-driven implementation contract.

Grok additionally rechecked the local action-only LOCATIONS test list, icon-host utility loop, early label-mode icon suppression, static W292 warning assertions, hidden field naming, and translated attribute evidence. These are already owned by 06-02's separate form contexts and utility-slot parametrization (:96-97), 06-04's no-output label branch (:82), 06-06's explicit W292 tests (:107-120), 06-05's unchanged/custom GET names (:107), and 06-09's preserved example assertions (:86). The prose term “direction” does not assert a wire name; source/current-value comparison remains the specified test. The empty-layout/None-hook pack fallback is explicitly dispositioned in 06-05:109 as unchanged pack behavior, so the suggestion to mention it again in public migration prose adds optional explanatory detail rather than an undispositioned behavior. Neither a passing example error-only system check nor a nonempty spec heading is claimed as a substitute for the separately required warning/behavior/source evidence.

Gemini's remaining observations are already incorporated or advisory: 06-02 owns location/default warning-count and matching settings-table updates; 06-03 explicitly defines absent page fallback as project settings and keeps form/helper priority, so an AJAX row with no page context does not authorize inventing a fourth owner tier from x_formset; 06-01 requires source-plan reading and 06-04 owns matching icon meanings/registry parity; 06-05 explicitly copies the layout rather than the helper and ties action state to layout identity. Nox default-session participation is an implementation choice, and no new coverage output is mandated; preserve the existing unique-output convention if adding coverage. The exact docs guards are already protected by 06-08's unchanged assertion requirement. Broader example-suite execution is optional breadth: targeted changed consumers plus full package tests and actual browser flows remain mandatory and no coverage hole is demonstrated by listing additional existing tests.

Gemini's strength description at settings.py:67-69 quotes the proposed form-map field as though it already exists. The actual source there declares existing context/list fields; the form field is a declared new artifact. Likewise submit_icon is a planned addition, not present current code. These inaccuracies are retained in raw reviewer text but are not accepted as source facts or additional findings.

## Verification coverage

The deterministic `drift-guard authority --raw` result is **intel**. `.planning/intel/API-SURFACE.md:5` explicitly reports an incomplete empty index and `api-map.json` is absent. Every non-new symbol below is **UNCHECKABLE** under that adapter. The severity seam returned `INFO, hardBlock=false`; no absence is treated as MISSING, and supplemental file/AST inspection is not an intel VERIFIED verdict. Signatures, CLI behavior, browser APIs, literal wire fields and configuration tokens remain unverified by this adapter. New artifacts are excluded before resolution.

Inventory: 328 referenced symbols/paths; 60 explicit new-artifact exclusions. Each row quotes a current plan line; all occurrence locations appear in the final column. Repeated or multiple declarations are candidates only, not signature proof.

| Symbol | Adapter verdict | Exact current-plan excerpt | Supplemental declaration/path evidence | Current plan occurrences |
|---|---|---|---|---|
| `--check` | UNCHECKABLE | &lt;automated&gt;.venv/bin/ruff format --check&lt;/automated&gt; | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-09-PLAN.md:233` |
| `--prefix` | UNCHECKABLE | Then invoke that absolute Node with its recorded npm-cli.js and --prefix . test, forwarding supplied test | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:108` |
| `--strict` | UNCHECKABLE | &lt;automated&gt;.venv/bin/mkdocs build --strict&lt;/automated&gt; | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-08-PLAN.md:122`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:88` |
| `-SUMMARY.md` | UNCHECKABLE | &lt;read_first&gt;All 06-*-SUMMARY.md files; 06-SPEC.md; 06-VALIDATION.md; 06-01 baseline commit evidence; tests/test1/test_crud.py; tests/test1/test_cancel_origin.py&lt;/read_first&gt; | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-09-PLAN.md:67` |
| `-n` | UNCHECKABLE | &lt;automated&gt;.venv/bin/pytest tests -n auto&lt;/automated&gt; | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-09-PLAN.md:72` |
| `-q` | UNCHECKABLE | tests/test1/test_action_label_mode_config.py tests/test1/test_button_classes.py -q; record the command, | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:91`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:189`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:216`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:237`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:102`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:126`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:141`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:87`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:113`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:86`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:107`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:87`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:112`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:93`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:123`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:89`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:105`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:237`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:241`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:245` |
| `-s` | UNCHECKABLE | &lt;automated&gt;.venv/bin/nox -s crispy_floor&lt;/automated&gt; | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-07-PLAN.md:118` |
| `../../.venv/bin/pytest` | UNCHECKABLE | &lt;automated&gt;cd examples/bootstrap5 &amp;&amp; ../../.venv/bin/pytest project/tests.py::SystemChecksTest::test_no_check_errors_with_every_viewset_registered -q&lt;/automated&gt; | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-09-PLAN.md:237`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:241`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:245` |
| `.planning/PROJECT.md` | UNCHECKABLE | @.planning/PROJECT.md | `.planning/PROJECT.md:1` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:54`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:67`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:56`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:56`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:55`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:58`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:53`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:64`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:49` |
| `.planning/REQUIREMENTS.md` | UNCHECKABLE | @.planning/REQUIREMENTS.md | `.planning/REQUIREMENTS.md:1` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:57` |
| `.planning/ROADMAP.md` | UNCHECKABLE | @.planning/ROADMAP.md | `.planning/ROADMAP.md:1` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:55`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:68`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:57`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:57`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:56`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:59`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:54`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:65`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:50` |
| `.planning/STATE.md` | UNCHECKABLE | @.planning/STATE.md | `.planning/STATE.md:1` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:56`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:69`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:58`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:58`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:57`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:60`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:55`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:66`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:51` |
| `.planning/phases/01-label-mode-defaults/01-CONTEXT.md` | UNCHECKABLE | .planning/phases/01-label-mode-defaults/01-CONTEXT.md; .planning/phases/02-form-key-grammar/02-CONTEXT.md; | `.planning/phases/01-label-mode-defaults/01-CONTEXT.md:1` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:79` |
| `.planning/phases/02-form-key-grammar/02-CONTEXT.md` | UNCHECKABLE | .planning/phases/01-label-mode-defaults/01-CONTEXT.md; .planning/phases/02-form-key-grammar/02-CONTEXT.md; | `.planning/phases/02-form-key-grammar/02-CONTEXT.md:1` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:79` |
| `.planning/phases/06-form-button-leaf/06-01-SUMMARY.md` | EXCLUDED_NEW | Create .planning/phases/06-form-button-leaf/06-01-SUMMARY.md with prerequisite and baseline commit evidence. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:316` |
| `.planning/phases/06-form-button-leaf/06-02-SUMMARY.md` | EXCLUDED_NEW | Create .planning/phases/06-form-button-leaf/06-02-SUMMARY.md. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-02-PLAN.md:186` |
| `.planning/phases/06-form-button-leaf/06-03-SUMMARY.md` | EXCLUDED_NEW | Create .planning/phases/06-form-button-leaf/06-03-SUMMARY.md. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-03-PLAN.md:176` |
| `.planning/phases/06-form-button-leaf/06-04-SUMMARY.md` | EXCLUDED_NEW | Create .planning/phases/06-form-button-leaf/06-04-SUMMARY.md. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-04-PLAN.md:147` |
| `.planning/phases/06-form-button-leaf/06-05-SUMMARY.md` | EXCLUDED_NEW | Create .planning/phases/06-form-button-leaf/06-05-SUMMARY.md. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-05-PLAN.md:177` |
| `.planning/phases/06-form-button-leaf/06-06-SUMMARY.md` | EXCLUDED_NEW | Create .planning/phases/06-form-button-leaf/06-06-SUMMARY.md. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-06-PLAN.md:188` |
| `.planning/phases/06-form-button-leaf/06-07-SUMMARY.md` | EXCLUDED_NEW | Create .planning/phases/06-form-button-leaf/06-07-SUMMARY.md. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-07-PLAN.md:160` |
| `.planning/phases/06-form-button-leaf/06-08-SUMMARY.md` | EXCLUDED_NEW | Create .planning/phases/06-form-button-leaf/06-08-SUMMARY.md. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-08-PLAN.md:179` |
| `.planning/phases/06-form-button-leaf/06-09-SUMMARY.md` | EXCLUDED_NEW | Create .planning/phases/06-form-button-leaf/06-09-SUMMARY.md. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-09-PLAN.md:294` |
| `.planning/phases/06-form-button-leaf/06-ACCEPTANCE.md` | EXCLUDED_NEW | - .planning/phases/06-form-button-leaf/06-ACCEPTANCE.md | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-09-PLAN.md:8`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:25`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:30`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:61`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:66`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:81` |
| `.planning/phases/06-form-button-leaf/06-CONTEXT.md` | UNCHECKABLE | @.planning/phases/06-form-button-leaf/06-CONTEXT.md | `.planning/phases/06-form-button-leaf/06-CONTEXT.md:1` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:58`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:70`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:59`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:59`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:58`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:61`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:56`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:67`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:52` |
| `.planning/phases/06-form-button-leaf/06-JS-RUNTIME.json` | EXCLUDED_NEW | - .planning/phases/06-form-button-leaf/06-JS-RUNTIME.json | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:10`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:77` |
| `.planning/phases/06-form-button-leaf/06-PATTERNS.md` | UNCHECKABLE | @.planning/phases/06-form-button-leaf/06-PATTERNS.md | `.planning/phases/06-form-button-leaf/06-PATTERNS.md:1` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:60`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:72`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:61`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:61`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:60`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:63`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:58`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:69`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:54` |
| `.planning/phases/06-form-button-leaf/06-RESEARCH.md` | UNCHECKABLE | @.planning/phases/06-form-button-leaf/06-RESEARCH.md | `.planning/phases/06-form-button-leaf/06-RESEARCH.md:1` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:59`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:71`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:60`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:60`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:59`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:62`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:57`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:68`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:53` |
| `.planning/phases/06-form-button-leaf/06-SPEC.md` | EXCLUDED_NEW | - .planning/phases/06-form-button-leaf/06-SPEC.md | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:8`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:31`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:77`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:189`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:199`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:226`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:73`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:62`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:62`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:61`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:64`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:59`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:70`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:55` |
| `.planning/phases/06-form-button-leaf/06-VALIDATION.md` | UNCHECKABLE | @.planning/phases/06-form-button-leaf/06-VALIDATION.md | `.planning/phases/06-form-button-leaf/06-VALIDATION.md:1` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:61`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:9`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:27`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:33`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:66`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:81` |
| `.planning/phases/06-form-button-leaf/06-js-verify.sh` | EXCLUDED_NEW | - .planning/phases/06-form-button-leaf/06-js-verify.sh | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:9`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:77`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:112`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:83`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:103`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:225` |
| `.venv/bin/mkdocs` | UNCHECKABLE | &lt;automated&gt;.venv/bin/mkdocs build --strict&lt;/automated&gt; | `.venv/bin/mkdocs:1` | `.planning/phases/06-form-button-leaf/06-08-PLAN.md:122`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:88` |
| `.venv/bin/nox` | UNCHECKABLE | &lt;automated&gt;.venv/bin/nox -s crispy_floor&lt;/automated&gt; | `.venv/bin/nox:1` | `.planning/phases/06-form-button-leaf/06-07-PLAN.md:118` |
| `.venv/bin/pytest` | UNCHECKABLE | VARIANT_LOCATIONS. Before authoring the spec, run .venv/bin/pytest tests/test1/test_label_mode.py | `.venv/bin/pytest:1` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:90`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:189`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:216`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:237`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:102`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:126`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:141`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:87`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:113`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:86`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:107`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:87`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:112`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:93`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:123`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:89`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:105`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:72`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:237`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:241`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:245` |
| `.venv/bin/python` | UNCHECKABLE | &lt;automated&gt;.venv/bin/python -c &#x27;from pathlib import Path; import re; p=Path(&quot;.planning/phases/06-form-button-leaf/06-SPEC.md&quot;); s=p.read_text(); headings=(&quot;Prerequisite evidence&quot;, &quot;Form contract&quot;, &quot;Literal text and attributes&quot;, &quot;Template selection&quot;, &quot;Ownership&quot;, &quot;Helper lifecycle&quot;, &quot;Diagnostics and icons&quot;, &quot;Dependency validation&quot;, &quot;Golden history&quot;); sections={h: re.search(r&quot;(?m)^## &quot; + re.escape(h) + r&quot;\n([\s\S]*?)(?=^## &#124;\Z)&quot;, s) for h in headings}; assert all(m and m.group(1).strip() for m in sections.values()), &quot;Missing/empty design section&quot;; assert re.search(r&quot;\b[0-9a-f]{40}\b&quot;, sections[&quot;Prerequisite evidence&quot;].group(1)), &quot;Missing executing-branch HEAD SHA&quot;&#x27; &amp;&amp; .venv/bin/pytest tests/test1/test_crispy_buttons.py tests/test1/test_button_data.py tests/test1/test_label_mode.py tests/test1/test_action_label_mode_config.py tests/test1/test_button_classes.py -q&lt;/automated&gt; | `.venv/bin/python:1` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:189` |
| `.venv/bin/ruff` | UNCHECKABLE | &lt;automated&gt;.venv/bin/ruff check&lt;/automated&gt; | `.venv/bin/ruff:1` | `.planning/phases/06-form-button-leaf/06-09-PLAN.md:229`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:233` |
| `/home/alex/.codex/gsd-core/templates/summary.md` | UNCHECKABLE | @/home/alex/.codex/gsd-core/templates/summary.md | `/home/alex/.codex/gsd-core/templates/summary.md:1` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:49`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:62`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:51`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:51`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:50`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:53`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:48`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:59`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:44` |
| `/home/alex/.codex/gsd-core/workflows/execute-plan.md` | UNCHECKABLE | @/home/alex/.codex/gsd-core/workflows/execute-plan.md | `/home/alex/.codex/gsd-core/workflows/execute-plan.md:1` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:48`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:61`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:50`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:50`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:49`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:52`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:47`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:58`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:43` |
| `06-01-SUMMARY.md` | EXCLUDED_NEW | Create .planning/phases/06-form-button-leaf/06-01-SUMMARY.md with prerequisite and baseline commit evidence. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:316`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:86`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:136` |
| `06-07-SUMMARY.md` | EXCLUDED_NEW | Create .planning/phases/06-form-button-leaf/06-07-SUMMARY.md. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-07-PLAN.md:160`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:82` |
| `06-08-SUMMARY.md` | EXCLUDED_NEW | Create .planning/phases/06-form-button-leaf/06-08-SUMMARY.md. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-08-PLAN.md:179`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:82` |
| `06-JS-RUNTIME.json` | EXCLUDED_NEW | - .planning/phases/06-form-button-leaf/06-JS-RUNTIME.json | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:10`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:69`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:77`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:102`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:65` |
| `06-RESEARCH.md` | UNCHECKABLE | @.planning/phases/06-form-button-leaf/06-RESEARCH.md | `.planning/phases/06-form-button-leaf/06-RESEARCH.md:1` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:59`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:71`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:60`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:60`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:59`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:62`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:57`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:71`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:113`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:68`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:53` |
| `06-SPEC.md` | EXCLUDED_NEW | - .planning/phases/06-form-button-leaf/06-SPEC.md | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:8`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:31`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:66`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:77`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:189`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:199`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:226`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:73`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:62`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:74`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:97`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:62`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:61`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:73`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:64`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:103`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:59`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:70`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:82`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:55`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:67` |
| `06-VALIDATION.md` | UNCHECKABLE | @.planning/phases/06-form-button-leaf/06-VALIDATION.md | `.planning/phases/06-form-button-leaf/06-VALIDATION.md:1` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:61`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:9`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:27`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:33`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:61`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:66`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:67`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:81`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:82` |
| `06-js-verify.sh` | EXCLUDED_NEW | - .planning/phases/06-form-button-leaf/06-js-verify.sh | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:9`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:69`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:77`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:103`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:112`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:65`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:83`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:103`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:225` |
| `ACCEPTANCE.md` | UNCHECKABLE | - .planning/phases/06-form-button-leaf/06-ACCEPTANCE.md | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-09-PLAN.md:8`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:25`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:30`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:61`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:66`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:81` |
| `BOOTSTRAP_ICONS` | UNCHECKABLE | Add save, cancel and filter-reset to DEFAULT_ICONS and BOOTSTRAP_ICONS with matching semantic meanings. Ensure the leaf reads mode classes through cv_button_class and the existing form utility keys through dedicated lookups; host classes must be escaped as attributes. Label mode suppresses all icon output and host classes, both emits icon plus text without generated tooltip, icon emits hidden text/title/form tooltip. Cover renderer prefix variants and explicit host opt-out, a Unicode/lazy label, an empty label, and repeated renders with changed registry/settings. Extend the real host/leaf tests for finite kind grammar and utility keys and keep exhaustive class/default checks green. | `src/crud_views/lib/icons.py:51` | `.planning/phases/06-form-button-leaf/06-04-PLAN.md:83` |
| `BaseInput` | UNCHECKABLE | Implement adapter render without calling BaseInput.render: retain raw value and kwargs, normalize per spec, render the selected leaf through a scoped context copy. Strip inherited input aliases from the template context, never expose the adapter object. Normalize SafeData and lazy values at render time to ordinary strings then use Django autoescaping once; serialized extra attrs are escaped once separately. Preserve constructor signature, slot-selected semantic kind, upstream generated IDs and legacy field_classes/flat_attrs for helper.inputs. Do not infer kind from the submitted name. The leaf uses cv_button_class form/cv_key/cv_label_mode, appends cv_css_class and host classes, and renders the three bodies with cancel URL only for cancel. Keep normalizer/icon behavior extensible for 06-04 rather than hardcoding a temporary floor. Update existing input-only assertions only where layout buttons changed; filter helper inputs remain inputs until 06-05. | `.venv/lib/python3.12/site-packages/crispy_forms/layout.py:199` | `.planning/phases/06-form-button-leaf/06-02-PLAN.md:99`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:112`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:178` |
| `BaseInput.render` | UNCHECKABLE | Implement adapter render without calling BaseInput.render: retain raw value and kwargs, normalize per spec, render the selected leaf through a scoped context copy. Strip inherited input aliases from the template context, never expose the adapter object. Normalize SafeData and lazy values at render time to ordinary strings then use Django autoescaping once; serialized extra attrs are escaped once separately. Preserve constructor signature, slot-selected semantic kind, upstream generated IDs and legacy field_classes/flat_attrs for helper.inputs. Do not infer kind from the submitted name. The leaf uses cv_button_class form/cv_key/cv_label_mode, appends cv_css_class and host classes, and renders the three bodies with cancel URL only for cancel. Keep normalizer/icon behavior extensible for 06-04 rather than hardcoding a temporary floor. Update existing input-only assertions only where layout buttons changed; filter helper inputs remain inputs until 06-05. | `.venv/lib/python3.12/site-packages/crispy_forms/layout.py:250` | `.planning/phases/06-form-button-leaf/06-02-PLAN.md:99`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:178` |
| `BasicNode.get_render` | UNCHECKABLE | &lt;read_first&gt;06-SPEC.md ownership contract; installed crispy BasicNode.get_render/get_response_dict, FormActions.render and FormHelper.get_attributes; src/crud_views/lib/formsets/layout.py; src/crud_views/templatetags/crud_views_formsets.py; src/crud_views/templates/crud_views/formsets/formsets.html; src/crud_views/templates/crud_views/formsets/formset.html; Django InclusionNode.render; tests/test1/test_crispy_buttons.py&lt;/read_first&gt; | `.venv/lib/python3.12/site-packages/crispy_forms/templatetags/crispy_forms_tags.py:70` | `.planning/phases/06-form-button-leaf/06-03-PLAN.md:97`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:73` |
| `BasicNode.get_response_dict` | UNCHECKABLE | &#124; H-OVERLAY-PROVENANCE &#124; Rejected as a missing-API claim, not as a test obligation: installed BasicNode.get_response_dict supplies inputs/is_formset/template_pack metadata; no named provenance field is required. Task 2 and the pre-implementation spec retain the current-invocation/page-boundary proof and nested-row/None regressions; this single-reviewer unconfirmed HIGH does not authorize an ownership redesign or certify future implementation. &#124; | `.venv/lib/python3.12/site-packages/crispy_forms/templatetags/crispy_forms_tags.py:137` | `.planning/phases/06-form-button-leaf/06-03-PLAN.md:147`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:83` |
| `CHANGELOG.md` | UNCHECKABLE | - CHANGELOG.md | `CHANGELOG.md:1` | `.planning/phases/06-form-button-leaf/06-08-PLAN.md:17`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:114`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:115` |
| `CLAUDE.md` | UNCHECKABLE | @CLAUDE.md | `CLAUDE.md:1` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:53`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:66`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:55`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:55`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:54`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:57`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:52`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:63`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:48` |
| `CONTEXT.md` | UNCHECKABLE | @.planning/phases/06-form-button-leaf/06-CONTEXT.md | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:58`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:79`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:275`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:70`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:59`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:59`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:58`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:61`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:56`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:67`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:52` |
| `CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE` | EXCLUDED_NEW | NEW fields: CrudViewsSettings.form_actions_label_mode (CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE), ViewSet.form_actions_label_mode, CrudView.cv_form_actions_label_mode. NEW public resolver: CrudView.cv_get_form_actions_label_mode(). Existing cv_get_action_label_mode gains location=&#x27;form&#x27;. Private owner-recovery helpers and a scoped page-owner transport key across Formsets/cv_x_formset are internal, not promised public names or leaf-context keys. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-03-PLAN.md:68`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:83`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:84`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:85` |
| `CRUD_VIEWS_ICONS` | UNCHECKABLE | Resolve form mode through the public resolver; catch ValueError only around mode resolution so E108/E210/E211 survive strict checking. For M-REGISTRY-OFF and M-ICON-AVAILABILITY, use the existing icons.resolve_icon(value) in both static inspection and the form normalizer: a None result means an absent/disabled semantic mapping, including explicit None/empty and a semantic name mapped by CRUD_VIEWS_ICONS to None/empty. Test each with known default submit/delete/filter controls. For L-UNREGISTERED-FORM-ICON, semantic resolution alone is insufficient: a nonempty prefix must also have a dict-valued library entry and a usable registered renderer. Add a private side-effect-free availability helper in icons.py reusing resolve_icon/get_libraries/_get_renderers metadata; resolving a renderer callable is allowed, invoking it is not. Share this predicate between form static checks and the normalizer. A resolved empty prefix is the existing raw CSS-class path and remains available. A direct submit_icon=&#x27;unknown:save&#x27; must trigger W292 for static icon-only controls and the same strict ValueError/non-strict logged label fallback as disabled semantic icons at runtime. Registry W352 only visits table entries, so do not claim it covers direct per-form values. Preserve existing registry diagnostics for malformed libraries and named entries; do not change their IDs or silently suppress them. Never call render_icon or a custom renderer to probe availability. Leave actual inline rendering to the leaf&#x27;s one cv_icon call; no rendered-markup cache or extra public leaf key is needed. A custom renderer&#x27;s returned markup remains its existing renderer contract, not a second missing-mapping test. Preserve icon_host_keys/resolve_icon_name_class for placement: a valid host icon is available even though the leaf emits no inline element, and a None/empty form:icon-host class override remains the existing explicit placement opt-out rather than a missing semantic icon. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-06-PLAN.md:118` |
| `CRUD_VIEWS_LABEL_MODE_DEFAULTS` | UNCHECKABLE | Extend the config suite&#x27;s existing monkeypatch.setattr(crud_views_settings, ...) pattern for form maps, restoring it after each case; construct CrudViewsSettings(form_actions_label_mode=...) explicitly for model-level validation cases. Add real crispy rendering with a monkeypatched singleton submit=&#x27;both&#x27; and an unmapped cancel: a post-import override_settings(CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE={&#x27;submit&#x27;: &#x27;icon&#x27;}) alone leaves submit in both, while nested CRUD_VIEWS_LABEL_MODE_DEFAULTS={&#x27;form&#x27;: &#x27;icon&#x27;} changes only the unmapped cancel and exiting restores its label floor. Keep this distinction explicit in the spec and documentation rather than treating override_settings on the map as a supported hot refresh. The render assertion proves the selected map is connected to the leaf. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-03-PLAN.md:84`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:85`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:119` |
| `CRUD_VIEWS_STRICT` | UNCHECKABLE | In cv_button_data&#x27;s form branch perform the dynamic guard after effective mode/icon resolution. For icon mode with no icon, including registry-disabled semantic names, strict raises ValueError naming form kind; non-strict logs one warning per render using the existing button-data logger, switches to label and drops generated icon-only title/tooltip/host classes. Set CRUD_VIEWS_STRICT explicitly in both test branches. With empty label as well, retain the empty literal payload and log the both-missing diagnostic; do not invent text. Validate exact FORM_LEAF_KEYS membership, cancel-only URL, invalid caller kind/type and absence of action-only fields here. Add real crispy render tests with custom hooks and concrete/dynamic polymorphic providers so static skipping cannot create a silent hole. No placement/owner conflict warnings are introduced. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-06-PLAN.md:119` |
| `Context.dicts` | UNCHECKABLE | Define owner recovery from Django Context.dicts before flattening: the actual adapter render(form, context) | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:133`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:107` |
| `CrispyDeleteForm` | UNCHECKABLE | EXISTING prerequisites from 06-02: form:hidden-label and form:icon-host with updated exhaustive keys/count. NEW registry names: save, cancel, filter-reset. NEW form attributes: CrispyFormMixin.submit_icon=&#x27;save&#x27;, CrispyDeleteForm.delete_icon=&#x27;delete&#x27;, WorkflowForm.submit_icon=&#x27;workflow&#x27;. NEW adapter icon= keyword is consumed as rendering configuration, never serialized as an HTML attribute; omission selects kind default while explicit None/empty suppresses it. | `src/crud_views/lib/crispy/form.py:116` | `.planning/phases/06-form-button-leaf/06-04-PLAN.md:68`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:116` |
| `CrispyDeleteForm.delete_icon` | EXCLUDED_NEW | EXISTING prerequisites from 06-02: form:hidden-label and form:icon-host with updated exhaustive keys/count. NEW registry names: save, cancel, filter-reset. NEW form attributes: CrispyFormMixin.submit_icon=&#x27;save&#x27;, CrispyDeleteForm.delete_icon=&#x27;delete&#x27;, WorkflowForm.submit_icon=&#x27;workflow&#x27;. NEW adapter icon= keyword is consumed as rendering configuration, never serialized as an HTML attribute; omission selects kind default while explicit None/empty suppresses it. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-04-PLAN.md:68` |
| `CrispyFormMixin` | UNCHECKABLE | EXISTING prerequisites from 06-02: form:hidden-label and form:icon-host with updated exhaustive keys/count. NEW registry names: save, cancel, filter-reset. NEW form attributes: CrispyFormMixin.submit_icon=&#x27;save&#x27;, CrispyDeleteForm.delete_icon=&#x27;delete&#x27;, WorkflowForm.submit_icon=&#x27;workflow&#x27;. NEW adapter icon= keyword is consumed as rendering configuration, never serialized as an HTML attribute; omission selects kind default while explicit None/empty suppresses it. | `src/crud_views/lib/crispy/form.py:11` | `.planning/phases/06-form-button-leaf/06-04-PLAN.md:68`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:104`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:116` |
| `CrispyFormMixin.submit_icon` | EXCLUDED_NEW | EXISTING prerequisites from 06-02: form:hidden-label and form:icon-host with updated exhaustive keys/count. NEW registry names: save, cancel, filter-reset. NEW form attributes: CrispyFormMixin.submit_icon=&#x27;save&#x27;, CrispyDeleteForm.delete_icon=&#x27;delete&#x27;, WorkflowForm.submit_icon=&#x27;workflow&#x27;. NEW adapter icon= keyword is consumed as rendering configuration, never serialized as an HTML attribute; omission selects kind default while explicit None/empty suppresses it. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-04-PLAN.md:68` |
| `CrudView` | UNCHECKABLE | NEW fields: CrudViewsSettings.form_actions_label_mode (CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE), ViewSet.form_actions_label_mode, CrudView.cv_form_actions_label_mode. NEW public resolver: CrudView.cv_get_form_actions_label_mode(). Existing cv_get_action_label_mode gains location=&#x27;form&#x27;. Private owner-recovery helpers and a scoped page-owner transport key across Formsets/cv_x_formset are internal, not promised public names or leaf-context keys. | `src/crud_views/lib/view/base.py:61` | `.planning/phases/06-form-button-leaf/06-03-PLAN.md:68`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:107`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:116` |
| `CrudView.checks` | UNCHECKABLE | Introduce a static form checker wired from CrudView.checks. Inspect concrete statically selected form classes only while the helper property, action provider and relevant button/kwargs hooks retain known package implementations. Select the provider before controls (H-DELETE-STATIC): check CrispyDeleteForm first, whose helper renders delete via delete_icon plus cancel, never its inherited submit_icon. Otherwise default CrispyFormMixin/workflow helpers render submit via submit_icon plus cancel. Hook/helper overrides make the affected provider dynamic rather than evidence for inherited controls. Tests set inherited submit_icon=None on a default delete form and require no submit warning, then delete_icon=None and require a delete W292; custom delete helpers also get runtime coverage. | `src/crud_views/lib/view/base.py:135` | `.planning/phases/06-form-button-leaf/06-06-PLAN.md:116` |
| `CrudView.cv_form_actions_label_mode` | EXCLUDED_NEW | NEW fields: CrudViewsSettings.form_actions_label_mode (CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE), ViewSet.form_actions_label_mode, CrudView.cv_form_actions_label_mode. NEW public resolver: CrudView.cv_get_form_actions_label_mode(). Existing cv_get_action_label_mode gains location=&#x27;form&#x27;. Private owner-recovery helpers and a scoped page-owner transport key across Formsets/cv_x_formset are internal, not promised public names or leaf-context keys. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-03-PLAN.md:68` |
| `CrudView.cv_get_form_actions_label_mode` | EXCLUDED_NEW | NEW fields: CrudViewsSettings.form_actions_label_mode (CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE), ViewSet.form_actions_label_mode, CrudView.cv_form_actions_label_mode. NEW public resolver: CrudView.cv_get_form_actions_label_mode(). Existing cv_get_action_label_mode gains location=&#x27;form&#x27;. Private owner-recovery helpers and a scoped page-owner transport key across Formsets/cv_x_formset are internal, not promised public names or leaf-context keys. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-03-PLAN.md:68` |
| `CrudViewsSettings` | UNCHECKABLE | or explicit CrudViewsSettings arguments, not an invented setting_changed refresh; 06-03 proves the distinction. | `src/crud_views/lib/settings.py:17` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:156`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:26`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:68`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:83`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:84` |
| `CrudViewsSettings.form_actions_label_mode` | EXCLUDED_NEW | NEW fields: CrudViewsSettings.form_actions_label_mode (CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE), ViewSet.form_actions_label_mode, CrudView.cv_form_actions_label_mode. NEW public resolver: CrudView.cv_get_form_actions_label_mode(). Existing cv_get_action_label_mode gains location=&#x27;form&#x27;. Private owner-recovery helpers and a scoped page-owner transport key across Formsets/cv_x_formset are internal, not promised public names or leaf-context keys. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-03-PLAN.md:68`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:83` |
| `DEFAULT_ICONS` | UNCHECKABLE | Add save, cancel and filter-reset to DEFAULT_ICONS and BOOTSTRAP_ICONS with matching semantic meanings. Ensure the leaf reads mode classes through cv_button_class and the existing form utility keys through dedicated lookups; host classes must be escaped as attributes. Label mode suppresses all icon output and host classes, both emits icon plus text without generated tooltip, icon emits hidden text/title/form tooltip. Cover renderer prefix variants and explicit host opt-out, a Unicode/lazy label, an empty label, and repeated renders with changed registry/settings. Extend the real host/leaf tests for finite kind grammar and utility keys and keep exhaustive class/default checks green. | `src/crud_views/lib/icons.py:14` | `.planning/phases/06-form-button-leaf/06-04-PLAN.md:83` |
| `E108_LOCATIONS` | UNCHECKABLE | Start with a failing real-crispy render test. Add form to LOCATIONS and label to LABEL_MODE_DEFAULTS together. In this same change update E108_LOCATIONS in test_action_label_mode_config.py to include form, move the old form-invalid case to the valid defaults parametrization, and retain unknown-location coverage using an actual typo. Update the settings.md defaults table literal and location prose, plus test_label_mode_docs.py&#x27;s matching location assertions; full form-map documentation stays in 06-08. In test_button_classes_templates.py, use VARIANT_LOCATIONS for action/menu sentinel loops, assert its relation to LOCATIONS, and add separate form-leaf sentinel cases over every FORM_KINDS/mode combination with valid form contexts and an existing registered icon. Do not remove coverage or pass form into action leaves. These small direct consumer updates are inseparable from the location/default migration despite exceeding the usual per-task file heuristic (H-LOCATIONS). | `tests/test1/test_action_label_mode_config.py:278` | `.planning/phases/06-form-button-leaf/06-02-PLAN.md:96` |
| `EXPECTED_KEYS` | UNCHECKABLE | Add form:hidden-label=&#x27;visually-hidden&#x27; and form:icon-host now, before advertising icon/host rendering (H-EARLY-UTILITIES, D-14). Update test_button_classes.py&#x27;s exhaustive EXPECTED_KEYS, the measured count (71 to 73 on the reviewed tree), and utility-slot parametrization in this same producing task (H-KEYSET). Update buttons.md&#x27;s measured count and complete utility rows/arithmetic, including five icon-host keys. Preserve finite FORM_KINDS/VARIANT_LOCATIONS; a utility key never accepts a mode suffix. Test hidden-label/title/form-tooltip and host class behavior with an already registered icon; new semantic icon names/hooks remain 06-04 work. | `tests/test1/test_button_classes.py:21` | `.planning/phases/06-form-button-leaf/06-02-PLAN.md:97`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:158`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:82` |
| `FORM_KINDS` | UNCHECKABLE | contracts at that HEAD: default_label_mode with shared lazy defaults and independent FORM_KINDS / | `src/crud_views/lib/button_classes.py:210`<br>`tests/test1/test_button_classes_checks.py:111` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:89`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:96`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:97`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:98`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:25`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:41`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:88` |
| `FORM_LEAF_KEYS` | EXCLUDED_NEW | 06-02 through 06-06. Set separate FORM_LEAF_KEYS, preserving LEAF_KEYS; define type/name/value/id/key, | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:116`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:79`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:98`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:119`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:84`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:157` |
| `FormActions` | UNCHECKABLE | helper overlay by its provenance/response metadata, never a fixed stack offset: FormActions leaves extra | `.venv/lib/python3.12/site-packages/crispy_forms/bootstrap.py:259` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:140`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:141`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:158`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:170`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:268`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:88`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:30`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:97`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:103`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:107`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:108`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:114`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:129`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:24`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:41`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:67`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:71`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:77`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:100`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:107`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:108`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:31`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:101`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:196` |
| `FormActions.render` | UNCHECKABLE | &lt;read_first&gt;06-SPEC.md ownership contract; installed crispy BasicNode.get_render/get_response_dict, FormActions.render and FormHelper.get_attributes; src/crud_views/lib/formsets/layout.py; src/crud_views/templatetags/crud_views_formsets.py; src/crud_views/templates/crud_views/formsets/formsets.html; src/crud_views/templates/crud_views/formsets/formset.html; Django InclusionNode.render; tests/test1/test_crispy_buttons.py&lt;/read_first&gt; | `.venv/lib/python3.12/site-packages/crispy_forms/bootstrap.py:306` | `.planning/phases/06-form-button-leaf/06-03-PLAN.md:97`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:107` |
| `FormData` | UNCHECKABLE | jsdom native SubmitEvent/FormData requires acceptance on the reconciled locked environment. The expanded | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:181`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:27`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:36`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:74`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:80`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:84`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:135`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:152`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:164`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:192` |
| `FormHelper` | UNCHECKABLE | and its prepared Layout truthy before crispy evaluates &#96;if helper and helper.layout&#96;. FormHelper inherits | `.venv/lib/python3.12/site-packages/crispy_forms/helper.py:106` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:160`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:97`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:73`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:82` |
| `FormHelper.get_attributes` | UNCHECKABLE | &lt;read_first&gt;06-SPEC.md ownership contract; installed crispy BasicNode.get_render/get_response_dict, FormActions.render and FormHelper.get_attributes; src/crud_views/lib/formsets/layout.py; src/crud_views/templatetags/crud_views_formsets.py; src/crud_views/templates/crud_views/formsets/formsets.html; src/crud_views/templates/crud_views/formsets/formset.html; Django InclusionNode.render; tests/test1/test_crispy_buttons.py&lt;/read_first&gt; | `.venv/lib/python3.12/site-packages/crispy_forms/helper.py:290` | `.planning/phases/06-form-button-leaf/06-03-PLAN.md:97`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:73` |
| `Formsets` | UNCHECKABLE | For L-FORMSET-PAGE-CONTEXT, capture only the genuine page-owner fallback before Formsets.render flattens | `src/crud_views/lib/formsets/layout.py:7` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:147`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:151`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:68`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:109`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:110`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:157`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:69` |
| `Formsets.render` | UNCHECKABLE | For L-FORMSET-PAGE-CONTEXT, capture only the genuine page-owner fallback before Formsets.render flattens | `src/crud_views/lib/formsets/layout.py:10` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:147`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:109` |
| `HomePageTest` | UNCHECKABLE | &lt;read_first&gt;examples/bootstrap5/project/settings.py; examples/bootstrap5/pytest.ini; examples/bootstrap5/test_i18n.py; examples/bootstrap5/project/tests.py (HomePageTest and SystemChecksTest); examples/bootstrap5/test_doc_links.py; docs/migrating-1.0.md Form buttons; 06-07-SUMMARY.md; 06-08-SUMMARY.md; 06-VALIDATION.md&lt;/read_first&gt; | `examples/bootstrap5/project/tests.py:34` | `.planning/phases/06-form-button-leaf/06-09-PLAN.md:82`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:85`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:245` |
| `HomePageTest.test_every_feature_landing_page_renders` | UNCHECKABLE | For L-EXAMPLE-COVERAGE, run the separate example-consumer gate below from examples/bootstrap5 so its pytest.ini selects project.settings: all test_i18n.py cases (including test_demo_pages_render_german and its translated create-submit value), HomePageTest.test_every_feature_landing_page_renders, and all test_doc_links.py reference/backlink cases. Record their collected counts and results after 06-08 enables form=both. Root pytest tests does not include this example tree; SystemChecksTest and test_docs_sync alone cannot substitute. Retain those two existing gates as independent evidence. A failure is an acceptance blocker to route to the producing implementation/docs plan, not grounds to remove or relax the affected assertion. | `examples/bootstrap5/project/tests.py:45` | `.planning/phases/06-form-button-leaf/06-09-PLAN.md:85` |
| `InclusionNode.context.new` | UNCHECKABLE | Test the actual outer crispy Layout(Formsets()) -&gt; formsets.html -&gt; cv_x_formset -&gt; formset.html -&gt; row crispy path, plus a recursive child formset and standalone cv_x_formset entry. Direct inclusion of formset.html with injected view is not acceptance evidence. For ownerless/current-helper-None rows assert genuine page P survives both context.flatten and InclusionNode.context.new, including P distinct from enclosing helper H. Test no page/ordinary/falsey page and row/helper overrides, two independent formsets with different pages, and repeated/exceptional renders with unchanged caller Context. Assert no warnings for D-12 and no mutation after repeated/interleaved renders. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-03-PLAN.md:110` |
| `InclusionNode.render` | UNCHECKABLE | &lt;read_first&gt;06-SPEC.md ownership contract; installed crispy BasicNode.get_render/get_response_dict, FormActions.render and FormHelper.get_attributes; src/crud_views/lib/formsets/layout.py; src/crud_views/templatetags/crud_views_formsets.py; src/crud_views/templates/crud_views/formsets/formsets.html; src/crud_views/templates/crud_views/formsets/formset.html; Django InclusionNode.render; tests/test1/test_crispy_buttons.py&lt;/read_first&gt; | `.venv/lib/python3.12/site-packages/django/template/library.py:355` | `.planning/phases/06-form-button-leaf/06-03-PLAN.md:97` |
| `LABEL_MODE_DEFAULTS` | UNCHECKABLE | Update test_label_mode.py and test_button_data.py location/default assertions in this producing task, preserving set(LABEL_MODE_DEFAULTS) == LOCATIONS, before running the tracer shard. | `src/crud_views/lib/view/label_mode.py:23` | `.planning/phases/06-form-button-leaf/06-02-PLAN.md:95`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:96` |
| `LEAF_KEYS` | UNCHECKABLE | 06-02 through 06-06. Set separate FORM_LEAF_KEYS, preserving LEAF_KEYS; define type/name/value/id/key, | `src/crud_views/lib/view/button_data.py:16` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:116`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:98` |
| `Layout` | UNCHECKABLE | and its prepared Layout truthy before crispy evaluates &#96;if helper and helper.layout&#96;. FormHelper inherits | `.venv/lib/python3.12/site-packages/crispy_forms/layout.py:108` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:160`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:161`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:162`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:168`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:88`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:110`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:28`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:82`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:83`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:103`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:108`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:130` |
| `ListViewFilterFormHelper` | UNCHECKABLE | ListViewFilterFormHelper.__bool__ returning True plus the private truthy prepared Layout; retain ordinary | `src/crud_views/lib/views/list.py:57` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:162`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:67`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:82`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:83`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:101`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:102` |
| `ListViewFilterFormHelper.__bool__` | EXCLUDED_NEW | ListViewFilterFormHelper.__bool__ returning True plus the private truthy prepared Layout; retain ordinary | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:162`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:82` |
| `ListViewFilterFormHelper.get_attributes` | EXCLUDED_NEW | For M-EMPTY-REPLACEMENT, prepare the current layout in a ListViewFilterFormHelper.get_attributes override before delegating to super: BasicNode.get_response_dict calls this method before get_render evaluates helper truthiness followed by layout truthiness. Detect a caller replacement by identity against the prepared instance, deep-copy it, and normalize an explicitly empty Layout to a private truthy instance layout preserving its empty field selection; appending actions remains render_layout&#x27;s job. Track the genuine no-layout/default-fields case separately so an explicit Layout() never resurrects constructor or inferred fields. The same idempotent preparation helper may serve direct render_layout calls, but replacement detection solely inside render_layout is insufficient. Repeated get_attributes calls must not replace a prepared layout or append actions. Preserve selected nested/custom layout nodes and order while isolating them, and tie exactly-once state to the prepared replacement identity, not a helper lifetime flag. This stays inside the package helper; no crispy monkeypatch, global template override or caller constructor change is involved. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-05-PLAN.md:83` |
| `ListViewFilterFormHelper.get_form_actions` | EXCLUDED_NEW | NEW public method: ListViewFilterFormHelper.get_form_actions() -&gt; FormActions &#124; None. NEW __bool__, get_attributes and render_layout overrides with private instance layout/action initialization state. No new test files; only existing phase-owned filter golden changes. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-05-PLAN.md:67` |
| `ListViewTableFilterMixin` | UNCHECKABLE | Add get_form_actions following the spec. Initialize FormHelper without passing form when preserving declared layout; deep-copy declared layout per instance, and retain helper.form as the identical explicit form argument when supplied, preserving upstream association without rebuilding its fields (M-HELPER-STATE). Make ListViewFilterFormHelper.__bool__ return True independently of its inherited __len__, AND keep a truthy prepared instance layout before crispy dispatch even for no-layout or None actions (private Layout subclass __bool__ returning True). Both terms of &#96;if helper and helper.layout&#96; must pass; a layout-only fix is insufficient. Preserve len(helper) as the actual layout field count, use identity/is-None checks for owner resolution, and do not alter upstream or unrelated helper classes. All new lifecycle/owner state uses underscore-prefixed attributes so get_attributes does not publish it. Populate no-layout fields from the actual form at render_layout before appending the action group. Preserve the helper&#x27;s configured layout field order. Build Apply/Reset as package adapters with form:filter-submit/form:filter-reset and original IDs, append exactly once to the isolated layout. Keep Hidden controls on inputs with current GET naming/value logic. During render_layout push the actual helper owner under a private context key so adapters need not inspect a fresh form.helper property; restore context afterward. Keep ListViewTableFilterMixin construction unchanged. | `src/crud_views/lib/views/mixins.py:299` | `.planning/phases/06-form-button-leaf/06-05-PLAN.md:82` |
| `PATTERNS.md` | UNCHECKABLE | @.planning/phases/06-form-button-leaf/06-PATTERNS.md | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:60`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:72`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:61`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:61`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:60`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:63`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:58`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:69`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:54` |
| `PROJECT.md` | UNCHECKABLE | @.planning/PROJECT.md | `.planning/PROJECT.md:1` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:54`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:67`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:56`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:56`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:55`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:58`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:53`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:64`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:49` |
| `REQUIREMENTS.md` | UNCHECKABLE | @.planning/REQUIREMENTS.md | `.planning/REQUIREMENTS.md:1` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:57` |
| `RESEARCH.md` | UNCHECKABLE | @.planning/phases/06-form-button-leaf/06-RESEARCH.md | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:59`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:71`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:60`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:60`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:59`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:62`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:57`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:71`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:113`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:68`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:53` |
| `ROADMAP.md` | UNCHECKABLE | @.planning/ROADMAP.md | `.planning/ROADMAP.md:1` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:55`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:275`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:68`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:57`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:57`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:56`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:59`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:54`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:65`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:50` |
| `RUNTIME.json` | UNCHECKABLE | - .planning/phases/06-form-button-leaf/06-JS-RUNTIME.json | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:10`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:69`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:77`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:102`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:65` |
| `SPEC.md` | UNCHECKABLE | - .planning/phases/06-form-button-leaf/06-SPEC.md | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:8`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:31`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:66`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:77`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:189`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:199`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:226`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:73`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:62`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:74`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:97`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:62`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:61`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:73`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:64`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:103`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:59`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:70`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:82`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:55`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:67` |
| `STATE.md` | UNCHECKABLE | @.planning/STATE.md | `.planning/STATE.md:1` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:56`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:69`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:58`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:58`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:57`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:60`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:55`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:66`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:51` |
| `SUMMARY.md` | UNCHECKABLE | Create .planning/phases/06-form-button-leaf/06-01-SUMMARY.md with prerequisite and baseline commit evidence. | `.planning/research/SUMMARY.md:1` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:316`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:86`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:136`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:186`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:176`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:147`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:177`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:188`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:160`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:179`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:67`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:82`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:294` |
| `SafeData` | UNCHECKABLE | Normalize text to a plain str that has no SafeData trust marker before exactly one Django escaping boundary; | `.venv/lib/python3.12/site-packages/django/utils/safestring.py:13` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:118`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:99` |
| `SafeString` | UNCHECKABLE | - &quot;D-15: Empty, Unicode, lazy, SafeString and template-looking values remain exact literal DOM text and values; none evaluates template syntax or creates injected nodes/attributes.&quot; | `.venv/lib/python3.12/site-packages/django/utils/safestring.py:25` | `.planning/phases/06-form-button-leaf/06-02-PLAN.md:37`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:116`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:122`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:177`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:159`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:194` |
| `SubmitEvent` | UNCHECKABLE | jsdom native SubmitEvent/FormData requires acceptance on the reconciled locked environment. The expanded | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:181`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:27`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:36`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:73`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:80`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:164` |
| `SubmitEvent.submitter` | UNCHECKABLE | - &quot;The native SubmitEvent.submitter and FormData contract is tested on exact locked JS packages under a compatible isolated runtime, without hiding failure through mocks/polyfills.&quot; | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-07-PLAN.md:27`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:73` |
| `SystemChecksTest` | UNCHECKABLE | &lt;read_first&gt;examples/bootstrap5/project/settings.py; examples/bootstrap5/pytest.ini; examples/bootstrap5/test_i18n.py; examples/bootstrap5/project/tests.py (HomePageTest and SystemChecksTest); examples/bootstrap5/test_doc_links.py; docs/migrating-1.0.md Form buttons; 06-07-SUMMARY.md; 06-08-SUMMARY.md; 06-VALIDATION.md&lt;/read_first&gt; | `examples/bootstrap5/project/tests.py:97` | `.planning/phases/06-form-button-leaf/06-09-PLAN.md:82`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:85`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:237`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:256`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:271` |
| `TemplateNameMixin` | UNCHECKABLE | &lt;read_first&gt;The spec literal/attribute rules; crispy BaseInput and TemplateNameMixin in the declared-floor environment; tests/test1/test_button_leaves.py&lt;/read_first&gt; | `.venv/lib/python3.12/site-packages/crispy_forms/layout.py:18` | `.planning/phases/06-form-button-leaf/06-02-PLAN.md:112` |
| `VALIDATION.md` | UNCHECKABLE | @.planning/phases/06-form-button-leaf/06-VALIDATION.md | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:61`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:9`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:27`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:33`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:61`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:66`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:67`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:81`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:82` |
| `VARIANT_LOCATIONS` | UNCHECKABLE | VARIANT_LOCATIONS. Before authoring the spec, run .venv/bin/pytest tests/test1/test_label_mode.py | `src/crud_views/lib/button_classes.py:209` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:90`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:96`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:97` |
| `ValueError` | UNCHECKABLE | Branch cv_button_data early for form before action URL/modal derivation; retain existing action behavior and LEAF_KEYS. Introduce FORM_LEAF_KEYS for the exact spec contract. Validate cv_key against FORM_KINDS and cv_type against submit/button/reset; invalid caller kind/type raises ValueError. Explicitly reject non-form and unknown slot kinds when rendering through the new layout leaf; preserve arbitrary slot handling on legacy helper.inputs without constructor-time rejection or warnings (M-SLOT, D-01/D-02/D-13). Cover formset:control and form:unknown as rejected layout slots and retained legacy input cases; 06-08 records this layout-only Breaking change. Missing or None textual values normalize to empty text without coercing other falsey data such as numeric zero to empty. Preserve valid empty labels without manufacturing text. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-02-PLAN.md:98`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:27`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:118`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:119`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:117` |
| `ViewSet` | UNCHECKABLE | - &quot;D-13: Form mode maps select view, else ViewSet, else setting as whole maps; an empty selected map and missing kind fall directly to the live form floor.&quot; | `src/crud_views/lib/viewset/__init__.py:45` | `.planning/phases/06-form-button-leaf/06-03-PLAN.md:25`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:68`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:76`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:90`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:82`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:84`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:89`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:96`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:84`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:86`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:208` |
| `ViewSet.form_actions_label_mode` | EXCLUDED_NEW | NEW fields: CrudViewsSettings.form_actions_label_mode (CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE), ViewSet.form_actions_label_mode, CrudView.cv_form_actions_label_mode. NEW public resolver: CrudView.cv_get_form_actions_label_mode(). Existing cv_get_action_label_mode gains location=&#x27;form&#x27;. Private owner-recovery helpers and a scoped page-owner transport key across Formsets/cv_x_formset are internal, not promised public names or leaf-context keys. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-03-PLAN.md:68` |
| `ViewSets` | UNCHECKABLE | &lt;fails_when&gt;The URLconf does not register feature ViewSets, the registered example reports system-check errors, or the test fails to start; bare manage.py check alone is insufficient.&lt;/fails_when&gt; | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-09-PLAN.md:238`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:256` |
| `WorkflowForm.submit_icon` | EXCLUDED_NEW | EXISTING prerequisites from 06-02: form:hidden-label and form:icon-host with updated exhaustive keys/count. NEW registry names: save, cancel, filter-reset. NEW form attributes: CrispyFormMixin.submit_icon=&#x27;save&#x27;, CrispyDeleteForm.delete_icon=&#x27;delete&#x27;, WorkflowForm.submit_icon=&#x27;workflow&#x27;. NEW adapter icon= keyword is consumed as rendering configuration, never serialized as an HTML attribute; omission selects kind default while explicit None/empty suppresses it. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-04-PLAN.md:68` |
| `__bool__` | UNCHECKABLE | ListViewFilterFormHelper.__bool__ returning True plus the private truthy prepared Layout; retain ordinary | `tests/test1/test_assets.py:132` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:162`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:67`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:82` |
| `__len__` | UNCHECKABLE | __len__ returning len(layout.fields), so a truthy Layout alone cannot admit an empty helper. Specify a | `.venv/lib/python3.12/site-packages/crispy_forms/helper.py:99`<br>`.venv/lib/python3.12/site-packages/crispy_forms/layout.py:38`<br>`src/crud_views/lib/pipeline.py:101` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:161`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:82` |
| `_get_renderers` | UNCHECKABLE | Resolve form mode through the public resolver; catch ValueError only around mode resolution so E108/E210/E211 survive strict checking. For M-REGISTRY-OFF and M-ICON-AVAILABILITY, use the existing icons.resolve_icon(value) in both static inspection and the form normalizer: a None result means an absent/disabled semantic mapping, including explicit None/empty and a semantic name mapped by CRUD_VIEWS_ICONS to None/empty. Test each with known default submit/delete/filter controls. For L-UNREGISTERED-FORM-ICON, semantic resolution alone is insufficient: a nonempty prefix must also have a dict-valued library entry and a usable registered renderer. Add a private side-effect-free availability helper in icons.py reusing resolve_icon/get_libraries/_get_renderers metadata; resolving a renderer callable is allowed, invoking it is not. Share this predicate between form static checks and the normalizer. A resolved empty prefix is the existing raw CSS-class path and remains available. A direct submit_icon=&#x27;unknown:save&#x27; must trigger W292 for static icon-only controls and the same strict ValueError/non-strict logged label fallback as disabled semantic icons at runtime. Registry W352 only visits table entries, so do not claim it covers direct per-form values. Preserve existing registry diagnostics for malformed libraries and named entries; do not change their IDs or silently suppress them. Never call render_icon or a custom renderer to probe availability. Leave actual inline rendering to the leaf&#x27;s one cv_icon call; no rendered-markup cache or extra public leaf key is needed. A custom renderer&#x27;s returned markup remains its existing renderer contract, not a second missing-mapping test. Preserve icon_host_keys/resolve_icon_name_class for placement: a valid host icon is available even though the leaf emits no inline element, and a None/empty form:icon-host class override remains the existing explicit placement opt-out rather than a missing semantic icon. | `src/crud_views/lib/icons.py:164` | `.planning/phases/06-form-button-leaf/06-06-PLAN.md:118` |
| `action_menus` | UNCHECKABLE | - docs/reference/action_menus.md | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-08-PLAN.md:10`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:45`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:81`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:82`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:84`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:86` |
| `action_menus.md` | UNCHECKABLE | - docs/reference/action_menus.md | `docs/reference/action_menus.md:1` | `.planning/phases/06-form-button-leaf/06-08-PLAN.md:10`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:45`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:81`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:82`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:84` |
| `add_input` | UNCHECKABLE | - &quot;D-01, D-02: Custom add_input controls remain legacy inputs quietly; hidden sort/order/direction inputs keep their current path and values.&quot; | `.venv/lib/python3.12/site-packages/crispy_forms/helper.py:260` | `.planning/phases/06-form-button-leaf/06-05-PLAN.md:22`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:104`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:107`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:101`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:117` |
| `assumption_delta_decision` | UNCHECKABLE | &lt;assumption_delta_decision&gt; | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:245`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:250` |
| `button.name` | UNCHECKABLE | Extend the existing modal suite using native SubmitEvent and native FormData, real button elements with nested icon/text, multiple submitters, no submitter, confirm=true plus delete=Delete and literal malicious/Unicode values. Assert actual FormData(form, button).get(button.name) and preserved hidden confirmation/CSRF values; sibling submitter fields must be absent. Fetch may be spied to inspect its FormData, but do not replace browser constructors or fake submitter support. Change modal.js only if a demonstrated regression requires it; keep its current error, CSRF and authorization interactions. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-07-PLAN.md:80` |
| `button_data.py` | UNCHECKABLE | src/crud_views/lib/view/button_data.py; src/crud_views/lib/view/label_mode.py; | `src/crud_views/lib/view/button_data.py:1` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:83`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:8`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:45`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:49`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:51`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:79`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:85`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:86`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:111`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:15`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:43`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:102`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:103` |
| `buttons.md` | UNCHECKABLE | - docs/reference/buttons.md | `docs/reference/buttons.md:1` | `.planning/phases/06-form-button-leaf/06-02-PLAN.md:11`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:85`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:97`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:8`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:81`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:82` |
| `check_viewsets` | UNCHECKABLE | - &quot;Empty and non-ASCII invalid keys/values yield deterministic diagnostics; malformed floor/map errors survive check_viewsets and are never hidden by W292.&quot; | `src/crud_views/checks.py:20` | `.planning/phases/06-form-button-leaf/06-06-PLAN.md:29`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:80`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:90` |
| `context.flatten` | UNCHECKABLE | Test the actual outer crispy Layout(Formsets()) -&gt; formsets.html -&gt; cv_x_formset -&gt; formset.html -&gt; row crispy path, plus a recursive child formset and standalone cv_x_formset entry. Direct inclusion of formset.html with injected view is not acceptance evidence. For ownerless/current-helper-None rows assert genuine page P survives both context.flatten and InclusionNode.context.new, including P distinct from enclosing helper H. Test no page/ordinary/falsey page and row/helper overrides, two independent formsets with different pages, and repeated/exceptional renders with unchanged caller Context. Assert no warnings for D-12 and no mutation after repeated/interleaved renders. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-03-PLAN.md:110` |
| `context.new` | UNCHECKABLE | Test the actual outer crispy Layout(Formsets()) -&gt; formsets.html -&gt; cv_x_formset -&gt; formset.html -&gt; row crispy path, plus a recursive child formset and standalone cv_x_formset entry. Direct inclusion of formset.html with injected view is not acceptance evidence. For ownerless/current-helper-None rows assert genuine page P survives both context.flatten and InclusionNode.context.new, including P distinct from enclosing helper H. Test no page/ordinary/falsey page and row/helper overrides, two independent formsets with different pages, and repeated/exceptional renders with unchanged caller Context. Assert no warnings for D-12 and no mutation after repeated/interleaved renders. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-03-PLAN.md:110` |
| `context.push` | UNCHECKABLE | helper. Package filter helper render_layout supplies a private helper-owner context entry using context.push | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:137` |
| `crispy_floor` | EXCLUDED_NEW | NEW nox session: crispy_floor, Python 3.12 with Django 4.2 and 6.0 variants and exact crispy 2.0/bootstrap5 2023.10 pins. Existing JS source files are conditional bug-fix ownership only; leave them byte-identical if the new regression tests pass. Runtime prerequisites: 06-01 task 1 creates 06-js-verify.sh and 06-JS-RUNTIME.json before per-wave JS sampling; every JS command below reasserts that selected runtime and exact lock-backed environment, including in fresh shells. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-07-PLAN.md:65`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:115`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:118`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:157` |
| `crud_views_settings` | UNCHECKABLE | settings.py is initialized and the existing crud_views_settings singleton serves map reads, like context/list. | `src/crud_views/lib/settings.py:320` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:154`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:79`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:83`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:84`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:85` |
| `css_class` | UNCHECKABLE | otherwise extra id wins over generated id; class-table classes then css_class then extra class are appended | `.venv/lib/python3.12/site-packages/crispy_forms/bootstrap.py:599`<br>`.venv/lib/python3.12/site-packages/crispy_forms/bootstrap.py:714`<br>`.venv/lib/python3.12/site-packages/crispy_forms/bootstrap.py:949`<br>`.venv/lib/python3.12/site-packages/crispy_forms/layout.py:732`<br>`.venv/lib/python3.12/site-packages/crispy_forms/templatetags/crispy_forms_field.py:103`<br>`.venv/lib/python3.12/site-packages/crispy_forms/templatetags/crispy_forms_field.py:108`<br>`.venv/lib/python3.12/site-packages/crispy_forms/templatetags/crispy_forms_field.py:61`<br>`src/crud_views/lib/crispy/table.py:13` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:126` |
| `css_id` | UNCHECKABLE | css_id wins over extra id, | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:125` |
| `cv_button_class` | UNCHECKABLE | Implement adapter render without calling BaseInput.render: retain raw value and kwargs, normalize per spec, render the selected leaf through a scoped context copy. Strip inherited input aliases from the template context, never expose the adapter object. Normalize SafeData and lazy values at render time to ordinary strings then use Django autoescaping once; serialized extra attrs are escaped once separately. Preserve constructor signature, slot-selected semantic kind, upstream generated IDs and legacy field_classes/flat_attrs for helper.inputs. Do not infer kind from the submitted name. The leaf uses cv_button_class form/cv_key/cv_label_mode, appends cv_css_class and host classes, and renders the three bodies with cancel URL only for cancel. Keep normalizer/icon behavior extensible for 06-04 rather than hardcoding a temporary floor. Update existing input-only assertions only where layout buttons changed; filter helper inputs remain inputs until 06-05. | `src/crud_views/templatetags/crud_views.py:525`<br>`src/crud_views_object_detail/templatetags/crud_views_object_detail.py:108` | `.planning/phases/06-form-button-leaf/06-02-PLAN.md:99`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:83` |
| `cv_button_data` | UNCHECKABLE | - &quot;D-13, D-14: A standalone package Submit renders a real button through cv_button_data(ctx, &#x27;form&#x27;), with label as the lazy form floor and finite kind semantics.&quot; | `src/crud_views/lib/view/button_data.py:52` | `.planning/phases/06-form-button-leaf/06-02-PLAN.md:36`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:98`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:119` |
| `cv_cancel_url` | EXCLUDED_NEW | NEW template: src/crud_views/templates/crud_views/tags/button/form.html. NEW symbol: FORM_LEAF_KEYS in button_data.py. NEW normalized fields: cv_type, cv_name, cv_value, cv_id, cancel-only cv_cancel_url, cv_css_class, cv_flat_attrs; existing label/icon fields are reused. NEW class utility defaults: form:hidden-label and form:icon-host, with exhaustive key/count documentation updated in their producing task. Private helper names are implementation-local. No new external package. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-02-PLAN.md:79` |
| `cv_css_class` | EXCLUDED_NEW | literal strings, cancel-only URL, mode/icon fields, cv_css_class suffix and cv_flat_attrs serialization. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:117`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:79`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:99`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:84` |
| `cv_first_inline_keys` | UNCHECKABLE | via: cv_first_inline_keys selects one map | `src/crud_views/lib/view/base.py:263` | `.planning/phases/06-form-button-leaf/06-03-PLAN.md:42`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:74`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:83` |
| `cv_flat_attrs` | EXCLUDED_NEW | literal strings, cancel-only URL, mode/icon fields, cv_css_class suffix and cv_flat_attrs serialization. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:117`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:79`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:84`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:101` |
| `cv_form_actions_label_mode` | EXCLUDED_NEW | NEW fields: CrudViewsSettings.form_actions_label_mode (CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE), ViewSet.form_actions_label_mode, CrudView.cv_form_actions_label_mode. NEW public resolver: CrudView.cv_get_form_actions_label_mode(). Existing cv_get_action_label_mode gains location=&#x27;form&#x27;. Private owner-recovery helpers and a scoped page-owner transport key across Formsets/cv_x_formset are internal, not promised public names or leaf-context keys. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-03-PLAN.md:68`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:85`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:88`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:89` |
| `cv_form_icon_mode_checks` | EXCLUDED_NEW | NEW test file: tests/test1/test_form_button_checks.py. NEW private/static form icon checker in view/buttons.py (suggested cv_form_icon_mode_checks). No new check IDs. Finite form contract tests live in this file or existing test_button_data.py read-only coverage; no new generic diagnostic framework. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-06-PLAN.md:70` |
| `cv_get_action_label_mode` | UNCHECKABLE | NEW fields: CrudViewsSettings.form_actions_label_mode (CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE), ViewSet.form_actions_label_mode, CrudView.cv_form_actions_label_mode. NEW public resolver: CrudView.cv_get_form_actions_label_mode(). Existing cv_get_action_label_mode gains location=&#x27;form&#x27;. Private owner-recovery helpers and a scoped page-owner transport key across Formsets/cv_x_formset are internal, not promised public names or leaf-context keys. | `src/crud_views/lib/view/base.py:299` | `.planning/phases/06-form-button-leaf/06-03-PLAN.md:68`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:74`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:83` |
| `cv_get_form_actions_label_mode` | EXCLUDED_NEW | NEW fields: CrudViewsSettings.form_actions_label_mode (CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE), ViewSet.form_actions_label_mode, CrudView.cv_form_actions_label_mode. NEW public resolver: CrudView.cv_get_form_actions_label_mode(). Existing cv_get_action_label_mode gains location=&#x27;form&#x27;. Private owner-recovery helpers and a scoped page-owner transport key across Formsets/cv_x_formset are internal, not promised public names or leaf-context keys. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-03-PLAN.md:68`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:83` |
| `cv_icon` | UNCHECKABLE | Resolve form mode through the public resolver; catch ValueError only around mode resolution so E108/E210/E211 survive strict checking. For M-REGISTRY-OFF and M-ICON-AVAILABILITY, use the existing icons.resolve_icon(value) in both static inspection and the form normalizer: a None result means an absent/disabled semantic mapping, including explicit None/empty and a semantic name mapped by CRUD_VIEWS_ICONS to None/empty. Test each with known default submit/delete/filter controls. For L-UNREGISTERED-FORM-ICON, semantic resolution alone is insufficient: a nonempty prefix must also have a dict-valued library entry and a usable registered renderer. Add a private side-effect-free availability helper in icons.py reusing resolve_icon/get_libraries/_get_renderers metadata; resolving a renderer callable is allowed, invoking it is not. Share this predicate between form static checks and the normalizer. A resolved empty prefix is the existing raw CSS-class path and remains available. A direct submit_icon=&#x27;unknown:save&#x27; must trigger W292 for static icon-only controls and the same strict ValueError/non-strict logged label fallback as disabled semantic icons at runtime. Registry W352 only visits table entries, so do not claim it covers direct per-form values. Preserve existing registry diagnostics for malformed libraries and named entries; do not change their IDs or silently suppress them. Never call render_icon or a custom renderer to probe availability. Leave actual inline rendering to the leaf&#x27;s one cv_icon call; no rendered-markup cache or extra public leaf key is needed. A custom renderer&#x27;s returned markup remains its existing renderer contract, not a second missing-mapping test. Preserve icon_host_keys/resolve_icon_name_class for placement: a valid host icon is available even though the leaf emits no inline element, and a None/empty form:icon-host class override remains the existing explicit placement opt-out rather than a missing semantic icon. | `src/crud_views/templatetags/crud_views.py:513`<br>`src/crud_views_object_detail/templatetags/crud_views_object_detail.py:102` | `.planning/phases/06-form-button-leaf/06-06-PLAN.md:118` |
| `cv_icon_inline` | UNCHECKABLE | In test_form_button_checks.py register a counting custom inline renderer using existing registry override fixtures and render a real package Submit in icon, both and label modes. Assert one call and one emitted marker for each icon/both render, zero calls for label/static checks, and fresh output for a second render; disabled semantic mappings make zero renderer calls and still raise/log-and-label as required. Add real host-library form renders under strict and non-strict settings with default and None/empty form:icon-host overrides: assert expected host classes or their intentional absence, cv_icon_inline=False, no inline element/render invocation and no false W292/log/exception. Separately disable the host&#x27;s semantic mapping and require the same strict/non-strict missing-icon behavior as inline mappings. Add a direct per-form unknown-prefix case (absent from the semantic table), and a registered prefix with unusable renderer, in static and custom-hook runtime paths. Assert W292/strict/logged accessible label fallback and zero renderer calls; retain raw unprefixed class, valid inline custom renderer and host opt-out controls as positive cases. A custom renderer that is callable but returns empty markup remains the explicitly documented renderer contract, not a reason to invoke it twice. These cases preserve D-14 host semantics while proving D-16 diagnostics without duplicate side effects. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-06-PLAN.md:120` |
| `cv_icon_mode_checks` | UNCHECKABLE | &lt;read_first&gt;src/crud_views/lib/view/buttons.py (cv_icon_mode_checks); src/crud_views/lib/crispy/form.py; src/crud_views/lib/views/list.py; src/crud_views/lib/view/button_data.py; src/crud_views/lib/icons.py (resolve_icon/render_icon/resolve_icon_name_class); tests/test1/test_icon_host_leaves.py; 06-SPEC.md static-check reach&lt;/read_first&gt; | `src/crud_views/lib/view/buttons.py:387` | `.planning/phases/06-form-button-leaf/06-06-PLAN.md:103` |
| `cv_id` | EXCLUDED_NEW | NEW template: src/crud_views/templates/crud_views/tags/button/form.html. NEW symbol: FORM_LEAF_KEYS in button_data.py. NEW normalized fields: cv_type, cv_name, cv_value, cv_id, cancel-only cv_cancel_url, cv_css_class, cv_flat_attrs; existing label/icon fields are reused. NEW class utility defaults: form:hidden-label and form:icon-host, with exhaustive key/count documentation updated in their producing task. Private helper names are implementation-local. No new external package. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-02-PLAN.md:79` |
| `cv_key` | UNCHECKABLE | Branch cv_button_data early for form before action URL/modal derivation; retain existing action behavior and LEAF_KEYS. Introduce FORM_LEAF_KEYS for the exact spec contract. Validate cv_key against FORM_KINDS and cv_type against submit/button/reset; invalid caller kind/type raises ValueError. Explicitly reject non-form and unknown slot kinds when rendering through the new layout leaf; preserve arbitrary slot handling on legacy helper.inputs without constructor-time rejection or warnings (M-SLOT, D-01/D-02/D-13). Cover formset:control and form:unknown as rejected layout slots and retained legacy input cases; 06-08 records this layout-only Breaking change. Missing or None textual values normalize to empty text without coercing other falsey data such as numeric zero to empty. Preserve valid empty labels without manufacturing text. | `examples/bootstrap5/action_menus/views.py:114`<br>`examples/bootstrap5/action_menus/views.py:132`<br>`examples/bootstrap5/resources/views.py:112`<br>`examples/bootstrap5/resources/views.py:94`<br>`examples/bootstrap5/showcase/views.py:122`<br>`src/crud_views/lib/view/base.py:67`<br>`src/crud_views/lib/views/action_ordered.py:19`<br>`src/crud_views/lib/views/action_ordered.py:47` | `.planning/phases/06-form-button-leaf/06-02-PLAN.md:98`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:99` |
| `cv_label_mode` | UNCHECKABLE | Implement adapter render without calling BaseInput.render: retain raw value and kwargs, normalize per spec, render the selected leaf through a scoped context copy. Strip inherited input aliases from the template context, never expose the adapter object. Normalize SafeData and lazy values at render time to ordinary strings then use Django autoescaping once; serialized extra attrs are escaped once separately. Preserve constructor signature, slot-selected semantic kind, upstream generated IDs and legacy field_classes/flat_attrs for helper.inputs. Do not infer kind from the submitted name. The leaf uses cv_button_class form/cv_key/cv_label_mode, appends cv_css_class and host classes, and renders the three bodies with cancel URL only for cancel. Keep normalizer/icon behavior extensible for 06-04 rather than hardcoding a temporary floor. Update existing input-only assertions only where layout buttons changed; filter helper inputs remain inputs until 06-05. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-02-PLAN.md:99` |
| `cv_label_mode_checks` | UNCHECKABLE | Addresses H-DIAGNOSTIC-CONTRACT with an explicit form-only policy: retain context/list cv_label_mode_checks exactly (E211 for any malformed map including invalid values, W291 only on the own view attribute). For the finite form map, deliberately distinguish shape from individual modes so D-16&#x27;s E210 extension has a concrete scope without adding a scalar API: non-dict or non-string keys yield one E211 and stop entry traversal; a string-keyed dict yields one E210 per invalid mode value in insertion order; unknown form keys with valid modes yield W291 on the view&#x27;s own cv_form_actions_label_mode only, naming sorted FORM_KINDS. None and {} are valid. This documented form-specific diagnostic distinction does not alter FORM-11 whole-map resolution semantics. Do not blindly invoke the old helper unchanged or change its behavior for context/list. | `src/crud_views/lib/view/action_menu.py:46` | `.planning/phases/06-form-button-leaf/06-06-PLAN.md:88` |
| `cv_name` | EXCLUDED_NEW | NEW template: src/crud_views/templates/crud_views/tags/button/form.html. NEW symbol: FORM_LEAF_KEYS in button_data.py. NEW normalized fields: cv_type, cv_name, cv_value, cv_id, cancel-only cv_cancel_url, cv_css_class, cv_flat_attrs; existing label/icon fields are reused. NEW class utility defaults: form:hidden-label and form:icon-host, with exhaustive key/count documentation updated in their producing task. Private helper names are implementation-local. No new external package. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-02-PLAN.md:79`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:122` |
| `cv_type` | EXCLUDED_NEW | NEW template: src/crud_views/templates/crud_views/tags/button/form.html. NEW symbol: FORM_LEAF_KEYS in button_data.py. NEW normalized fields: cv_type, cv_name, cv_value, cv_id, cancel-only cv_cancel_url, cv_css_class, cv_flat_attrs; existing label/icon fields are reused. NEW class utility defaults: form:hidden-label and form:icon-host, with exhaustive key/count documentation updated in their producing task. Private helper names are implementation-local. No new external package. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-02-PLAN.md:79`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:98` |
| `cv_value` | EXCLUDED_NEW | NEW template: src/crud_views/templates/crud_views/tags/button/form.html. NEW symbol: FORM_LEAF_KEYS in button_data.py. NEW normalized fields: cv_type, cv_name, cv_value, cv_id, cancel-only cv_cancel_url, cv_css_class, cv_flat_attrs; existing label/icon fields are reused. NEW class utility defaults: form:hidden-label and form:icon-host, with exhaustive key/count documentation updated in their producing task. Private helper names are implementation-local. No new external package. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-02-PLAN.md:79`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:101` |
| `cv_view` | UNCHECKABLE | argument&#x27;s cv_view first, never an outer context form; current helper view | `src/crud_views/lib/formsets/formsets.py:265`<br>`src/crud_views/lib/formsets/formsets.py:36` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:134`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:146`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:99`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:104`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:107`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:108` |
| `cv_x_formset` | UNCHECKABLE | Context, transport it in a private Python context key through cv_x_formset and recursive child inclusions, | `src/crud_views/templatetags/crud_views_formsets.py:7` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:148`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:151`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:68`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:109`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:110` |
| `data_cv_cancel_url` | UNCHECKABLE | once; data_cv_cancel_url/data-cv-cancel-url become one cancel-only URL; generated icon-mode title and tooltip | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:127` |
| `default_label_mode` | UNCHECKABLE | contracts at that HEAD: default_label_mode with shared lazy defaults and independent FORM_KINDS / | `src/crud_views/lib/view/label_mode.py:84` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:89`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:83` |
| `delete_icon` | EXCLUDED_NEW | EXISTING prerequisites from 06-02: form:hidden-label and form:icon-host with updated exhaustive keys/count. NEW registry names: save, cancel, filter-reset. NEW form attributes: CrispyFormMixin.submit_icon=&#x27;save&#x27;, CrispyDeleteForm.delete_icon=&#x27;delete&#x27;, WorkflowForm.submit_icon=&#x27;workflow&#x27;. NEW adapter icon= keyword is consumed as rendering configuration, never serialized as an HTML attribute; omission selects kind default while explicit None/empty suppresses it. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-04-PLAN.md:68`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:104`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:109`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:116` |
| `display_form.html` | UNCHECKABLE | For the explicit empty-layout plus None-hook case, assert the helper&#x27;s selected layout stays empty and no action group appears. Preserve the installed pack&#x27;s display_form.html fallback to uni_form.html when form_html is empty; this package-helper fix does not promise suppression of that existing pack-owned field fallback or add a global template override. The default-action case has nonempty layout output and must not restore discarded fields. | `.venv/lib/python3.12/site-packages/crispy_bootstrap5/templates/bootstrap5/display_form.html:1` | `.planning/phases/06-form-button-leaf/06-05-PLAN.md:109` |
| `django.conf.settings` | UNCHECKABLE | Only the form floor is read lazily from django.conf.settings. Map tests use isolated singleton monkeypatches | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:155` |
| `docs/example` | UNCHECKABLE | - &quot;Documentation recipes render successfully and repeated docs/example checks do not modify generated sources or shared settings.&quot; | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-08-PLAN.md:34`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:21`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:211` |
| `docs/getting_started/tutorial-5-filters-permissions.md` | UNCHECKABLE | &lt;read_first&gt;docs/getting_started/tutorial-5-filters-permissions.md; tests/test1/test_filter.py; tests/test1/test_crispy_buttons.py&lt;/read_first&gt; | `docs/getting_started/tutorial-5-filters-permissions.md:1` | `.planning/phases/06-form-button-leaf/06-05-PLAN.md:97`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:15`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:98`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:99` |
| `docs/migrating-1.0.md` | UNCHECKABLE | - docs/migrating-1.0.md | `docs/migrating-1.0.md:1` | `.planning/phases/06-form-button-leaf/06-08-PLAN.md:18`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:38`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:114`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:115`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:82` |
| `docs/reference/action_menus.md` | UNCHECKABLE | - docs/reference/action_menus.md | `docs/reference/action_menus.md:1` | `.planning/phases/06-form-button-leaf/06-08-PLAN.md:10`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:45`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:81`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:82` |
| `docs/reference/buttons.md` | UNCHECKABLE | - docs/reference/buttons.md | `docs/reference/buttons.md:1` | `.planning/phases/06-form-button-leaf/06-02-PLAN.md:11`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:85`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:8`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:81`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:82` |
| `docs/reference/icons.md` | UNCHECKABLE | - docs/reference/icons.md | `docs/reference/icons.md:1` | `.planning/phases/06-form-button-leaf/06-08-PLAN.md:12`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:98`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:99` |
| `docs/reference/javascript.md` | UNCHECKABLE | - docs/reference/javascript.md | `docs/reference/javascript.md:1` | `.planning/phases/06-form-button-leaf/06-08-PLAN.md:20`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:114` |
| `docs/reference/list_view.md` | UNCHECKABLE | &lt;read_first&gt;src/crud_views/lib/views/list.py; src/crud_views/lib/views/mixins.py (get_filterset); installed crispy BasicNode.get_render/get_response_dict and FormHelper.get_attributes; tests/test1/test_filter.py; docs/reference/list_view.md (field-only helper example); 06-SPEC.md in this phase directory&lt;/read_first&gt; | `docs/reference/list_view.md:1` | `.planning/phases/06-form-button-leaf/06-05-PLAN.md:73`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:14`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:98`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:99` |
| `docs/reference/settings.md` | UNCHECKABLE | - docs/reference/settings.md | `docs/reference/settings.md:1` | `.planning/phases/06-form-button-leaf/06-02-PLAN.md:12`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:85`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:9`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:46`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:81`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:82` |
| `docs/reference/theme.md` | UNCHECKABLE | - docs/reference/theme.md | `docs/reference/theme.md:1` | `.planning/phases/06-form-button-leaf/06-08-PLAN.md:13`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:48`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:98`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:99` |
| `examples/bootstrap5` | UNCHECKABLE | - examples/bootstrap5/project/settings.py | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-08-PLAN.md:19`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:42`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:114`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:115`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:82`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:85`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:237`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:241`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:245` |
| `examples/bootstrap5/project/settings.py` | UNCHECKABLE | - examples/bootstrap5/project/settings.py | `examples/bootstrap5/project/settings.py:1` | `.planning/phases/06-form-button-leaf/06-08-PLAN.md:19`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:42`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:114`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:115`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:82` |
| `examples/bootstrap5/project/tests.py` | UNCHECKABLE | &lt;read_first&gt;examples/bootstrap5/project/settings.py; examples/bootstrap5/pytest.ini; examples/bootstrap5/test_i18n.py; examples/bootstrap5/project/tests.py (HomePageTest and SystemChecksTest); examples/bootstrap5/test_doc_links.py; docs/migrating-1.0.md Form buttons; 06-07-SUMMARY.md; 06-08-SUMMARY.md; 06-VALIDATION.md&lt;/read_first&gt; | `examples/bootstrap5/project/tests.py:1` | `.planning/phases/06-form-button-leaf/06-09-PLAN.md:82` |
| `examples/bootstrap5/pytest.ini` | UNCHECKABLE | &lt;read_first&gt;examples/bootstrap5/project/settings.py; examples/bootstrap5/pytest.ini; examples/bootstrap5/test_i18n.py; examples/bootstrap5/project/tests.py (HomePageTest and SystemChecksTest); examples/bootstrap5/test_doc_links.py; docs/migrating-1.0.md Form buttons; 06-07-SUMMARY.md; 06-08-SUMMARY.md; 06-VALIDATION.md&lt;/read_first&gt; | `examples/bootstrap5/pytest.ini:1` | `.planning/phases/06-form-button-leaf/06-09-PLAN.md:82` |
| `examples/bootstrap5/test_doc_links.py` | UNCHECKABLE | &lt;read_first&gt;examples/bootstrap5/project/settings.py; examples/bootstrap5/pytest.ini; examples/bootstrap5/test_i18n.py; examples/bootstrap5/project/tests.py (HomePageTest and SystemChecksTest); examples/bootstrap5/test_doc_links.py; docs/migrating-1.0.md Form buttons; 06-07-SUMMARY.md; 06-08-SUMMARY.md; 06-VALIDATION.md&lt;/read_first&gt; | `examples/bootstrap5/test_doc_links.py:1` | `.planning/phases/06-form-button-leaf/06-09-PLAN.md:82` |
| `examples/bootstrap5/test_docs_sync.py` | UNCHECKABLE | &lt;read_first&gt;CHANGELOG.md; docs/migrating-1.0.md; examples/bootstrap5/project/settings.py; examples/bootstrap5/test_docs_sync.py&lt;/read_first&gt; | `examples/bootstrap5/test_docs_sync.py:1` | `.planning/phases/06-form-button-leaf/06-08-PLAN.md:115` |
| `examples/bootstrap5/test_i18n.py` | UNCHECKABLE | &lt;read_first&gt;examples/bootstrap5/project/settings.py; examples/bootstrap5/pytest.ini; examples/bootstrap5/test_i18n.py; examples/bootstrap5/project/tests.py (HomePageTest and SystemChecksTest); examples/bootstrap5/test_doc_links.py; docs/migrating-1.0.md Form buttons; 06-07-SUMMARY.md; 06-08-SUMMARY.md; 06-VALIDATION.md&lt;/read_first&gt; | `examples/bootstrap5/test_i18n.py:1` | `.planning/phases/06-form-button-leaf/06-09-PLAN.md:82` |
| `fails_when` | UNCHECKABLE | &lt;fails_when&gt;The current real-render tracer fails, or the spec omits executing-branch dependency evidence or any named contract; passing old tests alone does not discharge the written design.&lt;/fails_when&gt; | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:190`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:217`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:238`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:103`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:127`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:142`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:88`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:114`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:87`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:108`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:88`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:113`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:94`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:124`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:84`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:104`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:119`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:90`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:106`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:123`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:73`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:89`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:226`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:230`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:234`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:238`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:242`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:246` |
| `field_classes` | UNCHECKABLE | Implement adapter render without calling BaseInput.render: retain raw value and kwargs, normalize per spec, render the selected leaf through a scoped context copy. Strip inherited input aliases from the template context, never expose the adapter object. Normalize SafeData and lazy values at render time to ordinary strings then use Django autoescaping once; serialized extra attrs are escaped once separately. Preserve constructor signature, slot-selected semantic kind, upstream generated IDs and legacy field_classes/flat_attrs for helper.inputs. Do not infer kind from the submitted name. The leaf uses cv_button_class form/cv_key/cv_label_mode, appends cv_css_class and host classes, and renders the three bodies with cancel URL only for cancel. Keep normalizer/icon behavior extensible for 06-04 rather than hardcoding a temporary floor. Update existing input-only assertions only where layout buttons changed; filter helper inputs remain inputs until 06-05. | `.venv/lib/python3.12/site-packages/crispy_forms/bootstrap.py:540`<br>`.venv/lib/python3.12/site-packages/crispy_forms/layout.py:232`<br>`.venv/lib/python3.12/site-packages/crispy_forms/layout.py:323`<br>`.venv/lib/python3.12/site-packages/crispy_forms/layout.py:387`<br>`.venv/lib/python3.12/site-packages/crispy_forms/layout.py:444`<br>`.venv/lib/python3.12/site-packages/crispy_forms/layout.py:508` | `.planning/phases/06-form-button-leaf/06-02-PLAN.md:99`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:123` |
| `flat_attrs` | UNCHECKABLE | Implement adapter render without calling BaseInput.render: retain raw value and kwargs, normalize per spec, render the selected leaf through a scoped context copy. Strip inherited input aliases from the template context, never expose the adapter object. Normalize SafeData and lazy values at render time to ordinary strings then use Django autoescaping once; serialized extra attrs are escaped once separately. Preserve constructor signature, slot-selected semantic kind, upstream generated IDs and legacy field_classes/flat_attrs for helper.inputs. Do not infer kind from the submitted name. The leaf uses cv_button_class form/cv_key/cv_label_mode, appends cv_css_class and host classes, and renders the three bodies with cancel URL only for cancel. Keep normalizer/icon behavior extensible for 06-04 rather than hardcoding a temporary floor. Update existing input-only assertions only where layout buttons changed; filter helper inputs remain inputs until 06-05. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-02-PLAN.md:99` |
| `form.cv_view` | UNCHECKABLE | - form.cv_view wins over conflicting helper/page owners; missing and None fall through. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-03-PLAN.md:99` |
| `form.helper` | UNCHECKABLE | Implement the spec&#x27;s owner selection before flattening context. First read cv_view from the actual adapter render form argument, not context[&#x27;form&#x27;] or an outer formset container (M-OWNERS, D-09). Obtain the current helper owner from the package&#x27;s private pushed context entry when present, otherwise identify the current crispy invocation&#x27;s helper overlay from response metadata/provenance and recover the genuine page view through Context.dicts, excluding all enclosing crispy helper response overlays rather than accepting the first lower view. Never use a fixed stack offset or the last dictionary alone: FormActions.render leaves layers behind, and nested crispy row renders create several overlays. Preserve actual object identity and the nearest non-None genuine page owner, including page-level None. Classify response boundaries using installed crispy metadata and demonstrate that classification with stacked invocations; another helper response is not a page layer. A private transported page-owner value, when present from a production inclusion boundary, is authoritative for the page tier, including an explicit None that means no page owner. It never overrides the current row form or current helper tiers. Do not instantiate/re-read form.helper properties to guess the current helper. Explicitly supplied tag helpers must be respected. Once a non-None owner is found, stop even if it lacks crud configuration; never search for a more convenient lower CrudView. Use scoped copies/pushes and restore all context state. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-03-PLAN.md:107`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:82` |
| `form:cancel` | UNCHECKABLE | - A delete payload with slot=form:cancel uses cancel styling/kind and retains its original name/value. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-04-PLAN.md:101` |
| `form:filter-reset` | UNCHECKABLE | Add get_form_actions following the spec. Initialize FormHelper without passing form when preserving declared layout; deep-copy declared layout per instance, and retain helper.form as the identical explicit form argument when supplied, preserving upstream association without rebuilding its fields (M-HELPER-STATE). Make ListViewFilterFormHelper.__bool__ return True independently of its inherited __len__, AND keep a truthy prepared instance layout before crispy dispatch even for no-layout or None actions (private Layout subclass __bool__ returning True). Both terms of &#96;if helper and helper.layout&#96; must pass; a layout-only fix is insufficient. Preserve len(helper) as the actual layout field count, use identity/is-None checks for owner resolution, and do not alter upstream or unrelated helper classes. All new lifecycle/owner state uses underscore-prefixed attributes so get_attributes does not publish it. Populate no-layout fields from the actual form at render_layout before appending the action group. Preserve the helper&#x27;s configured layout field order. Build Apply/Reset as package adapters with form:filter-submit/form:filter-reset and original IDs, append exactly once to the isolated layout. Keep Hidden controls on inputs with current GET naming/value logic. During render_layout push the actual helper owner under a private context key so adapters need not inspect a fresh form.helper property; restore context afterward. Keep ListViewTableFilterMixin construction unchanged. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-05-PLAN.md:82` |
| `form:filter-submit` | UNCHECKABLE | Add get_form_actions following the spec. Initialize FormHelper without passing form when preserving declared layout; deep-copy declared layout per instance, and retain helper.form as the identical explicit form argument when supplied, preserving upstream association without rebuilding its fields (M-HELPER-STATE). Make ListViewFilterFormHelper.__bool__ return True independently of its inherited __len__, AND keep a truthy prepared instance layout before crispy dispatch even for no-layout or None actions (private Layout subclass __bool__ returning True). Both terms of &#96;if helper and helper.layout&#96; must pass; a layout-only fix is insufficient. Preserve len(helper) as the actual layout field count, use identity/is-None checks for owner resolution, and do not alter upstream or unrelated helper classes. All new lifecycle/owner state uses underscore-prefixed attributes so get_attributes does not publish it. Populate no-layout fields from the actual form at render_layout before appending the action group. Preserve the helper&#x27;s configured layout field order. Build Apply/Reset as package adapters with form:filter-submit/form:filter-reset and original IDs, append exactly once to the isolated layout. Keep Hidden controls on inputs with current GET naming/value logic. During render_layout push the actual helper owner under a private context key so adapters need not inspect a fresh form.helper property; restore context afterward. Keep ListViewTableFilterMixin construction unchanged. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-05-PLAN.md:82` |
| `form:hidden-label` | EXCLUDED_NEW | NEW template: src/crud_views/templates/crud_views/tags/button/form.html. NEW symbol: FORM_LEAF_KEYS in button_data.py. NEW normalized fields: cv_type, cv_name, cv_value, cv_id, cancel-only cv_cancel_url, cv_css_class, cv_flat_attrs; existing label/icon fields are reused. NEW class utility defaults: form:hidden-label and form:icon-host, with exhaustive key/count documentation updated in their producing task. Private helper names are implementation-local. No new external package. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-02-PLAN.md:79`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:97`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:25`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:68` |
| `form:icon-host` | EXCLUDED_NEW | NEW template: src/crud_views/templates/crud_views/tags/button/form.html. NEW symbol: FORM_LEAF_KEYS in button_data.py. NEW normalized fields: cv_type, cv_name, cv_value, cv_id, cancel-only cv_cancel_url, cv_css_class, cv_flat_attrs; existing label/icon fields are reused. NEW class utility defaults: form:hidden-label and form:icon-host, with exhaustive key/count documentation updated in their producing task. Private helper names are implementation-local. No new external package. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-02-PLAN.md:79`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:97`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:25`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:68`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:112`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:118`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:120` |
| `form:unknown` | UNCHECKABLE | Branch cv_button_data early for form before action URL/modal derivation; retain existing action behavior and LEAF_KEYS. Introduce FORM_LEAF_KEYS for the exact spec contract. Validate cv_key against FORM_KINDS and cv_type against submit/button/reset; invalid caller kind/type raises ValueError. Explicitly reject non-form and unknown slot kinds when rendering through the new layout leaf; preserve arbitrary slot handling on legacy helper.inputs without constructor-time rejection or warnings (M-SLOT, D-01/D-02/D-13). Cover formset:control and form:unknown as rejected layout slots and retained legacy input cases; 06-08 records this layout-only Breaking change. Missing or None textual values normalize to empty text without coercing other falsey data such as numeric zero to empty. Preserve valid empty labels without manufacturing text. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-02-PLAN.md:98` |
| `form_actions_label_mode` | EXCLUDED_NEW | NEW fields: CrudViewsSettings.form_actions_label_mode (CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE), ViewSet.form_actions_label_mode, CrudView.cv_form_actions_label_mode. NEW public resolver: CrudView.cv_get_form_actions_label_mode(). Existing cv_get_action_label_mode gains location=&#x27;form&#x27;. Private owner-recovery helpers and a scoped page-owner transport key across Formsets/cv_x_formset are internal, not promised public names or leaf-context keys. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-03-PLAN.md:68`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:83`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:84` |
| `form_html` | UNCHECKABLE | For the explicit empty-layout plus None-hook case, assert the helper&#x27;s selected layout stays empty and no action group appears. Preserve the installed pack&#x27;s display_form.html fallback to uni_form.html when form_html is empty; this package-helper fix does not promise suppression of that existing pack-owned field fallback or add a global template override. The default-action case has nonempty layout output and must not restore discarded fields. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-05-PLAN.md:109` |
| `format_html` | UNCHECKABLE | Record accurate dependency findings: Django 6 removed zero-argument format_html calls, not the function; | `.venv/lib/python3.12/site-packages/django/utils/html.py:129` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:180`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:115`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:163` |
| `from_settings` | UNCHECKABLE | Record M-SETTINGS-LIFECYCLE&#x27;s existing lifecycle explicitly: from_settings captures form-map defaults when | `src/crud_views/lib/settings.py:13` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:153`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:83`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:142` |
| `get_attributes` | UNCHECKABLE | For M-EMPTY-REPLACEMENT, specify pre-dispatch preparation in the package helper&#x27;s get_attributes override: | `.venv/lib/python3.12/site-packages/crispy_forms/helper.py:290` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:166`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:97`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:67`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:73`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:82`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:83`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:108`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:142` |
| `get_filterset` | UNCHECKABLE | &lt;read_first&gt;src/crud_views/lib/views/list.py; src/crud_views/lib/views/mixins.py (get_filterset); installed crispy BasicNode.get_render/get_response_dict and FormHelper.get_attributes; tests/test1/test_filter.py; docs/reference/list_view.md (field-only helper example); 06-SPEC.md in this phase directory&lt;/read_first&gt; | `src/crud_views/lib/views/mixins.py:315` | `.planning/phases/06-form-button-leaf/06-05-PLAN.md:73` |
| `get_form_actions` | UNCHECKABLE | Define get_form_actions returning FormActions or None; None means no group, empty FormActions is retained. | `src/crud_views/lib/crispy/form.py:53` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:158`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:171`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:24`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:67`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:82`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:100`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:108`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:143`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:117`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:36`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:101`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:102`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:118` |
| `get_form_class` | UNCHECKABLE | For filter helpers inspect the configured helper class only when default get_form_actions is inherited. For a concrete dict-valued polymorphic_forms mapping inspect each distinct form class using the same provider rules, without selecting a request/model instance; identify form class and kind in warnings and deduplicate identical repeated class/kind entries locally per traversal (M-POLYMORPHIC). Missing/custom mapping providers skip static inference and get actual polymorphic create/update runtime tests. Never instantiate forms/helpers, call request-dependent get_form_class, or execute custom action hooks during checks. | `src/crud_views_polymorphic/lib/utils.py:64` | `.planning/phases/06-form-button-leaf/06-06-PLAN.md:117` |
| `get_libraries` | UNCHECKABLE | Resolve form mode through the public resolver; catch ValueError only around mode resolution so E108/E210/E211 survive strict checking. For M-REGISTRY-OFF and M-ICON-AVAILABILITY, use the existing icons.resolve_icon(value) in both static inspection and the form normalizer: a None result means an absent/disabled semantic mapping, including explicit None/empty and a semantic name mapped by CRUD_VIEWS_ICONS to None/empty. Test each with known default submit/delete/filter controls. For L-UNREGISTERED-FORM-ICON, semantic resolution alone is insufficient: a nonempty prefix must also have a dict-valued library entry and a usable registered renderer. Add a private side-effect-free availability helper in icons.py reusing resolve_icon/get_libraries/_get_renderers metadata; resolving a renderer callable is allowed, invoking it is not. Share this predicate between form static checks and the normalizer. A resolved empty prefix is the existing raw CSS-class path and remains available. A direct submit_icon=&#x27;unknown:save&#x27; must trigger W292 for static icon-only controls and the same strict ValueError/non-strict logged label fallback as disabled semantic icons at runtime. Registry W352 only visits table entries, so do not claim it covers direct per-form values. Preserve existing registry diagnostics for malformed libraries and named entries; do not change their IDs or silently suppress them. Never call render_icon or a custom renderer to probe availability. Leave actual inline rendering to the leaf&#x27;s one cv_icon call; no rendered-markup cache or extra public leaf key is needed. A custom renderer&#x27;s returned markup remains its existing renderer contract, not a second missing-mapping test. Preserve icon_host_keys/resolve_icon_name_class for placement: a valid host icon is available even though the leaf emits no inline element, and a None/empty form:icon-host class override remains the existing explicit placement opt-out rather than a missing semantic icon. | `src/crud_views/lib/icons.py:136` | `.planning/phases/06-form-button-leaf/06-06-PLAN.md:118` |
| `get_render` | UNCHECKABLE | &lt;read_first&gt;06-SPEC.md ownership contract; installed crispy BasicNode.get_render/get_response_dict, FormActions.render and FormHelper.get_attributes; src/crud_views/lib/formsets/layout.py; src/crud_views/templatetags/crud_views_formsets.py; src/crud_views/templates/crud_views/formsets/formsets.html; src/crud_views/templates/crud_views/formsets/formset.html; Django InclusionNode.render; tests/test1/test_crispy_buttons.py&lt;/read_first&gt; | `.venv/lib/python3.12/site-packages/crispy_forms/templatetags/crispy_forms_tags.py:70` | `.planning/phases/06-form-button-leaf/06-03-PLAN.md:97`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:73`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:83` |
| `get_response_dict` | UNCHECKABLE | crispy get_response_dict calls it before the combined helper-and-layout truthiness guard. Detect and isolate caller layout | `.venv/lib/python3.12/site-packages/crispy_forms/templatetags/crispy_forms_tags.py:137` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:167`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:97`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:147`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:73`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:83` |
| `group` | UNCHECKABLE | Define get_form_actions returning FormActions or None; None means no group, empty FormActions is retained. | `examples/bootstrap5/project/features.py:54`<br>`src/crud_views/lib/view/action_menu.py:102`<br>`src/crud_views/templatetags/crud_views.py:302`<br>`tests/test1/od/test_config.py:159`<br>`tests/test1/od/test_config.py:188`<br>`tests/test1/od/test_config.py:193`<br>`tests/test1/od/test_config.py:272`<br>`tests/test1/od/test_config.py:56` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:158`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:189`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:24`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:28`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:76`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:82`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:100`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:102`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:103`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:107`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:108`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:109`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:196` |
| `helper.form` | UNCHECKABLE | - &quot;D-03, D-04: A post-construction helper.layout replacement remains the selected layout across renders; explicit form construction retains helper.form identity without replacing fields.&quot; | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-05-PLAN.md:27`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:82`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:102`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:107`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:108`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:113`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:128` |
| `helper.input` | UNCHECKABLE | Select kind from slot, never the name. Add an explicit icon keyword using a sentinel so omission selects the semantic default while None/empty remains an intentional missing icon. Keep legacy helper.input attributes usable. CrispyFormMixin and delete hooks pass submit_icon/delete_icon; workflow supplies its class default. Preserve kwargs override ordering so a custom hook icon or slot wins over the standard hook, then the explicit form icon wins over the adapter kind default. Render each package form against form floor both/icon and preserve the baseline label-mode outputs. Do not change stored values or click handlers. Add sequential/interleaved form instance tests to prove custom icons and current language do not persist into later forms. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-04-PLAN.md:104` |
| `helper.inputs` | UNCHECKABLE | empty FormActions outcomes through the actual crispy tag. Clearing helper.inputs=[] no longer suppresses stock | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:170`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:91`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:98`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:99`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:160`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:143`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:36`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:102`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:118`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:140`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:153` |
| `helper.layout` | UNCHECKABLE | and its prepared Layout truthy before crispy evaluates &#96;if helper and helper.layout&#96;. FormHelper inherits | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:160`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:27`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:82`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:102`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:108` |
| `icon_host_keys` | UNCHECKABLE | for them while preserving raw CSS-class icons, valid host opt-outs and the one-render contract. The leaf owns one inline render, while existing icon_host_keys | `src/crud_views/lib/view/button_data.py:41` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:177`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:118` |
| `icons.resolve_icon` | UNCHECKABLE | For M-ICON-AVAILABILITY, both static checks and runtime missing-icon policy use icons.resolve_icon semantic | `src/crud_views/lib/icons.py:187` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:174`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:118` |
| `input.value` | UNCHECKABLE | Add one coherent Unreleased Breaking entry and a Form buttons migration section in the same commit, covering input-to-button selectors, literal values replacing template evaluation, and cv_* custom-template context replacing input.value. Include preserved confirmation-only delete flow plus the new clicked submitter field, crispy&#x27;s preserved multi-word name normalization, IDs and custom-template/helper migration links. Explicitly record M-SLOT: new layout rendering rejects non-form/unknown slots with ValueError, while legacy add_input controls keep their current path; migrate layout callers to one of the five finite form kinds and an appropriate form:&lt;kind&gt;:&lt;mode&gt; class override, without adding kinds/variants. Document reserved-attribute collision rules and intentional missing-icon fallback. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-08-PLAN.md:117` |
| `inputs.html` | UNCHECKABLE | Per L-HIDDEN-WRAPPER and D-01, retain the installed pack&#x27;s hidden-input wrapper and margin after the visible layout actions; this ordering is accepted pack-owned behavior. Extend the filter golden harness to capture the deterministic visible-action/hidden-wrapper region, excluding CSRF, and compare existing hidden names/values independently from this expected ordering change. Pin wrapper classes/order and the absence of visible duplicate actions. Update only filter expectations and its phase-owned golden after comparison to 06-01; 06-08 documents the accepted wrapper behavior rather than globally overriding inputs.html. | `.venv/lib/python3.12/site-packages/crispy_bootstrap5/templates/bootstrap5/inputs.html:1` | `.planning/phases/06-form-button-leaf/06-05-PLAN.md:84` |
| `is_formset` | UNCHECKABLE | &#124; H-OVERLAY-PROVENANCE &#124; Rejected as a missing-API claim, not as a test obligation: installed BasicNode.get_response_dict supplies inputs/is_formset/template_pack metadata; no named provenance field is required. Task 2 and the pre-implementation spec retain the current-invocation/page-boundary proof and nested-row/None regressions; this single-reviewer unconfirmed HIGH does not authorize an ownership redesign or certify future implementation. &#124; | `.venv/lib/python3.12/site-packages/crispy_forms/templatetags/crispy_forms_tags.py:108` | `.planning/phases/06-form-button-leaf/06-03-PLAN.md:147` |
| `javascript.md` | UNCHECKABLE | - docs/reference/javascript.md | `docs/reference/javascript.md:1` | `.planning/phases/06-form-button-leaf/06-08-PLAN.md:20`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:114`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:119`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:141` |
| `layout.fields` | UNCHECKABLE | __len__ returning len(layout.fields), so a truthy Layout alone cannot admit an empty helper. Specify a | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:161` |
| `len(helper)` | UNCHECKABLE | len(helper) field-count semantics and leave third-party helpers untouched. Then render_layout populates | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:163`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:82`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:108` |
| `list_view.md` | UNCHECKABLE | &lt;read_first&gt;src/crud_views/lib/views/list.py; src/crud_views/lib/views/mixins.py (get_filterset); installed crispy BasicNode.get_render/get_response_dict and FormHelper.get_attributes; tests/test1/test_filter.py; docs/reference/list_view.md (field-only helper example); 06-SPEC.md in this phase directory&lt;/read_first&gt; | `docs/reference/list_view.md:1` | `.planning/phases/06-form-button-leaf/06-05-PLAN.md:73`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:14`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:98`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:99`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:102` |
| `m.group` | UNCHECKABLE | &lt;automated&gt;.venv/bin/python -c &#x27;from pathlib import Path; import re; p=Path(&quot;.planning/phases/06-form-button-leaf/06-SPEC.md&quot;); s=p.read_text(); headings=(&quot;Prerequisite evidence&quot;, &quot;Form contract&quot;, &quot;Literal text and attributes&quot;, &quot;Template selection&quot;, &quot;Ownership&quot;, &quot;Helper lifecycle&quot;, &quot;Diagnostics and icons&quot;, &quot;Dependency validation&quot;, &quot;Golden history&quot;); sections={h: re.search(r&quot;(?m)^## &quot; + re.escape(h) + r&quot;\n([\s\S]*?)(?=^## &#124;\Z)&quot;, s) for h in headings}; assert all(m and m.group(1).strip() for m in sections.values()), &quot;Missing/empty design section&quot;; assert re.search(r&quot;\b[0-9a-f]{40}\b&quot;, sections[&quot;Prerequisite evidence&quot;].group(1)), &quot;Missing executing-branch HEAD SHA&quot;&#x27; &amp;&amp; .venv/bin/pytest tests/test1/test_crispy_buttons.py tests/test1/test_button_data.py tests/test1/test_label_mode.py tests/test1/test_action_label_mode_config.py tests/test1/test_button_classes.py -q&lt;/automated&gt; | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:189` |
| `manage.py` | UNCHECKABLE | &lt;fails_when&gt;The URLconf does not register feature ViewSets, the registered example reports system-check errors, or the test fails to start; bare manage.py check alone is insufficient.&lt;/fails_when&gt; | `examples/bootstrap5/manage.py:1`<br>`src/crud_views/lib/views/manage.py:1` | `.planning/phases/06-form-button-leaf/06-09-PLAN.md:238`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:256` |
| `modal.js` | UNCHECKABLE | - src/crud_views/static/crud_views/js/modal.js | `src/crud_views/static/crud_views/js/modal.js:1` | `.planning/phases/06-form-button-leaf/06-07-PLAN.md:9`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:34`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:70`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:71`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:80` |
| `monkeypatch.setattr` | UNCHECKABLE | Extend the config suite&#x27;s existing monkeypatch.setattr(crud_views_settings, ...) pattern for form maps, restoring it after each case; construct CrudViewsSettings(form_actions_label_mode=...) explicitly for model-level validation cases. Add real crispy rendering with a monkeypatched singleton submit=&#x27;both&#x27; and an unmapped cancel: a post-import override_settings(CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE={&#x27;submit&#x27;: &#x27;icon&#x27;}) alone leaves submit in both, while nested CRUD_VIEWS_LABEL_MODE_DEFAULTS={&#x27;form&#x27;: &#x27;icon&#x27;} changes only the unmapped cancel and exiting restores its label floor. Keep this distinction explicit in the spec and documentation rather than treating override_settings on the map as a supported hot refresh. The render assertion proves the selected map is connected to the leaf. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-03-PLAN.md:84` |
| `must_haves.prohibitions` | UNCHECKABLE | utility, so must_haves.prohibitions is empty. The two unclassified edge assumptions above are retained. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-09-PLAN.md:220` |
| `must_haves.truths` | UNCHECKABLE | must_haves.truths and behavioral acceptance. The unclassified rows retain their status even though the | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-09-PLAN.md:178` |
| `n` | UNCHECKABLE | &lt;automated&gt;.venv/bin/python -c &#x27;from pathlib import Path; import re; p=Path(&quot;.planning/phases/06-form-button-leaf/06-SPEC.md&quot;); s=p.read_text(); headings=(&quot;Prerequisite evidence&quot;, &quot;Form contract&quot;, &quot;Literal text and attributes&quot;, &quot;Template selection&quot;, &quot;Ownership&quot;, &quot;Helper lifecycle&quot;, &quot;Diagnostics and icons&quot;, &quot;Dependency validation&quot;, &quot;Golden history&quot;); sections={h: re.search(r&quot;(?m)^## &quot; + re.escape(h) + r&quot;\n([\s\S]*?)(?=^## &#124;\Z)&quot;, s) for h in headings}; assert all(m and m.group(1).strip() for m in sections.values()), &quot;Missing/empty design section&quot;; assert re.search(r&quot;\b[0-9a-f]{40}\b&quot;, sections[&quot;Prerequisite evidence&quot;].group(1)), &quot;Missing executing-branch HEAD SHA&quot;&#x27; &amp;&amp; .venv/bin/pytest tests/test1/test_crispy_buttons.py tests/test1/test_button_data.py tests/test1/test_label_mode.py tests/test1/test_action_label_mode_config.py tests/test1/test_button_classes.py -q&lt;/automated&gt; | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:189`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:72` |
| `node_modules` | UNCHECKABLE | preserving existing node_modules in a uniquely named backup until restoration succeeds. Do not change | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:99`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:79` |
| `noxfile.py` | UNCHECKABLE | pyproject.toml; package.json; package-lock.json; noxfile.py. | `noxfile.py:1` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:84`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:14`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:31`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:37`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:112`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:113` |
| `npm-cli.js` | UNCHECKABLE | Create the phase-local 06-JS-RUNTIME.json with absolute Node and npm-cli.js paths, actual Node/npm versions, | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:102`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:108` |
| `override_settings` | UNCHECKABLE | Retain the location/default assertions updated in task 1 and expand lazy override_settings coverage in test_label_mode.py and test_button_data.py. Existing action contracts and location-independent finite class grammar remain unchanged. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-02-PLAN.md:121`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:79`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:84`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:142`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:90`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:85`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:69` |
| `p.read_text` | UNCHECKABLE | &lt;automated&gt;.venv/bin/python -c &#x27;from pathlib import Path; import re; p=Path(&quot;.planning/phases/06-form-button-leaf/06-SPEC.md&quot;); s=p.read_text(); headings=(&quot;Prerequisite evidence&quot;, &quot;Form contract&quot;, &quot;Literal text and attributes&quot;, &quot;Template selection&quot;, &quot;Ownership&quot;, &quot;Helper lifecycle&quot;, &quot;Diagnostics and icons&quot;, &quot;Dependency validation&quot;, &quot;Golden history&quot;); sections={h: re.search(r&quot;(?m)^## &quot; + re.escape(h) + r&quot;\n([\s\S]*?)(?=^## &#124;\Z)&quot;, s) for h in headings}; assert all(m and m.group(1).strip() for m in sections.values()), &quot;Missing/empty design section&quot;; assert re.search(r&quot;\b[0-9a-f]{40}\b&quot;, sections[&quot;Prerequisite evidence&quot;].group(1)), &quot;Missing executing-branch HEAD SHA&quot;&#x27; &amp;&amp; .venv/bin/pytest tests/test1/test_crispy_buttons.py tests/test1/test_button_data.py tests/test1/test_label_mode.py tests/test1/test_action_label_mode_config.py tests/test1/test_button_classes.py -q&lt;/automated&gt; | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:189` |
| `package-lock.json` | UNCHECKABLE | pyproject.toml; package.json; package-lock.json; noxfile.py. | `package-lock.json:1` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:84`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:71` |
| `package.json` | UNCHECKABLE | pyproject.toml; package.json; package-lock.json; noxfile.py. | `package.json:1` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:84`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:71` |
| `polymorphic_forms` | UNCHECKABLE | - Concrete polymorphic_forms mappings inspect each supported form class; custom/request-dependent providers are skipped statically and proven by real runtime renders. | `examples/bootstrap5/polymorphic_demo/views.py:72`<br>`examples/bootstrap5/polymorphic_demo/views.py:78`<br>`src/crud_views_polymorphic/lib/utils.py:35`<br>`tests/test1/app/views.py:565`<br>`tests/test1/app/views.py:573` | `.planning/phases/06-form-button-leaf/06-06-PLAN.md:113`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:117`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:142` |
| `process.execPath` | UNCHECKABLE | Node directory to PATH, uses the selected Node to assert process.execPath/version and unchanged lock hash, | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:105` |
| `project.settings` | UNCHECKABLE | For L-EXAMPLE-COVERAGE, run the separate example-consumer gate below from examples/bootstrap5 so its pytest.ini selects project.settings: all test_i18n.py cases (including test_demo_pages_render_german and its translated create-submit value), HomePageTest.test_every_feature_landing_page_renders, and all test_doc_links.py reference/backlink cases. Record their collected counts and results after 06-08 enables form=both. Root pytest tests does not include this example tree; SystemChecksTest and test_docs_sync alone cannot substitute. Retain those two existing gates as independent evidence. A failure is an acceptance blocker to route to the producing implementation/docs plan, not grounds to remove or relax the affected assertion. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-09-PLAN.md:85` |
| `project/tests.py::HomePageTest::test_every_feature_landing_page_renders` | UNCHECKABLE | &lt;automated&gt;cd examples/bootstrap5 &amp;&amp; ../../.venv/bin/pytest test_i18n.py project/tests.py::HomePageTest::test_every_feature_landing_page_renders test_doc_links.py -q&lt;/automated&gt; | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-09-PLAN.md:245` |
| `project/tests.py::SystemChecksTest::test_no_check_errors_with_every_viewset_registered` | UNCHECKABLE | &lt;automated&gt;cd examples/bootstrap5 &amp;&amp; ../../.venv/bin/pytest project/tests.py::SystemChecksTest::test_no_check_errors_with_every_viewset_registered -q&lt;/automated&gt; | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-09-PLAN.md:237` |
| `pyproject.toml` | UNCHECKABLE | pyproject.toml; package.json; package-lock.json; noxfile.py. | `pyproject.toml:1` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:84`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:113` |
| `pytest.ini` | UNCHECKABLE | &lt;read_first&gt;examples/bootstrap5/project/settings.py; examples/bootstrap5/pytest.ini; examples/bootstrap5/test_i18n.py; examples/bootstrap5/project/tests.py (HomePageTest and SystemChecksTest); examples/bootstrap5/test_doc_links.py; docs/migrating-1.0.md Form buttons; 06-07-SUMMARY.md; 06-08-SUMMARY.md; 06-VALIDATION.md&lt;/read_first&gt; | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-09-PLAN.md:82`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:85` |
| `re.escape` | UNCHECKABLE | &lt;automated&gt;.venv/bin/python -c &#x27;from pathlib import Path; import re; p=Path(&quot;.planning/phases/06-form-button-leaf/06-SPEC.md&quot;); s=p.read_text(); headings=(&quot;Prerequisite evidence&quot;, &quot;Form contract&quot;, &quot;Literal text and attributes&quot;, &quot;Template selection&quot;, &quot;Ownership&quot;, &quot;Helper lifecycle&quot;, &quot;Diagnostics and icons&quot;, &quot;Dependency validation&quot;, &quot;Golden history&quot;); sections={h: re.search(r&quot;(?m)^## &quot; + re.escape(h) + r&quot;\n([\s\S]*?)(?=^## &#124;\Z)&quot;, s) for h in headings}; assert all(m and m.group(1).strip() for m in sections.values()), &quot;Missing/empty design section&quot;; assert re.search(r&quot;\b[0-9a-f]{40}\b&quot;, sections[&quot;Prerequisite evidence&quot;].group(1)), &quot;Missing executing-branch HEAD SHA&quot;&#x27; &amp;&amp; .venv/bin/pytest tests/test1/test_crispy_buttons.py tests/test1/test_button_data.py tests/test1/test_label_mode.py tests/test1/test_action_label_mode_config.py tests/test1/test_button_classes.py -q&lt;/automated&gt; | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:189` |
| `re.search` | UNCHECKABLE | &lt;automated&gt;.venv/bin/python -c &#x27;from pathlib import Path; import re; p=Path(&quot;.planning/phases/06-form-button-leaf/06-SPEC.md&quot;); s=p.read_text(); headings=(&quot;Prerequisite evidence&quot;, &quot;Form contract&quot;, &quot;Literal text and attributes&quot;, &quot;Template selection&quot;, &quot;Ownership&quot;, &quot;Helper lifecycle&quot;, &quot;Diagnostics and icons&quot;, &quot;Dependency validation&quot;, &quot;Golden history&quot;); sections={h: re.search(r&quot;(?m)^## &quot; + re.escape(h) + r&quot;\n([\s\S]*?)(?=^## &#124;\Z)&quot;, s) for h in headings}; assert all(m and m.group(1).strip() for m in sections.values()), &quot;Missing/empty design section&quot;; assert re.search(r&quot;\b[0-9a-f]{40}\b&quot;, sections[&quot;Prerequisite evidence&quot;].group(1)), &quot;Missing executing-branch HEAD SHA&quot;&#x27; &amp;&amp; .venv/bin/pytest tests/test1/test_crispy_buttons.py tests/test1/test_button_data.py tests/test1/test_label_mode.py tests/test1/test_action_label_mode_config.py tests/test1/test_button_classes.py -q&lt;/automated&gt; | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:189` |
| `read_bytes` | UNCHECKABLE | tests compare render bytes to read_bytes with no update-on-test behavior. Pin default text, name, value, | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:205` |
| `render` | UNCHECKABLE | &lt;name&gt;Task 1: Trace the existing form render and record the required design&lt;/name&gt; | `.venv/lib/python3.12/site-packages/crispy_forms/bootstrap.py:1127`<br>`.venv/lib/python3.12/site-packages/crispy_forms/bootstrap.py:306`<br>`.venv/lib/python3.12/site-packages/crispy_forms/bootstrap.py:356`<br>`.venv/lib/python3.12/site-packages/crispy_forms/bootstrap.py:402`<br>`.venv/lib/python3.12/site-packages/crispy_forms/bootstrap.py:460`<br>`.venv/lib/python3.12/site-packages/crispy_forms/bootstrap.py:558`<br>`.venv/lib/python3.12/site-packages/crispy_forms/bootstrap.py:725`<br>`.venv/lib/python3.12/site-packages/crispy_forms/bootstrap.py:775` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:75`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:119`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:122`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:133`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:146`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:147`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:150`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:177`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:190`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:193`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:205`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:268`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:269`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:41`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:50`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:91`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:96`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:99`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:122`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:127`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:178`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:28`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:30`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:84`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:97`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:102`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:107`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:109`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:129`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:169`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:89`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:98`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:144`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:23`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:102`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:103`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:107`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:108`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:35`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:107`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:116`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:119`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:120`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:154`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:175`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:185`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:186`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:34`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:84`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:86`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:90`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:97`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:102`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:20`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:22`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:76`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:111`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:165`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:189`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:198`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:200`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:246` |
| `render_icon` | UNCHECKABLE | &lt;read_first&gt;src/crud_views/lib/view/buttons.py (cv_icon_mode_checks); src/crud_views/lib/crispy/form.py; src/crud_views/lib/views/list.py; src/crud_views/lib/view/button_data.py; src/crud_views/lib/icons.py (resolve_icon/render_icon/resolve_icon_name_class); tests/test1/test_icon_host_leaves.py; 06-SPEC.md static-check reach&lt;/read_first&gt; | `src/crud_views/lib/icons.py:223` | `.planning/phases/06-form-button-leaf/06-06-PLAN.md:103`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:118` |
| `render_layout` | UNCHECKABLE | helper. Package filter helper render_layout supplies a private helper-owner context entry using context.push | `.venv/lib/python3.12/site-packages/crispy_forms/helper.py:266` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:137`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:163`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:169`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:67`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:82`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:83`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:88`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:108` |
| `request.user` | UNCHECKABLE | Add real crispy custom-template fixtures using an isolated template loader inside the test, including a subclass template and active pack substitution. Implement the spec collision policy for type/name/value/id/class/cancel/title/tooltip and ordinary underscore/hyphen aliases with exactly one final attribute. Preserve boolean True/False and underscore-to-hyphen extra attrs. For label/value/name/id/title and string attrs, test plain strings and marked-safe strings, literal {{ request.user }}, Unicode and lazy translated values under two language contexts. Assert decoded DOM text/value equal the originals and absence of injected attributes/nodes, not just escaped substrings. Ensure no mutation of self.value, shared field_classes, normalized input dicts, or outer Context; retain constructor-visible legacy behavior. An empty explicit template argument retains upstream truthy fallback semantics; valid explicit strings honor D-05–D-08. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-02-PLAN.md:123` |
| `resolve_icon` | UNCHECKABLE | For M-ICON-AVAILABILITY, both static checks and runtime missing-icon policy use icons.resolve_icon semantic | `src/crud_views/lib/icons.py:187` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:174`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:103`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:118`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:154` |
| `resolve_icon_name_class` | UNCHECKABLE | &lt;read_first&gt;src/crud_views/lib/view/buttons.py (cv_icon_mode_checks); src/crud_views/lib/crispy/form.py; src/crud_views/lib/views/list.py; src/crud_views/lib/view/button_data.py; src/crud_views/lib/icons.py (resolve_icon/render_icon/resolve_icon_name_class); tests/test1/test_icon_host_leaves.py; 06-SPEC.md static-check reach&lt;/read_first&gt; | `src/crud_views/lib/icons.py:240` | `.planning/phases/06-form-button-leaf/06-06-PLAN.md:103`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:118` |
| `sample_count` | UNCHECKABLE | is part of this plan set. Context estimates use factor 1, sample_count 0 and confidence low from estimate-calibration. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-09-PLAN.md:114` |
| `sections.values` | UNCHECKABLE | &lt;automated&gt;.venv/bin/python -c &#x27;from pathlib import Path; import re; p=Path(&quot;.planning/phases/06-form-button-leaf/06-SPEC.md&quot;); s=p.read_text(); headings=(&quot;Prerequisite evidence&quot;, &quot;Form contract&quot;, &quot;Literal text and attributes&quot;, &quot;Template selection&quot;, &quot;Ownership&quot;, &quot;Helper lifecycle&quot;, &quot;Diagnostics and icons&quot;, &quot;Dependency validation&quot;, &quot;Golden history&quot;); sections={h: re.search(r&quot;(?m)^## &quot; + re.escape(h) + r&quot;\n([\s\S]*?)(?=^## &#124;\Z)&quot;, s) for h in headings}; assert all(m and m.group(1).strip() for m in sections.values()), &quot;Missing/empty design section&quot;; assert re.search(r&quot;\b[0-9a-f]{40}\b&quot;, sections[&quot;Prerequisite evidence&quot;].group(1)), &quot;Missing executing-branch HEAD SHA&quot;&#x27; &amp;&amp; .venv/bin/pytest tests/test1/test_crispy_buttons.py tests/test1/test_button_data.py tests/test1/test_label_mode.py tests/test1/test_action_label_mode_config.py tests/test1/test_button_classes.py -q&lt;/automated&gt; | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:189` |
| `self.inputs` | UNCHECKABLE | Address L-SUPPRESSION-MIGRATION explicitly in list_view.md and link the same recipe from the filter tutorial: clearing self.inputs or helper.inputs to [] after construction previously removed stock Apply/Reset because they lived there; after migration it only clears remaining legacy/hidden inputs and no longer suppresses layout actions. Show a ListViewFilterFormHelper subclass overriding get_form_actions(self) to return None, retaining its field layout and base constructor/hidden inputs. Do not infer omission from empty inputs, relocate user controls, or add a compatibility warning. In test_form_button_docs.py execute the documented omission subclass through {% crispy form helper %}, render twice, and assert its fields and named sort/order/direction hidden values remain while Apply/Reset are absent. Add the old clearing-inputs case as a changed-behavior regression: its stock layout actions remain, with no new warning; this demonstrates why the recipe is required rather than claiming backward-compatible suppression. Preserve D-01 through D-04. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-08-PLAN.md:102` |
| `self.value` | UNCHECKABLE | Add real crispy custom-template fixtures using an isolated template loader inside the test, including a subclass template and active pack substitution. Implement the spec collision policy for type/name/value/id/class/cancel/title/tooltip and ordinary underscore/hyphen aliases with exactly one final attribute. Preserve boolean True/False and underscore-to-hyphen extra attrs. For label/value/name/id/title and string attrs, test plain strings and marked-safe strings, literal {{ request.user }}, Unicode and lazy translated values under two language contexts. Assert decoded DOM text/value equal the originals and absence of injected attributes/nodes, not just escaped substrings. Ensure no mutation of self.value, shared field_classes, normalized input dicts, or outer Context; retain constructor-visible legacy behavior. An empty explicit template argument retains upstream truthy fallback semantics; valid explicit strings honor D-05–D-08. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-02-PLAN.md:123` |
| `setting_changed` | UNCHECKABLE | or explicit CrudViewsSettings arguments, not an invented setting_changed refresh; 06-03 proves the distinction. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:156`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:83` |
| `settings.md` | UNCHECKABLE | - docs/reference/settings.md | `docs/reference/settings.md:1` | `.planning/phases/06-form-button-leaf/06-02-PLAN.md:12`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:85`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:96`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:9`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:46`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:81`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:82`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:84`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:85` |
| `settings.py` | UNCHECKABLE | settings.py is initialized and the existing crud_views_settings singleton serves map reads, like context/list. | `examples/bootstrap5/project/settings.py:1`<br>`src/crud_views/lib/settings.py:1` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:154`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:8`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:41`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:73`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:74`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:8`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:77`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:78`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:19`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:42`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:114`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:115`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:82` |
| `src/crud_views/lib/button_classes.py` | UNCHECKABLE | - src/crud_views/lib/button_classes.py | `src/crud_views/lib/button_classes.py:1` | `.planning/phases/06-form-button-leaf/06-02-PLAN.md:10`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:85`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:32`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:41`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:74` |
| `src/crud_views/lib/crispy/buttons.py` | UNCHECKABLE | src/crud_views/lib/crispy/buttons.py; src/crud_views/lib/crispy/form.py; | `src/crud_views/lib/crispy/buttons.py:1` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:81`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:17`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:48`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:85`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:86`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:111`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:11`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:34`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:37`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:73`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:96`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:13`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:38`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:95`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:40` |
| `src/crud_views/lib/crispy/form.py` | UNCHECKABLE | src/crud_views/lib/crispy/buttons.py; src/crud_views/lib/crispy/form.py; | `src/crud_views/lib/crispy/form.py:1` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:81`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:11`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:37`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:95`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:96`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:103` |
| `src/crud_views/lib/formsets/layout.py` | UNCHECKABLE | - src/crud_views/lib/formsets/layout.py | `src/crud_views/lib/formsets/layout.py:1` | `.planning/phases/06-form-button-leaf/06-03-PLAN.md:14`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:96`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:97` |
| `src/crud_views/lib/icons.py` | UNCHECKABLE | - src/crud_views/lib/icons.py | `src/crud_views/lib/icons.py:1` | `.planning/phases/06-form-button-leaf/06-04-PLAN.md:8`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:30`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:73`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:74`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:14`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:102`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:103` |
| `src/crud_views/lib/settings.py` | UNCHECKABLE | - src/crud_views/lib/settings.py | `src/crud_views/lib/settings.py:1` | `.planning/phases/06-form-button-leaf/06-03-PLAN.md:8`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:41`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:73`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:74`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:8`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:77`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:78` |
| `src/crud_views/lib/view/action_menu.py` | UNCHECKABLE | - src/crud_views/lib/view/action_menu.py | `src/crud_views/lib/view/action_menu.py:1` | `.planning/phases/06-form-button-leaf/06-06-PLAN.md:11`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:40`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:77`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:78` |
| `src/crud_views/lib/view/base.py` | UNCHECKABLE | - src/crud_views/lib/view/base.py | `src/crud_views/lib/view/base.py:1` | `.planning/phases/06-form-button-leaf/06-03-PLAN.md:10`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:32`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:38`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:40`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:73`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:74`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:10`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:39`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:77`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:78`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:102` |
| `src/crud_views/lib/view/button_data.py` | UNCHECKABLE | src/crud_views/lib/view/button_data.py; src/crud_views/lib/view/label_mode.py; | `src/crud_views/lib/view/button_data.py:1` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:83`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:8`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:45`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:49`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:51`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:85`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:86`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:111`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:15`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:43`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:102`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:103` |
| `src/crud_views/lib/view/buttons.py` | UNCHECKABLE | - src/crud_views/lib/view/buttons.py | `src/crud_views/lib/view/buttons.py:1` | `.planning/phases/06-form-button-leaf/06-06-PLAN.md:13`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:36`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:42`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:102`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:103` |
| `src/crud_views/lib/view/label_mode.py` | UNCHECKABLE | src/crud_views/lib/view/button_data.py; src/crud_views/lib/view/label_mode.py; | `src/crud_views/lib/view/label_mode.py:1` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:83`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:9`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:85`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:86` |
| `src/crud_views/lib/views/list.py` | UNCHECKABLE | src/crud_views/lib/views/list.py; src/crud_views/lib/views/mixins.py; | `src/crud_views/lib/views/list.py:1` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:82`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:8`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:31`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:37`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:39`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:72`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:73`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:96`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:103` |
| `src/crud_views/lib/views/mixins.py` | UNCHECKABLE | src/crud_views/lib/views/list.py; src/crud_views/lib/views/mixins.py; | `src/crud_views/lib/views/mixins.py:1` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:82`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:36`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:73` |
| `src/crud_views/lib/viewset/__init__.py` | UNCHECKABLE | - src/crud_views/lib/viewset/__init__.py | `src/crud_views/lib/viewset/__init__.py:1` | `.planning/phases/06-form-button-leaf/06-03-PLAN.md:9`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:73`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:74`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:9`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:77`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:78` |
| `src/crud_views/static/crud_views/js/list.filter.js` | UNCHECKABLE | - src/crud_views/static/crud_views/js/list.filter.js | `src/crud_views/static/crud_views/js/list.filter.js:1` | `.planning/phases/06-form-button-leaf/06-07-PLAN.md:13`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:92`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:93` |
| `src/crud_views/static/crud_views/js/modal.js` | UNCHECKABLE | - src/crud_views/static/crud_views/js/modal.js | `src/crud_views/static/crud_views/js/modal.js:1` | `.planning/phases/06-form-button-leaf/06-07-PLAN.md:9`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:34`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:70`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:71` |
| `src/crud_views/static/crud_views/js/tooltip.js` | UNCHECKABLE | - src/crud_views/static/crud_views/js/tooltip.js | `src/crud_views/static/crud_views/js/tooltip.js:1` | `.planning/phases/06-form-button-leaf/06-08-PLAN.md:21`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:114` |
| `src/crud_views/static/crud_views/js/viewset.js` | UNCHECKABLE | - src/crud_views/static/crud_views/js/viewset.js | `src/crud_views/static/crud_views/js/viewset.js:1` | `.planning/phases/06-form-button-leaf/06-07-PLAN.md:12`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:92`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:93` |
| `src/crud_views/templates/crud_views/formsets/formset.html` | UNCHECKABLE | &lt;read_first&gt;06-SPEC.md ownership contract; installed crispy BasicNode.get_render/get_response_dict, FormActions.render and FormHelper.get_attributes; src/crud_views/lib/formsets/layout.py; src/crud_views/templatetags/crud_views_formsets.py; src/crud_views/templates/crud_views/formsets/formsets.html; src/crud_views/templates/crud_views/formsets/formset.html; Django InclusionNode.render; tests/test1/test_crispy_buttons.py&lt;/read_first&gt; | `src/crud_views/templates/crud_views/formsets/formset.html:1` | `.planning/phases/06-form-button-leaf/06-03-PLAN.md:97` |
| `src/crud_views/templates/crud_views/formsets/formsets.html` | UNCHECKABLE | &lt;read_first&gt;06-SPEC.md ownership contract; installed crispy BasicNode.get_render/get_response_dict, FormActions.render and FormHelper.get_attributes; src/crud_views/lib/formsets/layout.py; src/crud_views/templatetags/crud_views_formsets.py; src/crud_views/templates/crud_views/formsets/formsets.html; src/crud_views/templates/crud_views/formsets/formset.html; Django InclusionNode.render; tests/test1/test_crispy_buttons.py&lt;/read_first&gt; | `src/crud_views/templates/crud_views/formsets/formsets.html:1` | `.planning/phases/06-form-button-leaf/06-03-PLAN.md:97` |
| `src/crud_views/templates/crud_views/tags/button/action.html` | UNCHECKABLE | &lt;read_first&gt;06-01-SUMMARY.md in this phase directory; src/crud_views/templates/crud_views/tags/button/action.html; src/crud_views/lib/crispy/buttons.py; src/crud_views/lib/view/button_data.py; src/crud_views/lib/view/label_mode.py; tests/test1/test_crispy_buttons.py; tests/test1/test_button_leaves.py&lt;/read_first&gt; | `src/crud_views/templates/crud_views/tags/button/action.html:1` | `.planning/phases/06-form-button-leaf/06-02-PLAN.md:86`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:74` |
| `src/crud_views/templates/crud_views/tags/button/form.html` | EXCLUDED_NEW | - src/crud_views/templates/crud_views/tags/button/form.html | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-02-PLAN.md:18`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:43`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:52`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:79`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:85`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:9`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:40`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:73` |
| `src/crud_views/templatetags/crud_views_formsets.py` | UNCHECKABLE | - src/crud_views/templatetags/crud_views_formsets.py | `src/crud_views/templatetags/crud_views_formsets.py:1` | `.planning/phases/06-form-button-leaf/06-03-PLAN.md:15`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:96`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:97` |
| `src/crud_views_workflow/lib/forms.py` | UNCHECKABLE | - src/crud_views_workflow/lib/forms.py | `src/crud_views_workflow/lib/forms.py:1` | `.planning/phases/06-form-button-leaf/06-04-PLAN.md:12`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:34`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:95`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:96` |
| `strip` | UNCHECKABLE | &lt;automated&gt;.venv/bin/python -c &#x27;from pathlib import Path; import re; p=Path(&quot;.planning/phases/06-form-button-leaf/06-SPEC.md&quot;); s=p.read_text(); headings=(&quot;Prerequisite evidence&quot;, &quot;Form contract&quot;, &quot;Literal text and attributes&quot;, &quot;Template selection&quot;, &quot;Ownership&quot;, &quot;Helper lifecycle&quot;, &quot;Diagnostics and icons&quot;, &quot;Dependency validation&quot;, &quot;Golden history&quot;); sections={h: re.search(r&quot;(?m)^## &quot; + re.escape(h) + r&quot;\n([\s\S]*?)(?=^## &#124;\Z)&quot;, s) for h in headings}; assert all(m and m.group(1).strip() for m in sections.values()), &quot;Missing/empty design section&quot;; assert re.search(r&quot;\b[0-9a-f]{40}\b&quot;, sections[&quot;Prerequisite evidence&quot;].group(1)), &quot;Missing executing-branch HEAD SHA&quot;&#x27; &amp;&amp; .venv/bin/pytest tests/test1/test_crispy_buttons.py tests/test1/test_button_data.py tests/test1/test_label_mode.py tests/test1/test_action_label_mode_config.py tests/test1/test_button_classes.py -q&lt;/automated&gt; | `.venv/lib/python3.12/site-packages/django/utils/html.py:428` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:189` |
| `submit_icon` | EXCLUDED_NEW | - &quot;Repeated renders with different icon settings, forms and languages do not mutate shared class/icon defaults or retain another form&#x27;s submit_icon.&quot; | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-04-PLAN.md:28`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:68`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:99`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:104`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:109`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:116`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:118`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:140`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:201` |
| `superpowers/plans/2026-10-24-concept-review-followups.md` | UNCHECKABLE | superpowers/plans/2026-10-24-concept-review-followups.md (source Phase 2); | `superpowers/plans/2026-10-24-concept-review-followups.md:1` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:80` |
| `template_pack` | UNCHECKABLE | &#124; H-OVERLAY-PROVENANCE &#124; Rejected as a missing-API claim, not as a test obligation: installed BasicNode.get_response_dict supplies inputs/is_formset/template_pack metadata; no named provenance field is required. Task 2 and the pre-implementation spec retain the current-invocation/page-boundary proof and nested-row/None regressions; this single-reviewer unconfirmed HIGH does not authorize an ownership redesign or certify future implementation. &#124; | `.venv/lib/python3.12/site-packages/crispy_forms/templatetags/crispy_forms_tags.py:242`<br>`.venv/lib/python3.12/site-packages/crispy_forms/templatetags/crispy_forms_tags.py:252`<br>`.venv/lib/python3.12/site-packages/crispy_forms/templatetags/crispy_forms_tags.py:258`<br>`.venv/lib/python3.12/site-packages/crispy_forms/templatetags/crispy_forms_tags.py:262` | `.planning/phases/06-form-button-leaf/06-03-PLAN.md:147` |
| `test_action_label_mode_config.py` | UNCHECKABLE | tests/test1/test_action_label_mode_config.py tests/test1/test_button_classes.py -q; record the command, | `tests/test1/test_action_label_mode_config.py:1` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:91`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:189`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:14`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:85`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:96`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:102`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:12`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:73`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:74`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:87`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:113`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:78`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:93` |
| `test_button_classes.py` | UNCHECKABLE | tests/test1/test_action_label_mode_config.py tests/test1/test_button_classes.py -q; record the command, | `tests/test1/test_button_classes.py:1` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:91`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:189`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:13`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:85`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:97`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:102`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:86`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:89` |
| `test_button_classes_templates.py` | UNCHECKABLE | - tests/test1/test_button_classes_templates.py | `tests/test1/test_button_classes_templates.py:1` | `.planning/phases/06-form-button-leaf/06-02-PLAN.md:16`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:85`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:96`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:102` |
| `test_button_data.py` | UNCHECKABLE | &lt;automated&gt;.venv/bin/python -c &#x27;from pathlib import Path; import re; p=Path(&quot;.planning/phases/06-form-button-leaf/06-SPEC.md&quot;); s=p.read_text(); headings=(&quot;Prerequisite evidence&quot;, &quot;Form contract&quot;, &quot;Literal text and attributes&quot;, &quot;Template selection&quot;, &quot;Ownership&quot;, &quot;Helper lifecycle&quot;, &quot;Diagnostics and icons&quot;, &quot;Dependency validation&quot;, &quot;Golden history&quot;); sections={h: re.search(r&quot;(?m)^## &quot; + re.escape(h) + r&quot;\n([\s\S]*?)(?=^## &#124;\Z)&quot;, s) for h in headings}; assert all(m and m.group(1).strip() for m in sections.values()), &quot;Missing/empty design section&quot;; assert re.search(r&quot;\b[0-9a-f]{40}\b&quot;, sections[&quot;Prerequisite evidence&quot;].group(1)), &quot;Missing executing-branch HEAD SHA&quot;&#x27; &amp;&amp; .venv/bin/pytest tests/test1/test_crispy_buttons.py tests/test1/test_button_data.py tests/test1/test_label_mode.py tests/test1/test_action_label_mode_config.py tests/test1/test_button_classes.py -q&lt;/automated&gt; | `tests/test1/test_button_data.py:1` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:189`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:21`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:85`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:95`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:102`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:111`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:121`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:126`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:70`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:123` |
| `test_demo_pages_render_german` | UNCHECKABLE | For L-EXAMPLE-COVERAGE, run the separate example-consumer gate below from examples/bootstrap5 so its pytest.ini selects project.settings: all test_i18n.py cases (including test_demo_pages_render_german and its translated create-submit value), HomePageTest.test_every_feature_landing_page_renders, and all test_doc_links.py reference/backlink cases. Record their collected counts and results after 06-08 enables form=both. Root pytest tests does not include this example tree; SystemChecksTest and test_docs_sync alone cannot substitute. Retain those two existing gates as independent evidence. A failure is an acceptance blocker to route to the producing implementation/docs plan, not grounds to remove or relax the affected assertion. | `examples/bootstrap5/test_i18n.py:121` | `.planning/phases/06-form-button-leaf/06-09-PLAN.md:85` |
| `test_doc_links.py` | UNCHECKABLE | &lt;read_first&gt;examples/bootstrap5/project/settings.py; examples/bootstrap5/pytest.ini; examples/bootstrap5/test_i18n.py; examples/bootstrap5/project/tests.py (HomePageTest and SystemChecksTest); examples/bootstrap5/test_doc_links.py; docs/migrating-1.0.md Form buttons; 06-07-SUMMARY.md; 06-08-SUMMARY.md; 06-VALIDATION.md&lt;/read_first&gt; | `examples/bootstrap5/test_doc_links.py:1` | `.planning/phases/06-form-button-leaf/06-09-PLAN.md:82`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:85`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:245`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:271` |
| `test_docs_sync` | UNCHECKABLE | &lt;read_first&gt;CHANGELOG.md; docs/migrating-1.0.md; examples/bootstrap5/project/settings.py; examples/bootstrap5/test_docs_sync.py&lt;/read_first&gt; | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-08-PLAN.md:115`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:85`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:241` |
| `test_docs_sync.py` | UNCHECKABLE | &lt;read_first&gt;CHANGELOG.md; docs/migrating-1.0.md; examples/bootstrap5/project/settings.py; examples/bootstrap5/test_docs_sync.py&lt;/read_first&gt; | `examples/bootstrap5/test_docs_sync.py:1` | `.planning/phases/06-form-button-leaf/06-08-PLAN.md:115`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:241` |
| `test_form_button_baselines` | EXCLUDED_NEW | tests/test1/golden/form_buttons/*.html files enumerated above. NEW test symbol: test_form_button_baselines. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:67` |
| `test_form_button_checks.py` | EXCLUDED_NEW | - tests/test1/test_form_button_checks.py | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-06-PLAN.md:12`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:34`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:70`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:77`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:93`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:102`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:120`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:123`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:113`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:34` |
| `test_form_button_docs.py` | EXCLUDED_NEW | - tests/test1/test_form_button_docs.py | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-08-PLAN.md:16`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:40`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:49`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:76`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:98`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:102`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:105` |
| `test_i18n.py` | UNCHECKABLE | &lt;read_first&gt;examples/bootstrap5/project/settings.py; examples/bootstrap5/pytest.ini; examples/bootstrap5/test_i18n.py; examples/bootstrap5/project/tests.py (HomePageTest and SystemChecksTest); examples/bootstrap5/test_doc_links.py; docs/migrating-1.0.md Form buttons; 06-07-SUMMARY.md; 06-08-SUMMARY.md; 06-VALIDATION.md&lt;/read_first&gt; | `examples/bootstrap5/test_i18n.py:1`<br>`tests/test1/test_i18n.py:1` | `.planning/phases/06-form-button-leaf/06-09-PLAN.md:82`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:85`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:245`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:271` |
| `test_label_mode.py` | UNCHECKABLE | VARIANT_LOCATIONS. Before authoring the spec, run .venv/bin/pytest tests/test1/test_label_mode.py | `tests/test1/test_label_mode.py:1` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:90`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:189`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:20`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:85`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:95`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:111`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:121`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:126`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:93` |
| `test_label_mode_docs.py` | UNCHECKABLE | - tests/test1/test_label_mode_docs.py | `tests/test1/test_label_mode_docs.py:1` | `.planning/phases/06-form-button-leaf/06-02-PLAN.md:15`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:85`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:96`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:102`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:11`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:81`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:82`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:89` |
| `tests/docs` | UNCHECKABLE | &#124; H-KEYSET / H-EARLY-UTILITIES &#124; HIGH &#124; Utility defaults and exhaustive tests/docs move together to 06-02 task 1; this plan consumes them and expands real icon/host coverage without a second key addition. &#124; | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-04-PLAN.md:123`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:139` |
| `tests/js/helpers/setup.js` | UNCHECKABLE | &lt;read_first&gt;package.json; package-lock.json; vitest.config.js; tests/js/modal.test.js; tests/js/helpers/setup.js; src/crud_views/static/crud_views/js/modal.js; 06-RESEARCH.md Package Legitimacy Audit&lt;/read_first&gt; | `tests/js/helpers/setup.js:1` | `.planning/phases/06-form-button-leaf/06-07-PLAN.md:71` |
| `tests/js/list.filter.test.js` | UNCHECKABLE | - tests/js/list.filter.test.js | `tests/js/list.filter.test.js:1` | `.planning/phases/06-form-button-leaf/06-07-PLAN.md:11`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:92`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:93`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:103` |
| `tests/js/modal.test.js` | UNCHECKABLE | - tests/js/modal.test.js | `tests/js/modal.test.js:1` | `.planning/phases/06-form-button-leaf/06-07-PLAN.md:8`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:29`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:35`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:70`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:71`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:83` |
| `tests/js/viewset.test.js` | UNCHECKABLE | - tests/js/viewset.test.js | `tests/js/viewset.test.js:1` | `.planning/phases/06-form-button-leaf/06-07-PLAN.md:10`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:92`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:93`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:103` |
| `tests/test1/app/views.py` | UNCHECKABLE | &lt;read_first&gt;tests/test1/test_workflow.py; tests/test1/test_filter.py; tests/test1/app/views.py; .planning/phases/06-form-button-leaf/06-SPEC.md&lt;/read_first&gt; | `tests/test1/app/views.py:1` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:226` |
| `tests/test1/conftest.py` | UNCHECKABLE | &lt;read_first&gt;tests/test1/test_crispy_buttons.py; tests/test1/test_crud.py; tests/test1/conftest.py; tests/test1/test_pagination_docs.py; .planning/phases/06-form-button-leaf/06-SPEC.md&lt;/read_first&gt; | `tests/test1/conftest.py:1` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:199` |
| `tests/test1/golden/form_buttons/*.html` | EXCLUDED_NEW | tests/test1/golden/form_buttons/*.html files enumerated above. NEW test symbol: test_form_button_baselines. | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:67` |
| `tests/test1/golden/form_buttons/create.html` | EXCLUDED_NEW | - tests/test1/golden/form_buttons/create.html | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:12`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:37`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:198`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:23`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:135` |
| `tests/test1/golden/form_buttons/delete.html` | EXCLUDED_NEW | - tests/test1/golden/form_buttons/delete.html | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:14`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:198`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:25`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:135` |
| `tests/test1/golden/form_buttons/filter.html` | EXCLUDED_NEW | - tests/test1/golden/form_buttons/filter.html | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:16`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:225`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:12`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:72` |
| `tests/test1/golden/form_buttons/update.html` | EXCLUDED_NEW | - tests/test1/golden/form_buttons/update.html | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:13`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:198`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:24`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:135` |
| `tests/test1/golden/form_buttons/workflow.html` | EXCLUDED_NEW | - tests/test1/golden/form_buttons/workflow.html | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:15`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:225`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:26`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:135` |
| `tests/test1/test_action_label_mode_config.py` | UNCHECKABLE | tests/test1/test_action_label_mode_config.py tests/test1/test_button_classes.py -q; record the command, | `tests/test1/test_action_label_mode_config.py:1` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:91`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:189`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:14`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:85`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:102`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:12`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:73`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:74`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:87`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:113`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:78`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:93` |
| `tests/test1/test_button_classes.py` | UNCHECKABLE | tests/test1/test_action_label_mode_config.py tests/test1/test_button_classes.py -q; record the command, | `tests/test1/test_button_classes.py:1` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:91`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:189`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:13`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:85`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:102`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:86`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:89` |
| `tests/test1/test_button_classes_templates.py` | UNCHECKABLE | - tests/test1/test_button_classes_templates.py | `tests/test1/test_button_classes_templates.py:1` | `.planning/phases/06-form-button-leaf/06-02-PLAN.md:16`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:85`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:102` |
| `tests/test1/test_button_data.py` | UNCHECKABLE | &lt;automated&gt;.venv/bin/python -c &#x27;from pathlib import Path; import re; p=Path(&quot;.planning/phases/06-form-button-leaf/06-SPEC.md&quot;); s=p.read_text(); headings=(&quot;Prerequisite evidence&quot;, &quot;Form contract&quot;, &quot;Literal text and attributes&quot;, &quot;Template selection&quot;, &quot;Ownership&quot;, &quot;Helper lifecycle&quot;, &quot;Diagnostics and icons&quot;, &quot;Dependency validation&quot;, &quot;Golden history&quot;); sections={h: re.search(r&quot;(?m)^## &quot; + re.escape(h) + r&quot;\n([\s\S]*?)(?=^## &#124;\Z)&quot;, s) for h in headings}; assert all(m and m.group(1).strip() for m in sections.values()), &quot;Missing/empty design section&quot;; assert re.search(r&quot;\b[0-9a-f]{40}\b&quot;, sections[&quot;Prerequisite evidence&quot;].group(1)), &quot;Missing executing-branch HEAD SHA&quot;&#x27; &amp;&amp; .venv/bin/pytest tests/test1/test_crispy_buttons.py tests/test1/test_button_data.py tests/test1/test_label_mode.py tests/test1/test_action_label_mode_config.py tests/test1/test_button_classes.py -q&lt;/automated&gt; | `tests/test1/test_button_data.py:1` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:189`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:21`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:85`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:102`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:111`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:126`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:123` |
| `tests/test1/test_button_leaves.py` | UNCHECKABLE | &lt;read_first&gt;06-01-SUMMARY.md in this phase directory; src/crud_views/templates/crud_views/tags/button/action.html; src/crud_views/lib/crispy/buttons.py; src/crud_views/lib/view/button_data.py; src/crud_views/lib/view/label_mode.py; tests/test1/test_crispy_buttons.py; tests/test1/test_button_leaves.py&lt;/read_first&gt; | `tests/test1/test_button_leaves.py:1` | `.planning/phases/06-form-button-leaf/06-02-PLAN.md:86`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:112` |
| `tests/test1/test_cancel_origin.py` | UNCHECKABLE | &lt;read_first&gt;06-01-SUMMARY.md in this phase directory; tests/test1/test_form_buttons_golden.py; tests/test1/test_crud.py; tests/test1/test_cancel_origin.py&lt;/read_first&gt; | `tests/test1/test_cancel_origin.py:1` | `.planning/phases/06-form-button-leaf/06-02-PLAN.md:136`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:141`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:67` |
| `tests/test1/test_crispy_buttons.py` | UNCHECKABLE | &lt;automated&gt;.venv/bin/python -c &#x27;from pathlib import Path; import re; p=Path(&quot;.planning/phases/06-form-button-leaf/06-SPEC.md&quot;); s=p.read_text(); headings=(&quot;Prerequisite evidence&quot;, &quot;Form contract&quot;, &quot;Literal text and attributes&quot;, &quot;Template selection&quot;, &quot;Ownership&quot;, &quot;Helper lifecycle&quot;, &quot;Diagnostics and icons&quot;, &quot;Dependency validation&quot;, &quot;Golden history&quot;); sections={h: re.search(r&quot;(?m)^## &quot; + re.escape(h) + r&quot;\n([\s\S]*?)(?=^## &#124;\Z)&quot;, s) for h in headings}; assert all(m and m.group(1).strip() for m in sections.values()), &quot;Missing/empty design section&quot;; assert re.search(r&quot;\b[0-9a-f]{40}\b&quot;, sections[&quot;Prerequisite evidence&quot;].group(1)), &quot;Missing executing-branch HEAD SHA&quot;&#x27; &amp;&amp; .venv/bin/pytest tests/test1/test_crispy_buttons.py tests/test1/test_button_data.py tests/test1/test_label_mode.py tests/test1/test_action_label_mode_config.py tests/test1/test_button_classes.py -q&lt;/automated&gt; | `tests/test1/test_crispy_buttons.py:1` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:189`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:199`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:19`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:85`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:86`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:102`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:111`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:126`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:13`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:87`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:96`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:97`<br>`.planning/phases/06-form-button-leaf/06-03-PLAN.md:113`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:14`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:95`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:96`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:107`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:10`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:72`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:87`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:96`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:97`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:112`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:38`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:113` |
| `tests/test1/test_crud.py` | UNCHECKABLE | &lt;read_first&gt;tests/test1/test_crispy_buttons.py; tests/test1/test_crud.py; tests/test1/conftest.py; tests/test1/test_pagination_docs.py; .planning/phases/06-form-button-leaf/06-SPEC.md&lt;/read_first&gt; | `tests/test1/test_crud.py:1` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:199`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:206`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:216`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:136`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:141`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:67` |
| `tests/test1/test_filter.py` | UNCHECKABLE | &lt;read_first&gt;tests/test1/test_workflow.py; tests/test1/test_filter.py; tests/test1/app/views.py; .planning/phases/06-form-button-leaf/06-SPEC.md&lt;/read_first&gt; | `tests/test1/test_filter.py:1` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:226`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:237`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:9`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:33`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:72`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:73`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:87`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:96`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:97`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:112`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:113` |
| `tests/test1/test_form_button_checks.py` | EXCLUDED_NEW | - tests/test1/test_form_button_checks.py | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-06-PLAN.md:12`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:34`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:70`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:77`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:93`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:102`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:123`<br>`.planning/phases/06-form-button-leaf/06-07-PLAN.md:113`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:34` |
| `tests/test1/test_form_button_docs.py` | EXCLUDED_NEW | - tests/test1/test_form_button_docs.py | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-08-PLAN.md:16`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:40`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:49`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:76`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:98`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:105` |
| `tests/test1/test_form_buttons_golden.py` | EXCLUDED_NEW | - tests/test1/test_form_buttons_golden.py | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:11`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:33`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:36`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:66`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:198`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:216`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:225`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:237`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:22`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:135`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:136`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:141`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:11`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:72`<br>`.planning/phases/06-form-button-leaf/06-05-PLAN.md:87`<br>`.planning/phases/06-form-button-leaf/06-09-PLAN.md:31` |
| `tests/test1/test_icon_host_leaves.py` | UNCHECKABLE | - tests/test1/test_icon_host_leaves.py | `tests/test1/test_icon_host_leaves.py:1` | `.planning/phases/06-form-button-leaf/06-04-PLAN.md:10`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:73`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:74`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:86`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:103` |
| `tests/test1/test_icons_registry.py` | UNCHECKABLE | &lt;read_first&gt;src/crud_views/lib/button_classes.py; src/crud_views/lib/icons.py; tests/test1/test_icon_host_leaves.py; tests/test1/test_icons_registry.py; src/crud_views/templates/crud_views/tags/button/action.html&lt;/read_first&gt; | `tests/test1/test_icons_registry.py:1` | `.planning/phases/06-form-button-leaf/06-04-PLAN.md:74`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:86`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:107` |
| `tests/test1/test_label_mode.py` | UNCHECKABLE | VARIANT_LOCATIONS. Before authoring the spec, run .venv/bin/pytest tests/test1/test_label_mode.py | `tests/test1/test_label_mode.py:1` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:90`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:189`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:20`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:85`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:111`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:126`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:93` |
| `tests/test1/test_label_mode_docs.py` | UNCHECKABLE | - tests/test1/test_label_mode_docs.py | `tests/test1/test_label_mode_docs.py:1` | `.planning/phases/06-form-button-leaf/06-02-PLAN.md:15`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:85`<br>`.planning/phases/06-form-button-leaf/06-02-PLAN.md:102`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:11`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:81`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:82`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:89` |
| `tests/test1/test_pagination_docs.py` | UNCHECKABLE | &lt;read_first&gt;tests/test1/test_crispy_buttons.py; tests/test1/test_crud.py; tests/test1/conftest.py; tests/test1/test_pagination_docs.py; .planning/phases/06-form-button-leaf/06-SPEC.md&lt;/read_first&gt; | `tests/test1/test_pagination_docs.py:1` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:199`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:99` |
| `tests/test1/test_workflow.py` | UNCHECKABLE | &lt;read_first&gt;tests/test1/test_workflow.py; tests/test1/test_filter.py; tests/test1/app/views.py; .planning/phases/06-form-button-leaf/06-SPEC.md&lt;/read_first&gt; | `tests/test1/test_workflow.py:1` | `.planning/phases/06-form-button-leaf/06-01-PLAN.md:226`<br>`.planning/phases/06-form-button-leaf/06-01-PLAN.md:237`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:96`<br>`.planning/phases/06-form-button-leaf/06-04-PLAN.md:107` |
| `tooltip.js` | UNCHECKABLE | - src/crud_views/static/crud_views/js/tooltip.js | `src/crud_views/static/crud_views/js/tooltip.js:1` | `.planning/phases/06-form-button-leaf/06-08-PLAN.md:21`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:114`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:119`<br>`.planning/phases/06-form-button-leaf/06-08-PLAN.md:141` |
| `uni_form.html` | UNCHECKABLE | For the explicit empty-layout plus None-hook case, assert the helper&#x27;s selected layout stays empty and no action group appears. Preserve the installed pack&#x27;s display_form.html fallback to uni_form.html when form_html is empty; this package-helper fix does not promise suppression of that existing pack-owned field fallback or add a global template override. The default-action case has nonempty layout output and must not restore discarded fields. | `.venv/lib/python3.12/site-packages/crispy_bootstrap5/templates/bootstrap5/uni_form.html:1` | `.planning/phases/06-form-button-leaf/06-05-PLAN.md:109` |
| `view/buttons.py` | UNCHECKABLE | - src/crud_views/lib/view/buttons.py | No independent declaration asserted. | `.planning/phases/06-form-button-leaf/06-06-PLAN.md:13`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:36`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:42`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:70`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:102`<br>`.planning/phases/06-form-button-leaf/06-06-PLAN.md:103` |
| `vitest.config.js` | UNCHECKABLE | &lt;read_first&gt;package.json; package-lock.json; vitest.config.js; tests/js/modal.test.js; tests/js/helpers/setup.js; src/crud_views/static/crud_views/js/modal.js; 06-RESEARCH.md Package Legitimacy Audit&lt;/read_first&gt; | `vitest.config.js:1` | `.planning/phases/06-form-button-leaf/06-07-PLAN.md:71` |

## Previous Review History

<details>
<summary>Previous cycle 3 report and subsequent manual disposition, preserved for audit</summary>


## Manual disposition after cycle 3

The user selected manual revision after this review (snapshot fcc404f). All four findings below are now
incorporated into executable plan tasks and acceptance evidence: H-HELPER-TRUTHINESS in 06-01/05;
M-OUTER-HELPER-PAGE and L-FORMSET-PAGE-CONTEXT in 06-01/03; L-UNREGISTERED-FORM-ICON in 06-01/06.
06-09 and VALIDATION require their execution evidence. Original reviewer text and counts are preserved.
These revisions have not been externally re-reviewed, implemented or accepted as converged.


## Reviewer Execution Record

Reviewed committed plan set `be0aa152408023b669a0a4a1c23f2ffcd36f8b08`, convergence cycle 3. Configured reviewers, pinned models, high effort and canonical lane invocation were preserved. Configured parallel dispatch was used. No plan, product, state, configuration, or runtime source was edited.

| Reviewer | Result | Plan coverage | Evidence |
|---|---|---|---|
| fable-review | Real external review | 9/9 | Source citations present |
| grok-review | Real external review | 9/9 | Source citations present |
| gemini-review | Real external review | 9/9 | Source citations present |

Gemini attempt 1 timed out at 1200000ms: ETIMEDOUT, stop reason tool-calls, 66 output tokens, no assistant review text. The one bounded retry used the identical prompt/model/runner and timeout. A process-local CommonJS wrapper changed only the resolved timeout (the installed runner consumes plan.timeoutMs); no runtime/configuration files were changed. The shorter 660000ms failure pattern had already occurred in both prior cycles. Failed-attempt diagnostics are retained and never count as reviewer approval.

The writer-owned conflict block above is preserved byte-for-byte (SHA256 `03f805c366d031be9c6450c8231af0fef5f5db27e2e6536b5d018c9b3505b0be`); it contains no open conflict.


## Claude Review (fable-review)

Verification is complete. I confirmed the installed crispy dispatch path, the settings singleton lifecycle, the icon registry, the JS lock, the example tests, and the test-app helper patterns. Writing the review now.

# Phase 06 plan review, convergence cycle 3 (be0aa15)

Reviewed against the working tree at `be0aa152408023b669a0a4a1c23f2ffcd36f8b08`, django-crispy-forms 2.6, crispy-bootstrap5 2026.3, Django 5.2.14, Node 20.20.2. All nine plans were read against source. One new HIGH defect was found in the mechanism the plans use to close M-EMPTY-REPLACEMENT. The other four prior findings are closed by executable actions. Git branch commands required approval in this session, so the D-18 prerequisite was checked on the working tree's source instead of on commit history.

## 06-01

### 1. Summary
The plan correctly gates the spec on the Phase 1/2 contracts, which are present on the working tree: `default_label_mode` with the lazy floor at `src/crud_views/lib/view/label_mode.py:84-117` and the finite `FORM_KINDS` / `VARIANT_LOCATIONS` split at `src/crud_views/lib/button_classes.py:209-228`. The five pytest files named in the Task 1 verify exist. The baseline protocol (commit goldens with `git diff BASELINE^ BASELINE -- src` empty) is sound. The spec section list carries the Round 2 closures, but one of those recorded mechanisms is wrong (see Concerns).

### 2. Strengths
- D-18 prerequisite is checkable on source, not on a branch name: `label_mode.py:93-96` reads `LOCATIONS` from `button_data`, and `button_classes.py:225` encodes the Option A grammar. Both are what Phase 6 depends on.
- Task 2's new POST `{"confirm": True, "delete": "Delete"}` is valid against `src/crud_views/lib/views/delete.py:199-216`: `post()` only requires a valid form, so the extra submitter key is accepted and the redirect path is exercised. The existing confirmation-only test at `tests/test1/test_crud.py:63` stays untouched, as M-PAYLOAD required.
- Task 1's M-NAME rule matches the pack exactly: `crispy_bootstrap5/templates/bootstrap5/layout/baseinput.html` emits `name` via `wordcount > 1` then `slugify`, and the ID is generated once in `BaseInput.__init__` (`crispy_forms/layout.py:237-241`).
- Task 1's claim that `FormActions.render` leaves context layers behind is correct: `crispy_forms/bootstrap.py:309` does `context.update(...)` with no pop, and `KeepContext` (`crispy_forms/base.py:19-22`) only deletes `extra_context` keys, which are empty for layout objects.
- Research's JS discrepancy is real: `package-lock.json:799` locks jsdom 30.1.2 with engines `^22.22.2 || ^24.15.0 || >=26.0.0`, `package-lock.json:1506/1530` locks vitest 5.0.3 with `^22.12.0 || ^24.0.0 || >=26.0.0`, while `node_modules` holds jsdom 29.1.1 and vitest 4.1.10 and the runtime is Node 20.20.2.

### 3. Concerns
- **HIGH, H-HELPER-TRUTHINESS.** The spec's Helper lifecycle section is told to record "A no-layout helper gets a truthy instance Layout so crispy calls render_layout" and, for M-EMPTY-REPLACEMENT, to "normalize an explicitly empty Layout to a private truthy instance layout". That mechanism cannot pass the dispatch guard. `crispy_forms/templatetags/crispy_forms_tags.py:116` reads `if helper and helper.layout:`. The helper is evaluated first, and `FormHelper` has no `__bool__`; it inherits `DynamicLayoutHandler.__len__` at `crispy_forms/helper.py:99-103`, which returns `len(self.layout.fields)`. For an empty-fields layout the helper is falsy, the `and` short-circuits, and the layout's `__bool__` is never consulted. `render_layout` is skipped and `display_form.html` falls back to `uni_form.html`. The spec must record a helper-level truthiness override (or field population before the guard), not a layout-level one. Details under 06-05.
- **MEDIUM, nested-row page owner.** The spec is told to recover "the nearest non-None lower page view" below the current crispy overlay. Every public helper attribute, including `view`, is copied into that overlay by `crispy_forms/helper.py:340-346` and pushed by `crispy_forms_tags.py:112`. For a formset row (`src/crud_views/templates/crud_views/formsets/formset.html:42`) rendered inside an outer crispy form, the "nearest non-None lower view" can be the outer helper's `view`, not the page's. The spec must say whether an outer helper overlay counts as page under D-09 or is skipped. This is a definition gap in the current design, independent of the rejected H-OVERLAY-PROVENANCE existence premise.
- **LOW, scope.** Task 1 is the only task in the phase that downloads and verifies an external artifact (an official Node archive) inside a spec-and-goldens plan. The plan does allow recording a blocker, which is the right escape hatch; keep that path cheap so the spec and baselines are not held hostage by network access.
- **LOW.** The spec's literal-text rule says "plain str that has no SafeData trust marker". `str(SafeString(...))` returns the same SafeString because `SafeString.__str__` returns `self`, which the research notes. The spec should name a concrete demotion (for example `str.__str__(value)` or `f"{value!s}"` via `str.__format__`) so the implementer does not use `str()`.

### 4. Suggestions
- In the Helper lifecycle section, write: `ListViewFilterFormHelper.__bool__` returns True (or `__len__` returns a nonzero value independent of fields), and the instance layout is also truthy. Cite `helper.py:99-103` and `crispy_forms_tags.py:116`.
- In the Ownership section, define "page view" as the first non-None `view` in a `Context.dicts` entry that is not a crispy response overlay (one lacking `is_formset`/`template_pack`), and add that case to the 06-03 regressions.
- Record the demotion idiom for SafeString and lazy values in Literal text and attributes.

### 5. Risk Assessment
MEDIUM. The prerequisite and baseline mechanics are correct and verifiable, but the spec is told to record one wrong lifecycle mechanism that 06-05 then builds on.

## 06-02

### 1. Summary
This is the critical producing tracer, and its atomic ownership of `LOCATIONS`, defaults, E108 consumers, the two utility keys, and the exhaustive key set is correct. Every consumer the plan names was verified as a real breakage point. The adapter design (bypass `BaseInput.render`, strip the `input` alias, normalize then autoescape once) matches the installed source.

### 2. Strengths
- `BaseInput.render` at `crispy_forms/layout.py:250-259` compiles `str(self.value)` as a Template and injects `input` into the context. Bypassing it is required, and the plan does so.
- The atomic consumer list is accurate: `tests/test1/test_action_label_mode_config.py:278` hardcodes `E108_LOCATIONS = "['card', 'context', 'list']"` and `:323` expects `{"form": "both"}` to be an E108 error; `tests/test1/test_label_mode.py:67` asserts `set(LABEL_MODE_DEFAULTS) == LOCATIONS` and `:137` parametrizes `"form"` as an invalid location; `tests/test1/test_button_classes_templates.py:214` iterates `sorted(LOCATIONS)` through the action chain. All three break the moment `"form"` lands, exactly as H-LOCATIONS said.
- Key count arithmetic is right: `tests/test1/test_button_classes.py:90` asserts 71, `docs/reference/buttons.md:145-146` says 71 and "the `*:icon-host` row for four"; adding `form:hidden-label` and `form:icon-host` makes 73 and five host keys, and `test_button_classes.py:97-101` parses the doc sentence.
- `icon_host_keys(icon, "form")` at `button_data.py:41-49` calls `get_icon_host_class("form", ...)`, which needs `form:icon-host` to exist (`button_classes.py:152-165`). Delivering the key in the same task as the leaf is correct, closing H-EARLY-UTILITIES.
- Boolean and underscore attribute semantics are inherited for free: crispy `flatatt` (`crispy_forms/utils.py:142-149`) delegates to Django's `flatatt`, which handles True/False and uses `conditional_escape`. The plan's rule to demote SafeString before serialization is therefore necessary and sufficient.
- Slot rejection on the layout path is safe for package code: the only `slot=` uses in `src/` are `list.py:71` (`form:filter-submit`) and `form.py:130` (`form:delete`), both finite kinds.

### 3. Concerns
- **LOW.** `tests/test1/test_button_data.py:9` declares a local `LOCATIONS = ["context", "list", "card"]` list used by 18 parametrized tests. It is not the real set, so adding `"form"` does not break it, but the plan's "update test_button_data.py location/default assertions" should state that this local list stays action-only and that form contract cases get their own parametrization, so an executor does not "fix" it by appending `"form"` and feed action contexts into the form branch.
- **LOW.** Task 1 says "Missing or None textual values normalize to empty text" while `cv_button_data` today forces `label_mode = "icon"` when the label is empty (`button_data.py:95-96`). The form branch must not inherit that line, or an empty-label form button silently becomes icon mode and then trips the missing-icon policy. The plan's "Preserve valid empty labels without manufacturing text" implies this, but the branch point should be named explicitly.

### 4. Suggestions
- State that the form branch returns before `button_data.py:95` and never applies the empty-label-to-icon rule.
- Name `test_button_data.py:9` as a deliberately action-only list in the task text.

### 5. Risk Assessment
MEDIUM. Largest blast radius in the phase, but every breakage point is enumerated and owned in the producing task.

## 06-03

### 1. Summary
M-SETTINGS-LIFECYCLE is closed correctly. The plan's description of the lifecycle matches source: `from_settings` at `src/crud_views/lib/settings.py:13-14` is evaluated as a Pydantic field default at class definition, the singleton is created at `settings.py:320`, and there is no `setting_changed` receiver in `settings.py` (the only receivers are in `button_classes.py:113` and `icons.py:111`). Existing tests mutate the singleton via `monkeypatch.setattr(crud_views_settings, ...)` at `tests/test1/test_action_label_mode_config.py:78-80`, which is the pattern the plan adopts. The whole-map resolver at `src/crud_views/lib/view/base.py:263-272` is the right seam.

### 2. Strengths
- The planned real-render proof (map-only `override_settings` leaves submit in `both`, nested floor override changes only the unmapped cancel) is exactly the distinction between the snapshot map and the lazy floor at `label_mode.py:54-58`.
- `cv_get_action_label_mode` raises for any location other than context/list (`base.py:329`), so the plan's explicit form support there is required, not optional.
- The existing `ViewSet` validator at `src/crud_views/lib/viewset/__init__.py:105-111` is the right place for the third map field.
- Task 2 correctly refuses fixed stack offsets: `bootstrap.py:309` and `layout.py:257` both push layers that are never popped, so offsets drift with every `FormActions` and every button.

### 3. Concerns
- **MEDIUM, same as 06-01's nested-row concern.** "Nearest non-None lower page view" is underspecified when the lower dict is another crispy overlay. `helper.py:340-346` publishes `view` from any helper that sets it. For package forms the outer `FormHelper()` has no `view`, so today's package paths are unaffected, but a custom row helper with a `view` attribute would be chosen as "page". Task 2's regression list ("outer form, row form, helper and page conflicting modes") should include the outer-helper-has-view case and assert the intended winner.
- **LOW.** The plan says invalid selected map values use "shared strict/log fallback rather than membership crashes". For context/list, `base.py:313-328` returns the mapped value as configured and lets the leaf validate it (`button_data.py:88-94`), which `test_action_label_mode_config.py:162-172` pins. The form resolver should follow that exact division (resolver returns, normalizer validates) so diagnostics stay in one place.

### 4. Suggestions
- Add the outer-helper-with-`view` row regression to Task 2 and decide its outcome in the spec.
- Mirror `base.py:323-328` membership-then-floor verbatim for form, including the comment about never using `dict.get` with a floor default.

### 5. Risk Assessment
MEDIUM. Lifecycle closure is sound; ownership definition has one unresolved edge that the spec must settle before Task 2 can be written.

## 06-04

### 1. Summary
Registry and icon-precedence work is accurately scoped. `save`, `cancel` and `filter-reset` are absent from both `DEFAULT_ICONS` (`src/crud_views/lib/icons.py:14-49`) and `BOOTSTRAP_ICONS` (`icons.py:51-89`); `delete`, `workflow` and `filter` exist. The workflow form at `src/crud_views_workflow/lib/forms.py:11-20` only overrides `submit_label`, so a `submit_icon = "workflow"` class default is the minimal change.

### 2. Strengths
- Kind-from-slot, not from name, is already how the delete hook works (`form.py:130` passes `slot="form:delete"` with `name="delete"`), and `tests/test1/test_crispy_buttons.py:62-73` pins the slot override case the plan reuses.
- The leaf conventions to copy are concrete: `src/crud_views/templates/crud_views/tags/button/action.html:7-8` has the title/tooltip and three-body branches.
- Correctly consumes the keys delivered by 06-02 instead of adding them twice.

### 3. Concerns
- **LOW.** Task 2's sentinel `icon=` keyword on the adapters must be popped from kwargs before `BaseInput.__init__` (`layout.py:248`) or it is serialized as an `icon="..."` attribute by `flatatt`. The plan says it is "never serialized", so name the pop in the task.
- **LOW.** Host-placed form icons: `icon_host_keys` returns `("", True)` for a non-host icon and `(class, False)` for host (`button_data.py:41-49`). The leaf must gate the inline `cv_icon` call on `cv_icon_inline`, like `action.html:8`; the plan says so, but the test fixture at `tests/lib/helper/icons.py:3-13` maps no form-kind names, so the host tests must register `save`/`cancel`/`filter-reset` host entries explicitly.

### 4. Suggestions
- Add "pop `icon` before `super().__init__`" to Task 2 and a test that `icon=` never appears in `cv_flat_attrs`.
- Extend `HOST_ICONS` in the test helper (or a local override) with the five form kinds.

### 5. Risk Assessment
LOW.

## 06-05

### 1. Summary
This plan carries the HIGH defect. Its source analysis is otherwise correct: `FormHelper.__init__(form)` replaces a declared layout (`helper.py:212-214`), `get_attributes` runs inside `get_response_dict` before the guard (`crispy_forms_tags.py:109,147` then `:116`), public helper attributes leak into the context (`helper.py:340-346`), and the pack renders `inputs.html` after `display_form.html` (`whole_uni_form.html`), so the hidden-input wrapper follows the layout. The class-level shared layout hazard is real in the test app: `tests/test1/app/views.py:288-289` declares `layout = Layout(Row(Column4("name")))` and three views share it (`:303, :374, :393`).

### 2. Strengths
- The constructor convention is preserved: `src/crud_views/lib/views/mixins.py:319` calls `formhelper_class(request=..., view=...)` with no form, matching `list.py:65`.
- Underscore-prefixed lifecycle state is the correct way to stay out of the overlay (`helper.py:344`).
- L-SUPPRESSION-MIGRATION is accurately dispositioned: today Apply/Reset live in `inputs` (`list.py:70-73`), so clearing `inputs` removed them; after the move it removes only hidden controls.
- L-HIDDEN-WRAPPER acceptance matches the pack: `inputs.html` renders its own `mb-3` wrapper after the layout.

### 3. Concerns
- **HIGH, H-HELPER-TRUTHINESS.** Task 1: "Keep a truthy instance layout before crispy dispatch even for no-layout or None actions; a private Layout subclass with `__bool__` returning True is a concrete option." Task 1 (M-EMPTY-REPLACEMENT): "normalize an explicitly empty Layout to a private truthy instance layout preserving its empty field selection; appending actions remains render_layout's job." The guard at `crispy_forms_tags.py:116` is `if helper and helper.layout:`. `helper` is tested first. `FormHelper` defines no `__bool__`; `DynamicLayoutHandler.__len__` at `helper.py:99-103` returns `len(self.layout.fields)`. So:
  - Explicit `Layout()` replacement plus default actions: at guard time `fields == []`, `len(helper) == 0`, `helper` is falsy, `render_layout` never runs, and `display_form.html` falls into `uni_form.html`, which re-renders every form field. The must_have "receives one default action group without restoring discarded fields" is violated by the designed mechanism, not just untested.
  - No-layout helper with fields populated at `render_layout`: same failure, because the prepared layout is empty at guard time. The helper cannot populate fields in `get_attributes` either, since it has no form (`mixins.py:319`) and `get_attributes(template_pack)` receives none.
  - The layout-level `__bool__` is never evaluated in either case.
  The plan's `fails_when` ("an empty replacement bypasses render_layout") would catch this at execution, but the executor is handed a wrong "concrete option" and no correct one. Fix: define `__bool__` on `ListViewFilterFormHelper` returning True (or override `__len__` to count the prepared action group), and keep `helper.layout` truthy as well. Note `{% if form.helper %}` at `src/crud_views/templates/crud_views/tags/form.html:3` also relies on helper truthiness; a `__bool__` override on the filter helper does not touch that path since filters use `list_filter.inner.html:15`.
- **LOW.** The None-hook plus `Layout()` case is dispositioned as "pack-owned fallback to uni_form.html", which renders every field. That is fine as an accepted behaviour, but it should be documented in 06-08 as the visible result, since a consumer who omits actions and empties the layout will see all fields reappear.

### 4. Suggestions
- Replace the "private Layout subclass with `__bool__`" sentence with: override `__bool__` on the helper; the prepared layout is a plain `Layout` whose fields are filled in `render_layout`.
- Add a direct unit test: `bool(helper)` is True with an empty prepared layout, and `{% crispy form helper %}` with `helper.layout = Layout()` yields exactly one Apply/Reset group and zero fields.

### 5. Risk Assessment
HIGH until the helper-level truthiness mechanism is written into the plan and the spec. Everything else in the plan is grounded.

## 06-06

### 1. Summary
The diagnostic policy is reconciled with the existing helpers and the static-reach rules are consistent with the providers. M-ICON-AVAILABILITY is closed by routing availability through `resolve_icon` (`icons.py:187-202`), which returns None for a disabled semantic mapping without invoking any renderer, while `render_icon` (`icons.py:223-237`) is the only renderer invocation and belongs to the leaf.

### 2. Strengths
- The existing E211 message hardcodes card/context scalar hints (`src/crud_views/lib/view/action_menu.py:57-61`) that `test_action_label_mode_config.py:227-245` pins; the plan's narrowly scoped form branch keeps those bytes untouched.
- W291 only on the view's own attribute matches `action_menu.py:46-72` and `test_action_label_mode_config.py:269-273`.
- H-DELETE-STATIC is right: `CrispyDeleteForm.helper` at `form.py:132-142` uses `get_delete_button` and `get_cancel_button` and never `get_submit_button`, so inherited `submit_icon` is unused there. The delete form is view-supplied (`tests/test1/app/views.py:122`), so the static check reads `form_class`.
- M-POLYMORPHIC: `polymorphic_forms` is a plain class dict (`src/crud_views_polymorphic/lib/utils.py:35`) and `get_form_class` depends on URL kwargs (`:64-72`), so inspect-the-dict-never-call is the right split.
- The existing W292 pattern catches `ValueError` only around mode resolution (`src/crud_views/lib/view/buttons.py:426-429`), which the plan mirrors.

### 3. Concerns
- **LOW, residual availability hole.** `resolve_icon` returns `(prefix, name)` for an unregistered prefix (`icons.py:199-202`), while `render_icon` returns an empty string for it (`icons.py:230-236`). W352 only inspects icon-table entries (`icons.py:413-432`), not a per-form `submit_icon="xx:save"`. An icon-only form button with such a value renders an empty inline icon and a hidden label with neither W292 nor a strict error. The plan explicitly leaves unregistered prefixes to "separate registry diagnostics", but those diagnostics do not see per-form values. Suggest the dynamic guard also treat an unregistered prefix as missing, using `get_libraries()` lookup only, still without invoking a renderer.
- **LOW.** The must_have says "a valid inline custom renderer is called once per icon/both control". The leaf renders `{% cv_icon %}` once, so this holds only if the normalizer never calls `render_icon`. The plan says so; the counting-renderer test is the right guard.

### 4. Suggestions
- Extend the "missing" definition to `resolve_icon(...) is None or (prefix and prefix not in get_libraries())`, and add one test with a per-form unregistered-prefix icon.

### 5. Risk Assessment
MEDIUM. Rules are grounded; the unregistered-prefix hole is small but real.

## 06-07

### 1. Summary
Environment facts are verified: lock engines for jsdom and vitest exclude Node 20, local `node_modules` are a generation behind the lock, and the existing modal test `tests/js/modal.test.js:196` already asserts the clicked submitter is posted, so the plan extends rather than invents. `modal.js:82` uses `new FormData(form, submitter || undefined)` and `viewset.js:40` uses `closest("[data-cv-cancel-url]")`, so nested icon/span clicks are already delegated.

### 2. Strengths
- The nox session design mirrors `noxfile.py:6-19` (uv backend, extras install, 4.2 skip rule for 3.14+).
- Rejecting the Node-20-only acceptance is justified by the lock engines quoted above.
- Reset handler at `list.filter.js:42-53` reads `sort`/`order`/`dir` from the config query string and does not `preventDefault`, so `type="reset"` native behaviour and navigation coexist as the plan expects; existing cases at `tests/js/list.filter.test.js:236-243` cover encoded values.

### 3. Concerns
- **LOW.** Task 3 installs `django~={version}.0` and the extras with the two crispy pins "in the same resolver transaction". With uv that is one `session.install(...)` call containing all four specs; the plan should say so explicitly, since the existing session installs Django in a separate call (`noxfile.py:13-14`), and copying that shape would let the extras resolve crispy upward.
- **LOW.** The existing `examples` session also pins Django separately; the new session should not touch it.

### 4. Suggestions
- Write the single-call install literally in Task 3.

### 5. Risk Assessment
LOW to MEDIUM, dominated by runtime acquisition owned by 06-01.

## 06-08

### 1. Summary
Documentation and migration actions are complete for the Round 2 findings. M-SETTINGS-LIFECYCLE wording ("startup snapshot on `crud_views_settings`, not hot-refreshed") is correct per `settings.py:13-14,320`. L-SUPPRESSION-MIGRATION has an executable recipe and a changed-behaviour regression. The tooltip location inventory at `src/crud_views/static/crud_views/js/tooltip.js:6` lists locations in a comment and the runtime reads the marker value generically (`tooltip.js:27-28`), so adding `form` is comment-only, as the plan says.

### 2. Strengths
- The field-only helper example to preserve exists at `docs/reference/list_view.md:143-144` and `docs/getting_started/tutorial-5-filters-permissions.md:28-29`, and the example project uses it at `examples/bootstrap5/library/views.py:48-49`.
- The example settings currently define no `CRUD_VIEWS_LABEL_MODE_DEFAULTS` (`examples/bootstrap5/project/settings.py:124-128`), so "preserve other locations" is trivially satisfied and the change is one line.
- The key-count sentence guard (`test_button_classes.py:97-101`) and the merged-vs-replaced table assertions (`tests/test1/test_label_mode_docs.py:129,146`) keep the docs honest.

### 3. Concerns
- **LOW.** Task 2 should document the 06-05 None-hook plus empty-layout outcome (all fields reappear via `uni_form.html`) since that is the one case where "omit actions" changes visible field output.
- **LOW.** `examples/bootstrap5/test_i18n.py:135` asserts `'value="Sichern"'`; it stays green only because the leaf keeps `value` on the button. Task 3 should mention that this assertion is intentionally retained as consumer evidence.

### 4. Suggestions
- Add the empty-layout fallback sentence to the list_view.md hook section.

### 5. Risk Assessment
LOW.

## 06-09

### 1. Summary
L-EXAMPLE-COVERAGE is closed with a grounded gate: `test_demo_pages_render_german` exists at `examples/bootstrap5/test_i18n.py:121-135`, `HomePageTest.test_every_feature_landing_page_renders` at `examples/bootstrap5/project/tests.py:45`, and the reference/backlink cases at `examples/bootstrap5/test_doc_links.py:119,140`. `SystemChecksTest` at `project/tests.py:97-114` resolves the full URLconf as M-EXAMPLE-CHECKS required. `pytest.ini` selects `project.settings`.

### 2. Strengths
- Separates the three delete evidences (confirmation-only, rendered name/value, confirmation-plus-submitter) so no one test is overclaimed.
- Keeps the two unclassified probe rows visible instead of relabelling them.
- Human checks are explicit and end-of-phase, consistent with `06-VALIDATION.md` manual rows.

### 3. Concerns
- **LOW.** The example gates run with the root `.venv`. The nox `examples` session installs `.[all,test,examples]` plus `requirements/demo.txt` (`noxfile.py:29-30`); if the root venv lacks the demo requirements, the gate fails for environment reasons. Task 2 should state that a collection failure is an environment blocker to record, not a product failure to route to 06-08.
- **LOW.** The acceptance table should carry the H-HELPER-TRUTHINESS fix once 06-05 is corrected, so the empty-layout evidence is traceable.

### 4. Suggestions
- Add a one-line environment precondition for the example gate.

### 5. Risk Assessment
LOW.

## Prior findings: present closure

| Finding | Closure | Evidence |
|---|---|---|
| M-SETTINGS-LIFECYCLE | Closed | `settings.py:13-14,320`, no receiver in settings.py, `test_action_label_mode_config.py:78-80`; 06-03 task 1 and 06-08 task 1 match |
| M-EMPTY-REPLACEMENT | Not closed | Preparation timing is right (`crispy_forms_tags.py:109,147` before `:116`), but the truthiness mechanism targets the wrong object (`helper.py:99-103`). See H-HELPER-TRUTHINESS |
| L-SUPPRESSION-MIGRATION | Closed | `list.py:70-73`; 06-05 disposition, 06-08 tasks 2/3 executable |
| M-ICON-AVAILABILITY | Closed, with one residual LOW | `icons.py:187-202` vs `:223-237`; unregistered-prefix per-form values remain undiagnosed |
| L-EXAMPLE-COVERAGE | Closed | `test_i18n.py:121`, `project/tests.py:45`, `test_doc_links.py:119,140` |
| H-OVERLAY-PROVENANCE | Stays rejected as an existence claim | `crispy_forms_tags.py:171-175` supplies overlay metadata; the separate nested-row "page" definition gap is reported above as MEDIUM |

## Cross-plan assessment

Dependency order is sound and the same-wave pair (06-07, 06-08) has no file overlap. The one ordering hazard is that 06-01 writes the Helper lifecycle section of the spec before 06-05 executes, so the HIGH fix must land in both 06-01 Task 1 text and 06-05 Task 1 text, or the executor will implement the wrong mechanism from the spec. No scope creep beyond the already-accepted runtime wrapper. Security posture is correct: the literal boundary, SafeString demotion, and single escape pass are grounded in `layout.py:255` and Django `flatatt` semantics.

## Overall risk

MEDIUM. Eight plans are source-grounded and executable. One HIGH mechanism error in 06-05 (recorded into the spec by 06-01) would make the empty-layout and no-layout filter paths skip `render_layout`, losing Apply/Reset; the plan's own `fails_when` would catch it late, but the fix is a two-line helper truthiness override that should be written into the plans now. The MEDIUM nested-row ownership definition needs one sentence in the spec and one added regression in 06-03.


---

## OpenCode Review (grok-review)

I'll verify each plan against the source, starting with the settings lifecycle, helper dispatch, icon resolution, and example coverage the prior findings depend on.
The plans are in the prompt; next I’ll check the mechanisms they claim already exist in settings, crispy helpers, and icon resolution.
## 06-01

**Summary.** Spec-first and baseline-first ordering matches the code that later plans have to change: today’s controls are `<input>`s, filter actions live in `helper.inputs`, and Phase 1/2 contracts are already on this tree. The plan records those facts before any product edit.

**Strengths.**
- `ListViewFilterFormHelper` still builds Apply/Reset with `add_input` (`src/crud_views/lib/views/list.py:70-73`) and hidden sort/order only when the query is nonempty (`list.py:77-87`). Task 3’s nonempty query pin is what makes those hidden fields show up in the golden.
- Delete today posts only `{"confirm": True}` (`tests/test1/test_crud.py:63`). Keeping that POST and adding a separate `delete=Delete` case matches the view, not an invented submitter-only contract.
- Wire names are normalized in the pack template, not the constructor: `wordcount > 1` then `slugify` (`crispy_bootstrap5/.../baseinput.html:2`), while `BaseInput.__init__` always slugifies the id (`crispy_forms/layout.py:240-241`). The spec’s split of stored name vs emitted name vs generated id matches that.
- `from_settings` is a one-shot `getattr` at class definition (`src/crud_views/lib/settings.py:13-14,67-68`); there is no `setting_changed` receiver in that module. The spec’s singleton-vs-lazy-floor note is the real lifecycle.
- Lock engines are real: jsdom 30.1.2 wants `^22.22.2 || ^24.15.0 || >=26`, while `package.json:16` still says `>=20`. A selected-runtime wrapper is the right gate.

**Concerns.**
- **MEDIUM:** The ownership rule still says “nearest non-None page view” under the current overlay. A lower crispy response dict can also hold `view`, copied from the helper (`crispy_forms/helper.py:340-346` into `get_response_dict`). The spec must say to skip every layer that has `inputs` + `is_formset` + `template_pack` (`crispy_forms/templatetags/crispy_forms_tags.py:171-174`), not only the top one. This is a walk rule, not a missing provenance API.

**Suggestions.**
- Write that skip-all-overlays rule into the Ownership section before 06-03 implements it.

**Risk Assessment.** LOW. Prerequisite, baseline, and settings-lifecycle claims match the tree. The overlay walk is the only contract still loose.

## 06-02

**Summary.** The first tracer is aimed at the path that actually evaluates values. `BaseInput.render` compiles `self.value` as a template and pushes `input` onto the context (`crispy_forms/layout.py:255-257`). Helper inputs never call that method (`inputs.html:9` includes `baseinput.html`). Branching layout adapters off `BaseInput.render` is the right break.

**Strengths.**
- `LOCATIONS` is still `{"context", "list", "card"}` (`button_data.py:12`) and `LEAF_KEYS` includes action-only `cv_href` / `cv_modal` (`button_data.py:16-38`). An early form branch plus `FORM_LEAF_KEYS` avoids that contract.
- `{"form": "both"}` is an E108 failure today (`tests/test1/test_action_label_mode_config.py:278,322-323`). Moving that case in the same change as adding `"form"` to `LOCATIONS` is required, not cleanup.
- Key count is 71 (`tests/test1/test_button_classes.py:90`, `docs/reference/buttons.md:145-146`) with four `*:icon-host` keys (`button_classes.py:91-94`). 71→73 and a fifth host key is the right arithmetic.
- Cancel’s submitted name is `reset` (`crispy/form.py:76`), the same as filter reset. Slot-based kind, not name, is necessary.

**Concerns.**
- **LOW:** `BaseInput.__init__` stores extra kwargs only as already-escaped `flat_attrs` (`layout.py:248`, `crispy_forms/utils.py:142-149`). “Retain raw kwargs” must mean capture them before `super()`, or the leaf will double-escape. The fails-when clause covers it; the action text does not.

**Suggestions.**
- Say explicitly: copy `kwargs` before `super().__init__`; do not re-escape `self.flat_attrs`.

**Risk Assessment.** LOW. The render bypass, location consumers, and key-count move are grounded.

## 06-03

**Summary.** Whole-map selection is the existing seam: `cv_first_inline_keys` returns the first non-None map (`base.py:263-272`), and a missing key falls to `default_label_mode`, which reads Django settings on every call (`label_mode.py:54-58,84-117`). Map tests already use `monkeypatch.setattr(crud_views_settings, ...)` (`test_action_label_mode_config.py:79`). The new form map should follow that, not `override_settings`.

**Strengths.**
- M-SETTINGS-LIFECYCLE is closed against source. `crud_views_settings = CrudViewsSettings()` (`settings.py:320`) freezes map defaults at import. The floor is the only lazy read. The planned monkeypatch-vs-`override_settings` render is the right proof.
- Form owner must come from the `render(form, context)` argument. `{% crispy x_form.form x_form.helper %}` (`formsets/formset.html:42`) passes the row form; `CrispyFormMixin.helper` builds a new helper on every access (`crispy/form.py:41-48`). Not re-reading that property is correct.
- `Context.update` pushes a layer and does not pop it (`django/template/context.py:167-173`). `FormActions.render` pushes `formactions` / `fields_output` after the buttons render (`bootstrap.py:306-309`). A fixed stack offset is wrong.

**Concerns.**
- **MEDIUM:** H-OVERLAY-PROVENANCE’s “no metadata” premise is wrong: the response dict always has `inputs`, `is_formset`, and `template_pack` (`crispy_forms_tags.py:171-174`). The remaining defect is the walk. Nested `{% crispy %}` copies the context (`context.py:40-44`) and pushes another trio layer. The first `view` below the current trio can be an outer helper’s `view` (`helper.py:340-346`), not the page view. D-09’s page fallback must skip every trio layer. Task 2’s “exact fallback” for an absent row owner does not assert page identity against a conflicting outer helper view.

**Suggestions.**
- In the absent/None row-owner case, assert the page view’s mode, not merely “not the outer form.” Skip every trio layer before taking `view`.

**Risk Assessment.** MEDIUM. Map lifecycle is solid. Owner recovery is correct only if the walk ignores every crispy response layer.

## 06-04

**Summary.** Icon availability and host placement already exist and do not need a renderer probe. `resolve_icon` returns `None` for empty input and for a table value of `None`/`""` (`icons.py:187-198`) and never calls `render_icon`. `icon_host_keys` uses `resolve_icon_name_class` (`button_data.py:41-49`).

**Strengths.**
- `save`, `cancel`, and `filter-reset` are absent from `DEFAULT_ICONS` (`icons.py:14-49`). `delete`, `filter`, and `workflow` are already there. The three new names are the real registry gap.
- A `None`/empty `location:icon-host` slot makes `get_icon_host_class` return `""` (`button_classes.py:149,152-165`) while `icon_host_keys` still sets inline to false when the icon itself is a host icon. That is the opt-out the plan preserves.
- `CrispyDeleteForm.helper` renders `get_delete_button()` (`slot="form:delete"`) plus cancel, not `get_submit_button` (`crispy/form.py:123-140`). Kind-from-slot is required. `WorkflowForm` has no `submit_icon` today (`crud_views_workflow/lib/forms.py:11-20`); the class default is new, not a rename.

**Concerns.**
- **LOW:** An unregistered name is not missing. `resolve_icon("save")` before registration returns `("", "save")` (`icons.py:199-200`). W292 must key off `resolve_icon is None`, which 06-06 states. This plan should not treat a raw-class fallback as “no icon.”

**Suggestions.**
- Keep semantic defaults as registry names and let 06-06 own the None/empty test. Do not call `render_icon` to decide availability.

**Risk Assessment.** LOW. Registry, host, and slot rules match the current helpers.

## 06-05

**Summary.** Moving stock Apply/Reset into `FormActions` while leaving `Hidden` on `helper.inputs` matches the pack. `whole_uni_form.html:9-11` renders the layout, then `inputs.html`, which wraps inputs in `mb-3` (`inputs.html:2`) and includes `baseinput.html` directly (`inputs.html:9`). Clearing `inputs` today removes Apply/Reset because they are inputs (`list.py:70-73`).

**Strengths.**
- M-EMPTY-REPLACEMENT is closed as a mechanism. `Layout` has `__len__` and no `__bool__` (`layout.py:38-39,108-138`); `bool(Layout())` is false. `get_render` calls `get_response_dict` → `get_attributes` (`crispy_forms_tags.py:109,147`) before `if helper and helper.layout` (`crispy_forms_tags.py:116`). Preparing a truthy layout in `get_attributes` runs before that guard. Doing it only in `render_layout` never runs, and `display_form.html:7-8` then falls back to `uni_form.html`.
- `FormHelper.__init__` replaces a declared layout when `form is not None` (`helper.py:212-214`). The mixin constructs helpers as `(request=, view=)` only (`mixins.py:319`). Not passing `form` into `super().__init__` is what keeps a class `layout`.
- Non-underscore attributes are published into the crispy context (`helper.py:340-346`). Underscore lifecycle state is the right hiding rule.
- L-SUPPRESSION-MIGRATION matches the code: after the move, `inputs=[]` only clears leftover inputs. The None-hook recipe is the replacement, and this plan does not fake the old suppression.

**Concerns.**
- **LOW:** `get_attributes` can run more than once per tag. If each call deep-copies the prepared layout again, the action group appended on the previous object is dropped. The plan says not to do that; the identity check has to survive a second `get_attributes` before `render_layout`.

**Suggestions.**
- Store the prepared layout identity and treat a repeat `get_attributes` on that object as a no-op.

**Risk Assessment.** LOW. The falsy-layout guard and the inputs-vs-layout split are verified on installed crispy 2.6. The 2.0 floor is an execution check, not an unverified claim.

## 06-06

**Summary.** Reusing `cv_label_mode_checks` unchanged would be wrong. That helper emits E211 for any invalid map, including bad mode values, and W291 only for keys outside the view’s own actions (`action_menu.py:46-72`). E210 today is the scalar check (`label_mode.py:44-50`). W292 today only walks context toolbar keys and `cv_icon_action` (`buttons.py:387-435`). A separate form policy is required.

**Strengths.**
- M-ICON-AVAILABILITY is closed. `resolve_icon` is the availability test and does not call a renderer (`icons.py:187-202,223-237`). A host icon stays available when `resolve_icon_name_class` returns a class (`icons.py:240-259`); a `None` host slot is an opt-out, not a missing icon (`button_classes.py:155-165`).
- Default delete helpers must not be checked via inherited `submit_icon`. `CrispyDeleteForm.helper` never calls `get_submit_button` (`form.py:132-140`). Selecting that provider first matches the render path.
- `polymorphic_forms` is a class dict (`crud_views_polymorphic/lib/utils.py:35,69`). Inspecting the classes without constructing a request-bound form matches how checks work today (`buttons.py:411-420` already skips dynamic buttons).

**Concerns.**
- **LOW:** `is_label_mode_map` accepts any string key (`label_mode.py:37-41`). The ViewSet validator is the same open check (`viewset/__init__.py:105-111`). Finite form keys have to be a new validator, not that decorator with the field name added. The plan says this; an executor who “follows the existing validator” will miss unknown form kinds.

**Suggestions.**
- Name a form-only validator in the task text so it is not the open `check_label_mode_map`.

**Risk Assessment.** LOW. Diagnostic IDs, delete-provider reach, and semantic `None` icons match the current functions.

## 06-07

**Summary.** Browser contracts already exist and should stay. Modal submit uses native `FormData(form, submitter || undefined)` (`modal.js:75-82`). Cancel is a delegated click on `[data-cv-cancel-url]` (`viewset.js:38-43`), so a nested icon still hits the button. Reset is `getElementById("filter-button-reset")` with no `preventDefault` (`list.filter.js:42-57`).

**Strengths.**
- Task 2’s `type=reset` plus navigation matches the current handler: the click listener does not cancel the native reset, then assigns `location.href`. Asserting both is the real behavior.
- The locked engines are not optional. jsdom 30.1.2 and vitest 5.0.3 both require Node 22+. Rejecting a Node 20 / old `node_modules` pass is correct.
- The floor session listing filter and owner tests is what would catch a crispy 2.0 `get_attributes` order difference. Installed code here is 2.6 only.

**Concerns.**
- **LOW:** `onReset` always navigates and does not read the button’s `name`/`value`. A nested-span click still bubbles to the id listener. The test should click the inner span and still expect one navigation, not a second listener.

**Suggestions.**
- Keep handler edits conditional. The current listeners already cover nested clicks and submitter `FormData`.

**Risk Assessment.** LOW. The JS contracts are in tree. Runtime acquisition is an execution gate, not a design hole.

## 06-08

**Summary.** The migration text matches the code change. Stock filter buttons are inputs today (`list.py:70-73`), so `inputs=[]` suppresses them. After 06-05 they will not. Tooltip dispatch is already generic (`tooltip.js:27-28` passes the marker value through); only the comment (`tooltip.js:6-7`) and the location table (`docs/reference/javascript.md:99-107`) omit `form`.

**Strengths.**
- L-SUPPRESSION-MIGRATION is closed as a plan action: the recipe returns `None` from `get_form_actions`, keeps fields and hidden GET controls, and the old `inputs=[]` case is a changed-behavior regression, not a silent compatibility claim.
- M-SETTINGS-LIFECYCLE docs match `settings.py:13-14,65-68` and `label_mode.py:54-58`: maps are a startup snapshot; the floor is lazy.
- The example does not set `CRUD_VIEWS_LABEL_MODE_DEFAULTS` today. `form=both` does not overwrite another location.
- Hidden-wrapper order is pack-owned (`whole_uni_form.html:9-11`, `inputs.html:2`). Documenting it instead of overriding `inputs.html` matches the out-of-scope global-pack rule.

**Concerns.**
- **LOW:** `test_demo_pages_render_german` asserts `value="Sichern"` (`examples/bootstrap5/test_i18n.py:135`). That survives only if the button keeps a `value` attribute. FORM-06 requires that; this plan’s changelog should say the attribute stays, or the 06-09 gate will fail for a docs-only surprise.

**Suggestions.**
- In the Breaking note, state that `value` remains on the `<button>`, so the German create assertion still matches.

**Risk Assessment.** LOW. Recipes and diagnostic wording follow the implementation plans and the current helpers.

## 06-09

**Summary.** The example gate is pointed at tests that exist and that root `pytest tests` does not run. `examples/bootstrap5/pytest.ini:2` sets `DJANGO_SETTINGS_MODULE = project.settings`. `SystemChecksTest` loads the URLconf before `run_checks` (`project/tests.py:97-114`). `test_every_feature_landing_page_renders` (`project/tests.py:45-51`), `test_i18n.py:121`, and `test_doc_links.py` are real cases.

**Strengths.**
- L-EXAMPLE-COVERAGE is closed at plan level. The extra command runs those three modules under the example settings and treats failure as a blocker back to the producing plan. Root-suite success cannot substitute.
- Baseline history, confirmation-only delete (`test_crud.py:63`), and the new submitter POST are cited separately. That matches the current test.
- Unclassified FORM-01/FORM-02 rows stay flagged. That does not weaken the ordinary history and contract tests.

**Concerns.**
- **LOW:** `test_every_feature_landing_page_renders` only checks status 200. It will not catch a broken form button on a create page. `test_demo_pages_render_german` is the form assertion, and it only covers the author create `value`. That is enough for the named finding; it is not full example form coverage.

**Suggestions.**
- Keep the German value assertion as the form probe. Do not treat landing-page 200s as button proof.

**Risk Assessment.** LOW. The acceptance commands match files that are in the tree.

## Prior findings and overall risk

M-SETTINGS-LIFECYCLE, M-EMPTY-REPLACEMENT, L-SUPPRESSION-MIGRATION, M-ICON-AVAILABILITY, and L-EXAMPLE-COVERAGE are closed against source, not only against the ledger. `from_settings` is import-time; empty `Layout()` is falsy and `get_attributes` runs before the layout guard; stock actions are inputs today; `resolve_icon` does not render; the example tests named in 06-09 exist and load `project.settings`.

H-OVERLAY-PROVENANCE’s missing-API premise is not a defect. `get_response_dict` already supplies `inputs` / `is_formset` / `template_pack`. The independent gap is the page-view walk in 06-01 and 06-03: skip every such layer, or an outer helper `view` is selected for an ownerless embedded form.

**Overall risk: MEDIUM.** The phase achieves FORM-01–FORM-13 if that walk is tightened. Nothing else in the nine plans contradicts the installed crispy, button, icon, or example code.


---

## OpenCode Review (gemini-review)

## 06-01

### 1. Summary
Plan `06-01` establishes the pre-implementation design spec (`06-SPEC.md`), the isolated JS runtime verification wrapper (`06-js-verify.sh` / `06-JS-RUNTIME.json`), and the five before-change golden baselines (`create.html`, `update.html`, `delete.html`, `workflow.html`, `filter.html`) committed prior to any `src/` edits. All cycle-2 findings assigned to `06-01` (`M-SETTINGS-LIFECYCLE`, `M-EMPTY-REPLACEMENT`, `L-SUPPRESSION-MIGRATION`, `M-ICON-AVAILABILITY`) are accurately integrated into Task 1's spec requirements with concrete source-grounded mechanisms.

### 2. Strengths
- **Working-branch prerequisite verification (D-18):** Task 1 verifies the completed Phase 1/2 contracts directly against `src/crud_views/lib/view/label_mode.py:84-117` (`default_label_mode`) and `src/crud_views/lib/button_classes.py:209-210` (`VARIANT_LOCATIONS`, `FORM_KINDS`) and runs `tests/test1/test_label_mode.py`, `tests/test1/test_action_label_mode_config.py`, and `tests/test1/test_button_classes.py` before authoring `06-SPEC.md`.
- **Closure of cycle-2 spec findings:**
  - `M-SETTINGS-LIFECYCLE` is grounded in `src/crud_views/lib/settings.py:13-14, 67-68, 320`, where `from_settings()` snapshots settings at `crud_views_settings = CrudViewsSettings()` instantiation time without a `setting_changed` receiver, whereas `src/crud_views/lib/view/label_mode.py:54-58` reads `CRUD_VIEWS_LABEL_MODE_DEFAULTS` lazily on each call.
  - `M-EMPTY-REPLACEMENT` is grounded in `.venv/lib/python3.12/site-packages/crispy_forms/templatetags/crispy_forms_tags.py:109, 116, 147` and `.venv/lib/python3.12/site-packages/crispy_forms/layout.py:38-39`, where `BasicNode.get_render` calls `helper.get_attributes()` inside `get_response_dict()` before testing `if helper and helper.layout:`, and an empty `Layout()` has `len(self.fields) == 0` (`bool(Layout()) is False`).
  - `M-ICON-AVAILABILITY` is grounded in `src/crud_views/lib/icons.py:187-202` (`resolve_icon`), which resolves semantic names and returns `None` for `None`/`""`/whitespace or registry-disabled entries (`CRUD_VIEWS_ICONS = {name: None | ""}`) without invoking `_get_renderers()` (`icons.py:223-237`).
  - `L-SUPPRESSION-MIGRATION` is grounded in `src/crud_views/lib/views/list.py:70-87`, where moving Apply/Reset out of `self.inputs` into layout `FormActions` means `helper.inputs = []` only clears legacy/hidden inputs and no longer suppresses default filter buttons.
- **Separate delete payload assertions (`M-PAYLOAD`):** Task 2 preserves `tests/test1/test_crud.py:63` (`client_user_author_delete.post(..., {"confirm": True})`) unchanged while adding a separate POST test with `{"confirm": True, "delete": "Delete"}` in `tests/test1/test_form_buttons_golden.py`.

### 3. Concerns
- **LOW — Filter baseline query parameters must match `PublisherListView` / `PublisherOrderCardListView` configuration:** In Task 3 (`06-01-PLAN.md:155-157`), the plan specifies capturing `filter.html` with *"nonempty sort/order/direction query values so conditional hidden fields are present"*. In `src/crud_views/lib/views/list.py:77-87`, `ListViewFilterFormHelper.__init__` always emits `Hidden("sort", sort)` (even when empty, line 78), and conditionally emits `Hidden(order_param, order)` and `Hidden(dir_param, direction)` when `request.GET.get("order")` and `request.GET.get("dir")` are truthy (lines 80-87). Ensure the exact GET query string used for `tests/test1/golden/form_buttons/filter.html` in `06-01` Task 3 is reused identically in `06-05` Task 1 when updating `filter.html`.

### 4. Suggestions
- In `tests/test1/test_form_buttons_golden.py`, define a module-level constant (e.g. `FILTER_QUERY = {"sort": "name", "order": "name", "dir": "desc"}`) so `06-01` Task 3 and `06-05` Task 1 share the exact same request parameters.

### 5. Risk Assessment
- **LOW:** `06-01` makes no production code changes and has deterministic automated verification gates for every section of `06-SPEC.md` and all five baseline golden files.

---

## 06-02

### 1. Summary
Plan `06-02` delivers the core form-button leaf (`src/crud_views/templates/crud_views/tags/button/form.html`), the `"form"` branch and `FORM_LEAF_KEYS` in `src/crud_views/lib/view/button_data.py`, `"form": "label"` in `src/crud_views/lib/view/label_mode.py`, the `form:hidden-label` and `form:icon-host` utility keys in `src/crud_views/lib/button_classes.py`, and the `Submit`/`Button`/`Reset` adapter `render()` implementation in `src/crud_views/lib/crispy/buttons.py`. It also atomically updates location/key-count consumers across tests and docs so wave 2 stays green.

### 2. Strengths
- **Atomic location and utility-key rollout (`H-LOCATIONS`, `H-EARLY-UTILITIES`, `H-KEYSET`):** Task 1 updates `LOCATIONS` (`src/crud_views/lib/view/button_data.py:12`), `LABEL_MODE_DEFAULTS` (`src/crud_views/lib/view/label_mode.py:23`), `DEFAULT_BUTTON_CLASSES` (`src/crud_views/lib/button_classes.py:84-94`), `EXPECTED_KEYS` and the `71 -> 73` count (`tests/test1/test_button_classes.py:21-91`), `E108_LOCATIONS` (`tests/test1/test_action_label_mode_config.py:278, 323`), `docs/reference/buttons.md:145`, and `docs/reference/settings.md:78, 90` in the same task. This satisfies `tests/test1/test_button_classes_templates.py:50-56` (`test_every_literal_slot_in_templates_is_a_default_key`), which scans `src/*/templates/**/*.html` for `{% cv_button_class "<loc>" "<slot>" %}` literal pairs.
- **Bypassing crispy template compilation of `value` (FORM-07, D-15):** In `.venv/lib/python3.12/site-packages/crispy_forms/layout.py:255`, `BaseInput.render` executes `self.value = Template(str(self.value)).render(context)`, which both mutates `self.value` on the adapter instance and evaluates Django template syntax. Overriding `render()` on `_TableClassMixin` (`src/crud_views/lib/crispy/buttons.py`) without calling `super().render()` eliminates both the SSTI vector and the instance mutation hazard.
- **Preserving crispy multi-word `name` slugification (`M-NAME`):** In `.venv/lib/python3.12/site-packages/crispy_bootstrap5/templates/bootstrap5/layout/baseinput.html:2, 6`, crispy renders `name="{% if input.name|wordcount > 1 %}{{ input.name|slugify }}{% else %}{{ input.name }}{% endif %}"` while generating `self.id = f"{self.input_type}-id-{slugify(self.name)}"` in `BaseInput.__init__` (`crispy_forms/layout.py:240-241`). Task 2 preserves both rules without mutating `self.name`.

### 3. Concerns
- **LOW — `test_no_button_class_literal_in_shipped_templates_python_or_js` scans raw Python/HTML/JS text (including docstrings and comments):** In `tests/test1/test_button_classes_templates.py:21, 35-47`, `TOKEN = re.compile(r"(?<![\w-])btn(?:-[\w-]+)?(?![\w-])")` scans `path.read_text()` for every `.py`, `.html`, and `.js` file under `src/` (exempting only `crud_views/lib/button_classes.py` and the token `btn-close`). If any comment or docstring added to `src/crud_views/lib/crispy/buttons.py`, `src/crud_views/lib/view/button_data.py`, or `src/crud_views/templates/crud_views/tags/button/form.html` mentions `btn` or `btn-primary`, that test will fail.
- **LOW — `tests/test1/test_label_mode.py` has four specific assertions tied to the 3-location set and is omitted from Task 1's `<verify>` command:** Task 1 modifies `tests/test1/test_label_mode.py` (`06-02-PLAN.md:52, 62`), where four existing assertions hardcode the pre-Phase-6 location set:
  1. `PACKAGE = {"context": "icon", "list": "icon", "card": "both"}` (`test_label_mode.py:17`),
  2. `({"form": "label", "list": "both"}, {**PACKAGE, "list": "both"})` in `test_default_label_mode_merge` (`test_label_mode.py:94`),
  3. `@pytest.mark.parametrize("location", ["toolbar", "form", "filter", "", "Context"])` in `test_default_label_mode_invalid_location` (`test_label_mode.py:137`),
  4. `assert len(_records(caplog)) == 3  # one per location queried` in `test_default_label_mode_invalid_setting_whole` (`test_label_mode.py:155`, which becomes `4` once `_resolved()` iterates 4 `LOCATIONS`).
  While `test_label_mode.py` runs in Task 2's `<verify>` (`06-02-PLAN.md:100`), running it in Task 1's `<verify>` as well catches all four immediately when `LOCATIONS` and `LABEL_MODE_DEFAULTS` are updated.

### 4. Suggestions
- Keep all comments and docstrings in `src/crud_views/lib/crispy/buttons.py`, `src/crud_views/lib/view/button_data.py`, and `src/crud_views/templates/crud_views/tags/button/form.html` free of `btn` / `btn-*` tokens so `tests/test1/test_button_classes_templates.py:35-47` passes.
- Include `tests/test1/test_label_mode.py` in Task 1's `<verify>` command alongside the other location consumer suites, and update lines `17`, `94`, `137`, and `155` of `tests/test1/test_label_mode.py` in Task 1.

### 5. Risk Assessment
- **LOW:** The leaf contract, escaping boundary, and consumer updates are thoroughly specified and verified against existing tests.

---

## 06-03

### 1. Summary
Plan `06-03` wires `CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE` (`CrudViewsSettings.form_actions_label_mode`), `ViewSet.form_actions_label_mode`, `CrudView.cv_form_actions_label_mode`, and `CrudView.cv_get_form_actions_label_mode()`, and implements owner-first resolution (`form.cv_view` → helper `view` → page `view`) in `src/crud_views/lib/crispy/buttons.py`. It closes `M-SETTINGS-LIFECYCLE` and dispositions `H-OVERLAY-PROVENANCE` while retaining concrete regression requirements for multiple `FormActions` groups and formset row rendering.

### 2. Strengths
- **Complete closure of `M-SETTINGS-LIFECYCLE`:** Task 1 (`06-03-PLAN.md:57-75`) matches `src/crud_views/lib/settings.py:67-68, 320` (`from_settings("CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE", default={})` on `CrudViewsSettings`) and `tests/test1/test_action_label_mode_config.py:78-95` (`monkeypatch.setattr(crud_views_settings, ...)`), and explicitly tests the difference between the import-time singleton map snapshot and the call-time `CRUD_VIEWS_LABEL_MODE_DEFAULTS` floor.
- **Whole-map selection and lazy floor fallback:** Task 1 reuses `CrudView.cv_first_inline_keys` (`src/crud_views/lib/view/base.py:263-272`) and extends `CrudView.cv_get_action_label_mode` (`src/crud_views/lib/view/base.py:299-329`) with `location == "form"`, checking `if key in mapping:` before calling `default_label_mode("form")` so an explicit mapping never triggers a strict error on an invalid floor.
- **Distinguishing `H-OVERLAY-PROVENANCE` from real `Context.dicts` mechanics:** In `.venv/lib/python3.12/site-packages/crispy_forms/templatetags/crispy_forms_tags.py:109-113, 147-185`, `BasicNode.get_render` pushes `{"is_bound": actual_form.is_bound}` followed by `response_dict` (which contains `"is_formset"`, `"template_pack"`, `"inputs"`, `"flat_attrs"`, `"field_template"`, plus any non-`_` attributes from `helper.__dict__` extracted by `FormHelper.get_attributes` at `crispy_forms/helper.py:340-346`), while `FormActions.render` (`crispy_forms/bootstrap.py:309`) later appends `{"formactions": self, "fields_output": html}` onto `context.dicts`. Identifying the crispy `response_dict` layer by its structure rather than a fixed index offset (`context.dicts[-1]`) handles any number of `FormActions`, `Fieldset`, or `Context.push()` layers.

### 3. Concerns
- **LOW — Formset template path (`formset.html` vs `{% cv_x_formset %}` and `Formsets.render`) strips or flattens page `view` when invoked via inclusion tag:** In Task 2 (`06-03-PLAN.md:79, 86, 94-96`), the plan tests *"the package formset row-template path with an explicitly supplied row helper"* (`src/crud_views/templates/crud_views/formsets/formset.html:42`, `{% crispy x_form.form x_form.helper %}`), including fallback to the page `view` when both row `form.cv_view` and row `helper.view` are `None`/absent. Tracing the actual template chain reveals two distinct entry points:
  1. Rendering `crud_views/formsets/formset.html` directly (e.g. `Template('{% include "crud_views/formsets/formset.html" %}').render(Context({...}))`) preserves the caller's `Context.dicts` (including `"view"`) for top-level rows in `x_formset.forms` (`formset.html:32-44`).
  2. However, rendering via `{% cv_x_formset %}` (`src/crud_views/templatetags/crud_views_formsets.py:6-9`, used in `formsets.html:6,9` and for nested child rows at `formset.html:48`) uses `@register.inclusion_tag(takes_context=True, filename="crud_views/formsets/formset.html")` and returns only `{"x_formset": x_formset}`. Django's `InclusionNode.render` (`.venv/lib/python3.12/site-packages/django/template/library.py:377`, `new_context = context.new(_dict)`) creates a fresh `Context` containing only `x_formset` and `csrf_token`, dropping `"view"` from `new_context.dicts`. Furthermore, `Formsets.render` (`src/crud_views/lib/formsets/layout.py:17`) calls `render_to_string(self.template, context.flatten())`, which flattens the outer crispy `response_dict` into a single dict before calling `formsets.html`.
  Because `06-03-PLAN.md` only modifies `src/crud_views/lib/crispy/buttons.py` and `tests/test1/test_crispy_buttons.py`, the page-owner fallback test on `formset.html` will work when rendering `crud_views/formsets/formset.html` directly for `x_formset.forms`, and when scanning `Context.dicts` for the page `view` the helper-overlay detector should also skip any earlier crispy `response_dict` layers in `Context.dicts` so an outer helper's `view` is never mistaken for a page `view`.

### 4. Suggestions
- In `src/crud_views/lib/crispy/buttons.py`, identify crispy `response_dict` layers in `context.dicts` by their `BasicNode.get_response_dict` keys (`{"is_formset", "template_pack", "inputs", "flat_attrs", "field_template"} <= d.keys()`), read the current invocation's helper `view` from the innermost `response_dict` (or the private key pushed by `ListViewFilterFormHelper.render_layout`), and when falling back to the page `view`, scan `context.dicts` below the outermost `response_dict` (skipping any crispy `response_dict` layers) for the nearest non-`None` `"view"`.
- In `tests/test1/test_crispy_buttons.py`, render `crud_views/formsets/formset.html` via `Template('{% include "crud_views/formsets/formset.html" %}').render(Context(...))` (matching `06-03-PLAN.md:79`) so the enclosing page `Context.dicts` layers remain intact during the row helper/page fallback test.

### 5. Risk Assessment
- **LOW:** The owner precedence and `Context.dicts` layer inspection are well-bounded and directly verifiable in `tests/test1/test_crispy_buttons.py` and `tests/test1/test_action_label_mode_config.py`.

---

## 06-04

### 1. Summary
Plan `06-04` adds the `save`, `cancel`, and `filter-reset` semantic icons to `DEFAULT_ICONS` and `BOOTSTRAP_ICONS` in `src/crud_views/lib/icons.py`, wires `submit_icon = "save"` on `CrispyFormMixin`, `delete_icon = "delete"` on `CrispyDeleteForm`, and `submit_icon = "workflow"` on `WorkflowForm`, and adds the `icon=` keyword argument on the crispy button adapters in `src/crud_views/lib/crispy/buttons.py`.

### 2. Strengths
- **Registry parity preserved:** Adding `save`, `cancel`, and `filter-reset` to both `DEFAULT_ICONS` (`src/crud_views/lib/icons.py:14-49`) and `BOOTSTRAP_ICONS` (`src/crud_views/lib/icons.py:51-89`) with `far:`/`fas:` and `bi:` prefixes satisfies `test_bootstrap_preset_covers_exactly_default_names` and `test_defaults_are_font_awesome_only` in `tests/test1/test_icons_registry.py:106-112`.
- **Clean separation from `06-02` utility keys (`H-KEYSET`, `H-EARLY-UTILITIES`):** `form:hidden-label` and `form:icon-host` are already added in `06-02` Task 1, so `06-04` Task 1 focuses cleanly on icon registry entries and host/inline rendering tests in `tests/test1/test_icon_host_leaves.py`.
- **Sentinel-based `icon=` kwarg on adapters:** Using an `_UNSET` sentinel for `icon=` in `src/crud_views/lib/crispy/buttons.py` distinguishes omitted `icon` (which resolves the kind's default icon: `submit`→`save`, `delete`→`delete`, `cancel`→`cancel`, `filter-submit`→`filter`, `filter-reset`→`filter-reset`) from explicit `icon=None` or `icon=""` (which intentionally suppresses the icon and triggers the missing-icon policy in `"icon"` mode), while consuming `icon` before `flatatt(kwargs)` so it never leaks as an HTML `icon="..."` attribute.

### 3. Concerns
- **LOW — Hook kwargs override ordering in `CrispyFormMixin` and `CrispyDeleteForm`:** In `src/crud_views/lib/crispy/form.py:56-63, 123-130`, `get_submit_button_kwargs()` returns `{"name": "submit", "value": self.submit_label}` and `get_delete_button_kwargs()` returns `{"name": "delete", "value": _("Delete")}`, while `get_delete_button()` calls `Submit(**{"slot": "form:delete", **self.get_delete_button_kwargs()})` (so a subclass overriding `get_delete_button_kwargs()` can override `slot`, as tested by `test_delete_button_kwargs_may_choose_the_slot` in `tests/test1/test_crispy_buttons.py:62-73`). Make sure `submit_icon` and `delete_icon` are injected as defaults (e.g. in `get_submit_button_kwargs()` / `get_delete_button_kwargs()` or as `{"slot": "form:delete", "icon": self.delete_icon, **self.get_delete_button_kwargs()}`) so that:
  1. A subclass overriding `get_submit_button_kwargs()` / `get_delete_button_kwargs()` to return `{**super().get_submit_button_kwargs(), "icon": "custom"}` wins over `self.submit_icon` / `self.delete_icon`, and
  2. Existing subclasses in tests that override `get_delete_button_kwargs()` without calling `super()` (such as `EraseForm` in `tests/test1/test_crispy_buttons.py:52-54`, which returns `{"name": "delete", "value": "Erase"}`) still receive `delete_icon` (or `slot="form:delete"`'s default `delete` icon)!
  Putting `"icon": self.delete_icon` alongside `"slot": "form:delete"` in `get_delete_button()` (`Submit(**{"slot": "form:delete", "icon": self.delete_icon, **self.get_delete_button_kwargs()})`) and `"icon": self.submit_icon` in `get_submit_button()` (`Submit(**{"icon": self.submit_icon, **self.get_submit_button_kwargs()})`) guarantees that subclasses overriding `get_*_button_kwargs()` without `super()` still inherit `self.submit_icon` / `self.delete_icon`, while any `"icon"` key returned by `get_*_button_kwargs()` overrides it.

### 4. Suggestions
- In `src/crud_views/lib/crispy/form.py:59-63, 126-130`, pass `"icon": self.submit_icon` in `get_submit_button()` as `Submit(**{"icon": self.submit_icon, **self.get_submit_button_kwargs()})` and `"icon": self.delete_icon` in `get_delete_button()` as `Submit(**{"slot": "form:delete", "icon": self.delete_icon, **self.get_delete_button_kwargs()})` so both `submit_icon`/`delete_icon` class attributes and `get_*_button_kwargs()` overrides work even when a subclass does not call `super().get_*_button_kwargs()`.

### 5. Risk Assessment
- **LOW:** All icon names, class lookups, and form hooks follow established patterns in `icons.py` and `form.py`.

---

## 06-05

### 1. Summary
Plan `06-05` migrates `ListViewFilterFormHelper` in `src/crud_views/lib/views/list.py` from `self.add_input(Submit(...))` / `self.add_input(Reset(...))` to a `get_form_actions() -> FormActions | None` hook rendered through `Layout`, while isolating class-level `layout` declarations per instance, keeping hidden `sort`/`order`/`dir` inputs on `self.inputs`, and closing `M-EMPTY-REPLACEMENT` and `L-SUPPRESSION-MIGRATION`.

### 2. Strengths
- **Complete closure of `M-EMPTY-REPLACEMENT`:** Task 1 (`06-05-PLAN.md:72-80`) and Task 2 (`06-05-PLAN.md:117-125`) directly address `.venv/lib/python3.12/site-packages/crispy_forms/templatetags/crispy_forms_tags.py:109, 116, 147`. Because `BasicNode.get_render` calls `helper.get_attributes()` inside `get_response_dict()` at line 109 *before* checking `if helper and helper.layout:` at line 116, overriding `ListViewFilterFormHelper.get_attributes()` to detect caller assignments to `helper.layout` (by identity) and wrap an empty `Layout()` into a private truthy `Layout` subclass ensures `helper.render_layout()` is still invoked by `{% crispy form helper %}` without resurrecting discarded default fields.
- **Accurate handling of `display_form.html` empty `form_html` fallback:** Task 2 (`06-05-PLAN.md:122-125`) accurately accounts for `.venv/lib/python3.12/site-packages/crispy_bootstrap5/templates/bootstrap5/display_form.html:1-9`, where `{% if form.form_html %}{{ form.form_html }}{% else %}{% include "bootstrap5/uni_form.html" %}{% endif %}` falls back to `uni_form.html` when both fields and actions are empty (`form_html == ""`), while a default `get_form_actions()` with `helper.layout = Layout()` produces non-empty `form_html` (only the `FormActions` group) and does not render any fields.
- **Preservation of declared class `layout` when `form` is passed (`D-03`, `M-HELPER-STATE`):** In `.venv/lib/python3.12/site-packages/crispy_forms/helper.py:208-215`, `FormHelper.__init__(self, form=None)` overwrites `self.layout = self.build_default_layout(form)` whenever `form is not None`. Initializing `super().__init__()` without `form` and setting `if form is not None: self.form = form` while deep-copying any class-level `layout` preserves both `AuthorFilterFormHelper.layout` (`docs/reference/list_view.md:143-146`) and `helper.form` identity.
- **Underscore-prefixed internal state:** In `.venv/lib/python3.12/site-packages/crispy_forms/helper.py:340-346`, `FormHelper.get_attributes` copies every key in `self.__dict__` that does not start with `"_"` (except `"layout"` and `"inputs"`) into the template context. Task 1 (`06-05-PLAN.md:69`) explicitly requires all new lifecycle/tracking attributes on `ListViewFilterFormHelper` to start with `"_"` so nothing leaks into `response_dict`.

### 3. Concerns
- **LOW — `tests/test1/test_button_classes_templates.py` page rendering guard on `/publisher/` once filter buttons become `<button>` elements:** When `ListViewFilterFormHelper` moves Apply and Reset into `FormActions` in `06-05` Task 1, the filter buttons on `/publisher/` (`PublisherListView`) and `/publisher_order/card/` (`PublisherOrderCardListView`) render through `crud_views/tags/button/form.html` with `<span>{{ cv_label }}</span>` inside `<button>`. In `tests/test1/test_button_classes_templates.py:140-150`, `_offenders(doc)` inspects every sentinel-styled `<button>` AND every `<span>` descendant (`for node in (el, *el.iter("span")):`), flagging any class token on `<button>` or `<span>` that is not in `SENTINELS`, `cv-*`, or `BEHAVIOUR_TOKENS`. Because `form.html` uses `<span class="{% cv_button_class 'form' 'hidden-label' %}">` in `"icon"` mode and classless `<span>{{ cv_label }}</span>` in `"both"`/`"label"` mode, `_offenders(doc)` will pass as long as `form.html` does not put any non-table, non-`cv-*` class on its `<button>` or `<span>` elements.

### 4. Suggestions
- Run `.venv/bin/pytest tests/test1/test_button_classes_templates.py -q` alongside the `06-05` verification shard to confirm the migrated filter buttons on `/publisher/` and `/publisher_order/card/` pass `test_button_chain_renders_only_table_classes`.

### 5. Risk Assessment
- **LOW:** The `FormHelper` dispatch lifecycle (`get_attributes` → `if helper and helper.layout` → `render_layout`) has been verified line-by-line against `crispy_forms/templatetags/crispy_forms_tags.py:109-120` and `crispy_forms/helper.py:208-348`.

---

## 06-06

### 1. Summary
Plan `06-06` extends Django system checks (`crud_views.E106`, `viewset.E210`, `viewset.E211`, `viewset.W291`, `viewset.W292`) and runtime missing-icon handling in `cv_button_data` to cover form label-mode maps and icon-only form buttons. It closes `M-ICON-AVAILABILITY`, `H-DIAGNOSTIC-CONTRACT`, `H-DELETE-STATIC`, `M-REGISTRY-OFF`, and `M-POLYMORPHIC`.

### 2. Strengths
- **Complete closure of `M-ICON-AVAILABILITY`:** Task 2 (`06-06-PLAN.md:92-113`) uses `icons.resolve_icon(value)` (`src/crud_views/lib/icons.py:187-202`) in both static `W292` and runtime `cv_button_data` normalization. `resolve_icon(value)` returns `None` when `value` is `None`/`""`/whitespace or when `CRUD_VIEWS_ICONS` maps a semantic icon name to `None`/`""`, without calling `render_icon` or invoking any custom renderer callable (`icons.py:223-237`). It also preserves `icon_host_keys` (`src/crud_views/lib/view/button_data.py:41-49`) so a `form:icon-host` class slot set to `None`/`""` remains a host-placement opt-out rather than a missing semantic icon.
- **Provider-first static `W292` inspection (`H-DELETE-STATIC`, `M-POLYMORPHIC`):** In `src/crud_views/lib/crispy/form.py:116-142`, `CrispyDeleteForm` inherits from `CrispyForm` (and thus `CrispyFormMixin`, which defines `submit_icon = "save"`), but `CrispyDeleteForm.helper` (`form.py:132-142`) only renders `self.get_delete_button()` (`delete_icon`) and `self.get_cancel_button()`. Checking `issubclass(form_class, CrispyDeleteForm)` before `CrispyFormMixin` prevents false-positive `submit` warnings on delete views. Similarly, inspecting `dict`-valued `polymorphic_forms` (`src/crud_views_polymorphic/lib/utils.py:35`, `tests/test1/app/views.py:565-577`) statically without calling `self.get_form_class()` (`utils.py:64-72`, which requires `self.kwargs` / `self.get_object()`) avoids crashing system checks on polymorphic views.
- **Well-scoped form diagnostic contract (`H-DIAGNOSTIC-CONTRACT`):** Task 1 keeps `cv_label_mode_checks` (`src/crud_views/lib/view/action_menu.py:46-72`) byte-identical for `cv_list_actions_label_mode` and `cv_context_actions_label_mode` (which `tests/test1/test_action_label_mode_config.py:217-246` and `tests/test1/test_label_mode_docs.py:419-428` pin), while giving `cv_form_actions_label_mode` its own check function (`E211` for non-dict or non-`str` keys, `E210` for invalid mode values, `W291` for unknown keys on the view's own `cv_form_actions_label_mode` against `sorted(FORM_KINDS)`).

### 3. Concerns
- **LOW — `CheckUnknownAttributes` (`viewset.W280`) requires `cv_form_actions_label_mode` to be declared on `CrudView`:** In `src/crud_views/lib/check.py:297-307, 347-421`, `CheckUnknownAttributes` builds the known `cv_*` attribute vocabulary by inspecting `vars(klass)` and `klass.__annotations__` across `crud_views*` classes in the MRO. Because `06-03` Task 1 declares `cv_form_actions_label_mode: dict[str, str] | None = None` on `CrudView` (`src/crud_views/lib/view/base.py`), `W280` will automatically recognize `cv_form_actions_label_mode` on any `CrudView` subclass. However, note that `_VOCAB_CACHE` in `src/crud_views/lib/check.py:321-344` caches the vocabulary keyed by `len(_registered_view_classes())`; since `cv_form_actions_label_mode` is on `CrudView` itself, it is always in `self._context_names()` (`check.py:364-374`).
- **LOW — Static `W292` check on views without `CrispyViewMixin` or without `filterset_class`:** In `tests/test1/app/views.py:975-983`, `PublisherBcCreateView` and `PublisherBcUpdateView` inherit from `CreateView` / `UpdateView` with `fields = ["name"]` and `form_class = None` (no `CrispyViewMixin`). And a `ListViewTableFilterMixin` subclass may have `formhelper_class = None` (default at `src/crud_views/lib/views/mixins.py:309`). Ensure `cv_form_icon_mode_checks` only checks form classes that are concrete subclasses of `CrispyFormMixin` (or `CrispyDeleteForm`) and only checks filter helpers when `issubclass(getattr(cls, "formhelper_class", None) or object, ListViewFilterFormHelper)` is true.

### 4. Suggestions
- In `cv_form_icon_mode_checks` (`src/crud_views/lib/view/buttons.py`), guard form-class inspection with `isinstance(form_class, type) and issubclass(form_class, CrispyFormMixin)` and filter-helper inspection with `isinstance(helper_cls, type) and issubclass(helper_cls, ListViewFilterFormHelper) and getattr(cls, "filterset_class", None) is not None`.

### 5. Risk Assessment
- **LOW:** Static and runtime diagnostic rules are clearly specified, isolated from existing context/list check messages, and paired with comprehensive tests in `tests/test1/test_form_button_checks.py`.

---

## 06-07

### 1. Summary
Plan `06-07` validates browser-side interactions with real `<button>` elements across `tests/js/modal.test.js`, `tests/js/viewset.test.js`, and `tests/js/list.filter.test.js` using the locked JS environment wrapper from `06-01`, and adds the isolated `crispy_floor` session to `noxfile.py` testing Python 3.12 with Django 4.2 and 6.0 against `django-crispy-forms==2.0` and `crispy-bootstrap5==2023.10`.

### 2. Strengths
- **Production JS handlers already support `<button>` with nested `<span>`/`<i>` children:**
  - `src/crud_views/static/crud_views/js/modal.js:82, 137` uses `new FormData(form, submitter || undefined)` with `event.submitter`.
  - `src/crud_views/static/crud_views/js/viewset.js:40` uses `e.target.closest("[data-cv-cancel-url]")`, so clicks on nested `<i>` or `<span>` children inside `<button type="button" data-cv-cancel-url="...">` bubble and resolve to the `<button>` element.
  - `src/crud_views/static/crud_views/js/list.filter.js:57` binds `click` on `document.getElementById("filter-button-reset")`, so clicking a nested `<i>` or `<span>` inside `<button type="reset" id="filter-button-reset">` triggers `onReset` with `event.currentTarget` set to the button.
- **Single-transaction constraint in `noxfile.py`:** Task 3 (`06-07-PLAN.md:107-116`) installs `.[polymorphic,workflow,ordered,test]` together with `django-crispy-forms==2.0` and `crispy-bootstrap5==2023.10` in the same `session.install(...)` call in `noxfile.py`, preventing `uv` from upgrading `django-crispy-forms` or `crispy-bootstrap5` when installing the package extras (compare `noxfile.py:13-14`, which currently runs two separate `session.install` calls).

### 3. Concerns
- **LOW — `noxfile.py` default session list when running `nox` (`task test`):** In `noxfile.py:6, 22`, both existing `@nox.session` decorators omit `default=False`, so running `nox` without `-s` runs all defined sessions. If `crispy_floor` is decorated with `@nox.session(python=["3.12"], venv_backend="uv")` without checking whether `task test` (`nox`) is expected to run `crispy_floor` by default or only via `nox -s crispy_floor`, it will also run during `task test`. Either behavior is fine in `uv`, provided `crispy_floor` passes cleanly.

### 4. Suggestions
- In `noxfile.py`, pass `f"django~={django}.0"`, `".[polymorphic,workflow,ordered,test]"`, `"django-crispy-forms==2.0"`, and `"crispy-bootstrap5==2023.10"` in a single `session.install(...)` invocation inside `crispy_floor` so `uv` resolves all constraints simultaneously.

### 5. Risk Assessment
- **LOW:** The JS handlers (`modal.js`, `viewset.js`, `list.filter.js`) already use delegation (`closest(...)`), `getElementById(...)`, and `new FormData(form, submitter || undefined)`, and the `crispy_floor` session is isolated in `noxfile.py`.

---

## 06-08

### 1. Summary
Plan `06-08` updates reference documentation (`buttons.md`, `settings.md`, `action_menus.md`, `icons.md`, `theme.md`, `list_view.md`, `javascript.md`, `tutorial-5-filters-permissions.md`), adds executable documentation recipe tests in `tests/test1/test_form_button_docs.py` and `tests/test1/test_label_mode_docs.py`, pairs the `CHANGELOG.md` `### Breaking` entry with `docs/migrating-1.0.md`, updates the `tooltip.js` header comment, and enables `CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"form": "both"}` in `examples/bootstrap5/project/settings.py`.

### 2. Strengths
- **Complete closure of `L-SUPPRESSION-MIGRATION` and `M-SETTINGS-LIFECYCLE` in docs and tests:**
  - Task 1 (`06-08-PLAN.md:62-66`) documents in `docs/reference/settings.md` that `CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE` is read at startup on `crud_views_settings` (matching `tests/test1/test_label_mode_docs.py:456`), whereas `CRUD_VIEWS_LABEL_MODE_DEFAULTS` is read lazily on each render.
  - Tasks 2 and 3 (`06-08-PLAN.md:83-90, 106-109`) document and test in `tests/test1/test_form_button_docs.py` that clearing `helper.inputs = []` no longer suppresses stock Apply/Reset buttons and that overriding `get_form_actions(self)` to return `None` omits Apply/Reset while preserving filter fields and hidden `sort`/`order`/`dir` inputs.
- **Careful preservation of existing `test_label_mode_docs.py` invariants:** Task 1 (`06-08-PLAN.md:67-71`) explicitly preserves the existing `viewset.E211` scalar-knob count (`tests/test1/test_label_mode_docs.py:252, 423`, which asserts `_row(..., "\`viewset.E211\`")[...].count("string or None") == 2`) and the unique `- \`CRUD_VIEWS_LABEL_MODE_DEFAULTS\` sets` bullet prefix in `CHANGELOG.md` (`tests/test1/test_label_mode_docs.py:368`).

### 3. Concerns
- **LOW — `tests/test1/test_label_mode_docs.py` strict structural assertions on `settings.md`, `action_menus.md`, and `buttons.md`:** In `tests/test1/test_label_mode_docs.py`:
  1. `test_documented_card_floor_renders_label_only` (`lines 88-100`) parses every `python` fence in `docs/reference/settings.md` that assigns `CRUD_VIEWS_LABEL_MODE_DEFAULTS` with a `"card"` key and asserts `assert len(examples) == 1` and `assert examples[0] == {"card": "label"}`. Any new `CRUD_VIEWS_LABEL_MODE_DEFAULTS` example fence in `settings.md` for `"form"` must NOT include a `"card"` key in its dict literal (e.g. use `CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"form": "both"}`).
  2. `test_label_mode_configuration_table` (`lines 145-159`) checks `expected` rows in `### Label-mode configuration` of `settings.md`, where line 146 asserts `f"\`{SETTING}\`": ("merged per location", "project floor", '"card"')` — keep `"card"` in that row's keys cell when adding `"form"`.
  3. `test_button_label_mode_check_reference` (`lines 423-427`) asserts `e211.count("string or None") == 2` in `docs/reference/buttons.md` and `_row(checks, "\`viewset.E211\`")[1].count("string or None") == 2` in `docs/reference/action_menus.md` (`line 252`). When updating the `viewset.E211` row in `buttons.md` (`line 497`) and `action_menus.md` (`line 290`) to mention `cv_form_actions_label_mode`, do not add a third occurrence of the substring `"string or None"` in that row.
- **LOW — `docs/getting_started/tutorial-5-filters-permissions.md` `cv-sync` blocks:** `docs/getting_started/tutorial-5-filters-permissions.md:11, 26, 41, 78` contains four `<!-- cv-sync: ... -->` fenced code blocks verified verbatim against `examples/bootstrap5/library/views.py` and `examples/bootstrap5/library/seed.py` by `examples/bootstrap5/test_docs_sync.py:86-92`. Task 2 must only edit the prose at `tutorial-5-filters-permissions.md:32-34` (which currently says *"no submit button of its own — the list view renders one"*), leaving the fenced blocks untouched.

### 4. Suggestions
- In `docs/reference/settings.md`, write the new form floor fence as `CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"form": "both"}` (without `"card"`) so `test_documented_card_floor_renders_label_only` (`tests/test1/test_label_mode_docs.py:99-100`) still finds exactly one `"card"`-bearing assignment.
- In `docs/reference/buttons.md:497` and `docs/reference/action_menus.md:290`, keep the parenthetical `(cv_card_actions_label_mode is the string or None default of card views, cv_context_action_label_mode the string or None target-view default; ...)` with exactly two occurrences of `"string or None"`.

### 5. Risk Assessment
- **LOW:** Running `tests/test1/test_label_mode_docs.py`, `tests/test1/test_form_button_docs.py`, `examples/bootstrap5/test_docs_sync.py`, and `mkdocs build --strict` immediately validates all documentation and example changes.

---

## 06-09

### 1. Summary
Plan `06-09` executes the final integrated verification gates across Python, JavaScript, linter/formatter, `mkdocs build --strict`, and the `examples/bootstrap5` suite, and records the complete phase acceptance and downstream-theme follow-up in `.planning/phases/06-form-button-leaf/06-ACCEPTANCE.md` and `06-VALIDATION.md`.

### 2. Strengths
- **Complete closure of `L-EXAMPLE-COVERAGE`:** Task 2 and the Additional Integrated Gates (`06-09-PLAN.md:80-85, 224-235`) explicitly run `pytest` from `examples/bootstrap5` (so `examples/bootstrap5/pytest.ini:1-5` sets `DJANGO_SETTINGS_MODULE = project.settings`) covering:
  - `examples/bootstrap5/project/tests.py::SystemChecksTest::test_no_check_errors_with_every_viewset_registered` (`project/tests.py:97-115`),
  - `examples/bootstrap5/test_docs_sync.py` (`test_docs_sync.py:86-92`),
  - `examples/bootstrap5/test_i18n.py` (including `test_demo_pages_render_german` at `test_i18n.py:121-136`, which asserts `assert 'value="Sichern"' in html` on `/library/author/create/`),
  - `examples/bootstrap5/project/tests.py::HomePageTest::test_every_feature_landing_page_renders` (`project/tests.py:45-51`),
  - `examples/bootstrap5/test_doc_links.py` (`test_doc_links.py:118-147`).
- **Auditable baseline-commit and golden-diff verification:** Task 1 (`06-09-PLAN.md:56-65`) verifies git ancestry and `src/` blob equality of the `06-01` baseline commits and confirms that no unrelated golden files under `tests/test1/golden/` (`form_frame`, `table_pagination`, `card_pagination`, `alerts`, `heading_level`, `action_menus`) were modified.

### 3. Concerns
- **LOW — Full `examples/bootstrap5` feature app tests (`library/tests.py`, `workflow/tests.py`, `polymorphic_demo/tests.py`, etc.):** In `examples/bootstrap5/`, in addition to `test_i18n.py`, `project/tests.py`, `test_doc_links.py`, and `test_docs_sync.py`, there are feature-app test modules (`library/tests.py`, `workflow/tests.py`, `polymorphic_demo/tests.py`, `formsets/tests.py`, `conditional/tests.py`, `action_menus/tests.py`, `context_buttons/tests.py`, `showcase/tests.py`, `nested/tests.py`, `guardian_demo/tests.py`, `object_detail/tests.py`, `breadcrumbs/tests.py`, `resources/tests.py`) that `nox -s examples` (`noxfile.py:32-33`) runs when executing bare `pytest` inside `./examples/bootstrap5`. Running the full `cd examples/bootstrap5 && ../../.venv/bin/pytest -q` (or including the feature-app test modules alongside the named example gates) ensures every example CRUD/workflow/polymorphic POST and cancel assertion (such as `examples/bootstrap5/library/tests.py:45-93`) is also verified under `CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"form": "both"}`.

### 4. Suggestions
- In `06-09` Task 2, after running the targeted example gates (`SystemChecksTest`, `test_docs_sync.py`, `test_i18n.py`, `HomePageTest`, `test_doc_links.py`), also run `cd examples/bootstrap5 && ../../.venv/bin/pytest -q` so the entire `examples/bootstrap5` test suite (identical to `noxfile.py:32-33`) is evidenced in `06-ACCEPTANCE.md`.

### 5. Risk Assessment
- **LOW:** `06-09` is a pure verification and documentation-recording plan with clear blocking criteria if any gate fails.

---

## Cross-Plan Assessment & Cycle 3 Closure Summary

| Prior Finding | Cycle 3 Status | Source Verification |
|---|---|---|
| `M-SETTINGS-LIFECYCLE` | **Closed** (`06-01`, `06-03`, `06-08`) | Verified against `src/crud_views/lib/settings.py:13-14, 67-68, 320` (`from_settings` import-time snapshot on `crud_views_settings`) vs `src/crud_views/lib/view/label_mode.py:54-58` (lazy `_raw_label_mode_defaults()`). |
| `M-EMPTY-REPLACEMENT` | **Closed** (`06-01`, `06-05`) | Verified against `crispy_forms/templatetags/crispy_forms_tags.py:109, 116, 147`, `crispy_forms/layout.py:38-39`, and `crispy_bootstrap5/templates/bootstrap5/display_form.html:1-9`. Preparing `helper.layout` in `ListViewFilterFormHelper.get_attributes()` runs before `if helper and helper.layout:`. |
| `L-SUPPRESSION-MIGRATION` | **Closed** (`06-01`, `06-05`, `06-08`) | Verified against `src/crud_views/lib/views/list.py:70-87`. Documented and tested in `06-08` Tasks 2 & 3 (`get_form_actions() -> None` replaces `helper.inputs = []`). |
| `M-ICON-AVAILABILITY` | **Closed** (`06-01`, `06-06`) | Verified against `src/crud_views/lib/icons.py:187-260` (`resolve_icon` vs `render_icon` and `resolve_icon_name_class`) and `src/crud_views/lib/view/button_data.py:41-49` (`icon_host_keys`). |
| `L-EXAMPLE-COVERAGE` | **Closed** (`06-08`, `06-09`) | Verified against `examples/bootstrap5/pytest.ini:1-5`, `examples/bootstrap5/test_i18n.py:121-136`, `examples/bootstrap5/project/tests.py:45-51, 97-115`, and `examples/bootstrap5/test_doc_links.py:118-147`. |
| `H-OVERLAY-PROVENANCE` | **Closed / Dispositioned** (`06-03`) | Verified against `crispy_forms/templatetags/crispy_forms_tags.py:109-113, 147-185` and `crispy_forms/helper.py:340-346`: `BasicNode.get_response_dict` produces a deterministic `response_dict` layer in `Context.dicts`. |

### Overall Risk Assessment
- **Overall Risk:** **LOW**
- **Justification:** All five actionable findings from cycle 2 are closed with mechanisms that match the live repository and installed dependency code (`django-crispy-forms` 2.6 / `crispy-bootstrap5` 2026.3). No HIGH or MEDIUM defects remain; the remaining observations are LOW-severity implementation pointers (keeping `src/` comments free of `btn` tokens for `test_button_classes_templates.py:21`, updating the 4-location count in `test_label_mode.py:155`, preserving the 2-occurrence `"string or None"` invariant in `test_label_mode_docs.py:252, 423`, and rendering `formset.html` directly in `06-03` Task 2 because `cv_x_formset` uses `@register.inclusion_tag`). The plans are ready for execution.


---

## Consensus Summary

Cycle 3 independently reviewed the nine plans at `be0aa152408023b669a0a4a1c23f2ffcd36f8b08`. Earlier complete review outputs remain in git (`6089258` and `b883e7b`); historical quotations are not current concerns. This is pre-execution review: closure requires a valid executable plan, not future implementation already existing.

### Agreed Strengths

The reviewers confirm the actual working-branch prerequisite contracts, atomic location/default/class-key consumers, literal layout-render bypass, whole-map settings lifecycle, slot-driven icons, provider-aware diagnostics, native browser/locked-runtime gates, paired migration, and separate example-consumer verification. D-18 remains authoritative; no merge-to-main gate is reopened.

### Previous Findings Rechecked

| Previous finding | Current disposition |
|---|---|
| M-SETTINGS-LIFECYCLE | Closed at plan level. 06-03 task 1 and 06-08 task 1 explicitly preserve import-time singleton maps, distinguish the lazy floor, and test/document that distinction. Source: `src/crud_views/lib/settings.py:13`, `:320`; `src/crud_views/lib/view/label_mode.py:54`. |
| M-EMPTY-REPLACEMENT | Preparation timing is corrected, but the proposed truthy-layout mechanism is insufficient. Superseded by the concrete H-HELPER-TRUTHINESS below; do not count the same defect twice. |
| L-SUPPRESSION-MIGRATION | Closed. 06-08 tasks 2/3 explicitly replace clearing helper.inputs with the None hook and test preserved fields/hidden controls. |
| M-ICON-AVAILABILITY | Original double-render/host concern closed. 06-06 task 2 uses non-rendering semantic resolution plus counting-renderer and host tests. A distinct unregistered per-form prefix hole remains below. |
| L-EXAMPLE-COVERAGE | Closed. 06-09's added command runs translations, feature landing pages, and doc links under the example settings, separately from root tests and SystemChecksTest. |
| H-OVERLAY-PROVENANCE | Rejected existence premise remains rejected. Installed get_response_dict has inputs/is_formset/template_pack metadata, and current reviewers acknowledge it. No suppressed HIGH from that prior claim remains current. The independent nested-owner edge is considered separately below. |

**Current result:** one HIGH blocker and three actionable non-HIGH findings. All three configured reviewers produced source-cited nine-plan reviews; Gemini succeeded on its single retry.

### Unresolved Findings

**H-HELPER-TRUTHINESS — HIGH / BLOCKER; plans 06-01 and 06-05, task 1.** Required property: empty/no-layout filter helpers must pass both terms of crispy's dispatch guard and reach the planned render lifecycle without restoring caller-discarded fields. Evidence: `06-05-PLAN.md:82-83` prescribes an empty prepared Layout whose `__bool__` returns True while fields/actions are populated later in render_layout; `06-01-PLAN.md:149-156` records that mechanism into the spec. Installed `.venv/lib/python3.12/site-packages/crispy_forms/templatetags/crispy_forms_tags.py:116` first evaluates `helper` in `if helper and helper.layout`. FormHelper inherits DynamicLayoutHandler.__len__ (`.venv/lib/python3.12/site-packages/crispy_forms/helper.py:99-106`), returning `len(self.layout.fields)`, and defines no __bool__. An empty-fields helper therefore short-circuits before the layout's truthiness is consulted. The test would catch the failure during execution, but cannot make the planned mechanism valid. Example remedy, non-binding: explicitly make both the helper and prepared layout truthy before dispatch, retaining the real-tag default/None/empty-group and replacement tests. Fixing only helper truthiness while leaving an ordinary empty falsy Layout would still fail the second term; no global crispy override is needed.

**M-OUTER-HELPER-PAGE — MEDIUM / WARNING; plans 06-01 and 06-03, ownership contract/task 2.** Required property: page fallback for an ownerless embedded row with a None current-helper owner must not select an enclosing crispy helper's owner. Evidence: `06-03-PLAN.md:105-106` identifies the current overlay and asks for a lower page owner, but its conflicting-owner fixture names outer form, row form, current helper and page, without a distinct enclosing helper carrying its own view. Every helper's public view is published by `.venv/lib/python3.12/site-packages/crispy_forms/helper.py:340-346`; nested invocations copy and push response dictionaries at `crispy_forms_tags.py:109-114`, so another helper's non-None view can sit below the current overlay. Fable and Grok independently identify this separate walk/fixture gap. The existing prohibition on selecting an outer owner is the intended invariant, but the actual boundary and this separate outer-helper input remain unspecified. Example remedy, non-binding: define which lower dictionaries qualify as page context, exclude enclosing helper overlays, and add an explicit current-helper=None/outer-helper≠page regression. This does not reopen D-09 or assert a nonexistent provenance API.

**L-UNREGISTERED-FORM-ICON — LOW / WARNING; plan 06-06, task 2.** Required property: an icon-only per-form value that cannot resolve to a registered renderer must not escape both diagnostics and the runtime accessibility policy under a false claim of separate registry coverage. Evidence: `06-06-PLAN.md:115` limits availability to resolve_icon returning None and delegates unregistered names to separate registry diagnostics. `src/crud_views/lib/icons.py:199-202` returns a non-None tuple for an unknown `prefix:name`, but `:230-236` renders it empty. Registry W352 iterates only get_icons entries (`:413-432`); it does not inspect a form's direct submit_icon='unknown:save'. That direct value can therefore produce hidden text with no visible icon and no promised warning/fallback. Example remedy, non-binding: check the resolved prefix's registered library/renderer availability without invoking a renderer, or explicitly document/test a justified disposition for this direct-value case. Preserve valid host opt-outs, raw-class semantics, and the one-render contract.

**L-FORMSET-PAGE-CONTEXT — LOW / WARNING; plan 06-03, task 2.** Required property: owner fallback tests must represent the production formset entry path, and page-owner loss at its context boundary must be handled or explicitly dispositioned. Evidence: Gemini traces `src/crud_views/lib/formsets/layout.py:17` flattening the outer context, `src/crud_views/templates/crud_views/formsets/formsets.html:6,9` calling cv_x_formset, and `src/crud_views/templatetags/crud_views_formsets.py:6-9` returning only x_formset. Django's `.venv/lib/python3.12/site-packages/django/template/library.py:377-384` then creates a fresh context, preserving CSRF but not page view; nested rows repeat this inclusion at `src/crud_views/templates/crud_views/formsets/formset.html:48`. Consequently the adapter cannot recover an owner that was discarded upstream. 06-03 task 2 owns only buttons.py and its test file and asks for the package row-template path with page fallback, without any upstream owner transport or explicit isolated-row disposition. A direct include with an injected page context tests a different path and does not establish that production behavior. Example remedy, non-binding: exercise the actual Formsets/inclusion chain and preserve the chosen owner information across its boundaries, or explicitly define/test a justified isolated-row limitation consistent with D-09 through D-12. Do not silently substitute a direct-template-only test or introduce global context leakage.

### HIGH Consensus Gate

H-HELPER-TRUTHINESS is a correctness/judgment claim, grounded in the actual helper length method and short-circuit guard. It counts even if only one full-weight reviewer raised it; it is not a missing-symbol claim and requires no second vote. The supporting source was independently inspected. Grok and Gemini sign off empty replacement after checking get_attributes ordering and layout truthiness, but neither evaluates inherited helper.__len__; their positive assessment does not refute the short-circuit defect. A majority vote cannot override the demonstrated mechanism. No future implementation was demanded to close a plan-level concern. H-OVERLAY-PROVENANCE is historical and explicitly rejected; its existence premise is not used to manufacture a current HIGH.

### Other Suggestions Already Covered or Advisory

| Suggestion | Executable coverage or disposition |
|---|---|
| Capture raw kwargs/classes before inherited flattening; demote SafeString concretely | 06-01 requires SafeData-free plain text and exactly-once attributes/classes; 06-02 retains raw kwargs, preserves legacy flat_attrs separately, and tests actual decoded malicious SafeString output. A particular capture/demotion idiom is implementation guidance. |
| Keep action-only parameter lists separate; do not inherit empty-label-to-icon behavior | 06-02 explicitly branches before action derivation, retains LEAF_KEYS/action behavior and separate FORM_LEAF_KEYS, and requires form-specific contexts plus preserved empty literals. No task instructs feeding action contexts into form tests. |
| Pop icon kwarg; register host fixture semantic names; do not treat raw classes as missing | 06-04 declares icon= configuration never serialized, covers all five semantic kinds and host libraries; 06-06 explicitly uses semantic resolution and preserves valid host opt-outs. These properties already have tasks and assertions. |
| Repeated get_attributes must preserve prepared identity | 06-05:83 explicitly forbids replacing a prepared layout or appending actions on repeated get_attributes calls, ties state to replacement identity, and task 2 tests repeated/interleaved rendering. |
| Separate finite form validator | 06-06 task 1 explicitly rejects unknown finite form keys while preserving open context/list policy. Naming a preferred new function is unnecessary for coverage. |
| Native nested reset/cancel and conditional JS edits | 06-07 task 2 already uses nested targets, expects one action, and keeps source changes conditional. |
| Keep translated value attribute; do not mistake landing-page 200 for button evidence | 06-02 preserves name/value and 06-09 separately runs the translated form assertion, real golden/request evidence and observed browser checks. No plan claims landing status alone proves buttons. |
| Single resolver transaction for crispy floors; preserve existing nox sessions | 06-07 task 3 explicitly requires both pins and extras in the same transaction and preserves existing sessions. A literal session.install spelling is optional implementation guidance. |
| Empty-layout plus None-hook pack fallback | 06-05:109 already explicitly dispositions the unchanged uni_form fallback, distinguishing empty selected layout from pack-rendered fields. The known fallback is visible to execution; no global template override or new fields-suppression guarantee is authorized. |
| Example collection environment failures | 06-09 requires actual collection, explicit environment/browser blockers, exact commands and no false pass. Installing a missing declared example dependency during authorized execution is environment preparation; the review does not certify future collection. |
| Node acquisition belongs in a later wave / scope quality | Current VALIDATION requires integrated-wave JS sampling and 06-01 explicitly establishes the compatible runtime before it. Acquisition failure remains a blocker, not a pass. Task partition preferences do not create a new invisible phase requirement. |

| Gemini: stable golden filter query | 06-01 task 3 establishes the same phase-owned harness and nonempty query; 06-05 reuses it and compares unchanged hidden values to the baseline. A module constant is one implementation option. |
| Gemini: raw-source btn token guard and extra focused shards | 06-02 uses class-table lookups and runs the template class guard; 06-05 preserves that contract and mandatory integrated-wave full Python sampling runs the guard after migration. No plan directs literal button classes in comments or templates. |
| Gemini: four test_label_mode assertions | 06-02 task 1 explicitly owns location/default assertions in this file before its tracer; task 2 and integrated-wave validation run it. Another immediate command placement is advisory, not missing ownership. |
| Gemini: kwargs override without calling super | 06-04 task 2 explicitly makes hook kwargs win, then explicit form icon, then adapter kind default. The property covers subclasses that replace the kwargs dictionary; a precise merge-expression spelling is discretionary. |
| Gemini: W280 vocabulary and non-crispy/static providers | 06-03 adds the declared CrudView attribute; 06-06 restricts inspection to concrete known package providers, skips absent/dynamic providers, and drives actual registered checks without exceptions. |
| Gemini: nox default session participation | Either default participation is acceptable by the reviewer; 06-07 defines an isolated session and preserves existing sessions. This is an implementation choice, not a missing invariant. |
| Gemini: documentation structural guards and cv-sync fences | 06-08 explicitly retains existing message assertions, unique changelog prefix, synced fences and documentation tests. The suggested concrete fence spelling satisfies an existing invariant rather than adding work. |
| Gemini: run every example feature test | Additional breadth is advisory: named affected example consumers are covered in 06-09, while CRUD/workflow/cancel behavior is separately required by full package tests and observed example browser flows. The reviewer identifies additional existing tests, not a concrete uncovered new behavior or a plan instruction to weaken them. The full example suite may be run during execution; it is not a reopened L-EXAMPLE-COVERAGE defect. |

### Structured Issues

```yaml
issues:
  - id: H-HELPER-TRUTHINESS
    plan: "06-05"
    related_plans: ["06-01"]
    task: 1
    dimension: key_links_planned
    severity: blocker
    review_severity: HIGH
    required_property: "Empty/no-layout helpers pass both helper and layout truthiness guards before render_layout."
    description: "06-05:82-83 only makes Layout truthy, but crispy_forms_tags.py:116 first tests helper; inherited helper.py:99-103 returns zero for empty layout.fields."
    fix_hint: "Ensure both objects pass dispatch and retain real-tag empty replacement/no-layout regressions; a package helper __bool__ plus truthy prepared layout is one route."
  - id: M-OUTER-HELPER-PAGE
    plan: "06-03"
    related_plans: ["06-01"]
    task: 2
    dimension: task_completeness
    severity: warning
    review_severity: MEDIUM
    required_property: "Nested fallback distinguishes the page from enclosing helpers whose response overlays also contain view."
    description: "06-03:105-106 identifies current overlay but lacks a distinct outer-helper-with-view fallback fixture; helper.py:340-346 and crispy_forms_tags.py:109-114 publish and preserve such older overlays."
    fix_hint: "Specify the page boundary and test current-helper None against conflicting outer-helper and page owners."
  - id: L-UNREGISTERED-FORM-ICON
    plan: "06-06"
    task: 2
    dimension: key_links_planned
    severity: warning
    review_severity: LOW
    required_property: "Unavailable direct per-form icon prefixes are handled or explicitly dispositioned without relying on unrelated registry-table diagnostics."
    description: "06-06:115 assumes separate diagnostics, while icons.py:413-432 only checks table entries; direct unknown-prefix submit_icon passes resolve_icon and renders empty at :230-236."
    fix_hint: "Validate the resolved prefix without calling renderers and add direct per-form strict/non-strict coverage, or record a justified explicit disposition."
  - id: L-FORMSET-PAGE-CONTEXT
    plan: "06-03"
    task: 2
    dimension: key_links_planned
    severity: warning
    review_severity: LOW
    required_property: "Production formset context boundaries preserve required owner semantics or have an explicit tested disposition."
    description: "Formsets.render flattens context at layout.py:17 and cv_x_formset returns only x_formset at crud_views_formsets.py:6-9; InclusionNode creates context.new at library.py:377. A direct include with page view bypasses that production loss."
    fix_hint: "Exercise actual inclusion dispatch and preserve needed owner metadata, or explicitly disposition isolated-row semantics within locked ownership decisions."
```

Remediation examples are non-binding; any mechanism meeting the stated property addresses the finding.

### Cross-artifact Fact Drift

- Deterministic phase-status result: `lag`, STATE Planning versus ROADMAP Planned (ranks 0/1). This is not a finding; STATE.md is the status authority.
- ROADMAP FORM-01..13 requirement IDs match claimed plan requirements; real-button, escaping, modes, semantic icons, diagnostics, and migration/example truths agree.
- CONTEXT D-01..18 and plans agree on locked scope, whole-map selection, literal text, quiet legacy input retention, and working-branch prerequisites. Missing D-18 from RESEARCH's older copied context is not a contradictory statement.
- ROADMAP.md:227's historical assertion that the existing delete test posts delete=Delete is inaccurate against tests/test1/test_crud.py:63. Plans explicitly preserve confirm=True and separately add the clicked-submitter payload; this already-dispositioned source fact is not grounds to remove confirmation or reopen scope. It contributes to neither convergence count.
- All four axes were inspected; no missing artifact axis was silently treated as verified. Additional plan truths are allowed. No countable cross-artifact finding is introduced.


## Verification coverage

Effective authority: `intel` (deterministic drift-guard result). `.planning/intel/API-SURFACE.md:5` explicitly reports an incomplete empty index; `api-map.json` is absent. Every non-new reference below remains **UNCHECKABLE / INFO** under that authority, including signatures and CLI flags. `drift-guard severity --status UNCHECKABLE --authority intel` returned INFO, hardBlock=false. Supplemental exact-file/AST declaration evidence is independent read-only context, **not** an intel VERIFIED verdict. Multiple declaration candidates remain ambiguous and do not prove a call signature; absent candidates mean unchecked, never missing. Paths never use token/fuzzy symbol matching. New phase outputs are excluded rather than demanded before execution.

Inventory: 301 unique references, 59 explicitly new exclusions. Every entry carries current-plan line citations and an exact quoted plan line; repeated occurrences are listed.

<details>
<summary><code>--check</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-09-PLAN.md:233` — &lt;automated&gt;.venv/bin/ruff format --check&lt;/automated&gt;

Occurrences: `.planning/phases/06-form-button-leaf/06-09-PLAN.md:233`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>--prefix</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:108` — Then invoke that absolute Node with its recorded npm-cli.js and --prefix . test, forwarding supplied test

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:108`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>--strict</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-08-PLAN.md:122` — &lt;automated&gt;.venv/bin/mkdocs build --strict&lt;/automated&gt;

Occurrences: `.planning/phases/06-form-button-leaf/06-08-PLAN.md:122`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:88`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>-SUMMARY.md</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-09-PLAN.md:67` — &lt;read_first&gt;All 06-*-SUMMARY.md files; 06-SPEC.md; 06-VALIDATION.md; 06-01 baseline commit evidence; tests/test1/test_crud.py; tests/test1/test_cancel_origin.py&lt;/read_first&gt;

Occurrences: `.planning/phases/06-form-button-leaf/06-09-PLAN.md:67`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>-n</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-09-PLAN.md:72` — &lt;automated&gt;.venv/bin/pytest tests -n auto&lt;/automated&gt;

Occurrences: `.planning/phases/06-form-button-leaf/06-09-PLAN.md:72`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>-q</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:91` — /test1/test_action_label_mode_config.py tests/test1/test_button_classes.py -q; record the command,

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:91`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:174`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:201`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:222`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:102`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:126`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:141`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:85`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:109`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:86`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:107`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:87`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:112`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:90`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:120`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:89`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:105`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:237`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:241`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:245`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>-s</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-07-PLAN.md:118` — &lt;automated&gt;.venv/bin/nox -s crispy_floor&lt;/automated&gt;

Occurrences: `.planning/phases/06-form-button-leaf/06-07-PLAN.md:118`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>../../.venv/bin/pytest</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-09-PLAN.md:237` — &lt;automated&gt;cd examples/bootstrap5 &amp;&amp; ../../.venv/bin/pytest project/tests.py::SystemChecksTest::test_no_check_errors_with_every_viewset_registered -q&lt;/automated&gt;

Occurrences: `.planning/phases/06-form-button-leaf/06-09-PLAN.md:237`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:241`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:245`.

Supplemental exact path/declaration candidates: `.venv/bin/pytest:1`.

</details>

<details>
<summary><code>.planning/PROJECT.md</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:54` — @.planning/PROJECT.md

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:54`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:67`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:54`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:56`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:55`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:57`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:53`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:64`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:49`.

Supplemental exact path/declaration candidates: `.planning/PROJECT.md:1`.

</details>

<details>
<summary><code>.planning/REQUIREMENTS.md</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:57` — @.planning/REQUIREMENTS.md

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:57`.

Supplemental exact path/declaration candidates: `.planning/REQUIREMENTS.md:1`.

</details>

<details>
<summary><code>.planning/ROADMAP.md</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:55` — @.planning/ROADMAP.md

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:55`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:68`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:55`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:57`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:56`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:58`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:54`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:65`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:50`.

Supplemental exact path/declaration candidates: `.planning/ROADMAP.md:1`.

</details>

<details>
<summary><code>.planning/STATE.md</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:56` — @.planning/STATE.md

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:56`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:69`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:56`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:58`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:57`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:59`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:55`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:66`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:51`.

Supplemental exact path/declaration candidates: `.planning/STATE.md:1`.

</details>

<details>
<summary><code>.planning/phases/01-label-mode-defaults/01-CONTEXT.md</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:79` — .planning/phases/01-label-mode-defaults/01-CONTEXT.md; .planning/phases/02-form-key-grammar/02-CONTEXT.md;

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:79`.

Supplemental exact path/declaration candidates: `.planning/phases/01-label-mode-defaults/01-CONTEXT.md:1`.

</details>

<details>
<summary><code>.planning/phases/02-form-key-grammar/02-CONTEXT.md</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:79` — .planning/phases/01-label-mode-defaults/01-CONTEXT.md; .planning/phases/02-form-key-grammar/02-CONTEXT.md;

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:79`.

Supplemental exact path/declaration candidates: `.planning/phases/02-form-key-grammar/02-CONTEXT.md:1`.

</details>

<details>
<summary><code>.planning/phases/06-form-button-leaf/06-01-SUMMARY.md</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:290` — Create .planning/phases/06-form-button-leaf/06-01-SUMMARY.md with prerequisite and baseline commit evidence.

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:290`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>.planning/phases/06-form-button-leaf/06-02-SUMMARY.md</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-02-PLAN.md:186` — Create .planning/phases/06-form-button-leaf/06-02-SUMMARY.md.

Occurrences: `.planning/phases/06-form-button-leaf/06-02-PLAN.md:186`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>.planning/phases/06-form-button-leaf/06-03-SUMMARY.md</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-03-PLAN.md:162` — Create .planning/phases/06-form-button-leaf/06-03-SUMMARY.md.

Occurrences: `.planning/phases/06-form-button-leaf/06-03-PLAN.md:162`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>.planning/phases/06-form-button-leaf/06-04-SUMMARY.md</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-04-PLAN.md:147` — Create .planning/phases/06-form-button-leaf/06-04-SUMMARY.md.

Occurrences: `.planning/phases/06-form-button-leaf/06-04-PLAN.md:147`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>.planning/phases/06-form-button-leaf/06-05-SUMMARY.md</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-05-PLAN.md:168` — Create .planning/phases/06-form-button-leaf/06-05-SUMMARY.md.

Occurrences: `.planning/phases/06-form-button-leaf/06-05-PLAN.md:168`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>.planning/phases/06-form-button-leaf/06-06-SUMMARY.md</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-06-PLAN.md:176` — Create .planning/phases/06-form-button-leaf/06-06-SUMMARY.md.

Occurrences: `.planning/phases/06-form-button-leaf/06-06-PLAN.md:176`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>.planning/phases/06-form-button-leaf/06-07-SUMMARY.md</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-07-PLAN.md:160` — Create .planning/phases/06-form-button-leaf/06-07-SUMMARY.md.

Occurrences: `.planning/phases/06-form-button-leaf/06-07-PLAN.md:160`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>.planning/phases/06-form-button-leaf/06-08-SUMMARY.md</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-08-PLAN.md:179` — Create .planning/phases/06-form-button-leaf/06-08-SUMMARY.md.

Occurrences: `.planning/phases/06-form-button-leaf/06-08-PLAN.md:179`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>.planning/phases/06-form-button-leaf/06-09-SUMMARY.md</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-09-PLAN.md:294` — Create .planning/phases/06-form-button-leaf/06-09-SUMMARY.md.

Occurrences: `.planning/phases/06-form-button-leaf/06-09-PLAN.md:294`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>.planning/phases/06-form-button-leaf/06-ACCEPTANCE.md</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-09-PLAN.md:8` — - .planning/phases/06-form-button-leaf/06-ACCEPTANCE.md

Occurrences: `.planning/phases/06-form-button-leaf/06-09-PLAN.md:8`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:25`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:30`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:61`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:66`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:81`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>.planning/phases/06-form-button-leaf/06-CONTEXT.md</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:58` — @.planning/phases/06-form-button-leaf/06-CONTEXT.md

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:58`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:70`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:57`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:59`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:58`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:60`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:56`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:67`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:52`.

Supplemental exact path/declaration candidates: `.planning/phases/06-form-button-leaf/06-CONTEXT.md:1`.

</details>

<details>
<summary><code>.planning/phases/06-form-button-leaf/06-JS-RUNTIME.json</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:10` — - .planning/phases/06-form-button-leaf/06-JS-RUNTIME.json

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:10`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:77`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>.planning/phases/06-form-button-leaf/06-PATTERNS.md</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:60` — @.planning/phases/06-form-button-leaf/06-PATTERNS.md

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:60`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:72`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:59`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:61`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:60`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:62`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:58`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:69`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:54`.

Supplemental exact path/declaration candidates: `.planning/phases/06-form-button-leaf/06-PATTERNS.md:1`.

</details>

<details>
<summary><code>.planning/phases/06-form-button-leaf/06-RESEARCH.md</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:59` — @.planning/phases/06-form-button-leaf/06-RESEARCH.md

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:59`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:71`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:58`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:60`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:59`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:61`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:57`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:68`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:53`.

Supplemental exact path/declaration candidates: `.planning/phases/06-form-button-leaf/06-RESEARCH.md:1`.

</details>

<details>
<summary><code>.planning/phases/06-form-button-leaf/06-SPEC.md</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:8` — - .planning/phases/06-form-button-leaf/06-SPEC.md

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:8`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:31`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:77`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:174`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:184`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:211`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:73`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:60`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:62`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:61`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:63`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:59`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:70`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:55`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>.planning/phases/06-form-button-leaf/06-VALIDATION.md</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:61` — @.planning/phases/06-form-button-leaf/06-VALIDATION.md

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:61`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:9`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:27`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:33`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:66`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:81`.

Supplemental exact path/declaration candidates: `.planning/phases/06-form-button-leaf/06-VALIDATION.md:1`.

</details>

<details>
<summary><code>.planning/phases/06-form-button-leaf/06-js-verify.sh</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:9` — - .planning/phases/06-form-button-leaf/06-js-verify.sh

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:9`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:77`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:112`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:83`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:103`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:225`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>.venv/bin/mkdocs</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-08-PLAN.md:122` — &lt;automated&gt;.venv/bin/mkdocs build --strict&lt;/automated&gt;

Occurrences: `.planning/phases/06-form-button-leaf/06-08-PLAN.md:122`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:88`.

Supplemental exact path/declaration candidates: `.venv/bin/mkdocs:1`.

</details>

<details>
<summary><code>.venv/bin/nox</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-07-PLAN.md:118` — &lt;automated&gt;.venv/bin/nox -s crispy_floor&lt;/automated&gt;

Occurrences: `.planning/phases/06-form-button-leaf/06-07-PLAN.md:118`.

Supplemental exact path/declaration candidates: `.venv/bin/nox:1`.

</details>

<details>
<summary><code>.venv/bin/pytest</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:90` — VARIANT_LOCATIONS. Before authoring the spec, run .venv/bin/pytest tests/test1/test_label_mode.py

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:90`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:174`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:201`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:222`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:102`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:126`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:141`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:85`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:109`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:86`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:107`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:87`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:112`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:90`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:120`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:89`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:105`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:72`.

Supplemental exact path/declaration candidates: `.venv/bin/pytest:1`.

</details>

<details>
<summary><code>.venv/bin/python</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:174` — &lt;automated&gt;.venv/bin/python -c &#x27;from pathlib import Path; import re; p=Path(&quot;.planning/phases/06-form-button-leaf/06-SPEC.md&quot;); s=p.read_text(); headings=(&quot;Prerequisite evidence

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:174`.

Supplemental exact path/declaration candidates: `.venv/bin/python (file exists; binary)`.

</details>

<details>
<summary><code>.venv/bin/ruff</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-09-PLAN.md:229` — &lt;automated&gt;.venv/bin/ruff check&lt;/automated&gt;

Occurrences: `.planning/phases/06-form-button-leaf/06-09-PLAN.md:229`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:233`.

Supplemental exact path/declaration candidates: `.venv/bin/ruff (file exists; binary)`.

</details>

<details>
<summary><code>/home/alex/.codex/gsd-core/templates/summary.md</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:49` — @/home/alex/.codex/gsd-core/templates/summary.md

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:49`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:62`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:49`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:51`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:50`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:52`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:48`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:59`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:44`.

Supplemental exact path/declaration candidates: `/home/alex/.codex/gsd-core/templates/summary.md:1`.

</details>

<details>
<summary><code>/home/alex/.codex/gsd-core/workflows/execute-plan.md</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:48` — @/home/alex/.codex/gsd-core/workflows/execute-plan.md

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:48`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:61`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:48`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:50`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:49`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:51`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:47`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:58`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:43`.

Supplemental exact path/declaration candidates: `/home/alex/.codex/gsd-core/workflows/execute-plan.md:1`.

</details>

<details>
<summary><code>06-01-SUMMARY.md</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-02-PLAN.md:86` — &lt;read_first&gt;06-01-SUMMARY.md in this phase directory; src/crud_views/templates/crud_views/tags/button/action.html; src/crud_views/lib/crispy/buttons.py; src/crud_views/lib/view/b

Occurrences: `.planning/phases/06-form-button-leaf/06-02-PLAN.md:86`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:136`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>06-07-SUMMARY.md</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-09-PLAN.md:82` — examples/bootstrap5/test_doc_links.py; docs/migrating-1.0.md Form buttons; 06-07-SUMMARY.md; 06-08-SUMMARY.md; 06-VALIDATION.md&lt;/read_first&gt;

Occurrences: `.planning/phases/06-form-button-leaf/06-09-PLAN.md:82`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>06-08-SUMMARY.md</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-09-PLAN.md:82` — 5/test_doc_links.py; docs/migrating-1.0.md Form buttons; 06-07-SUMMARY.md; 06-08-SUMMARY.md; 06-VALIDATION.md&lt;/read_first&gt;

Occurrences: `.planning/phases/06-form-button-leaf/06-09-PLAN.md:82`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>06-JS-RUNTIME.json</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:69` — NEW validation artifacts: 06-js-verify.sh and 06-JS-RUNTIME.json at the full phase-local paths in files_modified;

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:69`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:102`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:65`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>06-RESEARCH.md</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-07-PLAN.md:71` — ; tests/js/helpers/setup.js; src/crud_views/static/crud_views/js/modal.js; 06-RESEARCH.md Package Legitimacy Audit&lt;/read_first&gt;

Occurrences: `.planning/phases/06-form-button-leaf/06-07-PLAN.md:71`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:113`.

Supplemental exact path/declaration candidates: `.planning/phases/06-form-button-leaf/06-RESEARCH.md:1`.

</details>

<details>
<summary><code>06-SPEC.md</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:66` — NEW files: 06-SPEC.md at the full path in files_modified; tests/test1/test_form_buttons_golden.py; the five

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:66`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:72`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:95`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:73`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:100`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:82`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:67`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>06-VALIDATION.md</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-09-PLAN.md:61` — NEW file: .planning/phases/06-form-button-leaf/06-ACCEPTANCE.md. Existing 06-VALIDATION.md receives measured results. No new product/test symbols.

Occurrences: `.planning/phases/06-form-button-leaf/06-09-PLAN.md:61`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:67`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:82`.

Supplemental exact path/declaration candidates: `.planning/phases/06-form-button-leaf/06-VALIDATION.md:1`.

</details>

<details>
<summary><code>06-js-verify.sh</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:69` — NEW validation artifacts: 06-js-verify.sh and 06-JS-RUNTIME.json at the full phase-local paths in files_modified;

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:69`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:103`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:65`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>BOOTSTRAP_ICONS</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-04-PLAN.md:83` — Add save, cancel and filter-reset to DEFAULT_ICONS and BOOTSTRAP_ICONS with matching semantic meanings. Ensure the leaf reads mode classes through cv_button_class and the existing form utility keys through dedicated look

Occurrences: `.planning/phases/06-form-button-leaf/06-04-PLAN.md:83`.

Supplemental exact path/declaration candidates: `src/crud_views/lib/icons.py:51`.

</details>

<details>
<summary><code>BaseInput</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-02-PLAN.md:112` — &lt;read_first&gt;The spec literal/attribute rules; crispy BaseInput and TemplateNameMixin in the declared-floor environment; tests/test1/test_button_leaves.py&lt;/read_first&gt;

Occurrences: `.planning/phases/06-form-button-leaf/06-02-PLAN.md:112`.

Supplemental exact path/declaration candidates: `.venv/lib/python3.12/site-packages/crispy_forms/layout.py:199`.

</details>

<details>
<summary><code>BaseInput.render</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-02-PLAN.md:99` — Implement adapter render without calling BaseInput.render: retain raw value and kwargs, normalize per spec, render the selected leaf through a scoped context copy. Strip inherited input aliases from the temp

Occurrences: `.planning/phases/06-form-button-leaf/06-02-PLAN.md:99`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:178`.

Supplemental exact path/declaration candidates: `.venv/lib/python3.12/site-packages/crispy_forms/layout.py:250`.

</details>

<details>
<summary><code>BasicNode.get_render</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-03-PLAN.md:95` — &lt;read_first&gt;06-SPEC.md ownership contract; installed crispy BasicNode.get_render/get_response_dict, FormActions.render and FormHelper.get_attributes; src/crud_views/templates/crud_views/formsets/formset.html; tests/test1/test_cris

Occurrences: `.planning/phases/06-form-button-leaf/06-03-PLAN.md:95`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:73`.

Supplemental exact path/declaration candidates: `.venv/lib/python3.12/site-packages/crispy_forms/templatetags/crispy_forms_tags.py:70`.

</details>

<details>
<summary><code>BasicNode.get_response_dict</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-03-PLAN.md:143` — NCE | Rejected as a missing-API claim, not as a test obligation: installed BasicNode.get_response_dict supplies inputs/is_formset/template_pack metadata; no named provenance field is required. Task 2 and the pre-implementation spec retain the current-i

Occurrences: `.planning/phases/06-form-button-leaf/06-03-PLAN.md:143`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:83`.

Supplemental exact path/declaration candidates: `.venv/lib/python3.12/site-packages/crispy_forms/templatetags/crispy_forms_tags.py:137`.

</details>

<details>
<summary><code>CHANGELOG.md</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-08-PLAN.md:17` — - CHANGELOG.md

Occurrences: `.planning/phases/06-form-button-leaf/06-08-PLAN.md:17`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:114`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:115`.

Supplemental exact path/declaration candidates: `CHANGELOG.md:1`.

</details>

<details>
<summary><code>CLAUDE.md</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:53` — @CLAUDE.md

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:53`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:66`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:53`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:55`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:54`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:56`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:52`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:63`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:48`.

Supplemental exact path/declaration candidates: `CLAUDE.md:1`.

</details>

<details>
<summary><code>CONTEXT.md</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:260` — g branch, recording HEAD and test evidence before the spec. ROADMAP.md and CONTEXT.md now carry this requirement. No claim that main changed; no merge or branch switch. Dependency verification, spec-first and baseline-first gates remai

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:260`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-03-PLAN.md:66` — NEW fields: CrudViewsSettings.form_actions_label_mode (CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE), ViewSet.form_actions_label_mode, CrudView.cv_form_actions_label_mode. NEW public resolver: CrudView.cv_get_form_actions_label_mode(). Existing cv_g

Occurrences: `.planning/phases/06-form-button-leaf/06-03-PLAN.md:66`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:81`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:82`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:85`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>CRUD_VIEWS_ICONS</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-06-PLAN.md:115` — antic mapping, including explicit None/empty and a semantic name mapped by CRUD_VIEWS_ICONS to None/empty. Test each with known default submit/delete/filter controls. Named-but-unregistered icons retain separate registry diagnostics; this is

Occurrences: `.planning/phases/06-form-button-leaf/06-06-PLAN.md:115`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>CRUD_VIEWS_LABEL_MODE_DEFAULTS</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-03-PLAN.md:82` — S_LABEL_MODE={&#x27;submit&#x27;: &#x27;icon&#x27;}) alone leaves submit in both, while nested CRUD_VIEWS_LABEL_MODE_DEFAULTS={&#x27;form&#x27;: &#x27;icon&#x27;} changes only the unmapped cancel and exiting restores its label floor. Keep this distinction explicit in the spec and documentation 

Occurrences: `.planning/phases/06-form-button-leaf/06-03-PLAN.md:82`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:85`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:119`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>CRUD_VIEWS_STRICT</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-06-PLAN.md:116` — hes to label and drops generated icon-only title/tooltip/host classes. Set CRUD_VIEWS_STRICT explicitly in both test branches. With empty label as well, retain the empty literal payload and log the both-missing diagnostic; do not invent text.

Occurrences: `.planning/phases/06-form-button-leaf/06-06-PLAN.md:116`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>Context.dicts</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:133` — Define owner recovery from Django Context.dicts before flattening: the actual adapter render(form, context)

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:133`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:105`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>CrispyDeleteForm</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-06-PLAN.md:113` — lementations. Select the provider before controls (H-DELETE-STATIC): check CrispyDeleteForm first, whose helper renders delete via delete_icon plus cancel, never its inherited submit_icon. Otherwise default CrispyFormMixin/workflow helpers r

Occurrences: `.planning/phases/06-form-button-leaf/06-06-PLAN.md:113`.

Supplemental exact path/declaration candidates: `src/crud_views/lib/crispy/form.py:116`.

</details>

<details>
<summary><code>CrispyDeleteForm.delete_icon</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-04-PLAN.md:68` — el, filter-reset. NEW form attributes: CrispyFormMixin.submit_icon=&#x27;save&#x27;, CrispyDeleteForm.delete_icon=&#x27;delete&#x27;, WorkflowForm.submit_icon=&#x27;workflow&#x27;. NEW adapter icon= keyword is consumed as rendering configuration, never serialized as an HTML attribut

Occurrences: `.planning/phases/06-form-button-leaf/06-04-PLAN.md:68`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>CrispyFormMixin</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-04-PLAN.md:104` — s an intentional missing icon. Keep legacy helper.input attributes usable. CrispyFormMixin and delete hooks pass submit_icon/delete_icon; workflow supplies its class default. Preserve kwargs override ordering so a custom hook icon or slot w

Occurrences: `.planning/phases/06-form-button-leaf/06-04-PLAN.md:104`.

Supplemental exact path/declaration candidates: `src/crud_views/lib/crispy/form.py:11`.

</details>

<details>
<summary><code>CrispyFormMixin.submit_icon</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-04-PLAN.md:68` — ount. NEW registry names: save, cancel, filter-reset. NEW form attributes: CrispyFormMixin.submit_icon=&#x27;save&#x27;, CrispyDeleteForm.delete_icon=&#x27;delete&#x27;, WorkflowForm.submit_icon=&#x27;workflow&#x27;. NEW adapter icon= keyword is consumed as rendering configuration,

Occurrences: `.planning/phases/06-form-button-leaf/06-04-PLAN.md:68`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>CrudView</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-03-PLAN.md:105` — n if it lacks crud configuration; never search for a more convenient lower CrudView. Use scoped copies/pushes and restore all context state.

Occurrences: `.planning/phases/06-form-button-leaf/06-03-PLAN.md:105`.

Supplemental exact path/declaration candidates: `src/crud_views/lib/view/base.py:61`.

</details>

<details>
<summary><code>CrudView.checks</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-06-PLAN.md:113` — Introduce a static form checker wired from CrudView.checks. Inspect concrete statically selected form classes only while the helper property, action provider and relevant button/kwargs hooks retain known pack

Occurrences: `.planning/phases/06-form-button-leaf/06-06-PLAN.md:113`.

Supplemental exact path/declaration candidates: `src/crud_views/lib/view/base.py:135`.

</details>

<details>
<summary><code>CrudView.cv_form_actions_label_mode</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-03-PLAN.md:66` — ode (CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE), ViewSet.form_actions_label_mode, CrudView.cv_form_actions_label_mode. NEW public resolver: CrudView.cv_get_form_actions_label_mode(). Existing cv_get_action_label_mode gains location=&#x27;form&#x27;. Private owner-recovery help

Occurrences: `.planning/phases/06-form-button-leaf/06-03-PLAN.md:66`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>CrudView.cv_get_form_actions_label_mode</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-03-PLAN.md:66` — ions_label_mode, CrudView.cv_form_actions_label_mode. NEW public resolver: CrudView.cv_get_form_actions_label_mode(). Existing cv_get_action_label_mode gains location=&#x27;form&#x27;. Private owner-recovery helpers are internal, not promised public names.

Occurrences: `.planning/phases/06-form-button-leaf/06-03-PLAN.md:66`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>CrudViewsSettings</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:147` — or explicit CrudViewsSettings arguments, not an invented setting_changed refresh; 06-03 proves the distinction.

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:147`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:24`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:82`.

Supplemental exact path/declaration candidates: `src/crud_views/lib/settings.py:17`.

</details>

<details>
<summary><code>CrudViewsSettings.form_actions_label_mode</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-03-PLAN.md:66` — NEW fields: CrudViewsSettings.form_actions_label_mode (CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE), ViewSet.form_actions_label_mode, CrudView.cv_form_actions_label_mode. NEW public resolver: CrudView.cv_get_form

Occurrences: `.planning/phases/06-form-button-leaf/06-03-PLAN.md:66`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:81`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>DEFAULT_ICONS</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-04-PLAN.md:83` — Add save, cancel and filter-reset to DEFAULT_ICONS and BOOTSTRAP_ICONS with matching semantic meanings. Ensure the leaf reads mode classes through cv_button_class and the existing form utility keys th

Occurrences: `.planning/phases/06-form-button-leaf/06-04-PLAN.md:83`.

Supplemental exact path/declaration candidates: `src/crud_views/lib/icons.py:14`.

</details>

<details>
<summary><code>E108_LOCATIONS</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-02-PLAN.md:96` — IONS and label to LABEL_MODE_DEFAULTS together. In this same change update E108_LOCATIONS in test_action_label_mode_config.py to include form, move the old form-invalid case to the valid defaults parametrization, and retain unknown-locatio

Occurrences: `.planning/phases/06-form-button-leaf/06-02-PLAN.md:96`.

Supplemental exact path/declaration candidates: `tests/test1/test_action_label_mode_config.py:278`.

</details>

<details>
<summary><code>EXPECTED_KEYS</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-02-PLAN.md:97` — ring (H-EARLY-UTILITIES, D-14). Update test_button_classes.py&#x27;s exhaustive EXPECTED_KEYS, the measured count (71 to 73 on the reviewed tree), and utility-slot parametrization in this same producing task (H-KEYSET). Update buttons.md&#x27;s mea

Occurrences: `.planning/phases/06-form-button-leaf/06-02-PLAN.md:97`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:158`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:82`.

Supplemental exact path/declaration candidates: `tests/test1/test_button_classes.py:21`.

</details>

<details>
<summary><code>FORM_KINDS</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:89` — at that HEAD: default_label_mode with shared lazy defaults and independent FORM_KINDS /

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:89`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:96`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:97`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:98`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:25`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:40`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:85`.

Supplemental exact path/declaration candidates: `src/crud_views/lib/button_classes.py:210`, `tests/test1/test_button_classes_checks.py:111`.

</details>

<details>
<summary><code>FORM_LEAF_KEYS</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:116` — 06-02 through 06-06. Set separate FORM_LEAF_KEYS, preserving LEAF_KEYS; define type/name/value/id/key,

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:116`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:79`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:98`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:116`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:84`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:157`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>FormActions</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:140` — r overlay by its provenance/response metadata, never a fixed stack offset: FormActions leaves extra

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:140`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:141`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:149`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:149`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:157`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:253`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:28`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:101`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:106`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:110`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:125`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:24`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:24`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:41`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:67`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:71`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:77`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:100`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:107`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:108`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:31`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:101`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:196`.

Supplemental exact path/declaration candidates: `.venv/lib/python3.12/site-packages/crispy_forms/bootstrap.py:259`.

</details>

<details>
<summary><code>FormActions.render</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-03-PLAN.md:95` — nership contract; installed crispy BasicNode.get_render/get_response_dict, FormActions.render and FormHelper.get_attributes; src/crud_views/templates/crud_views/formsets/formset.html; tests/test1/test_crispy_buttons.py&lt;/read_first&gt;

Occurrences: `.planning/phases/06-form-button-leaf/06-03-PLAN.md:95`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:105`.

Supplemental exact path/declaration candidates: `.venv/lib/python3.12/site-packages/crispy_forms/bootstrap.py:306`.

</details>

<details>
<summary><code>FormData</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-07-PLAN.md:27` — - &quot;The native SubmitEvent.submitter and FormData contract is tested on exact locked JS packages under a compatible isolated runtime, without hiding failure through mocks/polyfills.&quot;

Occurrences: `.planning/phases/06-form-button-leaf/06-07-PLAN.md:27`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:36`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:74`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:80`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:80`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:80`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:135`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:152`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:192`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>FormHelper</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-05-PLAN.md:82` — Add get_form_actions following the spec. Initialize FormHelper without passing form when preserving declared layout; deep-copy declared layout per instance, and retain helper.form as the identical explicit form a

Occurrences: `.planning/phases/06-form-button-leaf/06-05-PLAN.md:82`.

Supplemental exact path/declaration candidates: `.venv/lib/python3.12/site-packages/crispy_forms/helper.py:106`.

</details>

<details>
<summary><code>FormHelper.get_attributes</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-03-PLAN.md:95` — lled crispy BasicNode.get_render/get_response_dict, FormActions.render and FormHelper.get_attributes; src/crud_views/templates/crud_views/formsets/formset.html; tests/test1/test_crispy_buttons.py&lt;/read_first&gt;

Occurrences: `.planning/phases/06-form-button-leaf/06-03-PLAN.md:95`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:73`.

Supplemental exact path/declaration candidates: `.venv/lib/python3.12/site-packages/crispy_forms/helper.py:290`.

</details>

<details>
<summary><code>HomePageTest</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-09-PLAN.md:82` — i; examples/bootstrap5/test_i18n.py; examples/bootstrap5/project/tests.py (HomePageTest and SystemChecksTest); examples/bootstrap5/test_doc_links.py; docs/migrating-1.0.md Form buttons; 06-07-SUMMARY.md; 06-08-SUMMARY.md; 06-VALIDATION.m

Occurrences: `.planning/phases/06-form-button-leaf/06-09-PLAN.md:82`.

Supplemental exact path/declaration candidates: `examples/bootstrap5/project/tests.py:34`.

</details>

<details>
<summary><code>HomePageTest.test_every_feature_landing_page_renders</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-09-PLAN.md:85` — ing test_demo_pages_render_german and its translated create-submit value), HomePageTest.test_every_feature_landing_page_renders, and all test_doc_links.py reference/backlink cases. Record their collected counts and results after 06-08 enables form=both. Root pytest tests does 

Occurrences: `.planning/phases/06-form-button-leaf/06-09-PLAN.md:85`.

Supplemental exact path/declaration candidates: `examples/bootstrap5/project/tests.py:45`.

</details>

<details>
<summary><code>LABEL_MODE_DEFAULTS</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-02-PLAN.md:95` — data.py location/default assertions in this producing task, preserving set(LABEL_MODE_DEFAULTS) == LOCATIONS, before running the tracer shard.

Occurrences: `.planning/phases/06-form-button-leaf/06-02-PLAN.md:95`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:96`.

Supplemental exact path/declaration candidates: `src/crud_views/lib/view/label_mode.py:23`.

</details>

<details>
<summary><code>LEAF_KEYS</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:116` — 06-02 through 06-06. Set separate FORM_LEAF_KEYS, preserving LEAF_KEYS; define type/name/value/id/key,

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:116`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:98`.

Supplemental exact path/declaration candidates: `src/crud_views/lib/view/button_data.py:16`.

</details>

<details>
<summary><code>Layout</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:155` — replacements there, including Layout() before/between renders; keep explicit empty field selection distinct

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:155`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:83`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:103`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:108`.

Supplemental exact path/declaration candidates: `.venv/lib/python3.12/site-packages/crispy_forms/layout.py:108`.

</details>

<details>
<summary><code>ListViewFilterFormHelper</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-08-PLAN.md:101` — attributes instead of the old input object. Keep the documented field-only ListViewFilterFormHelper subclass unchanged and explain base-added actions, instance isolation and get_form_actions None omission. Provide opt-in migration from legacy add_in

Occurrences: `.planning/phases/06-form-button-leaf/06-08-PLAN.md:101`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:102`.

Supplemental exact path/declaration candidates: `src/crud_views/lib/views/list.py:57`.

</details>

<details>
<summary><code>ListViewFilterFormHelper.get_attributes</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-05-PLAN.md:83` — For M-EMPTY-REPLACEMENT, prepare the current layout in a ListViewFilterFormHelper.get_attributes override before delegating to super: BasicNode.get_response_dict calls this method before get_render evaluates helper.layout truthiness. Detect a cal

Occurrences: `.planning/phases/06-form-button-leaf/06-05-PLAN.md:83`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>ListViewFilterFormHelper.get_form_actions</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-05-PLAN.md:67` — NEW public method: ListViewFilterFormHelper.get_form_actions() -&gt; FormActions | None. NEW get_attributes and render_layout overrides with private instance layout/action initialization state. No new test files; 

Occurrences: `.planning/phases/06-form-button-leaf/06-05-PLAN.md:67`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>ListViewTableFilterMixin</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-05-PLAN.md:82` —  not inspect a fresh form.helper property; restore context afterward. Keep ListViewTableFilterMixin construction unchanged.

Occurrences: `.planning/phases/06-form-button-leaf/06-05-PLAN.md:82`.

Supplemental exact path/declaration candidates: `src/crud_views/lib/views/mixins.py:299`.

</details>

<details>
<summary><code>ROADMAP.md</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:260` — xecuting working branch, recording HEAD and test evidence before the spec. ROADMAP.md and CONTEXT.md now carry this requirement. No claim that main changed; no merge or branch switch. Dependency verification, spec-first and baseline-fi

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:260`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>SafeData</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:118` — Normalize text to a plain str that has no SafeData trust marker before exactly one Django escaping boundary;

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:118`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:99`.

Supplemental exact path/declaration candidates: `.venv/lib/python3.12/site-packages/django/utils/safestring.py:13`.

</details>

<details>
<summary><code>SafeString</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-02-PLAN.md:37` — - &quot;D-15: Empty, Unicode, lazy, SafeString and template-looking values remain exact literal DOM text and values; none evaluates template syntax or creates injected nodes/attributes.&quot;

Occurrences: `.planning/phases/06-form-button-leaf/06-02-PLAN.md:37`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:116`.

Supplemental exact path/declaration candidates: `.venv/lib/python3.12/site-packages/django/utils/safestring.py:25`.

</details>

<details>
<summary><code>SubmitEvent</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-07-PLAN.md:36` — via: Native SubmitEvent and FormData payload

Occurrences: `.planning/phases/06-form-button-leaf/06-07-PLAN.md:36`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:80`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>SubmitEvent.submitter</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-07-PLAN.md:27` — - &quot;The native SubmitEvent.submitter and FormData contract is tested on exact locked JS packages under a compatible isolated runtime, without hiding failure through mocks/polyfills.&quot;

Occurrences: `.planning/phases/06-form-button-leaf/06-07-PLAN.md:27`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:73`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>SystemChecksTest</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-09-PLAN.md:82` — trap5/test_i18n.py; examples/bootstrap5/project/tests.py (HomePageTest and SystemChecksTest); examples/bootstrap5/test_doc_links.py; docs/migrating-1.0.md Form buttons; 06-07-SUMMARY.md; 06-08-SUMMARY.md; 06-VALIDATION.md&lt;/read_first&gt;

Occurrences: `.planning/phases/06-form-button-leaf/06-09-PLAN.md:82`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:85`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:256`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:271`.

Supplemental exact path/declaration candidates: `examples/bootstrap5/project/tests.py:97`.

</details>

<details>
<summary><code>TemplateNameMixin</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-02-PLAN.md:112` — &lt;read_first&gt;The spec literal/attribute rules; crispy BaseInput and TemplateNameMixin in the declared-floor environment; tests/test1/test_button_leaves.py&lt;/read_first&gt;

Occurrences: `.planning/phases/06-form-button-leaf/06-02-PLAN.md:112`.

Supplemental exact path/declaration candidates: `.venv/lib/python3.12/site-packages/crispy_forms/layout.py:18`.

</details>

<details>
<summary><code>VARIANT_LOCATIONS</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:90` — VARIANT_LOCATIONS. Before authoring the spec, run .venv/bin/pytest tests/test1/test_label_mode.py

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:90`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:96`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:97`.

Supplemental exact path/declaration candidates: `src/crud_views/lib/button_classes.py:209`.

</details>

<details>
<summary><code>ValueError</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-02-PLAN.md:98` — S and cv_type against submit/button/reset; invalid caller kind/type raises ValueError. Explicitly reject non-form and unknown slot kinds when rendering through the new layout leaf; preserve arbitrary slot handling on legacy helper.inpu

Occurrences: `.planning/phases/06-form-button-leaf/06-02-PLAN.md:98`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:26`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:115`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:116`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:117`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>ViewSet</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-03-PLAN.md:23` — - &quot;D-13: Form mode maps select view, else ViewSet, else setting as whole maps; an empty selected map and missing kind fall directly to the live form floor.&quot;

Occurrences: `.planning/phases/06-form-button-leaf/06-03-PLAN.md:23`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:88`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:79`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:86`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:93`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:86`.

Supplemental exact path/declaration candidates: `src/crud_views/lib/viewset/__init__.py:45`.

</details>

<details>
<summary><code>ViewSet.form_actions_label_mode</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-03-PLAN.md:66` — iewsSettings.form_actions_label_mode (CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE), ViewSet.form_actions_label_mode, CrudView.cv_form_actions_label_mode. NEW public resolver: CrudView.cv_get_form_actions_label_mode(). Existing cv_get_action_label_mode gains locatio

Occurrences: `.planning/phases/06-form-button-leaf/06-03-PLAN.md:66`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>ViewSets</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-09-PLAN.md:238` — &lt;fails_when&gt;The URLconf does not register feature ViewSets, the registered example reports system-check errors, or the test fails to start; bare manage.py check alone is insufficient.&lt;/fails_when&gt;

Occurrences: `.planning/phases/06-form-button-leaf/06-09-PLAN.md:238`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:256`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>WorkflowForm.submit_icon</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-04-PLAN.md:68` — CrispyFormMixin.submit_icon=&#x27;save&#x27;, CrispyDeleteForm.delete_icon=&#x27;delete&#x27;, WorkflowForm.submit_icon=&#x27;workflow&#x27;. NEW adapter icon= keyword is consumed as rendering configuration, never serialized as an HTML attribute; omission selects kind default wh

Occurrences: `.planning/phases/06-form-button-leaf/06-04-PLAN.md:68`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>action_menus</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-08-PLAN.md:86` — Extend the existing docs tests&#x27; setting-row/merge-table assertions and the action_menus form resolution section, and render a documented form configuration proving both/icon output. Preserve synced example fences and the unique existing 

Occurrences: `.planning/phases/06-form-button-leaf/06-08-PLAN.md:86`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>action_menus.md</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-08-PLAN.md:84` —  lookup and form utility keys. Keep the canonical form resolution order in action_menus.md: first select owner (D-09–D-12), then whole view/ViewSet/settings map, then lazy floor for a missing key. Add the Form column and getter, and extend 

Occurrences: `.planning/phases/06-form-button-leaf/06-08-PLAN.md:84`.

Supplemental exact path/declaration candidates: `docs/reference/action_menus.md:1`.

</details>

<details>
<summary><code>add_input</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-05-PLAN.md:22` — - &quot;D-01, D-02: Custom add_input controls remain legacy inputs quietly; hidden sort/order/direction inputs keep their current path and values.&quot;

Occurrences: `.planning/phases/06-form-button-leaf/06-05-PLAN.md:22`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:104`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:107`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:101`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:117`.

Supplemental exact path/declaration candidates: `.venv/lib/python3.12/site-packages/crispy_forms/helper.py:260`.

</details>

<details>
<summary><code>assumption_delta_decision</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:230` — &lt;assumption_delta_decision&gt;

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:230`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:235`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>button.name</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-07-PLAN.md:80` — literal malicious/Unicode values. Assert actual FormData(form, button).get(button.name) and preserved hidden confirmation/CSRF values; sibling submitter fields must be absent. Fetch may be spied to inspect its FormData, but do not repla

Occurrences: `.planning/phases/06-form-button-leaf/06-07-PLAN.md:80`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>button_data.py</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-02-PLAN.md:79` — /templates/crud_views/tags/button/form.html. NEW symbol: FORM_LEAF_KEYS in button_data.py. NEW normalized fields: cv_type, cv_name, cv_value, cv_id, cancel-only cv_cancel_url, cv_css_class, cv_flat_attrs; existing label/icon fields are reu

Occurrences: `.planning/phases/06-form-button-leaf/06-02-PLAN.md:79`.

Supplemental exact path/declaration candidates: `src/crud_views/lib/view/button_data.py:1`.

</details>

<details>
<summary><code>buttons.md</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-02-PLAN.md:97` — tility-slot parametrization in this same producing task (H-KEYSET). Update buttons.md&#x27;s measured count and complete utility rows/arithmetic, including five icon-host keys. Preserve finite FORM_KINDS/VARIANT_LOCATIONS; a utility key nev

Occurrences: `.planning/phases/06-form-button-leaf/06-02-PLAN.md:97`.

Supplemental exact path/declaration candidates: `docs/reference/buttons.md:1`.

</details>

<details>
<summary><code>check_viewsets</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-06-PLAN.md:28` — values yield deterministic diagnostics; malformed floor/map errors survive check_viewsets and are never hidden by W292.&quot;

Occurrences: `.planning/phases/06-form-button-leaf/06-06-PLAN.md:28`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:77`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:87`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:87`.

Supplemental exact path/declaration candidates: `src/crud_views/checks.py:20`.

</details>

<details>
<summary><code>context.push</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:137` — r helper render_layout supplies a private helper-owner context entry using context.push

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:137`.

Supplemental exact path/declaration candidates: `.venv/lib/python3.12/site-packages/django/template/context.py:53`.

</details>

<details>
<summary><code>crispy_floor</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-07-PLAN.md:65` — NEW nox session: crispy_floor, Python 3.12 with Django 4.2 and 6.0 variants and exact crispy 2.0/bootstrap5 2023.10 pins. Existing JS source files are conditional bug-fix ownershi

Occurrences: `.planning/phases/06-form-button-leaf/06-07-PLAN.md:65`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:115`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:118`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:157`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>crud_views_settings</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:145` — settings.py is initialized and the existing crud_views_settings singleton serves map reads, like context/list.

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:145`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:77`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:81`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:82`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:85`.

Supplemental exact path/declaration candidates: `src/crud_views/lib/settings.py:320`.

</details>

<details>
<summary><code>css_class</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:126` — otherwise extra id wins over generated id; class-table classes then css_class then extra class are appended

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:126`.

Supplemental exact path/declaration candidates: `src/crud_views/lib/crispy/table.py:5`, `src/crud_views/lib/crispy/table.py:9`, `src/crud_views/lib/crispy/table.py:13`, `src/crud_views/lib/crispy/table.py:17`, `src/crud_views/lib/crispy/table.py:21`, `src/crud_views/lib/crispy/table.py:25`, `src/crud_views/lib/crispy/table.py:29`, `src/crud_views/lib/crispy/table.py:33`, `src/crud_views/lib/crispy/table.py:37`, `src/crud_views/lib/crispy/table.py:41`, `src/crud_views/lib/crispy/table.py:45`, `src/crud_views/lib/crispy/table.py:49`, `.venv/lib/python3.12/site-packages/crispy_forms/bootstrap.py:599`, `.venv/lib/python3.12/site-packages/crispy_forms/bootstrap.py:714`, `.venv/lib/python3.12/site-packages/crispy_forms/bootstrap.py:949`, `.venv/lib/python3.12/site-packages/crispy_forms/layout.py:732`, `.venv/lib/python3.12/site-packages/crispy_forms/templatetags/crispy_forms_field.py:61`, `.venv/lib/python3.12/site-packages/crispy_forms/templatetags/crispy_forms_field.py:103`, `.venv/lib/python3.12/site-packages/crispy_forms/templatetags/crispy_forms_field.py:108`.

</details>

<details>
<summary><code>css_id</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:125` — css_id wins over extra id,

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:125`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>cv_button_class</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-02-PLAN.md:99` — or helper.inputs. Do not infer kind from the submitted name. The leaf uses cv_button_class form/cv_key/cv_label_mode, appends cv_css_class and host classes, and renders the three bodies with cancel URL only for cancel. Keep normalizer/icon 

Occurrences: `.planning/phases/06-form-button-leaf/06-02-PLAN.md:99`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:83`.

Supplemental exact path/declaration candidates: `src/crud_views_object_detail/templatetags/crud_views_object_detail.py:108`, `src/crud_views/templatetags/crud_views.py:525`.

</details>

<details>
<summary><code>cv_button_data</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-02-PLAN.md:36` — - &quot;D-13, D-14: A standalone package Submit renders a real button through cv_button_data(ctx, &#x27;form&#x27;), with label as the lazy form floor and finite kind semantics.&quot;

Occurrences: `.planning/phases/06-form-button-leaf/06-02-PLAN.md:36`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:98`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:116`.

Supplemental exact path/declaration candidates: `src/crud_views/lib/view/button_data.py:52`.

</details>

<details>
<summary><code>cv_cancel_url</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-02-PLAN.md:79` — .py. NEW normalized fields: cv_type, cv_name, cv_value, cv_id, cancel-only cv_cancel_url, cv_css_class, cv_flat_attrs; existing label/icon fields are reused. NEW class utility defaults: form:hidden-label and form:icon-host, with exhaustiv

Occurrences: `.planning/phases/06-form-button-leaf/06-02-PLAN.md:79`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>cv_css_class</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:117` — literal strings, cancel-only URL, mode/icon fields, cv_css_class suffix and cv_flat_attrs serialization.

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:117`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:79`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:99`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:84`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>cv_first_inline_keys</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-03-PLAN.md:40` — via: cv_first_inline_keys selects one map

Occurrences: `.planning/phases/06-form-button-leaf/06-03-PLAN.md:40`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:72`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:81`.

Supplemental exact path/declaration candidates: `src/crud_views/lib/view/base.py:263`.

</details>

<details>
<summary><code>cv_flat_attrs</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:117` — iteral strings, cancel-only URL, mode/icon fields, cv_css_class suffix and cv_flat_attrs serialization.

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:117`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:79`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:84`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:101`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>cv_form_actions_label_mode</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-06-PLAN.md:82` — - Form-specific messages name cv_form_actions_label_mode, finite form kinds and the form floor; existing context/list message text remains unchanged.

Occurrences: `.planning/phases/06-form-button-leaf/06-06-PLAN.md:82`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:85`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:86`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>cv_form_icon_mode_checks</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-06-PLAN.md:69` — cks.py. NEW private/static form icon checker in view/buttons.py (suggested cv_form_icon_mode_checks). No new check IDs. Finite form contract tests live in this file or existing test_button_data.py read-only coverage; no new generic diagnostic framew

Occurrences: `.planning/phases/06-form-button-leaf/06-06-PLAN.md:69`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>cv_get_action_label_mode</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-03-PLAN.md:66` — . NEW public resolver: CrudView.cv_get_form_actions_label_mode(). Existing cv_get_action_label_mode gains location=&#x27;form&#x27;. Private owner-recovery helpers are internal, not promised public names.

Occurrences: `.planning/phases/06-form-button-leaf/06-03-PLAN.md:66`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:72`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:81`.

Supplemental exact path/declaration candidates: `src/crud_views/lib/view/base.py:299`.

</details>

<details>
<summary><code>cv_get_form_actions_label_mode</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-03-PLAN.md:81` — ettings or maps to lazy access or reload the settings module in tests. Add cv_get_form_actions_label_mode via cv_first_inline_keys and form support to cv_get_action_label_mode using key membership followed by default_label_mode(&#x27;form&#x27;). No target-view sca

Occurrences: `.planning/phases/06-form-button-leaf/06-03-PLAN.md:81`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>cv_icon</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-06-PLAN.md:115` — rer to probe availability. Leave actual inline rendering to the leaf&#x27;s one cv_icon call; no rendered-markup cache or extra public leaf key is needed. A custom renderer&#x27;s returned markup remains its existing renderer contract, not a 

Occurrences: `.planning/phases/06-form-button-leaf/06-06-PLAN.md:115`.

Supplemental exact path/declaration candidates: `src/crud_views_object_detail/templatetags/crud_views_object_detail.py:102`, `src/crud_views/templatetags/crud_views.py:513`.

</details>

<details>
<summary><code>cv_icon_inline</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-06-PLAN.md:117` — host overrides: assert expected host classes or their intentional absence, cv_icon_inline=False, no inline element/render invocation and no false W292/log/exception. Separately disable the host&#x27;s semantic mapping and require the same stric

Occurrences: `.planning/phases/06-form-button-leaf/06-06-PLAN.md:117`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>cv_icon_mode_checks</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-06-PLAN.md:100` — &lt;read_first&gt;src/crud_views/lib/view/buttons.py (cv_icon_mode_checks); src/crud_views/lib/crispy/form.py; src/crud_views/lib/views/list.py; src/crud_views/lib/view/button_data.py; src/crud_views/lib/icons.py (resolve_i

Occurrences: `.planning/phases/06-form-button-leaf/06-06-PLAN.md:100`.

Supplemental exact path/declaration candidates: `src/crud_views/lib/view/buttons.py:387`.

</details>

<details>
<summary><code>cv_id</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-02-PLAN.md:79` — KEYS in button_data.py. NEW normalized fields: cv_type, cv_name, cv_value, cv_id, cancel-only cv_cancel_url, cv_css_class, cv_flat_attrs; existing label/icon fields are reused. NEW class utility defaults: form:hidden-label and for

Occurrences: `.planning/phases/06-form-button-leaf/06-02-PLAN.md:79`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>cv_key</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-02-PLAN.md:98` —  LEAF_KEYS. Introduce FORM_LEAF_KEYS for the exact spec contract. Validate cv_key against FORM_KINDS and cv_type against submit/button/reset; invalid caller kind/type raises ValueError. Explicitly reject non-form and unknown slot k

Occurrences: `.planning/phases/06-form-button-leaf/06-02-PLAN.md:98`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:99`.

Supplemental exact path/declaration candidates: `src/crud_views_workflow/lib/views.py:24`, `src/crud_views/lib/views/update.py:13`, `src/crud_views/lib/views/card.py:22`, `src/crud_views/lib/views/manage.py:14`, `src/crud_views/lib/views/child.py:13`, `src/crud_views/lib/views/list.py:19`, `src/crud_views/lib/views/detail.py:10`, `src/crud_views/lib/views/create.py:13`, `src/crud_views/lib/views/action_ordered.py:19`, `src/crud_views/lib/views/action_ordered.py:47`, `src/crud_views/lib/views/delete.py:32`, `src/crud_views/lib/view/base.py:67`, `src/crud_views_polymorphic/lib/create_select.py:29`, `tests/test1/test_backend_only_labels.py:22`, `tests/test1/test_backend_only_labels.py:41`, `tests/test1/test_success_origin.py:206`, `tests/test1/test_post_object_resolution.py:65`, `tests/test1/test_icons_checks.py:97`, `tests/test1/test_icons_checks.py:135`, `tests/test1/test_workflow.py:541`, `tests/test1/test_workflow.py:554`, `tests/test1/test_workflow.py:568`, `tests/test1/test_workflow.py:587`, `tests/test1/test_workflow.py:611`, `tests/test1/test_workflow.py:635`, `tests/test1/test_cancel_origin.py:204`, `tests/test1/test_context_actions_isolation.py:47`, `tests/test1/test_context_actions_isolation.py:68`, `tests/test1/test_detail_view.py:26`, `tests/test1/test_detail_view.py:38`, `tests/test1/test_detail_view.py:73`, `tests/test1/test_detail_view.py:90`, `tests/test1/test_detail_view.py:107`, `tests/test1/test_detail_view.py:124`, `tests/test1/test_detail_view.py:141`, `tests/test1/test_detail_view.py:158`, `tests/test1/test_detail_view.py:175`, `tests/test1/test_detail_view.py:187`, `tests/test1/test_detail_view.py:199`, `tests/test1/od/test_object_detail_view.py:17`, `tests/test1/od/test_object_detail_view.py:27`, `tests/test1/od/test_object_detail_view.py:37`, `tests/test1/od/test_object_detail_view.py:54`, `tests/test1/od/test_object_detail_view.py:134`, `tests/test1/od/test_object_detail_view.py:168`, `tests/test1/od/test_object_detail_view.py:180`, `tests/test1/app/resources.py:95`, `tests/test1/app/resources.py:119`, `tests/test1/app/views.py:135`, `tests/test1/app/views.py:151`, `tests/test1/app/views.py:163`, `tests/test1/app/views.py:177`, `tests/test1/app/views.py:209`, `tests/test1/app/views.py:918`, `tests/test1/app/views.py:1099`, `tests/test1/app/views.py:1121`, `examples/bootstrap5/action_menus/views.py:114`, `examples/bootstrap5/action_menus/views.py:132`, `examples/bootstrap5/resources/views.py:94`, `examples/bootstrap5/resources/views.py:112`, `examples/bootstrap5/showcase/views.py:122`.

</details>

<details>
<summary><code>cv_label_mode</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-02-PLAN.md:99` — er kind from the submitted name. The leaf uses cv_button_class form/cv_key/cv_label_mode, appends cv_css_class and host classes, and renders the three bodies with cancel URL only for cancel. Keep normalizer/icon behavior extensible for 06

Occurrences: `.planning/phases/06-form-button-leaf/06-02-PLAN.md:99`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>cv_label_mode_checks</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-06-PLAN.md:85` — DIAGNOSTIC-CONTRACT with an explicit form-only policy: retain context/list cv_label_mode_checks exactly (E211 for any malformed map including invalid values, W291 only on the own view attribute). For the finite form map, deliberately distinguish

Occurrences: `.planning/phases/06-form-button-leaf/06-06-PLAN.md:85`.

Supplemental exact path/declaration candidates: `src/crud_views/lib/view/action_menu.py:46`.

</details>

<details>
<summary><code>cv_name</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-02-PLAN.md:79` —  symbol: FORM_LEAF_KEYS in button_data.py. NEW normalized fields: cv_type, cv_name, cv_value, cv_id, cancel-only cv_cancel_url, cv_css_class, cv_flat_attrs; existing label/icon fields are reused. NEW class utility defaults: form:hid

Occurrences: `.planning/phases/06-form-button-leaf/06-02-PLAN.md:79`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:122`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>cv_type</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-02-PLAN.md:79` — html. NEW symbol: FORM_LEAF_KEYS in button_data.py. NEW normalized fields: cv_type, cv_name, cv_value, cv_id, cancel-only cv_cancel_url, cv_css_class, cv_flat_attrs; existing label/icon fields are reused. NEW class utility defaults:

Occurrences: `.planning/phases/06-form-button-leaf/06-02-PLAN.md:79`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:98`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>cv_value</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-02-PLAN.md:79` — FORM_LEAF_KEYS in button_data.py. NEW normalized fields: cv_type, cv_name, cv_value, cv_id, cancel-only cv_cancel_url, cv_css_class, cv_flat_attrs; existing label/icon fields are reused. NEW class utility defaults: form:hidden-label 

Occurrences: `.planning/phases/06-form-button-leaf/06-02-PLAN.md:79`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:101`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>cv_view</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:134` — argument&#x27;s cv_view first, never an outer context form; current helper view

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:134`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:102`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:105`.

Supplemental exact path/declaration candidates: `src/crud_views/lib/formsets/formsets.py:36`, `src/crud_views/lib/formsets/formsets.py:265`.

</details>

<details>
<summary><code>data_cv_cancel_url</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:127` — once; data_cv_cancel_url/data-cv-cancel-url become one cancel-only URL; generated icon-mode title and tooltip

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:127`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>default_label_mode</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:89` — contracts at that HEAD: default_label_mode with shared lazy defaults and independent FORM_KINDS /

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:89`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:81`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:81`.

Supplemental exact path/declaration candidates: `src/crud_views/lib/view/label_mode.py:84`.

</details>

<details>
<summary><code>delete_icon</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-04-PLAN.md:104` — input attributes usable. CrispyFormMixin and delete hooks pass submit_icon/delete_icon; workflow supplies its class default. Preserve kwargs override ordering so a custom hook icon or slot wins over the standard hook, then the explicit 

Occurrences: `.planning/phases/06-form-button-leaf/06-04-PLAN.md:104`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:106`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:106`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:113`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:113`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>display_form.html</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-05-PLAN.md:109` — out stays empty and no action group appears. Preserve the installed pack&#x27;s display_form.html fallback to uni_form.html when form_html is empty; this package-helper fix does not promise suppression of that existing pack-owned field fallback or

Occurrences: `.planning/phases/06-form-button-leaf/06-05-PLAN.md:109`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>django.conf.settings</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:146` — Only the form floor is read lazily from django.conf.settings. Map tests use isolated singleton monkeypatches

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:146`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>docs/example</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-08-PLAN.md:34` — - &quot;Documentation recipes render successfully and repeated docs/example checks do not modify generated sources or shared settings.&quot;

Occurrences: `.planning/phases/06-form-button-leaf/06-08-PLAN.md:34`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:21`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:211`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>docs/getting_started/tutorial-5-filters-permissions.md</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-05-PLAN.md:97` — &lt;read_first&gt;docs/getting_started/tutorial-5-filters-permissions.md; tests/test1/test_filter.py; tests/test1/test_crispy_buttons.py&lt;/read_first&gt;

Occurrences: `.planning/phases/06-form-button-leaf/06-05-PLAN.md:97`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:15`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:98`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:99`.

Supplemental exact path/declaration candidates: `docs/getting_started/tutorial-5-filters-permissions.md:1`.

</details>

<details>
<summary><code>docs/migrating-1.0.md</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-08-PLAN.md:18` — - docs/migrating-1.0.md

Occurrences: `.planning/phases/06-form-button-leaf/06-08-PLAN.md:18`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:38`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:114`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:115`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:82`.

Supplemental exact path/declaration candidates: `docs/migrating-1.0.md:1`.

</details>

<details>
<summary><code>docs/reference/action_menus.md</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-08-PLAN.md:10` — - docs/reference/action_menus.md

Occurrences: `.planning/phases/06-form-button-leaf/06-08-PLAN.md:10`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:45`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:81`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:82`.

Supplemental exact path/declaration candidates: `docs/reference/action_menus.md:1`.

</details>

<details>
<summary><code>docs/reference/buttons.md</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-02-PLAN.md:11` — - docs/reference/buttons.md

Occurrences: `.planning/phases/06-form-button-leaf/06-02-PLAN.md:11`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:85`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:8`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:81`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:82`.

Supplemental exact path/declaration candidates: `docs/reference/buttons.md:1`.

</details>

<details>
<summary><code>docs/reference/icons.md</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-08-PLAN.md:12` — - docs/reference/icons.md

Occurrences: `.planning/phases/06-form-button-leaf/06-08-PLAN.md:12`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:98`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:99`.

Supplemental exact path/declaration candidates: `docs/reference/icons.md:1`.

</details>

<details>
<summary><code>docs/reference/javascript.md</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-08-PLAN.md:20` — - docs/reference/javascript.md

Occurrences: `.planning/phases/06-form-button-leaf/06-08-PLAN.md:20`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:114`.

Supplemental exact path/declaration candidates: `docs/reference/javascript.md:1`.

</details>

<details>
<summary><code>docs/reference/list_view.md</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-05-PLAN.md:73` — t_response_dict and FormHelper.get_attributes; tests/test1/test_filter.py; docs/reference/list_view.md (field-only helper example); 06-SPEC.md in this phase directory&lt;/read_first&gt;

Occurrences: `.planning/phases/06-form-button-leaf/06-05-PLAN.md:73`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:14`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:98`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:99`.

Supplemental exact path/declaration candidates: `docs/reference/list_view.md:1`.

</details>

<details>
<summary><code>docs/reference/settings.md</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-02-PLAN.md:12` — - docs/reference/settings.md

Occurrences: `.planning/phases/06-form-button-leaf/06-02-PLAN.md:12`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:85`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:9`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:46`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:81`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:82`.

Supplemental exact path/declaration candidates: `docs/reference/settings.md:1`.

</details>

<details>
<summary><code>docs/reference/theme.md</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-08-PLAN.md:13` — - docs/reference/theme.md

Occurrences: `.planning/phases/06-form-button-leaf/06-08-PLAN.md:13`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:48`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:98`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:99`.

Supplemental exact path/declaration candidates: `docs/reference/theme.md:1`.

</details>

<details>
<summary><code>examples/bootstrap5</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-09-PLAN.md:85` — For L-EXAMPLE-COVERAGE, run the separate example-consumer gate below from examples/bootstrap5 so its pytest.ini selects project.settings: all test_i18n.py cases (including test_demo_pages_render_german and its translated create-submit value), 

Occurrences: `.planning/phases/06-form-button-leaf/06-09-PLAN.md:85`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:237`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:241`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:245`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>examples/bootstrap5/project/settings.py</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-08-PLAN.md:19` — - examples/bootstrap5/project/settings.py

Occurrences: `.planning/phases/06-form-button-leaf/06-08-PLAN.md:19`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:42`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:114`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:115`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:82`.

Supplemental exact path/declaration candidates: `examples/bootstrap5/project/settings.py:1`.

</details>

<details>
<summary><code>examples/bootstrap5/project/tests.py</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-09-PLAN.md:82` — ings.py; examples/bootstrap5/pytest.ini; examples/bootstrap5/test_i18n.py; examples/bootstrap5/project/tests.py (HomePageTest and SystemChecksTest); examples/bootstrap5/test_doc_links.py; docs/migrating-1.0.md Form buttons; 06-07-SUMMARY.md; 06-08-SUMMARY.md; 0

Occurrences: `.planning/phases/06-form-button-leaf/06-09-PLAN.md:82`.

Supplemental exact path/declaration candidates: `examples/bootstrap5/project/tests.py:1`.

</details>

<details>
<summary><code>examples/bootstrap5/pytest.ini</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-09-PLAN.md:82` — &lt;read_first&gt;examples/bootstrap5/project/settings.py; examples/bootstrap5/pytest.ini; examples/bootstrap5/test_i18n.py; examples/bootstrap5/project/tests.py (HomePageTest and SystemChecksTest); examples/bootstrap5/test_doc_links.py; d

Occurrences: `.planning/phases/06-form-button-leaf/06-09-PLAN.md:82`.

Supplemental exact path/declaration candidates: `examples/bootstrap5/pytest.ini:1`.

</details>

<details>
<summary><code>examples/bootstrap5/test_doc_links.py</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-09-PLAN.md:82` —  examples/bootstrap5/project/tests.py (HomePageTest and SystemChecksTest); examples/bootstrap5/test_doc_links.py; docs/migrating-1.0.md Form buttons; 06-07-SUMMARY.md; 06-08-SUMMARY.md; 06-VALIDATION.md&lt;/read_first&gt;

Occurrences: `.planning/phases/06-form-button-leaf/06-09-PLAN.md:82`.

Supplemental exact path/declaration candidates: `examples/bootstrap5/test_doc_links.py:1`.

</details>

<details>
<summary><code>examples/bootstrap5/test_docs_sync.py</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-08-PLAN.md:115` — NGELOG.md; docs/migrating-1.0.md; examples/bootstrap5/project/settings.py; examples/bootstrap5/test_docs_sync.py&lt;/read_first&gt;

Occurrences: `.planning/phases/06-form-button-leaf/06-08-PLAN.md:115`.

Supplemental exact path/declaration candidates: `examples/bootstrap5/test_docs_sync.py:1`.

</details>

<details>
<summary><code>examples/bootstrap5/test_i18n.py</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-09-PLAN.md:82` — t&gt;examples/bootstrap5/project/settings.py; examples/bootstrap5/pytest.ini; examples/bootstrap5/test_i18n.py; examples/bootstrap5/project/tests.py (HomePageTest and SystemChecksTest); examples/bootstrap5/test_doc_links.py; docs/migrating-1.0.md Form buttons;

Occurrences: `.planning/phases/06-form-button-leaf/06-09-PLAN.md:82`.

Supplemental exact path/declaration candidates: `examples/bootstrap5/test_i18n.py:1`.

</details>

<details>
<summary><code>fails_when</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:175` — &lt;fails_when&gt;The current real-render tracer fails, or the spec omits executing-branch dependency evidence or any named contract; passing old tests alone does not 

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:175`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:175`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:202`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:202`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:223`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:223`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:103`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:103`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:127`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:127`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:142`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:142`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:86`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:86`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:110`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:110`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:87`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:87`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:108`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:108`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:88`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:88`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:113`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:113`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:91`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:91`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:121`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:121`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:84`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:84`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:104`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:104`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:119`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:119`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:90`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:90`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:106`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:106`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:123`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:123`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:73`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:73`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:89`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:89`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:226`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:226`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:230`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:230`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:234`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:234`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:238`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:238`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:242`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:242`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:246`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:246`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>field_classes</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-02-PLAN.md:99` —  signature, slot-selected semantic kind, upstream generated IDs and legacy field_classes/flat_attrs for helper.inputs. Do not infer kind from the submitted name. The leaf uses cv_button_class form/cv_key/cv_label_mode, appends cv_css_clas

Occurrences: `.planning/phases/06-form-button-leaf/06-02-PLAN.md:99`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:123`.

Supplemental exact path/declaration candidates: `.venv/lib/python3.12/site-packages/crispy_forms/bootstrap.py:540`, `.venv/lib/python3.12/site-packages/crispy_forms/layout.py:232`, `.venv/lib/python3.12/site-packages/crispy_forms/layout.py:323`, `.venv/lib/python3.12/site-packages/crispy_forms/layout.py:387`, `.venv/lib/python3.12/site-packages/crispy_forms/layout.py:444`, `.venv/lib/python3.12/site-packages/crispy_forms/layout.py:508`.

</details>

<details>
<summary><code>flat_attrs</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-02-PLAN.md:99` — ot-selected semantic kind, upstream generated IDs and legacy field_classes/flat_attrs for helper.inputs. Do not infer kind from the submitted name. The leaf uses cv_button_class form/cv_key/cv_label_mode, appends cv_css_class and host 

Occurrences: `.planning/phases/06-form-button-leaf/06-02-PLAN.md:99`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>form.cv_view</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-03-PLAN.md:97` — - form.cv_view wins over conflicting helper/page owners; missing and None fall through.

Occurrences: `.planning/phases/06-form-button-leaf/06-03-PLAN.md:97`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>form.helper</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-03-PLAN.md:105` — non-None page owner, including page-level None. Do not instantiate/re-read form.helper properties to guess the current helper. Explicitly supplied tag helpers must be respected. Once a non-None owner is found, stop even if it lacks crud

Occurrences: `.planning/phases/06-form-button-leaf/06-03-PLAN.md:105`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:82`.

Supplemental exact path/declaration candidates: `src/crud_views/lib/crispy/form.py:42`, `src/crud_views/lib/crispy/form.py:43`, `src/crud_views/lib/crispy/form.py:133`, `src/crud_views/lib/crispy/form.py:134`.

</details>

<details>
<summary><code>form:cancel</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-04-PLAN.md:101` — - A delete payload with slot=form:cancel uses cancel styling/kind and retains its original name/value.

Occurrences: `.planning/phases/06-form-button-leaf/06-04-PLAN.md:101`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>form:filter-reset</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-05-PLAN.md:82` — field order. Build Apply/Reset as package adapters with form:filter-submit/form:filter-reset and original IDs, append exactly once to the isolated layout. Keep Hidden controls on inputs with current GET naming/value logic. During render_layou

Occurrences: `.planning/phases/06-form-button-leaf/06-05-PLAN.md:82`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>form:filter-submit</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-05-PLAN.md:82` —  configured layout field order. Build Apply/Reset as package adapters with form:filter-submit/form:filter-reset and original IDs, append exactly once to the isolated layout. Keep Hidden controls on inputs with current GET naming/value logic. D

Occurrences: `.planning/phases/06-form-button-leaf/06-05-PLAN.md:82`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>form:hidden-label</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-02-PLAN.md:79` — _attrs; existing label/icon fields are reused. NEW class utility defaults: form:hidden-label and form:icon-host, with exhaustive key/count documentation updated in their producing task. Private helper names are implementation-local. No new ex

Occurrences: `.planning/phases/06-form-button-leaf/06-02-PLAN.md:79`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:97`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:25`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:68`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>form:icon-host</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-02-PLAN.md:79` — /icon fields are reused. NEW class utility defaults: form:hidden-label and form:icon-host, with exhaustive key/count documentation updated in their producing task. Private helper names are implementation-local. No new external package.

Occurrences: `.planning/phases/06-form-button-leaf/06-02-PLAN.md:79`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:97`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:25`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:68`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:109`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:115`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:117`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>form:unknown</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-02-PLAN.md:98` —  rejection or warnings (M-SLOT, D-01/D-02/D-13). Cover formset:control and form:unknown as rejected layout slots and retained legacy input cases; 06-08 records this layout-only Breaking change. Missing or None textual values normalize to

Occurrences: `.planning/phases/06-form-button-leaf/06-02-PLAN.md:98`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>form_actions_label_mode</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-03-PLAN.md:82` — n for form maps, restoring it after each case; construct CrudViewsSettings(form_actions_label_mode=...) explicitly for model-level validation cases. Add real crispy rendering with a monkeypatched singleton submit=&#x27;both&#x27; and an unmapped cancel: a po

Occurrences: `.planning/phases/06-form-button-leaf/06-03-PLAN.md:82`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>form_html</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-05-PLAN.md:109` — erve the installed pack&#x27;s display_form.html fallback to uni_form.html when form_html is empty; this package-helper fix does not promise suppression of that existing pack-owned field fallback or add a global template override. The defa

Occurrences: `.planning/phases/06-form-button-leaf/06-05-PLAN.md:109`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>format_html</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:165` — Record accurate dependency findings: Django 6 removed zero-argument format_html calls, not the function;

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:165`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:115`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:163`.

Supplemental exact path/declaration candidates: `.venv/lib/python3.12/site-packages/django/utils/html.py:129`.

</details>

<details>
<summary><code>from_settings</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:144` — Record M-SETTINGS-LIFECYCLE&#x27;s existing lifecycle explicitly: from_settings captures form-map defaults when

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:144`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:81`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:138`.

Supplemental exact path/declaration candidates: `src/crud_views/lib/settings.py:13`.

</details>

<details>
<summary><code>get_attributes</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:153` — MPTY-REPLACEMENT, specify pre-dispatch preparation in the package helper&#x27;s get_attributes override:

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:153`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:67`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:82`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:83`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:108`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:142`.

Supplemental exact path/declaration candidates: `.venv/lib/python3.12/site-packages/crispy_forms/helper.py:290`.

</details>

<details>
<summary><code>get_filterset</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-05-PLAN.md:73` — irst&gt;src/crud_views/lib/views/list.py; src/crud_views/lib/views/mixins.py (get_filterset); installed crispy BasicNode.get_render/get_response_dict and FormHelper.get_attributes; tests/test1/test_filter.py; docs/reference/list_view.md (fie

Occurrences: `.planning/phases/06-form-button-leaf/06-05-PLAN.md:73`.

Supplemental exact path/declaration candidates: `src/crud_views/lib/views/mixins.py:315`.

</details>

<details>
<summary><code>get_form_actions</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:149` — Define get_form_actions returning FormActions or None; None means no group, empty FormActions is retained.

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:149`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:158`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:24`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:82`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:100`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:108`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:143`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:114`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:36`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:101`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:102`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:118`.

Supplemental exact path/declaration candidates: `src/crud_views/lib/crispy/form.py:53`.

</details>

<details>
<summary><code>get_form_class</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-06-PLAN.md:114` — ate runtime tests. Never instantiate forms/helpers, call request-dependent get_form_class, or execute custom action hooks during checks.

Occurrences: `.planning/phases/06-form-button-leaf/06-06-PLAN.md:114`.

Supplemental exact path/declaration candidates: `src/crud_views_polymorphic/lib/utils.py:64`.

</details>

<details>
<summary><code>get_render</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-05-PLAN.md:83` —  delegating to super: BasicNode.get_response_dict calls this method before get_render evaluates helper.layout truthiness. Detect a caller replacement by identity against the prepared instance, deep-copy it, and normalize an explicitly 

Occurrences: `.planning/phases/06-form-button-leaf/06-05-PLAN.md:83`.

Supplemental exact path/declaration candidates: `.venv/lib/python3.12/site-packages/crispy_forms/templatetags/crispy_forms_tags.py:70`.

</details>

<details>
<summary><code>get_response_dict</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:154` — crispy get_response_dict calls it before the helper.layout truthiness guard. Detect and isolate caller layout

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:154`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:95`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:73`.

Supplemental exact path/declaration candidates: `.venv/lib/python3.12/site-packages/crispy_forms/templatetags/crispy_forms_tags.py:137`.

</details>

<details>
<summary><code>group</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:174` — h) + r&quot;\n([\s\S]*?)(?=^## |\Z)&quot;, s) for h in headings}; assert all(m and m.group(1).strip() for m in sections.values()), &quot;Missing/empty design section&quot;; assert re.search(r&quot;\b[0-9a-f]{40}\b&quot;, sections[&quot;Prerequisite evidence&quot;].group

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:174`.

Supplemental exact path/declaration candidates: `src/crud_views/templatetags/crud_views.py:302`, `src/crud_views/lib/view/action_menu.py:102`, `tests/test1/test_button_leaves.py:253`, `tests/test1/test_button_leaves.py:310`, `tests/test1/test_button_leaves.py:318`, `tests/test1/test_button_leaves.py:326`, `tests/test1/test_guardian.py:100`, `tests/test1/test_guardian.py:667`, `tests/test1/test_manage.py:124`, `tests/test1/test_manage.py:177`, `tests/test1/test_action_menus_split.py:24`, `tests/test1/test_action_menus_split.py:30`, `tests/test1/test_action_menus_split.py:37`, `tests/test1/test_action_menus_split.py:42`, `tests/test1/test_action_menus_split.py:49`, `tests/test1/test_action_menus_split.py:55`, `tests/test1/test_action_menus_split.py:61`, `tests/test1/test_action_menus_split.py:74`, `tests/test1/test_heading_level.py:45`, `tests/test1/test_heading_level.py:166`, `tests/test1/test_action_menus_groups.py:42`, `tests/test1/test_action_menus_groups.py:51`, `tests/test1/test_action_menus_groups.py:60`, `tests/test1/test_action_menus_groups.py:69`, `tests/test1/test_action_menus_groups.py:78`, `tests/test1/test_action_menus_groups.py:88`, `tests/test1/test_action_menus_groups.py:102`, `tests/test1/test_action_menus_groups.py:116`, `tests/test1/test_action_menus_groups.py:133`, `tests/test1/od/test_icons.py:12`, `tests/test1/od/test_icons.py:19`, `tests/test1/od/test_config.py:56`, `tests/test1/od/test_config.py:66`, `tests/test1/od/test_config.py:80`, `tests/test1/od/test_config.py:85`, `tests/test1/od/test_config.py:159`, `tests/test1/od/test_config.py:188`, `tests/test1/od/test_config.py:193`, `tests/test1/od/test_config.py:272`, `examples/bootstrap5/project/features.py:54`.

</details>

<details>
<summary><code>helper.form</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-05-PLAN.md:27` — ins the selected layout across renders; explicit form construction retains helper.form identity without replacing fields.&quot;

Occurrences: `.planning/phases/06-form-button-leaf/06-05-PLAN.md:27`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:82`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:102`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:107`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:108`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:113`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:128`.

Supplemental exact path/declaration candidates: `.venv/lib/python3.12/site-packages/crispy_forms/helper.py:185`.

</details>

<details>
<summary><code>helper.input</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-04-PLAN.md:104` —  default while None/empty remains an intentional missing icon. Keep legacy helper.input attributes usable. CrispyFormMixin and delete hooks pass submit_icon/delete_icon; workflow supplies its class default. Preserve kwargs override order

Occurrences: `.planning/phases/06-form-button-leaf/06-04-PLAN.md:104`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>helper.inputs</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:157` — empty FormActions outcomes through the actual crispy tag. Clearing helper.inputs=[] no longer suppresses stock

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:157`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:91`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:98`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:99`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:160`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:143`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:36`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:102`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:118`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:140`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:153`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>helper.layout</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:154` — crispy get_response_dict calls it before the helper.layout truthiness guard. Detect and isolate caller layout

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:154`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:27`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:83`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:102`.

Supplemental exact path/declaration candidates: `.venv/lib/python3.12/site-packages/crispy_forms/helper.py:189`.

</details>

<details>
<summary><code>icon_host_keys</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:162` — thout invoking a renderer. The leaf owns one inline render, while existing icon_host_keys

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:162`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:115`.

Supplemental exact path/declaration candidates: `src/crud_views/lib/view/button_data.py:41`.

</details>

<details>
<summary><code>icons.resolve_icon</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:161` — -ICON-AVAILABILITY, both static checks and runtime missing-icon policy use icons.resolve_icon semantic

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:161`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:115`.

Supplemental exact path/declaration candidates: `src/crud_views/lib/icons.py:187`.

</details>

<details>
<summary><code>input.value</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-08-PLAN.md:117` —  replacing template evaluation, and cv_* custom-template context replacing input.value. Include preserved confirmation-only delete flow plus the new clicked submitter field, crispy&#x27;s preserved multi-word name normalization, IDs and cust

Occurrences: `.planning/phases/06-form-button-leaf/06-08-PLAN.md:117`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>inputs.html</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-05-PLAN.md:84` — 08 documents the accepted wrapper behavior rather than globally overriding inputs.html.

Occurrences: `.planning/phases/06-form-button-leaf/06-05-PLAN.md:84`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>is_formset</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-03-PLAN.md:143` — s a test obligation: installed BasicNode.get_response_dict supplies inputs/is_formset/template_pack metadata; no named provenance field is required. Task 2 and the pre-implementation spec retain the current-invocation/page-boundary pro

Occurrences: `.planning/phases/06-form-button-leaf/06-03-PLAN.md:143`.

Supplemental exact path/declaration candidates: `.venv/lib/python3.12/site-packages/crispy_forms/templatetags/crispy_forms_tags.py:108`.

</details>

<details>
<summary><code>javascript.md</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-08-PLAN.md:119` — L-TOOLTIP-DOC add form to the public data-cv-tooltip location inventory in javascript.md and the tooltip.js header comment, keeping runtime logic untouched because marker-value dispatch is already generic. Set CRUD_VIEWS_LABEL_MODE_DEFAUL

Occurrences: `.planning/phases/06-form-button-leaf/06-08-PLAN.md:119`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:141`.

Supplemental exact path/declaration candidates: `docs/reference/javascript.md:1`.

</details>

<details>
<summary><code>list_view.md</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-08-PLAN.md:102` — Address L-SUPPRESSION-MIGRATION explicitly in list_view.md and link the same recipe from the filter tutorial: clearing self.inputs or helper.inputs to [] after construction previously removed stock Apply/Rese

Occurrences: `.planning/phases/06-form-button-leaf/06-08-PLAN.md:102`.

Supplemental exact path/declaration candidates: `docs/reference/list_view.md:1`.

</details>

<details>
<summary><code>m.group</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:174` — e(h) + r&quot;\n([\s\S]*?)(?=^## |\Z)&quot;, s) for h in headings}; assert all(m and m.group(1).strip() for m in sections.values()), &quot;Missing/empty design section&quot;; assert re.search(r&quot;\b[0-9a-f]{40}\b&quot;, sections[&quot;Prerequisite evidence&quot;].group

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:174`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>manage.py</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-09-PLAN.md:238` — ered example reports system-check errors, or the test fails to start; bare manage.py check alone is insufficient.&lt;/fails_when&gt;

Occurrences: `.planning/phases/06-form-button-leaf/06-09-PLAN.md:238`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:256`.

Supplemental exact path/declaration candidates: `src/crud_views/lib/views/manage.py:1`, `examples/bootstrap5/manage.py:1`.

</details>

<details>
<summary><code>modal.js</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-07-PLAN.md:80` —  but do not replace browser constructors or fake submitter support. Change modal.js only if a demonstrated regression requires it; keep its current error, CSRF and authorization interactions.

Occurrences: `.planning/phases/06-form-button-leaf/06-07-PLAN.md:80`.

Supplemental exact path/declaration candidates: `src/crud_views/static/crud_views/js/modal.js:1`.

</details>

<details>
<summary><code>monkeypatch.setattr</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-03-PLAN.md:82` — Extend the config suite&#x27;s existing monkeypatch.setattr(crud_views_settings, ...) pattern for form maps, restoring it after each case; construct CrudViewsSettings(form_actions_label_mode=...) explicitly fo

Occurrences: `.planning/phases/06-form-button-leaf/06-03-PLAN.md:82`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>must_haves.prohibitions</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-09-PLAN.md:220` — utility, so must_haves.prohibitions is empty. The two unclassified edge assumptions above are retained.

Occurrences: `.planning/phases/06-form-button-leaf/06-09-PLAN.md:220`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>must_haves.truths</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-09-PLAN.md:178` — must_haves.truths and behavioral acceptance. The unclassified rows retain their status even though the

Occurrences: `.planning/phases/06-form-button-leaf/06-09-PLAN.md:178`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>n</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:174` — &lt;automated&gt;.venv/bin/python -c &#x27;from pathlib import Path; import re; p=Path(&quot;.planning/phases/06-form-button-leaf/06-SPEC.md&quot;); s=p.read_text(); headings=(&quot;Prerequis

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:174`.

Supplemental exact path/declaration candidates: `.venv/lib/python3.12/site-packages/django/utils/dateformat.py:251`.

</details>

<details>
<summary><code>node_modules</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:99` — preserving existing node_modules in a uniquely named backup until restoration succeeds. Do not change

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:99`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:79`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>noxfile.py</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:84` — pyproject.toml; package.json; package-lock.json; noxfile.py.

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:84`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:14`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:31`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:37`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:112`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:113`.

Supplemental exact path/declaration candidates: `noxfile.py:1`.

</details>

<details>
<summary><code>npm-cli.js</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:102` — Create the phase-local 06-JS-RUNTIME.json with absolute Node and npm-cli.js paths, actual Node/npm versions,

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:102`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:108`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>override_settings</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-02-PLAN.md:121` — Retain the location/default assertions updated in task 1 and expand lazy override_settings coverage in test_label_mode.py and test_button_data.py. Existing action contracts and location-independent finite class grammar remain unchanged.

Occurrences: `.planning/phases/06-form-button-leaf/06-02-PLAN.md:121`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:77`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:82`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:82`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:138`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:87`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:85`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:85`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:69`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>p.read_text</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:174` — h; import re; p=Path(&quot;.planning/phases/06-form-button-leaf/06-SPEC.md&quot;); s=p.read_text(); headings=(&quot;Prerequisite evidence&quot;, &quot;Form contract&quot;, &quot;Literal text and attributes&quot;, &quot;Template selection&quot;, &quot;Ownership&quot;, &quot;Helper lifecycle&quot;, &quot;Diagnos

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:174`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>package-lock.json</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:84` — pyproject.toml; package.json; package-lock.json; noxfile.py.

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:84`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:71`.

Supplemental exact path/declaration candidates: `package-lock.json:1`.

</details>

<details>
<summary><code>package.json</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:84` — pyproject.toml; package.json; package-lock.json; noxfile.py.

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:84`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:71`.

Supplemental exact path/declaration candidates: `package.json:1`.

</details>

<details>
<summary><code>polymorphic_forms</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-06-PLAN.md:110` — - Concrete polymorphic_forms mappings inspect each supported form class; custom/request-dependent providers are skipped statically and proven by real runtime renders.

Occurrences: `.planning/phases/06-form-button-leaf/06-06-PLAN.md:110`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:114`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:139`.

Supplemental exact path/declaration candidates: `src/crud_views_polymorphic/lib/utils.py:35`, `tests/test1/app/views.py:565`, `tests/test1/app/views.py:573`, `examples/bootstrap5/polymorphic_demo/views.py:72`, `examples/bootstrap5/polymorphic_demo/views.py:78`.

</details>

<details>
<summary><code>process.execPath</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:105` — Node directory to PATH, uses the selected Node to assert process.execPath/version and unchanged lock hash,

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:105`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>project.settings</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-09-PLAN.md:85` — ple-consumer gate below from examples/bootstrap5 so its pytest.ini selects project.settings: all test_i18n.py cases (including test_demo_pages_render_german and its translated create-submit value), HomePageTest.test_every_feature_landing_pag

Occurrences: `.planning/phases/06-form-button-leaf/06-09-PLAN.md:85`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>project/tests.py::HomePageTest::test_every_feature_landing_page_renders</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-09-PLAN.md:245` — &lt;automated&gt;cd examples/bootstrap5 &amp;&amp; ../../.venv/bin/pytest test_i18n.py project/tests.py::HomePageTest::test_every_feature_landing_page_renders test_doc_links.py -q&lt;/automated&gt;

Occurrences: `.planning/phases/06-form-button-leaf/06-09-PLAN.md:245`.

Supplemental exact path/declaration candidates: `examples/bootstrap5/project/tests.py:1`.

</details>

<details>
<summary><code>project/tests.py::SystemChecksTest::test_no_check_errors_with_every_viewset_registered</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-09-PLAN.md:237` — &lt;automated&gt;cd examples/bootstrap5 &amp;&amp; ../../.venv/bin/pytest project/tests.py::SystemChecksTest::test_no_check_errors_with_every_viewset_registered -q&lt;/automated&gt;

Occurrences: `.planning/phases/06-form-button-leaf/06-09-PLAN.md:237`.

Supplemental exact path/declaration candidates: `examples/bootstrap5/project/tests.py:1`.

</details>

<details>
<summary><code>pyproject.toml</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:84` — pyproject.toml; package.json; package-lock.json; noxfile.py.

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:84`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:113`.

Supplemental exact path/declaration candidates: `pyproject.toml:1`.

</details>

<details>
<summary><code>pytest.ini</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-09-PLAN.md:85` — n the separate example-consumer gate below from examples/bootstrap5 so its pytest.ini selects project.settings: all test_i18n.py cases (including test_demo_pages_render_german and its translated create-submit value), HomePageTest.test_

Occurrences: `.planning/phases/06-form-button-leaf/06-09-PLAN.md:85`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>re.escape</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:174` — dency validation&quot;, &quot;Golden history&quot;); sections={h: re.search(r&quot;(?m)^## &quot; + re.escape(h) + r&quot;\n([\s\S]*?)(?=^## |\Z)&quot;, s) for h in headings}; assert all(m and m.group(1).strip() for m in sections.values()), &quot;Missing/empty design sectio

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:174`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>re.search</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:174` — stics and icons&quot;, &quot;Dependency validation&quot;, &quot;Golden history&quot;); sections={h: re.search(r&quot;(?m)^## &quot; + re.escape(h) + r&quot;\n([\s\S]*?)(?=^## |\Z)&quot;, s) for h in headings}; assert all(m and m.group(1).strip() for m in sections.values()), &quot;Mis

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:174`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:174`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>read_bytes</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:190` — tests compare render bytes to read_bytes with no update-on-test behavior. Pin default text, name, value,

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:190`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>render</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:133` — r recovery from Django Context.dicts before flattening: the actual adapter render(form, context)

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:133`.

Supplemental exact path/declaration candidates: `src/crud_views/templatetags/crud_views.py:333`, `src/crud_views/lib/table/columns.py:23`, `src/crud_views/lib/table/columns.py:38`, `src/crud_views/lib/table/columns.py:63`, `src/crud_views/lib/conditional/layout.py:25`, `src/crud_views/lib/formsets/layout.py:10`, `src/crud_views/lib/formsets/layout.py:26`, `tests/test1/test_icon_host_leaves.py:36`, `examples/bootstrap5/object_detail/views.py:128`, `.venv/lib/python3.12/site-packages/crispy_forms/bootstrap.py:91`, `.venv/lib/python3.12/site-packages/crispy_forms/bootstrap.py:306`, `.venv/lib/python3.12/site-packages/crispy_forms/bootstrap.py:356`, `.venv/lib/python3.12/site-packages/crispy_forms/bootstrap.py:402`, `.venv/lib/python3.12/site-packages/crispy_forms/bootstrap.py:460`, `.venv/lib/python3.12/site-packages/crispy_forms/bootstrap.py:558`, `.venv/lib/python3.12/site-packages/crispy_forms/bootstrap.py:725`, `.venv/lib/python3.12/site-packages/crispy_forms/bootstrap.py:775`, `.venv/lib/python3.12/site-packages/crispy_forms/bootstrap.py:888`, `.venv/lib/python3.12/site-packages/crispy_forms/bootstrap.py:959`, `.venv/lib/python3.12/site-packages/crispy_forms/bootstrap.py:1127`, `.venv/lib/python3.12/site-packages/crispy_forms/layout.py:140`, `.venv/lib/python3.12/site-packages/crispy_forms/layout.py:190`, `.venv/lib/python3.12/site-packages/crispy_forms/layout.py:250`, `.venv/lib/python3.12/site-packages/crispy_forms/layout.py:577`, `.venv/lib/python3.12/site-packages/crispy_forms/layout.py:655`, `.venv/lib/python3.12/site-packages/crispy_forms/layout.py:746`, `.venv/lib/python3.12/site-packages/crispy_forms/layout.py:873`, `.venv/lib/python3.12/site-packages/crispy_forms/layout.py:938`, `.venv/lib/python3.12/site-packages/crispy_forms/templatetags/crispy_forms_field.py:79`, `.venv/lib/python3.12/site-packages/crispy_forms/templatetags/crispy_forms_tags.py:199`, `.venv/lib/python3.12/site-packages/crispy_forms/templatetags/crispy_forms_utils.py:20`, `.venv/lib/python3.12/site-packages/django/template/base.py:166`, `.venv/lib/python3.12/site-packages/django/template/base.py:965`, `.venv/lib/python3.12/site-packages/django/template/base.py:1017`, `.venv/lib/python3.12/site-packages/django/template/base.py:1037`, `.venv/lib/python3.12/site-packages/django/template/base.py:1075`, `.venv/lib/python3.12/site-packages/django/template/defaulttags.py:52`, `.venv/lib/python3.12/site-packages/django/template/defaulttags.py:66`, `.venv/lib/python3.12/site-packages/django/template/defaulttags.py:73`, `.venv/lib/python3.12/site-packages/django/template/defaulttags.py:101`, `.venv/lib/python3.12/site-packages/django/template/defaulttags.py:121`, `.venv/lib/python3.12/site-packages/django/template/defaulttags.py:138`, `.venv/lib/python3.12/site-packages/django/template/defaulttags.py:150`, `.venv/lib/python3.12/site-packages/django/template/defaulttags.py:188`, `.venv/lib/python3.12/site-packages/django/template/defaulttags.py:261`, `.venv/lib/python3.12/site-packages/django/template/defaulttags.py:316`, `.venv/lib/python3.12/site-packages/django/template/defaulttags.py:338`, `.venv/lib/python3.12/site-packages/django/template/defaulttags.py:367`, `.venv/lib/python3.12/site-packages/django/template/defaulttags.py:387`, `.venv/lib/python3.12/site-packages/django/template/defaulttags.py:396`, `.venv/lib/python3.12/site-packages/django/template/defaulttags.py:411`, `.venv/lib/python3.12/site-packages/django/template/defaulttags.py:420`, `.venv/lib/python3.12/site-packages/django/template/defaulttags.py:441`, `.venv/lib/python3.12/site-packages/django/template/defaulttags.py:463`, `.venv/lib/python3.12/site-packages/django/template/defaulttags.py:498`, `.venv/lib/python3.12/site-packages/django/template/defaulttags.py:509`, `.venv/lib/python3.12/site-packages/django/template/defaulttags.py:547`, `.venv/lib/python3.12/site-packages/django/template/loader_tags.py:51`, `.venv/lib/python3.12/site-packages/django/template/loader_tags.py:133`, `.venv/lib/python3.12/site-packages/django/template/loader_tags.py:176`, `.venv/lib/python3.12/site-packages/django/template/response.py:105`, `.venv/lib/python3.12/site-packages/django/template/library.py:322`, `.venv/lib/python3.12/site-packages/django/template/library.py:355`, `.venv/lib/python3.12/site-packages/django/template/backends/dummy.py:43`, `.venv/lib/python3.12/site-packages/django/template/backends/jinja2.py:64`, `.venv/lib/python3.12/site-packages/django/template/backends/django.py:102`.

</details>

<details>
<summary><code>render_icon</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-06-PLAN.md:100` — d_views/lib/view/button_data.py; src/crud_views/lib/icons.py (resolve_icon/render_icon/resolve_icon_name_class); tests/test1/test_icon_host_leaves.py; 06-SPEC.md static-check reach&lt;/read_first&gt;

Occurrences: `.planning/phases/06-form-button-leaf/06-06-PLAN.md:100`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:115`.

Supplemental exact path/declaration candidates: `src/crud_views/lib/icons.py:223`.

</details>

<details>
<summary><code>render_layout</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:137` — helper. Package filter helper render_layout supplies a private helper-owner context entry using context.push

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:137`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:151`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:156`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:67`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:82`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:82`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:83`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:83`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:83`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:88`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:108`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:108`.

Supplemental exact path/declaration candidates: `.venv/lib/python3.12/site-packages/crispy_forms/helper.py:266`.

</details>

<details>
<summary><code>request.user</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-02-PLAN.md:123` — e and string attrs, test plain strings and marked-safe strings, literal {{ request.user }}, Unicode and lazy translated values under two language contexts. Assert decoded DOM text/value equal the originals and absence of injected attribu

Occurrences: `.planning/phases/06-form-button-leaf/06-02-PLAN.md:123`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>resolve_icon</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-06-PLAN.md:100` — t.py; src/crud_views/lib/view/button_data.py; src/crud_views/lib/icons.py (resolve_icon/render_icon/resolve_icon_name_class); tests/test1/test_icon_host_leaves.py; 06-SPEC.md static-check reach&lt;/read_first&gt;

Occurrences: `.planning/phases/06-form-button-leaf/06-06-PLAN.md:100`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:151`.

Supplemental exact path/declaration candidates: `src/crud_views/lib/icons.py:187`.

</details>

<details>
<summary><code>resolve_icon_name_class</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-06-PLAN.md:100` — view/button_data.py; src/crud_views/lib/icons.py (resolve_icon/render_icon/resolve_icon_name_class); tests/test1/test_icon_host_leaves.py; 06-SPEC.md static-check reach&lt;/read_first&gt;

Occurrences: `.planning/phases/06-form-button-leaf/06-06-PLAN.md:100`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:115`.

Supplemental exact path/declaration candidates: `src/crud_views/lib/icons.py:240`.

</details>

<details>
<summary><code>sample_count</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-09-PLAN.md:114` — is part of this plan set. Context estimates use factor 1, sample_count 0 and confidence low from estimate-calibration.

Occurrences: `.planning/phases/06-form-button-leaf/06-09-PLAN.md:114`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>sections.values</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:174` — |\Z)&quot;, s) for h in headings}; assert all(m and m.group(1).strip() for m in sections.values()), &quot;Missing/empty design section&quot;; assert re.search(r&quot;\b[0-9a-f]{40}\b&quot;, sections[&quot;Prerequisite evidence&quot;].group(1)), &quot;Missing executing-branch HEAD

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:174`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>self.inputs</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-08-PLAN.md:102` — n list_view.md and link the same recipe from the filter tutorial: clearing self.inputs or helper.inputs to [] after construction previously removed stock Apply/Reset because they lived there; after migration it only clears remaining leg

Occurrences: `.planning/phases/06-form-button-leaf/06-08-PLAN.md:102`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>self.value</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-02-PLAN.md:123` — ected attributes/nodes, not just escaped substrings. Ensure no mutation of self.value, shared field_classes, normalized input dicts, or outer Context; retain constructor-visible legacy behavior. An empty explicit template argument reta

Occurrences: `.planning/phases/06-form-button-leaf/06-02-PLAN.md:123`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>setting_changed</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:147` — or explicit CrudViewsSettings arguments, not an invented setting_changed refresh; 06-03 proves the distinction.

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:147`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:81`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>settings.md</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-02-PLAN.md:96` — ion, and retain unknown-location coverage using an actual typo. Update the settings.md defaults table literal and location prose, plus test_label_mode_docs.py&#x27;s matching location assertions; full form-map documentation stays in 06-08. I

Occurrences: `.planning/phases/06-form-button-leaf/06-02-PLAN.md:96`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:84`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:85`.

Supplemental exact path/declaration candidates: `docs/reference/settings.md:1`.

</details>

<details>
<summary><code>settings.py</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:145` — settings.py is initialized and the existing crud_views_settings singleton serves map reads, like context/list.

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:145`.

Supplemental exact path/declaration candidates: `src/crud_views/lib/settings.py:1`, `examples/bootstrap5/project/settings.py:1`.

</details>

<details>
<summary><code>src/crud_views/lib/button_classes.py</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-02-PLAN.md:10` — - src/crud_views/lib/button_classes.py

Occurrences: `.planning/phases/06-form-button-leaf/06-02-PLAN.md:10`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:85`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:32`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:41`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:74`.

Supplemental exact path/declaration candidates: `src/crud_views/lib/button_classes.py:1`.

</details>

<details>
<summary><code>src/crud_views/lib/crispy/buttons.py</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:81` — src/crud_views/lib/crispy/buttons.py; src/crud_views/lib/crispy/form.py;

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:81`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:17`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:48`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:85`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:86`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:111`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:11`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:32`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:35`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:71`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:94`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:13`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:38`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:95`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:40`.

Supplemental exact path/declaration candidates: `src/crud_views/lib/crispy/buttons.py:1`.

</details>

<details>
<summary><code>src/crud_views/lib/crispy/form.py</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:81` — src/crud_views/lib/crispy/buttons.py; src/crud_views/lib/crispy/form.py;

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:81`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:11`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:37`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:95`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:96`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:100`.

Supplemental exact path/declaration candidates: `src/crud_views/lib/crispy/form.py:1`.

</details>

<details>
<summary><code>src/crud_views/lib/icons.py</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-04-PLAN.md:8` — - src/crud_views/lib/icons.py

Occurrences: `.planning/phases/06-form-button-leaf/06-04-PLAN.md:8`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:30`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:73`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:74`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:100`.

Supplemental exact path/declaration candidates: `src/crud_views/lib/icons.py:1`.

</details>

<details>
<summary><code>src/crud_views/lib/settings.py</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-03-PLAN.md:8` — - src/crud_views/lib/settings.py

Occurrences: `.planning/phases/06-form-button-leaf/06-03-PLAN.md:8`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:39`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:71`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:72`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:8`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:74`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:75`.

Supplemental exact path/declaration candidates: `src/crud_views/lib/settings.py:1`.

</details>

<details>
<summary><code>src/crud_views/lib/view/action_menu.py</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-06-PLAN.md:11` — - src/crud_views/lib/view/action_menu.py

Occurrences: `.planning/phases/06-form-button-leaf/06-06-PLAN.md:11`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:39`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:74`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:75`.

Supplemental exact path/declaration candidates: `src/crud_views/lib/view/action_menu.py:1`.

</details>

<details>
<summary><code>src/crud_views/lib/view/base.py</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-03-PLAN.md:10` — - src/crud_views/lib/view/base.py

Occurrences: `.planning/phases/06-form-button-leaf/06-03-PLAN.md:10`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:30`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:36`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:38`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:71`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:72`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:10`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:38`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:74`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:75`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:99`.

Supplemental exact path/declaration candidates: `src/crud_views/lib/view/base.py:1`.

</details>

<details>
<summary><code>src/crud_views/lib/view/button_data.py</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:83` — src/crud_views/lib/view/button_data.py; src/crud_views/lib/view/label_mode.py;

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:83`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:8`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:45`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:49`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:51`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:85`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:86`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:111`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:14`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:42`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:99`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:100`.

Supplemental exact path/declaration candidates: `src/crud_views/lib/view/button_data.py:1`.

</details>

<details>
<summary><code>src/crud_views/lib/view/buttons.py</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-06-PLAN.md:13` — - src/crud_views/lib/view/buttons.py

Occurrences: `.planning/phases/06-form-button-leaf/06-06-PLAN.md:13`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:35`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:41`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:99`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:100`.

Supplemental exact path/declaration candidates: `src/crud_views/lib/view/buttons.py:1`.

</details>

<details>
<summary><code>src/crud_views/lib/view/label_mode.py</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:83` — src/crud_views/lib/view/button_data.py; src/crud_views/lib/view/label_mode.py;

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:83`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:9`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:85`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:86`.

Supplemental exact path/declaration candidates: `src/crud_views/lib/view/label_mode.py:1`.

</details>

<details>
<summary><code>src/crud_views/lib/views/list.py</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:82` — src/crud_views/lib/views/list.py; src/crud_views/lib/views/mixins.py;

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:82`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:8`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:31`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:37`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:39`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:72`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:73`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:96`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:100`.

Supplemental exact path/declaration candidates: `src/crud_views/lib/views/list.py:1`.

</details>

<details>
<summary><code>src/crud_views/lib/views/mixins.py</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:82` — src/crud_views/lib/views/list.py; src/crud_views/lib/views/mixins.py;

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:82`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:36`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:73`.

Supplemental exact path/declaration candidates: `src/crud_views/lib/views/mixins.py:1`.

</details>

<details>
<summary><code>src/crud_views/lib/viewset/__init__.py</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-03-PLAN.md:9` — - src/crud_views/lib/viewset/__init__.py

Occurrences: `.planning/phases/06-form-button-leaf/06-03-PLAN.md:9`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:71`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:72`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:9`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:74`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:75`.

Supplemental exact path/declaration candidates: `src/crud_views/lib/viewset/__init__.py:1`.

</details>

<details>
<summary><code>src/crud_views/static/crud_views/js/list.filter.js</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-07-PLAN.md:13` — - src/crud_views/static/crud_views/js/list.filter.js

Occurrences: `.planning/phases/06-form-button-leaf/06-07-PLAN.md:13`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:92`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:93`.

Supplemental exact path/declaration candidates: `src/crud_views/static/crud_views/js/list.filter.js:1`.

</details>

<details>
<summary><code>src/crud_views/static/crud_views/js/modal.js</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-07-PLAN.md:9` — - src/crud_views/static/crud_views/js/modal.js

Occurrences: `.planning/phases/06-form-button-leaf/06-07-PLAN.md:9`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:34`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:70`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:71`.

Supplemental exact path/declaration candidates: `src/crud_views/static/crud_views/js/modal.js:1`.

</details>

<details>
<summary><code>src/crud_views/static/crud_views/js/tooltip.js</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-08-PLAN.md:21` — - src/crud_views/static/crud_views/js/tooltip.js

Occurrences: `.planning/phases/06-form-button-leaf/06-08-PLAN.md:21`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:114`.

Supplemental exact path/declaration candidates: `src/crud_views/static/crud_views/js/tooltip.js:1`.

</details>

<details>
<summary><code>src/crud_views/static/crud_views/js/viewset.js</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-07-PLAN.md:12` — - src/crud_views/static/crud_views/js/viewset.js

Occurrences: `.planning/phases/06-form-button-leaf/06-07-PLAN.md:12`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:92`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:93`.

Supplemental exact path/declaration candidates: `src/crud_views/static/crud_views/js/viewset.js:1`.

</details>

<details>
<summary><code>src/crud_views/templates/crud_views/formsets/formset.html</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-03-PLAN.md:95` — ender/get_response_dict, FormActions.render and FormHelper.get_attributes; src/crud_views/templates/crud_views/formsets/formset.html; tests/test1/test_crispy_buttons.py&lt;/read_first&gt;

Occurrences: `.planning/phases/06-form-button-leaf/06-03-PLAN.md:95`.

Supplemental exact path/declaration candidates: `src/crud_views/templates/crud_views/formsets/formset.html:1`.

</details>

<details>
<summary><code>src/crud_views/templates/crud_views/tags/button/action.html</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-02-PLAN.md:86` — &lt;read_first&gt;06-01-SUMMARY.md in this phase directory; src/crud_views/templates/crud_views/tags/button/action.html; src/crud_views/lib/crispy/buttons.py; src/crud_views/lib/view/button_data.py; src/crud_views/lib/view/label_mode.py; tests/test1/test_crispy_buttons

Occurrences: `.planning/phases/06-form-button-leaf/06-02-PLAN.md:86`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:74`.

Supplemental exact path/declaration candidates: `src/crud_views/templates/crud_views/tags/button/action.html:1`.

</details>

<details>
<summary><code>src/crud_views/templates/crud_views/tags/button/form.html</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-02-PLAN.md:18` — - src/crud_views/templates/crud_views/tags/button/form.html

Occurrences: `.planning/phases/06-form-button-leaf/06-02-PLAN.md:18`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:43`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:52`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:79`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:85`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:9`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:40`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:73`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>src/crud_views_workflow/lib/forms.py</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-04-PLAN.md:12` — - src/crud_views_workflow/lib/forms.py

Occurrences: `.planning/phases/06-form-button-leaf/06-04-PLAN.md:12`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:34`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:95`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:96`.

Supplemental exact path/declaration candidates: `src/crud_views_workflow/lib/forms.py:1`.

</details>

<details>
<summary><code>strip</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:174` — ([\s\S]*?)(?=^## |\Z)&quot;, s) for h in headings}; assert all(m and m.group(1).strip() for m in sections.values()), &quot;Missing/empty design section&quot;; assert re.search(r&quot;\b[0-9a-f]{40}\b&quot;, sections[&quot;Prerequisite evidence&quot;].group(1)), &quot;Mi

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:174`.

Supplemental exact path/declaration candidates: `.venv/lib/python3.12/site-packages/django/utils/html.py:428`.

</details>

<details>
<summary><code>submit_icon</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-04-PLAN.md:28` — anguages do not mutate shared class/icon defaults or retain another form&#x27;s submit_icon.&quot;

Occurrences: `.planning/phases/06-form-button-leaf/06-04-PLAN.md:28`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:99`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:104`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:106`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:113`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:113`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:113`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:137`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:201`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>superpowers/plans/2026-10-24-concept-review-followups.md</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:80` — superpowers/plans/2026-10-24-concept-review-followups.md (source Phase 2);

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:80`.

Supplemental exact path/declaration candidates: `superpowers/plans/2026-10-24-concept-review-followups.md:1`.

</details>

<details>
<summary><code>template_pack</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-03-PLAN.md:143` — ligation: installed BasicNode.get_response_dict supplies inputs/is_formset/template_pack metadata; no named provenance field is required. Task 2 and the pre-implementation spec retain the current-invocation/page-boundary proof and nested-

Occurrences: `.planning/phases/06-form-button-leaf/06-03-PLAN.md:143`.

Supplemental exact path/declaration candidates: `.venv/lib/python3.12/site-packages/crispy_forms/templatetags/crispy_forms_tags.py:242`, `.venv/lib/python3.12/site-packages/crispy_forms/templatetags/crispy_forms_tags.py:252`, `.venv/lib/python3.12/site-packages/crispy_forms/templatetags/crispy_forms_tags.py:258`, `.venv/lib/python3.12/site-packages/crispy_forms/templatetags/crispy_forms_tags.py:262`.

</details>

<details>
<summary><code>test_action_label_mode_config.py</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-02-PLAN.md:96` — LABEL_MODE_DEFAULTS together. In this same change update E108_LOCATIONS in test_action_label_mode_config.py to include form, move the old form-invalid case to the valid defaults parametrization, and retain unknown-location coverage using an actual typo. Upd

Occurrences: `.planning/phases/06-form-button-leaf/06-02-PLAN.md:96`.

Supplemental exact path/declaration candidates: `tests/test1/test_action_label_mode_config.py:1`.

</details>

<details>
<summary><code>test_button_classes.py</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-02-PLAN.md:97` — , before advertising icon/host rendering (H-EARLY-UTILITIES, D-14). Update test_button_classes.py&#x27;s exhaustive EXPECTED_KEYS, the measured count (71 to 73 on the reviewed tree), and utility-slot parametrization in this same producing task (H-KEYSE

Occurrences: `.planning/phases/06-form-button-leaf/06-02-PLAN.md:97`.

Supplemental exact path/declaration candidates: `tests/test1/test_button_classes.py:1`.

</details>

<details>
<summary><code>test_button_classes_templates.py</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-02-PLAN.md:96` — tching location assertions; full form-map documentation stays in 06-08. In test_button_classes_templates.py, use VARIANT_LOCATIONS for action/menu sentinel loops, assert its relation to LOCATIONS, and add separate form-leaf sentinel cases over every FORM_KI

Occurrences: `.planning/phases/06-form-button-leaf/06-02-PLAN.md:96`.

Supplemental exact path/declaration candidates: `tests/test1/test_button_classes_templates.py:1`.

</details>

<details>
<summary><code>test_button_data.py</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-02-PLAN.md:95` — Update test_label_mode.py and test_button_data.py location/default assertions in this producing task, preserving set(LABEL_MODE_DEFAULTS) == LOCATIONS, before running the tracer shard.

Occurrences: `.planning/phases/06-form-button-leaf/06-02-PLAN.md:95`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:121`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:69`.

Supplemental exact path/declaration candidates: `tests/test1/test_button_data.py:1`.

</details>

<details>
<summary><code>test_demo_pages_render_german</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-09-PLAN.md:85` — its pytest.ini selects project.settings: all test_i18n.py cases (including test_demo_pages_render_german and its translated create-submit value), HomePageTest.test_every_feature_landing_page_renders, and all test_doc_links.py reference/backlink cases. Re

Occurrences: `.planning/phases/06-form-button-leaf/06-09-PLAN.md:85`.

Supplemental exact path/declaration candidates: `examples/bootstrap5/test_i18n.py:121`.

</details>

<details>
<summary><code>test_doc_links.py</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-09-PLAN.md:85` — bmit value), HomePageTest.test_every_feature_landing_page_renders, and all test_doc_links.py reference/backlink cases. Record their collected counts and results after 06-08 enables form=both. Root pytest tests does not include this example tr

Occurrences: `.planning/phases/06-form-button-leaf/06-09-PLAN.md:85`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:245`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:271`.

Supplemental exact path/declaration candidates: `examples/bootstrap5/test_doc_links.py:1`.

</details>

<details>
<summary><code>test_docs_sync</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-09-PLAN.md:85` — Root pytest tests does not include this example tree; SystemChecksTest and test_docs_sync alone cannot substitute. Retain those two existing gates as independent evidence. A failure is an acceptance blocker to route to the producing implem

Occurrences: `.planning/phases/06-form-button-leaf/06-09-PLAN.md:85`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>test_docs_sync.py</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-09-PLAN.md:241` — &lt;automated&gt;cd examples/bootstrap5 &amp;&amp; ../../.venv/bin/pytest test_docs_sync.py -q&lt;/automated&gt;

Occurrences: `.planning/phases/06-form-button-leaf/06-09-PLAN.md:241`.

Supplemental exact path/declaration candidates: `examples/bootstrap5/test_docs_sync.py:1`.

</details>

<details>
<summary><code>test_form_button_baselines</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:67` — /test1/golden/form_buttons/*.html files enumerated above. NEW test symbol: test_form_button_baselines.

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:67`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>test_form_button_checks.py</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-06-PLAN.md:117` — In test_form_button_checks.py register a counting custom inline renderer using existing registry override fixtures and render a real package Submit in icon, both and label modes. 

Occurrences: `.planning/phases/06-form-button-leaf/06-06-PLAN.md:117`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>test_form_button_docs.py</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-08-PLAN.md:102` — m empty inputs, relocate user controls, or add a compatibility warning. In test_form_button_docs.py execute the documented omission subclass through {% crispy form helper %}, render twice, and assert its fields and named sort/order/direction hidden 

Occurrences: `.planning/phases/06-form-button-leaf/06-08-PLAN.md:102`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>test_i18n.py</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-09-PLAN.md:85` — w from examples/bootstrap5 so its pytest.ini selects project.settings: all test_i18n.py cases (including test_demo_pages_render_german and its translated create-submit value), HomePageTest.test_every_feature_landing_page_renders, and all

Occurrences: `.planning/phases/06-form-button-leaf/06-09-PLAN.md:85`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:245`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:271`.

Supplemental exact path/declaration candidates: `tests/test1/test_i18n.py:1`, `examples/bootstrap5/test_i18n.py:1`.

</details>

<details>
<summary><code>test_label_mode.py</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-02-PLAN.md:95` — Update test_label_mode.py and test_button_data.py location/default assertions in this producing task, preserving set(LABEL_MODE_DEFAULTS) == LOCATIONS, before running the trac

Occurrences: `.planning/phases/06-form-button-leaf/06-02-PLAN.md:95`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:121`.

Supplemental exact path/declaration candidates: `tests/test1/test_label_mode.py:1`.

</details>

<details>
<summary><code>test_label_mode_docs.py</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-02-PLAN.md:96` — po. Update the settings.md defaults table literal and location prose, plus test_label_mode_docs.py&#x27;s matching location assertions; full form-map documentation stays in 06-08. In test_button_classes_templates.py, use VARIANT_LOCATIONS for action/men

Occurrences: `.planning/phases/06-form-button-leaf/06-02-PLAN.md:96`.

Supplemental exact path/declaration candidates: `tests/test1/test_label_mode_docs.py:1`.

</details>

<details>
<summary><code>tests/docs</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-04-PLAN.md:123` — | H-KEYSET / H-EARLY-UTILITIES | HIGH | Utility defaults and exhaustive tests/docs move together to 06-02 task 1; this plan consumes them and expands real icon/host coverage without a second key addition. |

Occurrences: `.planning/phases/06-form-button-leaf/06-04-PLAN.md:123`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:136`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>tests/js/helpers/setup.js</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-07-PLAN.md:71` — package.json; package-lock.json; vitest.config.js; tests/js/modal.test.js; tests/js/helpers/setup.js; src/crud_views/static/crud_views/js/modal.js; 06-RESEARCH.md Package Legitimacy Audit&lt;/read_first&gt;

Occurrences: `.planning/phases/06-form-button-leaf/06-07-PLAN.md:71`.

Supplemental exact path/declaration candidates: `tests/js/helpers/setup.js:1`.

</details>

<details>
<summary><code>tests/js/list.filter.test.js</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-07-PLAN.md:11` — - tests/js/list.filter.test.js

Occurrences: `.planning/phases/06-form-button-leaf/06-07-PLAN.md:11`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:92`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:93`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:103`.

Supplemental exact path/declaration candidates: `tests/js/list.filter.test.js:1`.

</details>

<details>
<summary><code>tests/js/modal.test.js</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-07-PLAN.md:8` — - tests/js/modal.test.js

Occurrences: `.planning/phases/06-form-button-leaf/06-07-PLAN.md:8`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:29`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:35`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:70`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:71`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:83`.

Supplemental exact path/declaration candidates: `tests/js/modal.test.js:1`.

</details>

<details>
<summary><code>tests/js/viewset.test.js</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-07-PLAN.md:10` — - tests/js/viewset.test.js

Occurrences: `.planning/phases/06-form-button-leaf/06-07-PLAN.md:10`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:92`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:93`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:103`.

Supplemental exact path/declaration candidates: `tests/js/viewset.test.js:1`.

</details>

<details>
<summary><code>tests/test1/app/views.py</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:211` — &lt;read_first&gt;tests/test1/test_workflow.py; tests/test1/test_filter.py; tests/test1/app/views.py; .planning/phases/06-form-button-leaf/06-SPEC.md&lt;/read_first&gt;

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:211`.

Supplemental exact path/declaration candidates: `tests/test1/app/views.py:1`.

</details>

<details>
<summary><code>tests/test1/conftest.py</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:184` — &lt;read_first&gt;tests/test1/test_crispy_buttons.py; tests/test1/test_crud.py; tests/test1/conftest.py; tests/test1/test_pagination_docs.py; .planning/phases/06-form-button-leaf/06-SPEC.md&lt;/read_first&gt;

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:184`.

Supplemental exact path/declaration candidates: `tests/test1/conftest.py:1`.

</details>

<details>
<summary><code>tests/test1/golden/form_buttons/*.html</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:67` — tests/test1/golden/form_buttons/*.html files enumerated above. NEW test symbol: test_form_button_baselines.

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:67`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>tests/test1/golden/form_buttons/create.html</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:12` — - tests/test1/golden/form_buttons/create.html

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:12`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:37`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:183`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:23`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:135`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>tests/test1/golden/form_buttons/delete.html</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:14` — - tests/test1/golden/form_buttons/delete.html

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:14`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:183`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:25`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:135`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>tests/test1/golden/form_buttons/filter.html</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:16` — - tests/test1/golden/form_buttons/filter.html

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:16`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:210`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:12`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:72`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>tests/test1/golden/form_buttons/update.html</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:13` — - tests/test1/golden/form_buttons/update.html

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:13`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:183`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:24`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:135`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>tests/test1/golden/form_buttons/workflow.html</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:15` — - tests/test1/golden/form_buttons/workflow.html

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:15`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:210`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:26`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:135`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>tests/test1/test_action_label_mode_config.py</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:91` — tests/test1/test_action_label_mode_config.py tests/test1/test_button_classes.py -q; record the command,

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:91`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:174`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:14`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:85`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:102`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:12`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:71`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:72`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:85`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:109`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:75`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:90`.

Supplemental exact path/declaration candidates: `tests/test1/test_action_label_mode_config.py:1`.

</details>

<details>
<summary><code>tests/test1/test_button_classes.py</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:91` — tests/test1/test_action_label_mode_config.py tests/test1/test_button_classes.py -q; record the command,

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:91`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:174`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:13`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:85`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:102`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:86`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:89`.

Supplemental exact path/declaration candidates: `tests/test1/test_button_classes.py:1`.

</details>

<details>
<summary><code>tests/test1/test_button_classes_templates.py</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-02-PLAN.md:16` — - tests/test1/test_button_classes_templates.py

Occurrences: `.planning/phases/06-form-button-leaf/06-02-PLAN.md:16`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:85`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:102`.

Supplemental exact path/declaration candidates: `tests/test1/test_button_classes_templates.py:1`.

</details>

<details>
<summary><code>tests/test1/test_button_data.py</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:174` — g-branch HEAD SHA&quot;&#x27; &amp;&amp; .venv/bin/pytest tests/test1/test_crispy_buttons.py tests/test1/test_button_data.py tests/test1/test_label_mode.py tests/test1/test_action_label_mode_config.py tests/test1/test_button_classes.py -q&lt;/automated&gt;

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:174`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:21`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:85`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:102`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:111`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:126`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:120`.

Supplemental exact path/declaration candidates: `tests/test1/test_button_data.py:1`.

</details>

<details>
<summary><code>tests/test1/test_button_leaves.py</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-02-PLAN.md:86` — src/crud_views/lib/view/label_mode.py; tests/test1/test_crispy_buttons.py; tests/test1/test_button_leaves.py&lt;/read_first&gt;

Occurrences: `.planning/phases/06-form-button-leaf/06-02-PLAN.md:86`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:112`.

Supplemental exact path/declaration candidates: `tests/test1/test_button_leaves.py:1`.

</details>

<details>
<summary><code>tests/test1/test_cancel_origin.py</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-02-PLAN.md:136` — ectory; tests/test1/test_form_buttons_golden.py; tests/test1/test_crud.py; tests/test1/test_cancel_origin.py&lt;/read_first&gt;

Occurrences: `.planning/phases/06-form-button-leaf/06-02-PLAN.md:136`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:141`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:67`.

Supplemental exact path/declaration candidates: `tests/test1/test_cancel_origin.py:1`.

</details>

<details>
<summary><code>tests/test1/test_crispy_buttons.py</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:174` — ence&quot;].group(1)), &quot;Missing executing-branch HEAD SHA&quot;&#x27; &amp;&amp; .venv/bin/pytest tests/test1/test_crispy_buttons.py tests/test1/test_button_data.py tests/test1/test_label_mode.py tests/test1/test_action_label_mode_config.py tests/test1/test_button_classes.py -q&lt;/au

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:174`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:184`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:19`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:85`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:86`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:102`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:111`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:126`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:13`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:85`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:94`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:95`, `.planning/phases/06-form-button-leaf/06-03-PLAN.md:109`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:14`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:95`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:96`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:107`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:10`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:72`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:87`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:96`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:97`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:112`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:38`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:113`.

Supplemental exact path/declaration candidates: `tests/test1/test_crispy_buttons.py:1`.

</details>

<details>
<summary><code>tests/test1/test_crud.py</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:184` — &lt;read_first&gt;tests/test1/test_crispy_buttons.py; tests/test1/test_crud.py; tests/test1/conftest.py; tests/test1/test_pagination_docs.py; .planning/phases/06-form-button-leaf/06-SPEC.md&lt;/read_first&gt;

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:184`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:191`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:201`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:136`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:141`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:67`.

Supplemental exact path/declaration candidates: `tests/test1/test_crud.py:1`.

</details>

<details>
<summary><code>tests/test1/test_filter.py</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:211` — &lt;read_first&gt;tests/test1/test_workflow.py; tests/test1/test_filter.py; tests/test1/app/views.py; .planning/phases/06-form-button-leaf/06-SPEC.md&lt;/read_first&gt;

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:211`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:222`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:9`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:33`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:72`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:73`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:87`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:96`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:97`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:112`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:113`.

Supplemental exact path/declaration candidates: `tests/test1/test_filter.py:1`.

</details>

<details>
<summary><code>tests/test1/test_form_button_checks.py</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-06-PLAN.md:12` — - tests/test1/test_form_button_checks.py

Occurrences: `.planning/phases/06-form-button-leaf/06-06-PLAN.md:12`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:33`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:69`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:74`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:90`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:99`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:120`, `.planning/phases/06-form-button-leaf/06-07-PLAN.md:113`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:34`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>tests/test1/test_form_button_docs.py</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-08-PLAN.md:16` — - tests/test1/test_form_button_docs.py

Occurrences: `.planning/phases/06-form-button-leaf/06-08-PLAN.md:16`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:40`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:49`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:76`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:98`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:105`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>tests/test1/test_form_buttons_golden.py</code> — EXCLUDED_NEW</summary>

Declared phase deliverable, not an existing-source claim.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:11` — - tests/test1/test_form_buttons_golden.py

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:11`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:33`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:36`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:66`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:183`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:201`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:210`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:222`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:22`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:135`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:136`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:141`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:11`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:72`, `.planning/phases/06-form-button-leaf/06-05-PLAN.md:87`, `.planning/phases/06-form-button-leaf/06-09-PLAN.md:31`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>tests/test1/test_icon_host_leaves.py</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-04-PLAN.md:10` — - tests/test1/test_icon_host_leaves.py

Occurrences: `.planning/phases/06-form-button-leaf/06-04-PLAN.md:10`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:73`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:74`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:86`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:100`.

Supplemental exact path/declaration candidates: `tests/test1/test_icon_host_leaves.py:1`.

</details>

<details>
<summary><code>tests/test1/test_icons_registry.py</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-04-PLAN.md:74` — ses.py; src/crud_views/lib/icons.py; tests/test1/test_icon_host_leaves.py; tests/test1/test_icons_registry.py; src/crud_views/templates/crud_views/tags/button/action.html&lt;/read_first&gt;

Occurrences: `.planning/phases/06-form-button-leaf/06-04-PLAN.md:74`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:86`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:107`.

Supplemental exact path/declaration candidates: `tests/test1/test_icons_registry.py:1`.

</details>

<details>
<summary><code>tests/test1/test_label_mode.py</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:90` — VARIANT_LOCATIONS. Before authoring the spec, run .venv/bin/pytest tests/test1/test_label_mode.py

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:90`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:174`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:20`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:85`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:111`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:126`, `.planning/phases/06-form-button-leaf/06-06-PLAN.md:90`.

Supplemental exact path/declaration candidates: `tests/test1/test_label_mode.py:1`.

</details>

<details>
<summary><code>tests/test1/test_label_mode_docs.py</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-02-PLAN.md:15` — - tests/test1/test_label_mode_docs.py

Occurrences: `.planning/phases/06-form-button-leaf/06-02-PLAN.md:15`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:85`, `.planning/phases/06-form-button-leaf/06-02-PLAN.md:102`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:11`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:81`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:82`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:89`.

Supplemental exact path/declaration candidates: `tests/test1/test_label_mode_docs.py:1`.

</details>

<details>
<summary><code>tests/test1/test_pagination_docs.py</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:184` — test_crispy_buttons.py; tests/test1/test_crud.py; tests/test1/conftest.py; tests/test1/test_pagination_docs.py; .planning/phases/06-form-button-leaf/06-SPEC.md&lt;/read_first&gt;

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:184`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:99`.

Supplemental exact path/declaration candidates: `tests/test1/test_pagination_docs.py:1`.

</details>

<details>
<summary><code>tests/test1/test_workflow.py</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-01-PLAN.md:211` — &lt;read_first&gt;tests/test1/test_workflow.py; tests/test1/test_filter.py; tests/test1/app/views.py; .planning/phases/06-form-button-leaf/06-SPEC.md&lt;/read_first&gt;

Occurrences: `.planning/phases/06-form-button-leaf/06-01-PLAN.md:211`, `.planning/phases/06-form-button-leaf/06-01-PLAN.md:222`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:96`, `.planning/phases/06-form-button-leaf/06-04-PLAN.md:107`.

Supplemental exact path/declaration candidates: `tests/test1/test_workflow.py:1`.

</details>

<details>
<summary><code>tooltip.js</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-08-PLAN.md:119` —  to the public data-cv-tooltip location inventory in javascript.md and the tooltip.js header comment, keeping runtime logic untouched because marker-value dispatch is already generic. Set CRUD_VIEWS_LABEL_MODE_DEFAULTS form=both in the

Occurrences: `.planning/phases/06-form-button-leaf/06-08-PLAN.md:119`, `.planning/phases/06-form-button-leaf/06-08-PLAN.md:141`.

Supplemental exact path/declaration candidates: `src/crud_views/static/crud_views/js/tooltip.js:1`.

</details>

<details>
<summary><code>uni_form.html</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-05-PLAN.md:109` — group appears. Preserve the installed pack&#x27;s display_form.html fallback to uni_form.html when form_html is empty; this package-helper fix does not promise suppression of that existing pack-owned field fallback or add a global template ove

Occurrences: `.planning/phases/06-form-button-leaf/06-05-PLAN.md:109`.

Supplemental declaration/path: none asserted.

</details>

<details>
<summary><code>view/buttons.py</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-06-PLAN.md:69` — /test1/test_form_button_checks.py. NEW private/static form icon checker in view/buttons.py (suggested cv_form_icon_mode_checks). No new check IDs. Finite form contract tests live in this file or existing test_button_data.py read-only covera

Occurrences: `.planning/phases/06-form-button-leaf/06-06-PLAN.md:69`.

Supplemental exact path/declaration candidates: `src/crud_views/lib/view/buttons.py:1`.

</details>

<details>
<summary><code>vitest.config.js</code> — UNCHECKABLE</summary>

Effective intel authority has no populated index; Python/template/signature/CLI evidence cannot be verified by that adapter.

Plan evidence (exact line excerpt): `.planning/phases/06-form-button-leaf/06-07-PLAN.md:71` — &lt;read_first&gt;package.json; package-lock.json; vitest.config.js; tests/js/modal.test.js; tests/js/helpers/setup.js; src/crud_views/static/crud_views/js/modal.js; 06-RESEARCH.md Package Legitimacy Audit&lt;/read_first

Occurrences: `.planning/phases/06-form-button-leaf/06-07-PLAN.md:71`.

Supplemental exact path/declaration candidates: `vitest.config.js:1`.

</details>


</details>
