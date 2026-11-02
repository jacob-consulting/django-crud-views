## 06.4-01

### Summary
Establishes exact bound checkbox identity from server rendering through client lookup in `src/crud_views/lib/conditional/layout.py:25-35`, `src/crud_views/templates/crud_views/conditional/toggle_group.html:3-12`, `src/crud_views/static/crud_views/js/toggle.js:15-51`, and top-level conditional formset wrappers in `src/crud_views/lib/formsets/formsets.py:162-170`, `src/crud_views/lib/formsets/render_tree.py:195-198`, and `src/crud_views/templates/crud_views/formsets/formsets.html:3-11` (`.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-01-PLAN.md:108-141`). Revision `83c4f35` gates the Node/jsdom tracer test collection on `CV_CONDITIONAL_TRACER=1` so ordinary Python test runs remain independent of Node/npm while phase acceptance enforces enabled execution (`06.4-01-PLAN.md:29,113-126,180-188`).

### Strengths
- **Source-grounded bound identity**: Replaces unprefixed `self.toggle_field` emission in `src/crud_views/lib/conditional/layout.py:29` and `conditional.toggle.field_name()` in `src/crud_views/lib/formsets/render_tree.py:196-198` with `form.add_prefix(...)`, and replaces suffix selector matching in `src/crud_views/static/crud_views/js/toggle.js:18-20` with exact `name` equality among checkboxes in the nearest owning `form` (`06.4-01-PLAN.md:114,134`).
- **Ambiguity isolation and retryability**: Replaces premature `group.__cvToggleWired = true` before lookup (`src/crud_views/static/crud_views/js/toggle.js:36-44`) with private binding state that leaves unresolved groups retryable via `cv.initConditional(root = document)` and isolates duplicate-name warnings without altering local state or bypassing bound ancestor disabling (`06.4-01-PLAN.md:114`).
- **Complete closure of A17 and A18**: Task `01-01` keeps `_resolve_tracer_node` and the inline Node/jsdom script inside `tests/test1/test_conditional_layout.py:1-90` (`06.4-01-PLAN.md:85,114`), sets `test_tracer_rendered_conditional_round_trip.__test__` strictly from `CV_CONDITIONAL_TRACER=1`, performs zero manifest/runtime work at import time, verifies both the enabled exact-node tracer route and the `env -u CV_CONDITIONAL_TRACER -u CV_FOCUS_NODE PATH=` disabled route (`06.4-01-PLAN.md:116-122`), and records `tracer_node_path`, `tracer_node_version`, and `tracer_jsdom_version` via `record_property` for Plan 10's JUnit gate.

### Concerns
None. Prior A17 and A18 are fully resolved.

### Suggestions
None.

### Risk Assessment
**Low**: The `__test__` collection boundary cleanly decouples ordinary Python CI (`.github/workflows/tests.yml:18-25`, `noxfile.py:13-19`) from machine-specific Node paths in `.planning/phases/06-form-button-leaf/06-JS-RUNTIME.json:7` while preserving hard runtime failures once enabled.

---

## 06.4-02

### Summary
Repairs inactive conditional field persistence in `src/crud_views/lib/conditional/group.py:36-85` and existing-row inline save gating in `src/crud_views/lib/formsets/render_tree.py:256-260`, backed by schema-backed persistence tests in `tests/test1/test_conditional_persistence.py` and `tests/test1/app/models.py:202-218` (`.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-02-PLAN.md:92-119`).

### Strengths
- **Pre-validation model construction**: Applies resolved inactive scalar/file values via model field `save_form_data` in `ConditionalGroupFormMixin._post_clean` before inherited `ModelForm._post_clean` runs, preventing Django's `construct_instance` from retaining pre-existing or default values when widgets are omitted (`src/crud_views/lib/conditional/group.py:62-84`; `06.4-02-PLAN.md:97`).
- **Trusted server-disabled precedence**: Preserves fields where server-side `Field.disabled` is true before error suppression (`self.errors.pop` at `src/crud_views/lib/conditional/group.py:83`) and before explicit `empty_values` overrides (`06.4-02-PLAN.md:97,111`).
- **Preserved H1, A01, and A15 closures**: Propagates private `_cv_conditional_requires_save` into `XFormSet.save` (`src/crud_views/lib/formsets/render_tree.py:259`) so existing persisted rows with unchanged off toggles still persist cleared scalar/file/image/relation values without inserting untouched blank extras; isolates temporary media storage outside the `storage.delete` spy; and bounds `ImageField` tests to stored references without Pillow while proving upload discard with real `SimpleUploadedFile` bytes on `FileField` (`06.4-02-PLAN.md:79,97,111,143-166`).

