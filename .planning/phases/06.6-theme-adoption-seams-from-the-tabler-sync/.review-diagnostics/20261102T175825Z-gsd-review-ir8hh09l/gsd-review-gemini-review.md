# Cross-AI Plan Review — Phase 06.6 (Cycle 2 Resolution Verification)

Verified against current repository source and revised plans at commit `1faf42d`. All nine plans (`06.6-01` through `06.6-09`) and their Round 1 disposition ledgers (`H01`–`H12`, `A01`–`A18`) have been audited against the live codebase.

---

## 06.6-01

### 1. Summary
Plan `06.6-01` (`06.6-01-PLAN.md:1-243`) establishes single-form and single-CSRF-token ownership for the create flow (`THEME-01`, `D-01`–`D-04`, `D-16`) by setting `form_tag = False` on `CrispyFormMixin.helper` (`src/crud_views/lib/crispy/form.py:43-50`) and `CrispyDeleteForm.helper` (`src/crud_views/lib/crispy/form.py:136-146`), resolving and adapting `cv_form_helper` once in `cv_render_form` (`src/crud_views/templatetags/crud_views.py:464-466`), and consuming `cv_form_helper` in `src/crud_views/templates/crud_views/tags/form.html:1-7`. All Round 1 concerns assigned to this plan (`H02`, `H03`, `H09`, `H10`, `A01`, `A04`, `A10`) are fully resolved in executable task instructions (`06.6-01-PLAN.md:221-240`).

### 2. Strengths
- **Atomic commit and fixture boundary (`H02`, `H03` signed off):** Tasks `01-01` and `01-02` (`06.6-01-PLAN.md:12-17,93-95,151-164`) co-locate the `cv_render_form` ownership change with updating `_CustomHelperForm` (`tests/test1/test_form_button_checks.py:560-567`) and `_DeleteCustomHelper` (`tests/test1/test_form_button_checks.py:578-585`) to `form_tag=False` and updating the four frame goldens (`tests/test1/golden/form_frame/{create,update,custom_form,delete}.html:1`), verified together by `pytest tests/test1/test_theme_form_ownership.py tests/test1/test_form_frame.py tests/test1/test_form_button_checks.py -n 4 -q` (`06.6-01-PLAN.md:161`). Plan `02` now depends on `06.6-01` in Wave 2 (`06.6-02-PLAN.md:5-6`), eliminating the Wave 1 test breakage.
- **Preserves `Context.dicts` owner-tier resolution (`A10` signed off):** Task `01-01` (`06.6-01-PLAN.md:119-122`) replaces `context.flatten()` in `src/crud_views/templatetags/crud_views.py:466` with `get_template(...).template.render(context)` inside `with context.push(...)` (matching `cv_alert` at `src/crud_views/templatetags/crud_views.py:453-455`), preserving the `Context.dicts` stack required by `_is_response_overlay`, `_cv_helper_tier`, and `_cv_page_tier` in `src/crud_views/lib/crispy/buttons.py:44-77`.
- **Scoped raw HTML event scanner (`H10` signed off):** `assert_owned_form_markup` (`06.6-01-PLAN.md:92,104,139-140`) scans raw `HTMLParser` start/end events prior to DOM repair, rejecting any nested `<form>` (including unclassed `<form>` tags) and counting tokens inside the target owning form while allowing independent sibling POST forms.
- **Explicit copied-template and standalone crispy boundaries (`H09`, `A01`, `A04` signed off):** Task `01-01` (`06.6-01-PLAN.md:111-114,123-129,140-141`) keeps `disable_csrf` local to `cv_render_form` so standalone `{% crispy %}` rendering is unaffected, uses a task-owned archive of `cb26af4dfef2afb31d774a219abfad1c675cdff1`, tests legacy copied inner templates that ignore `cv_form_helper`, and cites `tests/test1/test_form_validation.py` and `tests/test1/test_formsets.py:16-35`.

### 3. Concerns
- **LOW — Bounded helper-adaptation experiment (`A2`) remains an execution gate:** Task `01-01` (`06.6-01-PLAN.md:130-138`) requires testing render-local CSRF suppression across custom `FormHelper` subclasses (`__copy__` returning `self` or raising, `__slots__`, read-only properties, overridden `get_attributes`/`render_layout`, shared layouts) and halting with a design checkpoint if any case mutates caller state or fails to suppress the inner token. This is an intentional, well-bounded execution check rather than a planning defect.

