# Cross-AI Plan Review — Phase 06.6 (Cycle 4 Resolution Verification at HEAD `0d7c377`)

Verified read-only against the current repository checkout at HEAD `0d7c377`, prior Cycle 3 review `ef632e7` (`.planning/phases/06.6-theme-adoption-seams-from-the-tabler-sync/06.6-REVIEWS.md:1-820`), the `06.6-RESEARCH.md` source and runtime availability addenda, and the embedded companion sources from `../tabler-test` at pinned commit `885dfc791a150fdc715d6fb34c2e6181d6b92f3c`.

---

## 06.6-01

### 1. Summary
Plan `06.6-01` (`06.6-01-PLAN.md:1-262`) establishes the single-form and single-CSRF-token render boundary (`THEME-01`, `D-01`–`D-04`, `D-16`) on the create flow before expanding to other views. It sets `form_tag = False` on `CrispyFormMixin.helper` (`src/crud_views/lib/crispy/form.py:43-50`) and `CrispyDeleteForm.helper` (`src/crud_views/lib/crispy/form.py:136-146`), introduces `_prepare_form_helper(form)` and `_diagnose_form_wrapper(helper)` behind `cv_render_form` (`src/crud_views/templatetags/crud_views.py:464-466`), passes `cv_form_helper` into `src/crud_views/templates/crud_views/tags/form.html:1-7` using `context.push` rather than `context.flatten()`, and updates the four frame goldens (`tests/test1/golden/form_frame/{create,update,custom_form,delete}.html:1`) and two custom-helper test fixtures (`tests/test1/test_form_button_checks.py:560-585`) in the same atomic commit (`06.6-01-PLAN.md:95-98,154-167`).

### 2. Strengths
- **Grounded single-helper selection and context-tier preservation (`A10`):** `src/crud_views/templates/crud_views/view_create.content.html:5-11` already owns the outer `<form class="cv-form" method="post" action="{{ request.get_full_path }}" enctype="multipart/form-data" novalidate>` and `{% csrf_token %}`, while `src/crud_views/templates/crud_views/tags/form.html:3-6` evaluates `form.helper` twice (`{% if form.helper %}` and `{% crispy form form.helper %}`), allocating two `FormHelper()` instances (`src/crud_views/lib/crispy/form.py:44-50`). Switching `cv_render_form` (`src/crud_views/templatetags/crud_views.py:464-466`) to `get_template(...).template.render(context)` with `with context.push(cv_form_helper=...)`—matching `cv_alert` at `src/crud_views/templatetags/crud_views.py:453-455`—preserves `Context.dicts` for `_is_response_overlay`, `_cv_helper_tier`, and `_cv_page_tier` (`src/crud_views/lib/crispy/buttons.py:44-77`).
- **Atomic fixture and golden migration (`H02`, `H03`):** Tasks `01-01` and `01-02` (`06.6-01-PLAN.md:95-98,154-167`) update `_CustomHelperForm` and `_DeleteCustomHelper` (`tests/test1/test_form_button_checks.py:560-585`) to `form_tag = False` and remove the nested `<form method="post" ><input type="hidden" name="csrfmiddlewaretoken" value="CSRF">` from `tests/test1/golden/form_frame/{create,update,custom_form,delete}.html:1` in one green commit.
- **Standalone library-form wrapper change explicitly tested (`C2-A02`):** Tasks `01-01` and `01-03` (`06.6-01-PLAN.md:125-129,174-175,192-193`) distinguish standalone `{% crispy form %}` on a `CrispyModelForm` (`src/crud_views/lib/crispy/form.py:87`, where `form_tag = False` removes the helper-owned `<form>` wrapper while keeping fields and the crispy CSRF token) from `cv_render_form` (where the page owns `<form>` and CSRF and the inner token is suppressed).
- **Raw `HTMLParser` ownership scanner (`H10`):** `assert_owned_form_markup` (`06.6-01-PLAN.md:92-94,142-144`) inspects raw start/end tag events prior to browser DOM repair, catching unclassed nested `<form>` tags while allowing sibling POST forms outside the owning form.

### 3. Concerns
- None. All Round 1 (`H02`, `H03`, `H09`, `H10`, `A01`, `A04`, `A10`) and Round 2 (`C2-A02`) concerns are resolved in the plan tasks.

### 4. Suggestions
- None; all prior suggestions are incorporated into Tasks `01-01`–`01-03`.

