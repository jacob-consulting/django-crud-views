# Cross-AI Plan Review — Phase 06.6, cycle 7 (HEAD `2630278`)

**Reviewer mode:** read-only. Every claim below was checked against the checkout at `2630278bef3fac6319f84241a0bba589c69c0100` (product/test/docs tree byte-identical to the pinned pre-phase revision `cb26af4`; `git diff --stat cb26af4 HEAD -- src tests docs examples noxfile.py` is empty) and against the embedded companion excerpts at `885dfc7`. The installed executor contract and `~/.codex/gsd-core/workflows/execute-plan.md` were read; the `gsd-core/bin` tooling itself is outside the permitted directories, so its verbs are cited from the workflow text only (see Open questions).

**Headline:** the six prior cycles' fixes are genuinely incorporated. Of the items I checked, every source premise the plans rely on holds. Two unresolved, executable gaps remain, both cheap to close: (1) plan 10 writes to the companion at absolute paths outside any core worktree, which the installed executor's worktree path-containment guard refuses, and the plan never names that rule or requires sequential dispatch; (2) five verify commands in plans 07 and 10 expand `$CV_THEME_PYTHON` in a shell where the executor contract says env state does not persist, so they run with an empty runtime path unless the executor improvises. Everything else is LOW or an open question.

---

## 06.6-01

### Summary
Plan 01 fixes the nested-form/duplicate-token defect at the render boundary and hardens helper diagnostics. Every premise is confirmed in source: `cv_render_form` flattens the context (`src/crud_views/templatetags/crud_views.py:464-466`), the inner template reads `form.helper` twice (`src/crud_views/templates/crud_views/tags/form.html:3-6`), both library helpers construct a bare `FormHelper()` with crispy's default `form_tag=True` (`src/crud_views/lib/crispy/form.py:43-50,136-146`), and all four frame goldens contain two `<form` starts and two tokens on one normalized line (`tests/test1/golden/form_frame/create.html`, `delete.html`: `<form class="cv-form"...><input ... csrfmiddlewaretoken ...><form method="post" ><input ... csrfmiddlewaretoken ...>`). The pack's token branch is independent of `form_tag` on both floor and current packs (`whole_uni_form.html:4-7` in both `.nox` envs), so the plan's "suppress inner CSRF separately" is required, not optional.

### Strengths
- **Atomic boundary is correct.** `_CustomHelperForm` and `_DeleteCustomHelper` build `FormHelper()` without `form_tag=False` (`tests/test1/test_form_button_checks.py:560-583`), so 01-02's fixture migration in the same commit as the renderer is necessary; the plan says so.
- **Context-tier preservation has a proven analog.** `cv_alert` uses `context.push` and `template.template.render(context)` (`crud_views.py:453-455`); the owner-tier helpers the plan asks to read first exist (`src/crud_views/lib/crispy/buttons.py:34-95`).
- **Enforced-CSRF pattern exists to copy** (`tests/test1/test_form_validation.py:76-105`, three `Client(enforce_csrf_checks=True)` cases).
- **Normalizer is left alone.** `_norm` only replaces token values and whitespace (`tests/test1/test_form_frame.py:44-47`); raw assertions are added beside it, as 01-03 requires.

### Concerns
- **LOW — tracer commit deviation is by design but must be reported.** The executor contract says a `type="tracer"` task is "executed and committed exactly like auto"; 01-01 defers its commit to 01-02. This was accepted in round 1 (H02/H03) and is correct for green history, but the SUMMARY should record it as a planned deviation so `verify-work`'s ledger math (`plan_head_before`) does not look like a missing commit.

### Suggestions
- State in 01-01's `<done>` that the tracer feedback gate re-runs the verify before 01-02 begins (the contract does this automatically in `end-of-phase` mode with automated-only verify), so no human checkpoint is synthesized.

### Risk Assessment
**LOW.** Premises verified; mechanism bounded; helper-copy experiment has an explicit stop condition.

---

## 06.6-02