### 4. Suggestions
- When replacing `render_to_string(..., context.flatten())` in `src/crud_views/templatetags/crud_views.py:466` with `template.template.render(context)`, wrap the return value in `mark_safe(...)` exactly as `cv_alert` does at `src/crud_views/templatetags/crud_views.py:455`.

### 5. Risk Assessment
**LOW** — All Round 1 cross-plan test and golden ordering issues (`H02`, `H03`, `H09`, `H10`, `A01`, `A04`, `A10`) are resolved with concrete verification gates.

---

## 06.6-02

### 1. Summary
Plan `06.6-02` (`06.6-02-PLAN.md:1-178`) implements `register_label_mode_defaults(defaults)` in `src/crud_views/lib/view/label_mode.py`, inserting a validated theme layer (`package → theme → project setting`) into `default_label_mode(location)` (`src/crud_views/lib/view/label_mode.py:86-120`) while keeping explicit view/button modes, `override_settings`, `crud_views.E108` (`src/crud_views/lib/settings.py:161-190`), and `viewset.W292` (`src/crud_views/lib/view/buttons.py:435-448,546-584`) aligned (`THEME-02`, `D-05`–`D-07`, `D-15`). All Round 1 concerns (`H02`, `A02`, `A16`, `A17`, `A18`) are resolved (`06.6-02-PLAN.md:158-175`).

### 2. Strengths
- **Non-recursive invalid-setting fallback (`A17` signed off):** Task `02-02` (`06.6-02-PLAN.md:69,120-124`) specifies private `_theme_or_package_default(location)` reading only the theme snapshot and `LABEL_MODE_DEFAULTS` (`src/crud_views/lib/view/label_mode.py:23-25`), replacing the four `LABEL_MODE_DEFAULTS[location]` fallback sites in `src/crud_views/lib/view/label_mode.py:101,107,110,118` without re-reading `CRUD_VIEWS_LABEL_MODE_DEFAULTS` or recursing into `default_label_mode()`.
- **Lock-protected rebind publication and autouse test isolation (`A02`, `A16` signed off):** Task `02-01` (`06.6-02-PLAN.md:69,72,92-99`) validates the entire dictionary against `LOCATIONS` and `is_label_mode()` before rebinding `_THEME_LABEL_MODE_DEFAULTS` under `_theme_defaults_lock`, and adds an `autouse` snapshot/restore-by-rebind fixture in `tests/test1/conftest.py` (alongside `isolate_label_mode_warnings` at `tests/test1/conftest.py:23-33`) verified across consecutive tests in the same worker.
- **Wave 2 dependency and non-form location coverage (`H02`, `A18` signed off):** `06.6-02-PLAN.md:5-6,71,98,130` runs in Wave 2 after `06.6-01` migrates the shared custom-helper fixtures in `tests/test1/test_form_button_checks.py`, and adds `test_card_theme_floor` to verify `"card"` floor resolution and `override_settings` restoration alongside form buttons.

### 3. Concerns
- None. All Round 1 concerns (`H02`, `A02`, `A16`, `A17`, `A18`) are resolved.

### 4. Suggestions
- Keep the edits to `src/crud_views/lib/settings.py:61-74,159-160` strictly to comments/docstrings as planned in `02-02` (`06.6-02-PLAN.md:124-129`) so `crud_views.E108` behavior remains untouched.

### 5. Risk Assessment
**LOW** — Self-contained changes in `src/crud_views/lib/view/label_mode.py` with complete test isolation and non-recursive fallback semantics.

---

## 06.6-03

### 1. Summary
Plan `06.6-03` (`06.6-03-PLAN.md:1-184`) adds `form:actions` and `form:filter-actions` (both defaulting to `""`) to `DEFAULT_BUTTON_CLASSES` (`src/crud_views/lib/button_classes.py:15-113`), wires them into `CrispyFormMixin.get_form_actions` (`src/crud_views/lib/crispy/form.py:55-56`), `CrispyDeleteForm.helper` (`src/crud_views/lib/crispy/form.py:141-144`), and `ListViewFilterFormHelper.get_form_actions` (`src/crud_views/lib/views/list.py:125-133`), and provides a private `_ThemedFormActions` bridge in `src/crud_views/lib/crispy/actions.py` for the `crispy-bootstrap5==2023.10` floor (`THEME-03`, `D-09`, `D-10`, `D-17`). All Round 1 concerns (`H01`, `H04`, `H05`, `H11`) are resolved (`06.6-03-PLAN.md:165-180`).

