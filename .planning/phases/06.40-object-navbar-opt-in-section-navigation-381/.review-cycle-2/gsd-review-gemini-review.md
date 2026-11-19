## 06.40-01

### 1. Summary
Plan `06.40-01` introduces `src/crud_views/lib/navbar.py` (`NavBar`, `NavItem`, `CrudViewNavBarMixin`), the `{% cv_navbar %}` template tag in `src/crud_views/templatetags/crud_views.py`, the guarded layout-B wrapper `src/crud_views/templates/crud_views/tags/navbar.html`, and the core routing and startup-check suites (`tests/test1/test_navbar.py` and `tests/test1/test_navbar_checks.py`). All eight prior review findings assigned to this plan (`R1`, `R7`, `R8`, `R9`, `R10`, `R11`, `R13`, `R14`) are resolved in the revised tasks.

### 2. Strengths
- **Resolves `R1` (single-pass plain-text normalization without double escaping)**: `CrudView.cv_get_action_short_label` (`src/crud_views/lib/view/base.py:638-643`) delegates to `cls.render_snippet` (`src/crud_views/lib/view/base.py:578-592`), which renders a Django template with autoescaping and wraps the output in `mark_safe(result.strip())`. Task 01 now normalizes only that pre-rendered default via `html.unescape` followed by `str.__str__(str(value))`, while stripping `SafeData` without `html.unescape` on raw `str(owner)`, explicit `NavItem.label`, and child plural labels so standard template autoescaping escapes every value once.
- **Resolves `R7` and `R9` (test-local template harness and cache/registry isolation)**: Because `tests/test1/app/templates/app/crud_views.html:1-40` does not contain `{% cv_navbar %}`, Task 01 owns a `locmem` template loader and `cv_extends_template` harness inside `tests/test1/test_navbar.py` with paired tag-present and tag-free bases, and preserves the pre-import ordering (`import tests.test1.project.urls` at `tests/test1/test_ancestor_authorization.py:38`) and snapshot/restore of `_REGISTRY`, `check_module._VOCAB_CACHE`, `ViewSet._default_permissions` (`src/crud_views/lib/viewset/__init__.py:489-505`), URL caches, and `ContentType` cache (`tests/test1/test_ancestor_authorization.py:46-76`).
- **Resolves `R8`, `R10`, `R11`, `R13`, and `R14` (completed-registry barrier and explicit check boundaries)**:
  - Task 01 pins `NavBar(viewset: str, items: list[NavItem], template: str | None = None)` and `NavItem(key: str | None = None, child: str | None = None, ...)` as late-bound string names (`R13`), allowing declarations before child ViewSets register.
  - Task 03 gates registry-dependent checks on `crud_views.checks._url_configuration_loaded()` (`src/crud_views/checks.py:172-195`) so partial URLconf imports do not emit false missing-ViewSet errors (`R8`), validates non-empty `NavBar.template` via `get_template` / `TemplateDoesNotExist` matching `CheckTemplate` (`src/crud_views/lib/check.py:232-253`, `R10`), treats `items=[]` as valid and `NavItem()` / empty string keys as startup check errors (`R11`), and rejects all owner attachments with `cv_object=False` (`R14`).
- **Defeats `"list" -> "card"` lookup aliasing on explicit keys**: Checks `viewset.is_view_registered(key)` (`src/crud_views/lib/viewset/__init__.py:372-373`) before calling `get_view_class` or `get_router_name` (`src/crud_views/lib/viewset/__init__.py:375-388`), and reuses request-local `_resolved_ancestor(view, owner_name)` (`src/crud_views/lib/ancestors.py:576-585`).

### 3. Concerns
- **[LOW] Lazy translation evaluation timing on `NavItem.label` (implementation detail, no plan change needed)**:
  - Task 01 accepts `gettext_lazy` (`Promise`) on `NavItem.label`. During implementation, `NavItem` should keep `label` as a `Promise` (or `str | Promise | None`) at model construction and coerce `str.__str__(str(item.label))` inside the request-time navbar builder rather than inside a Pydantic `@field_validator` at import time, so language switching (`translation.override("de")`) resolves at render time.

### 4. Suggestions
- Coerce `NavItem.label` to `str.__str__(str(value))` in the request-time builder rather than at Pydantic model construction so `gettext_lazy` promises evaluate under the active request language.