### Summary
Adds the validated theme layer to the label-mode floor. Source matches the plan exactly: `LABEL_MODE_DEFAULTS` is a `MappingProxyType` (`src/crud_views/lib/view/label_mode.py:22-25`), `_UNSET` is distinct from explicit `None` (`:28`), every invalid-setting fallback lambda returns the package table (`:106-118`), `form_label_mode` nests `default_label_mode("form")` as its fallback (`:129-145`), and the autouse conftest fixture resets only `_warned` (`tests/test1/conftest.py:23-32`). E108 validates shape/key/mode from the raw setting (`src/crud_views/lib/settings.py:160-188`). Both W292 branches already call the public resolver (`src/crud_views/lib/view/buttons.py:435-437`, `:568-571`), so the plan's "prove, don't rewire" instruction is right.

### Strengths
- **A17 recursion guard is real.** Because `form_label_mode` → `default_label_mode` → `_invalid_label_mode` can chain, a setting-free `_theme_or_package_default` is the correct terminal.
- **C3-A03 composed case is reachable** through the nested fallback above; the dedup register is keyed `(location, repr(value))` (`label_mode.py:73-79`), so the plan's "use distinct malformed values" instruction avoids masking.
- **Rebind-under-lock publication** fits the existing `threading.Lock` pattern (`label_mode.py:31-32`).

### Concerns
- None unresolved.

### Suggestions
- Add one assertion that `LABEL_MODE_DEFAULTS` remains a `MappingProxyType` after registration, guarding against an accidental dict rebind of the package layer.

### Risk Assessment
**LOW.**

---

## 06.6-03

### Summary
Resolves the positively reproduced floor incompatibility. Verified: the floor pack template never reads `css_class` (`.nox/crispy_floor-3-12-django-6-0/.../bootstrap5/layout/formactions.html:1`), the current pack does (`.nox/tests-3-12-django-5-2/.../formactions.html:3`), and crispy 2.0's `FormActions.__init__` accepts and stores `css_class` (`crispy_forms/bootstrap.py:299-302`), so the failure is template-side only. Both floor environments exist (`.nox/crispy_floor-3-12-django-4-2`, `-6-0`). `CRISPY_FLOOR` and the single deselect are as quoted (`noxfile.py:24`, `:56`). The filter helper caches `_cv_actions` per prepared layout (`src/crud_views/lib/views/list.py:102-105,165-175`), so H05's "re-resolve classes each render" instruction targets the right object. The 84-key count is live in both the test and docs (`tests/test1/test_button_classes.py:105`, `docs/reference/buttons.md:151`), making the 86→88 handoff from plan 04 arithmetically consistent.

### Strengths
- **Discriminator predicates are source-exact** (pack name + installed-distribution origin + whole-source equality with the nine-line floor template), not version sniffing.
- **Filter hidden inputs stay pack-owned** (`list.py:112-123` uses `add_input(layout.Hidden(...))`), so the plan's "do not move hidden controls" is consistent with existing structure.

### Concerns
- None unresolved.

### Suggestions
- The floor template's `{% if formactions.attrs %} {{ formactions.flat_attrs }}` branch (`formactions.html:1`) depends on the 2.0 `LayoutObject` attribute names; keep the fixture string byte-exact and include `attrs`/`flat_attrs` in the compare (the plan already says so, C4-A04).

### Risk Assessment
**LOW–MEDIUM.** Mechanism is bounded; the only risk is the experiment finding no compliant bridge, which the plan routes to a decision rather than a weakened contract.

---

## 06.6-04

### Summary
Two utility keys with byte-identical defaults. Verified: the leaf hardcodes ` alert-dismissible fade show` and `btn-close` (`src/crud_views/templates/crud_views/tags/alert.html:2,5`); the golden is raw bytes with that spacing (`tests/test1/golden/alerts/dismissible.html`); the adapter hook is `data-cv-alert-dismiss` consumed by `cv.adapters.alert` (`src/crud_views/static/crud_views/js/adapters.js:94`); the theme.md single-fence guard exists (`tests/test1/test_alerts.py:250-253`) and the override recipe is executed (`:257`). W362 accepts any key in `DEFAULT_BUTTON_CLASSES` and rejects mode-suffixed unknowns (`src/crud_views/lib/button_classes.py:328-346`).

