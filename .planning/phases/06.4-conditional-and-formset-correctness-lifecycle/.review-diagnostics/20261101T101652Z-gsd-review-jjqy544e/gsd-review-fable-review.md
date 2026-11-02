# Cross-AI Plan Review — Phase 6.4, cycle 4/6, commit `83c4f35`

Read-only review with repository access. Source lines below are from the current checkout at `83c4f35`. Direct execution of the cached interpreters was blocked by the sandbox, so interpreter facts come from installed `dist-info` metadata and the installed pytest source rather than from running Python.

## 06.4-01

**Summary.** Exact bound-name identity from `ToggleGroup` through shipped `toggle.js` to a real ModelForm save, plus bound names on top-level conditional formset wrappers. Owns the A17/A18 tracer collection boundary.

**Strengths.**
- Root causes confirmed in source: `layout.py:29` emits the unprefixed `self.toggle_field`; `toggle.js:17-19` suffix-matches `[name$="-<name>"]`; `toggle.js:36-39` sets `__cvToggleWired` before resolving, so a missing toggle can never be retried; `toggle.js:41` scopes to `closest("form") || document`.
- The wrapper gap is real: `formsets.html:4-5` reads `x_formset.cv_toggle_field`, which `render_tree.py:195-198` derives from the declaration, not from the owning form. `FormSet.init` has the main form in hand (`formsets.py:144-152`), so the plan's `cv_bound_toggle_field` placement (`06.4-01-PLAN.md:134`) is the right seam.
- Server authority is unaffected by the rename: `ModelFieldToggle.is_on` reads cleaned data by unprefixed field name, so only rendering changes.
- A18 mechanics hold. Installed pytest 9.2.0 gates function collection on `elif getattr(obj, "__test__", True):` at `.nox/crispy_floor-3-12-django-6-0/lib/python3.12/site-packages/_pytest/python.py:264`. A function with `__test__ = False` is never collected and produces no skip record, which is exactly what the "no skipped tracer" evidence needs (`06.4-01-PLAN.md:116`).
- The Node-free disabled route (`06.4-01-PLAN.md:121`) is survivable by the existing suite: every subprocess call in tests uses `sys.executable` (`tests/test1/test_import_safety.py:33`, `tests/test1/test_pipeline_sources.py:138`), and no test reads `PATH`.

**Concerns.** None.

**Suggestions.**
- LOW, implementation detail: when the inline tracer script runs under `node -e`, require jsdom by absolute path built from the resolved repository root rather than relying on cwd resolution, so a different cwd cannot change which jsdom loads.
- Note for the executor: the wave-1 tracer runs before plan 02 lands, and `Profile.email`/`phone` are nullable text (`tests/test1/app/models.py:206-207`), so the tracer must assert row identity only, not field-aware clearing.

**Risk Assessment.** Medium. The bound-name contract is a copied-template break (correctly routed to plan 09); the tracer plumbing is now portable.

## 06.4-02

**Summary.** Field-aware clearing resolver, trusted server-disabled precedence, pre-`_post_clean` instance application, and the H1 existing-row save predicate repair.

**Strengths.**
- Defects confirmed: `group.py:36-37` returns `None` for every field; `group.py:78-84` pops errors and writes `None` after `super().clean()`; `group.py:57-60` disarms `required` on all group fields with no disabled exemption.
- H1 target confirmed: `render_tree.py:254-256` saves an existing row only `if form.has_changed()`, and `render_tree.py:222-234` calls `form.save(commit=False)` per form, so an unchanged off-toggle row never reaches persistence today. The private `_cv_conditional_requires_save` signal (`06.4-02-PLAN.md:97`) sits at the right predicate.
- The pre-`_post_clean` ordering is correct against Django: `construct_instance` skips omitted defaulted fields whose cleaned value is empty, so a value applied to the instance before inherited `_post_clean` survives, while `FileField.save_form_data(instance, False)` clears the reference and `None` is a no-change sentinel.
- A15 holds in this suite: no Pillow in any cached environment (no `PIL`/`pillow` dist-info under the three `.nox` site-packages), and every existing `run_checks` call is tag-scoped (`tests/test1/test_button_classes_checks.py:325`, `tests/test1/test_guardian_composition.py:112,123`), so Django's model-tag `fields.E210` never runs. pytest-django's migrate goes through `call_command`, which defaults `skip_checks=True`.

