## 06.6-01

### Summary
Plan `06.6-01` establishes single-form and single-CSRF ownership on the create path and introduces render-local helper selection (`_prepare_form_helper`) and wrapper diagnostics (`_diagnose_form_wrapper`) behind `cv_render_form`. Checking the referenced implementation seams confirms that `CrispyFormMixin.helper` (`src/crud_views/lib/crispy/form.py:43-50`) and `CrispyDeleteForm.helper` (`src/crud_views/lib/crispy/form.py:136-146`) currently construct `FormHelper()` with crispy's default `form_tag = True`, while `src/crud_views/templates/crud_views/view_create.content.html:5-11` already wraps `{% cv_render_form %}` inside `<form class="cv-form" method="post" ...>{% csrf_token %}...`, producing the nested `<form method="post">` and duplicate `csrfmiddlewaretoken` input captured in `tests/test1/golden/form_frame/create.html:1`. The plan's atomic commit boundary pairing Tasks `01-01` and `01-02` cleanly migrates the renderer alongside the four frame goldens and the two custom-helper test fixtures in `tests/test1/test_form_button_checks.py:560-585`.

### Strengths
- **Preserves `Context.dicts` stack for button owner resolution (`src/crud_views/templatetags/crud_views.py:453-466`, `src/crud_views/lib/crispy/buttons.py:49-77`):** `cv_render_form` at `src/crud_views/templatetags/crud_views.py:465-466` currently calls `render_to_string(..., context.flatten())`, which flattens the `RequestContext` stack. Replacing this with `get_template(...).template.render(context)` under `with context.push(cv_form_helper=...):` (matching `cv_alert` at `src/crud_views/templatetags/crud_views.py:453-455`) preserves `context.dicts` so `_cv_helper_tier` (`src/crud_views/lib/crispy/buttons.py:49-61`) and `_cv_page_tier` (`src/crud_views/lib/crispy/buttons.py:64-77`) continue to distinguish crispy response overlays from page layers.
- **Eliminates double evaluation of `form.helper` (`src/crud_views/templates/crud_views/tags/form.html:3-6`, `src/crud_views/lib/crispy/form.py:43-50`):** `tags/form.html:3-4` currently evaluates `{% if form.helper %}` and then `{% crispy form form.helper %}`, which invokes the `@property def helper` factory twice per render and checks truthiness (`FormHelper.__len__` delegates to `len(self.layout)`). Selecting `cv_form_helper` once by identity/presence in `_prepare_form_helper` and rendering `{% crispy form cv_form_helper %}` avoids double allocation and preserves empty/falsy helpers.
- **Atomic fixture and golden migration (`tests/test1/test_form_button_checks.py:560-585,1085-1110`, `tests/test1/test_form_frame.py:19-24,71-73`):** `_CustomHelperForm.helper` (`tests/test1/test_form_button_checks.py:564-567`) and `_DeleteCustomHelper.helper` (`tests/test1/test_form_button_checks.py:582-585`) instantiate raw `FormHelper()` with default `form_tag=True` to test missing-icon runtime fallback at `lines 1085-1110`. Migrating those two helpers to `form_tag=False` and updating `tests/test1/golden/form_frame/{create,update,custom_form,delete}.html` in Task `01-02` within the same commit as Task `01-01` prevents an intermediate broken test suite.
- **Standalone crispy token preservation (`src/crud_views/lib/crispy/form.py:43-50`):** By setting `form_tag = False` on `CrispyFormMixin.helper` and `CrispyDeleteForm.helper` while keeping `disable_csrf = True` scoped to `cv_render_form`, standalone `{% crispy form %}` renders retain their CSRF token while page-owned `cv_render_form` renders emit only the outer `<form class="cv-form">` token.

### Concerns
- **[LOW] Helper-less plain `django.forms.Form` rendering in `tests/test1/test_form_frame.py:34-41` relies on `_prepare_form_helper` synthesizing a non-wrapping default helper:** `NameForm` in `tests/test1/test_form_frame.py:34-35` is a plain `forms.Form` with no `.helper` attribute (`getattr(form, "helper", None)` is `None`). In `src/crud_views/templates/crud_views/tags/form.html:5-6`, the `{% else %}{% crispy form %}{% endif %}` branch previously let `crispy_forms` synthesize a default `FormHelper()` with `form_tag=True` and `disable_csrf=False` (causing the inner `<form method="post">` in `tests/test1/golden/form_frame/create.html:1`). Task `01-01` notes that a missing/`None` helper receives a library-created non-wrapping helper (`form_tag=False`, `disable_csrf=True`), which is essential so `tags/form.html` can unconditionally call `{% crispy form cv_form_helper %}` and pass `test_form_frame.py:71-73`.

### Suggestions
- In `src/crud_views/templates/crud_views/tags/form.html`, render `{% crispy form cv_form_helper %}` directly (without a fallback `{% crispy form %}` branch) so any direct include of `tags/form.html` without `cv_render_form` cannot silently reintroduce an inner `<form>` and duplicate CSRF token.

### Risk Assessment
**LOW** — The target seams in `src/crud_views/lib/crispy/form.py`, `src/crud_views/templatetags/crud_views.py`, and `src/crud_views/templates/crud_views/tags/form.html` are small, well-isolated, and directly verified against existing golden and check suites.

---

## 06.6-02

### Summary
Plan `06.6-02` adds `register_label_mode_defaults(defaults: dict[str, str]) -> None` to `src/crud_views/lib/view/label_mode.py`, inserting a validated theme floor between `LABEL_MODE_DEFAULTS` (`src/crud_views/lib/view/label_mode.py:23-25`) and the live `CRUD_VIEWS_LABEL_MODE_DEFAULTS` setting (`src/crud_views/lib/view/label_mode.py:56-60,86-119`), while updating invalid-setting fallback destinations (D-07) and verifying `crud_views.E108` (`src/crud_views/lib/settings.py:161-190`) and `viewset.W292` (`src/crud_views/lib/view/buttons.py:435-448,546-579`).

