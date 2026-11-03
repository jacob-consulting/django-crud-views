# Cross-AI Plan Review — Phase 06.6 (Cycle 3 Focused Resolution Verification)

Verified against current repository source and revised plans at `9b10cf0`, prior Cycle 2 review `cec0b2f` (`.planning/phases/06.6-theme-adoption-seams-from-the-tabler-sync/06.6-REVIEWS.md:704-758`), the `06.6-RESEARCH.md` source availability addendum, and the supplied companion checkout `../tabler-test` at clean HEAD `885dfc791a150fdc715d6fb34c2e6181d6b92f3c` (external-directory reads were not requested; verbatim numbered companion sources and template inventory supplied by the orchestrator were verified directly against the plan specifications).

---

## 06.6-01

### 1. Summary
Plan `06.6-01` (`06.6-01-PLAN.md:1-251`) delivers the single-form and single-CSRF-token render boundary (`THEME-01`, `D-01`–`D-04`, `D-16`) by setting `form_tag = False` on `CrispyFormMixin.helper` (`src/crud_views/lib/crispy/form.py:43-50`) and `CrispyDeleteForm.helper` (`src/crud_views/lib/crispy/form.py:136-146`), selecting and adapting `cv_form_helper` once in `cv_render_form` (`src/crud_views/templatetags/crud_views.py:464-466`), and consuming `cv_form_helper` in `src/crud_views/templates/crud_views/tags/form.html:1-7`. Both prior Round 1 (`H02`, `H03`, `H09`, `H10`, `A01`, `A04`, `A10`) and Round 2 (`C2-A02`) concerns assigned to this plan are resolved in executable task instructions (`06.6-01-PLAN.md:124-129,192-193,217-249`).

### 2. Strengths
- **Standalone library-form wrapper change explicitly recorded (`C2-A02` signed off):** Task `01-01` (`06.6-01-PLAN.md:123-129`) and Task `01-03` (`06.6-01-PLAN.md:174-175,192-193`) explicitly distinguish token preservation from outer-form removal when a `CrispyModelForm` (`src/crud_views/lib/crispy/form.py:87`) is rendered via standalone `{% crispy form %}`: setting `form_tag = False` on `CrispyFormMixin.helper` (`src/crud_views/lib/crispy/form.py:44-50`) removes the helper-owned `<form>` wrapper while keeping its fields and CSRF token, and tests that an explicit caller-owned `<form>` wrapper restores one form and one token without adding a duplicate token.
- **Atomic commit boundary for renderer, custom-helper fixtures, and frame goldens (`H02`, `H03` signed off):** Tasks `01-01` and `01-02` (`06.6-01-PLAN.md:12-17,95-98,154-167`) update `_CustomHelperForm` and `_DeleteCustomHelper` in `tests/test1/test_form_button_checks.py` and the four frame goldens (`tests/test1/golden/form_frame/{create,update,custom_form,delete}.html:1`) in the same commit as the renderer change, verified together by `pytest tests/test1/test_theme_form_ownership.py tests/test1/test_form_frame.py tests/test1/test_form_button_checks.py -n 4 -q` (`06.6-01-PLAN.md:164`).
- **Context tier preservation and raw event scanning (`A10`, `H10` signed off):** Task `01-01` (`06.6-01-PLAN.md:92,119-123,142-144`) replaces `context.flatten()` in `src/crud_views/templatetags/crud_views.py:466` with `get_template(...).template.render(context)` inside `with context.push(...)` (matching `cv_alert` at `src/crud_views/templatetags/crud_views.py:453-455`) to preserve `Context.dicts` for `_is_response_overlay`, `_cv_helper_tier`, and `_cv_page_tier` (`src/crud_views/lib/crispy/buttons.py:44-77`), and scans raw `HTMLParser` events via `assert_owned_form_markup` before DOM repair.

### 3. Concerns
- None. All Round 1 and Round 2 (`C2-A02`) concerns for this plan are resolved.

### 4. Suggestions
- None; all previously suggested improvements are incorporated into Tasks `01-01` through `01-03`.

### 5. Risk Assessment
**LOW** — The create ownership seam, custom-helper adaptation experiment (`A2` with fail-closed design checkpoint), and fixture/golden migrations are grounded directly in `src/crud_views/lib/crispy/form.py` and `src/crud_views/templatetags/crud_views.py`.

---

## 06.6-02

