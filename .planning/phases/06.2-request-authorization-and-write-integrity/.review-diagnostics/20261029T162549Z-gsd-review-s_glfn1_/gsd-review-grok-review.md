I'll verify each plan against the current source, starting with the delete, Guardian, and formset paths the plans depend on.
The delete and Guardian preview paths match the gap descriptions. Next I’ll check guardian’s lookup, the templates, and the tests the pending plans rewrite.
Guardian’s lookup matches the diagnosis. I’ll check the cascade fixtures and the write-path assumptions plan 08 depends on.
Verified the pending plans against `delete.py`, the Guardian lookup, guardian 3.5.2’s `get_objects_for_user`, and the templates and pins those plans rewrite. Plans 01–06 match the code they already shipped; the open defects are the ones 07–09 own.

## 06.2-01

**Summary:** Executed as written. The method guard and the filtered preview are in the tree; the ProtectedError 500 and the always-on form are the deliberate deferral that 08 now has to reverse, not a missed mechanism.

**Strengths:**
- `_DeleteMethodGuardMixin` sits after `CrudView` and before `generic.DeleteView` (`delete.py:37-48`). `dispatch` rejects `DELETE` before handler selection; `_allowed_methods` strips `DELETE` from both 405 `Allow` and `OPTIONS`. `DeletionMixin.delete` is not overridden, so the Django 4.2 warning stays avoided.
- `has_protected_objects` is taken from the unfiltered collector before `cv_filter_related_objects` (`delete.py:202-206`). The outer include is `related_summary or has_protected_objects` (`view_delete.content.html:8-9`), so an all-hidden preview still shows the notice.

**Concerns:**
- **Historical, owned by 08.** `post()` only honors `delete_protection_errors` (`delete.py:231-240`), then `cv_form_valid` calls `self.object.delete()` (`delete.py:247`). `test_database_protect_post_raises_and_keeps_storage` (`test_delete.py:246-257`) pins the 500. The form is outside that branch (`view_delete.content.html:12-18`). This contradicts D-08’s “must not look deletable,” which the plan’s ledger explicitly deferred.
- **Historical, owned by 07.** `_PermittedPks` still builds `f"{opts.app_label}.view_{opts.model_name}"` (`views.py:74-76`). That is the CR-01 crash, extended to `related.protected` by this plan.

**Suggestions:** None for this plan. Do not reopen the guard or the filter boundary while closing the gaps.

**Risk Assessment:** LOW as an executed plan. Residual risk is entirely in 07 and 08.

## 06.2-02

**Summary:** Executed. Parent resolution, FK own-child normalization, and inactive denial match the locked decisions. No change required from the gap plans.

**Strengths:**
- `_cv_guardian_create_parent` accepts a parent instance, resolves a single FK via `ParentViewSet.get_attribute()`, and returns `None` for M2M own-children and unrelated objects (`views.py:139-160`). State goes through `_cv_action_enabled_for_context` and does not call the hook when the parent is unresolved (`views.py:162-171`).
- `_guardian_inactive_actor` is authenticated-and-inactive, not anonymous (`mixins.py:10-17`), and `_PermittedPks` returns before the guardian call (`views.py:69-70`).

**Concerns:**
- **Historical, not a 07–09 defect.** `GuardianQuerysetMixin.get_queryset` and `GuardianViewSet.get_objects_for_user` still pass the ViewSet’s app-qualified permission (`mixins.py:188-195`, `viewset.py:102-108`). That is the `MixedContentTypeError` carry-forward 09 records, not something 07’s preview fix should absorb.

**Suggestions:** Leave the M2M object-only fail-closed boundary alone. 09 already has to keep it out of the new delete docs.

**Risk Assessment:** LOW.

## 06.2-03

**Summary:** Executed. Fragment GET loads the object through cooperative `get_object()` before rendering, which is the authorization gate this plan claimed.

**Strengths:**
- `FormSetMixinBase.get` sets `self.object` via `get_object()` for object views before `get_template_html` (`mixins.py:47-51`). Coordinate validation runs before `get_template` (`mixins.py:71-78`).

**Concerns:**
- **Historical, deferred.** The non-first child emitted-index mismatch stays a proposed-6.3 item. 07–09 must not “fix” it while touching formset-adjacent tests.

**Suggestions:** None.

