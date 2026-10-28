---
phase: 06-form-button-leaf
plan: "03"
subsystem: ui
tags: [crispy-forms, form-button-leaf, label-mode, ownership, formsets, tracer]

requires:
  - phase: 06-form-button-leaf
    provides: "form" location, FORM_LEAF_KEYS normalizer and literal form leaf rendered by the layout adapters (06-02)
provides:
  - CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE (CrudViewsSettings.form_actions_label_mode, import-time singleton like the context/list maps)
  - ViewSet.form_actions_label_mode (construction-validated label-mode map)
  - CrudView.cv_form_actions_label_mode and cv_get_form_actions_label_mode() (whole-map view -> ViewSet -> setting)
  - cv_get_action_label_mode("form", kind) (membership, then the lazy form floor)
  - shared form_label_mode() in label_mode.py with strict/log fallback for invalid selected maps or values
  - owner selection for layout Submit/Button/Reset (render form cv_view -> current helper -> page), quiet and identity-based
  - private page-owner transport across Formsets.render (flatten) and cv_x_formset (context.new), recursive
affects: [06-04, 06-05, 06-06, 06-08]

tech-stack:
  added: []
  patterns:
    - "Crispy response overlays are recognised by get_response_dict metadata (is_formset, template_pack, inputs, form_method/formset_method) and are never page layers"
    - "Private underscore context keys (_cv_helper_owner, _cv_page_owner): unreadable from templates, not published by FormHelper.get_attributes"
    - "Owner-recovery helpers live in crud_views.lib.crispy.buttons as pure functions; callers in formsets/layout.py and crud_views_formsets.py import them at call time"

key-files:
  created: []
  modified:
    - src/crud_views/lib/settings.py
    - src/crud_views/lib/viewset/__init__.py
    - src/crud_views/lib/view/base.py
    - src/crud_views/lib/view/label_mode.py
    - src/crud_views/lib/crispy/buttons.py
    - src/crud_views/lib/formsets/layout.py
    - src/crud_views/templatetags/crud_views_formsets.py
    - tests/test1/test_action_label_mode_config.py
    - tests/test1/test_crispy_buttons.py

key-decisions:
  - "Invalid form maps are validated by the shared form_label_mode(): a non-dict selected map or a non-mode mapped value raises in strict mode, otherwise warns once and uses the form floor. A mapped value is never returned unvalidated, unlike the list resolver"
  - "Task 1 routes only the render form's cv_view; Task 2 adds the current-helper tier (a private _cv_helper_owner entry above the nearest overlay, else that overlay's view) and the page tier (transported _cv_page_owner, authoritative even when None, else the nearest non-None view outside every response overlay)"
  - "Formsets.render no longer pushes a formsets layer onto the crispy node context. It renders a flattened copy that adds formsets and the captured page owner"
  - "_CV_HELPER_OWNER is defined and read now; the package filter helper's push of it belongs to 06-05"
  - "E106 for the new setting and form-specific E210/E211/W291 belong to 06-06; settings.md and lifecycle prose belong to 06-08"

patterns-established:
  - "Owner signature tests: give each owner a distinct (submit, cancel) mode pair and map every form:<kind>:<mode> class to m-<mode>, so the rendered classes name the owner that won"
  - "Mutation sanity on the owner tiers: break overlay skipping, identity checks, helper tier and each transport in place, confirm a failure, then restore"

requirements-completed: [FORM-10, FORM-11]