### 1. Summary
Plan `06.6-02` (`06.6-02-PLAN.md:1-178`) implements `register_label_mode_defaults(defaults)` in `src/crud_views/lib/view/label_mode.py`, adding the validated theme floor layer (`package → theme → project setting`) to `default_label_mode(location)` (`src/crud_views/lib/view/label_mode.py:86-120`) while preserving explicit owner modes, `override_settings` responsiveness, `crud_views.E108` (`src/crud_views/lib/settings.py:161-190`), and `viewset.W292` (`src/crud_views/lib/view/buttons.py:435-448,546-584`) (`THEME-02`, `D-05`–`D-07`, `D-15`). All Round 1 concerns (`H02`, `A02`, `A16`, `A17`, `A18`) remain resolved (`06.6-02-PLAN.md:158-175`), and no Round 2 concerns applied to this plan.

### 2. Strengths
- **Setting-free non-recursive fallback (`A17` signed off):** Task `02-02` (`06.6-02-PLAN.md:69,120-124`) routes the four package-only fallback exits in `src/crud_views/lib/view/label_mode.py:101,107,110,118` through `_theme_or_package_default(location)`, reading only the theme snapshot and `LABEL_MODE_DEFAULTS` (`src/crud_views/lib/view/label_mode.py:23-25`) so malformed settings cannot trigger recursion.
- **Atomic rebind under lock and autouse fixture isolation (`A02`, `A16`, `A18` signed off):** Task `02-01` (`06.6-02-PLAN.md:69-72,92-99`) validates the entire dictionary against `LOCATIONS` (`src/crud_views/lib/view/button_data.py:19`) and `is_label_mode()` (`src/crud_views/lib/view/label_mode.py:35-36`) before rebinding `_THEME_LABEL_MODE_DEFAULTS` under `_theme_defaults_lock`, and adds an `autouse` snapshot/restore fixture in `tests/test1/conftest.py` verified across both `"form"` and `"card"` locations.

### 3. Concerns
- None. All Round 1 concerns (`H02`, `A02`, `A16`, `A17`, `A18`) are resolved and no Round 2 concerns were raised.

### 4. Suggestions
- None; all suggestions are already incorporated into Tasks `02-01` and `02-02`.

### 5. Risk Assessment
**LOW** — Self-contained registry and resolver extension in `src/crud_views/lib/view/label_mode.py` with complete test isolation.

---

## 06.6-03

### 1. Summary
Plan `06.6-03` (`06.6-03-PLAN.md:1-194`) adds `form:actions` and `form:filter-actions` (both `""`) to `DEFAULT_BUTTON_CLASSES` (`src/crud_views/lib/button_classes.py:15-113`), wires them into `CrispyFormMixin.get_form_actions` (`src/crud_views/lib/crispy/form.py:55-56`), `CrispyDeleteForm.helper` (`src/crud_views/lib/crispy/form.py:141-144`), and `ListViewFilterFormHelper.get_form_actions` (`src/crud_views/lib/views/list.py:125-133`), and provides a private `_ThemedFormActions` bridge in `src/crud_views/lib/crispy/actions.py` for the `crispy-bootstrap5==2023.10` floor (`THEME-03`, `D-09`, `D-10`, `D-17`). All Round 1 (`H01`, `H04`, `H05`, `H11`) and Round 2 (`C2-A03`) concerns are resolved (`06.6-03-PLAN.md:141-148,165-191`).

### 2. Strengths
- **Both cached crispy-floor Django series verified (`C2-A03` signed off):** Task `03-03` (`06.6-03-PLAN.md:141-148`) now executes `pytest tests/test1/test_theme_action_groups.py tests/test1/test_form_buttons_golden.py tests/test1/test_filter.py -n 4 -q --deselect tests/test1/test_form_buttons_golden.py::test_filter_form_baseline` on both `.nox/crispy_floor-3-12-django-6-0/bin/python` and `.nox/crispy_floor-3-12-django-4-2/bin/python` (matching the `@nox.parametrize("django", ["4.2", "6.0"])` session in `noxfile.py:97`) and records separate provenance and results in `03-pack-bridge-evidence.md`.
- **Exact floor-template discriminator (`H01`, `H11` signed off):** Task `03-01` (`06.6-03-PLAN.md:67,76-86`) restricts `crud_views/crispy/bootstrap5_formactions.html` to `template_pack == "bootstrap5"`, resolved origin inside the installed `crispy_bootstrap5` package's `layout/formactions.html`, and exact source equality with the audited `2023.10` floor template; custom templates and non-Bootstrap packs delegate unchanged.
- **Render-time class resolution and `86 → 88` key inventory (`H04`, `H05` signed off):** Task `03-02` (`06.6-03-PLAN.md:111-126`) resolves classes dynamically per render on `ListViewFilterFormHelper._cv_actions` (`src/crud_views/lib/views/list.py:172-180`) without mutating or accumulating `css_class` across `copy.deepcopy` (`src/crud_views/lib/views/list.py:155`), and updates `EXPECTED_KEYS` (`tests/test1/test_button_classes.py:21-106`) and `docs/reference/buttons.md:151` from `86` to `88`.