### 5. Risk Assessment
**LOW** — The create ownership seam, render-local CSRF suppression experiment with fail-closed design checkpoint (`06.6-01-PLAN.md:134-141`), and atomic golden/fixture updates are directly verified against current source.

---

## 06.6-02

### 1. Summary
Plan `06.6-02` (`06.6-02-PLAN.md:1-179`) adds `register_label_mode_defaults(defaults)` to `src/crud_views/lib/view/label_mode.py`, inserting the validated theme floor layer (`package → theme → project setting`) into `default_label_mode(location)` (`src/crud_views/lib/view/label_mode.py:86-120`) while keeping explicit button/view modes, owner maps, `crud_views.E108` (`src/crud_views/lib/settings.py:161-190`), and `viewset.W292` (`src/crud_views/lib/view/buttons.py:395-448,546-584`) authoritative (`THEME-02`, `D-05`–`D-07`, `D-15`). Round 3 adds explicit verification of the composed two-level fallback (`C3-A03`, `06.6-02-PLAN.md:106-107,118-125,164-175`).

### 2. Strengths
- **Two-level composed fallback explicitly verified (`C3-A03` signed off):** In `src/crud_views/lib/view/label_mode.py:122-146`, `form_label_mode(mapping, kind)` handles a non-`dict` owner map (`:129-135`) or invalid mapped value (`:139-146`) by calling `_invalid_label_mode(..., "form", ..., lambda: default_label_mode("form"))`. In `_invalid_label_mode` (`src/crud_views/lib/view/label_mode.py:63-84`), strict mode raises `ValueError` at `:74` before invoking `fallback()`, whereas non-strict mode resolves `fallback()` at `:75` outside `_warned_lock` (`:77-80`), which calls `default_label_mode("form")` (`:86-120`) and, on a malformed `CRUD_VIEWS_LABEL_MODE_DEFAULTS`, re-enters `_invalid_label_mode` with `lambda: _theme_or_package_default("form")`. Task `02-02` (`06.6-02-PLAN.md:106-107,118-125,137`) now explicitly tests this composed non-strict and strict path with distinct malformed values, verifying that `"both"` is returned and rendered, both warnings log `"both"`, deduplication holds without recursion or deadlock, and strict mode raises at the owner without entering settings fallback.
- **Atomic registration under lock and autouse isolation (`A02`, `A16`, `A18`):** Task `02-01` (`06.6-02-PLAN.md:69-72,89-99`) validates the entire dictionary against `LOCATIONS` and `is_label_mode()` (`src/crud_views/lib/view/label_mode.py:35-36`) before rebinding `_THEME_LABEL_MODE_DEFAULTS` under `_theme_defaults_lock`, and isolates tests via an `autouse` fixture in `tests/test1/conftest.py`.
- **Static `W292` reach preserved:** Both `cv_icon_mode_checks` (`src/crud_views/lib/view/buttons.py:435`) and `cv_form_icon_mode_checks` (`src/crud_views/lib/view/buttons.py:570`) already resolve through `cls.cv_get_action_label_mode` → `default_label_mode` / `form_label_mode`, so Task `02-02` (`06.6-02-PLAN.md:127-131`) tests effective theme floors without instantiating request-dependent forms.

### 3. Concerns
- None. All Round 1 (`H02`, `A02`, `A16`, `A17`, `A18`) and Round 3 (`C3-A03`) concerns are resolved.

### 4. Suggestions
- None; all suggestions are incorporated into Tasks `02-01` and `02-02`.

### 5. Risk Assessment
**LOW** — The call chain in `src/crud_views/lib/view/label_mode.py:63-146` directly supports both single-level and composed two-level fallback without lock re-entrancy hazards.

---

## 06.6-03

### 1. Summary
Plan `06.6-03` (`06.6-03-PLAN.md:1-203`) adds `form:actions` and `form:filter-actions` (both `""`) to `DEFAULT_BUTTON_CLASSES` (`src/crud_views/lib/button_classes.py:15-113`), wires them into `CrispyFormMixin.get_form_actions` (`src/crud_views/lib/crispy/form.py:55-56`), `CrispyDeleteForm.helper` (`src/crud_views/lib/crispy/form.py:141-144`), and `ListViewFilterFormHelper.get_form_actions` (`src/crud_views/lib/views/list.py:125-133`), and introduces a private `_ThemedFormActions` bridge in `src/crud_views/lib/crispy/actions.py` with `src/crud_views/templates/crud_views/crispy/bootstrap5_formactions.html` for the `crispy-bootstrap5==2023.10` floor (`THEME-03`, `D-09`, `D-10`, `D-17`).

