I'll verify the nine revised plans against current source and the Round 1 ledgers, starting with the revision and the files each plan claims to change.
The plans match `1faf42d`. Next I’ll check the Round 1 dispositions against the code they cite.
Reviewed current plans at `1faf42d` (HEAD `f4c7744` changes only `ROADMAP.md`). Round 1 planning items H01–H05 and H07–H12, and A01–A18, are signed off below. H06 remains an external blocker, not a new planning defect.

## 06.6-01

**Summary.** The ownership defect is real and the plan targets the right boundary: page templates already own the outer form (`view_create.content.html:5-10`), while `cv_render_form` flattens into a template that reads `form.helper` twice (`crud_views.py:465-466`, `tags/form.html:3-6`). Library helpers never set `form_tag` (`form.py:43-50`, `136-146`). The revised tracer, atomic golden commit, and helper diagnostics match D-01–D-04 and the create slice of D-16.

**Strengths.**
- H03 is closed: `06.6-01-PLAN.md:95` makes 01-01/01-02 one green commit covering the four frame goldens before plan 05.
- H02 is closed: `06.6-01-PLAN.md:93` migrates `_CustomHelperForm` and `_DeleteCustomHelper` (`test_form_button_checks.py:560-585`) in that same commit; plan 02 depends on 01.
- H09/H10/A10 are executable: inner CSRF stays local to `cv_render_form` (`06.6-01-PLAN.md:124-126`), the raw scanner rejects unclassed nested forms (`:92`, `:139-140`), and rendering follows `cv_alert`'s `context.push` plus `template.template.render` (`crud_views.py:453-455`, plan `:119`).
- A01 is an independent pinned archive at `cb26af4` (`:112-114`).

**Concerns.**
- LOW: Between this commit and plan 05, stock workflow still calls `{% crispy form form.helper %}` (`view_workflow.action.html:15`). `form_tag=False` removes the nested form but not the inner token. The plan records that partial sequence (`:126-128`) and workflow tests do not assert token counts, so this is an accepted intermediate, not an undispositioned red suite.

**Suggestions.**
- None required for planning closure.

**Risk Assessment.** LOW. The create path, fixture migration, and diagnostic matrix are specified against the code that actually emits the nested form.

## 06.6-02

**Summary.** The theme floor can sit in the existing resolver. `default_label_mode` already reads settings per call and falls back to the package table (`label_mode.py:86-119`); W292 already calls the public resolver (`buttons.py:435-436`, `:569-572`); E108 already validates setting shape (`settings.py:159-188`). The plan adds one atomic theme layer without renaming owner APIs.

**Strengths.**
- A02/A16: publish by rebind under `_theme_defaults_lock`, autouse snapshot/restore, same-worker isolation (`06.6-02-PLAN.md:69`, `:94-96`).
- A17: `_theme_or_package_default` must not call `default_label_mode` (`:120-122`), which is the recursion that the current fallback lambdas at `label_mode.py:107` and `:118` would create if they re-entered the public resolver.
- A18: card is an explicit non-form case (`:98`) against the real package floor `card=both` (`label_mode.py:23-24`).
- H02 dependency is real: this plan edits `test_form_button_checks.py` only after plan 01 (`depends_on: ["06.6-01"]`).

**Concerns.**
- None remaining. Invalid registration raises regardless of strict mode (D-06); invalid settings still use the existing strict/log path (D-07). That split matches the current code.

**Suggestions.**
- None.

**Risk Assessment.** LOW. Precedence and check wiring are already centralized; the plan does not invent a second resolver.

## 06.6-03

**Summary.** The three group constructors are real and separate: `CrispyFormMixin.get_form_actions` (`form.py:55-56`), `CrispyDeleteForm.helper` (`form.py:141-144`, which does not call that hook), and `ListViewFilterFormHelper.get_form_actions` (`list.py:125-133`). The declared floor is `crispy-bootstrap5==2023.10` (`noxfile.py:24`). The plan no longer leaves bridge selection to an open experiment.