### Concerns
None. Prior H1, A01, and A15 remain closed with no regression.

### Suggestions
None.

### Risk Assessment
**Medium**: Ordering `_cv_conditional_requires_save` computation before `_post_clean` mutates `form.instance` and scoping `XFormSet.save` strictly to persisted rows (`not form.instance._state.adding`) are critical invariants that the planned tasks specify and test directly (`06.4-02-PLAN.md:97,111`).

---

## 06.4-03

### Summary
Aligns static system checks in `src/crud_views/checks.py:53-204` and runtime validation in `src/crud_views/lib/conditional/group.py:50-85` around the shared `resolve_conditional_empty_value` helper, introducing `crud_views.E312` for unsupported automatic clearing and retiring obsolete `W320` (`src/crud_views/checks.py:79-86,141-161`; `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-03-PLAN.md:81-108`).

### Strengths
- **Per-form namespace isolation (A02)**: Fixes `_collect_view_findings` / `_walk_formset` (`src/crud_views/checks.py:130-179`), which previously only inspected the view's main `form_class`, by traversing all declared inline `FormSet` form classes (including custom `BaseInlineFormSet` subclasses) with their own isolated `base_fields`, declared toggles, and injected `UIFieldToggle` sets (`06.4-03-PLAN.md:86,135-137`).
- **Consistent static and runtime failure mode**: Statically detectable unsupported clearing emits `crud_views.E312` at check time (`06.4-03-PLAN.md:86`), while request-dynamically added unsupported fields raise `ImproperlyConfigured` before `save()` rather than surfacing as user-facing form validation errors (`06.4-03-PLAN.md:100`).
- **Authoritative model/form invariants**: Explicitly verifies that inherited `Form.clean()` non-field errors and `Model.clean()` / uniqueness constraints still invalidate submissions after conditional field-error suppression (`src/crud_views/lib/conditional/group.py:62-84`; `06.4-03-PLAN.md:100`).

### Concerns
None. Prior A02 remains closed with no regression.

### Suggestions
None.

### Risk Assessment
**Low**: Reusing the resolver from Plan 02 in `src/crud_views/checks.py` without instantiating request-dependent forms at startup keeps system checks fast and deterministic.

---

## 06.4-04

### Summary
Adds mandatory active-formset row-policy validation (`XFormSet._cv_validate_row_policy`) in `src/crud_views/lib/formsets/render_tree.py:200-204` and `src/crud_views/lib/formsets/formsets.py:348-370`, rejecting nonblank `edit_only` extra rows (`cv_additions_not_allowed`) and missing/malformed/unauthorized existing-row IDs (`cv_invalid_row`) before `cv_form_valid` (`src/crud_views/lib/formsets/mixins.py:80-129`) can save any model (`.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-04-PLAN.md:85-112`).

### Strengths
- **Covers all accepted `BaseInlineFormSet` classes**: Because `FormSet.validate_formset` (`src/crud_views/lib/formsets/formsets.py:60,88-89`) accepts any `django.forms.models.BaseInlineFormSet` subclass (imported via `src/crud_views/lib/formsets/inline_formset.py:7`), enforcing row policy in `XFormSet` during `FormSets.is_valid()` / `all_valid()` (`src/crud_views/lib/formsets/formsets.py:348-370`) protects both `InlineFormSet` and custom native subclasses (`06.4-04-PLAN.md:90`).
- **Reachable HTTP and native-subclass fixtures (H3)**: Task `04-01` builds `policy_routes` with isolated ViewSets/URLs and `PolicyNativeInlineFormSet` accepting `formset` and `parent_form` kwargs passed by `FormSet.init` (`src/crud_views/lib/formsets/formsets.py:148-160`) and exposing `helper` (`src/crud_views/lib/formsets/render_tree.py:82-90`), proving positive GET/POST before spying on `_cv_validate_row_policy` and zero saves on negative requests (`06.4-04-PLAN.md:90-91,143-144`).
- **Authorized identity and unsaved UUID distinction**: Validates submitted existing-row IDs against `instance.get_queryset()` on its DB alias while using `_cv_prefix_identity` / `instance._state.adding` (`src/crud_views/lib/formsets/formsets.py:28-37`) so unsaved default-UUID extra rows are not mistaken for persisted rows (`06.4-04-PLAN.md:104`).

