---
last_mapped_commit: 7cdb6f2b2f609b4ac8b586b06ff05630a8da42cd
last_mapped_at: 2026-11-21
---
# Coding Conventions

**Analysis Date:** 2026-11-21

## Naming Patterns

**Files:**
- snake_case modules, one concern per file: `src/crud_views/lib/views/delete.py`, `action_ordered.py`, `label_mode.py`.
- View modules mirror the view key (`list.py`, `detail.py`, `create.py`, `update.py`, `delete.py`).
- Tests: `tests/test1/test_<topic>.py`, flat, topic-prefixed families (`test_access_trace_*.py`, `test_ancestor_*.py`, `test_action_menus_*.py`).
- Keep a feature's tests split by contract where that makes failures easier to locate. Bulk action tests use focused files such as `tests/test1/test_bulk_source.py` (selection UI), `test_bulk_scope.py` (request keys and authorization boundaries), `test_bulk_flow.py` (review/execution lifecycle), and `test_bulk_return.py` (navigation).
- Navbar contracts are split among `tests/test1/test_navbar.py`, `test_navbar_templates.py`, `test_navbar_costs.py`, `test_navbar_checks.py`, `test_navbar_permissions.py`, and `test_navbar_docs.py`; keep tests beside the behavior they verify.

**Functions:**
- snake_case. Private helpers have a leading underscore and are imported across modules when needed (for example `_walk_ancestors`, `_check_nested_alias` in `src/crud_views/checks.py`, `src/crud_views/lib/views/delete.py`).
- Workflow transition methods use the `wf_` prefix.

**Variables / class attributes:**
- Every `CrudView` class attribute uses the `cv_` prefix: `cv_key`, `cv_path`, `cv_success_key`, `cv_context_actions`, `cv_header_template`, `cv_icon_action`, `cv_modal_supported`.
- Module-level constants are UPPER_SNAKE (`TAG`, `_REGISTRY`, `_REGISTRY_LOCK`, `GOLDEN_DIR`). Sentinels are `_NAME_UNSET = object()`.
- Process-wide theme registration is a module scalar with a public register/get API (`src/crud_views/lib/data_prefix.py`, re-exported from `src/crud_views/lib/__init__.py`); validate the complete value before assignment. This is a startup-only setting: register from `AppConfig.ready()`, and do not build runtime theme switching or request-scoped behavior on top of it.
- View keys match CRUD operations: `list`, `detail`, `create`, `update`, `delete`, `workflow`, `manage`.
- Permission mapping: list/detail -> view, create -> add, update -> change, delete -> delete.
- Settings read from Django settings use the `CRUD_VIEWS_*` prefix.

**Types / classes:**
- PascalCase. Concrete views `<Op>View`, permission variants `<Op>ViewPermissionRequired`, Guardian variants `Guardian<Op>ViewPermissionRequired`.
- Pydantic models for config: `ViewSet`, `CrudViewsSettings`, `Check` subclasses.

## Code Style

**Formatting:**
- `ruff format` (pre-commit hook `ruff-format`, `.pre-commit-config.yaml`). Line length 120, double quotes, space indent (`pyproject.toml` `[tool.ruff]`).
- Run `task format` / `task check`.

**Linting:**
- `ruff check` with `select = ["E", "F", "I", "UP", "B", "C4", "SIM", "RUF"]`.
- `RUF012` (mutable ClassVar) is ignored in `tests/**`, `examples/**`, migrations. In `src/`, annotate mutable class attributes: `http_method_names: ClassVar[list[str]] = [...]`.
- `›` is allowed as a confusable (breadcrumb separator).
- Ruff excludes `superpowers/**` and `.planning/**`.
- Modern typing: `str | None`, `list[str]`, `collections.abc.Iterable` (UP rules).

## Import Organization

**Order (ruff isort):**
1. stdlib (`logging`, `collections.abc`, `functools`)
2. third-party (`django`, `pydantic`, `crispy_forms`)
3. first-party absolute imports (`from crud_views.lib.settings import crud_views_settings`)

