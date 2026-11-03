## 06.4-01

### Summary
Plan `06.4-01` (`06.4-01-PLAN.md:1-186`) establishes exact bound-name identity for conditional field groups (`ToggleGroup`) and top-level conditional formset wrappers (`XFormSet.cv_toggle_field`), introduces `cv.initConditional(root = document)` with owning-form checkbox matching and ambiguity isolation, and adds an end-to-end rendered HTML -> Node/jsdom -> `FormData` -> Django `ModelForm` save tracer in `tests/test1/test_conditional_layout.py`.

### Strengths
- **End-to-end bound-name trace**: `06.4-01-PLAN.md:113` traces `ToggleGroup.render` in `src/crud_views/lib/conditional/layout.py:25-35` (changing `"cv_toggle_field": self.toggle_field` at line 29 to `form.add_prefix(self.toggle_field)`) through `src/crud_views/templates/crud_views/conditional/toggle_group.html:4,9` (`cv-data-toggle-field="{{ cv_toggle_field }}"`) and `src/crud_views/static/crud_views/js/toggle.js:15-51` (replacing the suffix selector `input[type="checkbox"][name$="-' + escaped + '"]` at lines 18-20 with exact `name` equality within `group.closest("form")`).
- **Top-level conditional formset wrapper binding**: `06.4-01-PLAN.md:128-129` threads the main form's `form.add_prefix(toggle.field_name())` from `FormSet.init` (`src/crud_views/lib/formsets/formsets.py:162-169`) into private `XFormSet.cv_bound_toggle_field` and `XFormSet.cv_toggle_field` (`src/crud_views/lib/formsets/render_tree.py:93-103,195-198`), consumed by `src/crud_views/templates/crud_views/formsets/formsets.html:4-5`.
- **Closure of prior A17 (inline Node resolver and ownership)**: `06.4-01-PLAN.md:84,111-114` places private `_resolve_tracer_node` and the inline Node/jsdom script directly inside `tests/test1/test_conditional_layout.py` (`tests/test1/test_conditional_layout.py:1-90`), honoring `CV_FOCUS_NODE` first and falling back to `node.path` in `.planning/phases/06-form-button-leaf/06-JS-RUNTIME.json:6-8` (matching `tests/browser/modal-focus.cjs:11-12`), and failing pytest explicitly on missing/invalid runtimes or `jsdom` load errors without skipping.

### Concerns
None.

### Suggestions
- None. Existing `tests/js/toggle.test.js:67-71` (`finds the checkbox by formset-prefixed suffix name`) is already owned by `06.4-01-PLAN.md:110` for replacement with exact bound-name assertions.

### Risk Assessment
**LOW** — Scope and ownership are self-contained; A17 is fully resolved.

---

## 06.4-02

### Summary
Plan `06.4-02` (`06.4-02-PLAN.md:1-181`) replaces the universal `None` clearing default in `src/crud_views/lib/conditional/group.py:36-37,62-85` with field-aware persistence (`resolve_conditional_empty_value`), applies resolved scalar/file values before `ModelForm._post_clean` constructs and validates the model instance, preserves server-side `Field.disabled=True` fields ahead of error suppression and clearing, and propagates a private `_cv_conditional_requires_save` flag into `XFormSet.save` (`src/crud_views/lib/formsets/render_tree.py:256-260`).

