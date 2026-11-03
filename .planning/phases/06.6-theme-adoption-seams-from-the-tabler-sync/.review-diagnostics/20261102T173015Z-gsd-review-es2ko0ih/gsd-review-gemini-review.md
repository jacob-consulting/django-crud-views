## 06.6-01

### 1. Summary
Plan `06.6-01` establishes single-form and single-CSRF-token ownership on stock create pages by setting `form_tag = False` on the library helpers (`CrispyFormMixin.helper` and `CrispyDeleteForm.helper`), selecting and adapting `form.helper` once in `cv_render_form` (`cv_form_helper` with render-local CSRF suppression), and diagnosing `form_tag=True` (unconditional error) vs. unused outer-form wrapper attributes (warning in non-strict mode, error in strict mode). While the core mechanism directly addresses the double-`<form>` and double-CSRF bug in the current codebase, landing it in Wave 1 without updating two existing test files (`tests/test1/test_form_button_checks.py` and `tests/test1/test_form_frame.py`) will immediately break existing tests in Wave 1.

### 2. Strengths
- **Fixes double helper allocation and implicit wrapping in `tags/form.html`:** `src/crud_views/templates/crud_views/tags/form.html:3-6` currently evaluates `form.helper` twice (`{% if form.helper %}` then `{% crispy form form.helper %}`), which invokes `@property def helper` in `src/crud_views/lib/crispy/form.py:43-50` and `136-146` twice per render and falls back to `{% crispy form %}` (creating a default `FormHelper` with `form_tag=True`) when `form.helper` is absent or falsey. Resolving `cv_form_helper` once by presence/identity in `src/crud_views/templatetags/crud_views.py:464-466` eliminates both defects.
- **Handles inner CSRF emission independently of `form_tag`:** `src/crud_views/templates/crud_views/view_create.content.html:5-11` already owns `<form class="cv-form" method="post" ...>` and `{% csrf_token %}`. Because `crispy-bootstrap5` emits `{% csrf_token %}` whenever `form_method|lower == 'post' and not disable_csrf` regardless of `form_tag`, suppressing CSRF on the render-local helper is necessary to eliminate the duplicate token shown in `tests/test1/golden/form_frame/create.html:1`.
- **Clean separation between D-01 and D-03/D-04 diagnostics:** Unconditionally rejecting `form_tag=True` while inspecting raw `_form_action`, `form_id`, `attrs`, `form_class`, and non-default `form_method` avoids calling `reverse()` on unresolvable action strings and leaves `ListViewFilterFormHelper` (`form_method = "GET"`, `form_tag = False` at `src/crud_views/lib/views/list.py:93-94`, rendered via `{% crispy filter.form filter.form.helper %}` in `src/crud_views/templates/crud_views/tags/list_filter.inner.html:15`) untouched.

### 3. Concerns
- **[HIGH] Immediate breakage of `tests/test1/test_form_button_checks.py` in Wave 1:** `tests/test1/test_form_button_checks.py:560-567` (`_CustomHelperForm`) and `578-585` (`_DeleteCustomHelper`) instantiate `helper = FormHelper()` without setting `helper.form_tag = False`. Both forms are rendered through `/author/create/` and `/author/{pk}/delete/` (which call `{% cv_render_form %}`) in `test_custom_submit_hooks_follow_the_runtime_policy` (`tests/test1/test_form_button_checks.py:1082-1095`) and `test_custom_delete_helper_follows_the_runtime_policy` (`1097-1111`). Once `06.6-01` makes `cv_render_form` raise `ImproperlyConfigured` for `form_tag=True` in both strict modes, both tests will fail (raising `ImproperlyConfigured` instead of `ValueError(match="form button ...")` in strict mode, and raising instead of returning HTTP 200 in non-strict mode). Because `06.6-02` (also Wave 1) runs `pytest ... tests/test1/test_form_button_checks.py`, Wave 1 verification will fail.
- **[HIGH] Wave-ordering split leaves `tests/test1/test_form_frame.py` broken after Wave 1:** `tests/test1/test_form_frame.py:71-73` (`test_stock_markup_unchanged`) renders `crud_views/view_create.content.html`, `view_update.content.html`, `view_custom_form.content.html`, and `view_delete.content.html` (all of which call `{% cv_render_form %}`) using `NameForm` (a plain `forms.Form` with no `.helper` at `tests/test1/test_form_frame.py:34-35`). As soon as `06.6-01` changes `cv_render_form` and `tags/form.html` in Wave 1, the inner `<form method="post" ><input type="hidden" name="csrfmiddlewaretoken" value="CSRF">` in `tests/test1/golden/form_frame/{create,update,custom_form,delete}.html:1` disappears, breaking `test_form_frame.py` until Plan `06.6-05` runs in Wave 2.
- **[MEDIUM] `context.flatten()` in `cv_render_form` vs. `Context.dicts` owner lookup:** `src/crud_views/templatetags/crud_views.py:465-466` currently calls `render_to_string(..., context.flatten())`. In `src/crud_views/lib/crispy/buttons.py:44-77`, `_cv_helper_tier` and `_cv_page_tier` walk `context.dicts` and skip any dict matching `_is_response_overlay(layer)` (`layer.keys() >= {"is_formset", "template_pack", "inputs"}` and method key). Rendering `tags/form.html` via `get_template(...).template.render(context)` inside `with context.push(cv_form_helper=helper):` (matching `cv_alert` at `src/crud_views/templatetags/crud_views.py:453-455`) preserves the `Context.dicts` stack instead of collapsing all layers into one dict.
- **[LOW] Redundant `helper` overrides on formset parent forms suppress static W292:** `tests/test1/app/views_formset.py:44-50` (`PublisherFormSetForm.helper`) and `examples/bootstrap5/formsets/views.py:36-41` (`QuestionnaireForm.helper`) override `helper` solely to set `h.form_tag = False` on `super().helper`. Because `_static_form_controls` in `src/crud_views/lib/view/buttons.py:511` checks `_inherits(form_class, "helper", CrispyFormMixin)`, those workarounds become redundant once `CrispyFormMixin.helper` sets `form_tag = False` and currently prevent static W292 inspection on those forms.