**Path Aliases:** None. Use absolute package imports (`crud_views.lib...`, `crud_views_workflow.lib...`); tests import helpers as `from tests.lib.helper.user import ...`.

## Error Handling

**Patterns:**
- Misconfiguration raises `django.core.exceptions.ImproperlyConfigured`, or `ValueError` in Pydantic validators with messages naming the setting and the bad value (`f"... got {value!r}"`), see `src/crud_views/lib/viewset/__init__.py`.
- `CRUD_VIEWS_STRICT` (True in tests) makes misconfigurations raise; with it off they log a warning instead.
- Startup validation goes through Django system checks (`src/crud_views/checks.py`, `src/crud_views/lib/check.py`): yield `Error(id="viewset.E...", msg=...)` / `Warning` objects; check classes are Pydantic models (`CheckAttribute`, `CheckMapping`, `CheckEitherAttribute`, `CheckTemplateOrCode`).
- Custom exceptions live in `src/crud_views/lib/exceptions.py` (for example `ViewSetKeyFoundError`).
- Delete flow guards HTTP DELETE via `_DeleteMethodGuardMixin` and returns 405.

## Logging

**Framework:** stdlib `logging`; one `logger = logging.getLogger(__name__)` per module (`src/crud_views/lib/views/delete.py`, `lib/view/label_mode.py`, `templatetags/crud_views.py`).
- Warnings for deduplicated configuration problems (once per location/value via a module `_warned` set).

## Comments

**When to Comment:**
- Docstrings explain why and MRO/ordering constraints (see `_DeleteMethodGuardMixin` in `src/crud_views/lib/views/delete.py`). Inline comments explain intent, often referencing issue numbers (`#264`, `#103`).
- Group class attributes with lowercase section comments (`# related objects`, `# texts and labels`, `# icons`, `# messages`).

## Function Design

**Size:** Small helpers; larger behavior is split into mixins (`CrudViewProcessFormMixin`).
**Parameters:** Views are configured via class attributes, not constructor args.
**Return Values:** Check functions are generators yielding Error/Warning; template tags return context dicts.

## Module Design

**Exports:** Import from the defining module or package `__init__` (`from crud_views.lib.view import CrudView, CrudViewPermissionRequiredMixin`). No wildcard imports.
**Barrel Files:** `crud_views/lib/view/__init__.py` and `lib/viewset/__init__.py` re-export core classes.

## Template and Lazy Rendering Contracts

- Keep public template seams explicit. The navbar wrapper and independently usable identity/items components are `src/crud_views/templates/crud_views/tags/navbar.html`, `navbar_identity.html`, and `navbar_items.html`; tags are registered in `src/crud_views/templatetags/crud_views.py`. Themes can compose the independent tags directly, and absent data renders empty output.
- Preserve the request-local `SimpleLazyObject` context value for `cv_navbar`. Repeated context creation, copies, and includes share one evaluation per response; different requests must not share actor-specific results. See `tests/test1/test_navbar_templates.py::test_context_copies_and_repeated_calls_reuse_one_lazy_build` and `::test_separate_requests_do_not_share_users_or_results`.
- Avoid navbar permission, action-state, or SQL work when navigation is omitted or a modal suppresses it. Cover both template and real-response layers (`tests/test1/test_navbar_templates.py::test_omitted_consumers_and_modal_direct_includes_do_no_work`, `::test_real_response_omits_all_navbar_work_without_consumers_or_in_custom_modal`).
- Treat labels and accessible names as plain text, including `SafeString` inputs. Test escaping and one-time entity normalization through `tests/test1/test_navbar_templates.py::test_plain_labels_and_accessible_names_are_escaped_once`; do not mark caller-controlled text safe to bypass escaping.
- Keep query budgets and categories explicit when cost is contractual. `tests/test1/test_navbar_costs.py::test_navbar_isolated_costs` captures SQL for plain/Guardian/mixed configurations and cold/warm caches, asserting no parent/child-row or deep-object query leaks into rendering. `::test_nonparticipant_complete_response_bytes_and_queries` protects exact response bytes and SQL equality with and without navbar integration.