### Concerns
None. Prior H1 integration and H3 remain closed with no regression.

### Suggestions
None.

### Risk Assessment
**Medium**: Integrating `_cv_validate_row_policy` into the two-pass `FormSets.all_valid()` (`src/crud_views/lib/formsets/formsets.py:354-370`) must remain idempotent across both passes; `06.4-04-PLAN.md:90` explicitly requires idempotence without duplicate non-form errors.

---

## 06.4-05

### Summary
Implements per-control disabled-state ownership composition, native form-scoped reset resynchronization, and stranded-focus recovery in `src/crud_views/static/crud_views/js/toggle.js:23-66` and `tests/js/toggle.test.js` (`.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-05-PLAN.md:73-100`).

### Strengths
- **Composed disabled ownership**: Replaces unconditional `el.disabled = !on` writes across `input, select, textarea` (`src/crud_views/static/crud_views/js/toggle.js:26-31`) with a per-control reducer combining observed external baseline `disabled` state and all inactive bound ancestor groups, while extending coverage to `button` elements (including formset Add/Delete/Reorder controls) and preserving the `MGMT_FIELD` exemption (`src/crud_views/static/crud_views/js/toggle.js:13,27-29`; `06.4-05-PLAN.md:78`).
- **Cancellable post-default reset (A04)**: Schedules form-scoped reset synchronization in a macrotask (`setTimeout(..., 0)`) after native form reset completes and checks `event.defaultPrevented` at the deferred point so later listeners calling `preventDefault()` are respected (`06.4-05-PLAN.md:92,129`).
- **Coherent modal and conditional focus recovery**: Moves focus only when hiding a group strands `document.activeElement` inside it (to its usable controlling checkbox, nearest usable ancestor toggle, or temporary `tabindex="-1"` on the visible owning form inside an active modal), preserving `modal.js` initial-show and 422 replacement focus ownership (`src/crud_views/static/crud_views/js/modal.js:46-69,90-103`; `06.4-05-PLAN.md:92`).

### Concerns
None. Prior A04 remains closed with no regression.

### Suggestions
None.

### Risk Assessment
**Medium**: Draining pending `MutationObserver` records before synchronous library writes and disconnecting only around self-writes (`06.4-05-PLAN.md:78`) is essential so same-value external `disabled = true` writes are not lost; both Vitest (`05-01`) and Chromium (`08-02`) test this explicitly.

---

## 06.4-06

### Summary
Replaces the page-global `CrudViewsFormset` startup in `src/crud_views/static/crud_views/js/formset.js:461-645` with a form-scoped, repeat-safe `cv.initFormsets(root = document)` initializer, hides stock `Add` controls on `edit_only` formsets in `src/crud_views/templates/crud_views/formsets/control.html:18-22`, and coordinates formset reorder on submit with `src/crud_views/static/crud_views/js/modal.js:165-178,227-233` (`.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-06-PLAN.md:94-123`).

### Strengths
- **Form-scoped controllers and exact attribute matching (A12, A16)**: Replaces page-wide `$(selector)` lookups in `XBase.sel`, `XFormset`, `XForm`, and `CrudViewsFormset` (`src/crud_views/static/crud_views/js/formset.js:52-55,130,173,280,371,476,543,600`) with owning-form-scoped structural queries and exact DOM attribute/name equality, tested with valid `FormSets.check_keys` (`src/crud_views/lib/formsets/formsets.py:294-299`) lowercase/hyphenated keys, UUIDs, deep prefixes, near-match decoys, and two same-prefix forms (`06.4-06-PLAN.md:99-100,164-166`).
- **Django-rendered stock control verification (A11)**: Gates the stock Add button in `src/crud_views/templates/crud_views/formsets/control.html:19-22` on `not formset.edit_only` and verifies actual Django template rendering in `tests/test1/test_formsets_controls.py` alongside JS handler enforcement (`06.4-06-PLAN.md:99,102-103,153`).
- **Modal submit ordering and error propagation**: Fixes `CrudViewsFormset.reorder_formsets()` (`src/crud_views/static/crud_views/js/formset.js:597-611`, where `return false` inside `.each(...)` only broke the loop while `reorder_formsets` still returned `true`) and ensures `document` submit handling in `src/crud_views/static/crud_views/js/modal.js:227-233` honors `event.defaultPrevented` after owning-form reorder runs (`06.4-06-PLAN.md:115`).

