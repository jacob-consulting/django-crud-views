I'll verify each plan against the current source, starting with the conditional, formset, and JavaScript paths the plans depend on.
The identity and clearing defects match the plans. Next I’ll trace formset validation, fragment indexing, and the JS lifecycle the later plans depend on.
Source checks confirm the plans target real defects. Two gaps would still let a green phase miss a required persistence path and a broken fragment.

## 06.4-01

**Summary:** The identity repair is aimed at the right code. `ToggleGroup.render` emits the raw field name, and `toggle.js` suffix-matches the first checkbox in the form.

**Strengths:**
- `layout.py:29` sets `cv_toggle_field` to `self.toggle_field` with no `form.add_prefix`. `toggle.js:15-20` then matches `name` or `name$=-name` via `querySelector`, so the first hit wins.
- `toggle.js:36-44` sets `__cvToggleWired` before the checkbox exists, so a late checkbox cannot retry. The plan forbids that.
- Task 01-02 matches the real wrapper: `render_tree.py:195-198` returns the unprefixed declaration name, and `formsets.html:4-6` prints it. Top-level `FormSet.init` already has the main form (`formsets.py:385-388`).

**Concerns:**
- MEDIUM: Task 01 does not say to delete the `DOMContentLoaded` / `cv:modal:loaded` / `cv:formset:row-added` calls to `wireGroups` (`toggle.js:53-65`). Plan 05 adds `cv.initConditional` on those same events. Leaving both binds two `change` handlers.
- LOW: `FSET-02` is listed here, but automatic page/modal/row startup is plan 05/06. This plan only proves an explicit `cv.initConditional` call.
- LOW: `XFormSet` is a pydantic model with no `extra` allowance (`render_tree.py:93-102`). `cv_bound_toggle_field` must be a declared field; a bare attribute assignment will raise.

**Suggestions:**
- In 01, replace `wireGroups` listeners with `cv.initConditional` instead of adding a second path.
- Declare `cv_bound_toggle_field: str = ""` on `XFormSet` and keep `cv_toggle_field` as the template-facing property.

**Risk:** LOW. The binding contract and the tracer (render, shipped JS, `FormData`, correct row) match the defect.

## 06.4-02

**Summary:** The clearing design matches Django 6.0.9 `construct_instance`, but the formset writer can skip the save the tests need to prove.

**Strengths:**
- `group.py:36-37` and `group.py:78-84` always store `None` and pop field errors. That is the file/Boolean/default bug.
- Installed `construct_instance` skips a field when it has a default, the widget omitted it, and `cleaned_data` is in the form field's `empty_values`. Applying `save_form_data` before `super()._post_clean()` is the right order so `full_clean` sees the cleared value.
- `FileField.save_form_data` treats `None` as no change and any other false value as clear (`data or ""`). Automatic `False` versus explicit `None` matches that.
- Main-form update saves unconditionally (`update.py:34`), so a direct `form.save()` test can pass for the main form.
- No test-app migrations exist, so a test-only model on `tests.test1.app` does not need a migration.

**Concerns:**
- HIGH: `XFormSet.save` writes a row only when `form.has_changed()` (`render_tree.py:256-260`). `FileField.has_changed` returns false when `data is None`. An off group omits the upload, so an inline file/image clear never reaches `save_form_data`. Plan 02 never edits `render_tree.py` and can go green with `ModelForm.save()` only. Plan 03 explicitly covers inline form classes, so this path is in scope.
- MEDIUM: Disabled fields also report `has_changed() == False`. Preservation is fine if the row is not saved; if another cleared field forces a save, disabled precedence must already have been applied in `clean` before `_post_clean`. The plan says that, but the file-only row never enters that code.
- LOW: `CrispyModelForm.__init__` requires `cv_view` (`form.py:39`). Persistence tests must follow `test_conditional_group.py`, not a bare `ModelForm()`.

**Suggestions:**
- Treat conditional clearing as a reason to save the inline row, or call the same resolver from `XFormSet.save` before the `has_changed` skip.
- Add a regression that goes through `XFormSet.save`, not only `form.save()`: existing file, group off, no upload, `storage.delete` not called, refreshed name empty.

