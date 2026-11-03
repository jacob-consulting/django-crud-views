Verification is complete. I confirmed the key source claims (nested form and duplicate token in all four frame goldens, helper and render-tag seams, class-table count 84, workflow bypass, modal gates, nox floors, browser ports, docs guards, pinned revision identical to current product source) and compared the companion excerpts against the plans' candidate deltas. Writing the review now.

# Cross-AI Plan Review, Cycle 6, HEAD 04419e0

**Reviewer mode:** read-only. Core checkout at `04419e05ed1da60bbea18ace7add9fa4a0020947`. Companion claims are checked only against the embedded excerpts; no external directory was accessed. Where the embedded excerpts do not contain the cited companion file, the finding is downgraded to an open question.

**Headline:** no HIGH findings remain. C5-H01, C5-A01 and C5-A08 are incorporated with concrete, source-consistent values and mechanics. One MEDIUM executable gap and two LOW gaps remain, all in plan 10's cross-repository close-out, plus two open questions that only companion-side inspection can settle.

**Shared ground truth used below**

| Claim in plans | Evidence | Status |
|---|---|---|
| Stock frames nest a second form and emit two tokens | `tests/test1/golden/form_frame/{create,update,custom_form,delete}.html` each contain 2 `<form` and 2 `csrfmiddlewaretoken`; `delete_protection.html` contains none | CONFIRMED |
| Library helpers construct a default `FormHelper()` with `form_tag` left True | `src/crud_views/lib/crispy/form.py:44-50` and `:136-146` | CONFIRMED |
| `cv_render_form` flattens context and re-reads `form.helper` in the inner template | `src/crud_views/templatetags/crud_views.py:465-466`; `src/crud_views/templates/crud_views/tags/form.html:3-6` | CONFIRMED |
| `cv_alert` already uses `context.push` and `template.template.render(context)` | `src/crud_views/templatetags/crud_views.py:453-455` | CONFIRMED |
| Workflow bypasses the shared tag and loads `crispy_forms_tags` | `src/crud_views_workflow/templates/crud_views_workflow/view_workflow.action.html:2,15` | CONFIRMED |
| Package floor, lazy raw read, package-only fallbacks | `src/crud_views/lib/view/label_mode.py:23-25,56-60,107,118` | CONFIRMED |
| Default table has 84 keys, documented as 84 | `tests/test1/test_button_classes.py:104-106`; `docs/reference/buttons.md:151` | CONFIRMED |
| Alert leaf hardcodes `alert-dismissible fade show` and `btn-close` | `src/crud_views/templates/crud_views/tags/alert.html:2,5` | CONFIRMED |
| Floor pins, floor test list, single deselect | `noxfile.py:24,28-52,57` | CONFIRMED |
| Cached runtimes: 4.2/5.2 tests, 4.2/6.0 floors; no current-pack 6.0 | `.nox/` listing | CONFIRMED |
| Pinned pre-phase revision equals current product source | `git diff --stat cb26af4..HEAD -- src tests examples docs noxfile.py pyproject.toml` is empty | CONFIRMED |
| Companion `TABLER_ICONS` lacks `save`, `cancel`, `filter-reset`; core `DEFAULT_ICONS` has them | embedded `icons.py:12-47`; `src/crud_views/lib/icons.py:51-53` | CONFIRMED |
| Companion `test_table_values` is whole-dictionary equality | embedded `tests.py:98-139` | CONFIRMED |
| Companion alert copy hardcodes classes and `data-bs-dismiss` | embedded `templates/crud_views/tags/alert.html:7,17` | CONFIRMED |

---

## 06.6-01

**Summary.** The plan targets the right seams and its evidence procedure is sound: the pinned revision `cb26af4` exists, is a docs-only commit, and its product tree is byte-identical to HEAD, so the "before" archive is a true pre-change baseline. The deferred-commit boundary between 01-01 and 01-02 is justified by the fixtures: all four frame goldens currently encode the nested form, and both custom-helper fixtures construct a `FormHelper()` without `form_tag=False`.

