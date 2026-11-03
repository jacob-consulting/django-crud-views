## 06.4-01

### Summary
Establishes exact bound checkbox identity from server rendering (`ToggleGroup` and top-level `ConditionalFormSet` wrappers) through client-side `toggle.js` resolution (`cv.initConditional(root = document)`) to ModelForm submission (`06.4-01-PLAN.md:57-61,106-136`).

### Strengths
- **End-to-end bound-name contract:** `src/crud_views/lib/conditional/layout.py:25-35` currently emits unprefixed `self.toggle_field` into `src/crud_views/templates/crud_views/conditional/toggle_group.html:4,9`, and `src/crud_views/lib/formsets/render_tree.py:196-198` emits unprefixed `conditional.toggle.field_name()` into `src/crud_views/templates/crud_views/formsets/formsets.html:4-5`. Tasks `01-01` and `01-02` (`06.4-01-PLAN.md:112,128`) emit `form.add_prefix(...)` for both group and top-level formset wrappers while keeping `XFormSet.cv_bound_toggle_field` as an explicit declared Pydantic field on `XFormSet` (`src/crud_views/lib/formsets/render_tree.py:93-103`).
- **Safe owning-form lookup and ambiguity isolation:** Replaces the suffix selector in `src/crud_views/static/crud_views/js/toggle.js:15-21,38-45` (which currently sets `group.__cvToggleWired = true` before resolving the checkbox and matches `input[type="checkbox"][name$="-" + escaped]`) with exact `el.name === name` matching scoped to `group.closest("form") || document`, keeping missing toggles retryable and isolating duplicate-name ambiguity with `console.warn` (`06.4-01-PLAN.md:112`).

### Concerns
None.

### Suggestions
- In `01-01` (`06.4-01-PLAN.md:112`), ensure existing unit tests in `tests/js/toggle.test.js:67-71` (which currently assert legacy suffix matching) and `tests/test1/test_conditional_layout.py:30-37` are updated alongside the new prefixed and ambiguity cases.

### Risk Assessment
**LOW** — The bound-name change is small, well-isolated, and verified via a real Django-to-Node/jsdom-to-ModelForm round-trip tracer (`06.4-01-PLAN.md:112-119`).

---

## 06.4-02

### Summary
Implements field-aware conditional clearing and server-disabled preservation in `ConditionalGroupFormMixin`, and connects effective conditional clearing on existing inline rows to `XFormSet.save()` even when `form.has_changed()` is `False` (`06.4-02-PLAN.md:51-55,91-118`).

### Strengths
- **Closes prior H1 (`XFormSet.save` `has_changed()` skip):** In `src/crud_views/lib/formsets/render_tree.py:256-260`, `XFormSet.save()` only calls `_save_changed_form(form, can_order)` when `form.has_changed()` is `True`. Tasks `02-01` and `02-02` (`06.4-02-PLAN.md:76,96,110`) compute a private `_cv_conditional_requires_save` flag on the form from effective scalar/file/relation differences against the original persisted instance before `_post_clean` mutates `self.instance`, and consume that signal in `XFormSet.save()` only for existing persisted rows (never forcing untouched blank extras or unsaved default-UUID rows).
- **Closes prior A01 (storage isolation):** Task `02-02` (`06.4-02-PLAN.md:110,148`) isolates `FileField` and `ImageField` persistence tests to `pytest` `tmp_path` via `override_settings(MEDIA_ROOT=...)` and explicit per-field storage, spying on `storage.delete` during production save while keeping fixture teardown outside the spy window.
- **Pre-validation instance construction:** Applying resolved scalar/file values via `model_field.save_form_data` in cooperative `_post_clean` before `super()._post_clean()` prevents Django's `construct_instance` from retaining pre-existing or default values when a widget is omitted from `request.POST`, and ensures `instance.full_clean()` / `validate_unique()` see the final cleared state (`06.4-02-PLAN.md:42-43,96`).