### Strengths
- **A03 whitespace rule is precisely specified** (no separator for empty/None; `class=""` on the close control), which is what keeps the default golden byte-identical.
- **Inventory bump lands with the defaults** (84→86), so plan 03's 86→88 is sequenced.

### Concerns
- None unresolved.

### Suggestions
- None.

### Risk Assessment
**LOW.**

---

## 06.6-05

### Summary
Expands ownership to all stock forms and workflow. Verified: the workflow action template calls `{% crispy form form.helper %}` directly inside its own POST form (`src/crud_views_workflow/templates/crud_views_workflow/view_workflow.action.html:8-16`) and loads `crispy_forms_tags` (`:2`, A12); `WorkflowView(CustomFormView)` inherits `cv_content_template = "crud_views/view_custom_form.content.html"` (`src/crud_views_workflow/lib/views.py:18`, `src/crud_views/lib/views/form.py:51`), confirming C3-A01; the modal shell includes `view.cv_content_template` (`modal/content.html:9`); `cv_modal_supported` defaults False with E251 (`src/crud_views/lib/view/base.py:111,169-170`) and is True only on custom/delete (`form.py:20,52`, `delete.py:55`). The parent-formset raw guard counts only `<form` starts (`tests/test1/test_formsets.py:33`); the two redundant overrides are exactly where named (`tests/test1/app/views_formset.py:45-49`, `examples/bootstrap5/formsets/views.py:37-40`); child formset helpers already set `disable_csrf = True` (`src/crud_views/lib/formsets/inline_formset.py:58-59,144-145`), so "child tokens stay suppressed" is accurate. The delete template omits its form when `has_protected_objects` (`view_delete.content.html:16`).

### Strengths
- **Protected-delete and no-choice exceptions are grounded in real branches**, not a blanket one-form rule.
- **C2-A05 deferral is accurate**: the named conditional/authorization/browser fixtures set `form_tag=False` and stay compatible (`examples/bootstrap5/conditional/views.py:136`, `tests/test1/test_fragment_authorization.py:180,195`, `tests/browser/conditional_formsets_server.py:142,261`).

### Concerns
- **LOW — path ambiguity.** 05-01 says "read base.py's cv_modal_supported/E251 gate"; the file is `src/crud_views/lib/view/base.py`, and `src/crud_views/lib/views/base.py` does not exist. An executor grepping the `views/` package first wastes a step.
- **LOW — deferral list is incomplete.** `test_fragment_authorization.py:1586` is a third `form_tag=False` helper not named in C2-A05; harmless (it is in the do-not-touch set) but the SUMMARY should not claim the list is exhaustive.

### Suggestions
- Write the full path `src/crud_views/lib/view/base.py:111,169` in 05-01's read_first.

### Risk Assessment
**LOW–MEDIUM.** Broad request matrix, but every branch it must distinguish exists in source.

---

## 06.6-06

### Summary
Builds the Django-free provenance/baseline/replay/delivery utility and captures the real baseline. The companion facts in the embedded source match the plan: pack name and Python >=3.14/Django 6.1 pins (`../tabler-test/pyproject.toml:4-6,12-15,32`), the eight shadow templates named as the minimum discovery set are all present in the excerpt, `checks.py`'s `check_tabler_icons` and `icons.py`'s `render` are the counted behavior (`crud_views_tabler/checks.py:8-27`, `icons.py:50-52`). `tests/browser` has no `__init__.py` or `conftest.py` and the root `tests/conftest.py` is empty, so the importlib loading strategy and "no collection side effects" claims hold.

A concrete baseline expectation the plan does not state but will meet: the companion asserts `set(TABLER_ICONS) == set(DEFAULT_ICONS)` (`crud_views_tabler/tests.py:62-63`). Core `DEFAULT_ICONS` has `save`, `cancel`, `filter-reset` (`src/crud_views/lib/icons.py:51-53`); `TABLER_ICONS` has 35 keys without them (`crud_views_tabler/icons.py:12-47`). So the unmodified baseline against `cb26af4` has at least one failing node (`test_every_upstream_icon_name_is_mapped`), and plan 07's three mappings are what turn it green. This is exactly the "required scenario broken at baseline" case the plans already handle; 06-02's capture should expect a non-zero failure count rather than a clean run.

