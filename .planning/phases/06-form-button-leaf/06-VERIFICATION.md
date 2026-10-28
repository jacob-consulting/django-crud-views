---
phase: 06-form-button-leaf
verified: 2026-10-28T10:51:09Z
status: human_needed
score: 42/42 must-haves verified
covered_files: [".planning/phases/06-form-button-leaf/06-01-PLAN.md", ".planning/phases/06-form-button-leaf/06-01-SUMMARY.md", ".planning/phases/06-form-button-leaf/06-02-PLAN.md", ".planning/phases/06-form-button-leaf/06-02-SUMMARY.md", ".planning/phases/06-form-button-leaf/06-03-PLAN.md", ".planning/phases/06-form-button-leaf/06-03-SUMMARY.md", ".planning/phases/06-form-button-leaf/06-04-PLAN.md", ".planning/phases/06-form-button-leaf/06-04-SUMMARY.md", ".planning/phases/06-form-button-leaf/06-05-PLAN.md", ".planning/phases/06-form-button-leaf/06-05-SUMMARY.md", ".planning/phases/06-form-button-leaf/06-06-PLAN.md", ".planning/phases/06-form-button-leaf/06-06-SUMMARY.md", ".planning/phases/06-form-button-leaf/06-07-PLAN.md", ".planning/phases/06-form-button-leaf/06-07-SUMMARY.md", ".planning/phases/06-form-button-leaf/06-08-PLAN.md", ".planning/phases/06-form-button-leaf/06-08-SUMMARY.md", ".planning/phases/06-form-button-leaf/06-09-PLAN.md", ".planning/phases/06-form-button-leaf/06-09-SUMMARY.md", ".planning/phases/06-form-button-leaf/06-10-PLAN.md", ".planning/phases/06-form-button-leaf/06-10-SUMMARY.md", "CHANGELOG.md", "docs/getting_started/tutorial-5-filters-permissions.md", "docs/migrating-1.0.md", "docs/reference/action_menus.md", "docs/reference/buttons.md", "docs/reference/icons.md", "docs/reference/javascript.md", "docs/reference/list_view.md", "docs/reference/settings.md", "docs/reference/theme.md", "examples/bootstrap5/project/settings.py", "noxfile.py", "src/crud_views/lib/button_classes.py", "src/crud_views/lib/crispy/buttons.py", "src/crud_views/lib/crispy/form.py", "src/crud_views/lib/formsets/layout.py", "src/crud_views/lib/icons.py", "src/crud_views/lib/settings.py", "src/crud_views/lib/view/action_menu.py", "src/crud_views/lib/view/base.py", "src/crud_views/lib/view/button_data.py", "src/crud_views/lib/view/buttons.py", "src/crud_views/lib/view/label_mode.py", "src/crud_views/lib/views/list.py", "src/crud_views/lib/viewset/__init__.py", "src/crud_views/static/crud_views/js/tooltip.js", "src/crud_views/templates/crud_views/tags/button/form.html", "src/crud_views/templatetags/crud_views.py", "src/crud_views/templatetags/crud_views_formsets.py", "src/crud_views_workflow/lib/forms.py", "tests/js/list.filter.test.js", "tests/js/modal.test.js", "tests/js/viewset.test.js", "tests/test1/golden/form_buttons/create.html", "tests/test1/golden/form_buttons/delete.html", "tests/test1/golden/form_buttons/filter.html", "tests/test1/golden/form_buttons/update.html", "tests/test1/golden/form_buttons/workflow.html", "tests/test1/test_action_label_mode_config.py", "tests/test1/test_button_classes.py", "tests/test1/test_button_classes_templates.py", "tests/test1/test_button_data.py", "tests/test1/test_crispy_buttons.py", "tests/test1/test_filter.py", "tests/test1/test_form_button_checks.py", "tests/test1/test_form_button_docs.py", "tests/test1/test_form_buttons_golden.py", "tests/test1/test_icon_host_leaves.py", "tests/test1/test_icons_registry.py", "tests/test1/test_label_mode.py", "tests/test1/test_label_mode_docs.py"]
covered_digest: "v4:sha256:26313c28f94879d1e31d09f16f76d66fb2ce69c973e30540d1ef1a94da9ec052"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 34/35
  previous_verified: 2026-10-28T10:35:00Z
  gaps_closed:
    - "D-16: submit/save, delete/delete, cancel/cancel, filter-submit/filter and filter-reset/filter-reset resolve independently of the submitted name for every package button on the layout path, and the icon-only missing-icon policy (strict ValueError / logged label fallback) fires only when an icon is genuinely unavailable"
  gaps_remaining: []
  regressions: []
human_verification:
  - test: "Run examples/bootstrap5 with CRUD_VIEWS_LABEL_MODE_DEFAULTS = {\"form\": \"icon\"}; hover the save, cancel, delete and both filter buttons with a pointer"
    expected: "A tooltip with the button's label appears on hover (focus tooltips were already observed in headless Chromium; pointer hover did not register there)"
    why_human: "Synthetic mouseMoved did not set :hover in the headless harness; needs a real pointer"
  - test: "View the create, delete and list-filter pages under label, both and icon form modes, including a custom filter layout holding package Submit/Reset (the 06-10 path)"
    expected: "Icon/text spacing and alignment look right, hidden labels do not clip, the both-mode icon gap matches the context toolbar buttons, and the non-strict label fallback does not look out of place next to icon-only siblings"
    why_human: "Appearance judgment; the UI review (20/24) flagged advisory fixes only"
  - test: "With a screen reader, tab through the create form and the filter panel in icon mode and activate a button"
    expected: "Each button is announced by its label (from the visually hidden span), the modal delete flow is announced, and reset announces the field reset"
    why_human: "Only the AX tree was inspected programmatically; no assistive technology ran"
  - test: "Read docs/migrating-1.0.md 'Form buttons' as a downstream maintainer with a custom Submit template and a filter helper that cleared helper.inputs"
    expected: "The reader can migrate without guessing (selectors, literal values, cv_* context, get_form_actions None recipe); note that IN-02 (sorted extra-attribute order) is still not mentioned"
    why_human: "Prose judgment"
---

# Phase 6: Form-button leaf Verification Report

