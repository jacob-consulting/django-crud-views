I'll verify each plan against the current source, starting with the form, label-mode, class-table, alert, and workflow seams the plans depend on.
Cycle 5's concrete `form=both`, native icon, five-kind/three-mode, reset, and split-commit instructions are in the plans and match the source. One companion preservation check is still missing.

## 06.6-01

**Summary.** The create-path tracer matches the real nested-form bug: library helpers allocate a wrapping `FormHelper` on every access, and the inner template reads that property twice, while the page already owns the form and token. The atomic 01-01/01-02 commit and the workflow deferral are specified against those files, not assumed.

**Strengths.**
- `src/crud_views/lib/crispy/form.py:43-50` and `:136-146` build a new `FormHelper` and never set `form_tag=False`. `src/crud_views/templates/crud_views/tags/form.html:3-6` then tests `form.helper` and passes `form.helper` again, so a falsey or fresh helper is a second resolution. Selecting once by presence is the right fix.
- `src/crud_views/templatetags/crud_views.py:464-466` flattens the context; `cv_alert` at `:453-455` already keeps `Context.dicts`. Reusing that pattern protects `src/crud_views/lib/crispy/buttons.py:80-92`, which stops at the first non-`None` owner tier.
- `src/crud_views/templates/crud_views/view_create.content.html:5-10` already owns method, enctype, and `{% csrf_token %}`. Keeping `disable_csrf` inside `cv_render_form` is what leaves standalone library tokens intact.
- `tests/test1/test_form_button_checks.py:560-585` custom helpers do not set `form_tag=False`. Migrating those two fixtures in the same commit as the renderer avoids a red `form_tag=True` policy test.

**Concerns.**
- LOW: 01-01 is `type="tracer"`. The installed executor commits a tracer like an auto task before the next task. The plan forbids that commit until 01-02. A contract-literal executor can commit red goldens or stop on an empty core commit. The shared boundary is written; the task type does not implement it.

**Suggestions.**
- Mark 01-01 `type="auto"` with the same "commit only with 01-02" line, or name the tracer commit rule as an explicit deferral the executor must follow.

**Risk Assessment.** LOW. The ownership mechanism is grounded, and the workflow hole is explicitly left to plan 05.

## 06.6-02

**Summary.** The theme floor belongs in `default_label_mode`, which today merges only the live setting over the immutable package table. Atomic rebind is stricter than the class registry and matches D-06.

**Strengths.**
- `src/crud_views/lib/view/label_mode.py:23-25` is `{"context": "icon", "list": "icon", "card": "both", "form": "label"}`. `default_label_mode` at `:86-119` reads settings per call and falls back with `LABEL_MODE_DEFAULTS[location]`, so there is no theme slot yet.
- Strict mode raises in `_invalid_label_mode` at `:73-74` before the fallback runs. A setting-free `_theme_or_package_default` avoids re-entry while a bad setting is installed.
- `src/crud_views/lib/view/buttons.py:434-435` and `:546-555` already call the public resolver and skip when it raises. W292 follows a theme floor without new form construction. E108 at `src/crud_views/lib/settings.py:159-188` stays a settings-shape check.
- `register_button_classes` at `src/crud_views/lib/button_classes.py:135-138` mutates the published dict in place. Rebind-under-lock is the right divergence for D-06.

**Concerns.**
- None unresolved. C3-A03's composed owner-map plus bad setting is specified against `form_label_mode` at `label_mode.py:122-145`, which calls `default_label_mode("form")` only as the non-strict fallback.

**Suggestions.**
- None.

**Risk Assessment.** LOW. Precedence and check wiring match the current resolver.

## 06.6-03

**Summary.** Independent group keys are justified by three separate constructors, and the filter helper will ignore later class changes unless the key is resolved at render. The floor bridge is fail-closed on exact installed-template identity rather than a missing `css_class` token.

**Strengths.**
- Ordinary, delete, and filter groups are built separately at `src/crud_views/lib/crispy/form.py:55-56`, `:141-144`, and `src/crud_views/lib/views/list.py:125-133`. Delete does not call `get_form_actions`.
- `ListViewFilterFormHelper.render_layout` at `list.py:172-179` stores `_cv_actions` once per prepared layout. A class baked in at construction would survive `register_button_classes` (`button_classes.py:135-138`) and `setting_changed` (`:129-132`). Primitive key plus render-time lookup is the mechanism that makes H05 true.
- W362 at `button_classes.py:328-345` accepts any key already in `DEFAULT_BUTTON_CLASSES`. New utility keys are accepted; mode suffixes still fall through `_action_key_parts`. The live count is 84 (`tests/test1/test_button_classes.py:105`, `docs/reference/buttons.md:151`). 86 then 88 is the right arithmetic if plan 04 lands first, and `depends_on` includes 04.
- `noxfile.py:22-24` and `:54-57` pin the floor and deselect only `test_filter_form_baseline`. Plan 03-03 does not widen that exclusion.

