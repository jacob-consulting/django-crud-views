I have verified every seam the plans rely on against the checkout. Review follows.

# Phase 06.6 Plan Review — verified against source at `7be4a7f`

Review method: I opened every product file, test, golden, template, nox session and cached runtime the nine plans cite, and traced each mechanism the plans claim. Where I could not verify something (sibling companion directories are outside my allowed working directory), I say so and downgrade to an open question.

Key source facts that anchor the whole phase, all confirmed:

- Nested form and duplicate token are real today: `tests/test1/golden/form_frame/create.html:1` is literally `<form class="cv-form" …><input …csrfmiddlewaretoken…><form method="post" ><input …csrfmiddlewaretoken…>…</form></form>`; same in `delete.html:1`. Cause: `src/crud_views/templates/crud_views/tags/form.html:3-7` branches on `{% if form.helper %}` and renders `form.helper` twice, and both library helpers leave crispy defaults (`src/crud_views/lib/crispy/form.py:43-50`, `136-146`).
- Workflow bypasses the shared tag: `src/crud_views_workflow/templates/crud_views_workflow/view_workflow.action.html:15` calls `{% crispy form form.helper %}` directly inside its own `<form>` (line 8).
- The crispy floor really ignores group classes: `.nox/crispy_floor-3-12-django-6-0/.../bootstrap5/layout/formactions.html:1` hardcodes `class="mb-3"`, and its `{% if formactions.attrs %}` tests an attribute `FormActions.__init__` never sets (`crispy_forms/bootstrap.py:299-304` sets only `flat_attrs`), so neither `css_class` nor extra kwargs reach the DOM at the floor. The current pack reads `formactions.css_class` (`.nox/tests-3-12-django-5-2/.../formactions.html:3`).
- Three cached runtimes exist as the plans name them: `.nox/tests-3-12-django-4-2`, `.nox/tests-3-12-django-5-2`, `.nox/crispy_floor-3-12-django-6-0`.
- The pinned baseline revision `cb26af4dfef2afb31d774a219abfad1c675cdff1` exists (a planning-docs commit; product source equals the research HEAD).

---

## 06.6-01

**Summary.** The tracer correctly targets the real defect and the real seam. The plan's mechanism claims hold: the crispy token branch is independent of `form_tag` (`crispy_bootstrap5/templates/bootstrap5/whole_uni_form.html:4-7` at the floor), `get_response_dict` reads `disable_csrf` and `form_tag` from `helper.get_attributes()` (`crispy_forms/templatetags/crispy_forms_tags.py:146-159`), and the raw action is stored in `_form_action` while the `form_action` property calls `reverse()` (`crispy_forms/helper.py:234-242`), so the "diagnose without reverse" instruction is implementable exactly as written. Enforced-CSRF testing has an in-repo precedent the plan does not cite but can copy (`tests/test1/test_form_validation.py:78-110`).

**Strengths.**
- Selecting the helper once is necessary, not cosmetic: `CrispyFormMixin.helper` allocates per access (`form.py:43-50`), and `{% if form.helper %}` is truthiness over `FormHelper.__len__`, which is why `ListViewFilterFormHelper` had to define `__bool__` (`src/crud_views/lib/views/list.py:135-137`). The plan's "presence, not truthiness" rule is grounded.
- The D-01 blast radius inside this repo is small and verified: the only application helper overrides are `tests/test1/app/views_formset.py:44-50` (builds on `super().helper`, sets `form_tag=False`) and the example login form `examples/bootstrap5/project/urls.py:13-18`, which renders through standalone crispy, not `cv_render_form`, so the plan's "standalone crispy untouched" boundary keeps the example green.
- Keeping diagnostics in the tag (`src/crud_views/templatetags/crud_views.py:465-466`) rather than a startup check is consistent with how W292 already refuses to instantiate forms (`src/crud_views/lib/view/buttons.py:546-556`).

