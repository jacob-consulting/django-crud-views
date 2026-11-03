I'll verify each plan against the current source, not the plan text alone. Starting with the ownership, label-mode, class-table, and alert seams the plans claim to change.
The nested-form and alert seams match the plans' starting point. Next I'll check workflow routing, label-mode fallback, and the class-key grammar those plans depend on.
## 06.6-01

**Summary.** The ownership design matches the current nested-form bug and the render boundary that must fix it. `CrispyFormMixin.helper` and `CrispyDeleteForm.helper` still build a default `FormHelper` with no `form_tag=False` (`src/crud_views/lib/crispy/form.py:43-50`, `:136-146`), while the page already owns the form and token (`src/crud_views/templates/crud_views/view_create.content.html:5-10`). `cv_render_form` flattens the context (`src/crud_views/templatetags/crud_views.py:464-466`), and `tags/form.html:3-6` reads `form.helper` twice by truthiness. The plan’s selected-helper, render-local CSRF suppression, and atomic golden migration are the right boundary. Prior H02/H03/H09/H10/A10 actions are in the task text, not missing evidence.

**Strengths.**
- Outer ownership is already in the page templates, including protected-delete omission (`view_delete.content.html:8-22`). The plan does not move method, action, or enctype onto the helper.
- It preserves `Context.dicts`, which form-button ownership actually scans (`src/crud_views/lib/crispy/buttons.py:49-77`) and which formset layout captures before its own flatten (`src/crud_views/lib/formsets/layout.py:14-18`). `cv_alert` is the right pattern (`crud_views.py:453-455`).
- Standalone library-wrapper removal is separated from page-token suppression, and workflow’s direct `{% crispy %}` (`view_workflow.action.html:15`) is explicitly left for plan 05.

**Concerns.**
- None actionable beyond execution. The alias-copy halt is a required stop, not a hole. Future CSRF and golden evidence is an execution task, not a missing plan task.

**Suggestions.**
- When implementing the `cv_alert` pattern, keep its `mark_safe` around `template.template.render(context)`. A plain string return would escape the form.

**Risk Assessment.** LOW. The mechanism is pinned to the current render path, and the dangerous cases (alias mutation, unclassed nested forms, fixture drift) are explicit gates.

## 06.6-02

**Summary.** The theme floor is absent today: `default_label_mode` reads only the setting, then `LABEL_MODE_DEFAULTS` (`src/crud_views/lib/view/label_mode.py:23-25`, `:86-119`). Owner maps stay above that floor (`base.py:316-349`; `form_label_mode` at `label_mode.py:122-146`). W292 already calls `cv_get_action_label_mode` (`src/crud_views/lib/view/buttons.py:569-572`), so a resolver change reaches both context and form checks without a new check implementation. Atomic rebind, setting-free fallback, and the composed owner/setting case are specified correctly against the strict-before-fallback order at `label_mode.py:73-74`.

**Strengths.**
- Does not merge owner maps, and does not rename the singular/plural APIs.
- E108 remains a settings check (`src/crud_views/lib/settings.py:159-188`), distinct from registration `ValueError`.
- Autouse rebind isolation matches a module-global registry. The class registry’s in-place update (`button_classes.py:135-138`) is deliberately not copied, which avoids a partial publish.

**Concerns.**
- None actionable. C3-A03 is an execution test, not an undescribed branch.

**Suggestions.**
- In the registration docs owned by plan 08, state that later `AppConfig.ready()` wins and that order follows `INSTALLED_APPS`. The plan already says “later wins”; the Django ordering is the part authors will get wrong.

**Risk Assessment.** LOW. Precedence and recursion boundaries match the current resolver.

## 06.6-03

**Summary.** The floor failure is real and identical on both cached floor runtimes. Both `formactions.html` files are `class="mb-3"` with `flat_attrs`, `label_class`, `field_class`, and `fields_output`, and neither reads `css_class` (`.nox/crispy_floor-3-12-django-4-2/.../formactions.html:1-8` and the Django 6.0 copy). The current pack does read `formactions.css_class`. Three constructors exist (`form.py:55-56`, `:141-144`, `list.py:125-133`). The filter helper caches the group object once per prepared layout (`list.py:172-179`), so baking classes in `__init__` would freeze them. The plan’s render-time key lookup is the mechanism that actually satisfies H05. C4-A04’s whole-source predicate matches the file, including the absent hidden-input branch.

**Strengths.**
- Refuses a generic sentinel fallback and a global `bootstrap5/layout/formactions.html` shadow.
- Keeps filter hidden inputs on the helper `add_input` path (`list.py:114-123`), separate from the group template.
- 86-to-88 is sequenced after plan 04. Current count is 84 (`tests/test1/test_button_classes.py:105`, `docs/reference/buttons.md:151`). `form:actions` stays out of `FORM_KINDS` (`button_classes.py:240`), so `form:actions:icon` remains an unknown key (`:262-265`, `:339-345`).

**Concerns.**
- None actionable. If the exact floor source does not match, the plan stops for a support decision instead of dropping classes. That is the correct failure.

**Suggestions.**
- Resolve classes inside the group object’s render method, not in `get_form_actions()`. Individual button `field_classes` are already frozen at construction (`src/crud_views/lib/crispy/buttons.py:142`); do not “fix” that here.

**Risk Assessment.** LOW for the scoped bridge. MEDIUM only if execution treats a failed exact-source predicate as permission to ship a different wrapper. The plan forbids that.

## 06.6-04

**Summary.** The frame still hard-codes the two class strings and already uses the core dismiss hook (`src/crud_views/templates/crud_views/tags/alert.html:2-5`). The golden is the byte target, including the newline before `role` (`tests/test1/golden/alerts/dismissible.html:1-7`). `cv_button_class` returns a plain string through a `simple_tag` (`crud_views.py:570-573`, `button_classes.py:154-165`), so hostile values escape unless marked safe. Empty-value spacing is specified tightly enough to keep that golden.

**Strengths.**
- Does not regenerate the golden, and does not add focus or auto-dismiss behavior.
- Inventory moves 84 to 86 in the same task as the defaults, before plan 03’s 86 to 88.
- Mode-suffixed utility keys stay invalid because `alert` is not a variant location (`button_classes.py:239-265`).

**Concerns.**
- None actionable. The Tabler copy still using `data-bs-dismiss` is plan 07’s work, not a hole in this core change.

**Suggestions.**
- Keep the dismissible separator in the template, not inside the class-table value. The golden has no trailing space on the level classes.

**Risk Assessment.** LOW.

## 06.6-05

**Summary.** The workflow split the plan preserves is what the code does. `WorkflowView` overrides `template_name` to `view_workflow.html` (`src/crud_views_workflow/lib/views.py:18-27`) and does not override `cv_content_template`, so it inherits `crud_views/view_custom_form.content.html` and `cv_modal_supported = True` (`src/crud_views/lib/views/form.py:18-20`). The full page includes history plus `view_workflow.action.html` (`view_workflow.html:3-4`, `view_workflow.content.html:3-5`), and only that action template branches on `has_workflow_choices` and calls crispy directly (`view_workflow.action.html:6-18`). Modal content includes `view.cv_content_template` (`modal/content.html:8`), so a modal workflow never renders the workflow action template. Create and update stay on the base `cv_modal_supported = False` and E251 (`base.py:111`, `:167-171`).

**Strengths.**
- C3-A01 is accurate: modal success must not be recorded as full-page workflow branch coverage.
- Parent `form_tag=False` overrides are only that assignment (`tests/test1/app/views_formset.py:44-50`, `examples/bootstrap5/formsets/views.py:36-41`). Child helpers already suppress their own tag and token (`inline_formset.py:57-59`).
- C2-A05’s retained helper overrides are explicitly not cleaned up.

**Concerns.**
- None actionable. The full-page workflow form has no `action` or `enctype` (`view_workflow.action.html:8`); the plan correctly leaves page attributes alone rather than copying the custom-form attributes onto it.

**Suggestions.**
- In the result record, store included template origins from the response, not a constant. The plan already says this; it is the check that stops a modal body from being labeled as `view_workflow.action.html`.

**Risk Assessment.** LOW. The template split is the main trap, and the plan tests both sides.

## 06.6-06

**Summary.** Source identity is no longer the blocker. The pinned companion revision is the supplied monorepo, and plans archive `cb26af4` rather than mutable HEAD. That pin is still the product tree: `cd5e9a5` has no diff from `cb26af4` under `src/`, `tests/`, `examples/`, `noxfile.py`, `docs/`, or `CHANGELOG.md`. C4-A01’s exhaustive tree classification is an execution requirement, not an allowlist of the eight embedded shadows. Baseline isolation and dirty `settings.py` exclusion match the amended D-11/D-14 rule.