**Strengths**
- The helper boundary analysis matches source. `CrispyFormMixin.helper` allocates per access at `src/crud_views/lib/crispy/form.py:44-50`, and the inner template reads `form.helper` twice at `tags/form.html:3-4`, so "select once" is a real correction, not a refactor.
- The `Context.dicts` preservation requirement (A10) has a working in-repo analog: `cv_alert` at `templatetags/crud_views.py:453-455` pushes onto the caller's context and renders `template.template.render(context)`. The plan points at exactly this.
- The fixture migration list is complete for the renderer change. `_CustomHelperForm` at `tests/test1/test_form_button_checks.py:560-567` and `_DeleteCustomHelper` at `:578-585` are the only custom helpers in that module without `form_tag=False`; the line-948 helper already sets it.
- Enforced-CSRF precedent exists at `tests/test1/test_form_validation.py`, and the raw nested-form guard the plan reuses as analog exists at `tests/test1/test_formsets.py:17-34`.
- `is_strict()` lives at `src/crud_views/lib/exceptions.py:32`, so the D-01/D-04 strict branch has its established predicate.

**Concerns**
- LOW: the golden normalizer at `tests/test1/test_form_frame.py:44-48` collapses whitespace and rewrites token values. The plan asks 01-03 to add raw owner/no-nesting/token assertions "without changing their normalizer". That is the correct split, but the golden diff review in 01-02 should compare raw before/after output, not normalized text, or the removed second `<form>` could be masked by the `>\s+<` collapse. The plan says "compare each small diff with the pinned pre-change output"; state that the comparison is on raw bytes.

**Suggestions**
- In 01-02, name the raw-byte comparison explicitly so the reviewed diff is the DOM correction D-19 must document.

**Risk Assessment:** LOW. Mechanisms are source-grounded; the only remaining item is a wording precision on how the golden diff is reviewed.

---

## 06.6-02

**Summary.** The registration API and its layering are planned against the actual resolver. The two package-only fallbacks the plan targets are real: `label_mode.py:107` and `:118` return `LABEL_MODE_DEFAULTS[location]` directly. The form-map fallbacks at `:134` and `:145` correctly call the public floor and are not "package-only", and the plan's wording ("every existing package-only invalid-setting fallback") scopes the change to the right two sites.

**Strengths**
- Isolation need is real. `tests/test1/conftest.py:23-32` resets only `_warned`; nothing snapshots a theme map because none exists yet. The class-registry analog at `src/crud_views/lib/button_classes.py:119-151` shows the per-key merge pattern the plan copies.
- E108 vocabulary reuse is correct. The settings check at `src/crud_views/lib/settings.py:161-191` already validates with `LOCATIONS` and `is_label_mode`; W292 at `src/crud_views/lib/view/buttons.py:435,570` calls `cv_get_action_label_mode`, which bottoms out in `default_label_mode`, so the theme layer propagates without check edits.
- A17's recursion guard is sound: `form_label_mode`'s fallback lambda already re-enters `default_label_mode`, which can re-enter `_invalid_label_mode`. A setting-free private resolver for the two package-only sites prevents a loop while a malformed setting is installed.
- The strict-first ordering in `_invalid_label_mode` at `:73-74` supports the C3-A03 requirement that strict mode raises at the owner before any settings fallback runs.

**Concerns**
- LOW: `test_migration_e108_location_inventory` at `tests/test1/test_label_mode_docs.py:797` asserts the literal "falls back to its package floor." in `docs/migrating-1.0.md:64`. Plan 02 changes that behavior but does not touch docs; plan 08-02 owns the sentence/test pair (H07). Plan 02's 02-02 verify selection does not include `test_label_mode_docs.py`, so the stale doc assertion does not fail plan 02's gate. That is the intended split, but the plan 02 SUMMARY should record the known pending doc drift so a wave-2 full-suite run is not misread.

**Suggestions**
- Add one sentence to 02-02: "The migrating-1.0 package-floor sentence and its guard are intentionally stale until 08-02."

**Risk Assessment:** LOW.

---

## 06.6-03

