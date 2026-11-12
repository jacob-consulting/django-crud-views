---
last_mapped_commit: 6c09417f8f15a93e0e39d8340ec05dba331e82fb
last_mapped_at: 2026-11-11
---
# Codebase Structure

**Analysis Date:** 2026-11-11

## Directory Layout

```text
django-crud-views/
├── src/
│   ├── crud_views/                    # Core Django app: views, shared libraries, theme, assets
│   ├── crud_views_object_detail/       # Rich object detail extension
│   ├── crud_views_workflow/            # django-fsm integration
│   ├── crud_views_polymorphic/         # django-polymorphic integration
│   └── crud_views_guardian/            # django-guardian integration
├── tests/
│   ├── test1/                          # Django test project, models, golden outputs, Python tests
│   ├── js/                             # JavaScript unit tests
│   ├── js-integration/                 # Browser/runtime integration tests
│   └── browser/                        # Browser test support and templates
├── examples/bootstrap5/                # Runnable integrated demo Django project
├── docs/                               # User/developer documentation source
├── site/                               # MkDocs site pages, static docs assets and examples
├── requirements/                       # Split requirements inputs
├── scripts/                            # Repository maintenance/build helpers
├── .planning/                           # GSD plans, research, codebase maps and project state
├── pyproject.toml                      # Python package, tooling and build configuration
├── package.json                        # Browser-side tooling and npm scripts
├── noxfile.py                          # Python/Django test and quality matrix
└── taskfile.yaml                       # Common development task entry points
```

## Directory Purposes

**`src/crud_views/`:**
- Purpose: Core distributable Django application.
- Contains: App startup/checks, CBV integration, shared presentation and utility libraries, management commands, migrations, theme templates, static files, translations, and template tags.
- Key files: `src/crud_views/apps.py`, `src/crud_views/checks.py`, `src/crud_views/lib/view/base.py`, `src/crud_views/lib/viewset/__init__.py`, `src/crud_views/templatetags/crud_views.py`.

**`src/crud_views/lib/viewset/`:**
- Purpose: View registry, URL router, PK handling and parent ViewSet descriptors.
- Contains: `ViewSet`, path regexes and `ParentViewSet`.
- Key files: `src/crud_views/lib/viewset/__init__.py`, `src/crud_views/lib/viewset/parentviewset.py`, `src/crud_views/lib/viewset/path_regs.py`.

**`src/crud_views/lib/view/`:**
- Purpose: CrudView behavior and presentation contracts consumed across concrete CBVs and templates.
- Contains: Base mixin, metaclass, context, action/menu grouping, buttons, card configuration, label modes, variants and visibility resolution.
- Key files: `src/crud_views/lib/view/base.py`, `src/crud_views/lib/view/meta.py`, `src/crud_views/lib/view/context.py`, `src/crud_views/lib/view/action_menu.py`, `src/crud_views/lib/view/buttons.py`.
- Form Cancel URL resolution lives in `src/crud_views/lib/view/base.py`; the template-tag API is in `src/crud_views/templatetags/crud_views.py`, and button data/rendering is in `src/crud_views/lib/view/button_data.py` plus `src/crud_views/templates/crud_views/tags/button/form.html`.
- Snippet metadata is assembled by `CrudView.cv_get_meta()` in `src/crud_views/lib/view/base.py`; child views expose lazy immediate `parent_object`, reusing ancestor-guard state after dispatch and otherwise resolving through the parent URL kwarg. Action/breadcrumb labels, context-button labels, and `LinkChildColumn` templates use separate contexts; see `docs/reference/templates.md`.
- Header icon selection is implemented by `CrudView.cv_get_header_icon()` in `src/crud_views/lib/view/base.py`: only `None` inherits `ViewSet.icon_header`, while `""` suppresses. The public readability constants live in `src/crud_views/lib/icons.py` as plain values (`Icon.VIEWSET_DEFAULT is None`, `Icon.NONE == ""`). Heading templates should use the `cv_heading_icon` projection in `src/crud_views/templatetags/crud_views.py` to place library classes on the host heading and inline icon HTML inside it; getter overrides returning `None` suppress the icon.

