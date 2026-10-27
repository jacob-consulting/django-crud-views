---
phase: "06"
reviewers: ["fable-review", "grok-review", "gemini-review"]
reviewed_at: "2026-10-27T15:43:30.459762+00:00"
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

> Grok and Gemini share the OpenCode adapter; any agreement between them is cross-model, not cross-tool.

# Cross-AI Plan Review — Phase 06

<!-- gsd:plan-revision-conflicts:begin -->
## Plan-Revision Conflicts

<!-- gsd:plan-revision-conflicts:end -->

## Reviewer execution record

Configured default reviewers were invoked unchanged and concurrently through `review-lane invoke`: Fable/Claude and Grok/Gemini/OpenCode. No reviewer was substituted. No prompt-budget trimming was configured. Fable and Grok completed real source-cited reviews with no leading evidence discount. Gemini attempt1 reached the660000ms outer timeout, returned no assistant text (stop reason tool-calls,82 output tokens), and produced an ETIMEDOUT stub despite the wrapper returning ok=true. That stub is not a reviewer verdict. One retry used the same model, high effort, prompt and canonical runner with a temporary in-memory timeout override to1200000ms; no project/runtime/config files changed. No third attempt occurred.

| Identity | Final runner outcome | Coverage | Discount |
|---|---|---|---|
| fable-review | ok=True; stubbed=False | complete 9/9 | None |
| grok-review | ok=True; stubbed=False | complete 9/9 | None |
| gemini-review | ok=True; stubbed=False | complete 9/9 | None |

3 real reviewer outputs contribute to consensus. Failure stubs never count as corroboration. The consensus gate applies to newly raised HIGHs; source-confirmed existence claims and non-discounted judgment claims retain weight. Repeated concerns are counted once. The two final current-concern sections and CYCLE_SUMMARY are intentionally returned to the orchestrator, not embedded as machine fields here.

Gemini retry completed with a real review; its initial timeout remains preserved as a separate attempt.


## Claude Review (fable-review)

# Cross-AI Plan Review: Phase 6 (Form-button leaf), plans 06-01 … 06-09

Reviewed read-only against the working tree of `introduce-gsd` (HEAD `007c21e`), the installed `django-crispy-forms 2.6` / `crispy-bootstrap5 2026.3`, and git refs. No repository files were modified. Three findings cut across several plans and are stated once here, then referenced:

- **X-1 (HIGH, 06-01):** the stated execution precondition cannot be satisfied. `main` and `origin/main` are both `38b0100`, which is also the merge base with `introduce-gsd` (183 commits ahead). `git grep default_label_mode main -- src/crud_views/lib/view/label_mode.py` and `git grep FORM_KINDS main -- src/crud_views/lib/button_classes.py` both return nothing. Phases 1–5 exist only on `introduce-gsd`. As written, 06-01 Task 1 halts the whole phase.
- **X-2 (HIGH, 06-02 → 06-08):** adding `"form"` to `LOCATIONS` / `LABEL_MODE_DEFAULTS` in wave 2 breaks two existing tests whose fixes are scheduled in waves 3 and 7 (`tests/test1/test_label_mode_docs.py:126` and `tests/test1/test_action_label_mode_config.py:278`), so the "full suite green after each wave" sampling rule in 06-VALIDATION.md is unattainable between waves 2 and 7.
- **X-3 (HIGH, 06-07 → 06-09):** the only Node on this machine is 20.20.2 (`~/.nvm/versions/node/v20.20.2/bin/node` and `/usr/bin/node`), while the lock pins `jsdom 30.1.2` (engines `^22.22.2 || ^24.15.0 || >=26.0.0`) and `vitest 5.0.3` (`^22.12.0 || ^24.0.0 || >=26.0.0`), see `package-lock.json:32-50`. The installed `node_modules` is jsdom 29.1.1 / vitest 4.1.10. 06-07 Task 1 forbids using that environment as acceptance, and 06-09's `npm test` gate requires "runtime/packages match 06-07's lock-backed evidence". Without an explicit fallback the JS gate can never be declared passed.

---

## 06-01

**Summary.** The plan correctly makes the design spec and before-change goldens a gate, and its reading of the crispy render path is accurate. Its hard precondition, however, is already known to be false (the plan itself records "local main was 38b0100 and did not contain Phases 1/2"), and it instructs the executor to stop rather than offering any resolution path. Task 2 also builds on a payload assertion that does not exist in the suite.

**Strengths.**
- The spec contents the plan demands match real hazards I could reproduce from source: `BaseInput.render` compiles the value as a Django template and mutates the instance (`.venv/.../crispy_forms/layout.py:255`), and pushes `{"input": self}` onto the shared context without popping (`layout.py:257`). The helper-input path bypasses the adapter entirely because `bootstrap5/inputs.html:9` includes `baseinput.html` directly.
- "Unrelated goldens stay byte-identical" is verifiable: the existing `form_frame` goldens render a plain `NameForm` without a helper (`tests/test1/test_form_frame.py:37-40`), so they contain no buttons, and no file under `tests/test1/golden/` contains `type="submit"` or `type="reset"`.
- Baseline-first ordering mirrors Phases 4 and 5 (`f6982bf`, `be7daa5`), and the `tag()` regex helper at `tests/test1/test_crispy_buttons.py:21-27` is a ready pattern for raw-control extraction.
- Workflow and filter endpoints exist for Task 3 (`tests/test1/test_workflow.py:229`, `tests/test1/test_filter.py:12`).

**Concerns.**
- **HIGH (X-1):** Task 1's precondition "authoritative main contains completed Phases 1 and 2" is false today, and the plan's only instruction is "stop execution". `.planning/STATE.md:91` records that the user chose to stay on `introduce-gsd` for Phase 1, so this is the project's working convention, not an accident. Either the precondition must be restated as "the executing branch contains the Phase 1/2 symbols" or a maintainer merge/PR of `introduce-gsd` into `main` must happen before this phase. The plan should say which.
- **MEDIUM:** Task 2 says "Add the existing delete payload assertion … the established `{"delete": "Delete"}` value". No such assertion exists: `tests/test1/test_crud.py:63` posts `{"confirm": True}`, as do `tests/test1/test_delete.py:84,173,186`. The source plan only says "`test_delete`, `test_cancel_origin` green" (`superpowers/plans/2026-10-24-concept-review-followups.md:211-212`); the `{"delete": "Delete"}` wording was introduced in ROADMAP.md. The task should define the new assertion (rendered control has `name="delete"` / `value="Delete"`, and a POST that includes `delete=Delete` still deletes), not reference an existing one.
- **LOW:** Task 1's verify command only runs the pre-existing crispy and button-data shards; it does not check that the spec file contains the named contracts. The `fails_when` text promises that, the automated command does not.

**Suggestions.**
- Replace the precondition with a symbol check on the executing branch (`default_label_mode` in `label_mode.py`, `FORM_KINDS` in `button_classes.py`), and add a separate "merge to main" note to the phase acceptance instead of a halt.
- Rewrite Task 2's payload bullet as a new assertion, and keep the extraction helper tolerant of both `<input …>` and `<button …>…</button>` from the start so 06-02 Task 3 only flips an expectation.
- Add a cheap spec-presence check (headings or key phrases) to Task 1's automated verify.

**Risk Assessment: HIGH** (guaranteed halt unless the precondition is restated or main is updated first).

---

## 06-02

**Summary.** This is the right first product tracer and its mechanism claims are accurate against crispy 2.6. The plan is undermined by two cross-plan test breakages it causes but does not own (X-2), one silent behavior change for non-form slots, and a missing name-normalization detail in the contract.

