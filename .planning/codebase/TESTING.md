---
last_mapped_commit: 9afb8b2f0d9597f2044089d44840fe38d055b72b
last_mapped_at: 2026-11-10
---
# Testing Patterns

**Analysis Date:** 2026-11-10

## Test Framework

**Runner:**
- Python: pytest (`--strict-markers`) with pytest-django, pytest-cov, pytest-xdist, pytest-random-order, and pytest-mock (`pyproject.toml`). Nox runs a Python 3.12–3.15 and Django 4.2/5.2/6.0 matrix, skipping Django 4.2 on Python 3.14+ (`noxfile.py`).
- JavaScript: Vitest with jsdom; Node-based browser scenarios live under `tests/browser/` (`package.json`, `vitest.config.js`).
- Django test setup and shared fixtures live in `tests/test1/conftest.py`; root `tests/conftest.py` supplies broader test support.

**Assertion Library:**
- Python uses plain `assert`, pytest parametrization/fixtures/`pytest.raises`; HTML checks use lxml and cssselect.
- Vitest unit tests use `expect`; browser Node tests use `node:assert/strict` and Playwright assertions/locators.

**Run Commands:**

```bash
pytest tests -n auto                      # Broad suite, multicore
pytest tests -n 4                         # Bound workers when sharing resources
pytest tests/test1/test_crud.py           # One module
pytest tests/test1/test_crud.py::test_create_author -v
task test                                 # Nox Python/Django matrix
npm test                                  # JavaScript unit suite
npm run test:integration                  # Server-rendered JS integration suite
task test-js                              # Vitest unit suite via Task
```

Prefer `-n auto` or bounded `-n N` for broad pytest runs; the nox sessions also use `-n auto`. Use serial execution for a small selection where worker startup dominates, or a concrete isolation, ordering, or debugging constraint. Browser scenarios use dedicated harnesses in `tests/browser/` and may require Playwright/Chromium; inspect their preflight requirements.

## Test File Organization

**Location:**
- Django behavior tests: `tests/test1/`; object-detail tests: `tests/test1/od/`.
- JavaScript unit tests: `tests/js/`; server-backed JS integration tests: `tests/js-integration/`.
- Browser acceptance tests and disposable host scripts: `tests/browser/`.
- Shared Python fixtures/helpers: `tests/test1/conftest.py`, `tests/lib/helper/`.

**Naming:** Python modules and functions use `test_*.py` and `test_*`; Vitest files use `*.test.js`; Node browser tests use `*.test.cjs`.

**Structure:**

```text
tests/
├── test1/                 # Django behavior tests, app, and golden HTML
│   ├── app/               # Test models, ViewSets, URLs, templates
│   ├── golden/            # Rendered output snapshots
│   └── od/                # Object-detail tests and templates
├── js/                    # Vitest/jsdom tests and helpers
├── js-integration/        # Tests using real server-rendered fragments
├── browser/               # Node/Playwright scenarios and Python hosts
└── lib/helper/            # Shared Python test utilities
```

## Test Structure

**Suite Organization:**

```python
@pytest.mark.django_db
def test_create_author(client_user_author_add, cv_author):
    response = client_user_author_add.get("/author/create/")
    assert response.status_code == 200

    response = client_user_author_add.post("/author/create/", {
        "first_name": "Isaac", "last_name": "Asimov", "pseudonym": "",
    })
    assert response.status_code == 302
    assert Author.objects.filter(first_name="Isaac", last_name="Asimov").exists()
```

This request-level pattern is represented in `tests/test1/test_crud.py`: exercise the public URL and verify both response and persisted state.

**Patterns:**
- Mark database tests with `@pytest.mark.django_db`; fixtures create users, models, ViewSets, and authenticated Django clients in `tests/test1/conftest.py`.
- Parametrize shared behavior across permissions, settings, layouts, and input cases (`tests/test1/test_permissions_full.py`, `tests/test1/od/test_layout_a11y.py`).
- Assert HTTP status, redirect destination, authorization, form errors, rendered semantics, and state changes. Parse HTML with lxml when structural assertions are clearer than strings.
- Store stable rendered output under `tests/test1/golden/`; compare via helpers in `tests/lib/helper/golden.py`.
- `tests/test1/test_workflow_permissions.py` covers workflow permissions through real GET/POST requests. It verifies available transition choices, denied transitions, and that forbidden requests leave the object and history unchanged. Successful POST assertions cover redirect, resulting state, and persisted audit history fields (transition, old/new state, actor, and object identity). Use `_persisted_snapshot()` when proving rejection causes no mutation; test execution-time permission rechecks by submitting a form validated before permission denial.

