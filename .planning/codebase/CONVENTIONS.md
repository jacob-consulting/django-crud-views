---
last_mapped_commit: 910d8bb98ea06a21ff838dacd56704c0ce31e4de
last_mapped_at: 2026-11-09
---
# Coding Conventions

**Analysis Date:** 2026-11-09

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

## Module Design

**Exports:** Keep Python imports explicit. JavaScript test helpers use named exports.

**Barrel Files:** No general barrel-file pattern detected; import from the owning module.

---

*Convention analysis: 2026-11-09*
