---
last_mapped_commit: a78b63db1f637b6b8b4cf6b4aaa24885a061ae26
last_mapped_at: 2026-11-16
---
# Testing Patterns

**Analysis Date:** 2026-11-16

## Test Framework

**Runner:**
- pytest with pytest-django, configured in `pyproject.toml` (`--strict-markers`).
- The primary test project configures Django in `tests/test1/conftest.py`; the root `tests/conftest.py` supplies cross-project access-recording isolation.

**Assertion Library:**
- Plain pytest `assert` statements, with Django test client and response/context assertions.

**Run Commands:**
```bash
pytest tests -n auto                         # Full suite, parallel workers
pytest tests/test1/test_crud.py              # One test module
pytest tests/test1/test_crud.py::test_create_author -v  # One test
task test                                    # nox Python/Django matrix
```

## Test File Organization

**Location:**
- Primary package tests live in `tests/test1/`; helper factories and utilities live in `tests/lib/helper/`.
- Browser-oriented tests are under `tests/browser/`. Demo project tests live beside their example app under `examples/bootstrap5/`.

**Naming:**
- Files follow `test_<topic>.py`; functions follow `test_<behavior>`.

**Structure:**
```text
tests/
├── conftest.py                 # Cross-test access recording fixture
├── lib/helper/                 # Shared user, form, icon, guardian and golden helpers
├── test1/
│   ├── conftest.py             # In-memory Django settings and fixtures
│   ├── app/                    # Test models and configured views
│   └── test_*.py               # Feature-focused tests
└── browser/                    # Browser-level checks
```

## Test Structure

**Suite Organization:**
```python
@pytest.mark.django_db
def test_create_author(client_user_author_add: Client, cv_author):
    response = client_user_author_add.post("/author/create/", {"first_name": "Isaac", "last_name": "Asimov"})
    assert response.status_code == 302
    assert Author.objects.filter(first_name="Isaac", last_name="Asimov").exists()
```

**Patterns:**
- Group tests by user-visible feature or invariant; use descriptive comments to divide operation/scenario groups (`tests/test1/test_form_validation.py`).
- Mark ORM-using tests with `@pytest.mark.django_db`; plain unit tests avoid database setup (`tests/test1/test_guardian_composition.py`).
- Share auth/viewset/client fixtures from `tests/test1/conftest.py`; fixture names encode the model and permission, such as `client_user_author_add`.
- Parametrize combinations where one invariant spans variants, with `ids` when they improve failure readability (`tests/test1/test_ancestor_resources.py`).

## Mocking

**Framework:** pytest `monkeypatch`; `pytest-mock` is a declared test extra, but the prevalent pattern uses monkeypatch.

**Patterns:**
```python
monkeypatch.setattr(view_class, "cv_viewset", child_viewset)
with pytest.raises(ImproperlyConfigured, match=r"Guardian.*Mixin"):
    view_class().has_permission()
```

**What to Mock:**
- Patch a narrow dependency or class attribute to create an invalid composition, force a branch, or spy on calls; pytest restores patches after the test (`tests/test1/test_guardian_composition.py`, `tests/test1/test_ancestor_resources.py`).
- For module-global registries, snapshot/restore them in fixtures or patch them with `monkeypatch`; examples include `asset_registry` and warning state isolation in `tests/test1/conftest.py`.

**What NOT to Mock:**
- For CRUD, forms, permission, and routing behavior, exercise the real Django client/request path and assert both response and database effects (`tests/test1/test_crud.py`).
- Avoid mocking Django internals when an in-memory database or `RequestFactory` can test the contract directly.

## Fixtures and Factories

**Test Data:**
```python
@pytest.fixture
def user_author_view(cv_author):
    user = User.objects.create_user(username="user_author_view", password="password")
    user_viewset_permission(user, cv_author, "view")
    return user
```

**Location:**
- Core Django settings, clients, users, and model factories are in `tests/test1/conftest.py`.
- Reusable helpers are in `tests/lib/helper/` (`user.py`, `forms.py`, `guardian.py`, `golden.py`).
- Fixtures should leave process-global state as they found it; `asset_registry` explicitly snapshots and restores the registry in `tests/test1/conftest.py`.

## Coverage

**Requirements:** `pyproject.toml` sets `fail_under = 88`, reports missing lines, and measures all five source packages.

**View Coverage:**
```bash
pytest tests -n auto --cov --cov-report=term-missing
task test  # nox sessions generate per Python/Django coverage XML
```

## Test Types

**Unit Tests:**
- Use direct class/helper calls, `RequestFactory`, `SimpleNamespace`, and monkeypatch for focused configuration, composition, and permission invariants (`tests/test1/test_guardian_composition.py`).

**Integration Tests:**
- The bulk of `tests/test1/` integrates configured Django views, middleware, templates, auth, and SQLite in-memory databases. Assert HTTP responses, rendered content/context, database state, and permission outcomes.
- `noxfile.py` runs installed-distribution tests across Python 3.12–3.15 and Django 4.2/5.2/6.0 (Django 4.2 skips Python 3.14+), with parallel pytest workers.

**E2E Tests:**
- Browser checks exist in `tests/browser/`; full browser tooling details are not configured in pytest's base configuration.

## Common Patterns

**Async Testing:**
```python
# No async pytest pattern detected; use synchronous Django client tests for current view APIs.
```

**Error Testing:**
```python
with pytest.raises(ImproperlyConfigured, match=r"Guardian.*Mixin"):
    view_class().has_permission()
```
- Assert exception type and a stable message fragment for invalid configuration; assert form error fields and unchanged persisted data for invalid submissions (`tests/test1/test_form_validation.py`).

**Markup Regression Tests:**
- `tests/lib/helper/golden.py` normalizes whitespace and compares generated markup to checked-in golden files; updating snapshots requires the explicit `CV_UPDATE_GOLDEN` environment variable.

---

*Testing analysis: 2026-11-16*
