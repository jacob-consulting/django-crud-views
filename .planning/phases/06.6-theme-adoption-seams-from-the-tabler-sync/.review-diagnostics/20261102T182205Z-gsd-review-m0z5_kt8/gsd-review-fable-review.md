# Cross-AI Plan Review — Phase 06.6, Cycle 3 (HEAD `9b10cf0`)

**Reviewer access note.** Core repo read fully. The sibling `/home/alex/projects/alex/tabler-test` is outside this session's permitted working directory: every `ls`, `git -C`, `find`, `grep` and `Read` against it was blocked by the sandbox. I therefore could **not** independently reproduce the `885dfc7` clean-checkout, monorepo-layout, `pyproject` or `formactions.html` claims. Those rest on the planner's recorded read-only verification (`06.6-SOURCE-AUDIT.md:163-172`, `06.6-RESEARCH.md` addendum, `06.6-VALIDATION.md:23`). Per the instructions, I downgrade that part to an open question rather than asserting either way. Everything else below cites core source I read.

Baseline facts verified before the per-plan sections:

- HEAD is `9b10cf0`; pinned pre-phase revision `cb26af4` exists and `git diff --stat cb26af4 HEAD -- src tests docs examples noxfile.py pyproject.toml` is empty, so the plan-01/06 archive baseline equals the current product tree.
- Cached runtimes: `.nox/tests-3-12-django-4-2` (Django 4.2.30, crispy 2.5, pack 2026.3), `.nox/tests-3-12-django-5-2` (5.2.18 / 2.7 / 2026.9), `.nox/crispy_floor-3-12-django-4-2` and `.nox/crispy_floor-3-12-django-6-0` (both crispy 2.0 / pack 2023.10). No current-pack Django 6.0 env exists (H12 disposition is accurate).
- Nested form/token problem reproduced in `tests/test1/golden/form_frame/create.html` (two `<form`, two `csrfmiddlewaretoken`).

---

## 06.6-01

**Summary.** The tracer-first ownership plan is grounded in the actual seams: `CrispyFormMixin.helper` and `CrispyDeleteForm.helper` build fresh `FormHelper()` instances with crispy's default `form_tag=True` (`src/crud_views/lib/crispy/form.py:43-50,136-146`); the inner template reads `form.helper` twice and falls to `{% crispy form %}` (`src/crud_views/templates/crud_views/tags/form.html:3-7`), which crispy resolves as `FormHelper() if not hasattr(actual_form, "helper") else actual_form.helper` (`crispy_forms/templatetags/crispy_forms_tags.py:96`), so the no-helper branch also nests. `cv_render_form` flattens context today (`src/crud_views/templatetags/crud_views.py:464-466`) while `cv_alert` uses the `context.push` pattern the plan mandates (`:442-455`). The floor pack's token branch is independent of its form-tag branch (`.nox/crispy_floor-3-12-django-6-0/.../bootstrap5/whole_uni_form.html:4-7`), which is why render-local `disable_csrf` is required rather than `form_tag=False` alone.

**Strengths.**
- H02 closure is complete, not just for the two named fixtures: I enumerated every `def helper` in `tests/`, `examples/`, `src/`. Only `_CustomHelperForm` and `_DeleteCustomHelper` (`tests/test1/test_form_button_checks.py:560-586`) return `form_tag=True` helpers *and* render through create/delete pages (`:688,748,1084,1102`). The other custom helpers either already set `form_tag=False` (`views_formset.py:45-50`, `test_fragment_authorization.py:178-196,1584`, `conditional_formsets_server.py:140,259`, `examples/.../conditional/views.py:133-136`) or render standalone via `render_crispy_form` (`tests/test1/test_conditional_layout.py:41-107`), which D-01 does not touch.
- Enforced-CSRF precedent exists (`tests/test1/test_form_validation.py:78,91,105`), so the tracer's 403 cases have a working pattern.
- A10 handling is backed by real tier helpers: `_CV_HELPER_OWNER` / `_CV_PAGE_OWNER` scan `Context.dicts` (`src/crud_views/lib/crispy/buttons.py:34-71`); flattening would lose them.
- Crispy's per-node `render_context` cache (`crispy_forms_tags.py:84-88`) is isolated per `Template.render` via `push_state`, so switching to `template.template.render(context)` does not leak helpers across two forms on one page.

