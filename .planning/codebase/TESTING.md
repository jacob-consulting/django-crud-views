---
last_mapped_commit: 644048051fb9df94d042c698a3962738e486d74b
last_mapped_at: 2026-11-13
---
# Testing Patterns

**Analysis Date:** 2026-11-13

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
nox -s crispy_floor --django=4.2            # Declared crispy dependency floors, Django 4.2
nox -s crispy_floor --django=6.0            # Declared crispy dependency floors, Django 6.0
```

`noxfile.py` defines `crispy_floor` on Python 3.12 with exact `django-crispy-forms==2.0` and `crispy-bootstrap5==2023.10` pins. It checks resolved package versions and audits Django 6 `format_html()` calls before running `CRISPY_FLOOR_TESTS` with `-n auto`. The focused list is intentionally maintained separately from the full suite and includes `tests/test1/test_crispy_columns.py`; its only deselection is `tests/test1/test_form_buttons_golden.py::test_filter_form_baseline`, whose outer crispy wrapper differs at the floor. Keep this floor list and exclusion explicit when adding coverage for the crispy leaf features.

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

## Registry and Rendering Contract Tests

- `tests/test1/test_button_classes.py` pins both new registry keys, empty defaults, and the documented core count. `tests/test1/test_button_classes_checks.py::test_legend_keys_are_recognized` parameterizes the two keys across theme registration and project settings, including explicit empty values.
- Registry fixtures snapshot `_THEME_BUTTON_CLASSES` and reset the class cache before and after each test. Reuse this isolation when changing registrations or settings; don't rely on pytest-xdist worker lifetime to clear shared module state (`tests/test1/test_button_classes.py`, `tests/test1/test_button_classes_checks.py`, `tests/test1/test_conditional_layout.py`, `tests/test1/test_formsets_compact.py`).
- `tests/test1/test_conditional_layout.py` verifies layered precedence and independence, class escaping, ordinary legend text escaping, and the no-legend `div` path against rendered crispy HTML. `tests/test1/test_formsets_compact.py` parameterizes full, nested, classic/compact, and row-only formsets; it checks direct owner legends, omission on row-only roots, and preservation of full nested child legends.
- Hostile-value tests must check both raw escaped markup and parsed DOM semantics: exact original text/class, no child injection, and no unexpected script/image/attribute nodes. A row-only fragment assertion should target its own root; nested full descendants are expected to have legends (`tests/test1/test_conditional_layout.py::test_toggle_group_legend_escapes_plain_text_and_classes`, `tests/test1/test_formsets_compact.py::test_formset_legend_escapes_plain_text_and_classes`).
- `tests/test1/test_theme_adoption_docs.py::test_workflow_presentation_docs` and `tests/test1/test_button_classes.py::test_documented_default_key_count_matches_table` guard reference inventories: 102 core keys and 120 effective core-plus-workflow keys (18 contributed by workflow). Keep embedded fresh-process source and documentation counts synchronized.
- Phase 06.25.1 retained a full-suite result of 12,486 passed and one existing skip on Python 3.12 / Django 5.2; this is one environment, not a run of the supported matrix. Focused legend/registry/documentation selection and the full run used multicore pytest. See `.planning/phases/06.25.1-issue-346/06.25.1-VERIFICATION.md` for exact gate evidence and environment details.

## Executable Documentation Recipes

**Published JavaScript fences:** Mark a public recipe with a unique HTML comment and extract the actual fence in the test. `tests/js/adapters.test.js` loads the shipped adapter factory and executes the `cv-tooltip-adapter-location` fence from `docs/reference/javascript.md`; do not duplicate the recipe in test code. Keep assertions tied to production factory behavior, including option precedence, instance identity, disposal, stale callback suppression, absent components, late availability, and repeated initialization.

**Cross-runtime formset integration:** `npm test` is Node/jsdom-only. The required `npm run test:integration` command executes real Django-rendered fragments and submits the DOM's actual `FormData`. Run it from the repository root with an explicit already-prepared interpreter and source checkout path:

```bash
CV_FRAGMENT_PYTHON="$PWD/.nox/crispy_floor-3-12-django-6-0/bin/python" \
PYTHONPATH="$PWD/src:$PWD" npm run test:integration
```

`CV_FRAGMENT_PYTHON` must be an executable Python with Django test dependencies; select the appropriate prepared runtime when its path differs. The harness validates that interpreter and fails on missing or unusable values; it does not install packages or silently skip the Django bridge (`docs/reference/javascript.md`, `tests/js-integration/formset.test.js`).

## Ship Gate Evidence

- Before integrating Phase 06.27, Phase 06.28 ship verification passed 12,519 Python tests using `-n 4` on Python 3.12.3 / Django 6.1.2, and 401 JavaScript tests. `mkdocs build --strict`, `ruff check`, and `ruff format --check` passed. This predates integration of Phase 06.27 and is the recorded ship environment only; it does not establish that the supported Python/Django Nox matrix was run.

- After integrating Phase 06.27 for PR #358, the combined tree passed 12,710 Python tests with four workers (Python 3.12.3 / Django 6.1.2), 438 JavaScript tests, strict MkDocs and Ruff. The phase06.28 verifier independently reran all 18 recipe cases; browser and full supported-runtime matrix evidence remain separate.

## Choice-Driven Conditional Groups (Phase 06.27)

- Python conditional-group coverage is divided by contract among `tests/test1/test_conditional_toggle.py`, `tests/test1/test_conditional_group.py`, `tests/test1/test_conditional_checks.py`, `tests/test1/test_conditional_persistence.py`, and `tests/test1/test_conditional_layout.py`. Keep toggle parsing, form validation, configuration checks, persistence, and rendering assertions in their corresponding modules.
- For choice activation, cover native `Select` and `RadioSelect`, string and integer tokens, falsy values such as zero, and prefixed forms. Verify invalid or missing cleaned controller data cannot activate a group (`tests/test1/test_conditional_toggle.py`, `tests/test1/test_conditional_group.py`).
- Persistence assertions should query saved model state as well as `cleaned_data`. Cover inactive forged values, explicit falsy values, model-choice inference, nullable and blankable clearing, defaults, and inherited model/form validation (`tests/test1/test_conditional_persistence.py`).
- Browser checks separate stock/native choice widgets from lifecycle behavior. Generate records with `tests/browser/conditional-formsets.cjs` and validate them with `tests/browser/conditional-formsets-evidence.test.cjs`; assert exact case matrices and observed values.
- Phase 06.27's pre-fix compatibility pass recorded the full Python suite at **12,700 passed, 1 existing skip**, 420 full JS tests, examples, and fragment integration. These are historical pre-fix results. After review fixes, targeted conditional tests recorded **364 passed on each of Django 4.2, 5.2, and 6.0**, with 92 focused JS toggle tests and targeted evidence/browser/source checks. The full Python suite was not rerun after fixes; do not present its historical count as post-fix verification. See `.planning/phases/06.27-choice-driven-conditional-groups-354/06.27-COMPATIBILITY.md` and `.planning/phases/06.27-choice-driven-conditional-groups-354/06.27-VERIFICATION.md` for exact provenance and limits.

## Themeable Numbered Column Helpers (Phase 06.29)

- `tests/test1/test_crispy_columns.py` owns rendered behavior for the twelve `ColumnN` helpers: compare default bytes against ordinary crispy `Column`, parameterize all widths and registry values, and verify theme/settings precedence and late lookup. Use its layout/context tracer, custom-template ownership cases, caller attribute and hostile-value assertions, plus built-in delete/formset/workflow consumer checks as patterns for changes to crispy wrapper rendering.
- Registry acceptance, invalid values, empty/`None`, and utility-mode contracts are tested in `tests/test1/test_button_classes_checks.py`; keep the documented and executable registry inventory checks in `tests/test1/test_button_classes.py` and `tests/test1/test_theme_adoption_docs.py` synchronized.
- Phase 06.29's verification record reports a full Python suite on Django 5.2/current crispy at **12,868 passed, 1 pre-existing version skip**, and a separate post-merge integration selection at **1,375 passed** with four workers. The floor selection recorded **1,391 passed** on each of Django 4.2 and 6.0. These are phase-recorded results, not checks run during this map refresh; the full-suite count predates ship-time merge integration. See `.planning/phases/06.29-themeable-column-helpers-356/06.29-VERIFICATION.md` for commands, environment, and scope limits.

## Workflow Transition Metadata (Phase 06.32)

- `tests/test1/test_workflow_buttons.py` is the rendered request contract for workflow transition variant/icon metadata. It covers all eight accepted variants; missing, empty, unsupported, hostile, and non-string inputs; icon aliases, suppression, host markup, and declared renderer errors; and full visible captions under icon-only generic form settings.
- Keep class precedence checks across app defaults, theme registrations, and project settings, including empty/null suppression and conflicting generic label-mode keys. Registry tests isolate `_THEME_BUTTON_CLASSES` and reset its cache (`tests/test1/test_workflow_buttons.py`, `tests/test1/test_button_classes.py`).
- Preserve lifecycle assertions for page/modal responses, all comment policies, escaped literal labels/help/blockers, required-comment markers, description IDs, disabled state, radio presentation, custom prefixes/forms, bound-form redisplay, refresh after metadata changes, and no writes on refused transitions (`tests/test1/test_workflow_buttons.py`).
- Inventory and import contracts live in `tests/test1/test_button_classes.py`, `tests/test1/test_button_classes_templates.py`, and `tests/test1/test_import_safety.py`; executable reference tables/recipes live in `tests/test1/test_theme_adoption_docs.py`. Keep 102 core, 18 workflow, and 120 effective counts synchronized, and preserve the bounded AST allowlist for workflow defaults.
- Phase 06.32 records an independent, focused verifier selection of **90 passed** across workflow rendering, variants/icons, precedence, refresh/refusal, docs, app setup, and pre-setup imports on Python 3.12.3 / Django 6.0.10. The phase verification separately records orchestrator-reported full Python **13,150 passed**, focused Django 4.2 and 5.2 selections of **1,589 each**, and JavaScript **438 tests**; those are recorded phase evidence, not commands run during this map refresh. See `.planning/phases/06.32-workflow-transition-variant-and-icon-metadata-362/06.32-VERIFICATION.md` for provenance and limits.

**Checks run during this map refresh:** None. Test/configuration patterns above were inspected from source and phase records only.

*Testing analysis: 2026-11-13*
