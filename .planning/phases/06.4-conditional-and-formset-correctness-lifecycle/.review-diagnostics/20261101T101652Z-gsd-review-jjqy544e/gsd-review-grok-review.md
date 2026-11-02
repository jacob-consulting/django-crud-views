I'll review all ten plans against current source and the A18 opt-in contract, without editing files.
Commit matches. Next I’ll trace the tracer opt-in and the save, fragment, and formset paths the plans claim to repair.
## 06.4-01

Summary: Exact owning-form checkbox identity, plus an opt-in Node tracer that ordinary Python collection never runs. Sufficient for COND-01 and A18's collection boundary.
Strengths: `layout.py:29` emits the raw field; `toggle.js:15-20` suffix-matches and `toggle.js:36-44` marks a group wired before the checkbox exists. `06.4-01-PLAN.md:114-116` emits `form.add_prefix`, matches by equality, retries misses, and sets only `test_tracer_rendered_conditional_round_trip.__test__` from `CV_CONDITIONAL_TRACER=1`. Pytest collects that function only when `__test__` is true. Import stays inert; the disabled command clears the opt-in and empties `PATH`.
Concerns: None
Suggestions: None
Risk Assessment: Low. Enabled acceptance still depends on the machine manifest at `06-JS-RUNTIME.json:7`, which is correct once opted in.

## 06.4-02

Summary: Field-aware off values and the inline save gate that `has_changed()` misses. H1 remains closed.
Strengths: `group.py:36-37,78-84` clears to `None` with no server-disabled exception. `render_tree.py:259` saves only `has_changed()`. `06.4-02-PLAN.md:93-111` applies resolved values in cooperative `_post_clean` and adds `_cv_conditional_requires_save` for an existing off row, including FileField/ImageField reference semantics without Pillow.
Concerns: None
Suggestions: None
Risk Assessment: Low. Persistence proof is still planned, not landed.

## 06.4-03

Summary: Shared resolver becomes `E312` at check time and `ImproperlyConfigured` at runtime. A02 remains closed.
Strengths: `checks.py:79-85,141-149` warns only on non-null/blank and walks one form namespace. `06.4-03-PLAN.md:82-96` recomputes names per inline form and keeps inherited nonfield/model errors authoritative.
Concerns: None
Suggestions: None
Risk Assessment: Low.

## 06.4-04

Summary: Mandatory row policy on the runtime tree, including native `BaseInlineFormSet` subclasses. H1/H3 remain closed.
Strengths: `formsets.py:12,88` accepts Django's `BaseInlineFormSet`, while `formsets.py:148-160` always passes `formset`/`parent_form`. Package `InlineFormSet.clean` cannot cover that. `formsets.py:348-369` and `mixins.py:97-116` validate before the atomic save. `06.4-04-PLAN.md:86-100` owns registered routes, a kwargs-absorbing native adapter, policy spies, and zero saves.
Concerns: None
Suggestions: None
Risk Assessment: Low. Constructor TypeError is an explicit negative-control failure, not a silent pass.

## 06.4-05

Summary: Composed disabled ownership, post-default native reset, and stranded-focus recovery. A04 remains closed.
Strengths: `toggle.js:26-30` writes `disabled` unconditionally and skips buttons. `06.4-05-PLAN.md:74-88` uses an observer that does not recapture library writes, a macrotask reset check including later `preventDefault`, and focus movement only when a hide strands the active control.
Concerns: None
Suggestions: None
Risk Assessment: Low. Chromium reset/same-value proof stays in plan 08.

## 06.4-06

Summary: One controller per form, stock edit-only Add, and modal submit ordering. A11/A12/A16 remain closed.
Strengths: `control.html:18-22` always renders Add. `formset.js:130,473-489,597-610,637-638` interpolates prefixes, binds every `form.cv-form`, and returns true after a jQuery `each` `return false`. `modal.js:227-232` submits without reading `defaultPrevented`. `formsets.py:294-298` accepts only `^[a-z\-]+$`. `06.4-06-PLAN.md:95-111` scopes lookups by exact attribute equality, rejects `line.items:detail`, and stops fetch after a failed reorder.
Concerns: None
Suggestions: None
Risk Assessment: Low.

## 06.4-07

