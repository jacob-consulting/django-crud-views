---
last_mapped_commit: 9a181a30743ec643e20cbcffcc3a55e950b587e8
last_mapped_at: 2026-11-13
---
# Coding Conventions

**Analysis Date:** 2026-11-13

## Naming Patterns

**Files:**
- Python modules use lowercase snake_case (`src/crud_views/lib/viewset.py`); tests use `test_<behavior>.py` under `tests/test1/`, `tests/browser/`, or `tests/js/`.
- Bootstrap demo apps commonly collect Django `TestCase` classes in `tests.py` (`examples/bootstrap5/formsets/tests.py`).
- JavaScript unit tests use `*.test.js` (`tests/js/toggle.test.js`); Node browser-harness tests use `*.test.cjs` (`tests/browser/presentation-cleanup.test.cjs`).

**Functions:**
- Python functions and pytest fixtures use snake_case; test methods/functions begin `test_` (`tests/test1/test_form_enctype.py`).
- JavaScript functions and variables use camelCase; Vitest test descriptions use readable behavior statements (`tests/js/toggle.test.js`).

**Variables:**
- Python locals use snake_case; Django fixture names encode the entity/action, e.g. `cv_<model>` and `client_user_<model>_<permission>` (`tests/test1/conftest.py`).
- JavaScript locals use camelCase (`tests/js/toggle.test.js`).

**Types:**
- Python classes use CapWords (`CrudView`, `FormsetsTestCase`); Django model/Form/View classes follow domain names (`examples/bootstrap5/formsets/tests.py`).
- JavaScript constructors/classes use PascalCase where needed; ordinary helpers remain camelCase.

## Code Style

**Formatting:**
- Ruff formats Python with 120-character lines, spaces, and double quotes (`pyproject.toml`).
- Ruff is configured to lint `E`, `F`, `I`, `UP`, `B`, `C4`, `SIM`, and `RUF`; it allows the breadcrumb confusable `›` (`pyproject.toml`).
- `ruff format` runs on Markdown Python fences as well as Python files in CI (`.github/workflows/lint.yml`).
- Run `task format` to format and `task check` for Ruff fixes; pre-commit runs `ruff-check` and `ruff-format` (`taskfile.yaml`, `.pre-commit-config.yaml`).
- JavaScript uses four-space indentation, double quotes, and semicolons in the current Vitest suites (`tests/js/toggle.test.js`, `vitest.config.js`).

**Linting:**
- Ruff is the Python linter/formatter; there is no separate configured JS lint command (`pyproject.toml`, `package.json`).
- Ruff per-file ignores permit `RUF012` in tests, examples, and migrations (`pyproject.toml`).

## Import Organization

**Order:**
1. Standard library imports.
2. Third-party packages such as Django, pytest, and lxml.
3. Project and test utility imports.

Ruff's `I` rule enforces import sorting. Follow the grouping visible in `tests/test1/test_form_enctype.py` and `examples/bootstrap5/formsets/tests.py`.

**Path Aliases:**
- No Python package alias is configured. Sources live under `src/`; project commands and explicit cross-runtime commands add `src` to `PYTHONPATH` (`docs/reference/javascript.md`, `noxfile.py`).
- JS tests import helpers via relative paths (`tests/js/toggle.test.js`).

## Error Handling

**Patterns:**
- Tests assert explicit response codes, persisted state, errors, and no-mutation conditions rather than treating any response as success (`examples/bootstrap5/formsets/tests.py`).
- Use `try/finally` for global-state and browser/process cleanup; fixture teardown restores monkeypatched state (`tests/conftest.py`, `tests/browser/presentation-cleanup.test.cjs`).
- Parameterized edge cases use `subTest`, pytest parametrization, or Vitest `it.each` (`examples/bootstrap5/library/tests.py`, `tests/test1/test_form_enctype.py`, `tests/js/toggle.test.js`).

## Logging

**Framework:** Django/Python logging and console APIs; no project-wide logging wrapper was detected.

