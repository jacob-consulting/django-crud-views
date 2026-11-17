---
last_mapped_commit: 54c18a1b65f038e5fcdb5dc0038782133f93ffb8
last_mapped_at: 2026-11-17
---
# Testing Patterns

**Analysis Date:** 2026-11-17

## Test Framework

**Runner:**
- pytest with pytest-django, pytest-xdist, pytest-cov, pytest-mock, pytest-random-order (`pyproject.toml` `test` extra); `addopts = "--strict-markers"`.
- Config: `pyproject.toml` `[tool.pytest.ini_options]`; Django is configured in code by `pytest_configure()` in `tests/test1/conftest.py` (in-memory sqlite `default` and `shard` DBs, `CRUD_VIEWS_STRICT=True`).

**Assertion Library:**
- Plain `assert`, `pytest.raises(..., match=...)`, `caplog`; HTML parsed with `lxml` / `cssselect`.

**Run Commands:**
```bash
pytest tests -n auto                       # full suite, multicore (preferred)
pytest tests/test1/test_basic.py -v        # single file
pytest tests/test1/test_x.py::test_name    # single test
task test                                  # nox matrix: py3.12-3.15 x Django 4.2/5.2/6.0
pytest tests -n auto --cov                 # coverage (fail_under = 88)
CV_UPDATE_GOLDEN=1 pytest tests/test1/test_action_menus_golden.py   # regenerate goldens
npm test                                   # vitest JS unit tests (tests/js)
npm run test:integration                   # vitest integration (tests/js-integration)
```
Use `-n auto` (or bounded `-n N`) for broad runs; serial only with a concrete isolation reason.

## Test File Organization

**Location:** Separate from source, under `tests/`:
- `tests/test1/` - Python tests (about 270 files, flat) plus test apps `tests/test1/app/` (models Author UUID, Publisher int, Book child, Vehicle polymorphic, Campaign workflow), `tests/test1/od_app/`, `tests/test1/project/` (urls), `tests/test1/golden/` (stored markup).
- `tests/lib/helper/` - shared helpers: `user.py` (`user_viewset_permission`), `boostrap5.py` (`Table` HTML parser), `golden.py` (`check_golden`), `guardian.py`, `forms.py`, `icons.py`.
- `tests/browser/` - `*.cjs` scripts, `*.test.cjs` and Python servers for browser tests; `tests/js/`, `tests/js-integration/` - vitest.
- `tests/check_manage_schema.py` - schema check script.

**Naming:** `test_<topic>.py`, functions `test_<behavior>`; topic families share a prefix.

## Test Structure

**Suite Organization:** Module-level functions, no test classes. Typical view test:
```python
@pytest.mark.django_db
def test_debug_view(user_author_view: User, cv_author, author_douglas_adams, author_terry_pratchett):
    client = Client()
    client.force_login(user_author_view)
    response = client.get("/author/")
    assert response.status_code == 200
    lst = Table(response)
```

**Patterns:**
- `@pytest.mark.django_db` on DB tests (heavily used); `@pytest.mark.parametrize` extensively.
- Fixtures naming: `cv_<model>` for ViewSets, `user_<model>_<permission>` for users, `client_user_<model>_<permission>` for logged-in clients, plus data fixtures like `author_douglas_adams`.
- Permissions granted with `user_viewset_permission(user, viewset, "view")`.
- Parse rendered HTML with helpers (`Table(response)`) rather than substring matching.

## Mocking

**Framework:** pytest `monkeypatch` (primary), `override_settings`, pytest-mock available.

**Patterns:**
```python
monkeypatch.setattr(cv_book, "verbose_name", "volume")
monkeypatch.setattr(PublisherDetailView, "cv_context_actions", ["books"])
```
- Autouse fixtures in `tests/test1/conftest.py` isolate global state per test: `isolate_theme_label_modes`, `isolate_label_mode_warnings`; opt-in `asset_registry` snapshots/restores `assets._REGISTRY`; `database_routes` swaps DB routers.
- Mutate class attributes through `monkeypatch.setattr` so they revert; never leave module/class state changed.

**What to Mock:** class attributes/settings and module-global registries.
**What NOT to Mock:** the Django test client, ORM, and template rendering; exercise real views against in-memory sqlite.

## Fixtures and Factories

- Fixtures live in `tests/test1/conftest.py` (grouped by model with `# --- Publisher fixtures ---` comments); no factory library, objects are created through the ORM inside fixtures.
- Goldens: normalised markup files under `tests/test1/golden/<area>/`, compared through `tests/lib/helper/golden.py::check_golden`; set `CV_UPDATE_GOLDEN=1` to rewrite.

## Coverage

**Requirements:** `fail_under = 88` (`pyproject.toml` `[tool.coverage.report]`); sources are the five packages; `relative_files` and path mapping for nox installs. XML per session (`coverage-py<py>-dj<dj>.xml`), uploaded to Codecov (`codecov.yml`).

```bash
pytest tests -n auto --cov --cov-report=term-missing
```

## Test Types

**Unit Tests:** helpers, settings validation, checks (`tests/test1/test_ancestor_*.py`).
**Integration Tests:** Django test-client requests across ViewSets, permissions, nested resources, Guardian, workflow, polymorphic.
**Docs Tests:** tests such as `test_access_trace_docs.py` and `test_badge_docs.py` verify documentation against the code.
**E2E / JS:** vitest (`vitest.config.js`, `vitest.integration.config.js`) and browser scripts in `tests/browser/`; CI in `.github/workflows/js.yml`, `tests.yml`.
**nox:** `noxfile.py` installs the built distribution (asserts `crud_views` is not imported from `src/`), runs the suite with coverage, then reruns the full suite with `--no-cov` and `CV_ACCESS_RECORD_REQUESTS=1` to observe every existing request with the same assertions (first run uses `CV_ACCESS_RECORD_REQUESTS=0`).

## Common Patterns

**Error Testing:**
```python
with pytest.raises(ImproperlyConfigured, match=r"form_tag=False|form_action"):
    ...
```
**Warnings:** use `caplog` to assert logged warnings when `CRUD_VIEWS_STRICT` is off.
**Async:** Not used.

---

*Testing analysis: 2026-11-17*
