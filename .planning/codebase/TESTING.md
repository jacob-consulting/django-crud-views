---
last_mapped_commit: 38b0100683fa71412b8bc00dd0eeb7f985efb459
last_mapped_at: 2026-10-25
---
# Testing Patterns

**Analysis Date:** 2026-10-25

## Test Framework

**Runner (Python):**

- pytest + pytest-django (installed via the `test` extra in `pyproject.toml`; no version pins)
- Plugins: `pytest-cov`, `pytest-xdist` (`-n auto` in nox), `pytest-mock` (installed, but `monkeypatch` is the house style), `pytest-random-order` (installed, not enabled by default)
- HTML parsing for assertions: `lxml`, `cssselect`
- Config: `[tool.pytest.ini_options] addopts = "--strict-markers"` in `pyproject.toml`. Django is configured programmatically in `pytest_configure()` in `tests/test1/conftest.py` — there is no `DJANGO_SETTINGS_MODULE` for the package tests.
- Examples project has its own config: `examples/bootstrap5/pytest.ini` (`DJANGO_SETTINGS_MODULE = project.settings`, `python_files = test_*.py *_test.py tests.py`).

**Runner (JS):**

- Vitest `^5.0.3` with `jsdom` environment, jQuery `~3.7.1` as dev dependency only (`package.json`)
- Config: `vitest.config.js` (`include: ["tests/js/**/*.test.js"]`, `setupFiles: ["tests/js/helpers/setup.js"]`)

**Matrix:**

- `noxfile.py`: session `tests` × Python 3.12/3.13/3.14/3.15 × Django 4.2/5.2/6.0 (Django 4.2 skipped on 3.14+); session `examples` runs `pytest` in `examples/bootstrap5`.
- CI: `.github/workflows/tests.yml` (nox per Python row, Codecov upload), `.github/workflows/js.yml` (`npm test` on Node 22), `.github/workflows/lint.yml`.

**Assertion Library:**

- Plain `assert` (pytest rewriting); Vitest `expect`.

**Run Commands:**

```bash
pytest tests                                   # Run all package tests (quick, current env)
pytest tests/test1/test_crud.py::test_create_author -v   # Single test
pytest tests -n auto --cov --cov-report=term-missing     # Parallel + coverage (as nox does)
task test                                      # Full nox matrix (uv run nox -p)
task test-js                                   # JS unit tests (npx vitest run)
task test-js-watch                             # JS watch mode
CV_UPDATE_GOLDEN=1 pytest tests/test1/test_action_menus_golden.py   # Regenerate golden HTML
```

## Test File Organization

**Location:**

- Separate tree, not co-located: `tests/test1/` for Python, `tests/js/` for JS.
- `tests/test1/od/` holds `crud_views_object_detail` tests with its own `conftest.py`.
- `examples/bootstrap5/<app>/tests.py` plus `examples/bootstrap5/test_docs_sync.py`, `test_doc_links.py`, `test_i18n.py` test the demo project and docs.

**Naming:**

- `test_<feature>.py`, split by aspect when a feature grows: `test_action_menus_card.py`, `test_action_menus_config.py`, `test_action_menus_context.py`, `test_action_menus_golden.py`.
- Test functions: `test_<subject>_<expected_behaviour>` (`test_create_hook_exception_rolls_back_save`, `test_missing_extends_names_the_setting`, `test_check_template_missing_emits_error`).
- Regression tests for a check id embed it: `test_e211_invalid_view_value`.

**Structure:**

```
tests/
├── conftest.py                 # root (shared)
├── lib/helper/                 # reusable test helpers
│   ├── boostrap5.py            # Table/Row/Column/Action HTML parsers (lxml)
│   ├── forms.py                # form_payload(), field_key(s)()
│   ├── user.py                 # user_viewset_permission()
│   ├── guardian.py             # user_guardian_object_perm()
│   └── icons.py                # icon library fixtures
├── js/
│   ├── helpers/{setup,load,dom,errors}.js
│   └── <script>.test.js
└── test1/
    ├── conftest.py             # pytest_configure() settings + all model/user/client fixtures
    ├── project/urls.py         # ROOT_URLCONF
    ├── app/                    # test Django app: models.py, views.py, views_formset.py, resources.py, templates/
    ├── od_app/, od/            # object-detail app + its tests
    ├── golden/<suite>/*.html   # golden HTML snapshots
    └── test_*.py               # ~1675 test functions total
```

## Test Structure

**Suite Organization:** Module-level functions are the default; group related tests in a `class Test...` only when they share helper methods (12 classes, e.g. in `tests/test1/test_breadcrumb.py`).

