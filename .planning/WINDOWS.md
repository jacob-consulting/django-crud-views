---
schema_version: 1
open_count: 2
waived_count: 0
fixed_count: 2
total_count: 4
last_updated: 2026-10-26T12:40:20.826Z
---

# Broken Windows Ledger

> Cross-phase defect register. With `workflow.windows_enforce` enabled, `/gsd-ship` blocks while `open_count > 0`.
> Waive with `gsd-tools windows waive <id> "<reason>"` (reason required).
> Mark fixed with `gsd-tools windows fixed <id>`.

| id | phase | kind | file | line | description | status | reason | recorded_at | resolved_at |
|----|-------|------|------|------|-------------|--------|--------|-------------|-------------|
| 1 | 01 | deviation | tests/test1/test_card_label_mode_render.py |  | RequestFactory render helper sets resolver_match before recording valid RED evidence | fixed |  | 2026-10-26T11:03:49.854Z | 2026-10-26T11:04:00.477Z |
| 2 | 01 | deviation | tests/test1/test_card_label_mode_render.py |  | Task 2 was already green after Task 1; the expanded matrix was verified red against the exact pre-fix source and committed as tests only | fixed |  | 2026-10-26T11:03:49.979Z | 2026-10-26T11:04:00.593Z |
| 3 | 02 | skipped-test | tests/test1/test_assets.py | 332 | Existing CSP nonce roundtrip test skips on Django 5.2 because built-in CSP middleware requires Django 6.0 | open |  | 2026-10-26T12:40:20.697Z |  |
| 4 | 02 | lint-warning | .planning/phases/02-form-key-grammar/deferred-items.md |  | Ruff 0.16.10 differs from manifest >=0.17,<0.18; global format reports seven pre-existing planning Markdown files | open |  | 2026-10-26T12:40:20.826Z |  |

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
    "resolved_at": "2026-10-26T11:04:00.477Z",
    "milestone": null
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
    "resolved_at": "2026-10-26T11:04:00.593Z",
    "milestone": null
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
    "resolved_at": null,
    "milestone": null
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
    "resolved_at": null,
    "milestone": null
  }
]
````