### 2. Strengths
- **Exact floor-template discriminator (`H01`, `H11` signed off):** Task `03-01` (`06.6-03-PLAN.md:67,76-86`) defines `_use_bootstrap5_floor_bridge(template_pack, resolved_template)` so `crud_views/crispy/bootstrap5_formactions.html` is used only when `template_pack == "bootstrap5"`, the resolved template origin is the installed `crispy_bootstrap5` package's `layout/formactions.html`, and its source matches the audited `2023.10` floor template (`.nox/crispy_floor-3-12-django-6-0/lib/python3.12/site-packages/crispy_bootstrap5/templates/bootstrap5/layout/formactions.html:1-9`). Custom templates and other packs (including a custom pack that ignores `css_class` in `03-03`, `06.6-03-PLAN.md:135-138`) are never overwritten with Bootstrap markup.
- **Render-time class resolution and `deepcopy` safety (`H05` signed off):** Tasks `03-01` and `03-02` (`06.6-03-PLAN.md:90-91,119-124`) store primitive key/base-class state on `_ThemedFormActions` and resolve classes dynamically on each render without mutating or accumulating `self.css_class`, compatible with `ListViewFilterFormHelper._cv_prepare_layout()` (`copy.deepcopy` at `src/crud_views/lib/views/list.py:155`) and cached `self._cv_actions` (`src/crud_views/lib/views/list.py:174-179`).
- **Synchronized 86→88 key inventory and doc count (`H04` signed off):** Plan `03` depends on `06.6-04` (`06.6-03-PLAN.md:6`) and Task `03-02` (`06.6-03-PLAN.md:13,107,111-113,125`) updates `EXPECTED_KEYS` in `tests/test1/test_button_classes.py:21-106` and the count/prose in `docs/reference/buttons.md:151-153` from `86` to `88`, running `tests/test1/test_button_classes.py` in `<verify>`.

### 3. Concerns
- None. All Round 1 concerns (`H01`, `H04`, `H05`, `H11`) are resolved.

### 4. Suggestions
- In `src/crud_views/templates/crud_views/crispy/bootstrap5_formactions.html`, format the outer wrapper class as `class="mb-3{% if formactions_css_class %} {{ formactions_css_class }}{% endif %}"` so when the resolved class is `""`, the floor output is byte-for-byte identical to `.nox/crispy_floor-3-12-django-6-0/lib/python3.12/site-packages/crispy_bootstrap5/templates/bootstrap5/layout/formactions.html:1-9` and satisfies `_action_groups` in `tests/test1/test_crispy_buttons.py:1436-1446`.

### 5. Risk Assessment
**LOW** — The floor discriminator predicates, `deepcopy`-safe dynamic class resolution, and `EXPECTED_KEYS` synchronization are fully specified and verified on both `.nox/tests-3-12-django-5-2` and `.nox/crispy_floor-3-12-django-6-0`.

---

## 06.6-04

### 1. Summary
Plan `06.6-04` (`06.6-04-PLAN.md:1-125`) adds `alert:dismissible` (`"alert-dismissible fade show"`) and `alert:close` (`"btn-close"`) to `DEFAULT_BUTTON_CLASSES` (`src/crud_views/lib/button_classes.py:92-96`) and consumes them in `src/crud_views/templates/crud_views/tags/alert.html:2-5` (`THEME-04`, `D-08`, `D-17`). Both Round 1 concerns (`H04`, `A03`) are resolved (`06.6-04-PLAN.md:108-122`).

### 2. Strengths
- **Synchronized 84→86 key inventory and doc count (`H04` signed off):** Task `04-01` (`06.6-04-PLAN.md:11,60,70-73,85`) adds `tests/test1/test_button_classes.py` and `docs/reference/buttons.md` to `files_modified`, `<files>`, and `<verify>`, updating `EXPECTED_KEYS` (`tests/test1/test_button_classes.py:21-106`) and `docs/reference/buttons.md:151-153` from `84` to `86` in the same commit as the new defaults.
- **Exact omitted-value whitespace contract (`A03` signed off):** Task `04-01` (`06.6-04-PLAN.md:67-70`) resolves `alert:dismissible` into a template variable in `src/crud_views/templates/crud_views/tags/alert.html:2` and emits the leading space separator only when nonempty, ensuring `None`/`""` yields exact `class="alert alert-success"` on the wrapper and `class=""` on the close button while preserving byte-identical default output against `tests/test1/golden/alerts/dismissible.html:1-7`.