### Strengths
- **Non-recursive fallback helper (`src/crud_views/lib/view/label_mode.py:86-119,122-146`):** In `default_label_mode` (`src/crud_views/lib/view/label_mode.py:107,118`), invalid `CRUD_VIEWS_LABEL_MODE_DEFAULTS` values currently fall back via `lambda: LABEL_MODE_DEFAULTS[location]`. Routing those fallbacks to `_theme_or_package_default(location)` (which reads only the rebound `_THEME_LABEL_MODE_DEFAULTS` snapshot and `LABEL_MODE_DEFAULTS`, never `_raw_label_mode_defaults()`) guarantees that composed invalid owner map + invalid setting fallback in `form_label_mode` (`src/crud_views/lib/view/label_mode.py:129-146`) resolves to the theme floor without recursion.
- **Dedup register awareness in composed fallback tests (`src/crud_views/lib/view/label_mode.py:31-32,76-83`):** `_invalid_label_mode` deduplicates warnings per process by `pair = (location, repr(value))` (`src/crud_views/lib/view/label_mode.py:76`). Task `02-02` explicitly requires distinct malformed values for the owner map and `CRUD_VIEWS_LABEL_MODE_DEFAULTS` when testing composed non-strict fallback on location `"form"`, preventing `_warned` from suppressing the outer warning after the inner fallback logs.
- **Autouse test isolation in `tests/test1/conftest.py:23-33`:** `conftest.py` currently isolates `label_mode._warned` (`lines 24-32`) but has no fixture for theme label-mode defaults (unlike `_isolate_registry` in `tests/test1/test_button_classes.py:94-101`). Adding an autouse snapshot/rebind fixture in `tests/test1/conftest.py` prevents cross-test contamination under `pytest-xdist`.
- **Zero-instantiation W292 compatibility (`src/crud_views/lib/view/buttons.py:435,569`):** Both `context_button_checks` (`line 435`) and `cv_form_icon_mode_checks` (`line 569`) already resolve effective modes via `cls.cv_get_action_label_mode(...)`, which delegates to `default_label_mode`. Updating `default_label_mode` automatically makes `W292` respect theme-registered floors without violating the non-instantiation invariant tested in `tests/test1/test_form_button_checks.py:713-724`.

### Concerns
- **[LOW] Circular import boundary between `label_mode.py` and `button_data.py` (`src/crud_views/lib/view/label_mode.py:94-95`, `src/crud_views/lib/view/button_data.py:15,19`):** `button_data.py:15` imports `default_label_mode` from `.label_mode` at module import time, which is why `default_label_mode` defers `from .button_data import LOCATIONS` inside the function body (`src/crud_views/lib/view/label_mode.py:94-95`). `register_label_mode_defaults` must similarly defer `from .button_data import LOCATIONS` inside its function body rather than importing `LOCATIONS` at the top of `label_mode.py`.

### Suggestions
- Keep `from .button_data import LOCATIONS` deferred inside `register_label_mode_defaults` (matching `default_label_mode` at `src/crud_views/lib/view/label_mode.py:95`) so module-level import order between `label_mode` and `button_data` remains cycle-free.

### Risk Assessment
**LOW** — The layering and validation rules directly mirror `src/crud_views/lib/button_classes.py:135-151` and `src/crud_views/lib/view/label_mode.py:86-146`, with full unit and system-check coverage.

---

## 06.6-03

### Summary
Plan `06.6-03` introduces the `form:actions` and `form:filter-actions` utility keys (with `""` defaults in `DEFAULT_BUTTON_CLASSES`) and wires them into the three default action-group constructors (`CrispyFormMixin.get_form_actions` at `src/crud_views/lib/crispy/form.py:55-56`, `CrispyDeleteForm.helper` at `src/crud_views/lib/crispy/form.py:141-144`, and `ListViewFilterFormHelper.get_form_actions` at `src/crud_views/lib/views/list.py:125-133`), including a narrowly scoped compatibility bridge for `crispy-bootstrap5==2023.10` (`noxfile.py:24`).

### Strengths
- **Covers all three independent `FormActions` construction sites (`src/crud_views/lib/crispy/form.py:55-56,141-144`, `src/crud_views/lib/views/list.py:125-133`):** `CrispyDeleteForm.helper` (`src/crud_views/lib/crispy/form.py:137-146`) builds `FormActions(self.get_delete_button(), self.get_cancel_button())` inline rather than calling `self.get_form_actions()`. Explicitly wiring `CrispyDeleteForm.helper` alongside `CrispyFormMixin.get_form_actions` and `ListViewFilterFormHelper.get_form_actions` ensures delete pages receive `form:actions` styling.
- **Preserves static W292 inheritance checks (`src/crud_views/lib/view/buttons.py:504,513,538`):** `_static_form_controls` (`src/crud_views/lib/view/buttons.py:504,513`) and `_static_filter_controls` (`line 538`) use `_inherits(form_class, "get_form_actions", CrispyFormMixin)`, `_inherits(form_class, "helper", CrispyDeleteForm)`, and `_inherits(helper, "get_form_actions", ListViewFilterFormHelper)`. Updating those methods on the base classes themselves keeps `_inherits(...)` `True` for all unoverridden subclasses.
- **Dynamic per-render class resolution for cached filter action groups (`src/crud_views/lib/views/list.py:172-180`):** `ListViewFilterFormHelper.render_layout` caches `self._cv_actions = self.get_form_actions()` once per prepared layout (`lines 174-179`). Storing the class-table key on `_ThemedFormActions` as primitive state and resolving `get_button_class` during `render` ensures `register_button_classes` and `override_settings(CRUD_VIEWS_BUTTON_CLASSES=...)` take effect on repeated renders of the same filter helper without mutating `self.css_class` or failing `copy.deepcopy` (`src/crud_views/lib/views/list.py:155`).
- **Synchronized key count and inventory (`tests/test1/test_button_classes.py:21-91,105,112-116`, `docs/reference/buttons.md:151`):** Task `03-02` updates `EXPECTED_KEYS` and `docs/reference/buttons.md:151` from 86 (after Plan 04) to 88 in the same commit as the `DEFAULT_BUTTON_CLASSES` additions, keeping `test_default_table_is_complete` and `test_documented_default_key_count_matches_table` green.

