# Phase 06.6 Plan Review — Cycle 2, verified against source at `f4c7744` (plans unchanged since `1faf42d`)

Method: I opened every product file, template, golden, test module, nox session, cached runtime and documentation page the nine revised plans cite and traced each claimed mechanism. The product tree is clean and byte-identical between the pinned baseline `cb26af4` and HEAD (`git diff --stat cb26af4 HEAD -- src tests docs examples noxfile.py` is empty), so line numbers below hold for the executor. I could not read two things from this sandbox and say so where it matters: the sibling companion directories (outside the working directory) and the GSD reference `planner-preconditions.md` (permission denied).

Anchor facts confirmed on current source:

- Nested form and duplicate token exist today: `tests/test1/golden/form_frame/create.html:1`, `delete.html:1`, `custom_form.html:1` each contain an outer `<form class="cv-form" …>` with a token, then an inner `<form method="post" >` with a second token. Cause: `src/crud_views/templates/crud_views/tags/form.html:3-7` tests and renders `form.helper` twice, and both library helpers leave crispy defaults (`src/crud_views/lib/crispy/form.py:43-50`, `136-146`).
- The crispy token branch is independent of `form_tag` (floor `bootstrap5/whole_uni_form.html:4-7`), and `FormHelper` exposes `disable_csrf` through `get_attributes` (crispy 2.7 `helper.py:202`, `290-306`); `FormHelper` has `__len__` (line 99) but no `__copy__`/`__bool__`.
- Workflow bypasses the shared tag: `src/crud_views_workflow/templates/crud_views_workflow/view_workflow.action.html:15` calls `{% crispy form form.helper %}` inside its own `<form>` (line 8), and loads `crispy_forms_tags` at line 2.
- Floor pack ignores group classes: `.nox/crispy_floor-3-12-django-6-0/.../bootstrap5/layout/formactions.html:1` hardcodes `class="mb-3"` and tests `formactions.attrs`, an attribute `FormActions.__init__` never sets (`crispy_forms/bootstrap.py:299-304` sets `flat_attrs`). The current pack reads `formactions.css_class` (`.nox/tests-3-12-django-5-2/.../formactions.html:3`). `FormActions.__init__` accepts `template=` (bootstrap.py:299), so a private subclass with a library-local template is viable.
- Cached runtimes: `tests-3-12-django-4-2` (Django 4.2.30, crispy 2.5, pack 2026.3), `tests-3-12-django-5-2` (5.2.18, 2.7, 2026.9), `crispy_floor-3-12-django-6-0` (6.0.9, 2.0, 2023.10), plus an unused `crispy_floor-3-12-django-4-2` (4.2.30, 2.0, 2023.10). No `tests-3-12-django-6-0` exists; `.venv` has Django 6.1.2.
- Key inventory: `tests/test1/test_button_classes.py:104-108` pins 84 keys, `:111-116` parses the single sentence at `docs/reference/buttons.md:151`, and the live table has 84 keys.

---

## 06.6-01

**Summary.** The tracer targets the real defect at the real seam, and the Round 1 fixes are executable: the two custom-helper fixtures (`tests/test1/test_form_button_checks.py:560-566`, `578-584`) and the four frame goldens are now in this plan's files and in 01-02's verify selection, with an explicit one-commit boundary for 01-01/01-02. The raw owner scanner (`assert_owned_form_markup`, plan lines 92, 139) answers H10, and the `Context.dicts` requirement (A10) copies a pattern that exists: `cv_alert` renders with `get_template(...).template.render(context)` under `context.push` just above `cv_render_form` (`src/crud_views/templatetags/crud_views.py:464-466` uses `context.flatten()` today). The owner-tier helpers the plan tells the executor to read first are at `src/crud_views/lib/crispy/buttons.py:44-77` and distinguish crispy response overlays exactly as the plan assumes.

