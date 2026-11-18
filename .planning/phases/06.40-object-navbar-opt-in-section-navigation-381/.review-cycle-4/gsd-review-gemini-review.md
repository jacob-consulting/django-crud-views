## 06.40-01

### 1. Summary
Plan `06.40-01` establishes the core opt-in navbar module (`src/crud_views/lib/navbar.py`), the `{% cv_navbar %}` template tag (`src/crud_views/templatetags/crud_views.py`), the initial layout-B wrapper template, descendant owner/route resolution, and startup checks. In this cycle-4 revision, Task `06.40-01-03` explicitly owns `src/crud_views/checks.py` and closes R20 by running `_url_configuration_loaded()` in `check_viewsets` before `ViewSet.checks_all()` takes its registry snapshot, while extending `_url_configuration_loaded` with a keyword-only `load: bool = True` parameter so cooperative navbar checks can probe `load=False` against cached `URLResolver.url_patterns` without triggering module imports during live `_views.values()` iteration.

### 2. Strengths
- **Complete, source-grounded resolution of R20 (`src/crud_views/checks.py:38-48,172-195` and `src/crud_views/lib/viewset/__init__.py:225-232,286-287`):** Calling `_url_configuration_loaded()` at the start of `check_viewsets` (`src/crud_views/checks.py:39`) ensures URLconf imports finish before `ViewSet.checks_all()` snapshots `list(_REGISTRY.values())` (`src/crud_views/lib/viewset/__init__.py:230`) and before any `ViewSet.checks()` iterates `self._views.values()` (`src/crud_views/lib/viewset/__init__.py:286`).
- **Import-free `load=False` readiness probe across Django 4.2, 5.2, and 6.0 (`django/urls/resolvers.py` and `django/utils/functional.py`):** In all three supported Django series (verified at `.nox/tests-3-12-django-4-2/.../django/urls/resolvers.py:712`, `.nox/tests-3-12-django-5-2/.../django/urls/resolvers.py:715`, and `.nox/tests-3-12-django-6-0/.../django/urls/resolvers.py:726`), `URLResolver.url_patterns` is a `@cached_property` whose descriptor (`django/utils/functional.py:47`) writes `"url_patterns"` into `resolver.__dict__` only after successful evaluation. Checking `"url_patterns" in resolver.__dict__` when `load=False` distinguishes an unloaded or failed resolver from a valid cached empty `urlpatterns = []` without ever invoking `resolver.url_patterns` or `resolver.urlconf_module` inside `self._views.values()` iteration.
- **Strong cold-URLconf and failed-preflight regressions:** Task `06.40-01-03` requires testing a cold temporary `ROOT_URLCONF` that registers invalid configured views on both a pre-existing `ViewSet` and a newly registered `ViewSet`, invoking `check_viewsets` directly first and asserting all distinct late diagnostics in the first completed pass, plus an import-attempt counter proving failed/in-progress imports are not retried during live iteration.
- **Prior concerns R1, R7, R8, R9, R10, R11, R13, R14, R17, and R18 remain closed:** Owner-bound `ViewContext` for `cv_get_action_short_label` (`src/crud_views/lib/view/base.py:630-644`), single-pass `html.unescape` + `SafeData` stripping for `render_snippet` (`src/crud_views/lib/view/base.py:578-592`), literal `is_view_registered` checks before `get_view_class`/`get_router_name` (`src/crud_views/lib/viewset/__init__.py:372-388`), and `owner_viewset.pk_name` vs `owner.pk` routing (`src/crud_views/lib/viewset/__init__.py:420-422`) are all preserved intact.

### 3. Concerns
- None. R20 is closed at the planning level and no new gaps were introduced.

### 4. Suggestions
- None required for plan readiness.

### 5. Risk Assessment
- **LOW:** The startup check ordering, `load=False` cached-property inspection, owner-bound short-label context, and route resolution are directly verified against `src/crud_views/checks.py`, `src/crud_views/lib/viewset/__init__.py`, and all three supported Django series.

---

## 06.40-02

