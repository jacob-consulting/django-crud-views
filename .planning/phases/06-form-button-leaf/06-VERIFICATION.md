---
phase: 06-form-button-leaf
verified: 2026-10-28T10:35:00Z
status: gaps_found
score: 34/35 must-haves verified
covered_files: [".planning/phases/06-form-button-leaf/06-01-PLAN.md", ".planning/phases/06-form-button-leaf/06-01-SUMMARY.md", ".planning/phases/06-form-button-leaf/06-02-PLAN.md", ".planning/phases/06-form-button-leaf/06-02-SUMMARY.md", ".planning/phases/06-form-button-leaf/06-03-PLAN.md", ".planning/phases/06-form-button-leaf/06-03-SUMMARY.md", ".planning/phases/06-form-button-leaf/06-04-PLAN.md", ".planning/phases/06-form-button-leaf/06-04-SUMMARY.md", ".planning/phases/06-form-button-leaf/06-05-PLAN.md", ".planning/phases/06-form-button-leaf/06-05-SUMMARY.md", ".planning/phases/06-form-button-leaf/06-06-PLAN.md", ".planning/phases/06-form-button-leaf/06-06-SUMMARY.md", ".planning/phases/06-form-button-leaf/06-07-PLAN.md", ".planning/phases/06-form-button-leaf/06-07-SUMMARY.md", ".planning/phases/06-form-button-leaf/06-08-PLAN.md", ".planning/phases/06-form-button-leaf/06-08-SUMMARY.md", ".planning/phases/06-form-button-leaf/06-09-PLAN.md", ".planning/phases/06-form-button-leaf/06-09-SUMMARY.md", "CHANGELOG.md", "docs/getting_started/tutorial-5-filters-permissions.md", "docs/migrating-1.0.md", "docs/reference/action_menus.md", "docs/reference/buttons.md", "docs/reference/icons.md", "docs/reference/javascript.md", "docs/reference/list_view.md", "docs/reference/settings.md", "docs/reference/theme.md", "examples/bootstrap5/project/settings.py", "noxfile.py", "src/crud_views/lib/button_classes.py", "src/crud_views/lib/crispy/buttons.py", "src/crud_views/lib/crispy/form.py", "src/crud_views/lib/formsets/layout.py", "src/crud_views/lib/icons.py", "src/crud_views/lib/settings.py", "src/crud_views/lib/view/action_menu.py", "src/crud_views/lib/view/base.py", "src/crud_views/lib/view/button_data.py", "src/crud_views/lib/view/buttons.py", "src/crud_views/lib/view/label_mode.py", "src/crud_views/lib/views/list.py", "src/crud_views/lib/viewset/__init__.py", "src/crud_views/static/crud_views/js/tooltip.js", "src/crud_views/templates/crud_views/tags/button/form.html", "src/crud_views/templatetags/crud_views.py", "src/crud_views/templatetags/crud_views_formsets.py", "src/crud_views_workflow/lib/forms.py", "tests/js/list.filter.test.js", "tests/js/modal.test.js", "tests/js/viewset.test.js", "tests/test1/golden/form_buttons/create.html", "tests/test1/golden/form_buttons/delete.html", "tests/test1/golden/form_buttons/filter.html", "tests/test1/golden/form_buttons/update.html", "tests/test1/golden/form_buttons/workflow.html", "tests/test1/test_action_label_mode_config.py", "tests/test1/test_button_classes.py", "tests/test1/test_button_classes_templates.py", "tests/test1/test_button_data.py", "tests/test1/test_crispy_buttons.py", "tests/test1/test_filter.py", "tests/test1/test_form_button_checks.py", "tests/test1/test_form_button_docs.py", "tests/test1/test_form_buttons_golden.py", "tests/test1/test_icon_host_leaves.py", "tests/test1/test_icons_registry.py", "tests/test1/test_label_mode.py", "tests/test1/test_label_mode_docs.py"]
covered_digest: "v4:sha256:a119f5af40596af3bdd28bd573bec23ced2fde26d3325ab0b4a9cbdd4ebeb79e"
behavior_unverified: 0
overrides_applied: 0
gaps:
  - truth: "D-16: submit/save, delete/delete, cancel/cancel, filter-submit/filter and filter-reset/filter-reset resolve independently of the submitted name for every package button on the layout path, and the icon-only missing-icon policy (strict ValueError / logged label fallback) fires only when an icon is genuinely unavailable"
    status: partial
    reason: "The icon= 'not given' sentinel is a bare object() compared by identity (crispy/buttons.py:26, :159). ListViewFilterFormHelper._cv_prepare_layout deep-copies every class-level or caller-assigned layout (views/list.py:153), and copy.deepcopy(object()) is a new object, so each copied Submit/Button/Reset constructed without icon= carries a fresh truthy non-sentinel object as its icon. Reproduced at HEAD 2e4e90a with a real {% crispy form helper %} render of a ListViewFilterFormHelper subclass declaring layout = Layout('name', FormActions(Submit('submit','Go',slot='form:filter-submit'), Reset('reset','Clear'))): form floor 'both' renders '<button ...> <span>Go</span></button>' with no icon; floor 'icon' non-strict logs \"form button 'filter-submit' renders icon-only but its icon <object object at ...> is not available; rendered with its label instead\" on every request; floor 'icon' strict raises ValueError (a 500; CRUD_VIEWS_STRICT defaults to DEBUG). The stock hook-built Apply/Reset and every package form button are unaffected (they are built after the copy). docs/reference/list_view.md documents class-level and assigned layouts as supported and copied, and the example project ships CRUD_VIEWS_LABEL_MODE_DEFAULTS={'form':'both'}, so a project following the docs hits the silent variant. The static W292 check reads _KIND_ICONS[kind] and reports nothing, so static and dynamic no longer agree (06-06 key link). Matches 06-REVIEW.md CR-01 (critical, disposition open); WR-01 (no test on this path) and WR-02 (normalizer admits a non-str cv_icon) are the same root cause."
    artifacts:
      - path: "src/crud_views/lib/crispy/buttons.py"
        issue: "_KIND_ICON = object() does not survive copy.deepcopy; _cv_button_context compares self._cv_icon is _KIND_ICON"
      - path: "src/crud_views/lib/view/button_data.py"
        issue: "_form_button_data keeps any truthy non-str cv_icon (icon = ctx.get('cv_icon') or None), so a Python object reaches _icon_available, the strict/log message and the leaf contract documented as str | None"
      - path: "src/crud_views/lib/views/list.py"
        issue: "_cv_prepare_layout deep-copies the layout and its adapters; no test renders a copied adapter under 'both' or 'icon'"
    missing:
      - "Make 'icon not given' copy-stable: store a bool (self._cv_kind_icon = icon is _KIND_ICON) or give the sentinel __copy__/__deepcopy__/__reduce__ returning itself"
      - "Normalize a non-str or blank cv_icon to None in _form_button_data before the icon-mode availability check, so cv_icon is always str | None and the strict/log message names None rather than a repr"
      - "Regression test: a ListViewFilterFormHelper subclass with a class-level layout holding package Submit/Reset (get_form_actions returning None), rendered through {% crispy form helper %} under CRUD_VIEWS_LABEL_MODE_DEFAULTS={'form':'both'} and {'form':'icon'} with CRUD_VIEWS_STRICT=True; assert fa-filter / fa-rotate-left present, no warning, no exception; plus cv_button_data on copy.deepcopy(Submit('submit','Go')) yields a str cv_icon"
      - "Update 06-REVIEW-DISPOSITION.md (CR-01, WR-01, WR-02) once fixed"