### Concerns
- **[LOW] `crispy-bootstrap5` 2023.10 floor template path resolution across symlinked/virtualenv site-packages (`src/crud_views/lib/crispy/actions.py`):** In Task `03-01`, `_use_bootstrap5_floor_bridge` checks that `template_pack == "bootstrap5"`, the resolved template origin belongs to the installed `crispy_bootstrap5` package, and its content matches the 2023.10 `bootstrap5/layout/formactions.html` source. Using `Path(origin.name).resolve()` and `Path(crispy_bootstrap5.__file__).resolve().parent` (as specified in `03-01` "resolve real paths") is important so symlinked `.nox` virtualenvs do not cause false path mismatches.

### Suggestions
- In `_ThemedFormActions`, ensure `__deepcopy__` (or standard attribute copying via `FormActions.__dict__`) preserves the class-key attribute and authored `css_class` separately so `copy.deepcopy(current)` in `ListViewFilterFormHelper._cv_prepare_layout` (`src/crud_views/lib/views/list.py:155`) works when a subclass places a `super().get_form_actions()` group directly inside a custom `layout`.

### Risk Assessment
**LOW** — The floor pack limitation was reproduced in research (`06.6-RESEARCH.md:208-231`), and the origin + exact-content discriminator prevents any interference with custom pack templates or `crispy_tabler`.

---

## 06.6-04

### Summary
Plan `06.6-04` adds the `alert:dismissible` (`"alert-dismissible fade show"`) and `alert:close` (`"btn-close"`) utility keys to `DEFAULT_BUTTON_CLASSES` (`src/crud_views/lib/button_classes.py:91-96`) and consumes them in `src/crud_views/templates/crud_views/tags/alert.html:2-5`.

### Strengths
- **Byte-identical default golden preservation (`src/crud_views/templates/crud_views/tags/alert.html:2-5`, `tests/test1/test_alerts.py:166-181`, `tests/test1/golden/alerts/dismissible.html:1-7`):** `test_dismissible_alert_golden` (`tests/test1/test_alerts.py:166-181`) compares raw UTF-8 bytes without whitespace normalization. Task `04-01` resolves `alert:dismissible` into a template variable and emits the leading space only when non-empty, while keeping `class="{% cv_button_class 'alert' 'close' %}"` on the `<button type="button" ... data-cv-alert-dismiss>`, preserving exact byte parity with `tests/test1/golden/alerts/dismissible.html`.
- **W362 base-only utility validation (`src/crud_views/lib/button_classes.py:251-275,328-346`):** Adding `"alert:dismissible"` and `"alert:close"` to `DEFAULT_BUTTON_CLASSES` allows `button_class_check_messages` (`line 329`) to accept them as base keys while `_is_action_mode_key` (`lines 269-275`, which only allows `VARIANT_LOCATIONS` and `form` + `FORM_KINDS`) continues to flag `alert:close:icon` and `alert:dismissible:both` with `crud_views.W362`.
- **Preserves `test_alerts.py` Bootstrap data-attribute guard (`tests/test1/test_alerts.py:319-330`):** Retaining `data-cv-alert-dismiss` in `src/crud_views/templates/crud_views/tags/alert.html:5` keeps `test_stock_bootstrap_data_attributes_are_dropdown_only` passing.

### Concerns
- None identified. All file references, key counts (84 to 86), and template whitespace contracts match the live codebase.

### Suggestions
- In `tests/test1/test_alerts.py`, include a test case combining `alert:dismissible = ""` and `alert.extra_tags = "my-extra"` to verify that `alert.extra_tags` still receives its single leading space when `alert:dismissible` is omitted (`class="alert alert-success my-extra"`).

### Risk Assessment
**LOW** — Small, self-contained template and dictionary change guarded by byte-exact golden and system-check tests.

---

## 06.6-05

### Summary
Plan `06.6-05` routes `src/crud_views_workflow/templates/crud_views_workflow/view_workflow.action.html` through `{% cv_render_form %}`, expands raw single-form/single-CSRF and enforced-CSRF request testing across all five actionable form types (full-page and supported modal paths), and removes the two redundant `form_tag = False` parent formset helper overrides in `tests/test1/app/views_formset.py:44-50` and `examples/bootstrap5/formsets/views.py:36-41`.

### Strengths
- **Fixes workflow's direct crispy bypass (`src/crud_views_workflow/templates/crud_views_workflow/view_workflow.action.html:2,8-16`):** `view_workflow.action.html:8-16` opens `<form class="cv-form" method="post" novalidate>{% csrf_token %}` and then calls `{% crispy form form.helper %}` at line 15, bypassing `cv_render_form`. Replacing line 15 with `{% cv_render_form %}` and dropping `{% load crispy_forms_tags %}` at line 2 brings workflow pages into the single-helper, single-CSRF boundary.
- **Accurately distinguishes workflow modal vs. full-page template paths (`src/crud_views_workflow/lib/views.py:18-28`, `src/crud_views/templates/crud_views/modal/content.html:8`, `src/crud_views_workflow/templates/crud_views_workflow/view_workflow.content.html:1-5`):** `WorkflowView` (`src/crud_views_workflow/lib/views.py:18-28`) inherits `cv_content_template = "crud_views/view_custom_form.content.html"` from `CustomFormView` (`src/crud_views/lib/views/form.py`), whereas full-page `view_workflow.html` includes `view_workflow.content.html` -> `view_workflow.action.html`. Task `05-01` (C3-A01) explicitly tests both paths and asserts their distinct template origins rather than conflating modal custom-form rendering with `view_workflow.action.html`.
- **Restores static W292 inspection on formset parent forms (`tests/test1/app/views_formset.py:44-50`, `examples/bootstrap5/formsets/views.py:36-41`, `src/crud_views/lib/view/buttons.py:512`):** `_static_form_controls` (`src/crud_views/lib/view/buttons.py:512`) skips forms that override `CrispyFormMixin.helper`. Removing the now-redundant `@property def helper` overrides in `PublisherFormSetForm` and `QuestionnaireForm` (along with the unused `from crispy_forms.helper import FormHelper` at `examples/bootstrap5/formsets/views.py:4`) makes both forms statically inspectable by `W292` while keeping `tests/test1/test_formsets.py:16-35` passing.

