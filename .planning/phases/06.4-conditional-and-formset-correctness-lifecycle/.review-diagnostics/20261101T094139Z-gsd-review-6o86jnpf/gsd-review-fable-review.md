Review complete. All ten plans at `75c1fea` were checked against current source; no HIGH remains, two new MEDIUM gaps were found.

## 06.4-01

**Summary.** Replaces the form-wide suffix lookup with the exact bound checkbox name, adds `cv.initConditional(root)`, and pushes the owning main form's bound name into top-level conditional formset wrappers.

**Strengths.** Every targeted defect is real in current source: suffix selector at `src/crud_views/static/crud_views/js/toggle.js:15-21`, wired flag set before resolution at `toggle.js:36-44`, unprefixed context at `src/crud_views/lib/conditional/layout.py:29`, and declaration-name projection at `src/crud_views/lib/formsets/render_tree.py:195-198` consumed by `src/crud_views/templates/crud_views/formsets/formsets.html:5`. The renderer-to-persistence tracer at `06.4-01-PLAN.md:112` is the right discriminator. Keeping nested `ConditionalFormSet` on E310 at `06.4-01-PLAN.md:128` matches `src/crud_views/checks.py:59-66`.

**Concerns.**
- LOW. The pytest tracer spawns a Node subprocess but names no runtime resolution. `tests/browser/modal-focus.cjs:12-17` resolves Node through the JS runtime manifest and re-execs. Node is on this shell's PATH at `/home/alex/.nvm/versions/node/v24.21.0/bin/node`, but a nox or CI shell without nvm would fail obscurely. Also, no helper script path appears in the task's files list, so either an inline `-e` script via stdin or a declared helper path is needed.
- LOW. `tests/js/toggle.test.js:67-71` asserts suffix matching and must be rewritten, not merely extended. The plan implies this but does not say it.
- LOW. `toggle.js:41` falls back to `document` when no enclosing form exists. The plan should state the scope used for groups outside any `<form>` so the ambiguity rule stays defined.

**Suggestions.** Resolve Node via the `06-JS-RUNTIME.json` path with a `CV_FOCUS_NODE` override and fail clearly. Name the suffix test as a required rewrite.

**Risk Assessment.** MEDIUM. Costly reversibility is correctly declared at `06.4-01-PLAN.md:108`; coverage is adequate.

## 06.4-02

**Summary.** Field-aware clearing resolver, server-disabled precedence, model-construction ordering through `_post_clean`, and the H1 save-predicate repair.

**Strengths.** H1 is real: `render_tree.py:259` gates existing-row saves on `form.has_changed()`, and Django's `FileField.has_changed` returns False whenever no upload is present at `.nox/crispy_floor-3-12-django-6-0/lib/python3.12/site-packages/django/forms/fields.py:703-704`. The universal `None` default at `src/crud_views/lib/conditional/group.py:36-37` and the clear-after-pop at `group.py:78-84` match the plan's diagnosis. The private `_cv_conditional_requires_save` signal, captured before instance mutation and consumed only for persisted rows, is specified at `06.4-02-PLAN.md:96` and `:110` with an explicit `has_changed() is False` assertion. `tests/test1/app` has no migrations directory, so the new test model needs no migration. A01 is addressed by `override_settings(MEDIA_ROOT=tmp_path)` plus isolated per-field storage at `06.4-02-PLAN.md:110`.

**Concerns.**
- MEDIUM. Pillow is not installed in any cached environment or in `.venv`, and is not declared in `pyproject.toml`, `uv.lock` or `noxfile.py`. Task 02-02 requires an `ImageField` and explicitly requires discarding off-group uploaded data. Django's form `ImageField.to_python` imports Pillow for any non-empty upload at `django/forms/fields.py:724-729`, and the model field emits `fields.E210` under any explicit system check at `django/db/models/fields/files.py:439-451`. Test database creation and the fixture server analog both use `call_command("migrate")`, which defaults `skip_checks=True` at `django/core/management/__init__.py:192-193`, so reference-only image cases run, but the upload-discard image case cannot. The plan's threat register forbids installs without the legitimacy audit and checkpoint. The executor would have to install silently or skip a required case.