### Strengths
- **C6-A03 recorded-root resolution** removes the cwd-sibling dependency that a core worktree would break.
- **C5-A01 commit-receipt validation** reads companion objects with `git -C` against the verified root, and the plan correctly requires both core and companion checks since the core evaluation scope cannot see companion commits.
- **Purpose-based D-18 counting** is fully specified, with positive and negative fixtures.

### Concerns
- **LOW — verify command shape contradicts its own done note.** 06-01's verify runs `pytest tests -k theme_adoption_sources -n 4`, which collects the entire Django suite under `tests/test1` to deselect to a handful of file-based tests, while the `<done>` says these tests "run serially". Plan 09 already uses the direct form (`pytest tests/browser/test_theme_adoption_sources.py -q`).
- **LOW — 06-01 is one task carrying capture, check, replay, delivered-source, require-committed, bundle merging and disposable Git fixtures.** It is executable, but the executor's three-attempt fix limit applies per task; a failure late in the matrix stalls everything earlier. Same-file sequential tasks are permitted (plan 01 uses them), so splitting is cheap.
- **LOW — dual writers on the delivery bundle** (see 06.6-07 C7-L02).

### Suggestions
- Replace 06-01's verify with `pytest tests/browser/test_theme_adoption_sources.py -q` (keep `env -u`).
- Split 06-01 into 06-01a (capture/check/replay + inventory rules) and 06-01b (delivered-source/require-committed/bundle), both owning the same two files.
- Record in 06-02's action that the icon set-equality node is an expected baseline failure fixed by 07, so D-13 classification does not mislabel it as "unrelated".

### Risk Assessment
**MEDIUM.** The utility is the trust root for plans 07, 09 and 10; its size is the main execution risk, not its design.

---

## 06.6-07

### Summary
Real Tabler acceptance and the retained patch. Companion claims verified from the embedded source: `TABLER_BUTTON_CLASSES` lacks the four keys and `test_table_values` is whole-dictionary equality (`buttons.py:3-44`, `tests.py:98-139`), so C5-A08's literal-dictionary extension is required; `test_every_theme_key_is_an_upstream_key` will accept the four single-colon keys once plans 03/04 add them (`tests.py:84-90`); the alert copy hardcodes classes and `data-bs-dismiss` (`templates/crud_views/tags/alert.html:7,17`), so C4-A02's parity-test delta is unavoidable; `test_plain_include_matches_cv_messages` compares normalized markup (`tests.py:556-572`); the browser harness conventions the plan copies exist (`tests/browser/presentation.cjs:2-5` port rules, `:396` runtime discovery, `:405` loopback probe; `presentation-config.test.cjs:13-14` rejection matrix). `CRUD_VIEWS_EXTENDS` shell and the form-frame shadow match the plan's description (`crud_views_tabler/page.html`, `snippets/form_frame.html:3-5`).

### Strengths
- **C6-A01 cancel-no-url matrix** is specified per mode with tag/type/href/icon/side-effect assertions; it maps onto Phase 6.1's "URL-less cancel falls back to a button" contract.
- **No manufactured pack adaptation**: the native `layout/formactions.html` consumes `css_class` per the research addendum, and the plan treats adaptation as conditional on a failed render.

