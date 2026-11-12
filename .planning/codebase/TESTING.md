---
last_mapped_commit: 6c09417f8f15a93e0e39d8340ec05dba331e82fb
last_mapped_at: 2026-11-11
---
# Testing Patterns

**Analysis Date:** 2026-11-11

## Test Framework

**Runner:**
- Python: pytest with pytest-django, pytest-xdist, pytest-cov, pytest-mock, and pytest-random-order (`pyproject.toml`). Django compatibility runs are orchestrated by Nox (`noxfile.py`).
- JavaScript: Vitest with jsdom for unit tests; Node's built-in `node:test` for browser harness tests (`package.json`, `vitest.config.js`, `tests/browser/presentation-cleanup.test.cjs`).
- Browser interaction: Playwright scripts and dedicated Python fixture servers under `tests/browser/`; these are separate from the ordinary Vitest command (`tests/browser/`).
- Config: pytest settings are in `pyproject.toml`, with Django settings configured in `tests/conftest.py`. The demo project has `examples/bootstrap5/pytest.ini`.

**Assertion Library:**
- Python uses pytest assertions and Django `TestCase` assertions; structural HTML checks use lxml/cssselect (`examples/bootstrap5/formsets/tests.py`).
- JavaScript uses Vitest `expect`/`vi` and Node `assert/strict` (`tests/js/toggle.test.js`, `tests/browser/presentation-cleanup.test.cjs`).

**Run Commands:**
```bash
pytest tests -n auto                              # All Python core tests, multicore
nox -p                                            # Supported Python/Django Nox matrix (task test wraps this)
pytest tests/test1/test_crud.py -n auto           # Focused Python module
task test-js                                      # Vitest jsdom unit suite
npm test                                          # Equivalent ordinary Vitest suite
npm run test:integration                          # Django-rendered fragment/FormData/POST JS bridge
```

Use multiple workers for broad pytest runs (`-n auto`, or bounded `-n N` when resources are shared). Nox pytest sessions also use `-n auto`. Sequential Django-version sessions are compatible with multicore workers within each session. Choose serial pytest only for a concrete isolation/order/debugging constraint or a very small selection where worker startup dominates.

The Python suite imports the src-layout package. Use the repository's environment or set `PYTHONPATH="$PWD/src:$PWD"` for commands that cross into Django from Node; the integration command requires an explicit prepared interpreter such as `CV_FRAGMENT_PYTHON="$PWD/.nox/crispy_floor-3-12-django-6-0/bin/python"` (`docs/reference/javascript.md`).

## Test File Organization

**Location:**
- Core Python tests are in `tests/test1/`, shared fixtures/helpers in `tests/conftest.py` and `tests/lib/helper/`.
- Django demo tests live beside each app as `tests.py`; `examples/bootstrap5/pytest.ini` enables discovery of `test_*.py`, `*_test.py`, and `tests.py`.
- JS unit tests: `tests/js/**/*.test.js`; browser and harness tests: `tests/browser/*.test.cjs` plus paired `.cjs` runners and Python server fixtures.

**Naming:** Python pytest modules/functions use `test_` names; Django app tests commonly use `<app>/tests.py` with `TestCase` classes. JS uses `*.test.js` and `*.test.cjs`.

**Structure:**
```text
tests/
├── conftest.py              # Django/pytest setup and shared fixtures
├── test1/                   # Core Django behavior tests
├── lib/helper/              # Shared test utilities
├── js/                      # Vitest + jsdom tests of shipped assets
└── browser/                 # Node harness, Playwright runners, Python fixture servers
examples/bootstrap5/
├── pytest.ini               # Demo suite discovery and Django settings
└── <app>/tests.py           # Django TestCase tests for demo behavior
```

## Test Structure

**Suite Organization:**
```python
def test_form_content_template_posts_multipart(template):
    request = RequestFactory().get("/")
    html = render_to_string(template, {"form": UploadForm(), "request": request, "view": None}, request=request)
    outer_form_tag = re.search(r"<form\b[^>]*>", html).group(0)
    assert 'enctype="multipart/form-data"' in outer_form_tag
```
This focused render assertion from `tests/test1/test_form_enctype.py` checks the outer form contract because nested crispy markup is ignored by browsers.

