---
phase: 06-form-button-leaf
plan: "04"
subsystem: ui
tags: [crispy-forms, form-button-leaf, icons, label-mode, accessibility, workflow, tracer]

requires:
  - phase: 06-form-button-leaf
    provides: "form leaf with label/both/icon bodies, form:hidden-label / form:icon-host utility keys (06-02); form-map ownership and cv_label_mode resolution in the adapters (06-03)"
provides:
  - save, cancel and filter-reset in DEFAULT_ICONS and BOOTSTRAP_ICONS
  - kind-default icons for layout Submit/Button/Reset chosen from the slot (submit save, delete delete, cancel cancel, filter-submit filter, filter-reset filter-reset)
  - adapter icon= keyword with a sentinel default (omitted = kind default, explicit None/"" = no icon), never serialized as an attribute
  - CrispyFormMixin.submit_icon = "save", CrispyDeleteForm.delete_icon = "delete", WorkflowForm.submit_icon = "workflow"
  - real-render coverage of icon/both/label bodies for inline (element) and host-placed icon libraries
affects: [06-05, 06-06, 06-08, 06-09]

actuals:
  tokens: 9299
  tasks: 2
  commits: 4
plan_head_before: 3bb016d1bd8b56a485ab60e7bcec85162d8d5637
plan_head_after: 0960031099d99076a3bd06dc290cff6e006c1826

tech-stack:
  added: []
  patterns:
    - "Sentinel default for icon= (_KIND_ICON = object()): omission and an explicit None/empty are distinct, so intentional suppression reaches the normalizer"
    - "Hook kwargs merge order {form-attribute defaults, **hook_kwargs}: a hook's icon or slot wins over the form attribute, which wins over the adapter kind default"

key-files:
  created: []
  modified:
    - src/crud_views/lib/icons.py
    - src/crud_views/lib/crispy/buttons.py
    - src/crud_views/lib/crispy/form.py
    - src/crud_views_workflow/lib/forms.py
    - tests/test1/test_icon_host_leaves.py
    - tests/test1/test_icons_registry.py
    - tests/test1/test_crispy_buttons.py

key-decisions:
  - "Registry glyphs: save far:floppy-disk / bi:floppy, cancel fas:xmark / bi:x-lg, filter-reset fas:rotate-left / bi:arrow-counterclockwise; filter-reset stays distinct from the filter-close panel-toggle icon"
  - "The kind-to-icon map is private (_KIND_ICONS in crispy/buttons.py). The public seams are icon=, submit_icon and delete_icon"
  - "A delete hook that moves the delete payload to slot form:cancel gets cancel classes and kind but keeps the form's delete_icon: the explicit form icon wins over the kind default"
  - "No cancel_icon attribute was added (not in the spec). The cancel icon is the adapter kind default, and a cancel hook can override it with an icon kwarg"
  - "The form leaf template needed no change: it already reads mode classes through cv_button_class and the form utility keys through dedicated lookups, with autoescaped host classes"

patterns-established:
  - "Element vs host form tests: override CRUD_VIEWS_ICONS={} for package-default inline icons, or with a host map, inside the module-wide host fixture"
  - "The client_user_* fixtures share one Client, so endpoint tests that need different users are parametrized one page per test"

requirements-completed: [FORM-03, FORM-04, FORM-09, FORM-10]

