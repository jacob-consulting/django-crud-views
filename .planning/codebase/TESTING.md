---
last_mapped_commit: 38f49b77fdd3ac823a2d31a907b58a433212b423
last_mapped_at: 2026-11-02
---
# Testing Patterns

**Analysis Date:** 2026-11-02

## Test Framework

**Runner:**
- Python: pytest with pytest-django, pytest-cov, pytest-xdist, pytest-random-order, pytest-mock (`pyproject.toml`). Django setup and fixtures are in `tests/test1/conftest.py`.
- JavaScript: Vitest 5 with jsdom; Node 20+ (`package.json`, `vitest.config.js`).
- Browser: Node's built-in test runner and Playwright-driven scenarios are used under `tests/browser/`; Python host scripts configure disposable Django test servers.

**Assertion Library:**
- Python uses plain `assert` and pytest features (`pytest.mark.parametrize`, fixtures, `pytest.raises`). HTML inspection uses lxml/cssselect (`tests/test1/od/test_layout_a11y.py`).
- JavaScript unit tests use Vitest `expect` matchers; integration harnesses also use Node `assert/strict` (`tests/browser/presentation-config.test.cjs`).
- Browser scenarios use Playwright locators plus Node assertions/check helpers (`tests/browser/conditional-formsets.cjs`).

**Run Commands:**

```bash
pytest tests -n auto                  # Full Python suite, multicore
pytest tests/test1/test_crud.py      # One Python test module
pytest tests/test1/test_crud.py::test_create_author -v
task test                            # nox Python/Django version matrix
npm test                             # Vitest unit suite
npm run test:integration             # Vitest/jsdom integration suite
npm run test:watch                   # Vitest watch mode
task test-js                         # Vitest unit suite via task
```

Broad pytest runs should use `-n auto` or a bounded `-n N` when resources are shared. Nox sessions also run pytest with `-n auto`; reserve serial execution for a small selection or a concrete isolation/debugging need. Browser scenarios have dedicated Node/Python harnesses in `tests/browser/` and may require locally available Playwright/Chromium; inspect each script's preflight requirements before invoking it.

## Test File Organization

**Location:**
- Django package and behavior tests: `tests/test1/`, with object-detail coverage under `tests/test1/od/`.
- JavaScript unit tests: `tests/js/`; server-backed JavaScript tests: `tests/js-integration/`.
- Browser acceptance and presentation tests: `tests/browser/`; reusable HTML and presentation variants live under `tests/browser/templates/`.
- Shared Python fixtures and helpers: `tests/test1/conftest.py`, `tests/lib/helper/`.

**Naming:** Python uses `test_*.py` and `test_*` functions. Vitest uses `*.test.js`. Browser Node test files use `.test.cjs`, while standalone browser scenarios use descriptive `.cjs` names.

**Structure:**

```
tests/
├── test1/                 # Django behavior tests, app, and golden HTML
│   ├── app/               # test models, ViewSets, URLs, templates
│   └── od/                # object-detail tests and templates
├── js/                    # Vitest/jsdom unit tests and helpers
├── js-integration/        # Vitest tests coupled to real server-rendered fragments
├── browser/               # Node/Playwright scenarios and Python disposable hosts
└── lib/helper/            # shared test utilities
```

## Test Structure

**Suite Organization:**

```python
@pytest.mark.django_db
def test_create_author(client_user_author_add: Client, cv_author):
    response = client_user_author_add.get("/author/create/")
    assert response.status_code == 200

    response = client_user_author_add.post("/author/create/", {
        "first_name": "Isaac", "last_name": "Asimov", "pseudonym": "",
    })
    assert response.status_code == 302
    assert Author.objects.filter(first_name="Isaac", last_name="Asimov").exists()
```

This reflects `tests/test1/test_crud.py`: exercise the public HTTP path and verify persisted state.

**Patterns:**
- Mark database tests with `@pytest.mark.django_db`; fixtures create users/models and logged-in Django clients (`tests/test1/conftest.py`).
- Use parametrization for a shared behavioral contract across settings/layouts/input cases (`tests/test1/od/test_layout_a11y.py`).
- Assert rendered semantics, authorization, status/redirect, and state changes. For templates, parse HTML with lxml where structural assertions are clearer than string matching.
- Golden rendered output lives in `tests/test1/golden/` and common comparisons are supported by `tests/lib/helper/golden.py`.

## Mocking

**Framework:** pytest `monkeypatch`, pytest-mock, and Vitest `vi`.

**Patterns:**

```javascript
vi.stubGlobal("$", $);
vi.spyOn(console, "log").mockImplementation(() => {});
```

Global browser setup is centralized in `tests/js/helpers/setup.js`. `tests/js/helpers/load.js` evaluates the actual package static scripts in a jsdom-compatible window and stubs navigation.

**What to Mock:** External side effects such as network AJAX, browser navigation, and console chatter when they are not under test. Tests can inject AJAX callbacks and assert requested data as in `tests/js-integration/formset.test.js`.

**What NOT to Mock:** Core application behavior, Django URL/view rendering, or the shipped JS under test. Integration tests intentionally pass real Django-generated fragments to the actual static scripts.

## Fixtures and Factories

**Test Data:**

```python
@pytest.fixture
def author_douglas_adams():
    from tests.test1.app.models import Author
    return Author.objects.create(first_name="Douglas", last_name="Adams")
```

Follow the `cv_<model>`, `user_<model>_<permission>`, and `client_user_<model>_<permission>` naming patterns in `tests/test1/conftest.py`.

**Location:** Django project-wide model/client fixtures: `tests/test1/conftest.py`; shared utilities: `tests/lib/helper/`; JS DOM and script helpers: `tests/js/helpers/`. `tests/test1/app/models.py` defines test-domain models.

## Coverage

**Requirements:** Coverage is enforced at 88% via `[tool.coverage.report].fail_under` in `pyproject.toml`. Nox writes a separate XML report for each Python/Django combination to avoid collisions (`noxfile.py`).

**View Coverage:**

```bash
pytest tests -n auto --cov --cov-report=term-missing
```

## Test Types

**Unit Tests:** Python module and view tests cover CRUD, permissions, validation, settings/system checks, and template output in `tests/test1/`. JavaScript unit tests isolate behavior in jsdom under `tests/js/`.

**Integration Tests:** `tests/js-integration/` combines real server-rendered Django fragments with shipped JavaScript. Python view tests also exercise full request/response paths against the configured in-memory database.

**E2E Tests:** Playwright browser scenarios under `tests/browser/` cover presentation and interactive formsets across rendered pages and themes. Python host scripts such as `tests/browser/conditional_formsets_server.py` create disposable SQLite/media state. Browser setup is environment-dependent and separate from the default Vitest commands.

## Common Patterns

**Async Testing:**

```javascript
beforeAll(async () => {
    await loadScript("formset");
});
```

Await setup and async browser actions; Vitest suite setup is in `tests/js/helpers/setup.js` and scripts are loaded through `tests/js/helpers/load.js`.

**Error Testing:**

```python
with pytest.raises(ValueError):
    operation()
```

For browser event listeners, collect `window` error events with `listenerErrors` (`tests/js/helpers/errors.js`) because listener exceptions do not propagate from dispatch. For views, assert status codes, redirect targets, and permission outcomes (`tests/test1/test_crud.py`).

---

*Testing analysis: 2026-11-02*