### 4. Suggestions
- Update `_CustomHelperForm` (`tests/test1/test_form_button_checks.py:565`) and `_DeleteCustomHelper` (`tests/test1/test_form_button_checks.py:583`) to set `helper.form_tag = False` inside Plan `06.6-01` (and add a dedicated test in `test_theme_form_ownership.py` for `form_tag=True` rejection on endpoints).
- Either move the four `tests/test1/golden/form_frame/{create,update,custom_form,delete}.html` updates into `06.6-01` (since `06.6-01` is the plan that changes their output) or explicitly document that `test_form_frame.py` is expected to fail between `06.6-01` and `06.6-05`.
- Use `get_template(f"{crud_views_settings.theme_path}/tags/form.html")` with `with context.push(cv_form_helper=helper):` in `cv_render_form` (`src/crud_views/templatetags/crud_views.py:465-466`) instead of `context.flatten()`.

### 5. Risk Assessment
**MEDIUM** — The render-local helper adaptation for custom `FormHelper` subclasses (slots, custom `__copy__`, overridden `get_attributes`/`render_layout`) and the unaddressed Wave 1 test breakages in `tests/test1/test_form_button_checks.py` and `tests/test1/test_form_frame.py` require careful handling during execution.

---

## 06.6-02

### 1. Summary
Plan `06.6-02` introduces `register_label_mode_defaults(defaults)` in `src/crud_views/lib/view/label_mode.py`, adding a validated theme floor between `LABEL_MODE_DEFAULTS` and `CRUD_VIEWS_LABEL_MODE_DEFAULTS` (`package → theme → project setting`) while preserving explicit button/view label modes, `override_settings` responsiveness, `E108` settings validation, and `W292` missing-icon checks. The design aligns tightly with the existing resolver architecture in `label_mode.py` and `buttons.py`.

### 2. Strengths
- **Zero-churn integration with `W292` and action resolvers:** Both `cv_context_action_checks` (`src/crud_views/lib/view/buttons.py:435`) and `cv_form_icon_mode_checks` (`src/crud_views/lib/view/buttons.py:570`) already resolve modes through `cls.cv_get_action_label_mode(...)`, which delegates to `default_label_mode(location)` (`src/crud_views/lib/view/label_mode.py:86-120`) and `form_label_mode()` (`label_mode.py:122-146`). Adding the theme layer inside `default_label_mode()` automatically propagates to both render-time button resolution and static `viewset.W292` checks without instantiating forms.
- **Atomic validation before mutation:** Validating all keys against `LOCATIONS` (`src/crud_views/lib/view/button_data.py`) and values against `is_label_mode()` (`src/crud_views/lib/view/label_mode.py:35-36`) before updating `_THEME_LABEL_MODE_DEFAULTS` guarantees that a partially invalid dict leaves prior registrations intact (D-06).
- **Autouse test isolation in `tests/test1/conftest.py`:** Adding a snapshot/restore fixture for `_THEME_LABEL_MODE_DEFAULTS` alongside `isolate_label_mode_warnings` (`tests/test1/conftest.py:23-33`) prevents cross-test state pollution under `pytest-xdist`.

### 3. Concerns
- **[HIGH] Task `02-02` `<verify>` runs `tests/test1/test_form_button_checks.py`, which breaks when `06.6-01` lands:** Task `02-02` runs `pytest ... tests/test1/test_form_button_checks.py`. As detailed in `06.6-01`, `_CustomHelperForm` (`tests/test1/test_form_button_checks.py:565`) and `_DeleteCustomHelper` (`583`) leave `helper.form_tag = True` and are rendered via `cv_render_form` at lines `1085-1111`. If `06.6-01` runs before `06.6-02` in Wave 1 (or when they merge), `02-02`'s verification command will fail unless those two test helpers in `test_form_button_checks.py` set `helper.form_tag = False`.
- **[LOW] Fallback closure and warning message in `default_label_mode()`:** In `src/crud_views/lib/view/label_mode.py:107,118`, `default_label_mode()` currently passes `lambda: LABEL_MODE_DEFAULTS[location]` as the `fallback` argument to `_invalid_label_mode()` (`label_mode.py:63-84`), which logs `logger.warning("%s, got %r; the %s button uses %r", source, value, location, resolved)`. When updated for D-07, both fallback lambdas (and the missing-setting/missing-key branches at lines `101` and `110`) must resolve `_THEME_LABEL_MODE_DEFAULTS.get(location, LABEL_MODE_DEFAULTS[location])` so the warning log message also reports the effective theme fallback value.
- **[LOW] Re-export and `__all__` consistency:** Check whether `register_label_mode_defaults` should also be mentioned or imported alongside `register_button_classes` (`src/crud_views/lib/button_classes.py:135`) and `register_icons` (`src/crud_views/lib/icons.py`), as Phase 7 (`STAB-01`/`STAB-03`) will verify the documented import path.

### 4. Suggestions
- Coordinate `tests/test1/test_form_button_checks.py` between `06.6-01` and `06.6-02` so `_CustomHelperForm` and `_DeleteCustomHelper` set `helper.form_tag = False`.
- Define a small helper `_theme_or_package_default(location: str) -> str` in `src/crud_views/lib/view/label_mode.py` and use it in all four fallback sites of `default_label_mode()` (`lines 101, 107, 110, 118`).

