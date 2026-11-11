---
last_mapped_commit: 702469fe04c5d27262391e04a52d78904a93659f
last_mapped_at: 2026-11-11
---
# Coding Conventions

**Analysis Date:** 2026-11-11

## Maintainability Constraint

- Keep behavior understandable, explainable, and maintainable by the project developer. Prefer the simplest bounded solution that meets a demonstrated need, preserve proven paths unless a concrete defect or requirement warrants change, and account for runtime and cognitive costs (`CLAUDE.md`).
- Favor self-contained, opt-in additions that can demonstrate downstream value before wider integration. Passing tests or covering more cases alone does not justify added complexity (`CLAUDE.md`, `superpowers/notes/2026-11-04-opt-in-url-helper-decision.md`).

## Naming Patterns

**Files:**
- Python modules use lowercase snake_case; Django test modules use `test_*.py` (`src/crud_views/lib/view/base.py`, `tests/test1/test_crud.py`). Object-detail tests are grouped under `tests/test1/od/`.
- JavaScript unit and integration files use descriptive names ending in `.test.js` under `tests/js/` and `tests/js-integration/`; Node browser tests use `.test.cjs` under `tests/browser/`.

**Functions:**
- Python functions, pytest fixtures, and test functions use snake_case; tests begin with `test_` and name an observable behavior.
- JavaScript functions and variables use camelCase. Workflow transitions use the `wf_` prefix (`tests/test1/app/models.py`).

**Variables:**
- Use descriptive snake_case in Python and camelCase in JavaScript. Fixtures encode model and permission, such as `client_user_author_add` in `tests/test1/conftest.py`.

**Types:**
- Python classes use CapWords (`ViewSet`, `CrudView`). Add annotations to public APIs where useful; supported Python begins at 3.12 (`pyproject.toml`).
- JavaScript helpers use named exports, as in `tests/js/helpers/load.js`.

## Code Style

**Formatting:**
- Use Ruff formatting: 120-character line length, spaces, and double quotes (`pyproject.toml`).
- Preserve template and golden HTML formatting when output markup is asserted byte-for-byte (`tests/lib/helper/golden.py`, `tests/test1/golden/`).

**Linting:**
- Ruff selects `E`, `F`, `I`, `UP`, `B`, `C4`, `SIM`, and `RUF`; tests, examples, and migrations ignore `RUF012` (`pyproject.toml`).
- Pre-commit runs `ruff-check` and `ruff-format` (`.pre-commit-config.yaml`).

## Import Organization

**Order:**
1. Python standard library.
2. Third-party packages, including Django and pytest.
3. Package imports (`crud_views...`) and test support (`tests...`).

Ruff's `I` rules enforce Python import sorting. JavaScript tests import runner and Node modules before local helpers (for example `tests/js/formset.test.js`).

**Path Aliases:**
- No Python import aliases are configured; import from the owning module. JavaScript test loading maps shipped source paths explicitly in `tests/js/helpers/load.js`.

## Error Handling

