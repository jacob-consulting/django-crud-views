I have what I need. No files were edited; all evidence below comes from read-only inspection at 9de2644.

## 06.4-01

**Summary.** Exact bound-name identity (`form.add_prefix(toggle_field)` → `cv-data-toggle-field`), owning-form equality matching, ambiguity isolation, `cv.initConditional(root)`, and a renderer→shipped-JS→FormData→ModelForm tracer, plus top-level formset wrappers carrying the main form's bound name.

**Strengths.**
- Root cause confirmed in source: `src/crud_views/lib/conditional/layout.py:29` emits the unprefixed `self.toggle_field`; `toggle.js:17-20` suffix-matches (`name$="-…"`) inside `closest("form")`; `toggle.js:36-39` sets `__cvToggleWired` before resolution, so a missing toggle can never be retried. Plan tasks target each mechanism.
- Formset wrapper gap confirmed: `render_tree.py:195-198` returns the declaration name, consumed by `formsets.html:4-5`; 01-02's `cv_bound_toggle_field` set in `FormSet.init` (which receives the main form at `formsets.py:385-388`) is the right seam.
- A17 remedy matches the cited precedent exactly: `tests/browser/modal-focus.cjs:11-12` resolves `process.env.CV_FOCUS_NODE || runtime.node.path` from the tracked manifest (`git ls-files` confirms `.planning/phases/06-form-button-leaf/06-JS-RUNTIME.json`); `node_modules/jsdom` and `vitest.mjs` exist; `tests/js/helpers/load.js:32-40` shows the shipped-file evaluation pattern the inline script can mirror. The Profile fixture and `ToggleGroup("with_contact", …)` already exist in `tests/test1/test_conditional_layout.py:8-25`.

**Concerns.**
- **MEDIUM (new, A18):** the tracer is collected unconditionally inside `tests/test1`, and 01-01 mandates "missing/unusable Node … must fail pytest … never skip". The manifest path is machine-specific (`06-JS-RUNTIME.json:8`: `/home/alex/.nvm/versions/node/v24.21.0/bin/node`), and CI's Python workflow provisions no Node and runs no `npm ci` (`.github/workflows/tests.yml:24-25` runs the nox `tests`/`examples` sessions; `setup-node`/`npm ci` appear only in `js.yml:14-18`). Under the plan as written, every CI matrix cell and every developer machine without that nvm path (or without `node_modules/jsdom`) turns the whole `pytest tests` run red. No existing pytest test spawns Node (`subprocess` users are `test_pipeline_sources.py`, `test_import_safety.py`, `test_button_data.py`, all Python-only). This is a consequence of the agreed A17 remedy, not a regression of it, but it needs an explicit decision.

**Suggestions.**
- Choose one and write it into 01-01 and 10-01: (a) an explicit opt-in marker/env for the Node tracer, deselected by default in the nox `tests` sessions, with plan 10's evidence checker asserting the tracer case actually ran and passed (so local acceptance still cannot skip it); or (b) extend `tests.yml`/noxfile to provision Node and run `npm ci` before pytest (explicit CI scope). Adding `shutil.which("node")` as a last default helps developers but does not fix CI without jsdom.
- LOW: when resolving "owning form", use `form.elements` so `<input form="id">`-associated checkboxes outside the `<form>` subtree are included; implementation detail only.

**Risk Assessment.** Medium. Product repair is well-grounded; the only open risk is suite portability introduced by the tracer's hard runtime requirement.

## 06.4-02

**Summary.** Field-aware clearing resolver with trusted `Field.disabled` precedence, `_post_clean` pre-application through `save_form_data`, schema-backed persistence matrix (scalar, Boolean, FK, FileField/ImageField reference-only, M2M), and the H1 `_cv_conditional_requires_save` signal consumed by `XFormSet.save`.