### 5. Risk Assessment
**LOW** — All prior `HIGH`/`MEDIUM`/`LOW` concerns (`R1`, `R7`, `R8`, `R9`, `R10`, `R11`, `R13`, `R14`) are addressed in the task specifications with concrete mechanisms.

---

## 06.40-02

### 1. Summary
Plan `06.40-02` extracts `src/crud_views/templates/crud_views/tags/navbar_identity.html` and `navbar_items.html` from `navbar.html`, finalizes the 1.0 public template context (`cv_navbar.object`, `label`, `icon`, `items`; `item.label`, `icon`, `url`, `active`), updates the core German locale catalog (`src/crud_views/locale/de/LC_MESSAGES/django.po` and `.mo`), and tests overrides, laziness, escaping, and German landmark rendering in `tests/test1/test_navbar_templates.py` and `tests/test1/test_i18n.py`. Both prior review findings (`R1` and `R15`) are resolved.

### 2. Strengths
- **Resolves `R1` and `R15` (single-pass template autoescaping and shipped German catalog)**:
  - Task 02 consumes the plain `str` values normalized by Plan 01 without applying `|force_escape` a second time, and tests parsed text and attribute escaping for `&`, `'`, literal entity strings, and `SafeString` markup (`R1`).
  - `files_modified` and Task 02 now explicitly own `src/crud_views/locale/de/LC_MESSAGES/django.po` and `django.mo`, adding `msgid "Sections for %(object)s"` / `msgstr "Abschnitte für %(object)s"`, compiling via `polib` (`tests/test1/test_i18n.py:66-90`), and asserting the rendered German `aria-label` alongside `tests/test1/test_i18n.py` (`R15`).
- **Self-contained partial guards and `aria-current="true"`**: Each template (`navbar.html`, `navbar_identity.html`, `navbar_items.html`) independently guards on `cv_navbar` before emitting markup or whitespace, and `navbar_items.html` uses `aria-current="true"` on the active link, avoiding collision with `examples/bootstrap5/project/tests.py:544` (`nav.count('aria-current="page"') == 1`).
- **Preserves `<head>` asset output on nonparticipating pages**: Uses Bootstrap flex/wrapping utilities (`nav`, `nav-pills`, `flex-wrap`, `mw-100`, `text-break`) inside the navbar templates rather than adding a global stylesheet to `CrudViewsSettings.css` (`src/crud_views/lib/settings.py:354-362` / `src/crud_views/lib/assets.py:88-96`).

### 3. Concerns
None — no remaining actionable plan gaps.

### 4. Suggestions
- None.

### 5. Risk Assessment
**LOW** — `R1` and `R15` are closed and verified by `tests/test1/test_navbar_templates.py` and `tests/test1/test_i18n.py`.

---

## 06.40-03

### 1. Summary
Plan `06.40-03` tests the D-09 access-then-state admission contract across core and Guardian endpoints in `tests/test1/test_navbar_permissions.py`, and verifies hook/query costs and whole-page nonparticipant byte parity in `tests/test1/test_navbar_costs.py` and `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-COST.md`. Prior findings `R7` and `R9` are resolved.

### 2. Strengths
- **Resolves `R7` (whole-page response byte parity)**: Task 02 reuses Plan 01's `locmem` / `cv_extends_template` harness to compare complete `response.content` bytes between tag-free and tag-present base templates for both no-mixin views and mixin views with `cv_navbar = None`, rather than relying only on region goldens under `tests/test1/golden/`.
- **Resolves `R9` (deterministic cold/warm cache resets across xdist workers)**: Task 02 explicitly resets `check_module._VOCAB_CACHE` (`src/crud_views/lib/check.py:341-365`), each participating `ViewSet._default_permissions` (`src/crud_views/lib/viewset/__init__.py:489-505`), `ContentType.objects.clear_cache()`, and actor `_perm_cache`/`_user_perm_cache`/`_group_perm_cache` (plus Guardian object-permission cache where used) before cold measurements, restoring snapshots in `finally`.
- **Preserves single-call Guardian and core child admission**: Calls `target._cv_child_link_has_access(user, owner)` (`src/crud_views/lib/view/base.py:528-541`, `src/crud_views_guardian/lib/mixins.py:297-305`, `src/crud_views_guardian/lib/views.py:387-390`) once before `target._cv_action_enabled_for_rendering(user, owner, rendering_view)` (`src/crud_views/lib/view/base.py:564-566`), and propagates `ImproperlyConfigured` from `_immediate_parent_access` (`src/crud_views/lib/ancestors.py:654-686`).

