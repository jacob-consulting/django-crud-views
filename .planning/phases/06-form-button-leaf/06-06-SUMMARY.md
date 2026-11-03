---
phase: 06-form-button-leaf
plan: "06"
subsystem: ui
tags: [crispy-forms, form-button-leaf, system-checks, label-mode, icons, accessibility, tracer]

requires:
  - phase: 06-form-button-leaf
    provides: "form leaf and FORM_LEAF_KEYS normalizer (06-02); form maps, owner recovery and form_label_mode (06-03); kind-default icons, icon=, submit_icon / delete_icon (06-04); filter helper get_form_actions layout controls (06-05)"
provides:
  - "cv_form_label_mode_checks: form-only viewset.E211 (shape, stops traversal), E210 per invalid mode in insertion order, W291 for unknown form kinds with valid modes on the view's own cv_form_actions_label_mode"
  - "crud_views.E106 for CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE against the finite FORM_KINDS"
  - "ViewSet.form_actions_label_mode construction validator rejecting unknown form kinds"
  - "cv_is_form_label_mode_map (finite-kind map predicate shared by the settings and ViewSet owners)"
  - "icons._icon_available: private, side-effect-free availability predicate (registry, library, renderer, built-in font class)"
  - "cv_form_icon_mode_checks: viewset.W292 for statically known icon-only package form controls without a usable icon"
  - "runtime missing-icon policy in the form normalizer: strict ValueError naming the kind, else a logged label fallback per render"
affects: [06-07, 06-08, 06-09]

actuals:
  tokens: 16247
  tasks: 2
  commits: 4
plan_head_before: 04853272b49cb475cc1e4e0afcfc4b6c62f7c79c
plan_head_after: 648b36b49b20533917bcc924182f722ee99ea6c0

tech-stack:
  added: []
  patterns:
    - "Static reach by MRO identity: a package hook counts as known only while vars(owner)[name] is the declared attribute (_declared/_inherits); any override makes that provider dynamic"
    - "Availability without rendering: resolve the renderer callable, never call it; the built-in font_renderer is identified by identity with the module global so a spy stays recognisable"

key-files:
  created:
    - tests/test1/test_form_button_checks.py
  modified:
    - src/crud_views/lib/view/action_menu.py
    - src/crud_views/lib/view/base.py
    - src/crud_views/lib/settings.py
    - src/crud_views/lib/viewset/__init__.py
    - src/crud_views/lib/view/buttons.py
    - src/crud_views/lib/icons.py
    - src/crud_views/lib/view/button_data.py
    - tests/test1/test_button_data.py
    - .planning/WINDOWS.md

key-decisions:
  - "Form E211 covers only a non-dict value or a non-string key and stops there; a string-keyed dict reports each invalid mode as E210, and W291 lists only unknown kinds whose modes are valid (an unknown kind with an invalid mode is reported once, as E210). Context/list cv_label_mode_checks are untouched and pinned byte-for-byte"
  - "Unknown form kinds in the settings map are E106 and in the ViewSet map a ValidationError; the open context/list key policy is unchanged"
  - "W292 static reach selects the provider before the controls: CrispyDeleteForm helper -> delete (delete_icon) + cancel; CrispyFormMixin helper and get_form_actions (incl. WorkflowForm) -> submit (submit_icon) + cancel; filter helpers only while get_filterset and get_form_actions are inherited; polymorphic_forms only via PolymorphicCrudViewMixin.get_form_class and a dict value, deduplicated per class"
  - "Only Django's own get_form_class (form_class) and the polymorphic mixin's are understood statically; any other get_form_class is request-dependent and skipped without being called"
  - "W292 skips a view whose selected form map is malformed and catches ValueError only around cv_get_action_label_mode, so E108/E210/E211/E106 survive strict checks"
  - "The runtime fallback switches to label for an empty label too (logging the both-missing message), so no title/tooltip is generated; a caller title/data-cv-tooltip then stays an ordinary escaped attribute"
  - "Host placement is not part of availability: a valid host icon is available and a None/empty form:icon-host slot remains a placement opt-out; the standalone wrapper is not validated by the predicate (E354 still reports it)"

