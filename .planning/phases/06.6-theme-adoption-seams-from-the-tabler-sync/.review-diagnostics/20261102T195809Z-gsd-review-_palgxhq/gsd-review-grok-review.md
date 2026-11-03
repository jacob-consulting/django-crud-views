I'll verify each plan against the source, starting with the ownership, label-mode, class-table, and workflow seams the plans claim.
Cycle-6 contracts hold against source. No new unresolved executable gap. Pending baseline, browser, and human runs stay execution gates, not spec holes.

## 06.6-01

**Summary.** The ownership plan matches the current double-form boundary and the helper-selection bug. `cv_render_form` still flattens context, and both library helpers still emit a nested form.

**Strengths.**
- `CrispyFormMixin.helper` and `CrispyDeleteForm.helper` allocate a new `FormHelper` and never set `form_tag` (`src/crud_views/lib/crispy/form.py:43-50`, `136-146`). Page templates already own the outer form and token (`src/crud_views/templates/crud_views/view_create.content.html:5-10`).
- `tags/form.html:3-6` reads `form.helper` twice by truthiness. Selecting once and passing `cv_form_helper` is the right fix.
- `cv_render_form` uses `context.flatten()` (`src/crud_views/templatetags/crud_views.py:465-466`), which drops the tiers `Button.render` scans (`src/crud_views/lib/crispy/buttons.py:49-76`). The `cv_alert` push/render pattern at `crud_views.py:453-455` is the correct model.
- The 01-01/01-02 single green commit is a justified fixture boundary, same shape as plan 10. Workflow stays on `{% crispy form form.helper %}` until plan 05 (`view_workflow.action.html:15`).

**Concerns.** None unresolved.

**Suggestions.** None.

**Risk Assessment.** LOW. Mechanism and atomic fixture boundary are source-backed. CSRF and helper-copy evidence is still future execution.

## 06.6-02

**Summary.** Theme label floors belong in the existing resolver. W292 already calls that resolver, so the plan correctly refuses a second check implementation.

**Strengths.**
- Package floor is exactly `context=icon`, `list=icon`, `card=both`, `form=label` (`src/crud_views/lib/view/label_mode.py:23-25`). Invalid settings fall back to that table today (`label_mode.py:107`, `118`), which is what D-07 must retarget.
- Form and context W292 both go through `cv_get_action_label_mode` (`src/crud_views/lib/view/buttons.py:435`, `570`; `base.py:341`, `348-349`). A theme layer inside `default_label_mode` reaches both checks without new startup form construction.
- `form_label_mode` calls `default_label_mode("form")` only for unnamed or invalid maps (`label_mode.py:129-145`). The private theme/package helper that must not read settings is the right recursion break.

**Concerns.** None unresolved. C3-A03's composed owner/setting case is specified against this call chain.

**Suggestions.** None.

**Risk Assessment.** LOW. Public API and precedence match D-15. Isolation is a test obligation, not a missing design.

## 06.6-03

**Summary.** The floor incompatibility is real, and the bridge predicates match the installed floor template. Filter class caching is the right place to resolve keys at render time.

**Strengths.**
- Installed floor `bootstrap5/layout/formactions.html` is nine lines, has `flat_attrs`, `label_class`, `field_class`, and `fields_output`, and never reads `css_class` (`.nox/crispy_floor-3-12-django-6-0/.../formactions.html:1-9` and the 4.2 floor copy). Current pack does read `formactions.css_class` (`.venv/.../formactions.html:3`).
- Both floor copies include `class="aab {{ label_class }}"`. Exact whole-source equality will keep that token. That is upstream-in-cache, not a local probe.
- Filter actions are built once and cached on `_cv_actions` (`src/crud_views/lib/views/list.py:172-179`). Storing a key and resolving classes in `render` is required. Hidden inputs stay on `add_input` (`list.py:114-123`), outside this template, so C4-A04's split is correct.
- `form:actions:icon` is not an action-mode key unless `actions` is added to `FORM_KINDS` (`button_classes.py:251-263`). Keeping the new keys out of `FORM_KINDS` is required for W362.

**Concerns.** None unresolved.

**Suggestions.**
- When retaining the floor fixture, copy the installed file bytes, including `aab`. Do not reconstruct the template from the research summary.

**Risk Assessment.** LOW for the contract. Floor proof is still an execution task, and the plan already halts if the predicates fail.

## 06.6-04

**Summary.** Alert utility keys can replace the two literals without changing default bytes, and the 84-key inventory is the right base.

