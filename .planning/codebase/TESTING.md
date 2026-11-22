---
last_mapped_commit: af5d74efd12e965b432fe30c6044f139b406eafc
last_mapped_at: 2026-11-21
---
# Testing Patterns

**Analysis Date:** 2026-11-21

## Test Framework

**Runner:**
- pytest with pytest-django, pytest-xdist, pytest-cov, pytest-mock, pytest-random-order (`pyproject.toml` `test` extra); `addopts = "--strict-markers"`.
- Config: `pyproject.toml` `[tool.pytest.ini_options]`; Django is configured in code by `pytest_configure()` in `tests/test1/conftest.py` (in-memory sqlite `default` and `shard` DBs, `CRUD_VIEWS_STRICT=True`).

**Assertion Library:**
- Plain `assert`, `pytest.raises(..., match=...)`, `caplog`; HTML parsed with `lxml` / `cssselect`.

**Run Commands:**
```bash
pytest tests -n auto                       # full suite, multicore (preferred)
pytest tests -n 4                          # broad local run on a shared/resource-bounded machine
pytest tests/test1/test_crud.py -v         # representative single file
pytest tests/test1/test_crud.py::test_name # single test
task test                                  # nox matrix: py3.12-3.15 x Django 4.2/5.2/6.0
pytest tests -n auto --cov                 # coverage (fail_under = 88)
CV_UPDATE_GOLDEN=1 pytest tests/test1/test_action_menus_golden.py   # regenerate goldens
npm test                                   # Node/jsdom unit + runtime-boundary checks (tests/js)
npm run test:integration                   # requires CV_FRAGMENT_PYTHON + PYTHONPATH (see below)
task test-js                              # task wrapper; runs npm test
```
Use four pytest-xdist workers for broad local runs when resources are shared; use `-n auto` on a dedicated machine. CI/Nox uses `-n auto`. Run serially only for a concrete isolation/order/debugging constraint or when worker startup costs more than a tiny selection.

## Test File Organization

**Location:** Separate from source, under `tests/`:
- `tests/test1/` - Python tests (topic-focused `test_*.py` files, mostly flat) plus test apps `tests/test1/app/` (models Author UUID, Publisher int, Book child, Vehicle polymorphic, Campaign workflow), `tests/test1/od_app/`, `tests/test1/project/` (urls), `tests/test1/golden/` (stored markup).
- `tests/lib/helper/` - shared helpers: `user.py` (`user_viewset_permission`), `boostrap5.py` (`Table` HTML parser), `golden.py` (`check_golden`), `guardian.py`, `forms.py`, `icons.py`.
- `tests/browser/` - `*.cjs` scripts, `*.test.cjs` and Python servers for browser tests; `tests/js/`, `tests/js-integration/` - vitest.
- `tests/check_manage_schema.py` - schema check script.

**Naming:** `test_<topic>.py`, functions `test_<behavior>`; topic families share a prefix.

## Test Structure

**Suite Organization:** Module-level functions are common; topic-based test classes also group related contracts (for example `TestBreadcrumbItem` and `TestBreadcrumbTopLevel` in `tests/test1/test_breadcrumb.py`). Typical view test:
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
- Check contracts at the layer where they are promised: exact response bytes for compatibility, parsed DOM for structure/accessibility, and `django_assert_num_queries` or `CaptureQueriesContext` for SQL counts/categories. Examples: `tests/test1/test_navbar_costs.py::test_nonparticipant_complete_response_bytes_and_queries` and `::test_navbar_isolated_costs`.
- Use lazy-object assertions when evaluation timing matters. `tests/test1/test_navbar_templates.py::test_context_copies_and_repeated_calls_reuse_one_lazy_build` covers copied Django contexts, includes, and repeated renders; `::test_omitted_consumers_and_modal_direct_includes_do_no_work` guards zero-work paths; `tests/test1/test_lazy_labels.py` checks lazy translations resolve in the active language.
- Escaping tests should parse output and assert hostile inputs do not create markup or active attributes. `tests/test1/test_navbar_templates.py::test_plain_labels_and_accessible_names_are_escaped_once` covers raw/safe labels, entity-looking text, and localized accessible names.
- Bulk action tests separate rendered selection, request validation, lifecycle, and return-navigation contracts. Use `tests/test1/test_bulk_source.py` for table/card selection markup and proof that source rendering does not invoke destination permission/item hooks; use `tests/test1/test_bulk_scope.py` for UUID/integer/string key canonicalization, deduplication, malformed and NUL key rejection, write-database routing, and authorization boundaries; use `tests/test1/test_bulk_flow.py` for review/execute ordering and atomic rollback; use `tests/test1/test_bulk_return.py` for origin preservation. Build requests with the real Django `Client` and assert state, response, or query behavior at the boundary under test.