**`src/crud_views/lib/ancestors.py`, `ancestor_policy.py`, `ancestor_db.py`:**
- Purpose: Ancestor authorization for nested ViewSets (engine, policy values, default-database boundary).
- Contains: `_authorize_ancestors`, `_walk_ancestors`, `_validate_child_parent`, `_scope_child_queryset`; `AncestorPolicy`/`AncestorPermissions`; `_check_nested_*` database guards.
- Key files: `src/crud_views/lib/ancestors.py`, `src/crud_views/lib/ancestor_policy.py`, `src/crud_views/lib/ancestor_db.py`, `src/crud_views_guardian/lib/ancestors.py` (Guardian provider).
- Tests: `tests/test1/test_ancestor_*.py`, `tests/test1/test_guardian_*.py`, `tests/test1/test_nested_viewset.py`; docs in `docs/reference/nested.md`.
- Nested dispatch must reach `_authorize_ancestors` before the endpoint's state-loading permission check; core permission-required, Guardian, and manage views use dispatch bridges. The resolved chain is cached on the request view for child membership/list scoping and lazy snippet `parent_object` reuse (`src/crud_views/lib/view/base.py`, `src/crud_views_guardian/lib/mixins.py`, `src/crud_views/lib/views/manage.py`).

**`src/crud_views/lib/deletion.py` and `src/crud_views/templates/crud_views/snippets/delete/`:**
- Purpose: Build bounded related-object delete previews and render blocked relationships.
- Contains: Collector-backed relationship summaries, protected-object labels, and preview/truncation presentation.
- Key files: `src/crud_views/lib/deletion.py`, `src/crud_views/lib/views/delete.py`, `src/crud_views/templates/crud_views/view_delete.content.html`, `src/crud_views/templates/crud_views/snippets/delete/protected_objects.html`.

**`src/crud_views/lib/views/`:**
- Purpose: Concrete generic CRUD and action views.
- Contains: List/card/detail/create/update/delete, custom form, manage, child redirect, ordering and common mixins.
- Key files: `src/crud_views/lib/views/list.py`, `src/crud_views/lib/views/card.py`, `src/crud_views/lib/views/detail.py`, `src/crud_views/lib/views/create.py`, `src/crud_views/lib/views/update.py`, `src/crud_views/lib/views/delete.py`, `src/crud_views/lib/views/mixins.py`.

**`src/crud_views/lib/` supporting modules:**
- Purpose: Reusable domain and presentation services that do not belong to a single CBV.
- Contains: Asset registry/pipeline support, resource abstraction, settings, breadcrumbs, icons, buttons, formsets, conditional fields/layouts, table configuration, crispy integration, messages, ordering and session helpers.
- Key files: `src/crud_views/lib/assets.py`, `src/crud_views/lib/pipeline.py`, `src/crud_views/lib/resource.py`, `src/crud_views/lib/settings.py`, `src/crud_views/lib/formsets/`, `src/crud_views/lib/conditional/`, `src/crud_views/lib/table/`, `src/crud_views/lib/crispy/`.