**Strengths.**
- The `template` precedence is implementable exactly as D-05–D-08 require: `BaseInput.__init__` already accepts `template=` and does `self.template = template or self.template` (`layout.py:234,247`), `TemplateNameMixin.get_template_name` handles `%s` (`layout.py:18-25`), and `_TableClassMixin` sits first in the MRO (`src/crud_views/lib/crispy/buttons.py:21-30`) so a class-level `template` on it beats `BaseInput.template`.
- Generated IDs come from `BaseInput.__init__` (`layout.py:237-241`), so `submit-id-submit`, `button-id-reset`, `submit-id-delete` are preservable without touching the leaf.
- The plan correctly refuses `BaseInput.render` (template evaluation + instance mutation, `layout.py:255-257`) and correctly targets the SafeString trap (Django's `SafeString.__str__` returns itself, so `str()` does not strip the marker).
- The early `form` branch before `card = location == "card"` (`src/crud_views/lib/view/button_data.py:67`) is the right cut; the action normaliser reads `ctx["cv_url"]`/`ctx["cv_oid"]` at lines 139-141 and would KeyError for forms.

**Concerns.**
- **HIGH (X-2):** `tests/test1/test_label_mode_docs.py:126` asserts the settings.md table cell literal-evals to `dict(LABEL_MODE_DEFAULTS)`; `docs/reference/settings.md:78` currently says `{"context": "icon", "list": "icon", "card": "both"}`, and settings.md is only in 06-08's file list. Likewise `tests/test1/test_action_label_mode_config.py:278` hard-codes `E108_LOCATIONS = "['card', 'context', 'list']"` and the E108 message at `src/crud_views/lib/settings.py:159` prints `sorted(LOCATIONS)`; that test file is only in 06-03. Both fail the moment Task 1 lands.
- **MEDIUM:** "invalid caller kind/type raises ValueError" changes today's contract: `_TableClassMixin` accepts any slot string and `get_button_class` returns `""` for an unknown key (`button_classes.py:148-149`). A project doing `Submit(..., slot="formset:control")` renders fine today and would raise at render after this plan. Either list it as Breaking in 06-08 or degrade (unknown slot → label mode, classes from that slot).
- **MEDIUM:** FORM-06 promises the same `name`, but `baseinput.html:2` slugifies multi-word names (`{% if input.name|wordcount > 1 %}{{ input.name|slugify }}`). The spec text in 06-01 says "positional name/value win" but never mentions slugification; the leaf must replicate it or the plan must call the change out.
- **LOW:** `render_field` wraps only `extra_context` keys in `KeepContext` (`crispy_forms/utils.py:55-65`); the `input` key pushed by any legacy `BaseInput.render` earlier in the same layout survives into later leaves. The plan's "strip inherited input aliases" is therefore necessary, not just hygiene; worth stating why in the spec.

**Suggestions.**
- Move the `settings.md:78/90` literal update and the `E108_LOCATIONS` constant update into Task 2's file list (they are one-line edits), so the suite is green at the end of wave 2.
- Decide the non-form-slot policy explicitly and test it.
- Add `cv_name` slugification (or its explicit removal) to the normalisation contract and the golden comparison.

**Risk Assessment: HIGH** (ordering defect makes every intermediate wave red; the rest is MEDIUM).

---

## 06-03

**Summary.** The whole-map resolver work is a faithful copy of an existing, verified pattern. The owner-recovery task is correctly identified as the hard part, but the plan's description of how to find the "current helper view" in `Context.dicts` is positional, and crispy's own pushes make position unreliable.

**Strengths.**
- Every integration point named exists with the claimed semantics: `cv_first_inline_keys` returns the first non-`None` layer (`src/crud_views/lib/view/base.py:263-272`), settings fields and the E106 loop (`settings.py:67-68, 128-141`), the ViewSet validator (`viewset/__init__.py:105-111`), and the `ValueError` on unknown location in `cv_get_action_label_mode` (`base.py:329`).
- The research's shadowing hazard is real: `BasicNode.get_render` copies the context and pushes `response_dict` (`crispy_forms_tags.py:110-112`), and `FormHelper.get_attributes` dumps every non-underscore instance attribute into it (`helper.py:340-346`), so `ListViewFilterFormHelper.view` (`list.py:68`) lands in the top dict even when `None`.
- "Do not re-read `form.helper`" is correct: `CrispyFormMixin.helper` is a property that builds a fresh `FormHelper` on every access (`src/crud_views/lib/crispy/form.py:41-48`).

**Concerns.**
- **MEDIUM:** the plan says "obtain the current helper owner from … crispy's visible helper view overlay" and "recover the nearest non-None lower page view by inspecting Context.dicts". Which dict is the overlay is not fixed by position: `FormActions.render` pushes `{"formactions": …, "fields_output": …}` after rendering its children (`crispy_forms/bootstrap.py:306-311`) and that push persists, so a second `FormActions` or any button after one sees a different top dict. The spec needs a marker to identify crispy's overlay (its `get_response_dict` always sets `is_formset`, `template_pack`, `form_attrs`, `crispy_forms_tags.py:153-175`) rather than "the dict above the page".
- **MEDIUM:** nested `{% crispy %}` inside formsets (`src/crud_views/templates/crud_views/formsets/formset.html:42`) stacks several overlays; the Cartesian test matrix in Task 2 should include a formset row form, not only a single embedded form.
- **LOW:** a `view` key with `None` in the *page* context (the `form_frame` tests render with `"view": None`, `test_form_frame.py:39`) must be treated as "no owner", consistent with D-10. The plan says None overlays fall through; make sure the page layer is included in that rule.

**Suggestions.**
- Name the overlay marker in the spec and test it with two `FormActions` in one layout.
- Add a formset case to the owner matrix.

**Risk Assessment: MEDIUM.**

---

## 06-04

**Summary.** Registry and class-key work is small and well grounded; the icon precedence design (sentinel for `icon=`) is sound. The plan's own verify command cannot pass as scoped because it excludes the test file that pins the default key set.

**Strengths.**
- `DEFAULT_ICONS` / `BOOTSTRAP_ICONS` indeed lack `save`, `cancel`, `filter-reset` (`src/crud_views/lib/icons.py:14-89`); `delete`, `filter`, `workflow` exist.
- `icon_host_keys()` → `get_icon_host_class(location, …)` → `get_button_class(location, "icon-host")` (`button_data.py:41-49`, `button_classes.py:152-165`) means `form:icon-host` is genuinely required; today only `context/list/card/menu:icon-host` exist (`button_classes.py:91-94`).
- `{% cv_button_class "form" cv_key cv_label_mode %}` already resolves `form:<kind>:<mode>` through the mode-key fallback (`button_classes.py:138-149`, tag at `templatetags/crud_views.py:525-528`).
- Slot-from-kind independence matches the existing `CrispyDeleteForm.get_delete_button` merge order (`form.py:130`) and the test that overrides the slot (`test_crispy_buttons.py:62-73`).

**Concerns.**
- **MEDIUM:** Task 1 runs `tests/test1/test_button_classes.py` but keeps the task "within its declared five files". That file hard-codes `EXPECTED_KEYS` and asserts `len(EXPECTED_KEYS) == 71` and set equality with `DEFAULT_BUTTON_CLASSES` (`test_button_classes.py:21-91`), and parametrises utility slots at lines 104-119. Adding two keys fails it. Add the test file to Task 1.
- **LOW:** `icon=` as a constructor keyword flows into `**kwargs` → `flatatt` (`layout.py:248`) and would serialize as an `icon="save"` attribute unless consumed before `super().__init__`; the plan says consume, but the mixin currently forwards `**kwargs` unchanged (`buttons.py:18`).
- **LOW:** `filter-close` already maps to `fas:filter-circle-xmark` / `bi:x-circle`; choose `filter-reset` glyphs that stay distinguishable from the toggle's close state.

**Suggestions.** Add `tests/test1/test_button_classes.py` to Task 1's files and update `EXPECTED_KEYS` with the count change (71 → 73) in the same commit as `buttons.md`.

**Risk Assessment: LOW–MEDIUM.**

---

## 06-05

**Summary.** The filter-helper lifecycle plan is the most carefully reasoned of the set and its constraints match source. Two crispy mechanics deserve explicit treatment: empty `Layout` objects are falsy, and helper instance state leaks into the template context unless underscore-prefixed.

**Strengths.**
- Constructor wiring is exactly as claimed: `filterset.form.helper = self.formhelper_class(request=self.request, view=self)` (`src/crud_views/lib/views/mixins.py:319`) and `def __init__(self, view, request, form=None)` (`list.py:65`).
- `FormHelper.__init__(form)` replaces the layout whenever a form is passed (`helper.py:208-214`), confirming the "deep-copy, do not pass form" guidance; documented subclasses use class-level `layout` (`tests/test1/app/views.py:288-289`, `docs/reference/list_view.md:143-144`, example `library/views.py:48-49`).
- Keeping `Hidden` controls on `helper.inputs` (`list.py:77-87`) is consistent with D-01.
- `list.filter.js:57` binds by id, so a nested icon click bubbles to `#filter-button-reset` unchanged.

**Concerns.**
- **MEDIUM:** `BasicNode.get_render` calls `render_layout` only `if helper and helper.layout` (`crispy_forms_tags.py:116`), and `LayoutObject.__len__` returns `len(self.fields)` (`layout.py:38-39`), so `Layout()` is falsy. The plan's "truthy Layout instance" is correct but should say how (a placeholder element or a `__bool__` override on a private subclass); a no-layout helper otherwise silently renders `uni_form.html` with no actions.
- **MEDIUM:** `get_attributes` copies every non-underscore instance attribute into the crispy context (`helper.py:340-346`). New state such as an "actions appended" flag or a per-instance layout copy must be underscore-prefixed, or it appears as a template variable (and a non-underscore `view` is precisely what causes the shadowing in 06-03).
- **LOW:** after Apply/Reset move into the layout, `inputs.html:1-13` still wraps the remaining hidden inputs in `<div class="mb-3"><div class="">…</div></div>` (the `sort` hidden is always added, `list.py:77-78`), leaving an empty margin block below the buttons and moving the hidden inputs after them in DOM order. The filter golden diff should expect this; it is a small visual change worth a sentence in the migration note.

**Suggestions.** Name the truthy-layout mechanism and the underscore rule in the spec; add an assertion that the crispy context contains no new non-underscore helper keys.

**Risk Assessment: MEDIUM.**

---

## 06-06

**Summary.** Diagnostics reuse the real owners (E210 in `label_mode.py`, E211/W291 in `action_menu.py`, W292 in `buttons.py`, E106 in `settings.py`) and the plan correctly scopes static reach. The cross-tier W291 "deterministic dedup" is the one piece of new machinery that is not needed.

**Strengths.**
- All cited owners and IDs exist: `label_mode_check` E210 (`label_mode.py:44-51`), `cv_label_mode_checks` E211/W291 (`action_menu.py:46-72`), `cv_icon_mode_checks` W292 with its narrow `except ValueError` (`buttons.py:387-440`), wiring at `base.py:186-197`, E106 loop at `settings.py:128-141`.
- Static-only inspection is realistic: delete views set `form_class = CrispyDeleteForm` statically (`tests/test1/app/views.py:122,340,…`), the workflow view requires `form_class` via E230 (`crud_views_workflow/lib/views.py:23,46`), and the "hook retains package implementation" test mirrors `type(button).get_context is not ContextButton.get_context` at `buttons.py:411`.
- Keeping `cv_viewset is not None` gating (as W292 does, `base.py:195-197`) is implied and correct.

**Concerns.**
- **MEDIUM:** W291 for "ViewSet/settings-selected form maps … with deterministic dedup" contradicts the documented rule at `action_menu.py:47-50` (only the view's own attribute is checked for unknown keys) and requires process-level dedup state. Because `FORM_KINDS` is finite and global, unknown kinds are better reported where those layers are already validated: the ViewSet Pydantic validator (`viewset/__init__.py:105-111`, raises at construction) and the settings E106 path (one message, no dedup). Drop the cross-tier W291.
- **LOW:** "non-strict logs one warning per render" in `cv_button_data`'s form branch differs from the once-per-process register used by `_invalid_label_mode` (`label_mode.py:28-30, 74-81`); the existing action path also logs per render (`button_data.py:106-110`), so this is consistent, but the test suite's `CRUD_VIEWS_STRICT=True` (`conftest.py:41`) means non-strict cases need explicit `override_settings`.

**Suggestions.** Restrict W291 to `cv_form_actions_label_mode` on the view; validate ViewSet/settings maps at their existing owners.

**Risk Assessment: MEDIUM.**

---

## 06-07

**Summary.** The JS and floor validation is where the roadmap's open investigations get executed, and the plan is honest about environment gates. But the gate it sets for the locked JS environment cannot be met on this machine, and the plan does not say what counts as acceptance when it is not.

**Strengths.**
- Native `SubmitEvent` with `submitter` already works in the installed jsdom: `tests/js/modal.test.js:202` dispatches `new SubmitEvent("submit", {… submitter: button})`.
- The production seams the plan intends to leave untouched are the right ones: `new FormData(form, submitter || undefined)` (`modal.js:82`), `closest("[data-cv-cancel-url]")` (`viewset.js:40`), id-bound reset (`list.filter.js:57`). Nested icon/text clicks bubble to these naturally.
- The nox pattern is simple to extend (`noxfile.py:6-19`), and the plan preserves the matrix and skip logic.

**Concerns.**
- **HIGH (X-3):** no Node ≥ 22 is available (`which -a node` lists only v20.20.2 and `/usr/bin/node`; I could not list other nvm versions from this sandbox, but PATH resolution shows 20.20.2). Task 1 both forbids using the existing environment as acceptance and forbids changing declarations. The plan needs a defined fallback: treat the pre-existing lock/runtime drift as a recorded environment issue, run the suite on the environment Phases 3–5 used, and keep the lock-backed run as a follow-up, or add an explicit, approved "install Node 22 via nvm" step.
- **MEDIUM:** `FormData(form, submitter)` second-argument support in jsdom 29 is inherited evidence only (06-RESEARCH.md "Assumptions Log" A2). Task 1 should assert it directly (`new FormData(form, button).get(button.name)`), which it does implicitly, but should treat a failure as a finding, not a mock opportunity.
- **LOW:** Task 3 says "constrain … in the same resolver transaction"; the current session installs Django and the project in two `session.install` calls (`noxfile.py:13-14`). One `session.install("django~=X.0", "django-crispy-forms==2.0", "crispy-bootstrap5==2023.10", ".[…]")` does what the plan wants with uv; worth writing out. Whether crispy 2.0 / bootstrap5 2023.10 import cleanly on Django 6.0 is unverified here.

**Suggestions.** Add an explicit decision branch to Task 1 for "no compatible runtime"; record the Node 20 run as the baseline the project has actually been gating on.

**Risk Assessment: MEDIUM–HIGH** (environment, not design).

---

## 06-08

**Summary.** Documentation work is well targeted and the executable-recipe pattern already exists (`tests/test1/test_pagination_docs.py` with `_section` / `TEMPLATE_FENCE`). The doc-contract tests from Phase 1 constrain wording tightly, and the plan should name the rows it must extend to keep them green.

**Strengths.**
- `test_label_mode_docs.py` already dictates the settings.md shapes: the `CRUD_VIEWS_LABEL_MODE_DEFAULTS` row must literal-eval to the live defaults (line 126) and the knob table rows are checked by exact first cell (lines 145-159), so extending them is mechanical.
- Example settings have no label-mode entry yet (`examples/bootstrap5/project/settings.py:125-142`), so `{"form": "both"}` is a clean addition.
- Keeping Breaking + migration in one commit matches `CLAUDE.md:105` and the Phase 5 precedent (`09549b2`).

**Concerns.**
- **MEDIUM:** Task 1 says "update its live default-key count from DEFAULT_BUTTON_CLASSES", but 06-04 Task 1 already changes `buttons.md:145` to 73. Two plans editing the same canonical sentence invites a merge/ordering mistake; 06-08 should only verify it.
- **LOW:** `_card_release_contract` requires exactly one Added bullet starting with "- `CRUD_VIEWS_LABEL_MODE_DEFAULTS` sets" (`test_label_mode_docs.py:368-369`); a new Added bullet with that prefix would break it. Also `settings.md:78` lists locations in prose ("`"context"`, `"list"`, `"card"`"), which the row check at line 128-129 reads; add `"form"` there, not only in the dict.
- **LOW:** the "merging with its existing configured locations" instruction in Task 3 is moot (no existing entry).

**Suggestions.** Remove the key-count edit from Task 1; add an explicit list of doc-test rows to extend (`settings.md` setting row, knob table form row, `action_menus.md` form resolution section, `buttons.md` leaf-contract row for `cv_label_mode`).

**Risk Assessment: LOW–MEDIUM.**

---

## 06-09

**Summary.** A sound closing plan: it demands observed evidence, keeps unresolved items visible, and separates human checks. Its automated gates inherit X-3 unless 06-07 defines the fallback, and one command path should be verified before execution.

**Strengths.**
- Gates mirror `.planning/PROJECT.md` quality gates and Phase 4/5 acceptance records; the plan already anticipates the known `ruff format --check` redness on planning files (`STATE.md:114`).
- Baseline ancestry and source-blob equality checks are the right proof for FORM-01.

**Concerns.**
- **MEDIUM (X-3):** `npm test` with "recorded runtime/packages match 06-07's lock-backed evidence" cannot be satisfied without the 06-07 fallback.
- **LOW:** I did not verify `examples/bootstrap5/manage.py` exists at that path; the `examples` nox session runs pytest from `examples/bootstrap5` (`noxfile.py:32-33`), so the check command is plausible but should be confirmed.
- **LOW:** the "unclassified classifier assumption" bookkeeping for FORM-01/02 adds no verification value; harmless but noisy.

**Suggestions.** Tie the JS gate wording to whatever 06-07 decides; confirm the example `manage.py check` path.

**Risk Assessment: LOW** (conditional on 06-07).

---

## Cross-plan assessment

**Dependency ordering.** The serial waves are correct for file ownership, but the test suite is red from wave 2 through wave 7 (X-2) because two one-line fixtures live in later plans. Moving `settings.md:78/90` and `E108_LOCATIONS` into 06-02 fixes it at no cost.

**Scope.** Nine plans and 22 tasks for one feature is heavy but defensible for the phase the roadmap calls "highest risk". Two items are over-engineering: cross-tier W291 dedup (06-06) and the repeated `T-06-SC` dependency-install threat row in every plan where no install happens.

**Security.** The escaping design is correct and well motivated by source (`layout.py:255`, SafeString semantics). The plans should add the non-form-slot policy (06-02) so a raise at render cannot be triggered by previously valid configuration.

**Missing.** No plan states the `name` slugification rule (06-02), the empty `mb-3` wrapper after the filter move (06-05), or a decision for the absent Node ≥ 22 runtime (06-07).

**Overall risk: HIGH** until three edits are made: restate the 06-01 precondition against the executing branch (or merge first), pull the two fixture updates into 06-02, and give 06-07 an explicit no-runtime fallback. With those, the remaining risk is MEDIUM and concentrated in the crispy context-overlay recovery (06-03) and the filter-helper lifecycle (06-05), both of which the plans already target with real-render tests.


---


## OpenCode Review (grok-review)

I'll review all nine Phase 6 plans against the source, starting with the contracts they depend on.
Planning files aren't where the prompt expected. I'll locate the source the plans cite and read those contracts directly.
The cited contracts exist. I'll read the button, form, and check implementations the plans depend on.
## 06-01

**Summary:** The gate is real and correctly blocking. `origin/main` is `38b0100` and does not contain `FORM_KINDS` or `default_label_mode`; those contracts exist only on the current branch. The spec-first and baseline-first split matches the crispy hazards this phase has to avoid.

**Strengths:**
- Stopping unless authoritative `main` has Phases 1 and 2 matches the repo: `git grep FORM_KINDS origin/main` exits 1, while `src/crud_views/lib/button_classes.py:210` and `src/crud_views/lib/view/label_mode.py:84` exist here.
- Not calling `BaseInput.render` is required. Installed crispy compiles `self.value` as a `Template` and injects `input` (`crispy_forms/layout.py` `BaseInput.render`).
- `add_input()` never hits adapter `render()`. `bootstrap5/inputs.html:9` includes `baseinput.html` directly.
- Helper `view=None` does overlay the page view: `FormHelper.get_attributes` copies every public instance attribute, and `ListViewFilterFormHelper` sets `self.view` at `src/crud_views/lib/views/list.py:68`.

**Concerns:**
- **MEDIUM:** The "established `{"delete": "Delete"}` POST" does not exist. `tests/test1/test_crud.py:63` posts `{"confirm": True}`. `DeleteView.post` (`src/crud_views/lib/views/delete.py:199`) never reads a `delete` button. Adding that assertion to the current test fails.
- **LOW:** Two baseline commits are fine, but task 2's verify does not include workflow/filter, so a partial baseline can look done.

**Suggestions:**
- Assert the rendered control's `name`/`value`, and leave `test_crud.py:63` unchanged.
- Record `origin/main` SHA in the spec only after `git grep` shows both Phase 1 and Phase 2 symbols.

**Risk Assessment:** MEDIUM. The design gate is right; the delete-payload claim is not.

## 06-02

**Summary:** The tracer is aimed at the real layout path, and bypassing value templating is the correct break. Adding `"form"` to `LOCATIONS` has side effects this plan does not own, so its own shard can pass while the suite is already red.

**Strengths:**
- Early form branch is necessary. `cv_button_data` rejects unknown locations at `src/crud_views/lib/view/button_data.py:58` and then requires action fields such as `cv_url` at `:139`.
- `set(LABEL_MODE_DEFAULTS) == LOCATIONS` is pinned at `tests/test1/test_label_mode.py:67`. Updating that file is in scope.
- `tests/test1/test_crispy_buttons.py:21-27` only matches `<input>`. The plan updates those assertions for layout buttons and leaves filter inputs alone until 06-05.
- Template precedence matches installed crispy: `self.template = template or self.template`, and `%s` is applied only when present (`BaseInput.get_template_name`).

**Concerns:**
- **HIGH:** `"form"` in `LOCATIONS` immediately breaks tests this plan neither edits nor runs. `tests/test1/test_action_label_mode_config.py:278` pins `['card', 'context', 'list']`, and `:323` expects `{"form": "both"}` to be E108. `tests/test1/test_button_classes_templates.py:214-217` renders `action.html` for every `LOCATIONS` entry; `form` has no variant key, so `styled` is empty and `:225` fails. `tests/test1/test_label_mode_docs.py:126` literal-evals the settings table against `LABEL_MODE_DEFAULTS`.
- **MEDIUM:** `css_class` is already folded into `field_classes` by `BaseInput.__init__` after `buttons.py:17` sets the table classes. Passing `self.field_classes` into the leaf and also calling `cv_button_class` duplicates classes. `test_crispy_buttons.py:35` currently forbids `btn btn btn-secondary`.
- **MEDIUM:** `viewset.js:40` listens for `[data-cv-cancel-url]`. A context field `cv_cancel_url` does nothing unless the leaf emits that attribute. Cancel today is `data_cv_cancel_url` at `src/crud_views/lib/crispy/form.py:78`, which crispy turns into `data-cv-cancel-url`.
- **MEDIUM:** `slot` is a real HTML attribute. The reserved-attribute list omits `slot` and `template`. Leaking `slot="form:submit"` changes shadow-DOM slot assignment.

**Suggestions:**
- In this plan, update the E108 pin, exclude `form` from the action-leaf loop (use `VARIANT_LOCATIONS`), and either update `settings.md` or defer the `LABEL_MODE_DEFAULTS` change until the docs test is in the same commit.
- Capture `css_class` before `super().__init__` and do not re-append table classes.
- Emit `data-cv-cancel-url` only for cancel, and strip `slot`, `template`, `css_id`, and `css_class` before attribute serialization.

**Risk Assessment:** HIGH. The render design is sound; the `LOCATIONS` blast radius is not scheduled.

## 06-03

**Summary:** Whole-map selection matches the existing resolver, and the owner-before-flatten rule matches a reproduced crispy overlay. The plan does not say that its verify file is already broken by 06-02.

**Strengths:**
- `cv_first_inline_keys` (`src/crud_views/lib/view/base.py:263-272`) returns the first non-`None` map, so `{}` suppresses lower maps. List lookup uses membership, not `dict.get`, at `:323-328`. Copying that for form is the right semantic.
- `cv_get_action_label_mode` currently raises unless location is `context` or `list` (`base.py:329`). Adding `form` without the context-button/`target_default` chain is required.
- `CrispyFormMixin.helper` is a property that builds a new helper on every access (`src/crud_views/lib/crispy/form.py:41-48`). Re-reading it during `render()` would build a second action group. The plan forbids that.
- ViewSet validation is a decorator on the two existing maps only (`src/crud_views/lib/viewset/__init__.py:105`). The new field must be added there, and the plan owns that file.

**Concerns:**
- **HIGH:** Task 1 runs `tests/test1/test_action_label_mode_config.py`, which still treats `form` as an unknown floor key (`:323`) and embeds the three-location list (`:278`). The action never mentions those lines.
- **MEDIUM:** E106 is a hand-written loop at `src/crud_views/lib/settings.py:128-131`, not a side effect of adding a field. 06-03 can add `form_actions_label_mode` and still leave a malformed setting unchecked until 06-06.
- **LOW:** `CheckUnknownAttributes` will accept `cv_form_actions_label_mode` only if it is declared on `CrudView`. That is in this plan's `base.py` edit, but it is easy to put the resolver on a mixin the check does not see.

**Suggestions:**
- Make the E108 string and the `{"form": "both"}` case an explicit task step before any new map tests.
- Add the new setting to the E106 loop in this plan, not only in 06-06.

**Risk Assessment:** MEDIUM. Resolution design matches source; the inherited E108 pin will fail the plan's own verify.

## 06-04

**Summary:** Utility keys and semantic icons fit the existing class grammar and icon registries. The plan's own class-table test cannot pass with the files it is allowed to edit.

**Strengths:**
- `save`, `cancel`, and `filter-reset` are absent from both registries (`src/crud_views/lib/icons.py:14-88`). `delete`, `filter`, and `workflow` already exist, so the mapping table is partly there.
- `form:hidden-label` / `form:icon-host` are two-segment utility keys. W362 mode keys go through `_action_key_parts` (`src/crud_views/lib/button_classes.py:223-226`), which only accepts `FORM_KINDS`. `form:hidden-label:icon` stays unknown. Adding them does not widen the grammar.
- `get_icon_host_class` formats `location:icon-host` (`button_classes.py:152-163`). A `form` location key is the right extension.
- Slot-versus-name is already how delete styling works: `CrispyDeleteForm.get_delete_button` forces `slot="form:delete"` while the name stays `delete` (`src/crud_views/lib/crispy/form.py:123-130`).

**Concerns:**
- **HIGH:** `tests/test1/test_button_classes.py:89-91` asserts `len(EXPECTED_KEYS) == 71` and `set(DEFAULT_BUTTON_CLASSES) == EXPECTED_KEYS`. The new keys are not in `EXPECTED_KEYS` (`:21-76`). The plan runs that file and does not list it in `files_modified`. Updating only the sentence in `docs/reference/buttons.md:145` does not satisfy the set equality.
- **MEDIUM:** `buttons.md:145-146` says the icon-host row stands for four keys. Adding `form:icon-host` makes that arithmetic wrong even if the integer becomes 73.
- **LOW:** `tooltip.js:6` lists tooltip locations and omits `form`. The adapter ignores the token (`adapters.js:25`), so behavior is fine; the comment and any later stability list will drift.

**Suggestions:**
- Add `tests/test1/test_button_classes.py` to this plan and extend `EXPECTED_KEYS` in the same commit as the two defaults.
- Add the two documentation rows and change the "four" icon-host count in that same commit.

**Risk Assessment:** HIGH. The feature is small; the completeness test makes the written file list unexecutable.

## 06-05

**Summary:** Moving stock filter actions onto a layout is the only path that calls adapter `render()`. The lifecycle rules match crispy's actual dispatch, including the example's shared class layout.

**Strengths:**
- `ListViewTableFilterMixin.get_filterset` calls `formhelper_class(request=..., view=...)` with no form (`src/crud_views/lib/views/mixins.py:319`). Keeping that signature is required.
- `FormHelper.__init__` replaces `self.layout` whenever a form is passed. Not passing `form` is the only way to keep `AuthorFilterFormHelper.layout` (`examples/bootstrap5/library/views.py:48-49`) and `PublisherFilterFormHelper.layout` (`tests/test1/app/views.py:288-289`).
- If `helper.layout` is truthy, crispy sets `form.form_html` and `display_form.html` renders only that. A button-only layout would drop fields. Populating fields inside `render_layout` before `layout.render` is the right fix.
- Hidden controls can stay on `helper.inputs`. `whole_uni_form.html` includes `inputs.html` after the layout, so names and values survive even if they move below the buttons.
- `list.filter.js:57` binds `#filter-button-reset`. Preserving that id is necessary and sufficient for the current handler.

**Concerns:**
- **MEDIUM:** `render_layout` runs on every render of the same helper instance. Appending fields or actions in place duplicates them. The acceptance text says "once"; the action text says "append" without "rebuild or guard".
- **MEDIUM:** A truthy empty `Layout()` must exist before crispy's `if helper.layout` check, not only inside `render_layout`. Setting it only in the override never runs.
- **LOW:** Hidden inputs will render after the action group instead of beside the old inputs. Goldens must not treat position as part of the contract.

**Suggestions:**
- Rebuild the instance layout at the start of each `render_layout`, or set a per-instance initialized flag and test two renders of one helper.
- Assign the empty `Layout` in `__init__` when the class has no layout.

**Risk Assessment:** MEDIUM. The crispy constraints are understood; repeated-render mutation is the likely implementation miss.

## 06-06

**Summary:** Reusing E210/E211/W291/W292 is right, and not instantiating request-bound forms is mandatory. The proposed form-map split does not match the helper the plan says to extend.

**Strengths:**
- Existing map checks are `cv_label_mode_checks` (`src/crud_views/lib/view/action_menu.py:46-71`), wired from `CrudView.checks` at `src/crud_views/lib/view/base.py:193-194`. Settings use E106 (`settings.py:128-141`), not E210. The plan keeps that split.
- W292 already skips dynamic buttons and swallows floor `ValueError` so E108 still surfaces (`src/crud_views/lib/view/buttons.py:387-429`). Copying that narrow catch is correct.
- `CrispyFormMixin.__init__` requires `cv_view` (`form.py:37-39`). A check that constructs the form will crash `check_viewsets`. The plan forbids that.
- Runtime icon-only fallback already exists for actions at `button_data.py:97-110`. A form branch can reuse the strict/log policy without a new check id.

**Concerns:**
- **MEDIUM:** `is_label_mode_map` fails the whole map if any value is not a mode, and `cv_label_mode_checks` then emits one E211, not per-entry E210. The plan wants E210 for bad form-mode values. Reusing the helper will fail the new tests.
- **MEDIUM:** The E211 message hardcodes card/context attribute names (`action_menu.py:58-61`). Reusing it for `cv_form_actions_label_mode` produces a misleading diagnostic. W291's "not among this view's actions" is also wrong if `known_keys` is `FORM_KINDS`.
- **LOW:** Static reach that only inspects `form_class` misses helpers. `formhelper_class` lives on the mixin (`mixins.py:309`) and is often a subclass that inherits `get_form_actions`. The plan says to handle that; an executor who only walks `form_class` will never warn on filter buttons.

**Suggestions:**
- Write a form-specific checker with its own messages. Do not call `cv_label_mode_checks` and expect E210.
- Treat an inherited `get_form_actions` on the configured helper class as knowable, and skip the class if that method is overridden.

**Risk Assessment:** MEDIUM. Diagnostics are scoped correctly; the ID split will not fall out of the existing helper.

## 06-07

**Summary:** Browser coverage is aimed at the handlers that actually exist, and the crispy floor session is a real gap in `noxfile.py`. The automated verify line can still go green on the wrong Node runtime.

**Strengths:**
- `modal.js:82` already passes `submitter` to `FormData`. A real `<button type="submit">` is what that call needs. Nested icon clicks are already handled by `closest` in `viewset.js:40`.
- `list.filter.js:42-57` keeps `sort`/`order`/`dir` from the page query string and binds the reset id. Label-mode markup does not require a JS change if the id and attribute survive.
- `noxfile.py:6-19` installs extras with no crispy pin. A separate `crispy_floor` session is the right place to pin `django-crispy-forms==2.0` and `crispy-bootstrap5==2023.10` without moving the matrix.
- `format_html` in this repo is called with an argument (`src/crud_views/lib/icons.py:220`). Django 6 only removed the zero-argument form. The plan's investigation target is accurate.

**Concerns:**
- **MEDIUM:** `package.json:16` says `node >= 20`, while the lock's jsdom/vitest engines are newer. The verify command is `npm --prefix . test`, which uses whatever `node` is on `PATH`. A green run on Node 20 does not meet the plan's own acceptance text.
- **LOW:** `onReset` does not call `preventDefault` (`list.filter.js:42`). A `type="reset"` button still clears fields before navigation. That is current behavior; a test that expects the form to stay dirty until navigation will fail for the old reason.
- **LOW:** The floor session must constrain extras in one uv transaction. Installing `.[workflow,test]` first lets the resolver upgrade crispy before the pin.

**Suggestions:**
- Put the required Node binary in the verify command and record `process.version` plus the lockfile versions in the summary.
- Pass a constraints file to `session.install` in the same call as the extras.

**Risk Assessment:** MEDIUM. Product risk is low if JS stays untouched; the evidence command can certify the wrong runtime.

## 06-08

**Summary:** The docs plan points at the pages that are currently wrong, and executable recipes are the right check. It also inherits every contract mistake made earlier, because it documents the implementation rather than the source as it stands.

**Strengths:**
- `docs/reference/buttons.md:84-86` still says crispy buttons do not select a mode or render icons. That sentence has to go.
- `docs/reference/settings.md:78` lists only `context`/`list`/`card` and a three-key default. `test_label_mode_docs.py:126` compares that cell to `LABEL_MODE_DEFAULTS`, so the table update is forced.
- The field-only helper in `examples/bootstrap5/library/views.py:48-49` and the tutorial must stay a class-level `layout` with no actions. Documenting `get_form_actions()` as the extension point matches D-03/D-04.
- Example settings have no `CRUD_VIEWS_LABEL_MODE_DEFAULTS` today (`examples/bootstrap5/project/settings.py:124-128`). Setting `{"form": "both"}` does not clobber another location.

**Concerns:**
- **MEDIUM:** Task 1 says "update the live key count" again. If 06-04 already changed the integer but left `EXPECTED_KEYS` and the row arithmetic stale, this task can "fix" the sentence a second time and still leave the set test red. The count test does not check that every default key appears in the markdown table.
- **MEDIUM:** The canonical resolution section will be wrong if 06-03's owner recovery does not match the spec. This plan has no source assertion for owner precedence; it only renders a configuration recipe.
- **LOW:** `tooltip.js:6` and `javascript.md` are not in `files_modified`. Icon-mode form buttons introduce `data-cv-tooltip="form"` with no doc hook.

**Suggestions:**
- Make the recipe test render an embedded form whose `cv_view` disagrees with the page view, and assert the owner's mode.
- Add the two utility rows to the class table and mention `data-cv-tooltip="form"` next to the icon-mode contract.

**Risk Assessment:** MEDIUM. Publication is well aimed; it will freeze earlier omissions if those plans are not corrected first.

## 06-09

**Summary:** Closing on full-suite evidence rather than inherited probes is the right end gate. As written, that gate is where the unowned `LOCATIONS` and key-set failures show up, after eight plans have already committed.

**Strengths:**
- Full `pytest tests -n auto` plus docs, JS, ruff, and the example check is the only command set that sees `test_button_classes_templates.py` and `test_label_mode_docs.py`.
- Refusing to treat the old seven-test crispy probe as acceptance matches the research caveat.
- Generic downstream follow-up, with no downstream name in new files, matches the project rule.
- Browser checks are explicitly pending until observed. That avoids a false pass.

**Concerns:**
- **HIGH:** Acceptance depends on fixes no earlier plan owns: the `LOCATIONS` loop at `test_button_classes_templates.py:214` and `EXPECTED_KEYS` at `test_button_classes.py:21-91`. This plan's `files_modified` are only the two acceptance docs, so it cannot fix those failures.
- **MEDIUM:** The delete-payload story from 06-01 can be recorded as proven if someone posts `delete=Delete` in a new test while `test_crud.py:63` still omits it. Acceptance should cite the rendered control and the unchanged existing POST separately.
- **LOW:** The unclassified FORM-01/FORM-02 classifier rows do not describe a code gap. Keeping them visible is process noise, not a product risk.

**Suggestions:**
- Move the two test-file fixes into 06-02 and 06-04 so this plan only records results.
- Require the acceptance note to quote `test_crud.py`'s actual POST body and the golden control's `name`/`value` as two different facts.

**Risk Assessment:** HIGH as a closing gate, because it cannot repair the suite breaks the earlier plans leave behind.

## Cross-plan

The phase achieves FORM-01–FORM-13 if the spec's owner, escaping, and layout rules are implemented as written. Those rules match the installed crispy code, not just the plan narrative.

The plans are not executable in order. `"form"` joining `LOCATIONS` (`button_data.py:12`) breaks E108 pins and the action-leaf sentinel loop before 06-03 owns the first file and before anyone owns the second. Adding `form:hidden-label` and `form:icon-host` fails `EXPECTED_KEYS` in a file 06-04 runs but does not list. 06-09 is not allowed to edit either test.

Fix those three file lists before execution. Do not start 06-01 until `origin/main` actually contains Phases 1 and 2; today it does not.


---


## OpenCode Review (gemini-review)

# Cross-AI Plan Review — Phase 6: Form-Button Leaf (`06-01` – `06-09`)

## 06-01

### 1. Summary
Plan `06-01` establishes the required Phase 6 design specification (`.planning/phases/06-form-button-leaf/06-SPEC.md`) and commits five pre-change form-button HTML baselines (`create.html`, `update.html`, `delete.html`, `workflow.html`, `filter.html`) via `tests/test1/test_form_buttons_golden.py` before any production code is edited. While its golden-first discipline and upfront contract design are strong, Task 1 contains a self-blocking git branch precondition (`origin/main` vs `introduce-gsd`) and Task 2's delete POST payload description conflicts with how `CrispyDeleteForm` validates deletion in the repository.

### 2. Strengths
- **Raw control extraction avoids CSRF churn (`src/crud_views/templates/crud_views/view_create.content.html:5-11`, `src/crud_views/templates/crud_views/view_delete.content.html:12-18`):** Extracting only the rendered form controls rather than full `<form>` bodies avoids non-deterministic `{% csrf_token %}` values while preserving exact `<input>` byte representations for `FORM-01` and `D-17`.
- **Upfront resolution of cross-cutting contracts (`src/crud_views/lib/view/button_data.py:16-38`, `src/crud_views/lib/views/list.py:57-87`):** Settling `FORM_LEAF_KEYS` vs `LEAF_KEYS`, attribute collision rules, `Context.dicts` owner recovery, and `ListViewFilterFormHelper.get_form_actions()` omission semantics in `06-SPEC.md` before `06-02` prevents design drift across waves.

### 3. Concerns
- **[HIGH] Self-blocking precondition on `origin/main` vs `introduce-gsd` (`.planning/STATE.md:91`, `src/crud_views/lib/view/label_mode.py:84-117`, `src/crud_views/lib/button_classes.py:209-210`):** Task 1's `<precondition>` requires that remote `main` contain completed Phases 1 and 2 and instructs the executor: *"If absent, stop execution at this precondition; do not merge, switch branches, or reinterpret the current development branch as main."* In this repository, `main` and `origin/main` are still at `38b0100` (before Phase 1), whereas all completed Phase 1–5 work (`default_label_mode`, `FORM_KINDS`, `VARIANT_LOCATIONS`) was committed directly to `introduce-gsd` (`007c21e`) per user instruction recorded in `.planning/STATE.md:91`. Literal adherence to Task 1's precondition will immediately halt execution.
- **[MEDIUM] Incomplete delete POST payload in Task 2 (`src/crud_views/lib/crispy/form.py:121-130`, `src/crud_views/lib/views/delete.py:199-220`, `tests/test1/test_crud.py:55-68`):** Task 2 states *"Add the existing delete payload assertion without changing endpoint authorization or the established `{"delete": "Delete"}` value."* In `src/crud_views/lib/crispy/form.py:121`, `CrispyDeleteForm` requires `confirm = BooleanField(label=_("Confirm deletion"))`, and `tests/test1/test_crud.py:62` posts `{"confirm": True}`. Posting `{"delete": "Delete"}` without `"confirm": True` fails form validation (`200` re-render instead of `302` redirect).
- **[LOW] Conditional hidden inputs on filter baseline (`src/crud_views/lib/views/list.py:77-87`, `tests/test1/app/views.py:300-305`):** Task 3 captures `"filter Apply/Reset plus hidden sort/order/direction controls"`. In `ListViewFilterFormHelper.__init__` (`src/crud_views/lib/views/list.py:77-87`), `Hidden("sort", sort)` is always added, but `Hidden(order_param, order)` and `Hidden(dir_param, direction)` are only added when `order` and `direction` are non-empty in `request.GET` (lines 84–87). A bare `GET /publisher/` request will not render `order` or `dir` hidden inputs unless query parameters (e.g., `?sort=name&order=name&dir=asc`) are supplied.

### 4. Suggestions
- Relax Task 1's `<precondition>` to verify that `HEAD` (on `introduce-gsd`) contains the Phase 1 (`src/crud_views/lib/view/label_mode.py:84`) and Phase 2 (`src/crud_views/lib/button_classes.py:209-210`) contracts, noting `origin/main` (`38b0100`) vs `introduce-gsd` (`007c21e`) without halting.
- In Task 2, post `{"confirm": True, "delete": "Delete"}` when testing the delete endpoint and assert that the rendered delete control carries `name="delete"` and `value="Delete"`.
- In Task 3, specify the exact query string (e.g., `?sort=name&order=name&dir=asc`) used when capturing `tests/test1/golden/form_buttons/filter.html` so all three hidden inputs (`sort`, `order`, `dir`) are present in the baseline.

### 5. Risk Assessment
**MEDIUM** — No production files are modified, but the `origin/main` precondition in Task 1 will block execution immediately unless reconciled with the repo's single-branch (`introduce-gsd`) workflow.

---

## 06-02

### 1. Summary
Plan `06-02` implements the core form-button normalizer (`cv_button_data(ctx, "form")` with `FORM_LEAF_KEYS`), adds `"form"` to `LOCATIONS` and `"form": "label"` to `LABEL_MODE_DEFAULTS`, creates `src/crud_views/templates/crud_views/tags/button/form.html`, overrides `render()` on `Submit`/`Button`/`Reset` in `src/crud_views/lib/crispy/buttons.py` to bypass crispy's `Template(str(self.value))` evaluation, and updates the four layout-button goldens. However, adding `"form"` to `LOCATIONS` and `LABEL_MODE_DEFAULTS` in `06-02` breaks existing tests in `tests/test1/test_action_label_mode_config.py` and `tests/test1/test_label_mode_docs.py` that are not scheduled for update until later waves, and `tags/button/form.html` needs `form:hidden-label` / `form:icon-host` which are not added to `DEFAULT_BUTTON_CLASSES` until `06-04`.

### 2. Strengths
- **Eliminates template evaluation of button values at the adapter boundary (`src/crud_views/lib/crispy/buttons.py:8-30`):** Overriding `render()` on `_TableClassMixin` rather than delegating to `BaseInput.render` prevents `django-crispy-forms` from compiling `self.value` as a Django `Template`, directly mitigating SSTI (`FORM-07`, `D-15`, `T-06-03`) while preserving `self.field_classes` in `__init__` (line 17) for legacy `helper.add_input()` controls (`D-01`).
- **Clean separation of `FORM_LEAF_KEYS` from `LEAF_KEYS` (`src/crud_views/lib/view/button_data.py:16-38, 52-68`):** Branching `cv_button_data` early for `location == "form"` avoids coupling form buttons to action-only keys (`cv_href`, `cv_submit_target`, `cv_modal`, `cv_active`, `cv_oid`).

### 3. Concerns
- **[HIGH] Adding `"form"` to `LOCATIONS` in `06-02` breaks `tests/test1/test_action_label_mode_config.py:278,323` and `tests/test1/test_label_mode_docs.py:125` across Waves 2–6 (`src/crud_views/lib/settings.py:105,158-172`):**
  - `CrudViewsSettings._action_settings_messages()` (`src/crud_views/lib/settings.py:105,158`) validates `CRUD_VIEWS_LABEL_MODE_DEFAULTS` against `button_data.LOCATIONS`.
  - `tests/test1/test_action_label_mode_config.py:278,322-323` hardcodes `E108_LOCATIONS = "['card', 'context', 'list']"` and explicitly tests `({"form": "both"}, [_key_msg("form", E108_LOCATIONS, "both")])` with the comment `# the form location arrives with Phase 6, through LOCATIONS`.
  - Similarly, `tests/test1/test_label_mode_docs.py:124-125` asserts `ast.literal_eval(cells[3].strip("`")) == dict(label_mode.LABEL_MODE_DEFAULTS)` against `docs/reference/settings.md:78`.
  - Because `06-02` modifies `LOCATIONS` and `LABEL_MODE_DEFAULTS` without updating `tests/test1/test_action_label_mode_config.py` (deferred to `06-03`/`06-06`) or `docs/reference/settings.md` (deferred to `06-08`), running the full pytest suite after Wave 2 (`06-VALIDATION.md:26`) will fail.
- **[HIGH] `tags/button/form.html` in `06-02` uses `form:hidden-label` and `form:icon-host` before `06-04` adds them (`src/crud_views/lib/button_classes.py:84-94`, `src/crud_views/lib/view/button_data.py:41-49`):** Task 1 states that `tags/button/form.html` renders all three bodies (`label`, `both`, `icon`) and calls `cv_button_data`. In `icon` mode, the leaf calls `{% cv_button_class 'form' 'hidden-label' %}` and `cv_button_data` calls `icon_host_keys(icon, "form")` → `get_button_class("form", "icon-host")` (`src/crud_views/lib/button_classes.py:163`). Because `form:hidden-label` and `form:icon-host` are not added to `DEFAULT_BUTTON_CLASSES` until `06-04`, `get_button_class("form", "hidden-label")` returns `""` during `06-02` and `06-03`, producing `<span class="">` instead of `<span class="visually-hidden">`.
- **[MEDIUM] `test_crispy_buttons.py` helper `tag()` only matches `<input>` while `test_filter_buttons` stays `<input>` until `06-05` (`tests/test1/test_crispy_buttons.py:21-27, 77-83`):** In `tests/test1/test_crispy_buttons.py:23`, `tag()` searches `r"<input\b[^>]*>"`. In `06-02`, create/delete buttons become `<button>` while filter buttons (`test_filter_buttons`, line 77) remain `<input>` until `06-05`. Replacing `tag()` to only match `<button>` will break `test_filter_buttons` in `06-02`–`06-04`.

### 4. Suggestions
- Update `tests/test1/test_action_label_mode_config.py:278,323` in `06-02` Task 2 when `"form"` is added to `LOCATIONS`.
- Either move the addition of `"form:hidden-label"` and `"form:icon-host"` in `DEFAULT_BUTTON_CLASSES` (`src/crud_views/lib/button_classes.py`) into `06-02` (along with updating `tests/test1/test_button_classes.py:21-91` and `docs/reference/buttons.md:145`), or explicitly scope `06-02` icon-mode tests to not expect `visually-hidden` until `06-04`.
- In `tests/test1/test_crispy_buttons.py`, parse controls with `lxml.html` or support `<button>` for layout controls while keeping `<input>` for `test_filter_buttons` until `06-05`.

### 5. Risk Assessment
**HIGH** — This plan introduces the breaking `<input>` → `<button>` DOM change, custom template context contract, and escaping boundary, and has cross-wave test dependencies with `test_action_label_mode_config.py` and `button_classes.py`.

---

## 06-03

### 1. Summary
Plan `06-03` adds the three-layer `form_actions_label_mode` configuration (`CrudViewsSettings.form_actions_label_mode`, `ViewSet.form_actions_label_mode`, `CrudView.cv_form_actions_label_mode`), extends `CrudView.cv_get_action_label_mode` to `"form"`, and implements view owner selection (`form.cv_view` → helper `view` → page `view`) in `src/crud_views/lib/crispy/buttons.py`. The ownership model is well-thought-out, but the plan needs to be explicit about reading `form.cv_view` from the `form` parameter passed to `render(self, form, context, ...)` rather than `context.get("form")`, and should clarify the overlap with `06-06` on `settings.py` and `viewset/__init__.py`.

### 2. Strengths
- **Consistent whole-map resolution (`src/crud_views/lib/view/base.py:263-272, 299-330`):** Routing `cv_get_form_actions_label_mode()` through `cv_first_inline_keys(cls.cv_form_actions_label_mode, "form_actions_label_mode")` and checking `if key in mapping:` before calling `default_label_mode("form")` matches `location == "list"` (`src/crud_views/lib/view/base.py:323-328`) and guarantees that an explicit mode never triggers a strict-mode error on an unused invalid floor.
- **Handles crispy-forms context shadowing (`src/crud_views/lib/views/list.py:68`, `src/crud_views/templates/crud_views/tags/form.html:3-6`):** Recovering the nearest non-`None` `"view"` across `context.dicts` prevents a `FormHelper` whose `view` attribute is `None` from hiding the enclosing `CrudView` in the page template context (`D-09`).

### 3. Concerns
- **[MEDIUM] Reading `form.cv_view` from the `form` argument of `render()` vs `context` (`src/crud_views/templates/crud_views/tags/list_filter.inner.html:15`, `src/crud_views/lib/crispy/form.py:37-39`):** Task 2 states that `form.cv_view` is the highest-priority owner (`D-09`). In `django-crispy-forms`, `LayoutObject.render(self, form, context, template_pack=..., **kwargs)` receives `form` as a positional argument, while the template context may name the form `filter.form` (`src/crud_views/templates/crud_views/tags/list_filter.inner.html:15`) or an outer form may occupy `context["form"]`. If the adapter looks up `context.get("form")` instead of the `form` argument passed to `render()`, embedded forms and filter forms will resolve the wrong owner.
- **[MEDIUM] Duplicate file ownership with `06-06` on `src/crud_views/lib/settings.py` and `src/crud_views/lib/viewset/__init__.py` (`src/crud_views/lib/settings.py:128-141`, `src/crud_views/lib/viewset/__init__.py:105-111`):** Task 1 instructs: *"Add the three named map fields using existing declaration/validator patterns"* and runs `pytest tests/test1/test_action_label_mode_config.py`. In `src/crud_views/lib/viewset/__init__.py:105`, `@field_validator("context_actions_label_mode", "list_actions_label_mode")` validates ViewSet maps, and `src/crud_views/lib/settings.py:128-141` validates setting maps with `crud_views.E106`. `06-06` Task 1 then lists the same files (`settings.py`, `viewset/__init__.py`, `base.py`) to add `E106` and ViewSet map validation.
- **[LOW] Reference to `06-05`'s private context entry before `06-05` is implemented (`src/crud_views/lib/views/list.py:68`):** Task 2 says *"Obtain the current helper owner from the package's private pushed context entry when present, otherwise crispy's visible helper view overlay"*. Under `{% crispy form form.helper %}`, crispy's `CrispyFormNode` already copies `helper.__dict__` (including `helper.view`) into the pushed context dict, so walking `reversed(context.dicts)` for the first non-`None` `"view"` already finds `helper.view` before the page `view`.

### 4. Suggestions
- Specify in Task 2 that `form_owner = getattr(form, "cv_view", None)` is read directly from the `form` positional parameter of `render(self, form, context, template_pack=..., **kwargs)`.
- Complete the `E106` loop addition in `src/crud_views/lib/settings.py:128-131` and the `@field_validator` addition in `src/crud_views/lib/viewset/__init__.py:105` in `06-03` Task 1, leaving `06-06` Task 1 focused on `CrudView.checks()` (`E210`/`E211`/`W291`).

### 5. Risk Assessment
**MEDIUM** — The ownership precedence rules (`D-09`–`D-12`) are subtle when interacting with `django-crispy-forms`'s internal `Context` stack, requiring thorough integration tests through `{% crispy %}`.

---

## 06-04

### 1. Summary
Plan `06-04` adds the `save`, `cancel`, and `filter-reset` icons to `DEFAULT_ICONS` and `BOOTSTRAP_ICONS` (`src/crud_views/lib/icons.py`), adds `form:hidden-label` and `form:icon-host` to `DEFAULT_BUTTON_CLASSES` (`src/crud_views/lib/button_classes.py`), updates the default key count in `docs/reference/buttons.md`, and wires default semantic icons plus `CrispyFormMixin.submit_icon`, `CrispyDeleteForm.delete_icon`, and `WorkflowForm.submit_icon`. However, Task 1 omits `tests/test1/test_button_classes.py` from `files_modified` even though its `<verify>` command runs `test_button_classes.py`, which hardcodes `assert len(EXPECTED_KEYS) == 71` and `assert set(DEFAULT_BUTTON_CLASSES) == EXPECTED_KEYS`.

### 2. Strengths
- **Synchronized `DEFAULT_ICONS` and `BOOTSTRAP_ICONS` (`src/crud_views/lib/icons.py:14-89`, `tests/test1/test_icons_registry.py:106-112`):** Adding `save`, `cancel`, and `filter-reset` to both registries satisfies `test_bootstrap_preset_covers_exactly_default_names` and `test_defaults_are_font_awesome_only`.
- **Slot-based kind selection independent of `name` (`src/crud_views/lib/crispy/form.py:76, 123-130`, `tests/test1/test_crispy_buttons.py:62-73`):** Selecting the form kind from `slot` (`form:cancel`, `form:delete`, etc.) rather than the HTML `name` attribute prevents `cancel` (`name="reset"`) and `filter-reset` (`name="reset"`) from colliding and preserves `test_delete_button_kwargs_may_choose_the_slot`.

### 3. Concerns
- **[HIGH] `tests/test1/test_button_classes.py:21-91` will fail in Task 1's `<verify>` step because `EXPECTED_KEYS` (71 keys) is not updated (`tests/test1/test_button_classes.py:89-91`):**
  - In `tests/test1/test_button_classes.py:21-91`, `EXPECTED_KEYS` enumerates all 71 keys of `DEFAULT_BUTTON_CLASSES`, and `test_default_table_is_complete()` asserts:
    ```python
    assert len(EXPECTED_KEYS) == 71
    assert set(DEFAULT_BUTTON_CLASSES) == EXPECTED_KEYS
    ```
  - Task 1 adds `"form:hidden-label"` and `"form:icon-host"` to `DEFAULT_BUTTON_CLASSES` in `src/crud_views/lib/button_classes.py` and runs `.venv/bin/pytest tests/test1/test_icon_host_leaves.py tests/test1/test_button_classes.py tests/test1/test_icons_registry.py -q`, but intentionally excludes `tests/test1/test_button_classes.py` from `files_modified` (*"Put any new class/utility regression cases in test_icon_host_leaves.py alongside real rendering, keeping this task within its declared five files"*).
  - Without updating `EXPECTED_KEYS` (to 73 keys) and `test_icon_host_default_slots` (`tests/test1/test_button_classes.py:303-305`) in `tests/test1/test_button_classes.py`, Task 1's `<verify>` command is guaranteed to fail, and no other plan in `06-01`–`06-09` lists `tests/test1/test_button_classes.py` in `files_modified`.
- **[MEDIUM] Partial update to `docs/reference/buttons.md` in Task 1 (`docs/reference/buttons.md:133, 143, 145-146`):** Task 1 updates the `71 keys` count in `docs/reference/buttons.md:145` so `test_documented_default_key_count_matches_table` (`tests/test1/test_button_classes.py:97-101`) passes, but `docs/reference/buttons.md:145-146` also says *"the `*:icon-host` row for four"* and lists the keys in the table at lines 133 and 143. Updating the count to `73` without adding `form:hidden-label` and `form:icon-host` to the table and changing *"for four"* to *"for five"* leaves the table math inconsistent between `06-04` and `06-08`.
- **[LOW] Exact Font Awesome and Bootstrap Icon glyph names for `save`, `cancel`, `filter-reset` not specified in `06-04` (`src/crud_views/lib/icons.py:14-89`, `superpowers/specs/2026-10-22-form-button-label-mode-design.md:125-130`):** Task 1 says *"Add save, cancel and filter-reset to DEFAULT_ICONS and BOOTSTRAP_ICONS with matching semantic meanings"* without stating the exact strings (e.g. `save`: `far:floppy-disk` / `bi:floppy`, `cancel`: `fas:xmark` / `bi:x-lg`, `filter-reset`: `fas:rotate-left` / `bi:arrow-counterclockwise`). Pinning the exact values in `06-SPEC.md` and `06-04` prevents mismatch with `06-08` docs.

### 4. Suggestions
- Add `tests/test1/test_button_classes.py` to `files_modified` in `06-04` (or move `docs/reference/buttons.md` and `tests/test1/test_button_classes.py` into a dedicated task/sub-step if a 5-file per-task limit applies) so `EXPECTED_KEYS` (71 → 73) and `test_utility_slots_default_to_the_bootstrap_word` / `test_icon_host_default_slots` (`tests/test1/test_button_classes.py:104-121, 303-305`) are updated when `DEFAULT_BUTTON_CLASSES` grows.
- Update the table rows at `docs/reference/buttons.md:133,143` alongside line 145.
- State the exact `DEFAULT_ICONS` and `BOOTSTRAP_ICONS` values for `save`, `cancel`, and `filter-reset` in `06-04` Task 1.

### 5. Risk Assessment
**MEDIUM** — The implementation is straightforward, but the missing `tests/test1/test_button_classes.py` file ownership is a guaranteed test failure in Task 1's verification step.

---

## 06-05

### 1. Summary
Plan `06-05` migrates `ListViewFilterFormHelper` (`src/crud_views/lib/views/list.py:57-87`) from `self.add_input(Submit(...))` / `self.add_input(Reset(...))` to a `get_form_actions() -> FormActions | None` hook appended to an instance-isolated `Layout`, while keeping `Hidden` sort/order/dir inputs in `self.inputs` and preserving legacy `add_input()` helpers (`D-01`–`D-04`). The lifecycle design addresses crispy's layout mutation and `super().__init__(form)` traps well, with minor edge cases around instance-level `helper.layout` assignment.

### 2. Strengths
- **Protects class-level `layout` on `ListViewFilterFormHelper` subclasses (`tests/test1/app/views.py:288-289`, `examples/bootstrap5/library/views.py:48-49`):** Deep-copying a subclass's class-level `layout = Layout(...)` per helper instance and appending `get_form_actions()` once prevents repeated renders or multiple requests from mutating the shared `Layout` class attribute (`D-03`, `T-06-09`).
- **Preserves `ListViewTableFilterMixin.get_filterset` constructor call (`src/crud_views/lib/views/mixins.py:315-320`, `src/crud_views/lib/views/list.py:65`):** Keeping `def __init__(self, view, request, form=None):` without requiring `form` in `__init__` preserves compatibility with existing custom `formhelper_class` subclasses that only accept `(self, view, request)`.
- **Retains hidden sort/order/dir inputs on `self.inputs` (`src/crud_views/lib/views/list.py:77-87`, `tests/test1/test_card_order.py:420`):** Leaving `layout.Hidden("sort", ...)` and `order`/`dir` on `self.add_input(...)` keeps hidden `<input type="hidden">` rendering unchanged.

### 3. Concerns
- **[MEDIUM] Distinguishing no-layout helpers from instance-assigned `helper.layout` before `render_layout` (`src/crud_views/lib/views/list.py:57-74`):** Task 1 states: *"Keep a truthy Layout instance for crispy dispatch even for no-layout or None actions; populate no-layout fields from the actual form at render_layout before appending the action group."* If `__init__` assigns `self.layout = Layout()` when no class-level `layout` is declared so crispy's `CrispyFormNode` calls `helper.render_layout()`, care must be taken if a caller assigns `helper.layout = Layout(...)` on the instance after `__init__` or if `render_layout` is called twice on the same no-layout helper instance: `render_layout` must track whether default form fields and `get_form_actions()` have already been populated on that instance so a second `render_layout` call does not prepend `form.fields` or append `FormActions` a second time.
- **[LOW] Passing `form` explicitly to `PublisherFilterFormHelper(view, request, form=form)` (`src/crud_views/lib/views/list.py:65-66`):** In `FormHelper.__init__(self, form=None)`, passing a non-`None` `form` overwrites `self.layout = self.build_default_layout(form)`. Task 1 notes *"Initialize FormHelper without passing form when preserving declared layout"*; make sure `self.form = form` is still stored on `self` when `form is not None` so any crispy code expecting `helper.form` sees it even when `super().__init__()` is called without `form`.

### 4. Suggestions
- In `ListViewFilterFormHelper.__init__`, snapshot whether a declared layout existed (`_declared_layout = copy.deepcopy(getattr(self, "layout", None))`), call `super().__init__()` without `form` when `_declared_layout is not None` (setting `if form is not None: self.form = form`), and build the final per-render layout cleanly in `render_layout` from a fresh copy of `_declared_layout` (or `self.build_default_layout(form)` if `_declared_layout is None` and the instance `self.layout` was not replaced), appending `get_form_actions()` onto that render copy. Building the combined `Layout` on a fresh copy inside `render_layout` (and restoring `self.layout` in a `finally:` block) makes repeated `render_layout()` calls trivially idempotent without any accumulation!

### 5. Risk Assessment
**MEDIUM** — `django-crispy-forms`'s `FormHelper` layout initialization has sharp edges around class-attribute shadowing and `render_layout` dispatch, which this plan identifies and tests thoroughly.

---

## 06-06

### 1. Summary
Plan `06-06` adds static system checks (`E210`/`E211`/`W291` and `W292`) and runtime missing-icon handling (`CRUD_VIEWS_STRICT` `ValueError` vs logged warning + `"label"` fallback) for form buttons. While the runtime fallback and `W292` exception-guard design are solid, there is a direct conflict between Task 1's instruction to emit `E210` for invalid dict values in `cv_form_actions_label_mode` and the existing `cv_label_mode_checks` implementation in `src/crud_views/lib/view/action_menu.py:46-63` (which emits `E211` for invalid dict values), as well as a static `W292` pitfall with `CrispyDeleteForm` and `PolymorphicCrudViewMixin`.

### 2. Strengths
- **Narrow `ValueError` guard in static `W292` check (`src/crud_views/lib/view/buttons.py:426-429`):** Catching `ValueError` only around `cls.cv_get_action_label_mode("form", ...)` mirrors `cv_icon_mode_checks` and ensures an invalid `CRUD_VIEWS_LABEL_MODE_DEFAULTS` in strict mode still surfaces as `crud_views.E108` rather than crashing `check_viewsets()`.
- **Safe runtime fallback in `cv_button_data` (`src/crud_views/lib/view/button_data.py:97-110`):** Falling back from `"icon"` to `"label"` mode when an icon is missing in non-strict mode, while dropping generated `cv_title`, `data-cv-tooltip="form"`, and `cv_icon_class`, prevents rendering an invisible, inaccessible `<button>` in production.

### 3. Concerns
- **[HIGH] `E210` vs `E211` contradiction with `src/crud_views/lib/view/action_menu.py:46-63` and `tests/test1/test_action_label_mode_config.py:221-224`:**
  - Task 1 states: *"For a form mapping, distinguish shape from values: non-dict/non-string keys produce E211 for the view attribute; string-keyed mappings with invalid mode values produce E210 entry diagnostics. Unknown string kinds produce W291 against FORM_KINDS, including ViewSet/settings-selected form maps where statically available"*.
  - In the actual codebase (`src/crud_views/lib/view/action_menu.py:46-63` and `src/crud_views/lib/view/label_mode.py:37-51`), `cv_label_mode_checks` uses `is_label_mode_map(value)` and emits **`viewset.E211`** for **both** bad map shape (`"both"`, `["create"]`) **and** invalid mode values inside a dict (`{"create": "text"}`, `{"create": None}`). This is explicitly pinned in `tests/test1/test_action_label_mode_config.py:221-224` (`test_e211_invalid_view_value`) and documented in `docs/reference/buttons.md:496-497` (where `viewset.E210` is solely for scalar `label_mode` attributes: `CardAction.label_mode`, `cv_card_actions_label_mode`, `ContextButton.label_mode`, `cv_context_action_label_mode`, or a scalar `Submit(..., label_mode=...)` if supported).
  - Furthermore, `src/crud_views/lib/view/action_menu.py:49-50` and `tests/test1/test_action_label_mode_config.py:269-273` (`test_w291_never_for_viewset_or_setting`) explicitly pin that `W291` is only checked on the view's own `cv_*_actions_label_mode` attribute, never on `ViewSet` or settings maps.
  - Implementing Task 1 as written will make `cv_form_actions_label_mode` behave differently from `cv_context_actions_label_mode` and `cv_list_actions_label_mode` (violating `FORM-11` and `superpowers/specs/2026-10-22-form-button-label-mode-design.md:145-146`, which specifies: *"`cv_form_actions_label_mode` gets E211 / W291 through `cv_label_mode_checks(cls, 'cv_form_actions_label_mode', FORM_ACTION_KEYS)`"*).
- **[HIGH] `CrispyDeleteForm` subclasses `CrispyFormMixin`, causing false-positive/missed static `W292` checks if inspected naively (`src/crud_views/lib/crispy/form.py:116-143`):**
  - `CrispyDeleteForm` (`src/crud_views/lib/crispy/form.py:116`) inherits from `CrispyForm(CrispyFormMixin, Form)`, so `issubclass(CrispyDeleteForm, CrispyFormMixin)` is `True` and `CrispyDeleteForm.submit_icon` is `"save"`. However, `CrispyDeleteForm.helper` (lines 133–142) renders `self.get_delete_button()` (`delete` kind, `delete_icon`) and `self.get_cancel_button()` (`cancel` kind), **not** `self.get_submit_button()` (`submit` kind)!
  - If `cv_form_icon_mode_checks` checks `submit_icon` on every `CrispyFormMixin` subclass without distinguishing `CrispyDeleteForm` (which uses `delete_icon` for kind `"delete"`, not `submit_icon` for kind `"submit"`), it will check the wrong button kind on `DeleteView`.
- **[MEDIUM] Static `W292` when an icon is disabled via `CRUD_VIEWS_ICONS = {"save": None}` or on `PolymorphicCreateView` / `PolymorphicUpdateView` (`src/crud_views/lib/icons.py:190-198`, `src/crud_views_polymorphic/lib/utils.py:35`):**
  - Task 2 says: *"Form static missing means icon is None or empty; named-but-unregistered icons retain the icon registry's separate diagnostics."* Note that in `src/crud_views/lib/icons.py:190-191`, setting `CRUD_VIEWS_ICONS = {"save": None}` or `{"save": ""}` is the documented way to switch a semantic icon off (and `check_icons()` allows `None`/`""` without warning, per `tests/test1/test_icons_checks.py:155-157`). Also, `PolymorphicCreateView` and `PolymorphicUpdateView` (`tests/test1/app/views.py:563-577`) configure forms via `polymorphic_forms = {Car: CarForm, Truck: TruckForm}` (`src/crud_views_polymorphic/lib/utils.py:35`) rather than `form_class`. Task 2 should state whether `polymorphic_forms.values()` is inspected alongside `form_class`.

### 4. Suggestions
- Align Task 1 with `src/crud_views/lib/view/action_menu.py:46-73` and `superpowers/specs/2026-10-22-form-button-label-mode-design.md:144-147`: wire `cv_label_mode_checks(cls, "cv_form_actions_label_mode", FORM_KINDS)` in `CrudView.checks()` (`src/crud_views/lib/view/base.py:194`) so `E211` and `W291` work identically to `cv_context_actions_label_mode` and `cv_list_actions_label_mode`. If `E210` is also needed for form buttons, clarify whether it applies to a scalar `label_mode` attribute or whether `E211` covers the map as in `action_menu.py`.
- In `cv_form_icon_mode_checks` (Task 2), check `issubclass(form_class, CrispyDeleteForm)` first (which has kinds `"delete"` via `delete_icon` and `"cancel"`), and otherwise `issubclass(form_class, CrispyFormMixin)` (which has kinds `"submit"` via `submit_icon` and `"cancel"`), and include `polymorphic_forms.values()` when `getattr(cls, "polymorphic_forms", None)` is a dict of form classes.

### 5. Risk Assessment
**HIGH** — The `E210` vs `E211` discrepancy in Task 1 and the `CrispyDeleteForm` inheritance hierarchy in Task 2 can cause diagnostic mismatches with existing checks and documentation tests (`tests/test1/test_label_mode_docs.py:419-428`).

---

## 06-07

### 1. Summary
Plan `06-07` verifies browser-side `<button>` behavior across `modal.js`, `viewset.js`, and `list.filter.js` under the locked Vitest/jsdom packages, and adds an isolated `crispy_floor` session in `noxfile.py` testing `django-crispy-forms==2.0` and `crispy-bootstrap5==2023.10` with Python 3.12 on Django 4.2 and 6.0. The test coverage is thorough, though the plan's `<verify>` commands use bare `npm --prefix . test`, which runs under Node 20 on `PATH` and will fail if `node_modules` is updated in-place to `jsdom 30.1.2` without invoking Node 22.

### 2. Strengths
- **Single-transaction `uv` install for `crispy_floor` (`noxfile.py:13-15`):** Installing `f"django~={django}.0"`, `"django-crispy-forms==2.0"`, `"crispy-bootstrap5==2023.10"`, and `".[polymorphic,workflow,ordered,test]"` in a single `session.install(...)` call prevents `uv` from upgrading `django-crispy-forms` to 2.6 when installing the project extras (unlike `noxfile.py:13-14`, which uses two separate `session.install` calls).
- **Tests nested `<i>`/`<span>` click targets on `<button>` elements (`src/crud_views/static/crud_views/js/viewset.js:38-44`, `src/crud_views/static/crud_views/js/modal.js:75-84, 132-138`):** Dispatching clicks on child `<i>` and `<span>` nodes inside `<button data-cv-cancel-url="...">` and testing `SubmitEvent(..., { submitter: button })` with `new FormData(form, submitter)` directly validates the DOM transition from childless `<input>` elements to `<button>` elements with inner markup.

### 3. Concerns
- **[MEDIUM] `npm --prefix . test` in `<verify>` uses `PATH` Node 20.20.2, which is incompatible with locked `jsdom 30.1.2` (`package.json:15-21`, `superpowers/plans/2026-10-24-concept-review-followups.md:60-61`):**
  - `06-RESEARCH.md` notes that the host environment has Node `20.20.2` on `PATH`, while `package-lock.json` locks `jsdom@30.1.2` (requires Node `^22.22.2 || ^24.15.0 || >=26.0.0`) and `vitest@5.0.3`.
  - If Task 1 runs `npm ci` in the repo root to install `jsdom@30.1.2`, then the `<verify>` command `npm --prefix . test -- tests/js/modal.test.js` (and `npm --prefix . test` in `06-09`) will invoke Node `20.20.2` from `PATH` and fail on `jsdom@30.1.2`.
  - Notice how `superpowers/plans/2026-10-24-concept-review-followups.md:60-61` runs vitest via `npx -y -p node@22 -- node node_modules/vitest/vitest.mjs run`.
- **[LOW] `tests/js/list.filter.test.js:15` uses `<button type="button" id="filter-button-reset">` instead of `type="reset"`:** In `tests/js/list.filter.test.js:15`, the reset button fixture is `<button type="button" id="filter-button-reset"></button>`, whereas `ListViewFilterFormHelper` renders `<button type="reset" name="reset" id="filter-button-reset">`. Task 2 should test `<button type="reset">` with nested `<i>`/`<span>` children inside a `<form>` so any interaction between native form reset and `onReset()` navigation (`src/crud_views/static/crud_views/js/list.filter.js:42-53`) is exercised.

### 4. Suggestions
- Either restore the locked `node_modules` (`jsdom 30.1.2`, `vitest 5.0.3`) in an isolated temp prefix under Node 22 while keeping the working tree `node_modules` intact for Node 20, or invoke vitest via the Node 22 runtime (`npx -y -p node@22 -- node node_modules/vitest/vitest.mjs run`) in both `06-07` and `06-09`.
- In `tests/js/list.filter.test.js`, wrap the filter reset button in `<form id="filter-form">` with `<button type="reset" name="reset" id="filter-button-reset">` and nested `<i>`/`<span>` children.

### 5. Risk Assessment
**MEDIUM** — Production JS (`modal.js`, `viewset.js`, `list.filter.js`) likely requires no changes, but the Node 20 vs `jsdom 30.1.2` engine mismatch can break `npm test` if `node_modules` is mutated in-place without Node 22 on `PATH`.

---

## 06-08

### 1. Summary
Plan `06-08` updates all reference documentation (`buttons.md`, `settings.md`, `action_menus.md`, `icons.md`, `theme.md`, `list_view.md`, `tutorial-5-filters-permissions.md`), adds executable documentation recipe tests (`tests/test1/test_form_button_docs.py`), pairs the `CHANGELOG.md` `### Breaking` entry with `docs/migrating-1.0.md`, and enables `both` mode in `examples/bootstrap5/project/settings.py`. The documentation coverage and executable recipe tests are well-structured, but Task 3's `examples/bootstrap5/project/settings.py` instruction has a discrepancy regarding whether filter buttons should also become `both` (`CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"form": "both"}`) or remain `label` (`CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE = {"submit": "both", "delete": "both", "cancel": "both"}`).

### 2. Strengths
- **Executable documentation recipes (`tests/test1/test_form_button_docs.py`, `tests/test1/test_label_mode_docs.py`):** Following the pattern in `tests/test1/test_pagination_docs.py:45-70` and `tests/test1/test_label_mode_docs.py:88-118`, executing the documented `ListViewFilterFormHelper` and custom button `template=` snippets through real `{% crispy %}` rendering with an isolated template loader ensures the migration recipes in `docs/reference/theme.md` and `docs/migrating-1.0.md` are verified against actual code.
- **Fixes outdated prose in `docs/reference/buttons.md:84-86` and `docs/getting_started/tutorial-5-filters-permissions.md:32-34`:** Explicitly replaces the Phase 2 placeholder sentences in `docs/reference/buttons.md:84-86` (*"Crispy form buttons continue using their existing `slot=` calls without choosing a mode..."*) and updates the filter helper tutorial.

### 3. Concerns
- **[MEDIUM] Discrepancy in `examples/bootstrap5/project/settings.py` configuration (`examples/bootstrap5/project/settings.py:124-130`, `superpowers/specs/2026-10-22-form-button-label-mode-design.md:168-169`):**
  - Task 3 states: *"Set `CRUD_VIEWS_LABEL_MODE_DEFAULTS` `form=both` in the example, merging with its existing configured locations; show submit/delete/cancel and filter controls."*
  - First, `examples/bootstrap5/project/settings.py:124-149` currently does **not** define `CRUD_VIEWS_LABEL_MODE_DEFAULTS` at all, so there are no "existing configured locations" in that file to merge with.
  - Second, `REQUIREMENTS.md` (`FORM-13`), `ROADMAP.md` (Success Criterion 5), `06-CONTEXT.md` (`D-17`), and `superpowers/specs/2026-10-22-form-button-label-mode-design.md:168-169` say: *"example project enables `both` for submit, delete, cancel"* (with `2026-10-22-form-button-label-mode-design.md:168-169` specifying `CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE = {"submit": "both", "delete": "both", "cancel": "both"}` *"so the demo shows icon + text on form buttons while the filter stays text-only"*, whereas `superpowers/plans/2026-10-24-concept-review-followups.md:197` says *"Example project turns on `both` for submit, delete and cancel through `CRUD_VIEWS_LABEL_MODE_DEFAULTS`"*). Setting `CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"form": "both"}` turns on `both` for `filter-submit` and `filter-reset` as well, not just `submit`, `delete`, and `cancel`.
- **[MEDIUM] Tight structural assertions in `tests/test1/test_label_mode_docs.py` (`tests/test1/test_label_mode_docs.py:120-254, 412-428`):**
  - `tests/test1/test_label_mode_docs.py` enforces exact heading names, table column counts, step counts, and anchor links across `settings.md`, `action_menus.md`, `buttons.md`, `migrating-1.0.md`, and `CHANGELOG.md` (for example, line 252 and line 423 assert `_row(..., "`viewset.E211`")[...].count("string or None") == 2`). Any edit to those rows in `action_menus.md` or `buttons.md` in Task 1 must preserve those exact phrases or update the assertions in `test_label_mode_docs.py` in lockstep.
- **[LOW] `<!-- cv-sync: library/views.py -->` blocks in `docs/getting_started/tutorial-5-filters-permissions.md:11,26,41,78` (`examples/bootstrap5/test_docs_sync.py:86-92`):** Task 2 edits `docs/getting_started/tutorial-5-filters-permissions.md`. Because `examples/bootstrap5/test_docs_sync.py` asserts that every fenced block preceded by `<!-- cv-sync: ... -->` matches `examples/bootstrap5/library/views.py` verbatim, Task 2 must only edit the prose in `tutorial-5-filters-permissions.md` and leave the fenced code blocks unchanged.

### 4. Suggestions
- Clarify in `06-SPEC.md` and `06-08` Task 3 whether `examples/bootstrap5/project/settings.py` should set `CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"form": "both"}` (all 5 form buttons including filter) or `CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE = {"submit": "both", "delete": "both", "cancel": "both"}` (submit, delete, cancel only), and note that `examples/bootstrap5/project/settings.py` currently has no `CRUD_VIEWS_LABEL_MODE_DEFAULTS` setting.
- Run `examples/bootstrap5/test_docs_sync.py` as part of `06-08` Task 2's `<verify>` command rather than waiting until `06-09`.

### 5. Risk Assessment
**LOW** — Primarily documentation, changelog, and example settings changes, guarded by `mkdocs build --strict` and doc sync tests.

---

## 06-09

### 1. Summary
Plan `06-09` executes the integrated verification gates (full pytest suite, JS suite, `mkdocs build --strict`, `ruff check`, `ruff format --check`, example project checks, `test_docs_sync.py`, and browser acceptance) and records the final verification and generic downstream-theme follow-up in `.planning/phases/06-form-button-leaf/06-ACCEPTANCE.md` and `06-VALIDATION.md`. Its audit trail is comprehensive, but its example verification gate (`python examples/bootstrap5/manage.py check`) misses ViewSet checks in the example project unless `examples/bootstrap5`'s pytest suite is also run.

### 2. Strengths
- **Honest gate reporting for `ruff format --check` (`.planning/STATE.md:114, 130`):** Explicitly instructing the executor to distinguish the 8 pre-existing unformatted `.planning/` markdown files from Phase 6 product/test/doc files avoids either hiding a real formatting failure or creating unrelated churn outside Phase 6.
- **Hygiene-compliant downstream theme note (`.planning/PROJECT.md` Constraints, `06-CONTEXT.md` `D-17`):** Recording the downstream icon mappings (`save` → `device-floppy`, `cancel` → `x`, `filter-reset` → `filter-off`) and selector updates generically in `06-ACCEPTANCE.md` without using downstream project names satisfies the repo hygiene rule.

### 3. Concerns
- **[MEDIUM] Bare `python examples/bootstrap5/manage.py check` skips all example ViewSet checks (`examples/bootstrap5/project/tests.py:97-115`):**
  - `06-09-PLAN.md` runs `.venv/bin/python examples/bootstrap5/manage.py check` with `<fails_when>The example reports form configuration/system-check errors or fails to start its checks.</fails_when>`.
  - As documented in `examples/bootstrap5/project/tests.py:98-105` (`SystemChecksTest.test_no_check_errors_with_every_viewset_registered`), bare `manage.py check` does **not** import the example feature apps' `views.py` modules (which are loaded lazily via the URLconf), so `ViewSet._REGISTRY` is empty during bare `manage.py check` and none of the `ViewSet`/`CrudView` checks (`E210`, `E211`, `W291`, `W292`) run against the example apps!
- **[LOW] `npm --prefix . test` gate in `06-09` vs Node 22 runtime (`superpowers/plans/2026-10-24-concept-review-followups.md:60-61`):** As in `06-07`, if the locked `jsdom 30.1.2` / `vitest 5.0.3` environment requires Node 22 while default `PATH` has Node 20.20.2, the `<verify>` command in `06-09` must invoke the Node 22 runtime so it matches `06-07`'s lock-backed environment.

### 4. Suggestions
- Replace or supplement `cd examples/bootstrap5 && ../../.venv/bin/pytest test_docs_sync.py -q` in `06-09` with `cd examples/bootstrap5 && ../../.venv/bin/pytest -q` so that `SystemChecksTest.test_no_check_errors_with_every_viewset_registered` (`examples/bootstrap5/project/tests.py:97-115`) and all example app tests run against the updated form buttons and `examples/bootstrap5/project/settings.py`.

### 5. Risk Assessment
**LOW** — Read-only verification and acceptance documentation plan; adding the full `examples/bootstrap5` pytest run closes the `manage.py check` blind spot.

---

## Cross-Plan Comparison & Overall Summary

### Cross-Plan Dependency & Ordering Issues
1. **`tests/test1/test_button_classes.py` is missing from `files_modified` across all 9 plans (`06-04` Task 1):**
   - `tests/test1/test_button_classes.py:21-91` pins `EXPECTED_KEYS` (71 keys) and asserts `set(DEFAULT_BUTTON_CLASSES) == EXPECTED_KEYS`. When `06-04` adds `"form:hidden-label"` and `"form:icon-host"` to `DEFAULT_BUTTON_CLASSES`, `test_button_classes.py` fails immediately unless updated.
2. **Adding `"form"` to `LOCATIONS` and `LABEL_MODE_DEFAULTS` in `06-02` breaks existing tests in `tests/test1/test_action_label_mode_config.py` and `tests/test1/test_label_mode_docs.py` until Waves 3/6/7:**
   - `tests/test1/test_action_label_mode_config.py:278,323` asserts that `{"form": "both"}` in `CRUD_VIEWS_LABEL_MODE_DEFAULTS` fails `crud_views.E108` with `['card', 'context', 'list']`.
   - `tests/test1/test_label_mode_docs.py:125` asserts that the `CRUD_VIEWS_LABEL_MODE_DEFAULTS` table cell in `docs/reference/settings.md:78` equals `dict(label_mode.LABEL_MODE_DEFAULTS)`.
   - Updating `LOCATIONS` and `LABEL_MODE_DEFAULTS` in `06-02` without updating those two assertions will cause full-suite runs between waves (`06-VALIDATION.md:26`) to fail until `06-06` and `06-08`.
3. **Diagnostic ID mismatch (`E210` vs `E211`) between `06-06` Task 1 and `src/crud_views/lib/view/action_menu.py:46-63`:**
   - Existing `cv_label_mode_checks` (`src/crud_views/lib/view/action_menu.py:46-63`) emits `viewset.E211` for invalid dict values in `cv_context_actions_label_mode` and `cv_list_actions_label_mode` (`tests/test1/test_action_label_mode_config.py:221-224`), while `viewset.E210` is used for scalar `label_mode` attributes (`docs/reference/buttons.md:496-497`). `06-06` Task 1 asks for `E210` on invalid dict values in `cv_form_actions_label_mode`.
4. **Git branch precondition in `06-01` Task 1 (`origin/main` vs `introduce-gsd`):**
   - Phases 1–5 live on `introduce-gsd` (`007c21e`), not `origin/main` (`38b0100`). `06-01` Task 1's instruction to halt if `origin/main` lacks Phases 1 and 2 must be updated to check `HEAD` on the active branch.

### Overall Risk Assessment
**MEDIUM-HIGH** — The architectural design for Phase 6 (dedicated `tags/button/form.html` leaf, `FORM_LEAF_KEYS`, bypassing `BaseInput.render` template evaluation, `Context.dicts` owner recovery, and isolated `ListViewFilterFormHelper` layouts) is sound and achieves all phase goals (`FORM-01`–`FORM-13`). Resolving the four cross-plan issues above before execution will prevent self-inflicted test and precondition failures across waves.


---


## Consensus Summary

This review concerns committed plan set `007c21efab564b8aaa5f8706215fbf98ebbb8388`; no implementation was performed. Repeated findings in individual plan sections are deduplicated below. A proposed fix is advisory: it may not replace a locked decision or lower acceptance standards.

### Agreed Strengths

Fable, Grok and Gemini independently trace the same implementation hazards: crispy layout rendering must bypass `BaseInput.render` value compilation, while helper.inputs must retain the pack-owned path; whole-map resolution must preserve `{}`; helper layouts must be isolated before appending actions; real native submitter payload tests and baseline-first history are appropriate. Both identify the existing package methods and real crispy templates behind those statements.

### Agreed Concerns

- **H-LOCATIONS — HIGH; plans 06-02/03/08/09.** Changes to LOCATIONS/LABEL_MODE_DEFAULTS must update all existing consumers in the same integrated wave. Grok, Fable and Gemini corroborate the hard-coded E108 locations and form-invalid case (`tests/test1/test_action_label_mode_config.py:278,323`) and settings-table equality (`tests/test1/test_label_mode_docs.py:126`). Grok additionally identifies the action/menu sentinel loop (`tests/test1/test_button_classes_templates.py:214`), which wrongly sends every location through action leaves. 06-02 omits these consumer edits, 06-03 first owns the configuration tests, 06-08 first owns settings.md, and no plan owns the template sentinel file. Required property: every intermediate integrated wave can pass the promised full suite. One route is to move the affected existing assertions/table cell to 06-02 and split action-location coverage from finite form-kind coverage. Keep the final form tests; do not erase them to make the suite green.
- **H-KEYSET — HIGH; plan 06-04.** The utility-key addition must update the exhaustive default-key contract in its producing task. Grok and Gemini mark HIGH and Fable corroborates at MEDIUM: `tests/test1/test_button_classes.py:21-91` hard-codes EXPECTED_KEYS and a count of71, while 06-04 adds two defaults, runs that file, and expressly restricts the task to five other files. Required property: the utility-key task owns and verifies the complete expected-key update. Example route: include that test file and update the exhaustive set/count alongside the measured docs count.
- **M-PAYLOAD — MEDIUM; plan 06-01.** Describe a new submitter assertion accurately. All three reviewers found that `tests/test1/test_crud.py:63` posts `{"confirm": True}`, not the claimed existing `{"delete": "Delete"}` assertion. Required plan change: preserve the existing confirmation flow, assert the rendered delete control's name/value separately, and add a POST including confirmation and the clicked submitter value. Do not replace required confirmation data with a submitter-only request.

### Divergent Views and Solo Findings

- **H-MAIN — HIGH, external execution prerequisite; plan 06-01.** Fable and Gemini raise this as a HIGH; Grok independently confirms the absent main-branch contracts while calling the halt correct. A fresh read-only `git ls-remote origin refs/heads/main` returned `38b0100683fa71412b8bc00dd0eeb7f985efb459`; source reads at that SHA found neither `default_label_mode` nor FORM_KINDS. Required property: the roadmap's authoritative-main Phase1/2 prerequisite holds before spec/execution. The plan already records the correct halt, so this is an unresolved external prerequisite, not permission to weaken that halt. Fable/Gemini's suggested executing-branch substitution conflicts with ROADMAP.md:209 and is not an admissible remedy without an explicit user decision. No merge/branch change is authorized or performed by this review.
- **H-NODE — HIGH reported by Fable, (single-reviewer, unconfirmed), excluded from the blocking count.** The installed nvm tree contains only v20.20.2 and the lockfile engines indeed require newer Node. However the asserted impossibility of completing acceptance without lowering the gate is not established: 06-07 task1 explicitly allows obtaining an isolated compatible runtime and requires a recorded blocker if that cannot be done. The premise that no compatible runtime can be obtained is unconfirmed. Keep this concern visible; do not accept the suggested old-runtime-only acceptance fallback. Grok/Gemini's distinct MEDIUM concern about binding commands across shells remains M-NODE-COMMANDS; it does not prove acquisition impossible.
- **M-NAME — MEDIUM; plans 06-01/02.** Preserve actual upstream submitted-name semantics for multi-word names. Installed `crispy_bootstrap5/templates/bootstrap5/layout/baseinput.html:2` uses wordcount and slugify; the new spec says positional name wins but never distinguishes stored raw name from the name currently emitted by the pack. Required plan change: settle and test that normalization against the old rendered wire name while preserving literal escaping and generated IDs. Any intentional difference needs an explicit compatible decision/migration treatment.
- **M-SLOT — MEDIUM; plans 06-02/08.** Record the compatibility policy for non-form/unknown slot inputs. `_TableClassMixin` currently accepts arbitrary slot strings (`src/crud_views/lib/crispy/buttons.py:16-18`); 06-02's finite form validation will reject these. Required plan change: explicitly disposition this change and its test/migration in PLAN.md. Do not broaden FORM_KINDS or reinterpret variant grammar against D-13; recording the rejection as Breaking is one possible route.
- **M-OWNERS — MEDIUM; plans 06-01/03.** Extend the owner recovery evidence to multiple FormActions and nested formset row forms. `crispy_forms/bootstrap.py:309` leaves another context layer, and `src/crud_views/templates/crud_views/formsets/formset.html:42` invokes crispy for rows with explicit helpers. Existing tasks name nested Context pushes and an embedded form but not these concrete layouts. Required plan change: read ownership from the actual render form argument (not an outer context form), and add these source-grounded regression cases or explicitly explain why the existing matrix covers them. The review does not prescribe a particular marker implementation; arbitrary fixed stack offsets would not meet the owner invariant.

- **L-HIDDEN-WRAPPER — LOW; plans 06-05/08.** Moving visible actions leaves the pack's hidden-input wrapper and its margin after the layout (`crispy_bootstrap5/templates/bootstrap5/inputs.html:1-13`). Required plan change: acknowledge/test the expected wrapper/ordering in the phase golden and migration or explicitly disposition it as an accepted unchanged pack-owned behavior. Do not globally override crispy inputs or move hidden controls against D-01.
- **L-TOOLTIP-DOC — LOW; plan 06-08.** The public location list in `docs/reference/javascript.md:99-107` and `src/crud_views/static/crud_views/js/tooltip.js:6-7` omits the new `form` token; neither file is assigned. Required plan change: include those existing contract descriptions or explicitly disposition the omission. Runtime initialization already handles arbitrary marker values; this is documentation maintenance, not a missing JS feature.

- **H-EARLY-UTILITIES — HIGH; plans 06-02/04.** Gemini identifies a separate within-phase delivery gap: 06-02 promises all three mode bodies while the `form:hidden-label` and `form:icon-host` defaults only arrive in06-04. Existing `get_button_class` returns an empty class for absent keys (`src/crud_views/lib/button_classes.py:148-149`), so an icon-mode label would be visible and a host icon unstyled between those tasks. Required property: each producing task has the utility dependencies for the behaviors it claims and verifies. Move coherent prerequisites earlier or explicitly stage the intermediate contract without reducing final D-14 scope. This is a solo non-discounted judgment HIGH and counts.
- **H-DIAGNOSTIC-CONTRACT — HIGH; plan06-06.** Gemini raises HIGH, overlapping Grok/Fable MEDIUM concerns: the proposed invalid-value E210/shape E211 and cross-tier W291 split differs from existing map-check semantics (`action_menu.py:46-71`, tests/test1/test_action_label_mode_config.py:221-224,269-273) and the earlier design's map-check wiring. Required property: the new form diagnostics have an explicit reconciled policy and tests/documentation while existing context/list behavior remains intact. Either retain the established map policy or explicitly justify the intentional form-specific distinction in executable PLAN.md; do not assume an older background spec overrides current CONTEXT. Also specify truthful form-specific message wording rather than the old card/context hints and view-action terminology. M-MESSAGES is folded here, not counted again.
- **H-DELETE-STATIC — HIGH; plan06-06 task2.** Gemini notes that CrispyDeleteForm inherits CrispyFormMixin but its overridden helper renders delete/cancel, not submit/cancel (`src/crud_views/lib/crispy/form.py:116-143`). Required property: static W292 inspects the controls the actual default helper renders and neither warns on an unused inherited submit icon nor misses delete_icon. Add an explicit delete-provider branch and regression cases, or an equivalent provider-aware mechanism. The existing generic named-control behavior is intent; the reviewer identifies the concrete inheritance case needing executable coverage. Solo non-discounted judgment HIGH; counted.
- **M-HELPER-STATE — MEDIUM/LOW; plan06-05.** Gemini adds cases not explicitly named in the existing class-layout tests: a caller replacing `helper.layout` after construction, and the `helper.form` reference stored by upstream FormHelper when an explicit form is supplied (`crispy_forms/helper.py:208-214`). Required plan change: preserve/test these instance contracts or explicitly disposition them while retaining D-03/D-04; repeated rendering must not replace the caller layout or lose the explicit form association.
- **M-REGISTRY-OFF — MEDIUM; plan06-06.** `resolve_icon` treats registry values None/empty as disabled (`src/crud_views/lib/icons.py:187-198`), and `tests/test1/test_icons_checks.py:155-157` intentionally reports no registry warning. A nonempty semantic name can therefore render no icon despite the task's raw None/empty definition. Required plan change: explicitly cover registry-disabled icons in static/runtime form checks or document an intentional scoped distinction with the required fallback preserved. This is not the separate unregistered-prefix diagnostic case.
- **M-POLYMORPHIC — MEDIUM; plan06-06.** Concrete forms may live in `PolymorphicCrudViewMixin.polymorphic_forms` (`src/crud_views_polymorphic/lib/utils.py:35,64-70`) instead of form_class. Required plan change: define and test static inspection of a concrete mapping or explicitly classify it as dynamic with proven runtime coverage; do not silently omit the provider.
- **M-NODE-COMMANDS — MEDIUM; plans06-07/09.** Grok and Gemini distinguish runtime acquisition from binding actual verification to it. All automated JS commands remain bare npm, while later tasks may have fresh shells. Required plan change: make the chosen compatible Node/npm selection reproducible in each JS gate and record/assert actual runtime plus lock versions. This does not require loosening the locked package gate or adding a fixed obsolete Node22 minor.
- **M-EXAMPLE-CHECKS — MEDIUM; plan06-09.** Gemini's example-check blind spot is independently confirmed in `examples/bootstrap5/project/tests.py:97-115`: bare manage.py check can leave feature ViewSets unregistered; its dedicated test loads the URLconf before checking. Required plan change: run that registered-ViewSet test or equivalent explicit URLconf-backed check, rather than claiming the current bare command alone validates example form checks. Running the full example pytest suite is one possible remedy.

### Findings Already Represented or Not Substantiated

These findings remain in raw reviews as audit history and are not additional actionable counts:

| Reviewer / concern | Disposition and executable evidence |
|---|---|
| Grok06-01 partial baseline verification | 06-01 task3 captures and verifies workflow/filter before any product plan; baseline completion is not claimed at task2. |
| Fable06-01 spec content not asserted by pytest | 06-01 task1 acceptance/fails_when explicitly require written spec/main evidence; old tests alone are explicitly insufficient. This is an inspectable design deliverable, not a claim that pytest validates prose. |
| Grok06-02 duplicate CSS | 06-01 defines one append of class-table/css_class/extra class; 06-02 task2 requires no class mutation and exactly-one final attributes. |
| Grok06-02 cancel URL wiring | 06-02 requires cancel-only URL and preserved attribute behavior; 06-07 explicitly exercises the actual data-cv-cancel-url handler. |
| Grok06-02 slot/template kwargs leakage | Existing constructors consume slot/template/css_id/css_class; 06-02 preserves their signature and separates raw extra kwargs. Not evidence of a planned leak. |
| Grok06-03 delayed E106 / own CrudView field | 06-03 declares the actual CrudView field and setting validators; 06-06 explicitly extends E106 and real checks. No missing final wiring. |
| Grok06-04 docs table arithmetic | Included with H-KEYSET and 06-08's complete utility-table update; do not count a duplicate. |
| Grok06-05 append guard / pre-dispatch layout | 06-05 task1 says initialize a truthy layout, append exactly once; task2 covers two helpers and repeated rendering. Fable correctly notes empty Layout is falsy; this supports the existing truthy requirement rather than mandating its preferred implementation. |
| Fable06-05 public helper state | 06-05 Artifacts explicitly calls the new state private, and the task specifies a private pushed context key. |
| Grok06-06 E210 does not fall out of old helper | 06-06 task1 explicitly changes shape/value handling; it does not say to invoke the old helper unchanged. The current diagnostic-policy concern and wording are consolidated in H-DIAGNOSTIC-CONTRACT. |
| Grok06-06 helper static reach | 06-06 task2 explicitly inspects configured helper classes inheriting default get_form_actions; dynamic hooks skip static inference and have real runtime tests. |
| Fable06-06 W291 cross-tier dedup | The policy discrepancy is now consolidated in H-DIAGNOSTIC-CONTRACT following Gemini. The process-global-state claim remains unsubstantiated: the old comment documents context/list behavior; the plan deliberately adds finite form behavior without changing existing locations. Dedup does not inherently require process-global state. Any later policy change must preserve FORM-12/D-16. |
| Grok/Fable06-07 native FormData and floor installation | 06-07 expressly forbids fake constructors, tests actual FormData payloads and constrains floors plus extras in one transaction. |
| Grok06-07 reset preventDefault | Source already omits preventDefault; plan preserves established semantics and does not demand the suggested contradictory assertion. |
| Grok06-08 owner recipe | Actual conflicting-owner rendering is covered by06-03; M-OWNERS captures the concrete additional cases, not an additional duplicate documentation-test mandate. |
| Fable06-08 same canonical sentence edited twice | Plans06-04 and06-08 are ordered by dependencies, not parallel; rereading live defaults is not a merge race. |
| Fable06-08 Added-bullet prefix | The new form setting/icons use different public names; no plan asks for a duplicate old-prefix Added bullet. Preserve existing doc tests as already required. |
| Fable06-09 manage.py uncertainty | Supplemental filesystem read confirms `examples/bootstrap5/manage.py`; no missing-path concern. |
| Grok/Fable06-09 classifier bookkeeping | Explicitly required by the current plan inputs and not a product gap; no new work demanded. |
| Fable06-04 icon keyword / glyph suggestions | 06-04 explicitly consumes icon= as configuration and requires matching semantic meanings; exact glyph choice remains implementation discretion. |

| Gemini06-01 hidden baseline query | 06-01 task3 explicitly requires hidden order/direction capture with stable fixture values; supplying nonempty query inputs follows that existing action. |
| Gemini06-02 mixed input/button extraction | 06-02 explicitly retains filter inputs until06-05 and updates only migrated assertions; no instruction replaces the helper with a button-only matcher. |
| Gemini06-03 actual form vs context form | Folded into M-OWNERS: add an explicit render-argument identity assertion in the concrete nested cases. |
| Gemini06-03 repeated file ownership / future helper marker | Plans are sequential; 06-03 explicitly uses the private marker only when present and falls back otherwise. No undeclared dependency or race. |
| Gemini06-04 exact glyph strings | Semantic mappings are locked; precise supported library glyph selection is spec/implementation work, not a new user decision. |
| Gemini06-07 type=reset inside form | 06-07 task2 already requires actual rendered button shape and established native semantics; execution should use type=reset inside form, not retain the old type=button fixture. |
| Gemini06-08 example per-kind map vs floor | Current CONTEXT D-17 and 06-08 explicitly choose form floor both; the earlier background spec's text-only filters are superseded. No new decision is required and the old spec cannot silently narrow the current plan. |
| Gemini06-08 exact docs structure / sync fences | 06-08 owns the existing doc tests and preserves the documented field-only subclass;06-09 runs docs synchronization. Do not alter synced example code just to add prose. |

## Verification coverage

### Cross-artifact fact drift

- Phase status seam: `drift-guard phase-status --phase 06` returned `consistent`, STATE=`Ready to execute`, ROADMAP=`Planned`, rank1/rank1; authority STATE.md. This status comparison does not prove the main-branch prerequisite.
- Requirement IDs: ROADMAP.md:222-223 lists FORM-01..13; PLAN requirements and task references use the same IDs. No contradictory duplicate fact found.
- Success criteria: ROADMAP.md:224-235 and the plan must_haves agree on real buttons, default payloads, modes, escaping, icons/checks and paired migration/example deliverables. Missing test-consumer ownership is reported above as a plan coverage/order defect, not duplicated as drift.
- Glossary: CONTEXT decisions D-01..17 and plan use of owner, whole-map selection, finite kinds, literal values and legacy helper.inputs agree. No contradiction found; discretionary/deferred prose was not treated as authority.
- All four axes were compared. No cross-artifact advisory is included in HIGH/actionable counts. The roadmap's historical delete-test wording is clarified by M-PAYLOAD against source, not misclassified as a contradiction between the plan and roadmap.


### Source-grounding coverage inventory

Effective authority: `intel` (drift-guard authority --raw), not the configured hint `grep`. `.planning/intel/API-SURFACE.md:5` explicitly says its index has no entries; api-map.json is absent. The adapter cannot establish Python names/signatures, browser APIs, CLI options or path targets from this index. Consequently the verdict is **UNCHECKABLE / INFO**, not MISSING, for existing references below. Direct filesystem/source observations are supplemental evidence, not a claim of verified call signatures or successful execution. No hardBlock or needs-acknowledgement verdict was produced. The seam returned VERIFIED→none, UNCHECKABLE→INFO, AMBIGUOUS→MEDIUM, MISSING→needs-acknowledgement at effective authority intel.

Every symbol below includes all citing plan lines. Proposed symbols and files are explicitly excluded under each plan’s “Artifacts this phase produces”; cross-plan uses remain future outputs. `get_form_actions` and `render_layout` have existing base declarations and proposed filter-helper overrides, both distinguished below. Short file names resolve through the plan’s full read_first/files paths. Python signatures are UNCHECKABLE even where a declaration is located.

#### Named symbols, fields and options

<details>
<summary><code>--check</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); no authoritative declaration claim; runtime/property/CLI/browser or framework contract requires execution-time confirmation</summary>

06-09-PLAN.md:230 — <automated>.venv/bin/ruff format --check</automated>

All citations: 06-09-PLAN.md:230

</details>

<details>
<summary><code>--prefix</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); no authoritative declaration claim; runtime/property/CLI/browser or framework contract requires execution-time confirmation</summary>

