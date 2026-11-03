## 06.6-01

### 1. Summary
Plan `06.6-01` establishes single-form and single-CSRF-token ownership at the `cv_render_form` template-tag boundary (`src/crud_views/templatetags/crud_views.py:464-466`) and in the library form helpers (`src/crud_views/lib/crispy/form.py:43-50,136-146`), while diagnosing incompatible (`form_tag=True`) and unused wrapper attributes on custom `FormHelper` instances per D-01–D-04 and D-16. It pairs the renderer change with atomic updates to the four `form_frame` goldens and the two custom-helper test fixtures in `tests/test1/test_form_button_checks.py:560-585`.

### 2. Strengths
- **Root-cause accuracy for nested forms and duplicate CSRF tokens:** `CrispyFormMixin.helper` (`src/crud_views/lib/crispy/form.py:43-50`) and `CrispyDeleteForm.helper` (`src/crud_views/lib/crispy/form.py:136-146`) currently return a fresh `FormHelper()` with default `form_tag=True` and `disable_csrf=False`, while `src/crud_views/templates/crud_views/view_create.content.html:5-11` already wraps `{% cv_render_form %}` in `<form class="cv-form" method="post" ...>{% csrf_token %}...`, producing the nested `<form>` and second `csrfmiddlewaretoken` visible in `tests/test1/golden/form_frame/create.html:1`.
- **Single helper evaluation and preserved `Context.dicts` stack:** `src/crud_views/templates/crud_views/tags/form.html:3-6` currently evaluates `form.helper` twice (`{% if form.helper %}` and `{% crispy form form.helper %}`), and `cv_render_form` (`src/crud_views/templatetags/crud_views.py:465-466`) calls `context.flatten()`, which collapses the `context.dicts` layers inspected by `_cv_helper_tier` and `_cv_page_tier` (`src/crud_views/lib/crispy/buttons.py:49-78`). Resolving `cv_form_helper` once and rendering via `get_template(...).template.render(context)` with `context.push(...)` (matching `cv_alert` at `src/crud_views/templatetags/crud_views.py:453-455`) fixes both issues cleanly.
- **Atomic fixture and golden migration (`01-01` + `01-02`):** `_CustomHelperForm` (`tests/test1/test_form_button_checks.py:560-567`) and `_DeleteCustomHelper` (`tests/test1/test_form_button_checks.py:578-585`) construct raw `FormHelper()` instances without `form_tag=False` and are exercised through full-page renders in `test_custom_submit_hooks_follow_the_runtime_policy` (`tests/test1/test_form_button_checks.py:1085-1094`) and `test_custom_delete_helper_follows_the_runtime_policy` (`tests/test1/test_form_button_checks.py:1099-1110`). Migrating them alongside `tests/test1/golden/form_frame/{create,update,custom_form,delete}.html` prevents mid-wave breakage.

### 3. Concerns
- **LOW — Plain `django.forms.Form` instances without `.helper` in `test_form_frame.py`:** `NameForm` in `tests/test1/test_form_frame.py:34-41` is a plain `forms.Form` with no `.helper` attribute, which previously took the `{% else %}{% crispy form %}` branch in `src/crud_views/templates/crud_views/tags/form.html:5-6`. When `_prepare_form_helper` synthesizes a default non-wrapping `FormHelper(form_tag=False)` with `disable_csrf=True` for helperless forms, it must not attach `.helper` back onto the `NameForm` instance (preserving caller form state) and must return `mark_safe(...)` from `cv_render_form` (`src/crud_views/templatetags/crud_views.py:465`).

### 4. Suggestions
- In `_prepare_form_helper(form)`, ensure that when `getattr(form, "helper", None)` is `None`, the synthesized `FormHelper` sets both `form_tag = False` and `disable_csrf = True` on the render-local helper only, leaving ` hasattr(form, "helper")` unchanged after `cv_render_form` returns.

### 5. Risk Assessment
**LOW** — The render boundary in `src/crud_views/templatetags/crud_views.py:464-466` and helper definitions in `src/crud_views/lib/crispy/form.py:43-50,136-146` are small and self-contained, and the plan bounds the custom-helper copy experiment with explicit fallback criteria.

---

## 06.6-02

### 1. Summary
Plan `06.6-02` adds `register_label_mode_defaults(defaults: dict[str, str]) -> None` to `src/crud_views/lib/view/label_mode.py`, introducing a validated theme floor between `LABEL_MODE_DEFAULTS` (`src/crud_views/lib/view/label_mode.py:23-25`) and the live `CRUD_VIEWS_LABEL_MODE_DEFAULTS` setting (`src/crud_views/lib/view/label_mode.py:86-120`) while preserving explicit button/view and whole-map owner precedence, `E108` settings validation (`src/crud_views/lib/settings.py:161-190`), and `W292` missing-icon checks (`src/crud_views/lib/view/buttons.py:435,570`).