**Summary.** The plan resolves the positively reproduced floor incompatibility with a narrowly scoped bridge and explicit eligibility predicates. All three construction sites it names exist: ordinary group at `form.py:55-56`, delete group at `form.py:136-146`, filter group at `src/crud_views/lib/views/list.py:125-133` with `form_tag = False` at `:94`. The floor runtimes for both 03-01 and 03-03 commands exist.

**Strengths**
- Both floor interpreters exist: `.nox/crispy_floor-3-12-django-4-2` and `.nox/crispy_floor-3-12-django-6-0`. The named deselect matches `noxfile.py:57`, and `test_filter_form_baseline` exists at `tests/test1/test_form_buttons_golden.py:266`.
- Key-count ownership is coherent. Plan 04 moves 84 to 86, plan 03 moves 86 to 88; `test_default_table_is_complete` at `test_button_classes.py:104-106` and the prose at `buttons.md:151-156` are the two live guards the plan names.
- W362 grammar is safe for the new keys. `button_classes.py:328-345` accepts any key present in `DEFAULT_BUTTON_CLASSES` and warns on anything else; `form:actions:icon` is neither a default nor an `_action_key_parts` form kind, since `FORM_KINDS` at `:240` excludes "actions", so it stays invalid as required.
- The filter helper's prepared-layout lifecycle (`list.py:97-101`) is the right place to make H05's "resolve classes at render time without accumulation" testable.

**Concerns**
- LOW: the bridge predicate compares the resolved template's whole source to an audited 2023.10 fixture string. That is deliberately strict. If a maintainer later bumps `CRISPY_FLOOR` to a release whose template differs, the bridge silently stops applying and the only signal is the floor test failing. Acceptable, but the evidence file should state this maintenance coupling.

**Suggestions**
- Record in `03-pack-bridge-evidence.md` that the bridge is bound to the exact 2023.10 template bytes and must be re-audited with any floor change.

**Risk Assessment:** MEDIUM, driven by research assumption A1 still needing the experiment, not by plan gaps. The plan handles the fallback honestly with a support-policy checkpoint.

---

## 06.6-04

**Summary.** Smallest plan, fully grounded. The leaf literals to replace are at `alert.html:2,5`; the default golden is raw bytes at `tests/test1/golden/alerts/dismissible.html`; the JS adapter test exists at `tests/js/adapters.test.js` and `node_modules/vitest/vitest.mjs` is present.

**Strengths**
- A03's separator rule is precise against source: the leading space lives inside `{% if alert.dismissible %} alert-dismissible fade show{% endif %}` at `alert.html:2`, so an empty configured value must emit no space to keep `class="alert alert-success"`.
- The 84-to-86 count update lands in the same task as the defaults, which is what `test_default_table_is_complete` and `test_documented_default_key_count_matches_table` at `test_button_classes.py:104-113` require to stay green between commits.
- The theme.md "Custom alert frame" recipe (`docs/reference/theme.md:308-334`) is guarded by `test_alerts.py:250-253` requiring exactly one fence; plan 04 does not touch that section, and plan 08 explicitly preserves it (H08).

**Concerns**
- LOW: `docs/reference/theme.md:310-311` currently states the frame classes "are literal Bootstrap CSS" and that authors must ship a template to restyle them. After plan 04 this sentence is false. Plan 08-01 owns theme.md prose, but plan 04's `files_modified` includes `docs/reference/buttons.md` only. The stale sentence will persist from wave 1 to wave 3. Not a correctness gap, but a documentation window worth naming in 04's SUMMARY.

**Suggestions**
- Note the pending theme.md sentence in 04's SUMMARY so plan 08 cannot miss it.

**Risk Assessment:** LOW.

---

## 06.6-05

**Summary.** The expansion plan is correctly scoped to actionable forms and respects the modal gate. The mechanisms behind C3-A01 and C2-A01 are verified: `WorkflowView` extends `CustomFormView` at `src/crud_views_workflow/lib/views.py:18`, which sets `cv_content_template = "crud_views/view_custom_form.content.html"` at `src/crud_views/lib/views/form.py:19`; the modal shell includes `view.cv_content_template` at `crud_views/modal/content.html:8`. Create and update inherit `cv_modal_supported = False` from `src/crud_views/lib/view/base.py:111`, and E251 at `:169-170` enforces it.