**Strengths.**
- Mechanisms verified: raw `_form_action` is stored separately from the reversing property (`helper.py:183`, `232-240`), so "diagnose without `reverse()`" is implementable; `is_strict()` reads `CRUD_VIEWS_STRICT` defaulting to `DEBUG` (`src/crud_views/lib/exceptions.py:32-36`) and the test project sets it `True` (`tests/test1/conftest.py:41`), so both strict branches are exercisable.
- The enforced-CSRF analog cited in `read_first` exists: `tests/test1/test_form_validation.py:78-110` uses `Client(enforce_csrf_checks=True)` and asserts 403.
- The parent-ownership analog exists: `tests/test1/test_formsets.py:15-33` is the only raw nested-form guard, and `tests/test1/app/views_formset.py:44-50` sets only `form_tag=False`, so that page emits two tokens today, exactly as the plan assumes for A04.
- The decision to set only `form_tag=False` on the library helpers and keep CSRF suppression render-local is a deliberate, stated disposition of H09's open question. `src/crud_views/lib/formsets/inline_formset.py:58-59`, `144-145` set both flags directly for nested helpers, so the alternative existed; the plan's reason (standalone crispy token semantics) is coherent. Sign-off.
- The baseline archive is the right revision: product source at `cb26af4` equals HEAD.

**Concerns.**
- **LOW — standalone rendering of library forms changes shape, not only tokens.** Setting `form_tag=False` on `CrispyFormMixin.helper` means a standalone `{% crispy form %}` of any `CrispyModelForm` now emits no `<form>` while still emitting a token. The plan pins "current token semantics" for standalone helpers (line 123), which is accurate for the token, but the wrapper removal is a visible change that only plan 08 can document; 08-01 currently says "standalone crispy retains its independent semantics", which undersells it. Make 01's evidence note the wrapper change so 08 words it correctly.
- **LOW — `files` cap and new helper.** The scanner and tracer live in a new test module, fine; the two private functions land in the tag module. No overlap with other wave-1 plans (04 touches `button_classes.py`/`alert.html`; 06 touches `tests/browser/`). Verified no file overlap.

**Suggestions.**
- In the evidence log, record the standalone `{% crispy form %}` before/after for one `CrispyModelForm` so plan 08 has the exact wording.
- Keep the fixture migration diff minimal: `_CustomHelperForm`/`_DeleteCustomHelper` only need `helper.form_tag = False`; the policy tests at `:1082-1111` still reach `ValueError("form button 'submit'")` after that.

**Risk: LOW–MEDIUM.** Mechanisms verified; residual risk is the copy-strategy experiment, which the plan correctly gates with a stop condition rather than an assumption.

---

## 06.6-02

**Summary.** The plan matches the resolver exactly. The four package-only exits that must become theme-then-package are `src/crud_views/lib/view/label_mode.py:101`, `107`, `110`, `118`; `_UNSET` is a distinct sentinel (`:28`); the strict/warn-once helper is `:63-83`; E108 validates raw settings with `LOCATIONS`/`LABEL_MODES`/`is_label_mode` (`src/crud_views/lib/settings.py:159-188`); both W292 paths resolve through the public resolver (`src/crud_views/lib/view/buttons.py:434-437` context; `:568-571` form). The A02/A16/A17/A18 dispositions are all concrete in 02-01/02-02 text.

**Strengths.**
- Rebind-under-lock publication (A02) and an autouse snapshot/restore fixture in `tests/test1/conftest.py` (A16) are exactly what is missing: the existing autouse fixture only resets `_warned` (`conftest.py:23-32`), and the only registry-isolation fixture is module-local in `tests/test1/test_button_classes.py:94-101`.
- A17's `_theme_or_package_default` reading only the theme snapshot and `LABEL_MODE_DEFAULTS` prevents the recursion the current lambdas would otherwise create if a malformed setting is installed while the fallback is resolved.
- The plan refuses to merge owner maps and preserves `form_label_mode` membership semantics (`label_mode.py:122-146`), consistent with D-15.
- `LOCATIONS` already includes `"form"` (`src/crud_views/lib/view/button_data.py:19`), so the theme map's location vocabulary is the right one.

**Concerns.**
- **LOW — `settings.py` is in `files` but only prose should change.** 02-02 says so ("update stale resolver/settings descriptions"); keep it to docstrings so E108 semantics verified in 06.1/06.5 do not drift.
- **LOW — W292 "prove, do not modify" instruction is correct** and reduces risk; no further concern.