**Concerns.**
- **MEDIUM — the plan makes CSRF suppression for library helpers depend on the copy experiment.** Task 01-01 says to set only `form_tag=False` on the two library helpers and rely on a render-local copy for `disable_csrf`. The package already has the direct pattern for library-owned helpers: `src/crud_views/lib/formsets/inline_formset.py:57-60` and `:143-146` set both `form_tag = False` and `disable_csrf = True`. Setting both directly on `CrispyFormMixin.helper`/`CrispyDeleteForm.helper` removes the stock pages from research assumption A2 entirely; the copy strategy is then needed only for application helpers. As written, a failed copy experiment would block even the stock fix.
- **MEDIUM — a copied `tags/form.html` that still reads `form.helper` silently regresses to two tokens.** Diagnostics run in the tag, so an overriding theme template gets the checks but, if it ignores `cv_form_helper`, renders a fresh helper with `disable_csrf=False`. The plan tests the recipe (01-02) and documents it (08), which is the right scope, but the summary should state plainly that this case is undetectable by the library.
- **LOW — "configured wrapper intent" vs `form_class`.** `get_attributes` folds `form_class` into `attrs["class"]` (`helper.py:296-302`), which crispy also exposes as `form_class` to the pack and which `formactions.html` reads for `form-horizontal` (current pack line 3). Warning on it is correct per D-03, but the message must not claim the class has no effect; the plan already says this. Keep it.
- **LOW — baseline archive.** 01-01 asks the executor to archive `cb26af4` before editing; plan 06 pins the same revision. Fine, but do it once and reference it, or two wave-1 agents will each archive.

**Suggestions.**
- Change 01-01 to set `form_tag=False` and `disable_csrf=True` on both library helpers, mirroring `inline_formset.py:57-60`; scope the copy experiment to application helpers only.
- Add `/publisher-formset/create/` to the raw-count assertions: `tests/test1/test_formsets.py:19-33` is the only existing raw nested-form guard and proves the breakage mechanism (`formset.js` binds `form.cv-form`); that page's parent helper override (`views_formset.py:44-50`) sets only `form_tag=False`, so it currently emits two tokens.
- Cite `test_form_validation.py:78-110` as the `enforce_csrf_checks` analog in `read_first`.

**Risk: MEDIUM.** Mechanisms verified; the main risk is self-inflicted coupling of the stock fix to the helper-copy experiment.

---

## 06.6-02

**Summary.** The plan matches the resolver exactly. `default_label_mode` has four package-only exits that must become theme-then-package (`src/crud_views/lib/view/label_mode.py:101`, `107`, `110`, `118`); E108 validates the raw setting with `LOCATIONS`/`LABEL_MODES`/`is_label_mode` (`src/crud_views/lib/settings.py:159-188`); and both W292 checks reach the floor through the public resolver (`buttons.py:435-437` for context; `buttons.py:568-571` → `base.py:349` → `form_label_mode` → `default_label_mode` for forms). The plan's instruction "do not modify checks merely to make already-correct wiring appear new" is correct and well judged.

**Strengths.**
- Reuses the `_invalid_label_mode` strict/warn-once machinery (`label_mode.py:63-83`) and the existing `override_settings` test shapes (`tests/test1/test_label_mode.py:104-135`).
- Registry isolation copies a proven fixture (`tests/test1/test_button_classes.py:94-101`); the existing autouse fixture only resets `_warned` (`tests/test1/conftest.py:23-32`), so the new fixture is genuinely needed.
- Atomic validation before commit is the right correction to the class registry's unvalidated `.update()` (`src/crud_views/lib/button_classes.py:135-138`).

**Concerns.**
- **LOW — commit semantics under concurrent readers.** "Validate whole dict, then update" should rebind a new merged dict rather than `.update()` the shared module global, so a render in another thread never observes a half-merged map. Cheap to specify.
- **LOW — unknown-location registration.** Use `button_data.LOCATIONS` via the same deferred import pattern (`label_mode.py:94-95`) so a theme registering `{"toolbar": "both"}` is rejected with the same vocabulary E108 uses.
- **LOW — plan touches `src/crud_views/lib/settings.py`.** Nothing in E108 needs to change for correctness; only docstring/description text. Keep the diff to prose to avoid accidental semantic drift in a check that 06.1/06.5 verified.

**Suggestions.**
- State the rebind-not-mutate commit rule in 02-01.
- Add one test that `register_label_mode_defaults` followed by `override_settings(CRUD_VIEWS_LABEL_MODE_DEFAULTS=...)` and exit restores the theme value, not the package value (the D-15 layering in both directions).

