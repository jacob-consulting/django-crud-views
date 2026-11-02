I've confirmed the key mechanisms against source. Writing the review now.

# Cross-AI Plan Review: Phase 06.4 (Conditional and formset correctness/lifecycle)

**Scope of this review.** Read-only. I opened the referenced source files, templates, tests, the Django installed in `.nox/crispy_floor-3-12-django-6-0`, and the environment paths the verify commands depend on. Findings below cite `path:line`. Where I could not verify a claim, I say so.

**Environment facts verified.** `.nox/crispy_floor-3-12-django-4-2`, `.nox/crispy_floor-3-12-django-6-0`, `.nox/tests-3-12-django-5-2` exist. `.venv/bin/mkdocs` and `.venv/bin/ruff` exist. `tests/test1/app/` has no `migrations/` directory (so new test-only models need no migration file). `tests/test1/conftest.py` configures no `MEDIA_ROOT` (lines 85–110). The test app contains no `edit_only=True` formset declaration (`grep edit_only tests/` hits only `test_conditional_checks.py` fakes and `tests/js/helpers/dom.js`).

**Root causes the plans assume are confirmed in current source:**

| Finding | Evidence |
|---|---|
| Suffix matching, eager wired flag, unconditional disabled writes | `toggle.js:15-21` (`name$="-'+escaped+'"`), `:36-39` (`__cvToggleWired = true` before resolve), `:30` (`el.disabled = !on`) |
| Universal `None` clearing | `group.py:36-37` |
| Formset wrapper uses declaration name, not bound name | `render_tree.py:195-198`, `formsets.html:4-5` |
| Fragment always index 0 | `formsets.py:513` |
| Page-wide one-shot controller, global lookups | `formset.js:476`, `:543`, `:600`, `:638` |
| `reorder_formsets` swallows per-formset failure | `formset.js:600-611` (`return false` only breaks `.each`; function returns `true`) |
| Stock Add has no edit-only predicate | `control.html:18-22` |
| Stray closing wrappers in fragments | `formset.html:56` tests `end_at_rows`, which no `XFormSet` field defines (`render_tree.py:93-102`), so the closing `</div></fieldset></div></div>` always renders even when `render_rows_only=True` |
| Save bypasses Django's `edit_only`/pk guards | `render_tree.py:256-260` saves any `has_changed()` form; Django's own guards live in `save()` (`django/forms/models.py:814-817`, `:948-960`) which this code never calls |

---

## 06.4-01

**Summary.** Correctly targets the exact-identity defect at both emission points (crispy `ToggleGroup` and the formset wrapper) and the JS resolver. The tracer design (rendered HTML → shipped `toggle.js` in a Node subprocess → FormData → bind back to Django → save) is a genuine end-to-end proof. Two existing tests encode the old contract and will have to be replaced, which the plan does not say explicitly.

**Strengths.**
- `ToggleGroup.render` receives `form` (`layout.py:25`), so `form.add_prefix(self.toggle_field)` is directly available; the context-key set stays `cv_toggle_field/css/legend/inner` as required.
- `FormSets.init(request, form)` (`formsets.py:385-388`) has the main form at the point where top-level `XFormSet`s are created, so the private bound name for the wrapper can be set there without a public constructor.
- Keeps `D-02` isolation: ambiguity leaves the group's own state alone, retry stays possible because the early `__cvToggleWired` flag is removed.

**Concerns.**
- **MEDIUM — two existing JS tests assert the old suffix contract and are not named for replacement.** `tests/js/toggle.test.js:67-71` ("finds the checkbox by formset-prefixed suffix name") passes `cv-data-toggle-field="active"` with checkbox `book-None-0-active` and expects hide. Under exact matching this becomes an unresolved group (display untouched) and the test fails. `:89-97` ("leaves a group without a matching checkbox untouched") still passes but now describes the retry case rather than an error. Plan 01-01 says "Expand JS cases" but must also *delete or invert* the suffix test; otherwise the verify command for 01-01 cannot go green.
- **MEDIUM — `XFormSet` is a Pydantic model; "private field" needs `PrivateAttr` or an explicit field.** `render_tree.py:93` declares `class XFormSet(BaseModel, arbitrary_types_allowed=True)`. Setting an undeclared attribute on a Pydantic v2 model raises. The plan's "private cv_bound_toggle_field" must be either a declared field (`cv_bound_toggle_field: str = ""`) or `PrivateAttr`. Not a design flaw, but the executor should know before writing.
- **LOW — `ModelFieldToggle.is_on` already uses `form.add_prefix`** (`toggle.py:29`), so server authority is unaffected by the rendering change; worth stating in the tracer's assertions so the "server policy unchanged" claim is tested, not assumed.
- **LOW — wrapper scope.** `formsets.html` is rendered via the `Formsets` crispy layout object (`layout.py:7-19`) inside the main form's crispy layout, so `group.closest("form")` resolves the main form. The plan relies on this but does not assert it; a test with two prefixed forms each carrying a formset wrapper would pin it.