**Suggestions.** Decide explicitly: either add Pillow to the `test` extra through the T-06.4-SC audit and checkpoint, or bound `ImageField` coverage to reference clearing with no uploaded image bytes and say so in 02, 08 and 09.

**Risk Assessment.** MEDIUM. The persistence design is sound; the prerequisite gap is the only execution blocker.

## 06.4-03

**Summary.** New E312 for unsupported automatic clearing, retirement of W320, and per-form-class namespaces for inline checks.

**Strengths.** A02 is real: `src/crud_views/checks.py:164-176` derives `declared` from the main `form_class` only and never inspects inline form classes. The null-or-blank-only W320 heuristic at `checks.py:141-149` contradicts the new matrix. The per-class recomputation at `06.4-03-PLAN.md:86` is the correct remedy.

**Concerns.**
- LOW. Existing W320 assertions at `tests/test1/test_conditional_checks.py:298` and `:373-393` must be replaced. The acceptance text at `06.4-03-PLAN.md:85` says E310/E311/W321 tests stay green but does not name the W320 rewrite, though the file is owned.
- LOW. `ConditionalFormSet` toggles legitimately live on the main form, checked at `checks.py:118-123` with the main namespace. The instruction to never carry the main namespace into inline checks should be scoped to `ConditionalGroup` declarations on inline forms, so the formset-toggle E311 check is not broken.

**Suggestions.** Add one sentence for each of the two points above.

**Risk Assessment.** LOW to MEDIUM.

## 06.4-04

**Summary.** Mandatory active row-policy gate for edit-only extras and existing-row identity, with reachable test-local HTTP fixtures for package and native formset classes.

**Strengths.** H3 is real and the remedy fits: `src/crud_views/lib/formsets/formsets.py:60` accepts any `BaseInlineFormSet`, while `formsets.py:148-160` passes `formset=` and `parent_form=` kwargs that Django's `BaseFormSet.__init__` does not accept at `django/forms/formsets.py:81-91`. `rg edit_only tests/test1/app` finds no declaration, so the test-local `edit_only=True` routes at `06.4-04-PLAN.md:90` are necessary. D-12 is real: a missing or foreign pk makes Django bind a new instance at `django/forms/models.py:741-757`, and `render_tree.py:256-260` would then insert it. The gate sits in the traversal every class passes at `render_tree.py:200-203`, before the atomic save at `src/crud_views/lib/formsets/mixins.py:114-128`. Positive GET and POST before each negative family at `06.4-04-PLAN.md:91` rules out construction failures masquerading as rejections.

**Concerns.** None.

**Suggestions.** None required.

**Risk Assessment.** MEDIUM. Security-relevant, well specified.

## 06.4-05

**Summary.** Per-control disabled ownership with a mutation observer, native reset synchronization after the default action, and stranded-focus recovery.

**Strengths.** `toggle.js:23-31` writes `disabled` unconditionally and `toggle.js:46-49` gives each group a single owner, so both nesting orders and external baselines are currently broken. A04 is addressed at `06.4-05-PLAN.md:92` with a macrotask and a `defaultPrevented` check that tolerates later listeners, and 08 supplies real reset-button activation. Focus recovery mirrors `src/crud_views/static/crud_views/js/modal.js:57-69`.

**Concerns.** None. The observer drain-and-disconnect protocol at `06.4-05-PLAN.md:78` is implementable in jsdom and Chromium.

**Suggestions.** None required.

**Risk Assessment.** MEDIUM. Complex but bounded JavaScript.

## 06.4-06

**Summary.** Per-form formset controllers behind `cv.initFormsets(root)`, capability-aware stock Add, submit ordering with the modal listener, and exact prefix lookup.

**Strengths.** All defects confirmed: the global constructor binds every form at `src/crud_views/static/crud_views/js/formset.js:473-489`; `reorder_formsets` swallows a failed child because `return false` only breaks the jQuery `each` at `formset.js:614-626`; the page-wide control lookup assumes `edit_only: false` at `formset.js:540-547`; `control.html:19-22` renders Add unconditionally; the modal listener calls `preventDefault` and fetches without checking `defaultPrevented` at `modal.js:227-233`. A11 is addressed by the Django-rendered control test at `06.4-06-PLAN.md:99` and `:102`.