**Phase Goal:** Crispy form buttons render as real `<button>` elements through a crud_views leaf, share the action-button label-mode and class-table contract, and are safe against template injection. With no configuration, POST data is unchanged.
**Verified:** 2026-10-28T10:51:09Z
**Status:** human_needed
**Re-verification:** Yes — after gap closure (plan 06-10, commits `ae83e62`..`3c9d847`; re-review `1e0b38f`)

Checked against the working tree at HEAD `1e0b38f` on branch `introduce-gsd` (working tree clean for `src`, `tests`, `docs`, `examples`). The previous report (`verified: 2026-10-28T10:35:00Z`, HEAD `2e4e90a`) had one `gaps:` item, so this pass ran in re-verification mode: full three-level verification of the failed truth (T18) and of every 06-10 must-have, and a named-test regression sweep of the 34 previously verified truths. Nothing was taken from the 06-10 SUMMARY or the re-review; every claim below was re-derived from code, from named tests run here one selection at a time (never the full suite), or from an independent render script outside pytest. The orchestrator's full-suite result (`pytest tests -n auto` 4631 passed) is context only.

## Goal Achievement

### Observable Truths

Roadmap Success Criteria first, then the plan-level truths carried over verbatim from the previous report (T6..T35), then the seven truths added by the 06-10 gap-closure plan (G1..G7). "regression" = quick regression check (named test re-run + symbol presence); "full" = three-level verification this pass.