**Risk Assessment:** LOW.

## 06.2-04

**Summary:** Executed. The removed ViewSet key fails construction, and the helper stays strict. Manage policy display is outside these gap plans.

**Strengths:**
- `GuardianViewSet` has a before-validator path and `STRICT_HELPER_POLICY` with `accept_global_perms=False` (`viewset.py:9-18`, `102-108`). Failed construction is specified not to register a ViewSet.

**Concerns:** None that 07–09 need to reopen. The AUTH-06 unclassified probe stays flagged; 09 correctly does not mark it resolved.

**Suggestions:** None.

**Risk Assessment:** LOW.

## 06.2-05

**Summary:** Executed replay. Its matrix still encodes the old database-PROTECT contract, which 08 must rewrite in place rather than add a second cell beside.

**Strengths:**
- `MxDelete` is a real registered delete view with `cv_modal = True` and a hook counter (`test_authorization_matrix.py:151-162`). The protect cell uses a real `Contract` and `pytest.raises(ProtectedError)` (`test_authorization_matrix.py:727-738`).

**Concerns:**
- **Actionable only as an input to 08.** The cell posts `{"confirm": "on"}` with no modal header. After 08, that same request is a 200, not an exception. 08’s rewrite has to add the header request itself; the old cell does not already cover 422.
- **Historical.** The matrix table’s “Granted database-PROTECT confirmed delete POST → ProtectedError” row is now a stale plan claim. 08 supersedes it.

**Suggestions:** When 08 rewrites the cell, keep `_set_policy`, `_granted_actor`, `_snapshot`, and `_assert_no_write`. Add an explicit `headers=MODAL` post. Do not assume `{"confirm": True}` and `{"confirm": "on"}` are the only difference; both are valid for `BooleanField` (`form.py:123`), but the existing cell uses `"on"`.

**Risk Assessment:** LOW for the executed replay. MEDIUM if 08’s matrix rewrite drifts from this fixture.

## 06.2-06

**Summary:** Executed documentation of the then-current contract. It correctly paired the preview-filter Breaking entry, and it also froze the 500 into the public docs. 09 has to amend that text, not treat it as still true.

**Strengths:**
- `delete_view.md:179-187` and the execution list at `272-284` match today’s code: flag only with `cv_show_related_objects`, POST raises `ProtectedError`. `theme.md:345-347` copies the colon heading. ACCEPTANCE line 116 and the open item at line 230 name the same tests 08 will replace.

**Concerns:**
- **Historical, owned by 09.** Those paragraphs are now the contract drift 09 must delete. A gap closure that updates code and not these lines would leave Phase 7 freezing the 500.

**Suggestions:** 09 should edit the cited paragraphs in place. The line numbers still match.

**Risk Assessment:** LOW as history. The doc drift is 09’s job.

## 06.2-07

**Summary:** The diagnosis matches the code. `_PermittedPks.__call__` (`views.py:68-78`) passes an app-qualified string into `get_objects_for_user`, and guardian 3.5.2 resolves that string in `_get_ct_cached` (`shortcuts.py:47-50`, `527-537`) before the superuser short-circuit (`shortcuts.py:671-680`). A bare codename with `klass=` skips that lookup (`shortcuts.py:533-535`, `551-553`). The auto-created short-circuit is justified: `get_content_type` is `get_for_model` (`ctypes.py:15-28`), which inserts a row. This plan should close G-06.2-1.

**Strengths:**
- Route coverage uses the real cascade view (`views.py:769-772`, `cv_show_related_objects = True`) and the existing `/guardian_publisher_cascade/{pk}/delete/` helper (`test_guardian_delete.py:153-154`).
- `Royalty` is the right protected-list fixture: `Contract` has a `view_` row, so it cannot reproduce `ContentType.DoesNotExist`. The test app has no migrations directory, and the DB is in-memory (`conftest.py:91-95`), so a new model is created by syncdb.
- Existing `test_guardian_protected_global_permission_follows_view_fallback` (`test_guardian_delete.py:257-277`) stays in the 07-01 command, so a bare-codename change that drops global fallback fails the suite.
- Rejecting the review’s `Permission.objects.filter` precheck is right: that shape still raises `MixedContentTypeError` when `GUARDIAN_GET_CONTENT_TYPE` is the polymorphic base.