**`src/crud_views/lib/formsets/`:**
- Purpose: Describe, initialize, recursively traverse and adapt nested inline formsets for view context and templates.
- Contains: Public exports in `__init__.py`, recursive declarations in `formsets.py`, compact grid metadata/helper generation in `compact.py`, render-tree nodes in `render_tree.py`, orchestration mixins in `mixins.py`, and layout helpers in `layout.py` / `inline_formset.py`.
- Key files: `src/crud_views/lib/formsets/__init__.py`, `src/crud_views/lib/formsets/formsets.py`, `src/crud_views/lib/formsets/compact.py`, `src/crud_views/lib/formsets/render_tree.py`, `src/crud_views/lib/formsets/mixins.py`.
- Guidance: Add opt-in compact behavior to this package and its formset templates; declare it with `compact_layout` per `FormSet` node. Keep consumer declarations and comparison UI in the example app.
- Custom widgets may inherit the publicly exported `CompactWidgetCompatible` marker alongside their Django widget class to promise complete compact rendering support; this bypasses widget-specific checks only and supplies no rendering behavior. Shared field coverage, roles, effective labels and row consistency are still validated (`src/crud_views/lib/formsets/compact.py`, `src/crud_views/lib/formsets/__init__.py`, `docs/reference/formsets.md`).

**`src/crud_views/templates/crud_views/formsets/`:**
- Purpose: Render the recursive formset tree and its browser controls.
- Contains: `formset.html` for rows and child insertion, `compact_headings.html` for shared headings, control/empty-form partials, plus accompanying static JavaScript and CSS under `src/crud_views/static/crud_views/`.
- Key files: `src/crud_views/templates/crud_views/formsets/formset.html`, `src/crud_views/templates/crud_views/formsets/compact_headings.html`, `src/crud_views/static/crud_views/js/formset.js`, `src/crud_views/static/crud_views/css/formset.css`.
- Guidance: Preserve the existing row/control attributes and JavaScript add/delete/reorder contract when changing markup; compact class hooks are additive and per node.

Compact rendering in `src/crud_views/lib/formsets/compact.py` projects and validates request-time field schemas, then `_compact_helper()` builds crispy layout objects around the existing bound fields and `FormControl`. The exact stock `django.forms.widgets.CheckboxInput` is supported. A custom subclass or custom template requires `CompactWidgetCompatible`; the marker is a compatibility promise, supplies no renderer, and leaves shared role/label/schema validation in force. `src/crud_views/templates/crud_views/formsets/formset.html` continues to own the common row, management form, hidden-field errors, recursion and crispy invocation, preserving the outer form, CSRF, validation and save lifecycle.

**`src/crud_views/templates/crud_views/` and `src/crud_views/static/crud_views/`:**
- Purpose: Bundled Bootstrap 5 theme and browser-side behavior.
- Contains: Full view templates and content partials, tag partials, action/button snippets, formsets, modal shell/content, shared CSS/JS hooks, CSS and JavaScript adapters/components.
- Key files: `src/crud_views/templates/crud_views/view_list.html`, `src/crud_views/templates/crud_views/view_create.html`, `src/crud_views/templates/crud_views/shared/`, `src/crud_views/templates/crud_views/tags/`, `src/crud_views/static/crud_views/js/`, `src/crud_views/static/crud_views/css/`.

**`src/crud_views_object_detail/`:**
- Purpose: Configurable detail properties and layouts, usable by a core detail view.
- Contains: Property/group/link/badge configuration, resolvers, presentation mixin/view, layout packs, type templates, CSS and tab JS.
- Key files: `src/crud_views_object_detail/lib/config.py`, `src/crud_views_object_detail/lib/resolvers.py`, `src/crud_views_object_detail/lib/presentation.py`, `src/crud_views_object_detail/lib/views.py`, `src/crud_views_object_detail/templates/crud_views_object_detail/layouts/`, `src/crud_views_object_detail/templates/crud_views_object_detail/types/`.
- Interactive layouts: `src/crud_views_object_detail/static/crud_views_object_detail/js/tabs.js` scopes tab lifecycle through `cv.adapters.tab`. Accordion markup in `src/crud_views_object_detail/templates/crud_views_object_detail/layouts/accordion/group.html` projects `presentation.selected` into initial classes and ARIA; Bootstrap's existing Collapse data API handles switching and parent-scoped close-all behavior through `data-bs-toggle`, `data-bs-target`, and `data-bs-parent`.

