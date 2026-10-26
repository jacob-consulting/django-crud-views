---
phase: 03-filter-toggle-label-mode
plan: "01"
subsystem: ui
tags: [django, templates, label-mode, filter-toggle, i18n, gettext, vitest, pytest]

requires:
  - phase: 01-label-mode-defaults
    provides: cv_get_action_label_mode() context precedence and the lazy default_label_mode("context") floor
provides:
  - FilterContextButton.get_context() stamps cv_label_mode for its declared key (no target default)
  - context_action_filter.html renders icon (unchanged bytes), both and label bodies with mode-specific classes
  - Default "Filter" label translated through gettext at get_context time, plus a German PO/MO entry
  - Raw byte baseline, full mode x state x placement matrix, resolution/customization/policy and JS regression tests
affects: [03-02-docs-and-release-notes, downstream themes overriding context_action_filter.html]

actuals:
  tokens: 13839
  tasks: 3
  commits: 8
plan_head_before: 3a51f817530d90b29ac67c965a230a7d8c132f21
plan_head_after: 367a8fdcdfc06b3d6707031f9664119fb27ea73b

tech-stack:
  added: []
  patterns:
    - "Specialized leaf branches: explicit both/label branches, legacy icon branch as fallback for absent/None/empty/unknown modes, with literal 'icon' passed to cv_button_class"
    - "Raw render_to_string byte baseline captured before production edits, separate from the normalized golden"
    - "Filter-specific DOM selectors: visible label = ./span[not(@class) and not(@data-cv-filter-icon)]"

key-files:
  created:
    - tests/test1/test_filter_toggle_label_mode.py
  modified:
    - src/crud_views/lib/view/buttons.py
    - src/crud_views/templates/crud_views/tags/context_action_filter.html
    - src/crud_views/locale/de/LC_MESSAGES/django.po
    - src/crud_views/locale/de/LC_MESSAGES/django.mo
    - tests/test1/test_i18n.py
    - tests/test1/test_button_leaves.py
    - tests/test1/test_context_action_label_mode.py
    - tests/js/list.filter.test.js

key-decisions:
  - "Filter toggle resolves cv_get_action_label_mode('context', self.key, self) with no target default: own view map > button label_mode > first view/ViewSet/settings map > live context floor"
  - "Leaf fallback for absent/None/empty/unknown cv_label_mode is the legacy icon body with literal icon classes; no runtime normalizer for malformed map/button values (E210/E211/E106/ValidationError remain the diagnostics)"
  - "Both mode puts a literal space before the visible label span, with no title or tooltip marker; label mode skips cv_icon_class lookups, icon spans and host swap hooks entirely"
  - "list.filter.js stays unchanged: its empty icon loop, collapse-first ordering and non-rollback persistence already cover label-only markup"

patterns-established:
  - "Mode-aware specialized leaf: wrap new conditionals around existing whitespace so the default branch keeps exact bytes"
  - "Translation evidence split into PO/MO membership, a gettext sentinel, and an active-language render"

requirements-completed: [FILT-01, FILT-02, FILT-03, FILT-04]