---

# Phase 6: Form-button leaf Verification Report

**Phase Goal:** Crispy form buttons render as real `<button>` elements through a crud_views leaf, share the action-button label-mode and class-table contract, and are safe against template injection. With no configuration, POST data is unchanged.
**Verified:** 2026-10-28T10:35:00Z
**Status:** gaps_found
**Re-verification:** No — initial verification

Every claim below was checked against the working tree at HEAD `2e4e90a` on branch `introduce-gsd`, not taken from the SUMMARY files. Named tests were run individually (never the full suite); the orchestrator's full-suite results (`pytest tests -n auto` 4445 passed, `vitest run` 223 passed) are recorded as context only.

## Goal Achievement

### Observable Truths

Roadmap Success Criteria (the contract) first, then the plan-level must-haves, deduplicated and merged by concern.

| #   | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| SC1 | With nothing configured, create/update/delete/cancel and both filter buttons render as `<button type="…">` with the same text, classes, `name`, `value`, `id`; `test_delete` posts `{"delete": "Delete"}` unchanged; `#filter-button-reset` preserved; before-change goldens show the diff | ✓ VERIFIED | Goldens read directly: `create/update/delete/workflow.html` hold `<button type="submit" name="submit|delete" value="Create|Delete|Process Workflow Step" id="submit-id-…" class="btn btn-primary">` and `<button type="button" name="reset" value="Cancel" id="button-id-reset" class="btn btn-secondary" data-cv-cancel-url=…>`; `filter.html` holds `id="filter-button"` / `id="filter-button-reset"` buttons then unchanged `<input type="hidden" name="sort|order|dir">`. Baselines `2956f3e`, `98b71ed`: `git diff B^ B -- src` empty, `src` tree `dcc38f4` equals `49f44cd:src`, both precede the first `src` change `df2308b` (checked with `merge-base --is-ancestor`). Ran `tests/test1/test_form_buttons_golden.py` (all) + `test_crud.py::test_delete_author`: pass |
| SC2 | `{"form": "both"}` shows icon + text on save/delete/cancel/both filter buttons; `{"form": "icon"}` shows icon-only with visually hidden label, `title`, `data-cv-tooltip="form"`; setting → ViewSet → view per-key maps and `form:<kind>:<mode>` keys apply | ✓ VERIFIED | `form.html` renders the three bodies with `{% cv_button_class 'form' cv_key cv_label_mode %}`, `title`/`data-cv-tooltip="form"` and `form:hidden-label` span. Ran `test_package_forms_render_their_semantic_icons`, `test_workflow_form_uses_the_workflow_icon`, `test_filter.py::test_filter_actions_honor_the_list_view_form_modes`, `test_icon_host_leaves.py::test_form_element_icon_mode/both_mode`, `test_form_maps_are_selected_whole`, `test_view_map_reaches_the_endpoint`, `test_settings_map_reaches_the_leaf_and_only_the_floor_is_live`: pass. My own render (repro script) of the stock filter helper under both/icon, strict on/off: icons present. The stock paths hold; the copied-layout path is Gap 1 (T18) |
| SC3 | A label or value containing `<b>`, `"><script>` or `{{ request.user }}` renders as escaped plain text in body and `value` | ✓ VERIFIED | `crispy/buttons.py` `render()` never calls `BaseInput.render`; `button_data._literal()` normalizes to plain `str`, extras serialized once via Django `flatatt`, leaf autoescapes `{{ cv_value }}`/`{{ cv_label }}`. Ran `test_hostile_literals_never_create_nodes_or_attributes` and `test_layout_values_stay_literal` (both contain `{{ request.user }}` cases) and `test_form_button_docs.py::test_custom_template_selection_and_scoped_context`: pass |
| SC4 | Workflow submit shows `workflow` icon; per-form `submit_icon` wins; icon-only form button with no icon → W292, raises in strict mode, else logs and renders label; E210/E211/W291 cover form maps | ✓ VERIFIED | `crud_views_workflow/lib/forms.py:22` `submit_icon = "workflow"`; `crispy/form.py:65,134` hook merge order. `base.py` `checks` yields `cv_form_label_mode_checks(cls)` and `cv_form_icon_mode_checks(cls)`; `action_menu.py:90-126` E211/E210/W291; `view/buttons.py:538` W292; `button_data.py:245-261` strict raise / log fallback. Ran `test_per_form_submit_icon_wins`, `test_strict_missing_icon_raises_naming_the_kind`, `test_non_strict_missing_icon_logs_and_uses_the_label`, `test_delete_form_inspects_delete_and_cancel_never_submit`, `test_mixed_map_reports_invalid_modes_then_unknown_kinds`: pass. Note: the policy also fires falsely on copied-layout buttons — Gap 1 |
| SC5 | CHANGELOG `### Breaking` entry and `docs/migrating-1.0.md` "Form buttons" section exist; example shows `both` for submit/delete/cancel; Tabler follow-up in the acceptance note | ✓ VERIFIED | `CHANGELOG.md` Unreleased `### Breaking` bullet "**Form buttons** render as `<button>` elements through the new leaf … (#257)"; `docs/migrating-1.0.md:219` `## Form buttons` with six subsections; `examples/bootstrap5/project/settings.py:131` `CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"form": "both"}`; `06-ACCEPTANCE.md §10` records the downstream glyph mapping (`device-floppy`, `x`, `filter-off`, selector and assertion updates) generically — the downstream theme is deliberately unnamed per 06-08's "keep downstream names out" decision. Ran `test_form_buttons_breaking_entry_pairs_with_migration`, `test_example_enables_form_both_only`: pass |
| T6 | D-17/D-18: spec authored only after Phase 1/2 contracts verified at the executing HEAD; baselines committed before every product edit | ✓ VERIFIED | `06-SPEC.md` has all nine required sections and a 40-char HEAD SHA (re-ran the 06-01 gate check); baseline history as in SC1 |
| T7 | D-01..D-12: the spec fixes template precedence, pack substitution, cv_* context, first-non-None ownership, legacy input placement, isolated layouts, exactly-once actions, None omission | ✓ VERIFIED | Sections "Form contract", "Template selection", "Ownership", "Helper lifecycle" present and non-empty; each is implemented and tested below (T12, T16, T20, T21) |
| T8 | D-13/D-14: a standalone package Submit renders a real button via `cv_button_data(ctx, "form")`; omitted/`"action"` third kind accepted, `menu-item`/unknown/semantic names raise `ValueError` in both strict modes, independent of `cv_key` | ✓ VERIFIED | `button_data.py:84-101`; `FORM_LEAF_KEYS`, `FORM_TYPES` defined; ran `test_button_data.py -k form` (146 pass) |
| T9 | `{% cv_button "form" %}` raises before resolution/normalization/leaf dispatch; context/list/card unchanged | ✓ VERIFIED | `templatetags/crud_views.py:206-209`; ran `test_cv_button_tag_rejects_form_location` (spies on dispatch): pass |
| T10 | Public `WorkflowForm`/formset-tag imports work after `settings.configure()` without `django.setup()`; view-package imports deferred to render time | ✓ VERIFIED | `crispy/buttons.py` imports `cv_button_data`, `CrudView`, `form_label_mode` inside `render()`/`_cv_form_label_mode()`; ran `test_workflow_lib_model_mixin_public_path_imports_without_app_registry`: pass |
| T11 | D-15: empty, Unicode, lazy, SafeString and template-looking values remain exact literal DOM text/values | ✓ VERIFIED | As SC3 |
| T12 | D-05..D-08: explicit template > subclass template > bundled; `%s` substitution; custom templates receive cv_* with no `input` alias | ✓ VERIFIED | `_TableClassMixin.template = FORM_LEAF_TEMPLATE`, `get_template_name(template_pack)`; `render_to_string(…, data)` with the normalized dict only. Ran `test_template_precedence`, `test_custom_template_gets_only_normalized_fields`: pass |
| T13 | D-14/D-17: repeated and interleaved renders preserve names/values/IDs/CSS without mutating adapters or contexts; reserved attributes once; multi-word names slugified | ✓ VERIFIED (behavior test) | Ran `test_interleaved_renders_of_one_shared_adapter_are_independent`, `test_interleaved_owners_do_not_leak`, `test_interleaved_icons_of_shared_adapters_do_not_leak`: pass |
| T14 | D-13: `form` in `LOCATIONS`/`LABEL_MODE_DEFAULTS` with floor `label`; `form:hidden-label`=`visually-hidden`, `form:icon-host` utility keys; exhaustive key count maintained | ✓ VERIFIED | `button_data.py:19` `LOCATIONS = {"context","list","card","form"}`; `button_classes.py:88,97`; ran `test_button_classes.py::test_documented_default_key_count_matches_table` and related: pass |
| T15 | D-13: form maps selected whole (view → ViewSet → setting); empty winning map suppresses lower maps; unmapped kind → lazy form floor; map follows the import-time singleton, only the floor is live | ✓ VERIFIED | `base.py:308-313` via `cv_first_inline_keys` → `crud_views_settings.form_actions_label_mode`; `settings.py:73` `from_settings(…, default={})`; `viewset/__init__.py:90,117`. Tests as in SC2 |
| T16 | D-09..D-12: owner = first non-None of render form `cv_view` → current helper → page; ordinary/falsey owner stops lookup; helper `view=None` never hides the page; no fixed stack offsets; formset rows carry the page tier through flatten/inclusion; caller context unchanged after failing renders | ✓ VERIFIED (behavior test) | `crispy/buttons.py:41-89` (overlay classification by response metadata, identity checks). Ran `test_owner_priority`, `test_enclosing_helper_overlays_are_never_page_layers`, `test_transported_page_owner_is_authoritative_even_when_none`, `test_formset_render_failure_leaves_the_caller_context_unchanged`: pass |
| T17 | D-14: all five kinds support label/both/icon bodies; icon mode has hidden label, matching `title`, form tooltip marker; utility keys never widen `FORM_KINDS` | ✓ VERIFIED | `form.html`; ran `test_form_element_icon_mode`, `test_form_element_both_mode`: pass |
| T18 | D-16: kind icons resolve independently of the submitted name for every layout-path package button; workflow default and per-form overrides win; the missing-icon policy fires only for genuinely unavailable icons | ✗ FAILED (partial) | Holds for hook-built and directly rendered adapters (`test_kind_default_icons`, `test_kind_icon_follows_the_slot_not_the_name`, `test_explicit_none_or_empty_icon_suppresses_the_kind_default` pass). Does NOT hold for adapters inside a deep-copied filter layout: reproduced `copy.deepcopy(_KIND_ICON) is _KIND_ICON -> False`; copied `Submit("submit","Go")._cv_button_context()["cv_icon"]` is `<object object>`; real `{% crispy %}` render of a class-level `Layout(... FormActions(Submit(..., slot="form:filter-submit"), Reset(...)))` under `{"form":"both"}` emits `<button …> <span>Go</span></button>` (no icon), under `{"form":"icon"}` logs the missing-icon warning per request (non-strict) or raises `ValueError` (strict). See Gaps Summary |
| T19 | Empty/disabled host classes produce no inline duplicate; Unicode/lazy labels exact; repeated renders with changed registries/settings/languages do not mutate shared defaults or retain another form's `submit_icon` | ✓ VERIFIED (behavior test) | Ran `test_form_host_slot_none_or_empty_switches_the_icon_off`, `test_form_repeated_renders_follow_the_current_registry`, `test_form_instances_do_not_share_icons_or_language`: pass |
| T20 | D-01/D-02: custom `add_input` controls stay legacy inputs quietly; hidden sort/order/direction inputs keep their path and values; pack-owned hidden wrapper follows the action group | ✓ VERIFIED | `list.py:120-123` keeps `add_input(layout.Hidden(...))`; `filter.html` golden; ran `test_filter_legacy_add_input_controls_stay_quiet_inputs`, `test_filter_hidden_controls_unchanged`: pass |
| T21 | D-03/D-04: declared layouts cloned per helper instance; actions exactly once after fields; `get_form_actions` None omits / empty `FormActions` kept; empty `Layout()` replacement prepared in `get_attributes` before crispy's guard; `helper.form` identity kept; equal labels not deduplicated | ✓ VERIFIED (behavior test) | `list.py:135-178` (`__bool__`, `_cv_prepare_layout`, `get_attributes`, identity-keyed `render_layout`). Ran `test_filter_class_layout_is_cloned_per_instance_and_actions_appear_once`, `test_filter_empty_layout_replacement_dispatches_through_the_tag`, `test_filter_action_hook_none_empty_and_equal_labels`, `test_filter_helper_private_state_is_not_published`, `test_filter.py::test_filter_endpoint_repeated_requests_never_accumulate_actions`: pass |
| T22 | D-09/D-14/D-17: default Apply/Reset use the leaf, selected owner, finite kinds and stable IDs; custom helper constructors still receive only `(view, request)` | ✓ VERIFIED | `list.py:130-133` `Submit(..., css_id="filter-button", slot="form:filter-submit")`, `Reset(..., css_id="filter-button-reset")`; `render_layout` pushes `_CV_HELPER_OWNER`; `mixins.py:319` `self.formhelper_class(request=self.request, view=self)` unchanged |
| T23 | D-17: before/after filter golden evidence uses the identical raw extraction region and extractor committed in 06-01 | ✓ VERIFIED | `diff` of `_extract_filter_form_region` between `98b71ed` and HEAD: identical |
| T24 | D-16: form-only E211 (shape, stops traversal) / E210 (per invalid mode) / W291 (unknown kinds, own view only); settings map E106; ViewSet construction validator; context/list diagnostics unchanged | ✓ VERIFIED | `action_menu.py:90-126`; `settings.py:149-155`; `viewset/__init__.py:117`; ran `test_mixed_map_reports_invalid_modes_then_unknown_kinds`: pass |
| T25 | D-16: static W292 inspects delete/cancel for delete providers, submit/cancel for ordinary/workflow providers, filter defaults, concrete polymorphic maps; never instantiates forms/helpers or calls hooks/renderers | ✓ VERIFIED | `view/buttons.py:519-532` (`_static_filter_controls` only when `get_form_actions` is inherited), `:538+`; ran `test_delete_form_inspects_delete_and_cancel_never_submit`, `test_checks_never_instantiate_forms_or_helpers`, `test_filter_helper_with_default_actions_is_statically_known`: pass |
| T26 | D-15/D-16: dynamic missing-icon icon mode raises `ValueError` in strict mode, else logs and renders the literal label with label classes and no generated tooltip; empty label keeps the empty payload | ✓ VERIFIED | `button_data.py:244-261`; ran strict/non-strict tests (SC4): pass. False positive on copied adapters is Gap 1 |
| T27 | D-14/D-16: one side-effect-free availability predicate (registry, library, renderer, built-in font class) shared by static checks and the normalizer; a custom inline renderer runs exactly once per icon/both control; host icons never trigger inline probes; E354 preserved | ✓ VERIFIED | `icons.py:270` `_icon_available`; imported by `button_data.py:14` and `view/buttons.py`; ran `test_icon_availability_predicate`, `test_counting_inline_renderer_runs_once_per_icon_render`: pass |
| T28 | D-17: native and modal submission include only the clicked button's name/value; delete payload and CSRF preserved; no polyfilled constructors | ✓ VERIFIED | Ran `bash 06-js-verify.sh tests/js/modal.test.js` on node v24.21.0 / jsdom 30.1.2 / vitest 5.0.3 with lock sha256 `567bff55…`: 31 passed |
| T29 | D-14/D-17: nested icon/text clicks cancel exactly once; filter reset keeps `sort`/`order`/`dir` and its stable ID in all three bodies | ✓ VERIFIED | Ran `bash 06-js-verify.sh tests/js/viewset.test.js tests/js/list.filter.test.js`: 92 passed |
| T30 | Expanded form tests pass at crispy 2.0 / crispy-bootstrap5 2023.10 on Django 4.2 and 6.0 without changing declared floors; `format_html` never called without arguments | ✓ VERIFIED | `noxfile.py:24` `CRISPY_FLOOR = {"django-crispy-forms": "2.0", "crispy-bootstrap5": "2023.10"}`, `:97-102` session parametrized over 4.2/6.0 installing the pins in the same resolver call, `:75-91` AST audit of `format_html`; `pyproject.toml` floors unchanged. The session itself was not re-run here (it builds two virtualenvs); 06-09 records 1877 passed per environment at `e40b0de` |
| T31 | D-01..D-08: docs keep field-only helper examples, show `FormActions` opt-in and None omission, migrate templates to `cv_*` with pack substitution; both E108 rows and the migration Step-zero paragraph list exactly `LOCATIONS` | ✓ VERIFIED | Ran `test_form_button_docs.py` (8 recipes executed through real crispy with a hostile literal), `test_e108_rows_list_exactly_the_button_locations`, `test_migration_e108_location_inventory`: pass |
| T32 | D-15..D-17: paired Breaking/migration entries explain DOM, literal values, custom context; example uses `both`; downstream follow-up generic | ✓ VERIFIED | As SC5 |
| T33 | D-01..D-04: consumers that cleared `helper.inputs` have an executable migration to `get_form_actions` returning None | ✓ VERIFIED | `docs/reference/list_view.md` "#### Removing the filter buttons"; `test_form_button_docs.py` executes the recipe and the changed-behavior regression: pass |
| T34 | D-17: acceptance records baselines, suites, floors, browser flows and downstream follow-up; the FORM-01/FORM-02 unclassified assumptions remain visible | ✓ VERIFIED | `06-ACCEPTANCE.md` §3 history, §9 browser (CDP, headless Chromium), §10 downstream; "unclassified" appears 5 times; `06-VALIDATION.md` task/wave/threat rows filled |
| T35 | D-15/D-16: no unresolved high/critical form-render *security* finding is reported as passed | ✓ VERIFIED | `06-SECURITY.md` `threats_open: 0`, 18/18 closed with named tests; the escaping boundary verified in SC3. CR-01 is a correctness defect (icon loss / false strict error), not an injection path, so this truth stands — but the acceptance sign-off predates the code review and should be reopened with Gap 1 |