### 2. Strengths
- **Non-recursive invalid-setting fallback (`_theme_or_package_default`):** In `src/crud_views/lib/view/label_mode.py:122-146`, `form_label_mode` passes `lambda: default_label_mode("form")` as the `fallback` to `_invalid_label_mode`. In turn, `default_label_mode` (`src/crud_views/lib/view/label_mode.py:103-119`) passes a fallback lambda when `CRUD_VIEWS_LABEL_MODE_DEFAULTS` is malformed. Routing `default_label_mode`'s fallback through `_theme_or_package_default(location)` (reading only the rebounds of `_THEME_LABEL_MODE_DEFAULTS` and `LABEL_MODE_DEFAULTS`) guarantees that composed invalid owner map + invalid setting configurations resolve to the registered theme default (`"both"`) without re-reading settings or recursing.
- **Automatic `W292` integration without form instantiation:** Both `context_button_checks` (`src/crud_views/lib/view/buttons.py:435`) and `cv_form_icon_mode_checks` (`src/crud_views/lib/view/buttons.py:570`) call `cls.cv_get_action_label_mode(...)`, which delegates unnamed keys to `default_label_mode("context")` (`src/crud_views/lib/view/base.py:341`) and `form_label_mode(..., kind)` -> `default_label_mode("form")` (`src/crud_views/lib/view/base.py:349`). Updating `default_label_mode` automatically makes `W292` honor theme-registered floors while preserving static non-instantiation (`tests/test1/test_form_button_checks.py:713-724`).
- **Autouse test isolation in `tests/test1/conftest.py`:** `tests/test1/conftest.py:23-33` currently resets `label_mode._warned` via `isolate_label_mode_warnings`, and `tests/test1/test_button_classes.py:94-101` isolates `_THEME_BUTTON_CLASSES` locally. Adding an autouse fixture in `tests/test1/conftest.py` to snapshot/rebind `_THEME_LABEL_MODE_DEFAULTS` prevents cross-test leakage across `pytest-xdist` workers.

### 3. Concerns
- None identified. All prior concerns (`H02`, `A02`, `A16`, `A17`, `A18`, `C3-A03`) are fully resolved in the task specifications.

### 4. Suggestions
- Export `register_label_mode_defaults` in `src/crud_views/lib/view/label_mode.py` alongside `default_label_mode` and `LABEL_MODE_DEFAULTS` so theme `AppConfig.ready()` hooks have a single canonical import module.

### 5. Risk Assessment
**LOW** — The change extends `src/crud_views/lib/view/label_mode.py` using the same layering model already proven in `src/crud_views/lib/button_classes.py:135-151`, with atomic validation and copy-on-write rebinding under a lock.

---

## 06.6-03

### 1. Summary
Plan `06.6-03` adds the empty-default `form:actions` and `form:filter-actions` utility keys to `DEFAULT_BUTTON_CLASSES` (`src/crud_views/lib/button_classes.py:15-113`), wires them into the three default action-group constructors (`CrispyFormMixin.get_form_actions` at `src/crud_views/lib/crispy/form.py:55-56`, `CrispyDeleteForm.helper` at `src/crud_views/lib/crispy/form.py:141-144`, and `ListViewFilterFormHelper.get_form_actions` at `src/crud_views/lib/views/list.py:125-133`), provides a scoped bridge for `crispy-bootstrap5==2023.10`, and updates the key inventory from 86 to 88 in `tests/test1/test_button_classes.py:21-116` and `docs/reference/buttons.md:151`.

### 2. Strengths
- **Covers all three independent action-group constructors:** `CrispyDeleteForm.helper` (`src/crud_views/lib/crispy/form.py:136-146`) builds its own `FormActions(self.get_delete_button(), self.get_cancel_button())` rather than calling `CrispyFormMixin.get_form_actions()` (`src/crud_views/lib/crispy/form.py:55-56`), and `ListViewFilterFormHelper.get_form_actions()` (`src/crud_views/lib/views/list.py:125-133`) builds the filter group. Updating all three ensures `form:actions` styles both ordinary and delete forms while `form:filter-actions` styles only filter forms.
- **Render-time class resolution compatible with `ListViewFilterFormHelper` caching:** `ListViewFilterFormHelper.render_layout` (`src/crud_views/lib/views/list.py:174-180`) caches `self._cv_actions = self.get_form_actions()` once per `self._cv_prepared` layout and reuses it across renders. Storing the class-table key on `_ThemedFormActions` and resolving `get_button_class(...)` at render time without mutating the authored `css_class` avoids stale or accumulated classes under `register_button_classes` / `override_settings` and survives `copy.deepcopy` in `_cv_prepare_layout` (`src/crud_views/lib/views/list.py:155`).
- **Strict origin/content guard for the `crispy-bootstrap5` 2023.10 floor bridge:** The floor bridge activates only when `template_pack == "bootstrap5"`, the resolved template origin is the installed `crispy_bootstrap5` package's `bootstrap5/layout/formactions.html`, and its content matches the exact 2023.10 template, ensuring custom pack overrides and `crispy_tabler` (`../tabler-test/src/django_tabler/templates/crispy_tabler/layout/formactions.html`) are never shadowed.

