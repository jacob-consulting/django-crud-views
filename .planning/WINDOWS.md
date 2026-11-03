---
schema_version: 1
open_count: 4
waived_count: 0
fixed_count: 5
total_count: 9
last_updated: 2026-10-28T08:48:15.158Z
---

# Broken Windows Ledger

> Cross-phase defect register. `/gsd-ship` blocks while `open_count > 0`.
> Waive with `gsd-tools windows waive <id> "<reason>"` (reason required).
> Mark fixed with `gsd-tools windows fixed <id>`.

| id | phase | kind | file | line | description | status | reason | recorded_at | resolved_at |
|----|-------|------|------|------|-------------|--------|--------|-------------|-------------|
| 1 | 01 | deviation | tests/test1/test_card_label_mode_render.py |  | RequestFactory render helper sets resolver_match before recording valid RED evidence | fixed |  | 2026-10-26T11:03:49.854Z | 2026-10-26T11:04:00.477Z |
| 2 | 01 | deviation | tests/test1/test_card_label_mode_render.py |  | Task 2 was already green after Task 1; the expanded matrix was verified red against the exact pre-fix source and committed as tests only | fixed |  | 2026-10-26T11:03:49.979Z | 2026-10-26T11:04:00.593Z |
| 3 | 02 | skipped-test | tests/test1/test_assets.py | 332 | Existing CSP nonce roundtrip test skips on Django 5.2 because built-in CSP middleware requires Django 6.0 | open |  | 2026-10-26T12:40:20.697Z |  |
| 4 | 02 | lint-warning | .planning/phases/02-form-key-grammar/deferred-items.md |  | Ruff 0.16.10 differs from manifest >=0.17,<0.18; global format reports seven pre-existing planning Markdown files | open |  | 2026-10-26T12:40:20.826Z |  |
| 5 | 06 | deviation | tests/js/list.filter.test.js | 159 | Pre-existing JS failure on locked jsdom 30.1.2: element-scoped '#cv-filter-toggle > span' selector returns null; Phase 06 JS gates stay red until fixed (06-01 deferred-items) | fixed |  | 2026-10-28T06:15:42.420Z | 2026-10-28T07:58:29.012Z |
| 6 | 06 | deviation | package-lock.json |  | npm audit: high-severity advisories in transitive dev-only undici; lockfile intentionally unchanged in Phase 06 (06-01 deferred-items) | open |  | 2026-10-28T06:15:42.562Z |  |
| 7 | 06 | stub | src/crud_views/lib/crispy/buttons.py |  | Crispy layout form buttons pass no icon yet: icon/both modes (form floor set to icon or both) render no visible icon until 06-04 adds kind-default icons, icon= hooks and the missing-icon policy | fixed |  | 2026-10-28T06:36:10.760Z | 2026-10-28T07:04:38.892Z |
| 8 | 06 | stub | src/crud_views/lib/view/button_data.py |  | Form missing-icon policy not yet applied: an icon-mode form button whose icon is explicitly None/empty or unavailable renders hidden text only (no strict ValueError, no logged label fallback) until 06-06 adds the availability predicate and runtime policy | fixed |  | 2026-10-28T07:04:39.037Z | 2026-10-28T07:48:56.639Z |
| 9 | 06 | unrun-verify | .planning/phases/06-form-button-leaf/06-ACCEPTANCE.md |  | 06-09 human-check pending: hover tooltip (not observed in headless harness), visual quality in label/both/icon, screen-reader announcement and migration-prose readability | open |  | 2026-10-28T08:48:15.158Z |  |

````json
[
  {
    "id": 1,
    "kind": "deviation",
    "phase": "01",
    "file": "tests/test1/test_card_label_mode_render.py",
    "line": null,
    "description": "RequestFactory render helper sets resolver_match before recording valid RED evidence",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-10-26T11:03:49.854Z",
    "resolved_at": "2026-10-26T11:04:00.477Z"
  },
  {
    "id": 2,
    "kind": "deviation",
    "phase": "01",
    "file": "tests/test1/test_card_label_mode_render.py",
    "line": null,
    "description": "Task 2 was already green after Task 1; the expanded matrix was verified red against the exact pre-fix source and committed as tests only",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-10-26T11:03:49.979Z",
    "resolved_at": "2026-10-26T11:04:00.593Z"
  },
  {
    "id": 3,
    "kind": "skipped-test",
    "phase": "02",
    "file": "tests/test1/test_assets.py",
    "line": 332,
    "description": "Existing CSP nonce roundtrip test skips on Django 5.2 because built-in CSP middleware requires Django 6.0",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-10-26T12:40:20.697Z",
    "resolved_at": null
  },
  {
    "id": 4,
    "kind": "lint-warning",
    "phase": "02",
    "file": ".planning/phases/02-form-key-grammar/deferred-items.md",
    "line": null,
    "description": "Ruff 0.16.10 differs from manifest >=0.17,<0.18; global format reports seven pre-existing planning Markdown files",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-10-26T12:40:20.826Z",
    "resolved_at": null
  },
  {
    "id": 5,
    "kind": "deviation",
    "phase": "06",
    "file": "tests/js/list.filter.test.js",
    "line": 159,
    "description": "Pre-existing JS failure on locked jsdom 30.1.2: element-scoped '#cv-filter-toggle > span' selector returns null; Phase 06 JS gates stay red until fixed (06-01 deferred-items)",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-10-28T06:15:42.420Z",
    "resolved_at": "2026-10-28T07:58:29.012Z"
  },
  {
    "id": 6,
    "kind": "deviation",
    "phase": "06",
    "file": "package-lock.json",
    "line": null,
    "description": "npm audit: high-severity advisories in transitive dev-only undici; lockfile intentionally unchanged in Phase 06 (06-01 deferred-items)",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-10-28T06:15:42.562Z",
    "resolved_at": null
  },
  {
    "id": 7,
    "kind": "stub",
    "phase": "06",
    "file": "src/crud_views/lib/crispy/buttons.py",
    "line": null,
    "description": "Crispy layout form buttons pass no icon yet: icon/both modes (form floor set to icon or both) render no visible icon until 06-04 adds kind-default icons, icon= hooks and the missing-icon policy",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-10-28T06:36:10.760Z",
    "resolved_at": "2026-10-28T07:04:38.892Z"
  },
  {
    "id": 8,
    "kind": "stub",
    "phase": "06",
    "file": "src/crud_views/lib/view/button_data.py",
    "line": null,
    "description": "Form missing-icon policy not yet applied: an icon-mode form button whose icon is explicitly None/empty or unavailable renders hidden text only (no strict ValueError, no logged label fallback) until 06-06 adds the availability predicate and runtime policy",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-10-28T07:04:39.037Z",
    "resolved_at": "2026-10-28T07:48:56.639Z"
  },
  {
    "id": 9,
    "kind": "unrun-verify",
    "phase": "06",
    "file": ".planning/phases/06-form-button-leaf/06-ACCEPTANCE.md",
    "line": null,
    "description": "06-09 human-check pending: hover tooltip (not observed in headless harness), visual quality in label/both/icon, screen-reader announcement and migration-prose readability",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-10-28T08:48:15.158Z",
    "resolved_at": null
  }
]
````