**Score:** 34/35 truths verified (0 present, behavior-unverified)

### Deferred Items

None. Phase 7 ("Theme-surface stability policy") covers documenting public theme names; nothing in its goal or success criteria addresses the copied-adapter icon loss, so Gap 1 is not deferred.

### Required Artifacts

`gsd_run query verify.artifacts` returned `all_passed: true` for all nine plans (exit 0 each). Level 3/4 checked by hand:

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `src/crud_views/templates/crud_views/tags/button/form.html` | Real `<button>` leaf, three bodies | ✓ VERIFIED | Rendered by `_TableClassMixin.render` via `FORM_LEAF_TEMPLATE`; reads only `FORM_LEAF_KEYS`; data flows from `cv_button_data(raw, "form")` |
| `src/crud_views/lib/view/button_data.py` | Separate finite form contract and literal normalization | ✓ VERIFIED | `FORM_LEAF_KEYS`, `FORM_TYPES`, `_form_button_data`, `_literal`; wired from the adapter and from checks |
| `src/crud_views/lib/crispy/buttons.py` | Adapter render through the leaf; owner-aware mode resolution | ⚠️ VERIFIED with defect | Wired and substantive; `_KIND_ICON` identity sentinel is not copy-stable (Gap 1) |
| `src/crud_views/lib/view/base.py` | Form whole-map resolver; check wiring | ✓ VERIFIED | `cv_get_form_actions_label_mode`, form branch of `cv_get_action_label_mode`, `checks` yields both form checks |
| `src/crud_views/lib/icons.py` | `save`, `cancel`, `filter-reset` in both registries; `_icon_available` | ✓ VERIFIED | Lines 51-53, 93-95, 270 |
| `src/crud_views/lib/button_classes.py` | `form:hidden-label`, `form:icon-host` | ✓ VERIFIED | Lines 88, 97; count guard test passes |
| `src/crud_views_workflow/lib/forms.py` | `submit_icon = "workflow"` | ✓ VERIFIED | Line 22 |
| `src/crud_views/lib/views/list.py` | Isolated filter layout lifecycle and `get_form_actions` hook | ⚠️ VERIFIED with defect | Substantive and wired; its deepcopy is the trigger for Gap 1 |
| `src/crud_views/lib/view/buttons.py` | Static form W292 | ✓ VERIFIED | `cv_form_icon_mode_checks`, wired from `CrudView.checks` |
| `tests/test1/test_form_button_checks.py` | Map and missing-icon diagnostics/render contract | ✓ VERIFIED | 273 tests, named ones run; no skips |
| `tests/test1/test_filter.py`, `tests/test1/test_form_buttons_golden.py`, `tests/test1/test_form_button_docs.py`, `tests/js/modal.test.js` | Regressions | ✓ VERIFIED | Run as named above |
| `noxfile.py` | `crispy_floor` session | ✓ VERIFIED | Pins and Django 4.2/6.0 parametrization present |
| `docs/migrating-1.0.md`, `examples/bootstrap5/project/settings.py` | Migration section; `both` example | ✓ VERIFIED | `## Form buttons`; `{"form": "both"}` |
| `.planning/…/06-SPEC.md`, `06-ACCEPTANCE.md`, `06-VALIDATION.md` | Design, acceptance, validation records | ✓ VERIFIED | Present and section-complete |