**Suggestions.**
- Name `toggle.test.js:67` for removal/inversion in 01-01's action.
- State the Pydantic field mechanism for `cv_bound_toggle_field`.
- Add a two-form wrapper case (two main forms with prefixes `a`/`b`, both with a conditional formset) to 01-02.

**Risk: MEDIUM.** Contract change is deliberate (D-01); the mechanics are sound; the main execution risk is the un-named test churn and the private-field mechanics.

---

## 06.4-02

**Summary.** The persistence approach (apply resolved off-values to the instance *before* inherited `_post_clean`, let `construct_instance` skip omitted-with-default fields) is correct against installed Django and is the only way to fix the "existing/default value survives" defect without re-implementing `construct_instance`. The matrix is appropriately bounded. The test environment lacks `MEDIA_ROOT`, which the "real storage" file tests need.

**Strengths.**
- Mechanism verified: `construct_instance` skips a field when `f.has_default()` and the widget reports the value omitted and the cleaned value is empty (`django/forms/models.py:75-82`). Pre-setting the instance attribute before `super()._post_clean()` survives that skip. For posted-but-empty values, `save_form_data` writes the same resolved value. FileField `save_form_data` treats `None` as no-change and other falsy as clear (`files.py:360-364`), matching the plan's `False` choice.
- `_post_clean` exists on `BaseForm` as a no-op hook (`forms.py:361`) and on `BaseModelForm` (`models.py:479`), so the cooperative override works for plain forms too, as D-15 requires.
- D-09 ordering is right: Django's `_clean_fields` places the *initial* value in `cleaned_data` for `disabled=True` fields, so skipping disabled fields before `_cv_clear_group` (`group.py:78-84`) preserves the trusted value.

**Concerns.**
- **MEDIUM — no `MEDIA_ROOT` in the test settings.** `tests/test1/conftest.py` (DB block at :91-100) sets no `MEDIA_ROOT`/`STORAGES`. "Use real storage and spy on delete" (02-02) will write uploaded files relative to the CWD (repo root) unless the test overrides `MEDIA_ROOT` to `tmp_path`. The plan should require an `override_settings(MEDIA_ROOT=tmp_path)` fixture; otherwise the test litters the checkout and can collide across workers.
- **MEDIUM — explicit `None` for FileField is "no change", but the current mixin pops the field error and rewrites `cleaned_data`.** With `empty_values={"attachment": None}` an explicit None means *keep the existing reference* yet *discard the off-group upload*. `_cv_clear_group` currently assigns `cleaned[name] = None` which construct_instance passes to `save_form_data(instance, None)` → no change: fine. But `request.FILES` still carries the upload, and nothing in the plan states that the file upload is discarded *and* not validated when off. The behavior statement ("explicit None retains the reference") should add "and the posted file is neither validated nor stored."
- **LOW — M2M off-value through `save_m2m`.** `render_tree.py:233-234` calls `instance.save()` then `form.save_m2m()`. Django's `_save_m2m` only touches fields in `cleaned_data`; with `[]` it clears. Correct, but note that the main-form path (`super().cv_form_valid`) uses `form.save()`; both paths must be exercised, as the plan says. Fine as written.
- **LOW — plan test model is in the shared `tests/test1/app/models.py`.** Without a migrations dir this is syncdb-created at test DB setup; no migration needed. The browser fixture in plan 08 says it will create its own table separately; that is consistent.