coverage:
  - id: D1
    description: "Configured context label modes (icon/both/label) reach the filter toggle through its declared key, with no target-view default and existing whole-map replacement"
    requirement: FILT-01
    verification:
      - kind: integration
        ref: "tests/test1/test_filter_toggle_label_mode.py#test_filter_both_tracer"
        status: pass
      - kind: integration
        ref: "tests/test1/test_filter_toggle_label_mode.py#test_filter_mode_resolution"
        status: pass
      - kind: integration
        ref: "tests/test1/test_filter_toggle_label_mode.py#test_filter_declared_key_and_direct_button"
        status: pass
      - kind: integration
        ref: "tests/test1/test_filter_toggle_label_mode.py#test_filter_live_floor"
        status: pass
      - kind: integration
        ref: "tests/test1/test_filter_toggle_label_mode.py#test_filter_ignores_list_singular_default"
        status: pass
    human_judgment: false
  - id: D2
    description: "Default icon output stays byte-identical (raw baseline for both states, mode-less and explicit icon) and the toolbar golden is unchanged"
    requirement: FILT-01
    verification:
      - kind: unit
        ref: "tests/test1/test_filter_toggle_label_mode.py#test_filter_raw_default_bytes"
        status: pass
      - kind: integration
        ref: "tests/test1/test_action_menus_golden.py#test_toolbar_list_with_filter"
        status: pass
      - kind: unit
        ref: "tests/test1/test_filter_toggle_label_mode.py#test_filter_direct_mode_fallback"
        status: pass
    human_judgment: false
  - id: D3
    description: "All 24 mode x expansion x placement combinations plus empty/None icon-host fallback render the right icon, label, class and ARIA contract; label mode has no icon hooks"
    requirement: FILT-02
    verification:
      - kind: unit
        ref: "tests/test1/test_filter_toggle_label_mode.py#test_filter_mode_placement_matrix"
        status: pass
      - kind: unit
        ref: "tests/test1/test_filter_toggle_label_mode.py#test_filter_host_slot_fallback"
        status: pass
      - kind: unit
        ref: "tests/js/list.filter.test.js#a label-mode toggle with element icons (#262)"
        status: pass
    human_judgment: false
  - id: D4
    description: "Visible default and custom labels stay constant across toggles, failures and out-of-order persistence; custom label/whole-button templates and variants keep working and see the resolved mode"
    requirement: FILT-03
    verification:
      - kind: unit
        ref: "tests/js/list.filter.test.js#keeps the label %j over two clicks (starts expanded: %s)"
        status: pass
      - kind: unit
        ref: "tests/js/list.filter.test.js#never rolls back the latest state when persistence settles out of order"
        status: pass
      - kind: integration
        ref: "tests/test1/test_filter_toggle_label_mode.py#test_filter_custom_label"
        status: pass
      - kind: integration
        ref: "tests/test1/test_filter_toggle_label_mode.py#test_filter_whole_button_template"
        status: pass
      - kind: integration
        ref: "tests/test1/test_filter_toggle_label_mode.py#test_filter_customization"
        status: pass
      - kind: unit
        ref: "tests/test1/test_filter_toggle_label_mode.py#test_filter_label_escaping"
        status: pass
    human_judgment: false
  - id: D5
    description: "Translated default Filter label: German PO/MO entry, runtime gettext per call, German render with custom-label precedence"
    requirement: FILT-04
    verification:
      - kind: unit
        ref: "tests/test1/test_i18n.py#test_filter_catalog_entry"
        status: pass
      - kind: unit
        ref: "tests/test1/test_i18n.py#test_filter_gettext_at_render_time"
        status: pass
      - kind: integration
        ref: "tests/test1/test_i18n.py#test_filter_german_render"
        status: pass
      - kind: other
        ref: "msgfmt --check --check-format -o /dev/null src/crud_views/locale/de/LC_MESSAGES/django.po"
        status: pass
    human_judgment: false
  - id: D6
    description: "No-filter and pinned-filter pages still render no toggle and resolve no mode; malformed configuration keeps its existing diagnostics and invalid-floor policy"
    verification:
      - kind: integration
        ref: "tests/test1/test_filter_toggle_label_mode.py#test_filter_visibility"
        status: pass
      - kind: integration
        ref: "tests/test1/test_filter_toggle_label_mode.py#test_filter_invalid_configuration_policy"
        status: pass
      - kind: integration
        ref: "tests/test1/test_filter_pinned.py"
        status: pass
    human_judgment: false

duration: 15min
completed: 2026-10-26
status: complete
---

# Phase 3 Plan 01: Filter Toggle Label Mode Summary

**The list filter toggle now resolves the context label mode of its declared key and renders icon (pre-change bytes kept), both (icons plus spaced visible label) or label (no icon hooks), with a render-time translated, German-cataloged "Filter" default.**

## Performance

- **Duration:** 15 min
- **Started:** 2026-10-26T15:33:35Z
- **Completed:** 2026-10-26T15:48:16Z
- **Tasks:** 3
- **Files modified:** 9