**Risk: LOW.**

---

## 06.6-03

**Summary.** The plan's premise is positively true at the floor (see anchor facts) and its chosen bridge is viable: `FormActions.__init__` accepts a per-instance `template=` (`crispy_forms/bootstrap.py:299-303`), so a private `_ThemedFormActions` can point at a library-local template without shadowing `bootstrap5/layout/formactions.html`. The three construction sites are exactly where the plan says (`form.py:55-56`, `form.py:141-144`, `list.py:125-133`), and the delete helper indeed bypasses `get_form_actions`.

**Strengths.**
- Refuses to rely on `css_class` alone, which the floor evidence demands.
- Preserves the filter helper's prepared-layout lifecycle (`list.py:150-170`) by styling only the default group.
- Requires both current and floor runtimes in the first task, not as a late matrix.

**Concerns.**
- **HIGH — the pack-selection rule is underspecified, and the wrong choice violates D-10.** The plan says "derive and test a conservative selection rule from installed source/capabilities." Two tempting rules fail: a version threshold (forbidden by the plan itself) and template-source sniffing (breaks on a custom pack such as crispy-tabler whose `formactions.html` renders `form-footer` and may or may not read `css_class`). The only rule that respects arbitrary packs is a feature probe: render a `FormActions(css_class=<sentinel>)` once per `CRISPY_TEMPLATE_PACK`, cache whether the sentinel survives, and use the library-local template only when it does not. Spell this out; otherwise plan 07's crispy-tabler run may get a Bootstrap-shaped wrapper injected.
- **MEDIUM — `tests/test1/test_button_classes.py` is missing from `files_modified`.** `test_default_table_is_complete` hardcodes `len(EXPECTED_KEYS) == 84` and `set(DEFAULT_BUTTON_CLASSES) == EXPECTED_KEYS` (`tests/test1/test_button_classes.py:21`, `104-106`). Adding `form:actions`/`form:filter-actions` breaks it, and none of 03's verify selections include that file, so the break surfaces only in plan 09's full run. Same omission in plan 04.
- **LOW — W362 behavior claim verified.** `_action_key_parts("form:actions:icon")` returns `None` because `actions` is not in `FORM_KINDS` (`button_classes.py:240`, `263`), so mode-suffixed group keys fall to the "not a known key" branch (`button_classes.py:343-346`) as the plan states.

**Suggestions.**
- Replace "derive a selection rule" with the feature-probe rule above, cached per pack and reset on `setting_changed` like `get_button_classes` (`button_classes.py:129-132`).
- Add `tests/test1/test_button_classes.py` to files and to the 03-02 verify selection.
- The library-local fallback template must reproduce the floor's `label_class`/`field_class` context usage (`floor formactions.html:2-8`), and the test should diff the empty-class output against the floor's original bytes, as the plan already implies.

**Risk: MEDIUM** (HIGH if the selection rule is left to execution-time judgment).

---

## 06.6-04

**Summary.** Smallest and best-grounded plan. The literals and hooks are exactly where stated (`src/crud_views/templates/crud_views/tags/alert.html:2-5`), the golden is raw bytes (`tests/test1/golden/alerts/dismissible.html`), and the exact-class assertion already exists (`tests/test1/test_alerts.py:191-198`). `cv_button_class` is an autoescaped simple tag (`src/crud_views/templatetags/crud_views.py:571-573`), and 2-segment keys are accepted by W362 once in `DEFAULT_BUTTON_CLASSES` (`button_classes.py:328-329`) while `alert:*:mode` is rejected because `alert` is in neither `VARIANT_LOCATIONS` nor the form branch (`button_classes.py:239-240`, `263`).

**Strengths.**
- `test_only_the_alert_templates_write_alert_markup` scans templates, not Python (`test_alerts.py:151-163`), so moving the literal into `button_classes.py` is safe.
- Existing adapter tests cover ownership and fallback (`tests/js/adapters.test.js:223-304`); the plan reuses rather than duplicates them.