**Suggestions.**
- Add a `media_root` fixture requirement to 02-02.
- State the FILES-discard semantics for the explicit-None file case.

**Risk: MEDIUM.** The approach is right; residual risk is in the breadth of the matrix and the storage/test hygiene gap.

---

## 06.4-03

**Summary.** Extends the existing `_ConditionalFindings` traversal correctly and the new ID `crud_views.E312` is unallocated (`checks.py` registers only E310/E311/W320/W321 at :64-93; `grep E312 src/` is empty). The W320 retirement is appropriate because its predicate (`null and blank`, `checks.py:141-149`) contradicts the new supported matrix (non-null Boolean=False, blank text=""). Scope is tight.

**Strengths.**
- `_collect_group_findings` already receives `form_class`/model (`checks.py:152-161`); the resolver can slot in there.
- The plan traverses form classes reachable through `FormSet` declarations (`klass.form`), which `_walk_formset` (`checks.py:130-138`) currently does not inspect for groups; that is the real coverage gap.

**Concerns.**
- **MEDIUM — nested-form static checks need the inline form's `base_fields`, but `cv_conditional_groups` on inline forms is not in the current traversal and the `declared` set at `checks.py:166` is computed only for the view's `form_class`.** The plan says "include form classes reachable from all FormSet declarations" but 03-01's acceptance ("including inline/custom declarations") needs an explicit statement that `declared`/`available_toggles` is recomputed per inline form class; otherwise E311 false positives are likely on inline forms whose toggle is injected.
- **MEDIUM — "retire W320" changes a registered check ID.** Phase 7 freezes check IDs; removing W320 is a public-surface change. The plan routes documentation to 09 but does not say whether the ID is *removed* or *kept-but-never-emitted*. Removal is a Breaking entry per the project's docs rule; the plan should decide.
- **LOW — "Active-only unsupported fields still need configuration suitable for being switched off."** Correct policy, but it means some currently passing projects will fail checks at startup after upgrade. This should be called out as Breaking in 09's inputs.

**Suggestions.**
- Specify per-form-class `declared` recomputation in 03-01.
- Decide W320 fate (remove vs. silent) and route the Breaking pairing to 09 explicitly.

**Risk: MEDIUM.**

---

## 06.4-04

**Summary.** This is the highest-value plan and its placement is right: the policy gate must live where every accepted `BaseInlineFormSet` subclass passes (`formsets.py:88-89` admits any Django `BaseInlineFormSet`), i.e. `XFormSet.is_valid` (`render_tree.py:200-203`), not `InlineFormSet.clean` (`inline_formset.py:111-118`). The "replacement row" risk in D-12 is not hypothetical: I traced it in source.

**Strengths.**
- Verified that forged/missing/foreign initial-row ids become *new* instances: Django's `_construct_form` falls through on a missing or unparsable pk and `_existing_object(pk)` returns `None` for a pk outside `get_queryset()` (`models.py:721-755`); Django's own `save_existing_objects` skips such forms (`:948-960`) but `render_tree.py:256-260` saves them if `has_changed()`, and `BaseInlineFormSet._construct_form` sets the FK to the current parent. So a forged foreign id creates a new row under the current parent with the posted data. The plan's "must not become an unauthorized create/replacement" is exactly right.
- Verified that edit-only extras are saved: Django's `save()` returns only `save_existing_objects` when `edit_only` (`models.py:814-815`); `render_tree.py:256-260` ignores that distinction.
- The two-pass `all_valid` (`formsets.py:365-369`) means errors appended during pass 1 are seen in pass 2; the plan's idempotency requirement is the correct complement because `full_clean` runs once (`formsets.py:131`, `formsets.py:365`) and appended nonform errors persist.

