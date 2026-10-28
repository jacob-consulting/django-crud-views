---
phase: 06-form-button-leaf
plan: "02"
subsystem: ui
tags: [crispy-forms, form-button-leaf, label-mode, escaping, golden, tracer]

requires:
  - phase: 06-form-button-leaf
    provides: 06-SPEC.md form contract and the before-change goldens 2956f3e / 98b71ed (06-01)
provides:
  - "form" button location with lazy floor "label" (LOCATIONS, LABEL_MODE_DEFAULTS, E108)
  - FORM_LEAF_KEYS and the cv_button_data(ctx, "form") normalizer branch
  - crud_views/tags/button/form.html literal <button> leaf (label / both / icon bodies)
  - Submit / Button / Reset layout render through the leaf, with the view package imported at render time
  - cv_button rejects location "form" before resolution and dispatch
  - form:hidden-label and form:icon-host utility keys (table 71 -> 73)
  - four layout-control goldens updated to button markup
affects: [06-03, 06-04, 06-05, 06-06, 06-07, 06-08]

tech-stack:
  added: []
  patterns:
    - "Form normalizer input: cv_key, cv_type, cv_name, cv_value, optional cv_label, cv_id, cv_css_id, cv_css_class, cv_attrs, cv_label_mode, cv_icon"
    - "Literal boundary: _literal() -> exact plain str (str.__str__), escaped once by leaf autoescape; extras serialized once by django flatatt"
    - "Adapter render() never calls BaseInput.render; render_to_string(template, FORM_LEAF_KEYS dict) with no outer context"

key-files:
  created:
    - src/crud_views/templates/crud_views/tags/button/form.html
  modified:
    - src/crud_views/lib/view/button_data.py
    - src/crud_views/lib/view/label_mode.py
    - src/crud_views/lib/crispy/buttons.py
    - src/crud_views/lib/button_classes.py
    - src/crud_views/templatetags/crud_views.py
    - docs/reference/buttons.md
    - docs/reference/settings.md
    - tests/test1/test_crispy_buttons.py
    - tests/test1/test_button_data.py
    - tests/test1/test_label_mode.py
    - tests/test1/test_action_label_mode_config.py
    - tests/test1/test_label_mode_docs.py
    - tests/test1/test_button_classes.py
    - tests/test1/test_button_classes_templates.py
    - tests/test1/test_form_buttons_golden.py
    - tests/test1/golden/form_buttons/create.html
    - tests/test1/golden/form_buttons/update.html
    - tests/test1/golden/form_buttons/delete.html
    - tests/test1/golden/form_buttons/workflow.html

key-decisions:
  - "Form normalizer raw input keys are cv_key, cv_type, cv_name, cv_value, optional cv_label, cv_id (generated), cv_css_id, cv_css_class, cv_attrs (raw extra kwargs), cv_label_mode, cv_icon; reserved-attribute resolution lives in the normalizer so direct and adapter calls share it"
  - "cv_cancel_url is present for the cancel kind only and is None when no URL was supplied; the leaf emits data-cv-cancel-url only when it is not None"
  - "An icon-mode form button with an empty label renders no title and no data-cv-tooltip, matching the action leaf"
  - "The bundled default template is the literal crud_views/tags/button/form.html declared on the adapter mixin (not theme_path), so crispy's %s/layout/baseinput.html never wins on the layout path"
  - "Layout render rejects any slot other than form:<FORM_KINDS member> with ValueError; construction and legacy helper.inputs accept any slot"

patterns-established:
  - "Tracer gate in interactive end-of-phase mode: re-run both automated verifies after the tracer commit before expanding"
  - "Mutation sanity check for tests that pass on first run: break the behavior in place, confirm a failure, restore"

requirements-completed: [FORM-02, FORM-03, FORM-04, FORM-05, FORM-06, FORM-07]

actuals:
  tokens: 15963
  tasks: 3
  commits: 4
plan_head_before: b09de54e3c4bf6c78904b927bccbcb079e04b658
plan_head_after: 552c9e73312990b84e19c5fc6b27d607ebf322b0

duration: 17min
completed: 2026-10-28
status: complete
---

