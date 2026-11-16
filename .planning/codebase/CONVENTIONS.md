---
last_mapped_commit: a78b63db1f637b6b8b4cf6b4aaa24885a061ae26
last_mapped_at: 2026-11-16
---
# Coding Conventions

**Analysis Date:** 2026-11-16

## Naming Patterns

**Files:**
- Python modules and tests use lowercase `snake_case`; tests use `test_<behavior>.py` (for example `tests/test1/test_form_validation.py`).
- Production view modules correspond to their operation under `src/crud_views/lib/views/` (`create.py`, `detail.py`, `update.py`).

**Functions:**
- Functions and methods use `snake_case`; Django extension hooks retain the package's `cv_` prefix (for example `cv_form_valid` in `src/crud_views/lib/views/create.py`).
- Test functions use `test_<behavior>` and state the behavior/outcome in the name (see `tests/test1/test_guardian_composition.py`).

**Variables:**
- Use `snake_case`; Django extension attributes and hooks use `cv_` (configured through view classes and ViewSets).
- Workflow transition methods use `wf_` as documented in `CLAUDE.md`.

**Types:**
- Classes use `PascalCase`; type aliases and enums follow normal Python naming conventions.
- Add type annotations to public or non-obvious interfaces and fixtures; the project uses built-in generic forms such as `dict[str, ...]` and nullable unions (`str | None`).

## Code Style

**Formatting:**
- Use Ruff formatting, 120-character lines, four-space indentation, and double quotes as configured in `pyproject.toml`.
- Run `task format` to format. Ruff excludes `.planning/**` and `superpowers/**` from source linting.

**Linting:**
- Ruff selects `E`, `F`, `I`, `UP`, `B`, `C4`, `SIM`, and `RUF` rules in `pyproject.toml`.
- Keep imports sorted through Ruff's `I` rules. Test/example/migration modules ignore `RUF012` because Django model attributes and teaching examples need not add `ClassVar` annotations.

## Import Organization

**Order:**
1. Standard library imports.
2. Third-party packages (including Django and pytest).
3. Project/package imports.

Separate groups with blank lines; Ruff/isort ordering is authoritative. For local optional packages, follow the relevant extension package's existing imports.

**Path Aliases:**
- No Python import alias convention beyond normal module aliases was detected. Tests import reusable fixtures/helpers from `tests.lib.helper` and models from `tests.test1.app`.

## Error Handling

**Patterns:**
- Raise Django's domain exceptions (`ImproperlyConfigured`, `Http404`) or standard exceptions (`TypeError`, `ValueError`) for invalid configuration or unsupported input; see `src/crud_views/lib/views/create.py` and `tests/test1/test_resource.py`.
- Preserve Django's normal form validation cycle: invalid POSTs re-render with form errors, while successful submissions redirect (`tests/test1/test_form_validation.py`).
- Catch only expected lookup/routing exceptions at user-facing boundaries; for example, `CreateView` converts missing related parent routes into an unavailable action instead of hiding arbitrary exceptions (`src/crud_views/lib/views/create.py`).
- Validate configuration early and test actionable exception messages with `pytest.raises(..., match=...)` (`tests/test1/test_guardian_composition.py`).

## Logging

**Framework:** Python logging through module loggers where needed; no mandatory logging wrapper was detected.

**Patterns:**
- Avoid logging ordinary control flow. Tests that exercise warning behavior should isolate warning-dedup state and assert the relevant behavior rather than depend on global process state (`tests/test1/conftest.py`).

## Comments

**When to Comment:**
- Explain non-obvious compatibility constraints, ordering, or security boundaries; comments in `src/crud_views/lib/views/create.py` explain parent routing semantics.
- Prefer tests with a short behavior-focused docstring when the scenario is not obvious (`tests/test1/test_form_validation.py`).

**JSDoc/TSDoc:**
- Not applicable (Python project). Use concise Python docstrings for public APIs and non-obvious hooks.

## Function Design

**Size:** Keep view hooks focused on one operation; extract helpers when route, permission, or data-flow logic has a clear boundary. Existing extension hooks are intentionally explicit (`cv_form_valid` in `src/crud_views/lib/views/create.py`).

**Parameters:** Prefer named, typed parameters for stable hooks. Django overrides retain Django's expected signatures. Test fixture parameters are injected by pytest and may be typed when useful.

**Return Values:** Preserve Django response/form/queryset contracts. Annotate helper return values where they clarify public or shared behavior; use explicit `None`/false results for unavailable optional actions as the surrounding API expects.

## Module Design

**Exports:** Keep implementation in package submodules and expose intended public APIs via package `__init__.py` modules.

**Barrel Files:** Python package `__init__.py` files serve as curated re-export points; follow neighboring exports rather than importing internal modules from unrelated packages.

---

*Convention analysis: 2026-11-16*