## Breadcrumb and Effective Ordering Contracts

- `tests/test1/test_breadcrumb.py::test_breadcrumb_default_bytes` compares three literal outputs: empty, single current item, and linked/unlinked ancestors with a current item. Keep these exact captures alongside DOM checks so default class integration preserves whitespace and escaping.
- `tests/test1/test_breadcrumb.py::test_breadcrumb_class_overrides` parametrizes three class keys across theme registration, settings, and settings-over-theme precedence, with custom strings, empty strings, `None`, invalid integers, and hostile quote-containing values. Its `assert_breadcrumb_classes` helper verifies the complete element/attribute structure, labels, and link destination. `::test_breadcrumb_current_page_independent_of_classes` clears all contributions and preserves current-page semantics.
- The opt-in `breadcrumb_classes` fixture in `tests/test1/test_breadcrumb.py` snapshots `_THEME_BUTTON_CLASSES`, resets the class cache, and restores both registry and cache in `finally`. Use this pattern for tests that register theme classes; `override_settings` scopes application overrides.
- `tests/test1/test_table_template.py::test_table_header_effective_sort_state` has eight cases: URL ascending/descending, unsorted, constructor ascending/descending, `Meta.order_by`, and prefixed URL ascending/descending. It creates real django-tables2 tables and applies `RequestConfig`; assert both icon direction and `aria-sort` from effective ordering.
- `tests/test1/test_table_template.py::test_table_header_attributes_and_links` checks custom header attributes, hostile text escaping, next-sort URLs, and preservation of unrelated query parameters. Its `HeaderAttributes(HTMLParser)` also counts raw `aria-sort` attributes: DOM parsers alone can hide duplicates. Orderable headers have exactly one; nonorderable headers have none.

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
- Exact compatibility captures may live as frozen raw strings beside their deterministic rendering helper. `tests/test1/test_data_prefix.py` holds seven component outputs and two config aliases; `tests/test1/test_breadcrumb.py` holds three breadcrumb outputs. Compare byte-for-byte; never normalize or regenerate these captures during ordinary test runs.
- Real HTTP behavior uses Django `Client` against the in-memory project. Navbar examples include `tests/test1/test_navbar.py::test_real_owner_navbar`, `tests/test1/test_navbar_templates.py::test_component_tags_render_independently_in_real_response`, and `::test_real_response_omits_all_navbar_work_without_consumers_or_in_custom_modal`.
- Published examples are executable fixtures: `tests/test1/test_navbar_docs.py` extracts navbar recipes and renders them with real context; related harnesses include `tests/test1/test_cancel_docs.py`, `test_object_detail_value_docs.py`, `test_conditional_migration_docs.py`, `test_theme_adoption_docs.py`, and `tests/test1/test_data_prefix_docs.py`. The latter compiles the exact `AppConfig.ready()` recipe from `docs/reference/theme.md`, calls the real tag, renders copied template recipes against real groups, and parses the output DOM. Keep recipe markers/fences stable or update extraction tests with documentation changes.
- Mutable theme prefix tests must request `isolate_data_prefix` from `tests/test1/conftest.py`; this fixture restores the shared module scalar via `monkeypatch`. Do not add it as an autouse fixture: tests that never register a theme should not acquire unrelated global-state setup. Registration is startup-only; these tests cover repeated startup registration and late tag reads, not runtime switching guarantees.