### 3. Concerns
- **LOW — `copy.deepcopy` compatibility of `_ThemedFormActions` inside `ListViewFilterFormHelper._cv_prepare_layout`:** If a subclass or caller assigns a layout containing `super().get_form_actions()` before `_cv_prepare_layout()` runs (`src/crud_views/lib/views/list.py:155`), `copy.deepcopy(current)` will copy `_ThemedFormActions`. Because `crispy_forms.bootstrap.FormActions` defines `self.fields` and `self.attrs`, `_ThemedFormActions` must keep its extra state (`_cv_class_key`, base `css_class`) in standard instance attributes or preserve them if `__deepcopy__` is ever customized.

### 4. Suggestions
- In `tests/test1/test_theme_action_groups.py`, include a test that assigns a layout containing `super().get_form_actions()` onto a `ListViewFilterFormHelper` instance before rendering, verifying that `_cv_prepare_layout()`'s `copy.deepcopy` (`src/crud_views/lib/views/list.py:155`) preserves `_ThemedFormActions`'s class-key resolution across `override_settings`.

### 5. Risk Assessment
**LOW** — The key additions in `src/crud_views/lib/button_classes.py` are empty strings by default (preserving all existing goldens), and the 2023.10 floor bridge is strictly gated by pack name, resolved origin path, and exact template source.

---

## 06.6-04

### 1. Summary
Plan `06.6-04` adds `alert:dismissible` (`"alert-dismissible fade show"`) and `alert:close` (`"btn-close"`) to `DEFAULT_BUTTON_CLASSES` (`src/crud_views/lib/button_classes.py:91-96`), replaces the hardcoded dismissal and close-button classes in `src/crud_views/templates/crud_views/tags/alert.html:2,5`, and updates the key inventory from 84 to 86 in `tests/test1/test_button_classes.py:21-116` and `docs/reference/buttons.md:151`.

### 2. Strengths
- **Byte-for-byte preservation of unconfigured alert output:** `tests/test1/test_alerts.py:166-181` (`test_dismissible_alert_golden`) compares `markup.encode("utf-8")` directly against `tests/test1/golden/alerts/dismissible.html:1-7` with no whitespace normalization. Resolving `{% cv_button_class "alert" "dismissible" as dismissible_class %}` in `src/crud_views/templates/crud_views/tags/alert.html:2` and emitting a leading space only when `alert.dismissible and dismissible_class` is non-empty keeps the default render byte-identical to `tests/test1/golden/alerts/dismissible.html` while producing clean `class="alert alert-success"` when `alert:dismissible` is `""` or `None`.
- **Automatic `W362` validation without mode suffixes:** In `src/crud_views/lib/button_classes.py:251-275,328-346`, `_action_key_parts` only allows three-segment `:mode` suffixes for `VARIANT_LOCATIONS` (`context`, `list`, `card`) and `form:<FORM_KINDS>`. Adding `alert:dismissible` and `alert:close` to `DEFAULT_BUTTON_CLASSES` automatically permits the base keys while flagging `alert:close:icon` and `alert:dismissible:both` with `crud_views.W362`.
- **Synchronized key count in Wave 1:** Updating `EXPECTED_KEYS` and `assert len(EXPECTED_KEYS) == 86` in `tests/test1/test_button_classes.py:105` together with `The default table has 86 keys` in `docs/reference/buttons.md:151` keeps `test_default_table_is_complete` and `test_documented_default_key_count_matches_table` (`tests/test1/test_button_classes.py:104-116`) green before Plan `06.6-03` advances the count to 88 in Wave 2.

### 3. Concerns
- None identified. Prior concerns `H04` and `A03` are completely addressed.

### 4. Suggestions
- Keep the newline and indentation structure of `src/crud_views/templates/crud_views/tags/alert.html:1-6` identical when introducing `{% cv_button_class "alert" "dismissible" as dismissible_class %}` (e.g., on line 1 alongside `{% load crud_views i18n %}`) so the leading newline on line 1 of `tests/test1/golden/alerts/dismissible.html` is preserved.

### 5. Risk Assessment
**LOW** — Touching two lines in `src/crud_views/templates/crud_views/tags/alert.html` and two entries in `src/crud_views/lib/button_classes.py` is minimal and directly guarded by `tests/test1/test_alerts.py` and `tests/js/adapters.test.js`.

---

## 06.6-05