**Strengths.**
- Defect confirmed: `group.py:36-37` returns `None` for every field; `group.py:78-84` clears without any disabled check. Django 6.0's `construct_instance` skips omitted-with-default fields (`django/forms/models.py:76-77`), so applying resolved values before `super()._post_clean()` (`models.py:479-496`) is the correct ordering; M2M stays on `save_m2m` (`render_tree.py:234`).
- H1 path confirmed: `render_tree.py:259` gates persistence on `form.has_changed()`; the private signal consumed after validation is the minimal correct change, and untouched extras never reach `_post_clean` because `empty_permitted` short-circuits `full_clean`.
- A15 bound is executable on the real stack: `find .nox .venv -iname PIL` returns nothing; installed Django 4.2.30 / 5.2.18 / 6.0.9 confirmed via dist-info. An `ImageField` without `width_field`/`height_field` never imports PIL on assignment (`update_dimension_fields` early-returns) or on no-upload clean (`FileField.clean` returns `initial`/`False` before `ImageField.to_python`). The only PIL-dependent path is `fields.E210`, and the suite's check invocations are tagged (`test_button_classes_checks.py:325` `tags=["crud_views"]`, `test_guardian_composition.py:112,123` `tags=["crud_views_guardian"]`), so model-field checks never run; pytest-django's `create_test_db` reaches `migrate` through `call_command`, whose default is `skip_checks=True`.

**Concerns.**
- LOW: 02-02 says "keep the existing fixture setup through `call_command('migrate')`", but `tests/test1/conftest.py` contains no explicit migrate call; the effect holds via pytest-django. Wording only.
- LOW: per-field isolated storage requires swapping `field.storage` on the model field (storage is class-bound); the plan's "explicitly isolated storage for each file/image field … restore in teardown" implies this. Fine, just note monkeypatching the field attribute rather than a per-test `storage=` kwarg.

**Suggestions.** None requiring revision.

**Risk Assessment.** Low–medium. The persistence ordering is right; the main execution risk is test-fixture bookkeeping (storage swap, has_changed assertions), all specified.

## 06.4-03

**Summary.** `crud_views.E312` for statically detectable unsupported clearing across main and declared inline form classes, retirement of W320, per-form namespace handling (A02), and runtime `ImproperlyConfigured` for dynamic fields; inherited nonfield/model invariant tests.

**Strengths.**
- Current check surface confirmed: `checks.py:141-149` (`_non_nullable_clears`) only knows null/blank, inspects only `view.form_class` (`checks.py:164-179`), and never descends into `formset.klass.form`. Existing W320 tests at `test_conditional_checks.py:292-298,372-393` will need rewriting, which 03-01 owns.
- E310/E311/W321 retained with existing semantics; IDs E312 unused in registry.

**Concerns.** None.

**Suggestions.** Deduplicate findings by `(form_class, group, field)` since create/update share form classes (the existing `dict.fromkeys` at `checks.py:200-202` is the pattern).

**Risk Assessment.** Low.

## 06.4-04

**Summary.** Mandatory active row-policy gate (`XFormSet._cv_validate_row_policy`) rejecting nonblank edit-only extras and invalid existing-row identities with generic nonform errors before any save, for package and native `BaseInlineFormSet` declarations, with test-local registered HTTP routes (H3).

**Strengths.**
- Seam is right: `formsets.py:88-89` accepts any Django `BaseInlineFormSet`; `render_tree.py:200-203` is the traversal every accepted class passes through; `mixins.py:98-105` evaluates `all_valid()` before `cv_form_valid`'s atomic block (`mixins.py:114-128`).
- D-12 risk confirmed in Django 6.0: `_construct_form` (`models.py:735-755`) binds an instance only when the pk is in the formset queryset; otherwise the form gets a fresh instance, the hidden pk field uses `_default_manager` (`models.py:774,1026-1028`), and the package's `_save_changed_form` (`render_tree.py:223-234`) bypasses Django's `save_existing_objects` guard (`models.py:948`), so a foreign pk in an initial position becomes an INSERT under the current parent. 04-02's "reject generically if it cannot be bound as an authorized existing row" is the correct rule.
- Two-pass `all_valid` (`formsets.py:365-369`) is compatible: errors appended to `_non_form_errors` after the first `is_valid()` persist, because `full_clean` runs once.

**Concerns.** None.

**Suggestions.** State in 04-01 that policy errors are appended only after `instance.is_valid()` has triggered `full_clean` (which resets `_non_form_errors`), and are deduplicated by a private marker so pass two does not double them.

**Risk Assessment.** Low–medium. Security-relevant but well-scoped; fixture construction (native adapter exposing `helper`, `formset`, `parent_form`) is the main effort.

## 06.4-05

**Summary.** Composed disabled ownership (baseline via `MutationObserver` + inactive ancestor set), management-input exception, native visibility, deferred cancellable reset resync, stranded-focus recovery, readyState startup and observer disposal on modal unload.