**Patterns:**
- Tests silence expected JS console chatter in shared setup and spy on warnings/errors when their behavior is under test (`tests/js/helpers/setup.js`, `tests/js/toggle.test.js`).
- Browser harnesses print a concise report location and preserve error details in JSON (`tests/browser/presentation.cjs`).

## Comments

**When to Comment:**
- Explain non-obvious framework/browser behavior and why a regression assertion is necessary, not routine test steps (`tests/test1/test_form_enctype.py`, `tests/browser/presentation-cleanup.test.cjs`).
- Keep scope/contract comments near specialized coverage, as in the formsets example tests (`examples/bootstrap5/formsets/tests.py`).

**JSDoc/TSDoc:**
- No broad JSDoc/TSDoc convention detected. JavaScript test helper intent is documented with short comments where useful (`tests/js/helpers/setup.js`).

## Function Design

**Size:** Keep helpers focused on a reusable fixture or assertion; use local helpers such as `form_payload`, `field_key`, and `fragment_params` to keep formset cases readable (`examples/bootstrap5/project/testing.py`, `examples/bootstrap5/formsets/tests.py`).

**Parameters:** Use pytest fixtures for shared test dependencies and explicit parameters for meaningful case variation (`tests/test1/conftest.py`, `tests/test1/test_form_enctype.py`).

**Return Values:** Return concrete values from parsing/setup helpers; test assertions should state the expected response or state change directly (`examples/bootstrap5/project/testing.py`, `examples/bootstrap5/formsets/tests.py`).

## Module Design

**Exports:** Prefer explicit imports from the module under test; import local helpers where the behavior is shared (`tests/test1/test_form_enctype.py`).

**Barrel Files:** No general JS barrel pattern detected. `tests/js/helpers/load.js` is a test harness that loads shipped static assets, not an application export barrel.

---

## Registry and Template Contracts

- Add presentation hooks through the existing layered button-class registry, with separate keys for independent consumers (`conditional:legend`, `formset:legend`). Both keys default to `""`; keep empty overrides meaningful and preserve the existing default rendering (`src/crud_views/lib/button_classes.py`, `tests/test1/test_button_classes.py`).
- Registry precedence is defaults → installed theme registrations → `CRUD_VIEWS_BUTTON_CLASSES`; cache invalidation follows theme registration and settings changes. Tests that register theme classes should snapshot/restore `bc._THEME_BUTTON_CLASSES` and reset the cache around each test (`tests/test1/test_button_classes_checks.py`, `tests/test1/test_conditional_layout.py`, `tests/test1/test_formsets_compact.py`).
- Keep legend text as ordinary template-interpolated values and classes in quoted attributes. Test hostile plain strings at both boundaries by asserting escaped source output, exact parsed text/attribute values, and absence of injected nodes (`src/crud_views/templates/crud_views/conditional/toggle_group.html`, `src/crud_views/templates/crud_views/formsets/formset.html`, `tests/test1/test_conditional_layout.py`, `tests/test1/test_formsets_compact.py`).
- Preserve markup ownership: ToggleGroup without a legend remains a `div`; formset row-only fragments omit their own outer fieldset/legend, while nested full formsets retain their own direct legends. Assert direct-child ownership and fragment roots rather than banning all descendant legends (`tests/test1/test_conditional_layout.py`, `tests/test1/test_formsets_compact.py`).
- Button-class reference inventories are executable contracts: the core inventory has 102 keys and the effective core-plus-workflow inventory currently has 120. Update the canonical table, reference docs, workflow inventory, and embedded fresh-process guard together (`tests/test1/test_button_classes.py`, `tests/test1/test_theme_adoption_docs.py`, `docs/reference/buttons.md`).

## Executable Documentation Recipes