### Concerns
None. Prior A11, A12, and A16 remain closed with no regression.

### Suggestions
None.

### Risk Assessment
**Low**: Scoping controllers per `<form>` via a `WeakMap` and wiring `cv:modal:loaded` and `cv:formset:row-added` through `cv.initFormsets` cleanly supports 422 modal replacements without duplicate listeners.

---

## 06.4-07

### Summary
Repairs A19 non-first sibling child fragment indexing in `src/crud_views/lib/formsets/formsets.py:508-521` and fixes unbalanced closing tags on rows-only fragments in `src/crud_views/templates/crud_views/formsets/formset.html:4,56`, replacing the mismatch characterization in `tests/test1/test_fragment_authorization.py:1154-1205` with end-to-end prefix, wrapper-balance, and POST round-trip tests (`.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-07-PLAN.md:81-110`).

### Strengths
- **Exact root-cause fix for A19**: In `FormSets.get_template` (`src/crud_views/lib/formsets/formsets.py:508-513`), derives `index` from the parent `FormSet.children` declaration order (matching `FormSet.init` at `src/crud_views/lib/formsets/formsets.py:181-189` and `_cv_validate_fragment_coordinates` at `src/crud_views/lib/formsets/formsets.py:446`) instead of hardcoding `index=0`, and updates the docstring note at `src/crud_views/lib/formsets/formsets.py:417-418` (`06.4-07-PLAN.md:86`).
- **Unconditional raw fragment wrapper balance (H2)**: Replaces `{% if not x_formset.end_at_rows %}` at `src/crud_views/templates/crud_views/formsets/formset.html:56` (`end_at_rows` is undefined on `XFormSet` in `src/crud_views/lib/formsets/render_tree.py:93-103`, causing rows-only fragments to emit four stray closing tags) with `{% if not x_formset.render_rows_only %}` matching line 4, verified by a raw pre-parser tag-stack check and a negative control (`06.4-07-PLAN.md:100,139`).
- **Preserved AUTH-02 security gates**: Retains `_cv_validate_fragment_coordinates` ancestry checks and 403/400 negative assertions in `tests/test1/test_fragment_authorization.py:1187-1204` (`06.4-07-PLAN.md:86`).

### Concerns
None. Prior H2 remains closed with no regression.

### Suggestions
None.

### Risk Assessment
**Low**: Both `formsets.py:513` and `formset.html:56` are localized, high-precision repairs backed by raw HTML and round-trip POST assertions.

---

## 06.4-08

### Summary
Adds a real HTTP and Chromium acceptance harness (`tests/browser/conditional-formsets.cjs` and `tests/browser/conditional_formsets_server.py`) modeled on `tests/browser/modal-focus.cjs:1-120`, exercising stock Bootstrap and minimal non-Bootstrap templates across page, modal/422, dynamic row, reset, focus, and tampered POST lifecycles (`.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-08-PLAN.md:99-143`).

### Strengths
- **Runtime provenance and process isolation (A06, A07)**: Honors `CV_FOCUS_NODE`, `CV_FOCUS_PYTHON`, `CV_FOCUS_PLAYWRIGHT`, and `CV_FOCUS_CHROMIUM` before `.planning/phases/06-form-button-leaf/06-JS-RUNTIME.json:7` (`tests/browser/modal-focus.cjs:11-17,81-86`), fails on invalid overrides, binds `127.0.0.1` on `CV_CONDITIONAL_PORT` (default `8144`, rejecting `8143` used by `modal-focus.cjs:21,79`), refuses occupied ports, and reaps its own server child (`06.4-08-PLAN.md:83,119,175-176`).
- **Mandatory regression assertion table (H1, H2, A04, A10, A15)**: Defines required per-theme (`stock` and `native`) case and assertion IDs in `06.4-08-PLAN.md:105-111` covering `inline-file-clear-unchanged` (including reference-only `ImageField` clearing and real `FileField` multipart upload discard without Pillow), `fragment-raw-balance` (inspecting raw JSON `response.html` before DOM insertion), `native-reset-user-default` / `native-reset-user-cancelled` (Playwright click and keyboard reset activation), and `disabled-same-value-ownership`.