**Strengths.**
- Defects confirmed: `toggle.js:23-31` writes `el.disabled = !on` unconditionally and omits `button`; `toggle.js:53` only listens to `DOMContentLoaded` (late scripts never initialize); no reset handling exists. `cv:modal:unload` is dispatched while old nodes are attached (`modal.js:93-96`), so observer disposal has a hook.
- Reset timing (macrotask after default reset, re-check `defaultPrevented`) matches the WHATWG order; A04 already incorporated.

**Concerns.** None.

**Suggestions.** `modal.js`'s `cvModalFocus`/`cvModalUsable` are not exported (`modal.js:238-239` exports only the five listed names); the plan correctly keeps a private helper in toggle.js. Keep the usability predicate identical in behavior to `modal.js:46-55` to avoid divergent focus rules.

**Risk Assessment.** Medium (JS state ownership is the most intricate piece), mitigated by the required observer spike test.

## 06.4-06

**Summary.** `cv.initFormsets(root)`, one controller per owning form, exact attribute/name lookups with supported UUID/deep-hyphenated/identical-prefix fixtures (A16), capability-gated stock Add (A11), handler-level edit-only/disabled enforcement, 422 replacement, widget-event counts, submit-cancellation ordering and `reorder_formsets` error aggregation.

**Strengths.**
- A16 fixture repair verified: `formsets.py:294-298` `check_keys` accepts only `^[a-z\-]+$`, so `line-items` is valid and `line.items:detail` is correctly used only as a rejection control.
- Defects confirmed: `control.html:19-22` renders Add unconditionally while `FormSet.edit_only` exists (`formsets.py:111-113`); `formset.js:600-611` loses a child `reorder()` failure (`return false` inside jQuery `each` only breaks the loop, outer returns `true`); `modal.js:227-233` never checks `event.defaultPrevented`; `find_page_form_controls` (`formset.js:542-548`) assumes `edit_only:false` page-wide; `formset.js:165` uses an unquoted attribute value.
- Listener order is favorable: formset.js binds on the form element, modal.js on `document`, so honoring `defaultPrevented` in modal.js is sufficient.

**Concerns.** None.

**Suggestions.** None.

**Risk Assessment.** Medium, driven by the controller rewrite under a retained jQuery dependency.

## 06.4-07

**Summary.** Declaration-derived selected-child index in `get_template`, A19 success round trip replacing the characterization, raw wrapper-balance assertions with a negative control, unconditional `render_rows_only` closing predicate (H2).

**Strengths.**
- Both defects confirmed: `formsets.py:513` hardcodes `index=0` while `init` enumerates `child_index` (`formsets.py:181-189`) and the coordinate validator already computes the declared position (`formsets.py:446`); `formset.html:56` tests `end_at_rows`, which `XFormSet` (`render_tree.py:93-102`) does not define, so rows-only fragments always emit stray closing wrappers. The stale docstring is at `formsets.py:417-418`.
- Characterization test confirmed at `tests/test1/test_fragment_authorization.py:1154-1204`; after the fix, `formset.js:156-160`'s anchored regex already parses `{pa}-0-0-{ba}-1` with pk 34 / index 1, so the browser side needs no change for the row lookup.

**Concerns.** None.

**Suggestions.** Implement the raw token stack with `html.parser.HTMLParser` (void/comment handling is built in) rather than a hand-rolled tokenizer.

**Risk Assessment.** Low.

## 06.4-08

**Summary.** Disposable loopback Django fixture (port 8144), cached Playwright/Chromium runner with overrides and provenance, stock and native-theme cases, required assertion table (H1/H2/A04/A10/A15), tampered POST and zero-save checks.

**Strengths.**
- Analog verified: `17-evidence/server.py:14-37` configures settings via `tests.test1.conftest.pytest_configure`, calls `call_command("migrate", run_syncdb=True)` (checks skipped by default) and serves through `StaticFilesHandler(get_wsgi_application())`, so the ImageField fixture starts without Pillow. `modal-focus.cjs:76-100` supplies the port probe, runtime assertions and owned child lifecycle; the native dialog shell/adapter is extracted from `docs/reference/javascript.md` "## A non-Bootstrap modal" (line 140), which exists.
- Required-assertion table is explicit per theme, and the tracer-only record is labelled non-acceptable.

**Concerns.**
- LOW: "private BrowserMemo" must be registered under an installed app label (e.g. `Meta.app_label = "app"`) and created with `schema_editor.create_model` since `run_syncdb` only creates tables for models known at migrate time. Executable, but 08-01 should say which mechanism.