**Concerns.**
- **HIGH — no edit-only formset fixture exists anywhere in the test app.** `grep -rn edit_only tests/` finds only fakes in `test_conditional_checks.py:306-339` and the JS DOM helper. 04-01 requires "a real create/update request test" against an edit-only formset with both the package subclass and a native `BaseInlineFormSet`. The plan's `files_modified` lists neither `tests/test1/app/views_formset.py` nor a new fixture module; it relies on "existing test-local registry/URL cleanup patterns" (the `fr` fixture in `test_fragment_authorization.py:217-335`). That is workable but it is unstated scope: the executor must build URL-registered viewsets with `edit_only=True`, a restricted-queryset formset, and a native-subclass variant inside `test_formsets_policy.py`. Name it.
- **MEDIUM — appending to `_non_form_errors` after `is_valid()` must not break Django's `errors` caching for the re-render.** `formset.html:27` renders `x_formset.instance|as_crispy_errors`, which reads `non_form_errors()`. Appending to the existing `ErrorList` after `full_clean` works; replacing it would not because `is_valid()` (`formsets.py:379`) re-reads `self.non_form_errors()`. The plan should state "append to the existing list" to avoid an executor rebuilding it.
- **MEDIUM — existing-row identity check must use the parsed pk, not `cleaned_data["id"]`.** The hidden pk `ModelChoiceField` is built from `self.model._default_manager.get_queryset()` and validates existence anywhere, so `cleaned_data[pk]` can be a foreign instance. The plan says this ("not merely a broad ModelChoiceField queryset"); good. But also note `form.instance._state.adding` is the reliable "Django bound a persisted row" signal, and `_cv_prefix_identity` (`formsets.py:28-37`) already encodes this rule; reuse it.
- **LOW — DELETE-marked forged rows.** `render_tree.py:244-250` deletes when `form.instance.pk` is truthy. A forged foreign id yields instance pk `None` (unfetched), so no cross-parent delete occurs today; the plan's "including DELETE-marked rows" is still right because the generic error must be raised regardless.

**Suggestions.**
- Add the edit-only/native-subclass fixture construction to 04-01's action and acceptance explicitly.
- Specify "append to existing `_non_form_errors`" and "use `instance._state.adding` plus queryset membership" as implementation constraints.

**Risk: HIGH (correctness criticality), execution risk MEDIUM.** The plan has the right mechanism; the fixture gap is the thing most likely to stall it.

---

## 06.4-05

**Summary.** The ownership model (baseline ∨ any inactive bound ancestor, recomputed per owning form) is the right replacement for `apply()`'s last-writer-wins at `toggle.js:23-32`. The MutationObserver approach is viable in jsdom and Chromium, and the plan correctly front-loads a spike test. One timing detail in the native-reset design can pass in jsdom and fail in a real browser.

**Strengths.**
- Explicitly excludes fieldset-level disabling (which would also disable the four management inputs excluded at `toggle.js:13`).
- Focus fallback reuses the modal's usability predicate semantics (`modal.js:46-69`, `cvModalUsable`/`cvModalFocus`) by description; the plan asks for connected/hidden/inert/aria-hidden/disabled checks matching that helper.
- Reset cancellation checked at the deferred point, including later listeners, matches the WHATWG algorithm.

**Concerns.**
- **MEDIUM — "schedule synchronization after the default reset algorithm" must be a macrotask, not a microtask.** When a *user* activates a reset button, the browser dispatches `reset`; after each listener returns the JS stack is empty, so a microtask checkpoint runs *before* the UA performs the default reset of controls. A `queueMicrotask`/`Promise.then` resync would therefore read pre-reset `checked` state. In jsdom, `form.reset()` called from test code keeps the stack non-empty, so a microtask would run after reset and the unit test would pass. Only `setTimeout(…, 0)` (or `requestAnimationFrame`) is safe in both. 05-02 should name the macrotask explicitly; plan 08's keyboard reset case will catch a wrong choice, but late.
- **MEDIUM — observer scope on detached modal content.** `cvModalInject` (`modal.js:90-96`) dispatches `cv:modal:unload` while old nodes are attached, then `innerHTML = html`. The plan says to dispose observers on unload. MutationObservers on removed nodes are GC-safe, but `WeakMap` per-form bookkeeping keyed on a detached form is also fine. The risk is the *reverse*: 422 replacement injects a new `<form>` while the page-level `document` listener for `cv:modal:loaded` (`toggle.js:59-61`) calls the initializer; nothing there is wrong, but the plan must ensure the initializer runs on the *new* form root, and that `cv:modal:loaded` fires before modal.js's focus recovery (`modal.js:96-102`) so hiding does not strand focus mid-recovery. The plan says this; keep it as an explicit test.
- **LOW — external true→false while inactive.** With `attributeOldValue`, a record with oldValue `""` and current absence means "externally enabled". But if the library itself is currently holding `disabled` true, an external `el.disabled = false` is observable only if the external write happened while the library's observer was connected. The plan's "disconnect only around the library's synchronous writes after draining" handles this; the spike test should include this exact case.