### 1. Summary
Plan `06.40-02` extracts the `tags/navbar_identity.html` and `tags/navbar_items.html` leaf partials, locks in the `SimpleLazyObject` single-build contract per view/request (`src/crud_views/lib/views/manage.py:1013-1019`), verifies global, leaf, split-placement, and per-bar `NavBar(template=...)` overrides, and ships the German `Sections for %(object)s` translation (`src/crud_views/locale/de/LC_MESSAGES/django.po` and `.mo`).

### 2. Strengths
- **Independent leaf guards and landmark ownership:** Both partials guard on `cv_navbar` before emitting markup or whitespace, and `navbar_items.html` owns the `<nav aria-label="...">` landmark independently of `navbar_identity.html`, enabling split placement with a single lazy evaluation (D-08, AC7).
- **Single-pass escaping and bilingual catalog verification (R1, R15 closed):** Consumes the plain-`str` values normalized in Plan `06.40-01`, compiles `.mo` via `polib` in the supported test environment, and asserts the literal German accessible name (`Abschnitte für ...`) under `translation.override("de")`.

### 3. Concerns
- None.

### 4. Suggestions
- None required for plan readiness.

### 5. Risk Assessment
- **LOW:** Lazy context patterns and template-loader overrides follow established conventions in `src/crud_views/lib/views/manage.py:1013-1019` and `tests/test1/test_breadcrumb.py:39-43`.

---

## 06.40-03

### 1. Summary
Plan `06.40-03` validates the permission-then-state admission sequence (`D-09`, `AC3`) against real core and Guardian endpoints (`tests/test1/test_navbar_permissions.py`) and records categorized hook/SQL cost measurements and whole-page byte-for-byte nonparticipant preservation (`tests/test1/test_navbar_costs.py` and `06.40-COST.md`).

### 2. Strengths
- **Exact helper invocation order and count (`src/crud_views/lib/view/base.py:524-566`):** Calls `target.cv_has_access(user, owner)` for owner items and `target._cv_child_link_has_access(user, owner)` once for child items, invoking `target._cv_action_enabled_for_rendering(user, owner, rendering_view)` only after permission passes, and propagating reached `ImproperlyConfigured` policy errors (`src/crud_views/lib/ancestors.py:654-686`).
- **Complete cold-cache reset and whole-page byte parity (R7, R9, R19 closed):** Resets `check_module._VOCAB_CACHE`, `ViewSet._default_permissions` (`src/crud_views/lib/viewset/__init__.py:489-505`), `ContentType.objects.clear_cache()`, and `guardian.shortcuts.clear_ct_cache()` (`tests/test1/test_guardian_child_link_visibility.py:1068-1151`), and compares full `response.content` bytes using the local `cv_extends_template` harness.

### 3. Concerns
- None.

### 4. Suggestions
- None required for plan readiness.

### 5. Risk Assessment
- **LOW:** Directly reuses the proven spy and query-categorization patterns in `tests/test1/test_guardian_child_link_visibility.py:1097-1109` and `tests/test1/test_action_enabled.py`.

---

## 06.40-04

### 1. Summary
Plan `06.40-04` creates the self-contained `examples/bootstrap5/navbar_demo` app slice for `Tenant` and `Customer` (`D-15`), wiring `GuardianViewSet` on `Tenant` (`AncestorPolicy(provider="guardian", accept_global_perms=False)`), core `ViewSet` with `ParentViewSet(name="navbar_tenant", attribute="tenant")` on `Customer`, two `Customer` detail views (`detail` and `notes`), `/object-navbar/` routes, and `0001_initial.py`.

### 2. Strengths
- **Explicit `ParentViewSet` FK attribute mapping (R2 closed):** Because the ViewSets use unique `navbar_tenant` / `navbar_customer` registry names while the model FK is `tenant`, `ParentViewSet(name="navbar_tenant", attribute="tenant")` is explicitly specified (`src/crud_views/lib/viewset/parentviewset.py:48-54`) and verified through system checks, queryset filtering, and parent-bound creation.
- **Executable migration drift gate (R16 closed):** Task `06.40-04-02` runs `makemigrations navbar_demo --check --dry-run` with the provisioned `.nox/examples-3-12-django-5-2/bin/python` interpreter as an explicit verification command.