**Suggestions.**
- Add one explicit test for register → `override_settings` → exit restoring the theme value (both directions of D-15); the plan's "nested override_settings restoration for card" (A18) covers it if the executor reads it that way; spell it out.

**Risk: LOW.** All H/A items for this plan (H02 dependency, A02, A16, A17, A18) are resolved in planning.

---

## 06.6-03

**Summary.** The H01 disposition is now a fixed predicate rather than an experiment: pack name `bootstrap5`, resolved template origin inside the installed `crispy_bootstrap5` distribution, and byte-exact match against the audited 2023.10 template retained as a fixture; everything else delegates unchanged. That respects D-10 and rejects the generic sentinel fallback. The three constructors are where the plan says (`form.py:55-56`, `:141-144`, `src/crud_views/lib/views/list.py:125-133`); the H05 cache is real (`list.py:171-186` resolves `_cv_actions` once per prepared layout), and storing the key as primitive state resolved at render time is the right fix. H04 is resolved: `tests/test1/test_button_classes.py` is in `files` and in 03-02's verify.

**Strengths.**
- W362 claim verified: `_action_key_parts("form:actions:icon")` returns `None` because `actions` is not in `FORM_KINDS` (`src/crud_views/lib/button_classes.py:239-240`, `252-267`), so mode-suffixed group keys hit the "not a known key" branch (`:339-346`).
- The 86→88 count ownership is explicit and matches `buttons.md:151-156` plus the parser at `test_button_classes.py:111-116`.
- Floor runtime is required in the first task, and the only floor exclusion is the pre-existing wrapper golden named at `noxfile.py:55`.

**Concerns.**
- **MEDIUM — intermediate pack versions are neither bridged nor proven.** The exact-byte predicate triggers only for the 2023.10 template. The declared floor is `>=2023.10` (`noxfile.py:22`), and the first pack release whose `formactions.html` reads `css_class` is not identified anywhere in the plans. Any release between 2023.10 and that point will drop classes silently, and the predicate (correctly, for D-10 safety) will not inject. This is not a planning defect in the predicate; it is an unstated coverage limit. Record in `03-pack-bridge-evidence.md` and in plan 08's docs that class consumption is proven at the tested pack generations only, or enumerate additional byte-variants if obtainable without installing packages (installing would trip the legitimacy gate).
- **LOW — floor Django 4.2 is available and unused.** `.nox/crispy_floor-3-12-django-4-2` exists and matches the nox `crispy_floor` parametrization (`noxfile.py:93-95`). 03-01/03-03 run the floor only at 6.0. After A15 adds the theme modules to `CRISPY_FLOOR_TESTS`, CI will run them at the 4.2 floor without local evidence. Cheap to add one run.

**Suggestions.**
- Add the coverage-limit sentence above to 03-03's evidence and to 08-01's "actual tested pack support" wording.
- Run 03-03's floor selection once on `crispy_floor-3-12-django-4-2` as well, or record that combination as untested in 09.

**Risk: MEDIUM.** The mechanism is grounded; the residual is a support-claim boundary that must be stated, not a design gap.

---

## 06.6-04

**Summary.** Smallest and best-grounded plan. Literals and hooks are at `src/crud_views/templates/crud_views/tags/alert.html:2-5`; the golden is raw bytes (`tests/test1/golden/alerts/dismissible.html`, exact-class assertion at `tests/test1/test_alerts.py:191-198`); `cv_button_class` is an autoescaped `simple_tag` (`src/crud_views/templatetags/crud_views.py:570-573`), which also supports `as var`, so A03's "resolve into a template variable and add the separator only for a nonempty value" is implementable without a new tag. H04 is resolved in-task with 84→86 and the `buttons.md` count/arithmetic.

