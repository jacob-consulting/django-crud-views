---
last_mapped_commit: 7d9b74dc51306d98ce007cd001f416463982c456
last_mapped_at: 2026-11-26
---
# Testing Patterns

**Analysis Date:** 2026-11-26

## Test Framework

**Runner:**
- pytest with pytest-django, pytest-xdist, pytest-cov, pytest-mock, pytest-random-order (`pyproject.toml` `test` extra); `addopts = "--strict-markers"`.
- Config: `pyproject.toml` `[tool.pytest.ini_options]`; Django is configured in code by `pytest_configure()` in `tests/test1/conftest.py` (in-memory sqlite `default` and `shard` DBs, `CRUD_VIEWS_STRICT=True`).

**Assertion Library:**
- Plain `assert`, `pytest.raises(..., match=...)`, `caplog`; HTML parsed with `lxml` / `cssselect` (`tests/test1/test_crud.py`, `tests/test1/test_robustness.py`, `tests/lib/helper/golden.py`). Test dependencies are unpinned in `pyproject.toml`; report actual runtime versions for verification.

**Run Commands:**
```bash
PYTHONPATH=src:. pytest tests -n auto      # full checkout suite, multicore (preferred)
pytest tests -n 4                          # broad local run on a shared/resource-bounded machine
pytest tests/test1/test_crud.py -v         # representative single file
pytest tests/test1/test_crud.py::test_create_author # single test
task test                                  # nox matrix: py3.12-3.15 x Django 4.2/5.2/6.0
pytest tests -n auto --cov                 # coverage (fail_under = 88)
CV_UPDATE_GOLDEN=1 pytest tests/test1/test_action_menus_golden.py   # regenerate goldens
npm test                                   # Node/jsdom unit + runtime-boundary checks (tests/js)
npm run test:integration                   # requires CV_FRAGMENT_PYTHON + PYTHONPATH (see below)
task test-js                              # task wrapper; runs npm test
```
Use four pytest-xdist workers for broad local runs when resources are shared; use `-n auto` on a dedicated machine (`CLAUDE.md`). Core CI/Nox tests use `-n auto`; `noxfile.py::examples` forwards positional arguments and does not select workers itself. Add `-- -n auto` or a bounded worker count when invoking that broad examples session. Run serially only for a concrete isolation/order/debugging constraint or when worker startup costs more than a tiny selection.

## Test File Organization

**Location:** Separate from source, under `tests/`:
- `tests/test1/` - Python tests (topic-focused `test_*.py` files, mostly flat) plus test apps `tests/test1/app/` (models Author UUID, Publisher int, Book child, Vehicle polymorphic, Campaign workflow), `tests/test1/od_app/`, `tests/test1/project/` (urls), `tests/test1/golden/` (stored markup).
- `tests/lib/helper/` - shared helpers: `user.py` (`user_viewset_permission`), `boostrap5.py` (`Table` HTML parser), `golden.py` (`check_golden`), `guardian.py`, `forms.py`, `icons.py`.
- `tests/browser/` - `*.cjs` scripts, `*.test.cjs` and Python servers for browser tests; `tests/js/`, `tests/js-integration/` - vitest.
- `tests/check_manage_schema.py` - schema check script.

**Naming:** `test_<topic>.py`, functions `test_<behavior>`; topic families share a prefix.

## Test Structure

**Suite Organization:** Module-level functions are common; topic-based test classes also group related contracts (for example `TestBreadcrumbItem` and `TestBreadcrumbTopLevel` in `tests/test1/test_breadcrumb.py`). A complete public-boundary test from `tests/test1/test_crud.py`:
```python
@pytest.mark.django_db
def test_detail_author(client_user_author_view: Client, cv_author, author_douglas_adams):
    pk = author_douglas_adams.pk
    response = client_user_author_view.get(f"/author/{pk}/detail/")
    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "Douglas" in content
    assert "Adams" in content
```

