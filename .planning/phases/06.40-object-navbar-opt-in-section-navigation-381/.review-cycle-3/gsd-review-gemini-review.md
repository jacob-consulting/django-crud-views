## 06.40-01

### 1. Summary
Plan `06.40-01` delivers the core opt-in navbar module (`src/crud_views/lib/navbar.py` with `NavBar`, `NavItem`, `CrudViewNavBarMixin`, and private resolution/check helpers), the context-taking `{% cv_navbar %}` template tag (`src/crud_views/templatetags/crud_views.py`), the guarded layout-B wrapper (`src/crud_views/templates/crud_views/tags/navbar.html`), and the real-request routing and startup-check suites (`tests/test1/test_navbar.py` and `tests/test1/test_navbar_checks.py`). It closes prior cycle findings `R1`, `R7`, `R8`, `R9`, `R10`, `R11`, `R13`, `R14` and Round 2 findings `R17` and `R18`.

### 2. Strengths
- **Explicit Sign-Off on `R17` (Owner-Bound `ViewContext.object` for Short Action Labels)**: `CrudView.cv_get_action_short_label(cls, context: ViewContext)` (`src/crud_views/lib/view/base.py:638-643`) delegates to `cls.cv_viewset.get_meta(context)` (`src/crud_views/lib/viewset/__init__.py:517-540`), which merges `context.to_dict()` (`:539`), where `ViewContext.to_dict()` returns `{"object": self.object}` (`src/crud_views/lib/view/context.py:44-45`). Passing the rendering view's own `ViewContext` on a descendant page would therefore expose the `Order` or `Item` instance as `{{ object }}` inside an owner item's short-label template. Revised Task `06.40-01-01` (`.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-01-PLAN.md:83`) and Task `06.40-01-02` (`06.40-01-PLAN.md:94-96`) explicitly construct a request-local `ViewContext(view=rendering_view, object=owner)` after access and state pass without mutating the rendering view or shared declarations, and test an object-dependent short-label template across real owner, child, and grandchild requests with distinct captions.
- **Explicit Sign-Off on `R18` (`owner_viewset.pk_name` Route Metadata vs. `owner.pk` Model Value)**: `ViewSet.pk_name` (`src/crud_views/lib/viewset/__init__.py:79`, consumed by `ViewSet.get_path_pk` at `:421`) holds the URL kwarg name on the `ViewSet`, whereas `ParentViewSet.get_pk_name()` (`src/crud_views/lib/viewset/parentviewset.py:56-60`) holds the parent URL kwarg name on a child edge. Task `06.40-01-02` (`06.40-01-PLAN.md:95`) now unambiguously specifies `owner_viewset.pk_name` as the route argument name and `owner.pk` as the model instance value for owner links, and `child.parent.get_pk_name()` with `owner.pk` for child links.
- **Preserves `R1`, `R7`, `R8`, `R9`, `R10`, `R11`, `R13`, and `R14` Closure**:
  - `R1`: `CrudView.render_snippet` (`src/crud_views/lib/view/base.py:578-592`) renders templates with autoescaping and wraps the output in `mark_safe(result.strip())`. Task `06.40-01-01` (`06.40-01-PLAN.md:83`) normalizes only `cv_get_action_short_label` via a single `html.unescape` pass followed by `str.__str__(str(value))`, while stripping `SafeData` without entity decoding on raw `str(owner)`, explicit `NavItem.label`, and child plural names.
  - `R7` & `R9`: Uses a test-local `locmem` template loader and `cv_extends_template` (`src/crud_views/lib/view/base.py:426-431`) inside `tests/test1/test_navbar.py` without editing `tests/test1/app/templates/app/crud_views.html`, and pre-imports `tests.test1.project.urls` before snapshotting `_REGISTRY`, `check_module._VOCAB_CACHE` (`src/crud_views/lib/check.py:341`), and `ViewSet._default_permissions` (`src/crud_views/lib/viewset/__init__.py:109, 489-505`).
  - `R8`, `R10`, `R11`, `R13`, `R14`: Keeps `viewset` and `child` as late-bound `str` fields (`06.40-01-PLAN.md:83`), gates registry-dependent checks on `crud_views.checks._url_configuration_loaded()` (`src/crud_views/checks.py:172-195`) in Task `06.40-01-03` (`06.40-01-PLAN.md:107`), validates non-empty `NavBar.template` via `get_template` / `TemplateDoesNotExist` (`src/crud_views/lib/check.py:232-253`), allows `items=[]` as a valid no-output bar while rejecting `NavItem()` or empty keys at startup, and rejects all owner attachments where `cv_object=False`.
