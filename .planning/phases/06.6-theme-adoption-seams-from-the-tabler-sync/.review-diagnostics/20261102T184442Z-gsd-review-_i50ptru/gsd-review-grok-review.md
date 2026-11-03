I'll verify each plan against the current source, starting with the ownership, label-mode, class-key, and workflow seams the plans claim to close.
## 06.6-01

**Summary.** The ownership plan matches the current render split and is safe to execute. Stock pages already own the outer form and token (`view_create.content.html:5-10`, same pattern in update/custom/delete), while `cv_render_form` still flattens context and the inner template reads `form.helper` twice (`crud_views.py:465-466`, `tags/form.html:3-6`). Library helpers allocate a wrapping `FormHelper` and never set `form_tag=False` (`form.py:43-50`, `136-146`), so the nested form and second token in the four frame goldens are real.

**Strengths.**
- Selecting the helper once and rendering through `context.push`, as `cv_alert` already does (`crud_views.py:454-455`), is the right fix for the form-button owner scan, which walks `Context.dicts` (`crispy/buttons.py:49-76`).
- Diagnosing raw `_form_action` avoids `form_action`'s `reverse()` (`crispy_forms/helper.py:232-236`). Defaults that must stay quiet are the real crispy defaults (`helper.py:182-202`).
- `form_tag=True` is rejected in both strict modes; unused-wrapper warnings are a separate path. The two fixtures that would start raising are the ones that build a default `FormHelper` (`test_form_button_checks.py:560-567`, `578-585`).
- Workflow is explicitly left outside this boundary until plan 05. `test_workflow.py` does not assert form or token counts, so that sequencing does not turn the existing suite red.

**Concerns.**
- None at HIGH or MEDIUM. The helper-copy experiment is a required stop, not an assumed mechanism.

**Suggestions.**
- Keep CSRF suppression on the render-local helper only. `disable_csrf` is an instance attribute (`helper.py:202`); mutating the object returned by a custom `helper` property would change standalone crispy output.

**Risk Assessment.** LOW. The create tracer, golden migration, and diagnostic matrix are tied to the code that actually emits the second form and token.

## 06.6-02

**Summary.** The theme floor belongs in `default_label_mode`, which today merges only the live setting over the package table and falls back to that table (`label_mode.py:23-25`, `86-119`). `form_label_mode` already sends a bad owner map or entry through that function (`label_mode.py:129-145`), and W292 already calls `cv_get_action_label_mode` (`buttons.py:570`, `base.py:348-349`). No check rewrite is required for the theme layer to be visible.

**Strengths.**
- Atomic validate-then-rebind matches D-06. The package table is a `MappingProxyType` (`label_mode.py:23-25`), so the plan correctly leaves it immutable.
- C3-A03 is closed in the plan, not just named. The composed case follows the real call chain: a bad owner map calls `default_label_mode("form")`, which is where a bad setting is handled, and strict mode raises inside `_invalid_label_mode` before the fallback lambda runs (`label_mode.py:73-74`).
- Distinct malformed values are required because the warning key is `(location, repr(value))` (`label_mode.py:76-80`). Same repr would hide the second warning.
- The autouse fixture is necessary. `conftest.py:23-32` resets only `_warned`.

**Concerns.**
- None. Execution evidence is still future work, not a missing test obligation.

**Suggestions.**
- Assert the log line's resolved mode, not only that a warning was emitted. The format already includes the fallback (`label_mode.py:82`).

**Risk Assessment.** LOW. Precedence and the composed fallback are specified against the functions that implement them.

## 06.6-03

**Summary.** Independent group keys are still absent, and a keyword-only fix would fail on the declared floor. Both cached floor templates render `class="mb-3"` and never read `css_class` (`.nox/crispy_floor-3-12-django-6-0/.../formactions.html:1-9` and the 4.2 floor copy). The current pack does read `formactions.css_class` (`.nox/tests-3-12-django-5-2/.../formactions.html:1-4`). Delete does not use `get_form_actions` (`form.py:141-144`). The filter group is cached on the helper (`list.py:172-179`).