### 3. Concerns
- None. All Round 1 and Round 2 (`C2-A03`) concerns are resolved.

### 4. Suggestions
- None; all suggestions are already incorporated into Tasks `03-01` through `03-03`.

### 5. Risk Assessment
**LOW** — The floor discriminator, `deepcopy`-safe dynamic class resolution, key-inventory synchronization, and dual-series floor verification (`4.2` and `6.0`) are completely specified.

---

## 06.6-04

### 1. Summary
Plan `06.6-04` (`06.6-04-PLAN.md:1-125`) adds `alert:dismissible` (`"alert-dismissible fade show"`) and `alert:close` (`"btn-close"`) to `DEFAULT_BUTTON_CLASSES` (`src/crud_views/lib/button_classes.py:92-96`) and consumes them via `cv_button_class` in `src/crud_views/templates/crud_views/tags/alert.html:2-5` (`THEME-04`, `D-08`, `D-17`). All Round 1 concerns (`H04`, `A03`) remain resolved (`06.6-04-PLAN.md:108-122`), and no Round 2 concerns applied to this plan.

### 2. Strengths
- **Exact omitted-value whitespace and default byte-identity (`A03` signed off):** Task `04-01` (`06.6-04-PLAN.md:67-70`) resolves `alert:dismissible` into a template variable in `src/crud_views/templates/crud_views/tags/alert.html:2` and adds the leading space separator only when nonempty, producing exact `class="alert alert-success"` on the wrapper and `class=""` on the close button for `""`/`None` while preserving `tests/test1/golden/alerts/dismissible.html:1-7` byte-for-byte under defaults.
- **Task-synchronized `84 → 86` key count (`H04` signed off):** Task `04-01` (`06.6-04-PLAN.md:60,70-73`) updates `EXPECTED_KEYS` in `tests/test1/test_button_classes.py:105` and `docs/reference/buttons.md:151` in the same task as `DEFAULT_BUTTON_CLASSES`, and `button_class_check_messages` (`src/crud_views/lib/button_classes.py:328-346`) rejects mode-suffixed `alert:close:icon` / `alert:dismissible:both` with `crud_views.W362`.

### 3. Concerns
- None. All Round 1 concerns (`H04`, `A03`) are resolved.

### 4. Suggestions
- None; all suggestions are already incorporated into Tasks `04-01` and `04-02`.

### 5. Risk Assessment
**LOW** — Minimal, well-tested leaf template and class-table update.

---

## 06.6-05

### 1. Summary
Plan `06.6-05` (`06.6-05-PLAN.md:1-162`) routes `src/crud_views_workflow/templates/crud_views_workflow/view_workflow.action.html:15` through `{% cv_render_form %}`, verifies full-page GET/POST/CSRF ownership across all five stock form types (create, update, custom form, delete, workflow) plus parent formsets, plain `django.forms.Form` views, and `PolymorphicCreateSelectView`, scopes modal (`X-CV-Modal: true`) HTTP coverage to the modal-supported view types (`CustomFormView`, `DeleteView`, `WorkflowView`), and removes the two targeted redundant `form_tag=False` helper overrides (`THEME-01`, `D-16`, `D-19`). All Round 1 (`H03`, `H09`, `H10`, `A04`, `A11`, `A12`, `A13`) and Round 2 (`C2-A01`, `C2-A05`) concerns are resolved (`06.6-05-PLAN.md:18,64-86,93-95,128-159`).