# Phase 06 Plan 02: Form-button leaf tracer Summary

**Crispy layout Submit/Button/Reset now render one literal, escaped `<button>` through `crud_views/tags/button/form.html`. This uses a separate `FORM_LEAF_KEYS` normalizer, the lazy `"form"` floor `"label"`, finite kind/type validation and render-time view imports. Default payload and classes are byte-for-byte compatible in meaning with the 06-01 baselines.**

## Performance

- **Duration:** 17 min
- **Started:** 2026-10-28T06:20:03Z
- **Completed:** 2026-10-28T06:37:00Z
- **Tasks:** 3
- **Files modified:** 20 (1 created, 19 modified)

## Accomplishments

- `cv_button_data(ctx, "form")` branches right after argument validation. It takes an omitted or explicit `kind="action"` and rejects `menu-item`, unknown values and semantic names such as `submit` in both strict modes. `cv_key` must be a `FORM_KINDS` member and `cv_type` must be submit/button/reset. Every text field becomes an exact plain `str`. It applies crispy's wordcount/slugify name rule, resolves reserved attributes once (hyphen spelling wins in either order; `css_id` > extra `id` > generated id; class table + `css_class` + extra `class`; cancel URL for cancel only; generated title/tooltip win in icon mode) and serializes the extras once with Django `flatatt`.
- The adapters keep their constructor and crispy-visible state. `render()` never calls `BaseInput.render`: no value is compiled as a template, and the context and adapter are not mutated. The selected template (explicit > subclass > bundled, `%s` = pack) gets only the normalized dict. `cv_button_data` is imported inside `render()`, and both unchanged bare-settings import subprocess tests pass.
- `{% cv_button "form" %}` raises `ValueError` naming `cv_button` and `'form'` before `cv_resolve_action`, normalization or leaf rendering. Context/list/card action, menu-item and hidden behavior is unchanged.
- `LOCATIONS`/`LABEL_MODE_DEFAULTS` gained `form`/`label`. The E108 locations, settings.md defaults and location prose, and the docs guard were updated in the same change. `form:hidden-label` and `form:icon-host` were added, with `EXPECTED_KEYS` at 73 and buttons.md count/rows/arithmetic checked (49 rows → 73 keys, five icon-host keys).
- The create/update/delete/workflow goldens now hold button markup. Parsed controls equal the baselines `2956f3e`/`98b71ed` in type, name, value, id, classes, cancel URL and text. `filter.html` is unchanged.

## Task Commits

1. **Task 1 (tracer): Render one real crispy Submit through the literal form leaf.** RED `aa81b4e` (test), GREEN `df2308b` (feat). Tracer gate: both automated verifies re-run after the GREEN commit (525 passed; 2 import-safety passed) before expanding.
2. **Task 2: Prove template precedence, safe attributes and repeatable rendering.** `9e19f9a` (test).
3. **Task 3: Update only the captured layout-button goldens.** `552c9e7` (test).

**Plan metadata:** recorded in the final docs commit for this plan.

## Golden comparison evidence

| Golden | Baseline commit | Parsed (type, name, value, id, class, cancel URL, text) | Structural change |
|---|---|---|---|
| create | `2956f3e` | equal (2 controls) | `<input>` → `<button>` + `<span>` label |
| update | `2956f3e` | equal (2 controls) | same |
| delete | `2956f3e` | equal (2 controls) | same |
| workflow | `98b71ed` | equal (2 controls) | same |
| filter | `98b71ed` | untouched (`git diff 98b71ed HEAD -- filter.html` empty) | none (06-05) |

Captured with a throwaway module that reused the unchanged `_page_controls`/`_golden_bytes` and was deleted before commit. Both baseline commits are ancestors of HEAD.

## Files Created/Modified