### Key Link Verification

`gsd_run query verify.key-links` reports "Target not referenced in source" for 15 of 17 links: it greps for the target *file path* in the source file, which Python imports and Django templates never contain. Each link was therefore verified by symbol:

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `crispy/buttons.py` | `view/button_data.py` | adapter render → form normalization | WIRED | `render()` imports and calls `cv_button_data(raw, "form")`; `BaseInput.render` never called |
| `view/button_data.py` | `tags/button/form.html` | normalized literal contract | WIRED | adapter passes the `FORM_LEAF_KEYS` dict to `render_to_string(FORM_LEAF_TEMPLATE)` |
| `crispy/buttons.py` | `view/base.py` | owner → public resolver seam | WIRED | `owner.cv_get_action_label_mode("form", kind)` (line 105) |
| `view/base.py` | `lib/settings.py` | `cv_first_inline_keys` selects one map | WIRED | `getattr(crud_views_settings, "form_actions_label_mode")` (line 281) |
| `crispy/form.py` | `crispy/buttons.py` | explicit icon kwargs precedence | WIRED | `Submit(**{"icon": self.submit_icon, **hook_kwargs})` |
| `tags/button/form.html` | `button_classes.py` | mode and utility class lookups | WIRED | `{% cv_button_class 'form' cv_key cv_label_mode %}` → `get_button_class` |
| `views/mixins.py` | `views/list.py` | `(view, request)` constructor preserved | WIRED | `self.formhelper_class(request=self.request, view=self)` |
| `views/list.py` | `crispy/buttons.py` | default `FormActions` reaches adapters | WIRED | imports `Submit`, `Reset`, `_CV_HELPER_OWNER` |
| `view/base.py` | `view/action_menu.py` | form checks use finite `FORM_KINDS` | WIRED | `yield from cv_form_label_mode_checks(cls)` |
| `view/buttons.py` | `view/button_data.py` | static W292 and dynamic fallback agree on modes/icons | PARTIAL | Both use `_icon_available` and `cv_get_action_label_mode("form", …)`, but the static side reads `_KIND_ICONS[kind]` while the dynamic side reads the (possibly deep-copied) adapter's `_cv_icon`; for a copied layout the check is silent and the render raises — Gap 1 |
| `js/modal.js` | `tests/js/modal.test.js` | native SubmitEvent/FormData | WIRED | suite loads `modal.js` through `helpers/load.js`; 31 pass on locked jsdom |
| `noxfile.py` | `test_crispy_buttons.py` | expanded suite at floors | WIRED | tool-verified |
| `docs/reference/action_menus.md` | `docs/reference/settings.md` | canonical resolution + merge table | WIRED | links to `settings.md#label-mode-configuration` (lines 61, 85) |
| `docs/reference/theme.md` | `tests/test1/test_form_button_docs.py` | documented recipes executed | WIRED | test reads `THEME_MD`/`LIST_VIEW_MD`, `exec`s the fenced recipes |
| `06-ACCEPTANCE.md` | `test_form_buttons_golden.py` | baseline/history evidence | WIRED | tool-verified |
| `06-VALIDATION.md` | `test_form_button_checks.py` | diagnostic evidence | PARTIAL | VALIDATION rows cite "W292", "repair shard" and plan 06-06 but never the file name; evidence is in ACCEPTANCE/06-06-SUMMARY instead. Informational |
| `test_form_buttons_golden.py` | `golden/form_buttons/create.html` | raw control bytes | WIRED | golden path built from a case id; baseline tests pass |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| `form.html` | `cv_type/cv_name/cv_value/cv_id/cv_label` | adapter `name`/`value`/`input_type`/`id` → `_form_button_data` literals | Yes | ✓ FLOWING |
| `form.html` | `cv_label_mode` | `_cv_form_owner(form, context)` → `cv_get_action_label_mode("form", kind)` → map/floor | Yes | ✓ FLOWING |
| `form.html` | `cv_icon` | `_KIND_ICONS[kind]` if sentinel else `icon=`; `submit_icon`/`delete_icon` hooks | Yes for hook-built/direct adapters; a Python `object` for deep-copied adapters | ⚠️ STATIC on the copied path (Gap 1) |
| `form.html` | `cv_cancel_url` | `data_cv_cancel_url` kwarg, cancel kind only | Yes | ✓ FLOWING |
| `filter.html` golden | hidden `sort/order/dir` | `request.GET` → `add_input(Hidden)` | Yes | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Sentinel survives deepcopy | `python repro_cr01.py` (scratchpad; uses `tests/test1/conftest.pytest_configure`) | `copy.deepcopy(_KIND_ICON) is _KIND_ICON -> False`; copied `Submit` hands `<object object>` to the normalizer; `cv_button_data(...)["cv_icon"]` type `object` | ✗ FAIL |
| Stock filter helper under both/icon, strict on/off | same script, `DefaultHookHelper` | icons present in all four combinations | ✓ PASS |
| Class-level filter layout with package buttons | same script, `ClassLayoutHelper` | both: no icon; icon non-strict: warning per button; icon strict: `ValueError: form button 'filter-submit' renders icon-only but its icon <object object at …> is not available …` | ✗ FAIL |
| Success-criteria named Python tests (22 node ids incl. the golden module) | `pytest -p no:randomly <ids>` | 185 passed | ✓ PASS |
| State/ownership/exactly-once named tests (21 node ids + `test_button_data -k form`) | `pytest -p no:randomly <ids>` | 146 passed | ✓ PASS |
| Docs/recipe/E108/key-count named tests | `pytest -p no:randomly <ids>` | 73 passed | ✓ PASS |
| Interleaved-render tests | `pytest … test_interleaved_*` | 3 passed | ✓ PASS |
| Locked JS gate, modal | `bash 06-js-verify.sh tests/js/modal.test.js` | runtime/lock asserted; 31 passed | ✓ PASS |
| Locked JS gate, cancel/reset | `bash 06-js-verify.sh tests/js/viewset.test.js tests/js/list.filter.test.js` | 92 passed | ✓ PASS |
| Baseline commits src-free and ancestral | `git diff B^ B -- src`, `git rev-parse B:src`, `merge-base --is-ancestor` | 0 lines; `dcc38f4` == `49f44cd:src`; `98b71ed` precedes `df2308b` | ✓ PASS |
| Filter extractor unchanged since baseline | `diff <(git show 98b71ed:…) <(…)` on `_extract_filter_form_region` | identical | ✓ PASS |
| Commits documented in SUMMARYs exist | `verify.commits` over 32 hashes | `all_valid: true` | ✓ PASS |
| `nox -s crispy_floor` | not run (builds two virtualenvs; > 10 s) | 06-09 recorded 1877 passed per environment at `e40b0de` | ? SKIP |

