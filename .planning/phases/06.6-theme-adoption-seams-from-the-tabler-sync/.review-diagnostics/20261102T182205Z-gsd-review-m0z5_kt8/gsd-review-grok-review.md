I'll verify each plan against current source and the supplied companion excerpts, then write the nine-section review with explicit closure status.
HEAD `9b10cf0` matches the review target. Product trees at `cb26af4` and HEAD are identical. Companion identity is taken from the supplied excerpts, not a live sibling listing.

## 06.6-01

**Summary.** The ownership defect is real and the boundary is right. Stock pages already own the outer form, while `cv_render_form` flattens context into a template that reads `form.helper` twice, and library helpers never disable the inner form tag. The atomic fixture/golden commit and render-local CSRF experiment match D-01–D-04 and the create slice of D-16.

**Strengths.**
- `view_create.content.html:5-10` owns `<form>` and `{% csrf_token %}`; `tags/form.html:3-6` then calls `{% crispy form form.helper %}` twice. `cv_render_form` flattens at `crud_views.py:465-466`, unlike `cv_alert` at `:454-455`.
- `CrispyFormMixin.helper` and `CrispyDeleteForm.helper` never set `form_tag` (`form.py:43-50`, `136-146`). Floor `whole_uni_form.html:4-7` emits the token independently of `form_tag`. `helper.py:232-236` resolves `form_action` through `reverse`; diagnosing raw `_form_action` (`helper.py:183`) is the correct side-effect-free check.
- H02/H03 target the real fixtures: `_CustomHelperForm` / `_DeleteCustomHelper` at `test_form_button_checks.py:560-585`, still reaching the runtime policy at `:1082-1094`. `golden/form_frame/create.html:1` is still a nested form plus two tokens.
- C2-A02 is closed in 01-01/01-03: standalone library rendering loses the wrapper and keeps the token; page rendering suppresses the inner token only.

**Concerns.**
- MEDIUM: between this commit and plan 05, `view_workflow.action.html:15` stays outside `cv_render_form`. `form_tag=False` removes the nested form but not the inner token. The plan records that partial sequence; do not treat plan 01 as phase-wide ownership.

**Suggestions.**
- Keep the design checkpoint if no copy strategy suppresses CSRF without mutating the caller. That stop is already in 01-01.

**Risk Assessment.** LOW. The create tracer, helper immutability rule, and golden commit are executable against current source.

## 06.6-02

**Summary.** The theme floor belongs in `default_label_mode`, and the plan correctly refuses to merge owner maps or cache settings. W292 already reaches that resolver, so check changes should stay descriptive.

**Strengths.**
- Package floor is exactly `{"context": "icon", "list": "icon", "card": "both", "form": "label"}` (`label_mode.py:23-25`). Invalid settings fall back to that table at `:107` and `:118`.
- `cv_get_action_label_mode` calls `default_label_mode` / `form_label_mode` (`base.py:341-349`). W292 calls `cv_get_action_label_mode` (`buttons.py:569-570`) and skips instantiation (`:546-555`). E108 validates setting shape only (`settings.py:159-189`). Routing the fallback through a setting-free theme/package helper avoids the recursion A17 named.
- `register_button_classes` mutates in place (`button_classes.py:135-138`). A validate-then-rebind lock is the right divergence for D-06.
- C2 has no open item here. A16/A17/A18 are in 02-01/02-02.

**Concerns.**
- None that are not already tasked.

**Suggestions.**
- None beyond the existing autouse rebind and card `override_settings` cases.

**Risk Assessment.** LOW. Precedence and check wiring match the current call chain.

## 06.6-03

**Summary.** Independent group keys are justified, and the floor pack cannot consume `css_class`. The exact-source bridge is a fail-closed experiment, not a blanket pack replacement.

**Strengths.**
- Three constructors are separate: `form.py:55-56`, delete `form.py:141-144` (does not call `get_form_actions`), filter `list.py:125-133`.
- Floor `formactions.html:1` is `class="mb-3"` and never reads `css_class`. Current pack `formactions.html:3` does. The bridge predicate matches that split.
- Filter actions are cached on the helper (`list.py:174-177`). Storing a key and resolving at render is the mechanism that makes H05 true.
- Live inventory is 84 (`test_button_classes.py:104-116`, `buttons.md:151`). 04 then 03 (86 then 88) matches `depends_on`.
- C2-A03 is closed: `.nox/crispy_floor-3-12-django-4-2` exists, and 03-03/09 require it beside the 6.0 floor. H01/H04/H05/H11 remain in the tasks.