**Strengths.**
- The leaf hardcodes `alert-dismissible fade show` and `btn-close` while the hook is already `data-cv-alert-dismiss` (`src/crud_views/templates/crud_views/tags/alert.html:2-5`).
- `test_default_table_is_complete` asserts 84 keys (`tests/test1/test_button_classes.py:104-106`). `buttons.md:151` quotes 84. Adding two keys in this plan, then two in plan 03, matches the wave order.
- `{% cv_button_class %}` autoescapes (`crud_views.py:570-573`). Empty/None becomes `""` in `get_button_class` (`button_classes.py:160-165`), so the no-separator rule is implementable.
- `alert:close:icon` is not an action-mode key (`button_classes.py:263`). W362 already rejects it once the base key is the only default.

**Concerns.** None unresolved.

**Suggestions.** None.

**Risk Assessment.** LOW. Default-byte risk is pinned by the existing golden and the separator rule.

## 06.6-05

**Summary.** Full-page workflow and modal workflow are different templates today. The plan's split matches that inheritance instead of forcing one body.

**Strengths.**
- `WorkflowView` sets `template_name` to `view_workflow.html` and does not override `cv_content_template` (`src/crud_views_workflow/lib/views.py:18-27`). It inherits `crud_views/view_custom_form.content.html` and `cv_modal_supported = True` (`src/crud_views/lib/views/form.py:18-20`).
- Modal content includes `view.cv_content_template` (`src/crud_views/templates/crud_views/modal/content.html:8`). Full page includes `view_workflow.content.html`, which includes the action template (`view_workflow.html:4`, `view_workflow.content.html:3-5`).
- The action template is the only direct `{% crispy form form.helper %}` (`view_workflow.action.html:8-15`) and still loads `crispy_forms_tags`. `WorkflowForm` is a `CrispyForm` (`src/crud_views_workflow/lib/forms.py:11`), so plan 01's helper reaches it once this call becomes `cv_render_form`.
- Create/update stay `cv_modal_supported = False` (`src/crud_views/lib/view/base.py:111`; create/update do not override it). Protected delete already omits the form (`view_delete.content.html:15-23`).
- `PublisherFormSetForm.helper` and `QuestionnaireForm.helper` exist only to set `form_tag=False` (`tests/test1/app/views_formset.py:44-50`, `examples/bootstrap5/formsets/views.py:36-41`). Removing them restores `_inherits(..., "helper", CrispyFormMixin)` so W292 can see them (`buttons.py:511-515`).

**Concerns.** None unresolved. The no-choice modal still rendering a form is inherited custom-form behavior. The plan records it instead of pretending the workflow branch ran.

**Suggestions.** None.

**Risk Assessment.** LOW. Template provenance is verifiable before the new request matrix exists.

## 06.6-06

**Summary.** Baseline identity, purpose counts, and the recorded companion root are specified against the supplied tree. Fresh suite results are still an execution precondition, which the plan already treats as blocking.

**Strengths.**
- `tests/browser/theme_adoption_sources.py` resolves the core root at `Path(__file__).parents[2]`. That is the checkout root, not a cwd sibling. C6-A03 matches that layout.
- Companion `pyproject.toml:17-18` points editable installs at `../django-crud-views`. Isolated sibling copies are required. The plan says so.
- Embedded `crud_views_tabler/templates/crud_views/` includes `modal/shell.html` plus the four render probes. An allowlist of four shadows would miss `modal/shell.html`. The omission fixture is aimed at a real file.
- `checks.py:8-26` and `icons.py:50-52` are behavior, not data-only registration. Counting them separately from `TABLER_ICONS` matches the source.

**Concerns.** None unresolved. H06 acquisition is closed by the supplied revision. Unrun baseline remains a halt, not a waiver.

**Suggestions.** None.

**Risk Assessment.** MEDIUM only because 06-02 has not run. The halt/resume contract is already in the plan.

## 06.6-07

**Summary.** C5-H01 and C6-A01 are implementable on the current core leaf and the companion icon registry. The plan does not invent missing Tabler glyphs or a cancel tag the core does not already fall back.

**Strengths.**
- Core cancel is `layout.Button` (`input_type` `button`, confirmed on the installed crispy `Button`). URL-less output is a `<button>` with no `href` (`button_data.py:354-357`; `tags/button/form.html:1-2`). Empty `cancel_url` is falsy, so a requested `form:cancel-tag` of `a` still stays a button.
- Companion tests already render `svg("check")` and `svg("arrow-left")`, and `filter-close` is `tabler:filter-x` with an `ICONS` membership assertion (`icons.py:25`, `tests.py:62-67`, `307`). The three new names are the only keys in `DEFAULT_ICONS` (`icons.py:51-53`) missing from `TABLER_ICONS`.
- `test_table_values` compares the entire dict (`tests.py:98-139`). Adding four pairs there, not a subset, is the real C5-A08 lock.
- Companion `tags/alert.html:17` still uses `data-bs-dismiss="alert"`. `MessagesParityTests` (`tests.py:556-572`) currently requires byte parity with the native include. The named one-attribute delta is necessary.
- No companion `tags/form.html` or `view_workflow.action.html` is in the embedded tree. The plan's "migrate only an existing copy" rule avoids a new override.

