I'll review the six revised plans against current source and the prior H01/H02 and A01–A17 ledgers, without treating unfixed code as a plan gap.
Plans are on disk. I'll read the delete, guardian, formset, and test seams the revised actions cite.
H01 and H02 are closed in the revised plans. Current source is still unfixed; that is not a remaining plan gap.

## 06.2-01

Summary: Reject DELETE and project an independent blocked notice with filtered protected labels, while leaving the validated POST lifecycle unchanged.

Strengths: The enclosing include is now owned. `view_delete.content.html:8` still gates on `related_summary or protected_objects`, and a protected-only collect leaves summary empty because the root is skipped at `delete.py:88-92` while PROTECT objects land only in `collector.protected`. Task 01-01 updates both that include and `related_objects.html:4`, and modal rendering uses the same content template (`modal/content.html:7`). `delete()` is overridden, not merely removed from `http_method_names`, so a subclass that restores the name cannot reach Django's raw delete. Core filtering stays in `cv_filter_related_objects` (`delete.py:147`); Guardian filtering stays in its override (`views.py:39-49`) and must not call the core model-permission pass.

Concerns: None.

Suggestions: None.

Risk Assessment: Low. The all-hidden full-page and modal notice is an executable acceptance check, not an implied template side effect.

## 06.2-02

Summary: Parent permission `None` skips only the permission check, and inactive actors are denied on request and callable paths.

Strengths: H02 is an owned compatibility change, not a contradictory test. `test_guardian.py:337-341` still expects `True`; `06.2-02-PLAN.md:89` changes that named test and both docstrings to denial, and plan 06 documents it. `None` currently returns before parent resolution and the no-object state gate (`mixins.py:232-234`). The plan resolves the parent first and always runs `cv_action_enabled` for no-object views. Inactive denial is placed before Guardian's permissive `has_permission` returns (`mixins.py:31-38`, `98-105`) and before `get_objects_for_user`'s superuser shortcut, which does not check `is_active`.

Concerns: None.

Suggestions: None.

Risk Assessment: Low. Wrong-type denial is explicitly not a D-10 lock; URL-bound valid-parent behavior stays covered.

## 06.2-03

Summary: Authorize the fragment target before choices render, then validate declared ancestry for saved and unsaved rows.

Strengths: Browser positives match `formset.js:318-322` and empty top-level `parent_prefix_key` at `render_tree.py:135-138`, including omitted versus `""`. UUID coverage is executable: `tests/test1/app` has no migrations, so the two new models get tables from the existing unmigrated app. Prefix identity is normalized only when `_state.adding` is true (`formsets.py:123`), so unsaved UUID defaults are not treated as persisted parents. Ancestry validation stays, as D-09 requires.

Concerns: None.

Suggestions: None.

Risk Assessment: Low. Integer regressions remain in the 03-02 gate, so the UUID sentinel cannot silently change `None` prefixes.

## 06.2-04

Summary: Remove the inert ViewSet flag in the same task as the manage reader, then show per-view applicability and the strict helper.

Strengths: The only runtime reader is `views.py:231`; 04-01 updates that read, `config_table.html:15-17`, and `test_guardian_manage_context_has_guardian_config` before the combined Guardian gate. The before-validator is mapping-guarded, so `model_validate(instance)` is not a `TypeError`. Parent-only `None` is not applicable even if the view sets fallback `True`, because that flag is never consulted after the `perm_key is None` return (`mixins.py:232-234`). The AUTH-06 probe is carried verbatim at `06.2-04-PLAN.md:80` and is not treated as passed.

Concerns: None.

Suggestions: None.

Risk Assessment: Low for the named AUTH-06 clauses. The classifier limit stays open by design and is not an implementation hole.

## 06.2-05

Summary: Replay direct actor and native-template matrices against the already-fixed handlers.