06-07-PLAN.md:83 — <automated>npm --prefix . test -- tests/js/modal.test.js</automated>

All citations: 06-07-PLAN.md:83, 06-07-PLAN.md:103, 06-09-PLAN.md:222

</details>

<details>
<summary><code>--strict</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); no authoritative declaration claim; runtime/property/CLI/browser or framework contract requires execution-time confirmation</summary>

06-08-PLAN.md:113 — <automated>.venv/bin/mkdocs build --strict</automated>

All citations: 06-08-PLAN.md:113, 06-09-PLAN.md:86

</details>

<details>
<summary><code>ACCEPTANCE.md</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); no authoritative declaration claim; runtime/property/CLI/browser or framework contract requires execution-time confirmation</summary>

06-09-PLAN.md:8 — - .planning/phases/06-form-button-leaf/06-ACCEPTANCE.md

All citations: 06-09-PLAN.md:8, 06-09-PLAN.md:24, 06-09-PLAN.md:29, 06-09-PLAN.md:60, 06-09-PLAN.md:65, 06-09-PLAN.md:80

</details>

<details>
<summary><code>BOOTSTRAP_ICONS</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `src/crud_views/lib/icons.py:51` — `BOOTSTRAP_ICONS: dict[str, str] = {`</summary>

06-04-PLAN.md:85 — Add save, cancel and filter-reset to DEFAULT_ICONS and BOOTSTRAP_ICONS with matching semantic meanings. Add form:hidden-label='visually-hidden' and form:icon-host following the existing host composition grammar. Ensure the leaf reads mode classes through cv_button_class and the utility keys through their dedicated lookups; host classes must be escaped as attributes. Label mode suppresses all icon output and host classes, both emits icon plus text without generated tooltip, icon emits hidden text/title/form tooltip. Cover renderer prefix variants and explicit host opt-out, a Unicode/lazy label, an empty label, and repeated renders with changed registry/settings. Extend the real host/leaf tests for finite kind grammar and utility keys; keep the existing live default-key count guard satisfied by the count update described above.

