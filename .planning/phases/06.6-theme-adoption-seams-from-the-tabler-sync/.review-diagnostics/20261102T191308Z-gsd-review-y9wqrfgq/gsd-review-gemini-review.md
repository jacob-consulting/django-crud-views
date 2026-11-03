## 06.6-01

### 1. Summary
Plan `06.6-01` establishes single-form and single-CSRF-token ownership for CRUD create views and hardens `cv_render_form` against helper mutation, double evaluation, and incompatible wrapper configuration (`D-01`–`D-04`, `D-16`). It aligns the library helpers (`CrispyFormMixin.helper` and `CrispyDeleteForm.helper`) with the outer `<form class="cv-form">` already owned by the page templates, preserves `Context.dicts` across `cv_render_form`, and bundles the dependent custom-helper test fixtures and four `form_frame` goldens into a single green commit (`01-01` + `01-02`).

### 2. Strengths
- **Fixes verified nested-form and duplicate-CSRF emission at the source (`src/crud_views/lib/crispy/form.py:43-50,136-146` and `tests/test1/golden/form_frame/create.html:1`):** `CrispyFormMixin.helper` (`form.py:45`) and `CrispyDeleteForm.helper` (`form.py:138`) currently instantiate `FormHelper()` with default `form_tag=True`, while `src/crud_views/templates/crud_views/view_create.content.html:5-11` (and `view_update.content.html:5-11`, `view_custom_form.content.html:5-11`, `view_delete.content.html:16-22`) already wrap `{% cv_render_form %}` in `<form class="cv-form" method="post" ...>{% csrf_token %}`. The committed golden `tests/test1/golden/form_frame/create.html:1` proves the current defect (`<form class="cv-form" ...><input type="hidden" name="csrfmiddlewaretoken" value="CSRF"><form method="post" ><input type="hidden" name="csrfmiddlewaretoken" value="CSRF">...`).
- **Preserves `Context.dicts` for button owner-tier resolution (`src/crud_views/templatetags/crud_views.py:453-455,464-466` and `src/crud_views/lib/crispy/buttons.py:49-92`):** `cv_render_form` (`crud_views.py:466`) currently calls `render_to_string(..., context.flatten())`, which collapses the context stack that `_cv_helper_tier` (`buttons.py:49-61`) and `_cv_page_tier` (`buttons.py:64-77`) scan to distinguish `_is_response_overlay` layers from page layers. Switching to `get_template(...).template.render(context)` with `context.push(cv_form_helper=...)` (matching `cv_alert` at `crud_views.py:453-455`) preserves stack-tier semantics.
- **Eliminates double evaluation and truthiness traps on `form.helper` (`src/crud_views/templates/crud_views/tags/form.html:3-6`):** `tags/form.html:3-4` currently evaluates `{% if form.helper %}` and then `{% crispy form form.helper %}`, which invokes the `@property def helper` getter (`form.py:43-50`) twice per render and treats an empty `FormHelper()` (whose `__len__` is `0`) as falsy. Passing `cv_form_helper` once fixes both issues.
- **Atomic fixture and golden migration (`tests/test1/test_form_button_checks.py:560-586,1082-1110`):** `_CustomHelperForm.helper` (`test_form_button_checks.py:563-567`) and `_DeleteCustomHelper.helper` (`test_form_button_checks.py:581-585`) leave `form_tag=True` and are exercised via live endpoints at lines `1085-1110`. Migrating them in Task `01-02` within the same commit as `01-01` prevents breaking existing missing-icon runtime policy tests when `D-01` lands.
- **Separates standalone crispy wrapper removal from `cv_render_form` CSRF suppression (`C2-A02`):** Setting `form_tag=False` on `CrispyFormMixin.helper` while keeping `disable_csrf=True` local to `cv_render_form` preserves CSRF tokens for standalone `{% crispy form form.helper %}` renders and explicitly records the outer-`<form>` removal for Plan `08`'s migration guide.

### 3. Concerns
- **[LOW] Plain `forms.Form` instances without a `.helper` attribute must not gain an attached `.helper` side effect (`tests/test1/test_form_frame.py:34-41`, `../tabler-test/src/crud_views_tabler/tests.py:37-38,296-299`):** Both `NameForm` (`test_form_frame.py:34-35`) and the companion's `ProbeForm` (`../tabler-test/src/crud_views_tabler/tests.py:37-38`) are plain `django.forms.Form` subclasses with no `.helper` attribute. When `_prepare_form_helper(form)` creates a default nonwrapping helper for a form where `getattr(form, "helper", None) is None`, it must only bind that helper to `cv_form_helper` in the pushed template context and never assign `form.helper = ...` on the caller's form instance.

### 4. Suggestions
- In `test_helper_adaptation_contract` (`01-01`), include an explicit assertion on a plain `forms.Form()` instance rendered through `cv_render_form` verifying that `hasattr(form, "helper")` remains `False` after rendering and that `form.media` is still emitted exactly once (`include_media=True` default).

### 5. Risk Assessment
- **LOW** — The render seam in `src/crud_views/templatetags/crud_views.py:464-466` and `src/crud_views/templates/crud_views/tags/form.html:1-7` is small and well-isolated, and bundling `01-01` with `01-02` avoids intermediate test-suite breakage.

---

## 06.6-02

### 1. Summary
Plan `06.6-02` introduces `register_label_mode_defaults(defaults)` in `src/crud_views/lib/view/label_mode.py` to provide an atomic, per-key merged theme floor (`package -> theme -> project setting`) below explicit view/button label modes (`D-05`–`D-07`, `D-15`), while preserving lazy `override_settings` responsiveness, `E108` validation, and `W292` effective-floor diagnostics.