**Strengths.**
- `test_only_the_alert_templates_write_alert_markup` (`test_alerts.py:151`) scans templates, so moving literals into the class table is safe.
- The adapter tests exist (`tests/js/adapters.test.js`) and the vitest entry point exists (`node_modules/vitest/vitest.mjs`); 04-02's command is runnable.
- Both W362 outcomes are verified: 2-segment keys present in `DEFAULT_BUTTON_CLASSES` pass (`button_classes.py:328-329`); `alert:*:mode` fails because `alert` is in neither `VARIANT_LOCATIONS` nor the form branch.

**Concerns.**
- **LOW — none remaining from Round 1.** A03 whitespace rule pinned (`"alert alert-success"` exactly for empty/None; `class=""` on the close control).

**Suggestions.**
- Parametrize the omitted-value test over `""`, `None` and a hostile string as the plan implies.

**Risk: LOW.**

---

## 06.6-05

**Summary.** Expansion targets are correct: all four content templates render through `cv_render_form` (`view_create.content.html:10`, `view_delete.content.html:21`, `view_custom_form.content.html:10`); the delete page omits its form under `has_protected_objects` (`view_delete.content.html:15-23`) and workflow omits it without choices (`view_workflow.action.html:6-19`). `X-CV-Modal` is the real header (`src/crud_views/lib/view/base.py:58-59`). `WorkflowForm` extends `CrispyForm` (`src/crud_views_workflow/lib/forms.py:11`), so routing it through `cv_render_form` inherits plan 01's fix. The A11 removals are safe: `PublisherFormSetForm.helper` (`views_formset.py:44-50`) and `QuestionnaireForm.helper` (`examples/bootstrap5/formsets/views.py:36-41`) only set `form_tag=False`. A13's polymorphic create-select renders `crud_views/view_create.html` (`src/crud_views_polymorphic/lib/create_select.py:25`), so it is a genuine extra `cv_render_form` consumer.

**Strengths.**
- H10's owner scanner is reused rather than reinvented; auxiliary forms (language selector at `src/crud_views/templates/crud_views/snippets/language_selector.html:13`, action POST forms in `tags/list_action_form.html`) are explicitly allowed as siblings.
- A12 is concrete: the `crispy_forms_tags` load at `view_workflow.action.html:2` becomes unused and is removed.
- The W292 static-reach claim for inherited helpers is consistent with `buttons.py:548-551` ("whose helper, action provider and button hooks are still the package implementations").

**Concerns.**
- **MEDIUM — "page and modal for every actionable type" is not a real-view path for create/update.** `cv_modal_supported` defaults to `False` (`base.py:111`) and check `E251` rejects `cv_modal` on unsupported views (`base.py:167-172`, tested at `tests/test1/test_modal.py:182-189`). Only `CustomFormView` (`src/crud_views/lib/views/form.py:20`, `:52`), `DeleteView` (`delete.py:55`), `WorkflowView` via `CustomFormView` (`src/crud_views_workflow/lib/views.py:18`) and object-detail support it. 05-01's behavior bullet and acceptance ("Five actionable form types pass page/modal …") must scope modal to custom/delete/workflow through real views; create/update "modal" can only be the header-driven frame render that `test_form_frame.py:94-98` already does, which is not a view response. Same wording appears in 07-02.
- **LOW — `test_workflow.py` is unit-level** (`:19-148`: state names, transitions, labels); it carries no page GET/POST, so the preservation command adds little and the new matrix must own workflow HTTP coverage. The plan does create those cases; just do not count the old suite as workflow-page preservation.
- **LOW — "create local test-only routes where needed"** implies edits to `tests/test1/app/views.py` or the test URLconf, which are not in `files_modified`. Either reuse `cv_author_modal`/`cv_publisher_formset` fixtures (both exist in `conftest.py`) or add the files.

**Suggestions.**
- Rewrite 05-01's modal clause: "modal responses for the modal-capable types (custom form, delete, workflow); create/update are page-only by E251".
- Prefer existing modal fixtures (`client_user_author_modal`, `test_modal.py:74-140` shows custom-form/delete modal 422/204 contracts) over new routes.

**Risk: LOW–MEDIUM.** One acceptance sentence overstates reachable coverage; the rest is grounded.

---

## 06.6-06