**Concerns.** None.

**Suggestions.**
- LOW, wording: `group.py:14` and `group.py:44-45` still say an off group is "never validated"; plan 09 fixes the docs, but the module docstring should be corrected in this plan's own edit of `group.py`.

**Risk Assessment.** High complexity, well bounded. The persistence matrix, storage spy (`06.4-02-PLAN.md:111`) and real `XFormSet.save` path are all named.

## 06.4-03

**Summary.** `crud_views.E312` for statically detectable unsupported clearing on main and inline form classes, runtime `ImproperlyConfigured`, W320 retirement, inherited-invariant proof.

**Strengths.**
- Current check limits confirmed: `checks.py:141-149` warns only on null/blank; `checks.py:164-179` inspects only `view.form_class`; `checks.py:130-138` passes the main form's namespace into child formsets, which is the A02 defect the plan fixes.
- `E312` is unused anywhere in `src/` or `docs/` (registry grep), so allocation is clean.
- Reusing the plan-02 resolver over `klass.form.base_fields` (available through `formsets.py:91-92`) avoids request-dependent form construction.

**Concerns.** None.

**Suggestions.**
- LOW: `crud_views.W320` is a documented public check ID (`docs/reference/conditional.md:142`). Retiring it (`06.4-03-PLAN.md:86`) should surface as an explicit CHANGELOG line, not only as prose in the conditional reference. Plan 09-02's pairing rule already covers this if the executor classifies it as a changed contract.

**Risk Assessment.** Low.

## 06.4-04

**Summary.** Mandatory edit-only and existing-row identity policy inside the active runtime traversal, with test-local HTTP routes and a native `BaseInlineFormSet` adapter.

**Strengths.**
- Placement is correct. Declarations accept any `BaseInlineFormSet` (`formsets.py:60,88-89`), `FormSet.init` passes `formset`/`parent_form` kwargs (`formsets.py:144-152`) so a native subclass needs the adapter named at `06.4-04-PLAN.md:90`, and `XFormSet.save` bypasses Django's `BaseModelFormSet.save()` edit-only short circuit entirely by saving forms individually (`render_tree.py:254-256`). A5 is a live defect.
- D-12's "replacement row" hazard is real: Django's `_construct_form` drops an out-of-queryset pk and `BaseInlineFormSet` assigns the parent FK to the fresh instance, so the per-form save would insert a new row. Converting through the pk field and checking `get_queryset()` membership on the alias (`06.4-04-PLAN.md:104`) is the right test.
- The two-pass `all_valid` (`formsets.py:365-369`) is respected by the idempotence requirement.

**Concerns.** None.

**Suggestions.**
- Implementation note: nonform policy errors must be appended after `full_clean` has populated `_non_form_errors` (Django resets that list at the start of `full_clean`), and the private idempotence marker must survive the second pass.

**Risk Assessment.** High value, medium complexity. Security-relevant and correctly gated before the atomic block at `mixins.py:113`.

## 06.4-05

**Summary.** Composed disabled ownership with an observed external baseline, native reset synchronization after the default action, stranded-focus recovery.

**Strengths.**
- Defects confirmed: `toggle.js:26-31` writes `el.disabled = !on` unconditionally and only over `input, select, textarea`, so buttons are never disabled (D-07 gap) and any independent disabled reason is destroyed on the next toggle.
- The spike-first order for the MutationObserver (`06.4-05-PLAN.md:78`) and the macrotask-after-default-reset requirement (`06.4-05-PLAN.md:92`) match the WHATWG reset ordering.
- Modal ownership is preserved: `modal.js:90-103` recovers focus only when the active element was inside replaced content; the plan's "no early focus on hidden shell" keeps that contract.

**Concerns.** None.

**Suggestions.** None beyond what the plan states.

**Risk Assessment.** Medium. Pure client state machine; jsdom plus plan 08 Chromium evidence cover it.

## 06.4-06

**Summary.** One controller per owning form, `cv.initFormsets(root)`, capability-aware stock and custom Add, submit ordering with the modal listener, Django-rendered control assertions.

