---
schema_version: 1
open_count: 1
waived_count: 9
fixed_count: 30
total_count: 40
last_updated: 2026-11-08T20:57:48.948Z
---

# Broken Windows Ledger

> Cross-phase defect register. With `workflow.windows_enforce` enabled, `/gsd-ship` blocks while `open_count > 0`.
> Waive with `gsd-tools windows waive <id> "<reason>"` (reason required).
> Mark fixed with `gsd-tools windows fixed <id>`.

| id | phase | kind | file | line | description | status | reason | recorded_at | resolved_at |
|----|-------|------|------|------|-------------|--------|--------|-------------|-------------|
| 1 | 01 | deviation | tests/test1/test_card_label_mode_render.py |  | RequestFactory render helper sets resolver_match before recording valid RED evidence | fixed |  | 2026-10-26T11:03:49.854Z | 2026-10-26T11:04:00.477Z |
| 2 | 01 | deviation | tests/test1/test_card_label_mode_render.py |  | Task 2 was already green after Task 1; the expanded matrix was verified red against the exact pre-fix source and committed as tests only | fixed |  | 2026-10-26T11:03:49.979Z | 2026-10-26T11:04:00.593Z |
| 3 | 02 | skipped-test | tests/test1/test_assets.py | 332 | Existing CSP nonce roundtrip test skips on Django 5.2 because built-in CSP middleware requires Django 6.0 | waived | Explicitly deferred for the 06.15 ship gate: this CSP nonce test requires Django 6.0 and is skipped on Django 5.2. Keep the Django-version-specific coverage gap visible; follow up in a test-matrix maintenance task. | 2026-10-26T12:40:20.697Z | 2026-11-06T12:43:45.337Z |
| 4 | 02 | lint-warning | .planning/phases/02-form-key-grammar/deferred-items.md |  | Ruff 0.16.10 differs from manifest >=0.17,<0.18; global format reports seven pre-existing planning Markdown files | waived | Explicitly deferred for the 06.15 ship gate: the recorded Ruff version differs from the manifest and global formatting reports seven pre-existing planning files. Do not reformat unrelated planning artifacts as part of 06.15; reconcile tool version and formatting separately. | 2026-10-26T12:40:20.826Z | 2026-11-06T12:43:45.500Z |
| 5 | 06 | deviation | tests/js/list.filter.test.js | 159 | Pre-existing JS failure on locked jsdom 30.1.2: element-scoped '#cv-filter-toggle > span' selector returns null; Phase 06 JS gates stay red until fixed (06-01 deferred-items) | fixed |  | 2026-10-28T06:15:42.420Z | 2026-10-28T07:58:29.012Z |
| 6 | 06 | deviation | package-lock.json |  | npm audit: high-severity advisories in transitive dev-only undici; lockfile intentionally unchanged in Phase 06 (06-01 deferred-items) | waived | Explicitly deferred for the 06.15 ship gate: npm audit reported high-severity issues in transitive dev-only undici, and phase 06 intentionally left package-lock.json unchanged. Track dependency remediation separately; this waiver does not claim the advisories are resolved. | 2026-10-28T06:15:42.562Z | 2026-11-06T12:43:45.666Z |
| 7 | 06 | stub | src/crud_views/lib/crispy/buttons.py |  | Crispy layout form buttons pass no icon yet: icon/both modes (form floor set to icon or both) render no visible icon until 06-04 adds kind-default icons, icon= hooks and the missing-icon policy | fixed |  | 2026-10-28T06:36:10.760Z | 2026-10-28T07:04:38.892Z |
| 8 | 06 | stub | src/crud_views/lib/view/button_data.py |  | Form missing-icon policy not yet applied: an icon-mode form button whose icon is explicitly None/empty or unavailable renders hidden text only (no strict ValueError, no logged label fallback) until 06-06 adds the availability predicate and runtime policy | fixed |  | 2026-10-28T07:04:39.037Z | 2026-10-28T07:48:56.639Z |
| 9 | 06 | unrun-verify | .planning/phases/06-form-button-leaf/06-ACCEPTANCE.md |  | 06-09 human-check pending: hover tooltip (not observed in headless harness), visual quality in label/both/icon, screen-reader announcement and migration-prose readability | waived | Explicitly deferred for the 06.15 ship gate: phase 06-09 human checks for tooltip, visual modes, screen-reader announcement, and migration prose remain unperformed. Preserve this acceptance gap for a dedicated human verification follow-up; no pass is asserted. | 2026-10-28T08:48:15.158Z | 2026-11-06T12:43:45.821Z |
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
| 20 | 06.4 | deviation | .planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py | 984 | WR-03: aggregate checker accepts missing or contradictory corruption subprocess evidence; independent security T22/T28/T33 remains blocking | waived | Explicitly deferred for the 06.15 ship gate: WR-03 evidence checker gap and referenced security findings T22/T28/T33 remain unresolved. Track a dedicated phase 06.4 evidence/security follow-up; this waiver does not claim the checks are safe or complete. | 2026-11-01T17:22:40.240Z | 2026-11-06T12:43:45.979Z |
| 21 | 06.4 | deviation | .planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py | 857 | WR-04: aggregate checker omits conditional screenshot inventory/hash contract; security T22/T33 high and T31 medium remain open | waived | Explicitly deferred for the 06.15 ship gate: WR-04 screenshot inventory/hash contract gap and referenced security findings T22/T33/T31 remain unresolved. Track a dedicated phase 06.4 evidence/security follow-up; this waiver does not claim the checks are safe or complete. | 2026-11-01T17:22:40.406Z | 2026-11-06T12:43:46.147Z |
| 22 | 06.5 | deviation | tests/test1/test_form_buttons_golden.py | 268 | Required raw Django 6.0 full gate fails the pre-existing crispy-floor wrapper golden; no deselection or waiver applied. | waived | User explicitly authorized existing CRISPY_FLOOR_DESELECT for only test_form_buttons_golden.py::test_filter_form_baseline and multicore rerun on 2026-11-02. Reconciled plan09 command passed 8328 tests with -n 4 in 256.14s, zero skips/failures; companion controls and Django6 CSP executed. Separate 09-evidence/django60-floor-multicore.log/xml; original django60.log remains byte-identical to de61f3c with 1 failed, 8328 passed. Wrapper mismatch not fixed; no other exclusion or install authorized. | 2026-11-02T13:17:44.247Z | 2026-11-02T13:51:14.237Z |
| 23 | 06.6 | unrun-verify | .planning/phases/06.6-theme-adoption-seams-from-the-tabler-sync/06.6-06-PLAN.md |  | Task 06-02 real companion capture/check blocked: pytest, pytest-django and pytest-xdist absent; source HEAD externally advanced from pinned revision. | fixed |  | 2026-11-02T21:10:26.684Z | 2026-11-02T21:25:49.151Z |
| 24 | 06.7 | deviation | src/crud_views/lib/crispy/form.py |  | Share one cancel context during button rendering to prevent duplicate destination state evaluation while preserving custom kwargs hooks. | fixed |  | 2026-11-03T16:41:44.156Z | 2026-11-03T16:41:52.777Z |
| 25 | 06.7 | deviation | tests/test1/test_crispy_buttons.py |  | Authorize list destinations locally in 17 presentation cases whose pre-plan fixtures lacked the permission required for visible Cancel. | fixed |  | 2026-11-03T16:41:44.314Z | 2026-11-03T16:41:52.936Z |
| 26 | 06.7 | deviation | tests/test1/test_cancel_permissions.py |  | Migrate selector fallback diagnostic to automatic defaults while retaining explicit static invalid-fallback coverage. | fixed |  | 2026-11-03T16:54:56.249Z | 2026-11-03T16:55:04.782Z |
| 27 | 06.7 | deviation | tests/test1/test_cancel_navigation.py |  | Isolate late-registration fixture registry so it cannot contaminate the registered-form inventory. | fixed |  | 2026-11-03T16:54:56.421Z | 2026-11-03T16:55:04.913Z |
| 28 | 06.7 | deviation | tests/test1/test_form_button_docs.py |  | Cancel-present documentation fixtures now grant view permission; three legacy add-only fixture failures fixed and verified in 34-test recipe selection. | fixed |  | 2026-11-03T17:03:26.320Z | 2026-11-03T17:04:29.345Z |
| 29 | 06.7 | deviation | src/crud_views/lib/crispy/form.py | 92 | Plan05 final matrix exposed standalone custom Cancel kwargs regression plus remaining exact-link/permission fixtures; scoped plan01/02 repair preserves bound policy and passed 334 focused tests. | fixed |  | 2026-11-03T18:10:58.862Z | 2026-11-03T18:13:00.670Z |
| 30 | 06.7 | unrun-verify | .planning/phases/06.7-dynamic-cancel-navigation-and-origin-query-state/06.7-ACCEPTANCE.md |  | Human keyboard, focus and visual Cancel acceptance plus UI consideration confirmation remain pending; automated browser results do not supply human acceptance. | fixed |  | 2026-11-03T18:10:59.020Z | 2026-11-03T19:53:19.111Z |
| 31 | 06.7 | deviation | tests/test1/test_cancel_state.py |  | Plan05 Django4.2 replay required explicit filter helpers and removal of filtering metadata from plain-list fixtures; 83 focused tests pass on4.2 and5.2 with product unchanged. | fixed |  | 2026-11-03T18:17:50.004Z | 2026-11-03T18:17:50.177Z |
| 32 | 06.9 | deviation | src/crud_views/lib/views/delete.py |  | Resolved in 5169325: preserve custom QuerySet.get Http404 and bind mounted SCRIPT_NAME; final 819-test suite passes. | fixed |  | 2026-11-04T10:12:29.437Z | 2026-11-04T10:12:55.657Z |
| 33 | 06.10 | skipped-test | tests/test1/test_assets.py | 332 | Existing Django 6-only CSP roundtrip skips on Django 5.2; this runtime-specific skip is outside the delete-preview change. | fixed |  | 2026-11-04T21:29:51.737Z | 2026-11-04T21:30:19.548Z |
| 34 | 06.10 | unrun-verify | .planning/phases/06.10-simplify-protected-object-previews-and-cap-total-displayed-o/06.10-ACCEPTANCE.md |  | Human stock/copied page/modal presentation, keyboard acceptance and UI kind confirmation remain pending at the normal end-of-phase check. | fixed |  | 2026-11-04T21:30:19.709Z | 2026-11-05T09:25:26.031Z |
| 35 | 06.16 | deviation | tests/test1/od/test_help_text_policy.py |  | Plan 02 task 2 is test-only expansion of task 1 behavior; no separate failing RED or production GREEN commit was needed. | fixed |  | 2026-11-06T19:15:57.137Z | 2026-11-06T19:16:25.752Z |
| 36 | 06.17 | deviation | docs/reference/javascript.md |  | Task 1 documentation edits began before RED evidence classifier approval; actual pre-edit report subsequently approved, final executable recipes and all regression gates pass. | waived | Independent deep review found no product defect: genuine pre-edit failures were preserved and later classifier-approved; final executable recipe and full regression checks pass. Accept the documentation-only ordering exception while retaining the historical violation; no retroactive compliance claimed. | 2026-11-07T10:17:20.705Z | 2026-11-07T10:25:35.767Z |
| 37 | 06.18 | deviation | src/crud_views/lib/ancestors.py |  | Interim (06.18-01): nested endpoints outside the core list/detail/create/update/delete families without an exact actions entry perform no ancestor work until 06.18-02 Task 2 adds the finite family table and custom-declaration guards | fixed |  | 2026-11-08T17:34:13.035Z | 2026-11-08T18:15:32.509Z |
| 38 | 06.18 | deviation | tests/test1/test_authorization_matrix.py |  | Interim (06.18-03): eight legacy Guardian authorization modules still declare/patch the removed cv_guardian_parent_* fields (1044 setup errors, 5 monkeypatch AttributeErrors, 2 removed-name manage assertions) and 3 test_guardian.py cases assert child-view fallback relaxing the Publisher ancestor (H2-removed/H2-semantics); fixture/expectation migration owned by 06.18-08 | open |  | 2026-11-08T18:42:19.870Z |  |
| 39 | 06.18 | deviation | tests/test1/test_resource_views.py |  | Interim (06.18-04): with ancestry before has_permission(), test_resource_views.py::test_nested_detail_scoped_to_parent_404 now returns 403 (S3 viewer lacks Publisher view) instead of the masked Resource-loader 404; it joins the 3 open H1-resource rows owned by 06.18-05 Task 2 (Publisher-view + Resource-view actor migration) | fixed |  | 2026-11-08T19:18:23.782Z | 2026-11-08T19:47:55.487Z |
| 40 | 06.18 | unmet-truth | src/crud_views/lib/view/base.py |  | Found during 06.18-06: CrudView.get_context_data applies _scope_child_queryset only when object_list is not a keyword; django-filter's BaseFilterView.get passes object_list=..., so a nested ListViewTableFilterMixin list whose get_queryset omits the parent filter lists other parents' rows (ANCE-05, 06.18-05 seam; see deferred-items.md). Default ViewSet querysets already filter. | fixed |  | 2026-11-08T20:21:21.236Z | 2026-11-08T20:57:48.948Z |

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
    "status": "waived",
    "reason": "Explicitly deferred for the 06.15 ship gate: this CSP nonce test requires Django 6.0 and is skipped on Django 5.2. Keep the Django-version-specific coverage gap visible; follow up in a test-matrix maintenance task.",
    "recorded_at": "2026-10-26T12:40:20.697Z",
    "resolved_at": "2026-11-06T12:43:45.337Z"
  },
  {
    "id": 4,
    "kind": "lint-warning",
    "phase": "02",
    "file": ".planning/phases/02-form-key-grammar/deferred-items.md",
    "line": null,
    "description": "Ruff 0.16.10 differs from manifest >=0.17,<0.18; global format reports seven pre-existing planning Markdown files",
    "status": "waived",
    "reason": "Explicitly deferred for the 06.15 ship gate: the recorded Ruff version differs from the manifest and global formatting reports seven pre-existing planning files. Do not reformat unrelated planning artifacts as part of 06.15; reconcile tool version and formatting separately.",
    "recorded_at": "2026-10-26T12:40:20.826Z",
    "resolved_at": "2026-11-06T12:43:45.500Z"
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
    "status": "waived",
    "reason": "Explicitly deferred for the 06.15 ship gate: npm audit reported high-severity issues in transitive dev-only undici, and phase 06 intentionally left package-lock.json unchanged. Track dependency remediation separately; this waiver does not claim the advisories are resolved.",
    "recorded_at": "2026-10-28T06:15:42.562Z",
    "resolved_at": "2026-11-06T12:43:45.666Z"
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
    "status": "waived",
    "reason": "Explicitly deferred for the 06.15 ship gate: phase 06-09 human checks for tooltip, visual modes, screen-reader announcement, and migration prose remain unperformed. Preserve this acceptance gap for a dedicated human verification follow-up; no pass is asserted.",
    "recorded_at": "2026-10-28T08:48:15.158Z",
    "resolved_at": "2026-11-06T12:43:45.821Z"
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
    "resolved_at": "2026-11-01T07:57:07.320Z"
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
    "resolved_at": "2026-11-01T07:57:07.320Z"
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
    "resolved_at": "2026-10-30T23:41:41.882Z"
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
    "resolved_at": "2026-10-30T23:47:17.135Z"
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
    "resolved_at": "2026-10-31T00:01:09.404Z"
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
    "resolved_at": "2026-10-31T00:05:46.035Z"
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
    "resolved_at": "2026-11-01T07:57:07.320Z"
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
    "resolved_at": "2026-11-01T07:57:07.320Z"
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
    "resolved_at": "2026-11-01T10:53:29.098Z"
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
    "resolved_at": "2026-11-01T11:11:17.692Z"
  },
  {
    "id": 20,
    "kind": "deviation",
    "phase": "06.4",
    "file": ".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py",
    "line": 984,
    "description": "WR-03: aggregate checker accepts missing or contradictory corruption subprocess evidence; independent security T22/T28/T33 remains blocking",
    "status": "waived",
    "reason": "Explicitly deferred for the 06.15 ship gate: WR-03 evidence checker gap and referenced security findings T22/T28/T33 remain unresolved. Track a dedicated phase 06.4 evidence/security follow-up; this waiver does not claim the checks are safe or complete.",
    "recorded_at": "2026-11-01T17:22:40.240Z",
    "resolved_at": "2026-11-06T12:43:45.979Z"
  },
  {
    "id": 21,
    "kind": "deviation",
    "phase": "06.4",
    "file": ".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/15-evidence/run.py",
    "line": 857,
    "description": "WR-04: aggregate checker omits conditional screenshot inventory/hash contract; security T22/T33 high and T31 medium remain open",
    "status": "waived",
    "reason": "Explicitly deferred for the 06.15 ship gate: WR-04 screenshot inventory/hash contract gap and referenced security findings T22/T33/T31 remain unresolved. Track a dedicated phase 06.4 evidence/security follow-up; this waiver does not claim the checks are safe or complete.",
    "recorded_at": "2026-11-01T17:22:40.406Z",
    "resolved_at": "2026-11-06T12:43:46.147Z"
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
    "resolved_at": "2026-11-02T13:51:14.237Z"
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
    "resolved_at": "2026-11-02T21:25:49.151Z"
  },
  {
    "id": 24,
    "kind": "deviation",
    "phase": "06.7",
    "file": "src/crud_views/lib/crispy/form.py",
    "line": null,
    "description": "Share one cancel context during button rendering to prevent duplicate destination state evaluation while preserving custom kwargs hooks.",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-11-03T16:41:44.156Z",
    "resolved_at": "2026-11-03T16:41:52.777Z"
  },
  {
    "id": 25,
    "kind": "deviation",
    "phase": "06.7",
    "file": "tests/test1/test_crispy_buttons.py",
    "line": null,
    "description": "Authorize list destinations locally in 17 presentation cases whose pre-plan fixtures lacked the permission required for visible Cancel.",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-11-03T16:41:44.314Z",
    "resolved_at": "2026-11-03T16:41:52.936Z"
  },
  {
    "id": 26,
    "kind": "deviation",
    "phase": "06.7",
    "file": "tests/test1/test_cancel_permissions.py",
    "line": null,
    "description": "Migrate selector fallback diagnostic to automatic defaults while retaining explicit static invalid-fallback coverage.",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-11-03T16:54:56.249Z",
    "resolved_at": "2026-11-03T16:55:04.782Z"
  },
  {
    "id": 27,
    "kind": "deviation",
    "phase": "06.7",
    "file": "tests/test1/test_cancel_navigation.py",
    "line": null,
    "description": "Isolate late-registration fixture registry so it cannot contaminate the registered-form inventory.",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-11-03T16:54:56.421Z",
    "resolved_at": "2026-11-03T16:55:04.913Z"
  },
  {
    "id": 28,
    "kind": "deviation",
    "phase": "06.7",
    "file": "tests/test1/test_form_button_docs.py",
    "line": null,
    "description": "Cancel-present documentation fixtures now grant view permission; three legacy add-only fixture failures fixed and verified in 34-test recipe selection.",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-11-03T17:03:26.320Z",
    "resolved_at": "2026-11-03T17:04:29.345Z"
  },
  {
    "id": 29,
    "kind": "deviation",
    "phase": "06.7",
    "file": "src/crud_views/lib/crispy/form.py",
    "line": 92,
    "description": "Plan05 final matrix exposed standalone custom Cancel kwargs regression plus remaining exact-link/permission fixtures; scoped plan01/02 repair preserves bound policy and passed 334 focused tests.",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-11-03T18:10:58.862Z",
    "resolved_at": "2026-11-03T18:13:00.670Z"
  },
  {
    "id": 30,
    "kind": "unrun-verify",
    "phase": "06.7",
    "file": ".planning/phases/06.7-dynamic-cancel-navigation-and-origin-query-state/06.7-ACCEPTANCE.md",
    "line": null,
    "description": "Human keyboard, focus and visual Cancel acceptance plus UI consideration confirmation remain pending; automated browser results do not supply human acceptance.",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-11-03T18:10:59.020Z",
    "resolved_at": "2026-11-03T19:53:19.111Z"
  },
  {
    "id": 31,
    "kind": "deviation",
    "phase": "06.7",
    "file": "tests/test1/test_cancel_state.py",
    "line": null,
    "description": "Plan05 Django4.2 replay required explicit filter helpers and removal of filtering metadata from plain-list fixtures; 83 focused tests pass on4.2 and5.2 with product unchanged.",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-11-03T18:17:50.004Z",
    "resolved_at": "2026-11-03T18:17:50.177Z"
  },
  {
    "id": 32,
    "kind": "deviation",
    "phase": "06.9",
    "file": "src/crud_views/lib/views/delete.py",
    "line": null,
    "description": "Resolved in 5169325: preserve custom QuerySet.get Http404 and bind mounted SCRIPT_NAME; final 819-test suite passes.",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-11-04T10:12:29.437Z",
    "resolved_at": "2026-11-04T10:12:55.657Z"
  },
  {
    "id": 33,
    "kind": "skipped-test",
    "phase": "06.10",
    "file": "tests/test1/test_assets.py",
    "line": 332,
    "description": "Existing Django 6-only CSP roundtrip skips on Django 5.2; this runtime-specific skip is outside the delete-preview change.",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-11-04T21:29:51.737Z",
    "resolved_at": "2026-11-04T21:30:19.548Z"
  },
  {
    "id": 34,
    "kind": "unrun-verify",
    "phase": "06.10",
    "file": ".planning/phases/06.10-simplify-protected-object-previews-and-cap-total-displayed-o/06.10-ACCEPTANCE.md",
    "line": null,
    "description": "Human stock/copied page/modal presentation, keyboard acceptance and UI kind confirmation remain pending at the normal end-of-phase check.",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-11-04T21:30:19.709Z",
    "resolved_at": "2026-11-05T09:25:26.031Z"
  },
  {
    "id": 35,
    "kind": "deviation",
    "phase": "06.16",
    "file": "tests/test1/od/test_help_text_policy.py",
    "line": null,
    "description": "Plan 02 task 2 is test-only expansion of task 1 behavior; no separate failing RED or production GREEN commit was needed.",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-11-06T19:15:57.137Z",
    "resolved_at": "2026-11-06T19:16:25.752Z"
  },
  {
    "id": 36,
    "kind": "deviation",
    "phase": "06.17",
    "file": "docs/reference/javascript.md",
    "line": null,
    "description": "Task 1 documentation edits began before RED evidence classifier approval; actual pre-edit report subsequently approved, final executable recipes and all regression gates pass.",
    "status": "waived",
    "reason": "Independent deep review found no product defect: genuine pre-edit failures were preserved and later classifier-approved; final executable recipe and full regression checks pass. Accept the documentation-only ordering exception while retaining the historical violation; no retroactive compliance claimed.",
    "recorded_at": "2026-11-07T10:17:20.705Z",
    "resolved_at": "2026-11-07T10:25:35.767Z"
  },
  {
    "id": 37,
    "kind": "deviation",
    "phase": "06.18",
    "file": "src/crud_views/lib/ancestors.py",
    "line": null,
    "description": "Interim (06.18-01): nested endpoints outside the core list/detail/create/update/delete families without an exact actions entry perform no ancestor work until 06.18-02 Task 2 adds the finite family table and custom-declaration guards",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-11-08T17:34:13.035Z",
    "resolved_at": "2026-11-08T18:15:32.509Z"
  },
  {
    "id": 38,
    "kind": "deviation",
    "phase": "06.18",
    "file": "tests/test1/test_authorization_matrix.py",
    "line": null,
    "description": "Interim (06.18-03): eight legacy Guardian authorization modules still declare/patch the removed cv_guardian_parent_* fields (1044 setup errors, 5 monkeypatch AttributeErrors, 2 removed-name manage assertions) and 3 test_guardian.py cases assert child-view fallback relaxing the Publisher ancestor (H2-removed/H2-semantics); fixture/expectation migration owned by 06.18-08",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-11-08T18:42:19.870Z",
    "resolved_at": null
  },
  {
    "id": 39,
    "kind": "deviation",
    "phase": "06.18",
    "file": "tests/test1/test_resource_views.py",
    "line": null,
    "description": "Interim (06.18-04): with ancestry before has_permission(), test_resource_views.py::test_nested_detail_scoped_to_parent_404 now returns 403 (S3 viewer lacks Publisher view) instead of the masked Resource-loader 404; it joins the 3 open H1-resource rows owned by 06.18-05 Task 2 (Publisher-view + Resource-view actor migration)",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-11-08T19:18:23.782Z",
    "resolved_at": "2026-11-08T19:47:55.487Z"
  },
  {
    "id": 40,
    "kind": "unmet-truth",
    "phase": "06.18",
    "file": "src/crud_views/lib/view/base.py",
    "line": null,
    "description": "Found during 06.18-06: CrudView.get_context_data applies _scope_child_queryset only when object_list is not a keyword; django-filter's BaseFilterView.get passes object_list=..., so a nested ListViewTableFilterMixin list whose get_queryset omits the parent filter lists other parents' rows (ANCE-05, 06.18-05 seam; see deferred-items.md). Default ViewSet querysets already filter.",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-11-08T20:21:21.236Z",
    "resolved_at": "2026-11-08T20:57:48.948Z",
    "milestone": "v1.0"
  }
]
````
