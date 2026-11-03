# Cross-AI Plan Review — Phase 06.6, cycle 8 (HEAD `3baad01`)

Read-only review of all ten plans against the core checkout at `3baad01`, the installed executor contract supplied in the request, and the embedded companion source at `885dfc7`. I did not access `../tabler-test` or any directory outside the core checkout. Two verification limits apply and are called out where relevant: reads of `$HOME/.codex/gsd-core/bin/gsd-tools.cjs` and the `references/*.md` files were denied, so the GSD commit tool's handling of `GIT_INDEX_FILE` is an open question rather than a finding, and `django_tabler/icons.py` is not in the embedded excerpt, so glyph existence is inferred from the companion tests that exercise those names.

Headline: all cycle-5, cycle-6 and cycle-7 dispositions named in the scope (C5-H01, C5-A01, C5-A08, C6-A01/A02/A03, C7-A01, C7-A02) are present in the plan text and verified against source. The one item the request calls "C7-A03" does not exist in any plan at HEAD. `grep -rn C7-A03 .planning/` returns nothing; the only trace is an adjudication note in `06.6-REVIEWS.md:736` saying no plan edit is needed. That adjudication is not visible to an executor, and the executor's mandatory step 0b still forbids out-of-tree Edit/Write in worktree mode. That is the single genuinely unresolved executable gap; everything else below is LOW or an open question.

## 06.6-01

**Summary.** The problem statement is real and the fix seam is correctly identified. The committed golden `tests/test1/golden/form_frame/create.html:1` contains a nested `<form method="post" >` with a second `csrfmiddlewaretoken`, exactly as the plan claims. The library helper at `src/crud_views/lib/crispy/form.py:43-50` constructs `FormHelper()` with crispy's default `form_tag=True`, and `CrispyDeleteForm.helper` at `:138-146` builds its own helper, so both must change, as the plan says. The inner template `src/crud_views/templates/crud_views/tags/form.html:3-6` reads `form.helper` twice, and `cv_render_form` at `src/crud_views/templatetags/crud_views.py:465-466` flattens the context, while `cv_alert` at `:454` uses `context.push`, which is the preservation pattern the plan adopts.

**Strengths.**
- The two custom-helper fixtures the plan migrates in 01-02 exist and lack `form_tag=False`: `tests/test1/test_form_button_checks.py:560-567` and `:578-585`. H02 is grounded.
- The raw nested-form guard the plan reuses as a parent-formset analog exists at `tests/test1/test_formsets.py:16-34` and scans raw markup, not a repaired DOM.
- `tests/test1/test_form_validation.py` exists for the enforced-CSRF pattern; `test_form_frame.py:44-55` normalizes tokens and whitespace, so the plan's instruction not to alter that normalizer while adding raw assertions is coherent.
- The research-selected `copy(helper); disable_csrf=True` candidate is explicitly an experiment with alias and custom-`__copy__` negative cases, not a locked mechanism.

**Concerns.**
- LOW: none unresolved. The tracer-commit deferral across 01-01/01-02 is a conscious deviation from the executor's per-task commit rule and was accepted in round 1; the TDD RED test commit remains permitted before the combined GREEN commit.

**Suggestions.**
- When writing the SUMMARY, record the shared 01-01/01-02 commit as a deliberate executor-contract deviation so the measured `commits:` count is not misread.

**Risk Assessment.** LOW. Every claim about current source holds; the remaining uncertainty is the helper-copy experiment, which the plan converts into a checkpoint if no strategy satisfies the predicates.

## 06.6-02

**Summary.** The resolver changes are precisely located. `src/crud_views/lib/view/label_mode.py:56-60` reads the setting lazily on every call, and the fallback lambdas at `:99-118` return `LABEL_MODE_DEFAULTS[location]` only, which is the package-only destination D-07 replaces. The autouse fixture in `tests/test1/conftest.py:23-32` resets only `_warned`, confirming the plan's statement that registry isolation must be added. Both W292 branches already route through the public resolver: context at `src/crud_views/lib/view/buttons.py:435-442` and form at `:568-578`, so theme floors propagate to checks without new wiring, as the plan says.

**Strengths.**
- E108 at `src/crud_views/lib/settings.py` validates shape, location and mode from `LOCATIONS` and `LABEL_MODES`; the plan reuses that vocabulary rather than a literal list.
- A17's setting-free `_theme_or_package_default` avoids recursion while a malformed setting is installed, which matters because `form_label_mode` at `label_mode.py:146-160` chains into `default_label_mode` from its own fallback.
- Snapshot-by-rebind under a lock matches the `monkeypatch.setattr(label_mode, "_warned", set())` pattern already in conftest.