**Concerns.**
- **MEDIUM — whitespace contract for empty/None values is unstated.** `{% if alert.dismissible %} {% cv_button_class "alert" "dismissible" %}{% endif %}` yields `class="alert alert-success "` when a theme sets the key to `""`. That is harmless in browsers, but the plan promises both byte-identical defaults and "omission" without saying which form the omitted case takes; `test_dismissible_alert_preserves_frame_contract` compares the exact attribute string. Decide (accept the trailing space, or strip inside a tiny helper) and test it.
- **LOW — files list omits `tests/test1/test_button_classes.py`** (same hard-coded 84-key set as noted for plan 03).

**Suggestions.**
- State the empty-value whitespace rule and add a parametrized test over `""`, `None`, and a hostile value.
- Add `tests/test1/test_button_classes.py` to files and to the 04-02 verify selection.

**Risk: LOW.**

---

## 06.6-05

**Summary.** The expansion targets are correct. All four content templates render through `cv_render_form` (`view_create.content.html:10`, `view_update.content.html:10`, `view_custom_form.content.html:10`, `view_delete.content.html:21`); the delete page omits its form when `has_protected_objects` (`view_delete.content.html:15-23`) and workflow omits it without choices (`view_workflow.action.html:6-19`), so the plan's "assert one only for an actionable form" rule matches the templates. `X-CV-Modal` is the real header (`src/crud_views/lib/view/base.py:57-59`), and `WorkflowForm` extends `CrispyForm` (`src/crud_views_workflow/lib/forms.py:11`), so routing it through `cv_render_form` inherits plan 01's helper fix.

**Strengths.**
- The four goldens show precisely the inner `<form method="post" >` and second token to remove; `delete_protection.html` has no form and stays untouched.
- `test_theme_frame_wraps_the_form` counts opening versus closing `<form` (`tests/test1/test_form_frame.py:82-87`) and survives the change, so no hidden golden churn there.
- Modal 422 and 204 contracts already have tests to preserve (`tests/test1/test_modal.py:88-140`).

**Concerns.**
- **MEDIUM — formset pages are absent from the matrix.** `tests/test1/test_formsets.py:19-33` is the suite's only raw nested-form guard and documents why nesting matters (formset.js binds `form.cv-form`). Because `PublisherFormSetForm.helper` sets only `form_tag=False` (`views_formset.py:44-50`), that page emits two tokens today. Add it as a sixth actionable type, page and modal where supported.
- **LOW — workflow preservation suite is thin.** `tests/test1/test_workflow.py` is unit-level (state names, transitions, badges); the GET/POST page coverage the plan needs must come from the new matrix, so the named preservation command adds less than it appears to.
- **LOW — `_norm` is adequate.** It only rewrites token values and collapses whitespace (`test_form_frame.py:44-47`); it cannot hide nesting, so the plan's "never normalize away nesting" is already satisfied.

**Suggestions.**
- Add the formset create/update routes to 05-01 and extend `test_formset_create_page_has_no_nested_form` with a token count rather than inventing a parallel assertion.
- In 05-02, record the before/after diff of each golden in the summary verbatim; the change is small enough to quote.

**Risk: LOW–MEDIUM.**

---

## 06.6-06

**Summary.** The fail-closed design is right, but the plan's process shape does not match the blocker it anticipates. Nothing in the repository identifies a companion source: `git remote -v` shows only `origin`, and the only references are historical paths and revisions in the source note (`superpowers/notes/2026-10-28-pre-1.0-before-theme-freeze-analysis.md:95-97`). I could not list sibling directories from this sandbox, so I rely on research's finding that `../tabler-test` and `../crispy-tabler` are absent; treat that as an open question only in the sense that a human may know where they are.

**Strengths.**
- Pins the pre-change core revision and requires provenance hashes, raw failing node IDs and original-checkout digests.
- Explicitly forbids substituting a synthetic theme for acceptance.