**Suggestions.**
- Write "`setTimeout(0)` after `reset`" into 05-02.
- Add the "external enable while conditionally disabled" case to 05-01's spike list.

**Risk: MEDIUM.**

---

## 06.4-06

**Summary.** Correct diagnosis of the lifecycle defects: the controller is bound once on `form.cv-form` present at start (`formset.js:476`, `:638-645`), `XFormset` resolves content by global `$()` (`:130`), and `reorder_formsets` hides failures (`:600-611`). The submit-ordering analysis is right but the plan slightly overstates the modal interaction.

**Strengths.**
- `cv.initFormsets(root)` with a per-form `WeakMap` fixes two-same-prefix-forms and modal replacement at once.
- The `.each` early-return bug (`formset.js:603-606`) is real and would otherwise let a failed reorder submit.
- Stock Add visibility tied to `edit_only` in `control.html` plus handler-side capability checks matches D-07/D-11.

**Concerns.**
- **MEDIUM — the modal `defaultPrevented` concern is partly moot and partly real.** formset.js's handler is jQuery `.on("submit")` returning `false` (`:485-488`), which calls `stopPropagation` as well, so the document-level modal listener (`modal.js:227-233`) never fires on a formset reorder failure *today*. The real gap is that modal forms get no formset submit handler at all because binding happened at page start. Once the plan binds per form via native listeners (no `return false`), the document listener *will* run, so checking `event.defaultPrevented` in `modal.js` becomes necessary. The plan's wording should state that the check is needed *because* of the new binding model, not that it is a pre-existing hole.
- **MEDIUM — double-binding risk on `row-added`.** `XForm.add()` calls `this.ctl.add_form_control_for_new_rows(rows)` (`formset.js:341`) *and then* dispatches `row-added` (`:342`). If the initializer also listens for `row-added` and binds controls, rows get two handlers unless binding is delegated at form level. The plan says "delegated or namespaced handlers"; it should mandate delegated binding (one click handler per form, matching `.cv-form-ctrl-*` by `closest`) and drop `add_form_control_for_new_rows`, otherwise the "no duplicate action handlers" acceptance is at risk.
- **LOW — existing tests construct `new window.cv.CrudViewsFormset()` directly** (`tests/js/formset.test.js:296-363`). The plan keeps old seams internal; those tests will still pass only if the constructor remains callable without arguments. If the constructor becomes form-scoped, those tests need updating; the plan's `files_modified` includes `formset.test.js`, so this is covered but unstated.

**Suggestions.**
- Mandate delegated control binding and remove the per-row rebinding call.
- Clarify the `defaultPrevented` rationale.

**Risk: MEDIUM.**

---

## 06.4-07

**Summary.** Minimal, correct repair. `get_template` passes `index=0` (`formsets.py:513`) while `_cv_validate_fragment_coordinates` already computes declared child indices for *ancestors* (`:446`), so deriving the selected formset's own index from `list(chain[-2].children).index(key_path[-1])` is a one-line extension of existing logic. The characterization test is exactly as described (`test_fragment_authorization.py:1184-1185`).

**Strengths.**
- Fixture already exists: `two_child_formsets()` with `notes`/`memos` (`:116-128`) and `three_level_formsets()` for deeper variants (`:131-158`).
- Keeps `_cv_fragment_pk`, grammar and ancestry unchanged.

**Concerns.**
- **MEDIUM — the `end_at_rows` imbalance is demonstrable now, not conditionally.** `formset.html:56` reads `x_formset.end_at_rows`; `XFormSet` (`render_tree.py:93-102`) defines `render_rows_only` only. Django templates resolve the missing attribute to empty, so every fragment emits four unmatched closing tags. Browsers drop stray end tags in `insertAdjacentHTML`, which is why it has gone unnoticed. 07-02's "align closing behavior … only where the regression demonstrates unbalanced fragment output" should simply be "fix the closing condition to `render_rows_only` and add the parsed-DOM test"; the conditional phrasing invites an executor to skip a known defect.
- **LOW — `_cv_validate_fragment_coordinates` docstring and `docs/reference/formsets.md:205-210` both state the A19 limitation.** The plan routes docs to 09 but the docstring at `formsets.py:417-418` is source and should be updated in 07-01.