**Concerns.**
- LOW: none unresolved. The owner-first form map precedence at `button_data.py:308-317` is unchanged by this plan and the plan says so.

**Suggestions.**
- None beyond the plan's own matrix.

**Risk Assessment.** LOW.

## 06.6-03

**Summary.** The floor incompatibility is reproduced in the cached environment, not inferred: `.nox/crispy_floor-3-12-django-6-0/.../bootstrap5/layout/formactions.html` renders `<div ... class="mb-3">` and never reads `css_class`. Both floor interpreters the plan runs exist (`.nox/crispy_floor-3-12-django-4-2`, `.nox/crispy_floor-3-12-django-6-0`). W362 at `src/crud_views/lib/button_classes.py:326-347` accepts any key in `DEFAULT_BUTTON_CLASSES`, and `_action_key_parts` returns `None` for `form:actions:icon` because `actions` is not in `FORM_KINDS` (`:240`), so mode-suffixed utility keys stay invalid exactly as the plan requires.

**Strengths.**
- The inventory arithmetic is owned: `tests/test1/test_button_classes.py:105` asserts 84 and `:112-116` parses the documented count at `docs/reference/buttons.md:151`. Plan 04 moves it to 86 first and plan 03 to 88, consistent with `depends_on: ["06.6-01", "06.6-04"]`.
- The filter helper's once-per-prepared-layout action resolution at `src/crud_views/lib/views/list.py:172-175` is why H05 demands render-time class resolution on the cached group rather than at construction. The plan says exactly that.
- The bridge discriminator is pack-name plus resolved-origin plus exact floor-source equality; the companion pack is `crispy_tabler`, so the bridge never engages there and the native template is proven instead.

**Concerns.**
- LOW: none unresolved.

**Suggestions.**
- Keep the floor-template fixture string byte-identical to the file above; the test should read the installed file and compare, not embed a hand-copied variant.

**Risk Assessment.** LOW on current source; the floor bridge remains an experiment with an explicit stop condition.

## 06.6-04

**Summary.** The alert leaf hardcodes both literals the keys replace: `src/crud_views/templates/crud_views/tags/alert.html:2` has ` alert-dismissible fade show` and `:5` has `class="btn-close"` with `data-cv-alert-dismiss` and the translated close label. The A03 separator rule is necessary because the default golden bytes include the leading space only inside the dismissible branch.

**Strengths.**
- `tests/test1/golden/alerts/dismissible.html` exists as the byte guard.
- `tests/js/adapters.test.js` exists for the 04-02 vitest preservation command.
- `cv_button_class` is a simple tag, so `as` capture for the separator rule is available.

**Concerns.**
- LOW: none unresolved.

**Suggestions.**
- None.

**Risk Assessment.** LOW.

## 06.6-05

**Summary.** Every structural claim checks out. `src/crud_views_workflow/templates/crud_views_workflow/view_workflow.action.html` calls `{% crispy form form.helper %}` directly inside its own `<form>` and loads `crispy_forms_tags`, so A12's unused-load removal follows the switch. `src/crud_views/lib/view/base.py:111` defaults `cv_modal_supported` to False and `:169-170` is E251; `CreateView` (`create.py:12`) and `UpdateView` (`update.py:9`) do not set it, while `CustomFormView` (`form.py:20`), `CustomFormNoObjectView` (`form.py:52`), `DeleteView` (`delete.py:55`) do. `WorkflowView(CustomFormView)` at `src/crud_views_workflow/lib/views.py:18` sets no `cv_content_template`, so C3-A01's inherited custom-form modal body is the actual behavior, and `modal/content.html` includes `view.cv_content_template`.

**Strengths.**
- The delete content template owns its form only when `not has_protected_objects` and no protection errors exist (`view_delete.content.html`), matching the plan's explicit omission exceptions.
- The two parent overrides removed in 05-02 do nothing but `form_tag=False`: `tests/test1/app/views_formset.py:45-49` and `examples/bootstrap5/formsets/views.py:37-41`. The deferred C2-A05 list is accurate (`examples/bootstrap5/conditional/views.py:136`, `tests/test1/test_fragment_authorization.py:180,195,1586`, `tests/browser/conditional_formsets_server.py:142,261`).

**Concerns.**
- LOW: none unresolved.