### 2. Strengths
- **Scoped floor-pack bridge (`H01`, `H11`):** Task `03-01` (`06.6-03-PLAN.md:67,76-89`) restricts the bridge to `template_pack == "bootstrap5"`, resolved template origin inside the installed `crispy_bootstrap5` package's `layout/formactions.html`, and exact whole-file source equality with the audited `2023.10` floor template, delegating unchanged for all other packs and custom templates (including `crispy_tabler`).
- **Dynamic per-render class resolution on cached filter actions (`H05`):** `ListViewFilterFormHelper.render_layout` (`src/crud_views/lib/views/list.py:172-180`) caches `self._cv_actions` per prepared layout (`_cv_prepare_layout` at `:139-165` uses `copy.deepcopy` at `:155`). Task `03-02` (`06.6-03-PLAN.md:111-125`) stores primitive key/base-class state on `_ThemedFormActions` and resolves classes per render without mutating or accumulating `css_class`.
- **Synchronized `86 → 88` key inventory and dual-series floor gates (`H04`, `C2-A03`):** Task `03-02` (`06.6-03-PLAN.md:112-115`) updates `EXPECTED_KEYS` (`tests/test1/test_button_classes.py:21-106`) and `docs/reference/buttons.md:151` from `86` (after Plan `04`) to `88`, and Task `03-03` (`06.6-03-PLAN.md:141-148`) runs the floor verification on both `.nox/crispy_floor-3-12-django-6-0/bin/python` and `.nox/crispy_floor-3-12-django-4-2/bin/python` (`noxfile.py:97`).

### 3. Concerns
- None. All Round 1 (`H01`, `H04`, `H05`, `H11`) and Round 2 (`C2-A03`) concerns are resolved.

### 4. Suggestions
- None; all suggestions are incorporated into Tasks `03-01`–`03-03`.

### 5. Risk Assessment
**LOW** — The three action-group constructors, `ListViewFilterFormHelper` caching lifecycle, W362 grammar (`src/crud_views/lib/button_classes.py:240,262-265`), and dual-floor nox environments are verified in source.

---

## 06.6-04

### 1. Summary
Plan `06.6-04` (`06.6-04-PLAN.md:1-125`) adds `alert:dismissible` (`"alert-dismissible fade show"`) and `alert:close` (`"btn-close"`) to `DEFAULT_BUTTON_CLASSES` (`src/crud_views/lib/button_classes.py:92-96`) and consumes them in `src/crud_views/templates/crud_views/tags/alert.html:2-5` while preserving byte-identical default output (`tests/test1/golden/alerts/dismissible.html:1-7`), accessible close labels, and `data-cv-alert-dismiss` behavior (`THEME-04`, `D-08`, `D-17`).

### 2. Strengths
- **Byte-identical default markup and clean omitted-value spacing (`A03`):** `src/crud_views/templates/crud_views/tags/alert.html:2,5` currently hardcodes ` alert-dismissible fade show` and `class="btn-close"`. Task `04-01` (`06.6-04-PLAN.md:67-70`) resolves `alert:dismissible` into a template variable and emits the leading space separator only when nonempty, producing exact `class="alert alert-success"` on the wrapper and `class=""` on the close button when set to `""` or `None`, and preserving `tests/test1/golden/alerts/dismissible.html:1-7` under defaults.
- **Atomic `84 → 86` key-inventory update and W362 grammar (`H04`):** Task `04-01` (`06.6-04-PLAN.md:60,70-73`) updates `EXPECTED_KEYS` in `tests/test1/test_button_classes.py:105` and `docs/reference/buttons.md:151` from `84` to `86` in the same commit as `DEFAULT_BUTTON_CLASSES`. Because `"alert"` is not in `VARIANT_LOCATIONS` (`src/crud_views/lib/button_classes.py:239`) or `"form"` (`:263`), `_action_key_parts` (`:251-266`) returns `None` and `button_class_check_messages` (`:328-346`) automatically flags `alert:close:icon` and `alert:dismissible:both` with `crud_views.W362`.

### 3. Concerns
- None. All Round 1 concerns (`H04`, `A03`) are resolved.

### 4. Suggestions
- None; all suggestions are incorporated into Tasks `04-01` and `04-02`.

### 5. Risk Assessment
**LOW** — Leaf-only template update with exact golden and W362 coverage.

---

## 06.6-05