### 1. Summary
Plan `06.6-05` routes full-page workflow forms (`src/crud_views_workflow/templates/crud_views_workflow/view_workflow.action.html:1-19`) through `{% cv_render_form %}`, verifies single-form/single-CSRF-token ownership and enforced-CSRF POST behavior across all five actionable view types (create, update, custom form, delete, workflow) and parent formsets, and removes the two redundant `form_tag = False` helper overrides in `tests/test1/app/views_formset.py:44-50` and `examples/bootstrap5/formsets/views.py:37-41`.

### 2. Strengths
- **Fixes the workflow bypass in `view_workflow.action.html`:** `src/crud_views_workflow/templates/crud_views_workflow/view_workflow.action.html:8-16` currently wraps `{% crispy form form.helper %}` inside `<form class="cv-form" method="post" novalidate>{% csrf_token %}`. Replacing `{% crispy form form.helper %}` on line 15 with `{% cv_render_form %}` and removing `{% load crispy_forms_tags %}` on line 2 brings workflow pages onto the same single-helper/single-token boundary as stock CRUD forms.
- **Accurate distinction between full-page and modal workflow templates:** `WorkflowView` (`src/crud_views_workflow/lib/views.py:18-28`) subclasses `CustomFormView` (`src/crud_views/lib/views/form.py:10-21`), setting `template_name = "crud_views_workflow/view_workflow.html"` for full pages while inheriting `cv_content_template = "crud_views/view_custom_form.content.html"` and `cv_modal_supported = True` for modal partials (`src/crud_views/templates/crud_views/modal/content.html:8`). Task `05-01` accurately tests both paths and their distinct template origins without altering `WorkflowView.cv_content_template`.
- **Restores static `W292` coverage on formset parent forms:** `_static_form_controls` (`src/crud_views/lib/view/buttons.py:511-514`) skips any form where `_inherits(form_class, "helper", CrispyFormMixin)` is `False`. Removing the redundant `helper` properties in `PublisherFormSetForm` (`tests/test1/app/views_formset.py:44-50`) and `QuestionnaireForm` (`examples/bootstrap5/formsets/views.py:37-41`) (and the unused `from crispy_forms.helper import FormHelper` import at `examples/bootstrap5/formsets/views.py:4`) restores static `W292` inspection for those forms.

### 3. Concerns
- None identified. Prior concerns (`H03`, `H09`, `H10`, `A04`, `A11`, `A12`, `A13`, `C2-A01`, `C2-A05`, `C3-A01`) are cleanly resolved.

### 4. Suggestions
- When removing `QuestionnaireForm.helper` in `examples/bootstrap5/formsets/views.py:37-41`, remember to remove `from crispy_forms.helper import FormHelper` on line 4 of `examples/bootstrap5/formsets/views.py` so `ruff check src tests examples` in Plan `06.6-09` does not flag `F401`.

### 5. Risk Assessment
**LOW** — The template change in `src/crud_views_workflow/templates/crud_views_workflow/view_workflow.action.html` is a two-line replacement, and the test matrix thoroughly covers full-page, modal, parent-formset, plain-form, and polymorphic create-select flows.

---

## 06.6-06

### 1. Summary
Plan `06.6-06` builds the Django-free, import-pure provenance and verification CLI `tests/browser/theme_adoption_sources.py` (with unit tests in `tests/browser/test_theme_adoption_sources.py`) and captures the unmodified baseline of `../tabler-test` (`885dfc791a150fdc715d6fb34c2e6181d6b92f3c`) against an isolated archive of pre-phase core revision `cb26af4dfef2afb31d774a219abfad1c675cdff1` into `06-companion-baseline.json`.

### 2. Strengths
- **Complete tree-bound override and behavior accounting (D-18 / C4-A01):** Rather than relying on a hardcoded four-template list or self-reported counts, `06-01` enumerates the entire tracked archive of `../tabler-test` at `885dfc791a150fdc715d6fb34c2e6181d6b92f3c` — covering all eight `crud_views/` template shadows (`tags/alert.html`, `snippets/form_frame.html`, `tags/list_filter.html`, `tags/list_filter.inner.html`, `modal/shell.html`, `table/bootstrap5.html`, `tags/card.html`, `view_card.content.html`), `crud_views_tabler/page.html`, `django_tabler` pack templates (`crispy_tabler/field.html`, `crispy_tabler/layout/help_text_and_errors.html`, `crispy_tabler/layout/formactions.html`, etc.), and bespoke Python behavior (`check_tabler_icons` in `../tabler-test/src/crud_views_tabler/checks.py:8-27`, `render` in `../tabler-test/src/crud_views_tabler/icons.py:50-52`).
- **Strict verification of replay and delivered companion state (`C5-H01`, `C5-A01`, `C5-A08`):** `--verify-replay` and `--delivered-source` validate the concrete adoption values (`register_label_mode_defaults({"form": "both"})`, `save`/`cancel`/`filter-reset` icon mappings, the 4 class keys in `TABLER_BUTTON_CLASSES` and `ButtonClassTests.test_table_values`), full tree hashes, preserved dirty `example/config/settings.py` bytes, and repository-qualified commit receipts via `git -C`.