**Concerns:**
- **MEDIUM:** 07-02’s proxy and polymorphic cases are the version-sensitive modes, and its verify command runs only Django 6.0. 07-01 runs 4.2, but only the M2M/Royalty routes. A 4.2 `get_for_model` or polymorphic content-type difference would not be seen until 09-03.
- **LOW:** Duplicate-codename is untested on purpose (`Permission.objects.get(codename="view_contract")` at `test_delete.py:223` would break). The bare-codename path does skip `_get_ct_cached`, so the claim is structurally true, but it is not a regression.
- **LOW:** The superuser `auto_created` branch materializes every through-table pk via `_default_manager`, not the pks in the cascade. That matches guardian’s superuser queryset, and it is a full scan on every superuser preview of an M2M root.

**Suggestions:**
- Run the 07-02 module on the cached 4.2 interpreter as well, or state that 09-03 is the 4.2 gate for proxy/polymorphic and do not call 07 done on 6.0 alone.
- In the through-table test, assert on `ContentType.objects.filter(...).exists()` before and after, as written. Do not call `get_for_model` in the assertion helper.
- Keep the inactive return first. An `auto_created` branch above it would let an inactive superuser see through-rows, which D-11 forbids.

**Risk Assessment:** MEDIUM. The fix shape is right; the gap is evidence on 4.2 for the non-route modes, not the mechanism.

## 06.2-08

**Summary:** The three defects are real and colocated. The flag exists only inside `if self.cv_show_related_objects` (`delete.py:202-205`). The form is unconditional (`view_delete.content.html:12-18`). `post()` never reads the flag (`delete.py:224-244`). `related_objects.html:5` always passes the colon heading and `items=protected_objects`, and `alert_data` picks the text body when `items` is empty (`messages.py:42-44`), which is the dangling colon. Modal GET/POST includes the same content template (`modal/content.html:7`). Core, Guardian, and polymorphic share this `post()`. The plan’s shape matches that structure.

**Strengths:**
- Computing the flag from `cv_get_related_objects()` on every delete GET/POST, while leaving `protected_objects` behind `cv_show_related_objects`, keeps the unfiltered collection out of context. A missing `protected_objects` is falsy in the template, so the plain route still gets the generic sentence.
- Wrapping `cv_form_valid_process` is the right backstop site. That method is the `with self.cv_get_atomic()` boundary (`mixins.py:48-57`). `ProtectedError` and `RestrictedError` are both importable from `django.db.models` on 4.2 and 6.0, and `NestedObjects` puts both on `.protected`.
- The three `pytest.raises(ProtectedError)` pins are exactly `test_delete.py:246`, `test_guardian_delete.py:315`, and `test_authorization_matrix.py:737`. No other test expects the exception.
- `Royalty` depending on 07 is the correct RESTRICT fixture. `Contract` cannot raise `RestrictedError`.

**Concerns:**
- **MEDIUM:** The action says the atomic block “has already exited” when these exceptions are raised. It has not. `self.object.delete()` runs inside `cv_get_atomic()` (`mixins.py:54-55`, `delete.py:247`). Catching inside that `with` marks the transaction broken and the following render can raise `TransactionManagementError`. The exceptions are raised by the collector before DELETE SQL, but they still propagate from inside the block. The `try` must stay around the `cv_form_valid_process` call in `post()`, not inside the `with`.
- **MEDIUM:** Every delete GET/POST will call `cv_get_related_objects()`, which uses `router.db_for_write` (`delete.py:105-107`). Today that alias is touched only when `cv_show_related_objects` is true. The default confirmation page starts hitting the write database. T-06.2-17 accepts the extra collector pass and does not mention the alias.
- **LOW:** `{% if not has_protected_objects %}` also drops the cancel control, because cancel lives in the form (`form.py:141-144`). That matches the custom-protection page, but a copied template that only has cancel inside `<form>` loses the way back. 09 should say so.
- **LOW:** `BLOCKED_HEADING = "Deletion is blocked by protected relationships"` is a prefix of the colon msgid (`django.po:225`). `assert BLOCKED_HEADING in content` passes for both copies. The hidden-case test must assert the colon heading is absent, not only that the prefix is present.
- **LOW:** The blocked return is inside the valid-form branch. An invalid confirm still goes through `cv_form_invalid`. The template then omits the form, so the user never sees the validation error. That is acceptable, but the spy on `cv_form_valid_hook` does not cover this branch.