## Accomplishments
- `FilterContextButton.get_context()` stamps `cv_label_mode` from `context.view.cv_get_action_label_mode("context", self.key, self)` before the label/variant/template hooks, and seeds `cv_action_label` with `_("Filter")` (gettext) on each call. Both early `cv_access=False` returns are kept.
- `context_action_filter.html` has explicit `both` and `label` branches that pass `cv_label_mode` to `cv_button_class`. Absent, None, empty or unknown modes fall back to the legacy icon branch, which gets the literal `icon`. In icon-bearing modes the host-versus-child placement rule is unchanged. Label mode skips the `cv_icon_class` lookups, icon spans and `data-cv-filter-icon-open/close` hooks.
- Raw `render_to_string` baselines for both expansion states were captured at source HEAD `3a51f81` and committed in `cf17af2` before any production edit. They still match byte for byte, with and without an explicit icon mode, and `toolbar_publisher_list.html` is unchanged.
- Coverage: 88 Python cases in the new module, 3 i18n tests (5 cases), 22 new JS cases. They run against the unchanged `list.filter.js`, and mutation checks confirmed they catch rollback, label re-rendering and ARIA set before collapse.

## Task Commits

1. **Task 1: Render and toggle one configured both-mode filter end to end** (tracer)
   - `cf17af2` test: raw default baseline (before production edits)
   - `62b5862` test: failing both-mode tracer (RED)
   - `4036e97` feat: both mode, stamped mode, gettext seed, JS both case (GREEN)
2. **Task 2: Expand all modes, customizations and disclosure failure cases**
   - `2d0fd09` test: failing matrix, resolution, customization and policy tests (RED)
   - `00e6d48` feat: label-only branch and ELIGIBLE comment (GREEN)
   - `3f1d04c` test: JS label-only / constant-label coverage of the unchanged handler
3. **Task 3: Ship and prove the translated default Filter label**
   - `d085903` test: failing catalog checks (RED)
   - `367a8fd` feat: German PO entry and recompiled MO (GREEN)

**Plan metadata:** see the docs(03-01) commit that adds this file

## TDD Gate Compliance

| Task | RED | GREEN | RED evidence (classifier) | Semantic assessment |
|------|-----|-------|---------------------------|---------------------|
| 03-01-01 | 62b5862 | 4036e97 | `RED_EVIDENCE_OK` (JUnit, target `test_filter_both_tracer`) | The target ran and failed on `assert ctx.get("cv_label_mode") == "both"` (None): the planned behavior was missing. No setup or collection fault. |
| 03-01-02 | 2d0fd09 | 00e6d48 | `RED_EVIDENCE_OK` (JUnit, target `test_filter_mode_placement_matrix[label-False-element]`) | Failed on `assert [] == ['Filter']`: label mode rendered the legacy icon body. All 22 failures in the module came from label mode (checked in the detailed output). |
| 03-01-03 | d085903 | 367a8fd | `RED_EVIDENCE_OK` (JUnit, target `test_filter_catalog_entry`) | Failed on `msgid 'Filter' missing from the core German catalog`. |

Notes:
- The baseline commit `cf17af2` is a passing `test(...)` commit by design, because it protects the pre-change bytes.
- The JS tests (`3f1d04c`, and the both case in `4036e97`) cover the unchanged production handler, so they could not go RED. To show they are not vacuous, three handler mutants were run and then reverted: rollback on rejection (4 failures), re-rendering the label node (17 failures) and setting ARIA before collapse (7 failures).
- `test_filter_gettext_at_render_time` passed before the catalog edit. The plan puts the render-time call in Task 1, so Task 3's RED is the catalog test.

## Files Created/Modified
- `src/crud_views/lib/view/buttons.py` - gettext import; stamps `cv_label_mode`; translated `Filter` seed
- `src/crud_views/templates/crud_views/tags/context_action_filter.html` - both/label branches around the existing whitespace
- `src/crud_views/locale/de/LC_MESSAGES/django.po` / `django.mo` - `Filter` → `Filter` entry (`lib/view/buttons.py:330`); MO recompiled with `msgfmt --check-format`
- `tests/test1/test_filter_toggle_label_mode.py` - new: raw baseline, tracer, matrix, resolution, customization, visibility, escaping, fallback, policy
- `tests/test1/test_i18n.py` - `test_filter_catalog_entry`, `test_filter_gettext_at_render_time`, `test_filter_german_render`
- `tests/test1/test_button_leaves.py` - `_filter_toggle(mode=None)` keeps the mode-less path; explicit-icon host case
- `tests/test1/test_context_action_label_mode.py` - ELIGIBLE comment now points to the dedicated filter coverage
- `tests/js/list.filter.test.js` - `modeFixture` (label / both-element / both-host) plus interaction, failure, order and out-of-order cases