**Suggestions.** Record `node_modules/jsdom` is not needed here (Playwright only), to keep plan 08's runtime set distinct from plan 01's.

**Risk Assessment.** Medium, proportional to the breadth of real-browser cases; infrastructure is proven.

## 06.4-09

**Summary.** Executable docs recipes, clearing matrix with the reference-only image boundary, projection documentation (A13 grammar vs row identity), example-model comment fix (A08), paired Breaking/migration entries, PUBLIC-SURFACE inventory.

**Strengths.**
- Targets confirmed: `examples/bootstrap5/conditional/models.py:7` still promises "clears its fields to None … (see crud_views.W320)"; `docs/reference/formsets.md:205-209` carries the second-child limitation; `docs/reference/conditional.md:31,142` carry the null/blank-only and W320 claims. `XFormSet.data["pk"]` is the grammar (`render_tree.py:188`) and `XForm.data["pk"]` is the enum spelling (`render_tree.py:67`), as A13 requires. `tests/test1/test_delete_migration_docs.py` and `.venv/bin/mkdocs` exist.

**Concerns.**
- LOW: the "old 'never validated' wording" quoted in 09-01 is actually "Validation is skipped entirely for the group" (`conditional.md:31`); the executor should target that sentence.

**Suggestions.** None.

**Risk Assessment.** Low.

## 06.4-10

**Summary.** Stdlib evidence runner over three cached Django series, full JS, strict docs, touched-file Ruff, sequential conditional then modal-focus browser runs, source-hash manifest, checker corruption controls, A19 reconciliation and acceptance.

**Strengths.**
- All referenced environments and inputs exist: `.nox/crispy_floor-3-12-django-4-2`, `.nox/tests-3-12-django-5-2`, `.nox/crispy_floor-3-12-django-6-0`, `.venv/bin/ruff`, `06.3-REGRESSION-GATE.md`, `06.3-MATRIX.md`, `06.2-ACCEPTANCE.md`.
- Correctly limits claims to executed series and keeps the descriptor-less prohibition flagged.

**Concerns.**
- MEDIUM (shared with A18): "full tests in these three environments" is local-only; if plan 01's tracer stays unconditional, CI's `tests.yml` matrix cannot reproduce this gate. Plan 10 should record how the tracer is gated and assert it ran.

**Suggestions.** Have `--check` verify the tracer case ID from `test_conditional_layout.py` appears as passed in each series' JUnit/pytest output, which also closes A18 option (a) without permitting silent skips.

**Risk Assessment.** Low–medium.

## Prior-item closure ledger

| Item | Disposition | Evidence |
|---|---|---|
| H1 | CLOSED, no regression | `render_tree.py:259` has_changed gate; 02-02/04-01/08/10 unchanged remedies |
| H2 | CLOSED, no regression | `formset.html:56` `end_at_rows` absent from `render_tree.py:93-102`; 07-02 unchanged |
| H3 | CLOSED, no regression | `formsets.py:88-89` native acceptance; 04-01 routes/adapter unchanged |
| A01–A14 | Preserved | No regression found in the cited plan lines; A12 superseded by A16 as recorded |
| A15 | CLOSED | No PIL in any env; reference-only ImageField never imports PIL; E210 unreachable under tagged checks and `call_command` migrate; propagated to 02/08/09 |
| A16 | CLOSED | `check_keys` regex confirms valid/invalid fixtures; 06-01 uses supported keys and a rejection control |
| A17 | CLOSED as specified | Precedence matches `modal-focus.cjs:12`; manifest tracked; helper inline; clear failure. Consequence raised separately as A18 |

## Unresolved concerns (deduplicated)

| ID | Severity | Plans | Change still needed |
|---|---|---|---|
| A18 | MEDIUM | 01, 10 | The unconditional Node/jsdom tracer in `tests/test1` fails `pytest tests` on CI runners and machines without the manifest path or `node_modules`; choose an explicit opt-in marker enforced by plan 10's checker, or provision Node + `npm ci` in `tests.yml`/noxfile. Never-skip semantics can be preserved either way. |

LOW notes (no revision required): plan 02 migrate wording; plan 08 BrowserMemo table-creation mechanism; plan 09 doc sentence quote.

`CYCLE_SUMMARY: current_high=0 current_actionable=1`