### 3. Concerns
- **LOW — Companion test-runner parallel flags (`-n 4` and `--parallel 4`) vs. installed companion dependencies:** In `../tabler-test/pyproject.toml:32`, the `test` dependency group declares `test = ["pytest", "pytest-django", "crispy-bootstrap5==2026.9"]` without `pytest-xdist`, and `06.6-RESEARCH.md` ("Runtime availability addendum") explicitly observed that `xdist` was absent in `/home/alex/projects/alex/tabler-test/.venv/bin/python`. While `06-01` and `06-02` properly include a dependency preflight that halts if required dependencies are missing, requiring `-n 4` unconditionally on `../tabler-test`'s `pytest` invocation will trigger that halt unless `pytest-xdist` is either present or `pytest tests -q` (for a tiny companion `tests/` directory, per `AGENTS.md:89-91`'s allowance for serial execution on tiny selections or concrete environment constraints) is used when `xdist` is not installed in the companion venv.

### 4. Suggestions
- In `tests/browser/theme_adoption_sources.py`, check whether `../tabler-test`'s `tests/` suite is a small unit suite and, if `xdist` is absent in `/home/alex/projects/alex/tabler-test/.venv/bin/python`, either document the exact serial fallback reason per `AGENTS.md:89-91` (avoiding an unnecessary package-install gate for an undeclared dependency of `../tabler-test/pyproject.toml:32`) or trigger the blocking human package-legitimacy checkpoint before installing `pytest-xdist`.

### 5. Risk Assessment
**LOW** — The provenance tool is pure stdlib Python with comprehensive negative unit tests in `tests/browser/test_theme_adoption_sources.py`, and baseline capture operates strictly on temporary archives without touching live worktrees.

---

## 06.6-07

### 1. Summary
Plan `06.6-07` implements the isolated real-Tabler HTTP/Chromium acceptance suite (`tests/browser/theme-adoption.cjs`, `tests/browser/theme_adoption_server.py`, `tests/browser/theme-adoption-config.test.cjs`), applies the candidate Tabler theme adaptations in isolated copies, verifies all eight browser case families (`owned-form`, `csrf-post`, `label-floor`, `action-groups`, `alert-dismiss`, `modal-replace`, `conditional-formset`, `cancel-navigation`) plus companion test suites, and exports/replays `07-tabler-adaptation.patch`.

### 2. Strengths
- **Complete resolution of `C5-H01` (`form="both"` + native Tabler icon mappings):** In `src/crud_views/lib/icons.py:51-53`, `DEFAULT_ICONS` maps `"save": "far:floppy-disk"`, `"cancel": "fas:xmark"`, and `"filter-reset": "fas:rotate-left"`, whereas `../tabler-test/src/crud_views_tabler/icons.py:12-47` (`TABLER_ICONS`) currently omits those three keys. Without mapping them in `TABLER_ICONS`, registering `{"form": "both"}` in `CrudViewsTablerConfig.ready()` (`../tabler-test/src/crud_views_tabler/apps.py:15-31`) would render Font Awesome `<i class="...">` tags on form buttons and fail both `TablerIconTests.test_every_upstream_icon_name_is_mapped` (`../tabler-test/src/crud_views_tabler/tests.py:62-67`) and `ThemeRenderingTests.test_list_uses_tabler_table_and_icons` (`../tabler-test/src/crud_views_tabler/tests.py:175`). Adding `"save": "tabler:check"`, `"cancel": "tabler:arrow-left"`, and `"filter-reset": "tabler:filter-x"` to `TABLER_ICONS` and testing all five form kinds (`submit`, `delete`, `cancel`, `filter-submit`, `filter-reset`) across `both`, `icon`, and `label` modes resolves this completely.
- **Complete resolution of `C5-A08` (`ButtonClassTests.test_table_values` synchronization):** `../tabler-test/src/crud_views_tabler/tests.py:98-140` asserts exact dict equality `self.assertEqual(TABLER_BUTTON_CLASSES, expected)` against all 39 existing entries of `../tabler-test/src/crud_views_tabler/buttons.py:3-44`. Synchronizing those exact 4 new keys (`form:actions`, `form:filter-actions`, `alert:dismissible`, `alert:close`) in both `buttons.py` and `tests.py` keeps full dictionary equality intact.
- **Clean handling of `MessagesParityTests` (`C4-A02`):** `../tabler-test/src/crud_views_tabler/templates/crud_views/tags/alert.html:7,17` currently hardcodes `alert-dismissible fade show`, `btn-close`, and `data-bs-dismiss="alert"`, and `MessagesParityTests.test_plain_include_matches_cv_messages` (`../tabler-test/src/crud_views_tabler/tests.py:556-573`) compares `django_tabler/includes/messages.html` with `{% cv_messages %}`. Updating `crud_views_tabler`'s `alert.html` to consume `alert:dismissible`, `alert:close`, and `data-cv-alert-dismiss` while updating `MessagesParityTests` to assert the single intentional hook delta (`data-bs-dismiss="alert"` on standalone `django_tabler` vs. `data-cv-alert-dismiss` on `crud_views_tabler`) preserves standalone `django_tabler` independence and full markup parity.