coverage:
  - id: D1
    description: "save, cancel and filter-reset exist in both registries, the Bootstrap preset covers exactly the default names, and filter-reset is distinct from filter-close"
    requirement: FORM-09
    verification:
      - kind: unit
        ref: "tests/test1/test_icons_registry.py#test_form_icon_defaults"
        status: pass
      - kind: unit
        ref: "tests/test1/test_icons_registry.py#test_bootstrap_preset_covers_exactly_default_names"
        status: pass
    human_judgment: false
  - id: D2
    description: "All five form kinds render icon mode (inline icon, hidden label, title, data-cv-tooltip=form), both mode (icon + text, no generated title) and label mode (no icon, no host class). This holds for Font Awesome, Bootstrap, raw-class and custom-renderer prefixes"
    requirement: FORM-03
    verification:
      - kind: integration
        ref: "tests/test1/test_icon_host_leaves.py#test_form_element_icon_mode"
        status: pass
      - kind: integration
        ref: "tests/test1/test_icon_host_leaves.py#test_form_element_both_mode"
        status: pass
      - kind: integration
        ref: "tests/test1/test_icon_host_leaves.py#test_form_label_mode_suppresses_every_icon"
        status: pass
      - kind: integration
        ref: "tests/test1/test_icon_host_leaves.py#test_form_raw_class_and_custom_renderer_prefixes"
        status: pass
    human_judgment: false
  - id: D3
    description: "Host icons put the form:icon-host class on the button with no inline element. A None/empty form:icon-host override opts out. Host and hidden-label classes are escaped attributes, and the utility keys never take a mode suffix (W362)"
    requirement: FORM-04
    verification:
      - kind: integration
        ref: "tests/test1/test_icon_host_leaves.py#test_form_host_icon_goes_on_the_button"
        status: pass
      - kind: integration
        ref: "tests/test1/test_icon_host_leaves.py#test_form_host_slot_none_or_empty_switches_the_icon_off"
        status: pass
      - kind: integration
        ref: "tests/test1/test_icon_host_leaves.py#test_form_host_classes_are_escaped_attributes"
        status: pass
      - kind: unit
        ref: "tests/test1/test_icon_host_leaves.py#test_form_utility_keys_and_finite_grammar"
        status: pass
    human_judgment: false
  - id: D4
    description: "Unicode, lazy and empty labels keep exact visible/hidden/title text. Repeated renders across registries, settings and languages leave the shared icon and class defaults unchanged"
    requirement: FORM-03
    verification:
      - kind: integration
        ref: "tests/test1/test_icon_host_leaves.py#test_form_unicode_and_lazy_labels_are_exact"
        status: pass
      - kind: integration
        ref: "tests/test1/test_icon_host_leaves.py#test_form_empty_label_in_icon_mode"
        status: pass
      - kind: integration
        ref: "tests/test1/test_icon_host_leaves.py#test_form_repeated_renders_follow_the_current_registry"
        status: pass
    human_judgment: false
  - id: D5
    description: "Kind icons follow the slot, never the submitted name. icon= overrides the kind default, explicit None/'' reaches the normalizer as no icon, and icon= is never serialized on layout or legacy input paths"
    requirement: FORM-09
    verification:
      - kind: integration
        ref: "tests/test1/test_crispy_buttons.py#test_kind_default_icons"
        status: pass
      - kind: integration
        ref: "tests/test1/test_crispy_buttons.py#test_kind_icon_follows_the_slot_not_the_name"
        status: pass
      - kind: integration
        ref: "tests/test1/test_crispy_buttons.py#test_explicit_none_or_empty_icon_suppresses_the_kind_default"
        status: pass
      - kind: integration
        ref: "tests/test1/test_crispy_buttons.py#test_icon_keyword_is_configuration_not_an_attribute"
        status: pass
    human_judgment: false
  - id: D6
    description: "Real create/update/delete/workflow endpoints under the form floor both/icon render save/delete/workflow plus cancel with unchanged payloads. Per-form submit_icon/delete_icon and hook kwargs follow the precedence, the label floor stays icon-free, and form instances do not share icons or language"
    requirement: FORM-10
    verification:
      - kind: integration
        ref: "tests/test1/test_crispy_buttons.py#test_package_forms_render_their_semantic_icons"
        status: pass
      - kind: integration
        ref: "tests/test1/test_crispy_buttons.py#test_workflow_form_uses_the_workflow_icon"
        status: pass
      - kind: integration
        ref: "tests/test1/test_crispy_buttons.py#test_per_form_submit_icon_wins"
        status: pass
      - kind: integration
        ref: "tests/test1/test_crispy_buttons.py#test_delete_form_icon_and_slot_hooks"
        status: pass
      - kind: integration
        ref: "tests/test1/test_crispy_buttons.py#test_form_instances_do_not_share_icons_or_language"
        status: pass
      - kind: integration
        ref: "tests/test1/test_form_buttons_golden.py#test_form_button_baselines"
        status: pass
    human_judgment: false
  - id: D7
    description: "The filter-submit and filter-reset kind icons work on the layout path, but the stock filter helper still adds its buttons as legacy helper inputs until 06-05. Visible FORM-10 on the real filter form is not yet observable"
    requirement: FORM-10
    verification: []
    human_judgment: true
    rationale: "06-05 moves the filter buttons to layout controls; the filter page in both/icon mode must be checked after that plan (and in the 06-09 browser pass)"