### Concerns
- None identified. The modal support boundary (`cv_modal_supported = False` on create/update in `src/crud_views/lib/view/base.py:111`), workflow template resolution, and parent formset helper cleanup are all verified against source.

### Suggestions
- When removing `QuestionnaireForm.helper` in `examples/bootstrap5/formsets/views.py:36-41`, ensure `from crispy_forms.helper import FormHelper` on line 4 of `examples/bootstrap5/formsets/views.py` is removed so `.venv/bin/ruff check src tests examples` in Plan `06.6-09` does not fail on `F401`.

### Risk Assessment
**LOW** — Builds directly on Plan `06.6-01`'s render boundary and aligns with existing workflow, modal, and formset architectures.

---

## 06.6-06

### Summary
Plan `06.6-06` builds the import-pure `tests/browser/theme_adoption_sources.py` provenance, baseline, replay, and delivery validation CLI (with unit tests in `tests/browser/test_theme_adoption_sources.py`) and captures the unmodified baseline of `../tabler-test` (`885dfc791a150fdc715d6fb34c2e6181d6b92f3c`) against the pre-phase core revision (`cb26af4dfef2afb31d774a219abfad1c675cdff1`).

### Strengths
- **Complete tree-derived shadow and behavior classification (`../tabler-test/src/crud_views_tabler/checks.py:8-27`, `../tabler-test/src/crud_views_tabler/icons.py:50-52`, `../tabler-test/src/crud_views_tabler/templates/crud_views/`):** Inspection of the embedded companion source confirms that `crud_views_tabler` ships eight template shadows under `templates/crud_views/` (`modal/shell.html`, `snippets/form_frame.html`, `table/bootstrap5.html`, `tags/alert.html`, `tags/card.html`, `tags/list_filter.html`, `tags/list_filter.inner.html`, `view_card.content.html`) plus custom Python behavior in `checks.py:8-27` (`check_tabler_icons`) and `icons.py:50-52` (`render`). Task `06-01` (C4-A01) requires full archived-tree enumeration and purpose-ID classification rather than trusting a 4-template probe list.
- **Worktree-safe `--delivered-source recorded` resolution (`C6-A03`):** Resolving `companion_root` from `06-companion-baseline.json` beneath `Path(__file__).resolve().parents[2]` (and defaulting `CV_THEME_SOURCE` / `CV_PACK_SOURCE` to `/home/alex/projects/alex/tabler-test`) ensures that fresh subprocesses and isolated git worktrees (where `../tabler-test` relative to the worktree root does not exist) always locate and validate the exact companion checkout.
- **Progressive single-file delivery evidence bundle (`C6-A02`):** Merging `form_probe`, `delivered_probe`, and `committed_probe` with full sanitized stdout/stderr logs and digests into `.planning/phases/06.6-theme-adoption-seams-from-the-tabler-sync/10-companion-delivery.json` avoids untracked sidecar files or brittle `/tmp` log dependencies while keeping private `example/config/settings.py` contents out of git history.

### Concerns
- **[MEDIUM] `C6-A01` empty-string cancel destination (`data_cv_cancel_url=""`) vs. absent destination (`None`) in Chromium click/keyboard activation (`src/crud_views/lib/view/button_data.py:354-357,392-393`, `src/crud_views/templates/crud_views/tags/button/form.html:3`, `src/crud_views/static/crud_views/js/viewset.js:38-44`):** Task `06-01` (lines 113-119) and Task `07-02` (lines 124-132) require `cancel-no-url` validation for both absent (`None`) and empty (`""`) cancel destinations, including Chromium click/keyboard activation asserting "zero submit/reset events with the edited value preserved". However, tracing the core code shows a critical distinction between `None` and `""`:
  1. When `data_cv_cancel_url=None` (or omitted, as produced by `CrudView.get_cancel_button_context` at `src/crud_views/lib/view/base.py:750,823` when `cv_cancel_key=None`), `_attr_text(None)` (`src/crud_views/lib/view/button_data.py:229-233`) returns `None`, so `cv_cancel_url` is `None` and `src/crud_views/templates/crud_views/tags/button/form.html:3` (`{% if cv_cancel_url is not None %} data-cv-cancel-url="{{ cv_cancel_url }}"{% endif %}`) omits `data-cv-cancel-url`. Clicking the `<button type="button">` in Chromium is a true no-op that preserves edited form inputs.
  2. When `data_cv_cancel_url=""` (explicit empty string), `_attr_text("")` returns `""` (`not None`), `tag` falls back to `"button"` (`button_data.py:357`), and `form.html:3` renders `data-cv-cancel-url=""` on the `<button type="button">` (a locked Phase 6.1 contract asserted at `tests/test1/test_crispy_buttons.py:2110`). On a live Tabler page loading `crud_views/js/viewset.js` (`crud_views_tabler/page.html:16`), clicking or keyboard-activating `<button type="button" data-cv-cancel-url="">` matches `e.target.closest("[data-cv-cancel-url]")` at `src/crud_views/static/crud_views/js/viewset.js:39` and executes `globalThis.location.href = ""` (`line 43`), which in Chromium reloads the current page URL and wipes out the edited input value unless navigation is intercepted or the live browser activation targets the real `cv_cancel_key=None` (`cv_cancel_url=None`) state.