All citations: 06-04-PLAN.md:85

</details>

<details>
<summary><code>BaseInput</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `.venv/lib/python3.12/site-packages/crispy_forms/layout.py:199` — `class BaseInput(TemplateNameMixin):`</summary>

06-02-PLAN.md:86 — Implement adapter render without calling BaseInput.render: retain raw value and kwargs, normalize per spec, render the selected leaf through a scoped context copy. Strip inherited input aliases from the template context, never expose the adapter object. Normalize SafeData and lazy values at render time to ordinary strings then use Django autoescaping once; serialized extra attrs are escaped once separately. Preserve constructor signature, slot-selected semantic kind, upstream generated IDs and legacy field_classes/flat_attrs for helper.inputs. Do not infer kind from the submitted name. The leaf uses cv_button_class form/cv_key/cv_label_mode, appends cv_css_class and host classes, and renders the three bodies with cancel URL only for cancel. Keep normalizer/icon behavior extensible for 06-04 rather than hardcoding a temporary floor. Update existing input-only assertions only where layout buttons changed; filter helper inputs remain inputs until 06-05.

All citations: 06-02-PLAN.md:86, 06-02-PLAN.md:99, 06-02-PLAN.md:146

</details>

<details>
<summary><code>BaseInput.render</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `src/crud_views/templatetags/crud_views.py:333` — `def render(self, context):`; `src/crud_views/lib/table/columns.py:23` — `def render(self, table, **kwargs):`; `src/crud_views/lib/table/columns.py:38` — `def render(self, table, record, **kwargs):`</summary>

06-02-PLAN.md:86 — Implement adapter render without calling BaseInput.render: retain raw value and kwargs, normalize per spec, render the selected leaf through a scoped context copy. Strip inherited input aliases from the template context, never expose the adapter object. Normalize SafeData and lazy values at render time to ordinary strings then use Django autoescaping once; serialized extra attrs are escaped once separately. Preserve constructor signature, slot-selected semantic kind, upstream generated IDs and legacy field_classes/flat_attrs for helper.inputs. Do not infer kind from the submitted name. The leaf uses cv_button_class form/cv_key/cv_label_mode, appends cv_css_class and host classes, and renders the three bodies with cancel URL only for cancel. Keep normalizer/icon behavior extensible for 06-04 rather than hardcoding a temporary floor. Update existing input-only assertions only where layout buttons changed; filter helper inputs remain inputs until 06-05.

All citations: 06-02-PLAN.md:86, 06-02-PLAN.md:146

</details>

<details>
<summary><code>BasicNode</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `.venv/lib/python3.12/site-packages/crispy_forms/templatetags/crispy_forms_tags.py:56` — `class BasicNode(template.Node):`</summary>

06-03-PLAN.md:91 — <read_first>06-SPEC.md ownership contract; installed crispy BasicNode.get_render/FormHelper.get_attributes; tests/test1/test_crispy_buttons.py</read_first>

All citations: 06-03-PLAN.md:91

</details>

<details>
<summary><code>BasicNode.get_render</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `.venv/lib/python3.12/site-packages/crispy_forms/templatetags/crispy_forms_tags.py:70` — `def get_render(self, context):`</summary>

06-03-PLAN.md:91 — <read_first>06-SPEC.md ownership contract; installed crispy BasicNode.get_render/FormHelper.get_attributes; tests/test1/test_crispy_buttons.py</read_first>

All citations: 06-03-PLAN.md:91

</details>

<details>
<summary><code>Button</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `src/crud_views/lib/crispy/buttons.py:25` — `class Button(_TableClassMixin, layout.Button):`; `.venv/lib/python3.12/site-packages/crispy_forms/layout.py:326` — `class Button(BaseInput):`</summary>

06-02-PLAN.md:101 — - Explicit template > subclass template > bundled template on Submit, Button and Reset; %s resolves the active pack.

All citations: 06-02-PLAN.md:101

</details>

<details>
<summary><code>CHANGELOG.md</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); no authoritative declaration claim; runtime/property/CLI/browser or framework contract requires execution-time confirmation</summary>

06-08-PLAN.md:17 — - CHANGELOG.md

All citations: 06-08-PLAN.md:17, 06-08-PLAN.md:107, 06-08-PLAN.md:108

</details>

<details>
<summary><code>CLAUDE.md</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); no authoritative declaration claim; runtime/property/CLI/browser or framework contract requires execution-time confirmation</summary>

06-01-PLAN.md:51 — @CLAUDE.md

All citations: 06-01-PLAN.md:51, 06-02-PLAN.md:57, 06-03-PLAN.md:51, 06-04-PLAN.md:57, 06-05-PLAN.md:51, 06-06-PLAN.md:53, 06-07-PLAN.md:52, 06-08-PLAN.md:59, 06-09-PLAN.md:47

</details>

<details>
<summary><code>CONTEXT.md</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); no authoritative declaration claim; runtime/property/CLI/browser or framework contract requires execution-time confirmation</summary>

06-01-PLAN.md:56 — @.planning/phases/06-form-button-leaf/06-CONTEXT.md

All citations: 06-01-PLAN.md:56, 06-01-PLAN.md:75, 06-02-PLAN.md:61, 06-03-PLAN.md:55, 06-04-PLAN.md:61, 06-05-PLAN.md:55, 06-06-PLAN.md:57, 06-07-PLAN.md:56, 06-08-PLAN.md:63, 06-09-PLAN.md:51

</details>

<details>
<summary><code>CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE</code> — SKIPPED: explicitly produced by this phase</summary>

06-03-PLAN.md:64 — NEW fields: CrudViewsSettings.form_actions_label_mode (CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE), ViewSet.form_actions_label_mode, CrudView.cv_form_actions_label_mode. NEW public resolver: CrudView.cv_get_form_actions_label_mode(). Existing cv_get_action_label_mode gains location='form'. Private owner-recovery helpers are internal, not promised public names.

All citations: 06-03-PLAN.md:64

</details>

<details>
<summary><code>CRUD_VIEWS_LABEL_MODE_DEFAULTS</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `tests/test1/test_card_label_mode_render.py:292` — `settings.CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"card": floor}`; `tests/test1/test_card_label_mode_render.py:335` — `settings.CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"card": floor}`</summary>

06-08-PLAN.md:110 — Add one coherent Unreleased Breaking entry and a Form buttons migration section in the same commit, covering input-to-button selectors, literal values replacing template evaluation, and cv_* custom-template context replacing input.value. Include exact preserved payload/name/ID behavior and custom-template/helper migration links. Document reserved-attribute collision rules and intentional missing-icon fallback. Set CRUD_VIEWS_LABEL_MODE_DEFAULTS form=both in the example, merging with its existing configured locations; show submit/delete/cancel and filter controls. Add public icon/helper/settings additions to the appropriate changelog section without splitting the Breaking/migration pair. Keep downstream names out of all newly authored files; detailed generic follow-up goes into 06-09 acceptance.

All citations: 06-08-PLAN.md:110

</details>

<details>
<summary><code>Check</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `src/crud_views/lib/check.py:24` — `class Check(BaseModel):`</summary>

06-01-PLAN.md:83 — Check the prerequisite before writing the spec. At planning time local main was 38b0100 and did not contain

All citations: 06-01-PLAN.md:83, 06-01-PLAN.md:202, 06-06-PLAN.md:80, 06-09-PLAN.md:83

</details>

<details>
<summary><code>Context</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `.venv/lib/python3.12/site-packages/django/template/context.py:138` — `class Context(BaseContext):`</summary>

06-01-PLAN.md:105 — Define owner recovery from Django Context.dicts before flattening: form.cv_view first; current helper view

All citations: 06-01-PLAN.md:105, 06-02-PLAN.md:108, 06-03-PLAN.md:94, 06-03-PLAN.md:99, 06-09-PLAN.md:112, 06-09-PLAN.md:155

</details>

<details>
<summary><code>Context.dicts</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `.venv/lib/python3.12/site-packages/django/template/context.py:34` — `self.dicts = [builtins]`; `.venv/lib/python3.12/site-packages/django/template/context.py:44` — `duplicate.dicts = self.dicts[:]`; `.venv/lib/python3.12/site-packages/django/template/context.py:54` — `dicts = []`</summary>

06-01-PLAN.md:105 — Define owner recovery from Django Context.dicts before flattening: form.cv_view first; current helper view

All citations: 06-01-PLAN.md:105, 06-03-PLAN.md:99

</details>

<details>
<summary><code>CrispyDeleteForm</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `src/crud_views/lib/crispy/form.py:116` — `class CrispyDeleteForm(CrispyForm):`</summary>

06-04-PLAN.md:70 — NEW class-table keys: form:hidden-label and form:icon-host. NEW registry names: save, cancel, filter-reset. NEW form attributes: CrispyFormMixin.submit_icon='save', CrispyDeleteForm.delete_icon='delete', WorkflowForm.submit_icon='workflow'. NEW adapter icon= keyword is consumed as rendering configuration, never serialized as an HTML attribute; omission selects kind default while explicit None/empty suppresses it.

All citations: 06-04-PLAN.md:70

</details>

<details>
<summary><code>CrispyDeleteForm.delete_icon</code> — SKIPPED: explicitly produced by this phase</summary>

06-04-PLAN.md:70 — NEW class-table keys: form:hidden-label and form:icon-host. NEW registry names: save, cancel, filter-reset. NEW form attributes: CrispyFormMixin.submit_icon='save', CrispyDeleteForm.delete_icon='delete', WorkflowForm.submit_icon='workflow'. NEW adapter icon= keyword is consumed as rendering configuration, never serialized as an HTML attribute; omission selects kind default while explicit None/empty suppresses it.

All citations: 06-04-PLAN.md:70

</details>

<details>
<summary><code>CrispyFormMixin</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `src/crud_views/lib/crispy/form.py:11` — `class CrispyFormMixin:`</summary>

06-04-PLAN.md:70 — NEW class-table keys: form:hidden-label and form:icon-host. NEW registry names: save, cancel, filter-reset. NEW form attributes: CrispyFormMixin.submit_icon='save', CrispyDeleteForm.delete_icon='delete', WorkflowForm.submit_icon='workflow'. NEW adapter icon= keyword is consumed as rendering configuration, never serialized as an HTML attribute; omission selects kind default while explicit None/empty suppresses it.

All citations: 06-04-PLAN.md:70, 06-04-PLAN.md:106

</details>

<details>
<summary><code>CrispyFormMixin.submit_icon</code> — SKIPPED: explicitly produced by this phase</summary>