### 3. Concerns
- None.

### 4. Suggestions
- None required for plan readiness.

### 5. Risk Assessment
- **LOW:** Follows `examples/bootstrap5/nested/models.py` and `examples/bootstrap5/guardian_demo/views.py:21-28` without cross-app model imports.

---

## 06.40-05

### 1. Summary
Plan `06.40-05` completes the `Tenant → Customer → (Order → Item, Address)` hierarchy (`0002_order_item_address.py`), attaches the four-item `Customer` navbar across owner, child, and grandchild views (omitting an intermediate `Order` view mixin per `D-06`), adds idempotent seeding for `alice`, `bob`, and `charlie` (`examples/bootstrap5/project/seeding.py:6-10`), places `{% cv_navbar %}` in `examples/bootstrap5/project/templates/project/crud_views.html:10-16`, and registers the feature in `examples/bootstrap5/project/features.py` and `examples/bootstrap5/project/tests.py`.

### 2. Strengths
- **Shared feature contract and landing composition alignment (R2, R3, R4, R6 closed):** Models the landing view on `ThemeIndexView` (`examples/bootstrap5/theming/views.py:21-34`) with `BreadcrumbMixin`, `example_about`, `cv_breadcrumb`, and `snippet_panels`; updates `FeatureGroupsTest.test_grouping_matches_spec` (`examples/bootstrap5/project/tests.py:457-477`); and renders all three demo credentials (`alice/alice`, `bob/bob`, `charlie/charlie`) on the dedicated landing page while preserving `developer` last in `DEMO_USERS` (`examples/bootstrap5/project/seeding.py:6-10`).
- **Temporary `DocRefsPanelTest` exclusion is cleanly bounded:** Excluding `DocRefsPanelTest` (`examples/bootstrap5/project/tests.py:386-444`) in Wave 4 while `docs/reference/navbar.md` does not yet exist—and running the full unexcluded `project/tests.py` in Plan `06.40-06` Task `06.40-06-03` once the `DocRef` is attached—is well-sequenced.

### 3. Concerns
- None.

### 4. Suggestions
- None required for plan readiness.

### 5. Risk Assessment
- **LOW:** All shared example test invariants in `examples/bootstrap5/project/tests.py` are accounted for.

---

## 06.40-06

### 1. Summary
Plan `06.40-06` authors `docs/reference/navbar.md`, updates related reference pages (`index.md`, `nested.md`, `context_buttons.md`, `breadcrumb.md`, `templates.md`, `theme.md`, `demo.md`), inventories the 1.0-stable public navbar surface in `docs/development/stability.md` (`D-16`), adds the `CHANGELOG.md` entry, adds executable doc/contract tests in `tests/test1/test_navbar_docs.py`, and wires the reciprocal `DocRef` (`examples/bootstrap5/project/features.py` and `examples/bootstrap5/test_doc_links.py`).

### 2. Strengths
- **Preserves `## Snippet variables` schema in `docs/reference/templates.md` (R5 closed):** Places navbar context documentation under its own level-two `## Object navbar context` heading and runs `tests/test1/test_snippet_docs.py` (`tests/test1/test_snippet_docs.py:14-56`) directly in Task `06.40-06-02` verification.
- **Full unexcluded example and reciprocal doc-link verification (R3, R4, R6, R15 closed):** Task `06.40-06-03` runs `navbar_demo/tests.py project/tests.py test_i18n.py test_doc_links.py` without `-k 'not DocRefsPanelTest'`, verifying `DocRefsPanelTest` (`examples/bootstrap5/project/tests.py:386-444`) and `test_doc_links.py:118-146`.

### 3. Concerns
- None.

### 4. Suggestions
- None required for plan readiness.

### 5. Risk Assessment
- **LOW:** Documentation structure, `test_snippet_docs.py` invariants, and `test_doc_links.py` reciprocal checks are verified against existing source.

---

## 06.40-07

