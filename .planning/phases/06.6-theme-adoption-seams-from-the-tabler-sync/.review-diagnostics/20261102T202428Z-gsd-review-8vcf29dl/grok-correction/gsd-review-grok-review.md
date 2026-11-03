The C7-A03 citation is unsupported. I'll reread plan 10 and the executor commit/path rules before deciding whether that removes the no-gap verdict.
## Cycle 8 addendum

**Unresolved concerns: 0. Verdict unchanged.** Plans 01–09 stand as previously written. Only 06.6-10 and the cross-plan close relied on the false appendix; those two sections are corrected below and are not restated with the old claims.

`06.6-10-PLAN.md` is 319 lines. Its Round 7 ledger names only C7-A01 and C7-A02 (`06.6-10-PLAN.md:302-315`). There is no C7-A03 row, no `<sequential_execution>` block, and no forced-dispatch instruction. The prior review was wrong to say C7-A03 supersedes executor step 0b, and wrong to call shared-checkout sequential routing the matching rule.

### Cycle 7 adjudication

The decision holds. The reason does not need a waiver that is not in the plan.

Executor step 0b (`task_commit_protocol`, also the supplied executor lines 464–476) is worktree-only and runs before an Edit/Write whose absolute path is outside `WT_ROOT`. It is not waived. Plan 10 never asks for that waiver. Companion delivery is recorded-root resolution plus `git -C` and a private index: `06.6-10-PLAN.md:73-76`, `:80-81`, `:85-88`, `:104-114`, `:198`. Those are not Edit/Write calls, so 0b does not regulate them. `git -C` also keeps the executor cwd in core, which is what step 0a (#3097) requires.

`#4799` sets `SEQUENTIAL=true` only when the spawn prompt contains `<sequential_execution>`. Plan 10 has no such block. Lines 85–88 require the opposite accommodation: an isolated core worktree must use the recorded companion root, not a sibling inferred from that worktree. `wave: 4` and `depends_on: ["06.6-07"]` (`06.6-10-PLAN.md:5-6`) are ordering, not a dispatch mode. Adding sequential routing would be new text.

Authorization already in the plan is amended D-11/D-14 (`06.6-10-PLAN.md:44`, `:261`): deliver the tested companion delta and scoped local commits, preserving dirty settings. This prompt’s user authorization matches that text. It is not a Round 7 finding.

The generic “commit immediately” rule (supplied executor line 439) and the tracer rule “commit exactly like `type=auto`” do not create a missing permission. C5-A01 already forbids an early 10-01 commit and assigns the companion commit to 10-02 (`06.6-10-PLAN.md:93-98`, `:165-166`, `:168-169`). An early core or companion commit fails those criteria. That exception was already accepted under C5-A01; it does not depend on C7-A03.

If an executor ignores the patch/`git -C` instructions and Edit/Writes the absolute companion path, 0b halts. That is noncompliance with `06.6-10-PLAN.md:85-88` and `:104-114`, not a missing amendment. The halt is fail-closed. No new concern is opened.

## 06.6-10 (corrected)

**Summary.** The shared companion commit for 10-01/02 and the core-only 10-03 evidence commit are specified by C5-A01. Companion writes are recorded-root `git -C` operations under D-11/D-14. They do not need another authorization id or a sequential-dispatch flag.

**Strengths.**
- 10-01 must not be auto-committed (`06.6-10-PLAN.md:95`, `:165-166`). 10-02 commits the combined delta with `git -C "$COMPANION_ROOT"` and a temporary index (`:104-114`). 10-03 commits only the two core evidence files (`:97-98`, `:226-229`). Core `plan_head_before` counts core commits only (`:131-133`).
- `files_modified` uses `../tabler-test` as the supplied checkout’s relative spelling (`:7-13`, `:80-81`). An isolated worktree must resolve the recorded absolute `companion_root`, not a different sibling (`:85-88`). Delivery commands use `--delivered-source recorded` (`:73-76`, `:167`).
- Round 7 adds only C7-A01 and C7-A02 (`:302-315`). Empty still performs the real same-URL GET. The one node command unsets both interpreter variables (`:161-162`, `:167`).

**Concerns.** None unresolved. Publishing remains out of scope. `settings.py` preservation is a delivery check (`:22`, `:145`), not a new permission.

**Suggestions.** None. Do not add a C7-A03 waiver, a `<sequential_execution>` block, or a third commit.

**Risk Assessment.** MEDIUM until the recorded-root delivery commands run. The commit accounting itself is sound.

## Cross-plan (corrected)

C7-A01 and C7-A02 are incorporated. Empty and absent cancel destinations stay different activation paths, and the plans test that difference without changing `viewset.js`. The node commands unset both interpreter variables and reload the recorded runtime. Companion delivery is the C5-A01 `git -C` / temporary-index procedure, not a worktree Edit and not a sequential-dispatch exception.

No new executable planning gap. What remains is execution: baseline, browser, replay, delivery, and the human check. Those are already blocking in 06, 07, 09, and 10.

## 06.6-01 through 06.6-09 (unchanged)

**06.6-01.** The create-path diagnosis matches the source: page templates already own the outer form and token, while `cv_render_form` flattens context and the inner template reads `form.helper` twice. The shared 01-01/01-02 commit is a real executor exception, and it is the right one. `view_create.content.html:5-10` owns `<form class="cv-form">` and `{% csrf_token %}`; `tags/form.html:3-6` then calls `{% crispy form form.helper %}` twice, and `form.py:43-50` allocates a new `FormHelper` with the default `form_tag=True`. `crud_views.py:453-455` already shows the `context.push` / `template.template.render(context)` pattern; `:466` currently discards that with `context.flatten()`. `_CustomHelperForm` and `_DeleteCustomHelper` (`test_form_button_checks.py:560-585`) construct helpers without `form_tag=False`. Concerns: none unresolved. Risk: LOW.

**06.6-02.** The theme layer is a real insertion into a resolver that today jumps from a bad setting straight to the package table. `label_mode.py:23-25` is the immutable package floor. `default_label_mode` (`:86-119`) reads settings on every call. `_invalid_label_mode` (`:73-75`) resolves the fallback before taking `_warned_lock`. Concerns: none unresolved. Risk: LOW.

**06.6-03.** Independent group keys are justified by three separate constructors. Ordinary and delete groups are built at `form.py:55-56` and `:141-144`. The filter group is at `list.py:125-133`. `list.py:172-179` appends `_cv_actions` once per prepared layout. `button_classes.py:328-345` accepts only table keys, heading keys, or action-mode keys. `EXPECTED_KEYS` is 84. Concerns: none unresolved. Risk: LOW for the plan. MEDIUM only as unrun floor evidence, which 03-03 and 09 already refuse to waive.

**06.6-04.** The two alert literals are still hardcoded. `tags/alert.html:2` appends ` alert-dismissible fade show` only when dismissible; `:5` hardcodes `class="btn-close"` and `data-cv-alert-dismiss`. The template scanner at `test_button_classes_templates.py:23,51-57` only accepts quoted `cv_button_class` pairs that exist in `DEFAULT_BUTTON_CLASSES`. Concerns: none unresolved. Risk: LOW.

**06.6-05.** Workflow is the remaining direct crispy bypass. `view_workflow.action.html:8-15` owns a POST form and token, then calls `{% crispy form form.helper %}`. `WorkflowView` (`views.py:18-27`) inherits `crud_views/view_custom_form.content.html` from `form.py:19`. `cv_modal_supported` defaults false (`base.py:111`). The two parent overrides at `views_formset.py:44-50` and `examples/bootstrap5/formsets/views.py:36-41` only assign `form_tag=False`. Concerns: none unresolved. Risk: LOW.

**06.6-06.** Companion `apps.py:15-31` registers icons, button classes, and assets from `ready()`. `buttons.py:3-44` and `tests.py:99-139` are the same dictionary. `icons.py:12-47` has no `save`, `cancel`, or `filter-reset`. C7-A02 is real because each Bash call is a fresh shell. C7-A01’s two states are evidence requirements, not a product change. Concerns: none unresolved. Risk: MEDIUM only because 06-02 has not run.

**06.6-07.** `viewset.js:38-44` assigns `location.href` to the attribute value and has no empty-string special case. `button_data.py:354-357` keeps `""` but selects `button` because `""` is falsy. `form.html:3` emits `data-cv-cancel-url=""` when `cv_cancel_url is not None`. Absent/None omits the attribute. Companion `alert.html:7-17` hardcodes dismissal classes and `data-bs-dismiss="alert"`. Concerns: none unresolved. Risk: MEDIUM as unrun Chromium evidence.

**06.6-08.** After `form_tag=False` on the library helper, standalone `{% crispy form %}` loses the helper-owned wrapper and keeps the token. `buttons.md:151-156` is the live count sentence. Concerns: none unresolved. Risk: LOW.

**06.6-09.** `noxfile.py:22-24` and `:28-57` are the real floor pins and the one allowed deselect. C7-A01 and C7-A02 are final-check predicates. The Django 6.0 current-pack gap stays untested. Concerns: none unresolved. Risk: MEDIUM until the listed gates exist.