**Strengths.**
- The bridge is eligible only for pack name `bootstrap5` plus the installed floor template's exact source. A missing `css_class` token is not treated as proof of Bootstrap structure.
- Class lookup is deferred to render, which is what makes `register_button_classes` and `override_settings` visible on the cached `_cv_actions` object.
- `form:actions` and `form:filter-actions` stay out of `FORM_KINDS` (`button_classes.py:240`). W362 then rejects `form:actions:icon` as an unknown key (`button_classes.py:251-265`, `328-345`) rather than as a legal mode key.
- Plan 04's 86-key table is the input to the 88-key update, and `test_button_classes.py` is in this plan's files and verify command (`test_button_classes.py:104-116`).

**Concerns.**
- None unresolved. If the exact-source predicate fails, the task stops. That is the correct outcome, not a waiver of the floor.

**Suggestions.**
- Pin the bridge fixture to the 9-line floor template above, including the `label_class` / `field_class` branches and the absence of a hidden-input branch.

**Risk Assessment.** MEDIUM. The mechanism is identified, but the scoped bridge is still an experiment. Acceptance depends on that experiment, not on passing `css_class` through.

## 06.6-04

**Summary.** The two alert literals are still in the leaf (`tags/alert.html:2` and `:5`), beside `data-cv-alert-dismiss`, `role="alert"`, and the translated Close label. `get_button_class` returns `""` for a missing or `None` value (`button_classes.py:164-165`), so a permanent space before the new dismissible tag would change the golden. The plan's nonempty separator is the right guard.

**Strengths.**
- Defaults `alert-dismissible fade show` and `btn-close` match the current literals, so an unconfigured render can stay byte-identical.
- `EXPECTED_KEYS` and the single count sentence move in the same task as the defaults (`test_button_classes.py:105-116`, `buttons.md:151`). Mode-suffixed utility keys stay invalid because `alert` is not a variant location and `close` is not a form kind (`button_classes.py:239-265`).
- Core dropdown `data-bs-*` hooks are untouched (`language_selector.html:6`, `actions_menu_toggle.html:4-5`).

**Concerns.**
- None.

**Suggestions.**
- Assert the raw success wrapper is exactly `class="alert alert-success"` when the dismissible value is empty, including no trailing space.

**Risk Assessment.** LOW. This is a leaf and inventory change with an existing golden as the byte gate.

## 06.6-05

**Summary.** Full-page workflow and modal workflow are different templates, and the plan now tests them as different templates. `WorkflowView` sets `template_name` only (`views.py:18-27`). `cv_content_template` stays `crud_views/view_custom_form.content.html` (`form.py:18-20`). Modal rendering includes that attribute (`modal/content.html:8`, `base.py:222-224`). Full-page `view_workflow.html` includes `view_workflow.content.html`, which includes `view_workflow.action.html` (`view_workflow.content.html:3-5`). The action template is the direct `{% crispy %}` bypass (`view_workflow.action.html:6-18`).

**Strengths.**
- C3-A01 is closed against that split. Modal GET, invalid POST, and no-choice behavior stay on the inherited custom-form body. Full-page choice and no-choice branches are separate includes. The plan does not set `cv_content_template` to the workflow body.
- Create and update stay `cv_modal_supported` false via the base default (`base.py:111`) and E251 (`base.py:167-171`). Delete and custom form are the supported modal types (`delete.py:55`, `form.py:20`).
- Parent formset removal is safe only after plan 01, which this plan depends on. `PublisherFormSetForm.helper` exists solely to set `form_tag=False` (`views_formset.py:44-50`). That override is what hides the form from W292 (`buttons.py:511-515`).
- The existing nested-form guard starts after `class="cv-form"` (`test_formsets.py:29-34`), so it misses a token count. Plan 05 adds that count instead of replacing the guard with a whole-document count.

**Concerns.**
- None. C2-A05's retained `form_tag=False` overrides are an explicit deferral, and those helpers remain compatible with the new library default.

**Suggestions.**
- Assert the no-steps msgid from `view_workflow.action.html:18` on the full page only. The custom-form modal body does not contain that branch.

**Risk Assessment.** LOW. The modal/full-page invariant matches the view and template code. Request coverage is specified, not implied by a green modal POST.

## 06.6-06

**Summary.** Companion identity in the plan matches the supplied tree: one repo at `885dfc7`, theme and pack both present, Python `>=3.14` and Django `>=6.1,<6.2` (`../tabler-test/pyproject.toml:4-8`). Product source at `cb26af4` still matches HEAD for `src`, `tests`, `docs`, `examples`, and `noxfile.py`. Fresh suite results remain an execution gate, which the plan already treats as a halt rather than a pass.

