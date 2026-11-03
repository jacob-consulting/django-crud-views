I'll verify each plan against the current source, starting with the ownership, label-mode, cancel, and class-table seams the plans claim to change.
The cancel-URL and executor-boundary claims need a direct source check before I treat the latest dispositions as closed.
## 06.6-01

**Summary.** The create-path diagnosis matches the source: page templates already own the outer form and token, while `cv_render_form` flattens context and the inner template reads `form.helper` twice. The shared 01-01/01-02 commit is a real executor exception, and it is the right one.

**Strengths.**
- `view_create.content.html:5-10` owns `<form class="cv-form">` and `{% csrf_token %}`; `tags/form.html:3-6` then calls `{% crispy form form.helper %}` twice, and `form.py:43-50` allocates a new `FormHelper` with the default `form_tag=True`.
- `crud_views.py:453-455` already shows the `context.push` / `template.template.render(context)` pattern the plan requires; `:466` currently discards that with `context.flatten()`.
- `_CustomHelperForm` and `_DeleteCustomHelper` (`test_form_button_checks.py:560-585`) construct helpers without `form_tag=False`, so the atomic fixture migration is necessary before plan 02.

**Concerns.** None unresolved. The helper-copy experiment is a bounded stop, not a silent contract change.

**Suggestions.** None. Do not restate the already-owned raw scanner or standalone-token distinction.

**Risk Assessment.** LOW. The mechanism is source-backed; remaining risk is execution of the helper experiment, which the plan already blocks on.

## 06.6-02

**Summary.** The theme layer is a real insertion into a resolver that today jumps from a bad setting straight to the package table. The planned setting-free fallback matches the existing lock order and does not need a new public API.

**Strengths.**
- `label_mode.py:23-25` is the immutable package floor `context=icon, list=icon, card=both, form=label`. `default_label_mode` (`:86-119`) reads settings on every call and falls back only to `LABEL_MODE_DEFAULTS`.
- `_invalid_label_mode` (`:73-75`) resolves the fallback before taking `_warned_lock`, so a theme-only fallback cannot deadlock even when the owner map and the setting are both malformed.
- W362/W292 stay downstream of `default_label_mode`; the plan correctly refuses to invent startup form construction.

**Concerns.** None unresolved. C3-A03's composed owner-then-setting case is an executable test of this existing order, not a new product rule.

**Suggestions.** None.

**Risk Assessment.** LOW.

## 06.6-03

**Summary.** Independent group keys are justified by three separate constructors, and the filter helper's cached action object is exactly why render-time resolution is mandatory. The floor bridge is correctly forbidden from guessing at custom templates.

**Strengths.**
- Ordinary and delete groups are built separately at `form.py:55-56` and `:141-144`. The filter group is a third constructor at `list.py:125-133`.
- `list.py:172-179` appends `_cv_actions` once per prepared layout. A class stored at construction time would ignore later `register_button_classes` / `override_settings` changes. The plan's render-time key lookup is the actual fix.
- `button_classes.py:328-345` accepts only table keys, heading keys, or action-mode keys. `form:actions` / `form:filter-actions` become valid only once added; mode suffixes stay invalid because `form` plus a non-kind is not an action key (`:251-266`).
- `EXPECTED_KEYS` is 84 (`test_button_classes.py:105`; `buttons.md:151`). 04 then 03 is the only order that keeps that guard green.

**Concerns.** None unresolved. The floor template's missing hidden-input branch is already separated from the filter regression.

**Suggestions.** None.

**Risk Assessment.** LOW for the plan. MEDIUM only as unrun floor evidence, which 03-03 and 09 already refuse to waive.

## 06.6-04

**Summary.** The two alert literals are still hardcoded, and the omission rule is necessary because a naive class substitution would change the default golden.

**Strengths.**
- `tags/alert.html:2` appends ` alert-dismissible fade show` only when dismissible; `:5` hardcodes `class="btn-close"` and `data-cv-alert-dismiss`.
- Empty dismissal must not leave the separator space, or a success alert would no longer be exactly `alert alert-success`. The plan pins that.
- The template scanner at `test_button_classes_templates.py:23,51-57` only accepts quoted `cv_button_class` pairs that exist in `DEFAULT_BUTTON_CLASSES`. Adding the keys in the same task as the leaf is required.