## Coverage

**Requirements:** `fail_under = 88` (`pyproject.toml` `[tool.coverage.report]`); sources are the five packages; `relative_files` and path mapping for nox installs. XML per session (`coverage-py<py>-dj<dj>.xml`), uploaded to Codecov (`codecov.yml`).

```bash
pytest tests -n auto --cov --cov-report=term-missing
```

## Test Types

**Unit Tests:** helpers, settings validation, checks (`tests/test1/test_ancestor_*.py`).
**Integration Tests:** Django test-client requests across ViewSets, permissions, nested resources, Guardian, workflow, polymorphic.
**Docs Tests:** tests such as `test_access_trace_docs.py` and `test_badge_docs.py` verify documentation against the code.
**JavaScript:** Vitest unit tests (`vitest.config.js`) cover `tests/js/`; `.github/workflows/js.yml` runs `npm ci --ignore-scripts` and `npm test` on Node 22. The package declares Node `>=20` (`package.json`). `tests/js/runtime-contract.test.js` launches the ordinary suite in a disposable Node-only checkout, verifies every ordinary test file executes, and asserts that integration tests fail explicitly when the selected Python runtime is missing or invalid. The real Django configuration bridge is in `tests/js-integration/js-config.test.js`: it runs `pytest_configure()`, registers a namespace/data prefix/tooltip placement, renders `{% cv_config %}` through Django, then executes `adapters.js` and `tooltip.js` in jsdom and asserts the configured host receives the owned tooltip. `tests/js-integration/formset.test.js` combines actual Django-generated fragment markup and POST validation with a disposable Node driver that loads shipped `formset.js` and submits the DOM's real `FormData`; see `tests/test1/test_fragment_authorization.py::test_server_fragment_dom_round_trip`. Run this separate lane with the documented `CV_FRAGMENT_PYTHON` and `PYTHONPATH` command below. `tests/browser/` contains purpose-built Chromium scripts and Python servers; these do not run via `npm test` or the Nox Python matrix.
**nox:** `noxfile.py` installs the built distribution (asserts `crud_views` is not imported from `src/`), runs the full Python suite with coverage, then reruns the full suite with `--no-cov` and `CV_ACCESS_RECORD_REQUESTS=1` to observe every existing request with the same assertions (first run uses `CV_ACCESS_RECORD_REQUESTS=0`). `.github/workflows/tests.yml` defines Python 3.12–3.15 against Django 4.2/5.2/6.0; Django 4.2 is skipped for Python 3.14/3.15, leaving ten supported combinations. Each supported row runs both recorder modes and the examples suite; coverage reports are `coverage-py<py>-dj<django>.xml`. `nox -s crispy_floor` separately tests the declared django-crispy-forms/crispy-bootstrap5 floors against Django 4.2 and 6.0 on Python 3.12; `nox -s manage_report_floor` is an opt-in manual Pydantic 2.2.1 compatibility gate. This matrix describes configured Nox/CI coverage; a local run or one selected receipt proves only the rows actually completed.

## Browser and Revision-Bound Evidence

- Report Python full-suite evidence with the revision and exact matrix rows completed. A prior coverage XML, plan receipt, or partial matrix is not proof of a fresh full run; generated files such as `coverage-py3.12-dj4.2.xml` do not identify a passing current revision by themselves.
- Browser scripts under `tests/browser/` launch Chromium against purpose-built local Django servers (for example `tests/browser/theme-adoption.cjs`, `queryset-conditional.cjs`, and `cancel-navigation.cjs`). Their receipts are phase-specific: verify recorded source hashes/revision before describing them as current.
- `.github/workflows/js.yml` runs `npm test` (Vitest) on Node 22; the Node-only runtime-contract assertion is part of that command. Browser scripts are not a blanket part of it or the Python Nox matrix. Name the script, browser/runtime, target revision, and result when reporting a browser check.
- `npm run test:integration` uses `vitest.integration.config.js`; it is distinct from the jsdom unit suite and from browser scripts in `tests/browser/`. It requires a selected installed Python environment containing Django test dependencies; no fallback or installation occurs.