### Concerns
None.

### Suggestions
- When computing `_cv_conditional_requires_save` for M2M fields in `02-02` (`06.4-02-PLAN.md:110`), check `self.instance.pk` and compare the existing relation PK set against the resolved empty collection so an already-empty M2M relation on an unchanged off-toggle inline row does not trigger a redundant row save.

### Risk Assessment
**LOW** — Sequencing Plan 02 in Wave 2 after Plan 01 (`06.4-02-PLAN.md:5-6`) eliminates shared-file contention on `render_tree.py` and directly tests `XFormSet.save()` with real schema-backed models.

---

## 06.4-03

### Summary
Extends `crud_views.checks.check_conditional` (`crud_views.E312`, retiring `W320`) and runtime `ConditionalGroupFormMixin` validation to reject unsupported automatic clearing configurations across main and inline form classes (`06.4-03-PLAN.md:42-46,81-108`).

### Strengths
- **Closes prior A02 (per-form-class static check namespaces):** `src/crud_views/checks.py:164-179` currently computes `declared` and `group_injected` once from `view.form_class`. Task `03-01` (`06.4-03-PLAN.md:86,137`) recomputes `base_fields`, declared toggle fields, and injected toggle names independently for each main and inline form class traversed in `cv_formsets` (and nested `children`), with explicit tests preventing main-form field names from masking missing inline toggles (`E311`) or inline clearing errors (`E312`).
- **Shared static and runtime resolver:** Reuses `resolve_conditional_empty_value` from `src/crud_views/lib/conditional/group.py` without instantiating request-dependent forms at startup (`06.4-03-PLAN.md:37-39,86,100`).

### Concerns
None.

### Suggestions
- In `03-01` (`06.4-03-PLAN.md:86`), update the existing `W320` unit tests in `tests/test1/test_conditional_checks.py:292-298,372-393` to assert `crud_views.E312` on unsupported non-nullable fields (like `Profile.name` without `empty_values`) and zero warnings on supported non-nullable blank/Boolean/M2M shapes.

### Risk Assessment
**LOW** — Static and runtime checks share a single resolver and are verified against both static `base_fields` and dynamic `__init__`-injected fields (`06.4-03-PLAN.md:88-90,102-104`).

---

## 06.4-04

### Summary
Enforces mandatory active-formset row policy (`edit_only` extra rejection and existing-row PK authorization/identity validation) in `XFormSet` before any main, sibling, or nested save occurs (`06.4-04-PLAN.md:45-49,85-112`).

### Strengths
- **Closes prior H3 (reachable HTTP fixtures and native subclass adapter):** Task `04-01` (`06.4-04-PLAN.md:70-71,90-91,144`) constructs `policy_routes` inside `tests/test1/test_formsets_policy.py` following `tests/test1/test_fragment_authorization.py:195-340`, registering dedicated `edit_only=True` and `edit_only=False` create/update views with restricted querysets. It also defines `PolicyNativeInlineFormSet` as a direct `django.forms.models.BaseInlineFormSet` subclass that accepts `formset` and `parent_form` in `__init__` (`src/crud_views/lib/formsets/formsets.py:148-160`) and provides `helper` (`src/crud_views/lib/formsets/render_tree.py:90`) without inheriting `crud_views.lib.formsets.inline_formset.InlineFormSet.clean`, proving positive GET/POST and spying on `_cv_validate_row_policy` on negative requests.
- **Preserves H1 inline conditional persistence:** Depends on `06.4-02` (`06.4-04-PLAN.md:6,90,107,143`) and runs `tests/test1/test_conditional_persistence.py` in `04-02` verification so mandatory row-policy gates and conditional inline saves compose cleanly in `render_tree.py`.
- **Covers all accepted declarations and tampering vectors:** Putting `_cv_validate_row_policy` on `XFormSet` (`src/crud_views/lib/formsets/render_tree.py:200-203`) rather than `InlineFormSet.clean` (`src/crud_views/lib/formsets/inline_formset.py:111-118`) protects custom `BaseInlineFormSet` classes, `DELETE`-marked forged rows, nested-only data on blank extra parents, and tampered `INITIAL_FORMS` counts (`06.4-04-PLAN.md:90,104`).