**Concerns.**
- LOW — The plan's "falsey helper" wording is right but worth being precise in execution: `FormHelper.__len__` counts layout fields, so an empty-layout helper is falsy and today silently falls to the `{% crispy form %}` branch. The plan's "presence rather than truthiness" rule covers it; the test should include an explicit empty-`Layout()` helper so the regression is discriminating.

**Suggestions.**
- Add the empty-layout helper to the 01-03 matrix explicitly (currently implied by "falsey").

**Risk: LOW.** Mechanism, fixtures and test precedents all verified in source.

---

## 06.6-02

**Summary.** The theme layer slots into an existing lazy, strict/log resolver. `default_label_mode` reads `_raw_label_mode_defaults()` on every call and falls back to the immutable `LABEL_MODE_DEFAULTS` (`src/crud_views/lib/view/label_mode.py:56-60,86-119`); the three fallback lambdas at `:107,110,118` are exactly the "package-only fallback destinations" D-07 redirects to `_theme_or_package_default`. E108 validates raw settings independently (`src/crud_views/lib/settings.py:159-188`), and both W292 branches resolve through the public resolver (`src/crud_views/lib/view/buttons.py:435-443,568-578`), so "W292 already invokes the public resolver: prove, don't modify" is correct.

**Strengths.**
- A17 recursion guard is necessary and correctly placed: `_invalid_label_mode` calls `fallback()` before logging (`:75`), so a settings-reading fallback would re-enter a malformed setting.
- A18 is grounded: `card.py:54,119` and `button_data.py:146,310` are independent callers of the floor.
- Registry-isolation pattern to copy exists at `tests/test1/test_button_classes.py:94-101`; `tests/test1/conftest.py:23-32` indeed resets only `_warned`.

**Concerns.**
- LOW — `form_label_mode` falls back to `default_label_mode("form")` (`label_mode.py:134,145`), i.e. the public resolver. That is correct chain order (owner map → setting → theme → package), but 02-02's test list should include "malformed owner map + malformed setting + theme entry" to prove the theme value is reached through two fallbacks without recursion.

**Suggestions.**
- Add that two-level fallback case to 02-02.

**Risk: LOW.**

---

## 06.6-03

**Summary.** The floor incompatibility is real and reproduced on disk: floor `formactions.html` hardcodes `class="mb-3"` and never reads `css_class` (`.nox/crispy_floor-3-12-django-6-0/.../layout/formactions.html:1`), while the current pack renders `{{ formactions.css_class|default:'' }}` (`.nox/tests-3-12-django-5-2/.../layout/formactions.html:3`). Floor `FormActions.__init__` accepts `css_class` and `template` (`.nox/crispy_floor-3-12-django-6-0/.../crispy_forms/bootstrap.py:299-302`), so a per-instance template override is a viable scoped bridge. Three construction sites verified: `form.py:55-56`, `form.py:141-144`, `list.py:125-133`.

**Strengths.**
- W362 grammar already rejects `form:actions:icon`: `_action_key_parts` returns `None` unless `parts[1] in FORM_KINDS` (`button_classes.py:255-266`), so "do not add these keys to FORM_KINDS" is the exact mechanism that keeps mode-suffixed utility keys invalid.
- H05 is grounded: the filter helper caches `_cv_actions` on the prepared layout (`list.py:95-99`), so render-time key resolution is required.
- C2-A03 closed: `crispy_floor-3-12-django-4-2` exists with Django 4.2.30 / crispy 2.0 / pack 2023.10 (dist-info listing), and 03-03 now runs it separately.
- The existing exclusion `CRISPY_FLOOR_DESELECT` is exactly one test (`noxfile.py:57`); the plan's "no new exclusion" rule matches.

**Concerns.**
- LOW — The bridge discriminator compares resolved template *source* to an audited fixture string. Both floor and current templates share `label_class`/`field_class` branches, so the fixture must be the full floor file, not a fragment. The plan says so ("compare the entire source"). No gap, noted only because a partial fixture would silently match a future pack.