**Strengths**
- Protected-delete omission is a real branch: `view_delete.content.html:15-23` renders the form only when `not has_protected_objects`. The plan's explicit exception list is right.
- The two redundant parent-helper overrides exist with the stated rationale: `tests/test1/app/views_formset.py:45-49` and `examples/bootstrap5/formsets/views.py:37-40`. The C2-A05 deferral correctly leaves the other `form_tag=False` fixtures at `examples/bootstrap5/conditional/views.py:136`, `tests/test1/test_fragment_authorization.py:180,195,1586` and `tests/browser/conditional_formsets_server.py:142,261` alone.
- The A12 removal is correct: `view_workflow.action.html:2` loads `crispy_forms_tags` only for the line-15 call that becomes `cv_render_form`.
- Every named preservation suite exists, including `tests/test1/test_cancel_origin.py`.
- The polymorphic create-select route exists in the test app: `VehicleCreateSelectView` at `tests/test1/app/views.py:557`.

**Concerns**
- LOW: the companion's `test_delete_form_is_the_stock_crispy_delete_form` at embedded `tests.py:323` still expects `<input type="submit"`, while the core leaf renders `<button type=…>` at `src/crud_views/templates/crud_views/tags/button/form.html:2`. Cycle 5 dispositioned this as an execution note for baseline recording (C5-A02), not a plan gap. I agree, and only note here that plan 05's `delete/trash` ThemeAdoptionTests coverage in 07 will pass while this older companion assertion stays red at baseline; the recorded failure identity must name it.

**Suggestions**
- None beyond keeping the baseline failure identity explicit, which plans 06/07 already require.

**Risk Assessment:** LOW to MEDIUM. Breadth is large, but every path cited exists and the gates are explicit.

---

## 06.6-06

**Summary.** The baseline utility is the load-bearing piece of THEME-05, and the plan's provenance, purpose-counting and delivered-source validation contracts are now specified in enough detail to be testable. Pytest layout facts support the A05 purity requirement: `tests/__init__.py` exists, `tests/browser/` has no `__init__.py`, and `tests/conftest.py` is empty, so a new `tests/browser/test_*.py` will be collected by every `pytest tests` command in plan 09 under rootdir prepend import.

**Strengths**
- The D-18 counting rule is now a specification, not a slogan: stable purpose IDs, data-only adoption excluded, mixed files split by symbol, renamed paths cannot reset IDs. The embedded `checks.py:8-27` and `icons.py:50-52` are exactly the "data-only file with a counted callback" case the rule anticipates.
- The shadow discovery examples match the embedded tree: `tags/alert.html`, `snippets/form_frame.html`, `tags/list_filter.html`, `tags/list_filter.inner.html`, `modal/shell.html`, `table/bootstrap5.html`, `tags/card.html`, `view_card.content.html` all appear in the excerpts.
- The delivered-source mode is designed so plan 10's authorized HEAD advance is not misread as corruption, while `--check-baseline` keeps validating the pinned archive.
- The commit-receipt validation (C5-A01) reads companion objects with `git -C` against the verified root and tests wrong-repo SHA, swept staged content and same-file staged hunks with disposable fixtures. Those negative fixtures are what makes plan 10's protocol falsifiable.

**Concerns**
- LOW: the 06-01 verify command collects the whole `tests` tree with `-k`. Cycle 5 already dispositioned this (C5-A06). Not re-raised.
- Open question, not a gap: the plan asserts the companion's native `formactions.html` consumes `css_class` and that `django_tabler.icons.ICONS` defines `check`, `arrow-left` and `filter-x`. Neither file is in the embedded excerpts, so this reviewer cannot confirm. The companion's own `test_every_upstream_icon_name_is_mapped` at `tests.py:67` will fail loudly if a mapped Tabler name is absent from `ICONS`, so the risk is detection-covered.

