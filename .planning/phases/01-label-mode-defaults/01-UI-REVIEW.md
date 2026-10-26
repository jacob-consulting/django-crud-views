# Phase 01 — UI Review

**Audited:** 2026-10-26
**Baseline:** Abstract six-pillar standards, bounded by 01-CONTEXT.md's label-mode configuration contract; no UI-SPEC.md exists.
**Screenshots:** Not captured (localhost ports 3000, 5173 and 8080 each returned 000).
**Interaction captures:** off (workflow.ui_interaction_capture is false)
**Scope:** Code-derived rendering review, including the 01-05 request-instance correction. This phase introduces no frontend design, templates, CSS, or new screens. The configured frontend gate is false.

## Pillar Scores

| Pillar | Score | Key Finding |
|--------|-------|-------------|
| 1. Copywriting | 4/4 | Existing action labels survive all three modes; icon-only actions retain hidden full labels. |
| 2. Visuals | 4/4 (markup contract only) | Icon/text composition and accessible naming are explicit and covered by render assertions. Actual browser hierarchy is unassessed. |
| 3. Color | N/A | No color changes; palette balance and contrast cannot be established from this resolver-only phase. |
| 4. Typography | N/A | No font changes or typography contract; computed sizes and weights were not measured. |
| 5. Spacing | N/A | No spacing changes or breakpoint contract; configured labels' browser wrapping was not measured. |
| 6. Experience Design | 4/4 (rendering behavior only) | Request-local mode choices, explicit action precedence, disabled actions and accessible names remain represented in source and tests. |

**Overall: 12/12 applicable code-contract points; no /24 visual score.** Assigning passing or failing visual scores to unobserved design dimensions would imply evidence this audit does not have. These scores are not a claim that the package or consuming themes meet all six visual standards.

## Top 3 Priority Fixes

No supported implementation defect was found in the audited phase. There are no mandatory fixes to rank. The following are optional validation follow-ups, not confirmed UI failures:

1. Capture an actual consumer's configured text/both toolbar and card actions at 375, 768 and 1440 px when undertaking frontend validation; confirm labels wrap without hiding actions.
2. Exercise keyboard focus, tooltips and action activation in that consumer; this audit establishes HTML semantics, not browser interaction behavior.
3. Check external theme consumers of the changed card attribute against the migration guidance; use stamped `cv_label_mode` for effective per-action/request behavior and the public resolver for class defaults.

## Detailed Findings

### Pillar 1: Copywriting (4/4)

No in-scope copy defect found. `src/crud_views/lib/view/button_data.py:74` preserves card action labels, `:80` preserves full and short toolbar/list labels, and `:111` selects the visible short label only for labelled modes. Icon mode keeps the full label for the hidden text and title (`:142`). `src/crud_views/templates/crud_views/tags/button/action.html:8` emits the label in each branch. `tests/test1/test_button_leaves.py:508` explicitly checks the configured visible "Detail" versus unconfigured hidden "Details" contract. No new empty/error page copy is introduced by this change.

### Pillar 2: Visuals (4/4 for the markup contract)

No in-scope icon/text composition defect found. The shared action leaf (`src/crud_views/templates/crud_views/tags/button/action.html:7`) associates title/tooltip metadata with icon mode and includes hidden accessible text. Render assertions cover all three card states (`tests/test1/test_card_label_mode_render.py:82`), including decorative icon `aria-hidden`, visible text and hidden labels. The instance correction now reaches the actual rendered leaf (`:266`, `:288`). This is evidence for composition and naming only; screenshot-based focal point, visual hierarchy and legibility remain unverified.

### Pillar 3: Color (not applicable to the phase delta)

`git diff --stat ebc7c23 -- src/crud_views/templates tests/test1/golden examples` returned no changes. Color remains selected by the existing theme class table, not by the new default resolver: `src/crud_views/templates/crud_views/tags/button/action.html:2` calls `cv_button_class`; `src/crud_views/lib/button_classes.py:16`–`:27` defines four variant slots for each of three locations. Those twelve slot definitions are not twelve observed accent elements. No accent distribution, 60/30/10 ratio or contrast measurement is claimed. Mode-specific theme overrides remain supported at `button_classes.py:136`.