**Suggestions.**
- None beyond what 03-01 already states.

**Risk: LOW–MEDIUM.** Mechanism verified; the residual risk is research assumption A1 (bridge preserves floor structure), which 03-01 is explicitly designed to resolve or halt on.

---

## 06.6-04

**Summary.** Minimal and correct. The alert leaf has exactly the two literals the keys replace (`src/crud_views/templates/crud_views/tags/alert.html:2,5`) and already uses `cv_button_class` for the level (`:2`). `EXPECTED_KEYS` is pinned at 84 (`tests/test1/test_button_classes.py:105`) and the documented count is parsed from `buttons.md` (`:113-116`; prose at `docs/reference/buttons.md:151-155`). The raw-byte golden test for the dismissible alert (`tests/test1/test_alerts.py:170-181`) is the right D-17 guard.

**Strengths.**
- H04 ordering is coherent: 04 owns 84→86 in wave 1, 03 owns 86→88 in wave 2, and `test_button_classes.py:105,116` enforce both the set and the doc count.
- A03 whitespace rule is specific and testable (`"alert alert-success"` with no trailing separator for empty values).
- 04-02's "alert:close:icon stays invalid" is guaranteed by `_action_key_parts` (`button_classes.py:262-263`): `alert` is neither in `VARIANT_LOCATIONS` nor `form`.

**Concerns.**
- LOW — `docs/reference/theme.md:310` states the frame classes "are literal Bootstrap CSS". After 04-01 lands in wave 1 that sentence is false until plan 08 (wave 3) rewrites `theme.md`. No test guards the sentence (grep of `tests/` for "literal Bootstrap" is empty), and 04-01's file list includes `buttons.md` but not `theme.md`. 08-01 says "Explain alert replacement/omission" but does not name this line.

**Suggestions.**
- Either add `docs/reference/theme.md` to 04-01's files with a one-sentence correction outside the single fence, or name `theme.md:310` explicitly in 08-01. Keep the fence count at one either way (`tests/test1/test_alerts.py:249-253` asserts exactly one).

**Risk: LOW.**

---

## 06.6-05

**Summary.** The request-matrix plan is consistent with the actual modal gate and template branches. `cv_modal_supported` defaults `False` at `src/crud_views/lib/view/base.py:111` and E251 enforces it (`:169-170`); it is `True` only on `CustomFormView`/`CustomFormNoObjectView` (`views/form.py:20,52`), `DeleteView` (`views/delete.py:55`) and the object-detail mixin. `WorkflowView(CustomFormView)` (`src/crud_views_workflow/lib/views.py:18`) therefore inherits `True`, so C2-A01's "custom/delete/workflow supported, create/update not" is **correct**. Delete omits the form under `{% if not has_protected_objects %}` (`view_delete.content.html:16`), workflow under `{% if has_workflow_choices %}` (`view_workflow.action.html:6-19`).

**Strengths.**
- H10's sibling-form requirement matches real stock templates: `language_selector.html:13` (POST with token), `list_action_form.html:2` (hidden POST), `card_order.html:4` and `list_filter.inner.html:14` (GET).
- A11 removal is safe and does restore W292 reach: `_static_form_controls` requires `_inherits(form_class, "helper", CrispyFormMixin)` (`buttons.py:~505`), and both named overrides (`views_formset.py:45-50`, `examples/bootstrap5/formsets/views.py:37-41`) only set `form_tag=False` on `super().helper`.
- Child formset helpers already set `form_tag=False` and `disable_csrf=True` (`inline_formset.py:58-59,144-145`) and render via `{% crispy x_form.form x_form.helper %}` (`formsets/formset.html:42`), outside `cv_render_form`; "child tokens stay suppressed" holds.
- A12 is accurate: after replacing line 15, `view_workflow.action.html:2` (`{% load crispy_forms_tags %}`) becomes unused.
- Existing raw guard to extend is at `tests/test1/test_formsets.py:16-35`.

**Concerns.**
- LOW — The C2-A05 deferral names two overrides in `test_fragment_authorization.py` (lines 178, 193), but a third `form_tag=False` helper exists at `:1584-1586`. The deferral's reasoning (compatible, no runtime failure) applies equally; the ledger is just incomplete.