### 1. Summary
Plan `06.6-05` (`06.6-05-PLAN.md:1-175`) migrates `src/crud_views_workflow/templates/crud_views_workflow/view_workflow.action.html:15` from `{% crispy form form.helper %}` to `{% cv_render_form %}`, verifies full-page GET/POST/CSRF ownership across all five stock form types (create, update, custom form, delete, workflow) plus parent formset create/update, plain `django.forms.Form` views, and `PolymorphicCreateSelectView`, scopes modal (`X-CV-Modal: true`) HTTP coverage to modal-supported views (`CustomFormView`, `DeleteView`, `WorkflowView`), and removes the two targeted redundant `form_tag=False` overrides in `tests/test1/app/views_formset.py:44-50` and `examples/bootstrap5/formsets/views.py:36-41` (`THEME-01`, `D-16`, `D-19`). Round 3 explicitly binds and separates the inherited workflow modal body from the full-page workflow template branches (`C3-A01`, `06.6-05-PLAN.md:19,68-69,75-84,102,163-173`).

### 2. Strengths
- **Substantive workflow modal vs full-page template invariant verified (`C3-A01` signed off):** In `src/crud_views_workflow/lib/views.py:18-28`, `WorkflowView(CustomFormView)` overrides `template_name = "crud_views_workflow/view_workflow.html"` (`:27`)—which includes `crud_views_workflow/view_workflow.content.html` (`src/crud_views_workflow/templates/crud_views_workflow/view_workflow.html:4`) and `crud_views_workflow/view_workflow.action.html` (`src/crud_views_workflow/templates/crud_views_workflow/view_workflow.content.html:5`)—but intentionally inherits `cv_content_template = "crud_views/view_custom_form.content.html"` from `CustomFormView` (`src/crud_views/lib/views/form.py:19`). On a modal request (`X-CV-Modal: true`), `CrudView.get_template_names()` (`src/crud_views/lib/view/base.py:222-225`) renders `crud_views/modal/content.html`, which includes `view.cv_content_template` (`src/crud_views/templates/crud_views/modal/content.html:8`). Task `05-01` (`06.6-05-PLAN.md:68-69,75-84,102`) preserves that inherited modal body without overriding `cv_content_template`, asserts included template names and origins for modal GET/invalid POST (confirming `view_workflow.content.html` and `view_workflow.action.html` are not rendered in modal mode and testing inherited no-choice modal form rendering + refused transition), and separately tests full-page workflow GET/invalid POST with choices (`has_workflow_choices=True`) and no-choice omission (`has_workflow_choices=False`, `src/crud_views_workflow/templates/crud_views_workflow/view_workflow.action.html:6-19`).
- **Modal support boundary aligned with `E251` (`C2-A01`):** `CreateView` and `UpdateView` inherit `cv_modal_supported = False` (`src/crud_views/lib/view/base.py:111`) and are checked by `E251` (`:168-172`); `06.6-05-PLAN.md:66-67,85-88` preserves that boundary and keeps template-only frame probes separate from modal HTTP tests.
- **Targeted parent-formset helper cleanup restores static `W292` reach (`A04`, `A11`, `C2-A05`):** Removing the redundant `form_tag = False` property overrides on `PublisherFormSetForm.helper` (`tests/test1/app/views_formset.py:44-50`) and `QuestionnaireForm.helper` (`examples/bootstrap5/formsets/views.py:36-41`) restores `_inherits(form_class, "helper", CrispyFormMixin)` in `_static_form_controls` (`src/crud_views/lib/view/buttons.py:512`), while other fixture helpers remain explicitly deferred in the ledger (`06.6-05-PLAN.md:155-161`).

### 3. Concerns
- None. All Round 1 (`H03`, `H09`, `H10`, `A04`, `A11`, `A12`, `A13`), Round 2 (`C2-A01`, `C2-A05`), and Round 3 (`C3-A01`) concerns are resolved.

### 4. Suggestions
- None; all suggestions are incorporated into Tasks `05-01` and `05-02`.

### 5. Risk Assessment
**LOW** — Both the full-page workflow template chain (`view_workflow.html` → `view_workflow.content.html` → `view_workflow.action.html`) and the modal template chain (`modal/content.html` → `view_custom_form.content.html`) are accurately traced and separately verified.

---

## 06.6-06