### 3. Concerns
- **LOW — Pre-existing `test_delete_form_is_the_stock_crispy_delete_form` baseline failure in `../tabler-test/src/crud_views_tabler/tests.py:320-325`:** Line 323 of `../tabler-test/src/crud_views_tabler/tests.py` asserts `self.assertRegex(html, r'<input type="submit"[^>]*class="btn btn-danger"')`, which predates Phase 6's `<input>` -> `<button>` migration (`src/crud_views/templates/crud_views/tags/button/form.html:2`). Because `07-03` compares failing node IDs against `06-companion-baseline.json`, this pre-existing failure is properly accounted for by `06-02` (while `TablerIconTests.test_every_upstream_icon_name_is_mapped` at `tests.py:62-67` transitions from failing at baseline to passing in candidate/replay), provided `--verify-replay` allows baseline failures to transition to passing while forbidding any passing baseline test from regressing.

### 4. Suggestions
- Ensure `--verify-replay` in `tests/browser/theme_adoption_sources.py` checks `candidate_failures <= baseline_failures` (subset, not set equality) so that fixing `TablerIconTests.test_every_upstream_icon_name_is_mapped` (`../tabler-test/src/crud_views_tabler/tests.py:62-67`) via the new `TABLER_ICONS` entries is recognized as an improvement rather than a mismatch.

### 5. Risk Assessment
**LOW** — Every companion file touched (`apps.py`, `buttons.py`, `icons.py`, `templates/crud_views/tags/alert.html`, `tests.py`) has been verified line-by-line against the embedded `../tabler-test` source at `885dfc791a150fdc715d6fb34c2e6181d6b92f3c`.

---

## 06.6-08

### 1. Summary
Plan `06.6-08` updates `docs/reference/theme.md`, `docs/reference/action_menus.md`, `docs/reference/settings.md`, `docs/migrating-1.0.md`, and `CHANGELOG.md` with executable adoption and migration recipes (`tests/test1/test_theme_adoption_docs.py` and `tests/test1/test_label_mode_docs.py`) covering `register_label_mode_defaults`, page-owned forms (`cv_form_helper`, `form_tag=False`), standalone `CrispyModelForm` wrapper migration, `form:actions` / `form:filter-actions` opt-in, and `alert:dismissible` / `alert:close`.

### 2. Strengths
- **Preserves strict structural guards in `test_label_mode_docs.py` and `test_alerts.py`:**
  - `tests/test1/test_alerts.py:249-255` (`_documented_alert_frame`) asserts that `### Custom alert frame` in `docs/reference/theme.md:308-321` contains `assert len(bodies) == 1` `django`/`html` code fence. Task `08-01` explicitly preserves that single fence and runs `tests/test1/test_alerts.py`.
  - `tests/test1/test_label_mode_docs.py:190-223` and `709-717` assert the exact numbered step count under `### Context label-mode resolution`, `### List label-mode resolution`, `### Card label-mode resolution`, and `### Form label-mode resolution` in `docs/reference/action_menus.md`. Describing the three floor layers (`package -> theme -> project setting`) inside the existing floor step preserves those step counts.
  - `tests/test1/test_label_mode_docs.py:777-816` (`test_migration_e108_location_inventory`) asserts the exact wording of the `E108` paragraph in `docs/migrating-1.0.md:61-64`; deferring that paragraph's edit to `08-02` alongside `test_migration_e108_location_inventory` keeps `test_label_mode_docs.py` passing at both `08-01` and `08-02`.

### 3. Concerns
- **LOW — Exact phrase assertions in `tests/test1/test_label_mode_docs.py:166-178` and `715-717`:** In `tests/test1/test_label_mode_docs.py:166-178`, `test_label_mode_configuration_table` checks exact substrings in `docs/reference/settings.md`'s `### Label-mode configuration` section, and line `716` checks `assert '`default_label_mode("form")`' in mode[1] and '`"label"`' in mode[1]` in `docs/reference/action_menus.md`. When `08-01` updates `settings.md` and `action_menus.md` to include `register_label_mode_defaults`, it must retain those substrings or update the corresponding assertions in `tests/test1/test_label_mode_docs.py` in the same task (`08-01` already lists `tests/test1/test_label_mode_docs.py` in `<files>`).