### 2. Strengths
- **Modal HTTP coverage accurately scoped to `cv_modal_supported=True` views (`C2-A01` signed off):** `06.6-05-PLAN.md:18,64-66,71-75,85,93-94` explicitly scopes real modal (`X-CV-Modal: true`) HTTP GET/POST responses to `CustomFormView` (`src/crud_views/lib/views/form.py:20,52`), `DeleteView` (`src/crud_views/lib/views/delete.py:55`), and `WorkflowView` (`src/crud_views_workflow/lib/views.py:18`, inheriting `CustomFormView`), while preserving `CreateView` (`src/crud_views/lib/views/create.py:12`) and `UpdateView` (`src/crud_views/lib/views/update.py:9`) at `cv_modal_supported = False` (`src/crud_views/lib/view/base.py:111`) and testing their `E251` rejection (`src/crud_views/lib/view/base.py:168-172`).
- **Explicit disposition of remaining `form_tag=False` helper overrides (`C2-A05` signed off):** The Round 2 ledger (`06.6-05-PLAN.md:155-158`) explicitly retains `EventForm.helper` (`examples/bootstrap5/conditional/views.py:132-137`), `PublisherMainForm.helper` and `BookMainForm.helper` (`tests/test1/test_fragment_authorization.py:177-196`), and `BrowserPublisherForm.helper` (`tests/browser/conditional_formsets_server.py:139-143`) as compatible custom helpers in accepted conditional/authorization/browser fixtures, while Task `05-02` (`06.6-05-PLAN.md:95-96`) removes `PublisherFormSetForm.helper` (`tests/test1/app/views_formset.py:44-50`) and `QuestionnaireForm.helper` (`examples/bootstrap5/formsets/views.py:36-41`) and tests restored static `W292` inspection (`src/crud_views/lib/view/buttons.py:511-515`).
- **Workflow template migration and unused tag cleanup (`H09`, `A12` signed off):** Task `05-01` (`06.6-05-PLAN.md:69-77`) replaces `{% crispy form form.helper %}` at `src/crud_views_workflow/templates/crud_views_workflow/view_workflow.action.html:15` with `{% cv_render_form %}` and removes `{% load crispy_forms_tags %}` at line `2`.

### 3. Concerns
- None. All Round 1 and Round 2 (`C2-A01`, `C2-A05`) concerns are resolved.

### 4. Suggestions
- None; all suggestions are already incorporated into Tasks `05-01` and `05-02` or explicitly dispositioned in the Round 2 ledger (`06.6-05-PLAN.md:155-158`).

### 5. Risk Assessment
**LOW** — All view types, modal support boundaries (`E251`), parent formset guards (`tests/test1/test_formsets.py:16-35`), and helper override dispositions match live codebase declarations.

---

## 06.6-06

### 1. Summary
Plan `06.6-06` (`06.6-06-PLAN.md:1-189`) builds the hermetic companion-source provenance and baseline utility (`tests/browser/theme_adoption_sources.py` and `tests/browser/test_theme_adoption_sources.py`) and captures the isolated unmodified companion baseline (`06-companion-baseline.json`, `06-COMPANION-SETUP.md`) against the supplied `../tabler-test` monorepo at `885dfc791a150fdc715d6fb34c2e6181d6b92f3c` and archived pre-phase core revision `cb26af4dfef2afb31d774a219abfad1c675cdff1` (`THEME-05`, `D-11`, `D-13`, `D-18`). Round 1 (`A01`, `A05`, `A09`) and Round 2 (`H06 — source acquisition`) concerns are resolved in the plan (`06.6-06-PLAN.md:69-74,80-131,152-186`).

### 2. Strengths
- **`H06` source acquisition resolved against verified `../tabler-test` monorepo (`H06 — source acquisition` signed off):** `06.6-06-PLAN.md:69-74,80-97,111-125,176-186` and `06.6-RESEARCH.md` (Source availability addendum) accurately bind both `CV_THEME_SOURCE` and `CV_PACK_SOURCE` to `/home/alex/projects/alex/tabler-test` at clean commit `885dfc791a150fdc715d6fb34c2e6181d6b92f3c`, containing `src/crud_views_tabler` (`../tabler-test/src/crud_views_tabler/apps.py:4-31`) and `src/django_tabler` (`../tabler-test/README.md:41-50`). The plan preserves `../django-crud-views` (`../tabler-test/pyproject.toml:18`) via isolated sibling `baseline/tabler-test` + `baseline/django-crud-views` and `candidate/tabler-test` + `candidate/django-crud-views` copies without touching the original checkouts.
- **Exact companion test suites and Python >=3.14 / Django 6.1 runtime preflight:** Tasks `06-01` and `06-02` (`06.6-06-PLAN.md:14-19,89-99,111-118`) specify the exact two suites documented in `../tabler-test/README.md:64-65` and `../tabler-test/pyproject.toml:34-38` (`example/manage.py test django_tabler crud_views_tabler dashboard catalog customers --parallel 4` and `-m pytest tests -n 4 -q` with `DJANGO_SETTINGS_MODULE = "tests.crispy_tabler.settings"`), gated on a verified `CV_THEME_PYTHON` satisfying `requires-python = ">=3.14"` and `django>=6.1,<6.2` (`../tabler-test/pyproject.toml:4-8,12-15,32`).
- **Clear separation of resolved acquisition from future execution evidence (`H06 — execution evidence`, `A09` signed off):** `06.6-06-PLAN.md:120-131,182-186` does not confuse checkout availability with a completed baseline run: Task `06-02` is a required future execution task, and if a complete Python >=3.14 companion dependency environment (`CV_THEME_PYTHON`) is absent at execution time, `06-02` fails closed and writes a committed `status: halted` `06.6-06-SUMMARY.md` without fabricating baseline passage or installing unaudited packages.