### Concerns
None.

### Suggestions
- Ensure `XFormSet.is_valid()` (`src/crud_views/lib/formsets/render_tree.py:200-203`) reflects non-form errors added by `_cv_validate_row_policy()` in both passes of `FormSets.all_valid()` (`src/crud_views/lib/formsets/formsets.py:365-369`), since `BaseFormSet.is_valid()` checks `self.is_bound and not self.errors and not self.non_form_errors()`.

### Risk Assessment
**LOW** — Pre-save validation in `XFormSet` integrates directly with `FormSetMixinBase.cv_form_is_valid` (`src/crud_views/lib/formsets/mixins.py:104-105`) before `cv_form_valid` enters its transaction block (`mixins.py:114`).

---

## 06.4-05

### Summary
Replaces unconditional `el.disabled = !on` writes in `toggle.js` with composed baseline + inactive-ancestor disabled ownership, post-default native form reset synchronization, and stranded-focus recovery (`06.4-05-PLAN.md:37-41,73-100`).

### Strengths
- **Closes prior A04 (macrotask native reset scheduling):** Task `05-02` (`06.4-05-PLAN.md:92,129`) schedules reset resynchronization in a macrotask (`setTimeout(..., 0)`) after the browser's native reset algorithm finishes and checks `event.defaultPrevented` at the deferred point so later `reset` listeners calling `preventDefault()` are respected.
- **Sound disabled-state ownership model:** Task `05-01` (`06.4-05-PLAN.md:78`) uses a `MutationObserver` on `disabled` with `attributeOldValue: true`, drains pending records via `takeRecords()` before synchronous updates, and disconnects only around `toggle.js`'s own synchronous writes, preserving external `true -> false` and `false -> true` changes (including setting `disabled = true` while already conditionally disabled) and excluding management inputs (`TOTAL_FORMS`, `INITIAL_FORMS`, `MIN_NUM_FORMS`, `MAX_NUM_FORMS`).
- **Coordinated modal focus:** Preserves `modal.js`'s focus lifecycle (`src/crud_views/static/crud_views/js/modal.js:90-103`) and disposes observers on `cv:modal:unload` (`06.4-05-PLAN.md:92`).

### Concerns
None.

### Suggestions
- None.

### Risk Assessment
**LOW** — Composed ownership and macrotask reset handling are well-specified and verified in both Vitest (`06.4-05-PLAN.md:81,95`) and Chromium (`06.4-08-PLAN.md:109-111`).

---

## 06.4-06

### Summary
Scopes `formset.js` controllers per owning `<form>` via `cv.initFormsets(root = document)`, hides/blocks `edit_only` Add controls, eliminates raw prefix CSS selector interpolation, and orders formset submit reordering ahead of `modal.js` `FormData` serialization (`06.4-06-PLAN.md:52-56,94-123`).

### Strengths
- **Closes prior A11 (Django-rendered stock control template verification):** Task `06-01` (`06.4-06-PLAN.md:11,29-30,78,98-103,153`) adds `tests/test1/test_formsets_controls.py` and a dedicated pytest verification step that renders `src/crud_views/templates/crud_views/formsets/control.html` through Django for `edit_only=True` and `edit_only=False` alongside `can_delete`/`can_order` combinations.
- **Closes prior A12 (prefix selector safety):** Replaces raw attribute selector interpolation in `src/crud_views/static/crud_views/js/formset.js:130,165,173,180,230,280,306,347,371,439,511` with fixed structural queries scoped to the owning form plus exact attribute/name equality, and tests punctuation-bearing prefixes (`line.items:detail`) (`06.4-06-PLAN.md:99-100,154`).
- **Fixes submit reorder error propagation and modal ordering:** Corrects `reorder_formsets()` (`src/crud_views/static/crud_views/js/formset.js:597-611`, where `return false` inside `.each()` failed to make `reorder_formsets()` return `false`) and updates `src/crud_views/static/crud_views/js/modal.js:227-233` to honor `event.defaultPrevented` before calling `cvModalSubmit` (`06.4-06-PLAN.md:115`).