**Suggestions.**
- Make the `end_at_rows` fix unconditional in 07-02.
- Update the docstring in 07-01.

**Risk: LOW.**

---

## 06.4-08

**Summary.** The browser packet is the integrating acceptance for the phase and is well-specified. It follows the proven runner (`tests/browser/modal-focus.cjs`: port probe `:77-80`, runtime discovery `:81-86`, owned child `:88-100`, evidence checker `:37-67`). The main gaps are fixture-engineering details that the prior 06.3 fixture solved differently.

**Strengths.**
- Real HTTP, real DB, zero-mock requirement with a save-hook counter and state endpoint; evidence checker with required-assertion names mirrors `modal-focus.cjs:46-55`.
- Minimal non-Bootstrap templates exercise the documented projection, which is the only real test that themes can consume it.

**Concerns.**
- **MEDIUM — the fixture server lives in `tests/browser/` while its analog lives under `.planning/` (`modal-focus.cjs:88` spawns `${phase}/17-evidence/server.py`).** Moving it into `tests/browser/` is better for Phase 7, but `pytest` collection (`tests` root) and Ruff will now see it; ensure it is not collected as a test module (name it without `test_` prefix, which the plan does) and that it passes lint, since plan 10 runs touched-file Ruff.
- **MEDIUM — "private BrowserMemo fixture model … create/drop the fixture-only table in its isolated DB."** The 06.3 fixture used `call_command("migrate", run_syncdb=True)` on a temp SQLite file (`17-evidence/server.py:20,37`). A model defined outside an `INSTALLED_APPS` app label cannot be synced that way; it needs either a tiny fixture app in `tests/browser/` or `schema_editor.create_model`. The plan should pick one; otherwise the executor may put the model in the shared `tests/test1/app/models.py`, which plan 02 owns in wave 1 and which the SOURCE-AUDIT says is isolated from browser fixtures.
- **MEDIUM — the runner reads a Node runtime path from `.planning/phases/06-form-button-leaf/06-JS-RUNTIME.json` (`modal-focus.cjs:11-17`) and hard-codes Playwright/Chromium paths (`:82-83`).** The new runner will inherit the same machine-specific defaults. Acceptable for this repo's established practice, but the plan should require env-var overrides (as the analog does) and record them in evidence.
- **LOW — port.** Analog uses 8143; the plan says "separate port" without a number; both runners are in plan 10's gate, so they must not collide.
- **LOW — "JS-disabled/direct tampered HTTP POST"** is best done via `context.request.post` with the session cookie and CSRF token rather than a JS-disabled page; either works, but the evidence should capture the server-received payload (the plan says so).

**Suggestions.**
- Decide the fixture-model mechanism (tiny app under `tests/browser/` is simplest and keeps `models.py` ownership clean).
- Fix the port number and env overrides in the plan.

**Risk: MEDIUM.** High engineering effort; the design is sound.

---

## 06.4-09

**Summary.** Documentation plan is proportionate and correctly executable-test-backed (analog `tests/test1/test_delete_migration_docs.py` exists). It correctly refuses to promote `XForm`/`XFormSet` constructors. The Breaking inventory needs to include two items the earlier plans create but do not flag.

**Strengths.**
- Enumerates the real projection (`render_tree.py:173-189` JSON keys; `formset.js:319-324` request keys; `get_template` response `:520`).
- Links A19 limitation removal (`docs/reference/formsets.md:205-210`) to 07/08 evidence rather than asserting it.