patterns-established:
  - "Counting custom renderer fixture: each output carries its call number, proving one call per icon/both render, zero in label mode and checks, and no shared cached markup"
  - "font_renderer spy fixture: monkeypatch icons.font_renderer and reset_icon_cache() to prove the availability path never renders"

requirements-completed: [FORM-02, FORM-10, FORM-11, FORM-12]

coverage:
  - id: D1
    description: "The view's own cv_form_actions_label_mode reports E211 for shape (once, stopping traversal), E210 per invalid mode in insertion order and W291 for unknown kinds, with exact messages, via real check_viewsets, deterministic across repeated runs and for empty/non-ASCII entries"
    requirement: FORM-11
    verification:
      - kind: integration
        ref: "tests/test1/test_form_button_checks.py#test_non_string_keys_are_one_e211_and_stop_traversal"
        status: pass
      - kind: integration
        ref: "tests/test1/test_form_button_checks.py#test_mixed_map_reports_invalid_modes_then_unknown_kinds"
        status: pass
      - kind: integration
        ref: "tests/test1/test_form_button_checks.py#test_empty_and_non_ascii_entries_are_deterministic"
        status: pass
      - kind: integration
        ref: "tests/test1/test_form_button_checks.py#test_repeated_check_runs_report_the_same_messages"
        status: pass
    human_judgment: false
  - id: D2
    description: "Settings form maps are E106 and ViewSet form maps a construction error (unknown kinds included); neither emits W291; context/list E211/W291/E106 messages are unchanged; the form floor stays E108 under lazy and nested strict overrides"
    requirement: FORM-11
    verification:
      - kind: unit
        ref: "tests/test1/test_form_button_checks.py#test_invalid_settings_form_map_is_one_e106"
        status: pass
      - kind: unit
        ref: "tests/test1/test_form_button_checks.py#test_viewset_rejects_invalid_form_maps"
        status: pass
      - kind: unit
        ref: "tests/test1/test_form_button_checks.py#test_context_list_e211_is_unchanged"
        status: pass
      - kind: integration
        ref: "tests/test1/test_form_button_checks.py#test_nested_floor_recovery_under_strict"
        status: pass
    human_judgment: false
  - id: D3
    description: "One side-effect-free availability predicate: registry-disabled names, unknown prefixes, unusable renderers and invalid built-in font classes are unavailable; raw classes, custom renderers and valid host icons are available; no renderer runs; E354 keeps its ID/message/severity"
    requirement: FORM-12
    verification:
      - kind: unit
        ref: "tests/test1/test_form_button_checks.py#test_icon_availability_predicate"
        status: pass
      - kind: unit
        ref: "tests/test1/test_form_button_checks.py#test_invalid_builtin_font_class_is_unavailable_and_keeps_e354"
        status: pass
      - kind: unit
        ref: "tests/test1/test_form_button_checks.py#test_usable_builtin_font_class_is_available"
        status: pass
    human_judgment: false
  - id: D4
    description: "Static W292 for icon-only package controls: delete/cancel on delete forms (never the inherited submit_icon), submit/cancel on ordinary and workflow forms, filter helper defaults, each concrete polymorphic form class once; overridden helpers/hooks, custom get_form_class and non-dict polymorphic_forms are skipped without instantiation"
    requirement: FORM-12
    verification:
      - kind: integration
        ref: "tests/test1/test_form_button_checks.py#test_delete_form_inspects_delete_and_cancel_never_submit"
        status: pass
      - kind: integration
        ref: "tests/test1/test_form_button_checks.py#test_concrete_polymorphic_forms_are_each_inspected_once"
        status: pass
      - kind: integration
        ref: "tests/test1/test_form_button_checks.py#test_filter_helper_with_default_actions_is_statically_known"
        status: pass
      - kind: integration
        ref: "tests/test1/test_form_button_checks.py#test_checks_never_instantiate_forms_or_helpers"
        status: pass
      - kind: integration
        ref: "tests/test1/test_form_button_checks.py#test_mode_errors_survive_and_hide_no_w292"
        status: pass
    human_judgment: false
  - id: D5
    description: "Runtime: icon mode without an available icon raises ValueError naming the kind in strict mode, else logs once per render and renders the literal label with label classes, no generated title/tooltip/host class, FORM_LEAF_KEYS-only data; real crispy, delete, polymorphic create/update and filter endpoints prove the dynamic providers"
    requirement: FORM-12
    verification:
      - kind: unit
        ref: "tests/test1/test_form_button_checks.py#test_strict_missing_icon_raises_naming_the_kind"
        status: pass
      - kind: unit
        ref: "tests/test1/test_form_button_checks.py#test_non_strict_missing_icon_logs_and_uses_the_label"
        status: pass
      - kind: integration
        ref: "tests/test1/test_form_button_checks.py#test_custom_submit_hooks_follow_the_runtime_policy"
        status: pass
      - kind: integration
        ref: "tests/test1/test_form_button_checks.py#test_polymorphic_create_follows_the_runtime_policy"
        status: pass
      - kind: integration
        ref: "tests/test1/test_form_button_checks.py#test_filter_helper_follows_the_runtime_policy"
        status: pass
    human_judgment: false
  - id: D6
    description: "A counting custom inline renderer runs once per icon/both render and never in label mode or checks; host icons and None/empty form:icon-host opt-outs render without inline probes, W292, log or exception; a disabled host semantic icon follows the missing-icon policy"
    requirement: FORM-02
    verification:
      - kind: integration
        ref: "tests/test1/test_form_button_checks.py#test_counting_inline_renderer_runs_once_per_icon_render"
        status: pass
      - kind: integration
        ref: "tests/test1/test_form_button_checks.py#test_host_form_renders_without_inline_probes_or_false_fallback"
        status: pass
      - kind: integration
        ref: "tests/test1/test_form_button_checks.py#test_disabled_host_semantic_icon_follows_the_missing_icon_policy"
        status: pass
    human_judgment: false
  - id: D7
    description: "Visual and assistive-technology adequacy of the label fallback (a former icon-only button now showing its text) in a real browser"
    requirement: FORM-10
    verification: []
    human_judgment: true
    rationale: "Tests assert the DOM, classes and attributes; how the fallback looks next to icon-only siblings and how screen readers announce it needs the 06-09 browser pass"