Typical HTTP-level CRUD test (`tests/test1/test_crud.py`):

```python
import pytest
from django.test.client import Client

from tests.test1.app.models import Author

@pytest.mark.django_db
def test_create_author(client_user_author_add: Client, cv_author):
    # GET create form
    response = client_user_author_add.get("/author/create/")
    assert response.status_code == 200

    # POST valid data
    response = client_user_author_add.post(
        "/author/create/",
        {"first_name": "Isaac", "last_name": "Asimov", "pseudonym": ""},
    )
    assert response.status_code == 302
    assert response.url == "/author/"

    # Verify author created in DB
    assert Author.objects.filter(first_name="Isaac", last_name="Asimov").exists()
```

Unit test of a check without a database (`tests/test1/test_check_messages.py`):

```python
class BothSet:
    attr_a = "x"
    attr_b = "y"

def test_check_either_attribute_both_set_emits_both_message():
    check = CheckEitherAttribute(context=BothSet, id="E999", attribute1="attr_a", attribute2="attr_b")
    messages = list(check.messages())
    assert len(messages) == 1
    assert "Both attributes" in messages[0].msg
```

**Patterns:**

- Mark every DB-touching test with `@pytest.mark.django_db`, or request the `db` fixture inside a fixture (`def objects(db): ...`).
- Request the `cv_<model>` fixture even when unused so the ViewSet module is imported and URLs are registered.
- Module docstrings state the issue and contract under test: `"""#174: with every inline value None, the action containers render exactly the pre-#174 HTML."""` / `"""Audit task 2.4 (M9): ..."""`.
- Use inline `# GET ...` / `# POST ...` / `# Verify ...` comments to separate phases.
- `--strict-markers` is on: only use registered markers (`django_db`, `parametrize`, `urls`, `skipif`, `usefixtures`).
- Use `@pytest.mark.urls("tests.test1.test_readme_snippet")` when a test module defines its own `urlpatterns`.
- Teardown is fixture-based (`yield` then restore); no `setUp`/`tearDown` methods.

## Mocking

**Framework:** pytest `monkeypatch` (dominant); `settings` fixture from pytest-django; `override_settings` from `django.test`. `unittest.mock`/`mocker` are rarely used.

**Patterns:**

```python

# Patch a view class attribute for one test — monkeypatch restores it (tests/test1/test_transactions.py)

@pytest.mark.django_db
def test_create_hook_exception_rolls_back_save(client_user_publisher_add, monkeypatch):
    from tests.test1.app.views import PublisherCreateView

    monkeypatch.setattr(PublisherCreateView, "cv_form_valid_hook", _boom)
    with pytest.raises(Boom):
        client_user_publisher_add.post("/publisher/create/", {"name": "Rolled Back"})
    assert not Publisher.objects.filter(name="Rolled Back").exists()

# Patch the settings singleton or a ViewSet field (tests/test1/test_action_label_mode_config.py)

def test_viewset_beats_setting(monkeypatch):
    monkeypatch.setattr(crud_views_settings, "context_actions_label_mode", {"create": "both"})
    monkeypatch.setattr(cv_author, "context_actions_label_mode", {"home": "label"})

# Wrap a classmethod to record calls (tests/test1/test_action_enabled.py)

monkeypatch.setattr(GuardianBookDeleteView, "cv_action_enabled", classmethod(_record))

# Remove a registered view temporarily (tests/test1/test_breadcrumb.py)

monkeypatch.delitem(cv_publisher_bc._views, "detail")
```

Module-global registries are snapshotted and restored by fixtures (`tests/test1/conftest.py`):

```python
@pytest.fixture
def asset_registry():
    """Snapshot/restore the module-global asset registry around each test."""
    from crud_views.lib import assets

    snapshot = dict(assets._REGISTRY)
    assets._REGISTRY.clear()
    yield assets
    assets._REGISTRY.clear()
    assets._REGISTRY.update(snapshot)
```

Cached settings singletons are reset with an autouse fixture (`tests/test1/od/conftest.py`): `monkeypatch.setattr(conf, "crud_views_object_detail_settings", CrudViewsObjectDetailSettings())` — do the same when a test relies on `override_settings` reaching a `cached_property`.

**JS mocking (`tests/js/`):**

```javascript
// tests/js/modal.test.js
function stubFetch(responseOrError) {
    const fetchMock = vi.fn(() => Promise.resolve(responseOrError));
    vi.stubGlobal("fetch", fetchMock);
    return fetchMock;
}
window.cv = { ...window.cv, adapters: { modal: { show, hide, setSize } } };
expect(nav.assign).toHaveBeenCalledWith("/books/create/");
```