**Patterns:**
- `@pytest.mark.django_db` on DB tests (heavily used); `@pytest.mark.parametrize` extensively.
- Fixtures naming: `cv_<model>` for ViewSets, `user_<model>_<permission>` for users, `client_user_<model>_<permission>` for logged-in clients, plus data fixtures like `author_douglas_adams`.
- Permissions granted with `user_viewset_permission(user, viewset, "view")`.
- Parse rendered HTML with helpers (`Table(response)`) rather than substring matching.
- Check contracts at the layer where they are promised: exact response bytes for compatibility, parsed DOM for structure/accessibility, and `django_assert_num_queries` or `CaptureQueriesContext` for SQL counts/categories. Examples: `tests/test1/test_navbar_costs.py::test_nonparticipant_complete_response_bytes_and_queries` and `::test_navbar_isolated_costs`.
- Use lazy-object assertions when evaluation timing matters. `tests/test1/test_navbar_templates.py::test_context_copies_and_repeated_calls_reuse_one_lazy_build` covers copied Django contexts, includes, and repeated renders; `::test_omitted_consumers_and_modal_direct_includes_do_no_work` guards zero-work paths; `tests/test1/test_lazy_labels.py` checks lazy translations resolve in the active language.
- Escaping tests should parse output and assert hostile inputs do not create markup or active attributes. `tests/test1/test_navbar_templates.py::test_plain_labels_and_accessible_names_are_escaped_once` covers raw/safe labels, entity-looking text, and localized accessible names.
- Bulk action tests separate rendered selection, request validation, lifecycle, and return-navigation contracts. Use `tests/test1/test_bulk_source.py` for table/card selection markup, destination admission/state checks, and proof that source rendering does not invoke per-record permission/check hooks; use `tests/test1/test_bulk_scope.py` for UUID/integer/string key canonicalization, deduplication, malformed and NUL key rejection, write-database routing, and authorization boundaries; use `tests/test1/test_bulk_flow.py` for review/execute ordering and atomic rollback; use `tests/test1/test_bulk_return.py` for origin preservation. Build requests with the real Django `Client` and assert state, response, or query behavior at the boundary under test.
- Destination-gated toolbar (Phase 06.46): `tests/test1/test_bulk_source.py::test_bulk_toolbar_snippet_guards_itself` renders an override that includes `crud_views/snippets/bulk_toolbar.html` without the offered-action condition and asserts no empty toolbar (form, select-all) for a viewer admitted to no action; `::test_bulk_button_presentation_errors_are_not_swallowed` makes the `cv_get_action_short_label` hook raise `ObjectDoesNotExist` or a silent-gate error and asserts the same exception object propagates (Django templates would otherwise silence it and drop the toolbar).
- Query-cost tests compare relative cost, not absolute counts. `tests/test1/test_bulk_source.py::test_bulk_source_query_cost` captures queries for the page with offered actions and for the same page with `cv_bulk_actions = ()`, and asserts `len(offered_queries) == len(baseline_queries)` across nested/top, table/card, row and action counts; the measured count is recorded via `record_property`. Do not pin absolute query numbers.

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
- Published examples are executable fixtures: `tests/test1/test_navbar_docs.py` extracts navbar recipes and renders them with real context; related harnesses include `tests/test1/test_cancel_docs.py`, `test_object_detail_value_docs.py`, `test_conditional_migration_docs.py`, `test_theme_adoption_docs.py`, and `tests/test1/test_data_prefix_docs.py`. The latter compiles the exact `AppConfig.ready()` recipe from `docs/reference/theme.md`, calls the real tag, renders copied template recipes against real groups, and parses the output DOM. Keep recipe markers/fences stable or update extraction tests with documentation changes. Documentation tests pin hook and template names (for example `tests/test1/test_bulk_docs.py::test_bulk_guide_names_the_visibility_hooks_and_template_guard`, `::test_bulk_hook_exception_beside_stability_hook_inventory`). `::test_bulk_theme_authorization_boundary` pins that the "Authorized data in overridden templates" section of `docs/reference/theme.md` states the toolbar offers bulk destinations only to a viewer passing `cv_has_access` and `cv_action_enabled`, with no record checks during source rendering, links `bulk_actions.md#which-actions-a-user-sees` and names `view.cv_bulk_buttons`. `superpowers/prompts/acme-example-sync/drift.py` is a docs/tooling script, not part of the test suite, not prose wording.
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
**Async:** Core Django request tests use synchronous clients; no general Python async-fixture pattern is configured in `tests/test1/conftest.py`. JavaScript asynchronous behavior uses the separate Vitest/jsdom harness in `tests/js/`.

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