- **[LOW] `pytest-xdist` absence in `../tabler-test/.venv` (`../tabler-test/pyproject.toml:32`, `06.6-RESEARCH.md:315-318`):** `../tabler-test/pyproject.toml:32` declares `test = ["pytest", "pytest-django", "crispy-bootstrap5==2026.9"]` without `pytest-xdist`, and the research addendum confirms `xdist` is absent from `/home/alex/projects/alex/tabler-test/.venv/bin/python`. Yet Task `06-01` (line 97) specifies running `-m pytest tests -n 4 -q` with a preflight that halts on missing `pytest-xdist`. Because package installation is gated by `T-06.6-SC`, unconditionally passing `-n 4` to `tabler-test`'s `pytest` (whose `tests/crispy_tabler/` suite is tiny) or halting on missing `xdist` in `tabler-test/.venv` will immediately trigger a precondition halt in `06-02` unless `theme_adoption_sources.py` either checks `import xdist` to pass `-n 4` when available and serial when `xdist` is not in `tabler-test/pyproject.toml`, or the user installs `pytest-xdist` via the gate. (`example/manage.py test ... --parallel 4` uses Django's built-in `multiprocessing` runner and does not require `pytest-xdist`.)

### Suggestions
- In `tests/browser/theme_adoption_sources.py`, distinguish the two `cancel-no-url` sub-states in the schema: require `ThemeAdoptionTests` (Python) to verify both `None` (absent) and `""` (empty) destination fallback to `<button type="button">` without `href` across `both`/`icon`/`label` modes (including with `form:cancel-tag="a"`), and have the Chromium click/keyboard activation test either exercise the `cv_cancel_key=None` (`cv_cancel_url=None`) URL-less button or intercept `location.href` when testing `data-cv-cancel-url=""` so `viewset.js:43` does not reload the page in Chromium.
- For the companion `pytest tests` invocation in `tests/browser/theme_adoption_sources.py`, note that `../tabler-test/pyproject.toml:32` does not list `pytest-xdist`; either probe `importlib.util.find_spec("xdist")` in `CV_THEME_PYTHON` (using `-n 4` when present and serial with a recorded reason when absent, per `AGENTS.md:89-91`) while keeping `--parallel 4` on `example/manage.py test`, or explicitly surface `pytest-xdist` in the `06-02` precondition gate.

### Risk Assessment
**MEDIUM** — The provenance and validation design is thorough, but the interaction between `data-cv-cancel-url=""` (`form.html:3`) and `viewset.js:38-44` in Chromium and the absence of `pytest-xdist` in `../tabler-test/pyproject.toml:32` should be handled carefully during implementation.

---

## 06.6-07

### Summary
Plan `06.6-07` implements the isolated real-Tabler browser harness (`tests/browser/theme-adoption.cjs` and `tests/browser/theme_adoption_server.py`), applies the concrete companion adaptations in the isolated candidate copy (`register_label_mode_defaults({"form": "both"})` in `apps.py`, three native icon mappings in `icons.py`, four button-class keys in `buttons.py`, alert utility/hook updates in `templates/crud_views/tags/alert.html`, and test updates in `tests.py`), and replays the exported `07-tabler-adaptation.patch` against fresh exact-base copies.

### Strengths
- **Concrete native Tabler icon mappings prevent `<i class="fa-...">` regression (`../tabler-test/src/crud_views_tabler/icons.py:12-47`, `../tabler-test/src/crud_views_tabler/tests.py:62-67,173-175,451-452`):** In `../tabler-test/src/crud_views_tabler/icons.py:12-47`, `TABLER_ICONS` currently maps 35 keys (`"delete": "tabler:trash"`, `"filter": "tabler:filter"`, `"filter-close": "tabler:filter-x"`, `"message-success": "tabler:check"`, etc.) but omits `"save"`, `"cancel"`, and `"filter-reset"`. Adding `"save": "tabler:check"`, `"cancel": "tabler:arrow-left"`, and `"filter-reset": "tabler:filter-x"` in `07-02` (`C5-H01`) uses SVG paths already present in `django_tabler.icons.ICONS`, fixes `TablerIconTests.test_every_upstream_icon_name_is_mapped` (`tests.py:62-67`), and prevents `register_label_mode_defaults({"form": "both"})` from rendering Font Awesome `<i>` fallback tags on filter/form buttons (which would break `self.assertNotIn("<i class=", html)` at `tests.py:175` and `tests.py:452`).
- **Exact `TABLER_BUTTON_CLASSES` dictionary synchronization (`../tabler-test/src/crud_views_tabler/buttons.py:3-44`, `../tabler-test/src/crud_views_tabler/tests.py:84-139`):** `ButtonClassTests.test_table_values` (`tests.py:98-139`) asserts exact dict equality (`self.assertEqual(TABLER_BUTTON_CLASSES, expected)`). Updating both `buttons.py` and `expected` in `tests.py:98-139` with the exact four pairs (`"form:actions": "d-flex flex-wrap gap-2"`, `"form:filter-actions": "d-flex flex-wrap gap-1"`, `"alert:dismissible": "alert-dismissible fade show"`, `"alert:close": "btn-close"`) while `DEFAULT_BUTTON_CLASSES` in core gains the same four keys keeps both `test_table_values` (`line 139`) and `test_every_theme_key_is_an_upstream_key` (`line 88`) green (`C5-A08`).
- **Strict named-hook message parity without breaking `django_tabler` standalone independence (`../tabler-test/src/crud_views_tabler/templates/crud_views/tags/alert.html:7,17`, `../tabler-test/src/crud_views_tabler/tests.py:556-573`):** `crud_views_tabler/templates/crud_views/tags/alert.html:17` currently emits `data-bs-dismiss="alert"`, whereas `django_tabler/includes/messages.html` is used standalone without `crud_views` JS. Updating `crud_views_tabler`'s `tags/alert.html:17` to use `{% cv_button_class "alert" "close" %}` and `data-cv-alert-dismiss` while updating `MessagesParityTests.test_plain_include_matches_cv_messages` (`tests.py:556-573`) to assert the exact `data-bs-dismiss="alert"` vs. `data-cv-alert-dismiss` hook swap preserves full markup parity and `django_tabler.tests.PackageTests` independence (`C4-A02`).
- **Verified existing template shadows (`../tabler-test/src/crud_views_tabler/templates/crud_views/snippets/form_frame.html:1-6`, `tags/list_filter.html:1-11`, `tags/list_filter.inner.html:1-14`):** Inspection of the embedded companion templates confirms `form_frame.html:1-6` only wraps `{% block cv_form_body %}` in `<div class="card"><div class="card-body">` on non-modal requests, and `list_filter.inner.html:10-12` wraps `{% crispy filter.form filter.form.helper %}` in `<form id="filter-form" method="get">`, while `crud_views_tabler` has no override of `crud_views/tags/form.html` or `view_workflow.action.html` (`tests.py:251-263,406-421`).