**Concerns.**
- **HIGH — the blocking checkpoint is implicit.** Task 06-02 is `type="auto"` with a `<precondition>`. The executor stops only on `type="checkpoint:*"` tasks (execute-plan.md:233-234); a missing `CV_THEME_SOURCE` would leave the agent improvising a "blocking acquisition checkpoint" and could end the plan with production commits but no SUMMARY, the illegal partial state the workflow warns about (execute-plan.md:12-20). Make acquisition an explicit `checkpoint:human-action` (or put it first in the plan) and set `autonomous: false`.
- **MEDIUM — package layout for the new Python test.** `tests/` and `tests/test1/` are packages, `tests/browser/` is not (`tests/__init__.py`, `tests/test1/__init__.py` exist; `tests/browser/__init__.py` does not). Adding `tests/browser/test_theme_adoption_sources.py` that imports `theme_adoption_sources` and running `pytest tests -n 4` (plan 09) risks module-name and import-mode errors. Add `tests/browser/__init__.py` or place the test under `tests/test1/`.
- **MEDIUM — companion dependencies.** Running "the unmodified theme/pack suite" needs the companion's own dependencies (at minimum crispy-tabler and the theme's extras). The cached nox envs contain only this repo's dependencies, and any install trips the SUS legitimacy gate the plans themselves impose. This will block 06-02 in practice; surface it as a named prerequisite rather than discovering it mid-task.
- **LOW — "discover from workspace metadata"** will find nothing; the task is effectively env-var driven.

**Suggestions.**
- Restructure: 06-00 `checkpoint:human-action` (sources + revisions + dependency availability) → 06-01 utility → 06-02 capture.
- Define the required-override inventory schema (path, purpose, reason) in 06 so plan 07's before/after comparison is mechanical.

**Risk: HIGH** for schedule; LOW for correctness of what it builds.

---

## 06.6-07

**Summary.** The browser plan reuses a mature harness pattern (`tests/browser/presentation.cjs:387-416`: revision and source hashes, checkout-import assertion, supported-series regex, port probe, fixture readiness, Chromium launch) and chooses the right case families. It inherits plan 06's acquisition block in full.

**Strengths.**
- Raw response counts before browser parsing, `element.form`/FormData/submitter ownership and negative CSRF are the right evidence for D-12/D-16.
- Patch replay against fresh exact-base copies, with original digests checked, satisfies D-14 without touching companion worktrees.

**Concerns.**
- **HIGH (inherited) — blocked until 06-02 succeeds;** THEME-05 cannot close otherwise, and the plan correctly refuses substitutes.
- **MEDIUM — estimate vs scope.** Eight case families × five form types × page/modal, plus a new server that must flip `CRISPY_TEMPLATE_PACK`/`CRISPY_ALLOWED_TEMPLATE_PACKS` (hardcoded to `bootstrap5` in `tests/test1/conftest.py:117-118`) and put the theme ahead of `crud_views` in `INSTALLED_APPS`, in 40k tokens and two tasks is optimistic. Split "server + config validation" from "cases" so a config failure does not consume the case budget.
- **MEDIUM — override-count comparison depends on an undefined schema** (see plan 06).
- **LOW — authentication.** Reuse the `/signin/` fixture pattern from `tests/browser/presentation_server.py` so Tabler pages render under real permissions, not `AnonymousUser`.

**Suggestions.**
- Three tasks: server/config (with the config test), cases, patch/replay.
- Record the theme's `INSTALLED_APPS` order and pack name in the results JSON as provenance, since both change what template is actually resolved.

**Risk: HIGH** (availability), MEDIUM (scope).

---

## 06.6-08

**Summary.** Documentation obligations map onto existing executable-docs infrastructure: `tests/test1/test_presentation_migration_docs.py` for extracted recipes, and `tests/test1/test_label_mode_docs.py:120,180,254` which already pin the settings table and resolution sections, so stale precedence prose fails loudly. `CHANGELOG.md` has Unreleased `Breaking`/`Fixed`/`Added` sections (lines 7, 311, 421) and `docs/migrating-1.0.md` has a clear sectioned structure to pair against.

**Strengths.**
- Separates the "Fixed" nested-form DOM note from the "Breaking" helper policy, which is exactly D-19's distinction.
- The current `theme.md` "Framing the form pages" section (`docs/reference/theme.md:272-290`) is the natural home for the ownership contract and is in the files list.