**Suggestions**
- In 06-COMPANION-SETUP.md, record the hash of `src/django_tabler/icons.py` and `crispy_tabler/layout/formactions.html` at baseline so plan 07's "already exists" claims bind to inspected bytes.

**Risk Assessment:** MEDIUM. Execution-heavy, companion-runtime dependent, but the plan converts every dependency into a precondition or negative fixture.

---

## 06.6-07

**Summary.** C5-H01 and C5-A08 are resolved with concrete values and the right mechanics. The three icon mappings are exactly the gap: core `DEFAULT_ICONS` at `src/crud_views/lib/icons.py:51-53` has `save`, `cancel`, `filter-reset`; the companion's `TABLER_ICONS` at embedded `icons.py:12-47` has every other core key but these three. Adding them also repairs the companion's own `test_every_upstream_icon_name_is_mapped` at `tests.py:62-67`, which asserts `set(TABLER_ICONS) == set(DEFAULT_ICONS)` and therefore fails against current core at baseline.

**Strengths**
- Five kinds in three modes plus native reset are specified for candidate, browser and replay (07-02, 07-03), with SVG path comparison to the native definition, negative controls per mapping and an explicit ban on text-only or `icon=None` evasion. This is the full C5-H01 ask.
- The four class values are concrete and the `test_table_values` synchronization retains whole-dictionary equality (embedded `tests.py:98-139`). The dependency on plans 03/04 also satisfies the companion's `test_every_theme_key_is_an_upstream_key` at `tests.py:84-90`, which requires each one-colon theme key to exist in core `DEFAULT_BUTTON_CLASSES`.
- The alert parity change is mechanically correct. The companion's `MessagesParityTests` at `tests.py:556-572` compares the native include to `{% cv_messages %}` after whitespace normalization; switching the CRUD copy's hook from `data-bs-dismiss="alert"` (embedded `alert.html:17`) to `data-cv-alert-dismiss` breaks byte parity unless the test maps that one attribute, which is exactly what C4-A02 specifies. The companion page loads `cv_js` at `page.html:16`, so the core delegated listener is present on CRUD pages.
- Port policy is verified: `tests/browser/presentation.cjs:2,4` defaults to 8145 and reserves 8143/8144; `modal-focus.cjs:21` hardcodes 8143; `conditional-formsets.cjs:28-31` defaults 8144.
- `register_label_mode_defaults({"form": "both"})` in `ready()` fits the existing registration block at embedded `apps.py:15-31`.

**Concerns**
- LOW: the "no-URL cancel" check from the review scope is only implicitly covered by "preserve cancel link/button navigation". The companion registers no `form:cancel-tag`, so cancel renders as a button regardless, and a URL-less cancel adds little discriminating value here. Still, one ThemeAdoptionTests case for a cancel without a destination would pin Phase 6.1's fallback under the Tabler table.
- Open question: `django_tabler.icons.ICONS` content is not embedded; see 06.6-06.

**Suggestions**
- Add a URL-less cancel render to ThemeAdoptionTests as a cheap completion of the five-kind matrix.

**Risk Assessment:** MEDIUM. Browser and companion execution risk, not specification risk.

---

## 06.6-08

**Summary.** The documentation plan names real guards and keeps the two fragile pairs intact. `test_migration_e108_location_inventory` exists at `tests/test1/test_label_mode_docs.py:786-816` and asserts the exact "falls back to its package floor." sentence found at `docs/migrating-1.0.md:64`; the single-fence requirement for the alert recipe is enforced at `tests/test1/test_alerts.py:250-253`. All referenced doc pages and test modules exist.

**Strengths**
- H07's split is correct and necessary: 08-01 touches reference pages only and leaves the migration sentence; 08-02 changes sentence and test together and runs `test_label_mode_docs.py`.
- `test_form_button_docs.py` holds the tutorial/list-helper recipe guards (`:100-155`) the plan runs to prove A08's retained prose still executes.
- The standalone library-form wrapper removal (C2-A02) is a real Breaking consequence of plan 01's `form_tag=False` on library helpers, and the plan pairs it with an executable caller-owned wrapper recipe.

