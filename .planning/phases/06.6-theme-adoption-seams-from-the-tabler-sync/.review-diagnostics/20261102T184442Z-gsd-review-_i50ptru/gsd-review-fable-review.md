# Cross-AI Plan Review — Phase 06.6, Cycle 4 (resolution verification at HEAD `0d7c377`)

**Reviewer evidence basis.** Core repository read directly at `0d7c3771abe512085e3e4680c5a54f01f77e322c`. `git diff --stat cb26af4 HEAD -- src tests docs examples noxfile.py pyproject.toml` is empty and those paths have no uncommitted changes, so the pinned planning revision `cb26af4` and HEAD carry identical product/test/docs source. Companion facts come only from the embedded excerpts of `../tabler-test` at `885dfc7`; no sibling-directory access was attempted. One companion file the review depends on (`src/django_tabler/templates/django_tabler/includes/messages.html`) is not in the excerpt; the single finding that rests on it is marked conditional. No product test was run and nothing was modified.

**Headline.** C3-A01, C3-A02 and C3-A03 are closed against source. No previously closed HIGH is revived. Two new MEDIUM findings and three LOW notes are raised; both MEDIUMs concern companion-evidence completeness in plans 06/07, not core product design.

---

## 06.6-01

### 1. Summary
The plan targets the right seams and its source claims hold. `CrispyFormMixin.helper` allocates a bare `FormHelper()` per access (`src/crud_views/lib/crispy/form.py:43-50`) and `CrispyDeleteForm.helper` does the same (`:136-146`); neither sets `form_tag=False`. The inner template reads `form.helper` twice by truthiness (`src/crud_views/templates/crud_views/tags/form.html:3-6`). `cv_render_form` flattens the context (`src/crud_views/templatetags/crud_views.py:465-466`) while `cv_alert` uses `get_template(...)` plus `context.push` and `template.template.render(context)` (`:453-455`), so the A10 pattern the plan copies exists. The committed create golden literally contains the defect: an outer `<form class="cv-form" ...>` with a token, then a nested `<form method="post" >` with a second token (`tests/test1/golden/form_frame/create.html:1`).

### 2. Strengths
- The H02 fixture hazard is real and correctly scoped: `_CustomHelperForm` (`tests/test1/test_form_button_checks.py:560-567`) and `_DeleteCustomHelper` (`:578-585`) build `FormHelper()` without `form_tag=False`; under D-01 they would raise, so migrating them in the same commit (01-02) is necessary, and `test_form_button_checks.py` is in both plan 01 and plan 02 `files_modified` with `02 depends_on 01`.
- Enforced-CSRF precedent exists (`tests/test1/test_form_validation.py:78,91,105`), and the raw nested-form guard the plan cites as the parent analog exists (`tests/test1/test_formsets.py:16-34`, counting `<form\b` from the class attribute onward).
- The frame normalizer the plan promises not to change is at `tests/test1/test_form_frame.py:44-47`; the tier constants it tells the executor to read first exist (`src/crud_views/lib/crispy/buttons.py:34-36`).
- The partial-sequencing honesty is correct: `WorkflowForm` is a `CrispyForm` (`src/crud_views_workflow/lib/forms.py:11`), so after 01 it loses the nested form but keeps its inner token until 05 reroutes `view_workflow.action.html:15`.

### 3. Concerns
- **LOW** — The `delete_protection.html` golden is a fifth frame golden not listed in 01-02's four; it contains no form so it is unaffected, and 01-02 says protected-delete goldens stay unchanged. No action needed beyond noting it exists (`tests/test1/golden/form_frame/delete_protection.html`).

### 4. Suggestions
- When recording the before/after standalone render in `01-ownership-evidence.md`, include the no-helper `{% crispy form %}` branch (`tags/form.html:5-6`) explicitly, since `PolymorphicCreateSelectView` reaches `view_create.content.html` with a plain `FormView` (`src/crud_views_polymorphic/lib/create_select.py:24-26`) and plan 05-02 depends on that branch.

### 5. Risk Assessment
**LOW–MEDIUM.** Mechanism is source-grounded; the residual risk is the helper-copy strategy experiment, which the plan correctly gates with an explicit stop condition rather than assuming A2.

---

## 06.6-02

### 1. Summary
The resolver the plan extends is exactly as described: immutable package floor (`src/crud_views/lib/view/label_mode.py:23-25`), `_UNSET` sentinel (`:28`), strict-raise/warn-once helper (`:63-83`), and four package-only fallback sites in `default_label_mode` (`:101`, `:107`, `:110`, `:118`). `form_label_mode` routes malformed owner maps and entries to `default_label_mode("form")` (`:129-146`), which is the composed path C3-A03 asked for. E108 lives at `src/crud_views/lib/settings.py:159-189` and uses `LOCATIONS`/`is_label_mode`. Both W292 branches already call the public resolver (`src/crud_views/lib/view/buttons.py:435-437` context; `:568-573` form) with static, non-instantiating reach (`:546-556` docstring).

### 2. Strengths
- The C3-A03 disposition traces correctly through source: non-strict `form_label_mode(non-dict)` → `_invalid_label_mode(A, fallback)` → `fallback()` → `default_label_mode` with a malformed setting → `_invalid_label_mode(B, theme-or-package)` → returns the theme value and logs B, then logs A with the same resolved value. Dedup is keyed `(location, repr(value))` (`:76-80`), so the plan's instruction to use distinct malformed values is exactly what keeps both warnings visible. Strict mode raises at A before `fallback()` runs (`:73-74`), matching "settings fallback is not called".
- The A17 recursion guard (`_theme_or_package_default` reads no settings) is necessary: the existing fallback lambdas are what `_invalid_label_mode` re-enters.
- Isolation gap is real: the autouse fixture resets only `_warned` (`tests/test1/conftest.py:23-32`); `LOCATIONS` is the finite vocabulary at `src/crud_views/lib/view/button_data.py:19`. `test_action_label_mode_render.py` and `test_label_mode.py` (with `no_setting`/parametrized `override_settings` tests at `:51-130`) exist for the executor to extend.

### 3. Concerns
- None actionable. The one wording note: 02-02 says "Route every existing package-only invalid-setting fallback"; the two non-error package returns at `:101` and `:110` must also become theme-aware, which 02-01's "package then theme then live setting" sentence covers. Make sure the executor does not treat 02-02's sentence as the complete list.

### 4. Suggestions
- Add the explicit `None` setting case to the composed test as well (`_UNSET` vs `None` is distinguished at `:28`, and `None` is "not a dict" at `:102`), so the fallback-to-theme destination is proven for both malformed shapes.

### 5. Risk Assessment
**LOW.** Small, well-bounded change on an already lazy resolver; the only subtlety (re-entrant fallback) is named and tested.

---

## 06.6-03

### 1. Summary
The floor incompatibility is confirmed: the cached 2023.10 pack template never reads `css_class` (`.nox/crispy_floor-3-12-django-6-0/.../bootstrap5/layout/formactions.html:1-9` renders `class="mb-3"` and only `flat_attrs`), while the current pack does (`.../tests-3-12-django-5-2/.../formactions.html:3`). Floor `FormActions.__init__` accepts `css_class`, `template` and `**kwargs` (`crispy_forms/bootstrap.py:298` in the floor env), so a private subclass with a library-local template is feasible. Both floor runtimes exist (`.nox/crispy_floor-3-12-django-4-2` with Django 4.2.30, crispy 2.0, pack 2023.10). The filter helper's exactly-once action cache (`src/crud_views/lib/views/list.py:172-179`) is the H05 hazard the plan addresses by resolving classes at render.

### 2. Strengths
- Grammar guard holds: `form:actions` and `form:filter-actions` are two-part keys; `_action_key_parts` requires `parts[1] in FORM_KINDS` for `form:*` (`src/crud_views/lib/button_classes.py:262-263`), so `form:actions:icon` stays an "unknown key" W362 (`:339-346`) without touching `FORM_KINDS` (`:240`).
- Count arithmetic anchored: `len(EXPECTED_KEYS) == 84` (`tests/test1/test_button_classes.py:105`) and the parsed documented count (`:112-116`, `docs/reference/buttons.md:151`). 86→88 after plan 04's 84→86 is correct, and `03 depends_on 04`.
- The sole floor exclusion is the one in `noxfile.py:57`; the plan forbids any new exclusion.

### 3. Concerns
- **LOW** — 03-01 says to compare the floor template "including hidden-input and label/field-class branches". The floor `formactions.html` has `label_class`/`field_class` branches but no hidden-input branch (that lives in `whole_uni_form.html`). Harmless, since the plan requires whole-source equality, but the wording could send the executor looking for a branch that does not exist.

### 4. Suggestions
- State the discriminator's exact fixture: the 9-line floor template above, hashed, with the origin resolved via `get_template("bootstrap5/layout/formactions.html").origin.name` under the installed distribution's real path.

### 5. Risk Assessment
**MEDIUM.** The bridge is the one piece of this phase with no existing analog; the plan handles it responsibly (fixed predicates, no generic fallback, explicit stop for a policy decision), but it remains the most likely place for execution to need a design checkpoint.

---

## 06.6-04

### 1. Summary
The alert leaf is exactly two literals away from the target: `{% if alert.dismissible %} alert-dismissible fade show{% endif %}` and `class="btn-close" data-cv-alert-dismiss` (`src/crud_views/templates/crud_views/tags/alert.html:2-5`). `cv_button_class` is a `simple_tag` (`src/crud_views/templatetags/crud_views.py:570-571`), so the A03 "resolve into a variable" approach (`as` syntax) is available. The raw golden exists (`tests/test1/golden/alerts/dismissible.html`). `alert_data` supplies `level/icon_name/heading/text/body_template/dismissible/extra_tags` (`src/crud_views/lib/messages.py:20-52`), which both the core leaf and the companion copy consume.

### 2. Strengths
- Default-byte identity is achievable as described: emitting the separator only for a nonempty resolved value reproduces the current `" alert-dismissible fade show"` bytes.
- W362 behavior for `alert:close:icon` / `alert:dismissible:both` is the "unknown key" branch (`button_classes.py:339-346`), as the plan asserts.
- The H08 fence guard is real: `test_alerts.py:250-253` requires exactly one `django/html` fence under `### Custom alert frame` (`docs/reference/theme.md:308`).

### 3. Concerns
- None actionable for this plan. `docs/reference/theme.md:310` ("are literal Bootstrap CSS") becomes false after 04-01; plan 08-01 owns that text (already incorporated per Round 3).

### 4. Suggestions
- In 04-01's hostile-value test, include a value containing `"` to prove the simple_tag output is autoescaped inside the `class` attribute (the companion's own test suite does this for icons at `tests.py:56-57`; the core leaf should have the same guard).

### 5. Risk Assessment
**LOW.**

---

## 06.6-05

### 1. Summary
C3-A01's premise is confirmed and the plan now describes the actual contract. `WorkflowView` overrides `template_name` but not `cv_content_template` (`src/crud_views_workflow/lib/views.py:18-27`), inheriting `crud_views/view_custom_form.content.html` and `cv_modal_supported = True` from `CustomFormView` (`src/crud_views/lib/views/form.py:19-20`). A modal request (`X-CV-Modal`, `src/crud_views/lib/view/base.py:58-59`) selects `crud_views/modal/content.html` (`:222-225`), which includes `view.cv_content_template` (`modal/content.html:8`). So a workflow modal renders the generic custom-form body; the workflow branches live only in the full page (`view_workflow.html` → `view_workflow.content.html:3-5` → `view_workflow.action.html:6-19`). Protected-delete omission is `{% if not has_protected_objects %}` (`view_delete.content.html:15-23`). The two parent helper overrides to remove exist with comments stating form-tag suppression as their sole purpose (`tests/test1/app/views_formset.py:45-50`, `examples/bootstrap5/formsets/views.py:36-41`).

### 2. Strengths
- The no-choice modal case is correctly kept as "form rendered, transition refused": `cv_form_valid` raises `SuspiciousOperation` for an unavailable transition (`views.py:98-99`).
- E251 and the default gate are where the plan says (`base.py:111`, `:167-172`); create/update modal remains unsupported.
- Auxiliary forms the raw scanner must tolerate exist in stock templates: `language_selector.html:13` (POST), `tags/list_action_form.html:2` (hidden POST), `snippets/card_order.html:4` (GET).
- Removing the two overrides restores static W292 reach, because `_static_form_controls` requires the package helper implementation (`buttons.py:546-556`).
- A12 is correct: `view_workflow.action.html:2` loads `crispy_forms_tags` only for the call at `:15`.

### 3. Concerns
- **LOW (incorporated)** — No workflow view in the test app sets `cv_modal = True` (`tests/test1/app/views.py:880-951` enables modals only on author delete/detail/custom form and the protected publisher). 05-01's "create local test-only routes where needed" clause covers this; name the fixture (a Campaign ViewSet variant with `cv_modal=True` on the workflow view) so the modal matrix is not quietly reduced to custom/delete.

### 4. Suggestions
- Record in `05-SUMMARY` the three template-bound records 09-01 will later validate (modal body origin = `view_custom_form.content.html`; full-page with choices includes `view_workflow.action.html` form; full-page no-choice renders `:17-19`), using the same field names 07/09 expect, so the validator contract is fixed by the first producer.

### 5. Risk Assessment
**LOW–MEDIUM.** Broad request matrix, but every branch is now bound to a real template path; the only execution risk is fixture volume.

---

## 06.6-06

### 1. Summary
The companion identity work is sound and the counting rule added for C3-A02 is well specified (stable purpose IDs, data-only registration excluded, renamed paths retain IDs, positive/negative comparisons). The embedded companion source confirms the four named shadows exist and that the companion registers icons, button classes and assets as data (`crud_views_tabler/apps.py:24-31`). The pinned core base `cb26af4` is a real commit and is product-identical to HEAD, so the baseline archive is the true pre-change source. The companion test group lacks pytest-xdist (`pyproject.toml:32`), which the plan already preflights and halts on.

### 2. Strengths
- Import-pure utility with `importlib` loading is the right call: `tests/browser` has no `__init__.py` while `tests/` and `tests/test1/` do, so a package-relative import would not work and rootdir collection of `tests/browser/test_theme_adoption_sources.py` will still happen under `pytest tests`.
- The baseline is required to record failures rather than relabel them, and the embedded companion already predicts at least two pre-existing failures against current core: `test_every_upstream_icon_name_is_mapped` asserts `set(TABLER_ICONS) == set(DEFAULT_ICONS)` (`tests.py:62-67`) while `TABLER_ICONS` (`icons.py:12-47`) lacks the Phase 6 `save`/`cancel`/`filter-reset` icons; and `test_delete_form_is_the_stock_crispy_delete_form` expects `<input type="submit"` (`tests.py:320-324`) after Phase 6 moved form buttons to `<button>`. These are exactly the "unrelated failures predate the changes" D-13 requires.

### 3. Concerns
- **MEDIUM (C4-A01, omission)** — 06-01 says "Inventory actual shadowing copies under `src/crud_views_tabler/templates/crud_views/`:" and lists four files; 07-02 then speaks of "all four shadowing copies". The embedded pinned source shows at least eight shadows in that namespace: `modal/shell.html`, `table/bootstrap5.html`, `tags/card.html` and `view_card.content.html` in addition to `tags/alert.html`, `snippets/form_frame.html`, `tags/list_filter.html`, `tags/list_filter.inner.html` (all core paths exist, e.g. `src/crud_views/templates/crud_views/table/bootstrap5.html`). The companion's own `test_upstream_templates_are_not_overridden` (`tests.py:406-420`) enumerates what is *not* overridden, implying the rest is overridden by design. If the utility hardcodes the four, the D-18 "required overrides" count in `06-companion-baseline.json`, `07-tabler-replay.json` and `ACCEPTANCE` undercounts, the retained Tabler card/table/shell/card-list purposes get no IDs, and growth outside the four cannot be rejected. The four are the phase-affected subset needing render evidence, not the inventory. Also count the bespoke Python behavior: `checks.py:3` imports private `_get_renderers`/`_icon_str` (a custom check, not data-only registration; it is Phase 7 STAB-04's concern but belongs in this phase's purpose inventory).
- **LOW (incorporated, decision point)** — xdist absence in the companion venv means 06-02's `-m pytest tests -n 4` will halt under the installation gate before any baseline exists. That is the plan's chosen policy; flag it to the user as the first predictable stop so they can authorize an audited install (or a serial run) before execution rather than mid-run.

### 4. Suggestions
- Reword 06-01: "Enumerate every template under `src/crud_views_tabler/templates/crud_views/` and every Python override/callback in `src/crud_views_tabler/` (templates, `checks.py`, `icons.render`), assign purpose IDs to all; the four phase-affected shadows additionally require loader-origin and render evidence." Add a negative test where a fifth pre-existing shadow is dropped from the inventory and the comparison must fail.
- Pre-register the two predicted baseline failures above as a positive control for `--capture-baseline` (the capture must list them as failing node IDs, not passing).