## Breadcrumb Classes and Table Ordering

- Route breadcrumb styling through the existing class registry in `src/crud_views/lib/button_classes.py`: `breadcrumb:list` styles the `ol`, `breadcrumb:item` every `li`, and `breadcrumb:item-active` the final item. Use `{% cv_button_class "breadcrumb" "list" %}` and equivalent slots in `src/crud_views/templates/crud_views/tags/breadcrumb.html`; theme registration contributes defaults and `CRUD_VIEWS_BUTTON_CLASSES` takes precedence.
- Preserve structural and accessibility semantics when class contributions are empty, invalid, or hostile. The final breadcrumb item keeps `aria-current="page"` independently of its classes; labels remain escaped, links retain their destinations, and class values cannot introduce attributes. See `tests/test1/test_breadcrumb.py::test_breadcrumb_class_overrides` and `::test_breadcrumb_current_page_independent_of_classes`.
- Derive stock table sort state from the bound column (`column.is_ordered` and `column.order_by_alias.is_descending`), as in `src/crud_views/templates/crud_views/table/bootstrap5.html`. Use the same effective state for icons and `aria-sort`; this includes constructor ordering, `Meta.order_by`, and prefixed URL ordering. Preserve `table.prefixed_order_by_field` when generating the next sort link.
- Give orderable headers exactly one `aria-sort` value (`ascending`, `descending`, or `none`); nonorderable headers omit it and the sort link. Preserve custom header attributes, escaped labels, and unrelated query parameters. Use `tests/test1/test_table_template.py::test_table_header_effective_sort_state` and `::test_table_header_attributes_and_links` as the contract.

## Documentation Test Conventions

- When docs publish copyable recipes, extract the exact fenced block and execute it against project objects/views. Follow `tests/test1/test_navbar_docs.py`, `test_object_detail_value_docs.py`, `test_cancel_docs.py`, and `test_theme_adoption_docs.py`; avoid maintaining a retyped example that can drift.
- For rendering recipes, use Django `Template`, real request/context/response fixtures, and parsed DOM assertions. Verify public semantics and documented inventories/cross-links alongside recipe behavior.
- For published registration examples, extract and execute the exact fenced recipe in `tests/test1/test_data_prefix_docs.py::test_data_prefix_documented_registration`; verify default, repeat-ready, and last-registration behavior through the real `{% cv_data_prefix %}` tag. Keep all calls scoped to startup registration.

## Global Scalar Isolation

- Tests that register a theme prefix opt into `isolate_data_prefix` from `tests/test1/conftest.py`. It snapshots the current scalar through `monkeypatch` and restores it after the test; use the fixture on every test that changes the registration. Do not make it autouse, because modules that do not register a prefix need no additional global-state handling.
- Keep invalid registration atomic: validate first, raise `ValueError` for invalid input, and assert the previous value remains intact (`tests/test1/test_data_prefix.py::test_data_prefix_invalid_values_preserve_state`).
- Preserve default output using named frozen raw captures. Authorized template changes should compare exact output and explain each byte delta; do not normalize or regenerate captures to make a changed render pass (`tests/test1/test_data_prefix.py::test_data_prefix_default_component_bytes`, `::test_data_prefix_config_byte_delta`).

## Project Rules

- Decision rule (`CLAUDE.md`): prefer the simplest bounded solution the maintainer can explain; keep new features opt-in and self-contained; avoid hidden state and extra queries on existing paths.
- Preserve contracts with focused tests at the public seam. For bulk selection, keep source-page rendering free of destination permission work (`tests/test1/test_bulk_source.py`), validate and canonicalize submitted keys before hooks (`tests/test1/test_bulk_scope.py`), and exercise transaction rollback for multi-record failures (`tests/test1/test_bulk_flow.py`). Avoid duplicating implementation complexity in tests when a small observable contract assertion suffices.
- Until 1.0.0, a `### Breaking` entry in `CHANGELOG.md` also requires an update to `docs/migrating-1.0.md`.
- Version bumps go through bump-my-version (`task bump-patch`); never edit version strings by hand.

