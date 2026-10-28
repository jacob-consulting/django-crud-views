---
status: testing
phase: 06-form-button-leaf
source: [06-VERIFICATION.md]
started: 2026-10-28T10:56:51Z
updated: 2026-10-28T10:56:51Z
---

## Current Test

number: 1
name: Hover tooltips in icon mode
expected: |
  Run examples/bootstrap5 with CRUD_VIEWS label mode {"form": "icon"}; hover the save, cancel, delete and filter buttons with a real pointer. The label tooltip appears for each (the headless harness could not trigger :hover).
awaiting: user response

## Tests

### 1. Hover tooltips in icon mode
expected: Run examples/bootstrap5 with {"form": "icon"}; hovering save/cancel/delete/filter buttons with a real pointer shows the label tooltip.
result: [pending]

### 2. Visual quality of label/both/icon modes
expected: On create, delete and list-filter pages (including a custom filter layout holding package Submit/Reset), spacing and alignment are right, hidden labels do not clip, and the fallback label fits beside icon-only siblings.
result: [pending]

### 3. Screen-reader announcement
expected: Tabbing through the create form and filter panel in icon mode, buttons are announced by their hidden-span label; the modal delete flow and reset are announced.
result: [pending]

### 4. Migration-guide readability
expected: Reading docs/migrating-1.0.md "Form buttons" as a downstream maintainer, migration is possible without guessing (note: IN-02 sorted extra-attribute order is still unmentioned).
result: [pending]

## Summary

total: 4
passed: 0
issues: 0
pending: 4
skipped: 0
blocked: 0

## Gaps