**Patterns:**
- Core `tests/test1/` uses pytest functions/fixtures and `@pytest.mark.django_db`; Django's in-memory test configuration is set up once in `tests/conftest.py`.
- Demo tests use `django.test.TestCase`, class-level `setUpTestData`, login setup, and Django client requests (`examples/bootstrap5/library/tests.py`).
- Assert actual submitted form semantics. The shared `form_payload()` helpers omit unchecked checkboxes as browsers do (`tests/lib/helper/forms.py`, `examples/bootstrap5/project/testing.py`).
- For newly added Django demo modules, put cases in `examples/bootstrap5/<app>/tests.py`; the demo's pytest discovery explicitly includes these unlabelled `tests.py` modules (`examples/bootstrap5/pytest.ini`).
- Assert both rendered structure and persistence for checkbox/formset behavior: `examples/bootstrap5/formsets/tests.py` checks checked `done` submission, omitted unchecked values, labels/IDs in returned fragments, and that omitted checkboxes save as `False`.
- Pair runtime and docs/catalog contracts where user-facing examples are involved. `examples/bootstrap5/project/tests.py` verifies Checklist feature-catalog copy, code snippets, and active navigation; `examples/bootstrap5/formsets/tests.py` verifies Checklist registration and CRUD.
- Use exact golden files only for stable, intentional rendered contracts (`tests/test1/golden/`, `tests/lib/helper/golden.py`).

## Mocking

**Framework:** pytest `monkeypatch`/pytest-mock; Vitest `vi`; Node harness tests use `child_process`, temp directories, and controlled fixture processes.

**Patterns:**
```javascript
beforeAll(async () => { await loadScript("toggle"); });

it("reacts to checkbox change in both directions", () => {
    const { checkbox } = fixture({ checked: true });
    checkbox.click();
    expect(checkbox.form.checkValidity()).toBe(true);
});
```
See `tests/js/toggle.test.js`; shared globals and `beforeEach` navigation reset are in `tests/js/helpers/setup.js`.

**What to Mock:** External effects such as navigation, network requests, selected permission rechecks, and failure paths (`tests/js/helpers/load.js`, `tests/test1/test_workflow_permissions.py`).

**What NOT to Mock:** Django rendering/URL dispatch or shipped JS when testing integration behavior. The Node/Django bridge intentionally exercises real rendered fragments and FormData (`docs/reference/javascript.md`).

## Fixtures and Factories

**Test Data:**
```python
@classmethod
def setUpTestData(cls):
    cls.admin = get_user_model().objects.create_superuser(username="test-admin", password="pw")
    cls.author = Author.objects.create(first_name="Ursula", last_name="Le Guin")
```
Demo `TestCase` fixture setup uses this pattern (`examples/bootstrap5/library/tests.py`). Core fixtures follow `cv_<model>`, `user_<model>_<permission>`, and `client_user_<model>_<permission>` names (`tests/test1/conftest.py`).

**Location:** pytest/Django fixtures in `tests/conftest.py` and `tests/test1/conftest.py`; reusable helpers in `tests/lib/helper/`; example request-payload parsing in `examples/bootstrap5/project/testing.py`.

## Coverage

**Requirements:** `pytest-cov` is configured with `fail_under = 88` and `show_missing = true` (`pyproject.toml`). Nox writes one XML report per Python/Django session to avoid overwrites (`noxfile.py`).

**View Coverage:**
```bash
pytest tests -n auto --cov --cov-report=term-missing
```

## Test Types

**Unit Tests:** Python configuration, rendering, permissions, and model behavior in `tests/test1/`; JS DOM behavior in jsdom under `tests/js/`.

**Integration Tests:** Django client request/database tests in `tests/test1/` and `examples/bootstrap5/`; explicit cross-runtime fragment/FormData/POST checks through `npm run test:integration` (`docs/reference/javascript.md`).

**E2E Tests:** Playwright scripts in `tests/browser/` exercise real browser interactions against dedicated Django fixture servers. The runners select explicit runtimes and ports, write JSON reports to a configurable output path, and record cleanup outcomes (`tests/browser/presentation.cjs`, `tests/browser/presentation-config.test.cjs`). Keep report paths isolated between concurrent runs; the default presentation report points into a phase artifact directory and can otherwise overwrite a prior run. Fixture servers are disposable: runners terminate and reap their owned process, release ports, and preserve cleanup failures in reports (`tests/browser/presentation.cjs`, `tests/browser/presentation-cleanup.test.cjs`).

## Common Patterns

**Async Testing:**
```javascript
beforeAll(async () => { await loadScript("toggle"); });
```
Vitest loads the real asset into jsdom before cases (`tests/js/toggle.test.js`, `tests/js/helpers/load.js`).

**Error Testing:**
- Python tests assert invalid forms retain submitted values and produce no partial writes (`examples/bootstrap5/formsets/tests.py`).
- Multipart encoding has a focused render regression test covering create, update, and custom-form templates (`tests/test1/test_form_enctype.py`).
- Native checkbox tests must model browser submission: checked controls submit their value; unchecked controls are omitted. Verify both the rendered native checkbox and omitted-value persistence (`examples/bootstrap5/formsets/tests.py`, `tests/lib/helper/forms.py`).
- Browser-runner failure tests should verify a failed report, nonzero exit, original error retention, and fixture process reaping even when browser close or server shutdown fails (`tests/browser/presentation-cleanup.test.cjs`).

---

*Testing analysis: 2026-11-11*