### Probe Execution

No `scripts/*/tests/probe-*.sh` exist and no plan or summary names a probe. The phase's own gate script `06-js-verify.sh` was run (table above).

| Probe | Command | Result | Status |
| ----- | ------- | ------ | ------ |
| none declared | — | — | N/A |

### Requirements Coverage

All 13 IDs declared in PLAN frontmatter; REQUIREMENTS.md maps exactly FORM-01..FORM-13 to Phase 6 — no orphaned requirements.

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| FORM-01 | 01, 09 | Golden of today's markup committed before any change | ✓ SATISFIED | SC1 baseline history |
| FORM-02 | 01, 02, 06, 09 | `"form"` location; `cv_button_data(ctx,"form")` provides `cv_type/cv_name/cv_value/cv_id/cv_cancel_url`; `cv_key` is the kind | ✓ SATISFIED | T8, T14; `FORM_LEAF_KEYS` |
| FORM-03 | 02, 04, 09 | Leaf renders three bodies with `cv_button_class "form" cv_key cv_label_mode` | ✓ SATISFIED | SC2, T17 |
| FORM-04 | 02, 04, 09 | `form:hidden-label` (`visually-hidden`) and `form:icon-host` | ✓ SATISFIED | T14, T19 |
| FORM-05 | 01, 02, 05, 07, 08, 09 | Submit/Button/Reset keep signature, render through leaf; `css_class` appended; extra kwargs as attributes | ✓ SATISFIED | T8, T12, T13; crispy floor session (T30) |
| FORM-06 | 01, 02, 05, 07, 09 | No config → `<button type>` with same text/classes/name/value/id; POST unchanged | ✓ SATISFIED | SC1, T28 |
| FORM-07 | 02, 07, 09 | Values/labels autoescaped plain text, never evaluated; `<b>` escaped in text and `value` | ✓ SATISFIED | SC3, T11 |
| FORM-08 | 01, 05, 07, 08, 09 | Filter Apply/Reset move into layout `FormActions`; `#filter-button-reset` preserved; hidden inputs unchanged | ✓ SATISFIED | T20, T21, T22, T29 |
| FORM-09 | 04, 08, 09 | `save`/`cancel`/`filter-reset` icons; kind mapping; workflow uses `workflow`; per-form `submit_icon` wins | ⚠️ SATISFIED with defect | Registries and hook precedence verified (SC4); kind mapping is lost on deep-copied layout adapters (Gap 1) |
| FORM-10 | 03, 04, 05, 06, 08, 09 | `{"form":"both"}` icon+text on all five; `{"form":"icon"}` hidden label + `title` + `data-cv-tooltip="form"` | ⚠️ SATISFIED with defect | Stock controls verified (SC2); custom-layout package buttons lose icons / raise (Gap 1) |
| FORM-11 | 01, 03, 06, 08, 09 | Setting → ViewSet → view per-key maps resolve like context/list maps | ✓ SATISFIED | T15 |
| FORM-12 | 06, 08, 09 | E210/E211/W291 form maps; W292 icon-only without icon; strict raises else logs and renders label | ✓ SATISFIED | T24-T26 (false positive on copied adapters tracked under Gap 1) |
| FORM-13 | 08, 09 | CHANGELOG Breaking + migrating-1.0.md "Form buttons"; example `both`; downstream follow-up in acceptance note | ✓ SATISFIED | SC5 |