Strengths: Core DELETE ordering matches `CrudViewPermissionRequiredMixin.has_permission` (`base.py:900-910`), which runs before method selection and 404s missing targets in `cv_get_action_object` (`base.py:368-372`). Guardian object and state checks run in `get_object` (`mixins.py:50-57`), so active top-level DELETE is 405 without that call. Inactive core denial under `AllowAllUsersModelBackend` is still a real `has_perm` denial: that backend only overrides `user_can_authenticate`, while `ModelBackend.has_perm` still requires `is_active`. Manage `"yes"` really is open to any actor (`manage.py:31-32`) and is kept off the inactive object-view policy.

Concerns: None.

Suggestions: None.

Risk Assessment: Low. This wave is post-fix replay; it does not reintroduce a red-first requirement.

## 06.2-06

Summary: Document the settled contracts and compare both supported full suites with the recorded pre-fix baseline.

Strengths: The baseline is explicit at `06.2-06-PLAN.md:80` (5459 Django 4.2 / 5460 Django 6.0) and is not claimed as future AUTH proof. H02 migration text is paired with Breaking guidance. New theme text is required outside the fence-counted sections that `test_alerts.py:249-253` and `test_form_button_docs.py:168-171` slice by heading. Unrun Python, Django 5.2, and Guardian-floor combinations are excluded.

Concerns: None.

Suggestions: None.

Risk Assessment: Low. Completion still depends on measured execution; the plan does not treat the baseline as that execution.

## Prior-item closure

| ID | Disposition |
| --- | --- |
| H01 | Closed. Sign-off. Enclosing template is in `files_modified` and task 01-01; both gates use the independent flag; full-page and modal empty-summary cases are required. |
| H02 | Closed. Sign-off. 02-01 owns and flips `test_create_cv_has_access_child_wrong_type_obj`; 06 documents the intentional denial. Preserving `True` is explicitly rejected. |
| A01 | Closed in 01-01/01-02: custom protection stays 200/422; database PROTECT stays `ProtectedError` with storage unchanged. |
| A02 | Closed in 01-01/01-02: the three leak-preserving tests are named and replaced. |
| A03 | Closed across 01, 02, 05, and 06: defect reproductions are red-to-green; preservation, replay, and docs are not. |
| A04 | Closed in 01-01/01-02: core and Guardian filters stay in their own hooks; no second core pass. |
| A05 | Closed in 01-01: `delete()` rejects even if the method name is restored. |
| A06 | Closed in 03: empty/omitted root prefix, create/update, saved/unsaved nested, and new indices are concrete payloads. |
| A07 | Closed in 03-02: two models in the unmigrated test app, with persisted FK requests. |
| A08 | Closed in 02/03/04/05: fresh routes, `finally` registry/URLConf/cache/vocabulary restore, wave-2 fragment routes independent of plan 03. |
| A09 | Closed in 04-01: field, reader, leaf, and existing assertion move together. |
| A10 | Closed in 05, with statuses reused by 01/02: actor, method, storage, inactive 403, parent-None POST, and manage modes are pinned. |
| A11 | Closed in 06: both pre-fix full-suite results are recorded; unrelated failures cannot be labeled AUTH passes. |
| A12 | Closed in 04-01: mapping guard plus non-mapping and instance revalidation. |
| A13 | Closed in 02-01: both attributes are declared; W280 is checked with vocabulary cleanup. |
| A14 | Closed in 03-02: unsaved UUID defaults normalize to the `None` sentinel without clearing the instance pk. |
| A15 | Closed in 03-02: `num=²` and prefix `²` are stable 400s via ASCII grammar. |
| A16 | Closed in 06-02: new theme section stays outside fence-counted headings; those doc tests run. |
| A17 | Closed in 04-02: parent-only resolved permission `None` is not applicable, including `fallback=True`. |

## Unresolved plan concerns

None. The AUTH-06 unclassified probe remains a flagged assumption at `06.2-04-PLAN.md:80`, carried into the Phase 7 handoff. It is not a new defect and is not inferred complete.