**Suggestions.**
- Add `test_fragment_authorization.py:1584` to the C2-A05 deferral row so the retained-override inventory is exact.

**Risk: LOW.**

---

## 06.6-06

**Summary.** The baseline utility is fail-closed by design and its in-repo preconditions check out: `cb26af4` exists and equals HEAD for product paths; `tests/browser/` has no `__init__.py` (so the `importlib` strategy is needed); `pyproject.toml:129-130` sets only `--strict-markers`, so `pytest tests -k theme_adoption_sources` will collect `tests/browser/test_theme_adoption_sources.py` under default `test_*.py` discovery. The companion-side facts (monorepo layout, `885dfc7`, Python ≥3.14 / Django 6.1 requirement, two README suites) are consistent across `06.6-SOURCE-AUDIT.md:163-172`, the research addendum and `06.6-VALIDATION.md:23`, but **I could not read the companion from this sandbox** (see access note).

**Strengths.**
- A05 is real: `tests/test1/conftest.py` configures Django in `pytest_configure`; a Django-free utility avoids ordering hazards when `tests/browser` is collected before `tests/test1`.
- A09's halted-summary contract matches the GSD `status: halted` semantics (`templates/summary.md:175`), so dependents are correctly blocked rather than offered.
- The `user_setup` block names the exact prerequisite (`CV_THEME_PYTHON`, Python ≥3.14 / Django 6.1) instead of implying availability.
- Import-shadowing risk (an editable install in the companion env pointing at the *original* core checkout) is already covered by 06-01's "probe actual module/template origins" and 07-01's "record the resolved imports … verify against the baseline".

**Concerns.**
- OPEN QUESTION (not a plan defect) — Independent confirmation of the companion identity was not possible here. The plan correctly makes `--capture-baseline` re-validate revision/content hashes at execution, so a wrong recorded identity fails closed rather than silently passing.
- LOW — `uv python list` and the companion `.venv` check were also blocked; the plan's statement that no companion environment exists is therefore unverified by me, but it is phrased as a prerequisite, not a fact.

**Suggestions.**
- None required. The executor should paste the raw `git -C ../tabler-test rev-parse HEAD` / `status --porcelain` output into `06-COMPANION-SETUP.md` so later reviewers can see the evidence this sandbox could not.

**Risk: MEDIUM (environmental, not design).** The missing Python 3.14 / Django 6.1 dependency environment is the single most likely halt point in the phase, and the plan handles it truthfully.

---

## 06.6-07

**Summary.** The browser/patch plan reuses verified harness conventions: `presentation.cjs:2-5` defaults `CV_PRESENTATION_PORT` to 8145 and rejects 8143/8144 (C2-A04 verified), `modal-focus.cjs:21,79` owns 8143 and `conditional-formsets.cjs:28-31` owns 8144. `CV_FOCUS_PYTHON` is the existing interpreter variable (`modal-focus.cjs:81`, `conditional-formsets.cjs:123`). C2-A06's "migrate only an existing bypass copy; absence is success" is the right rule given 07-03's no-growth gate; whether such copies exist at `885dfc7` is unverifiable from here but the plan defers to execution-time inspection.

**Strengths.**
- Workflow modal coverage is legitimate (inherits `cv_modal_supported=True`, see 06.6-05).
- The port collision test ("leave the listener alive, prove it still answers") is a concrete, falsifiable behaviour rather than a note.
- 07-03 binds the patch to exact base hashes and replays on fresh copies with the tested `--verify-replay` utility from plan 06.

**Concerns.**
- LOW — `PATTERNS.md:199-201` quotes the presentation harness provenance block, which asserts `/^(4\.2|5\.2|6\.0)\./` on the Django version. 07-01/02 say "reuse existing browser runtime discovery conventions" and separately "use the Python ≥3.14 / Django 6.1 runtime". If the executor copies the provenance block verbatim, the companion server is rejected for Django 6.1. The plan's intent is clear; the specific assertion to *not* copy is not named.
- LOW — Overloading `CV_FOCUS_PYTHON` for a Django 6.1 interpreter in plan 07 while plan 09 sets the same variable to the 5.2 interpreter for `modal-focus.cjs` is safe only if the lanes run in separate shell environments. Plan 09 runs them sequentially from explicit commands, so this is a documentation nit.