### 3. Concerns
- **LOW — Minor wording remnant in `04-01` `<read_first>`:** `06.6-04-PLAN.md:61` says `"Read all three files..."` while `<files>` on line `60` now lists five files (`button_classes.py`, `alert.html`, `test_alerts.py`, `test_button_classes.py`, `buttons.md`). Non-blocking.

### 4. Suggestions
- None required; the executor will read all five files listed in `<files>` (`06.6-04-PLAN.md:60`).

### 5. Risk Assessment
**LOW** — Small, self-contained template and registry update with exact byte-identity and key-inventory guards.

---

## 06.6-05

### 1. Summary
Plan `06.6-05` (`06.6-05-PLAN.md:1-145`) routes `src/crud_views_workflow/templates/crud_views_workflow/view_workflow.action.html:15` through `{% cv_render_form %}`, verifies full-page and modal (`X-CV-Modal: true`) GET/POST/CSRF ownership across all five stock form types plus parent formsets, plain `django.forms.Form` views, and `PolymorphicCreateSelectView`, and removes redundant parent formset helper overrides (`THEME-01`, `D-16`, `D-19`). All Round 1 concerns (`H03`, `H09`, `H10`, `A04`, `A11`, `A12`, `A13`) are resolved (`06.6-05-PLAN.md:123-142`).

### 2. Strengths
- **Workflow template migration and unused tag cleanup (`H09`, `A12` signed off):** Task `05-01` (`06.6-05-PLAN.md:69-72`) replaces `{% crispy form form.helper %}` at `src/crud_views_workflow/templates/crud_views_workflow/view_workflow.action.html:15` with `{% cv_render_form %}` and removes the unused `{% load crispy_forms_tags %}` at line `2`.
- **Parent formset ownership, redundant helper removal, and extension coverage (`A04`, `A11`, `A13` signed off):** Task `05-02` (`06.6-05-PLAN.md:86-101`) extends `tests/test1/test_formsets.py:16-35` to assert single-token ownership on parent formset create/update (page and modal) with enforced-CSRF POST, removes the redundant `h.form_tag = False` helper overrides in `PublisherFormSetForm` (`tests/test1/app/views_formset.py:44-50`) and `QuestionnaireForm` (`examples/bootstrap5/formsets/views.py:36-41`), verifies restored static `W292` visibility (`src/crud_views/lib/view/buttons.py:511-514`), and tests plain no-helper forms and `PolymorphicCreateSelectView` (`src/crud_views_polymorphic/lib/create_select.py:24-28`).
- **Clean golden and scanner reuse (`H03`, `H10` signed off):** Consumes the frame goldens and `assert_owned_form_markup` scanner already landed in Plan `01` (`06.6-05-PLAN.md:54,72-74,97`), testing fixtures with auxiliary sibling action/language forms outside the target content region.

### 3. Concerns
- None. All Round 1 concerns (`H03`, `H09`, `H10`, `A04`, `A11`, `A12`, `A13`) are resolved.

### 4. Suggestions
- When removing `QuestionnaireForm.helper` in `examples/bootstrap5/formsets/views.py:36-41`, also remove `from crispy_forms.helper import FormHelper` at `examples/bootstrap5/formsets/views.py:4` (as instructed by `"clean up only imports made unused"` at `06.6-05-PLAN.md:94`) so `ruff check src tests examples` in Plan `09` passes cleanly.

### 5. Risk Assessment
**LOW** — Well-scoped expansion of Plan `01`'s proven render boundary across stock, workflow, formset, and polymorphic views.

---

## 06.6-06

### 1. Summary
Plan `06.6-06` (`06.6-06-PLAN.md:1-163`) builds the hermetic companion-source provenance and baseline utility (`tests/browser/theme_adoption_sources.py` and `tests/browser/test_theme_adoption_sources.py`) and defines the isolated unmodified companion baseline capture (`06-companion-baseline.json`, `06-COMPANION-SETUP.md`) against archived pre-phase core revision `cb26af4dfef2afb31d774a219abfad1c675cdff1` (`THEME-05`, `D-11`, `D-13`, `D-18`). Round 1 planning concerns `A01`, `A05`, and `A09` are resolved (`06.6-06-PLAN.md:145-160`), while `H06` remains an explicit, fail-closed external prerequisite.