**Strengths.**
- H01 is signed off: bridge only when pack name is `bootstrap5`, the resolved origin is the installed distribution's `layout/formactions.html`, and the full source matches the audited floor fixture (`06.6-03-PLAN.md:76-85`). Custom origins never fall back. A failed experiment blocks rather than waiving D-10.
- H04/H05 are signed off: 03-02 owns the 86-to-88 inventory (`:112`) after plan 04, and the cached `_cv_actions` object (`list.py:172-179`) must resolve classes at render time (`06.6-03-PLAN.md:101-108` in the filter-freshness action).
- H11's core half is signed off: a class-dropping custom template must not be overwritten (`03-03`).

**Concerns.**
- None that reopen H01. Exact source match can still fail the floor probe; the plan correctly stops for a support-policy decision instead of raising the floor.

**Suggestions.**
- None.

**Risk Assessment.** MEDIUM for execution, LOW as a planning defect. The floor incompatibility is positively specified; the mechanism is allowed to fail closed.

## 06.6-04

**Summary.** Alert literals are still hardcoded (`alert.html:2-5`: `alert-dismissible fade show`, `btn-close`, `role="alert"`, `data-cv-alert-dismiss`, translated Close). `get_button_class` already turns `None` into `""` (`button_classes.py:165`), so the empty-close `class=""` rule is implementable without a new renderer.

**Strengths.**
- A03 is signed off at `06.6-04-PLAN.md:68-69`: no separator for empty/None dismissal; close control stays `class=""`; default golden bytes stay.
- H04 is signed off at `:70-71`: `EXPECTED_KEYS` and the documented count (`test_button_classes.py:104-116`, `buttons.md:151`) move 84 to 86 in the same task as the defaults. W362 only treats mode keys as valid for variant locations or `FORM_KINDS` (`button_classes.py:251-274`), so `alert:close:icon` stays invalid without a grammar change.

**Concerns.**
- None remaining.

**Suggestions.**
- None.

**Risk Assessment.** LOW. This is a leaf and inventory change with an existing golden guard.

## 06.6-05

**Summary.** Workflow is the only stock form that bypasses `cv_render_form` (`view_workflow.action.html:8-16`). Delete already omits the form when protected (`view_delete.content.html:8-23`). Modals include the same content template (`modal/content.html:7-8`). Polymorphic create-select uses `view_create.content.html` with a helper-less form (`create_select.py:16-27`). The expansion matches D-16.

**Strengths.**
- H09 stock half is signed off: replace the direct crispy call and drop the unused `crispy_forms_tags` load (A12, `view_workflow.action.html:2`).
- H10 is signed off: raw owner scanner, auxiliary forms allowed, every nested tag an error (`06.6-05-PLAN.md` task 05-01).
- A04 is signed off against the existing guard at `test_formsets.py:16-34`, extended to tokens and update/modal/CSRF.
- A11/A13 are signed off for the two named parent overrides (`views_formset.py:44-50`, `examples/bootstrap5/formsets/views.py:36-41`) and real no-helper/create-select requests. Removing those overrides restores W292, which skips any class that does not inherit `helper` (`buttons.py:511-515`).

**Concerns.**
- LOW: Other parent overrides whose only job is `form_tag=False` are neither removed nor explicitly retained: `examples/bootstrap5/conditional/views.py:132-137`, `test_fragment_authorization.py:177-195`, `conditional_formsets_server.py:139-143`. They keep working after plan 01, and they keep hiding W292. That is the current behavior, not a broken gate.

**Suggestions.**
- One sentence in 05-02 or 08-01: those remaining overrides are intentionally retained.

**Risk Assessment.** LOW. Stock request coverage and the workflow bypass are concrete.

## 06.6-06

**Summary.** The utility plan is fail-closed and import-safe. Companion sources are still absent. That is H06, an external prerequisite, not a missing task.