### 1. Summary
Plan `06.40-07` acquires or verifies an isolated checkout of `https://github.com/jacob-consulting/skills` at `../skills-navbar-06-40`, updates the four tracked skill files (`SKILL.md`, `references/templates-and-navigation.md`, `references/api-reference.md`, and `CHANGELOG.md`), runs the companion repo's native `scripts/validate.py`, creates a scoped local commit on `docs/navbar-06.40`, and records provenance in `06.40-COMPANION-DELIVERY.md`.

### 2. Strengths
- **Safe external checkout hygiene and native validation:** Verifies remote URL and `git ls-files` before editing, never touches installed skill mirrors, runs `.venv/bin/python ../skills-navbar-06-40/scripts/validate.py`, and records the commit SHA in `06.40-COMPANION-DELIVERY.md`.

### 3. Concerns
- None.

### 4. Suggestions
- None required for plan readiness.

### 5. Risk Assessment
- **LOW:** Companion repository targets and validation script are pre-verified in `06.40-COMPANION-GUIDANCE.md`.

---

## 06.40-08

### 1. Summary
Plan `06.40-08` executes live Playwright viewport, reflow (`1280px`, `320px`, `200%` zoom/reflow), long-token (`>=120`-char caption, `>=80`-char unbroken token), and keyboard navigation checks against an isolated SQLite server instance (`06.40-BROWSER-CHECK.js`, `06.40-BROWSER.json`, screenshots), and runs the full source/installed/floor/docs/lint/JS/package acceptance gates (`06.40-ACCEPTANCE.md` and `06.40-VALIDATION.md`).

### 2. Strengths
- **Guaranteed teardown of transient server and files (R12 closed):** Task `06.40-08-01` wraps the temporary settings file (`.pytest_cache/navbar_browser_settings.py`), temporary SQLite directory, and `runserver` process in an outer `try/finally` lifecycle and requires testing cleanup on a deliberate assertion failure before the passing run.
- **Complete floor and matrix coverage (`noxfile.py:20-58,88-107,189-222`):** Task `06.40-08-02` runs all six new navbar test modules (`test_navbar.py`, `test_navbar_checks.py`, `test_navbar_templates.py`, `test_navbar_permissions.py`, `test_navbar_costs.py`, `test_navbar_docs.py`) in `manage_report_floor` at `pydantic==2.2.1` (`noxfile.py:88-107`) alongside cached Django 4.2/5.2/6.0 source runs, `nox -s tests examples crispy_floor`, `mkdocs build --strict`, `ruff`, `npm test`, and `nox -s package`.

### 3. Concerns
- None.

### 4. Suggestions
- None required for plan readiness.

### 5. Risk Assessment
- **LOW:** Verification commands and environment isolation match `noxfile.py` and existing phase gate conventions.

---

## Cross-Plan Comparison and Sign-Off

### Status of R20 and Prior Concerns R1–R19
- **R20 — SIGNED OFF (CLOSED at planning level):** `06.40-01-PLAN.md` Task `06.40-01-03` explicitly owns `src/crud_views/checks.py`, runs `_url_configuration_loaded()` in `check_viewsets` (`src/crud_views/checks.py:39`) before `ViewSet.checks_all()` (`src/crud_views/lib/viewset/__init__.py:225-232`) snapshots `_REGISTRY` or iterates `self._views.values()` (`src/crud_views/lib/viewset/__init__.py:286`), and extends `_url_configuration_loaded(*, load: bool = True) -> bool` (`src/crud_views/checks.py:172-195`) so cooperative navbar checks call `_url_configuration_loaded(load=False)` using only `resolver.__dict__["url_patterns"]` without importing modules during live iteration. Cold URLconf imports into both existing and new ViewSets, as well as failed/in-progress imports, have explicit regression tests in `tests/test1/test_navbar_checks.py`.
- **R1–R19 — REMAIN CLOSED:** All 19 prior review findings remain fully addressed in the current plans with no regressions.

### Overall Readiness and Risk Assessment
- **Overall Risk Level:** **LOW**
- **Verdict:** All 8 plans (`06.40-01` through `06.40-08`) are coherent, source-grounded, properly wave-ordered, and ready for execution with no further plan changes needed.