**Concerns.**
- **MEDIUM — Breaking items are incomplete relative to the upstream plans.** Besides the bound-marker change (01), two further changes are user-visible breaks: (a) W320 retirement/E312 introduction can turn previously passing projects into startup errors (03); (b) `render_tree.save` behavior change: edit-only extras and forged ids that were previously *saved* are now rejected (04). The migration guide must tell users what used to happen and what now happens. The plan lists "strict pre-save row rejection as applicable" for migration but not the check-ID change.
- **LOW — `.venv/bin/mkdocs build --strict` is the verify command; `mkdocs.yml` nav must already include the touched pages.** They are existing pages, so fine; new anchors referenced from `migrating-1.0.md` must exist or strict mode fails. Normal risk.

**Suggestions.**
- Add W320→E312 and the save-behavior change to 09-02's Breaking list explicitly.

**Risk: LOW.**

---

## 06.4-10

**Summary.** Mirrors the 06.3 evidence pattern (`06.3-REGRESSION-GATE.md`, `06.3-MATRIX.md` exist) with checker self-tests via deliberate corruption, which is good practice. The plan correctly refuses to claim the Python 3.13–3.15 matrix. Interpreters are present.

**Strengths.**
- `.nox/tests-3-12-django-5-2` and both `crispy_floor` envs exist; `PYTHONPATH="$PWD/src:$PWD"` import-identity assertion matches 06.3 practice.
- Honors only the enumerated CSP/golden exclusions (`06.3-REGRESSION-GATE.md:4-5,14,38`).

**Concerns.**
- **MEDIUM — the `crispy_floor` envs pin crispy floors; the full-suite "three series" run therefore mixes one floor-pinned 4.2 env, one floor-pinned 6.0 env and one current-pin 5.2 env.** `noxfile.py:96-106` shows `crispy_floor` deselects `CRISPY_FLOOR_DESELECT` tests. Plan 10's "full tests in these three environments" must apply the same deselection on the floor envs or it will record a known golden failure as new. The 06.3 gate handled this; the plan should cite the exact deselect expression rather than "honor only the exact documented existing exclusions".
- **LOW — both browser runners (new `conditional-formsets.cjs` and `modal-focus.cjs --case all`) hard-code loopback ports; running them sequentially is fine, but the evidence runner must not launch them concurrently.**
- **LOW — "descriptor-less prohibition status from 02 as flagged-unverified"** is correctly carried; nothing to add.

**Suggestions.**
- Quote the `CRISPY_FLOOR_DESELECT` expression and the golden node IDs in 10-01's action.
- State sequential execution for the two browser runners.

**Risk: LOW–MEDIUM.**

---

## Cross-plan assessment

**Dependency ordering.** Verified against `files_modified`: wave-1 plans 01 (layout/toggle/formsets/render_tree/templates) and 02 (group.py/models.py/persistence tests) are disjoint. Wave 2 (03: checks/group; 04: render_tree/formsets; 05: toggle.js) is disjoint. 01→04 and 01→05 shared-path sequencing is correct. 06→07 ordering for `formset.test.js` is correct. 08 depends on 03 and 07, transitively on all repairs. No ordering defects found.

**Scope.** Nothing here exceeds A1–A7/A19 plus D-01–19. A8, jQuery removal and presentation adapters stay excluded. The one implicit scope item is the edit-only fixture infrastructure (plan 04), which is necessary rather than creep.

**Security.** The two security-critical plans (02 and 04) are grounded in source-confirmed defects: default-restoring clears (`construct_instance` skip rule) and render-tree saves bypassing Django's `edit_only`/unfetched-instance guards. Their gates sit before the atomic block at `mixins.py:114`, meeting D-18.

**Performance.** Per-control MutationObserver and per-form controllers are proportionate; `_existing_object` already materializes the queryset once per formset, so the membership check adds no extra query if it reuses `get_queryset()`.

**Do the plans achieve the phase goal?** Yes, if executed as specified. The seven roadmap success criteria map to concrete producer tasks, and the browser packet integrates them. The findings above are refinements that prevent stalls or late discovery, not design reversals.

**Overall risk: MEDIUM.** Highest-attention items, in order:
1. Plan 04 fixture gap (no edit-only formset exists in the test app).
2. Plan 05 reset timing (macrotask, not microtask).
3. Plan 01 old-contract JS test (`toggle.test.js:67`) and Pydantic private field.
4. Plan 08 fixture-model mechanism and runtime path overrides.
5. Plan 09 Breaking inventory (W320/E312 and save-behavior change).