**Summary.** The fail-closed design is unchanged and now has the A01/A05/A09 dispositions written in: independent pinned archive, import-pure utility loaded by explicit `importlib` path (no package marker required; `tests/browser/` indeed has no `__init__.py` while `tests/` and `tests/test1/` do), and a committed `status: halted` SUMMARY when the precondition fails. The pinned revision `cb26af4` exists and its product tree equals HEAD. H06 remains correctly deferred as an external prerequisite: `git remote -v` shows only `origin`, the only companion references are historical paths and revisions in `superpowers/notes/2026-10-28-pre-1.0-before-theme-freeze-analysis.md:93-97` (`../tabler-test`, `../crispy-tabler`, `0c5e816`, `32a3533`), and I cannot list sibling directories from this sandbox.

**Strengths.**
- Negative-evidence tests (missing source, mutated revision, empty results) and provenance hashes make a synthetic pass impossible, matching D-13/D-18.
- Running `pytest tests -k theme_adoption_sources` under the whole tree is safe: `tests/conftest.py` is empty and `tests/test1/conftest.py:35` configures Django for the session, so collection of the Django-free browser test works.

**Concerns.**
- **HIGH (external, unchanged) — H06.** No authoritative companion identity exists in the repository or in this environment. 06-02, 07 and final acceptance stay blocked. This is unresolved execution evidence, not a planning defect, and the plans say so consistently.
- **MEDIUM (open question) — `<precondition>` halting semantics.** 06-02 is `type="auto"` and relies on the executor halting "exactly as planner-preconditions.md requires" (plan line 109). I could not read that reference (permission denied). The execute-plan workflow I can see stops only on `type="checkpoint:*"` tasks. If the executor does not treat `<precondition>` as a halt, the A09 halted-summary instruction still prevents an illegal partial state, but the capture commands would be attempted first. Someone with access to `planner-preconditions.md` should confirm; otherwise convert 06-02's prerequisite into an explicit `checkpoint:human-action` as Round 1 proposed.
- **LOW — companion dependencies.** The cached environments contain this repo's dependencies only; the real theme suite may need extras (crispy-tabler at minimum). The precondition names "required existing companion dependencies", which is correct; just expect this to be the practical blocker after sources arrive.

**Suggestions.**
- Have the halted SUMMARY record the exact env var values tried and the three discovery sources checked, so the resume command is deterministic.

**Risk: HIGH** for schedule (external), **LOW** for correctness of what it builds.

---

## 06.6-07

**Summary.** The browser plan reuses a mature harness (`tests/browser/presentation.cjs:385-430`: revision, source hashes, checkout-import assertion, supported-series regex, port probe, fixture readiness, Chromium launch) and the real `/signin/` fixture (`tests/browser/presentation_server.py:191-197`). A06 is resolved by three tasks; H09/H10/H11 are explicit in 07-02/07-03. It inherits H06 in full.

**Strengths.**
- Raw nesting checks before browser parsing plus `element.form`/FormData/submitter and negative CSRF are the right evidence for D-12/D-16.
- H11 is handled exactly as Round 1 asked: conditional, isolated adaptation of the real pack's `layout/formactions.html`, included in the patch and the purpose-level override count.
- The config test pattern exists to copy (`tests/browser/presentation-config.test.cjs:1-30`, `node:test` over invalid/reserved ports).

**Concerns.**
- **HIGH (inherited) — H06.** Both 07-01 and 07-02 preconditions depend on `06-companion-baseline.json`.
- **MEDIUM — modal scope overstated**, same as plan 05: "all five form types on page/modal" (07-02) is not achievable for create/update through real views (`E251`, `base.py:167-172`). Scope modal cases to custom/delete/workflow.
- **LOW — A14's "dedicated" port is not dedicated.** `presentation.cjs:2-5` already defaults to `8145` and reserves only `8143`/`8144`; `modal-focus.cjs:21,79` binds `8143`; `conditional-formsets.cjs:28-31` defaults `8144`. The plan's `CV_THEME_PORT` default `8145` collides with the presentation harness default. Because the plan rejects an occupied port before spawn, a concurrent run fails closed rather than corrupts, so this is LOW, but `06.6-SOURCE-AUDIT.md:20` ("browser port 8145 is owned") is inaccurate. Use `8146` and reject `8143`–`8145`.