## CSS Tokens and Compact Formset Browser Checks

- `tests/js/css-tokens.test.js` is the focused source-contract suite for the six documented CRUD Views CSS tokens and fallback chains in `src/crud_views/static/crud_views/css/manage.css` and `formset.css`. It checks bounded declaration parsing, source locations, and rejected/accepted fixtures without adding a CSS parser dependency. Run it through `npm test -- tests/js/css-tokens.test.js`.
- `tests/browser/css-tokens.cjs --case all --output <receipt.json>` checks computed CSS in six browser cases. `tests/browser/manage-presentation.cjs --case smoke --output <receipt.json>` checks the three manage smoke cases. These purpose-built Chromium scripts are independent of `npm test` and the Python suite.
- `tests/browser/conditional-formsets.cjs --case compact-lifecycle` records the compact lifecycle browser case; `--compact-capture-root` scopes capture output and evidence paths to a repository-local directory. Follow the source path-safety validation and check that the destination is ignored and untracked before capture.
- Check capture evidence in a separate invocation with `--check-evidence <receipt.json>`. `tests/browser/conditional-formsets-evidence.test.cjs` runs writer/checker contracts in an isolated VM and covers default/override agreement, unsafe roots, traversal, stale or missing captures, tracked destinations, symlinks, and invalid filesystem leaves. Treat browser receipts as revision-bound: inspect their recorded revision/source hashes before using them as evidence for the current tree.
- For Python/Django compatibility, the configured matrix is ten supported Python/Django combinations. A single local interpreter, the JavaScript integration bridge, a manual floor session, or a phase receipt does not establish all ten combinations; report the exact rows and revision actually exercised.

## Common Patterns

**Error Testing:**
```python
with pytest.raises(ImproperlyConfigured, match=r"form_tag=False|form_action"):
    ...
```
**Warnings:** use `caplog` to assert logged warnings when `CRUD_VIEWS_STRICT` is off.
**Async:** Not used.

## JavaScript Commands and Cross-Runtime Setup

Ordinary JS checks need Node and installed npm dependencies only. The runtime-contract test copies its bounded JS
inputs into a temporary directory, links `node_modules`, and exposes only a Node executable on `PATH`; this keeps
the unit suite independent from Python even when the parent shell is inside a virtualenv. `npm test` includes that
boundary test.

The integration suite needs an explicit interpreter with the repository's Django test dependencies. From the
repository root, the documented recipe is:

```bash
CV_FRAGMENT_PYTHON="$PWD/.nox/crispy_floor-3-12-django-6-0/bin/python" \
PYTHONPATH="$PWD/src:$PWD" npm run test:integration
```

The exact `.nox` environment may differ; choose an existing supported runtime. `CV_FRAGMENT_PYTHON` must be
executable and able to import the test project dependencies. The `PYTHONPATH` pins imports to this checkout. The
integration harness fails clearly for absent or invalid interpreter selections, and makes no silent skip or package
installation. `tests/js-integration/js-config.test.js` tests Django settings/config serialization into a DOM element
and actual JS consumption. `tests/js-integration/formset.test.js` crosses Django-rendered fragments, JS row insertion,
and a real Django POST/authorization assertion. Passing `npm test` alone says nothing about these Django-backed
paths.

---

*Testing analysis: 2026-11-21*

Both integration suites import `selectedPython()` from `tests/js-integration/python.js`. This shared test-only helper preserves the selected virtualenv launcher and bounded missing/invalid-interpreter diagnostics.