### 4. Suggestions
- In `08-01`, keep the existing substring markers required by `tests/test1/test_label_mode_docs.py:166-178,715-717` intact while extending `tests/test1/test_label_mode_docs.py` to assert the presence of `crud_views.lib.view.label_mode.register_label_mode_defaults` and the `theme -> package` fallback order.

### 5. Risk Assessment
**LOW** — Both documentation test suites (`test_theme_adoption_docs.py`, `test_label_mode_docs.py`, `test_alerts.py`, `test_form_button_docs.py`) and `mkdocs build --strict` run directly in the task verification steps.

---

## 06.6-09

### 1. Summary
Plan `06.6-09` runs the integrated verification gates across the supported cached Django 4.2/5.2 runtimes, both cached `crispy_floor` runtimes (Django 4.2 and 6.0), the `examples/bootstrap5` pytest suite, Vitest unit and integration lanes, Playwright browser preservation harnesses, `mkdocs build --strict`, and `ruff`, updates `noxfile.py:28-52` (`CRISPY_FLOOR_TESTS`), validates all upstream/delivered companion evidence via `--check-final`, and writes `06.6-PUBLIC-SURFACE.md`, `06.6-ACCEPTANCE.md`, and `06.6-VALIDATION.md`.

### 2. Strengths
- **Permanent `CRISPY_FLOOR_TESTS` synchronization in `noxfile.py`:** `noxfile.py:28-52` explicitly enumerates the test files run by the `crispy_floor` session. Appending the five new `tests/test1/test_theme_*.py` modules plus `tests/test1/test_alerts.py` and `tests/test1/test_button_classes.py` and guarding that list via an AST test in `tests/browser/test_theme_adoption_sources.py` ensures floor regressions are caught in CI/nox runs going forward.
- **Comprehensive cross-repo and workflow-branch checks in `--check-final`:** `09-01` verifies that `10-companion-delivery.json`, `07-tabler-replay.json`, `07-browser-results.json`, and `06-companion-baseline.json` agree on full tree hashes, concrete `form="both"` + 3 icon mappings + 4 class keys, `ButtonClassTests.test_table_values` and `ThemeAdoptionTests` results, workflow modal vs. full-page template origins, and repository-qualified commit receipts.

### 3. Concerns
- None identified. All prior findings (`H12`, `A07`, `A09`, `A15`, `C2-A03`, `C3-A01`, `C4-A01`, `C4-A02`, `C5-H01`, `C5-A01`, `C5-A08`) are incorporated with concrete verification commands.

### 4. Suggestions
- When running the sequential browser harnesses (`modal-focus.cjs`, `conditional-formsets.cjs`, `theme-adoption.cjs`), confirm each process exits cleanly before starting the next so loopback ports remain free.

### 5. Risk Assessment
**LOW** — This plan is a verification and documentation handoff gate that fails closed if any upstream artifact, commit receipt, or test suite is missing or stale.

---

## 06.6-10

### 1. Summary
Plan `06.6-10` delivers the verified adaptation patch from Plan `06.6-07` into the live `../tabler-test` companion checkout (`apps.py`, `buttons.py`, `icons.py`, `templates/crud_views/tags/alert.html`, `tests.py`, and conditional `formactions.html`), verifies the delivered tree and focused test/browser probes in isolation, creates a scoped local commit in `../tabler-test` using a temporary `GIT_INDEX_FILE` that preserves `example/config/settings.py` and any unrelated staged/unstaged changes, and commits `10-companion-delivery.json` and `07-TABLER-HANDOFF.md` in the core repository.

### 2. Strengths
- **Sound multi-repository commit protocol (`C5-A01`) aligned with `gsd-executor`:**
  - The installed `gsd-executor` contract measures `COMMITS_ACTUAL=$(git rev-list --count ${PLAN_HEAD_BEFORE}..HEAD)` in the core repository (`<task_commit_protocol>` step `0c` and `<summary_creation>`) and halts if code changes are uncommitted or if `COMMITS_ACTUAL` is `0` when core files changed.
  - By grouping `10-01` and `10-02` into one shared explicit commit in `../tabler-test` (via `git -C "$COMPANION_ROOT"`) and making `10-03` commit `10-companion-delivery.json` and `07-TABLER-HANDOFF.md` in the core repository (`COMMITS_ACTUAL = 1` in core), the plan satisfies `gsd_run check evaluation-scope --plan 06.6-10 --commits-only --raw` and `SUMMARY.md` ledger measurement without passing `../tabler-test` paths to core `git add`.
