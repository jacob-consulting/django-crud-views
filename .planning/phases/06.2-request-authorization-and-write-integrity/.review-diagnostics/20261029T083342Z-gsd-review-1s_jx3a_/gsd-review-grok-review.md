I'll verify each plan against the current delete, Guardian, and formset code before scoring the claims.
## 06.2-01

The delete bypass and the protected-label leak are real, and the plan aims at the right methods. The stock notice still will not survive an all-hidden protected-only preview, because the include that actually renders it is outside the files this plan may change.

**Strengths**
- HTTP DELETE is not handled by `DeleteView.post()`. `DeletionMixin.delete()` loads the object and deletes it with no form, protection, or hook path. Restricting methods on `DeleteView` covers `DeleteViewPermissionRequired`, `GuardianDeleteViewPermissionRequired`, and `PolymorphicDeleteView` by inheritance, and mixin `dispatch` still runs before `View.dispatch`, so login and parent gates stay first.
- `cv_filter_related_objects` keeps `protected` unfiltered at `delete.py:172`, and the Guardian override does the same at `views.py:42-49`, including the empty-tree return. Capturing blocked state before that filter matches the template, which today keys the alert off `protected_objects` truthiness (`related_objects.html:4-5`).
- POST integrity is already in `CrudViewProcessFormMixin.cv_form_valid_process` (`mixins.py:48-57`). Task 01-03 correctly pins it instead of rewriting it.

**Concerns**
- HIGH: A protected-only collection never reaches the snippet the plan edits. `NestedObjects.collect` records PROTECT targets only in `self.protected`, not in `collector.data`, so `related.summary` is empty. `view_delete.content.html:8-9` includes the snippet only when `related_summary or protected_objects`. After labels are removed, that condition is false, `has_protected_objects` is never read, and the generic notice is absent. That file is not in `files_modified`.
- MEDIUM: Task 01-01 can be read as a second model-level filter in `get_context_data` after `cv_filter_related_objects`. Guardian object grants do not imply `view_<model>`. A post-hook pass would hide labels the Guardian filter had correctly kept.
- MEDIUM: `http_method_names` does not close `DeletionMixin.delete()`. A subclass that puts `"delete"` back selects the direct-delete lifecycle the must-have forbids. Research asked to close that method.
- MEDIUM: `test_guardian_delete.py:45-50` and `:73`, and `test_delete.py:153`, lock the leak (empty-tree identity, unfiltered `protected`, `len(protected_objects) > 0` for a delete-only user). The plan never says to replace those assertions.

**Suggestions**
- Add `view_delete.content.html` and gate the include on `has_protected_objects`, not the filtered list.
- Filter only inside each `cv_filter_related_objects`. `get_context_data` should store the boolean, then assign the hook’s `protected`.
- Override `delete()` to return 405 as well as dropping the method name.
- Rewrite the three characterization assertions above as part of the red test, not as behavior to preserve.

**Risk Assessment:** HIGH. The 405 change is sound, but the stated notice mechanism cannot render for the protected-only case the requirement calls out.

## 06.2-02

Parent-`None` and inactive-user defects match the code. The plan names the right helpers, but inactive denial has to sit on `dispatch`, or fragment and parent-`None` requests still skip it.

**Strengths**
- `_guardian_check_parent` returns before `get_object_or_404` and before `cv_action_enabled` when the key is `None` (`mixins.py:232-244`). That is the B4/B6 bug, and the docs at `guardian.md:177-179` already say `None` only skips the permission check.
- Both create helpers build `perm` with `or` and then call `perm.split` (`views.py:146-155`, `195-204`). `None` crashes. A shared resolver that skips only the permission call is the right unification.
- No Guardian path checks `is_active`. `has_permission` returns `True` for any authenticated user (`mixins.py:31-38`, `98-105`), and `get_objects_for_user` is called with superuser privileges still on (`viewset.py:67-72`). `AllowAllUsersModelBackend` plus `force_login` is the right test, because the default backend would hide it.
- URL parent binding already comes from the URL in `CreateViewParentMixin` (`create.py:49-67`), so a forged FK test has a real control.