### 3. Concerns
- None (no planning defect). `H06` source acquisition is closed; provisioning/locating `CV_THEME_PYTHON` (Python >=3.14 with Django 6.1 and `crispy-bootstrap5==2026.9` per `../tabler-test/pyproject.toml:4-15,32`) and running `06-02` are properly modeled as fail-closed execution work.

### 4. Suggestions
- None; all suggestions are already incorporated into Tasks `06-01` and `06-02`.

### 5. Risk Assessment
**LOW (Plan Correctness) / MEDIUM (Execution Environment Preflight)** — Source identity is resolved and verified against `../tabler-test` (`885dfc791a150fdc715d6fb34c2e6181d6b92f3c`); execution of `06-02` is cleanly gated on `CV_THEME_PYTHON` preflight.

---

## 06.6-07

### 1. Summary
Plan `06.6-07` (`06.6-07-PLAN.md:1-208`) implements the isolated Tabler HTTP/Chromium acceptance harness (`tests/browser/theme-adoption.cjs`, `tests/browser/theme_adoption_server.py`, `tests/browser/theme-adoption-config.test.cjs`), exercises all eight required scenario families against the isolated `candidate/tabler-test` and `candidate/django-crud-views` sibling copies under `CV_THEME_PYTHON`, and exports/replays `07-tabler-adaptation.patch` (`THEME-01`–`THEME-05`, `D-11`–`D-14`, `D-18`). All Round 1 (`H09`, `H10`, `H11`, `A06`, `A14`) and Round 2 (`C2-A01`, `C2-A04`, `C2-A06`, `H06 — source acquisition`) concerns are resolved (`06.6-07-PLAN.md:81-139,170-204`).

### 2. Strengths
- **Grounded against actual `../tabler-test` settings, template inventory, and `formactions.html` (`H06 — source acquisition`, `C2-A06`, `H11` signed off):** Tasks `07-01` and `07-02` (`06.6-07-PLAN.md:81-89,109-121`) match `../tabler-test/example/config/settings.py:48-51,159-162` (`django_tabler`, `crud_views_tabler` before `crud_views.apps.CrudViewsConfig`, `CRISPY_ALLOWED_TEMPLATE_PACKS = ('crispy_tabler',)`, `CRISPY_TEMPLATE_PACK = 'crispy_tabler'`, `CRUD_VIEWS_EXTENDS = 'crud_views_tabler/page.html'`). They accurately note that `../tabler-test`'s tracked template inventory has neither `crud_views/tags/form.html` nor `view_workflow.action.html` (`C2-A06`: absence with inherited core rendering is success and must not add an override) and that `../tabler-test/src/django_tabler/templates/crispy_tabler/layout/formactions.html:4` already renders `class="form-footer{% if 'form-horizontal' in form_class %} row{% endif %} {{ formactions.css_class|default:'' }} {{ field_class }}"` (preserving the native template when rendered tests pass rather than manufacturing a pack diff).
- **Modal scope aligned with `E251` (`C2-A01` signed off):** Task `07-02` (`06.6-07-PLAN.md:125-128,143`) runs all five form types and parent formset create/update on full pages, scopes modal HTTP/browser acceptance to modal-supported `custom`/`delete`/`workflow` views (`src/crud_views/lib/views/{form,delete}.py`, `src/crud_views_workflow/lib/views.py`), and preserves `CreateView`/`UpdateView` `cv_modal_supported = False` (`src/crud_views/lib/view/base.py:111,168-172`).
- **Explicit port `8145` sharing and non-destructive collision test (`C2-A04`, `A14` signed off):** Task `07-01` (`06.6-07-PLAN.md:91-98`) explicitly dispositions sharing default port `8145` with `tests/browser/presentation.cjs:2-5` under sequential execution, requires an explicit unused port for concurrent runs, and tests that an existing listener on `8145` causes `theme-adoption.cjs` to fail before spawn while leaving the listener alive and responsive afterward.

### 3. Concerns
- None (no planning defect). Execution of `07-01` through `07-03` properly depends on `06-02`'s baseline artifact and `CV_THEME_PYTHON`.

### 4. Suggestions
- None; all suggestions are already incorporated into Tasks `07-01` through `07-03`.

### 5. Risk Assessment
**LOW (Plan Correctness)** — Every companion path, setting, template inventory fact, modal boundary, and port-collision rule is verified against `../tabler-test` (`885dfc7`) and `tests/browser/presentation.cjs`.