### Concerns
None.

### Suggestions
- None.

### Risk Assessment
**LOW** — Form-scoped `WeakMap` controller management and exact attribute comparisons directly address all multi-form and modal lifecycle defects in `formset.js`.

---

## 06.4-07

### Summary
Repairs A19 non-first sibling child-fragment indexing in `FormSets.get_template`, unconditionally fixes the mismatched closing wrapper condition in `formset.html`, and proves raw HTML wrapper balance and full POST/DB round trips (`06.4-07-PLAN.md:43-47,81-110`).

### Strengths
- **Closes prior H2 (unconditional `render_rows_only` closing guard + pre-parser raw HTML check):** `src/crud_views/templates/crud_views/formsets/formset.html:56` currently checks `{% if not x_formset.end_at_rows %}` against an attribute that does not exist on `XFormSet` (`src/crud_views/lib/formsets/render_tree.py:102`), emitting four stray closing tags on every AJAX fragment. Task `07-02` (`06.4-07-PLAN.md:99-101,139`) unconditionally changes line 56 to `{% if not x_formset.render_rows_only %}` to match line 4, validates raw HTML with a strict tag-token stack before any DOM parser runs, and includes a negative control that appends the old stray closing tags and must fail the checker. Task `07-01` (`06.4-07-PLAN.md:86`) also updates the stale A19 docstring note in `src/crud_views/lib/formsets/formsets.py:417-418`.
- **Exact declaration-index derivation:** In `src/crud_views/lib/formsets/formsets.py:508-514`, `get_template` derives the selected child's index from its parent's ordered `children` dict (matching `FormSet.init` at line 181 and `_cv_validate_fragment_coordinates` at line 446) while keeping `0` for top-level formsets (`06.4-07-PLAN.md:86`).

### Concerns
None.

### Suggestions
- None.

### Risk Assessment
**LOW** — The index derivation and template guard are exact 1-to-1 alignments with `FormSet.init` and `formset.html:4`, backed by raw token-stack and DB round-trip tests.

---

## 06.4-08

### Summary
Builds a permanent real-HTTP/Playwright Chromium acceptance harness (`tests/browser/conditional-formsets.cjs` and `tests/browser/conditional_formsets_server.py`) covering stock Bootstrap and minimal non-Bootstrap templates across all Phase 06.4 lifecycle, focus, reset, persistence, and row-policy requirements (`06.4-08-PLAN.md:56-60,113-143`).

### Strengths
- **Closes prior H1, H2, A04, and A10 in real browser evidence:** Explicitly defines the required regression evidence table (`06.4-08-PLAN.md:99-111`) for both `stock` and `native` themes with mandatory case IDs (`inline-file-clear-unchanged`, `fragment-raw-balance`, `native-reset-user-default`, `native-reset-user-cancelled`, `disabled-same-value-ownership`) and exact assertion IDs enforced by `--check-evidence` (`06.4-08-PLAN.md:119,133-141,172-177`).
- **Closes prior A06 and A07 (runtime overrides and port isolation):** Honors `CV_FOCUS_NODE`, `CV_FOCUS_PYTHON`, `CV_FOCUS_PLAYWRIGHT`, and `CV_FOCUS_CHROMIUM` (failing clearly on invalid overrides and recording resolved paths/versions in evidence) and uses `CV_CONDITIONAL_PORT` defaulting to `8144` while rejecting `8143` reserved by `tests/browser/modal-focus.cjs:21,79` (`06.4-08-PLAN.md:83,119,175-176`).