**Concerns**
- MEDIUM: Child `has_permission` returns `True` without calling the object mixin (`mixins.py:191-193`). Fragment GET returns before `get_object` (`formsets/mixins.py:37-44`). An `is_active` check only in `get_object` does not cover those paths. Task 02-02 also asks for fragment denial before plan 03 owns fragment authorization, so a literal fragment assertion can stall wave 2.
- MEDIUM: The inactive check must run after the anonymous branch (`mixins.py:197-198`) and before the `perm_key is None` return (`mixins.py:233`). The reverse order turns anonymous users into 403s, or leaves parent-`None` creates open to inactive users.
- LOW: `cv_has_access` returns `True` for a wrong-type object (`views.py:206`), and the docstring calls that intentional (`views.py:181-183`). Failing closed is safer, but it is not what D-10 locked.

**Suggestions**
- Put inactive denial in `GuardianParentPermissionMixin.dispatch` and both `has_permission` overrides, then in the callable helpers and `_PermittedPks`. Do not rely on `get_object`.
- Keep 02’s fragment cases to “dispatch already denied”; leave choice-disclosure proof to 03.
- Preserve the wrong-type helper fallback unless a test shows a caller depends on it.

**Risk Assessment:** MEDIUM. The defects and the resolver are correctly identified. Status-code and fragment coverage depend on putting the inactive gate on `dispatch`, which the action only implies.

## 06.2-03

The fragment hole is exactly `FormSetMixinBase.get` returning before Guardian `get_object`. Authorization-before-render is the right fix. The coordinate validator is underspecified against the prefix grammar the client already uses, and the UUID fixture the plan wants does not exist.

**Strengths**
- `get()` serves `?template=` before `super().get()` (`formsets/mixins.py:37-44`). Guardian object and state checks live only in `get_object` (`mixins.py:50-58`). Core permission views already call `get_object` from `has_permission` (`base.py:900-910`); the hole is the Guardian composition the tracer names.
- Child querysets already filter on the URL parent (`viewset/__init__.py:292-306`), so calling `get_object()` also 404s a child under the wrong parent. That matches “keep object-lookup semantics.”
- `pk="None"` is the live unsaved sentinel (`formset.js:320`, `formsets/mixins.py:50`). Rejecting only forged persisted ancestry, not new nonnegative `num`s, matches `num.isdigit()` (`mixins.py:54-55`) and client-added rows.
- Polymorphic formset lookup uses `polymorphic_model`, which reads the URL ctype or `get_object()` (`utils.py:38-45`). Setting `self.object` on object views and leaving create as `None` is the right split.

**Concerns**
- MEDIUM: The client already parses prefixes with `FormSet.PK` (`formsets.py:27-29`, `formset.js:155`: `^(.*)(None|<pk pattern>)-(\d+)$`). The plan never cites that grammar. A hyphen split, or `pk == self.object.pk` on every request, rejects legitimate UUID prefixes and create fragments whose `self.object` is `None`.
- MEDIUM: There is no UUID inline. `Author.id` is a UUID (`models.py:13-14`); formset fixtures are int `Publisher`/`Book`/`BookNote` (`views_formset.py:64-74`). “No production schema change” leaves no persisted UUID chain to parse. A test-only model is not in `INSTALLED_APPS`.
- MEDIUM: `ViewSet.register` inserts into the process-global `_REGISTRY` (`viewset/__init__.py:146-151`). Existing tests pop names (`test_viewset.py:64`). This plan does not. A detail view for `Publisher` left registered can change `cv_get_related_object_url` (`delete.py:102-112`) for later plans in the same process.
- LOW: `get_template` does not load `pk` (`formsets.py:192-193`). Forged coordinates change the prefix, not the choice queryset. Authorization is what stops `SECRET-CONTRACT-TITLE`. Coordinate checks are still required, but they are not the disclosure control.

**Suggestions**
- Parse with the existing `FormSet.PK` regex, special-case the `"None"` sentinel before `to_python`, and compare a top-level persisted `pk` to the endpoint only on object views.
- Drive the UUID case with `FormSet.PK.UUID` and a prefix string if no child model exists. Do not add a model to pass one test.
- `try/finally` `_REGISTRY.pop` the probe viewset, following `test_viewset.py:64`.