**Suggestions.**
- In 07-01, state that the theme harness asserts a Django `6.1.x` series (or the companion's declared range) and must not inherit the core `4.2|5.2|6.0` regex.
- Optionally rename the harness variable to `CV_THEME_PYTHON` throughout plan 07 to avoid the overload with plan 09.

**Risk: MEDIUM (execution-heavy, gated).** Design is sound; outcomes depend on plan 06's baseline and the companion runtime.

---

## 06.6-08

**Summary.** Documentation obligations are pinned to real guard tests. `test_migration_e108_location_inventory` asserts the exact string "falls back to its package floor" (`tests/test1/test_label_mode_docs.py:786-797`), so H07's "update both together in 08-02" is mandatory, not optional. `_documented_alert_frame` asserts exactly one fence under "### Custom alert frame" (`tests/test1/test_alerts.py:249-253`), matching H08. `test_canonical_label_mode_resolution_sections` (`test_label_mode_docs.py:180`) enforces the numbered structure 08-01 preserves. CHANGELOG has an `## Unreleased` with `### Breaking`/`### Fixed`/`### Added` (`CHANGELOG.md:3-7,311,421`) and `migrating-1.0.md` has `## Form buttons` (`:328`) and `## A downstream theme` (`:1003`) anchors.

**Strengths.**
- C2-A07 fixed: 08-02 `read_first` now cites plan 01 / `01-ownership-evidence.md`.
- C2-A02 wording is now accurate: library helpers' `form_tag=False` changes standalone crispy output (wrapper removed, token kept), and the plan publishes a caller-owned outer-form recipe rather than claiming "unchanged".
- A08 is grounded: `test_form_button_docs.py` exists and runs the tutorial/list-helper recipes.

**Concerns.**
- LOW — Same as 06.6-04: `theme.md:310` ("literal Bootstrap CSS") must be rewritten here if plan 04 does not touch it. Not currently named.

**Suggestions.**
- Name `docs/reference/theme.md:310` in 08-01's action.

**Risk: LOW.**

---

## 06.6-09

**Summary.** The final-gate plan matches the real environment. `CRISPY_FLOOR_TESTS` (`noxfile.py:28-52`) does not yet include `test_alerts.py` or `test_button_classes.py`; A15's addition is substantive. The example gate is runnable: `examples/bootstrap5/pytest.ini` sets `DJANGO_SETTINGS_MODULE = project.settings` and `pythonpath = .`, ten `tests.py` modules exist, and `project/urls.py:15-16` holds the standalone login `FormHelper()` the plan names. `CV_FRAGMENT_PYTHON` is read by `tests/js-integration/formset.test.js:92-108`; `vitest.integration.config.js`, `.venv/bin/mkdocs`, `.venv/bin/ruff` and `node_modules/vitest/vitest.mjs` all exist.

**Strengths.**
- H12 and C2-A03 dispositions are exactly right given `.nox/` contents: two floor envs (4.2, 6.0) and two current-pack envs (4.2, 5.2); current-pack 6.0 absent.
- `--check-final` rejecting stale hashes / zero collection / skipped required cases is the correct repudiation control for a plan that reuses plan-07 evidence conditionally.
- The AST-based nox selection test avoids importing nox and is a real check on A15.

**Concerns.**
- LOW — The verification block runs `modal-focus.cjs` with `CV_FOCUS_PYTHON=.nox/tests-3-12-django-5-2/bin/python`, whereas that script defaults to the 6.0 floor env (`modal-focus.cjs:81`). Either is a supported series; just record which one was used so the "preservation" evidence names its runtime.

**Suggestions.**
- None blocking.

**Risk: LOW–MEDIUM.** Fully gated on 06/07; halted-summary contract preserves truthfulness.

---

## Round 2 (cec0b2f) concern closure — verification against source

| ID | Verdict | Evidence |
|---|---|---|
| C2-A01 | **Signed off.** | `base.py:111,169-170` default False + E251; `views/form.py:20,52`, `views/delete.py:55` True; `WorkflowView(CustomFormView)` at `crud_views_workflow/lib/views.py:18` inherits True. Plans 05/07 now scope modal HTTP to custom/delete/workflow and keep create/update E251. |
| C2-A02 | **Signed off.** | Library helpers at `form.py:43-50,136-146` are the only standalone-affected ones; 01-01 records before/after, 08-01/02 publish the caller-owned wrapper recipe and Breaking pairing. |
| C2-A03 | **Signed off.** | `.nox/crispy_floor-3-12-django-4-2` exists (Django 4.2.30, crispy 2.0, pack 2023.10 dist-info); 03-03 and 09-01 add it as a distinct gate. |
| C2-A04 | **Signed off.** | `presentation.cjs:2-5` / `presentation_server.py:7-9` default 8145, reject 8143/8144; 07-01 documents sequential sharing and tests the live-listener collision. |
| C2-A05 | **Signed off, with one inventory gap (LOW).** | Named overrides exist at `conditional/views.py:133-136`, `test_fragment_authorization.py:178-196`, `conditional_formsets_server.py:140,259`; a third `test_fragment_authorization.py:1584-1586` is omitted from the deferral row. |
| C2-A06 | **Signed off (conditionally).** | Plan 07 migrates only existing copies and treats absence as success; existence at `885dfc7` unverifiable from this sandbox, but the rule is correct regardless. |
| C2-A07 | **Signed off.** | 08-02 `read_first` cites plan 01 / `01-ownership-evidence.md`. |

**H06 verdict.** The *source-acquisition* component is closed at the planning level: plans 06/07/09 now name one monorepo root, exact component subpaths, the two README suites, sibling isolated copies preserving the `../django-crud-views` editable layout, and a separately verified Python ≥3.14 / Django 6.1 runtime that is explicitly *not* core support-matrix evidence. The in-repo records agree with each other (`SOURCE-AUDIT.md:163-172`, research addendum, `VALIDATION.md:23`). I give reviewer sign-off on the plan content. I could not independently inspect the checkout (sandbox limit), so the identity claim itself is an open question for the executor's first capture, which the plan already re-validates by hash. The remaining "H06 — execution evidence" row is future execution work (baseline, replay, browser runs), **not a plan defect**, and is correctly fail-closed with halted summaries. No HIGH plan defect remains.

Prior H01–H05/H07–H12: no current evidence warrants reopening. H02's fixture inventory was re-checked exhaustively above and is complete.

---

## Final current ledger

**Unresolved HIGH plan defects:** none.

**Actionable MEDIUM:** none.

**Actionable LOW (new this cycle; not yet in tasks or deferrals):**

1. `docs/reference/theme.md:310` ("literal Bootstrap CSS") becomes false after plan 04 in wave 1 and is not named in 04-01 or 08-01. Add it to one of them.
2. Plan 07 should state that the theme harness must not inherit `presentation.cjs`'s `4.2|5.2|6.0` Django-series assertion (`PATTERNS.md:201`), since the companion runs Django 6.1. Optionally use `CV_THEME_PYTHON` instead of overloading `CV_FOCUS_PYTHON`.
3. Plan 05's C2-A05 deferral row omits the third retained override at `tests/test1/test_fragment_authorization.py:1584`.
4. Plan 01-03: name the empty-`Layout()` helper explicitly in the falsey-helper matrix.
5. Plan 02-02: add the two-level fallback case (malformed owner map → malformed setting → theme value) to prove the A17 path end to end.

**Already covered in tasks (no action):** companion import-shadowing (06-01/07-01 origin probes); H12 current-pack 6.0 limit (09-01); floor 4.2 gate (03-03/09-01); halted-summary contract (06-02/09-02).

**Open question (not a finding):** independent confirmation of `../tabler-test` at `885dfc7` with the stated layout and `pyproject` constraints; blocked by sandbox, re-validated by hash at plan 06 execution.

**Overall risk: LOW–MEDIUM.** Product plans 01–05 and 08 are verified against source and executable now. Plans 06/07/09 are correctly gated on a companion runtime that this environment does not demonstrably have; that is an environmental prerequisite the plans handle truthfully, not a defect.