- `src/crud_views/templates/crud_views/tags/button/form.html`: the literal `<button>` leaf
- `src/crud_views/lib/view/button_data.py`: `"form"` location, `FORM_LEAF_KEYS`, `FORM_TYPES`, form normalizer
- `src/crud_views/lib/view/label_mode.py`: `"form": "label"` floor
- `src/crud_views/lib/crispy/buttons.py`: layout `render()` through the leaf; slot-kind check at render
- `src/crud_views/lib/button_classes.py`: `form:hidden-label`, `form:icon-host`
- `src/crud_views/templatetags/crud_views.py`: `cv_button` form guard
- `docs/reference/settings.md`, `docs/reference/buttons.md`: defaults, locations, key count and rows
- `tests/test1/*`: the shards listed under key-files, plus the four goldens

## Decisions Made

See `key-decisions` in the frontmatter.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Stale buttons.md statement about crispy form buttons**
- **Found during:** Task 1
- **Issue:** The Phase 2 paragraph after the form mode keys said crispy form buttons "continue using their existing `slot=` calls without choosing a mode, so their rendering is unchanged". After this plan that is false: layout buttons resolve the `"form"` floor and look up `form:<kind>:<mode>`.
- **Fix:** Rewrote that sentence to describe the layout and `add_input()` paths. Full form-map documentation stays with 06-08.
- **Files modified:** `docs/reference/buttons.md`
- **Commit:** `df2308b`

### TDD notes

- Task 2's new tests passed on first run, because the spec required Task 1's normalizer and adapter to implement these behaviors already. There was no RED/GREEN pair for that task. To show the tests can fail, I broke two behaviors in place and restored them before committing. Merging the outer context into the render data was caught. Removing the hyphen-wins rule was not caught at first, because every test listed the underscore alias first. I added reversed-order cases in `test_crispy_buttons.py` and `test_button_data.py`, after which the mutation failed 5 tests.
- Several first-run failures in Tasks 1 and 2 were wrong test expectations, all fixed in the tests: an expected dict missing `form`, the cancel URL on non-cancel kinds (the spec keeps it as an ordinary attribute), the FormActions wrapper around custom output, and the de catalog translating "Save" as "Sichern".

**Total deviations:** 1 auto-fixed (Rule 1, documentation correctness). No product scope change.

## Issues Encountered

- The pre-existing JS failure (`tests/js/list.filter.test.js:159`, jsdom 30.1.2) is unrelated to this plan and is owned by 06-07. No JS source changed; `viewset.js` binds cancel through the element-agnostic `[data-cv-cancel-url]`.

## Known Stubs

| File | Reason | Owner |
|---|---|---|
| `src/crud_views/lib/crispy/buttons.py` | Layout form buttons pass no `cv_icon` yet. With the default `"label"` floor nothing is missing, but a project that sets the form floor to `icon`/`both` gets no visible icon. Kind-default icons, the `icon=` hooks and the missing-icon policy are 06-04 scope (per plan: "keep normalizer/icon behavior extensible for 06-04"). | 06-04 (WINDOWS ledger entry appended) |

Owner-based mode resolution (`cv_form_actions_label_mode`, settings/ViewSet maps) is 06-03 scope. Today a layout button resolves only the `"form"` floor.

## Threat Flags

None. T-06-02, T-06-03 and T-06-04 are mitigated and covered by the real-crispy hostile-literal, no-template-evaluation and one-final-attribute regressions. No dependency was installed (T-06-SC).

## User Setup Required

None. No external service configuration required.

## Next Phase Readiness

- 06-03 can add owner recovery: the adapter's `render(form, context, ...)` receives the real form and context, and `_cv_button_context()` is the seam for passing a resolved `cv_label_mode`.
- 06-04 can pass `cv_icon` through the same seam. The normalizer already handles host/inline placement and label-mode suppression.
- Full suite: 3952 passed; import-safety module 18 passed; ruff clean.

## Self-Check: PASSED

- Created/modified key files exist: `form.html`, `button_data.py`, `crispy/buttons.py`, the four goldens.
- Commits `aa81b4e`, `df2308b`, `9e19f9a`, `552c9e7` are ancestors of HEAD; measured `git rev-list --count b09de54..HEAD` = 4.
- Verifies: Task 1 shard 525 passed and both import subprocess tests passed; Task 2 shard 503 passed; Task 3 shard 70 passed; full `pytest tests -n auto` 3952 passed.

---
*Phase: 06-form-button-leaf*
*Completed: 2026-10-28*