### Pillar 4: Typography (not applicable to the phase delta)

No new font sizes or weights are introduced by the label-mode implementation. The existing class table uses three button size variants (`btn-lg`, `btn-xs`, `btn-sm`, `src/crud_views/lib/button_classes.py:16`–`:27`), whose actual typography depends on the consuming CSS. Counting nonexistent Tailwind classes in a Django/Bootstrap package would not establish font consistency. Browser-computed typography remains unassessed.

### Pillar 5: Spacing (not applicable to the phase delta)

No spacing tokens changed. Existing action containers use `btn-group`, `btn-group-xs` and `d-flex gap-2` (`src/crud_views/lib/button_classes.py:28`–`:30`). These are source observations, not proof that newly visible labels fit all viewports. No measured overflow or clipping defect was observed because no screenshots were captured. A consumer-level responsive check is the appropriate follow-up if the project enables longer labels globally.

### Pillar 6: Experience Design (4/4 for rendering behavior)

No in-scope flow-breaking defect found. `src/crud_views/lib/views/card.py:49` resolves explicit action mode before legacy `no_label`, instance choice and the class resolver; instance `None` reads the configured floor. The same resolved value feeds child and ordinary actions (`:74`, `:92`). `tests/test1/test_card_label_mode_render.py:331` checks request isolation across setup/dispatch/queryset assignments; `:365` checks explicit None and live settings; `:408` checks subclass resolver hooks; `:440` checks child actions and permissions.

The unchanged leaf retains disabled state and submit/modal metadata (`src/crud_views/templates/crud_views/tags/button/action.html:3`–`:6`); render cases for disabled and POST actions exist at `tests/test1/test_card_label_mode_render.py:191` and `:207`. Invalid settings recover through a bounded fallback in non-strict mode (`src/crud_views/lib/view/label_mode.py:61`, `:84`). Empty action lists are covered at `tests/test1/test_card_label_mode_render.py:506`. Loading indicators and new destructive-action confirmation designs are outside this configuration phase. Keyboard navigation, focus appearance, tooltip behavior and browser activation were not captured or tested here.

## Validation and Limitations

- Fresh targeted verification: `.venv/bin/pytest tests/test1/test_card_label_modes.py tests/test1/test_card_label_mode_render.py tests/test1/test_button_leaves.py tests/test1/test_action_menus_golden.py -q` — **96 passed in 8.68s**. No golden regeneration enabled.
- Branch observed: `feat/label-mode-defaults`; no branch changes or commits performed.
- Source and render-test audit; no app setup or browser session started.
- No screenshots were attempted or created. Screenshot storage setup was therefore unnecessary for this run; the required ignore gate must run before any future capture. The audit assignment permits only this artifact, so no ignore/configuration files were changed.
- No project-local skills directories were found; configured `gsd-ui-auditor` skill query returned no skill entries.
- No `components.json` or UI-SPEC third-party registry contract was found; registry audit is not applicable.
- Plans 01–05, execution summaries and phase context informed the scope. Existing summary test results were treated as historical evidence, not new test executions.

## Files Audited

- `AGENTS.md`
- `.planning/phases/01-label-mode-defaults/01-CONTEXT.md`
- `.planning/phases/01-label-mode-defaults/01-{01,02,03,04,05}-PLAN.md`
- `.planning/phases/01-label-mode-defaults/01-{01,02,03,04,05}-SUMMARY.md`
- `src/crud_views/lib/view/label_mode.py`
- `src/crud_views/lib/view/button_data.py`
- `src/crud_views/lib/views/card.py`
- `src/crud_views/lib/button_classes.py`
- `src/crud_views/templates/crud_views/tags/button/action.html`
- `tests/test1/test_card_label_modes.py`
- `tests/test1/test_card_label_mode_render.py`
- `tests/test1/test_button_leaves.py`

## Recommendation Count

- Confirmed BLOCKER findings: 0
- Confirmed WARNING defects: 0
- Priority fixes: 0
- Optional validation recommendations: 3