**Concerns.**
- None new. A1 stays an execution experiment with an explicit stop, which is correct.

**Suggestions.**
- None. Do not widen the bridge to `crispy_tabler`; that pack already prints `formactions.css_class` (supplied `formactions.html:4`).

**Risk Assessment.** MEDIUM. The floor mechanism is still unproven code, but the plan refuses a weakened contract if the predicates fail.

## 06.6-04

**Summary.** Alert keys are a leaf change with a byte-identical default. The dismissal hook stays out of the class values.

**Strengths.**
- `tags/alert.html:2-5` hard-codes `alert-dismissible fade show` and `btn-close`, and already has `role="alert"`, `type="button"`, translated Close, and `data-cv-alert-dismiss`.
- W362 accepts keys in `DEFAULT_BUTTON_CLASSES` (`button_classes.py:328-329`) and rejects mode suffixes through `_action_key_parts` (`:262-265`). Empty/None spacing is pinned in 04-01, which matches A03.
- 04-01 updates `EXPECTED_KEYS` and the docs count in the same commit as the defaults. The count test is in `test_button_classes.py:112-116`, and that file is in the verify command.

**Concerns.**
- None unresolved. The companion `tags/alert.html` copy can shadow this leaf; that inspection belongs to plan 07, and the alert-dismiss case cannot pass if the copy ignores the keys.

**Suggestions.**
- None beyond the existing golden and adapter checks.

**Risk Assessment.** LOW. Defaults, escaping, and grammar are fully specified against current templates.

## 06.6-05

**Summary.** Full-page expansion matches the templates that actually own forms, and the create/update modal exclusion matches E251. Workflow modal coverage is not bound to the workflow action template.

**Strengths.**
- Create/update do not set `cv_modal_supported` (`create.py:12-14`; default `base.py:111`). E251 is `base.py:167-171`. Custom and delete set it (`form.py:20,52`; `delete.py:55`). `WorkflowView` subclasses `CustomFormView` (`workflow/lib/views.py:18`).
- Actionable pages own forms at `view_create.content.html:5-10`, `view_update.content.html:5-10`, `view_custom_form.content.html:5-10`, `view_delete.content.html:15-22`. Protected delete omits the form at `view_delete.content.html:15`. No-choice workflow omits it at `view_workflow.action.html:6-17`.
- `X-CV-Modal` is `base.py:57-59`. Modal templates switch at `:222-224`.
- Parent overrides only set `form_tag=False` (`views_formset.py:44-50`, `examples/bootstrap5/formsets/views.py:36-41`). Removing them restores `_inherits(..., "helper", ...)` at `buttons.py:511-514`. C2-A01's create/update split and C2-A05's named deferrals match those files.
- C2-A07's golden owner is plan 01, not this plan.

**Concerns.**
- MEDIUM: workflow modal HTTP does not include `view_workflow.action.html`. `WorkflowView` never sets `cv_content_template` (`workflow/lib/views.py:18-27`), so it inherits `crud_views/view_custom_form.content.html` (`form.py:18-20`). `modal/content.html:8` includes that attribute. A green modal case can pass on the custom-form partial and never render the choice branch or the template 05-01 changes. Full-page workflow is still the right fix.

**Suggestions.**
- In 05-01 and 07-02, assert the modal include is `crud_views_workflow/view_workflow.content.html`, or set `cv_content_template` before calling the case a workflow modal. This is not in the current tasks.
- Clarify 05-02's "without added helpers": plan 01 must still supply a render-local nonwrapping helper for `PolymorphicCreateSelectView` (`create_select.py:16-27`, plain `forms.Form`). Do not persist it on the form class. LOW wording clash, already constrained by 01's one-form contract.

**Risk Assessment.** MEDIUM. Page and CSRF coverage is sound; workflow modal evidence is mis-aimed until the content template is bound.