- `tests/js/helpers/setup.js` stubs `$`/`jQuery` globals and silences `console.log`/`console.assert`.
- `tests/js/helpers/load.js` `loadScript(name)` evaluates the shipped file from `src/crud_views/static/crud_views/js/` inside a Proxy window whose `location` is the `nav` stub (`nav.assign`, `nav.href`), reset before each test.
- `tests/js/helpers/dom.js` builds DOM skeletons (`modalSkeleton()`).

**What to Mock:**

- View/ViewSet class attributes and hooks (`cv_*`), `crud_views_settings` fields, Django `settings` (via the `settings` fixture), module-level registries, `fetch` and navigation in JS.

**What NOT to Mock:**

- The database, URL routing, templates, permissions, or the Django test `Client` — tests run real requests against the in-memory SQLite DB and parse the rendered HTML.
- Do not mutate `tests/test1/app/views.py` classes without `monkeypatch`; they are shared by every test.

## Fixtures and Factories

**Test Data:** No factory library. Named fixtures in `tests/test1/conftest.py` create concrete objects with ORM calls; lazy imports inside fixtures keep model imports after `django.setup()`.

```python
@pytest.fixture
def cv_author():
    from tests.test1.app.views import cv_author as ret

    return ret

@pytest.fixture
def user_author_view(cv_author):
    from django.contrib.auth.models import User

    user = User.objects.create_user(username="user_author_view", password="password")
    user_viewset_permission(user, cv_author, "view")
    return user

@pytest.fixture
def client_user_author_view(client, user_author_view) -> Client:
    client.force_login(user_author_view)
    return client

@pytest.fixture
def author_douglas_adams():
    from tests.test1.app.models import Author

    return Author.objects.create(first_name="Douglas", last_name="Adams")
```

**Fixture naming convention (follow exactly):**

- `cv_<model>` — the ViewSet (`cv_author`, `cv_publisher`, `cv_book`, `cv_vehicle`, `cv_guardian_author`)
- `user_<model>_<perm>` — user with one viewset permission (`user_book_change`); combined perms join names (`user_publisher_view_delete`)
- `client_user_<model>_<perm>` — logged-in `Client`
- `<model>_<name>` — data objects (`author_douglas_adams`, `publisher_penguin`, `book_hitchhiker`, `car_sedan`)
- Guardian: `client_guardian`, `user_guardian`, `user_guardian_object_perm(user, viewset, perm, obj)` helper
- Settings toggles: `bundled`, `pipeline_setting` (bottom of `tests/test1/conftest.py`)

**Test models** (`tests/test1/app/models.py`): `Author` (UUID PK, `OrderedModel`), `Publisher` (int PK), `Book` (child of Publisher), `Genre` (M2M child), `Vehicle`/`Car`/`Truck` (polymorphic), `Campaign` (workflow, `FSMField`). Add new test models here and register views in `tests/test1/app/views.py` (or `views_formset.py`), URLs in `tests/test1/project/urls.py`.

**HTML helpers:**

- `tests/lib/helper/boostrap5.py`: `Table(response)` → `.rows`, `.headers`, `.context_actions`, `row.columns[i].text`, `row.get_action("update").href`, `action.is_disabled`, `action.key` (reads `cv-key`).
- `tests/lib/helper/forms.py`: `form_payload(response)` turns a rendered form into a browser-like POST dict; `field_key(payload, "-title")` finds formset field names.

**Golden files:**

- Location: `tests/test1/golden/<suite>/<case>.html` (`action_menus`, `card_pagination`, `form_frame`, `heading_level`).
- Pattern (`tests/test1/test_action_menus_golden.py`): render, select fragments by XPath, canonicalize (sort attributes and class tokens, normalize whitespace, replace CSRF token), compare against file. Regenerate only when a markup change is intended, with `CV_UPDATE_GOLDEN=1`. Use fixed PKs (`uuid.UUID("00000000-0000-4000-8000-000000000174")`) so output is stable.

## Coverage

**Requirements:** `fail_under = 88` (`[tool.coverage.report]` in `pyproject.toml`), `show_missing`, `skip_empty`. Sources: all five `src/` packages; `tests/test1/test_coverage_config.py` asserts the source list matches `src/` packages and that relative paths are emitted. Codecov (`codecov.yml`) is advisory: waits for 4 uploads, ignores `src/**/migrations/**`.

**View Coverage:**