**Risk:** HIGH until the `has_changed` gate is in this plan or plan 04.

## 06.4-03

**Summary:** Sharing one resolver between checks and runtime is the right contract, and `E312` is unused. W320 retirement is real work, not a comment.

**Strengths:**
- Checks only walk the view `form_class` today (`checks.py:164-179`). Inline forms with `cv_conditional_groups` are invisible. Extending the walk to `FormSet.klass.form` is necessary.
- `E310`/`E311`/`W321` stay. `E312` does not collide with `E300`, `E310`, `E311`, or `E330`.
- `_non_nullable_clears` (`checks.py:141-149`) warns on every non-null/non-blank field, including Boolean. Retiring that for the supported matrix matches D-08.
- Existing W320 assertions are at `tests/test1/test_conditional_checks.py:298` and `:373`. The task file list includes that module, so those assertions cannot be left as-is.

**Concerns:**
- MEDIUM: Startup checks must not instantiate request-bound forms. The plan says that, but `resolve_conditional_empty_value(form_field, model_field, ...)` still needs a form field object. Use `base_fields` only. A check that calls `form_class()` will break views whose form `__init__` requires `cv_view`.
- MEDIUM: Raising `ImproperlyConfigured` from `clean`/`_post_clean` 500s the request. That matches D-10, but a test that only expects a check message will miss a dynamic field that is absent from `base_fields`. Task 03-02 covers that; keep it on the dynamic form, not a second static check.
- LOW: `examples/bootstrap5/conditional/models.py` still says off-group clear is `None` because of W320. Plan 09 does not list that file.

**Suggestions:**
- Rewrite the W320 tests in this plan, not in 09. 09 only documents the replacement.
- Exempt `Field.disabled` in the check the same way runtime does, or a disabled non-null field becomes `E312` even though D-09 forbids clearing it.

**Risk:** MEDIUM. The check design is sound if it consumes plan 02's resolver and does not pretend W320 tests still pass unchanged.

## 06.4-04

**Summary:** The policy gate belongs on the runtime tree, not `InlineFormSet.clean`. The "native formset" test will not reach that gate unless the fixture accepts the package constructor.