**Patterns:**
- Raise Django exceptions and validation errors at request or model boundaries; test observable status, redirect, form errors, and persisted state (`tests/test1/test_resource.py`, `tests/test1/test_crud.py`).
- Keep workflow business validation in the model's `workflow_check_transition(name, *, user)` hook (`src/crud_views_workflow/lib/mixins.py`); it should be inexpensive, side-effect-free, and raise single/list `ValidationError` messages. It supplements django-fsm availability/permission/condition gates and is not an authorization mechanism (`src/crud_views_workflow/lib/execution.py`, `tests/test1/test_workflow_execution.py`).
- The workflow engine converts expected business/comment refusals into field errors; unrelated `ValidationError` from transition/callback code propagates as a defect. Sanitize user-visible blocker messages into plain text before adding them to forms so a `SafeString` cannot inject markup (`src/crud_views_workflow/lib/execution.py`).
- Browser event listener errors are collected from `window` error events through `tests/js/helpers/errors.js`; DOM dispatch does not reliably rethrow them synchronously.
- Ancestor authorization configuration uses strict Pydantic values: `AncestorPermissions` and `AncestorPolicy` set `ConfigDict(strict=True, extra="forbid")`, require complete `nearest`/`higher` pairs and reject whitespace-padded keys (`src/crud_views/lib/ancestor_policy.py`). Keep policy values free of request/user/grant state; the evaluation engine lives in `src/crud_views/lib/ancestors.py`, DB-alias handling in `src/crud_views/lib/ancestor_db.py`, Guardian adapters in `src/crud_views_guardian/lib/ancestors.py`.
- Invalid ancestor/permission-map configuration raises `ImproperlyConfigured` at request/registration time and is surfaced by system checks in `src/crud_views/checks.py`; unavailable context (no parent, ambiguous M2M) stays unavailable rather than raising (`tests/test1/test_ancestor_helpers.py`).
- Ancestor authorization order is a tested contract: anonymous/inactive actor and missing parent are decided before any child queryset call (`tests/test1/test_ancestor_authorization.py`).

## Logging

**Framework:** Python standard logging where needed; no project-wide logging wrapper is configured. Browser scripts use console APIs.

**Patterns:**
- Avoid noisy normal-operation logging. Browser tests capture expected listener errors and assert on them; `tests/js/helpers/setup.js` silences expected console chatter.

## Comments

**When to Comment:**
- Explain non-obvious compatibility constraints, fixture/server synchronization, and harness workarounds (`tests/js/helpers/dom.js`, `tests/js/helpers/load.js`).

**Docstrings:**
- Use concise docstrings for helpers and fixtures whose setup is not self-evident; let test names carry ordinary behavior descriptions.

## Function Design

**Size:** Keep helpers focused; factor complex test setup into fixtures or local helpers.

**Parameters:** Prefer explicit pytest fixture dependencies and small options objects for reusable JavaScript DOM fixtures (`tests/js/helpers/dom.js`).

**Return Values:** Return concrete responses or data from helpers; assert observable output, database state, rendered markup, and DOM state.

## Presentation and Published Recipes

- Preserve raw values and expose display metadata separately. Object-detail callbacks and custom templates retain raw `value`; stock leaves consume `display_value` (`src/crud_views_object_detail/lib/resolvers.py`, `src/crud_views_object_detail/templatetags/crud_views_object_detail.py`).
- Treat booleans as explicit policy instructions only where declared: `PropertyConfig.detail` accepts `StrictBool`, lazy/string text or None. Avoid truthiness/string conversion of lazy help during resolution (`src/crud_views_object_detail/lib/config.py`, `src/crud_views_object_detail/lib/resolvers.py`).
- Keep rendered empty values exact: None/empty strings differ from zero, False, spaces and collections. Preserve escaping, newline behavior and custom-template ownership.
- Published examples use unique HTML recipe markers beside fenced snippets, enabling tests to execute the actual documentation (`tests/test1/test_object_detail_value_docs.py`). Format Markdown Python fences with the repository-wide Ruff command.
- Before 1.0, pair a `### Breaking` changelog entry with `docs/migrating-1.0.md`; document restoration/opt-out recipes for changed defaults (`CLAUDE.md`).
- Instance snippets receive the `cv` object and a deliberately small, documented context (`view`, `object`, model labels, and `viewset`; child views additionally receive lazy `parent_object`). Keep the metadata key set exact; do not add request/user/ancestor state to this published context (`src/crud_views/lib/view/context.py`, `src/crud_views/lib/view/base.py`, `tests/test1/test_snippet_context.py`, `tests/test1/test_snippet_docs.py`).
- When publishing snippet variables, keep `docs/reference/templates.md#snippet-variables` canonical and link other reference pages to it. Tests execute snippet behavior and pin the exact key sets as well as lazy parent resolution and absent-key behavior (`tests/test1/test_snippet_docs.py`, `tests/test1/test_snippet_context.py`).
- Table behavior should preserve explicit django-tables2 customization: default `actions` placement is last only absent a declared sequence, explicit constructor sequence takes precedence, and `Meta.exclude` can remove it (`src/crud_views/lib/table/table.py`, `tests/test1/test_table_meta.py`).
- Button data is normalized to an explicit location-specific contract; preserve exact key sets and each leaf's tag/URL/submit-target semantics. Use `tests/test1/test_button_data.py` and golden/render tests when changing button fields or markup.