Summary: Declaration-derived sibling index and raw wrapper balance before DOM repair. H2 remains closed.
Strengths: `formsets.py:181-188` enumerates child indexes, but `formsets.py:513` always passes `index=0`. The stale note is `formsets.py:417-418`. `formset.html:4` opens on `render_rows_only`; `formset.html:56` closes on missing `end_at_rows`. `test_fragment_authorization.py:1154-1185` characterizes the mismatch. `06.4-07-PLAN.md:82-96` replaces that with a POST/DB round trip and a raw tag stack plus stray-close negative control.
Concerns: None
Suggestions: None
Risk Assessment: Low.

## 06.4-08

Summary: Real HTTP/Chromium acceptance for both themes, including the H1/H2/A04/A10/A15 assertion IDs.
Strengths: `06.4-08-PLAN.md:107-133` requires no mocked fetch, raw `html` balance before insertion, user-activated reset, same-value disabled ownership, and FileField upload discard distinct from reference-only ImageField. Ports stay 8144 vs modal-focus 8143.
Concerns: None
Suggestions: None
Risk Assessment: Medium execution cost, not a plan gap. The fixture must follow `17-evidence/server.py:37` (`run_syncdb=True`) because `tests/test1/app` has no migrations; plan 08 already requires isolated table creation.

## 06.4-09

Summary: Executable docs and Phase 7 inventory after 07/08 evidence. A08/A13/A15 remain closed.
Strengths: `examples/bootstrap5/conditional/models.py:8` still promises universal `None`/`W320`. `render_tree.py:173-189` is the projection to document, including grammar `pk` versus row identity. `06.4-09-PLAN.md:98-114` extracts recipes, pairs Breaking with `docs/migrating-1.0.md`, and does not publish constructors.
Concerns: None
Suggestions: None
Risk Assessment: Low.

## 06.4-10

Summary: Three-series enabled tracer success, missing-runtime failure, and Node-free ordinary full suites. A18's acceptance half is specified.
Strengths: `.github/workflows/tests.yml:18-24` and `noxfile.py:13-19` stay Python-only. `06.4-10-PLAN.md:97-111` and `06.4-VALIDATION.md:120-128` require, per cached 4.2/5.2/6.0 interpreter, a passed tracer with `record_property` provenance, a failed exact-node missing-runtime control, and an ordinary suite with opt-in removed, empty `PATH`, and no tracer case. `--check` rejects skipped, failed, or zero-selected tracer records. Pytest 9.2.0 still provides `record_property`.
Concerns: None
Suggestions: None
Risk Assessment: Low as a plan. Evidence files do not exist yet; that is execution, not a remedy gap.

## Cross-plan summary

The ten plans at `83c4f35` still target the unfixed mechanisms above and keep H1–H3 and A01–A17 closed. Dependencies put shared edits to `render_tree.py`, `formsets.py`, `toggle.js`, and `formset.test.js` in order. A18 is one opt-in, not a second tracer.

## Prior-item closure ledger

| ID | Disposition |
|---|---|
| H1 | Closed. No regression. `06.4-02-PLAN.md:111`, `06.4-04-PLAN.md:90`, `06.4-08-PLAN.md:107-133`, `06.4-10-PLAN.md:97` still require real `XFormSet.save` when `has_changed()` is false. |
| H2 | Closed. No regression. `06.4-07-PLAN.md:96-100` aligns the close predicate and checks raw balance before parse. |
| H3 | Closed. No regression. `06.4-04-PLAN.md:86-91` still owns reachable native/package HTTP fixtures and policy spies. |
| A01–A14 | Prior incorporated/deferred dispositions preserved. No concrete regression. |
| A15 | Closed. No regression. Reference-only ImageField plus real FileField upload discard remains in plans 02, 08, and 09. |
| A16 | Closed. No regression. `06.4-06-PLAN.md:95-100` keeps `^[a-z\-]+$` and exact prefix equality. |
| A17 | Closed. No regression. Enabled resolver precedence and hard failure stay inside the opted-in tracer. |
| A18 | **Signed off.** `CV_CONDITIONAL_TRACER=1` is the only collection switch (`06.4-01-PLAN.md:116`). Ordinary import does no manifest/Node/jsdom work. Once enabled, missing runtime fails and is not skipped. Plan 10 requires that passed case, the missing-runtime failure, and a Node-free full suite on each cached Django series (`06.4-10-PLAN.md:99`, `06.4-VALIDATION.md:107-128`). CI/nox need no Node provisioning. |

## Unresolved concerns

None.