### Concerns
- **MEDIUM (C7-M02) — `$CV_THEME_PYTHON` is an ambient variable the verify commands cannot rely on.** Both 07-01 and 07-02 verifies are `CV_FOCUS_PYTHON="$CV_THEME_PYTHON" node ...`. The executor contract states each Bash call is a fresh shell ("Each Bash call is a FRESH shell, so the ledger persists on disk"; harness: "Shell state (env vars, functions) does not persist"). Plan 06 defines `CV_THEME_PYTHON` as a variable the *Python* utility reads with a default; nothing exports it for Node. Run verbatim, `CV_FOCUS_PYTHON` is empty, and `presentation.cjs:396`'s `runtimePath` pattern falls back to `.nox/tests-3-12-django-5-2/bin/python`, a Django 5.2 core venv that cannot import `crispy_tabler`/Django 6.1. The plan's `fails_when` ("missing/incompatible CV_THEME_PYTHON") means the harness must fail closed, so this is not a silent wrong-runtime pass, but the verify as written cannot succeed without the executor improvising. Same issue in plan 10 (three commands).
- **LOW (C7-L01, open question) — native glyph existence is not provable from the excerpt.** The plan asserts `check`, `arrow-left`, `filter-x` exist in `django_tabler.icons.ICONS` and forbids editing that module. `svg()` returns `""` for unknown names (`tests.py:52`), so existing assertions such as `assertIn(str(svg("arrow-left")), …)` (`tests.py:182-184`) pass trivially and prove nothing. If any name is absent, `crud_views_tabler.W001` fires (`checks.py:19-26`) and `test_system_checks_pass` fails at `--fail-level WARNING` (`tests.py:163-164`). 07-02's nonempty-SVG comparison would catch it at execution, but the plan gives no fallback.
- **LOW (C7-L02) — two writers on one committed bundle.** 07-01 (Node) writes `form_probe` into `10-companion-delivery.json`; 06-01 (Python) writes `delivered_probe`/`committed_probe`. Both must implement the same atomic-merge and digest rules. The negative tests catch dropped slots, but schema drift between the two implementations is a reproducibility risk that a single merge entry point removes.

### Suggestions
- Record the verified interpreter path in `06-companion-baseline.json` (e.g. `companion_python`) and have `theme-adoption.cjs` resolve `CV_FOCUS_PYTHON` from the recorded manifest when the variable is unset, rejecting anything that does not match the recorded identity; or write the literal path in the verify commands.
- Add a 07-02 preflight asserting the three names are in `ICONS`, with a stated fallback (choose another existing native glyph with the same semantics and record the substitution in the handoff) rather than an undefined halt.
- Let Node delegate the merge: `theme_adoption_sources.py --merge-probe form_probe <tmpfile>` so one implementation owns the bundle schema.

### Risk Assessment
**MEDIUM.** Largest execution surface in the phase; one executable gap in the verify wiring.

---

## 06.6-08

### Summary
Executable docs and paired migrations. Verified: `test_migration_e108_location_inventory` pins the sentence "falls back to its package floor." (`tests/test1/test_label_mode_docs.py:786-797`) and `docs/migrating-1.0.md:58-61` carries the E108 paragraph, so H07's pairing is real; the single-fence guard under "### Custom alert frame" exists (`test_alerts.py:250-253`; `theme.md:308`); `register_button_classes` recipes are the pattern to mirror (`theme.md:88-113`); the stale package-only prose the plan must update is where it says (`action_menus.md:100,111,130,188`; `settings.md:78-81,91,143`). Tutorial/list-view pages and `test_form_button_docs.py`/`test_presentation_migration_docs.py` exist.

### Strengths
- **C2-A02 standalone-wrapper note** is grounded: the library helper's `form_tag=False` changes standalone crispy output, and the plan pairs it as Breaking with a tested caller-owned recipe.
- **Docs-count discipline** is enforced by live tests (`test_button_classes.py:112-116`).

### Concerns
- None unresolved.

### Suggestions
- `settings.md:78` says invalid `CRUD_VIEWS_LABEL_MODE_DEFAULTS` values "raise crud_views.E108"; after D-07 the runtime path warns and falls back to the theme layer. 08-01 lists `settings.md`; make sure that cell is rewritten, not only the longer section.

### Risk Assessment
**LOW.**

---

## 06.6-09