**Suggestions.**
- Record `INSTALLED_APPS` order and `CRISPY_TEMPLATE_PACK`/`CRISPY_ALLOWED_TEMPLATE_PACKS` in the results JSON (the test project hardcodes `bootstrap5` at `tests/test1/conftest.py:117-118`; the theme server must differ).
- Fix the port default and the SOURCE-AUDIT sentence.

**Risk: HIGH** (availability), **MEDIUM** (scope wording).

---

## 06.6-08

**Summary.** Documentation obligations map to existing executable-docs infrastructure, and both Round 1 HIGHs are resolved at the right task boundary. H07: `tests/test1/test_label_mode_docs.py:786-800` asserts the sentence "falls back to its package floor." which lives at `docs/migrating-1.0.md:64`; 08-02 updates both together. H08: `test_alerts.py:249-255` requires exactly one `django/html` fence under "### Custom alert frame" (`docs/reference/theme.md:308-330`), and 08-01 runs `test_alerts.py`. The numbered-step structure 08-01 must preserve is pinned at `test_label_mode_docs.py:180-252` (five context steps ending in `default_label_mode("context")`, two list steps, three card steps), and `docs/reference/action_menus.md:95-100`, `109-111`, `128-130`, `185-187` are the lists it will edit inside the floor step.

**Strengths.**
- A08 verified: `docs/getting_started/tutorial-5-filters-permissions.md:35` and `docs/reference/list_view.md:182-232` describe `get_form_actions()` replacement/removal and `add_input()` hidden inputs; `tests/test1/test_form_button_docs.py:155-161` pins those markers. Retaining them is correct; the opt-in recipe belongs in `theme.md`.
- Changelog anchors exist: Unreleased `### Breaking` (`CHANGELOG.md:7`), `### Fixed` (`:311`), `### Added` (`:421`).
- The settings table rows that assert package-only fallback are identified (`docs/reference/settings.md:78-81`, `143`, `157`) and the table test (`test_label_mode_docs.py:120`) is in 08-01's selection.

**Concerns.**
- **LOW — standalone-rendering wording.** 08-01 says "standalone crispy retains its independent semantics". After plan 01, standalone `{% crispy form %}` of a library form emits no `<form>` wrapper (token unchanged). State that the caller must own the `<form>`.
- **LOW — pack support wording.** Tie "actual tested pack support" to the concrete tested generations (floor 2023.10 and current 2026.x) per the plan 03 coverage limit above.

**Suggestions.**
- Grep docs for `form_tag`/`FormHelper(` before writing so every helper example carries `form_tag=False`.

**Risk: LOW.**

---

## 06.6-09

**Summary.** The integration commands are runnable as written: the three interpreters exist; the single floor deselect matches `noxfile.py:55`; `conditional-formsets.cjs --case lifecycle` is a real required family (`:57`) and defaults to the floor interpreter unless `CV_FOCUS_PYTHON` is set (`:123`); `modal-focus.cjs` honors `CV_FOCUS_PYTHON` (`:81`); `vitest.config.js`, `vitest.integration.config.js`, `.venv/bin/mkdocs` and `.venv/bin/ruff` exist. A07 is feasible: `examples/bootstrap5/pytest.ini` sets `DJANGO_SETTINGS_MODULE = project.settings` and `pythonpath = .`, test modules exist (`test_docs_sync.py`, `*/tests.py`), the cached 5.2 env has guardian/polymorphic/fsm/tables2/filter/ordered_model/pytest-django/xdist/pygments, and `requirements/demo.txt` is deploy-only (gunicorn, whitenoise, ratelimit) and not imported by `project/settings.py`. H12 is correctly dispositioned: no current-pack Django 6.0 environment exists. A15 is concrete (`CRISPY_FLOOR_TESTS` at `noxfile.py:26-50`; AST read avoids importing nox).

