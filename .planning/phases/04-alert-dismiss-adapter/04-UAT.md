---
status: complete
phase: 04-alert-dismiss-adapter
source: [04-VERIFICATION.md]
started: 2026-10-26T20:58:57Z
updated: 2026-10-26T21:02:28.439Z
---

## Current Test

[testing complete]

## Tests

### 1. Example-project browser dismissal of three fresh flash messages (A/B/C)
expected: A and C close via Bootstrap's Alert transition, B via the default adapter's el.remove() fallback; the original C frame stays attached while its post-load clone closes; no console errors besides favicon. (The executor's headless-Chrome run in 04-ACCEPTANCE.md §6 used an uncommitted driver script.)
result: pass
reported: "1+2 done"

### 2. Maintainer review of upgrade prose + decision on review WR-01 / IN-03
expected: docs/migrating-1.0.md ("Hooks instead of copies" JS bullet; "The alert frame" before/after) and docs/reference/javascript.md (cv.adapters whole-map paragraph; "Dismissible alerts") both distinguish pre-load default filling from post-load whole-map replacement, require alert.close(el) in a later replacement and show cv.bootstrapAdapters(ns).alert; CHANGELOG Unreleased Breaking/Added name four adapters. Decide WR-01: theme.md:212-214 claims the dropdown templates are "the only stock templates with Bootstrap data-bs-* attributes", but crud_views_object_detail accordion/group.html and tabs-vertical/object_detail.html also carry data-bs-* — scope the sentence to crud_views core, or accept a Phase 7 deferral. Decide IN-03: messages.md:40-41 says the X "does nothing" without core scripts, whereas viewset.js without adapters.js throws a TypeError on click.
result: pass
reported: "1+2 done" — WR-01 and IN-03 both decided "fix now"; fixed in b7b49ae (theme.md data-bs-* claim scoped to core templates, object-detail layouts named; messages.md describes TypeError when adapters.js is missing)

## Summary

total: 2
passed: 2
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps
