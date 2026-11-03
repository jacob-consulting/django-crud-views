Source verification is complete. Writing the review now, with each plan's claims checked against the cited files.

# Cross-AI Plan Review — Phase 06.6, cycle 5 (HEAD `cd5e9a5`)

**Reviewer mode:** read-only, source-grounded. Every `file:line` below was opened in this checkout; companion evidence uses the embedded `../tabler-test` excerpts at `885dfc7` with their original line numbers. No file was modified and no test was run.

**Verification scope performed before the per-plan sections:**

- `git merge-base --is-ancestor cb26af4 HEAD` succeeds and `git diff --stat cb26af4 HEAD -- src tests docs examples noxfile.py pyproject.toml` is empty. The pinned pre-phase revision used by plans 01/06 is therefore product-identical to HEAD.
- Cached runtimes: `crispy_floor-3-12-django-4-2` (Django 4.2.30 / crispy 2.0 / bootstrap5 2023.10), `crispy_floor-3-12-django-6-0` (6.0.9 / 2.0 / 2023.10), `tests-3-12-django-4-2` (4.2.30 / 2.5 / 2026.3), `tests-3-12-django-5-2` (5.2.18 / 2.7 / 2026.9). All four carry `pytest_xdist-3.8.0`. No `tests-3-12-django-6-0` exists.
- Prior-cycle invariants re-checked: C4-A01 negative controls (06-01 action, replicated in 07-03 and 09-01), C4-A02 single-hook parity (07-02 action, 09-01 rejection rule), C4-A04 floor wording (03-01 action). All three are present as written and consistent with the source cited under each plan.

---

## 06.6-01

### Summary
The tracer plan is grounded in the real defect. `src/crud_views/lib/crispy/form.py:43-50` and `:136-146` construct a bare `FormHelper()` with crispy's default `form_tag=True` and `disable_csrf=False`; `src/crud_views/templates/crud_views/tags/form.html:3-6` reads `form.helper` twice and falls through to `{% crispy form %}` for helper-less forms. The committed golden `tests/test1/golden/form_frame/create.html` shows exactly the nested `<form method="post" >` and two `csrfmiddlewaretoken` inputs the plan sets out to remove. The crispy pack's token branch is independent of `form_tag` on both the floor and the current pack (`whole_uni_form.html:4-7` in both `.nox` envs), so the plan's insistence on render-local `disable_csrf` rather than `form_tag=False` alone is correct.

### Strengths
- **A10 is a real requirement, not defensive prose.** `src/crud_views/templatetags/crud_views.py:466` renders with `context.flatten()`, while `cv_alert` at `:454` uses `context.push(...)` and `template.template.render(context)`. The form-button owner resolver scans `Context.dicts` for response overlays (`src/crud_views/lib/crispy/buttons.py:34-72`), so switching to the push pattern is the only way the selected helper can coexist with owner tiers.
- **01-02's fixture set is complete.** `_CustomHelperForm` (`tests/test1/test_form_button_checks.py:560-567`) and `_DeleteCustomHelper` (`:578-586`) build `FormHelper()` with no `form_tag` assignment and render through the create/delete views. A sweep of every other `def helper(` in `tests/`, `examples/` and `tests/browser/` found only standalone crispy renders (`tests/test1/test_conditional_layout.py:30-31,69-70`, `tests/test1/test_crispy_buttons.py:855`, `examples/bootstrap5/project/urls.py:15-16`) or helpers that already set `form_tag=False` (`test_fragment_authorization.py:178-195,1584`, `conditional_formsets_server.py:142,261`, `examples/bootstrap5/conditional/views.py:136`). Nothing else will trip D-01.
- **Nested formset rows are already safe.** `src/crud_views/lib/formsets/inline_formset.py:58-59,144-145` set both `form_tag=False` and `disable_csrf=True`, so the `Formsets()` layout path emits no inner tokens today; plan 01's scope correctly stays on the parent helper.
- **Enforced-CSRF precedent exists** at `tests/test1/test_form_validation.py:76-105` (`Client(enforce_csrf_checks=True)` for create/update/delete), which 01-01's `read_first` cites.

### Concerns
- **LOW — raw scanner contract vs. the legacy formset guard.** `tests/test1/test_formsets.py:29-34` counts every `<form\b` from `class="cv-form"` to end of document. Plan 01's `assert_owned_form_markup` permits auxiliary sibling forms; plan 05-02 says it "extends" the legacy guard. If 05-02 adds sibling fixture forms to the formset page (as 05-01 does for other pages) the suffix count will fail. This is a 05 wording issue, but 01 should state that the new scanner replaces, not supplements, suffix counting.

### Suggestions
- State explicitly in 01-01 that `assert_owned_form_markup` is the sole raw-ownership predicate reused downstream, and that any legacy suffix-count guard is migrated to it rather than kept alongside.
- Record in `01-ownership-evidence.md` that `inline_formset.py` helpers already carry `disable_csrf=True`; this closes the "would changing library helpers alter standalone token semantics?" question for nested rows without an experiment.

### Risk Assessment
**LOW–MEDIUM.** The mechanism is grounded; the only open variable is the helper-copy experiment, which the plan correctly gates with a design checkpoint rather than a silent narrowing.

---

## 06.6-02

### Summary
The theme-layer plan targets the right seams. `src/crud_views/lib/view/label_mode.py:86-119` resolves package floor → raw setting with package-only fallbacks at `:107` and `:118`; those two lambdas are exactly where `_theme_or_package_default` must be substituted. All consumers reach the floor through `default_label_mode` or `form_label_mode` (`button_data.py:146,152,310,316`; `base.py:295-311`), so one resolver change propagates everywhere, including W292.

### Strengths
- **"W292 already invokes the public resolver" is true.** Context W292 calls `cls.cv_get_action_label_mode("context", ...)` at `src/crud_views/lib/view/buttons.py:435` and form W292 at `:570`; both terminate in `default_label_mode`. No check wiring change is needed, matching 02-02's "do not modify source checks merely to make wiring appear new".
- **E108 is raw-setting only** (`src/crud_views/lib/settings.py:159-188`), so adding a theme layer cannot change its error semantics; D-15's "consistent with E108" is satisfied by leaving it alone.
- **Isolation pattern is correct.** `tests/test1/conftest.py:23-32` resets only `_warned`; 02-01's autouse snapshot/restore-by-rebind mirrors `tests/test1/test_button_classes.py:94-101` for the class registry.
- **A17 recursion guard is necessary.** `form_label_mode` falls back via `lambda: default_label_mode("form")` (`label_mode.py:134,145`); a theme fallback that read settings again would loop while a malformed setting is installed. The plan names a setting-free helper. Correct.

### Concerns
- **LOW — `LOCATIONS` import is deferred to avoid a cycle** (`label_mode.py:94-95`). `register_label_mode_defaults` must validate keys against the same set; the plan says so but should note the import must stay inside the function body, or the module import order breaks `button_data`.

### Suggestions
- Add one test that `register_label_mode_defaults` called before `django.setup()` (as `AppConfig.ready()` ordering can vary across apps) still validates against `LOCATIONS` without triggering settings access.

### Risk Assessment
**LOW.** Small, well-bounded change with existing analogs for every piece.

---

## 06.6-03

### Summary
The pack-bridge plan is the most technically delicate and its predicates are now source-exact. The floor `crispy_bootstrap5/templates/bootstrap5/layout/formactions.html` (2023.10, 9 lines) renders `class="mb-3"` with no `css_class` read and no hidden-input branch; the current pack reads `{{ formactions.css_class|default:'' }}`. Floor `FormActions.__init__` accepts `template=` (`crispy_forms/bootstrap.py:297-299`), so a private subclass choosing its template per render is feasible without touching installed templates.

### Strengths
- **Key-count arithmetic is right.** `tests/test1/test_button_classes.py:105` asserts 84; `docs/reference/buttons.md:151` says 84; `test_documented_default_key_count_matches_table` (`:112-116`) parses that sentence. 84 → 86 (plan 04) → 88 (plan 03) with 03 depending on 04 is consistent.
- **W362 behaves as claimed.** Keys in `DEFAULT_BUTTON_CLASSES` are accepted (`button_classes.py:329`); `_action_key_parts` requires `parts[1] in FORM_KINDS` for `form:` keys (`:255-265`), so `form:actions:icon` falls to the "not a known key" warning. No grammar change needed.
- **All three construction sites identified.** Ordinary (`form.py:55-56`), delete (`form.py:141-144`, which bypasses `get_form_actions`), filter (`list.py:125-133` with the private `_cv_actions`/`_cv_actions_layout` lifecycle at `:95-99`). H05's deepcopy/re-resolve requirement follows directly from that lifecycle.
- **C4-A04 wording matches the floor source**: the plan's "no hidden-input branch" statement is literally true of the 9-line template.

### Concerns
- **LOW — coverage gap between the exact floor source and the current pack.** The bridge is eligible only when the resolved template equals the audited 2023.10 bytes. Any supported intermediate crispy-bootstrap5 release whose template still ignores `css_class` but differs textually would silently drop classes. Only 2023.10, 2026.3 and 2026.9 are cached, so this cannot be exercised here.

### Suggestions
- In `03-pack-bridge-evidence.md`, record the first pack release that consumes `formactions.css_class` (from the pack changelog) and state the support claim as "2023.10 via bridge; that release and later natively; intermediate releases untested". This is a documentation obligation under D-18's "record limits", not a code change.

### Risk Assessment
**MEDIUM.** The approach is sound and the predicates are exact; the residual risk is that research assumption A1 still has to be proven by the 03-01 experiment.

---

## 06.6-04

### Summary
Smallest plan, fully grounded. `src/crud_views/templates/crud_views/tags/alert.html:2` holds the literal `alert-dismissible fade show`, `:5` the literal `btn-close` beside `data-cv-alert-dismiss`. `alert_data()` already supplies `dismissible` and escaped `extra_tags` (`src/crud_views/lib/messages.py:20-50`). The byte-exact golden guard exists (`tests/test1/test_alerts.py:166-181`, `read_bytes()` comparison).

### Strengths
- **A03 separator rule is testable against the current template**: the `{% if alert.dismissible %} …{% endif %}` leading space at `:2` is what must become conditional on a nonempty resolved value.
- **Dismissal contract preserved by construction.** `src/crud_views/static/crud_views/js/viewset.js:46-55` dispatches on `[data-cv-alert-dismiss]` within `[role="alert"]`; `adapters.js:94-101` closes via the namespace's `Alert` or `el.remove()`. Neither reads a class, so class replacement cannot break closing.
- **H08 handled correctly.** `tests/test1/test_alerts.py:250-253` asserts exactly one django/html fence under `### Custom alert frame` (`docs/reference/theme.md:308`). 04-02 edits docs only outside that fence.
- **Verify command targets an existing file**: `tests/js/adapters.test.js` exists and already covers `cv.adapters.alert.close` (`:9-15,45-49`).

### Concerns
- **None actionable.** The 84 → 86 edit lands with the defaults in one task, which is what H04 required.

### Suggestions
- Add `alert:close:icon` and `alert:dismissible:both` to the W362 negative test by literal string, as the plan says, and also `alert:dismissible:label` to cover the third mode token.

### Risk Assessment
**LOW.**

---

## 06.6-05

### Summary
The expansion plan's template and view claims are all verified. `view_workflow.action.html:15` is the only direct `{% crispy form form.helper %}` call left in product templates; `:2` loads `crispy_forms_tags` and `:3` already loads `crud_views`, so A12's removal is safe. `WorkflowView` sets only `template_name` (`src/crud_views_workflow/lib/views.py:27`) and inherits `cv_content_template = "crud_views/view_custom_form.content.html"` from `CustomFormView` (`src/crud_views/lib/views/form.py:19`), confirming C3-A01. Full-page workflow includes `view_workflow.content.html`, which includes history and action (`view_workflow.html:4`, `view_workflow.content.html:3-5`).

### Strengths
- **C2-A01 is correct against source.** `cv_modal_supported` defaults to `False` (`src/crud_views/lib/view/base.py:111`); E251 is `not cls.cv_modal or cls.cv_modal_supported` (`:169-170`); `True` is set only in `delete.py:55`, `form.py:20,52` (the two custom-form views) and the object-detail mixin. Create/Update inherit `False`.
- **Protected-delete omission is real.** `view_delete.content.html` wraps the form in `{% if not has_protected_objects %}`; the blocked branch renders no form, so the plan's explicit exception is required.
- **05-02's two overrides are exactly what it says.** `tests/test1/app/views_formset.py:45-50` and `examples/bootstrap5/formsets/views.py:37-41` do nothing but `h.form_tag = False` on `super().helper`. Removing them after plan 01 is safe; the C2-A05 deferral list (EventForm, PublisherMainForm/BookMainForm, BrowserPublisherForm) matches the sweep above.

### Concerns
- **LOW — legacy suffix-count guard** (`tests/test1/test_formsets.py:29-34`) will reject any auxiliary form appended after `cv-form` on the formset page. 05-02 should replace it with plan 01's owner-scoped scanner rather than "extend" it, or avoid adding sibling forms on that fixture.

### Suggestions
- Change 05-02's wording from "extend the existing parent formset create raw guard" to "replace the suffix-count with `assert_owned_form_markup` and add token counting", so the two predicates do not diverge.

### Risk Assessment
**LOW–MEDIUM.** Mostly test expansion over verified templates; the workflow change is a one-line template substitution.

---

## 06.6-06

### Summary
The baseline/utility plan is now bound to a real monorepo and its shadow inventory matches the embedded source: `src/crud_views_tabler/templates/crud_views/` holds exactly the eight files the plan names (`modal/shell.html`, `snippets/form_frame.html`, `table/bootstrap5.html`, `tags/alert.html`, `tags/card.html`, `tags/list_filter.html`, `tags/list_filter.inner.html`, `view_card.content.html`), and `checks.py:8-27` / `icons.py:50-52` are the bespoke-behavior files it insists stay counted. The pinned core archive at `cb26af4` is product-identical to HEAD (verified above), so wave-1 contamination is a non-issue today but the isolation rule remains correct for later waves.

### Strengths
- **C4-A01 negative controls are concrete** (omit `modal/shell.html`, omit `checks.py` classification, hide a new behavior file, row/total tampering) and are re-required in 07-03 and 09-01.
- **Delivered-source mode is specified before plan 10 needs it**, including the subtle rule that an advanced companion HEAD is not corruption while the pinned archive stays the baseline identity.
- **Import-pure utility + explicit `importlib` loading** is consistent with the test layout: `tests/__init__.py` exists, `tests/browser/__init__.py` does not, `tests/conftest.py` is empty, so a `tests/browser/test_*.py` module is collected standalone. Django configuration comes only from `tests/test1/conftest.py:36-124`.

### Concerns
- **MEDIUM — predictable halt on the companion runtime.** 06-01/06-02 require `-m pytest tests -n 4 -q` in the isolated companion copy and "halt with exact missing inputs" if xdist is absent. RESEARCH round-3 addendum records xdist as absent in `/home/alex/projects/alex/tabler-test/.venv`, and the companion's declared test group (`pyproject.toml:32`) lists only `pytest`, `pytest-django`, `crispy-bootstrap5==2026.9`. Unless the user installs `pytest-xdist` there before execution, 06-02 halts on its first run. The AGENTS.md multicore rule governs this repo's broad runs, not a companion's ~84-test suite.
- **LOW — verify command collects the whole core suite.** `pytest tests -k theme_adoption_sources -n 4` imports every `tests/test1` module and configures Django just to run a few Django-free utility tests, while the task's `done` text says they run serially. Plan 09-01 already uses the direct file path.

### Suggestions
- Either ask the user to add `pytest-xdist` to the companion venv up front (recording the install under the legitimacy gate), or run the companion pytest serially and state that exception explicitly in 06-01; `manage.py test --parallel 4` needs no xdist and can stay.
- Use `pytest tests/browser/test_theme_adoption_sources.py -q` for the 06-01 verify, matching 09-01.