**Concerns.** None unresolved. Browser and replay results are still required and already gated.

**Suggestions.** None.

**Risk Assessment.** MEDIUM for unrun Chromium/replay, not for a missing mapping or mode matrix.

## 06.6-08

**Summary.** The doc split around the E108 sentence matches the test that still requires the old package-floor wording. Alert-frame guidance can move outside the single extracted fence.

**Strengths.**
- `test_migration_e108_location_inventory` still requires "falls back to its package floor" (`tests/test1/test_label_mode_docs.py:797`; `docs/migrating-1.0.md:64`). Leaving that pair to 08-02 is required. 08-01 does not list `migrating-1.0.md`.
- `test_alerts.py` extracts exactly one fence under `### Custom alert frame` (`theme.md:308-321`). Utility-key text must stay outside that fence.
- Standalone library helpers will lose their wrapper once `form_tag=False` is set on the property, while `disable_csrf` stays local to `cv_render_form`. The caller-owned wrapper recipe is the matching migration.

**Concerns.** None unresolved.

**Suggestions.** None.

**Risk Assessment.** LOW. Docs tests already encode the fences this plan must not break.

## 06.6-09

**Summary.** Final checks bind the earlier evidence instead of substituting a shorter suite. The floor selection and the two floor runtimes are real nox inputs.

**Strengths.**
- `CRISPY_FLOOR` is crispy 2.0 / bootstrap5 2023.10 (`noxfile.py:22-24`). `CRISPY_FLOOR_TESTS` does not yet include the new theme modules or `test_button_classes.py` / `test_alerts.py` (`noxfile.py:28-52`). Appending them is a real selection change. The only deselect is `test_filter_form_baseline` (`noxfile.py:57`).
- Both cached floor interpreters exist. Current-pack Django 6.0 is a separate limit. The plan does not let the 6.0 floor stand in for it.
- C6-A01/A02/A03 are rechecked here against candidate, replay, and the committed delivery bundle, including the recorded-root resolver. That is the right final bind.
- The human check is outside automated acceptance. The plan refuses to fabricate it.

**Concerns.** None unresolved.

**Suggestions.** None.

**Risk Assessment.** MEDIUM until the listed gates exist. Missing evidence stays a failed `--check-final`, which is the intended outcome.

## 06.6-10

**Summary.** The shared companion commit is a real multi-repo boundary, not a missing core task commit. Core ledger accounting stays valid if 10-03 is the only core task commit.

**Strengths.**
- The installed executor commits in the current repo unless `sub_repos` is set. This plan is not `sub_repos`. It keeps the core ledger on core and commits companion files with `git -C` and a temporary index. That matches "do not pass `../` paths to core `git add`."
- 10-01 must not commit. The class-table test and alert hook have to land with the registrations or `test_table_values` and `MessagesParityTests` fail on a partial tree (`tests.py:98-139`, `556-572`). One companion commit after 10-02 is the correct green boundary.
- 10-03's core allowlist is the delivery JSON plus the handoff. `actuals.commits` measured before the SUMMARY metadata commit then sees only that evidence commit. Companion SHAs stay in a separate section. That satisfies the executor's core `rev-list` rule without pretending the companion commit is core.
- C6-A01 is required in the partial, provisional, and `--require-committed` probes. Core cancel fallback (`button_data.py:357`) is what those probes must observe. C6-A03's `recorded` operand does not depend on the core worktree sitting beside `tabler-test`.

**Concerns.** None unresolved. Unrelated index preservation is specified, including same-file staged hunks, and stops on overlap instead of stashing.

**Suggestions.** None.

**Risk Assessment.** MEDIUM for the live companion index and hooks. The accounting contract itself is executable and should not be rewritten into three core commits.

## Cross-plan

Cycle-6 items are closed in the plans and match source. `form=both`, `tabler:check` / `arrow-left` / `filter-x`, five kinds, three modes, reset, and URL-less cancel are required from candidate through committed delivery. The exact `ButtonClassTests` dict is the companion lock. Plan 10's first two tasks share one companion commit. Only 10-03 is a core evidence commit. No further spec change is needed before execution. Acceptance remains blocked until baseline, replay, browser, and the human check exist.
