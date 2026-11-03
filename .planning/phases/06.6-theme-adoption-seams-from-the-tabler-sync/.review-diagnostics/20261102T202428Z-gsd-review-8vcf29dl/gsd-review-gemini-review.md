## 06.6-01

### Summary
Plan `06.6-01` resolves the nested `<form>` and duplicate CSRF token defect on the create path and introduces render-local helper selection (`_prepare_form_helper`) and wrapper diagnostics (`_diagnose_form_wrapper`) behind `cv_render_form`. Verification against the live source confirms that `CrispyFormMixin.helper` (`src/crud_views/lib/crispy/form.py:43-50`) and `CrispyDeleteForm.helper` (`src/crud_views/lib/crispy/form.py:136-146`) instantiate `FormHelper()` with crispy's default `form_tag = True`, while `src/crud_views/templates/crud_views/view_create.content.html:5-11` already wraps `{% cv_render_form %}` in `<form class="cv-form" method="post" ...>{% csrf_token %}`, producing the nested `<form method="post">` and second `csrfmiddlewaretoken` input captured in `tests/test1/golden/form_frame/create.html:1`. Pairing Tasks `01-01` and `01-02` in one atomic commit cleanly migrates the renderer together with the four frame goldens (`tests/test1/golden/form_frame/{create,update,custom_form,delete}.html`) and the two custom-helper test fixtures (`_CustomHelperForm` and `_DeleteCustomHelper` in `tests/test1/test_form_button_checks.py:560-585`).

### Strengths
- **Preserves `Context.dicts` stack for form-button owner resolution (`src/crud_views/templatetags/crud_views.py:453-466`, `src/crud_views/lib/crispy/buttons.py:49-93`):** `cv_render_form` at `src/crud_views/templatetags/crud_views.py:465-466` currently calls `render_to_string(..., context.flatten())`, collapsing the template context stack. Switching to `get_template(...).template.render(context)` under `with context.push(cv_form_helper=...):` (matching `cv_alert` at `src/crud_views/templatetags/crud_views.py:453-455`) preserves `context.dicts` so `_cv_helper_tier` (`src/crud_views/lib/crispy/buttons.py:49-61`) and `_cv_page_tier` (`src/crud_views/lib/crispy/buttons.py:64-77`) continue to separate crispy response overlays from page layers.
- **Eliminates double evaluation and truthiness traps on `form.helper` (`src/crud_views/templates/crud_views/tags/form.html:3-6`, `src/crud_views/lib/crispy/form.py:43-50`):** `tags/form.html:3-4` currently evaluates `{% if form.helper %}` and then `{% crispy form form.helper %}`, invoking the `@property def helper` factory twice and testing truthiness (`FormHelper.__len__` delegates to `len(self.layout)`). Selecting `cv_form_helper` once by presence/identity in `_prepare_form_helper` and synthesizing a non-wrapping helper (`form_tag=False`, `disable_csrf=True`) when `form.helper` is absent/`None` ensures plain `django.forms.Form` instances (such as `NameForm` in `tests/test1/test_form_frame.py:34-35`) also render without a nested `<form>` or duplicate token.
- **Atomic fixture and golden boundary (`tests/test1/test_form_button_checks.py:560-585,1084-1110`, `tests/test1/test_form_frame.py:19-24,71-73`):** `_CustomHelperForm.helper` (`tests/test1/test_form_button_checks.py:564-567`) and `_DeleteCustomHelper.helper` (`tests/test1/test_form_button_checks.py:582-585`) construct bare `FormHelper()` instances to test missing-icon runtime policy at `lines 1084-1110`. Migrating those two helpers to `form_tag=False` and updating the four frame goldens in Task `01-02` within the same commit as Task `01-01` keeps the suite green at every commit boundary.
- **Standalone crispy token preservation (`src/crud_views/lib/crispy/form.py:43-50`):** Setting `form_tag = False` on `CrispyFormMixin.helper` and `CrispyDeleteForm.helper` while keeping `disable_csrf = True` render-local to `cv_render_form` preserves standalone `{% crispy form %}` CSRF emission (`C2-A02`).

### Concerns
- None unresolved. All source seams, fixture dependencies, and helper-diagnostic boundaries are verified.

