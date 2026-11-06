---
last_mapped_commit: 3aad91002c8d176fc6308cafa84dabc42da59031
last_mapped_at: 2026-11-06
---
# Coding Conventions

**Analysis Date:** 2026-11-06

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
- Browser event listener errors are collected from `window` error events through `tests/js/helpers/errors.js`; DOM dispatch does not reliably rethrow them synchronously.

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

## Module Design

**Exports:** Keep Python imports explicit. JavaScript test helpers use named exports.

**Barrel Files:** No general barrel-file pattern detected; import from the owning module.

---

*Convention analysis: 2026-11-06*