**Strengths.**
- Pinned archives exclude the dirty `example/config/settings.py` and keep the `../django-crud-views` layout (`pyproject.toml:17-18`).
- The utility is import-pure, and `tests/browser/` has no package marker. The explicit `importlib` load is required.
- C3-A02's counting rule is in the plan: stable purpose IDs, data-only registration excluded, a retained shadow still counted. The four phase-relevant shadows exist: `tags/alert.html` (hardcoded `data-bs-dismiss` at the embedded alert template line 17), `snippets/form_frame.html`, `tags/list_filter.html`, and `tags/list_filter.inner.html`.
- `pytest -n 4` cannot run on the declared companion test extra (`pyproject.toml:32` has no xdist). The plan halts on that preflight instead of inventing a green baseline.

**Concerns.**
- LOW: the capture action names those four files, but the verified theme also shadows `modal/shell.html`, `table/bootstrap5.html`, `tags/card.html`, and `view_card.content.html`. A comparator implemented as that closed list would miss a new shadow outside the four.

**Suggestions.**
- Walk every `templates/crud_views/**` shadow, and treat the four named files as mandatory assertions on top of that walk.

**Risk Assessment.** MEDIUM for acceptance, LOW for the utility design. Missing baseline still blocks 07 and 09, by the plan's own precondition.

## 06.6-07

**Summary.** Browser acceptance is aimed at the real theme and pack, and it preserves the workflow split from plan 05. The supplied theme has no `tags/form.html` and no `view_workflow.action.html`, so those copies must not be created. `form_frame.html` only adds a card outside the modal (`form_frame.html:1-5`). The alert override is a real shadow of the core leaf and still uses `data-bs-dismiss` (embedded `tags/alert.html:7-17`), so it will not pick up `alert:dismissible` / `alert:close` or `data-cv-alert-dismiss` until the isolated copy is edited.

**Strengths.**
- C3-A01 and C3-A02 are carried into the browser record: modal origins stay on `view_custom_form.content.html`; full-page choice and no-choice runs must include the workflow content and action templates; the four shadows get before/after hashes even when unchanged.
- Port 8145 is the presentation default (`presentation.cjs:2`, `presentation_server.py:7`). The collision test leaves the other listener alive. That closes the shared-port claim.
- Pack adaptation is conditional. The plan does not invent a `formactions.html` patch when the native template already consumes `css_class`.
- Original checkouts stay untouched. The patch is replayed onto fresh sibling copies.

**Concerns.**
- None in the plan text. No baseline, browser run, or patch exists yet. That is the execution gate, not a revived HIGH.

**Suggestions.**
- On the adapted alert copy, assert `data-cv-alert-dismiss` and the absence of `data-bs-dismiss`. Tabler's current close control would otherwise keep working through Bootstrap and hide a missed hook.

**Risk Assessment.** MEDIUM. The scenarios match the theme's actual templates. THEME-05 is still unproven until 06's baseline and this replay exist.

## 06.6-08

**Summary.** Author docs still describe the pre-change contracts. `theme.md:310-311` says the dismissible and close classes are literal Bootstrap CSS and tells themes to copy `tags/alert.html`. That section has one `django` fence (`theme.md:314-321`), which `test_alerts.py`'s extractor depends on. Label resolution is still documented as package-then-setting. The plan's executable fences are the right place to lock the new behavior.

**Strengths.**
- Standalone library forms lose the helper-owned wrapper once `form_tag=False` is set on the mixin property, while `cv_render_form` is the only path that suppresses the inner token. The plan keeps those two migrations distinct.
- Copied `view_workflow.action.html` is a documented migration, with the detection limit stated: a copy that ignores `cv_form_helper` cannot be diagnosed by Python.
- The E108 migration sentence and `test_migration_e108_location_inventory` stay paired until 08-02. That avoids a red docs test in 08-01.
- Breaking notes are paired with `docs/migrating-1.0.md` before Phase 7.

**Concerns.**
- LOW: "explain alert replacement outside the fence" can be satisfied by a new paragraph while `theme.md:310` still says a copy is required. That sentence contradicts THEME-04.

