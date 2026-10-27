---
status: testing
phase: 05-table-pagination-parity
source: [05-VERIFICATION.md]
started: 2026-10-27T14:30:00Z
updated: 2026-10-27T14:30:00Z
---

## Current Test

number: 1
name: Visual and assistive-technology parity of table and card pagination in a browser
expected: |
  In the example app, a paginated table list and a paginated card list look the same on the first, a middle and the
  last page: chevron icons with no visible label text, the same pill styling, the active page shown as a non-link,
  the unavailable direction greyed out and not focusable, and the table's `...` items greyed out like disabled ends.
  Tabbing skips disabled items. A screen reader announces the nav as "pagination" and the arrows as "previous" /
  "next".
awaiting: user response

## Tests

### 1. Visual and assistive-technology parity of table and card pagination in a browser
expected: Table and card pagination are visually identical on first/middle/last pages (chevrons, no visible label text, same pill styling, non-link active page, greyed non-focusable disabled end, disabled `...` items on the table); the nav is announced as "pagination" and the arrows as "previous"/"next".
result: [pending]

### 2. Maintainer read of the new documentation prose
expected: The CHANGELOG Breaking entry, `docs/migrating-1.0.md` "Table pagination overrides", `docs/reference/list_view.md` "Pagination", and the shared-key mentions in `buttons.md`, `icons.md` and `card-list-view.md` are accurate against the shipped templates and clear for a theme author.
result: [pending]

## Summary

total: 2
passed: 0
issues: 0
pending: 2
skipped: 0
blocked: 0

## Gaps