### Concerns
- **[MEDIUM] Chromium click/keyboard activation of empty-string `data_cv_cancel_url=""` vs. `None` (`src/crud_views/templates/crud_views/tags/button/form.html:3`, `src/crud_views/static/crud_views/js/viewset.js:38-44`, `06.6-07-PLAN.md` Task `07-02` lines 124-132):** As traced in `06.6-06`, in `src/crud_views/lib/view/button_data.py:354-393` and `src/crud_views/templates/crud_views/tags/button/form.html:3`, an absent/`None` cancel destination (`cv_cancel_key=None` / `data_cv_cancel_url=None`) omits `data-cv-cancel-url` completely, whereas an explicit empty string `data_cv_cancel_url=""` renders `<button type="button" ... data-cv-cancel-url="">`. When `viewset.js` (`src/crud_views/static/crud_views/js/viewset.js:38-44`) is active in Chromium on a Tabler page (`crud_views_tabler/page.html:16`), clicking or keyboard-activating an element with `data-cv-cancel-url=""` matches `e.target.closest("[data-cv-cancel-url]")` and assigns `globalThis.location.href = ""`, which reloads the page in Chromium and resets any edited `<input>` value.

### Suggestions
- In `tests/browser/theme_adoption_server.py` and `tests/browser/theme-adoption.cjs` (Task `07-02`), use a view with `cv_cancel_key = None` (which produces `cv_cancel_url = None` via `src/crud_views/lib/view/base.py:750,823` and omits `data-cv-cancel-url`) for the live Chromium click/keyboard preserved-input test across `both`, `icon`, and `label` modes (with and without `form:cancel-tag = "a"`), and if also clicking a `data_cv_cancel_url=""` control in Chromium, spy/prevent `location.href` reload or test `data_cv_cancel_url=""` DOM fallback in `ThemeAdoptionTests`.

### Risk Assessment
**MEDIUM** — All five companion files (`apps.py`, `buttons.py`, `icons.py`, `tags/alert.html`, `tests.py`) and their interactions with core are verified line-by-line against the embedded companion source; avoiding the `viewset.js` empty-attribute reload in Chromium is the main execution subtlety.

---

## 06.6-08

### Summary
Plan `06.6-08` updates the reference documentation (`docs/reference/theme.md`, `docs/reference/action_menus.md`, `docs/reference/settings.md`), migration guide (`docs/migrating-1.0.md`), and `CHANGELOG.md`, accompanied by executable documentation tests in `tests/test1/test_theme_adoption_docs.py` and updated assertions in `tests/test1/test_label_mode_docs.py`.

### Strengths
- **Preserves strict structural guards in `tests/test1/test_alerts.py` and `tests/test1/test_label_mode_docs.py`:**
  - `tests/test1/test_alerts.py:249-255` (`_documented_alert_frame`) asserts that `### Custom alert frame` under `## Alerts` in `docs/reference/theme.md:308-321` contains **exactly one** `django`/`html` code fence (`assert len(bodies) == 1`). Task `08-01` explicitly places the new `alert:dismissible` / `alert:close` guidance outside that section's fence and runs `test_alerts.py` in `08-01`'s verify step.
  - `tests/test1/test_label_mode_docs.py:777-815` (`test_migration_e108_location_inventory`) asserts exact substrings on the E108 paragraph in `docs/migrating-1.0.md:61-64` (`"otherwise it logs one warning and the location falls back to its package floor."`). Task `08-01` leaves `docs/migrating-1.0.md` and `test_migration_e108_location_inventory` untouched until Task `08-02` updates both together in one commit (H07).
- **Documents and tests standalone `CrispyModelForm` wrapper removal (`C2-A02`):** Because `CrispyFormMixin.helper` (`src/crud_views/lib/crispy/form.py:43-50`) now sets `form_tag = False`, callers rendering a `CrispyModelForm` via standalone `{% crispy form %}` outside `cv_render_form` must supply their own `<form>` tag while keeping crispy's CSRF token. Tasks `08-01` and `08-02` provide an executable recipe and paired `### Breaking` / `docs/migrating-1.0.md` entry.

### Concerns
- **[LOW] Exact phrase and step-count guards in `tests/test1/test_label_mode_docs.py:120-252,664-750`:** `tests/test1/test_label_mode_docs.py` enforces tight regex and substring invariants on `docs/reference/settings.md` and `docs/reference/action_menus.md`:
  - `test_label_mode_configuration_table` (`lines 145-177`) checks exact table cells in `### Label-mode configuration` (e.g., `"`CRUD_VIEWS_LABEL_MODE_DEFAULTS`": ("merged per location", "project floor", '"card"')` at `line 146`) and exact phrases in `flat` (`lines 166-177`).
  - `test_canonical_label_mode_resolution_sections` (`lines 190-229`) and `test_form_label_mode_reference_contract` (`lines 709-717`) count the exact number of numbered list items (`^\d+\. `) in `### Context label-mode resolution` (5 steps), `### List label-mode resolution` (2 steps), `### Card label-mode resolution` (3 steps, with `'"both"' in card[2]` at `line 223`), and `### Form label-mode resolution` (5 steps, with `'`default_label_mode("form")`' in mode[1] and '`"label"`' in mode[1]` at `line 716`).
  Task `08-01` rightly instructs describing the three floor layers (`package -> theme -> project`) *inside* the existing final floor step rather than adding a new numbered step, and keeping the `"both"` / `"label"` package-default tokens in those steps so `lines 223` and `716` continue to match unless updated in lockstep in `test_label_mode_docs.py`.