duration: 12min
completed: 2026-10-28
status: complete
---

# Phase 06 Plan 04: Accessible form modes and semantic icons Summary

**In `both` and `icon` modes, crispy layout form buttons now show their kind's semantic icon: submit `save`, delete `delete`, cancel `cancel`, filter-submit `filter`, filter-reset `filter-reset`. The kind comes from the slot, never the submitted name. A new `icon=` keyword (sentinel default) overrides it, and an explicit None/"" means no icon. `CrispyFormMixin.submit_icon`, `CrispyDeleteForm.delete_icon` and `WorkflowForm.submit_icon = "workflow"` supply the per-form icons. The new `save`, `cancel` and `filter-reset` names are registered in both the Font Awesome and Bootstrap registries, and inline and host libraries are covered by real renders.**

## Performance

- **Duration:** 12 min
- **Started:** 2026-10-28T06:52:09Z
- **Completed:** 2026-10-28T07:04:48Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments

- **Registries.** `DEFAULT_ICONS` gains `save` `far:floppy-disk`, `cancel` `fas:xmark` and `filter-reset` `fas:rotate-left`. `BOOTSTRAP_ICONS` gains `bi:floppy`, `bi:x-lg` and `bi:arrow-counterclockwise`, so the preset still covers exactly the default names.
- **Leaf coverage.** Real renders cover icon, both and label modes for all five kinds. They cover Font Awesome, the Bootstrap preset, raw classes and a dotted-path custom renderer. Host icons render as a class on the button with no inline element, a None/"" host slot opts out, and host and hidden-label classes are escaped. Unicode, lazy and empty labels keep their exact text. Repeated renders under changing registries leave the shared defaults unchanged. The utility keys reject mode suffixes with W362.
- **Adapters.** `Submit`/`Button`/`Reset` take `icon=`. If omitted, the icon comes from `_KIND_ICONS[kind]`, where the kind is read from the slot. If explicitly None or "", it is passed through as no icon, which is where 06-06's missing-icon policy will apply. `icon=` is consumed before crispy sees the kwargs, so it is never an HTML attribute on either the layout or the legacy input path.
- **Forms.** `get_submit_button` builds `{"icon": self.submit_icon, **get_submit_button_kwargs()}`. `get_delete_button` builds `{"slot": "form:delete", "icon": self.delete_icon, **get_delete_button_kwargs()}`. Hook kwargs therefore win over the form attribute, which wins over the kind default. `WorkflowForm.submit_icon = "workflow"`, and a subclass value wins.
- **Endpoints.** Under the form floor `both`/`icon`, the create, update, delete and workflow pages render the right icons. Name, value, type, id and cancel URL are unchanged. The label-mode goldens and the label floor stay icon-free.

## Task Commits

1. **Task 1 (tracer): Render inline and host icons with accessible labels.** RED `96f5800` (test), GREEN `0bac48e` (feat). Tracer gate (interactive, end-of-phase, automated-only verify): re-ran the Task 1 verify after GREEN (174 passed), then expanded to Task 2.
2. **Task 2: Wire semantic defaults and form-specific workflow overrides.** RED `ffe96ba` (test), GREEN `0960031` (feat).

**Plan metadata:** recorded in the docs commit for this plan.

## Files Created/Modified

- `src/crud_views/lib/icons.py`: three new names in both registries
- `src/crud_views/lib/crispy/buttons.py`: `_KIND_ICONS`, the `_KIND_ICON` sentinel, the `icon=` keyword and `cv_icon` in the raw button context
- `src/crud_views/lib/crispy/form.py`: `submit_icon`, `delete_icon` and the hook merge order
- `src/crud_views_workflow/lib/forms.py`: `submit_icon = "workflow"`
- `tests/test1/test_icon_host_leaves.py`, `tests/test1/test_icons_registry.py`, `tests/test1/test_crispy_buttons.py`: the regressions listed under coverage

## Decisions Made

See `key-decisions` in the frontmatter.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] 06-02 stub-era test expectations updated**
- **Found during:** Task 2
- **Issue:** `test_hostile_literals_never_create_nodes_or_attributes` and `test_form_floor_selects_the_body` compared `button.text_content()` with the label. That was only true while layout buttons had no icon (the 06-02 stub). Both mode now renders `<i …></i> <span>label</span>`.
- **Fix:** Both tests now compare the label span text. The floor test also asserts the submit icon in both/icon mode and none in label mode.
- **Files modified:** `tests/test1/test_crispy_buttons.py`
- **Commit:** `0960031`