**Suggestions.**
- Rewrite `theme.md:310-311` so the keys are the supported path and the fenced copy remains only for structural changes. Keep a single fence.

**Risk Assessment.** LOW. The recipes are grounded in plans 01-05. Companion success is correctly not claimed here.

## 06.6-09

**Summary.** The final gate is fail-closed and does not pretend the floor session already covers this phase. `CRISPY_FLOOR_TESTS` (`noxfile.py:28-52`) has neither `test_alerts.py`, `test_button_classes.py`, nor the five new `test_theme_*.py` modules. `DJANGO_VERSIONS` is still `4.2`, `5.2`, and `6.0` (`noxfile.py:3`). Both floor interpreters exist on disk. Current-pack Django 6.0 is recorded as untested rather than replaced by the 6.0 floor run.

**Strengths.**
- C3-A01 is checked again: `--check-final` rejects a modal pass substituted for full-page workflow branch records, and it checks included template names and origins against plans 05 and 07.
- The example-project command uses `examples/bootstrap5/pytest.ini`, which exists. The login helper in `project/urls.py:13-18` is not a `cv_render_form` form, so plan 01 must not reject it.
- Human visual and assistive-technology results stay pending until a person records them. A halted summary is required when upstream evidence is missing.
- Preservation commands rerun authorization, modal focus, and conditional formset lanes instead of citing older phase summaries.

**Concerns.**
- None as plan omissions. Missing companion replay and human observations remain blocking execution evidence, already specified.

**Suggestions.**
- Record the companion Python 3.14 / Django 6.1 run as extra integration evidence in a separate field from the 4.2/5.2/6.0 gates, so a green companion run cannot satisfy a missing core-series gate.

**Risk Assessment.** MEDIUM. The checker can certify the phase only after 07 and 08. The plan does not mark that certification done in advance.

## Cross-plan comparison

Workspace HEAD is `223a0af`, one docs commit after the requested `0d7c377`. The nine plan files are identical between those commits. Product trees at `cb26af4` and HEAD match, so the cited line numbers are the tree an executor will edit.

Cycle 3 closures hold against source, not only against the disposition tables:

- C3-A01 is signed off. Modal workflow renders `view.cv_content_template`, which `WorkflowView` does not override. Full-page workflow renders `view_workflow.action.html`, including the no-choice omission. Plans 05, 07, and 09 test those as separate records and do not change the modal body to manufacture coverage.
- C3-A02 is signed off as a counting rule. Purpose IDs, data-only registration, and the four real shadows are in plans 06 and 07. The LOW below is about inventory scope, not about the rule being missing.
- C3-A03 is signed off. The composed non-strict path is `form_label_mode` to `default_label_mode`, and strict mode raises before that fallback. Plan 02-02 tests both.

Previously closed HIGHs (frame goldens, `EXPECTED_KEYS`, workflow bypass, raw owner scan, floor discriminator, cached filter classes, companion identity, current-pack Django 6.0 limit) are implemented in the current task text. They are not reopened because the runs have not happened.

Wave order is consistent: 01 and 04 land the renderer and the 84-to-86 key change before 02, 03, and 05 edit the same suites. 03 depends on 04, so the 86-to-88 count is not racy. 07 and 09 cannot pass without 06's baseline.

## Unresolved list

**HIGH:** none.

**MEDIUM omissions:** none.

**LOW omissions:**
- Plan 06's capture text can be read as an inventory of only four shadows. The verified theme also has `modal/shell.html`, `table/bootstrap5.html`, `tags/card.html`, and `view_card.content.html`. The walk should include every `templates/crud_views/**` shadow.
- Plan 08 does not explicitly order a rewrite of `theme.md:310-311`, which still says dismissible and close classes are literals that require a copied frame.

**Already incorporated or explicitly deferred, not omissions:**
- C3-A01, C3-A02, and C3-A03 dispositions in plans 02, 05, 06, 07, and 09.
- Companion baseline, replay, browser proofs, and human visual or assistive-technology observations. These block acceptance and are specified as halt-or-pending, not as unstated work.
- xdist absence on the companion venv. Plan 06 halts rather than treating interpreter availability as a suite pass.
- C2-A05 retained helper overrides. They still set `form_tag=False` and are outside the two removals in plan 05.
- Current-pack Django 6.0. Plan 09 records it as untested and forbids substituting the floor run.