**Strengths.**
- Import-pure utility, negative omission fixtures, and purpose IDs rather than file counts.
- `--check-baseline` stays on the pinned archive after an authorized companion commit, instead of treating that commit as corruption.
- The embedded theme really does shadow `tags/alert.html`, `form_frame.html`, both filter templates, `modal/shell.html`, `table/bootstrap5.html`, `tags/card.html`, and `view_card.content.html`. The plan treats that list as a floor, not a ceiling.

**Concerns.**
- MEDIUM: companion pytest is specified as `pytest tests -n 4`, but the companion test extra is only `pytest`, `pytest-django`, and `crispy-bootstrap5==2026.9` (embedded `pyproject.toml:30-32`). xdist was already observed absent. The plan halts instead of using the README’s serial pytest. That is a predictable preflight stop, not a product defect, and it blocks 07 and 09 if left unchanged.

**Suggestions.**
- If xdist is absent, run the companion’s declared `pytest` serially and record that reason. Do not install an undeclared plugin without the legitimacy gate. Django `--parallel` is a separate flag; do not conflate it with xdist.

**Risk Assessment.** MEDIUM until the parallel-flag halt is given a serial disposition. Source acquisition itself is not the risk.

## 06.6-07

**Summary.** Browser acceptance is aimed at the real theme, and the embedded companion confirms the seams the plan names. `tags/alert.html` hard-codes dismissal classes and `data-bs-dismiss="alert"` (embedded companion `alert.html:7-17`). `MessagesParityTests` currently requires whitespace-normalized equality with the native include (`tests.py:556-572`). `form_frame.html` only adds a card outside the modal (`form_frame.html:1-6`). There is no embedded `tags/form.html` or `view_workflow.action.html`, so creating those copies would grow overrides. The local Tabler 1.6.1 archive is not an asset substitute; these plans do not authorize swapping it in for the companion’s loaded assets.

**Strengths.**
- C4-A02 keeps the standalone include on `data-bs-dismiss` and the CRUD frame on `data-cv-alert-dismiss`, with negative parity cases and unchanged `PackageTests`.
- Full-page workflow and inherited-body modal records are separate, matching plan 05 and `modal/content.html:8`.
- Port 8145 is shared with the presentation harness and must not kill a foreign listener.
- Native `formactions.html` is adapted only if a render probe shows it drops classes. The research addendum says the pinned pack already consumes `css_class`; the plan requires that proof rather than a manufactured diff.

**Concerns.**
- MEDIUM, inherited from 06: replay of both companion suites with `-n 4` halts if xdist is still absent. A green isolated core suite cannot fill that hole.
- Pending browser, patch, and replay artifacts are execution evidence, not missing tasks.

**Suggestions.**
- Do not point the harness at `/home/alex/projects/tabler/tabler-1.6.1` when a CDN asset fails. Record the missing asset and stop.

**Risk Assessment.** MEDIUM. The scenario matrix is right; acceptance still depends on a real baseline and on not substituting assets or suites.

## 06.6-08

**Summary.** The doc guards the plan must not break are real. `test_migration_e108_location_inventory` requires the exact package-floor sentence (`tests/test1/test_label_mode_docs.py:797`, `docs/migrating-1.0.md:64`). `test_alerts.py:250-253` requires one django/html fence under `### Custom alert frame`. The current theme prose still says those classes are literal and that authors must copy the frame (`docs/reference/theme.md:310-311`). Pairing the migration sentence with its test in 08-02, and leaving 08-01’s reference edits outside that pair, is the correct task split.

**Strengths.**
- Standalone library-wrapper removal is a Breaking note with a caller-owned form recipe, distinct from page-token suppression.
- Copied workflow templates are a documented migration, with the unsupported old-copy limit stated.
- Tutorial `get_form_actions` replacement text is explicitly retained.

**Concerns.**
- LOW: “explain alert replacement” can be satisfied by a new paragraph while `theme.md:310-311` still says copying the frame is how you restyle. That would contradict THEME-04.