### 3. Concerns
None — no remaining actionable plan gaps.

### 4. Suggestions
- None.

### 5. Risk Assessment
**LOW** — `R7` and `R9` are closed with explicit cache-reset and whole-response byte assertions.

---

## 06.40-04

### 1. Summary
Plan `06.40-04` scaffolds the self-contained `examples/bootstrap5/navbar_demo` app with `Tenant` and `Customer` models, `0001_initial.py`, `GuardianViewSet` for `Tenant`, core `ViewSet` for `Customer` (`Details` and `Notes` detail views), and `/object-navbar/` routing. Prior findings `R2` and `R16` are resolved.

### 2. Strengths
- **Resolves `R2` (`ParentViewSet(name="navbar_tenant", attribute="tenant")`)**: Because `ParentViewSet.get_attribute()` (`src/crud_views/lib/viewset/parentviewset.py:62-66`) defaults to `self.viewset.name` (`"navbar_tenant"`) and `_validate_relationship` (`src/crud_views/lib/ancestors.py:158-174`) checks `Customer._meta.get_field(attribute)`, Task 01 now explicitly sets `ParentViewSet(name="navbar_tenant", attribute="tenant")` and tests the edge through system checks, queryset filtering, GETs, and parent-bound creation.
- **Resolves `R16` (executable migration drift gate)**: Task 02 `<verify>` now executes `(cd examples/bootstrap5 && PYTHONPATH=../../src:. ../../.nox/examples-3-12-django-5-2/bin/python manage.py makemigrations navbar_demo --check --dry-run)` after the Nox example run so any model/migration drift fails the task gate directly.
- **Avoids `_REGISTRY` collision and premature seed dispatch**: Prefixes ViewSet names (`navbar_tenant`, `navbar_customer`) so `Customer` does not collide with `conditional`'s `customer` ViewSet in `_REGISTRY` (`src/crud_views/lib/viewset/__init__.py:47, 207-211`), and withholds `FEATURES` registration until `navbar_demo/seed.py` is created in Plan 05 (`examples/bootstrap5/project/management/commands/seed.py:18-19`).

### 3. Concerns
None — no remaining actionable plan gaps.

### 4. Suggestions
- None.

### 5. Risk Assessment
**LOW** — Both `R2` and `R16` are addressed directly in Task 01 and Task 02.

---

## 06.40-05

### 1. Summary
Plan `06.40-05` completes the `navbar_demo` hierarchy (`Order`, `Item`, `Address` and `0002_order_item_address.py`), seeds `alice`, `bob`, and `charlie` (`navbar_demo/seed.py`, `project/seeding.py`, `project/management/commands/seed.py`), builds the `navbar-demo-home` landing page (`navbar_demo/templates/navbar_demo/home.html`), registers `navbar_demo` in `project/features.py` and `project/tests.py`, and places `{% cv_navbar %}` in `examples/bootstrap5/project/templates/project/crud_views.html`. All four prior `HIGH` findings (`R2`, `R3`, `R4`, `R6`) are resolved.

### 2. Strengths
- **Resolves `R2` (explicit `attribute=` on descendant `ParentViewSet`s)**: Task 01 declares `ParentViewSet(name="navbar_customer", attribute="customer")` on `Order` and `Address` and `ParentViewSet(name="navbar_order", attribute="order")` on `Item`, plus a `call_command('makemigrations', 'navbar_demo', check=True, dry_run=True)` regression after `0002_order_item_address.py`.
- **Resolves `R3` and `R4` (shared `project/tests.py` ownership and standalone landing page contracts)**:
  - `examples/bootstrap5/project/tests.py` is now in `files_modified` for Task 03, updating `FeatureGroupsTest.test_grouping_matches_spec` (`examples/bootstrap5/project/tests.py:457-477`) to include `"navbar_demo"` at the end of `"ui"`.
  - Task 03 models `navbar-demo-home` on `ThemeIndexView` (`examples/bootstrap5/theming/views.py:21-34` and `examples/bootstrap5/theming/templates/theming/index.html:1-41`) with `project.views.BreadcrumbMixin`, `{% example_about %}`, `{% cv_breadcrumb %}`, `{% snippet_panels %}`, and HTTP 200 for an unseeded superuser, satisfying `HomePageTest`, `ExampleAboutTest`, `BreadcrumbAdoptionTest`, and `NavGroupsTest` in `examples/bootstrap5/project/tests.py:75-81, 238-248, 278-285, 506-592`.
  - Task 03 `<verify>` runs `navbar_demo/tests.py project/tests.py test_i18n.py -k 'not DocRefsPanelTest'`, deferring only `DocRefsPanelTest` (`examples/bootstrap5/project/tests.py:386-404`) until Plan 06 Task 03 creates `docs/reference/navbar.md` and populates `Feature.docs`.