```bash
pytest tests --cov --cov-report=term-missing
pytest tests --cov --cov-report=html     # htmlcov/
```

## Test Types

**Unit Tests:**

- Checks, settings, registries, resolvers, icon/label-mode logic tested by instantiating objects directly (`CrudViewsSettings(extends=None).check_messages`, `CheckTemplate(...).messages()`), often without `django_db`.
- View methods tested via `RequestFactory` + manual view instantiation (`make_view(...)` in `tests/test1/test_breadcrumb.py`).

**Integration Tests:**

- The majority: full request/response through `Client` against the test project, asserting status codes, redirects (`response.url`), DB state, and parsed HTML.
- Query-count guards: `django_assert_num_queries` (`test_breadcrumb.py::test_ancestor_query_count`).
- Transactions: `django_capture_on_commit_callbacks(execute=True)` (`tests/test1/test_transactions.py`).
- Management commands: `call_command("cv_assets", ..., stdout=out)` (`tests/test1/test_cv_assets_command.py`), migrations check (`test_migrations.py`).
- Import safety in a clean interpreter: `subprocess.run([sys.executable, "-c", code])` (`tests/test1/test_import_safety.py`).
- Guard tests over source/templates: `test_js_no_jquery_guard.py`, `test_templates_no_crispy_pack_guard.py`, `test_no_django_bootstrap5.py`, `test_public_api_surface.py`, `test_template_a11y.py`, `test_readme_snippet.py`.

**JS Unit Tests:**

- `tests/js/*.test.js`: `describe`/`it`/`beforeAll(loadScript)`/`beforeEach(skeleton)`; async flows awaited with `await vi.waitFor(() => expect(...))`.

**E2E Tests:**

- Not used (no Playwright/Selenium suite; `.playwright-mcp/` is tooling state only).

## Common Patterns

**Parametrized check tests:**

```python

# tests/test1/test_action_label_mode_config.py — tuple names, stacked parametrize for a cross product

def _ids(view_cls) -> list[str]:
    return [m.id for c in view_cls.checks() for m in c.messages()]

@pytest.mark.parametrize(
    ("view_cls", "attr"),
    [(AuthorListView, "cv_list_actions_label_mode"), (AuthorDetailView, "cv_context_actions_label_mode")],
)
@pytest.mark.parametrize("value", ["both", ["create"], {"create": "text"}, {"create": None}])
def test_e211_invalid_view_value(monkeypatch, view_cls, attr, value):
    monkeypatch.setattr(view_cls, attr, value)
    ...
```

**Settings override:**

```python

# tests/test1/test_strict_mode.py — pytest-django `settings` fixture + override_settings

def test_strict_defaults_to_debug_on(settings):
    # pytest-django forces DEBUG=False during tests, so set it explicitly
    del settings.CRUD_VIEWS_STRICT
    with override_settings(DEBUG=True), pytest.raises(KeyError):
        _boom()
```

**Log assertions:**

```python
def test_empty_label_and_icon_stays_icon_and_logs(caplog):
    ...
    assert "'detail'" in caplog.text
```

**Error Testing:**

```python
with pytest.raises(ValueError, match="'js' or 'css'"):
    ...
with pytest.raises(Http404):
    view.cv_breadcrumb()
```

- Strict mode is on in tests (`CRUD_VIEWS_STRICT=True` in `pytest_configure`), so `@ignore_exception` paths raise — test the swallow branch explicitly with `override_settings(CRUD_VIEWS_STRICT=False)` or `del settings.CRUD_VIEWS_STRICT` + `DEBUG=False` (`tests/test1/test_strict_mode.py`).

**Async Testing (JS):**

```javascript
it("GETs the url with the X-CV-Modal header", async () => {
    const fetchMock = stubFetch(textResponse("<p>hi</p>"));
    window.cv.cvModalOpen("/books/create/", "");
    await vi.waitFor(() => expect(show).toHaveBeenCalled());
    expect(fetchMock).toHaveBeenCalledWith("/books/create/", { headers: { "X-CV-Modal": "true" } });
});
```

**Adding a test for a new feature:**

1. Write the failing test first in `tests/test1/test_<feature>.py`, with a module docstring citing the issue.
2. Reuse `cv_*` / `client_user_*` fixtures; add new ones to `tests/test1/conftest.py` following the naming scheme.
3. Add test views to `tests/test1/app/views.py` only when existing ones cannot be monkeypatched.
4. Assert on parsed HTML (`Table`, `lxml`) rather than raw substrings where structure matters.
5. Run `pytest tests -n auto` before the full `task test` matrix.

---

*Testing analysis: 2026-10-25*