| #   | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| SC1 | With nothing configured, create/update/delete/cancel and both filter buttons render as `<button type="…">` with the same text, classes, `name`, `value`, `id`; `test_delete` posts `{"delete": "Delete"}` unchanged; `#filter-button-reset` preserved; before-change goldens show the diff | ✓ VERIFIED (regression) | Goldens last touched at `db8f33a` (06-05); `git diff --stat ae83e62^..HEAD -- src tests` lists only the four 06-10 files, so no golden, template or payload path moved during gap closure. Ran `test_form_buttons_golden.py` (all) + `test_crud.py::test_delete_author`: pass (in the 306-pass sweep) |
| SC2 | `{"form": "both"}` shows icon + text on save/delete/cancel/both filter buttons; `{"form": "icon"}` shows icon-only with visually hidden label, `title`, `data-cv-tooltip="form"`; setting → ViewSet → view per-key maps and `form:<kind>:<mode>` keys apply | ✓ VERIFIED (full) | Previously held only for stock/hook-built controls. Now also holds on the copied-layout path: independent script renders `{% crispy form helper %}` for a `ListViewFilterFormHelper` subclass with class-level `Layout("name", FormActions(Submit(..., slot="form:filter-submit"), Reset(...)))` and `get_form_actions() -> None` under both/icon x strict/lenient: `fa-solid fa-filter` / `fa-solid fa-rotate-left` present, icon mode carries `title` = label and `data-cv-tooltip="form"`, no warning, no exception. Stock helper identical. Named tests `test_filter_actions_honor_the_list_view_form_modes`, `test_form_element_icon_mode/both_mode`, `test_form_maps_are_selected_whole`, `test_view_map_reaches_the_endpoint`, `test_settings_map_reaches_the_leaf_and_only_the_floor_is_live`, `test_package_forms_render_their_semantic_icons`: pass |
| SC3 | A label or value containing `<b>`, `"><script>` or `{{ request.user }}` renders as escaped plain text in body and `value` | ✓ VERIFIED (regression) | Escaping boundary untouched by 06-10 (`render()` still never calls `BaseInput.render`; `_literal()` unchanged). Ran `test_hostile_literals_never_create_nodes_or_attributes`, `test_layout_values_stay_literal`, `test_form_button_docs.py` (hostile-literal recipes): pass |
| SC4 | Workflow submit shows `workflow` icon; per-form `submit_icon` wins; icon-only form button with no icon → W292, raises in strict mode, else logs and renders label; E210/E211/W291 cover form maps | ✓ VERIFIED (full) | `crud_views_workflow/lib/forms.py:22` `submit_icon = "workflow"`; `button_data.py:246-261` strict raise / log fallback now reached only with a genuinely missing icon (`None` or an unavailable nonblank string). The previous false positive on copied adapters is gone (SC2 evidence, T18). Ran `test_form_button_checks.py` (273, all) incl. `test_strict_missing_icon_raises_naming_the_kind`, `test_non_strict_missing_icon_logs_and_uses_the_label`, `test_delete_form_inspects_delete_and_cancel_never_submit`, `test_mixed_map_reports_invalid_modes_then_unknown_kinds`, `test_per_form_submit_icon_wins`: pass |
| SC5 | CHANGELOG `### Breaking` entry and `docs/migrating-1.0.md` "Form buttons" section exist; example shows `both`; Tabler follow-up in the acceptance note | ✓ VERIFIED (regression) | None of `CHANGELOG.md`, `docs/`, `examples/` changed since the previous pass (git log since `2026-10-28T10:35:00Z` lists only `.planning/` files). `06-ACCEPTANCE.md §10` still present; §12 added. Ran `test_form_button_docs.py` incl. the Breaking/migration pairing test: pass |
| T6 | D-17/D-18: spec authored after Phase 1/2 contracts verified at the executing HEAD; baselines committed before every product edit | ✓ VERIFIED (regression) | Unchanged history; 06-10 added no new baseline requirement (defect fix, no contract change, no new Breaking entry needed) |
| T7 | D-01..D-12 settled in the spec and implemented | ✓ VERIFIED (regression) | As before; T12/T16/T20/T21 re-run below |
| T8 | D-13/D-14: standalone package Submit renders via `cv_button_data(ctx, "form")`; third-kind validation | ✓ VERIFIED (regression) | Ran `test_button_data.py -k form` (all form cases, in the 444-pass sweep): pass |
| T9 | `{% cv_button "form" %}` raises before resolution | ✓ VERIFIED (regression) | Ran `test_cv_button_tag_rejects_form_location`: pass |
| T10 | Public form-module imports work before `django.setup()` | ✓ VERIFIED (regression) | `crispy/buttons.py` still imports `cv_button_data`, `CrudView`, `form_label_mode` inside `render()` / `_cv_form_label_mode()` (lines 102-104, 169); the 06-10 diff added no module-level import |
| T11 | D-15: empty, Unicode, lazy, SafeString and template-looking values remain literal | ✓ VERIFIED (regression) | As SC3 |
| T12 | D-05..D-08: template precedence, `%s` pack substitution, `cv_*`-only custom context | ✓ VERIFIED (regression) | Ran `test_template_precedence`, `test_custom_template_gets_only_normalized_fields`: pass |
| T13 | D-14/D-17: repeated and interleaved renders preserve names/values/IDs/CSS without mutating adapters | ✓ VERIFIED (behavior test) | Ran `test_interleaved_renders_of_one_shared_adapter_are_independent`, `test_interleaved_owners_do_not_leak`, `test_interleaved_icons_of_shared_adapters_do_not_leak`: pass |
| T14 | D-13: `form` in `LOCATIONS`/`LABEL_MODE_DEFAULTS`; `form:hidden-label`, `form:icon-host` keys | ✓ VERIFIED (regression) | Ran `test_button_classes.py::test_documented_default_key_count_matches_table`: pass |
| T15 | D-13: form maps selected whole; floor live, map import-time | ✓ VERIFIED (regression) | Tests as SC2 |
| T16 | D-09..D-12: owner = first non-None of render form `cv_view` → helper → page; no fixed stack offsets | ✓ VERIFIED (behavior test) | Ran `test_owner_priority`, `test_enclosing_helper_overlays_are_never_page_layers`, `test_transported_page_owner_is_authoritative_even_when_none`, `test_formset_render_failure_leaves_the_caller_context_unchanged`: pass |
| T17 | D-14: all five kinds support the three bodies; icon mode has hidden label, `title`, form tooltip marker | ✓ VERIFIED (regression) | Ran `test_form_element_icon_mode`, `test_form_element_both_mode`: pass; independent script confirms `title`/`data-cv-tooltip="form"` on copied controls |
| T18 | D-16: kind icons resolve independently of the submitted name for every layout-path package button; workflow default and per-form overrides win; the missing-icon policy fires only for genuinely unavailable icons | ✓ VERIFIED (full, behavior test) | **Gap closed.** `crispy/buttons.py:131-132` `self._cv_kind_icon = icon is _KIND_ICON; self._cv_icon = None if self._cv_kind_icon else icon` (sentinel compared in `__init__` only); `:163` `"cv_icon": _KIND_ICONS[kind] if self._cv_kind_icon else self._cv_icon`. A bool survives `copy.deepcopy`, so `list.py:153` no longer strips the omission. Repo-wide grep: no reader of `_cv_icon`/`_KIND_ICON` outside `crispy/buttons.py`. Independent script: `copy.copy`, `copy.deepcopy` and a `pickle` round-trip of `Submit("submit", "Go")` all yield `cv_icon == "save"` (`str`); misnamed `Submit("delete", ..., slot="form:filter-submit")` → `"filter"`; explicit `None`/`""`/`"workflow"` survive copying unchanged. Ran `test_copied_filter_layout_keeps_kind_icons` (12: class / before-first-render / between-renders x both / icon x strict / lenient), `test_copied_adapter_keeps_icon_contract` (5), `test_copied_adapter_preserves_explicit_icon` (5): 22 passed. Prior tests `test_kind_default_icons`, `test_kind_icon_follows_the_slot_not_the_name`, `test_explicit_none_or_empty_icon_suppresses_the_kind_default`: pass |
| T19 | Empty/disabled host classes no inline duplicate; repeated renders follow current registry; no cross-form `submit_icon` leak | ✓ VERIFIED (behavior test) | Ran `test_form_host_slot_none_or_empty_switches_the_icon_off`, `test_form_repeated_renders_follow_the_current_registry`, `test_form_instances_do_not_share_icons_or_language`: pass |
| T20 | D-01/D-02: custom `add_input` controls stay legacy inputs; hidden sort/order/direction inputs unchanged | ✓ VERIFIED (regression) | `list.py:120-123` unchanged; ran `test_filter_legacy_add_input_controls_stay_quiet_inputs`, `test_filter_hidden_controls_unchanged`: pass; `test_copied_filter_layout_keeps_kind_icons` asserts `HIDDEN_SORT` after the copied actions on every round |
| T21 | D-03/D-04: declared layouts cloned per instance; actions exactly once; None omits / empty kept; `helper.form` identity kept | ✓ VERIFIED (behavior test) | `list.py:139-178` unchanged by 06-10 (deepcopy isolation kept, not bypassed). Ran `test_filter_class_layout_is_cloned_per_instance_and_actions_appear_once`, `test_filter_empty_layout_replacement_dispatches_through_the_tag`, `test_filter_action_hook_none_empty_and_equal_labels`, `test_filter_helper_private_state_is_not_published`, `test_filter_endpoint_repeated_requests_never_accumulate_actions`: pass |
| T22 | D-09/D-14/D-17: default Apply/Reset use the leaf with stable IDs; custom helper constructors receive `(view, request)` | ✓ VERIFIED (regression) | `list.py:130-133` unchanged; stock helper render in the independent script shows `Apply Filter` / `Reset Filter` with kind icons |
| T23 | D-17: before/after filter golden evidence uses the identical extractor | ✓ VERIFIED (regression) | `test_form_buttons_golden.py` untouched since the previous pass |
| T24 | D-16: form-only E211/E210/W291; settings E106; ViewSet validator | ✓ VERIFIED (regression) | `action_menu.py`, `settings.py`, `viewset/__init__.py` unchanged; ran `test_mixed_map_reports_invalid_modes_then_unknown_kinds`: pass |
| T25 | D-16: static W292 inspects the right controls and never instantiates forms/helpers | ✓ VERIFIED (regression) | `view/buttons.py:491-532` unchanged; ran `test_delete_form_inspects_delete_and_cancel_never_submit`, `test_checks_never_instantiate_forms_or_helpers`, `test_filter_helper_with_default_actions_is_statically_known`: pass |
| T26 | D-15/D-16: dynamic missing-icon policy in icon mode (strict raise / log + label); empty label keeps empty payload | ✓ VERIFIED (full) | `button_data.py:246-261`. Now also deterministic for malformed input: strict message names `None`, never an object repr (independent script + `test_form_icon_normalization_strict_icon_mode_raises_naming_none`); lenient logs once per render (`..._lenient_icon_mode_logs_and_uses_the_label`); empty-label path kept (`..._lenient_without_a_label_keeps_the_empty_path`). The previous false positive on copied adapters is gone |
| T27 | D-14/D-16: one availability predicate shared by static checks and the normalizer; inline renderer runs once | ✓ VERIFIED (regression) | `_icon_available` still the single predicate (`button_data.py:14`, `view/buttons.py:549`); ran `test_icon_availability_predicate`, `test_counting_inline_renderer_runs_once_per_icon_render`: pass |
| T28 | D-17: native and modal submission include only the clicked button's name/value; CSRF preserved | ✓ VERIFIED (behavior test) | Ran `bash 06-js-verify.sh tests/js/modal.test.js tests/js/viewset.test.js tests/js/list.filter.test.js` (runtime/lock asserted): 3 files, 123 passed |
| T29 | D-14/D-17: nested icon/text clicks cancel once; filter reset keeps `sort`/`order`/`dir` and its stable ID | ✓ VERIFIED (behavior test) | Same JS run |
| T30 | Expanded form tests pass at crispy 2.0 / crispy-bootstrap5 2023.10 on Django 4.2 and 6.0 | ✓ VERIFIED (regression) | `noxfile.py` unchanged. The session was not re-run here (builds two virtualenvs; > 10 s). 06-10 records 2063 passed per environment at `61103dd` with the two changed test files inside `CRISPY_FLOOR_TESTS`; the four 06-10 code changes are pure-Python and crispy-version-independent |
| T31 | Docs keep field-only helper examples, show `FormActions` opt-in and None omission; E108 rows list `LOCATIONS` | ✓ VERIFIED (regression) | Docs unchanged since the previous pass; ran `test_form_button_docs.py` (all): pass |
| T32 | Paired Breaking/migration entries; example `both`; downstream follow-up generic | ✓ VERIFIED (regression) | As SC5 |
| T33 | Consumers that cleared `helper.inputs` have an executable migration | ✓ VERIFIED (regression) | Recipe test in `test_form_button_docs.py`: pass |
| T34 | Acceptance records baselines, suites, floors, browser flows and downstream follow-up; FORM-01/02 unclassified assumptions visible | ✓ VERIFIED (full) | `06-ACCEPTANCE.md`: §1-§10 kept as history, §11 status updated, §12 "Gap closure 06-10 (measured 2026-10-28, HEAD `61103dd`)" added; "Specless edge classifier: unresolved assumptions (kept visible)" section present. `06-VALIDATION.md`: task rows 06-10-1..3 and threats T-06-18..21 with named tests |
| T35 | No unresolved high/critical form-render security finding reported as passed | ✓ VERIFIED (regression) | `06-SECURITY.md` unchanged (18/18 closed); 06-10 threats T-06-18..21 recorded as mitigated with named tests; the escaping boundary (SC3) untouched |
| G1 | 06-10: package Submit/Reset inside class-level and caller-assigned filter layouts render `fa-filter`/`fa-rotate-left` through real crispy under both/icon with strict mode, without warnings or exceptions | ✓ VERIFIED (behavior test) | `test_copied_filter_layout_keeps_kind_icons` renders through `FILTER_CRISPY = Template("{% load crispy_forms_tags %}{% crispy form helper %}")` (`test_crispy_buttons.py:1398`, `:1425`) with `warnings.simplefilter("error")` and asserts no WARNING-level log record. Independent script reproduces the same four combinations outside pytest |
| G2 | 06-10: deep-copied Submit/Button/Reset retain slot-derived icons for all five kinds independently of submitted names; explicit None/empty and overrides stay distinct from omission | ✓ VERIFIED (behavior test) | `test_copied_adapter_keeps_icon_contract[cancel|delete|filter-reset|filter-submit|submit]` uses `MISLEADING_NAMES` and asserts `type(cv_icon) is str`; `test_copied_adapter_preserves_explicit_icon[none|empty|none-misnamed|workflow|prefixed-misnamed]` through `copy.copy` and `copy.deepcopy`. Independent script agrees (including a pickle round-trip, not covered by the tests) |
| G3 | 06-10 / FORM-02: the form normalizer emits `cv_icon` as a nonblank `str` or `None`; non-string and whitespace-only inputs become `None` before availability checks, without coercing to `str` or mutating the caller's context | ✓ VERIFIED (full) | `button_data.py:246-248` `icon = ctx.get("cv_icon"); if not isinstance(icon, str) or not icon.strip(): icon = None`, placed before `_icon_available` (`:249`), the diagnostics, `icon_host_keys` (`:287`) and the returned dict (`:297`). Independent script: `object()`, `True`, `1`, `b"save"`, `["save"]`, `"   "`, `" \t\n"` → `None`, input dict identity preserved. `test_form_icon_normalization_*` (164) incl. `..._never_mutates_the_input`: pass. Form-branch only; `_action_button_data` untouched |
| G4 | 06-10 / D-16: invalid icons are quiet in label/both; icon-only strict raises `ValueError` naming `None`; lenient logs and renders the label; valid strings keep the existing registry/host/missing-icon policies | ✓ VERIFIED (behavior test) | `..._label_and_both_are_quiet` (asserts no warning, no `cv_title`), `..._strict_icon_mode_raises_naming_none` (asserts `"object at" not in message`), `..._keeps_nonblank_strings_exactly` (`" save "` kept byte-for-byte), `..._unavailable_nonblank_string_is_not_none` (`"unknown:save"` still goes through the missing-icon policy under its own value): pass. `test_form_button_checks.py` (273) still green, so the static-check / renderer-count behavior is unchanged |
| G5 | 06-10: repeated/interleaved copied-layout renders preserve layout isolation, field/action order, exactly one selected action group, hidden GET controls, names/values/IDs/CSS and quiet legacy helper inputs | ✓ VERIFIED (behavior test) | `test_copied_filter_layout_keeps_kind_icons` runs 3 rounds x (helper, other, helper), asserts `_controls_of(out) == _fields("name") + COPIED_CONTROLS + HIDDEN_SORT`, `len(_action_groups(out)) == 1`, one `(id, class)` tuple across all renders (`submit-id-submit`, `reset-id-reset`, project `x-go` kept), source layout fields/buttons unmodified, copies distinct per helper, `helper.form is form`. Legacy `add_input` behavior covered by T20 re-run |
| G6 | 06-10: CR-01, WR-01, WR-02 are marked fixed only with measured regression evidence; IN-01/IN-02, formatting limitations and pending human checks remain explicit | ✓ VERIFIED (full) | `06-REVIEW-DISPOSITION.md`: CR-01/WR-01/WR-02 `fixed`, each Source cell cites `06-10-SUMMARY.md` plus the RED/GREEN commits (`ae83e62`/`f33d396`, `7f974ad`/`61103dd`) and named tests; IN-01, IN-02 and the re-review's new IN-03 `open` (header `open: 3 / total: 6`, superseding the plan's pre-re-review `2 / 5`). `verify.commits` over all eight documented hashes: `all_valid: true`. The independent re-review at `1e0b38f` reached the same disposition. 06-10 SUMMARY "Remaining advisories" lists IN-01/IN-02, the four human checks, the whole-repo `ruff format` limitation and the unclassified assumptions |
| G7 | 06-10: FORM-01/FORM-02 unclassified assumptions stay flagged; the 28 classified edge predicates keep their evidence | ✓ VERIFIED (full) | `06-ACCEPTANCE.md` "Specless edge classifier: unresolved assumptions (kept visible)" present; 06-10 PLAN "Specless fallback reconciliation" table retains all 30 items (28 + 2); no 06-01..06-09 PLAN/SUMMARY changed since the previous pass |