- **Guards Explicit Keys Against `"list" -> "card"` Fallback and Reuses Request Ancestors**: Checks `viewset.is_view_registered(key)` (`src/crud_views/lib/viewset/__init__.py:372-373`) before `get_view_class` or `get_router_name` (`:375-388`), and resolves descendant owners via `_resolved_ancestor(view, owner_name)` (`src/crud_views/lib/ancestors.py:576-585`) without additional ORM queries.

### 3. Concerns
None — `R17`, `R18`, and all prior Round 1 findings on Plan 01 (`R1`, `R7`, `R8`, `R9`, `R10`, `R11`, `R13`, `R14`) are fully resolved in executable task specifications.

### 4. Suggestions
- None.

### 5. Risk Assessment
**LOW** — All routing, label-context, escaping, and startup-check invariants are grounded in concrete repository mechanisms.

---

## 06.40-02

### 1. Summary
Plan `06.40-02` splits `src/crud_views/templates/crud_views/tags/navbar.html` into `navbar_identity.html` and `navbar_items.html`, locks the 1.0 public template context contract (`cv_navbar.object`, `label`, `icon`, `items`; `item.label`, `icon`, `url`, `active`), adds the German translation entry to `src/crud_views/locale/de/LC_MESSAGES/django.po` and `.mo`, and verifies lazy evaluation, overrides, escaping, and i18n in `tests/test1/test_navbar_templates.py` and `tests/test1/test_i18n.py`.

### 2. Strengths
- **Preserves `R1` and `R15` Closure**:
  - Task `06.40-02-02` (`.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-02-PLAN.md:101`) consumes the plain `str` values produced by Plan 01 without double-escaping and tests parsed text and attribute values across `&`, `'`, entity-looking strings, and `SafeString` markup.
  - Task `06.40-02-02` owns `src/crud_views/locale/de/LC_MESSAGES/django.po` and `django.mo`, adds `msgid "Sections for %(object)s"` / `msgstr "Abschnitte für %(object)s"`, compiles `.mo` via `polib` (`pyproject.toml:81`, verified by `tests/test1/test_i18n.py:65-90`), and asserts the rendered German `aria-label` under `translation.override("de")`.
- **Single-Build `SimpleLazyObject` Contract Across Tag and Split Partials**: Mirrors the `SimpleLazyObject` pattern in `src/crud_views/lib/views/manage.py:1013-1019` and uses a context-taking `@register.simple_tag(takes_context=True)` (`src/crud_views/templatetags/crud_views.py:457-471`) rather than a fixed `@register.inclusion_tag` (`:446-449`), enabling `NavBar(template=...)`, global wrapper overrides, leaf overrides, and split partial includes from one shared request-local build.
- **Avoids Landmark/Active-Marker Collisions and Global Asset Drift**: Uses `aria-current="true"` on the active `<a class="nav-link active">` inside `<nav aria-label="...">` with `nav nav-pills flex-wrap`, avoiding any collision with `examples/bootstrap5/project/tests.py:499-503` (`<nav class="navbar`) or `:544` (`aria-current="page"` count in top navbar), and adds no global CSS entry to `CrudViewsSettings.css` (`src/crud_views/lib/settings.py:353-362`).

### 3. Concerns
None — no remaining actionable plan gaps.

### 4. Suggestions
- None.

### 5. Risk Assessment
**LOW** — Template context, lazy evaluation, escaping, and German locale compilation are fully specified and tested.

---

## 06.40-03

### 1. Summary
Plan `06.40-03` verifies D-09 access-then-state admission across plain and Guardian views in `tests/test1/test_navbar_permissions.py` and measures hook/SQL costs plus whole-page nonparticipant byte parity in `tests/test1/test_navbar_costs.py` and `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-COST.md`. It closes prior findings `R7`, `R9`, and Round 2 finding `R19`.