### Concerns
None. Prior H1, H2, A04, A06, A07, A10, and A15 remain closed with no regression.

### Suggestions
None.

### Risk Assessment
**Medium**: The browser suite coordinates multiple lifecycle paths across two themes; enforcing `--check-evidence` against source SHA-256 hashes and required assertion IDs (`06.4-08-PLAN.md:101-111,138`) prevents silent partial passes.

---

## 06.4-09

### Summary
Updates reference documentation (`docs/reference/conditional.md`, `docs/reference/formsets.md`, `docs/reference/javascript.md`), example commentary (`examples/bootstrap5/conditional/models.py:8-12`), paired `CHANGELOG.md` and `docs/migrating-1.0.md` entries, executable doc tests (`tests/test1/test_conditional_migration_docs.py`), and the Phase 7 handoff inventory (`.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-09-PLAN.md:96-128`).

### Strengths
- **Accurate clearing, validation, and commentary contracts (A08, A15)**: Updates `docs/reference/conditional.md:29-34,138-144` and `examples/bootstrap5/conditional/models.py:8` to replace the obsolete universal-`None` / `W320` / "Validation is skipped entirely" claims with the field-aware clearing matrix, `crud_views.E312`, authoritative inherited/model invariants, and the explicit distinction between tested `ImageField` reference semantics, `FileField` upload-discard evidence, and Django's application-level Pillow requirement for image upload decoding (`06.4-09-PLAN.md:102,157,170`).
- **Exact JSON PK projection vs. row identity (A13)**: Explicitly distinguishes `XFormSet.data["pk"]` (`self.pk.value` regex grammar in `src/crud_views/lib/formsets/render_tree.py:188`) from `XForm.data["pk"]` (`str(self.parent.pk)` enum spelling in `src/crud_views/lib/formsets/render_tree.py:67`) and from actual row/request `pk` identities (`06.4-09-PLAN.md:102,158`), and removes the A19 limitation note in `docs/reference/formsets.md:205-210` only after Plans 07/08 pass while keeping the integer/UUID PK boundary (`docs/reference/formsets.md:187-193`).
- **Bounded Phase 7 surface handoff**: Documents `cv.initConditional(root = document)` and `cv.initFormsets(root = document)` and the template data projection without promoting internal `XForm`/`XFormSet` constructors or `commit=False` (A8) to public API (`06.4-09-PLAN.md:102,118`).

### Concerns
None. Prior A08, A13, and A15 remain closed with no regression.

### Suggestions
None.

### Risk Assessment
**Low**: Executable fenced-code extraction in `tests/test1/test_conditional_migration_docs.py` and `.venv/bin/mkdocs build --strict` (`06.4-09-PLAN.md:105-108,121-124`) ensure documentation stays synchronized with code.

---

## 06.4-10

### Summary
Executes and records the supported-series regression gates across cached Django 4.2, 5.2, and 6.0 environments, Vitest, sequential Chromium runners (`conditional-formsets.cjs` on port 8144 then `modal-focus.cjs` on port 8143), strict MkDocs, and Ruff via `.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/10-evidence/run.py`, and reconciles `06.4-VALIDATION.md`, `06.4-ACCEPTANCE.md`, and the A19 handoff in `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-ACCEPTANCE.md` (`.planning/phases/06.4-conditional-and-formset-correctness-lifecycle/06.4-10-PLAN.md:93-122`).

### Strengths
- **Complete three-route per-series verification for A18**: In `06.4-10-PLAN.md:26,97-100` and `06.4-VALIDATION.md:113-133`, `10-evidence/run.py` runs and checks three distinct routes for each cached interpreter (`.nox/crispy_floor-3-12-django-4-2/bin/python`, `.nox/tests-3-12-django-5-2/bin/python`, `.nox/crispy_floor-3-12-django-6-0/bin/python`):
  1. **Enabled acceptance** (`CV_CONDITIONAL_TRACER=1`): requires exit 0 and JUnit testcase `tests/test1/test_conditional_layout.py::test_tracer_rendered_conditional_round_trip` passed with `tracer_node_path`, `tracer_node_version`, and `tracer_jsdom_version` properties.
  2. **Ordinary Node-free full suite** (`env -u CV_CONDITIONAL_TRACER -u CV_FOCUS_NODE PATH=`): requires exit 0, nonempty ordinary passing tests, `shutil.which("node") is None` and `shutil.which("npm") is None` in the subprocess environment, and no tracer testcase (including no skipped tracer) in JUnit.
  3. **Enabled missing-runtime negative control** (`CV_CONDITIONAL_TRACER=1 CV_FOCUS_NODE="$CV_PHASE_MISSING_NODE"` pointing to a nonexistent path inside a `TemporaryDirectory`): requires nonzero exit and the exact tracer node recorded as failed with the nonexistent-path diagnostic, zero skips, and no fallback.