**Risk Assessment:** MEDIUM. The authorization insertion is sound. A validator that does not match `formset.js:155` will break authorized nested adds, which is the compatibility half of AUTH-02.

## 06.2-04

Removing the inert ViewSet flag and showing per-view policy matches the code. The before-validator is the correct Pydantic hook. Manage rendering can ride the existing views table if the new fields distinguish “not applicable” from “strict.”

**Strengths**
- Runtime reads the view attribute (`mixins.py:28`, `43`, `95`, `168`). The ViewSet field is only stored (`viewset.py:23`) and copied into manage context (`views.py:231`, `config_table.html:16-17`). Removing it is the right break.
- `ViewSet` sets no `model_config`, so Pydantic’s default `extra='ignore'` drops an unknown keyword. A `mode='before'` validator sees that key before it is discarded. A field validator on a removed field would never run.
- `get_view_data` already adds `guardian_mixin` (`views.py:270-275`), and `view_manage.html:118-133` prints every key. Per-view policy does not need a new page. `test_guardian.py:644-645` asserts the old ViewSet flag; task 04-02 correctly includes that file.
- `get_objects_for_user` already passes `accept_global_perms=False` (`viewset.py:71`). Keeping that, and not inheriting the view flag, matches D-03 and D-05.

**Concerns**
- MEDIUM: `getattr(view, "cv_guardian_accept_global_perms", False)` is the wrong display for top-level create. Create does not use the object mixin; the flag matters for child parent fallback (`views.py:150-151`, `mixins.py:224`). Showing `False` there reads as a strict object policy the view does not apply. The action warns about this and then leaves the applicability rule unspecified.
- LOW: The before-validator covers constructor input only. A subclass that redeclares the field, or a post-init assignment, is inert again. That is not the documented configuration path.
- LOW: The plan’s own “unclassified edge” note is still open. Constructor, mixed-view, helper, and manage-gate tests do not define what that probe failed to classify, so AUTH-06 can be marked done with an unknown edge still open.

**Suggestions**
- Emit three states per view: object/queryset fallback, parent-only fallback, or not applicable. Put the strict helper only in `guardian_config`, not as a copy of any view’s flag.
- Name the removed key and the view-class attribute in the `ValidationError`. Do not set `extra='forbid'`.
- Record the unclassified probe’s input in `06.2-ACCEPTANCE.md` instead of closing it by assertion count.

**Risk Assessment:** MEDIUM. Removal and the strict helper are safe. A boolean dumped for every registered view would make manage lie, which is the failure D-06 exists to prevent.

## 06.2-05

This plan is the phase’s proof that enforcement is not a hidden button. It is test-only and correctly ordered after the fixes, but the matrix has no expected outcome per cell, and the red-then-green instruction does not apply.

**Strengths**
- Direct requests are the right oracle. Guardian `has_permission` admits authenticated users (`mixins.py:38`), so a hidden control does not prove denial.
- The locmem pattern exists (`test_crispy_buttons.py:356-364`): deepcopy `TEMPLATES`, `APP_DIRS=False`, locmem first. Requiring an override sentinel avoids a pass that never loaded the override.
- Running `test_conditional_formset.py` preserves purge behavior (`test_conditional_formset.py:35-60`, `104`) without reopening that lifecycle. The crispy-floor deselect matches `noxfile.py:57`.
- Context-plus-HTML assertions are necessary. `alert_data` escapes items (`messages.py:42`), so HTML alone cannot prove a denied model never entered context.

**Concerns**
- MEDIUM: “Match their effective policy” is not a matrix. Anonymous redirect/403/404, inactive 403, missing-object 404, and DELETE 405 are different codes. Without a cell table, a partial matrix still satisfies the wording.
- MEDIUM: Acceptance says the new tests must fail against old behavior. This wave runs after 01–04, and this plan changes no production code. There is nothing to turn red except by reverting earlier waves.
- LOW: Native list/card/action/manage/alert/formset seams are named, but not the template paths. A list override that does not render `object_list` can pass a sentinel check and miss a leaked row.