### 2. Strengths
- **Explicit Sign-Off on `R19` (Cold Guardian Content-Type Cache Reset via `clear_ct_cache()`)**: In `tests/test1/test_guardian_child_link_visibility.py:1052-1059`, `reset_discovery(links)` calls `ContentType.objects.clear_cache()` (`:1056`) and `guardian.shortcuts.clear_ct_cache()` (`:1057`) alongside resetting `_default_permissions` (`:1058-1059`), because `django-guardian` caches content types separately from Django's `ContentType` manager. Revised Task `06.40-03-02` (`.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-03-PLAN.md:91`) and the Round 2 ledger (`06.40-03-PLAN.md:141-147`) explicitly include `guardian.shortcuts.clear_ct_cache()` in the cold-vocabulary reset and record that condition in `06.40-COST.md`.
- **Preserves `R7` and `R9` Closure**: Task `06.40-03-02` (`06.40-03-PLAN.md:91`) reuses Plan 01's `locmem` / `cv_extends_template` harness for whole-response `response.content` byte comparisons between tag-free and tag-present base templates on no-mixin and `cv_navbar=None` views, and resets `check_module._VOCAB_CACHE` (`src/crud_views/lib/check.py:341`), participating `ViewSet._default_permissions` (`src/crud_views/lib/viewset/__init__.py:109, 489-505`), `ContentType.objects.clear_cache()`, `clear_ct_cache()`, and actor permission caches.
- **Exact Once-Only Child Hook and Access-Before-State Ordering**: Calls `target._cv_child_link_has_access(user, owner)` (`src/crud_views/lib/view/base.py:528-541`, `src/crud_views_guardian/lib/views.py:387-390`) once per child item and only invokes `target._cv_action_enabled_for_rendering(user, owner, rendering_view)` (`src/crud_views/lib/view/base.py:564-566`) after permission passes, while propagating `ImproperlyConfigured` from `_immediate_parent_access` (`src/crud_views/lib/ancestors.py:654-686`).

### 3. Concerns
None — `R19` and prior findings `R7` and `R9` are completely resolved.

### 4. Suggestions
- None.

### 5. Risk Assessment
**LOW** — Permission hooks, state adapters, and cold/warm measurement resets match existing repository helpers.

---

## 06.40-04

### 1. Summary
Plan `06.40-04` creates the self-contained `examples/bootstrap5/navbar_demo` app with `Tenant` and `Customer` models, `0001_initial.py`, `GuardianViewSet` for `Tenant`, core `ViewSet` for `Customer` (`Details` and `Notes` detail views), and `/object-navbar/` routes. It preserves closure of `R2` and `R16`.

### 2. Strengths
- **Preserves `R2` Closure (`ParentViewSet(name="navbar_tenant", attribute="tenant")`)**: Because `ParentViewSet.get_attribute()` (`src/crud_views/lib/viewset/parentviewset.py:62-66`) defaults to `self.viewset.name`, and `_validate_relationship` (`src/crud_views/lib/ancestors.py:158-174`) looks up that field on the child model, Task `06.40-04-01` (`.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-04-PLAN.md:83`) explicitly sets `attribute="tenant"` on `Customer`'s `ParentViewSet(name="navbar_tenant", attribute="tenant")` and tests the relationship through system checks, queryset filtering, GETs, and parent-bound creation.
- **Preserves `R16` Closure (Executable Migration Drift Gate)**: Task `06.40-04-02` (`06.40-04-PLAN.md:99-100`) runs `.venv/bin/nox -s "examples-3.12(django='5.2')" -- -n 4 -q navbar_demo/tests.py` followed by `(cd examples/bootstrap5 && PYTHONPATH=../../src:. ../../.nox/examples-3-12-django-5-2/bin/python manage.py makemigrations navbar_demo --check --dry-run)` so any model/migration mismatch fails verification immediately.
- **Clean Registry Isolation and Deferred `FEATURES` Registration**: Uses `navbar_tenant` and `navbar_customer` to avoid colliding with `conditional`'s `customer` ViewSet in `_REGISTRY` (`src/crud_views/lib/viewset/__init__.py:47`), and defers `FEATURES` registration until `navbar_demo/seed.py` exists in Plan 05 (`examples/bootstrap5/project/management/commands/seed.py:18-19`).

### 3. Concerns
None — no remaining actionable plan gaps.

### 4. Suggestions
- None.

### 5. Risk Assessment
**LOW** — Disjoint from Plan 03 in Wave 3, with explicit parent-attribute mapping and migration drift verification.

---

## 06.40-05