**Suggestions.**
- None.

**Risk Assessment.** LOW.

## 06.6-06

**Summary.** This plan now carries the C5/C6/C7 validator contracts in one task, and each contract is grounded in the companion excerpt. The counted customization inventory names the eight shadows actually present under `src/crud_views_tabler/templates/crud_views/` in the embedded tree, and the counted behavior (`checks.py` `check_tabler_icons`, `icons.py` `render`) exists. The C7-A02 record of `companion_python` plus `sys.prefix` and versions, reloaded from the manifest under `Path(__file__).resolve().parents[2]`, addresses the fresh-shell problem that the analogous harness exhibits at `tests/browser/presentation.cjs:396` (core `.nox`/`.venv` fallback) and `tests/browser/presentation-config.test.cjs:7-8` (ambient variable required).

**Strengths.**
- Collection is feasible: `pyproject.toml:129-130` sets no `testpaths`, `tests/__init__.py` and `tests/conftest.py` exist, and `tests/browser/` holds no Python tests today, so the new file is collected by `pytest tests` without a package marker.
- The C5-H01 validator is checking the right thing. Core `DEFAULT_ICONS` at `src/crud_views/lib/icons.py:15-53` minus the companion `TABLER_ICONS` at `icons.py:12-47` is exactly `{save, cancel, filter-reset}`.
- C7-A01 as now written matches source: `button_data.py:354` keeps `""` via `_attr_text` (`:229-233` returns None only for None/False), `:357` selects `button` for a falsy destination, the leaf emits `data-cv-cancel-url=""` only when not None (`tags/button/form.html:3`), and `viewset.js:40-43` assigns that empty value to `location.href`, which is a same-document GET. `tests/test1/test_crispy_buttons.py:2464` ("empty-url", `tag="a"`) already pins the button fallback.

**Concerns.**
- LOW (not previously named): the companion test `test_every_upstream_icon_name_is_mapped` (`tests.py:62-67`) asserts `set(TABLER_ICONS) == set(DEFAULT_ICONS)`. Against the pinned pre-phase core it fails today, and the three mappings in plan 07 make it pass. No plan names this expected failing-to-passing flip, so 07-03's D-13 comparison could log it only as a vanished baseline failure instead of a phase-fixed, related failure.
- Open question: the companion's current branch is never recorded as a policy input. Plan 10 says "Do not change branches" and commits with `git -C`. If that branch is `main`, the commit is still user-authorized, but the executor's protected-branch guard is written for core and an executor may hesitate. Say explicitly that the companion commit lands on the currently checked-out branch under the D-11 amendment.

**Suggestions.**
- Add one sentence to 06-01's D-13 classification: a baseline failure whose node ID is in the required ThemeAdoptionTests/icon-mapping set must be recorded as "fixed by phase", not "unrelated pre-existing".
- Record `git -C "$COMPANION_ROOT" rev-parse --abbrev-ref HEAD` in `06-companion-baseline.json` so plan 10's receipt binds to a named branch.

**Risk Assessment.** MEDIUM, driven by unrun baseline evidence and the size of 06-01, not by unresolved plan text.

## 06.6-07

**Summary.** The browser plan is now consistent with the actual cancel handler and runtime-selection analogs. The port rules match the existing harness (`presentation.cjs:2-5` defaults 8145 and reserves 8143/8144; `conditional-formsets.cjs:28-31` owns 8144). The eight shadow templates and the `data-bs-dismiss` literal in the companion alert copy (`alert.html:17`) are confirmed, and `MessagesParityTests` (`tests.py:556-572`) does a whitespace-normalized equality between the native include and `cv_messages`, so changing the CRUD hook without the C4-A02 mapping would break it, which the plan handles.

**Strengths.**
- The candidate values are exactly what the companion tests need: C5-A08's four pairs extend the literal dictionary at `tests.py:98-139`, which currently mirrors `buttons.py:3-44` entry for entry. `test_every_theme_key_is_an_upstream_key` (`tests.py:84-90`) requires the base of each new key to exist in core `DEFAULT_BUTTON_CLASSES`, so the test delta is correctly bound to the sibling candidate core from plans 03/04.
- Glyph existence for the three mappings is supported by the companion's own tests even without the icon module excerpt: `svg("check", ...)` at `tests.py:307`, `tabler:arrow-left` at `:182-184`, and `filter-close: tabler:filter-x` at `icons.py:25` under the ICONS membership assertion at `tests.py:62-67`.
- The cancel-no-url matrix now distinguishes absent from empty and forbids interception, which is the only truthful way to test `viewset.js:38-44` unchanged.