### 1. Summary
Plan `06.6-06` (`06.6-06-PLAN.md:1-199`) creates the Django-free companion provenance, baseline capture, and replay verification utility (`tests/browser/theme_adoption_sources.py` and `tests/browser/test_theme_adoption_sources.py`) and captures the unmodified baseline (`06-companion-baseline.json`, `06-COMPANION-SETUP.md`) from the supplied `../tabler-test` monorepo at `885dfc791a150fdc715d6fb34c2e6181d6b92f3c` against archived pre-phase core commit `cb26af4dfef2afb31d774a219abfad1c675cdff1` (`THEME-05`, `D-11`, `D-13`, `D-18`). Round 3 defines the purpose-based D-18 counting contract, separates data-only registration adoption, inventories the four shadowing templates (`C3-A02`), and incorporates the verified `../tabler-test/.venv` runtime (`06.6-06-PLAN.md:64-78,84-119,191-197`).

### 2. Strengths
- **Purpose-based D-18 override accounting and explicit shadow inventory (`C3-A02` signed off):** `06.6-06-PLAN.md:71-78,108-119` defines D-18's counting unit as distinct required customization purposes with stable purpose IDs and implementing paths, explicitly separating data-only calls to public registration APIs (`register_label_mode_defaults`, `register_button_classes`, `register_icons` as in `../tabler-test/src/crud_views_tabler/apps.py:24-31`) into adoption entries excluded from required-override counts unless they invoke custom callbacks/helpers/templates. Task `06-01` explicitly inventories the four actual shadowing templates in `../tabler-test/src/crud_views_tabler/templates/crud_views/`—`tags/alert.html` (`:1-18`), `snippets/form_frame.html` (`:1-6`), `tags/list_filter.html` (`:1-11`), and `tags/list_filter.inner.html` (`:1-14`)—and tests positive and negative purpose/adoption comparisons (including renamed paths retaining purpose IDs and rejecting relabeled templates/helpers) in `tests/browser/test_theme_adoption_sources.py`.
- **Verified companion runtime and private user `settings.py` preservation:** `06.6-06-PLAN.md:64-68,84-99` defaults `CV_THEME_PYTHON` to `/home/alex/projects/alex/tabler-test/.venv/bin/python` (verified Python 3.14.7, Django 6.1.2, crispy-forms 2.7, crispy-bootstrap5 2026.9 per `../tabler-test/pyproject.toml:4-18,30-33`), archives tracked sources at pinned commit `885dfc791a150fdc715d6fb34c2e6181d6b92f3c` into isolated `baseline/` and `candidate/` sibling trees so the user's private modified `example/config/settings.py` is never read into isolated fixtures or exposed, overrides the editable `../django-crud-views` import (`../tabler-test/pyproject.toml:18`) with explicit isolated `PYTHONPATH`, and retains the fail-closed `pytest-xdist` preflight and `status: halted` summary contract (`A09`).

### 3. Concerns
- None. All Round 1 (`A01`, `A05`, `A09`), Round 2 (`H06 — source acquisition`), and Round 3 (`C3-A02` and runtime availability update) concerns are resolved.

### 4. Suggestions
- None; all suggestions are incorporated into Tasks `06-01` and `06-02`.

### 5. Risk Assessment
**LOW** — Source identity (`885dfc791a150fdc715d6fb34c2e6181d6b92f3c`), runtime path (`../tabler-test/.venv/bin/python`), private dirty-file preservation, and purpose-vs-adoption override accounting are fully specified.

---

## 06.6-07

### 1. Summary
Plan `06.6-07` (`06.6-07-PLAN.md:1-226`) builds the isolated Tabler HTTP/Chromium acceptance harness (`tests/browser/theme-adoption.cjs`, `tests/browser/theme_adoption_server.py`, `tests/browser/theme-adoption-config.test.cjs`), runs all eight required scenario families against the isolated `candidate/tabler-test` and `candidate/django-crud-views` sibling copies under `CV_THEME_PYTHON`, and exports/replays `07-tabler-adaptation.patch` (`THEME-01`–`THEME-05`, `D-11`–`D-14`, `D-18`). Round 3 binds separate template-origin records for modal vs full-page workflow (`C3-A01`) and specifies exact handling of the four companion shadow templates (`C3-A02`, `06.6-07-PLAN.md:94-98,113-126,139-149,168-174,218-223`).