**Concerns.**
- None unresolved. The floor template itself is not in this checkout's search path, so exact 2023.10 bytes remain an execution proof, which the plan already requires before the bridge is eligible.

**Suggestions.**
- None.

**Risk Assessment.** LOW. A1 is an experiment with a stop, not an inherited fact.

## 06.6-04

**Summary.** The two alert keys replace literals that are still hard-coded, and the default-byte and inventory tasks are in the same commit as the defaults. This is the right size.

**Strengths.**
- `src/crud_views/templates/crud_views/tags/alert.html:2-5` interpolates `alert-dismissible fade show` and `btn-close` directly, and keeps `role="alert"`, `type="button"`, `data-cv-alert-dismiss`, and `{% translate 'Close' %}`.
- The leading space before `alert-dismissible` is inside the `if`. Pinning empty/None to exactly `alert alert-success` (`alert:success` at `button_classes.py:94`) and `class=""` on the close control matches that template.
- `tests/test1/test_button_classes.py:105` and `docs/reference/buttons.md:151` are the 84-key guards. Updating both in 04-01, before plan 03's 88, avoids a red inventory commit.

**Concerns.**
- None unresolved. `docs/reference/theme.md:310-311` still says those classes are literal and that a theme must copy the frame. Plan 08 owns that sentence. Leaving it untouched here is correct wave separation.

**Suggestions.**
- None.

**Risk Assessment.** LOW.

## 06.6-05

**Summary.** Full-page workflow and modal workflow are different templates today, and the plan tests them separately instead of flipping `cv_content_template`. Create/update modal rejection is a real class flag, not a doc claim.

**Strengths.**
- `WorkflowView` (`src/crud_views_workflow/lib/views.py:18-27`) subclasses `CustomFormView` and sets `template_name` only. It inherits `cv_content_template = "crud_views/view_custom_form.content.html"` and `cv_modal_supported = True` from `src/crud_views/lib/views/form.py:18-20`.
- Full-page workflow includes `view_workflow.content.html`, which includes `view_workflow.action.html` (`src/crud_views_workflow/templates/crud_views_workflow/view_workflow.html:3-4`, `view_workflow.content.html:3-5`). The action template still calls `{% crispy form form.helper %}` inside its own form and token (`view_workflow.action.html:6-16`). Replacing that call is the actual D-16 fix. Modal content includes `view.cv_content_template` (`src/crud_views/templates/crud_views/modal/content.html:8`), so a modal pass cannot prove the action branch.
- `CreateView` does not set `cv_modal_supported` (`src/crud_views/lib/views/create.py:12-14`). The base default is `False` (`src/crud_views/lib/view/base.py:111`) and E251 is `:167-171`.
- Parent workarounds only assign `form_tag=False` after `super().helper` (`tests/test1/app/views_formset.py:44-50`, `examples/bootstrap5/formsets/views.py:36-41`). After plan 01 they are redundant. The deferred helpers in the ledger still only set `form_tag=False` and stay compatible.

**Concerns.**
- None unresolved. C2-A01 and C3-A01 are written against these template identities.

**Suggestions.**
- None.

**Risk Assessment.** LOW. Stock ownership is specified. Companion copies stay in 07.

## 06.6-06

**Summary.** The acquisition utility is aimed at the supplied monorepo and at fail-closed tree classification. It does not yet require the URL-less cancel assertion that cycle 5 asked to bind through replay and delivery.

**Strengths.**
- Embedded companion `apps.py:15-31` registers icons, classes, and assets only. `buttons.py:3-44` has no `form:actions`, `form:filter-actions`, `alert:dismissible`, or `alert:close`. `icons.py:12-47` has no `save`, `cancel`, or `filter-reset`. `tests.py:98-139` asserts the whole class dict. The validator's exact-value checks match those files.
- The eight shadows named as a floor, not a limit, are in the embedded tree, including `modal/shell.html` and `tags/alert.html` (`alert.html:17` still has `data-bs-dismiss="alert"`). `checks.py:3-12` and `icons.py:50-51` are behavior, not data-only registration. Counting them separately is right.
- Baseline isolation against pinned `cb26af4` and preservation of dirty `example/config/settings.py` matches amended D-11. `--require-committed` using `git -C` on the companion root is the contract-compatible way to prove a non-core commit.