**Strengths.**
- Refuses historical exclusions for new scenarios, names the Django-6-only CSP skip, and separates automated pass from pending human/AT observations.
- Prior floor evidence pattern exists (`06.5-09-SUMMARY.md:84-96`: 8328 passed with the single deselect and four workers), so the floor full run is realistic.
- A09's blocked-path contract (halted SUMMARY, partial PUBLIC-SURFACE, ACCEPTANCE blocked) is now explicit in 09-02.

**Concerns.**
- **HIGH (inherited) — H06.** `--check-final` cannot pass without 06/07 evidence; the plan says so.
- **LOW — unused floor 4.2 runtime.** `crispy_floor-3-12-django-4-2` exists and is what nox's `crispy_floor` session also runs; after A15 the new theme modules will execute there in CI without local evidence. Either run that selection once or list it beside the H12 limit.
- **LOW — effort.** Three full runs, two browser lanes, example project, docs/lint, plus authoring, in 35k tokens; 06.4-10 took 60 minutes for comparable scope.

**Suggestions.**
- Add the floor-4.2 selection run (or its explicit "untested" note) to 09-01.
- Set `CV_FOCUS_PYTHON` explicitly for `conditional-formsets.cjs` in the verification list so the interpreter is recorded rather than defaulted.

**Risk: LOW** for content; schedule inherits 06/07.

---

## Round 1 ledger verification (H01–H12, A01–A18)

| ID | Current disposition in plans | Verified against source | Verdict |
|---|---|---|---|
| H01 | 03-01 fixed predicates: pack `bootstrap5`, installed-distribution origin, byte-exact 2023.10 fixture; no fallback for custom origins | Floor template bytes and `FormActions(template=)` confirmed | **Resolved (planning)**; new MEDIUM coverage-limit note on intermediate pack versions |
| H02 | 01-02 migrates `_CustomHelperForm`/`_DeleteCustomHelper`; 02 depends on 01 | Fixtures at `test_form_button_checks.py:560-584`; policy tests `:1082-1111` | **Resolved** |
| H03 | 01-01/01-02 one green commit incl. four goldens | Goldens and `test_form_frame.py:71-73` | **Resolved** |
| H04 | 04-01 (84→86) and 03-02 (86→88) own `test_button_classes.py` and `buttons.md` | `test_button_classes.py:104-116`, `buttons.md:151` | **Resolved** |
| H05 | 03-01 primitive key state, 03-02 freshness/deepcopy/restoration tests | `list.py:171-186` cache | **Resolved** |
| H06 | Deferred external prerequisite in 06/07/09 | No companion identity in repo; sandbox cannot see siblings | **Unresolved, external; correctly not waived** |
| H07 | 08-02 co-locates migration sentence and assertion | `test_label_mode_docs.py:786-800`, `migrating-1.0.md:64` | **Resolved** |
| H08 | 08-01 preserves single fence and runs `test_alerts.py` | `test_alerts.py:249-255`, `theme.md:308-330` | **Resolved** |
| H09 | 01 old-copy regressions and sequencing note; 05 stock workflow; 07/08 copied workflow | `view_workflow.action.html:15`; `inline_formset.py:58-59` alternative acknowledged | **Resolved** (with LOW wording note for 08) |
| H10 | Raw HTMLParser owner scanner in 01, reused by 05/07/08 | Auxiliary forms exist (`language_selector.html:13`, action forms) | **Resolved** |
| H11 | 07-02 isolated pack template adaptation; 07-03 replay/override count | Floor pack drops classes; real pack unverified | **Resolved in planning; execution gated by H06** |
| H12 | 09-01 records current-pack 6.0 as untested | No `tests-3-12-django-6-0` env | **Resolved** |
| A01 | Independent archives in 01/06 | `cb26af4` equals HEAD for product source | Resolved |
| A02 | Rebind under lock | — | Resolved |
| A03 | Exact whitespace rule | `alert.html:2`, golden | Resolved |
| A04 | 05-02 parent formset raw tokens | `test_formsets.py:15-33` | Resolved |
| A05 | Import-pure utility, importlib load, env cleared | `tests/browser/` has no `__init__.py`; root conftest empty | Resolved |
| A06 | 07 split into three tasks | — | Resolved |
| A07 | 09-01 example gate | pytest.ini, tests and extras present | Resolved |
| A08 | 08-01 retains tutorial wording | `tutorial-5:35`, `list_view.md:182-232`, docs test `:155-161` | Resolved |
| A09 | Halted summaries in 06-02/09-02 | — | Resolved (precondition semantics remain an open question) |
| A10 | `Context.dicts` preserved via `context.push` | `cv_alert` pattern; `crispy/buttons.py:44-77` | Resolved |
| A11 | 05-02 removes redundant overrides | `views_formset.py:44-50`, example `:36-41` | Resolved |
| A12 | Remove `crispy_forms_tags` load | `view_workflow.action.html:2` | Resolved |
| A13 | Polymorphic create-select case | `create_select.py:25` renders `view_create.html` | Resolved |
| A14 | Port 8145, reject 8143/8144 | `presentation.cjs:2` already defaults to 8145 | **Partially**: pick 8146, reject 8145 too; fix SOURCE-AUDIT:20 |
| A15 | Permanent `CRISPY_FLOOR_TESTS` update | `noxfile.py:26-50` | Resolved |
| A16 | Autouse snapshot/restore | `conftest.py:23-32` only resets `_warned` | Resolved |
| A17 | Setting-free theme/package helper | `label_mode.py:101-118` lambdas | Resolved |
| A18 | Card theme floor pinned | — | Resolved |