- **Byte-for-byte preservation of dirty `example/config/settings.py` and live Git index:** Using a temporary `GIT_INDEX_FILE` seeded from `git -C "$COMPANION_ROOT" read-tree "$COMPANION_HEAD_BEFORE"` plus `git apply --cached` for the commit, followed by a second temporary index copy with `git apply --cached --3way` installed under `index.lock`, guarantees that only the replay-approved task hunks enter the companion commit while any unrelated staged or unstaged edits (including `example/config/settings.py`) remain untouched.
- **Synchronized source and test boundary (`10-01` + `10-02`):** Delivering `apps.py`, `buttons.py`, and `icons.py` in `10-01` and `alert.html` + `tests.py` in `10-02` before creating the single companion commit ensures `ButtonClassTests.test_table_values` (`../tabler-test/src/crud_views_tabler/tests.py:98-140`), `TablerIconTests.test_every_upstream_icon_name_is_mapped` (`tests.py:62-67`), and `MessagesParityTests` (`tests.py:556-573`) are never committed out of sync with `TABLER_BUTTON_CLASSES` (`buttons.py:3-44`) or `TABLER_ICONS` (`icons.py:12-47`).

### 3. Concerns
- **LOW — `<task type="tracer">` on `10-01` (`06.6-10-PLAN.md:107`) vs. shared `10-01`/`10-02` commit boundary:** In the installed `gsd-executor` contract (`<execution_flow>` -> `execute_tasks` step 2), a `type="tracer"` task normally commits before running the tracer feedback gate. `06.6-10-PLAN.md:59-64,126-128` explicitly overrides this by instructing the executor *not* to commit after `10-01` (since `tests.py` is updated in `10-02`) and instead to run the `10-01` `<verify>` probe (`--delivered-source ../tabler-test --case label-floor`) as the tracer gate and commit `10-01` + `10-02` together at the end of `10-02`. The executor must follow the plan prose (`06.6-10-PLAN.md:59-64,126-128`) rather than attempting a companion commit at the end of `10-01`.

### 4. Suggestions
- During execution of `10-01`, treat `<verify>` (`node tests/browser/theme-adoption.cjs --delivered-source ../tabler-test --case label-floor ...`) as the tracer feedback gate and defer the companion `git commit` until `10-02`'s `--delivered-source` provisional check passes, exactly as specified in `06.6-10-PLAN.md:59-64`.

### 5. Risk Assessment
**LOW** — The temporary-index commit protocol, preservation digests, and `--require-committed` verification provide strong safeguards against accidental index pollution or unverified companion changes.

---

## Cross-Plan Comparison & Cycle 6 Convergence Assessment

### Verification of Cycle 5 Focus Areas (`C5-H01`, `C5-A01`, `C5-A08`)
| Focus Area | Status | Source & Plan Evidence |
|---|---|---|
| **C5-H01**: Concrete `form="both"`, native Tabler `save`/`cancel`/`filter-reset` mappings, 5 action kinds in 3 modes + reset/cancel checks across candidate, replay, and delivery | **RESOLVED** | `src/crud_views/lib/icons.py:51-53` defines `save`, `cancel`, `filter-reset`; `../tabler-test/src/crud_views_tabler/icons.py:12-47` lacked them. Plans `06.6-06` (`06-01`), `06.6-07` (Artifacts, `07-02`, `07-03`), `06.6-09` (`09-01`), and `06.6-10` (`10-01`, `10-02`) now register `{"form": "both"}` in `apps.py`, map `save: tabler:check`, `cancel: tabler:arrow-left`, `filter-reset: tabler:filter-x` in `icons.py`, and verify all 5 kinds across `both`/`icon`/`label` plus native reset and cancel navigation. |
| **C5-A01**: Explicit companion shared commit for `10-01`/`10-02`, core evidence commit for `10-03`, preserving unrelated index/worktree under `gsd-executor` contract | **RESOLVED** | `06.6-10-PLAN.md:51-105` defines a temporary-index (`GIT_INDEX_FILE`) protocol using `git -C "$COMPANION_ROOT"` for the shared `10-01`/`10-02` companion commit and core Git for `10-03` (`10-companion-delivery.json`, `07-TABLER-HANDOFF.md`), keeping core `COMMITS_ACTUAL` non-zero and preserving `example/config/settings.py` and any staged hunks. |
| **C5-A08**: Exact companion `TABLER_BUTTON_CLASSES` dictionary synchronized in `ButtonClassTests.test_table_values` | **RESOLVED** | `../tabler-test/src/crud_views_tabler/tests.py:98-140` asserts full dictionary equality against `../tabler-test/src/crud_views_tabler/buttons.py:3-44`. Plans `06.6-06`, `06.6-07`, `06.6-09`, and `06.6-10` synchronize the 4 new keys (`form:actions`, `form:filter-actions`, `alert:dismissible`, `alert:close`) in `tests.py` and run `ButtonClassTests.test_table_values` as a required gate. |

### Overall Risk Assessment
**LOW (0 HIGH, 0 MEDIUM, 4 LOW execution notes)** — All ten plans (`06.6-01` through `06.6-10`) are internally consistent, accurately grounded in both the core repository and the embedded `../tabler-test` companion source (`885dfc791a150fdc715d6fb34c2e6181d6b92f3c`), and ready for execution.