**2. [Scope note] Registry assertions placed in `tests/test1/test_icons_registry.py`**
- **Found during:** Task 1
- **Issue:** Task 1's `<files>` list names only `test_icon_host_leaves.py`, but its verify runs `test_icons_registry.py`, where the default-value tests (`MESSAGE_ICONS`) already live.
- **Fix:** Added `FORM_ICONS` default-value tests there, plus a filter-reset vs filter-close distinctness check.
- **Commit:** `96f5800`

### Process notes

- **Lint fixes in GREEN.** The Task 1 RED commit went in with three ruff findings in the new tests: two SIM300 and one line over 120 characters. A `;` in my command chain let the commit run after `ruff check` failed. They were fixed in the GREEN commit `0bac48e`.
- **Workflow form change restored.** A mutation cleanup ran `git checkout` on the then-uncommitted `src/crud_views_workflow/lib/forms.py`, which reverted it. I re-applied the change and re-ran the full suite before committing `0960031`.
- **Mutation checks.** Each of these was applied in place, confirmed to fail, then restored:
  - unescaped host class: 1 failure
  - unconditional inline icon: 10 failures
  - hook kwargs losing to `submit_icon`: 1 failure
  - None falling back to the kind default: 12 failures
  - no workflow default: 3 failures

**Total deviations:** 1 auto-fixed (Rule 1 test-expectation update) plus 1 file-placement note. No scope change.

## Issues Encountered

- The `client_user_*` fixtures share one Django `Client`, so a test that requests several fixtures logs in only as the last user and gets 403s. The affected endpoint tests are parametrized one page per test.
- The pre-existing JS failure (`tests/js/list.filter.test.js:159`, jsdom 30.1.2) is unrelated and owned by 06-07. This plan changed no JS.

## Known Stubs

- Missing-icon policy: an icon-mode form button with an explicitly None/empty or unavailable icon currently renders hidden text only. There is no strict `ValueError` and no logged label fallback yet. 06-06 owns the availability predicate and the runtime policy. Recorded in `.planning/WINDOWS.md`. WINDOWS #7, the "no icon from layout adapters" stub from 06-02, is marked fixed.
- The stock filter helper still adds its buttons with `add_input` (legacy inputs), so their kind icons appear only after 06-05 moves them to layout controls (coverage D7).

## Threat Flags

None. T-06-07 is mitigated by `test_form_host_classes_are_escaped_attributes` (escaped host and hidden-label classes, no injected attributes or nodes) and the host no-duplicate-inline tests. T-06-08 is mitigated by `test_delete_form_icon_and_slot_hooks` and `test_kind_icon_follows_the_slot_not_the_name`, where slot and name mismatches keep the request name and value. No dependency was installed (T-06-SC).

## User Setup Required

None. No external service configuration required.

## Next Phase Readiness

- 06-05 can move the filter buttons to `FormActions(Submit(..., slot="form:filter-submit"), Reset(...))`. The `filter` and `filter-reset` icons then apply with no further change.
- 06-06 can put the availability predicate and the strict/log missing-icon policy in `_form_button_data`. Explicit None/"" icons already arrive there as `cv_icon` None. W292 static reach can read `submit_icon`/`delete_icon` from the package classes.
- 06-08 documents `save`/`cancel`/`filter-reset` in `icons.md` (distinct from `filter-close`), `icon=`, `submit_icon` and `delete_icon`.
- Verification: the plan's Task 1 shard (174 passed) and Task 2 shard (333 passed), the golden, leaf and import-safety shard (215 passed) and the full `pytest tests -n auto` (4122 passed) all pass, and ruff is clean.

## Self-Check: PASSED

- Modified key files exist: `icons.py`, `crispy/buttons.py`, `crispy/form.py`, `crud_views_workflow/lib/forms.py` and the three test files.
- Commits `96f5800`, `0bac48e`, `ffe96ba`, `0960031` are ancestors of HEAD. Measured `git rev-list --count 3bb016d..HEAD` = 4, and `check evaluation-scope --plan 06-04 --commits-only` resolves them.

---
*Phase: 06-form-button-leaf*
*Completed: 2026-10-28*