### 5. Risk Assessment
**MEDIUM.** Infrastructure is well designed; the enumeration gap directly affects the D-18 number the phase will report.

---

## 06.6-07

### 1. Summary
Plan 07 is bound to real companion structure: the alert copy hardcodes `alert-dismissible fade show` and `btn-close` with `data-bs-dismiss="alert"` (`crud_views_tabler/templates/crud_views/tags/alert.html:7,17`); the frame copy adds only card wrappers keyed on `request.headers.x_cv_modal` (`snippets/form_frame.html:3-5`), matching core's header detection; the list-filter copies own a GET form and call `{% crispy filter.form filter.form.helper %}` (`list_filter.inner.html:10-12`) with a helper that already has `form_tag=False` (`src/crud_views/lib/views/list.py:93-94`). Ports are as stated (`presentation.cjs:2-5` default 8145 reserving 8143/8144; `modal-focus.cjs:21,79` on 8143; `conditional-formsets.cjs:28-31` on 8144). The signin fixture exists (`presentation_server.py:191-197`). The native pack `formactions.html` consuming `css_class` was not re-verified from the embedded excerpt in this cycle; it is consistent with the prior cycle's independent read.

### 2. Strengths
- C3-A01 carry-through is concrete: separate template-bound records for modal inherited body and full-page choice/no-choice, collected from actual render observations, feeding 09's validator.
- C2-A06 logic is right: the companion test `test_form_pages_frame_through_upstream_content_templates` (`tests.py:251-256`) asserts the theme overrides only the frame, so no `tags/form.html` or workflow copy exists to migrate.
- Existing-copy-only, no-override-growth, exact-base replay and original-digest preservation are all gated by `--verify-replay`.

### 3. Concerns
- **MEDIUM (C4-A02, omission; conditional)** — 07-02 instructs adapting the isolated alert copy to the core `data-cv-alert-dismiss` hook. The companion's `MessagesParityTests.test_plain_include_matches_cv_messages` (`tests.py:556-572`) renders `django_tabler/includes/messages.html` and `{% cv_messages %}` and asserts whitespace-normalized equality, which preserves attributes. If the pack include emits `data-bs-dismiss="alert"` (its content is not in the embedded excerpt, so this is unverified here; it is Tabler's native Bootstrap markup, so it is likely), the hook change alone makes that test a *new* failure in the candidate replay and trips D-13 in 07-03. Class-key adoption does not affect parity, because default values reproduce the hardcoded bytes. The plan does not disposition this. Compliant options: adapt `django_tabler/includes/messages.html` in the patch's pack section in the same step, or keep `data-bs-dismiss` in the copy (dismissal still works through Tabler's bundled Bootstrap) and prove D-12 dismissal that way. Either is acceptable; the plan should pick one before execution so the executor does not discover it as an unexplained regression.
- Inherits C4-A01: 07-02/07-03 must apply purpose IDs to all eight shadows, not four.

### 4. Suggestions
- Add to 07-02: "Run the companion `MessagesParityTests` immediately after the alert-copy adaptation; if parity fails on the hook attribute, adapt the pack include in the same isolated commit and record both hashes under one purpose ID."
- In 07-01's provenance report, record the resolved origin of the pack's `layout/formactions.html` and its `css_class` consumption line, since this cycle could not re-verify it from the excerpt.

### 5. Risk Assessment
**MEDIUM.** Real browser and real companion work always carries execution risk; the plan's fail-closed gates are right, and the one foreseeable regression is cheap to pre-declare.

---

## 06.6-08

### 1. Summary
Documentation anchors and guards exist as the plan states: the single-fence guard for `### Custom alert frame` (`tests/test1/test_alerts.py:250-257` over `docs/reference/theme.md:308`); the numbered owner-resolution structure test (`tests/test1/test_label_mode_docs.py:180`); the E108 migration sentence pair (`test_label_mode_docs.py:786-797` asserting the exact "falls back to its package floor" wording found at `docs/migrating-1.0.md:64`), which is why H07 keeps them together in 08-02. `test_form_button_docs.py`, `test_presentation_migration_docs.py`, the tutorial and `list_view.md` exist; `.venv/bin/mkdocs` is present.