### 1. Summary
Plan `06.40-05` completes the `navbar_demo` hierarchy (`Order`, `Item`, `Address` and `0002_order_item_address.py`), adds idempotent seeding for `alice`, `bob`, and `charlie` (`navbar_demo/seed.py`, `project/seeding.py`, `project/management/commands/seed.py`), builds `navbar_demo/templates/navbar_demo/home.html`, registers `navbar_demo` in `project/features.py` and `project/tests.py`, and places `{% cv_navbar %}` in `examples/bootstrap5/project/templates/project/crud_views.html`. It preserves closure of `R2`, `R3`, `R4`, and `R6`.

### 2. Strengths
- **Preserves `R2` Closure Across Descendants**: Task `06.40-05-01` (`.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-05-PLAN.md:91`) sets `ParentViewSet(name="navbar_customer", attribute="customer")` on `Order` and `Address` and `ParentViewSet(name="navbar_order", attribute="order")` on `Item` (`src/crud_views/lib/viewset/parentviewset.py:62-66`), and includes a `makemigrations navbar_demo --check --dry-run` regression after `0002_order_item_address.py`.
- **Preserves `R3` and `R4` Closure (Shared `project/tests.py` Contracts and Standalone Landing Page)**:
  - Task `06.40-05-03` (`06.40-05-PLAN.md:113-119`) owns `examples/bootstrap5/project/tests.py`, updating `FeatureGroupsTest.test_grouping_matches_spec` (`examples/bootstrap5/project/tests.py:457-477`) to append `"navbar_demo"` to the `"ui"` group.
  - Models `navbar-demo-home` on `ThemeIndexView` with `project.views.BreadcrumbMixin`, `{% example_about %}`, `{% cv_breadcrumb %}`, `{% snippet_panels %}`, and HTTP 200 for an unseeded superuser (`examples/bootstrap5/project/tests.py:75-81, 238-248, 278-285, 506-559`).
  - Runs `navbar_demo/tests.py project/tests.py test_i18n.py -k 'not DocRefsPanelTest'` in Wave 4 before Plan 06 populates `Feature.docs` and runs the unfiltered suite.
- **Preserves `R6` Closure (Credential Discoverability Without Breaking Shared Translated Notices)**: Adds `("charlie", "charlie", False)` before `("developer", "developer", False)` in `DEMO_USERS` (`examples/bootstrap5/project/seeding.py:5-10`) and updates `seed.py` output while leaving the shared `login.html`, `home.html`, and `base.html` notices unchanged, satisfying `test_demo_account_notices_include_developer` and `test_published_demo_credentials_match_seed_output` (`examples/bootstrap5/test_i18n.py:185-217`) and listing all three credentials (`alice/alice`, `bob/bob`, `charlie/charlie`) on `navbar_demo/home.html`.

### 3. Concerns
None — no remaining actionable plan gaps.

### 4. Suggestions
- None.

### 5. Risk Assessment
**LOW** — Shared example test contracts, seeding invariants, and ancestor policies are fully aligned with repository source.

---

## 06.40-06

### 1. Summary
Plan `06.40-06` authors `docs/reference/navbar.md`, updates `docs/reference/index.md`, `nested.md`, `context_buttons.md`, `breadcrumb.md`, `templates.md`, `theme.md`, `docs/getting_started/demo.md`, `docs/development/stability.md`, and `CHANGELOG.md`, adds executable doc tests in `tests/test1/test_navbar_docs.py`, and connects `Feature.docs` in `examples/bootstrap5/project/features.py` with verification via `examples/bootstrap5/test_doc_links.py` and the unfiltered `examples/bootstrap5/project/tests.py`. It preserves closure of `R3`, `R4`, `R5`, `R6`, and `R15`.