**Suggestions**
- Add a table: actor × route × expected status × storage unchanged or not. Include DELETE 405, parent-`None` disabled POST, and inactive list context empty.
- Drop the red-before-fix line for this plan. These tests are confirmation.
- Point each seam at the stock template it replaces, and assert a denied label is absent from `response.context`.

**Risk Assessment:** MEDIUM. It can prove AUTH-07 if the matrix is written tightly. As specified, it can also pass while missing the cells the source note actually broke.

## 06.2-06

Documentation and the supported-version run belong last, and the Breaking/migration pairing matches the repo rule. The automated verify does not check that the docs describe the code, and the full crispy-floor suite is a broader claim than the cached envs have shown.

**Strengths**
- The public contracts to update are the ones readers use: `guardian.md:86-98` and `:239-247` still describe one global flag; `formsets.md:139-146` still says the fragment GET skips normal GET; delete docs need `has_protected_objects`.
- Pairing every `### Breaking` entry with `docs/migrating-1.0.md` matches `CLAUDE.md`. HTTP DELETE removal, the constructor key, and the preview/manage context are the three breaks.
- The verify interpreter is the cached floor (`noxfile.py:96-106`). Saying Django 5.2 and other Python versions were not run is the correct limit. Keeping `test_filter_form_controls_match_golden` while deselecting only `test_filter_form_baseline` matches the floor note.

**Concerns**
- MEDIUM: Task verify is `.venv/bin/mkdocs build --strict` for 06-01 and 06-02. Strict mode catches broken links, not a missing Breaking heading or a doc that still says the ViewSet flag works. The acceptance line “new regressions must fail against the old behavior” is copied onto a docs task and cannot be executed.
- MEDIUM: 06-03’s automated command is only the Django 6.0 file list. The 4.2 rerun and full `tests/test1` live in prose. Only crispy-floor envs exist under `.nox/`. Full `tests/test1` on crispy-bootstrap5 2023.10 is not what that nox session runs (`noxfile.py:106` is the form-button list). An unrelated floor failure can block the phase, or be misrecorded as an AUTH failure.
- LOW: Phase 7 handoff depends on 01’s context names. If the include gate was not fixed, the inventory will freeze a notice contract the stock template does not implement.

**Suggestions**
- Add a grep or doc test that `CHANGELOG.md` and `docs/migrating-1.0.md` both mention HTTP DELETE 405, the removed ViewSet key, and `has_protected_objects`.
- Put the Django 4.2 command in the task `verify` block, not only in the plan footer.
- Record floor-only failures as environment limits. Do not treat a crispy wrapper mismatch as an authorization regression.

**Risk Assessment:** MEDIUM. The doc list is right. The sign-off command does not prove the docs match the implementation, and the full-suite claim is wider than the cached floor session.

## Cross-plan

- The notice contract is split across 01, 05, and 06, but the include that decides whether it renders is in none of them (`view_delete.content.html:8-9`). 05 can assert context while stock HTML still omits the alert. 06 would then document a contract the template does not keep.
- 02 and 03 overlap on fragment denial. Inactive denial belongs in `dispatch` in 02. Choice disclosure belongs in 03, after `get_object`. Putting fragment choice tests in 02 blocks wave 2 on wave 3.
- 03 and 04 are parallel and do not share files. 03’s global `_REGISTRY` insert is visible to 04 and to 06 if the probe viewset is not removed.
- 01 must not model-level-filter after Guardian’s `cv_filter_related_objects`. 02’s `_PermittedPks` inactive short-circuit belongs inside that same hook, not a second pass.
- Wave order 01 → 02 → (03 ∥ 04) → 05 → 06 matches the code dependencies. The copied “fail against old behavior” line does not. It fits 01–04 only.

## Overall risk

MEDIUM, with one HIGH hole in 06.2-01. The phase goals are achievable if the include gate, `dispatch`-level inactive denial, and the existing prefix grammar are added before execution. Without the include-gate change, AUTH-03’s “notice survives when every label is hidden” is false for a protected-only delete.