### 2. Strengths
- C2-A02 wording is accurate against source: standalone `{% crispy form %}` of a library form will lose its wrapper (`form.py:43-50` change) but keep its token because `disable_csrf` stays default; the page path suppresses the token only render-locally.
- H10 wording ("owning content, sibling forms allowed, no nested forms even unclassed") matches the scanner contract in 01 and the raw guard precedent (`test_formsets.py:32-34`).
- `theme.md:310` currently says the frame classes "are literal Bootstrap CSS" — 08-01 already owns rewriting that prose outside the single fence.

### 3. Concerns
- None actionable. Note that `tests/test1/test_label_mode_docs.py:379` asserts the literal `(package default "icon")` wording; 08-01's "describe the three layers inside the existing floor step" must keep that string or update the assertion in the same task (the plan already names `test_label_mode_docs.py` in 08-01's files).

### 4. Suggestions
- In the caller-owned outer-form recipe, show both the standalone pattern (caller `<form>` + `{% crispy form %}` emitting the token) and the `cv_render_form` pattern side by side, since the difference in who emits the token is the single thing most likely to produce duplicate tokens in downstream copies.

### 5. Risk Assessment
**LOW.**

---

## 06.6-09

### 1. Summary
Every runtime and artifact the final gates name exists: `.nox/tests-3-12-django-4-2`, `tests-3-12-django-5-2`, `crispy_floor-3-12-django-4-2`, `crispy_floor-3-12-django-6-0`; `examples/bootstrap5/pytest.ini` and `project/settings.py`; `vitest.integration.config.js`; `tests/browser/modal-focus.cjs` and `conditional-formsets.cjs`; `.venv/bin/mkdocs` and `ruff`; `06.5-09-SUMMARY.md` and `06.5-PUBLIC-SURFACE.md` as patterns. `CRISPY_FLOOR_TESTS` (`noxfile.py:28-52`) currently lacks `test_alerts.py` and `test_button_classes.py`, so A15's addition is substantive. The single deselect (`noxfile.py:57`) is the only permitted exclusion. The five new `tests/test1/test_theme_*.py` modules named across plans 01/02/03/05/08 are exactly five.

### 2. Strengths
- C3-A01 validation is specified with negative tests (swapped/missing records) and without changing the production modal template.
- H12 is recorded as a coverage limit, not waived; C2-A03 requires both floor results distinctly.
- Companion Django 6.1 evidence is kept separate from the 4.2/5.2/6.0 core matrix.

### 3. Concerns
- Inherits C4-A01: `--check-final` should reject a baseline/replay whose override inventory omits shadows that exist in the archived companion tree (a directory-enumeration cross-check against the recorded purpose IDs).
- **LOW** — 09-01's ruff format gate is scoped to `src tests examples`; STATE records whole-repo `ruff format --check` as red on planning Markdown. The scoping is correct; state it explicitly in `09-REGRESSION.md` so a future reader does not read "format check passed" as whole-repo.

### 4. Suggestions
- Have `--check-final` verify that the baseline companion failing node IDs include the two predictable pre-existing failures named under plan 06 (icon-set equality and `<input type="submit">`); a baseline that reports them passing against current core would indicate the wrong core was imported.

### 5. Risk Assessment
**LOW–MEDIUM.** Purely evidence orchestration; risk is proportional to the companion gates it depends on.

---

## Cycle 4 resolution verification

| ID | Prior severity | Plans | Verification against source | Verdict |
|---|---|---|---|---|
| C3-A01 | MEDIUM | 05, 07, 09 | `WorkflowView` inherits `cv_content_template` and `cv_modal_supported` (`crud_views_workflow/lib/views.py:18-27`; `crud_views/lib/views/form.py:19-20`); modal selection at `base.py:222-225`; include at `modal/content.html:8`; workflow branches only in `view_workflow.content.html:3-5` and `view_workflow.action.html:6-19`. Plan 05-01 pins the inherited body, asserts origins, tests full-page choice/no-choice separately; 07-02 records template-bound branch records; 09-01 validates them with negative cases. The substantive invariant (modal keeps the generic owning form; full-page keeps choice/omission) is what the plans now test, not an old suggested implementation. | **Closed** |
| C3-A02 | MEDIUM | 06, 07 | Purpose-based counting unit, data-only registration exclusion, renamed-path ID retention and positive/negative comparison tests are specified in 06's artifact section and applied in 07-03. The four named shadows exist in the embedded source and are inspected with origin/hash/render evidence. | **Closed**; see new C4-A01 for enumeration completeness beyond those four |
| C3-A03 | LOW | 02 | `form_label_mode` → `default_label_mode("form")` fallback chain (`label_mode.py:129-146`, `:63-83`); 02-02 tests the composed non-strict fallback to `form="both"`, both diagnostics with distinct values, dedup retention and strict owner-first refusal. | **Closed** |
| H01–H12 | HIGH (historical) | all | Round 1/2 dispositions unchanged in source; H06 source acquisition closed in Round 2 and confirmed by the embedded `885dfc7` excerpts. Fresh baseline, replay, browser and human observations remain execution deliverables and are not revived here. | **Remain closed** |