### Suggestions
- In `src/crud_views/templates/crud_views/tags/form.html`, render `{% crispy form cv_form_helper %}` directly so `cv_form_helper` is the single inner rendering path.

### Risk Assessment
**LOW** — The changes in `src/crud_views/lib/crispy/form.py`, `src/crud_views/templatetags/crud_views.py`, and `src/crud_views/templates/crud_views/tags/form.html` are tightly scoped and directly guarded by golden and enforced-CSRF tests.

---

## 06.6-02

### Summary
Plan `06.6-02` adds `register_label_mode_defaults(defaults: dict[str, str]) -> None` to `src/crud_views/lib/view/label_mode.py`, introducing a validated theme floor between `LABEL_MODE_DEFAULTS` (`src/crud_views/lib/view/label_mode.py:23-25`) and the live `CRUD_VIEWS_LABEL_MODE_DEFAULTS` setting (`src/crud_views/lib/view/label_mode.py:56-60,86-119`), while updating invalid-setting fallback destinations (`D-07`) and verifying `crud_views.E108` (`src/crud_views/lib/settings.py:161-190`) and `viewset.W292` (`src/crud_views/lib/view/buttons.py:435-448,546-584`).

### Strengths
- **Setting-free `_theme_or_package_default` prevents fallback recursion (`src/crud_views/lib/view/label_mode.py:86-146`):** In `default_label_mode` (`src/crud_views/lib/view/label_mode.py:107,118`), invalid `CRUD_VIEWS_LABEL_MODE_DEFAULTS` values currently fall back via `lambda: LABEL_MODE_DEFAULTS[location]`. Routing those fallbacks through `_theme_or_package_default(location)` (reading only the rebound `_THEME_LABEL_MODE_DEFAULTS` snapshot and `LABEL_MODE_DEFAULTS`, never `_raw_label_mode_defaults()`) ensures that composed invalid owner map + invalid setting fallback in `form_label_mode` (`src/crud_views/lib/view/label_mode.py:129-146`, `C3-A03`) resolves to the theme floor without recursion.
- **Dedup-aware composed fallback testing (`src/crud_views/lib/view/label_mode.py:31-32,76-83`):** Because `_invalid_label_mode` deduplicates warnings by `pair = (location, repr(value))` (`line 76`), Task `02-02` explicitly uses distinct malformed values for the owner map and setting on `"form"`, ensuring both warnings are observed.
- **Autouse registry isolation in `tests/test1/conftest.py:23-33`:** Adding an autouse snapshot/rebind fixture for `_THEME_LABEL_MODE_DEFAULTS` in `tests/test1/conftest.py` (alongside the existing `label_mode._warned` reset) prevents cross-test contamination under `pytest-xdist`.
- **Static W292 compatibility (`src/crud_views/lib/view/buttons.py:435,569`):** Both `context_button_checks` (`line 435`) and `cv_form_icon_mode_checks` (`line 569`) already resolve effective modes via `cls.cv_get_action_label_mode(...)` -> `default_label_mode(...)`, so theme defaults take effect without instantiating forms at startup.

### Concerns
- None unresolved.

### Suggestions
- Keep `from .button_data import LOCATIONS` deferred inside `register_label_mode_defaults` (matching `default_label_mode` at `src/crud_views/lib/view/label_mode.py:95`) to avoid circular imports with `src/crud_views/lib/view/button_data.py:15`.

### Risk Assessment
**LOW** — Directly follows the established registry and resolver patterns in `src/crud_views/lib/button_classes.py:135-151` and `src/crud_views/lib/view/label_mode.py:86-146`.

---

## 06.6-03

### Summary
Plan `06.6-03` adds the `form:actions` and `form:filter-actions` utility keys (`""` defaults in `DEFAULT_BUTTON_CLASSES`) and wires them into the three library action-group constructors (`CrispyFormMixin.get_form_actions` at `src/crud_views/lib/crispy/form.py:55-56`, `CrispyDeleteForm.helper` at `src/crud_views/lib/crispy/form.py:141-144`, and `ListViewFilterFormHelper.get_form_actions` at `src/crud_views/lib/views/list.py:125-133`), backed by a narrowly scoped compatibility bridge (`_ThemedFormActions` and `crud_views/crispy/bootstrap5_formactions.html`) for the declared `crispy-bootstrap5==2023.10` floor (`noxfile.py:24`).