**Concerns**
- LOW: `docs/reference/theme.md:310-311` still tells authors the frame classes are literal and must be overridden by copying the template. 08-01 must rewrite that paragraph while keeping the single fence; the plan says "add utility guidance outside that fence", which is compatible, but it should explicitly say the two literal-class sentences are replaced, not merely supplemented.

**Suggestions**
- Name `theme.md:310-311` as the sentences to rewrite in 08-01.

**Risk Assessment:** LOW.

---

## 06.6-09

**Summary.** The final gate is comprehensive and its runtime assumptions match the machine: `.nox/tests-3-12-django-4-2`, `tests-3-12-django-5-2`, `crispy_floor-3-12-django-4-2` and `crispy_floor-3-12-django-6-0` exist; current-pack Django 6.0 does not, matching the H12 disposition. `examples/bootstrap5/pytest.ini`, `vitest.integration.config.js`, `.venv/bin/mkdocs` and `.venv/bin/ruff` exist. `CV_FOCUS_PYTHON` is the env var `modal-focus.cjs:81` reads, and `CV_FRAGMENT_PYTHON` is read by `tests/js/runtime-contract.test.js`.

**Strengths**
- The A15 floor-selection change is substantive: `noxfile.py:28-52` lists 23 modules and omits `test_alerts.py` and `test_button_classes.py`; adding those plus the five new `test_theme_*` modules makes the permanent floor session cover the phase.
- The example gate command is consistent with `examples/bootstrap5/pytest.ini` (`DJANGO_SETTINGS_MODULE = project.settings`, `pythonpath = .`).
- `--check-final` binds delivery receipts in both repositories and keeps companion hashes out of the core Task Commits section, which matters because the executor's self-check runs `git merge-base --is-ancestor {hash} HEAD` on every listed hash and would fail on a companion SHA.
- The `conditional-formsets.cjs --case lifecycle` selection exists at `tests/browser/conditional-formsets.cjs:57`.

**Concerns**
- LOW: the plan says raw logs go "under this phase's 09-evidence directory" but 09-01's `files` list does not include that directory, and `.gitignore` has no `.planning` or evidence rule. Prior phases committed their evidence trees (319 tracked files under 06.3's `09-evidence/`, 30 under 06.5). The executor's untracked-file step will commit them as intentional, which matches precedent, but the plan should say so to avoid an executor adding a `.gitignore` rule instead.

**Suggestions**
- Add "commit 09-evidence raw logs with 09-01" to the task, or list the directory in `files`.

**Risk Assessment:** MEDIUM. Nothing structurally missing; the gate is as strict as the phase requires and its pass depends on upstream execution.

---

## 06.6-10

**Summary.** The cross-repository protocol is now explicit and, read against the installed executor contract, mostly compatible. The contract's `task_commit_protocol` stages named files and commits in the current repository unless `sub_repos` is configured; `.planning/config.json` has no `sub_repos`, `commit_docs` is true, `auto_advance` is false and `human_verify_mode` is `end-of-phase`. Under that contract the plan's design works because: 10-01 and 10-02 leave no core-tracked change, so there is nothing for the core protocol to stage; 10-03 produces one core commit, so the measured `commits:` is 1 and the "0 commits with code changes → HALT" rule does not trigger; companion hashes stay out of Task Commits, so the self-check's ancestry test passes; `git -C` avoids the #3097 cwd-drift guard. Three residues remain.

**Strengths**
- The temporary-index protocol protects the user's dirty `example/config/settings.py` and any pre-staged hunks by construction rather than by instruction, and 06-01's negative fixtures test it.
- The 10-01/10-02 shared-commit boundary mirrors the accepted 01-01/01-02 precedent, so the executor is not asked to do anything new in kind.
- C5-H01's three mappings and C5-A08's test synchronization are both in the delivery allowlist, with `icons.py` owned by 10-01 and `tests.py` by 10-02.
- The explicit statement that `gsd_run check evaluation-scope --plan 06.6-10 --commits-only` must list the 10-03 commit aligns with the executor's SUMMARY self-check.

