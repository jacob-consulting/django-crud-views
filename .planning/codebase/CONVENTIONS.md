---
last_mapped_commit: 782d6f34fc2adf2509ab8a8a150e69266a3e7e2a
last_mapped_at: 2026-11-19
---
# Coding Conventions

**Analysis Date:** 2026-11-19

## Naming Patterns

**Files:**
- snake_case modules, one concern per file: `src/crud_views/lib/views/delete.py`, `action_ordered.py`, `label_mode.py`.
- View modules mirror the view key (`list.py`, `detail.py`, `create.py`, `update.py`, `delete.py`).
- Tests: `tests/test1/test_<topic>.py`, flat, topic-prefixed families (`test_access_trace_*.py`, `test_ancestor_*.py`, `test_action_menus_*.py`).
- Navbar contracts are split among `tests/test1/test_navbar.py`, `test_navbar_templates.py`, `test_navbar_costs.py`, `test_navbar_checks.py`, `test_navbar_permissions.py`, and `test_navbar_docs.py`; keep tests beside the behavior they verify.

**Functions:**
- snake_case. Private helpers have a leading underscore and are imported across modules when needed (for example `_walk_ancestors`, `_check_nested_alias` in `src/crud_views/checks.py`, `src/crud_views/lib/views/delete.py`).
- Workflow transition methods use the `wf_` prefix.

**Variables / class attributes:**
- Every `CrudView` class attribute uses the `cv_` prefix: `cv_key`, `cv_path`, `cv_success_key`, `cv_context_actions`, `cv_header_template`, `cv_icon_action`, `cv_modal_supported`.
- Module-level constants are UPPER_SNAKE (`TAG`, `_REGISTRY`, `_REGISTRY_LOCK`, `GOLDEN_DIR`). Sentinels are `_NAME_UNSET = object()`.
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

## Documentation Test Conventions

- When docs publish copyable recipes, extract the exact fenced block and execute it against project objects/views. Follow `tests/test1/test_navbar_docs.py`, `test_object_detail_value_docs.py`, `test_cancel_docs.py`, and `test_theme_adoption_docs.py`; avoid maintaining a retyped example that can drift.
- For rendering recipes, use Django `Template`, real request/context/response fixtures, and parsed DOM assertions. Verify public semantics and documented inventories/cross-links alongside recipe behavior.

## Project Rules

- Decision rule (`CLAUDE.md`): prefer the simplest bounded solution the maintainer can explain; keep new features opt-in and self-contained; avoid hidden state and extra queries on existing paths.
- Until 1.0.0, a `### Breaking` entry in `CHANGELOG.md` also requires an update to `docs/migrating-1.0.md`.
- Version bumps go through bump-my-version (`task bump-patch`); never edit version strings by hand.

---

*Convention analysis: 2026-11-19*