### Strengths
- **Covers all three default `FormActions` constructors while preserving static W292 checks (`src/crud_views/lib/crispy/form.py:55-56,141-144`, `src/crud_views/lib/views/list.py:125-133`, `src/crud_views/lib/view/buttons.py:504,513,538`):** Updating `CrispyFormMixin.get_form_actions`, `CrispyDeleteForm.helper`, and `ListViewFilterFormHelper.get_form_actions` on the base classes covers ordinary, delete, and filter forms while keeping `_inherits(...)` in `_static_form_controls` and `_static_filter_controls` `True`.
- **Render-time class lookup on cached filter action groups (`src/crud_views/lib/views/list.py:155,172-180`):** `ListViewFilterFormHelper.render_layout` caches `self._cv_actions = self.get_form_actions()` per prepared layout (`lines 174-179`). Storing the class-table key as primitive deepcopy-safe state on `_ThemedFormActions` and resolving `get_button_class` per render (`H05`) ensures `register_button_classes` and `override_settings` updates apply without accumulating classes or mutating `self.css_class`.
- **Exact floor-template discriminator (`noxfile.py:24`, `06.6-RESEARCH.md:208-231`):** `_use_bootstrap5_floor_bridge` checks that `template_pack == "bootstrap5"`, the resolved template origin is inside the installed `crispy_bootstrap5` distribution, and the template content equals the audited 9-line 2023.10 `bootstrap5/layout/formactions.html` source (`H01`, `C4-A04`), delegating unchanged for all other packs (`crispy_tabler`) and custom templates.
- **Synchronized key count (`tests/test1/test_button_classes.py:21-91,105,112-116`, `docs/reference/buttons.md:151`):** Depends on Plan `06.6-04` and updates `EXPECTED_KEYS` and `docs/reference/buttons.md:151` from 86 to 88 in Task `03-02` (`H04`), with verification on both `.nox/crispy_floor-3-12-django-6-0` and `.nox/crispy_floor-3-12-django-4-2` in Task `03-03` (`C2-A03`).

### Concerns
- None unresolved.

### Suggestions
- Retain the exact 9-line `crispy-bootstrap5==2023.10` `bootstrap5/layout/formactions.html` source string (including its `class="aab {{ label_class }}"` token) for the whole-source equality check in `_use_bootstrap5_floor_bridge`.

### Risk Assessment
**LOW** — The floor limitation was reproduced in research and the bridge is strictly gated by pack name, resolved origin path, and exact template source equality.

---

## 06.6-04

### Summary
Plan `06.6-04` introduces the `alert:dismissible` (`"alert-dismissible fade show"`) and `alert:close` (`"btn-close"`) utility keys in `DEFAULT_BUTTON_CLASSES` (`src/crud_views/lib/button_classes.py:91-96`) and consumes them in `src/crud_views/templates/crud_views/tags/alert.html:2-5` while keeping unconfigured default alert bytes, escaping, accessible names, and `data-cv-alert-dismiss` adapter behavior intact.

### Strengths
- **Byte-identical default golden preservation (`src/crud_views/templates/crud_views/tags/alert.html:2-5`, `tests/test1/golden/alerts/dismissible.html:1-7`, `tests/test1/test_alerts.py:166-181`):** `test_dismissible_alert_golden` (`tests/test1/test_alerts.py:166-181`) compares raw bytes without whitespace normalization. Resolving `alert:dismissible` into a template variable and emitting the leading space only when non-empty (`A03`), while rendering `class="{% cv_button_class 'alert' 'close' %}"` on the close `<button>`, preserves exact byte identity with `tests/test1/golden/alerts/dismissible.html`.
- **W362 base-only utility validation (`src/crud_views/lib/button_classes.py:251-275,328-346`):** Adding `"alert:dismissible"` and `"alert:close"` to `DEFAULT_BUTTON_CLASSES` makes `button_class_check_messages` (`line 329`) accept them as base keys while rejecting mode-suffixed variants such as `alert:close:icon` or `alert:dismissible:both` with `crud_views.W362`.
- **Atomic 84 -> 86 key-inventory update (`tests/test1/test_button_classes.py:21-91,105,112-116`, `docs/reference/buttons.md:151`):** Updating `EXPECTED_KEYS` and `docs/reference/buttons.md:151` in Task `04-01` keeps `test_default_table_is_complete` and `test_documented_default_key_count_matches_table` green.