### 2. Strengths
- **Hermetic, import-pure utility and explicit `importlib` loading (`A05` signed off):** Task `06-01` (`06.6-06-PLAN.md:68,88-91,95`) keeps `tests/browser/theme_adoption_sources.py` Django-free and side-effect-free at import time, loads it via `importlib.util.spec_from_file_location` in `tests/browser/test_theme_adoption_sources.py`, and verifies broad pytest collection with `env -u CV_THEME_SOURCE -u CV_PACK_SOURCE -u CV_THEME_CORE_BASE`.
- **Independent archive lifetime and durable halted close-out (`A01`, `A09` signed off):** Task `06-01` (`06.6-06-PLAN.md:86-88`) uses a task-owned temporary archive of `cb26af4dfef2afb31d774a219abfad1c675cdff1` independent of Plan `01`, and Task `06-02` (`06.6-06-PLAN.md:113-117`) mandates writing and committing `06.6-06-SUMMARY.md` with `status: halted`, completed utility commits, failed precondition details, and an exact resume command if companion sources are unavailable.

### 3. Concerns
- **HIGH (External Prerequisite `H06` — Not a Planning Defect):** Authoritative companion sources (`CV_THEME_SOURCE` for the reference Tabler theme and `CV_PACK_SOURCE` for `crispy-tabler`) and a fresh unmodified baseline remain unavailable in the current workspace (`06.6-RESEARCH.md` Environment Availability; `06.6-06-PLAN.md:101,109-117,158-159`). Task `06-02` properly fails closed on its `<precondition>` and halts with an acquisition checkpoint rather than inventing sources or accepting synthetic fixtures.

### 4. Suggestions
- None for plan structure; execution of `06-02` will proceed once `CV_THEME_SOURCE` and `CV_PACK_SOURCE` are supplied, or record the durable `status: halted` summary per `06.6-06-PLAN.md:113-117`.

### 5. Risk Assessment
**HIGH (External Schedule Dependency) / LOW (Plan Correctness)** — The utility design and fail-closed halted-summary protocol (`A01`, `A05`, `A09`) are sound; completion of Task `06-02` is gated on external companion source availability (`H06`).

---

## 06.6-07

### 1. Summary
Plan `06.6-07` (`06.6-07-PLAN.md:1-184`) implements the isolated reference-theme HTTP/Chromium acceptance harness (`tests/browser/theme-adoption.cjs`, `tests/browser/theme_adoption_server.py`, `tests/browser/theme-adoption-config.test.cjs`), exercises all eight required scenario families against isolated copies of the reference Tabler theme and `crispy-tabler` pack, and exports and replays `07-tabler-adaptation.patch` against fresh exact-base copies (`THEME-01`–`THEME-05`, `D-11`–`D-14`, `D-18`). All Round 1 planning concerns (`H09`, `H10`, `H11`, `A06`, `A14`) are resolved (`06.6-07-PLAN.md:164-181`), while execution remains gated on `H06`.

### 2. Strengths
- **Three-task split and dedicated port policy (`A06`, `A14` signed off):** Task `07-01` (`06.6-07-PLAN.md:71-90`) isolates server/config validation and a single `owned-form` create path before Task `07-02` (`06.6-07-PLAN.md:91-124`) expands to all eight case families. `CV_THEME_PORT` defaults to `8145`, rejects reserved ports `8143` (`tests/browser/modal-focus.cjs:21,79`) and `8144` (`tests/browser/conditional-formsets.cjs:28-31`), and probes loopback occupancy before spawning.
- **Conditional isolated pack template adaptation and workflow migration (`H09`, `H11` signed off):** Task `07-02` (`06.6-07-PLAN.md:99-104`) explicitly migrates any copied `view_workflow.action.html` to `cv_render_form`, probes the acquired pack's resolved `layout/formactions.html`, and authorizes adapting that template in the isolated pack copy if it omits `css_class` (preserving native wrappers and default empty bytes), recording the diff in `07-tabler-adaptation.patch` and purpose-level override counts in `07-03` (`06.6-07-PLAN.md:129-138`).
- **Scoped raw-content ownership with sibling forms (`H10` signed off):** Tasks `07-01` and `07-02` (`06.6-07-PLAN.md:20,81-82,109-112`) scope raw start/end tag scanning and native `element.form` / `FormData` checks to the target owning content region alongside auxiliary sibling action/search forms.