**Strengths.**
- A01: separate archive lifetime from plan 01, same pin `cb26af4` (`06.6-06-PLAN.md:103`).
- A05: import-pure CLI, `importlib` loading, companion env cleared, broad collection (`06.6-06-PLAN.md` task 06-01). `tests/browser/` has no package marker today; the plan does not invent one.
- A09: unmet precondition writes a halted summary and does not create a passing baseline (`:113-117`).
- H06 disposition is accurate: `:109-112` forbids inventing identities or substituting a fixture.

**Concerns.**
- H06 remains unresolved execution evidence. `06-02` cannot pass until authoritative `CV_THEME_SOURCE` and `CV_PACK_SOURCE` exist. This does not weaken the product plans.

**Suggestions.**
- Do not add synthetic acceptance. Keep the halt.

**Risk Assessment.** HIGH for this plan's acceptance outcome, LOW as a planning defect. The blocker is named and fail-closed.

## 06.6-07

**Summary.** Browser acceptance is correctly gated on a source-bound baseline (`06.6-07-PLAN.md:73`). Ports match the existing reservation: modal-focus owns 8143 (`modal-focus.cjs:21`), conditional owns 8144 (`conditional-formsets.cjs:28`), presentation rejects both (`presentation.cjs:4-5`). Default 8145 is free of those reservations (A14, plan `:83-85`).

**Strengths.**
- A06 is signed off: 07-01 is one real create path; 07-02 is the eight families; 07-03 replays the patch.
- H09/H10/H11 companion halves are specified: migrate an existing copied workflow template (`:99`), scope raw checks to owning content (`:109`), and adapt the pack's own `formactions.html` only if it drops classes (`:100-104`).
- Override growth fails acceptance (`:104`). Original trees stay untouched (D-11/D-14).

**Concerns.**
- LOW: `:80-81` and `:99` do not say that a missing theme copy is success. Adding a new `tags/form.html` or `view_workflow.action.html` would grow required overrides and then fail 07-03. Fail-closed, but the instruction can be misread as "create the copy."
- H06 still blocks 07-01's precondition. Not a planning hole.

**Suggestions.**
- State: adapt only an existing bypass copy; absence of that file is not a task failure and must not add an override.

**Risk Assessment.** MEDIUM until companions exist. The harness design is sound; acceptance cannot start.

## 06.6-08

**Summary.** Migration docs have a real assertion to update. `test_migration_e108_location_inventory` still requires "falls back to its package floor" (`test_label_mode_docs.py:786-800`). The alert recipe extractor requires exactly one fence under `### Custom alert frame` (`test_alerts.py:249-255`). The plan keeps those gates intact.

**Strengths.**
- H07 is signed off: 08-01 leaves the migration sentence and its test together; 08-02 updates both (`06.6-08-PLAN.md:84-85`, `:107-108`).
- H08 is signed off: `:85-87` runs `test_alerts.py` and forbids a second fence.
- H09/H10 docs are signed off: copied workflow migration, undetectable old inner copies, owning-content scope (`:73-77`).
- A08 is signed off: tutorial `get_form_actions` guidance stays, proved by `test_form_button_docs.py` (`:88-90`).
- A11's W292 note matches `buttons.py:511-515` (`:91-92`).

**Concerns.**
- LOW: `06.6-08-PLAN.md:100` still says read "the four frame golden diffs from 05". H03 moved those diffs into plan 01's `01-ownership-evidence.md`. The action text does not depend on the stale pointer, so this will not change the contract.

**Suggestions.**
- Point 08-02 at `01-ownership-evidence.md`, not plan 05.

**Risk Assessment.** LOW. Executable recipes and paired Breaking notes are specified; companion success is explicitly not claimed here.

## 06.6-09

**Summary.** The final gate matches the cached matrix. Present interpreters are Django 4.2/5.2 with current packs and Django 6.0 only at the crispy floor. There is no current-pack Django 6.0 environment. Plan 09 records that limit instead of treating the floor run as coverage (H12, `06.6-09-PLAN.md:100`).