## Module Design

**Exports:** Keep Python imports explicit. JavaScript test helpers use named exports.

**Barrel Files:** No general barrel-file pattern detected; import from the owning module.

## JavaScript Conventions

- Use ES modules, double-quoted strings, semicolons, and camelCase identifiers in the Vitest harness (`tests/js/formset.test.js`).
- Import Vitest APIs explicitly (`describe`, `it`, `expect`, lifecycle hooks, and `vi`) and import Node modules via `node:` specifiers (`tests/js/formset.test.js`).
- Load shipped browser scripts through `tests/js/helpers/load.js`; do not duplicate production logic in test helpers. Build DOM state with focused fixtures from `tests/js/helpers/dom.js` and reset globals/mocks via shared setup and per-test hooks (`tests/js/helpers/setup.js`).

## Test Isolation Conventions

- Treat module registries, warning deduplication sets, URL caches, and Django ContentType caches as shared process state. Snapshot and restore state using fixtures or `monkeypatch`, including teardown paths (`tests/conftest.py`, `tests/test1/test_ancestor_authorization.py`).
- For temporary ViewSet registration or URLconf replacement, restore registries and Django URL caches in `finally` blocks so randomized test order remains safe (`tests/test1/test_ancestor_authorization.py`).
- Prefer strict configuration validation and exact output assertions where behavior is public: tests pin complete button data key sets, metadata key sets, and system-check diagnostics (`tests/test1/test_button_data.py`, `tests/test1/test_snippet_context.py`, `tests/test1/test_permission_declarations.py`).

## Lazy Label Configuration (Phase 06.20)

- Preserve unset metadata paths and resolve explicit overrides centrally in `get_meta()` (`src/crud_views/lib/viewset/__init__.py`).
- Validate only plain blank strings at construction. Avoid stringifying lazy translations during app loading, normalizing padded strings, inferring plurals or using parent display names (`src/crud_views/lib/lazy.py`, `docs/reference/nested.md#labels`).
- Tests monkeypatch existing shared ViewSets/views; constructor probes remove registry entries under `_REGISTRY_LOCK` in `finally` or teardown (`tests/test1/test_viewset_verbose_name.py`, `tests/test1/test_viewset_verbose_name_render.py`).

## Static permission checks (Phase 06.22)

- Use concrete-model metadata for declared core permission vocabulary and remove only the exact terminal `_<model_name>` suffix. Share `_permission_key` with the runtime map (`src/crud_views/lib/ancestors.py`, `src/crud_views/lib/viewset/__init__.py`).
- Completion-dependent diagnostics belong behind the existing URLconf barrier; do not read Permission/ContentType rows at startup (`src/crud_views/checks.py`).
- Keep declaration helpers private and preserve the distinct ownership of existing error codes/provider exclusions. Publish one executable recipe rather than duplicating application examples (`docs/reference/custom_form_view.md`, `tests/test1/test_ancestor_docs.py`).

## Header Icon Values (Phase 06.23)

- `Icon` in `src/crud_views/lib/icons.py` is a plain class of semantic constants, not an enum: `Icon.VIEWSET_DEFAULT` is literally `None`, and `Icon.NONE` is literally `""`. Use these names to make view-header configuration readable (`docs/reference/icons.md`).
- On `cv_icon_header` only, `None` inherits `ViewSet.icon_header`; every non-None value is the view's explicit choice. Empty string and `Icon.NONE` suppress the header icon. Do not use truthiness fallback for this attribute (`src/crud_views/lib/view/base.py`, `tests/test1/test_heading_icons.py`).
- Keep this context-specific meaning separate from general icon resolution: `Icon.VIEWSET_DEFAULT` has no ViewSet-fallback meaning in action or object-detail icon slots (`src/crud_views/lib/icons.py`, `docs/reference/icons.md`).
- Custom heading text/template selection is independent of icon inheritance/suppression. Preserve custom file/code header content while testing icon selection (`tests/test1/test_heading_icons.py`, `tests/test1/test_heading_docs.py`).