**`src/crud_views_workflow/`:**
- Purpose: FSM transition and history integration.
- Contains: Workflow views/forms/mixins, audit-history models and migrations, templates, app checks and translations.
- Key files: `src/crud_views_workflow/lib/views.py` (request/database orchestration and hooks), `src/crud_views_workflow/lib/execution.py` (shared transition validation and transactional engine plus public helper), `src/crud_views_workflow/lib/forms.py` (transition choices, business blocker and comment validation), `src/crud_views_workflow/lib/widgets.py` (button presentation), `src/crud_views_workflow/lib/mixins.py` (model/history API), and `src/crud_views_workflow/models.py` plus `src/crud_views_workflow/migrations/` (audit persistence).
- Workflow form actions share core form presentation, while workflow badges and content are themed in `src/crud_views_workflow/templates/crud_views_workflow/`; transition permission opt-in examples and regression tests are maintained under `tests/test1/`.

**`src/crud_views_polymorphic/`:**
- Purpose: Polymorphic model CRUD flows.
- Contains: Create type selector, specialized create/update/detail/delete views, shared utilities and app config.
- Key files: `src/crud_views_polymorphic/lib/create_select.py`, `src/crud_views_polymorphic/lib/create.py`, `src/crud_views_polymorphic/lib/utils.py`.

**`src/crud_views_guardian/`:**
- Purpose: Per-object permission-aware ViewSets and management.
- Contains: Specialized ViewSet, permission mixins/views, templates, checks and translations.
- Key files: `src/crud_views_guardian/lib/viewset.py`, `src/crud_views_guardian/lib/mixins.py`, `src/crud_views_guardian/lib/views.py`.

**`tests/`:**
- Purpose: Python/Django behavior tests, browser-side JavaScript contracts and integration harnesses.
- Contains: `tests/test1/` test project, app models and fixtures; `tests/js/`; `tests/js-integration/`; `tests/browser/`; shared helpers/golden files in `tests/lib/` and `tests/test1/golden/`.
- Key files: `tests/test1/conftest.py`, `tests/test1/app/models.py`, `tests/lib/helper/`, `tests/js/helpers/`.

**`examples/bootstrap5/`:**
- Purpose: Consumer-like demo application and integrated examples.
- Contains: Django project settings/URLs, management commands and feature apps demonstrating list/detail/forms, nested data, resources, formsets, conditional fields, object detail, Guardian, workflow, polymorphic views, action menus and breadcrumbs.
- Compact formsets are demonstrated beside classic formsets in `examples/bootstrap5/formsets/views.py`: `cv_formsets` remains the classic recursive tree and `cv_compact_formsets` opts questions and choices in independently. The `compact_create` and `compact_update` views provide comparison routes without changing the default create/update flow. A separate Checklist CRUD family (`Checklist` / `ChecklistItem`) in the same feature app demonstrates a stock BooleanField checkbox in compact rows; its schema is in `models.py` and migration `migrations/0003_checklist_checklistitem.py`. `examples/bootstrap5/project/features.py` keeps one shared Formsets catalog/source-panel entry; `examples/bootstrap5/project/templatetags/example_tags.py` derives an additional nav-only Checklist link and active URL state from it.
- Key files: `examples/bootstrap5/project/settings_demo.py`, `examples/bootstrap5/project/urls.py`, `examples/bootstrap5/project/management/commands/seed.py`.

**`docs/` and `site/`:**
- Purpose: Documentation content and static site output/source support.
- Contains: Getting-started, reference and development material, localized/documentation assets, screenshots and JavaScript documentation examples.
- Key files: `docs/`, `site/`, `mkdocs.yml`.

**`.planning/`:**
- Purpose: GSD planning lifecycle, phase artifacts, research, codebase analyses and project-level state.
- Contains: `.planning/codebase/`, `.planning/phases/`, `.planning/research/`, `.planning/quick/` and other workflow artifacts.

## Test Layout Notes

