---
last_mapped_commit: dced8509ce37fd54351952d2e1302784d0278d0b
last_mapped_at: 2026-11-05
---
# Coding Conventions

**Analysis Date:** 2026-11-05

## Naming Patterns

**Files:**
- Python modules use lowercase snake_case, including Django views and test modules (for example `src/crud_views/lib/view/base.py`, `tests/test1/test_crud.py`).
- Browser unit test files use descriptive kebab/dotted names ending in `.test.js`, under `tests/js/` or `tests/js-integration/`.
- Django test files use `test_*.py`; nested object-detail tests live in `tests/test1/od/`.

**Functions:**
- Python functions and fixtures use snake_case. Test functions begin `test_` and state a behavior or outcome.
- JavaScript functions and variables use camelCase; DOM attributes and CSS classes use the package's `cv-` / `cv_` prefixes where applicable.
- Workflow transitions use `wf_` prefix as established in `tests/test1/app/models.py` and package conventions.

**Variables:**
- Use descriptive snake_case in Python and camelCase in JavaScript. Fixtures identify model and permission, e.g. `client_user_author_add` in `tests/test1/conftest.py`.

**Types:**
- Python classes use CapWords (`ViewSet`, `CrudView`, `ResolvedProperty`). Add type annotations to public APIs and fixtures where useful; runtime Python support starts at 3.12 (`pyproject.toml`).
- JavaScript uses named exports for test helpers such as `loadScript` (`tests/js/helpers/load.js`).

## Code Style

**Formatting:**
- Use Ruff formatting with 120-character lines, spaces, and double quotes (`pyproject.toml`).
- Preserve existing formatting for templates and HTML fixtures; golden tests can compare output byte-for-byte.

**Linting:**
- Ruff lint selects `E`, `F`, `I`, `UP`, `B`, `C4`, `SIM`, and `RUF`; import sorting is included (`pyproject.toml`).
- Test/example class attributes and migration files ignore `RUF012` (`pyproject.toml`).
- Pre-commit runs `ruff-check` and `ruff-format` (`.pre-commit-config.yaml`).

## Import Organization

**Order:**
1. Python standard library.
2. Third-party packages, including Django and pytest.
3. Project imports (`crud_views...`) and test support (`tests...`).

Ruff's `I` rules enforce import sorting. JavaScript tests place Vitest and Node imports before project-local helpers (see `tests/js/formset.test.js`).

**Path Aliases:**
- No Python import alias configuration is defined; use package imports (`crud_views...`) and test imports (`tests...`).
- Vitest resolves shipped JavaScript source paths through the explicit `JS_DIRS` map in `tests/js/helpers/load.js`.

## Error Handling

**Patterns:**
- Raise Django exceptions such as `Http404` or validation errors at request/model boundaries; tests assert behavior and status codes rather than implementation internals (see `tests/test1/test_resource.py`, `tests/test1/test_crud.py`).
- Browser listener exceptions are captured through `window` error events using `listenerErrors` in `tests/js/helpers/errors.js`; don't rely on a DOM dispatch call throwing synchronously.

## Logging

**Framework:** Python uses standard logging where needed; no project-wide logging wrapper is configured. Browser scripts use console APIs; `tests/js/helpers/setup.js` silences expected `console.log` and `console.assert` chatter.

**Patterns:**
- Avoid noisy logs in normal operation. Tests should capture expected browser listener errors explicitly and assert none occurred.

## Comments

**When to Comment:**
- Explain non-obvious compatibility constraints, fixture synchronization requirements, and test harness workarounds. Examples include the fixture/server markup synchronization note in `tests/js/helpers/dom.js` and jsdom navigation details in `tests/js/helpers/load.js`.

**Docstrings:**
- Use concise docstrings for fixtures/helpers when setup behavior is not self-evident; test names should carry the ordinary behavioral description.

## Function Design

**Size:** Keep methods and helpers focused on one behavior. Split complex test setup into fixtures or local helpers.

**Parameters:** Prefer explicit fixture dependencies in pytest and small options objects for reusable JavaScript DOM fixtures (`tests/js/helpers/dom.js`).

**Return Values:** Return Django responses or concrete data from helpers; assert observable results (response, database state, rendered markup, DOM state).

## Module Design

**Exports:** Keep Python imports explicit. JavaScript test helpers use named exports.

**Barrel Files:** No general barrel-file pattern detected; import from the owning module.

---

*Convention analysis: 2026-11-05*

## Phase 06.12 incremental refresh — 2026-11-05

Scope: workflow presentation, class registry, associated tests/docs and companion integration. Other sections retain the preceding full-map findings.

### Optional-app presentation conventions

Keep workflow defaults on its AppConfig rather than adding optional keys to the core default mapping. `src/crud_views/lib/button_classes.py` validates declarations and active workflow colour keys. Core remains at 88 defaults; installing workflow adds ten.

Treat registry values as complete class replacements. Preserve explicit empty/None values; fallback is for absent keys only. Keep Django autoescaping active for badge labels/classes even though the rendered fragment is returned as safe HTML by the model helper.

Use the shared `crud_views/snippets/form_frame.html` contract for decoration. The action leaf owns its single form; history has a separate table-only wrapper. Preserve the existing generic modal response path and HTTP status/redirect semantics.