coverage:
  - id: D1
    description: "The form maps on the setting, the ViewSet and the view are each selected whole. An empty winning map suppresses the lower ones, unmapped kinds read the lazy form floor, and explicit modes never read an invalid strict floor"
    requirement: FORM-11
    verification:
      - kind: unit
        ref: "tests/test1/test_action_label_mode_config.py#test_form_maps_are_selected_whole"
        status: pass
      - kind: unit
        ref: "tests/test1/test_action_label_mode_config.py#test_explicit_form_mode_bypasses_invalid_floor"
        status: pass
      - kind: unit
        ref: "tests/test1/test_action_label_mode_config.py#test_invalid_selected_form_map_uses_shared_fallback"
        status: pass
    human_judgment: false
  - id: D2
    description: "The maps reach real crispy output and the create endpoint. Overriding only the map with override_settings changes nothing; the nested floor override changes only unmapped kinds and is restored on exit"
    requirement: FORM-11
    verification:
      - kind: integration
        ref: "tests/test1/test_action_label_mode_config.py#test_settings_map_reaches_the_leaf_and_only_the_floor_is_live"
        status: pass
      - kind: integration
        ref: "tests/test1/test_action_label_mode_config.py#test_view_map_reaches_the_endpoint"
        status: pass
    human_judgment: false
  - id: D3
    description: "Owner priority is form cv_view, then the current helper, then the page. A None owner falls through, while ordinary, falsey and string owners stop the lookup. Helper view=None overlays, stacked enclosing helpers and FormActions leftover layers never hide or replace the page"
    requirement: FORM-10
    verification:
      - kind: integration
        ref: "tests/test1/test_crispy_buttons.py#test_owner_priority"
        status: pass
      - kind: integration
        ref: "tests/test1/test_crispy_buttons.py#test_enclosing_helper_overlays_are_never_page_layers"
        status: pass
      - kind: integration
        ref: "tests/test1/test_crispy_buttons.py#test_overlay_classification_on_stacked_invocations"
        status: pass
    human_judgment: false
  - id: D4
    description: "Formset rows on the real Layout(Formsets()) -> formsets.html -> cv_x_formset -> formset.html path use the row form, then the row helper, then the transported page. This holds for recursive children and standalone cv_x_formset, and the caller context is unchanged after repeated or failing renders"
    requirement: FORM-10
    verification:
      - kind: integration
        ref: "tests/test1/test_crispy_buttons.py#test_formset_rows_use_the_row_form_then_row_helper_then_page"
        status: pass
      - kind: integration
        ref: "tests/test1/test_crispy_buttons.py#test_formset_page_tier_is_transported_exactly"
        status: pass
      - kind: integration
        ref: "tests/test1/test_crispy_buttons.py#test_formset_render_failure_leaves_the_caller_context_unchanged"
        status: pass
    human_judgment: false
  - id: D5
    description: "The formset tag library and the public WorkflowForm import still work after settings.configure() alone"
    verification:
      - kind: unit
        ref: "tests/test1/test_import_safety.py::test_templatetags_import_without_app_registry"
        status: pass
      - kind: unit
        ref: "tests/test1/test_import_safety.py::test_workflow_lib_model_mixin_public_path_imports_without_app_registry"
        status: pass
    human_judgment: false

actuals:
  tokens: 9897
  tasks: 2
  commits: 4
plan_head_before: 148350fe1cc118d0d038855262083e87e2ed51b1
plan_head_after: b8df8c17800135d14a21242fe4532fdbf32181b4

duration: 11min
completed: 2026-10-28
status: complete
---

# Phase 06 Plan 03: Form-button ownership and form maps Summary

**Crispy layout buttons now take their mode from the view that owns them. The owner is the render form's `cv_view`, else the current helper, else the page, chosen by identity and without warnings. That owner's whole form map applies (view, then ViewSet, then `CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE`), and unmapped kinds fall to the lazy `"form"` floor. Formset rows get the page owner through a private key, so `context.flatten()` and the inclusion `context.new()` no longer drop it.**

## Performance

- **Duration:** 11 min
- **Started:** 2026-10-28T06:38:50Z
- **Completed:** 2026-10-28T06:50:04Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments

- **New map fields and resolvers.** Three new fields hold a form map: `CrudViewsSettings.form_actions_label_mode`, `ViewSet.form_actions_label_mode` (checked by the existing label-mode validator) and `CrudView.cv_form_actions_label_mode`. `cv_get_form_actions_label_mode()` picks one of them whole through `cv_first_inline_keys`. `cv_get_action_label_mode("form", kind)` uses map membership, then `default_label_mode("form")`. Context, list and card behaviour is unchanged; the error for an unknown location now names `'form'`.
- **Shared `form_label_mode()`.** It turns a bad selected map (a list, a str or an int) or a bad mapped mode into the shared strict/warn-once fallback instead of a membership crash. A valid explicit mode never reads the floor.
- **Map lifecycle proven in real crispy output.** The map is read once at import, like the context and list maps. With the singleton monkeypatched to `submit='both'`, wrapping the render in `override_settings` of only the map keeps submit at `both`. A nested `CRUD_VIEWS_LABEL_MODE_DEFAULTS={'form': 'icon'}` changes only the unmapped cancel, and the floor is restored on exit.
- **Owner selection.** A CrudView owner (class or instance) is resolved through its public seam, so subclass overrides apply. An ordinary, falsey or string owner stops the lookup and uses the settings map; a lower CrudView is never borrowed.
- **How the helper and page owners are found.** The current helper is the nearest crispy response overlay, or a private `_cv_helper_owner` entry above it. The page owner is the transported `_cv_page_owner`, or else the nearest non-None `view` outside every overlay. Stack offsets and `form.helper` are never used.
- **Formset transport.** `Formsets.render` and `cv_x_formset` pass only the page-tier owner across the formset boundaries, recursively, and derive it when called on a live page. Both deferred imports keep the two unchanged bare-settings import tests green.

## Task Commits

1. **Task 1 (tracer): Resolve a setting and view map through the actual form leaf.** RED `5486bca` (test), GREEN `379d079` (feat). Tracer gate (interactive, end-of-phase, automated-only verify): re-ran the verify after GREEN (245 passed), then expanded to Task 2.
2. **Task 2: Preserve ownership under crispy helper overlays and embedded forms.** RED `0b45e77` (test), GREEN `b8df8c1` (feat).

**Plan metadata:** recorded in the final docs commit for this plan.

## Files Created/Modified