### 2. Strengths
- **Matches existing resolver and fallback architecture (`src/crud_views/lib/view/label_mode.py:63-146`):** `default_label_mode(location)` (`label_mode.py:86-119`) currently falls back to `LABEL_MODE_DEFAULTS[location]` at lines `101`, `107`, `110`, and `118`. Routing those four sites through `_theme_or_package_default(location)` (reading only the rebound `_THEME_LABEL_MODE_DEFAULTS` snapshot and `LABEL_MODE_DEFAULTS`) prevents infinite recursion when `form_label_mode` (`label_mode.py:122-145`) falls back to `default_label_mode("form")` while `CRUD_VIEWS_LABEL_MODE_DEFAULTS` is also malformed (`C3-A03`).
- **Seamless integration with `W292` static checks (`src/crud_views/lib/view/buttons.py:435-438,568-574`):** Both context `W292` (`buttons.py:435`) and form `W292` (`buttons.py:570`) call `cls.cv_get_action_label_mode(...)` (`src/crud_views/lib/view/base.py:316-350`), which delegates unnamed keys to `default_label_mode(...)`. Updating `default_label_mode` automatically makes `W292` respect the registered theme layer without instantiating forms at startup.
- **Process and worker isolation (`tests/test1/conftest.py:23-32`):** `conftest.py:23-32` currently resets only `label_mode._warned`. Adding an `autouse=True` fixture to snapshot and restore `_THEME_LABEL_MODE_DEFAULTS` by module-attribute rebind prevents state leaks across tests in the same `pytest-xdist` worker.

### 3. Concerns
- **[LOW] Existing `E211`/`W291` check message strings are pinned by exact-string assertions (`tests/test1/test_form_button_checks.py:57-73`):** `test_form_button_checks.py:57` defines `FLOOR_HINT = "kinds not named take the form floor CRUD_VIEWS_LABEL_MODE_DEFAULTS['form']"` and asserts exact message equality for `viewset.E211` and `viewset.W291` (`lines 60-73`). When Task `02-02` updates "stale resolver/settings descriptions to name all three layers" in `src/crud_views/lib/view/label_mode.py` and `src/crud_views/lib/settings.py`, it must only update docstrings/comments and not alter the `viewset.E211`, `viewset.W291`, or `crud_views.E108` (`settings.py:165-189`) runtime check message strings.

### 4. Suggestions
- Keep `crud_views.E108` (`src/crud_views/lib/settings.py:165-189`) and `viewset.E211`/`W291` message strings byte-identical while updating the comments/docstrings in `src/crud_views/lib/settings.py:61-73,159-160` and `src/crud_views/lib/view/label_mode.py:22-23,86-93`.

### 5. Risk Assessment
- **LOW** — The precedence and atomic rebind rules are tightly specified, and `W292` already routes through `default_label_mode()`.

---

## 06.6-03

### 1. Summary
Plan `06.6-03` adds the `form:actions` and `form:filter-actions` utility keys (`default ""`) to `DEFAULT_BUTTON_CLASSES` (`D-09`, `D-10`, `D-17`), wires them into the three library `FormActions` constructors, and provides a narrowly scoped `_ThemedFormActions` bridge for the declared `crispy-bootstrap5==2023.10` floor where `FormActions.css_class` is ignored by the upstream template.

### 2. Strengths
- **Covers all three default `FormActions` construction sites (`src/crud_views/lib/crispy/form.py:55-56,141-144` and `src/crud_views/lib/views/list.py:125-133`):** `CrispyFormMixin.get_form_actions` (`form.py:55-56`), `CrispyDeleteForm.helper` (`form.py:141-144`, which does not call `get_form_actions()`), and `ListViewFilterFormHelper.get_form_actions` (`list.py:125-133`) are all explicitly targeted.
- **Handles cached filter action groups across dynamic class changes and `deepcopy` (`src/crud_views/lib/views/list.py:155,174-179`):** `ListViewFilterFormHelper._cv_prepare_layout` (`list.py:155`) deep-copies `self.layout`, and `render_layout` (`list.py:174-179`) caches `self._cv_actions = self.get_form_actions()` once per prepared layout. Storing the class-table key (`"form:actions"` / `"form:filter-actions"`) and base `css_class` as primitive attributes on `_ThemedFormActions` and resolving `get_button_class(...)` at render time avoids stale cached classes or class accumulation across repeated renders (`H05`).
- **Strict floor-bridge provenance and accurate floor template characterization (`C4-A04`, `noxfile.py:24,96-98`):** Task `03-01` activates `crud_views/crispy/bootstrap5_formactions.html` only when `template_pack == "bootstrap5"`, the resolved template origin belongs to the installed `crispy_bootstrap5` package, and its full source matches the audited `2023.10` floor template (`attrs`/`flat_attrs`, label/field-class branches, `fields_output`), while testing both cached floor environments (`.nox/crispy_floor-3-12-django-6-0` and `.nox/crispy_floor-3-12-django-4-2`) in `03-03` (`C2-A03`).
- **Clean sequencing of key-count updates (`tests/test1/test_button_classes.py:105`, `docs/reference/buttons.md:151`):** Depending on `06.6-04` and advancing the key count from `86` to `88` in `03-02` avoids merge/assertion conflicts on `EXPECTED_KEYS` (`test_button_classes.py:21-91`).