### Suggestions
- When editing `docs/reference/action_menus.md` and `docs/reference/settings.md` in Task `08-01`, keep `'`default_label_mode("form")`'`, `'`"label"`'`, and `'"both"'` present in the final numbered steps of `### Form label-mode resolution` (`test_label_mode_docs.py:716`) and `### Card label-mode resolution` (`test_label_mode_docs.py:223`), and verify all assertions in `tests/test1/test_label_mode_docs.py:120-252,664-750` before committing.

### Risk Assessment
**LOW** — All existing documentation test guards in `tests/test1/test_label_mode_docs.py` and `tests/test1/test_alerts.py` have been identified and included in the task verification commands.

---

## 06.6-09

### Summary
Plan `06.6-09` runs in Wave 5 after Plans `06.6-07`, `06.6-08`, and `06.6-10` complete, extending `noxfile.py` (`CRISPY_FLOOR_TESTS` at `noxfile.py:28-52`) with the new theme-adoption test modules, executing the full multi-series Python, crispy-floor (Django 4.2 and 6.0), `examples/bootstrap5`, Vitest, fragment integration, browser lifecycle, docs, and lint gates, validating the committed companion delivery (`--check-final`), and producing `06.6-PUBLIC-SURFACE.md` and `06.6-ACCEPTANCE.md` for Phase 7.

### Strengths
- **Permanent `CRISPY_FLOOR_TESTS` expansion verified via AST (`noxfile.py:28-52`, `06.6-09-PLAN.md` Task `09-01`):** `noxfile.py:28-52` currently lists 23 test files in `CRISPY_FLOOR_TESTS` and omits `tests/test1/test_alerts.py`, `tests/test1/test_button_classes.py`, and the five new `tests/test1/test_theme_*.py` files. Appending those seven modules to `CRISPY_FLOOR_TESTS` while keeping `CRISPY_FLOOR_DESELECT` (`noxfile.py:57`) restricted to `test_filter_form_baseline` ensures future `nox -s crispy_floor` runs permanently guard the floor bridge and theme seams.
- **Comprehensive cross-artifact `--check-final` gate (`tests/browser/theme_adoption_sources.py`):** Task `09-01` verifies that `10-companion-delivery.json` (committed in core), `07-tabler-replay.json`, `07-browser-results.json`, and `06-companion-baseline.json` all bind to matching source/test/asset/runtime hashes, that `form_probe`, `delivered_probe`, and `committed_probe` retain complete sanitized logs (`C6-A02`), that `cancel-no-url` and all five action kinds across `both`/`icon`/`label` modes pass (`C5-H01`, `C6-A01`), and that the companion repository commit and untouched `example/config/settings.py` state validate via `--delivered-source recorded` (`C5-A01`, `C6-A03`).
- **Explicit matrix boundary for current-pack Django 6.0 (H12) and dual floor runs (`C2-A03`):** Both `.nox/crispy_floor-3-12-django-4-2` and `.nox/crispy_floor-3-12-django-6-0` are executed and recorded separately alongside `.nox/tests-3-12-django-4-2` and `.nox/tests-3-12-django-5-2`, without misrepresenting floor runs as current-pack Django 6.0 coverage.

### Concerns
- None beyond the upstream `C6-A01` empty-string `data-cv-cancel-url=""` browser click behavior and `tabler-test/.venv` `xdist` check already noted under `06.6-06` and `06.6-07`.

### Suggestions
- Ensure `06.6-PUBLIC-SURFACE.md` explicitly lists `register_label_mode_defaults`, `form:actions`, `form:filter-actions`, `alert:dismissible`, `alert:close`, and `cv_form_helper` with their exact module/template paths so Phase 7 (`tests/test1/test_stability_doc.py`, STAB-01–03) can consume them directly without re-auditing Phase 06.6 commits.

### Risk Assessment
**LOW** — Wave 5 sequencing after `06.6-07`, `06.6-08`, and `06.6-10` ensures all code, documentation, and companion delivery artifacts are settled before final verification runs.

---

## 06.6-10

### Summary
Plan `06.6-10` delivers the replay-verified companion changes from Plan `06.6-07` into the user-supplied `../tabler-test` repository under amended D-11/D-14, commits the companion source/test delta (`apps.py`, `buttons.py`, `icons.py`, `templates/crud_views/tags/alert.html`, `tests.py`, and conditional `formactions.html`) using a private temporary `GIT_INDEX_FILE` that preserves `example/config/settings.py` and any unrelated staged/unstaged work, and commits `10-companion-delivery.json` and `07-TABLER-HANDOFF.md` in the core repository.

### Strengths
- **Shared companion commit boundary (`10-01` + `10-02`) prevents broken intermediate companion state (`C5-A01`, `C5-A08`):** Delivering `buttons.py` (`TABLER_BUTTON_CLASSES`) in `10-01` without `tests.py` (`ButtonClassTests.test_table_values` at `../tabler-test/src/crud_views_tabler/tests.py:98-139`) would fail `test_table_values` if committed alone. Grouping `10-01` and `10-02` into one verified companion commit after `10-02`'s provisional `--verify-replay --delivered-source recorded` gate passes, followed by a separate core commit in `10-03` for `10-companion-delivery.json` and `07-TABLER-HANDOFF.md`, cleanly respects both the companion test suite and the GSD executor's core commit ledger (`gsd-plan-head-before-06.6-10`).
- **Private `GIT_INDEX_FILE` index-isolation protocol (`06.6-10-PLAN.md` lines 88-115):** Constructing a temporary index from `git -C "$COMPANION_ROOT" read-tree "$COMPANION_HEAD_BEFORE"`, applying only the verified patch with `git apply --cached`, committing with that temporary `GIT_INDEX_FILE`, and reconciling the live index via `git apply --cached --3way` under `index.lock` only if the original index snapshot is unchanged guarantees that `example/config/settings.py` and any unrelated staged/unstaged hunks in either repository are never swept into a commit or overwritten.
- **No unnecessary pack template modification (`../tabler-test/src/django_tabler/templates/crispy_tabler/layout/formactions.html`):** As noted in `06.6-RESEARCH.md:299-301` and `10-01`/`10-02`, `crispy_tabler/layout/formactions.html` already consumes `formactions.css_class`, so `formactions.html` is touched only if `07`'s verified patch required a hunk.
- **Self-contained committed delivery evidence (`C6-A02`, `C6-A03`):** All four verification commands in `10-01`, `10-02`, and `10-03` use `--delivered-source recorded` and persist `form_probe`, `delivered_probe`, and `committed_probe` (with sanitized logs and digests) inside `.planning/phases/06.6-theme-adoption-seams-from-the-tabler-sync/10-companion-delivery.json`.