### 3. Concerns
- **HIGH (External Prerequisite `H06` — Not a Planning Defect):** Tasks `07-01`, `07-02`, and `07-03` (`06.6-07-PLAN.md:73,93,180`) are gated on `06-companion-baseline.json` passing `--check-baseline` from authoritative companion sources.

### 4. Suggestions
- None; the 3-task decomposition and fail-closed preconditions cleanly bound the browser harness and patch replay.

### 5. Risk Assessment
**HIGH (External Schedule Dependency) / LOW (Plan Correctness)** — All Round 1 planning concerns (`H09`, `H10`, `H11`, `A06`, `A14`) are resolved; execution depends on `06.6-06`'s external companion baseline (`H06`).

---

## 06.6-08

### 1. Summary
Plan `06.6-08` (`06.6-08-PLAN.md:1-155`) updates `docs/reference/theme.md`, `docs/reference/action_menus.md`, `docs/reference/settings.md`, `docs/migrating-1.0.md`, and `CHANGELOG.md` with executable adoption recipes and paired `### Breaking`, `### Fixed`, and `### Added` release notes (`THEME-06`, `D-19`). All Round 1 concerns (`H07`, `H08`, `H09`, `H10`, `A08`, `A11`) are resolved (`06.6-08-PLAN.md:134-152`).

### 2. Strengths
- **Task-synchronized doc assertions (`H07`, `H08` signed off):** Task `08-01` (`06.6-08-PLAN.md:82-87,93`) updates reference prose in `docs/reference/{theme,action_menus,settings}.md` while preserving the exact numbered-step counts enforced by `tests/test1/test_label_mode_docs.py:190-229,709-716` and the single `django`/`html` fence under `### Custom alert frame` in `docs/reference/theme.md:308-323` (`tests/test1/test_alerts.py:249-255`), and leaves `test_migration_e108_location_inventory` (`tests/test1/test_label_mode_docs.py:786-800`) and `docs/migrating-1.0.md` synchronized for Task `08-02` (`06.6-08-PLAN.md:99,107-109,111`).
- **Copied inner/workflow migration recipes and tutorial preservation (`H09`, `H10`, `A08`, `A11` signed off):** Tasks `08-01` and `08-02` (`06.6-08-PLAN.md:72-77,88-92,105-107`) provide executable migration examples for both copied `tags/form.html` (`cv_form_helper`) and copied `view_workflow.action.html` (`cv_render_form`), document the detection boundary for legacy copies and the owning-content scope for single-form/token guarantees, retain valid `get_form_actions()` tutorial/list-view prose verified by `tests/test1/test_form_button_docs.py:155-163`, and document restored static `W292` inspection for subclasses that remove redundant `form_tag=False` helper overrides.

### 3. Concerns
- None. All Round 1 concerns (`H07`, `H08`, `H09`, `H10`, `A08`, `A11`) are resolved.

### 4. Suggestions
- None; task boundaries and `<verify>` commands are fully aligned with existing doc-contract tests.

### 5. Risk Assessment
**LOW** — Executable doc tests and existing structural doc guards (`test_label_mode_docs.py`, `test_alerts.py`, `test_form_button_docs.py`, `test_button_classes.py`, `mkdocs build --strict`) are synchronized at each task boundary.

---

## 06.6-09

### 1. Summary
Plan `06.6-09` (`06.6-09-PLAN.md:1-202`) runs the final multi-version Python, crispy-floor, example-project, Vitest, real-browser, MkDocs, and Ruff verification gates, updates `CRISPY_FLOOR_TESTS` in `noxfile.py:28-52`, and publishes `06.6-PUBLIC-SURFACE.md`, `06.6-ACCEPTANCE.md`, `09-REGRESSION.md`, and `09-final-evidence.json` (`THEME-01`–`THEME-06`, `D-13`, `D-16`, `D-18`, `D-19`). All Round 1 planning concerns (`H12`, `A07`, `A09`, `A15`) are resolved (`06.6-09-PLAN.md:183-199`), while final phase acceptance remains properly gated on `H06` and human visual observations.