06-04-PLAN.md:70 — NEW class-table keys: form:hidden-label and form:icon-host. NEW registry names: save, cancel, filter-reset. NEW form attributes: CrispyFormMixin.submit_icon='save', CrispyDeleteForm.delete_icon='delete', WorkflowForm.submit_icon='workflow'. NEW adapter icon= keyword is consumed as rendering configuration, never serialized as an HTML attribute; omission selects kind default while explicit None/empty suppresses it.

All citations: 06-04-PLAN.md:70

</details>

<details>
<summary><code>CrudView</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `src/crud_views/lib/view/base.py:61` — `class CrudView(metaclass=CrudViewMetaClass):`</summary>

06-03-PLAN.md:64 — NEW fields: CrudViewsSettings.form_actions_label_mode (CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE), ViewSet.form_actions_label_mode, CrudView.cv_form_actions_label_mode. NEW public resolver: CrudView.cv_get_form_actions_label_mode(). Existing cv_get_action_label_mode gains location='form'. Private owner-recovery helpers are internal, not promised public names.

All citations: 06-03-PLAN.md:64, 06-03-PLAN.md:99, 06-06-PLAN.md:101

</details>

<details>
<summary><code>CrudView.checks</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); no authoritative declaration claim; runtime/property/CLI/browser or framework contract requires execution-time confirmation</summary>

06-06-PLAN.md:101 — Introduce a static form checker wired from CrudView.checks. Inspect only concrete statically selected form classes that inherit package defaults and whose relevant button/kwargs hooks retain the package implementation; inherited class submit_icon/delete_icon attributes are knowable. For filter helpers inspect the configured helper class only when its default get_form_actions is inherited; do not instantiate a form/helper, call get_form_class(request), or execute custom action hooks. Unknown/custom providers skip static icon inference and must be covered by runtime normalization. Resolve form mode through the same public resolver; catch ValueError only around mode resolution so E108/E210/E211 survive strict checking. Form static missing means icon is None or empty; named-but-unregistered icons retain the icon registry's separate diagnostics.

All citations: 06-06-PLAN.md:101

</details>

<details>
<summary><code>CrudView.cv_form_actions_label_mode</code> — SKIPPED: explicitly produced by this phase</summary>

06-03-PLAN.md:64 — NEW fields: CrudViewsSettings.form_actions_label_mode (CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE), ViewSet.form_actions_label_mode, CrudView.cv_form_actions_label_mode. NEW public resolver: CrudView.cv_get_form_actions_label_mode(). Existing cv_get_action_label_mode gains location='form'. Private owner-recovery helpers are internal, not promised public names.

All citations: 06-03-PLAN.md:64

</details>

<details>
<summary><code>CrudView.cv_get_form_actions_label_mode</code> — SKIPPED: explicitly produced by this phase</summary>

06-03-PLAN.md:64 — NEW fields: CrudViewsSettings.form_actions_label_mode (CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE), ViewSet.form_actions_label_mode, CrudView.cv_form_actions_label_mode. NEW public resolver: CrudView.cv_get_form_actions_label_mode(). Existing cv_get_action_label_mode gains location='form'. Private owner-recovery helpers are internal, not promised public names.

All citations: 06-03-PLAN.md:64

</details>

<details>
<summary><code>CrudViewsSettings</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `src/crud_views/lib/settings.py:17` — `class CrudViewsSettings(BaseModel):`</summary>

06-03-PLAN.md:64 — NEW fields: CrudViewsSettings.form_actions_label_mode (CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE), ViewSet.form_actions_label_mode, CrudView.cv_form_actions_label_mode. NEW public resolver: CrudView.cv_get_form_actions_label_mode(). Existing cv_get_action_label_mode gains location='form'. Private owner-recovery helpers are internal, not promised public names.

All citations: 06-03-PLAN.md:64

</details>

<details>
<summary><code>CrudViewsSettings.form_actions_label_mode</code> — SKIPPED: explicitly produced by this phase</summary>

06-03-PLAN.md:64 — NEW fields: CrudViewsSettings.form_actions_label_mode (CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE), ViewSet.form_actions_label_mode, CrudView.cv_form_actions_label_mode. NEW public resolver: CrudView.cv_get_form_actions_label_mode(). Existing cv_get_action_label_mode gains location='form'. Private owner-recovery helpers are internal, not promised public names.

All citations: 06-03-PLAN.md:64

</details>

<details>
<summary><code>DEFAULT_BUTTON_CLASSES</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `src/crud_views/lib/button_classes.py:15` — `DEFAULT_BUTTON_CLASSES: dict[str, str | None] = {`</summary>

06-08-PLAN.md:80 — Replace obsolete statements that form controls never choose modes or render icons. Document the separate FORM_LEAF_KEYS contract, cancel-only URL, cv_css_class/cv_flat_attrs, literal text boundary, class mode lookup and form utility keys. Keep the canonical form resolution order in action_menus.md: first select owner (D-09–D-12), then whole view/ViewSet/settings map, then lazy floor for a missing key. Add the Form column and getter, and extend the single merge/replace table in settings.md rather than duplicating resolution prose across pages. State empty map versus None precisely. Preserve the class grammar and update its live default-key count from DEFAULT_BUTTON_CLASSES. Extend existing meaningful doc/recipe tests to render a documented form configuration, proving both/icon output rather than checking strings alone.

All citations: 06-08-PLAN.md:80

</details>

<details>
<summary><code>DEFAULT_ICONS</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `src/crud_views/lib/icons.py:14` — `DEFAULT_ICONS: dict[str, str] = {`</summary>

06-04-PLAN.md:85 — Add save, cancel and filter-reset to DEFAULT_ICONS and BOOTSTRAP_ICONS with matching semantic meanings. Add form:hidden-label='visually-hidden' and form:icon-host following the existing host composition grammar. Ensure the leaf reads mode classes through cv_button_class and the utility keys through their dedicated lookups; host classes must be escaped as attributes. Label mode suppresses all icon output and host classes, both emits icon plus text without generated tooltip, icon emits hidden text/title/form tooltip. Cover renderer prefix variants and explicit host opt-out, a Unicode/lazy label, an empty label, and repeated renders with changed registry/settings. Extend the real host/leaf tests for finite kind grammar and utility keys; keep the existing live default-key count guard satisfied by the count update described above.

All citations: 06-04-PLAN.md:85

</details>

<details>
<summary><code>FORM_KINDS</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `src/crud_views/lib/button_classes.py:210` — `FORM_KINDS: frozenset[str] = frozenset({"submit", "cancel", "delete", "filter-submit", "filter-reset"})`; `tests/test1/test_button_classes_checks.py:111` — `FORM_KINDS = ("submit", "cancel", "delete", "filter-submit", "filter-reset")`</summary>

06-01-PLAN.md:86 — contracts: default_label_mode with the shared defaults and independent FORM_KINDS/VARIANT_LOCATIONS.

All citations: 06-01-PLAN.md:86, 06-02-PLAN.md:85, 06-04-PLAN.md:27, 06-06-PLAN.md:37, 06-06-PLAN.md:80

</details>

<details>
<summary><code>FORM_LEAF_KEYS</code> — SKIPPED: explicitly produced by this phase</summary>

06-01-PLAN.md:92 — 06-02 through 06-06. Set separate FORM_LEAF_KEYS, preserving LEAF_KEYS; define type/name/value/id/key,

All citations: 06-01-PLAN.md:92, 06-02-PLAN.md:70, 06-02-PLAN.md:85, 06-06-PLAN.md:102, 06-08-PLAN.md:80, 06-09-PLAN.md:154

</details>

<details>
<summary><code>FormActions</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `.venv/lib/python3.12/site-packages/crispy_forms/bootstrap.py:259` — `class FormActions(LayoutObject):`</summary>

06-01-PLAN.md:112 — Define get_form_actions returning FormActions or None; None means no group, empty FormActions is retained.

All citations: 06-01-PLAN.md:112, 06-02-PLAN.md:79, 06-05-PLAN.md:24, 06-05-PLAN.md:38, 06-05-PLAN.md:64, 06-05-PLAN.md:68, 06-05-PLAN.md:74, 06-05-PLAN.md:94, 06-05-PLAN.md:99, 06-08-PLAN.md:29, 06-08-PLAN.md:95, 06-09-PLAN.md:193

</details>

<details>
<summary><code>FormData</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); no authoritative declaration claim; runtime/property/CLI/browser or framework contract requires execution-time confirmation</summary>

06-01-PLAN.md:119 — jsdom native SubmitEvent/FormData requires acceptance on the reconciled locked environment. The expanded

All citations: 06-01-PLAN.md:119, 06-07-PLAN.md:27, 06-07-PLAN.md:36, 06-07-PLAN.md:74, 06-07-PLAN.md:80, 06-07-PLAN.md:84, 06-07-PLAN.md:137, 06-09-PLAN.md:161, 06-09-PLAN.md:189

</details>

<details>
<summary><code>FormHelper</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `.venv/lib/python3.12/site-packages/crispy_forms/helper.py:106` — `class FormHelper(DynamicLayoutHandler):`</summary>

06-03-PLAN.md:91 — <read_first>06-SPEC.md ownership contract; installed crispy BasicNode.get_render/FormHelper.get_attributes; tests/test1/test_crispy_buttons.py</read_first>

All citations: 06-03-PLAN.md:91, 06-05-PLAN.md:78

</details>

<details>
<summary><code>FormHelper.get_attributes</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `.venv/lib/python3.12/site-packages/crispy_forms/helper.py:290` — `def get_attributes(self, template_pack=TEMPLATE_PACK):`</summary>

06-03-PLAN.md:91 — <read_first>06-SPEC.md ownership contract; installed crispy BasicNode.get_render/FormHelper.get_attributes; tests/test1/test_crispy_buttons.py</read_first>

All citations: 06-03-PLAN.md:91

</details>

<details>
<summary><code>Hidden</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `.venv/lib/python3.12/site-packages/crispy_forms/layout.py:390` — `class Hidden(BaseInput):`</summary>

06-04-PLAN.md:35 — provides: Hidden-label and host utility keys

All citations: 06-04-PLAN.md:35, 06-05-PLAN.md:78, 06-09-PLAN.md:185

</details>

<details>
<summary><code>LABEL_MODE_DEFAULTS</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `src/crud_views/lib/view/label_mode.py:23` — `LABEL_MODE_DEFAULTS: Mapping[str, str] = MappingProxyType({"context": "icon", "list": "icon", "card": "both"})`</summary>

06-02-PLAN.md:85 — Start with a failing real-crispy render test. Add form to LOCATIONS and label to LABEL_MODE_DEFAULTS together. Branch cv_button_data early for form before action URL/modal derivation; retain existing action behavior and LEAF_KEYS. Introduce FORM_LEAF_KEYS for the exact spec contract. Validate cv_key against FORM_KINDS and cv_type against submit/button/reset; invalid caller kind/type raises ValueError. Missing or None textual values normalize to empty text without coercing other falsey data such as numeric zero to empty. Preserve valid empty labels without manufacturing text.

All citations: 06-02-PLAN.md:85, 06-02-PLAN.md:107

</details>

<details>
<summary><code>LEAF_KEYS</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `src/crud_views/lib/view/button_data.py:16` — `LEAF_KEYS = frozenset(`</summary>

06-01-PLAN.md:92 — 06-02 through 06-06. Set separate FORM_LEAF_KEYS, preserving LEAF_KEYS; define type/name/value/id/key,

All citations: 06-01-PLAN.md:92, 06-02-PLAN.md:85

</details>

<details>
<summary><code>LOCATIONS</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `src/crud_views/lib/view/button_data.py:12` — `LOCATIONS = frozenset({"context", "list", "card"})`; `tests/test1/test_button_data.py:9` — `LOCATIONS = ["context", "list", "card"]`</summary>

06-02-PLAN.md:85 — Start with a failing real-crispy render test. Add form to LOCATIONS and label to LABEL_MODE_DEFAULTS together. Branch cv_button_data early for form before action URL/modal derivation; retain existing action behavior and LEAF_KEYS. Introduce FORM_LEAF_KEYS for the exact spec contract. Validate cv_key against FORM_KINDS and cv_type against submit/button/reset; invalid caller kind/type raises ValueError. Missing or None textual values normalize to empty text without coercing other falsey data such as numeric zero to empty. Preserve valid empty labels without manufacturing text.

All citations: 06-02-PLAN.md:85, 06-02-PLAN.md:107

</details>

<details>
<summary><code>Layout</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `.venv/lib/python3.12/site-packages/crispy_forms/layout.py:108` — `class Layout(LayoutObject):`</summary>

06-01-PLAN.md:113 — Deep-copy declared layouts per helper instance. A no-layout helper gets a truthy instance Layout so crispy

All citations: 06-01-PLAN.md:113, 06-02-PLAN.md:79, 06-05-PLAN.md:78

</details>

<details>
<summary><code>ListViewFilterFormHelper</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `src/crud_views/lib/views/list.py:57` — `class ListViewFilterFormHelper(FormHelper):`</summary>

06-05-PLAN.md:64 — NEW public method: ListViewFilterFormHelper.get_form_actions() -> FormActions \| None. NEW render_layout override and private instance layout/action initialization state. No new test files; only existing phase-owned filter golden changes.

All citations: 06-05-PLAN.md:64, 06-08-PLAN.md:95

</details>

<details>
<summary><code>ListViewFilterFormHelper.get_form_actions</code> — SKIPPED: explicitly produced by this phase</summary>

06-05-PLAN.md:64 — NEW public method: ListViewFilterFormHelper.get_form_actions() -> FormActions \| None. NEW render_layout override and private instance layout/action initialization state. No new test files; only existing phase-owned filter golden changes.

All citations: 06-05-PLAN.md:64

</details>

<details>
<summary><code>ListViewTableFilterMixin</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `src/crud_views/lib/views/mixins.py:299` — `class ListViewTableFilterMixin(FilterView):`</summary>

06-05-PLAN.md:78 — Add get_form_actions following the spec. Initialize FormHelper without passing form when preserving declared layout; deep-copy declared layout per instance. Keep a truthy Layout instance for crispy dispatch even for no-layout or None actions; populate no-layout fields from the actual form at render_layout before appending the action group. Preserve the helper's configured layout field order. Build Apply/Reset as package adapters with form:filter-submit/form:filter-reset and original IDs, append exactly once to the isolated layout. Keep Hidden controls on inputs with current GET naming/value logic. During render_layout push the actual helper owner under a private context key so adapters need not inspect a fresh form.helper property; restore context afterward. Keep ListViewTableFilterMixin construction unchanged. Update only filter expectations and its phase-owned golden after comparing old/new payload/control attributes from 06-01.

All citations: 06-05-PLAN.md:78

</details>

<details>
<summary><code>PATTERNS.md</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); no authoritative declaration claim; runtime/property/CLI/browser or framework contract requires execution-time confirmation</summary>

06-01-PLAN.md:58 — @.planning/phases/06-form-button-leaf/06-PATTERNS.md

All citations: 06-01-PLAN.md:58, 06-02-PLAN.md:63, 06-03-PLAN.md:57, 06-04-PLAN.md:63, 06-05-PLAN.md:57, 06-06-PLAN.md:59, 06-07-PLAN.md:58, 06-08-PLAN.md:65, 06-09-PLAN.md:53

</details>

<details>
<summary><code>PROJECT.md</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); no authoritative declaration claim; runtime/property/CLI/browser or framework contract requires execution-time confirmation</summary>

06-01-PLAN.md:52 — @.planning/PROJECT.md

All citations: 06-01-PLAN.md:52, 06-02-PLAN.md:58, 06-03-PLAN.md:52, 06-04-PLAN.md:58, 06-05-PLAN.md:52, 06-06-PLAN.md:54, 06-07-PLAN.md:53, 06-08-PLAN.md:60, 06-09-PLAN.md:48

</details>

<details>
<summary><code>REQUIREMENTS.md</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); no authoritative declaration claim; runtime/property/CLI/browser or framework contract requires execution-time confirmation</summary>

06-01-PLAN.md:55 — @.planning/REQUIREMENTS.md

All citations: 06-01-PLAN.md:55

</details>

<details>
<summary><code>RESEARCH.md</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); no authoritative declaration claim; runtime/property/CLI/browser or framework contract requires execution-time confirmation</summary>

06-01-PLAN.md:57 — @.planning/phases/06-form-button-leaf/06-RESEARCH.md

All citations: 06-01-PLAN.md:57, 06-02-PLAN.md:62, 06-03-PLAN.md:56, 06-04-PLAN.md:62, 06-05-PLAN.md:56, 06-06-PLAN.md:58, 06-07-PLAN.md:57, 06-07-PLAN.md:71, 06-07-PLAN.md:113, 06-08-PLAN.md:64, 06-09-PLAN.md:52

</details>

<details>
<summary><code>ROADMAP.md</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); no authoritative declaration claim; runtime/property/CLI/browser or framework contract requires execution-time confirmation</summary>

06-01-PLAN.md:53 — @.planning/ROADMAP.md

All citations: 06-01-PLAN.md:53, 06-02-PLAN.md:59, 06-03-PLAN.md:53, 06-04-PLAN.md:59, 06-05-PLAN.md:53, 06-06-PLAN.md:55, 06-07-PLAN.md:54, 06-08-PLAN.md:61, 06-09-PLAN.md:49

</details>

<details>
<summary><code>Reset</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `src/crud_views/lib/crispy/buttons.py:29` — `class Reset(_TableClassMixin, layout.Reset):`; `.venv/lib/python3.12/site-packages/crispy_forms/layout.py:447` — `class Reset(BaseInput):`</summary>

06-01-PLAN.md:159 — Extend the capture harness for workflow submit/cancel and filter Apply/Reset plus hidden sort/order/direction

All citations: 06-01-PLAN.md:159, 06-02-PLAN.md:101, 06-05-PLAN.md:25, 06-05-PLAN.md:72, 06-05-PLAN.md:78, 06-07-PLAN.md:96, 06-09-PLAN.md:194

</details>

<details>
<summary><code>SPEC.md</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); no authoritative declaration claim; runtime/property/CLI/browser or framework contract requires execution-time confirmation</summary>

06-01-PLAN.md:8 — - .planning/phases/06-form-button-leaf/06-SPEC.md

All citations: 06-01-PLAN.md:8, 06-01-PLAN.md:29, 06-01-PLAN.md:64, 06-01-PLAN.md:73, 06-01-PLAN.md:134, 06-01-PLAN.md:157, 06-02-PLAN.md:64, 06-03-PLAN.md:58, 06-03-PLAN.md:70, 06-03-PLAN.md:91, 06-04-PLAN.md:64, 06-05-PLAN.md:58, 06-05-PLAN.md:70, 06-06-PLAN.md:60, 06-06-PLAN.md:93, 06-07-PLAN.md:59, 06-08-PLAN.md:66, 06-08-PLAN.md:78, 06-09-PLAN.md:54, 06-09-PLAN.md:66

</details>

<details>
<summary><code>STATE.md</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); no authoritative declaration claim; runtime/property/CLI/browser or framework contract requires execution-time confirmation</summary>

06-01-PLAN.md:54 — @.planning/STATE.md

All citations: 06-01-PLAN.md:54, 06-02-PLAN.md:60, 06-03-PLAN.md:54, 06-04-PLAN.md:60, 06-05-PLAN.md:54, 06-06-PLAN.md:56, 06-07-PLAN.md:55, 06-08-PLAN.md:62, 06-09-PLAN.md:50

</details>

<details>
<summary><code>SUMMARY.md</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); no authoritative declaration claim; runtime/property/CLI/browser or framework contract requires execution-time confirmation</summary>

06-01-PLAN.md:205 — Create .planning/phases/06-form-button-leaf/06-01-SUMMARY.md with prerequisite and baseline commit evidence.

All citations: 06-01-PLAN.md:205, 06-02-PLAN.md:77, 06-02-PLAN.md:121, 06-02-PLAN.md:154, 06-03-PLAN.md:128, 06-04-PLAN.md:135, 06-05-PLAN.md:129, 06-06-PLAN.md:132, 06-07-PLAN.md:145, 06-08-PLAN.md:139, 06-09-PLAN.md:66, 06-09-PLAN.md:81, 06-09-PLAN.md:258

</details>

<details>
<summary><code>SafeData</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `.venv/lib/python3.12/site-packages/django/utils/safestring.py:13` — `class SafeData:`</summary>

06-01-PLAN.md:94 — Normalize text to a plain str that has no SafeData trust marker before exactly one Django escaping boundary;

All citations: 06-01-PLAN.md:94, 06-02-PLAN.md:86

</details>

<details>
<summary><code>SafeString</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `.venv/lib/python3.12/site-packages/django/utils/safestring.py:25` — `class SafeString(str, SafeData):`</summary>

06-02-PLAN.md:30 — - "D-15: Empty, Unicode, lazy, SafeString and template-looking values remain exact literal DOM text and values; none evaluates template syntax or creates injected nodes/attributes."

All citations: 06-02-PLAN.md:30, 06-02-PLAN.md:103, 06-02-PLAN.md:145, 06-09-PLAN.md:156, 06-09-PLAN.md:191

</details>

<details>
<summary><code>Submit</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `src/crud_views/lib/crispy/buttons.py:21` — `class Submit(_TableClassMixin, layout.Submit):`; `.venv/lib/python3.12/site-packages/crispy_forms/layout.py:262` — `class Submit(BaseInput):`</summary>

06-02-PLAN.md:29 — - "D-13, D-14: A standalone package Submit renders a real button through cv_button_data(ctx, 'form'), with label as the lazy form floor and finite kind semantics."

All citations: 06-02-PLAN.md:29, 06-02-PLAN.md:48, 06-02-PLAN.md:74, 06-02-PLAN.md:101, 06-03-PLAN.md:72, 06-05-PLAN.md:99

</details>

<details>
<summary><code>SubmitEvent</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); no authoritative declaration claim; runtime/property/CLI/browser or framework contract requires execution-time confirmation</summary>

06-01-PLAN.md:119 — jsdom native SubmitEvent/FormData requires acceptance on the reconciled locked environment. The expanded

All citations: 06-01-PLAN.md:119, 06-07-PLAN.md:27, 06-07-PLAN.md:36, 06-07-PLAN.md:73, 06-07-PLAN.md:80, 06-09-PLAN.md:161

</details>

<details>
<summary><code>SubmitEvent.submitter</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); no authoritative declaration claim; runtime/property/CLI/browser or framework contract requires execution-time confirmation</summary>

06-07-PLAN.md:27 — - "The native SubmitEvent.submitter and FormData contract is tested on exact locked JS packages under a compatible isolated runtime, without hiding failure through mocks/polyfills."

All citations: 06-07-PLAN.md:27, 06-07-PLAN.md:73

</details>

<details>
<summary><code>TemplateNameMixin</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `.venv/lib/python3.12/site-packages/crispy_forms/layout.py:18` — `class TemplateNameMixin:`</summary>

06-02-PLAN.md:99 — <read_first>The spec literal/attribute rules; crispy BaseInput and TemplateNameMixin in the declared-floor environment; tests/test1/test_button_leaves.py</read_first>

All citations: 06-02-PLAN.md:99

</details>

<details>
<summary><code>VALIDATION.md</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); no authoritative declaration claim; runtime/property/CLI/browser or framework contract requires execution-time confirmation</summary>

06-01-PLAN.md:59 — @.planning/phases/06-form-button-leaf/06-VALIDATION.md

All citations: 06-01-PLAN.md:59, 06-09-PLAN.md:9, 06-09-PLAN.md:26, 06-09-PLAN.md:32, 06-09-PLAN.md:60, 06-09-PLAN.md:65, 06-09-PLAN.md:66, 06-09-PLAN.md:80, 06-09-PLAN.md:81

</details>

<details>
<summary><code>VARIANT_LOCATIONS</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `src/crud_views/lib/button_classes.py:209` — `VARIANT_LOCATIONS: frozenset[str] = frozenset({"context", "list", "card"})`</summary>

06-01-PLAN.md:86 — contracts: default_label_mode with the shared defaults and independent FORM_KINDS/VARIANT_LOCATIONS.

All citations: 06-01-PLAN.md:86

</details>

<details>
<summary><code>ValueError</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); no authoritative declaration claim; runtime/property/CLI/browser or framework contract requires execution-time confirmation</summary>

06-02-PLAN.md:85 — Start with a failing real-crispy render test. Add form to LOCATIONS and label to LABEL_MODE_DEFAULTS together. Branch cv_button_data early for form before action URL/modal derivation; retain existing action behavior and LEAF_KEYS. Introduce FORM_LEAF_KEYS for the exact spec contract. Validate cv_key against FORM_KINDS and cv_type against submit/button/reset; invalid caller kind/type raises ValueError. Missing or None textual values normalize to empty text without coercing other falsey data such as numeric zero to empty. Preserve valid empty labels without manufacturing text.

All citations: 06-02-PLAN.md:85, 06-06-PLAN.md:26, 06-06-PLAN.md:101, 06-06-PLAN.md:102

</details>

<details>
<summary><code>ViewSet</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `src/crud_views/lib/viewset/__init__.py:45` — `class ViewSet(BaseModel):`</summary>

06-03-PLAN.md:23 — - "D-13: Form mode maps select view, else ViewSet, else setting as whole maps; an empty selected map and missing kind fall directly to the live form floor."

All citations: 06-03-PLAN.md:23, 06-03-PLAN.md:64, 06-03-PLAN.md:72, 06-03-PLAN.md:84, 06-06-PLAN.md:76, 06-06-PLAN.md:80, 06-06-PLAN.md:86, 06-08-PLAN.md:80, 06-09-PLAN.md:205

</details>

<details>
<summary><code>ViewSet.form_actions_label_mode</code> — SKIPPED: explicitly produced by this phase</summary>

06-03-PLAN.md:64 — NEW fields: CrudViewsSettings.form_actions_label_mode (CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE), ViewSet.form_actions_label_mode, CrudView.cv_form_actions_label_mode. NEW public resolver: CrudView.cv_get_form_actions_label_mode(). Existing cv_get_action_label_mode gains location='form'. Private owner-recovery helpers are internal, not promised public names.

All citations: 06-03-PLAN.md:64

</details>

<details>
<summary><code>WorkflowForm</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `src/crud_views_workflow/lib/forms.py:11` — `class WorkflowForm(CrispyForm):`</summary>

06-04-PLAN.md:70 — NEW class-table keys: form:hidden-label and form:icon-host. NEW registry names: save, cancel, filter-reset. NEW form attributes: CrispyFormMixin.submit_icon='save', CrispyDeleteForm.delete_icon='delete', WorkflowForm.submit_icon='workflow'. NEW adapter icon= keyword is consumed as rendering configuration, never serialized as an HTML attribute; omission selects kind default while explicit None/empty suppresses it.

All citations: 06-04-PLAN.md:70

</details>

<details>
<summary><code>WorkflowForm.submit_icon</code> — SKIPPED: explicitly produced by this phase</summary>

06-04-PLAN.md:70 — NEW class-table keys: form:hidden-label and form:icon-host. NEW registry names: save, cancel, filter-reset. NEW form attributes: CrispyFormMixin.submit_icon='save', CrispyDeleteForm.delete_icon='delete', WorkflowForm.submit_icon='workflow'. NEW adapter icon= keyword is consumed as rendering configuration, never serialized as an HTML attribute; omission selects kind default while explicit None/empty suppresses it.

All citations: 06-04-PLAN.md:70

</details>

<details>
<summary><code>_action_settings_messages</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `src/crud_views/lib/settings.py:100` — `def _action_settings_messages(self) -> list[CheckMessage]:`</summary>

06-06-PLAN.md:72 — <read_first>src/crud_views/lib/view/action_menu.py; src/crud_views/lib/view/base.py (checks); src/crud_views/lib/settings.py (_action_settings_messages); src/crud_views/lib/viewset/__init__.py (map validator); tests/test1/test_action_label_mode_config.py</read_first>

All citations: 06-06-PLAN.md:72

</details>

<details>
<summary><code>action_menu</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); module/file reference resolved in path inventory</summary>

06-06-PLAN.md:11 — - src/crud_views/lib/view/action_menu.py

All citations: 06-06-PLAN.md:11, 06-06-PLAN.md:36, 06-06-PLAN.md:71, 06-06-PLAN.md:72

</details>

<details>
<summary><code>action_menus</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); module/file reference resolved in path inventory</summary>

06-08-PLAN.md:10 — - docs/reference/action_menus.md

All citations: 06-08-PLAN.md:10, 06-08-PLAN.md:41, 06-08-PLAN.md:77, 06-08-PLAN.md:78, 06-08-PLAN.md:80

</details>

<details>
<summary><code>add_input</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `.venv/lib/python3.12/site-packages/crispy_forms/helper.py:260` — `def add_input(self, input_object):`</summary>

06-05-PLAN.md:22 — - "D-01, D-02: Custom add_input controls remain legacy inputs quietly; hidden sort/order/direction inputs keep their current path and values."

All citations: 06-05-PLAN.md:22, 06-05-PLAN.md:96, 06-05-PLAN.md:99, 06-08-PLAN.md:95

</details>

<details>
<summary><code>button_classes</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); module/file reference resolved in path inventory</summary>

06-04-PLAN.md:8 — - src/crud_views/lib/button_classes.py

All citations: 06-04-PLAN.md:8, 06-04-PLAN.md:34, 06-04-PLAN.md:43, 06-04-PLAN.md:75, 06-04-PLAN.md:76

</details>

<details>
<summary><code>button_data</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); module/file reference resolved in path inventory</summary>

06-01-PLAN.md:79 — src/crud_views/lib/view/button_data.py; src/crud_views/lib/view/label_mode.py;

All citations: 06-01-PLAN.md:79, 06-02-PLAN.md:8, 06-02-PLAN.md:36, 06-02-PLAN.md:40, 06-02-PLAN.md:42, 06-02-PLAN.md:70, 06-02-PLAN.md:76, 06-02-PLAN.md:77, 06-02-PLAN.md:98, 06-06-PLAN.md:14, 06-06-PLAN.md:39, 06-06-PLAN.md:92, 06-06-PLAN.md:93

</details>

<details>
<summary><code>check_viewsets</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `src/crud_views/checks.py:20` — `def check_viewsets(app_configs=None, **kwargs):`</summary>

06-06-PLAN.md:28 — - "Empty and non-ASCII invalid keys/values yield deterministic diagnostics; malformed floor/map errors survive check_viewsets and are never hidden by W292."

All citations: 06-06-PLAN.md:28, 06-06-PLAN.md:74, 06-06-PLAN.md:80

</details>

<details>
<summary><code>crispy_floor</code> — SKIPPED: explicitly produced by this phase</summary>

06-07-PLAN.md:65 — NEW nox session: crispy_floor, Python 3.12 with Django 4.2 and 6.0 variants and exact crispy 2.0/bootstrap5 2023.10 pins. Existing JS source files are conditional bug-fix ownership only; leave them byte-identical if the new regression tests pass.