- Mark public JavaScript recipe fences with stable HTML comments and extract the published fence in tests instead of copying its text into a test-only fixture. The per-location tooltip recipe uses `<!-- cv-tooltip-adapter-location -->`; `tests/js/adapters.test.js` runs the exact fence against the shipped factory loaded by its test harness. Preserve the marker when editing that recipe and update its behavioral assertions alongside the public code (`docs/reference/javascript.md`, `tests/js/adapters.test.js`).
- Keep recipe wrappers delegating to the public adapter/factory. For the tooltip placement recipe, install factory adapters first, capture the existing `init`, apply only the context default when placement is absent, then delegate with the original options. Tests cover explicit and empty placement, non-context locations, cleanup, stale callbacks, replacement identity, missing components, and repeat initialization (`docs/reference/javascript.md`, `tests/js/adapters.test.js`).
- Document both script-loading paths for recipes that initialize immediately: install before `DOMContentLoaded` while loading, or after adapter/factory wiring but before evaluating the initializer once the document is ready. State which changes affect future instances versus already-created instances (`docs/reference/javascript.md`).

## Choice-Driven Conditional Groups (Phase 06.27)

- Declare choice-driven groups with `ConditionalGroup(toggle=ValueToggle(field_name, values=[...]), fields=[...])`. Use explicit `empty_values` for values that cannot be inferred unambiguously from the model field (`src/crud_views/lib/conditional/group.py`, `src/crud_views/lib/conditional/toggle.py`, `tests/test1/test_conditional_group.py`, `tests/test1/test_conditional_persistence.py`).
- Keep server activation based on cleaned controller values; raw POST controls presentation only. Preserve existing `ModelFieldToggle` and `UIFieldToggle` behavior when extending choice support (`src/crud_views/lib/conditional/toggle.py`, `tests/test1/test_conditional_toggle.py`).
- Conditional group field ownership must remain disjoint. Test overlap and clearing conflicts with declarations in both orders (`tests/test1/test_conditional_checks.py`).
- Cover native `Select` and `RadioSelect` tokens as strings and integers, including zero, with prefixed and unprefixed forms (`tests/test1/test_conditional_toggle.py`, `tests/test1/test_conditional_group.py`).

## Themeable Numbered Column Helpers (Phase 06.29)

- Keep `Column1` through `Column12` as public crispy layout helpers exported from `src/crud_views/lib/crispy/__init__.py`; shared rendering and theme lookup belong in `src/crud_views/lib/crispy/table.py`, with defaults in the existing `src/crud_views/lib/button_classes.py` registry (`form:column-1` through `form:column-12`).
- Resolve registry classes at render time so already-built layouts observe current theme/settings. Preserve constructor-provided classes additively, but honor explicit subclass or instance class/template ownership; do not infer ownership by comparing class strings (`src/crud_views/lib/crispy/table.py`, `tests/test1/test_crispy_columns.py`).
- Render through a shallow per-render copy and crispy's existing renderer. Keep caller context and the original layout reusable across nested/sibling renders; avoid mutating shared wrapper state (`tests/test1/test_crispy_columns.py::test_column6_theme_tracer`, `test_column_nested_sibling_context_isolation`).
- The local Bootstrap leaf is an audited bridge only for the installed stock Bootstrap template. Preserve ordinary crispy `Column` behavior and explicit custom templates/packs; test classes, field output, attributes, and ownership through rendered HTML (`src/crud_views/templates/crud_views/crispy/bootstrap5_column.html`, `tests/test1/test_crispy_columns.py`).
- Phase 06.29's recorded inventory was 102 core / 112 core-plus-workflow keys; Phase 06.32 adds eight workflow defaults, bringing the current effective count to 120 (`tests/test1/test_button_classes.py`, `tests/test1/test_theme_adoption_docs.py`, `docs/reference/buttons.md`).

## Queryset-Driven Conditional Fields (Phase 06.30)