**Strengths.**
- A15 is signed off: permanent `CRISPY_FLOOR_TESTS` (`noxfile.py:28-52`) gains the five `test_theme_*.py` modules plus `test_alerts.py` and `test_button_classes.py`, with an AST check and a full floor run (`:67`, `:79-83`). The only existing deselect remains `test_filter_form_baseline` (`noxfile.py:57`).
- A07 is signed off: example project has `pytest.ini` and collected tests (`examples/bootstrap5/pytest.ini:1-4`). Missing extras halt (`:176-178`).
- A09/H06: halted partial handoff, no fabricated baseline (`:125-131`). Human observations stay pending until a person supplies them (`:133`).
- Full `pytest tests` on 4.2, 5.2, and the 6.0 floor (`:160-162`) is the acceptance gate, not the narrower nox selection.

**Concerns.**
- H06 still blocks `--check-final` because replay evidence cannot exist. That is required, not a waiver.
- H12's untested current-pack Django 6.0 combination remains a coverage limit. The disposition is correct; do not treat the floor result as a substitute.
- LOW: the example command (`:163`) is not the historical `cd examples/bootstrap5 && pytest`. `django-ratelimit` is imported by `project/test_ratelimit.py:11` and is not in the listed preflight modules. The plan already fails closed on missing extras.

**Suggestions.**
- Preflight `django_ratelimit` by name, or run from `examples/bootstrap5` as the known-good cwd. Do not install it outside the legitimacy gate.

**Risk Assessment.** MEDIUM. Automated product gates are specified. Phase acceptance stays blocked on companions and human observation, by design.

## Cross-plan

Round 1 planning concerns are closed in the current plans:

| ID | Disposition |
|---|---|
| H01 | Signed off. `06.6-03-PLAN.md:76-85` fixes the selection predicates and rejects a generic Bootstrap fallback. |
| H02 | Signed off. Fixture migration is in plan 01's atomic commit; plan 02 depends on it. |
| H03 | Signed off. Four frame goldens move with the renderer in 01-01/01-02. |
| H04 | Signed off. 84→86 in plan 04 (`:70-71`); 86→88 in plan 03 (`:112`); both run `test_button_classes.py`. |
| H05 | Signed off. Render-time resolution against `list.py:172-179`, including settings changes and deepcopy. |
| H06 | Still open as execution evidence. Plans 06-02, 07, and 09 fail closed. Not a planning defect. |
| H07 | Signed off. Migration sentence and `test_label_mode_docs.py:786-800` stay one task. |
| H08 | Signed off. Single alert fence and `test_alerts.py:249-255` stay in 08-01. |
| H09 | Signed off. CSRF suppression stays inside `cv_render_form`; stock workflow moves in plan 05; copies are documented and, if present, adapted in plan 07. |
| H10 | Signed off. Owner-scoped raw scan in plans 01, 05, 07, and 08. |
| H11 | Signed off. Core does not rewrite custom packs; plan 07 adapts the real pack only in isolation. |
| H12 | Signed off as an explicit untested limit. No current-pack Django 6.0 runtime exists. |
| A01–A18 | Signed off. Each has an executable action or an explicit halt. No deferred item lacks a disposition. |

New remaining items are the LOW instruction nits in plans 05, 07, 08, and 09. They do not reopen a Round 1 HIGH.

Dependency order holds: wave 1 is 01/04/06 with no shared product files; wave 2 is 02/03/05 after their dependencies; 03 waits for 04 before the key-count handoff; wave 3 docs do not claim companion success; wave 4 cannot pass `--check-final` without 07's replay.

## Overall risk

MEDIUM. THEME-01 through THEME-04 and THEME-06 are planned against the code that implements them. THEME-05 and final acceptance remain blocked because authoritative companion sources and a fresh baseline are unavailable. That is unresolved execution evidence. Do not invent sources or synthetic acceptance.