All citations: 06-07-PLAN.md:65, 06-07-PLAN.md:115, 06-07-PLAN.md:118, 06-07-PLAN.md:142

</details>

<details>
<summary><code>crud_views</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); module/file reference resolved in path inventory</summary>

06-01-PLAN.md:77 — src/crud_views/lib/crispy/buttons.py; src/crud_views/lib/crispy/form.py;

All citations: 06-01-PLAN.md:77, 06-01-PLAN.md:78, 06-01-PLAN.md:79, 06-02-PLAN.md:8, 06-02-PLAN.md:9, 06-02-PLAN.md:10, 06-02-PLAN.md:11, 06-02-PLAN.md:34, 06-02-PLAN.md:36, 06-02-PLAN.md:39, 06-02-PLAN.md:40, 06-02-PLAN.md:42, 06-02-PLAN.md:43, 06-02-PLAN.md:70, 06-02-PLAN.md:76, 06-02-PLAN.md:77, 06-02-PLAN.md:98, 06-03-PLAN.md:8, 06-03-PLAN.md:9, 06-03-PLAN.md:10, 06-03-PLAN.md:11, 06-03-PLAN.md:28, 06-03-PLAN.md:30, 06-03-PLAN.md:33, 06-03-PLAN.md:34, 06-03-PLAN.md:36, 06-03-PLAN.md:37, 06-03-PLAN.md:69, 06-03-PLAN.md:70, 06-03-PLAN.md:90, 06-04-PLAN.md:8, 06-04-PLAN.md:9, 06-04-PLAN.md:10, 06-04-PLAN.md:13, 06-04-PLAN.md:15, 06-04-PLAN.md:32, 06-04-PLAN.md:34, 06-04-PLAN.md:39, 06-04-PLAN.md:40, 06-04-PLAN.md:42, 06-04-PLAN.md:43, 06-04-PLAN.md:75, 06-04-PLAN.md:76, 06-04-PLAN.md:97, 06-04-PLAN.md:98, 06-05-PLAN.md:8, 06-05-PLAN.md:28, 06-05-PLAN.md:33, 06-05-PLAN.md:34, 06-05-PLAN.md:36, 06-05-PLAN.md:37, 06-05-PLAN.md:69, 06-05-PLAN.md:70, 06-05-PLAN.md:90, 06-06-PLAN.md:8, 06-06-PLAN.md:9, 06-06-PLAN.md:10, 06-06-PLAN.md:11, 06-06-PLAN.md:13, 06-06-PLAN.md:14, 06-06-PLAN.md:32, 06-06-PLAN.md:35, 06-06-PLAN.md:36, 06-06-PLAN.md:38, 06-06-PLAN.md:39, 06-06-PLAN.md:71, 06-06-PLAN.md:72, 06-06-PLAN.md:92, 06-06-PLAN.md:93, 06-07-PLAN.md:9, 06-07-PLAN.md:12, 06-07-PLAN.md:13, 06-07-PLAN.md:34, 06-07-PLAN.md:70, 06-07-PLAN.md:71, 06-07-PLAN.md:92, 06-07-PLAN.md:93

</details>

<details>
<summary><code>crud_views_workflow</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); module/file reference resolved in path inventory</summary>

06-04-PLAN.md:14 — - src/crud_views_workflow/lib/forms.py

All citations: 06-04-PLAN.md:14, 06-04-PLAN.md:36, 06-04-PLAN.md:97, 06-04-PLAN.md:98

</details>

<details>
<summary><code>css_class</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `src/crud_views/lib/crispy/table.py:5` — `css_class = "col-md-1"`; `src/crud_views/lib/crispy/table.py:9` — `css_class = "col-md-2"`; `src/crud_views/lib/crispy/table.py:13` — `css_class = "col-md-3"`</summary>

06-01-PLAN.md:98 — otherwise extra id wins over generated id; class-table classes then css_class then extra class are appended

All citations: 06-01-PLAN.md:98

</details>

<details>
<summary><code>css_id</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `.venv/lib/python3.12/site-packages/crispy_forms/bootstrap.py:1117` — `self.css_id = css_id`; `.venv/lib/python3.12/site-packages/crispy_forms/bootstrap.py:607` — `self.css_id = slugify(self.name, allow_unicode=True)`; `.venv/lib/python3.12/site-packages/crispy_forms/bootstrap.py:882` — `self.css_id = "-".join(["accordion", str(randint(1000, 9999))])`</summary>

06-01-PLAN.md:97 — Define reserved attributes once: adapter type and positional name/value win; css_id wins over extra id,

All citations: 06-01-PLAN.md:97

</details>

<details>
<summary><code>cv_button_class</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `src/crud_views_object_detail/templatetags/crud_views_object_detail.py:108` — `def cv_button_class(location, slot, mode=None):`; `src/crud_views/templatetags/crud_views.py:525` — `def cv_button_class(location, slot, mode=None):`</summary>

06-02-PLAN.md:86 — Implement adapter render without calling BaseInput.render: retain raw value and kwargs, normalize per spec, render the selected leaf through a scoped context copy. Strip inherited input aliases from the template context, never expose the adapter object. Normalize SafeData and lazy values at render time to ordinary strings then use Django autoescaping once; serialized extra attrs are escaped once separately. Preserve constructor signature, slot-selected semantic kind, upstream generated IDs and legacy field_classes/flat_attrs for helper.inputs. Do not infer kind from the submitted name. The leaf uses cv_button_class form/cv_key/cv_label_mode, appends cv_css_class and host classes, and renders the three bodies with cancel URL only for cancel. Keep normalizer/icon behavior extensible for 06-04 rather than hardcoding a temporary floor. Update existing input-only assertions only where layout buttons changed; filter helper inputs remain inputs until 06-05.

All citations: 06-02-PLAN.md:86, 06-04-PLAN.md:85

</details>

<details>
<summary><code>cv_button_data</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `src/crud_views/lib/view/button_data.py:52` — `def cv_button_data(ctx: dict, location: str, kind: str = "action") -> dict:`</summary>

06-02-PLAN.md:29 — - "D-13, D-14: A standalone package Submit renders a real button through cv_button_data(ctx, 'form'), with label as the lazy form floor and finite kind semantics."

All citations: 06-02-PLAN.md:29, 06-02-PLAN.md:85, 06-06-PLAN.md:102

</details>

<details>
<summary><code>cv_cancel_url</code> — SKIPPED: explicitly produced by this phase</summary>

06-02-PLAN.md:70 — NEW template: src/crud_views/templates/crud_views/tags/button/form.html. NEW symbol: FORM_LEAF_KEYS in button_data.py. NEW normalized fields: cv_type, cv_name, cv_value, cv_id, cancel-only cv_cancel_url, cv_css_class, cv_flat_attrs; existing label/icon fields are reused. Private helper names are implementation-local. No new external package.

All citations: 06-02-PLAN.md:70

</details>

<details>
<summary><code>cv_css_class</code> — SKIPPED: explicitly produced by this phase</summary>

06-01-PLAN.md:93 — literal strings, cancel-only URL, mode/icon fields, cv_css_class suffix and cv_flat_attrs serialization.

All citations: 06-01-PLAN.md:93, 06-02-PLAN.md:70, 06-02-PLAN.md:86, 06-08-PLAN.md:80

</details>

<details>
<summary><code>cv_first_inline_keys</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `src/crud_views/lib/view/base.py:263` — `def cv_first_inline_keys(cls, view_value, viewset_field: str):`</summary>

06-03-PLAN.md:38 — via: cv_first_inline_keys selects one map

All citations: 06-03-PLAN.md:38, 06-03-PLAN.md:70, 06-03-PLAN.md:78

</details>

<details>
<summary><code>cv_flat_attrs</code> — SKIPPED: explicitly produced by this phase</summary>

06-01-PLAN.md:93 — literal strings, cancel-only URL, mode/icon fields, cv_css_class suffix and cv_flat_attrs serialization.

All citations: 06-01-PLAN.md:93, 06-02-PLAN.md:70, 06-08-PLAN.md:80, 06-08-PLAN.md:95

</details>

<details>
<summary><code>cv_form_actions_label_mode</code> — SKIPPED: explicitly produced by this phase</summary>

06-03-PLAN.md:64 — NEW fields: CrudViewsSettings.form_actions_label_mode (CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE), ViewSet.form_actions_label_mode, CrudView.cv_form_actions_label_mode. NEW public resolver: CrudView.cv_get_form_actions_label_mode(). Existing cv_get_action_label_mode gains location='form'. Private owner-recovery helpers are internal, not promised public names.

All citations: 06-03-PLAN.md:64

</details>

<details>
<summary><code>cv_form_icon_mode_checks</code> — SKIPPED: explicitly produced by this phase</summary>

06-06-PLAN.md:66 — NEW test file: tests/test1/test_form_button_checks.py. NEW private/static form icon checker in view/buttons.py (suggested cv_form_icon_mode_checks). No new check IDs. Finite form contract tests live in this file or existing test_button_data.py read-only coverage; no new generic diagnostic framework.

All citations: 06-06-PLAN.md:66

</details>

<details>
<summary><code>cv_get_action_label_mode</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `src/crud_views/lib/view/base.py:299` — `def cv_get_action_label_mode(`</summary>

06-03-PLAN.md:64 — NEW fields: CrudViewsSettings.form_actions_label_mode (CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE), ViewSet.form_actions_label_mode, CrudView.cv_form_actions_label_mode. NEW public resolver: CrudView.cv_get_form_actions_label_mode(). Existing cv_get_action_label_mode gains location='form'. Private owner-recovery helpers are internal, not promised public names.

All citations: 06-03-PLAN.md:64, 06-03-PLAN.md:70, 06-03-PLAN.md:78

</details>

<details>
<summary><code>cv_get_form_actions_label_mode</code> — SKIPPED: explicitly produced by this phase</summary>

06-03-PLAN.md:64 — NEW fields: CrudViewsSettings.form_actions_label_mode (CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE), ViewSet.form_actions_label_mode, CrudView.cv_form_actions_label_mode. NEW public resolver: CrudView.cv_get_form_actions_label_mode(). Existing cv_get_action_label_mode gains location='form'. Private owner-recovery helpers are internal, not promised public names.

All citations: 06-03-PLAN.md:64, 06-03-PLAN.md:78

</details>

<details>
<summary><code>cv_icon_mode_checks</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `src/crud_views/lib/view/buttons.py:387` — `def cv_icon_mode_checks(cls):`</summary>

06-06-PLAN.md:93 — <read_first>src/crud_views/lib/view/buttons.py (cv_icon_mode_checks); src/crud_views/lib/crispy/form.py; src/crud_views/lib/views/list.py; src/crud_views/lib/view/button_data.py; 06-SPEC.md static-check reach</read_first>

All citations: 06-06-PLAN.md:93

</details>

<details>
<summary><code>cv_id</code> — SKIPPED: explicitly produced by this phase</summary>

06-02-PLAN.md:70 — NEW template: src/crud_views/templates/crud_views/tags/button/form.html. NEW symbol: FORM_LEAF_KEYS in button_data.py. NEW normalized fields: cv_type, cv_name, cv_value, cv_id, cancel-only cv_cancel_url, cv_css_class, cv_flat_attrs; existing label/icon fields are reused. Private helper names are implementation-local. No new external package.

All citations: 06-02-PLAN.md:70

</details>

<details>
<summary><code>cv_key</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `src/crud_views_workflow/lib/views.py:24` — `cv_key = "workflow"`; `src/crud_views/lib/views/update.py:13` — `cv_key = "update"`; `src/crud_views/lib/views/card.py:22` — `cv_key = "card"`</summary>

06-02-PLAN.md:85 — Start with a failing real-crispy render test. Add form to LOCATIONS and label to LABEL_MODE_DEFAULTS together. Branch cv_button_data early for form before action URL/modal derivation; retain existing action behavior and LEAF_KEYS. Introduce FORM_LEAF_KEYS for the exact spec contract. Validate cv_key against FORM_KINDS and cv_type against submit/button/reset; invalid caller kind/type raises ValueError. Missing or None textual values normalize to empty text without coercing other falsey data such as numeric zero to empty. Preserve valid empty labels without manufacturing text.

All citations: 06-02-PLAN.md:85, 06-02-PLAN.md:86

</details>

<details>
<summary><code>cv_label_mode</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); no authoritative declaration claim; runtime/property/CLI/browser or framework contract requires execution-time confirmation</summary>

06-02-PLAN.md:86 — Implement adapter render without calling BaseInput.render: retain raw value and kwargs, normalize per spec, render the selected leaf through a scoped context copy. Strip inherited input aliases from the template context, never expose the adapter object. Normalize SafeData and lazy values at render time to ordinary strings then use Django autoescaping once; serialized extra attrs are escaped once separately. Preserve constructor signature, slot-selected semantic kind, upstream generated IDs and legacy field_classes/flat_attrs for helper.inputs. Do not infer kind from the submitted name. The leaf uses cv_button_class form/cv_key/cv_label_mode, appends cv_css_class and host classes, and renders the three bodies with cancel URL only for cancel. Keep normalizer/icon behavior extensible for 06-04 rather than hardcoding a temporary floor. Update existing input-only assertions only where layout buttons changed; filter helper inputs remain inputs until 06-05.

All citations: 06-02-PLAN.md:86

</details>

<details>
<summary><code>cv_name</code> — SKIPPED: explicitly produced by this phase</summary>

06-02-PLAN.md:70 — NEW template: src/crud_views/templates/crud_views/tags/button/form.html. NEW symbol: FORM_LEAF_KEYS in button_data.py. NEW normalized fields: cv_type, cv_name, cv_value, cv_id, cancel-only cv_cancel_url, cv_css_class, cv_flat_attrs; existing label/icon fields are reused. Private helper names are implementation-local. No new external package.

All citations: 06-02-PLAN.md:70

</details>

<details>
<summary><code>cv_type</code> — SKIPPED: explicitly produced by this phase</summary>

06-02-PLAN.md:70 — NEW template: src/crud_views/templates/crud_views/tags/button/form.html. NEW symbol: FORM_LEAF_KEYS in button_data.py. NEW normalized fields: cv_type, cv_name, cv_value, cv_id, cancel-only cv_cancel_url, cv_css_class, cv_flat_attrs; existing label/icon fields are reused. Private helper names are implementation-local. No new external package.

All citations: 06-02-PLAN.md:70, 06-02-PLAN.md:85

</details>

<details>
<summary><code>cv_value</code> — SKIPPED: explicitly produced by this phase</summary>

06-02-PLAN.md:70 — NEW template: src/crud_views/templates/crud_views/tags/button/form.html. NEW symbol: FORM_LEAF_KEYS in button_data.py. NEW normalized fields: cv_type, cv_name, cv_value, cv_id, cancel-only cv_cancel_url, cv_css_class, cv_flat_attrs; existing label/icon fields are reused. Private helper names are implementation-local. No new external package.

All citations: 06-02-PLAN.md:70, 06-08-PLAN.md:95

</details>

<details>
<summary><code>cv_view</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `src/crud_views/lib/crispy/form.py:38` — `self.cv_view = cv_view`; `src/crud_views/lib/formsets/formsets.py:36` — `cv_view: CrudView | None = None`; `src/crud_views/lib/formsets/formsets.py:265` — `cv_view: CrudView | None = None`</summary>

06-01-PLAN.md:105 — Define owner recovery from Django Context.dicts before flattening: form.cv_view first; current helper view

All citations: 06-01-PLAN.md:105, 06-03-PLAN.md:93

</details>

<details>
<summary><code>data_cv_cancel_url</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); no authoritative declaration claim; runtime/property/CLI/browser or framework contract requires execution-time confirmation</summary>

06-01-PLAN.md:99 — once; data_cv_cancel_url/data-cv-cancel-url become one cancel-only URL; generated icon-mode title and tooltip

All citations: 06-01-PLAN.md:99

</details>

<details>
<summary><code>default_label_mode</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `src/crud_views/lib/view/label_mode.py:84` — `def default_label_mode(location: str) -> str:`</summary>

06-01-PLAN.md:86 — contracts: default_label_mode with the shared defaults and independent FORM_KINDS/VARIANT_LOCATIONS.

All citations: 06-01-PLAN.md:86, 06-03-PLAN.md:78

</details>

<details>
<summary><code>delete_icon</code> — SKIPPED: explicitly produced by this phase</summary>

06-04-PLAN.md:70 — NEW class-table keys: form:hidden-label and form:icon-host. NEW registry names: save, cancel, filter-reset. NEW form attributes: CrispyFormMixin.submit_icon='save', CrispyDeleteForm.delete_icon='delete', WorkflowForm.submit_icon='workflow'. NEW adapter icon= keyword is consumed as rendering configuration, never serialized as an HTML attribute; omission selects kind default while explicit None/empty suppresses it.

All citations: 06-04-PLAN.md:70, 06-04-PLAN.md:106, 06-06-PLAN.md:101

</details>

<details>
<summary><code>dicts</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `.venv/lib/python3.12/site-packages/django/template/context.py:34` — `self.dicts = [builtins]`; `.venv/lib/python3.12/site-packages/django/template/context.py:44` — `duplicate.dicts = self.dicts[:]`; `.venv/lib/python3.12/site-packages/django/template/context.py:54` — `dicts = []`</summary>

06-01-PLAN.md:105 — Define owner recovery from Django Context.dicts before flattening: form.cv_view first; current helper view

All citations: 06-01-PLAN.md:105, 06-02-PLAN.md:108, 06-03-PLAN.md:99

</details>

<details>
<summary><code>field_classes</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `src/crud_views/lib/crispy/buttons.py:17` — `self.field_classes = get_button_class(*(slot or self.slot).split(":", 1))`; `.venv/lib/python3.12/site-packages/crispy_forms/bootstrap.py:540` — `field_classes = "btn"`; `.venv/lib/python3.12/site-packages/crispy_forms/layout.py:232` — `field_classes = ""`</summary>

06-02-PLAN.md:86 — Implement adapter render without calling BaseInput.render: retain raw value and kwargs, normalize per spec, render the selected leaf through a scoped context copy. Strip inherited input aliases from the template context, never expose the adapter object. Normalize SafeData and lazy values at render time to ordinary strings then use Django autoescaping once; serialized extra attrs are escaped once separately. Preserve constructor signature, slot-selected semantic kind, upstream generated IDs and legacy field_classes/flat_attrs for helper.inputs. Do not infer kind from the submitted name. The leaf uses cv_button_class form/cv_key/cv_label_mode, appends cv_css_class and host classes, and renders the three bodies with cancel URL only for cancel. Keep normalizer/icon behavior extensible for 06-04 rather than hardcoding a temporary floor. Update existing input-only assertions only where layout buttons changed; filter helper inputs remain inputs until 06-05.

All citations: 06-02-PLAN.md:86, 06-02-PLAN.md:108

</details>

<details>
<summary><code>flat_attrs</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `.venv/lib/python3.12/site-packages/crispy_forms/bootstrap.py:304` — `self.flat_attrs = flatatt(kwargs)`; `.venv/lib/python3.12/site-packages/crispy_forms/bootstrap.py:556` — `self.flat_attrs = flatatt(kwargs)`; `.venv/lib/python3.12/site-packages/crispy_forms/bootstrap.py:1125` — `self.flat_attrs = flatatt(kwargs)`</summary>

06-02-PLAN.md:86 — Implement adapter render without calling BaseInput.render: retain raw value and kwargs, normalize per spec, render the selected leaf through a scoped context copy. Strip inherited input aliases from the template context, never expose the adapter object. Normalize SafeData and lazy values at render time to ordinary strings then use Django autoescaping once; serialized extra attrs are escaped once separately. Preserve constructor signature, slot-selected semantic kind, upstream generated IDs and legacy field_classes/flat_attrs for helper.inputs. Do not infer kind from the submitted name. The leaf uses cv_button_class form/cv_key/cv_label_mode, appends cv_css_class and host classes, and renders the three bodies with cancel URL only for cancel. Keep normalizer/icon behavior extensible for 06-04 rather than hardcoding a temporary floor. Update existing input-only assertions only where layout buttons changed; filter helper inputs remain inputs until 06-05.

All citations: 06-02-PLAN.md:86

</details>

<details>
<summary><code>form_actions_label_mode</code> — SKIPPED: explicitly produced by this phase</summary>

06-03-PLAN.md:64 — NEW fields: CrudViewsSettings.form_actions_label_mode (CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE), ViewSet.form_actions_label_mode, CrudView.cv_form_actions_label_mode. NEW public resolver: CrudView.cv_get_form_actions_label_mode(). Existing cv_get_action_label_mode gains location='form'. Private owner-recovery helpers are internal, not promised public names.

All citations: 06-03-PLAN.md:64

</details>

<details>
<summary><code>format_html</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `.venv/lib/python3.12/site-packages/django/utils/html.py:129` — `def format_html(format_string, *args, **kwargs):`</summary>

06-01-PLAN.md:118 — Record accurate dependency findings: Django 6 removed zero-argument format_html calls, not the function;

All citations: 06-01-PLAN.md:118, 06-07-PLAN.md:115, 06-09-PLAN.md:160

</details>

<details>
<summary><code>get_attributes</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `.venv/lib/python3.12/site-packages/crispy_forms/helper.py:290` — `def get_attributes(self, template_pack=TEMPLATE_PACK):`</summary>

06-03-PLAN.md:91 — <read_first>06-SPEC.md ownership contract; installed crispy BasicNode.get_render/FormHelper.get_attributes; tests/test1/test_crispy_buttons.py</read_first>

All citations: 06-03-PLAN.md:91

</details>

<details>
<summary><code>get_filterset</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `src/crud_views/lib/views/mixins.py:315` — `def get_filterset(self, filterset_class):`</summary>

06-05-PLAN.md:70 — <read_first>src/crud_views/lib/views/list.py; src/crud_views/lib/views/mixins.py (get_filterset); tests/test1/test_filter.py; docs/reference/list_view.md (field-only helper example); 06-SPEC.md in this phase directory</read_first>

All citations: 06-05-PLAN.md:70

</details>

<details>
<summary><code>get_form_actions</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `src/crud_views/lib/crispy/form.py:53` — `def get_form_actions(self) -> FormActions:`</summary>

06-01-PLAN.md:112 — Define get_form_actions returning FormActions or None; None means no group, empty FormActions is retained.

All citations: 06-01-PLAN.md:112, 06-05-PLAN.md:24, 06-05-PLAN.md:64, 06-05-PLAN.md:78, 06-05-PLAN.md:94, 06-06-PLAN.md:101, 06-08-PLAN.md:95

</details>

<details>
<summary><code>get_form_class</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `src/crud_views_polymorphic/lib/utils.py:64` — `def get_form_class(self):`</summary>

06-06-PLAN.md:101 — Introduce a static form checker wired from CrudView.checks. Inspect only concrete statically selected form classes that inherit package defaults and whose relevant button/kwargs hooks retain the package implementation; inherited class submit_icon/delete_icon attributes are knowable. For filter helpers inspect the configured helper class only when its default get_form_actions is inherited; do not instantiate a form/helper, call get_form_class(request), or execute custom action hooks. Unknown/custom providers skip static icon inference and must be covered by runtime normalization. Resolve form mode through the same public resolver; catch ValueError only around mode resolution so E108/E210/E211 survive strict checking. Form static missing means icon is None or empty; named-but-unregistered icons retain the icon registry's separate diagnostics.

All citations: 06-06-PLAN.md:101

</details>

<details>
<summary><code>get_render</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `.venv/lib/python3.12/site-packages/crispy_forms/templatetags/crispy_forms_tags.py:70` — `def get_render(self, context):`</summary>

06-03-PLAN.md:91 — <read_first>06-SPEC.md ownership contract; installed crispy BasicNode.get_render/FormHelper.get_attributes; tests/test1/test_crispy_buttons.py</read_first>

All citations: 06-03-PLAN.md:91

</details>

<details>
<summary><code>helper</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `src/crud_views/lib/views/mixins.py:319` — `filterset.form.helper = self.formhelper_class(request=self.request, view=self)`; `src/crud_views/lib/crispy/form.py:42` — `def helper(self) -> FormHelper:`; `src/crud_views/lib/crispy/form.py:133` — `def helper(self):`</summary>

06-01-PLAN.md:105 — Define owner recovery from Django Context.dicts before flattening: form.cv_view first; current helper view

All citations: 06-01-PLAN.md:105, 06-01-PLAN.md:107, 06-01-PLAN.md:108, 06-01-PLAN.md:113, 06-02-PLAN.md:70, 06-02-PLAN.md:82, 06-02-PLAN.md:86, 06-02-PLAN.md:90, 06-03-PLAN.md:24, 06-03-PLAN.md:25, 06-03-PLAN.md:89, 06-03-PLAN.md:93, 06-03-PLAN.md:94, 06-03-PLAN.md:96, 06-03-PLAN.md:99, 06-03-PLAN.md:103, 06-04-PLAN.md:106, 06-05-PLAN.md:23, 06-05-PLAN.md:25, 06-05-PLAN.md:26, 06-05-PLAN.md:35, 06-05-PLAN.md:70, 06-05-PLAN.md:73, 06-05-PLAN.md:75, 06-05-PLAN.md:78, 06-05-PLAN.md:96, 06-05-PLAN.md:99, 06-05-PLAN.md:103, 06-05-PLAN.md:105, 06-05-PLAN.md:116, 06-05-PLAN.md:121, 06-06-PLAN.md:101, 06-08-PLAN.md:29, 06-08-PLAN.md:37, 06-08-PLAN.md:46, 06-08-PLAN.md:72, 06-08-PLAN.md:91, 06-08-PLAN.md:110, 06-08-PLAN.md:127, 06-08-PLAN.md:137, 06-09-PLAN.md:155, 06-09-PLAN.md:196

</details>

<details>
<summary><code>label_mode</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `src/crud_views/lib/views/card.py:50` — `label_mode = action.label_mode`; `src/crud_views/lib/views/card.py:52` — `label_mode = "icon"`; `src/crud_views/lib/views/card.py:54` — `label_mode = self.cv_card_actions_label_mode`</summary>

06-01-PLAN.md:79 — src/crud_views/lib/view/button_data.py; src/crud_views/lib/view/label_mode.py;

All citations: 06-01-PLAN.md:79, 06-02-PLAN.md:9, 06-02-PLAN.md:76, 06-02-PLAN.md:77

</details>

<details>
<summary><code>list_view</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `tests/test1/test_manage.py:97` — `list_view = views["list"]`; `tests/test1/test_action_menus_groups.py:30` — `def list_view(client_user_author_view, author_douglas_adams):`</summary>

06-05-PLAN.md:70 — <read_first>src/crud_views/lib/views/list.py; src/crud_views/lib/views/mixins.py (get_filterset); tests/test1/test_filter.py; docs/reference/list_view.md (field-only helper example); 06-SPEC.md in this phase directory</read_first>

All citations: 06-05-PLAN.md:70, 06-08-PLAN.md:14, 06-08-PLAN.md:92, 06-08-PLAN.md:93

</details>

<details>
<summary><code>override_settings</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); no authoritative declaration claim; runtime/property/CLI/browser or framework contract requires execution-time confirmation</summary>

06-02-PLAN.md:107 — Update existing test_label_mode.py and test_button_data.py location/default assertions for form, retaining the set(LABEL_MODE_DEFAULTS) == LOCATIONS invariant and adding lazy override_settings coverage. Existing action contracts and location-independent finite class grammar remain unchanged.

All citations: 06-02-PLAN.md:107, 06-06-PLAN.md:80, 06-09-PLAN.md:68

</details>

<details>
<summary><code>push</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `.venv/lib/python3.12/site-packages/django/template/context.py:53` — `def push(self, *args, **kwargs):`; `.venv/lib/python3.12/site-packages/django/template/loader_tags.py:32` — `def push(self, name, block):`; `.venv/lib/python3.12/site-packages/django/template/loader_tags.py:58` — `push = block = block_context.pop(self.name)`</summary>

06-01-PLAN.md:108 — helper. Package filter helper render_layout supplies a private helper-owner context entry using context.push

All citations: 06-01-PLAN.md:108, 06-05-PLAN.md:78, 06-09-PLAN.md:117

</details>

<details>
<summary><code>read_bytes</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); no authoritative declaration claim; runtime/property/CLI/browser or framework contract requires execution-time confirmation</summary>

06-01-PLAN.md:140 — tests compare render bytes to read_bytes with no update-on-test behavior. Pin default text, name, value,

All citations: 06-01-PLAN.md:140

</details>

<details>
<summary><code>render</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `src/crud_views/templatetags/crud_views.py:333` — `def render(self, context):`; `src/crud_views/lib/table/columns.py:23` — `def render(self, table, **kwargs):`; `src/crud_views/lib/table/columns.py:38` — `def render(self, table, record, **kwargs):`</summary>

06-01-PLAN.md:71 — <name>Task 1: Trace the existing form render and record the required design</name>

All citations: 06-01-PLAN.md:71, 06-01-PLAN.md:95, 06-01-PLAN.md:125, 06-01-PLAN.md:128, 06-01-PLAN.md:140, 06-02-PLAN.md:41, 06-02-PLAN.md:82, 06-02-PLAN.md:85, 06-02-PLAN.md:86, 06-02-PLAN.md:112, 06-02-PLAN.md:146, 06-03-PLAN.md:25, 06-03-PLAN.md:78, 06-03-PLAN.md:96, 06-03-PLAN.md:121, 06-04-PLAN.md:91, 06-04-PLAN.md:100, 06-04-PLAN.md:132, 06-05-PLAN.md:23, 06-06-PLAN.md:31, 06-06-PLAN.md:97, 06-06-PLAN.md:102, 06-06-PLAN.md:119, 06-06-PLAN.md:129, 06-06-PLAN.md:130, 06-08-PLAN.md:32, 06-08-PLAN.md:80, 06-08-PLAN.md:84, 06-08-PLAN.md:91, 06-09-PLAN.md:20, 06-09-PLAN.md:75, 06-09-PLAN.md:100, 06-09-PLAN.md:109, 06-09-PLAN.md:162, 06-09-PLAN.md:186, 06-09-PLAN.md:195, 06-09-PLAN.md:197

</details>

<details>
<summary><code>render_layout</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `.venv/lib/python3.12/site-packages/crispy_forms/helper.py:266` — `def render_layout(self, form, context, template_pack=TEMPLATE_PACK):`</summary>

06-01-PLAN.md:108 — helper. Package filter helper render_layout supplies a private helper-owner context entry using context.push

All citations: 06-01-PLAN.md:108, 06-01-PLAN.md:114, 06-05-PLAN.md:64, 06-05-PLAN.md:78

</details>