### 3. Concerns
- **[LOW] Static `W292` inspection checks `_inherits(form_class, "get_form_actions", CrispyFormMixin)` (`src/crud_views/lib/view/buttons.py:513,538`):** In `src/crud_views/lib/view/buttons.py:513` and `538`, `_static_form_controls` and `_static_filter_controls` verify that `get_form_actions` is still the un-overridden `CrispyFormMixin.get_form_actions` or `ListViewFilterFormHelper.get_form_actions`. Default subclasses remain statically inspectable because the base methods themselves return `_ThemedFormActions`, whereas subclasses that override `get_form_actions()` via the `super().get_form_actions()` opt-in recipe become dynamic (skipping static `W292` and relying on runtime `cv_button_data` checks, just like `_NoActionsHelper` in `tests/test1/test_form_button_checks.py:763-777`). Ensure `03-02`'s tests and `08-01`'s docs do not claim static `W292` runs on overridden `get_form_actions()` methods.

### 4. Suggestions
- In `test_theme_action_groups.py` (`03-02`), add an assertion confirming that un-overridden `AuthorForm` / `PublisherFilterFormHelper` still pass `_inherits(..., "get_form_actions", ...)` for static `W292` after wiring `_ThemedFormActions`.

### 5. Risk Assessment
- **LOW** — The floor problem was already reproduced and isolated in research, and the exact-source discriminator prevents unintended template shadowing on custom or newer packs.

---

## 06.6-04

### 1. Summary
Plan `06.6-04` introduces the `alert:dismissible` (`"alert-dismissible fade show"`) and `alert:close` (`"btn-close"`) utility keys in `src/crud_views/lib/button_classes.py` and consumes them in `src/crud_views/templates/crud_views/tags/alert.html` (`D-08`, `D-17`), preserving byte-identical default output against `tests/test1/golden/alerts/dismissible.html`.

### 2. Strengths
- **Preserves byte-exact golden output and clean empty-value spacing (`src/crud_views/templates/crud_views/tags/alert.html:2-5`, `tests/test1/golden/alerts/dismissible.html:1-7`, `tests/test1/test_alerts.py:166-203`):** `test_dismissible_alert_golden` (`test_alerts.py:166-181`) compares `markup.encode("utf-8")` against `tests/test1/golden/alerts/dismissible.html` with zero whitespace normalization, and `test_dismissible_alert_preserves_frame_contract` (`test_alerts.py:191-203`) asserts `frame.get("class") == "alert alert-success alert-dismissible fade show"` and `control.get("class") == "btn-close"`. Resolving `alert:dismissible` into a variable and prefixing a space only when nonempty (`A03`) preserves exact default bytes while avoiding a trailing space (`"alert alert-success"`) when omitted (`""` or `None`).
- **Automatically integrates with `W362` and `E361` checks (`src/crud_views/lib/button_classes.py:286-294,328-346`):** Adding `"alert:dismissible"` and `"alert:close"` to `DEFAULT_BUTTON_CLASSES` (`button_classes.py:92-96`) makes `button_class_check_messages()` accept them as base keys (`line 329`), reject non-string values with `E361` (`line 287`), and warn with `W362` on mode-suffixed variants like `alert:close:icon` (`line 340`, since `"alert"` is neither in `VARIANT_LOCATIONS` nor `"form"` at `lines 239-240,263`).
- **Synchronizes key inventory in the same commit (`tests/test1/test_button_classes.py:21-91,105`, `docs/reference/buttons.md:151`):** Updating `EXPECTED_KEYS` and the documented key count from `84` to `86` in `04-01` keeps `test_default_table_is_complete` and `test_documented_default_key_count_matches_table` green at the Wave 1 commit boundary.

### 3. Concerns
- **[LOW] `docs/reference/theme.md:310` prose reference to literal alert classes (`tests/test1/test_alerts.py:249-317`):** `docs/reference/theme.md:310` currently says `The frame's own classes (alert-dismissible fade show, btn-close) are literal Bootstrap CSS.` Plan `04` leaves `docs/reference/theme.md` untouched (owned by Plan `08-01`), which is appropriate for wave separation; ensure `08-01` updates that sentence above `### Custom alert frame` while keeping the single `django`/`html` code fence inside `### Custom alert frame` intact for `test_documented_alert_frame_override` (`test_alerts.py:249-259`).

### 4. Suggestions
- None required for Plan `04` itself; the boundary with Plan `08-01` (`H08`) is cleanly drawn.

### 5. Risk Assessment
- **LOW** — Straightforward two-key table addition and template lookup guarded by an existing byte-exact golden test (`tests/test1/test_alerts.py:166-181`).

---

## 06.6-05

### 1. Summary
Plan `06.6-05` routes the full-page workflow action template (`src/crud_views_workflow/templates/crud_views_workflow/view_workflow.action.html`) through `{% cv_render_form %}`, verifies the full-page and supported-modal request/CSRF matrix across all five actionable form types (`D-16`), and removes the redundant `form_tag = False` parent formset helper workarounds in `tests/test1/app/views_formset.py` and `examples/bootstrap5/formsets/views.py`.