### Decision Coverage

`check.decision-coverage-verify`: All trackable CONTEXT.md decisions are honored by shipped artifacts (honored 18 / total 18, not_honored: []). Non-blocking.

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
| --------- | ---------- | ------ | ------- | -------- | --------------- | ------- |
| `test_form_buttons_golden.py` | FORM-01/06/08 | 19+ | 0 | PARTIAL (goldens captured from the pre-change system — a legitimate before/after oracle; parsed attributes are compared against the *baseline* commit, not the new output) | Value | OK |
| `test_crispy_buttons.py` | FORM-02/05/07/09/10 | all | 0 | no | Behavioral (parsed DOM, spies, interleaving) | OK |
| `test_form_button_checks.py` | FORM-12 | 273 | 0 | no | Value/Behavioral (exact IDs, messages, call counts) | OK |
| `test_filter.py`, `test_icon_host_leaves.py`, `test_form_button_docs.py`, `test_label_mode_docs.py`, `test_button_data.py` | FORM-03/04/08/10/11/13 | all | 0 | no | Value/Behavioral | OK |
| `tests/js/*.test.js` | FORM-06/07/08 | all | 0 | no | Behavioral (native FormData) | OK |

**Disabled tests on requirements:** 0. **Circular patterns detected:** 0 (golden provenance is the intended before-change oracle). **Insufficient assertions:** 0. **Coverage hole:** no test renders a deep-copied adapter under `both`/`icon` (06-REVIEW WR-01) — the hole through which Gap 1 passed 4445 green tests.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| `src/crud_views/lib/crispy/buttons.py` | 26, 159 | identity-compared `object()` sentinel stored on an instance that is deep-copied by `views/list.py:153` | 🛑 Blocker | Gap 1 — reproduced runtime defect (icon loss; false strict `ValueError`) |
| `src/crud_views/lib/view/button_data.py` | 244 | `ctx.get("cv_icon") or None` admits any truthy non-`str` into a `str | None` contract | ⚠️ Warning | Same root cause; message prints a Python repr |
| `src/crud_views/lib/views/list.py` | 153 | per-request `copy.deepcopy` of arbitrary user layouts; docs do not state the deep-copyable requirement (06-REVIEW IN-01) | ℹ️ Info | New failure surface for non-copyable layout members |
| `src/crud_views/lib/view/button_data.py` | 276 | Django `flatatt` sorts extra attributes; crispy preserved kwarg order; migration note does not mention it (06-REVIEW IN-02) | ℹ️ Info | Byte-level change for custom-button goldens |
| `src/crud_views_workflow/lib/forms.py` | 27-33 | `LABEL-PLACEHOLDER` / `HELP-PLACEHOLDER` field labels | ℹ️ Info | Pre-existing (predates Phase 06 per `git log -S`); runtime-replaced labels, not a Phase 06 stub |