### 2. Strengths
- **Permanent `noxfile.py` floor coverage and AST test (`A15` signed off):** Task `09-01` (`06.6-09-PLAN.md:7,67,69,75,79-83`) adds the five new `tests/test1/test_theme_*.py` modules plus `tests/test1/test_alerts.py` and `tests/test1/test_button_classes.py` to `CRISPY_FLOOR_TESTS` in `noxfile.py:28-52` and verifies that selection via AST in `test_floor_selection_covers_theme_modules`.
- **Example-project pytest gate and explicit Django 6.0 current-pack disposition (`A07`, `H12` signed off):** Task `09-01` (`06.6-09-PLAN.md:68,96-105,163`) runs `PYTHONPATH=src:examples/bootstrap5 DJANGO_SETTINGS_MODULE=project.settings .nox/tests-3-12-django-5-2/bin/python -m pytest -c examples/bootstrap5/pytest.ini examples/bootstrap5 -n 4 -q` and requires its result in `--check-final`, while explicitly recording current-pack Django 6.0 as an untested matrix combination (unless an already-cached runtime is present) rather than conflating it with `.nox/crispy_floor-3-12-django-6-0`.
- **Durable blocked/halted reporting (`A09` signed off):** Task `09-02` (`06.6-09-PLAN.md:125-131`) specifies writing and committing `06.6-09-SUMMARY.md` with `status: halted` and publishing partial/unaccepted `06.6-PUBLIC-SURFACE.md` and blocked `06.6-ACCEPTANCE.md` if upstream companion evidence (`H06`) or human visual observations remain pending.

### 3. Concerns
- **HIGH (External Prerequisite `H06` — Not a Planning Defect):** Final phase acceptance (`--check-final` and `06.6-ACCEPTANCE.md` at `06.6-09-PLAN.md:24,107-108,124-133,198`) remains blocked until authoritative companion sources, fresh baseline/replay (`06.6-06`/`06.6-07`), and human visual observations are supplied.

### 4. Suggestions
- None; `--check-final` and the halted-summary protocol accurately distinguish automated core verification from pending external companion and human acceptance.

### 5. Risk Assessment
**HIGH (External Schedule Dependency for Final Acceptance) / LOW (Plan Correctness)** — All Round 1 planning concerns (`H12`, `A07`, `A09`, `A15`) are resolved.

---

## Cross-Plan Comparison & Consensus Summary

### Round 1 Concern Resolution Sign-Off (`1faf42d`)
All **29 planning concerns** from Round 1 (**11 HIGH** and **18 actionable non-HIGH**) have been verified resolved in the current plans:
- **Signed off HIGH planning concerns (11/11):** `H01` (`06.6-03-PLAN.md:67,76-86`), `H02` (`06.6-01-PLAN.md:12,93-95,151-164`; `06.6-02-PLAN.md:5-6,130`), `H03` (`06.6-01-PLAN.md:14-17,93-95,151-164`; `06.6-05-PLAN.md:54,97`), `H04` (`06.6-04-PLAN.md:11,60,70-73`; `06.6-03-PLAN.md:13,107,111-113`), `H05` (`06.6-03-PLAN.md:90-91,119-124`), `H07` (`06.6-08-PLAN.md:84-85,99,107-111`), `H08` (`06.6-08-PLAN.md:83-87,93`), `H09` (`06.6-01-PLAN.md:123-129`; `06.6-05-PLAN.md:69-72`; `06.6-07-PLAN.md:99`; `06.6-08-PLAN.md:73-76,106-107`), `H10` (`06.6-01-PLAN.md:92,104,139-140`; `06.6-05-PLAN.md:72-74`; `06.6-07-PLAN.md:81-82,109-112`; `06.6-08-PLAN.md:76-77`), `H11` (`06.6-03-PLAN.md:135-138`; `06.6-07-PLAN.md:99-104,129-138`), and `H12` (`06.6-09-PLAN.md:68,100-105`).
- **Signed off non-HIGH planning concerns (18/18):** `A01`–`A18` are each incorporated into executable task actions and `<verify>` gates across Plans `01`–`09`.
- **Remaining external prerequisite (`H06` — 1 item, non-defect):** Authoritative reference-theme (`CV_THEME_SOURCE`) and pack (`CV_PACK_SOURCE`) checkouts are not present on disk. Plans `06`, `07`, and `09` properly gate companion baseline, browser replay, and final phase acceptance behind fail-closed preconditions and durable `status: halted` summaries without inventing sources or accepting synthetic substitutes.

### Overall Risk Assessment: **LOW (Planning & Core Implementation) / HIGH (External Companion Source Availability `H06`)**
The nine plans are internally consistent, properly sequenced across Waves 1–4 with zero same-wave file conflicts, grounded in the live repository seams, and ready for execution.