- **Tamper-evident checker**: `run.py --check` validates all required browser case/assertion IDs from Plan 08 (H1, H2, A04, A10, A15), sequential browser execution (A07), source SHA-256 hashes, and deliberate corruption controls that mutate the passed tracer record to absent, skipped, failed, and zero-selected and corrupt disabled-route environment facts (`06.4-10-PLAN.md:97,99-100`).

### Concerns
None. Prior H1, H2, A04, A07, A10, and A18 are fully resolved.

### Suggestions
None.

### Risk Assessment
**Low**: The evidence runner and checker verify positive acceptance, Node-free ordinary portability, and negative-control failure behavior across all three supported Django series without modifying `.github/workflows/tests.yml` or `noxfile.py`.

---

## Cross-Plan Summary & Prior-Item Closure Ledger

All ten Phase 6.4 plans at commit `83c4f35` are coherent, source-grounded, and ready for execution. Revision `83c4f35` cleanly resolves A18 without widening scope or regressing any prior closure.

### Prior-Item Closure Ledger

| ID | Prior Severity | Plans | Status / Verification at `83c4f35` |
|---|---|---|---|
| **H1** | HIGH | 02, 04, 08, 10 | **CLOSED (preserved)** — `06.4-02-PLAN.md:97,111`, `06.4-04-PLAN.md:90`, `06.4-08-PLAN.md:107,119,133`, `06.4-10-PLAN.md:97` wire `_cv_conditional_requires_save` into `XFormSet.save` (`src/crud_views/lib/formsets/render_tree.py:259`) and require DB/storage proof when `form.has_changed()` is false. |
| **H2** | HIGH | 07, 08, 10 | **CLOSED (preserved)** — `06.4-07-PLAN.md:86,100`, `06.4-08-PLAN.md:108,119`, `06.4-10-PLAN.md:97` replace `x_formset.end_at_rows` (`src/crud_views/templates/crud_views/formsets/formset.html:56`) with `x_formset.render_rows_only` and enforce pre-parser raw wrapper stack balance. |
| **H3** | HIGH | 04 | **CLOSED (preserved)** — `06.4-04-PLAN.md:90-91` defines isolated `policy_routes` create/update ViewSets and `PolicyNativeInlineFormSet` adapting `formset`/`parent_form` kwargs (`src/crud_views/lib/formsets/formsets.py:148-160`) with positive GET/POST controls and `_cv_validate_row_policy` spies. |
| **A01** | MEDIUM | 02 | **CLOSED (preserved)** — `06.4-02-PLAN.md:111,149` isolates temporary `MEDIA_ROOT` and per-field storage with teardown outside the `storage.delete` spy interval. |
| **A02** | MEDIUM | 03 | **CLOSED (preserved)** — `06.4-03-PLAN.md:86,137` computes `base_fields`, declared toggles, and injected toggles per main/inline form class in `src/crud_views/checks.py:130-179`. |
| **A03** | LOW | — | **CLOSED (preserved)** — Previously incorporated/disposed in Round 1. |
| **A04** | MEDIUM | 05, 08, 10 | **CLOSED (preserved)** — `06.4-05-PLAN.md:92`, `06.4-08-PLAN.md:109-110,133`, `06.4-10-PLAN.md:97` schedule reset resync in a macrotask after native reset and verify click/keyboard reset and later-listener cancellation in both themes. |
| **A05** | LOW | — | **CLOSED (preserved)** — Previously incorporated/disposed in Round 1. |
| **A06** | MEDIUM | 08, 10 | **CLOSED (preserved)** — `06.4-08-PLAN.md:83,119,175` and `06.4-10-PLAN.md:97` honor `CV_FOCUS_NODE`, `CV_FOCUS_PYTHON`, `CV_FOCUS_PLAYWRIGHT`, and `CV_FOCUS_CHROMIUM` with recorded path/version provenance and hard failure on invalid overrides. |
| **A07** | MEDIUM | 08, 10 | **CLOSED (preserved)** — `06.4-08-PLAN.md:83,119,176` and `06.4-10-PLAN.md:97,154` use `CV_CONDITIONAL_PORT` (default `8144`, reserving `8143`) and run browser suites sequentially with owned-process cleanup. |
| **A08** | LOW | 09 | **CLOSED (preserved)** — `06.4-09-PLAN.md:102,157` updates `examples/bootstrap5/conditional/models.py:8` commentary to match field-aware clearing and `E312`. |
| **A09** | LOW | — | **CLOSED (preserved)** — Previously incorporated/disposed in Round 1. |
| **A10** | MEDIUM | 08, 10 | **CLOSED (preserved)** — `06.4-08-PLAN.md:111,133` and `06.4-10-PLAN.md:97` require Chromium same-value `disabled = true` and `disabled = false` ownership transitions in both themes. |
| **A11** | MEDIUM | 06, 10 | **CLOSED (preserved)** — `06.4-06-PLAN.md:99,102,153` and `06.4-10-PLAN.md:97` verify Django-rendered `crud_views/formsets/control.html` (`src/crud_views/templates/crud_views/formsets/control.html:18-22`) in `tests/test1/test_formsets_controls.py`. |
| **A12** | LOW | 06 | **CLOSED (preserved)** — `06.4-06-PLAN.md:99,154,166` replaces raw prefix CSS interpolation in `src/crud_views/static/crud_views/js/formset.js` with owning-form structural queries and exact DOM attribute/name equality. |
| **A13** | MEDIUM | 09 | **CLOSED (preserved)** — `06.4-09-PLAN.md:102,158` distinguishes `XFormSet.data["pk"]` regex grammar (`src/crud_views/lib/formsets/render_tree.py:188`) from `XForm.data["pk"]` enum spelling (`render_tree.py:67`) and row PK values. |
| **A14** | LOW | — | **CLOSED (preserved)** — Previously incorporated/disposed in Round 1. |
| **A15** | MEDIUM | 02, 08, 09, 10 | **CLOSED (preserved)** — `06.4-02-PLAN.md:79,111`, `06.4-08-PLAN.md:81,107,119,133`, `06.4-09-PLAN.md:102,170` test `ImageField` stored-reference clearing without image-byte decoding/Pillow, prove upload discard with real `FileField` bytes, and document the boundary. |
| **A16** | MEDIUM | 06 | **CLOSED (preserved)** — `06.4-06-PLAN.md:98-100,166` tests valid `FormSets.check_keys` (`src/crud_views/lib/formsets/formsets.py:294-299`) lowercase/hyphenated keys, UUIDs, deep prefixes, near-match decoys, and punctuation-rejection controls. |
| **A17** | LOW | 01 | **CLOSED (preserved)** — `06.4-01-PLAN.md:85,114,171` owns `_resolve_tracer_node` and inline JS in `tests/test1/test_conditional_layout.py`, honoring `CV_FOCUS_NODE` before `.planning/phases/06-form-button-leaf/06-JS-RUNTIME.json:7` and failing explicitly on invalid/missing runtimes once enabled. |
| **A18** | MEDIUM | 01, 10 | **CLOSED (signed off at `83c4f35`)** — `06.4-01-PLAN.md:29,113-126,137,183`, `06.4-10-PLAN.md:26,97-100,166`, and `06.4-VALIDATION.md:18-20,34-35,57,73-75,105-133` gate `test_tracer_rendered_conditional_round_trip.__test__` on `CV_CONDITIONAL_TRACER=1` with zero import-time runtime/manifest work, verify Node-free disabled collection (`env -u CV_CONDITIONAL_TRACER -u CV_FOCUS_NODE PATH=`), and require per-Django-series JUnit evidence for enabled tracer pass (with runtime properties), Node-free ordinary full suite pass, and enabled missing-runtime (`CV_FOCUS_NODE="$CV_PHASE_MISSING_NODE"`) failure control. |

### Deduplicated Unresolved Concerns

None.