## 06.6-06

**Summary.** H06 source acquisition is closed. The plan now targets one supplied monorepo, two real suites, sibling editable copies, and a separate Python/Django runtime. Fresh baseline results remain future execution, and that is not a plan defect.

**Strengths.**
- Supplied `pyproject.toml:5-18` and `:30-37` match the plan: Python `>=3.14`, Django `>=6.1,<6.2`, editable `../django-crud-views`, pytest settings `tests.crispy_tabler.settings`.
- Supplied `settings.py:48-51` and `:159-161` place `crud_views_tabler` before core, set `CRISPY_TEMPLATE_PACK = 'crispy_tabler'`, and set `CRUD_VIEWS_EXTENDS`.
- README lines 63-65 are the two suite commands. The plan's sibling `baseline/` and `candidate/` layout preserves the relative editable path.
- `cb26af4` is an ancestor of HEAD and has no product diff in `src`, `tests`, `examples`, `docs`, or `noxfile.py`. Pinning it does not drop product changes.
- Missing runtime writes a halted summary instead of a passing baseline. C2-A01 through C2-A07 do not reopen acquisition.

**Concerns.**
- MEDIUM: 06-01 mandates `python -m pytest tests -n 4`, but the supplied test group is only `pytest`, `pytest-django`, and `crispy-bootstrap5==2026.9` (`pyproject.toml:32`). `pytest-xdist` is not declared. Halting on that missing plugin blocks a README-valid suite. Django `--parallel` on `manage.py test` does not have this problem.

**Suggestions.**
- If xdist is absent, run the README pytest command without `-n` and record serial execution. Do not treat that as a missing-source failure. This fallback is not in the task.

**Risk Assessment.** MEDIUM for execution preflight, LOW for source identity. Acquisition itself is signed off.

## 06.6-07

**Summary.** Real Tabler acceptance is correctly gated on plan 06, and the supplied pack does not need a manufactured `formactions` patch. Browser cases still have to bind workflow modal content and the override-count rule.

**Strengths.**
- `presentation.cjs:2-5` defaults to 8145 and reserves 8143/8144. C2-A04's shared-port collision test matches that file.
- Supplied theme inventory has neither `crud_views/tags/form.html` nor `view_workflow.action.html`. Supplied `formactions.html:4` already renders `formactions.css_class`. C2-A06's "do not create those copies" rule matches the excerpts.
- `apps.py:15-31` already registers icons, button classes, and assets. Settings order matches the plan's server setup.
- Required cases cannot be skipped, and original trees stay read-only. H06 execution evidence is still a precondition, not waived by the checkout existing.

**Concerns.**
- MEDIUM: D-18's nonincrease count is not defined against the known copy list. The supplied inventory includes `tags/alert.html`, `snippets/form_frame.html`, and `tags/list_filter*.html`, any of which can shadow core leaves. A temporary `register_label_mode_defaults` call is adoption, not a required template override. Counting it as growth can fail a correct patch; ignoring a shadowing `form_frame.html` can hide a nested form until the owned-form case, with no named inspection step.
- MEDIUM: the same workflow `cv_content_template` miss as plan 05 applies to the workflow modal browser case.

**Suggestions.**
- Inventory those three copies by resolved path before deciding absence is success. Exclude temporary registration calls from the D-18 count and keep them in the handoff patch. Neither rule is explicit in 07-02/07-03.

**Risk Assessment.** MEDIUM. The harness shape is executable; false override accounting and the workflow modal template are the remaining plan gaps.

## 06.6-08

**Summary.** Migration docs follow the actual contracts, including the standalone wrapper removal and the plan 01 golden owner. No new product API is introduced here.

**Strengths.**
- `migrating-1.0.md:61-64` still says invalid modes fall back to the package floor. H07 correctly leaves `test_migration_e108_location_inventory` (`test_label_mode_docs.py:786`) for 08-02.
- `test_alerts.py:250-253` requires one fence under `### Custom alert frame`. 08-01 keeps that fence.
- C2-A02 is closed: 08-01/08-02 publish a caller-owned wrapper for standalone library fields plus the existing token, and distinguish page-token suppression.
- C2-A07 is closed: 08-02 reads the four frame diffs from plan 01's evidence, which is the atomic owner. Current `golden/form_frame/create.html:1` is the before state.