<details>
<summary><code>slot</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `src/crud_views/lib/crispy/buttons.py:14` — `slot: str`; `src/crud_views/lib/crispy/buttons.py:22` — `slot = "form:submit"`; `src/crud_views/lib/crispy/buttons.py:26` — `slot = "form:cancel"`</summary>

06-02-PLAN.md:86 — Implement adapter render without calling BaseInput.render: retain raw value and kwargs, normalize per spec, render the selected leaf through a scoped context copy. Strip inherited input aliases from the template context, never expose the adapter object. Normalize SafeData and lazy values at render time to ordinary strings then use Django autoescaping once; serialized extra attrs are escaped once separately. Preserve constructor signature, slot-selected semantic kind, upstream generated IDs and legacy field_classes/flat_attrs for helper.inputs. Do not infer kind from the submitted name. The leaf uses cv_button_class form/cv_key/cv_label_mode, appends cv_css_class and host classes, and renders the three bodies with cancel URL only for cancel. Keep normalizer/icon behavior extensible for 06-04 rather than hardcoding a temporary floor. Update existing input-only assertions only where layout buttons changed; filter helper inputs remain inputs until 06-05.

All citations: 06-02-PLAN.md:86, 06-04-PLAN.md:103, 06-04-PLAN.md:106, 06-04-PLAN.md:128, 06-09-PLAN.md:159

</details>

<details>
<summary><code>submit_icon</code> — SKIPPED: explicitly produced by this phase</summary>

06-04-PLAN.md:30 — - "Repeated renders with different icon settings, forms and languages do not mutate shared class/icon defaults or retain another form's submit_icon."

All citations: 06-04-PLAN.md:30, 06-04-PLAN.md:70, 06-04-PLAN.md:101, 06-04-PLAN.md:106, 06-06-PLAN.md:101, 06-09-PLAN.md:198

</details>

<details>
<summary><code>template</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); supplemental same-name declaration candidates (not signature or qualified-identity verification): `src/crud_views_object_detail/lib/resolvers.py:51` — `template: str | None = None`; `src/crud_views_object_detail/lib/config.py:37` — `template: str | None = None`; `src/crud_views/lib/icons.py:208` — `template = config.get("class")`</summary>

06-01-PLAN.md:25 — - "D-05, D-06, D-07, D-08: The spec fixes template precedence, pack substitution and the cv_* context before implementation."

All citations: 06-01-PLAN.md:25, 06-01-PLAN.md:95, 06-02-PLAN.md:30, 06-02-PLAN.md:31, 06-02-PLAN.md:48, 06-02-PLAN.md:70, 06-02-PLAN.md:80, 06-02-PLAN.md:81, 06-02-PLAN.md:82, 06-02-PLAN.md:86, 06-02-PLAN.md:97, 06-02-PLAN.md:101, 06-02-PLAN.md:108, 06-02-PLAN.md:141, 06-02-PLAN.md:152, 06-03-PLAN.md:105, 06-05-PLAN.md:99, 06-08-PLAN.md:37, 06-08-PLAN.md:46, 06-08-PLAN.md:72, 06-08-PLAN.md:91, 06-08-PLAN.md:95, 06-08-PLAN.md:99, 06-08-PLAN.md:110, 06-08-PLAN.md:127, 06-08-PLAN.md:131, 06-08-PLAN.md:137, 06-09-PLAN.md:21, 06-09-PLAN.md:83, 06-09-PLAN.md:122, 06-09-PLAN.md:215

</details>

<details>
<summary><code>test_action_label_mode_config</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); module/file reference resolved in path inventory</summary>

06-03-PLAN.md:12 — - tests/test1/test_action_label_mode_config.py

All citations: 06-03-PLAN.md:12, 06-03-PLAN.md:69, 06-03-PLAN.md:70, 06-03-PLAN.md:81, 06-03-PLAN.md:102, 06-06-PLAN.md:72, 06-06-PLAN.md:83

</details>

<details>
<summary><code>test_button_classes</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); module/file reference resolved in path inventory</summary>

06-04-PLAN.md:88 — <automated>.venv/bin/pytest tests/test1/test_icon_host_leaves.py tests/test1/test_button_classes.py tests/test1/test_icons_registry.py -q</automated>

All citations: 06-04-PLAN.md:88, 06-08-PLAN.md:83

</details>

<details>
<summary><code>test_button_data</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); module/file reference resolved in path inventory</summary>

06-01-PLAN.md:124 — <automated>.venv/bin/pytest tests/test1/test_crispy_buttons.py tests/test1/test_button_data.py -q</automated>

All citations: 06-01-PLAN.md:124, 06-02-PLAN.md:14, 06-02-PLAN.md:89, 06-02-PLAN.md:98, 06-02-PLAN.md:107, 06-02-PLAN.md:111, 06-06-PLAN.md:66, 06-06-PLAN.md:105

</details>

<details>
<summary><code>test_button_leaves</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); module/file reference resolved in path inventory</summary>

06-02-PLAN.md:77 — <read_first>06-01-SUMMARY.md in this phase directory; src/crud_views/templates/crud_views/tags/button/action.html; src/crud_views/lib/crispy/buttons.py; src/crud_views/lib/view/button_data.py; src/crud_views/lib/view/label_mode.py; tests/test1/test_crispy_buttons.py; tests/test1/test_button_leaves.py</read_first>

All citations: 06-02-PLAN.md:77, 06-02-PLAN.md:99

</details>

<details>
<summary><code>test_cancel_origin</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); module/file reference resolved in path inventory</summary>

06-02-PLAN.md:121 — <read_first>06-01-SUMMARY.md in this phase directory; tests/test1/test_form_buttons_golden.py; tests/test1/test_crud.py; tests/test1/test_cancel_origin.py</read_first>

All citations: 06-02-PLAN.md:121, 06-02-PLAN.md:126, 06-09-PLAN.md:66

</details>

<details>
<summary><code>test_crispy_buttons</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); module/file reference resolved in path inventory</summary>

06-01-PLAN.md:124 — <automated>.venv/bin/pytest tests/test1/test_crispy_buttons.py tests/test1/test_button_data.py -q</automated>

All citations: 06-01-PLAN.md:124, 06-01-PLAN.md:134, 06-02-PLAN.md:12, 06-02-PLAN.md:76, 06-02-PLAN.md:77, 06-02-PLAN.md:89, 06-02-PLAN.md:98, 06-02-PLAN.md:111, 06-03-PLAN.md:13, 06-03-PLAN.md:81, 06-03-PLAN.md:90, 06-03-PLAN.md:91, 06-03-PLAN.md:102, 06-04-PLAN.md:16, 06-04-PLAN.md:97, 06-04-PLAN.md:98, 06-04-PLAN.md:109, 06-05-PLAN.md:10, 06-05-PLAN.md:69, 06-05-PLAN.md:81, 06-05-PLAN.md:90, 06-05-PLAN.md:91, 06-05-PLAN.md:102, 06-07-PLAN.md:38, 06-07-PLAN.md:113

</details>

<details>
<summary><code>test_crud</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); module/file reference resolved in path inventory</summary>

06-01-PLAN.md:134 — <read_first>tests/test1/test_crispy_buttons.py; tests/test1/test_crud.py; tests/test1/conftest.py; tests/test1/test_pagination_docs.py; .planning/phases/06-form-button-leaf/06-SPEC.md</read_first>

All citations: 06-01-PLAN.md:134, 06-01-PLAN.md:147, 06-02-PLAN.md:121, 06-02-PLAN.md:126, 06-09-PLAN.md:66

</details>

<details>
<summary><code>test_docs_sync</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); module/file reference resolved in path inventory</summary>

06-08-PLAN.md:108 — <read_first>CHANGELOG.md; docs/migrating-1.0.md; examples/bootstrap5/project/settings.py; examples/bootstrap5/test_docs_sync.py</read_first>

All citations: 06-08-PLAN.md:108, 06-09-PLAN.md:238

</details>

<details>
<summary><code>test_filter</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); module/file reference resolved in path inventory</summary>

06-01-PLAN.md:157 — <read_first>tests/test1/test_workflow.py; tests/test1/test_filter.py; tests/test1/app/views.py; .planning/phases/06-form-button-leaf/06-SPEC.md</read_first>

All citations: 06-01-PLAN.md:157, 06-01-PLAN.md:167, 06-05-PLAN.md:9, 06-05-PLAN.md:30, 06-05-PLAN.md:69, 06-05-PLAN.md:70, 06-05-PLAN.md:81, 06-05-PLAN.md:90, 06-05-PLAN.md:91, 06-05-PLAN.md:102, 06-07-PLAN.md:113

</details>

<details>
<summary><code>test_form_button_baselines</code> — SKIPPED: explicitly produced by this phase</summary>