**Concerns.**
- LOW: none unresolved in plan text. The real risk is execution: Chromium, Playwright and the Python 3.14 venv must all be present at recorded identities.

**Suggestions.**
- For the "empty" branch, assert the navigation request URL equals `document.URL` with the fragment stripped, since `location.href = ""` resolves against the base URL including the query string.

**Risk Assessment.** MEDIUM, purely because acceptance depends on fresh browser and replay results.

## 06.6-08

**Summary.** The documentation guards the plan must respect exist and behave as described. `tests/test1/test_alerts.py:249-254` requires exactly one django/html fence under "### Custom alert frame", and `docs/reference/theme.md:308-321` currently holds exactly one (H08). `tests/test1/test_label_mode_docs.py:786-816` pins the E108 migration paragraph's location inventory and the sentence "falls back to its package floor", which plan 08-02 must update together with `docs/migrating-1.0.md` (H07). `CHANGELOG.md` has `### Breaking` at `:7`, `### Fixed` at `:311` and `### Added` at `:421` under Unreleased.

**Strengths.**
- `test_presentation_migration_docs.py` and `test_form_button_docs.py` exist as the extraction analogs.
- The standalone-wrapper-removal Breaking note (C2-A02) is a correct consequence of `form.py:43-50` gaining `form_tag=False`.

**Concerns.**
- LOW: none unresolved.

**Suggestions.**
- None.

**Risk Assessment.** LOW.

## 06.6-09

**Summary.** Every integration command is grounded in present runtime and configuration. `.nox` contains exactly `tests-3-12-django-4-2`, `tests-3-12-django-5-2`, `crispy_floor-3-12-django-4-2` and `crispy_floor-3-12-django-6-0`, so H12's "current-pack Django 6.0 untested" is accurate and the four floor/current runs are the complete cached set. `noxfile.py` `CRISPY_FLOOR_TESTS` lacks the five new theme modules (A15), and `CRISPY_FLOOR_DESELECT` holds only `test_filter_form_baseline`. `examples/bootstrap5/pytest.ini` sets `DJANGO_SETTINGS_MODULE=project.settings` and `pythonpath = .`; `examples/bootstrap5/project/settings.py:136` enables form=both. `modal-focus.cjs:81` honors `CV_FOCUS_PYTHON`, `conditional-formsets.cjs:26-27` accepts `--case`/`--output`, and `tests/js-integration/formset.test.js:92-108` requires `CV_FRAGMENT_PYTHON`.

**Strengths.**
- `--check-final` consumes the validators plan 06 tests, including the omission fixtures and the two cancel branches, so the final gate cannot pass on report-declared totals.
- Core actuals stay core-only; companion commits are kept out of the canonical Task Commits section.

**Concerns.**
- LOW: the SUMMARY metadata commit stages `.planning/ROADMAP.md` and `.planning/STATE.md` whole-file. Both are already dirty with unrelated edits in the working tree at HEAD (`git status` at session start). This is a GSD-wide hazard rather than a plan-09 defect, but C5-A01's "preserve unrelated index" intent is not met for those two files by whole-file staging.

**Suggestions.**
- Before the metadata commit, hunk-stage or stash-free isolate the pre-existing ROADMAP/STATE edits the same way plan 10 does for the companion, or record in the SUMMARY that they were swept intentionally.

**Risk Assessment.** MEDIUM, because final acceptance is gated on evidence that does not yet exist and on human observations.

## 06.6-10

**Summary.** The repository and commit boundary section is the strongest text in the phase for its purpose. Against the executor contract as supplied, the plan is correct that no rule says every task commit must be core: the task_commit_protocol governs commits the executor makes, `sub_repos` is not configured in `.planning/config.json` so `commit-to-subrepo` is not in play, the per-plan ledger measures `plan_head_before..HEAD` on core only, and `evaluation-scope --commits-only` is satisfied by the 10-03 `docs(06.6-10)` commit. The shared 10-01/10-02 companion commit is the same deferral pattern accepted for 01-01/01-02.

**Strengths.**
- Hunk-level `apply --cached` into a private index, allow-list review by `diff --cached --name-only`, and a second reconciled index for same-file unrelated staged hunks are the right mechanisms for "unrelated staged content stays staged and out of the commit".
- All four delivery commands use the recorded operand and unset both interpreter variables, matching 06/07's resolver contracts.
- 10-03 is the only core commit, holds exactly two files, and the evidence bundle is self-contained.