**Concerns.**
- MEDIUM. The A12 regression names a supported key containing punctuation, `line.items:detail`, at `06.4-06-PLAN.md:99`, and the acceptance text at `:100` requires punctuation-bearing supported prefixes to resolve. `FormSets.check_keys` rejects any key outside `^[a-z\-]+$` at `formsets.py:294-298`, and prefix keys are `None`, digits or UUID hex plus hyphenated indices. No supported prefix carries such punctuation, so the criterion is unsatisfiable without loosening the key grammar, which the same task forbids. The underlying remedy, attribute equality instead of interpolation into selectors such as `formset.js:160`, remains correct.

**Suggestions.** Replace the example with supported shapes: a UUID identity prefix, a deep hyphenated nested prefix, and identical prefixes in two forms, plus one unit test proving lookups compare attribute values rather than interpolate them, and one assertion that `check_keys` still rejects punctuation keys.

**Risk Assessment.** MEDIUM.

## 06.4-07

**Summary.** Declaration-derived selected-child index in `get_template`, the unconditional closing-wrapper repair, raw wrapper-balance assertions, and the A19 round trip.

**Strengths.** H2 is real and now unconditional: `formset.html:4` opens on `render_rows_only` but `formset.html:56` closes on `end_at_rows`, which no `XFormSet` field defines at `render_tree.py:93-102`, so rows-only fragments always emit stray closing tags. `06.4-07-PLAN.md:100` requires a raw token-stack check with a stray-close negative control before any parser. The stale docstring at `formsets.py:417-418` is owned at `06.4-07-PLAN.md:86`. `formsets.py:513` passes `index=0`, and `formsets.py:181-188` already enumerates child positions, so the derivation is cheap. The characterization at `tests/test1/test_fragment_authorization.py:1180-1181` is correctly treated as non-evidence.

**Concerns.** None.

**Suggestions.** None required.

**Risk Assessment.** LOW to MEDIUM.

## 06.4-08

**Summary.** Real HTTP and Chromium acceptance with a disposable server, stock and native themes, and the required review-regression evidence table.

**Strengths.** The runner analog supports every claimed property: Node re-exec at `tests/browser/modal-focus.cjs:12-17`, port probe and env overrides at `:76-83`, disposable SQLite via `migrate` at `.planning/phases/06.3-delete-protection-and-write-boundary-integrity-issue-282/17-evidence/server.py:37`, and port 8143 at `server.py:129`. A06, A07, A04 and A10 are addressed at `06.4-08-PLAN.md:119` and `:133`, and the H1 and H2 assertion IDs are explicit at `:107-108`.

**Concerns.**
- MEDIUM, shared with 02. `BrowserConditionalRecord` carries an `ImageField`. Startup through `call_command("migrate")` skips checks, and the `inline-file-clear-unchanged` case needs no upload, so the required assertions can pass without Pillow. Any image-upload case, or any explicit `check` invocation in the server, fails without Pillow. The plan must inherit whatever decision 02 makes and must not add a `check` call.

**Suggestions.** State the Pillow decision in the fixture-model description and keep startup on `call_command("migrate")`.

**Risk Assessment.** MEDIUM to HIGH. Largest integration surface, well instrumented.

## 06.4-09

**Summary.** Executable documentation, migration pairing, and the Phase 7 public-surface inventory.

**Strengths.** A08 confirmed: `examples/bootstrap5/conditional/models.py:8` still promises universal `None` and W320. A13 confirmed: `render_tree.py:67` emits the enum spelling while `:188` emits the regex grammar. `docs/reference/conditional.md:31` carries the wording to correct, and `docs/reference/formsets.md:206-210` carries the limitation note to reconcile. `.venv/bin/mkdocs` exists; `tests/test1/test_delete_migration_docs.py` exists as analog. `conditional.md` is the only docs page listing W320, W321 and E311, so ownership is complete.

**Concerns.**
- LOW. If 02 bounds `ImageField` support, the clearing matrix must say so.

**Suggestions.** Tie the documented image support bound to 02's decision.

**Risk Assessment.** LOW.

## 06.4-10