**Concerns.**
- **MEDIUM — example project is unmentioned anywhere in the phase.** D-01 does not break it (verified: the login helper at `examples/bootstrap5/project/urls.py:13-18` renders via standalone crispy), but the `examples` nox session is a project gate; plan 08 or 09 should state that check explicitly rather than leave it implied.
- **LOW — tutorial drift.** `tests/test1/test_form_button_docs.py:159-161` asserts tutorial markers about `get_form_actions()`. If plan 03's opt-in recipe changes the recommended wording, the tutorial (not in any files list) may need the same edit.
- **LOW — the `.venv` used for `mkdocs build --strict` has Django 6.1.** Harmless for a docs build; just do not let it leak into any Python evidence.

**Suggestions.**
- Add an explicit "example project unchanged and green" line item with the `examples` command to 08-02 or 09-01.
- Grep docs for "helper" and "form_tag" before writing, so every page that shows a crispy helper carries the `form_tag=False` requirement.

**Risk: LOW.**

---

## 06.6-09

**Summary.** The integration commands are runnable as written: the three interpreters exist, the single floor deselect matches `noxfile.py:57`, `conditional-formsets.cjs --case lifecycle` names a real required family (`tests/browser/conditional-formsets.cjs:57`), `modal-focus.cjs` defaults to the floor interpreter and honors `CV_FOCUS_PYTHON` (`modal-focus.cjs:81`), and `vitest.config.js`/`vitest.integration.config.js` exist. Running the whole `tests` tree on the floor env with one deselect was already done in 06.5 (STATE records 8328 passed), so it is feasible.

**Strengths.**
- Refuses to let historical exclusions waive new scenarios, and names the Django-6-only CSP skip as pre-existing.
- Separates automated pass from pending human/AT observations.

**Concerns.**
- **MEDIUM — blocked-state output is undefined.** If 06-02/07 never obtain companions, 09 correctly cannot pass `--check-final`; the plan should say it then writes a `status: halted` SUMMARY and what partial artifacts it still publishes (public-surface inventory can be complete even when acceptance is not).
- **LOW — new browser Python test under `tests/browser/`** will be collected by every full run on all three series; keep it Django-free (see plan 06 layout concern).
- **LOW — effort.** Three full runs plus two browser lanes plus report authoring in 35k tokens is tight; 06.4-10 took 60 minutes for comparable scope.

**Suggestions.**
- Add the blocked-path contract to 09-02.
- Have `--check-final` verify the example-project gate too, since it is the one project gate no plan currently names.

**Risk: LOW** for content; schedule inherits plans 06/07.

---

## Cross-plan assessment

**Dependency ordering.** Wave 1 (01, 02, 04, 06) has no file overlap, so parallel worktrees are safe. The two shared files are correctly serialized: `form.py` (01 → 03) and `button_classes.py`/`buttons.md` (04 → 03). Shared requirement IDs (THEME-01 across 01/05/07/09; THEME-05 across 06/07/09) are handled by the shared-ID gate. One ordering gap: both 03 and 04 will break `tests/test1/test_button_classes.py:104-106` and neither lists or runs it.

**Does the phase achieve its goal?** For #277, #278, #279 and #280 (THEME-01 to THEME-04, THEME-06), yes: every mechanism is grounded in current source and the tests are discriminating. For THEME-05, the plans are honest that acceptance is impossible without the real companions, but they encode that dependency as a soft precondition instead of a hard checkpoint, and they do not name the companion-dependency installation problem.

**Scope.** No creep. The one place the plans under-specify a product mechanism is the pack-selection rule in plan 03, and the one place they over-couple is tying the stock CSRF fix to the helper-copy experiment in plan 01.

**Security.** CSRF positive/negative tests, autoescaped class values and no new auth surface are all consistent with ASVS 5.0 V3 as the plans claim. One note for plan 01: the helper diagnostic should name the helper type and option only, never the resolved action URL, because `form_action` reversal could embed object identifiers.

## Overall risk: MEDIUM

Product changes are low-risk and well evidenced. The phase's schedule risk is concentrated in companion acquisition (plans 06/07) and the two concrete fixes needed before execution are: (1) make acquisition an explicit human checkpoint with `autonomous: false` on plan 06; (2) specify the per-pack feature-probe selection rule in plan 03 and add `tests/test1/test_button_classes.py` to plans 03 and 04.
