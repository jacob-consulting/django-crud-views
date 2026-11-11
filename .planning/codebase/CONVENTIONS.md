---
last_mapped_commit: 6c09417f8f15a93e0e39d8340ec05dba331e82fb
last_mapped_at: 2026-11-11
---
# Coding Conventions

**Analysis Date:** 2026-11-11

## Naming Patterns

**Files:**
- Python modules use lowercase snake_case (`src/crud_views/lib/viewset.py`); tests use `test_<behavior>.py` under `tests/test1/`, `tests/browser/`, or `tests/js/`.
- Bootstrap demo apps commonly collect Django `TestCase` classes in `tests.py` (`examples/bootstrap5/formsets/tests.py`).
- JavaScript unit tests use `*.test.js` (`tests/js/toggle.test.js`); Node browser-harness tests use `*.test.cjs` (`tests/browser/presentation-cleanup.test.cjs`).

**Functions:**
- Python functions and pytest fixtures use snake_case; test methods/functions begin `test_` (`tests/test1/test_form_enctype.py`).
- JavaScript functions and variables use camelCase; Vitest test descriptions use readable behavior statements (`tests/js/toggle.test.js`).

**Variables:**
- Python locals use snake_case; Django fixture names encode the entity/action, e.g. `cv_<model>` and `client_user_<model>_<permission>` (`tests/test1/conftest.py`).
- JavaScript locals use camelCase (`tests/js/toggle.test.js`).

**Types:**
- Python classes use CapWords (`CrudView`, `FormsetsTestCase`); Django model/Form/View classes follow domain names (`examples/bootstrap5/formsets/tests.py`).
- JavaScript constructors/classes use PascalCase where needed; ordinary helpers remain camelCase.

## Code Style

**Formatting:**
- Ruff formats Python with 120-character lines, spaces, and double quotes (`pyproject.toml`).
- Ruff is configured to lint `E`, `F`, `I`, `UP`, `B`, `C4`, `SIM`, and `RUF`; it allows the breadcrumb confusable `›` (`pyproject.toml`).
- `ruff format` runs on Markdown Python fences as well as Python files in CI (`.github/workflows/lint.yml`).
- Run `task format` to format and `task check` for Ruff fixes; pre-commit runs `ruff-check` and `ruff-format` (`taskfile.yaml`, `.pre-commit-config.yaml`).
- JavaScript uses four-space indentation, double quotes, and semicolons in the current Vitest suites (`tests/js/toggle.test.js`, `vitest.config.js`).

**Linting:**
- Ruff is the Python linter/formatter; there is no separate configured JS lint command (`pyproject.toml`, `package.json`).
- Ruff per-file ignores permit `RUF012` in tests, examples, and migrations (`pyproject.toml`).

## Import Organization

**Order:**
1. Standard library imports.
2. Third-party packages such as Django, pytest, and lxml.
3. Project and test utility imports.

Ruff's `I` rule enforces import sorting. Follow the grouping visible in `tests/test1/test_form_enctype.py` and `examples/bootstrap5/formsets/tests.py`.

**Path Aliases:**
- No Python package alias is configured. Sources live under `src/`; project commands and explicit cross-runtime commands add `src` to `PYTHONPATH` (`docs/reference/javascript.md`, `noxfile.py`).
- JS tests import helpers via relative paths (`tests/js/toggle.test.js`).

## Error Handling

**Patterns:**
- Tests assert explicit response codes, persisted state, errors, and no-mutation conditions rather than treating any response as success (`examples/bootstrap5/formsets/tests.py`).
- Use `try/finally` for global-state and browser/process cleanup; fixture teardown restores monkeypatched state (`tests/conftest.py`, `tests/browser/presentation-cleanup.test.cjs`).
- Parameterized edge cases use `subTest`, pytest parametrization, or Vitest `it.each` (`examples/bootstrap5/library/tests.py`, `tests/test1/test_form_enctype.py`, `tests/js/toggle.test.js`).

## Logging

**Framework:** Django/Python logging and console APIs; no project-wide logging wrapper was detected.

**Patterns:**
- Tests silence expected JS console chatter in shared setup and spy on warnings/errors when their behavior is under test (`tests/js/helpers/setup.js`, `tests/js/toggle.test.js`).
- Browser harnesses print a concise report location and preserve error details in JSON (`tests/browser/presentation.cjs`).

## Comments

**When to Comment:**
- Explain non-obvious framework/browser behavior and why a regression assertion is necessary, not routine test steps (`tests/test1/test_form_enctype.py`, `tests/browser/presentation-cleanup.test.cjs`).
- Keep scope/contract comments near specialized coverage, as in the formsets example tests (`examples/bootstrap5/formsets/tests.py`).

**JSDoc/TSDoc:**
- No broad JSDoc/TSDoc convention detected. JavaScript test helper intent is documented with short comments where useful (`tests/js/helpers/setup.js`).

## Function Design

**Size:** Keep helpers focused on a reusable fixture or assertion; use local helpers such as `form_payload`, `field_key`, and `fragment_params` to keep formset cases readable (`examples/bootstrap5/project/testing.py`, `examples/bootstrap5/formsets/tests.py`).

**Parameters:** Use pytest fixtures for shared test dependencies and explicit parameters for meaningful case variation (`tests/test1/conftest.py`, `tests/test1/test_form_enctype.py`).

**Return Values:** Return concrete values from parsing/setup helpers; test assertions should state the expected response or state change directly (`examples/bootstrap5/project/testing.py`, `examples/bootstrap5/formsets/tests.py`).

## Module Design

**Exports:** Prefer explicit imports from the module under test; import local helpers where the behavior is shared (`tests/test1/test_form_enctype.py`).

**Barrel Files:** No general JS barrel pattern detected. `tests/js/helpers/load.js` is a test harness that loads shipped static assets, not an application export barrel.

---

*Convention analysis: 2026-11-11*