### Summary
Final gates and Phase 7 handoff. Verified: the cached runtimes are exactly `tests-3-12-django-4-2`, `tests-3-12-django-5-2`, `crispy_floor-3-12-django-4-2`, `crispy_floor-3-12-django-6-0` (`.nox/`), so the four pytest lanes and the H12 "current-pack 6.0 untested" disposition are accurate; `CRISPY_FLOOR_TESTS` is the list A15 extends (`noxfile.py:27-51`); the example project has its own `pytest.ini` with `DJANGO_SETTINGS_MODULE = project.settings` and `pythonpath = .` (`examples/bootstrap5/pytest.ini:1-5`) and eight test modules; vitest and the integration config exist; `.venv/bin/mkdocs` and `ruff` exist. The halted-summary contract matches the atomic close-out invariant (`execute-plan.md:12-33`).

### Strengths
- **C5-A01 two-repository validation** is the only way a core-scoped evaluation can certify companion delivery; the plan says so explicitly.
- **Evidence reuse is fingerprint-bound**, and the plan refuses report-only completeness flags.

### Concerns
- **MEDIUM (shares C7-M01 with plan 10)** — `--check-final` reads companion objects at an absolute path outside the core tree. That is read-only and does not trip the write-containment guard, but 09 inherits plan 10's dispatch assumption; see 06.6-10.
- **LOW** — 09-01's first verify runs the utility tests without `env -u CV_THEME_SOURCE …`; the plan relies on 06-01's tests clearing those variables themselves (stated in 06-01's action). Keep that requirement when 09 adds `--check-final` fixtures.

### Suggestions
- Add the `env -u` prefix to 09-01's utility-test verify for symmetry with 06-01.

### Risk Assessment
**MEDIUM.** Correctly gated; depends on 06/07/10 evidence that does not exist yet.

---

## 06.6-10

### Summary
Delivers the verified companion delta and scoped local commits. The repository-boundary section correctly distinguishes GSD `sub_repos` (not configured: `.planning/config.json` has no `sub_repos`) from an explicit multi-repository task, keeps the core ledger core-only, and resolves the companion through the recorded manifest. The executor contract's single-repo commit branch therefore applies to 10-03 only; the shared 10-01/02 companion commit via `git -C` is outside the GSD commit protocol and is authorized by the user's amendment. The temporary-index protocol avoids every command in the executor's destructive-git list. Core is a plain checkout on `introduce-gsd` (`.git` is a directory), no `core.hooksPath` is set and no core hooks are installed, so core-side hook mutation is not a current risk.

### Strengths
- **Evaluation-scope accounting** is handled honestly: the plan expects an evidence-only `changedFiles` scope and separates Companion Commits from Task Commits.
- **C6-A02** removes the earlier temporary-sidecar dependency; the three probes live in one committed file.

### Concerns
- **MEDIUM (C7-M01) — worktree write-containment guard is not addressed.** The installed executor's protocol step 0b (#3099) says that in worktree mode, before any Edit/Write with an absolute path, the path must resolve inside `git rev-parse --show-toplevel` or the executor prints `FATAL … is outside the worktree` and exits. Plan 10's `files_modified` are `../tabler-test/src/...`, which resolve to `/home/alex/projects/alex/tabler-test/...`, outside any core worktree. This project runs with `parallelization: true` and phase branching (`.planning/config.json:4,13-19`), `use_worktrees` defaults to true (`execute-plan.md:101`), and Pattern A dispatch resolves `harness-worktree` isolation (`execute-plan.md:121-131`). STATE.md shows earlier phases degraded to sequential on fork-base mismatch (`STATE.md:76,176`), which is why this has not bitten before, but the plan cannot rely on that. The plan's boundary text covers cwd, ledger and recorded-root resolution yet never names step 0b or declares the companion root an authorized out-of-tree write target.
- **MEDIUM (C7-M02)** — three verify commands use `CV_FOCUS_PYTHON="$CV_THEME_PYTHON"`; see 06.6-07.
- **LOW (C7-L05) — index reconciliation is elaborate.** Swapping a reconciled index under `index.lock` is correct in intent but is the most fragile step in the phase. A simpler equivalent: after committing from the temporary index, if the original index has no staged entries for the six task-owned paths, run `git -C root update-index` for just those paths; otherwise halt (which the plan already permits).
- **LOW — companion branch is unrecorded in the plan.** The plan captures "HEAD, branch" at runtime but does not say whether committing to the companion's current branch (possibly its default) is intended. The user amendment authorizes "ordinary scoped local commits", so this is a reporting item, not a gate.

### Suggestions
- Add to "Repository and commit boundary": "The verified companion root from `06-companion-baseline.json` is the only permitted Edit/Write target outside the core tree; this is a deliberate, user-authorized exception to the worktree containment guard (#3099), substituted by the recorded-root identity check. If dispatched in a harness worktree, the executor must not treat these paths as a containment violation." Alternatively require wave 4 to run with `dispatch-isolation --force-isolation none`.
- Fix the `$CV_THEME_PYTHON` wiring as in 06.6-07.
- Prefer the simpler index reconciliation above; keep the full protocol only for the same-file-staged-hunk case.

### Risk Assessment
**MEDIUM.** Design is sound and the amendment covers scope; the remaining risk is executor-mechanics, not product behavior.

---

## Cross-plan comparison

- **Dependency order is consistent**: 01 → {02, 03 (also ← 04), 05}; 06 (wave 1) → 07 → 10 → 09; 08 parallel with 07. Shared-file ownership is sequential everywhere it matters (`theme_adoption_sources.py`: 06 then 09; `10-companion-delivery.json`: 07-01 writer, 10 owner).
- **Executor contract fit.** Only three contract points are strained, all in plans 07/10: (a) tracer-task commit deferral (accepted since round 1, applies to 01-01 and 10-01); (b) worktree write containment (C7-M01, new, unresolved); (c) ambient env in verify commands (C7-M02, new, unresolved). The claim that "every task commit must be core" is indeed not what the contract says; the contract's single-repo branch applies only to commits the executor itself makes, and plan 10's companion commit is outside it. The core ledger measurement remains correct.
- **Baseline reality check.** The unmodified companion against current core already fails `test_every_upstream_icon_name_is_mapped` (`crud_views_tabler/tests.py:62-63` vs `src/crud_views/lib/icons.py:51-53` and `crud_views_tabler/icons.py:12-47`). This is evidence the C5-H01 mappings are mandatory, and a concrete node ID plan 06-02 should expect to record.

## Open questions (could not be verified here)
1. `django_tabler/icons.py` is not in the embedded excerpt; existence of `check`, `arrow-left`, `filter-x` in `ICONS` is asserted by the plan, not shown.
2. `~/.codex/gsd-core/bin` is outside the permitted directories; `gsd_run check evaluation-scope --commits-only` is cited from `execute-plan.md:195`, not from the tool source.
3. Companion `core.hooksPath` and sample-hook status are taken from the plan's revision-time note; not re-inspected.

## Genuinely unresolved executable gaps (cycle 7)

| ID | Severity | Plans | Fix size |
|---|---|---|---|
| C7-M01 | MEDIUM | 10 (09 inherits) | one paragraph in plan 10's boundary section, or a forced-sequential dispatch note |
| C7-M02 | MEDIUM | 07, 10 | record `companion_python` in the 06 manifest and resolve `CV_FOCUS_PYTHON` from it when unset; or literal path in five verify commands |
| C7-L01 | LOW / open | 07 | preflight + stated fallback for the three native glyphs |
| C7-L02 | LOW | 06, 07, 10 | single merge entry point for the delivery bundle |
| C7-L03 | LOW | 06 | direct-file verify command; optional task split |
| C7-L04 | LOW | 05 | write `src/crud_views/lib/view/base.py` explicitly |
| C7-L05 | LOW | 10 | simpler index reconciliation path |

## Overall risk assessment

**MEDIUM.** Plans 01–05 and 08 are source-grounded with no unresolved gaps and would be LOW on their own. Plans 06, 07, 09 and 10 carry the phase's real risk because their acceptance depends on fresh companion baseline, browser and delivery evidence that does not yet exist, and because two executor-mechanics details (worktree write containment, non-persistent `$CV_THEME_PYTHON`) would make conforming execution halt on plans 07 and 10 as written. Both are closable with text edits before execution; neither changes scope, authority or any D-01–D-19 decision. All six prior review cycles' fixes are present in the plans and were not re-counted here.