duration: 20min
completed: 2026-10-28
status: complete
---

# Phase 06 Plan 06: Form-button diagnostics and missing-icon fallback Summary

**Form label-mode mistakes now surface through existing check IDs, and icon-only form buttons without a usable icon can no longer render invisibly. A view's own `cv_form_actions_label_mode` gets a form-only E211/E210/W291 policy against the finite `FORM_KINDS`. The settings map is checked by E106 and the ViewSet map at construction. W292 covers statically known package form controls (delete forms, ordinary and workflow forms, filter helpers, concrete polymorphic maps). At render time, an unavailable icon raises in strict mode and otherwise falls back to the literal label. All three decisions use one private predicate, `icons._icon_available`, that never renders.**

## Performance

- **Duration:** 20 min
- **Started:** 2026-10-28T07:28:09Z
- **Completed:** 2026-10-28T07:49:04Z
- **Tasks:** 2
- **Files modified:** 10 (1 created)

## Accomplishments

- **Form map checks (Task 1).** `cv_form_label_mode_checks` in `action_menu.py` is wired from `CrudView.checks`.
  - A non-dict value or any non-string key gives one E211, and checking stops there.
  - Each invalid mode gives its own E210, in insertion order.
  - Unknown kinds with valid modes give one W291. It names the sorted `FORM_KINDS` and the form floor, not "this view's actions".
  - `None` and `{}` are valid.
  - Context and list checks keep their exact messages, and tests pin them.