### 2. Strengths
- **Preserves `R5` Closure (`## Snippet variables` Table Integrity in `docs/reference/templates.md`)**: `tests/test1/test_snippet_docs.py:27-42` extracts `## Snippet variables` up to the next `\n## ` heading and asserts that the markdown table rows match the exact 8 `VARIABLES` (`:15-24`). Task `06.40-06-02` (`.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-06-PLAN.md:107-109`) places navbar template context documentation under a separate `## Object navbar context` level-two heading *before* `## Snippet variables` and executes `tests/test1/test_snippet_docs.py` directly in its `<verify>` step.
- **Preserves `R3`, `R4`, and `R6` Closure with Unfiltered Example & Doc-Link Verification**: Task `06.40-06-03` (`06.40-06-PLAN.md:117-120`) attaches the `DocRef` for `reference/navbar.md` to `navbar_demo` in `examples/bootstrap5/project/features.py` and runs `.venv/bin/nox -s "examples-3.12(django='5.2')" -- -n 4 -q navbar_demo/tests.py project/tests.py test_i18n.py test_doc_links.py` with no `-k` exclusion.
- **Complete 1.0 Stability Inventory (`D-16`)**: Explicitly inventories `NavBar`, `NavItem`, `CrudViewNavBarMixin`, `cv_navbar`, the three `crud_views/tags/navbar*.html` templates, and the documented `cv_navbar` / `item` context attributes in `docs/development/stability.md` while keeping private helpers internal.

### 3. Concerns
None — no remaining actionable plan gaps.

### 4. Suggestions
- None.

### 5. Risk Assessment
**LOW** — Documentation, stability inventory, snippet-variable schema, and reciprocal `DocRef` links are covered by automated gates.

---

## 06.40-07

### 1. Summary
Plan `06.40-07` acquires or verifies an isolated checkout of `https://github.com/jacob-consulting/skills` at `../skills-navbar-06-40`, updates the four tracked skill files (`plugins/django-crud-views/skills/django-crud-views/SKILL.md`, `references/templates-and-navigation.md`, `references/api-reference.md`, and `plugins/django-crud-views/CHANGELOG.md`), runs `scripts/validate.py`, creates a scoped local commit on `docs/navbar-06.40`, and writes `.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-COMPANION-DELIVERY.md`.

### 2. Strengths
- **Grounded External Skill Delivery (`docs/development/index.md:87-91`)**: Correctly targets the separate `jacob-consulting/skills` repository at `../skills-navbar-06-40` rather than creating dead files in `django-crud-views` or editing installed skill mirrors.
- **Fail-Closed Provenance and Validation Gates**: Task `06.40-07-01` and Task `06.40-07-02` (`.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-07-PLAN.md:74-96`) verify git remote identity, `git ls-files` tracking on all four target paths, native validation via `.venv/bin/python ../skills-navbar-06-40/scripts/validate.py`, and commit hygiene via `git -C ../skills-navbar-06-40 show --check --oneline HEAD`, treating any missing checkout or failed validation as an explicit unmet gate.

### 3. Concerns
None — environmental availability at execution time is explicitly gated fail-closed.

### 4. Suggestions
- None.

### 5. Risk Assessment
**LOW** — Well-bounded companion documentation update with explicit repository provenance and native validator checks.

---

## 06.40-08

### 1. Summary
Plan `06.40-08` executes live Playwright viewport/reflow and keyboard navigation checks (`06.40-BROWSER-CHECK.js` producing `06.40-BROWSER.json`, `06.40-desktop.png`, `06.40-narrow-focus.png`) against an isolated SQLite database configured via `.pytest_cache/navbar_browser_settings.py`, runs the full source and installed Nox test matrices (`noxfile.py:20-222`), and records final acceptance in `06.40-ACCEPTANCE.md` and `06.40-VALIDATION.md`. It preserves closure of `R12`.

### 2. Strengths
- **Preserves `R12` Closure (`try/finally` Process and Transient-File Cleanup)**: Task `06.40-08-01` (`.planning/phases/06.40-object-navbar-opt-in-section-navigation-381/06.40-08-PLAN.md:83`) wraps the temporary SQLite directory, `.pytest_cache/navbar_browser_settings.py`, and `runserver 127.0.0.1:8765 --noreload` lifecycle in an outer `try/finally` block that fails if port `8765` or the settings path is already occupied, terminates and awaits only the owned server PID, removes the transient settings module/bytecode and temp DB directory across all exit paths, and verifies cleanup via a deliberate failing assertion before the passing run.
- **Complete Matrix and Floor Coverage (`noxfile.py:20-222`)**: Task `06.40-08-02` (`06.40-08-PLAN.md:91-106`) runs cached Django 4.2/5.2/6.0 source suites, `nox -s tests examples crispy_floor -- -n 4 -q` (which runs both normal and `CV_ACCESS_RECORD_REQUESTS=1` passes at `noxfile.py:36-57` and the `format_html` AST audit at `noxfile.py:170-198`), `nox -s manage_report_floor` at Pydantic `2.2.1` (`noxfile.py:88-107`) with all six `test_navbar*.py` modules, `mkdocs build --strict`, `ruff check`, `ruff format --check`, `npm test`, and `nox -s package` (`noxfile.py:216-222`).