## Decisions Made
- Followed the plan's `gettext` (not the `gettext_lazy` that PATTERNS.md mentions), so translation happens on each `get_context` call and Task 3 can patch it as `buttons._`.
- The generic wrapper still resolves a second time and still evaluates `cv_access=False` contexts (A11). The two resolutions agree because the filter context has no `cv_context_label_mode`.
- A1 limitation, recorded and not a promise: a malformed map or button value that still reaches rendering comes back raw from the resolver (for example `"text"`), and the stock leaf renders its legacy icon form. Diagnostics stay `viewset.E210` (button), `viewset.E211` (view attribute), `crud_views.E106` (setting) and `pydantic.ValidationError` (ViewSet construction). An invalid floor still raises in strict mode and warns once with an icon fallback otherwise; a valid explicit mode skips the floor.

## Deviations from Plan

None - plan executed exactly as written. Additions within task scope:
- Extra tests beyond the named list: `test_filter_direct_context_mode_less_icon_class`, `test_filter_ignores_list_singular_default`, `test_filter_custom_label`, `test_filter_whole_button_template`, `test_filter_variant_mode_classes`.
- Task 2's JS coverage went into its own `test(03-01)` commit after the GREEN commit, because it covers unchanged production code.

**Total deviations:** 0 auto-fixed.
**Impact on plan:** None.

## Issues Encountered
- In `test_filter_visibility`, the `client_user_*` fixtures share Django's single `client`, so the last login won. The author page now gets its own `Client()`.
- The first version of the out-of-order JS test rejected the earliest request, so a rollback mutant landed on the same final state and passed. It now rejects the latest request first and resolves the earlier one late, which catches that mutant.
- Tooling drift (recorded, not fixed): `package.json` declares `vitest ^5.0.3` / `jsdom ^30.1.2` but 4.1.10 / 29.1.1 are installed. Ruff 0.16.10 differs from the manifest, as research noted. All gates still passed.

## Verification Evidence
- Task 1: `.venv/bin/pytest tests/test1/test_filter_toggle_label_mode.py tests/test1/test_action_menus_golden.py tests/test1/test_button_leaves.py -q` → 141 passed (also with `--random-order`); `npm --prefix . test -- tests/js/list.filter.test.js` → 36 passed
- Task 2: focused matrix command (8 modules) → 225 passed
- Task 3: `msgfmt --check --check-format -o /dev/null .../django.po` → OK; `.venv/bin/pytest tests/test1/test_i18n.py tests/test1/test_filter_toggle_label_mode.py tests/test1/test_context_button_template.py tests/test1/test_action_menus_golden.py -q` → 120 passed, 0 skipped
- Extra regression run: `.venv/bin/pytest tests -q -n auto` → 3456 passed, 1 skipped (pre-existing: Django 6.0-only CSP test); `npm --prefix . test` → 149 passed; `ruff check src tests` and `ruff format --check src tests` clean
- `git diff 3a51f81 -- tests/test1/golden/ src/crud_views/static/crud_views/js/list.filter.js` is empty
- Before the catalog edit, recompiling the unchanged PO reproduced the tracked MO byte for byte.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Ready for 03-02 (docs, CHANGELOG, full phase gates).
- Downstream-theme follow-up for 03-02: a theme that overrides `crud_views/tags/context_action_filter.html` still renders icon-only. To honor `both` and `label` it has to branch on the `cv_label_mode` its context now carries. The release notes and the copied-template checklist should say so, along with the floor impact: a non-icon `CRUD_VIEWS_LABEL_MODE_DEFAULTS["context"]` now changes the stock toggle.
- `docs/reference/context_buttons.md`, `buttons.md`, `action_menus.md` and `javascript.md` still describe the filter as icon-only. Correcting them is 03-02's job.

---
*Phase: 03-filter-toggle-label-mode*
*Completed: 2026-10-26*

## Self-Check: PASSED

All 7 key files exist on disk; all 8 task commits (`cf17af2`, `62b5862`, `4036e97`, `2d0fd09`, `00e6d48`, `3f1d04c`, `d085903`, `367a8fd`) are ancestors of HEAD; `check evaluation-scope --plan 03-01 --commits-only` resolved them; every task's acceptance criteria and the plan-level verification were re-run and pass.