No `TBD`/`FIXME`/`XXX` markers in any phase-modified file. No skipped tests. Working tree clean for `src`, `tests`, `docs`, `examples`.

### Human Verification Required

The phase is user-facing (buttons, tooltips, keyboard, modal). `06-ACCEPTANCE.md §9` already observed accessible names, keyboard focus, focus tooltips, cancel, filter apply/reset and modal delete via headless Chromium; the following remain human-only. Items 1-3 are harvested from `06-ACCEPTANCE.md §9` and the `<human-check>` in `06-09-PLAN.md` task 2; they stay recorded here so they survive the gap-closure round and reach UAT on re-verification.

### 1. Hover tooltips on form buttons in icon mode

**Test:** Run `examples/bootstrap5` with `CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"form": "icon"}`; hover the save, cancel, delete and both filter buttons with a pointer.
**Expected:** A tooltip with the button's label appears on hover (focus tooltips were already observed; pointer hover did not register in the headless harness).
**Why human:** Synthetic `mouseMoved` did not set `:hover`; needs a real pointer.

### 2. Visual quality of the three modes

**Test:** View create, delete and list-filter pages under `label`, `both` and `icon`.
**Expected:** Icon/text spacing and alignment look right, hidden labels do not clip, the both-mode icon gap matches the context toolbar buttons, and the non-strict label fallback does not look out of place next to icon-only siblings.
**Why human:** Appearance judgment; the UI review (20/24) flagged advisory fixes only.