### Concerns
- None unresolved.

### Suggestions
- None.

### Risk Assessment
**LOW** — Self-contained dictionary and leaf-template update guarded by byte-exact golden assertions and Vitest adapter tests (`tests/js/adapters.test.js`).

---

## 06.6-05

### Summary
Plan `06.6-05` routes `src/crud_views_workflow/templates/crud_views_workflow/view_workflow.action.html` through `{% cv_render_form %}`, expands raw single-form/single-CSRF and enforced-CSRF request testing across all five actionable form types (full-page and supported modal paths), and removes the two redundant `form_tag = False` parent formset helper overrides in `tests/test1/app/views_formset.py:44-50` and `examples/bootstrap5/formsets/views.py:36-41`.

### Strengths
- **Eliminates workflow's direct crispy bypass (`src/crud_views_workflow/templates/crud_views_workflow/view_workflow.action.html:2,8-16`):** `view_workflow.action.html:8-16` opens `<form class="cv-form" method="post" novalidate>{% csrf_token %}` and calls `{% crispy form form.helper %}` at line 15. Replacing line 15 with `{% cv_render_form %}` and removing the unused `{% load crispy_forms_tags %}` at line 2 (`A12`) routes full-page workflow forms through Plan `06.6-01`'s single-helper boundary.
- **Accurately separates workflow modal and full-page template paths (`src/crud_views_workflow/lib/views.py:18-28`, `src/crud_views/lib/views/form.py:18-55`, `src/crud_views/templates/crud_views/modal/content.html:8`):** `WorkflowView` inherits `cv_content_template = "crud_views/view_custom_form.content.html"` from `CustomFormView` while setting `template_name = "crud_views_workflow/view_workflow.html"`. Task `05-01` (`C3-A01`) tests modal workflow (`view_custom_form.content.html`) and full-page workflow (`view_workflow.content.html` / `view_workflow.action.html` with and without choices) separately and asserts their distinct template origins, while preserving `cv_modal_supported = False` and `E251` on create/update (`src/crud_views/lib/view/base.py:111,169-170`, `C2-A01`).
- **Restores static W292 inspection on parent formset forms (`tests/test1/app/views_formset.py:44-50`, `examples/bootstrap5/formsets/views.py:4,36-41`, `src/crud_views/lib/view/buttons.py:512`):** Removing the redundant `helper` properties on `PublisherFormSetForm` and `QuestionnaireForm` (and the unused `FormHelper` import in `examples/bootstrap5/formsets/views.py:4`) restores `_inherits(form_class, "helper", CrispyFormMixin)` so static `W292` checks inspect them while `tests/test1/test_formsets.py:16-35` continues to pass.

### Concerns
- None unresolved.

### Suggestions
- None.

### Risk Assessment
**LOW** — Directly extends Plan `06.6-01` across all stock and extension form views with source-verified modal and template-origin boundaries.

---

## 06.6-06

### Summary
Plan `06.6-06` builds the import-pure, Django-free `tests/browser/theme_adoption_sources.py` provenance, baseline, replay, and delivery validation CLI (with unit tests in `tests/browser/test_theme_adoption_sources.py`) and captures the unmodified baseline of `../tabler-test` (`885dfc791a150fdc715d6fb34c2e6181d6b92f3c`) against the pre-phase core revision (`cb26af4dfef2afb31d774a219abfad1c675cdff1`).