- **Settings and ViewSet owners.** `CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE` gets one E106 that names the form kinds. `ViewSet.form_actions_label_mode` has its own validator that rejects unknown kinds. Both use `cv_is_form_label_mode_map`. The context and list maps still accept any action key.
- **Availability predicate.** `icons._icon_available(value)` returns False for:
  - `resolve_icon(value) is None` (including names that `CRUD_VIEWS_ICONS` maps to None or "")
  - a prefix with no dict library entry or no usable renderer
  - a built-in `font_renderer` library (explicit or default) whose `class` is not a nonempty str that formats with the icon name

  Raw classes, custom renderers and valid host icons count as available. The predicate never calls a renderer.
- **Static W292 (Task 2).** `cv_form_icon_mode_checks` in `view/buttons.py`:
  - picks form classes without a request (`form_class` via Django's `get_form_class`, or each distinct class of a dict `polymorphic_forms`)
  - picks the provider before the controls (delete forms check `delete_icon` and cancel; other forms check `submit_icon` and cancel)
  - adds the filter helper's two default controls
  - resolves each mode through `cv_get_action_label_mode("form", kind)` and warns when the mode is icon-only and the icon is unavailable

  It never instantiates a form or helper and never calls a hook.
- **Runtime policy.** After mode and icon resolution, `_form_button_data` raises a `ValueError` naming the kind in strict mode. Otherwise it logs a warning on every render and switches to `label`: no generated title or tooltip, no host class, and the label and value stay literal. When the label is empty too, it keeps the empty payload and logs the both-missing message.

## Task Commits

1. **Task 1 (tracer): Report malformed form maps through actual system checks.** RED `b1e8e5a` (test), GREEN `d8c9871` (feat). Tracer gate (interactive, end-of-phase, automated-only verify): re-ran the Task 1 verify after GREEN (262 passed), then expanded to Task 2.
2. **Task 2: Align static W292 reach and dynamic missing-icon fallback.** RED `8864205` (test), GREEN `648b36b` (feat).

**Plan metadata:** recorded in the docs commit for this plan.

## Files Created/Modified

- `tests/test1/test_form_button_checks.py` (new, 273 tests): the map and missing-icon regressions listed under coverage
- `src/crud_views/lib/view/action_menu.py`: `cv_is_form_label_mode_map`, `cv_form_label_mode_checks`
- `src/crud_views/lib/view/base.py`: wires the form map and form icon checks into `CrudView.checks`
- `src/crud_views/lib/settings.py`: E106 for `CRUD_VIEWS_FORM_ACTIONS_LABEL_MODE`
- `src/crud_views/lib/viewset/__init__.py`: separate `form_actions_label_mode` validator
- `src/crud_views/lib/view/buttons.py`: `_declared`/`_inherits`, the static form, control and filter reach, and `cv_form_icon_mode_checks`
- `src/crud_views/lib/icons.py`: `_icon_available`
- `src/crud_views/lib/view/button_data.py`: the strict and logged-fallback guard in the form branch
- `tests/test1/test_button_data.py`: `form_ctx` gets an available default icon (see deviations)
- `.planning/WINDOWS.md`: stub #8 (form missing-icon policy) marked fixed

## Decisions Made

See `key-decisions` in the frontmatter.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] 06-02-era form leaf fixtures rendered icon mode without an icon**
- **Found during:** Task 2 (GREEN)
- **Issue:** `tests/test1/test_button_data.py::form_ctx` had no `cv_icon`. Its icon-mode cases had been asserting the 06-02 stub behaviour, a hidden label with no icon, which this plan replaces with the strict `ValueError`. Nine tests failed.
- **Fix:** `form_ctx` now defaults to `cv_icon="save"`. These tests pin the key/presence/floor contract, not the missing-icon policy, which `test_form_button_checks.py` covers. No assertion was weakened.
- **Files modified:** `tests/test1/test_button_data.py`
- **Committed in:** `648b36b`