Both integration suites import `selectedPython()` from `tests/js-integration/python.js`. This shared test-only helper preserves the selected virtualenv launcher and bounded missing/invalid-interpreter diagnostics.

## JavaScript Adapter Event Prefix

- `tests/js/adapters.test.js` parametrizes `MODAL_EVENT_CASES` (no `data-data-prefix` on `#cv-config`, `bs`, `coreui`, hyphenated `my-lib`) via `describe.each`. Modal `onHidden` waits for `hide.<prefix>.modal` then `hidden.<prefix>.modal` (PR #405, #403), for the default, object-namespace and callback-namespace adapters, and unsubscribes idempotently. Dispatch events named from the registered prefix; an absent element or attribute means `bs`.

## Bulk Variant and Copied Leaf Contracts

- `tests/test1/test_bulk_variants.py` exercises table/card sources, `label`/`icon`/`both` modes, available/missing/disabled/host icons, four destination variants, inherited secondary styling, explicit empty/None class overrides, form-style isolation, and native review POSTs. Preserve real request/state assertions alongside parsed markup checks.
- `tests/test1/test_bulk_variants.py::test_stock_toolbar_matches_form_leaf` captures each actual normalized payload, independently renders `crud_views/tags/button/form.html`, and compares it byte for byte with both the raw response control and the bulk leaf under the default secondary variant, across 24 source/mode/icon combinations. Raw extraction retains each terminal newline and the full signed URL. The comparison is computed live, has no stored fixture (the former frozen `bulk_toolbar_pre_variant.json` and `test_stock_toolbar_bytes` are removed) and is relative to the form leaf; absolute form-leaf bytes are pinned by `tests/test1/test_form_buttons_golden.py`.
- `tests/test1/test_bulk_docs.py::test_copied_bulk_leaf_contract` extracts the exact nine-field Django recipe from `docs/reference/buttons.md`, renders it and the shipped bulk leaf against the actual projected payload, and compares both with the stock control. Its 36 cases cover table/card, three modes, inline/host/disabled icons and hostile labels. Missing `cv_title` is permitted outside icon mode; the original icon key remains available when disabled.
- The copied-leaf test instruments `Variable.resolve` and checks recorded reads after rendering, since Django conditionals can suppress exceptions. It proves the guard with false/missing/truthy synthetic undeclared input, then asserts that form-only keys do not affect either template. Use this pattern to detect ambient-context dependencies rather than relying on output equality alone (`tests/test1/test_bulk_docs.py::test_copied_bulk_leaf_contract`).
- `tests/test1/test_bulk_variants.py::test_short_labels_and_escaping` and `::test_bulk_action_key_is_escaped` exercise plain, safe and lazy hostile text, escaped action URLs/keys, accessible labels, and native submit attributes. Test DOM semantics and exact escaping together.
- `tests/test1/test_bulk_docs.py::test_bulk_modules_remain_in_maintained_crispy_floor_selection` parses `noxfile.py` to keep bulk flow/execution/source/scope/return/variants in `CRISPY_FLOOR_TESTS`. A passing local selection does not establish that the floor sessions or full supported matrix ran.

## Governed Link Matrix and Runtime Cost Contracts

- `tests/test1/test_link_access_matrix.py` executes 1,178 unique coordinates against `tests/test1/link_access_matrix_baseline.json`. Its stage-3b ledger records 45 link/filter deltas with before, after, decision IDs and reasons. Hash-checked reconstruction proves the prior baseline; request coordinates are prohibited in the delta ledger.
- Keep real rendered control outcomes and direct target requests together in `tests/test1/test_link_consumers.py`; public hook spies in `test_link_access.py` prove exact actor/object identity, parent-before-own-before-state order and short-circuiting.
- Actual Cancel and bulk return contracts live in `tests/test1/test_link_cancel.py` and `test_bulk_return.py`. Test explicit actor/request binding, missing parent/configuration, true/false create overrides and parent-only behavior at the actual Cancel boundary.
- Request authorization and access-trace expectations remain independently protected in `tests/test1/test_authorization_matrix.py`, `test_ancestor_authorization.py` and `test_access_trace_ancestors.py`. Link-only changes cannot justify weakening request outcomes.
- `tests/test1/test_link_consumer_costs.py` parametrizes 444 runtime scenarios: 276 historical coordinates plus 168 additional coordinates. Capture real SQL with `CaptureQueriesContext`; classify permission/ancestor/other work separately from public hook and provider events.
- Record row counts, composition, allow/deny, actor-cache and vocabulary-cache preparation alongside measured costs. Query counts bind to those exact fixtures; a lower count does not establish lower response time (`tests/test1/test_link_consumer_costs.py`, `test_guardian_checker_costs.py`, `test_navbar_costs.py`).
- Historical stage-3a before/after receipts are immutable and independently checked. Stage-3b runtime pins and its receipt are separate; do not rewrite historical receipts to match current constants (`tests/test1/test_link_consumer_costs.py::test_historical_cost_receipts_are_independent_of_current_pins`).
- The current checked-in receipt is `.planning/phases/06.51-remove-retained-guardian-link-exceptions-stage-3b-413/06.51-COST-BASELINE.md`, paired with `06.51-COST-MEASUREMENTS.xml`. Tests validate provenance, source identity, XML membership, counts and corruption rejection.
- Missing repository-only receipts skip only their audits. Runtime parametrization and SQL tests remain active without `.planning/`, as proven by `tests/test1/test_link_consumer_costs.py::test_repository_receipt_absence_skips_only_audits`.
- Temporary registered route fixtures must restore the ViewSet registry, permission vocabulary, ContentType cache, URL cache and temporary modules in `finally` (`isolated_routes` in `tests/test1/test_ancestor_authorization.py`). Use fresh actors where a new request/grant lifetime is intended.

## Guardian Grant Lifetime Testing

- `tests/test1/test_guardian_checker.py` covers shared acquisition, actor/model/object isolation, positive/negative grant retention, mutations and fresh requests observing revocation.
- A retained user intentionally preserves loaded grant state. Refresh the user for a new lifetime rather than adding implicit invalidation to make a test pass (`src/crud_views_guardian/lib/permissions.py`, `tests/test1/test_guardian_checker.py`).
- Real list responses and independent controls accompany query pins in `tests/test1/test_guardian_checker_costs.py`. Use its fixture/cache protocol rather than applying recorded counts to arbitrary pages.

## Source-Bound Verification Evidence

The current recorded verification is `.planning/phases/06.52-publish-check-link-access-as-the-documented-way-to-decide-a/06.52-VERIFICATION.md`. Its ship addendum binds the documentation clarification at `9ec58fa48bbe3a656349c499313d179f817827ef`; the full source and examples receipts are explicitly historical. This mapping runs no tests.

| Evidence scope | Recorded result | Limits |
| --- | --- | --- |
| Current link/navbar documentation | 77 passed, four workers | Ship receipt covers changed docs and tests; strict MkDocs and scoped Ruff check/format also pass |
| Current verifier named checks | 2 passed across separate tiny invocations | Stability inventory and original public object-target tracer only |
| Historical full core suite | 20,397 passed, six workers | Python 3.12.3 / Django 6.0.10, recorder off, checkout imports; precedes the three-file ship clarification |
| Historical example project suite | 637 passed plus 300 subtests, six workers | Same runtime; six known pagination warnings; precedes that clarification |
| Protected matrix/cost gate | 1,665 passed recorded by plan 02 | Reused for unchanged protected inputs; no new full matrix claim |

- See `06.52-ship-evidence/receipt.json` and `06.52-verification-ship-evidence.json` under the phase directory for current checks. The historical full result is `06.52-03-evidence/full-source-fixed.json`; examples are recorded in `06.52-regression-evidence/receipt.json`. The verifier reports exactly three changed inputs (two Markdown files and their docs test), with production source, executable Python fences and public behavior tests unchanged. Reuse historical evidence only within those recorded preservation limits.
- The receipts use explicit checkout `PYTHONPATH=src:.` and `CV_ACCESS_RECORD_REQUESTS=0`. They do not certify recorder-on, other Python/Django rows, browser scenarios or rebuilt installed-distribution behavior.
- Nox's installed-origin assertion and recorder-on/off matrix in `noxfile.py` describe configured coverage; only completed named rows establish evidence. Cached XML or a prior phase count is insufficient proof.
- `.github/workflows/tests.yml` triggers on main pushes and PRs targeting main; `.github/workflows/js.yml` runs the separate JavaScript unit lane. Browser and Django/JS integration commands require their own explicit evidence.

## Public Link Checker Tests and Executable Examples

- `tests/test1/test_public_link_access.py::test_public_signature_and_enum` pins the exact positional/keyword signature, regular enum members, identity and false-denial behavior. `::test_public_validation_before_authorization` and malformed target/container tests use spies to establish that invalid input reaches neither delegation nor permission/state hooks. Generator and queryset inputs remain unconsumed (`::test_public_invalid_ancestor_container`).
- Keep compatibility and failure cases explicit: proxy/subclass/polymorphic/Resource inputs, unsaved objects, missing parents, ancestor holes, excess slots and declaration errors are covered in `tests/test1/test_public_link_access.py`. Match prefixed public validation messages separately from reached existing ancestry/authentication errors; preserve exception identity when delegation fails.
- `::test_public_direct_outcomes`, `::test_public_state_object_and_order`, and `::test_public_ancestor_alignment` use real registered core/Guardian/Resource views with controlled hooks. Assert exact actor/object identities, nearest-first supplied slots, outermost-first reached gates, denial short-circuiting and correct state object. `::test_public_repeated_decisions` changes permission/state results between calls to prove decisions are not cached.
- `::test_public_no_domain_queries` reloads rows outside measurement to clear FK caches, instruments lookup/save/refresh, captures SQL and rejects domain-table FROM/JOIN access. This proves no domain loading or mutation; it permits authorization queries and does not promise zero SQL. `::test_public_membership_is_not_validated` preserves caller responsibility for ancestry membership.
- `tests/test1/test_link_access_docs.py::test_public_documented_examples` parametrizes the three actual fences in `docs/reference/link_access.md`: Object target, Nested collection and Off-page caller. Its `_run_public_example` uses the shared `_fence` extractor with `exec(compile(...), namespace)` and only documented inputs, then checks `result is LinkAccess.ALLOWED` and `show_link is True`. The off-page example exercises a registered Guardian target and two supplied ancestor levels without a request or view instance.
- Preserve the independent original `tests/test1/test_public_link_access.py::test_public_object_tracer`. Keep stable inventory, migration links and bounded authorization/database prose under `tests/test1/test_link_access_docs.py`; update those assertions when an intentional public contract changes. Tests execute published examples directly, so changing headings or fences requires maintaining extraction rather than retyping recipes.

---

*Testing analysis: 2026-11-26*
