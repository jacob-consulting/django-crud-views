# Cycle 1 source-grounding coverage

Effective authority: `intel`. `.planning/intel/API-SURFACE.md:5-6` reports an empty JS-only index. Existing Python/template/CLI/path references are UNCHECKABLE; literal declaration/path observations are supplemental evidence, never signature verification. New artifacts are excluded. Full quoted plan lines and supplemental declarations appear in source-grounding.json.

| Kind | Symbol | Verdict | Plan-line provenance |
|---|---|---|---|
| CLI flag | `--check` | UNCHECKABLE | 06.40-04-PLAN.md:108, 06.40-04-PLAN.md:111, 06.40-07-PLAN.md:93, 06.40-08-PLAN.md:109 |
| CLI flag | `--dry-run` | UNCHECKABLE | 06.40-04-PLAN.md:108, 06.40-04-PLAN.md:111 |
| CLI flag | `--noreload` | UNCHECKABLE | 06.40-08-PLAN.md:89 |
| CLI flag | `--oneline` | UNCHECKABLE | 06.40-07-PLAN.md:93 |
| CLI flag | `--settings` | UNCHECKABLE | 06.40-08-PLAN.md:89 |
| CLI flag | `--strict` | UNCHECKABLE | 06.40-06-PLAN.md:109, 06.40-08-PLAN.md:107 |
| call/signature | `_cv_action_enabled_for_rendering` | UNCHECKABLE | 06.40-03-PLAN.md:79 |
| call/signature | `_resolved_ancestor` | UNCHECKABLE | 06.40-01-PLAN.md:95 |
| call/signature | `parent.get_pk_name` | UNCHECKABLE | 06.40-01-PLAN.md:95 |
| call/signature | `target._cv_child_link_has_access` | UNCHECKABLE | 06.40-03-PLAN.md:79 |
| call/signature | `target.cv_has_access` | UNCHECKABLE | 06.40-03-PLAN.md:79 |
| file | `../../.pytest_cache` | UNCHECKABLE | 06.40-08-PLAN.md:89 |
| file | `../../src` | UNCHECKABLE | 06.40-04-PLAN.md:107, 06.40-08-PLAN.md:89 |
| file | `../skills-navbar-06-40` | SKIPPED | 06.40-07-PLAN.md:79, 06.40-07-PLAN.md:93 |
| file | `../skills-navbar-06-40/.github/workflows/validate.yml` | SKIPPED | 06.40-07-PLAN.md:89 |
| file | `../skills-navbar-06-40/plugins/django-crud-views/CHANGELOG.md` | SKIPPED | 06.40-07-PLAN.md:7, 06.40-07-PLAN.md:27, 06.40-07-PLAN.md:69, 06.40-07-PLAN.md:77 |
| file | `../skills-navbar-06-40/plugins/django-crud-views/skills/django-crud-views/SKILL.md` | SKIPPED | 06.40-07-PLAN.md:7, 06.40-07-PLAN.md:21, 06.40-07-PLAN.md:36, 06.40-07-PLAN.md:66, 06.40-07-PLAN.md:77 |
| file | `../skills-navbar-06-40/plugins/django-crud-views/skills/django-crud-views/references/api-reference.md` | SKIPPED | 06.40-07-PLAN.md:7, 06.40-07-PLAN.md:25, 06.40-07-PLAN.md:68, 06.40-07-PLAN.md:77 |
| file | `../skills-navbar-06-40/plugins/django-crud-views/skills/django-crud-views/references/templates-and-navigation.md` | SKIPPED | 06.40-07-PLAN.md:7, 06.40-07-PLAN.md:23, 06.40-07-PLAN.md:33, 06.40-07-PLAN.md:67, 06.40-07-PLAN.md:77 |
| file | `../skills-navbar-06-40/scripts/validate.py` | SKIPPED | 06.40-07-PLAN.md:81, 06.40-07-PLAN.md:89, 06.40-07-PLAN.md:92 |
| file | `.nox/examples-3-12-django-5-2/bin/python` | UNCHECKABLE | 06.40-04-PLAN.md:107, 06.40-08-PLAN.md:89 |
| file | `.nox/tests-3-12-django-4-2/bin/python` | UNCHECKABLE | 06.40-08-PLAN.md:103 |
| file | `.nox/tests-3-12-django-5-2/bin/python` | UNCHECKABLE | 06.40-01-PLAN.md:85, 06.40-01-PLAN.md:97, 06.40-01-PLAN.md:109, 06.40-02-PLAN.md:87, 06.40-02-PLAN.md:99, 06.40-03-PLAN.md:81, 06.40-03-PLAN.md:93, 06.40-06-PLAN.md:122, 06.40-08-PLAN.md:102 |
| file | `.nox/tests-3-12-django-6-0/bin/python` | UNCHECKABLE | 06.40-08-PLAN.md:104 |
| file | `.planning/PROJECT.md` | UNCHECKABLE | 06.40-01-PLAN.md:57, 06.40-02-PLAN.md:59, 06.40-03-PLAN.md:54, 06.40-04-PLAN.md:65, 06.40-05-PLAN.md:71, 06.40-06-PLAN.md:74, 06.40-07-PLAN.md:54, 06.40-08-PLAN.md:62 |
| file | `.planning/ROADMAP.md` | UNCHECKABLE | 06.40-01-PLAN.md:58, 06.40-02-PLAN.md:60, 06.40-03-PLAN.md:55, 06.40-04-PLAN.md:66, 06.40-05-PLAN.md:72, 06.40-06-PLAN.md:75, 06.40-07-PLAN.md:55, 06.40-08-PLAN.md:63 |
| file | `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-SUMMARY.md` | SKIPPED | 06.40-01-PLAN.md:142 |
| file | `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-SUMMARY.md` | SKIPPED | 06.40-02-PLAN.md:131 |
| file | `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-SUMMARY.md` | SKIPPED | 06.40-03-PLAN.md:126 |
| file | `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-SUMMARY.md` | SKIPPED | 06.40-04-PLAN.md:141 |
| file | `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-SUMMARY.md` | SKIPPED | 06.40-05-PLAN.md:162 |
| file | `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-SUMMARY.md` | SKIPPED | 06.40-06-PLAN.md:165 |
| file | `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-SUMMARY.md` | SKIPPED | 06.40-07-PLAN.md:125 |
| file | `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-SUMMARY.md` | SKIPPED | 06.40-08-PLAN.md:143 |
| file | `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-ACCEPTANCE.md` | SKIPPED | 06.40-08-PLAN.md:7, 06.40-08-PLAN.md:32, 06.40-08-PLAN.md:40, 06.40-08-PLAN.md:43, 06.40-08-PLAN.md:79, 06.40-08-PLAN.md:98 |
| file | `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-BROWSER-CHECK.js` | SKIPPED | 06.40-08-PLAN.md:7, 06.40-08-PLAN.md:22, 06.40-08-PLAN.md:37, 06.40-08-PLAN.md:74, 06.40-08-PLAN.md:87, 06.40-08-PLAN.md:91 |
| file | `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-BROWSER.json` | SKIPPED | 06.40-08-PLAN.md:7, 06.40-08-PLAN.md:24, 06.40-08-PLAN.md:75, 06.40-08-PLAN.md:87, 06.40-08-PLAN.md:91 |
| file | `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-COMPANION-DELIVERY.md` | SKIPPED | 06.40-07-PLAN.md:7, 06.40-07-PLAN.md:29, 06.40-07-PLAN.md:35, 06.40-07-PLAN.md:70, 06.40-07-PLAN.md:77, 06.40-07-PLAN.md:88, 06.40-07-PLAN.md:89, 06.40-08-PLAN.md:44 |
| file | `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-COMPANION-GUIDANCE.md` | UNCHECKABLE | 06.40-07-PLAN.md:78 |
| file | `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-CONTEXT.md` | UNCHECKABLE | 06.40-01-PLAN.md:59, 06.40-02-PLAN.md:61, 06.40-03-PLAN.md:56, 06.40-04-PLAN.md:67, 06.40-05-PLAN.md:73, 06.40-06-PLAN.md:76, 06.40-07-PLAN.md:56, 06.40-08-PLAN.md:64 |
| file | `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-COST.md` | SKIPPED | 06.40-03-PLAN.md:7, 06.40-03-PLAN.md:27, 06.40-03-PLAN.md:68, 06.40-03-PLAN.md:88, 06.40-06-PLAN.md:56, 06.40-06-PLAN.md:106 |
| file | `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-ISSUE-381.md` | UNCHECKABLE | 06.40-01-PLAN.md:60, 06.40-02-PLAN.md:62, 06.40-03-PLAN.md:57, 06.40-04-PLAN.md:68, 06.40-05-PLAN.md:74, 06.40-06-PLAN.md:77, 06.40-07-PLAN.md:57, 06.40-08-PLAN.md:65 |
| file | `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-PATTERNS.md` | UNCHECKABLE | 06.40-01-PLAN.md:62, 06.40-02-PLAN.md:64, 06.40-03-PLAN.md:59, 06.40-04-PLAN.md:70, 06.40-05-PLAN.md:76, 06.40-06-PLAN.md:79, 06.40-07-PLAN.md:59, 06.40-08-PLAN.md:67 |
| file | `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-RESEARCH.md` | UNCHECKABLE | 06.40-01-PLAN.md:61, 06.40-02-PLAN.md:63, 06.40-03-PLAN.md:58, 06.40-04-PLAN.md:69, 06.40-05-PLAN.md:75, 06.40-06-PLAN.md:78, 06.40-07-PLAN.md:58, 06.40-08-PLAN.md:66 |
| file | `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-UI-PROBE.json` | UNCHECKABLE | 06.40-02-PLAN.md:95, 06.40-08-PLAN.md:88 |
| file | `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-UI-SPEC.md` | UNCHECKABLE | 06.40-01-PLAN.md:63, 06.40-02-PLAN.md:65, 06.40-02-PLAN.md:83, 06.40-03-PLAN.md:60, 06.40-04-PLAN.md:71, 06.40-05-PLAN.md:77, 06.40-05-PLAN.md:125, 06.40-06-PLAN.md:80, 06.40-06-PLAN.md:106, 06.40-07-PLAN.md:60, 06.40-08-PLAN.md:68, 06.40-08-PLAN.md:88 |
| file | `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-VALIDATION.md` | UNCHECKABLE | 06.40-01-PLAN.md:64, 06.40-02-PLAN.md:66, 06.40-03-PLAN.md:61, 06.40-04-PLAN.md:72, 06.40-05-PLAN.md:78, 06.40-06-PLAN.md:81, 06.40-07-PLAN.md:61, 06.40-08-PLAN.md:7, 06.40-08-PLAN.md:34, 06.40-08-PLAN.md:69, 06.40-08-PLAN.md:80, 06.40-08-PLAN.md:98, 06.40-08-PLAN.md:99 |
| file | `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-desktop.png` | SKIPPED | 06.40-08-PLAN.md:7, 06.40-08-PLAN.md:26, 06.40-08-PLAN.md:76, 06.40-08-PLAN.md:87 |
| file | `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-narrow-focus.png` | SKIPPED | 06.40-08-PLAN.md:7, 06.40-08-PLAN.md:28, 06.40-08-PLAN.md:77, 06.40-08-PLAN.md:87 |
| file | `.pytest_cache/navbar_browser_settings.py` | SKIPPED | 06.40-08-PLAN.md:7, 06.40-08-PLAN.md:30, 06.40-08-PLAN.md:78, 06.40-08-PLAN.md:87 |
| file | `.venv/bin/mkdocs` | UNCHECKABLE | 06.40-06-PLAN.md:109, 06.40-08-PLAN.md:107 |
| file | `.venv/bin/nox` | UNCHECKABLE | 06.40-04-PLAN.md:97, 06.40-04-PLAN.md:109, 06.40-05-PLAN.md:105, 06.40-05-PLAN.md:117, 06.40-05-PLAN.md:129, 06.40-06-PLAN.md:133, 06.40-08-PLAN.md:105, 06.40-08-PLAN.md:106, 06.40-08-PLAN.md:111 |
| file | `.venv/bin/python` | UNCHECKABLE | 06.40-07-PLAN.md:81, 06.40-07-PLAN.md:92 |
| file | `.venv/bin/ruff` | UNCHECKABLE | 06.40-08-PLAN.md:108, 06.40-08-PLAN.md:109 |
| file | `/home/alex/.codex/gsd-core/templates/summary.md` | UNCHECKABLE | 06.40-01-PLAN.md:52, 06.40-02-PLAN.md:54, 06.40-03-PLAN.md:49, 06.40-04-PLAN.md:60, 06.40-05-PLAN.md:66, 06.40-06-PLAN.md:69, 06.40-07-PLAN.md:49, 06.40-08-PLAN.md:57 |
| file | `/home/alex/.codex/gsd-core/workflows/execute-plan.md` | UNCHECKABLE | 06.40-01-PLAN.md:51, 06.40-02-PLAN.md:53, 06.40-03-PLAN.md:48, 06.40-04-PLAN.md:59, 06.40-05-PLAN.md:65, 06.40-06-PLAN.md:68, 06.40-07-PLAN.md:48, 06.40-08-PLAN.md:56 |
| file | `AGENTS.md/CLAUDE.md` | UNCHECKABLE | 06.40-07-PLAN.md:79 |
| file | `docs/development/index.md` | UNCHECKABLE | 06.40-07-PLAN.md:78 |
| file | `docs/development/stability.md` | UNCHECKABLE | 06.40-06-PLAN.md:7, 06.40-06-PLAN.md:32, 06.40-06-PLAN.md:52, 06.40-06-PLAN.md:91, 06.40-06-PLAN.md:117, 06.40-06-PLAN.md:118, 06.40-07-PLAN.md:78 |
| file | `docs/getting_started/demo.md` | UNCHECKABLE | 06.40-06-PLAN.md:7, 06.40-06-PLAN.md:46, 06.40-06-PLAN.md:98, 06.40-06-PLAN.md:129, 06.40-06-PLAN.md:130 |
| file | `docs/migrating-1.0.md` | UNCHECKABLE | 06.40-06-PLAN.md:120 |
| file | `docs/reference/breadcrumb.md` | UNCHECKABLE | 06.40-06-PLAN.md:7, 06.40-06-PLAN.md:30, 06.40-06-PLAN.md:90, 06.40-06-PLAN.md:105, 06.40-06-PLAN.md:106 |
| file | `docs/reference/context_buttons.md` | UNCHECKABLE | 06.40-03-PLAN.md:89, 06.40-06-PLAN.md:7, 06.40-06-PLAN.md:28, 06.40-06-PLAN.md:89, 06.40-06-PLAN.md:105, 06.40-06-PLAN.md:106 |
| file | `docs/reference/index.md` | UNCHECKABLE | 06.40-06-PLAN.md:7, 06.40-06-PLAN.md:24, 06.40-06-PLAN.md:87, 06.40-06-PLAN.md:105 |
| file | `docs/reference/navbar.md` | SKIPPED | 06.40-06-PLAN.md:7, 06.40-06-PLAN.md:22, 06.40-06-PLAN.md:50, 06.40-06-PLAN.md:55, 06.40-06-PLAN.md:86, 06.40-06-PLAN.md:105, 06.40-06-PLAN.md:107, 06.40-06-PLAN.md:130, 06.40-07-PLAN.md:32, 06.40-07-PLAN.md:78, 06.40-07-PLAN.md:89 |
| file | `docs/reference/nested.md` | UNCHECKABLE | 06.40-06-PLAN.md:7, 06.40-06-PLAN.md:26, 06.40-06-PLAN.md:88, 06.40-06-PLAN.md:105, 06.40-06-PLAN.md:106 |
| file | `docs/reference/templates.md` | UNCHECKABLE | 06.40-06-PLAN.md:7, 06.40-06-PLAN.md:34, 06.40-06-PLAN.md:92, 06.40-06-PLAN.md:117, 06.40-06-PLAN.md:118 |
| file | `docs/reference/theme.md` | UNCHECKABLE | 06.40-06-PLAN.md:7, 06.40-06-PLAN.md:36, 06.40-06-PLAN.md:93, 06.40-06-PLAN.md:117, 06.40-06-PLAN.md:118 |
| file | `examples/bootstrap5/guardian_demo/seed.py` | UNCHECKABLE | 06.40-05-PLAN.md:113 |
| file | `examples/bootstrap5/guardian_demo/views.py` | UNCHECKABLE | 06.40-04-PLAN.md:93 |
| file | `examples/bootstrap5/navbar_demo/__init__.py` | SKIPPED | 06.40-04-PLAN.md:7, 06.40-04-PLAN.md:21, 06.40-04-PLAN.md:77, 06.40-04-PLAN.md:92 |
| file | `examples/bootstrap5/navbar_demo/migrations/0001_initial.py` | SKIPPED | 06.40-04-PLAN.md:7, 06.40-04-PLAN.md:33, 06.40-04-PLAN.md:83, 06.40-04-PLAN.md:104 |
| file | `examples/bootstrap5/navbar_demo/migrations/0002_order_item_address.py` | SKIPPED | 06.40-05-PLAN.md:7, 06.40-05-PLAN.md:29, 06.40-05-PLAN.md:86, 06.40-05-PLAN.md:100 |
| file | `examples/bootstrap5/navbar_demo/migrations/__init__.py` | SKIPPED | 06.40-04-PLAN.md:7, 06.40-04-PLAN.md:31, 06.40-04-PLAN.md:82, 06.40-04-PLAN.md:104 |
| file | `examples/bootstrap5/navbar_demo/models.py` | SKIPPED | 06.40-04-PLAN.md:7, 06.40-04-PLAN.md:23, 06.40-04-PLAN.md:78, 06.40-04-PLAN.md:92, 06.40-05-PLAN.md:7, 06.40-05-PLAN.md:23, 06.40-05-PLAN.md:83, 06.40-05-PLAN.md:100 |
| file | `examples/bootstrap5/navbar_demo/seed.py` | SKIPPED | 06.40-05-PLAN.md:7, 06.40-05-PLAN.md:31, 06.40-05-PLAN.md:46, 06.40-05-PLAN.md:87, 06.40-05-PLAN.md:112, 06.40-08-PLAN.md:88 |
| file | `examples/bootstrap5/navbar_demo/templates/navbar_demo/home.html` | SKIPPED | 06.40-05-PLAN.md:7, 06.40-05-PLAN.md:33, 06.40-05-PLAN.md:88, 06.40-05-PLAN.md:124 |
| file | `examples/bootstrap5/navbar_demo/tests.py` | SKIPPED | 06.40-04-PLAN.md:7, 06.40-04-PLAN.md:29, 06.40-04-PLAN.md:81, 06.40-04-PLAN.md:92, 06.40-04-PLAN.md:104, 06.40-05-PLAN.md:7, 06.40-05-PLAN.md:35, 06.40-05-PLAN.md:89, 06.40-05-PLAN.md:100, 06.40-05-PLAN.md:112, 06.40-05-PLAN.md:124 |
| file | `examples/bootstrap5/navbar_demo/urls.py` | SKIPPED | 06.40-04-PLAN.md:7, 06.40-04-PLAN.md:27, 06.40-04-PLAN.md:41, 06.40-04-PLAN.md:80, 06.40-04-PLAN.md:104, 06.40-05-PLAN.md:7, 06.40-05-PLAN.md:27, 06.40-05-PLAN.md:50, 06.40-05-PLAN.md:85, 06.40-05-PLAN.md:100, 06.40-08-PLAN.md:38 |
| file | `examples/bootstrap5/navbar_demo/views.py` | SKIPPED | 06.40-04-PLAN.md:7, 06.40-04-PLAN.md:25, 06.40-04-PLAN.md:43, 06.40-04-PLAN.md:46, 06.40-04-PLAN.md:79, 06.40-04-PLAN.md:92, 06.40-05-PLAN.md:7, 06.40-05-PLAN.md:25, 06.40-05-PLAN.md:84, 06.40-05-PLAN.md:100, 06.40-05-PLAN.md:124, 06.40-08-PLAN.md:88 |
| file | `examples/bootstrap5/nested/migrations/0001_initial.py` | UNCHECKABLE | 06.40-04-PLAN.md:105 |
| file | `examples/bootstrap5/nested/models.py` | UNCHECKABLE | 06.40-04-PLAN.md:93, 06.40-05-PLAN.md:101 |
| file | `examples/bootstrap5/nested/seed.py` | UNCHECKABLE | 06.40-05-PLAN.md:113 |
| file | `examples/bootstrap5/nested/tests.py` | UNCHECKABLE | 06.40-04-PLAN.md:93, 06.40-05-PLAN.md:101 |
| file | `examples/bootstrap5/nested/urls.py` | UNCHECKABLE | 06.40-04-PLAN.md:105 |
| file | `examples/bootstrap5/nested/views.py` | UNCHECKABLE | 06.40-04-PLAN.md:93, 06.40-05-PLAN.md:101 |
| file | `examples/bootstrap5/project/features.py` | UNCHECKABLE | 06.40-05-PLAN.md:7, 06.40-05-PLAN.md:41, 06.40-05-PLAN.md:49, 06.40-05-PLAN.md:92, 06.40-05-PLAN.md:124, 06.40-05-PLAN.md:125, 06.40-06-PLAN.md:7, 06.40-06-PLAN.md:42, 06.40-06-PLAN.md:49, 06.40-06-PLAN.md:96, 06.40-06-PLAN.md:129, 06.40-06-PLAN.md:130 |
| file | `examples/bootstrap5/project/management/commands/seed.py` | UNCHECKABLE | 06.40-05-PLAN.md:7, 06.40-05-PLAN.md:39, 06.40-05-PLAN.md:91, 06.40-05-PLAN.md:112, 06.40-05-PLAN.md:113 |
| file | `examples/bootstrap5/project/seeding.py` | UNCHECKABLE | 06.40-05-PLAN.md:7, 06.40-05-PLAN.md:37, 06.40-05-PLAN.md:47, 06.40-05-PLAN.md:90, 06.40-05-PLAN.md:112, 06.40-05-PLAN.md:113 |
| file | `examples/bootstrap5/project/settings.py` | UNCHECKABLE | 06.40-04-PLAN.md:7, 06.40-04-PLAN.md:35, 06.40-04-PLAN.md:84, 06.40-04-PLAN.md:92, 06.40-04-PLAN.md:93, 06.40-08-PLAN.md:88 |
| file | `examples/bootstrap5/project/templates/project/crud_views.html` | UNCHECKABLE | 06.40-05-PLAN.md:7, 06.40-05-PLAN.md:43, 06.40-05-PLAN.md:52, 06.40-05-PLAN.md:93, 06.40-05-PLAN.md:124, 06.40-05-PLAN.md:125 |
| file | `examples/bootstrap5/project/templates/project/home.html` | UNCHECKABLE | 06.40-05-PLAN.md:125 |
| file | `examples/bootstrap5/project/urls.py` | UNCHECKABLE | 06.40-04-PLAN.md:7, 06.40-04-PLAN.md:37, 06.40-04-PLAN.md:40, 06.40-04-PLAN.md:85, 06.40-04-PLAN.md:104, 06.40-04-PLAN.md:105 |
| file | `examples/bootstrap5/test_doc_links.py` | UNCHECKABLE | 06.40-06-PLAN.md:7, 06.40-06-PLAN.md:44, 06.40-06-PLAN.md:97, 06.40-06-PLAN.md:129, 06.40-06-PLAN.md:130 |
| file | `migrations/__init__.py` | SKIPPED | 06.40-04-PLAN.md:107 |
| file | `navbar_demo/tests.py` | SKIPPED | 06.40-04-PLAN.md:97, 06.40-04-PLAN.md:109, 06.40-05-PLAN.md:105, 06.40-05-PLAN.md:117, 06.40-05-PLAN.md:129, 06.40-06-PLAN.md:133 |
| file | `scripts/check_dist.py` | UNCHECKABLE | 06.40-08-PLAN.md:99 |
| file | `scripts/validate.py` | UNCHECKABLE | 06.40-07-PLAN.md:90 |
| file | `src/crud_views/checks.py` | UNCHECKABLE | 06.40-01-PLAN.md:105 |
| file | `src/crud_views/lib/ancestor_policy.py` | UNCHECKABLE | 06.40-05-PLAN.md:101 |
| file | `src/crud_views/lib/ancestors.py` | UNCHECKABLE | 06.40-01-PLAN.md:36, 06.40-01-PLAN.md:93 |
| file | `src/crud_views/lib/breadcrumb.py` | UNCHECKABLE | 06.40-01-PLAN.md:81, 06.40-01-PLAN.md:105, 06.40-02-PLAN.md:83 |
| file | `src/crud_views/lib/check.py` | UNCHECKABLE | 06.40-01-PLAN.md:105 |
| file | `src/crud_views/lib/icons.py` | UNCHECKABLE | 06.40-02-PLAN.md:95 |
| file | `src/crud_views/lib/navbar.py` | SKIPPED | 06.40-01-PLAN.md:7, 06.40-01-PLAN.md:21, 06.40-01-PLAN.md:33, 06.40-01-PLAN.md:35, 06.40-01-PLAN.md:38, 06.40-01-PLAN.md:69, 06.40-01-PLAN.md:80, 06.40-01-PLAN.md:92, 06.40-01-PLAN.md:104, 06.40-02-PLAN.md:7, 06.40-02-PLAN.md:29, 06.40-02-PLAN.md:41, 06.40-02-PLAN.md:74, 06.40-02-PLAN.md:82, 06.40-03-PLAN.md:7, 06.40-03-PLAN.md:29, 06.40-03-PLAN.md:32, 06.40-03-PLAN.md:35, 06.40-03-PLAN.md:69, 06.40-03-PLAN.md:76, 06.40-04-PLAN.md:47, 06.40-06-PLAN.md:53, 06.40-06-PLAN.md:106, 06.40-06-PLAN.md:118 |
| file | `src/crud_views/lib/view/base.py` | UNCHECKABLE | 06.40-01-PLAN.md:81, 06.40-03-PLAN.md:33, 06.40-03-PLAN.md:77 |
| file | `src/crud_views/lib/view/buttons.py` | UNCHECKABLE | 06.40-01-PLAN.md:93 |
| file | `src/crud_views/lib/views/manage.py` | UNCHECKABLE | 06.40-02-PLAN.md:83 |
| file | `src/crud_views/lib/viewset/__init__.py` | UNCHECKABLE | 06.40-01-PLAN.md:39, 06.40-01-PLAN.md:93 |
| file | `src/crud_views/lib/viewset/parentviewset.py` | UNCHECKABLE | 06.40-01-PLAN.md:93 |
| file | `src/crud_views/templates/crud_views/tags/button/action.html` | UNCHECKABLE | 06.40-02-PLAN.md:95 |
| file | `src/crud_views/templates/crud_views/tags/navbar.html` | SKIPPED | 06.40-01-PLAN.md:7, 06.40-01-PLAN.md:23, 06.40-01-PLAN.md:70, 06.40-01-PLAN.md:80, 06.40-02-PLAN.md:7, 06.40-02-PLAN.md:31, 06.40-02-PLAN.md:34, 06.40-02-PLAN.md:37, 06.40-02-PLAN.md:75, 06.40-02-PLAN.md:82 |
| file | `src/crud_views/templates/crud_views/tags/navbar_identity.html` | SKIPPED | 06.40-02-PLAN.md:7, 06.40-02-PLAN.md:23, 06.40-02-PLAN.md:35, 06.40-02-PLAN.md:71, 06.40-02-PLAN.md:82, 06.40-02-PLAN.md:94 |
| file | `src/crud_views/templates/crud_views/tags/navbar_items.html` | SKIPPED | 06.40-02-PLAN.md:7, 06.40-02-PLAN.md:25, 06.40-02-PLAN.md:38, 06.40-02-PLAN.md:40, 06.40-02-PLAN.md:72, 06.40-02-PLAN.md:82, 06.40-02-PLAN.md:94 |
| file | `src/crud_views/templatetags/crud_views.py` | UNCHECKABLE | 06.40-01-PLAN.md:7, 06.40-01-PLAN.md:29, 06.40-01-PLAN.md:32, 06.40-01-PLAN.md:73, 06.40-01-PLAN.md:80, 06.40-01-PLAN.md:81, 06.40-02-PLAN.md:83, 06.40-05-PLAN.md:53, 06.40-06-PLAN.md:118 |
| file | `src/crud_views_guardian/lib/mixins.py` | UNCHECKABLE | 06.40-03-PLAN.md:77 |
| file | `src/crud_views_guardian/lib/views.py` | UNCHECKABLE | 06.40-03-PLAN.md:36, 06.40-03-PLAN.md:77 |
| file | `src/crud_views_guardian/lib/viewset.py` | UNCHECKABLE | 06.40-04-PLAN.md:44 |
| file | `tags/navbar.html` | SKIPPED | 06.40-01-PLAN.md:83 |
| file | `tests/test1/test_action_enabled.py` | UNCHECKABLE | 06.40-03-PLAN.md:77, 06.40-03-PLAN.md:81, 06.40-03-PLAN.md:93 |
| file | `tests/test1/test_ancestor_authorization.py` | UNCHECKABLE | 06.40-01-PLAN.md:81 |
| file | `tests/test1/test_breadcrumb.py` | UNCHECKABLE | 06.40-01-PLAN.md:81, 06.40-01-PLAN.md:105, 06.40-03-PLAN.md:89 |
| file | `tests/test1/test_guardian_child_link_visibility.py` | UNCHECKABLE | 06.40-03-PLAN.md:77, 06.40-03-PLAN.md:81, 06.40-03-PLAN.md:89, 06.40-03-PLAN.md:93 |
| file | `tests/test1/test_navbar.py` | SKIPPED | 06.40-01-PLAN.md:7, 06.40-01-PLAN.md:25, 06.40-01-PLAN.md:71, 06.40-01-PLAN.md:80, 06.40-01-PLAN.md:85, 06.40-01-PLAN.md:92, 06.40-01-PLAN.md:97, 06.40-03-PLAN.md:77, 06.40-03-PLAN.md:89, 06.40-08-PLAN.md:106 |
| file | `tests/test1/test_navbar_checks.py` | SKIPPED | 06.40-01-PLAN.md:7, 06.40-01-PLAN.md:27, 06.40-01-PLAN.md:72, 06.40-01-PLAN.md:104, 06.40-01-PLAN.md:109, 06.40-08-PLAN.md:106 |
| file | `tests/test1/test_navbar_costs.py` | SKIPPED | 06.40-03-PLAN.md:7, 06.40-03-PLAN.md:25, 06.40-03-PLAN.md:67, 06.40-03-PLAN.md:88, 06.40-03-PLAN.md:93, 06.40-08-PLAN.md:106 |
| file | `tests/test1/test_navbar_docs.py` | SKIPPED | 06.40-06-PLAN.md:7, 06.40-06-PLAN.md:40, 06.40-06-PLAN.md:95, 06.40-06-PLAN.md:117, 06.40-06-PLAN.md:122, 06.40-08-PLAN.md:106 |
| file | `tests/test1/test_navbar_permissions.py` | SKIPPED | 06.40-03-PLAN.md:7, 06.40-03-PLAN.md:23, 06.40-03-PLAN.md:66, 06.40-03-PLAN.md:76, 06.40-03-PLAN.md:81, 06.40-08-PLAN.md:106 |
| file | `tests/test1/test_navbar_templates.py` | SKIPPED | 06.40-02-PLAN.md:7, 06.40-02-PLAN.md:27, 06.40-02-PLAN.md:73, 06.40-02-PLAN.md:82, 06.40-02-PLAN.md:87, 06.40-02-PLAN.md:94, 06.40-02-PLAN.md:99, 06.40-03-PLAN.md:89, 06.40-08-PLAN.md:106 |
| symbol | `ActionView` | UNCHECKABLE | 06.40-01-PLAN.md:107 |
| symbol | `AncestorPolicy` | UNCHECKABLE | 06.40-04-PLAN.md:95, 06.40-05-PLAN.md:103 |
| symbol | `CHANGELOG` | UNCHECKABLE | 06.40-06-PLAN.md:7, 06.40-06-PLAN.md:38, 06.40-06-PLAN.md:94, 06.40-06-PLAN.md:117, 06.40-06-PLAN.md:118 |
| symbol | `CV_MANAGE_SCHEMA_EXPORT_DIR` | UNCHECKABLE | 06.40-08-PLAN.md:100, 06.40-08-PLAN.md:106 |
| symbol | `Check` | UNCHECKABLE | 06.40-01-PLAN.md:107 |
| symbol | `Child` | UNCHECKABLE | 06.40-01-PLAN.md:96, 06.40-01-PLAN.md:99 |
| symbol | `Create` | UNCHECKABLE | 06.40-01-PLAN.md:142, 06.40-02-PLAN.md:131, 06.40-03-PLAN.md:126, 06.40-04-PLAN.md:141, 06.40-05-PLAN.md:162, 06.40-06-PLAN.md:165, 06.40-07-PLAN.md:125, 06.40-08-PLAN.md:143 |
| symbol | `CreateViewParentMixin` | UNCHECKABLE | 06.40-04-PLAN.md:95 |
| symbol | `CrudViewNavBarMixin` | SKIPPED | 06.40-01-PLAN.md:22, 06.40-01-PLAN.md:69, 06.40-01-PLAN.md:83, 06.40-06-PLAN.md:120 |
| symbol | `Customer` | UNCHECKABLE | 06.40-04-PLAN.md:17, 06.40-04-PLAN.md:18, 06.40-04-PLAN.md:19, 06.40-04-PLAN.md:24, 06.40-04-PLAN.md:48, 06.40-04-PLAN.md:52, 06.40-04-PLAN.md:78, 06.40-04-PLAN.md:95, 06.40-04-PLAN.md:96, 06.40-04-PLAN.md:98, 06.40-04-PLAN.md:99, 06.40-04-PLAN.md:108, 06.40-04-PLAN.md:111, 06.40-04-PLAN.md:127, 06.40-04-PLAN.md:128, 06.40-05-PLAN.md:19, 06.40-05-PLAN.md:26, 06.40-05-PLAN.md:84, 06.40-05-PLAN.md:99, 06.40-05-PLAN.md:103, 06.40-05-PLAN.md:104, 06.40-05-PLAN.md:107, 06.40-05-PLAN.md:115, 06.40-05-PLAN.md:127 |
| symbol | `DATABASES` | UNCHECKABLE | 06.40-08-PLAN.md:89 |
| symbol | `DEMO_BASE` | UNCHECKABLE | 06.40-06-PLAN.md:131 |
| symbol | `DEMO_USERS` | UNCHECKABLE | 06.40-05-PLAN.md:115 |
| symbol | `DocRef` | UNCHECKABLE | 06.40-06-PLAN.md:51, 06.40-06-PLAN.md:131, 06.40-06-PLAN.md:132, 06.40-06-PLAN.md:135, 06.40-05-PLAN.md:127, 06.40-06-PLAN.md:19, 06.40-06-PLAN.md:134 |
| symbol | `Document` | UNCHECKABLE | 06.40-06-PLAN.md:104, 06.40-06-PLAN.md:107 |
| symbol | `Example` | UNCHECKABLE | 06.40-01-PLAN.md:134, 06.40-02-PLAN.md:123, 06.40-03-PLAN.md:118, 06.40-04-PLAN.md:133, 06.40-05-PLAN.md:154, 06.40-06-PLAN.md:157, 06.40-07-PLAN.md:117, 06.40-08-PLAN.md:135 |
| symbol | `FEATURES` | UNCHECKABLE | 06.40-04-PLAN.md:107, 06.40-05-PLAN.md:127, 06.40-06-PLAN.md:131 |
| symbol | `Feature` | UNCHECKABLE | 06.40-05-PLAN.md:127, 06.40-06-PLAN.md:19, 06.40-06-PLAN.md:131 |
| symbol | `Feature.docs` | UNCHECKABLE | 06.40-06-PLAN.md:131 |
| symbol | `First` | UNCHECKABLE | 06.40-01-PLAN.md:83 |
| symbol | `GuardianViewSet` | UNCHECKABLE | 06.40-04-PLAN.md:45, 06.40-04-PLAN.md:95 |
| symbol | `INSTALLED_APPS` | UNCHECKABLE | 06.40-04-PLAN.md:95 |
| symbol | `Identity` | UNCHECKABLE | 06.40-02-PLAN.md:97 |
| symbol | `ImproperlyConfigured` | UNCHECKABLE | 06.40-03-PLAN.md:79 |
| symbol | `Invalid` | UNCHECKABLE | 06.40-01-PLAN.md:19 |
| symbol | `Inventory` | UNCHECKABLE | 06.40-06-PLAN.md:115 |
| symbol | `Item` | UNCHECKABLE | 06.40-01-PLAN.md:96, 06.40-01-PLAN.md:99, 06.40-02-PLAN.md:97, 06.40-05-PLAN.md:19, 06.40-05-PLAN.md:24, 06.40-05-PLAN.md:83, 06.40-05-PLAN.md:99, 06.40-05-PLAN.md:102, 06.40-05-PLAN.md:103, 06.40-05-PLAN.md:104, 06.40-05-PLAN.md:106, 06.40-05-PLAN.md:107 |
| symbol | `List` | UNCHECKABLE | 06.40-06-PLAN.md:107 |
| symbol | `Migration` | UNCHECKABLE | 06.40-04-PLAN.md:87 |
| symbol | `NavBar` | SKIPPED | 06.40-01-PLAN.md:22, 06.40-01-PLAN.md:69, 06.40-01-PLAN.md:83, 06.40-06-PLAN.md:120 |
| symbol | `NavItem` | SKIPPED | 06.40-01-PLAN.md:22, 06.40-01-PLAN.md:69, 06.40-01-PLAN.md:83, 06.40-06-PLAN.md:120 |
| symbol | `NavbarMixin` | SKIPPED | 06.40-04-PLAN.md:26, 06.40-04-PLAN.md:79, 06.40-04-PLAN.md:95, 06.40-05-PLAN.md:103 |
| symbol | `Never` | UNCHECKABLE | 06.40-07-PLAN.md:79 |
| symbol | `Ordinary` | UNCHECKABLE | 06.40-08-PLAN.md:18 |
| symbol | `Owned` | UNCHECKABLE | 06.40-04-PLAN.md:94 |
| symbol | `PK` | UNCHECKABLE | 06.40-01-PLAN.md:95, 06.40-01-PLAN.md:96, 06.40-01-PLAN.md:99, 06.40-04-PLAN.md:107 |
| symbol | `PYTHONPATH` | UNCHECKABLE | 06.40-01-PLAN.md:85, 06.40-01-PLAN.md:97, 06.40-01-PLAN.md:109, 06.40-02-PLAN.md:87, 06.40-02-PLAN.md:99, 06.40-03-PLAN.md:81, 06.40-03-PLAN.md:93, 06.40-04-PLAN.md:107, 06.40-06-PLAN.md:122, 06.40-08-PLAN.md:89, 06.40-08-PLAN.md:100, 06.40-08-PLAN.md:102, 06.40-08-PLAN.md:103, 06.40-08-PLAN.md:104 |
| symbol | `Parent` | UNCHECKABLE | 06.40-04-PLAN.md:108, 06.40-04-PLAN.md:111 |
| symbol | `ParentViewSet` | UNCHECKABLE | 06.40-04-PLAN.md:95 |
| symbol | `Probe` | UNCHECKABLE | 06.40-08-PLAN.md:100 |
| symbol | `Project` | UNCHECKABLE | 06.40-04-PLAN.md:110 |
| symbol | `SafeString` | UNCHECKABLE | 06.40-01-PLAN.md:82, 06.40-01-PLAN.md:83, 06.40-01-PLAN.md:128, 06.40-02-PLAN.md:118 |
| symbol | `SimpleLazyObject` | UNCHECKABLE | 06.40-01-PLAN.md:83 |
| symbol | `Task` | UNCHECKABLE | 06.40-01-PLAN.md:127, 06.40-01-PLAN.md:128, 06.40-01-PLAN.md:129, 06.40-02-PLAN.md:117, 06.40-02-PLAN.md:118, 06.40-03-PLAN.md:111, 06.40-03-PLAN.md:112, 06.40-03-PLAN.md:113, 06.40-04-PLAN.md:95, 06.40-04-PLAN.md:127, 06.40-04-PLAN.md:128, 06.40-05-PLAN.md:147, 06.40-05-PLAN.md:148, 06.40-05-PLAN.md:149, 06.40-06-PLAN.md:151, 06.40-06-PLAN.md:152, 06.40-07-PLAN.md:22, 06.40-07-PLAN.md:24, 06.40-07-PLAN.md:26, 06.40-07-PLAN.md:28, 06.40-07-PLAN.md:66, 06.40-07-PLAN.md:67, 06.40-07-PLAN.md:68, 06.40-07-PLAN.md:69, 06.40-07-PLAN.md:111, 06.40-07-PLAN.md:112, 06.40-08-PLAN.md:129, 06.40-08-PLAN.md:130 |
| symbol | `Update` | UNCHECKABLE | 06.40-01-PLAN.md:96, 06.40-01-PLAN.md:99, 06.40-06-PLAN.md:25, 06.40-06-PLAN.md:27, 06.40-06-PLAN.md:29, 06.40-06-PLAN.md:31, 06.40-06-PLAN.md:33, 06.40-06-PLAN.md:35, 06.40-06-PLAN.md:37, 06.40-06-PLAN.md:39, 06.40-06-PLAN.md:43, 06.40-06-PLAN.md:45, 06.40-06-PLAN.md:47, 06.40-06-PLAN.md:87, 06.40-06-PLAN.md:88, 06.40-06-PLAN.md:89, 06.40-06-PLAN.md:90, 06.40-06-PLAN.md:91, 06.40-06-PLAN.md:92, 06.40-06-PLAN.md:93, 06.40-06-PLAN.md:94, 06.40-06-PLAN.md:96, 06.40-06-PLAN.md:97, 06.40-06-PLAN.md:98, 06.40-06-PLAN.md:131, 06.40-07-PLAN.md:41, 06.40-07-PLAN.md:79, 06.40-08-PLAN.md:100 |
| symbol | `ViewSet` | UNCHECKABLE | 06.40-04-PLAN.md:95, 06.40-04-PLAN.md:107 |
| symbol | `__init__` | UNCHECKABLE | 06.40-01-PLAN.md:39, 06.40-01-PLAN.md:93, 06.40-04-PLAN.md:7, 06.40-04-PLAN.md:21, 06.40-04-PLAN.md:31, 06.40-04-PLAN.md:77, 06.40-04-PLAN.md:82, 06.40-04-PLAN.md:92, 06.40-04-PLAN.md:104, 06.40-04-PLAN.md:107 |
| symbol | `_cv_action_enabled_for_rendering` | UNCHECKABLE | 06.40-03-PLAN.md:79 |
| symbol | `_cv_child_link_has_access` | UNCHECKABLE | 06.40-03-PLAN.md:79 |
| symbol | `_resolved_ancestor` | UNCHECKABLE | 06.40-01-PLAN.md:37, 06.40-01-PLAN.md:95 |
| symbol | `_walk_ancestors` | UNCHECKABLE | 06.40-01-PLAN.md:37, 06.40-01-PLAN.md:95 |
| symbol | `accept_global_perms` | UNCHECKABLE | 06.40-04-PLAN.md:95 |
| symbol | `active` | UNCHECKABLE | 06.40-01-PLAN.md:95, 06.40-01-PLAN.md:96, 06.40-01-PLAN.md:98, 06.40-01-PLAN.md:99, 06.40-02-PLAN.md:85, 06.40-02-PLAN.md:97, 06.40-02-PLAN.md:100, 06.40-04-PLAN.md:19, 06.40-04-PLAN.md:96, 06.40-04-PLAN.md:99, 06.40-05-PLAN.md:19, 06.40-05-PLAN.md:104, 06.40-05-PLAN.md:107, 06.40-06-PLAN.md:107, 06.40-08-PLAN.md:89, 06.40-08-PLAN.md:90, 06.40-08-PLAN.md:93 |
| symbol | `browser_run_code` | UNCHECKABLE | 06.40-08-PLAN.md:89, 06.40-08-PLAN.md:91 |
| symbol | `child` | UNCHECKABLE | 06.40-01-PLAN.md:83, 06.40-01-PLAN.md:94, 06.40-01-PLAN.md:95, 06.40-01-PLAN.md:96, 06.40-01-PLAN.md:99, 06.40-01-PLAN.md:107, 06.40-03-PLAN.md:17, 06.40-03-PLAN.md:78, 06.40-03-PLAN.md:79, 06.40-03-PLAN.md:82, 06.40-06-PLAN.md:107, 06.40-07-PLAN.md:79 |
| symbol | `cv_get_url_extra_kwargs` | UNCHECKABLE | 06.40-01-PLAN.md:95 |
| symbol | `cv_has_access` | UNCHECKABLE | 06.40-03-PLAN.md:79 |
| symbol | `cv_navbar` | SKIPPED | 06.40-01-PLAN.md:30, 06.40-01-PLAN.md:34, 06.40-01-PLAN.md:73, 06.40-01-PLAN.md:83, 06.40-02-PLAN.md:24, 06.40-02-PLAN.md:71, 06.40-02-PLAN.md:85, 06.40-05-PLAN.md:54, 06.40-05-PLAN.md:127, 06.40-06-PLAN.md:120 |
| symbol | `cv_navbar.items` | SKIPPED | 06.40-02-PLAN.md:42 |
| symbol | `cv_navbar.object` | SKIPPED | 06.40-02-PLAN.md:85 |
| symbol | `deviceScaleFactor` | UNCHECKABLE | 06.40-08-PLAN.md:89 |
| symbol | `document.clientWidth` | UNCHECKABLE | 06.40-08-PLAN.md:89 |
| symbol | `document.scrollWidth` | UNCHECKABLE | 06.40-08-PLAN.md:89 |
| symbol | `ensure_demo_users` | UNCHECKABLE | 06.40-05-PLAN.md:115 |
| symbol | `feature.url_name` | UNCHECKABLE | 06.40-06-PLAN.md:131 |
| symbol | `get` | UNCHECKABLE | 06.40-01-PLAN.md:107, 06.40-05-PLAN.md:115 |
| symbol | `get_context_data` | UNCHECKABLE | 06.40-01-PLAN.md:83, 06.40-02-PLAN.md:85 |
| symbol | `get_pk_name` | UNCHECKABLE | 06.40-01-PLAN.md:95 |
| symbol | `get_router_name` | UNCHECKABLE | 06.40-01-PLAN.md:95 |
| symbol | `get_view_class` | UNCHECKABLE | 06.40-01-PLAN.md:95 |
| symbol | `grant_model_perms` | UNCHECKABLE | 06.40-05-PLAN.md:115 |
| symbol | `http_method_names` | UNCHECKABLE | 06.40-01-PLAN.md:107 |
| symbol | `icon` | UNCHECKABLE | 06.40-01-PLAN.md:83, 06.40-01-PLAN.md:95, 06.40-02-PLAN.md:20, 06.40-02-PLAN.md:85, 06.40-02-PLAN.md:97, 06.40-02-PLAN.md:100 |
| symbol | `item.label` | SKIPPED | 06.40-02-PLAN.md:85 |
| symbol | `items` | UNCHECKABLE | 06.40-01-PLAN.md:83, 06.40-02-PLAN.md:26, 06.40-02-PLAN.md:39, 06.40-02-PLAN.md:72, 06.40-02-PLAN.md:85, 06.40-02-PLAN.md:97, 06.40-02-PLAN.md:98, 06.40-02-PLAN.md:100, 06.40-02-PLAN.md:101, 06.40-03-PLAN.md:79, 06.40-03-PLAN.md:82 |
| symbol | `key` | UNCHECKABLE | 06.40-01-PLAN.md:83, 06.40-01-PLAN.md:95, 06.40-01-PLAN.md:107 |
| symbol | `label` | UNCHECKABLE | 06.40-01-PLAN.md:83, 06.40-01-PLAN.md:95, 06.40-02-PLAN.md:85, 06.40-08-PLAN.md:89 |
| symbol | `navbar_browser_settings` | SKIPPED | 06.40-08-PLAN.md:89 |
| symbol | `navbar_customer` | SKIPPED | 06.40-04-PLAN.md:95 |
| symbol | `navbar_demo` | SKIPPED | 06.40-04-PLAN.md:36, 06.40-04-PLAN.md:84, 06.40-04-PLAN.md:95, 06.40-04-PLAN.md:96, 06.40-04-PLAN.md:99, 06.40-04-PLAN.md:108, 06.40-04-PLAN.md:111, 06.40-05-PLAN.md:42, 06.40-05-PLAN.md:92, 06.40-05-PLAN.md:127, 06.40-06-PLAN.md:131 |
| symbol | `navbar_tenant` | SKIPPED | 06.40-04-PLAN.md:95 |
| symbol | `parent` | UNCHECKABLE | 06.40-01-PLAN.md:96, 06.40-01-PLAN.md:99, 06.40-04-PLAN.md:106, 06.40-04-PLAN.md:107, 06.40-04-PLAN.md:110, 06.40-04-PLAN.md:128, 06.40-05-PLAN.md:103, 06.40-08-PLAN.md:89 |
| symbol | `provider` | UNCHECKABLE | 06.40-04-PLAN.md:95 |
| symbol | `self.object` | UNCHECKABLE | 06.40-01-PLAN.md:95 |
| symbol | `target._cv_child_link_has_access` | UNCHECKABLE | 06.40-03-PLAN.md:79 |
| symbol | `target.cv_has_access` | UNCHECKABLE | 06.40-03-PLAN.md:79 |
| symbol | `template` | UNCHECKABLE | 06.40-01-PLAN.md:30, 06.40-01-PLAN.md:73, 06.40-01-PLAN.md:83, 06.40-02-PLAN.md:17, 06.40-02-PLAN.md:42, 06.40-02-PLAN.md:46, 06.40-02-PLAN.md:85, 06.40-02-PLAN.md:118, 06.40-03-PLAN.md:91, 06.40-05-PLAN.md:127, 06.40-06-PLAN.md:107, 06.40-06-PLAN.md:120, 06.40-07-PLAN.md:17, 06.40-07-PLAN.md:90 |
| symbol | `url` | UNCHECKABLE | 06.40-02-PLAN.md:85 |
| symbol | `viewset` | UNCHECKABLE | 06.40-01-PLAN.md:83 |