**Concerns.** None unresolved.

**Suggestions.** None.

**Risk Assessment.** LOW.

## 06.6-05

**Summary.** Workflow is the remaining direct crispy bypass, and the modal/full-page split matches the class hierarchy. Create/update modal support must stay off.

**Strengths.**
- `view_workflow.action.html:8-15` owns a POST form and token, then calls `{% crispy form form.helper %}` and loads `crispy_forms_tags` (`:2`). Replacing that call and dropping the unused load is the real D-16 fix.
- `WorkflowView` (`views.py:18-27`) does not override `cv_content_template`. It inherits `crud_views/view_custom_form.content.html` from `form.py:19`. Modal content includes that attribute (`modal/content.html:8`). The plan's refusal to retarget the modal body is correct.
- `cv_modal_supported` defaults false (`base.py:111`) and E251 rejects an unsupported opt-in (`:167-171`). Create/update do not override it.
- The two parent overrides at `views_formset.py:44-50` and `examples/bootstrap5/formsets/views.py:36-41` only assign `form_tag=False`. The four retained helpers still do the same and are correctly left alone.

**Concerns.** None unresolved. C2-A05's deferred helpers are real and still compatible.

**Suggestions.** None.

**Risk Assessment.** LOW.

## 06.6-06

**Summary.** The acquisition identity is settled. Fresh suite results are not. The latest runtime and cancel contracts are executable and match the installed executor's fresh-shell rule.

**Strengths.**
- Companion `apps.py:15-31` registers icons, button classes, and assets from `ready()`. There is no label-mode registration yet, so `form=both` is a real addition, not a restyle of an existing call.
- `buttons.py:3-44` and `tests.py:99-139` are the same dictionary. Four new pairs must land in both or `test_table_values` fails. The plan requires whole-dictionary equality.
- `icons.py:12-47` has no `save`, `cancel`, or `filter-reset`. The renderer at `:50-51` is separate behavior and stays counted.
- C7-A02 is real: each Bash call is a fresh shell, so a Python default cannot export `CV_THEME_PYTHON`. Recording `companion_python` plus `sys.prefix` and reloading it is the mechanism that makes later commands work.
- C7-A01's two states are distinguished here as evidence requirements, not as a product change.

**Concerns.** None unresolved. xdist absence remains a preflight halt, already stated. Unrun baseline is execution evidence, not a missing plan step.

**Suggestions.** None. Do not add a serial fallback.

**Risk Assessment.** MEDIUM only because 06-02 has not run. The plan already blocks 07/09 on that result.

## 06.6-07

**Summary.** The browser contract now describes the cancel handler that actually ships, including the empty-attribute navigation that a preservation assertion would have gotten wrong. The five fresh-shell commands are present.

**Strengths.**
- `viewset.js:38-44` matches `[data-cv-cancel-url]` and assigns `location.href` to the attribute value. It has no empty-string special case. Phase 6.1 D-17 is therefore preserved by not editing this file.
- `button_data.py:354-357` keeps `""` as the destination but selects `button` because `""` is falsy. `form.html:3` emits `data-cv-cancel-url=""` when `cv_cancel_url is not None`. `test_crispy_buttons.py:2110` already locks that attribute.
- Absent/None omits the attribute, so the handler does not run and the edited input stays. Explicit empty assigns `""`, which is a same-document GET. The plan's split, including no interception, matches that code.
- Companion `alert.html:7-17` hardcodes dismissal classes and `data-bs-dismiss="alert"`. `page.html:16` loads `{% cv_js %}`, so the CRUD copy must move to `data-cv-alert-dismiss` while `tests.py:556-572` cannot keep treating the two includes as identical. The named one-attribute parity delta is the correct fix.
- The five browser/config commands in 07-01, 07-02, and 10-01 all `env -u` both interpreter variables. That is the C7-A02 set.