**Concerns**
- MEDIUM: untracked runtime-only evidence inside the core repository. 10-01's verify writes `.planning/phases/.../10-evidence/form-probe.json`; 10-02 writes `delivered-probe.json` and `committed-probe.json` there. `.gitignore` contains no `.planning` or evidence pattern, and prior phases committed evidence directories. The executor contract step 7 says "Never leave generated files untracked"; 10-03 says "commit only the two named core evidence/handoff files". An executor following the contract will either commit the probes (violating 10-03's allowlist) or add a `.gitignore` entry (an unplanned core change). Decide one way in the plan.
- LOW: the three verify commands pass `--delivered-source ../tabler-test`, a cwd-relative path, while the prose says an isolated core worktree must resolve the recorded companion root from the 06 manifest. `config.json` does not set `use_worktrees: false` and `parallelization` is true, so a worktree executor is possible even though prior phases degraded to sequential. Either the utility must resolve `../tabler-test` against the manifest-recorded core root, or the commands should pass the absolute recorded root.
- LOW, open question: the executor contract's step-0 guard refuses commits on a protected or default branch. The plan says "Do not change branches" but never records which branch the companion is on, nor whether the user's amendment ("ordinary scoped local commits") is meant to cover a companion `main`. Companion branch state is not in the embedded excerpts and cannot be checked here. The plan should record the branch in 10-01's preservation snapshot and state the policy explicitly, so the executor does not have to choose between the core guard and the authorization.

**Suggestions**
- Add `10-evidence/*.json` to 10-03's `files` and commit them, or state a `.gitignore` rule and list `.gitignore` as a modified file.
- Replace `../tabler-test` in the three verify commands with the manifest-recorded absolute root, or define that the utility resolves relative companion paths against the recorded core root.
- Record companion `HEAD`/branch in the 10-01 snapshot and state: "A protected-branch name on the companion is authorized by the 2026-11-02 amendment; record it, do not halt," or the opposite, but decide.

**Risk Assessment:** MEDIUM. The protocol is sound; the three residues are small but each is the kind of ambiguity that stalls an autonomous executor at the finish line.

---

## Cross-plan assessment

**Dependency ordering.** The wave graph holds under the companion's own tests, not only the core's. Plan 07 depends on 03 and 04, which is required because the companion's `test_every_theme_key_is_an_upstream_key` demands the four new keys exist in core before `TABLER_BUTTON_CLASSES` gains them. Plan 02 before 07 is required for `register_label_mode_defaults` to exist in `ready()`. Plan 10 after 07 and 09 after 10 is correct given 09's delivered-source binding.

**Scope.** No scope creep found. The one scope-adjacent item, the companion's stale `<input type="submit">` assertion, is a Phase 6 drift that cycle 5 already dispositioned as a baseline-recording obligation; the plans do not widen into repairing it, which is consistent with D-13.

**Security.** CSRF enforcement, authorization preservation and escaping are tested at the right layers (plans 01, 05, 07). The temporary-index commit protocol in plan 10 is the only new write path and is guarded by the 06-01 fixtures.

**Performance.** Only the 06-01 whole-suite collection is heavier than needed; previously dispositioned.

**Executor-contract verdict on C5-A01.** The plan's reading is correct: the contract does not require every task to produce a core commit, it requires that nothing core-tracked is left uncommitted and that the SUMMARY's measured commit count is honest. Plan 10 satisfies both, with the untracked-evidence residue above as the one remaining conflict.

## Overall risk: MEDIUM

Zero HIGH. One MEDIUM executable gap (plan 10 untracked runtime evidence versus executor step 7), two LOW gaps (relative companion path in plan 10 verify commands; undeclared companion branch policy), one LOW documentation window (plan 04/08 theme.md literal-class sentences), and two open questions that only companion inspection can close (`django_tabler.icons.ICONS` contents, native `formactions.html` consumption). All C5 findings are incorporated with source-consistent mechanics; no previously resolved item is re-counted here. Execution evidence, not plan text, remains the gate for THEME-05.