### Strengths
- **Pre-validation model construction**: `06.4-02-PLAN.md:97` hooks `ConditionalGroupFormMixin._post_clean` in `src/crud_views/lib/conditional/group.py:40-85` so resolved scalar/file values are written via `model_field.save_form_data` before `super()._post_clean()` runs `construct_instance` and `instance.full_clean()`, preventing omitted widgets with model `default=` from retaining stale or default values.
- **Closure of prior H1 and A01**: `06.4-02-PLAN.md:97,110-112` computes `_cv_conditional_requires_save` from effective pre-mutation differences on persisted rows (`not form.instance._state.adding`) and consumes it in `XFormSet.save` (`src/crud_views/lib/formsets/render_tree.py:259-260`) when `form.has_changed()` is `False`, while isolating file/image test storage to `tmp_path` (`override_settings(MEDIA_ROOT=...)`) and spying on `storage.delete` during production save outside test teardown.
- **Closure of prior A15 (runnable ImageField contract without Pillow)**: `06.4-02-PLAN.md:79,110-112,161` keeps real `ImageField` coverage on `ConditionalPersistenceRecord` (`tests/test1/app/models.py:202-218`) for stored-reference clearing (`False`), explicit `None` retention, `Field.disabled=True` preservation, and unchanged-inline `XFormSet.save` clearing by seeding storage directly without `width_field`/`height_field` or uploaded image bytes (avoiding `PIL` import in `forms.ImageField.to_python` and keeping `call_command('migrate')`'s default `skip_checks=True`), while proving off-group upload discard with real `SimpleUploadedFile` bytes on `FileField`.

### Concerns
None.

### Suggestions
- None.

### Risk Assessment
**LOW** — H1, A01, and A15 are cleanly addressed with concrete mechanisms that run in the installed no-Pillow environments.

---

## 06.4-03

### Summary
Plan `06.4-03` (`06.4-03-PLAN.md:1-157`) shares `resolve_conditional_empty_value` between `src/crud_views/checks.py` and `src/crud_views/lib/conditional/group.py`, introduces system check `crud_views.E312` for statically detectable unsupported automatic clearing across main and inline form classes, retires obsolete `crud_views.W320`, and enforces runtime `ImproperlyConfigured` before save for dynamic fields.

### Strengths
- **Per-form-class namespace isolation (A02)**: `06.4-03-PLAN.md:86` extends `_collect_view_findings` and `_walk_formset` in `src/crud_views/checks.py:130-180` to compute `base_fields`, declared toggles, and `group_injected` toggles independently for each main and inline form class rather than leaking the main form's field namespace into inline form checks.
- **Consistent static and runtime configuration errors**: `06.4-03-PLAN.md:86,100` replaces `_non_nullable_clears` / `crud_views.W320` (`src/crud_views/checks.py:79-86,141-150` and `tests/test1/test_conditional_checks.py:292-299,362-393`) with `crud_views.E312` at startup and `ImproperlyConfigured` at runtime before any save, while preserving `E310`, `E311`, and `W321`.

### Concerns
None.

### Suggestions
- None.

### Risk Assessment
**LOW** — Static traversal and runtime validation share a single resolver and preserve existing check semantics.

---

## 06.4-04

### Summary
Plan `06.4-04` (`06.4-04-PLAN.md:1-164`) enforces mandatory active formset row-policy validation (`XFormSet._cv_validate_row_policy`) in `src/crud_views/lib/formsets/render_tree.py` and `src/crud_views/lib/formsets/formsets.py` before `cv_form_valid` saves any model or formset, rejecting nonblank `edit_only` extras (`cv_additions_not_allowed`) and missing/malformed/unauthorized existing-row IDs (`cv_invalid_row`) across both package `InlineFormSet` and custom `BaseInlineFormSet` subclasses.

### Strengths
- **Order-independent pre-save enforcement**: `06.4-04-PLAN.md:90,104` places `_cv_validate_row_policy` inside the active `XFormSet.is_valid` traversal (`src/crud_views/lib/formsets/render_tree.py:200-203`) invoked by both passes of `FormSets.all_valid()` (`src/crud_views/lib/formsets/formsets.py:354-370`), ensuring `FormSetMixinBase.cv_form_is_valid` (`src/crud_views/lib/formsets/mixins.py:80-105`) rejects invalid submissions before `cv_form_valid` (`mixins.py:107-129`) enters its atomic write block.
- **Closure of prior H3 and preservation of H1**: `06.4-04-PLAN.md:90-91` builds isolated registered `policy_routes` in `tests/test1/test_formsets_policy.py` (modeled on `tests/test1/test_fragment_authorization.py`) and defines `PolicyNativeInlineFormSet` as a direct `BaseInlineFormSet` subclass accepting `formset` and `parent_form` (`src/crud_views/lib/formsets/formsets.py:148-160`) without inheriting `InlineFormSet.clean` (`src/crud_views/lib/formsets/inline_formset.py:16-44,111-118`), while preserving `06.4-02`'s `_cv_conditional_requires_save` logic in `render_tree.py`.
- **Queryset-scoped identity verification**: `06.4-04-PLAN.md:104` checks submitted existing-row PKs via model PK field conversion against `instance.get_queryset()` on its routed DB alias and distinguishes unsaved default-UUID rows via `instance._state.adding` (`src/crud_views/lib/formsets/formsets.py:28-37`).

### Concerns
None.

### Suggestions
- None.

### Risk Assessment
**LOW** — H1 and H3 are closed and verified by both direct tree tests and real HTTP route fixtures.

---

## 06.4-05

### Summary
Plan `06.4-05` (`06.4-05-PLAN.md:1-150`) implements composed per-control disabled ownership (independent baseline `OR` any inactive bound ancestor group), native action button disabling, form-scoped cancellable native `reset` resynchronization, and stranded-focus recovery in `src/crud_views/static/crud_views/js/toggle.js` and `tests/js/toggle.test.js`.

### Strengths
- **Mutation-observed baseline ownership**: `06.4-05-PLAN.md:78` replaces unconditional `el.disabled = !on` writes in `src/crud_views/static/crud_views/js/toggle.js:26-31` with a `MutationObserver` (`attributeFilter: ["disabled"], attributeOldValue: true`) that drains pending records before disconnecting around synchronous library writes, accurately tracking external `true`/`false` mutations even while a control is already conditionally disabled and including `button` controls while exempting `MGMT_FIELD` (`toggle.js:13`).
- **Closure of prior A04 (macrotask native reset)**: `06.4-05-PLAN.md:92` schedules form-scoped reset resynchronization in a macrotask (`setTimeout(..., 0)`) after native control resetting completes and checks `event.defaultPrevented` at the deferred point so later `reset` listeners that call `preventDefault()` are respected.
- **Modal-compatible stranded-focus recovery**: `06.4-05-PLAN.md:92` moves focus only when a newly hidden group contains `document.activeElement` (to controlling checkbox -> nearest usable ancestor toggle -> visible owning `<form>` with temporary `tabindex="-1"`), preserving `cvModalInject` / `cvModalFocus` in `src/crud_views/static/crud_views/js/modal.js:57-69,90-103`.

### Concerns
None.

### Suggestions
- None.

### Risk Assessment
**LOW** — Ownership composition, reset timing, and focus recovery are well-bounded and non-invasive to modal focus.

---

## 06.4-06

### Summary
Plan `06.4-06` (`06.4-06-PLAN.md:1-187`) introduces `cv.initFormsets(root = document)` with one scoped controller per owning `<form>` in `src/crud_views/static/crud_views/js/formset.js`, hides the stock Add button when `formset.edit_only` is true in `src/crud_views/templates/crud_views/formsets/control.html`, replaces raw prefix CSS selector interpolation with exact DOM attribute/name equality within the owning form, and coordinates formset submit reordering with `src/crud_views/static/crud_views/js/modal.js`.

### Strengths
- **Closure of prior A11 (Django-rendered control template tests)**: `06.4-06-PLAN.md:99,102` guards the stock Add button in `src/crud_views/templates/crud_views/formsets/control.html:18-22` with `{% if not formset.edit_only %}` and verifies the shipped template via Django rendering in `tests/test1/test_formsets_controls.py`.
- **Closure of prior A12 and A16 (exact attribute/name equality with valid declaration keys)**: `06.4-06-PLAN.md:98-100,166` eliminates unescaped prefix interpolation in `src/crud_views/static/crud_views/js/formset.js:130,165,173,180,230,280,306,347,371,439,511,600` using fixed structural queries under the owning `<form>` plus exact DOM attribute/name comparison, and replaces the invalid `line.items:detail` fixture with keys valid under `FormSets.check_keys` (`src/crud_views/lib/formsets/formsets.py:294-298`, e.g., `line-items`), UUID/deep hyphenated prefixes, two identical-prefix forms, and near-match decoys, while asserting in `tests/test1/test_formsets_controls.py` that `FormSets.check_keys` still rejects `line.items:detail`.
- **Submit reorder and modal cancellation ordering**: `06.4-06-PLAN.md:115` fixes `reorder_formsets()` (`src/crud_views/static/crud_views/js/formset.js:597-611`, where returning `false` from `.each()` was previously swallowed and `return true` always ran at line 610) and updates `src/crud_views/static/crud_views/js/modal.js:227-233` to respect `event.defaultPrevented` after form-level submit reordering.

### Concerns
None.

### Suggestions
- None.

### Risk Assessment
**LOW** — A11, A12, and A16 are closed without expanding the formset key grammar.

---

## 06.4-07

### Summary
Plan `06.4-07` (`06.4-07-PLAN.md:1-159`) repairs A19 non-first sibling fragment indexing in `FormSets.get_template` (`src/crud_views/lib/formsets/formsets.py:508-521`), fixes the mismatched closing wrapper condition in `src/crud_views/templates/crud_views/formsets/formset.html:56`, and replaces the mismatch characterization in `tests/test1/test_fragment_authorization.py:1154-1204` with full rendered-prefix -> fragment -> management-total -> POST -> DB round-trip and raw wrapper-balance assertions.

### Strengths
- **Declaration-derived sibling index**: `06.4-07-PLAN.md:86` updates `FormSets.get_template` (`src/crud_views/lib/formsets/formsets.py:508-514`) to pass the child's declared index in `parent.children` (matching `FormSet.init` at `formsets.py:181-189` and `_cv_validate_fragment_coordinates` at `formsets.py:446`) instead of `index=0`, and updates the docstring note at `formsets.py:417-418`.
- **Closure of prior H2 (unconditional closing-wrapper repair and pre-parser balance check)**: `06.4-07-PLAN.md:100` changes `{% if not x_formset.end_at_rows %}` in `src/crud_views/templates/crud_views/formsets/formset.html:56` to `{% if not x_formset.render_rows_only %}` (matching line 4) and verifies raw rendered HTML with a strict non-void wrapper tag stack and a stray-close negative control before DOM parsing.

### Concerns
None.

### Suggestions
- None.

### Risk Assessment
**LOW** — Direct two-line production fix backed by raw HTML token-stack and full round-trip persistence tests.

---

## 06.4-08

### Summary
Plan `06.4-08` (`06.4-08-PLAN.md:1-209`) delivers the real Chromium and disposable loopback Django HTTP server acceptance suite (`tests/browser/conditional-formsets.cjs` and `tests/browser/conditional_formsets_server.py`) plus minimal non-Bootstrap templates (`tests/browser/templates/conditional_formsets/native_*.html`), verifying stock and native theme lifecycles and writing `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/08-browser-results.json`.

### Strengths
- **Closure of prior H1, H2, A04, A06, A07, A10**: `06.4-08-PLAN.md:99-112,119,133` mandates named per-theme (`stock` and `native`) cases and assertion IDs in `--check-evidence` for `inline-file-clear-unchanged`, `fragment-raw-balance`, `native-reset-user-default`, `native-reset-user-cancelled`, and `disabled-same-value-ownership`, while honoring `CV_FOCUS_NODE`/`CV_FOCUS_PYTHON`/`CV_FOCUS_PLAYWRIGHT`/`CV_FOCUS_CHROMIUM` (`tests/browser/modal-focus.cjs:11-17,81-86`) and binding `CV_CONDITIONAL_PORT` (default `8144`, rejecting `8143`).
- **Closure of prior A15 in browser fixture**: `06.4-08-PLAN.md:81,107,119,133,189` seeds `ImageField` references on `BrowserConditionalRecord` without uploaded image bytes or dimension hooks (`call_command('migrate')` with default `skip_checks=True`), while adding a separate multipart `FileField` upload while the group is off and requiring `file-upload-received`, `off-file-upload-discarded`, and `uploaded-file-not-stored` in both `stock` and `native` themes.

### Concerns
None.

### Suggestions
- None.

### Risk Assessment
**LOW** — Browser harness follows the proven `tests/browser/modal-focus.cjs` architecture and enforces all review regression assertions without requiring Pillow.

---

## 06.4-09

### Summary
Plan `06.4-09` (`06.4-09-PLAN.md:1-191`) updates `docs/reference/conditional.md`, `docs/reference/formsets.md`, `docs/reference/javascript.md`, `examples/bootstrap5/conditional/models.py`, `CHANGELOG.md`, `docs/migrating-1.0.md`, and `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-PUBLIC-SURFACE.md`, and adds executable documentation tests in `tests/test1/test_conditional_migration_docs.py`.

### Strengths
- **Closure of prior A08 and A13**: `06.4-09-PLAN.md:102` updates the stale `null=True` / `W320` comment in `examples/bootstrap5/conditional/models.py:8-12` to match the field-aware clearing matrix and `E312`, and explicitly distinguishes `XFormSet.data.pk` (`self.pk.value` regex grammar at `src/crud_views/lib/formsets/render_tree.py:188`) from `XForm.data.pk` (`str(self.parent.pk)` enum string at `render_tree.py:67`) and the actual row/parent `pk` in fragment requests (`docs/reference/formsets.md:170-200`), testing both integer and UUID runtime projections.
- **Closure of prior A15 in published docs**: `06.4-09-PLAN.md:101-103,170` keeps `ImageField` in the supported reference-clearing matrix (`False` default, explicit `None` no-change, server-disabled precedence, stored-file retention) while explicitly documenting the reference-only test boundary, the real `FileField` multipart upload-discard evidence, and Django's existing application-level Pillow requirement for decoding uploaded images.
- **Paired Breaking/migration and Phase 7 handoff**: `06.4-09-PLAN.md:118` pairs every `### Breaking` entry in `CHANGELOG.md` with `docs/migrating-1.0.md` and inventories public names (`cv.initConditional`, `cv.initFormsets`, `crud_views.E312`, template projection) for Phase 7 without promoting internal `XForm`/`XFormSet` classes.

### Concerns
None.

### Suggestions
- None.

### Risk Assessment
**LOW** — Documentation claims are bounded to tested behavior and verified by `test_conditional_migration_docs.py` and `.venv/bin/mkdocs build --strict`.

---

## 06.4-10

### Summary
Plan `06.4-10` (`06.4-10-PLAN.md:1-171`) implements `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/10-evidence/run.py` to execute and verify the three cached Django series (`4.2`, `5.2`, `6.0`), Vitest, strict MkDocs, Ruff, and sequential browser acceptance (`conditional-formsets.cjs` on port `8144` then `modal-focus.cjs` on port `8143`), writing `10-evidence/results.json`, `10-evidence/source-manifest.json`, `06.4-MATRIX.md`, `06.4-VALIDATION.md`, `06.4-ACCEPTANCE.md`, and the scoped A19 update in `06.2-ACCEPTANCE.md`.

### Strengths
- **Complete regression and corruption checks**: `06.4-10-PLAN.md:96` requires `run.py --check` to verify every `stock` and `native` case and assertion ID from `06.4-08-PLAN.md:105-111` (automatically including the A15 `file-upload-received`, `off-file-upload-discarded`, and `uploaded-file-not-stored` assertion IDs alongside H1, H2, A04, and A10), and tests `--check` against deliberate corruptions of exit codes, case lists, required assertions, and source hashes.
- **Sequential browser scheduling and honest scope accounting**: `06.4-10-PLAN.md:96,111` runs the two browser harnesses sequentially with process-exit verification (A07), keeps Python 3.13–3.15 unclaimed unless executed, preserves the descriptor-less prohibition status from `06.4-02-PLAN.md:48` as `flagged-unverified` until canonical verification, and reconciles only the A19 handoff in `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-ACCEPTANCE.md`.

### Concerns
None.

### Suggestions
- None.

### Risk Assessment
**LOW** — Final evidence gate is deterministic, self-auditing, and tightly bound to checkout source hashes.

---

## Cross-Plan Summary

All ten revised Phase 6.4 plans at commit `9de2644` form a complete, source-grounded, and executable 8-wave dependency graph with disjoint same-wave file ownership. Commit `9de2644` cleanly closes all three remaining items from Cycle 2 (`A15`, `A16`, `A17`) while preserving all previously closed/incorporated items (`H1`–`H3`, `A01`–`A14`) without regression.

### Explicit Prior-Item Closure Ledger

| Prior Item | Severity | Status at `9de2644` | Verification & Plan/Source Evidence |
|---|---|---|---|
| **H1** | HIGH | **CLOSED** (preserved) | `06.4-02-PLAN.md:97,110-112`, `06.4-04-PLAN.md:90,107`, `06.4-08-PLAN.md:107,119,133`, `06.4-10-PLAN.md:96` — `_cv_conditional_requires_save` augments `XFormSet.save` (`src/crud_views/lib/formsets/render_tree.py:259-260`) when `form.has_changed()` is `False` on persisted rows. |
| **H2** | HIGH | **CLOSED** (preserved) | `06.4-07-PLAN.md:86,100`, `06.4-08-PLAN.md:108,119`, `06.4-10-PLAN.md:96` — `src/crud_views/templates/crud_views/formsets/formset.html:56` matches `not x_formset.render_rows_only` (line 4), verified by raw pre-parser tag-stack balance and a stray-close negative control. |
| **H3** | HIGH | **CLOSED** (preserved) | `06.4-04-PLAN.md:70-71,90-91` — `tests/test1/test_formsets_policy.py` registers isolated create/update routes (`policy_routes`) and `PolicyNativeInlineFormSet` accepting `formset`/`parent_form` kwargs (`src/crud_views/lib/formsets/formsets.py:148-160`). |
| **A01** | MEDIUM | **CLOSED** (preserved) | `06.4-02-PLAN.md:111` — File/image test storage isolated to `tmp_path` (`override_settings(MEDIA_ROOT=...)`) with `storage.delete` spy active during production save and teardown outside the spy window. |
| **A02** | MEDIUM | **CLOSED** (preserved) | `06.4-03-PLAN.md:86` — `src/crud_views/checks.py:130-180` computes `base_fields`, declared toggles, and `group_injected` toggles per main/inline form class without cross-form namespace leakage. |
| **A03** | MEDIUM | **CLOSED** (preserved) | Incorporated in Cycle 1 (`06.4-02-PLAN.md:97`, `06.4-03-PLAN.md:86`) — shared `resolve_conditional_empty_value` across runtime and static checks. |
| **A04** | MEDIUM | **CLOSED** (preserved) | `06.4-05-PLAN.md:92`, `06.4-08-PLAN.md:109-110,133`, `06.4-10-PLAN.md:96` — Macrotask (`setTimeout(..., 0)`) post-reset resynchronization checking `event.defaultPrevented`, verified by real click/keyboard reset activation and later-listener cancellation in Chromium. |
| **A05** | MEDIUM | **CLOSED** (preserved) | Incorporated in Cycle 1 (`06.4-04-PLAN.md:90,104`) — mandatory row-policy gate in `XFormSet.is_valid` covers all `BaseInlineFormSet` subclasses and DELETE/nested-only extras. |
| **A06** | MEDIUM | **CLOSED** (preserved) | `06.4-08-PLAN.md:83,119`, `06.4-10-PLAN.md:96` — Honors `CV_FOCUS_NODE`, `CV_FOCUS_PYTHON`, `CV_FOCUS_PLAYWRIGHT`, and `CV_FOCUS_CHROMIUM` with recorded provenance and explicit failure on invalid overrides. |
| **A07** | MEDIUM | **CLOSED** (preserved) | `06.4-08-PLAN.md:83,119`, `06.4-10-PLAN.md:96` — Separate `CV_CONDITIONAL_PORT` (default `8144`, rejecting `8143`), occupied-port refusal, owned-child cleanup, and sequential execution in `10-evidence/run.py`. |
| **A08** | LOW | **CLOSED** (preserved) | `06.4-09-PLAN.md:30-31,102` — Updates stale `null=True` / `W320` commentary in `examples/bootstrap5/conditional/models.py:8-12` and asserts consistency in `test_conditional_migration_docs.py`. |
| **A09** | LOW | **CLOSED** (preserved) | Incorporated in Cycle 1 (`06.4-01-PLAN.md:128-129`) — top-level conditional formset wrappers bind to the main form's prefixed toggle name. |
| **A10** | MEDIUM | **CLOSED** (preserved) | `06.4-05-PLAN.md:78`, `06.4-08-PLAN.md:111,133`, `06.4-10-PLAN.md:96` — Explicit same-value external `disabled = true` while conditionally disabled and external `disabled = false` while inactive verified in Vitest and both Chromium themes. |
| **A11** | MEDIUM | **CLOSED** (preserved) | `06.4-06-PLAN.md:29-30,99,102` — `tests/test1/test_formsets_controls.py` renders shipped `src/crud_views/templates/crud_views/formsets/control.html` through Django for `edit_only=True/False`. |
| **A12** | LOW | **CLOSED** (preserved) | `06.4-06-PLAN.md:99` — Replaces raw prefix CSS selector interpolation in `src/crud_views/static/crud_views/js/formset.js` with owning-form structural queries and exact DOM attribute/name equality. |
| **A13** | MEDIUM | **CLOSED** (preserved) | `06.4-09-PLAN.md:102` — Explicitly documents and tests `XFormSet.data.pk` regex grammar (`src/crud_views/lib/formsets/render_tree.py:188`) vs `XForm.data.pk` enum string (`render_tree.py:67`) vs fragment request `pk`. |
| **A14** | LOW | **CLOSED** (preserved) | Incorporated in Cycle 1 (`06.4-10-PLAN.md:111`, `06.4-VALIDATION.md:107-109`) — descriptor-less prohibition in `06.4-02-PLAN.md:48` remains `flagged-unverified` until canonical verifier enforcement. |
| **A15** | MEDIUM | **CLOSED** (signed off) | `06.4-02-PLAN.md:79,110-112,161`, `06.4-08-PLAN.md:81,107,119,133,189`, `06.4-09-PLAN.md:101-103,170`, `06.4-10-PLAN.md:96` — Bounds `ImageField` tests to stored-reference semantics without `width_field`/`height_field` or uploaded image bytes (using `call_command('migrate')` default `skip_checks=True` and no `PIL` import or skip), proves off-group upload discard with real `FileField` multipart bytes (`file-upload-received`, `off-file-upload-discarded`, `uploaded-file-not-stored`), and documents the boundary accurately. |
| **A16** | MEDIUM | **CLOSED** (signed off) | `06.4-06-PLAN.md:98-100,107,166` — Replaces unsupported `line.items:detail` fixture with keys valid under `FormSets.check_keys` (`src/crud_views/lib/formsets/formsets.py:294-298`), UUID/deep hyphenated prefixes, two identical-prefix forms, and near-match decoys, while asserting in `tests/test1/test_formsets_controls.py` that `FormSets.check_keys` rejects `line.items:detail`. |
| **A17** | LOW | **CLOSED** (signed off) | `06.4-01-PLAN.md:84,111-114,121,166` — Owns private `_resolve_tracer_node` and inline Node/jsdom script in `tests/test1/test_conditional_layout.py`, resolving `CV_FOCUS_NODE` then `.planning/phases/06-form-button-leaf/06-JS-RUNTIME.json:6-8` (`tests/browser/modal-focus.cjs:11-12`) and failing explicitly on missing/invalid runtimes without skipping. |

### Deduplicated Unresolved Concerns

None (`current_high=0`, `current_actionable=0`).