**Suggestions:**
- Write the `except` only around `self.cv_form_valid_process(context)` in `DeleteView.post`. On catch, set `has_protected_objects` on the existing context and re-render that dict. Do not call `get_context_data` again: the 08-02 backstop monkeypatches `cv_get_related_objects` to return an empty `protected` list, and a second collect would clear the flag the test asserts.
- Assert `":" not in the heading element` for the hidden case, or compare against `BLOCKED_LIST_HEADING` and require it absent.
- In the matrix rewrite, send one post without `MODAL` (200) and one with `headers=MODAL` (422). `MxDelete.cv_modal = True` does not make a header-less post a modal request (`base.py:57-59`).

**Risk Assessment:** MEDIUM. The product shape is locked and the pins are complete. The implementation hazard is catching the exception inside `atomic()`, which the plan’s wording invites.

## 06.2-09

**Summary:** The doc targets are still where the plan says they are. `delete_view.md:174-187` and `280-284`, `theme.md:345-347`, and `guardian.md:281-313` describe the pre-gap contract. ACCEPTANCE line 230 is the open item to remove. The disposition file has 8 open findings (`06.2-REVIEW-DISPOSITION.md:38`); marking CR-01 and WR-02 fixed leaves 6. The Breaking/migration pair is required: the 500 is documented behavior, not an unreleased accident.

**Strengths:**
- Scoped edits, not a rewrite of ACCEPTANCE. The evidence row at line 116 names the three tests 08 replaces.
- The MixedContentTypeError carry-forward cites the two call sites that still pass app-qualified permissions (`mixins.py:188-195`, `viewset.py:102-108`). Those are outside `_PermittedPks` and should stay open.
- `mkdocs --strict` plus the `#blocked-deletions` anchor is a real pairing check. The section intro at `migrating-1.0.md:339-344` does not enumerate subsections, so “extend it if it does” is a no-op unless the executor adds a list.
- 09-03 reuses the 06-03 loop and compares against 6311 collected. That is the right gate after both code plans.

**Concerns:**
- **MEDIUM:** The acceptance line “no longer describe a POST that raises” fights the required backstop paragraph, which must say a `ProtectedError` or `RestrictedError` raised inside the write is caught. An executor can “satisfy” the sentence by deleting the exception names, and the `RestrictedError` grep would still pass if the name appears once in Execution Order. The public contract has to distinguish “the client receives 200/422” from “the collector can still raise, and the view catches it.”
- **LOW:** 09-03 does not list `06.2-VALIDATION.md`, whose gap rows are already `pending`. After a green run those rows stay stale unless someone updates them.
- **LOW:** The old Breaking bullet (`CHANGELOG.md:167-176`) stays true for filtering and does not mention the form. The new bullet must stand alone. Do not edit the old bullet into the new contract or the existing migration anchor changes meaning.

**Suggestions:**
- In `delete_view.md`, replace “the POST lets Django raise” with “the client gets 200/422 and the row remains; a race that still raises `ProtectedError` or `RestrictedError` is caught and answered the same way.”
- Tell copied templates that wrapping `<form>` also removes cancel, and that `has_protected_objects` is now set when `cv_show_related_objects` is false.
- Record the 09-03 counts in ACCEPTANCE and flip the VALIDATION rows for 07–09 in the same task.

**Risk Assessment:** MEDIUM. Documentation drift is the failure mode. The code contracts are specified; the risk is a Phase 7 inventory that still quotes the 500 or claims the queryset `MixedContentTypeError` path is fixed.

## Cross-plan

07 then 08 then 09 is the right order. 08’s RESTRICT fixture is 07’s `Royalty`. 07’s new Guardian tests must not assert that a form is present, or 08 will break them; the 07 behavior text does not, so that coupling is safe. 08’s matrix rewrite is the only edit that has to follow 05’s fixture shape (`{"confirm": "on"}`, no header on the 200 cell). 09 must not mark WR-01 or the AUTH-06 probe fixed.

Overall risk for the pending gap closure is **MEDIUM**. The two code fixes match the source and guardian’s lookup order. The failures that would still ship are catching `ProtectedError` inside `atomic()`, and documenting the caught exception as if the view still raises it to the client.