06-01-PLAN.md:65 — tests/test1/golden/form_buttons/*.html files enumerated above. NEW test symbol: test_form_button_baselines.

All citations: 06-01-PLAN.md:65

</details>

<details>
<summary><code>test_form_button_checks</code> — SKIPPED: explicitly produced by this phase</summary>

06-06-PLAN.md:12 — - tests/test1/test_form_button_checks.py

All citations: 06-06-PLAN.md:12, 06-06-PLAN.md:30, 06-06-PLAN.md:66, 06-06-PLAN.md:71, 06-06-PLAN.md:83, 06-06-PLAN.md:92, 06-06-PLAN.md:105, 06-07-PLAN.md:113, 06-09-PLAN.md:33

</details>

<details>
<summary><code>test_form_button_docs</code> — SKIPPED: explicitly produced by this phase</summary>

06-08-PLAN.md:16 — - tests/test1/test_form_button_docs.py

All citations: 06-08-PLAN.md:16, 06-08-PLAN.md:36, 06-08-PLAN.md:45, 06-08-PLAN.md:72, 06-08-PLAN.md:92, 06-08-PLAN.md:98

</details>

<details>
<summary><code>test_form_buttons_golden</code> — SKIPPED: explicitly produced by this phase</summary>

06-01-PLAN.md:9 — - tests/test1/test_form_buttons_golden.py

All citations: 06-01-PLAN.md:9, 06-01-PLAN.md:31, 06-01-PLAN.md:34, 06-01-PLAN.md:64, 06-01-PLAN.md:133, 06-01-PLAN.md:147, 06-01-PLAN.md:156, 06-01-PLAN.md:167, 06-02-PLAN.md:15, 06-02-PLAN.md:120, 06-02-PLAN.md:121, 06-02-PLAN.md:126, 06-05-PLAN.md:11, 06-05-PLAN.md:69, 06-05-PLAN.md:81, 06-09-PLAN.md:30

</details>

<details>
<summary><code>test_icon_host_leaves</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); module/file reference resolved in path inventory</summary>

06-04-PLAN.md:11 — - tests/test1/test_icon_host_leaves.py

All citations: 06-04-PLAN.md:11, 06-04-PLAN.md:75, 06-04-PLAN.md:76, 06-04-PLAN.md:84, 06-04-PLAN.md:88

</details>

<details>
<summary><code>test_icons_registry</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); module/file reference resolved in path inventory</summary>

06-04-PLAN.md:76 — <read_first>src/crud_views/lib/button_classes.py; src/crud_views/lib/icons.py; tests/test1/test_icon_host_leaves.py; tests/test1/test_icons_registry.py; src/crud_views/templates/crud_views/tags/button/action.html</read_first>

All citations: 06-04-PLAN.md:76, 06-04-PLAN.md:88, 06-04-PLAN.md:109

</details>

<details>
<summary><code>test_label_mode</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); module/file reference resolved in path inventory</summary>

06-02-PLAN.md:13 — - tests/test1/test_label_mode.py

All citations: 06-02-PLAN.md:13, 06-02-PLAN.md:98, 06-02-PLAN.md:107, 06-06-PLAN.md:83

</details>

<details>
<summary><code>test_label_mode_docs</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); module/file reference resolved in path inventory</summary>

06-08-PLAN.md:11 — - tests/test1/test_label_mode_docs.py

All citations: 06-08-PLAN.md:11, 06-08-PLAN.md:77, 06-08-PLAN.md:78, 06-08-PLAN.md:83

</details>

<details>
<summary><code>test_pagination_docs</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); module/file reference resolved in path inventory</summary>

06-01-PLAN.md:134 — <read_first>tests/test1/test_crispy_buttons.py; tests/test1/test_crud.py; tests/test1/conftest.py; tests/test1/test_pagination_docs.py; .planning/phases/06-form-button-leaf/06-SPEC.md</read_first>

All citations: 06-01-PLAN.md:134, 06-08-PLAN.md:93

</details>

<details>
<summary><code>test_workflow</code> — UNCHECKABLE (intel index empty / unsupported Python or external symbol); module/file reference resolved in path inventory</summary>

06-01-PLAN.md:157 — <read_first>tests/test1/test_workflow.py; tests/test1/test_filter.py; tests/test1/app/views.py; .planning/phases/06-form-button-leaf/06-SPEC.md</read_first>

All citations: 06-01-PLAN.md:157, 06-01-PLAN.md:167, 06-04-PLAN.md:98, 06-04-PLAN.md:109

</details>

#### File references and produced artifacts

<details>
<summary><code>.planning/phases/06-form-button-leaf/06-SPEC.md</code> — SKIPPED: declared phase output / execution summary</summary>

06-01-PLAN.md:8 — - .planning/phases/06-form-button-leaf/06-SPEC.md

All citations: 06-01-PLAN.md:8, 06-01-PLAN.md:29, 06-01-PLAN.md:73, 06-01-PLAN.md:134, 06-01-PLAN.md:157, 06-02-PLAN.md:64, 06-03-PLAN.md:58, 06-04-PLAN.md:64, 06-05-PLAN.md:58, 06-06-PLAN.md:60, 06-07-PLAN.md:59, 06-08-PLAN.md:66, 06-09-PLAN.md:54

</details>

<details>
<summary><code>tests/test1/test_form_buttons_golden.py</code> — SKIPPED: declared phase output / execution summary</summary>

06-01-PLAN.md:9 — - tests/test1/test_form_buttons_golden.py

All citations: 06-01-PLAN.md:9, 06-01-PLAN.md:31, 06-01-PLAN.md:34, 06-01-PLAN.md:64, 06-01-PLAN.md:133, 06-01-PLAN.md:147, 06-01-PLAN.md:156, 06-01-PLAN.md:167, 06-02-PLAN.md:15, 06-02-PLAN.md:120, 06-02-PLAN.md:121, 06-02-PLAN.md:126, 06-05-PLAN.md:11, 06-05-PLAN.md:69, 06-05-PLAN.md:81, 06-09-PLAN.md:30

</details>

<details>
<summary><code>tests/test1/golden/form_buttons/create.html</code> — SKIPPED: declared phase output / execution summary</summary>

06-01-PLAN.md:10 — - tests/test1/golden/form_buttons/create.html

All citations: 06-01-PLAN.md:10, 06-01-PLAN.md:35, 06-01-PLAN.md:133, 06-02-PLAN.md:16, 06-02-PLAN.md:120

</details>

<details>
<summary><code>tests/test1/golden/form_buttons/update.html</code> — SKIPPED: declared phase output / execution summary</summary>

06-01-PLAN.md:11 — - tests/test1/golden/form_buttons/update.html

All citations: 06-01-PLAN.md:11, 06-01-PLAN.md:133, 06-02-PLAN.md:17, 06-02-PLAN.md:120

</details>

<details>
<summary><code>tests/test1/golden/form_buttons/delete.html</code> — SKIPPED: declared phase output / execution summary</summary>

06-01-PLAN.md:12 — - tests/test1/golden/form_buttons/delete.html

All citations: 06-01-PLAN.md:12, 06-01-PLAN.md:133, 06-02-PLAN.md:18, 06-02-PLAN.md:120

</details>

<details>
<summary><code>tests/test1/golden/form_buttons/workflow.html</code> — SKIPPED: declared phase output / execution summary</summary>

06-01-PLAN.md:13 — - tests/test1/golden/form_buttons/workflow.html

All citations: 06-01-PLAN.md:13, 06-01-PLAN.md:156, 06-02-PLAN.md:19, 06-02-PLAN.md:120

</details>

<details>
<summary><code>tests/test1/golden/form_buttons/filter.html</code> — SKIPPED: declared phase output / execution summary</summary>

06-01-PLAN.md:14 — - tests/test1/golden/form_buttons/filter.html

All citations: 06-01-PLAN.md:14, 06-01-PLAN.md:156, 06-05-PLAN.md:12, 06-05-PLAN.md:69

</details>

<details>
<summary><code>home/alex/.codex/gsd-core/workflows/execute-plan.md</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: /home/alex/.codex/gsd-core/workflows/execute-plan.md</summary>

06-01-PLAN.md:46 — @/home/alex/.codex/gsd-core/workflows/execute-plan.md

All citations: 06-01-PLAN.md:46, 06-02-PLAN.md:52, 06-03-PLAN.md:46, 06-04-PLAN.md:52, 06-05-PLAN.md:46, 06-06-PLAN.md:48, 06-07-PLAN.md:47, 06-08-PLAN.md:54, 06-09-PLAN.md:42

</details>

<details>
<summary><code>home/alex/.codex/gsd-core/templates/summary.md</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: /home/alex/.codex/gsd-core/templates/summary.md</summary>

06-01-PLAN.md:47 — @/home/alex/.codex/gsd-core/templates/summary.md

All citations: 06-01-PLAN.md:47, 06-02-PLAN.md:53, 06-03-PLAN.md:47, 06-04-PLAN.md:53, 06-05-PLAN.md:47, 06-06-PLAN.md:49, 06-07-PLAN.md:48, 06-08-PLAN.md:55, 06-09-PLAN.md:43

</details>

<details>
<summary><code>CLAUDE.md</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: CLAUDE.md</summary>

06-01-PLAN.md:51 — @CLAUDE.md

All citations: 06-01-PLAN.md:51, 06-02-PLAN.md:57, 06-03-PLAN.md:51, 06-04-PLAN.md:57, 06-05-PLAN.md:51, 06-06-PLAN.md:53, 06-07-PLAN.md:52, 06-08-PLAN.md:59, 06-09-PLAN.md:47

</details>

<details>
<summary><code>.planning/PROJECT.md</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: .planning/PROJECT.md</summary>

06-01-PLAN.md:52 — @.planning/PROJECT.md

All citations: 06-01-PLAN.md:52, 06-02-PLAN.md:58, 06-03-PLAN.md:52, 06-04-PLAN.md:58, 06-05-PLAN.md:52, 06-06-PLAN.md:54, 06-07-PLAN.md:53, 06-08-PLAN.md:60, 06-09-PLAN.md:48

</details>

<details>
<summary><code>.planning/ROADMAP.md</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: .planning/ROADMAP.md</summary>

06-01-PLAN.md:53 — @.planning/ROADMAP.md

All citations: 06-01-PLAN.md:53, 06-02-PLAN.md:59, 06-03-PLAN.md:53, 06-04-PLAN.md:59, 06-05-PLAN.md:53, 06-06-PLAN.md:55, 06-07-PLAN.md:54, 06-08-PLAN.md:61, 06-09-PLAN.md:49

</details>

<details>
<summary><code>.planning/STATE.md</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: .planning/STATE.md</summary>

06-01-PLAN.md:54 — @.planning/STATE.md

All citations: 06-01-PLAN.md:54, 06-02-PLAN.md:60, 06-03-PLAN.md:54, 06-04-PLAN.md:60, 06-05-PLAN.md:54, 06-06-PLAN.md:56, 06-07-PLAN.md:55, 06-08-PLAN.md:62, 06-09-PLAN.md:50

</details>

<details>
<summary><code>.planning/REQUIREMENTS.md</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: .planning/REQUIREMENTS.md</summary>

06-01-PLAN.md:55 — @.planning/REQUIREMENTS.md

All citations: 06-01-PLAN.md:55

</details>

<details>
<summary><code>.planning/phases/06-form-button-leaf/06-CONTEXT.md</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: .planning/phases/06-form-button-leaf/06-CONTEXT.md</summary>

06-01-PLAN.md:56 — @.planning/phases/06-form-button-leaf/06-CONTEXT.md

All citations: 06-01-PLAN.md:56, 06-02-PLAN.md:61, 06-03-PLAN.md:55, 06-04-PLAN.md:61, 06-05-PLAN.md:55, 06-06-PLAN.md:57, 06-07-PLAN.md:56, 06-08-PLAN.md:63, 06-09-PLAN.md:51

</details>

<details>
<summary><code>.planning/phases/06-form-button-leaf/06-RESEARCH.md</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: .planning/phases/06-form-button-leaf/06-RESEARCH.md</summary>

06-01-PLAN.md:57 — @.planning/phases/06-form-button-leaf/06-RESEARCH.md

All citations: 06-01-PLAN.md:57, 06-02-PLAN.md:62, 06-03-PLAN.md:56, 06-04-PLAN.md:62, 06-05-PLAN.md:56, 06-06-PLAN.md:58, 06-07-PLAN.md:57, 06-08-PLAN.md:64, 06-09-PLAN.md:52

</details>

<details>
<summary><code>.planning/phases/06-form-button-leaf/06-PATTERNS.md</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: .planning/phases/06-form-button-leaf/06-PATTERNS.md</summary>

06-01-PLAN.md:58 — @.planning/phases/06-form-button-leaf/06-PATTERNS.md

All citations: 06-01-PLAN.md:58, 06-02-PLAN.md:63, 06-03-PLAN.md:57, 06-04-PLAN.md:63, 06-05-PLAN.md:57, 06-06-PLAN.md:59, 06-07-PLAN.md:58, 06-08-PLAN.md:65, 06-09-PLAN.md:53

</details>

<details>
<summary><code>.planning/phases/06-form-button-leaf/06-VALIDATION.md</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: .planning/phases/06-form-button-leaf/06-VALIDATION.md</summary>

06-01-PLAN.md:59 — @.planning/phases/06-form-button-leaf/06-VALIDATION.md

All citations: 06-01-PLAN.md:59, 06-09-PLAN.md:9, 06-09-PLAN.md:26, 06-09-PLAN.md:32, 06-09-PLAN.md:65, 06-09-PLAN.md:80

</details>

<details>
<summary><code>06-SPEC.md</code> — SKIPPED: declared phase output / execution summary</summary>

06-01-PLAN.md:64 — NEW files: 06-SPEC.md at the full path in files_modified; tests/test1/test_form_buttons_golden.py; the five

All citations: 06-01-PLAN.md:64, 06-03-PLAN.md:70, 06-03-PLAN.md:91, 06-05-PLAN.md:70, 06-06-PLAN.md:93, 06-08-PLAN.md:78, 06-09-PLAN.md:66

</details>

<details>
<summary><code>tests/test1/golden/form_buttons/*.html</code> — SKIPPED: declared phase output / execution summary</summary>

06-01-PLAN.md:65 — tests/test1/golden/form_buttons/*.html files enumerated above. NEW test symbol: test_form_button_baselines.

All citations: 06-01-PLAN.md:65

</details>

<details>
<summary><code>.planning/phases/01-label-mode-defaults/01-CONTEXT.md</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: .planning/phases/01-label-mode-defaults/01-CONTEXT.md</summary>

06-01-PLAN.md:75 — .planning/phases/01-label-mode-defaults/01-CONTEXT.md; .planning/phases/02-form-key-grammar/02-CONTEXT.md;

All citations: 06-01-PLAN.md:75

</details>

<details>
<summary><code>.planning/phases/02-form-key-grammar/02-CONTEXT.md</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: .planning/phases/02-form-key-grammar/02-CONTEXT.md</summary>

06-01-PLAN.md:75 — .planning/phases/01-label-mode-defaults/01-CONTEXT.md; .planning/phases/02-form-key-grammar/02-CONTEXT.md;

All citations: 06-01-PLAN.md:75

</details>

<details>
<summary><code>superpowers/plans/2026-10-24-concept-review-followups.md</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: superpowers/plans/2026-10-24-concept-review-followups.md</summary>

06-01-PLAN.md:76 — superpowers/plans/2026-10-24-concept-review-followups.md (source Phase 2);

All citations: 06-01-PLAN.md:76

</details>

<details>
<summary><code>src/crud_views/lib/crispy/buttons.py</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: src/crud_views/lib/crispy/buttons.py</summary>

06-01-PLAN.md:77 — src/crud_views/lib/crispy/buttons.py; src/crud_views/lib/crispy/form.py;

All citations: 06-01-PLAN.md:77, 06-02-PLAN.md:10, 06-02-PLAN.md:39, 06-02-PLAN.md:76, 06-02-PLAN.md:77, 06-02-PLAN.md:98, 06-03-PLAN.md:11, 06-03-PLAN.md:30, 06-03-PLAN.md:33, 06-03-PLAN.md:69, 06-03-PLAN.md:90, 06-04-PLAN.md:15, 06-04-PLAN.md:40, 06-04-PLAN.md:97, 06-05-PLAN.md:37

</details>

<details>
<summary><code>src/crud_views/lib/crispy/form.py</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: src/crud_views/lib/crispy/form.py</summary>

06-01-PLAN.md:77 — src/crud_views/lib/crispy/buttons.py; src/crud_views/lib/crispy/form.py;

All citations: 06-01-PLAN.md:77, 06-04-PLAN.md:13, 06-04-PLAN.md:39, 06-04-PLAN.md:97, 06-04-PLAN.md:98, 06-06-PLAN.md:93

</details>

<details>
<summary><code>src/crud_views/lib/views/mixins.py</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: src/crud_views/lib/views/mixins.py</summary>

06-01-PLAN.md:78 — src/crud_views/lib/views/list.py; src/crud_views/lib/views/mixins.py;

All citations: 06-01-PLAN.md:78, 06-05-PLAN.md:33, 06-05-PLAN.md:70

</details>

<details>
<summary><code>src/crud_views/lib/views/list.py</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: src/crud_views/lib/views/list.py</summary>

06-01-PLAN.md:78 — src/crud_views/lib/views/list.py; src/crud_views/lib/views/mixins.py;

All citations: 06-01-PLAN.md:78, 06-05-PLAN.md:8, 06-05-PLAN.md:28, 06-05-PLAN.md:34, 06-05-PLAN.md:36, 06-05-PLAN.md:69, 06-05-PLAN.md:70, 06-05-PLAN.md:90, 06-06-PLAN.md:93

</details>

<details>
<summary><code>src/crud_views/lib/view/button_data.py</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: src/crud_views/lib/view/button_data.py</summary>

06-01-PLAN.md:79 — src/crud_views/lib/view/button_data.py; src/crud_views/lib/view/label_mode.py;

All citations: 06-01-PLAN.md:79, 06-02-PLAN.md:8, 06-02-PLAN.md:36, 06-02-PLAN.md:40, 06-02-PLAN.md:42, 06-02-PLAN.md:76, 06-02-PLAN.md:77, 06-02-PLAN.md:98, 06-06-PLAN.md:14, 06-06-PLAN.md:39, 06-06-PLAN.md:92, 06-06-PLAN.md:93

</details>

<details>
<summary><code>src/crud_views/lib/view/label_mode.py</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: src/crud_views/lib/view/label_mode.py</summary>

06-01-PLAN.md:79 — src/crud_views/lib/view/button_data.py; src/crud_views/lib/view/label_mode.py;

All citations: 06-01-PLAN.md:79, 06-02-PLAN.md:9, 06-02-PLAN.md:76, 06-02-PLAN.md:77

</details>

<details>
<summary><code>noxfile.py</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: noxfile.py</summary>

06-01-PLAN.md:80 — pyproject.toml; package.json; package-lock.json; noxfile.py.

All citations: 06-01-PLAN.md:80, 06-07-PLAN.md:14, 06-07-PLAN.md:31, 06-07-PLAN.md:37, 06-07-PLAN.md:112, 06-07-PLAN.md:113

</details>

<details>
<summary><code>pyproject.toml</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: pyproject.toml</summary>

06-01-PLAN.md:80 — pyproject.toml; package.json; package-lock.json; noxfile.py.

All citations: 06-01-PLAN.md:80, 06-07-PLAN.md:113

</details>

<details>
<summary><code>package.json</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: package.json</summary>

06-01-PLAN.md:80 — pyproject.toml; package.json; package-lock.json; noxfile.py.

All citations: 06-01-PLAN.md:80, 06-07-PLAN.md:71, 06-07-PLAN.md:79

</details>

<details>
<summary><code>package-lock.json</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: package-lock.json</summary>

06-01-PLAN.md:80 — pyproject.toml; package.json; package-lock.json; noxfile.py.

All citations: 06-01-PLAN.md:80, 06-07-PLAN.md:71

</details>

<details>
<summary><code>tests/test1/test_button_data.py</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: tests/test1/test_button_data.py</summary>

06-01-PLAN.md:124 — <automated>.venv/bin/pytest tests/test1/test_crispy_buttons.py tests/test1/test_button_data.py -q</automated>

All citations: 06-01-PLAN.md:124, 06-02-PLAN.md:14, 06-02-PLAN.md:89, 06-02-PLAN.md:98, 06-02-PLAN.md:111, 06-06-PLAN.md:105

</details>

<details>
<summary><code>tests/test1/test_crispy_buttons.py</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: tests/test1/test_crispy_buttons.py</summary>

06-01-PLAN.md:124 — <automated>.venv/bin/pytest tests/test1/test_crispy_buttons.py tests/test1/test_button_data.py -q</automated>

All citations: 06-01-PLAN.md:124, 06-01-PLAN.md:134, 06-02-PLAN.md:12, 06-02-PLAN.md:76, 06-02-PLAN.md:77, 06-02-PLAN.md:89, 06-02-PLAN.md:98, 06-02-PLAN.md:111, 06-03-PLAN.md:13, 06-03-PLAN.md:81, 06-03-PLAN.md:90, 06-03-PLAN.md:91, 06-03-PLAN.md:102, 06-04-PLAN.md:16, 06-04-PLAN.md:97, 06-04-PLAN.md:98, 06-04-PLAN.md:109, 06-05-PLAN.md:10, 06-05-PLAN.md:69, 06-05-PLAN.md:81, 06-05-PLAN.md:90, 06-05-PLAN.md:91, 06-05-PLAN.md:102, 06-07-PLAN.md:38, 06-07-PLAN.md:113

</details>

<details>
<summary><code>tests/test1/test_crud.py</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: tests/test1/test_crud.py</summary>

06-01-PLAN.md:134 — <read_first>tests/test1/test_crispy_buttons.py; tests/test1/test_crud.py; tests/test1/conftest.py; tests/test1/test_pagination_docs.py; .planning/phases/06-form-button-leaf/06-SPEC.md</read_first>

All citations: 06-01-PLAN.md:134, 06-01-PLAN.md:147, 06-02-PLAN.md:121, 06-02-PLAN.md:126, 06-09-PLAN.md:66

</details>

<details>
<summary><code>tests/test1/test_pagination_docs.py</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: tests/test1/test_pagination_docs.py</summary>

06-01-PLAN.md:134 — <read_first>tests/test1/test_crispy_buttons.py; tests/test1/test_crud.py; tests/test1/conftest.py; tests/test1/test_pagination_docs.py; .planning/phases/06-form-button-leaf/06-SPEC.md</read_first>

All citations: 06-01-PLAN.md:134, 06-08-PLAN.md:93

</details>

<details>
<summary><code>tests/test1/conftest.py</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: tests/test1/conftest.py</summary>

06-01-PLAN.md:134 — <read_first>tests/test1/test_crispy_buttons.py; tests/test1/test_crud.py; tests/test1/conftest.py; tests/test1/test_pagination_docs.py; .planning/phases/06-form-button-leaf/06-SPEC.md</read_first>

All citations: 06-01-PLAN.md:134

</details>

<details>
<summary><code>tests/test1/test_workflow.py</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: tests/test1/test_workflow.py</summary>

06-01-PLAN.md:157 — <read_first>tests/test1/test_workflow.py; tests/test1/test_filter.py; tests/test1/app/views.py; .planning/phases/06-form-button-leaf/06-SPEC.md</read_first>

All citations: 06-01-PLAN.md:157, 06-01-PLAN.md:167, 06-04-PLAN.md:98, 06-04-PLAN.md:109

</details>

<details>
<summary><code>tests/test1/app/views.py</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: tests/test1/app/views.py</summary>

06-01-PLAN.md:157 — <read_first>tests/test1/test_workflow.py; tests/test1/test_filter.py; tests/test1/app/views.py; .planning/phases/06-form-button-leaf/06-SPEC.md</read_first>

All citations: 06-01-PLAN.md:157

</details>

<details>
<summary><code>tests/test1/test_filter.py</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: tests/test1/test_filter.py</summary>

06-01-PLAN.md:157 — <read_first>tests/test1/test_workflow.py; tests/test1/test_filter.py; tests/test1/app/views.py; .planning/phases/06-form-button-leaf/06-SPEC.md</read_first>

All citations: 06-01-PLAN.md:157, 06-01-PLAN.md:167, 06-05-PLAN.md:9, 06-05-PLAN.md:30, 06-05-PLAN.md:69, 06-05-PLAN.md:70, 06-05-PLAN.md:81, 06-05-PLAN.md:90, 06-05-PLAN.md:91, 06-05-PLAN.md:102, 06-07-PLAN.md:113

</details>

<details>
<summary><code>.planning/phases/06-form-button-leaf/06-01-SUMMARY.md</code> — SKIPPED: declared phase output / execution summary</summary>

06-01-PLAN.md:205 — Create .planning/phases/06-form-button-leaf/06-01-SUMMARY.md with prerequisite and baseline commit evidence.

All citations: 06-01-PLAN.md:205

</details>

<details>
<summary><code>src/crud_views/templates/crud_views/tags/button/form.html</code> — SKIPPED: declared phase output / execution summary</summary>

06-02-PLAN.md:11 — - src/crud_views/templates/crud_views/tags/button/form.html

All citations: 06-02-PLAN.md:11, 06-02-PLAN.md:34, 06-02-PLAN.md:43, 06-02-PLAN.md:70, 06-02-PLAN.md:76, 06-04-PLAN.md:10, 06-04-PLAN.md:42, 06-04-PLAN.md:75

</details>

<details>
<summary><code>tests/test1/test_label_mode.py</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: tests/test1/test_label_mode.py</summary>

06-02-PLAN.md:13 — - tests/test1/test_label_mode.py

All citations: 06-02-PLAN.md:13, 06-02-PLAN.md:98, 06-06-PLAN.md:83

</details>

<details>
<summary><code>button_data.py</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: src/crud_views/lib/view/button_data.py</summary>

06-02-PLAN.md:70 — NEW template: src/crud_views/templates/crud_views/tags/button/form.html. NEW symbol: FORM_LEAF_KEYS in button_data.py. NEW normalized fields: cv_type, cv_name, cv_value, cv_id, cancel-only cv_cancel_url, cv_css_class, cv_flat_attrs; existing label/icon fields are reused. Private helper names are implementation-local. No new external package.

All citations: 06-02-PLAN.md:70

</details>

<details>
<summary><code>src/crud_views/templates/crud_views/tags/button/action.html</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: src/crud_views/templates/crud_views/tags/button/action.html</summary>

06-02-PLAN.md:77 — <read_first>06-01-SUMMARY.md in this phase directory; src/crud_views/templates/crud_views/tags/button/action.html; src/crud_views/lib/crispy/buttons.py; src/crud_views/lib/view/button_data.py; src/crud_views/lib/view/label_mode.py; tests/test1/test_crispy_buttons.py; tests/test1/test_button_leaves.py</read_first>

All citations: 06-02-PLAN.md:77, 06-04-PLAN.md:76

</details>

<details>
<summary><code>tests/test1/test_button_leaves.py</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: tests/test1/test_button_leaves.py</summary>

06-02-PLAN.md:77 — <read_first>06-01-SUMMARY.md in this phase directory; src/crud_views/templates/crud_views/tags/button/action.html; src/crud_views/lib/crispy/buttons.py; src/crud_views/lib/view/button_data.py; src/crud_views/lib/view/label_mode.py; tests/test1/test_crispy_buttons.py; tests/test1/test_button_leaves.py</read_first>

All citations: 06-02-PLAN.md:77, 06-02-PLAN.md:99

</details>

<details>
<summary><code>06-01-SUMMARY.md</code> — SKIPPED: declared phase output / execution summary</summary>

06-02-PLAN.md:77 — <read_first>06-01-SUMMARY.md in this phase directory; src/crud_views/templates/crud_views/tags/button/action.html; src/crud_views/lib/crispy/buttons.py; src/crud_views/lib/view/button_data.py; src/crud_views/lib/view/label_mode.py; tests/test1/test_crispy_buttons.py; tests/test1/test_button_leaves.py</read_first>

All citations: 06-02-PLAN.md:77, 06-02-PLAN.md:121

</details>

<details>
<summary><code>test_label_mode.py</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: tests/test1/test_label_mode.py</summary>

06-02-PLAN.md:107 — Update existing test_label_mode.py and test_button_data.py location/default assertions for form, retaining the set(LABEL_MODE_DEFAULTS) == LOCATIONS invariant and adding lazy override_settings coverage. Existing action contracts and location-independent finite class grammar remain unchanged.

All citations: 06-02-PLAN.md:107

</details>

<details>
<summary><code>test_button_data.py</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: tests/test1/test_button_data.py</summary>

06-02-PLAN.md:107 — Update existing test_label_mode.py and test_button_data.py location/default assertions for form, retaining the set(LABEL_MODE_DEFAULTS) == LOCATIONS invariant and adding lazy override_settings coverage. Existing action contracts and location-independent finite class grammar remain unchanged.

All citations: 06-02-PLAN.md:107, 06-06-PLAN.md:66

</details>

<details>
<summary><code>tests/test1/test_cancel_origin.py</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: tests/test1/test_cancel_origin.py</summary>

06-02-PLAN.md:121 — <read_first>06-01-SUMMARY.md in this phase directory; tests/test1/test_form_buttons_golden.py; tests/test1/test_crud.py; tests/test1/test_cancel_origin.py</read_first>

All citations: 06-02-PLAN.md:121, 06-02-PLAN.md:126, 06-09-PLAN.md:66

</details>

<details>
<summary><code>.planning/phases/06-form-button-leaf/06-02-SUMMARY.md</code> — SKIPPED: declared phase output / execution summary</summary>

06-02-PLAN.md:154 — Create .planning/phases/06-form-button-leaf/06-02-SUMMARY.md.

All citations: 06-02-PLAN.md:154

</details>

<details>
<summary><code>src/crud_views/lib/settings.py</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: src/crud_views/lib/settings.py</summary>

06-03-PLAN.md:8 — - src/crud_views/lib/settings.py

All citations: 06-03-PLAN.md:8, 06-03-PLAN.md:37, 06-03-PLAN.md:69, 06-03-PLAN.md:70, 06-06-PLAN.md:8, 06-06-PLAN.md:71, 06-06-PLAN.md:72

</details>

<details>
<summary><code>src/crud_views/lib/viewset/__init__.py</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: src/crud_views/lib/viewset/__init__.py</summary>

06-03-PLAN.md:9 — - src/crud_views/lib/viewset/__init__.py

All citations: 06-03-PLAN.md:9, 06-03-PLAN.md:69, 06-03-PLAN.md:70, 06-06-PLAN.md:9, 06-06-PLAN.md:71, 06-06-PLAN.md:72

</details>

<details>
<summary><code>src/crud_views/lib/view/base.py</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: src/crud_views/lib/view/base.py</summary>

06-03-PLAN.md:10 — - src/crud_views/lib/view/base.py

All citations: 06-03-PLAN.md:10, 06-03-PLAN.md:28, 06-03-PLAN.md:34, 06-03-PLAN.md:36, 06-03-PLAN.md:69, 06-03-PLAN.md:70, 06-06-PLAN.md:10, 06-06-PLAN.md:35, 06-06-PLAN.md:71, 06-06-PLAN.md:72, 06-06-PLAN.md:92

</details>

<details>
<summary><code>tests/test1/test_action_label_mode_config.py</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: tests/test1/test_action_label_mode_config.py</summary>

06-03-PLAN.md:12 — - tests/test1/test_action_label_mode_config.py

All citations: 06-03-PLAN.md:12, 06-03-PLAN.md:69, 06-03-PLAN.md:70, 06-03-PLAN.md:81, 06-03-PLAN.md:102, 06-06-PLAN.md:72, 06-06-PLAN.md:83

</details>

<details>
<summary><code>.planning/phases/06-form-button-leaf/06-03-SUMMARY.md</code> — SKIPPED: declared phase output / execution summary</summary>

06-03-PLAN.md:128 — Create .planning/phases/06-form-button-leaf/06-03-SUMMARY.md.

All citations: 06-03-PLAN.md:128

</details>

<details>
<summary><code>src/crud_views/lib/button_classes.py</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: src/crud_views/lib/button_classes.py</summary>

06-04-PLAN.md:8 — - src/crud_views/lib/button_classes.py

All citations: 06-04-PLAN.md:8, 06-04-PLAN.md:34, 06-04-PLAN.md:43, 06-04-PLAN.md:75, 06-04-PLAN.md:76

</details>

<details>
<summary><code>src/crud_views/lib/icons.py</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: src/crud_views/lib/icons.py</summary>

06-04-PLAN.md:9 — - src/crud_views/lib/icons.py

All citations: 06-04-PLAN.md:9, 06-04-PLAN.md:32, 06-04-PLAN.md:75, 06-04-PLAN.md:76

</details>

<details>
<summary><code>tests/test1/test_icon_host_leaves.py</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: tests/test1/test_icon_host_leaves.py</summary>

06-04-PLAN.md:11 — - tests/test1/test_icon_host_leaves.py

All citations: 06-04-PLAN.md:11, 06-04-PLAN.md:75, 06-04-PLAN.md:76, 06-04-PLAN.md:88

</details>

<details>
<summary><code>docs/reference/buttons.md</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: docs/reference/buttons.md</summary>

06-04-PLAN.md:12 — - docs/reference/buttons.md

All citations: 06-04-PLAN.md:12, 06-04-PLAN.md:75, 06-04-PLAN.md:84, 06-08-PLAN.md:8, 06-08-PLAN.md:77, 06-08-PLAN.md:78

</details>

<details>
<summary><code>src/crud_views_workflow/lib/forms.py</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: src/crud_views_workflow/lib/forms.py</summary>

06-04-PLAN.md:14 — - src/crud_views_workflow/lib/forms.py

All citations: 06-04-PLAN.md:14, 06-04-PLAN.md:36, 06-04-PLAN.md:97, 06-04-PLAN.md:98

</details>

<details>
<summary><code>tests/test1/test_icons_registry.py</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: tests/test1/test_icons_registry.py</summary>

06-04-PLAN.md:76 — <read_first>src/crud_views/lib/button_classes.py; src/crud_views/lib/icons.py; tests/test1/test_icon_host_leaves.py; tests/test1/test_icons_registry.py; src/crud_views/templates/crud_views/tags/button/action.html</read_first>

All citations: 06-04-PLAN.md:76, 06-04-PLAN.md:88, 06-04-PLAN.md:109

</details>

<details>
<summary><code>test_icon_host_leaves.py</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: tests/test1/test_icon_host_leaves.py</summary>

06-04-PLAN.md:84 — Update the canonical default-key count in docs/reference/buttons.md in this task when adding utility keys, so the existing live-count test remains green. Put any new class/utility regression cases in test_icon_host_leaves.py alongside real rendering, keeping this task within its declared five files; 06-08 completes the surrounding documentation.

All citations: 06-04-PLAN.md:84

</details>

<details>
<summary><code>tests/test1/test_button_classes.py</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: tests/test1/test_button_classes.py</summary>

06-04-PLAN.md:88 — <automated>.venv/bin/pytest tests/test1/test_icon_host_leaves.py tests/test1/test_button_classes.py tests/test1/test_icons_registry.py -q</automated>

All citations: 06-04-PLAN.md:88, 06-08-PLAN.md:83

</details>

<details>
<summary><code>.planning/phases/06-form-button-leaf/06-04-SUMMARY.md</code> — SKIPPED: declared phase output / execution summary</summary>

06-04-PLAN.md:135 — Create .planning/phases/06-form-button-leaf/06-04-SUMMARY.md.

All citations: 06-04-PLAN.md:135

</details>

<details>
<summary><code>docs/reference/list_view.md</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: docs/reference/list_view.md</summary>

06-05-PLAN.md:70 — <read_first>src/crud_views/lib/views/list.py; src/crud_views/lib/views/mixins.py (get_filterset); tests/test1/test_filter.py; docs/reference/list_view.md (field-only helper example); 06-SPEC.md in this phase directory</read_first>

All citations: 06-05-PLAN.md:70, 06-08-PLAN.md:14, 06-08-PLAN.md:92, 06-08-PLAN.md:93

</details>

<details>
<summary><code>docs/getting_started/tutorial-5-filters-permissions.md</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: docs/getting_started/tutorial-5-filters-permissions.md</summary>

06-05-PLAN.md:91 — <read_first>docs/getting_started/tutorial-5-filters-permissions.md; tests/test1/test_filter.py; tests/test1/test_crispy_buttons.py</read_first>

All citations: 06-05-PLAN.md:91, 06-08-PLAN.md:15, 06-08-PLAN.md:92, 06-08-PLAN.md:93

</details>

<details>
<summary><code>.planning/phases/06-form-button-leaf/06-05-SUMMARY.md</code> — SKIPPED: declared phase output / execution summary</summary>

06-05-PLAN.md:129 — Create .planning/phases/06-form-button-leaf/06-05-SUMMARY.md.

All citations: 06-05-PLAN.md:129

</details>

<details>
<summary><code>src/crud_views/lib/view/action_menu.py</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: src/crud_views/lib/view/action_menu.py</summary>

06-06-PLAN.md:11 — - src/crud_views/lib/view/action_menu.py

All citations: 06-06-PLAN.md:11, 06-06-PLAN.md:36, 06-06-PLAN.md:71, 06-06-PLAN.md:72

</details>

<details>
<summary><code>tests/test1/test_form_button_checks.py</code> — SKIPPED: declared phase output / execution summary</summary>

06-06-PLAN.md:12 — - tests/test1/test_form_button_checks.py

All citations: 06-06-PLAN.md:12, 06-06-PLAN.md:30, 06-06-PLAN.md:66, 06-06-PLAN.md:71, 06-06-PLAN.md:83, 06-06-PLAN.md:92, 06-06-PLAN.md:105, 06-07-PLAN.md:113, 06-09-PLAN.md:33

</details>

<details>
<summary><code>src/crud_views/lib/view/buttons.py</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: src/crud_views/lib/view/buttons.py</summary>

06-06-PLAN.md:13 — - src/crud_views/lib/view/buttons.py

All citations: 06-06-PLAN.md:13, 06-06-PLAN.md:32, 06-06-PLAN.md:38, 06-06-PLAN.md:92, 06-06-PLAN.md:93

</details>

<details>
<summary><code>view/buttons.py</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: src/crud_views/lib/view/buttons.py</summary>

06-06-PLAN.md:66 — NEW test file: tests/test1/test_form_button_checks.py. NEW private/static form icon checker in view/buttons.py (suggested cv_form_icon_mode_checks). No new check IDs. Finite form contract tests live in this file or existing test_button_data.py read-only coverage; no new generic diagnostic framework.

All citations: 06-06-PLAN.md:66

</details>

<details>
<summary><code>checks.py</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: src/crud_views_workflow/checks.py, src/crud_views/checks.py</summary>

06-06-PLAN.md:80 — Extend established checks at their existing owners, not only checks.py registration. For a form mapping, distinguish shape from values: non-dict/non-string keys produce E211 for the view attribute; string-keyed mappings with invalid mode values produce E210 entry diagnostics. Unknown string kinds produce W291 against FORM_KINDS, including ViewSet/settings-selected form maps where statically available, with deterministic dedup so one effective issue is not repeated per control. Preserve existing settings E106 validation and ViewSet Pydantic validation semantics; do not rename prior IDs to force uniformity. Add form floor coverage for lazy override_settings, malformed None/list/dict data and strict nested recovery. Drive real check_viewsets as well as targeted Check objects. All checked malformed inputs must produce diagnostics without exceptions.

All citations: 06-06-PLAN.md:80

</details>

<details>
<summary><code>.planning/phases/06-form-button-leaf/06-06-SUMMARY.md</code> — SKIPPED: declared phase output / execution summary</summary>

06-06-PLAN.md:132 — Create .planning/phases/06-form-button-leaf/06-06-SUMMARY.md.

All citations: 06-06-PLAN.md:132

</details>

<details>
<summary><code>tests/js/modal.test.js</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: tests/js/modal.test.js</summary>

06-07-PLAN.md:8 — - tests/js/modal.test.js

All citations: 06-07-PLAN.md:8, 06-07-PLAN.md:29, 06-07-PLAN.md:35, 06-07-PLAN.md:70, 06-07-PLAN.md:71, 06-07-PLAN.md:83

</details>

<details>
<summary><code>src/crud_views/static/crud_views/js/modal.js</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: src/crud_views/static/crud_views/js/modal.js</summary>

06-07-PLAN.md:9 — - src/crud_views/static/crud_views/js/modal.js

All citations: 06-07-PLAN.md:9, 06-07-PLAN.md:34, 06-07-PLAN.md:70, 06-07-PLAN.md:71

</details>

<details>
<summary><code>tests/js/viewset.test.js</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: tests/js/viewset.test.js</summary>

06-07-PLAN.md:10 — - tests/js/viewset.test.js

All citations: 06-07-PLAN.md:10, 06-07-PLAN.md:92, 06-07-PLAN.md:93, 06-07-PLAN.md:103

</details>

<details>
<summary><code>tests/js/list.filter.test.js</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: tests/js/list.filter.test.js</summary>

06-07-PLAN.md:11 — - tests/js/list.filter.test.js

All citations: 06-07-PLAN.md:11, 06-07-PLAN.md:92, 06-07-PLAN.md:93, 06-07-PLAN.md:103

</details>

<details>
<summary><code>src/crud_views/static/crud_views/js/viewset.js</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: src/crud_views/static/crud_views/js/viewset.js</summary>

06-07-PLAN.md:12 — - src/crud_views/static/crud_views/js/viewset.js

All citations: 06-07-PLAN.md:12, 06-07-PLAN.md:92, 06-07-PLAN.md:93

</details>

<details>
<summary><code>src/crud_views/static/crud_views/js/list.filter.js</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: src/crud_views/static/crud_views/js/list.filter.js</summary>

06-07-PLAN.md:13 — - src/crud_views/static/crud_views/js/list.filter.js

All citations: 06-07-PLAN.md:13, 06-07-PLAN.md:92, 06-07-PLAN.md:93

</details>

<details>
<summary><code>tests/js/helpers/setup.js</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: tests/js/helpers/setup.js</summary>

06-07-PLAN.md:71 — <read_first>package.json; package-lock.json; vitest.config.js; tests/js/modal.test.js; tests/js/helpers/setup.js; src/crud_views/static/crud_views/js/modal.js; 06-RESEARCH.md Package Legitimacy Audit</read_first>

All citations: 06-07-PLAN.md:71

</details>

<details>
<summary><code>vitest.config.js</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: vitest.config.js</summary>

06-07-PLAN.md:71 — <read_first>package.json; package-lock.json; vitest.config.js; tests/js/modal.test.js; tests/js/helpers/setup.js; src/crud_views/static/crud_views/js/modal.js; 06-RESEARCH.md Package Legitimacy Audit</read_first>

All citations: 06-07-PLAN.md:71

</details>

<details>
<summary><code>06-RESEARCH.md</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: .planning/phases/06-form-button-leaf/06-RESEARCH.md</summary>

06-07-PLAN.md:71 — <read_first>package.json; package-lock.json; vitest.config.js; tests/js/modal.test.js; tests/js/helpers/setup.js; src/crud_views/static/crud_views/js/modal.js; 06-RESEARCH.md Package Legitimacy Audit</read_first>

All citations: 06-07-PLAN.md:71, 06-07-PLAN.md:113

</details>

<details>
<summary><code>modal.js</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: src/crud_views/static/crud_views/js/modal.js</summary>

06-07-PLAN.md:80 — Extend the existing modal suite using native SubmitEvent and native FormData, real button elements with nested icon/text, multiple submitters, no submitter, delete=Delete and literal malicious/Unicode values. Fetch may be spied to inspect its FormData, but do not replace browser constructors or fake submitter support. Change modal.js only if a demonstrated regression requires it; keep its current error, CSRF and authorization interactions.

All citations: 06-07-PLAN.md:80

</details>

<details>
<summary><code>.planning/phases/06-form-button-leaf/06-07-SUMMARY.md</code> — SKIPPED: declared phase output / execution summary</summary>

06-07-PLAN.md:145 — Create .planning/phases/06-form-button-leaf/06-07-SUMMARY.md.

All citations: 06-07-PLAN.md:145

</details>

<details>
<summary><code>docs/reference/settings.md</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: docs/reference/settings.md</summary>

06-08-PLAN.md:9 — - docs/reference/settings.md

All citations: 06-08-PLAN.md:9, 06-08-PLAN.md:42, 06-08-PLAN.md:77, 06-08-PLAN.md:78

</details>

<details>
<summary><code>docs/reference/action_menus.md</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: docs/reference/action_menus.md</summary>

06-08-PLAN.md:10 — - docs/reference/action_menus.md

All citations: 06-08-PLAN.md:10, 06-08-PLAN.md:41, 06-08-PLAN.md:77, 06-08-PLAN.md:78

</details>

<details>
<summary><code>tests/test1/test_label_mode_docs.py</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: tests/test1/test_label_mode_docs.py</summary>

06-08-PLAN.md:11 — - tests/test1/test_label_mode_docs.py

All citations: 06-08-PLAN.md:11, 06-08-PLAN.md:77, 06-08-PLAN.md:78, 06-08-PLAN.md:83

</details>

<details>
<summary><code>docs/reference/icons.md</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: docs/reference/icons.md</summary>

06-08-PLAN.md:12 — - docs/reference/icons.md

All citations: 06-08-PLAN.md:12, 06-08-PLAN.md:92, 06-08-PLAN.md:93

</details>

<details>
<summary><code>docs/reference/theme.md</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: docs/reference/theme.md</summary>

06-08-PLAN.md:13 — - docs/reference/theme.md

All citations: 06-08-PLAN.md:13, 06-08-PLAN.md:44, 06-08-PLAN.md:92, 06-08-PLAN.md:93

</details>

<details>
<summary><code>tests/test1/test_form_button_docs.py</code> — SKIPPED: declared phase output / execution summary</summary>

06-08-PLAN.md:16 — - tests/test1/test_form_button_docs.py

All citations: 06-08-PLAN.md:16, 06-08-PLAN.md:36, 06-08-PLAN.md:45, 06-08-PLAN.md:72, 06-08-PLAN.md:92, 06-08-PLAN.md:98

</details>

<details>
<summary><code>CHANGELOG.md</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: CHANGELOG.md</summary>

06-08-PLAN.md:17 — - CHANGELOG.md

All citations: 06-08-PLAN.md:17, 06-08-PLAN.md:107, 06-08-PLAN.md:108

</details>

<details>
<summary><code>docs/migrating-1.0.md</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: docs/migrating-1.0.md</summary>

06-08-PLAN.md:18 — - docs/migrating-1.0.md

All citations: 06-08-PLAN.md:18, 06-08-PLAN.md:34, 06-08-PLAN.md:107, 06-08-PLAN.md:108, 06-09-PLAN.md:81

</details>

<details>
<summary><code>examples/bootstrap5/project/settings.py</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: examples/bootstrap5/project/settings.py</summary>

06-08-PLAN.md:19 — - examples/bootstrap5/project/settings.py

All citations: 06-08-PLAN.md:19, 06-08-PLAN.md:38, 06-08-PLAN.md:107, 06-08-PLAN.md:108, 06-09-PLAN.md:81

</details>

<details>
<summary><code>action_menus.md</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: docs/reference/action_menus.md</summary>

06-08-PLAN.md:80 — Replace obsolete statements that form controls never choose modes or render icons. Document the separate FORM_LEAF_KEYS contract, cancel-only URL, cv_css_class/cv_flat_attrs, literal text boundary, class mode lookup and form utility keys. Keep the canonical form resolution order in action_menus.md: first select owner (D-09–D-12), then whole view/ViewSet/settings map, then lazy floor for a missing key. Add the Form column and getter, and extend the single merge/replace table in settings.md rather than duplicating resolution prose across pages. State empty map versus None precisely. Preserve the class grammar and update its live default-key count from DEFAULT_BUTTON_CLASSES. Extend existing meaningful doc/recipe tests to render a documented form configuration, proving both/icon output rather than checking strings alone.

All citations: 06-08-PLAN.md:80

</details>

<details>
<summary><code>settings.md</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: docs/reference/settings.md</summary>

06-08-PLAN.md:80 — Replace obsolete statements that form controls never choose modes or render icons. Document the separate FORM_LEAF_KEYS contract, cancel-only URL, cv_css_class/cv_flat_attrs, literal text boundary, class mode lookup and form utility keys. Keep the canonical form resolution order in action_menus.md: first select owner (D-09–D-12), then whole view/ViewSet/settings map, then lazy floor for a missing key. Add the Form column and getter, and extend the single merge/replace table in settings.md rather than duplicating resolution prose across pages. State empty map versus None precisely. Preserve the class grammar and update its live default-key count from DEFAULT_BUTTON_CLASSES. Extend existing meaningful doc/recipe tests to render a documented form configuration, proving both/icon output rather than checking strings alone.

All citations: 06-08-PLAN.md:80

</details>

<details>
<summary><code>examples/bootstrap5/test_docs_sync.py</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: examples/bootstrap5/test_docs_sync.py</summary>

06-08-PLAN.md:108 — <read_first>CHANGELOG.md; docs/migrating-1.0.md; examples/bootstrap5/project/settings.py; examples/bootstrap5/test_docs_sync.py</read_first>

All citations: 06-08-PLAN.md:108

</details>

<details>
<summary><code>.planning/phases/06-form-button-leaf/06-08-SUMMARY.md</code> — SKIPPED: declared phase output / execution summary</summary>

06-08-PLAN.md:139 — Create .planning/phases/06-form-button-leaf/06-08-SUMMARY.md.

All citations: 06-08-PLAN.md:139

</details>

<details>
<summary><code>.planning/phases/06-form-button-leaf/06-ACCEPTANCE.md</code> — SKIPPED: declared phase output / execution summary</summary>

06-09-PLAN.md:8 — - .planning/phases/06-form-button-leaf/06-ACCEPTANCE.md

All citations: 06-09-PLAN.md:8, 06-09-PLAN.md:24, 06-09-PLAN.md:29, 06-09-PLAN.md:60, 06-09-PLAN.md:65, 06-09-PLAN.md:80

</details>

<details>
<summary><code>06-VALIDATION.md</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: .planning/phases/06-form-button-leaf/06-VALIDATION.md</summary>

06-09-PLAN.md:60 — NEW file: .planning/phases/06-form-button-leaf/06-ACCEPTANCE.md. Existing 06-VALIDATION.md receives measured results. No new product/test symbols.

All citations: 06-09-PLAN.md:60, 06-09-PLAN.md:66, 06-09-PLAN.md:81

</details>

<details>
<summary><code>SUMMARY.md</code> — SKIPPED: declared phase output / execution summary</summary>

06-09-PLAN.md:66 — <read_first>All 06-*-SUMMARY.md files; 06-SPEC.md; 06-VALIDATION.md; 06-01 baseline commit evidence; tests/test1/test_crud.py; tests/test1/test_cancel_origin.py</read_first>

All citations: 06-09-PLAN.md:66

</details>

<details>
<summary><code>06-08-SUMMARY.md</code> — SKIPPED: declared phase output / execution summary</summary>

06-09-PLAN.md:81 — <read_first>examples/bootstrap5/project/settings.py; docs/migrating-1.0.md Form buttons; 06-07-SUMMARY.md; 06-08-SUMMARY.md; 06-VALIDATION.md</read_first>

All citations: 06-09-PLAN.md:81

</details>

<details>
<summary><code>06-07-SUMMARY.md</code> — SKIPPED: declared phase output / execution summary</summary>

06-09-PLAN.md:81 — <read_first>examples/bootstrap5/project/settings.py; docs/migrating-1.0.md Form buttons; 06-07-SUMMARY.md; 06-08-SUMMARY.md; 06-VALIDATION.md</read_first>

All citations: 06-09-PLAN.md:81

</details>

<details>
<summary><code>examples/bootstrap5/manage.py</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: examples/bootstrap5/manage.py</summary>

06-09-PLAN.md:234 — <automated>.venv/bin/python examples/bootstrap5/manage.py check</automated>

All citations: 06-09-PLAN.md:234

</details>

<details>
<summary><code>test_docs_sync.py</code> — UNCHECKABLE by empty intel index; supplemental filesystem readable: examples/bootstrap5/test_docs_sync.py</summary>

06-09-PLAN.md:238 — <automated>cd examples/bootstrap5 && ../../.venv/bin/pytest test_docs_sync.py -q</automated>

All citations: 06-09-PLAN.md:238

</details>

<details>
<summary><code>.planning/phases/06-form-button-leaf/06-09-SUMMARY.md</code> — SKIPPED: declared phase output / execution summary</summary>

06-09-PLAN.md:258 — Create .planning/phases/06-form-button-leaf/06-09-SUMMARY.md.

All citations: 06-09-PLAN.md:258

</details>