### Strengths
- **Complete tree-derived shadow and behavior classification (`../tabler-test/src/crud_views_tabler/checks.py:8-27`, `../tabler-test/src/crud_views_tabler/icons.py:50-52`, `../tabler-test/src/crud_views_tabler/templates/crud_views/*`):** Task `06-01` (`C3-A02`, `C4-A01`) enumerates the full archived companion tree, discovers all eight template shadows (`modal/shell.html`, `snippets/form_frame.html`, `table/bootstrap5.html`, `tags/alert.html`, `tags/card.html`, `tags/list_filter.html`, `tags/list_filter.inner.html`, `view_card.content.html`), and classifies bespoke Python behavior (`check_tabler_icons` in `checks.py:8-27` and `render` in `icons.py:50-52`) separately from data-only registrations.
- **Per-invocation recorded companion root and interpreter resolution (`C6-A03`, `C7-A02`):** `06-companion-baseline.json` records both the canonical absolute `companion_root` and `companion_python` (preserving the venv symlink path without dereferencing it, along with `sys.prefix` and runtime versions). Every subsequent `--check-baseline`, `--verify-replay`, and `--delivered-source recorded` invocation reloads both fields from the manifest beneath `Path(__file__).resolve().parents[2]`, ensuring fresh shells and isolated core checkouts never depend on ambient environment variables or cwd-relative siblings.
- **Truthful `cancel-no-url` validation distinguishing `None` from `""` (`src/crud_views/lib/view/button_data.py:354-357,392-393`, `src/crud_views/templates/crud_views/tags/button/form.html:3`, `src/crud_views/static/crud_views/js/viewset.js:38-44`, `C7-A01`):** Task `06-01` validates both URL-less cancel branches separately in replay and delivery records: absent/`None` (which omits `data-cv-cancel-url` and preserves edited input without navigation) and explicit `""` (which emits `data-cv-cancel-url=""` per `tests/test1/test_crispy_buttons.py:2110` and performs `viewset.js:43`'s same-URL document GET with zero submit/reset events and no POST).
- **Single-file progressive delivery bundle (`C6-A02`):** `form_probe`, `delivered_probe`, and `committed_probe` with full sanitized logs and digests are merged atomically into `.planning/phases/06.6-theme-adoption-seams-from-the-tabler-sync/10-companion-delivery.json` while keeping private settings and index snapshots outside both repositories.

### Concerns
- None unresolved. All Cycle 6 and Cycle 7 findings (`C6-A01`, `C6-A02`, `C6-A03`, `C7-A01`, `C7-A02`) are incorporated with negative unit tests.

### Suggestions
- None.

### Risk Assessment
**LOW** — The utility is import-pure, tested with isolated disposable fixtures in `tests/browser/test_theme_adoption_sources.py`, and fails closed on missing prerequisites or mismatched provenance.

---

## 06.6-07

### Summary
Plan `06.6-07` implements the isolated real-Tabler browser harness (`tests/browser/theme-adoption.cjs`, `tests/browser/theme_adoption_server.py`, and `tests/browser/theme-adoption-config.test.cjs`), applies the verified companion adaptations in the isolated candidate copy (`register_label_mode_defaults({"form": "both"})` in `apps.py`, three native icon mappings in `icons.py`, four button-class keys in `buttons.py`, alert utility/hook updates in `templates/crud_views/tags/alert.html`, and test updates in `tests.py`), and replays the exported `07-tabler-adaptation.patch` against fresh exact-base copies.

### Strengths
- **Concrete native Tabler icon mappings (`../tabler-test/src/crud_views_tabler/icons.py:12-47`, `../tabler-test/src/crud_views_tabler/tests.py:62-67,173-175,451-452`, `C5-H01`):** Adding `"save": "tabler:check"`, `"cancel": "tabler:arrow-left"`, and `"filter-reset": "tabler:filter-x"` to `TABLER_ICONS` maps the three Phase 6 keys from `DEFAULT_ICONS` (`src/crud_views/lib/icons.py:51-53`), satisfies `TablerIconTests.test_every_upstream_icon_name_is_mapped` (`tests.py:62-67`), and renders native Tabler SVGs across all five form action kinds (`submit`, `delete`, `cancel`, `filter-submit`, `filter-reset`) in `both`, `icon`, and `label` modes without Font Awesome `<i class="...">` fallback.
- **Exact `TABLER_BUTTON_CLASSES` dictionary synchronization (`../tabler-test/src/crud_views_tabler/buttons.py:3-44`, `../tabler-test/src/crud_views_tabler/tests.py:84-139`, `C5-A08`):** Adding `"form:actions": "d-flex flex-wrap gap-2"`, `"form:filter-actions": "d-flex flex-wrap gap-1"`, `"alert:dismissible": "alert-dismissible fade show"`, and `"alert:close": "btn-close"` to both `TABLER_BUTTON_CLASSES` and `ButtonClassTests.test_table_values` preserves whole-dictionary equality (`tests.py:139`) and upstream-key validation (`tests.py:88`).
- **Real browser activation for both URL-less cancel states without interception (`src/crud_views/lib/view/button_data.py:354-393`, `src/crud_views/templates/crud_views/tags/button/form.html:3`, `src/crud_views/static/crud_views/js/viewset.js:38-44`, `C6-A01`, `C7-A01`):** Task `07-02` exercises both absent/`None` (`data-cv-cancel-url` omitted -> no navigation, zero submit/reset, edited input preserved) and explicit `""` (`data-cv-cancel-url=""` emitted -> real same-URL document GET awaited in Chromium with `sessionStorage` tracking zero submit/reset events and no POST) across `both`/`icon`/`label` modes and requested `button`/`a` tags without modifying `viewset.js` or intercepting navigation.
- **Fresh-shell `resolveCompanionPython` in `tests/browser/theme-adoption.cjs` (`tests/browser/presentation.cjs:396-403`, `tests/browser/presentation-config.test.cjs:1-27`, `C7-A02`):** Exporting `resolveCompanionPython` from `tests/browser/theme-adoption.cjs` (reading `companion_python` and its `sys.prefix`/version from `06-companion-baseline.json` beneath `path.resolve(__dirname, "../..")` without `fs.realpathSync` on the venv symlink) and running all four verification commands in `07-01` and `07-02` with `env -u CV_THEME_PYTHON -u CV_FOCUS_PYTHON` guarantees hermetic per-invocation runtime selection.
- **Strict named-hook message parity (`../tabler-test/src/crud_views_tabler/templates/crud_views/tags/alert.html:7,17`, `../tabler-test/src/crud_views_tabler/tests.py:556-573`, `C4-A02`):** Updating `crud_views_tabler`'s `tags/alert.html` to consume `alert:dismissible`, `alert:close`, and `data-cv-alert-dismiss` while keeping `django_tabler/includes/messages.html` on native `data-bs-dismiss="alert"` and asserting that exact single-attribute difference in `MessagesParityTests.test_plain_include_matches_cv_messages` preserves standalone `django_tabler` independence.

### Concerns
- None unresolved. Both `C7-A01` and `C7-A02` are cleanly incorporated in `07-01`, `07-02`, and `07-03`.

### Suggestions
- None.

### Risk Assessment
**LOW** — Every companion file change, browser case, and fresh-shell runtime resolution contract is verified against the core and embedded companion sources.

---

## 06.6-08

### Summary
Plan `06.6-08` updates the author-facing documentation (`docs/reference/theme.md`, `docs/reference/action_menus.md`, `docs/reference/settings.md`), migration guide (`docs/migrating-1.0.md`), and `CHANGELOG.md`, backed by executable documentation tests in `tests/test1/test_theme_adoption_docs.py` and synchronized assertions in `tests/test1/test_label_mode_docs.py`.

### Strengths
- **Respects existing documentation test guards (`tests/test1/test_alerts.py:249-258`, `tests/test1/test_label_mode_docs.py:190-229,709-717,777-815`):**
  - `test_alerts.py:249-255` requires `### Custom alert frame` in `docs/reference/theme.md:308-321` to contain a single `django`/`html` code fence; Task `08-01` places the new utility-key prose outside that fence and runs `test_alerts.py` (`H08`).
  - `test_label_mode_docs.py:777-815` (`test_migration_e108_location_inventory`) checks the E108 fallback sentence in `docs/migrating-1.0.md:61-64`; Task `08-01` leaves that pair untouched until Task `08-02` updates `docs/migrating-1.0.md` and `test_label_mode_docs.py` together (`H07`).
  - Task `08-01` preserves the numbered owner-resolution step structure in `docs/reference/action_menus.md` by describing the three floor layers (`package -> theme -> project`) inside the existing floor step.
- **Executable standalone `CrispyModelForm` wrapper migration (`C2-A02`):** Tasks `08-01` and `08-02` document and test a caller-owned outer `<form>` wrapper around standalone `{% crispy form %}` renders of `CrispyModelForm` (retaining crispy's CSRF token without adding a duplicate token) and pair the `### Breaking` changelog entry with `docs/migrating-1.0.md`.

### Concerns
- None unresolved.

### Suggestions
- None.

### Risk Assessment
**LOW** — All documentation fence extractors, step-count guards, and strict MkDocs checks (`.venv/bin/mkdocs build --strict`) are directly verified by the task commands.

---

## 06.6-09

### Summary
Plan `06.6-09` runs in Wave 5 after Plans `06.6-07`, `06.6-08`, and `06.6-10` complete, extending `noxfile.py` (`CRISPY_FLOOR_TESTS` at `noxfile.py:28-52`) with the new theme-adoption test modules, executing the full multi-series Python, crispy-floor (Django 4.2 and 6.0), `examples/bootstrap5`, Vitest, fragment integration, browser lifecycle, docs, and lint gates, validating the committed companion delivery (`--check-final`), and producing `06.6-PUBLIC-SURFACE.md` and `06.6-ACCEPTANCE.md` for Phase 7.

### Strengths
- **Permanent `CRISPY_FLOOR_TESTS` expansion verified via AST (`noxfile.py:28-52`, `A15`):** Appending the five new `tests/test1/test_theme_*.py` modules plus `tests/test1/test_alerts.py` and `tests/test1/test_button_classes.py` to `CRISPY_FLOOR_TESTS` (while keeping `CRISPY_FLOOR_DESELECT` at `noxfile.py:57` limited to `test_filter_form_baseline`) and verifying the list via AST in `test_floor_selection_covers_theme_modules` ensures permanent floor coverage across both `.nox/crispy_floor-3-12-django-4-2` and `.nox/crispy_floor-3-12-django-6-0` (`C2-A03`).
- **End-to-end `--check-final` verification (`C4-A01`, `C4-A02`, `C5-H01`, `C5-A01`, `C5-A08`, `C6-A01`, `C6-A02`, `C6-A03`, `C7-A01`, `C7-A02`):** Task `09-01` binds `06-companion-baseline.json`, `07-browser-results.json`, `07-tabler-replay.json`, and committed `10-companion-delivery.json` to actual source/test/runtime fingerprints, verifies both absent/`None` and explicit `""` `cancel-no-url` records, verifies `companion_python` / `sys.prefix` / version consistency and fresh-shell config test results, and validates both the companion commit (via `git -C` on the recorded `companion_root`) and the core `10-03` evidence commit.
- **Honest matrix and human-verification boundaries (`H12`, `A09`):** Current-pack Django 6.0 is explicitly recorded as untested unless an environment is present, and human visual/assistive-technology checks remain a distinct gate that automation never fabricates.

### Concerns
- None unresolved.

### Suggestions
- None.

### Risk Assessment
**LOW** — Sequenced in Wave 5 with deterministic source-bound checks across all upstream artifacts.

---

## 06.6-10

### Summary
Plan `06.6-10` delivers the replay-verified companion changes from Plan `06.6-07` into the user-supplied `../tabler-test` repository under amended `D-11`/`D-14`, commits the companion source/test delta (`apps.py`, `buttons.py`, `icons.py`, `templates/crud_views/tags/alert.html`, `tests.py`, and conditional `formactions.html`) in a single green companion commit after `10-02` using a private temporary `GIT_INDEX_FILE` that preserves `example/config/settings.py` and unrelated staged/unstaged work, and commits `10-companion-delivery.json` and `07-TABLER-HANDOFF.md` in the core repository in `10-03`.

### Strengths
- **Shared companion commit boundary (`10-01` + `10-02`) and separate core evidence commit (`10-03`) (`C5-A01`, `C5-A08`):** Delivering `apps.py`, `buttons.py`, and `icons.py` in `10-01` and synchronizing `templates/crud_views/tags/alert.html` and `tests.py` (`ButtonClassTests.test_table_values`, `ThemeAdoptionTests`, `MessagesParityTests`) in `10-02` before making one companion commit ensures `test_table_values` (`../tabler-test/src/crud_views_tabler/tests.py:98-139`) and `MessagesParityTests` (`lines 556-573`) are never broken on a partial companion commit. Committing only `10-companion-delivery.json` and `07-TABLER-HANDOFF.md` in core in `10-03` keeps the core `gsd-plan-head-before-06.6-10` commit ledger and `gsd_run check evaluation-scope --plan 06.6-10 --commits-only --raw` accurate.
- **Private `GIT_INDEX_FILE` index-isolation and 3-way reconciliation protocol (`06.6-10-PLAN.md:104-125`):** Building a temporary index from `git -C "$COMPANION_ROOT" read-tree "$COMPANION_HEAD_BEFORE"`, applying only the verified patch with `git apply --cached`, committing with that temporary index, and reconciling the live index via `git apply --cached --3way` under `index.lock` preserves `example/config/settings.py` and any unrelated staged/unstaged hunks without using prohibited git commands (`git stash`, `git clean`, `git reset --hard`).
- **Self-contained committed delivery manifest and fresh-shell runtime resolution (`C6-A02`, `C6-A03`, `C7-A01`, `C7-A02`):** All four verification commands use `--delivered-source recorded`, `10-01`'s browser command runs with `env -u CV_THEME_PYTHON -u CV_FOCUS_PYTHON` (reloading `companion_python` from `06-companion-baseline.json`), and `form_probe`, `delivered_probe`, and `committed_probe` (including both absent/`None` and explicit `""` `cancel-no-url` records and full sanitized logs) are stored inside `.planning/phases/06.6-theme-adoption-seams-from-the-tabler-sync/10-companion-delivery.json`.

### Concerns
- None unresolved. All cross-repository commit accounting, index-preservation, cancel-activation (`C7-A01`), and fresh-shell runtime (`C7-A02`) contracts are complete.

### Suggestions
- None.

### Risk Assessment
**LOW** — The cross-repository delivery and commit protocol is fully specified, preserves all user work in both repositories, and aligns with the installed `gsd-executor` contract.

---

## Cross-Plan Comparison and Overall Risk Assessment

### Verification of Cycle 8 Focus Areas
1. **`C5-H01` & `C5-A08` (Concrete `form=both`, native Tabler `save`/`cancel`/`filter-reset` mappings, five action kinds in three modes + reset, and exact `TABLER_BUTTON_CLASSES` sync):** Verified against `../tabler-test/src/crud_views_tabler/{apps.py,buttons.py,icons.py,tests.py}` and core `src/crud_views/lib/icons.py:51-53`. Consistently enforced across Plans `06.6-06`, `06.6-07`, `06.6-09`, and `06.6-10`.
2. **`C5-A01` & `C7-A03` (Bounded shared companion commit for `10-01`/`10-02`, core evidence commit for `10-03`, temporary-index preservation, and authorized companion write routing):** Verified against the installed `gsd-executor` contract and `06.6-10-PLAN.md:83-135`.
3. **`C6-A01` & `C7-A01` (URL-less cancel across `both`/`icon`/`label` modes preserving Phase 6.1 `D-08`/`D-17` and current `D-16`):** Verified against `src/crud_views/lib/view/button_data.py:354-393`, `src/crud_views/templates/crud_views/tags/button/form.html:1-3`, `src/crud_views/static/crud_views/js/viewset.js:38-44`, and `tests/test1/test_crispy_buttons.py:2110`. Absent/`None` (`data-cv-cancel-url` omitted -> no-op preserving edited input) and explicit `""` (`data-cv-cancel-url=""` -> real same-URL document GET with zero submit/reset events and no POST) are tested separately without interception across Plans `06.6-06`, `06.6-07`, `06.6-09`, and `06.6-10`.
4. **`C6-A02`, `C6-A03`, & `C7-A02` (Embedded sanitized probes/logs in `10-companion-delivery.json`, `--delivered-source recorded`, and per-invocation `companion_python` reload with `env -u CV_THEME_PYTHON -u CV_FOCUS_PYTHON`):** Verified across all 5 browser/config verification commands in Plans `06.6-07` and `06.6-10` and the Python validators in Plans `06.6-06` and `06.6-09`.

### Unresolved Executable Gaps
- **HIGH:** 0
- **MEDIUM:** 0
- **LOW:** 0

### Overall Risk Assessment
**LOW** — All ten plans (`24` tasks, `33` automated verification commands across `5` waves) are source-grounded, internally consistent, and ready for execution.