**Concerns.**
- MEDIUM (unresolved; the "C7-A03" amendment does not exist): the executor contract's step 0b is mandatory in worktree mode and prints `FATAL: ... is outside the worktree` for any Edit/Write to an absolute path outside `git rev-parse --show-toplevel`. Plan 10's `files_modified` are all `../tabler-test/...`. With `parallelization: true`, phase branching, and `use_worktrees` defaulting to true in `execute-plan.md:101`, wave 4 may be dispatched in a harness worktree. Earlier phases ran sequentially only because of fork-base mismatch fallbacks (`STATE.md:76,176`), which is not a guarantee. The cycle-7 adjudication at `06.6-REVIEWS.md:736` says no edit is required, but an executor reads the plan, not the review record, and nothing in plan 10 tells it that the recorded companion root is an authorized out-of-tree write target or that the companion delta must be materialized with `git -C "$COMPANION_ROOT" apply` in Bash rather than Edit/Write. As written, a conforming executor halts or improvises.
- LOW / open question: `gsd_run query commit` honoring `GIT_INDEX_FILE` could not be verified (read of `gsd-tools.cjs` denied). If it ignores the variable, the metadata commit uses the real index; today no core content is staged, so the practical effect is nil, but the plan relies on it.
- LOW / open question: the companion branch is unnamed (see plan 06). The plan should state the commit lands on the currently checked-out branch and that the core protected-branch guard does not apply to `git -C` companion commits.

**Suggestions.**
- Add one paragraph to "Repository and commit boundary": the verified `companion_root` from `06-companion-baseline.json` is the single permitted write target outside the core tree under the 2026-11-02 D-11/D-14 amendment; executor step 0b does not apply to it; materialize the delta with `git -C "$COMPANION_ROOT" apply` of the verified patch rather than Edit/Write. Alternatively require wave 4 to run with `dispatch-isolation --force-isolation none`. Either sentence closes the gap.
- Record the companion branch name and the `core.hooksPath` finding in `10-companion-delivery.json`.

**Risk Assessment.** MEDIUM. The protocol is sound; the single unresolved item is executor-visibility of the worktree exception, and it is closable with text.

---

## Cross-plan assessment

**Dependency ordering.** 01 precedes 02/03/05; 04 precedes 03 for the 84→86→88 count; 06 precedes 07, 07 precedes 10, 10 precedes 09; 08 runs beside 07. Shared files are sequentially owned (`theme_adoption_sources.py`: 06 then 09; `10-companion-delivery.json`: 07-01 writer, 10 owner). No ordering defect found.

**Scope.** No scope creep. The plans implement D-01 through D-19 and the D-11/D-14 amendment without adding product behavior; C7-A01 correctly preserves Phase 6.1 D-08/D-17 and `viewset.js` instead of "fixing" the empty-destination GET.

**Security.** CSRF enforcement, authorization, escaping and helper immutability are tested through real views; nothing in the plans weakens them. Companion delivery never pushes or publishes.

**Performance.** Not materially affected; render-time class and floor resolution are dictionary lookups under a snapshot read.

**Genuinely unresolved executable gaps (cycle 8).**

| ID | Severity | Plan | Required change |
|---|---|---|---|
| C8-A01 | MEDIUM | 10 | One paragraph (or forced sequential dispatch) telling the executor that the recorded companion root is an authorized out-of-tree write target, since step 0b otherwise halts in worktree mode and no C7-A03 text exists at HEAD. |
| C8-A02 | LOW | 06, 07 | Name the expected baseline-to-pass flip of `test_every_upstream_icon_name_is_mapped` so D-13 comparison records it as phase-fixed. |
| C8-A03 | LOW | 06, 10 | Record the companion branch and state that the core protected-branch guard does not govern `git -C` companion commits. |

Open questions, not counted: GSD commit tool and `GIT_INDEX_FILE`; whole-file staging of already-dirty `ROADMAP.md`/`STATE.md` in metadata commits.

**Overall risk: MEDIUM.** Plans 01 through 05 and 08 are fully source-grounded and would be LOW alone. Plans 06, 07, 09 and 10 carry the phase's risk because acceptance depends on fresh baseline, browser, replay and delivery evidence that does not yet exist. The only planning-level defect that would stop a conforming execution is C8-A01, and it is a text fix that changes no decision or authority.