## Object-Detail Acceptance Coverage

- `tests/test1/od/test_choice_display.py` covers scalar/related choices, unknown/missing labels, lazy translation, escaping, raw custom ownership, badge precedence, and query baselines. `test_help_text_policy.py` covers all 48 property/project/view combinations plus interleaving and stable resolved results.
- Query-count assertions distinguish loaded FK/O2O (zero), uncached scalar relations (one), and prefetched collections (zero); they do not promise application display overrides are query-free.
- `tests/test1/test_object_detail_value_docs.py` extracts unique marked fences from current Markdown and executes real core/Guardian/polymorphic composition and migration recipes. This suite passed 38 cases during shipping, using four pytest workers on Python 3.12 / Django 5.2.
- Phase 06.16 retained final-source evidence records 10,837 passed/one existing skip on the full Django 5.2 suite and 665 focused cases each on Django 4.2/5.2/6.0. These are historical phase results, not a new full matrix run (`.planning/phases/06.16-object-detail-choice-labels-help-text-policy-empty-values-an/06.16-VERIFICATION.md`).
- CI lint formats Markdown Python fences too. Run `ruff format --check .` and `ruff check .` before shipping documentation changes (`.github/workflows/lint.yml`).

## Ancestor Authorization Coverage (Phase 06.18)

- 19 modules `tests/test1/test_ancestor_*.py` (resolution, authorization, policy, boundaries, operations, ordering, redirect, manage, resources, Guardian, actors, costs, helpers, structure, databases, auth_databases, migration, docs) cover nested-ViewSet authorization through real URLs with database-backed model grants.
- Isolation pattern: build fresh, uniquely named ViewSets inside `isolated_routes(build)` (`tests/test1/test_ancestor_authorization.py`). It installs a temporary `ROOT_URLCONF` module, then restores `_REGISTRY`, `check_module._VOCAB_CACHE`, URL caches and the ContentType cache in `finally`. Other ancestor modules import `_client`, `_url`, `_user`, `isolated_routes` from it.
- Ordered-event spy: the `events` fixture monkeypatches `ViewSet.get_queryset` and `PermissionsMixin.has_perm` to record call order; assert authorization decisions happen before child queryset calls.
- Query cost: `CaptureQueriesContext(connection)` pins query counts for cold/warm permission vocabulary. Set `CV_ANCESTOR_OBSERVATIONS_DIR` to write JSON observations; unset, the test only asserts normal responses.
- Multi-database cases use the `shard` alias and routers (`tests/test1/test_ancestor_databases.py`, `tests/test1/test_ancestor_auth_databases.py`).
- `tests/test1/test_ancestor_docs.py` executes documentation recipes; `tests/test1/test_ancestor_migration.py` covers migration/opt-out behavior.
- Module docstrings state phase/plan scope and the contract proved; keep that header on new modules. Use `from __future__ import annotations`.
- Test ViewSet families are composed with `type("List", (GuardianListViewPermissionRequired,), {...})` (`tests/test1/test_ancestor_helpers.py`).

## Table Meta Coverage (Phase 06.19)

- `tests/test1/test_table_meta.py` builds `Table` subclasses over plain dict rows with a dummy `view=object()` (no DB, no request) and asserts column order via `[c.name for c in table.columns]`.
- Covers: default `actions` last, `Meta.sequence` used as written, `sequence` kwarg precedence over `Meta.sequence`, `Meta.exclude = ("actions",)` removing the column.

## Mocking

**Framework:** pytest `monkeypatch`/pytest-mock for Python; Vitest `vi` for JavaScript.

**Patterns:**

```python
def test_execution_recheck(client, workflowrequest_new, user_workflowrequest_step, monkeypatch):
    monkeypatch.setattr(WorkflowRequest, "workflow_has_transition", deny_transition)
    response = client.post(url, payload)
    assert response.status_code == 400
```