### 2. Strengths
- **Concrete adaptation and verification of all four companion shadow templates (`C3-A02` signed off):**
  - `../tabler-test/src/crud_views_tabler/templates/crud_views/tags/alert.html:7,17` currently hardcodes `alert-dismissible fade show`, `class="btn-close"`, and `data-bs-dismiss="alert"` (also asserted in `../tabler-test/src/crud_views_tabler/tests.py:258-285,301-310`). Task `07-02` (`06.6-07-PLAN.md:113-121`) adapts that isolated copy to consume `{% cv_button_class "alert" "dismissible" %}`, `{% cv_button_class "alert" "close" %}`, and `data-cv-alert-dismiss` while preserving Tabler's `.alert-icon`, `.alert-heading`, and `.alert-description` layout (`../tabler-test/src/crud_views_tabler/templates/crud_views/tags/alert.html:8-16`).
  - `../tabler-test/src/crud_views_tabler/templates/crud_views/snippets/form_frame.html:1-6` wraps `{% block cv_form_body %}` in `<div class="card"><div class="card-body">` only when `request.headers.x_cv_modal != "true"` (tested at `../tabler-test/src/crud_views_tabler/tests.py:241-256`); Tasks `07-01` and `07-02` (`06.6-07-PLAN.md:94-98,123-124`) verify its resolved origin and preserve it with its existing layout purpose ID.
  - `../tabler-test/src/crud_views_tabler/templates/crud_views/tags/list_filter.html:1-11` and `list_filter.inner.html:1-14` own `<form id="filter-form" method="get">` (`:10`) and call `{% crispy filter.form filter.form.helper %}` (`:11`); Task `07-02` (`06.6-07-PLAN.md:121-123`) verifies that `form:filter-actions` reaches `../tabler-test/src/django_tabler/templates/crispy_tabler/layout/formactions.html` while preserving the GET owner, collapse/pinned structure, and hidden inputs.
  - Task `07-03` (`06.6-07-PLAN.md:168-174`) reuses Plan `06`'s purpose-based counting rule so adding `register_label_mode_defaults` in `crud_views_tabler` is recorded as an adoption entry rather than override growth.
- **Distinct server-observed template provenance for workflow modal vs full-page (`C3-A01` signed off):** Task `07-02` (`06.6-07-PLAN.md:139-149,161`) records actual server template-render observations in `07-browser-results.json`, proving that workflow modal GET/422/no-choice requests render the inherited `crud_views/view_custom_form.content.html` body while full-page workflow requests render `crud_views_workflow/view_workflow.content.html` and `view_workflow.action.html` for both actionable (`has_workflow_choices=True`) and omitted (`has_workflow_choices=False`) states.

### 3. Concerns
- None. All Round 1 (`H09`, `H10`, `H11`, `A06`, `A14`), Round 2 (`C2-A01`, `C2-A04`, `C2-A06`, `H06 — source acquisition`), and Round 3 (`C3-A01`, `C3-A02`) concerns are resolved.

### 4. Suggestions
- None; all suggestions are incorporated into Tasks `07-01`–`07-03`.

### 5. Risk Assessment
**LOW** — Every template path, button/icon registration (`../tabler-test/src/crud_views_tabler/{apps,buttons,icons}.py`), shadow template (`tags/alert.html`, `snippets/form_frame.html`, `tags/list_filter*.html`), and workflow modal/page split matches the verified `../tabler-test` (`885dfc7`) and core sources.

---

## 06.6-08

### 1. Summary
Plan `06.6-08` (`06.6-08-PLAN.md:1-176`) updates `docs/reference/theme.md`, `docs/reference/action_menus.md`, `docs/reference/settings.md`, `docs/migrating-1.0.md`, and `CHANGELOG.md`, and adds executable documentation tests in `tests/test1/test_theme_adoption_docs.py` alongside updated assertions in `tests/test1/test_label_mode_docs.py` (`THEME-06`, `D-19`).

### 2. Strengths
- **Synchronized doc-guard updates (`H07`, `H08`, `A08`):** Task `08-01` (`06.6-08-PLAN.md:86-98`) keeps a single `django`/`html` code fence under `### Custom alert frame` in `docs/reference/theme.md:308-321` (guarded by `tests/test1/test_alerts.py:249-255`), preserves the numbered owner-resolution structure in `docs/reference/action_menus.md` (`tests/test1/test_label_mode_docs.py:180-229`), and retains the tutorial `get_form_actions()` recipes (`tests/test1/test_form_button_docs.py:155-163`). Task `08-02` (`06.6-08-PLAN.md:115-119`) updates `docs/migrating-1.0.md:64` (`"falls back to its package floor"`) and `test_migration_e108_location_inventory` (`tests/test1/test_label_mode_docs.py:786-800`) together in one commit.
- **Executable standalone library-form wrapper migration (`C2-A02`, `C2-A07`):** Tasks `08-01` and `08-02` (`06.6-08-PLAN.md:77-82,105,109-111`) read the four frame golden diffs from Plan `01` (`01-ownership-evidence.md`), publish and execute a caller-owned outer `<form>` recipe for standalone `{% crispy form %}` on a `CrispyModelForm`, and pair the `### Breaking` changelog entry with `docs/migrating-1.0.md`.