## Cross-plan assessment

**Dependency ordering.** Wave 1 (01, 04, 06) has no modified-file overlap (verified). Wave 2 (02, 03, 05) is correctly serialized on `form.py` (01→03), `button_classes.py`/`buttons.md`/`test_button_classes.py` (04→03) and `test_form_button_checks.py` (01→02). Wave 3 (07, 08) touches disjoint trees. The shared-ID gate handles THEME-01 (01/05/07/09) and THEME-05 (06/07/09).

**Goal achievement.** THEME-01 to THEME-04 and THEME-06 are grounded in current source with discriminating tests; the only wording defects are the modal-scope sentences in 05/07 and the standalone-rendering sentence in 08. THEME-05 is honestly blocked on H06; the plans neither invent sources nor allow fixture substitution.

**Scope.** No creep. The one support-claim boundary not yet stated is plan 03's intermediate-pack-version coverage.

**Security.** CSRF positive/negative tests, autoescaped class values, no new auth surface, and the instruction that diagnostics never resolve `form_action` (which could embed identifiers) are consistent with ASVS 5.0 V3.

## New and remaining concerns (cycle 2)

1. **MEDIUM (05-01, 07-02):** modal coverage claimed for create/update is not a real-view path; `E251` forbids it (`base.py:167-172`). Scope to custom/delete/workflow.
2. **MEDIUM (03):** exact-byte floor predicate leaves pack releases between 2023.10 and the first `css_class`-aware template neither bridged nor proven; state the tested-generation limit in 03 evidence and 08 docs.
3. **MEDIUM, open question (06-02):** `<precondition>` halt semantics unverified here (reference file unreadable in this sandbox); A09's halted SUMMARY bounds the damage.
4. **LOW (07, SOURCE-AUDIT:20):** `CV_THEME_PORT` default 8145 collides with `presentation.cjs` default; fails closed, but not "dedicated".
5. **LOW (01/08):** standalone library forms lose their `<form>` wrapper; document as part of the ownership note.
6. **LOW (03/09):** unused `crispy_floor-3-12-django-4-2` runtime; run once or list as untested.
7. **LOW (05):** `test_workflow.py` is unit-level; new matrix must own workflow HTTP coverage; test-only routes imply files outside the list.

## Overall risk: MEDIUM

Product plans (01–05, 08) are low-risk and well evidenced; every Round 1 planning concern assigned to them is resolved with an executable disposition. Schedule risk is concentrated in H06 (plans 06, 07, 09), which is an external prerequisite and is handled truthfully. Before execution, fix the two wording defects (modal scope in 05/07; standalone wrapper in 08), state plan 03's pack-coverage limit, and correct the browser port default.