### Concerns
None.

### Suggestions
- None.

### Risk Assessment
**LOW** — Reuses the proven disposable loopback server and Playwright process-management pattern from `tests/browser/modal-focus.cjs` with strict source-hash and assertion-ID validation.

---

## 06.4-09

### Summary
Updates reference documentation (`conditional.md`, `formsets.md`, `javascript.md`), example model comments (`examples/bootstrap5/conditional/models.py`), paired `CHANGELOG.md` / `docs/migrating-1.0.md` Breaking notes, and the Phase 7 public surface handoff (`06.4-PUBLIC-SURFACE.md`), verified by executable doc-recipe tests (`06.4-09-PLAN.md:55-59,96-128`).

### Strengths
- **Closes prior A08 (stale conditional example comment):** Adds `examples/bootstrap5/conditional/models.py` (`06.4-09-PLAN.md:12,30-31,89,99,102,157`) to update line 8's stale comment (`# null=True: a switched-off ConditionalGroup clears its fields to None on save (see crud_views.W320).`) to match field-aware clearing and `crud_views.E312`.
- **Closes prior A13 (JSON `pk` grammar vs. row identity):** Task `09-01` (`06.4-09-PLAN.md:102,158`) explicitly distinguishes `XFormSet.data.pk` (`self.pk.value`, the regex grammar in `src/crud_views/lib/formsets/render_tree.py:188`) from `XForm.data.pk` (`str(self.parent.pk)`, the enum string `"PK.INT"` / `"PK.UUID"` in `render_tree.py:67`) and from the request `pk` parameter, testing published JSON examples against live runtime data.
- **Executable documentation recipes:** Modeled on `tests/test1/test_delete_migration_docs.py`, `tests/test1/test_conditional_migration_docs.py` extracts and runs published fences and verifies `CHANGELOG.md` ↔ `docs/migrating-1.0.md` anchors plus `.venv/bin/mkdocs build --strict` (`06.4-09-PLAN.md:104-109,120-125`).

### Concerns
None.

### Suggestions
- None.

### Risk Assessment
**LOW** — All documentation updates follow verified implementation/browser evidence in Wave 7 and are guarded by executable fence tests and `mkdocs build --strict`.

---

## 06.4-10

### Summary
Executes and verifies the supported Django-series (4.2, 5.2, 6.0), Vitest, Ruff, MkDocs, and sequential browser regression gates (`10-evidence/run.py`), and reconciles `06.4-MATRIX.md`, `06.4-VALIDATION.md`, `06.4-ACCEPTANCE.md`, and the scoped A19 note in `06.2-ACCEPTANCE.md` (`06.4-10-PLAN.md:51-55,91-119`).

### Strengths
- **Closes prior H1, H2, A04, A07, and A10 in final gate verification:** Task `10-01` (`06.4-10-PLAN.md:96,148-151`) runs `tests/browser/conditional-formsets.cjs` (`8144`) and `tests/browser/modal-focus.cjs` (`8143`) sequentially, waiting for server/browser exit and port release between runs, and requires all both-theme case/assertion IDs from Plan 08's review regression evidence table plus negative-control corruption checks on exit code, case list, raw-balance/inline-clear assertions, and source hashes.
- **Strict checkout-source provenance across cached Django series:** Runs focused and full suites on `.nox/crispy_floor-3-12-django-4-2/bin/python`, `.nox/tests-3-12-django-5-2/bin/python`, and `.nox/crispy_floor-3-12-django-6-0/bin/python` with `PYTHONPATH="$PWD/src:$PWD"`, honoring only the documented CSP and crispy-floor golden exclusions from `06.3-MATRIX.md` (`06.4-10-PLAN.md:96`).

### Concerns
None.

### Suggestions
- None.

### Risk Assessment
**LOW** — Comprehensive, source-hash-bound verification gate with negative controls on the evidence checker itself.