**Suggestions.**
- Rewrite that lead sentence so the class keys are the supported path and the fenced copy remains the full-frame escape hatch. Do not add a second fence.

**Risk Assessment.** LOW. The executable-doc machinery is already in place.

## 06.6-09

**Summary.** Final acceptance correctly depends on 07, 08, and 10, and it refuses to treat missing companion or human evidence as pass. The core matrix commands on current-pack 4.2/5.2 and the separate current-pack Django 6.0 limit are consistent with `noxfile.py:3` and the cached floor sessions. C4-A01/C4-A02 and delivered-source binding are checks, not new product work. Human visual results are correctly left pending.

**Strengths.**
- Full current-pack `pytest tests` on 4.2 and 5.2, plus docs, ruff, and the named preservation browser scripts.
- Floor evidence is required on both cached interpreters, and the one historical deselect stays `test_filter_form_baseline` (`noxfile.py:54-57`).
- Halted summaries are required when upstream evidence is missing. That is the right response to absent execution artifacts.

**Concerns.**
- MEDIUM: the integrated floor command is `pytest tests` on the floor interpreters, but the established floor session runs only `CRISPY_FLOOR_TESTS` (`noxfile.py:28-52`, `:106`). Phase 6’s green floor evidence was that selection, not the full tree. The plan forbids another waiver. A pre-existing floor-only failure outside that selection, reproduced on `cb26af4`, would become an undifferentiated phase blocker.
- The human check lists create/update next to a modal replacement. Create/update modal support is still E251 (`base.py:167-171`). A reader can treat a missing create/update modal as incomplete acceptance.

**Suggestions.**
- Before the floor gate, record an unmodified `cb26af4` full-tree floor result, or scope the required floor command to the expanded `CRISPY_FLOOR_TESTS` plus the named preservation modules. Do not deselect a new phase test.
- Say in the human check that create/update are full-page only.

**Risk Assessment.** MEDIUM. The handoff contract is complete; the floor command is broader than the contract that has actually been green.

## 06.6-10

**Summary.** Companion delivery is authorized and correctly placed after a green exact-base replay, not instead of it. The files named are the real adoption points: registration, class defaults, the existing alert shadow, the parity test, and a conditional pack template that should stay unchanged if its probe passes. Private `settings.py` preservation is a must-have, and `--require-committed` rejects an uncommitted task hunk without demanding that the dirty settings file be clean.

**Strengths.**
- Delivery is byte-bound to the replayed candidate, including post-hook recheck.
- No push or publication. Core and companion commits are recorded separately.
- Does not create absent form or workflow copies, and does not add a core dependency to `django_tabler`.

**Concerns.**
- MEDIUM: “commit only task-owned hunks” does not forbid `git add -A` or `git commit -a`. `example/config/settings.py` is a tracked dirty file. Either command would sweep it into the companion commit and break the preservation invariant the rest of the phase is built around.

**Suggestions.**
- Stage only the patch paths that actually changed, by path. Refuse the commit if `git diff --cached --name-only` contains `example/config/settings.py` or any path absent from the tested patch.

**Risk Assessment.** MEDIUM for the commit step only. The delivery sequence itself matches amended D-11/D-14.

## Cross-plan

The ten plans cover THEME-01–06 without reviving the superseded temporary-copy rule. Wave order is consistent: 01/04/06 in wave 1, 02/03/05 in wave 2, 07 and 08 in wave 3, 10 after 07, 09 last. Shared edits to `form.py`, `buttons.md`, and the key inventory are dependency-ordered. Product source at `cd5e9a5` is still the `cb26af4` tree those plans pin.

Incorporated and not reopened: raw owner scanning, atomic golden migration, workflow template split, floor whole-source bridge predicate, cached group-class resolution, exhaustive companion inventory, native/CRUD hook parity, and real companion commits with dirty-settings preservation. Missing baseline, browser, and delivery artifacts are future execution evidence.

Unresolved before execution: companion pytest `-n 4` without declared xdist (06, inherited by 07 and 09); full-tree floor pytest without a pre-change full-tree floor baseline (09); path-limited companion commit so dirty `settings.py` cannot be swept (10). None of these authorize asset substitution from the Tabler 1.6.1 archive.

**Overall risk: MEDIUM.** The product mechanisms match the source. The remaining risk is verification and commit hygiene, not an undescribed ownership, class, or dismissal path.
