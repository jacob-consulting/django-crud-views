---
status: testing
phase: 03-filter-toggle-label-mode
source: [03-VERIFICATION.md]
started: 2026-10-26T16:26:03Z
updated: 2026-10-26T16:26:03Z
---

## Current Test

number: 1
name: Compact filter contract matches decisions D-01..D-10
expected: |
  docs/reference/context_buttons.md#the-filter-toggle links one canonical resolution order (action_menus.md#context-label-mode-resolution) with no second precedence list; examples use the real import `from crud_views.lib.view.buttons import FilterContextButton`; "no target view, so no target-view default" is stated; the never-folded rule is present.
awaiting: user response

## Tests

### 1. Compact filter contract matches decisions D-01..D-10
expected: One canonical resolution order linked (not restated); real import in examples; no target-view default stated; never-folded rule present.
result: [pending]

### 2. Optional-icon prose (javascript.md, icons.md) matches the test fixtures
expected: Host form only when both open/close resolve to usable host classes; mixed or switched-off pairs render two element spans in icon/both; label mode has no spans, host classes or data-cv-filter-icon-* attributes; tooltip marker only in icon mode; labels are never icon hooks.
result: [pending]

### 3. CHANGELOG Fixed entry and both migration entry points match real behavior
expected: Fixed (not Breaking); default output unchanged; context-floor impact named; both migration locations say copied templates must branch on cv_label_mode and that icons are optional. Decide on review IN-02 (the Fixed sentence reads as if FilterContextButton(label_mode="label") selects "icon").
result: [pending]

### 4. Browser check of icon / both / label modes
expected: both = funnel icon + visible "Filter", no tooltip, icon swaps when open, text constant; label = text-only, panel opens/closes, state survives reload; default identical to before (icon-only, title tooltip); German renders "Filter". Note whether label-only needs a visual open/closed cue (UI review warning 1).
result: [pending]

## Summary

total: 4
passed: 0
issues: 0
pending: 4
skipped: 0
blocked: 0

## Gaps