### 2. Strengths
- **Fixes the workflow template bypass (`src/crud_views_workflow/templates/crud_views_workflow/view_workflow.action.html:1-19`):** `view_workflow.action.html:8-16` wraps `{% crispy form form.helper %}` inside `<form class="cv-form" method="post" novalidate>{% csrf_token %}`. Replacing `{% crispy form form.helper %}` at line `15` with `{% cv_render_form %}` and dropping unused `{% load crispy_forms_tags %}` at line `2` (`A12`) eliminates the nested `<form>` and duplicate CSRF token on workflow pages.
- **Accurately distinguishes workflow modal inheritance from full-page workflow templates (`src/crud_views_workflow/lib/views.py:18-27`, `src/crud_views/lib/views/form.py:18-20`, `src/crud_views/templates/crud_views/modal/content.html:8`):** `WorkflowView` (`views.py:18`) subclasses `CustomFormView` (`form.py:10`), which sets `cv_content_template = "crud_views/view_custom_form.content.html"` and `cv_modal_supported = True`, while `WorkflowView` only overrides `template_name = "crud_views_workflow/view_workflow.html"`. Thus modal requests (`modal/content.html:8`: `{% include view.cv_content_template %}`) render `crud_views/view_custom_form.content.html`, whereas full-page requests render `crud_views_workflow/view_workflow.content.html` (`lines 1-5`) and `view_workflow.action.html` (`C3-A01`).
- **Respects `cv_modal_supported` boundaries (`C2-A01`, `tests/test1/test_modal.py`):** Only `custom_form`, `delete`, and `workflow` support `X-CV-Modal` HTTP requests (`cv_modal_supported = True`), whereas `create` and `update` inherit `cv_modal_supported = False` and reject modal opt-in with `viewset.E251`.
- **Restores static `W292` inspection for parent formset forms (`tests/test1/app/views_formset.py:44-50`, `examples/bootstrap5/formsets/views.py:36-41`, `src/crud_views/lib/view/buttons.py:512`):** Removing the redundant `@property def helper` overrides in `PublisherFormSetForm` and `QuestionnaireForm` makes `_inherits(form_class, "helper", CrispyFormMixin)` (`buttons.py:512`) return `True`, restoring static `W292` coverage while `test_formset_create_page_has_no_nested_form` (`tests/test1/test_formsets.py:16-35`) is expanded to assert token counts and update/POST paths.

### 3. Concerns
- **[LOW] Unused `FormHelper` import in `examples/bootstrap5/formsets/views.py:4` when removing `QuestionnaireForm.helper` (`examples/bootstrap5/formsets/views.py:36-41`):** Line `4` of `examples/bootstrap5/formsets/views.py` is `from crispy_forms.helper import FormHelper`, which is used only as the return type annotation on `QuestionnaireForm.helper` (`line 37`). Task `05-02` already notes "clean up only imports made unused"—removing line `4` is necessary so `ruff check src tests examples` (`09-01`) does not fail with `F401`.

### 4. Suggestions
- Ensure Task `05-02` removes `from crispy_forms.helper import FormHelper` at `examples/bootstrap5/formsets/views.py:4` when deleting `QuestionnaireForm.helper` (`lines 36-41`).

### 5. Risk Assessment
- **LOW** — Template and formset helper changes are minimal and directly backed by existing and expanded CSRF/request matrices.

---

## 06.6-06

### 1. Summary
Plan `06.6-06` builds the import-pure `tests/browser/theme_adoption_sources.py` provenance and inventory validator and captures the unmodified baseline of the user-supplied `../tabler-test` monorepo (`885dfc791a150fdc715d6fb34c2e6181d6b92f3c`) against the pinned pre-phase core revision (`cb26af4dfef2afb31d774a219abfad1c675cdff1`) in isolated sibling worktrees (`D-11`, `D-13`, `D-18`).

### 2. Strengths
- **Matches the verified `../tabler-test` monorepo structure (`../tabler-test/pyproject.toml:1-38`):** `pyproject.toml:17-18` declares `[tool.uv.sources] django-crud-views = { path = "../django-crud-views", editable = true }`, `requires-python = ">=3.14"` (`line 4`), and `DJANGO_SETTINGS_MODULE = "tests.crispy_tabler.settings"` (`line 35`). Archiving `tabler-test` and `django-crud-views` as sibling directories inside isolated `baseline/` and `candidate/` roots preserves the relative `../django-crud-views` layout without touching the user's dirty `example/config/settings.py`.
- **Exhaustive tree-derived shadow and behavior reconciliation (`C4-A01`, `../tabler-test/src/crud_views_tabler/`):** At `885dfc7`, `src/crud_views_tabler/templates/crud_views/` contains 8 template overrides (`modal/shell.html`, `snippets/form_frame.html`, `table/bootstrap5.html`, `tags/alert.html`, `tags/card.html`, `tags/list_filter.html`, `tags/list_filter.inner.html`, `view_card.content.html`), and `src/crud_views_tabler/` contains custom behavior in `checks.py:8-27` (`check_tabler_icons`) and `icons.py:50-52` (`render`). Task `06-01` enumerates the entire tracked archive tree independently of self-reported manifest counts and tests negative fixtures that omit `modal/shell.html`, `checks.py`, or a newly added candidate behavior file.
- **Supports both isolated baseline/replay and delivered-source validation (`--delivered-source`, `--require-committed`):** Adding read-only delivered-source verification to `theme_adoption_sources.py` in `06-01` cleanly supports Plan `10`'s companion delivery and local commit checks while keeping `--check-baseline` bound to the pinned `885dfc7` archive.