## CSS Token Contract Tests

- Keep CSS tests bounded to the two owned stylesheets `src/crud_views/static/crud_views/css/manage.css` and `formset.css`; add a stylesheet to the scanner only when ownership is explicitly expanded.
- `tests/js/css-tokens.test.js` checks the documented six `--cv-*` properties, component-to-Bootstrap fallback chains, and rejected/accepted declaration forms. Keep parser expectations tied to the small Node-only sandbox in `tests/js/helpers/load.js`; do not turn this into a general CSS parser or add browser/runtime dependencies.
- Use `tests/browser/css-tokens.cjs` for computed browser checks across the documented CSS cases. Manage presentation and compact formset browser suites remain separate: `tests/browser/manage-presentation.cjs` checks page smoke states, and `tests/browser/conditional-formsets.cjs` verifies compact layout behavior.
- For capture tooling changes, preserve default historical capture destinations and isolate phase captures with `--compact-capture-root`. Exercise `compactCapture` and `validateEvidence` together in `tests/browser/conditional-formsets-evidence.test.cjs`; reject outside-root, traversal, missing/stale files, unsafe Git destinations, symlink leaves, and non-file leaves before writing. Validate `--check-evidence` separately from browser capture and preserve historical PNG bytes.

## JavaScript Source and Runtime Boundaries

- Shipped browser code is plain JavaScript under `src/crud_views/static/crud_views/js/` and
  `src/crud_views_object_detail/static/crud_views_object_detail/js/`. Keep it compatible with the declared Node
  `>=20` test runtime and browser globals; do not add a framework or transpilation step for a small behavior change.
- JavaScript tests use ES modules, Vitest `describe`/`it`/`expect`, and jsdom (`package.json`, `vitest.config.js`).
  Load the actual shipped script with `loadScript()` from `tests/js/helpers/load.js`; fixtures should construct the
  DOM shape consumed by the public script and assert visible state, events, fetch payloads, or navigation calls.
  Shared browser globals are initialized and reset in `tests/js/helpers/setup.js`.
- jsdom cannot perform real navigation. Route navigation through the existing `nav` proxy from
  `tests/js/helpers/load.js` and assert `nav.assign` / `nav.href`; do not replace jsdom's unforgeable
  `window.location` or introduce browser-only assumptions into ordinary unit tests.
- Keep source/runtime boundary checks in `tests/js/runtime-contract.test.js`. That suite launches Vitest in a
  disposable directory containing only the JS tree and selected docs/goldens, with a PATH containing Node only.
  It confirms that every ordinary JS test is included, that there are no Python or venv dependencies, and that the
  integration lane fails explicitly when `CV_FRAGMENT_PYTHON` is absent or invalid. Update the explicit ordinary
  file inventory there when adding or renaming a test.
- Put cross-runtime cases in `tests/js-integration/` and configure them through
  `vitest.integration.config.js`; do not make `npm test` acquire a Python dependency. Select the installed test
  interpreter explicitly with `CV_FRAGMENT_PYTHON`, and preserve the virtualenv launcher path (`path.resolve`, not
  realpath) so the intended environment remains selected. See `docs/reference/javascript.md` for runnable commands.
- For server-configured JS, render configuration through Django's real `{% cv_config %}` tag in
  `tests/js-integration/js-config.test.js`, pass the rendered element to jsdom, and then execute the shipped JS
  against that configuration. For generated formset fragments, keep the Django test client/database responsible
  for rendering and POST validation; pass the actual returned DOM and `FormData` through the disposable Node driver
  in `tests/js-integration/formset.test.js` and `tests/test1/test_fragment_authorization.py`.

---

*Convention analysis: 2026-11-21*