**2. [Rule 1 - Bug] Task 1 resolver-isolation test was too broad**
- **Found during:** Task 2 (GREEN)
- **Issue:** `test_checks_do_not_resolve_the_mode` patched the form-map resolver to raise and ran all of `check_viewsets`. The new W292 check is required to call that public resolver.
- **Fix:** The test is renamed `test_map_checks_do_not_resolve_the_mode`. It now calls `cv_form_label_mode_checks` directly with both resolvers patched to raise, which keeps its original intent.
- **Committed in:** `648b36b`

**3. [Simplification] Redundant per-traversal dedupe removed**
- **Found during:** Task 2 mutation checks
- **Issue:** A `(class, kind)` seen-set in `cv_form_icon_mode_checks` never fired, because `_static_form_classes` already deduplicates form classes. Removing it left the tests green.
- **Fix:** I dropped the seen-set and documented that the class-level dedupe is the single owner. Mutating that dedupe makes 2 tests fail.
- **Committed in:** `648b36b`

### Process notes

- **Mutation sanity**, each applied in place and restored from a scratchpad copy (no `git checkout`):
  - E211 not stopping traversal: 9 failures
  - settings map using the open-key predicate: 4
  - delete provider not chosen first: 1
  - class dedupe removed: 2
  - truthiness instead of availability (static): 26
  - truthiness in the normalizer: 79
  - no font class validation: 58
  - raw class unavailable: 4
  - no form strict raise: 56
  - no label switch: 57
  - no `ValueError` guard: 5
  - custom delete helper treated as static: 1
- My first strict-raise mutation also matched the older action-branch text and seemed to survive. A form-specific anchor shows 56 failures.
- One expectation in the new tests was wrong: Django's `flatatt` sorts attributes. It was fixed before the GREEN commit.

**Total deviations:** 2 auto-fixed (Rule 1 test-expectation updates) plus 1 simplification. No scope change.

## Issues Encountered

- `ViewSet(...)` registers names process-wide, so the parametrized constructor test uses one name per parameter.
- The pre-existing JS failure (`tests/js/list.filter.test.js:159`, jsdom 30.1.2) is unrelated and owned by 06-07. This plan changed no JS.

## Known Stubs

None. WINDOWS #8 (form missing-icon policy) is fixed by this plan.

## Threat Flags

None. No new endpoint, auth path or schema change.
- **T-06-11** is mitigated: checks never instantiate forms or helpers and never call `get_form_class`, hooks or renderers. `test_checks_never_instantiate_forms_or_helpers`, `test_request_dependent_form_class_is_skipped` and the zero-renderer-call assertions cover this. `ValueError` is caught only around mode resolution.
- **T-06-12** is mitigated by the strict and non-strict runtime tests. They check the exception, the one log per render, the literal label, label classes and the absence of a generated title, tooltip or host class.
- **T-06-SC:** no dependency was installed.

## User Setup Required

None. No external service configuration required.

## Next Phase Readiness

- 06-07 owns the JS gate and the jsdom failure. No JS changed here.
- 06-08 should document the following:
  - the form-only diagnostic distinction (E211 for shape, E210 per mode, W291 for unknown kinds, and E106 or a construction error for the settings and ViewSet maps)
  - W292 static reach and its skipped dynamic providers
  - the runtime strict and log-and-label policy, including that `submit_icon="unknown:save"` and an invalid built-in font `class` count as missing icons
- Verification:
  - the plan's Task 1 shard: 262 passed
  - the Task 2 shard: 603 passed
  - `tests/test1/test_import_safety.py`: 18 passed
  - full `pytest tests -n auto`: 4428 passed
  - `ruff check` and `ruff format --check` on `src` and `tests`: clean

## Self-Check: PASSED

- Created and modified key files exist on disk (9 checked).
- Commits `b1e8e5a`, `d8c9871`, `8864205` and `648b36b` are ancestors of HEAD. Measured `git rev-list --count 0485327..HEAD` = 4, and `check evaluation-scope --plan 06-06 --commits-only` resolves them.

---
*Phase: 06-form-button-leaf*
*Completed: 2026-10-28*