### 3. Concerns
- None. All Round 1 (`H07`, `H08`, `H09`, `H10`, `A08`, `A11`) and Round 2 (`C2-A02`, `C2-A07`) concerns are resolved.

### 4. Suggestions
- None; all suggestions are incorporated into Tasks `08-01` and `08-02`.

### 5. Risk Assessment
**LOW** — All doc fence extractors and paragraph guards in `tests/test1/` are accounted for.

---

## 06.6-09

### 1. Summary
Plan `06.6-09` (`06.6-09-PLAN.md:1-230`) executes the final multi-series Python (`4.2` and `5.2`), crispy-floor (`4.2` and `6.0`), `examples/bootstrap5`, Vitest, browser preservation, companion replay, MkDocs, and Ruff gates, updates `CRISPY_FLOOR_TESTS` in `noxfile.py:28-52`, and writes `09-final-evidence.json`, `09-REGRESSION.md`, `06.6-PUBLIC-SURFACE.md`, `06.6-ACCEPTANCE.md`, and `06.6-VALIDATION.md` (`THEME-01`–`THEME-06`, `D-13`, `D-16`, `D-18`, `D-19`). Round 3 extends `--check-final` to enforce distinct modal vs full-page workflow template and branch records (`C3-A01`, `06.6-09-PLAN.md:78-85,123,221-229`).

### 2. Strengths
- **Fail-closed `--check-final` validation of workflow modal vs full-page branch records (`C3-A01` signed off):** Task `09-01` (`06.6-09-PLAN.md:78-85,123`) requires `--check-final` in `tests/browser/theme_adoption_sources.py` to verify Plan `07`'s distinct workflow records—checking `route`/`mode`, `has_workflow_choices`, logical included templates, resolved origins (`crud_views/view_custom_form.content.html` for modal GET/422/no-choice vs `crud_views_workflow/view_workflow.content.html` and `view_workflow.action.html` for full-page actionable and no-choice omission), and passing branch assertions—and tests negative missing/swapped-origin fixtures and a complete positive fixture in `tests/browser/test_theme_adoption_sources.py`.
- **Complete floor, example, and companion provenance gates (`A07`, `A15`, `H12`, `C2-A03`, `H06`):** Task `09-01` (`06.6-09-PLAN.md:67-70,86-120,169-181`) appends the five `tests/test1/test_theme_*.py` modules plus `test_alerts.py` and `test_button_classes.py` to `CRISPY_FLOOR_TESTS` (`noxfile.py:28-52`, verified by AST test `test_floor_selection_covers_theme_modules`), runs both `.nox/crispy_floor-3-12-django-4-2` and `.nox/crispy_floor-3-12-django-6-0`, runs `examples/bootstrap5`, records current-pack Django 6.0 as an explicit untested combination (`H12`), and preserves the user's modified `../tabler-test/example/config/settings.py`.

### 3. Concerns
- None. All Round 1 (`H12`, `A07`, `A09`, `A15`), Round 2 (`C2-A03`, `H06 — source acquisition`), and Round 3 (`C3-A01`) concerns are resolved.

### 4. Suggestions
- None; all suggestions are incorporated into Tasks `09-01` and `09-02`.

### 5. Risk Assessment
**LOW** — Final verification gates, AST floor-list checks, workflow branch validators, and fail-closed halted/pending-human handoff rules are complete and consistent.

---

## Cycle 4 Resolution Verification Summary