**Concerns.**
- None unresolved. Companion names stay out of product docs until plan 07 evidence exists; that prohibition is already in 08-02.

**Suggestions.**
- None.

**Risk Assessment.** LOW. Recipes are tied to implemented seams and existing doc tests.

## 06.6-09

**Summary.** The final gate records real coverage limits and does not treat companion availability as a passing suite. Phase 7 handoff stays an inventory, not a stability freeze.

**Strengths.**
- `noxfile.py:3` is Django 4.2/5.2/6.0. `CRISPY_FLOOR_TESTS` (`:28-52`) omits `test_button_classes.py` and the new theme modules; 09-01 adds them. The only deselect is `test_filter_form_baseline` (`:57`).
- `.nox/tests-3-12-django-6-0` is absent. H12's "current-pack 6.0 untested" limit matches the tree. `.nox/crispy_floor-3-12-django-4-2` exists, so C2-A03's second floor command is real.
- `examples/bootstrap5/pytest.ini:2` is `DJANGO_SETTINGS_MODULE = project.settings`, matching the example command.
- Human visual/AT results stay pending. A missing baseline cannot mark THEME-05 complete. That is the correct H06 execution disposition.

**Concerns.**
- None new. It inherits plan 06's xdist halt and plan 05/07's workflow modal binding if those gates are written green against the wrong template or a blocked plugin.

**Suggestions.**
- `--check-final` should reject a workflow modal result that does not name `view_workflow.content.html` as the included body. Not currently specified.

**Risk Assessment.** MEDIUM. Automated matrix design is honest; acceptance is only as strong as the 06/07 evidence it binds.

## Closure

| Item | Verdict |
|---|---|
| C2-A01 | Signed off for create/update exclusion (`base.py:111`, `create.py:12-14`, E251 `:169-171`) and for custom/delete support. Workflow modal support flag is inherited, but the modal body is not the workflow action template. That remaining gap is MEDIUM below, not an open C2-A01 wording miss. |
| C2-A02 | Signed off. Plans 01 and 08 record wrapper removal versus page-token suppression. |
| C2-A03 | Signed off. Cached 4.2 floor exists; 03-03 and 09 require it separately from the 6.0 floor. H12 stays a distinct current-pack limit. |
| C2-A04 | Signed off. Default 8145 is shared with `presentation.cjs:2`; collision handling is tasked. |
| C2-A05 | Signed off as an explicit deferral. Named helpers still only set `form_tag=False` and stay out of scope. |
| C2-A06 | Signed off against the supplied inventory: no `tags/form.html` or workflow action copy; pack `formactions.html:4` already consumes `css_class`. Execution must recheck. |
| C2-A07 | Signed off. Golden migration owner is plan 01; 08-02 reads that evidence. |
| H06 acquisition | Signed off. One monorepo, both packages, revision and settings match the supplied excerpts. No remaining HIGH plan defect. |
| H06 execution | Not a plan defect. Baseline, browser runs, patch replay, and human checks are future gates. Plans 06-02, 07, and 09 already halt instead of certifying them. |

## Current unresolved findings

No current HIGH.

MEDIUM:
- Workflow modal evidence is unbound. `WorkflowView` inherits `cv_content_template` (`form.py:19`, `workflow/lib/views.py:18-27`); `modal/content.html:8` includes it, not `view_workflow.action.html`. Plans 05 and 07 do not assert or set that template. Not already tasked.
- Companion pytest `-n 4` requires undeclared `pytest-xdist` (`pyproject.toml:32`). Plan 06 halts instead of using the README command. Not already tasked.
- Plan 07 does not define the D-18 count against the known shadowing copies (`tags/alert.html`, `snippets/form_frame.html`, `tags/list_filter*.html`) or exclude temporary registration calls. Not already tasked.

LOW:
- Plan 05-02 "without added helpers" can be read against plan 01's render-local helper for plain/polymorphic forms (`create_select.py:16-27`). Outcome is still constrained by the one-form contract. Clarify only.