---

## 06.6-08

### 1. Summary
Plan `06.6-08` (`06.6-08-PLAN.md:1-172`) publishes executable theme-adoption and migration recipes in `docs/reference/theme.md`, `docs/reference/action_menus.md`, `docs/reference/settings.md`, `docs/migrating-1.0.md`, and `CHANGELOG.md` (`THEME-06`, `D-19`). All Round 1 (`H07`, `H08`, `H09`, `H10`, `A08`, `A11`) and Round 2 (`C2-A02`, `C2-A07`) concerns are resolved (`06.6-08-PLAN.md:77-82,105,109-111,139-169`).

### 2. Strengths
- **Executable standalone library-form wrapper migration and paired `### Breaking` entry (`C2-A02` signed off):** Task `08-01` (`06.6-08-PLAN.md:77-82`) and Task `08-02` (`06.6-08-PLAN.md:109-111`) document that standalone `{% crispy form %}` on a library `CrispyModelForm` now omits the helper-owned `<form>` wrapper while keeping its fields and CSRF token, publish and execute a caller-owned outer `<form>` recipe that retains the crispy-emitted token without adding a second token, and pair the `### Breaking` changelog entry with `docs/migrating-1.0.md`.
- **Golden diff evidence pointer corrected to Plan `01` (`C2-A07` signed off):** Task `08-02` `<read_first>` (`06.6-08-PLAN.md:105`) now points directly to `"the four frame golden diffs from plan 01 / 01-ownership-evidence.md (C2-A07)"`, matching `06.6-01-PLAN.md:154-167`.
- **Synchronized doc-guard assertions (`H07`, `H08`, `A08` signed off):** Task `08-01` (`06.6-08-PLAN.md:86-98`) preserves the single `django`/`html` fence under `### Custom alert frame` (`tests/test1/test_alerts.py:249-255`), the numbered owner-resolution steps (`tests/test1/test_label_mode_docs.py:190-229`), and the tutorial `get_form_actions()` prose (`tests/test1/test_form_button_docs.py:155-163`), while Task `08-02` (`06.6-08-PLAN.md:115-119`) updates `docs/migrating-1.0.md:64` and `test_migration_e108_location_inventory` (`tests/test1/test_label_mode_docs.py:786-800`) together.

### 3. Concerns
- None. All Round 1 and Round 2 (`C2-A02`, `C2-A07`) concerns are resolved.

### 4. Suggestions
- None; all suggestions are already incorporated into Tasks `08-01` and `08-02`.

### 5. Risk Assessment
**LOW** — Documentation changes and executable fence tests are aligned with every existing doc-contract test in `tests/test1/`.

---

## 06.6-09

### 1. Summary
Plan `06.6-09` (`06.6-09-PLAN.md:1-225`) runs the final multi-version Python, crispy-floor (`4.2` and `6.0`), example-project, Vitest, real-browser, companion replay, MkDocs, and Ruff verification gates, updates `CRISPY_FLOOR_TESTS` in `noxfile.py:28-52`, and publishes `06.6-PUBLIC-SURFACE.md`, `06.6-ACCEPTANCE.md`, `09-REGRESSION.md`, and `09-final-evidence.json` (`THEME-01`–`THEME-06`, `D-13`, `D-16`, `D-18`, `D-19`). All Round 1 (`H12`, `A07`, `A09`, `A15`) and Round 2 (`C2-A03`, `H06 — source acquisition`) concerns are resolved (`06.6-09-PLAN.md:94-110,168-171,192-222`).

### 2. Strengths
- **Both cached crispy-floor series (`4.2` and `6.0`) required in final gates (`C2-A03` signed off):** Task `09-01` (`06.6-09-PLAN.md:100-104,170-171`) adds `PYTHONPATH=src:. .nox/crispy_floor-3-12-django-4-2/bin/python -m pytest tests -n 4 -q --deselect tests/test1/test_form_buttons_golden.py::test_filter_form_baseline` alongside `.nox/crispy_floor-3-12-django-6-0/bin/python` and requires `--check-final` to verify both floor results separately while keeping `H12`'s untested current-pack Django 6.0 limit distinct (`06.6-09-PLAN.md:107-113`).
- **Companion monorepo provenance bound and separated from core support matrix (`H06 — source acquisition` signed off):** Task `09-01` (`06.6-09-PLAN.md:94-99,212-222`) binds the theme and pack component paths to `../tabler-test` (`885dfc791a150fdc715d6fb34c2e6181d6b92f3c`) and the sibling core digests from Plan `06`, requires both companion suites and Plan `07`'s browser/replay evidence under `CV_THEME_PYTHON` (Python >=3.14 / Django 6.1), and records that runtime as companion integration evidence without conflating it with the core `4.2`/`5.2`/`6.0` support matrix.
- **Permanent `noxfile.py` floor coverage, example-project gate, and fail-closed halted handoff (`A07`, `A09`, `A15` signed off):** Task `09-01` (`06.6-09-PLAN.md:67-70,79-83,105-107,172`) updates `CRISPY_FLOOR_TESTS` (`noxfile.py:28-52`) with an AST guard test and runs the `examples/bootstrap5` pytest suite (failing closed if any required extra such as `django_ratelimit` is missing), while Task `09-02` (`06.6-09-PLAN.md:133-141`) preserves the committed `status: halted` summary and blocked acceptance contract until all execution and human-check gates complete.