- `tests/test1/` holds ~280 flat `test_<feature>.py` modules (ancestor, button, cancel, card, formsets, guardian, workflow, resource, pipeline, docs-sync checks); sub-packages `tests/test1/od/` (object detail) with fixtures in `tests/test1/od_app/`, test models in `tests/test1/app/models.py`, project settings in `tests/test1/project/`.
- `tests/browser/` holds Node `*.test.cjs` browser tests with Python fixture servers (`*_server.py`); `tests/js/` vitest units; `tests/js-integration/` integration.
- Docs tests (`test_*_docs.py`) execute marked snippets from `docs/reference/*.md`. `examples/bootstrap5/` has its own `pytest.ini`, `test_docs_sync.py`, `test_i18n.py`.

## Detail and Composition Navigation

- `src/crud_views_object_detail/lib/conf.py`: object-detail settings singleton, including automatic-help default.
- `src/crud_views_object_detail/lib/config.py`: strict help instructions and `choices_display` property configuration.
- `src/crud_views_object_detail/lib/resolvers.py`: terminal metadata, scalar-owner traversal, help selection, and additive choice labels.
- `src/crud_views_object_detail/templatetags/crud_views_object_detail.py`: raw/display context and value-template dispatch.
- `tests/test1/od/test_choice_display.py` and `tests/test1/od/test_help_text_policy.py`: choice/help/query/lazy-policy regressions; fixtures live in `tests/test1/od_app/models.py`.
- `tests/test1/test_object_detail_value_docs.py`: extracts and executes marked Python/Django recipes from published references and migration instructions.
- `src/crud_views/templates/crud_views/tags/card.html`: empty `card_root`/`card_header` extension blocks preserve stock output; `tests/test1/test_card_blocks.py` exercises overrides.
- `tests/test1/test_polymorphic_docs.py` and `docs/reference/polymorphic_view.md`: executable form-mapping guidance; selector labels are implemented in `src/crud_views_polymorphic/lib/create_select.py`.

## Key File Locations

**Entry Points:**
- `src/crud_views/apps.py`: Core Django app config and registration of core checks.
- `src/crud_views/lib/viewset/__init__.py`: Public `ViewSet` definition and generated `urlpatterns`.
- `src/crud_views/lib/view/meta.py`: Import-time CrudView class registration hook.
- `examples/bootstrap5/project/settings_demo.py`: Demo project's Django settings.
- `examples/bootstrap5/project/urls.py`: Demo URL wiring.

**Configuration:**
- `pyproject.toml`: Build backend, package metadata, Python dependencies and Ruff/coverage configuration.
- `taskfile.yaml`: Common task aliases.
- `noxfile.py`: Environment matrix and test sessions.
- `package.json`, `vitest.config.js`, `vitest.integration.config.js`: JavaScript development and browser test configuration.
- `src/crud_views/lib/settings.py`: `CRUD_VIEWS_*` Django setting model and defaults.
- `render.yaml`: Demo hosting/deployment configuration.

**Core Logic:**
- `src/crud_views/lib/viewset/__init__.py`: ViewSet registration, routing and queryset behavior.
- `src/crud_views/lib/view/base.py`: CrudView cross-cutting behavior and context/link APIs.
- `src/crud_views/lib/views/`: Concrete request handlers.
- `src/crud_views/lib/view/`: Presentation/action resolution contracts.
- `src/crud_views/lib/assets.py`: Static asset bundles and rendering registry.
- `src/crud_views/lib/resource.py`: Non-ORM row interface.
- `src/crud_views/lib/deletion.py`: Bounded delete preview and protection collection.
- `src/crud_views/lib/table/table.py`: `Table` base (view context, `actions` column, `Meta.sequence`-aware default ordering).
- `src/crud_views/lib/view/base.py`: `cv_get_meta()` creates page-snippet metadata; `cv_get_parent_object()` returns the immediate parent using the request's resolved ancestor when available; `cv_get_header_icon()` applies the None-only ViewSet fallback.
- `src/crud_views/lib/icons.py`: semantic icon registry and plain public `Icon.VIEWSET_DEFAULT` / `Icon.NONE` constants.
- `src/crud_views/lib/formsets/compact.py`: explicit compact layout declarations, validated form schema projection, compact heading metadata and per-form crispy helper generation.
- `src/crud_views/lib/formsets/render_tree.py`: recursive formset context tree; chooses compact helper generation only for nodes with `compact_layout` set.
- `examples/bootstrap5/formsets/views.py`: classic/compact formset declarations and opt-in create/update comparison views.