---

## Cross-Plan Summary

All ten revised Phase 6.4 plans at commit `75c1fea` are coherent, properly sequenced across 8 waves with zero same-wave file ownership overlap, and grounded in current repository source:
- `src/crud_views/lib/formsets/render_tree.py` is cleanly sequenced across Wave 1 (`06.4-01`), Wave 2 (`06.4-02`), and Wave 3 (`06.4-04`).
- `src/crud_views/lib/formsets/formsets.py` is cleanly sequenced across Wave 1 (`06.4-01`), Wave 3 (`06.4-04`), and Wave 5 (`06.4-07`).
- `src/crud_views/static/crud_views/js/toggle.js` is sequenced across Wave 1 (`06.4-01`) and Wave 2 (`06.4-05`), before `06.4-06` (Wave 4) and `06.4-07` (Wave 5) exercise combined formset/modal/toggle JS lifecycles.
- `06.4-08` (Wave 6), `06.4-09` (Wave 7), and `06.4-10` (Wave 8) integrate browser acceptance, documentation/migration contracts, and multi-series evidence in order.

## Explicit Prior-Item Closure Ledger

| Prior ID | Class / Severity | Status | Verification of Executable Remedy in Current Plans (`75c1fea`) |
|---|---|---|---|
| **H1** | HIGH (judgment) | **CLOSED / SIGNED OFF** | `06.4-02-PLAN.md:6,25,27-28,38-40,76,96,110,147` adds `render_tree.py` ownership to Plan 02, computes private `_cv_conditional_requires_save` before `_post_clean` mutates `self.instance`, augments `XFormSet.save()` (`src/crud_views/lib/formsets/render_tree.py:259`) for existing persisted rows when `form.has_changed()` is `False`, and tests unchanged/off-toggle `FileField`/`ImageField` inline rows via `XFormSet.save()`. Preserved in `06.4-04-PLAN.md:6,90,107,143` and enforced in `06.4-08-PLAN.md:107,119,133,172` and `06.4-10-PLAN.md:96,148`. |
| **H2** | HIGH (judgment) | **CLOSED / SIGNED OFF** | `06.4-07-PLAN.md:24,69,86,99-101,139` unconditionally changes `src/crud_views/templates/crud_views/formsets/formset.html:56` from `{% if not x_formset.end_at_rows %}` to `{% if not x_formset.render_rows_only %}`, updates the stale A19 docstring in `src/crud_views/lib/formsets/formsets.py:417-418`, and verifies raw pre-parser wrapper balance with a strict token stack and a stray-close negative control. Enforced in `06.4-08-PLAN.md:108,119,173` and `06.4-10-PLAN.md:96,149`. |
| **H3** | HIGH (existence) | **CLOSED / SIGNED OFF** | `06.4-04-PLAN.md:70-71,90-91,144` specifies test-local `policy_routes` (registered create/update ViewSets, `edit_only=True`/`False` declarations, restricted querysets, teardown restoration) and `PolicyNativeInlineFormSet` (direct `BaseInlineFormSet` subclass handling `formset`/`parent_form` kwargs and `.helper` without inheriting package `InlineFormSet.clean`), with positive GET/POST proofs and `_cv_validate_row_policy` spies. |
| **A01** | MEDIUM | **CLOSED / SIGNED OFF** | `06.4-02-PLAN.md:77,110,148` isolates `FileField`/`ImageField` tests to `pytest` `tmp_path` via `override_settings(MEDIA_ROOT=...)` and explicit per-field storage, keeping fixture teardown outside the `storage.delete` spy interval. |
| **A02** | MEDIUM | **CLOSED / SIGNED OFF** | `06.4-03-PLAN.md:86,137` recomputes `base_fields`, declared toggles, and injected toggles per inspected main/inline form class in `src/crud_views/checks.py:164-179` and tests distinct main/inline namespaces for `E311` and `E312`. |
| **A03** | Non-HIGH (prior cycle) | **CLOSED / SIGNED OFF** | Preserved in `06.4-01-PLAN.md:112` and `06.4-02-PLAN.md:96`; no regression. |
| **A04** | MEDIUM | **CLOSED / SIGNED OFF** | `06.4-05-PLAN.md:92,129`, `06.4-08-PLAN.md:109-110,119,133,174`, and `06.4-10-PLAN.md:96,150` specify macrotask (`setTimeout(..., 0)`) resync after native reset, inspect `event.defaultPrevented` (including later listeners), and test real user click + keyboard reset-button activation in Chromium. |
| **A05** | Non-HIGH (prior cycle) | **CLOSED / SIGNED OFF** | Preserved in `06.4-05-PLAN.md:78,92` and `06.4-06-PLAN.md:115`; no regression. |
| **A06** | MEDIUM | **CLOSED / SIGNED OFF** | `06.4-08-PLAN.md:83,119,175` and `06.4-10-PLAN.md:96` honor `CV_FOCUS_NODE`, `CV_FOCUS_PYTHON`, `CV_FOCUS_PLAYWRIGHT`, and `CV_FOCUS_CHROMIUM`, fail clearly on invalid overrides, and record resolved real paths and versions. |
| **A07** | MEDIUM | **CLOSED / SIGNED OFF** | `06.4-08-PLAN.md:83,119,176` and `06.4-10-PLAN.md:96,151` configure `CV_CONDITIONAL_PORT` (default `8144`, rejecting `8143`), refuse occupied ports, reap owned child processes, and run the two browser harnesses sequentially in Plan 10. |
| **A08** | LOW | **CLOSED / SIGNED OFF** | `06.4-09-PLAN.md:12,30-31,89,99,102,157` updates `examples/bootstrap5/conditional/models.py:8` to replace the stale universal-`None`/`W320` comment with the field-aware clearing and `E312` contract. |
| **A09** | Non-HIGH (prior cycle) | **CLOSED / SIGNED OFF** | Preserved across `06.4-08-PLAN.md`, `06.4-09-PLAN.md`, and `06.4-10-PLAN.md`; no regression. |
| **A10** | MEDIUM | **CLOSED / SIGNED OFF** | `06.4-08-PLAN.md:111,133,177` and `06.4-10-PLAN.md:96,150` require Chromium case `disabled-same-value-ownership` (external `disabled=true` while already conditionally disabled, external `false` while inactive, off/on, and reinit) in both themes. |
| **A11** | MEDIUM | **CLOSED / SIGNED OFF** | `06.4-06-PLAN.md:11,29-30,78,96,98-103,153` and `06.4-10-PLAN.md:96` add `tests/test1/test_formsets_controls.py` rendering `src/crud_views/templates/crud_views/formsets/control.html` through Django for `edit_only=True`/`False` and run pytest on it in `06-01`. |
| **A12** | LOW | **CLOSED / SIGNED OFF** | `06.4-06-PLAN.md:98-100,154` uses fixed structural selectors within the owning form plus exact attribute/name equality for all dynamic prefix lookups and tests punctuation-bearing prefixes (`line.items:detail`). |
| **A13** | MEDIUM | **CLOSED / SIGNED OFF** | `06.4-09-PLAN.md:102,158` documents and tests `XFormSet.data.pk` (regex grammar `FormSet.PK.value`) vs. `XForm.data.pk` (`"PK.INT"`/`"PK.UUID"` enum spelling) vs. actual row/request `pk`. |
| **A14** | Non-HIGH (prior cycle) | **CLOSED / SIGNED OFF** | Preserved in `06.4-10-PLAN.md:96,111`; no regression. |

## Deduplicated Unresolved Concerns

None (`current_high=0`, `current_actionable=0`). All prior HIGH and actionable concerns are resolved in the current plan set at commit `75c1fea`, and fresh review identified no new blocking or actionable concerns.