### 3. Concerns
None — no remaining actionable plan gaps; runtime/browser availability is gated fail-closed as future execution evidence.

### 4. Suggestions
- None.

### 5. Risk Assessment
**LOW** — Process/file cleanup is deterministic, and all matrix, floor, and browser checks fail closed if unavailable.

---

## Cross-Plan Conclusions

### 1. Verification of Prior Cycle Closure (`R1`–`R16`) and Re-Evaluation of `R17`–`R19`

Closure of `R1`–`R16` remains sound and intact across all eight plans. Re-evaluation of `R17`–`R19` against the repository source, revised `06.40-01-PLAN.md` and `06.40-03-PLAN.md`, and Round 2 ledgers confirms complete resolution with zero residual gaps:

| ID | Severity | Plan(s) | Verdict | Source & Plan Verification |
|---|---|---|---|---|
| **R17** | MEDIUM | `06.40-01` | **SIGNED OFF (CLOSED)** | `CrudView.cv_get_action_short_label` (`src/crud_views/lib/view/base.py:638-643`) -> `ViewSet.get_meta` (`src/crud_views/lib/viewset/__init__.py:517-540`) -> `ViewContext.to_dict` (`src/crud_views/lib/view/context.py:44-45`). `06.40-01-PLAN.md:83` (Task 01) and `:94-96` (Task 02) bind `ViewContext(view=rendering_view, object=owner)` after admission and test an object-dependent short-label template across owner, child, and grandchild requests with distinct captions. |
| **R18** | LOW | `06.40-01` | **SIGNED OFF (CLOSED)** | `ViewSet.pk_name` (`src/crud_views/lib/viewset/__init__.py:79`) vs. `ParentViewSet.get_pk_name()` (`src/crud_views/lib/viewset/parentviewset.py:56-60`) vs. model `owner.pk`. `06.40-01-PLAN.md:95` (Task 02) specifies `owner_viewset.pk_name` as the route argument name and `owner.pk` as its value for owner links, and `child.parent.get_pk_name()` with `owner.pk` for child links. |
| **R19** | LOW | `06.40-03` | **SIGNED OFF (CLOSED)** | `reset_discovery` (`tests/test1/test_guardian_child_link_visibility.py:1052-1059`) calls `guardian.shortcuts.clear_ct_cache()` (`:1057`) alongside `ContentType.objects.clear_cache()` (`:1056`). `06.40-03-PLAN.md:91` (Task 02) and Round 2 ledger (`:146`) include `guardian.shortcuts.clear_ct_cache()` in the cold-vocabulary reset and record it in `06.40-COST.md`. |
| **R1–R16** | HIGH / MEDIUM / LOW | `01`–`06`, `08` | **SIGNED OFF (CLOSED)** | All 16 prior dispositions remain intact in `06.40-01-PLAN.md` through `06.40-08-PLAN.md` and match the underlying repository mechanisms. |

### 2. Coverage Limitations and Grounding Notes
- **Grounding Adapter Authority**: Effective source-grounding authority resolves to `intel` (`.planning/intel/API-SURFACE.md`), which indexes JS only; Python symbols/signatures are `UNCHECKABLE` by that adapter and are independently verified above via direct repository file reads.
- **Phase-Status Seam Limitation**: The deterministic phase-status seam reports `phase_not_in_roadmap` (`uncheckable`), even though the Phase `06.40` section is present at `.planning/ROADMAP.md:2118-2151`; this is recorded as a tool coverage limitation, not plan drift.
- **Future Execution Checks vs. Plan Obligations**: Provisioning `.nox/examples-3-12-django-5-2`, acquiring `../skills-navbar-06-40`, discovering Python 3.13/3.14 runtimes, and running Playwright browser checks in `06.40-04`, `06.40-07`, and `06.40-08` are future execution checks with explicit fail-closed gates, not missing plan obligations.

### 3. Unresolved HIGH and Concrete Actionable Non-HIGH Plan Gaps
- **Unresolved `HIGH` concerns**: **0**
- **Concrete actionable non-`HIGH` (`MEDIUM`/`LOW`) plan gaps**: **0**

All eight plans across nineteen tasks and six waves are converged and ready for execution.