### 3. Concerns
- **[MEDIUM] `pytest-xdist` (`-n 4`) preflight in `../tabler-test/.venv` (`06.6-RESEARCH.md` Runtime availability addendum, `06-01`):** Research notes that `../tabler-test/.venv/bin/python` has Python 3.14.7, Django 6.1.2, crispy-forms 2.7, and crispy-bootstrap5 2026.9, but `pytest-xdist` was absent during the read-only orchestrator preflight, while `06-01` specifies running `-m pytest tests -n 4 -q` and `example/manage.py test ... --parallel 4` and halting if `pytest-xdist` is unavailable. Look at `../tabler-test/pyproject.toml:32`: `test = ["pytest", "pytest-django", "crispy-bootstrap5==2026.9"]`—`pytest-xdist` is **not** a declared dependency of `tabler-test` (`pyproject.toml:32`), and `tabler-test`'s `tests/` suite is a small crispy template-pack suite while `example/manage.py test --parallel 4` uses Django's built-in multiprocessing runner (stdlib `multiprocessing`, no `xdist` needed). Requiring `pytest-xdist` inside `../tabler-test/.venv` (where `pyproject.toml:32` does not declare it and the plan forbids unaudited package installs) would artificially halt `06-02` on a tool not declared by the companion's `pyproject.toml`.