### 5. Risk Assessment
**LOW** — `src/crud_views/lib/view/label_mode.py` is small (146 lines), self-contained, and already serves as the single source of truth for floor resolution across views, template tags, and `W292` system checks.

---

## 06.6-03

### 1. Summary
Plan `06.6-03` adds the `form:actions` and `form:filter-actions` utility keys (defaulting to `""`) to `DEFAULT_BUTTON_CLASSES`, wires them into the three default action-group constructors (`CrispyFormMixin.get_form_actions`, `CrispyDeleteForm.helper`, and `ListViewFilterFormHelper.get_form_actions`), and introduces a private `_ThemedFormActions` bridge in `src/crud_views/lib/crispy/actions.py` to work around `crispy-bootstrap5==2023.10` ignoring `FormActions(css_class=...)`. However, the plan misses updating `tests/test1/test_button_classes.py`, which hardcodes the 84-key set of `DEFAULT_BUTTON_CLASSES`.

### 2. Strengths
- **Covers all three independent action-group construction sites:** Correctly identifies that `CrispyDeleteForm.helper` (`src/crud_views/lib/crispy/form.py:141-144`) constructs its own `FormActions(self.get_delete_button(), self.get_cancel_button())` rather than calling `CrispyFormMixin.get_form_actions()` (`form.py:55-56`), and that `ListViewFilterFormHelper.get_form_actions()` (`src/crud_views/lib/views/list.py:125-133`) constructs the filter group separately.
- **Scoped bridge for the declared `crispy-bootstrap5==2023.10` floor:** Rather than globally shadowing `bootstrap5/layout/formactions.html` (which would violate D-10/D-17) or bumping the `CRISPY_FLOOR` pin in `noxfile.py:24`, isolating the floor compatibility bridge to a library-local template (`src/crud_views/templates/crud_views/crispy/bootstrap5_formactions.html`) used only when the active Bootstrap 5 pack template drops `formactions.css_class` preserves both floor support and custom pack templates.