**Strengths:**
- `render_tree.py:222-260` saves individual forms and never calls Django's formset `save()`, so `edit_only` on the class is not enforced.
- `FormSets.all_valid` is two-pass (`formsets.py:354-369`) and `cv_form_is_valid` runs before `cv_form_valid` (`mixins.py:80-128`). A non-form error added before the second pass blocks the atomic write.
- `formsets.py:88-89` accepts any Django `BaseInlineFormSet` subclass (`inline_formset.py` re-exports Django's class). A guard only on `InlineFormSet.clean` (`inline_formset.py:111-118`) does not cover that.
- Inactive formsets are skipped in `is_valid` (`formsets.py:348-351`) and purge stays in `save` (`formsets.py:371-382`). Keeping them out of the active gate matches D-18.

**Concerns:**
- HIGH: This plan also misses `render_tree.py:259`. Edit-only rejection is before save, but a valid off-group file clear is not a policy error and still dies on `has_changed`.
- MEDIUM: `FormSet.init` always passes `formset=` and `parent_form=` (`formsets.py:148-160`). Django's `BaseInlineFormSet.__init__` forwards unknown kwargs into `BaseFormSet`, which rejects them. A raw native class never reaches the policy. An executor who then subclasses `InlineFormSet` will not prove the bypass.
- MEDIUM: A foreign id can still produce Django's "Select a valid choice" on the PK field while the new error says "Invalid row." The plan requires one generic error and no existence leak, but it does not say to drop the choice error.
- LOW: `LIFE-02` is documentation. This plan does not publish it; plan 09 does.

**Suggestions:**
- Fixture class: subclass `django.forms.models.BaseInlineFormSet`, accept `formset` and `parent_form`, do not inherit `InlineFormSet.clean`.
- After the generic error is added, clear field errors that name the rejected id.
- Put the `has_changed` persistence fix here if plan 02 does not, and test it on both class families.

**Risk:** MEDIUM for the policy gate itself, HIGH if the file-clear hole stays in plan 02.

## 06.4-05

**Summary:** Disabled composition is necessary. `apply` writes `el.disabled = !on` for `input, select, textarea` only (`toggle.js:26-30`) and never records a baseline.

**Strengths:**
- Management exclusion already exists (`toggle.js:8-13`, names match `TOTAL_FORMS`/`INITIAL_FORMS`/`MIN_NUM_FORMS`/`MAX_NUM_FORMS`). The plan keeps it and refuses to disable an enclosing fieldset. That is required because management inputs sit inside the conditional wrapper (`formsets.html:4-7`, `formset.html:23-24`).
- Stock action controls are `<button>` (`control.html:8-28`), so today's `apply` leaves Add/Delete/Reorder enabled inside a hidden group. Including `button` fixes that.
- Reset is absent from `toggle.js`. A form-scoped `reset` listener that checks `defaultPrevented` after the default action matches the WHATWG order and D-03/D-15.
- Modal focus stays in `modal.js`. `cvModalInject` dispatches `cv:modal:loaded` before replacement focus (`modal.js:90-102`). Not moving focus on init avoids stealing that.

**Concerns:**
- MEDIUM: If plan 01 leaves `wireGroups`, this plan must remove it. The acceptance says no duplicate handlers, but the action does not name the old listener.
- MEDIUM: The observer proof is jsdom-only. Plan 08 does not require the "set `disabled=true` while already conditionally disabled, then clear it" case. jsdom `attributeOldValue` has been wrong before; Chromium would not catch a false green.
- LOW: Define "transition" so the first init of an already-off group does not move focus. D-05 forbids focus changes on initialization.

**Suggestions:**
- One listener path: `cv.initConditional` only.
- Add the same-value external-disabled case to plan 08, or accept that observer behavior is unit-tested only and say so in plan 10.

**Risk:** MEDIUM. The state model is right; the failure mode is stacked listeners or an observer that only works in jsdom.

## 06.4-06

**Summary:** Form-scoped controllers and submit ordering match the current global jQuery lookups and the modal listener bug.

**Strengths:**
- `XBase.sel` and management lookups are page-global (`formset.js:52-55`, `172-182`). Two forms with the same prefix cannot be independent.
- `start()` always constructs one `CrudViewsFormset` and never listens for `cv:modal:loaded` (`formset.js:621-644`).
- `reorder_formsets` returns `true` even when a child `return false` only breaks `jQuery.each` (`formset.js:597-610`). The plan names that bug.
- The document submit listener always calls `cvModalSubmit` and does not read `defaultPrevented` (`modal.js:227-232`). Reorder-on-form then fetch-on-document is the right order only if that flag is honored.
- `formset.edit_only` is already on the declarative object passed into `control.html` (`formsets.py:111-113`, `layout.py:29`). The template can branch without a new context variable.

**Concerns:**
- MEDIUM: Task 06-01 changes `control.html`, but the verify command is only `tests/js/formset.test.js`. Vitest does not render that template. Stock Add can remain in the Django template while JS fixtures omit it.
- MEDIUM: `find_page_form_controls` passes `edit_only: false` for the whole page (`formset.js:542-546`). Per-formset flags exist only on the row path (`formset.js:554-556`). A page-level delegated handler must read the clicked control's own JSON, not the page-wide flags. The plan says this; it is easy to "fix" by hiding the button and leaving the old page lookup.
- LOW: `formset.js:165` builds an unquoted attribute selector from the prefix. Scoping to the form does not by itself make that selector safe. Compare names in JS, as plan 01 does for toggles.

**Suggestions:**
- Add a pytest that renders `control.html` for `edit_only=True` and asserts no `cv-form-ctrl-add`.
- Keep server rejection in plan 04 as the authority; this plan is the UI and handler half only.

**Risk:** MEDIUM. Lifecycle scoping is well targeted. The template half is unverified by the stated command.

## 06.4-07

**Summary:** The index bug is exactly `get_template`'s `index=0`. The fragment template is already unbalanced, and the plan treats that as optional.

**Strengths:**
- `formsets.py:513` calls `formset.template(index=0, ...)`. `FormSet.init` assigns `child_index` (`formsets.py:181-188`). The characterization test asserts the mismatch (`test_fragment_authorization.py:1184-1185`) and is not a round trip.
- Parent-prefix validation already requires the declared child index (`formsets.py:446-448`). Fixing emission without relaxing that check is the right A19 shape.
- Request keys and `{html, rows}` stay (`formsets.py:518-520`, `formset.js:319-324`).
- `formset.parent` is set by `apply_hierarchy` (`formsets.py:302-314`), so the selected child's index is derivable without a second registry.

**Concerns:**
- HIGH: Closing wrappers test `end_at_rows` (`formset.html:56`). `XFormSet` has `render_rows_only` and no `end_at_rows` (`render_tree.py:102`). Django treats the missing attribute as empty, so `{% if not x_formset.end_at_rows %}` is true. `template()` sets `render_rows_only=True` for the selected fragment (`formsets.py:224`). Open tags are skipped and close tags are emitted. `test_crispy_buttons.py:903` still passes `end_at_rows=True` on a `SimpleNamespace`, which shows the template contract and the model diverged at the rename. The plan repairs this only if a parsed insertion fails. `insertAdjacentHTML` drops stray end tags, so the regression can pass while the raw fragment stays unbalanced.
- MEDIUM: Deeper non-first descendants need the selected node's own sibling index, not only the top-level child's. `get_template` always starts the selected node at `level=0`. Don't "fix" that by changing nested `template()` child indexes (`formsets.py:254-257`); those are already correct.
- LOW: Replacing the characterization assertion in the same test is right, but keep the denied-editor and forged-ancestry loops (`test_fragment_authorization.py:1187-1203`) in that test, as the plan says.

**Suggestions:**
- Make the close condition `render_rows_only` in this plan, unconditionally.
- Assert on the raw HTML string (start vs end tag counts) before browser insertion. Do not use only jsdom's HTML parser.

**Risk:** HIGH until the close-tag fix is mandatory.

## 06.4-08

**Summary:** A real browser/HTTP packet is the right acceptance for lifecycle, and the runner shape matches `modal-focus.cjs`. It will not catch the two server holes above unless the fixture uses the package save and raw fragment HTML.

**Strengths:**
- `modal-focus.cjs` already has cached Playwright, loopback refusal, own-process cleanup, and `--check-evidence` hashes. Copying that pattern is grounded.
- CSRF, session, 422 replacement, and no mocked `fetch` match D-15/D-19.
- Native templates are a separate task from the server, so 08-01 can land before the overrides exist.
- Transitive dependencies cover 01-07 via 07 and 03. Persistence matrix stays in pytest, which is appropriate.

**Concerns:**
- HIGH: If the fixture saves with `form.save()` instead of `FormSetMixin.cv_form_valid` → `XFormSet.save`, the file-clear hole stays green. The action says "real package CRUD views/formsets"; add an assertion that the inline save path ran.
- MEDIUM: `modal-focus.cjs:21` binds `127.0.0.1:8143`. This plan does not pick another port. Plan 10 runs both browsers. A leaked 06.3 server or an overlap fails the occupied-port check for the wrong reason.
- MEDIUM: No case requires the external disabled mutation from plan 05, or raw fragment tag balance from plan 07.
- LOW: `--check-evidence` must hash the new server and templates. `modal-focus.cjs` hashes a fixed input list; a new runner that hashes too little will accept stale JS.

**Suggestions:**
- Use a port other than 8143.
- One stock case: inline `FileField`, group off, no upload, storage object remains, DB name empty, and the save went through `XFormSet.save`.
- One case: fragment response raw HTML has balanced tags for a second sibling.

**Risk:** MEDIUM as a harness, HIGH as proof of COND-04/FSET-03 if those two assertions are absent.

## 06.4-09

**Summary:** Publishing after 08, with executable examples, matches D-19. The docs to change are the current ones, not a guessed API.

**Strengths:**
- `conditional.md:31` says off skips validation entirely and fields must be null/blank or `empty_values`. That is the wording to replace, even though the plan's "never validated" phrase is not verbatim.
- `formsets.md:205-210` and `migrating-1.0.md` still document the first-child fragment limit. Removing that only after 07/08 is the right gate.
- `.venv/bin/mkdocs` exists, so the strict build command is real.
- Not promoting `XForm`/`XFormSet` is consistent with `render_tree.py:1-17`, which already calls them an internal tree.

**Concerns:**
- MEDIUM: The matrix in 09 must not document file clear as supported on inline rows until plan 02/04 persists it through `has_changed`. Otherwise the published contract is wider than the code.
- MEDIUM: JSON `pk` is `FormSet.PK.value`, the grammar, not the row id (`render_tree.py:188`). Documenting it as the row primary key would be false. Row identity is in the prefix.
- LOW: `examples/bootstrap5/conditional/models.py` will still mention W320/`None` clearing after this plan.

**Suggestions:**
- Tie each matrix row to a test name from `test_conditional_persistence.py`.
- State that `pk` in `cv-data-formset` is the prefix grammar (`\d+` or the UUID pattern).

**Risk:** MEDIUM. The handoff is well scoped; it becomes wrong if it freezes behavior plan 02 did not actually persist.

## 06.4-10

**Summary:** The evidence runner matches the cached interpreters and refuses to treat a green baseline as acceptance. It cannot see a hole the earlier tests never named.

**Strengths:**
- `.nox/crispy_floor-3-12-django-4-2`, `.nox/tests-3-12-django-5-2`, and `.nox/crispy_floor-3-12-django-6-0` exist. The three-series command is runnable here.
- `.venv/bin/ruff` and `.venv/bin/mkdocs` exist.
- Leaving Python 3.13-3.15 unclaimed, and not marking the phase complete, matches the phase boundary.
- Amending only the A19 note in `06.2-ACCEPTANCE.md` is the right cross-phase write. The old characterization must stay historical.

**Concerns:**
- HIGH: `--check` validates commands, counts, and hashes. It does not know that file-clear through `XFormSet.save` or raw fragment balance were required. A complete green packet can still miss those.
- MEDIUM: Full suite times three, plus both browser runners, will collide if both bind port 8143.
- LOW: Planning-file edits in task 10-02 must stay out of the product hash set, as the plan says. Include the new browser server and templates or the checker will not notice a fixture-only pass.

**Suggestions:**
- Add the two missing cases to the required assertion IDs before `--check` can return success.
- Run the two browser fixtures sequentially on different ports.

**Risk:** MEDIUM as a provenance design, HIGH as a phase gate until those cases are required.

## Cross-plan

Dependency order is sound: 01 before 04 and 05, 02 before 03, 04 and 05 before 06, 06 before 07, 07 and 03 before 08, 08 before 09, 09 before 10. Wave 1 (01, 02) and wave 2 (03, 04, 05) do not share files.

The plans correctly name defects that are still in source: suffix match (`toggle.js:15-20`), null clearing (`group.py:36-37`), `index=0` (`formsets.py:513`), `reorder_formsets` always returning true (`formset.js:609-610`), and modal submit ignoring `defaultPrevented` (`modal.js:227-232`). They keep ancestry checks, purge, and jQuery.

They do not close two paths the phase still requires:

1. Inline off-group file clear versus `form.has_changed()` (`render_tree.py:259`, `FileField.has_changed`).
2. Fragment close tags keyed on a field the model no longer has (`formset.html:56`, `render_tree.py:102`).

Requirement IDs are all assigned. `FSET-02` on plan 01 and `LIFE-02` on plan 04 are early; the behavior lands in 05/06 and 09. That is bookkeeping, not a missing phase task.

**Overall risk: HIGH.** The lifecycle and policy split is implementable. Do not execute as written until plan 02 or 04 forces a save when conditional clearing changes an inline row, and plan 07 always aligns the fragment close condition with `render_rows_only`, proven on the raw string.