### Risk Assessment
**MEDIUM.** The utility design is solid; the risk is operational (companion dependency preflight) and is best removed before execution rather than discovered by a halt.

---

## 06.6-07

### Summary
The browser/replay plan's companion claims hold against the embedded source. The alert shadow hardcodes `alert-dismissible fade show` (`tags/alert.html:7`) and `btn-close … data-bs-dismiss="alert"` (`:17`); `page.html:10` renders `{% cv_messages %}` through core's `tags/messages.html` (the companion's own test at `tests.py:258-263` asserts messages.html is not overridden) and `page.html:16` loads `{% cv_js %}`, so the core `data-cv-alert-dismiss` listener will be active on CRUD pages. `MessagesParityTests` (`tests.py:556-572`) currently passes only because both includes emit identical markup; the C4-A02 single-attribute mapping is the minimal honest change. Port handling mirrors `presentation.cjs:2-5` and `presentation_server.py:7-9` exactly.

### Strengths
- **Form-frame retention rule is correct**: the shadow (`form_frame.html:1-6`) adds only card wrappers and the companion's own test (`tests.py:251-256`) pins that it frames upstream content templates, so no form/token ownership is introduced there.
- **Native pack already consumes `css_class`** (RESEARCH round-2 addendum), and the plan forbids manufacturing a pack diff when the probe passes. This keeps D-18's count honest.
- **Alert adapter namespace is handled as evidence, not assumption.** `tabler-adapters.js` wires `cv.bootstrapAdapters(() => globalThis.tabler)` (`tests.py:222`); the plan requires recording the actual hook and asset identities rather than assuming `globalThis.bootstrap`.
- **Workflow branch records** are separable because the full-page and modal bodies genuinely differ (see 06.6-05 evidence).

### Concerns
- **MEDIUM — a predictable in-scope baseline failure is not pre-classified.** Companion `tests.py:320-324` (`test_delete_form_is_the_stock_crispy_delete_form`) asserts `<input type="submit"[^>]*class="btn btn-danger"`. Core's form leaf renders `<button>` only (`src/crud_views/templates/crud_views/tags/button/form.html`: one `<button`, zero `<input`), a Phase 6 breaking change. Against current core this test fails at `885dfc7` before any Phase 06.6 edit. D-13 allows unrelated pre-existing failures, but this one is on the delete form, a page 07-02's `csrf-post`/`modal-replace` families exercise. Leaving it unclassified invites ambiguity in 07-03's "compare raw failing identities". `tests.py` is already a candidate patch path.
- **LOW — `label-floor` case needs a stated registration value.** The patch map says `apps.py` gains "registration" but no plan states which key the companion registers (for example `{"form": "both"}`), which decides what the browser case asserts and whether companion form-button markup changes.

### Suggestions
- Decide in 07-03 whether the `<input>` → `<button>` delete assertion is updated as a documented Phase-6 sync inside the tested patch, or retained as a named baseline failure with its node ID. Either is defensible; silence is not.
- Name the registered label-mode value and the two Tabler class values (`alert:dismissible`, `alert:close`) the candidate patch will add to `buttons.py`, so 09's inventory can bind exact bytes.

### Risk Assessment
**MEDIUM.** Execution-heavy by design; the concerns are classification gaps, not mechanism errors.

---

## 06.6-08

### Summary
Documentation targets are precise and the guard tests exist as described. `tests/test1/test_label_mode_docs.py:786-800` reads a paragraph-scoped E108 sentence from `docs/migrating-1.0.md:58-61` and asserts the literal "falls back to its package floor", so H07's "update both in 08-02" is mandatory, not optional. `docs/reference/theme.md` already has `## Buttons` (`:95`), `## Alerts` (`:292`) and `### Custom alert frame` (`:308`) sections for the new prose. `tests/test1/test_presentation_migration_docs.py` and `tests/test1/test_form_button_docs.py` exist as the extraction analogs.

### Strengths
- **C2-A02 standalone-wrapper note is grounded**: `whole_uni_form.html:4` wraps only `{% if form_tag %}`, so a library `CrispyModelForm` rendered standalone after plan 01 loses its `<form>` but keeps its token (`:5-7`). The caller-owned recipe is the right migration.
- **Single-fence constraint respected**: new alert-key guidance goes outside the fence that `test_alerts.py:250-253` pins.
- **Strict docs build is a verify step**, catching anchor drift from the new section names.

### Concerns
- **LOW — "no downstream project names in product docs" (PROJECT.md:97) vs. the need to explain theme adoption.** The plan says "reference general theme adoption without introducing downstream project names"; make sure the executable recipe uses a neutral app name, as `theme.md:76,92,105` already does.

### Suggestions
- Have `test_breaking_migration_pair` parse the CHANGELOG `### Breaking` block (`CHANGELOG.md:7`) and assert each new bullet contains a `migrating-1.0.md#…` anchor that exists, mirroring the existing E108 inventory test's paragraph scoping.

### Risk Assessment
**LOW.**

---

## 06.6-09

### Summary
The final-gate plan's runtime claims are accurate: four cached interpreters, no current-pack Django 6.0 environment (H12 disposition correct), `CRISPY_FLOOR_TESTS` (`noxfile.py:28-51`) lacks `test_alerts.py` and `test_button_classes.py` (A15 correct), and the sole deselect is `test_filter_form_baseline` (`noxfile.py:57`). The example gate is runnable: `examples/bootstrap5/pytest.ini` sets `project.settings`, `project/settings.py` exists, and ten app `tests.py` files plus `project/test_*.py` are present.

### Strengths
- **Dependency order is right**: wave 5, `depends_on` includes 06.6-10, and `--check-final` consumes `10-companion-delivery.json`.
- **Evidence reuse is fingerprint-bound**, including the rule that local-commit metadata changes with identical content are recorded rather than rejected.
- **Halted-summary contract** keeps a missing human observation from being laundered into acceptance.

### Concerns
- **LOW — the example gate's `-c examples/bootstrap5/pytest.ini` with `pythonpath = .`** resolves relative to the ini's rootdir; with `examples/bootstrap5` as the only argument that is the example root, so it works, but the command should say so because `PYTHONPATH=src:examples/bootstrap5` is also set and the two must agree.
- **LOW — two full floor runs of the entire `tests` tree** are heavier than the nox session (which runs only `CRISPY_FLOOR_TESTS`). Phase 06.5 already did this (STATE.md:49), so it is feasible, but durations should be recorded as the plan says.

### Suggestions
- In `--check-final`, also assert that the five `tests/test1/test_theme_*.py` modules appear in the JUnit of both floor runs with nonzero counts, not only that they are listed in the nox AST. The plan implies this; make it a named negative test.

### Risk Assessment
**MEDIUM**, driven by the volume of gates and the human-check dependency rather than any design flaw.

---

## 06.6-10

### Summary
The new delivery plan correctly consumes 06's `--delivered-source`/`--require-committed` modes and keeps private `settings.py` bytes out of commits and reports. The five companion paths match plan 07's candidate patch map, with `formactions.html` correctly marked conditional.

### Strengths
- **No-reuse-across-bytes rule**: a pre-delivery green report cannot certify different delivered bytes; post-hook re-hashing is required.
- **Separate identities**: pinned baseline HEAD vs. deliberately advanced companion HEAD, both retained.
- **AGENTS.md/CLAUDE.md discovery in the companion** before editing is the right habit for a second repository.

### Concerns
- **MEDIUM — cross-repository commit mechanics are unspecified.** `files_modified` lists `../tabler-test/...` paths and 10-02 says "ordinary local execution commits … in that repository". The execute-plan workflow commits through the executor's protocol (`execute-plan.md:334-340`, `gsd_run query commit --files …`), which operates on this checkout; `.planning/config.json` defines no `sub_repos`, so no sub-repo commit path is configured. Out-of-tree paths will fail the per-task commit and the `evaluation-scope --commits-only` self-check (`execute-plan.md:195`). I could not read the executor agent file (permission), so treat the exact failure mode as unverified, but the gap is real: the plan needs explicit `git -C /home/alex/projects/alex/tabler-test add -- <paths> && git -C … commit` steps, and must state that the core-side task commit contains only `10-companion-delivery.json` and `07-TABLER-HANDOFF.md`.
- **LOW — pre-commit hooks in the companion** are mentioned ("after commit hooks") but the plan should state up front whether any exist, since hook rewrites invalidate the fingerprint.

### Suggestions
- Add to 10-02: the exact companion git commands, the staged-path allowlist (five files), a `git -C … status --porcelain` capture before and after proving `example/config/settings.py` stays modified-unstaged, and the core-side commit scope.
- Consider setting `sub_repos` in config (if GSD supports it for this layout) so the standard protocol applies; otherwise document the manual path as the deliberate exception.

### Risk Assessment
**MEDIUM.** Correct intent and validation; the commit mechanics need one concrete paragraph before an executor can run it without improvising.

---

## Cross-plan comparison

| Topic | Finding | Evidence |
|---|---|---|
| File ownership across waves | No two plans in the same wave touch the same file; cross-wave overlaps (`form.py` 01→03, `test_form_button_checks.py` 01→02, `test_button_classes.py`/`buttons.md` 04→03, `theme_adoption_sources.py` 06→09, `07-TABLER-HANDOFF.md` 07→10) are all ordered by `depends_on`. | Plan frontmatter vs. wave numbers |
| Key-count chain | 84 (live) → 86 (04) → 88 (03) | `test_button_classes.py:105`, `buttons.md:151` |
| Floor coverage | 03-03 and 09-01 both require the cached 4.2 and 6.0 floors; both exist with identical crispy pins | `.nox` listing |
| Companion scope | Eight shadows + two behavior files inventoried; alert copy migrated, form-frame/list-filter retained, no form/workflow copies exist | embedded `tags/alert.html`, `form_frame.html`, `tests.py:251-263` |
| Memory vs. source | A prior-session note claimed library helpers already set `form_tag=False`/`disable_csrf=True`; that is true only of `inline_formset.py`, not `crispy/form.py`. The plans follow the source. | `form.py:43-50,136-146` vs. `inline_formset.py:58-59` |

## New actionable findings (cycle 5)

| ID | Severity | Plans | Finding |
|---|---|---|---|
| C5-A01 | MEDIUM | 10, 09 | Cross-repo commit mechanics unspecified; no `sub_repos` in config, `files_modified` uses `../` paths. |
| C5-A02 | MEDIUM | 07, 10, 06 | Companion `tests.py:323` `<input type="submit">` assertion is a predictable baseline failure on a Phase-06.6 page; needs explicit disposition. |
| C5-A03 | MEDIUM | 06 | Companion venv lacks xdist per research; `-n 4` will halt 06-02 unless resolved up front. |
| C5-A04 | LOW | 05, 01 | Legacy suffix-count formset guard conflicts with sibling-form allowance; replace rather than extend. |
| C5-A05 | LOW | 03 | Document the untested intermediate pack-version band between 2023.10 and the first `css_class`-consuming release. |
| C5-A06 | LOW | 06 | 06-01 verify collects the whole suite; use the direct file path. |
| C5-A07 | LOW | 07 | Name the registered label-mode value and Tabler class values the candidate patch adds. |

Explicitly incorporated and **not** counted as gaps: C4-A01 exhaustive inventory and negative controls, C4-A02 strict single-hook parity, C4-A04 floor wording, the D-11/D-14 amendment, and all future execution evidence (baseline, replay, browser, human checks).

## Overall risk assessment

**MEDIUM.** No HIGH findings remain. Every product-side mechanism the ten plans rely on was traced to current source and holds. The remaining risk is concentrated in companion execution: one operational blocker that can be removed before execution (xdist), one classification decision (the delete-form `<input>` assertion), and one procedural gap (how plan 10 commits in the sibling repository). The plans achieve the phase goals as written once those three paragraphs are added.