- **Resolves `R6` (discoverable credentials without breaking shared translated notices)**:
  - Adding `("charlie", "charlie", False)` before `("developer", "developer", False)` in `DEMO_USERS` (`examples/bootstrap5/project/seeding.py:6-10`) and updating `examples/bootstrap5/project/management/commands/seed.py:17` while keeping the shared home/login/banner notices untouched preserves both `test_demo_account_notices_include_developer` (`examples/bootstrap5/test_i18n.py:186-200`) and `test_published_demo_credentials_match_seed_output` (`examples/bootstrap5/test_i18n.py:204-217`, which checks `for username in ("alice", "bob", "developer")`).
  - Rendering `alice/alice`, `bob/bob`, and `charlie/charlie` with a login link on `navbar_demo/home.html` satisfies `06.40-UI-SPEC.md:235-236` ("in the example's own intro or shared account help").

### 3. Concerns
None — no remaining actionable plan gaps.

### 4. Suggestions
- None.

### 5. Risk Assessment
**LOW** — All four prior `HIGH` concerns (`R2`, `R3`, `R4`, `R6`) are resolved and verified against `project/tests.py` and `test_i18n.py`.

---

## 06.40-06

### 1. Summary
Plan `06.40-06` writes `docs/reference/navbar.md`, updates reference/theme/template/demo/stability docs and `CHANGELOG.md`, adds executable documentation tests in `tests/test1/test_navbar_docs.py`, and wires `Feature.docs` in `examples/bootstrap5/project/features.py` with full verification in `examples/bootstrap5/test_doc_links.py` and `examples/bootstrap5/project/tests.py`. Prior findings `R3`, `R4`, `R5`, `R6`, and `R15` are resolved.

### 2. Strengths
- **Resolves `R5` (`docs/reference/templates.md` `## Snippet variables` schema preservation)**: `tests/test1/test_snippet_docs.py:27-42` splits `docs/reference/templates.md` at `## Snippet variables` (`docs/reference/templates.md:161`) up to the next `\n## ` heading and asserts that regex `r"^\| `([a-z_]+)` \| (.*?) \|$"` matches only the 8 canonical snippet variables. Task 02 places navbar context documentation under a separate `## Object navbar context` heading *before* `## Snippet variables` and adds `tests/test1/test_snippet_docs.py` directly to Task 02's `<verify>` command.
- **Resolves `R3`, `R4`, and `R6` in final Wave 5 verification**: Once `Feature.docs` is populated on `navbar_demo` in Task 03, Task 03 `<verify>` runs `.venv/bin/nox -s "examples-3.12(django='5.2')" -- -n 4 -q navbar_demo/tests.py project/tests.py test_i18n.py test_doc_links.py` without any `-k` filter, verifying `DocRefsPanelTest.test_every_feature_page_lists_its_doc_refs` (`examples/bootstrap5/project/tests.py:394-403`) and `test_every_feature_declares_doc_refs` / `test_docs_page_links_back_to_demo` (`examples/bootstrap5/test_doc_links.py:105-147`).
- **Complete 1.0 stability inventory (`D-16`)**: Updates `docs/development/stability.md:21-66` to list `NavBar`, `NavItem`, `CrudViewNavBarMixin`, `cv_navbar`, the three `crud_views/tags/navbar*.html` templates, and the documented `cv_navbar` / `item` context keys while keeping private helpers internal.

### 3. Concerns
None — no remaining actionable plan gaps.

### 4. Suggestions
- None.

### 5. Risk Assessment
**LOW** — All documentation, snippet-table, and reciprocal `DocRef` invariants are explicitly guarded by automated tests in Tasks 01–03.