**Strengths.**
- Confirmed: `control.html:19-22` renders Add unconditionally; `formset.js:542-548` binds page controls with a universal `{edit_only: false}`; `formset.js:53,130,165,280` use global jQuery selections; `formset.js:621-645` starts once with no modal-loaded handling.
- The `reorder_formsets` bug is real: `formset.js:600-608` returns `false` from the `.each` callback, which only breaks the loop, and the outer function returns `true` at `:610`.
- A16 fixture correction is consistent with `check_keys` (`formsets.py:294-297`, `^[a-z\-]+$`).

**Concerns.**
- LOW. The 06-02 behavior "a cancelled submit invokes zero fetches" is not discriminating as written. The formset handler returns `false` from a jQuery handler (`formset.js:485-487`), which also stops propagation, so the document-level modal listener (`modal.js:227-233`) never sees a cancelled submit today. The test would pass on unchanged code. Mechanism: bubbling order form → document, suppressed by jQuery's `return false`.

**Suggestions.**
- Add one case where an earlier non-jQuery listener calls only `preventDefault()` (no `stopPropagation`) and assert zero fetches. That is the case the "honor an earlier defaultPrevented flag" repair (`06.4-06-PLAN.md:115`) actually changes.

**Risk Assessment.** Medium. Largest JS refactor of the phase; the test matrix is explicit.

## 06.4-07

**Summary.** Declaration-derived selected-child index, successful second-sibling round trip, raw fragment wrapper balance, parsed insertion.

**Strengths.**
- A19 confirmed: `formsets.py:513` hardcodes `index=0`; the validator already computes `declared = list(chain[j - 1].children).index(key_path[j])` at `formsets.py:446`, so the same derivation serves `get_template` with no grammar change. The stale docstring is at `formsets.py:417-418` exactly as `06.4-07-PLAN.md:86` says.
- H2 confirmed: `formset.html:4` opens on `render_rows_only` while `formset.html:56` closes on `end_at_rows`, an attribute `XFormSet` does not define (`render_tree.py:93-102`), so the closing wrappers are always emitted and rows-only fragments carry stray closers. Aligning both predicates (`06.4-07-PLAN.md:100`) is the minimal correct repair.
- The old characterization at `tests/test1/test_fragment_authorization.py:1186-1187` asserts the mismatch and is correctly treated as non-evidence.

**Concerns.** None.

**Suggestions.** None.

**Risk Assessment.** Low to medium. Small backend change, broad test replacement.

## 06.4-08

**Summary.** Disposable loopback Django fixture plus cached Chromium runner, stock and native themes, named review-regression assertions.

**Strengths.**
- Analog confirmed: `tests/browser/modal-focus.cjs:76-89` (port probe on 8143, `CV_FOCUS_PYTHON/PLAYWRIGHT/CHROMIUM` overrides, owned child spawn). The 06.3 fixture server serves through `wsgiref.make_server` and migrates with `call_command("migrate", run_syncdb=True)` (`17-evidence/server.py:12,37,129`), which runs no system checks. Following that analog keeps the no-Pillow `ImageField` fixture startup-safe, as `06.4-08-PLAN.md:119` requires.
- Port separation (8144 vs 8143) and sequential scheduling are explicit.

**Concerns.** None.

**Suggestions.**
- LOW, wording: state explicitly that the fixture serves via `wsgiref`/`basehttp` and never the `runserver` management command. `runserver` performs system checks by default and would raise `fields.E210` on the Pillow-less `ImageField` model, which would read as a Pillow dependency rather than the intended check boundary.

**Risk Assessment.** High effort, bounded. The required assertion table makes the evidence checkable.

## 06.4-09

**Summary.** Executable documentation recipes, projection and clearing matrix, paired Breaking and migration guidance, Phase 7 inventory.

**Strengths.**
- Stale artifacts confirmed: `examples/bootstrap5/conditional/models.py:8` promises universal `None` and W320 (A08); `docs/reference/conditional.md:31` says validation is skipped entirely; `docs/reference/formsets.md:205-210` carries the second-child limitation that 09 removes only after 07/08 pass.
- The analog `tests/test1/test_delete_migration_docs.py` exists and `.venv/bin/mkdocs` is present for the strict build.
- A13's grammar-versus-identity distinction matches `render_tree.py:188` (`"pk": self.pk.value`) and the `str+Enum` note at `formsets.py:46-50`.