**Concerns.** None unresolved. Glyph path data was not in the embedded excerpts; the plan already requires comparing rendered SVG bytes to the native definition, so a missing glyph fails closed.

**Suggestions.** None.

**Risk Assessment.** MEDIUM as unrun Chromium evidence. The plan does not treat a partial `owned-form` report as acceptance.

## 06.6-08

**Summary.** The documentation plan follows the code boundary instead of promising that every standalone crispy render stays unchanged.

**Strengths.**
- After `form_tag=False` on the library helper, standalone `{% crispy form %}` loses the helper-owned wrapper and keeps the token, because CSRF suppression is local to `cv_render_form`. The caller-owned wrapper recipe is the matching migration.
- `buttons.md:151-156` is the live count sentence. 08 correctly leaves the 84-to-88 inventory to the producing tasks.
- The retained tutorial helpers are still valid `get_form_actions` replacements. Removing that prose would be a false migration.

**Concerns.** None unresolved.

**Suggestions.** None.

**Risk Assessment.** LOW.

## 06.6-09

**Summary.** Final acceptance is gated on source-bound evidence, including both cancel activation states and the recorded companion runtime. It does not certify Phase 7 stability, and it should not.

**Strengths.**
- `noxfile.py:22-24` and `:28-57` are the real floor pins and the one allowed deselect. Adding the new theme modules to `CRISPY_FLOOR_TESTS` is a substantive gate, not a count.
- C7-A01 and C7-A02 are both final-check predicates: conflated empty/absent navigation fails, and a core-runtime fallback cannot satisfy companion evidence.
- The Django 6.0 current-pack gap is recorded as untested rather than filled by the 6.0 floor session. That matches the installed matrix (`noxfile.py:3`).

**Concerns.** None unresolved. Pending human observation is an explicit acceptance blocker, not a missing automated step.

**Suggestions.** None.

**Risk Assessment.** MEDIUM until the listed gates exist. The plan already fails closed.

## 06.6-10

**Summary.** The shared companion commit for 10-01/02 and the core-only 10-03 evidence commit match the installed executor contract. Companion source delivery is not a core task commit, and C7-A03 authorizes the out-of-tree write without another plan edit.

**Strengths.**
- The executor commits only the task it stages. 10-01 is a tracer whose plan forbids an early commit; 10-02 is the companion commit via `git -C` and a temporary index; 10-03 stages only `10-companion-delivery.json` and `07-TABLER-HANDOFF.md`. Core `plan_head_before` therefore counts one core evidence commit. That is the contract, not a missing per-task core commit.
- `files_modified` names `../tabler-test/...`, outside a core worktree. C7-A03 supersedes step 0b for that verified root. Plan 10 already binds writes to the recorded absolute `companion_root`, forbids an inferred sibling, and preserves unrelated index entries. Restating `#3099` would be duplicative.
- Shared-checkout sequential routing is the matching execution rule: wave 4 runs after 07, and companion edits are not worktree-isolated. The port rule in 07-01 is the same pattern for the shared 8145 listener.
- C7-A01 remains a delivered/committed evidence gate. Empty still performs the real `location.href = ""` GET. C7-A02's one node command unsets both variables and reloads `companion_python`.

**Concerns.** None unresolved. Publishing remains out of scope. Unrelated `settings.py` preservation is a delivery check, not a new permission.

**Suggestions.** None. Do not add a forced isolation flag or a third commit.

**Risk Assessment.** MEDIUM until the recorded-root delivery commands run. The commit accounting itself is sound.

## Cross-plan

C7-A01, C7-A02, and C7-A03 are incorporated. Empty and absent cancel destinations are different activation paths in current code, and the plans now test that difference without changing `viewset.js`. The five node commands cannot inherit a dead shell variable. Companion writes are an authorized shared-checkout exception, not a worktree violation.

No new executable planning gap. What remains is execution: baseline, browser, replay, delivery, and the human check. Those are already blocking in 06, 07, 09, and 10.