**Presentation and Browser Behavior:**
- `src/crud_views/templates/crud_views/`: Core theme templates and reusable partials.
- `src/crud_views/static/crud_views/`: Core CSS/JavaScript.
- `src/crud_views/templatetags/crud_views.py`: `{% cv_heading_icon %}` host-class/inline-HTML projection, standalone icon tag, snippet-facing tags and theme API.
- `src/crud_views_object_detail/templates/crud_views_object_detail/`: Object detail layout and field rendering packs.
- `src/crud_views_object_detail/static/crud_views_object_detail/js/tabs.js`: Object-detail tab lifecycle bridge loaded through asset registration in `src/crud_views_object_detail/apps.py`.

**Testing:**
- `tests/test1/`: Python/Django tests and test app.
- `tests/test1/test_workflow_execution.py`: public transition helper and view execution, validation/refusal, transaction, callback, and multi-database routing contracts.
- `tests/test1/test_table_meta.py`: `Table` honours `Meta.sequence`, `sequence` kwarg precedence and `Meta.exclude` of `actions` (Phase 06.19).
- `tests/js/`: JavaScript unit tests.
- `tests/js-integration/`: JavaScript integration tests.
- `tests/browser/`: Browser test harness assets.
- `noxfile.py`: Supported Python/Django test matrix.

## Naming Conventions

**Files:**
- Python modules use lowercase snake_case, usually matching their class/feature (`src/crud_views/lib/views/action_ordered.py`, `src/crud_views/lib/view/action_menu.py`).
- Django template files use descriptive view/partial names, with paired full/content templates where a view supports partial rendering (`view_create.html`, `view_create.content.html` in `src/crud_views/templates/crud_views/`).
- Browser source and tests use lowercase kebab/dotted feature names (`src/crud_views/static/crud_views/js/list.filter.js`, `tests/js/list.filter.test.js`).
- Extension apps use the `crud_views_<feature>` package prefix.

**Directories:**
- Python implementation is organized by concern under `lib/` (`view/`, `viewset/`, `views/`, `formsets/`, `conditional/`, `table/`).
- Django apps use conventional `templates/<app namespace>/`, `static/<app namespace>/`, `templatetags/`, `locale/<language>/LC_MESSAGES/` and optional `migrations/` paths.
- Examples are grouped under `examples/bootstrap5/<feature>/` with their own models, views, URLs and migrations where useful.

## Where to Add New Code