- Describe option activation with `QuerysetConditions(field_name, conditional_key=..., keys=...)`; keep native option keys/labels intact while mapping selected model instances to declared categories (`src/crud_views/lib/conditional/queryset.py`, `tests/test1/test_conditional_queryset.py`).
- Keep offered-option coverage validation separate from selected-object validation. Exercise rendering of every offered option (including sources whose groups contain no fields), then submit selected/forged/deleted options through Django's normal `ModelChoiceField` validation and assert no writes on invalid submissions (`tests/test1/test_conditional_queryset_contract.py`, `tests/test1/test_conditional_queryset.py`).
- Assert query budgets with `CaptureQueriesContext` at multiple option counts and row counts. Native scalar admission must remain query-free; category inspection, render costs and labels should have explicit bounded expectations rather than only asserting eventual output (`tests/test1/test_conditional_queryset_contract.py`, `tests/test1/test_conditional_queryset_inlines.py`).
- Cover base forms and independent ordinary/compact inline rows, including category switching, stale/inactive values, errors, save/reopen, empty or retired selections and atomic rejection (`tests/test1/test_conditional_queryset.py`, `tests/test1/test_conditional_queryset_inlines.py`, `tests/test1/test_conditional_queryset_compact.py`).
- Browser acceptance uses real Django servers, Playwright Chromium, source/runtime fingerprints, exact assertion inventories, database-confirmed scenarios, served-script hash checks and cleanup evidence. Keep upstream and pinned downstream targets distinct (`tests/browser/queryset-conditional.cjs`, `tests/browser/queryset_conditional_server.py`, `tests/browser/queryset_downstream_server.py`, `tests/browser/verify_queryset_release.py`).
- Preserve honest separation between automated acceptance and human UAT. Phase 06.30's final UAT records explicit H1 and all H2 responses; browser captures and computed-style assertions alone do not count as human approval (`.planning/phases/06.30-queryset-driven-conditional-fields-360/06.30-UAT.md`, `.planning/phases/06.30-queryset-driven-conditional-fields-360/06.30-VERIFICATION.md`).

## Developer-Only Manage Diagnostics (Phase 06.31)

- Keep authorization and presentation separate in tests: `tests/test1/test_manage.py` checks direct manage access, action visibility and configured developer-group membership, while `tests/test1/test_authorization_matrix.py` covers the broader user/action matrix. An enabled manage page requires explicit membership even for staff/superusers and with `DEBUG=False`; protect both action visibility and URL access (`src/crud_views/lib/views/manage.py`, `src/crud_views/lib/view/visibility.py`).
- Test ancestor diagnostics as a bounded query contract. `tests/test1/test_ancestor_manage.py` verifies the requested scope and declared values beside effective defaults, and asserts that rendering does not probe farther ancestors. Preserve the temporary URL configuration, ViewSet registry, and cache cleanup in its fixture.
- Reuse parameterized core/Guardian policy cases, with specific presentation checks for Guardian pages (`tests/test1/test_ancestor_manage.py`, `tests/test1/test_guardian.py`).

## Workflow Transition Presentation Metadata (Phase 06.32)

- Attach optional `label`, `variant`, and `icon` metadata to existing django-fsm transition declarations; continue rendering through the existing workflow form and native submit template (`src/crud_views_workflow/lib/forms.py`, `src/crud_views_workflow/lib/widgets.py`, `src/crud_views_workflow/templates/crud_views_workflow/widgets/transitions.html`).
- Resolve transition variants through the shared `workflow:transition-<variant>` button-class registry. Keep its eight supported values bounded and use normal app defaults, theme registrations, and project overrides (`src/crud_views_workflow/apps.py`, `src/crud_views/lib/button_classes.py`, `tests/test1/test_workflow_buttons.py`).
- Keep shipped class literals confined to `CrudViewsWorkflowConfig.crud_views_button_class_defaults`; the AST/source inventory exception is intentionally limited to those declarations (`tests/test1/test_button_classes_templates.py`).
- Keep documentation and executable inventories synchronized at 102 core and 120 effective core-plus-workflow defaults (`tests/test1/test_button_classes.py`, `tests/test1/test_theme_adoption_docs.py`, `docs/reference/buttons.md`).

*Convention analysis: 2026-11-13*