**Concerns.**
- MEDIUM: Replay and delivery validation require kind/mode/reset and exact class equality, but no plan text requires a URL-less cancel. `src/crud_views/lib/view/button_data.py:355-357` keeps tag `button` unless `selected_tag == "a"` and `cancel_url` is nonempty. A create page always has a destination, so the five-kind matrix can pass without that fallback.

**Suggestions.**
- Add one URL-less cancel render, in both/icon/label, to the replay/delivery required results, asserting a `<button>` and no empty `href`, even though Tabler does not override `form:cancel-tag`.

**Risk Assessment.** MEDIUM. Provenance design is sound. The missing assertion is the remaining C5-H01 hole.

## 06.6-07

**Summary.** Candidate acceptance now names `register_label_mode_defaults({"form": "both"})`, the three native mappings, the four class strings, and all five kinds in three modes plus native reset. That closes the aggregate-count failure mode. It still never names the URL-less cancel fallback.

**Strengths.**
- `CrudViewsTablerConfig.ready` (`apps.py:15-31`) is the registration site. `Reset.slot = "form:filter-reset"` (`src/crud_views/lib/crispy/buttons.py:212-213`) and the kind icons at `:23` and `:117-119` are what `save` / `cancel` / `filter-reset` must hit. Retaining `delete=tabler:trash` and `filter=tabler:filter` matches `icons.py:18` and `:24`.
- `tests.py:139` is `assertEqual(TABLER_BUTTON_CLASSES, expected)`. Extending that literal and forbidding a subset assertion is the C5-A08 mechanism.
- `MessagesParityTests` (`tests.py:556-572`) compares whitespace-normalized markup only. Today's theme alert uses `data-bs-dismiss` (`alert.html:17`) while core uses `data-cv-alert-dismiss` (`src/crud_views/templates/crud_views/tags/alert.html:5`). Changing only the CRUD copy without a one-attribute parity delta would fail this test. The plan's negative hook cases match that comparator.
- Port 8145 is `presentation.cjs:2` and `presentation_server.py:7`. Shared default plus "do not kill the other listener" matches that code. Absent `tags/form.html` and `view_workflow.action.html` in the embedded tree matches the "do not create a copy" rule.
- Workflow modal versus full-page branch records follow `views.py:18-27` and `view_workflow.content.html:3-5`.

**Concerns.**
- MEDIUM: Same URL-less gap. 07-02's cancel line is "preserve cancel link/button navigation". It does not require a cancel with no `data-cv-cancel-url` (`button_data.py:354-357`) under `form=both` in candidate, replay, and the partial delivery probe.
- LOW: `django_tabler.icons.ICONS` is not in the embedded excerpts, so "check / arrow-left / filter-x already exist" is unverified here. Empty SVG failure is specified (`icons.py` render returns nothing for an unknown name, per `tests.py:51-54`). That is fail-closed, not a planning hole.

**Suggestions.**
- Put the URL-less button assertion next to the five-kind/three-mode block, and require it in `07-tabler-replay.json`.

**Risk Assessment.** MEDIUM. Icon and class contracts are now executable. The no-URL check is the open C5-H01 item.

## 06.6-08

**Summary.** Migration docs are tied to guards that already fail on the wrong edit: the E108 sentence, the single alert fence, and the standalone wrapper change plan 01 will actually make.

**Strengths.**
- `docs/migrating-1.0.md:64` says an invalid mode "falls back to its package floor." Updating that sentence with `test_migration_e108_location_inventory` is required, not optional.
- `docs/reference/theme.md:308-321` has one `django` fence under `### Custom alert frame`, and `:310-311` still says the classes are literal. Utility prose outside that fence is the only edit that keeps the extractor green.
- Standalone library forms currently wrap because `CrispyFormMixin.helper` leaves `form_tag` at the crispy default (`form.py:43-50`). Documenting caller-owned outer markup, distinct from page-token suppression, matches D-19.
- Workflow copy migration is aimed at `view_workflow.action.html:15`, which is the direct `{% crispy %}` bypass.

**Concerns.**
- None unresolved. Companion no-URL coverage is not this plan's gate.

**Suggestions.**
- When explaining cancel links, cite `button_data.py:355-357` so the published contract includes the URL-less button fallback the companion gates still omit.

**Risk Assessment.** LOW.

## 06.6-09

**Summary.** Final acceptance is gated on plan 10's delivered tree, both floor interpreters, and the concrete icon/class results. It will still pass if those results omit a URL-less cancel, because the validator is not told to require one.