---

## Final list of current findings

### Current unresolved HIGH
**None.**

### Current actionable MEDIUM / LOW — omissions (need a plan edit)

| ID | Severity | Plan(s) | Required disposition |
|---|---|---|---|
| C4-A01 | MEDIUM | 06-01, 07-02/03, 09-01 | Enumerate every shadow under `src/crud_views_tabler/templates/crud_views/` (at least eight at `885dfc7`: `modal/shell.html`, `table/bootstrap5.html`, `tags/card.html`, `view_card.content.html` plus the four named) and every bespoke Python override (`checks.py` private-import check, `icons.render`) with purpose IDs; keep the four as the render-evidence subset; add a negative test for an omitted pre-existing shadow; have `--check-final` cross-check inventory against the archived tree. |
| C4-A02 | MEDIUM (conditional on pack include content) | 07-02, 07-03 | Pre-declare how `MessagesParityTests.test_plain_include_matches_cv_messages` (`tests.py:556-572`) is handled when the alert copy's `data-bs-dismiss="alert"` (`alert.html:17`) is changed to `data-cv-alert-dismiss`: adapt `django_tabler/includes/messages.html` in the pack section under the same purpose ID, or retain the Bootstrap hook in the copy and prove D-12 dismissal with it. Do not let it surface as an unexplained new regression. |
| C4-A04 | LOW | 03-01 | Fix wording: the floor `formactions.html` has `label_class`/`field_class` branches but no hidden-input branch; whole-source equality is the predicate. |

### Current LOW — already incorporated or explicit deferrals (no plan edit required; recorded for execution)

| ID | Plan(s) | Status |
|---|---|---|
| C4-A03 | 06-02, 09-01 | Predictable pre-existing companion failures (`test_every_upstream_icon_name_is_mapped`, `test_delete_form_is_the_stock_crispy_delete_form`) are covered by "record failures, never relabel"; optionally pre-register them as a positive control. |
| C4-A05 | 05-01 | No workflow modal fixture exists in `tests/test1/app/views.py`; covered by the "local test-only routes" clause. Name the fixture in the summary. |
| xdist preflight | 06-02 | Companion test group lacks pytest-xdist (`pyproject.toml:32`); plan halts under the install gate. This is the first predictable stop; surface it to the user before execution. |
| C2-A05 | 05 | Retained compatible `form_tag=False` helpers (`EventForm`, `PublisherMainForm`, `BookMainForm`, `BrowserPublisherForm`, `AuthorMainForm`) remain an explicit deferral. |
| H06 execution evidence | 06, 07, 09 | Baseline, replay, browser and human observations are execution gates, not planning defects. |
| H12 | 09 | Current-pack Django 6.0 recorded as untested; not waived. |
| `theme.md:310` | 08-01 | Stale "literal Bootstrap CSS" sentence; owned by the existing task. |

---

## Overall risk assessment

**MEDIUM, trending LOW once C4-A01 and C4-A02 are dispositioned.** Core product plans (01–05, 08) are source-grounded at the line level and their dependency ordering is correct (01 → 02/03/05; 04 → 03; 02/03/04/05 → 07/08 → 09, with no same-wave file overlap). The remaining risk sits where it should: the floor pack bridge experiment (03) and the real-companion evidence chain (06/07/09). Both new MEDIUMs are companion-evidence completeness issues that are cheap to fix in plan text and would otherwise degrade the D-13/D-18 numbers the phase reports to Phase 7. No previously closed HIGH is revived, and the plans are otherwise ready for execution after those two edits.