| Concern ID | Prior Severity | Target Plan(s) | Verification Against Source & Current Plan Text at `0d7c377` | Cycle 4 Verdict |
|---|---|---|---|---|
| `C3-A01` | MEDIUM | `05`, `07`, `09` | `WorkflowView(CustomFormView)` (`src/crud_views_workflow/lib/views.py:18-28`) sets `template_name = "crud_views_workflow/view_workflow.html"` (which includes `view_workflow.content.html` → `view_workflow.action.html`), while inheriting `cv_content_template = "crud_views/view_custom_form.content.html"` from `CustomFormView` (`src/crud_views/lib/views/form.py:19`) used by `src/crud_views/templates/crud_views/modal/content.html:8`. Plans `06.6-05-PLAN.md:19,68-69,75-84,102`, `06.6-07-PLAN.md:139-149,161`, and `06.6-09-PLAN.md:78-85,123` preserve the inherited custom-form modal body, assert actual included template names and origins for modal GET/422/no-choice vs full-page `has_workflow_choices` True/False branches, and enforce both in `--check-final`. | **Signed off (Closed)** |
| `C3-A02` | MEDIUM | `06`, `07` | `06.6-06-PLAN.md:71-78,108-119` and `06.6-07-PLAN.md:94-98,113-126,168-174` define D-18's counting unit by stable required customization purpose IDs, separate data-only public registration calls (`register_label_mode_defaults`, `register_button_classes`, `register_icons`) into adoption entries excluded from required-override counts, explicitly inventory and test the four shadowing templates in `../tabler-test/src/crud_views_tabler/templates/crud_views/` (`tags/alert.html:1-18`, `snippets/form_frame.html:1-6`, `tags/list_filter.html:1-11`, `tags/list_filter.inner.html:1-14`), adapt the isolated `tags/alert.html` copy to `alert:dismissible`, `alert:close`, and `data-cv-alert-dismiss`, and test positive/negative purpose comparisons in `test_theme_adoption_sources.py`. | **Signed off (Closed)** |
| `C3-A03` | LOW | `02` | `form_label_mode` (`src/crud_views/lib/view/label_mode.py:122-146`) falls back via `_invalid_label_mode` (`:63-84`) to `default_label_mode("form")` (`:86-120`), which on a malformed setting re-enters `_invalid_label_mode` outside `_warned_lock` (`:75-80`) to `_theme_or_package_default("form")`. `06.6-02-PLAN.md:106-107,118-125,137` explicitly tests this composed non-strict and strict path with registered `form="both"`, verifying the returned/rendered mode, both logged warnings, deduplication, and strict owner-first refusal. | **Signed off (Closed)** |
| Runtime addendum & prior `H01`–`H12`, `A01`–`A18`, `C2-A01`–`C2-A07` | HIGH / MEDIUM / LOW | `01`–`09` | `06.6-06-PLAN.md:64-70,84-99` and `06.6-09-PLAN.md:97-102` incorporate `/home/alex/projects/alex/tabler-test/.venv/bin/python` (Python 3.14.7, Django 6.1.2, crispy 2.7, crispy-bootstrap5 2026.9), preserve the user's private modified `example/config/settings.py` via pinned-commit (`885dfc791a150fdc715d6fb34c2e6181d6b92f3c`) archives, and keep `pytest-xdist` preflight and fresh baseline/replay/browser runs as fail-closed execution tasks. All prior Round 1 and Round 2 items remain intact. | **Signed off (Closed)** |

---

## Final Current Unresolved Findings

- **Current Unresolved HIGH Concerns:** **0 (None).**
- **Current Actionable MEDIUM / LOW Concerns (Omissions):** **0 (None).**
- **Already Incorporated Actions & Explicit Deferrals (No Plan Edits Required):**
  - *Incorporated in current tasks:* `C3-A01` (workflow modal inherited `view_custom_form.content.html` body vs full-page `view_workflow.content.html`/`view_workflow.action.html` choice and no-choice branches in Plans `05`, `07`, `09`), `C3-A02` (purpose-based D-18 counting rule, data-only registration adoption separation, and inspection/adaptation of the four `crud_views_tabler` shadowing templates in Plans `06`, `07`), `C3-A03` (composed malformed owner-map + malformed setting → theme floor fallback test in Plan `02`), `C2-A01`–`C2-A04`, `C2-A06`–`C2-A07`, `H01`–`H12`, `A01`–`A18`, and the `../tabler-test/.venv` runtime / private `settings.py` preservation update in Plans `06`, `07`, `09`.
  - *Explicitly deferred / bounded in plan ledgers:* `C2-A05` (`06.6-05-PLAN.md:155-161`, retaining compatible `form_tag=False` custom helpers in accepted conditional/fragment-authorization/browser fixtures while removing the two targeted parent-formset workarounds in `05-02`) and `H06 — execution evidence` (`06.6-06-PLAN.md:182-186`, `06.6-07-PLAN.md:201-204`, `06.6-09-PLAN.md:218-222`, keeping fresh baseline capture, isolated patch replay, Chromium runs, and human visual/AT checks as mandatory fail-closed execution gates).

### Overall Risk Assessment
**LOW** — All nine plans (`06.6-01` through `06.6-09`) are fully converged against the core repository and companion sources and are ready for execution.