---

## 06.40-07

### 1. Summary
Plan `06.40-07` acquires or verifies an isolated checkout of `https://github.com/jacob-consulting/skills` at `../skills-navbar-06-40`, updates the four tracked skill files (`SKILL.md`, `references/templates-and-navigation.md`, `references/api-reference.md`, `CHANGELOG.md`), validates them with `scripts/validate.py`, creates a scoped local commit on `docs/navbar-06.40`, and records the receipt in `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-COMPANION-DELIVERY.md`.

### 2. Strengths
- **Respects repository boundaries (`docs/development/index.md:87-91`)**: Targets the external `jacob-consulting/skills` repository rather than creating unmaintained skill files in `django-crud-views` or modifying installed skill mirrors.
- **Verified validator and provenance guards**: Task 01 checks remote URL identity and `git ls-files` before editing, and Task 02 validates with `.venv/bin/python ../skills-navbar-06-40/scripts/validate.py` and `git -C ../skills-navbar-06-40 show --check --oneline HEAD`.

### 3. Concerns
None — all prior review items on Plan 07 were adjudicated as non-actionable in the orchestrator environment, and missing prerequisites remain explicit fail-closed gates.

### 4. Suggestions
- None.

### 5. Risk Assessment
**LOW** — Bounded external companion documentation task with deterministic validation and commit receipts.

---

## 06.40-08

### 1. Summary
Plan `06.40-08` runs live Playwright viewport/reflow and keyboard navigation checks (`06.40-BROWSER-CHECK.js` -> `06.40-BROWSER.json`, `06.40-desktop.png`, `06.40-narrow-focus.png`) against an isolated SQLite database (`.pytest_cache/navbar_browser_settings.py`), executes the full source and installed Nox test matrices (`noxfile.py:20-222`), and records final acceptance in `06.40-ACCEPTANCE.md` and `06.40-VALIDATION.md`. Prior finding `R12` is resolved.

### 2. Strengths
- **Resolves `R12` (owned server process and transient path cleanup in `try/finally`)**: Task 01 now specifies an outer `try/finally` lifecycle that fails closed if port `8765` or `.pytest_cache/navbar_browser_settings.py` is already in use, allocates the SQLite database in a unique temporary directory, terminates and awaits only its own `runserver` PID, removes the transient settings module/bytecode and temp DB directory on all exit paths, and verifies cleanup via a deliberate failing assertion before the passing run.
- **Comprehensive matrix and floor coverage (`noxfile.py:20-222`)**: Exercises cached Django 4.2/5.2/6.0 source runs, installed `tests` (including `CV_ACCESS_RECORD_REQUESTS=1` at `noxfile.py:49-57`), `examples`, `crispy_floor` (`noxfile.py:189-200`), `manage_report_floor` at Pydantic `2.2.1` (`noxfile.py:88-108`) with all six `test_navbar*.py` modules, `mkdocs build --strict`, `ruff`, `npm test`, and `package` (`scripts/check_dist.py`).

### 3. Concerns
None — no remaining actionable plan gaps.

### 4. Suggestions
- None.

### 5. Risk Assessment
**LOW** — `R12` is resolved with deterministic `try/finally` process and file cleanup, and unavailable runtimes/browser tools are strictly fail-closed.

---

## Cross-Plan Summary & Disposition Verification

### Verification of Previous Actionable Findings (R1–R16)

All 16 prior actionable findings (`R1`–`R16`) have been verified against the revised plans at HEAD `0ed46a40` and the repository source:

| Finding | Severity | Plan(s) | Status | Verification Summary |
|---|---|---|---|---|
| **R1** | HIGH | 01, 02 | **RESOLVED** | Plan 01 Task 01 decodes pre-rendered `cv_get_action_short_label` (`base.py:638-643`) once via `html.unescape` and strips `SafeData` via `str.__str__(str(val))`; raw `str(owner)`, explicit `NavItem.label`, and child plural names strip `SafeData` without entity decoding; Plan 02 Task 02 autoescapes once. |
| **R2** | HIGH | 04, 05 | **RESOLVED** | Plan 04 Task 01 sets `ParentViewSet(name="navbar_tenant", attribute="tenant")`; Plan 05 Task 01 sets `attribute="customer"` on `Order`/`Address` and `attribute="order"` on `Item` (`parentviewset.py:62-66`, `ancestors.py:158-174`). |
| **R3** | HIGH | 05, 06 | **RESOLVED** | Plan 05 adds `examples/bootstrap5/project/tests.py` to `files_modified`, updates `FeatureGroupsTest.test_grouping_matches_spec` (`project/tests.py:457-477`), and runs `project/tests.py` in Plan 05 Task 03 and Plan 06 Task 03. |
| **R4** | HIGH | 05, 06 | **RESOLVED** | Plan 05 Task 03 equips `navbar-demo-home` with `BreadcrumbMixin`, `{% example_about %}`, `{% cv_breadcrumb %}`, `{% snippet_panels %}`, and unseeded-superuser HTTP 200 (`theming/views.py:21-34`, `project/tests.py:75-81, 238-248, 278-285, 394-403`). |
| **R5** | HIGH | 06 | **RESOLVED** | Plan 06 Task 02 places navbar context docs under a separate `## Object navbar context` heading before `## Snippet variables` (`templates.md:161`) and runs `tests/test1/test_snippet_docs.py` (`test_snippet_docs.py:27-42`). |
| **R6** | HIGH | 05, 06 | **RESOLVED** | Plan 05 Tasks 02/03 keep shared translated login/home/banner notices untouched (`test_i18n.py:186-217`), keep `developer` last in `DEMO_USERS`, and render all three credentials (`alice/alice`, `bob/bob`, `charlie/charlie`) with a login link on `navbar_demo/home.html` and in `docs/getting_started/demo.md`. |
| **R7** | MEDIUM | 01, 03 | **RESOLVED** | Plan 01 Task 01 and Plan 03 Task 02 own a test-local `locmem` / `cv_extends_template` harness for real-request rendering and whole-page byte-parity comparisons without mutating `tests/test1/app/templates/app/crud_views.html`. |
| **R8** | MEDIUM | 01 | **RESOLVED** | Plan 01 Task 03 gates registry-dependent navbar startup checks on `crud_views.checks._url_configuration_loaded()` (`checks.py:172-195`). |
| **R9** | MEDIUM | 01, 03 | **RESOLVED** | Plan 01 Task 01 pre-imports `tests.test1.project.urls` (`test_ancestor_authorization.py:38`); Plan 03 Task 02 resets `_VOCAB_CACHE`, `ViewSet._default_permissions`, `ContentType` cache, and actor/Guardian permission caches for cold measurements. |
| **R10** | MEDIUM | 01 | **RESOLVED** | Plan 01 Task 03 validates non-empty `NavBar.template` at startup via `get_template` / `TemplateDoesNotExist` (`check.py:232-253`). |
| **R11** | MEDIUM | 01 | **RESOLVED** | Plan 01 Tasks 01/03 define construction-time Pydantic field-type checks, allow `items=[]` as a no-output bar, and check missing/empty `NavItem` target selections at startup. |
| **R12** | MEDIUM | 08 | **RESOLVED** | Plan 08 Task 01 wraps the isolated SQLite/settings and `runserver` lifecycle in `try/finally` cleanup and tests cleanup on a deliberate failure path. |
| **R13** | MEDIUM | 01 | **RESOLVED** | Plan 01 Task 01 pins `viewset: str` and `child: str | None` and tests declaration prior to ViewSet registration. |
| **R14** | LOW | 01 | **RESOLVED** | Plan 01 Task 03 rejects every owner attachment with `cv_object=False` (including `card` and custom no-object views). |
| **R15** | MEDIUM | 02, 06 | **RESOLVED** | Plan 02 Task 02 owns `src/crud_views/locale/de/LC_MESSAGES/django.po` and `.mo`, compiles via `polib`, and asserts the German `aria-label` in `test_navbar_templates.py` and `test_i18n.py`. |
| **R16** | MEDIUM | 04 | **RESOLVED** | Plan 04 Task 02 `<verify>` runs `manage.py makemigrations navbar_demo --check --dry-run` in the provisioned example environment. |

### Overall Readiness
- **Actionable plan changes required:** **0** (0 HIGH, 0 MEDIUM, 0 LOW; one non-blocking implementation note on `06.40-01` for `gettext_lazy` evaluation timing).
- **Wave and file ownership:** Disjoint across parallel waves (Plans 03/04 in Wave 3; Plans 07/08 in Wave 6). The plan set is ready for execution.