**Concerns.** None.

**Suggestions.** Include the W320 retirement and the `group.py` docstring correction in the consistency assertions (see 03 and 02 notes).

**Risk Assessment.** Low.

## 06.4-10

**Summary.** Three-series evidence runner with enabled, ordinary Node-free and missing-runtime routes per interpreter, browser and docs gates, A19 reconciliation.

**Strengths.**
- Interpreters exist with matching metadata: `django-4.2.30`, `django-5.2.18`, `django-6.0.9`, `pytest-9.2.0`, `pytest_django-4.14.0` in `.nox/crispy_floor-3-12-django-4-2`, `.nox/tests-3-12-django-5-2`, `.nox/crispy_floor-3-12-django-6-0`. `.venv/bin/ruff` and `.venv/bin/mkdocs` exist.
- The ordinary route (`06.4-10-PLAN.md:99`) is sound: no test depends on `PATH`, subprocesses use `sys.executable`, and `shutil.which` returns `None` for an empty `PATH` by documented behavior since Python 3.7 (direct probe blocked by the sandbox).
- The missing-runtime control is distinguishable: with the opt-in set the node is collected, a nonexistent `CV_FOCUS_NODE` fails hard per plan 01, and the JUnit record carries the diagnostic. If the opt-in were missing, pytest exits 4 with no testcase, which the checker already rejects as invalid control evidence (`06.4-VALIDATION.md:124`).
- CI remains untouched: `.github/workflows/tests.yml:24` runs the nox `tests` sessions (`noxfile.py:18`), which never set the opt-in.

**Concerns.** None.

**Suggestions.** None.

**Risk Assessment.** Low risk, long runtime. Evidence-only plan with corruption controls.

## Cross-plan summary

All ten plans are internally coherent against current source. Every cited defect reproduces at the named line, every repair sits at the seam that actually executes, and the wave ordering respects shared-file ownership (01 → 02 → 04 on `render_tree.py`, 01 → 05 on `toggle.js`, 06 → 07 on `formset.test.js`). No HIGH was found and no prior closure regressed.

**A18: signed off.** The opt-in is a true collection boundary (installed pytest honors function-level `__test__`), ordinary CI and nox need neither Node nor jsdom, the enabled route keeps A17's hard failures, and plan 10 requires the passed tracer, a missing-runtime failure and a Node-free ordinary full suite per series. The disabled route is executable on this suite because no existing test resolves executables through `PATH`.

## Prior-item closure ledger

| Item | Disposition this cycle | Source evidence |
|---|---|---|
| H1 | Closed, no regression | `render_tree.py:254-256` predicate; 02:97, 02:111, 04:90, 08 assertion table, 10:99 |
| H2 | Closed, no regression | `formset.html:4` vs `:56`, `render_tree.py:93-102`; 07:86, 07:100 |
| H3 | Closed, no regression | `formsets.py:144-152` kwargs; 04:90 adapter and route fixture |
| A01–A14 | Dispositions preserved | No regression found in any plan body |
| A15 | Closed, no regression | No Pillow in three envs; tag-scoped `run_checks` only; wsgiref analog server |
| A16 | Closed, no regression | `formsets.py:294-297` grammar unchanged; 06:99 fixture |
| A17 | Closed, no regression | 01:116 precedence and hard failure inside the enabled case |
| A18 | **Closed, signed off** | `_pytest/python.py:264`; `tests.yml:24`; `noxfile.py:18`; 01:116, 01:121, 10:99 |

## Unresolved concerns (deduplicated)

None at HIGH or MEDIUM. Optional LOW suggestions, no revision required:

1. **06-02 discriminating cancel case.** Add a `preventDefault()`-only canceller so the modal ordering repair is actually exercised; today's jQuery `return false` masks the path.
2. **08-01 server wording.** State "wsgiref/basehttp, not `runserver`" to keep the Pillow-less `ImageField` fixture from tripping `fields.E210` at startup.
3. **Docstring and W320 wording.** Correct `group.py:14,44-45` in plan 02 and give the W320 retirement an explicit CHANGELOG line through plan 09-02's pairing rule.

`CYCLE_SUMMARY: current_high=0 current_actionable=0`