**Strengths.**
- `noxfile.py:28-52` does not yet include the new `test_theme_*.py` modules. Appending them, and checking that list by AST, makes the floor session actually collect the new cases. The only deselect remains `:57`.
- Binding `apps.py`, `icons.py`, `buttons.py`, and `tests.py` to replay and delivery identities matches the files plan 10 is allowed to change. Core `evaluation-scope` cannot see `git -C` companion commits. Requiring a separate companion receipt is the right reading of the executor contract.
- Workflow origin checks follow `form.py:19` versus `view_workflow.content.html:5`. A generic modal pass cannot satisfy the full-page branch.
- `.planning/PROJECT.md:71` still says companion worktrees stay unchanged. That sentence is superseded by amended D-11/D-14. This plan should not treat it as authority. It is also not in `files_modified`, so execution will not refresh it.

**Concerns.**
- MEDIUM: `--check-final` repeats the C5-H01 icon/mode/reset requirements and does not require the URL-less cancel result. The phase can be marked accepted without that check.
- LOW: Stale `PROJECT.md:71` can confuse a later reader. It is not a reason to block delivery.

**Suggestions.**
- Reject final evidence that lacks the URL-less cancel assertion. Point the handoff at CONTEXT D-11/D-14, not `PROJECT.md:71`.

**Risk Assessment.** MEDIUM. The gate is otherwise source-bound. It certifies the checks it lists, and the no-URL check is not listed.

## 06.6-10

**Summary.** The shared companion commit for 10-01/02 and the core-only 10-03 evidence commit match the installed executor: `sub_repos` is not configured, so `commit-to-subrepo` must not be used, and companion paths must not be `git add`ed in core. The temporary index is the right way to keep the user's index. `type="tracer"` on 10-01 still fights that boundary.

**Strengths.**
- Delivery files match the embedded tree: `apps.py` has no label-mode call; `buttons.py:3-44` lacks the four keys; `icons.py:12-47` lacks the three mappings; `alert.html:17` still has `data-bs-dismiss`; `tests.py:139` is full-dict equality. The allowlist is those paths plus conditional `formactions.html`.
- The executor commits in cwd after each task and forbids `git add -A`, stash, and blanket reset. `git -C` with a private `GIT_INDEX_FILE`, `read-tree` of the companion HEAD, and `apply --cached` of only the reviewed patch implements that without a core commit of sibling files. Keeping companion SHAs out of the core Task Commits section matches `actuals.commits` being measured from the core ledger.
- 10-01's label-floor probe is partial and cannot satisfy `--verify-replay`. 10-02 runs `--require-committed` only after the provisional byte check. That is the C5-A01 split, not "every task commit is core".
- Unrelated dirty `settings.py` is excluded from the patch and compared to a pre-delivery digest. That is the preservation D-11 requires.

**Concerns.**
- MEDIUM: 10-01 is `type="tracer"`. The installed contract says execute and commit exactly like `type="auto"` before the next task. The plan says do not commit and do not pass `../` paths to core `git add`. A literal executor either halts on an empty core commit or tries to stage sibling paths. The shared-commit prose does not change the task type, so the contract conflict is still executable.
- MEDIUM: The delivery probe requires five kinds, three modes, and reset. It does not require a URL-less cancel (`button_data.py:355-357`).
- LOW: Worktree path check `#3099` refuses writes outside a linked worktree. These plans do not set `isolation: worktree`. On the main checkout the check does not run. If the orchestrator uses a linked worktree, `../tabler-test` edits halt unless the plan names an authorized exception.

**Suggestions.**
- Change 10-01 to `type="auto"` and state that the 10-02 companion commit is the task commit for both tasks, so the tracer rule does not fire.
- Add the URL-less cancel assertion to the label-floor probe and to `--require-committed`.
- One line: companion edits are authorized outside the core worktree; do not treat `#3099` as a scope refusal.

**Risk Assessment.** MEDIUM. Commit accounting is otherwise the contract-correct design. The tracer type and the missing no-URL check are the residual execution gaps.

## Cross-plan

C5-H01's concrete registrations are specified in 07 and enforced again in 06, 09, and 10, against `apps.py:15-31`, `icons.py:12-47`, `buttons.py:3-44`, and `tests.py:139`. C5-A08 is the same full-dict equality, not a subset. C5-A01 is a real two-repository protocol: companion commit via temporary index, core commit only for the delivery manifest. That is what the executor allows when `sub_repos` is empty. Do not reopen it as "10-01 needs a core hash."

The unresolved items are narrow. No plan text requires the URL-less cancel fallback at `button_data.py:355-357` on the candidate, replay, or delivery path. 10-01 remains a tracer, so the shared commit can still lose to the executor's per-task commit rule. Neither reopens form ownership, the theme floor, the pack bridge, or alert defaults.

**Overall risk: MEDIUM.** Prior high findings are incorporated and fail-closed. Acceptance can still go green without the URL-less cancel check, and a contract-literal executor can break the 10-01/02 commit boundary.