### 4. Suggestions
- In `06-01` / `06-02`, keep `--parallel 4` for `example/manage.py test` (which uses Django's stdlib parallel test runner), and for `tabler-test`'s `-m pytest tests` either detect whether `xdist` is installed in `CV_THEME_PYTHON` (using `-n 4` when present and serial `-m pytest tests -q` with an explicit log note when `xdist` is not in `tabler-test/pyproject.toml:32`, matching the `AGENTS.md` rule *"Use serial execution only for a concrete isolation/order/debugging constraint or a tiny selection... explain the reason"*), rather than halting `06-02` over an undeclared companion plugin.

### 5. Risk Assessment
- **MEDIUM** — The provenance and tree-inventory design is thorough, but unconditionally requiring `-n 4` (`pytest-xdist`) in `../tabler-test/.venv` when `../tabler-test/pyproject.toml:32` only declares `pytest` and `pytest-django` risks an avoidable preflight halt during `06-02`.

---

## 06.6-07

### 1. Summary
Plan `06.6-07` validates the Phase 06.6 seams against the isolated `tabler-test` candidate copy in Chromium (`tests/browser/theme-adoption.cjs` and `theme_adoption_server.py`), adapts `crud_views_tabler` to consume the new label-mode floor, action-group keys, and alert utility/dismissal hooks, preserves strict single-hook parity in `MessagesParityTests` (`C4-A02`), and exports/replays `07-tabler-adaptation.patch` (`D-11`–`D-14`, `D-18`).

### 2. Strengths
- **Resolves the `MessagesParityTests` vs. standalone `django_tabler` hook conflict (`C4-A02`, `../tabler-test/src/crud_views_tabler/templates/crud_views/tags/alert.html:17`, `../tabler-test/src/crud_views_tabler/tests.py:556-573`):** `crud_views_tabler/templates/crud_views/tags/alert.html:17` currently emits `data-bs-dismiss="alert"`, and `MessagesParityTests.test_plain_include_matches_cv_messages` (`tests.py:556-573`) asserts `normalized(plain) == normalized(themed)` against `django_tabler/includes/messages.html`. Keeping standalone `django_tabler/includes/messages.html` on `data-bs-dismiss="alert"` (so standalone `django_tabler` remains dependency-free) while updating `crud_views_tabler`'s `tags/alert.html:17` to `data-cv-alert-dismiss` and asserting that exact single-attribute delta before `normalized(...)` equality in `MessagesParityTests` preserves both standalone Tabler and CRUD adapter dismissal.
- **Avoids manufacturing unneeded template overrides (`C2-A06`, `../tabler-test/src/django_tabler/templates/crispy_tabler/`):** Because `tabler-test` at `885dfc7` does not copy `crud_views/tags/form.html` or `crud_views_workflow/view_workflow.action.html` (`tests.py:251-263,406-420`), and its native `crispy_tabler/layout/formactions.html` already consumes `formactions.css_class`, `07-01`/`07-02` verify inherited rendering rather than adding unnecessary overrides.
- **Port collision safety (`C2-A04`, `tests/browser/presentation-config.test.cjs:13-26`):** `07-01` validates port `1024..65535` (excluding `8143`/`8144`) and checks that an existing listener on `8145` is rejected before spawning and left alive.

### 3. Concerns
- **[HIGH] Registering `{"form": "both"}` in `crud_views_tabler/apps.py` without mapping `"save"`, `"cancel"`, and `"filter-reset"` in `crud_views_tabler/icons.py` causes new Font Awesome `<i class=` regressions in `ThemeRenderingTests` and `CardThemeTests` (`../tabler-test/src/crud_views_tabler/icons.py:12-47`, `../tabler-test/src/crud_views_tabler/tests.py:166-176,445-452`, `src/crud_views/lib/icons.py:51-53`):**
  Let's trace the exact execution path:
  1. In `src/crud_views/lib/icons.py:51-53`, `DEFAULT_ICONS` maps the three Phase 6 form-button icon keys to Font Awesome icons: `"save": "far:floppy-disk"`, `"cancel": "fas:xmark"`, and `"filter-reset": "fas:rotate-left"`.
  2. In `../tabler-test/src/crud_views_tabler/icons.py:12-47`, `TABLER_ICONS` maps only the 34 pre-Phase-6 keys (`"list"` through `"page-next"`) and does **not** contain `"save"`, `"cancel"`, or `"filter-reset"`. (This also causes `TablerIconTests.test_every_upstream_icon_name_is_mapped` at `tests.py:62-63` to fail on the baseline.)
  3. On the unmodified baseline (`885dfc7`), `default_label_mode("form")` is `"label"`, so the filter form (`crud_views_tabler/templates/crud_views/tags/list_filter.inner.html:11`, rendered on both `customer-list` and `customer-card`) renders its `Apply Filter` (`filter-submit`) and `Reset Filter` (`filter-reset`) buttons without icons. Thus `ThemeRenderingTests.test_list_uses_tabler_table_and_icons` (`tests.py:166-176`) and `CardThemeTests.test_cards_render_in_tabler_grid` (`tests.py:445-452`) **pass** on the baseline.
  4. As soon as `crud_views_tabler/apps.py` calls `register_label_mode_defaults({"form": "both"})` in `07-02`, the filter form's `Reset` button (`src/crud_views/lib/views/list.py:132`, `slot="form:filter-reset"`) resolves `cv_label_mode = "both"` and renders `{% cv_icon "filter-reset" %}`.
  5. Because `"filter-reset"` is unmapped in `TABLER_ICONS` (`../tabler-test/src/crud_views_tabler/icons.py:12-47`), `cv_icon` falls back to `DEFAULT_ICONS["filter-reset"] = "fas:rotate-left"`, emitting `<i class="fa-solid fa-rotate-left" aria-hidden="true"></i>` into `customer-list` and `customer-card`!
  6. That immediately breaks `self.assertNotIn("fa-solid", html)` and `self.assertNotIn("<i class=", html)` in **both** `ThemeRenderingTests.test_list_uses_tabler_table_and_icons` (`tests.py:174-175`) and `CardThemeTests.test_cards_render_in_tabler_grid` (`tests.py:451-452`)—introducing **2 new test regressions** against the baseline and rendering Font Awesome `<i>` tags on `customer-create`/`customer-update` (`save` and `cancel`) instead of Tabler SVGs!
- **[MEDIUM] Updating `TABLER_BUTTON_CLASSES` in `../tabler-test/src/crud_views_tabler/buttons.py` without updating `ButtonClassTests.test_table_values` in `../tabler-test/src/crud_views_tabler/tests.py:98-139` introduces a new test regression:**
  `06.6-07-PLAN.md` ("Artifacts this phase produces") states that the candidate patch modifies `src/crud_views_tabler/buttons.py` (class defaults, e.g., `form:actions` / `form:filter-actions`) and `src/crud_views_tabler/tests.py` (strict message parity). However, `ButtonClassTests.test_table_values` (`../tabler-test/src/crud_views_tabler/tests.py:98-139`) asserts `self.assertEqual(TABLER_BUTTON_CLASSES, expected)` against a hardcoded 39-entry dictionary. On the baseline, `test_table_values` passes; adding any key to `TABLER_BUTTON_CLASSES` in `buttons.py` without updating `expected` in `tests.py:98-139` will cause `ButtonClassTests.test_table_values` to fail as a new regression under `D-13`.

### 4. Suggestions
- Include `src/crud_views_tabler/icons.py` (and `src/django_tabler/icons.py` if any chosen Tabler icon name such as `device-floppy`, `x`, or `rotate` is not already in `django_tabler.icons.ICONS`) in the candidate adaptation patch in `07-02`/`07-03` (and `10-01`) to map `"save"`, `"cancel"`, and `"filter-reset"` to `tabler:` icons. This prevents the new `fa-solid` / `<i class=` regressions in `test_list_uses_tabler_table_and_icons` (`tests.py:174-175`) and `test_cards_render_in_tabler_grid` (`tests.py:451-452`), ensures Tabler form buttons actually render Tabler SVGs when `form="both"` is registered, and fixes `test_every_upstream_icon_name_is_mapped` (`tests.py:62-68`).
- Explicitly include updating `ButtonClassTests.test_table_values` (`../tabler-test/src/crud_views_tabler/tests.py:98-139`) in `07-02`/`07-03` alongside `MessagesParityTests` whenever `TABLER_BUTTON_CLASSES` in `buttons.py` is modified.

### 5. Risk Assessment
- **HIGH** — Without mapping `"save"`, `"cancel"`, and `"filter-reset"` in `crud_views_tabler/icons.py` and updating `ButtonClassTests.test_table_values` in `crud_views_tabler/tests.py:98-139`, registering `{"form": "both"}` in `apps.py` and adding action-group keys in `buttons.py` will deterministically break passing baseline tests (`test_list_uses_tabler_table_and_icons`, `test_cards_render_in_tabler_grid`, and `test_table_values`), violating `D-13` ("require no new regressions").

---

## 06.6-08

### 1. Summary
Plan `06.6-08` documents the new theme label-mode registration API (`register_label_mode_defaults`), page-owned form and `cv_form_helper` contracts, standalone `CrispyModelForm` wrapper migration (`C2-A02`), action-group class keys and opt-in recipe, and alert utility keys across `docs/reference/theme.md`, `docs/reference/action_menus.md`, `docs/reference/settings.md`, `docs/migrating-1.0.md`, and `CHANGELOG.md`, backed by executable documentation tests (`D-19`).

### 2. Strengths
- **Preserves existing documentation guard invariants (`tests/test1/test_alerts.py:249-259`, `tests/test1/test_label_mode_docs.py:190-229,777-816`):**
  - `test_alerts.py:249-255` (`_documented_alert_frame`) asserts that `### Custom alert frame` under `## Alerts` in `docs/reference/theme.md:308-321` contains **exactly one** `django`/`html` code fence. Task `08-01` explicitly preserves that single fence and places utility-key guidance outside it (`H08`).
  - `test_label_mode_docs.py:190-229` and `709-717` assert the exact numbered step count and markers in `docs/reference/action_menus.md` (`### Context label-mode resolution`, `### List label-mode resolution`, `### Card label-mode resolution`, `### Form label-mode resolution`). Task `08-01` preserves the numbered step structure by describing the three floor layers inside the existing `default_label_mode(...)` floor step.
- **Clean task split for `test_migration_e108_location_inventory` (`tests/test1/test_label_mode_docs.py:777-816`, `docs/migrating-1.0.md:61-64`):** `test_migration_e108_location_inventory` (`test_label_mode_docs.py:797`) asserts that `docs/migrating-1.0.md:64` contains `"otherwise it logs one warning and the location falls back to its package floor."` Leaving both `docs/migrating-1.0.md:64` and `test_migration_e108_location_inventory` untouched in `08-01` and updating them together in `08-02` (`H07`) keeps `test_label_mode_docs.py` passing after both tasks.
- **Addresses standalone `CrispyModelForm` wrapper removal (`C2-A02`):** `08-01` and `08-02` document and test the caller-owned `<form>` wrapper recipe for standalone `{% crispy form form.helper %}` renders of `CrispyModelForm` (where `form_tag=False` removes the helper's `<form>` while keeping its CSRF token).

### 3. Concerns
- **[LOW] `test_label_mode_docs.py:166-177` checks exact phrase substrings in `docs/reference/settings.md` (`### Label-mode configuration`):** `test_label_mode_configuration_table` (`tests/test1/test_label_mode_docs.py:166-177`) asserts exact substrings in the flattened `### Label-mode configuration` section (`"`CardListView.cv_get_card_actions_label_mode()`"`, `"`override_settings`"`, `"on every call"`, `"read-only"`, `"`crud_views.E108` (error)"`, `"raises `ValueError` in every mode"`, `"raises `ValueError` in strict mode"`, `"logs one warning"`, `"unknown key is ignored"`), plus line `519` asserts `'.default_label_mode(location)` returns the floor of `"context"`, `"list"`, `"card"` or `"form"' in flat`. When `08-01` updates `### Label-mode configuration` in `docs/reference/settings.md` to describe `register_label_mode_defaults`, it must retain those exact phrase substrings so `test_label_mode_configuration_table` and `test_label_mode_defaults_document_every_location` continue to pass.

### 4. Suggestions
- When editing `docs/reference/settings.md` in `08-01`, keep the existing sentences checked by `test_label_mode_docs.py:166-177,519` intact and add the `register_label_mode_defaults` layer explanation alongside them.

### 5. Risk Assessment
- **LOW** — All fragile doc-test regexes and section extractors in `test_label_mode_docs.py` and `test_alerts.py` have been accounted for.

---

## 06.6-09

### 1. Summary
Plan `06.6-09` (Wave 5) runs the final cross-version and crispy-floor regression gates, updates `noxfile.py`'s `CRISPY_FLOOR_TESTS` list, validates complete baseline/replay/delivered-source provenance via `theme_adoption_sources.py --check-final`, and publishes the Phase 7 public-surface handoff (`06.6-PUBLIC-SURFACE.md`, `06.6-ACCEPTANCE.md`, `06.6-VALIDATION.md`).

### 2. Strengths
- **Permanent `noxfile.py` floor coverage (`noxfile.py:28-52`):** `CRISPY_FLOOR_TESTS` (`noxfile.py:28-52`) currently omits `tests/test1/test_alerts.py` and `tests/test1/test_button_classes.py` as well as the five new `tests/test1/test_theme_*.py` modules. Appending all seven modules in `09-01` and verifying them via AST in `test_floor_selection_covers_theme_modules` ensures future `nox -s crispy_floor` runs permanently guard Phase 06.6 contracts.
- **Executes both cached floor environments (`noxfile.py:97`, `C2-A03`) and the `examples/bootstrap5` suite (`noxfile.py:110-120`, `A07`):** `09-01` runs full pytest on `.nox/tests-3-12-django-4-2`, `.nox/tests-3-12-django-5-2`, `.nox/crispy_floor-3-12-django-4-2`, and `.nox/crispy_floor-3-12-django-6-0`, plus `examples/bootstrap5`, Vitest unit/integration, browser preservation (`modal-focus.cjs`, `conditional-formsets.cjs`), `mkdocs build --strict`, and `ruff`.
- **Verifies delivered companion state after Plan `10` (`10-companion-delivery.json`):** Running `06.6-09` in Wave 5 after `06.6-10` ensures `--check-final` binds final acceptance to the actual delivered and committed companion tree as well as the preserved user `example/config/settings.py` digest.

### 3. Concerns
- **[LOW] Sequential port sharing between `modal-focus.cjs`, `conditional-formsets.cjs`, and `theme-adoption.cjs` (`09-01`):** `09-01` runs multiple browser harnesses. Provided they are executed sequentially as written in the `<verification>` list of `06.6-09-PLAN.md`, their default ports will not collide.

### 4. Suggestions
- Keep the browser verification commands in `09-01` strictly sequential so each harness releases its loopback port before the next starts.

### 5. Risk Assessment
- **LOW** — Comprehensive final verification and handoff gate with clear fail-closed criteria and truthful halted/pending-human states.

---

## 06.6-10

### 1. Summary
Plan `06.6-10` (Wave 4) materializes Plan `07`'s verified adaptation patch into the real `../tabler-test` companion repository under the amended `D-11`/`D-14` user authorization, verifies the delivered tree in isolation while preserving the user's dirty `example/config/settings.py` byte-for-byte, and creates scoped local commits in `../tabler-test` (`10-01`, `10-02`).

### 2. Strengths
- **Preserves user's dirty `example/config/settings.py` across delivery and commit (`10-01`, `10-02`):** `10-01` records the pre-delivery dirty digest of `example/config/settings.py`, applies only the verified patch hunks, validates the delivered tree using test-only settings in an isolated copy (never importing or exposing private settings), and `10-02` stages/commits only task-owned companion hunks before re-verifying with `--require-committed`.
- **Guards against pre-commit hook mutations (`10-02`):** `10-02` explicitly rechecks delivered file hashes and preserved dirty hashes after running `git commit` in `../tabler-test`, ensuring any companion commit hook modification cannot silently invalidate the replay evidence.

### 3. Concerns
- **[MEDIUM] `files_modified` in `06.6-10-PLAN.md` omits `../tabler-test/src/crud_views_tabler/icons.py` (and `../tabler-test/src/django_tabler/icons.py` if needed) (`../tabler-test/src/crud_views_tabler/icons.py:12-47`):**
  As traced in Plan `06.6-07` above, `../tabler-test/src/crud_views_tabler/icons.py:12-47` (`TABLER_ICONS`) currently lacks `"save"`, `"cancel"`, and `"filter-reset"`, which `src/crud_views/lib/icons.py:51-53` (`DEFAULT_ICONS`) maps to Font Awesome (`far:floppy-disk`, `fas:xmark`, `fas:rotate-left`). When `../tabler-test/src/crud_views_tabler/apps.py` registers `register_label_mode_defaults({"form": "both"})`, `crud_views_tabler/icons.py` must also map `"save"`, `"cancel"`, and `"filter-reset"` to `tabler:` icons (otherwise `ThemeRenderingTests.test_list_uses_tabler_table_and_icons` at `tests.py:174-175` and `CardThemeTests.test_cards_render_in_tabler_grid` at `tests.py:451-452` fail with new `fa-solid` / `<i class=` regressions). However, `10-01` states: *"Apply only actual patch hunks for the five named files... If the tested patch needs another path, update explicit task ownership before widening delivery."* Listing `../tabler-test/src/crud_views_tabler/icons.py` (and `../tabler-test/src/django_tabler/icons.py` if an SVG path is added) in `06.6-10-PLAN.md`'s `files_modified` and `10-01` `<files>` now avoids a task-ownership halt during Wave 4 execution.

### 4. Suggestions
- Add `../tabler-test/src/crud_views_tabler/icons.py` (and conditionally `../tabler-test/src/django_tabler/icons.py`) to `files_modified` and Task `10-01`'s `<files>` list in `06.6-10-PLAN.md` so the icon mappings required by `register_label_mode_defaults({"form": "both"})` are pre-authorized for delivery and local commit.

### 5. Risk Assessment
- **MEDIUM** — The delivery and local-commit verification mechanics are well-designed and safe for the user's dirty `settings.py`, provided `crud_views_tabler/icons.py` is included in the owned companion file list alongside `apps.py`, `buttons.py`, `tags/alert.html`, and `tests.py`.

---

## Cross-Plan Synthesis & Overall Assessment

All Cycle 4 concerns (`C4-A01` exhaustive recursive inventory negative controls, `C4-A02` single-hook assertion in `MessagesParityTests` preserving standalone `django_tabler` and CRUD alert adapter dismissal with strict rest-of-markup equality, and `C4-A04` floor template wording) and the user's `D-11`/`D-14` companion-modification authorization (Wave 4 Plan `06.6-10` + Wave 5 Plan `06.6-09`) are well-integrated across the 10 plans.

Two concrete companion-source interactions verified against the embedded `../tabler-test` files should be addressed before or during execution:
1. **`../tabler-test/src/crud_views_tabler/icons.py:12-47` (`06.6-07` & `06.6-10`, HIGH) and `../tabler-test/src/crud_views_tabler/tests.py:98-139` (`06.6-07` & `06.6-10`, MEDIUM):** Registering `{"form": "both"}` in `crud_views_tabler/apps.py` causes the `filter-reset` button on `customer-list` and `customer-card` to render its icon; because `"save"`, `"cancel"`, and `"filter-reset"` are absent from `TABLER_ICONS` (`icons.py:12-47`), `cv_icon` falls back to `DEFAULT_ICONS` (`src/crud_views/lib/icons.py:51-53`: `"fas:rotate-left"`), emitting `<i class="fa-solid fa-rotate-left">` and breaking `ThemeRenderingTests.test_list_uses_tabler_table_and_icons` (`tests.py:174-175`) and `CardThemeTests.test_cards_render_in_tabler_grid` (`tests.py:451-452`). Similarly, adding `form:actions` / `form:filter-actions` to `TABLER_BUTTON_CLASSES` (`buttons.py:3-44`) will break `ButtonClassTests.test_table_values` (`tests.py:98-139`) unless `expected` in `test_table_values` is updated. Include `src/crud_views_tabler/icons.py` and the `test_table_values` update in Plan `07`'s patch and Plan `10`'s `files_modified`.
2. **Companion `pytest-xdist` preflight (`06.6-06`, MEDIUM):** `../tabler-test/pyproject.toml:32` declares `test = ["pytest", "pytest-django", "crispy-bootstrap5==2026.9"]` without `pytest-xdist`. Allow `06-01`/`06-02` to run `tabler-test`'s small `pytest tests` suite without `-n 4` when `xdist` is absent from `CV_THEME_PYTHON` (while keeping `--parallel 4` on `example/manage.py test`), avoiding an unnecessary preflight halt.