### 3. Concerns
- None (no planning defect). Final acceptance (`--check-final` and `06.6-ACCEPTANCE.md`) properly awaits execution of the baseline, implementation, replay, and human-check tasks.

### 4. Suggestions
- None; all suggestions are already incorporated into Tasks `09-01` and `09-02`.

### 5. Risk Assessment
**LOW (Plan Correctness)** — Verification gates, runtime provenance checks, and Phase 7 handoff artifacts are completely specified and fail closed on any missing execution evidence.

---

## Cycle 3 Resolution Verification & Reviewer Sign-Off

### 1. Explicit Sign-Off of Cycle 2 Actionable Concerns (`C2-A01` – `C2-A07`)

| ID | Prior Severity | Plan(s) | Verification Against Source & Current Tasks | Reviewer Verdict |
|---|---|---|---|---|
| `C2-A01` | MEDIUM | `05`, `07` | `CreateView` (`src/crud_views/lib/views/create.py:12`) and `UpdateView` (`src/crud_views/lib/views/update.py:9`) inherit `cv_modal_supported = False` (`src/crud_views/lib/view/base.py:111`), enforced by `E251` (`src/crud_views/lib/view/base.py:168-172`), whereas `CustomFormView` (`src/crud_views/lib/views/form.py:20,52`), `DeleteView` (`src/crud_views/lib/views/delete.py:55`), and `WorkflowView` (`src/crud_views_workflow/lib/views.py:18`) support modals. Plans `06.6-05-PLAN.md:18,64-66,71-75,85,93-94` and `06.6-07-PLAN.md:125-128,143` now require all 5 full-page paths, scope modal HTTP/browser coverage to supported `custom`/`delete`/`workflow` views, preserve `E251`, and separate template-only frame probes. | **Signed off (Closed)** |
| `C2-A02` | LOW | `01`, `08` | Setting `form_tag = False` on `CrispyFormMixin.helper` (`src/crud_views/lib/crispy/form.py:44-50`) removes the outer `<form>` when a library `CrispyModelForm` is rendered via standalone `{% crispy form %}` while preserving its CSRF token. `06.6-01-PLAN.md:125-129,174-175,192-193` records before/after standalone evidence and tests caller-owned `<form>` wrapping; `06.6-08-PLAN.md:77-82,109-111` publishes an executable caller-owned outer-form recipe and pairs a `### Breaking` changelog entry with `docs/migrating-1.0.md`. | **Signed off (Closed)** |
| `C2-A03` | LOW | `03`, `09` | `noxfile.py:97` parametrizes `crispy_floor` over `["4.2", "6.0"]` and `.nox/crispy_floor-3-12-django-4-2/bin/python` is cached. `06.6-03-PLAN.md:141-148` and `06.6-09-PLAN.md:100-104,170-171` now execute the floor gates on both Django `4.2` and `6.0` and require separate results in `03-pack-bridge-evidence.md`, `--check-final`, `09-REGRESSION.md`, and `06.6-ACCEPTANCE.md`. | **Signed off (Closed)** |
| `C2-A04` | LOW | `07` | `tests/browser/presentation.cjs:2-5` defaults `CV_PRESENTATION_PORT` to `8145` and reserves `8143`/`8144`. `06.6-07-PLAN.md:91-98,195` explicitly documents intentional sequential sharing of default port `8145`, requires an explicit unused port for concurrent runs, and adds a test proving that an occupied `8145` listener fails closed before spawn without killing or disrupting the existing listener. | **Signed off (Closed)** |
| `C2-A05` | LOW | `05` | `06.6-05-PLAN.md:155-158` explicitly defers removing `EventForm.helper` (`examples/bootstrap5/conditional/views.py:132-137`), `PublisherMainForm.helper` / `BookMainForm.helper` (`tests/test1/test_fragment_authorization.py:177-196`), and `BrowserPublisherForm.helper` (`tests/browser/conditional_formsets_server.py:139-143`), documenting why those accepted fixture helpers remain retained while `05-02` removes the two targeted overrides (`tests/test1/app/views_formset.py:44-50`, `examples/bootstrap5/formsets/views.py:36-41`). | **Signed off (Closed by explicit deferral)** |
| `C2-A06` | LOW | `07` | Companion template inventory (`../tabler-test/src/crud_views_tabler/templates/...`) contains neither `crud_views/tags/form.html` nor `view_workflow.action.html`. `06.6-07-PLAN.md:85-88,104-108,143,196` instructs the executor to migrate only actual existing bypass copies and treat absence with inherited core rendering as passing without creating new overrides. | **Signed off (Closed)** |
| `C2-A07` | LOW | `08` | `06.6-08-PLAN.md:105,162` updates Task `08-02` `<read_first>` to read the four frame golden diffs from `plan 01 / 01-ownership-evidence.md`, matching `06.6-01-PLAN.md:154-167`. | **Signed off (Closed)** |