For JavaScript, use `vi.stubGlobal` and `vi.spyOn`; shared browser setup is in `tests/js/helpers/setup.js`, and `tests/js/helpers/load.js` loads actual package scripts in a jsdom window.

**What to Mock:** External side effects such as network AJAX, browser navigation, and behavior that must change during a specific recheck test.

**What NOT to Mock:** Core application behavior, Django URL/view rendering, or the shipped JavaScript under test. Integration tests pass real Django-generated fragments to actual scripts.

## Fixtures and Factories

**Test Data:**

```python
@pytest.fixture
def author_douglas_adams():
    from tests.test1.app.models import Author
    return Author.objects.create(first_name="Douglas", last_name="Adams")
```

Follow `cv_<model>`, `user_<model>_<permission>`, and `client_user_<model>_<permission>` fixture names (`tests/test1/conftest.py`). Workflow permission tests define scenario-specific user fixtures and a workflow object fixture in `tests/test1/test_workflow_permissions.py`.

**Location:** Django fixtures in `tests/test1/conftest.py`; shared Python utilities in `tests/lib/helper/`; JavaScript helpers in `tests/js/helpers/`; domain models in `tests/test1/app/models.py`.

## Coverage

**Requirements:** Coverage must reach 88%; `[tool.coverage.report].fail_under` enforces this in `pyproject.toml`. Nox emits a separate XML report per Python/Django session (`noxfile.py`).

**View Coverage:**

```bash
pytest tests -n auto --cov --cov-report=term-missing
```

## Test Types

**Unit Tests:** Python model/view/configuration tests in `tests/test1/`; JavaScript behavior tests in jsdom under `tests/js/`.

**Integration Tests:** `tests/js-integration/` combines actual rendered fragments and shipped JS. Django tests exercise HTTP request/response paths against the configured test database.

**E2E Tests:** Playwright scenarios under `tests/browser/` exercise rendered presentation and interaction. They use Python disposable servers/fixtures and are separate from default Vitest commands.

## Common Patterns

**Async Testing:**

```javascript
beforeAll(async () => {
    await loadScript("formset");
});
```

Await asynchronous setup and browser actions. Vitest setup is centralized in `tests/js/helpers/setup.js`.

**Error Testing:**

```python
with pytest.raises(ValueError):
    operation()
```

For view failures, assert response status, form errors, redirect, and unchanged state as appropriate (`tests/test1/test_workflow_permissions.py`). Capture browser listener errors through `tests/js/helpers/errors.js` because event dispatch does not synchronously propagate listener exceptions.

**Workflow execution/database routing:** `tests/test1/test_workflow_execution.py` exercises the public helper and request path, atomic and non-atomic view settings, transaction rollback, `on_commit` timing, selected database aliases, and rejection of unsaved or cross-database actors/objects. Database-router tests use the `shard` alias and verify history writes/reads remain aligned. Extend these cases when changing `src/crud_views_workflow/lib/execution.py` or `src/crud_views_workflow/lib/views.py`.

## ViewSet Label Coverage (Phase 06.20)

- `tests/test1/test_viewset_verbose_name.py`: 13 cases for model/Resource defaults, independent overrides, active-language translation, lazy/padded preservation, blank validation, Guardian inheritance and nested list rendering.
- `tests/test1/test_viewset_verbose_name_render.py`: eight cases for headings/paragraphs, explicit precedence, breadcrumb GET HTML, child-column text/title, full/short button labels, and POST/message/alert delivery. Book message production remains separately asserted; delivery uses the existing message-enabled Publisher view.
- Tests reuse registered fixtures with monkeypatch; constructor probes clean up under the registry lock. Exact DOM/message assertions exercise real requests.
- Fresh shipping selection (these modules plus `test_breadcrumb.py` and `test_messages.py`): 96 passed with four workers. Ruff lint/format over `src`/`tests` and strict MkDocs passed on 2026-11-10.
- Historical evidence: 12,066 full-suite passes before the final test-only addition; final request coverage has focused follow-up evidence. Do not describe the historical run as a full-suite run of the final tree (`.planning/phases/06.20-viewset-verbose-name-override-for-every-default-label/06.20-VERIFICATION.md`).

---

*Testing analysis: 2026-11-10*