### Concerns
- **[LOW] Avoiding self-referential core commit hashes in `10-companion-delivery.json` (`06.6-10-PLAN.md` Task `10-03`, lines 113-114, 178-198):** In Task `10-03`, `--verify-replay --delivered-source recorded --require-committed --output ...10-companion-delivery.json` runs *before* `10-03` commits `10-companion-delivery.json` and `07-TABLER-HANDOFF.md` in core. As lines 113-114 note ("Avoid self-referential hashes: the delivery manifest records its core parent and evidence hashes; the SUMMARY records the resulting core commit"), `--require-committed` in `theme_adoption_sources.py` must require the **companion** commit to be present at `10-02`/`10-03` verification time, whereas the **core** `10-03` evidence commit is verified afterward by `09-01` (`--check-final`) and `gsd_run check evaluation-scope`. If `--require-committed` in `10-02`/`10-03` demanded that `10-companion-delivery.json` already be committed in core before `10-03` commits it, `10-02` and `10-03`'s `<verify>` commands would deadlock.

### Suggestions
- Ensure `--verify-replay --delivered-source recorded --require-committed` in `tests/browser/theme_adoption_sources.py` checks that the **companion** repository commit is clean and matches the candidate delta (recording the core parent HEAD and file digests in `committed_probe`), while `--check-final` in Plan `06.6-09` additionally verifies that `10-companion-delivery.json` and `07-TABLER-HANDOFF.md` are committed in the core repository.

### Risk Assessment
**LOW** — The cross-repository commit protocol, index preservation, and evidence embedding are explicitly specified and align with both user authorization (amended D-11/D-14) and the GSD executor contract.

---

## Cross-Plan Comparison and Overall Assessment

### Wave and Dependency Ordering
- **Wave 1 (`06.6-01`, `06.6-04`, `06.6-06`):** Disjoint `files_modified` sets. Both `06.6-01` and `06.6-06` create independent task-owned temporary archives of pre-phase commit `cb26af4dfef2afb31d774a219abfad1c675cdff1` so concurrent Wave 1 execution cannot contaminate baselines (`A01`). `06.6-04` updates `DEFAULT_BUTTON_CLASSES` and `EXPECTED_KEYS` from 84 to 86.
- **Wave 2 (`06.6-02`, `06.6-03`, `06.6-05`):** `06.6-02` and `06.6-05` depend on `06.6-01`; `06.6-03` depends on both `06.6-01` and `06.6-04` and updates `DEFAULT_BUTTON_CLASSES` and `EXPECTED_KEYS` from 86 to 88 (`H04`). Disjoint `files_modified` across `06.6-02`, `06.6-03`, and `06.6-05` except `tests/test1/test_form_button_checks.py` (which is modified by `06.6-02` and only read/executed in `06.6-05`'s `05-02` verify command).
- **Wave 3 (`06.6-07`, `06.6-08`):** Disjoint `files_modified` sets (`06.6-07` owns `tests/browser/theme-adoption*` and `07-*` artifacts; `06.6-08` owns `docs/*`, `CHANGELOG.md`, `test_theme_adoption_docs.py`, and `test_label_mode_docs.py`).
- **Wave 4 (`06.6-10`):** Depends on `06.6-07`; delivers verified companion changes to `../tabler-test` and commits `10-companion-delivery.json` and `07-TABLER-HANDOFF.md` in core.
- **Wave 5 (`06.6-09`):** Depends on `06.6-07`, `06.6-08`, and `06.6-10`; runs final multi-series/floor/browser/docs/lint gates and `--check-final`.

### Verification of Cycle 6 / Cycle 7 Focus Areas
1. **`C5-H01` / `C5-A08` (Concrete `form=both`, native Tabler `save`/`cancel`/`filter-reset` icons, four class keys, and `test_table_values` sync):** Verified against `../tabler-test/src/crud_views_tabler/{apps.py,buttons.py,icons.py,tests.py}`. All three new icon mappings (`save: tabler:check`, `cancel: tabler:arrow-left`, `filter-reset: tabler:filter-x`) and all four class keys are specified identically across Plans `06`, `07`, `09`, and `10`.
2. **`C5-A01` (Bounded companion commit for `10-01`/`10-02` + core evidence commit for `10-03` + index preservation):** Verified against the installed `gsd-executor` contract (`_GSD_LEDGER`, `COMMITS_ACTUAL`, `evaluation-scope`).
3. **`C6-A01` (URL-less cancel across `both`/`icon`/`label` modes):** Incorporated across Plans `06`, `07`, `09`, and `10`. As noted in `06.6-06` and `06.6-07`, the executor should account for the difference between `cv_cancel_url=None` (no `data-cv-cancel-url` attribute emitted by `src/crud_views/templates/crud_views/tags/button/form.html:3`) and `cv_cancel_url=""` (`data-cv-cancel-url=""` emitted, which `src/crud_views/static/crud_views/js/viewset.js:38-44` intercepts on click in Chromium).
4. **`C6-A02` & `C6-A03` (Embedded sanitized probes/logs in `10-companion-delivery.json` and `--delivered-source recorded` resolution):** Incorporated consistently across Plans `06`, `07`, `09`, and `10`.

### Overall Risk Assessment
**LOW-MEDIUM** — All ten plans are cohesive, well-sequenced across five waves, and grounded in the actual core and companion source files. Addressing the two minor execution subtleties noted in `06.6-06`/`06.6-07` (`data-cv-cancel-url=""` click handling under `viewset.js` in Chromium and `pytest-xdist` detection in `../tabler-test/.venv`) will ensure smooth autonomous execution.