### 2. Explicit Sign-Off of `H06` Source Acquisition

- **`H06 — source acquisition` is CLOSED and SIGNED OFF:** The companion checkout `../tabler-test` at clean HEAD `885dfc791a150fdc715d6fb34c2e6181d6b92f3c` supplies both `src/django_tabler` (the `crispy_tabler` template pack and `django_tabler.crispy` layout helpers, `../tabler-test/README.md:41-47`) and `src/crud_views_tabler` (the Tabler theme, `../tabler-test/src/crud_views_tabler/apps.py:4-31`). Its only sibling path dependency is `django-crud-views = { path = "../django-crud-views", editable = true }` (`../tabler-test/pyproject.toml:18`).
- **Plans `06.6-06`, `06.6-07`, and `06.6-09` accurately reflect the verified companion structure:**
  - `06.6-06-PLAN.md:69-74,80-99` binds `CV_THEME_SOURCE` and `CV_PACK_SOURCE` to `/home/alex/projects/alex/tabler-test` at `885dfc791a150fdc715d6fb34c2e6181d6b92f3c`, constructs isolated sibling `tabler-test/` and `django-crud-views/` copies for baseline (`cb26af4dfef2afb31d774a219abfad1c675cdff1`) and candidate runs, and runs the exact two test suites from `../tabler-test/README.md:64-65` under a verified `CV_THEME_PYTHON` (Python >=3.14 / Django 6.1, separate from the core `4.2`/`5.2`/`6.0` support matrix).
  - `06.6-07-PLAN.md:81-89,104-121` configures `CRISPY_TEMPLATE_PACK = 'crispy_tabler'`, `CRUD_VIEWS_EXTENDS = 'crud_views_tabler/page.html'`, and app ordering from `../tabler-test/example/config/settings.py:48-51,159-162`, notes that `../tabler-test/src/django_tabler/templates/crispy_tabler/layout/formactions.html:4` already renders `{{ formactions.css_class|default:'' }}`, and avoids creating unnecessary template overrides.
  - `06.6-09-PLAN.md:94-99,212-222` binds final verification to the monorepo baseline/replay artifacts while keeping future baseline capture, test execution, and patch replay as mandatory execution gates (`H06 — execution evidence`).
- **No remaining HIGH is a plan defect:** All twelve `H01`–`H12` items are resolved at the planning level (`H01`–`H05` and `H07`–`H12` in Round 1, and `H06` source acquisition in Round 2). Fresh baseline capture (`06-02`), browser/patch execution (`07-01`–`07-03`), and final gate execution (`09-01`–`09-02`) are future execution tasks, not planning defects.

---

## Final List of CURRENT Unresolved Findings

- **CURRENT Unresolved HIGH Concerns:** **0 (None).**
- **CURRENT Actionable MEDIUM / LOW Concerns:** **0 (None).** Every prior suggestion and concern (`H01`–`H12`, `A01`–`A18`, `C2-A01`–`C2-A07`) is either incorporated into concrete task instructions and `<verify>` gates across `06.6-01-PLAN.md` through `06.6-09-PLAN.md` or explicitly dispositioned in the plans' `Review Dispositions Ledger` sections (specifically `C2-A05` in `06.6-05-PLAN.md:155-158` and the `H06 — execution evidence` execution boundary in `06.6-06-PLAN.md:182-186`, `06.6-07-PLAN.md:201-204`, and `06.6-09-PLAN.md:218-222`).

All nine plans (`06.6-01` through `06.6-09`) are converged and ready for execution.
