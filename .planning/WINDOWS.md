---
schema_version: 1
open_count: 6
waived_count: 2
fixed_count: 15
total_count: 23
last_updated: 2026-11-02T21:25:49.151Z
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
| 5 | 06 | deviation | tests/js/list.filter.test.js | 159 | Pre-existing JS failure on locked jsdom 30.1.2: element-scoped '#cv-filter-toggle > span' selector returns null; Phase 06 JS gates stay red until fixed (06-01 deferred-items) | fixed |  | 2026-10-28T06:15:42.420Z | 2026-10-28T07:58:29.012Z |
| 6 | 06 | deviation | package-lock.json |  | npm audit: high-severity advisories in transitive dev-only undici; lockfile intentionally unchanged in Phase 06 (06-01 deferred-items) | open |  | 2026-10-28T06:15:42.562Z |  |
| 7 | 06 | stub | src/crud_views/lib/crispy/buttons.py |  | Crispy layout form buttons pass no icon yet: icon/both modes (form floor set to icon or both) render no visible icon until 06-04 adds kind-default icons, icon= hooks and the missing-icon policy | fixed |  | 2026-10-28T06:36:10.760Z | 2026-10-28T07:04:38.892Z |
| 8 | 06 | stub | src/crud_views/lib/view/button_data.py |  | Form missing-icon policy not yet applied: an icon-mode form button whose icon is explicitly None/empty or unavailable renders hidden text only (no strict ValueError, no logged label fallback) until 06-06 adds the availability predicate and runtime policy | fixed |  | 2026-10-28T07:04:39.037Z | 2026-10-28T07:48:56.639Z |
| 9 | 06 | unrun-verify | .planning/phases/06-form-button-leaf/06-ACCEPTANCE.md |  | 06-09 human-check pending: hover tooltip (not observed in headless harness), visual quality in label/both/icon, screen-reader announcement and migration-prose readability | open |  | 2026-10-28T08:48:15.158Z |  |
| 10 | 06.3 | unmet-truth | tests/test1/test_guardian_policy.py | 879 | CT-01 has candidate repair evidence: configured Car helper/list and published grant/revoke positives pass on all three series; AUTH-06-unclassified remains unresolved and independent review is pending. | fixed | CT-01 independently repaired and reviewed; AUTH-06 classifier fallback dismissed by recovered-source investigation (06.3-UNCLASSIFIED-REVIEW.md). | 2026-10-30T13:35:57.187Z | 2026-11-01T07:57:07.320Z |
| 11 | 06.3 | unmet-truth | .planning/phases/06.3-delete-protection-and-write-boundary-integrity-issue-282/06.3-GUARDIAN-REVIEW.md |  | GUA-01 precision backstop remains human_needed/insufficient_spec: normal int/UUID and exact configured-key tests pass, but no general custom-PK/coercion predicate was supplied. | waived | Maintainer authorized formal scope reconciliation on 2026-11-01: tested int/UUID/exact-key/queryset/alias predicate is the phase contract; broader custom-PK/cast/collation compatibility remains unverified follow-up in issue 286. Not a universal precision pass. | 2026-10-30T13:36:14.791Z | 2026-11-01T07:57:07.320Z |
| 12 | 06.3 | deviation | tests/test1/test_delete.py | 1397 | Plan 13 synthetic deletion metadata fixtures now supply declaring field owners; directly impacted compatibility correction verified on Django 4.2 and 6.0. | fixed |  | 2026-10-30T23:41:34.442Z | 2026-10-30T23:41:41.882Z |
| 13 | 06.3 | deviation | src/crud_views/lib/deletion.py | 258 | Fixed absent nullable parent joins in _native_parent_rows alongside inspection; prevents unrelated null-key parent deletion. | fixed |  | 2026-10-30T23:46:34.873Z | 2026-10-30T23:47:17.135Z |
| 14 | 06.3 | deviation | .planning/phases/06.3-delete-protection-and-write-boundary-integrity-issue-282/16-evidence/check.py |  | Plan 16 checker now independently validates overlapping package and imported-module hashes; original capture checker retained and 11 invalid variants rejected. | fixed |  | 2026-10-31T00:00:58.208Z | 2026-10-31T00:01:09.404Z |
| 15 | 06.3 | deviation | .planning/phases/06.3-delete-protection-and-write-boundary-integrity-issue-282/16-evidence/check.py |  | Plan 16 JUnit reconciliation now handles class-qualified full-suite nodes; copied class controls pass and mismatches reject, without repeating unchanged product suites. | fixed |  | 2026-10-31T00:05:45.859Z | 2026-10-31T00:05:46.035Z |
| 16 | 06.3 | unmet-truth | src/crud_views/static/crud_views/js/modal.js | 43 | UI-F01: real keyboard invalid/blocked 422 modal replacement leaves focus on BODY until next Tab; Close also leaves BODY. Newly observed on unchanged baseline JS; independent severity/remediation review required. | fixed | UI-F01/CR-04 and CR-05 repaired; current twelve-case browser evidence source-validated and owner keyboard review accepted. | 2026-10-31T00:26:22.293Z | 2026-11-01T07:57:07.320Z |
| 17 | 06.3 | unrun-verify | .planning/phases/06.3-delete-protection-and-write-boundary-integrity-issue-282/06.3-GAP-REVIEW.md |  | Plan 17 final human checks pending for all twelve individually tracked IDs: GUA-precision, four unclassified predicates, four prohibitions and UI-01/02/03. Design approval does not answer these final questions. | fixed | All twelve owner responses preserved; four detector flags dismissed after investigation; bounded precision predicate established and broader scope deferred to issue 286 under formal reconciliation. | 2026-10-31T00:26:22.432Z | 2026-11-01T07:57:07.320Z |
| 18 | 06.4 | deviation | .planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-01-SUMMARY.md |  | Sequential execution preserves required prior-phase HEAD; FSET-02 remains pending later lifecycle plans. | fixed |  | 2026-11-01T10:52:17.888Z | 2026-11-01T10:53:29.098Z |
| 19 | 06.4 | deviation | tests/test1/test_conditional_persistence.py |  | Disabled ImageField reference-only fixture uses native initial=None/no-change because validating a nonempty disabled image initial requires Pillow; production image validation remains unchanged. | fixed |  | 2026-11-01T11:10:51.632Z | 2026-11-01T11:11:17.692Z |
| 20 | 06.4 | deviation | .planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py | 984 | WR-03: aggregate checker accepts missing or contradictory corruption subprocess evidence; independent security T22/T28/T33 remains blocking | open |  | 2026-11-01T17:22:40.240Z |  |
| 21 | 06.4 | deviation | .planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py | 857 | WR-04: aggregate checker omits conditional screenshot inventory/hash contract; security T22/T33 high and T31 medium remain open | open |  | 2026-11-01T17:22:40.406Z |  |
| 22 | 06.5 | deviation | tests/test1/test_form_buttons_golden.py | 268 | Required raw Django 6.0 full gate fails the pre-existing crispy-floor wrapper golden; no deselection or waiver applied. | waived | User explicitly authorized existing CRISPY_FLOOR_DESELECT for only test_form_buttons_golden.py::test_filter_form_baseline and multicore rerun on 2026-11-02. Reconciled plan09 command passed 8328 tests with -n 4 in 256.14s, zero skips/failures; companion controls and Django6 CSP executed. Separate 09-evidence/django60-floor-multicore.log/xml; original django60.log remains byte-identical to de61f3c with 1 failed, 8328 passed. Wrapper mismatch not fixed; no other exclusion or install authorized. | 2026-11-02T13:17:44.247Z | 2026-11-02T13:51:14.237Z |
| 23 | 06.6 | unrun-verify | .planning/phases/06.6-theme-adoption-seams-from-the-tabler-sync/06.6-06-PLAN.md |  | Task 06-02 real companion capture/check blocked: pytest, pytest-django and pytest-xdist absent; source HEAD externally advanced from pinned revision. | fixed |  | 2026-11-02T21:10:26.684Z | 2026-11-02T21:25:49.151Z |

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
  },
  {
    "id": 10,
    "kind": "unmet-truth",
    "phase": "06.3",
    "file": "tests/test1/test_guardian_policy.py",
    "line": 879,
    "description": "CT-01 has candidate repair evidence: configured Car helper/list and published grant/revoke positives pass on all three series; AUTH-06-unclassified remains unresolved and independent review is pending.",
    "status": "fixed",
    "reason": "CT-01 independently repaired and reviewed; AUTH-06 classifier fallback dismissed by recovered-source investigation (06.3-UNCLASSIFIED-REVIEW.md).",
    "recorded_at": "2026-10-30T13:35:57.187Z",
    "resolved_at": "2026-11-01T07:57:07.320Z",
    "milestone": "v1.0"
  },
  {
    "id": 11,
    "kind": "unmet-truth",
    "phase": "06.3",
    "file": ".planning/phases/06.3-delete-protection-and-write-boundary-integrity-issue-282/06.3-GUARDIAN-REVIEW.md",
    "line": null,
    "description": "GUA-01 precision backstop remains human_needed/insufficient_spec: normal int/UUID and exact configured-key tests pass, but no general custom-PK/coercion predicate was supplied.",
    "status": "waived",
    "reason": "Maintainer authorized formal scope reconciliation on 2026-11-01: tested int/UUID/exact-key/queryset/alias predicate is the phase contract; broader custom-PK/cast/collation compatibility remains unverified follow-up in issue 286. Not a universal precision pass.",
    "recorded_at": "2026-10-30T13:36:14.791Z",
    "resolved_at": "2026-11-01T07:57:07.320Z",
    "milestone": "v1.0"
  },
  {
    "id": 12,
    "kind": "deviation",
    "phase": "06.3",
    "file": "tests/test1/test_delete.py",
    "line": 1397,
    "description": "Plan 13 synthetic deletion metadata fixtures now supply declaring field owners; directly impacted compatibility correction verified on Django 4.2 and 6.0.",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-10-30T23:41:34.442Z",
    "resolved_at": "2026-10-30T23:41:41.882Z",
    "milestone": "v1.0"
  },
  {
    "id": 13,
    "kind": "deviation",
    "phase": "06.3",
    "file": "src/crud_views/lib/deletion.py",
    "line": 258,
    "description": "Fixed absent nullable parent joins in _native_parent_rows alongside inspection; prevents unrelated null-key parent deletion.",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-10-30T23:46:34.873Z",
    "resolved_at": "2026-10-30T23:47:17.135Z",
    "milestone": "v1.0"
  },
  {
    "id": 14,
    "kind": "deviation",
    "phase": "06.3",
    "file": ".planning/phases/06.3-delete-protection-and-write-boundary-integrity-issue-282/16-evidence/check.py",
    "line": null,
    "description": "Plan 16 checker now independently validates overlapping package and imported-module hashes; original capture checker retained and 11 invalid variants rejected.",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-10-31T00:00:58.208Z",
    "resolved_at": "2026-10-31T00:01:09.404Z",
    "milestone": "v1.0"
  },
  {
    "id": 15,
    "kind": "deviation",
    "phase": "06.3",
    "file": ".planning/phases/06.3-delete-protection-and-write-boundary-integrity-issue-282/16-evidence/check.py",
    "line": null,
    "description": "Plan 16 JUnit reconciliation now handles class-qualified full-suite nodes; copied class controls pass and mismatches reject, without repeating unchanged product suites.",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-10-31T00:05:45.859Z",
    "resolved_at": "2026-10-31T00:05:46.035Z",
    "milestone": "v1.0"
  },
  {
    "id": 16,
    "kind": "unmet-truth",
    "phase": "06.3",
    "file": "src/crud_views/static/crud_views/js/modal.js",
    "line": 43,
    "description": "UI-F01: real keyboard invalid/blocked 422 modal replacement leaves focus on BODY until next Tab; Close also leaves BODY. Newly observed on unchanged baseline JS; independent severity/remediation review required.",
    "status": "fixed",
    "reason": "UI-F01/CR-04 and CR-05 repaired; current twelve-case browser evidence source-validated and owner keyboard review accepted.",
    "recorded_at": "2026-10-31T00:26:22.293Z",
    "resolved_at": "2026-11-01T07:57:07.320Z",
    "milestone": "v1.0"
  },
  {
    "id": 17,
    "kind": "unrun-verify",
    "phase": "06.3",
    "file": ".planning/phases/06.3-delete-protection-and-write-boundary-integrity-issue-282/06.3-GAP-REVIEW.md",
    "line": null,
    "description": "Plan 17 final human checks pending for all twelve individually tracked IDs: GUA-precision, four unclassified predicates, four prohibitions and UI-01/02/03. Design approval does not answer these final questions.",
    "status": "fixed",
    "reason": "All twelve owner responses preserved; four detector flags dismissed after investigation; bounded precision predicate established and broader scope deferred to issue 286 under formal reconciliation.",
    "recorded_at": "2026-10-31T00:26:22.432Z",
    "resolved_at": "2026-11-01T07:57:07.320Z",
    "milestone": "v1.0"
  },
  {
    "id": 18,
    "kind": "deviation",
    "phase": "06.4",
    "file": ".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-01-SUMMARY.md",
    "line": null,
    "description": "Sequential execution preserves required prior-phase HEAD; FSET-02 remains pending later lifecycle plans.",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-11-01T10:52:17.888Z",
    "resolved_at": "2026-11-01T10:53:29.098Z",
    "milestone": "v1.0"
  },
  {
    "id": 19,
    "kind": "deviation",
    "phase": "06.4",
    "file": "tests/test1/test_conditional_persistence.py",
    "line": null,
    "description": "Disabled ImageField reference-only fixture uses native initial=None/no-change because validating a nonempty disabled image initial requires Pillow; production image validation remains unchanged.",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-11-01T11:10:51.632Z",
    "resolved_at": "2026-11-01T11:11:17.692Z",
    "milestone": "v1.0"
  },
  {
    "id": 20,
    "kind": "deviation",
    "phase": "06.4",
    "file": ".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py",
    "line": 984,
    "description": "WR-03: aggregate checker accepts missing or contradictory corruption subprocess evidence; independent security T22/T28/T33 remains blocking",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-11-01T17:22:40.240Z",
    "resolved_at": null,
    "milestone": "v1.0"
  },
  {
    "id": 21,
    "kind": "deviation",
    "phase": "06.4",
    "file": ".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py",
    "line": 857,
    "description": "WR-04: aggregate checker omits conditional screenshot inventory/hash contract; security T22/T33 high and T31 medium remain open",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-11-01T17:22:40.406Z",
    "resolved_at": null,
    "milestone": "v1.0"
  },
  {
    "id": 22,
    "kind": "deviation",
    "phase": "06.5",
    "file": "tests/test1/test_form_buttons_golden.py",
    "line": 268,
    "description": "Required raw Django 6.0 full gate fails the pre-existing crispy-floor wrapper golden; no deselection or waiver applied.",
    "status": "waived",
    "reason": "User explicitly authorized existing CRISPY_FLOOR_DESELECT for only test_form_buttons_golden.py::test_filter_form_baseline and multicore rerun on 2026-11-02. Reconciled plan09 command passed 8328 tests with -n 4 in 256.14s, zero skips/failures; companion controls and Django6 CSP executed. Separate 09-evidence/django60-floor-multicore.log/xml; original django60.log remains byte-identical to de61f3c with 1 failed, 8328 passed. Wrapper mismatch not fixed; no other exclusion or install authorized.",
    "recorded_at": "2026-11-02T13:17:44.247Z",
    "resolved_at": "2026-11-02T13:51:14.237Z",
    "milestone": "v1.0"
  },
  {
    "id": 23,
    "kind": "unrun-verify",
    "phase": "06.6",
    "file": ".planning/phases/06.6-theme-adoption-seams-from-the-tabler-sync/06.6-06-PLAN.md",
    "line": null,
    "description": "Task 06-02 real companion capture/check blocked: pytest, pytest-django and pytest-xdist absent; source HEAD externally advanced from pinned revision.",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-11-02T21:10:26.684Z",
    "resolved_at": "2026-11-02T21:25:49.151Z",
    "milestone": "v1.0"
  }
]
````