### 3. Concerns
- **[HIGH] Omission of `tests/test1/test_button_classes.py` breaks the test suite and skips the doc-count check:** `tests/test1/test_button_classes.py:21-91` hardcodes `EXPECTED_KEYS` and `test_default_table_is_complete()` (`lines 104-106`) asserts `assert len(EXPECTED_KEYS) == 84` and `assert set(DEFAULT_BUTTON_CLASSES) == EXPECTED_KEYS`. Furthermore, `test_documented_default_key_count_matches_table()` lives in `tests/test1/test_button_classes.py:112-116`, **not** in `tests/test1/test_button_classes_checks.py`. Plan `06.6-03` neither lists `tests/test1/test_button_classes.py` in `files_modified` nor runs it in `<verify>`. Consequently, Task `03-02` never actually runs the documented key-count test it claims to verify, and `tests/test1/test_button_classes.py::test_default_table_is_complete` will fail when the full suite runs in Plan `06.6-09`.
- **[HIGH] Render-time resolution, `copy.deepcopy`, and `_action_groups` DOM structure in `ListViewFilterFormHelper`:**
  1. `ListViewFilterFormHelper._cv_prepare_layout()` (`src/crud_views/lib/views/list.py:155`) calls `copy.deepcopy(current)` on layouts, and `render_layout()` (`list.py:174-179`) caches `self._cv_actions = self.get_form_actions()` per prepared layout across repeated renders (`tests/test1/test_crispy_buttons.py:1474-1479`). If `_ThemedFormActions` resolves `get_button_class("form", "filter-actions")` only once in `__init__()` and mutates `self.css_class` on render, repeated renders under `override_settings` or `register_button_classes` will either use stale classes or duplicate classes (violating Task `03-03`'s behavior `"repeated renders do not duplicate classes"`). `_ThemedFormActions` must resolve the table key dynamically per render and combine it with any caller-supplied `css_class` without mutating `self.css_class` in place.
  2. In `tests/test1/test_crispy_buttons.py:1436-1446`, `_action_groups(markup)` asserts that an unconfigured `FormActions` group renders as `<div class="mb-3"><div class="">...</div></div>` (`(div.get("class") or "").split() == ["mb-3"]` and `[child.get("class") for child in div] == [""]`). In `crispy-bootstrap5` (both 2023.10 and 2026.x), `css_class` on `FormActions` is placed on the **outer** `<div{% if formactions.css_class %} class="{{ formactions.css_class }}"{% endif %}>` (or `<div class="mb-3 {{ formactions.css_class }}">` in 2026.x, whereas 2023.10 had `<div class="mb-3">` outer and `<div class="{{ ... }}">` inner). The fallback template `crud_views/crispy/bootstrap5_formactions.html` must match `crispy-bootstrap5 >= 2024`'s exact placement (`mb-3` + `css_class` on the outer `div`, `class=""` on the inner `div` when horizontal is false) so both empty defaults and configured classes behave identically across floor and current packs.
- **[MEDIUM] Static W292 check if `CrispyDeleteForm` overrides `get_form_actions`:** In `src/crud_views/lib/view/buttons.py:504-520`, `_static_form_controls(form_class)` checks `_inherits(form_class, "helper", CrispyDeleteForm)` for `CrispyDeleteForm` and `_inherits(form_class, "helper", CrispyFormMixin) and _inherits(form_class, "get_form_actions", CrispyFormMixin)` for `CrispyFormMixin`. Keep `CrispyDeleteForm.helper` constructing the delete action group (or update `_static_form_controls` if `CrispyDeleteForm` adds `get_form_actions`) so static W292 checks (`tests/test1/test_form_button_checks.py:604-609,744-745`) continue to pass.

### 4. Suggestions
- Add `tests/test1/test_button_classes.py` to `files_modified` and `<verify>` in Plan `06.6-03` (updating `EXPECTED_KEYS` and `assert len(EXPECTED_KEYS) == 88` after `06.6-04` and `06.6-03`).
- In `_ThemedFormActions`, store the class-table slot key (`"actions"` or `"filter-actions"`) and the caller's explicit `css_class` separately on the instance, and compute the effective `css_class` inside `render()` using a temporary copy or context restore so repeated renders and `override_settings` never accumulate or cache stale classes.
- Add `tests/test1/test_crispy_buttons.py` to Task `03-02`'s `<verify>` command so `_action_groups` (`tests/test1/test_crispy_buttons.py:1436-1446`) is verified immediately.

### 5. Risk Assessment
**MEDIUM** — The `_ThemedFormActions` bridge across `crispy-bootstrap5==2023.10` and `2026.x` is well-scoped, but `tests/test1/test_button_classes.py` is currently missed in `files_modified` and `ListViewFilterFormHelper` caches `self._cv_actions` across repeated renders.

---

## 06.6-04

### 1. Summary
Plan `06.6-04` adds `alert:dismissible` (`"alert-dismissible fade show"`) and `alert:close` (`"btn-close"`) to `DEFAULT_BUTTON_CLASSES` in `src/crud_views/lib/button_classes.py` and consumes them in `src/crud_views/templates/crud_views/tags/alert.html`, preserving byte-identical default output (`tests/test1/golden/alerts/dismissible.html`), accessible labels, and `data-cv-alert-dismiss` behavior. Like `06.6-03`, it omits `tests/test1/test_button_classes.py` from `files_modified` and `<verify>`.

### 2. Strengths
- **Preserves byte-identical golden output and dismissal hooks:** `src/crud_views/templates/crud_views/tags/alert.html:2-5` currently hardcodes `alert-dismissible fade show` and `btn-close`. Replacing those literals with `alert:dismissible` and `alert:close` keeps `role="alert"`, `type="button"`, `data-cv-alert-dismiss`, and `aria-label="{% translate 'Close' %}"` untouched and verified by `tests/test1/test_alerts.py:166-203` and `tests/js/adapters.test.js`.
- **Automatic W362 base-key acceptance and mode-suffix rejection:** Because `src/crud_views/lib/button_classes.py:262-265` (`_action_key_parts`) only allows 3-segment mode keys for `VARIANT_LOCATIONS` (`context`, `list`, `card`) and `form` (`FORM_KINDS`), adding `alert:dismissible` and `alert:close` to `DEFAULT_BUTTON_CLASSES` (`button_classes.py:92-96`) automatically makes W362 (`button_classes.py:328-346`) accept the base keys and warn on `alert:close:icon` or `alert:dismissible:both`.

### 3. Concerns
- **[HIGH] Missing `tests/test1/test_button_classes.py` in `files_modified` and `<verify>`:** Task `04-02` modifies `docs/reference/buttons.md` (`"The default table has 84 keys"`, `docs/reference/buttons.md:151`) and states acceptance criteria `"docs count matches DEFAULT_BUTTON_CLASSES"`. However, `test_documented_default_key_count_matches_table()` and `test_default_table_is_complete()` (`EXPECTED_KEYS`) live in `tests/test1/test_button_classes.py:21-116`, **not** in `tests/test1/test_button_classes_checks.py`! Because `04-02` only runs `pytest tests/test1/test_button_classes_checks.py tests/test1/test_alerts.py`, the doc count assertion is never run by `04-02`, and `tests/test1/test_button_classes.py` will fail as soon as `06.6-04` adds the two keys to `DEFAULT_BUTTON_CLASSES`.
- **[MEDIUM] Trailing space in `div[role="alert"]` class attribute when `alert:dismissible` is `None` or `""`:** In `src/crud_views/templates/crud_views/tags/alert.html:2`:
  `<div class="{% cv_button_class "alert" alert.level %}{% if alert.dismissible %} alert-dismissible fade show{% endif %}{% if alert.extra_tags %} {{ alert.extra_tags }}{% endif %}"`
  When `alert:dismissible` is configured as `None` or `""` (D-08: `"allow themes to replace or omit these classes"`), `{% cv_button_class "alert" "dismissible" %}` returns `""`. If the template unconditionally writes a leading space inside `{% if alert.dismissible %} {% cv_button_class "alert" "dismissible" %}{% endif %}`, omitting `alert:dismissible` produces `class="alert alert-success "` with a trailing space (or double space before `extra_tags`). Using `{% if alert.dismissible %}{% cv_button_class "alert" "dismissible" as dismissible_css %}{% if dismissible_css %} {{ dismissible_css }}{% endif %}{% endif %}` avoids stray whitespace when omitted while remaining byte-identical to `tests/test1/golden/alerts/dismissible.html` by default.

### 4. Suggestions
- Add `tests/test1/test_button_classes.py` to `files_modified` and `<verify>` in both `06.6-04` (updating `EXPECTED_KEYS` to 86 keys) and `06.6-03` (updating `EXPECTED_KEYS` to 88 keys).
- Guard the space before `{% cv_button_class "alert" "dismissible" %}` in `src/crud_views/templates/crud_views/tags/alert.html:2` with `as dismissible_css` and assert exact `frame.get("class") == "alert alert-success"` when `alert:dismissible` is `None` or `""` in `tests/test1/test_alerts.py`.

### 5. Risk Assessment
**LOW** — Small, localized change to `button_classes.py` and `tags/alert.html`; adding `tests/test1/test_button_classes.py` and guarding the leading space resolves all identified issues.

---

## 06.6-05

### 1. Summary
Plan `06.6-05` routes `src/crud_views_workflow/templates/crud_views_workflow/view_workflow.action.html` through `{% cv_render_form %}`, builds a comprehensive full-page and modal (`X-CV-Modal: true`) request/CSRF matrix across all five actionable form types (create, update, custom form, delete, workflow) in `tests/test1/test_theme_form_requests.py`, and updates the four form-frame golden files (`tests/test1/golden/form_frame/{create,update,custom_form,delete}.html`).

### 2. Strengths
- **Eliminates the workflow bypass cleanly:** `src/crud_views_workflow/templates/crud_views_workflow/view_workflow.action.html:8-16` wraps `{% crispy form form.helper %}` inside `<form class="cv-form" method="post" novalidate>{% csrf_token %}`. Because `WorkflowForm` inherits `CrispyForm` (`src/crud_views_workflow/lib/forms.py:11`), replacing line 15 with `{% cv_render_form %}` unifies workflow with `view_create.content.html`, `view_update.content.html`, `view_custom_form.content.html`, and `view_delete.content.html`.
- **Preserves intentional form-omission branches:** Explicitly tests that blocked deletes (`has_protected_objects` / `delete_protection_errors` in `src/crud_views/templates/crud_views/view_delete.content.html:8-24` and `tests/test1/golden/form_frame/delete_protection.html`) and workflow states without transitions (`{% if has_workflow_choices %}` in `view_workflow.action.html:6`) continue to omit confirmation forms.
- **Raw pre-parse tag and token counting:** Counting `<form` / `</form>` and `name="csrfmiddlewaretoken"` on the raw response string before `lxml.html` parsing prevents the HTML5 parser from masking nested `<form>` tags.

### 3. Concerns
- **[MEDIUM] Unused `{% load crispy_forms_tags %}` in `view_workflow.action.html:2`:** Once line 15 of `src/crud_views_workflow/templates/crud_views_workflow/view_workflow.action.html` changes from `{% crispy form form.helper %}` to `{% cv_render_form %}`, `{% load crispy_forms_tags %}` on line 2 is no longer used anywhere in `view_workflow.action.html` and should be removed to match `src/crud_views/templates/crud_views/view_create.content.html:1-2`.
- **[MEDIUM] Golden file update timing relative to `06.6-01`:** As noted in `06.6-01`, the markup change in `tests/test1/golden/form_frame/{create,update,custom_form,delete}.html` actually happens when `06.6-01` edits `cv_render_form` and `tags/form.html` in Wave 1. Keeping the golden file regeneration in `06.6-05` (Wave 2) means `tests/test1/test_form_frame.py` fails if run after `06.6-01`.
- **[LOW] Polymorphic views in the request matrix:** `PolymorphicCreateSelectView` (`src/crud_views_polymorphic/lib/create_select.py:24-28`) renders `crud_views/view_create.content.html` with `PolymorphicContentTypeForm` (a plain `django.forms.Form` without `CrispyFormMixin`, unless overridden as in `tests/test1/app/views.py:550`). Including polymorphic create-select and create/update endpoints in `test_theme_form_requests.py` will verify both `CrispyForm` and non-`CrispyFormMixin` views end-to-end.

### 4. Suggestions
- Remove `{% load crispy_forms_tags %}` from `src/crud_views_workflow/templates/crud_views_workflow/view_workflow.action.html:2` when replacing `{% crispy form form.helper %}` with `{% cv_render_form %}`.
- Add a test case in `tests/test1/test_theme_form_requests.py` for a view whose `form_class` is a plain `django.forms.Form` (such as `PolymorphicContentTypeForm`) to exercise the default nonwrapping helper path on a real view request.

### 5. Risk Assessment
**LOW** — The template change is a one-line replacement in `view_workflow.action.html`, and the golden diffs in `tests/test1/golden/form_frame/*.html` are deterministic removals of `<form method="post" ><input type="hidden" name="csrfmiddlewaretoken" value="CSRF">` and `</form>`.

---

## 06.6-06

### 1. Summary
Plan `06.6-06` builds `tests/browser/theme_adoption_sources.py` (and unit tests in `tests/browser/test_theme_adoption_sources.py`) to verify companion source provenance (`CV_THEME_SOURCE` and `CV_PACK_SOURCE`), archive the pre-phase core revision `cb26af4dfef2afb31d774a219abfad1c675cdff1`, and capture an unmodified baseline (`06-companion-baseline.json`) without mutating the companion worktrees. While the provenance design is thorough, execution of Task `06-02` faces a known environment blocker because the companion repositories are currently absent on disk.

### 2. Strengths
- **Isolated pre-change core archive (`cb26af4dfef2afb31d774a219abfad1c675cdff1`):** Archiving the planning-time core revision into a temporary directory before running the companion baseline ensures that concurrent Wave 1 edits from Plans `01`, `02`, and `04` cannot contaminate the baseline capture.
- **Fail-closed provenance and read-only worktree guards:** Checking before/after digests of `CV_THEME_SOURCE` and `CV_PACK_SOURCE`, recording exact `import` file paths, and distinguishing recorded baseline test failures from passing tests directly enforces D-11, D-13, and D-18.

### 3. Concerns
- **[HIGH] External availability blocker for `CV_THEME_SOURCE` (`tabler-test`) and `CV_PACK_SOURCE` (`crispy-tabler`):** `06.6-RESEARCH.md` ("Environment Availability") verified that neither `../tabler-test` nor `../crispy-tabler` exists anywhere under `/home/alex` (searched to depth 6). Unless automated discovery finds git remotes/bundles or the user supplies `CV_THEME_SOURCE` and `CV_PACK_SOURCE`, Task `06-02` will immediately stop at its precondition/acquisition checkpoint, which in turn blocks Plans `06.6-07` and `06.6-09`.
- **[MEDIUM] `pytest tests` collection of `tests/browser/test_theme_adoption_sources.py`:** In `noxfile.py:19` and Plan `06.6-09`, broad test runs execute `pytest tests -n 4 -q`, which collects every `test_*.py` file under `tests/`, including `tests/browser/test_theme_adoption_sources.py`. Every test in `tests/browser/test_theme_adoption_sources.py` must be hermetic (using `tmp_path` mocks/fixtures) and must not require `CV_THEME_SOURCE` or `CV_PACK_SOURCE` to be set in the environment.
- **[LOW] Python environment isolation when running the companion test suite:** The companion `tabler-test` suite may import `crispy_tabler` and `tabler` theme modules that are not installed in `.nox/tests-3-12-django-5-2`. `theme_adoption_sources.py` must construct `PYTHONPATH` from the isolated copies of `core/src`, `CV_THEME_SOURCE`, and `CV_PACK_SOURCE` when invoking `pytest`.

### 4. Suggestions
- Ensure `tests/browser/test_theme_adoption_sources.py` uses only hermetic `tmp_path` fixtures so `pytest tests` passes even when `CV_THEME_SOURCE` and `CV_PACK_SOURCE` are unset.
- In `theme_adoption_sources.py`, check `git config`, local git bundles, or sibling parent directories first, and emit a clear, structured diagnostic naming `CV_THEME_SOURCE` and `CV_PACK_SOURCE` if neither exists.

### 5. Risk Assessment
**HIGH** — Not due to code complexity, but because `06.6-RESEARCH.md` confirmed the companion repositories (`tabler-test` and `crispy-tabler`) are absent from the local filesystem, making Task `06-02` an immediate external dependency blocker until those sources are supplied.

---

## 06.6-07

### 1. Summary
Plan `06.6-07` implements the real-browser Chromium acceptance suite (`tests/browser/theme-adoption.cjs`, `tests/browser/theme_adoption_server.py`, `tests/browser/theme-adoption-config.test.cjs`) against isolated copies of the reference Tabler theme and `crispy-tabler` pack, and exports/replays the temporary adaptation patch (`07-tabler-adaptation.patch`, `07-tabler-replay.json`, `07-TABLER-HANDOFF.md`).

### 2. Strengths
- **Follows proven repo browser-harness conventions:** Mirrors the process-lifecycle, runtime-verification, and error-gate structure of `tests/browser/presentation.cjs:377-469` and `tests/browser/conditional-formsets.cjs:1-100`, including verifying that `crud_views.__file__` resolves inside the checkout and reaping the spawned Django server with `SIGTERM`/`SIGKILL` in `finally`.
- **Verifies both raw HTTP markup and live DOM/FormData association:** Checking raw `<form>` and `csrfmiddlewaretoken` counts before browser parsing alongside `element.form`, `new FormData(form, submitter)`, modal 422 replacement, conditional/formset lifecycle, label floors, action-group classes, and alert dismissal covers every acceptance requirement in D-11–D-14 and D-18.
- **Fresh-copy patch replay (`--verify-replay`):** Applying `07-tabler-adaptation.patch` to fresh copies of the exact base revisions proves the patch is self-contained, minimal, and leaves original companion worktrees untouched.

### 3. Concerns
- **[HIGH] Blocked by `06.6-06` companion source availability:** Cannot execute until authoritative `CV_THEME_SOURCE` and `CV_PACK_SOURCE` are provided and baselined in `06.6-06`.
- **[MEDIUM] Runtime `PYTHONPATH` and static asset serving in `theme_adoption_server.py`:** Because `.nox/tests-3-12-django-5-2` does not have `tabler-test` or `crispy-tabler` installed as wheels, `theme-adoption.cjs` and `theme_adoption_server.py` must inject the isolated temporary copy paths of both `CV_THEME_SOURCE` and `CV_PACK_SOURCE` into `PYTHONPATH`, register their apps/template dirs and staticfiles dirs in `settings`, and verify via `importlib` that templates and static assets resolve from the isolated copies.
- **[LOW] Port reservation across browser scripts:** `tests/browser/conditional-formsets.cjs:28-31` uses port `8144` and explicitly rejects reserved port `8143` (used by `modal-focus.cjs` and `presentation.cjs`). `theme-adoption.cjs` and `theme-adoption-config.test.cjs` should default `CV_THEME_PORT` to a distinct port (e.g., `8145`) and reject `8143` and `8144`.

### 4. Suggestions
- Reserve a dedicated default port (e.g., `8145`) for `CV_THEME_PORT` in `tests/browser/theme-adoption.cjs` and test port validation in `tests/browser/theme-adoption-config.test.cjs`.
- Have `theme_adoption_server.py` print a startup JSON payload (with `"ready": true`) that includes the resolved `__file__` paths of `crud_views`, the theme app, and `crispy_tabler`, plus the resolved template origin of `crud_views/tags/form.html` and `crud_views/tags/alert.html`, and assert those paths in `theme-adoption.cjs`.

### 5. Risk Assessment
**HIGH** — Dependent on external companion sources (`06.6-06`) and coordinates two external codebases (`tabler-test` and `crispy-tabler`) with live Chromium + CSRF HTTP interactions.

---

## 06.6-08

### 1. Summary
Plan `06.6-08` updates `docs/reference/theme.md`, `docs/reference/action_menus.md`, `docs/reference/settings.md`, `docs/migrating-1.0.md`, and `CHANGELOG.md` with executable adoption recipes and paired Breaking/Fixed/Added notes, verified by `tests/test1/test_theme_adoption_docs.py`, `tests/test1/test_label_mode_docs.py`, and `mkdocs build --strict`. However, several existing doc-contract tests in `tests/test1/test_label_mode_docs.py` and `tests/test1/test_alerts.py` assert exact prose substrings and fence counts that will break if not carefully coordinated across Tasks `08-01` and `08-02`.

### 2. Strengths
- **Executable documentation tests:** Extracting and executing Python/Django template fences from `docs/reference/theme.md`, `docs/reference/settings.md`, and `docs/migrating-1.0.md` follows the established pattern in `tests/test1/test_label_mode_docs.py:88-118,585-662` and `tests/test1/test_form_button_docs.py:247-259`.
- **Clear separation of `### Fixed` vs. `### Breaking` in `CHANGELOG.md`:** Distinguishes the stock nested-form/duplicate-token DOM bugfix (`### Fixed`) from the `form_tag=True` rejection, unused-wrapper strict-mode error, and `cv_form_helper` inner-template contract (`### Breaking`, paired with `docs/migrating-1.0.md`).

### 3. Concerns
- **[HIGH] Task split between `08-01` and `08-02` conflicts with `tests/test1/test_label_mode_docs.py` on `docs/migrating-1.0.md`:** Look at `tests/test1/test_label_mode_docs.py:786-800` (`test_migration_e108_location_inventory`): it reads `MIGRATING_MD` (`docs/migrating-1.0.md`) and asserts the exact substring `"otherwise it logs one warning and the location falls back to its package floor."` (`line 797`). Task `08-01` modifies `tests/test1/test_label_mode_docs.py` (to update the fallback prose from package-only to `theme → package`) and runs `pytest ... tests/test1/test_label_mode_docs.py`, but `docs/migrating-1.0.md` is not modified until Task `08-02`! If `08-01` updates `test_migration_e108_location_inventory` in `test_label_mode_docs.py` before `08-02` edits `docs/migrating-1.0.md`, `08-01`'s verify step will fail; conversely, if `08-02` edits that sentence in `docs/migrating-1.0.md` without updating `test_label_mode_docs.py:797`, `test_label_mode_docs.py` will fail in Plan `06.6-09`!
- **[HIGH] Fragile exact-step and exact-phrase assertions in `tests/test1/test_label_mode_docs.py` and `tests/test1/test_alerts.py`:**
  1. `tests/test1/test_label_mode_docs.py:145-178` (`test_label_mode_configuration_table`), `190-229` (`test_canonical_label_mode_resolution_sections`), and `709-729` (`test_form_label_mode_reference_contract`) assert exact numbered-list lengths (`len(context) == 5`, `len(listing) == 2`, `len(card) == 3`, `len(mode) == 2`) and exact phrases in `docs/reference/settings.md` and `docs/reference/action_menus.md`. Adding `register_label_mode_defaults()` as a separate numbered step in `action_menus.md` (instead of describing the 3-layer floor within `default_label_mode(...)`) will break those length assertions unless `test_label_mode_docs.py` is updated in tandem.
  2. `tests/test1/test_alerts.py:249-255` (`_documented_alert_frame`) parses `docs/reference/theme.md` -> `## Alerts` -> `### Custom alert frame` and asserts `assert len(bodies) == 1, "'### Custom alert frame' must hold exactly one django/html fence"`. Meanwhile, `docs/reference/theme.md:310-311` currently states: `"The frame's own classes (alert-dismissible fade show, btn-close) are literal Bootstrap CSS. To style them your way, ship templates/crud_views/tags/alert.html in your theme app."` Task `08-01` must update that obsolete claim in `docs/reference/theme.md:308-323` without adding a second `django`/`html` fence under `### Custom alert frame`, and should run `tests/test1/test_alerts.py` in `<verify>`.

### 4. Suggestions
- Include `docs/migrating-1.0.md` in Task `08-01` (or include `tests/test1/test_label_mode_docs.py` in Task `08-02` as well) so `test_migration_e108_location_inventory` (`tests/test1/test_label_mode_docs.py:786-800`) and `docs/migrating-1.0.md` stay synchronized at every task boundary.
- Add `tests/test1/test_alerts.py` and `tests/test1/test_button_classes.py` to Task `08-01`'s `<verify>` pytest command to immediately catch any fence-count or table-count regression in `docs/reference/theme.md` and `docs/reference/buttons.md`.

### 5. Risk Assessment
**MEDIUM** — The existing documentation test suite (`tests/test1/test_label_mode_docs.py` and `tests/test1/test_alerts.py`) enforces strict structural and substring invariants across `settings.md`, `action_menus.md`, `buttons.md`, `theme.md`, `migrating-1.0.md`, and `CHANGELOG.md`.

---

## 06.6-09

### 1. Summary
Plan `06.6-09` executes the final multi-version verification gates across cached Django 4.2, 5.2, and the Django 6.0 crispy floor (`2.0` / `2023.10`), Vitest unit and integration lanes, browser preservation suites (`modal-focus.cjs`, `conditional-formsets.cjs`, `theme-adoption.cjs`), strict MkDocs build, and Ruff checks, and produces the Phase 7 public-surface handoff (`06.6-PUBLIC-SURFACE.md`, `06.6-ACCEPTANCE.md`, `09-final-evidence.json`).

### 2. Strengths
- **Comprehensive cross-series and cross-layer verification:** Runs the full Python test suite on `.nox/tests-3-12-django-4-2`, `.nox/tests-3-12-django-5-2`, and `.nox/crispy_floor-3-12-django-6-0` (with only the pre-existing `test_filter_form_baseline` deselected per `noxfile.py:57`), plus JS unit/integration and real-browser suites.
- **Explicit fail-closed gate (`--check-final`):** Rejects stale source hashes, missing companion baseline/replay artifacts, zero-test collections, or skipped required phase scenarios, and keeps human visual/AT confirmation explicitly blocking rather than fabricating a pass.

### 3. Concerns
- **[MEDIUM] `noxfile.py` `CRISPY_FLOOR_TESTS` is not updated with the new Phase 06.6 test modules:** `noxfile.py:28-52` defines an explicit list `CRISPY_FLOOR_TESTS` for the `crispy_floor` nox session. Although Plan `06.6-09` runs `.nox/crispy_floor-3-12-django-6-0/bin/python -m pytest tests -n 4 -q ...` directly across all of `tests/`, `noxfile.py:28-52` itself will not include `tests/test1/test_theme_form_ownership.py`, `tests/test1/test_theme_label_modes.py`, `tests/test1/test_theme_action_groups.py`, `tests/test1/test_theme_form_requests.py`, or `tests/test1/test_theme_adoption_docs.py` when `nox -s crispy_floor` (`task test`) is run later.
- **[LOW] Inconsistent `CV_FOCUS_PYTHON` environment variable on `conditional-formsets.cjs` in `<verification>`:** In `06.6-09` `<verification>`, `modal-focus.cjs` is run with `CV_FOCUS_PYTHON=.nox/tests-3-12-django-5-2/bin/python`, while `node tests/browser/conditional-formsets.cjs --case lifecycle ...` on the next line omits `CV_FOCUS_PYTHON`. Passing `CV_FOCUS_PYTHON=.nox/tests-3-12-django-5-2/bin/python` to both ensures neither script accidentally uses `.venv/bin/python` (which has Django 6.1.2 installed).
- **[LOW] `examples/bootstrap5` redundant `helper` override (`examples/bootstrap5/formsets/views.py:36-41`):** While `06.6-09` runs `ruff check src tests examples`, running the example pytest suite (`.nox/examples-3-12-django-5-2` or equivalent) and cleaning up the redundant `h.form_tag = False` override in `examples/bootstrap5/formsets/views.py:36-41` would ensure the example app reflects the settled Phase 06.6 contract.

### 4. Suggestions
- Update `CRISPY_FLOOR_TESTS` in `noxfile.py:28-52` to include the five new `tests/test1/test_theme_*.py` test files so `nox -s crispy_floor` permanently guards Phase 06.6 on the crispy floor.
- Prefix the `conditional-formsets.cjs` command in `<verification>` with `CV_FOCUS_PYTHON=.nox/tests-3-12-django-5-2/bin/python`.

### 5. Risk Assessment
**MEDIUM** — The verification matrix is thorough and sound, but its completion is gated on resolving the cross-plan test omissions (`tests/test1/test_button_classes.py`, `tests/test1/test_form_button_checks.py`, `tests/test1/test_label_mode_docs.py`) and the external companion source blocker (`06.6-06`/`06.6-07`).

---

## Cross-Plan Comparison & Overall Risk Assessment

### Key Cross-Plan Findings (Verified Against Repo Source)
1. **`tests/test1/test_button_classes.py` is missing from both `06.6-04` and `06.6-03` (`HIGH`):**
   - `tests/test1/test_button_classes.py:21-91,104-116` defines `EXPECTED_KEYS` (currently 84 keys), `test_default_table_is_complete()`, and `test_documented_default_key_count_matches_table()`.
   - Plans `06.6-04` and `06.6-03` add 4 keys (`alert:dismissible`, `alert:close`, `form:actions`, `form:filter-actions`) to `DEFAULT_BUTTON_CLASSES` in `src/crud_views/lib/button_classes.py` and update `docs/reference/buttons.md:151`, but only list `tests/test1/test_button_classes_checks.py` in `files_modified` and `<verify>`. Without updating `tests/test1/test_button_classes.py`, the doc-count test is never run in `06.6-04`/`06.6-03` and the full test suite in `06.6-09` will fail.
2. **Wave 1 cross-plan breakage in `tests/test1/test_form_button_checks.py` and `tests/test1/test_form_frame.py` (`HIGH`):**
   - `_CustomHelperForm` (`tests/test1/test_form_button_checks.py:565`) and `_DeleteCustomHelper` (`583`) use `FormHelper()` (`form_tag=True`) and are rendered through `/author/create/` and `/author/{pk}/delete/` (`{% cv_render_form %}`) at lines `1085-1111`. When `06.6-01` rejects `form_tag=True` at `cv_render_form`, `06.6-02`'s verification command (`pytest ... tests/test1/test_form_button_checks.py`) will fail in Wave 1 unless those two test helpers set `helper.form_tag = False`.
   - Similarly, `06.6-01` changes the rendered output of `cv_render_form` in Wave 1, which immediately changes the markup tested by `tests/test1/test_form_frame.py:71-73`, while the four golden files `tests/test1/golden/form_frame/{create,update,custom_form,delete}.html` are not updated until `06.6-05` in Wave 2.
3. **Doc-test synchronization across `08-01` and `08-02` (`HIGH`):**
   - `tests/test1/test_label_mode_docs.py:786-800` asserts exact fallback wording in `docs/migrating-1.0.md`, while `06.6-08` splits `test_label_mode_docs.py` (`08-01`) and `docs/migrating-1.0.md` (`08-02`) across two tasks.
   - `tests/test1/test_alerts.py:249-317` asserts that `### Custom alert frame` in `docs/reference/theme.md:308-323` has exactly one `django`/`html` code fence.
4. **External companion repository blocker in `06.6-06` and `06.6-07` (`HIGH`):**
   - `tabler-test` and `crispy-tabler` are not present in the workspace environment; `06.6-06` properly fails closed with an acquisition checkpoint, which will block `06.6-06`, `06.6-07`, and `06.6-09` until the paths are provided.

### Overall Risk Level: **MEDIUM**
The technical architecture for `THEME-01`–`THEME-04` and `THEME-06` is well-grounded in the existing codebase seams (`crud_views.py`, `form.py`, `label_mode.py`, `button_classes.py`, `alert.html`, `view_workflow.action.html`). Fixing the four concrete test/file-list gaps identified above will prevent avoidable test failures across Waves 1–4, leaving only the external companion source acquisition (`THEME-05`) as an environmental prerequisite.