**Score:** 42/42 truths verified (0 present, behavior-unverified)

### Deferred Items

None. Phase 7 ("Theme-surface stability policy") addresses public theme-name documentation only; nothing from this phase is deferred to it.

### Advisory (New Scope, Unevidenced)

Re-verification ran, so this section is reported explicitly. No new-scope 🛑 Blocker was raised in Step 7, so nothing was downgraded under the convergence evidence gate (#3304).

| # | Finding | Category | Why Advisory |
|---|---------|----------|--------------|
| — | None | — | — |

### Required Artifacts

`gsd_run query verify.artifacts 06-10-PLAN.md`: `all_passed: true`, 7/7 (exit 0). Levels 3 and 4 checked by hand for the code artifacts; the nine earlier plans' artifacts were tool-verified `all_passed` in the previous pass and none of their files changed since (git log since the previous `verified:` timestamp lists only `.planning/` files).

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `src/crud_views/lib/crispy/buttons.py` | Copy-stable omitted-icon state; unchanged public adapter constructors; contains `_cv_kind_icon` | ✓ VERIFIED | `__init__(self, name, value, *, slot=None, icon=_KIND_ICON, **kwargs)` signature unchanged; `_cv_kind_icon` bool set at `:131`, consumed at `:163`; wired: imported by `views/list.py:13` (`Submit`, `Reset`, `_CV_HELPER_OWNER`), `crispy/form.py` and `crud_views_workflow/lib/forms.py` (via `CrispyModelForm` hooks) |
| `src/crud_views/lib/view/button_data.py` | Form-only non-str/blank icon normalization before availability checks; contains `_form_button_data` | ✓ VERIFIED | `:246-248`; wired from `crispy/buttons.py:169-172` (`cv_button_data(raw, "form")`) and from the static checks' shared predicate path |
| `tests/test1/test_crispy_buttons.py` | Real copied-layout and direct copied-adapter regressions; contains `test_copied_filter_layout_keeps_kind_icons` | ✓ VERIFIED | `:1784`, `:1829`, `:1860`; 22 cases collected and passing; renders through the real `{% crispy %}` tag |
| `tests/test1/test_button_data.py` | Icon type, whitespace, diagnostic and purity regressions; contains `test_form_icon_normalization` | ✓ VERIFIED | Seven `test_form_icon_normalization_*` functions at `:809-898`; 164 cases passing; `INVALID_ICONS` covers `object()`, `True`, `False`, `1`, `0`, bytes, list, dict, spaces, tab/newline |
| `.planning/…/06-REVIEW-DISPOSITION.md` | Evidence-backed dispositions for the three gap findings | ✓ VERIFIED | See G6 |
| `.planning/…/06-ACCEPTANCE.md` | Dated gap-closure results without replacing historical acceptance | ✓ VERIFIED | §12 dated 2026-10-28 at HEAD `61103dd`; §1-§10 intact |
| `.planning/…/06-VALIDATION.md` | New task, command and threat evidence for 06-10 | ✓ VERIFIED | Rows 06-10-1..3 (`:62-64`), threats T-06-18..21 (`:75-78`), closure note (`:169`) |
| Previously verified artifacts (`form.html`, `base.py`, `icons.py`, `button_classes.py`, `crud_views_workflow/lib/forms.py`, `views/list.py`, `view/buttons.py`, `noxfile.py`, docs, example, goldens) | As in the previous report | ✓ VERIFIED (regression) | Unchanged since the previous pass; the two entries previously marked "VERIFIED with defect" (`crispy/buttons.py`, `views/list.py`) are now clean: the adapter is copy-stable and the helper's deepcopy was kept as designed |

### Key Link Verification

`gsd_run query verify.key-links 06-10-PLAN.md` reports "Target not referenced in source" for all 4 links (exit 1): the verb greps for the target file path inside the source file, which Python imports and Django templates never contain. Each link was therefore verified by symbol and behavior.

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `views/list.py` | `crispy/buttons.py` | `_cv_prepare_layout` deepcopy preserves the adapter's omitted-icon boolean | WIRED | `list.py:153` `copy.deepcopy(current)` unchanged; the copied adapter's `_cv_kind_icon` is a bool and copies as itself. Proven by `test_copied_filter_layout_keeps_kind_icons` and the independent script (copied `Submit` → `"save"`; pickle round-trip too) |
| `crispy/buttons.py` | `view/button_data.py` | `_cv_button_context` resolves slot defaults before `cv_button_data` normalizes the form contract | WIRED | `buttons.py:163` resolves `_KIND_ICONS[kind]` vs explicit icon; `:169-172` passes the raw dict to `cv_button_data(raw, "form")`, where `:246-248` enforces `str | None`. Order verified by reading both functions |
| `tests/test1/test_crispy_buttons.py` | `tags/button/form.html` | `_filter_render` invokes the real crispy tag and adapter render, asserting final icon and accessible-label DOM | WIRED | `_filter_render` (`:1425`) renders `FILTER_CRISPY` (`:1398`, `{% crispy form helper %}`); `_copied_buttons` parses the resulting `<button>`/`<i>`/`<span>` DOM and asserts `visually-hidden`, `title`, `data-cv-tooltip` |
| `06-REVIEW-DISPOSITION.md` | `06-10-SUMMARY.md` | Fixed findings cite the regression evidence and implementation commits recorded in the summary | WIRED | All three fixed rows' Source cells name `06-10-SUMMARY.md`, the commits and the test names; the summary's "CR-01 / WR-01 / WR-02 mapping" table matches |
| `view/buttons.py` | `view/button_data.py` | static W292 and dynamic fallback agree on modes/icons (previous pass: PARTIAL) | WIRED | Static side reads `_KIND_ICONS[kind]` (`view/buttons.py:515`, `:532`); dynamic side now also reads `_KIND_ICONS[kind]` whenever `icon=` was omitted, on copied and uncopied adapters alike. For a copied layout with default icons, static silence and a clean render now agree (independent script: no warning, no raise, strict on) |
| `06-VALIDATION.md` | `test_form_button_checks.py` | diagnostic evidence (previous pass: PARTIAL, informational) | WIRED | The 06-10 rows now name the test files and node names explicitly (`:62-63`) |
| All other 06-01..06-09 links | As in the previous report | WIRED (regression) | Source files unchanged since the previous pass |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| `form.html` | `cv_type/cv_name/cv_value/cv_id/cv_label` | adapter `name`/`value`/`input_type`/`id` → `_form_button_data` literals | Yes | ✓ FLOWING |
| `form.html` | `cv_label_mode` | `_cv_form_owner(form, context)` → `cv_get_action_label_mode("form", kind)` → map/floor | Yes | ✓ FLOWING |
| `form.html` | `cv_icon` | `_KIND_ICONS[kind]` when `_cv_kind_icon`, else the explicit `icon=`; `submit_icon`/`delete_icon` hooks; normalized to nonblank `str` or `None` | Yes, on hook-built, direct and deep-copied adapters (previous pass: STATIC on the copied path) | ✓ FLOWING |
| `form.html` | `cv_cancel_url` | `data_cv_cancel_url` kwarg, cancel kind only | Yes | ✓ FLOWING |
| `filter.html` golden | hidden `sort/order/dir` | `request.GET` → `add_input(Hidden)` | Yes | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Copied adapter keeps its kind icon (copy / deepcopy / pickle) | `.venv/bin/python -I <scratchpad>/repro_cr01_reverify.py` (Django configured via `tests/test1/conftest.pytest_configure()`, no pytest) | `raw='save' normalized='save' type=str` for all three copiers; explicit `None`/`""`/`"workflow"` and misnamed slot preserved | ✓ PASS |
| Normalizer rejects non-str / blank icons without mutating input | same script | 7 invalid inputs → `cv_icon=None`, mode `both`, caller's value identity kept; strict icon-mode `object()` → `ValueError … its icon None is not available` (no `object at`) | ✓ PASS |
| Original CR-01 scenario: class-level `Layout(… FormActions(Submit(slot="form:filter-submit"), Reset(…)))`, `get_form_actions() -> None`, real `{% crispy form helper %}` | same script, both/icon x strict/lenient | `[('submit', ['fa-solid fa-filter']), ('reset', ['fa-solid fa-rotate-left'])]`, icon mode `title`=label + `data-cv-tooltip="form"`, `warnings=''`, no exception, all four combinations | ✓ PASS |
| Stock filter helper under the same four combinations | same script | icons present, `Apply Filter`/`Reset Filter` titles in icon mode, no warnings | ✓ PASS |
| 06-10 regressions (named selection) | `pytest -p no:randomly -q tests/test1/test_crispy_buttons.py -k "copied_filter_layout or copied_adapter"` | 22 passed | ✓ PASS |
| 06-10 normalizer regressions (named selection) | `pytest -p no:randomly -q tests/test1/test_button_data.py -k form_icon_normalization` | 164 passed | ✓ PASS |
| Regression sweep A: goldens, `test_delete_author`, docs recipes, form diagnostics | `pytest -p no:randomly -q test_form_buttons_golden.py test_crud.py::test_delete_author test_form_button_docs.py test_form_button_checks.py` | 306 passed in 16.39 s | ✓ PASS |
| Regression sweep B: escaping, ownership, lifecycle, icon, class-table named tests | `pytest -p no:randomly -q test_crispy_buttons.py test_filter.py test_icon_host_leaves.py test_button_classes.py test_button_data.py -k <named list>` | 444 passed, 419 deselected in 3.78 s | ✓ PASS |
| Locked JS gate (modal submitter, cancel, filter reset) | `bash 06-js-verify.sh tests/js/modal.test.js tests/js/viewset.test.js tests/js/list.filter.test.js` | runtime/lock asserted; 3 files, 123 passed | ✓ PASS |
| Lint/format on the four 06-10 code files | `ruff check …`; `ruff format --check …` | All checks passed; 4 files already formatted | ✓ PASS |
| Commits documented in 06-10 SUMMARY / re-review exist | `verify.commits ae83e62 f33d396 7f974ad 61103dd 3e6a450 9438a5a 3c9d847 1e0b38f` | `all_valid: true` | ✓ PASS |
| No code or golden change outside the 06-10 fix | `git diff --stat ae83e62^..HEAD -- src tests` | exactly `crispy/buttons.py` (+10/-?), `button_data.py` (+6), two test files | ✓ PASS |
| `nox -s crispy_floor` | not run (builds two virtualenvs; > 10 s) | 06-10 recorded 2063 passed per environment at `61103dd` | ? SKIP |

### Probe Execution

No `scripts/*/tests/probe-*.sh` exist and no plan or summary names a probe. The phase's own gate script `06-js-verify.sh` was run (table above).

| Probe | Command | Result | Status |
| ----- | ------- | ------ | ------ |
| none declared | — | — | N/A |

### Requirements Coverage

All 13 IDs are declared across the PLAN frontmatters (06-10 re-declares FORM-02/05/08/09/10/12); REQUIREMENTS.md maps exactly FORM-01..FORM-13 to Phase 6 — no orphaned requirements. The REQUIREMENTS.md rows still read "Gaps Found": per the orchestrator this is intentional pending this report, not a defect.

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| FORM-01 | 01, 09 | Golden of today's markup committed before any change | ✓ SATISFIED | SC1; goldens untouched by 06-10 |
| FORM-02 | 01, 02, 06, 09, 10 | `"form"` location; `cv_button_data(ctx,"form")` provides `cv_type/cv_name/cv_value/cv_id/cv_cancel_url`; `cv_key` is the kind | ✓ SATISFIED | T8, T14; `cv_icon` now always `str | None` (G3) |
| FORM-03 | 02, 04, 09 | Leaf renders three bodies with `cv_button_class "form" cv_key cv_label_mode` | ✓ SATISFIED | SC2, T17 |
| FORM-04 | 02, 04, 09 | `form:hidden-label` (`visually-hidden`) and `form:icon-host` | ✓ SATISFIED | T14, T19 |
| FORM-05 | 01, 02, 05, 07, 08, 09, 10 | Submit/Button/Reset keep signature, render through leaf; `css_class` appended; extra kwargs as attributes | ✓ SATISFIED | T8, T12, T13; constructor signature unchanged by 06-10; copied `css_class="x-go"` kept (G5) |
| FORM-06 | 01, 02, 05, 07, 09 | No config → `<button type>` with same text/classes/name/value/id; POST unchanged | ✓ SATISFIED | SC1, T28 |
| FORM-07 | 02, 07, 09 | Values/labels autoescaped plain text, never evaluated | ✓ SATISFIED | SC3, T11 |
| FORM-08 | 01, 05, 07, 08, 09, 10 | Filter Apply/Reset in layout `FormActions`; `#filter-button-reset` preserved; hidden inputs unchanged | ✓ SATISFIED | T20, T21, T22, T29, G5 |
| FORM-09 | 04, 08, 09, 10 | `save`/`cancel`/`filter-reset` icons; kind mapping; workflow uses `workflow`; per-form `submit_icon` wins | ✓ SATISFIED (previously "with defect") | SC4, T18, G2: kind mapping now survives deep copy |
| FORM-10 | 03, 04, 05, 06, 08, 09, 10 | `{"form":"both"}` icon+text on all five; `{"form":"icon"}` hidden label + `title` + `data-cv-tooltip="form"` | ✓ SATISFIED (previously "with defect") | SC2, G1: custom-layout package buttons now keep icons and no longer raise |
| FORM-11 | 01, 03, 06, 08, 09 | Setting → ViewSet → view per-key maps resolve like context/list maps | ✓ SATISFIED | T15 |
| FORM-12 | 06, 08, 09, 10 | E210/E211/W291 form maps; W292 icon-only without icon; strict raises else logs and renders label | ✓ SATISFIED | T24-T26, G4: policy fires only for genuinely unavailable icons; static and dynamic agree |
| FORM-13 | 08, 09 | CHANGELOG Breaking + migrating-1.0.md "Form buttons"; example `both`; downstream follow-up in acceptance note | ✓ SATISFIED | SC5 |

### Decision Coverage

`check.decision-coverage-verify` (gate enabled): All trackable CONTEXT.md decisions are honored by shipped artifacts (honored 18 / total 18, not_honored: []). Non-blocking.

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
|-----------|-----------|--------|---------|----------|-----------------|---------|
| `test_crispy_buttons.py` (incl. 06-10 additions `:1784-1877`) | FORM-02/05/07/08/09/10 | all | 0 | no | Behavioral (real crispy tag, parsed DOM, identity checks on source vs copies, interleaving, `warnings.simplefilter("error")`, caplog) | OK |
| `test_button_data.py` (incl. 06-10 additions `:809-907`) | FORM-02/12 | all (164 new) | 0 | no | Value (exact `None`, exact message text, exact string identity, input purity) | OK, one note (IN-03 below) |
| `test_form_button_checks.py` | FORM-12 | 273 | 0 | no | Value/Behavioral | OK |
| `test_form_buttons_golden.py` | FORM-01/06/08 | all | 0 | PARTIAL (before-change oracle by design) | Value | OK |
| `test_filter.py`, `test_icon_host_leaves.py`, `test_form_button_docs.py`, `test_button_classes.py` | FORM-03/04/08/10/11/13 | all | 0 | no | Value/Behavioral | OK |
| `tests/js/*.test.js` | FORM-06/07/08 | 123 run | 0 | no | Behavioral (native FormData) | OK |

**Disabled tests on requirements:** 0 (grep for skip/xfail markers in the four changed test files and `test_form_button_checks.py`/`test_filter.py`: none). **Circular patterns detected:** 0. **Insufficient assertions:** 0. **Note (06-REVIEW IN-03, info):** `test_form_icon_normalization_keeps_nonblank_strings_exactly` branches on the outcome it asserts (`if data["cv_label_mode"] == mode … else …`); all five parameters are available icons, so the `else` branch is dead. It does not weaken this verification: the taken branch asserts string identity at value level, and the unavailable-string case is covered unconditionally by `..._unavailable_nonblank_string_is_not_none`. The previous pass's coverage hole (no test rendered a deep-copied adapter under both/icon) is closed by `test_copied_filter_layout_keeps_kind_icons`.

### Anti-Patterns Found

Scanned the four files 06-10 modified (`crispy/buttons.py`, `button_data.py`, `test_crispy_buttons.py`, `test_button_data.py`) plus a regression check of the previous pass's findings.

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| `src/crud_views/lib/crispy/buttons.py` | 26, 159 (previous pass) | identity-compared `object()` sentinel stored on a deep-copied instance | — resolved | Sentinel now compared only in `__init__` (`:131`); no instance holds it |
| `src/crud_views/lib/view/button_data.py` | 244 (previous pass) | `ctx.get("cv_icon") or None` admitted any truthy non-`str` | — resolved | `:246-248` `isinstance(icon, str)` + blank check |
| `src/crud_views/lib/crispy/buttons.py` | 163 | `_KIND_ICONS[kind]` after `kind in FORM_KINDS` relies on the two sets staying equal; no test asserts `set(_KIND_ICONS) == FORM_KINDS` directly | ℹ️ Info | `tests/test1/test_icon_host_leaves.py:365` pins `FORM_KINDS` to exactly the five names in `_KIND_ICONS`, so adding a kind fails a test before this lookup could `KeyError`; pre-existing shape, unchanged by 06-10 |
| `src/crud_views/lib/views/list.py` | 153 | per-request `copy.deepcopy` of user layouts; deep-copyable requirement undocumented (06-REVIEW IN-01, open) | ℹ️ Info | Pre-existing (06-05); deliberately left open by 06-10 |
| `src/crud_views/lib/view/button_data.py` | 280 | `flatatt` sorts extra attributes; migration note silent (06-REVIEW IN-02, open) | ℹ️ Info | Pre-existing (06-02); deliberately left open by 06-10 |
| `tests/test1/test_button_data.py` | 866-881 | adaptive assertion with an unreachable `else` (06-REVIEW IN-03, open) | ℹ️ Info | New in 06-10; test quality only, see audit above |
| `src/crud_views_workflow/lib/forms.py` | 27-33 | `LABEL-PLACEHOLDER` / `HELP-PLACEHOLDER` field labels | ℹ️ Info | Pre-existing (predates Phase 06), runtime-replaced labels |

No `TBD`/`FIXME`/`XXX` markers in any file 06-10 modified. No `TODO`/`HACK`/`PLACEHOLDER` or empty-implementation patterns in the two source files. No skipped tests. Working tree clean for `src`, `tests`, `docs`, `examples`.

**Convergence evidence gate (#3304):** no 🛑 Blocker was raised on this pass, so nothing needed the carried-forward / regression / deterministic-evidence triage. The only carried-forward gap (T18) is closed with deterministic evidence (named tests green, independent reproduction green).

### Human Verification Required

All automated must-haves are verified; the four human-only items from the previous report remain open and are carried forward unchanged (items 1-3 harvested from `06-ACCEPTANCE.md §9` and the `<human-check>` in `06-09-PLAN.md` task 2; item 4 from the previous pass). 06-10 did not change any user-visible markup for the stock paths, but item 2 now also covers the repaired custom-layout path.

### 1. Hover tooltips on form buttons in icon mode

**Test:** Run `examples/bootstrap5` with `CRUD_VIEWS_LABEL_MODE_DEFAULTS = {"form": "icon"}`; hover the save, cancel, delete and both filter buttons with a pointer.
**Expected:** A tooltip with the button's label appears on hover (focus tooltips were already observed in headless Chromium; pointer hover did not register there).
**Why human:** Synthetic `mouseMoved` did not set `:hover`; needs a real pointer.

### 2. Visual quality of the three modes

**Test:** View the create, delete and list-filter pages under `label`, `both` and `icon`, including a custom filter layout holding package `Submit`/`Reset` (the 06-10 path).
**Expected:** Icon/text spacing and alignment look right, hidden labels do not clip, the both-mode icon gap matches the context toolbar buttons, and the non-strict label fallback does not look out of place next to icon-only siblings.
**Why human:** Appearance judgment; the UI review (20/24) flagged advisory fixes only.

### 3. Screen-reader announcement

**Test:** With a screen reader, tab through the create form and the filter panel in `icon` mode and activate a button.
**Expected:** Each button is announced by its label (from the visually hidden span), the modal delete flow is announced, and reset announces the field reset.
**Why human:** Only the AX tree was inspected; no assistive technology ran.

### 4. Migration-guide readability

**Test:** Read `docs/migrating-1.0.md` "Form buttons" as a downstream maintainer with a custom `Submit` template and a filter helper that cleared `helper.inputs`.
**Expected:** The reader can migrate without guessing (selectors, literal values, `cv_*` context, `get_form_actions` None recipe). Note IN-02: the sorted extra-attribute order is still not mentioned.
**Why human:** Prose judgment.

### Gaps Summary

No gaps. The single gap from the previous pass is closed and independently reproduced as fixed.

**Gap 1 (closed) — kind icons did not survive the filter helper's layout copy (06-REVIEW CR-01).** The root cause was an identity-compared `object()` sentinel stored on adapter instances that `ListViewFilterFormHelper._cv_prepare_layout` deep-copies per helper. 06-10 (`f33d396`) moved the sentinel comparison into `__init__` and stores the omission as a private bool `_cv_kind_icon`, which copies as itself; `_cv_button_context` resolves `_KIND_ICONS[kind]` from that bool. 06-10 (`61103dd`) additionally made `_form_button_data` enforce the leaf's `str | None` icon contract before availability, diagnostics, host classes and the returned data, so a malformed icon can never reach the strict/lenient messages as an object repr. I reproduced the exact scenario from the previous report outside pytest (class-level layout, package `Submit`/`Reset`, `get_form_actions() -> None`, real `{% crispy form helper %}`): under `{"form": "both"}` and `{"form": "icon"}`, strict and lenient, both buttons carry their kind icons, icon mode carries `title` and `data-cv-tooltip="form"`, no warning is logged and nothing raises. The static W292 check and the dynamic render now read the same `_KIND_ICONS` default on copied adapters, so the previously PARTIAL static/dynamic key link is WIRED. The deepcopy isolation (D-03) was kept, not bypassed; the 12-case real-render regression asserts the source layout and its button objects are never mutated and that two helpers hold distinct copies. Everything the first pass found present, wired, data-flowing and behaviorally tested is unchanged: the four code files are the only `src`/`tests` changes since the previous HEAD, and the named-test sweep (306 + 444 pytest, 123 JS) is green.

The remaining non-blocking items are the three open info findings in `06-REVIEW-DISPOSITION.md` (IN-01 deep-copy requirement undocumented, IN-02 sorted extra-attribute order not in the migration note, IN-03 dead test branch) and the four human-only UAT checks above, which is why the status is `human_needed` rather than `passed`.

---

_Verified: 2026-10-28T10:51:09Z_
_Verifier: Claude (gsd-verifier)_