**New Feature:**
- Primary code: Add a reusable core abstraction under `src/crud_views/lib/`; add a request handler to `src/crud_views/lib/views/` when it is a new view type.
- Tests: Add Python behavior tests in the nearest `tests/test1/` feature module; extend browser tests under `tests/js/` or `tests/js-integration/` when client behavior changes.
- User-facing theme: Add/update the corresponding template in `src/crud_views/templates/crud_views/`, Python template-tag/context support in `src/crud_views/templatetags/` or `src/crud_views/lib/view/`, and static behavior in `src/crud_views/static/crud_views/`.
- Formset presentation: Extend `src/crud_views/lib/formsets/` and `src/crud_views/templates/crud_views/formsets/`; preserve classic rendering as the `compact_layout=None` path and add a demonstration under `examples/bootstrap5/formsets/`.
- Interactive object-detail layouts: Put markup in `src/crud_views_object_detail/templates/crud_views_object_detail/layouts/<layout>/`. For tabs, use the existing scoped lifecycle bridge in `src/crud_views_object_detail/static/crud_views_object_detail/js/tabs.js` and `cv.adapters.tab`; for accordion markup, preserve Bootstrap Collapse data attributes and render initial selected state from `presentation.selected` in the template.
- Nested/ancestor authorization changes: edit `src/crud_views/lib/ancestors.py` (engine), `src/crud_views/lib/ancestor_policy.py` (config values), `src/crud_views/lib/ancestor_db.py` (database boundary); add tests as `tests/test1/test_ancestor_<aspect>.py` and update `docs/reference/nested.md`.
- Demonstration: Add or update an example app under `examples/bootstrap5/<feature>/` and connect it through `examples/bootstrap5/project/`.
- For form cancellation behavior, extend the request-aware resolver in `src/crud_views/lib/view/base.py` and its focused tests; preserve template access through `{% cv_cancel_url %}`.
- For deletion relationship previews, change the collector/summary behavior in `src/crud_views/lib/deletion.py` and the corresponding partials in `src/crud_views/templates/crud_views/snippets/delete/`; keep protected references as plain labels and preserve the display budget.
- For workflow presentation or permission examples, use `src/crud_views_workflow/lib/` and its templates; document and test permission checks as opt-in per transition.
- For workflow business blockers or execution semantics, implement the model-only `workflow_check_transition(name, *, user)` contract in the consumer model, keep shared validation/execution in `src/crud_views_workflow/lib/execution.py`, and test public helper plus request behavior in `tests/test1/test_workflow_execution.py`. Do not treat business blockers as permission checks: django-fsm permissions/conditions gate transition availability, while the workflow view's page permission remains separately enforced.

**New Component/Module:**
- Implementation: Place cross-view concepts in the closest `src/crud_views/lib/<concern>/` package; place a concrete Django CBV in `src/crud_views/lib/views/`.
- Optional integration: Keep dependencies and specialized behavior in a dedicated `src/crud_views_<integration>/` app, following existing extension package layouts.
- Object detail feature: Put config, resolution and view behavior under `src/crud_views_object_detail/lib/`; templates/assets belong to that app's namespace.

**Utilities:**
- Shared helpers: Use focused modules under `src/crud_views/lib/`; if a helper is specific to presentation, put it in `src/crud_views/lib/view/` rather than in an unrelated generic utility.
- Template API: Add tags to `src/crud_views/templatetags/crud_views.py` or `src/crud_views/templatetags/crud_views_formsets.py`; keep HTML in theme templates.
- Static assets: Add files under `src/crud_views/static/crud_views/` and configure/register them through `src/crud_views/lib/settings.py` and `src/crud_views/lib/assets.py` as appropriate.

## Special Directories

**`src/`:**
- Purpose: Source-layout Python packages included in the built distribution.
- Generated: No.
- Committed: Yes.

**`src/*/templates/`, `src/*/static/`, `src/*/locale/`:**
- Purpose: Django-discovered extension templates, static files and translations.
- Generated: Source files are maintained in the repository; compiled translation `.mo` files are present alongside `.po` sources.
- Committed: Yes.

**`tests/test1/golden/`:**
- Purpose: Expected rendered-output fixtures used to check presentation compatibility.
- Generated: Some fixtures are generated/updated by project test helper workflows; treat them as test artifacts and inspect diffs.
- Committed: Yes.

**`node_modules/`, `.nox/`, `.pytest_cache/`, `.ruff_cache/`:**
- Purpose: Local JavaScript dependencies, nox environments and tool caches.
- Generated: Yes.
- Committed: No; do not place product source here.

**`.planning/`:**
- Purpose: Project planning, mapping, research, phase execution and workflow artifacts.
- Generated: Workflow-produced and human-maintained.
- Committed: Yes in this repository workflow; keep codebase maps scoped to `.planning/codebase/`.

