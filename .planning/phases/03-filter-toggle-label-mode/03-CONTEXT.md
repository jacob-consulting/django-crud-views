# Phase 3: Filter toggle label mode - Context

**Gathered:** 2026-10-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Make the list filter toggle honor the configured context label mode while retaining its existing collapse and
state-persistence behavior (source plan 1B, #262; FILT-01 through FILT-04). Cover icon, both, and label modes,
element and host icon placement, mixed placements, and translation of the default label.

This discussion records the maintainer decisions for the short design clarification requested by the roadmap.
No separate SPEC.md was supplied. Form-button rendering, other adapter changes, and downstream theme edits
remain outside this phase.

</domain>

<decisions>
## Implementation Decisions

### Default inheritance
- **D-01:** The filter toggle has no target view. Do not use the current list view's singular
  `cv_context_action_label_mode` as a target default. Resolve through the existing context chain without a
  target-default argument: the view's own per-key map, button override, resolved ViewSet/settings map,
  then the context floor. Preserve existing whole-map replacement semantics.
- **D-02:** Resolve using the button's declared key, not a hard-coded `filter` key.
  `FilterContextButton(key="search")` uses the `search` entry; the default instance still uses `filter`.
  Use the existing `cv_get_action_label_mode()` resolver and preserve its precedence.

### Icon placement and modes
- **D-03:** In `both` mode retain the existing placement rule. When both open/close icons provide usable host
  classes, place the active classes on the button and swap them on toggle. Otherwise render child icons
  and switch their visibility. Mixed placements use child icons, including the existing standalone rendering
  of a host-configured icon. Do not introduce a rule that always forces child icons in `both` mode.
- **D-04:** The visible label stays constant while toggling; only the icon and expanded state change.
  This applies to custom labels as well as the default `Filter` label.
- **D-05 (carried from requirements):** `icon` retains the current hidden accessible label, title, tooltip,
  and icon behavior. With default configuration its markup remains byte-identical to the existing
  `toolbar_publisher_list.html` golden. `both` shows icon plus visible label without a title; follow the
  existing action-button convention of no tooltip marker when a visible label is present.
- **D-06 (carried from source plan):** `label` renders visible text without icon spans, host icon classes,
  or open/close icon data attributes. It still toggles the panel, updates `aria-expanded`, and persists state.
  Preserve the existing failure behavior: a collapse adapter that throws or returns false changes no state;
  a failed persistence request does not undo a successful toggle.

### Customization and documentation
- **D-07:** Preserve existing label templates, variants, and whole-button template overrides. Custom templates
  receive resolved `cv_label_mode` and control their own markup. No new precedence or customization API is needed.
- **D-08:** Add a compact contract with examples, not a full custom-template walkthrough. Show filter mode
  configuration, explain the absence of a target-view default, and document all three modes and optional icon
  hooks. Link to the canonical resolution order instead of duplicating it. Correct documentation that currently
  describes the bundled filter toggle as icon-only by construction.
- **D-09 (carried from requirements):** Translate the default `Filter` msgid and update the German catalog.
  Existing custom label templates continue to override the default label.

### Carried-forward constraints
- **D-10:** Keep no-filter and pinned-filter visibility behavior, DOM IDs, collapse integration, persistence,
  and reset behavior unchanged. This phase changes label-mode support, not filtering semantics.
- **D-11:** Record the public behavior change in CHANGELOG.md. Any Breaking entry also requires a matching
  update in docs/migrating-1.0.md. Preserve the project quality gates and unchanged default goldens.

### Agent's Discretion
- No product choice was explicitly delegated. Exact helper placement, test organization, template whitespace
  management, and documentation wording remain implementation details within these decisions.
- Verify whether JavaScript needs a functional change: its current icon loop already tolerates no matches.
  Add meaningful regression coverage without requiring a needless rewrite.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Scope and prior decisions
- `.planning/ROADMAP.md` — Phase 3 boundary, design questions, and success criteria.
- `.planning/REQUIREMENTS.md` — FILT-01 through FILT-04 and default-golden compatibility.
- `.planning/PROJECT.md` — stable public names, scope, documentation rules, and quality gates.
- `.planning/phases/01-label-mode-defaults/01-CONTEXT.md` — lazy floors, precedence, validation policy,
  and canonical documentation locations.
- `.planning/phases/02-form-key-grammar/02-CONTEXT.md` — context keys retain variant/mode grammar;
  form rendering remains Phase 6.
- `superpowers/plans/2026-10-24-concept-review-followups.md` — Phase 1B and global constraints.
- `superpowers/notes/2026-10-24-icons-buttons-theme-concept-review.md` — origin of the filter-toggle inconsistency.

### Public contracts and documentation
- `docs/reference/context_buttons.md` — custom labels, button overrides, and existing icon-only filter wording.
- `docs/reference/action_menus.md` — canonical context label-mode resolution order.
- `docs/reference/buttons.md` — class-table mode lookup and button leaf conventions.
- `docs/reference/javascript.md` — filter toggle DOM contract, optional icon hooks, and collapse failure semantics.
- `docs/reference/icons.md` — host placement and standalone icon rendering.
- `CHANGELOG.md` — public behavior change record.
- `docs/migrating-1.0.md` — companion update if a change is classified as Breaking.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/crud_views/lib/view/base.py`: `cv_get_action_label_mode()` already accepts a button and optional target
  default and implements the required context precedence and lazy floor fallback.
- `src/crud_views/lib/view/buttons.py`: `FilterContextButton.get_context()` seeds filter data and applies existing
  label, variant, and template hooks. It currently seeds an untranslated label and does not itself stamp a mode.
- `src/crud_views/templates/crud_views/tags/button/action.html`: established three-way label body and title/tooltip
  conventions; use as a reference while preserving the filter toggle's specialized contract.
- `src/crud_views/lib/icons.py`: host-class resolution and standalone rendering already support mixed placement.
- `src/crud_views/templatetags/crud_views.py`: `cv_icon_class`, `cv_icon`, and `cv_button_class` provide the existing
  icon and class-table seams.

### Established Patterns
- The filter template uses host classes only when both open and close resolve to usable classes; otherwise it
  renders two child spans. Preserve this behavior in both icon-bearing modes.
- Mode-specific button classes use the existing context variant and mode lookup. The current filter template
  hard-codes icon mode; the resolved mode needs to reach that lookup as well as the label body.
- Existing context label templates override the seeded label; whole-button templates own their rendering.

### Integration Points
- `src/crud_views/templates/crud_views/tags/context_action_filter.html`: mode branches, icon hooks, visible/hidden
  label, title/tooltip behavior, and byte-identical default output.
- `src/crud_views/static/crud_views/js/list.filter.js`: preserves state, host swaps, and child visibility;
  its empty `querySelectorAll()` loop is already harmless when no icons exist.
- `tests/js/list.filter.test.js`: existing host, element, persistence, reset, and adapter-failure tests;
  extend for label-only and constant visible-label behavior.
- `tests/test1/test_context_button_label_mode.py`, `tests/test1/test_context_action_label_mode.py`,
  and `tests/test1/test_filter_pinned.py`: existing resolution and visibility coverage to reuse.
- `tests/test1/golden/`: preserve the existing `toolbar_publisher_list.html` baseline.
- `src/crud_views/locale/de/LC_MESSAGES/django.po`: German translation of the default label.

</code_context>

<specifics>
## Specific Ideas

- `CRUD_VIEWS_CONTEXT_ACTIONS_LABEL_MODE = {"filter": "both"}` shows icon plus constant visible `Filter` text.
- `FilterContextButton(key="search")` follows the `search` mode entry and has no target-view default.
- Cover both initially expanded and collapsed states across label modes and icon placements; retain the
  accessible label and state contract while checking the default golden remains unchanged.

</specifics>

<deferred>
## Deferred Ideas

None added. Always using child icons in both mode and a full custom-template walkthrough were rejected,
not deferred. Downstream theme implementation remains outside this repository; record any follow-up in acceptance.

</deferred>

---

*Phase: 03-filter-toggle-label-mode*
*Context gathered: 2026-10-26*
