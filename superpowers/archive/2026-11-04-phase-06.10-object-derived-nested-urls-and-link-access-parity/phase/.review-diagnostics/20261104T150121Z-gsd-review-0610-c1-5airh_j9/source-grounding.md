# Cycle 1 source-grounding coverage

Effective authority: `intel` (deterministic drift-guard seam). The API surface is empty and Python symbols/signatures are UNCHECKABLE, never inferred absent. Filesystem existence is checked separately; supplemental declaration locations do not upgrade an unsupported adapter verdict. Existing CLI flags have no authoritative registry check here and are UNCHECKABLE. New artifacts and execution-generated SUMMARY files are excluded.

| Kind / reference | Plan lines | Verdict | Evidence |
|---|---|---|---|
| flag `--case` | 06.10-06-PLAN.md:73, 06.10-06-PLAN.md:93, 06.10-06-PLAN.md:112 | UNCHECKABLE | Not indexed by empty intel surface; external/library/field/CLI references not verified by authority |
| flag `--check` | 06.10-06-PLAN.md:142 | UNCHECKABLE | Not indexed by empty intel surface; external/library/field/CLI references not verified by authority |
| flag `--deselect` | 06.10-06-PLAN.md:130 | UNCHECKABLE | Not indexed by empty intel surface; external/library/field/CLI references not verified by authority |
| flag `--output` | 06.10-06-PLAN.md:93, 06.10-06-PLAN.md:112 | UNCHECKABLE | Not indexed by empty intel surface; external/library/field/CLI references not verified by authority |
| flag `--site-dir` | 06.10-05-PLAN.md:111, 06.10-06-PLAN.md:138 | UNCHECKABLE | Not indexed by empty intel surface; external/library/field/CLI references not verified by authority |
| flag `--strict` | 06.10-05-PLAN.md:111, 06.10-06-PLAN.md:138 | UNCHECKABLE | Not indexed by empty intel surface; external/library/field/CLI references not verified by authority |
| flag `--test` | 06.10-06-PLAN.md:91 | UNCHECKABLE | Not indexed by empty intel surface; external/library/field/CLI references not verified by authority |
| path `.nox/crispy_floor-3-12-django-6-0/bin/python` | 06.10-06-PLAN.md:130 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `.nox/tests-3-12-django-4-2/bin/python` | 06.10-06-PLAN.md:128 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `.nox/tests-3-12-django-5-2/bin/python` | 06.10-01-PLAN.md:117, 06.10-01-PLAN.md:135, 06.10-01-PLAN.md:154, 06.10-02-PLAN.md:91, 06.10-02-PLAN.md:109, 06.10-02-PLAN.md:111, 06.10-03-PLAN.md:98, 06.10-03-PLAN.md:117, 06.10-03-PLAN.md:135, 06.10-03-PLAN.md:137, 06.10-04-PLAN.md:82, 06.10-04-PLAN.md:84, 06.10-04-PLAN.md:102, 06.10-05-PLAN.md:81, 06.10-05-PLAN.md:94, 06.10-05-PLAN.md:107, 06.10-05-PLAN.md:109, 06.10-06-PLAN.md:126, 06.10-06-PLAN.md:132 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `.planning/PROJECT.md` | 06.10-01-PLAN.md:56, 06.10-06-PLAN.md:62, 06.10-06-PLAN.md:123 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `.planning/REQUIREMENTS.md` | 06.10-01-PLAN.md:59, 06.10-03-PLAN.md:57 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `.planning/ROADMAP.md` | 06.10-01-PLAN.md:57 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `.planning/STATE.md` | 06.10-01-PLAN.md:58 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `.planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-01-SUMMARY.md` | 06.10-01-PLAN.md:188, 06.10-02-PLAN.md:56, 06.10-04-PLAN.md:56, 06.10-05-PLAN.md:60 | EXCLUDED_NEW | Declared phase artifact or prior-plan SUMMARY execution output |
| path `.planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-02-SUMMARY.md` | 06.10-02-PLAN.md:144, 06.10-03-PLAN.md:60 | EXCLUDED_NEW | Declared phase artifact or prior-plan SUMMARY execution output |
| path `.planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-03-SUMMARY.md` | 06.10-03-PLAN.md:172, 06.10-05-PLAN.md:61, 06.10-06-PLAN.md:65 | EXCLUDED_NEW | Declared phase artifact or prior-plan SUMMARY execution output |
| path `.planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-04-SUMMARY.md` | 06.10-04-PLAN.md:135, 06.10-05-PLAN.md:62, 06.10-06-PLAN.md:66 | EXCLUDED_NEW | Declared phase artifact or prior-plan SUMMARY execution output |
| path `.planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-05-SUMMARY.md` | 06.10-05-PLAN.md:142, 06.10-06-PLAN.md:67 | EXCLUDED_NEW | Declared phase artifact or prior-plan SUMMARY execution output |
| path `.planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-06-SUMMARY.md` | 06.10-06-PLAN.md:176 | EXCLUDED_NEW | Declared phase artifact or prior-plan SUMMARY execution output |
| path `.planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-ACCEPTANCE.md` | 06.10-06-PLAN.md:15, 06.10-06-PLAN.md:38, 06.10-06-PLAN.md:122 | EXCLUDED_NEW | Declared phase artifact or prior-plan SUMMARY execution output |
| path `.planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-CONTEXT.md` | 06.10-01-PLAN.md:60, 06.10-02-PLAN.md:54, 06.10-03-PLAN.md:58, 06.10-04-PLAN.md:55, 06.10-05-PLAN.md:59, 06.10-06-PLAN.md:63 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `.planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-PATTERNS.md` | 06.10-01-PLAN.md:62, 06.10-02-PLAN.md:55 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `.planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-RESEARCH.md` | 06.10-01-PLAN.md:61, 06.10-03-PLAN.md:59 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `.planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-VALIDATION.md` | 06.10-01-PLAN.md:63, 06.10-06-PLAN.md:16, 06.10-06-PLAN.md:44, 06.10-06-PLAN.md:64, 06.10-06-PLAN.md:122 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `.planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-browser.json` | 06.10-06-PLAN.md:11, 06.10-06-PLAN.md:34, 06.10-06-PLAN.md:102, 06.10-06-PLAN.md:112 | EXCLUDED_NEW | Declared phase artifact or prior-plan SUMMARY execution output |
| path `.planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/06.10-gates.json` | 06.10-06-PLAN.md:14, 06.10-06-PLAN.md:36, 06.10-06-PLAN.md:45, 06.10-06-PLAN.md:122 | EXCLUDED_NEW | Declared phase artifact or prior-plan SUMMARY execution output |
| path `.planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/screenshots/nested-custom.png` | 06.10-06-PLAN.md:13, 06.10-06-PLAN.md:102 | EXCLUDED_NEW | Declared phase artifact or prior-plan SUMMARY execution output |
| path `.planning/phases/06.10-object-derived-nested-urls-and-link-access-parity/screenshots/nested-stock.png` | 06.10-06-PLAN.md:12, 06.10-06-PLAN.md:102 | EXCLUDED_NEW | Declared phase artifact or prior-plan SUMMARY execution output |
| path `.planning/phases/06.7-dynamic-cancel-navigation-and-origin-query-state/06.7-CONTEXT.md` | 06.10-02-PLAN.md:57 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `.planning/phases/06.8-action-tooltips-short-captions-and-visible-label-suppression/06.8-CONTEXT.md` | 06.10-02-PLAN.md:58 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `.planning/phases/06.9-protected-delete-preview-object-links/06.9-01-SUMMARY.md` | 06.10-04-PLAN.md:58 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `.planning/phases/06.9-protected-delete-preview-object-links/06.9-02-SUMMARY.md` | 06.10-04-PLAN.md:59 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `.planning/phases/06.9-protected-delete-preview-object-links/06.9-03-SUMMARY.md` | 06.10-05-PLAN.md:63 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `.planning/phases/06.9-protected-delete-preview-object-links/06.9-04-SUMMARY.md` | 06.10-06-PLAN.md:68 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `.planning/phases/06.9-protected-delete-preview-object-links/06.9-CONTEXT.md` | 06.10-04-PLAN.md:57 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `.planning/phases/06.9-protected-delete-preview-object-links/06.9-VERIFICATION.md` | 06.10-06-PLAN.md:123 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `.venv/bin/mkdocs` | 06.10-05-PLAN.md:111, 06.10-06-PLAN.md:138 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `.venv/bin/ruff` | 06.10-06-PLAN.md:140, 06.10-06-PLAN.md:142 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `/home/alex/.codex/gsd-core/templates/summary.md` | 06.10-01-PLAN.md:51, 06.10-02-PLAN.md:49, 06.10-03-PLAN.md:52, 06.10-04-PLAN.md:50, 06.10-05-PLAN.md:54, 06.10-06-PLAN.md:57 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `/home/alex/.codex/gsd-core/workflows/execute-plan.md` | 06.10-01-PLAN.md:50, 06.10-02-PLAN.md:48, 06.10-03-PLAN.md:51, 06.10-04-PLAN.md:49, 06.10-05-PLAN.md:53, 06.10-06-PLAN.md:56 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `docs/development/stability.md` | 06.10-05-PLAN.md:14, 06.10-05-PLAN.md:35, 06.10-05-PLAN.md:103 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `docs/migrating-1.0.md` | 06.10-05-PLAN.md:9, 06.10-05-PLAN.md:31, 06.10-05-PLAN.md:39, 06.10-05-PLAN.md:69, 06.10-05-PLAN.md:77, 06.10-05-PLAN.md:104, 06.10-06-PLAN.md:83, 06.10-06-PLAN.md:89 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `docs/reference/buttons.md` | 06.10-06-PLAN.md:83, 06.10-06-PLAN.md:89 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `docs/reference/context_buttons.md` | 06.10-05-PLAN.md:12, 06.10-05-PLAN.md:90 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `docs/reference/delete_view.md` | 06.10-05-PLAN.md:13, 06.10-05-PLAN.md:103 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `docs/reference/guardian.md` | 06.10-05-PLAN.md:11, 06.10-05-PLAN.md:41, 06.10-05-PLAN.md:90 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `docs/reference/nested.md` | 06.10-05-PLAN.md:10, 06.10-05-PLAN.md:42, 06.10-05-PLAN.md:90 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `src/crud_views/lib/resource.py` | 06.10-01-PLAN.md:145 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `src/crud_views/lib/view/base.py` | 06.10-01-PLAN.md:10, 06.10-01-PLAN.md:35, 06.10-01-PLAN.md:107, 06.10-01-PLAN.md:108, 06.10-02-PLAN.md:8, 06.10-02-PLAN.md:37, 06.10-02-PLAN.md:82, 06.10-02-PLAN.md:100, 06.10-03-PLAN.md:8, 06.10-03-PLAN.md:88, 06.10-05-PLAN.md:91 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `src/crud_views/lib/view/buttons.py` | 06.10-02-PLAN.md:9, 06.10-02-PLAN.md:33, 06.10-02-PLAN.md:82, 06.10-02-PLAN.md:101 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `src/crud_views/lib/view/link_context.py` | 06.10-02-PLAN.md:10, 06.10-02-PLAN.md:28, 06.10-02-PLAN.md:34, 06.10-02-PLAN.md:63, 06.10-02-PLAN.md:82, 06.10-02-PLAN.md:100, 06.10-03-PLAN.md:37, 06.10-03-PLAN.md:108 | EXCLUDED_NEW | Declared phase artifact or prior-plan SUMMARY execution output |
| path `src/crud_views/lib/views/card.py` | 06.10-02-PLAN.md:11, 06.10-02-PLAN.md:36, 06.10-02-PLAN.md:82, 06.10-02-PLAN.md:101 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `src/crud_views/lib/views/delete.py` | 06.10-04-PLAN.md:8, 06.10-04-PLAN.md:27, 06.10-04-PLAN.md:34, 06.10-04-PLAN.md:37, 06.10-04-PLAN.md:38, 06.10-04-PLAN.md:60, 06.10-04-PLAN.md:73, 06.10-04-PLAN.md:93, 06.10-05-PLAN.md:104 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `src/crud_views/lib/viewset/__init__.py` | 06.10-01-PLAN.md:8, 06.10-01-PLAN.md:30, 06.10-01-PLAN.md:38, 06.10-01-PLAN.md:107, 06.10-01-PLAN.md:108, 06.10-01-PLAN.md:126, 06.10-01-PLAN.md:144, 06.10-02-PLAN.md:83, 06.10-03-PLAN.md:89, 06.10-04-PLAN.md:35, 06.10-04-PLAN.md:74, 06.10-05-PLAN.md:78 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `src/crud_views/lib/viewset/parentviewset.py` | 06.10-01-PLAN.md:39, 06.10-01-PLAN.md:108, 06.10-01-PLAN.md:127 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `src/crud_views/lib/viewset/resolution.py` | 06.10-01-PLAN.md:9, 06.10-01-PLAN.md:28, 06.10-01-PLAN.md:36, 06.10-01-PLAN.md:72, 06.10-01-PLAN.md:107, 06.10-01-PLAN.md:126, 06.10-01-PLAN.md:144, 06.10-02-PLAN.md:83, 06.10-03-PLAN.md:108, 06.10-04-PLAN.md:74 | EXCLUDED_NEW | Declared phase artifact or prior-plan SUMMARY execution output |
| path `src/crud_views_guardian/lib/mixins.py` | 06.10-02-PLAN.md:83, 06.10-03-PLAN.md:9, 06.10-03-PLAN.md:29, 06.10-03-PLAN.md:36, 06.10-03-PLAN.md:40, 06.10-03-PLAN.md:61, 06.10-03-PLAN.md:88, 06.10-03-PLAN.md:107, 06.10-03-PLAN.md:126, 06.10-05-PLAN.md:91 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `src/crud_views_guardian/lib/views.py` | 06.10-02-PLAN.md:83, 06.10-03-PLAN.md:10, 06.10-03-PLAN.md:39, 06.10-03-PLAN.md:62, 06.10-03-PLAN.md:88, 06.10-03-PLAN.md:89, 06.10-03-PLAN.md:107, 06.10-04-PLAN.md:94, 06.10-05-PLAN.md:91 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `tests/browser/action-tooltips.cjs` | 06.10-06-PLAN.md:83 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `tests/browser/cancel-navigation.cjs` | 06.10-06-PLAN.md:83 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `tests/browser/cancel-navigation.test.cjs` | 06.10-06-PLAN.md:91 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `tests/browser/protected-delete.cjs` | 06.10-06-PLAN.md:8, 06.10-06-PLAN.md:32, 06.10-06-PLAN.md:41, 06.10-06-PLAN.md:82, 06.10-06-PLAN.md:93, 06.10-06-PLAN.md:102, 06.10-06-PLAN.md:103, 06.10-06-PLAN.md:112 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `tests/browser/protected-delete.test.cjs` | 06.10-06-PLAN.md:9, 06.10-06-PLAN.md:82, 06.10-06-PLAN.md:91, 06.10-06-PLAN.md:103 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `tests/browser/protected_delete_server.py` | 06.10-06-PLAN.md:10, 06.10-06-PLAN.md:42, 06.10-06-PLAN.md:82, 06.10-06-PLAN.md:103 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `tests/test1/app/models.py` | 06.10-01-PLAN.md:11, 06.10-01-PLAN.md:75, 06.10-01-PLAN.md:126, 06.10-01-PLAN.md:145, 06.10-04-PLAN.md:74 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `tests/test1/app/views.py` | 06.10-01-PLAN.md:108, 06.10-01-PLAN.md:127 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `tests/test1/conftest.py` | 06.10-01-PLAN.md:127 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `tests/test1/test_breadcrumb.py` | 06.10-02-PLAN.md:101, 06.10-02-PLAN.md:111 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `tests/test1/test_cancel_origin.py` | 06.10-02-PLAN.md:101, 06.10-02-PLAN.md:111 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `tests/test1/test_card.py` | 06.10-02-PLAN.md:83 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `tests/test1/test_context_button_permission_filter.py` | 06.10-02-PLAN.md:83 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `tests/test1/test_delete.py` | 06.10-04-PLAN.md:9, 06.10-04-PLAN.md:29, 06.10-04-PLAN.md:73, 06.10-04-PLAN.md:82, 06.10-04-PLAN.md:84, 06.10-04-PLAN.md:93, 06.10-04-PLAN.md:102 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `tests/test1/test_delete_databases.py` | 06.10-04-PLAN.md:11, 06.10-04-PLAN.md:93, 06.10-04-PLAN.md:102 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `tests/test1/test_delete_inspection.py` | 06.10-04-PLAN.md:12, 06.10-04-PLAN.md:93, 06.10-04-PLAN.md:102 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `tests/test1/test_delete_migration_docs.py` | 06.10-04-PLAN.md:94, 06.10-05-PLAN.md:78, 06.10-05-PLAN.md:104, 06.10-05-PLAN.md:109 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `tests/test1/test_form_buttons_golden.py` | 06.10-06-PLAN.md:130 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `tests/test1/test_guardian_composition.py` | 06.10-03-PLAN.md:108, 06.10-03-PLAN.md:127, 06.10-03-PLAN.md:137 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `tests/test1/test_guardian_delete.py` | 06.10-01-PLAN.md:108, 06.10-03-PLAN.md:108, 06.10-04-PLAN.md:10, 06.10-04-PLAN.md:31, 06.10-04-PLAN.md:73, 06.10-04-PLAN.md:82, 06.10-04-PLAN.md:93, 06.10-04-PLAN.md:102 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `tests/test1/test_guardian_link_visibility.py` | 06.10-03-PLAN.md:12, 06.10-03-PLAN.md:33, 06.10-03-PLAN.md:70, 06.10-03-PLAN.md:107, 06.10-03-PLAN.md:117, 06.10-03-PLAN.md:126, 06.10-03-PLAN.md:135, 06.10-06-PLAN.md:83 | EXCLUDED_NEW | Declared phase artifact or prior-plan SUMMARY execution output |
| path `tests/test1/test_guardian_parent_none.py` | 06.10-03-PLAN.md:89, 06.10-03-PLAN.md:108, 06.10-03-PLAN.md:127, 06.10-03-PLAN.md:137 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `tests/test1/test_guardian_policy.py` | 06.10-03-PLAN.md:89, 06.10-03-PLAN.md:127, 06.10-03-PLAN.md:137 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `tests/test1/test_link_access_parity.py` | 06.10-03-PLAN.md:11, 06.10-03-PLAN.md:31, 06.10-03-PLAN.md:70, 06.10-03-PLAN.md:88, 06.10-03-PLAN.md:98 | EXCLUDED_NEW | Declared phase artifact or prior-plan SUMMARY execution output |
| path `tests/test1/test_nested_url_docs.py` | 06.10-05-PLAN.md:15, 06.10-05-PLAN.md:33, 06.10-05-PLAN.md:38, 06.10-05-PLAN.md:68, 06.10-05-PLAN.md:77, 06.10-05-PLAN.md:81, 06.10-05-PLAN.md:90, 06.10-05-PLAN.md:94, 06.10-05-PLAN.md:103, 06.10-05-PLAN.md:107 | EXCLUDED_NEW | Declared phase artifact or prior-plan SUMMARY execution output |
| path `tests/test1/test_nested_url_rendering.py` | 06.10-02-PLAN.md:12, 06.10-02-PLAN.md:30, 06.10-02-PLAN.md:65, 06.10-02-PLAN.md:82, 06.10-02-PLAN.md:91, 06.10-02-PLAN.md:100, 06.10-02-PLAN.md:109, 06.10-06-PLAN.md:83 | EXCLUDED_NEW | Declared phase artifact or prior-plan SUMMARY execution output |
| path `tests/test1/test_nested_url_resolution.py` | 06.10-01-PLAN.md:12, 06.10-01-PLAN.md:32, 06.10-01-PLAN.md:74, 06.10-01-PLAN.md:107, 06.10-01-PLAN.md:117, 06.10-01-PLAN.md:126, 06.10-01-PLAN.md:135, 06.10-01-PLAN.md:144, 06.10-01-PLAN.md:154, 06.10-04-PLAN.md:74, 06.10-05-PLAN.md:78 | EXCLUDED_NEW | Declared phase artifact or prior-plan SUMMARY execution output |
| path `tests/test1/test_nested_viewset.py` | 06.10-01-PLAN.md:108 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `tests/test1/test_resource_views.py` | 06.10-01-PLAN.md:145 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `tests/test1/test_resource_viewset.py` | 06.10-01-PLAN.md:145 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `tests/test1/test_success_origin.py` | 06.10-02-PLAN.md:101, 06.10-02-PLAN.md:111 | VERIFIED | Filesystem existence; source contents reviewed separately |
| path `tests/test1/test_viewset.py` | 06.10-03-PLAN.md:89 | VERIFIED | Filesystem existence; source contents reviewed separately |
| symbol `ChildContextButton` | 06.10-02-PLAN.md:86, 06.10-02-PLAN.md:89 | UNCHECKABLE | Supplemental declaration locations: src/crud_views/lib/view/buttons.py:203 |
| symbol `ContextButton` | 06.10-02-PLAN.md:86, 06.10-02-PLAN.md:89 | UNCHECKABLE | Supplemental declaration locations: src/crud_views/lib/view/buttons.py:29 |
| symbol `ContextVar` | 06.10-02-PLAN.md:63, 06.10-02-PLAN.md:70, 06.10-02-PLAN.md:74, 06.10-02-PLAN.md:104, 06.10-02-PLAN.md:129 | UNCHECKABLE | Not indexed by empty intel surface; external/library/field/CLI references not verified by authority |
| symbol `GuardianParentPermissionMixin` | 06.10-03-PLAN.md:67, 06.10-03-PLAN.md:69, 06.10-05-PLAN.md:70 | UNCHECKABLE | Supplemental declaration locations: src/crud_views_guardian/lib/mixins.py:215 |
| symbol `ImproperlyConfigured` | 06.10-03-PLAN.md:68, 06.10-03-PLAN.md:96 | UNCHECKABLE | Not indexed by empty intel surface; external/library/field/CLI references not verified by authority |
| symbol `NoReverseMatch` | 06.10-01-PLAN.md:93, 06.10-01-PLAN.md:99, 06.10-01-PLAN.md:150, 06.10-05-PLAN.md:27, 06.10-05-PLAN.md:84, 06.10-05-PLAN.md:92 | UNCHECKABLE | Not indexed by empty intel surface; external/library/field/CLI references not verified by authority |
| symbol `ObjectDoesNotExist` | 06.10-01-PLAN.md:99, 06.10-01-PLAN.md:150 | UNCHECKABLE | Not indexed by empty intel surface; external/library/field/CLI references not verified by authority |
| symbol `ParentContextButton` | 06.10-02-PLAN.md:87 | UNCHECKABLE | Supplemental declaration locations: src/crud_views/lib/view/buttons.py:132 |
| symbol `ParentViewSet` | 06.10-01-PLAN.md:133 | UNCHECKABLE | Supplemental declaration locations: src/crud_views/lib/viewset/parentviewset.py:13 |
| symbol `SiblingContextButton` | 06.10-02-PLAN.md:87 | UNCHECKABLE | Supplemental declaration locations: src/crud_views/lib/view/buttons.py:255 |
| symbol `ViewSet` | 06.10-01-PLAN.md:46, 06.10-01-PLAN.md:73, 06.10-01-PLAN.md:114, 06.10-02-PLAN.md:70, 06.10-03-PLAN.md:68, 06.10-03-PLAN.md:91, 06.10-03-PLAN.md:96, 06.10-05-PLAN.md:70 | UNCHECKABLE | Supplemental declaration locations: src/crud_views/lib/viewset/__init__.py:47 |
| symbol `_LinkDestinationContext` | 06.10-02-PLAN.md:63 | EXCLUDED_NEW | Declared phase artifact or prior-plan SUMMARY execution output |
| symbol `_ParentResolution` | 06.10-01-PLAN.md:72, 06.10-05-PLAN.md:105 | EXCLUDED_NEW | Declared phase artifact or prior-plan SUMMARY execution output |
| symbol `_assemble_destination` | 06.10-01-PLAN.md:72 | EXCLUDED_NEW | Declared phase artifact or prior-plan SUMMARY execution output |
| symbol `_cv_cancel_target_available` | 06.10-03-PLAN.md:82, 06.10-03-PLAN.md:115 | UNCHECKABLE | Supplemental declaration locations: src/crud_views/lib/view/base.py:850, src/crud_views_guardian/lib/mixins.py:46, src/crud_views_guardian/lib/mixins.py:125, src/crud_views_guardian/lib/mixins.py:248 |
| symbol `_cv_get_action_context` | 06.10-02-PLAN.md:89 | UNCHECKABLE | Supplemental declaration locations: src/crud_views/lib/view/base.py:735 |
| symbol `_cv_get_protected_object_url` | 06.10-04-PLAN.md:39, 06.10-04-PLAN.md:80 | UNCHECKABLE | Supplemental declaration locations: src/crud_views/lib/views/delete.py:212 |
| symbol `_cv_guardian_create_parent` | 06.10-03-PLAN.md:115 | UNCHECKABLE | Supplemental declaration locations: src/crud_views_guardian/lib/views.py:275 |
| symbol `_get_link_parent_resolution` | 06.10-02-PLAN.md:64 | EXCLUDED_NEW | Declared phase artifact or prior-plan SUMMARY execution output |
| symbol `_guardian_declared_permission` | 06.10-03-PLAN.md:68 | EXCLUDED_NEW | Declared phase artifact or prior-plan SUMMARY execution output |
| symbol `_guardian_user_has_parent_perm` | 06.10-03-PLAN.md:67 | UNCHECKABLE | Supplemental declaration locations: src/crud_views_guardian/lib/mixins.py:348 |
| symbol `_link_destination_scope` | 06.10-02-PLAN.md:64 | EXCLUDED_NEW | Declared phase artifact or prior-plan SUMMARY execution output |
| symbol `_publish_link_parent_resolution` | 06.10-02-PLAN.md:64 | EXCLUDED_NEW | Declared phase artifact or prior-plan SUMMARY execution output |
| symbol `_resolve_parent_chain` | 06.10-01-PLAN.md:72, 06.10-01-PLAN.md:114, 06.10-01-PLAN.md:172 | EXCLUDED_NEW | Declared phase artifact or prior-plan SUMMARY execution output |
| symbol `clear_url_caches` | 06.10-01-PLAN.md:133 | UNCHECKABLE | Not indexed by empty intel surface; external/library/field/CLI references not verified by authority |
| symbol `cv_create_has_access` | 06.10-03-PLAN.md:80, 06.10-03-PLAN.md:112 | UNCHECKABLE | Supplemental declaration locations: src/crud_views_guardian/lib/views.py:310, tests/test1/test_cancel_permissions.py:472 |
| symbol `cv_get_child_url` | 06.10-02-PLAN.md:72, 06.10-02-PLAN.md:89 | UNCHECKABLE | Supplemental declaration locations: src/crud_views/lib/view/base.py:985 |
| symbol `cv_get_link_url` | 06.10-01-PLAN.md:114 | UNCHECKABLE | Supplemental declaration locations: src/crud_views/lib/view/base.py:958 |
| symbol `cv_get_parent_object` | 06.10-02-PLAN.md:105 | UNCHECKABLE | Supplemental declaration locations: src/crud_views/lib/view/base.py:1023 |
| symbol `cv_get_related_object_url` | 06.10-04-PLAN.md:36, 06.10-04-PLAN.md:65, 06.10-04-PLAN.md:80, 06.10-05-PLAN.md:105 | UNCHECKABLE | Supplemental declaration locations: src/crud_views/lib/views/delete.py:192 |
| symbol `cv_get_router_and_args` | 06.10-01-PLAN.md:37, 06.10-01-PLAN.md:114, 06.10-02-PLAN.md:72, 06.10-02-PLAN.md:103 | UNCHECKABLE | Supplemental declaration locations: src/crud_views/lib/view/base.py:576 |
| symbol `cv_get_url` | 06.10-01-PLAN.md:114, 06.10-02-PLAN.md:103 | UNCHECKABLE | Supplemental declaration locations: src/crud_views/lib/view/base.py:611 |
| symbol `cv_get_url_extra_kwargs` | 06.10-02-PLAN.md:103 | UNCHECKABLE | Supplemental declaration locations: src/crud_views/lib/views/child.py:27, src/crud_views/lib/view/base.py:559 |
| symbol `cv_guardian_has_parent_access` | 06.10-03-PLAN.md:67, 06.10-03-PLAN.md:115, 06.10-05-PLAN.md:70 | EXCLUDED_NEW | Declared phase artifact or prior-plan SUMMARY execution output |
| symbol `cv_has_access` | 06.10-02-PLAN.md:70, 06.10-02-PLAN.md:76, 06.10-02-PLAN.md:107, 06.10-03-PLAN.md:38, 06.10-03-PLAN.md:69, 06.10-03-PLAN.md:113 | UNCHECKABLE | Supplemental declaration locations: src/crud_views/lib/view/base.py:398, src/crud_views/lib/view/base.py:1085, src/crud_views_guardian/lib/views.py:344, src/crud_views_guardian/lib/mixins.py:85, src/crud_views_guardian/lib/mixins.py:143, tests/test1/test_cancel_quality.py:74 |
| symbol `cv_object` | 06.10-01-PLAN.md:80 | UNCHECKABLE | Not indexed by empty intel surface; external/library/field/CLI references not verified by authority |
| symbol `get_attribute` | 06.10-01-PLAN.md:40 | UNCHECKABLE | Supplemental declaration locations: src/crud_views/lib/viewset/parentviewset.py:62 |
| symbol `get_objects_for_user` | 06.10-03-PLAN.md:96 | UNCHECKABLE | Supplemental declaration locations: src/crud_views_guardian/lib/viewset.py:122 |
| symbol `get_parent_pks` | 06.10-01-PLAN.md:31, 06.10-01-PLAN.md:73, 06.10-05-PLAN.md:70 | EXCLUDED_NEW | Declared phase artifact or prior-plan SUMMARY execution output |
| symbol `get_pk_name` | 06.10-01-PLAN.md:40 | UNCHECKABLE | Supplemental declaration locations: src/crud_views/lib/viewset/parentviewset.py:56 |
| symbol `get_url` | 06.10-01-PLAN.md:25, 06.10-01-PLAN.md:31, 06.10-01-PLAN.md:73, 06.10-02-PLAN.md:70, 06.10-04-PLAN.md:22, 06.10-04-PLAN.md:36, 06.10-04-PLAN.md:80, 06.10-05-PLAN.md:70 | EXCLUDED_NEW | Declared phase artifact or prior-plan SUMMARY execution output |
| symbol `select_related` | 06.10-01-PLAN.md:133, 06.10-05-PLAN.md:92 | UNCHECKABLE | Not indexed by empty intel surface; external/library/field/CLI references not verified by authority |
| symbol/field `_PermittedPks` | 06.10-04-PLAN.md:94 | UNCHECKABLE | Python field/library callable/runtime reference is unsupported by empty intel surface; signatures are not verified |
| symbol/field `field.target_field` | 06.10-01-PLAN.md:133 | UNCHECKABLE | Python field/library callable/runtime reference is unsupported by empty intel surface; signatures are not verified |
| symbol/field `db_column` | 06.10-01-PLAN.md:75, 06.10-01-PLAN.md:130 | UNCHECKABLE | Python field/library callable/runtime reference is unsupported by empty intel surface; signatures are not verified |
| symbol/field `attname` | 06.10-01-PLAN.md:133 | UNCHECKABLE | Python field/library callable/runtime reference is unsupported by empty intel surface; signatures are not verified |
| symbol/field `inspect.signature` | 06.10-05-PLAN.md:95 | UNCHECKABLE | Python field/library callable/runtime reference is unsupported by empty intel surface; signatures are not verified |
| symbol/field `reverse` | 06.10-01-PLAN.md:25, 06.10-01-PLAN.md:93, 06.10-01-PLAN.md:97, 06.10-01-PLAN.md:114, 06.10-01-PLAN.md:147, 06.10-01-PLAN.md:152, 06.10-01-PLAN.md:168 | UNCHECKABLE | Python field/library callable/runtime reference is unsupported by empty intel surface; signatures are not verified |
| symbol/field `pk` | 06.10-01-PLAN.md:133 | UNCHECKABLE | Python field/library callable/runtime reference is unsupported by empty intel surface; signatures are not verified |
| symbol/field `asyncio` | 06.10-02-PLAN.md:74, 06.10-02-PLAN.md:104 | UNCHECKABLE | Python field/library callable/runtime reference is unsupported by empty intel surface; signatures are not verified |