## Label Override Navigation (Phase 06.20)

- `src/crud_views/lib/viewset/__init__.py`: display-name fields, plain-string validation and `get_meta()` resolution; `src/crud_views/lib/lazy.py` supplies the existing lazy type.
- `tests/test1/test_viewset_verbose_name.py`: defaults, independent fields, lazy language/construction behavior, Resource and Guardian inheritance, nested list heading.
- `tests/test1/test_viewset_verbose_name_render.py`: headings/paragraphs, precedence, breadcrumb HTML, child links/buttons and message delivery.
- `docs/reference/nested.md#labels`: contract and replacement declaration example; `docs/reference/breadcrumb.md`: variable semantics; `CHANGELOG.md`: issue #338 entry.

## Permission declaration locations (Phase 06.22)

- `src/crud_views/checks.py`: local and ancestor `viewset.E269` message builders inside the completed-registry check.
- `src/crud_views/lib/ancestors.py`: private concrete-model vocabulary, suffix normalization, provider eligibility and shared pair-source helpers.
- `src/crud_views/lib/viewset/__init__.py`: runtime permission-map population reuses the shared normalizer.
- `tests/test1/test_permission_declarations.py`: declaration diagnostics, concrete-model boundaries, exclusions and zero-query checks.
- `tests/test1/test_ancestor_docs.py`: executable custom-permission recipe and cross-link tests; `tests/test1/app/models.py` declares Author's `contact_author` permission while preserving OrderedModel Meta options.
- `docs/reference/custom_form_view.md#a-permission-of-its-own`: canonical model/view recipe; action, Guardian and nested reference pages link or explain the applicable boundaries.

## Header icons and snippet context (Phase 06.23)

- `src/crud_views/lib/view/base.py`: `cv_get_header_icon()` uses the view value unless it is `None`, then falls back to `cv_viewset.icon_header`; `cv_get_meta()` provides ViewSet metadata, optional `object`, `view`, and lazy `parent_object` for nested views.
- `src/crud_views/lib/icons.py`: import `Icon.VIEWSET_DEFAULT` and `Icon.NONE` from `crud_views.lib.icons`; these public constants are plain `None` and empty-string values. Do not treat them as enum/sentinel instances.
- `src/crud_views/templatetags/crud_views.py`: `cv_heading_icon` splits selected icon presentation into host classes and inline markup for heading templates. Use the documented page/modal recipes in `docs/reference/templates.md`; a custom getter returning `None` suppresses rather than falling back again.
- `docs/reference/templates.md#snippet-variables`: canonical snippet variable list and distinctions among page snippets, target action/breadcrumb labels, context-button labels, and `LinkChildColumn` context. Child `parent_object` is lazy and reuses request-authorized ancestor state after dispatch.
- `tests/test1/test_heading_icons.py`, `tests/test1/test_snippet_docs.py`: header selection/rendering and documented snippet context contracts.

## Compact Checklist example navigation

- `examples/bootstrap5/formsets/models.py`: separate `Checklist` and `ChecklistItem` models, including the ordinary optional `done` BooleanField.
- `examples/bootstrap5/formsets/migrations/0003_checklist_checklistitem.py`: creates both Checklist tables and the child relationship.
- `examples/bootstrap5/formsets/views.py`: independent `cv_checklist` ViewSet and list/create/update flow; `ChecklistForm` places `Formsets()` in its crispy layout and the inline child opts in with `CompactLayout` for `label` and `done`.
- `examples/bootstrap5/formsets/urls.py`: combines the Questionnaire and Checklist ViewSet URL patterns.
- `examples/bootstrap5/project/features.py`: keep one shared Formsets feature record and source/code panel for both examples.
- `examples/bootstrap5/project/templatetags/example_tags.py`: derive the direct Checklist navbar entry from the existing Formsets feature and keep active navigation associated with that shared record; do not add a second catalog feature.

---

*Structure analysis: 2026-11-11*