**Summary.** Three-series evidence runner and checker, browser preservation, and A19 acceptance reconciliation.

**Strengths.** All named interpreters exist: `.nox/crispy_floor-3-12-django-4-2`, `.nox/tests-3-12-django-5-2`, `.nox/crispy_floor-3-12-django-6-0`, plus `.venv/bin/ruff` and `.venv/bin/mkdocs`. A07 sequencing at `06.4-10-PLAN.md:96` and the required both-theme assertion set are explicit. The A19 note to amend exists at `.planning/phases/06.2-request-authorization-and-write-integrity/06.2-ACCEPTANCE.md:304`. Corruption controls for the checker are a good addition.

**Concerns.** None.

**Suggestions.** None required.

**Risk Assessment.** LOW to MEDIUM.

## Cross-plan summary

The dependency graph and shared-file ownership remain coherent. All three prior HIGHs now have unconditional, executable remedies with discriminating evidence, and every actionable prior item has a concrete task. The fresh review found no HIGH. Two MEDIUM gaps would stall execution as written: an undeclared Pillow prerequisite behind the `ImageField` fixtures, and an A12 regression that names a key shape the key validator rejects.

`CYCLE_SUMMARY: current_high=0 current_actionable=5`

## Prior-item closure ledger

| Item | Verdict | Evidence |
|---|---|---|
| H1 | Closed | `06.4-02-PLAN.md:96,110` signal before `_post_clean`, consumed in `XFormSet.save`; `04-PLAN.md:90`; `08-PLAN.md:107`; `10-PLAN.md:96`. Source premise `render_tree.py:259`, `fields.py:703-704`. |
| H2 | Closed | `06.4-07-PLAN.md:100` unconditional predicate, raw stack, negative control; `07-PLAN.md:86` docstring; `08-PLAN.md:108`. Source premise `formset.html:4,56`, `render_tree.py:102`. |
| H3 | Closed | `06.4-04-PLAN.md:90-91` test-local routes, `edit_only` declarations, native adapter, positive-path proof. Source premise `formsets.py:148-160`, Django `formsets.py:81-91`. |
| A01 | Closed | `06.4-02-PLAN.md:110`. |
| A02 | Closed | `06.4-03-PLAN.md:86`. |
| A03, A05, A09 | No entry in the prior consensus table | Nothing to close. |
| A04 | Closed | `06.4-05-PLAN.md:92`; `08-PLAN.md:133`. |
| A06 | Closed | `06.4-08-PLAN.md:119`. |
| A07 | Closed | `06.4-08-PLAN.md:119`; `10-PLAN.md:96`. |
| A08 | Closed | `06.4-09-PLAN.md:102`. |
| A10 | Closed | `06.4-08-PLAN.md:133`. |
| A11 | Closed | `06.4-06-PLAN.md:99,102`. |
| A12 | Closed with correction needed | Remedy correct; example and acceptance wording conflict with `formsets.py:294-298`. See M2. |
| A13 | Closed | `06.4-09-PLAN.md:102`. |

## Unresolved concerns, deduplicated

| ID | Severity | Plans | Required plan change |
|---|---|---|---|
| M1 | MEDIUM | 02, 08, 09 | Decide the Pillow prerequisite: add it to the `test` extra through the T-06.4-SC audit and checkpoint, or bound `ImageField` coverage to reference clearing without uploaded image bytes and document that bound. Keep the fixture server on `call_command("migrate")` with no explicit `check`. |
| M2 | MEDIUM | 06 | Replace `line.items:detail` and the "punctuation-bearing supported prefixes" acceptance with supported shapes and a direct attribute-equality unit test; optionally assert `check_keys` rejects punctuation keys. |
| L1 | LOW | 01 | Specify Node resolution for the pytest subprocess tracer via the JS runtime manifest or `CV_FOCUS_NODE`, with a clear failure, and declare or inline the helper script. |
| L2 | LOW | 03 | Name the W320 test rewrite at `tests/test1/test_conditional_checks.py:298,373-393` as required. |
| L3 | LOW | 03 | Scope the namespace rule so `ConditionalFormSet` toggles keep the main-form namespace while inline `ConditionalGroup` checks use their own. |