---

## Compact Formset Declarations and Rendering (Phase 06.24)

- Keep compact layout declarations explicit and immutable: use `CompactColumn(field_name, span=...)` and `CompactLayout(columns, controls_span=...)`; the public API is re-exported from `src/crud_views/lib/formsets/__init__.py`. Constructors reject coercion, positional convenience, duplicate/ambiguous fields, and non-instance `FormSet.compact_layout` values (`src/crud_views/lib/formsets/compact.py`, `tests/test1/test_formsets_compact.py`).
- Compact rendering is an opt-in projection over the existing recursive formset renderer. Preserve classic custom helper/layout behavior, request-local resolved labels, form-owned field errors and row controls. Keep heading includes independently overridable and headings outside their owning rows (`src/crud_views/lib/formsets/render_tree.py`, `src/crud_views/templates/crud_views/formsets/formset.html`, `tests/test1/test_formsets_compact.py`).
- When declaring nested compact examples, define a separate compact formset tree rather than mutating/reusing the classic tree. Use normal `InlineFormSet` factories and existing CRUD routes/actions so authorization and persistence stay on the proven view path (`examples/bootstrap5/formsets/views.py`, `.planning/phases/06.24-opt-in-compact-formsets-shared-desktop-headings-and-nested-m/06.24-06-SUMMARY.md`).
- For example navigation, use existing labelled action menus and keep classic/compact labels visible on list rows; mobile layout should be achieved through existing theme behavior rather than a new menu or CSS mechanism (`examples/bootstrap5/formsets/views.py`, `examples/bootstrap5/formsets/tests.py`).

## Independent Legend Class Hooks (Phase 06.25.1)

- Add presentation hooks through the existing layered button-class registry, with separate keys for independent consumers (`conditional:legend`, `formset:legend`). Both keys default to `""`; keep empty overrides meaningful and preserve the existing default rendering (`src/crud_views/lib/button_classes.py`, `tests/test1/test_button_classes.py`).
- Registry precedence is defaults → installed theme registrations → `CRUD_VIEWS_BUTTON_CLASSES`; cache invalidation follows theme registration and settings changes. Tests that register theme classes should snapshot/restore `bc._THEME_BUTTON_CLASSES` and reset the cache around each test (`tests/test1/test_button_classes_checks.py`, `tests/test1/test_conditional_layout.py`, `tests/test1/test_formsets_compact.py`).
- Keep legend text as ordinary template-interpolated values and classes in quoted attributes. Test hostile plain strings at both boundaries by asserting escaped source output, exact parsed text/attribute values, and absence of injected nodes (`src/crud_views/templates/crud_views/conditional/toggle_group.html`, `src/crud_views/templates/crud_views/formsets/formset.html`, `tests/test1/test_conditional_layout.py`, `tests/test1/test_formsets_compact.py`).
- Preserve markup ownership: ToggleGroup without a legend remains a `div`; formset row-only fragments omit their own outer fieldset/legend, while nested full formsets retain their own direct legends. Assert direct-child ownership and fragment roots rather than banning all descendant legends (`tests/test1/test_conditional_layout.py`, `tests/test1/test_formsets_compact.py`).
- Button-class reference inventories are executable contracts: core has 90 keys and the effective core-plus-workflow inventory has 100. Update the canonical table, reference docs, workflow inventory, and embedded fresh-process guard together (`tests/test1/test_button_classes.py`, `tests/test1/test_theme_adoption_docs.py`, `docs/reference/buttons.md`).

*Convention analysis: 2026-11-11*