### 3. Screen-reader announcement

**Test:** With a screen reader, tab through the create form and filter panel in `icon` mode and activate a button.
**Expected:** Each button is announced by its label (from the visually hidden span), the modal delete flow is announced, and reset announces the field reset.
**Why human:** Only the AX tree was inspected; no assistive technology ran.

### 4. Migration-guide readability

**Test:** Read `docs/migrating-1.0.md` "Form buttons" as a downstream maintainer with a custom `Submit` template and a filter helper that cleared `helper.inputs`.
**Expected:** The reader can migrate without guessing (selectors, literal values, `cv_*` context, `get_form_actions` None recipe, sorted extra-attribute order — note IN-02 says the last is currently missing).
**Why human:** Prose judgment.

### Gaps Summary

One gap, with one root cause, blocks the phase goal's "share the action-button label-mode … contract" clause for a documented configuration.

**Gap 1 — kind icons do not survive the filter helper's layout copy (06-REVIEW CR-01, open).** `crud_views.lib.crispy.buttons._KIND_ICON` is a bare `object()` and `_cv_button_context` tests `self._cv_icon is _KIND_ICON`. `ListViewFilterFormHelper._cv_prepare_layout` deep-copies any class-level or caller-assigned layout on every helper construction, and `copy.deepcopy(object())` returns a new object. Every copied `Submit`/`Button`/`Reset` created without `icon=` therefore carries a truthy non-sentinel object. I reproduced it through a real `{% crispy form helper %}` render at HEAD: under the example project's `{"form": "both"}` the button renders with no icon (silently); under `{"form": "icon"}` non-strict, a warning is logged on every request; under `{"form": "icon"}` with `CRUD_VIEWS_STRICT` (default `DEBUG`), the render raises `ValueError` — a 500 that the static `W292` check does not predict, because it reads `_KIND_ICONS[kind]` rather than the copied instance. The stock hook-built Apply/Reset and all package forms are unaffected, which is why 4445 tests pass. `docs/reference/list_view.md` explicitly documents class-level and assigned layouts as supported and copied, so this is a defect on a documented path, not an edge case. The fix is small (a copy-stable sentinel or a boolean flag, plus normalizing non-`str` `cv_icon` to `None`) and needs the regression test listed in the frontmatter `gaps.missing`. `06-ACCEPTANCE.md` and `06-SECURITY.md` were signed off before the code review found this; the acceptance should be amended once closed.

Everything else the phase promised is present, wired, data-flowing and behaviorally tested: real `<button>` elements with byte-equal attributes against committed before-change baselines, a single escaping boundary that keeps `{{ request.user }}` and `"><script>` literal, owner-first whole-map label-mode resolution, the three accessible bodies with utility classes, the filter helper's isolated layout lifecycle and `get_form_actions` hook, the form-only E210/E211/W291 and W292 diagnostics, native submitter payloads on the locked jsdom, the crispy 2.0 floor session, and the paired Breaking/migration documentation with the `both` example.

---

_Verified: 2026-10-28T10:35:00Z_
_Verifier: Claude (gsd-verifier)_