- `src/crud_views/lib/settings.py`: `form_actions_label_mode` from `CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE` (default `{}`)
- `src/crud_views/lib/viewset/__init__.py`: `form_actions_label_mode` field plus the label-mode map validator
- `src/crud_views/lib/view/base.py`: `cv_form_actions_label_mode`, `cv_get_form_actions_label_mode()`, the `form` branch of `cv_get_action_label_mode`
- `src/crud_views/lib/view/label_mode.py`: `form_label_mode(mapping, kind)`
- `src/crud_views/lib/crispy/buttons.py`: private owner tiers, overlay classification, `_cv_form_label_mode`, and `render()` passing `cv_label_mode`
- `src/crud_views/lib/formsets/layout.py`: `Formsets.render` flattens a scoped copy that adds `formsets` and the page owner
- `src/crud_views/templatetags/crud_views_formsets.py`: `cv_x_formset` returns the private page-owner key
- `tests/test1/test_action_label_mode_config.py`, `tests/test1/test_crispy_buttons.py`: the regressions listed under coverage

## Decisions Made

See `key-decisions` in the frontmatter.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Shared form resolver placed in `label_mode.py`**
- **Found during:** Task 1
- **Issue:** The plan's file list leaves out `label_mode.py`. But the strict/log fallback that both the CrudView seam and the ownerless adapter path need (`_invalid_label_mode`) lives there, as do the other floor helpers.
- **Fix:** Added `form_label_mode()` there and used it from `base.py` and `crispy/buttons.py`. `label_mode.py` is already imported by `base.py`, so this adds no new import edge.
- **Files modified:** `src/crud_views/lib/view/label_mode.py`
- **Commit:** `379d079`

**2. [Rule 1 - Bug] `Formsets.render` pushed a layer onto the crispy node context**
- **Found during:** Task 2
- **Issue:** `context.update({"formsets": ...})` left a persistent layer on the context it was given. The plan requires scoped state with no leaks.
- **Fix:** It now renders a flattened copy that adds `formsets` and the transported page owner. The `formsets` value the template sees is the same as before.
- **Files modified:** `src/crud_views/lib/formsets/layout.py`
- **Commit:** `b8df8c1`

### TDD notes

- RED was confirmed for both tasks before any implementation: Task 1 had 28 failing tests and Task 2 had 24 after a test-helper fix. In that helper, a falsey owner fell through `or` to `getattr`.
- Mutation sanity on Task 2, each applied in place and then restored. Five of six mutations fail a test: reading overlays as page layers, truthiness instead of `is None`, turning off the helper tier, dropping the inclusion transport, and dropping the `Formsets` transport. The sixth, making a transported None non-authoritative, passed the integration tests: on the production path, every context where the transported value is None also has no genuine page `view`. I added `test_transported_page_owner_is_authoritative_even_when_none` to pin the contract directly.

**Total deviations:** 2 auto-fixed (1 blocking placement, 1 scoped-state bug). No scope change.

## Issues Encountered

- The pre-existing JS failure (`tests/js/list.filter.test.js:159`, jsdom 30.1.2) is unrelated and owned by 06-07. This plan changed no JS.
- This plan adds no validation of `CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE` itself (E106) and no form-specific E210/E211/W291 view checks; those are 06-06. A malformed setting is handled at render time by the shared strict/log fallback.

## Known Stubs

None added. The 06-02 icon stub (no `cv_icon` from layout adapters) stays open for 06-04 in the WINDOWS ledger.

## Threat Flags

None. T-06-05 is mitigated by the conflicting-owner regressions across all three tiers, covering None overlays and ordinary/falsey owners. T-06-06 is mitigated by the unchanged-caller-context, interleaved and failing-render regressions, with no instance or global owner cache. No dependency was installed (T-06-SC).

## User Setup Required

None. No external service configuration required.

## Next Phase Readiness

- 06-04 can pass `cv_icon` through `raw` in `_TableClassMixin.render`. `cv_label_mode` is already resolved there.
- 06-05 can push `{_CV_HELPER_OWNER: view}` around `ListViewFilterFormHelper.render_layout`'s `super()` call; `_cv_helper_tier` already reads it.
- 06-06 can add E106 for the setting and the form-specific view checks on `cv_form_actions_label_mode`.
- 06-08 documents the startup snapshot vs. the lazy floor, as proven by `test_settings_map_reaches_the_leaf_and_only_the_floor_is_live`.
- Verification: both shards 287 passed, the import-safety pair 2 passed, the full `pytest tests -n auto` 4022 passed, and ruff is clean.

## Self-Check: PASSED

- Modified key files exist: `crispy/buttons.py`, `formsets/layout.py`, `crud_views_formsets.py`, `label_mode.py`, `base.py`, `settings.py`, `viewset/__init__.py`.
- Commits `5486bca`, `379d079`, `0b45e77`, `b8df8c1` are ancestors of HEAD; measured `git rev-list --count 148350f..HEAD` = 4.

---
*Phase: 06-form-button-leaf*
*Completed: 2026-10-28*
